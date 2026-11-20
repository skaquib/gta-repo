"""
run_strange_eggs_3d_short.py — "The 3 strangest eggs in nature", a stylized
3D countdown (render3d.py), 2026-10-31. Third video of the egg series.

Why this topic: the egg videos are the channel's two best (snake 2,399
views at 48h, chick 1,309 at 24h vs a ~1.2k lifetime ceiling before).
topic_validate.py 2026-10-31: "strangest animal eggs" has TWELVE Shorts over
1M in the last year (14.6M, 10.5M, 9.2M, 7.9M, 7.2M...) -- the most
repeatable demand found so far. Countdown format: "number one is creepy" in
the hook keeps viewers to the end; the CTA asks "3, 2 or 1?" (a choice gets
more comments than yes/no).

FACTS (checked 2026-10-31):
  #3 horn shark: spiral, screw-shaped egg case; the spiral helps it wedge
     into rock crevices (Science Friday "Picture of the week: horn shark egg
     case", The World/PRI, A-Z Animals). NOT claimed: that the mother screws
     it in herself (the expert source says she leaves right after laying).
  #2 kiwi: egg up to ~20% of the female's weight (Encyclopedia of Life;
     other sources 15-20%); 2-3 days before laying there's so little room
     for her stomach that she has to fast (EOL, Science Insights).
  #1 Surinam toad (Pipa pipa): eggs embed in the skin of the mother's back;
     the young develop there and emerge as fully formed toadlets after
     roughly 3-4 months (Univ. of the West Indies field guide, Wikipedia).
Stylized animation, not photorealistic -> no altered-content label.
"""
import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import config

config.assert_safe_pipeline()

import motion_shorts as ms
import render3d as r3
import sfx
from run_chick_egg_3d_short import (_ellipsoid, _cone, _transform, _ghost, _project, _pointer, _sm, _lerp,
                                    _S1V, _S1T, _S2V, _S2T, _S3V, _S3T)

VIDEO_ID = "strange_eggs_3d"
W, H = 1080, 1920
HERE = os.path.dirname(os.path.abspath(__file__))
FONT_T = os.path.join(HERE, "fonts", "BebasNeue-Regular.ttf")
GOLD, CYAN, RED, WHITE = (255, 206, 84), (56, 217, 255), (255, 84, 72), (255, 255, 255)

SEGMENTS = [
    {"line": "These are the three strangest eggs in nature. Number one is creepy.",
     "head": "3 STRANGEST EGGS", "sub": ""},
    {"line": "Number three: the horn shark's egg is a spiral, shaped like a screw.",
     "head": "#3 HORN SHARK", "sub": "SHAPED LIKE A SCREW"},
    {"line": "That spiral helps it wedge tight into cracks in the rocks.",
     "head": "#3 HORN SHARK", "sub": "WEDGED INTO ROCK"},
    {"line": "Number two: a kiwi's egg can weigh up to a fifth of her body.",
     "head": "#2 KIWI", "sub": "UP TO 1/5 OF HER WEIGHT"},
    {"line": "It squeezes her stomach so much, she stops eating before she lays it.",
     "head": "#2 KIWI", "sub": "NO ROOM TO EAT"},
    {"line": "Number one: the Surinam toad. Her eggs sink into the skin on her back.",
     "say": "Number one: the Soo-rih-nam toad. Her eggs sink into the skin on her back.",
     "head": "#1 SURINAM TOAD", "sub": "EGGS SINK INTO HER BACK"},
    {"line": "Months later, tiny toads pop out of her back!",
     "head": "#1 SURINAM TOAD", "sub": "BABIES POP OUT"},
    {"line": "Which egg is the strangest? Comment three, two, or one!",
     "head": "WHICH IS STRANGEST?", "sub": ""},
]

SCRIPT = {
    "hook": SEGMENTS[0]["line"],
    "body": " ".join(s["line"] for s in SEGMENTS[1:-1]),
    "cta": SEGMENTS[-1]["line"],
    "title": "The 3 Strangest Eggs in Nature 🥚 #shorts",
    "tags": ["strangest eggs", "weird animal eggs", "horn shark egg", "kiwi egg", "surinam toad", "animal facts",
             "3d animation", "top 3", "nature", "shorts"],
    "seo_description": (
        "#3 the horn shark's screw-shaped egg wedges into rock cracks. #2 a kiwi's egg can weigh up to a fifth "
        "of her body -- it squeezes her stomach so much she stops eating before laying it. #1 the Surinam toad's "
        "eggs sink into the skin on her back, and months later tiny toads pop out. Animated in 3D by FramedFacts. "
        "#animals #eggs #facts #3d #shorts"
    ),
    "ai_generated_visuals": False,
    "topic_category": "Animals",
}

