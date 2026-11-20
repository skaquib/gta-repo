"""
run_chick_egg_3d_short.py — "How a chick grows inside an egg, day 1 to 21",
a stylized 3D x-ray animation (render3d.py), 2026-10-30.

Why this topic: the snake/egg 3D Short (l5eE6dnMfag) beat every earlier
video (1,834 views, 20 likes, 5 viewer comments in 24h vs a ~1.2k ceiling).
topic_validate.py (2026-10-30): "How a chick grows inside the egg" is the
most repeatable animal topic found -- top Short 14.7M, SEVEN versions over
1M in the last year. Same format: x-ray 3D, a day counter as the retention
hook (viewers wait for the hatch), a payoff crack, a yes/no question.

FACTS (checked 2026-10-30, 2+ sources each):
  - heart starts beating within ~2 days (~42-44 h): Mississippi State
    extension "Stages of chick embryo development", Utah AITC/Illinois deck
  - blood vessels spread over the yolk by day 3: Cobb embryo chart, MSU
  - beak starts to harden ~day 10; wings and legs formed well before:
    The Poultry Site "Embryonic development day by day", Illinois extension
  - yolk sac drawn into the body on days 19-20: Penn State 4-H embryology,
    Cobb chart, Illinois "Embryonic development days 1-21"
  - day 20: beak pokes into the air cell, first breath (internal pipping);
    day 21: egg tooth breaks the shell: Penn State, Illinois
  - the absorbed yolk feeds the chick for its first day or two (hatcheries
    say 48-72 h; welfare sources warn problems can start ~48 h -> we say
    "a day or two", which every source supports)
Stylized animation, not photorealistic -> no altered-content label.
"""
import os
import math
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

import config

config.assert_safe_pipeline()

import motion_shorts as ms
import render3d as r3
import sfx

VIDEO_ID = "chick_egg_3d"
W, H = 1080, 1920
HERE = os.path.dirname(os.path.abspath(__file__))
FONT_T = os.path.join(HERE, "fonts", "BebasNeue-Regular.ttf")
GOLD, CYAN, RED, WHITE = (255, 206, 84), (56, 217, 255), (255, 84, 72), (255, 255, 255)

SEGMENTS = [
    {"line": "There's a chick folded up inside this egg.", "head": "THERE'S A CHICK INSIDE"},
    {"line": "Day one, it's just a tiny dot.", "head": "A TINY DOT"},
    {"line": "Day two, a tiny heart starts beating.", "head": "HEARTBEAT"},
    {"line": "Blood vessels spread over the yolk to feed it.", "head": "BLOOD VESSELS"},
    {"line": "Day ten, it has wings, legs, and a beak.", "head": "WINGS, LEGS, BEAK"},
    {"line": "Day nineteen, it starts pulling the yolk into its belly.", "head": "YOLK INTO BELLY"},
    {"line": "Day twenty, it pokes into the air pocket and takes its first breath.", "head": "FIRST BREATH"},
    {"line": "Day twenty-one, it cracks the shell with an egg tooth on its beak!", "head": "HATCH!"},
    {"line": "That yolk feeds it for its first day or two. Did you know? Comment yes or no!",
     "head": "DID YOU KNOW?"},
]

SCRIPT = {
    "hook": SEGMENTS[0]["line"],
    "body": " ".join(s["line"] for s in SEGMENTS[1:-1]),
    "cta": SEGMENTS[-1]["line"],
    # live trend scan 2026-10-30: the winners use short "How/Why..." titles with one emoji
    # (Zack D. Films 6.5M in 48h); the pipeline's compliance check still requires #shorts.
    "title": "How a Chick Grows Inside an Egg 🐣 #shorts",
    "tags": ["chick inside egg", "how a chick grows", "egg hatching", "chick embryo", "day by day",
             "21 days", "3d animation", "animal facts", "what happens inside", "shorts"],
    "seo_description": (
        "Day 1 it's a dot. Day 2 a heart beats. Blood vessels spread over the yolk, the beak forms, and on "
        "days 19-20 the chick pulls the whole yolk into its belly -- then breathes the air pocket and cracks "
        "the shell with its egg tooth on day 21. Animated in 3D by FramedFacts. Facts from university poultry "
        "extension guides (Mississippi State, Penn State, Illinois). #animals #chick #egg #3d #shorts"
    ),
    "ai_generated_visuals": False,
    "topic_category": "Animals",
}

# ── per-segment day timeline (the counter IS the retention hook) ──────────────
DAY_RANGE = [(20, 20), (1.0, 1.9), (2.0, 2.9), (3.0, 5.0), (6.0, 10.0), (14.0, 19.7), (20.0, 20.9),
             (21, 21), (21, 21)]
