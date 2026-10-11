#!/usr/bin/env python3
"""
reelkit/render.py — in-agent viral reel renderer (no paid video model needed).

Fuses the three repos' ideas:
  * vox-director  -> collage keyframes + local motion engine (eased camera, impact shake,
                     punch zoom, confetti, whip cuts, anti-monotony moves, paper grain)
  * Hypit         -> WORD-ANCHORED timeline: every shot cut / effect / caption is pinned to
                     a spoken word ("b2:1" = beat b2, word #1) from ASR, not to seconds;
                     script owns the display text, ASR owns the timing; color-box karaoke.
  * Lightpanda    -> upstream research (facts/trends) that fills reel.json

Usage: python3 render.py <reel.json>      (needs words.json from align step + ffmpeg)
"""
import json, math, os, subprocess, sys, random
os.environ["PATH"] = os.path.expanduser("~/.cache/bin") + os.pathsep + os.environ.get("PATH", "")  # setup.sh tools
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import script as SC

spec_path = sys.argv[1]
SPEC = json.load(open(spec_path))
ROOT = os.path.dirname(os.path.abspath(spec_path))
W, H, FPS = SPEC.get("W", 1080), SPEC.get("H", 1920), SPEC.get("fps", 30)
OS = 1.30                                  # overscan so the camera can move without edges
FONT = SPEC.get("font", os.path.expanduser("~/fonts/Anton-Regular.ttf"))
PAL = [tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) for c in SPEC.get("palette",
       ["#F2B33D", "#D93A2B", "#F3E9D2", "#1C2A4A"])]
HL = PAL[0]                                 # karaoke box / emphasis colour
WORDS = json.load(open(os.path.join(ROOT, "words.json")))
random.seed(7)

# ------------------------------------------------------------------ timeline (word anchors)
beats, t = [], 0.0
for b in SPEC["beats"]:
    d = WORDS[b["vo"]]["dur"] + b.get("pad", 0.0)
    bb = dict(b, t0=t, t1=t + d, words=WORDS[b["vo"]]["words"])
    if "script" in b:
        bb["units"] = SC.timed_units(b["script"], bb["words"])
    beats.append(bb)
    t += d
TOTAL = t + SPEC.get("tail", 0.6)
BEAT = {b["id"]: b for b in beats}


def anchor(a):
    """'b2:1' -> absolute time of word 1 in beat b2;  'b2' -> beat start;  number -> seconds."""
    if isinstance(a, (int, float)):
        return float(a)
    if ":" in a:
        bid, i = a.split(":", 1)
        b = BEAT[bid]
        if "units" in b:
            return b["t0"] + b["units"][SC.find(b["units"], i)]["s"]
        return b["t0"] + b["words"][int(i)]["s"]
    return BEAT[a]["t0"]


# shots: each beat lists shots with a start anchor; build a flat sorted list
SHOTS = []
for b in beats:
    for k, s in enumerate(b["shots"]):
        SHOTS.append(dict(s, t0=b["t0"] if k == 0 else anchor(s["at"])))
for i, s in enumerate(SHOTS):
    s["t1"] = SHOTS[i + 1]["t0"] if i + 1 < len(SHOTS) else TOTAL

# images (pre-scaled once to overscan canvas, cover-fit)
CACHE = {}
def img(path):
    if path not in CACHE:
        im = Image.open(os.path.join(ROOT, path)).convert("RGB")
        BW, BH = int(W * OS), int(H * OS)
        sc = max(BW / im.width, BH / im.height)
        im = im.resize((int(im.width * sc + .5), int(im.height * sc + .5)), Image.LANCZOS)
        l, tp = (im.width - BW) // 2, (im.height - BH) // 2
        CACHE[path] = im.crop((l, tp, l + BW, tp + BH))
    return CACHE[path]

EVENTS = [dict(e, t=anchor(e["at"])) for e in SPEC.get("events", [])]

# ------------------------------------------------------------------ easing + camera
def smooth(p): p = min(max(p, 0), 1); return p * p * (3 - 2 * p)

