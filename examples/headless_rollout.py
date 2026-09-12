"""Run a seeded first-level action sequence without a display server.

From a built, editable checkout: python examples/headless_rollout.py --seed 7
For an installed wheel, pass --binary and --data-dir as absolute paths.
This exercises the native runtime; the scripted actions are not a trained policy.
"""
import argparse
from dataclasses import asdict
import json
from pathlib import Path

from chromium_rl import Action, GameClient


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=7, help="Episode seed (uint32)")
    parser.add_argument("--steps", type=int, default=250, help="Maximum decisions, not simulation ticks")
    parser.add_argument("--ticks", type=int, default=5, help="Simulation ticks per decision (1..50)")
    parser.add_argument("--binary", type=Path, help="Built chromium-bsu-rl executable")
    parser.add_argument("--data-dir", type=Path, help="Game assets directory containing png/")
    args = parser.parse_args()
    if not 0 <= args.seed <= 4294967295 or args.steps < 1 or not 1 <= args.ticks <= 50:
        parser.error("seed must be uint32, steps positive, and ticks in 1..50")

    actions = (Action.RIGHT_FIRE, Action.LEFT_FIRE, Action.FIRE, Action.IDLE)
    with GameClient(binary=args.binary, data_directory=args.data_dir, synchronous=True,
                    render_each_step=False, headless=True) as game:
        if not (game.capabilities.powerups and game.capabilities.projectile_damage):
            raise RuntimeError("This example needs current native instrumentation; rebuild the game.")
        state = game.reset(args.seed)
        for decision in range(args.steps):
            result = game.step(actions[(decision // 12) % len(actions)], ticks=args.ticks)
            state = result.snapshot
            if result.terminated:
                break
        print(json.dumps({
            "implementation": game.capabilities.implementation,
            "seed": args.seed,
            "decisions": decision + 1,
            "episode_tick": result.episode_tick,
            "simulated_seconds": result.simulated_seconds,
            "terminated": result.terminated,
            "decision_limit_reached": not result.terminated,
            "mode": state.mode,
            "score": state.player.score,
            "powerups": len(state.powerups) if state.powerups is not None else None,
            "episode_events": asdict(state.episode_events) if state.episode_events is not None else None,
        }, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
