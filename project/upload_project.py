"""Build and flash the complete application from a terminal (desktop Python).

    py -3 project\\upload_project.py                  # find the board automatically
    py -3 project\\upload_project.py --port COM5      # or name the port
    py -3 project\\upload_project.py --with-firmware  # new board: also install MicroPython
    py -3 project\\upload_project.py --build-only     # build without a board

The PlatformIO Upload button in VS Code does the same thing (always with firmware).
"""

import argparse
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIO_HOME = Path.home() / ".platformio"


def flash_command(python, esptool, port, offset, image, firmware=None):
    command = [str(python), str(esptool), "--chip", "esp32s3", "--port", port,
               "--baud", "115200", "--before", "no_reset", "--after", "hard_reset",
               "write_flash", "--flash_mode", "keep", "--flash_size", "keep"]
    if firmware is not None:
        command.extend(["0x0", str(firmware)])
    command.extend([hex(offset), str(image)])
    return command


def first_existing(*paths):
    return next((str(path) for path in paths if path.exists()), None)


def main():
    parser = argparse.ArgumentParser(description="Build/flash the complete PA1484 application")
    parser.add_argument("--port", help="Serial port, e.g. COM5 (found automatically if left out)")
    parser.add_argument("--with-firmware", action="store_true", help="Also install the MicroPython firmware")
    parser.add_argument("--build-only", action="store_true", help="Build without touching a device")
    args = parser.parse_args()

    pio = (shutil.which("pio") or shutil.which("platformio") or first_existing(
        PIO_HOME / "penv/Scripts/platformio.exe", PIO_HOME / "penv/bin/platformio"))
    if pio is None:
        raise SystemExit("Install/open the PlatformIO IDE extension first, then retry")
    subprocess.run([pio, "run", "--project-dir", str(ROOT), "-t", "build_app_fs"], check=True)
    image = ROOT / "device-build/t4s3-vfs.img"
    if not image.exists():
        raise SystemExit("The filesystem image was not produced")
    if args.build_only:
        print("Built:", image)
        return

    esptool = PIO_HOME / "packages/tool-esptoolpy/esptool.py"
    if not esptool.exists():
        raise SystemExit("PlatformIO's esptool was not found in " + str(esptool.parent))
    # PlatformIO's Python has pyserial, which esptool and board_port need.
    python = first_existing(PIO_HOME / "penv/Scripts/python.exe",
                            PIO_HOME / "penv/bin/python") or sys.executable
    port_finder = [python, str(ROOT / "platformio/board_port.py")]
    if args.port:
        port_finder.append(args.port)
    port = subprocess.run(port_finder, check=True, stdout=subprocess.PIPE,
                          text=True).stdout.strip().splitlines()[-1]

    firmware = ROOT / "firmware/t4s3-lvgl-micropython.bin"
    spec = importlib.util.spec_from_file_location("firmware_layout", ROOT / "platformio/firmware_layout.py")
    layout = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(layout)
    offset, size = layout.find_vfs_partition(firmware)
    if image.stat().st_size != size:
        raise SystemExit("Filesystem size does not match the firmware's partition")
    print("Uploading on %s - this takes a few minutes, do not unplug." % port)
    print("Note: saved settings on the board are replaced by the defaults.")
    subprocess.run(flash_command(python, esptool, port, offset, image,
                                 firmware if args.with_firmware else None), check=True)
    print("Upload complete. The board restarts by itself.")


if __name__ == "__main__":
    main()
