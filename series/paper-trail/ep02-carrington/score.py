#!/usr/bin/env python3
"""Paper Trail File 02 — original score + SFX + VO mix (procedural, royalty-free).
Music identity (differs from File 01 by design): E minor, 72 bpm telegraph-sounder pulse, aurora shimmer pads,
ends UNRESOLVED on an Esus2 swell under "a world built on wires" (File 01 resolved D minor -> F major at 60 bpm).
Reads timeline.json + trimmed VO wavs. Writes <out>/mix.wav (48k stereo, -14 LUFS, TP -2.0 pre-AAC) + stems + mix_report.json.
usage: python3 score.py [vo_dir] [out_dir]
"""
import json, sys
from pathlib import Path
import numpy as np
import soundfile as sf
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "reelkit"))
import synth as S
from synth import note as N, place, SR

HERE = Path(__file__).resolve().parent
VO_DIR = Path(sys.argv[1] if len(sys.argv) > 1 else Path.home() / ".cache/build/ep02-carrington")
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else Path.home() / ".cache/build/ep02-carrington")
TL = json.load(open(HERE / "timeline.json"))
C, SC, TOTAL = TL["cues"], {s["id"]: s for s in TL["scenes"]}, TL["total"]
TYPE_RATE = 22.0                                   # must match build.py
BEAT = 60 / 72
S.seed(1859)
rng = np.random.default_rng(1859)
n = int((TOTAL + 0.5) * SR)
music = np.zeros((n, 2), np.float32)               # ducked under VO
sfx = np.zeros((n, 2), np.float32)                 # lightly ducked
vo = np.zeros((n, 2), np.float32)

def chord(names): return [N(x) for x in names]

def zap(d=0.35, level=0.35):
    """Electric arc: band-passed crackle bursts over a 120 Hz buzz, fast decay."""
    m = int(d * SR); t = np.arange(m) / SR
    burst = rng.normal(0, 1, m) * (rng.random(m) < 0.18)
    crack = S.filt(S.filt(burst, "high", 1800), "low", 9000)
    buzz = np.sign(np.sin(2 * np.pi * 120 * t)) * 0.25
    x = (crack + buzz) * np.exp(-t / (d * 0.35))
    return (x / (np.abs(x).max() + 1e-9) * level).astype(np.float32)

def crackle(d=6.0, level=0.06):
    """Campfire: sparse pops over soft low hiss."""
    m = int(d * SR); x = S.filt(rng.normal(0, 0.15, m), "low", 900)
    for p in rng.integers(0, m - 800, int(d * 9)):
        k = np.arange(600); x[p:p + 600] += rng.uniform(0.4, 1.0) * np.exp(-k / 90) * rng.normal(0, 1, 600)
    x = S.filt(x, "high", 120)
    return (x / (np.abs(x).max() + 1e-9) * level).astype(np.float32)

def morse(bus, code, t0, unit=0.085, level=0.12, pan=0.25):
    """Telegraph sounder: down-click + up-click per element (dot = 1 unit, dash = 3)."""
    t = t0
    for ch in code:
        if ch in ".-":
            place(bus, S.tick(True, level), t, pan=pan); dur = unit * (1 if ch == "." else 3)
            place(bus, S.tick(False, level * 0.7), t + dur, pan=pan); t += dur + unit
        else:
            t += unit * 3
    return t

# ---------- VO ----------
for s in TL["scenes"]:
    x, sr = sf.read(VO_DIR / f"{s['vo']}.wav", dtype="float32")
    assert sr == SR, sr
    if x.ndim > 1: x = x.mean(1)
    x = S.filt(x, "high", 70)
    place(vo, x / (np.abs(x).max() + 1e-9) * 0.7, s["start"])
vo = S.reverb(vo, secs=0.9, wet=0.06, bright=6000)[:n]

