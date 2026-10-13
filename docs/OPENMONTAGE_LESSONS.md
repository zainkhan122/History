# Lessons from OpenMontage → Paper Trail production line

Studied: `github.com/calesthio/OpenMontage` @ e45f5b1 (2026-10-12). **AGPL-3.0** — we take *ideas/patterns only*, no code copied.

**What it is.** An agent-first video system. Python only for tools + persistence; the agent drives stages
(`idea → script → scene_plan → assets → edit → compose → publish`) from YAML pipeline manifests plus markdown
"director" skills, with JSON-schema'd artifacts, reviewer passes, checkpoints, 1,387 tests.
Its `documentary-montage` pipeline (archive footage + narration) is the closest match to Paper Trail.

**Where we already match it:** staged pipeline (`episode.sh`), cloud render in CI, HyperFrames runtime,
LUFS/ASR QA (`qa.py`), readability gate (`textqa.py` — stricter than theirs), media releases as SSOT,
public-domain archive sourcing, credits on screen.

---

## A. Three problems in OUR line found while comparing (fix first)

| # | Finding | Evidence | Fix |
|---|---|---|---|
| A1 | **Upload bitrate too low.** Their short-form spec: 8–15 Mbps, *<5 Mbps triggers a quality downgrade* on re-encode. Our film grain/light leaks are exactly what turns to mush. | `episode.sh` encodes `-crf 21 -maxrate 3.6M` → v2.1 = 41.9 MB / 87.4 s ≈ **3.8 Mbps** | Upload master at `-crf 18 -maxrate 12M -bufsize 24M` (~100–120 MB / 90 s). Lives only in the GitHub release, never in the workspace. Optional small preview copy for chat review. |
| A2 | **Channel bug sits in platform UI dead zones.** Dead zones on 1080×1920: top 108–210 px, right 84–120 px, bottom 300–320 px. Universal safe area = **900×1400 centred** (x 90–990, y 260–1660). | `.bug{right:40px; top:96px}` → hidden under the IG/Shorts top bar. Caption strip `max-width:960px` (x 60–1020) clips under the Shorts action column on long lines. | Move the bug to y≥260 / x≤990; caption `max-width:860px`; add a **safe-zone check to textqa** (glyph boxes vs. the union dead-zone mask) so this can't regress. |
| A3 | **`out/` is excluded from workspace snapshots** (also `build/`, `dist/`). The local v2.1 `final.mp4` was lost on the sandbox restart. | `series/.../ep01-petrov/out/` missing after restart | The release is the only durable home for finals (already true for the cloud path). Agent rule: never treat `out/` as storage, and re-render or fetch from the release. |

## B. Lessons worth adopting (mapped to our files)

### B1. Claims ledger = research brief + our verification rules → `research.json` + `tools/factcheck.py`
*They:* `research_brief` must have ≥3 `data_points` (claim, source_url, credibility, surprise_factor,
`usable_as: hook|stat_card|closing_punch`), ≥5 sources, `misconceptions[] {myth, reality, source}`,
`landscape {existing_content (what_it_misses), saturated_angles, underserved_gaps}`.

*Us:* facts live in prose (`script.md`); verification exists only as a policy in `CONTENT_STRATEGY.md`.

*Adopt:* per episode `research.json`:
```
claims[]: {id, text, sources:[{url,title,type:primary|scholarly|press}], quote_traced, myth_check, usable_as}
landscape: {existing:[{url, angle, misses}], saturated_angles[], our_gap}
```
`factcheck.py` gate: every VO sentence that contains a number, date, name or quote must map to a claim id with
≥2 sources, at least one primary or scholarly. The `landscape.our_gap` field is our written answer to YouTube's
"generic/template" test, so each episode records why it isn't a re-hash.

### B2. Voice performance plan + sample gate (directly serves "emotionally moving TTS")
*They:* a narration script must carry `voice_performance {intent, pacing_profile, energy_curve, pause_policy}`
and per-section `delivery_cues {pace, energy, emphasis_words, pause_before_s, pause_after_s, note}`.
"Read naturally" counts as a quality failure. Synthesize the **most emotional line first** (not line 1), approve it,
and lock the voice and settings. Any change of provider, voice or speed needs a new sample.

