# Testing and acceptance record

43 offline tests passed on 4 November 2026 using desktop Python. Syntax checks,
credential scanning and original skeleton hash checks were also performed.
The API key was not used. No board or live-API test result is claimed.

Run from the repository root:
python -m unittest discover -s project/tests -v

Coverage: representative real response parsing, sorting, cancellation priority,
timetable-only and malformed times, mode filtering, URL encoding, arbitrary
stop IDs, response cleanup, API errors, persistence and backup recovery,
sixty-second refresh, reconnect behavior, background thread/result failures,
UI method construction, stop selection/reset and stale-response rejection.
The bundled client's fixed-length/chunked response bodies and cleanup are
also checked. UI doubles do not render a screen or validate firmware bindings.

## Manual checks (all pending)

Record tester/date/firmware, expected result, actual result, pass/fail and defects.

| Check | Expected result |
| --- | --- |
| USB and upload | Correct port; upload succeeds without changing board files |
| Boot offline | Live mode shows a connection/API error; Demo remains selectable |
| Startup timer | Moves after 3 seconds; does not override user navigation |
| Tiles | Horizontal swipes reach all screens, including over the table |
| Demo | Eight rows, five destinations; Campus Gräsvik and Centralstation included |
| Table | Four readable columns; long destinations wrap; last row reachable |
| Stop search | Search a stop outside the original five; returned ID/name selected |
| Broad search | Over 20 matches prompts a narrower query |
| Keyboard | Text entry and result dropdown usable on the display |
| Live mode | Real response appears with attribution; never labelled demo |
| Filtering | All/Bus/Train/Ferry match API modes; empty result has a message |
| Refresh | Manual refresh and 60-second automatic update work |
| Stop change during request | Old-stop response never appears under the new name |
| Lost Wi-Fi | Shows error; restores access after hotspot returns and Refresh |
| Invalid key | Shows error without printing a key or substituting demo rows |
| Save/restart | Save stop, filter, theme/mode; RESET without reflash restores them |
| Save twice | Second save replaces the first on the device filesystem |
| Reset to saved | Unsaved changes revert; controls/table/theme agree |
| Backup recovery | Invalid primary settings recover the preceding saved values |
| Reflash | Team understands filesystem flashing can replace stored settings |
| Stability | Multiple searches/updates do not exhaust memory or freeze touch |
| Peer review | Teammate can explain the modules, callbacks and error handling |

Both the VS Code upload tasks and upload_project.py flash the complete
filesystem image (the original skeleton flashed only a 128 KB prefix).
Fixtures are deliberately small. Check package size again if adding large data
or documentation inside project/. Never put the 28 MB stop catalogue there.
Filesystem packaging verification is reported in PACKAGE-CHECKS.txt at the
package root. This is a host check, not a flash or hardware test.

## Current limitations

- Exact firmware bindings, heap usage, threading and actual TLS/network behavior
  require the supplied board. The dependency check only verifies module names.
- Upstream bundled TLS verification is disabled; this project has not configured
  CA certificate validation. Do not claim authenticated HTTPS was verified.
- A settings backup improves recovery but does not guarantee power-loss safety.
- Search supports names nationwide; it is not a certified Karlskrona municipal list.
- Planning documents, contribution statements and customer communication must
  be completed by the team; application code cannot establish those facts.
