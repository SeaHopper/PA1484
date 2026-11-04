# Public Transport Information and Interaction on ESP32

PA1484, Group 22. Version 0.1, October 2026.

We built a departure board for the LilyGO ESP32-T4-S3 using MicroPython and LVGL.
You can search for any stop in Sweden, see live departures from Trafiklab, filter
by transport type and save your choices so they are still there after a restart.
There is also a demo mode with made-up departures.

We have tested the code on a computer. Testing on the board with live data is
still left to do (see TESTING.md).

## Files

- `main.py` – the app itself: the three screens, the search keyboard, the departure table and what happens when you press things.
- `departures.py` – our parser. It picks out time, line, destination and status from the Trafiklab data, filters by transport type and sorts by time.
- `trafiklab_api.py` – searches for stops and fetches departures. Stop names are URL-encoded so å, ä and ö work. The API key is not stored here.
- `network_job.py` – runs the API requests in the background so the screen does not freeze while waiting. Results for an old stop are thrown away.
- `settings.py` – saves and loads the selected stop, filter, theme and mode. It keeps a backup of the previous file in case a save is interrupted.
- `demo_departures.py` – the made-up departures used in demo mode.
- `departure_updates.py` – the refresh helper from our first version, retained for its tests.
- `vendor/` – an HTTP library for MicroPython, with its license.
- `upload_project.py` – builds and uploads the whole app to the board from a terminal (the VS Code Upload button does the same).
- `device_check.py` – lists which modules the board has. Does not read secrets.
- `tests/` – offline tests with small example responses from Trafiklab.

## Requirements

| Requirement | How we solved it | Still to check on the board |
| --- | --- | --- |
| Start screen with title, version, group and members | Start tile in main.py | Readable, right timing |
| Demo table with five destinations and four columns | demo_departures.py | Wrapping, scrolling, touch |
| Swipe between screens and open Settings | Three tiles and Settings buttons | Swiping over the table |
| Choose a stop | Search by name, save the stop ID and name | Search for different stops |
| Choose transport type | All/Bus/Train/Ferry (Ferry = BOAT in the API) | Live results for each type |
| Save defaults and keep them after restart | settings.py and Save defaults | Save, then power off and on |
| Reset to saved defaults | Reloads the saved settings | Everything updates together |
| Live data and refresh | API, parser, background job, update every 60 s | API key, network, memory |
| Show where the data comes from | Footer and license address in Settings | Readable on screen |
| Code standard and documentation | Four-space indentation, clear names, short comments | Review by the group |
| Skeleton files unchanged | Checked against the original files on GitHub | See SKELETON_VERIFICATION.json |
| Testing | 42 offline tests and a checklist in TESTING.md | Test on the board |

Stop search covers all of Sweden, so Karlskrona stops can be found by name.
If a live request fails, the app shows an error instead of switching to demo
data. Departures that only follow the timetable are shown differently from
realtime departures.

## Credits

We worked on this project together as a group. We used AI during testing to
help debug issues, identify their causes, and explore different ways to write
parts of the code, such as screen refresh. We reviewed the results and are
responsible for the finished project.

Data from Trafiklab.se, CC BY 4.0. We filter and format the departure data.
https://creativecommons.org/licenses/by/4.0/

Trafiklab API documentation:
https://www.trafiklab.se/api/our-apis/trafiklab-realtime-apis/stop-lookup/
https://www.trafiklab.se/api/our-apis/trafiklab-realtime-apis/timetables/

The firmware and skeleton keep their original license. See vendor/LICENSE.txt
for the HTTP library's license.

## Running the tests

From the project root:

    python -m unittest discover -s project/tests -v

See ../INSTRUCTIONS.md for setup and upload. Put your Wi-Fi details and API key
in a local `secrets.py` only. It is not committed to Git.
