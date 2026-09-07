# Synchronous GUI step, control model v1

Stage C is partially implemented: exact action/tick boundaries, not a render-free game loop.

## Process and wire contract

`GameClient()` retains live human operation. `GameClient(synchronous=True)` additionally sets `CHROMIUM_BSU_RL_SYNCHRONOUS=1`; native mode requires the existing opt-in protocol and isolated state directory. It starts the already-initialized first level at game_frame=0, without running menu frames. Physical keyboard/mouse/joystick inputs are ignored; window close and protocol close/EOF still terminate the owned process.

Protocol version and snapshot schema remain 1 (existing fields unchanged). The optional step capability is true only for the synchronous process. The implementation string is `chromium-bsu-rl/sync-gui-v1`. Reset, headless and deterministic capabilities remain false.

Request, in addition to version/request_id/command:

```json
{"protocol_version":1,"request_id":2,"command":"step","action":13,"ticks":1}
```

`action` is an integer 0..17, `ticks` an integer 1..50, never a boolean. Invalid requests do not advance state. Direction indices: 0 idle, 1 up, 2 down, 3 left, 4 right, 5 up-left, 6 up-right, 7 down-left, 8 down-right. Add 9 for fire. Python exposes named `Action` members instead of requiring numeric memorization.

Result fields: `snapshot` (existing schema), `actual_ticks`, `episode_tick`, `simulated_seconds=episode_tick*0.02`, `terminated`. The episode counter is monotonic within this process, distinct from upstream game_frame. Every requested internal tick runs all collisions; termination stops repeat early. HeroDead or LevelOver terminates this **single-level** prototype, never a claim of full-game victory. Further step returns `episode_ended` without advancing. No automatic reset, reward, truncation or Gym tuple is provided.

## Input mechanism and boundary

One tick: apply held direction and fire → moveEvent → original drawGL (update AND rendering side effects) → swap buffers → increment global frame → snapshot after all requested ticks.

The old human loop applied input after drawing. This prototype explicitly puts input before the complete update so one returned state includes the requested action. It does not claim identical wall-clock human trajectories.

For each axis, a newly pressed direction adds ±5 once. Holding adds `direction*(2+abs(accumulator)*0.4)`, then multiplies by0.7. The resulting accumulator is truncated toward zero for moveEvent. Default isolated movementSpeed=0.03. Screen y is downward; world y is upward. Diagonals are not normalized. Changing from right to up-right keeps the right edge held and creates only an up edge. Opposing simultaneous keys and OS key-repeat events are not modeled.

Starting x=0 and accumulator=0:

- First right: `(5+(2+5*0.4))*0.7=6.3`; integer6 moves x by0.18.
- Second right: `(6.3+(2+6.3*0.4))*0.7=7.574`; integer7 adds0.21, so x=0.39.
- Release next: `7.574*0.7=5.3018`; integer5 adds0.15, so x=0.54. Release is not immediate stopping.

Held fire uses `HeroAircraft::holdFire` to change the trigger only when necessary, avoiding a cooldown restart every tick; after resurrection a held request can reassert fire once the hero is visible. Keyboard arithmetic currently mirrors the upstream formula; it has not yet been extracted into a shared human/RL helper.

## Timing and current limitation

speedAdj stays1; no FPS adaptation or per-tick SDL_Delay. SDL2 swap interval0 is requested on a best-effort basis. Idle polling sleeps2ms to avoid busy-spinning; no gameplay updates or RNG draws occur in idle. Python delays control viewing pace only. Native GUI may initially be blank until the first step presents a frame.

Do not skip or repeat drawGL as an optimization: HeroAircraft::drawGL decrements dontShow; EnemyFleet::drawGL can retarget enemies; several render paths consume shared IRAND. Consequently each tick still draws exactly once. No render command is offered, no hidden window is called headless, and no render-independent equivalence is claimed. Background/framebuffer expose handling and full update/render separation remain stage-C work.

The 0.02 seconds field is a reference-time label for the upstream50fps rule, not a unified continuous physics timestep. Do not enlarge it to simulate omitted collisions. Seed/reset and same-seed slow/fast comparisons remain stageD and acceleration acceptance work.

## Developer evidence, 2026-09-07

- Local standalone build succeeded (`build/stage-c-build.log`).
- Native X11 checks cover initial freeze, arithmetic above, diagonal movement, exact repeat counts, fixed speed, invalid request recovery, terminal freeze, live-mode compatibility and child cleanup.
- A manual idle run ended at episode_tick852 with actual_ticks2 from a50-tick request, mode hero_dead. Subsequent step rejected and snapshot unchanged. This is one unseeded diagnostic, not a benchmark or reproducibility claim.
- Native screenshot `/tmp/chromium-rl-stage-c-game.png` shows the moved player and fired projectiles after12 right/fire ticks; screenshot is a local non-versioned artifact.
- Both default-driver and X11 demonstration runs were exercised. This is native game/bridge evidence, not network training or robot simulation.

Reproduce from an installed standalone checkout:

```bash
bash scripts/build_chromium_rl.sh
RUN_CHROMIUM_GUI_TESTS=1 <venv>/bin/python -m unittest discover -s tests -p 'test_*.py' -v
<venv>/bin/python examples/watch_steps.py
```