# ---------- A: s01 hook — sounder clicks, then the sky ----------
place(sfx, S.hit(0.5), 0.30)
morse(sfx, "-.-. --.-  -.-. --.-", 0.55)                  # "CQ CQ" (calling any station) under the opening line
place(sfx, zap(0.30, 0.30), C["unplugged"] + 0.05, pan=-0.2)
morse(sfx, ".-- --- .-. -.-", C["talking"] - 0.2, level=0.10)   # keeps on talking
place(music, S.drone(N("E1"), SC["s03"]["start"] + 0.5, cutoff=280, level=0.26), 0.0)
place(music, S.pad(chord(["E3", "G3", "B3"]), 9.6, cutoff=650, level=0.06), 0.3)
shimmer = S.pad(chord(["B4", "E5", "F#5", "B5"]), 5.0, cutoff=5200, a=1.2, r=2.0, level=0.07)
place(music, shimmer, C["power"] - 0.2)
for i, nm in enumerate(["E6", "B5", "F#6"]):
    place(music, S.bell(N(nm), 3.0, 0.045), C["sky"] + i * 0.35, pan=-0.4 + 0.4 * i)
place(sfx, S.whoosh(0.8, 0.22), C["power"] - 0.6)

# ---------- B: s02 Redhill — 72 bpm piano pulse, the flare ----------
s2 = SC["s02"]["start"]
place(sfx, S.paper(0.6, 0.28), s2 - 0.05, pan=-0.2)
P = np.zeros((n, 2), np.float32)
prog = [("E2", ["E3", "G3", "B3"]), ("C2", ["C3", "G3", "E4"]), ("A1", ["A2", "E3", "C4"]), ("B1", ["B2", "F#3", "D#4"])]
t = s2
while t < C["broke"] - 0.1:
    bass, ch = prog[int((t - s2) / (2 * BEAT)) % 4]
    place(P, S.piano(N(bass), 1.6, 0.30), t, pan=-0.1)
    for j, nm in enumerate(ch): place(P, S.piano(N(nm), 0.9, 0.18), t + BEAT * (0.5 + j * 0.5), pan=0.2)
    t += 2 * BEAT
music += S.reverb(P, secs=2.6, wet=0.30, bright=4200)[:n]
place(sfx, S.whoosh(0.5, 0.2), C["carrington"] - 0.4)
place(sfx, S.paper(0.4, 0.22), C["carrington"] + 0.1, pan=0.3)
place(sfx, S.riser(1.4, 0.2), C["white"] - 1.3)
place(sfx, S.boom(1.4, 110, 40, 0.5), C["broke"]); place(sfx, S.reverb(S.bell(N("E6"), 2.4, 0.1), 2.0, 0.4), C["broke"])

# ---------- C: s03 sixty seconds -> five minutes -> gone ----------
s3 = SC["s03"]["start"]
place(sfx, S.whoosh(0.45, 0.32, up=False), s3 - 0.3)
place(sfx, S.projector(SC["s03"]["end"] - s3, 0.10), s3)
for k in range(int((C["gone"] - C["sixty"]) / 0.5)):
    place(sfx, S.tick(k % 2 == 0, 0.12), C["sixty"] + k * 0.5, pan=0.3)
place(sfx, S.stamp(0.8), C["sixty"] + 0.25)
place(music, S.pad(chord(["E2", "B2", "E3", "F3"]), C["gone"] - s3, cutoff=900, level=0.08), s3)   # b9 tension
place(sfx, S.boom(1.8, 60, 25, 0.45), C["gone"] + 0.1)

# ---------- D: s04 +17 hours: the field shakes, the sky turns red ----------
s4 = SC["s04"]["start"]
place(sfx, S.paper(0.4, 0.30), s4 - 0.28, pan=0.3); place(sfx, S.whoosh(0.45, 0.16), s4 - 0.33)
place(music, S.drone(N("E1"), SC["s05"]["start"] - s4 + 1, cutoff=420, level=0.22), s4)
k = 0; t = s4 + 0.3
while t < C["shake"]:
    place(sfx, S.heartbeat(0.32 + 0.04 * k), t); t += BEAT; k += 1
place(sfx, S.riser(1.6, 0.24), C["shake"] - 1.5)
place(sfx, S.boom(2.0, 70, 26, 0.75), C["shake"])
place(sfx, S.whoosh(0.6, 0.25), C["blood"] - 0.5)
place(sfx, S.projector(SC["s04"]["end"] - C["blood"] + 0.3, 0.12), C["blood"] - 0.3)
place(music, S.pad(chord(["C3", "E3", "G3", "B3"]), 4.2, cutoff=1800, level=0.10), C["blood"] - 0.3)

