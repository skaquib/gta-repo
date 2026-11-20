"""
blender_panda_scene.py — "Being a Panda Is a Scam 🐼" (owner-approved script A, 2026-11-05).

A tired, grumpy giant panda (stylised 3D with real fur, not a cartoon) slumped against a tree in a sunny bamboo
forest, next to a pile of bamboo taller than itself. Everything is built from code and rendered with Cycles on the
CPU, so it costs Rs 0.

The panda is built from soft shapes parented to pivots (body, head, jaw, arms, eyelids), so the animation step can
keyframe chewing, blinking, pointing and shrugging without a skinned rig; the fur hides the joins.

  /root/.venvs/blender/bin/python blender_panda_scene.py OUT_DIR still [FRAME ...]
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Euler, Matrix, Vector  # noqa: E402

import blender_kit as bk  # noqa: E402
from blender_critic_scene import leaf_mesh  # noqa: E402

FPS = 24
EYE_R = 0.03
rng = random.Random(7)


# ── helpers ───────────────────────────────────────────────────────────────────
def link(ob, parent=None):
    bpy.context.scene.collection.objects.link(ob)
    if parent is not None:
        ob.parent = parent
    return ob


def pivot(name, loc, parent=None, rot=(0, 0, 0)):
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = 0.05
    e.location = loc
    e.rotation_euler = rot
    return link(e, parent)


def blob(name, radii, center=(0, 0, 0), deform=None, segs=72, rings=36):
    """An ellipsoid with the shape baked into the vertices (object scale stays 1, so fur keeps its length)."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=1.0)
    for v in bm.verts:
        x, y, z = v.co
        if deform:
            x, y, z = deform(x, y, z)
        v.co = (center[0] + x * radii[0], center[1] + y * radii[1], center[2] + z * radii[2])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    return bpy.data.objects.new(name, me)


