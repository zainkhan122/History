# Paper Trail: micro-history in collage (series bible)

**Promise:** one forgotten true story per file, told in 60–90 s, documented like an investigation.

## Look
- Cut-paper collage on aged cream paper.
- Palette: cream `#EFE6D2`, ink `#141414`, red `#C8102E`, mustard `#E3A72F`.
- Type:
  - Anton for titles;
  - Oswald for captions;
  - DM Serif Display italic for quotes and emotional lines;
  - Special Elite for typewriter evidence tags.
- Recurring devices:
  - typed date and place tags;
  - rubber stamps;
  - pinned index cards on red thread;
  - counters;
  - torn-paper wipes;
  - film grain and vignette;
  - "PAPER TRAIL · FILE NN" bug;
  - end card that repeats the opening title, so the Short loops.

## Sound
- Warm documentary narrator.
- Original procedural score: dread drone → tension pulse → silence at the turn → piano resolution.
- SFX: typewriter, stamp thuds, paper, heartbeat and ticks.

## Rules
- Every narrated fact sourced in `script.md`.
- Hedge contested claims.
- Real people shown only via public-domain photos or clearly illustrative art.
- Credit and AI-disclose in `POST_KIT.md`.

## Episode template
Copy `ep01-petrov/`, then replace:
- `script.md`
- `vo/`, `assets/`
- `words.json` (whisper timings)
- the scene blocks in `build.py`
- the arrangement in `score.py`

The engine pieces are reusable as-is.

## Readability rule (owner standard, 2026-10-11)
No free-floating light text over imagery.
- Every text sits on **its own plate** (paper strip, ink strip, card), on a **scrim ≥ 0.85**, or has a **≥ 3 px outline**.
- Reds:
  - `#A50B25` for red text on paper;
  - `#FF4D4D` for red text on dark;
  - brand `#C8102E` only as a fill or background behind cream text.
- Minimum sizes: 40 px primary, 22 px credits.
- Enforced by `reelkit/textqa.py`, which runs automatically in `episode.sh` (stage `textqa`):
  - FAIL < 3:1 blocks the render;
  - the target is ≥ 4.5:1 (WCAG contrast measured behind the glyphs, worst 10% of pixels).
