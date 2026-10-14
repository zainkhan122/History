#!/usr/bin/env python3
"""Generates the HyperFrames composition (index.html) for Paper Trail File 02 — the Carrington Event — from timeline.json.
One paused GSAP timeline, fully deterministic (seeded LCG, no Date/Math.random), local fonts + GSAP.
House style = File 01 (paper, ink/red strips, typed labels, stamps, karaoke strips); motion = 2 Wan plates,
5 public-domain NASA clips (full-bleed footage + projected film inserts) and animated graphics.
usage: python3 build.py <hf_dir>"""
import json, math, re, sys, html
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "engine")); import fx
HF = Path(sys.argv[1] if len(sys.argv) > 1 else Path.home() / ".cache/build/ep02-carrington/hf")
TL = json.load(open(HERE / "timeline.json"))
C, SC, TOTAL, WORDS = TL["cues"], {s["id"]: s for s in TL["scenes"]}, TL["total"], TL["words"]
SC["s01"] = {**SC["s01"], "start": 0.0}   # the opening plate is on screen from frame 0 (VO starts at 0.35)
CLIPS = {c["id"]: c for c in json.load(open(HERE / "clips.json"))["clips"]}
TYPE_RATE = 22.0                      # chars/s — must match score.py
INK, CREAM, RED, MUSTARD = "#141414", "#F4ECD8", "#C8102E", "#E3A72F"
RED_ON_LIGHT, RED_ON_DARK = "#A50B25", "#FF4D4D"   # readable reds: text on paper / text on dark (textqa ≥ 4.5:1)
NIGHT = "#0E1116"

body, js = [], []                     # html chunks, js timeline lines
def J(s): js.append(s)
FX = fx.FX(J, HERE / "clips.json", SC, seed=1859, hf=HF)
def f(x): return f"{x:.3f}"

_seed = [1859]
def rnd():
    _seed[0] = (_seed[0] * 1103515245 + 12345) % 2147483648
    return _seed[0] / 2147483648

def shake(sel, t, dur=0.45, amp=18):
    steps = max(3, int(dur / 0.045)); out = []; sel = FX.shake_targets(sel)
    for i in range(steps):
        a = amp * (1 - i / steps)
        out.append(f"tl.to('{sel}',{{x:{(rnd()*2-1)*a:.1f},y:{(rnd()*2-1)*a:.1f},rotation:{(rnd()*2-1)*a*0.04:.2f},duration:0.043,ease:'none'}},{f(t+i*0.045)});")
    out.append(f"tl.to('{sel}',{{x:0,y:0,rotation:0,duration:0.06,ease:'power1.out'}},{f(t+steps*0.045)});")
    J("\n".join(out))

def clip(id_, start, end, inner, z=10, extra_cls="", style=""):
    body.append(f'<div id="{id_}" class="clip {extra_cls}" data-start="{f(start)}" data-duration="{f(end-start)}" '
                f'data-track-index="{z//10}" style="z-index:{z};{style}">{inner}</div>')

def kb(id_, img, overlays="", style=""):
    return f'<div id="{id_}" class="kb" style="{style}">{FX.plate(img, id_)}{overlays}</div>'

def kb_move(sel, t0, t1, s0, s1, x0=0, x1=0, y0=0, y1=0, ease="none"):
    sel = FX.kb_targets(sel)
    J(f"tl.fromTo('{sel}',{{scale:{s0},x:{x0},y:{y0}}},{{scale:{s1},x:{x1},y:{y1},duration:{f(t1-t0)},ease:'{ease}',immediateRender:false}},{f(t0)});")

def tag(id_, text, x, y, size=40, rot=-1.5, extra="", attrs=""):
    chars = "".join(f'<span class="ch" id="{id_}_{i}" {attrs}>{html.escape(c) if c != " " else "&nbsp;"}</span>' for i, c in enumerate(text))
    return f'<div id="{id_}" class="tag" style="left:{x}px;top:{y}px;font-size:{size}px;transform:rotate({rot}deg);{extra}">{chars}</div>'

def type_anim(id_, text, t0):
    J(f"tl.fromTo('#{id_}',{{autoAlpha:0,scale:0.9}},{{autoAlpha:1,scale:1,duration:0.12,ease:'back.out(2)',immediateRender:false}},{f(t0-0.14)});")
    for i, _ in enumerate(text):
        J(f"tl.set('#{id_}_{i}',{{opacity:1}},{f(t0+i/TYPE_RATE)});")

def stamp(id_, lines, x, y, rot, size=90, color=RED):
    inner = "<br>".join(html.escape(l) for l in lines)
    return (f'<div id="{id_}" class="stamp" data-layout-allow-occlusion="true" data-layout-allow-overlap="true" style="left:{x}px;top:{y}px;font-size:{size}px;color:{color};border-color:{color};'
            f'--rot:{rot}deg;transform:rotate({rot}deg)">{inner}</div>')

def stamp_anim(id_, t, rot):
    J(f"tl.fromTo('#{id_}',{{autoAlpha:0,scale:2.3,rotation:{rot-6}}},{{autoAlpha:0.93,scale:1,rotation:{rot},duration:0.13,ease:'power4.in',immediateRender:false}},{f(t-0.13)});")

def pop(sel, t, dur=0.3, y=20):
    J(f"tl.fromTo('{sel}',{{autoAlpha:0,y:{y}}},{{autoAlpha:1,y:0,duration:{dur},ease:'power2.out',immediateRender:false}},{f(t)});")

def credit(text, x, y, w=840, dark=False):
    """On-screen archive credit (provenance gate needs it visible)."""
    cls = "credit dark" if dark else "credit"
    return f'<div class="{cls}" data-tq-dwell="off" style="position:absolute;left:{x}px;top:{y}px;width:{w}px">{html.escape(text)}</div>'

SAFE_TOP = 230          # platform UI: top bar ends y=210, bottom UI from y=1600, right action column x>960 below y=640
TYPED = {i: (t, txt) for t, txt, i in TL["typed"]}
def typed(id_, x, y, size=40, rot=-1.5, extra="", attrs=""):
    t, txt = TYPED[id_]; type_anim(id_, txt, t); return tag(id_, txt, x, y, size, rot, extra, attrs)

def tear(t):
    J(f"tl.fromTo('#tear',{{x:1120,autoAlpha:1}},{{x:-260,autoAlpha:1,duration:0.30,ease:'power3.in',immediateRender:false}},{f(t-0.30)});")
    J(f"tl.to('#tear',{{x:-1800,duration:0.34,ease:'power2.in'}},{f(t+0.02)});")
    J(f"tl.set('#tear',{{autoAlpha:0}},{f(t+0.37)});")

def sc(c): return CLIPS[c]["screen_credit"]

# ======================= BACKGROUND (paper) =======================
clip("bg", 0, TOTAL, '<img src="assets/bg_paper.jpg" style="width:100%;height:100%;object-fit:cover" alt="">', z=0)

# ======================= S1 — the key that kept talking (hook) =======================
s = SC["s01"]
title = ('<div id="title" class="title" data-layout-allow-overlap="true">'
         '<div class="strip ink" id="tl1" data-layout-allow-overlap="true">THE DAY THE SKY</div>'
         '<div class="strip red" id="tl2" data-layout-allow-overlap="true">RAN THE TELEGRAPH</div>'
         '<div class="kicker" id="tl3">— and why it matters now</div></div>')
