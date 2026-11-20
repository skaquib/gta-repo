"""
run_cat_teaser_short.py — vertical teaser Short that sends viewers to the
first long video ("What Does Your Cat Really Think You Are?", iROMkiiM8aE).

Why: 10 hours after upload the long video had 4 views. A new long video on
a small channel gets little browse traffic, while our Shorts reliably reach
~1.3K. The teaser reuses the long video's own cartoon scenes (same art,
same facts) in a 9:16 frame: big headline on top, the 16:9 scene in the
middle, captions and a "full video" banner below. The link goes in the
description and the first comment.
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import config

config.assert_safe_pipeline()

import motion_shorts as ms
import sfx
import run_cat_thinks_long as cat

VIDEO_ID = "cat_teaser_short"
LONG_URL = "https://www.youtube.com/watch?v=iROMkiiM8aE"
W, H = 1080, 1920
HERE = os.path.dirname(os.path.abspath(__file__))
FONT_T = os.path.join(HERE, "fonts", "BebasNeue-Regular.ttf")
GOLD, WHITE = (255, 214, 70), (255, 255, 255)


def _shot(line_start, k=0):
    for seg in cat.SEGMENTS:
        if seg["line"].startswith(line_start):
            sh = dict(seg["shots"][k])
            sh["props"] = [q for q in sh["props"] if q[0] != "stext"]   # the teaser has its own headline on top
            return sh
    raise KeyError(line_start)


SEGMENTS = [
    {"line": "Your cat might think you're a cat. Just a bigger, clumsier one.", "head": "YOU'RE A BIG CAT?",
     "shots": [_shot("Basically, a large"), _shot("Just bigger", 1)]},
    {"line": "Adult cats hardly ever meow at each other.", "head": "NO MEOWS", "shots": [_shot("Adult cats hardly")]},
    {"line": "They save their meows for us.", "head": "MEOWS ARE FOR YOU", "shots": [_shot("So every meow")]},
    {"line": "A tail straight up is the same hello cats give their friends.", "head": "TAIL UP = HELLO",
     "shots": [_shot("When two friendly cats", 1), _shot("You just got the same hello")]},
    {"line": "And kneading your lap? That's what kittens do to their mom.", "head": "YOU = MOM?",
     "shots": [_shot("Kittens do this"), _shot("So when your cat kneads you")]},
    {"line": "Watch the full video on our channel to see what else your cat thinks of you!", "head": "FULL VIDEO ON OUR CHANNEL",
     "shots": ["thumbnail"]},
]

SCRIPT = {
    "hook": SEGMENTS[0]["line"],
    "body": " ".join(s["line"] for s in SEGMENTS[1:-1]),
    "cta": "Watch the full video on our channel and comment what your cat does!",
    "title": "Your Cat Thinks You're a Big Cat 😺 #shorts",
    "tags": ["cat psychology", "cat facts", "what cats think of humans", "cat behavior", "cats", "shorts"],
    "seo_description": (f"Full video: {LONG_URL}\n\nAdult cats rarely meow at each other, they greet friends with "
                        "their tail up, and kittens knead their mother. Here's what that says about how your cat "
                        "sees you. #cats #catfacts #shorts"),
    "ai_generated_visuals": False,
    "topic_category": "Animals",
}

_thumb = {}


def _scene(i, t, t_in, dur):
    shots = SEGMENTS[i]["shots"]
    n = len(shots)
    k = min(n - 1, int(t_in / (dur / n)))
    sh = shots[k]
    if sh == "thumbnail":
        if "img" not in _thumb:
            _thumb["img"] = Image.open(cat.THUMB).convert("RGBA").resize((1920, 1080), Image.LANCZOS)
        return _thumb["img"]
    sd = dur / n
    return cat.render_shot(sh, ("teaser", i, k), t, t_in - k * sd, sd)


def frame(t, i, t_in, starts):
    dur = (starts[i + 1] - starts[i]) if i + 1 < len(starts) else 3.5
    img = Image.new("RGBA", (W, H), (34, 40, 74, 255))
    scene = _scene(i, t, t_in, dur).resize((W, 608), Image.LANCZOS)
    img.alpha_composite(scene, (0, 620))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 616, W, 620], fill=GOLD)
    d.rectangle([0, 1228, W, 1232], fill=GOLD)
    pop = 0.85 + 0.15 * ms.ease(t_in / 0.2)
    head = SEGMENTS[i]["head"]
    size = int((150 if len(head) < 16 else 112) * pop)
    d.text((W / 2, 420), head, font=ImageFont.truetype(FONT_T, size), fill=GOLD, anchor="mm",
           stroke_width=8, stroke_fill=(0, 0, 0))
    ms.caption(d, 1300, SEGMENTS[i]["line"], size=50)
    d.rounded_rectangle([140, 1640, W - 140, 1750], 40, fill=(230, 40, 40))
    d.text((W / 2, 1695), "FULL VIDEO ON OUR CHANNEL", font=ImageFont.truetype(FONT_T, 70), fill=WHITE, anchor="mm")
    ms.watermark(d)
    return np.array(img.convert("RGB"))


def sound_events(starts, total):
    ev = [(0.0, sfx.impact(0.6)), (0.0, sfx.whoosh(0.3, 0.3))]
    ev += [(s - 0.05, sfx.whoosh(0.35, 0.3)) for s in starts[1:]]
    return ev


if __name__ == "__main__":
    ms.render_short(SCRIPT, SEGMENTS, VIDEO_ID, frame, speed=1.08, sfx_fn=sound_events, music_vol=0.07)
