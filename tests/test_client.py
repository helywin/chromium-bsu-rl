"""Transport/parser regressions and optional native display checks using stdlib."""
import os
from dataclasses import replace
from pathlib import Path
import sys
import tempfile
import time
import unittest

from chromium_rl import Action, GameClient, ProtocolError, RemoteError
from chromium_rl.client import _JsonProcess
from chromium_rl.state import EnemyBulletState, boolean, integer, number, vector


class TransportTests(unittest.TestCase):
    def peer(self, mode: str) -> _JsonProcess:
        state = tempfile.TemporaryDirectory(prefix="chromium-peer-")
        self.addCleanup(state.cleanup)
        result = _JsonProcess([sys.executable, str(Path(__file__).with_name("protocol_peer.py")), mode],
                              os.environ, Path(state.name) / "log", 0.15)
        self.addCleanup(result.stop)
        return result

    def test_success_and_remote_error_recovery(self) -> None:
        peer = self.peer("normal")
        self.assertEqual(peer.call("hello"), {})
        with self.assertRaises(RemoteError):
            peer.call("bad")
        self.assertEqual(peer.call("close"), {})
        peer.stop()
        peer.stop()
        self.assertEqual(peer.process.returncode, 0)

    def test_transport_failures_reap_owned_child(self) -> None:
        for mode in ("eof", "timeout", "malformed", "large", "wrong_id"):
            with self.subTest(mode=mode):
                peer = self.peer(mode)
                with self.assertRaises(ProtocolError):
                    peer.call("hello")
                self.assertIsNotNone(peer.process.poll())
                with self.assertRaises(ProtocolError):
                    peer.call("snapshot")

    def test_state_rejects_wrong_types_and_nonfinite(self) -> None:
        for function, value in ((integer, True), (boolean, 1), (number, "1"),
                                (number, float("nan")), (number, float("inf")), (number, 10 ** 1000)):
            with self.assertRaises(ValueError):
                function(value)
        with self.assertRaises(ValueError):
            vector([1, 2], 3)

    def test_enemy_bullet_validation(self) -> None:
        data = dict(id=1, type=0, position=[0, 1, 25],
                    velocity_per_tick=[0, -0.2, 0], sprite_half_size=[0.25, 0.55], damage=75)
        self.assertEqual(EnemyBulletState.parse(data).velocity_per_tick[1], -0.2)
        for key, value in (("id", True), ("id", 0), ("type", 5),
                           ("position", [0, 1]), ("velocity_per_tick", [0, float("nan"), 0]),
                           ("sprite_half_size", [0, 1])):
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                EnemyBulletState.parse({**data, key: value})


