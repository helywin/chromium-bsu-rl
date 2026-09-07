"""Sampling-only throughput; not a training or headless benchmark.

<venv>/bin/python scripts/benchmark_render_steps.py build/fixed-epoch.so
One isolated native environment at a time, same three fixed time seeds.
Startup/teardown excluded. Each call requests50 internal ticks.
"""
import json
import os
from pathlib import Path
import sys
import time

from chromium_rl import Action, GameClient


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    os.environ["LD_PRELOAD"] = str(Path(sys.argv[1]).resolve())
    reports = []
    for drawing in (True, False):
        ticks = decisions = 0
        seconds = 0.0
        for epoch in (1234567, 2345678, 3456789):
            os.environ["CHROMIUM_TEST_EPOCH"] = str(epoch)
            with GameClient(synchronous=True, render_each_step=drawing, video_driver="x11") as game:
                start = time.perf_counter()
                for _ in range(80):
                    result = game.step(Action.FIRE, ticks=50)
                    ticks += result.actual_ticks
                    decisions += 1
                    if result.terminated:
                        break
                seconds += time.perf_counter() - start
        reports.append(dict(render_each_step=drawing, ticks=ticks, decisions=decisions,
                            seconds=seconds, ticks_per_second=ticks/seconds,
                            decisions_per_second=decisions/seconds,
                            reference_realtime_multiplier=ticks/seconds/50))
    print(json.dumps(reports, indent=2))


if __name__ == "__main__":
    main()
