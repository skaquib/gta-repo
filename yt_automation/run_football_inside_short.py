"""
run_football_inside_short.py — "What's inside a football?" in real 3D
(first video of the 3D-facts channel, 2026-10-24).

RESEARCH: CONTENT_BANK.md / topic_validate.py -- "How a football is made"
has the largest on-topic demand found (top Short 147.5M, 11 versions over
1M); "How giant football bladders are made" 15.1M. Those winners reuse the
same factory footage; this version is original: every visual is rendered in
3D by render3d.py.

FACTS (checked 2026-10-24, 2+ sources each):
  - Classic hand-stitched balls have 32 panels (sialkotfootball.com,
    sportsmonkie.com); the 32-panel design is a truncated icosahedron:
    12 pentagons + 20 hexagons (geometry).
  - 2-4 lining layers of polyester and/or cotton bonded under the cover
    (sportsmonkie.com, sialkotfootball.com).
  - Bladder of latex or butyl rubber holds the air (same sources).
  - Sialkot, Pakistan is widely cited as making most of the world's
    footballs (APP, Dunya News, Khaleej Times; percentages vary 70-85%, so
    no number is stated).
  - 2026 World Cup ball Trionda: 4 panels, sensor inside, made in Sialkot
    (Laughing Squid, Dunya News, weekend.at, Khaleej Times).
  Dropped: stitch counts (unverified).

HOOK: voice on frame 1 over a fast-spinning 3D ball; it bursts into its 32
panels at ~0.9s (impact). Every shot shows exactly what the voice says.
Visuals are code-rendered 3D animation (not photorealistic AI), so no
altered-content label is needed.
"""
import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import config

config.assert_safe_pipeline()

import motion_shorts as ms
import render3d as r3
import sfx

VIDEO_ID = "football_inside_3d"
W, H = 1080, 1920
REGION_Y = 360                  # top of the 1080x1080 3D viewport
BALL_CY = REGION_Y + 540
HERE = os.path.dirname(os.path.abspath(__file__))
FONT_T = os.path.join(HERE, "fonts", "BebasNeue-Regular.ttf")
FONT_B = os.path.join(HERE, "fonts", "Montserrat[wght].ttf")
CYAN = (56, 217, 255)
GOLD = (255, 206, 84)

SEGMENTS = [
    {"line": "What's inside a football?", "head": "WHAT'S INSIDE", "head2": "A FOOTBALL?"},
    {"line": "A classic ball has 32 panels. 12 pentagons. 20 hexagons.", "head": "32 PANELS"},
    {"line": "Under them, layers of polyester and cotton keep its shape.", "head": "THE LINING",
     "sub": "2-4 LAYERS · POLYESTER + COTTON"},
    {"line": "At the core, a rubber bladder holds the air.", "head": "THE BLADDER",
     "sub": "LATEX OR BUTYL RUBBER"},
    {"line": "Most of the world's footballs come from one city: Sialkot, Pakistan.",
     "say": "Most of the world's footballs come from one city: See-aal-kote, Pakistan.",
     "head": "SIALKOT, PAKISTAN", "sub": "WHERE MOST FOOTBALLS ARE MADE"},
    {"line": "And the 2026 World Cup ball? Just 4 panels, with a sensor inside.",
     "head": "2026 WORLD CUP BALL", "sub": "4 PANELS · SENSOR INSIDE"},
    {"line": "How many panels does your ball have? Comment below!", "head": "COUNT YOUR",
     "head2": "BALL'S PANELS"},
]

SCRIPT = {
    "hook": SEGMENTS[0]["line"],
    "body": " ".join(s["line"] for s in SEGMENTS[1:-1]),
    "cta": SEGMENTS[-1]["line"],
    "title": "What's Inside a Football? (3D) ⚽ #shorts",
    "tags": ["what's inside a football", "football", "soccer ball", "how footballs are made",
             "3d animation", "sialkot", "world cup ball", "trionda", "facts", "3d facts", "shorts"],
    "seo_description": (
        "A classic football has 32 panels -- 12 pentagons and 20 hexagons -- over 2-4 layers of "
        "polyester and cotton lining and a latex or butyl rubber bladder. Most of the world's "
        "footballs come from Sialkot, Pakistan, and the 2026 World Cup ball has just 4 panels "
        "with a sensor inside. Rendered in 3D by FramedFacts. #football #3d #facts #shorts"
    ),
    "ai_generated_visuals": False,   # code-rendered 3D animation, not photorealistic AI
}

