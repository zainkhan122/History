#!/usr/bin/env python3
"""Paper Trail Ep.01 — original score + SFX + VO mix (procedural, royalty-free, D minor -> F major).
Reads timeline.json + trimmed VO wavs. Writes <out>/mix.wav (48k stereo, -14 LUFS, TP -1.5) + stems.
usage: python3 score.py [vo_dir] [out_dir]
"""
import json, sys, subprocess, re, shutil
from pathlib import Path
import numpy as np
import soundfile as sf
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "reelkit"))
import synth as S
from synth import note as N, place, SR

HERE = Path(__file__).resolve().parent
VO_DIR = Path(sys.argv[1] if len(sys.argv) > 1 else Path.home() / ".cache/build/ep01-petrov")
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else Path.home() / ".cache/build/ep01-petrov")
TL = json.load(open(HERE / "timeline.json"))
C, SC, TOTAL = TL["cues"], {s["id"]: s for s in TL["scenes"]}, TL["total"]
TYPE_RATE = 22.0                                   # must match build.py
S.seed(1983)
n = int((TOTAL + 0.5) * SR)
music = np.zeros((n, 2), np.float32)               # ducked under VO
sfx = np.zeros((n, 2), np.float32)                 # lightly ducked
vo = np.zeros((n, 2), np.float32)

def chord(names): return [N(x) for x in names]

# ---------- VO ----------
for s in TL["scenes"]:
    x, sr = sf.read(VO_DIR / f"{s['vo']}.wav", dtype="float32")
    assert sr == SR, sr
    if x.ndim > 1: x = x.mean(1)
    x = S.filt(x, "high", 70)                       # rumble cut
    place(vo, x / (np.abs(x).max() + 1e-9) * 0.7, s["start"])
# gentle VO "air" room so it sits inside the score (very low wet)
vo = S.reverb(vo, secs=0.9, wet=0.06, bright=6000)[:n]

# ---------- A: 0 – 18.5  dread (drone + clock) ----------
s3 = SC["s03"]["start"]
music_a = S.drone(N("D1"), s3 + 1.5, cutoff=300, level=0.30) + S.drone(N("A1"), s3 + 1.5, cutoff=260, level=0.14)
place(music, music_a, 0.0)
place(music, S.pad(chord(["D3", "F3", "A3"]), 9.2, cutoff=700, level=0.07), 0.2)
place(music, S.pad(chord(["D3", "F3", "Bb3"]), 9.6, cutoff=800, level=0.08), 9.0)
k = 0
for t in np.arange(0.35, s3 - 0.3, 1.0):           # the bunker clock
    place(sfx, S.tick(k % 2 == 0, 0.10), t, pan=0.25); k += 1
place(sfx, S.hit(0.55), 0.30)                       # hook impact on frame 1
place(sfx, S.whoosh(0.9, 0.30), C["nuclear"] - 0.75)
place(sfx, S.boom(2.2, 70, 28, 0.85), C["nuclear"])
place(sfx, S.paper(0.6, 0.28), SC["s02"]["start"] - 0.05, pan=-0.2)   # card drop
place(sfx, S.stamp(0.8), C["died269"] + 0.1)                              # 269 DEAD stamp (build.py matches)
place(sfx, S.riser(1.6, 0.22), C["paranoid"] - 0.6)

# ---------- B: launch (siren + 5 impacts) ----------
place(sfx, S.whoosh(0.5, 0.35, up=False), s3 - 0.3)
place(sfx, S.siren(SC["s03"]["vo_end"] - C["launch"] + 0.6, 0.075), C["launch"] - 0.05, pan=0.1)
for i, key in enumerate(["launch", "m2", "m3", "m4", "m5"]):
    place(sfx, S.hit(0.42 + 0.09 * i), C[key] - 0.02)
place(music, S.pad(chord(["D2", "A2", "D3", "Eb3"]), 6.6, cutoff=900, level=0.10), s3)   # cluster (b9 tension)

# ---------- C: chain of command + Petrov (60 bpm pulse) ----------
s4, s5, s6 = SC["s04"]["start"], SC["s05"]["start"], SC["s06"]["start"]
prog = [(["D2", "D3", "F3", "A3"], s4), (["Bb1", "Bb2", "D3", "F3"], s4 + 3.5),
        (["G1", "G2", "Bb2", "D3"], s5), (["A1", "A2", "C#3", "E3"], s5 + 4.4)]
for i, (ch, t0) in enumerate(prog):
    t1 = prog[i + 1][1] if i + 1 < len(prog) else s6
    place(music, S.pad(chord(ch[1:]), t1 - t0 + 1.5, cutoff=1100, level=0.09), t0)
    for b in np.arange(t0, t1, 1.0):              # low pulse
        p = S.piano(N(ch[0]), 0.9, 0.55); place(music, S.filt(p, "low", 300), b)
