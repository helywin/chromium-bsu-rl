# Installation and troubleshooting

[English](installation.md) | [简体中文](installation.zh-CN.md) · [Home](../README.md)

## Supported workflow

Linux/POSIX, Bash, Python 3.11+ and a C++ toolchain are required. Ubuntu 24.04
is the reference container and CI environment. Other Linux distributions need
equivalent development packages. On Windows, build inside WSL2 or use the Linux
Docker image; the client uses POSIX pipes. Native Windows, macOS and other CPU
architectures are not currently validated.

## Prerequisites

Tools: `g++`, `make`, Autoconf, Automake, `autopoint`, gettext (`msgfmt`),
`pkg-config`. Libraries: SDL2, SDL2_image, OpenGL, GLU, FTGL, Fontconfig, OpenAL,
freealut, **json-c >= 0.15**. Headless execution still links these libraries.

On an Ubuntu 24.04 machine you administer, prepare the following packages.
These commands install system packages; the build script does not run them.
Use Docker below to keep dependencies inside a container.

```bash
sudo apt-get update
sudo apt-get install --no-install-recommends \
  build-essential autoconf automake autopoint gettext pkg-config \
  libsdl2-dev libsdl2-image-dev libgl1-mesa-dev libglu1-mesa-dev libftgl-dev \
  libfontconfig1-dev libopenal-dev libalut-dev libjson-c-dev \
  python3 python3-venv ca-certificates fonts-dejavu-core
```

Display tests in a virtual X server additionally need `xvfb`, `xauth` and
`libgl1-mesa-dri`. True headless tests do not need a display server.

## Local build

```bash
git clone https://github.com/helywin/chromium-bsu-rl.git
cd chromium-bsu-rl
python3 -m venv .venv
.venv/bin/python -m pip install -e .
bash scripts/build_chromium_rl.sh
.venv/bin/python examples/headless_rollout.py --seed 7
```

An existing project venv also works. The build uses four jobs by default;
`CHROMIUM_RL_BUILD_JOBS=2` changes this. Autotools runs in `build/work.*`, and the
executable goes to `build/install/bin/chromium-bsu-rl`. Build copies are retained
for diagnosis; old copies can be removed after confirming no build uses them.

Rebuild after updating native code or moving the checkout: the native installation
contains absolute paths. Keep paths short; the upstream code has fixed buffers,
and the client rejects asset paths of 180 bytes or more. Match the checkout,
binary and client revision. Installing Python code does not compile the game.

## Runtime modes

| Mode | Constructor | Requirements |
| --- | --- | --- |
| Human play and live inspection | `GameClient()` | Display/OpenGL; real time, starts in menu |
| Draw every synchronous tick | `GameClient(synchronous=True)` | Display/OpenGL; starts first level |
| Draw only on request | `GameClient(synchronous=True, render_each_step=False)` | Hidden SDL/GL window; `render()` shows current state |
| True headless | `GameClient(synchronous=True, render_each_step=False, headless=True)` | No display or GL context; no `render()` |

All client modes disable sound and use temporary preferences/high scores cleaned
on close. Use a context manager. The GUI shell launcher instead uses `build/state/`.
Neither overrides `HOME`. Direct binary execution without the isolation environment
follows upstream user-directory behavior; normally use the client or launcher.

## Docker

```bash
docker build -t chromium-bsu-rl:local .
docker run --rm --init --network none chromium-bsu-rl:local
docker run --rm --init --network none chromium-bsu-rl:local \
  .venv/bin/python examples/headless_rollout.py --seed 209 --steps 300
docker run --rm --init --network none chromium-bsu-rl:local \
  .venv/bin/python -m unittest discover -s tests -v
```

This source/development image runs as UID 10001. Building needs package repository
access; the shown runs disable networking. `docker build --build-arg BASE_IMAGE=...`
can select an equivalent Ubuntu 24.04 base. No host display mounts are needed.

To exercise the display path:

```bash
docker run --rm --init --network none -e RUN_CHROMIUM_GUI_TESTS=1 \
  -e LIBGL_ALWAYS_SOFTWARE=1 chromium-bsu-rl:local \
  xvfb-run -a .venv/bin/python -m unittest discover -s tests -v
```

Xvfb is a display server. This is neither true headless nor manual desktop verification.

## Use from another project

A Git submodule pins a source revision. Use your consuming project's Linux venv:

```bash
git submodule add https://github.com/helywin/chromium-bsu-rl.git third_party/chromium-bsu-rl
bash third_party/chromium-bsu-rl/scripts/build_chromium_rl.sh
python -m pip install -e third_party/chromium-bsu-rl
```

After cloning the consumer, initialize with `git submodule update --init --recursive`.
For a wheel, run in this repository's venv:

```bash
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m build
.venv/bin/python -m twine check dist/*
.venv/bin/python scripts/check_distribution.py
```

Install the actual generated wheel into the consumer using
`python -m pip install /absolute/path/to/the.whl`, then pass native paths:

```python
from pathlib import Path
from chromium_rl import GameClient

runtime = Path("/absolute/path/to/chromium-bsu-rl")
with GameClient(binary=runtime / "build/install/bin/chromium-bsu-rl",
                data_directory=runtime / "game/data",
                synchronous=True, render_each_step=False, headless=True) as game:
    print(game.reset(7).player.position)
```

The wheel ships Python code, `py.typed` and notices, with no native executable
or game assets. The source distribution includes game source/assets, scripts,
examples and docs and can serve as an independent build tree. These commands
do not assume a PyPI publication or a precompiled game release.

## Troubleshooting

| Symptom | Next step |
| --- | --- |
| Missing tool or pkg-config library | Prepare its development package; json-c must be >= 0.15 |
| Missing executable or capability | Rebuild in the same checkout as the client |
| Missing assets after wheel installation | Pass absolute `binary` and `data_directory` paths; data must contain `png/` |
| SDL video / GL initialization error | Use headless mode, or verify the display and GL drivers |
| Wayland backend problem | Try `SDL_VIDEODRIVER=x11 bash scripts/run_gui.sh` with XWayland; native Wayland remains unverified |
| `render()` fails in headless mode | Start a GUI client; the mode is fixed at construction |
| `episode_ended` | Preserve the terminal state, then call `reset(seed)` |
| `ProtocolError` | Read its game-log tail; match build versions and create a new client after failure |
| Different results for the same seed | Match commit, platform, configuration and actions/ticks; cross-platform identity is not promised |

See [contribution checks](../CONTRIBUTING.md). When reporting bugs, include the
commit, exact command, runtime mode and error log.
