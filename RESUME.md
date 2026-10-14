# RESUME: living handoff (update before every sync)

_Last updated: 2026-10-14 (later) PKT by the Arena agent. Short form: `python3 tools/state.py show`._

## Where we are
- **2026-10-14 (later): robustness pass** (owner: "anything else to fix… rendering on GitHub, media finding?"; mp4 named after the story).
  - Audit fixes: R1 dispatch pinned to HEAD sha (race of run #8 impossible) · R2 `episode.sh <ep> preflight` (textqa `--layout-only` locally,
    ~1 min, catches what stopped runs #6/#7) · R3 failure summary in the Actions page + `cloud.py why` · R4 API retries, `.part` replace-safe
    uploads, auth stripped on cross-host redirects (job logs) · R5 ci_setup retries + fail-fast tool checks · R6 story-named assets
    (both releases renamed) · R8 token-expiry warning · sandbox never decodes archival sources (deferred to CI).
  - Generators: Upsampler = HF Spaces → engines `wan14`, `ltx25` + per-clip `fallback`; browser-only tools (Creen, Media.io,
    Video-Generator.ai, Veo) manual only. Capacity lever: free HF token. No new clip was generated (none needed).
  - Validated end-to-end: cloud run #10 @ecdda6d (pinned while 6978828 was pushed mid-run) re-rendered File 02 identically and
    replaced the story-named assets in place; POST_KIT/README names fixed; check.yml now rejects `final.mp4`/`cover.jpg` in kits.
  - Media finding: `reelkit/find.py` (Commons/NASA/IA, licence-mapped to provenance, `add` → lint-clean url clip).
- **2026-10-14: File 02 "The Day the Sky Ran the Telegraph" (Carrington Event 1859), first episode built fully on the new system.**
  - Files: `series/paper-trail/ep02-carrington/` (research ledger 15 claims / 11 sources; voice plan + sample gate; shots.json fingerprint
    rotated vs ep01; promise motion_led 0.55; 2 Wan clips + 5 NASA PD archival clips (url clips trimmed in CI); 3 PD stills credited on screen).
  - **Delivered:** release `ep02-carrington-v1` (cloud run #9 @4e7eb35, 13 min): facts 0 FAIL, voice 0/0, provenance 0/0, planlint 0/0
    (motion 58 % vs 55 %), hyperframes check 0 errors, textqa 0 FAIL, QA pass (−14.1 LUFS, TP −1.81, 11.7 Mbps, ASR 0.99, no freezes/black/silence).
  - Runs #6–#7 were stopped by textqa dead-zone FAILs (fixed); #8 rendered the previous commit (dispatched in parallel with the push: see AGENTS.md).
  - Media: release `media-ep02-carrington` (25 files). Next: owner review; then Ep03.
  - Tooling learned on this episode is in `AGENTS.md` → "Voice workflow" steps 5–7 and "Build rules".
- **2026-10-13: implementing OpenMontage P0 + P1 in phases** (owner request; progress table in `docs/OPENMONTAGE_LESSONS.md` §D).
  - Phase 1 delivery gates ✅ · Phase 2 claims ledger + `factcheck.py` ✅ · Phase 3 voice plan + `voice.py` gate ✅ (ep01 climax pause shaped 0.37→0.6 s; media pushed) · Phase 4 planlint + promise lock + decisions.jsonl + provenance ✅ · next: **Phase 5** content-addressed clip cache + Wan 5-slot prompt template; then cloud render `ep01-petrov-v2.2` (87.6 s).
  - All gates for ep01 currently pass: voice 0/0, facts 0 FAIL (3 caveats), provenance 0 FAIL (10 legacy plates), planlint 0 FAIL (motion 20 % under approved exception until 2026-12-31), hyperframes check 0 errors, textqa 0 FAIL.
  - New-episode order: research.json → voice.json (+ sample gate) → shots.json (fingerprint must differ from previous episodes) → clips with recorded prompts → media.json provenance on push.
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
  - `archive-research`: research scrapes tarball;
  - (2026-10-14, owner: old versions deleted — ep01-petrov-v1/-v2/-cloud-test and media-reel-hamilton releases + tags, `archive/reel-hamilton/`; only the latest version of each episode is kept)
  - `ep01-petrov-v2.2`: **v2.2 delivered 2026-10-13** (cloud run #5: QA pass, −14.07 LUFS, TP −1.9, 12.1 Mbps, ASR 0.963) — +s01/s06 Wan clips, motion 40 %.
- **Ep01 v2 engine upgrade (done, in git):**
  - Wan 2.2 motion clips on s03 (console) and s07 (sunlight / satellite);
  - archival **Minuteman launch film insert** on "strike back" (projected frame, gate weave, flicker, label, credit, projector SFX, flash in, film burn out);
  - organic light leaks on the sunlight reveal, the wife memory and "survived by".
- **Clips (Phase 5, 2026-10-13):** s01_bunker + s06_phone generated with the 5-slot template and in the edit (motion 40 %).
  **Pending:** s05_officer, s09_kitchen — composed, linted, keyed. Anonymous ZeroGPU ≈ 240 GPU-s/day (2 runs of 105 s).
  `python3 reelkit/clips.py status series/paper-trail/ep01-petrov` → `clips.py gen …` (cache-first) → review frames →
  `shots.json` motion "clip" → `media.py push` → cloud render. With both: motion ≈ 61 %, the promise exception can retire.
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

## In progress — ep02 `series/paper-trail/ep02-carrington` (File 02, Carrington Event 1859), 2026-10-14
Owner choices: topic carrington · delete old releases but keep `ep01-petrov-v2.2`, `media-ep01-petrov`, `cache-clips` + ep01 source · motion = archival PD + 2 Wan clips.
Done (local, NOT yet committed/pushed — token needed):
- `research.json` 11 sources, 15 claims (C01–C14, Q01), 3 myths ("gold miners" → original says campers), 5 guardrails, landscape.
- `voice.json` 10 lines, plan check 0/0. Narrator = Arena TTS **voice-02** (owner audition; IDs don't survive sessions — re-audition if lost).
  Sample gate on v10: take1 best (wer 0, pauses on target) → `vo/v10.mp3`. Takes v01–v07 + v10 in `vo/`; `words.json` via new `voice.py words`.
- Plates `assets/s01_telegraph s02_sketch s05_campers s06_office.jpg` (collage style). `clips.json`: 2 Wan (s01_telegraph seed 21, s05_campers seed 15, composed, lint 0/0)
  + 4 PD archival trimmed via clip cache (arch_aurora, arch_flare, arch_iss_aurora, arch_cme2012; blobs local, `clipcache.py sync` needs token).
  Black Marble webm downloaded to `~/.cache/tmp/dl` (for s10, not in clips.json yet).
Next:
1. TTS v08, v09 + **retake v06** (pace 4.6 < urgent band 5.0) → `voice.py words --only v06,v08,v09` → `voice.py check` 0 FAIL.
2. `plan.py` (FIX map: whisper writes "11 .18", "60", "17", "5") → set arch_aurora window (gives 3.6 s for 4–9 s; widen) + arch_nightlights clip.
3. Wan clips after quota reset (~14:20 UTC): `clips.py gen <ep> --only s01_telegraph s05_campers`.
4. `build.py`, `score.py`, `make_assets.py`, `shots.json`, `episode.json` (promise lock), `POST_KIT.md` → all gates (planlint cross-episode vs ep01).
5. ✅ deletion plan done 2026-10-14. With token: `media.py push`, `clipcache.py sync`, `cloud.py render ep02 --tag ep02-carrington-v1`.

## Next
1. Owner review of v2.2 (delivered 2026-10-13) + confirm the min_motion exception.
2. Generate s05 + s09 (daily quota reset or owner HF token) → review → shots.json → render v3 in the cloud.
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
- The sandbox has **2 GB RAM**. Encoding a >1440p archival source thrashed the whole machine; `clips.gen_url` now runs ffmpeg under a 1.4 GB RLIMIT_AS (CLIP_MEM_MB) — give 4K sources `"max_h": 1440`.
- Commons API file URLs now carry `?utm_…` params: strip them before putting a URL in clips.json (the cache key hashes the URL).
- upload.wikimedia.org answers bursts with 429; `clips.fetch` backs off (Retry-After) — space out downloads.
- The fine-grained token expires **2026-11-10**.
