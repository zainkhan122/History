#!/usr/bin/env python3
"""Generates the HyperFrames composition (index.html) for Paper Trail Ep.01 from timeline.json.
One paused GSAP timeline, fully deterministic (seeded LCG, no Date/Math.random), local fonts + GSAP.
usage: python3 build.py <hf_dir>"""
import json, re, sys, html
from pathlib import Path

HERE = Path(__file__).resolve().parent
HF = Path(sys.argv[1] if len(sys.argv) > 1 else Path.home() / ".cache/build/ep01-petrov/hf")
TL = json.load(open(HERE / "timeline.json"))
C, SC, TOTAL, WORDS = TL["cues"], {s["id"]: s for s in TL["scenes"]}, TL["total"], TL["words"]
TYPE_RATE = 22.0                      # chars/s — must match score.py
INK, CREAM, RED, MUSTARD = "#141414", "#F4ECD8", "#C8102E", "#E3A72F"

body, js = [], []                     # html chunks, js timeline lines
def J(s): js.append(s)
def f(x): return f"{x:.3f}"

# deterministic pseudo-random (LCG) for shakes/rotations
_seed = [1983]
def rnd():
    _seed[0] = (_seed[0] * 1103515245 + 12345) % 2147483648
    return _seed[0] / 2147483648

def shake(sel, t, dur=0.45, amp=18):
    steps = max(3, int(dur / 0.045)); out = []
    for i in range(steps):
        a = amp * (1 - i / steps)
        out.append(f"tl.to('{sel}',{{x:{(rnd()*2-1)*a:.1f},y:{(rnd()*2-1)*a:.1f},rotation:{(rnd()*2-1)*a*0.04:.2f},duration:0.043,ease:'none'}},{f(t+i*0.045)});")
    out.append(f"tl.to('{sel}',{{x:0,y:0,rotation:0,duration:0.06,ease:'power1.out'}},{f(t+steps*0.045)});")
    J("\n".join(out))

def clip(id_, start, end, inner, z=10, extra_cls="", style=""):
    body.append(f'<div id="{id_}" class="clip {extra_cls}" data-start="{f(start)}" data-duration="{f(end-start)}" '
                f'data-track-index="{z//10}" style="z-index:{z};{style}">{inner}</div>')

def kb(id_, img, overlays="", style=""):
    # 1296x2322 art plate centred on the 1080x1920 frame (Ken Burns headroom); overlays use % of the plate
    return (f'<div id="{id_}" class="kb" style="{style}"><img src="assets/{img}.jpg" alt="">{overlays}</div>')

def kb_move(sel, t0, t1, s0, s1, x0=0, x1=0, y0=0, y1=0, ease="none"):
    J(f"tl.fromTo('{sel}',{{scale:{s0},x:{x0},y:{y0}}},{{scale:{s1},x:{x1},y:{y1},duration:{f(t1-t0)},ease:'{ease}',immediateRender:false}},{f(t0)});")

def tag(id_, text, x, y, size=40, rot=-1.5, extra=""):
    chars = "".join(f'<span class="ch" id="{id_}_{i}">{html.escape(c) if c != " " else "&nbsp;"}</span>' for i, c in enumerate(text))
    return f'<div id="{id_}" class="tag" style="left:{x}px;top:{y}px;font-size:{size}px;transform:rotate({rot}deg);{extra}">{chars}</div>'

def type_anim(id_, text, t0):
    J(f"tl.fromTo('#{id_}',{{autoAlpha:0,scale:0.9}},{{autoAlpha:1,scale:1,duration:0.12,ease:'back.out(2)',immediateRender:false}},{f(t0-0.14)});")
    for i, _ in enumerate(text):
        J(f"tl.set('#{id_}_{i}',{{opacity:1}},{f(t0+i/TYPE_RATE)});")

def stamp(id_, lines, x, y, rot, size=90, color=RED):
    inner = "<br>".join(html.escape(l) for l in lines)
    return (f'<div id="{id_}" class="stamp" style="left:{x}px;top:{y}px;font-size:{size}px;color:{color};border-color:{color};'
            f'--rot:{rot}deg;transform:rotate({rot}deg)">{inner}</div>')

def stamp_anim(id_, t, rot):
    J(f"tl.fromTo('#{id_}',{{autoAlpha:0,scale:2.3,rotation:{rot-6}}},{{autoAlpha:0.93,scale:1,rotation:{rot},duration:0.13,ease:'power4.in',immediateRender:false}},{f(t-0.13)});")

TYPED = {i: (t, txt) for t, txt, i in TL["typed"]}
def typed(id_, x, y, size=40, rot=-1.5, extra=""):
    t, txt = TYPED[id_]; type_anim(id_, txt, t); return tag(id_, txt, x, y, size, rot, extra)

def tear(t):          # torn-paper wipe covering the cut at time t
    J(f"tl.fromTo('#tear',{{x:1120,autoAlpha:1}},{{x:-260,autoAlpha:1,duration:0.30,ease:'power3.in',immediateRender:false}},{f(t-0.30)});")
    J(f"tl.to('#tear',{{x:-1800,duration:0.34,ease:'power2.in'}},{f(t+0.02)});")
    J(f"tl.set('#tear',{{autoAlpha:0}},{f(t+0.37)});")

# ======================= BACKGROUND (paper) =======================
clip("bg", 0, TOTAL, '<img src="assets/bg_paper.jpg" style="width:100%;height:100%;object-fit:cover" alt="">', z=0)

# ======================= S1 — bunker (hook) =======================
s = SC["s01"]
title = ('<div id="title" class="title" data-layout-allow-overlap="true">'
         f'<div class="strip ink" id="tl1">THE MAN WHO</div><div class="strip red" id="tl2">DID NOTHING</div>'
         '<div class="kicker" id="tl3">— and why the world is still here</div></div>')
