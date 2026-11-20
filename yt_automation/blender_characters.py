"""
blender_characters.py — character options for the "What If You ..." Shorts (owner, 2026-11-16: "show dummy
humanly, anime like that, give me options first").

Every option uses the SAME pivots as bp.build_dummy_v2 (root, pelvis, chest, head, sh+-1, el+-1, hip+-1, kn+-1),
so the existing timelines and ts.pose() drive any of them unchanged.

  cartoon   a 3D cartoon person: big head and eyes, hair, t-shirt, jeans, trainers
  anime     the same build, cel-shaded with flat colours and black outlines (works in Cycles: the shading is
            computed from the surface normal, not from lights, and the outline is an inverted hull)
  xray      a see-through glowing body with the skeleton and organs inside, for the inside-the-body shots

Run:  python blender_characters.py STYLE OUT.png [body|face]
"""
import math
import os
import sys

import bpy  # noqa: I001  (bpy first: it makes bmesh importable)
import bmesh
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_kit as bk          # noqa: E402
import blender_pitches as bp      # noqa: E402
import blender_tensec as ts       # noqa: E402

LIGHT = Vector((-0.45, -0.6, 0.66)).normalized()      # where the toon "light" comes from


# ── materials ────────────────────────────────────────────────────────────────
def toon(name, color, shade=0.55, rim=True):
    """Flat cel colour: lit or shadow, decided by the surface normal against a fixed direction."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    dot = nt.nodes.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    dot.inputs[1].default_value = tuple(LIGHT)
    nt.links.new(geo.outputs["Normal"], dot.inputs[0])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "CONSTANT"
    e0, e1 = ramp.color_ramp.elements
    e0.position, e0.color = 0.0, (*[c * shade for c in color], 1)
    e1.position, e1.color = 0.12, (*color, 1)
    hi = ramp.color_ramp.elements.new(0.86)                     # a small hard highlight
    hi.color = (*[min(1.0, c * 1.18 + 0.06) for c in color], 1)
    nt.links.new(dot.outputs["Value"], ramp.inputs["Fac"])
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(ramp.outputs["Color"], em.inputs["Color"])
    em.inputs["Strength"].default_value = 1.0
    nt.links.new(em.outputs[0], nt.nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
    return m


def outline_mat():
    m = bpy.data.materials.get("outline")
    if m:
        return m
    m = bpy.data.materials.new("outline")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    mix = nt.nodes.new("ShaderNodeMixShader")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    ink = nt.nodes.new("ShaderNodeEmission")
    ink.inputs["Color"].default_value = (0.01, 0.008, 0.012, 1)
    nt.links.new(geo.outputs["Backfacing"], mix.inputs[0])
    nt.links.new(ink.outputs[0], mix.inputs[1])                  # the hull's far side, seen past the edge: ink
    nt.links.new(tr.outputs[0], mix.inputs[2])                   # its near side (backfacing, flipped): clear
    nt.links.new(mix.outputs[0], nt.nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
    return m


def add_outlines(objs, width=0.0055):
    if os.environ.get("JEMS_STYLE", "3d") == "3d":                # lit 3D look: no drawn outlines
        return
    ol = outline_mat()
    for o in objs:
        if o.type != "MESH":
            continue
        o.data.materials.append(ol)
        m = o.modifiers.new("outline", "SOLIDIFY")
        m.thickness, m.offset, m.use_flip_normals = width, 1.0, True
        m.material_offset = len(o.data.materials) - 1


def holo(name, color, edge=4.0, core=0.05):
    """See-through glowing skin: almost clear where it faces you, bright at the edges."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.45
    pw = nt.nodes.new("ShaderNodeMath")
    pw.operation = "POWER"
    pw.inputs[1].default_value = 1.6
    nt.links.new(lw.outputs["Facing"], pw.inputs[0])
    add = nt.nodes.new("ShaderNodeMath")
    add.operation = "ADD"
    add.inputs[1].default_value = core
    nt.links.new(pw.outputs[0], add.inputs[0])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    em.inputs["Strength"].default_value = edge
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(add.outputs[0], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], nt.nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
    return m