REWIND_AT = 0.80          # hook: last 20% rewinds day 20 -> 1
CRACK_AT = 0.34           # seg 7: the voice says "cracks" at 21.83s = 34% in (measured on the voice render)
CAP_OFF = 0.70            # seg 7: the top of the shell comes off


def _sm(e0, e1, x):
    x = np.clip((x - e0) / (e1 - e0), 0, 1)
    return x * x * (3 - 2 * x)


def _lerp(a, b, p):
    return a + (b - a) * p


def _unit(v):
    return np.asarray(v, dtype=float) / np.linalg.norm(v)


# ── egg shell: blunt end up, split into a zig-zag cap for the hatch ──────────
EGG_R, EGG_H = 0.78, 1.0
_EV, _ET = r3.icosphere(4)


def _egg_shape(v):
    k = 1 + 0.09 * v[..., 1:2]
    return v * np.array([EGG_R, EGG_H, EGG_R]) * np.concatenate([k, np.ones_like(k), k], -1)


EGG_V = _egg_shape(_EV)
_EGG_N = r3._unit(_EV / np.array([EGG_R, EGG_H, EGG_R]))[_ET].mean(1)
_c = _EV[_ET].mean(1)
_theta = np.arctan2(_c[:, 2], _c[:, 0])
_tri_wave = 2 * np.abs((_theta * 7 / (2 * np.pi)) % 1 - 0.5) - 0.5          # -0.5..0.5
CUT_Y = 0.40 + 0.09 * _tri_wave
CAP = _c[:, 1] * EGG_H > CUT_Y
SHELL_COL = np.tile([246, 238, 222], (len(_ET), 1)).astype(float)   # even colour: per-triangle speckle showed facets


def _shell(part="all", inner=False):
    sel = np.ones(len(_ET), bool) if part == "all" else (CAP if part == "cap" else ~CAP)
    T = _ET[sel]
    m = dict(V=EGG_V, T=T[:, [0, 2, 1]] if inner else T, colors=SHELL_COL[sel] * (0.8 if inner else 1.0),
             N=-_EGG_N[sel] if inner else _EGG_N[sel], spec=0.35, shin=30, facet=0.08)
    return m


# ── yolk, blood vessels, air cell ─────────────────────────────────────────────
_SV, _ST = r3.icosphere(4)
_S3V, _S3T = r3.icosphere(3)
_S2V, _S2T = r3.icosphere(2)
_S1V, _S1T = r3.icosphere(1)
D0 = _unit([0.0, 0.70, 0.71])          # where the embryo sits on the yolk (top, toward camera)


def _ellipsoid(center, axes, color, spec=0.3, shin=30, verts=_SV, tris=_ST, Rm=None):
    V = verts * np.asarray(axes)
    N = r3._unit(verts / np.asarray(axes))
    if Rm is not None:
        V, N = V @ Rm.T, N @ Rm.T
    return dict(V=V + center, T=tris, colors=np.tile(color, (len(tris), 1)).astype(float),
                N=r3._unit(N[tris].mean(1)), spec=spec, shin=shin, facet=0.08)


def _cone(base, tip, rad, color, n=12):
    a = r3._unit(tip - base)
    u = r3._unit(np.cross(a, [0.0, 0.0, 1.0]) if abs(a[2]) < 0.95 else np.cross(a, [1.0, 0, 0]))
    w = np.cross(a, u)
    ring = np.array([base + rad * (math.cos(t) * u + math.sin(t) * w)
                     for t in np.linspace(0, 2 * np.pi, n, endpoint=False)])
    V = np.vstack([ring, tip[None], base[None]])
    tris = np.array([(i, (i + 1) % n, n) for i in range(n)] + [(n + 1, (i + 1) % n, i) for i in range(n)])
    p = V[tris]
    nrm = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0])
    inward = (nrm * (p.mean(1) - (base + tip) / 2)).sum(1) < 0
    tris[inward] = tris[inward][:, [0, 2, 1]]
    return dict(V=V, T=tris, colors=np.tile(color, (len(tris), 1)).astype(float), spec=0.4, shin=40)


