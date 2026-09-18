"""Runs before main.py and leaves evidence even when application import fails."""

import os
import sys

from debug_log import log, reset_log


reset_log()
log("boot.py started")
log("MicroPython: %r" % (sys.implementation,))
try:
    log("filesystem root: %s" % os.listdir("/"))
except Exception as error:
    log("filesystem listing failed: %r" % error)
log("boot.py complete; loading main.py")
