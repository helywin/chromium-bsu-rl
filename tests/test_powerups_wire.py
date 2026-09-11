"""Additive powerup wire fields; native, display-dependent, no mock state."""
import os
import unittest
from chromium_rl import GameClient


@unittest.skipUnless(os.environ.get('RUN_CHROMIUM_GUI_TESTS') == '1', 'native display opt-in required')
class PowerUpWireTests(unittest.TestCase):
    def test_read_only_ids_motion_and_seed_reset(self) -> None:
        with GameClient(synchronous=True, render_each_step=False, video_driver='x11') as game:
            wire = game._transport
            assert wire is not None
            self.assertTrue(wire.call('hello')['powerups'])
            traces: list[list[dict]] = []
            for _ in range(2):
                initial = wire.call('reset', seed=209)
                self.assertEqual(initial['powerups'], [])
                rows: list[dict] = [initial]
                tracked = 0
                for _ in range(1100):
                    result = wire.call('step', action=17, ticks=1)
                    state = result['snapshot']
                    previous = {p['id']: p for p in rows[-1]['powerups']}
                    ids = [p['id'] for p in state['powerups']]
                    self.assertEqual(len(ids), len(set(ids)))
                    for p in state['powerups']:
                        self.assertGreater(p['id'], 0)
                        self.assertIn(p['type'], range(6))
                        if p['id'] in previous:
                            old = previous[p['id']]
                            self.assertEqual(p['type'], old['type'])
                            self.assertAlmostEqual(p['position'][1] - old['position'][1],
                                                   old['next_displacement'][1], places=4)
                            tracked += 1
                    if state['powerups'] and len(rows) % 50 == 0:
                        self.assertEqual(state, wire.call('snapshot'))
                        self.assertEqual(state, wire.call('render'))
                    rows.append(state)
                    if result['terminated']:
                        break
                self.assertGreater(tracked, 10)
                traces.append(rows)
            self.assertEqual(traces[0], traces[1])
