# History · Shorts studio (SSOT)

Faceless, deeply researched micro-history Shorts: the **Paper Trail** series and more.

| | |
|---|---|
| Format | 9:16 · 1080×1920 · 30 fps · −14 LUFS |
| Editor | HyperFrames (HTML + GSAP), rendered with chrome-headless-shell |
| Music | Original, procedural (numpy) |
| Cloud | Renders run on GitHub Actions; outputs go to GitHub **Releases**, so git stays small |

## Quick start
```bash
source bootstrap.sh                                         # toolchain + resume pack
bash reelkit/episode.sh series/paper-trail/ep01-petrov      # full local pipeline (~10 min on 2 vCPU)
python3 reelkit/cloud.py render series/paper-trail/ep01-petrov --wait --download ~/.cache/dl   # cloud render
bash tools/sync.sh "message"                                # push media + code (do this after every change)
```

## Pipeline
`media pull → trim VO → plan (timeline from word timings) → score (music + SFX + mix) → assets → build (HyperFrames
composition) → lint → render → delivery encode → QA gate (spec, loudness, freezes, ASR intelligibility) → Release`

## Episodes
| Episode | Status | Release |
|---|---|---|
| Paper Trail 01: *The Man Who Did Nothing* (Petrov, 1983) | v2.2 delivered | `ep01-petrov-v2.2` |
| Paper Trail 02: *The Day the Sky Ran the Telegraph* (Carrington Event, 1859) | in production | `ep02-carrington-v1` (planned) |

Agents: start at **[AGENTS.md](AGENTS.md)**, then **[RESUME.md](RESUME.md)**.
