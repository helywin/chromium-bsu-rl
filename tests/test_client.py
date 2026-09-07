"""Developer regression checks, not learner exercises. Uses only stdlib."""
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest

from chromium_rl import Action, GameClient, ProtocolError, RemoteError
from chromium_rl.client import _JsonProcess
from chromium_rl.state import boolean, integer, number, vector


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


@unittest.skipUnless(os.environ.get("RUN_CHROMIUM_GUI_TESTS") == "1", "explicit GUI opt-in required")
class NativeTests(unittest.TestCase):
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
            self.assertEqual(first, game.snapshot())
            self.assertIsNotNone(game._transport)
            transport = game._transport
            assert transport is not None
            with self.assertRaises(RemoteError):
                transport.call("step")
            self.assertEqual(first, game.snapshot())
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
