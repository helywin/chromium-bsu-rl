# Live snapshot protocol v1

Default live mode runs in real time and accepts human GUI controls. Opt-in synchronous GUI `step` is now available; see [the command and its limitations](synchronous-step.md). This is not a deterministic training environment. Reset/seed, rewards, object IDs, bullets and power-up snapshots remain unimplemented.

## Transport

Linux/POSIX subprocess, one UTF-8 JSON object per line. Set `CHROMIUM_BSU_RL_PROTOCOL=1` and an isolated `CHROMIUM_BSU_RL_STATE_DIR` before launch; use `GameClient` normally. All legacy stdout output is redirected to stderr before initialization; a private duplicated stdout descriptor carries responses.

Requests have `protocol_version: 1`, strictly increasing positive int32 `request_id`, and string `command`. One request in flight per client. Maximum request 8192 bytes and response 1 MiB; excessive output closes the connection rather than silently truncating game data. JSON nesting is bounded. The native pump services bounded input on the main game thread, so incomplete requests do not block GUI events.

Commands: `hello`, `snapshot`, `close`. Unsupported commands return `ok: false` with `error.code/message`; successful messages contain `ok: true` and `result`. Response version and request ID must match. The client never retries commands automatically. EOF closes the owned game; timeout/malformed response reaps only the client's own subprocess. Close is idempotent on the Python side.

## Snapshot fields

| Field | Meaning and source |
|---|---|
| `schema_version` | 1, raw snapshot schema, not a policy observation version |
| `mode` | Global game/menu/level_over/hero_dead; not a Gymnasium termination flag |
| `paused`, `game_frame`, `level`, `speed_adjustment` | Raw Global values. game_frame resets on level changes; not a monotonic episode tick. Wall-clock adaptation still exists |
| `player.position` | ScreenItem::pos, game world x/y/z, not pixels. x right, y up. Fresh player: (0,-3,25) |
| `player.keyboard_motion` | MainSDL's raw two-axis keyboard accumulator; not world-space velocity. Its y convention differs from position y |
| `player.lives_counter` | Raw HeroAircraft counter (fresh value 4), not a claim that the displayed total is 4. Exhaustion semantics are not inferred from zero |
| `player.score/damage/shields` | Raw getters. Fresh damage can be -500 and shields 500; damage is not remaining health |
| `player.ammo_stock`, `visible` | Three raw ammunition stocks and hero visibility |
| `enemies` | Const traversal of EnemyFleet, does not modify the shared currentShip cursor |
| enemy `type/position/raw_velocity/size/damage` | Raw EnemyAircraft fields. raw_velocity is not guaranteed to describe all special enemy movement |

Enemy order is current list order and is not a persistent identity or fixed policy vector. No raw pointers are exposed. Bullet/event export and stable IDs are later work. Menu observations are introspection only, not transitions suitable for training.

Snapshots are copied at one complete main-loop boundary on the game thread, with no interleaved update during serialization. While paused or idle in the menu, unchanged fields may compare equal. In active play two requests can observe different frames; taking a snapshot is not a request to advance exactly one frame. `hello` explicitly reports `step/reset/headless/deterministic=false`.

## Python API

```python
from chromium_rl import GameClient, Snapshot

with GameClient() as game:
    state: Snapshot = game.snapshot()
    print(state.player.position, state.player.score, state.mode)
```

Use an editable installation in a source checkout for default binary/data lookup. For a separately installed wheel, pass `binary=Path(...)` and `data_directory=Path(...)`; assets and native build are not bundled in the wheel. No personal directory or course repository is required. `video_driver="x11"` is available for XWayland diagnostics; it is not forced on all users.

Each client has a fresh temporary preference/high-score directory, removed when closed. On failure the exception includes the last 4096 bytes of its game log. stderr goes to a temporary file, not an unread pipe. Public snapshot results are frozen dataclasses with validated numbers and vector lengths and include a `py.typed` marker for IDEs.
## Incremental capability update

The original live snapshot contract below remains supported. Opt-in synchronous GUI `step` is now available; see [the new command and its limitations](synchronous-step.md). Reset/seed and headless remain unimplemented. Statements below about unsupported step describe the default live mode.
