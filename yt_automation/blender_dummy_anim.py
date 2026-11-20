"""
blender_dummy_anim.py — full timelines for "The Dummy Tests" Shorts, keyed to the narration (dummy_shorts.py voice).

The opening of each (frames 0-48) is the approved pitch opening from blender_pitches.py; every later shot is keyed at
the start time of its line in timing.json, so each shot matches what is being said (LESSONS rule 7).

  /root/.venvs/blender/bin/python blender_dummy_anim.py NAME FRAMES_DIR TIMING.json still F [F ..]
  /root/.venvs/blender/bin/python blender_dummy_anim.py NAME FRAMES_DIR TIMING.json A B
"""
import json
import math
import os
import random
import sys

import bpy  # noqa: I001
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_kit as bk  # noqa: E402
import blender_pitches as bp  # noqa: E402

FPS = 24
EPS = 0.02          # a key this far before a cut holds the old shot, so motion blur never smears across a cut


def F(t):
    return int(round(t * FPS))


def ob(name):
    return bpy.data.objects[name]


def k(o, path, f, value, interp="BEZIER"):
    setattr(o, path, value)
    o.keyframe_insert(path, frame=f)
    if o.animation_data and o.animation_data.action:
        for fc in _curves(o.animation_data.action):
            for kp in fc.keyframe_points:
                if abs(kp.co[0] - f) < 1e-3:
                    kp.interpolation = interp


def _curves(action):
    c = getattr(action, "fcurves", None)
    if c is None:
        c = [fc for layer in action.layers for strip in layer.strips for bag in strip.channelbags for fc in bag.fcurves]
    return c


def shot(cam, f0, f1, loc0, at0, loc1=None, at1=None, lens=None, interp="LINEAR", up=(0, 0, 1)):
    # LINEAR on purpose: Bezier handles next to the near-duplicate keys at a cut overshoot wildly
    """Camera from (loc0 -> at0) at f0 to (loc1 -> at1) at the end of the shot; holds right up to the cut."""
    loc1, at1 = loc1 or loc0, at1 or at0
    for f, loc, at in ((f0, loc0, at0), (f1 - EPS, loc1, at1)):
        bp.aim(cam, Vector(loc), Vector(at), Vector(up))
        k(cam, "location", f, cam.location.copy(), interp)
        k(cam, "rotation_euler", f, cam.rotation_euler.copy(), interp)
        if lens:
            cam.data.lens = lens
            cam.data.keyframe_insert("lens", frame=f)


def show_only(o, f0, f1):
    """Rendered only in [f0, f1)."""
    for f, h in ((0, True), (f0, False), (f1, True)):
        o.hide_render = h
        o.keyframe_insert("hide_render", frame=f)


def pose(P, f, **rots):
    for name, deg in rots.items():
        k(P[name.replace("_", "-") if name.endswith("_1") else name], "rotation_euler", f,
          tuple(math.radians(x) for x in deg))


def dummy_pivots():
    names = ["dummy", "pelvis", "chest", "head"] + [f"{p}{s}" for p in ("sh", "el", "hip", "kn") for s in (-1, 1)]
    P = {n: ob(n) for n in names}
    P["root"] = P["dummy"]
    return P


def copper():
    return bpy.data.materials["copper"]


def mini_penny(name, loc, rot, parent=None):
    c = bp.cylinder(name, 0.0095, 0.0015, loc, copper(), parent, rot=rot, segs=48, bevel=0.0003)
    return c


