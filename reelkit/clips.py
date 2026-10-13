#!/usr/bin/env python3
"""Motion clips for episodes: compose (5-slot prompt) → lint → generate via cache (free) → store → prep for HyperFrames.

  python3 reelkit/clips.py compose <ep_dir> [--check]                  write prompt = compose(shot) for templated clips
  python3 reelkit/clips.py lint    <ep_dir> [--json out.json]          prompt/template/seed rules (also run by planlint)
  python3 reelkit/clips.py status  <ep_dir>                            per clip: in media / cached / key drift / runs needed
  python3 reelkit/clips.py gen     <ep_dir> [--only ID ...] [--force] [--cache-only] [--dry-run]
                                                                       raw clips -> <ep>/clips/<id>.mp4 (cache first, GPU last)
  python3 reelkit/clips.py adopt   <ep_dir> [--only ID ...]            register clips generated before the cache existed
  python3 reelkit/clips.py prep    <ep_dir> <hf_dir>                   graded/upscaled -> <hf>/assets/clips/<id>.mp4
  python3 reelkit/clips.py one     <image> "<prompt>" <out.mp4> [--engine wan|ltx] [--seconds 5] [--seed 7]

<ep>/clips.json:
{"template": {"style": "<series style lock, positive phrasing>", "avoid": ["photorealistic", "3D render", ...]},
 "clips": [
  {"id": "s06_phone", "engine": "wan", "image": "assets/s06_phone.jpg", "scene": "s06", "seconds": 5, "seed": 3,
   "shot": {"subject": "...", "motion": ["first beat", "second beat", "..."], "scene": "...", "spatial": "...",
            "camera": "...", "style": "(optional extra)", "avoid": ["(optional extra negatives)"]},
   "prompt": "<written by `compose` — never edit by hand>"},
  {"id": "arch_minuteman", "engine": "url", "url": "https://upload.wikimedia.org/...webm", "in": 13.5, "out": 19.5, ...}
 ]}
Wan 5-slot template (OpenMontage lesson B7): subject · motion as ordered steps · scene · spatial layout · ONE camera
move · style lock. 200–400 words, positive phrasing, no on-screen-text words (overlays are added in HyperFrames, never
generated). The Space runs a distilled model at guidance 1, where negative prompts barely act — so the style is locked
in the positive prompt and `avoid` is sent as negative_prompt as a cheap extra. Clips without `shot` are legacy
(generated before the template) and stay frozen: changing their prompt would orphan the cached/generated file.

Engines (all free, tested 2026-10-11, see docs/VIDEO_SOURCES.md):
  wan  zerogpu-aoti/wan2-2-fp8da-aoti-faster  Wan 2.2 14B i2v (Apache-2.0) · 480x832 16 fps ≤5 s · ~40 s/clip · keeps art style
  ltx  Lightricks/ltx-video-distilled         LTX-Video i2v · up to 704x1216 30 fps · ~20 s/clip · drifts toward photoreal
  url  any public-domain/CC0 footage URL (Wikimedia Commons, Internet Archive, NASA) trimmed in→out
Every call goes through reelkit/clipcache.py (key = exact call incl. seed + input-image sha256), so a clip is generated
once, ever. Raw clips are inputs (tracked by media.json + the media release). Prepped clips live only in the build dir.
Optional HF_TOKEN env raises the ZeroGPU quota (~3 anonymous runs/day).
"""
import argparse, hashlib, json, os, re, shutil, subprocess, sys, tempfile, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import clipcache  # noqa: E402