redwash = '<div id="redwash" class="wash" style="opacity:0;background:radial-gradient(ellipse at 50% 45%, rgba(200,16,46,0.15), rgba(200,16,46,0.75));"></div>'
clip("sc01", 0, s["end"], kb("kb01", "s01_bunker") + redwash + title +
     typed("t_date", 56, 190, 40, -1.2) + typed("t_place", 56, 262, 40, 0.8))
kb_move("#kb01", 0, 1.1, 1.0, 0.88, 0, 0, -40, 0, "expo.out")
kb_move("#kb01", 1.1, s["end"], 0.88, 0.97, 0, 0, 0, 30)
J("tl.fromTo('#title',{scale:1.08},{scale:1,duration:0.5,ease:'power3.out',immediateRender:false},0);")
J("tl.fromTo('#tl3',{autoAlpha:0,y:10},{autoAlpha:1,y:0,duration:0.4,immediateRender:false},0.5);")
J("tl.to('#title',{autoAlpha:0,y:-60,duration:0.35,ease:'power2.in'},2.75);")
J(f"tl.fromTo('#redwash',{{opacity:0}},{{opacity:0.9,duration:0.08,immediateRender:false}},{f(C['nuclear'])});")
J(f"tl.to('#redwash',{{opacity:0.35,duration:0.9,ease:'power2.out'}},{f(C['nuclear']+0.1)});")
shake("#sc01", C["nuclear"], 0.6, 26)

# ======================= S2 — KAL 007 card =======================
s = SC["s02"]
card2 = ('<div id="card2" class="card" style="left:150px;top:230px;width:780px;--r:-3deg">'
         '<img src="assets/s02_jet.jpg" style="width:740px;height:1326px" alt="">'
         '<div class="tape" style="left:-40px;top:-14px;transform:rotate(-28deg)"></div>'
         '<div class="tape" style="right:-40px;top:-14px;transform:rotate(30deg)"></div></div>')
st269 = stamp("st269", ["269 DEAD"], 430, 1020, -9, 112)
clip("sc02", s["start"], s["end"], card2 + st269 + typed("t_kal", 56, 150, 42, -1.0))
J(f"tl.fromTo('#card2',{{y:-1500,rotation:-14}},{{y:0,rotation:-3,duration:0.55,ease:'back.out(1.1)',immediateRender:false}},{f(s['start'])});")
J(f"tl.to('#card2',{{y:-24,rotation:-1.6,scale:1.03,duration:{f(C['paranoid']-0.42-s['start']-0.55)},ease:'none'}},{f(s['start']+0.55)});")
stamp_anim("st269", C["died269"] + 0.1, -9)
shake("#sc02", C["died269"] + 0.1, 0.25, 8)
J(f"tl.to('#card2',{{scale:1.09,duration:1.1,ease:'power2.in'}},{f(C['paranoid']-0.4)});")

# ======================= S3 — console -> globe, 5 missiles =======================
s = SC["s03"]
start_glow = ('<div id="start" class="startglow" style="left:18.2%;top:20.0%;width:65.5%;height:24.7%">'
              '<span>СТАРТ</span></div>')
arcs = "".join(
    f'<path id="arc{i}" d="M {x0} {y0} Q {cx} {cy} {x1} {y1}" stroke="{RED}" stroke-width="9" fill="none" stroke-linecap="round" '
    f'stroke-dasharray="1400" stroke-dashoffset="1400"/>'
    for i, (x0, y0, cx, cy, x1, y1) in enumerate([
        (230, 1250, 380, 520, 820, 760), (300, 1300, 520, 480, 900, 900), (200, 1180, 420, 620, 760, 1050),
        (340, 1330, 620, 560, 960, 1120), (260, 1220, 300, 420, 700, 640)], start=1))
globe = (kb("kb04g", "s04_globe") + f'<svg class="arcs" viewBox="0 0 1080 1920" width="1080" height="1920">{arcs}</svg>')
counter = ('<div id="counter" class="counter" data-layout-allow-overlap="true">' +
           "".join(f'<div class="num" id="n{i}">{i}</div>' for i in range(1, 6)) +
           '<div class="clabel">MISSILES DETECTED</div></div>')
flash = '<div id="flash3" class="wash" style="background:#fff;opacity:0"></div>'
clip("sc03", s["start"], s["end"],
     f'<div id="g3" class="wash" style="opacity:0">{globe}</div>' + kb("kb03", "s03_console", start_glow) + flash + counter)
kb_move("#kb03", s["start"], C["m2"], 1.05, 0.9, 0, 0, 60, 0, "power2.out")
J(f"tl.fromTo('#start',{{opacity:0}},{{opacity:1,duration:0.05,immediateRender:false}},{f(C['launch']-0.05)});")
for k, dt in enumerate([0.08, 0.16, 0.22]):
    J(f"tl.set('#start',{{opacity:{0.35 if k % 2 == 0 else 1}}},{f(C['launch']+dt)});")
