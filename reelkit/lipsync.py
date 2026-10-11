#!/usr/bin/env python3
"""
reelkit/lipsync.py — talking collage characters with Rhubarb Lip Sync (MIT, CPU, offline).

Rhubarb turns each VO beat into timed mouth shapes (A–H, X). render.py's "mouth" event then
pastes the matching mouth sprite onto a character — the classic South-Park / paper-cut
"talking photo" look, no GPU lip-sync model needed and zero uncanny-valley risk.

  python3 lipsync.py reel.json                 # -> mouths.json (cues for every beat's VO)
  python3 lipsync.py reel.json --beats b2,b5   # only some beats
  python3 lipsync.py --make-sprites mouths/    # generate paper-cut mouth sprites A..H,X (PNG)
      --style paper (default) | ink        --lip "#B0303A"

Recognizer: English beats use the pocketSphinx recognizer + the beat's script as dialog hint
(more accurate). Non-English (Urdu etc.) auto-switches to "phonetic" (language-independent).

Mouth shapes (Preston Blair set):
  A closed M/B/P · B slightly open, teeth (K S T EE) · C open (EH AE) · D wide (AA)
  E rounded (AO ER) · F puckered (OO W) · G F/V teeth-on-lip · H L tongue · X rest
reel.json event:
  {"at": "b2", "type": "mouth", "beats": ["b2","b3"], "sprites": "mouths/", "pos": [0.62, 0.48], "w": 0.16}
"""
import argparse, json, os, re, subprocess, sys, tempfile
os.environ["PATH"] = os.path.expanduser("~/.cache/bin") + os.pathsep + os.environ.get("PATH", "")  # setup.sh tools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

RHUBARB = os.path.expanduser("~/.cache/bin/rhubarb")

def cues_for(wav, text=None, phonetic=False):
    with tempfile.TemporaryDirectory(dir=os.path.expanduser("~/.cache/tmp")) as td:
        src = os.path.join(td, "in.wav")       # Rhubarb wants 16-bit PCM WAV
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", wav, "-ac", "1", "-ar", "16000",
                        "-c:a", "pcm_s16le", src], check=True)
        cmd = [RHUBARB, "-q", "-f", "json", "--extendedShapes", "GHX", src]
        if phonetic: cmd += ["-r", "phonetic"]
        elif text:
            dp = os.path.join(td, "dialog.txt"); open(dp, "w").write(text); cmd += ["-d", dp]
        out = subprocess.run(cmd, capture_output=True, text=True)
        if out.returncode: raise RuntimeError(out.stderr[-400:])
        return [dict(s=round(c["start"], 3), e=round(c["end"], 3), v=c["value"]) for c in json.loads(out.stdout)["mouthCues"]]

def make_sprites(d, style="paper", lip="#B0303A"):
    from PIL import Image, ImageDraw, ImageFilter
    os.makedirs(d, exist_ok=True)
    lip = tuple(int(lip[i:i + 2], 16) for i in (1, 3, 5))
    W, H = 360, 240; cx, cy = W // 2, H // 2
    # (half-width, opening height, roundness 0..1, teeth_top, teeth_bottom, tongue)
    S = dict(A=(95, 6, 0, 0, 0, 0), B=(100, 34, .1, 1, 1, 0), C=(92, 62, .3, 1, 0, 1),
             D=(100, 96, .4, 1, 0, 1), E=(70, 66, .8, 0, 0, 1), F=(42, 40, 1, 0, 0, 0),
             G=(96, 30, .1, 1, 0, 0), H=(90, 70, .3, 1, 0, 2), X=(80, 4, 0, 0, 0, 0))
    for k, (hw, oh, rnd, tt, tb, tg) in S.items():
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
        lipw = 16
        box = (cx - hw, cy - oh // 2 - lipw, cx + hw, cy + oh // 2 + lipw)
        if style == "paper":                                   # cream paper backing = cut-out look
            pb = (box[0] - 14, box[1] - 14, box[2] + 14, box[3] + 14)
            dr.rounded_rectangle(pb, radius=int(40 + 60 * rnd), fill=(247, 242, 230, 255))
        dr.rounded_rectangle(box, radius=int(18 + (hw) * rnd), fill=lip + (255,))       # lips
        if oh > 8:
            inner = (cx - hw + lipw, cy - oh // 2, cx + hw - lipw, cy + oh // 2)
            dr.rounded_rectangle(inner, radius=int(10 + hw * rnd * .8), fill=(60, 14, 22, 255))
            iw = inner[2] - inner[0]
            if tt: dr.rectangle((inner[0] + iw * .12, inner[1], inner[2] - iw * .12, inner[1] + min(16, oh * .3)), fill=(250, 248, 240, 255))
            if tb: dr.rectangle((inner[0] + iw * .15, inner[3] - min(14, oh * .28), inner[2] - iw * .15, inner[3]), fill=(250, 248, 240, 255))
            if tg == 1: dr.ellipse((cx - iw * .3, inner[3] - oh * .45, cx + iw * .3, inner[3] + oh * .1), fill=(214, 92, 104, 255))
            if tg == 2: dr.ellipse((cx - iw * .18, inner[1] + 2, cx + iw * .18, inner[1] + oh * .5), fill=(214, 92, 104, 255))
        else:
            dr.line((cx - hw + 10, cy, cx + hw - 10, cy), fill=(60, 14, 22, 255), width=6)
        if k == "G":  # top teeth biting the lower lip
            dr.rectangle((cx - hw * .55, cy - 4, cx + hw * .55, cy + 12), fill=(250, 248, 240, 255))
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sh.putalpha(im.getchannel("A").point(lambda v: v * 0.4).filter(ImageFilter.GaussianBlur(6)))
        out = Image.new("RGBA", (W, H), (0, 0, 0, 0)); out.alpha_composite(sh, (5, 7)); out.alpha_composite(im)
        out.save(os.path.join(d, f"{k}.png"))
    print(f"wrote 9 mouth sprites to {d}  ({', '.join(S)})")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reel", nargs="?"); ap.add_argument("--beats"); ap.add_argument("--make-sprites")
    ap.add_argument("--style", default="paper"); ap.add_argument("--lip", default="#B0303A")
    ap.add_argument("--phonetic", action="store_true")
    x = ap.parse_args()
    if x.make_sprites: make_sprites(x.make_sprites, x.style, x.lip)
    if not x.reel: return
    import script as SC
    spec = json.load(open(x.reel)); root = os.path.dirname(os.path.abspath(x.reel))
    want = set(x.beats.split(",")) if x.beats else None
    out_p = os.path.join(root, "mouths.json")
    res = json.load(open(out_p)) if os.path.exists(out_p) else {}
    for b in spec["beats"]:
        if want and b["id"] not in want: continue
        text = SC.tts_text(b["script"]) if "script" in b else b.get("text", "")
        phon = x.phonetic or bool(re.search(r"[^\x00-\x7f’‘“”—–…]", text))   # non-English -> phonetic
        cues = cues_for(os.path.join(root, b["vo"]), None if phon else text, phon)
        res[b["vo"]] = cues
        print(f"{b['id']}: {len(cues):3d} mouth cues  ({'phonetic' if phon else 'pocketSphinx+dialog'})  "
              + "".join(c["v"] for c in cues[:40]))
    json.dump(res, open(out_p, "w"), indent=0)
    print("wrote", out_p)

if __name__ == "__main__":
    main()