clip("sc01", 0, s["end"], kb("kb01", "s01_telegraph") + title)
kb_move("#kb01", 0, 1.0, 1.0, 0.9, 0, 0, -30, 0, "expo.out")
kb_move("#kb01", 1.0, s["end"], 0.9, 0.98, 0, 0, 0, 40)
J("tl.fromTo('#title',{scale:1.08},{scale:1,duration:0.5,ease:'power3.out',immediateRender:false},0);")
J("tl.fromTo('#tl3',{autoAlpha:0,y:10},{autoAlpha:1,y:0,duration:0.35,immediateRender:false},0.05);")
J("tl.to('#title',{autoAlpha:0,y:-60,duration:0.35,ease:'power2.in'},2.75);")
FX.flash(C["unplugged"] + 0.1, 0.35)                      # the key sparks as the battery comes off
aur0, aur1 = C["power"] - 0.3, s["end"] + 0.4
if FX.footage("kbA", "arch_aurora", aur0, aur1):          # full-bleed NASA aurora: "the power was coming from the sky"
    J(f"tl.fromTo('#kbA_vs',{{autoAlpha:0}},{{autoAlpha:1,duration:0.5,ease:'power1.inOut',immediateRender:false}},{f(aur0)});")
    J(f"tl.fromTo('#kbA_vw',{{scale:1.12}},{{scale:1.0,duration:{f(aur1-aur0)},ease:'none',immediateRender:false}},{f(aur0)});")
    J(f"tl.to('#kb01',{{autoAlpha:0,duration:0.4}},{f(aur0 + 0.2)});")
    clip("crA", aur0, aur1, credit(sc("arch_aurora"), 120, 1250, dark=True), z=12)
    pop("#crA .credit", aur0 + 0.3)

# ======================= S2 — Redhill, 11:18 a.m.: the drawing =======================
s = SC["s02"]
p2, p3 = C["carrington"] - 0.15, C["patches"] - 0.25
obs = ('<div id="obs" class="card print" style="left:66px;top:560px;--r:-2deg">'
       '<img src="assets/redhill_observatory.jpg" style="width:948px;height:656px" alt="">'
       '<div class="tape" style="left:-40px;top:-14px;transform:rotate(-28deg)"></div>'
       '<div class="tape" style="right:-40px;top:-14px;transform:rotate(30deg)"></div></div>'
       + credit("Archive: Redhill Observatory, 1857 engraving · Public Domain", 120, 1250))
clip("sc02a", s["start"], p2 + 0.05, obs + typed("t_date", 56, SAFE_TOP + 70, 42, -1.2) + typed("t_place", 56, SAFE_TOP + 146, 36, 0.8))
J(f"tl.fromTo('#obs',{{y:-1400,rotation:-12}},{{y:0,rotation:-2,duration:0.55,ease:'back.out(1.1)',immediateRender:false}},{f(s['start'])});")
J(f"tl.to('#obs',{{scale:1.06,y:20,duration:{f(p2-s['start']-0.55)},ease:'none'}},{f(s['start']+0.55)});")

portrait = ('<div id="por" class="card print" style="left:610px;top:270px;--r:4deg">'
            '<img src="assets/carrington_portrait.jpg" style="width:340px;height:407px" alt=""></div>'
            '<div class="tape" style="left:720px;top:250px;transform:rotate(-6deg)"></div>')
nametag = tag("t_name", "R. C. CARRINGTON · ASTRONOMER", 300, 740, 34, -1.0)
clip("sc02b", p2, p3 + 0.05, kb("kb02", "s02_sketch") + portrait + nametag +
     credit("Archive: R. C. Carrington · photo Maull & Polyblank · Public Domain", 300, 815, 640))
kb_move("#kb02", p2, p3 + 0.05, 1.08, 0.96, 0, -30, -60, 40)
J(f"tl.fromTo('#por',{{x:500,rotation:18}},{{x:0,rotation:4,duration:0.45,ease:'back.out(1.2)',immediateRender:false}},{f(p2+0.15)});")
type_anim("t_name", "R. C. CARRINGTON · ASTRONOMER", C["carrington"] + 0.25)

# Carrington's own drawing (crop box in make_assets.py: DRAW_BOX = 0.42,0.12 → 0.98,0.98); spot positions measured on it
DW, DL, DT = 900, 90, 300
def dpos(x, y): return DL + 20 + x * DW, DT + 20 + y * DW
PTS = {"A": (0.380, 0.634), "B": (0.451, 0.529), "C": (0.582, 0.738), "D": (0.641, 0.674)}
glows = "".join(f'<div id="g{k}" class="glow" style="left:{dpos(*PTS[k])[0]:.0f}px;top:{dpos(*PTS[k])[1]:.0f}px"></div>' for k in "AB")
rings = "".join(f'<div id="r{k}" class="ring tu" style="left:{dpos(*PTS[k])[0] - 32:.0f}px;top:{dpos(*PTS[k])[1] - 150:.0f}px">{k}</div>' for k in "AB")
drawing = ('<div class="wash" style="background:radial-gradient(ellipse at 50% 40%,#2a2620 0%,#0e0c0a 80%)"></div>'
           f'<div id="draw" class="card" style="left:{DL}px;top:{DT}px;--r:0deg;padding:20px">'
           f'<img src="assets/carrington_drawing.jpg" style="width:{DW}px;height:{DW}px" alt=""></div>' + glows + rings
           + credit("Archive: Carrington's drawing of the flare, 1 Sept 1859 · MNRAS 20 · Public Domain", 120, 1260, dark=True))
clip("sc02c", p3, s["end"], drawing)
J(f"tl.fromTo('#draw',{{scale:1.18,autoAlpha:0}},{{scale:1,autoAlpha:1,duration:0.3,ease:'power3.out',immediateRender:false}},{f(p3)});")
J(f"tl.to('#draw',{{scale:1.05,duration:{f(s['end']-p3-0.3)},ease:'none'}},{f(p3+0.3)});")
for i, k in enumerate("AB"):          # the two white patches break out at A and B …
    t = C["patches"] + 0.25 + i * 0.35
    J(f"tl.fromTo('#g{k}',{{autoAlpha:0,scale:0.2}},{{autoAlpha:1,scale:1,duration:0.35,ease:'back.out(2)',immediateRender:false}},{f(t)});")
    J(f"tl.to('#g{k}',{{scale:1.6,duration:0.25,ease:'power2.out',yoyo:true,repeat:1}},{f(C['white'])});")
    J(f"tl.fromTo('#r{k}',{{autoAlpha:0,y:-16}},{{autoAlpha:1,y:0,duration:0.25,ease:'back.out(2)',immediateRender:false}},{f(t+0.15)});")
FX.flash(C["broke"], 0.5)
for k, dst in (("A", "C"), ("B", "D")):   # … and travel to C and D, fading (Carrington's description)
    (x0, y0), (x1, y1) = dpos(*PTS[k]), dpos(*PTS[dst])
    J(f"tl.to('#g{k}',{{x:{x1-x0:.0f},y:{y1-y0:.0f},scale:0.45,autoAlpha:0.25,duration:{f(s['end']-C['broke']-0.5)},ease:'sine.in'}},{f(C['broke']+0.35)});")
    J(f"tl.to('#r{k}',{{autoAlpha:0,duration:0.3}},{f(C['broke']+0.4)});")

