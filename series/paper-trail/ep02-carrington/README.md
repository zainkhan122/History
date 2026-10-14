# Paper Trail · File 02: production folder

| | |
|---|---|
| Deliverables | Release `ep02-carrington-v1`: `final.mp4` (1080×1920, 30 fps, 88.5 s) + every gate report, `cover.jpg`, `POST_KIT.md` |
| Inputs (media store) | Release `media-ep02-carrington`: `assets/` (4 collage plates + 3 PD Commons stills), `clips/` (2 Wan + 5 NASA PD), `vo/` (TTS voice-02). Manifest + provenance: `media.json` |
| In git | `research.json` (claims ledger) · `voice.json` (performance plan) · `shots.json` · `clips.json` · `episode.json` (promise) · `decisions.jsonl` · `plan.py` · `score.py` · `make_assets.py` · `build.py` · `words.json` · `timeline.json` · `script.md` · `POST_KIT.md` |

## Rebuild
```bash
python3 reelkit/cloud.py render series/paper-trail/ep02-carrington --tag ep02-carrington-v1 --wait   # the way to render (GitHub Actions)
bash reelkit/episode.sh series/paper-trail/ep02-carrington plan assets build facts provenance planlint check   # light local gates only
```
Heavy stages (clip prep, render, encode) run on GitHub Actions — see the Operator model in `AGENTS.md`.