place(sfx, S.whoosh(0.8, 0.28), C["chain"] - 0.6)
for kk, t in enumerate([C["chain"] + 0.2, C["chain"] + 1.1, C["chain"] + 2.0, C["minutes"] - 0.3]):
    place(sfx, S.tick(True, 0.16), t, pan=-0.3 + 0.2 * kk)       # node pops
place(sfx, S.boom(1.4, 80, 35, 0.45), C["strike"])
if (HERE / "clips" / "arch_minuteman.mp4").exists() or (HERE / "clips.json").exists():   # v2 archival insert (build.py)
    place(sfx, S.projector(SC["s04"]["end"] + 0.25 - (C["strike"] - 0.42), 0.14), C["strike"] - 0.42)
    place(sfx, S.whoosh(0.45, 0.22, up=False), SC["s04"]["end"] - 0.3)            # film burn-out
place(sfx, S.hit(0.35), C["petrov"] - 0.08)
place(music, S.bell(N("A4"), 3.0, 0.05), C["quote"] - 0.2)

# ---------- D: false alarm, the wait ----------
place(sfx, S.stamp(0.9), C["falsealarm"] + 0.05)
place(music, S.pad(chord(["D3", "F3", "A3"]), C["waited"] - s6 + 0.8, cutoff=600, level=0.06), s6)
hb = C["waited"] + 0.05
while hb < C["nothingcame"] - 0.4:                  # heartbeat + ticks, nothing else
    place(sfx, S.heartbeat(0.55), hb); hb += 1.0
for kk, t in enumerate(np.arange(C["waited"], C["nothingcame"] - 0.2, 0.5)):
    place(sfx, S.tick(kk % 2 == 0, 0.13), t, pan=0.3)
# silence on "Nothing came." then a breath of air
place(music, S.pad(chord(["F3", "A3", "C4"]), 2.2, cutoff=700, level=0.045), C["nothingcame"] + 0.9)

# ---------- E: the reveal (sunlight) ----------
s7, s8 = SC["s07"]["start"], SC["s08"]["start"]
place(sfx, S.riser(1.4, 0.26), s7 - 1.3)
place(sfx, S.whoosh(0.6, 0.25, up=False), s7 - 0.05)
place(music, S.pad(chord(["F3", "A3", "C4", "G4"]), s8 - s7 + 1.2, cutoff=2600, level=0.15), s7)
place(sfx, S.reverb(S.bell(N("C6"), 3.0, 0.10), 2.5, 0.5), s7 + 0.05)
for i, nm in enumerate(["C6", "G5", "A5", "E6", "C6", "G6"]):
    place(sfx, S.bell(N(nm), 2.6, 0.045), s7 + 0.1 + i * 0.9, pan=-0.5 + 0.2 * i)

# ---------- F: cold aftermath (stamps) ----------
place(music, S.drone(N("D2"), SC["s09"]["start"] - s8 + 1, cutoff=320, level=0.18), s8)
place(music, S.pad(chord(["D3", "F3", "A3"]), SC["s09"]["start"] - s8 + 0.8, cutoff=650, level=0.06), s8)
place(sfx, S.paper(0.5, 0.25), s8 - 0.2)
place(sfx, S.stamp(0.95), C["reprimanded"] + 0.1)
place(sfx, S.stamp(0.95), C["secret"] + 0.1)

# ---------- G: piano theme (wife -> human race), resolves to F major ----------
s9, s10 = SC["s09"]["start"], SC["s10"]["start"]
P = np.zeros((n, 2), np.float32)
def pchord(names, t, vel=0.5, d=4.5, spread=0.03):
    for i, nm in enumerate(names):
        place(P, S.piano(N(nm), d, vel * (0.75 if i < len(names) - 1 else 1)), t + i * spread, pan=-0.3 + 0.6 * i / max(len(names) - 1, 1))
def pmel(seq, vel=0.5):
    for nm, t, d in seq: place(P, S.piano(N(nm), d, vel), t, pan=0.15)

