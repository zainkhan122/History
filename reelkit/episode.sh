#!/usr/bin/env bash
# One-command episode pipeline — identical in the sandbox and on GitHub Actions.
#   bash reelkit/episode.sh <episode_dir> [stage...]
# stages (default: all): pull trim plan score assets build facts check textqa snap render encode qa   ('lint' = alias of check)
# out/ is SCRATCH (snapshot-excluded): finished files live only in GitHub Releases (cloud.py render --tag …).
# Build dir: $BUILD (default ~/.cache/build/<episode-name>) — never inside the repo.
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EP="$(cd "$1" && pwd)"; shift || true
NAME="$(basename "$EP")"
BUILD="${BUILD:-$HOME/.cache/build/$NAME}"; HF="$BUILD/hf"
STAGES="${*:-pull trim plan score assets build facts check textqa render encode qa}"
STAGES=" ${STAGES//lint/check} "
FPS="${FPS:-30}"; CRF="${CRF:-18}"; WORKERS="${WORKERS:-auto}"
export HYPERFRAMES_NO_TELEMETRY=1 HYPERFRAMES_NO_UPDATE_CHECK=1 DO_NOT_TRACK=1 HYPERFRAMES_SKIP_SKILLS=1
export PATH="$HOME/.cache/bin:$HOME/.cache/node/bin:$HOME/.cache/npm-global/bin:/usr/local/bin:$PATH"
mkdir -p "$BUILD" "$HOME/.cache/tmp/hftmp"; export TMPDIR="$HOME/.cache/tmp/hftmp"
log() { printf '\n== [%s] %s\n' "$NAME" "$*"; }
has() { [[ " $STAGES " == *" $1 "* ]]; }

has pull   && { log "pull media (release assets -> $EP)"; python3 "$REPO/reelkit/media.py" pull "$EP"; }
has trim   && { log "trim VO"; python3 "$REPO/reelkit/trim_vo.py" "$EP/vo" "$BUILD" --check "$EP/words.json"; }
has plan   && { log "timeline"; python3 "$EP/plan.py" >/dev/null; }
has score  && { log "score + SFX + mix (-14 LUFS)"; python3 "$EP/score.py" "$BUILD" "$BUILD"; mkdir -p "$EP/out"; cp "$BUILD/mix_report.json" "$EP/out/" 2>/dev/null || true; }
has assets && { log "visual assets"; python3 "$EP/make_assets.py" "$HF"; [ -f "$EP/clips.json" ] && python3 "$REPO/reelkit/clips.py" prep "$EP" "$HF" || true; }
has build  && { log "composition"; python3 "$EP/build.py" "$HF"; cp "$BUILD/mix.wav" "$HF/assets/mix.wav"; }
has facts  && { log "fact gate (claims ledger ↔ narration + on-screen text, guardrails)"; mkdir -p "$EP/out"; python3 "$REPO/reelkit/factcheck.py" "$EP" --hf "$HF" --report "$EP/out/factcheck.json" --sources-md "$EP/out/sources.md"; }
has check  && { log "composition check (lint + runtime + layout collisions)"; mkdir -p "$EP/out"; python3 "$REPO/reelkit/hfcheck.py" "$HF" --report "$EP/out/check.json"; }
has textqa && { log "readability gate (every on-screen text ≥ 3:1, target 4.5:1)"; mkdir -p "$EP/out"; python3 "$REPO/reelkit/textqa.py" "$HF" --report "$EP/out/textqa.json" --sheet "$BUILD/textqa_fails.jpg"; }
has snap   && { log "snapshots"; (cd "$HF" && hyperframes snapshot --at "${SNAP_AT:-1,20,47,71,86}" --no-end --timeout 30000 -o "$BUILD/snaps" >/dev/null 2>&1); ls "$BUILD/snaps"; }
has render && { log "render ${FPS}fps crf $CRF workers $WORKERS"; (cd "$HF" && hyperframes render -f "$FPS" -w "$WORKERS" --crf "$CRF" -o "$BUILD/render.mp4" 2>&1 | grep -vE "@hf-progress|Render:trace|^\s+█" | tail -12); }
has encode && { log "upload master (H.264 High 4.2, CRF 18 capped 12 Mbps, AAC 256k, faststart)"; mkdir -p "$EP/out"
  # Platforms re-encode everything; feeding them < 5 Mbps makes grain/light-leaks block up. 10-12 Mbps is the sweet spot.
  ffmpeg -hide_banner -loglevel error -y -i "$BUILD/render.mp4" -i "$BUILD/mix.wav" -map 0:v -map 1:a -c:v libx264 -preset "${PRESET:-faster}" \
    -crf "${MASTER_CRF:-18}" -maxrate "${MASTER_MAXRATE:-12M}" -bufsize "${MASTER_BUFSIZE:-24M}" -pix_fmt yuv420p -profile:v high -level 4.2 \
    -r "$FPS" -g "$((FPS * 2))" -bf 2 -threads "${THREADS:-2}" -c:a aac -b:a 256k -ar 48000 -movflags +faststart -shortest "$EP/out/final.mp4"
  ffmpeg -hide_banner -loglevel error -y -ss "${COVER_AT:-1.3}" -i "$BUILD/render.mp4" -frames:v 1 -q:v 2 "$EP/out/cover.jpg"; ls -la "$EP/out"; }
has qa     && { log "QA"; python3 "$REPO/reelkit/qa.py" "$EP/out/final.mp4" --words "$EP/timeline.json" --report "$EP/out/qa.json"; }
log "done → $EP/out"
