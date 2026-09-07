# Local changes

## 2026-09-07 — source/build stage, no RL API yet

- Apply the two documented Arch patches: floating-point keyboard accumulation and OpenGL configure flag preservation.
- Config.cpp and HiScore.cpp accept `CHROMIUM_BSU_RL_STATE_DIR` for current and legacy preferences/score paths. The launcher always sets an isolated project directory and explicit score/data paths. No HOME override is used.
- Build via an ignored copy, install only below `build/install`, executable name `chromium-bsu-rl` via configure's program suffix.
- Always launch through `scripts/run_gui.sh` for isolation. Running the installed binary directly without the environment still follows upstream home-directory behavior.
- No step/reset protocol, deterministic time base, accelerated training or Python package has been implemented. Keyboard and game loop behavior otherwise remain at the upstream-plus-Arch baseline.
