# Read-only snapshot verification — 2026-09-07

## Scope

Validate C++→JSON→typed Python state and process lifecycle. No DQN, seeds, fixed-step simulation or acceleration. Use one GUI instance at a time; default process state starts in the menu, with no synthetic game movement required.

## Reproduce

From this repository, using an existing Python 3.11+ virtual environment:

```bash
bash scripts/build_chromium_rl.sh
<venv>/bin/python -m pip install -e .
RUN_CHROMIUM_GUI_TESTS=1 <venv>/bin/python -m unittest discover -s tests -p 'test_*.py' -v
<venv>/bin/python examples/watch_snapshot.py
```

Environment: Linux x86_64, existing json-c 0.19; no new system library installed. Native automated checks selected X11 on a Wayland desktop. A separate default-driver client also completed hello/snapshot/close, without asserting which backend SDL chose.

## Observed results

- Build completed successfully. Editable Python package installed; dependency check passed in the development environment.
- Five unittest methods passed, including multiple fault subcases: normal response, recoverable command rejection, EOF, timeout, malformed JSON, oversized response, mismatched request ID and invalid state values.
- Native hello accurately reports live_snapshot=true, step/reset/headless/deterministic=false.
- Native menu snapshot: position `(0,-3,25)`, lives_counter `4`, score `0`, damage `-500`, shields `500`, ammunition `(0,0,0)`, no enemies; a second menu read matched.
- Requesting unsupported step produced a structured error; the connection remained usable for another snapshot.
- Protocol close and parent-pipe EOF both produced native exit code 0. No keyboard or input-method state was needed. Python close was safe to call twice.
- Debug logging was enabled in one native test and did not corrupt the JSON channel. Faulted clients reaped their owned processes.

## Boundaries

These tests establish menu-state reads and cleanup, not full active-game field coverage. Human play versus live coordinates/enemy list was not independently verified in this record. Raw damage is not health, raw enemy velocity is not universally full movement, and list order is not a stable object ID.

No artifacts or private desktop images are included. Native request-parser coverage is currently hello/unsupported-command/close plus EOF; future work should extend malformed-request and stress coverage. Next implementation milestone is explicit action and deterministic single-tick advancement.
