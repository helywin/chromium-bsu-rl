# Local changes

## 2026-09-07 — source/build stage, no RL API yet

- Apply the two documented Arch patches: floating-point keyboard accumulation and OpenGL configure flag preservation.
- Config.cpp and HiScore.cpp accept `CHROMIUM_BSU_RL_STATE_DIR` for current and legacy preferences/score paths. The launcher always sets an isolated project directory and explicit score/data paths. No HOME override is used.
- Build via an ignored copy, install only below `build/install`, executable name `chromium-bsu-rl` via configure's program suffix.
- Always launch through `scripts/run_gui.sh` for isolation. Running the installed binary directly without the environment still follows upstream home-directory behavior.
- No step/reset protocol, deterministic time base, accelerated training or Python package has been implemented. Keyboard and game loop behavior otherwise remain at the upstream-plus-Arch baseline.

## 2026-09-07 — live snapshot stage

- Add optional POSIX JSON-lines bridge using system json-c >=0.15, initialized before startup logging. Native loop services hello/snapshot/close at iteration boundaries without replacing the real-time game loop.
- Const enemy traversal avoids mutating EnemyFleet's shared iteration cursor. Snapshot field sources and limitations are documented in docs/protocol.md.
- Add independently installable, typed Python client and fault-injection/native checks. Per-client state is temporary and isolated. The close command and EOF exit without desktop keystrokes.
- The earlier build-stage statement about no Python package is superseded; step/reset, fixed logic time and acceleration are still absent.
