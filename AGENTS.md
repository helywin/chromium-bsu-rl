# Standalone engineering repository

- Treat work here as game/runtime engineering, not a lesson. Do not apply the consuming course's teaching skill or generate learner exercises in this repository.
- Preserve upstream notices and document local behavior changes. No system installation or HOME override; use isolated process state.
- Use the consuming project's virtual environment or an explicitly provided standalone venv. Keep the Python API typed.
- Build with scripts/build_chromium_rl.sh. Generated builds, models and logs stay under ignored build/ or artifacts/.
- Validate native behavior, not just Python mocks. Keep rendered/display-dependent, render-free and truly headless evidence distinct.
- Do not describe raw snapshots as a complete policy observation, and do not claim training or full-game completion from interface tests.
