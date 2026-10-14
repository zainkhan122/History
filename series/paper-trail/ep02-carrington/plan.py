#!/usr/bin/env python3
"""Master timeline for Paper Trail File 02 (Carrington Event, 1859) — derived from the real VO durations + whisper word
times; pauses and the end hold come from the voice performance plan (voice.json, gated by reelkit/voice.py).
Writes timeline.json (scenes, absolute word times, named cues, typed labels) used by score.py and build.py."""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "reelkit"))
import voice as VOICE  # noqa: E402

W = json.load(open(HERE / "words.json"))
ORDER, END_HOLD = VOICE.gaps(HERE)

# The script owns the WORDS, whisper owns the TIMING (VOICE.script_words aligns them: "60" -> "sixty,", "11" ".18" -> "11:18").
TEXT = {l["id"]: l["text"] for l in VOICE.load_plan(HERE)["lines"]}

t = 0.0; scenes = []; words = []
for sid, vo, gap in ORDER:
    t += gap
    d = W[vo]["dur"]
    scenes.append({"id": sid, "vo": vo, "start": round(t, 3), "vo_end": round(t + d, 3)})
    for w in VOICE.script_words(TEXT[vo], W[vo]["words"]):
        words.append({"w": w["w"], "s": round(t + w["s"], 3), "e": round(t + w["e"], 3), "scene": sid})
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


def end_of(word, scene, nth=1):
    k = 0
    for w in words:
        if w["scene"] == scene and re.sub(r"[^a-z0-9]", "", w["w"].lower()) == word:
            k += 1
            if k == nth: return w["e"]
    raise KeyError((word, scene))


cues = {
    "unplugged": find("unplugged", "s01"), "talking": find("talking", "s01"), "power": find("power", "s01"), "sky": find("sky", "s01"),
    "september": find("september", "s02"), "time": find("1118", "s02"), "carrington": find("carrington", "s02"),
    "sketching": find("sketching", "s02"), "patches": find("patches", "s02"), "broke": find("broke", "s02"),
    "ran": find("ran", "s03"), "sixty": find("sixty", "s03"), "fading": find("fading", "s03"), "five": find("five", "s03"), "gone": find("gone", "s03"),
    "seventeen": find("seventeen", "s04"), "magnetic": find("magnetic", "s04"), "shake": find("shake", "s04"),
    "blood": find("blood", "s04"), "cuba": find("cuba", "s04"),
    "rocky": find("rocky", "s05"), "campers": find("campers", "s05"), "breakfast": find("breakfast", "s05"), "dawn": find("dawn", "s05"),
    "sparks": find("sparks", "s06"), "shocks": find("shocks", "s06"), "fire": find("fire", "s06"),
    "boston": find("boston", "s07"), "portland": find("portland", "s07"), "disconnected": find("disconnected", "s07"),
    "hours": find("hours", "s07"), "alone": find("alone", "s07"),
    "flare": find("flare", "s08"), "connected": find("connected", "s08"), "swallow": find("swallow", "s08"), "summer": find("summer", "s08"),
    "july": find("july", "s09"), "orbit": find("orbit", "s09"), "week": find("week", "s09"), "hitus": find("hit", "s09"),
    "white": find("white", "s02"), "storm": find("storm", "s08"), "find": find("find", "s10"), "next": find("next", "s10"), "wires": find("wires", "s10"), "end": scenes[-1]["vo_end"],
}
S = {s["id"]: s for s in scenes}
# typewriter labels (time, text, id) — shared by build.py (visual) and score.py (key clicks). Every one maps to a claim.
typed = [
    (cues["time"] - 0.1, "01.09.1859 · 11:18 A.M.", "t_date"),
    (cues["time"] + 1.15, "REDHILL, SURREY · PRIVATE OBSERVATORY", "t_place"),
    (cues["seventeen"] - 0.05, "+17 HOURS", "t_hours"),
    (cues["rocky"] - 0.05, "ROCKY MOUNTAIN NEWS, 1859", "t_rmn"),
    (cues["july"] - 0.05, "23.07.2012", "t_2012"),
    (total - 3.2, "FILE 02 · CLOSED", "t_closed"),
]
typed = [(round(a, 3), b, c) for a, b, c in typed]
json.dump({"total": total, "scenes": scenes, "words": words, "cues": {k: round(v, 3) for k, v in cues.items()}, "typed": typed},
          open(HERE / "timeline.json", "w"), indent=1)
if __name__ == "__main__":
    print("total", total)
    for s in scenes: print(s)
    print(" ".join(w["w"] for w in words))