*Adopt:* add cues to the episode's script lines and map them in `synth.py`:
- pace → speed;
- energy → Chatterbox exaggeration/cfg;
- pauses → silence inserted by `trim_vo.py`;
- emphasis → line splits.

For ep01 the sample lines are the "survived by… the entire human race" beat and the wife beat. Record the
approved settings in `episode.json`.

### B3. Scene plan with shot language + plan linter (`reelkit/planlint.py`, own code)
*They:* `slideshow_risk` scores 6 dimensions (0–5): repetition, decorative visuals (no `information_role`),
weak motion, weak shot intent, typography over-reliance, unsupported "cinematic" claims.
`variation_checker` adds shot-size variety and a blacklist of generic prompt words ("stunning", "cinematic",
"modern"…). Edit rules:
- no two adjacent cuts share subject AND scale;
- ≤4 transition types;
- every cut has a reason;
- hold lengths come from a tone table (elegiac 4.0 s base, 2.5–7; urgent 1.2 s, 0.5–2.5);
- total duration within ±10 % of the brief.

*Adopt:* add `shot_size`, `information_role`, `motion: clip|parallax|text|still`, `reason` and `source_id` per
beat in `timeline.json`. Then `planlint` runs **before** assets and build, and fails on:
- adjacent same subject and scale;
- the same source used in two slots;
- motion share below the promise (B4);
- a text-only share above 35 %;
- holds outside the tone band;
- generic words in generator prompts.

**Cross-episode mode:** compare against previous episodes' plans (hook type, opening shot, format, music
key). This is our main defence against YouTube's "template-based" demonetisation category.

### B4. Delivery promise + "no silent fallback"
*They:* the proposal locks a promise (`motion_led` = ≥70 % of cuts real motion, still-fallback forbidden).
If a provider fails, stop and ask; never quietly turn the video into Ken Burns. Any swap is logged.

*Us:* when four Wan clips failed (no HF_TOKEN) we fell back to stills. You were told, but nothing enforces it.

*Adopt:*
- set `episode.json: promise {type: motion_led, min_motion_ratio: 0.5}`;
- the build computes the real ratio from `timeline.json` and fails, or writes an approved exception to
  `decisions.jsonl`.

### B5. Decision log + unified final review
*They:* `decision_log` (options considered, scores, selected, reason, user_approved, confidence) and a
`final_review` with the following blocks:
- technical probe;
- visual spot-check of opening, middle, climax and ending (black frames, broken overlays, unreadable text);
- audio checks (narration present, music present, unexpected silence, clipping, intelligibility);
- subtitle coverage;
- transcript vs script;
- promise preservation.

Status is pass, revise or fail; a reviewer gets at most 2 revision rounds, then PASS_WITH_WARNINGS. Findings
carry a severity (critical, suggestion, nitpick) and every critical one carries a proposed fix.

*Adopt:*
- merge `qa.json` + `textqa.json` + planlint + factcheck into one `review.json` per render, attached to the
  release;
- add `decisions.jsonl` (voice, music, clip substitutions, text fixes);
- add blackdetect/silencedetect to `qa.py`.

### B6. Content-addressed generation cache (big win under free quotas)
*They:* key = tool + version + model + seed + prompt (+ input-image hash). Only seed-pinned or deterministic
calls are cached, the manifest is JSONL, and writes are atomic. Editing one scene regenerates only that scene.

*Adopt:* `clips.py` writes `clipcache.jsonl` and stores blobs as release assets (`cache-clips`), so a rebuild,
a CI run or a new session never spends anonymous ZeroGPU runs (~3/day) twice. Pin seeds on every Wan call.

### B7. Better generator prompts (Wan 2.2)
*They:* a 5-slot prompt skeleton:
- **Subject:** attributes and how to disambiguate it.
- **Subject Motion:** actions in temporal order.
- **Scene:** setting, time of day, scene dynamics.
- **Spatial:** shot size, depth layers, and how these change.
- **Camera:** speed → lens → height → angle → focus → steadiness → movement.

Further rules:
- Wan rewards **200–400 words**.
- LTX degrades past ~80 words.
- Overlays never go in the prompt.
- Keep translation, rotation and zoom separate.

