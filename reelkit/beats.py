#!/usr/bin/env python3
"""
reelkit/beats.py — beat-sync real music to a reel (librosa, ISC license, CPU).

Viral edits feel "tight" because cuts and punches land ON the beat. Our cuts are pinned to
spoken words (Hypit-style), so instead of moving the words we slide the MUSIC: find the
track start offset that lands the most shot cuts / punches on beats (downbeats for cuts).

  python3 beats.py analyze music/track.mp3            # BPM, beats, downbeats -> track.beats.json (in ~/.cache/tmp)
  python3 beats.py snap reel.json music/track.mp3     # after render.py (needs timeline.json)
        -> writes  "music": {"file", "offset", "gain"}  into reel.json, prints per-cut error
  python3 audio.py reel.json                          # mixes the track instead of the procedural bed

Options for snap: --gain 0.9   --max-offset 60 (search only first N s of track)
                  --autopad  add <=0.35 s breaths before VO beats so every beat-boundary cut hits a beat
Music must be licensed for your use (YouTube Audio Library, Pixabay Music, own ACE-Step output…).
"""
import argparse, json, os, sys
os.environ["PATH"] = os.path.expanduser("~/.cache/bin") + os.pathsep + os.environ.get("PATH", "")  # setup.sh tools
import numpy as np

SR = 22050
CACHE = os.path.expanduser("~/.cache/tmp")

def decode(path):
    import subprocess
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)

def analyze(path):
    import librosa
    y = decode(path)
    HOP = 256                                            # ~11.6 ms resolution
    oenv = librosa.onset.onset_strength(y=y, sr=SR, hop_length=HOP)
    tempo, bf = librosa.beat.beat_track(onset_envelope=oenv, sr=SR, hop_length=HOP, units="frames")
    beats = librosa.frames_to_time(bf, sr=SR, hop_length=HOP)
    # phase fix: trackers often lock onto off-beat hats. Kick/low end defines "the one":
    # if low-band (<180 Hz) onsets are stronger half a beat later, shift the whole grid.
    S_lo = librosa.feature.melspectrogram(y=y, sr=SR, n_mels=16, fmax=180, hop_length=HOP)
    lo = librosa.onset.onset_strength(S=librosa.power_to_db(S_lo), sr=SR, hop_length=HOP)
    fr = lambda ts: np.clip(librosa.time_to_frames(ts, sr=SR, hop_length=HOP), 0, len(lo) - 1)
    if len(beats) > 4:
        half = np.median(np.diff(beats)) / 2
        at = lambda ts: np.array([lo[max(0, f - 2):f + 3].max() for f in fr(ts)]).mean()
        if at(beats + half) > 1.25 * at(beats):
            beats = beats + half
        # refine each beat to the strongest onset within ±35 ms (removes frame/DP jitter)
        w = 3; f = fr(beats)
        f = np.array([max(0, k - w) + int(np.argmax(oenv[max(0, k - w):k + w + 1] + lo[max(0, k - w):k + w + 1])) for k in f])
        beats = librosa.frames_to_time(f, sr=SR, hop_length=HOP); bf = f
        tempo = 60.0 / np.mean(np.diff(beats))
    # downbeat phase: of the 4 possible bar phases pick the one with the strongest onsets
    strength = lo[np.clip(bf, 0, len(lo) - 1)]
    phase = int(np.argmax([strength[p::4].mean() if len(strength[p::4]) else 0 for p in range(4)]))
    rms = librosa.feature.rms(y=y, hop_length=512)[0]
    out = dict(file=os.path.abspath(path), dur=len(y) / SR, bpm=float(np.atleast_1d(tempo)[0]),
               beats=[round(float(b), 3) for b in beats], downbeats=[round(float(b), 3) for b in beats[phase::4]],
               rms_t=[round(float(t), 2) for t in librosa.frames_to_time(np.arange(len(rms)), sr=SR)[::10]],
               rms=[round(float(r), 4) for r in rms[::10]])
    os.makedirs(CACHE, exist_ok=True)
    jp = os.path.join(CACHE, os.path.splitext(os.path.basename(path))[0] + ".beats.json")
    json.dump(out, open(jp, "w"))
    return out, jp