def _make_vessels():
    """Branching vessel paths on the unit sphere, growing out from D0.
    Each: (array of unit directions, level, birth 0..1)."""
    rng = np.random.default_rng(4)
    out = []
    u = _unit(np.cross(D0, [1.0, 0, 0]))
    v = np.cross(D0, u)

    def grow(p, t, length, level, birth):
        pts = [p]
        steps = int(8 * length / 1.2) + 3
        for k in range(steps):
            ang = rng.normal(0, 0.25)
            n = np.cross(p, t)
            t = _unit(t * math.cos(ang) + n * math.sin(ang))
            p = _unit(p + t * length / steps)
            t = _unit(t - p * (t @ p))
            pts.append(p)
            if level < 2 and k in (steps // 3, 2 * steps // 3) and rng.random() < 0.85:
                side = 1 if rng.random() < 0.5 else -1
                nt = _unit(t * 0.5 + side * np.cross(p, t))
                grow(p, nt, length * 0.55, level + 1, birth + 0.5 * (k / steps) * (1 - birth))
        out.append((np.array(pts), level, birth))

    for k in range(7):
        a = 2 * np.pi * k / 7 + rng.normal(0, 0.2)
        t = _unit(u * math.cos(a) + v * math.sin(a))
        grow(_unit(D0 + 0.06 * t), t, 1.25, 0, 0.0)
    return out


VESSELS = _make_vessels()


def yolk_state(day):
    g = _sm(4, 18, day)
    absorb = _sm(18.9, 19.7, day)
    c = _lerp(np.array([0.0, -0.10, 0.0]), np.array([0.06, -0.42, -0.05]), g)
    r = _lerp(0.47, 0.33, g)
    belly = embryo_center(day) + np.array([-0.08, -0.14, 0.12])
    return _lerp(c, belly, absorb), _lerp(r, 0.13, absorb), absorb


def embryo_center(day, lift=0.0):
    attach = np.array([0.0, -0.10, 0.0]) + 0.48 * D0
    return _lerp(attach, np.array([0.0, 0.10, 0.08]), _sm(3.5, 14, day)) + np.array([0, 0.10 * lift, 0])


def growth(day):
    return float(np.clip((day - 2) / 17, 0, 1)) ** 0.85


PARTS = {}   # where the beak / wing / leg / heart were last drawn (for the on-screen labels)


def embryo_meshes(day, t, beak_up=0.0, breath=0.0):
    """The embryo as a curled chain of spheres whose profile morphs from a
    big-headed C-shaped embryo into a round, downy chick."""
    PARTS.clear()
    g = growth(day)
    ctr = embryo_center(day, beak_up)
    S = _lerp(0.13, 1.0, g)
    us = np.linspace(0, 1, 12)
    r_early = np.interp(us, [0, 0.14, 0.3, 0.6, 1], [0.30, 0.19, 0.17, 0.12, 0.035])
    r_late = np.interp(us, [0, 0.16, 0.36, 0.6, 0.84, 1], [0.25, 0.21, 0.40, 0.43, 0.38, 0.30])
    r = _lerp(r_early, r_late, _sm(0.15, 0.85, g)) * S * (1 + 0.04 * breath)
    span = _lerp(1.6 * np.pi, 1.72 * np.pi, g)
    Rc = 0.30 * S
    ang = np.pi / 2 - 0.35 + span * us
    P = ctr + Rc * np.stack([np.cos(ang), np.sin(ang), np.zeros_like(ang)], -1)
    skin = _lerp(np.array([232, 140, 132]), np.array([238, 186, 160]), _sm(0.1, 0.35, g))
    col = _lerp(skin, np.array([246, 206, 92]), _sm(0.42, 0.68, g))
    # painted tail -> head (layers), parts on top: no jagged seams between the spheres
    meshes = [dict(_ellipsoid(P[k], (r[k],) * 3, col, 0.25, 25, _S3V, _S3T), layer=len(us) - k)
              for k in range(len(us))]
    head, hr = P[0], r[0]
    # beak: points away from the body early, straight up (to the air cell) late
    out_dir = _unit(P[0] - ctr)
    bdir = _unit(_lerp(out_dir, np.array([0.15, 1.0, 0.25]), max(_sm(0.5, 0.9, g), beak_up)))
    if g > 0.18:
        k = _sm(0.18, 0.4, g)
        base = head + bdir * hr * 0.8
        beak_col = _lerp(np.array([236, 186, 110]), np.array([238, 160, 50]), _sm(0.45, 0.8, g))
        meshes.append(dict(_cone(base, base + bdir * (0.28 * S * k + 0.08 * beak_up), 0.085 * S * k, beak_col),
                           layer=40))
        PARTS["beak"] = base + bdir * 0.16 * S * k
    # eye: huge and dark early, on the side facing the camera
    if day >= 2.6:
        er = hr * _lerp(0.5, 0.26, g) * _sm(2.6, 3.4, day)
        epos = head + hr * 0.78 * _unit(np.array([0, 0, 1.0]) + 0.35 * bdir)
        meshes.append(dict(_ellipsoid(epos, (er,) * 3, (18, 16, 20), 0.9, 80, _S2V, _S2T), layer=41))
    # wing and leg buds
    if g > 0.14:
        k = _sm(0.14, 0.4, g)
        tang = _unit(P[5] - P[3])
        Rm = np.stack([tang, np.cross([0, 0, 1.0], tang), [0, 0, 1.0]], 1)
        wing = P[4] + np.array([0, 0, r[4] * 0.85])
        meshes.append(dict(_ellipsoid(wing, (0.24 * S * k, 0.11 * S * k, 0.06 * S), col * 0.84, 0.2, 20, _S3V, _S3T,
                                      Rm), layer=35))
        legc = _lerp(col, np.array([236, 150, 80]), 0.45 + 0.55 * _sm(0.5, 0.8, g))
        leg = P[8] + np.array([0, 0, r[8] * 0.8])
        meshes.append(dict(_ellipsoid(leg, (0.20 * S * k, 0.06 * S * k, 0.06 * S), legc, 0.2, 20, _S3V, _S3T, Rm),
                           layer=35))
        PARTS.update(wing=wing + np.array([0, 0, 0.06 * S]), leg=leg + np.array([0, 0, 0.06 * S]))
    # the early heart bulges out of the chest: pulses ~2.2x a second
    if 1.9 < day < 9:
        beat = max(0.0, math.sin(2 * np.pi * 2.2 * t)) ** 3
        hrad = 0.14 * S * (1 + 0.35 * beat) * _sm(1.9, 2.2, day) * (1 - _sm(7, 9, day))
        hpos = _lerp(P[2], ctr, 0.8) + np.array([0, 0, 0.02])     # bulging out on the open side of the C
        meshes.append(dict(_ellipsoid(hpos, (hrad,) * 3, (214, 28, 40), 0.6, 60, _S2V, _S2T), layer=42))
        PARTS["heart"] = hpos + np.array([0, 0, hrad])
    return meshes


LATE_G = 0.55             # from here (about day 12) the embryo is drawn as a curled chick


def chick_curled(day, beak_up=0.0, breath=0.0):
    """Late embryo (day ~12-20): a downy chick curled up, head tucked at the
    front. Returned as layers composited back to front -- separate layers
    keep the painter's renderer from drawing jagged seams where parts meet."""
    g = growth(day)
    ctr = embryo_center(day, beak_up)
    S = _lerp(0.78, 1.0, _sm(LATE_G, 1.0, g)) * (1 + 0.035 * breath)
    yel = np.array([246, 206, 92])
    rot = lambda a: r3.rot_matrix(0, 0, a)
    body = [_ellipsoid(ctr + S * np.array([-0.04, -0.10, 0.0]), S * np.array([0.50, 0.48, 0.40]), yel, 0.2, 20)]
    limbs = [_ellipsoid(ctr + S * np.array([0.10, -0.40, 0.28]), S * np.array([0.20, 0.06, 0.06]), (240, 170, 70),
                        0.3, 30, _S3V, _S3T, rot(-0.35)),
             _ellipsoid(ctr + S * np.array([-0.14, -0.04, 0.33]), S * np.array([0.27, 0.16, 0.07]), yel * 0.92,
                        0.2, 20, _S3V, _S3T, rot(0.45))]
    hc, hr = ctr + S * np.array([0.20, 0.28, 0.24]), 0.22 * S
    bdir = _unit(_lerp(np.array([0.75, 0.45, 0.45]), np.array([0.15, 1.0, 0.25]), beak_up))
    base = hc + bdir * hr * 0.85
    head = [_ellipsoid(hc, (hr,) * 3, yel, 0.2, 20, _S3V, _S3T),
            _ellipsoid(hc + hr * 0.82 * _unit([-0.15, 0.25, 0.95]), (0.045 * S,) * 3, (14, 12, 16), 0.9, 80, _S1V, _S1T),
            _cone(base, base + bdir * (0.13 * S + 0.08 * beak_up), 0.06 * S, (238, 160, 50))]
    for m in body:
        m["layer"] = 0
    for m in limbs:
        m["layer"] = 1
    head[0]["layer"] = 2
    head[1]["layer"] = head[2]["layer"] = 3
    return [body + limbs + head]


def chick_standing(pos, t, bob=0.0):
    """Hatched chick, facing the camera."""
    y = np.array([0, 0.03 * math.sin(t * 5) * bob, 0])
    yel = np.array([250, 212, 76])
    # detailed spheres + draw layers (body 1, wings 2, head 3, face 4) between the
    # shell's inner wall (0) and its front (5), so the shell still hides the lower body
    m = [dict(_ellipsoid(pos + y + [0, 0, 0], (0.34, 0.31, 0.30), yel, 0.2, 20, _SV, _ST), layer=1),
         dict(_ellipsoid(pos + y + [0, 0.40, 0.04], (0.23,) * 3, yel, 0.2, 20, _SV, _ST), layer=3)]
    for sx in (-1, 1):
        m.append(dict(_ellipsoid(pos + y + [0.085 * sx, 0.45, 0.22], (0.035,) * 3, (12, 12, 14), 0.9, 80, _S2V, _S2T),
                      layer=4))
        m.append(dict(_ellipsoid(pos + y + [0.33 * sx, 0.04, 0.02], (0.08, 0.18, 0.14), yel * 0.92, 0.2, 20, _S3V,
                                 _S3T), layer=2))
    m.append(dict(_cone(pos + y + np.array([0, 0.37, 0.21]), pos + y + np.array([0, 0.34, 0.36]), 0.06,
                        (244, 150, 40), n=20), layer=4))
    return m


# ── compositing helpers ───────────────────────────────────────────────────────
def _transform(meshes, R, focus):
    out = []
    for m in meshes:
        m = dict(m)
        m["V"] = (m["V"] - focus) @ R.T
        if "N" in m:
            m["N"] = m["N"] @ R.T
        out.append(m)
    return out


def _ghost(img, layer, alpha, glow=CYAN, glow_a=0.9):
    mask = layer.getchannel("A")
    a = np.array(layer)
    a[..., 3] = (a[..., 3] * alpha).astype(np.uint8)
    img.alpha_composite(Image.fromarray(a))
    if glow_a > 0:
        edge = ImageChops.subtract(mask.filter(ImageFilter.MaxFilter(7)), mask).filter(ImageFilter.GaussianBlur(1.5))
        g = Image.new("RGBA", (W, H), glow + (0,))
        g.putalpha(edge.point(lambda v: min(255, int(v * glow_a))))
        img.alpha_composite(g)


def _project(p, R, focus, cam):
    c = (np.asarray(p, dtype=float) - focus) @ R.T
    z = cam.D - c[..., 2]
    return cam.cx + cam.f * c[..., 0] / z, cam.cy - cam.f * c[..., 1] / z


def _draw_vessels(d, R, focus, cam, yc, yr, grow, fade):
    if grow <= 0 or fade <= 0:
        return
    for pts, level, birth in VESSELS:
        vis = np.clip((grow - birth) / 0.45, 0, 1)
        if vis <= 0:
            continue
        n = max(2, int(len(pts) * vis))
        dirs = pts[:n]
        facing = (dirs @ R.T)[:, 2]
        x, y = _project(yc + yr * 1.006 * dirs, R, focus, cam)
        w = int(max(2, (7 - 2.5 * level) * cam.f / 3000))
        col = (190, 24, 30, int(235 * fade))
        for k in range(n - 1):
            if facing[k] > 0.05 and facing[k + 1] > 0.05:
                d.line([(x[k], y[k]), (x[k + 1], y[k + 1])], fill=col, width=w)


def _pointer(d, target, label, side, y_off=-120):
    tx, ty = target
    lx = 130 if side < 0 else W - 130
    ly = ty + y_off
    d.line([(lx, ly), (tx, ty)], fill=(0, 0, 0), width=9)
    d.line([(lx, ly), (tx, ty)], fill=CYAN, width=4)
    d.ellipse([tx - 11, ty - 11, tx + 11, ty + 11], fill=CYAN, outline=(0, 0, 0), width=3)
    d.text((lx, ly - 8), label, font=ImageFont.truetype(FONT_T, 62), fill=CYAN, anchor="mb",
           stroke_width=5, stroke_fill=(0, 0, 0))


def _timeline(d, day):
    x0, x1, y = 120, W - 120, 330
    d.rounded_rectangle([x0 - 6, y - 16, x1 + 6, y + 16], 16, fill=(0, 0, 0, 170))
    fill = x0 + (x1 - x0) * np.clip(day / 21, 0, 1)
    if fill > x0 + 4:
        d.rounded_rectangle([x0, y - 10, fill, y + 10], 10, fill=GOLD)
    for k in range(1, 21):
        xx = x0 + (x1 - x0) * k / 21
        d.line([(xx, y - 10), (xx, y + 10)], fill=(0, 0, 0, 120), width=2)


_BG = None


def _background():
    ys, xs = np.mgrid[0:H, 0:W]
    t = ys / H
    base = np.stack([12 + 12 * t, 14 + 10 * t, 24 + 16 * t], -1)
    dd = np.sqrt((xs - W / 2) ** 2 + ((ys - 1000) * 1.05) ** 2) / 950
    glow = np.clip(1 - dd, 0, 1) ** 2
    img = np.clip(base + glow[..., None] * np.array([70, 58, 34]), 0, 255).astype(np.uint8)
    return Image.fromarray(img).convert("RGBA")


# ── scene timeline ────────────────────────────────────────────────────────────
def state(i, t_in, frac):
    d0, d1 = DAY_RANGE[i]
    if i == 4:                       # "Day ten..." -- count 5 -> 10 fast, then hold
        day = _lerp(5, 10, ms.ease(min(1, frac / 0.3)))
    elif i == 5:                     # "Day nineteen..." -- count 10 -> 19 fast, then the yolk goes in
        day = _lerp(10, 19, ms.ease(min(1, frac / 0.25))) + 0.7 * _sm(0.3, 0.95, frac)
    else:
        day = _lerp(d0, d1, ms.ease(frac))
    st = dict(day=day, focus=np.zeros(3), f=3000.0, shell_a=0.22, vessels=0.0,
              labels=(), hatch=None, beak_up=0.0, breath=0.0, aircell=0.45)
    attach = embryo_center(1.0)
    if i == 0:
        rw = _sm(REWIND_AT, 1.0, frac)
        st.update(day=_lerp(20, 1, rw), f=_lerp(_lerp(2900, 3150, ms.ease(min(1, frac / REWIND_AT))), 9000, rw),
                  focus=_lerp(np.array([0, 0.02, 0]), attach, rw), vessels=1 - rw)
    elif i in (1, 2):
        st.update(focus=attach + [0, 0.02, 0], f=_lerp(9000, 8200, frac) if i == 1 else _lerp(8200, 7400, frac))
        st["vessels"] = 0.12 * frac if i == 2 else 0.0
        st["labels"] = (("HEART", "heart"),) if i == 2 and frac > 0.3 else ()
    elif i == 3:
        p = ms.ease(min(1, frac * 1.3))
        st.update(focus=_lerp(attach, np.array([0, -0.05, 0]), p), f=_lerp(7400, 3300, p), vessels=_lerp(0.15, 1, frac))
        st["labels"] = (("VESSELS", "vessel"),) if frac > 0.35 else ()
    elif i == 4:
        st.update(focus=_lerp(np.array([0, -0.05, 0]), np.zeros(3), frac), f=_lerp(3300, 3000, frac), vessels=1.0)
        st["labels"] = (("BEAK", "beak"), ("WING", "wing"), ("LEG", "leg")) if frac > 0.32 else ()
    elif i == 5:
        st.update(vessels=1.0, labels=(("YOLK", "yolk"),) if frac > 0.25 else ())
    elif i == 6:
        p = ms.ease(min(1, frac * 1.6))
        st.update(focus=_lerp(np.zeros(3), np.array([0, 0.30, 0]), p), f=_lerp(3000, 3500, p), beak_up=p,
                  breath=max(0.0, math.sin(2 * np.pi * 1.3 * t_in)) * _sm(0.45, 0.6, frac), aircell=0.45 + 0.3 * p,
                  labels=(("AIR POCKET", "air"),) if frac > 0.2 else ())
    elif i == 7:
        st.update(focus=np.array([0, 0.12, 0]), f=3000, beak_up=1.0, shell_a=_lerp(0.22, 1.0, _sm(0.0, 0.22, frac)),
                  hatch=frac)
    else:
        st.update(focus=np.array([0, 0.12, 0]), f=3000, hatch=1.6, labels=(("YOLK INSIDE", "belly"),) if frac > 0.1 else ())
    return st


def frame(t, i, t_in, starts):
    global _BG
    if _BG is None:
        _BG = _background()
    seg_dur = (starts[i + 1] - starts[i]) if i + 1 < len(starts) else 4.0
    frac = min(1.0, t_in / max(seg_dur, 0.1))
    st = state(i, t_in, frac)
    day = st["day"]
    R = r3.rot_matrix(0.16, 0.30 * math.sin(0.35 * t), 0.0)
    cam = r3.Camera(W / 2, 1000, st["f"], 6.0)
    focus = st["focus"]
    img = _BG.copy()

    hatch = st["hatch"]
    opened = hatch is not None and hatch >= CAP_OFF
    if not opened:
        yc, yr, absorb = yolk_state(day)
        if st["shell_a"] < 0.98:
            img.alpha_composite(r3.render(_transform([_ellipsoid(yc, (yr,) * 3, (250, 178, 38), 0.5, 40)], R, focus),
                                          (W, H), cam))
            d = ImageDraw.Draw(img)
            _draw_vessels(d, R, focus, cam, yc, yr, st["vessels"], 1 - absorb)
            if growth(day) >= LATE_G:
                layers = chick_curled(day, st["beak_up"], st["breath"])
            else:
                layers = [embryo_meshes(day, t, st["beak_up"], st["breath"])]
            if day < 2.0:     # day 1: the blastoderm, a pale dot on the yolk
                k = _sm(1.0, 1.3, day) * (1 - _sm(1.85, 2.0, day))
                Rm = np.stack([np.cross(D0, [1.0, 0, 0]), np.cross(D0, np.cross(D0, [1.0, 0, 0])), D0], 1)
                layers = [[_ellipsoid(yc + yr * D0, (0.07 * k + 1e-3, 0.07 * k + 1e-3, 0.012), (252, 246, 232),
                                      0.3, 20, _S2V, _S2T, Rm)]]
            for layer in layers:
                img.alpha_composite(r3.render(_transform(layer, R, focus), (W, H), cam))
            if 0 < absorb < 1 or (i == 5 and absorb > 0):   # yolk moving into the belly: draw it over the chick
                lay = r3.render(_transform([_ellipsoid(yc, (yr,) * 3, (250, 178, 38), 0.5, 40)], R, focus), (W, H), cam)
                _ghost(img, lay, 0.8, glow=(255, 230, 120), glow_a=0.8)
            air = _ellipsoid(np.array([0, 0.84, 0]), (0.50, 0.13, 0.50), (190, 228, 250), 0.6, 40)
            _ghost(img, r3.render(_transform([air], R, focus), (W, H), cam), st["aircell"], glow_a=0)
        # the shell: see-through x-ray, solid for the hatch
        lay = r3.render(_transform([_shell()], R, focus), (W, H), cam)
        _ghost(img, lay, st["shell_a"], glow_a=0.9 * (1 - st["shell_a"]) + 0.15)
    else:
        rise = ms.ease(min(1.0, (hatch - CAP_OFF) / 0.22))
        cap_p = ms.ease(min(1.0, (hatch - CAP_OFF) / 0.3))
        chick = chick_standing(np.array([0, _lerp(-0.25, 0.30, rise), 0]), t, bob=1.0 if hatch > 1 else 0.0)
        meshes = [dict(_shell("bottom", inner=True), layer=0), dict(_shell("bottom"), layer=5)] + chick
        img.alpha_composite(r3.render(_transform(meshes, R, focus), (W, H), cam))
        if cap_p < 1:
            Rc = r3.rot_matrix(0, 0, -1.1 * cap_p)
            cap = _shell("cap")
            cap["V"] = (cap["V"] - [0, 0.6, 0]) @ Rc.T + [0.9 * cap_p, 0.6 + 1.3 * cap_p, 0]
            cap["N"] = cap["N"] @ Rc.T
            lay = r3.render(_transform([cap, dict(_shell("cap", inner=True), V=cap["V"])], R, focus), (W, H), cam)
            a = np.array(lay)
            a[..., 3] = (a[..., 3] * (1 - cap_p ** 3)).astype(np.uint8)
            img.alpha_composite(Image.fromarray(a))

    d = ImageDraw.Draw(img)
    # hatch: the chick pecks a crack around the shell, then the cap pops off
    if hatch is not None and CRACK_AT <= hatch < CAP_OFF + 0.05:
        p = min(1.0, (hatch - CRACK_AT) / (CAP_OFF - CRACK_AT - 0.04))
        th = np.linspace(-np.pi / 2 - np.pi * 0.62 * p, -np.pi / 2 + np.pi * 0.62 * p, 80)
        tw = 2 * np.abs((th * 7 / (2 * np.pi)) % 1 - 0.5) - 0.5
        yy = (0.40 + 0.09 * tw) / EGG_H
        dirs = np.stack([np.cos(th) * np.sqrt(1 - yy ** 2), yy, -np.sin(th) * np.sqrt(1 - yy ** 2)], -1)
        pts = _egg_shape(dirs) * 1.01
        x, y = _project(pts, R, focus, cam)
        d.line(list(zip(x, y)), fill=(40, 30, 22), width=7, joint="curve")
        # a hole where the egg tooth broke through
        hx, hy = _project(_egg_shape(np.array([0.0, 0.40, 1.0]) / np.linalg.norm([0, 0.40, 1.0])), R, focus, cam)
        hr = 22 * _sm(0.0, 0.25, p)
        d.ellipse([hx - hr, hy - hr * 0.8, hx + hr, hy + hr * 0.8], fill=(40, 30, 22))
    if hatch is not None and CAP_OFF <= hatch < CAP_OFF + 0.06:
        img.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(150 * (1 - (hatch - CAP_OFF) / 0.06)))))
        d = ImageDraw.Draw(img)

    # labels
    for lab, what in st["labels"]:
        if what == "vessel":
            yc, yr, _ = yolk_state(day)
            pts, _, _ = VESSELS[2]
            tgt = _project(yc + yr * pts[len(pts) // 2], R, focus, cam)
            _pointer(d, tgt, lab, -1)
        elif what == "yolk":
            yc, yr, _ = yolk_state(day)
            _pointer(d, _project(yc, R, focus, cam), lab, 1, y_off=160)
        elif what in ("heart", "beak", "wing", "leg") and what in PARTS:
            side, yo = {"heart": (1, -150), "beak": (1, -120), "wing": (-1, -110), "leg": (-1, 120)}[what]
            _pointer(d, _project(PARTS[what], R, focus, cam), lab, side, y_off=yo)
        elif what == "air":
            _pointer(d, _project(np.array([0.25, 0.86, 0.2]), R, focus, cam), lab, -1, y_off=-90)
        elif what == "belly":
            bx, by = _project(np.array([0.0, 0.2, 0.3]), R, focus, cam)
            ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(ov).ellipse([bx - 70, by - 60, bx + 70, by + 60], fill=(255, 196, 40, 150),
                                       outline=(255, 240, 160, 255), width=5)
            img.alpha_composite(ov)
            d = ImageDraw.Draw(img)
            _pointer(d, (bx + 60, by), lab, 1, y_off=-170)

    # headline, day counter, sub-label
    pop = 0.85 + 0.15 * ms.ease(t_in / 0.2)
    if i in (0, 8):
        d.text((W / 2, 215), SEGMENTS[i]["head"], font=ImageFont.truetype(FONT_T, int(112 * pop)), fill=GOLD,
               anchor="mm", stroke_width=7, stroke_fill=(0, 0, 0))
    else:
        d.text((W / 2, 215), f"DAY {int(day)}", font=ImageFont.truetype(FONT_T, int(150 * pop)), fill=GOLD,
               anchor="mm", stroke_width=8, stroke_fill=(0, 0, 0))
        d.text((W / 2, 410), SEGMENTS[i]["head"], font=ImageFont.truetype(FONT_T, 70),
               fill=RED if i in (2, 7) else WHITE, anchor="mm", stroke_width=5, stroke_fill=(0, 0, 0))
    _timeline(d, day)
    if i == 0 and frac > REWIND_AT:
        d.text((W / 2, 410), "REWIND", font=ImageFont.truetype(FONT_T, 70), fill=CYAN, anchor="mm",
               stroke_width=5, stroke_fill=(0, 0, 0))
    if i == 8 and t_in > 0.9:
        ap = ms.ease(min(1, (t_in - 0.9) / 0.25))
        f = ImageFont.truetype(FONT_T, int(96 * (0.6 + 0.4 * ap)))
        for cx, lab, col in ((W / 2 - 200, "YES", (46, 204, 113)), (W / 2 + 200, "NO", RED)):
            d.rounded_rectangle([cx - 150, 1330, cx + 150, 1460], 40, fill=col, outline=(0, 0, 0), width=6)
            d.text((cx, 1397), lab, font=f, fill=WHITE, anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0))
    ms.caption(d, 1590, SEGMENTS[i]["line"], size=46)
    ms.watermark(d)
    return np.array(img.convert("RGB"))


def sound_events(starts, total):
    ev = [(0.0, sfx.impact(0.7)), (0.0, sfx.whoosh(0.3, 0.35))]
    d0 = starts[1] - starts[0]
    ev += [(starts[0] + REWIND_AT * d0 - 0.1, sfx.riser(0.6, 0.35)), (starts[1] - 0.05, sfx.whoosh(0.45, 0.45))]
    ev += [(starts[1] + 0.3, sfx.pop(0.45))]
    t = starts[2] + 0.1
    while t < starts[3] - 0.1:            # heartbeat, matching the 2.2/s pulse on screen
        ev += [(t, sfx.thump(0.7)), (t + 0.17, sfx.thump(0.45))]
        t += 1 / 2.2
    ev += [(starts[3], sfx.whoosh(0.5, 0.4)), (starts[3] + 0.4, sfx.riser(1.2, 0.2))]
    d4, d5 = starts[5] - starts[4], starts[6] - starts[5]
    for k in range(5):                    # the counter ticking day 5 -> 10
        ev.append((starts[4] + 0.3 * d4 * (k + 1) / 5 - 0.05, sfx.tick(1.0 + 0.1 * k, 0.5)))
    ev += [(starts[5], sfx.whoosh(0.4, 0.4))]
    for k in range(9):                    # ... and 10 -> 19
        ev.append((starts[5] + 0.25 * d5 * (k + 1) / 9 - 0.04, sfx.tick(1.1 + 0.06 * k, 0.4)))
    ev += [(starts[6], sfx.whoosh(0.4, 0.35)), (starts[6] + 0.35 * (starts[7] - starts[6]), sfx.pop(0.5))]
    d7 = starts[8] - starts[7]
    crack, off = starts[7] + CRACK_AT * d7, starts[7] + CAP_OFF * d7
    t = crack
    while t < off - 0.05:                 # pecks around the shell
        ev.append((t, sfx.tick(0.55, 0.75)))
        t += 0.16
    ev += [(crack, sfx.impact(0.6, low=False)), (off, sfx.impact(0.9, low=False)), (off + 0.15, sfx.pop(0.55))]
    ev += [(starts[8] + 0.9, sfx.pop(0.45))]
    return ev


if __name__ == "__main__":
    ms.render_short(SCRIPT, SEGMENTS, VIDEO_ID, frame, speed=1.1, sfx_fn=sound_events, music_vol=0.08)
