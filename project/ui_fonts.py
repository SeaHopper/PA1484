"""Load Latin-1 fonts, including Swedish letters, without changing firmware."""

import lvgl as lv
import fs_driver


def load_fonts():
    # Keep the driver and fonts alive for as long as the application runs.
    driver = lv.fs_drv_t()
    fs_driver.fs_register(driver, "S")
    small = lv.binfont_create("S:fonts/noto_20.bin")
    large = lv.binfont_create("S:fonts/noto_28.bin")
    if small is None or large is None:
        raise RuntimeError("Upload the fonts folder together with main.py")
    # Preserve LVGL's arrow/icon glyphs, which are not in the text font.
    small.fallback = lv.font_montserrat_20
    large.fallback = lv.font_montserrat_28
    return driver, small, large