SCENE = [0, 1, 1, 2, 2, 3, 3, 0]
LINEUP_X = 0.74                                    # spacing of the three eggs in the hook / CTA lineup                      # segment -> scene (0 lineup, 1 shark, 2 kiwi, 3 toad)
TINT = {0: (70, 58, 34), 1: (30, 70, 110), 2: (40, 90, 46), 3: (96, 74, 36)}


# ── #3 horn shark: spiral egg case ────────────────────────────────────────────
def _orient_out(V, T, axis_pts):
    p = V[T]
    n = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0])
    inward = (n * (p.mean(1) - axis_pts)).sum(1) < 0
    T = T.copy()
    T[inward] = T[inward][:, [0, 2, 1]]
    return T


def _spiral_case_local():
    ns, nt, turns, length = 110, 18, 3.3, 1.8
    s = np.linspace(0, 1, ns)                        # 0 = rounded base, 1 = pointed tip
    y = (s - 0.42) * length
    rb = 0.17 * (1 - s) ** 0.75 * np.clip(s * 9, 0.35, 1) + 0.012
    th = np.linspace(0, 2 * np.pi, nt, endpoint=False)
    V = np.stack([rb[:, None] * np.cos(th), np.repeat(y[:, None], nt, 1), rb[:, None] * np.sin(th)], -1).reshape(-1, 3)
    T = []
    for i in range(ns - 1):
        for j in range(nt):
            a, b, c, d = i * nt + j, i * nt + (j + 1) % nt, (i + 1) * nt + j, (i + 1) * nt + (j + 1) % nt
            T += [(a, c, d), (a, d, b)]
    T = np.array(T)
    T = _orient_out(V, T, np.stack([np.zeros(len(T)), V[T][:, :, 1].mean(1), np.zeros(len(T))], -1))
    body = dict(V=V, T=T, colors=np.tile([92, 66, 40], (len(T), 1)).astype(float), spec=0.35, shin=25)
    # two helical flanges, like the thread of a screw (double-sided ribbons)
    w = 0.17 * np.sin(np.pi * np.clip(s * 1.04, 0, 1)) ** 0.6
    ribbons = []
    for ph in (0.0, np.pi):
        ang = 2 * np.pi * turns * s + ph
        inner = np.stack([rb * np.cos(ang), y, rb * np.sin(ang)], -1)
        outer = np.stack([(rb + w) * np.cos(ang), y - 0.05 * w, (rb + w) * np.sin(ang)], -1)
        Vr = np.concatenate([inner, outer])
        Tr = []
        for i in range(ns - 1):
            a, b, c, d = i, i + 1, ns + i, ns + i + 1
            Tr += [(a, c, d), (a, d, b), (a, d, c), (a, b, d)]
        Tr = np.array(Tr)
        shade = np.where(np.arange(len(Tr)) % 4 < 2, 1.0, 0.82)[:, None]
        ribbons.append(dict(V=Vr, T=Tr, colors=np.array([70, 50, 30]) * shade, spec=0.3, shin=20))
    return [body] + ribbons


SPIRAL = _spiral_case_local()


def spiral_case(center, scale=1.0, spin=0.0, tilt=0.0, flip=False):
    Ry = r3.rot_matrix(0, spin, 0)
    Rz = r3.rot_matrix(0, 0, tilt + (np.pi if flip else 0))
    out = []
    for m in SPIRAL:
        m = dict(m)
        m["V"] = (m["V"] * scale) @ Ry.T @ Rz.T + center
        out.append(m)
    return out


