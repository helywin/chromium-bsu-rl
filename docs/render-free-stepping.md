# Render-free stepping and enemy bullets (split-render-v2)

The synchronous single-level path now separates complete state updates from drawing. This is **not true headless**: native startup still creates an SDL window, GL context and textures and therefore needs a display service. Human-mode menus and terminal transitions are not a render-free full-game environment.

## Usage

~~~python
from chromium_rl import Action, EnemyBulletState, GameClient

with GameClient(synchronous=True, render_each_step=False) as game:
    result = game.step(Action.IDLE, ticks=10)
    for bullet in result.snapshot.enemy_bullets:
        print(bullet.id, bullet.position, bullet.velocity_per_tick)
    state = game.render()  # show current state; advances zero ticks
~~~

render_each_step=False starts with a hidden window and performs no frame drawing or swaps in step. Calling render explicitly shows the window. The normal default renders every tick. Step remains1..50 complete internal ticks, speedAdj=1, reference time0.02s/tick. No wall-clock FPS adaptation, collision skipping, or hidden automatic reset. Closing/EOF still exits the owned process.

render returns a current snapshot and works before the first tick and after single-level termination. It does not decrement visibility, advance HUD timers, create particles, move bullets, retarget enemies or advance the gameplay RNG cursor. The default rendered window can redraw on expose/resize while idle without a simulation update. Actual drawable pixel dimensions retain the corrected original-aspect viewport.

## Implementation and compatibility

MainGL::advanceSimulationTick runs core gameplay, background scrolling/recycling, targeting, visibility, electric particle acceleration and HUD animation/particle generation. MainGL::renderGameFrame only draws the resulting state. The latter saves the gameplay random cursor, uses a frame-indexed cursor into the same immutable random tables for visual rotations, and restores the gameplay cursor afterwards.

This is a **versioned random-stream behavior change**: older combined rendering consumed gameplay random numbers. Draw/skip equivalence is tested within split-render-v2, not asserted between v1 and v2. Background recycling and HUD/particle rendering order can also differ visually from the old combined path. No existing checkpoint compatibility guarantee is provided.

hello implementation is now chromium-bsu-rl/seeded-reset-v3 (render separation was introduced in split-render-v2); envelope protocol_version remains1, snapshot schema_version is2. In synchronous mode render and render_free_steps capabilities are true; enemy_bullets is true in both modes. reset/seed are now available in synchronous mode; headless/deterministic remain false. See [seeded reset](protocol.md#seeded-first-level-reset-seeded-reset-v3). Old Python clients that only accept schema1 must be updated; the new parser still accepts old schema1, but its enemy_bullets capability is false for old native builds.

## Enemy bullet contract

enemy_bullets is an immutable Python tuple of EnemyBulletState, copied from the five EnemyAmmo active lists only. It does not contain hero bullets, cached pool entries, screenshots or detected objects.

| Field | Meaning |
|---|---|
| id | Monotonic identity assigned at spawn; survives while that bullet is active. Reusing a pooled allocation assigns a new ID. IDs are episode-local (restart after reset) and are not pointers. |
| type | EnemyAmmo list type0..4, not an enemy aircraft type. |
| position | Current world x/y/z; x right, y up. |
| velocity_per_tick | Stored ActiveAmmo::vel. updatePos adds it directly each internal tick. Upstream speedAdj is baked into this value at spawn; do not multiply it again. Not a velocity per second. |
| sprite_half_size | Half-width/half-height of the visual quad in world units; **not a collision hitbox**. |
| damage | Stored raw bullet damage. Do not interpret it as remaining health. |

EnemyAmmo::checkForHits tests Manhattan distance from the hero, using the average of the hero's two size components, and does not use bullet sprite size. Removed or collided bullets are absent from the next snapshot; absence is not a typed collision event. Out-of-bounds cleanup occurs before each bullet movement, so a just-moved bullet can remain outside bounds until the next tick. No list truncation is performed; a response exceeding the protocol's1MiB bound fails instead of silently discarding threats.

For synchronous surviving bullets, the next position equals previous position plus velocity_per_tick (float32 rounding). In live mode, an unknown number of updates can occur between reads, so do not apply the one-tick equation to arbitrary live snapshots.

Snapshot also exports rng_cursor for diagnostics. Live menu reads need not have identical cursors because the human loop still runs. It is not intended as a policy input. Enemy aircraft still lack stable IDs, and bullet/HUD fields are not a finalized fixed-size network observation.

## Reproduce checks

From the standalone repository with the Python package installed:

~~~bash
bash scripts/build_chromium_rl.sh
cc -shared -fPIC tests/fixed_epoch.c -o build/fixed-epoch.so
RUN_CHROMIUM_GUI_TESTS=1 <venv>/bin/python -m unittest discover -s tests -p 'test_*.py' -v
<venv>/bin/python scripts/check_render_equivalence.py build/fixed-epoch.so
<venv>/bin/python scripts/benchmark_render_steps.py build/fixed-epoch.so
<venv>/bin/python examples/watch_enemy_bullets.py
~~~

The preload only pins upstream's initial time seed for native regression/benchmarks. It is not loaded by normal launchers. This historical preload check predates the public reset(seed) API; new seeded-reset checks use that API. The equivalence test covers three fixed epochs × three action patterns, all exported fields including enemy bullets/RNG, repeated redraw, short idle waits and terminal redraw. It does not independently fingerprint every private field or exercise every full-game transition.

The sampling benchmark is one environment at a time, three fixed initial seeds per mode, fixed FIRE action and50 internal ticks/request. It excludes startup, reports actual executed ticks, and includes JSON transport/Python parsing; no network inference or optimizer updates. Results depend on display/driver/hardware and are not a performance guarantee.

## Results, 2026-09-07

- Native build succeeded;9 transport/parser/native test methods passed.
- Render-on/off comparison:9 complete first-level traces reached hero_dead;9563 schema2 snapshots matched, including enemy bullets and gameplay RNG. Repeated/terminal render and idle waits preserved state. These traces encountered bullet type0 only; types1..4 have generic export/parser coverage but no separate native trajectory acceptance yet.
- Bullet-motion check observed surviving IDs and verified per-axis next_position=position+velocity_per_tick.
- Repeated native X11 rendering of the same250-tick scene produced0 differing pixels in two captured PNGs and unchanged snapshots. Local screenshots: /tmp/chromium-render-a.png and /tmp/chromium-render-b.png (not versioned). The attempted programmatic resize was constrained to640×480 by the window manager; no new arbitrary-size visual acceptance is claimed.
- Sampling benchmark:3443 actual ticks and71 decisions per mode. Drawn:1.234860s,2788tick/s,57.5decisions/s. Skipped:0.155009s,22212tick/s,458.0decisions/s. About7.97× faster for this short workload; reference50tick/s倍率约55.8×与444.2×。Not a long-run or neural-training benchmark.