def score(off, cuts, punches, beats, downs, sigma=.035):
    def near(ts, grid):
        if not len(grid): return np.full(len(ts), 9.0)
        idx = np.clip(np.searchsorted(grid, ts), 1, len(grid) - 1)
        return np.minimum(abs(grid[idx] - ts), abs(grid[idx - 1] - ts))
    c = np.asarray(cuts) + off; p = np.asarray(punches) + off
    g = lambda d: np.exp(-(d / sigma) ** 2)
    return 2.0 * g(near(c, downs)).sum() + 1.0 * g(near(c, beats)).sum() + 1.0 * g(near(p, beats)).sum()

def snap(reel, track, gain, max_off, autopad=False, max_pad=.35):
    root = os.path.dirname(os.path.abspath(reel))
    tlp = os.path.join(root, "timeline.json")
    if not os.path.exists(tlp): sys.exit("timeline.json missing — run render.py first")
    tl, spec = json.load(open(tlp)), json.load(open(reel))
    info, _ = analyze(track)
    beats, downs = np.array(info["beats"]), np.array(info["downbeats"])
    cuts = sorted({round(s["t0"], 3) for s in tl["shots"][1:]})
    punches = sorted({round(e["t"], 3) for e in tl["events"] if e["type"] in ("punch", "shake", "flash")})
    total = tl["total"]; hi = max(0.0, min(info["dur"] - total, max_off))
    rms_t, rms = np.array(info["rms_t"]), np.array(info["rms"])
    best = (-1, 0.0)
    for off in np.arange(0, hi + 1e-6, 0.01):
        s = score(off, cuts, punches, beats, downs)
        # avoid starting in a quiet intro: small bonus for loud first 2 s
        s += 0.5 * np.interp(off + 1.0, rms_t, rms) / (rms.max() + 1e-9)
        if s > best[0]: best = (s, round(float(off), 2))
    off = best[1]
    rel = os.path.relpath(os.path.abspath(track), root)
    spec["music"] = dict(file=rel if not rel.startswith("..") else os.path.abspath(track), offset=off, gain=gain,
                         bpm=round(info["bpm"], 1))
    json.dump(spec, open(reel, "w"), ensure_ascii=False, indent=2)
    print(f"track {info['bpm']:.1f} BPM, {info['dur']:.1f}s  ->  best offset {off:.2f}s  (score {best[0]:.2f})")
    errs = []
    for kind, ts in (("cut", cuts), ("hit", punches)):
        for t in ts:
            d = beats - (t + off); k = int(np.argmin(abs(d))); errs.append(abs(d[k]))
            print(f"  {kind} @ {t:6.2f}s  nearest beat {1000 * d[k]:+6.0f} ms")
    on = sum(e < .06 for e in errs)
    print(f"{on}/{len(errs)} cuts+hits within 60 ms of a beat. Wrote music block to {os.path.basename(reel)}.")
    if autopad:
        # delay each new VO beat (adds a breath before it) so its opening cut lands on the next beat
        shift, added = 0.0, []
        for i in range(1, len(tl["beats"])):
            t = tl["beats"][i]["t0"] + shift + off
            g = beats[beats >= t - .02]
            if not len(g): break
            need = float(g[0] - t)
            if need < .02 or need > max_pad: added.append(0.0); continue
            prev = spec["beats"][i - 1]; prev["pad"] = round(prev.get("pad", 0.0) + need, 3)
            shift += need; added.append(need)
        spec["music"]["autopadded"] = True
        json.dump(spec, open(reel, "w"), ensure_ascii=False, indent=2)
        print(f"autopad: added {', '.join(f'{a:.2f}' for a in added)} s before beats 2..{len(tl['beats'])} "
              f"(+{shift:.2f}s total). Re-run render.py, then audio.py — do NOT re-snap (offset is locked).")
    print("Tip: misses >150 ms? add  \"pad\": <seconds>  to the preceding beat in reel.json, re-render, re-snap.")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["analyze", "snap"]); ap.add_argument("a"); ap.add_argument("b", nargs="?")
    ap.add_argument("--autopad", action="store_true"); ap.add_argument("--max-pad", type=float, default=.35)
    ap.add_argument("--gain", type=float, default=0.9); ap.add_argument("--max-offset", type=float, default=90)
    x = ap.parse_args()
    if x.cmd == "analyze":
        info, jp = analyze(x.a)
        print(f"{info['bpm']:.1f} BPM, {len(info['beats'])} beats, {len(info['downbeats'])} downbeats, "
              f"{info['dur']:.1f}s -> {jp}")
    else:
        snap(x.a, x.b, x.gain, x.max_offset, x.autopad, x.max_pad)
