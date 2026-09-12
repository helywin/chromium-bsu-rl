# Chromium B.S.U. for RL

**English** | [简体中文](README.zh-CN.md)

[CI: tag pushes only](.github/workflows/ci.yml)

Control the Chromium B.S.U. arcade shooter from Python. Run seeded simulation
steps without a display, inspect typed game state, or watch the same runtime in
its native game window.

An independent, unofficial adaptation of **Chromium B.S.U. 0.9.16.1**, this
project provides a C++ game runtime and a dependency-free Python client for
experiments, tools and third-party integrations.

## What works today

| Capability | Status |
| --- | --- |
| Live native window and read-only snapshots | Available |
| 18 movement/fire actions; 1–50 ticks per request | Available; 0.02 simulated seconds per tick |
| Seeded reset in the same process | Available; first level only |
| True headless execution | Available; no display server, window or GL context |
| Rendering on demand | Available in a display-dependent mode |
| Typed player, enemy, bullet and powerup state | Available |
| Cumulative combat, damage, pickup and life-loss events | Available |
| Gymnasium environment, reward and observation encoding | Not implemented |
| Full-game task, trained policies and learning benchmarks | Not provided |

The project is **alpha**. Seed repeatability is scoped to the same native build,
platform and configuration. Raw snapshots are variable-length game state, not a
complete policy observation. Read the [API contract](docs/api.md) before using
fields as learning inputs or rewards.

## Quick start

The source workflow targets **Linux with Python 3.11+**. On Windows, run these
commands inside WSL2, or use Docker below. Native Windows and macOS builds are
not supported by this workflow.

Prepare the [build prerequisites](docs/installation.md#prerequisites), then:

```bash
git clone https://github.com/helywin/chromium-bsu-rl.git
cd chromium-bsu-rl
python3 -m venv .venv
.venv/bin/python -m pip install -e .
bash scripts/build_chromium_rl.sh
.venv/bin/python examples/headless_rollout.py --seed 7
```

The example runs a bounded scripted action sequence and prints JSON containing
the native implementation, simulation ticks, final score and episode events.
It stops at the first-level terminal state or its decision limit. It does not
train a policy. A successful run exits with code 0 and leaves no game process.

The build script checks existing dependencies and writes only to `build/`;
it does not install system packages. Each client owns an isolated temporary
configuration and score directory.

### Use it from Python

```python
from chromium_rl import Action, GameClient

with GameClient(synchronous=True, render_each_step=False, headless=True) as game:
    initial = game.reset(seed=7)
    for _ in range(200):
        result = game.step(Action.RIGHT_FIRE, ticks=5)
        state = result.snapshot
        print(result.episode_tick, state.player.score, state.episode_events)
        if result.terminated:
            break
```

Call `reset(seed)` before a repeatable run. A terminal episode stays frozen until
explicitly reset. Actions hold a complete button state; `IDLE` releases buttons
and preserves the original movement decay.

### Watch the native game

With a working desktop display and OpenGL:

```bash
bash scripts/run_gui.sh                         # Play through the game menu
.venv/bin/python examples/watch_snapshot.py     # Inspect state while you play
.venv/bin/python examples/watch_steps.py        # Watch a seeded action sequence
.venv/bin/python examples/watch_enemy_bullets.py
```

For occasional rendering use `GameClient(synchronous=True,
render_each_step=False)` and `game.render()`. This still creates an SDL/GL
context. A headless client cannot later open a window; create a GUI client for
playback. [Modes and troubleshooting](docs/installation.md).

### Run with Docker

From the cloned repository, with a Linux container engine:

```bash
docker build -t chromium-bsu-rl:local .
docker run --rm --init --network none chromium-bsu-rl:local
```

The development image contains the source, native runtime and Python venv. Its
default command runs the headless example as a non-root user. Building requires
network access; running the example does not. No prebuilt project image is
required. [More container commands](docs/installation.md#docker).

## Integrate with another project

Use an editable checkout, a pinned Git submodule, or build a Python wheel.
The wheel contains the **Python client only**; provide the separately built game
and assets through `binary=Path(...)` and `data_directory=Path(...)`.
Installing the Python package does not compile the game.

[Installation and packaging](docs/installation.md#use-from-another-project)
includes complete commands. Pin a repository commit for reproducibility;
Python package, wire schema and game behavior versions have separate meanings.

## Documentation and development

| Guide | English | 简体中文 |
| --- | --- | --- |
| Installation, Docker, packaging, troubleshooting | [Read](docs/installation.md) | [阅读](docs/installation.zh-CN.md) |
| Python API, actions and state semantics | [Read](docs/api.md) | [阅读](docs/api.zh-CN.md) |
| JSON-lines protocol for other languages | [Read](docs/protocol.md) | [阅读](docs/protocol.zh-CN.md) |
| Architecture and roadmap | [Read](docs/architecture.md) | [阅读](docs/architecture.zh-CN.md) |
| Contributing and verification | [Read](CONTRIBUTING.md) | [阅读](CONTRIBUTING.md#简体中文) |

[Documentation index and evidence](docs/README.md) · [Changelog](CHANGELOG.md) ·
[Report an issue](https://github.com/helywin/chromium-bsu-rl/issues) · [Security](SECURITY.md)

English and Chinese contributions are welcome. CI runs only on tag pushes and separates Python checks,
native headless tests, and SDL/OpenGL tests under Xvfb. Xvfb exercises the display
path; it is not manual desktop or native Wayland acceptance. Branch pushes and
pull requests do not start CI; use the local contribution checks during development.

## Upstream and licensing

Chromium B.S.U. was created by its [upstream authors](game/AUTHORS). The game
retains its [Clarified Artistic License](game/COPYING), and sound assets retain
their [MIT/Expat notice](game/data/wav/license.txt). Original additions use the
Clarified Artistic License unless a file says otherwise; embedded third-party
notices remain in place. This project does not replace upstream licenses or
claim upstream endorsement.

[License scope](LICENSE.md) · [Source provenance](game/UPSTREAM.md) ·
[Local game changes](game/LOCAL_CHANGES.md) · [Original project](https://chromium-bsu.sourceforge.net/)