# ======================= S3 — five minutes (archive film: SDO flare) =======================
s = SC["s03"]
ins03 = FX.film_insert("ins03", "arch_flare", s["start"], s["end"], "11:18 → 11:23", sc("arch_flare"), dy=-100)
ring = ('<svg id="sixty" class="sixty" viewBox="0 0 220 220" width="220" height="220">'
        '<circle cx="110" cy="110" r="92" fill="rgba(246,238,220,.92)" stroke="#141414" stroke-width="6"/>'
        f'<circle id="sweep" cx="110" cy="110" r="92" fill="none" stroke="{RED}" stroke-width="14" stroke-dasharray="578" stroke-dashoffset="578" transform="rotate(-90 110 110)"/></svg>')
clip("sc03", s["start"], s["end"], ins03 + ring + stamp("st60", ["60 SECONDS"], 70, SAFE_TOP + 40, -4, 84)
     + '<div id="blk03" class="wash" style="background:#000;opacity:0"></div>')
J(f"tl.fromTo('#sc03',{{scale:1.25,filter:'blur(10px)'}},{{scale:1,filter:'blur(0px)',duration:0.32,ease:'power3.out',immediateRender:false}},{f(s['start'])});")
J(f"tl.fromTo('#sixty',{{autoAlpha:0,scale:0.6}},{{autoAlpha:1,scale:1,duration:0.2,ease:'back.out(2)',immediateRender:false}},{f(C['sixty']-0.1)});")
J(f"tl.to('#sweep',{{attr:{{'stroke-dashoffset':0}},duration:1.1,ease:'none'}},{f(C['sixty'])});")
stamp_anim("st60", C["sixty"] + 0.25, -4)
shake("#sc03", C["sixty"] + 0.25, 0.25, 8)
J(f"tl.to('#sixty,#st60',{{autoAlpha:0,duration:0.3}},{f(C['five']-0.2)});")
J(f"tl.to('#blk03',{{opacity:1,duration:0.7,ease:'power2.in'}},{f(C['gone']-0.25)});")

# ======================= S4 — +17 hours: the field shakes; the sky turns red =======================
s = SC["s04"]
ins0 = C["blood"] - 0.3
gx = [i * 6 for i in range(151)]; brk = (C["shake"] - (s["start"] + 0.25)) / (ins0 - s["start"] - 0.25)
pts = []
for i, x in enumerate(gx):
    u = x / 900
    a = 7 + (0 if u < brk else 210 * min(1, (u - brk) / 0.12))
    y = 300 + a * math.sin(i * (0.35 if u < brk else 1.7)) * (0.6 + 0.4 * rnd()) + (0 if u < brk else (rnd() - .5) * a * .8)
    pts.append(f"{x + 20},{max(25, min(575, y)):.1f}")
trace = ('<div id="graph" class="graph"><svg viewBox="0 0 940 600" width="940" height="600">'
         f'<polyline id="trace" points="{" ".join(pts)}" fill="none" stroke="{RED}" stroke-width="5" stroke-linejoin="round" stroke-dasharray="6000" stroke-dashoffset="6000"/></svg>'
         '<div class="glabel tu">EARTH\'S MAGNETIC FIELD</div></div>')
clip("sc04", s["start"], ins0 + 0.05, trace + typed("t_hours", 300, SAFE_TOP + 50, 76, -2.0)
     + '<div id="red04" class="wash" style="opacity:0;background:radial-gradient(ellipse at 50% 45%,rgba(200,16,46,0.05),rgba(200,16,46,0.55))"></div>')
J(f"tl.fromTo('#graph',{{autoAlpha:0,y:60}},{{autoAlpha:1,y:0,duration:0.35,ease:'power2.out',immediateRender:false}},{f(s['start']+0.05)});")
J(f"tl.to('#trace',{{attr:{{'stroke-dashoffset':0}},duration:{f(ins0-s['start']-0.25)},ease:'none'}},{f(s['start']+0.25)});")
J(f"tl.fromTo('#red04',{{opacity:0}},{{opacity:1,duration:0.4,immediateRender:false}},{f(C['shake'])});")
shake("#sc04", C["shake"], 0.7, 16)
ins04 = FX.film_insert("ins04", "arch_iss_aurora", ins0, s["end"], "AURORA SEEN AS FAR SOUTH AS CUBA", sc("arch_iss_aurora"), dy=-150)
clip("sc04b", ins0, s["end"], ins04 + '<div class="wash" style="background:rgba(200,16,46,.16);mix-blend-mode:multiply;pointer-events:none"></div>', z=11)
FX.flash(ins0 + 0.02, 0.6)

# ======================= S5 — campers make breakfast at 1 a.m. (Wan) =======================
s = SC["s05"]
clip("sc05", s["start"], s["end"], kb("kb05", "s05_campers") + typed("t_rmn", 56, SAFE_TOP + 70, 40, -1.2))
kb_move("#kb05", s["start"], s["end"], 0.92, 1.02, 0, 0, 40, -20)
FX.light_leak(C["dawn"] - 0.3, 2.6, 0.6)

# ======================= S6 — lines go wild: sparks, shocks, fire =======================
s = SC["s06"]
def bolt(x, y, n=7, step=34):
    p, cx, cy = [], x, y
    for _ in range(n):
        p.append(f"{cx:.0f},{cy:.0f}"); cx += (rnd() - 0.3) * step; cy += (rnd() - 0.5) * step * 1.4
    return " ".join(p)
arcs = "".join(f'<polyline id="bz{i}" class="bz" points="{bolt(x, y)}"/>' for i, (x, y) in
               enumerate([(250, 1020), (330, 980), (460, 1040), (560, 990), (300, 1100), (520, 1080)]))
clip("sc06", s["start"], s["end"], kb("kb06", "s06_office")
     + f'<svg class="arcsvg" viewBox="0 0 1080 1920" width="1080" height="1920">{arcs}</svg>'
     + stamp("st8h", ["MANY LINES UNUSABLE FOR 8+ HOURS"], 56, SAFE_TOP + 70, -3, 54))
kb_move("#kb06", s["start"], s["end"], 1.0, 1.09, 0, 20, 0, -40)
for t0, n in ((C["sparks"], 14), (C["shocks"], 8), (C["fire"], 8)):
    for k in range(n):
        i = int(rnd() * 6); t = t0 + k * 0.07
        J(f"tl.set('#bz{i}',{{opacity:1}},{f(t)});"); J(f"tl.set('#bz{i}',{{opacity:0}},{f(t + 0.05)});")
FX.flash(C["sparks"], 0.5); FX.flash(C["shocks"], 0.4)
shake("#sc06", C["shocks"], 0.5, 18)
stamp_anim("st8h", C["shocks"] + 0.35, -3)
FX.film_burn(C["fire"] + 0.35, 0.6)