J(f"tl.fromTo('#flash3',{{opacity:0.9}},{{opacity:0,duration:0.35,immediateRender:false}},{f(C['launch'])});")
shake("#sc03", C["launch"], 0.5, 22)
# cut to globe at "second"
J(f"tl.set('#kb03',{{autoAlpha:0}},{f(C['m2']-0.04)});")
J(f"tl.set('#g3',{{opacity:1}},{f(C['m2']-0.04)});")
kb_move("#kb04g", C["m2"] - 0.04, s["end"], 0.92, 1.0)
J(f"tl.fromTo('#counter',{{autoAlpha:0}},{{autoAlpha:1,duration:0.08,immediateRender:false}},{f(C['m2']-0.04)});")
for i, key in enumerate(["launch", "m2", "m3", "m4", "m5"], start=1):
    t = C[key]
    J(f"tl.set('#n{i}',{{autoAlpha:1}},{f(t)});")
    if i > 1: J(f"tl.set('#n{i-1}',{{autoAlpha:0}},{f(t)});")
    J(f"tl.fromTo('#n{i}',{{scale:1.9}},{{scale:1,duration:0.22,ease:'power4.out',immediateRender:false}},{f(t)});")
    J(f"tl.to('#arc{i}',{{strokeDashoffset:0,duration:0.55,ease:'power2.out'}},{f(t)});")
    if i > 1:
        J(f"tl.fromTo('#flash3',{{opacity:{0.25+0.1*i}}},{{opacity:0,duration:0.25,immediateRender:false}},{f(t)});")
        shake("#g3", t, 0.3, 10 + 3 * i)

# ======================= S4 — chain of command =======================
s = SC["s04"]
nodes = [("DUTY OFFICER", 1170), ("COMMAND POST", 900), ("GENERAL STAFF", 630), ("LEADERSHIP", 360)]
node_html = "".join(
    f'<div class="node" id="nd{i}" style="top:{y}px;left:{300 if i % 2 == 0 else 360}px">'
    f'<div class="pin"></div>{html.escape(n)}</div>' for i, (n, y) in enumerate(nodes))
pts = [(330 if i % 2 == 0 else 390, y + 40) for i, (_, y) in enumerate(nodes)]
dpath = "M " + " L ".join(f"{x} {y}" for x, y in pts)
thread = (f'<svg class="arcs" viewBox="0 0 1080 1920" width="1080" height="1920"><path id="thread" d="{dpath}" '
          f'stroke="{RED}" stroke-width="5" fill="none" stroke-dasharray="1200" stroke-dashoffset="1200"/></svg>')
minutes = stamp("stmin", ["ONLY MINUTES", "TO DECIDE"], 520, 470, 7, 64)
globe_ghost = kb("kb04", "s04_globe", style="opacity:0.30;mix-blend-mode:multiply;filter:grayscale(0.4)")
clip("sc04", s["start"], s["end"], globe_ghost + thread + node_html + minutes)
kb_move("#kb04", s["start"], s["end"], 0.95, 1.05, 0, 0, 0, -40)
node_t = [C["chain"] + 0.2, C["chain"] + 1.1, C["chain"] + 2.0, C["minutes"] - 0.3]
J(f"tl.to('#thread',{{strokeDashoffset:0,duration:{f(node_t[-1]-node_t[0]+0.2)},ease:'none'}},{f(node_t[0])});")
for i, t in enumerate(node_t):
    J(f"tl.fromTo('#nd{i}',{{autoAlpha:0,scale:0.6,rotation:-8}},{{autoAlpha:1,scale:1,rotation:{(-1.5 if i % 2 else 1.5)},duration:0.25,ease:'back.out(2.5)',immediateRender:false}},{f(t)});")
stamp_anim("stmin", C["minutes"] + 0.05, 7)
J(f"tl.fromTo('#sc04',{{backgroundColor:'rgba(200,16,46,0)'}},{{backgroundColor:'rgba(200,16,46,0.22)',duration:0.15,immediateRender:false}},{f(C['strike'])});")
shake("#sc04", C["strike"], 0.4, 12)

# ======================= S5 — Petrov + quote =======================
s = SC["s05"]
qwords = [w for w in WORDS if w["scene"] == "s05" and w["s"] >= C["quote"] - 0.01]
qwords = [w for w in qwords if w["w"].lower() not in ("he", "said,")]
quote_html = "".join(f'<span class="qw" id="qw{i}">{html.escape(w["w"])}</span> ' for i, w in enumerate(qwords))
quote = (f'<div id="qdim" class="wash" style="background:rgba(12,10,8,0.72);opacity:0"></div>'
         f'<div id="quote" class="quote" data-layout-allow-overlap="true"><div class="qmark">“</div>{quote_html}'
         f'<div class="qby">— Stanislav Petrov</div></div>')
clip("sc05", s["start"], s["end"], kb("kb05", "s05_officer") + typed("t_name", 56, 1190, 40, -1.0) + quote)
kb_move("#kb05", s["start"], C["quote"], 0.88, 0.98, 0, -30, 0, 50)
kb_move("#kb05", C["quote"], s["end"], 0.98, 1.04, -30, -40, 50, 60)
J(f"tl.fromTo('#kb05',{{filter:'brightness(1)'}},{{filter:'brightness(1.12)',duration:0.12,yoyo:true,repeat:1,immediateRender:false}},{f(C['gut'])});")
J(f"tl.to('#t_name',{{autoAlpha:0,duration:0.3}},{f(C['quote']-0.3)});")
J(f"tl.to('#qdim',{{opacity:1,duration:0.5}},{f(C['quote']-0.35)});")
J(f"tl.fromTo('#quote .qmark',{{autoAlpha:0,scale:0.4}},{{autoAlpha:1,scale:1,duration:0.4,ease:'back.out(2)',immediateRender:false}},{f(C['quote']-0.3)});")
for i, w in enumerate(qwords):
    J(f"tl.fromTo('#qw{i}',{{autoAlpha:0,y:18,filter:'blur(8px)'}},{{autoAlpha:1,y:0,filter:'blur(0px)',duration:0.32,ease:'power2.out',immediateRender:false}},{f(w['s']-0.04)});")
