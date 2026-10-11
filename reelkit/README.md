# reelkit: an in-agent viral reel engine (v2, CPU-only toolkit)

Every session starts with **`source ~/reelkit/setup.sh`**. It is idempotent: it takes about 20 s when everything is already cached and about 2 min from scratch.
Binaries and models live in `~/.cache`, which is not saved with the workspace, so the workspace stays small. Reel folders hold only the source assets and `final.mp4`; intermediate files go to `~/.cache/tmp/<reel>/`. Note that `/tmp` is RAM-backed here, so don't render into it.

## Tools

| Tool | File | Open-source engine (license) | What it adds to a reel | Measured speed on this 2 vCPU / 2 GB machine |
|---|---|---|---|---|
| Research | `~/.cache/bin/lightpanda` | Lightpanda (AGPL-3.0) | Scrapes facts and trends into `reel.json` | about 0.2–0.4 s per page |
| Voice-over (free, offline) | `tts_kokoro.py` | Kokoro-82M ONNX int8 (Apache-2.0) | Unlimited English VO; 54 voices; blends such as `af_heart:60,am_adam:40` | 33 s of VO in about 100 s |
| Word timing | `script.py align` | faster-whisper (MIT) | Word-anchored cuts and karaoke captions | about real time |
| Cutouts | `cutout.py` | rembg + isnet-general-use (MIT/Apache) | Collage stickers with a scissor-cut paper border and shadow | about 8 s per image |
| Stickers / Lottie | `render.py` events | rlottie (MIT) | Pieces pop, drop, slide or spin in on a word; vector bursts | included in render time |
| Talking characters | `lipsync.py` + `mouth` event | Rhubarb Lip Sync (MIT) | Mouth sprites follow the VO; the mouth tracks the camera | about 10 s per beat |
| Fix garbled AI text | `inpaint.py` | LaMa ONNX (Apache-2.0) | Erases the text, then re-typesets the headline (`--text`) | about 20 s per region |
| Beat sync | `beats.py` | librosa (ISC) | Slides licensed music so cuts land on beats; `--autopad` | about 5 s per track |
| Silence and filler cutting | `auto-editor` CLI | auto-editor (Unlicense) | Tightens talking-head or podcast audio and video | faster than real time |
| Render | `render.py` | Pillow + ffmpeg | Camera moves, punch, shake, flash, confetti, whip cuts, grain, karaoke (`rtl` for Urdu) | about 4× real time |
| Mix | `audio.py` | numpy + ffmpeg | Procedural bed or real `music`, SFX, ducking, −14 LUFS | about 10 s |

## Pipeline (one reel folder)

```bash
source ~/reelkit/setup.sh
cd ~/viral_playbook/inputs/02_toebes_dementia
# 1. keyframes:   generate_image for each prompt in reel.json "keyframes"
#    garbled text?   python3 ~/reelkit/inpaint.py keyframes/k1.png --box .08,.04,.92,.22 --text "MOVING IN" --color "#C8553D" -o keyframes/k1.png
# 2. VO:  English  -> python3 ~/reelkit/tts_kokoro.py reel.json          (free, unlimited)
#         Urdu/other-> python3 ~/reelkit/script.py tts reel.json  then generate_speech per beat -> vo/bN.wav
python3 ~/reelkit/script.py align reel.json        # Whisper word times -> words.json
# 3. optional layers
python3 ~/reelkit/cutout.py keyframes/k3.png --crop .1,.4,.9,.95 -o cutouts/hero.png
python3 ~/reelkit/lipsync.py reel.json --make-sprites mouths/
python3 ~/reelkit/render.py reel.json              # -> timeline.json (+ video in ~/.cache/tmp)
# 4. optional real music (licensed!) — snap cuts to beats, re-render once
python3 ~/reelkit/beats.py snap reel.json music/track.mp3 --autopad && python3 ~/reelkit/render.py reel.json
python3 ~/reelkit/audio.py reel.json               # -> final.mp4 (-14 LUFS, 12 Mbps cap)
```

## New `reel.json` event types

```json
{"at": "b2:student", "type": "sticker", "img": "cutouts/lander.png", "pos": [0.78, 0.33], "w": 0.36,
 "anim": "drop", "rot": -6, "until": "b3", "boil": true}
{"at": "b1", "type": "mouth", "beats": ["b1", "b2"], "sprites": "mouths/", "pos": [0.5, 0.555], "w": 0.13}
{"at": "b5:people#2", "type": "lottie", "file": "~/reelkit/fx/burst.json", "pos": [0.5, 0.42], "w": 0.9}
```

- **sticker:**
  - `anim` options: `pop | drop | slide_l | slide_r | slide_up | spin`.
  - It stays until the next cut, or until `until`, then shrinks out.
  - `boil` adds an 8 fps stop-motion jitter.
  - `"scene": true` pins it to the keyframe so it moves with the camera.
- **mouth:**
  - Requires `mouths.json` from `lipsync.py`.
  - `pos` and `w` are in keyframe coordinates, so the mouth follows push-ins, pans and shake.
  - It shows the rest shape `X` when the character isn't speaking.
- **lottie:** any Lottie JSON or `.tgs` file. It plays once, or set `"loop": true` and `"speed"`.

Top-level spec key: `"music": {"file": "music/x.mp3", "offset": 7.19, "gain": 0.9}`. `beats.py` writes this; without it, `audio.py` uses the procedural bed.

## Limits

- **Kokoro has no Urdu.** Its Hindi voices read Devanagari only. For Urdu reels, keep using `generate_speech`.
- **Cutouts:** a busy full-scene collage counts as "all foreground", so always `--crop` to one object first. Better still, generate pieces on a flat background. The `u2net` model breaks collage objects into fragments, so `isnet` is the default.
- **LaMa** is excellent on flat or paper backgrounds but blurs large busy regions (>40% of the frame); regenerate those instead.
- **Rhubarb mouth sprites** are the stylised paper-cut look, not photoreal lip-sync. Photoreal needs a GPU (MuseTalk or LatentSync).
- **Beat sync:**
  - It slides the music and adds pauses of ≤0.35 s; it never time-stretches speech.
  - Cuts inside a beat (multi-shot beats) are not forced onto the grid.
- **auto-editor:**
  - It downloads its own binary on first run (stored in `~/.local`, not persisted).
  - Always pass `--no-open`.
- **Music:** it must be licensed. Use the YouTube Audio Library, Pixabay Music, or your own ACE-Step output on a GPU box.
- **Not here:** these need a GPU or more than 2 GB of RAM: Wan 2.2 image-to-video, ACE-Step music, Chatterbox voice cloning, LivePortrait, Real-ESRGAN, BiRefNet at full resolution.

## v2.1 additions (Paper Trail ep01)
- `synth.py`: seeded, royalty-free music and SFX primitives (pads, drones, piano, bells, boom/hit, stamp, typewriter, whoosh, riser, siren, heartbeat, paper, reverb, sidechain follower). See `~/paper_trail/ep01_petrov/score.py` for a full arrangement.
- `setup.sh` step 8 now also installs the chrome-headless-shell system libraries plus ffprobe through passwordless sudo, and sets TMPDIR to disk. `/tmp` is a ~1 GB RAM disk, too small for renders.
- HyperFrames render on 2 vCPU / 2 GB: 87 s of 1080×1920 at 30 fps renders in ~10 min (`-w 2`, low-memory screenshot mode). The CRF 18 master is ~370 MB. Re-encode for delivery at ~3.6 Mbps, which gives ~42 MB.