def smooth(e0, e1, x):
    t = min(1.0, max(0.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def vgroup(ob, name, fn):
    g = ob.vertex_groups.new(name=name)
    for v in ob.data.vertices:
        w = fn(v.co)
        if w > 0:
            g.add([v.index], w, "REPLACE")
    return g


def paint_faces(ob, fn, idx):
    """Material index idx on faces where fn(face centre) > 0.5."""
    for p in ob.data.polygons:
        if fn(p.center) > 0.5:
            p.material_index = idx


def fur(ob, name, mat, count, children, length, align=(0, 0, -0.5), density=None, lengthg=None,
        clump=0.3, rough=0.0035, radius=0.0011, seed=0, step=3):
    if mat.name not in [m.name for m in ob.data.materials]:
        ob.data.materials.append(mat)
    mod = ob.modifiers.new(name, "PARTICLE_SYSTEM")
    psys = mod.particle_system
    psys.seed = seed
    ps = psys.settings
    ps.name = name
    ps.type = "HAIR"
    ps.count = count
    ps.emit_from = "FACE"
    ps.use_even_distribution = True
    ps.use_emit_random = True
    # Blender stores hair length as velocity (length = 4 x |normal + align + random| velocity), so every
    # direction term is scaled to the wanted length; unscaled values made 7 m strands.
    k = length / 4 / math.sqrt(1 + sum(c * c for c in align))
    ps.normal_factor = k
    ps.object_align_factor = tuple(c * k for c in align)
    ps.factor_random = 0.15 * k
    ps.length_random = 0.35
    ps.child_type = "INTERPOLATED"
    ps.child_percent = 1
    ps.rendered_child_count = children
    ps.child_radius = 0.2
    ps.clump_factor = clump
    ps.clump_shape = 0.4
    ps.roughness_1 = rough
    ps.roughness_1_size = 1.0
    ps.roughness_endpoint = rough * 0.6
    ps.roughness_2 = rough * 0.8
    ps.roughness_2_threshold = 0.7
    ps.child_length = 1.0
    ps.child_length_threshold = 0.2
    ps.display_step = 2
    ps.render_step = step
    ps.radius_scale = radius
    ps.root_radius = 1.0
    ps.tip_radius = 0.12
    ps.shape = -0.2
    ps.material_slot = mat.name
    if density:
        psys.vertex_group_density = density
    if lengthg:
        psys.vertex_group_length = lengthg
    return psys


# ── materials ─────────────────────────────────────────────────────────────────
def mat_fur(name, melanin, redness, rough=0.34, rand=0.12):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    N.remove(N["Principled BSDF"])
    h = N.new("ShaderNodeBsdfHairPrincipled")
    h.parametrization = "MELANIN"
    h.inputs["Melanin"].default_value = melanin
    h.inputs["Melanin Redness"].default_value = redness
    h.inputs["Roughness"].default_value = rough
    h.inputs["Radial Roughness"].default_value = 0.45
    h.inputs["Coat"].default_value = 0.15
    h.inputs["Random Color"].default_value = rand
    h.inputs["Random Roughness"].default_value = 0.2
    L.new(h.outputs[0], N["Material Output"].inputs["Surface"])
    return m


def mat_eye():
    """Glossy dark-brown iris and black pupil facing the eyeball's local -Y (the eyeball tracks the camera)."""
    m, b, nt = bk._principled("eye")
    N, L = nt.nodes, nt.links
    b.inputs["Roughness"].default_value = 0.05
    b.inputs["Coat Weight"].default_value = 1.0
    b.inputs["Coat Roughness"].default_value = 0.02
    tc, sep = N.new("ShaderNodeTexCoord"), N.new("ShaderNodeSeparateXYZ")
    L.new(tc.outputs["Object"], sep.inputs[0])
    comb = N.new("ShaderNodeCombineXYZ")
    L.new(sep.outputs["X"], comb.inputs["X"])
    L.new(sep.outputs["Z"], comb.inputs["Y"])
    ln = N.new("ShaderNodeVectorMath")
    ln.operation = "LENGTH"
    L.new(comb.outputs[0], ln.inputs[0])
    nrm = N.new("ShaderNodeMath")
    nrm.operation = "DIVIDE"
    nrm.inputs[1].default_value = EYE_R           # 0 at the pupil centre, 1 at the eyeball's silhouette
    L.new(ln.outputs["Value"], nrm.inputs[0])
    ramp = N.new("ShaderNodeValToRGB")
    L.new(nrm.outputs[0], ramp.inputs["Fac"])
    e = ramp.color_ramp.elements
    e[0].position, e[0].color = 0.0, (0.003, 0.002, 0.002, 1)          # pupil
    e[1].position, e[1].color = 0.80, (0.5, 0.46, 0.4, 1)               # sclera at the corners
    for pos, col in ((0.30, (0.004, 0.003, 0.002, 1)), (0.34, (0.30, 0.15, 0.05, 1)),
                     (0.58, (0.17, 0.08, 0.03, 1)), (0.68, (0.03, 0.018, 0.01, 1)), (0.74, (0.03, 0.018, 0.01, 1))):
        el = e.new(pos)
        el.color = col
    L.new(ramp.outputs["Color"], b.inputs["Base Color"])
    return m


def mat_bark():
    """Furrowed bark: stretched noise for vertical ridges, dark grooves, mossy patches low down."""
    m, b, nt = bk._principled("bark")
    N, L = nt.nodes, nt.links
    b.inputs["Roughness"].default_value = 0.9
    tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (14, 14, 1.2)
    L.new(tc.outputs["Object"], mp.inputs["Vector"])
    nz = N.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 2.5
    nz.inputs["Detail"].default_value = 10
    nz.inputs["Roughness"].default_value = 0.65
    L.new(mp.outputs[0], nz.inputs["Vector"])
    ramp = N.new("ShaderNodeValToRGB")
    e = ramp.color_ramp.elements
    e[0].position, e[0].color = 0.38, (0.025, 0.018, 0.012, 1)
    e[1].position, e[1].color = 0.62, (0.26, 0.2, 0.14, 1)
    L.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    moss_n = N.new("ShaderNodeTexNoise")
    moss_n.inputs["Scale"].default_value = 4.0
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(tc.outputs["Object"], sep.inputs[0])
    low = N.new("ShaderNodeMapRange")
    low.inputs["From Min"].default_value = 1.6
    low.inputs["From Max"].default_value = 0.2
    L.new(sep.outputs["Z"], low.inputs["Value"])
    mm = N.new("ShaderNodeMath")
    mm.operation = "MULTIPLY"
    L.new(low.outputs["Result"], mm.inputs[0])
    L.new(moss_n.outputs["Fac"], mm.inputs[1])
    mossr = N.new("ShaderNodeMapRange")
    mossr.inputs["From Min"].default_value = 0.35
    mossr.inputs["From Max"].default_value = 0.5
    L.new(mm.outputs[0], mossr.inputs["Value"])
    mix = N.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    L.new(mossr.outputs["Result"], mix.inputs["Factor"])
    L.new(ramp.outputs["Color"], mix.inputs[6])
    mix.inputs[7].default_value = (0.08, 0.16, 0.03, 1)
    L.new(mix.outputs[2], b.inputs["Base Color"])
    bump = N.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 1.0
    bump.inputs["Distance"].default_value = 0.03
    L.new(nz.outputs["Fac"], bump.inputs["Height"])
    L.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def mat_ground():
    m, b, nt = bk._principled("ground")
    N, L = nt.nodes, nt.links
    b.inputs["Roughness"].default_value = 0.9
    nz = N.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 1.6
    nz.inputs["Detail"].default_value = 6
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.42
    ramp.color_ramp.elements[0].color = (0.16, 0.11, 0.06, 1)
    ramp.color_ramp.elements[1].position = 0.62
    ramp.color_ramp.elements[1].color = (0.13, 0.22, 0.05, 1)
    L.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    fine = N.new("ShaderNodeTexNoise")
    fine.inputs["Scale"].default_value = 60.0
    mix = N.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 0.35
    L.new(ramp.outputs["Color"], mix.inputs[6])
    L.new(fine.outputs["Color"], mix.inputs[7])
    L.new(mix.outputs[2], b.inputs["Base Color"])
    bump = N.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.5
    L.new(fine.outputs["Fac"], bump.inputs["Height"])
    L.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def mat_culm(name, color):
    """Bamboo stalk with node rings from the object's local Z (no extra geometry needed)."""
    m, b, nt = bk._principled(name)
    N, L = nt.nodes, nt.links
    b.inputs["Roughness"].default_value = 0.3
    b.inputs["Coat Weight"].default_value = 0.4
    tc, sep = N.new("ShaderNodeTexCoord"), N.new("ShaderNodeSeparateXYZ")
    L.new(tc.outputs["Object"], sep.inputs[0])
    w = N.new("ShaderNodeMath")
    w.operation = "PINGPONG"
    w.inputs[1].default_value = 0.17
    L.new(sep.outputs["Z"], w.inputs[0])
    ring = N.new("ShaderNodeMapRange")
    ring.inputs["From Min"].default_value = 0.0
    ring.inputs["From Max"].default_value = 0.012
    ring.inputs["To Min"].default_value = 1.0
    ring.inputs["To Max"].default_value = 0.0
    L.new(w.outputs[0], ring.inputs["Value"])
    mix = N.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    L.new(ring.outputs["Result"], mix.inputs["Factor"])
    mix.inputs[6].default_value = (*color, 1)
    mix.inputs[7].default_value = (min(1, color[0] * 2.2 + 0.12), min(1, color[1] * 1.4 + 0.08), color[2] * 1.5, 1)
    L.new(mix.outputs[2], b.inputs["Base Color"])
    bump = N.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.6
    bump.inputs["Distance"].default_value = 0.004
    L.new(ring.outputs["Result"], bump.inputs["Height"])
    L.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def culm(name, r, length, mat, segs=20):
    """A bamboo stalk along local +Z from the origin."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r * 0.9, depth=length)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, length / 2))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(mat)
    return bpy.data.objects.new(name, me)


def aim(ob, direction, axis="Z"):
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = Vector(direction).normalized().to_track_quat(axis, "Y")


# ── the panda ─────────────────────────────────────────────────────────────────
def build_panda():
    white_fur = mat_fur("fur_white", 0.10, 0.75, rough=0.32)
    black_fur = mat_fur("fur_black", 0.97, 0.35, rough=0.40, rand=0.05)
    skin_w = bk.mat_basic("skin_white", (0.62, 0.58, 0.52), rough=0.8)
    skin_b = bk.mat_basic("skin_black", (0.012, 0.011, 0.011), rough=0.6)
    nose_m = bk.mat_basic("nose", (0.01, 0.01, 0.012), rough=0.22, coat=0.7)
    pad_m = bk.mat_basic("pads", (0.01, 0.009, 0.009), rough=0.85)
    lid_m = bk.mat_basic("lid", (0.07, 0.05, 0.042), rough=0.35, coat=0.3)
    mouth_m = bk.mat_basic("mouth", (0.03, 0.008, 0.01), rough=0.5)
    P = {}

    root = pivot("panda_root", (0, 0, 0))
    body_p = pivot("body_p", (0, 0, 0), root)
    P["root"], P["body"] = root, body_p

    # body: a pear (wider at the bottom); white with a black band over the shoulders
    BR = (0.34, 0.30, 0.40)
    body = link(blob("body", BR, (0, 0, 0.38),
                     lambda x, y, z: (x * (1 - 0.2 * z), y * (1 - 0.16 * z), z)), body_p)
    body.data.materials.append(skin_w)
    body.data.materials.append(skin_b)

    def band(co):
        u, v, w = co.x / BR[0], co.y / BR[1], (co.z - 0.38) / BR[2]
        side = smooth(0.30, 0.48, abs(u)) * smooth(0.25, 0.42, w)
        back = smooth(-0.25, 0.1, v) * smooth(0.32, 0.45, w) * (1 - smooth(0.80, 0.9, w))
        return max(side, back)

    vgroup(body, "black", band)
    vgroup(body, "white", lambda co: 1 - band(co))
    paint_faces(body, band, 1)
    fur(body, "body_w", white_fur, 4000, 18, 0.032, (0, 0, -0.75), density="white", seed=1)
    fur(body, "body_b", black_fur, 2200, 18, 0.032, (0, 0, -0.75), density="black", seed=2)

    # head on a neck pivot; big round head with full cheeks, slightly flattened face
    head_p = pivot("head_p", (0, -0.05, 0.72), body_p)
    P["head"] = head_p
    HR = (0.245, 0.215, 0.205)
    HC = (0, -0.03, 0.17)

    def head_shape(x, y, z):
        x *= 1 + 0.10 * smooth(0.2, -0.6, z)           # cheeks
        y *= 1 - 0.10 * smooth(-0.3, -0.9, y)          # flatter face
        return x, y, z

    head = link(blob("head", HR, HC, head_shape), head_p)
    head.data.materials.append(skin_w)
    head.data.materials.append(skin_b)
    EYE = {}
    for s in (-1, 1):
        EYE[s] = Vector((s * 0.084, HC[1] - 0.166, HC[2] + 0.02))

    def patch(co):
        best = 0.0
        front = smooth(HC[1] + 0.0, HC[1] - 0.12, co.y)       # fades out toward the sides (no hard straight edge)
        if front <= 0:
            return 0.0
        for s in (-1, 1):
            cx, cz = s * 0.092, HC[2] - 0.006
            a = math.radians(38)
            ux, uz = s * math.sin(a), -math.cos(a)                    # long axis: from top-inner to bottom-outer
            dx, dz = co.x - cx, co.z - cz
            along = dx * ux + dz * uz
            across = -dx * uz + dz * ux
            minor = 0.043 * (1 + 0.35 * max(-1.0, min(1.0, along / 0.07)))   # teardrop, wider at the bottom
            e = (along / 0.072) ** 2 + (across / minor) ** 2
            best = max(best, 1 - smooth(0.8, 1.15, e))
        return best * front

    def socket(co):        # no fur over the eyeballs
        return smooth(0.036, 0.05, min((co - EYE[s]).length for s in (-1, 1)))

    vgroup(head, "black", lambda co: patch(co) * socket(co))
    vgroup(head, "white", lambda co: (1 - patch(co)) * socket(co))
    vgroup(head, "len", lambda co: (0.55 + 0.45 * smooth(-0.1, 0.12, co.y - HC[1]) + 0.3 * smooth(-0.05, -0.18, co.z - HC[2]))
           * (1 - 0.5 * patch(co)))
    paint_faces(head, patch, 1)
    fur(head, "head_w", white_fur, 4200, 14, 0.022, (0, 0.55, -0.35), density="white", lengthg="len", seed=3,
        clump=0.25)
    fur(head, "head_b", black_fur, 1800, 16, 0.017, (0, 0.4, -0.5), density="black", seed=4, clump=0.2)

    for s in (-1, 1):
        # eyeballs track the camera (set in build_scene); upper lids sit half closed: tired
        eye = link(blob(f"eye_{'L' if s > 0 else 'R'}", (EYE_R, EYE_R, EYE_R), segs=48, rings=24), head_p)
        eye.location = EYE[s]
        eye.data.materials.append(mat_eye())
        P[f"eye{s}"] = eye
        lid_p = pivot(f"lid_p{s}", EYE[s], head_p)
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=20, radius=EYE_R + 0.0028)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.002], context="VERTS")
        me = bpy.data.meshes.new(f"lid{s}")
        bm.to_mesh(me)
        bm.free()
        for p in me.polygons:
            p.use_smooth = True
        lid = link(bpy.data.objects.new(f"lid{s}", me), lid_p)
        me.materials.append(lid_m)
        sol = lid.modifiers.new("t", "SOLIDIFY")
        sol.thickness = 0.003
        lid_p.rotation_euler = (math.radians(26), 0, s * math.radians(-12))   # droop: lids cover the top ~60%
        P[f"lid{s}"] = lid_p
        # ears
        ear = link(blob(f"ear{s}", (0.072, 0.036, 0.066), (0, 0, 0),
                        lambda x, y, z: (x, y * (1 - 0.3 * z), z)), head_p)
        ear.location = (s * 0.172, HC[1] + 0.035, HC[2] + 0.155)
        ear.rotation_euler = (math.radians(-10), s * math.radians(28), 0)
        ear.data.materials.append(skin_b)
        fur(ear, f"ear_b{s}", black_fur, 500, 10, 0.017, (0, 0, 0.4), seed=5 + s, clump=0.35)

    # muzzle, nose, mouth and a jaw that can chew
    MZ = Vector((0, HC[1] - 0.168, HC[2] - 0.078))
    muz = link(blob("muzzle", (0.105, 0.088, 0.074), MZ, lambda x, y, z: (x, y, z * (1 - 0.15 * smooth(0, -1, z)))),
               head_p)
    muz.data.materials.append(skin_w)
    fur(muz, "muz_w", white_fur, 1400, 8, 0.0075, (0, 0.6, 0), seed=9, clump=0.1, rough=0.0015)
    nose = link(blob("nose", (0.037, 0.024, 0.024), (0, 0, 0), lambda x, y, z: (x * (1 + 0.25 * z), y, z)), head_p)
    nose.location = (0, MZ.y - 0.078, MZ.z + 0.04)
    nose.data.materials.append(nose_m)
    # mouth line: a short philtrum, corners turned down (grumpy)
    cd = bpy.data.curves.new("mouth_line", "CURVE")
    cd.dimensions = "3D"
    cd.bevel_depth = 0.0032
    pts_l = [(0, -0.05, 0.016), (-0.026, -0.058, 0.004), (-0.05, -0.064, -0.012)]

    def on_muzzle(x, z):
        rx, ry, rz = 0.105, 0.088, 0.074
        q = 1 - (x / rx) ** 2 - ((z) / rz) ** 2
        return -ry * math.sqrt(max(0.0, q)) - 0.004

    for side in (-1, 1):
        sp = cd.splines.new("POLY")
        pts = [(0, MZ.z + 0.012), (side * 0.0, MZ.z - 0.008), (side * 0.03, MZ.z - 0.02), (side * 0.054, MZ.z - 0.034)]
        sp.points.add(len(pts) - 1)
        for k, (x, z) in enumerate(pts):
            sp.points[k].co = (x, MZ.y + on_muzzle(x, z - MZ.z), z, 1)
    del pts_l
    ml = link(bpy.data.objects.new("mouth_line", cd), head_p)
    cd.materials.append(skin_b)
    jaw_p = pivot("jaw_p", (0, MZ.y + 0.05, MZ.z - 0.03), head_p)
    P["jaw"] = jaw_p
    jaw = link(blob("jaw", (0.072, 0.07, 0.036), (0, -0.065, -0.042)), jaw_p)
    jaw.data.materials.append(skin_w)
    fur(jaw, "jaw_w", white_fur, 500, 8, 0.008, (0, 0.5, -0.4), seed=11, clump=0.1, rough=0.0015)
    inside = link(blob("mouth_in", (0.04, 0.03, 0.02), (0, MZ.y - 0.03, MZ.z - 0.055)), head_p)
    inside.data.materials.append(mouth_m)
    _ = ml

    # arms: hang along local -Z from a shoulder pivot (aim the pivot to pose them)
    for s in (-1, 1):
        sh = pivot(f"arm_p{s}", (s * 0.27, -0.07, 0.6), body_p)
        arm = link(blob(f"arm{s}", (0.098, 0.098, 0.23), (0, 0, -0.2),
                        lambda x, y, z: (x * (1 + 0.1 * smooth(0, -1, z)), y * (1 + 0.1 * smooth(0, -1, z)), z)), sh)
        arm.data.materials.append(skin_b)
        fur(arm, f"arm_b{s}", black_fur, 1500, 14, 0.03, (0, 0, -0.8), seed=12 + s)
        P[f"arm{s}"] = sh
        # legs stretched forward, soles to the camera
        leg = link(blob(f"leg{s}", (0.125, 0.2, 0.125), (0, -0.2, 0),
                        lambda x, y, z: (x * (1 + 0.12 * smooth(0, -1, y)), y, z * (1 + 0.12 * smooth(0, -1, y)))),
                   body_p)
        leg.location = (s * 0.2, -0.06, 0.12)
        leg.rotation_euler = (math.radians(14), 0, s * math.radians(14))
        leg.data.materials.append(skin_b)
        vgroup(leg, "legfur", lambda co: 1 - smooth(-0.33, -0.385, co.y))
        fur(leg, f"leg_b{s}", black_fur, 1300, 14, 0.028, (0, -0.7, 0), density="legfur", seed=15 + s)
        sole = link(blob(f"sole{s}", (0.058, 0.01, 0.07)), leg)
        sole.location = (0, -0.405, 0.005)
        sole.data.materials.append(pad_m)
        for k in range(5):
            a = math.radians(-60 + k * 30)
            bean = link(blob(f"toe{s}{k}", (0.014, 0.008, 0.014), segs=24, rings=12), leg)
            bean.location = (0.068 * math.sin(a), -0.398, 0.09 + 0.025 * math.cos(a) - 0.012)
            bean.data.materials.append(pad_m)
    return P


def pose_opening(P, cam):
    """0:00 — slumped back, head tilted, chewing a stalk held up to the corner of the mouth."""
    P["root"].rotation_euler = (math.radians(-11), 0, math.radians(4))
    P["head"].rotation_euler = (math.radians(4), math.radians(-7), math.radians(-5))
    P["jaw"].rotation_euler = (math.radians(7), 0, 0)
    bpy.context.view_layer.update()
    # ground the body: lowest point of the body mesh to z = 0 (slightly sunk into the moss)
    body = bpy.data.objects["body"]
    mz = min((body.matrix_world @ v.co).z for v in body.data.vertices)
    P["root"].location.z -= mz + 0.015
    bpy.context.view_layer.update()

    head = P["head"]
    mouth_corner = head.matrix_world @ Vector((-0.058, -0.03 - 0.168 - 0.058, 0.17 - 0.078 - 0.034))
    sh = P["arm-1"]
    shw = sh.matrix_world.translation.copy()
    out_dir = Vector((-0.5, -0.42, -0.76)).normalized()      # down, to the viewer's left, toward the camera
    want = mouth_corner + 0.17 * out_dir
    d_world = (want - shw).normalized()
    inv = sh.parent.matrix_world.to_3x3().inverted()
    aim(sh, inv @ d_world, "-Z")
    bpy.context.view_layer.update()
    paw = sh.matrix_world @ Vector((0, 0, -0.4))
    axis = (paw - mouth_corner).normalized()
    # the other arm rests on the belly
    sh2 = P["arm1"]
    belly = P["body"].matrix_world @ Vector((0.02, -0.36, 0.3))
    aim(sh2, sh2.parent.matrix_world.to_3x3().inverted() @ (belly - sh2.matrix_world.translation), "-Z")
    return paw, axis, mouth_corner


# ── the set ───────────────────────────────────────────────────────────────────
def build_set(paw, axis, mouth_corner):
    bam_m = mat_culm("culm_green", (0.2, 0.42, 0.08))
    bam_y = mat_culm("culm_yellow", (0.42, 0.45, 0.12))
    bam_bg = mat_culm("culm_bg", (0.16, 0.36, 0.08))
    leaf_g = bk.mat_basic("leaf_g", (0.1, 0.32, 0.05), rough=0.45, sss=0.0)
    leaf_dry = bk.mat_basic("leaf_dry", (0.42, 0.3, 0.12), rough=0.7)

    g = bpy.data.meshes.new("ground")
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=2, y_segments=2, size=25)
    bm.to_mesh(g)
    bm.free()
    gr = link(bpy.data.objects.new("ground", g))
    g.materials.append(mat_ground())

    tree = link(bpy.data.objects.new("tree", bpy.data.meshes.new("tree")))
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=48, radius1=0.34, radius2=0.26, depth=7)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, 3.5))
    bm.to_mesh(tree.data)
    bm.free()
    for p in tree.data.polygons:
        p.use_smooth = True
    tree.data.materials.append(mat_bark())
    tree.location = (0.08, 0.78, -0.05)

    # the stalk being eaten: through the paw to the corner of the mouth, leaves at the top
    st = link(culm("stalk", 0.021, 0.85, bam_m))
    st.location = mouth_corner - axis * 0.025
    aim(st, axis, "Z")
    bpy.context.view_layer.update()

    # the pile, taller than the panda: cut stalks stacked crosswise behind its shoulder (viewer's left)
    for k in range(56):
        lvl = k / 56
        z = 0.03 + lvl * 1.22 + rng.uniform(-0.02, 0.02)
        length = rng.uniform(0.6, 0.92) * (1 - 0.3 * lvl)
        cx = -0.86 + rng.uniform(-0.1, 0.1) * (1 - lvl)
        cy = rng.uniform(0.45, 0.85)
        d = Vector((1.0, rng.uniform(-0.45, 0.45), rng.uniform(-0.12, 0.12))).normalized()
        c = link(culm(f"pile{k}", rng.uniform(0.018, 0.03), length, bam_m if rng.random() < 0.7 else bam_y))
        c.location = Vector((cx, cy, z)) - d * length / 2
        aim(c, d, "Z")
    for k in range(7):           # stalks leaning up against the back of the heap, leafy tops above it
        c = link(culm(f"pile_up{k}", 0.02, 1.55, bam_m))
        c.location = (-1.0 + k * 0.07, 0.8 + rng.uniform(0, 0.1), 0.0)
        aim(c, (rng.uniform(0.0, 0.3), rng.uniform(-0.25, -0.05), 1.0), "Z")
        bpy.context.view_layer.update()
        top = c.matrix_world @ Vector((0, 0, 1.55))
        for j in range(6):
            lf = link(leaf_mesh(f"pile_leaf{k}{j}", rng.uniform(0.15, 0.22), 0.028, leaf_g, curl=0.6, cup=0.2))
            lf.location = top + Vector((0, 0, rng.uniform(-0.12, 0)))
            lf.rotation_euler = (rng.uniform(-0.6, 0.6), rng.uniform(-1.4, -0.3), rng.uniform(0, 6.28))

    # bamboo grove behind (soft in the depth of field) with leafy sprays
    src_leaf = leaf_mesh("grove_leaf_src", 0.2, 0.03, leaf_g, curl=0.5, cup=0.2)
    for k in range(70):
        y = rng.uniform(1.4, 11.0)
        x = rng.uniform(-0.6 - 0.25 * y, 0.6 + 0.25 * y)
        if abs(x) < 0.5 and y < 2.0:
            continue
        r = rng.uniform(0.03, 0.055)
        c = link(culm(f"grove{k}", r, 9.0, bam_bg, segs=14))
        c.location = (x, y, -0.1)
        c.rotation_euler = (rng.uniform(-0.05, 0.05), rng.uniform(-0.05, 0.05), 0)
        for j in range(rng.randint(0, 3)):
            hz = rng.uniform(1.2, 3.5)
            for q in range(8):
                lf = bpy.data.objects.new(f"gl{k}_{j}_{q}", src_leaf.data)
                link(lf)
                lf.location = (x + rng.uniform(-0.25, 0.25), y + rng.uniform(-0.2, 0.2), hz + rng.uniform(-0.15, 0.15))
                lf.rotation_euler = (rng.uniform(-0.6, 0.6), rng.uniform(-1.5, -0.2), rng.uniform(0, 6.28))
    # fallen leaves on the ground
    dry_src = leaf_mesh("dry_leaf_src", 0.17, 0.026, leaf_dry, curl=0.15, cup=0.1)
    green_src = leaf_mesh("green_leaf_src", 0.17, 0.026, leaf_g, curl=0.15, cup=0.1)
    for k in range(900):
        lf = bpy.data.objects.new(f"litter{k}", (dry_src if rng.random() < 0.7 else green_src).data)
        link(lf)
        lf.location = (rng.uniform(-1.8, 1.8), rng.uniform(-1.4, 2.5), 0.004 + rng.uniform(0, 0.006))
        lf.rotation_euler = (rng.uniform(-0.15, 0.15), rng.uniform(-0.15, 0.15), rng.uniform(0, 6.28))
    _ = gr


def build_lights(sc):
    w = bpy.data.worlds.new("world")
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.62, 0.78, 0.66, 1)
    bg.inputs["Strength"].default_value = 1.1
    sc.world = w

    def light(name, kind, energy, color, loc=None, direction=None, size=1.0):
        ld = bpy.data.lights.new(name, kind)
        ld.energy = energy
        ld.color = color
        if kind == "AREA":
            ld.size = size
        if kind == "SUN":
            ld.angle = math.radians(2.5)
        ob = link(bpy.data.objects.new(name, ld))
        if loc:
            ob.location = loc
        if direction:
            aim(ob, direction, "-Z")
        return ob

    light("sun", "SUN", 7.0, (1.0, 0.88, 0.7), direction=(0.5, -0.75, -0.55))         # warm back-left rim
    light("key", "AREA", 200, (1.0, 0.97, 0.92), loc=(-1.4, -2.4, 1.9), direction=(1.4, 2.4, -1.2), size=2.0)
    light("fill", "AREA", 70, (0.85, 0.95, 1.0), loc=(1.8, -2.0, 1.0), direction=(-1.8, 2.0, -0.4), size=2.5)


def build_scene(samples=16):
    sc = bk.new_scene(fps=FPS, res=(720, 1280), samples=samples)
    c = sc.cycles
    c.max_bounces, c.diffuse_bounces, c.glossy_bounces, c.transmission_bounces = 6, 2, 3, 6
    sc.cycles_curves.shape = "RIBBONS"
    sc.cycles_curves.subdivisions = 2
    P = build_panda()
    cam, target = bk.camera(sc)
    paw, axis, mouth = pose_opening(P, cam)
    build_set(paw, axis, mouth)
    build_lights(sc)
    for s in (-1, 1):
        con = P[f"eye{s}"].constraints.new("DAMPED_TRACK")
        con.target = cam
        con.track_axis = "TRACK_NEGATIVE_Y"
    focus = pivot("focus", (0, 0, 0), P["head"])
    focus.location = (0, -0.2, 0.17)
    bk.shot(cam, target, 0, (-0.05, 0, 0.64), 3.3, elev_deg=5, azim_deg=-4, lens=38, fstop=1.4)
    cam.data.dof.focus_object = focus
    return sc, P, cam


if __name__ == "__main__":
    out = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "still"
    os.makedirs(out, exist_ok=True)
    sc, P, cam = build_scene()
    if mode == "still":
        frames = [int(f) for f in sys.argv[3:]] or [0]
        for f in frames:
            sc.frame_set(f)
            sc.render.filepath = os.path.join(out, f"still_{f:04d}.png")
            bpy.ops.render.render(write_still=True)
            print("wrote", sc.render.filepath)