J(f"tl.fromTo('#quote .qby',{{autoAlpha:0}},{{autoAlpha:1,duration:0.4,immediateRender:false}},{f(qwords[-1]['e']+0.1)});")
for i, w in enumerate(qwords):
    if w["w"].lower().startswith(("five", "missiles")):
        J(f"tl.to('#qw{i}',{{color:'{MUSTARD}',duration:0.2}},{f(w['s'])});")

# ======================= S6 — false alarm + the wait =======================
s = SC["s06"]
fa = stamp("stfa", ["ЛОЖНАЯ ТРЕВОГА", "FALSE ALARM"], 150, 830, -8, 80)
mins = "".join(f'<div class="dg" id="dg{m}">{m:02d}:00</div>' for m in range(0, 24))
wait = (f'<div id="waitbox" class="waitbox"><div class="wlabel">WAITING FOR IMPACT</div><div class="digits">{mins}</div>'
        f'<div class="wlabel" style="font-size:30px;opacity:.8">MINUTES</div></div>')
dim6 = '<div id="dim6" class="wash" style="background:rgba(10,8,6,0.62);opacity:0"></div>'
clip("sc06", s["start"], s["end"], kb("kb06", "s06_phone") + dim6 + fa + wait)
kb_move("#kb06", s["start"], C["waited"], 0.9, 0.97, 0, 0, 40, 0)
kb_move("#kb06", C["waited"], s["end"], 0.97, 1.08, 0, 0, 0, 20)
stamp_anim("stfa", C["falsealarm"] + 0.05, -8)
shake("#sc06", C["falsealarm"] + 0.05, 0.3, 12)
J(f"tl.to('#stfa',{{autoAlpha:0,duration:0.3}},{f(C['waited']-0.3)});")
J(f"tl.to('#dim6',{{opacity:1,duration:0.5}},{f(C['waited']-0.2)});")
J(f"tl.fromTo('#waitbox',{{autoAlpha:0,scale:0.9}},{{autoAlpha:1,scale:1,duration:0.3,immediateRender:false}},{f(C['waited']-0.1)});")
J(f"tl.set('#dg0',{{autoAlpha:1}},{f(C['waited']-0.1)});")
t0, t1 = C["waited"] + 0.2, C["nothingcame"] - 0.15
for m in range(1, 24):                      # eased count: slow start, accelerating
    p = (m / 23) ** 0.8
    t = t0 + (t1 - t0) * p
    J(f"tl.set('#dg{m-1}',{{autoAlpha:0}},{f(t)});tl.set('#dg{m}',{{autoAlpha:1}},{f(t)});")
hb = C["waited"] + 1.05
while hb < C["nothingcame"] - 0.4:
    J(f"tl.fromTo('#waitbox',{{scale:1.035}},{{scale:1,duration:0.35,ease:'power2.out',immediateRender:false}},{f(hb)});")
    hb += 1.0
J(f"tl.to('#dg23',{{color:'{CREAM}',duration:0.3}},{f(C['nothingcame'])});")
J(f"tl.to('#kb06',{{filter:'grayscale(1) brightness(0.8)',duration:0.6}},{f(C['nothingcame'])});")

# ======================= S7 — the reveal: sunlight =======================
s = SC["s07"]
glints = "".join(f'<div class="glint" id="gl{i}" style="left:{x}%;top:{y}%"></div>'
                 for i, (x, y) in enumerate([(24, 67), (44, 64), (57, 56), (72, 64), (82, 58)], start=1))
flash7 = '<div id="flash7" class="wash" style="background:#fffbe8;opacity:0"></div>'
five = '<div id="five" class="fivelabel">THE 5 “MISSILES”</div>'
clip("sc07", s["start"], s["end"], kb("kb07", "s07_sunlight", glints) + flash7 + five + typed("t_cause", 56, 180, 42, -1.0))
kb_move("#kb07", s["start"], s["end"], 1.0, 0.88, 0, 0, -60, 20, "power1.out")
J(f"tl.fromTo('#flash7',{{opacity:1}},{{opacity:0,duration:0.9,ease:'power2.out',immediateRender:false}},{f(s['start'])});")
for i in range(1, 6):
    t = s["start"] + 0.6 + i * 0.32
    J(f"tl.fromTo('#gl{i}',{{opacity:0,scale:0.3}},{{opacity:1,scale:1.25,duration:0.35,ease:'power2.out',immediateRender:false}},{f(t)});")
    J(f"tl.to('#gl{i}',{{opacity:0.55,scale:0.9,duration:0.9,ease:'sine.inOut',yoyo:true,repeat:3}},{f(t+0.35)});")
J(f"tl.fromTo('#five',{{autoAlpha:0,y:20,xPercent:-50,rotation:-2}},{{autoAlpha:1,y:0,xPercent:-50,rotation:-2,duration:0.35,immediateRender:false}},{f(C['satellite']-1.4)});")

# ======================= S8 — the logbook (reprimand) =======================
s = SC["s08"]
card8 = ('<div id="card8" class="card" style="left:150px;top:200px;width:780px;--r:2deg">'
         '<img src="assets/s08_logbook.jpg" style="width:740px;height:1326px" alt="">'
         '<div class="tape" style="left:300px;top:-22px;transform:rotate(-4deg)"></div></div>')
