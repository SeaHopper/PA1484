"""Turn a Trafiklab departures response into simple table rows."""

VALID_MODES = ("ALL", "BUS", "TRAIN", "BOAT")


def _time_hhmm(timestamp):
    """'2026-11-04T19:09:00' -> '19:09' ('--:--' if missing or malformed)."""
    if isinstance(timestamp, str) and len(timestamp) >= 16 and timestamp[10] == "T":
        return timestamp[11:16]
    return "--:--"


def _valid_time(timestamp):
    return timestamp if _time_hhmm(timestamp) != "--:--" else None


def _status(canceled, is_realtime, delay):
    if canceled:
        return "Inställd"
    if not is_realtime:
        return "Enligt tidtabell"
    if delay >= 60:
        return "Försenad"
    if delay <= -60:
        return "Tidigare"
    return "I tid"


def parse_departures(data, transport_mode="ALL", limit=None):
    """Return departures sorted by time, optionally filtered and limited."""
    if transport_mode not in VALID_MODES:
        raise ValueError("Unknown transport mode")
    if not isinstance(data, dict) or not isinstance(data.get("departures"), list):
        raise ValueError("Invalid Trafiklab departure data")
    if limit is not None and (type(limit) is not int or limit < 0):
        raise ValueError("Invalid departure limit")

    result = []
    for departure in data["departures"]:
        if not isinstance(departure, dict):
            continue
        route = departure.get("route") or {}
        if not isinstance(route, dict):
            continue
        mode = route.get("transport_mode") or "UNKNOWN"
        if transport_mode != "ALL" and mode != transport_mode:
            continue
        destination = route.get("destination")
        if not isinstance(destination, dict):
            destination = {}

        scheduled = _valid_time(departure.get("scheduled"))
        realtime = _valid_time(departure.get("realtime"))
        is_realtime = departure.get("is_realtime") is True and realtime is not None
        canceled = departure.get("canceled") is True
        delay = departure.get("delay") or 0
        if not isinstance(delay, (int, float)):
            delay = 0
        # A cancelled trip shows its timetable time; otherwise prefer realtime.
        shown_time = realtime if is_realtime and not canceled else scheduled
        shown_time = shown_time or scheduled

        result.append({
            "time": _time_hhmm(shown_time),
            "departure_datetime": shown_time,
            "scheduled_time": _time_hhmm(scheduled),
            "line": route.get("designation") or route.get("name") or "-",
            "destination": destination.get("name") or route.get("direction") or "Okänd",
            "transport_mode": mode,
            "status": _status(canceled, is_realtime, delay),
            "delay_seconds": delay,
        })

    result.sort(key=lambda item: item["departure_datetime"] or "9999")
    return result if limit is None else result[:limit]