# ======================= S7 — Boston ⇄ Portland on the aurora's current =======================
s = SC["s07"]
B, P = (250, 650), (700, 380)         # pin centres (map is schematic: Portland, Maine lies NE of Boston)
wire = (f'<svg class="wiresvg" viewBox="0 0 1080 1920" width="1080" height="1920">'
        f'<path id="wire" d="M {B[0]} {B[1]} C {B[0]+120} {B[1]-40}, {P[0]-180} {P[1]+120}, {P[0]} {P[1]}" stroke="{CREAM}" stroke-width="5" fill="none" stroke-dasharray="900" stroke-dashoffset="900"/>'
        f'<path id="wire2" d="M {B[0]} {B[1]} C {B[0]+120} {B[1]-40}, {P[0]-180} {P[1]+120}, {P[0]} {P[1]}" stroke="#7CFFB0" stroke-width="9" fill="none" stroke-linecap="round" stroke-dasharray="40 860" stroke-dashoffset="0" opacity="0"/></svg>')
nodes = (f'<div id="nB" class="node" style="left:{B[0]-40}px;top:{B[1]-36}px"><span class="pin"></span>BOSTON</div>'
         f'<div id="nP" class="node" style="left:{P[0]-40}px;top:{P[1]-36}px"><span class="pin"></span>PORTLAND</div>')
QUOTE = "“MINE IS DISCONNECTED, AND WE ARE WORKING WITH THE AURORAL CURRENT.”"
telegram = ('<div id="tgm" class="telegram"><div class="tghead tu">BOSTON OPERATOR · 2 SEPT. 1859</div><div class="tu">'
            + "".join(f'<span class="tq" id="tq_{i}">{html.escape(ch) if ch != " " else " "}</span>' for i, ch in enumerate(QUOTE)) + '</div></div>')
sky = ('<div class="wash" style="background:linear-gradient(180deg,#07130f 0%,#0b1c18 45%,#121212 100%)"></div>'
       '<div id="aur7" class="aur7"></div>')
clip("sc07", s["start"], s["end"], sky + wire + nodes + telegram + stamp("st2h", ["≈ 2 HOURS · NO BATTERIES"], 110, 1130, -4, 62, RED_ON_LIGHT))
J(f"tl.fromTo('#aur7',{{xPercent:-12,opacity:0.5}},{{xPercent:12,opacity:0.9,duration:{f(s['end']-s['start'])},ease:'sine.inOut',immediateRender:false}},{f(s['start'])});")
pop("#nB", C["boston"] - 0.1, 0.25); pop("#nP", C["portland"] - 0.1, 0.25)
J(f"tl.to('#wire',{{attr:{{'stroke-dashoffset':0}},duration:0.7,ease:'power2.inOut'}},{f(C['portland'])});")
J(f"tl.set('#wire2',{{opacity:1}},{f(C['disconnected']+0.3)});")
J(f"tl.fromTo('#wire2',{{attr:{{'stroke-dashoffset':0}}}},{{attr:{{'stroke-dashoffset':-1800}},duration:{f(s['end']-C['disconnected']-0.3)},ease:'none',immediateRender:false}},{f(C['disconnected']+0.3)});")
J(f"tl.fromTo('#tgm',{{autoAlpha:0,y:80,rotation:3}},{{autoAlpha:1,y:0,rotation:-1,duration:0.4,ease:'back.out(1.3)',immediateRender:false}},{f(C['disconnected']-0.2)});")
for i, _ in enumerate(QUOTE):
    J(f"tl.set('#tq_{i}',{{opacity:1}},{f(C['disconnected'] + 0.25 + i / TYPE_RATE)});")
stamp_anim("st2h", C["hours"] + 0.1, -4)
shake("#sc07", C["hours"] + 0.1, 0.25, 8)
FX.light_leak(C["alone"] - 0.4, 2.0, 0.45)

# ======================= S8 — "One swallow does not make a summer" =======================
s = SC["s08"]
por8 = ('<div id="por8" class="card print" style="left:260px;top:262px;--r:-2deg">'
        '<img src="assets/carrington_portrait.jpg" style="width:560px;height:671px" alt=""></div>'
        + credit("Archive: R. C. Carrington · photo Maull & Polyblank · Public Domain", 120, 978))
chips = ('<div id="chF" class="chip tu" style="left:110px">FLARE</div><div id="chS" class="chip tu" style="left:640px">STORM</div>'
         f'<svg id="link" class="link" viewBox="0 0 1080 200" width="1080" height="200"><line id="lnk" x1="420" y1="100" x2="640" y2="100" stroke="{INK}" stroke-width="7" stroke-dasharray="18 14" stroke-dashoffset="220"/></svg>'
         '<div id="qm" class="qmk tu">?</div>')
swallow = ('<svg id="swl" class="swl" viewBox="0 0 120 60" width="180" height="90">'
           f'<path d="M0 22 Q30 18 52 30 Q60 8 78 0 Q70 22 72 32 Q96 30 120 40 Q86 40 70 44 L60 60 L54 44 Q28 40 0 22 Z" fill="{INK}"/></svg>')
quote8 = ('<div id="q8" class="q8" data-tq-spoken="true"><div class="q8t tu">“One swallow does not make a summer.”</div>'
          '<div class="q8by tu">R. C. CARRINGTON · ROYAL ASTRONOMICAL SOCIETY · NOV. 1859</div></div>')
clip("sc08", s["start"], s["end"], '<img src="assets/paper_dark.jpg" class="wash" style="object-fit:cover" alt="">' + por8 + chips + swallow + quote8)
J(f"tl.fromTo('#por8',{{y:-1500,rotation:-14}},{{y:0,rotation:-2,duration:0.55,ease:'back.out(1.05)',immediateRender:false}},{f(s['start'])});")
J(f"tl.to('#por8',{{scale:1.03,duration:{f(s['end']-s['start']-0.55)},ease:'none'}},{f(s['start']+0.55)});")
pop("#chF", C["flare"] - 0.05, 0.25); pop("#chS", C["storm"] - 0.05, 0.25)
J(f"tl.to('#lnk',{{attr:{{'stroke-dashoffset':0}},duration:0.5,ease:'none'}},{f(C['connected']-0.6)});")
J(f"tl.fromTo('#qm',{{autoAlpha:0,scale:2.4}},{{autoAlpha:1,scale:1,duration:0.18,ease:'power4.in',immediateRender:false}},{f(C['connected'])});")
J(f"tl.to('#chF,#chS,#link,#qm',{{autoAlpha:0,duration:0.25}},{f(C['swallow']-0.3)});")
J(f"tl.fromTo('#q8',{{autoAlpha:0,y:30}},{{autoAlpha:1,y:0,duration:0.4,ease:'power2.out',immediateRender:false}},{f(C['swallow']-0.15)});")
J(f"tl.fromTo('#swl',{{x:-220,y:120,rotation:-8,autoAlpha:1}},{{x:1300,y:-60,rotation:6,duration:2.4,ease:'sine.inOut',immediateRender:false}},{f(C['swallow'])});")
for k in range(10):                   # wing beat
    J(f"tl.to('#swl',{{scaleY:{0.55 if k % 2 == 0 else 1},duration:0.12,ease:'sine.inOut'}},{f(C['swallow'] + k * 0.24)});")
