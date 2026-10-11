#!/usr/bin/env bash
# One-command episode pipeline — identical in the sandbox and on GitHub Actions.
#   bash reelkit/episode.sh <episode_dir> [stage...]
# stages (default: all): pull trim plan score assets build lint snap render encode qa
# Build dir: $BUILD (default ~/.cache/build/<episode-name>) — never inside the repo.
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EP="$(cd "$1" && pwd)"; shift || true
NAME="$(basename "$EP")"
BUILD="${BUILD:-$HOME/.cache/build/$NAME}"; HF="$BUILD/hf"
STAGES="${*:-pull trim plan score assets build lint render encode qa}"
FPS="${FPS:-30}"; CRF="${CRF:-18}"; WORKERS="${WORKERS:-auto}"
export HYPERFRAMES_NO_TELEMETRY=1 HYPERFRAMES_NO_UPDATE_CHECK=1 DO_NOT_TRACK=1 HYPERFRAMES_SKIP_SKILLS=1
export PATH="$HOME/.cache/bin:$HOME/.cache/node/bin:$HOME/.cache/npm-global/bin:/usr/local/bin:$PATH"
mkdir -p "$BUILD" "$HOME/.cache/tmp/hftmp"; export TMPDIR="$HOME/.cache/tmp/hftmp"
log() { printf '\n== [%s] %s\n' "$NAME" "$*"; }
has() { [[ " $STAGES " == *" $1 "* ]]; }

has pull   && { log "pull media (release assets -> $EP)"; python3 "$REPO/reelkit/media.py" pull "$EP"; }
has trim   && { log "trim VO"; python3 "$REPO/reelkit/trim_vo.py" "$EP/vo" "$BUILD" --check "$EP/words.json"; }
has plan   && { log "timeline"; python3 "$EP/plan.py" >/dev/null; }
has score  && { log "score + SFX + mix (-14 LUFS)"; python3 "$EP/score.py" "$BUILD" "$BUILD"; }
has assets && { log "visual assets"; python3 "$EP/make_assets.py" "$HF"; [ -f "$EP/clips.json" ] && python3 "$REPO/reelkit/clips.py" prep "$EP" "$HF" || true; }
has build  && { log "composition"; python3 "$EP/build.py" "$HF"; cp "$BUILD/mix.wav" "$HF/assets/mix.wav"; }
has lint   && { log "lint"; (cd "$HF" && hyperframes lint 2>&1 | grep -E "✗|◇" || true); (cd "$HF" && ! hyperframes lint 2>&1 | grep -q "✗"); }
has snap   && { log "snapshots"; (cd "$HF" && hyperframes snapshot --at "${SNAP_AT:-1,20,47,71,86}" --no-end --timeout 30000 -o "$BUILD/snaps" >/dev/null 2>&1); ls "$BUILD/snaps"; }
has render && { log "render ${FPS}fps crf $CRF workers $WORKERS"; (cd "$HF" && hyperframes render -f "$FPS" -w "$WORKERS" --crf "$CRF" -o "$BUILD/render.mp4" 2>&1 | grep -vE "@hf-progress|Render:trace|^\s+█" | tail -12); }
has encode && { log "delivery encode (~3.6 Mbps, faststart)"; mkdir -p "$EP/out"
  ffmpeg -hide_banner -loglevel error -y -i "$BUILD/render.mp4" -i "$BUILD/mix.wav" -map 0:v -map 1:a -c:v libx264 -preset "${PRESET:-faster}" \
    -crf 21 -maxrate 3.6M -bufsize 7.2M -pix_fmt yuv420p -profile:v high -level 4.2 -r "$FPS" -g 60 -c:a aac -b:a 192k -ar 48000 \
    -movflags +faststart -shortest "$EP/out/final.mp4"
  ffmpeg -hide_banner -loglevel error -y -ss "${COVER_AT:-1.3}" -i "$BUILD/render.mp4" -frames:v 1 -q:v 2 "$EP/out/cover.jpg"; ls -la "$EP/out"; }
has qa     && { log "QA"; python3 "$REPO/reelkit/qa.py" "$EP/out/final.mp4" --words "$EP/timeline.json" --report "$EP/out/qa.json"; }
log "done → $EP/out"
