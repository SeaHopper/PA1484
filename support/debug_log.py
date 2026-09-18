"""Serial and persistent diagnostics for the course device template."""

import time


LOG_PATH = "/debug.log"


def reset_log():
    try:
        with open(LOG_PATH, "w") as stream:
            stream.write("[BOOT] diagnostic log started\n")
    except OSError:
        pass


def log(message):
    line = "[%010d] %s" % (time.ticks_ms(), message)
    print(line)
    try:
        with open(LOG_PATH, "a") as stream:
            stream.write(line + "\n")
    except OSError:
        pass
