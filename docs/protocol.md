# Process protocol v1, snapshot schema v2

Default live mode runs in real time and accepts human GUI controls. Synchronous mode supports `step` and independent `render`; enemy bullet state is exported in both modes. See [render-free stepping and bullet semantics](render-free-stepping.md). Synchronous `reset(seed)` is available. Rewards, enemy aircraft IDs and power-up snapshots remain unimplemented.

## Transport

Linux/POSIX subprocess, one UTF-8 JSON object per line. Set `CHROMIUM_BSU_RL_PROTOCOL=1` and an isolated `CHROMIUM_BSU_RL_STATE_DIR` before launch; use `GameClient` normally. All legacy stdout output is redirected to stderr before initialization; a private duplicated stdout descriptor carries responses.

Requests have `protocol_version: 1`, strictly increasing positive int32 `request_id`, and string `command`. One request in flight per client. Maximum request 8192 bytes and response 1 MiB; excessive output closes the connection rather than silently truncating game data. JSON nesting is bounded. The native pump services bounded input on the main game thread, so incomplete requests do not block GUI events.

Commands: `hello`, `snapshot`, `close`; synchronous mode additionally accepts `step`, `render` and `reset`. Unsupported commands return `ok: false` with `error.code/message`; successful messages contain `ok: true` and `result`. Response version and request ID must match. The client never retries commands automatically. EOF closes the owned game; timeout/malformed response reaps only the client's own subprocess. Close is idempotent on the Python side.

## Snapshot fields

| Field | Meaning and source |
|---|---|
| `schema_version` | 2, raw snapshot schema, not a policy observation version |
| `mode` | Global game/menu/level_over/hero_dead; not a Gymnasium termination flag |
| `paused`, `game_frame`, `level`, `speed_adjustment` | Raw Global values. game_frame resets on level changes; not a monotonic episode tick. Wall-clock adaptation exists only in live mode |
| `player.position` | ScreenItem::pos, game world x/y/z, not pixels. x right, y up. Fresh player: (0,-3,25) |
| `player.keyboard_motion` | MainSDL's raw two-axis keyboard accumulator; not world-space velocity. Its y convention differs from position y |
| `player.lives_counter` | Raw HeroAircraft counter (fresh value 4), not a claim that the displayed total is 4. Exhaustion semantics are not inferred from zero |
| `player.score/damage/shields` | Raw getters. Fresh damage can be -500 and shields 500; damage is not remaining health |
| `player.ammo_stock`, `visible` | Three raw ammunition stocks and hero visibility |
| `enemies` | Const traversal of EnemyFleet, does not modify the shared currentShip cursor |
| enemy `type/position/raw_velocity/size/damage` | Raw EnemyAircraft fields. raw_velocity is not guaranteed to describe all special enemy movement |