FF = "/usr/bin/ffmpeg" if os.path.exists("/usr/bin/ffmpeg") else (shutil.which("ffmpeg") or "ffmpeg")
FP = "/usr/bin/ffprobe" if os.path.exists("/usr/bin/ffprobe") else (shutil.which("ffprobe") or "ffprobe")
SPACES = {"wan": "zerogpu-aoti/wan2-2-fp8da-aoti-faster", "ltx": "Lightricks/ltx-video-distilled"}
NEG_LTX = "worst quality, inconsistent motion, blurry, jittery, distorted, new objects, text, photorealistic"
URL_ENCODE = "libx264 veryfast crf16 yuv420p -an"   # part of the cache key for trimmed footage; change => re-trim
SLOTS = ("subject", "motion", "scene", "spatial", "camera")
OVERLAY = re.compile(r"\b(text|texts|caption|captions|title|titles|subtitle|subtitles|logo|logos|label|labels|watermark|watermarks|lettering|typography|words?)\b", re.I)
NEGATION = re.compile(r"\b(no|not|never|without|don't|doesn't|nothing)\b", re.I)
CAMERA = {"translation": r"\b(pan|pans|panning|truck|trucks|dolly|dollies|track|tracks|tracking|crane|cranes|pedestal|push(?:es)?[- ]in|pull(?:s)?[- ](?:back|out)|slides?|drifts? (?:left|right|up|down|forward|back))\b",
          "rotation": r"\b(tilt|tilts|tilting|roll|rolls|orbit|orbits|orbiting|rotat\w*|arc|arcs)\b",
          "zoom": r"\b(zoom|zooms|zooming)\b"}
WORDS = {"wan": (200, 400), "ltx": (0, 80)}


def words(t): return len(re.findall(r"[A-Za-z0-9'’-]+", t or ""))


def compose(shot, tpl=None):
    """5-slot template -> one paragraph. Deterministic: same slots => byte-identical prompt (=> same cache key)."""
    tpl = tpl or {}
    steps = [m.strip().rstrip(".") for m in shot["motion"]]
    seq = []
    for i, m in enumerate(steps):
        lead = "First, " if i == 0 else ("Finally, " if i == len(steps) - 1 and len(steps) > 2 else "Then ")
        seq.append(lead + m[0].lower() + m[1:] + ".")
    style = " ".join(x.strip() for x in (shot.get("style"), tpl.get("style")) if x)
    parts = [shot["subject"].strip().rstrip(".") + ".", " ".join(seq), shot["scene"].strip().rstrip(".") + ".",
             shot["spatial"].strip().rstrip(".") + ".", "Camera: " + shot["camera"].strip().rstrip(".") + ".", style]
    return re.sub(r"\s+", " ", " ".join(p for p in parts if p)).strip()


def negative(c, tpl=None):
    sh = c.get("shot")
    if not sh: return None                                     # legacy clip: Space default negative (part of its key)
    av = list((tpl or {}).get("avoid", [])) + [a for a in sh.get("avoid", []) if a not in (tpl or {}).get("avoid", [])]
    return ", ".join(av) or None


def input_sha(ep, rel):
    p = ep / rel
    if p.exists(): return clipcache.sha256_file(p)
    m = ep / "media.json"                                      # CI / fresh clone: trust the manifest sha of the plate
    e = json.loads(m.read_text()).get("files", {}).get(rel, {}) if m.exists() else {}
    if e.get("sha256"): return e["sha256"]
    raise FileNotFoundError(f"{rel}: not on disk and no sha256 in media.json (run media.py pull)")


def call_spec(c, ep, tpl=None):
    """The exact generator call as a JSON dict. The cache key is sha256(call_spec) and gen sends exactly this."""
    if tpl is None:
        cf = ep / "clips.json"; tpl = json.loads(cf.read_text()).get("template", {}) if cf.exists() else {}
    e = c["engine"]
    if e == "url":
        return {"engine": "url", "url": c["url"], "in": c["in"], "out": c["out"], "encode": URL_ENCODE}
    if "seed" not in c: raise ValueError(f"{c['id']}: AI clips must pin a seed (cacheable + reproducible)")
    if e == "wan":
        return {"engine": "wan", "space": SPACES["wan"], "api": "/generate_video", "seed": int(c["seed"]), "prompt": c["prompt"],
                "input_sha256": input_sha(ep, c["image"]),
                "params": {"steps": int(c.get("steps", 6)), "duration_seconds": min(float(c.get("seconds", 5)), 5.0),
                           "guidance_scale": 1, "guidance_scale_2": 1, "negative_prompt": negative(c, tpl)}}
    if e == "ltx":
        return {"engine": "ltx", "space": SPACES["ltx"], "api": "/image_to_video", "seed": int(c["seed"]), "prompt": c["prompt"],
                "input_sha256": input_sha(ep, c["image"]),
                "params": {"negative_prompt": negative(c, tpl) or NEG_LTX, "height_ui": 1216, "width_ui": 704, "mode": "image-to-video",
                           "duration_ui": min(float(c.get("seconds", 5)), 8), "ui_frames_to_use": 9, "ui_guidance_scale": 1, "improve_texture_flag": True}}
    raise ValueError(f"{c['id']}: unknown engine {e}")


