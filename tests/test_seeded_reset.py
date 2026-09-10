"""Native seeded reset regression; display-dependent integration checks."""
import os
import time
import unittest
from chromium_rl import Action, GameClient
from chromium_rl.client import RemoteError

@unittest.skipUnless(os.environ.get("RUN_CHROMIUM_GUI_TESTS") == "1", "native GUI opt-in required")
class SeededResetTests(unittest.TestCase):
    def trace(self, game, seed):
        initial = game.reset(seed)
        self.assertEqual(initial.mode, "game")
        self.assertEqual(initial.game_frame, 0)
        self.assertEqual(initial.player.position, (0.0, -3.0, 25.0))
        self.assertEqual(initial.player.keyboard_motion, (0.0, 0.0))
        self.assertEqual(initial.player.score, 0.0)
        self.assertEqual(initial.player.lives_counter, 4)
        self.assertEqual(initial.player.damage, -500.0)
        self.assertEqual(initial.player.shields, 500.0)
        self.assertEqual(initial.player.ammo_stock, (0.0, 0.0, 0.0))
        self.assertTrue(initial.player.visible)
        self.assertFalse(initial.paused)
        self.assertEqual(initial.level, 1)
        self.assertFalse(initial.enemies)
        self.assertFalse(initial.enemy_bullets)
        rows = [initial]
        actions = (Action.RIGHT_FIRE, Action.LEFT_FIRE, Action.FIRE, Action.IDLE)
        for index in range(250):
            result = game.step(actions[(index // 12) % len(actions)], ticks=10)
            if index == 0:
                self.assertEqual(result.episode_tick, 10)
            rows.append(result)
            if result.terminated:
                break
        self.assertTrue(any(row.snapshot.enemies for row in rows[1:]))
        self.assertTrue(any(row.snapshot.enemy_bullets for row in rows[1:]))
        self.assertTrue(any(row.snapshot.player.score > 0 for row in rows[1:]))
        return rows

    def test_repeat_seed_after_dirty_episode_and_across_render_modes(self):
        with GameClient(synchronous=True, render_each_step=False, video_driver="x11") as game:
            pid = game._transport.process.pid
            baseline = self.trace(game, 7)
            other = self.trace(game, 8)
            self.assertNotEqual(baseline, other)
            self.assertEqual(baseline, self.trace(game, 7))
            self.assertEqual(pid, game._transport.process.pid)
            state = game.reset(7)
            self.assertEqual(state, game.render())
            self.assertEqual(state, game.snapshot())
        with GameClient(synchronous=True, render_each_step=True, video_driver="x11") as game:
            self.assertEqual(baseline, self.trace(game, 7))

    def test_terminal_reset_and_repeated_release(self):
        with GameClient(synchronous=True, render_each_step=False, video_driver="x11") as game:
            initial = game.reset(19)
            for _ in range(600):
                result = game.step(Action.IDLE, ticks=50)
                if result.terminated:
                    break
            self.assertTrue(result.terminated)
            self.assertLess(result.snapshot.player.lives_counter, initial.player.lives_counter)
            with self.assertRaises(RemoteError):
                game.step(Action.IDLE)
            self.assertEqual(initial, game.reset(19))
            started = time.monotonic()
            for _ in range(20):
                game.step(Action.RIGHT_FIRE, ticks=10)
                self.assertEqual(initial, game.reset(19))
                idle = game.step(Action.IDLE)
                self.assertEqual(idle.episode_tick, 1)
                self.assertEqual(idle.snapshot.player.position, initial.player.position)
                self.assertEqual(idle.snapshot.player.keyboard_motion, (0.0, 0.0))
            print(f"20 dirty resets and idle steps: {time.monotonic() - started:.3f}s")

    def test_invalid_seed_does_not_mutate_state(self):
        with GameClient(synchronous=True, render_each_step=False, video_driver="x11") as game:
            for seed in (0, 4294967295):
                state = game.reset(seed)
                self.assertEqual(state, game.reset(seed))
            state = game.step(Action.RIGHT).snapshot
            for seed in (True, -1, 4294967296, 1.5, "7", None):
                with self.assertRaises(ValueError):
                    game.reset(seed)
                with self.assertRaises(RemoteError):
                    game._transport.call("reset", seed=seed)
                self.assertEqual(state, game.snapshot())
            with self.assertRaises(RemoteError):
                game._transport.call("reset")
            self.assertEqual(state, game.snapshot())
        with GameClient(video_driver="x11") as game:
            self.assertFalse(game.capabilities.reset)
            with self.assertRaises(RemoteError):
                game.reset(7)
