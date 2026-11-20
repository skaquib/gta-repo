"""
blender_jems.py — "What If ..." Shorts starring Jems (blender_hero.py), the channel's recurring character
(owner, 2026-11-16: "jems", no bag, lip-sync).

Everything in the scene is cel-shaded like Jems (blender_hero.toon), so he doesn't look pasted onto a lit
street. His mouth follows the narration: timing.json carries a per-frame "mouth" (loudness, 0..1) and "wide"
(brightness of the sound: ee vs oo) from dummy_shorts.step_voice when the spec sets "lipsync".

  friction   "What If Friction Disappeared for 5 Seconds?"
"""
import math
import random

import bpy
from mathutils import Vector

import blender_hero as bh
import blender_kit as bk
import blender_pitches as bp
import blender_tensec as ts
from blender_characters import add_outlines
from blender_tensec import EPS, FPS, O, k, pose, puffs, shot, shown

LIGHT = Vector((-0.45, -0.7, 0.62)).normalized()          # one fixed toon light for the whole street
AWAY = 60.0


def scene_base(samples, sky=(150, 196, 240)):
    sc = bk.new_scene(fps=FPS, res=ts.RES, samples=samples, frames=49)
    sc.cycles.transparent_max_bounces = 32
    sc.cycles.adaptive_min_samples = 4
    if bh.STYLE == "3d":                                         # daylight: a low warm sun, a blue sky for fill
        sc.view_settings.view_transform, sc.view_settings.look = "AgX", "AgX - Medium High Contrast"
        sc.render.use_motion_blur = True
        sc.render.motion_blur_shutter = 0.35
        bp.world(sc, bh.lin(sky), 0.9)
        bp.light("sun", "SUN", (0, 0, 20), 4.2, size=2.5, color=(1.0, 0.93, 0.82),
                 rot=(math.radians(52), math.radians(6), math.radians(-38)))
        return sc
    sc.view_settings.view_transform, sc.view_settings.look = "Standard", "None"
    sc.render.use_motion_blur = False                            # flat cel colours: crisp, like the drawing
    bp.world(sc, bh.lin(sky), 1.0)
    return sc


def aim_light():
    for inp in bh.DOTS:
        inp.default_value = tuple(LIGHT)


