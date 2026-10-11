# Viral animated reels made inside the agent: Hypit + vox-director + Lightpanda

**Prepared for:** a senior viral content lead (YouTube Shorts, IG Reels, TikTok, FB, WhatsApp Status)
**Date:** 11 Oct 2026 · **Workspace:** `~/repos` (the 3 cloned repos), `~/reelkit` (the engine I built), `~/viral_playbook/inputs` (ready-to-render reels), `~/reel_hamilton` (the finished proof reel)

---

## 0. Summary

1. **Proof first.** I built a finished 30.8-second, 1080×1920 vertical reel entirely inside this agent: *"The code that saved the Moon landing — Margaret Hamilton (1936–2026)"*. She died on 30 Sept 2026 and the NYT obituary ran on 7 Oct, so the topic is still current. I paid nothing to outside APIs. The ingredients were 6 collage keyframes, 9 shots, 14 effects tied to spoken words, word-by-word karaoke captions, a voice-over, a synthesized music bed and SFX, and audio normalized to about −14 LUFS. → `~/reel_hamilton/final.mp4`
2. **What each repo contributes:**
   - **Lightpanda** finds the facts and trends: 0.2–0.4s per page, structured Markdown output.
   - **vox-director** supplies the visual style and story structure: the Vox paper-collage look, 14 narrative arcs, hook and pacing rules, and a local motion engine.
   - **Hypit** supplies the timing system: visuals anchored to *words* rather than seconds, script/ASR separation, karaoke captions, and the "1 clone → 100 variants" approach.
3. **The fused engine (`reelkit`)** turns a topic into an upload-ready reel in about 5 minutes of compute. You approve two things: the voice and the keyframes.
4. **Ready to render now:** 4 more fully specified reels (Toebes, Navi Pillay, Taftan in Urdu, and an Iron Lung "On This Day" piece), plus 8 concept cards and a daily-series automation.

---

## 1. What I actually did (reproducible)

| Step | Tool used inside the agent | Repo idea it implements | Result |
|---|---|---|---|
| Trend and fact mining | `lightpanda fetch --dump markdown --dump-selector "#mp-itn"` etc. | Lightpanda | Live Wikipedia *In the news / Did you know / On this day* plus a full Hamilton fact page in under 1s |
| Angle and beat map | my reasoning plus vox-director `beat-layer.md` | vox-director (arc `hook_payoff`, hook `outcome_tease`, ending `loop_close`) | 6 beats, 77 words, ~30s |
| Keyframes | `generate_image` ×6, using vox's 5-part prompt (style block reused **word for word** on every beat) | vox-director `prompt-guide.md` | 6 Vox collage posters |
| QC / fix | `generate_image` edit ×2 | vox's "extract frames and look" rule | Fixed a garbled stamp ("EXPRED" → "KEEP") and removed real brand logos (monetization risk) |
| Voice-over | `add_voice` (you picked) then `generate_speech` per beat | vox: one narrator; each beat's real audio sets its length | 6 clips, 29.7s total |
| Word timing | `faster-whisper base.en` (installed in sandbox) | Hypit: WhisperX word alignment | Every word time-stamped |
| Script ownership | `reelkit/script.py` | Hypit Script syntax: `||` caption handoff, `<1202\|twelve-oh-two>` dual text, `*emphasis*` | ASR misheard "an abort" as "on a board"; captions still show the script's words |
| Motion | `reelkit/render.py` (Pillow → ffmpeg) | vox local engine: eased push / pull / tilt / pan, impact shake, punch zoom, confetti, whip cuts, paper grain, anti-monotony | 923 frames in 85s on 2 vCPU |
| Sound | `reelkit/audio.py` (numpy) | Hypit: sound events land on words | Tension pulse + clock tick → triumphant swell on "GO!" → tender pad; master alarm, impact and stamp SFX; bed ducks under the voice |
| Delivery | ffmpeg two-pass loudnorm, 12 Mbps cap | platform specs | `final.mp4`: 46 MB, 30 fps, AAC stereo 48 kHz, measured −14.9 to −15.3 LUFS (close to the −14 target) |

