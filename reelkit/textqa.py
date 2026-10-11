#!/usr/bin/env python3
"""Readability gate: every text that appears on screen must be legible on a phone.
  python3 reelkit/textqa.py <hf_dir> [--step 0.5] [--report textqa.json] [--sheet fails.jpg]
Method: textqa.cjs screenshots each visible text unit with and without its glyphs (plates and backgrounds kept).
Glyph-core pixels are those that changed AND match one of the unit's text colours. For those pixels we compute the
WCAG contrast between the text colour and what is directly behind the glyph. The score is the 10th percentile,
so busy backgrounds can't hide behind an average.
Thresholds (stricter than WCAG because the text moves over video): FAIL < 3.0 · WARN < 4.5 · PASS ≥ 4.5.
Outlines (-webkit-text-stroke ≥ 3 px) count as a plate. Text shadows/halos are ignored (conservative): a plate or scrim is the reliable fix, not a glow.
Exit 1 on any FAIL."""
import argparse, json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ap = argparse.ArgumentParser(); ap.add_argument("hf"); ap.add_argument("--step", type=float, default=0.5)
ap.add_argument("--report"); ap.add_argument("--sheet"); ap.add_argument("--keep", action="store_true")
a = ap.parse_args()
hf = Path(a.hf).resolve()
total = float(re.search(r'data-composition-id="main"[^>]*data-duration="([\d.]+)"', (hf / "index.html").read_text()).group(1))
times = [round(i * a.step, 3) for i in range(1, int(total / a.step))]
tmp = Path(tempfile.mkdtemp(prefix="textqa_", dir=os.environ.get("TMPDIR", str(Path.home() / ".cache/tmp"))))
node_path = subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip() + "/hyperframes/node_modules"
r = subprocess.run(["node", str(HERE / "textqa.cjs"), str(hf), str(tmp), ",".join(map(str, times))],
                   env={**os.environ, "NODE_PATH": node_path}, capture_output=True, text=True)
print(r.stdout.strip() or r.stderr[-2000:])
if r.returncode: sys.exit(2)
meta = json.load(open(tmp / "meta.json"))

def lum(rgb):
    c = rgb / 255.0; c = np.where(c <= 0.03928, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * c[..., 0] + 0.7152 * c[..., 1] + 0.0722 * c[..., 2]

def parse(c):
    v = [float(x) for x in re.findall(r"[\d.]+", c)]
    return np.array(v[:3]), (v[3] if len(v) > 3 else 1.0)

rows = []
for m in meta:
    T = np.asarray(Image.open(tmp / f"{m['tag']}_t.png").convert("RGB"), float)
    B = np.asarray(Image.open(tmp / f"{m['tag']}_b.png").convert("RGB"), float)
    cols = [parse(c)[0] for c in m["colors"] if parse(c)[1] > 0.5]
    if not cols: continue
    changed = np.abs(T - B).sum(-1) > 60
    d = np.stack([np.sqrt(((T - c) ** 2).sum(-1)) for c in cols])          # distance to each text colour
    near = d.argmin(0); core = changed & (d.min(0) < 32)                    # glyph cores, not antialiased edges
    if core.sum() < 25: continue                                           # covered by a wipe / mid-transition
    score = 99.0
    for i, c in enumerate(cols):                                           # worst colour group (e.g. red keyword)
        g = core & (near == i)
        if g.sum() < 25: continue
        lt, lb = lum(np.array(c)), lum(B[g])
        ratio = (np.maximum(lt, lb) + 0.05) / (np.minimum(lt, lb) + 0.05)
        score = min(score, float(np.percentile(ratio, 10)))
    if score == 99.0: continue
    if m.get("stroke"):                                   # a solid outline ≥3 px is the glyph's own plate
        lf = lum(np.array(cols[0])); ls = lum(parse(m["stroke"]["color"])[0])
        score = max(score, float((max(lf, ls) + 0.05) / (min(lf, ls) + 0.05)))
    status = "FAIL" if score < 3.0 else "WARN" if score < 4.5 else "PASS"
    rows.append({**m, "contrast_p10": round(score, 2), "status": status})

worst = {}
for row in rows:                                          # one line per text unit: its worst moment
    k = (row["id"], row["text"])
    if k not in worst or row["contrast_p10"] < worst[k]["contrast_p10"]: worst[k] = row
units = sorted(worst.values(), key=lambda r: r["contrast_p10"])
n = {s: sum(u["status"] == s for u in units) for s in ("FAIL", "WARN", "PASS")}
for u in units:
    if u["status"] != "PASS":
        print(f"  {u['status']}  {u['contrast_p10']:>5.2f}:1  t={u['t']:>5.1f}s  {u['size']:.0f}px  {u['text'][:60]!r}")
print(f"text units: {len(units)}  PASS {n['PASS']}  WARN {n['WARN']}  FAIL {n['FAIL']}")
if a.report: Path(a.report).write_text(json.dumps({"summary": n, "units": units}, indent=1, ensure_ascii=False) + "\n")
if a.sheet:
    bad = [u for u in units if u["status"] != "PASS"][:24]
    if bad:
        tiles = []
        for u in bad:
            im = Image.open(tmp / f"{u['tag']}_t.png").convert("RGB"); im.thumbnail((520, 220))
            c = Image.new("RGB", (540, 260), (30, 30, 30)); c.paste(im, (10, 34))
            ImageDraw.Draw(c).text((10, 8), f"{u['status']} {u['contrast_p10']}:1 t={u['t']}s", fill=(255, 210, 0)); tiles.append(c)
        sheet = Image.new("RGB", (540 * 2, 260 * ((len(tiles) + 1) // 2)), (0, 0, 0))
        for i, c in enumerate(tiles): sheet.paste(c, ((i % 2) * 540, (i // 2) * 260))
        sheet.save(a.sheet, quality=88)
if not a.keep: shutil.rmtree(tmp, ignore_errors=True)
sys.exit(1 if n["FAIL"] else 0)
