"""
blender_lightning.py -- Dummy Test #4 (lightning hits his car): the scene and the opening options for the owner
to pick from (rule 14, rule 18). Uses the upgraded dummy (v2).

  /root/.venvs/blender/bin/python blender_lightning.py OUT_DIR A|B|C [FRAME ...]     (default 0 12 24 48)

The full Short is rendered through blender_dummy_anim.py (TIMELINES["lightning"] -> build + timeline below).

A  windshield: from the hood, the bolt slams into the roof above him at frame 0
B  inside: his face big, the windows behind him blow out white, sparks rain past
C  window: outside the driver's window, his face big, the bolt hitting the roof right above him
"""
import math
import os
import random
import sys

import bpy  # noqa: I001
import bmesh
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_kit as bk  # noqa: E402
import blender_pitches as bp  # noqa: E402

STRIKE = Vector((-0.45, 0.05, 1.665))          # the roof edge, right above his head
BOLT_FROM = {"A": (1.0, 10.0, 22.0), "B": (1.0, 10.0, 22.0), "C": (6.0, 3.0, 22.0)}   # away from each camera
SKY_FLASH = {"A": 1.0, "B": 2.2, "C": 1.0}      # inside (B) the event is the windows blowing out white
R = random.Random(4)


# ── materials ─────────────────────────────────────────────────────────────────
def emit(name, color, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value, e.inputs["Strength"].default_value = (*color, 1), strength
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(e.outputs[0], o.inputs["Surface"])
    return m


def glass(name):
    """Thin window glass: see-through, with a fresnel reflection (no refraction blur)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    tr.inputs["Color"].default_value = (0.82, 0.88, 0.92, 1)
    gl = nt.nodes.new("ShaderNodeBsdfGlossy")
    gl.inputs["Roughness"].default_value = 0.04
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.25
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lw.outputs["Fresnel"], mx.inputs[0])
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(gl.outputs[0], mx.inputs[2])
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(mx.outputs[0], o.inputs["Surface"])
    return m


def asphalt():
    m, b, nt = bk._principled("wet_asphalt")
    b.inputs["Base Color"].default_value = (0.018, 0.018, 0.02, 1)
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value, nz.inputs["Detail"].default_value = 0.6, 6.0
    rr = nt.nodes.new("ShaderNodeMapRange")
    rr.inputs["From Min"].default_value, rr.inputs["From Max"].default_value = 0.45, 0.6
    rr.inputs["To Min"].default_value, rr.inputs["To Max"].default_value = 0.04, 0.5     # puddles mirror the flash
    nt.links.new(nz.outputs["Fac"], rr.inputs["Value"])
    nt.links.new(rr.outputs["Result"], b.inputs["Roughness"])
    return m


# ── geometry helpers ──────────────────────────────────────────────────────────
def rod(name, p0, p1, r, mat, parent=None):
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    ob = bp.cylinder(name, r, d.length, (p0 + p1) / 2, mat, parent, segs=16)
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = d.to_track_quat("Z", "Y")
    return ob


def cabin(paint, win, liner):
    """The greenhouse as one frustum: glass on the sides/front/back, paint on the roof."""
    bot = [(-0.82, -0.95), (0.82, -0.95), (0.82, 1.3), (-0.82, 1.3)]
    top = [(-0.7, -0.2), (0.7, -0.2), (0.7, 0.8), (-0.7, 0.8)]
    zb, zt = 0.95, 1.63
    bm = bmesh.new()
    vb = [bm.verts.new((x, y, zb)) for x, y in bot]
    vt = [bm.verts.new((x, y, zt)) for x, y in top]
    faces = [bm.faces.new((vb[i], vb[(i + 1) % 4], vt[(i + 1) % 4], vt[i])) for i in range(4)]
    roof = bm.faces.new(vt[::-1])
    me = bpy.data.meshes.new("cabin")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(win)
    me.materials.append(liner)
    me.polygons[4].material_index = 1
    ob = bpy.data.objects.new("cabin", me)
    bp.link(ob)
    for i in range(4):                          # pillars along the slanted edges, plus B-pillars
        rod(f"pillar{i}", (*bot[i], zb), (*top[i], zt), 0.035, paint)
    for s in (-1, 1):
        rod(f"bpillar{s}", (s * 0.815, 0.25, zb), (s * 0.7, 0.3, zt), 0.03, paint)
    bp.box("roof", (1.46, 1.06, 0.05), (0, 0.3, zt + 0.01), paint, bevel=0.025)
    return ob


def jagged(p0, p1, depth=6, rough=0.22):
    """Midpoint displacement: a lightning-shaped polyline from p0 to p1."""
    pts = [Vector(p0), Vector(p1)]
    for _ in range(depth):
        out = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            L = (b - a).length
            m = (a + b) / 2 + Vector((R.uniform(-1, 1), R.uniform(-1, 1), R.uniform(-0.3, 0.3))) * L * rough
            out += [m, b]
        pts = out
    return pts


def poly(name, pts, radius, mat, taper=(1.0, 1.0)):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions, cu.bevel_depth, cu.bevel_resolution = "3D", radius, 2
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    n = len(pts) - 1
    for i, (p, co) in enumerate(zip(sp.points, pts)):
        p.co = (*co, 1)
        p.radius = taper[0] + (taper[1] - taper[0]) * i / max(1, n)
    ob = bpy.data.objects.new(name, cu)
    cu.materials.append(mat)
    return bp.link(ob)


def visible_on(ob, frames_on, last=60):
    for f in range(0, last + 1):
        ob.hide_render = f not in frames_on
        ob.keyframe_insert("hide_render", frame=f)


# ── the scene ─────────────────────────────────────────────────────────────────
CAM_POINTS = [(-0.4, -1.75, 1.78), (-0.4, -2.05, 1.83), (-1.75, -2.6, 0.45), (-3.0, -3.1, 0.5),
              (-4.3, -1.0, 2.4), (-1.55, -2.35, 0.32), (-0.4, -2.45, 2.3), (0.5, -0.95, 1.38)]
VIS = {}          # object -> frames on which it is rendered (event objects); applied by finalize()
HIDE = {}         # object -> frames on which an always-there object is hidden (the convertible's missing roof)
O = {}            # named handles


def on(ob, frames):
    VIS.setdefault(ob, set()).update(frames)


def keyval(sock_or_obj, path, f, v, constant=False):
    setattr(sock_or_obj, path, v)
    sock_or_obj.keyframe_insert(path, frame=f)


def make_car(sc, label="TEST 04"):
    """The hard-top car with him at the wheel (also used by blender_sinking.py). Fills O; returns sc."""
    car = O["car"] = bp.pivot("car", (0, 0, 0))
    paint = O["paint"] = bp.mat("car_paint", (0.02, 0.07, 0.17), rough=0.22, metallic=0.55, coat=1.0)
    dark = bp.mat("car_dark", (0.02, 0.02, 0.022), rough=0.5)
    rubber = bp.mat("tire", (0.015, 0.015, 0.016), rough=0.75)
    steel = bp.mat("hub", (0.6, 0.6, 0.62), rough=0.25, metallic=1.0)
    seat = bp.mat("seat", (0.05, 0.05, 0.055), rough=0.8)
    before = set(bpy.data.objects)
    bp.box("headliner", (1.36, 0.98, 0.02), (0, 0.3, 1.6), seat)
    bp.box("body", (1.8, 4.4, 0.66), (0, 0, 0.62), paint, bevel=0.16)
    cabin(paint, glass("window"), seat)
    bp.box("grille", (1.3, 0.05, 0.22), (0, -2.2, 0.55), dark, bevel=0.02)
    for s in (-1, 1):
        bp.box(f"headlight{s}", (0.36, 0.04, 0.12), (s * 0.6, -2.205, 0.76), emit(f"hl{s}", (1.0, 0.93, 0.8), 18),
               bevel=0.02)
        bp.box(f"taillight{s}", (0.34, 0.04, 0.1), (s * 0.62, 2.205, 0.8), emit(f"tl{s}", (1.0, 0.05, 0.03), 8),
               bevel=0.02)
        bp.box(f"mirror{s}", (0.12, 0.08, 0.09), (s * 0.96, -0.85, 1.05), paint, bevel=0.02)
    for x in (-0.4, 0.4):
        bp.box(f"seat{x}", (0.55, 0.55, 0.12), (x, 0.3, 0.45), seat, bevel=0.04)
        bp.box(f"seatback{x}", (0.55, 0.12, 0.75), (x, 0.55, 0.85), seat, bevel=0.04, rot=(math.radians(-10), 0, 0))
    bp.box("dash", (1.6, 0.35, 0.18), (0, -0.78, 0.98), dark, bevel=0.04)
    O["radio"] = bp.box("radio", (0.22, 0.02, 0.1), (0.0, -0.6, 0.98), emit("radio_on", (0.3, 0.7, 1.0), 4))
    O["cluster"] = bp.box("cluster", (0.3, 0.02, 0.07), (-0.4, -0.66, 1.06), emit("cluster_on", (0.2, 0.9, 1.0), 3))
    bp.cylinder("wheel", 0.19, 0.03, (-0.4, -0.36, 0.97), dark, rot=(math.radians(60), 0, 0), bevel=0.01)
    bp.cylinder("column", 0.03, 0.3, (-0.4, -0.5, 0.9), dark, rot=(math.radians(60), 0, 0))
    # the convertible: low windshield frame + folded top (only shown while the roof is gone)
    O["lowshield"] = bp.box("lowshield", (1.5, 0.04, 0.32), (0, -0.88, 1.12), glass("window2"),
                            rot=(math.radians(-30), 0, 0))
    O["folded"] = bp.box("folded_top", (1.5, 0.45, 0.18), (0, 1.3, 1.02), seat, bevel=0.06)
    for ob in set(bpy.data.objects) - before:
        if ob.parent is None:
            ob.parent = car
    O["roof_parts"] = [bpy.data.objects[n] for n in ("cabin", "roof", "headliner", "bpillar-1", "bpillar1")] + \
        [bpy.data.objects[f"pillar{i}"] for i in range(4)]
    for s in (-1, 1):
        for y in (-1.35, 1.35):
            O[f"tire{s}{y}"] = bp.cylinder(f"tire{s}{y}", 0.34, 0.24, (s * 0.88, y, 0.34), rubber,
                                          rot=(0, math.radians(90), 0), bevel=0.05)
            O[f"hub{s}{y}"] = bp.cylinder(f"hubcap{s}{y}", 0.19, 0.25, (s * 0.88, y, 0.34), steel,
                                         rot=(0, math.radians(90), 0))
    P = O["P"] = bp.build_dummy_v2(at=(-0.4, 0.3, -0.37), label=label)
    P["root"].parent = car
    return sc


def build(samples=24, which="A"):
    """The static world: street, car, him at the wheel, and every event object (hidden until an event shows it)."""
    VIS.clear(), HIDE.clear(), O.clear()
    sc = bk.new_scene(fps=24, samples=samples, frames=73)
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.4
    sc.view_settings.exposure = 0.3                         # night, but readable on a phone
    w = bp.world(sc, (0.03, 0.036, 0.06), 0.5)
    O["sky"] = w.node_tree.nodes["Background"].inputs[1]
    O["sky_mult"] = SKY_FLASH[which]

    bp.box("ground", (80, 80, 0.02), (0, 0, -0.01), asphalt())
    sc = make_car(sc)
    car = O["car"]

    # event objects
    bolt_m = O["bolt_m"] = emit("bolt", (0.78, 0.86, 1.0), 60)
    top = STRIKE + Vector(BOLT_FROM[which])
    O["bolts"] = [poly("bolt", jagged(top, STRIKE, 7, 0.2), 0.035, bolt_m, taper=(1.6, 0.8))]
    pts = jagged(top, STRIKE, 4, 0.2)
    for j in range(5):
        a = pts[R.randrange(2, len(pts) - 3)]
        b = a + Vector((R.uniform(-3, 3), R.uniform(-3, 3), -R.uniform(2, 6)))
        O["bolts"].append(poly(f"branch{j}", jagged(a, b, 4, 0.25), 0.015, bolt_m, taper=(1.0, 0.2)))
    far_top = Vector((3.0, 30.0, 26.0))
    O["far"] = [poly("farbolt", jagged(far_top, Vector((2.5, 28.0, 0.0)), 7, 0.18), 0.07, bolt_m, taper=(1.4, 0.8))]
    O["hot"] = bp.ellipsoid("hotspot", (0.05, 0.05, 0.025), tuple(STRIKE), emit("hot", (1.0, 0.95, 0.9), 120))
    O["flash"] = bp.light("flash", "POINT", tuple(STRIKE + Vector((0.4, 0.6, 2.2))), 0, size=0.3,
                          color=(0.8, 0.88, 1.0))
    cur_m = emit("current", (0.7, 0.82, 1.0), 55)
    # just outside the skin (pillars r 0.035, roof top 1.665, body side x 0.9), or the paint hides the current
    paths = [[STRIKE, Vector((-0.75, 0.75, 1.69)), Vector((-0.9, 1.3, 0.98)), Vector((-0.96, 1.0, 0.6))],
             [STRIKE, Vector((-0.75, -0.2, 1.69)), Vector((-0.9, -0.95, 0.97)), Vector((-0.96, -1.0, 0.62))],
             [STRIKE, Vector((-0.77, 0.3, 1.69)), Vector((-0.89, 0.25, 0.95)), Vector((-0.96, 0.2, 0.45))],
             [STRIKE, Vector((0.4, 0.6, 1.69)), Vector((0.75, 0.8, 1.69)), Vector((0.9, 1.3, 0.98)),
              Vector((0.96, 1.6, 0.5))]]
    O["crawl"] = []
    for j, path in enumerate(paths):
        pts = sum((jagged(a, b, 3, 0.08)[:-1] for a, b in zip(path, path[1:])), []) + [path[-1]]
        O["crawl"].append(poly(f"crawl{j}", pts, 0.022, cur_m))
    O["arcs"] = [poly("arc", jagged((-0.92, -1.05, 0.6), (-1.25, -1.6, 0.0), 5, 0.3), 0.02, bolt_m, taper=(1.0, 0.6)),
                 poly("arc2", jagged((-0.92, 1.05, 0.55), (-1.2, 1.7, 0.0), 5, 0.3), 0.018, bolt_m, taper=(1.0, 0.6))]
    O["puddle"] = bp.light("puddle_flash", "POINT", (-1.25, -1.6, 0.15), 0, size=0.2, color=(0.75, 0.85, 1.0))
    O["glow"] = bp.light("glow", "AREA", (-1.6, 0.2, 1.6), 0, size=3.0, color=(0.6, 0.75, 1.0), aim=(-0.6, 0.2, 1.0))
    O["spark_m"] = emit("spark", (1.0, 0.75, 0.35), 60)
    O["shred_m"] = rubber
    O["base"] = sc

    rain_m = emit("rain", (0.55, 0.6, 0.7), 0.5)
    for j in range(320):
        c = Vector((R.uniform(-4.5, 3.5), R.uniform(-4.5, 3.5), R.uniform(0.0, 4.5)))
        if any((c - Vector(q)).length < 1.4 for q in CAM_POINTS):      # a drop next to the lens is a grey bar
            continue
        rod(f"rain{j}", c, c + Vector((0.04, 0.02, -0.38)), 0.0028, rain_m)
    bp.light("key", "AREA", (-3.5, -4.0, 4.0), 450, size=3.0, color=(0.7, 0.8, 1.0), aim=(-0.3, 0.0, 1.0))
    bp.light("rim", "AREA", (2.5, 4.5, 3.0), 600, size=2.0, color=(0.75, 0.85, 1.0), aim=(0, 0.3, 1.2))
    bp.light("left_fill", "AREA", (-4.0, 1.0, 2.0), 160, size=3.0, color=(0.75, 0.82, 1.0), aim=(-0.5, 0.2, 1.0))
    bp.light("cabin_fill", "AREA", (0.2, -0.5, 1.5), 14, size=0.4, color=(0.9, 0.95, 1.0), aim=(-0.4, 0.3, 1.3))
    for ob in sc.objects:                      # lights light the scene; they are never seen as blobs
        if ob.type == "LIGHT":
            ob.visible_camera = False
    return sc


def _keys(target, path, pairs):
    for f, v in pairs:
        setattr(target, path, v)
        target.keyframe_insert(path, frame=f)


def strike(f0, arc_frames=5, sparks=True, sky=1.0):
    """One strike on the roof at frame f0: bolt flicker, roof hot spot, flash, current over the body, arc to the
    puddle, sparks. Several strikes may be stacked (replays)."""
    for b in O["bolts"]:
        on(b, {f0, f0 + 1, f0 + 3})
    on(O["hot"], range(f0, f0 + 5))
    on(O["crawl"][0], range(f0, f0 + 5)), on(O["crawl"][1], {f0, f0 + 1, f0 + 3, f0 + 4})
    on(O["arcs"][0], range(f0 + 1, f0 + 1 + arc_frames))
    m = O["sky_mult"] * sky
    O.setdefault("sky_keys", []).extend([(f0 - 1, 0.5), (f0, 3.2 * m), (f0 + 1, 2.4 * m), (f0 + 2, 0.7 * m),
                                         (f0 + 3, 2.8 * m), (f0 + 4, 1.2 * m), (f0 + 6, 0.6), (f0 + 10, 0.5)])
    O.setdefault("flash_keys", []).extend([(f0 - 1, 0), (f0, 22000), (f0 + 1, 15000), (f0 + 2, 1500),
                                           (f0 + 3, 18000), (f0 + 4, 4000), (f0 + 6, 300), (f0 + 10, 0)])
    last = f0 + arc_frames + 2
    O.setdefault("puddle_keys", []).extend([(f0, 0), (f0 + 1, 4000), (f0 + 3, 5000), (last - 2, 2500), (last, 0)])
    if sparks:
        burst(f"spk{f0}", STRIKE, f0, 16, speed=2.5, up=(0.5, 3.0))


def burst(name, at, f0, n, speed=2.5, up=(0.5, 3.0), mat=None, size=0.012, life=18):
    for j in range(n):
        s = bp.ellipsoid(f"{name}_{j}", (size, size, size), tuple(at), mat or O["spark_m"])
        v = Vector((R.uniform(-speed, speed), R.uniform(-speed, speed), R.uniform(*up)))
        for f in range(f0, f0 + life + 1, 2):
            t = (f - f0) / 24
            p = Vector(at) + v * t + Vector((0, 0, -4.9 * t * t))
            s.location = (p.x, p.y, max(p.z, size))
            s.keyframe_insert("location", frame=f)
        on(s, range(f0, f0 + life))


def flicker(objs, f0, f1, pattern=(1, 1, 0, 1, 0, 1, 1, 1, 0)):
    for j, ob in enumerate(objs):
        on(ob, [f for f in range(f0, f1) if pattern[(f + 3 * j) % len(pattern)]])


def finalize(end):
    """Write hide_render keys only where visibility changes."""
    for ob, frames in VIS.items():
        prev = None
        for f in range(0, end + 1):
            h = f not in frames
            if h != prev:
                ob.hide_render = h
                ob.keyframe_insert("hide_render", frame=f)
                prev = h
    for ob, frames in HIDE.items():
        prev = None
        for f in range(0, end + 1):
            h = f in frames
            if h != prev:
                ob.hide_render = h
                ob.keyframe_insert("hide_render", frame=f)
                prev = h
    for name, target, path in (("sky_keys", O["sky"], "default_value"), ("flash_keys", O["flash"].data, "energy"),
                               ("puddle_keys", O["puddle"].data, "energy")):
        seen = {}
        for f, v in sorted(O.get(name, []), key=lambda x: x[0]):
            seen[f] = max(seen.get(f, v), v) if f in seen else v
        for f, v in sorted(seen.items()):
            setattr(target, path, v)
            target.keyframe_insert(path, frame=f)


def pose(P, f, **rots):
    """rots: sh/el/hip/kn apply mirrored to both sides; head/chest direct; keys like sh1/el-1 set one side."""
    for k, r in rots.items():
        if k in ("sh", "el", "hip", "kn"):
            for s in (-1, 1):
                rr = (r[0], r[1] * s, r[2] * s)
                P[f"{k}{s}"].rotation_euler = tuple(math.radians(a) for a in rr)
                P[f"{k}{s}"].keyframe_insert("rotation_euler", frame=f)
        else:
            P[k].rotation_euler = tuple(math.radians(a) for a in r)
            P[k].keyframe_insert("rotation_euler", frame=f)


SEATED = dict(sh=(-62, 0, 0), el=(-28, 0, 0), hip=(-90, 0, 0), kn=(90, 0, 0), head=(0, 0, 0), chest=(0, 0, 0))


def opening_poses(P, f0):
    pose(P, f0, **SEATED)
    pose(P, f0 + 3, sh=(-110, 0, 0), el=(-70, 0, 0), head=(18, 0, 0), chest=(8, 0, 0))
    pose(P, f0 + 12, sh=(-120, 10, 0), el=(-85, 0, 0), head=(26, 0, -6), chest=(6, 0, 0))
    pose(P, f0 + 24, sh=(-115, 12, 0), el=(-80, 0, 0), head=(30, 0, 4), chest=(4, 0, 0))
    pose(P, f0 + 48, sh=(-90, 14, 0), el=(-70, 0, 0), head=(6, 0, 18), chest=(2, 0, 0))


CAMS = {   # (location, aim, lens)
    "A": ((-0.4, -1.75, 1.78), (-0.4, 0.3, 1.42), 30),
    "B": ((0.3, -0.5, 1.56), (-0.42, 0.3, 1.27), 26),
    "C": ((-1.25, -0.2, 1.62), (-0.45, 0.2, 1.62), 24),
}


def camera(sc, which):
    loc, aim, lens = CAMS[which]
    cd = bpy.data.cameras.new("cam")
    cd.sensor_fit, cd.sensor_height, cd.lens, cd.clip_start = "VERTICAL", 24.0, lens, 0.02
    cam = bpy.data.objects.new("cam", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.location = loc
    c = cam.constraints.new("TRACK_TO")
    c.target = bp.pivot("cam_aim", aim)
    c.track_axis, c.up_axis = "TRACK_NEGATIVE_Z", "UP_Y"
    for f, k in ((0, 0.0), (48, 0.12)):                    # a slow push-in over the first 2 s
        cam.location = Vector(loc) + (Vector(aim) - Vector(loc)) * k
        cam.keyframe_insert("location", frame=f)
    return cam


if __name__ == "__main__":
    out, which = sys.argv[1], sys.argv[2]
    frames = [int(f) for f in sys.argv[3:]] or [0, 12, 24, 48]
    sc = build(int(os.environ.get("PITCH_SAMPLES", "24")), which)
    opening_poses(O["P"], 0)
    strike(0)
    rm = O["radio"].data.materials[0].node_tree.nodes["Emission"].inputs["Strength"]
    _keys(rm, "default_value", ((0, 4), (2, 0)))
    finalize(72)
    camera(sc, which)
    os.makedirs(out, exist_ok=True)
    for f in frames:
        sc.frame_set(f)
        sc.render.filepath = os.path.join(out, f"{which}_{f:03d}.png")
        bpy.ops.render.render(write_still=True)
        print("saved", sc.render.filepath, flush=True)
