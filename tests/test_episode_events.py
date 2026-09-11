"""Native cumulative episode events; no synthetic mutation of game state."""
import random
import unittest
from chromium_rl import GameClient


class EpisodeEventTests(unittest.TestCase):
    def test_real_events_monotonic_reset_and_score_split(self) -> None:
        observed: set[str] = set()
        isolated_shield_hit: bool = False
        with GameClient(synchronous=True, render_each_step=False, headless=True) as game:
            wire = game._transport
            assert wire is not None
            self.assertTrue(wire.call('hello')['episode_events'])
            self.assertTrue(wire.call('hello')['shield_damage'])
            for seed in range(1,17):
                state = wire.call('reset',seed=seed)
                self.assertTrue(all(v == 0 for v in state['episode_events'].values()))
                rng = random.Random(seed+100000)
                for _ in range(250):
                    before = state
                    result = wire.call('step',action=rng.randrange(18),ticks=5)
                    state = result['snapshot']
                    a,b = before['episode_events'],state['episode_events']
                    for key,value in b.items():
                        self.assertGreaterEqual(value,a[key])
                        if value>a[key]: observed.add(key)
                    # Below normal capacity there is no passive shield decay.
                    if (0 < before['player']['shields'] < 499
                            and b['pickups'] == a['pickups']
                            and b['lives_lost'] == a['lives_lost']
                            and b['shield_damage'] > a['shield_damage']):
                        self.assertAlmostEqual(b['shield_damage'] - a['shield_damage'],
                                               before['player']['shields'] - state['player']['shields'],
                                               places=4)
                        isolated_shield_hit = True
                    self.assertGreaterEqual(b['lives_lost'],b['enemies_escaped'])
                    self.assertGreaterEqual(b['lives_lost']-a['lives_lost'],
                                            before['player']['lives_counter']-state['player']['lives_counter'])
                    self.assertGreaterEqual(state['player']['score']+1e-5,
                                            b['pickup_score']+b['missed_powerup_score'])
                    self.assertEqual(state,wire.call('snapshot'))
                    if result['terminated']:break
        self.assertTrue(isolated_shield_hit)
        self.assertEqual(observed, {'enemies_destroyed','enemies_escaped','lives_lost',
                                    'pickups','missed_powerups','pickup_score','missed_powerup_score','shield_damage'})

    def test_passive_decay_does_not_count_as_damage(self) -> None:
        with GameClient(synchronous=True, render_each_step=False, headless=True) as game:
            wire = game._transport
            assert wire is not None
            before = wire.call('reset', seed=31)
            after = wire.call('step', action=0, ticks=1)['snapshot']
            self.assertLess(after['player']['shields'], before['player']['shields'])
            self.assertEqual(after['episode_events']['shield_damage'], 0)
