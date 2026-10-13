#!/usr/bin/env python3
"""Master timeline for Paper Trail Ep.01 — derived from the real VO clip durations + whisper word times.
Writes timeline.json (scenes, absolute word times, named cues) used by score.py and build.py."""
import json, re
from pathlib import Path
HERE = Path(__file__).resolve().parent
W = json.load(open(HERE / "words.json"))

# (scene id, vo clip, gap BEFORE the clip) + end hold come from the voice performance plan (voice.json):
# pauses are part of the performance, so they live with tone/energy and are gated by reelkit/voice.py.
import sys
sys.path.insert(0, str(HERE.parents[2] / "reelkit"))
import voice as VOICE
ORDER, END_HOLD = VOICE.gaps(HERE)

# The script owns the words (whisper only gives timing) — fix ASR spellings/number formatting
FIX = {"26,": "26TH,", "1983,": "1983,", "-nine": "NINE", "23": "TWENTY-THREE", "15": "FIFTEEN", "10": "TEN"}

t = 0.0; scenes = []; words = []
for sid, vo, gap in ORDER:
    t += gap
    d = W[vo]["dur"]
    scenes.append({"id": sid, "vo": vo, "start": round(t, 3), "vo_end": round(t + d, 3)})
    for w in W[vo]["words"]:
        txt = w["w"]
        if txt == "sixty" or txt == "sixty-": txt = "sixty-"
        words.append({"w": FIX.get(txt, txt), "s": round(t + w["s"], 3), "e": round(t + w["e"], 3), "scene": sid})
    t += d
total = round(t + END_HOLD, 2)
for i, s in enumerate(scenes):            # each scene's visual runs until the next scene's VO starts
    s["end"] = scenes[i + 1]["start"] if i + 1 < len(scenes) else total

def find(word, scene, nth=1):
    k = 0
    for w in words:
        if w["scene"] == scene and re.sub(r"[^a-z0-9]", "", w["w"].lower()) == word:
            k += 1
            if k == nth: return w["s"]
    raise KeyError((word, scene))

cues = {
    "nuclear": find("nuclear", "s01"),
    "paranoid": find("paranoid", "s02"), "died269": find("died", "s02"),
    "launch": find("launch", "s03"),
    "m2": find("second", "s03"), "m3": find("third", "s03"), "m4": find("fourth", "s03"), "m5": find("fifth", "s03"),
    "chain": find("chain", "s04"), "minutes": find("minutes", "s04"), "strike": find("strike", "s04"),
    "petrov": find("petrov", "s05"), "gut": find("gut", "s05"), "quote": find("when", "s05"),
    "falsealarm": find("false", "s06"), "waited": find("waited", "s06"), "nothingcame": find("nothing", "s06"),
    "sunlight": find("sunlight", "s07"), "satellite": find("satellite", "s07"),
    "medal": find("medal", "s08"), "reprimanded": find("reprimanded", "s08"), "secret": find("secret", "s08"),
    "wife": find("wife", "s09"), "nothing1": find("nothing", "s09", 2), "didnothing": find("did", "s09"),
    "died": find("died", "s10"), "months": find("months", "s10"), "survived": find("survived", "s10"),
    "entire": find("entire", "s10"), "end": scenes[-1]["vo_end"],
}
S = {s["id"]: s for s in scenes}
# typewriter labels (time, text, id) — shared by build.py (visual) and score.py (key clicks)
typed = [
    (3.05, "26.09.1983 — SHORTLY AFTER MIDNIGHT", "t_date"),
    (4.55, "SERPUKHOV-15 · EARLY-WARNING BUNKER", "t_place"),
    (S["s02"]["start"] + 0.55, "01.09.1983 · KAL 007 SHOT DOWN", "t_kal"),
    (cues["petrov"] - 0.05, "LT. COL. STANISLAV PETROV · AGE 44", "t_name"),
    (cues["sunlight"] + 1.6, "CAUSE: SUNLIGHT ON HIGH CLOUDS", "t_cause"),
    (cues["died"] + 0.1, "19.05.2017", "t_died"),
    (total - 3.2, "FILE 01 · CLOSED", "t_closed"),
]
typed = [(round(a, 3), b, c) for a, b, c in typed]
json.dump({"total": total, "scenes": scenes, "words": words, "cues": cues, "typed": typed}, open(HERE / "timeline.json", "w"), indent=1)
if __name__ == "__main__":
    print("total", total)
    for s in scenes: print(s)
    print(cues)