Enemy aircraft order is not a persistent identity or fixed policy vector. `enemy_bullets` has episode-local spawn IDs and typed fields documented in [the bullet contract](render-free-stepping.md#enemy-bullet-contract). `rng_cursor` is diagnostic state, not a policy input. No raw pointers are exposed. Collision events and enemy aircraft IDs are later work. Menu observations are introspection only, not transitions suitable for training.

Snapshots are copied at one complete main-loop boundary on the game thread, with no interleaved update during serialization. While paused or idle in the menu, unchanged fields may compare equal. In active play two requests can observe different frames; taking a snapshot is not a request to advance exactly one frame. `hello` reports step/render/render_free_steps according to synchronous mode and enemy_bullets=true. reset/seed are true in the SDL synchronous runtime. headless reports the selected runtime mode; deterministic remains false and seeded repeatability is scoped below. Snapshot schema2 requires enemy_bullets and rng_cursor; missing fields are errors, not silently interpreted as no threats.

## Python API

```python
from chromium_rl import GameClient, Snapshot

with GameClient() as game:
    state: Snapshot = game.snapshot()
    print(state.player.position, state.player.score, state.mode)
```

Use an editable installation in a source checkout for default binary/data lookup. For a separately installed wheel, pass `binary=Path(...)` and `data_directory=Path(...)`; assets and native build are not bundled in the wheel. No personal directory or course repository is required. `video_driver="x11"` is available for XWayland diagnostics; it is not forced on all users.

Each client has a fresh temporary preference/high-score directory, removed when closed. On failure the exception includes the last 4096 bytes of its game log. stderr goes to a temporary file, not an unread pipe. Public snapshot results are frozen dataclasses with validated numbers and vector lengths and include a `py.typed` marker for IDEs.
## Compatibility

The new Python parser accepts old schema1 but old native capabilities report no enemy-bullet support. For bullet consumers require `game.capabilities.enemy_bullets`. Old clients rejecting schema2 must be updated with the native build. Protocol envelope version remains1; schema and behavior versioning are separate.

## Seeded first-level reset (seeded-reset-v3)

Request: `{"protocol_version":1,"request_id":2,"command":"reset","seed":7}`.
Success `result` is a schema2 snapshot directly (not a step wrapper). Requires
synchronous mode; seed is a required JSON integer in 0..4294967295, excluding
booleans, floats, strings and null. Invalid requests do not mutate game state.

The game thread rebuilds episode-owned objects within the same SDL/GL context
and process. It regenerates the random tables using `srand(seed)` and resets
keyboard accumulators/direction edges, global frame counters, first-level state,
player resources/weapon state, scheduled and active objects, and bullet IDs.
`episode_tick` is zero after reset. IDs are unique within an episode, not across
resets. A successful reset returns at frame zero without simulation advancement;
render explicitly when an immediately refreshed window is needed.

Reset is allowed both during play and after terminal. Subsequent steps use a
fresh episode; the caller must preserve any previous terminal observation first.
The snapshot mode is game, unpaused, level 1, position (0,-3,25), keyboard (0,0),
score 0, lives counter 4, damage -500, shields 500 and empty ammo stock.
No transition or reward is manufactured by reset.

Same seed/actions/build/platform/configuration repeated raw-state traces match
in the native tests, including render on/off and separate processes. This is not
a cross-platform or cross-version bitwise guarantee: libc RNG and floating-point
behavior are platform-dependent. Different seed integers are not guaranteed to
produce unique sequences (e.g. libc may map seeds 0 and 1 identically). Keep the
broad `deterministic` capability false rather than promising universal identity.
Startup without an explicit reset retains the legacy time-based initialization;
repeatable runs must call reset first. Synchronous tests use no-audio X11/GL;
the default mode still requires a display; opt-in headless mode is described below. Multi-level support is not added.

Python standalone client: `GameClient.reset(seed) -> Snapshot`. The independent
learning project implements its own transport rather than importing this client.
See [native reset validation](validation/seeded-reset.md).

## Additive powerup snapshot fields (2026-09-11)

`hello.powerups=true` advertises `snapshot.powerups`. This is an additive schema2
extension; protocol and seeded-reset-v3 gameplay version are unchanged. No physics,
reward, RNG draws, or pickup rules changed. Old clients can ignore the array; consumers
requiring powerups must check the capability and reject a missing field.

Each item contains `id` (positive episode-local spawn ID, stable until removed),
`type` (0 Shields, 1 SuperShields, 2 Repair, 3/4/5 HeroAmmo00/01/02), `position`
(three world coordinates), `power` (raw refill multiplier, not score), and
`next_displacement` (two world-unit displacements for the next update before horizontal
boundary clamping). The latter uses the update's damping factor
`1-speedAdj+speedAdj*0.982` and vertical scroll contribution `speed*speedAdj`;
it is not a constant-velocity promise over multiple ticks. Removal or collection may
prevent an item from appearing in the next snapshot. Draw-only wobble is not position.

Traversal is const and does not change the legacy iteration cursor. IDs are assigned
when inserted and restart on seeded episode reconstruction. All active objects are
included, even outside the visible screen; array order is not a policy ordering.


## True headless synchronous mode (2026-09-11)

Set `CHROMIUM_BSU_RL_HEADLESS=1` with protocol/synchronous mode, or use
`GameClient(synchronous=True, render_each_step=False, headless=True)`.
No SDL video subsystem, window, GL context, texture/font loading or audio backend is
created. Game object construction, RNG draws, physics, collisions and visual-state
updates that affect snapshots remain intact. No display server or Xvfb is required.
The binary still links its usual libraries; this is a runtime mode, not a dependency-free build.

`hello.headless=true`, `render=false`, `step/reset/render_free_steps=true`.
A render request fails without advancing the game. Create a separate GUI process for
playback. GUI defaults are unchanged. The sync command loop now polls stdin and wakes
on input instead of sleeping 2 ms after each iteration; tick duration remains 0.02
simulated seconds. See [validation](validation/headless-throughput.md).

## Cumulative episode events (2026-09-11)

`hello.episode_events=true` advertises additive `snapshot.episode_events` fields.
Counters reset on newGame/reset, remain unchanged by snapshot/render and are never
used by native physics or scoring. Subtract snapshots from the same episode to get
step events; do not subtract across resets.

- `enemies_destroyed`: non-silent damaged enemy removal, including bullets,
  collisions and chain explosions. Excludes enemies removed after passing the bottom
  (age set to zero), reset and ordinary cleanup. Not exclusively bullet kill attribution.
- `enemies_escaped`: enemy passing y<-14; each invokes loseLife.
- `lives_lost`: each actual lives--, including escaped enemies, damage and self-destruct.
  Unlike net life difference, simultaneous awarded lives do not hide this count.
- `pickups`: each hero collision that consumes a powerup, including resource pickups
  that give no score or no benefit because a resource is full.
- `missed_powerups`: each powerup removed after passing y<-12.
- `pickup_score`, `missed_powerup_score`: actual raw score increases in those two paths;
  no score is invented if game mode suppresses scoring. Other raw score is the total
  minus these contributions; it is not a count of bullet hits.

Counts are nonnegative int64, score totals are nonnegative numbers. Existing gameplay
version and schema2 remain; this is instrumentation, not a scoring/rule modification.
