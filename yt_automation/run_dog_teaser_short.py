"""
run_dog_teaser_short.py — vertical teaser Short for the second long video
("Your Dog Doesn't See You as Its Boss. It Sees You as Its Parent", G6bFaS7npX4).

Same build as run_cat_teaser_short.py: the long video's own cartoon scenes in a
9:16 frame, a big headline on top, captions, and a "full video" banner. The link
goes in the description and first comment. The owner sets the Short's Related
video in YouTube Studio (the API can't), which is the only tappable link from the
Shorts feed to the long video.
"""

import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import config

config.assert_safe_pipeline()

import motion_shorts as ms
import sfx
import run_dog_thinks_long as dog

VIDEO_ID = "dog_teaser_short"
LONG_URL = "https://www.youtube.com/watch?v=G6bFaS7npX4"
W, H = 1080, 1920
HERE = os.path.dirname(os.path.abspath(__file__))
FONT_T = os.path.join(HERE, "fonts", "BebasNeue-Regular.ttf")
GOLD, WHITE = (255, 214, 70), (255, 255, 255)


def _shot(line_start, k=0):
    for seg in dog.SEGMENTS:
        if seg["line"].startswith(line_start):
            sh = dict(seg["shots"][k])
            sh["props"] = [q for q in sh["props"] if q[0] != "stext"]   # the teaser has its own headline on top
            return sh
    raise KeyError(line_start)


SEGMENTS = [
    {"line": "Your dog doesn't see you as its boss.", "head": "NOT THE BOSS",
     "shots": [_shot("For years, people said"), _shot("So your dog isn't secretly")]},
    {"line": "The whole alpha idea came from wolves in captivity. In the wild, a wolf pack is just a family.",
     "head": "ALPHA = MYTH", "shots": [_shot("That idea came from"), _shot("A wild wolf pack")]},
    {"line": "When you and your dog lock eyes, a bonding hormone can rise in both of you.", "head": "THE LOVE LOOP",
     "shots": [_shot("When dogs and their owners gazed"), _shot("A little loop")]},
    {"line": "Dogs even have a special muscle for puppy eyes. Wolves barely have it.", "head": "PUPPY EYES",
     "shots": [_shot("Dogs have a small muscle"), _shot("Wolves barely")]},
    {"line": "Say good boy in a bored voice, and their brain's reward area barely reacts. Your dog wants you to mean it.",
     "head": "MEAN IT!", "shots": [_shot("Good boy, in a bored"), _shot("Your dog wants you")]},
    {"line": "So what are you to your dog? Watch the full video on our channel!", "head": "FULL VIDEO ON OUR CHANNEL",
     "shots": ["thumbnail"]},
]

SCRIPT = {
    "hook": SEGMENTS[0]["line"],
    "body": " ".join(s["line"] for s in SEGMENTS[1:-1]),
    "cta": "Does your dog give you puppy eyes?",
    "title": "Your Dog Doesn't See You as the Boss 🐶 #shorts",
    "category_id": "15",
    "tags": ["dog psychology", "dog behavior", "alpha dog myth", "puppy dog eyes", "what do dogs think of humans",
             "dog facts", "dogs", "shorts"],
    "seo_description": (f"Full video: {LONG_URL}\n\nThe alpha-dog idea came from captive wolves; wild packs are families. "
                        "Dogs and owners share a gaze 'love loop', dogs have a muscle for puppy eyes that wolves barely "
                        "have, and praise only rewards your dog when you sound like you mean it. #dogs #dogfacts #shorts"),
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
            _thumb["img"] = Image.open(dog.THUMB).convert("RGBA").resize((1920, 1080), Image.LANCZOS)
        return _thumb["img"]
    sd = dur / n
    return dog.render_shot(sh, ("teaser", i, k), t, t_in - k * sd, sd)


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
