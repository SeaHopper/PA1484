"""Run one network request at a time in a background thread.

The UI timer collects the result with take_result(); the worker never touches LVGL.
"""

import _thread

# HTTPS (TLS) needs more stack than MicroPython's small default thread
# stack. Too little stack crashes or locks up the board mid-request.
THREAD_STACK = 20 * 1024


class NetworkJob:
    def __init__(self):
        self.lock = _thread.allocate_lock()
        self.busy = False
        self.result = None

    def start(self, tag, function, *args):
        """Start function(*args) unless a job is running or unread. Returns True if started."""
        with self.lock:
            if self.busy or self.result is not None:
                return False
            self.busy = True
        try:
            try:
                _thread.stack_size(THREAD_STACK)
            except (AttributeError, ValueError):
                pass
            _thread.start_new_thread(self.run, (tag, function, args))
        except Exception:
            self.finish(tag, None, "Could not start request. Restart the device.")
        return True

    def run(self, tag, function, args):
        try:
            self.finish(tag, function(*args), "")
        except Exception:
            # Never show exception text: it could contain the API key.
            self.finish(tag, None, "Request failed. Check Wi-Fi and API key, then retry.")

    def finish(self, tag, value, error):
        with self.lock:
            self.result = (tag, value, error)
            self.busy = False

    def take_result(self):
        with self.lock:
            result, self.result = self.result, None
            return result
