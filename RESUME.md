# RESUME: living handoff (update before every sync)

_Last updated: 2026-10-11 by the Arena agent._

## Where we are
- **Repo SSOT live:** `zainkhan122/History`, public. Code and docs are in git; media is in Releases (`media-*` = inputs, `<episode>-v*` / `-r<run>` = deliverables).
- **Paper Trail ep01 v1 delivered.** "The Man Who Did Nothing" (Petrov), 87.4 s, QA passed: −14.1 LUFS, TP −1.3, ASR 0.963. Files are in Release `ep01-petrov-v1`.
- **Cloud render:** `.github/workflows/render.yml` runs `reelkit/episode.sh` on a 4 vCPU / 16 GB runner and publishes to a Release.
- **Lightpanda vs Chrome:** owner asked to replace Chrome with Lightpanda for efficiency. Tested on nightly 1.1.0-nightly.10426: `fetch --dump png` renders text only (no CSS boxes, transforms, SVG or images), so it **cannot capture video frames**. Decision: Lightpanda for research scraping; chrome-headless-shell (HyperFrames) for frames. Efficiency comes from rendering in the cloud instead.

## Owner rules (standing)
See `STATE.json → owner_rules`. Key ones:
- the repo is the SSOT, and every change is synced;
- keep the workspace and repo lean;
- premium editing with real motion;
- sourced facts;
- emotional TTS;
- no auto-posting yet.

## How to continue
```bash
source ~/History/bootstrap.sh                 # toolchain + resume pack
python3 reelkit/cloud.py status               # last cloud renders
```

## Next
1. Verify a cloud render of ep01 end-to-end (Actions → Release).
2. `docs/VIDEO_SOURCES.md`: free image/video generators, tested.
3. Engine: video-clip layers + professional transitions (`reelkit/clips.py`).
4. Ep01 v2 with motion clips → cloud render → owner review.

## Known gotchas
- `/tmp` is a ~1 GB RAM disk. Builds go to `~/.cache/build`; renders need TMPDIR on disk (`episode.sh` sets it).
- Sandbox restarts wipe `~/.cache` and pip user packages. Re-run `source bootstrap.sh`.
- 2 vCPU / 2 GB sandbox: HyperFrames uses the low-memory screenshot mode (~10 min for 87 s). The cloud runner is much faster.
- HyperFrames: `immediateRender:false` on every fromTo; an element starting hidden needs `autoAlpha:1` in its destination; give initial CSS opacity for wash layers; don't tween the same props on one element from two tweens (shake the parent instead).
- GSAP 3: no `className` tweens; use `attr:{class:..}` in `tl.set`.
- Fine-grained token expires **2026-11-10**.
