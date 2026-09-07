"""Visible synchronous control demonstration, not learner training.

Run from the course repository:
  .venv/bin/python third_party/chromium-bsu-rl/examples/watch_steps.py
Standalone checkout: <venv>/bin/python examples/watch_steps.py

The two pauses below stop Python requests, not the game's pause flag.
The GUI must stay frozen during them. No physical keys are required.

Optional one-variable experiment: compare --delay 0.02 and --delay 0.15.
Only viewing delay changes, not actions or ticks. Compare early xy/tick outputs,
not scores across unseeded runs. Success: no extra ticks and idle snapshots stay
unchanged. This is not evidence of seeded full-game determinism.
"""
import argparse
import math
import time

from chromium_rl import Action, GameClient


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--delay", type=float, default=0.08, help="Viewing seconds between steps")
    args = parser.parse_args()
    if not math.isfinite(args.delay) or not 0 <= args.delay <= 2:
        parser.error("delay must be finite and between 0 and 2 seconds")
    with GameClient(synchronous=True) as game:
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
