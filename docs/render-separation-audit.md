# Rendering separation: incremental audit

> Historical audit / 历史审查。Current: [English API](api.md) / [中文 API](api.zh-CN.md).

Date: 2026-09-07. Historical first-pass audit. The single-level remaining items below have since been addressed in [split-render-v2](render-free-stepping.md), with render-free stepping now enabled (still requires display/GL). The old9563-state before/after result applies only to the initial extraction; the new version has a separate draw/skip comparison.

## Why simply skipping drawGL is wrong

A redraw should display a state without changing the next game's outcome. Upstream does more than drawing: it decrements resurrection visibility, retargets enemies, creates particles, moves background segments and consumes the same random sequence as gameplay. Removing the function call would therefore remove rules, not just graphics work.

For example, when the hero's dontShow counter is1, the old sprite code hides the hero for that frame and then changes the counter to0. The status display and the next tick see0. Decrementing at the start of the next update instead would change this boundary. The extracted advanceVisibility caches the old sprite decision before decrementing, preserving both observations.

## Extracted in this change

- `MainGL::updateGameLogic`: item spawning, object/ammo updates, collisions, explosions/audio, hero update and gameFrame increment. It contains no GL calls. It is only the **core update**, not a complete independent simulation tick yet.
- `HeroAircraft::advanceVisibility`: sprite decision and dontShow decrement, called once at the original actor-drawing boundary; drawGL itself no longer decrements the counter. Still consumes visual RNG in drawGL.
- `EnemyFleet::advanceTargeting`: periodic Straight/Boss01 targeting assignments moved out of drawGL. These assignments do not consume RNG or alter the enemy list, so moving them just before enemy drawing preserves the subsequent logic.
- All existing MainGL call sites, including human-mode death/success paths, call the extracted actor updates as appropriate. The combined drawGameGL entrypoint still owns the sequencing.
- The preceding drawable-size fix is retained. The original tester confirmed the slow playback window displayed the complete scene. Before drawing, actual SDL drawable pixels determine a centered original-aspect viewport; game coordinates are unchanged.

## Remaining dependency checklist

| Source | Mutation still inside drawing | Required before render-free acceptance |
|---|---|---|
| GroundMetal::drawGL | segment scrolling, recycling | advance once per logic tick; draw existing segments only |
| GroundMetalSegment::drawGL | age increment, cached colors | move animation state or derive it from tick |
| GroundSea / GroundSeaSegment | scrolling/recycling; constructors use FRAND | audit if/when this background is enabled |
| StatusDisplay::drawGL | blink, fading alpha, warning reset, tip counters, rotation | update HUD state separately |
| StatusDisplay::drawGL | super-shield addGlitter | create particles in the update path, not redraw |
| Explosions::drawElectric | scales particle velocity | move exactly once to an update stage |
| Hero/Enemy/PowerUps/EnemyAmmo/Explosions/StatusDisplay rendering | IRAND/FRAND/SRAND advance global randIndex | explicitly preserve the stream or introduce a versioned visual stream; do not silently change gameplay randomness |
| MainGL::drawDeadGL / drawSuccessGL | terminal/level transition updates | remain outside the single-level RL task; full-game separation is separate work |

This is a source audit of the paths inspected, not a proof that every remaining mutation has already been found. The next acceptance check must compare render-on/off traces and repeated redraws, including RNG and currently unexported state. Current snapshot equality does not prove equality of every bullet, particle or hidden field.

## Native before/after regression

Developer-only `tests/fixed_epoch.c` pins upstream's `time(NULL)` seed input via a process-local Linux preload. This is not a supported seed/reset API and is never loaded by normal launchers. `scripts/check_logic_extraction.py` compares all exported snapshot fields and tick results for three fixed epochs × idle/fire/combined-movement patterns, to termination or4000ticks.

Commands from this standalone repository; `<venv>` is the consuming virtual environment:

```bash
bash scripts/build_chromium_rl.sh
cc -shared -fPIC tests/fixed_epoch.c -o build/fixed-epoch.so
<venv>/bin/python scripts/check_logic_extraction.py \
  build/work.nFfVBz/src/chromium-bsu \
  build/install/bin/chromium-bsu-rl build/fixed-epoch.so
RUN_CHROMIUM_GUI_TESTS=1 <venv>/bin/python -m unittest discover -s tests -p 'test_*.py' -v
```

The first binary path is the local retained pre-extraction build with the viewport fix. On another checkout, supply an explicitly retained baseline binary instead; this ignored build directory is not shipped. Both binaries must use the same game assets and isolated default preferences. Build log: `build/logic-extraction-build.log` (local, ignored). No training or checkpoint is produced.

Result: all9 trajectories reached hero_dead with identical exported states at every tick;9563 snapshots compared in total. Counts by epoch (idle/fire/movement):1234567=1033/1209/1209;2345678=952/1182/953;3456789=1052/1052/921. Existing7 transport/native test methods also passed. The checks are developer regression evidence, not learner training and not headless verification.