# ── geometry (built once) ────────────────────────────────────────────────────
PANELS = r3.football_panels()
for _p in PANELS:
    _p["Nloc"] = r3._unit(_p["V"][_p["T"]].mean(1))
_TETRA = r3._unit(np.array([(1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1)], dtype=float))
_FOUR = [(242, 242, 246), (226, 92, 92), (84, 180, 110), (80, 130, 220)]
for _p in PANELS:
    region = np.argmax(_p["Nloc"] @ _TETRA.T, axis=1)
    _p["four"] = np.array(_FOUR, dtype=float)[region]

_SV, _ST = r3.icosphere(3)
_cen = _SV[_ST].mean(1)
_lat = np.arcsin(np.clip(r3._unit(_cen)[:, 1], -1, 1))
_lon = np.arctan2(_cen[:, 2], _cen[:, 0])
_weave = 0.9 + 0.1 * np.sign(np.sin(_lat * 18) * np.sin(_lon * 18))
LINING_COL = np.array([214, 190, 150], dtype=float)[None, :] * _weave[:, None]
# split the lining into two hemispheres (own vertices) so it can open up
_left = _cen[:, 0] < 0
LINING_HALVES = []
for mask, sign in ((_left, -1), (~_left, 1)):
    Vh = (_SV[_ST[mask]] * 0.9).reshape(-1, 3)
    Th = np.arange(len(Vh)).reshape(-1, 3)
    LINING_HALVES.append((Vh, Th, LINING_COL[mask], sign))
BLADDER_V, BLADDER_T = _SV * 0.76, _ST
BLADDER_COL = np.tile([158, 52, 44], (len(_ST), 1)).astype(float)
_VV, _VT = r3.icosphere(1)
VALVE_V, VALVE_T = _VV * 0.06 + np.array([0, 0.77, 0]), _VT
VALVE_COL = np.tile([40, 40, 44], (len(_VT), 1)).astype(float)

CAM = r3.Camera(540, 540, 1330, 4.6)
I3 = np.eye(3)


def _font(path, size, weight=None):
    f = ImageFont.truetype(path, size)
    if weight:
        try:
            f.set_variation_by_axes([weight])
        except Exception:
            pass
    return f


def _background():
    ys, xs = np.mgrid[0:H, 0:W]
    t = ys / H
    base = np.stack([8 + 10 * t, 12 + 8 * t, 30 + 26 * t], -1)
    d = np.sqrt((xs - W / 2) ** 2 + ((ys - BALL_CY) * 1.2) ** 2) / 820
    glow = np.clip(1 - d, 0, 1) ** 2
    img = Image.fromarray(np.clip(base + glow[..., None] * np.array([25, 60, 160]), 0, 255).astype(np.uint8))
    img = img.convert("RGBA")
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g = ImageDraw.Draw(layer)
    horizon, vx = 1215, W / 2
    for k in range(-12, 13):
        g.line([(vx + k * 18, horizon), (vx + k * 260, H)], fill=CYAN + (38,), width=2)
    y, step = horizon + 10, 14
    while y < H:
        g.line([(0, y), (W, y)], fill=CYAN + (30,), width=2)
        step *= 1.32
        y += step
    img.alpha_composite(layer)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([W / 2 - 250, 1205, W / 2 + 250, 1265], fill=(0, 0, 0, 150))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)))
    return img


_BG = _background()


def _rotation(t):
    ay = 0.55 * t + 3.4 * (1 - math.exp(-2.4 * t))
    return r3.rot_matrix(0.32 + 0.06 * math.sin(0.8 * t), ay, 0.08)


