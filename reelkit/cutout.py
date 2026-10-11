#!/usr/bin/env python3
"""
reelkit/cutout.py — background removal -> paper-collage STICKERS (rembg, MIT, CPU/ONNX).

Turns any keyframe element (a figure, a rocket, a book…) into a transparent cut-out with a
hand-cut white paper border + soft drop shadow, ready for render.py "sticker" events, which
fly / pop / drop pieces in on a spoken word ("assemble the collage" motion).

  python3 cutout.py keyframes/k1.png -o cutouts/k1_cut.png
  python3 cutout.py keyframes/k1.png -o cutouts/hero.png --crop 0.2,0.3,0.8,0.95   # region first (x0,y0,x1,y1 in 0..1)
  python3 cutout.py a.png b.png c.png --outdir cutouts                           # batch
      --model isnet-general-use (default, 179 MB — tested best on collage art) | u2net (fragments
              busy collage objects) | u2netp (tiny, 5 MB, rough)
              | birefnet-general-lite (best edges, slow + ~1.5 GB RAM — may OOM here)
      --border 14     paper border px (0 = none)      --no-shadow
      --rough 1.0     border edge irregularity (0 = clean vector, 1 = scissor-cut)
      --mask-only     write the alpha mask too (*_mask.png) — feed to inpaint.py to erase the object

Busy full-scene keyframes are "all foreground": always --crop to ONE object first.
Generate collage pieces on a FLAT, single-colour background for the cleanest cut
(prompt: "isolated paper cut-out of X on a plain flat #3B7A57 background").
"""
import argparse, os, sys
import numpy as np
from PIL import Image, ImageFilter, ImageChops

os.environ.setdefault("U2NET_HOME", os.path.expanduser("~/.cache/u2net"))
_S = {}

def session(name):
    if name not in _S:
        from rembg import new_session
        _S[name] = new_session(name)
    return _S[name]

def cut(im, model="isnet-general-use", border=14, shadow=True, rough=1.0, seed=0):
    from rembg import remove
    im = im.convert("RGB")
    # cap working size: 2 GB RAM sandbox; mask is upscaled back
    big = max(im.size); sc = min(1.0, 1600 / big)
    work = im.resize((int(im.width * sc), int(im.height * sc)), Image.LANCZOS) if sc < 1 else im
    mask = remove(work, session=session(model), only_mask=True, post_process_mask=True)
    mask = mask.convert("L").resize(im.size, Image.BILINEAR)
    m = np.asarray(mask, np.float32) / 255
    m = np.where(m > .5, 1.0, np.clip((m - .2) / .3, 0, 1))         # crisp paper edge, soft AA
    a = Image.fromarray((m * 255).astype(np.uint8))
    rgba = im.convert("RGBA"); rgba.putalpha(a)
    pad = border * 2 + (30 if shadow else 4)
    W, H = im.width + pad * 2, im.height + pad * 2
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    a_big = Image.new("L", (W, H), 0); a_big.paste(a, (pad, pad))
    if border > 0:
        # hand-cut border: dilate alpha, then wobble the edge with low-freq noise (scissors)
        b = a_big.filter(ImageFilter.MaxFilter(3))
        for _ in range(max(1, border // 3)): b = b.filter(ImageFilter.MaxFilter(7))
        b = b.filter(ImageFilter.GaussianBlur(2))
        if rough > 0:
            rng = np.random.default_rng(seed)
            n = Image.fromarray((rng.random((H // 24 + 2, W // 24 + 2)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)
            b = Image.fromarray(np.clip(np.asarray(b, np.float32) + (np.asarray(n, np.float32) - 128) * .9 * rough, 0, 255).astype(np.uint8))
        b = b.point(lambda v: 255 if v > 128 else 0).filter(ImageFilter.GaussianBlur(.8))
        paper = Image.new("RGBA", (W, H), (247, 242, 230, 255)); paper.putalpha(b)
        sil = b
    else:
        paper, sil = None, a_big
    if shadow:
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sh.putalpha(sil.point(lambda v: int(v * .45)).filter(ImageFilter.GaussianBlur(10)))
        canvas.alpha_composite(ImageChops.offset(sh, 9, 13))
    if paper is not None: canvas.alpha_composite(paper)
    canvas.alpha_composite(rgba, (pad, pad))
    bbox = canvas.getbbox()
    return canvas.crop(bbox) if bbox else canvas, mask

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+"); ap.add_argument("-o", "--out"); ap.add_argument("--outdir")
    ap.add_argument("--model", default="isnet-general-use"); ap.add_argument("--border", type=int, default=14)
    ap.add_argument("--no-shadow", action="store_true"); ap.add_argument("--rough", type=float, default=1.0)
    ap.add_argument("--crop"); ap.add_argument("--mask-only", action="store_true")
    x = ap.parse_args()
    if x.out and len(x.inputs) > 1: sys.exit("-o is for one input; use --outdir for batches")
    for k, p in enumerate(x.inputs):
        im = Image.open(p)
        if x.crop:
            x0, y0, x1, y1 = map(float, x.crop.split(","))
            im = im.crop((int(x0 * im.width), int(y0 * im.height), int(x1 * im.width), int(y1 * im.height)))
        st, mask = cut(im, x.model, x.border, not x.no_shadow, x.rough, seed=k)
        out = x.out or os.path.join(x.outdir or os.path.dirname(p) or ".", os.path.splitext(os.path.basename(p))[0] + "_cut.png")
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        st.save(out, optimize=True)
        if x.mask_only:
            mask.save(os.path.splitext(out)[0] + "_mask.png")
        cov = (np.asarray(mask) > 128).mean()
        print(f"{out}  {st.width}x{st.height}  subject={cov:.0%} of frame" + ("  (⚠ tiny/empty mask)" if cov < .02 else ""))

if __name__ == "__main__":
    main()
