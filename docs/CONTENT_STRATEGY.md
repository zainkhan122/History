# Content strategy: cadence, sources, verification, longevity (2026-10-11)

## 0 · The platform reality (why quality beats volume)
- YouTube renamed "repetitious" to **"inauthentic content"** (Jul 2025).
- On **16 Jul 2026** it clarified three non-monetisable categories:
  - generic or template-based videos;
  - unsatisfying content;
  - AI personas advising on sensitive topics.
- In Jan 2026 it terminated 16 faceless channels (35M subs).
- The systems judge the **whole channel**: upload frequency, format sameness, minimal editing.

Faceless and AI-assisted channels remain monetisable **if every video carries original research and storytelling**.
That's our model, but it means **no mass-production cadence**. Sources: aituber.app (Jul 2026), outlierkit.com (Jul 2026), newmoneymatrix.org (Aug 2026).

Shorts monetisation needs 1,000 subs plus 10M Shorts views in 90 days (or 4,000 long-form watch hours). Shorts RPM is low, so long-form is the revenue engine later.

## 1 · Cadence
| Phase | YouTube | TikTok · IG Reels · FB Reels | Why |
|---|---|---|---|
| **Pre-launch** (2 weeks) | Bank **6 finished episodes** before episode 1 goes live | Reserve handles, matching bios and banner | Never miss a slot; the first 10 uploads set the channel's audience signal |
| **Launch** (weeks 1–8) | **3 Shorts/week**: Mon · Wed · Fri, 22:00 PKT (13:00 ET / 18:00 UK) | Same day, native upload 2–3 h after YouTube, platform-specific caption and hashtags, no watermarks | Sustainable on the free stack with zero quality compromise |
| **Growth** (month 3+, if ≥ 70% "viewed vs swiped") | **4–5 Shorts/week** + **1 long-form every 2 weeks** (8–12 min "Paper Trail Files Vol. N" built from 3–4 episodes, expanded) | Same Shorts; long-form cut-downs as 60–90 s teasers | Long-form brings watch hours and the higher RPM |
| **Always** | Max 1 upload/day; never batch-upload; 1 Community poll/week ("Which file next?") | Reply to the first 30 comments within 1 h | The poll doubles as free topic research |

**Capacity check (free stack):**
- 10 images per agent turn, unlimited TTS, ~5–6 Wan clips/day with a free HF token, cloud render ~10 min.
- That supports **3–4 premium episodes/week**. Going faster would mean cutting research, which is exactly what the policy punishes.

**Scorecard (review every 10 episodes):**
- "Viewed vs swiped away" ≥ 70%;
- average % viewed ≥ 85% (Shorts loop);
- subs per 1k views ≥ 3;
- comments that dispute facts = 0.

Kill or rework any sub-format that misses 2 reviews in a row.

### Anti-template rotation (same brand, different structures)
1. **The File:** one forgotten person or decision (ep01 model).
2. **Close Call:** countdown of near-disasters, with an archival insert per item.
3. **Myth vs Record:** a famous claim against the primary document.
4. **One Document:** a single declassified memo, letter or photo, read and explained.

Rotate the 4 formats. Vary the hook type, scene count, music key and palette accents per episode.

## 2 · Where topics come from
| Layer | Sources |
|---|---|
| **Discovery** | Wikipedia (On this day, Did you know, Unusual articles), r/AskHistorians (moderated, sourced), r/todayilearned, Atlas Obscura, Smithsonian Magazine, JSTOR Daily, Public Domain Review, NYT *Overlooked* obituaries, Library of Congress "Today in History", National Archives (US/UK) blogs |
| **Cold War / declassified** (our strongest pillar) | CIA FOIA Reading Room, Wilson Center Digital Archive, National Security Archive (GWU), NSA declassified, NARA |
| **Demand check** | YouTube search autocomplete, Google Trends, competitors' top Shorts, our own Community polls. A topic needs a curiosity gap AND search or social demand |
| **Calendar hooks** | Anniversaries (posted on the date; evergreen, re-shareable yearly) |
| **Media** | Wikimedia Commons (PD/CC0), Internet Archive (DoD DIMOC/NARA CC0 films), Smithsonian Open Access (CC0), NASA, LoC, Europeana; plus our own AI plates and Wan clips |

## 3 · How accuracy is verified (gate before publish)
Each episode's `script.md` carries a **fact sheet**. **Every narrated claim gets one row:**
- claim;
- source 1 and source 2 (URL + archived Wayback link);
- type (primary / scholarly / major press / encyclopedia);
- confidence: ✅ confirmed · ⚠️ contested (script must hedge) · ❌ drop.

**Rules:**
1. **Two independent sources** for every number, date, name and quote. At least one must be primary (archive, document, first-hand interview) or scholarly/major press. Wikipedia is a map, never a source.
2. **Quotes are traced to the original**: book, interview or transcript, with date. If we can't find the origin, it isn't a quote; paraphrase and hedge.
3. **Myth check**: search "<claim> myth / debunked / AskHistorians". Popular stories (incl. Petrov's) have exaggerated versions; we narrate the defensible one ("might have" rather than "refused to launch").
4. **Media provenance**:
   - every clip and photo has its source URL and licence in `clips.json` / POST_KIT;
   - illustrative footage is **labelled on screen** (as with the 2023 Minuteman launch);
   - real people are only shown via PD photos or as clearly illustrated art.
5. **Disclosure**: AI imagery and voice are disclosed in the description; YouTube's "altered or synthetic" box is ticked when realistic.
6. **Owner sign-off**: a 2-minute read of the fact sheet before publishing. The AI researcher can be wrong, and a human gate is the cheapest insurance.
7. **Corrections**: pinned comment plus `script.md` accuracy notes. Repeated errors on a topic → that pillar gets three sources.

Planned automation (`tools/factcheck.py`, next):
- parse the fact sheet;
- fail if any script sentence has no fact ID;
- check every URL is live;
- auto-archive each URL via the Wayback save API;
- block publish on any ❌ or un-hedged ⚠️.

## 4 · Will topics last? Yes, if the pillars stay deep and the formats rotate
- **Supply is effectively unlimited.** Each pillar holds 50+ verifiable stories:
  - **Cold War close calls:** Petrov 1983, Arkhipov 1962, Goldsboro 1961, NORAD training tape 1979, Able Archer 83, Norwegian rocket 1995, Thule B-52 1968, Palomares 1966, …
  - **Overlooked people:** inventors, scientists, whistle-blowers, clerks who changed outcomes.
  - **Disasters that rewrote rules:** Triangle fire → labour law; thalidomide → drug testing; Tenerife → cockpit culture.
  - **Accidental discoveries and costly mistakes.**
  - **Dead Brands:** spin-off series.
  - **South Asia history:** a later Urdu/Hindi channel with the Kalaam series.
- **5 pillars × 50 = 250+ episodes ≈ 1.5–2 years** at 3/week before any repeat, and anniversaries make them re-shareable yearly.
- **Evergreen:** no news decay, so old episodes keep earning search and suggested views.
- **Risks and mitigations:**

| Risk | Mitigation |
|---|---|
| Template flag | Format rotation plus original research per episode |
| Low Shorts RPM | Long-form compilations and Facebook Reels |
| Advertiser-unfriendly war/death topics | No graphic imagery, factual tone |
| Platform AI-voice fatigue | Optional: the owner records VO later, which adds strong "human input" signal |
