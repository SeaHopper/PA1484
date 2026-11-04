"""Find the T4-S3's USB serial port and wait for upload (download) mode.

The ESP32-S3 shows up with two different USB IDs:
  303A:1001  upload mode (ROM bootloader) - esptool can flash it
  303A:4001  the MicroPython app is running - esptool cannot flash it
Software cannot switch this board into upload mode, so if the app is running
we ask the user to press BOOT + RESET and wait until upload mode appears.
Bluetooth "serial" ports are never chosen.
"""

import sys
import time

from serial.tools import list_ports

ESPRESSIF_VID = 0x303A
UPLOAD_MODE_PID = 0x1001


def say(message):
    # stderr, so the message shows even when stdout (the port) is captured.
    print(message, file=sys.stderr, flush=True)


def espressif_ports():
    return [port for port in list_ports.comports() if port.vid == ESPRESSIF_VID]


def wait_for_upload_port(requested=None, timeout=180):
    """Return the port to flash, waiting for upload mode if needed."""
    asked = False
    deadline = time.time() + timeout
    while time.time() < deadline:
        ports = espressif_ports()
        ready = [port.device for port in ports if port.pid == UPLOAD_MODE_PID]
        if ready:
            # Upload mode often has a different COM number than the app
            # (e.g. COM6 -> COM5), so fall back to whichever board is ready.
            return requested if requested in ready else ready[0]
        if not asked:
            if ports or requested:
                say(">>> The board is running the app, not in upload mode.")
            else:
                say(">>> No T4-S3 board found. Connect it with a USB data cable.")
            say(">>> Hold BOOT, tap RESET, then release BOOT. Waiting...")
            asked = True
        time.sleep(0.5)
    raise SystemExit("Board did not enter upload mode. Close any serial monitor and retry.")


if __name__ == "__main__":
    # Used by project/upload_project.py: prints the port to flash.
    print(wait_for_upload_port(sys.argv[1] if len(sys.argv) > 1 else None))