*Us:* about 40-word prompts, and LTX drifted. *Adopt:* a prompt template in `clips.py`, plus a "what to avoid" line.

### B8. Provenance on every asset
*They:* each clip records `provider, original_url, license, credit`, and no clip is reused across two slots.

*Adopt:* add those fields to `media.json` as required; the build fails on a missing licence; on-screen
credits and the description's credit block are generated from it.

### B9. Mix numbers to check our `audio.py` against
- Music bed **18–20 dB under VO** during speech.
- Whoosh starts **10–20 ms before** the visual change, with peak energy on the cut.
- Impacts −12 to −6 dB.
- True peak **≤ −1.5 dBTP** for YouTube. Our v2.1 was −1.12, so tighten the limiter.
- Text dwell time ≥ **13 characters/s** (a 30-character line needs 2.3 s). Add this to textqa as a WARN.

### B10. Small process wins
- Run `hyperframes validate` after `lint`. We pin 0.8.137, which has it: runtime seek checks plus contrast. It is a
  second net under textqa.
- **Contact-sheet approval before the cloud render** (their checkpoint gate). `textqa --sheet` already
  produces it; make it a required stop before `cloud.py render`.
- **Mid-stage checkpoints:** write `in_progress` to `STATE.json` when a stage starts, and archive superseded
  artifacts to `history/`, so a restart resumes inside a stage.
- **Contract tests in `check.yml`:** textqa against fixtures (the old v2 build = known 20 FAIL as a
  regression fixture), planlint, factcheck. All small and CPU-only.
- **Usage log instead of a $ budget:** ZeroGPU runs, Actions minutes, Pollinations calls per episode.

## C. Not adopting
- **Their whole orchestrator, tool registry and 40+ paid providers:** overkill for one series on a free stack.
- **Remotion, Backlot UI, avatars:** not needed.
- **Any code:** AGPL.

## D. Prioritised plan
Implementation progress (owner asked for P0 + P1, in phases):
- **Phase 1 — delivery (done, e2d01a3):** 12 Mbps master; `master.py` (−2.0 dBTP pre-AAC → ≤ −1.5 after); `hfcheck.py` (`hyperframes check`, since `validate` is deprecated); textqa dead zones + reading time; ep01 safe-area layout.
- **Phase 2 — claims ledger (done):** `series/<s>/<ep>/research.json` + `reelkit/factcheck.py` (stage `facts`, CI on every push). Ep01: 18 claims, 18 sources (6 primary/scholarly), 0 FAIL.
- **Phase 3 — voice performance (done):** `voice.json` plan (tone, energy, direction, pauses, climax, sample line) is the SSOT for narration + pauses (`plan.py` reads it); `reelkit/voice.py` check/sample/lines/kokoro/shape; stage `voice` + CI plan check. Ep01: 10/10 takes pass; climax pause shaped 0.37 → 0.6 s. Kokoro fallback measured at about half the pitch range of the Arena voice (8.8 vs 16.8 st), so it stays a fallback only.
- **Phase 4** planlint, promise lock, provenance · **Phase 5** clip cache, Wan template — pending.

| Pri | Item | Effort | Why now |
|---|---|---|---|
| **P0** | A1 bitrate, A2 safe zones (+ textqa check), B9 limiter −1.5 dBTP, B10 `hyperframes validate` | ~1 h | Visible quality on every upload; cheap |
| **P0** | B1 claims ledger + `factcheck.py` | ~2 h | Credibility + YouTube "original research" defence |
| **P0** | B2 voice performance plan + sample gate | ~1–2 h | Your "emotionally moving" bar |
| **P1** | B3 planlint (+ cross-episode), B4 promise lock, B8 provenance | ~3 h | Stops slideshow drift and template look before ep02–06 |
| **P1** | B6 clip cache, B7 Wan prompt template | ~2 h | Saves scarce free GPU runs; better clips |
| **P2** | B5 unified review.json + decisions.jsonl, B10 contact-sheet gate, checkpoints, contract tests | ~3 h | Robustness and resume |
| **P2** | CLIP-searchable archive corpus (their `corpus` idea: 5 frames/clip, embeddings, offline text search) | ~3 h + torch in cache | Faster footage hunting at ep10+ |