def cam(shot, t):
    """returns zoom z (>=1 inside overscan) and centre (cx,cy) in 0..1"""
    p = smooth((t - shot["t0"]) / max(.01, shot["t1"] - shot["t0"]))
    fx, fy = shot.get("focus", [0.5, 0.5])
    mv = shot.get("move", "push_in")
    if mv == "push_in":   z, cx, cy = 1.05 + .20 * p, .5 + (fx - .5) * p, .5 + (fy - .5) * p
    elif mv == "pull_out": z, cx, cy = 1.25 - .20 * p, fx + (.5 - fx) * p, fy + (.5 - fy) * p
    elif mv == "tilt_down": z, cx, cy = 1.15, fx, .40 + .20 * p
    elif mv == "tilt_up":  z, cx, cy = 1.15, fx, .60 - .20 * p
    elif mv == "pan_lr":   z, cx, cy = 1.18, .42 + .16 * p, fy
    elif mv == "pan_rl":   z, cx, cy = 1.18, .58 - .16 * p, fy
    else:                  z, cx, cy = 1.06 + .02 * math.sin(t * .8), .5, .5   # static (payoff)
    # word-anchored punch zoom (local engine = snaps are safe, no i2v jump-cut risk)
    for e in EVENTS:
        if e["type"] == "punch" and 0 <= t - e["t"] < .6:
            q = (t - e["t"]) / .6
            z *= 1 + e.get("amt", .10) * (1 - q) ** 2 * (1 if q > .08 else q / .08)
    return z, cx, cy

def shake(t):
    dx = dy = 0.0
    for e in EVENTS:
        if e["type"] == "shake" and 0 <= t - e["t"] < .7:
            u = t - e["t"]; a = e.get("amt", 22) * math.exp(-6 * u)
            dx += a * math.sin(2 * math.pi * 17 * u); dy += a * .6 * math.cos(2 * math.pi * 13 * u)
    return dx, dy

def frame_of(shot, t):
    im = img(shot["img"])
    z, cx, cy = cam(shot, t)
    BW, BH = im.size
    # at z=1 the view is the whole overscan canvas (widest); z>1 zooms in
    vw, vh = BW / z, BH / z
    dx, dy = shake(t)
    x0 = min(max(cx * BW - vw / 2 + dx, 0), BW - vw)
    y0 = min(max(cy * BH - vh / 2 + dy, 0), BH - vh)
    VIEW[id(shot)] = (x0, y0, vw, vh, BW, BH)
    return im.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + vw, y0 + vh))
VIEW = {}

