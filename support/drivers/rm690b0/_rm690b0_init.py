"""Initialization sequence derived from LilyGO's working RM690B0 driver."""

import time
import lvgl as lv


def init(self):
    buf = self._param_buf
    mv = self._param_mv

    self.reset()
    time.sleep_ms(120)

    buf[0] = 0x20
    self.set_params(0xFE, mv[:1])         # Manufacturer panel page
    buf[0] = 0x0A
    self.set_params(0x26, mv[:1])         # MIPI off
    buf[0] = 0x80
    self.set_params(0x24, mv[:1])         # SPI RAM write
    buf[0] = 0x51
    self.set_params(0x5A, mv[:1])         # SWIRE 1
    buf[0] = 0x2E
    self.set_params(0x5B, mv[:1])         # SWIRE 2
    buf[0] = 0x00
    self.set_params(0xFE, mv[:1])         # User command page
    color_size = lv.color_format_get_size(self._color_space)
    buf[0] = 0x55 if color_size == 2 else 0x77
    self.set_params(0x3A, mv[:1])
    buf[0] = 0x00
    self.set_params(0xC2, mv[:1])
    time.sleep_ms(10)
    buf[0] = self._madctl(self._color_byte_order, self._ORIENTATION_TABLE)
    self.set_params(0x36, mv[:1])
    buf[0] = 0x00
    self.set_params(0x51, mv[:1])
    self.set_params(0x35, mv[:1])         # Tearing-effect output on GPIO18
    self.set_params(0x11)                 # Sleep out
    time.sleep_ms(120)
    self.set_params(0x29)
    time.sleep_ms(10)
    self.set_brightness(80)
