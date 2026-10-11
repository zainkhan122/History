#!/usr/bin/env python3
"""Procedural + prepared visual assets for the HyperFrames project (seeded, deterministic).
usage: python3 make_assets.py <hf_dir>   -> writes <hf_dir>/assets/*"""
import sys, shutil
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter, ImageDraw, ImageEnhance, ImageOps

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
HF = Path(sys.argv[1]); A = HF / "assets"; A.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(26091983)
W, H = 1080, 1920


def fbm(h, w, octaves=5, base=6):
    out = np.zeros((h, w), np.float32); amp = 1.0; tot = 0
    for o in range(octaves):
        s = base * 2 ** o
        small = rng.random((max(2, h * s // w), s)).astype(np.float32)
        im = Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        out += np.asarray(im, np.float32) / 255 * amp; tot += amp; amp *= 0.5
    return out / tot


def paper(w, h, base=(239, 230, 210), stains=3, vignette=0.55):
    n = fbm(h, w)
    img = np.ones((h, w, 3), np.float32) * np.array(base, np.float32)
    img *= (0.93 + 0.12 * n)[..., None]
    fine = rng.normal(0, 4.5, (h, w, 1)).astype(np.float32)
    img += fine
    pil = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(pil, "RGBA")
    for _ in range(1400):                       # fibres
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        L = rng.uniform(6, 26); a = rng.uniform(0, np.pi)
        c = (120, 100, 70, int(rng.uniform(10, 30))) if rng.random() < 0.6 else (255, 252, 240, int(rng.uniform(20, 45)))
        d.line([(x, y), (x + L * np.cos(a), y + L * np.sin(a))], fill=c, width=1)
    st = Image.new("L", (w, h), 0); sd = ImageDraw.Draw(st)
    for _ in range(stains):                     # coffee/age rings
        cx, cy, r = rng.uniform(0, w), rng.uniform(0, h), rng.uniform(90, 220)
        for k in range(10):
            rr = r + rng.normal(0, 3)
            sd.ellipse([cx - rr, cy - rr * 0.95, cx + rr, cy + rr * 0.95], outline=int(10 + k * 2), width=3)
        sd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=7)
    st = st.filter(ImageFilter.GaussianBlur(5))
    tint = Image.new("RGB", (w, h), (150, 105, 50))
    pil = Image.composite(tint, pil, st.point(lambda v: min(255, v * 2)))
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    vig = 1 - vignette * np.clip(r - 0.55, 0, 1) ** 1.6
    arr = np.asarray(pil, np.float32) * vig[..., None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


# 1) paper background + darker card-back paper
paper(W, H).save(A / "bg_paper.jpg", quality=90)
paper(W, H, base=(226, 214, 188), stains=1, vignette=0.3).save(A / "paper_dark.jpg", quality=88)

# 2) grain tile (luminance noise, alpha) — animated via stepped GSAP background shifts
g = rng.normal(128, 42, (512, 512)).clip(0, 255).astype(np.uint8)
gi = Image.fromarray(g).filter(ImageFilter.GaussianBlur(0.6))
Image.merge("LA", (gi, Image.new("L", (512, 512), 255))).convert("RGBA").save(A / "grain.png", optimize=True)

# 3) torn-paper wipe sheet: cream sheet with a ragged leading (left) edge and soft shadow
TW, TH = 1500, 2100
sheet = paper(TW, TH, base=(236, 226, 204), stains=1, vignette=0.15).convert("RGBA")
def ragged(x0):
    e = np.zeros(TH); x = x0
    for yv in range(TH):
        x += rng.normal(0, 2.2); x = np.clip(x, x0 - 45, x0 + 45); e[yv] = x
    return np.convolve(e, np.ones(5) / 5, mode="same")
edge, edge2 = ragged(70.0), ragged(TW - 70.0)
edge[:3] = edge[3]; edge[-3:] = edge[-4]; edge2[:3] = edge2[3]; edge2[-3:] = edge2[-4]
mask = Image.new("L", (TW, TH), 0); md = ImageDraw.Draw(mask)
md.polygon([(edge[yv], yv) for yv in range(TH)] + [(edge2[yv], yv) for yv in range(TH - 1, -1, -1)], fill=255)
rim = Image.new("L", (TW, TH), 0); rd = ImageDraw.Draw(rim)
rd.line([(edge[yv] + 6, yv) for yv in range(TH)], fill=255, width=12)
rd.line([(edge2[yv] - 6, yv) for yv in range(TH)], fill=255, width=12)
rim = rim.filter(ImageFilter.GaussianBlur(1.2))
white = Image.new("RGBA", (TW, TH), (252, 249, 240, 255))
sheet = Image.composite(white, sheet, rim)
sheet.putalpha(mask)
shadow = Image.new("RGBA", (TW + 60, TH), (0, 0, 0, 0))
sm = mask.filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.45))
shadow.paste((20, 15, 10, 255), (0, 0), sm)
out = Image.new("RGBA", (TW + 60, TH), (0, 0, 0, 0))
out.alpha_composite(shadow, (0, 0)); out.alpha_composite(sheet, (30, 0))
out.save(A / "tear.png", optimize=True)
# 3b) distressed ink mask for rubber stamps (alpha speckle)
sm = fbm(400, 800, octaves=6, base=10)
fine = rng.random((400, 800)).astype(np.float32)
alpha = np.clip((sm * 0.7 + fine * 0.3 - 0.30) * 6, 0, 1)
alpha[fine > 0.985] = 0
Image.merge("RGBA", [Image.new("L", (800, 400), 0)] * 3 + [Image.fromarray((alpha * 255).astype(np.uint8))]).save(A / "stampmask.png", optimize=True)

# 4) scene art: Lanczos upscale 768x1376 -> 1296x2322 (1.2x frame for Ken Burns headroom) + light sharpen
src = HERE / "assets"
names = ["s01_bunker", "s02_jet", "s03_console", "s04_globe", "s05_officer", "s06_phone",
         "s07_sunlight", "s08_logbook", "s09_kitchen", "s10_earth"]
for nm in names:
    im = Image.open(src / f"{nm}.jpg").convert("RGB")
    im = im.resize((1296, 2322), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.6, percent=55, threshold=2))
    im.save(A / f"{nm}.jpg", quality=90)
# warm grade for the kitchen (memory) scene is done in CSS; memorial photo -> archival print look
m = Image.open(src / "memorial_stone.jpg").convert("RGB")
m = ImageOps.fit(m, (900, 1200), Image.LANCZOS, centering=(0.5, 0.45))
m = ImageEnhance.Color(m).enhance(0.55); m = ImageEnhance.Contrast(m).enhance(1.08)
sep = Image.new("RGB", m.size, (112, 86, 52))
m = Image.blend(m, sep, 0.10)
border = Image.new("RGB", (m.width + 56, m.height + 150), (246, 241, 230))
border.paste(m, (28, 28))
border.save(A / "memorial_print.jpg", quality=90)

# 5) fonts + gsap (local, no CDN)
F = HF / "fonts"; F.mkdir(exist_ok=True)
for f in ["Oswald.ttf", "Anton-Regular.ttf", "DMSerifDisplay-Regular.ttf", "DMSerifDisplay-Italic.ttf", "SpecialElite-Regular.ttf"]:
    p = REPO / "fonts" / f
    if not p.exists():
        cand = list((REPO / "fonts").glob(f.split("-")[0] + "*"))
        p = cand[0] if cand else None
    if p: shutil.copy(p, F / p.name); print("font", p.name)
shutil.copy(REPO / "engine/vendor/gsap.min.js", HF / "gsap.min.js")
print("assets ->", A)
