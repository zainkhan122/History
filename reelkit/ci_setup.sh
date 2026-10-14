#!/usr/bin/env bash
# Toolchain for a GitHub Actions ubuntu runner (public repo: 4 vCPU / 16 GB). Node 22 comes from actions/setup-node.
# Cached by actions/cache: ~/.cache/hyperframes (chrome-headless-shell), ~/.cache/pip, ~/.cache/huggingface.
set -euo pipefail
HFV="${HYPERFRAMES_VERSION:-0.8.137}"
export HYPERFRAMES_NO_TELEMETRY=1 HYPERFRAMES_NO_UPDATE_CHECK=1 DO_NOT_TRACK=1 HYPERFRAMES_SKIP_SKILLS=1
echo "== apt: ffmpeg + chrome-headless-shell libs"
retry() { local n=0; until "$@"; do n=$((n+1)); [ $n -ge 3 ] && return 1; echo "  … retry $n/2: $*" >&2; sleep $((10*n)); done; }
APT="-o Acquire::Retries=3 -o Acquire::http::Timeout=30"
retry sudo apt-get $APT update -qq
retry sudo DEBIAN_FRONTEND=noninteractive apt-get $APT install -y -qq ffmpeg libnspr4 libnss3 libatk1.0-0t64 libatk-bridge2.0-0t64 \
  libxdamage1 libxkbcommon0 libasound2t64 libatspi2.0-0t64 libgbm1 libxcomposite1 libxrandr2 libpango-1.0-0 libcairo2 \
  libcups2t64 libdrm2 libxfixes3 fonts-liberation >/dev/null
echo "== hyperframes@$HFV + browser"
retry npm i -g --silent "hyperframes@$HFV" >/dev/null
retry hyperframes browser ensure >/dev/null
# fail fast (seconds) instead of 10 minutes into a render: CLI version pinned, browser binary present
hyperframes --version 2>/dev/null | grep -q "$HFV" || { echo "ci_setup: hyperframes@$HFV not installed" >&2; exit 1; }
ls "$HOME"/.cache/hyperframes/chrome/chrome-headless-shell/*/chrome-headless-shell-linux64/chrome-headless-shell >/dev/null 2>&1 \
  || { echo "ci_setup: chrome-headless-shell missing after 'hyperframes browser ensure'" >&2; exit 1; }
command -v ffmpeg >/dev/null || { echo "ci_setup: ffmpeg missing" >&2; exit 1; }
echo "== python deps"
python3 -m pip install -q --upgrade pip >/dev/null 2>&1 || true
# every Python dependency of the pipeline gates (voice: librosa; provenance: fontTools; qa/voice: faster-whisper)
PYDEPS="numpy scipy soundfile pillow faster-whisper librosa fonttools"
retry python3 -m pip install -q $PYDEPS 2>/dev/null || retry python3 -m pip install -q --break-system-packages $PYDEPS
# preflight: fail in seconds with a clear message, not 10 minutes into a render
python3 -c "import numpy, scipy, soundfile, PIL, faster_whisper, librosa, fontTools" || { echo "ci_setup: Python gate dependencies missing" >&2; exit 1; }
echo "CI_SETUP_DONE nproc=$(nproc) mem=$(free -g | awk '/Mem/{print $2}')G node=$(node -v) hf=$(hyperframes --version 2>/dev/null | tail -1)"
