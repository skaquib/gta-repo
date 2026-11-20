"""
run_egg_sizes_blender_short.py — "Smallest vs biggest egg in the world",
the first FramedFacts Short rendered in Blender/Cycles (2026-11-01).

Owner, 2026-11-01: the scripts are good but the code-drawn animation looks
poor; no paid AI video for now -> use Blender (free). Egg series #4.
topic_validate.py: "smallest vs biggest egg" -- top Short 21.6M, 4 versions
over 1M in the last year.

FACTS (checked 2026-11-01):
  - smallest bird egg: vervain hummingbird, under 1 cm, ~0.37 g (Guinness
    "Smallest bird egg"; Wikipedia "Vervain hummingbird")
  - chicken egg ~5.7-6 cm long -> "about six times longer"
  - ostrich egg ~15 cm, typically 1.4 kg (range ~1.2-1.8), about two dozen
    chicken eggs (Food Republic, Tasting Table, How It Works)
  - elephant bird (extinct, Madagascar) egg ~30-34 cm, volume ~150 chicken
    eggs (Smithsonian via Fox News, Buffalo Museum of Science; UCL Grant
    Museum and Wikipedia say ~160) -> "about one hundred and fifty"
  - largest egg of any known vertebrate, dinosaurs included (Denver Museum
    of Nature & Science; Wikipedia "Elephant bird")

Steps (each re-runnable):
  python run_egg_sizes_blender_short.py voice     # Kokoro voice -> timing.json
  python run_egg_sizes_blender_short.py anchors   # Blender: label positions per frame
  python run_egg_sizes_blender_short.py frames A B   # Blender: render frames A..B (Cycles)
  python run_egg_sizes_blender_short.py compose   # overlays + voice + sfx + music -> mp4
"""
import os
import sys
import json
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import config

config.assert_safe_pipeline()

import motion_shorts as ms
import sfx
from run_strange_eggs_3d_short import _pill

VIDEO_ID = "egg_sizes_blender"
W, H = 1080, 1920
HERE = os.path.dirname(os.path.abspath(__file__))
FONT_T = os.path.join(HERE, "fonts", "BebasNeue-Regular.ttf")
GOLD, CYAN, RED, WHITE = (255, 206, 84), (56, 217, 255), (255, 84, 72), (255, 255, 255)
WORK = os.path.join(HERE, "output", "blender", VIDEO_ID)
BLENDER_PY = "/root/.venvs/blender/bin/python"
FPS = 24

SEGMENTS = [
    {"line": "This egg is bigger than any dinosaur egg ever found. But let's start small.",
     "head": "BIGGER THAN DINO EGGS", "sub": ""},
    {"line": "A hummingbird's egg is the smallest, less than one centimeter long.",
     "head": "SMALLEST EGG", "sub": "HUMMINGBIRD"},
    {"line": "A chicken egg is about six times longer.", "head": "CHICKEN EGG", "sub": "6X LONGER"},
    {"line": "An ostrich egg weighs about one and a half kilos. That's two dozen chicken eggs!",
     "head": "OSTRICH EGG", "sub": "= 24 CHICKEN EGGS"},
    {"line": "And the extinct elephant bird laid this. It holds about one hundred and fifty chicken eggs!",
     "head": "ELEPHANT BIRD EGG", "sub": "EXTINCT GIANT BIRD"},
    {"line": "Would you try an ostrich egg omelette? Comment yes or no!", "head": "WOULD YOU EAT IT?", "sub": ""},
]

SCRIPT = {
    "hook": SEGMENTS[0]["line"],
    "body": " ".join(s["line"] for s in SEGMENTS[1:-1]),
    "cta": SEGMENTS[-1]["line"],
    "title": "Smallest vs Biggest Egg in the World 🥚 #shorts",
    "tags": ["smallest egg", "biggest egg", "egg size comparison", "ostrich egg", "elephant bird egg",
             "hummingbird egg", "size comparison", "animal facts", "3d animation", "shorts"],
    "seo_description": (
        "From a hummingbird egg smaller than 1 cm to the extinct elephant bird's egg -- about 150 chicken eggs "
        "in one shell, bigger than any dinosaur egg ever found. An ostrich egg is about two dozen chicken eggs. "
        "Rendered in 3D by FramedFacts. Facts: Guinness World Records, Smithsonian, Denver Museum of Nature & "
        "Science. #animals #eggs #sizecomparison #3d #shorts"
    ),
    "ai_generated_visuals": False,
    "topic_category": "Animals",
}

