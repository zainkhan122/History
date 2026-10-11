#!/usr/bin/env python3
"""
reelkit/audio.py — procedural music bed + SFX + VO mix, then mux with the rendered video.
No music model needed: everything is synthesized with numpy, keyed to the word-anchored
timeline.json written by render.py (Hypit idea: sound events land on words).

Moods per beat (spec beat["mood"]): tension | triumph | tender
SFX per event (spec event["sfx"]):  alarm | impact | stamp | whoosh(auto on every shot cut)
Usage: python3 audio.py <reel.json>
"""
import json, os, subprocess, sys
os.environ["PATH"] = os.path.expanduser("~/.cache/bin") + os.pathsep + os.environ.get("PATH", "")  # setup.sh tools
import numpy as np

SR = 44100
spec_path = sys.argv[1]
SPEC = json.load(open(spec_path)); ROOT = os.path.dirname(os.path.abspath(spec_path))
TL = json.load(open(os.path.join(ROOT, "timeline.json")))
WORDS = json.load(open(os.path.join(ROOT, "words.json")))
N = int(TL["total"] * SR) + SR
rng = np.random.default_rng(3)
SCRATCH = os.path.expanduser("~/.cache/tmp/" + os.path.basename(ROOT)); os.makedirs(SCRATCH, exist_ok=True)

def load(path, ss=0.0):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(ss), "-i", os.path.join(ROOT, os.path.expanduser(path)), "-f", "f32le",
                          "-ac", "1", "-ar", str(SR), "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.float32)

def env(n, a=.01, r=.2):
    t = np.arange(n) / SR; e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / max(r, 1e-4)); return e

def lowpass(x, k):       # simple one-pole
    y = np.empty_like(x); acc = 0.0
    for i in range(len(x)): acc += k * (x[i] - acc); y[i] = acc
    return y

def put(buf, sig, t, g=1.0):
    i = int(t * SR); j = min(len(buf), i + len(sig))
    if i < len(buf) and j > i: buf[i:j] += g * sig[: j - i]

# ---------------------------------------------------------------- VO
vo = np.zeros(N, np.float32)
for b, spec_b in zip(TL["beats"], SPEC["beats"]):
    put(vo, load(spec_b["vo"]), b["t0"])

# ---------------------------------------------------------------- music bed per mood
bed = np.zeros(N, np.float32)
def seg_tension(n, t0):
    t = np.arange(n) / SR + t0
    drone = .5 * np.sin(2 * np.pi * 55 * t) + .25 * np.sin(2 * np.pi * 82.4 * t) + .12 * np.sin(2 * np.pi * 110 * t + np.sin(t))
    out = drone * (.6 + .4 * np.sin(2 * np.pi * .25 * t))
    beat = .6                                         # heartbeat kick every 0.6 s
    for k in np.arange(np.ceil(t0 / beat) * beat, t0 + n / SR, beat):
        m = int(.25 * SR); tt = np.arange(m) / SR
        kick = np.sin(2 * np.pi * (90 * np.exp(-tt * 18) + 38) * tt) * env(m, .002, .12)
        put(out, 1.6 * kick, k - t0)
        tick = rng.normal(0, 1, int(.012 * SR)) * env(int(.012 * SR), .0005, .004)   # clock tick
        put(out, .5 * np.diff(tick, prepend=0), k - t0 + beat / 2)
    return out * .5

def pad(n, t0, freqs, bright=.0):
    t = np.arange(n) / SR + t0
    sig = sum(np.sin(2 * np.pi * f * t) + .3 * np.sin(2 * np.pi * 2 * f * t + .3) + bright * np.sin(2 * np.pi * 3 * f * t) for f in freqs)
    sig *= .6 + .4 * np.sin(2 * np.pi * .5 * t) ** 2
    return sig / len(freqs) * .55

def seg_triumph(n, t0):
    out = pad(n, t0, [220, 277.18, 329.63, 440], bright=.25)
    a = np.minimum(1, np.arange(n) / (SR * .08)); return out * a * 1.2

def seg_tender(n, t0):
    out = pad(n, t0, [174.61, 220, 261.63, 349.23]) * .8
    notes = [523.25, 440, 349.23, 392, 440, 523.25, 587.33, 523.25]
    for k, f in enumerate(notes):                     # sparse music-box plucks
        st = k * .95
        if st * SR >= n: break
        m = int(1.6 * SR); tt = np.arange(m) / SR
        put(out, .5 * (np.sin(2 * np.pi * f * tt) + .3 * np.sin(4 * np.pi * f * tt)) * env(m, .004, .5), st)
    return out

