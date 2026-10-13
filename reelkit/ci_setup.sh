#!/usr/bin/env bash
# Toolchain for a GitHub Actions ubuntu runner (public repo: 4 vCPU / 16 GB). Node 22 comes from actions/setup-node.
# Cached by actions/cache: ~/.cache/hyperframes (chrome-headless-shell), ~/.cache/pip, ~/.cache/huggingface.
set -euo pipefail
HFV="${HYPERFRAMES_VERSION:-0.8.137}"
export HYPERFRAMES_NO_TELEMETRY=1 HYPERFRAMES_NO_UPDATE_CHECK=1 DO_NOT_TRACK=1 HYPERFRAMES_SKIP_SKILLS=1
echo "== apt: ffmpeg + chrome-headless-shell libs"
sudo apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq ffmpeg libnspr4 libnss3 libatk1.0-0t64 libatk-bridge2.0-0t64 \
  libxdamage1 libxkbcommon0 libasound2t64 libatspi2.0-0t64 libgbm1 libxcomposite1 libxrandr2 libpango-1.0-0 libcairo2 \
  libcups2t64 libdrm2 libxfixes3 fonts-liberation >/dev/null
echo "== hyperframes@$HFV + browser"
npm i -g --silent "hyperframes@$HFV" >/dev/null 2>&1
hyperframes browser ensure >/dev/null 2>&1 || true
echo "== python deps"
python3 -m pip install -q --upgrade pip >/dev/null 2>&1 || true
# every Python dependency of the pipeline gates (voice: librosa; provenance: fontTools; qa/voice: faster-whisper)
PYDEPS="numpy scipy soundfile pillow faster-whisper librosa fonttools"
python3 -m pip install -q $PYDEPS 2>/dev/null || python3 -m pip install -q --break-system-packages $PYDEPS
# preflight: fail in seconds with a clear message, not 10 minutes into a render
python3 -c "import numpy, scipy, soundfile, PIL, faster_whisper, librosa, fontTools" || { echo "ci_setup: Python gate dependencies missing" >&2; exit 1; }
echo "CI_SETUP_DONE nproc=$(nproc) mem=$(free -g | awk '/Mem/{print $2}')G node=$(node -v) hf=$(hyperframes --version 2>/dev/null | tail -1)"
