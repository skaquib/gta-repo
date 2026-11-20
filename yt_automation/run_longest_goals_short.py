"""
run_longest_goals_short.py — "Football's longest goals, drawn on a real-size
pitch" (2026-10-23). Visual-first countdown built with motion_shorts.

Proof of demand: "The Longest Ever Goal in Football by Every Type" 2.9M views
from a 14K-sub channel (output/research/visual_format_shorts.json).

Facts (checked 2026-10-23):
  - penalty spot 11 m; halfway line ~52.5 m on a 105 m pitch (IFAB-standard
    international pitch 105 x 68 m)
  - longest headed goal: Jone Samuelsen 58.13 m, Odd v Tromsø, 25 Sep 2011
    (Guinness; re-measured from 57.3 m)
  - Asmir Begović 91.9 m, Stoke v Southampton, 2 Nov 2013 (previous record)
  - Tom King 96.01 m, Newport County v Cheltenham, 19 Jan 2021 (Guinness
    record), from his own six-yard box, wind-assisted
Sources: guinnessworldrecords.com, newport-county.co.uk, espn.com,
sowetanlive.co.za.
"""
import math
import numpy as np
from PIL import Image, ImageDraw

import config

config.assert_safe_pipeline()

import motion_shorts as ms

VIDEO_ID = "longest_goals_short"
W, H = ms.W, ms.H

# Top-down pitch, attacking goal at the top. 105 x 68 m.
PITCH_TOP, PITCH_BOTTOM = 470, 1880
S = (PITCH_BOTTOM - PITCH_TOP) / 105.0          # px per metre
PITCH_W = 68 * S
PX0 = (W - PITCH_W) / 2


def pt(x_m, d_m):
    """x_m: metres from the left touchline; d_m: metres from the top goal line."""
    return PX0 + x_m * S, PITCH_TOP + d_m * S


GOAL_C = pt(34, 0)

SEGMENTS = [
    {"line": "Football's longest goals, drawn on a real-size pitch. How far is the record?",
     "head": "LONGEST GOALS EVER", "sub": "DRAWN TO SCALE", "shot": None},
    {"line": "A penalty. Eleven metres.", "head": "PENALTY", "sub": "11 m",
     "shot": (34, 11), "col": (255, 255, 255)},
    {"line": "From the halfway line. About fifty-two metres.", "head": "HALFWAY LINE", "sub": "≈ 52.5 m",
     "shot": (22, 52.5), "col": (120, 210, 255)},
    {"line": "The longest headed goal ever. Fifty-eight metres. A header from his own half.",
     "head": "LONGEST HEADER", "sub": "58.13 m · Samuelsen, 2011", "shot": (48, 58.13),
     "col": (255, 200, 60)},
    {"line": "Goalkeeper Asmir Begović. Ninety-one point nine metres.", "head": "BEGOVIĆ",
     "sub": "91.9 m · 2013", "shot": (20, 91.9), "col": (190, 130, 255)},
    {"line": "But the world record. Tom King, ninety-six metres. From his own box.",
     "head": "WORLD RECORD", "sub": "96.01 m · Tom King, 2021", "shot": (38, 96.01),
     "col": (255, 90, 90)},
    {"line": "Could you score from your own half? Comment yes or no.", "head": "COULD YOU",
     "sub": "SCORE FROM YOUR OWN HALF?", "shot": None},
]

SCRIPT = {
    "hook": SEGMENTS[0]["line"],
    "body": " ".join(s["line"] for s in SEGMENTS[1:-1]),
    "cta": SEGMENTS[-1]["line"],
    "title": "Football's Longest Goals, Drawn on a REAL-SIZE Pitch ⚽📏 #shorts",
    "tags": ["longest goal", "tom king", "begovic", "longest header", "football records",
             "guinness world record", "football facts", "soccer facts", "to scale", "shorts"],
    "seo_description": (
        "Football's longest goals drawn on a real 105 m pitch: penalty (11 m), halfway line "
        "(~52.5 m), Jone Samuelsen's 58.13 m header (2011), Asmir Begović's 91.9 m (2013) and "
        "Tom King's 96.01 m Guinness World Record (2021). #football #soccer #shorts"
    ),
}


