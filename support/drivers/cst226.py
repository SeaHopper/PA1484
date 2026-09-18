"""CST226 touch adapter for upstream LVGL MicroPython pointer framework."""

import machine
import pointer_framework
import time


I2C_ADDR = 0x5A
BITS = 8


class CST226(pointer_framework.PointerDriver):
    def __init__(self, device, reset_pin=17, swap_xy=False, mirror_y=False,
                 touch_cal=None, debug=False):
        self._device = device
        self._tx = bytearray(1)
        self._rx = bytearray(28)
        self._tx_mv = memoryview(self._tx)
        self._rx_mv = memoryview(self._rx)
        self._reset = machine.Pin(reset_pin, machine.Pin.OUT, value=1)
        self._swap_xy = swap_xy
        self._mirror_y = mirror_y
        self._reset.value(0)
        time.sleep_ms(100)
        self._reset.value(1)
        time.sleep_ms(100)
        super().__init__(touch_cal=touch_cal, debug=debug)

    def _get_coords(self):
        self._tx[0] = 0x00
        try:
            self._device.write_readinto(self._tx_mv, self._rx_mv)
        except OSError:
            return None
        data = self._rx
        if data[6] != 0xAB or data[0] == 0xAB or data[5] == 0x80:
            return None
        count = data[5] & 0x7F
        if count < 1 or count > 5:
            return None
        x = (data[1] << 4) | ((data[3] >> 4) & 0x0F)
        y = (data[2] << 4) | (data[3] & 0x0F)
        if self._swap_xy:
            x, y = y, x
        if self._mirror_y:
            y = 449 - y
        return self.PRESSED, x, y