@unittest.skipUnless(os.environ.get("RUN_CHROMIUM_GUI_TESTS") == "1", "explicit GUI opt-in required")
class NativeTests(unittest.TestCase):
    def test_enemy_bullets_and_render(self) -> None:
        with GameClient(synchronous=True, render_each_step=False, video_driver="x11") as game:
            self.assertTrue(game.capabilities.render_free_steps)
            self.assertTrue(game.capabilities.enemy_bullets)
            self.assertFalse(game.capabilities.headless)
            self.assertEqual(game.snapshot(), game.render())
            previous = {}
            moved = 0
            for _ in range(2000):
                result = game.step(Action.IDLE)
                bullets = {b.id: b for b in result.snapshot.enemy_bullets}
                for identity in previous.keys() & bullets.keys():
                    old, new = previous[identity], bullets[identity]
                    self.assertEqual(old.type, new.type)
                    self.assertEqual(old.velocity_per_tick, new.velocity_per_tick)
                    for axis in range(3):
                        self.assertAlmostEqual(new.position[axis],
                                               old.position[axis] + old.velocity_per_tick[axis], places=5)
                    moved += 1
                previous = bullets
                if moved >= 5 or result.terminated:
                    break
            self.assertGreaterEqual(moved, 5)
            state = game.snapshot()
            for _ in range(3):
                self.assertEqual(state, game.render())
            self.assertEqual(state, game.snapshot())

    def test_single_level_terminal_freezes(self) -> None:
        with GameClient(synchronous=True, video_driver="x11") as game:
            for _ in range(400):
                result = game.step(Action.IDLE, ticks=50)
                if result.terminated:
                    break
            self.assertTrue(result.terminated)
            self.assertIn(result.snapshot.mode, ("hero_dead", "level_over"))
            before = game.snapshot()
            with self.assertRaises(RemoteError):
                game.step(Action.IDLE)
            self.assertEqual(before, game.snapshot())

    def test_synchronous_steps_and_idle(self) -> None:
        with GameClient(synchronous=True, video_driver="x11") as game:
            self.assertTrue(game.capabilities.step)
            initial = game.snapshot()
            self.assertEqual(initial.game_frame, 0)
            self.assertEqual(initial.mode, "game")
            time.sleep(0.15)
            self.assertEqual(initial, game.snapshot())
            first = game.step(Action.RIGHT)
            self.assertEqual(first.actual_ticks, 1)
            self.assertEqual(first.episode_tick, 1)
            self.assertEqual(first.snapshot.game_frame, 1)
            self.assertAlmostEqual(first.snapshot.player.position[0], 0.18, places=5)
            self.assertAlmostEqual(first.snapshot.player.keyboard_motion[0], 6.3, places=5)
            second = game.step(Action.RIGHT)
            self.assertAlmostEqual(second.snapshot.player.keyboard_motion[0], 7.574, places=5)
            self.assertAlmostEqual(second.snapshot.player.position[0], 0.39, places=5)
            released = game.step(Action.IDLE)
            self.assertAlmostEqual(released.snapshot.player.keyboard_motion[0], 5.3018, places=5)
            self.assertAlmostEqual(released.snapshot.player.position[0], 0.54, places=5)
            multi = game.step(Action.UP_RIGHT, ticks=3)
            self.assertEqual(multi.episode_tick, 6)
            self.assertEqual(multi.actual_ticks, 3)
            self.assertEqual(multi.snapshot.game_frame, 6)
            self.assertEqual(multi.snapshot.speed_adjustment, 1)
            self.assertGreater(multi.snapshot.player.position[1], -3)
            time.sleep(0.15)
            self.assertEqual(multi.snapshot, game.snapshot())
            transport = game._transport
            assert transport is not None
            for action, ticks in ((True, 1), (18, 1), (0, 0), (0, 51), (0, 1.0)):
                with self.assertRaises(RemoteError):
                    transport.call("step", action=action, ticks=ticks)
                self.assertEqual(multi.snapshot, game.snapshot())
            for ticks in (True, 0, 51):
                with self.assertRaises(ValueError):
                    game.step(Action.IDLE, ticks=ticks)

    def test_live_snapshot_and_close(self) -> None:
        with GameClient(video_driver="x11", debug=True) as game:
            self.assertTrue(game.capabilities.live_snapshot)
            self.assertFalse(game.capabilities.step)
            self.assertFalse(game.capabilities.reset)
            self.assertFalse(game.capabilities.deterministic)
            first = game.snapshot()
            self.assertEqual(first.mode, "menu")
            self.assertEqual(first.player.position, (0.0, -3.0, 25.0))
            self.assertEqual(first.player.lives_counter, 4)
            # Live menu's RNG cursor is not frozen.
            self.assertEqual(first, replace(game.snapshot(), rng_cursor=first.rng_cursor))
            self.assertIsNotNone(game._transport)
            transport = game._transport
            assert transport is not None
            with self.assertRaises(RemoteError):
                transport.call("step")
            self.assertEqual(first, replace(game.snapshot(), rng_cursor=first.rng_cursor))
            process = transport.process
        self.assertEqual(process.returncode, 0)
        game.close()
        with self.assertRaises(ProtocolError):
            game.snapshot()

    def test_eof_closes_game(self) -> None:
        game = GameClient(video_driver="x11")
        transport = game._transport
        assert transport is not None
        transport.stop()  # close stdin; native loop should exit without window injection
        self.assertEqual(transport.process.returncode, 0)
        game.close()


if __name__ == "__main__":
    unittest.main()
