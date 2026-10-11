# Niche & Free-Tools Research for reelkit
*Researched 11 Oct 2026. Every RPM figure is a third-party estimate, and the estimates vary a lot. Treat them as relative, not as promises.*

---

## 0. TL;DR

**Build these five series first.** They score best on demand × virality × how easily reelkit makes them today:

| # | Series (working name) | Language | Why it wins | reelkit fit today |
|---|---|---|---|---|
| 1 | **"Paper Trail": micro-history in collage** (forgotten events, "the day…", OTD) | EN (global) | History/documentary RPM ~$5–12, medium competition; story retention; fits the "storytelling + research" lane YouTube says stays monetisable | ★★★★★ This is exactly the Hamilton reel's style |
| 2 | **"Dead Brands": one company, one fatal mistake** (rise/fall micro-docs) | EN | Business case studies ~$6–14 RPM; a proven faceless format (MagnatesMedia); the reels-studio owner runs a whole channel on it | ★★★★★ Collage + stickers + punch/flash; long-form plus 2 Shorts |
| 3 | **"Brain Glitch": psychology/curiosity explainers** with a talking paper character | EN | Psychology & curiosity is the #1 AI-fit niche in one 2026 ranking ($8–14 RPM); Psych2Go-style demand | ★★★★☆ mouth layer + stickers; keep claims sourced |
| 4 | **"Kalaam": Urdu classical poetry visualised** (Iqbal, Ghalib, Mir: public domain) | UR | Huge Pakistani appetite for Urdu content; **Iqbal Day is 9 Nov** (a seasonal spike in 4 weeks); low production cost | ★★★★☆ RTL Nastaliq + karaoke ready. Needs an Urdu voice (Gemini TTS free tier lists Urdu, or your own voice) |
| 5 | **"Numbers Don't Lie": South-Asia data stories** (PK vs IN vs BD, prices, cricket stats) | EN + UR captions | "Who wins?" debate; screenshot-able; low saturation if the data is checked | ★★★☆☆ Needs a new `chart` layer (about one day of work) or HyperFrames |

**Five free tools/patterns to add next** (ranked by impact per hour):
1. **GitHub Releases + a private-or-public repo as the source of truth.** This fixes our 128 MB workspace limit and the sandbox wipes. It's the reels-studio pattern.
2. **GitHub Actions render farm.** A public repo gets free 4 vCPU / 16 GB runners, 5 in parallel, so reels render off-sandbox.
3. **Gemini API free tier.** Text models for scripting, plus **TTS models with Urdu**, which would close our biggest gap.
4. **Cloudflare free stack:**
   - a Worker + Cron Trigger as a 24/7 "trend radar and scheduler" (Wikipedia pageviews + GitHub + news);
   - Workers AI FLUX-schnell (~230 images/day free) for B-roll and thumbnails;
   - Pages for OAuth callbacks and a public portfolio page.
5. **YouTube Data API direct upload and IG Content Publishing API.** Uploads now have their own 100/day bucket on YouTube; IG allows 100 API posts per 24 h. Optionally use **Buffer free** or **Postiz self-hosted** as one scheduler.

---

## 1. Ground rules for any 2026 "viral system"

These rules decide which niches are worth it. Read them before the rankings.

