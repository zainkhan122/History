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

## Hard rules
- **No media in git.** Images, audio and video go to Release assets via `reelkit/media.py`. git holds only `media.json` manifests.
  `tools/repo_guard.py` enforces this: no media extensions, no file > 1 MB, total < 15 MB.
- **Builds run in `~/.cache/build/`**, never inside the repo.
- **Workspace budget:** the Arena save limit is ~128 MB / 10k files. Keep only `~/History` in the workspace. Caches and models go in `~/.cache`.
- **Renders:** short drafts or snapshots run locally. Full renders run in the cloud: `python3 reelkit/cloud.py render <episode_dir> --wait`.
- **Lightpanda can't render frames.** Tested 2026-10-11: `--dump png` is text-only, with no CSS, images or SVG. It's used for fast research scraping only. Frame capture uses chrome-headless-shell (via HyperFrames).
- **Quality gates** (all in `episode.sh`; a FAIL blocks the render):
  - `facts` → `reelkit/factcheck.py`: every narrated sentence with a number/date/name/quote, and every on-screen label, must map to a claim in the episode's `research.json`. Evidence tiers: core ≥2 publishers incl. ≥1 primary/scholarly; record ≥2 incl. a fact-checked reference; detail ≥2; framing ≥1; quotes trace to their first publication. Guardrail phrases are checked in VO, on screen and in `POST_KIT.md`. Also writes `out/sources.md` (paste-ready description citations). `--online --archive` checks links and stores Wayback snapshots in the ledger.
  - `check` → `reelkit/hfcheck.py`: `hyperframes check` (lint + runtime + layout collisions, sampled at transitions) + the caption-zone audit. Intentional overlaps need explicit `data-layout-allow-*` on the text element itself (not inherited).
  - `textqa` → `reelkit/textqa.py`: contrast ≥3:1 (target 4.5), platform UI dead zones (top 230 / bottom 320 / right 120 px), reading time.
  - `qa` → `reelkit/qa.py`: loudness −14 LUFS, true peak ≤ −1.5 dBTP, bitrate ≥ 8 Mbps, no silence gaps.
  - Owner rule: free-floating white text over imagery is poor editing and loses viewers. See `series/paper-trail/SERIES.md`.
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
