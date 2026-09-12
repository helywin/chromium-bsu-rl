"""Public type compatibility and capability validation, without a native build."""
from dataclasses import replace
import unittest

from chromium_rl import Capabilities, EpisodeEvents, PowerUpState, Snapshot, StepResult


def snapshot_data() -> dict:
    return {
        "schema_version": 2, "rng_cursor": 0, "mode": "game", "paused": False,
        "game_frame": 0, "level": 1, "speed_adjustment": 1,
        "player": {"position": [0, -3, 25], "keyboard_motion": [0, 0],
                   "lives_counter": 4, "score": 0, "damage": -500, "shields": 500,
                   "visible": True, "ammo_stock": [0, 0, 0]},
        "enemies": [], "enemy_bullets": [],
    }


def events_data() -> dict:
    return dict(enemies_destroyed=0, enemies_escaped=0, lives_lost=0, pickups=0,
                missed_powerups=0, pickup_score=0, missed_powerup_score=0)


class PublicStateTests(unittest.TestCase):
    def test_older_snapshots_distinguish_missing_instrumentation(self) -> None:
        raw = snapshot_data()
        for schema in (1, 2):
            state = Snapshot.parse({**raw, "schema_version": schema})
            self.assertIsNone(state.powerups)
            self.assertIsNone(state.episode_events)
        events = EpisodeEvents.parse(events_data())
        self.assertIsNone(events.shield_damage)
        self.assertIsNone(events.projectile_damage)
        self.assertIsNone(events.projectile_kills)
        self.assertEqual(Snapshot.parse({**raw, "powerups": []}).powerups, ())

    def test_capability_promises_require_complete_data(self) -> None:
        caps = Capabilities("old", "0.9.16.1", True, True, True, True, False)
        for field in ("powerups", "episode_events", "shield_damage", "projectile_damage"):
            required = replace(caps, **{field: True})
            with self.subTest(field=field), self.assertRaises(ValueError):
                Snapshot.parse(snapshot_data(), capabilities=required)
        for field in ("shield_damage", "projectile_damage"):
            with self.subTest(field=field), self.assertRaises(ValueError):
                EpisodeEvents.parse(events_data(), capabilities=replace(caps, **{field: True}))
        with self.assertRaises(ValueError):
            StepResult.parse({"snapshot": snapshot_data(), "actual_ticks": 1, "episode_tick": 1,
                              "simulated_seconds": 0.02, "terminated": False},
                             capabilities=replace(caps, powerups=True))

    def test_events_reject_invalid_or_partial_attribution(self) -> None:
        for key, value in (("lives_lost", True), ("pickups", -1), ("pickup_score", -0.5),
                           ("shield_damage", float("nan")), ("projectile_damage", 1.0)):
            with self.subTest(key=key), self.assertRaises(ValueError):
                EpisodeEvents.parse({**events_data(), key: value})
        extra = dict(shield_damage=5, projectile_damage=7, projectile_damage_fraction=0.5, projectile_kills=1)
        self.assertEqual(EpisodeEvents.parse({**events_data(), **extra}).projectile_damage, 7.0)
        for bad in (True, -1, 1.5):
            with self.subTest(kills=bad), self.assertRaises(ValueError):
                EpisodeEvents.parse({**events_data(), **extra, "projectile_kills": bad})

    def test_powerups_validate_identity_and_motion(self) -> None:
        raw = dict(id=1, type=0, position=[0, 1, 25], power=1, next_displacement=[0.1, -0.1])
        self.assertEqual(PowerUpState.parse(raw).next_displacement, (0.1, -0.1))
        for key, value in (("id", True), ("id", 0), ("type", 6), ("position", [0, 1]),
                           ("next_displacement", [0, float("inf")])):
            with self.subTest(key=key), self.assertRaises(ValueError):
                PowerUpState.parse({**raw, key: value})
        with self.assertRaises(ValueError):
            Snapshot.parse({**snapshot_data(), "powerups": [raw, raw]})

    def test_capabilities_parse_additive_fields_and_legacy_defaults(self) -> None:
        raw = dict(implementation="test", upstream_version="0.9.16.1", schema_version=2,
                   live_snapshot=True, step=True, reset=True, headless=True, deterministic=False)
        self.assertFalse(Capabilities.parse(raw).projectile_damage)
        fields = ("seed", "powerups", "episode_events", "shield_damage", "projectile_damage")
        caps = Capabilities.parse({**raw, **dict.fromkeys(fields, True)})
        self.assertTrue(all(getattr(caps, field) for field in fields))
        with self.assertRaises(ValueError):
            Capabilities.parse({**raw, "powerups": 1})
