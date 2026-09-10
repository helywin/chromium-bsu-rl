# Local changes

## 2026-09-07 — split-render-v2 and enemy bullets

- Single-level advanceSimulationTick and renderGameFrame are independent. Background, HUD, electric acceleration and super-shield particles advance in the tick path. Rendering preserves the gameplay RNG cursor using frame-indexed visual sampling; this changes RNG consumption relative to v1 and is explicitly versioned.
- Optional render_each_step=False uses a hidden SDL/GL window and skips per-tick draw/swap. Explicit render reveals current state with no tick. This is not true headless. Default-mode expose/resize can repaint without gameplay updates.
- Snapshot schema2 adds enemy_bullets (spawn ID, type, position, displacement/tick, sprite half-size, damage) and diagnostic rng_cursor. Pooled allocations get new IDs on reuse. No hero bullets are included.
- Enemy bullet source values and collision caveats are in docs/render-free-stepping.md.9 native/parser/transport methods and9563 draw/skip snapshot comparisons passed; types seen in trajectories:0.

## 2026-09-07 — drawable fix and initial rendering separation

- Fit the original game aspect ratio into actual SDL drawable pixels before drawing. Slow-window clipping was reported fixed by the learner; no game coordinate or speed change.
- Extract MainGL core update, hero visibility countdown and enemy retargeting into explicit methods, preserving the original combined-loop order. No render-free switch is exposed yet.
- Add developer-only fixed-epoch before/after comparison, never loaded by the game launcher. It is not a public seed API.
- Remaining background, HUD, particle and random-stream dependencies are tracked in docs/render-separation-audit.md; see it for validation boundaries.

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

## 2026-09-07 — synchronous GUI prototype (stage C partial)

- MainSDL/SnapshotBridge support opt-in fixed reference ticks and full held actions; native human mode remains available. Input now precedes update in synchronous mode, physical inputs are ignored, and no gameplay advances between commands.
- HeroAircraft::holdFire avoids resetting shot cooldown for repeated held actions. Repeated direction edges are likewise suppressed; release preserves keyboard decay.
- Original drawGL runs exactly once per tick because render paths still mutate gameplay/RNG. This is not yet separated rendering or headless acceleration. No seed/reset or full-game task is claimed.
- Python adds Action/StepResult and an optional synchronous constructor; snapshot schema1 remains unchanged. See docs/synchronous-step.md for explicit behavioral differences, termination and evidence.

## 2026-09-10: seeded-reset-v3

- Add synchronous `reset(seed)` with strict uint32 validation and initial schema2 snapshot response.
- Rebuild episode-owned game objects while retaining SDL window/GL context and process; reset native RNG tables, global counters and keyboard state.
- Reconstruct constructor-only state including score thresholds, weapon state, object pools, visual objects and per-episode bullet identity counters.
- Keep live mode behavior, protocol version 1 and snapshot schema 2; advertise reset/seed capability only where implemented. Universal determinism remains unclaimed.
- Add standalone client method and native repeated-seed/terminal/invalid-input/resource checks. See `docs/validation/seeded-reset.md`.
