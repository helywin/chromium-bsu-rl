"""Linux native reset resource smoke check; opens one X11 game window.

Run with the consuming virtualenv from this repository. This is a bounded
resource check, not a leak detector or evidence of indefinitely stable training.
"""
from pathlib import Path
import json
import time
from chromium_rl import Action, GameClient


def resources(pid):
    root = Path(f"/proc/{pid}")
    status = (root / "status").read_text()
    rss = next(int(line.split()[1]) for line in status.splitlines() if line.startswith("VmRSS:"))
    return {"rss_kib": rss, "fds": len(list((root / "fd").iterdir()))}


def main():
    with GameClient(synchronous=True, render_each_step=False, video_driver="x11") as game:
        pid = game._transport.process.pid
        for _ in range(20):
            game.reset(7)
            game.step(Action.RIGHT_FIRE, ticks=10)
        before = resources(pid)
        start = time.monotonic()
        for _ in range(200):
            game.reset(7)
            game.step(Action.RIGHT_FIRE, ticks=10)
        elapsed = time.monotonic() - start
        after = resources(pid)
        assert before["fds"] == after["fds"], (before, after)
        # A deliberately broad smoke bound permits allocator/driver caching.
        assert after["rss_kib"] - before["rss_kib"] < 32 * 1024, (before, after)
    assert not Path(f"/proc/{pid}").exists(), "owned game did not exit"
    print(json.dumps({"warmup_resets": 20, "measured_resets": 200,
                      "before": before, "after": after, "elapsed_seconds": elapsed,
                      "process_exited": True}, indent=2))


if __name__ == "__main__":
    main()