# ── penny ─────────────────────────────────────────────────────────────────────
def timeline_penny(sc, T):
    st = T["starts"]
    fr = [F(t) for t in st] + [T["frames"]]
    S = dict(zip(T["shots"], zip(fr[:-1], fr[1:])))
    cam, pen, coin = ob("cam"), ob("penny_fall"), ob("penny")
    P = dummy_pivots()
    head_top = Vector((-1.2, 9.0, 2.04))
    sc.render.motion_blur_position = "START"
    # tumbling: keep flipping until the hit
    hit_f = F(st[T["shots"].index("hit")] - 0.32)
    for f in range(52, hit_f + 1, 4):
        k(coin, "rotation_euler", f, (math.radians(40 + f * 11), math.radians(18 + f * 2), math.radians(f * 4)), "LINEAR")

    def pen_on_cam(f):                       # the penny rides just in front of the falling camera
        bpy.context.scene.frame_set(int(f))
        return cam.location + cam.rotation_euler.to_matrix() @ Vector((-0.006, 0.019, -0.088))

    # 1 fall: continue the approved opening down to the cut
    a, b = S["fall"]
    tgt = Vector((-1.2, 9.0, 0.9)) + Vector((0.6, 4.5, 0))
    bp.aim(cam, Vector((-0.3, -2.5, 7.5)), tgt)
    k(cam, "location", b - EPS, Vector((-0.3, -2.5, 7.5)), "LINEAR")
    k(cam, "rotation_euler", b - EPS, cam.rotation_euler.copy(), "LINEAR")
    k(pen, "location", b - EPS, cam.location + cam.rotation_euler.to_matrix() @ Vector((-0.006, 0.019, -0.088)), "LINEAR")
    for f in range(0, b, 6):                 # the dummy waves up at the camera
        pose(P, f, el_1=(-70 + 25 * math.sin(f / 4.0), 0, 0))
    # 2 fall2: from the sidewalk, looking up past the dummy at the tower
    a, b = S["fall2"]
    shot(cam, a, b, (1.4, 11.6, 0.45), (-1.6, 8.7, 2.3), (1.3, 11.4, 0.5), (-1.6, 8.7, 2.6), lens=20)
    k(pen, "location", a, Vector((-1.2, 9.0, 120.0)), "CONSTANT")
    # 3 myth: his point of view, straight up the facade; the penny comes down at him
    a, b = S["myth"]
    shot(cam, a, b, (0.3, 11.2, 1.05), (-1.2, 9.0, 2.0), (0.15, 10.9, 1.1), (-1.2, 9.0, 2.05), lens=28)
    pose(P, a, head=(-42, 0, 0), sh_1=(-12, 18, 0), el_1=(-55, 0, 0), sh1=(-12, -18, 0), el1=(-55, 0, 0))
    pose(P, b - 1, head=(-46, 0, 4), sh_1=(-14, 20, 0), el_1=(-60, 0, 0), sh1=(-14, -20, 0), el1=(-60, 0, 0))
    # 4 flutter: beside the penny, falling with it; air streaks rush up past it
    a, b = S["flutter"]
    for f, z in ((a, 70.0), (b - EPS, 52.0)):
        loc = Vector((1.82, 3.3, z + 0.03))          # facade (windows streaming up) behind the penny
        at = Vector((1.6, 3.3, z))
        bp.aim(cam, loc, at)
        k(cam, "location", f, loc, "LINEAR")
        k(cam, "rotation_euler", f, cam.rotation_euler.copy(), "LINEAR")
        k(pen, "location", f, Vector((1.6, 3.3, z)), "LINEAR")
    cam.data.lens = 50
    cam.data.keyframe_insert("lens", frame=a)
    cam.data.keyframe_insert("lens", frame=b - EPS)
    # 5 terminal: falling with it toward his head; it leaves the camera and lands on him
    a, b = S["terminal"]
    for f, z in ((a, 14.0), (hit_f - 10, 3.1), (hit_f, 2.7), (b - EPS, 2.65)):
        loc = Vector((-0.9, 7.6, z))
        bp.aim(cam, loc, head_top + Vector((0.0, 0.08 * min(1.0, (z - 2.6) / 4.0), 0)), Vector((0, 1, 0)))
        k(cam, "location", f, loc, "LINEAR")
        k(cam, "rotation_euler", f, cam.rotation_euler.copy(), "LINEAR")
    cam.data.lens = 24
    cam.data.keyframe_insert("lens", frame=a)
    cam.data.keyframe_insert("lens", frame=b - EPS)
    k(pen, "location", a, pen_on_cam(a), "LINEAR")
    k(pen, "location", hit_f - 10, pen_on_cam(hit_f - 10), "LINEAR")
    k(pen, "location", hit_f, head_top + Vector((0.02, -0.03, 0.005)), "LINEAR")
    # bounce off his head, land on the sidewalk
    land = Vector((-0.8, 10.02, 0.13))           # in front of his feet, by the low camera
    k(pen, "location", hit_f + 6, head_top + Vector((0.25, -0.15, 0.32)), "BEZIER")
    k(pen, "location", hit_f + 16, land + Vector((0, 0, 0.004)), "BEZIER")
    k(pen, "location", hit_f + 20, land + Vector((0.03, -0.02, 0.06)), "BEZIER")
    k(pen, "location", hit_f + 26, land, "CONSTANT")
    k(coin, "rotation_euler", hit_f + 26, (0, 0, math.radians(30)), "CONSTANT")
    # dummy: looks up the whole fall; jolts at the hit, hand to head, then rubs it
    pose(P, a, head=(-40, 0, 0), sh_1=(-150, -25, 0), el_1=(-70, 0, 0))
    pose(P, hit_f, head=(-40, 0, 0), chest=(0, 0, 0))
    pose(P, hit_f + 3, head=(-5, 0, 6), chest=(10, 0, 0))
    pose(P, hit_f + 5, sh_1=(-150, -25, 0), el_1=(-70, 0, 0))
    pose(P, hit_f + 12, sh_1=(-165, -10, 0), el_1=(-115, 0, 0), head=(12, 0, 4))
    # 6 hit: close on his head as the penny flips away
    a, b = S["hit"]
    shot(cam, a, b, (-0.1, 10.6, 1.9), (-1.15, 9.0, 1.9), (-0.15, 10.5, 1.88), (-1.1, 9.0, 1.85), lens=40)
    # 7 after: rubbing his head, looking at the penny on the ground
    a, b = S["after"]
    shot(cam, a, b, (0.35, 11.7, 1.35), (-1.15, 9.0, 1.4), (0.25, 11.5, 1.35), (-1.15, 9.0, 1.42), lens=30)
    for f in range(a, b, 6):
        pose(P, f, el_1=(-115 + 18 * math.sin(f / 2.5), 0, 0))
    pose(P, a, head=(25, 0, -18), chest=(6, 0, -6))
    # 8 roof: a setback roof along the same tower, pennies piled up; a new one drifts onto it
    a, b = S["roof"]
    stone = bpy.data.materials["stone"]
    roofm = bp.mat("roof", (0.2, 0.2, 0.22), rough=0.8)
    terrace = bp.box("terrace", (6.0, 10.0, 0.3), (0.0, -30.0, 21.85), roofm)
    bp.box("parapet", (0.25, 10.0, 0.9), (2.9, -30.0, 22.4), stone)
    rnd = random.Random(8)
    for j in range(260):                             # a heap of pennies on the roof
        r, ang = 0.3 * rnd.random() ** 0.7, rnd.uniform(0, 2 * math.pi)
        mini_penny(f"roofcoin{j}", (-0.6 + r * math.cos(ang), -30.0 + r * math.sin(ang),
                                    22.0 + 0.004 + (0.3 - r) * 0.22 + rnd.uniform(0, 0.012)),
                   (rnd.uniform(-0.5, 0.5), rnd.uniform(-0.5, 0.5), rnd.uniform(0, 6)))
    drift = pen
    shot(cam, a, b, (11.0, -40.0, 30.0), (-1.5, -30.0, 18.0), (1.1, -31.1, 22.75), (-0.6, -30.0, 22.05), lens=24)
    k(drift, "location", a, Vector((2.6, -29.6, 25.4)), "LINEAR")
    k(drift, "location", a + int((b - a) * 0.55), Vector((0.4, -29.9, 22.6)), "BEZIER")
    k(drift, "location", a + int((b - a) * 0.7), Vector((-0.35, -29.95, 22.06)), "CONSTANT")
    for f in range(a, a + int((b - a) * 0.7), 4):
        k(coin, "rotation_euler", f, (math.radians(f * 13), math.radians(30), 0), "LINEAR")
    k(coin, "rotation_euler", a + int((b - a) * 0.7), (math.radians(8), 0, 0), "CONSTANT")
    upd = bp.mat("updraft", (0.95, 0.97, 1.0), rough=0.3, alpha=0.22)
    for j in range(40):                              # the updraft along the wall
        s_ = bp.cylinder(f"upd{j}", 0.004, rnd.uniform(0.4, 1.0), (rnd.uniform(0.8, 3.0), rnd.uniform(-31.5, -28.5),
                         rnd.uniform(22.3, 26.0)), upd, segs=6, rot=(0, math.radians(-12), 0))
        for f, dz in ((a, 0.0), (b, 3.0)):
            s_.location.z += dz if f == b else 0
            s_.keyframe_insert("location", frame=f)
        show_only(s_, a, b)
    # 9 end: back on the street, he holds the penny up to us
    a, b = S["end"]
    shot(cam, a, b, (-0.9, 11.6, 1.5), (-1.2, 9.0, 1.45), (-0.95, 11.3, 1.5), (-1.2, 9.0, 1.45), lens=30)
    pose(P, a - 1, sh1=(0, 8, 0), el1=(0, 0, 0), sh_1=(-165, -10, 0), el_1=(-100, 0, 0))
    pose(P, a, sh1=(-10, -35, 0), el1=(-85, 0, 0), sh_1=(-10, 35, 0), el_1=(-85, 0, 0), head=(-4, 0, 0),
         chest=(0, 0, 0))                                  # the shrug: "so... what next?"
    pose(P, b - 1, sh1=(-12, -40, 0), el1=(-90, 0, 0), sh_1=(-12, 40, 0), el_1=(-90, 0, 0), head=(-4, 0, 10))


# ── hail ──────────────────────────────────────────────────────────────────────
R_CAN, H_CAN = 0.58, 0.2


def canopy_point(up, x, y):
    t = min(1.0, Vector((x, y)).length / R_CAN)
    return up.matrix_world @ Vector((x, y, H_CAN * (1 - t ** 1.6) - 0.03 * t ** 3 + 0.62 + 0.012))


def extra_canopy(up, red, hole_at=None, hole_r=0.0):
    """Another canopy (and flaps) on the same umbrella; the duplicate shaft/ribs it makes are removed."""
    before = set(bpy.data.objects.keys())
    can, flaps = bp.umbrella(up, red, hole_at=hole_at, hole_r=hole_r)
    for n in set(bpy.data.objects.keys()) - before:
        if n.split(".")[0] in ("shaft", "handle") or n.startswith("rib"):
            bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
    return [can] + flaps


def visible(objs, spans, end):
    """Rendered only inside the [f0, f1) spans."""
    for o in objs:
        o.hide_render = True
        o.keyframe_insert("hide_render", frame=0)
        for f0, f1 in spans:
            o.hide_render = False
            o.keyframe_insert("hide_render", frame=f0)
            o.hide_render = True
            o.keyframe_insert("hide_render", frame=f1)


