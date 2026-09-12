"""Display native enemy bullets and print their typed protocol state.

Run after building and installing: python examples/watch_enemy_bullets.py
The player remains idle; this is a state inspection example.
"""
import time

from chromium_rl import Action, GameClient


def main() -> None:
    with GameClient(synchronous=True) as game:
        game.reset(209)
        if not game.capabilities.enemy_bullets:
            raise RuntimeError("Rebuild the native game for enemy-bullet snapshots")
        print("Enemy bullets: position in world coordinates; velocity is displacement per tick.")
        for tick in range(600):
            result = game.step(Action.IDLE)
            bullets = result.snapshot.enemy_bullets
            if tick % 25 == 0:
                print(f"tick={result.episode_tick} enemy_bullets={len(bullets)}", flush=True)
                if bullets:
                    bullet = bullets[0]
                    print(f"  id={bullet.id} type={bullet.type} "
                          f"xy={bullet.position[:2]} delta={bullet.velocity_per_tick[:2]}", flush=True)
            if result.terminated:
                print("Episode ended:", result.snapshot.mode)
                break
            time.sleep(0.02)
        print("Final frame held for 3 seconds.")
        time.sleep(3)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
