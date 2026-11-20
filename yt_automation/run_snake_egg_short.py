"""
run_snake_egg_short.py — "This egg is BIGGER than the snake's head" (animal
'what happens inside' format, 2026-10-24).

Why this topic: owner wants animal / most-watched curiosity topics, in the
style of the viral AI pigeon cutaway. Validated demand (topic_validate.py):
"This egg should NOT fit inside a snake" 38.2M (Aug 2026) -- the top animal
topic found. Our own version: own research, own script, own visuals.

FACTS (checked 2026-10-24, Wikipedia "Dasypeltis" + "Central African
egg-eating snake", Britannica "egg-eating snake", A-Z Animals):
  - Egg-eating snakes (Dasypeltis, Africa) swallow eggs much larger than
    their heads; extremely flexible, distensible jaws and neck.
  - Bony projections on the neck vertebrae (hypapophyses) jut into the
    throat; the egg is pressed against them and cracked from inside.
  - Contents are squeezed out and swallowed; the crushed shell is
    regurgitated.
  Dropped: jaw-ligament mechanics (unverified), "no teeth" (sources conflict).

FORMAT (the pigeon video's structure): the question/claim over the most
striking image on frame 1; each scene is the next step of the answer, shown
literally; voice on frame 1; whoosh on every cut, impact on the crack.
Realistic AI images -> altered-content label on upload.

Needs an image backend (image_gen.py): Gemini credits or a valid
BEDROCK_API_KEY in the environment. ~7 images, about $0.25-0.50.
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import config

config.assert_safe_pipeline()

import motion_shorts as ms
import image_gen
import sfx

VIDEO_ID = "snake_egg_inside"
W, H = 1080, 1920
HERE = os.path.dirname(os.path.abspath(__file__))
FONT_T = os.path.join(HERE, "fonts", "BebasNeue-Regular.ttf")
IMG_DIR = os.path.join(HERE, "output", "ai_images")

STYLE_PHOTO = "Photorealistic wildlife macro photography, dramatic natural light, shallow depth of field."
STYLE_CUT = ("Scientific 3D anatomical cutaway illustration, semi-transparent skin revealing the inside, "
             "hyper-detailed, cinematic lighting, dark background.")

SEGMENTS = [
    {"line": "This egg is bigger than the snake's head.", "head": "BIGGER THAN ITS HEAD",
     "prompt": f"An African egg-eating snake with brown patterned scales, its mouth stretched enormously wide "
               f"around a white bird egg far larger than its head, on a forest floor. {STYLE_PHOTO}"},
    {"line": "But it swallows it whole. Its jaws and neck stretch like rubber.", "head": "SWALLOWED WHOLE",
     "prompt": f"Side view of the same African egg-eating snake with the whole egg bulging inside its neck, "
               f"skin stretched thin, scales spread far apart. {STYLE_PHOTO}"},
    {"line": "Inside its neck, bony spikes from its spine poke into the throat.", "head": "SPINE SPIKES",
     "prompt": f"Inside a snake's neck: the spine with a row of sharp bony spikes pointing down into the "
               f"throat, a large egg sitting just below the spikes. {STYLE_CUT}"},
    {"line": "It squeezes the egg against them, and crack!", "head": "CRACK!",
     "prompt": f"Inside a snake's throat: bony spine spikes pressing into a white eggshell, the shell cracking "
               f"with sharp fracture lines, tiny shell fragments. {STYLE_CUT}"},
    {"line": "It swallows the yolk, then spits the crushed shell back out.", "head": "SHELL SPAT OUT",
     "prompt": f"An African egg-eating snake regurgitating a neatly folded, crushed white eggshell onto green "
               f"leaves, close-up. {STYLE_PHOTO}"},
    {"line": "Did you know a snake could do this? Comment yes or no!", "head": "DID YOU KNOW?",
     "prompt": f"An African egg-eating snake coiled beside a bird's nest full of eggs, looking at the camera. "
               f"{STYLE_PHOTO}"},
]

SCRIPT = {
    "hook": SEGMENTS[0]["line"],
    "body": " ".join(s["line"] for s in SEGMENTS[1:-1]),
    "cta": SEGMENTS[-1]["line"],
    "title": "This Egg Is BIGGER Than the Snake's Head 😳 #shorts",
    "tags": ["egg eating snake", "snake swallows egg", "snake facts", "animal facts", "what happens inside",
             "3d", "facts", "nature", "wildlife", "shorts"],
    "seo_description": (
        "African egg-eating snakes swallow eggs much bigger than their heads. Bony spikes from their "
        "spine poke into the throat and crack the egg from the inside -- then the snake spits the crushed "
        "shell back out. #animals #snake #facts #shorts"
    ),
    "ai_generated_visuals": True,
}

_IMGS = {}


def _img(i):
    if i not in _IMGS:
        im = Image.open(os.path.join(IMG_DIR, f"{VIDEO_ID}_{i}.png")).convert("RGB")
        scale = max(W / im.width, H / im.height) * 1.12   # headroom for the zoom
        _IMGS[i] = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
    return _IMGS[i]


def _kenburns(i, p):
    im = _img(i)
    z = 1.0 + 0.10 * p if i % 2 == 0 else 1.10 - 0.10 * p          # alternate push-in / pull-out
    cw, ch = int(W * 1.12 / z), int(H * 1.12 / z)
    cx = im.width / 2 + (30 if i % 3 == 0 else -30) * (p - 0.5)
    cy = im.height / 2 + (-20 if i % 3 == 1 else 20) * (p - 0.5)
    box = (int(cx - cw / 2), int(cy - ch / 2), int(cx + cw / 2), int(cy + ch / 2))
    return im.crop(box).resize((W, H), Image.BILINEAR)


def frame(t, i, t_in, starts):
    seg_dur = (starts[i + 1] - starts[i]) if i + 1 < len(starts) else 3.5
    p = min(1.0, t_in / max(seg_dur, 0.1))
    base = _kenburns(i, p)
    if i > 0 and t_in < 0.18:                      # quick crossfade from the previous scene
        prev = _kenburns(i - 1, 1.0)
        base = Image.blend(prev, base, t_in / 0.18)
    img = base.convert("RGBA")
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)
    for y in range(0, 420, 6):                       # top and bottom vignettes for legibility
        a = int(170 * (1 - y / 420))
        sd.rectangle([0, y, W, y + 6], fill=(0, 0, 0, a))
        sd.rectangle([0, H - y - 6, W, H - y], fill=(0, 0, 0, a))
    img.alpha_composite(shade)
    d = ImageDraw.Draw(img)
    pop = 0.85 + 0.15 * ms.ease(t_in / 0.2)
    if i == 3 and t_in > 0.9:                        # the crack lands: bigger, hotter headline
        pop *= 1.15
    d.text((W / 2, 230), SEGMENTS[i]["head"], font=ImageFont.truetype(FONT_T, int(124 * pop)),
           fill=(255, 214, 80) if i in (0, 3) else (255, 255, 255), anchor="mm",
           stroke_width=7, stroke_fill=(0, 0, 0))
    ms.caption(d, 1430, SEGMENTS[i]["line"], size=46)
    ms.watermark(d)
    return np.array(img.convert("RGB"))


def sound_events(starts, total):
    ev = [(0.0, sfx.impact(0.7, low=True)), (0.0, sfx.whoosh(0.3, 0.35))]
    for k in range(1, len(starts)):
        ev.append((starts[k] - 0.08, sfx.whoosh(0.35, 0.45)))
    crack = starts[3] + 0.9
    ev += [(crack, sfx.impact(0.95, low=False)), (crack, sfx.tick(0.6, 0.6)), (crack + 0.05, sfx.tick(0.5, 0.5))]
    ev += [(starts[5] + 0.2, sfx.pop(0.45))]
    return ev


def build():
    for i, seg in enumerate(SEGMENTS):
        image_gen.generate(seg["prompt"], os.path.join(IMG_DIR, f"{VIDEO_ID}_{i}.png"))
    return ms.render_short(SCRIPT, SEGMENTS, VIDEO_ID, frame, speed=1.1, sfx_fn=sound_events, music_vol=0.08)


if __name__ == "__main__":
    build()