def _ball_meshes(R, ex, tint=None, four=False):
    meshes = []
    if ex > 2.4:
        return meshes
    for k, p in enumerate(PANELS):
        if four:
            colors = p["four"]
        else:
            base = np.array((34, 34, 40) if p["kind"] == "pent" else (236, 236, 240), dtype=float)
            if tint and p["kind"] == tint[0]:
                base = base * (1 - tint[1]) + np.array(CYAN) * tint[1]
            colors = np.where(p["seam"][:, None], base * 0.42, base)
        Rk = r3.axis_rotation(p["center"], ex * 0.9 * (1 if k % 2 else -1)) if ex > 0 else I3
        V = (p["V"] @ Rk.T + p["center"] * ex) @ R.T
        N = (p["Nloc"] @ Rk.T) @ R.T
        meshes.append(dict(V=V, T=p["T"], colors=colors, N=N, spec=0.35, shin=40))
    return meshes


def _inner_meshes(R, split, lining_scale=1.0, bladder=True):
    meshes = []
    for Vh, Th, col, sign in LINING_HALVES:
        V = (Vh * lining_scale + np.array([sign * split, 0, 0])) @ R.T
        meshes.append(dict(V=V, T=Th, colors=col, spec=0.08, shin=10))
    if bladder:
        meshes.append(dict(V=BLADDER_V @ R.T, T=BLADDER_T, colors=BLADDER_COL, spec=0.6, shin=60))
        meshes.append(dict(V=VALVE_V @ R.T, T=VALVE_T, colors=VALVE_COL, spec=0.4, shin=30))
    return meshes


def _chip(img, cx, cy, t):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    pulse = 0.75 + 0.25 * math.sin(t * 7)
    d.ellipse([cx - 170, cy - 170, cx + 170, cy + 170], fill=CYAN + (int(110 * pulse),))
    glow = layer.filter(ImageFilter.GaussianBlur(40))
    img.alpha_composite(glow)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([cx - 70, cy - 46, cx + 70, cy + 46], radius=14, fill=(18, 24, 40, 255),
                        outline=CYAN + (255,), width=5)
    for k in range(-2, 3):
        d.line([(cx + k * 24, cy - 46), (cx + k * 24, cy - 66)], fill=GOLD + (255,), width=5)
        d.line([(cx + k * 24, cy + 46), (cx + k * 24, cy + 66)], fill=GOLD + (255,), width=5)
    d.text((cx, cy), "SENSOR", font=_font(FONT_B, 26, 800), fill=CYAN + (255,), anchor="mm")


def _text_layer(d, seg, t_in, frac, i):
    pop = 0.86 + 0.14 * ms.ease(t_in / 0.22)
    big = _font(FONT_T, int(132 * pop))
    col = GOLD if i in (4, 5) else (CYAN if i == 6 else (255, 255, 255))
    d.text((W / 2, 190), seg["head"], font=big, fill=col, anchor="mm", stroke_width=6, stroke_fill=(0, 0, 0))
    if seg.get("head2"):
        d.text((W / 2, 318), seg["head2"], font=big, fill=CYAN if i == 0 else GOLD, anchor="mm",
               stroke_width=6, stroke_fill=(0, 0, 0))
    elif seg.get("sub"):
        d.text((W / 2, 300), seg["sub"], font=_font(FONT_B, 40, 700), fill=(225, 232, 250), anchor="mm",
               stroke_width=3, stroke_fill=(0, 0, 0))
    if i == 1:   # counters, timed to the spoken numbers
        if frac > 0.42:
            a = ms.ease((frac - 0.42) / 0.08)
            _counter(d, 300, 1335, "12", "PENTAGONS", (34, 34, 40), a, pent=True)
        if frac > 0.72:
            a = ms.ease((frac - 0.72) / 0.08)
            _counter(d, 780, 1335, "20", "HEXAGONS", (236, 236, 240), a, pent=False)


