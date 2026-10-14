# AGENTS.md — read this first (any AI agent, any session)

This repo is the **single source of truth (SSOT)** for the owner's Shorts studio. The Arena workspace is a
disposable working copy. If it isn't in this repo (git or Release assets), it doesn't exist.

## Session start (empty workspace)
1. Ask the owner for the GitHub token if `~/.cache/secrets/gh_token` is missing. Store it there (chmod 600).
   Never write tokens to the repo, the workspace or logs.
2. `[ -d ~/History ] || git clone https://github.com/zainkhan122/History.git ~/History; source ~/History/bootstrap.sh`. Arena drops `.git/config` from snapshots; bootstrap restores it from `.repo`.
3. Read `RESUME.md` and continue from its **Next** list. `python3 tools/state.py show` gives the short version.

## Session end, or after any meaningful change
`bash tools/sync.sh "what changed"` pushes media to Release assets and code/docs to git.
Update `RESUME.md` (and `STATE.json` via `tools/state.py set`) **before** syncing.

## Operator model (owner, 2026-10-14)
The sandbox is the **operator**; GitHub is the **infrastructure**. The sandbox has 2 GB RAM and is wiped on restart.
| Sandbox (agent) does | GitHub does |
|---|---|
| research, writing, decisions, audits; asks the owner | **repo** = source of truth (code, plans, ledgers, manifests) |
| Arena-only generators: `generate_speech` (VO), `generate_image` (plates), `add_voice` auditions | **Releases** = all media (`media-<ep>`, `cache-clips`, finals) |
| light gates on text/JSON: voice plan + takes, factcheck (timeline), clips lint, planlint/provenance with `--hf /nonexistent` | **Actions** (4 vCPU / 16 GB) = everything heavy: archival downloads + trims (`url` clips are materialised by `clips.py gen --cache-only` in the render job), clip prep, assets, build, hyperframes check, textqa, render, encode, QA |
| orchestration: `media.py push`, `clipcache.py sync`, `cloud.py render/status/fetch` | renders publish a Release with every gate report |
Never decode/encode >1080p video or run a full render in the sandbox. Archival footage is *declared* in `clips.json`
(clean URL, in/out, `max_h` for >1440p sources) and trimmed in the cloud. Local frame checks use ≤720p proxies only.

## Hard rules
- **No media in git.** Images, audio and video go to Release assets via `reelkit/media.py`. git holds only `media.json` manifests.
  `tools/repo_guard.py` enforces this: no media extensions, no file > 1 MB, total < 15 MB.
- **Builds run in `~/.cache/build/`**, never inside the repo.
- **Workspace budget:** the Arena save limit is ~128 MB / 10k files. Keep only `~/History` in the workspace. Caches and models go in `~/.cache`.
- **Renders:** short drafts or snapshots run locally. Full renders run in the cloud: `python3 reelkit/cloud.py render <episode_dir> --wait`.
- **Lightpanda can't render frames.** Tested 2026-10-11: `--dump png` is text-only, with no CSS, images or SVG. It's used for fast research scraping only. Frame capture uses chrome-headless-shell (via HyperFrames).
- **Quality gates** (all in `episode.sh`; a FAIL blocks the render):
  - `facts` → `reelkit/factcheck.py`: every narrated sentence with a number/date/name/quote, and every on-screen label, must map to a claim in the episode's `research.json`. Evidence tiers: core ≥2 publishers incl. ≥1 primary/scholarly; record ≥2 incl. a fact-checked reference; detail ≥2; framing ≥1; quotes trace to their first publication. Guardrail phrases are checked in VO, on screen and in `POST_KIT.md`. Also writes `out/sources.md` (paste-ready description citations). `--online --archive` checks links and stores Wayback snapshots in the ledger.
  - `voice` → `reelkit/voice.py check`: every take measured against the performance plan `voice.json`. It checks fidelity (skipped words, wrong numbers), pace per tone band (syllables per second of phonation), marked pauses as real waveform silences, pitch range and clipping. `plan.py` takes its pauses from the plan.
  - `provenance` → `reelkit/provenance.py`: every file the build ships traces to a `media.json` entry with kind, licence (allow-list; SA/NC/ND/unknown are refused), provider, source and credit. AI media carries a prompt/spec and a realistic flag. Photo and archive credits must be visible on screen and in `POST_KIT.md`. Writes `out/credits.md`.
  - `planlint` → `reelkit/planlint.py`: checks `shots.json` (subject, shot size, motion, information role, reason) against reality:
    - the motion promise in `episode.json`, measured;
    - a declared clip shown as a still is a silent fallback and FAILs without an approved `clip_fallback` decision;
    - static holds measured from the build, limited by each scene's tone;
    - slideshow risk;
    - cross-episode fingerprint drift. The format, hook and opening must rotate.
  - `clips` (inside planlint, also `reelkit/clips.py lint`): pending Wan clips use the 5-slot `shot` template in `clips.json`
    (subject · ordered motion steps · scene · spatial · ONE camera move; series style lock + avoid-list in `template`), 200–400
    words, positive phrasing, no on-screen-text words; `prompt` is written by `clips.py compose` — never by hand. Clips without
    `shot` are frozen legacy (their prompt is part of their cache key).
  - **Generation goes through the cache only:** `clips.py status <ep>` → `clips.py gen <ep>` (local → release `cache-clips` → GPU).
    Every call pins a seed; a clip is generated once, ever. Review frames before putting a new clip in `shots.json`.
  - **Exceptions live in `decisions.jsonl`** (`reelkit/decide.py add …`): append-only, with an approver and an expiry. Never edit old lines; supersede them.
  - `check` → `reelkit/hfcheck.py`: `hyperframes check` (lint + runtime + layout collisions, sampled at transitions) + the caption-zone audit. Intentional overlaps need explicit `data-layout-allow-*` on the text element itself (not inherited).
  - `textqa` → `reelkit/textqa.py`: contrast ≥3:1 (target 4.5), platform UI dead zones (top 230 / bottom 320 / right 120 px), reading time.
  - `qa` → `reelkit/qa.py`: loudness −14 LUFS, true peak ≤ −1.5 dBTP, bitrate ≥ 8 Mbps, no silence gaps.
  - Owner rule: free-floating white text over imagery is poor editing and loses viewers. See `series/paper-trail/SERIES.md`.