def toon_street(rnd, span=16.0):
    T = bh.toon
    out = []
    O_ = lambda o: out.append(o) or o
    bp.box("road", (200, 200, 0.2), (0, 0, -0.1), T("s_road", (96, 98, 104), shade=0.9, hi=False))
    O_(bp.box("pavement", (2 * span + 30, 3.2, 0.14), (0, 2.6, -0.03), T("s_pave", (176, 170, 160), hi=False), bevel=0.02))
    O_(bp.box("kerb", (2 * span + 30, 0.2, 0.16), (0, 0.95, -0.02), T("s_kerb", (150, 146, 140), hi=False), bevel=0.02))
    paint = T("s_paint", (238, 236, 226), hi=False)
    for j in range(int(span * 2 / 2.2) + 1):
        bp.box(f"dash{j}", (1.1, 0.12, 0.004), (-span + j * 2.2, -1.6, 0.002), paint)
    walls = [(232, 186, 140), (170, 200, 220), (240, 222, 170), (200, 150, 140), (196, 214, 180), (226, 200, 214)]
    glass = T("s_glass", (90, 130, 170), shade=0.8)
    frame_m = T("s_frame", (246, 244, 238), hi=False)
    x, j = -span, 0
    while x < span:
        w, h = rnd.uniform(3.2, 5.0), rnd.uniform(6.0, 11.0)
        O_(bp.box(f"house{j}", (w, 4, h), (x + w / 2, 6.5, h / 2), T(f"s_wall{j}", walls[j % len(walls)]), bevel=0.05))
        for fl in range(int((h - 0.6) // 1.7)):
            for q in range(int(w // 1.2)):
                cx, cz = x + 0.75 + q * 1.2, 1.5 + fl * 1.7
                bp.box(f"wf{j}_{fl}_{q}", (0.74, 0.04, 0.94), (cx, 4.48, cz), frame_m)
                bp.box(f"wg{j}_{fl}_{q}", (0.6, 0.05, 0.8), (cx, 4.47, cz), glass)
        x += w + rnd.uniform(0.1, 0.6)
        j += 1
    leaf, bark = T("s_leaf", (92, 150, 70)), T("s_bark", (110, 74, 50))
    for j, tx in enumerate((-4.6, 5.2)):
        O_(bp.cylinder(f"trunk{j}", 0.13, 2.4, (tx, 3.2, 1.2), bark, segs=16))
        O_(bp.lumpy(f"crown{j}", 1.25, (tx, 3.2, 3.1), leaf, seed=60 + j, amp=0.22))
    add_outlines(out, width=0.012)


def bench(at):
    """A wooden bench held together by nails: planks on two legs."""
    T = bh.toon
    wood, metal = T("s_wood", (176, 120, 72)), T("s_nail", (150, 154, 160))
    root = bp.pivot("bench", at)
    parts, nails = [], []
    for s in (-1, 1):
        parts.append(bp.box(f"bleg{s}", (0.08, 0.42, 0.42), (s * 0.62, 0, 0.21), wood, root, bevel=0.01))
    planks = []
    for j, y in enumerate((-0.13, 0.0, 0.13)):
        o = bp.box(f"plank{j}", (1.5, 0.12, 0.035), (0, y, 0.44), wood, root, bevel=0.008)
        planks.append(o)
        parts.append(o)
        for s in (-1, 1):
            n = bp.pivot(f"nailp{j}{s}", (s * 0.62, y, 0.459), root)
            bp.cylinder(f"nailhead{j}{s}", 0.02, 0.008, (0, 0, 0.002), metal, n, segs=14)
            bp.cylinder(f"nailshank{j}{s}", 0.007, 0.1, (0, 0, -0.05), metal, n, segs=8)
            nails.append(n)
    back = bp.box("bback", (1.5, 0.035, 0.22), (0, 0.2, 0.62), wood, root, bevel=0.008)
    parts.append(back)
    add_outlines(parts, width=0.006)
    return root, planks, nails, back


def micro_block(rnd):
    """Magnified: the bottom of a shoe sole resting on pavement, bumps caught in bumps."""
    T = bh.toon
    root = bp.pivot("micro", (AWAY, 0, MZ))
    bp.box("micro_bg", (8, 0.1, 6), (0, 1.0, 0.4), T("m_bg", (30, 34, 48), shade=1.0, hi=False), root)
    sole_m, pave_m = T("m_sole", (66, 66, 70)), T("m_pave", (170, 162, 150))
    pave = bp.pivot("pave", (0, 0, 0), root)
    sole = bp.pivot("sole", (0, 0, 0), root)
    parts = [bp.box("pave_body", (1.6, 0.4, 0.3), (0, 0, -0.17), pave_m, pave)]
    parts.append(bp.box("sole_body", (1.2, 0.4, 0.22), (0, 0, 0.19), sole_m, sole))
    step = 0.13
    for j in range(13):                                          # the pavement's bumps, pointing up
        x = -0.8 + step * j + rnd.uniform(-0.01, 0.01)
        o = bh.spike(f"pbump{j}", (x, 0, -0.035), (x + rnd.uniform(-0.012, 0.012), 0, 0.065 + rnd.uniform(-0.01, 0.012)),
                     0.062, pave_m, pave)
        parts.append(o)
    for j in range(10):                                          # the sole's, pointing down between them
        x = -0.6 + step * j + step / 2
        o = bh.spike(f"sbump{j}", (x, 0, 0.09), (x, 0, -0.005 + rnd.uniform(-0.008, 0.008)), 0.06, sole_m, sole)
        parts.append(o)
    add_outlines(parts, width=0.006)
    white = ts.emit("m_white", (1.0, 1.0, 1.0), 1.4)
    for name, text, z in (("sole", "SHOE SOLE", 0.15), ("pave", "PAVEMENT", -0.17)):
        ts.no_light(bp.stencil(f"mlab_{name}", text, (-0.05, -0.21, z), 0.07, white, root))
    O.update(micro=root, sole=sole)
    return root


def lipsync(P, T, f0, f1, shut=0.06):
    """Mouth from the narration envelope, frames f0..f1 (timing.json "mouth"/"wide")."""
    m, w = T.get("mouth"), T.get("wide")
    if not m:
        return
    prev = 0.0
    for f in range(max(0, f0), min(f1, len(m))):
        v = max(m[f], prev * 0.5)                                # snap open, ease shut
        prev = v
        op = shut + (1 - shut) * min(1.0, v * 1.15)
        wide = w[f] if w else 0.5
        k(P["mouth"], "scale", f, (0.72 + 0.4 * wide, 1.0, op), "LINEAR")
    k(P["mouth"], "scale", min(f1, len(m)), (1.0, 1.0, shut), "LINEAR")


def plant(sc, P, f0, f1, free=()):
    """No part of him ever goes into the ground: every frame, lift (or lower) him so his lowest point is exactly on
    the road. In `free` frames (mid-fall, feet off the ground) he is only ever lifted, never pulled down."""
    root = P["root"]
    parts = [o for o in bpy.data.objects if o.type in ("MESH", "CURVE") and _is_child(o, root)
             and not o.name.startswith(("phone", "mouth", "teeth", "tongue"))]
    corners = [(o, [Vector(c) for c in o.bound_box]) for o in parts]
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        low = min((o.matrix_world @ c).z for o, cs in corners for c in cs)
        dz = -low
        if f in free and dz < 0:
            continue
        if abs(dz) > 0.001:
            p = root.location.copy()
            k(root, "location", f, Vector((p.x, p.y, p.z + dz)), "LINEAR")
    sc.frame_set(f0)


def _is_child(o, root):
    while o.parent is not None:
        if o.parent == root:
            return True
        o = o.parent
    return False


def blinks(P, end, rnd, every=(60, 110)):
    f = rnd.randint(20, 50)
    while f < end - 6:
        for s, e in P["eyes"].items():
            for df, z in ((0, 1.0), (2, 0.1), (4, 1.0)):
                k(e, "scale", f + df, (1.0, 1.0, z), "LINEAR")
        f += rnd.randint(*every)


def brows(P, f, up):
    for b in P["brows"].values():
        k(b, "location", f, (0, 0, up), "BEZIER")


# ── friction ─────────────────────────────────────────────────────────────────
MZ = 1.6                              # the magnified block floats well above the road
SPLIT_Z = -0.7                        # root height in side splits: hips just off the road


def scene_friction(samples):
    rnd = random.Random(12)
    sc = scene_base(samples)
    toon_street(rnd)
    P = bh.build_hero(bag=False)
    P["root"].rotation_euler = (0, 0, math.radians(-10))
    shadow = bp.cylinder("shadow", 0.34, 0.003, (0, 0, 0.004), ts.emit("s_shadow", bh.lin((70, 72, 78)), 1.0))
    shadow.scale = (1.0, 0.7, 1.0)
    if bh.STYLE == "3d":                                         # real shadows now
        shadow.hide_render = True
    O.update(P=P, rnd=rnd, shadow=shadow)
    O["bench"] = bench((-1.25, 0.35, 0.0))
    micro_block(rnd)
    aim_light()
    cam = bp.cam_free(sc, 35, (0.6, -6.0, 0.6), (0, 0, 0.3))
    cam.data.dof.use_dof = False
    cam.data.clip_end = 300
    return sc


def timeline_friction(sc, T):
    fr = [int(round(t * FPS)) for t in T["starts"]] + [T["frames"]]
    S = dict(zip(T["shots"], zip(fr[:-1], fr[1:])))
    end = T["frames"] + 2
    cam, P, rnd = bpy.data.objects["cam"], O["P"], O["rnd"]
    root = P["root"]
    loc = lambda f, x, z, i="BEZIER": k(root, "location", f, Vector((x, 0, z)), i)
    blinks(P, end, rnd)
    stand = dict(sh=(2, 9, 0), el=(-12, 0, 0), head=(-2, 0, 0), chest=(0, 0, 0), hip=(0, 0, 0), kn=(0, 0, 0))

    # 1 slip: mid-stride on the pavement -- the front foot shoots away, arms fly out
    a, b = S["slip"]
    shot(cam, a, b, (1.0, -7.2, 0.95), (0, 0, 0.32), (0.9, -6.6, 0.9), (0, 0, 0.22), lens=35)
    loc(0, 0, 0)
    pose(P, 0, sh_1=(28, 6, 0), sh1=(-28, 6, 0), el=(-24, 0, 0), hip_1=(-24, 0, 0), hip1=(16, 0, 0),
         kn_1=(10, 0, 0), kn1=(24, 0, 0), head=(-2, 0, 0), chest=(2, 0, 0))
    pose(P, 8, sh_1=(-60, 60, 0), sh1=(-50, 70, 0), el=(-30, 0, 0), hip_1=(-8, 34, 0), hip1=(-4, 22, 0),
         kn_1=(4, 0, 0), kn1=(12, 0, 0), head=(14, 0, 0), chest=(-10, 0, 0))
    loc(8, 0, -0.08)
    pose(P, 18, sh=(-40, 80, 0), el=(-40, 0, 0), hip=(0, 64, 0), kn=(0, 0, 0),
         head=(6, 0, 10), chest=(-4, 0, 6))
    loc(18, 0, -0.5)
    pose(P, 26, sh=(-30, 84, 0), el=(-30, 0, 0), hip=(0, 82, 0), kn=(0, 0, 0),
         head=(-6, 0, -6), chest=(4, 0, 0))
    loc(26, 0, SPLIT_Z + 0.02)
    loc(32, 0, SPLIT_Z)
    brows(P, 0, 0.0), brows(P, 6, 0.008)
    pose(P, 40, sh=(-50, 70, 0), el=(-50, 0, 0), hip=(0, 82, 0), head=(-10, 0, 0), chest=(0, 0, 0))

    # 2 walk: trying to get up and walk -- legs pedal, the shoes skate on the spot
    a, b = S["walk"]
    shot(cam, a, b, (-1.8, -7.0, 0.95), (0, 0, 0.36), (-1.6, -6.4, 0.95), (0, 0, 0.36), lens=35)
    loc(a, 0, SPLIT_Z), loc(a + 14, 0, -0.02), loc(a + 20, 0, 0)
    pose(P, a, sh=(-50, 70, 0), el=(-50, 0, 0), hip=(0, 82, 0), head=(-10, 0, 0))
    pose(P, a + 16, sh=(-30, 50, 0), el=(-30, 0, 0), hip=(-10, 0, 0), kn=(20, 0, 0), head=(4, 0, 0), chest=(8, 0, 0))
    for j, f in enumerate(range(a + 22, b - 6, 7)):
        s = 1 if j % 2 else -1
        pose(P, f, sh_1=(30 * s, 40, 0), sh1=(-30 * s, 40, 0), el=(-40, 0, 0), hip_1=(-38 * s, 0, 0),
             hip1=(38 * s, 0, 0), kn_1=(30 + 20 * s, 0, 0), kn1=(30 - 20 * s, 0, 0), chest=(10, 0, 4 * s),
             head=(6, 0, -6 * s))
        loc(f, 0.02 * s, -0.03)
    brows(P, a, 0.008), brows(P, b - 4, 0.004)

    # 3 micro: magnified, the shoe's bumps sit in the pavement's -- then slide clean past
    a, b = S["micro"]
    mx = AWAY
    shot(cam, a, b, (mx - 0.05, -2.1, MZ - 0.1), (mx - 0.05, 0, MZ - 0.15), (mx - 0.05, -2.0, MZ - 0.1), (mx - 0.05, 0, MZ - 0.15), lens=40)
    sole = O["sole"]
    rel = a + int(0.55 * (b - a))                                # on "Now they slide right past"
    k(sole, "location", a, (0, 0, 0), "LINEAR"), k(sole, "location", rel - 8, (0, 0, 0), "LINEAR")
    k(sole, "location", rel - 4, (0, 0, 0.03), "LINEAR")         # it rides up over them...
    k(sole, "location", b, (0.85, 0, 0.03), "LINEAR")            # ...and skates away
    for j, f in enumerate(range(a, rel - 8, 6)):                 # straining against the catch
        k(sole, "location", f, (0.006 * (j % 2), 0, 0), "LINEAR")

    # 4 phone: close on his hand -- the phone slips out, drops, and keeps sliding across the road
    a, b = S["phone"]
    pose(P, a, sh_1=(-40, 14, 0), sh1=(-10, 30, 0), el_1=(-70, 0, 0), el1=(-30, 0, 0), hip=(-10, 0, 0),
         kn=(20, 0, 0), head=(26, 0, 10), chest=(8, 0, 0))
    loc(a, 0, -0.03)
    sc.frame_set(a)
    hand = P["phone"].matrix_world.translation.copy()
    shot(cam, a, a + 20, hand + Vector((0.6, -1.7, 0.05)), hand + Vector((0.0, 0, -0.32)),
         hand + Vector((0.6, -1.75, 0.0)), hand + Vector((0.05, 0, -0.38)), lens=35)
    shot(cam, a + 20, b, hand + Vector((0.6, -1.75, 0.0)), hand + Vector((0.05, 0, -0.38)),
         Vector((hand.x + 1.2, hand.y - 2.6, 0.6)), Vector((hand.x + 0.7, hand.y - 0.2, -0.35)), lens=35)
    drop = a + 20
    k(P["phone"], "scale", 0, (1, 1, 1), "CONSTANT"), k(P["phone"], "scale", drop, (0, 0, 0), "CONSTANT")
    k(P["phone"], "scale", S["end"][0], (1, 1, 1), "CONSTANT")
    sc.frame_set(drop)
    mw = P["phone"].matrix_world.copy()
    free = bp.pivot("phone_free", mw.translation)
    free.rotation_euler = mw.to_euler()
    bp.box("phone_free_body", (0.012, 0.075, 0.15), (0, 0, 0), bpy.data.materials["h_band"], free, bevel=0.006)
    p0 = mw.translation.copy()
    t_fall = math.sqrt(2 * max(0.01, p0.z - 0.01) / 9.81)
    land = drop + int(t_fall * FPS)
    k(free, "location", drop, p0, "LINEAR")
    for f in range(drop + 1, land + 1):
        t = (f - drop) / FPS
        k(free, "location", f, (p0.x, p0.y, max(0.008, p0.z - 4.9 * t * t)), "LINEAR")
    k(free, "rotation_euler", drop, free.rotation_euler.copy(), "LINEAR")
    k(free, "rotation_euler", land, (0, math.radians(90), 0.4), "LINEAR")
    k(free, "location", end, (p0.x + 1.6 * (end - land) / FPS, p0.y - 0.3, 0.008), "LINEAR")   # never slows down
    k(free, "rotation_euler", end, (0, math.radians(90), 0.4 + 0.2 * (end - land) / FPS), "LINEAR")
    shown(free, drop, S["end"][0])
    brows(P, drop - 2, 0.0), brows(P, drop + 4, 0.009)

    # 5 laces: close on the shoes -- the bows slide apart and the ends drop loose
    a, b = S["laces"]
    pose(P, a, sh=(-10, 30, 0), el=(-30, 0, 0), hip=(-6, 0, 0), kn=(10, 0, 0), head=(30, 0, 0), chest=(10, 0, 0))
    loc(a, 0, -0.01)
    shot(cam, a, b, (0.45, -1.05, 0.3), (0, -0.05, -0.1), (0.4, -0.95, 0.28), (0, -0.05, -0.1), lens=32)
    undo = a + int(1.4 * FPS)
    for s, bow in P["bows"].items():
        for ch in bow.children:
            k(ch, "scale", undo + (0 if s < 0 else 5), tuple(ch.scale), "LINEAR")
            if ch.name.startswith("loop"):
                k(ch, "scale", undo + 14 + (0 if s < 0 else 5), (0.05, 0.05, 0.05), "LINEAR")
            else:
                k(ch, "rotation_euler", undo + (0 if s < 0 else 5), tuple(ch.rotation_euler), "LINEAR")
                k(ch, "rotation_euler", undo + 14 + (0 if s < 0 else 5), (math.radians(100), 0, ch.rotation_euler.z),
                  "LINEAR")
                k(ch, "scale", undo + 14 + (0 if s < 0 else 5), (1, 1, 1.8), "LINEAR")

    # 6 nails: the bench beside him -- nails creep up out of the wood, the planks slide off, it folds
    a, b = S["nails"]
    broot, planks, nails, back = O["bench"]
    bx = broot.location
    shot(cam, a, b, (bx.x + 0.5, bx.y - 2.6, 1.25), (bx.x, bx.y, 0.2), (bx.x + 0.6, bx.y - 3.0, 1.2), (bx.x, bx.y, 0.12),
         lens=35)
    for j, n in enumerate(nails):
        f0 = a + 10 + j * 3
        z0 = n.location.z
        k(n, "location", f0, tuple(n.location), "LINEAR")
        k(n, "location", f0 + 18, (n.location.x, n.location.y, z0 + 0.06), "LINEAR")
        k(n, "location", f0 + 30, (n.location.x + rnd.uniform(-0.1, 0.1), n.location.y - 0.2, 0.004), "LINEAR")
        k(n, "rotation_euler", f0 + 18, (0, 0, 0), "LINEAR")
        k(n, "rotation_euler", f0 + 30, (math.radians(90), 0, rnd.uniform(0, 3)), "LINEAR")
    slide = a + 36
    for j, pl in enumerate(planks + [back]):
        p0 = pl.location.copy()
        k(pl, "location", slide + j * 3, tuple(p0), "LINEAR")
        k(pl, "location", slide + 16 + j * 3, (p0.x + 0.5 + 0.15 * j, p0.y - 0.05 * j, max(0.02 + 0.04 * j, p0.z - 0.35)),
          "LINEAR")
        k(pl, "rotation_euler", slide + j * 3, tuple(pl.rotation_euler), "LINEAR")
        k(pl, "rotation_euler", slide + 16 + j * 3, (0, math.radians(rnd.uniform(-18, 18)), rnd.uniform(-0.2, 0.2)),
          "LINEAR")
    pose(P, a, sh=(-10, 30, 0), el=(-30, 0, 0), hip=(-6, 0, 0), kn=(10, 0, 0), head=(4, 0, 30), chest=(4, 0, 10))
    # Jems loses his footing again while he watches
    pose(P, b - 18, sh=(-40, 70, 0), el=(-40, 0, 0), hip=(0, 50, 0), head=(6, 0, 10))
    loc(b - 18, 0, -0.2)
    pose(P, b - 4, **dict(sh=(-30, 80, 0), el=(-30, 0, 0), hip=(0, 82, 0), head=(-6, 0, -6)))
    loc(b - 4, 0, SPLIT_Z)

    # 7 time's up: back in the splits, friction back -- stuck, a sheepish smile
    a, b = S["timesup"]
    shot(cam, a, b, (-0.9, -5.0, 0.8), (0, 0, -0.05), (-0.8, -4.4, 0.75), (0, 0, -0.02), lens=35)
    pose(P, a, sh=(-30, 80, 0), el=(-30, 0, 0), hip=(0, 82, 0), head=(-6, 0, -6), chest=(0, 0, 0))
    loc(a, 0, SPLIT_Z)
    pose(P, a + 30, sh_1=(-30, 80, 0), sh1=(-150, 10, 0), el_1=(-30, 0, 0), el1=(-60, 0, 0), head=(-4, 0, 14),
         chest=(-4, 0, 0))
    pose(P, b - 2, sh_1=(-30, 80, 0), sh1=(-150, 10, 0), el_1=(-30, 0, 0), el1=(-70, 0, 0), head=(-6, 0, 18))
    brows(P, a, 0.006), brows(P, a + 20, -0.002)

    # 8 end: he talks to you from the splits, the camera coming in on his face
    a, b = S["end"]
    shot(cam, a, b, (-0.4, -4.4, 0.85), (0, 0, 0.05), (-0.15, -2.4, 1.15), (0, 0, 0.92), lens=35)
    pose(P, a, sh_1=(-30, 80, 0), sh1=(-150, 10, 0), el_1=(-30, 0, 0), el1=(-70, 0, 0), head=(-6, 0, 18))
    pose(P, a + 20, sh_1=(-30, 80, 0), sh1=(-30, 70, 0), el1=(-50, 0, 0), head=(-8, 0, 0), chest=(-2, 0, 0))
    pose(P, b, sh_1=(-30, 80, 0), sh1=(-34, 70, 0), el1=(-54, 0, 0), head=(-6, 0, 4))
    brows(P, a, 0.004)

    lipsync(P, T, 0, T["frames"])                                # he narrates the whole Short
    plant(sc, P, 0, T["frames"], free=range(4, 27))


TIMELINES = {"friction": (scene_friction, timeline_friction)}


# ── spin: "What If the Earth Stopped Spinning for 5 Seconds?" ─────────────────
GLOBE_AT = Vector((-300.0, 0.0, 0.0))
OCEAN_AT = Vector((300.0, 0.0, 0.0))
BRAIN_AT = Vector((700.0, 700.0, 2.0))
POLE_X, REST_X = 20.0, 30.0


def car(name, srgb, at, yaw=0.0):
    T = bh.toon
    root = bp.pivot(name, at, rot=(0, 0, yaw))
    body = T(f"{name}_paint", srgb)
    glass = T(f"{name}_glass", (40, 52, 66))
    tyre = T(f"{name}_tyre", (26, 26, 28))
    bp.box(f"{name}_body", (3.8, 1.7, 0.62), (0, 0, 0.58), body, root, bevel=0.14)
    bp.box(f"{name}_cabin", (2.0, 1.52, 0.56), (-0.25, 0, 1.12), glass, root, bevel=0.1)
    bp.box(f"{name}_roof", (1.9, 1.5, 0.08), (-0.25, 0, 1.42), body, root, bevel=0.03)
    for sx in (-1.25, 1.25):
        for sy in (-0.86, 0.86):
            bp.cylinder(f"{name}_wheel{sx}{sy}", 0.34, 0.24, (sx, sy, 0.34), tyre, root, rot=(math.radians(90), 0, 0),
                        segs=24, bevel=0.04)
    lamp = ts.emit(f"{name}_lamp", (1.0, 0.95, 0.8), 2.0)
    for sy in (-0.6, 0.6):
        bp.box(f"{name}_light{sy}", (0.04, 0.3, 0.12), (1.91, sy, 0.68), lamp, root)
    return root


def streak_mat():
    m = bpy.data.materials.new("streak")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    tr, em, mx = nt.nodes.new("ShaderNodeBsdfTransparent"), nt.nodes.new("ShaderNodeEmission"), nt.nodes.new("ShaderNodeMixShader")
    em.inputs["Color"].default_value, em.inputs["Strength"].default_value = (1, 1, 1, 1), 0.9
    mx.inputs[0].default_value = 0.4
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(em.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], nt.nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
    return m


def globe_set(rnd):
    root = bp.pivot("gl_root", tuple(GLOBE_AT))
    black = ts.emit("space", (0.0, 0.0, 0.0), 1.0)
    bp.box("space_back", (80, 1, 80), (0, 16, 0), black, root)
    star = ts.emit("gl_star", (1.0, 1.0, 1.0), 4.0)
    for j in range(140):
        ts.no_light(bp.ellipsoid(f"gl_star{j}", (0.03,) * 3, (rnd.uniform(-16, 16), 15.4, rnd.uniform(-16, 16)), star,
                                 root, segs=6, rings=4))
    tilt = bp.pivot("gl_tilt", (0, 0, 0), root, rot=(math.radians(-22), 0, 0))
    spin = bp.pivot("gl_spin", (0, 0, 0), tilt)
    m = bp.mat("earth3d", (0.02, 0.1, 0.3), rough=0.45)
    nt = m.node_tree
    tex = nt.nodes.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value, tex.inputs["Detail"].default_value = 1.6, 8.0
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(tc.outputs["Object"], tex.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "CONSTANT"
    ramp.color_ramp.elements[0].color = (0.01, 0.06, 0.2, 1)
    ramp.color_ramp.elements[1].position = 0.54
    ramp.color_ramp.elements[1].color = (0.12, 0.25, 0.07, 1)
    sand = ramp.color_ramp.elements.new(0.66)
    sand.color = (0.38, 0.3, 0.16, 1)
    nt.links.new(tex.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    bp.ellipsoid("earth", (3.0, 3.0, 3.0), (0, 0, 0), m, spin, segs=128, rings=64)
    cloud = bp.mat("clouds", (1, 1, 1), rough=0.9, alpha=0.55)
    cn = cloud.node_tree
    ct = cn.nodes.new("ShaderNodeTexNoise")
    ct.inputs["Scale"].default_value, ct.inputs["Detail"].default_value = 3.5, 6.0
    cr = cn.nodes.new("ShaderNodeMapRange")
    cr.inputs["From Min"].default_value, cr.inputs["From Max"].default_value = 0.55, 0.7
    nt2 = cn.nodes.new("ShaderNodeTexCoord")
    cn.links.new(nt2.outputs["Object"], ct.inputs["Vector"])
    cn.links.new(ct.outputs["Fac"], cr.inputs["Value"])
    cn.links.new(cr.outputs["Result"], cn.nodes["Principled BSDF"].inputs["Alpha"])
    bp.ellipsoid("clouds", (3.04,) * 3, (0, 0, 0), cloud, spin, segs=96, rings=48)
    gold = ts.emit("spin_ring", (1.0, 0.75, 0.1), 3.0)
    bpy.ops.mesh.primitive_torus_add(major_radius=3.35, minor_radius=0.035, major_segments=128, minor_segments=8)
    ring = bpy.context.active_object
    ring.name, ring.parent = "spin_ring", tilt
    ring.data.materials.append(gold)
    ts.no_light(ring)
    for j in range(3):                                           # arrowheads riding the ring, eastward
        a = j * 2 * math.pi / 3
        o = bh.spike(f"spin_arrow{j}", (3.35 * math.cos(a), 3.35 * math.sin(a), 0),
                     (3.35 * math.cos(a) - 0.45 * math.sin(a), 3.35 * math.sin(a) + 0.45 * math.cos(a), 0), 0.14, gold, spin)
        ts.no_light(o)
    bp.light("gl_key", "AREA", tuple(GLOBE_AT + Vector((-7, -9, 6))), 2600, size=6, color=(1.0, 0.97, 0.92),
             aim=tuple(GLOBE_AT))
    O.update(gl_spin=spin)


def ocean_set(rnd):
    root = bp.pivot("oc_root", tuple(OCEAN_AT))
    water = bp.mat("sea", (0.01, 0.08, 0.13), rough=0.06, coat=1.0)
    bp.add_bump(water, 1.4, 0.5, distance=0.15)
    bp.box("sea_flat", (90, 90, 0.2), (-20, 0, -0.1), water, root)
    concrete = bh.toon("oc_wall", (150, 146, 140))
    bp.box("seawall", (2.0, 60, 3.0), (12, 0, 1.0), concrete, root, bevel=0.05)
    bp.box("promenade", (30, 60, 0.4), (27, 0, 2.3), bh.toon("oc_pave", (176, 170, 160)), root)
    walls = [(232, 186, 140), (170, 200, 220), (240, 222, 170), (200, 150, 140)]
    for j in range(8):
        h = rnd.uniform(6, 14)
        bp.box(f"oc_house{j}", (5, 4.5, h), (22, -16 + j * 5.2, 2.5 + h / 2), bh.toon(f"oc_wallc{j}", walls[j % 4]),
               root, bevel=0.05)
    wave = bp.pivot("wave", (-38, 0, 0), root)
    prof = [(-16, -0.1), (-10, 1.4), (-5, 3.8), (-2, 6.6), (0.2, 8.6), (1.8, 8.9), (2.9, 8.0), (3.1, 6.6), (2.5, 5.8)]
    import bmesh
    bm = bmesh.new()
    rows = []
    for q in range(41):
        y = -30 + 1.5 * q
        rows.append([bm.verts.new((px, y, pz)) for px, pz in prof])
    for q in range(40):
        for j in range(len(prof) - 1):
            bm.faces.new((rows[q][j], rows[q][j + 1], rows[q + 1][j + 1], rows[q + 1][j]))
    me = bpy.data.meshes.new("wave_mesh")
    bm.to_mesh(me)
    bm.free()
    wm = bp.mat("wave_water", (0.02, 0.16, 0.22), rough=0.05, coat=1.0, sss=0.2)
    bp.add_bump(wm, 2.5, 0.6, distance=0.12)
    me.materials.append(wm)
    for p_ in me.polygons:
        p_.use_smooth = True
    w = bp.link(bpy.data.objects.new("wave_body", me), wave)
    w.modifiers.new("sub", "SUBSURF").levels = 2
    tex = bpy.data.textures.new("wave_noise", "CLOUDS")
    tex.noise_scale = 2.2
    d = w.modifiers.new("ripple", "DISPLACE")
    d.texture, d.strength = tex, 0.7
    foam = bp.mat("foam", (0.92, 0.95, 0.97), rough=0.7, sss=0.3)
    bp.add_bump(foam, 6.0, 0.8, distance=0.08)
    crest = bp.cylinder("crest", 0.55, 60, (1.9, 0, 8.7), foam, wave, rot=(math.radians(90), 0, 0), segs=24)
    crest.modifiers.new("sub", "SUBSURF").levels = 1
    d2 = crest.modifiers.new("ripple", "DISPLACE")
    d2.texture, d2.strength = tex, 0.6
    for j in range(14):                                          # foam blobs riding the lip
        bp.lumpy(f"foam{j}", rnd.uniform(0.6, 1.1), (rnd.uniform(1.0, 3.0), -28 + j * 4.2, rnd.uniform(8.2, 9.4)), foam,
                 wave, seed=700 + j, amp=0.35)
    O.update(wave=wave, oc_root=root)


def brain_set():
    T = bh.toon
    root = bp.pivot("br_root", tuple(BRAIN_AT))
    bp.box("br_back", (12, 0.1, 10), (0, 1.2, 0), ts.emit("br_bg", (0.015, 0.02, 0.04), 1.0), root)
    head = bp.pivot("br_head", (0, 0, 0), root)
    disc = lambda n, r, y, m: bp.cylinder(n, 1.0, 0.04, (0.0, y, 0.0), m, head, rot=(math.radians(90), 0, 0),
                                          segs=96)
    for name, (rx, rz), y, col in (("br_skin", (0.56, 0.66), 0.0, (244, 206, 178)), ("br_skull", (0.5, 0.6), -0.02,
                                   (238, 232, 216)), ("br_fluid", (0.44, 0.54), -0.04, (150, 205, 235))):
        o = disc(name, 1.0, y, T(f"{name}_m", col))
        o.scale = (rx, rz, 1.0)
    bp.ellipsoid("br_nose", (0.09, 0.03, 0.08), (0.57, 0.0, -0.08), T("br_skin_m2", (244, 206, 178)), head)
    brain = bp.pivot("br_brain", (0, 0, 0.02), head)
    bm_ = bp.mat("br_brain_m", (0.92, 0.55, 0.6), rough=0.45, sss=0.2)
    nt = bm_.node_tree
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.inputs["Scale"].default_value, wave.inputs["Distortion"].default_value = 9.0, 9.0
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(tc.outputs["Object"], wave.inputs["Vector"])
    bmp = nt.nodes.new("ShaderNodeBump")
    bmp.inputs["Strength"].default_value, bmp.inputs["Distance"].default_value = 0.9, 0.02
    nt.links.new(wave.outputs["Fac"], bmp.inputs["Height"])
    nt.links.new(bmp.outputs["Normal"], nt.nodes["Principled BSDF"].inputs["Normal"])
    bp.ellipsoid("br_brain_body", (0.38, 0.12, 0.44), (0, -0.08, 0), bm_, brain, segs=64, rings=32)
    white = ts.emit("br_white", (1.0, 1.0, 1.0), 1.5)
    for name, text, x, z in (("skull", "SKULL", -0.52, 0.42), ("fluid", "FLUID", -0.47, 0.2), ("brain", "BRAIN", -0.3, -0.05)):
        ts.no_light(bp.stencil(f"brlab_{name}", text, (x - 0.42, -0.2, z), 0.1, white, root))
        ts.no_light(bp.box(f"brlead_{name}", (0.14, 0.006, 0.008), (x - 0.13, -0.2, z), white, root))
    flash = ts.no_light(bp.ellipsoid("br_flash", (0.06, 0.02, 0.2), (0.4, -0.2, 0.02), ts.emit("br_flash_m", (1.0, 0.9, 0.4), 6.0),
                                     head))
    bp.light("br_key", "AREA", tuple(BRAIN_AT + Vector((-1.5, -4.0, 2.0))), 220, size=3, aim=tuple(BRAIN_AT))
    O.update(br_head=head, br_brain=brain, br_flash=flash)


def scene_spin(samples):
    rnd = random.Random(31)
    sc = scene_base(samples)
    toon_street(rnd, span=60.0)
    P = bh.build_hero(bag=False)
    O.update(P=P, rnd=rnd)
    O["cars"] = [car("carA", (200, 40, 40), (-26, 3.2, 0)), car("carB", (40, 110, 200), (-12, -2.2, 0)),
                 car("carC", (240, 200, 60), (REST_X - 0.2, 1.25, 0), yaw=math.radians(8))]
    bp.cylinder("lamp_pole", 0.07, 4.2, (POLE_X, 0.9, 2.1), bh.toon("pole", (70, 74, 80)), segs=16)
    bp.box("lamp_head", (0.9, 0.18, 0.12), (POLE_X + 0.4, 0.9, 4.18), bh.toon("pole2", (70, 74, 80)))
    sm = streak_mat()
    O["streaks"] = [ts.no_light(bp.ellipsoid(f"streak{j}", (rnd.uniform(0.5, 1.2), 0.01, 0.01), (0, 0, 0), sm,
                                             segs=12, rings=6)) for j in range(70)]
    deb = []
    crate = bh.toon("crate", (150, 104, 60))
    paper = bh.toon("paper", (236, 234, 226))
    leaf = bh.toon("leafd", (120, 150, 60))
    binm = bh.toon("bin", (40, 90, 60))
    for j in range(12):
        deb.append(bp.box(f"crate{j}", (0.4, 0.4, 0.35), (0, 0, 0), crate, bevel=0.02))
    for j in range(30):
        deb.append(bp.box(f"paper{j}", (0.21, 0.3, 0.003), (0, 0, 0), paper))
    for j in range(40):
        deb.append(bp.ellipsoid(f"leafd{j}", (0.05, 0.03, 0.004), (0, 0, 0), leaf, segs=10, rings=6))
    for j in range(5):
        deb.append(bp.cylinder(f"bin{j}", 0.28, 0.9, (0, 0, 0), binm, segs=20))
    O["debris"] = deb
    stars = bp.pivot("dizzy", (0, 0, 0.36), P["head"])
    ystar = ts.emit("dizzy_m", (1.0, 0.85, 0.15), 4.0)
    for j in range(5):
        a = j * 2 * math.pi / 5
        ts.no_light(bp.ellipsoid(f"dizzy{j}", (0.035,) * 3, (0.2 * math.cos(a), 0.2 * math.sin(a), 0), ystar, stars,
                                 segs=8, rings=6))
    O["dizzy"] = stars
    globe_set(rnd)
    ocean_set(rnd)
    brain_set()
    aim_light()
    cam = bp.cam_free(sc, 30, (0, -6, 1), (0, 0, 1))
    cam.data.dof.use_dof = False
    cam.data.clip_end = 400
    return sc


def timeline_spin(sc, T):
    fr = [int(round(t * FPS)) for t in T["starts"]] + [T["frames"]]
    S = dict(zip(T["shots"], zip(fr[:-1], fr[1:])))
    end = T["frames"] + 2
    cam, P, rnd = bpy.data.objects["cam"], O["P"], O["rnd"]
    root = P["root"]
    R = lambda f, x, y, z, rx=0.0, ry=0.0, rz=-10.0, i="LINEAR": (
        k(root, "location", f, Vector((x, y, z)), i),
        k(root, "rotation_euler", f, (math.radians(rx), math.radians(ry), math.radians(rz)), i))
    blinks(P, end, rnd)

    # 1 fling: frame 0 he is already flying east, head first, tumbling, with the street streaming past
    a, b = S["fling"]
    x0, x1 = -34.0, -20.0
    for f in range(a, b + 1, 6):
        u = (f - a) / max(1, b - a)
        x = x0 + (x1 - x0) * u
        R(f, x, -0.3, 1.25 + 0.15 * math.sin(f * 0.25), rx=-20, ry=72 + 40 * u, rz=-10 + 6 * math.sin(f * 0.2))
        s_ = 1 if (f // 6) % 2 else -1
        pose(P, f, sh_1=(-150 + 25 * s_, 25, 0), sh1=(-150 - 25 * s_, 25, 0), el=(-30, 0, 0), hip_1=(10 * s_, 22, 0),
             hip1=(-10 * s_, 22, 0), kn=(35, 0, 0), head=(-10, 0, 0), chest=(-6, 0, 0))
    shot(cam, a, b, (x0 + 1.4, -7.6, 1.35), (x0 + 0.9, 0, 0.42), (x1 + 1.4, -7.6, 1.35), (x1 + 0.9, 0, 0.42), lens=30)
    ca = O["cars"][0]                                             # a car tumbling past behind him
    for f in range(a, b + 1, 8):
        u = (f - a) / max(1, b - a)
        k(ca, "location", f, (x0 - 5 + (x1 - x0 + 9) * u, 6.0, 2.3 + 0.5 * math.sin(u * 3)), "LINEAR")
        k(ca, "rotation_euler", f, (math.radians(30 * u), math.radians(-160 * u), 0), "LINEAR")
    brows(P, 0, 0.01)

    # 2 globe: Earth from space, spinning east... then it jolts to a stop
    a, b = S["globe"]
    G = GLOBE_AT
    shot(cam, a, b, (G.x + 0.4, -13.0, 0.8), (G.x, 0, -2.0), (G.x + 0.3, -12.0, 0.7), (G.x, 0, -2.0), lens=20)
    spin, stop = O["gl_spin"], b - 45
    k(spin, "rotation_euler", a, (0, 0, 0), "LINEAR")
    k(spin, "rotation_euler", stop, (0, 0, math.radians(0.9 * (stop - a))), "LINEAR")
    k(spin, "rotation_euler", stop + 3, (0, 0, math.radians(0.9 * (stop - a) + 1.0)), "BEZIER")
    k(spin, "rotation_euler", stop + 8, (0, 0, math.radians(0.9 * (stop - a) + 0.6)), "BEZIER")

    # 3 street: the ground has stopped; Jems and the cars tumble east along the road
    a, b = S["street"]
    shot(cam, a, b, (-9.0, -13.0, 2.6), (-7.0, 0, 0.2), (7.0, -13.0, 2.6), (9.0, 0, 0.2), lens=24)
    for f in range(a, b + 1, 4):
        u = (f - a) / max(1, b - a)
        x = -12 + 22 * u
        R(f, x, -0.4, 0.15 + 0.35 * abs(math.sin(u * 9)), rx=0, ry=-720 * u, rz=-10)
        pose(P, f, sh=(-40, 40, 0), el=(-60, 0, 0), hip=(-70, 0, 0), kn=(100, 0, 0), chest=(20, 0, 0), head=(20, 0, 0))
    for c, (y, x0_, x1_, spin_) in zip(O["cars"][:2], ((2.4, -18, 8, 1), (-2.4, -10, 14, -1))):
        for f in range(a, b + 1, 6):
            u = (f - a) / max(1, b - a)
            k(c, "location", f, (x0_ + (x1_ - x0_) * u, y, 0.9 + 0.6 * abs(math.sin(u * 5))), "LINEAR")
            k(c, "rotation_euler", f, (math.radians(spin_ * 25 * math.sin(u * 4)), math.radians(-300 * u), 0), "LINEAR")
    plant(sc, P, a, b, free=range(a, b + 1))

    # 4 wind: he grabs a lamp post and flaps out sideways like a flag
    a, b = S["wind"]
    hold = POLE_X + 2.12
    for f in range(a, b + 1, 3):
        s_ = math.sin(f * 0.9)
        R(f, hold, 0.9, 1.75 + 0.06 * s_, rx=8 * s_, ry=-90 + 4 * math.sin(f * 0.5), rz=-10 + 5 * s_)
        pose(P, f, sh=(-178, 4, 0), el=(-4, 0, 0), hip_1=(12 * s_, 6, 0), hip1=(-12 * s_, 6, 0), kn=(10 + 8 * s_, 0, 0),
             head=(20, 0, 0), chest=(4 * s_, 0, 0))
    shot(cam, a, b, (POLE_X + 3.4, -5.2, 2.1), (POLE_X + 1.3, 0.9, 1.3), (POLE_X + 3.2, -4.8, 2.0), (POLE_X + 1.3, 0.9, 1.3),
         lens=28)
    for c in O["cars"][:2]:
        k(c, "location", a, (POLE_X + 40, 0, 0), "CONSTANT")

    # 5 ocean: a wall of water races in and smashes into the sea wall
    a, b = S["ocean"]
    oc = OCEAN_AT
    shot(cam, a, b, (oc.x + 4, -46, 7.5), (oc.x + 2, 0, 1.5), (oc.x + 5, -45, 7.4), (oc.x + 4, 0, 1.5), lens=24)
    wave = O["wave"]
    k(wave, "location", a, (-24, 0, 0), "LINEAR")
    hit = b - 22
    k(wave, "location", hit, (7.5, 0, 0), "LINEAR")
    k(wave, "scale", hit, (1, 1, 1), "LINEAR")
    k(wave, "location", b + 6, (11, 0, 1.0), "LINEAR")
    k(wave, "scale", b + 6, (1.05, 1, 1.25), "LINEAR")
    for j in range(5):
        puffs(f"spray{j}", (oc.x + 11, -12 + j * 6, 4.0), hit + j, 6, rnd, (0.95, 0.97, 1.0), spread=3.0, rise=6.0, life=36,
              size=1.6, dense=0.85, ring=False)

    # 6 brain: inside his head -- the skull stops, the brain keeps going and hits the bone
    a, b = S["brain"]
    Bp = BRAIN_AT
    shot(cam, a, b, (Bp.x - 0.38, Bp.y - 7.2, Bp.z - 0.05), (Bp.x - 0.38, Bp.y, Bp.z - 0.62),
         (Bp.x - 0.38, Bp.y - 6.9, Bp.z - 0.05), (Bp.x - 0.38, Bp.y, Bp.z - 0.62), lens=40)
    hd, brn, fl = O["br_head"], O["br_brain"], O["br_flash"]
    stop = a + int(0.52 * (b - a))
    k(hd, "location", a, (-0.45, 0, 0), "LINEAR"), k(hd, "location", stop, (0.0, 0, 0), "LINEAR")
    k(brn, "location", stop, (0, 0, 0.02), "LINEAR"), k(brn, "scale", stop, (1, 1, 1), "LINEAR")
    k(brn, "location", stop + 5, (0.075, 0, 0.02), "LINEAR"), k(brn, "scale", stop + 5, (0.86, 1, 1.05), "LINEAR")
    k(brn, "location", stop + 12, (-0.03, 0, 0.02), "BEZIER"), k(brn, "scale", stop + 12, (1.03, 1, 0.98), "BEZIER")
    k(brn, "location", stop + 22, (0.0, 0, 0.02), "BEZIER"), k(brn, "scale", stop + 22, (1, 1, 1), "BEZIER")
    k(fl, "scale", 0, (0, 0, 0), "CONSTANT"), k(fl, "scale", stop + 4, (1, 1, 1), "LINEAR")
    k(fl, "scale", stop + 12, (0, 0, 0), "LINEAR")

    # 7 time's up: slumped against a car in the street, dizzy stars round his head
    a, b = S["timesup"]
    sit = dict(sh=(-48, 12, 0), el=(-36, 0, 0), hip=(-84, 0, 0), kn=(8, 0, 0), chest=(-16, 0, 0), head=(6, 0, 14))
    R(a, REST_X, -0.25, 0.0, rz=-12)
    R(b - 1, REST_X, -0.25, 0.0, rz=-12)
    pose(P, a, **sit)
    pose(P, a + 50, sh_1=(-48, 12, 0), sh1=(-150, 20, 0), el_1=(-36, 0, 0), el1=(-115, 0, 0), hip=(-86, 0, 0),
         kn=(80, 0, 0), chest=(-14, 0, 0), head=(-4, 0, -10))
    pose(P, b - 2, sh_1=(-48, 12, 0), sh1=(-150, 20, 0), el_1=(-36, 0, 0), el1=(-110, 0, 0), head=(-6, 0, 6))
    shot(cam, a, b, (REST_X + 1.3, -4.8, 1.2), (REST_X + 0.25, 0, 0.12), (REST_X + 1.1, -4.3, 1.15), (REST_X + 0.25, 0, 0.15),
         lens=30)
    dz = O["dizzy"]
    k(dz, "scale", 0, (0, 0, 0), "CONSTANT"), k(dz, "scale", a, (1, 1, 1), "CONSTANT")
    k(dz, "rotation_euler", a, (0, 0, 0), "LINEAR"), k(dz, "rotation_euler", end, (0, 0, math.radians(4 * (end - a))), "LINEAR")
    brows(P, a, -0.003)

    # 8 end: closer on his face as he asks what should stop next
    a, b = S["end"]
    R(a, REST_X, -0.25, 0.0, rz=-12)
    pose(P, a, sh_1=(-48, 12, 0), sh1=(-150, 20, 0), el_1=(-36, 0, 0), el1=(-110, 0, 0), head=(-6, 0, 6))
    pose(P, a + 24, sh=(-52, 14, 0), el=(-50, 0, 0), hip=(-84, 0, 0), kn=(8, 0, 0), chest=(-12, 0, 0), head=(-10, 0, 0))
    shot(cam, a, b, (REST_X + 0.9, -3.9, 1.0), (REST_X + 0.1, 0, 0.5), (REST_X + 0.55, -3.0, 1.0), (REST_X + 0.1, -0.2, 0.62), lens=32)
    brows(P, a, 0.005)
    plant(sc, P, S["timesup"][0], T["frames"])

    # debris, wind streaks: always streaming east past the camera in the street shots
    street_shots = [S[n] for n in ("fling", "street", "wind")]
    cx = {}
    for a_, b_ in street_shots:
        for f in range(a_, b_ + 1, 3):
            sc.frame_set(f)
            cx[f] = cam.matrix_world.translation.x
    keys = sorted(cx)
    def camx(f):
        f3 = min(keys, key=lambda q: abs(q - f))
        return cx[f3]
    for j, o in enumerate(O["streaks"] + O["debris"]):
        is_streak = j < len(O["streaks"])
        y0, z0 = rnd.uniform(-2.5, 3.5), rnd.uniform(0.1, 3.2 if is_streak else 2.6)
        life = rnd.randint(10, 18) if is_streak else rnd.randint(18, 34)
        span = rnd.uniform(9, 14)
        r0 = Vector((rnd.uniform(0, 6), rnd.uniform(0, 6), rnd.uniform(0, 6)))
        spin_ = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))) * (0 if is_streak else 0.5)
        k(o, "location", 0, (0, 0, -50), "CONSTANT")
        for a_, b_ in street_shots:
            f = a_ - rnd.randint(0, life)
            while f < b_:
                for q in (0, life):
                    ff = max(a_, min(b_, f + q))
                    u = (ff - f) / life
                    k(o, "location", ff, (camx(ff) - span / 2 + span * u, y0, z0 + (0 if is_streak else 0.4 * math.sin(u * 6))),
                      "LINEAR")
                    if not is_streak:
                        k(o, "rotation_euler", ff, tuple(r0 + spin_ * (ff - a_)), "LINEAR")
                f += life
            k(o, "location", b_, (0, 0, -50), "CONSTANT")
    lipsync(P, T, 0, T["frames"])


TIMELINES["spin"] = (scene_spin, timeline_spin)