The events are written as words, not seconds. For example, `"b1:screaming"` triggers alarm + shake + red flash, `"b2:1202"` triggers a punch zoom, and `"b5:go"` triggers an impact, white flash and confetti. If you re-record the VO faster, slower, or in another language, every effect moves with its word. That is Hypit's core idea, and I reimplemented it in about 150 lines.

---

## 2. Repo analysis

### 2.1 Hypit (`hypit-ai/hypit`) — viral video **cloning** as code
- **What it is:** an agent skill plus a Node/TypeScript runtime with its own markup (SVML), recipes (`.svs`) and run files (`.svrun`). You give your agent a viral video; it rebuilds it as an editable project (footage, word-level captions, B-roll, effects) and then swaps the face, product, topic or language to create variants.
- **Key mechanics:**
  - **Word-anchored timeline:** `@{hair-gel} … @{/hair-gel}` marks a B-roll window on the words themselves.
  - **Script vs ASR separation.** Dual text `<D | Dee>` shows "D" on screen and says "Dee".
  - **Format playbooks** in `skills/hypit/references/playbooks/formats/`: ranking/listicle, talking-head, two-person podcast, street interview, presenter explainer, narration demo, short drama.
  - **Craft docs:** captions, B-roll, motion graphics, voice direction, sound mix.
- **Viral value:** the examples are ready-made formats with real costs: "GOAT DEBATE" tier list for $1.15, "DAILY CREATINE" podcast for $1.07, "NICE RIDE" street interview for $1.09. Each ships with 3 variant clones (swap host, flip the ranking, swap topic, translate).
- **Limits here:** needs Node ≥ 22.15 (the sandbox has 20), Chromium render farms (examples use 64 headless processes), and a model account (HypiHub or your own keys) for A-roll video and lip-sync. The code is open, but sources disagree on pricing: the README says "free to use", while third-party guides list monthly plans.
- **License:** modified Apache-2.0. Running it yourself, including **client work**, is allowed, and output belongs to you. Reselling it or running it as a multi-tenant SaaS needs a commercial license.
- **What I took:** word anchors, script/ASR split, dual text, `||` caption handoffs, color-box karaoke, events bound to words, and the "1 clone → N variants" production model.

### 2.2 vox-director (`Alisa0808/vox-director`) — topic → Vox paper-collage film
- **What it is:** an MIT-licensed agent skill with 22 Python scripts running on the Atlas Cloud API plus ffmpeg. Topic → beat map (approval gate) → style bake-off (approval gate) → keyframes (nano-banana-2) → motion (Gemini Omni / Kling) → TTS + music → assemble.
- **The valuable part is the creative engine, not the API calls:**
  - `beat-layer.md`: 14 narrative arcs, 9 hook patterns, timing tables (30s = 6–8 beats, ~75 words), a cut every 3–5s, endings `hard_cut | quick_cta | loop_close`, and anti-monotony (no two adjacent beats use the same camera move; static is saved for the payoff).
  - `prompt-guide.md`: the 5-part image prompt, a 9-axis motion vocabulary, 10 theme presets (american-retro, swiss-modern, punk-zine, soviet-constructivist, newsprint-editorial…), and C-roll locks for faces and products.
  - `models-and-gotchas.md`: Omni and Seedance block real celebrities and logos; Kling allows them; **the local engine bypasses all of this**.
  - `motion.py`, `kenburns.py`, `mg_scrapbook.py`: the no-AI-video motion path, which is what makes it usable here.
- **Modes:** B-roll (topic only), A-roll (restyle your talking-head video), C-roll (one photo of a person or product anchored in the collage), and Host (digital presenter).
- **Limits here:** Atlas Cloud i2v, lip-sync and music need an `ATLASCLOUD_API_KEY`. The scripts are plain Python plus ffmpeg, so **they run in this sandbox as-is** if you supply a key.