# ------------------------------------------------------------------ overlays
yy, xx = np.mgrid[0:H, 0:W]
VIG = (1 - .38 * (((xx - W / 2) / (W / 1.6)) ** 2 + ((yy - H / 2) / (H / 1.5)) ** 2)).clip(.55, 1)[..., None].astype(np.float32)
# bottom gradient so captions always read
GRAD = np.ones((H, 1, 1), np.float32); g0 = int(H * .62)
GRAD[g0:, 0, 0] = 1 - .45 * ((np.arange(H - g0) / (H - g0)) ** 1.4)
VIG = VIG * GRAD
GRAIN = [np.random.default_rng(i).normal(0, 9, (H // 2, W // 2, 1)).repeat(2, 0).repeat(2, 1).astype(np.float32) for i in range(6)]

CONF = []
def spawn_confetti(t0, n=140):
    for _ in range(n):
        CONF.append(dict(t0=t0, x=random.uniform(0, W), y=random.uniform(-H * .5, -20),
                         vx=random.uniform(-60, 60), vy=random.uniform(380, 820),
                         r=random.uniform(0, 360), vr=random.uniform(-400, 400),
                         w=random.randint(14, 30), h=random.randint(8, 16), c=random.choice(PAL)))
for e in EVENTS:
    if e["type"] == "confetti": spawn_confetti(e["t"], e.get("n", 140))

def draw_confetti(im, t):
    lay = None
    for c in CONF:
        u = t - c["t0"]
        if not (0 <= u < 3.2): continue
        x, y = c["x"] + c["vx"] * u + 30 * math.sin(u * 3 + c["r"]), c["y"] + c["vy"] * u
        if y > H + 40: continue
        if lay is None: lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        a = math.radians(c["r"] + c["vr"] * u); sq = abs(math.cos(u * 6 + c["r"]))
        hw, hh = c["w"] / 2, c["h"] / 2 * (0.25 + .75 * sq)
        pts = [(x + px * math.cos(a) - py * math.sin(a), y + px * math.sin(a) + py * math.cos(a))
               for px, py in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh))]
        d.polygon(pts, fill=c["c"] + (255,))
    if lay is not None: im.alpha_composite(lay)


# ------------------------------------------------------------------ layers: sticker / mouth / lottie
# sticker: {"at":"b2:word","type":"sticker","img":"cutouts/x.png","pos":[.5,.45],"w":.45,
#           "anim":"pop|drop|slide_l|slide_r|slide_up|spin","rot":-4,"until":"b3","boil":true,"scene":false}
# mouth:   {"at":"b2","type":"mouth","beats":["b2"],"sprites":"mouths/","pos":[.62,.48],"w":.12,"rot":0}
#          pos/w are in KEYFRAME coords and follow the camera (push/pan/shake) -> stays on the face
# lottie:  {"at":"b4:word","type":"lottie","file":"fx/burst.json","pos":[.5,.4],"w":.6,"loop":false,"speed":1}
MOUTHS = json.load(open(os.path.join(ROOT, "mouths.json"))) if os.path.exists(os.path.join(ROOT, "mouths.json")) else {}
def ease_back(p, k=1.70158): p = min(max(p, 0), 1) - 1; return 1 + (k + 1) * p ** 3 + k * p ** 2
def ease_bounce(p):
    p = min(max(p, 0), 1)
    for a, b, c in ((1 / 2.75, 0, 0), (2 / 2.75, 1.5 / 2.75, .75), (2.5 / 2.75, 2.25 / 2.75, .9375), (9, 2.625 / 2.75, .984375)):
        if p < a: return 7.5625 * (p - b) ** 2 + c if b else 7.5625 * p * p
    return 1.0
def shot_end_after(t):
    nx = [s["t0"] for s in SHOTS if s["t0"] > t + .05]
    return (nx[0] - WHIP / 2) if nx else TOTAL
WHIP = .22
LAYERS, _SPR = [], {}
for e in EVENTS:
    if e["type"] not in ("sticker", "mouth", "lottie"): continue
    L = dict(e)
    if e["type"] == "mouth":
        bl = [BEAT[b] for b in e.get("beats", [e["at"].split(":")[0]])]
        L["t1"] = anchor(e["until"]) if "until" in e else bl[-1]["t1"]; L["bl"] = bl
        L["spr"] = {k: Image.open(os.path.join(ROOT, os.path.expanduser(e.get("sprites", "mouths/")), k + ".png")).convert("RGBA") for k in "ABCDEFGHX"}
        L["scene"] = True
    else:
        L["t1"] = anchor(e["until"]) if "until" in e else shot_end_after(e["t"])
    if e["type"] == "sticker":
        L["im"] = Image.open(os.path.join(ROOT, os.path.expanduser(e["img"]))).convert("RGBA")
    if e["type"] == "lottie":
        from rlottie_python import LottieAnimation
        L["anim_obj"] = LottieAnimation.from_file(os.path.join(ROOT, os.path.expanduser(e["file"])))
        L["nf"] = L["anim_obj"].lottie_animation_get_totalframe(); L["lfps"] = L["anim_obj"].lottie_animation_get_framerate()
        lw, lh = L["anim_obj"].lottie_animation_get_size(); L["lsize"] = (lw, lh); L["lcache"] = {}
    LAYERS.append(L)
WHIP = .22

def scaled(key, im, w_px):
    k = (key, int(w_px))
    if k not in _SPR:
        if len(_SPR) > 400: _SPR.clear()
        h = max(1, int(im.height * w_px / im.width)); _SPR[k] = im.resize((max(1, int(w_px)), h), Image.LANCZOS)
    return _SPR[k]

def to_screen(L, shot):
    """keyframe-space pos/width -> screen space through the current camera view"""
    px, py = L.get("pos", [.5, .5]); wf = L.get("w", .3)
    v = VIEW.get(id(shot))
    if not L.get("scene") or v is None: return px * W, py * H, wf * W
    x0, y0, vw, vh, BW, BH = v
    return (px * BW - x0) / vw * W, (py * BH - y0) / vh * H, wf * BW * W / vw

def draw_layers(im, t, shot, whipping):
    f = int(t * FPS)
    for L in LAYERS:
        if not (L["t"] <= t < L["t1"]): continue
        if L.get("scene") and whipping: continue
        cx, cy, wpx = to_screen(L, shot)
        u = t - L["t"]; rot = L.get("rot", 0.0); a = 1.0; sc = 1.0
        if L["type"] == "sticker":
            anim, p = L.get("anim", "pop"), u / .38
            if anim == "pop": sc = ease_back(p, 2.2) if p < 1 else 1
            elif anim == "drop": cy -= (1 - ease_bounce(p)) * (cy + wpx)
            elif anim == "slide_l": cx -= (1 - ease_back(p, 1.2)) * (cx + wpx)
            elif anim == "slide_r": cx += (1 - ease_back(p, 1.2)) * (W - cx + wpx)
            elif anim == "slide_up": cy += (1 - ease_back(p, 1.2)) * (H - cy + wpx)
            elif anim == "spin": sc = ease_back(p, 1.6) if p < 1 else 1; rot += (1 - smooth(p)) * 200
            out = (L["t1"] - t) / .12                                     # quick shrink-out
            if out < 1 and L["t1"] < TOTAL - .1: sc *= max(out, 0)
            if L.get("boil", True):                                       # stop-motion boil @ 8 fps
                r = random.Random(int(t * 8) * 7919 + id(L) % 997); cx += r.uniform(-2, 2); cy += r.uniform(-2, 2); rot += r.uniform(-.7, .7)
            spr = scaled(id(L), L["im"], max(2, wpx * max(sc, .01)))
        elif L["type"] == "mouth":
            shape = "X"
            for b in L["bl"]:
                if b["t0"] <= t < b["t1"]:
                    for c in MOUTHS.get(b["vo"], []):
                        if c["s"] <= t - b["t0"] < c["e"]: shape = c["v"]; break
            spr = scaled(("m", shape, id(L)), L["spr"][shape], wpx)
        else:  # lottie
            fi = int(u * L["lfps"] * L.get("speed", 1))
            if L.get("loop", False): fi %= L["nf"]
            elif fi >= L["nf"]: continue
            lw, lh = L["lsize"]; tw = int(wpx); th = int(lh * tw / lw); key = (fi, tw)
            if key not in L["lcache"]:
                if len(L["lcache"]) > 240: L["lcache"].clear()
                L["lcache"][key] = L["anim_obj"].render_pillow_frame(frame_num=fi, width=tw, height=th).convert("RGBA")
            spr = L["lcache"][key]
        if sc <= .01: continue
        if abs(rot) > .05: spr = spr.rotate(rot, Image.BICUBIC, expand=True)
        comp_clip(im, spr, int(cx - spr.width / 2), int(cy - spr.height / 2))

def comp_clip(im, spr, x, y):
    """alpha_composite that tolerates partly/fully off-screen sprites (slide-ins)"""
    l, t_ = max(0, -x), max(0, -y); r, b = min(spr.width, W - x), min(spr.height, H - y)
    if r <= l or b <= t_: return
    im.alpha_composite(spr.crop((l, t_, r, b)) if (l or t_ or r < spr.width or b < spr.height) else spr, (x + l, y + t_))

# ------------------------------------------------------------------ captions (Hypit color-box karaoke)
CUES = []   # each cue: list of (display, start, end, emph)
for b in beats:
    if "units" in b:
        us = [u for u in b["units"]]
        for k, u in enumerate(us):
            u["e2"] = us[k + 1]["s"] if k + 1 < len(us) else u["e"] + .45
        cue = []
        for u in us:
            if u["brk"] and cue: CUES.append(cue); cue = []
            if u["display"]: cue.append((u["display"], b["t0"] + u["s"], b["t0"] + u["e2"], u["emph"]))
        if cue: CUES.append(cue)
        continue
    ws = b["words"]; disp = b.get("display")  # optional overrides: {index: text}
    tokens = []
    for i, w in enumerate(ws):
        txt = (disp or {}).get(str(i), w["w"])
        if txt == "": continue
        tokens.append([txt, b["t0"] + w["s"], None, i])
    for k, tk in enumerate(tokens):
        tk[2] = tokens[k + 1][1] if k + 1 < len(tokens) else tk[1] + .45
    groups = b["cues"]        # list of [first_idx, last_idx] word ranges (Hypit '||' handoffs)
    emph = set(b.get("emph", []))
    for g0_, g1_ in groups:
        cue = [(tx, s, e, i in emph) for tx, s, e, i in tokens if g0_ <= i <= g1_]
        if cue: CUES.append(cue)
for k, c in enumerate(CUES):
    nxt = CUES[k + 1][0][1] if k + 1 < len(CUES) else TOTAL
    CUES[k] = (c, c[0][1] - .05, min(nxt, c[-1][2] + .6))

FS = SPEC.get("caption_size", 104)
FNT = ImageFont.truetype(FONT, FS)
CAP_Y = SPEC.get("caption_y", 0.70)

def draw_caption(im, t):
    cur = [c for c in CUES if c[1] <= t < c[2]]
    if not cur: return
    words, cs, ce = cur[0]
    d = ImageDraw.Draw(im)
    toks = [(w.upper() if not SPEC.get("rtl") else w, s, e, em) for w, s, e, em in words]
    sp = FS * .28
    sizes = [d.textbbox((0, 0), w, font=FNT) for w, *_ in toks]
    widths = [bb[2] - bb[0] for bb in sizes]
    # wrap to <= 920px lines
    lines, line, lw = [], [], 0
    for i, wd in enumerate(widths):
        if line and lw + sp + wd > 920: lines.append(line); line, lw = [], 0
        lw += (sp if line else 0) + wd; line.append(i)
    lines.append(line)
    pop = smooth((t - cs) / .12)                     # cue pops in
    lh = FS * 1.22
    y = H * CAP_Y - lh * len(lines) / 2 + (1 - pop) * 30
    for ln in lines:
        tw = sum(widths[i] for i in ln) + sp * (len(ln) - 1)
        x = W / 2 - tw / 2
        for i in (reversed(ln) if SPEC.get("rtl") else ln):    # Urdu/Arabic: right-to-left word order
            w, s, e, em = toks[i]
            active = s <= t < e
            bb = sizes[i]
            if active:   # mustard box behind current word, slight pop
                pad = 16
                d.rounded_rectangle((x - pad, y + bb[1] - pad * .7, x + widths[i] + pad, y + bb[3] + pad * .7),
                                    radius=14, fill=HL)
                d.text((x, y), w, font=FNT, fill=(20, 20, 20))
            else:
                col = HL if em and t >= s else (255, 255, 255)
                d.text((x, y), w, font=FNT, fill=col, stroke_width=9, stroke_fill=(10, 10, 10))
            x += widths[i] + sp
        y += lh

# ------------------------------------------------------------------ main loop
# intermediates live in ~/.cache/tmp (not snapshotted) so reel dirs stay small
SCRATCH = os.path.expanduser("~/.cache/tmp/" + os.path.basename(ROOT)); os.makedirs(SCRATCH, exist_ok=True)
out = os.path.join(ROOT, SPEC["video_out"]) if "video_out" in SPEC else os.path.join(SCRATCH, "video_noaudio.mp4")
ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                       "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast",
                       "-crf", "19", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
WHIP = .22
N = int(TOTAL * FPS)
for f in range(N):
    t = f / FPS
    si = max(i for i, s in enumerate(SHOTS) if s["t0"] <= t + 1e-6)
    sh = SHOTS[si]
    base = frame_of(sh, t); whipping = False
    # whip transition into a shot (slide + directional blur), skipped for the very first shot
    if si > 0 and t - sh["t0"] < WHIP / 2 and SHOTS[si].get("cut", "whip") == "whip":
        prev = frame_of(SHOTS[si - 1], t)
        q = .5 + (t - sh["t0"]) / WHIP
        off = int(W * smooth(q))
        comp = Image.new("RGB", (W, H)); comp.paste(prev, (-off, 0)); comp.paste(base, (W - off, 0))
        base = comp; whipping = True
    elif si + 1 < len(SHOTS) and SHOTS[si + 1]["t0"] - t < WHIP / 2 and SHOTS[si + 1].get("cut", "whip") == "whip":
        nxt = frame_of(SHOTS[si + 1], t)
        q = .5 - (SHOTS[si + 1]["t0"] - t) / WHIP
        off = int(W * smooth(q))
        comp = Image.new("RGB", (W, H)); comp.paste(base, (-off, 0)); comp.paste(nxt, (W - off, 0))
        base = comp; whipping = True
    a = np.asarray(base, np.float32)
    if whipping:                                     # motion blur on whip frames
        a = sum(np.roll(a, k, axis=1) for k in (-48, -24, 0, 24, 48)) / 5
    a = a * VIG + GRAIN[(f // 2) % 6]
    for e in EVENTS:                                  # word-anchored colour flash
        if e["type"] == "flash" and 0 <= t - e["t"] < .28:
            al = .55 * (1 - (t - e["t"]) / .28); col = np.array(e.get("color", [255, 255, 255]), np.float32)
            a = a * (1 - al) + col * al
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8)).convert("RGBA")
    draw_layers(im, t, sh, whipping)
    draw_confetti(im, t)
    draw_caption(im, t)
    ff.stdin.write(im.convert("RGB").tobytes())
    if f % 150 == 0: print(f"frame {f}/{N}", flush=True)
ff.stdin.close(); ff.wait()
json.dump(dict(total=TOTAL, beats=[dict(id=b["id"], t0=b["t0"], t1=b["t1"]) for b in beats],
               shots=[dict(img=s["img"], t0=s["t0"]) for s in SHOTS],
               events=[dict(type=e["type"], t=e["t"], sfx=e.get("sfx")) for e in EVENTS]),
          open(os.path.join(ROOT, "timeline.json"), "w"), indent=1)
print("wrote", out, f"{TOTAL:.2f}s")
