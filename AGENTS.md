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
- **Readability:** every on-screen text must pass `reelkit/textqa.py`, which runs in `episode.sh`. FAIL (< 3:1) blocks the render. Owner rule: free-floating white text over imagery is poor editing and loses viewers. See `series/paper-trail/SERIES.md`.
- **Accuracy:** every narrated fact needs 2 independent sources in the episode's `script.md` fact sheet (protocol in `docs/CONTENT_STRATEGY.md` §3). Follow the guardrails listed there.
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