# which egg gets the size bracket in each segment
BRACKETS = {1: ("hb", "UNDER 1 CM"), 2: ("ch", "~6 CM"), 3: ("os", "~15 CM"), 4: ("el", "~32 CM")}


def step_voice():
    os.makedirs(WORK, exist_ok=True)
    vo, starts, total = ms.build_voice(SEGMENTS, VIDEO_ID, speed=1.1)
    with open(os.path.join(WORK, "timing.json"), "w") as f:
        json.dump({"starts": starts, "total": total}, f)
    print("timing", [round(s, 2) for s in starts], round(total, 2), "->", int(round(total * FPS)) + 1, "frames")


def _blender(*args):
    cmd = [BLENDER_PY, os.path.join(HERE, "blender_egg_sizes_scene.py"), os.path.join(WORK, "timing.json"),
           os.path.join(WORK, "frames"), *map(str, args)]
    subprocess.run(cmd, check=True)


_cache = {"idx": None, "img": None}
_meta = {}


def _load_meta():
    if not _meta:
        a = json.load(open(os.path.join(WORK, "frames", "anchors.json")))
        _meta["anchors"], _meta["res"] = a["frames"], a["res"]
        _meta["pops"] = json.load(open(os.path.join(WORK, "frames", "pops.json")))
        _meta["timing"] = json.load(open(os.path.join(WORK, "timing.json")))
        _meta["last"] = max(int(k) for k in _meta["anchors"])
    return _meta


def _frame_img(idx):
    if _cache["idx"] != idx:
        p = os.path.join(WORK, "frames", f"f_{idx:04d}.png")
        _cache["img"] = Image.open(p).convert("RGBA").resize((W, H), Image.LANCZOS)
        _cache["idx"] = idx
    return _cache["img"]


def _anchor(idx, name):
    x, y, z = _meta["anchors"][str(idx)][name]
    s = W / _meta["res"][0]
    return x * s, y * s, z


def _pointer(d, target, label, y_off=-260):
    """Label + leader line, with the label kept fully inside the frame."""
    tx, ty = target
    f = ImageFont.truetype(FONT_T, 62)
    w = d.textlength(label, font=f)
    lx = min(max(tx - 180, w / 2 + 30), W - w / 2 - 30)
    ly = max(ty + y_off, 470)
    d.line([(lx, ly), (tx, ty)], fill=(0, 0, 0), width=9)
    d.line([(lx, ly), (tx, ty)], fill=CYAN, width=4)
    d.ellipse([tx - 11, ty - 11, tx + 11, ty + 11], fill=CYAN, outline=(0, 0, 0), width=3)
    d.text((lx, ly - 8), label, font=f, fill=CYAN, anchor="mb", stroke_width=5, stroke_fill=(0, 0, 0))


def _bracket(d, top, bot, label, appear):
    (x, y0, _), (_, y1, _) = top, bot
    x = min(max(x, 80), W - 250)            # keep the bracket and its label on screen
    ym = (y0 + y1) / 2
    h = (y1 - y0) / 2 * appear
    a, b = ym - h, ym + h
    for w, c in ((10, (0, 0, 0)), (4, GOLD)):
        d.line([(x, a), (x, b)], fill=c, width=w)
        d.line([(x - 16, a), (x + 16, a)], fill=c, width=w)
        d.line([(x - 16, b), (x + 16, b)], fill=c, width=w)
    if appear > 0.6:
        f = ImageFont.truetype(FONT_T, 66)
        tx = min(x + 26, W - d.textlength(label, font=f) - 20)
        d.text((tx, ym), label, font=f, fill=GOLD, anchor="lm", stroke_width=5, stroke_fill=(0, 0, 0))