FX.light_leak(C["summer"] - 0.2, 2.2, 0.4)

# ======================= S9 — 23 July 2012: the near miss =======================
s = SC["s09"]
g0 = C["orbit"] + 0.5
ins09 = FX.film_insert("ins09", "arch_cme2012", s["start"], g0 + 0.05, "", sc("arch_cme2012"), dy=-150)
SUN, R0 = (540, 860), 360
def onorb(deg): return SUN[0] + R0 * math.cos(math.radians(deg)), SUN[1] + R0 * math.sin(math.radians(deg))
EA, STA = 90, -31                      # Earth at the bottom; STEREO-A ~121° ahead on the orbit (July 2012)
ex, ey = onorb(EA); sx, sy = onorb(STA)
def cone(id_, deg, cls):
    return (f'<g id="{id_}" class="{cls}">'
            f'<path d="M {SUN[0]} {SUN[1]} L {SUN[0]+420} {SUN[1]-150} A 450 450 0 0 1 {SUN[0]+420} {SUN[1]+150} Z"/></g>')
orbit = ('<div class="wash" style="background:radial-gradient(ellipse at 50% 45%,#1b1510 0%,#07080a 75%)"></div>'
         '<svg class="orbsvg" viewBox="0 0 1080 1920" width="1080" height="1920">'
         f'<circle cx="{SUN[0]}" cy="{SUN[1]}" r="{R0}" fill="none" stroke="{CREAM}" stroke-opacity=".45" stroke-width="3" stroke-dasharray="10 12"/>'
         + cone("cone", STA, "cme") + cone("ghost", STA, "cme ghost") +
         f'<circle cx="{SUN[0]}" cy="{SUN[1]}" r="70" fill="#FFB43C"/><circle cx="{SUN[0]}" cy="{SUN[1]}" r="96" fill="#FF8A1E" opacity=".25"/>'
         f'<circle id="earth" cx="{ex:.0f}" cy="{ey:.0f}" r="26" fill="#3D8BFF" stroke="{CREAM}" stroke-width="4"/>'
         f'<circle id="ehit" cx="{ex:.0f}" cy="{ey:.0f}" r="26" fill="none" stroke="{RED_ON_DARK}" stroke-width="10" opacity="0"/>'
         f'<rect x="{sx-14:.0f}" y="{sy-14:.0f}" width="28" height="28" fill="{MUSTARD}" stroke="{CREAM}" stroke-width="3"/></svg>'
         f'<div class="olabel tu" style="left:{sx-250:.0f}px;top:{sy-90:.0f}px">STEREO-A</div>'
         f'<div class="olabel tu" style="left:{ex+44:.0f}px;top:{ey-24:.0f}px">EARTH</div>')
clip("sc09a", s["start"], g0 + 0.02, '<div id="f09" class="wash">' + ins09 + typed("t_2012", 56, SAFE_TOP + 10, 44, -1.2) + '</div>')
J(f"tl.to('#f09',{{autoAlpha:0,duration:0.22}},{f(g0-0.24)});")
clip("sc09", g0, s["end"], f'<div id="orb" class="wash">{orbit}</div>'
     + stamp("sthit", ["STEREO-A: HIT · EARTH: MISSED"], 70, SAFE_TOP + 90, -3, 50)
     + tag("t_week", "1 WEEK EARLIER", 300, 452, 44, -1.5))
FX.flash(s["start"] + 0.02, 0.5)
J(f"tl.fromTo('#orb',{{opacity:0}},{{opacity:1,duration:0.3,immediateRender:false}},{f(g0)});")
SVO = f"{SUN[0]} {SUN[1]}"                 # GSAP owns SVG transforms: rotate/scale about the Sun via svgOrigin
J(f"tl.set('#cone,#ghost',{{svgOrigin:'{SVO}',rotation:{STA},scale:1}},0);")
J(f"tl.fromTo('#cone',{{svgOrigin:'{SVO}',rotation:{STA},scale:0.1,autoAlpha:0}},{{svgOrigin:'{SVO}',rotation:{STA},scale:1,autoAlpha:1,duration:0.6,ease:'power2.out',immediateRender:false}},{f(g0+0.1)});")
stamp_anim("sthit", g0 + 0.6, -3)
J(f"tl.fromTo('#ghost',{{autoAlpha:0}},{{autoAlpha:1,duration:0.2,immediateRender:false}},{f(C['week']+0.1)});")
J(f"tl.fromTo('#ghost',{{svgOrigin:'{SVO}',rotation:{STA}}},{{svgOrigin:'{SVO}',rotation:{EA},duration:1.3,ease:'power2.inOut',immediateRender:false}},{f(C['week']+0.2)});")
type_anim("t_week", "1 WEEK EARLIER", C["week"] + 0.2)
J(f"tl.fromTo('#ehit',{{opacity:0,attr:{{r:26}}}},{{opacity:1,attr:{{r:80}},duration:0.5,ease:'power2.out',immediateRender:false}},{f(C['hitus'])});")
J(f"tl.to('#ehit',{{opacity:0,duration:0.5}},{f(C['hitus']+0.5)});")
FX.flash(C["hitus"], 0.5); shake("#sc09", C["hitus"], 0.5, 16)

# ======================= S10 — a world built on wires + end card =======================
s = SC["s10"]
clip("bk10", s["start"] - 0.4, TOTAL, f'<div class="wash" style="background:{NIGHT}"></div>', z=8)
J(f"tl.fromTo('#bk10',{{opacity:0}},{{opacity:1,duration:0.4,immediateRender:false}},{f(s['start']-0.4)});")
g1 = s["start"] + float(CLIPS["arch_nightlights"]["dur"]) - 0.1
if FX.footage("kbN", "arch_nightlights", s["start"], g1, box=(0, 400, 1080, 1080)):
    J(f"tl.fromTo('#kbN_vs',{{autoAlpha:0}},{{autoAlpha:1,duration:0.8,immediateRender:false}},{f(s['start'])});")
    J(f"tl.fromTo('#kbN_vw',{{scale:0.92}},{{scale:1.04,duration:{f(g1-s['start'])},ease:'none',immediateRender:false}},{f(s['start'])});")
    J(f"tl.to('#kbN_vs',{{autoAlpha:0,duration:0.5}},{f(C['end']+0.1)});")
lines10 = [("l10a", "In 1859, the sky ran a telegraph line.", s["start"] + 0.05), ("l10b", "Next time…", C["next"] - 0.05),
           ("l10c", "it will find a world built on wires.", C["find"] - 0.05)]
end_txt = ('<div id="wires" class="wires" data-tq-spoken="true">'
           f'<div id="l10a" class="w1 tu">{html.escape(lines10[0][1])}</div>'
           f'<div id="l10b" class="w2 tu">{html.escape(lines10[1][1])}</div></div>'
           f'<div id="l10c" class="w3 tu" data-tq-spoken="true" data-layout-allow-caption-zone="true">it will find a world built on <span class="wr">wires.</span></div>')