pchord(["D2", "A2", "F3", "A3"], s9 + 0.05, 0.45)
pmel([("A4", s9 + 0.6, 2.0), ("F4", s9 + 1.6, 1.6)])
pchord(["Bb1", "F2", "D3", "F3"], s9 + 3.0, 0.42)
pmel([("D5", s9 + 3.5, 1.6), ("C5", s9 + 4.4, 2.2)])
# hush before "Nothing. I did nothing." — just one held note
place(P, S.piano(N("A3"), 4.0, 0.3), C["nothing1"] - 0.35, pan=0)
t = C["didnothing"] + 0.9
pchord(["F2", "C3", "A3", "C4"], s10 + 0.0, 0.42)
pmel([("A4", s10 + 0.5, 2.2), ("G4", s10 + 1.8, 1.4), ("F4", s10 + 2.6, 2.4)])
pchord(["C2", "G2", "E3", "G3"], s10 + 3.6, 0.42)
pmel([("E4", s10 + 4.1, 2.0), ("G4", s10 + 5.2, 1.8)])
pchord(["D2", "A2", "F3", "A3"], C["survived"] - 0.35, 0.46)
pmel([("A4", C["survived"] + 0.2, 1.6), ("C5", C["survived"] + 1.3, 1.6)])
pchord(["Bb1", "F2", "D3", "F3"], C["entire"] - 1.6, 0.5)
pchord(["F1", "F2", "C3", "A3", "C4", "F4"], C["entire"] + 0.05, 0.62, d=6.5, spread=0.045)   # resolve on "entire"
pmel([("A5", C["entire"] + 0.9, 3.0), ("C6", C["end"] + 0.4, 3.2)], 0.38)
music += S.reverb(P, secs=3.4, wet=0.34, bright=4500)[:n]
# strings swell (warm pad, rising cutoff) under s10, peaks on "entire human race"
sw_len = TOTAL - s10 + 0.3
sw = S.pad(chord(["F2", "C3", "A3", "C4"]), sw_len, cutoff=900, a=4.0, r=2.6, level=0.12)
ramp = np.clip((S.t_(sw_len) - 0) / (C["entire"] - s10), 0, 1) ** 1.5
sw = sw * (0.35 + 0.9 * ramp)
place(music, sw, s10)
place(music, S.pad(chord(["D3", "F3", "A3"]), s10 - s9 + 1, cutoff=700, level=0.05), s9)
for i, nm in enumerate(["F5", "C6", "A5"]):
    place(music, S.bell(N(nm), 3.5, 0.045), C["entire"] + 0.4 + i * 0.7, pan=-0.4 + 0.4 * i)
place(sfx, S.whoosh(0.9, 0.22), s10 - 0.5)
place(sfx, S.hit(0.25), TOTAL - 3.4)                        # end-card land

# ---------- paper-tear transitions (match build.py TEAR_AT) ----------
for sid in ["s04", "s05", "s06", "s09"]:
    t = SC[sid]["start"] - 0.28
    place(sfx, S.paper(0.4, 0.30), t, pan=0.3); place(sfx, S.whoosh(0.45, 0.16), t - 0.05)

# ---------- typewriter clicks for every typed label ----------
for t0, text, _id in TL["typed"]:
    nchar = len(text)
    place(sfx, S.typing(nchar, TYPE_RATE, 0.13), t0, pan=0.15)

# ---------- music bed reverb glue + ducking ----------
music = S.reverb(music, secs=2.2, wet=0.12, bright=6000)[:n]
env = S.follower(vo[:, 0], 0.03, 0.40)
env = env / (env.max() + 1e-9)
duck = 1.0 - 0.72 * np.clip(env * 3.0, 0, 1)                  # up to ~-11 dB under speech
duck_sfx = 1.0 - 0.35 * np.clip(env * 3.0, 0, 1)
mix = vo * 1.0 + music * duck[:, None] * 0.95 + sfx * duck_sfx[:, None] * 0.9
# soft limiter-ish safety before loudnorm
mix = np.tanh(mix * 1.1) / 1.1
fade = int(1.2 * SR); mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
OUT.mkdir(parents=True, exist_ok=True)
sf.write(OUT / "mix_raw.wav", mix, SR, subtype="FLOAT")
sf.write(OUT / "stem_music.wav", (music * duck[:, None]), SR, subtype="FLOAT")

# ---------- two-pass loudnorm to -14 LUFS / TP -1.5 ----------
def ln(args):
    return subprocess.run([shutil.which("ffmpeg") or "ffmpeg", "-hide_banner", "-nostats", "-y"] + args, capture_output=True, text=True).stderr
st = ln(["-i", str(OUT / "mix_raw.wav"), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"])
m = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", st, re.S).group(0))
af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
      f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
ln(["-i", str(OUT / "mix_raw.wav"), "-af", af + ",aresample=48000", "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", str(OUT / "mix.wav")])
st = ln(["-i", str(OUT / "mix.wav"), "-af", "loudnorm=I=-14:TP=-1.5:print_format=json", "-f", "null", "-"])
m2 = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", st, re.S).group(0))
print("final LUFS", m2["input_i"], "TP", m2["input_tp"], "LRA", m2["input_lra"])