### 2.3 Lightpanda (`lightpanda-io/browser`) — the research engine
- **What it is:** a headless browser written from scratch in Zig for agents. It is not a Chromium fork. It offers a CDP server for Puppeteer/Playwright, an MCP server, an agent mode that records reusable "PandaScripts", and `fetch` with `--dump html|markdown|semantic_tree`, `--dump-selector`, and multiple URLs at once with `--json`. License: AGPL-3.0.
- **Measured in this sandbox:** HN front page in 0.19s; a Wikipedia section in 0.41s; full article pages (~100 KB) in under 1s. The vendor benchmark claims ~16× less memory and ~9× faster than headless Chrome.
- **Viral value:** finds the topic, checks the facts, and supplies the stats, all fast enough to run in a loop (daily series, news-jacking, comment mining).
- **Limits:** `--dump png/pdf` is a *text-only* rendering, so it can't make visual screenshots for B-roll. Reddit blocks it, and RSS/XML comes back empty; use `curl` for RSS. JS-heavy pages work through `--wait-ms` / `--wait-selector`.

---

## 3. What can run inside the agent

| Capability | Native in this agent | How |
|---|---|---|
| Trend and fact research | ✅ | Lightpanda binary (`~/.cache/bin/lightpanda`, via setup.sh) + `web_search` |
| Script, hooks, beat maps, A/B variants | ✅ | Reasoning + vox arcs/hooks |
| Collage keyframes, B-roll stills, thumbnails | ✅ | `generate_image` (+ edit for fixes or product/face locks) |
| Voice-over (EN, UR, and other languages) | ✅ | `add_voice` → `generate_speech` |
| Word-level timing | ✅ | faster-whisper (base.en; `small` for Urdu) |
| Motion graphics, karaoke captions, transitions | ✅ | `reelkit/render.py` |
| Music bed + SFX | ✅ (procedural) | `reelkit/audio.py` |
| Mix, loudness, encode | ✅ | static ffmpeg 7 |
| AI image-to-video, lip-sync, talking A-roll | ⚠️ needs your key | vox-director with an Atlas key, or Hypit with HypiHub / your API |
| Licensed hit music | ❌ | add it in-app on TikTok/IG (trending audio lifts reach) |

**Sandbox limits:** 2 vCPU, 2 GB RAM. One `-preset medium` 1080p encode was killed for running out of memory, so reelkit uses `veryfast` with 2 threads.

---

## 4. The fused pipeline (`~/reelkit`)

```
LIGHTPANDA (research)           VOX-DIRECTOR (look + story)          HYPIT (time = words)
 news / DYK / OTD / wiki   →    arc + hook + 6 beats + prompts  →    script with || <d|s> *emph*
        │                               │                                   │
        └──────────── reel.json (one file = the whole reel) ────────────────┘
                 │
   generate_image ×6  →  generate_speech ×6  →  script.py align (Whisper words)
                 │
   render.py: camera moves, shake/punch/flash/confetti ON WORDS, whip cuts, grain, karaoke
                 │
   audio.py: mood beds + SFX on words + ducking + 2-pass loudnorm → final.mp4 (+ cover frame)
```

> **Toolkit v2:** run `source ~/reelkit/setup.sh` first in every session. Full tool docs are in `~/reelkit/README.md`. New in v2:
> - free Kokoro VO (`tts_kokoro.py`);
> - collage stickers (`cutout.py`) and `sticker`, `lottie` and `mouth` events;
> - Rhubarb talking characters (`lipsync.py`);
> - LaMa text fixing (`inpaint.py`);
> - beat-synced real music (`beats.py`);
> - auto-editor.

**Run sequence:**
```bash
source ~/reelkit/setup.sh
# 0) Research
~/.cache/bin/lightpanda fetch --dump markdown --dump-selector "#mp-itn" https://en.wikipedia.org/wiki/Main_Page
# 1) Write reel.json (see inputs/), generate keyframes from its "keyframes" prompts
# 2) English: python3 ~/reelkit/tts_kokoro.py reel.json   (free)   |  Urdu: print lines -> generate_speech per beat
python3 ~/reelkit/script.py tts   reel.json
python3 ~/reelkit/script.py align reel.json        # -> words.json
python3 ~/reelkit/render.py reel.json               # -> timeline.json (video in ~/.cache/tmp)
python3 ~/reelkit/audio.py  reel.json               # -> final.mp4
```
**`reel.json` keys:**
- `beats[].script` uses Hypit markup.
- `beats[].shots[]` has `img`, a `move` (push_in | pull_out | tilt_up | tilt_down | pan_lr | pan_rl | static), `focus`, `at` (a word anchor), and `cut` (whip | none).
- `beats[].mood` is tension | triumph | tender.
- `events[]` has `at` (`"b5:go"`, `"b5:people#2"`, `"b2:@3"`), a `type` (punch | shake | flash | confetti | sticker | mouth | lottie), and an optional `sfx` (alarm | impact | stamp).
- Options: `rtl` + `font` for Urdu/Arabic captions, `palette`, `caption_y`.

