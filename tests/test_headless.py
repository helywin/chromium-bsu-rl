"""Native no-display mode, not an Xvfb or hidden-window test."""
import os
import unittest
from unittest.mock import patch
from chromium_rl import GameClient, Action, Snapshot
from chromium_rl.client import RemoteError


def trace(game: GameClient, seed: int) -> list:
    rows = [game.reset(seed)]
    for i in range(250):
        row = game.step((Action.RIGHT_FIRE, Action.LEFT_FIRE, Action.FIRE, Action.IDLE)[(i//12)%4], ticks=10)
        rows.append(row)
        if row.terminated:
            break
    return rows


class HeadlessTests(unittest.TestCase):
    def test_public_powerups_and_events_match_native_data(self) -> None:
        with GameClient(synchronous=True, render_each_step=False, headless=True) as game:
            for field in ('seed', 'powerups', 'episode_events', 'shield_damage', 'projectile_damage'):
                self.assertTrue(getattr(game.capabilities, field))
            initial = game.reset(209)
            self.assertEqual(initial.powerups, ())
            self.assertIsNotNone(initial.episode_events)
            seen = False
            for _ in range(220):
                state = game.step(Action.DOWN_RIGHT_FIRE, ticks=5).snapshot
                seen |= bool(state.powerups)
                self.assertIsNotNone(state.episode_events)
                assert state.episode_events is not None
                self.assertIsNotNone(state.episode_events.projectile_damage)
                wire = game._transport
                assert wire is not None
                self.assertEqual(state, Snapshot.parse(wire.call('snapshot'), capabilities=game.capabilities))
                if state.mode != 'game':
                    break
            self.assertTrue(seen, 'Need a real native powerup in the public API')
            self.assertEqual(initial, game.reset(209))

    def test_no_video_backend_and_reset(self) -> None:
        with patch.dict(os.environ, {'CHROMIUM_BSU_RL_HEADLESS':'1'}):
            os.environ.pop('DISPLAY', None)
            os.environ.pop('WAYLAND_DISPLAY', None)
            # An invalid driver would fail SDL_INIT_VIDEO even if a display server existed.
            with GameClient(synchronous=True, render_each_step=False, headless=True, video_driver='no-such-video-driver') as game:
                self.assertTrue(game.capabilities.headless)
                self.assertFalse(game.capabilities.render)
                first = trace(game, 7)
                self.assertEqual(first, trace(game, 7))
                self.assertTrue(any(r.snapshot.enemy_bullets for r in first[1:]))
                wire = game._transport
                assert wire is not None
                state = wire.call('snapshot')
                with self.assertRaises(RemoteError): wire.call('render')
                self.assertEqual(state, wire.call('snapshot'))

    @unittest.skipUnless(os.environ.get('RUN_CHROMIUM_GUI_TESTS')=='1', 'GUI comparison requires display')
    def test_gui_and_headless_same_trajectory(self) -> None:
        with patch.dict(os.environ, {'CHROMIUM_BSU_RL_HEADLESS':'0'}):
            with GameClient(synchronous=True, render_each_step=True, video_driver='x11') as game:
                reference = [trace(game, seed) for seed in (7,8,209)]
        with patch.dict(os.environ, {'CHROMIUM_BSU_RL_HEADLESS':'1'}):
            with GameClient(synchronous=True, render_each_step=False, headless=True, video_driver='no-such-video-driver') as game:
                self.assertEqual(reference, [trace(game, seed) for seed in (7,8,209)])
