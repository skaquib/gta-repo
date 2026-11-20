"""
run_snake_egg_3d_short.py — "This egg is BIGGER than the snake's head",
rendered as a stylized 3D animation with render3d.py (2026-10-29).

Owner, 2026-10-29: no Gemini or AWS credits -- build it with what we have.
Same verified script as run_snake_egg_short.py (facts: Wikipedia
"Dasypeltis", Britannica "egg-eating snake", A-Z Animals), but every visual
is drawn in 3D here instead of AI images, so it costs nothing:

  0 hook   the jaws stretched around an egg wider than the head (size bracket)
  1        swallowed in three gulps -- the skin stretches pale over the egg
  2        x-ray: bony spikes hang down from the spine, just ahead of the egg
  3        the egg is pushed onto the spikes -- CRACK (flash, cracks, collapse)
  4        yolk bulge slides to the stomach, the crushed shell travels back out
  5        CTA, the shell lying beside the snake

Stylized animation, not photorealistic -> no altered-content label needed.
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
from run_snake_egg_short import SEGMENTS as _SEG

VIDEO_ID = "snake_egg_3d"
W, H = 1080, 1920
HERE = os.path.dirname(os.path.abspath(__file__))
FONT_T = os.path.join(HERE, "fonts", "BebasNeue-Regular.ttf")
GOLD, CYAN, RED = (255, 206, 84), (56, 217, 255), (255, 84, 72)

SEGMENTS = [dict(line=s["line"], head=s["head"]) for s in _SEG]

SCRIPT = {
    "hook": SEGMENTS[0]["line"],
    "body": " ".join(s["line"] for s in SEGMENTS[1:-1]),
    "cta": SEGMENTS[-1]["line"],
    "title": "This Egg Is BIGGER Than the Snake's Head 😳 (3D) #shorts",
    "tags": ["egg eating snake", "snake swallows egg", "snake facts", "animal facts", "what happens inside",
             "3d animation", "3d facts", "nature", "wildlife", "shorts"],
    "seo_description": (
        "African egg-eating snakes swallow eggs much bigger than their heads. Bony spikes from their "
        "spine poke into the throat and crack the egg from the inside -- then the snake spits the crushed "
        "shell back out. Animated in 3D by FramedFacts. #animals #snake #facts #3d #shorts"
    ),
    "ai_generated_visuals": False,
    "topic_category": "Animals",
}

# ── snake body: a tube along an S-shaped centreline, head at the top ──────────
# Side view: +N is the back (spine), -N the belly, +B faces the camera.
L = 3.4
S = np.concatenate([np.linspace(0.0, 2.6, 180), np.linspace(2.63, L, 24)])
NR = 24
TH = np.linspace(0, 2 * np.pi, NR, endpoint=False)
ZH = np.array([0.0, 0.0, 1.0])
EGG_A, EGG_B = 0.40, 0.30            # egg half-length / radius; the head's radius is 0.17
CRUSHED = (EGG_A * 0.78, EGG_B * 0.42, EGG_B * 0.62)
YOLK = (0.22, 0.19)


def centerline(s):
    s = np.asarray(s, dtype=float)
    amp = 0.42 * np.clip(0.2 + s / 1.5, 0.2, 1.0)
    x = amp * np.sin(1.35 * s + 0.15) - 0.42 * 0.2 * math.sin(0.15)
    y = 1.40 - 0.92 * s
    return np.stack([x, y, np.zeros_like(x)], -1)


def frames_at(s):
    s = np.asarray(s, dtype=float)
    T = centerline(s + 1e-3) - centerline(s - 1e-3)
    T = T / np.linalg.norm(T, axis=-1, keepdims=True)
    N = np.cross(ZH, T)
    N = N / np.linalg.norm(N, axis=-1, keepdims=True)
    B = np.cross(T, N)
    return T, N, B


def _at(s):
    """Centre point and (T, N, B) at one arc position."""
    T, N, B = frames_at(np.array([s]))
    return centerline(np.array([s]))[0], T[0], N[0], B[0]


P0 = centerline(S)
T0, N0, B0 = frames_at(S)
_RS = [0.0, 0.05, 0.15, 0.30, 0.45, 1.2, 2.2, 2.9, L]
_RR = [0.01, 0.09, 0.15, 0.17, 0.14, 0.165, 0.17, 0.09, 0.012]


def body_radius(s, objs=()):
    """objs: [(s_centre, half_length, radius)] inside the body -- the skin
    stretches over each one (soft max of the body and an egg-shaped profile)."""
    r = np.interp(s, _RS, _RR)
    for sc, a, b in objs:
        d = (s - sc) / (a * 1.12)
        prof = b * 1.08 * np.sqrt(np.clip(1 - d * d, 0, 1))
        r = (r ** 6 + prof ** 6) ** (1 / 6)
    return r


def _verts(r):
    ring = np.cos(TH)[None, :, None] * N0[:, None, :] + np.sin(TH)[None, :, None] * B0[:, None, :]
    return (P0[:, None, :] + r[:, None, None] * ring).reshape(-1, 3)


def _build_topology():
    tris, ring_i, th_mid = [], [], []
    for i in range(len(S) - 1):
        for j in range(NR):
            a, b = i * NR + j, i * NR + (j + 1) % NR
            c, d = (i + 1) * NR + j, (i + 1) * NR + (j + 1) % NR
            tris += [(a, c, d), (a, d, b)]
            ring_i += [i, i]
            th_mid += [TH[j] + math.pi / NR] * 2
    tris, ring_i, th_mid = np.array(tris), np.array(ring_i), np.array(th_mid)
    V = _verts(np.interp(S, _RS, _RR))
    p = V[tris]
    n = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0])
    inward = (n * (p.mean(1) - P0[ring_i])).sum(1) < 0        # face away from the centreline
    tris[inward] = tris[inward][:, [0, 2, 1]]
    return tris, ring_i, th_mid


def _smooth(e0, e1, x):
    x = np.clip((x - e0) / (e1 - e0), 0, 1)
    return x * x * (3 - 2 * x)


BODY_T, TRI_I, TRI_TH = _build_topology()
_NEXT = np.minimum(TRI_I + 1, len(S) - 1)
_SMID = (S[TRI_I] + S[_NEXT]) / 2
_RADIAL = np.cos(TRI_TH)[:, None] * N0[TRI_I] + np.sin(TRI_TH)[:, None] * B0[TRI_I]
_R0_TRI = np.interp(_SMID, _RS, _RR)


def _skin_colors():
    """Egg-eater pattern: dark saddles along the back, bars on the flank, pale belly."""
    s, th = _SMID, TRI_TH
    dorsal, flank = np.cos(th), np.sin(th)
    saddle = _smooth(0.25, 0.65, np.cos(2 * np.pi * s / 0.21)) * _smooth(-0.1, 0.4, dorsal)
    bars = _smooth(0.45, 0.8, np.cos(2 * np.pi * (s + 0.105) / 0.21)) * _smooth(0.35, 0.85, flank) * 0.85
    dark = np.maximum(saddle, bars)[:, None]
    col = np.array([140, 106, 70]) * (1 - dark) + np.array([62, 43, 28]) * dark
    belly = _smooth(-0.45, -0.75, dorsal)[:, None]
    col = col * (1 - belly) + np.array([210, 194, 154]) * belly
    head = _smooth(0.42, 0.25, s)[:, None] * 0.5                        # plainer, darker head
    col = col * (1 - head) + np.array([96, 72, 48]) * head
    col *= (0.92 + 0.08 * np.sin(s * 70) * np.sin(th * 12))[:, None]  # scale texture
    col[s < 0.03] = (48, 34, 24)                                          # lip line at the mouth
    return col


BODY_COL = _skin_colors()
XRAY_COL = BODY_COL * 0.4 + np.array([70, 170, 210]) * 0.6
_SPH_V, _SPH_T = r3.icosphere(3)
_SMALL_V, _SMALL_T = r3.icosphere(1)


def _body(objs, xray=False):
    r = body_radius(S, objs)
    V = _verts(r)
    slope = (r[_NEXT] - r[TRI_I]) / np.maximum(S[_NEXT] - S[TRI_I], 1e-6)
    Nsh = r3._unit(_RADIAL - slope[:, None] * T0[TRI_I])
    if xray:
        col = XRAY_COL
    else:   # stretched skin: scales spread apart and the pale skin between them shows
        stretch = np.interp(_SMID, S, r) / _R0_TRI
        k = np.clip((stretch - 1) * 0.6, 0, 0.6)[:, None]
        col = BODY_COL * (1 - k) + np.array([222, 204, 182]) * k
    return dict(V=V, T=BODY_T, colors=col, N=Nsh, spec=0.35, shin=35)


def _ellipsoid(center, Rm, axes, color, spec=0.3, shin=30, verts=_SPH_V, tris=_SPH_T, jitter=0.0, seed=0):
    V = verts * np.asarray(axes)
    if jitter:
        V = V + np.random.default_rng(seed).normal(0, jitter, V.shape)
    Vw = V @ Rm.T + center
    N = r3._unit(r3._unit(verts / np.asarray(axes)) @ Rm.T)[tris].mean(1)
    col = np.tile(color, (len(tris), 1)).astype(float)
    return dict(V=Vw, T=tris, colors=col, N=N, spec=spec, shin=shin)


def _frame_matrix(s):
    _, T, N, B = _at(s)
    return np.stack([T, N, B], 1)          # columns = local x, y, z


def _cone(base, tip, rad, color, n=10):
    a = r3._unit(tip - base)
    u = r3._unit(np.cross(a, [0.0, 0.0, 1.0]))
    w = np.cross(a, u)
    ring = np.array([base + rad * (math.cos(t) * u + math.sin(t) * w)
                     for t in np.linspace(0, 2 * np.pi, n, endpoint=False)])
    V = np.vstack([ring, tip[None], base[None]])
    tris = np.array([(i, (i + 1) % n, n) for i in range(n)] + [(n + 1, (i + 1) % n, i) for i in range(n)])
    p = V[tris]
    nrm = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0])
    inward = (nrm * (p.mean(1) - (base + tip) / 2)).sum(1) < 0
    tris[inward] = tris[inward][:, [0, 2, 1]]
    return dict(V=V, T=tris, colors=np.tile(color, (len(tris), 1)).astype(float), spec=0.5, shin=40)


VERT_S = np.arange(0.30, 3.0, 0.08)
SPIKE_S = np.arange(1.25, 1.72, 0.075)
SPIKE_TIP = 1.47
CRACK_AT = 0.735     # fraction of segment 3 where the voice says "crack!" (measured onset ~12.32s)
STOMACH = 2.45


def _spine(highlight=0.0):
    bone = np.array([236, 230, 212])
    meshes = []
    for s in VERT_S:
        c, T, N, B = _at(s)
        meshes.append(_ellipsoid(c + 0.12 * N, np.eye(3), (0.045,) * 3, bone, 0.3, 30, _SMALL_V, _SMALL_T))
    for s in SPIKE_S:
        c, T, N, B = _at(s)
        col = bone * (1 - highlight) + np.array(RED) * highlight
        meshes.append(_cone(c + 0.10 * N, c - 0.07 * N, 0.036, col))
    return meshes


def _eye(objs):
    c, T, N, B = _at(0.16)
    r = body_radius(np.array([0.16]), objs)[0]
    c = c + r * 0.97 * r3._unit(0.45 * N + 0.89 * B)
    return _ellipsoid(c, np.eye(3), (0.036,) * 3, (10, 10, 12), 0.9, 80, _SMALL_V, _SMALL_T)


def _transform(meshes, R, focus):
    out = []
    for m in meshes:
        m = dict(m)
        m["V"] = (m["V"] - focus) @ R.T
        if "N" in m:
            m["N"] = m["N"] @ R.T
        out.append(m)
    return out


def _background():
    ys, xs = np.mgrid[0:H, 0:W]
    t = ys / H
    base = np.stack([10 + 14 * t, 16 + 10 * t, 22 + 18 * t], -1)
    d = np.sqrt((xs - W / 2) ** 2 + ((ys - 980) * 1.1) ** 2) / 900
    glow = np.clip(1 - d, 0, 1) ** 2
    img = np.clip(base + glow[..., None] * np.array([40, 70, 60]), 0, 255).astype(np.uint8)
    return Image.fromarray(img).convert("RGBA")


_BG = _background()


def _lerp(a, b, p):
    return a + (b - a) * p


def scene_state(i, t_in, frac):
    """egg = (s, axes, jitter) or None; shell = world position or None; yolk = s or None."""
    st = dict(egg=None, shell=None, shell_s=None, yolk=None, xray=False, highlight=0.0,
              crack=0.0, collapse=0.0, labels=())
    if i == 0:
        se = -0.22 + 0.08 * ms.ease(min(1, t_in / 2.2))
        st.update(egg=(se, (EGG_A, EGG_B, EGG_B), 0), focus=_at(-0.08)[0], f=2750, measure=True)
    elif i == 1:
        k = min(frac * 3, 2.999)                                    # three gulps
        p = (math.floor(k) + ms.ease(k % 1)) / 3
        se = _lerp(-0.14, 0.82, p)
        st.update(egg=(se, (EGG_A, EGG_B, EGG_B), 0), focus=_at(_lerp(-0.08, 0.8, ms.ease(frac)))[0],
                  f=_lerp(2750, 2300, ms.ease(frac)))
    elif i == 2:
        st.update(egg=(_lerp(0.82, 0.87, frac), (EGG_A, EGG_B, EGG_B), 0), xray=True, focus=_at(1.15)[0],
                  f=_lerp(2300, 2800, ms.ease(t_in / 0.7)),
                  highlight=(0.5 + 0.5 * math.sin(t_in * 7)) * (frac > 0.3),
                  labels=(("SPIKES", "spike"),) if frac > 0.3 else ())
    elif i == 3:
        hit = CRACK_AT
        st.update(xray=True, highlight=1.0, focus=_at(1.3)[0], f=_lerp(2800, 3300, ms.ease(min(1, frac / hit))))
        if frac < hit:
            p = ms.ease(frac / hit)
            st["egg"] = (_lerp(0.87, SPIKE_TIP, p), (EGG_A, EGG_B * (1 - 0.06 * p), EGG_B), 0)
        else:
            k = min(1.0, (frac - hit) / 0.06)
            c = ms.ease(min(1.0, max(0.0, (frac - hit - 0.04) / 0.16)))
            axes = tuple(_lerp(np.array([EGG_A, EGG_B * 0.94, EGG_B]), np.array(CRUSHED), c))
            st.update(egg=(SPIKE_TIP, axes, 0.022 * c), crack=k, collapse=c, yolk=SPIKE_TIP if c > 0.3 else None)
    elif i == 4:
        ys = _lerp(SPIKE_TIP, STOMACH, ms.ease(min(1, frac * 1.5)))
        ss = _lerp(SPIKE_TIP, -0.5, ms.ease(frac))
        st.update(xray=True, yolk=ys, shell_s=ss, shell=_at(ss)[0], focus=_at(_lerp(1.3, 1.0, ms.ease(frac)))[0],
                  f=_lerp(3300, 1800, ms.ease(min(1, frac * 1.4))),
                  labels=(("YOLK", "yolk"), ("SHELL", "shell")) if frac > 0.25 else ())
    else:
        out = _at(-0.5)[0]
        p = ms.ease(min(1, t_in / 0.8))
        st.update(yolk=STOMACH, shell=out + p * np.array([0.6, -0.55, 0.0]), shell_spin=1.4 * p,
                  focus=_at(1.0)[0], f=1800)
    return st


def _project(p, R, focus, cam):
    c = (np.asarray(p, dtype=float) - focus) @ R.T
    z = cam.D - c[2]
    return cam.cx + cam.f * c[0] / z, cam.cy - cam.f * c[1] / z, cam.f / z


def _crack_overlay(img, cx, cy, rpx, k, fade):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    rng = np.random.default_rng(5)
    for n in range(11):
        ang = 2 * np.pi * n / 11 + rng.uniform(-0.2, 0.2)
        x, y = cx + 0.1 * rpx * math.cos(ang), cy + 0.1 * rpx * math.sin(ang)
        pts = [(x, y)]
        for _ in range(5):
            ang += rng.uniform(-0.6, 0.6)
            step = rpx * rng.uniform(0.13, 0.2) * k
            x, y = x + step * math.cos(ang), y + step * math.sin(ang)
            pts.append((x, y))
        d.line(pts, fill=(30, 22, 16, int(255 * fade)), width=7, joint="curve")
    img.alpha_composite(layer)


def _bracket(d, x0, x1, y, color, label, appear):
    xm, half = (x0 + x1) / 2, (x1 - x0) / 2 * appear
    a, b = xm - half, xm + half
    for w, c in ((11, (0, 0, 0)), (5, color)):
        d.line([(a, y), (b, y)], fill=c, width=w)
        d.line([(a, y - 22), (a, y + 22)], fill=c, width=w)
        d.line([(b, y - 22), (b, y + 22)], fill=c, width=w)
    if appear > 0.6:
        d.text((b + 22, y), label, font=ImageFont.truetype(FONT_T, 62), fill=color, anchor="lm",
               stroke_width=5, stroke_fill=(0, 0, 0))


def _pointer(d, target, label, side):
    tx, ty = target
    lx = 120 if side < 0 else W - 120
    ly = ty - 120
    d.line([(lx, ly), (tx, ty)], fill=(0, 0, 0), width=9)
    d.line([(lx, ly), (tx, ty)], fill=CYAN, width=4)
    d.ellipse([tx - 11, ty - 11, tx + 11, ty + 11], fill=CYAN, outline=(0, 0, 0), width=3)
    d.text((lx, ly - 8), label, font=ImageFont.truetype(FONT_T, 64), fill=CYAN, anchor="mb",
           stroke_width=5, stroke_fill=(0, 0, 0))


def frame(t, i, t_in, starts):
    seg_dur = (starts[i + 1] - starts[i]) if i + 1 < len(starts) else 3.5
    frac = min(1.0, t_in / max(seg_dur, 0.1))
    st = scene_state(i, t_in, frac)
    R = r3.rot_matrix(0.05 * math.sin(0.5 * t), 0.22 + 0.16 * math.sin(0.45 * t), 0.0)
    cam = r3.Camera(W / 2, 980, st["f"], 6.0)
    focus = np.asarray(st["focus"], dtype=float)

    # what is inside the body (the skin bulges over it) and the meshes for it
    objs, things = [], []
    if st["egg"]:
        se, axes, jit = st["egg"]
        objs.append((se, axes[0], max(axes[1], axes[2])))
        egg_col = (240, 234, 216) if st["collapse"] < 0.5 else (226, 220, 200)
        things.append(_ellipsoid(_at(se)[0], _frame_matrix(se), axes, egg_col, 0.45, 50, jitter=jit, seed=3))
    if st["yolk"] is not None:
        objs.append((st["yolk"], *YOLK))
        yaxes = (YOLK[0], YOLK[1] * 0.8, YOLK[1] * 0.8)
        if st["collapse"]:
            yaxes = tuple(a * min(1, st["collapse"] * 1.4) for a in yaxes)
        things.append(_ellipsoid(_at(st["yolk"])[0], _frame_matrix(st["yolk"]), yaxes, (246, 186, 36), 0.6, 60))
    if st["shell"] is not None:
        if st["shell_s"] is not None and st["shell_s"] > -0.3:
            objs.append((st["shell_s"], CRUSHED[0], max(CRUSHED[1:])))
        Rm = _frame_matrix(-0.4 if st["shell_s"] is None else st["shell_s"])
        if st.get("shell_spin"):
            Rm = r3.rot_matrix(0, 0, st["shell_spin"]) @ Rm
        things.append(_ellipsoid(st["shell"], Rm, CRUSHED, (226, 220, 200), 0.2, 20, jitter=0.022, seed=3))

    img = _BG.copy()
    body = _body(objs, xray=st["xray"])
    eye = _eye(objs)
    if st["xray"]:
        img.alpha_composite(r3.render(_transform(things, R, focus), (W, H), cam))
        img.alpha_composite(r3.render(_transform(_spine(st["highlight"]), R, focus), (W, H), cam))
        layer = r3.render(_transform([body, eye], R, focus), (W, H), cam)
        mask = layer.getchannel("A")
        edge = ImageChops.subtract(mask.filter(ImageFilter.MaxFilter(7)), mask).filter(ImageFilter.GaussianBlur(1.5))
        a = np.array(layer)
        a[..., 3] = (a[..., 3] * 0.42).astype(np.uint8)
        img.alpha_composite(Image.fromarray(a))
        glow = Image.new("RGBA", (W, H), CYAN + (0,))
        glow.putalpha(edge.point(lambda v: min(255, int(v * 0.9))))
        img.alpha_composite(glow)
    else:
        # anything inside is hidden by the skin drawn over it; the egg in the
        # mouth / the spat-out shell show where the body doesn't cover them
        img.alpha_composite(r3.render(_transform(things, R, focus), (W, H), cam))
        img.alpha_composite(r3.render(_transform([body, eye], R, focus), (W, H), cam))

    d = ImageDraw.Draw(img)
    if st["crack"] > 0 and st["egg"]:
        se = st["egg"][0]
        c, T, N, B = _at(se)
        cx, cy, ppu = _project(c, R, focus, cam)
        _crack_overlay(img, cx, cy, EGG_B * ppu, st["crack"], 1 - 0.7 * st["collapse"])
        if st["crack"] < 1.0:
            img.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(190 * (1 - st["crack"])))))
        d = ImageDraw.Draw(img)

    if st.get("measure") and t_in > 0.3:
        ap = ms.ease(min(1, (t_in - 0.3) / 0.35))
        se = st["egg"][0]
        for s_m, rad, col, lab in ((se, EGG_B, GOLD, "EGG"), (0.42, body_radius(np.array([0.42]))[0], CYAN, "HEAD")):
            c, T, N, B = _at(s_m)
            x0, y0, _ = _project(c - rad * N, R, focus, cam)
            x1, y1, _ = _project(c + rad * N, R, focus, cam)
            x0, x1 = sorted((x0, x1))
            _bracket(d, x0, x1, (y0 + y1) / 2, col, lab, ap)
    for lab, what in st["labels"]:
        if what == "spike":
            c, T, N, B = _at(1.4)
            tgt = _project(c - 0.03 * N, R, focus, cam)[:2]
            side = 1
        elif what == "yolk":
            tgt, side = _project(_at(st["yolk"])[0], R, focus, cam)[:2], 1
        else:
            tgt, side = _project(st["shell"], R, focus, cam)[:2], -1
        _pointer(d, tgt, lab, side)

    pop = 0.85 + 0.15 * ms.ease(t_in / 0.2)
    if i == 3 and st["crack"] > 0:
        pop *= 1.2
    d.text((W / 2, 220), SEGMENTS[i]["head"], font=ImageFont.truetype(FONT_T, int(122 * pop)),
           fill=GOLD if i in (0, 3) else (RED if i == 2 else (255, 255, 255)), anchor="mm",
           stroke_width=7, stroke_fill=(0, 0, 0))
    if st["xray"]:
        d.text((W / 2, 322), "X-RAY VIEW", font=ImageFont.truetype(FONT_T, 54), fill=CYAN, anchor="mm",
               stroke_width=4, stroke_fill=(0, 0, 0))
    if i == 5 and t_in > 0.5:
        ap = ms.ease(min(1, (t_in - 0.5) / 0.25))
        f = ImageFont.truetype(FONT_T, int(96 * (0.6 + 0.4 * ap)))
        for cx, lab, col in ((W / 2 - 200, "YES", (46, 204, 113)), (W / 2 + 200, "NO", RED)):
            d.rounded_rectangle([cx - 150, 1250, cx + 150, 1380], 40, fill=col, outline=(0, 0, 0), width=6)
            d.text((cx, 1317), lab, font=f, fill=(255, 255, 255), anchor="mm", stroke_width=4,
                   stroke_fill=(0, 0, 0))
    ms.caption(d, 1500, SEGMENTS[i]["line"], size=46)
    ms.watermark(d)
    return np.array(img.convert("RGB"))


def sound_events(starts, total):
    ev = [(0.0, sfx.impact(0.75)), (0.0, sfx.whoosh(0.3, 0.35)), (starts[0] + 0.35, sfx.pop(0.4))]
    d1 = starts[2] - starts[1]
    ev += [(starts[1] + d1 * k / 3, sfx.whoosh(0.35, 0.35)) for k in range(3)]          # the three gulps
    ev += [(starts[2], sfx.whoosh(0.4, 0.45)), (starts[2] + 0.1, sfx.pop(0.45))]
    d2 = starts[3] - starts[2]
    ev += [(starts[2] + 0.3 * d2, sfx.pop(0.4))]
    d3 = starts[4] - starts[3]
    crack = starts[3] + CRACK_AT * d3
    ev += [(crack - 0.8, sfx.riser(0.8, 0.35)), (crack, sfx.impact(0.95, low=False)), (crack, sfx.tick(0.6, 0.7)),
           (crack + 0.04, sfx.tick(0.5, 0.6)), (crack + 0.09, sfx.tick(0.7, 0.5))]
    ev += [(starts[4], sfx.whoosh(0.5, 0.45)), (starts[4] + 0.25 * (starts[5] - starts[4]), sfx.pop(0.4))]
    ev += [(starts[5], sfx.whoosh(0.4, 0.35)), (starts[5] + 0.6, sfx.pop(0.45))]
    return ev


if __name__ == "__main__":
    ms.render_short(SCRIPT, SEGMENTS, VIDEO_ID, frame, speed=1.1, sfx_fn=sound_events, music_vol=0.08)
