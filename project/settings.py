"""Load and save the default settings."""

import json
import os

from departures import STOPS, TRANSPORT_TYPES

SETTINGS_PATH = "settings.json"
FACTORY_DEFAULTS = {"stop": "All stops", "transport_type": "All", "dark_mode": False}
STOP_OPTIONS = ("All stops",) + STOPS


def validate_settings(value):
    'Function: Checks that the settings contain valid values'
    if not isinstance(value, dict):
        raise ValueError("Settings must be an object")
    if value.get("stop") not in STOP_OPTIONS:
        raise ValueError("Unknown stop")
    if value.get("transport_type") not in TRANSPORT_TYPES:
        raise ValueError("Unknown transport type")
    if not isinstance(value.get("dark_mode"), bool):
        raise ValueError("Dark mode must be a boolean")
    return {key: value[key] for key in FACTORY_DEFAULTS}


def load_settings(path=SETTINGS_PATH):
    'Function: Loads saved settings or uses the starting defaults'
    try:
        with open(path, "r") as stream:
            return validate_settings(json.load(stream)), ""
    except OSError as error:
        if error.args and error.args[0] == 2:  # Filen finns inte ännu
            return dict(FACTORY_DEFAULTS), ""
        return dict(FACTORY_DEFAULTS), "Cannot read saved settings; using defaults"
    except (ValueError, TypeError):
        return dict(FACTORY_DEFAULTS), "Invalid saved settings; using defaults"


def save_settings(value, path=SETTINGS_PATH):
    'Function: Saves settings through a temporary file'
    validated = validate_settings(value)
    temporary = path + ".tmp"
    try:
        with open(temporary, "w") as stream:
            json.dump(validated, stream)
        # Använd replace på datorn och rename på MicroPython.
        replace = getattr(os, "replace", os.rename)
        replace(temporary, path)
    except OSError:
        try:
            os.remove(temporary)
        except OSError:
            pass
        raise
    return validated