def fly(o, path_pts, f0, step=1, interp="LINEAR"):
    for j, p in enumerate(path_pts):
        k(o, "location", f0 + j * step, p, interp)


def bounce_path(p_hit, out_dir, speed_out, speed_up, frames=14, ground=0.02, r=0.01):
    pts, v = [], Vector((out_dir.x * speed_out, out_dir.y * speed_out, speed_up))
    for j in range(1, frames + 1):
        t = j / FPS
        q = p_hit + v * t + Vector((0, 0, -4.9 * t * t))
        q.z = max(q.z, ground + r)
        pts.append(q)
    return pts


def timeline_hail(sc, T):
    st = T["starts"]
    fr = [F(t) for t in st] + [T["frames"]]
    S = dict(zip(T["shots"], zip(fr[:-1], fr[1:])))
    end = T["frames"] + 2
    sc.render.motion_blur_position = "START"
    cam, stone, up = ob("cam"), ob("stone"), ob("umb")
    P = dummy_pivots()
    red = bpy.data.materials["canopy_red"]
    ice = bpy.data.materials["ice"]
    canA = [ob("canopy")] + [ob(f"flap{j}") for j in range(6)]
    # rain that keeps falling: a rig of drops that slides down and wraps every 12 frames
    for o in [o for o in bpy.data.objects if o.name.startswith("rain")]:
        bpy.data.objects.remove(o, do_unlink=True)
    rig = bp.pivot("rain_rig", (0, 0, 0))
    rain = bpy.data.materials["rain"]
    rnd = random.Random(21)
    for j in range(300):
        x, y, z = rnd.uniform(-2.8, 3.2), rnd.uniform(-2.6, 6.0), rnd.uniform(0.0, 3.6)
        L = rnd.uniform(0.12, 0.3)
        for dz in (0.0, 3.6):
            bp.cylinder(f"drop{j}_{int(dz)}", 0.0012, L, (x, y, z + dz), rain, rig, rot=(math.radians(6), 0, 0), segs=6)
    f = 0
    while f < end:
        k(rig, "location", f, Vector((0, 0, 0)), "LINEAR")
        k(rig, "location", f + 12 - EPS, Vector((0, 0, -3.6)), "CONSTANT")
        f += 12
    # chips from the opening come down to the ground instead of hanging in the air
    for j in range(26):
        c = ob(f"chip{j}")
        q = c.location.copy()
        sc.frame_set(12 if j < 12 else 17)
        q = c.location.copy()
        q.z = 0.012
        k(c, "location", 20 if j < 12 else 24, q, "LINEAR")
    # 1 impact: the approved opening; hold the last framing to the cut
    a, b = S["impact"]
    sc.frame_set(48)
    k(cam, "location", b - EPS, cam.location.copy(), "LINEAR")
    k(cam, "rotation_euler", b - EPS, cam.rotation_euler.copy(), "LINEAR")
    # 2 close-up: the stone on the wet street, a ruler beside it
    a, b = S["closeup"]
    rest = Vector((0.69, -0.5, 0.1))
    shot(cam, a, b, (1.22, -1.08, 0.24), (0.66, -0.45, 0.1), (1.12, -0.98, 0.22), (0.68, -0.48, 0.1), lens=35)
    rul = bk.ruler("ruler", 0.3, 0.035, (0.79, -0.61, 0.003))          # in front of the stone, square to camera
    rul.rotation_euler = (0, 0, math.radians(41.6))
    visible([rul], [(a, b)], end)
    # 3 reset: a fresh umbrella (the torn one is gone)
    a, b = S["reset"]
    shot(cam, a, b, (1.0, -3.3, 1.0), (0.2, -0.35, 1.25), (0.95, -3.1, 1.02), (0.2, -0.35, 1.3), lens=24)
    pose(P, a, chest=(0, 0, 0), head=(0, 0, 0), sh_1=(0, 0, 0), el_1=(0, 0, 0))
    canB = extra_canopy(up, red)
    sc.frame_set(S["pea"][0])
    centre = canopy_point(up, 0, 0)
    # 4 pea: little stones bounce off the canopy
    a, b = S["pea"]
    shot(cam, a, b, centre + Vector((0.95, -1.45, 0.28)), centre + Vector((0.0, 0.0, -0.32)),
         centre + Vector((0.9, -1.38, 0.27)), centre + Vector((0.0, 0.0, -0.32)), lens=30)
    for j in range(60):
        r, ang = rnd.uniform(0.05, 0.5), rnd.uniform(0, 2 * math.pi)
        p = canopy_point(up, r * math.cos(ang), r * math.sin(ang))
        fh = a + 4 + int((b - a - 14) * j / 60) + rnd.randint(0, 3)
        pea = bp.lumpy(f"pea{j}", 0.0065, p, ice, seed=200 + j, amp=0.3)
        pea.modifiers["lumps"].strength *= 0.6
        out = Vector((math.cos(ang), math.sin(ang), 0))
        fly(pea, [p + Vector((0, 0, 1.4)), p], fh - 3, step=3)
        fly(pea, bounce_path(p, out, 1.3, 1.6, 16, r=0.0065), fh + 1)
        visible([pea], [(fh - 3, end)], end)
    # 5 golf: heavier thumps; the canopy shudders, he flinches
    a, b = S["golf"]
    shot(cam, a, b, centre + Vector((0.85, -1.3, 0.22)), centre + Vector((0.0, 0.0, -0.3)),
         centre + Vector((0.8, -1.22, 0.2)), centre + Vector((0.0, 0.0, -0.3)), lens=30)
    base = up.rotation_euler.copy()
    k(up, "rotation_euler", a, base)
    for j, (x, y) in enumerate(((0.22, -0.1), (-0.15, -0.2), (0.05, 0.25), (-0.3, 0.05), (0.32, 0.18))):
        p = canopy_point(up, x, y)
        fh = a + 6 + j * 10
        g = bp.lumpy(f"golf{j}", 0.021, p, ice, seed=300 + j, amp=0.3)
        fly(g, [p + Vector((0, 0, 1.6)), p], fh - 2, step=2)
        out = Vector((x, y, 0)).normalized()
        fly(g, bounce_path(p, out, 1.6, 2.2, 16, r=0.021), fh + 1)
        visible([g], [(fh - 2, end)], end)
        k(up, "rotation_euler", fh, base)
        k(up, "rotation_euler", fh + 2, (base.x + math.radians(4 if j % 2 else -4), base.y, base.z))
        k(up, "rotation_euler", fh + 6, base)
        pose(P, fh, head=(0, 0, 0))
        pose(P, fh + 2, head=(14, 0, -10))
        pose(P, fh + 7, head=(0, 0, 0))
    # 6 baseball: two bounce hard, the third tears straight through
    a, b = S["baseball"]
    shot(cam, a, b, (0.8, -1.95, 1.3), (0.2, -0.4, 1.95), (0.76, -1.85, 1.3), (0.2, -0.4, 1.95), lens=24)
    tear = (0.12, -0.3)                                       # on the side facing the camera
    canC = extra_canopy(up, red, hole_at=tear, hole_r=0.09)
    tear_f = a + 8 + 2 * 14
    for j, (x, y) in enumerate(((0.25, -0.2), (-0.28, 0.15), tear)):
        p = canopy_point(up, x, y)
        fh = a + 8 + j * 14
        bb = bp.lumpy(f"baseball{j}", 0.036, p, ice, seed=400 + j, amp=0.3)
        fly(bb, [p + Vector((0, 0, 2.0)), p], fh - 2, step=2)
        if j < 2:
            fly(bb, bounce_path(p, Vector((x, y, 0)).normalized(), 2.0, 2.4, 16, r=0.036), fh + 1)
        else:                                          # through the fabric and onto the street by his feet
            g = Vector((p.x - 0.1, p.y - 0.25, 0.04))
            fly(bb, [p + (g - p) * 0.5, g, g + Vector((0.08, -0.05, 0.08)), g + Vector((0.14, -0.1, 0.0))], fh + 1, step=2)
        visible([bb], [(fh - 2, end)], end)
    pose(P, tear_f, head=(0, 0, 0), sh_1=(0, 0, 0), el_1=(0, 0, 0), chest=(0, 0, 0))
    pose(P, tear_f + 3, head=(18, 0, -22), sh_1=(-95, -30, 0), el_1=(-110, 0, 0), chest=(8, 0, 6))
    pose(P, b - 1, head=(10, 0, -12), sh_1=(-60, -20, 0), el_1=(-80, 0, 0), chest=(4, 0, 2))
    # 7 record: slow-motion replay of the opening punch-through
    a, b = S["record"]
    shot(cam, a, b, (0.62, -1.55, 1.6), (0.24, -0.32, 2.02), (0.55, -1.35, 1.65), (0.24, -0.32, 2.0), lens=24)
    pose(P, a, head=(0, 0, 0), sh_1=(0, 0, 0), el_1=(0, 0, 0), chest=(0, 0, 0))
    sc.frame_set(a)
    hole_w = canopy_point(up, 0.17, -0.12)
    k(stone, "location", a - EPS, rest, "CONSTANT")
    k(stone, "location", a, hole_w + Vector((0, 0, 0.04)), "LINEAR")
    k(stone, "location", b - EPS, hole_w + Vector((0.02, -0.02, -0.2)), "CONSTANT")
    k(stone, "location", b, rest, "CONSTANT")
    k(stone, "rotation_euler", a, (0.3, 0.2, 0), "LINEAR")
    k(stone, "rotation_euler", b - EPS, (0.45, 0.3, 0.1), "CONSTANT")
    for j in range(12):                                # chips drift out of the hole in slow motion
        c = ob(f"chip{j}")
        d = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.6, 0.5))).normalized()
        k(c, "location", a - EPS, Vector((c.location.x, c.location.y, 0.012)), "CONSTANT")
        k(c, "location", a, hole_w + d * 0.06, "LINEAR")
        k(c, "location", b - EPS, hole_w + d * rnd.uniform(0.25, 0.45), "CONSTANT")
        k(c, "location", b, Vector((hole_w.x + d.x * 0.6, hole_w.y + d.y * 0.6, 0.012)), "CONSTANT")
    # 8 lookup: he stares up through the holes
    a, b = S["lookup"]
    shot(cam, a, b, (0.75, -2.3, 1.15), (0.2, -0.3, 1.75), (0.7, -2.15, 1.15), (0.2, -0.3, 1.78), lens=24)
    pose(P, a, head=(-38, 0, -8), chest=(-4, 0, 0), sh_1=(0, 0, 0), el_1=(0, 0, 0))
    pose(P, b - 1, head=(-42, 0, -10))
    # 9 end: the shrug, umbrella still up
    a, b = S["end"]
    shot(cam, a, b, (0.9, -3.0, 1.2), (0.1, -0.3, 1.4), (0.85, -2.85, 1.2), (0.1, -0.3, 1.42), lens=26)
    pose(P, a, head=(-4, 0, 6), chest=(0, 0, 0), sh_1=(-10, 35, 0), el_1=(-85, 0, 0))
    pose(P, b - 1, head=(-4, 0, 10), sh_1=(-12, 40, 0), el_1=(-90, 0, 0))
    # which canopy is up when
    pea0, base0, rec0 = S["reset"][0], S["baseball"][0], S["record"][0]
    visible(canA, [(0, pea0), (rec0, end)], end)
    visible(canB, [(pea0, tear_f)], end)
    visible(canC, [(tear_f, rec0)], end)


