#!/usr/bin/env python3
"""
reelkit/inpaint.py — erase garbled AI text / logos / stray objects with LaMa (Apache-2.0, ONNX, CPU),
then optionally re-typeset a clean headline in the reel's font. Fixes the #1 keyframe defect
(misspelled baked-in text) WITHOUT another image-generation round trip or losing the composition.

  python3 inpaint.py k1.png --box 0.08,0.05,0.92,0.22 -o k1_fixed.png
  python3 inpaint.py k1.png --box 0.08,0.05,0.92,0.22 --text "MOVING IN" --color "#C8553D" -o k1_fixed.png
  python3 inpaint.py k1.png --mask cutouts/hero_mask.png -o k1_clean.png     # remove an object (mask from cutout.py)
     --box can repeat; coords are fractions (x0,y0,x1,y1) of the image
     --shadow "#D93A2B"  offset print shadow colour (match the original headline)
     --font ~/fonts/Anton-Regular.ttf  --stroke 0  --rtl (Urdu, use NotoNastaliqUrdu.ttf)
     --dilate 9   grow mask px (catch anti-aliased glyph edges)

How: each masked region is cropped with context (>=512 px square), run through LaMa at 512²,
scaled back and feather-pasted ONLY inside the mask, so the rest of the image is untouched.
~6-10 s per region on 2 CPUs. Best on flat/paper textures (ideal for collage); large busy
regions (>40% of the image) blur — regenerate those instead.
"""
import argparse, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

MODEL = os.path.expanduser("~/.cache/models/lama_fp32.onnx")
_SESS = None

def sess():
    global _SESS
    if _SESS is None:
        import onnxruntime as ort
        o = ort.SessionOptions(); o.intra_op_num_threads = 2
        _SESS = ort.InferenceSession(MODEL, o, providers=["CPUExecutionProvider"])
    return _SESS

def lama512(img, mask):
    x = np.asarray(img.convert("RGB").resize((512, 512), Image.BICUBIC), np.float32).transpose(2, 0, 1)[None] / 255
    m = (np.asarray(mask.resize((512, 512), Image.NEAREST), np.float32) > 127).astype(np.float32)[None, None]
    y = sess().run(None, {"image": x, "mask": m})[0][0].transpose(1, 2, 0)
    if y.max() <= 1.5: y = y * 255
    return Image.fromarray(y.clip(0, 255).astype(np.uint8))

def inpaint(im, mask, dilate=9):
    im = im.convert("RGB"); W, H = im.size
    mask = mask.convert("L").point(lambda v: 255 if v > 127 else 0)
    if dilate: mask = mask.filter(ImageFilter.MaxFilter(dilate | 1))
    out = im.copy()
    # one pass per connected blob (via bbox of labelled regions), simple flood labelling on a coarse grid
    from scipy import ndimage
    lab, n = ndimage.label(np.asarray(mask) > 0)
    for sl in ndimage.find_objects(lab):
        y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
        side = int(max(512, (x1 - x0) * 1.7, (y1 - y0) * 1.7)); side = min(side, max(W, H))
        cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
        L = min(max(0, cx - side // 2), max(0, W - side)); T = min(max(0, cy - side // 2), max(0, H - side))
        box = (L, T, min(W, L + side), min(H, T + side))
        crop, mcrop = out.crop(box), mask.crop(box)
        fill = lama512(crop, mcrop).resize(crop.size, Image.LANCZOS)
        feather = mcrop.filter(ImageFilter.GaussianBlur(3))
        crop.paste(fill, (0, 0), feather); out.paste(crop, box[:2])
    return out

def typeset(im, box, text, font, color, stroke, rtl=False, shadow="#141414"):
    W, H = im.size; x0, y0, x1, y1 = box[0] * W, box[1] * H, box[2] * W, box[3] * H
    d = ImageDraw.Draw(im); bw, bh = (x1 - x0) * .92, (y1 - y0) * .86
    size = int(bh)
    while size > 10:
        f = ImageFont.truetype(font, size); bb = d.textbbox((0, 0), text, font=f, stroke_width=stroke)
        if bb[2] - bb[0] <= bw and bb[3] - bb[1] <= bh: break
        size = int(size * .94)
    col = tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))
    tx = x0 + ((x1 - x0) - (bb[2] - bb[0])) / 2 - bb[0]; ty = y0 + ((y1 - y0) - (bb[3] - bb[1])) / 2 - bb[1]
    # paper-print feel: slight offset shadow
    sc = tuple(int(shadow[i:i + 2], 16) for i in (1, 3, 5)); o = size * .055
    d.text((tx + o, ty + o * .6), text, font=f, fill=sc, stroke_width=stroke,
           stroke_fill=sc, direction="rtl" if rtl else None)
    d.text((tx, ty), text, font=f, fill=col, stroke_width=stroke, stroke_fill=(20, 20, 20),
           direction="rtl" if rtl else None)
    return im

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image"); ap.add_argument("-o", "--out")
    ap.add_argument("--box", action="append", default=[]); ap.add_argument("--mask")
    ap.add_argument("--text"); ap.add_argument("--color", default="#F2B33D"); ap.add_argument("--shadow", default="#141414")
    ap.add_argument("--font", default=os.path.expanduser("~/fonts/Anton-Regular.ttf"))
    ap.add_argument("--stroke", type=int, default=0); ap.add_argument("--rtl", action="store_true")
    ap.add_argument("--dilate", type=int, default=9)
    x = ap.parse_args()
    im = Image.open(x.image).convert("RGB"); W, H = im.size
    mask = Image.new("L", (W, H), 0); d = ImageDraw.Draw(mask)
    boxes = [tuple(map(float, b.split(","))) for b in x.box]
    for b in boxes: d.rectangle((b[0] * W, b[1] * H, b[2] * W, b[3] * H), fill=255)
    if x.mask:
        m = Image.open(x.mask).convert("L").resize((W, H)); mask.paste(255, (0, 0), m.point(lambda v: 255 if v > 127 else 0))
    if not mask.getbbox(): raise SystemExit("nothing to inpaint: give --box or --mask")
    import time; t = time.time()
    res = inpaint(im, mask, x.dilate)
    if x.text:
        if not boxes: raise SystemExit("--text needs a --box to place it in")
        res = typeset(res, boxes[0], x.text, x.font, x.color, x.stroke, x.rtl, x.shadow)
    out = x.out or os.path.splitext(x.image)[0] + "_fixed.png"
    res.save(out); print(f"wrote {out}  ({time.time() - t:.1f}s, {(np.asarray(mask) > 0).mean():.0%} of image inpainted)")

if __name__ == "__main__":
    main()