def lint_clip(c, tpl, generated):
    """-> list of (level, msg). level in FAIL/WARN/INFO."""
    out, cid, e = [], c.get("id", "?"), c.get("engine")
    if e not in ("wan", "ltx", "url"): return [("FAIL", f"{cid}: unknown engine {e!r}")]
    if e == "url":
        for k in ("url", "in", "out"):
            if k not in c: out.append(("FAIL", f"{cid}: url clip needs '{k}'"))
        if "in" in c and "out" in c and not float(c["out"]) > float(c["in"]): out.append(("FAIL", f"{cid}: out must be > in"))
        return out
    if "seed" not in c: out.append(("FAIL", f"{cid}: no seed — unpinned calls can't be cached or reproduced"))
    if not c.get("image"): out.append(("FAIL", f"{cid}: no input image"))
    sh = c.get("shot")
    if not sh:
        if generated: out.append(("INFO", f"{cid}: legacy prompt (generated before the 5-slot template) — frozen"))
        elif e == "wan": out.append(("FAIL", f"{cid}: pending Wan clip without `shot` slots — write the 5-slot template, then `clips.py compose`"))
        if e == "ltx" and words(c.get("prompt")) > WORDS["ltx"][1]: out.append(("WARN", f"{cid}: ltx prompt {words(c.get('prompt'))} words > 80"))
        return out
    miss = [k for k in SLOTS if not sh.get(k)]
    if miss: return out + [("FAIL", f"{cid}: shot slots missing: {', '.join(miss)}")]
    if not isinstance(sh["motion"], list) or len(sh["motion"]) < 2:
        out.append(("FAIL", f"{cid}: motion must be ≥2 ordered steps (a single verb produces a frozen frame or a morph)"))
        return out
    style = " ".join(x for x in (sh.get("style"), tpl.get("style")) if x)
    if not style: out.append(("FAIL", f"{cid}: no style lock (template.style or shot.style)"))
    positive = {k: (" ".join(sh[k]) if k == "motion" else sh[k]) for k in SLOTS}; positive["style"] = style
    for k, v in positive.items():
        hit = sorted({m.group(0).lower() for m in OVERLAY.finditer(v)})
        if hit: out.append(("FAIL", f"{cid}: on-screen-text word(s) {hit} in {k} — overlays belong in HyperFrames, Wan renders them as garbage glyphs"))
        neg = sorted({m.group(0).lower() for m in NEGATION.finditer(v)})
        if neg: out.append(("WARN", f"{cid}: negation {neg} in {k} — diffusion models read 'no X' as X; phrase it positively or move it to avoid"))
    moves = [k for k, rx in CAMERA.items() if re.search(rx, sh["camera"], re.I)]
    if len(moves) > 1: out.append(("FAIL", f"{cid}: camera combines {' + '.join(moves)} — use ONE move (or static)"))
    lo, hi = WORDS.get(e, (0, 10 ** 6)); n = words(compose(sh, tpl))
    if not lo <= n <= hi: out.append(("FAIL", f"{cid}: composed prompt {n} words, want {lo}–{hi}"))
    if c.get("prompt") != compose(sh, tpl):
        out.append(("FAIL", f"{cid}: prompt != compose(shot) — run `clips.py compose` (the stored prompt is what gets generated and keyed)"))
    if generated and c.get("prompt") == compose(sh, tpl): out.append(("INFO", f"{cid}: templated, generated"))
    return out


