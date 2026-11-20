"""
blender_hero.py — the channel's recurring character, built from the owner's turnaround sheet (2026-11-16):
messy dark-brown hair, brown eyes, green hoodie over a grey tee, dark-blue jeans, plain dark trainers with white
soles (no brand stripes), a grey-brown backpack, a black wristband and a watch.

Cel-shaded like the drawing (flat colour bands from the surface normal, black inverted-hull outlines), so it reads
as the same character as the sheet. Same pivots as bp.build_dummy_v2 (root, pelvis, chest, head, sh+-1, el+-1,
hip+-1, kn+-1), so the What If timelines can drive him.

Run:  python blender_hero.py OUT_DIR        -> hero_front.png, hero_side.png, hero_back.png, hero_face.png
"""
import math
import os
import random
import sys

import bpy  # noqa: I001  (bpy first: it makes bmesh importable)
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_kit as bk          # noqa: E402
import blender_pitches as bp      # noqa: E402
import blender_tensec as ts       # noqa: E402
from blender_characters import add_outlines, hair_cap, on_face, spike   # noqa: E402

DOTS = []                          # every toon material's light-direction input, re-aimed per camera
STYLE = os.environ.get("JEMS_STYLE", "3d")   # owner 2026-11-16: "should not look like a drawing" -> real lighting

# lit-3D surface for each part, picked by name: roughness, subsurface, coat, metallic, bump (scale, strength, kind)
PBR = [
    (("skin",), dict(rough=0.48, sss=0.28)),
    (("hood", "tee", "band", "strap", "pack"), dict(rough=0.92, bump=(380, 0.35, "noise"))),
    (("jeans",), dict(rough=0.82, bump=(260, 0.45, "wave"))),
    (("hair", "brow", "lash"), dict(rough=0.42, coat=0.15, bump=(90, 0.6, "wave"))),
    (("shoe", "sole", "lace", "tread"), dict(rough=0.62, bump=(160, 0.2, "noise"))),
    (("white",), dict(rough=0.12, coat=0.7)),
    (("iris", "pupil"), dict(rough=0.15, coat=0.9)),
    (("smile", "tongue"), dict(rough=0.5, sss=0.2)),
    (("road",), dict(rough=0.95, bump=(55, 0.55, "noise"))),
    (("pave", "kerb"), dict(rough=0.9, bump=(30, 0.4, "noise"))),
    (("wall",), dict(rough=0.88, bump=(18, 0.25, "noise"))),
    (("glass",), dict(rough=0.04, coat=1.0)),
    (("frame", "paint"), dict(rough=0.55)),
    (("leaf",), dict(rough=0.8, sss=0.1, bump=(6, 0.5, "noise"))),
    (("bark", "wood"), dict(rough=0.72, bump=(40, 0.5, "wave"))),
    (("nail",), dict(rough=0.35, metal=1.0)),
    (("m_sole",), dict(rough=0.7, bump=(20, 0.4, "noise"))),
    (("m_pave",), dict(rough=0.85, bump=(14, 0.5, "noise"))),
]


def pbr(name, srgb):
    spec = next((v for keys, v in PBR if any(k_ in name for k_ in keys)), dict(rough=0.6))
    m = bp.mat(name, lin(srgb), rough=spec.get("rough", 0.6), sss=spec.get("sss", 0.0), coat=spec.get("coat", 0.0),
               metallic=spec.get("metal", 0.0))
    if spec.get("bump"):
        sc_, st, kind = spec["bump"]
        if kind == "noise":
            bp.add_bump(m, sc_, st, distance=0.002)
        else:                                                    # strands / weave / grain running one way
            nt = m.node_tree
            wave = nt.nodes.new("ShaderNodeTexWave")
            wave.inputs["Scale"].default_value, wave.inputs["Distortion"].default_value = sc_, 3.0
            wave.bands_direction = "Z"
            tc = nt.nodes.new("ShaderNodeTexCoord")
            nt.links.new(tc.outputs["Object"], wave.inputs["Vector"])
            bmp = nt.nodes.new("ShaderNodeBump")
            bmp.inputs["Strength"].default_value, bmp.inputs["Distance"].default_value = st, 0.002
            nt.links.new(wave.outputs["Fac"], bmp.inputs["Height"])
            nt.links.new(bmp.outputs["Normal"], nt.nodes["Principled BSDF"].inputs["Normal"])
    return m