# ── parts ────────────────────────────────────────────────────────────────────
def on_face(rx, ry, rz, hz, x, z, out=0.0):
    """A point on the front of the head ellipsoid (head-pivot space), pushed `out` along -y."""
    u = 1 - (x / rx) ** 2 - ((z - hz) / rz) ** 2
    return (x, -ry * math.sqrt(max(0.02, u)) - out, z)


def hair_cap(name, rx, ry, rz, hz, mat, parent, fringe=0.35, clumps=0.012, seed=3):
    """A cap of hair over the top and back of the head, with the face left open below the fringe line."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=64, v_segments=40, radius=1.0)
    gone = [v for v in bm.verts if v.co.y < -0.15 and v.co.z < fringe + 0.55 * (abs(v.co.x) ** 2)]
    gone += [v for v in bm.verts if v.co.z < -0.15 and v.co.y < 0.55]
    bmesh.ops.delete(bm, geom=list(set(gone)), context="VERTS")
    import random
    rnd = random.Random(seed)
    phase = [rnd.uniform(0, 6) for _ in range(6)]
    for v in bm.verts:
        d = v.co.copy()
        bump = clumps * (math.sin(d.x * 9 + phase[0]) * math.sin(d.y * 7 + phase[1]) + 0.6 * math.sin(d.z * 11 + phase[2]))
        k = 1.0 + bump
        v.co = Vector((d.x * rx * 1.07 * k, d.y * ry * 1.08 * k + 0.008, d.z * rz * 1.04 * k + hz + 0.012))
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.012)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(mat)
    return bp.link(bpy.data.objects.new(name, me), parent)


def spike(name, base, tip, r, mat, parent):
    """A cone of hair from `base` to `tip` (anime spikes and bangs)."""
    b, t = Vector(base), Vector(tip)
    d = t - b
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=r, radius2=0.0, depth=d.length)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(mat)
    o = bp.link(bpy.data.objects.new(name, me), parent)
    o.location = (b + t) / 2
    o.rotation_euler = d.normalized().to_track_quat("Z", "Y").to_euler()
    return o


def build_person(style):
    """A person on the dummy's pivots. Returns P (pivots) and the list of visible parts."""
    S = {
        "cartoon": dict(skin=(0.86, 0.6, 0.47), shirt=(0.05, 0.55, 0.62), pants=(0.12, 0.2, 0.42), shoe=(0.92, 0.92, 0.9),
                        sole=(0.85, 0.2, 0.15), hair=(0.18, 0.09, 0.04), iris=(0.32, 0.18, 0.08), head=1.6),
        "anime": dict(skin=(1.0, 0.82, 0.7), shirt=(0.12, 0.13, 0.2), pants=(0.2, 0.22, 0.3), shoe=(0.9, 0.9, 0.92),
                      sole=(0.85, 0.12, 0.16), hair=(0.95, 0.42, 0.12), iris=(0.1, 0.45, 0.95), head=1.45),
        "xray": dict(skin=(0.25, 0.85, 1.0), shirt=(0.25, 0.85, 1.0), pants=(0.25, 0.85, 1.0), shoe=(0.25, 0.85, 1.0),
                     sole=(0.25, 0.85, 1.0), hair=(0.25, 0.85, 1.0), iris=(0.25, 0.85, 1.0), head=1.08),
    }[style]
    if style == "anime":
        M = lambda n, c, **kw: toon(n, c)
    elif style == "xray":
        M = lambda n, c, **kw: holo(n, c, edge=kw.get("edge", 4.0))
    else:
        M = lambda n, c, **kw: bp.mat(n, c, rough=kw.get("rough", 0.55), sss=kw.get("sss", 0.0))
    skin = M("p_skin", S["skin"], sss=0.25, rough=0.5)
    shirt = M("p_shirt", S["shirt"], rough=0.8)
    pants = M("p_pants", S["pants"], rough=0.75)
    shoe = M("p_shoe", S["shoe"], rough=0.5)
    sole = M("p_sole", S["sole"], rough=0.6)
    hair = M("p_hair", S["hair"], rough=0.45)
    white = M("p_white", (0.97, 0.97, 0.97), rough=0.15)
    iris = M("p_iris", S["iris"], rough=0.2)
    dark = M("p_dark", (0.02, 0.015, 0.015), rough=0.3)
    brow = M("p_brow", tuple(c * 0.7 for c in S["hair"]), rough=0.8)
    lip = M("p_lip", (0.7, 0.3, 0.28), rough=0.5)
    shine = ts.emit("p_shine", (1.0, 1.0, 1.0), 6.0)
    parts = []
    A = lambda o: parts.append(o) or o

    P = {}
    root = P["root"] = bp.pivot("person", (0, 0, 0))
    pelvis = P["pelvis"] = bp.pivot("pelvis", (0, 0, 0.95), root)
    A(bp.box("hips", (0.33, 0.2, 0.2), (0, 0, 0.0), pants, pelvis, bevel=0.07))
    chest = P["chest"] = bp.pivot("chest", (0, 0, 0.1), pelvis)
    A(bp.box("torso", (0.38, 0.21, 0.5), (0, 0, 0.22), shirt, chest, bevel=0.09))
    for s in (-1, 1):
        A(bp.ellipsoid(f"shcap{s}", (0.075, 0.1, 0.06), (s * 0.15, 0, 0.45), shirt, chest))
    A(bp.cylinder("neck", 0.05, 0.1, (0, 0, 0.5), skin, chest, segs=32))
    head = P["head"] = bp.pivot("head", (0, 0, 0.5), chest)
    k = S["head"]
    rx, ry, rz = 0.098 * k, 0.108 * k, 0.122 * k
    hz = rz * 0.92
    A(bp.ellipsoid("skull", (rx, ry, rz), (0, 0, hz), skin, head, segs=64, rings=40))
    A(bp.ellipsoid("jaw", (rx * 0.78, ry * 0.8, rz * 0.5), (0, -ry * 0.12, hz - rz * 0.42), skin, head))
    big = {"cartoon": 1.0, "anime": 1.15, "xray": 0.8}[style]
    ex, ez = rx * 0.4, hz + rz * 0.02
    for s in (-1, 1):
        A(bp.ellipsoid(f"ear{s}", (0.014, 0.03, 0.04), (s * rx * 0.98, 0.0, hz - rz * 0.02), skin, head))
        if style == "xray":
            continue
        sx, sy, sz = 0.03 * big, 0.016, 0.036 * big * (1.25 if style == "anime" else 1.0)
        p = on_face(rx, ry, rz, hz, s * ex, ez, out=-0.004)
        A(bp.ellipsoid(f"eye{s}", (sx, sy, sz), p, white, head))
        p2 = on_face(rx, ry, rz, hz, s * ex * 0.96, ez - 0.002, out=0.008)
        A(bp.ellipsoid(f"iris{s}", (sx * 0.72, 0.008, sz * 0.74), p2, iris, head))
        p3 = on_face(rx, ry, rz, hz, s * ex * 0.96, ez - 0.002, out=0.0135)
        A(bp.ellipsoid(f"pupil{s}", (sx * 0.36, 0.005, sz * 0.38), p3, dark, head))
        p4 = on_face(rx, ry, rz, hz, s * ex * 0.96 - 0.008, ez + sz * 0.3, out=0.017)
        A(ts.no_light(bp.ellipsoid(f"glint{s}", (0.006 * big,) * 3, p4, shine, head, segs=10, rings=6)))
        pb = on_face(rx, ry, rz, hz, s * ex, ez + sz + 0.022, out=0.002)
        o = A(bp.box(f"brow{s}", (0.05 * big, 0.01, 0.009), pb, brow, head, bevel=0.004))
        o.rotation_euler = (0, math.radians(-s * 10), 0)
    if style != "xray":
        A(bp.ellipsoid("nose", (0.013, 0.014, 0.014), on_face(rx, ry, rz, hz, 0, hz - rz * 0.28, out=0.004), skin, head))
        jc, jr = (-ry * 0.12, hz - rz * 0.42), (rx * 0.78, ry * 0.8, rz * 0.5)

        def front(x, z, out):                                    # the face surface: skull or jaw, whichever is further out
            y1 = on_face(rx, ry, rz, hz, x, z)[1]
            u = 1 - (x / jr[0]) ** 2 - ((z - jc[1]) / jr[2]) ** 2
            y2 = jc[0] - jr[1] * math.sqrt(u) if u > 0 else 0.0
            return (x, min(y1, y2) - out, z)
        smile = M("p_smile", (0.3, 0.06, 0.07), rough=0.5)
        for j in range(11):                                      # a smile: a line of beads along a shallow curve
            x = (j - 5) * 0.0055 * k
            A(bp.ellipsoid(f"mouth{j}", (0.0055, 0.004, 0.0038), front(x, hz - rz * 0.5 + 0.00055 * (j - 5) ** 2 * k, -0.001),
                           smile, head, segs=12, rings=8))
        A(hair_cap("hair", rx, ry, rz, hz, hair, head, fringe=0.32 if style == "cartoon" else 0.42))
    if style == "anime":                                         # spikes, and bangs falling over the forehead
        import random
        rnd = random.Random(11)
        for j in range(14):
            a = math.radians(-160 + 320 * j / 13)
            base = Vector((rx * 0.8 * math.sin(a), ry * 0.75 * math.cos(a) * 0.9 + 0.02, hz + rz * 0.55))
            tip = base + Vector((math.sin(a) * 0.09, math.cos(a) * 0.1 + 0.04, rnd.uniform(0.02, 0.09)))
            A(spike(f"spike{j}", base, tip, 0.04, hair, head))
        for j, x in enumerate((-0.07, -0.035, 0.0, 0.035, 0.07)):
            base = on_face(rx, ry, rz, hz, x * k * 0.9, hz + rz * 0.62, out=0.012)
            tip = (base[0] + x * 0.25, base[1] - 0.012, hz + rz * (0.12 + 0.06 * abs(j - 2)))
            A(spike(f"bang{j}", base, tip, 0.03, hair, head))
    for s in (-1, 1):
        sh = P[f"sh{s}"] = bp.pivot(f"sh{s}", (s * 0.21, 0, 0.44), chest)
        A(bp.capsule(f"sleeve{s}", 0.056, 0.15, (0, 0, -0.06), shirt, sh))
        A(bp.capsule(f"upper{s}", 0.05, 0.3, (0, 0, -0.16), skin, sh))
        el = P[f"el{s}"] = bp.pivot(f"el{s}", (0, 0, -0.31), sh)
        A(bp.ellipsoid(f"elbow{s}", (0.048,) * 3, (0, 0, 0), skin, el))
        A(bp.capsule(f"fore{s}", 0.045, 0.26, (0, 0, -0.13), skin, el))
        A(bp.ellipsoid(f"hand{s}", (0.042, 0.028, 0.066), (0, 0, -0.3), skin, el))
        o = A(bp.ellipsoid(f"thumb{s}", (0.012, 0.012, 0.03), (-s * 0.03, -0.012, -0.28), skin, el))
        o.rotation_euler = (0, math.radians(-s * 35), 0)
        hip = P[f"hip{s}"] = bp.pivot(f"hip{s}", (s * 0.09, 0, -0.03), pelvis)
        A(bp.capsule(f"thigh{s}", 0.082, 0.5, (0, 0, -0.22), pants, hip))
        kn = P[f"kn{s}"] = bp.pivot(f"kn{s}", (0, 0, -0.46), hip)
        A(bp.ellipsoid(f"knee{s}", (0.07,) * 3, (0, 0, 0), pants, kn))
        A(bp.capsule(f"shin{s}", 0.066, 0.42, (0, 0, -0.2), pants, kn))
        A(bp.box(f"shoe{s}", (0.1, 0.25, 0.08), (0, -0.045, -0.43), shoe, kn, bevel=0.035))
        A(bp.box(f"sole{s}", (0.104, 0.254, 0.022), (0, -0.045, -0.465), sole, kn, bevel=0.008))
    if style == "anime":
        add_outlines(parts)
    if style == "xray":
        xray_insides(P)
    return P, parts


