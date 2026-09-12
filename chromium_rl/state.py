"""Validated immutable snapshots. License: Clarified Artistic, game/COPYING."""
from dataclasses import dataclass
import math
from typing import Mapping, cast

Vec3 = tuple[float, float, float]
Vec2 = tuple[float, float]


def mapping(value: object) -> Mapping[str, object]:
    if not isinstance(value, dict) or not all(isinstance(k, str) for k in value):
        raise ValueError("Expected a JSON object")
    return cast(Mapping[str, object], value)


def integer(value: object) -> int:
    if type(value) is not int:
        raise ValueError("Expected integer (not boolean)")
    return value


def number(value: object) -> float:
    if type(value) not in (float, int):
        raise ValueError("Expected number")
    try:
        result = float(cast(float | int, value))
    except OverflowError as exc:
        raise ValueError("Number outside floating-point range") from exc
    if not math.isfinite(result):
        raise ValueError("Non-finite number in game state")
    return result


def boolean(value: object) -> bool:
    if type(value) is not bool:
        raise ValueError("Expected boolean")
    return value


def text(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("Expected string")
    return value


def values(value: object) -> list[object]:
    if not isinstance(value, list):
        raise ValueError("Expected array")
    return cast(list[object], value)


def vector(value: object, length: int) -> tuple[float, ...]:
    result = tuple(number(v) for v in values(value))
    if len(result) != length:
        raise ValueError(f"Expected vector length {length}")
    return result


@dataclass(frozen=True)
class Capabilities:
    implementation: str
    upstream_version: str
    live_snapshot: bool
    step: bool
    reset: bool
    headless: bool
    deterministic: bool
    render: bool = False
    render_free_steps: bool = False
    enemy_bullets: bool = False
    seed: bool = False
    powerups: bool = False
    episode_events: bool = False
    shield_damage: bool = False
    projectile_damage: bool = False

    @classmethod
    def parse(cls, value: object) -> "Capabilities":
        d = mapping(value)
        if integer(d["schema_version"]) not in (1, 2):
            raise ValueError("Unsupported snapshot schema")
        return cls(
            implementation=text(d["implementation"]), upstream_version=text(d["upstream_version"]),
            live_snapshot=boolean(d["live_snapshot"]), step=boolean(d["step"]),
            reset=boolean(d["reset"]), headless=boolean(d["headless"]),
            deterministic=boolean(d["deterministic"]), render=boolean(d.get("render", False)),
            render_free_steps=boolean(d.get("render_free_steps", False)),
            enemy_bullets=boolean(d.get("enemy_bullets", False)), seed=boolean(d.get("seed", False)),
            powerups=boolean(d.get("powerups", False)), episode_events=boolean(d.get("episode_events", False)),
            shield_damage=boolean(d.get("shield_damage", False)),
            projectile_damage=boolean(d.get("projectile_damage", False)),
        )


@dataclass(frozen=True)
class PlayerState:
    position: Vec3
    keyboard_motion: Vec2
    lives_counter: int
    score: float
    damage: float
    shields: float
    visible: bool
    ammo_stock: tuple[float, ...]

    @classmethod
    def parse(cls, value: object) -> "PlayerState":
        d = mapping(value)
        return cls(cast(Vec3, vector(d["position"], 3)), cast(Vec2, vector(d["keyboard_motion"], 2)),
                   integer(d["lives_counter"]), number(d["score"]), number(d["damage"]),
                   number(d["shields"]), boolean(d["visible"]), vector(d["ammo_stock"], 3))


@dataclass(frozen=True)
class EnemyState:
    type: int
    position: Vec3
    raw_velocity: Vec3
    size: Vec2
    damage: float

    @classmethod
    def parse(cls, value: object) -> "EnemyState":
        d = mapping(value)
        return cls(integer(d["type"]), cast(Vec3, vector(d["position"], 3)),
                   cast(Vec3, vector(d["raw_velocity"], 3)), cast(Vec2, vector(d["size"], 2)),
                   number(d["damage"]))


@dataclass(frozen=True)
class EnemyBulletState:
    id: int
    type: int
    position: Vec3
    velocity_per_tick: Vec3
    sprite_half_size: Vec2
    damage: float

    @classmethod
    def parse(cls, value: object) -> "EnemyBulletState":
        d = mapping(value)
        result = cls(integer(d["id"]), integer(d["type"]),
                     cast(Vec3, vector(d["position"], 3)),
                     cast(Vec3, vector(d["velocity_per_tick"], 3)),
                     cast(Vec2, vector(d["sprite_half_size"], 2)), number(d["damage"]))
        if result.id <= 0 or not 0 <= result.type < 5 or any(v <= 0 for v in result.sprite_half_size):
            raise ValueError("Invalid enemy bullet identity/type/size")
        return result


@dataclass(frozen=True)
class PowerUpState:
    """Episode-local pickup identity and raw motion before boundary clamping."""

    id: int
    type: int
    position: Vec3
    power: float
    next_displacement: Vec2

    @classmethod
    def parse(cls, value: object) -> "PowerUpState":
        d = mapping(value)
        result = cls(integer(d["id"]), integer(d["type"]),
                     cast(Vec3, vector(d["position"], 3)), number(d["power"]),
                     cast(Vec2, vector(d["next_displacement"], 2)))
        if result.id <= 0 or not 0 <= result.type < 6:
            raise ValueError("Invalid powerup identity/type")
        return result


@dataclass(frozen=True)
class EpisodeEvents:
    """Cumulative counters; subtract only within the same episode.

    Optional damage fields are None when an older native build omits them.
    Missing instrumentation must never be interpreted as a measured zero.
    """

    enemies_destroyed: int
    enemies_escaped: int
    lives_lost: int
    pickups: int
    missed_powerups: int
    pickup_score: float
    missed_powerup_score: float
    shield_damage: float | None = None
    projectile_damage: float | None = None
    projectile_damage_fraction: float | None = None
    projectile_kills: int | None = None

    @classmethod
    def parse(cls, value: object, *, capabilities: Capabilities | None = None) -> "EpisodeEvents":
        d = mapping(value)
        counts = tuple(integer(d[k]) for k in (
            "enemies_destroyed", "enemies_escaped", "lives_lost", "pickups", "missed_powerups"))
        scores = tuple(number(d[k]) for k in ("pickup_score", "missed_powerup_score"))
        shield = number(d["shield_damage"]) if "shield_damage" in d else None
        projectile_keys = ("projectile_damage", "projectile_damage_fraction", "projectile_kills")
        if any(k in d for k in projectile_keys) and not all(k in d for k in projectile_keys):
            raise ValueError("Incomplete projectile damage instrumentation")
        damage = number(d["projectile_damage"]) if "projectile_damage" in d else None
        fraction = number(d["projectile_damage_fraction"]) if "projectile_damage_fraction" in d else None
        kills = integer(d["projectile_kills"]) if "projectile_kills" in d else None
        if capabilities is not None:
            if capabilities.shield_damage and shield is None:
                raise ValueError("Native runtime advertised shield_damage but omitted it")
            if capabilities.projectile_damage and damage is None:
                raise ValueError("Native runtime advertised projectile_damage but omitted it")
        if any(v < 0 for v in (*counts, *scores, shield, damage, fraction, kills) if v is not None):
            raise ValueError("Negative episode event counter")
        return cls(counts[0], counts[1], counts[2], counts[3], counts[4],
                   scores[0], scores[1], shield, damage, fraction, kills)


@dataclass(frozen=True)
class Snapshot:
    mode: str
    paused: bool
    game_frame: int
    level: int
    speed_adjustment: float
    player: PlayerState
    enemies: tuple[EnemyState, ...]
    enemy_bullets: tuple[EnemyBulletState, ...] = ()
    rng_cursor: int | None = None
    powerups: tuple[PowerUpState, ...] | None = None
    episode_events: EpisodeEvents | None = None

    @classmethod
    def parse(cls, value: object, *, capabilities: Capabilities | None = None) -> "Snapshot":
        d = mapping(value)
        schema = integer(d["schema_version"])
        if schema not in (1, 2):
            raise ValueError("Unsupported snapshot schema")
        mode = text(d["mode"])
        if mode not in ("game", "menu", "level_over", "hero_dead"):
            raise ValueError("Unknown game mode")
        bullets = tuple(EnemyBulletState.parse(b) for b in values(d["enemy_bullets"])) if schema == 2 else ()
        if len({b.id for b in bullets}) != len(bullets):
            raise ValueError("Duplicate enemy bullet ID")
        powerups = tuple(PowerUpState.parse(p) for p in values(d["powerups"])) if "powerups" in d else None
        if powerups is not None and len({p.id for p in powerups}) != len(powerups):
            raise ValueError("Duplicate powerup ID")
        events = EpisodeEvents.parse(d["episode_events"], capabilities=capabilities) if "episode_events" in d else None
        if capabilities is not None:
            if capabilities.enemy_bullets and schema != 2:
                raise ValueError("Native runtime advertised enemy_bullets but omitted them")
            if capabilities.powerups and powerups is None:
                raise ValueError("Native runtime advertised powerups but omitted them")
            if (capabilities.episode_events or capabilities.shield_damage or capabilities.projectile_damage) and events is None:
                raise ValueError("Native runtime advertised episode events but omitted them")
        return cls(mode, boolean(d["paused"]), integer(d["game_frame"]), integer(d["level"]),
                   number(d["speed_adjustment"]), PlayerState.parse(d["player"]),
                   tuple(EnemyState.parse(e) for e in values(d["enemies"])), bullets,
                   integer(d["rng_cursor"]) if schema == 2 else None, powerups, events)


@dataclass(frozen=True)
class StepResult:
    snapshot: Snapshot
    actual_ticks: int
    episode_tick: int
    simulated_seconds: float
    terminated: bool

    @classmethod
    def parse(cls, value: object, *, capabilities: Capabilities | None = None) -> "StepResult":
        d = mapping(value)
        result = cls(Snapshot.parse(d["snapshot"], capabilities=capabilities), integer(d["actual_ticks"]),
                     integer(d["episode_tick"]), number(d["simulated_seconds"]),
                     boolean(d["terminated"]))
        if not 1 <= result.actual_ticks <= 50 or result.episode_tick < result.actual_ticks:
            raise ValueError("Invalid tick counts")
        if not math.isclose(result.simulated_seconds, result.episode_tick * 0.02):
            raise ValueError("Invalid fixed-step time")
        if result.terminated != (result.snapshot.mode in ("hero_dead", "level_over")):
            raise ValueError("Invalid single-level termination")
        return result