riley = tag("t_riley", "12% CHANCE PER DECADE", 300, 1250, 34, -1.2)
nl_credit = f'<div id="crN">{credit(sc("arch_nightlights"), 120, 430, dark=True)}</div>' 
endcard = ('<div id="endcard" class="wash endcard" style="opacity:0" data-layout-allow-overlap="true">'
           '<div class="eklogo">PAPER TRAIL</div>'
           '<div class="strip ink big" id="e1" data-layout-allow-overlap="true" data-layout-allow-overflow="true">THE DAY THE SKY</div>'
           '<div class="strip red big" id="e2" data-layout-allow-overlap="true" data-layout-allow-overflow="true">RAN THE TELEGRAPH</div>'
           '<div class="ename">The Carrington Event · 1–2 September 1859</div>'
           + tag("t_closed", TYPED["t_closed"][1], 330, 1180, 44, -1.0) +
           '<div class="esrc tu">SOURCES IN DESCRIPTION</div>'
           '<div class="efollow" id="efollow" data-layout-allow-caption-zone="true">FOLLOW FOR FILE 03 →</div></div>')
type_anim("t_closed", TYPED["t_closed"][1], TYPED["t_closed"][0])
clip("sc10", s["start"], s["end"], end_txt + riley + nl_credit + endcard, z=12)
pop("#crN", s["start"] + 0.4)
J(f"tl.to('#crN',{{autoAlpha:0,duration:0.4}},{f(C['end']+0.1)});")
for i, txt, t in lines10:
    J(f"tl.fromTo('#{i}',{{autoAlpha:0,y:20,filter:'blur(8px)'}},{{autoAlpha:1,y:0,filter:'blur(0px)',duration:0.5,ease:'power2.out',immediateRender:false}},{f(t)});")
J(f"tl.to('#l10a',{{autoAlpha:0.35,duration:0.4}},{f(C['next']-0.1)});")
J(f"tl.fromTo('#l10c .wr',{{color:'{CREAM}'}},{{color:'{RED_ON_DARK}',duration:0.3,immediateRender:false}},{f(C['wires'])});")
type_anim("t_riley", "12% CHANCE PER DECADE", C["next"] + 0.6)
FX.light_leak(s["start"] - 0.1, 2.6, 0.35)
et = C["end"] + 0.25
J(f"tl.to('#endcard',{{opacity:1,duration:0.6}},{f(et)});")
J(f"tl.to('#wires,#l10c,#t_riley',{{opacity:0,duration:0.5}},{f(et)});")
J(f"tl.fromTo('#e1',{{autoAlpha:0,x:-200}},{{autoAlpha:1,x:0,duration:0.4,ease:'power4.out',immediateRender:false}},{f(et+0.25)});")
J(f"tl.fromTo('#e2',{{autoAlpha:0,x:200}},{{autoAlpha:1,x:0,duration:0.4,ease:'power4.out',immediateRender:false}},{f(et+0.4)});")
J(f"tl.fromTo('#efollow',{{autoAlpha:0,y:20}},{{autoAlpha:1,y:0,duration:0.4,immediateRender:false}},{f(et+1.0)});")

# ======================= transitions =======================
body.append(f'<div id="tearwrap" class="clip" data-start="0" data-duration="{f(TOTAL)}" data-track-index="4" style="z-index:40;pointer-events:none">'
            '<img id="tear" src="assets/tear.png" style="position:absolute;top:-90px;left:0;width:1560px;height:2100px;opacity:0;visibility:hidden" alt=""></div>')
for sid in ["s02", "s04", "s06", "s08"]:
    tear(SC[sid]["start"])
J(f"tl.fromTo('#sc05',{{scale:1.2,filter:'blur(8px)'}},{{scale:1,filter:'blur(0px)',duration:0.32,ease:'power3.out',immediateRender:false}},{f(SC['s05']['start'])});")
J(f"tl.fromTo('#sc07',{{scale:1.15,filter:'blur(8px)'}},{{scale:1,filter:'blur(0px)',duration:0.3,ease:'power3.out',immediateRender:false}},{f(SC['s07']['start'])});")
FX.flash(SC["s07"]["start"] + 0.02, 0.5)

# ======================= captions (karaoke strips) =======================
HIDE = [(C["swallow"] - 0.05, SC["s08"]["end"]), (SC["s10"]["start"] - 0.05, TOTAL)]
KEY = {"1859", "unplugged", "sky", "sky.", "11:18", "carrington", "white", "sixty", "gone", "seventeen", "blood", "cuba",
       "breakfast", "dawn", "sparks", "fire", "disconnected", "two", "alone", "swallow", "summer", "2012", "week", "hit", "wires"}
def kword(w): return re.sub(r"[^a-z0-9:]", "", w.lower()).rstrip(":") in KEY
toks = []
for w in WORDS:
    if any(a <= w["s"] < b for a, b in HIDE): continue
    toks.append(dict(w))
chunks, cur = [], []
for i, w in enumerate(toks):
    cur.append(w)
    nxt = toks[i + 1] if i + 1 < len(toks) else None
    brk = (len(cur) >= 3 or sum(len(x["w"]) for x in cur) >= 15 or re.search(r"[.,?!…]$", w["w"])
           or nxt is None or nxt["scene"] != w["scene"] or nxt["s"] - w["e"] > 0.5)
    if brk: chunks.append(cur); cur = []
cap_html = []
for ci, ch in enumerate(chunks):
    rot = (-1.6, 1.2, -0.8, 1.6)[ci % 4]
    spans = "".join(
        f'<span class="cw{" key" if kword(w["w"]) else ""}" id="c{ci}_{wi}" data-layout-allow-overlap="true">{html.escape(w["w"].upper())}</span>'
        for wi, w in enumerate(ch))
    cap_html.append(f'<div class="cap" id="cap{ci}" data-layout-allow-caption-zone="true"><div class="capstrip" style="transform:rotate({rot}deg)">{spans}</div></div>')
    t_on = ch[0]["s"] - 0.06
    nxt_t = chunks[ci + 1][0]["s"] - 0.06 if ci + 1 < len(chunks) else TOTAL
    t_off = min(nxt_t, ch[-1]["e"] + 0.45)
    for a, b in HIDE:
        if t_on < a < t_off: t_off = a
    J(f"tl.fromTo('#cap{ci}',{{autoAlpha:0,y:26,scale:0.92}},{{autoAlpha:1,y:0,scale:1,duration:0.14,ease:'back.out(2.2)',immediateRender:false}},{f(t_on)});")
    J(f"tl.set('#cap{ci}',{{autoAlpha:0}},{f(t_off)});")
    for wi, w in enumerate(ch):
        k = " key" if kword(w["w"]) else ""
        end_t = ch[wi + 1]["s"] if wi + 1 < len(ch) else t_off
        J(f"tl.set('#c{ci}_{wi}',{{attr:{{class:'cw on{k}'}}}},{f(w['s'])});")
        J(f"tl.set('#c{ci}_{wi}',{{attr:{{class:'cw{k}'}}}},{f(end_t)});")
clip("captions", 0, TOTAL, "".join(cap_html), z=50, style="pointer-events:none")

# ======================= pro light =======================
clip("fxo", 0, TOTAL, FX.overlays(), z=65, style="pointer-events:none")
FX.light_leak(C["sky"] - 0.2, 2.6, 0.55)          # "…coming from the sky"

