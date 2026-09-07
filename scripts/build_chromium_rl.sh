#!/usr/bin/env bash
# Copyright 2026 Chromium B.S.U. for RL contributors.
# Distributed under the Clarified Artistic License; see ../game/COPYING.
set -euo pipefail
project_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
for tool in autoreconf autoconf automake aclocal autopoint make pkg-config g++ msgfmt; do
    command -v "$tool" >/dev/null || { echo "Missing build tool: $tool" >&2; exit 1; }
done
pkg-config --exists sdl2 SDL2_image gl glu ftgl fontconfig openal freealut json-c || {
    echo 'Missing development libraries; see README.md.' >&2; exit 1;
}
jobs=${CHROMIUM_RL_BUILD_JOBS:-4}
[[ $jobs =~ ^[1-9][0-9]*$ ]] || { echo 'CHROMIUM_RL_BUILD_JOBS must be a positive integer.' >&2; exit 1; }
mkdir -p "$project_root/build"
# Regenerate Autotools only in an isolated build copy, never in tracked sources.
build_source=$(mktemp -d "$project_root/build/work.XXXXXX")
cp -a "$project_root/game/." "$build_source/"
cd "$build_source"
autoreconf -fvi
./configure --prefix="$project_root/build/install" --program-suffix=-rl \
    --disable-glc --disable-sdl --disable-glut --disable-glpng \
    --disable-sdlimage --disable-sdlmixer --disable-sdl2mixer
make -j"$jobs"
make install
echo "Built locally: $project_root/build/install/bin/chromium-bsu-rl"
echo "Build logs and intermediates retained: $build_source"
