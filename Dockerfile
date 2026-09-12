# Development image with source, local native build and an isolated Python venv.
ARG BASE_IMAGE=ubuntu:24.04
FROM ${BASE_IMAGE}
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates build-essential autoconf automake autopoint gettext pkg-config \
    libsdl2-dev libsdl2-image-dev libgl1-mesa-dev libglu1-mesa-dev libftgl-dev \
    libfontconfig1-dev libopenal-dev libalut-dev libjson-c-dev \
    python3 python3-venv xvfb xauth libgl1-mesa-dri fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 chromiumrl \
    && mkdir -p /opt/chromium-bsu-rl \
    && chown chromiumrl:chromiumrl /opt/chromium-bsu-rl
WORKDIR /opt/chromium-bsu-rl
USER chromiumrl
COPY --chown=chromiumrl:chromiumrl . .
RUN bash scripts/build_chromium_rl.sh \
    && python3 -m venv .venv \
    && .venv/bin/python -m pip install --no-cache-dir -e '.[dev]'
CMD [".venv/bin/python", "examples/headless_rollout.py"]
