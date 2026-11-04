"""Demo departures used by the departure screen."""

from settings import TRANSPORT_TYPES

# Sample data only; these are not real departure times.
# Each row contains time, line, destination, status and transport type.
DEMO_DEPARTURES = (
    ("10:00", "1", "Campus Gräsvik", "Departed", "Bus"),
    ("10:05", "2", "Karlskrona Centralstation", "On time", "Bus"),
    ("10:10", "3", "Stortorget", "Delayed", "Bus"),
    ("10:15", "4", "Bergåsa", "On time", "Train"),
    ("10:20", "5", "Stumholmen", "Cancelled", "Ferry"),
    ("10:25", "1", "Campus Gräsvik", "On time", "Bus"),
    ("10:30", "2", "Karlskrona Centralstation", "Delayed", "Train"),
    ("10:35", "5", "Stumholmen", "On time", "Ferry"),
)


def get_demo_departures(transport_type="All"):
    """Return sample departures filtered by transport type."""
    if transport_type not in TRANSPORT_TYPES:
        raise ValueError("Unknown transport type")
    return [
        row for row in DEMO_DEPARTURES
        if (transport_type == "All" or row[4] == transport_type)
    ]
