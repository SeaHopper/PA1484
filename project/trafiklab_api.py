"""Trafiklab requests for the board and host tests."""

def quote(value):
    # URL-koda även å, ä och ö utan urllib.
    result = ""
    for byte in str(value).encode("utf-8"):
        if (65 <= byte <= 90 or 97 <= byte <= 122 or
                48 <= byte <= 57 or byte in (45, 46, 95, 126)):
            result += chr(byte)
        else:
            result += "%%%02X" % byte
    return result


class TrafiklabAPI:
    def __init__(self, api_key, get=None):
        self.api_key = api_key
        self.get = get

    def read_json(self, path):
        if not self.api_key or self.api_key == "YOUR_API_KEY":
            raise RuntimeError("Add TRAFIKLAB_API_KEY to secrets.py")
        response = None
        try:
            get = self.get
            if get is None:
                try:
                    import requests
                except ImportError:
                    try:
                        import urequests as requests
                    except ImportError:
                        from vendor import requests
                get = requests.get
            url = "https://realtime-api.trafiklab.se/v1/" + path
            response = get(url + "?key=" + quote(self.api_key), timeout=10)
            if response.status_code != 200:
                raise RuntimeError("Trafiklab HTTP %s" % response.status_code)
            data = response.json()
            if not isinstance(data, dict):
                raise ValueError("Invalid API response")
            return data
        except (OSError, ValueError):
            # Skriv aldrig ut URL:en eller nyckeln i felmeddelanden.
            raise RuntimeError("Could not read Trafiklab data")
        finally:
            if response is not None:
                response.close()

    def fetch_departures(self, stop_id):
        stop_id = str(stop_id)
        if not stop_id.isdigit():
            raise ValueError("Invalid stop ID")
        data = self.read_json("departures/" + stop_id)
        if not isinstance(data.get("departures"), list):
            raise ValueError("Missing departures in response")
        return data

    def search_stops(self, query):
        query = query.strip()
        if len(query) < 3:
            raise ValueError("Enter at least 3 letters")
        data = self.read_json("stops/name/" + quote(query))
        groups = data.get("stop_groups")
        if not isinstance(groups, list):
            raise ValueError("Invalid stop search response")
        stops = []
        seen = set()
        for group in groups:
            if not isinstance(group, dict):
                continue
            stop_id = str(group.get("id") or "")
            name = group.get("name")
            if not stop_id.isdigit() or not isinstance(name, str) or not name.strip():
                continue
            # LVGL separates dropdown options with newlines.
            name = " ".join(name.split())
            if stop_id in seen:
                continue
            stops.append({"id": stop_id, "name": name})
            seen.add(stop_id)
        return stops
