"""Print live snapshots while you play in the native window.

Run after building and installing the package: python examples/watch_snapshot.py
Enter a game from its menu and move with arrow keys. The real-time loop keeps
running between reads; sampling every 0.5 seconds does not define a step.
Close the window or press Ctrl+C to stop the owned process.
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
                      f"enemies={len(state.enemies)} enemy_bullets={len(state.enemy_bullets)}", flush=True)
                time.sleep(0.5)
    except KeyboardInterrupt:
        print("Stopped; owned game process cleaned up.")
    except ProtocolError as exc:
        print(f"Game connection ended: {exc}")


if __name__ == "__main__":
    main()
