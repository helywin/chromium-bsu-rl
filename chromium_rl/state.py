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
    return cast(int, value)


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
    return cast(bool, value)


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

    @classmethod
    def parse(cls, value: object) -> "Capabilities":
        d = mapping(value)
        if integer(d["schema_version"]) != 1:
            raise ValueError("Unsupported snapshot schema")
        return cls(text(d["implementation"]), text(d["upstream_version"]),
                   *(boolean(d[k]) for k in ("live_snapshot", "step", "reset", "headless", "deterministic")))


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
class Snapshot:
    mode: str
    paused: bool
    game_frame: int
    level: int
    speed_adjustment: float
    player: PlayerState
    enemies: tuple[EnemyState, ...]

    @classmethod
    def parse(cls, value: object) -> "Snapshot":
        d = mapping(value)
        if integer(d["schema_version"]) != 1:
            raise ValueError("Unsupported snapshot schema")
        mode = text(d["mode"])
        if mode not in ("game", "menu", "level_over", "hero_dead"):
            raise ValueError("Unknown game mode")
        return cls(mode, boolean(d["paused"]), integer(d["game_frame"]), integer(d["level"]),
                   number(d["speed_adjustment"]), PlayerState.parse(d["player"]),
                   tuple(EnemyState.parse(e) for e in values(d["enemies"])))