def lin(rgb):
    """sRGB 0-255 -> linear 0-1 (colours picked off the sheet)."""
    f = lambda c: (c / 255) / 12.92 if c / 255 <= 0.04045 else ((c / 255 + 0.055) / 1.055) ** 2.4
    return tuple(f(c) for c in rgb)


def toon(name, srgb, shade=0.62, hi=True):
    """Three flat bands (shadow, base, a thin highlight), decided by the normal against a light direction.
    In the lit-3D style (default) this returns a real material instead."""
    if STYLE == "3d":
        return pbr(name, srgb)
    color = lin(srgb)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    dot = nt.nodes.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    nt.links.new(geo.outputs["Normal"], dot.inputs[0])
    DOTS.append(dot.inputs[1])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "CONSTANT"
    e0, e1 = ramp.color_ramp.elements
    e0.position, e0.color = 0.0, (*[c * shade for c in color], 1)
    e1.position, e1.color = 0.18, (*color, 1)
    if hi:
        h = ramp.color_ramp.elements.new(0.9)
        h.color = (*[min(1.0, c * 1.35 + 0.02) for c in color], 1)
    nt.links.new(dot.outputs["Value"], ramp.inputs["Fac"])
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(ramp.outputs["Color"], em.inputs["Color"])
    nt.links.new(em.outputs[0], nt.nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
    return m


def flat(name, srgb, strength=1.0):
    if STYLE == "3d":
        return pbr(name, srgb)
    return ts.emit(name, lin(srgb), strength)


def soft(o, level=2):
    m = o.modifiers.new("subsurf", "SUBSURF")
    m.levels = m.render_levels = level
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def line(name, pts, r, mat, parent):
    """A drawn line (smile, lashes): a NURBS curve through pts with a round bevel."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions, cu.bevel_depth, cu.bevel_resolution = "3D", r, 2
    sp = cu.splines.new("NURBS")
    sp.points.add(len(pts) - 1)
    for p, q in zip(sp.points, pts):
        p.co = (*q, 1.0)
    sp.order_u, sp.use_endpoint_u = min(4, len(pts)), True
    cu.materials.append(mat)
    return bp.link(bpy.data.objects.new(name, cu), parent)


def slab(name, length, width, z0, h, top, cy, mat, parent, n=2.6, segs=56, h_toe=None):
    """A foot-shaped slab: a rounded-rectangle outline (superellipse, exponent n) extruded up by h, its top ring
    scaled by `top` (x, y) so the sides lean in. Centred at y=cy, bottom at z0."""
    import bmesh
    bm = bmesh.new()
    rings = []
    for z, (sx, sy) in ((z0, (1.0, 1.0)), (z0 + h, top)):
        ring = []
        for j in range(segs):
            t = 2 * math.pi * j / segs
            c, si = math.cos(t), math.sin(t)
            x = width / 2 * math.copysign(abs(c) ** (2 / n), c) * sx
            y = length / 2 * math.copysign(abs(si) ** (2 / n), si) * sy
            if y < 0:                                            # the toe end a touch wider than the heel
                x *= 1.0 + 0.08 * (-y / (length / 2))
            if z > z0 and h_toe is not None:                     # higher at the heel, sloping down to the toe
                u = (y / (length / 2) * (1 / sy) + 1) / 2           # 0 at the toe .. 1 at the heel
                z = z0 + h_toe + (h - h_toe) * min(1.0, max(0.0, u)) ** 0.8
            ring.append(bm.verts.new((x, cy + y, z)))
        rings.append(ring)
    for j in range(segs):
        a, b = rings[0][j], rings[0][(j + 1) % segs]
        bm.faces.new((a, b, rings[1][(j + 1) % segs], rings[1][j]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    o = bp.link(bpy.data.objects.new(name, me), parent)
    bv = o.modifiers.new("bevel", "BEVEL")
    bv.width, bv.segments, bv.limit_method = min(0.012, h * 0.35), 4, "ANGLE"
    for p_ in me.polygons:
        p_.use_smooth = True
    return o


def build_hero(bag=False):
    C = {k: toon(f"h_{k}", v) for k, v in dict(
        skin=(244, 206, 178), hood=(60, 96, 66), hood_dk=(46, 76, 52), tee=(178, 178, 175), jeans=(56, 84, 130),
        jeans_dk=(42, 64, 104), hair=(58, 40, 30), shoe=(72, 72, 70), sole=(236, 233, 226), lace=(200, 200, 196),
        pack=(112, 104, 97), pack_dk=(96, 89, 83), strap=(38, 38, 40), band=(30, 30, 32), brow=(52, 36, 28)).items()}
    C["hair"] = toon("h_hair2", (58, 40, 30), shade=0.6, hi=False)
    C["white"] = toon("h_white", (250, 250, 248), shade=0.85, hi=False)
    iris, dark = flat("h_iris", (122, 80, 44)), flat("h_pupil", (24, 16, 12))
    lash, smile = flat("h_lash", (30, 20, 16)), flat("h_smile", (130, 70, 60))
    shine = ts.emit("h_shine", (1.0, 1.0, 1.0), 4.0)
    outlined, P = [], {}
    O_ = lambda o: outlined.append(o) or o

    root = P["root"] = bp.pivot("hero", (0, 0, 0))
    pelvis = P["pelvis"] = bp.pivot("pelvis", (0, 0, 0.95), root)
    O_(soft(bp.box("hips", (0.33, 0.2, 0.2), (0, 0, 0.0), C["jeans"], pelvis, bevel=0.06), 1))
    chest = P["chest"] = bp.pivot("chest", (0, 0, 0.1), pelvis)

    # hoodie over a grey tee
    O_(soft(bp.box("hoodie", (0.38, 0.22, 0.47), (0, 0, 0.215), C["hood"], chest, bevel=0.09), 1))
    O_(soft(bp.box("hem", (0.375, 0.218, 0.055), (0, 0, -0.03), C["hood_dk"], chest, bevel=0.02), 1))
    O_(soft(bp.box("tee", (0.355, 0.205, 0.06), (0, 0, -0.07), C["tee"], chest, bevel=0.02), 1))
    O_(soft(bp.box("pocket", (0.25, 0.02, 0.13), (0, -0.108, 0.1), C["hood"], chest, bevel=0.025), 1))
    for s in (-1, 1):
        O_(bp.ellipsoid(f"shcap{s}", (0.085, 0.115, 0.07), (s * 0.165, 0, 0.425), C["hood"], chest))
    bpy.ops.mesh.primitive_torus_add(major_radius=0.08, minor_radius=0.032, major_segments=48, minor_segments=16)
    collar = bpy.context.active_object
    collar.name, collar.parent = "collar", chest
    collar.location, collar.scale = (0, 0.005, 0.47), (1.12, 1.0, 0.75)
    collar.data.materials.append(C["hood"])
    for p in collar.data.polygons:
        p.use_smooth = True
    O_(collar)
    O_(bp.ellipsoid("hood", (0.14, 0.065, 0.12), (0, 0.11, 0.43), C["hood"], chest))
    O_(bp.ellipsoid("tee_v", (0.05, 0.012, 0.03), (0, -0.068, 0.455), C["tee"], chest))
    for s in (-1, 1):                                            # drawstrings
        bp.cylinder(f"string{s}", 0.0045, 0.14, (s * 0.024, -0.1, 0.38), C["tee"], chest, segs=10)
        bp.cylinder(f"aglet{s}", 0.006, 0.02, (s * 0.024, -0.1, 0.305), C["band"], chest, segs=10)
    bp.cylinder("neck", 0.046, 0.12, (0, 0, 0.5), C["skin"], chest, segs=32)

    if bag:
        backpack(C, chest, O_)

    # head
    head = P["head"] = bp.pivot("head", (0, 0, 0.53), chest)
    face_rig(P, C, head, O_, dict(iris=iris, dark=dark, shine=shine, lash=lash, smile=smile))
    hair(C, head, O_)
    limbs(P, C, chest, pelvis, O_)
    add_outlines(outlined, width=0.0045)
    return P


def backpack(C, chest, O_):
    O_(soft(bp.box("pack", (0.3, 0.14, 0.38), (0, 0.19, 0.23), C["pack"], chest, bevel=0.06), 1))
    O_(soft(bp.box("pack_pocket", (0.24, 0.05, 0.16), (0, 0.265, 0.13), C["pack_dk"], chest, bevel=0.03), 1))
    bp.box("zip", (0.2, 0.004, 0.006), (0, 0.292, 0.19), C["band"], chest)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.035, minor_radius=0.01, major_segments=24, minor_segments=8)
    handle = bpy.context.active_object
    handle.name, handle.parent = "handle", chest
    handle.location, handle.rotation_euler = (0, 0.18, 0.43), (0, math.radians(90), 0)
    handle.data.materials.append(C["strap"])
    for s in (-1, 1):
        o = O_(bp.box(f"strap_top{s}", (0.05, 0.25, 0.018), (s * 0.115, 0.005, 0.47), C["strap"], chest, bevel=0.006))
        o.rotation_euler = (math.radians(-8), 0, 0)
        O_(bp.box(f"strap_front{s}", (0.045, 0.02, 0.33), (s * 0.13, -0.115, 0.29), C["strap"], chest, bevel=0.006))
        bp.box(f"buckle{s}", (0.05, 0.024, 0.025), (s * 0.13, -0.117, 0.16), C["tee"], chest, bevel=0.004)


HEAD = {}


def face_rig(P, C, head, O_, M):
    """Head, eyes that blink (P["eyes"][s] scale z), brows that lift (P["brows"]), a mouth that opens (P["mouth"]:
    scale z 0.06 shut .. 1 wide open; scale x below 1 rounds it into an 'oo')."""
    iris, dark, shine, lash, smile = M["iris"], M["dark"], M["shine"], M["lash"], M["smile"]
    k = 1.12
    rx, ry, rz = 0.098 * k, 0.108 * k, 0.122 * k
    hz = rz * 0.92
    O_(bp.ellipsoid("skull", (rx, ry, rz), (0, 0, hz), C["skin"], head, segs=64, rings=40))
    O_(bp.ellipsoid("jaw", (rx * 0.74, ry * 0.8, rz * 0.5), (0, -ry * 0.14, hz - rz * 0.45), C["skin"], head))
    for s in (-1, 1):
        O_(bp.ellipsoid(f"ear{s}", (0.013, 0.028, 0.038), (s * rx * 0.98, 0.006, hz - rz * 0.05), C["skin"], head))
    jc, jr = (-ry * 0.14, hz - rz * 0.45), (rx * 0.74, ry * 0.8, rz * 0.5)

    def front(x, z, out=0.0):
        y1 = on_face(rx, ry, rz, hz, x, z)[1]
        u = 1 - (x / jr[0]) ** 2 - ((z - jc[1]) / jr[2]) ** 2
        y2 = jc[0] - jr[1] * math.sqrt(u) if u > 0 else 0.0
        return Vector((x, min(y1, y2) - out, z))
    ez = hz - rz * 0.02

    def under(o, piv):                                           # re-parent a head part to a pivot on the head
        o.location = Vector(o.location) - Vector(piv.location)
        o.parent = piv
        return o
    P["eyes"], P["brows"] = {}, {}
    for s in (-1, 1):
        ex = s * rx * 0.4
        ep = P["eyes"][s] = bp.pivot(f"eyepiv{s}", tuple(front(ex, ez, -0.004)), head)
        under(O_(bp.ellipsoid(f"eye{s}", (0.024, 0.012, 0.017), front(ex, ez, -0.006), C["white"], head)), ep)
        under(bp.ellipsoid(f"iris{s}", (0.0135, 0.006, 0.0165), front(ex * 0.97, ez - 0.001, 0.003), iris, head), ep)
        under(bp.ellipsoid(f"pupil{s}", (0.0065, 0.004, 0.008), front(ex * 0.97, ez - 0.001, 0.006), dark, head), ep)
        under(ts.no_light(bp.ellipsoid(f"glint{s}", (0.0035,) * 3, front(ex * 0.97 - 0.005, ez + 0.006, 0.009), shine,
                                       head, segs=8, rings=6)), ep)
        under(line(f"lash{s}", [front(ex - 0.026, ez + 0.006, 0.004), front(ex - 0.008, ez + 0.017, 0.006),
                                front(ex + 0.012, ez + 0.017, 0.006), front(ex + 0.027, ez + 0.009, 0.004)], 0.0028,
                   lash, head), ep)
        bpiv = P["brows"][s] = bp.pivot(f"browpiv{s}", (0, 0, 0), head)
        under(line(f"brow{s}", [front(ex - 0.026, ez + 0.032, 0.003), front(ex, ez + 0.04, 0.003),
                                front(ex + 0.026, ez + 0.036, 0.003)], 0.0042, C["brow"], head), bpiv)
    bp.ellipsoid("nose", (0.009, 0.012, 0.012), front(0, hz - rz * 0.26, 0.002), C["skin"], head)
    line("smile", [front(-0.024, hz - rz * 0.5, 0.0), front(-0.01, hz - rz * 0.555, 0.001),
                   front(0.01, hz - rz * 0.555, 0.001), front(0.024, hz - rz * 0.5, 0.0)], 0.0022, smile, head)
    mz = hz - rz * 0.535
    mp = P["mouth"] = bp.pivot("mouthpiv", tuple(front(0, mz, -0.002)), head)
    under(bp.ellipsoid("mouth_in", (0.021, 0.007, 0.013), front(0, mz, -0.002), M["dark"], head), mp)
    under(bp.box("teeth", (0.026, 0.006, 0.0045), front(0, mz + 0.0085, -0.003), C["white"], head), mp)
    tongue = bp.mat("h_tongue", (0.7, 0.25, 0.25), rough=0.6)
    under(bp.ellipsoid("tongue", (0.012, 0.005, 0.004), front(0, mz - 0.008, -0.004), tongue, head), mp)
    mp.scale = (1.0, 1.0, 0.06)
    HEAD.update(rx=rx, ry=ry, rz=rz, hz=hz)


def hair(C, head, O_):
    rx, ry, rz, hz = HEAD["rx"], HEAD["ry"], HEAD["rz"], HEAD["hz"]

    def front(x, z, out=0.0):
        return Vector(on_face(rx, ry, rz, hz, x, z, out))

    # messy hair: a cap, clumps all over it, and bangs falling over the forehead
    O_(hair_cap("hair_cap", rx, ry, rz, hz, C["hair"], head, fringe=0.42, clumps=0.02, seed=7))
    rnd = random.Random(42)
    n = 0
    for j in range(110):
        a = rnd.uniform(-math.pi, math.pi)                        # around the head; 0 = straight back
        e = rnd.uniform(-0.1, 1.45)                              # up from the ear line
        d = Vector((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e)))
        if d.y < -0.35 and d.z < 0.75:                           # leave the face to the bangs
            continue
        base = Vector((d.x * rx * 0.92, d.y * ry * 0.92 + 0.008, hz + 0.012 + d.z * rz * 0.95))
        out = Vector((d.x * 1.1, d.y + 0.35, d.z * 0.3 - 0.25)).normalized()   # messy, falling back and down
        L = rnd.uniform(0.045, 0.085)
        tip = base + out * L + Vector((rnd.uniform(-0.02, 0.02), 0.0, rnd.uniform(-0.015, 0.02)))
        O_(spike(f"clump{n}", base, tip, rnd.uniform(0.032, 0.05), C["hair"], head))
        n += 1
    for j, x in enumerate((-0.07, -0.045, -0.02, 0.005, 0.03, 0.055, 0.075)):
        base = front(x * 0.85, hz + rz * 0.72, -0.004)
        tip = (x * 1.05 + rnd.uniform(-0.012, 0.012), front(x, hz + rz * 0.3)[1] - 0.012, hz + rz * rnd.uniform(0.2, 0.34))
        O_(spike(f"bang{j}", base, tip, rnd.uniform(0.026, 0.034), C["hair"], head))



def limbs(P, C, chest, pelvis, O_):
    # arms: sleeves pushed up to just below the elbow, forearms bare
    for s in (-1, 1):
        sh = P[f"sh{s}"] = bp.pivot(f"sh{s}", (s * 0.205, 0, 0.43), chest)
        O_(bp.capsule(f"sleeve{s}", 0.062, 0.34, (0, 0, -0.15), C["hood"], sh))
        el = P[f"el{s}"] = bp.pivot(f"el{s}", (0, 0, -0.31), sh)
        O_(bp.ellipsoid(f"scrunch{s}", (0.064, 0.064, 0.07), (0, 0, -0.03), C["hood"], el))
        bpy.ops.mesh.primitive_torus_add(major_radius=0.05, minor_radius=0.014, major_segments=32, minor_segments=10)
        cuff = bpy.context.active_object
        cuff.name, cuff.parent, cuff.location = f"cuff{s}", el, (0, 0, -0.09)
        cuff.data.materials.append(C["hood_dk"])
        O_(cuff)
        O_(bp.capsule(f"fore{s}", 0.041, 0.21, (0, 0, -0.17), C["skin"], el))
        if s == 1:                                               # wristband on one arm, a watch on the other
            O_(bp.cylinder(f"band{s}", 0.045, 0.024, (0, 0, -0.245), C["band"], el, segs=24))
        else:
            O_(bp.cylinder(f"strapw{s}", 0.043, 0.016, (0, 0, -0.245), C["band"], el, segs=24))
            O_(bp.box(f"watch{s}", (0.012, 0.03, 0.03), (s * 0.044, 0, -0.245), C["band"], el, bevel=0.004))
        O_(soft(bp.box(f"palm{s}", (0.046, 0.08, 0.085), (0, 0, -0.3), C["skin"], el, bevel=0.018), 1))
        for q, y in enumerate((-0.027, -0.009, 0.009, 0.027)):
            o = O_(bp.capsule(f"finger{s}{q}", 0.011, 0.06 - abs(q - 1.5) * 0.007, (0, y, -0.36), C["skin"], el))
            o.rotation_euler = (0, math.radians(-s * 10), 0)
        o = O_(bp.capsule(f"thumb{s}", 0.011, 0.06, (-s * 0.012, -0.045, -0.31), C["skin"], el))
        o.rotation_euler = (math.radians(25), 0, 0)

        # legs: straight dark jeans with a turned hem, plain trainers
        hip = P[f"hip{s}"] = bp.pivot(f"hip{s}", (s * 0.09, 0, -0.03), pelvis)
        O_(bp.capsule(f"thigh{s}", 0.08, 0.5, (0, 0, -0.22), C["jeans"], hip))
        kn = P[f"kn{s}"] = bp.pivot(f"kn{s}", (0, 0, -0.46), hip)
        O_(bp.ellipsoid(f"knee{s}", (0.068,) * 3, (0, 0, 0), C["jeans"], kn))
        O_(bp.capsule(f"shin{s}", 0.064, 0.4, (0, 0, -0.19), C["jeans"], kn))
        O_(bp.cylinder(f"jhem{s}", 0.066, 0.03, (0, 0, -0.38), C["jeans_dk"], kn, segs=32))
        # a trainer: a rounded sole that follows the foot (round toe, round heel), the upper on it, a toe cap
        O_(slab(f"sole{s}", 0.33, 0.112, -0.496, 0.032, (1.0, 1.0), -0.07, C["sole"], kn))
        O_(slab(f"shoe{s}", 0.31, 0.102, -0.466, 0.092, (0.8, 0.9), -0.064, C["shoe"], kn, h_toe=0.04))
        O_(bp.ellipsoid(f"toe{s}", (0.046, 0.06, 0.026), (0, -0.165, -0.445), C["shoe"], kn))
        for q in range(4):
            bp.box(f"lace{s}{q}", (0.05, 0.008, 0.006), (0, -0.05 - q * 0.025, -0.385 + q * -0.008), C["lace"], kn)
        bow = P.setdefault("bows", {})[s] = bp.pivot(f"bow{s}", (0, -0.085, -0.4), kn)    # a tied bow on each shoe
        for q in (-1, 1):
            bpy.ops.mesh.primitive_torus_add(major_radius=0.026, minor_radius=0.006, major_segments=20, minor_segments=6)
            loop = bpy.context.active_object
            loop.name, loop.parent = f"loop{s}{q}", bow
            loop.location, loop.rotation_euler, loop.scale = (q * 0.02, 0, 0.004), (math.radians(80), 0, 0), (1.0, 0.7, 1)
            loop.data.materials.append(C["lace"])
            end = bp.box(f"lend{s}{q}", (0.006, 0.006, 0.05), (q * 0.012, -0.01, -0.02), C["lace"], bow)
            end.rotation_euler = (math.radians(40), math.radians(q * 25), 0)
    phone = P["phone"] = bp.pivot("phone", (-0.03, -0.03, -0.31), P["el-1"],
                                  rot=(math.radians(90), 0, 0))       # in his right hand, as drawn, along the palm
    bp.box("phone_body", (0.012, 0.075, 0.15), (0, 0, 0), C["band"], phone, bevel=0.006)
    bp.box("phone_screen", (0.002, 0.066, 0.135), (-0.0066, 0, 0), ts.emit("h_screen", (0.25, 0.45, 0.8), 1.2), phone)


def studio():
    sc = bk.new_scene(fps=24, res=(540, 960), samples=16, frames=1)
    sc.view_settings.view_transform, sc.view_settings.look = "Standard", "None"
    sc.cycles.transparent_max_bounces = 32
    bp.world(sc, lin((150, 150, 150)), 1.0)
    shadow = ts.emit("h_floorshadow", lin((120, 120, 120)), 1.0)
    o = bp.cylinder("shadow", 0.32, 0.002, (0, -0.02, 0.0), shadow)
    o.scale = (1.0, 0.7, 1.0)
    P = build_hero()
    ts.pose(P, 0, sh=(2, 9, 0), el=(-12, 0, 0), head=(-2, 0, 0), chest=(0, 0, 0), hip=(0, 0, 0), kn=(0, 0, 0))
    if os.environ.get("HERO_TALK"):                              # look test: mouth open, brows up
        P["mouth"].scale = (0.85, 1.0, float(os.environ["HERO_TALK"]))
        for b in P["brows"].values():
            b.location.z = 0.006
    return sc, P


VIEWS = {  # camera position, look-at, toon light direction (from the camera side, a little above and left)
    "front": ((0, -4.4, 1.0), (0, 0, 0.93)),
    "side": ((4.4, 0, 1.0), (0, 0, 0.93)),
    "back": ((0, 4.4, 1.0), (0, 0, 0.93)),
    "face": ((0.18, -1.2, 1.68), (0, 0, 1.66)),
}

if __name__ == "__main__":
    out = (sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])[0]
    os.makedirs(out, exist_ok=True)
    sc, P = studio()
    cam = None
    for name, (loc, at) in VIEWS.items():
        d = (Vector(loc) - Vector(at)).normalized()
        side = d.cross(Vector((0, 0, 1))).normalized()
        light = (d + side * 0.45 + Vector((0, 0, 0.7))).normalized()
        for inp in DOTS:
            inp.default_value = tuple(light)
        if cam is None:
            cam = bp.cam_free(sc, 42, loc, at)
        else:
            bp.aim(cam, Vector(loc), Vector(at))
        cam.data.lens = 70 if name == "face" else 42
        cam.data.dof.use_dof = False
        sc.render.filepath = os.path.join(out, f"hero_{name}.png")
        bpy.ops.render.render(write_still=True)
        print("saved", sc.render.filepath, flush=True)
