# Powerup snapshot validation (2026-09-11)

Built with `scripts/build_chromium_rl.sh` using the existing toolchain, no system install.
The schema2 extension is read-only; seeded-reset-v3 physics and score rules are unchanged.

Reproduction command normalized to the standalone checkout and `.venv`:

```bash
RUN_CHROMIUM_GUI_TESTS=1 .venv/bin/python -m unittest discover -s tests -v
```

Native repository regression: 13 tests passed, including the new wire integration test.
It validates nonempty real powerups, unique positive IDs, per-tick vertical displacement,
read-only snapshot/render and identical seeded reset traces. Existing reset, actions,
transport and rendering regressions also passed.

The consuming runtime separately validates ID non-reuse after disappearance, reset,
and matching traces with per-tick rendering enabled/disabled. The new typed decoder
requires the advertised capability and rejects malformed fields and duplicate IDs.

These are real display-dependent game tests; render-free stepping is not headless.
Tests exercise naturally spawned items, not an exhaustive forced test of every pickup
or every powerup type. Scoring and collision event attribution are not added by this change.
