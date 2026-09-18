"""RM690B0 LVGL driver for the LilyGO T4-S3 QSPI panel.

UI rendering remains entirely in upstream LVGL. This module only translates
standard display-driver commands to the panel's 32-bit QSPI command format.
"""

from micropython import const
import display_driver_framework
import lvgl as lv


STATE_HIGH = display_driver_framework.STATE_HIGH
STATE_LOW = display_driver_framework.STATE_LOW
BYTE_ORDER_RGB = display_driver_framework.BYTE_ORDER_RGB
BYTE_ORDER_BGR = display_driver_framework.BYTE_ORDER_BGR

_CASET = const(0x2A)
_RASET = const(0x2B)
_RAMWR = const(0x2C)
_MADCTL = const(0x36)
_WRDISBV = const(0x51)


def _param_command(command):
    return 0x02000000 | (command << 8)


def _color_command(command):
    return 0x32000000 | (command << 8)


class RM690B0(display_driver_framework.DisplayDriver):
    # The application uses the panel's native landscape orientation.
    _ORIENTATION_TABLE = (0x60, 0xC0, 0xA0, 0x00)

    def __init__(
        self,
        data_bus,
        display_width=600,
        display_height=450,
        frame_buffer1=None,
        frame_buffer2=None,
        reset_pin=None,
        reset_state=STATE_LOW,
        power_pin=None,
        power_on_state=STATE_HIGH,
        offset_x=0,
        offset_y=0,
        color_byte_order=BYTE_ORDER_RGB,
        color_space=lv.COLOR_FORMAT.RGB565,
        rgb565_byte_swap=True,
    ):
        self._brightness = 0
        if data_bus.get_lane_count() != 4:
            raise ValueError("RM690B0 requires a four-lane QSPI bus")

        # Let the upstream framework allocate its standard 1/10-screen DMA
        # buffers. RM690B0 requires partial, windowed transfers; a single
        # 540 kB FULL-mode QSPI transaction stalls on ESP32-S3.
        super().__init__(
            data_bus=data_bus,
            display_width=display_width,
            display_height=display_height,
            frame_buffer1=frame_buffer1,
            frame_buffer2=frame_buffer2,
            reset_pin=reset_pin,
            reset_state=reset_state,
            power_pin=power_pin,
            power_on_state=power_on_state,
            offset_x=offset_x,
            offset_y=offset_y,
            color_byte_order=color_byte_order,
            color_space=color_space,
            rgb565_byte_swap=rgb565_byte_swap,
            _cmd_bits=32,
            _param_bits=8,
        )
        # RM690B0 window transfers must start and end on even boundaries.
        # Without this, adjacent LVGL partial updates leave visible seams.
        self._disp_drv.add_event_cb(
            self._round_invalidated_area, lv.EVENT.INVALIDATE_AREA, None
        )

    @staticmethod
    def _round_invalidated_area(event):
        area = lv.area_t.__cast__(event.get_param())
        if area.x1 & 1:
            area.x1 -= 1
        if not area.x2 & 1:
            area.x2 += 1
        if area.y1 & 1:
            area.y1 -= 1
        if not area.y2 & 1:
            area.y2 += 1

    def init(self, type=None):
        super().init(type)
        # The base class optimizes full-frame drivers by replacing this method,
        # but RM690B0 still needs its QSPI-prefixed RAM-write command.
        if self._backup_set_memory_location is not None:
            self._set_memory_location = self._backup_set_memory_location
            self._backup_set_memory_location = None
            self._set_memory_location(
                self._offset_x, self._offset_y,
                self._offset_x + self.display_width - 1,
                self._offset_y + self.display_height - 1,
            )

    def set_params(self, command, params=None):
        self._data_bus.tx_param(_param_command(command), params)

    def _set_memory_location(self, x1, y1, x2, y2):
        buf = self._param_buf
        buf[0] = x1 >> 8
        buf[1] = x1 & 0xFF
        buf[2] = x2 >> 8
        buf[3] = x2 & 0xFF
        self.set_params(_CASET, self._param_mv)
        buf[0] = y1 >> 8
        buf[1] = y1 & 0xFF
        buf[2] = y2 >> 8
        buf[3] = y2 & 0xFF
        self.set_params(_RASET, self._param_mv)
        return _color_command(_RAMWR)

    def _on_size_change(self, _event):
        rotation = self._disp_drv.get_rotation()
        self._width = self._disp_drv.get_horizontal_resolution()
        self._height = self._disp_drv.get_vertical_resolution()
        if rotation == self._rotation:
            return
        self._rotation = rotation
        if self._initilized:
            self._param_buf[0] = self._madctl(
                self._color_byte_order, self._ORIENTATION_TABLE, ~rotation
            )
            self.set_params(_MADCTL, self._param_mv[:1])

    def set_brightness(self, percent):
        percent = max(0, min(100, percent))
        self._brightness = percent
        self._param_buf[0] = int(percent * 255 / 100)
        self.set_params(_WRDISBV, self._param_mv[:1])

    def get_brightness(self):
        return self._brightness
