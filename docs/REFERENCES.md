# Reference repos (studied 2026-10-11; not vendored, to avoid redistributing third-party docs)

| Repo | License | What we took |
|---|---|---|
| [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) (npm `hyperframes@0.8.137`) | Apache 2.0 | The editor and renderer. Rules: one paused GSAP timeline on `window.__timelines`; `immediateRender:false` on fromTo; deterministic, no `Math.random` / `Date.now`; local GSAP and fonts |
| [zainkhan122/yt-tts · reels-studio](https://github.com/zainkhan122/yt-tts/tree/main/reels-studio) | owner's | Cloud render on Actions (one runner per brief), outputs to Releases, toolchain cache, RESUME / CURRENT_STATE handoff |
| [Alisa0808/vox-director](https://github.com/Alisa0808/vox-director) | MIT | Beat map discipline: hook ≤ 3 s, a cut every 3–5 s, loop-closing ending |
| [hypit-ai/hypit](https://github.com/hypit-ai/hypit) | modified Apache | Craft playbooks (b-roll, captions, sound mix, video direction) |
| [lightpanda-io/browser](https://github.com/lightpanda-io/browser) | AGPL-3.0 (used as a tool only) | Fast research scraping. **Not a renderer:** `--dump png` is text-only |