def _rock(center, axes, rz, seed):
    rng = np.random.default_rng(seed)
    f = rng.normal(0, 1, (4, 3)) * 2.2
    ph = rng.uniform(0, 2 * np.pi, 4)
    bump = sum(np.sin(_S3V @ f[k] + ph[k]) for k in range(4)) / 4      # smooth, low-frequency bumps
    V = _S3V * (1 + 0.12 * bump)[:, None] * np.asarray(axes)
    V = V @ r3.rot_matrix(0, 0, rz).T + center
    col = np.array([112, 104, 96]) * (0.92 + 0.08 * rng.random((len(_S3T), 1)))
    return dict(V=V, T=_S3T, colors=col, spec=0.15, shin=10)


ROCKS = [_rock(np.array([-0.66, -0.55, 0]), (0.55, 0.9, 0.6), 0.30, 1),
         _rock(np.array([0.66, -0.55, 0]), (0.55, 0.9, 0.6), -0.30, 2)]


# ── #2 kiwi ───────────────────────────────────────────────────────────────────
def kiwi(squeeze=0.0):
    rng = np.random.default_rng(3)
    brown = np.array([124, 94, 62])
    body = _ellipsoid(np.zeros(3), (0.78, 0.62, 0.6), brown)
    body["colors"] = body["colors"] * (0.88 + 0.12 * rng.random((len(body["T"]), 1)))     # shaggy feathers
    head = _ellipsoid(np.array([0.70, 0.36, 0]), (0.22,) * 3, brown * 0.95, 0.2, 20, _S3V, _S3T)
    outside = [dict(body, layer=0), dict(head, layer=1),
               dict(_ellipsoid(np.array([0.80, 0.44, 0.17]), (0.03,) * 3, (10, 10, 12), 0.9, 80, _S1V, _S1T), layer=2),
               dict(_cone(np.array([0.88, 0.32, 0]), np.array([1.78, -0.12, 0]), 0.05, (214, 192, 150)), layer=2)]
    for z in (-0.16, 0.16):
        outside.append(dict(_cone(np.array([0.05, -0.45, z]), np.array([0.12, -1.06, z]), 0.075, (150, 128, 104)),
                            layer=-1))
        outside.append(dict(_ellipsoid(np.array([0.2, -1.08, z]), (0.2, 0.04, 0.08), (150, 128, 104), 0.2, 20,
                                       _S2V, _S2T), layer=-1))
    egg = _ellipsoid(np.array([-0.08, -0.10, 0]), (0.52, 0.36, 0.36), (246, 240, 228), 0.45, 50)
    sq = _lerp(1.0, 0.45, squeeze)
    stomach = _ellipsoid(np.array([0.36, 0.30 + 0.05 * squeeze, 0.05]), (0.17 * sq, 0.12 * (0.7 + 0.3 * sq), 0.12),
                         (206, 92, 104), 0.4, 40, _S3V, _S3T)
    return outside, egg, stomach


# ── #1 Surinam toad ───────────────────────────────────────────────────────────
TOAD_AX = (0.95, 0.16, 0.8)


def _back_y(x, z):
    return TOAD_AX[1] * math.sqrt(max(0.0, 1 - (x / TOAD_AX[0]) ** 2 - (z / TOAD_AX[2]) ** 2))


POCKETS = []
for _row in range(-3, 4):
    for _col in range(-4, 5):
        _x, _z = _col * 0.15 + (0.075 if _row % 2 else 0), _row * 0.14 - 0.05
        if (_x / 0.66) ** 2 + ((_z + 0.05) / 0.52) ** 2 < 1:
            POCKETS.append((_x, _z))
_prng = np.random.default_rng(9)
POCKET_DELAY = _prng.random(len(POCKETS))            # staggered sinking / hatching
POCKET_JUMP = _prng.random((len(POCKETS), 2)) * 2 - 1


