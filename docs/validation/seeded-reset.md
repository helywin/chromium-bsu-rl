# Seeded reset validation — 2026-09-10

Base source HEAD: `23a1a36ee286c27afea617e375f140bec10900c2` plus the uncommitted seeded-reset-v3 changes. No commit/push performed.
Rebuilt binary SHA256: `8b981d0ca665f4ccd13115490bc5749e06d62d1294b5121afe111099f9e20bfd`.

Commands from the standalone runtime repository (consuming virtualenv used):

```bash
bash scripts/build_chromium_rl.sh > build/seeded-reset-build.log 2>&1
RUN_CHROMIUM_GUI_TESTS=1 /home/jiang/code/legged_robot_rl/.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v > build/seeded-reset-tests.log 2>&1
/home/jiang/code/legged_robot_rl/.venv/bin/python scripts/check_reset_resources.py > build/seeded-reset-resources.json
```

Build passed. Final suite: 12 tests in 5.493 seconds, all passed, no skips;
8 native GUI integration tests and 4 transport/parser tests. Native tests use
X11/GL and no audio; not a visual-quality or true-headless acceptance.

New reset evidence:

- Seeds 7, 8, 7 in one process: 250 decisions of 10 ticks, movement/fire/idle;
  full exported snapshot/step traces for seed 7 equal; seed 8 differs.
  Traces contain enemies, bullets and positive scores (not only identical empty starts).
- Separate process with drawing each step reproduces the seed 7 trace from
  render-free stepping. Explicit render after reset leaves state unchanged.
- Seed 19 idle trajectory reaches terminal with reduced lives; step rejects
  continuation and reset restores initial state. Twenty subsequent dirty
  move/fire resets reproduce the initial snapshot, clear keyboard motion,
  and restart episode tick numbering. Total 0.363 seconds including actions.
- Seed range endpoints accepted. Negative, overflow, bool, float, string, null
  and missing seed rejected at protocol boundary without state mutation;
  Python caller validation checked separately. Live reset rejected.

Resource smoke: warm up 20 resets, then 200 resets with 10-tick move/fire steps.
Elapsed 3.2072421420016326 seconds; roughly 16 ms per reset-and-step pair.
RSS 158768 → 160684 KiB (+1916 KiB), file descriptors 12 → 12. Owned process
exited after close. This finite run meets the script's broad 32 MiB growth
bound; it is not a leak-detector result or proof of indefinitely bounded memory.

Limits: raw-state equality is tested on this build/platform/configuration and
these finite traces, not all seeds, collision branches, long-term policy
behavior, visual pixels, sound or cross-platform determinism. No native
multi-level completion or trained policy is claimed. First-level success and
all weapon/observation semantics still need their own task-specific checks.
