"""Demo departures used by the departure screen."""

TRANSPORT_TYPES = ("All", "Train", "Bus", "Ferry")
STOPS = ("Campus Gräsvik", "Karlskrona Centralstation", "Stortorget",
         "Bergåsa", "Stumholmen")

# Testdata, inte riktiga avgångstider.
# Tid, linje, destination, status, transportsätt.
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


def get_demo_departures(transport_type="All", stop=None):
    'Function: Filters demo departures by stop and transport type'
    if transport_type not in TRANSPORT_TYPES:
        raise ValueError("Unknown transport type")
    if stop is not None and stop not in STOPS:
        raise ValueError("Unknown stop")
    # Destinationer som visas för varje hållplats i demon.
    destinations = {
        None: STOPS,
        STOPS[0]: (STOPS[1], STOPS[2], STOPS[3]),
        STOPS[1]: (STOPS[0], STOPS[2], STOPS[3], STOPS[4]),
        STOPS[2]: (STOPS[0], STOPS[1], STOPS[4]),
        STOPS[3]: (STOPS[0], STOPS[1]),
        STOPS[4]: (STOPS[1], STOPS[2]),
    }
    return [
        row for row in DEMO_DEPARTURES
        if (transport_type == "All" or row[4] == transport_type)
        and row[2] in destinations[stop]
    ]
