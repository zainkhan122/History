#!/usr/bin/env python3
"""Motion clips for episodes: generate (free) → store (media release) → prep for HyperFrames.

  python3 reelkit/clips.py gen  <ep_dir> [--only ID ...] [--force]   raw clips -> <ep>/clips/<id>.mp4
  python3 reelkit/clips.py prep <ep_dir> <hf_dir>                    graded/upscaled -> <hf>/assets/clips/<id>.mp4
  python3 reelkit/clips.py one  <image> "<prompt>" <out.mp4> [--engine wan|ltx] [--seconds 5]

<ep>/clips.json:
{"clips": [
  {"id": "s03_console", "engine": "wan", "image": "assets/s03_console.jpg", "seconds": 5, "seed": 7,
   "prompt": "...", "scene": "s03", "fit": [1296, 2322], "max_slow": 1.8},
  {"id": "arch_minuteman", "engine": "url", "url": "https://upload.wikimedia.org/...webm", "in": 13.5, "out": 19.5,
   "fit": [1000, 562], "grade": "film", "credit": "USAF / SLD 30 PA (public domain)", "dur": 2.7}
]}
Engines (all free, tested 2026-10-11, see docs/VIDEO_SOURCES.md):
  wan  zerogpu-aoti/wan2-2-fp8da-aoti-faster  Wan 2.2 14B i2v (Apache-2.0) · 480x832 16 fps ≤5 s · ~40 s/clip · keeps art style
  ltx  Lightricks/ltx-video-distilled         LTX-Video i2v · up to 704x1216 30 fps · ~20 s/clip · drifts toward photoreal
  url  any public-domain/CC0 footage URL (Wikimedia Commons, Internet Archive, NASA) trimmed in→out
Raw clips are inputs (tracked by media.json, pushed to the media release). Prepped clips live only in the build dir.
Optional HF_TOKEN env raises the ZeroGPU quota.
"""
import argparse, json, os, shutil, subprocess, sys, time
from pathlib import Path

FF = "/usr/bin/ffmpeg" if os.path.exists("/usr/bin/ffmpeg") else (shutil.which("ffmpeg") or "ffmpeg")
FP = "/usr/bin/ffprobe" if os.path.exists("/usr/bin/ffprobe") else (shutil.which("ffprobe") or "ffprobe")
SPACES = {"wan": "zerogpu-aoti/wan2-2-fp8da-aoti-faster", "ltx": "Lightricks/ltx-video-distilled"}
NEG_LTX = "worst quality, inconsistent motion, blurry, jittery, distorted, new objects, text, photorealistic"


def probe(p):
    r = json.loads(subprocess.run([FP, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate,nb_frames:format=duration",
                                   "-of", "json", str(p)], capture_output=True, text=True).stdout)
    s = r["streams"][0]; n, d = s["r_frame_rate"].split("/")
    return {"w": s["width"], "h": s["height"], "fps": float(n) / float(d), "dur": float(r["format"]["duration"])}


def gen_ai(engine, image, prompt, out, seconds=5.0, seed=7, retries=3):
    from gradio_client import Client, handle_file
    kw = {"hf_token": os.environ["HF_TOKEN"]} if os.environ.get("HF_TOKEN") else {}
    for attempt in range(retries):
        try:
            t = time.time(); c = Client(SPACES[engine], verbose=False, **kw)
            if engine == "wan":
                res = c.predict(input_image=handle_file(str(image)), prompt=prompt, steps=6, duration_seconds=min(float(seconds), 5.0),
                                guidance_scale=1, guidance_scale_2=1, seed=seed, randomize_seed=False, api_name="/generate_video")
            else:
                res = c.predict(prompt=prompt, negative_prompt=NEG_LTX, input_image_filepath=handle_file(str(image)), input_video_filepath=None,
                                height_ui=1216, width_ui=704, mode="image-to-video", duration_ui=min(float(seconds), 8), ui_frames_to_use=9,
                                seed_ui=seed, randomize_seed=False, ui_guidance_scale=1, improve_texture_flag=True, api_name="/image_to_video")
            v = res[0]["video"] if isinstance(res[0], dict) else res[0]
            Path(out).parent.mkdir(parents=True, exist_ok=True); shutil.copy(v, out)
            print(f"  ✓ {Path(out).name} via {engine} in {time.time() - t:.0f}s  {probe(out)}"); return True
        except Exception as e:
            msg = str(e)[:200]; print(f"  ! {engine} attempt {attempt + 1}: {msg}")
            if "quota" in msg.lower(): print("    ZeroGPU quota hit — set HF_TOKEN (free account) or retry later"); return False
            time.sleep(15 * (attempt + 1))
    return False


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


def main():
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="cmd", required=True)
    g = sp.add_parser("gen"); g.add_argument("ep"); g.add_argument("--only", nargs="*"); g.add_argument("--force", action="store_true")
    p = sp.add_parser("prep"); p.add_argument("ep"); p.add_argument("hf")
    o = sp.add_parser("one"); o.add_argument("image"); o.add_argument("prompt"); o.add_argument("out")
    o.add_argument("--engine", default="wan"); o.add_argument("--seconds", type=float, default=5.0); o.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    if a.cmd == "one": sys.exit(0 if gen_ai(a.engine, a.image, a.prompt, a.out, a.seconds, a.seed) else 1)
    ep = Path(a.ep).resolve(); cfg = json.load(open(ep / "clips.json"))["clips"]
    if a.cmd == "gen":
        bad = 0
        for c in cfg:
            if a.only and c["id"] not in a.only: continue
            out = ep / "clips" / f"{c['id']}.mp4"
            if out.exists() and not a.force: print(f"  = {out.name} exists"); continue
            ok = gen_url(c["url"], c["in"], c["out"], out) if c["engine"] == "url" else \
                 gen_ai(c["engine"], ep / c["image"], c["prompt"], out, c.get("seconds", 5), c.get("seed", 7))
            bad += not ok
        sys.exit(1 if bad else 0)
    scenes = scene_durations(ep); hf = Path(a.hf)
    for c in cfg:
        src = ep / "clips" / f"{c['id']}.mp4"
        if not src.exists(): print(f"  ! missing {src.name} — run `clips.py gen` or `media.py pull`"); continue
        prep_one(c, src, hf / "assets" / "clips" / f"{c['id']}.mp4", target_dur(c, scenes))


if __name__ == "__main__":
    main()