- **Template factories get demonetised. AI-assisted originals do not.** YouTube's July 2026 clarification makes three buckets ineligible:
  1. generic or template-based content;
  2. unsatisfying content;
  3. AI personas advising on health, finance or legal topics.

  The same guidance confirms that AI-assisted video with original commentary, storytelling or research **still monetises** ([noobclaw](https://noobclaw.com/blog/ai-video-monetization-youtube-2026-inauthentic-rules/), [ytgrowth](https://ytgrowth.io/blog/youtube-ai-policy)). In January 2026, 16 mass-production channels (35M subs) were terminated ([aituber](https://aituber.app/blog/faceless-youtube-channels-demonetized-2026/)).
- **Since 1 Oct 2026**, Shorts ranking favours originals. "Template-based bulk changes" and voice-overs describing on-screen action don't count as added value (cited in reels-studio's report from [androidheadlines](https://www.androidheadlines.com/2026/10/youtube-cuts-reach-reuploaded-shorts-originality-push.html)).
- **Money from Pakistan:**
  - Shorts pay from a per-country pool. Pakistan Shorts RPM is roughly $0.007–0.03, against $0.10–0.32 in the US ([ytmoneycalculator](https://ytmoneycalculator.com/youtube-shorts-earnings-calculator/), [fluxnote](https://fluxnote.io/guides/youtube-shorts-rpm-by-country)).
  - TikTok Creator Rewards is not available in Pakistan.
  - The YPP bar doubles on 1 Feb 2027 (20M Shorts views in 90 days).

  **Implication:** use Shorts and Reels for reach, and earn from **English long-form**, affiliates, services and sponsors. The audience's country matters more than the creator's.
- **AI disclosure** is needed only for *realistic* synthetic people or events. Clearly animated or collage content generally doesn't need it ([layer3labs](https://www.layer3labs.io/guides/youtube-ai-content-policy)). That's a structural advantage of reelkit's paper-collage look.

**Our anti-slop rules,** borrowed from reels-studio's `finance/MASTER_RULES.md` and adapted:
1. One real subject per film, with a `sources.md`.
2. A new picture every 4–6.5 s, never looped.
3. **The last film is not a template**: vary the opening line, closer and thumbnail layout every time.
4. No legal or advice language on screen.
5. Every Short is a cut of an original long-form or an original standalone, never a re-skin.

---

## 2. Scoring method

Each niche is scored 1–5 on five dimensions:

| Dimension | What 5 means |
|---|---|
| **D**emand | Search/browse demand + evidence of big faceless channels in 2026 |
| **V**irality | Built-in share/comment/rewatch mechanics (debate, surprise, play-along, identity) |
| **E**ase | How much reelkit already does it *today* inside this agent (collage images, Kokoro EN VO, karaoke captions, Urdu RTL, stickers, talking mouths, Lottie, beat-sync) |
| **M**oney | RPM of the likely audience + affiliate/sponsor/service potential for a Pakistan-based creator |
| **R**isk (inverted) | 5 = low policy, accuracy or copyright risk |

Total = D + V + E + M + R (max 25).

---

## 3. Ranked niche table

| Rank | Niche | D | V | E | M | R | **Total** | Evidence | reelkit features used |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **Micro-history / forgotten events / "On this day"** | 4 | 4 | 5 | 4 | 4 | **21** | History RPM $5–12; OverSimplified 8M+ subs; micro-history called low-competition ([mediacube](https://mediacube.io/en/blog/best-youtube-niches), [fableclip](https://fableclip.com/blog/best-faceless-youtube-niches)) | collage images, punch/whip, stickers, grain, karaoke, burst Lottie |
| 2 | **Business rise/fall micro-docs** | 4 | 4 | 5 | 5 | 3 | **21** | Business case studies $6–14 ([clipspeed](https://www.clipspeed.ai/blog/faceless-youtube-niches-2026.html)); MagnatesMedia 1.85M ([fliki](https://fliki.ai/blog/best-faceless-youtube-niches)); "The Public Record" channel in yt-tts | collage + logo-free "object" art, stat stickers, flash/shake on the "death" beat |
| 3 | **Psychology & curiosity ("why your brain…")** | 5 | 4 | 4 | 4 | 3 | **20** | Psychology & curiosity #1 for AI fit, $8–14 ([fableclip](https://fableclip.com/blog/best-faceless-youtube-niches)); Psych2Go 13M ([flowshorts](https://flowshorts.app/blog/best-faceless-youtube-channels)) | talking paper character (mouth layer), stickers, karaoke |
| 4 | **Science / space "what if"** | 4 | 5 | 4 | 3 | 4 | **20** | Space $4–7, binge-able; Zack D Films and Ridddle prove "what if" is sticky ([taletok](https://taletok.io/blog/best-faceless-youtube-channels/)) | NASA public-domain imagery + collage, Lottie, shake |
| 5 | **Urdu classical poetry (Iqbal/Ghalib/Mir)** | 4 | 4 | 4 | 2 | 5 | **19** | Urdu content channels reach millions (e.g. The Urdu Teacher, 4M subs, 320M views ([speakrj](https://www.speakrj.com/audit/top/youtube/pk/religion))); quote-slideshows are risky, so visualise each couplet's *meaning* | RTL Nastaliq, karaoke, grain, beat-sync, Urdu VO (Gemini TTS or your own voice) |
| 6 | **Data stories: South Asia comparisons** | 4 | 5 | 3 | 3 | 4 | **19** | Data comparisons $5–9, medium competition ([youtubeniches](https://youtubeniches.com/blog/best-faceless-youtube-niches-2026)); reels-studio's top pick | **Needs a chart layer** (bar race, line, counters) |
| 7 | **Cricket stats & records (PK/IN audience)** | 5 | 5 | 3 | 2 | 3 | **18** | "Pakistan Cricket" channel 6.35M subs, ~36M views/month ([youtubers.me](https://us.youtubers.me/pakistan-cricket/youtuber-stats)); Cricsheet data is ODC-BY | chart layer + collage players *without* real photos or footage (copyright) |
| 8 | **Animated folk tales / scary stories (Urdu & EN)** | 4 | 4 | 4 | 2 | 4 | **18** | Horror is the "most format-native faceless niche" ([fableclip](https://fableclip.com/blog/best-faceless-youtube-niches)); Urdu Kahaniyan 467K | collage scenes, talking characters, inpaint for visual gags, rain/grain |
| 9 | **Spoken English for Urdu speakers** | 5 | 4 | 3 | 3 | 5 | **20*** | Big demand, saves and sends; reels-studio's `say-this` template | karaoke EN + RTL UR captions. *Your own voice strongly recommended,* which lowers Ease |
| 10 | **AI tools, "tested not hyped"** | 5 | 4 | 3 | 5 | 2 | **19** | AI tools $13–22 RPM long-form ([youtubeniches](https://youtubeniches.com/blog/best-faceless-youtube-niches-2026)); very crowded; trust is the edge | needs screen captures (Lightpanda can't render; HyperFrames capture can) |
| 11 | **Book/idea summaries** | 4 | 3 | 4 | 4 | 3 | **18** | Escaping Ordinary's *Atomic Habits* video has 14–19M views ([invideo](https://invideo.io/blog/faceless-youtube-channel-ideas/)) | collage metaphors, stickers |
| 12 | **Local-business promo videos (service)** | 2 | 1 | 5 | 5 | 5 | **18** | Not viral, but direct cash; one template becomes N clients | everything; the client supplies assets |
| — | Islamic history / reminders | 5 | 4 | 3 | 2 | 2 | 16 | Enormous PK demand, but accuracy and sectarian sensitivity; do it only with scholarly sources and respect | — |
| — | Motivational quotes, Reddit stories, AI-slop "skeleton" 3D, re-uploads, kids' content | — | — | — | — | — | **Avoid** | Saturated and/or explicitly targeted by the 2026 policies; made-for-kids limits | — |

\* Row 9 scores high on paper, but it depends on a human voice for trust.

**The sweet spot is rows 1–4.** reelkit already makes them at top quality, they monetise in English long-form, and the collage style itself signals "original, designed content". Instagram's own originality examples include "a visual story" and "new graphics that add information".

---

## 4. Concrete series blueprints (ready to brief)

Each follows the vox-director rules: hook ≤3 s, a cut every 3–5 s, 6–8 beats per 30 s, and a loop close.

### 4.1 "Paper Trail": micro-history (EN, 30–45 s Shorts + 8–10 min monthly long-form)
**Look:** the Hamilton collage block (navy/cream/red/mustard). **VO:** Kokoro `bm_george` or `am_michael`.

| Reel | Hook (first 3 s, on screen + spoken) | Payoff / loop |
|---|---|---|
| The Great Emu War (1932) | "Australia sent soldiers with machine guns… against birds. The birds won." | "…and the emus are still there. Want the rematch?" |
| Carrington Event (1859) | "In 1859 the sky caught fire, and telegraph wires sparked on their own." | "If it happened today… your phone is the telegraph." |
| Mohenjo-daro's drains | "4,500 years ago, this city had covered drains. London didn't until the 1860s." | Loop back to the first frame's brick close-up |
| The Dancing Plague (1518) | "In 1518, hundreds of people danced… and couldn't stop." | Open question in the comments: "What do YOU think caused it?" |

**Sources:** Wikipedia + primary or academic citations in `sources.md`. Imagery is generated collage. Use Wikimedia Commons PD scans as textures, after checking licences.

### 4.2 "Dead Brands": one company, one fatal mistake (EN)
**Format:** 8–11 min long-form + 2 Shorts (hook cut + payoff cut), as yt-tts/finance does.

| Episode | One-line spine (the "one villain") |
|---|---|
| Kodak | Built the first digital camera (1975, Steve Sasson), then shelved it to protect film |
| Blockbuster | Turned down buying Netflix (2000) |
| Nokia | Bet on Symbian after the iPhone (2007–2011) |
| Pakistan-relevant pick | e.g. a once-dominant local brand (research first; avoid defamation; public record only) |

**reelkit:**
- the company "object" as a sticker (cutout);
- a counter sticker for money lost;
- `flash` + `shake` on the collapse beat;
- karaoke only on keywords (2–4 words, per their P8 rule).

### 4.3 "Brain Glitch": psychology explainers with a recurring paper mascot (EN)
**Mascot:** one generated paper-cut character, with `lipsync.py --make-sprites` mouths, reused for brand recognition.

| Reel | Hook |
|---|---|
| Doorway effect | "Walked into a room and forgot why? Your brain hit 'save' at the door." |
| Zeigarnik effect | "Your brain hates unfinished things. That's why you'll watch this to the end." |
| Spotlight effect | "Nobody noticed your stain. Science says they barely noticed YOU." |

**Rule:** cite peer-reviewed studies in the pinned comment. No therapy or medical advice (YouTube's AI-persona bucket).

### 4.4 "Kalaam": Urdu poetry visualised (UR, 20–40 s)
**Poets:** Iqbal (d. 1938), Ghalib (d. 1869) and Mir (d. 1810) are public domain. Faiz, Faraz and Jaun Elia are **not**.

**Each reel:**
1. Recite one couplet.
2. Show a 3-beat visual metaphor of its meaning in collage.
3. Give a one-line plain-Urdu explanation.
4. The couplet returns as RTL karaoke.

**Peg:** 9 Nov, Iqbal Day. Prepare an Iqbal mini-series now:
- "Khudi ko kar buland itna…";
- "Sitaron se aage jahan aur bhi hain…";
- "Tu shaheen hai…".

**Voice:** your own recording (best), or Gemini TTS (free tier lists `ur`). Machine-check it with a whisper roundtrip as reels-studio does.

### 4.5 "Numbers Don't Lie": South-Asia data (EN VO + Urdu subtitles)
**Ideas:**
- GDP per capita, PK vs BD vs IN, 1990→2025 (World Bank, CC BY);
- price of 1 kg of atta over time;
- Pakistan's population 1951→2023 census;
- cricket "most sixes" race (Cricsheet).

**Must-do:**
- run a series-break check (reels-studio caught Pakistan's 2000 GDP rebase, a statistical revision rather than a boom);
- footnote sources on screen.

**Build first:** a `chart` layer in `render.py` (bar race, line reveal, count-up), or the HyperFrames route (§6).

---

## 5. Seasonal calendar (next 6 months)

| When | Peg | Series |
|---|---|---|
| Now → 31 Oct | Halloween (global) | Scary folk tales: jinn, churail, Chalawa (as folklore, respectfully), plus "real history behind Halloween" |
| **9 Nov** | **Iqbal Day** (PK) | Kalaam: Iqbal mini-series (start production this week) |
| Mid-Nov → Dec | Year-end | "2026 in 60 seconds" data recap, "brands that died in 2026" |
| 25 Dec | Quaid Day (PK) | Micro-history: little-known Jinnah facts (sourced) |
| Jan | New-year habits | Brain Glitch: habit psychology |
| ~early Feb 2027 | Ramadan begins (moon-dependent) | Respectful history/science pieces (Islamic Golden Age scientists: Al-Khwarizmi, Ibn al-Haytham) |
| 1 Feb 2027 | New YPP thresholds apply | Have long-form running before this |

---

## 6. Lessons from `zainkhan122/yt-tts` (reels-studio)

The repo has **no licence**, so we take the ideas only and copy no code. It was built in the same Arena sandbox type as ours, so its lessons transfer directly.

| Pattern in reels-studio | Why it matters | How we adopt it in reelkit |
|---|---|---|
| **GitHub = single source of truth. Finished MP4s go to GitHub Releases**, not the workspace | Fixes the 128 MB and file-count limits and survives sandbox wipes | Add `reelkit/publish.py`: upload `final.mp4`, the cover and the kit to a Release; keep only manifests locally |
| **One-command bootstrap** (sparse + blobless clone, idempotent, ~3 min) | Same as our `setup.sh`, but it also restores code from GitHub | Extend `setup.sh` to `git pull` reelkit from your repo |
| **Cloud render via GitHub Actions** (`render.yml`: 1 runner per brief, max-parallel 5, 4 vCPU / 16 GB, free on public repos) | 5 reels in parallel without our 2 GB RAM OOM risk | A `render.yml` matrix running `setup.sh → render.py → audio.py → Release` |
| **Brief JSON → video + post kit** (`seo_pack.py`: per-platform titles, caption limits, hashtag caps) | One input per video; SEO validated per platform | We already have `reel.json`. Add a `post` block and a `seo_pack` validator |
| **Templates:** `quiz`, `data-race`, `ranked-list`, `say-this`, `tool-spotlight` | Formats with built-in mechanics (play-along, lead changes, open loop) | Port the *mechanics* as new render.py event types: `chart`, `countdown`, `quiz_options`, `strike_replace` |
| **QA gates:** whisper intelligibility match vs the script; 1080×1920/30 fps/−14±1 LUFS/peak ≤−1 dBFS; layout/contrast check; human checklist ("different from my last 5?") | Catches TTS mispronunciations and broken renders before posting | Add `qa.py`: ffprobe-free format check via PyAV, loudness, whisper roundtrip score, contact sheet |
| **Trend radar** (GitHub stars/day, HF trending) **with risk flags** (NSFW, ToS bypass, "free API keys", piracy) and **idea feed** (topic is a trend when ≥2 watched channels cover it) | Topic selection with data, plus a safety filter | `radar.py` for our niches: Wikipedia top pageviews (EN + UR), "On this day" API, GDELT, YouTube search counts, plus the same risk regex |
| **`channel_study`** with yt-dlp (competitors' transcripts, stats, hooks) | Learn hook and CTA patterns without copying clips | Same, for the history/business/psychology benchmark channels |
| **Long-form + 2 Shorts (hook & payoff)** per episode, with `sources.md`, `metadata.md` and thumbnails | Shorts funnel to monetisable long-form | Default pack for "Dead Brands" and "Paper Trail" |
| **Anti-template rules** (`MASTER_RULES`: "the last film is not a template"; `check_script.py` fails a cloned first sentence or closer) | Direct defence against the 2026 inauthentic-content policy | Add a `novelty_check` comparing the hook, closer and palette against the last 10 reels |
| **Paced publishing:** 3/day baseline, 5 cap, ≤8 pending per channel, explicit UTC timestamps, durable duplicate-receipt journal, quota reservation | Avoids spam signals and double posts | Copy the *policy* into our scheduler config |
| **Shorts custom covers via `thumbnails.set`** (opened 24 Jul 2026, YPP first; 9:16, min height 640 px), agent visually approves before set | Better packaging | Our pipeline already outputs a cover; add an approval step |
| **Static OAuth callback page on Cloudflare Pages** (strict CSP, no network, copy-paste handoff) | A stable redirect URI for Google OAuth from an ephemeral sandbox | Same pattern for our YouTube connection |
| **Own-voice mode:** record one phone file per segment; the pipeline trims, normalises and retimes | Human voice = trust + Urdu quality | Add `--voice files` to `tts_kokoro.py` (segments map to `vo/<id>.wav`) |
| **Context pack** (≤8 KB state file the agent reads first; measured ~1.1k vs ~44k tokens re-entry) | Our sessions get summarised and reset too | Add `reelkit/STATE.md`, auto-generated |

**Don't copy:**
- The repo root also contains zips of commercial WordPress plugins and a `vault/` folder. Don't download or use them.
- reels-studio's own conclusion: its optional free-LLM "producer/critic" automation was **unqualified** (factual weaknesses, rate limits). Keep the agent in the loop for facts.

---

## 7. Free tools to add (verified Oct 2026)

### 7.1 Compute & storage
| Tool | Free allowance | Use in our system | Caveat |
|---|---|---|---|
| **GitHub Actions** | Free for public repos (4 vCPU/16 GB Linux runners); private repos get a monthly minutes allowance | Cloud render farm, cron jobs (radar, posting) | A public repo exposes briefs (fine); keep secrets in encrypted Actions secrets |
| **GitHub Releases** | Large per-file limit, effectively free storage for public repos | MP4 + kit storage, capture packs | Don't store copyrighted inputs publicly |
| **Kaggle Notebooks** | ~30 GPU h/week (T4/P100) ([gputracker](https://gputracker.dev/blog/google-colab-alternatives)) | Occasional GPU jobs: Chatterbox voice, ACE-Step music, LivePortrait, Real-ESRGAN upscales | Session limits; manual-ish |
| **Colab / Lightning AI** | ~15 h/week T4 / credit pool | Backup GPU | Variable availability |
| **Cloudflare R2** | Free tier with zero egress fees | Public CDN for previews/portfolio | Check the current free GB |

### 7.2 Cloudflare free stack
| Piece | Free allowance | Use |
|---|---|---|
| **Workers + Cron Triggers** | Free plan includes cron-triggered Workers | 24/7 **trend radar** (fetch Wikipedia top pageviews, GDELT, GitHub; write a daily idea list to KV/D1); scheduler that calls the YouTube/IG APIs at the planned slot |
| **Workers AI** | **10,000 neurons/day**, no card ([itsfree.ai](https://itsfree.ai/provider/cloudflare-workers-ai/)) | **FLUX.1-schnell ≈ 43 neurons/image ≈ 230 images/day** ([bagrounds](https://bagrounds.org/ai-blog/2026-03-20-cloudflare-free-image-generation)): collage source images, thumbnails. **Whisper large-v3-turbo**: captions/ASR. Llama 3.3 70B / Qwen 3: titles, hashtag drafts. MeloTTS (no Urdu) |
| **Browser Rendering** | ~10 browser-min/day free ([nomadx](https://nomadx.ae/blog/cloudflare-ai-capabilities-complete-guide-2026/)) | Screenshots of real pages (what Lightpanda can't do); for "tested AI tools" captures |
| **Pages** | Free static hosting | OAuth callback page; public "portfolio / media kit" for sponsors and clients |
| **D1 / KV** | Free tiers | Publication journal (duplicate protection), idea backlog |

### 7.3 Free AI APIs
| Service | Free tier | Best use | Caveat |
|---|---|---|---|
| **Gemini API** | Flash/Flash-Lite/2.5 Pro text + **TTS models free**; **no free image output** ([laozhang, 8 Oct 2026](https://blog.laozhang.ai/en/posts/gemini-api-free-tier)) | **Urdu VO** (TTS lists `ur`, plus Pashto, Sindhi and Punjabi ([Firebase docs](https://firebase.google.com/docs/ai-logic/generate-speech))); script drafts; fact-check pass | Free-tier data may be used for training; limits are per project, shown in AI Studio |
| **Groq** | Free LLM + Whisper tiers | Fast ASR/LLM | Rate limits |
| **OpenRouter `:free` models** | Varies | Second-opinion critic | Unreliable; reels-studio found the critic rate-limited |
| **Uplift AI** (Pakistani Urdu TTS) | 10 min/month free ([upliftai.org](https://upliftai.org/)) | Premium-sounding Urdu for hero reels | Tiny free quota |
| **Pollinations** | Free Flux via URL, ~1 req/15 s anonymous ([apiframe](https://apiframe.ai/blog/free-ai-image-generation-api-2026)) | Backup image source | No SLA; check model licence |
| **Edge-TTS** (has `ur-PK` voices) | Free, unofficial | Drafts only | Unofficial service, not for commercial channels ([freeapihub](https://freeapihub.com/blog/best-free-text-to-speech-apis)) |

### 7.4 Free media & data sources
| Source | Licence | Use |
|---|---|---|
| NASA Image & Video Library | Mostly public domain | Space/science reels |
| Wikimedia Commons API / Openverse API | Per-file CC/PD; check each | Historical textures, maps, portraits (PD) |
| Library of Congress, Internet Archive | Many PD items | Old newspapers, ads → "Paper Trail" collage |
| Pexels / Pixabay API | Free commercial, no indemnity; Pexels API wants attribution | Occasional B-roll |
| Freesound API | CC0/CC-BY per sound | SFX (credit CC-BY) |
| World Bank API, Our World in Data | CC BY 4.0 | Data stories |
| Cricsheet | ODC-BY | Cricket stats |
| Wikidata SPARQL | CC0 | "On this day", birthdays, record facts |
| **Wikipedia Pageviews API** (top articles per day/language) | Free, official | **Trend signal**: what people are curious about today, including `ur.wikipedia` |
| GDELT | Free | News-trend pegs |

### 7.5 Publishing
| Route | Free limits | Notes |
|---|---|---|
| **YouTube Data API** | `videos.insert` now has its **own bucket: 100 uploads/day/project** (1 unit each); other calls share 10k units ([upload-post](https://www.upload-post.com/youtube-api/); also noted in yt-tts `tools/youtube/README`) | Unaudited projects upload **private-only**. Apply for an audit or publish manually from Studio |
| **Instagram Content Publishing API** | **100 API posts / rolling 24 h** (Reels + feed + stories) ([blckalpaca](https://blckalpaca.at/en/knowledge-base/social-media/social-media-platforms-compared/social-media-apis-access-limits-costs)) | Needs a Business/Creator account linked to a FB Page |
| **TikTok Content Posting API** | Unaudited apps can post **SELF_ONLY** (private) for 5 users/day ([postzen](https://www.postzen.dev/blog/tiktok-api)) | TikTok = reach only for PK; post manually or use "upload to inbox" drafts |
| **Buffer free API** | 100 req/15 min, 250/day; ~10 pending per channel on Free | Simplest: one key for YT Shorts + IG + FB (used live by yt-tts) |
| **Postiz** (AGPL, ~30k★) | Free self-host | 20+ networks + MCP server, but needs a server (not our sandbox) |

### 7.6 Render engines & repos worth knowing
| Tool | Status here | Verdict |
|---|---|---|
| **HyperFrames** (Apache-2.0, HTML/GSAP → MP4) | **Now feasible:** the Node 22 tarball (`node-v22.23.3-linux-x64`) can be downloaded into `~/.cache` with no root needed. reels-studio rendered with it on this same 2 vCPU/2 GB box (~7–8 s render per video second) | Best route for **charts, quizzes, rankings, UI mock-ups**, where reelkit is weakest. Keep reelkit for collage/character reels |
| Remotion | Free for individuals and teams ≤3 people | An alternative to HyperFrames; the licence matters at company scale |
| `gyoridavid/short-video-maker` (MIT, 1.4k★) | Kokoro + whisper + Pexels + Remotion; MCP/REST | Shows the n8n/MCP automation pattern; its stock-footage output is the templated style to avoid |
| `MoneyPrinterTurbo` (MIT, ~129k★) | Keyword → stock-footage short | **Avoid as a style**: exactly what the 2026 rules target. Useful only as a reference for its TTS-provider abstraction |

---

## 8. Proposed free architecture

```
 ┌───────── Cloudflare (free) ─────────┐        ┌──────── This agent (Arena) ────────┐
 │ Cron Worker: 06:00 PKT daily        │        │ research + fact-check (web)        │
 │  ├ Wikipedia top views (en, ur)     │  ideas │ write reel.json (brief)            │
 │  ├ "On this day" + GDELT + GitHub   ├───────►│ generate_image collage / FLUX (CF) │
 │  └ risk-flag filter → D1 backlog    │        │ Kokoro EN | Gemini TTS UR | own VO │
 │ Workers AI: FLUX images, Whisper    │        │ render.py + audio.py (draft)       │
 │ Pages: OAuth callback, portfolio    │        │ qa.py gates → approve              │
 └─────────────────────────────────────┘        └───────────────┬────────────────────┘
                                                                │ git push brief
                                        ┌───────────────────────▼────────────────────┐
                                        │ GitHub (free)                              │
                                        │  Actions: render matrix ×5 (4 vCPU/16 GB)  │
                                        │  Releases: final.mp4 + cover + post kit    │
                                        │  Actions cron: publish queue → YT API /    │
                                        │  IG Graph / Buffer; journal (no dupes)     │
                                        └────────────────────────────────────────────┘
```

---

## 9. Integration roadmap (suggested order)

| Step | Work | Effort | Unlocks |
|---|---|---|---|
| 1 | `qa.py` (format, loudness, whisper roundtrip, contact sheet) + `novelty_check` | ~2 h | Policy-safe quality at volume |
| 2 | `chart` + `countdown` + `quiz_options` event types in render.py | ~1 day | Data stories, cricket, quizzes, rankings |
| 3 | Gemini TTS adapter (`tts_gemini.py`, Urdu) + own-voice `--voice files` mode | ~2 h (needs your free API key) | Kalaam, Spoken English, Urdu folk tales |
| 4 | GitHub repo + `publish.py` (Releases) + `render.yml` | ~3 h (needs a GitHub token) | Unlimited storage, 5× parallel cloud renders |
| 5 | Cloudflare Worker radar (cron) + Workers AI FLUX helper | ~3 h (needs a CF account ID + token) | A daily idea list; free extra images |
| 6 | YouTube/IG publishing (or Buffer) + scheduler policy | ~4 h (needs OAuth) | Hands-off posting at 3/day |
| 7 | Optional: HyperFrames via Node 22 for data/quiz templates | ~2 h setup | Pro motion-graphics formats |

**Credentials only you can create:**
- a GitHub fine-grained token;
- a Cloudflare account ID + API token;
- a Gemini API key (AI Studio);
- a Google OAuth client (YouTube);
- a Meta app (Instagram).

Never paste them into public files. Store them under `~/.config/` (outside snapshots that are shared).

---

## 10. Honest limits
- No niche "guarantees" virality. Most uploads underperform. Judge each format against your channel median after 48–72 h. Keep a format when 3 of 5 beat the median; drop it after 5–8 misses.
- RPM tables come from creator-tool blogs with wide ranges. Your real RPM depends on audience country.
- Free tiers change often. Re-verify Gemini, Cloudflare and API quotas before building on them.
- Urdu TTS quality (Gemini/Uplift) is untested *here*. Run a whisper roundtrip and a native-listener check first.

## Sources (main)
yt-tts / reels-studio (README, PIPELINE, research/VIRAL-SYSTEM-REPORT.md, research/ai-tools-niche.md, finance/MASTER_RULES.md, tools/youtube/README.md, tools/post/README.md, .github/workflows/render.yml) · youtubeniches.com · fableclip.com · clipspeed.ai · virvid.ai · mediacube.io · vidiq.com · flowshorts.app · taletok.io · fluxnote.io · ytmoneycalculator.com · noobclaw.com · ytgrowth.io · aituber.app · layer3labs.io · itsfree.ai · bagrounds.org · nomadx.ae · blog.laozhang.ai · firebase.google.com · upliftai.org · freeapihub.com · apiframe.ai · gputracker.dev · upload-post.com · blckalpaca.at · postzen.dev · github.com/gyoridavid/short-video-maker · github.com/harry0703/MoneyPrinterTurbo · speakrj.com · youtubers.me