# ======================= global chrome: bug, progress, grain, vignette =======================
clip("chrome", 0, TOTAL,
     '<div id="bug" class="bug">PAPER TRAIL <b>·</b> FILE 02</div>'
     '<div class="progress"><div id="prog"></div></div>', z=60)
J(f"tl.fromTo('#prog',{{scaleX:0}},{{scaleX:1,duration:{f(TOTAL)},ease:'none',immediateRender:false}},0);")
J(f"tl.to('#bug',{{autoAlpha:0,duration:0.3}},{f(SC['s10']['start'])});")
clip("fx", 0, TOTAL, '<div id="grain" class="grain"></div><div class="vignette"></div>', z=70, style="pointer-events:none")
gt = 0.0
while gt < TOTAL:
    J(f"tl.set('#grain',{{x:{-int(rnd()*512)},y:{-int(rnd()*512)}}},{f(gt)});"); gt += 1 / 15
J(f"tl.to('#grain',{{opacity:0.07,duration:0.8}},{f(SC['s10']['start'])});")

CSS = fx.CSS + f"""
@font-face{{font-family:'Oswald';src:url('fonts/Oswald.ttf');font-weight:200 700}}
@font-face{{font-family:'Anton';src:url('fonts/Anton-Regular.ttf')}}
@font-face{{font-family:'DM Serif';src:url('fonts/DMSerifDisplay-Regular.ttf')}}
@font-face{{font-family:'DM Serif';src:url('fonts/DMSerifDisplay-Italic.ttf');font-style:italic}}
@font-face{{font-family:'Elite';src:url('fonts/SpecialElite-Regular.ttf')}}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:1080px;height:1920px;overflow:hidden;background:{CREAM}}}
#root{{position:relative;width:1080px;height:1920px;overflow:hidden;background:{CREAM};font-family:'Oswald',sans-serif}}
.clip{{position:absolute;left:0;top:0;width:1080px;height:1920px;overflow:hidden}}
.wash{{position:absolute;left:0;top:0;width:1080px;height:1920px}}
.kb{{position:absolute;left:-108px;top:-201px;width:1296px;height:2322px;transform-origin:50% 50%}}
.kb>img{{position:absolute;left:0;top:0;width:1296px;height:2322px}}
.title{{position:absolute;left:0;top:300px;width:1080px;text-align:center;transform-origin:50% 50%}}
.strip{{display:inline-block;font-family:'Anton';font-size:112px;line-height:1.02;padding:6px 30px 2px;margin:6px 0;letter-spacing:.01em}}
.strip.ink{{background:{INK};color:{CREAM};transform:rotate(-2deg)}}
.strip.red{{background:{RED};color:{CREAM};transform:rotate(1.5deg)}}
.title .strip{{display:block;width:max-content;margin:8px auto}}
.kicker{{display:block;width:max-content;margin:26px auto 0;font-family:'DM Serif';font-style:italic;font-size:50px;line-height:1.1;color:{INK};
  background:#F3EAD3;padding:12px 30px 10px;transform:rotate(-1deg);box-shadow:0 8px 20px rgba(0,0,0,.45)}}
.tag{{position:absolute;font-family:'Elite',monospace;color:{INK};background:#F3EAD3;padding:10px 20px 8px;
  box-shadow:0 6px 14px rgba(0,0,0,.35);white-space:nowrap;visibility:hidden;opacity:0;transform-origin:0 50%}}
.tag .ch{{opacity:0}}
.stamp{{position:absolute;font-family:'Anton';text-align:center;line-height:1.05;padding:14px 30px 10px;border:9px solid;
  border-radius:10px;background:rgba(246,238,220,.9);box-shadow:0 10px 26px rgba(0,0,0,.35);visibility:hidden;opacity:0;white-space:nowrap;
  -webkit-mask-image:url(assets/stampmask.png);-webkit-mask-size:100% 100%;mask-image:url(assets/stampmask.png);mask-size:100% 100%}}
.card{{position:absolute;background:#FBF7EE;padding:20px;box-shadow:0 24px 50px rgba(0,0,0,.40);transform:rotate(var(--r))}}
.card.print{{padding:0}}
.card img{{display:block}}
.tape{{position:absolute;width:180px;height:54px;background:rgba(227,201,120,.62);box-shadow:0 2px 4px rgba(0,0,0,.15)}}
.credit{{font-family:'Elite',monospace;font-size:24px;line-height:1.25;color:{INK};text-align:center;background:#F3EAD3;padding:8px 16px 6px;box-shadow:0 4px 10px rgba(0,0,0,.3)}}
.credit.dark{{background:rgba(12,10,8,.82);color:#EFE6D2;box-shadow:none}}
.glow{{position:absolute;width:120px;height:120px;margin:-60px 0 0 -60px;border-radius:50%;visibility:hidden;opacity:0;mix-blend-mode:normal;
  background:radial-gradient(circle,#FFFFFF 0%,#FFFBEA 22%,rgba(255,236,170,.85) 40%,rgba(255,200,90,.35) 62%,rgba(255,200,90,0) 72%)}}
.ring{{position:absolute;width:64px;height:80px;border-radius:12px;background:{RED};color:{CREAM};text-align:center;font-family:'Anton';font-size:60px;line-height:84px;
  box-shadow:0 6px 14px rgba(0,0,0,.45);visibility:hidden;opacity:0}}
.sixty{{position:absolute;left:770px;top:236px;visibility:hidden;opacity:0}}
.graph{{position:absolute;left:70px;top:430px;width:940px;height:600px;visibility:hidden;opacity:0;
  background:#F7F0DE repeating-linear-gradient(0deg,rgba(20,20,20,.10) 0 2px,transparent 2px 60px),repeating-linear-gradient(90deg,rgba(20,20,20,.10) 0 2px,transparent 2px 60px);
  box-shadow:0 18px 40px rgba(0,0,0,.35)}}
.graph svg{{position:absolute;left:0;top:0}}
.glabel{{position:absolute;left:50%;top:620px;transform:translateX(-50%);white-space:nowrap;background:{INK};color:{CREAM};font-weight:700;font-size:42px;letter-spacing:.14em;padding:8px 24px 6px}}
.arcsvg,.wiresvg,.orbsvg{{position:absolute;left:0;top:0}}
.bz{{fill:none;stroke:#E8F4FF;stroke-width:5;opacity:0;filter:drop-shadow(0 0 8px #7FB8FF) drop-shadow(0 0 18px #3B82F6)}}
.aur7{{position:absolute;left:-20%;top:0;width:140%;height:900px;opacity:.5;filter:blur(30px);
  background:radial-gradient(ellipse 30% 60% at 30% 20%,rgba(80,255,170,.55),transparent 70%),radial-gradient(ellipse 25% 50% at 65% 15%,rgba(255,60,90,.45),transparent 70%),radial-gradient(ellipse 35% 40% at 50% 35%,rgba(90,230,160,.35),transparent 70%)}}
.node{{position:absolute;font-family:'Elite',monospace;font-size:44px;color:{INK};background:#F7F0DE;padding:16px 28px 14px 60px;
  box-shadow:0 8px 18px rgba(0,0,0,.30);visibility:hidden;opacity:0;white-space:nowrap}}
.pin{{position:absolute;left:18px;top:50%;width:26px;height:26px;margin-top:-13px;border-radius:50%;
  background:radial-gradient(circle at 35% 35%,#ff6b6b,{RED} 60%,#6d0012);box-shadow:0 3px 5px rgba(0,0,0,.4)}}
.telegram{{position:absolute;left:70px;top:760px;width:940px;background:#F3EAD3;padding:26px 34px 30px;box-shadow:0 18px 40px rgba(0,0,0,.5);
  font-family:'Elite',monospace;font-size:44px;line-height:1.3;color:{INK};visibility:hidden;opacity:0}}
.tghead{{font-family:'Oswald';font-weight:700;font-size:30px;letter-spacing:.16em;color:{RED_ON_LIGHT};border-bottom:3px solid {INK};padding-bottom:10px;margin-bottom:16px}}
.tq{{opacity:0}}
.chip{{position:absolute;top:1090px;width:330px;text-align:center;font-family:'Anton';font-size:76px;line-height:1;color:{CREAM};background:{INK};padding:14px 0 8px;
  box-shadow:0 10px 22px rgba(0,0,0,.4);visibility:hidden;opacity:0}}
.link{{position:absolute;left:0;top:1040px}}
.qmk{{position:absolute;left:490px;top:1080px;width:100px;height:100px;border-radius:50%;background:{RED};color:{CREAM};font-family:'Anton';font-size:76px;line-height:104px;text-align:center;visibility:hidden;opacity:0}}
.swl{{position:absolute;left:0;top:700px;visibility:hidden;opacity:0}}
.q8{{position:absolute;left:90px;top:1050px;width:860px;text-align:center;visibility:hidden;opacity:0}}
.q8t{{background:{INK};color:{CREAM};font-family:'DM Serif';font-style:italic;font-size:60px;line-height:1.12;padding:18px 30px 20px;box-shadow:0 14px 30px rgba(0,0,0,.45)}}
.q8by{{display:inline-block;margin-top:16px;background:#F3EAD3;color:{INK};font-weight:600;font-size:26px;letter-spacing:.06em;padding:6px 16px 4px}}
.olabel{{position:absolute;width:240px;text-align:center;font-family:'Oswald';font-weight:700;font-size:40px;letter-spacing:.08em;color:{INK};background:{CREAM};padding:4px 0 2px}}
.cme path{{fill:rgba(255,150,60,.55);stroke:#FFC27A;stroke-width:3}}
.cme{{opacity:0;visibility:hidden}}
.cme.ghost path{{fill:rgba(255,77,77,.28);stroke:{RED_ON_DARK};stroke-dasharray:12 10}}
.wires{{position:absolute;left:60px;top:{SAFE_TOP + 10}px;width:960px;text-align:center;font-family:'DM Serif';color:#FFF6E4}}
.w1{{font-style:italic;font-size:58px;line-height:1.15;visibility:hidden;opacity:0}}
.w2{{font-style:italic;font-size:86px;line-height:1.2;margin-top:6px;visibility:hidden;opacity:0}}
.w3{{position:absolute;left:30px;top:1470px;width:1020px;text-align:center;font-family:'DM Serif';font-style:italic;font-size:54px;line-height:1.1;color:{CREAM};visibility:hidden;opacity:0}}
.endcard{{background:rgba(16,13,10,.96);text-align:center;padding-top:520px}}
.eklogo{{font-family:'Oswald';font-weight:700;font-size:40px;letter-spacing:.5em;color:{RED_ON_DARK};margin-bottom:34px;padding-left:.5em}}
.strip.big{{display:block;width:max-content;margin:10px auto;font-size:112px}}
.ename{{font-family:'DM Serif';font-style:italic;font-size:40px;color:{CREAM};margin-top:48px}}
.esrc{{position:absolute;left:0;width:1080px;top:1290px;font-family:'Oswald';font-weight:600;font-size:30px;letter-spacing:.2em;color:#CFC6B4}}
.efollow{{position:absolute;left:0;width:1080px;top:1380px;font-weight:600;font-size:50px;letter-spacing:.14em;color:{MUSTARD};visibility:hidden;opacity:0}}
.cap{{position:absolute;left:0;top:1350px;width:1080px;text-align:center;visibility:hidden;opacity:0}}
.capstrip{{display:inline-block;background:#F6EEDC;padding:12px 18px 8px;box-shadow:0 8px 0 rgba(0,0,0,.28),0 14px 28px rgba(0,0,0,.25);max-width:840px}}
.cw{{display:inline-block;font-family:'Oswald';font-weight:600;font-size:76px;line-height:1.1;color:{INK};padding:0 8px;border-radius:6px}}
.cw.key{{color:{RED_ON_LIGHT}}}
.cw.on{{background:{MUSTARD};color:{INK}}}
.cw.on.key{{background:{RED};color:{CREAM}}}
.bug{{position:absolute;right:60px;top:{SAFE_TOP - 8}px;font-weight:600;font-size:28px;letter-spacing:.22em;color:{CREAM};background:{INK};padding:8px 16px 6px}}
.bug b{{color:{RED}}}
.progress{{position:absolute;left:0;bottom:0;width:1080px;height:8px;background:rgba(20,20,20,.35)}}
#prog{{width:1080px;height:8px;background:{RED};transform-origin:0 50%}}
.grain{{position:absolute;left:0;top:0;width:1600px;height:2440px;background:url(assets/grain.png) repeat;opacity:.13;mix-blend-mode:overlay}}
.vignette{{position:absolute;left:0;top:0;width:1080px;height:1920px;background:radial-gradient(ellipse at 50% 48%,rgba(0,0,0,0) 55%,rgba(0,0,0,.42) 100%)}}
"""