def toad(sink=0.0, hatch=0.0):
    mud = np.array([120, 98, 72])
    rng = np.random.default_rng(4)
    body = _ellipsoid(np.zeros(3), TOAD_AX, mud)
    body["colors"] = body["colors"] * (0.9 + 0.1 * rng.random((len(body["T"]), 1)))
    m = [dict(body, layer=0),
         dict(_ellipsoid(np.array([0, 0.0, 0.80]), (0.40, 0.11, 0.38), mud * 0.97, 0.2, 20, _S3V, _S3T), layer=0)]
    for sx in (-1, 1):
        m.append(dict(_ellipsoid(np.array([0.16 * sx, 0.10, 0.98]), (0.028,) * 3, (12, 12, 12), 0.9, 80, _S1V, _S1T),
                      layer=1))
        m.append(dict(_ellipsoid(np.array([1.02 * sx, -0.04, -0.55]), (0.58, 0.07, 0.2), mud * 0.92, 0.2, 20,
                                 _S3V, _S3T, r3.rot_matrix(0, 0.6 * sx, 0)), layer=-1))
        m.append(dict(_ellipsoid(np.array([0.78 * sx, -0.04, 0.62]), (0.42, 0.05, 0.08), mud * 0.92, 0.2, 20,
                                 _S3V, _S3T, r3.rot_matrix(0, -0.8 * sx, 0)), layer=-1))
    for k, (x, z) in enumerate(POCKETS):
        y = _back_y(x, z)
        sk = _sm(0.0, 0.55, sink * 1.35 - POCKET_DELAY[k] * 0.35)          # 0 = egg on top, 1 = sunk in
        hk = float(np.clip((hatch - 0.55 * POCKET_DELAY[k]) / 0.42, 0, 1))  # this pocket's hatch progress
        if hatch > 0 and hk <= 0.08:
            sink, hatch_now = 1.0, False                                    # still sealed
        else:
            hatch_now = hatch > 0
        if not hatch_now and sink > 0:
            if sk < 1:      # amber egg sinking into the skin
                r = 0.062 * (1 - 0.75 * sk)
                m.append(dict(_ellipsoid(np.array([x, y + r * 0.7, z]), (r,) * 3, (236, 176, 70), 0.6, 60,
                                         _S2V, _S2T), layer=3))
            # skin closing over it: a raised, slightly lighter dome with a dark rim
            m.append(dict(_ellipsoid(np.array([x, y + 0.004, z]), (0.07 * (0.4 + 0.6 * sk), 0.012, 0.07 * (0.4 + 0.6 * sk)),
                                     (60, 44, 30), 0.2, 20, _S2V, _S2T), layer=1))
            if sk > 0.6:
                m.append(dict(_ellipsoid(np.array([x, y + 0.01, z]), (0.055, 0.02, 0.055), mud * 1.08, 0.3, 30,
                                         _S2V, _S2T), layer=2))
        else:
            m.append(dict(_ellipsoid(np.array([x, y + 0.004, z]), (0.07, 0.012, 0.07), (30, 20, 14), 0.1, 10,
                                     _S2V, _S2T), layer=1))                 # the open hole
            if hk < 1:
                rise = _sm(0.08, 0.4, hk)                                   # climbs out of the hole
                jump = _sm(0.62, 1.0, hk)                                   # then hops away
                jx, jz = POCKET_JUMP[k]
                pos = np.array([x + jx * 1.1 * jump, y + 0.045 * rise + 0.45 * math.sin(np.pi * jump),
                                z + 0.35 * jump + jz * 0.5 * jump])
                sc = 0.4 + 0.6 * rise
                m.append(dict(_ellipsoid(pos, (0.08 * sc, 0.04 * sc, 0.09 * sc), (158, 126, 88), 0.35, 30,
                                         _S2V, _S2T), layer=4))
                for sx in (-1, 1):
                    m.append(dict(_ellipsoid(pos + np.array([0.03 * sx, 0.032 * sc, 0.06 * sc]), (0.014 * sc,) * 3,
                                             (8, 8, 8), 0.9, 80, _S1V, _S1T), layer=5))
    return m


# ── frame ─────────────────────────────────────────────────────────────────────
_BGS = {}


def _background(scene):
    if scene not in _BGS:
        ys, xs = np.mgrid[0:H, 0:W]
        t = ys / H
        base = np.stack([12 + 12 * t, 14 + 10 * t, 22 + 16 * t], -1)
        dd = np.sqrt((xs - W / 2) ** 2 + ((ys - 1000) * 1.05) ** 2) / 950
        glow = np.clip(1 - dd, 0, 1) ** 2
        img = np.clip(base + glow[..., None] * np.array(TINT[scene]), 0, 255).astype(np.uint8)
        _BGS[scene] = Image.fromarray(img).convert("RGBA")
    return _BGS[scene]


def _pill(d, y, text, color, size=58):
    f = ImageFont.truetype(FONT_T, size)
    w = d.textlength(text, font=f)
    d.rounded_rectangle([W / 2 - w / 2 - 30, y - size * 0.62, W / 2 + w / 2 + 30, y + size * 0.62], 26,
                        fill=(0, 0, 0, 200), outline=color, width=4)
    d.text((W / 2, y), text, font=f, fill=color, anchor="mm")