def _counter(d, cx, cy, num, label, fill, a, pent):
    r = 42 * a
    pts = [(cx - 150 + r * math.cos(math.radians(90 + k * (72 if pent else 60))),
            cy - r * math.sin(math.radians(90 + k * (72 if pent else 60)))) for k in range(5 if pent else 6)]
    if a > 0.05:
        d.polygon(pts, fill=fill + (255,), outline=CYAN + (255,))
    d.text((cx - 90, cy), num, font=_font(FONT_T, int(96 * (0.7 + 0.3 * a))), fill=(255, 255, 255),
           anchor="lm", stroke_width=5, stroke_fill=(0, 0, 0))
    d.text((cx - 90, cy + 62), label, font=_font(FONT_B, 30, 800), fill=CYAN, anchor="lm",
           stroke_width=3, stroke_fill=(0, 0, 0))


def frame(t, i, t_in, starts):
    seg_dur = (starts[i + 1] - starts[i]) if i + 1 < len(starts) else 3.0
    frac = t_in / max(seg_dur, 0.1)
    R = _rotation(t)
    ex, split, inner, four, xray, tint = 0.0, 0.0, False, False, False, None

    if i == 0:
        ex = 0.42 * ms.ease((t_in - 0.85) / 0.5) if t_in > 0.85 else 0.0
    elif i == 1:
        ex = 0.42 + 0.02 * math.sin(2 * t)
        if 0.42 <= frac < 0.72:
            tint = ("pent", 0.55)
        elif frac >= 0.72:
            tint = ("hex", 0.35)
    elif i == 2:
        ex = 0.42 + 2.2 * ms.ease(t_in / 0.75)
        inner = True
    elif i == 3:
        ex, inner, split = 3.0, True, 0.62 * ms.ease(t_in / 0.6)
    elif i == 4:
        ex = 2.6 * (1 - ms.ease(t_in / 0.9))
        inner, split = True, 0.62 * (1 - ms.ease(t_in / 0.7))
    elif i == 5:
        four = xray = True
    meshes = _ball_meshes(R, ex, tint=tint, four=four)
    if inner:
        scale = 0.88 + 0.12 * ms.ease(t_in / 0.3) if i == 2 else 1.0
        meshes = _inner_meshes(R, split, scale) + meshes

    img = _BG.copy()
    ball = r3.render(meshes, (1080, 1080), CAM)
    if xray:
        _chip(img, W / 2, BALL_CY, t)
        a = np.array(ball)
        a[..., 3] = (a[..., 3] * 0.52).astype(np.uint8)
        ball = Image.fromarray(a)
    img.alpha_composite(ball, (0, REGION_Y))

    d = ImageDraw.Draw(img)
    _text_layer(d, SEGMENTS[i], t_in, frac, i)
    ms.caption(d, 1470, SEGMENTS[i]["line"], size=44)
    ms.watermark(d)
    return np.array(img.convert("RGB"))


def sound_events(starts, total):
    ev = [(0.0, sfx.whoosh(0.3, 0.4))]
    burst = starts[0] + 0.85
    ev += [(burst, sfx.impact(0.95)), (burst, sfx.whoosh(0.5, 0.55))]
    d1 = starts[2] - starts[1]
    ev += [(starts[1] + 0.42 * d1, sfx.pop(0.5)), (starts[1] + 0.72 * d1, sfx.pop(0.5))]
    ev += [(starts[2], sfx.whoosh(0.55, 0.55)), (starts[2] + 0.15, sfx.pop(0.35))]
    ev += [(starts[3], sfx.impact(0.6, low=False)), (starts[3] + 0.1, sfx.whoosh(0.4, 0.4))]
    ev += [(max(0, starts[4] - 0.7), sfx.riser(0.7, 0.45)), (starts[4] + 0.85, sfx.impact(0.85))]
    ev += [(starts[5], sfx.riser(0.5, 0.3)), (starts[5] + 0.5, sfx.pop(0.55))]
    ev += [(starts[6], sfx.impact(0.55, low=False)), (starts[6] + 0.2, sfx.pop(0.4))]
    return ev


if __name__ == "__main__":
    ms.render_short(SCRIPT, SEGMENTS, VIDEO_ID, frame, speed=1.12, sfx_fn=sound_events, music_vol=0.08)