body.append(FX.video_layers())   # root-level timed <video> layers (engine/fx.py)

doc = f"""<!doctype html>
<html lang="en" data-resolution="portrait">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<title>Paper Trail — File 02: The Day the Sky Ran the Telegraph</title>
<script src="gsap.min.js"></script>
<style>{CSS}</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{f(TOTAL)}" data-width="1080" data-height="1920">
<audio id="mix" src="assets/mix.wav" data-start="0" data-duration="{f(TOTAL)}" data-track-index="9"></audio>
{chr(10).join(body)}
</div>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(js)}
window.__timelines["main"] = tl;
tl.seek(0);
</script>
</body>
</html>
"""
HF.mkdir(parents=True, exist_ok=True)
(HF / "index.html").write_text(doc)
for fn, content in [("hyperframes.json", '{\n  "$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",\n  "paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"},\n  "media": {"autoProxy": false}\n}\n'),
                    ("meta.json", '{"id": "paper-trail-ep02", "name": "Paper Trail — File 02: The Day the Sky Ran the Telegraph"}\n'),
                    ("package.json", '{\n  "name": "paper-trail-ep02",\n  "private": true,\n  "type": "module",\n  "scripts": {\n    "check": "npx --yes hyperframes@0.8.137 check",\n    "render": "npx --yes hyperframes@0.8.137 render"\n  }\n}\n')]:
    (HF / fn).write_text(content)
print("index.html:", len(doc) // 1024, "KB,", len(js), "timeline ops,", len(chunks), "caption chunks,", len(FX.layers), "video layers, total", TOTAL)