st_rep = stamp("strep", ["ВЫГОВОР", "REPRIMAND"], 120, 420, -10, 84)
st_sec = stamp("stsec", ["СЕКРЕТНО", "CLASSIFIED 1983–1998"], 230, 880, 6, 64)
nomedal = '<div id="nomedal" class="tag" style="left:620px;top:150px;font-size:40px;transform:rotate(3deg)">MEDAL: <s style="color:#C8102E">NONE</s></div>'
clip("sc08", s["start"], s["end"], card8 + nomedal + st_rep + st_sec)
J(f"tl.fromTo('#card8',{{y:1700,rotation:9}},{{y:0,rotation:2,duration:0.5,ease:'power3.out',immediateRender:false}},{f(s['start']-0.02)});")
J(f"tl.to('#card8',{{scale:1.04,y:-20,duration:{f(s['end']-s['start']-0.5)},ease:'none'}},{f(s['start']+0.5)});")
J(f"tl.fromTo('#nomedal',{{autoAlpha:0,scale:0.8}},{{autoAlpha:1,scale:1,duration:0.2,ease:'back.out(2)',immediateRender:false}},{f(C['medal'])});")
stamp_anim("strep", C["reprimanded"] + 0.1, -10); shake("#sc08", C["reprimanded"] + 0.1, 0.25, 8)
stamp_anim("stsec", C["secret"] + 0.1, 6); shake("#sc08", C["secret"] + 0.1, 0.25, 8)

# ======================= S9 — the kitchen (heart) =======================
s = SC["s09"]
n9 = [w for w in WORDS if w["scene"] == "s09" and w["s"] >= C["nothing1"] - 0.01]
serif9 = ('<div id="dim9" class="wash" style="background:linear-gradient(rgba(14,10,6,0.25),rgba(14,10,6,0.78));opacity:0"></div>'
          '<div id="nothing" class="bigserif" data-layout-allow-overlap="true">'
          f'<div id="nl1">{html.escape(n9[0]["w"])}</div>'
          '<div id="nl2">' + " ".join(f'<span id="nw{i}">{html.escape(w["w"])}</span>' for i, w in enumerate(n9[1:])) + '</div></div>')
clip("sc09", s["start"], s["end"], kb("kb09", "s09_kitchen", style="filter:sepia(0.28) saturate(0.95) brightness(1.02)") + serif9)
kb_move("#kb09", s["start"], s["end"], 0.88, 1.0, 0, 20, 0, 40)
J(f"tl.to('#dim9',{{opacity:1,duration:0.8}},{f(C['nothing1']-0.6)});")
J(f"tl.fromTo('#nl1',{{autoAlpha:0,y:24,filter:'blur(10px)'}},{{autoAlpha:1,y:0,filter:'blur(0px)',duration:0.6,ease:'power2.out',immediateRender:false}},{f(C['nothing1']-0.05)});")
for i, w in enumerate(n9[1:]):
    J(f"tl.fromTo('#nw{i}',{{autoAlpha:0,y:16,filter:'blur(8px)'}},{{autoAlpha:1,y:0,filter:'blur(0px)',duration:0.45,ease:'power2.out',immediateRender:false}},{f(w['s']-0.04)});")

# ======================= S10 — memorial -> Earth -> end card =======================
s = SC["s10"]
mem = ('<div id="mem" class="card" style="left:150px;top:250px;width:780px;padding:0;background:none;box-shadow:none;--r:-3deg">'
       '<img src="assets/memorial_print.jpg" style="width:780px;display:block;box-shadow:0 18px 40px rgba(0,0,0,.35)" alt="">'
       '<div class="credit">Memorial stone, Warsaw · Photo: Brandmeister / Togrul Safarov · Public Domain</div>'
       '<div class="tape" style="left:300px;top:-20px;transform:rotate(3deg)"></div></div>')
reported = '<div id="reported" class="tag" style="left:600px;top:178px;font-size:36px;transform:rotate(2deg)">REPORTED: SEPT 2017</div>'
lines10 = [("survived", "survived by", "l10a"), ("two", "two children,", "l10b"), ("grandchildren", "two grandchildren,", "l10c"),
           ("and", "and the entire", "l10d"), ("human", "human race.", "l10e")]
w10 = [w for w in WORDS if w["scene"] == "s10"]
def wt(word, after=0):
    for w in w10:
        if w["s"] >= after and re.sub(r"[^a-z]", "", w["w"].lower()) == word: return w["s"]
lt, after = [], C["survived"] - 0.01
for key, txt, i in lines10:
    t = wt(key, after); lt.append((t, txt, i)); after = t + 0.01
earth_txt = ('<div id="humanrace" class="hr" data-layout-allow-overlap="true">' +
             "".join(f'<div id="{i}" class="{ "hrbig" if i == "l10e" else ""}">{html.escape(txt)}</div>' for _, txt, i in lt) + '</div>')
earth = (f'<div id="earth" class="wash" style="opacity:0">{kb("kb10", "s10_earth")}'
         '<div class="wash" style="background:linear-gradient(rgba(240,232,212,0.85) 0%,rgba(240,232,212,0.55) 26%,rgba(240,232,212,0) 34%)"></div>'
         f'{earth_txt}</div>')
endcard = ('<div id="endcard" class="wash endcard" style="opacity:0" data-layout-allow-overlap="true">'
           '<div class="eklogo">PAPER TRAIL</div>'
           '<div class="strip ink big" id="e1">THE MAN WHO</div><div class="strip red big" id="e2">DID NOTHING</div>'
           '<div class="ename">Stanislav Petrov · 1939–2017</div>'
           + tag("t_closed", TYPED["t_closed"][1], 330, 1180, 44, -1.0) +
           '<div class="efollow" id="efollow">FOLLOW FOR FILE 02 →</div></div>')
