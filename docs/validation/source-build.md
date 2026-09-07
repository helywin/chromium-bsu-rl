# Source/build baseline — 2026-09-07

## Question and scope

Can the pinned upstream release plus documented distribution fixes build and display a game window without replacing the system executable or changing existing user preferences?

One GUI instance at a time, no model training, no new dependency installation. This checks build/startup, not deterministic stepping or policy performance. Random seeds are not controlled at this stage.

## Commands

From the repository root:

```bash
bash -n scripts/build_chromium_rl.sh scripts/run_gui.sh
bash scripts/build_chromium_rl.sh
bash scripts/run_gui.sh --version
SDL_VIDEODRIVER=x11 bash scripts/run_gui.sh --debug
# A second, non-debug startup was also checked:
SDL_VIDEODRIVER=x11 bash scripts/run_gui.sh
```

Build: Linux x86_64, available system Autotools and C++ toolchain; SDL2 pkg-config 2.32.70, SDL2_image 2.8.12, FTGL 2.4.0. GUI: Wayland desktop with explicit X11 backend, Intel Mesa OpenGL 4.6 compatibility profile. Four build jobs, no system installation.

## Results

- Full configure, compile and repository-local install completed with exit code 0. Autotools reports deprecation warnings from legacy upstream macros; these do not mean the build failed.
- Version command reports Chromium B.S.U. 0.9.16.1. Executable is named `build/install/bin/chromium-bsu-rl`.
- SDL/OpenGL initialization completed. Menu and active gameplay screenshots were inspected; the scene showed the player and enemies. Screenshots were temporary local evidence, not published user desktop captures.
- Explicit window destruction in the first diagnostic run returned exit code 1; it is not evidence of a normal in-game exit.
- Synthetic letter-key exit attempts were inconclusive. An input method was active in the user's desktop environment and may affect letter input, but causality was not isolated. Do not infer that the game's quit handler is broken or that automated keyboard control works reliably.
- The second process was stopped using SIGTERM addressed to its verified PID; it exited 0 and saved preferences under the repository's `build/state/.chromium-bsu`.
- SHA256 checks before and after confirmed the existing system executable and existing user preferences unchanged. No pre-existing user score/legacy files were present at the checked paths; none were created there by these runs.
- Only repository-owned GUI processes were started/stopped. No build output, preferences, screenshots or model artifacts are committed.

## Not verified

Normal GUI close via the user's input method, native Wayland rendering, Python protocol, state snapshots, automatic reset, fixed seeds, deterministic ticks, acceleration, truly headless initialization, learned policies and ONNX export remain unverified.

Next stage: a read-only typed snapshot interface. Actions will eventually be protocol values, not synthetic desktop keystrokes, so training will not depend on input-method state.
