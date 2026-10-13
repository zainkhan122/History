# RESUME: living handoff (update before every sync)

_Last updated: 2026-10-13 PKT by the Arena agent. Short form: `python3 tools/state.py show`._

## Where we are
- **2026-10-13: implementing OpenMontage P0 + P1 in phases** (owner request; progress table in `docs/OPENMONTAGE_LESSONS.md` §D).
  - Phase 1 delivery gates ✅ · Phase 2 claims ledger + `factcheck.py` ✅ · Phase 3 voice plan + `voice.py` gate ✅ (ep01 climax pause shaped 0.37→0.6 s; media pushed) · next: **Phase 4** planlint (+cross-episode), promise lock + decisions.jsonl, provenance; then P5 (clip cache, Wan template); then cloud render `ep01-petrov-v2.2` (87.6 s).
  - All gates for ep01 currently pass: voice 0/0, facts 0 FAIL (3 caveat WARNs), hyperframes check 0 errors, textqa 0 FAIL.
- **2026-10-13: OpenMontage study** → `docs/OPENMONTAGE_LESSONS.md`. Self-found issues: upload bitrate 3.8 Mbps (too low, target 12M master), channel bug and caption width inside platform UI dead zones, and `out/` excluded from snapshots (local v2.1 final lost; regenerate via cloud). The owner chooses which items to implement.
- **2026-10-11 (later): v2.1 readability pass.** Owner: "text must be readable wherever it appears". Fixes:
  - kicker on a paper strip; stronger scrims on the quote, "Nothing" and "survived by" lines;
  - readable reds (`#A50B25` on paper, `#FF4D4D` on dark); dark CRT backing behind СТАРТ;
  - paper label on the memorial credit; larger film credit.
  - **New gate `reelkit/textqa.py`** (stage `textqa` in episode.sh): result 132 text units, 0 FAIL.
  - Strategy answers are in `docs/CONTENT_STRATEGY.md`.
  - **If local commits are not on origin, push first:** `bash tools/sync.sh`. The token was lost in a sandbox restart.
- **Repo SSOT live:** `zainkhan122/History` (public). Code and docs are in git (~1.8 MB). Media is in **Releases**:
  - `media-ep01-petrov`: plates, VO, raw clips (24 files, 11.8 MB, manifest `series/paper-trail/ep01-petrov/media.json`);
  - `media-reel-hamilton`: Hamilton proof reel (15 files, 64.8 MB);
  - `archive-research`: research scrapes tarball;
  - `ep01-petrov-v1`: delivered v1 (final.mp4, cover, POST_KIT, qa.json);
  - `ep01-petrov-cloud-test`: cloud render proof. Run #1: 10 min, QA pass, identical to local.
  - `ep01-petrov-v2`: **v2 delivered** (cloud run #2: QA pass, −14.08 LUFS, ASR 0.963).
- **Ep01 v2 engine upgrade (done, in git):**
  - Wan 2.2 motion clips on s03 (console) and s07 (sunlight / satellite);
  - archival **Minuteman launch film insert** on "strike back" (projected frame, gate weave, flicker, label, credit, projector SFX, flash in, film burn out);
  - organic light leaks on the sunlight reveal, the wife memory and "survived by".
- **Pending clips** (HF ZeroGPU anonymous quota hit after 3 clips): s01_bunker, s05_officer, s06_phone, s09_kitchen.
  Prompts are ready in `clips.json`. Run `python3 reelkit/clips.py gen series/paper-trail/ep01-petrov` with `HF_TOKEN` set, then `media.py push` and a cloud render → v3.
- **Lightpanda vs Chrome:** tested, and Lightpanda can't paint (`--dump png` is text-only). Chrome-headless-shell stays for frames; Lightpanda is for scraping only. Speed comes from cloud rendering.

## Owner rules (standing)
See `STATE.json → owner_rules`:
- the repo is the SSOT and every change is synced;
- keep the workspace and repo lean;
- premium editing with real motion;
- sourced facts;
- emotional TTS;
- no auto-posting yet (Buffer/YT later).

## How to continue (new session)
```bash
mkdir -p ~/.cache/secrets && printf %s "<TOKEN>" > ~/.cache/secrets/gh_token   # owner supplies the token (expires 2026-11-10)
[ -d ~/History ] || git clone https://github.com/zainkhan122/History.git ~/History
source ~/History/bootstrap.sh          # restores .git/config (Arena drops it), toolchain, prints resume pack
python3 reelkit/cloud.py status        # last cloud renders
python3 reelkit/media.py pull series/paper-trail/ep01-petrov   # only if you need the media locally
```

## Next
1. Owner review of v2 (delivered 2026-10-11).
2. Get a free HF token from the owner → generate the 4 pending clips → render v3 in the cloud.
3. Ep02 (Paper Trail): subject from `docs/NICHE_RESEARCH.md`. Build `clips.json` from day one:
   - 4–6 Wan clips;
   - 1–2 archive inserts (Commons / IA / NASA PD).
4. Optional: CPU depth-parallax fallback (Depth-Anything ONNX) for when the GPU quota is out.
5. Later (owner asked to wait): Buffer / YouTube auto-publish from the render workflow.

## Known gotchas
- Workspace snapshots EXCLUDE dirs named `out`, `build`, `dist`, etc. Episode `out/` is scratch, and finals live only in Releases.
- **Arena snapshots drop `.git/config`.** `bootstrap.sh` restores the remote, identity and auth; the slug lives in `.repo`.
- `/tmp` is a ~1 GB RAM disk. Builds go to `~/.cache/build`; `episode.sh` sets TMPDIR on disk.
- Sandbox restarts wipe `~/.cache` and pip user packages. Re-run `source bootstrap.sh`.
- The static ffmpeg in `~/.cache/bin` segfaults on HTTPS input. `clips.py` uses `/usr/bin/ffmpeg` and downloads first.
- HyperFrames:
  - `<video data-start>` must NOT be inside a timed div. `engine/fx.py` puts videos at root level under their scene and drives Ken Burns and shakes through `kb_targets` / `shake_targets`.
  - `immediateRender:false` on every fromTo.
  - Elements that start hidden need autoAlpha in the destination.
  - Don't let two tweens animate the same property of one element at the same time.
- read_file sometimes misses a just-written image; retry once.
- The fine-grained token expires **2026-11-10**.