def frame(t, i, t_in, starts):
    m = _load_meta()
    if abs(m["timing"]["starts"][1] - starts[1]) > 0.02:
        raise RuntimeError("voice timing changed since the Blender render -- re-run voice/anchors/frames")
    idx = min(int(t * FPS), m["last"])
    img = _frame_img(idx).copy()
    d = ImageDraw.Draw(img)
    seg_dur = (starts[i + 1] - starts[i]) if i + 1 < len(starts) else 3.0

    if i == 0 and t_in > 0.6:
        x, y, _ = _anchor(idx, "el_c")
        _pointer(d, (x, y), "ELEPHANT BIRD EGG")
    if i in BRACKETS and t_in > 0.5:
        k, lab = BRACKETS[i]
        _bracket(d, _anchor(idx, k + "_top"), _anchor(idx, k + "_bot"), lab, ms.ease(min(1, (t_in - 0.5) / 0.3)))
    if i in (3, 4):
        k, total_n = ("os", 24) if i == 3 else ("el", 150)
        n = sum(1 for p in m["pops"][k] if p <= t)
        if n:
            f = ImageFont.truetype(FONT_T, 104)
            txt = f"{n} CHICKEN EGGS"
            d.rounded_rectangle([W / 2 - d.textlength(txt, font=f) / 2 - 34, 1330, W / 2 + d.textlength(txt, font=f) / 2 + 34,
                                 1450], 36, fill=(0, 0, 0, 190), outline=GOLD if n == total_n else WHITE, width=5)
            d.text((W / 2, 1392), txt, font=f, fill=GOLD if n == total_n else WHITE, anchor="mm")
    if i == 5 and t_in > 0.8:
        ap = ms.ease(min(1, (t_in - 0.8) / 0.25))
        f = ImageFont.truetype(FONT_T, int(96 * (0.6 + 0.4 * ap)))
        for cx, lab, col in ((W / 2 - 200, "YES", (46, 204, 113)), (W / 2 + 200, "NO", RED)):
            d.rounded_rectangle([cx - 150, 1330, cx + 150, 1460], 40, fill=col, outline=(0, 0, 0), width=6)
            d.text((cx, 1397), lab, font=f, fill=WHITE, anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0))

    pop = 0.85 + 0.15 * ms.ease(t_in / 0.2)
    d.text((W / 2, 205), SEGMENTS[i]["head"], font=ImageFont.truetype(FONT_T, int(118 * pop)),
           fill=RED if i == 0 else GOLD, anchor="mm", stroke_width=8, stroke_fill=(0, 0, 0))
    if SEGMENTS[i]["sub"]:
        _pill(d, 325, SEGMENTS[i]["sub"], WHITE)
    ms.caption(d, 1590, SEGMENTS[i]["line"], size=46)
    ms.watermark(d)
    del seg_dur
    return np.array(img.convert("RGB"))


def sound_events(starts, total):
    m = _load_meta()
    ev = [(0.0, sfx.impact(0.75)), (0.0, sfx.whoosh(0.3, 0.35)), (starts[1] - 0.5, sfx.whoosh(0.6, 0.5))]
    for k in (2, 3, 4):
        ev += [(starts[k] + 0.1, sfx.whoosh(0.5, 0.35))]
    for k in (1, 2, 3, 4):
        ev.append((starts[k] + 0.5, sfx.pop(0.4)))
    for p in m["pops"]["os"]:
        ev.append((p, sfx.tick(1.4, 0.35)))
    for j, p in enumerate(m["pops"]["el"]):
        if j % 3 == 0:
            ev.append((p, sfx.tick(1.2 + 0.4 * j / 150, 0.3)))
    ev += [(m["pops"]["el"][-1] + 0.1, sfx.impact(0.6, low=False)), (starts[5] + 0.8, sfx.pop(0.45))]
    return ev


def step_compose():
    return ms.render_short(SCRIPT, SEGMENTS, VIDEO_ID, frame, speed=1.1, sfx_fn=sound_events, music_vol=0.08)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "voice":
        step_voice()
    elif cmd == "anchors":
        _blender("anchors")
    elif cmd == "frames":
        _blender(sys.argv[2], sys.argv[3])
    elif cmd == "compose":
        step_compose()
    else:
        print(__doc__)