# ---------- E: s05 campers at 1 a.m. ----------
s5 = SC["s05"]["start"]
place(sfx, S.whoosh(0.5, 0.25, up=False), s5 - 0.2)
place(sfx, crackle(SC["s05"]["end"] - s5 + 0.4, 0.07), s5, pan=-0.15)
place(music, S.pad(chord(["G3", "B3", "D4", "E4"]), SC["s05"]["end"] - s5 + 1.2, cutoff=2200, level=0.11), s5)
for i, nm in enumerate(["B5", "D6", "G5"]):
    place(music, S.bell(N(nm), 3.0, 0.04), C["dawn"] - 0.2 + i * 0.4, pan=0.3 - 0.3 * i)

# ---------- F: s06 sparks, shocks, fire ----------
s6 = SC["s06"]["start"]
place(sfx, S.paper(0.4, 0.30), s6 - 0.28, pan=0.3); place(sfx, S.whoosh(0.45, 0.16), s6 - 0.33)
place(music, S.drone(N("B0"), SC["s07"]["start"] - s6, cutoff=360, level=0.20), s6)
for t0, cnt in ((C["sparks"], 5), (C["shocks"], 3), (C["fire"], 3)):
    for j in range(cnt): place(sfx, zap(0.25, 0.26), t0 + j * 0.13, pan=-0.4 + 0.2 * j)
place(sfx, S.boom(1.2, 90, 40, 0.5), C["shocks"])
place(sfx, S.stamp(0.85), C["shocks"] + 0.35)
place(sfx, S.whoosh(0.6, 0.3), C["fire"] + 0.05); place(sfx, crackle(1.6, 0.1), C["fire"] + 0.1, pan=0.2)

# ---------- G: s07 Boston ⇄ Portland on the aurora's current ----------
s7 = SC["s07"]["start"]
place(sfx, S.hit(0.3), s7)
place(music, S.pad(chord(["E3", "B3", "F#4", "G4"]), SC["s08"]["start"] - s7 + 1.0, cutoff=3000, level=0.10), s7)
place(music, S.pad(chord(["B4", "E5", "F#5"]), SC["s08"]["start"] - s7, cutoff=5600, a=2.0, level=0.05), s7 + 0.5)
place(sfx, S.tick(True, 0.15), C["boston"] - 0.1, pan=-0.3); place(sfx, S.tick(True, 0.15), C["portland"] - 0.1, pan=0.3)
t = C["disconnected"] + 0.3
for word in [".-. . .- -.. -.--", "--. .-", "..-. .. -. ."]:              # READY · GA · FINE — sounder chatter, no battery
    t = morse(sfx, word, t, level=0.09, pan=0.1) + 0.35
place(sfx, S.stamp(0.85), C["hours"] + 0.1)
place(music, S.bell(N("B5"), 3.0, 0.05), C["alone"])

# ---------- H: s08 "One swallow does not make a summer" ----------
s8 = SC["s08"]["start"]
place(sfx, S.paper(0.4, 0.30), s8 - 0.28, pan=0.3); place(sfx, S.paper(0.5, 0.22), s8 + 0.05)
P = np.zeros((n, 2), np.float32)
for nm, t, d in [("E2", s8 + 0.05, 3.5), ("B3", s8 + 0.6, 2.0), ("G3", s8 + 1.6, 2.0), ("C2", C["flare"] + 0.4, 3.0),
                 ("E4", C["storm"] - 0.1, 1.6), ("A1", C["connected"] - 0.4, 3.0), ("C4", C["connected"], 2.0)]:
    place(P, S.piano(N(nm), d, 0.32), t, pan=0.1)
for nm, t, d in [("G4", C["swallow"] - 0.1, 1.4), ("A4", C["swallow"] + 0.7, 1.2), ("B4", C["swallow"] + 1.4, 2.6)]:
    place(P, S.piano(N(nm), d, 0.30), t, pan=0.2)
