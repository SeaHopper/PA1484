"""Minimal upstream-LVGL hardware setup for LilyGO T4-S3."""

from machine import Pin, SPI
import lcd_bus
import lvgl as lv
import i2c
import t4s3_rm690b0 as rm690b0
import cst226
import task_handler
from debug_log import log


def start_board():
    log("board: enabling AMOLED")
    Pin(9, Pin.OUT, value=1)  # AMOLED enable

    log("board: configuring four-lane SPI3 at 36 MHz")
    spi_bus = SPI.Bus(
        host=2,
        sck=15,
        quad_pins=(14, 10, 16, 12),  # data0, data1, data2, data3
    )
    display_bus = lcd_bus.SPIBus(
        spi_bus=spi_bus,
        dc=-1,
        cs=11,
        freq=36_000_000,
        quad=True,
    )
    display = rm690b0.RM690B0(
        data_bus=display_bus,
        display_width=600,
        display_height=450,
        reset_pin=13,
        power_pin=9,
        offset_y=16,
        color_space=lv.COLOR_FORMAT.RGB565,
        rgb565_byte_swap=True,
    )
    display.set_power(True)
    display.init()
    log("board: RM690B0 initialized at 600x450")

    log("board: configuring CST226 on I2C0")
    i2c_bus = i2c.I2C.Bus(host=0, scl=7, sda=6, freq=400_000)
    touch_device = i2c.I2C.Device(
        bus=i2c_bus, dev_id=cst226.I2C_ADDR, reg_bits=cst226.BITS
    )
    touch = cst226.CST226(device=touch_device, reset_pin=17,
                          swap_xy=True, mirror_y=True)
    handler = task_handler.TaskHandler()
    log("board: touch and LVGL task handler ready")
    return display, touch, handler