def _pitch_bg():
    img = Image.new("RGB", (W, H), (8, 14, 28))
    d = ImageDraw.Draw(img)
    stripe = 105 / 12
    for k in range(12):
        y0 = PITCH_TOP + k * stripe * S
        d.rectangle([PX0, y0, PX0 + PITCH_W, y0 + stripe * S],
                    fill=(22, 96, 46) if k % 2 else (18, 84, 40))
    lc, lw = (235, 245, 235), 4
    d.rectangle([PX0, PITCH_TOP, PX0 + PITCH_W, PITCH_BOTTOM], outline=lc, width=lw)
    mid = PITCH_TOP + 52.5 * S
    d.line([(PX0, mid), (PX0 + PITCH_W, mid)], fill=lc, width=lw)
    cx = W / 2
    r = 9.15 * S
    d.ellipse([cx - r, mid - r, cx + r, mid + r], outline=lc, width=lw)
    for top in (True, False):
        gl = PITCH_TOP if top else PITCH_BOTTOM
        sgn = 1 if top else -1
        # penalty area 40.32 x 16.5, goal area 18.32 x 5.5, spot 11 m
        for w_m, d_m in ((40.32, 16.5), (18.32, 5.5)):
            x0, x1 = cx - w_m / 2 * S, cx + w_m / 2 * S
            y1 = gl + sgn * d_m * S
            d.line([(x0, gl), (x0, y1), (x1, y1), (x1, gl)], fill=lc, width=lw)
        sy = gl + sgn * 11 * S
        d.ellipse([cx - 4, sy - 4, cx + 4, sy + 4], fill=lc)
    # the goal we shoot at (7.32 m), drawn just above the top line
    gw = 7.32 * S
    d.rectangle([cx - gw / 2, PITCH_TOP - 14, cx + gw / 2, PITCH_TOP], outline=(255, 255, 255), width=5)
    return img


_BG = _pitch_bg()


def _ball_path(x_m, d_m, p):
    """Point along a curved flight from the shot spot to the goal mouth."""
    (x0, y0), (x1, y1) = pt(x_m, d_m), GOAL_C
    bend = (x0 - x1) * 0.25 + 60
    cx_, cy_ = (x0 + x1) / 2 + bend, (y0 + y1) / 2
    q = 1 - p
    return q * q * x0 + 2 * q * p * cx_ + p * p * x1, q * q * y0 + 2 * q * p * cy_ + p * p * y1


def frame(t, i, t_in, starts):
    img = _BG.copy().convert("RGBA")
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    for k, seg in enumerate(SEGMENTS[: i + 1]):
        if not seg["shot"]:
            continue
        x_m, d_m = seg["shot"]
        current = k == i
        p = ms.ease(t_in / 1.1) if current else 1.0
        col = seg["col"] + ((255,) if current else (120,))
        # dotted trail
        n = int(34 * p)
        for j in range(n):
            bx, by = _ball_path(x_m, d_m, j / 34)
            d.ellipse([bx - 6, by - 6, bx + 6, by + 6], fill=col)
        sx, sy = pt(x_m, d_m)
        d.ellipse([sx - 15, sy - 15, sx + 15, sy + 15], fill=col, outline=(0, 0, 0, 255), width=2)
        if current:
            bx, by = _ball_path(x_m, d_m, p)
            d.ellipse([bx - 13, by - 13, bx + 13, by + 13], fill=(255, 255, 255, 255),
                      outline=(0, 0, 0, 255), width=3)
            # distance bracket on the left touchline
            gy, ty = PITCH_TOP, sy
            lx = PX0 - 26
            d.line([(lx, gy), (lx, ty)], fill=col, width=6)
            d.line([(lx - 10, ty), (lx + 10, ty)], fill=col, width=6)
            d.line([(lx - 10, gy), (lx + 10, gy)], fill=col, width=6)
        else:
            d.text((sx + 18, sy - 20), seg["sub"].split(" ·")[0], font=ms.font(40),
                   fill=col, stroke_width=3, stroke_fill=(0, 0, 0))

    seg = SEGMENTS[i]
    pop = 0.85 + 0.15 * ms.ease(t_in / 0.25)
    hs = int(104 * pop)
    col = seg.get("col", (255, 230, 80))
    ms.centered(d, 70, seg["head"], hs, fill=col)
    ms.centered(d, 70 + hs + 14, seg["sub"], 60)
    ms.caption(d, 70 + hs + 100, seg["line"], size=40)
    if i == 0:
        q = int(200 + 16 * math.sin(t * 6))
        ms.centered(d, 1300, "?", q, fill=(255, 230, 80))
    ms.watermark(d)

    img.alpha_composite(layer)
    return np.array(img.convert("RGB"))


if __name__ == "__main__":
    ms.render_short(SCRIPT, SEGMENTS, VIDEO_ID, frame)
