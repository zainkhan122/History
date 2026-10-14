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
rng = np.random.default_rng(1091859)
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

# 4) scene art: Lanczos upscale of the four original plates -> 1296x2322 (1.2x frame for Ken Burns headroom)
src = HERE / "assets"
for nm in ["s01_telegraph", "s02_sketch", "s05_campers", "s06_office"]:
    im = Image.open(src / f"{nm}.jpg").convert("RGB")
    im = im.resize((1296, 2322), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.6, percent=55, threshold=2))
    im.save(A / f"{nm}.jpg", quality=90)


def archival_print(im, size, centering=(0.5, 0.5), sepia=0.10, pad=24, foot=24):
    """Public-domain archive still -> mounted print (gentle sepia, cream border). Pixels stay ~1:1 in the card."""
    im = ImageOps.fit(im.convert("RGB"), size, Image.LANCZOS, centering=centering)
    im = ImageEnhance.Contrast(im).enhance(1.06)
    im = Image.blend(im, Image.new("RGB", im.size, (112, 86, 52)), sepia)
    out = Image.new("RGB", (im.width + 2 * pad, im.height + pad + foot), (246, 241, 230)); out.paste(im, (pad, pad))
    return out


# Carrington's own drawing (MNRAS 20, 1859): square crop around the spot group, his letters A-D kept in frame.
# build.py places the A/B/C/D glows in these crop coordinates (DRAW_BOX must match).
DRAW_BOX = (0.42, 0.12, 0.98, 0.98)
d = Image.open(src / "carrington_drawing.jpg").convert("L"); w, h = d.size
d = d.crop((int(DRAW_BOX[0] * w), int(DRAW_BOX[1] * h), int(DRAW_BOX[2] * w), int(DRAW_BOX[3] * h))).resize((920, 920), Image.LANCZOS)
d = ImageOps.autocontrast(d, cutoff=1)
ink = Image.merge("RGB", [d.point(lambda v, a=a, b=b: int(a + (b - a) * v / 255)) for a, b in ((28, 246), (24, 238), (22, 220))])
ink.save(A / "carrington_drawing.jpg", quality=92)
archival_print(Image.open(src / "carrington_portrait.jpg"), (560, 680), (0.5, 0.25), 0.06).save(A / "carrington_portrait.jpg", quality=90)
archival_print(Image.open(src / "redhill_observatory.jpg"), (900, 608), (0.5, 0.5), 0.12).save(A / "redhill_observatory.jpg", quality=90)

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
