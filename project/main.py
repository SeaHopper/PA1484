"""PA1484 Group 22 - public transport departures on the LilyGO T4-S3."""

import sys
import time

import lvgl as lv
import network

from board_lvgl import start_board
from debug_log import log
from departures import parse_departures
from demo_departures import get_demo_departures
from network_job import NetworkJob
from settings import TRANSPORT_TYPES, load_settings, save_settings
from trafiklab_api import TrafiklabAPI
from ui_fonts import load_fonts
from secrets import WIFI_SSID, WIFI_PASSWORD
try:
    from secrets import TRAFIKLAB_API_KEY
except ImportError:
    TRAFIKLAB_API_KEY = ""


class Application:
    # This firmware's animation arguments are plain 0/1 (no lv.ANIM constants).
    ANIMATION_OFF = 0
    ANIMATION_ON = 1
    REFRESH_MS = 60_000
    HEADER_HEIGHT = 50   # height of the fixed "Time / Line / ..." heading row
    API_MODES = {"All": "ALL", "Bus": "BUS", "Train": "TRAIN", "Ferry": "BOAT"}
    TEAM = (
        ("Mio Kimondo Öberg", "Lobke Scholten"),
        ("Muhammad Ghali Alshallet", "Sidra Sharaf"),
        ("David Åkesson", "Hadi Abd Alaal"),
    )

    def __init__(self):
        self.display, self.touch, self.handler = start_board()
        self.font_driver, self.font20, self.font28 = load_fonts()
        lv.screen_active().set_style_text_font(self.font20, 0)
        self.current_settings, warning = load_settings()
        self.api = TrafiklabAPI(TRAFIKLAB_API_KEY)
        self.network_job = NetworkJob()
        self.live_rows = None        # parsed live departures for live_stop_id
        self.live_stop_id = None
        self.live_time = ""
        self.pending_refresh = False
        self.next_refresh = time.ticks_ms()
        self.found_stops = []
        self.startup_pending = True
        self.create_ui()
        self.settings_message.set_text(warning)
        # Open Departures after three seconds unless the user navigates first.
        self.tileview.add_event_cb(self.on_navigation, lv.EVENT.VALUE_CHANGED, None)
        self.startup_timer = lv.timer_create(self.on_startup_timeout, 3000, None)
        self.startup_timer.set_repeat_count(1)
        self.network_job.start(("wifi", ""), self.connect_wifi)
        self.poll_timer = lv.timer_create(self.poll_network, 200, None)
        log("application ready")

    # ---------- widget helpers ----------

    def label(self, parent, text, x, y, width=540, size=20, muted=False):
        label = lv.label(parent)
        label.set_text(text)
        label.set_width(width)
        label.set_style_text_font(self.font28 if size == 28 else self.font20, 0)
        label.set_pos(x, y)
        if muted:
            self.muted_labels.append(label)
        return label

    def button(self, parent, text, x, y, width, callback):
        button = lv.button(parent)
        button.set_size(width, 44)
        button.set_pos(x, y)
        button.set_style_shadow_width(0, 0)
        button.set_style_border_width(0, 0)
        button.set_style_radius(6, 0)
        label = lv.label(button)
        label.set_text(text)
        label.set_style_text_font(self.font20, 0)
        label.center()
        button.add_event_cb(callback, lv.EVENT.CLICKED, None)
        self.buttons.append(button)
        return button

    def dropdown(self, parent, x, y, width):
        dropdown = lv.dropdown(parent)
        dropdown.set_size(width, 44)
        dropdown.set_pos(x, y)
        dropdown.set_style_text_font(self.font20, 0)
        dropdown.get_list().set_style_text_font(self.font20, 0)
        self.themed.extend(((dropdown, lv.PART.MAIN), (dropdown.get_list(), lv.PART.MAIN)))
        return dropdown

    def table(self, parent, y, height):
        """A four-column departures-style table."""
        table = lv.table(parent)
        table.set_column_count(4)
        for column, width in enumerate((80, 60, 240, 160)):
            table.set_column_width(column, width)
        table.set_pos(8, y)
        table.set_height(height)
        table.set_style_text_font(self.font20, 0)
        table.set_style_text_font(self.font20, lv.PART.ITEMS)
        table.set_style_pad_top(12, lv.PART.ITEMS)
        table.set_style_pad_bottom(12, lv.PART.ITEMS)
        table.set_style_pad_left(8, lv.PART.ITEMS)
        table.set_style_pad_right(8, lv.PART.ITEMS)
        table.set_style_border_width(1, 0)
        table.set_style_radius(0, 0)
        table.set_style_shadow_width(0, 0)
        table.add_flag(lv.obj.FLAG.SCROLL_CHAIN_HOR)
        self.themed.extend(((table, lv.PART.MAIN), (table, lv.PART.ITEMS)))
        return table

    # ---------- screens ----------

    def create_ui(self):
        self.buttons = []
        self.muted_labels = []
        self.themed = []   # (widget, part) pairs that follow the theme colors
        self.tileview = lv.tileview(lv.screen_active())
        self.tileview.set_size(600, 450)
        self.tileview.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)
        self.tileview.set_style_anim_duration(90, 0)  # long animations are slow here
        self.tileview.remove_flag(lv.obj.FLAG.SCROLL_ELASTIC)
        self.tile_start = self.tileview.add_tile(0, 0, lv.DIR.RIGHT)
        self.tile_departures = self.tileview.add_tile(1, 0, lv.DIR.LEFT | lv.DIR.RIGHT)
        self.tile_settings = self.tileview.add_tile(2, 0, lv.DIR.LEFT)
        self.tiles = (self.tile_start, self.tile_departures, self.tile_settings)
        for tile in self.tiles:
            tile.set_style_pad_all(12, 0)
            tile.remove_flag(lv.obj.FLAG.SCROLLABLE)
            tile.add_flag(lv.obj.FLAG.SCROLL_CHAIN_HOR)
        self.create_start_screen(self.tile_start)
        self.create_departures_screen(self.tile_departures)
        self.create_settings_screen(self.tile_settings)
        self.create_stop_search()
        self.sync_controls()
        self.apply_theme()
        self.refresh_departures()

    def create_start_screen(self, tile):
        self.label(tile, "PA1484 / GROUP 22", 20, 14, width=390, muted=True)
        self.button(tile, "Settings", 432, 4, 124, self.show_settings)
        self.label(tile, "Public Transport Information\nand Interaction on ESP32",
                   20, 76, width=536, size=28)
        self.divider = lv.obj(tile)
        self.divider.set_size(536, 1)
        self.divider.set_pos(20, 172)
        self.divider.set_style_border_width(0, 0)
        self.divider.set_style_radius(0, 0)
        self.divider.set_style_bg_opa(lv.OPA.COVER, 0)
        self.label(tile, "THE TEAM", 20, 192, muted=True)
        for row, (left, right) in enumerate(self.TEAM):
            self.label(tile, left, 20, 234 + row * 40, width=272)
            self.label(tile, right, 308, 234 + row * 40, width=248)
        self.label(tile, "Version 0.1", 20, 388, width=220, muted=True)
        self.button(tile, "Departures", 386, 376, 170, self.show_departures)

    def create_departures_screen(self, tile):
        self.label(tile, "Departures", 8, 0, width=170, size=28)
        self.button(tile, "Find stop", 188, 0, 120, self.open_stop_search)
        self.button(tile, "Refresh", 316, 0, 100, self.manual_refresh)
        self.button(tile, "Settings", 424, 0, 132, self.show_settings)
        self.departure_source = self.label(tile, "", 8, 58)
        # The column headings are a separate one-row table, so they stay in
        # place while only the departure rows below them scroll.
        header = self.table(tile, 108, self.HEADER_HEIGHT)
        header.set_row_count(1)
        for column, heading in enumerate(("Time", "Line", "Destination", "Status")):
            header.set_cell_value(0, column, heading)
        header.remove_flag(lv.obj.FLAG.SCROLLABLE)
        table = self.departure_table = self.table(
            tile, 108 + self.HEADER_HEIGHT, 222 - self.HEADER_HEIGHT)
        table.set_scroll_dir(lv.DIR.VER)
        table.set_scrollbar_mode(lv.SCROLLBAR_MODE.AUTO)
        self.departure_note = self.label(tile, "", 8, 338)
        self.label(tile, "Data from Trafiklab.se - CC BY 4.0", 8, 398, muted=True)

    def create_settings_screen(self, tile):
        self.label(tile, "Settings", 8, 0, size=28)
        # The stop is chosen with Find stop on the Departures screen.
        self.selected_stop_label = self.label(tile, "", 8, 50, width=540)
        self.label(tile, "Transport type", 8, 110)
        self.transport_dropdown = self.dropdown(tile, 8, 138, 260)
        self.transport_dropdown.set_options("\n".join(TRANSPORT_TYPES))
        self.transport_dropdown.add_event_cb(self.on_selection, lv.EVENT.VALUE_CHANGED, None)
        self.button(tile, "Light / dark", 290, 138, 248, self.on_theme)
        self.mode_button = self.button(tile, "", 8, 196, 250, self.on_mode)
        self.button(tile, "Save defaults", 280, 196, 258, self.on_save)
        self.button(tile, "Reset to saved", 8, 254, 250, self.on_reset)
        self.button(tile, "Departures", 280, 254, 258, self.show_departures)
        self.settings_message = self.label(tile, "", 8, 306)
        self.label(tile, "Data from Trafiklab.se - CC BY 4.0\n"
                   "creativecommons.org/licenses/by/4.0/\n"
                   "Departure data filtered and formatted", 8, 360, muted=True)

    def create_stop_search(self):
        panel = self.search_panel = lv.obj(lv.screen_active())
        panel.set_size(600, 450)
        panel.set_pos(0, 0)
        panel.set_style_bg_opa(lv.OPA.COVER, 0)
        panel.set_style_text_font(self.font20, 0)
        self.search_text = lv.textarea(panel)
        self.search_text.set_one_line(True)
        self.search_text.set_style_text_font(self.font20, 0)
        self.search_text.set_max_length(60)
        self.search_text.set_size(330, 42)
        self.search_text.set_pos(0, 0)
        self.search_text.set_placeholder_text("Stop name, at least 3 letters")
        self.button(panel, "Search", 340, 0, 100, self.search_stops)
        self.button(panel, "Close", 450, 0, 105, self.close_stop_search)
        self.search_results = self.dropdown(panel, 0, 56, 550)
        self.search_results.set_options("Search for a stop first")
        self.button(panel, "Use selected stop", 0, 106, 260, self.choose_stop)
        self.search_info = self.label(panel, "", 0, 154)
        self.create_keyboard(panel)
        panel.remove_flag(lv.obj.FLAG.SCROLLABLE)
        self.themed.extend(((panel, lv.PART.MAIN), (self.search_text, lv.PART.MAIN),
                            (self.search_keyboard, lv.PART.MAIN)))
        panel.add_flag(lv.obj.FLAG.HIDDEN)

    # ---------- Swedish on-screen keyboard ----------
    # A plain button grid, not lv.keyboard: this firmware's lv.keyboard keeps
    # its inactive layouts where the garbage collector cannot see them, so
    # switching to upper case read freed memory and rebooted the board.
    # A button grid owns the layout it shows, so that cannot happen here.

    def create_keyboard(self, panel):
        keyboard = self.search_keyboard = lv.buttonmatrix(panel)
        keyboard.set_size(568, 220)
        keyboard.align(lv.ALIGN.BOTTOM_MID, 0, 0)
        keyboard.set_style_text_font(self.font20, lv.PART.ITEMS)
        keyboard.set_style_pad_all(4, 0)
        keyboard.set_style_pad_gap(4, 0)
        keyboard.add_event_cb(self.on_key, lv.EVENT.VALUE_CHANGED, None)
        self.upper_case = False
        self.show_keyboard_layout()

    def show_keyboard_layout(self):
        S = lv.SYMBOL
        ctrl = lv.buttonmatrix.CTRL
        special = ctrl.CHECKED          # highlighted look
        once = special | ctrl.NO_REPEAT  # pressed once, no auto-repeat
        rows = ["1234567890", "qwertyuiopå", "asdfghjklöä", "zxcvbnm"]
        if self.upper_case:
            rows = [row.upper() for row in rows]
        shift = "abc" if self.upper_case else "ABC"
        layout = (list(rows[0]) + [S.BACKSPACE, "\n"]
                  + list(rows[1]) + ["\n"]
                  + list(rows[2]) + ["\n"]
                  + [shift] + list(rows[3]) + ["-", ".", "\n"]
                  + [S.CLOSE, S.LEFT, " ", S.RIGHT, S.OK, ""])
        widths = ([4] * 10 + [special | 6]
                  + [4] * 11
                  + [4] * 11
                  + [once | 6] + [4] * 9
                  + [once | 3, special | 3, 10, special | 3, once | 4])
        self.keyboard_layout = layout   # keep a reference while shown
        self.search_keyboard.set_map(layout)
        self.search_keyboard.set_ctrl_map(widths)

    def on_key(self, _event):
        keyboard = self.search_keyboard
        key = keyboard.get_button_text(keyboard.get_selected_button())
        if not key:
            return
        S = lv.SYMBOL
        text = self.search_text
        if key in ("ABC", "abc"):
            self.upper_case = not self.upper_case
            self.show_keyboard_layout()
        elif key == S.BACKSPACE:
            text.delete_char()
        elif key == S.LEFT:
            text.cursor_left()
        elif key == S.RIGHT:
            text.cursor_right()
        elif key == S.OK:
            self.search_stops(None)
        elif key == S.CLOSE:
            self.close_stop_search(None)
        else:
            text.add_text(key)

    # ---------- settings ----------

    def sync_controls(self):
        """Show the current settings on the controls."""
        settings = self.current_settings
        self.selected_stop_label.set_text(settings["stop_name"])
        self.transport_dropdown.set_selected(TRANSPORT_TYPES.index(settings["transport_type"]))
        self.mode_button.get_child(0).set_text(
            "Use Demo" if settings["live_mode"] else "Use Live")

    def apply_theme(self):
        dark = self.current_settings["dark_mode"]
        background = lv.color_hex(0x111820 if dark else 0xF7F9FC)
        foreground = lv.color_hex(0xF0F4F8 if dark else 0x182534)
        muted = lv.color_hex(0xA5B4C4 if dark else 0x56677A)
        accent = lv.color_hex(0x166B70 if dark else 0x126469)
        edge = lv.color_hex(0x344250 if dark else 0xD5DFE8)
        for tile in self.tiles:
            tile.set_style_bg_opa(lv.OPA.COVER, 0)
            tile.set_style_bg_color(background, 0)
            tile.set_style_text_color(foreground, 0)
        for widget, part in self.themed:
            widget.set_style_bg_color(background, part)
            widget.set_style_text_color(foreground, part)
            widget.set_style_border_color(edge, part)
        for button in self.buttons:
            button.set_style_bg_color(accent, 0)
            button.set_style_bg_opa(lv.OPA.COVER, 0)
            button.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
        for label in self.muted_labels:
            label.set_style_text_color(muted, 0)
        self.divider.set_style_bg_color(edge, 0)

    def on_selection(self, _event):
        self.current_settings["transport_type"] = TRANSPORT_TYPES[
            self.transport_dropdown.get_selected()]
        self.settings_message.set_text("Applied. Save to keep after restart.")
        self.refresh_departures()

    def on_theme(self, _event):
        self.current_settings["dark_mode"] = not self.current_settings["dark_mode"]
        self.apply_theme()
        self.settings_message.set_text("Theme applied. Save to keep after restart.")

    def on_mode(self, _event):
        self.current_settings["live_mode"] = not self.current_settings["live_mode"]
        self.sync_controls()
        self.reload_live()

    def on_save(self, _event):
        try:
            save_settings(self.current_settings)
        except (OSError, ValueError):
            self.settings_message.set_text("Save failed. Please try again.")
            return
        self.settings_message.set_text("Defaults saved.")
        self.show_departures()

    def on_reset(self, _event):
        """Reload the last saved settings."""
        self.current_settings, warning = load_settings()
        self.sync_controls()
        self.apply_theme()
        self.settings_message.set_text(warning or "Restored saved defaults.")
        self.reload_live()

    def reload_live(self):
        """Forget cached live rows and fetch new ones if live mode is on."""
        self.live_rows = None
        self.pending_refresh = self.current_settings["live_mode"]
        self.refresh_departures()

    # ---------- departures table ----------

    def refresh_departures(self):
        """Show live rows (if loaded) or the clearly labelled demo rows."""
        settings = self.current_settings
        mode = settings["transport_type"]
        if not settings["live_mode"]:
            self.departure_source.set_text("DEMO - fictional services, all demo stops")
            self.draw_rows([{"time": r[0], "line": r[1], "destination": r[2], "status": r[3]}
                            for r in get_demo_departures(mode)])
            self.departure_note.set_text("Demo data is not a real timetable")
            return
        self.departure_source.set_text("LIVE - " + settings["stop_name"])
        if self.live_rows is None or self.live_stop_id != settings["stop_id"]:
            self.draw_rows([])
            self.departure_note.set_text("Waiting for live data")
            return
        api_mode = self.API_MODES[mode]
        rows = [row for row in self.live_rows
                if api_mode == "ALL" or row["transport_mode"] == api_mode][:20]
        self.draw_rows(rows)
        self.departure_note.set_text("Updated: " + self.live_time if rows
                                     else "No departures match this filter")

    def draw_rows(self, rows):
        keys = ("time", "line", "destination", "status")
        table_rows = tuple(tuple(str(row[key]) for key in keys) for row in rows)
        if table_rows == getattr(self, "last_table_rows", None):
            return  # unchanged: avoid a redraw and keep the scroll position
        table = self.departure_table
        # Keep at least one (blank) row so an empty table is still valid.
        table.set_row_count(max(1, len(table_rows)))
        for column in range(4):
            table.set_cell_value(0, column, "")
        for row_number, departure in enumerate(table_rows):
            for column, value in enumerate(departure):
                table.set_cell_value(row_number, column, value)
        table.scroll_to_y(0, self.ANIMATION_OFF)
        self.last_table_rows = table_rows

    def manual_refresh(self, _event):
        if self.current_settings["live_mode"]:
            self.pending_refresh = True
        else:
            self.refresh_departures()

    # ---------- stop search ----------

    def open_stop_search(self, _event):
        self.startup_pending = False
        self.search_panel.remove_flag(lv.obj.FLAG.HIDDEN)
        self.search_text.add_state(lv.STATE.FOCUSED)  # show the text cursor
        self.search_info.set_text("Search by name, e.g. Campus or Karlskrona")

    def close_stop_search(self, _event):
        self.search_panel.add_flag(lv.obj.FLAG.HIDDEN)

    def search_stops(self, _event):
        query = self.search_text.get_text().strip()
        if len(query) < 3:
            self.search_info.set_text("Enter at least 3 letters")
        elif self.network_job.start(("search", query), self.load_stop_search, query):
            self.found_stops = []
            self.search_results.set_options("Searching...")
            self.search_info.set_text("Searching Trafiklab...")
        else:
            self.search_info.set_text("Another request is running. Try again shortly.")

    def choose_stop(self, _event):
        selected = self.search_results.get_selected()
        if not 0 <= selected < len(self.found_stops):
            self.search_info.set_text("Search and select a stop first")
            return
        stop = self.found_stops[selected]
        self.current_settings.update(stop_id=stop["id"], stop_name=stop["name"], live_mode=True)
        self.sync_controls()
        self.reload_live()
        self.close_stop_search(None)
        self.settings_message.set_text("Stop selected. Save to keep after restart.")

    # ---------- background network work ----------

    def poll_network(self, _timer):
        """UI timer: apply finished requests and start scheduled refreshes.

        The worker thread never touches LVGL; all widget updates happen here.
        """
        result = self.network_job.take_result()
        if result is not None:
            (action, value), data, error = result
            if action == "wifi":
                self.on_wifi_result(data, error)
            elif action == "search":
                self.on_search_result(data, error)
            elif action == "departures":
                self.on_departures_result(value, data, error)
        now = time.ticks_ms()
        if self.current_settings["live_mode"] and (
                self.pending_refresh or time.ticks_diff(now, self.next_refresh) >= 0):
            stop_id = self.current_settings["stop_id"]
            if self.network_job.start(("departures", stop_id), self.load_live_departures, stop_id):
                self.pending_refresh = False
                self.next_refresh = time.ticks_add(now, self.REFRESH_MS)
                self.departure_note.set_text("Updating...")

    def on_wifi_result(self, connected, error):
        self.settings_message.set_text(
            error or ("Wi-Fi connected" if connected else "Wi-Fi timeout. Check your hotspot."))
        self.pending_refresh = self.current_settings["live_mode"]

    def on_search_result(self, stops, error):
        stops = stops or []
        self.found_stops = stops[:20]
        self.search_results.set_options("\n".join(
            stop["name"] + " (" + stop["id"] + ")" for stop in self.found_stops) or "No results")
        self.search_info.set_text(error or (
            "More results: refine the name" if len(stops) > 20 else
            "Select a result" if stops else "No matching stops"))

    def on_departures_result(self, stop_id, data, error):
        settings = self.current_settings
        if stop_id != settings["stop_id"] or not settings["live_mode"]:
            return  # late answer for a stop that is no longer selected
        if error:
            self.live_rows = None
            self.refresh_departures()
            self.departure_note.set_text(error)
            return
        self.live_rows, self.live_time = data
        self.live_stop_id = stop_id
        self.refresh_departures()

    # These run in the worker thread: no LVGL calls allowed here.

    @staticmethod
    def connect_wifi():
        """Connect to Wi-Fi, waiting up to 15 seconds."""
        station = network.WLAN(network.STA_IF)
        station.active(True)
        if station.isconnected():
            return True
        try:
            station.connect(WIFI_SSID, WIFI_PASSWORD)
        except OSError:
            pass  # already connecting; just wait below
        started = time.ticks_ms()
        while (not station.isconnected() and
               time.ticks_diff(time.ticks_ms(), started) < 15_000):
            time.sleep_ms(250)
        return station.isconnected()

    def load_stop_search(self, query):
        if not self.connect_wifi():
            raise RuntimeError("Wi-Fi is not connected")
        return self.api.search_stops(query)

    def load_live_departures(self, stop_id):
        """Fetch and parse in the worker, so the UI thread only gets small rows."""
        if not self.connect_wifi():
            raise RuntimeError("Wi-Fi is not connected")
        data = self.api.fetch_departures(stop_id)
        rows = parse_departures(data, "ALL", limit=60)
        stamp = data.get("timestamp") or ""
        return rows, stamp[11:19] or "unknown time"

    # ---------- navigation ----------

    def on_navigation(self, _event):
        self.startup_pending = False

    def on_startup_timeout(self, _timer):
        if self.startup_pending:
            self.show_departures()

    def show_settings(self, _event=None):
        self.startup_pending = False
        self.tileview.set_tile(self.tile_settings, self.ANIMATION_ON)

    def show_departures(self, _event=None):
        self.startup_pending = False
        self.tileview.set_tile(self.tile_departures, self.ANIMATION_ON)


try:
    app = Application()
except Exception as error:
    log("FATAL: %r" % (error,))
    sys.print_exception(error)
    raise