# ── quicksand ────────────────────────────────────────────────────────────────
def timeline_quicksand(sc, T):
    st = T["starts"]
    fr = [F(t) for t in st] + [T["frames"]]
    S = dict(zip(T["shots"], zip(fr[:-1], fr[1:])))
    end = T["frames"] + 2
    sc.render.motion_blur_position = "START"
    cam = ob("cam")
    P = dummy_pivots()
    root = P["root"]
    # ripples keep spreading the whole video
    nt = bpy.data.materials["quicksand"].node_tree
    wave = [n for n in nt.nodes if n.bl_idname == "ShaderNodeTexWave"][0]
    wave.inputs["Phase Offset"].default_value = -9.0 * end / 48
    wave.inputs["Phase Offset"].keyframe_insert("default_value", frame=end)
    for fc in _curves(nt.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
    z = lambda f, v, i="BEZIER": k(root, "location", f, Vector((0, 0, v)), i)
    flail = [dict(sh_1=(-165, -35, 0), el_1=(-20, 0, 0), sh1=(-160, 35, 0), el1=(-25, 0, 0)),
             dict(sh_1=(-150, -45, 0), el_1=(-35, 0, 0), sh1=(-170, 25, 0), el1=(-15, 0, 0))]
    spread = dict(sh_1=(-10, 63, 0), el_1=(-8, 0, 0), sh1=(-10, -63, 0), el1=(-8, 0, 0))
    # 1 sink: the approved opening; hold to the cut
    a, b = S["sink"]
    sc.frame_set(48)
    k(cam, "location", b - EPS, cam.location.copy() + Vector((0.05, 0.15, -0.02)), "LINEAR")
    k(cam, "rotation_euler", b - EPS, cam.rotation_euler.copy(), "LINEAR")
    # 2 the movie version: he goes down to his chest, flailing
    a, b = S["sink2"]
    shot(cam, a, b, (0.55, -1.6, 0.25), (0.0, 0.0, 0.55), (0.5, -1.45, 0.22), (0.0, 0.0, 0.45), lens=24)
    z(a, -1.055), z(a + 18, -1.3), z(a + 40, -1.45), z(b - 1, -1.47)
    for j, f in enumerate(range(a, b, 8)):
        pose(P, f, head=(-25 if j % 2 else 20, 0, 12 if j % 2 else -12), **flail[j % 2])
    # 3 density: he pops back up to the waist and floats
    a, b = S["density"]
    shot(cam, a, b, (1.6, -2.2, 0.6), (0.0, 0.0, 0.4), (1.5, -2.05, 0.58), (0.0, 0.0, 0.42), lens=30)
    z(a + 12, -0.98), z(a + 26, -1.07), z(a + 44, -1.04), z(b - 1, -1.05)
    pose(P, a + 4, head=(10, 0, 0), **flail[0])
    pose(P, a + 30, head=(0, 0, -6), **spread)
    # 4 float: at the surface line, a gentle bob
    a, b = S["float"]
    shot(cam, a, b, (0.9, -2.0, 0.12), (0.0, 0.0, 0.3), (0.85, -1.85, 0.12), (0.0, 0.0, 0.3), lens=28)
    for j, f in enumerate(range(a, b, 14)):
        z(f, -1.05 + (0.012 if j % 2 else -0.008))
    pose(P, a, head=(-6, 0, 8), **spread)
    # 5 pull: straining to lift a leg; barely moves
    a, b = S["pull"]
    shot(cam, a, b, (0.6, -1.3, 0.6), (0.0, 0.0, 0.35), (0.55, -1.2, 0.58), (0.0, 0.0, 0.35), lens=30)
    push = dict(sh_1=(-25, 50, 0), el_1=(-25, 0, 0), sh1=(-25, -50, 0), el1=(-25, 0, 0))
    pose(P, a, head=(25, 0, 0), chest=(18, 0, 0), **push)
    for j, f in enumerate(range(a + 6, b, 5)):                      # the strain: tiny shakes
        pose(P, f, chest=(18 + (2 if j % 2 else -2), 0, (1.5 if j % 2 else -1.5)))
    z(a + 30, -1.0), z(a + 60, -1.08), z(a + 90, -1.01), z(b - 1, -1.06)
    # 6 wiggle: slow side-to-side, rising a little
    a, b = S["wiggle"]
    shot(cam, a, b, (0.2, -2.4, 0.7), (0.0, 0.0, 0.45), (0.2, -2.25, 0.68), (0.0, 0.0, 0.48), lens=28)
    pose(P, a, head=(0, 0, 0), **spread)
    for j, f in enumerate(range(a, b, 12)):
        pose(P, f, chest=(4, 0, 12 if j % 2 else -12))
    z(a, -1.06), z(b - 1, -0.9, "LINEAR")
    # 7 tide: the sea creeps in over the sand
    a, b = S["tide"]
    shot(cam, a, b, (2.4, -4.4, 1.7), (0.0, 1.0, 0.25), (2.2, -4.0, 1.5), (0.0, 0.8, 0.25), lens=24)
    water = bp.box("sea", (60, 60, 0.1), (0, 40, -0.2), bp.add_bump(
        bp.mat("sea", (0.08, 0.3, 0.34), rough=0.06, transmission=0.55, ior=1.33), 6, 0.25, distance=0.02))
    k(water, "location", 0, Vector((0, 40, -0.2)), "CONSTANT")
    k(water, "location", a, Vector((0, 36.0, 0.0)), "LINEAR")
    k(water, "location", b - 1, Vector((0, 26.0, 0.22)), "LINEAR")
    k(water, "location", end, Vector((0, 25.0, 0.26)), "LINEAR")
    z(a, -0.9)
    pose(P, a, head=(0, 0, 0), chest=(0, 0, 0), **spread)
    pose(P, a + 14, head=(-10, 0, 55), sh_1=(-150, -30, 0), el_1=(-20, 0, 0), sh1=(-150, 30, 0), el1=(-20, 0, 0))
    pose(P, b - 1, head=(-5, 0, 40))
    # 8 resigned
    a, b = S["resigned"]
    shot(cam, a, b, (0.4, -1.5, 0.85), (0.0, 0.0, 0.7), (0.38, -1.42, 0.84), (0.0, 0.0, 0.7), lens=30)
    pose(P, a, head=(18, 0, 12), chest=(12, 0, 0), sh_1=(-45, -25, 0), el_1=(-110, 0, 0), sh1=(-45, 25, 0),
         el1=(-110, 0, 0))
    pose(P, b - 1, head=(20, 0, 14))
    # 9 end: the shrug
    a, b = S["end"]
    shot(cam, a, b, (0.6, -2.2, 0.75), (0.0, 0.0, 0.6), (0.58, -2.05, 0.74), (0.0, 0.0, 0.62), lens=28)
    pose(P, a, head=(-4, 0, 8), chest=(0, 0, 0), sh_1=(-10, 35, 0), el_1=(-85, 0, 0), sh1=(-10, -35, 0),
         el1=(-85, 0, 0))
    pose(P, b - 1, head=(-4, 0, 12), sh_1=(-12, 40, 0), el_1=(-90, 0, 0), sh1=(-12, -40, 0), el1=(-90, 0, 0))



# ── 4. lightning (Dummy Test #4; approved opening A, upgraded dummy v2) ─────────
def timeline_lightning(sc, T):
    import blender_lightning as bl
    st = T["starts"]
    fr = [F(t) for t in st] + [T["frames"]]
    fr[0] = 0
    S = dict(zip(T["shots"], zip(fr[:-1], fr[1:])))
    end = T["frames"] + 2
    sc.render.motion_blur_position = "START"
    cd = bpy.data.cameras.new("cam")
    cd.sensor_fit, cd.sensor_height, cd.clip_start = "VERTICAL", 24.0, 0.02
    cam = bpy.data.objects.new("cam", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    O, P, pose = bl.O, bl.O["P"], bl.pose
    radio = O["radio"].data.materials[0].node_tree.nodes["Emission"].inputs["Strength"]
    cluster = O["cluster"].data.materials[0].node_tree.nodes["Emission"].inputs["Strength"]
    A_LOC, A_AIM = (-0.4, -1.75, 1.78), (-0.4, 0.3, 1.42)

    # 1 strike: the approved opening -- the bolt slams the roof above him at frame 0, his arms fly up
    a, b = S["strike"]
    shot(cam, a, b, A_LOC, A_AIM, (-0.4, -1.52, 1.75), A_AIM, lens=30)
    bl.opening_poses(P, 0)
    bl.strike(0)
    bl._keys(radio, "default_value", ((0, 4), (2, 0)))
    # 2 myth: the tire, close
    a, b = S["myth"]
    shot(cam, a, b, (-1.75, -2.6, 0.45), (-0.88, -1.35, 0.36), (-1.62, -2.38, 0.42), (-0.88, -1.35, 0.36), lens=32)
    pose(P, a, sh=(-85, 12, 0), el=(-60, 0, 0), head=(10, 0, 10), chest=(2, 0, 0))
    # 3 jump: the strike again; the current jumps past the tire into the puddle
    a, b = S["jump"]
    shot(cam, a, b, (-3.0, -3.1, 0.5), (-0.95, -1.25, 0.6), (-2.75, -2.85, 0.55), (-0.95, -1.25, 0.65), lens=22)
    bl.strike(a + 8, arc_frames=6, sparks=True)
    bl.flicker(O["arcs"][:1], a + 14, a + 44)
    bl.O.setdefault("puddle_keys", []).extend([(a + 14, 3500), (a + 30, 3000), (a + 44, 2500), (a + 47, 0)])
    pose(P, a, **bl.SEATED)
    # 4 shell: the current races over the outside, into the ground; inside he is untouched
    a, b = S["shell"]
    shot(cam, a, b, (-4.3, -1.0, 2.4), (-0.3, 0.15, 0.95), (-3.95, -0.75, 2.25), (-0.3, 0.2, 1.0), lens=30)
    bl.flicker(O["crawl"], a + 4, b)
    bl.flicker(O["arcs"], a + 10, b)
    glow = O["glow"].data
    bl._keys(glow, "energy", [(a - 1, 0)] + [(f, 700 if (f // 3) % 2 else 380) for f in range(a + 4, b - 2, 3)] +
             [(b - 1, 0)])
    pose(P, a, **bl.SEATED)
    pose(P, a + 30, head=(4, 0, -22))
    pose(P, b - 1, head=(6, 0, -30))
    # 5 damage: the tire blows, then the dash fries
    a, b = S["damage"]
    mid = a + (b - a) // 2
    shot(cam, a, mid, (-1.55, -2.35, 0.32), (-0.88, -1.35, 0.3), (-1.5, -2.25, 0.31), (-0.88, -1.35, 0.28), lens=30)
    shot(cam, mid, b, (0.25, -0.05, 1.32), (-0.3, -0.6, 1.05), (0.22, -0.1, 1.3), (-0.3, -0.6, 1.05), lens=26)
    tire, hub, car = O["tire-1-1.35"], O["hub-1-1.35"], O["car"]
    bl._keys(tire, "scale", ((a + 9, (1, 1, 1)), (a + 11, (0.6, 1.12, 1.06))))
    bl._keys(tire, "location", ((a + 9, (-0.88, -1.35, 0.34)), (a + 11, (-0.88, -1.35, 0.205))))
    bl._keys(hub, "location", ((a + 9, (-0.88, -1.35, 0.34)), (a + 11, (-0.88, -1.35, 0.24))))
    bl._keys(car, "rotation_euler", ((a + 9, (0, 0, 0)), (a + 13, (math.radians(2.0), math.radians(-2.0), 0))))
    bl.burst("shred", (-1.06, -1.5, 0.12), a + 10, 12, speed=2.6, up=(0.4, 1.8), mat=O["shred_m"], size=0.018,
             life=16)
    bl._keys(cluster, "default_value", ((mid + 5, 3), (mid + 6, 9), (mid + 7, 0), (mid + 8, 6), (mid + 9, 0)))
    bl.burst("dashspk", (-0.2, -0.64, 1.08), mid + 6, 14, speed=0.8, up=(0.3, 1.2), size=0.008, life=14)
    pose(P, mid + 5, head=(6, 0, -10), chest=(2, 0, 0))
    pose(P, mid + 9, head=(16, 0, 0), chest=(7, 0, 0))
    # 6 radio: "...My radio's dead." -- he taps it
    a, b = S["radio"]
    shot(cam, a, b, (0.5, -0.95, 1.38), (-0.18, -0.12, 1.18), (0.48, -0.9, 1.37), (-0.18, -0.12, 1.18), lens=22)
    pose(P, a, sh1=(-75, -10, 0), el1=(-15, 0, 0), head=(-18, 0, 25), chest=(0, 0, 6),
         **{"sh-1": (-62, 0, 0), "el-1": (-28, 0, 0)})
    for j, f in enumerate(range(a + 4, b - 2, 6)):
        pose(P, f, el1=((-25, 0, 0) if j % 2 == 0 else (-12, 0, 0)))
    # 7 convertible: no metal roof -- the sky goes white and we cut
    a, b = S["convertible"]
    shot(cam, a, b, (-0.4, -2.45, 2.3), (-0.4, 0.3, 1.6), (-0.4, -2.2, 2.2), (-0.4, 0.3, 1.6), lens=30)
    for o in O["roof_parts"]:
        bl.HIDE.setdefault(o, set()).update(range(a, b))
    bl.on(O["lowshield"], range(a, b)), bl.on(O["folded"], range(a, b))
    col = O["paint"].node_tree.nodes["Principled BSDF"].inputs["Base Color"]
    bl._keys(col, "default_value", ((a - 1, (0.02, 0.07, 0.17, 1)), (a, (0.32, 0.015, 0.012, 1)),
                                    (b - 1, (0.32, 0.015, 0.012, 1)), (b, (0.02, 0.07, 0.17, 1))))
    for fc in _curves(O["paint"].node_tree.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "CONSTANT"
    bl.on(O["far"][0], {a + 22, a + 23, a + 25})
    O.setdefault("sky_keys", []).extend([(a + 21, 0.5), (a + 22, 1.6), (a + 24, 0.6), (a + 25, 1.3), (a + 28, 0.5),
                                         (b - 5, 0.5), (b - 3, 9.0), (b - 1, 14.0), (b, 0.5)])
    O.setdefault("flash_keys", []).extend([(b - 4, 0), (b - 3, 30000), (b - 1, 45000), (b, 0)])
    pose(P, a, **bl.SEATED)
    pose(P, a + 8, head=(24, 0, 0))
    pose(P, a + 34, head=(32, 0, -14))
    pose(P, b - 6, sh=(-105, 8, 0), el=(-65, 0, 0), head=(34, 0, -6))
    # 8 end: back in the hard top, just before the strike; ends exactly on frame 0's framing (the loop)
    a, b = S["end"]
    shot(cam, a, b, (-0.4, -2.05, 1.83), A_AIM, A_LOC, A_AIM, lens=30)
    pose(P, a, **bl.SEATED)
    pose(P, b - 1, **bl.SEATED)
    O.setdefault("sky_keys", []).extend([(a + 40, 0.5), (a + 41, 1.1), (a + 43, 0.5)])
    bl.finalize(end)

def timeline_sinking(sc, T):
    """Dummy Test #5: his car goes into a river; a clock (drawn in compose) runs from 1:00 to 0:03."""
    import blender_lightning as bl
    import blender_sinking as bs
    st = T["starts"]
    fr = [F(t) for t in st] + [T["frames"]]
    fr[0] = 0
    S = dict(zip(T["shots"], zip(fr[:-1], fr[1:])))
    end = T["frames"] + 2
    sc.render.motion_blur_position = "START"
    O, P, pose = bl.O, bl.O["P"], bl.pose
    car = O["car"]
    bs.story_props()

    def mkcam(name, parent=None):
        cd = bpy.data.cameras.new(name)
        cd.sensor_fit, cd.sensor_height, cd.clip_start = "VERTICAL", 24.0, 0.01
        c = bpy.data.objects.new(name, cd)
        sc.collection.objects.link(c)
        c.parent = parent
        return c
    cam_w, cam_c = mkcam("cam_world"), mkcam("cam_car", car)

    def use(cam, f):
        m = sc.timeline_markers.new(cam.name, frame=f)
        m.camera = cam
    split = O["river_mat"].node_tree.nodes["split"].outputs[0]

    def split_key(f, v):
        split.default_value = v
        split.keyframe_insert("default_value", frame=f)

    def split_on(f0, f1):
        for f, v in ((f0 - 1, 0.0), (f0, 1.0), (f1 - 1, 1.0), (f1, 0.0)):
            split_key(f, v)
    split_key(0, 0.0)

    # the car keeps sinking through the whole Short (pitch > 0 = nose down)
    L = -bs.LEAD
    keys = [(f + L, *rest) for f, *rest in bs.OPENING_MOTION[:-1]]
    a92 = S["phone"][0]
    keys += [(a92, -0.45, 36, 0, -0.66), (S["door"][0], -0.6, 30, 0, -0.68), (S["window"][0], -0.72, 28, -1, -0.69),
             (S["stuck"][0], -0.86, 25, 0, -0.7), (S["out"][0], -0.98, 22, 0, -0.7), (S["surface"][0], -1.08, 20, 0, -0.7),
             (S["end"][0], -1.9, 18, 0, -0.7), (end, -2.6, 15, 0, -0.7)]
    bs.car_motion(keys)
    B_LOC, B_AIM = (-0.42, -3.6, 0.42), (-0.42, -0.9, 0.75)

    # 1 plunge: the approved opening B
    a, b = S["plunge"]
    use(cam_w, a)
    shot(cam_w, a, b, B_LOC, B_AIM, (-0.42, -3.35, 0.4), (-0.42, -0.9, 0.62), lens=22)
    bs.opening_poses(P, L)
    bs.splash(L, (0.0, -2.2, 0.05))
    bs.splash(L + 2, (-0.95, -1.4, 0.05), n=60, speed=1.6, up=(1.0, 3.0))
    bs.splash(L + 2, (0.95, -1.4, 0.05), n=60, speed=1.6, up=(1.0, 3.0))
    bs.foam_ring(L, b)
    bs.gush(0, S["window"][0])
    bl.on(O["belt"][0], range(0, S["window"][0] + 14)), bl.on(O["belt"][1], range(0, S["window"][0] + 14))

    # 2 phone: MISTAKE 1 -- he dials while the river comes in around his knees
    a, b = S["phone"]
    use(cam_w, a)                                              # through the windshield: the river is at the dash
    # low, so the sight line passes under the roof's front edge to his face (the car is nose down)
    shot(cam_w, a, b, (-0.42, -2.9, 0.25), (-0.42, -1.2, 0.74), (-0.42, -2.72, 0.24), (-0.42, -1.2, 0.72), lens=24)
    for o in O["phone"] + [O["phone_glow"]]:
        bl.on(o, range(a, b))
    # phone held in front of his chest (hand at about (-0.47, -1.41, 0.54) world, found by a pose search),
    # the other hand jabbing at its screen
    hold = {"sh-1": (-50, 20, 20), "el-1": (-108, 0, 0)}
    tap, back = ((-56, -10, -40), (-108, 0, 0)), ((-38, -10, -40), (-124, 0, 0))
    pose(P, a, **hold, sh1=back[0], el1=back[1], head=(16, 0, -4), chest=(-2, 0, 0))   # eyes down on the phone
    for j, f in enumerate(range(a + 8, b - 10, 8)):            # dialling, again and again
        sh, el = tap if j % 2 == 0 else back
        pose(P, f, sh1=sh, el1=el)
    pose(P, b - 14, head=(16, 0, -6), chest=(-2, 0, 0))       # still staring at it ...
    pose(P, b - 6, head=(-4, 0, -26), chest=(0, 0, -6))       # looks up: no signal, no time
    pose(P, b - 2, **hold)                                    # the phone stays up until the cut
    bs.hold_phone(sc, a + 4)

    # 3 door: MISTAKE 2 -- the waterline view: both hands on the glass, he shoves, the river pushes it shut.
    # Arm angles for this and the next two shots come from a solver that keeps every arm inside the closed door.
    a, b = S["door"]
    use(cam_w, a)
    split_on(a, b)
    shot(cam_w, a, b, (-2.9, -1.25, 0.004), (-0.8, -1.15, 0.14), (-2.75, -1.2, 0.004), (-0.8, -1.12, 0.14), lens=19)
    for o in O["arrows"]:
        bl.on(o, range(a + 6, b))
    for j, f in enumerate(range(a + 6, b, 6)):
        for o in O["arrows"]:
            k(o, "scale", f, (1.0, 1.0, 1.0) if j % 2 else (1.18, 1.18, 1.18))
    back = {"chest": (0, -8, -14), "head": (0, 0, -40), "sh-1": (-49, 7, 26), "el-1": (-112, 0, 0),
            "sh1": (-63, -2, -24), "el1": (-67, 0, 0)}
    push = {"chest": (0, -16, -22), "head": (8, 0, -46), "sh-1": (-62, 8, 29), "el-1": (-90, 0, 0),
            "sh1": (-76, -4, -15), "el1": (-46, 0, 0)}
    pose(P, a, **back)
    for j, f in enumerate(range(a + 5, b - 2, 5)):              # shove, shove, shove
        pose(P, f, **(push if j % 2 == 0 else back))
    for m in O["dim_glass"]:                                   # no key-light mirror across the cabin while the
        refl = m.node_tree.nodes["refl"].outputs[0]            # camera sits beside the car
        for f, v in ((0, 1.0), (a, 0.1), (S["out"][0], 1.0)):
            refl.default_value = v
            refl.keyframe_insert("default_value", frame=f)

    # 4 window: seatbelt off, switch down -- the glass starts to move
    a, b = S["window"]
    use(cam_c, a)                                              # outside his window, riding with the car
    shot(cam_c, a, b, (-2.0, -0.45, 1.5), (-0.5, 0.12, 1.08), (-1.85, -0.4, 1.47), (-0.5, 0.12, 1.08), lens=24)
    bl.on(O["belt_loose"], range(a + 14, S["out"][1]))
    buckle = {"chest": (-4, 0, 6), "head": (-22, 0, 12), "sh-1": (-4, -20, 29), "el-1": (-84, 0, 0),
              "sh1": (15, 9, -2), "el1": (-101, 0, 0)}
    switch = {"sh-1": (-27, -2, 3), "el-1": (-93, 0, 0)}
    switch_up = {"sh-1": (-34, -1, 5), "el-1": (-97, 0, 0)}
    pose(P, a, **buckle)                                       # both hands down at the buckle
    pose(P, a + 10, **buckle)
    pose(P, a + 18, chest=(0, 0, -4), head=(-8, 0, -10), sh1=(-49, -9, -52), el1=(-98, 0, 0))   # throws the belt off
    pose(P, a + 24, sh1=(-49, -9, -52), el1=(-98, 0, 0))
    pose(P, a + 32, chest=(0, 0, -12), head=(-12, 0, -40), sh1=(-62, 0, 0), el1=(-28, 0, 0), **switch_up)
    pose(P, a + 36, **switch)                                  # presses the window switch and holds it
    pose(P, b - 12, head=(-12, 0, -40))
    pose(P, b - 6, head=(-20, 0, -30))                         # it stopped?
    pane = O["pane"]
    bl.on(O["pane_edge"], range(a, S["out"][0] + 3))
    k(pane, "location", a + 38, (0.0, 0.0, 0.0))
    k(pane, "location", a + 74, (-0.0131, 0.0, -0.08))          # down a hand's width ... and there it stops
    k(pane, "location", a + 77, (-0.0123, 0.0, -0.075))         # the motor strains once
    k(pane, "location", a + 80, (-0.0131, 0.0, -0.08))
    for fc in _curves(pane.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"                        # a motor, not a cushion

    # 5 stuck: the power dies; he pulls out the window hammer
    a, b = S["stuck"]
    use(cam_c, a)
    shot(cam_c, a, b, (-1.8, -0.32, 1.48), (-0.6, 0.1, 1.3), (-1.68, -0.3, 1.46), (-0.6, 0.1, 1.3), lens=26)
    pose(P, a, chest=(0, 0, -12), head=(-18, 0, -32), **switch)
    for j, f in enumerate(range(a + 3, a + 16, 3)):             # jabbing a dead switch
        pose(P, f, **(switch if j % 2 else switch_up))
    for node_ob in (O["cluster"], O["radio"]):
        em = node_ob.data.materials[0].node_tree.nodes["Emission"].inputs["Strength"]
        bl._keys(em, "default_value", ((a + 18, em.default_value), (a + 19, 9), (a + 20, 0), (a + 22, 5), (a + 23, 0)))
    pose(P, a + 16, chest=(0, 0, -12), head=(-18, 0, -32), **switch)
    down = {"chest": (6, 0, -8), "head": (-24, 0, -8), "sh-1": (20, -6, 3), "el-1": (-102, 0, 0)}
    show = {"chest": (0, 0, -10), "sh-1": (-60, 1, 12), "el-1": (-99, 0, 0)}
    pose(P, a + 25, **down)                                    # reaches down beside the seat ...
    pose(P, a + 28, **down)
    for o in O["hammer"]:
        bl.on(o, range(a + 26, S["out"][0] + 4))             # gone from his hand the frame after it lands
    pose(P, a + 39, head=(-4, 0, -30), **show)                 # ... and up comes the window hammer
    pose(P, a + 50, head=(-4, 0, -30))
    pose(P, a + 58, head=(0, 0, 8))                            # "never the windshield": a look at the glass ahead
    pose(P, a + 72, head=(0, 0, 8))
    pose(P, a + 80, head=(-6, 0, -38))                         # back to his own window
    pose(P, b - 10, **show)
    pose(P, b - 3, chest=(0, 6, -4), **{"sh-1": (-57, 18, 5), "el-1": (-107, 0, 0)})        # wind-up
    bs.hold_hammer(sc, a + 39)

    # 6 out: the glass shatters, the river pours in, he goes through the window
    a, b = S["out"]
    use(cam_w, a)
    shot(cam_w, a, b, (-2.5, -2.4, 0.95), (-0.75, -1.2, 0.35), (-2.35, -2.25, 0.9), (-0.8, -1.15, 0.3), lens=22)
    hit = a + 3
    pose(P, hit, chest=(0, -8, -16), sh1=(-62, 0, 0), el1=(-28, 0, 0),                      # the hammer lands (his
         **{"sh-1": (-60, -20, 25), "el-1": (-87, 0, 0)})                                  # other hand held the wheel)
    bl.on(O["pane"], range(0, hit))
    sc.frame_set(hit)
    wc = car.matrix_world @ Vector((-0.8, -0.35, 1.25))
    bl.burst("shards", tuple(wc), hit, 40, speed=1.6, up=(0.2, 1.6), mat=O["glass_m"], size=0.014, life=20)
    bl.burst("spray", tuple(wc), hit, 60, speed=1.2, up=(0.0, 1.0), mat=O["drop_m"], size=0.008, life=16)
    jets = []
    for j in range(4):
        p0 = Vector((-0.86, -0.7 + 0.25 * j, 1.0))
        jets.append(bl.poly(f"pour{j}", bl.jagged(p0, p0 + Vector((0.55, 0.1, -0.35)), 3, 0.1), 0.035,
                            O["foam_m"], taper=(1.3, 0.5)))
        jets[-1].parent = car
    bl.flicker(jets, hit + 1, S["surface"][0])
    root = P["root"]
    k(root, "location", hit + 2, tuple(root.location))
    k(root, "rotation_euler", hit + 2, (0, 0, 0))
    pose(P, hit + 2, **{"sh-1": (-150, 30, 0), "el-1": (-10, 0, 0), "sh1": (-150, -30, 0), "el1": (-10, 0, 0),
                        "head": (-10, 0, -50), "chest": (0, -30, -30)})
    k(root, "location", b - 10, (-0.25, 0.12, 0.18))
    k(root, "rotation_euler", b - 10, (0, math.radians(-38), 0))
    k(root, "location", b, (-0.42, 0.08, 0.3))
    k(root, "rotation_euler", b, (0, math.radians(-50), 0))          # half out at the cut
    props = set(O["phone"] + O["hammer"])
    inside = [o for o in [root] + list(root.children_recursive) if o not in props]
    for o in inside:
        bl.on(o, range(0, b))

    # 7 surface: the waterline view -- he comes up; the headlights sink below him
    a, b = S["surface"]
    use(cam_w, a)
    split_on(a, S["end"][1] + 2)                                 # one run through the end shot: two back-to-back runs
                                                                 # cancel on the last surface frame (a mirror flash)
    shot(cam_w, a, b, (-3.4, -1.3, 0.004), (-1.6, -1.05, 0.12), (-3.25, -1.25, 0.004), (-1.6, -1.05, 0.12), lens=20)
    before = set(bpy.data.objects)
    P2 = bp.build_dummy_v2(at=(-1.6, -0.95, -1.5), label="TEST 05")
    for o in set(bpy.data.objects) - before:
        bl.on(o, range(a, S["end"][1] + 2))
    r2 = P2["root"]
    for j, f in enumerate(range(a, S["end"][1] + 2, 8)):                  # bobbing, treading water
        k(r2, "location", f, (-1.6, -0.95, -1.52 + (0.05 if j % 2 else -0.02)))
        pose(P2, f, sh=((-20, 55, 0) if j % 2 else (-35, 40, 0)), el=((-50, 0, 0) if j % 2 else (-25, 0, 0)),
             head=((14, 0, 6) if j % 2 else (8, 0, -6)), hip=(-15, 0, 0), kn=(30, 0, 0))
    pose(P2, a, head=(20, 0, 0))                                 # gasping, head back
    bs.bubbles(a, b, n=60)

    # 8 end: pull back from him at the surface, the headlights fading below; the loop restarts on the plunge
    a, b = S["end"]
    use(cam_w, a)
    shot(cam_w, a, b, (-3.25, -1.25, 0.004), (-1.6, -1.05, 0.12), (-4.3, -1.6, 0.004), (-1.4, -1.0, 0.0), lens=20)
    bs.bubbles(a, b, n=50)
    bs.finalize(end)
    for m in [O["river_mat"]] + O["dim_glass"]:                   # the split and reflection switches never blend
        for fc in _curves(m.node_tree.animation_data.action):
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT"


TIMELINES = {"penny": (bp.scene_penny, timeline_penny), "hail": (bp.scene_hail, timeline_hail),
             "quicksand": (bp.scene_quicksand, timeline_quicksand),
             "lightning": (lambda samples: __import__("blender_lightning").build(samples, "A"), timeline_lightning),
             "sinking": (lambda samples: __import__("blender_sinking").build(samples, "B"), timeline_sinking),
             # "10 Seconds in ___" (blender_tensec.py)
             "lavayou": (lambda samples: __import__("blender_whatif").scene_lavayou(samples),
                         lambda sc, T: __import__("blender_whatif").timeline_lavayou(sc, T)),
             "oxygen": (lambda samples: __import__("blender_whatif").scene_oxygen(samples),
                        lambda sc, T: __import__("blender_whatif").timeline_oxygen(sc, T)),
             "gravity": (lambda samples: __import__("blender_whatif").scene_gravity(samples),
                         lambda sc, T: __import__("blender_whatif").timeline_gravity(sc, T)),
             "spin": (lambda samples: __import__("blender_jems").scene_spin(samples),
                      lambda sc, T: __import__("blender_jems").timeline_spin(sc, T)),
             "friction": (lambda samples: __import__("blender_jems").scene_friction(samples),
                          lambda sc, T: __import__("blender_jems").timeline_friction(sc, T)),
             "lava": (lambda samples: __import__("blender_tensec").scene_lava(samples),
                      lambda sc, T: __import__("blender_tensec").timeline_lava(sc, T)),
             "venus": (lambda samples: __import__("blender_tensec").scene_venus(samples),
                       lambda sc, T: __import__("blender_tensec").timeline_venus(sc, T)),
             "ocean": (lambda samples: __import__("blender_tensec").scene_ocean(samples),
                       lambda sc, T: __import__("blender_tensec").timeline_ocean(sc, T))}

if __name__ == "__main__":
    name, frames_dir, timing_path = sys.argv[1:4]
    rest = sys.argv[4:]
    T = json.load(open(timing_path))
    samples = int(os.environ.get("DUMMY_SAMPLES", "20"))
    build, timeline = TIMELINES[name]
    sc = build(samples)
    if os.environ.get("DUMMY_RES"):                    # e.g. 540x960 for quick look tests
        sc.render.resolution_x, sc.render.resolution_y = map(int, os.environ["DUMMY_RES"].split("x"))
    sc.frame_end = T["frames"] - 1
    timeline(sc, T)
    os.makedirs(frames_dir, exist_ok=True)
    if rest and rest[0] == "still":
        sd = os.path.join(os.path.dirname(frames_dir.rstrip("/")), "stills")
        os.makedirs(sd, exist_ok=True)
        for f in rest[1:]:
            sc.frame_set(int(f))
            sc.render.filepath = os.path.join(sd, f"s_{int(f):04d}.png")
            bpy.ops.render.render(write_still=True)
            print("saved", sc.render.filepath, flush=True)
    else:
        bk.render(sc, frames_dir, int(rest[0]), int(rest[1]))