- **Voice workflow (new episodes):**
  1. `research.json` first.
  2. `voice.json`: per-line tone, energy, direction and pauses. Mark one `climax` and one `sample_line`.
  3. `voice.py lines <ep>` prints the TTS lines with the sample line first.
  4. Generate 2–3 takes of the sample line, then run `voice.py sample <ep> --take …`. Only produce the other lines once a take PASSes.
  5. Produce the rest, then `voice.py words <ep>` (faster-whisper base.en → `words.json`), then `plan.py`, then `voice.py check`.
     The fidelity check re-hears any mismatch with a second-opinion ASR (`VOICE_ASR2`, default small.en) before it FAILs: base.en
     mishears reduced function words ("as" → "is"). A word wrong in both models is a real misread → regenerate the take.
  6. **The script owns the words, ASR owns the timing.** `plan.py` builds captions with `voice.script_words(text, asr_words)`:
     script words take ASR timings (difflib alignment: 1:1 keeps timing, n:m spreads it), so "60"/"sixty" or "11 .18"/"11:18"
     never reach the screen as ASR spellings.
  7. If a marked pause is short, run `voice.py shape <ep>`. It extends only the take's own silence and keeps the original in `vo/orig/`.
     A small pace fix (`atempo` ≤ 1.05) is allowed: keep the original in `vo/orig/`, log it in `decisions.jsonl` and `media.json` `op`. Then push the media.
- **Build rules (learned on File 02):**
  - Every on-screen text element carries a text-unit class (the series set, or the generic `tu`). factcheck FAILs on visible text
    outside a unit (it would otherwise escape the ledger); textqa uses the same unit list.
  - Archival `url` clips: framed with `FX.film_insert(..., dy=)` (lift the frame so its credit clears the caption band y 1340–1540)
    or full-bleed / boxed with `FX.footage(kbid, cid, t0, t1, box=None)` (root-level timed video, same mechanism as AI plates).
    `fit`/`dur` are prep-only (not in the cache key); `in`/`out`/`max_h`/`url` are the key.
  - Procedural graphics in `shots.json` use `build:<id>` as their source (no media file); clip/film motion still needs a real `clips/` file.
  - `clips.py gen` re-validates existing files against `media.json` `cache_key`: a stale url clip is re-trimmed, a stale AI clip FAILs unless cached.
  - Never fade/hide a clip element itself with GSAP (`gsap_animates_clip_element`): wrap its content in a child div.
  - `textqa` runs only in the render job (it sweeps every 0.5 s). It measures the worst-case box over an element's whole dwell,
    including pop-in offsets: keep ≥ 15 px clearance from the dead zones (bottom UI y ≥ 1600, right column x > 960 below y 640).
  - **Dispatch a cloud render only after the commit + push call has returned** (never in parallel with it): `cloud.py` renders
    the HEAD it reads at start (File 02 run #8 rendered the previous commit this way).
- **Accuracy:** no fact goes in a script before it is in `research.json` with sources (protocol in `docs/CONTENT_STRATEGY.md` §3). Record conflicts between sources as a `caveat` instead of picking silently.
- **Licensing:** commercial-safe assets only (PD / CC0 / CC BY with credit / own-generated). Avoid CC BY-SA for monetised video. Credit everything in `POST_KIT.md`.
- Auto-posting (Buffer / YouTube API) is **not wanted yet**. Do not build or trigger it until the owner asks.

## Map
| Path | What |
|---|---|
| `RESUME.md` | Living handoff: current state, owner rules, next steps |
| `STATE.json` | Machine-readable state (`tools/state.py`) |
| `reelkit/` | Toolkit: setup, TTS, synth score/SFX, trim, media store, cloud driver, QA, episode pipeline |
| `engine/` | Shared composition assets (vendored GSAP) |
| `series/<series>/<episode>/` | One episode: script + fact sheet, plan/score/assets/build code, words/timeline, `media.json`, `POST_KIT.md` |
| `docs/` | Playbook, niche research, video-sources study, references |
| `archive/` | Earlier proofs (code only; media in releases) |
| `.github/workflows/` | `render.yml` (cloud render → Release) · `check.yml` (hygiene) |
