"""Save the selected Trafiklab stop, transport type and theme."""

import json
import os

TRANSPORT_TYPES = ("All", "Train", "Bus", "Ferry")
FACTORY_DEFAULTS = {
    "stop_id": "740000230",
    "stop_name": "Karlskrona Centralstation",
    "transport_type": "All",
    "dark_mode": True,
    "live_mode": True,
}


def validate_settings(value):
    if not isinstance(value, dict):
        raise ValueError("Invalid settings")
    stop_id = value.get("stop_id")
    name = value.get("stop_name")
    if not isinstance(stop_id, str) or not stop_id.isdigit():
        raise ValueError("Invalid stop ID")
    if not isinstance(name, str) or not name.strip() or len(name) > 200:
        raise ValueError("Invalid stop name")
    if value.get("transport_type") not in TRANSPORT_TYPES:
        raise ValueError("Invalid transport type")
    for option in ("dark_mode", "live_mode"):
        if not isinstance(value.get(option), bool):
            raise ValueError("Invalid setting: " + option)
    return {key: value[key] for key in FACTORY_DEFAULTS}


def load_settings(path="settings.json"):
    missing = False
    try:
        with open(path, "r") as file:
            return validate_settings(json.load(file)), ""
    except OSError as error:
        missing = bool(error.args and error.args[0] == 2)
    except (ValueError, TypeError):
        pass
    # En tidigare giltig fil kan användas om senaste sparningen avbröts.
    try:
        with open(path + ".bak", "r") as file:
            return validate_settings(json.load(file)), "Recovered previous saved settings"
    except (OSError, ValueError, TypeError):
        return dict(FACTORY_DEFAULTS), ("" if missing else
            "Old or invalid settings; using defaults")


def save_settings(value, path="settings.json"):
    value = validate_settings(value)
    temporary = path + ".tmp"
    try:
        previous = None
        try:
            with open(path, "r") as file:
                previous = validate_settings(json.load(file))
        except (ValueError, TypeError):
            pass
        except OSError as error:
            if not error.args or error.args[0] != 2:
                raise
        if previous is not None:
            with open(path + ".bak", "w") as file:
                json.dump(previous, file)
        with open(temporary, "w") as file:
            json.dump(value, file)
        replace = getattr(os, "replace", os.rename)
        replace(temporary, path)
    except OSError:
        try:
            os.remove(temporary)
        except OSError:
            pass
        raise
    return value
