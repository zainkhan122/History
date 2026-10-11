# Paper Trail · File 01: production folder

| | |
|---|---|
| Deliverables | Release `ep01-petrov-v1`: `final.mp4` (1080×1920, 30 fps, 87.4 s, −14 LUFS), `cover.jpg`, `POST_KIT.md` |
| Inputs (media store) | Release `media-ep01-petrov`: `assets/` (10 collage plates + PD memorial photo), `vo/` (TTS voice-01). Manifest: `media.json` |
| In git | `script.md` (script, fact sheet, guardrails) · `plan.py` · `score.py` · `make_assets.py` · `build.py` · `words.json` · `timeline.json` · `POST_KIT.md` |

## Rebuild
```bash
bash reelkit/episode.sh series/paper-trail/ep01-petrov                 # local, all stages
bash reelkit/episode.sh series/paper-trail/ep01-petrov build lint snap  # just iterate on the edit
python3 reelkit/cloud.py render series/paper-trail/ep01-petrov --wait   # cloud
```
