# Headless runtime and request latency validation — 2026-09-11

## Change and scope

Opt-in synchronous `CHROMIUM_BSU_RL_HEADLESS=1` / `GameClient(..., headless=True)`
skips SDL video/window/GL context, texture/font loading and the audio backend.
Gameplay constructors and simulation updates remain active. Rendering is rejected.
Replaced the sync loop's fixed 2 ms sleep with stdin polling that wakes on requests.
No simulator tick duration, collision, reward, reset or action semantics were changed.
The gameplay implementation ID stays seeded-reset-v3; headless is an explicit capability.

## Reproduction

From consuming workspace `/home/jiang/code/legged_robot_rl`:

```bash
third_party/chromium-bsu-rl/scripts/build_chromium_rl.sh
PYTHONPATH=third_party/chromium-bsu-rl RUN_CHROMIUM_GUI_TESTS=1 .venv/bin/python -m unittest discover -s third_party/chromium-bsu-rl/tests -v
```

15 tests passed. `test_headless.py` removes DISPLAY/WAYLAND_DISPLAY and supplies an
invalid SDL video driver: startup/reset/steps work because SDL video is never initialized.
It verifies real enemy bullets appear, reset repeatability and rejected render requests
leave the snapshot unchanged. A separate GUI test compares seeded full trajectories.

Also compared the preserved pre-change binary `/tmp/chromium-bsu-rl-before-speed`
against new GUI and headless runs for seeds7/8/209, actions cycling right-fire,
left-fire, fire, idle every12 decisions,10 ticks per step, up to250 decisions or terminal.
All raw snapshots/step results matched exactly (104/100/110 entries including reset).
The temporary old binary and build/test logs are local evidence, not committed artifacts.

## Throughput boundary

The consuming DQN project separately optimizes replay storage/logging and supports
N independent game processes. A 4000-update old single-environment run took9.902s;
new 1/4/8-environment median times over3 trials were2.337/2.212/2.131s. These are
combined Python/native improvements, not a claimed isolated native speedup.
Old/new single-environment final weights matched exactly. Changing N changes sampling
order and policy-update timing, so N-way policy quality needs separate assessment.
See consuming experiment `experiments/2026-09-11-chromium-training-throughput/`.

No Xvfb, display server, GPU context, dependency installation or driver changes were
used in headless tests. The executable still links GUI libraries. This is a tested
runtime mode, not a new graphics-free build or a trained-game success claim.
