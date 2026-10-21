import sys
import time
 
import lvgl as lv
import network
 
from board_lvgl import start_board
from debug_log import log
 
from secrets import WIFI_SSID, WIFI_PASSWORD
 
 
class Application:
    def __init__(self):
        self.display, self.touch, self.handler = start_board()
        self.tile2_dark = False
        self.create_ui()
        self.connect_wifi()
        log("student application ready")
        self.transport_type = "All"   # standardvärde
        
 
    @staticmethod
    def apply_tile_colors(tile, label, dark):
        tile.set_style_bg_opa(lv.OPA.COVER, 0)
        tile.set_style_bg_color(
            lv.color_hex(0x000000 if dark else 0xFFFFFF), 0
        )
        label.set_style_text_color(
            lv.color_hex(0x00c993 if dark else 0x000000), 0
        )
 
    def on_tile2_clicked(self, _event):
        self.tile2_dark = not self.tile2_dark
        self.apply_tile_colors(self.tile2, self.tile2_label, self.tile2_dark)
 
 
 
 
    def on_transport_selected(self, event):
        selected = self.transport_dropdown.get_selected()
        options = ["All", "Train", "Bus", "Ferry"]
        self.transport_type = options[selected]
        log("Transporttyp vald: " + self.transport_type)
 
 
 
    def create_ui(self):
        'Function: Creates UI'
        self.tileview = lv.tileview(lv.screen_active())
        self.tileview.set_size(600, 450)
        self.tileview.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)
 
        self.tile1 = self.tileview.add_tile(0, 0, lv.DIR.RIGHT)
        self.tile3 = self.tileview.add_tile(1, 0, lv.DIR.LEFT | lv.DIR.RIGHT)
        self.tile2 = self.tileview.add_tile(2, 0, lv.DIR.LEFT)
    
 
        #44-68 start screan
        self.tile1_label = lv.label(self.tile1)
        self.tile1_label.set_text("Public Transport Information and Interaction on ESP32")
        self.tile1_label.set_style_text_font(lv.font_montserrat_28, -1)
        self.tile1_label.align(lv.ALIGN.TOP_MID, 0, 60)
        self.apply_tile_colors(self.tile1, self.tile1_label, False)
 
        self.tile1_namn = lv.label(self.tile1)
        self.tile1_namn.set_text("Mio Kimondo Oberg Lobke Scholten \nMuhammad Ghali Alshallet Sidra Sharaf \nDavid Akesson Hadi Abd Alaal")
        self.tile1_namn.set_style_text_font(lv.font_montserrat_28, -1)
        self.tile1_namn.center()
        self.apply_tile_colors(self.tile1, self.tile1_namn, False)
 
        self.tile1_group = lv.label(self.tile1)
        self.tile1_group.set_text("PA1484 Group 22")
        self.tile1_group.set_style_text_font(lv.font_montserrat_28, -1)
        self.tile1_group.align(lv.ALIGN.TOP_MID, 0, 130)
        self.apply_tile_colors(self.tile1, self.tile1_group, False)
        
        self.tile1_version = lv.label(self.tile1)
        self.tile1_version.set_text("Version 0.1")
        self.tile1_version.set_style_text_font(lv.font_montserrat_28, -1)
        self.tile1_version.align(lv.ALIGN.BOTTOM_MID, 0, -60)
        self.apply_tile_colors(self.tile1, self.tile1_version, False)
        
#tile2 är inställnigar
        self.tile2_label = lv.label(self.tile2)
        self.tile2_label.set_text("Settings")
        self.tile2_label.set_style_text_font(lv.font_montserrat_28, 0)
        self.tile2_label.align(lv.ALIGN.TOP_MID, 0, 40)
        self.apply_tile_colors(self.tile2, self.tile2_label, False)
        self.tile2.add_flag(lv.obj.FLAG.CLICKABLE)
        self.tile2.add_event_cb(
            self.on_tile2_clicked, lv.EVENT.CLICKED, None
        )
        
 
        self.transport_dropdown = lv.dropdown(self.tile2)
        self.transport_dropdown.set_options("All\nTrain\nBus\nFerry")
        self.transport_dropdown.set_style_text_font(lv.font_montserrat_28, 0)
        self.transport_dropdown.align(lv.ALIGN.TOP_LEFT, 0, 0)
 
        self.transport_dropdown.add_event_cb(
            self.on_transport_selected, lv.EVENT.VALUE_CHANGED, None
        )
    
#tile3 är busstabellen
        self.tile3_label = lv.label(self.tile3)
        self.tile3_label.set_text("Departures")
        self.tile3_label.set_style_text_font(lv.font_montserrat_28, -1)
        self.tile3_label.align(lv.ALIGN.TOP_MID, 0, 40)
        self.apply_tile_colors(self.tile3, self.tile3_label, False)
 
        
        
    @staticmethod
    def connect_wifi():
        'Function: Connects to WiFi'
        log("connecting to Wi-Fi SSID: " + WIFI_SSID)
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
 
