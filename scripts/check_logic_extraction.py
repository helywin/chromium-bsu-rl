"""Compare native snapshots before/after refactoring.

Linux only. Build tests/fixed_epoch.c as a shared library, then:
<venv>/bin/python scripts/check_logic_extraction.py BEFORE_BINARY AFTER_BINARY LIBRARY
The preload is confined to children of this process. It fixes upstream's
time-based seed; it is not a runtime seed/reset feature. Display/GL required.
Full raw snapshots are compared each tick, not unexported bullets/particles.
Only compare the same behavior/schema version; v1 to split-render-v2 is an
intentional RNG contract change. Use check_render_equivalence.py for v2.
"""
import os
from pathlib import Path
import sys

from chromium_rl import Action, GameClient


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    before, after, library = (Path(arg).resolve() for arg in sys.argv[1:])
    os.environ["LD_PRELOAD"] = str(library)
    total = 0
    for epoch in (1234567, 2345678, 3456789):
        os.environ["CHROMIUM_TEST_EPOCH"] = str(epoch)
        for pattern in ("idle", "fire", "movement"):
            with GameClient(binary=before, synchronous=True, video_driver="x11") as old, \
                 GameClient(binary=after, synchronous=True, video_driver="x11") as new:
                if old.capabilities.implementation != new.capabilities.implementation:
                    raise RuntimeError("Different behavior versions; use check_render_equivalence.py for v2")
                assert old.snapshot() == new.snapshot(), (epoch, pattern, "initial")
                for tick in range(4000):
                    if pattern == "idle":
                        action = Action.IDLE
                    elif pattern == "fire":
                        action = Action.FIRE
                    else:
                        action = (Action.RIGHT_FIRE, Action.UP_LEFT_FIRE,
                                  Action.DOWN_RIGHT_FIRE, Action.IDLE)[(tick // 25) % 4]
                    expected, actual = old.step(action), new.step(action)
                    if expected != actual:
                        raise AssertionError((epoch, pattern, tick + 1, expected, actual))
                    total += 1
                    if actual.terminated:
                        break
                print(f"epoch={epoch} pattern={pattern} ticks={tick + 1} "
                      f"mode={actual.snapshot.mode}: identical", flush=True)
    print(f"PASS: {total} complete exported snapshots compared", flush=True)


if __name__ == "__main__":
    main()