def _label3(d, x, y, text, color, size=96):
    d.text((x, y), text, font=ImageFont.truetype(FONT_T, size), fill=color, anchor="mm",
           stroke_width=6, stroke_fill=(0, 0, 0))


def _lineup(img, t, cam_f, show_toad):
    """Hook / CTA: the three eggs side by side."""
    R = r3.rot_matrix(0.25, 0.0, 0.0)
    cam = r3.Camera(W / 2, 960, cam_f, 6.0)
    meshes = spiral_case(np.array([-LINEUP_X, 0.0, 0]), 0.72, spin=t * 1.2)
    egg = _ellipsoid(np.array([0.0, 0.0, 0]), (0.30, 0.42, 0.30), (246, 240, 228), 0.45, 50)
    meshes += [egg]
    img.alpha_composite(r3.render(_transform(meshes, R, np.zeros(3)), (W, H), cam))
    if show_toad:
        Rt = r3.rot_matrix(0.95, 0.5 * math.sin(t * 0.8), 0.0)
        lay = r3.render([dict(mm, V=mm["V"] * 0.27 + np.array([LINEUP_X, -0.05, 0])) for mm in
                         _transform(toad(sink=1.0), Rt, np.zeros(3))], (W, H), cam)
        img.alpha_composite(lay)
    return cam, R


def frame(t, i, t_in, starts):
    seg_dur = (starts[i + 1] - starts[i]) if i + 1 < len(starts) else 3.5
    frac = min(1.0, t_in / max(seg_dur, 0.1))
    scene = SCENE[i]
    img = _background(scene).copy()
    d = ImageDraw.Draw(img)
    pointers = []

    if i == 0:
        cam, R = _lineup(img, t, _lerp(2900, 3050, frac), show_toad=False)
        d = ImageDraw.Draw(img)
        _label3(d, W / 2 - LINEUP_X * cam.f / 6.0, 1300, "#3", WHITE)
        _label3(d, W / 2, 1300, "#2", WHITE)
        q = 0.85 + 0.15 * math.sin(t_in * 6)
        _label3(d, W / 2 + LINEUP_X * cam.f / 6.0, 960, "?", RED, int(300 * q))
        _label3(d, W / 2 + LINEUP_X * cam.f / 6.0, 1300, "#1", RED)
    elif i == 7:
        cam, R = _lineup(img, t, 2900, show_toad=True)
        d = ImageDraw.Draw(img)
        if t_in > 0.5:
            ap = ms.ease(min(1, (t_in - 0.5) / 0.25))
            for k, (lab, col) in enumerate((("3", (52, 152, 219)), ("2", (46, 204, 113)), ("1", RED))):
                cx = W / 2 + (k - 1) * LINEUP_X * cam.f / 6.0
                d.rounded_rectangle([cx - 110, 1290, cx + 110, 1430], 40, fill=col, outline=(0, 0, 0), width=6)
                d.text((cx, 1360), lab, font=ImageFont.truetype(FONT_T, int(110 * (0.6 + 0.4 * ap))), fill=WHITE,
                       anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0))
    elif scene == 1:
        cam = r3.Camera(W / 2, 1000, 2500 if i == 1 else 2200, 6.0)
        if i == 1:
            R = r3.rot_matrix(0.2, 0.0, 0.0)
            meshes = spiral_case(np.zeros(3), 1.0, spin=t_in * 1.6, tilt=0.15 * math.sin(t_in))
            img.alpha_composite(r3.render(_transform(meshes, R, np.zeros(3)), (W, H), cam))
            if frac > 0.35:
                pointers.append(((W / 2 + 0.2 * cam.f / 6.0, 1000 - 0.25 * cam.f / 6.0), "SPIRAL FLANGES", 1, -260))
        else:
            R = r3.rot_matrix(0.15, 0.25 * math.sin(t * 0.4), 0.0)
            p = ms.ease(min(1.0, frac / 0.85))
            egg = spiral_case(np.array([0, _lerp(1.6, 0.05, p), 0]), 0.8, spin=-p * 4 * np.pi, flip=True)
            meshes = [dict(m, layer=0) for m in ROCKS] + [dict(m, layer=1) for m in egg]
            img.alpha_composite(r3.render(_transform(meshes, R, np.array([0, 0.1, 0])), (W, H), cam))
    elif scene == 2:
        squeeze = _sm(0.15, 0.7, frac) if i == 4 else 0.0
        R = r3.rot_matrix(0.12, -0.35 + 0.25 * math.sin(t * 0.4), 0.0)
        cam = r3.Camera(W / 2, 1010, _lerp(2300, 2600, frac) if i == 3 else 2600, 6.0)
        focus = np.array([0.35, -0.1, 0])
        outside, egg, stomach = kiwi(squeeze)
        xr = _sm(0.0, 0.25, frac) if i == 3 else 1.0          # fade into the x-ray view
        img.alpha_composite(r3.render(_transform([egg, stomach], R, focus), (W, H), cam))
        lay = r3.render(_transform(outside, R, focus), (W, H), cam)
        _ghost(img, lay, _lerp(1.0, 0.35, xr), glow_a=0.9 * xr)
        d = ImageDraw.Draw(img)
        if i == 3 and frac > 0.3:
            pointers.append((_project(np.array([-0.2, -0.05, 0.36]), R, focus, cam), "EGG", -1, -200))
        if i == 4 and frac > 0.2:
            pointers.append((_project(np.array([0.36, 0.33, 0.17]), R, focus, cam), "STOMACH", 1, -230))
    else:
        R = r3.rot_matrix(0.95, 0.35 * math.sin(t * 0.35), 0.0)
        cam = r3.Camera(W / 2, 1000, _lerp(2100, 2600, ms.ease(frac)) if i == 5 else 2600, 6.0)
        mesh = toad(sink=frac if i == 5 else 1.0, hatch=0.0 if i == 5 else _sm(0.05, 0.95, frac))
        img.alpha_composite(r3.render(_transform(mesh, R, np.array([0, 0, -0.05])), (W, H), cam))

    d = ImageDraw.Draw(img)
    for tgt, lab, side, yo in pointers:
        _pointer(d, tgt, lab, side, y_off=yo)
    pop = 0.85 + 0.15 * ms.ease(t_in / 0.2)
    head = SEGMENTS[i]["head"]
    col = RED if head.startswith("#1") else GOLD
    d.text((W / 2, 220), head, font=ImageFont.truetype(FONT_T, int(124 * pop)), fill=col, anchor="mm",
           stroke_width=8, stroke_fill=(0, 0, 0))
    if SEGMENTS[i]["sub"]:
        _pill(d, 345, SEGMENTS[i]["sub"], WHITE)
    ms.caption(d, 1590, SEGMENTS[i]["line"], size=46)
    ms.watermark(d)
    return np.array(img.convert("RGB"))