MOODS = dict(tension=seg_tension, triumph=seg_triumph, tender=seg_tender)
MUSIC = SPEC.get("music")            # {"file": "music/track.mp3", "offset": 12.3, "gain": 1.0}
if MUSIC:                            # real track (offset chosen by beats.py so cuts land on beats)
    m = load(MUSIC["file"], MUSIC.get("offset", 0.0))
    if len(m) < N: m = np.tile(m, N // max(len(m), 1) + 1)
    bed[:] = m[:N] * MUSIC.get("gain", 1.0)
    f_in, f_out = int(.15 * SR), int(1.5 * SR)
    bed[:f_in] *= np.linspace(0, 1, f_in); end = int(TL["total"] * SR) + int(.6 * SR)
    bed[max(0, end - f_out):end] *= np.linspace(1, 0, min(f_out, end)); bed[end:] = 0
for b, sb in ([] if MUSIC else zip(TL["beats"], SPEC["beats"])):
    t1 = b["t1"] if sb is not SPEC["beats"][-1] else TL["total"]
    n = int((t1 - b["t0"]) * SR) + int(.3 * SR)
    s = MOODS[sb.get("mood", "tension")](n, b["t0"]).astype(np.float32)
    fade = int(.3 * SR); s[:fade] *= np.linspace(0, 1, fade); s[-fade:] *= np.linspace(1, 0, fade)
    put(bed, s, b["t0"])

# ---------------------------------------------------------------- SFX
sfx = np.zeros(N, np.float32)
def alarm():      # Apollo-style master alarm: alternating two-tone square
    out = []
    for k in range(6):
        f = 880 if k % 2 == 0 else 660; m = int(.11 * SR); tt = np.arange(m) / SR
        out.append(np.sign(np.sin(2 * np.pi * f * tt)) * .35 * env(m, .002, .2))
    return np.concatenate(out)
def impact():
    m = int(.9 * SR); tt = np.arange(m) / SR
    boom = np.sin(2 * np.pi * (120 * np.exp(-tt * 9) + 32) * tt) * env(m, .002, .35)
    crack = lowpass(rng.normal(0, 1, m).astype(np.float32), .35) * env(m, .001, .05)
    return 1.1 * boom + .6 * crack
def stamp():
    m = int(.25 * SR); tt = np.arange(m) / SR
    return np.sin(2 * np.pi * (180 * np.exp(-tt * 30) + 60) * tt) * env(m, .001, .06) + \
           .5 * lowpass(rng.normal(0, 1, m).astype(np.float32), .5) * env(m, .001, .02)
def whoosh():
    m = int(.45 * SR); x = rng.normal(0, 1, m).astype(np.float32)
    k = np.linspace(.02, .5, m // 2).tolist() + np.linspace(.5, .02, m - m // 2).tolist()
    y = np.empty_like(x); acc = 0.0
    for i in range(m): acc += k[i] * (x[i] - acc); y[i] = acc
    e = np.sin(np.linspace(0, np.pi, m)) ** 2
    return y * e * .9
FX = dict(alarm=alarm, impact=impact, stamp=stamp, whoosh=whoosh)
for e in TL["events"]:
    if e.get("sfx"): put(sfx, FX[e["sfx"]](), e["t"] - (.0 if e["sfx"] != "whoosh" else .2), .9)
for s in TL["shots"][1:]:
    put(sfx, whoosh(), s["t0"] - .22, .55)

# ---------------------------------------------------------------- mix with VO ducking (sidechain)
venv = np.abs(vo); win = int(.08 * SR)
venv = np.convolve(venv, np.ones(win) / win, "same"); venv = venv / (venv.max() + 1e-9)
duck = 1 - .55 * np.clip(venv * 3, 0, 1)
bed = bed / (np.abs(bed).max() + 1e-9)
mix = vo / (np.abs(vo).max() + 1e-9) * .9 + bed * .22 * duck + sfx / (np.abs(sfx).max() + 1e-9) * .45
mix = np.tanh(mix * 1.1) * .9
wav = os.path.join(SCRATCH, "mix.wav")
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", wav],
               input=mix.astype(np.float32).tobytes(), check=True)
# two-pass loudnorm -> -14 LUFS (YouTube/IG/TikTok target), stereo AAC
m = subprocess.run(["ffmpeg", "-hide_banner", "-i", wav, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
                    "-f", "null", "-"], capture_output=True, text=True).stderr
j = json.loads(m[m.rindex("{"):m.rindex("}") + 1])
af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
      f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true,"
      "aformat=channel_layouts=stereo")
m4a = os.path.join(SCRATCH, "mix.m4a")
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", wav, "-af", af, "-ar", "48000", "-c:a", "aac", "-b:a", "192k", m4a], check=True)
vid = os.path.join(ROOT, SPEC["video_out"]) if "video_out" in SPEC else os.path.join(SCRATCH, "video_noaudio.mp4")
final = os.path.join(ROOT, SPEC.get("final_out", "final.mp4"))
# memory-safe encode (2 GB sandbox): veryfast, 2 threads, 12 Mbps cap = upload-friendly
subprocess.run(["ffmpeg", "-y", "-v", "error", "-threads", "2", "-i", vid, "-i", m4a, "-map", "0:v", "-map", "1:a",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-maxrate", "12M", "-bufsize", "24M",
                "-pix_fmt", "yuv420p", "-c:a", "copy", "-shortest", "-movflags", "+faststart", final + ".tmp.mp4"], check=True)
os.replace(final + ".tmp.mp4", final)
print("wrote", final)
