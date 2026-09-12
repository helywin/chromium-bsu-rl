# Episode event instrumentation validation

Build: `scripts/build_chromium_rl.sh` (existing dependencies, local install only).
Reproduction command normalized to the standalone checkout and `.venv`:

```bash
RUN_CHROMIUM_GUI_TESTS=1 .venv/bin/python -m unittest discover -s tests -v
```

16 tests passed, including new headless native event test. Seeds1..16, random action
seed100000+game seed,5ticks/decision, up to250 decisions per episode. Observed all
seven fields increasing in real gameplay, reset zeros, monotonic counters, read-only
snapshot, livesLost>=escaped and accounted pickup/miss score<=raw total.
This tests naturally occurring pickups/destruction/escapes/losses, not synthetic events.

Also compared pre-instrumentation binary `/tmp/chromium-before-events` to current
headless wire traces for seeds7/209/30002, actions13/12/9/0 switching every12 decisions,
5ticks/decision, up to250 decisions or terminal. Removing only the additive events
object made all remaining raw step results equal (190/218/179 decisions respectively).

Actual subtraction sites were reviewed for all three lives-- paths, including
self-destruct. The 18-action RL API does not expose self-destruct; that path was not
triggered by the native random test. Enemy destruction is not exclusively player-shot
attribution; boss-chain destruction is counted as documented. No new game rewards,
collision rules, game RNG draws or visual behavior were introduced.
