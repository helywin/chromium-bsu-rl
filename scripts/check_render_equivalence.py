"""Native render-on/off comparison, Linux display/GL required.

Run: <venv>/bin/python scripts/check_render_equivalence.py build/fixed-epoch.so
Compile that developer-only preload using tests/fixed_epoch.c first.
Pin three upstream time-seed inputs; compare complete schema-2 snapshots,
including enemy bullets and gameplay RNG. This is not a public seed/reset API.
"""
import os
from pathlib import Path
import sys
import time

from chromium_rl import Action, GameClient


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    os.environ["LD_PRELOAD"] = str(Path(sys.argv[1]).resolve())
    total = 0
    seen_types: set[int] = set()
    for epoch in (1234567, 2345678, 3456789):
        os.environ["CHROMIUM_TEST_EPOCH"] = str(epoch)
        for pattern in ("idle", "fire", "movement"):
            with GameClient(synchronous=True, video_driver="x11") as drawn, \
                 GameClient(synchronous=True, render_each_step=False, video_driver="x11") as skipped:
                assert drawn.snapshot() == skipped.snapshot()
                for tick in range(4000):
                    action = Action.IDLE if pattern == "idle" else Action.FIRE
                    if pattern == "movement":
                        action = (Action.RIGHT_FIRE, Action.UP_LEFT_FIRE,
                                  Action.DOWN_RIGHT_FIRE, Action.IDLE)[(tick // 25) % 4]
                    expected, actual = drawn.step(action), skipped.step(action)
                    if expected != actual:
                        raise AssertionError((epoch, pattern, tick + 1, expected, actual))
                    seen_types.update(b.type for b in actual.snapshot.enemy_bullets)
                    total += 1
                    if tick % 100 == 0:
                        state = skipped.snapshot()
                        assert state == skipped.render() == skipped.render()
                        time.sleep(0.005)
                        assert state == skipped.snapshot()
                    if actual.terminated:
                        assert actual.snapshot == skipped.render() == skipped.render()
                        break
                print(f"epoch={epoch} pattern={pattern} ticks={tick + 1} "
                      f"mode={actual.snapshot.mode}: identical", flush=True)
    print(f"PASS: {total} snapshots; enemy bullet types observed={sorted(seen_types)}", flush=True)


if __name__ == "__main__":
    main()
