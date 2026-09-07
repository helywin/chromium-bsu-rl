"""Read live state while YOU play in the native game window.

Goal: connect visible game motion to Python's real snapshot fields, not train DQN.
Prerequisite: build the game and install this package in your virtual environment.
Run from this checkout: <your-venv>/bin/python examples/watch_snapshot.py
In the course repo: .venv/bin/python third_party/chromium-bsu-rl/examples/watch_snapshot.py

Enter a game using its menu, move with arrow keys, and compare x/y printed here.
Observe lives_counter and mode when losing fighters; do not assume 0 means game over.
The screen keeps running between snapshots (0.5s apart); this is NOT env.step().
Close the window or press Ctrl+C in this terminal to end. No TODO/API guessing.
Success: visible movement corresponds to changing world positions; close exits
without leaving a game process. Failure: send the explicit error, not only 'no motion'.
No seeds, fixed-step control, rewards, policy learning or speedup are validated here.
"""
import time
from chromium_rl import GameClient, ProtocolError


def main() -> None:
    try:
        with GameClient() as game:
            print(game.capabilities, flush=True)
            while True:
                state = game.snapshot()
                player = state.player
                print(f"mode={state.mode:10s} frame={state.game_frame:6d} "
                      f"xy=({player.position[0]:7.3f}, {player.position[1]:7.3f}) "
                      f"lives_counter={player.lives_counter} score={player.score:.1f} "
                      f"enemies={len(state.enemies)}", flush=True)
                time.sleep(0.5)
    except KeyboardInterrupt:
        print("Stopped; owned game process cleaned up.")
    except ProtocolError as exc:
        print(f"Game connection ended: {exc}")


if __name__ == "__main__":
    main()
