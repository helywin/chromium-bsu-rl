"""Display a seeded sequence of native actions and frozen intervals.

Run after building and installing the package: python examples/watch_steps.py
--delay changes playback pacing; each action still advances one simulation tick.
The pauses stop requests, so the game stays frozen without physical key input.
"""
import argparse
import math
import time

from chromium_rl import Action, GameClient


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--delay", type=float, default=0.08, help="Viewing seconds between steps")
    parser.add_argument("--seed", type=int, default=7, help="Episode seed (uint32)")
    args = parser.parse_args()
    if not math.isfinite(args.delay) or not 0 <= args.delay <= 2:
        parser.error("delay must be finite and between 0 and 2 seconds")
    with GameClient(synchronous=True) as game:
        game.reset(args.seed)
        print("Python controls time. Keyboard/mouse gameplay input is ignored.")
        game.step(Action.IDLE)  # Present the first complete frame.
        for label, action in (("right", Action.RIGHT_FIRE), ("release", Action.IDLE),
                              ("left", Action.LEFT_FIRE), ("up-right", Action.UP_RIGHT_FIRE)):
            for _ in range(12):
                result = game.step(action)
                print(f"{label:8} tick={result.episode_tick:3} "
                      f"time={result.simulated_seconds:.2f}s "
                      f"xy={result.snapshot.player.position[:2]}")
                if result.terminated:
                    print("Single-level episode ended:", result.snapshot.mode)
                    return
                time.sleep(args.delay)  # For your eyes only, never part of the logic step.
            before = game.snapshot()
            print("No requests for 2 seconds: the game should freeze.")
            time.sleep(2)
            print("Snapshot unchanged:", before == game.snapshot())
        print("Done. This demonstrates control, not a learned policy.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