def generated_ids(ep):
    m = ep / "media.json"
    files = json.loads(m.read_text()).get("files", {}) if m.exists() else {}
    return {Path(k).stem for k in files if k.startswith("clips/")} | {p.stem for p in (ep / "clips").glob("*.mp4")}


def lint_episode(ep):
    cf = ep / "clips.json"
    if not cf.exists(): return []
    d = json.loads(cf.read_text()); tpl = d.get("template", {}); gen = generated_ids(ep); res = []
    ids = [c.get("id") for c in d["clips"]]
    for dup in sorted({i for i in ids if ids.count(i) > 1}): res.append(("FAIL", f"duplicate clip id {dup}"))
    for c in d["clips"]: res += lint_clip(c, tpl, c.get("id") in gen)
    return res


def probe(p):
    r = json.loads(subprocess.run([FP, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate,nb_frames:format=duration",
                                   "-of", "json", str(p)], capture_output=True, text=True).stdout)
    s = r["streams"][0]; n, d = s["r_frame_rate"].split("/")
    return {"w": s["width"], "h": s["height"], "fps": float(n) / float(d), "dur": float(r["format"]["duration"])}


def gen_ai(spec, image, out, retries=3):
    """Run exactly `spec` (from call_spec) against its Space. Returns True on success."""
    from gradio_client import Client, handle_file
    kw = {"hf_token": os.environ["HF_TOKEN"]} if os.environ.get("HF_TOKEN") else {}
    P = {k: v for k, v in spec["params"].items() if v is not None}       # None => leave the Space default
    for attempt in range(retries):
        try:
            t = time.time(); cl = Client(spec["space"], verbose=False, **kw)
            if spec["engine"] == "wan":
                res = cl.predict(input_image=handle_file(str(image)), prompt=spec["prompt"], seed=spec["seed"], randomize_seed=False, api_name=spec["api"], **P)
            else:
                res = cl.predict(prompt=spec["prompt"], input_image_filepath=handle_file(str(image)), input_video_filepath=None,
                                 seed_ui=spec["seed"], randomize_seed=False, api_name=spec["api"], **P)
            v = res[0]["video"] if isinstance(res[0], dict) else res[0]
            Path(out).parent.mkdir(parents=True, exist_ok=True); shutil.copy(v, out)
            print(f"  ✓ {Path(out).name} via {spec['engine']} in {time.time() - t:.0f}s  {probe(out)}"); return True
        except Exception as e:
            msg = str(e)[:200]; print(f"  ! {spec['engine']} attempt {attempt + 1}: {msg}")
            if "quota" in msg.lower() or "exceeded" in msg.lower():
                print("    ZeroGPU quota hit — set HF_TOKEN (free account) or retry later"); return "quota"
            time.sleep(15 * (attempt + 1))
    return False


def space_sha(space):
    try:
        import urllib.request
        with urllib.request.urlopen(f"https://huggingface.co/api/spaces/{space}", timeout=20) as r: return json.load(r).get("sha")
    except Exception: return None


def gen_url(url, t_in, t_out, out):
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    import hashlib, urllib.request
    dl = Path.home() / ".cache/tmp/dl" / (hashlib.sha1(url.encode()).hexdigest()[:12] + Path(url.split("?")[0]).suffix)
    if not dl.exists():
        dl.parent.mkdir(parents=True, exist_ok=True)
        rq = urllib.request.Request(url, headers={"User-Agent": "HistoryShortsResearch/1.0 (github.com/zainkhan122/History)"})
        with urllib.request.urlopen(rq, timeout=120) as r, open(dl, "wb") as o: shutil.copyfileobj(r, o)
    subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", "-ss", str(t_in), "-to", str(t_out), "-i", str(dl),
                    "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", str(out)], check=True)
    print(f"  ✓ {Path(out).name} from archive {t_in}-{t_out}s  {probe(out)}")
    return True