type_anim("t_closed", TYPED["t_closed"][1], TYPED["t_closed"][0])
clip("sc10", s["start"], s["end"], mem + typed("t_died", 90, 170, 54, -2.0) + reported + earth + endcard)
J(f"tl.fromTo('#mem',{{y:-1600,rotation:-12}},{{y:0,rotation:-3,duration:0.6,ease:'back.out(1.05)',immediateRender:false}},{f(s['start']-0.05)});")
J(f"tl.to('#mem',{{scale:1.05,duration:{f(C['survived']-s['start'])},ease:'none'}},{f(s['start']+0.55)});")
J(f"tl.fromTo('#reported',{{autoAlpha:0,scale:0.8}},{{autoAlpha:1,scale:1,duration:0.2,ease:'back.out(2)',immediateRender:false}},{f(C['months'])});")
J(f"tl.to('#earth',{{opacity:1,duration:1.0,ease:'power1.inOut'}},{f(C['survived']-1.1)});")
kb_move("#kb10", C["survived"] - 1.1, s["end"], 0.86, 0.93, 0, 0, 150, 110)
for t, _, i in lt:
    J(f"tl.fromTo('#{i}',{{autoAlpha:0,y:20,filter:'blur(8px)'}},{{autoAlpha:1,y:0,filter:'blur(0px)',duration:0.5,ease:'power2.out',immediateRender:false}},{f(t-0.05)});")
J(f"tl.fromTo('#l10e',{{scale:0.92}},{{scale:1,duration:1.4,ease:'power2.out',immediateRender:false}},{f(lt[-1][0])});")
et = C["end"] + 0.25
J(f"tl.to('#endcard',{{opacity:1,duration:0.6}},{f(et)});")
J(f"tl.to('#humanrace',{{opacity:0,duration:0.5}},{f(et)});")
J(f"tl.fromTo('#e1',{{autoAlpha:0,x:-200}},{{autoAlpha:1,x:0,duration:0.4,ease:'power4.out',immediateRender:false}},{f(et+0.25)});")
J(f"tl.fromTo('#e2',{{autoAlpha:0,x:200}},{{autoAlpha:1,x:0,duration:0.4,ease:'power4.out',immediateRender:false}},{f(et+0.4)});")
J(f"tl.fromTo('#efollow',{{autoAlpha:0,y:20}},{{autoAlpha:1,y:0,duration:0.4,immediateRender:false}},{f(et+1.6)});")

# ======================= transitions =======================
body.append(f'<div id="tearwrap" class="clip" data-start="0" data-duration="{f(TOTAL)}" data-track-index="4" style="z-index:40;pointer-events:none">'
            '<img id="tear" src="assets/tear.png" style="position:absolute;top:-90px;left:0;width:1560px;height:2100px;opacity:0;visibility:hidden" alt=""></div>')
for sid in ["s04", "s05", "s06", "s09"]:
    tear(SC[sid]["start"])
# zoom-punch into S3
J(f"tl.fromTo('#sc03',{{scale:1.25,filter:'blur(10px)'}},{{scale:1,filter:'blur(0px)',duration:0.32,ease:'power3.out',immediateRender:false}},{f(SC['s03']['start'])});")

# ======================= captions (karaoke strips) =======================
HIDE = [(C["quote"] - 0.05, SC["s05"]["end"]), (C["nothing1"] - 0.05, SC["s09"]["end"]), (C["survived"] - 0.05, TOTAL)]
KEY = {"nuclear", "missile", "missile.", "launch", "sixty-nine", "paranoid", "fifth", "minutes", "strike", "gut",
       "false", "alarm", "twenty-three", "nothing", "sunlight", "satellite", "medal", "reprimanded", "secret", "fifteen",
       "wife", "ten", "died", "quietly", "two", "hundred", "nine"}
toks = []
for w in WORDS:
    if any(a <= w["s"] < b for a, b in HIDE): continue
    if toks and toks[-1]["w"].endswith("-") and toks[-1]["scene"] == w["scene"]:
        toks[-1] = {**toks[-1], "w": toks[-1]["w"] + w["w"], "e": w["e"]}; continue
    toks.append(dict(w))
chunks, cur = [], []
for i, w in enumerate(toks):
    cur.append(w)
    nxt = toks[i + 1] if i + 1 < len(toks) else None
    brk = (len(cur) >= 3 or sum(len(x["w"]) for x in cur) >= 15 or re.search(r"[.,?!]$", w["w"])
           or nxt is None or nxt["scene"] != w["scene"] or nxt["s"] - w["e"] > 0.5)
    if brk: chunks.append(cur); cur = []
cap_html = []
for ci, ch in enumerate(chunks):
    rot = (-1.6, 1.2, -0.8, 1.6)[ci % 4]
    spans = "".join(
        f'<span class="cw{" key" if re.sub(r"[^a-z-]", "", w["w"].lower()) in KEY else ""}" id="c{ci}_{wi}">{html.escape(w["w"].upper())}</span>'
        for wi, w in enumerate(ch))
    cap_html.append(f'<div class="cap" id="cap{ci}"><div class="capstrip" style="transform:rotate({rot}deg)">{spans}</div></div>')
    t_on = ch[0]["s"] - 0.06
    nxt_t = chunks[ci + 1][0]["s"] - 0.06 if ci + 1 < len(chunks) else TOTAL
    t_off = min(nxt_t, ch[-1]["e"] + 0.45)
    for a, b in HIDE:
        if t_on < a < t_off: t_off = a
    J(f"tl.fromTo('#cap{ci}',{{autoAlpha:0,y:26,scale:0.92}},{{autoAlpha:1,y:0,scale:1,duration:0.14,ease:'back.out(2.2)',immediateRender:false}},{f(t_on)});")
    J(f"tl.set('#cap{ci}',{{autoAlpha:0}},{f(t_off)});")
    for wi, w in enumerate(ch):
        k = " key" if re.sub(r"[^a-z-]", "", w["w"].lower()) in KEY else ""
        end_t = ch[wi + 1]["s"] if wi + 1 < len(ch) else t_off
        J(f"tl.set('#c{ci}_{wi}',{{attr:{{class:'cw on{k}'}}}},{f(w['s'])});")
        J(f"tl.set('#c{ci}_{wi}',{{attr:{{class:'cw{k}'}}}},{f(end_t)});")