music += S.reverb(P, secs=3.0, wet=0.32, bright=4500)[:n]
place(sfx, S.tick(True, 0.14), C["flare"] - 0.05); place(sfx, S.tick(True, 0.14), C["storm"] - 0.05)
place(sfx, S.stamp(0.5), C["connected"])
place(sfx, S.whoosh(0.9, 0.12), C["swallow"] + 0.2)

# ---------- I: s09 23 July 2012 ----------
s9 = SC["s09"]["start"]
place(sfx, S.hit(0.45), s9); place(sfx, S.projector(C["orbit"] + 0.55 - s9, 0.11), s9)
place(music, S.drone(N("E1"), SC["s10"]["start"] - s9 + 0.5, cutoff=380, level=0.24), s9)
place(music, S.pad(chord(["E2", "B2", "E3", "F3"]), C["week"] - s9, cutoff=1000, level=0.08), s9)
place(sfx, S.whoosh(0.6, 0.25), C["orbit"] + 0.4)
place(sfx, S.stamp(0.8), C["orbit"] + 1.1)
place(sfx, S.riser(1.6, 0.26), C["hitus"] - 1.55)
place(sfx, S.boom(2.2, 70, 26, 0.85), C["hitus"])

# ---------- J: s10 a world built on wires — unresolved ----------
s10 = SC["s10"]["start"]
place(sfx, S.whoosh(0.9, 0.22), s10 - 0.5)
sw_len = TOTAL - s10 + 0.3
sw = S.pad(chord(["E2", "B2", "F#3", "B3", "E4"]), sw_len, cutoff=1100, a=3.0, r=2.6, level=0.12)   # Esus2: no third, no resolution
ramp = np.clip(S.t_(sw_len) / (C["wires"] - s10), 0, 1) ** 1.5
place(music, sw * (0.35 + 0.9 * ramp), s10)
P = np.zeros((n, 2), np.float32)
for nm, t, d in [("E2", s10 + 0.05, 4.0), ("B3", s10 + 0.6, 2.2), ("F#4", s10 + 1.6, 2.4), ("C2", C["next"] - 0.2, 3.5),
                 ("G4", C["next"] + 0.4, 2.0), ("E2", C["wires"] - 0.1, 6.0), ("B4", C["wires"] + 0.4, 3.5), ("F#5", C["end"] + 0.4, 3.5)]:
    place(P, S.piano(N(nm), d, 0.36), t, pan=0.1)
music += S.reverb(P, secs=3.4, wet=0.34, bright=4500)[:n]
morse(sfx, "...  ---  ...", C["wires"] + 0.6, unit=0.07, level=0.06, pan=0.4)   # faint S·O·S under the last chord
place(sfx, S.hit(0.25), TOTAL - 3.4)

# ---------- paper-tear transitions (build.py tears at s02, s04, s06, s08 — placed above per scene) ----------
# ---------- typewriter clicks for every typed label ----------
for t0, text, _id in TL["typed"]:
    place(sfx, S.typing(len(text), TYPE_RATE, 0.13), t0, pan=0.15)
for t0, nchar in [(C["carrington"] + 0.25, 29), (C["disconnected"] + 0.25, 68), (C["week"] + 0.2, 14), (C["next"] + 0.6, 21)]:
    place(sfx, S.typing(nchar, TYPE_RATE, 0.11), t0, pan=0.15)   # untimed tags typed in build.py (name, telegram, 1 WEEK EARLIER, 12%)

# ---------- glue + ducking + master ----------
music = S.reverb(music, secs=2.2, wet=0.12, bright=6000)[:n]
env = S.follower(vo[:, 0], 0.03, 0.40)
env = env / (env.max() + 1e-9)
duck = 1.0 - 0.77 * np.clip(env * 3.0, 0, 1)
duck_sfx = 1.0 - 0.35 * np.clip(env * 3.0, 0, 1)
mix = vo * 1.0 + music * duck[:, None] * 0.95 + sfx * duck_sfx[:, None] * 0.9
mix = np.tanh(mix * 1.1) / 1.1
fade = int(1.2 * SR); mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
from master import finish
finish(mix, OUT, vo=vo, music=music * duck[:, None] * 0.95, sfx=sfx * duck_sfx[:, None] * 0.9)
