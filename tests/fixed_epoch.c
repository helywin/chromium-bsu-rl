/* Developer-only Linux regression helper, never used by the normal launcher.
 * Copyright 2026 Chromium B.S.U. for RL contributors.
 * Clarified Artistic License: see game/COPYING.
 * Upstream seeds srand(time(NULL)); pin that input to compare two builds.
 * This is NOT a public seed/reset implementation or determinism guarantee.
 */
#include <stdlib.h>
#include <time.h>

time_t time(time_t *out)
{
    const char *input = getenv("CHROMIUM_TEST_EPOCH");
    time_t epoch = input ? (time_t)strtoll(input, NULL, 10) : (time_t)1234567;
    if(out) *out = epoch;
    return epoch;
}