clip("captions", 0, TOTAL, "".join(cap_html), z=50, style="pointer-events:none")

# ======================= global chrome: bug, progress, grain, vignette =======================
clip("chrome", 0, TOTAL,
     '<div id="bug" class="bug">PAPER TRAIL <b>·</b> FILE 01</div>'
     '<div class="progress"><div id="prog"></div></div>', z=60)
J(f"tl.fromTo('#prog',{{scaleX:0}},{{scaleX:1,duration:{f(TOTAL)},ease:'none',immediateRender:false}},0);")
J(f"tl.to('#bug',{{autoAlpha:0,duration:0.3}},{f(C['survived']-0.6)});")
clip("fx", 0, TOTAL, '<div id="grain" class="grain"></div><div class="vignette"></div>', z=70, style="pointer-events:none")
gt, k = 0.0, 0
while gt < TOTAL:
    J(f"tl.set('#grain',{{x:{-int(rnd()*512)},y:{-int(rnd()*512)}}},{f(gt)});"); gt += 1 / 15; k += 1
J(f"tl.to('#grain',{{opacity:0.07,duration:0.8}},{f(SC['s09']['start'])});")
J(f"tl.to('#grain',{{opacity:0.13,duration:0.8}},{f(SC['s10']['start'])});")

CSS = f"""
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
.strip{{display:inline-block;font-family:'Anton';font-size:128px;line-height:1.02;padding:6px 30px 2px;margin:6px 0;letter-spacing:.01em}}
.strip.ink{{background:{INK};color:{CREAM};transform:rotate(-2deg)}}
.strip.red{{background:{RED};color:{CREAM};transform:rotate(1.5deg)}}
.title .strip{{display:block;width:max-content;margin:8px auto}}
.kicker{{font-family:'DM Serif';font-style:italic;font-size:46px;color:{CREAM};margin-top:22px;text-shadow:0 3px 12px rgba(0,0,0,.85)}}
.tag{{position:absolute;font-family:'Elite',monospace;color:{INK};background:#F3EAD3;padding:10px 20px 8px;
  box-shadow:0 6px 14px rgba(0,0,0,.35);white-space:nowrap;visibility:hidden;opacity:0;transform-origin:0 50%}}
.tag .ch{{opacity:0}}
#nomedal,#reported{{visibility:hidden;opacity:0}}
.stamp{{position:absolute;font-family:'Anton';text-align:center;line-height:1.05;padding:14px 30px 10px;border:9px solid;
  border-radius:10px;background:rgba(246,238,220,.86);box-shadow:0 10px 26px rgba(0,0,0,.35);visibility:hidden;opacity:0;white-space:nowrap;
  -webkit-mask-image:url(assets/stampmask.png);-webkit-mask-size:100% 100%;mask-image:url(assets/stampmask.png);mask-size:100% 100%}}
.card{{position:absolute;background:#FBF7EE;padding:20px;box-shadow:0 24px 50px rgba(0,0,0,.40);transform:rotate(var(--r))}}
.card img{{display:block}}
.tape{{position:absolute;width:180px;height:54px;background:rgba(227,201,120,.62);box-shadow:0 2px 4px rgba(0,0,0,.15)}}
.credit{{font-family:'Elite',monospace;font-size:21px;color:#3b3226;text-align:center;margin-top:-104px;padding:0 30px;position:relative}}
.startglow{{position:absolute;display:flex;align-items:center;justify-content:center;opacity:0}}
.startglow span{{font-family:'Oswald';font-weight:700;font-size:180px;color:#FFF1EA;letter-spacing:.04em;
  text-shadow:0 0 18px #ff3b3b,0 0 50px #ff1a1a,0 0 110px #ff0000}}
.arcs{{position:absolute;left:0;top:0;filter:drop-shadow(0 0 10px rgba(255,40,40,.8))}}
.counter{{position:absolute;left:0;top:150px;width:1080px;height:420px;text-align:center;visibility:hidden;opacity:0}}
.num{{position:absolute;left:0;top:0;width:1080px;font-family:'Anton';font-size:300px;line-height:1;color:{RED};
  -webkit-text-stroke:6px {CREAM};text-shadow:0 10px 30px rgba(0,0,0,.6);visibility:hidden;opacity:0}}
.clabel{{position:absolute;left:50%;top:315px;transform:translateX(-50%);background:{CREAM};color:{INK};font-weight:700;
  font-size:40px;letter-spacing:.18em;padding:6px 22px;white-space:nowrap}}
.node{{position:absolute;font-family:'Elite',monospace;font-size:44px;color:{INK};background:#F7F0DE;padding:16px 28px 14px 60px;
  box-shadow:0 8px 18px rgba(0,0,0,.30);visibility:hidden;opacity:0;white-space:nowrap}}
.pin{{position:absolute;left:18px;top:50%;width:26px;height:26px;margin-top:-13px;border-radius:50%;
  background:radial-gradient(circle at 35% 35%,#ff6b6b,{RED} 60%,#6d0012);box-shadow:0 3px 5px rgba(0,0,0,.4)}}
.quote{{position:absolute;left:90px;top:560px;width:900px;font-family:'DM Serif';font-style:italic;font-size:80px;line-height:1.12;color:{CREAM}}}
.qw{{display:inline-block;visibility:hidden;opacity:0}}
.qmark{{font-family:'DM Serif';font-size:260px;line-height:.6;color:{RED};height:120px;visibility:hidden;opacity:0}}
.qby{{font-family:'Oswald';font-style:normal;font-size:40px;letter-spacing:.12em;color:{MUSTARD};margin-top:34px;text-transform:uppercase;visibility:hidden;opacity:0}}
.waitbox{{position:absolute;left:190px;top:700px;width:700px;padding:30px 0 26px;text-align:center;background:rgba(20,20,20,.86);
  border:3px solid {RED};box-shadow:0 0 40px rgba(200,16,46,.45);visibility:hidden;opacity:0}}
.wlabel{{font-weight:700;font-size:40px;letter-spacing:.2em;color:{CREAM}}}
.digits{{position:relative;height:210px}}
.dg{{position:absolute;left:0;width:700px;top:0;font-family:'Oswald';font-weight:700;font-size:200px;line-height:210px;color:{RED};
  font-variant-numeric:tabular-nums;visibility:hidden;opacity:0;text-shadow:0 0 24px rgba(255,30,30,.55)}}
.glint{{position:absolute;width:520px;height:520px;margin:-260px 0 0 -260px;mix-blend-mode:screen;opacity:0;
  background:radial-gradient(circle,rgba(255,252,230,1) 0%,rgba(255,220,120,.85) 9%,rgba(255,190,60,.35) 26%,rgba(255,190,60,0) 50%),linear-gradient(90deg,rgba(255,230,150,0) 0%,rgba(255,236,170,.9) 50%,rgba(255,230,150,0) 100%) center/100% 6px no-repeat,linear-gradient(0deg,rgba(255,230,150,0) 20%,rgba(255,236,170,.7) 50%,rgba(255,230,150,0) 80%) center/4px 100% no-repeat}}
.fivelabel{{position:absolute;left:50%;top:880px;white-space:nowrap;font-family:'Anton';font-size:84px;color:{CREAM};
  background:{INK};padding:4px 30px 0;letter-spacing:.02em;box-shadow:0 10px 24px rgba(0,0,0,.5);visibility:hidden;opacity:0}}
.bigserif{{position:absolute;left:0;top:640px;width:1080px;text-align:center;font-family:'DM Serif';font-style:italic;color:#FFF6E4;
  text-shadow:0 6px 30px rgba(0,0,0,.6)}}
#nl1{{font-size:150px;line-height:1.1;visibility:hidden;opacity:0}}
#nl2{{font-size:118px;line-height:1.1}}
#nl2 span{{display:inline-block;visibility:hidden;opacity:0}}
.hr{{position:absolute;left:0;top:96px;width:1080px;text-align:center;font-family:'DM Serif';font-size:60px;line-height:1.12;color:{INK}}}
.hr>div{{visibility:hidden;opacity:0}}
.hrbig{{font-style:italic;font-size:110px;color:{RED};line-height:1.05;margin-top:6px}}
.endcard{{background:rgba(16,13,10,.90);text-align:center;padding-top:520px}}
.eklogo{{font-family:'Oswald';font-weight:700;font-size:40px;letter-spacing:.5em;color:{RED};margin-bottom:34px;padding-left:.5em}}
.strip.big{{display:block;width:max-content;margin:10px auto;font-size:136px}}
.ename{{font-family:'DM Serif';font-style:italic;font-size:56px;color:{CREAM};margin-top:48px}}
.efollow{{position:absolute;left:0;width:1080px;top:1380px;font-weight:600;font-size:50px;letter-spacing:.14em;color:{MUSTARD};visibility:hidden;opacity:0}}
.cap{{position:absolute;left:0;top:1350px;width:1080px;text-align:center;visibility:hidden;opacity:0}}
.capstrip{{display:inline-block;background:#F6EEDC;padding:12px 18px 8px;box-shadow:0 8px 0 rgba(0,0,0,.28),0 14px 28px rgba(0,0,0,.25);max-width:960px}}
.cw{{display:inline-block;font-family:'Oswald';font-weight:600;font-size:76px;line-height:1.1;color:{INK};padding:0 8px;border-radius:6px}}
.cw.key{{color:{RED}}}
.cw.on{{background:{MUSTARD};color:{INK}}}
.cw.on.key{{background:{RED};color:{CREAM}}}
.bug{{position:absolute;right:40px;top:96px;font-weight:600;font-size:28px;letter-spacing:.22em;color:{CREAM};background:{INK};padding:8px 16px 6px}}
.bug b{{color:{RED}}}
.progress{{position:absolute;left:0;bottom:0;width:1080px;height:8px;background:rgba(20,20,20,.35)}}
#prog{{width:1080px;height:8px;background:{RED};transform-origin:0 50%}}
.grain{{position:absolute;left:0;top:0;width:1600px;height:2440px;background:url(assets/grain.png) repeat;opacity:.13;mix-blend-mode:overlay}}
.vignette{{position:absolute;left:0;top:0;width:1080px;height:1920px;background:radial-gradient(ellipse at 50% 48%,rgba(0,0,0,0) 55%,rgba(0,0,0,.42) 100%)}}
"""

doc = f"""<!doctype html>
<html lang="en" data-resolution="portrait">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<title>Paper Trail — File 01: The Man Who Did Nothing</title>
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
(HF / "index.html").write_text(doc)
for fn, content in [("hyperframes.json", '{\n  "$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",\n  "paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"},\n  "media": {"autoProxy": false}\n}\n'),
                    ("meta.json", '{"id": "paper-trail-ep01", "name": "Paper Trail — File 01: The Man Who Did Nothing"}\n'),
                    ("package.json", '{\n  "name": "paper-trail-ep01",\n  "private": true,\n  "type": "module",\n  "scripts": {\n    "check": "npx --yes hyperframes@0.8.137 check",\n    "render": "npx --yes hyperframes@0.8.137 render"\n  }\n}\n')]:
    (HF / fn).write_text(content)
print("index.html:", len(doc) // 1024, "KB,", len(js), "timeline ops,", len(chunks), "caption chunks, total", TOTAL)