---

## 5. Viral mechanics built into every reel

| Mechanic | Rule (source) | How reelkit enforces it |
|---|---|---|
| Hook ≤ 3s | vox `beat-layer.md`: "~65% of viewers decide by 3s"; pick 1 of 9 hook patterns | Beat 1 = claim + baked headline + caption on frame 1 + an effect within 3.5s |
| Pattern change every 3–5s | vox cadence rule; never hold a shot > 7s | Each shot 2.5–5.5s; long beats split by a word-anchored second shot |
| Anti-monotony | vox: adjacent beats never share a camera move; static reserved for the payoff | Moves alternate scale ↔ translate; `static` on the payoff beat |
| Captions on (most people watch muted) | Hypit caption craft: whole-phrase cues, current word highlighted | Color-box karaoke; emphasized words turn mustard once spoken |
| Sound that "hits" | Hypit: sound events are part of the graphic system | SFX land on words; the music changes mood at the turning point |
| Rewatch loop | vox `loop_close`: last line mirrors the first | "…hers didn't." answers "the computer started screaming" |
| Comment bait | — | Every input file has a pinned question and a CTA |
| Platform-safe | vox gotchas + my QC | No real brand logos in generated art; real people shown as stylized collage, not photoreal deepfakes |

---

## 6. Ready-to-render reels

| # | File | Hook (first 3s) | Arc / ending | Why it can travel |
|---|---|---|---|---|
| 01 ✅ rendered | `~/reel_hamilton/reel.json` → `final.mp4` | "Three minutes before the first Moon landing… the computer started screaming." | hook_payoff / loop_close | Obituary news cycle this week; tech, STEM and women-in-history audiences; tagline "hers didn't" |
| 02 | `inputs/02_toebes_dementia/` | "At 21, he moved into a locked dementia ward. Not as a nurse. As a resident." | story_spine / question CTA | Featured in Wikipedia DYK this week; emotional; strong share-to-family signal |
| 03 | `inputs/03_pillay_nobel/` | "At five, she stood in a courtroom and testified against the man who robbed her." | origin / loop_close ("that courtroom finally paid her back") | Nobel Peace Prize news this week; rags-to-legacy arc |
| 04 | `inputs/04_taftan_urdu/` (Urdu, RTL Nastaliq captions) | "پاکستان کا ایک شہر ایک آتش فشاں کے نام پر ہے… اور وہ آتش فشاں ایران میں ہے۔" | myth_buster / punchline question | Local pride + "wait, what?" geography; almost no Urdu collage-explainer competition; WhatsApp-shareable |
| 05 | `inputs/05_iron_lung_otd/` | "In 1928, an eight-year-old girl couldn't breathe. So doctors put her inside a machine." | hook_payoff / quick_cta "Give the drops" | Daily "On This Day" series pilot; Pakistan public-health angle (**check the WHO/GPEI polio-endemic status before posting**) |

Each file holds **verified research facts with sources, keyframe prompts, the Hypit-markup script, shots, word-anchored events, the voice brief, and posting copy** (YT title, IG caption, hashtags, pinned comment). All 5 pass parsing and anchor checks, and each runs 30–36s of narration.

### 6.1 Hypit-style "1 clone → N variants" for reel 01 (only beat 1 changes: 1 new VO clip + optional keyframe)
- **A (current, outcome_tease):** "Three minutes before the first Moon landing… the computer started screaming."
- **B (mistake_callout):** "You've been told Neil Armstrong saved Apollo 11. The real hero never left Earth."
- **C (direct_question):** "What do you do when the computer flying you to the Moon… crashes?"
- **D (Urdu remake):** "چاند پر اترنے سے تین منٹ پہلے… کمپیوٹر چیخنے لگا۔" (re-run `script.py align` with `asr_language: ur`; every effect re-anchors automatically)