def scene_durations(ep):
    tl = ep / "timeline.json"
    return {s["id"]: (s["start"], s["end"]) for s in json.load(open(tl))["scenes"]} if tl.exists() else {}


def target_dur(c, scenes):
    if "dur" in c: return float(c["dur"])
    if c.get("scene") in scenes: a, b = scenes[c["scene"]]; return round(b - a + 0.8, 3)   # starts 0.35 s early under the wipe, +tail for the outgoing one
    return None


def prep_one(c, src, dst, dur):
    W, H = c.get("fit", [1296, 2322]); P = probe(src)
    vf = []
    if c.get("engine") in ("wan", "ltx"):
        slow = 1.0 if not dur else min(max(dur / P["dur"], 1.0), float(c.get("max_slow", 1.8)))
        if slow > 1.001: vf.append(f"setpts={slow:.4f}*PTS")
        # motion-compensated interpolation to 30 fps at native res (cheap), then upscale
        vf.append("minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1")
    else:
        vf.append("fps=30")
    vf += [f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos", f"crop={W}:{H}", "unsharp=5:5:0.45:5:5:0.0"]
    g = c.get("grade", "none")
    if g == "film":       # archival look: mono, lifted blacks, warm paper tint, moving grain, gentle vignette
        vf += ["hue=s=0", "eq=" + c.get("eq", "contrast=1.22:brightness=0.015:gamma=0.92"), "colorchannelmixer=.95:.05:0:0:.05:.90:.05:0:0:.10:.78",
               "noise=alls=16:allf=t+u", "vignette=PI/4.5"]
    elif g == "warm":
        vf += ["eq=saturation=0.92:contrast=1.04", "colorbalance=rm=0.04:bm=-0.04"]
    if dur: vf.append(f"tpad=stop_mode=clone:stop_duration={max(0.0, dur):.3f}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    cmd = [FF, "-hide_banner", "-loglevel", "error", "-y", "-i", str(src), "-vf", ",".join(vf), "-an", "-r", "30"]
    if dur: cmd += ["-t", f"{dur:.3f}"]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-g", "15", "-threads", "2", "-movflags", "+faststart", str(dst)]
    subprocess.run(cmd, check=True)
    print(f"  ✓ prep {dst.name}  {probe(dst)}")


def _write_json(p, d):
    fd, tmp = tempfile.mkstemp(dir=p.parent, suffix=".tmp"); os.close(fd)
    Path(tmp).write_text(json.dumps(d, indent=1, ensure_ascii=False if p.name == "clips.json" else True, sort_keys=p.name == "media.json") + "\n")
    os.replace(tmp, p)


def record_provenance(ep, c, key, spec, path, how):
    """Keep media.json honest about where the raw clip came from (media.py push preserves these keys)."""
    mp = ep / "media.json"; man = json.loads(mp.read_text()) if mp.exists() else {"files": {}}
    rel = f"clips/{c['id']}.mp4"; e = man.setdefault("files", {}).setdefault(rel, {})
    e.update({"cache_key": key, "spec": f"clips.json#{c['id']}", "sha256": clipcache.sha256_file(path), "size": Path(path).stat().st_size})
    if c["engine"] != "url":
        e.update({"ai": True, "kind": "clip", "licence": "own-ai", "realistic": bool(c.get("realistic", False)), "derived_from": c["image"],
                  "op": "image-to-video, style preserved", "seed": spec["seed"], "prompt_sha1": hashlib.sha1(c["prompt"].encode()).hexdigest(),
                  "provider": {"wan": "Wan 2.2 image-to-video (Apache-2.0 weights) via HF Space " + SPACES["wan"],
                               "ltx": "LTX-Video image-to-video via HF Space " + SPACES["ltx"]}[c["engine"]]})
        if how == "generated" or "source" not in e: e["source"] = f"generated {time.strftime('%Y-%m-%d')} from {c['image']}"
    _write_json(mp, man)


def main():
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="cmd", required=True)
    g = sp.add_parser("gen"); g.add_argument("ep"); g.add_argument("--only", nargs="*"); g.add_argument("--force", action="store_true")
    g.add_argument("--cache-only", action="store_true", help="never spend GPU: fail if a clip isn't cached"); g.add_argument("--dry-run", action="store_true")
    ad = sp.add_parser("adopt"); ad.add_argument("ep"); ad.add_argument("--only", nargs="*")
    cp = sp.add_parser("compose"); cp.add_argument("ep"); cp.add_argument("--check", action="store_true")
    li = sp.add_parser("lint"); li.add_argument("ep"); li.add_argument("--json")
    st = sp.add_parser("status"); st.add_argument("ep")
    p = sp.add_parser("prep"); p.add_argument("ep"); p.add_argument("hf")
    o = sp.add_parser("one"); o.add_argument("image"); o.add_argument("prompt"); o.add_argument("out")
    o.add_argument("--engine", default="wan"); o.add_argument("--seconds", type=float, default=5.0); o.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    if a.cmd == "one":                                  # ad-hoc experiments: uncached on purpose
        c = {"id": "one", "engine": a.engine, "image": str(Path(a.image).resolve()), "seconds": a.seconds, "seed": a.seed, "prompt": a.prompt}
        sys.exit(0 if gen_ai(call_spec(c, Path("/"), {}), a.image, a.out) else 1)
    ep = Path(a.ep).resolve(); cf = ep / "clips.json"; doc = json.loads(cf.read_text())
    cfg, tpl = doc["clips"], doc.get("template", {})

    if a.cmd == "compose":
        changed = []
        for c in cfg:
            if c.get("shot") and c.get("prompt") != compose(c["shot"], tpl): changed.append(c["id"]); c["prompt"] = compose(c["shot"], tpl)
        for c in cfg:
            if c.get("shot"): print(f"  {c['id']:16} {words(c['prompt'])} words{'  (updated)' if c['id'] in changed else ''}")
        if a.check: sys.exit(1 if changed else 0)
        if changed: _write_json(cf, doc)
        return

    if a.cmd == "lint":
        res = lint_episode(ep)
        for lv, m in res: print(f"{lv:4} {m}")
        F = sum(lv == "FAIL" for lv, _ in res); W = sum(lv == "WARN" for lv, _ in res)
        print(f"clips lint: FAIL {F}, WARN {W}")
        if a.json: Path(a.json).write_text(json.dumps([{"level": lv, "msg": m} for lv, m in res], indent=1, ensure_ascii=False))
        sys.exit(1 if F else 0)

    man = json.loads((ep / "media.json").read_text()).get("files", {}) if (ep / "media.json").exists() else {}
    cache = clipcache.load()

    if a.cmd == "status":
        need = 0
        print(f"  {'clip':16} {'engine':6} {'media':6} {'cache':6} key")
        for c in cfg:
            try: key = clipcache.make_key(call_spec(c, ep, tpl)); kerr = ""
            except (ValueError, FileNotFoundError) as x: key, kerr = None, str(x)
            ent = man.get(f"clips/{c['id']}.mp4", {})
            inm = "yes" if ent else "-"
            inc = ("L" if key and clipcache._blob(key).exists() else "") + ("R" if key in cache and cache[key].get("remote") else "")
            inc = inc or ("idx" if key in cache else "-")
            if kerr: note = "ERR " + kerr
            elif ent.get("cache_key") and ent["cache_key"] != key: note = "DRIFT: spec changed since this clip was made (regenerate or revert)"
            elif key in cache: note = key[:12]
            else: note = key[:12] + ("  needs adopt" if ent else "  NEEDS GPU RUN" if c["engine"] != "url" else "  needs trim (free)")
            need += (not kerr) and key not in cache and not ent and c["engine"] != "url"
            print(f"  {c['id']:16} {c['engine']:6} {inm:6} {inc:6} {note}")
        print(f"GPU runs needed: {need}  (anonymous ZeroGPU ≈ 3/day; HF_TOKEN raises it)"); return

    if a.cmd == "adopt":
        n = 0
        for c in cfg:
            if a.only and c["id"] not in a.only: continue
            f = ep / "clips" / f"{c['id']}.mp4"; ent = man.get(f"clips/{c['id']}.mp4", {})
            if not f.exists():
                print(f"  - {c['id']}: " + ("file missing — `media.py pull` first" if ent else "never generated — nothing to adopt")); continue
            if ent.get("sha256") and clipcache.sha256_file(f) != ent["sha256"]: print(f"  ! {c['id']}: file differs from media.json sha — refusing"); continue
            if c["engine"] != "url" and ent.get("prompt_sha1") != hashlib.sha1(c["prompt"].encode()).hexdigest():
                print(f"  ! {c['id']}: clips.json prompt is not the one this file was generated from — refusing"); continue
            spec = call_spec(c, ep, tpl); key = clipcache.make_key(spec)
            if key not in cache:
                clipcache.put(key, f, spec, {"label": f"{ep.name}/{c['id']}", "adopted": True, **probe(f), "space_sha": None}); n += 1
            record_provenance(ep, c, key, spec, f, "adopted"); print(f"  ✓ {c['id']} -> {key[:12]}")
        print(f"adopted {n}"); return

    if a.cmd == "gen":
        bad = runs = 0; quota = False
        for c in cfg:
            if a.only and c["id"] not in a.only: continue
            out = ep / "clips" / f"{c['id']}.mp4"
            if out.exists() and not a.force: print(f"  = {out.name} exists"); continue
            fails = [m for lv, m in lint_clip(c, tpl, False) if lv == "FAIL" and "legacy" not in m and "pending Wan clip" not in m]
            if c["engine"] == "wan" and not c.get("shot") and c["id"] not in generated_ids(ep):
                fails.append(f"{c['id']}: pending Wan clip without `shot` slots")
            if fails: print("  ✗ " + "\n  ✗ ".join(fails)); bad += 1; continue
            spec = call_spec(c, ep, tpl); key = clipcache.make_key(spec)
            hit = None if a.dry_run else clipcache.get(key, out)
            if hit:
                print(f"  ⚡ {out.name} from cache ({hit}) {key[:12]}"); record_provenance(ep, c, key, spec, out, "cache"); continue
            if a.dry_run: print(f"  ? {out.name} key {key[:12]} {'cached' if key in cache else 'would ' + ('trim' if c['engine'] == 'url' else 'spend 1 GPU run')}"); continue
            if a.cache_only and c["engine"] != "url": print(f"  ✗ {out.name}: not cached and --cache-only"); bad += 1; continue
            tmp = Path(tempfile.mkdtemp(dir=os.environ.get("TMPDIR"))) / out.name
            if quota and c["engine"] != "url": print(f"  - {out.name}: skipped (quota exhausted this run)"); bad += 1; continue
            ok = gen_url(c["url"], c["in"], c["out"], tmp) if c["engine"] == "url" else gen_ai(spec, ep / c["image"], tmp)
            if ok == "quota": quota, ok = True, False
            runs += c["engine"] != "url" and ok
            if ok:
                P = probe(tmp)
                if P["dur"] < 0.5 or P["w"] < 64: print(f"  ✗ {out.name}: implausible output {P} — not cached"); bad += 1; continue
                clipcache.put(key, tmp, spec, {"label": f"{ep.name}/{c['id']}", **P,
                                               "space_sha": space_sha(spec["space"]) if "space" in spec else None})
                out.parent.mkdir(parents=True, exist_ok=True); os.replace(tmp, out)
                record_provenance(ep, c, key, spec, out, "generated")
            bad += not ok
        print(f"gen: {runs} GPU run(s) spent, {bad} failure(s)")
        sys.exit(1 if bad else 0)

    scenes = scene_durations(ep); hf = Path(a.hf)
    for c in cfg:
        src = ep / "clips" / f"{c['id']}.mp4"
        if not src.exists(): print(f"  ! missing {src.name} — run `clips.py gen` (cache first) or `media.py pull`"); continue
        prep_one(c, src, hf / "assets" / "clips" / f"{c['id']}.mp4", target_dur(c, scenes))


if __name__ == "__main__":
    main()
