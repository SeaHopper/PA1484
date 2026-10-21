import sys
import time

import lvgl as lv
import network

from board_lvgl import start_board
from debug_log import log
from departures import TRANSPORT_TYPES, get_demo_departures
from settings import STOP_OPTIONS, load_settings, save_settings
from secrets import WIFI_SSID, WIFI_PASSWORD


class Application:
    def __init__(self):
        self.display, self.touch, self.handler = start_board()
        self.current_settings, warning = load_settings()
        self.create_ui()
        self.settings_message.set_text(warning)
        # Visa avgångar efter 3 sekunder om användaren inte byter sida.
        self.startup_pending = True
        self.tileview.add_event_cb(self.on_navigation, lv.EVENT.VALUE_CHANGED, None)
        self.startup_timer = lv.timer_create(self.on_startup_timeout, 3000, None)
        self.startup_timer.set_repeat_count(1)
        self.connect_wifi()
        log("student application ready")

    def label(self, parent, text, x, y, width=540, size=20):
        'Function: Creates a text label'
        label = lv.label(parent)
        label.set_text(text)
        label.set_width(width)
        label.set_style_text_font(
            lv.font_montserrat_28 if size == 28 else lv.font_montserrat_20, 0
        )
        label.set_pos(x, y)
        return label

    def button(self, parent, text, x, y, width, callback):
        'Function: Creates a button with a click event'
        button = lv.button(parent)
        button.set_size(width, 44)
        button.set_pos(x, y)
        label = lv.label(button)
        label.set_text(text)
        label.center()
        button.add_event_cb(callback, lv.EVENT.CLICKED, None)
        return button

    def create_ui(self):
        'Function: Creates UI'
        self.tileview = lv.tileview(lv.screen_active())
        self.tileview.set_size(600, 450)
        self.tileview.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)
        self.tile1 = self.tileview.add_tile(0, 0, lv.DIR.RIGHT)
        self.tile3 = self.tileview.add_tile(1, 0, lv.DIR.LEFT | lv.DIR.RIGHT)
        self.tile2 = self.tileview.add_tile(2, 0, lv.DIR.LEFT)
        for tile in (self.tile1, self.tile3, self.tile2):
            tile.set_style_pad_all(12, 0)

        # tile1 är startsidan
        self.label(self.tile1,
                   "Public Transport Information\nand Interaction on ESP32",
                   8, 56, size=28)
        self.label(self.tile1, "PA1484 Group 22", 8, 146, size=28)
        self.label(self.tile1,
                   "Mio Kimondo Oberg - Lobke Scholten\n"
                   "Muhammad Ghali Alshallet - Sidra Sharaf\n"
                   "David Akesson - Hadi Abd Alaal", 8, 200)
        self.label(self.tile1, "Version 0.1", 8, 324)
        self.button(self.tile1, "Settings", 420, 0, 140, self.show_settings)

        # tile2 är inställningar
        self.label(self.tile2, "Settings", 8, 0, size=28)
        self.label(self.tile2, "Departure stop", 8, 50)
        self.stop_dropdown = lv.dropdown(self.tile2)
        self.stop_dropdown.set_options("\n".join(STOP_OPTIONS))
        self.stop_dropdown.set_size(530, 44)
        self.stop_dropdown.set_pos(8, 78)
        self.stop_dropdown.add_event_cb(self.on_selection, lv.EVENT.VALUE_CHANGED, None)
        self.label(self.tile2, "Transport type", 8, 134)
        self.transport_dropdown = lv.dropdown(self.tile2)
        self.transport_dropdown.set_options("\n".join(TRANSPORT_TYPES))
        self.transport_dropdown.set_size(260, 44)
        self.transport_dropdown.set_pos(8, 162)
        self.transport_dropdown.add_event_cb(self.on_selection, lv.EVENT.VALUE_CHANGED, None)
        self.button(self.tile2, "Light / dark", 290, 162, 248, self.on_theme)
        self.button(self.tile2, "Save defaults", 8, 226, 250, self.on_save)
        self.button(self.tile2, "Reset to saved", 280, 226, 258, self.on_reset)
        self.button(self.tile2, "Departures", 8, 286, 250, self.show_departures)
        self.settings_message = self.label(self.tile2, "", 8, 344)

        # tile3 är avgångstabellen
        self.label(self.tile3, "Departures", 8, 0, width=300, size=28)
        self.button(self.tile3, "Settings", 420, 0, 140, self.show_settings)
        self.departure_source = self.label(self.tile3, "", 8, 50)
        self.departure_table = lv.table(self.tile3)
        self.departure_table.set_column_count(4)
        for column, width in enumerate((80, 60, 240, 160)):
            self.departure_table.set_column_width(column, width)
        self.departure_table.set_height(262)
        self.departure_table.set_pos(8, 108)
        self.departure_table.set_style_text_font(lv.font_montserrat_20, 0)
        self.departure_table.set_style_pad_top(12, lv.PART.ITEMS)
        self.departure_table.set_style_pad_bottom(12, lv.PART.ITEMS)
        self.departure_table.set_scroll_dir(lv.DIR.VER)
        self.departure_table.set_scrollbar_mode(lv.SCROLLBAR_MODE.AUTO)
        self.departure_table.add_flag(lv.obj.FLAG.SCROLL_CHAIN_HOR)
        self.departure_note = self.label(self.tile3, "", 8, 382)
        self.sync_controls()
        self.apply_theme()
        self.refresh_departures()

    def sync_controls(self):
        'Function: Updates dropdowns from current settings'
        self.stop_dropdown.set_selected(STOP_OPTIONS.index(self.current_settings["stop"]))
        self.transport_dropdown.set_selected(
            TRANSPORT_TYPES.index(self.current_settings["transport_type"])
        )

    def on_selection(self, _event):
        'Function: Applies selected stop and transport type'
        self.current_settings["stop"] = STOP_OPTIONS[self.stop_dropdown.get_selected()]
        self.current_settings["transport_type"] = TRANSPORT_TYPES[
            self.transport_dropdown.get_selected()
        ]
        self.settings_message.set_text("Applied for this session. Save to keep after restart.")
        self.refresh_departures()

    def on_theme(self, _event):
        'Function: Changes between light and dark mode'
        self.current_settings["dark_mode"] = not self.current_settings["dark_mode"]
        self.apply_theme()
        self.settings_message.set_text("Theme applied. Save to keep after restart.")

    def apply_theme(self):
        'Function: Updates screen and table colors'
        dark = self.current_settings["dark_mode"]
        background = lv.color_hex(0x151515 if dark else 0xFFFFFF)
        foreground = lv.color_hex(0xFFFFFF if dark else 0x151515)
        for tile in (self.tile1, self.tile2, self.tile3):
            tile.set_style_bg_opa(lv.OPA.COVER, 0)
            tile.set_style_bg_color(background, 0)
            tile.set_style_text_color(foreground, 0)
        for widget, part in ((self.departure_table, lv.PART.ITEMS),
                             (self.departure_table, lv.PART.MAIN),
                             (self.stop_dropdown, lv.PART.MAIN),
                             (self.transport_dropdown, lv.PART.MAIN)):
            widget.set_style_bg_color(background, part)
            widget.set_style_text_color(foreground, part)

    def on_save(self, _event):
        'Function: Saves settings and opens departures'
        try:
            save_settings(self.current_settings)
        except (OSError, ValueError):
            self.settings_message.set_text("Save failed. Please try again before restarting.")
            log("settings save failed")
            return
        self.settings_message.set_text("Defaults saved.")
        self.show_departures()

    def on_reset(self, _event):
        'Function: Restores saved settings'
        # Läs tillbaka de senast sparade inställningarna.
        self.current_settings, warning = load_settings()
        self.sync_controls()
        self.apply_theme()
        self.refresh_departures()
        self.settings_message.set_text(warning or "Restored saved defaults.")

    def refresh_departures(self):
        'Function: Updates departure rows after a selection'
        stop = self.current_settings["stop"]
        mode = self.current_settings["transport_type"]
        rows = get_demo_departures(mode, None if stop == "All stops" else stop)
        self.departure_source.set_text("DEMO - " + stop + "\nFictional times and lines")
        self.departure_table.set_row_count(len(rows) + 1)
        for column, heading in enumerate(("Time", "Line", "Destination", "Status")):
            self.departure_table.set_cell_value(0, column, heading)
        for row_number, departure in enumerate(rows, 1):
            for column in range(4):
                self.departure_table.set_cell_value(row_number, column, departure[column])
        self.departure_table.scroll_to_y(0, lv.ANIM.OFF)
        self.departure_note.set_text(
            "Swipe vertically for more" if rows else "No demo departures match these settings"
        )

    def on_navigation(self, _event):
        'Function: Cancels the automatic screen change'
        self.startup_pending = False

    def on_startup_timeout(self, _timer):
        'Function: Opens departures after the startup screen'
        if self.startup_pending:
            self.show_departures()

    def show_settings(self, _event=None):
        'Function: Opens the settings tile'
        self.startup_pending = False
        self.tileview.set_tile(self.tile2, lv.ANIM.OFF)

    def show_departures(self, _event=None):
        'Function: Opens the departure tile'
        self.startup_pending = False
        self.tileview.set_tile(self.tile3, lv.ANIM.OFF)

    @staticmethod
    def connect_wifi():
        'Function: Connects to WiFi'
        log("connecting to Wi-Fi")
        station = network.WLAN(network.STA_IF)
        station.active(True)
        station.connect(WIFI_SSID, WIFI_PASSWORD)
        started = time.ticks_ms()
        while (not station.isconnected() and
               time.ticks_diff(time.ticks_ms(), started) < 15_000):
            time.sleep_ms(250)
        log("Wi-Fi connected" if station.isconnected()
            else "Wi-Fi could not connect (timeout)")


try:
    app = Application()
except Exception as error:
    log("FATAL: %r" % (error,))
    sys.print_exception(error)
    raise