def xray_insides(P):
    """Bones, brain, heart, lungs and stomach inside the glowing body."""
    ts.skeleton(P)
    bone = bp.mat("bone", (0.95, 0.92, 0.84), rough=0.45)
    for o in bpy.data.objects:
        if o.name.startswith("b_") and o.type == "MESH":
            o.data.materials.clear()
            o.data.materials.append(bone)
    ch, hd = P["chest"], P["head"]
    org = lambda n, c, r, at, parent: bp.ellipsoid(n, r, at, bp.mat(n, c, rough=0.4, sss=0.2), parent)
    org("brain", (0.95, 0.55, 0.6), (0.075, 0.085, 0.06), (0, 0.006, 0.16), hd)
    for s in (-1, 1):
        org(f"lung{s}", (0.95, 0.45, 0.5), (0.065, 0.06, 0.12), (s * 0.075, 0.0, 0.33), ch)
    org("heart", (0.85, 0.06, 0.08), (0.042, 0.04, 0.05), (-0.03, -0.035, 0.3), ch)
    org("stomach", (0.9, 0.6, 0.45), (0.06, 0.045, 0.045), (0.035, -0.02, 0.14), ch)


# ── studio still ─────────────────────────────────────────────────────────────
def studio(style, shot):
    sc = bk.new_scene(fps=24, res=(540, 960), samples=24, frames=1)
    sc.view_settings.view_transform = "Standard" if style == "anime" else "AgX"
    sc.cycles.transparent_max_bounces = 32
    bg = {"cartoon": (0.55, 0.72, 0.9), "anime": (0.98, 0.86, 0.6), "xray": (0.005, 0.012, 0.03)}[style]
    bp.world(sc, bg, 0.9 if style != "xray" else 1.0)
    floor = bp.mat("floor", tuple(c * 0.75 for c in bg), rough=0.7) if style != "anime" else toon("floor", tuple(c * 0.92 for c in bg))
    bp.box("floor", (30, 30, 0.1), (0, 0, -0.05), floor)
    if style == "xray":                                          # a lab grid on the floor
        grid = ts.emit("grid", (0.1, 0.5, 0.8), 1.2)
        for j in range(-8, 9):
            ts.no_light(bp.box(f"gx{j}", (0.006, 8, 0.002), (j * 0.4, 2, 0.001), grid))
            ts.no_light(bp.box(f"gy{j}", (8, 0.006, 0.002), (0, j * 0.4, 0.001), grid))
    bp.light("key", "AREA", (-1.8, -3.0, 3.0), 260, size=2.5, color=(1.0, 0.95, 0.9), aim=(0, 0, 1.0))
    bp.light("fill", "AREA", (2.4, -2.0, 1.6), 90, size=3.0, color=(0.85, 0.9, 1.0), aim=(0, 0, 1.0))
    bp.light("rim", "AREA", (1.2, 3.0, 2.8), 220, size=2.0, aim=(0, 0, 1.2))
    P, _ = build_person(style)
    P["root"].rotation_euler = (0, 0, math.radians(-12))
    ts.pose(P, 0, sh_1=(-8, 12, 0), sh1=(-150, 20, 0), el_1=(-14, 0, 0), el1=(-40, 0, 0), head=(4, 0, 6), chest=(0, 0, -3),
            hip=(0, 0, 0), kn=(0, 0, 0))
    if shot == "face":
        cam = bp.cam_free(sc, 50, (0.15, -1.15, 1.78), (0.0, 0, 1.74))
    else:
        cam = bp.cam_free(sc, 32, (0.35, -3.4, 1.05), (0, 0, 0.98))
    cam.data.dof.use_dof = False
    return sc


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    style, out = argv[0], argv[1]
    shot = argv[2] if len(argv) > 2 else "body"
    sc = studio(style, shot)
    sc.frame_set(0)
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print("saved", out)
