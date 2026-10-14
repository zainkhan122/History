#!/usr/bin/env bash
# reelkit/setup.sh — idempotent toolkit bootstrap. Run at the start of every session:
#     source ~/History/reelkit/setup.sh   (or: source ~/History/bootstrap.sh — also wires git + prints resume)
#
# Everything heavy lives in ~/.cache (excluded from workspace snapshots -> never blows the
# 128 MB / 10k-file save budget). Re-running only fetches what is missing.
#
#   ~/.cache/bin/       ffmpeg (symlink), lightpanda, rhubarb
#   ~/.cache/kokoro/    Kokoro-82M ONNX int8 + voices        (Apache-2.0, CPU TTS)
#   ~/.cache/models/    LaMa ONNX inpainting                  (Apache-2.0)
#   ~/.cache/u2net/     rembg models (downloaded on first use)
#   ~/.cache/tools/     Rhubarb Lip Sync                      (MIT)
#   ~/.cache/tmp/       scratch (NOTE: /tmp is RAM-backed tmpfs here — don't render into it)
set -u
C="$HOME/.cache"; mkdir -p "$C"/{bin,kokoro,models,u2net,tools,tmp,node,npm-global}
export PATH="$C/node/bin:$C/npm-global/bin:$C/bin:$HOME/.local/bin:$PATH"
export NPM_CONFIG_PREFIX="$C/npm-global" NPM_CONFIG_CACHE="$C/npm-cache" PUPPETEER_CACHE_DIR="$C/puppeteer"
export HYPERFRAMES_NO_TELEMETRY=1 HYPERFRAMES_NO_UPDATE_CHECK=1 DO_NOT_TRACK=1
export U2NET_HOME="$C/u2net" LIGHTPANDA_DISABLE_TELEMETRY=true TMPDIR="$C/tmp"
export PIP_DISABLE_PIP_VERSION_CHECK=1
ok(){ printf '  \033[32m✓\033[0m %s\n' "$*"; }; bad(){ printf '  \033[31m✗\033[0m %s\n' "$*"; }
get(){ [ -s "$2" ] || { echo "  ↓ $(basename "$2")"; curl -fsSL --retry 3 -o "$2.part" "$1" && mv "$2.part" "$2"; }; }

echo "[1/8] python packages"
PKGS="imageio-ffmpeg faster-whisper librosa soundfile rembg onnxruntime kokoro-onnx auto-editor rlottie-python gradio_client"
python3 - <<'EOF' 2>/dev/null || pip install -q --user $PKGS 2>&1 | grep -v "^\s*$" | tail -3
import importlib.util as u, sys
mods = ["imageio_ffmpeg","faster_whisper","librosa","soundfile","rembg","onnxruntime","kokoro_onnx","rlottie_python","gradio_client"]
sys.exit(0 if all(u.find_spec(m) for m in mods) else 1)
EOF
ok "pip: $PKGS"

echo "[2/8] ffmpeg"
[ -x "$C/bin/ffmpeg" ] || ln -sf "$(python3 -c 'import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())')" "$C/bin/ffmpeg"
ffmpeg -hide_banner -version >/dev/null 2>&1 && ok "$(ffmpeg -version | head -1 | cut -c1-40)" || bad ffmpeg

echo "[3/8] lightpanda (AGPL-3.0 — fine to run as a tool; don't ship modified copies)"
get https://github.com/lightpanda-io/browser/releases/download/nightly/lightpanda-x86_64-linux "$C/bin/lightpanda"
chmod +x "$C/bin/lightpanda"; "$C/bin/lightpanda" version >/dev/null 2>&1 && ok lightpanda || bad lightpanda

echo "[4/8] kokoro tts models"
get https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/kokoro-v1.0.int8.onnx "$C/kokoro/kokoro-v1.0.int8.onnx"
get https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/voices-v1.0.bin "$C/kokoro/voices-v1.0.bin"
[ -s "$C/kokoro/voices-v1.0.bin" ] && ok kokoro || bad kokoro

echo "[5/8] rhubarb lip sync"
if [ ! -x "$C/bin/rhubarb" ]; then
  get https://github.com/DanielSWolf/rhubarb-lip-sync/releases/download/v1.14.0/Rhubarb-Lip-Sync-1.14.0-Linux.zip "$C/tools/rhubarb.zip"
  python3 -c "import zipfile;zipfile.ZipFile('$C/tools/rhubarb.zip').extractall('$C/tools')" && rm -f "$C/tools/rhubarb.zip"
  R=$(find "$C/tools" -maxdepth 2 -type f -name rhubarb | head -1); chmod +x "$R"; ln -sf "$R" "$C/bin/rhubarb"
fi
rhubarb --version >/dev/null 2>&1 && ok "$(rhubarb --version 2>&1 | grep -m1 -i version)" || bad rhubarb

echo "[6/8] LaMa inpainting (onnx)"
get https://huggingface.co/Carve/LaMa-ONNX/resolve/main/lama_fp32.onnx "$C/models/lama_fp32.onnx"
[ -s "$C/models/lama_fp32.onnx" ] && ok lama || bad lama

echo "[7/8] node 22 (HyperFrames needs >=22; no root needed)"
if ! node -v 2>/dev/null | grep -q '^v22'; then
  NV=$(curl -fsSL https://nodejs.org/dist/latest-v22.x/ | grep -o 'node-v22[^"]*linux-x64.tar.xz' | head -1)
  curl -fsSL "https://nodejs.org/dist/latest-v22.x/$NV" | tar -xJ -C "$C/node" --strip-components=1
fi
node -v >/dev/null 2>&1 && ok "node $(node -v)" || bad node

echo "[8/8] HyperFrames CLI (Apache-2.0) + headless Chrome"
HFV="${HYPERFRAMES_VERSION:-0.8.137}"
command -v hyperframes >/dev/null 2>&1 || npm i -g --silent "hyperframes@$HFV" >/dev/null 2>&1
command -v hyperframes >/dev/null 2>&1 && ok "hyperframes $(hyperframes --version 2>/dev/null | tail -1)" || bad hyperframes
ls "$C/hyperframes/chrome" 2>/dev/null | grep -q chrome || hyperframes browser ensure >/dev/null 2>&1
# chrome-headless-shell system libs + ffprobe (render preflight); passwordless sudo is available in this sandbox
if ! command -v ffprobe >/dev/null 2>&1 || ! ldconfig -p | grep -q libnss3; then
  sudo -n apt-get update -qq >/dev/null 2>&1
  sudo -n DEBIAN_FRONTEND=noninteractive apt-get install -y -qq ffmpeg libnspr4 libnss3 libatk1.0-0t64 libatk-bridge2.0-0t64 \
    libxdamage1 libxkbcommon0 libasound2t64 libatspi2.0-0t64 libgbm1 libxcomposite1 libxrandr2 libpango-1.0-0 libcairo2 \
    libcups2t64 libdrm2 libxfixes3 fonts-liberation >/dev/null 2>&1
fi
command -v ffprobe >/dev/null 2>&1 && ok ffprobe || bad "ffprobe (apt ffmpeg)"
mkdir -p "$C/tmp/hftmp"; export TMPDIR="$C/tmp/hftmp"     # /tmp is a ~1 GB RAM tmpfs; renders need disk
ls "$C/hyperframes/chrome" 2>/dev/null | grep -q chrome && ok "chrome-headless-shell" || bad "chrome (run: hyperframes browser ensure)"

echo "cache: $(du -sh "$C" 2>/dev/null | cut -f1)   workspace: $(du -sh --exclude=.cache --exclude=.local "$HOME" 2>/dev/null | cut -f1)"
