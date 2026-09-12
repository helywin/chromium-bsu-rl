# Python API

[English](api.md) | [简体中文](api.zh-CN.md) · [Home](../README.md)

Install and build first: [installation](installation.md). All public types below
are importable from `chromium_rl`; returned state uses frozen dataclasses and tuples.

## GameClient

```python
GameClient(
    binary=None, data_directory=None, video_driver=None, timeout=10.0, debug=False,
    synchronous=False, render_each_step=True, headless=False,
)
```

`binary` and `data_directory` accept `pathlib.Path`. Defaults locate the editable
checkout's local build and `game/data`. For a wheel, pass both explicitly.
`video_driver` selects an SDL backend such as `"x11"`. `timeout` is a positive,
finite response timeout in seconds. `debug=True` enables native diagnostic logs.

`headless=True` requires `synchronous=True, render_each_step=False`.
`render_each_step=False` requires synchronous mode. The default client opens a
live game menu; synchronous clients start a first-level episode. Use one owner
per client and `with GameClient(...) as game:` for process cleanup.

| Member | Contract |
| --- | --- |
| `capabilities: Capabilities` | Native feature flags negotiated at startup |
| `snapshot() -> Snapshot` | Read current state; does not advance synchronous simulation |
| `reset(seed: int) -> Snapshot` | Reset first level in the same process; seed in 0..4294967295, excludes bool |
| `step(action: Action, *, ticks: int = 1) -> StepResult` | Hold action for 1..50 complete logic ticks; stop early at terminal |
| `render() -> Snapshot` | Draw current state without a tick; requires synchronous GUI mode |
| `close() -> None` | Close and reap the owned subprocess; safe to call repeatedly |

Without `reset(seed)`, startup uses legacy time-based initialization. Repeatability
requires matching native build, platform, configuration, seed and action/tick sequence.
`deterministic` remains false because universal/cross-platform identity is not promised.

## Actions and time

Use enum members, not raw integers, with the public Python API.

| Movement | Without firing | With firing |
| --- | --- | --- |
| Release movement | `IDLE = 0` | `FIRE = 9` |
| Up | `UP = 1` | `UP_FIRE = 10` |
| Down | `DOWN = 2` | `DOWN_FIRE = 11` |
| Left | `LEFT = 3` | `LEFT_FIRE = 12` |
| Right | `RIGHT = 4` | `RIGHT_FIRE = 13` |
| Up-left | `UP_LEFT = 5` | `UP_LEFT_FIRE = 14` |
| Up-right | `UP_RIGHT = 6` | `UP_RIGHT_FIRE = 15` |
| Down-left | `DOWN_LEFT = 7` | `DOWN_LEFT_FIRE = 16` |
| Down-right | `DOWN_RIGHT = 8` | `DOWN_RIGHT_FIRE = 17` |

An action replaces the full held-button state. Repeated directions hold the same
input; `IDLE` releases it and movement decays. Each tick uses `speedAdj=1`, the
upstream 50 fps reference scale (0.02 simulated seconds), with collision checks.
Wall-clock waiting does not advance a synchronous game.

`StepResult` contains `snapshot`, `actual_ticks`, cumulative `episode_tick`,
cumulative `simulated_seconds`, and `terminated`. A terminal mode is `hero_dead`
or `level_over`. It ends this **single-level** episode, not a full-game task.
There is no reward, truncation flag or automatic reset. A consumer's decision
budget is separate from native termination.

## State and units

| Type / field | Meaning |
| --- | --- |
| `Snapshot.mode` | `game`, `menu`, `level_over`, `hero_dead` |
| `paused`, `game_frame`, `level`, `speed_adjustment` | Raw game values; `game_frame` is not the cumulative episode tick |
| `player: PlayerState` | Position, keyboard accumulator, lives counter, score, damage, shields, visibility, three ammo stocks |
| `player.position` | World x/y/z, not pixels; x right, y up; reset position `(0, -3, 25)` |
| `player.keyboard_motion` | Input accumulator, not world velocity; different y convention |
| `player.lives_counter` | Raw counter, initially 4; do not derive termination from zero |
| `player.damage`, `shields` | Raw resources; initial damage -500 and shields 500; damage is not remaining health |
| `enemies: tuple[EnemyState, ...]` | Type, world position, raw velocity, size, damage; no stable aircraft ID |
| `enemy_bullets: tuple[EnemyBulletState, ...]` | Episode-local ID, type, world position, displacement per tick, sprite half-size, raw damage |
| `powerups: tuple[PowerUpState, ...] \| None` | Episode-local ID, type, position, raw refill multiplier `power`, `next_displacement` |
| `episode_events: EpisodeEvents \| None` | Cumulative instrumentation, described below |
| `rng_cursor: int \| None` | RNG diagnostic; not a recommended policy input |

Enemy raw velocity does not describe every special movement. Bullet sprite
dimensions are **not collision bounds**. Powerup displacement predicts the next
update before horizontal clamping; damping, removal and collection limit this
prediction. Powerup types are 0 shields, 1 super shields, 2 repair, and 3/4/5 ammo
00/01/02. IDs restart on reset; list order is not a persistent policy ordering.
Arrays can include offscreen objects. See [wire fields](protocol.md).

## Episode events

Subtract counters only between snapshots from the same episode; reset clears them.

| Field | Meaning |
| --- | --- |
| `enemies_destroyed` | Non-silent damaged enemy removals from all sources; not exclusively projectile kills |
| `enemies_escaped` | Enemies crossing y < -14; each invokes life loss |
| `lives_lost` | Actual decrements, including escape, damage and self-destruct; rewards do not hide losses |
| `pickups`, `missed_powerups` | Consumed pickups and pickups passing y < -12 |
| `pickup_score`, `missed_powerup_score` | Actual score increases in those paths |
| `shield_damage` | Absorbed shield resource, capped at available resource; excludes passive decay, refill and cleanup |
| `projectile_damage` | Actual enemy HP removed by player ammunition, excluding overkill |
| `projectile_damage_fraction` | Accumulated effective damage / target's initial HP |
| `projectile_kills` | Projectile-induced transition from enemy damage <= 0 to > 0 |

Projectile attribution excludes collision, super-bomb and cleanup damage.
Persistent ammunition can contribute on multiple ticks. Shield damage includes
all `doDamage` callers, so it is not bullet-only. Native scoring/physics do not
read these diagnostic counters. Consumers choose their own rewards.

## Compatibility and errors

`Capabilities` exposes `implementation`, `upstream_version`, `live_snapshot`,
`step`, `reset`, `seed`, `headless`, `deterministic`, `render`, `render_free_steps`,
`enemy_bullets`, `powerups`, `episode_events`, `shield_damage`, `projectile_damage`.

Schema 1 and 2 are accepted. Older builds omit optional powerups/events;
the public fields are `None`, distinct from an empty tuple or measured zero.
Damage fields in `EpisodeEvents` are individually optional for older builds;
the three projectile fields must occur together. If a runtime advertises a
capability and omits its data, parsing fails. Check capabilities before requiring
instrumentation; unknown additive fields can be ignored.

`ValueError` rejects invalid local arguments. `RemoteError` reports a valid
native error and leaves the connection usable. `ProtocolError` means a failed
transport or invalid state; the client reaps its process and must be recreated.
The exception includes a native log tail. Commands are not automatically retried.
Rebuild the native runtime when updating the package to avoid feature mismatches.
