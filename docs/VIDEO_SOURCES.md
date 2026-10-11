# Free video/image sources: hands-on test (2026-10-11)

Goal: real motion in every Short, not stills with light animation. Every source below was **actually called from the
agent sandbox**. Tool: `reelkit/clips.py` (gen / prep / one).

## Verdict
| Rank | Source | What it gives | Result in our test | Use for |
|---|---|---|---|---|
| ★1 | **Wan 2.2 14B i2v** · HF Space `zerogpu-aoti/wan2-2-fp8da-aoti-faster` (Apache-2.0 model) | Image-to-video, ≤5 s, 480×832 @ 16 fps | **~40 s per clip, no key. Keeps our collage art style exactly** (s03 screen lights up; s07 satellite drifts and glare blooms). | Animating our own plates; the main motion source |
| ★2 | **Public-domain archive footage**: Wikimedia Commons API, Internet Archive (DoD DIMOC / NARA, CC0), NASA Images API | Real historical film | Instant, no key. 1,839 CC0/PD Cold-War films on IA; 380 missile videos on Commons; 1024×576 Minuteman launch used in ep01 v2 | "Proof" inserts that make it feel researched: projected film frame + on-screen label + credit |
| 3 | **LTX-Video distilled** · HF Space `Lightricks/ltx-video-distilled` | i2v up to 704×1216 @ 30 fps, ≤8 s | ~20 s/clip, sharper, **but drifted the collage into a photoreal window** | Photoreal series or b-roll from photos; stylised art only with very literal prompts |
| 4 | **Pollinations** `image.pollinations.ai/prompt/...` | Flux images, no key | 3 s/image, but anonymous output is capped at **580×1015** | Quick mood/thumbnail drafts. Video needs paid "Pollen" credits |
| — | Cloudflare Workers AI | FLUX.1-schnell images, 10k neurons/day free | Not tested (needs account ID + token); no video | Bulk image plates if the owner adds a token |
| — | Kling / Hailuo / Vidu / Wan web apps | Daily free credits | Web UI only (no API, watermarks on free tiers) | Manual hero shots only |
| ✗ | `Wan-AI/Wan2.2-5B` Space | — | 401 (gone) | — |
| ✗ | `Lightricks/LTX-2` Space | — | RUNTIME_ERROR | — |

## The quota (main constraint)
ZeroGPU Spaces share one per-user GPU quota:
- **Anonymous:** exhausted after 3 clips (2 Wan + 1 LTX).
- **Free HF account token** (`HF_TOKEN`): more daily GPU time, roughly 5–6 Wan clips/day.
- **HF PRO** ($9/mo): ~8× more.

Plan per episode: 4–6 AI clips plus 1–2 archive inserts. Keep the quota for hero shots (hook, turn, ending).
Clips are generated once, stored in the media release, and reused by every render (local or cloud).

## Pipeline (engine)
1. `clips.json` per episode lists AI clips (`engine: wan|ltx`, plate, prompt, scene) and archive clips (`engine: url`, in/out, credit).
2. `clips.py gen <ep>` writes raw clips to `<ep>/clips/`. `media.py push` uploads them; manifests stay in git.
3. `clips.py prep <ep> <hf>` (runs in `episode.sh assets`) does:
   - slow-mo to the scene length (≤ 1.8×);
   - **motion-compensated interpolation** to 30 fps (`minterpolate mci`);
   - Lanczos upscale to the 1296×2322 plate, then unsharp;
   - optional grade: `film` = mono, lifted blacks, paper tint, moving grain, vignette (+ per-clip `eq`).
4. `engine/fx.py`:
   - Video layers sit at root level directly under their scene (HyperFrames forbids `<video>` inside timed divs). Ken Burns and shakes drive the plate and its video together.
   - `film_insert()` adds a projected archive frame with gate weave, flicker, sprockets, typed label and credit.
   - Also: `light_leak()`, `flash()`, `film_burn()`.
   - `synth.projector()` adds matching 24 fps clatter.

## Prompt rules that worked (Wan i2v)
- Describe **motion only**, with camera language: "slow cinematic push-in", "static camera".
- Always end with "illustrated paper collage style preserved, no new objects/people".
- Name the light source that changes ("red screen flashes brighter", "golden glare grows").
- Avoid asking for hands or faces to perform actions, which drift. Add "no hands" on object shots.
- Fix seeds in clips.json for reproducibility.

## HyperFrames registry transitions available (`hyperframes catalog --tag transition`)
- **Shader:** whip-pan, light-leak, cinematic-zoom, flash-through-white, glitch, ridged-burn, domain-warp-dissolve, sdf-iris.
- **CSS:** halftone-dissolve, organic-light-leak-overlay, editorial-flash-overlay, fade-through, iris-reveal, match-cut, curtain-reveal.

Shader blocks need WebGL, which software-renders on CPU and is slow. We re-implemented the CSS ideas inline (single timeline, seek-safe) in `engine/fx.py`.