Post A/B/C as separate Shorts 48h apart, or run them as Meta ad hook tests. Keep the winner as your template.

---

## 7. More concept cards (fill in a reel.json the same way)

1. **Hypit "Tier List" (ranking-listicle): "Ranking Pakistani breakfasts."** Halwa puri, nihari, paratha-chai, anda shami, siri paye, lassi. Collage icons drop onto an S–D board, with comedy B-roll stills on the punchlines ("Siri paye? D tier… for your cardiologist"). Comments become arguments, which is good for the algorithm. *Needs:* a tier-board overlay in render.py (~60 lines: rows plus icon drop on word anchors). Easiest next upgrade.
2. **Hypit "Two-person podcast" with stills:** two generated collage characters (e.g. "Chai Uncle" vs "Gen-Z Coder") in a split screen, captions colored per speaker, one `add_voice` each. Script example: "Uncle, AI will take your job." / "Beta, it can't even find my car keys." Mouths don't move; collage style makes that acceptable. For real lip-sync, use Hypit + Seedance or vox Host mode with a key.
3. **Myth-buster series: "Nobody actually said that."** Fake quotes (Einstein's "insanity" line, Marie Antoinette's "let them eat cake"). Lightpanda pulls the Wikiquote "Misattributed" sections. Arc `myth_buster`, theme `punk-zine`.
4. **C-roll product ads for your clients:** one product photo → `generate_image` edit with vox's PRODUCT LOCK prompt → 6 collage posters around the real packshot → 15s `pas` arc (Problem → Agitate → Solve → Proof → CTA). Make 5 hook variants per SKU in one session.
5. **News-jack within 24h:** a cron-style loop. Lightpanda fetches `#mp-itn` each morning, the agent scores items (novelty × emotion × local relevance), drafts a beat map, and you approve. Today's candidates were the Nobel Chemistry and Physics winners: "Kagan & Soai — why some molecules copy themselves" (autocatalysis) and "Halzen — the telescope buried under Antarctic ice" (neutrino astronomy, IceCube).
6. **"Did You Know" Shorts series:** today's DYK had "13 Shibuya billboards announced one band at once" and "a video of letters on a small toy put conspiracy theorists on edge". These are 15s single-fact reels: 3 beats, one punch, `hard_cut` for rewatches.
7. **Urdu "شہر کی کہانی" (city story) series:** Taftan → Gwadar → Ziarat → Hunza. Lightpanda reads each town's Wikipedia page; the same template and voice give you 1 reel per day for 30 days with consistent branding (series build follow habits).
8. **Football/cricket "GOAT debate" (Hypit's football example):** the tier list with player names as text cards, not faces. That avoids likeness and rights blocks; vox notes Omni and Seedance refuse celebrities anyway.

---

## 8. Posting checklist (per reel)
- 1080×1920, 30 fps, H.264 ≤ 12 Mbps, AAC 48 kHz, about −14 LUFS: already handled by `audio.py`.
- Cover frame: export the hook frame with the headline visible (`cover_thumbnail.jpg` for reel 01).
- Keep text out of the bottom ~18% and right ~12% (platform UI). Captions sit at about 71% of height.
- First line of the caption = the hook rephrased. 3–7 hashtags. Pin the question comment.
- TikTok/IG: optionally add a low-volume trending sound in-app; keep the VO dominant.
- Tributes and news: keep a respectful tone, and cite the source in the description (e.g. NYT 7 Oct 2026 for Hamilton).

## 9. Caveats
- No native image-to-video or lip-sync: motion is 2.5D camera + effects over stills. That works well for collage explainers but not for talking-head or UGC formats; for those, use Hypit or vox A-roll/Host with your API key.
- The music is procedural (fine for VO-led reels). For music-driven trends, use platform audio.
- Facts in the input files come from live Wikipedia as of 10–11 Oct 2026. Re-check anything time-sensitive (flagged in `verify_before_posting`).
- Generated images can garble text. Always QC frames (reelkit's contact-sheet step caught "EXPRED").
