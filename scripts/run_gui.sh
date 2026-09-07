#!/usr/bin/env bash
# Copyright 2026 Chromium B.S.U. for RL contributors.
# Distributed under the Clarified Artistic License; see ../game/COPYING.
set -euo pipefail
project_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
binary="$project_root/build/install/bin/chromium-bsu-rl"
[[ -x $binary ]] || { echo 'Build first: bash scripts/build_chromium_rl.sh' >&2; exit 1; }
# Upstream uses several fixed 256-byte path buffers. Fail before launching.
[[ ${#project_root} -lt 180 ]] || { echo 'Project path is too long for upstream path buffers.' >&2; exit 1; }
export CHROMIUM_BSU_RL_STATE_DIR="$project_root/build/state"
export CHROMIUM_BSU_SCORE="$CHROMIUM_BSU_RL_STATE_DIR/high-scores"
export CHROMIUM_BSU_DATA="$project_root/game/data"
mkdir -p "$CHROMIUM_BSU_RL_STATE_DIR"
cd "$project_root"
exec "$binary" --window --vidmode 1 --noaudio "$@"