def sound_events(starts, total):
    ev = [(0.0, sfx.impact(0.7)), (0.0, sfx.whoosh(0.3, 0.35)), (starts[1] - 0.9, sfx.riser(0.8, 0.3))]
    for k in (1, 3, 5):                                     # each countdown reveal
        ev += [(starts[k] - 0.05, sfx.whoosh(0.45, 0.45)), (starts[k] + 0.05, sfx.impact(0.55, low=False))]
    d2 = starts[3] - starts[2]
    for k in range(10):                                     # the screw turning into the rock
        ev.append((starts[2] + 0.1 + k * 0.85 * d2 / 10, sfx.tick(0.8 + 0.03 * k, 0.45)))
    ev += [(starts[2] + 0.85 * d2, sfx.impact(0.5))]
    ev += [(starts[4], sfx.whoosh(0.35, 0.3)), (starts[4] + 0.4, sfx.pop(0.35))]
    d6 = starts[7] - starts[6]
    for k, dl in enumerate(sorted(POCKET_DELAY)[::2]):     # toadlets popping out
        ev.append((starts[6] + (0.05 + 0.6 * dl) * d6, sfx.pop(0.32)))
    ev += [(starts[7], sfx.whoosh(0.4, 0.35)), (starts[7] + 0.5, sfx.pop(0.45))]
    return ev


if __name__ == "__main__":
    ms.render_short(SCRIPT, SEGMENTS, VIDEO_ID, frame, speed=1.1, sfx_fn=sound_events, music_vol=0.08)
