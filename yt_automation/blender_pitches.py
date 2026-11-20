"""
blender_pitches.py — the first 2 seconds of three pitched Shorts, for the owner's approval (rule 14, rule 18).

Every opening is an EVENT at 0.0 s, not a poster (CHANNEL_DIAGNOSIS.md): the swipe decision is made in the first
second. Renders frames 0, 12, 24, 48 (0.0 / 0.5 / 1.0 / 2.0 s at 24 fps) of one pitch:

  /root/.venvs/blender/bin/python blender_pitches.py OUT_DIR penny|hail|quicksand [FRAME ...]

penny    camera falls with a tumbling penny down a skyscraper toward a crash-test dummy far below
hail     an 8-inch hailstone is punching through the dummy's umbrella at frame 0
quicksand the dummy is already waist-deep and sinking, flailing; then he floats and folds his arms
popcorn  (dropped: the macro kernel looked like candy) a kernel's hull splits and the foam grows a "leg"
"""
import math
import os
import random
import sys

import bpy  # noqa: I001  (bpy must load before bmesh)
import bmesh
from mathutils import Euler, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_kit as bk  # noqa: E402

FPS = 24


# ── small helpers ─────────────────────────────────────────────────────────────
def link(ob, parent=None):
    bpy.context.scene.collection.objects.link(ob)
    if parent is not None:
        ob.parent = parent
    return ob


def pivot(name, loc, parent=None, rot=(0, 0, 0)):
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = 0.05
    e.location, e.rotation_euler = loc, rot
    return link(e, parent)


def ellipsoid(name, radii, center=(0, 0, 0), mat=None, parent=None, segs=48, rings=24, smooth=True):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * radii[0], v.co.y * radii[1], v.co.z * radii[2]))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = smooth
    ob = bpy.data.objects.new(name, me)
    ob.location = center
    if mat:
        me.materials.append(mat)
    return link(ob, parent)


def box(name, size, center=(0, 0, 0), mat=None, parent=None, bevel=0.0, rot=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.location, ob.rotation_euler = center, rot
    if mat:
        me.materials.append(mat)
    if bevel:
        m = ob.modifiers.new("bevel", "BEVEL")
        m.width, m.segments = bevel, 4
        for p in me.polygons:
            p.use_smooth = True
    return link(ob, parent)


def cylinder(name, r, h, center=(0, 0, 0), mat=None, parent=None, rot=(0, 0, 0), segs=48, bevel=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r, depth=h)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.location, ob.rotation_euler = center, rot
    if mat:
        me.materials.append(mat)
    if bevel:
        m = ob.modifiers.new("bevel", "BEVEL")
        m.width, m.segments = bevel, 3
        m.limit_method = "ANGLE"
        for p in me.polygons:
            p.use_smooth = True
    return link(ob, parent)


def key(ob, path, frame, value=None, interp="BEZIER"):
    if value is not None:
        setattr(ob, path, value)
    ob.keyframe_insert(path, frame=frame)
    if ob.animation_data and ob.animation_data.action:
        bk._set_interp(ob.animation_data.action, frame, interp)


def hide_until(ob, frame, until_hidden=True):
    """Visible only from `frame` on (or only before it)."""
    for f, h in ((0, until_hidden), (frame, not until_hidden)):
        ob.hide_render = h
        ob.keyframe_insert("hide_render", frame=f)


def world(sc, color, strength=1.0):
    w = bpy.data.worlds.new("world")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (*color, 1)
    bg.inputs[1].default_value = strength
    return w


def light(name, kind, loc, energy, size=1.0, color=(1, 1, 1), aim=None, rot=None):
    l = bpy.data.lights.new(name, kind)
    l.energy, l.color = energy, color
    if kind == "AREA":
        l.size = size
    if kind == "SUN":
        l.angle = math.radians(size)
    o = link(bpy.data.objects.new(name, l))
    o.location = loc
    if rot is not None:
        o.rotation_euler = rot
    if aim is not None:
        c = o.constraints.new("TRACK_TO")
        c.target = pivot(name + "_aim", aim)
        c.track_axis, c.up_axis = "TRACK_NEGATIVE_Z", "UP_Y"
    return o


def cam_free(sc, lens, loc, look_at, roll_up=(0, 0, 1)):
    cd = bpy.data.cameras.new("cam")
    cd.lens, cd.sensor_fit, cd.sensor_height, cd.clip_start = lens, "VERTICAL", 24.0, 0.001
    cam = link(bpy.data.objects.new("cam", cd))
    sc.camera = cam
    aim(cam, loc, look_at, roll_up)
    return cam


def aim(cam, loc, look_at, up=(0, 0, 1)):
    cam.location = loc
    d = (Vector(look_at) - Vector(loc)).normalized()
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler() if abs(d.z) < 0.98 else \
        _down_euler(d, Vector(up))


def _down_euler(d, up):
    # looking (almost) straight down: build the basis by hand so "up" in frame is `up`
    z = -d
    if abs(up.normalized().dot(z)) > 0.95:
        up = Vector((0, 1, 0))
    x = up.cross(z).normalized()
    y = z.cross(x).normalized()
    from mathutils import Matrix
    return Matrix((x, y, z)).transposed().to_euler()


# ── materials ────────────────────────────────────────────────────────────────
def mat(name, color, rough=0.5, metallic=0.0, sss=0.0, coat=0.0, transmission=0.0, ior=1.45, alpha=1.0):
    m = bk.mat_basic(name, color, rough=rough, sss=sss, coat=coat, metallic=metallic)
    b = m.node_tree.nodes["Principled BSDF"]
    if transmission:
        b.inputs["Transmission Weight"].default_value = transmission
        b.inputs["IOR"].default_value = ior
    if alpha < 1.0:
        b.inputs["Alpha"].default_value = alpha
    return m


def add_bump(m, scale, strength, detail=6.0, distance=0.002):
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = scale
    tex.inputs["Detail"].default_value = detail
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = strength
    bump.inputs["Distance"].default_value = distance
    nt.links.new(tex.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def mat_target():
    """Crash-test calibration marker: black/yellow quadrants (object space x, y)."""
    m, b, nt = bk._principled("target")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    gx = nt.nodes.new("ShaderNodeMath"); gx.operation = "GREATER_THAN"; gx.inputs[1].default_value = 0.0
    gy = nt.nodes.new("ShaderNodeMath"); gy.operation = "GREATER_THAN"; gy.inputs[1].default_value = 0.0
    nt.links.new(sep.outputs[0], gx.inputs[0])
    nt.links.new(sep.outputs[1], gy.inputs[0])
    diff = nt.nodes.new("ShaderNodeMath"); diff.operation = "SUBTRACT"
    ab = nt.nodes.new("ShaderNodeMath"); ab.operation = "ABSOLUTE"
    nt.links.new(gx.outputs[0], diff.inputs[0]); nt.links.new(gy.outputs[0], diff.inputs[1])
    nt.links.new(diff.outputs[0], ab.inputs[0])
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
    mix.inputs["A"].default_value = (0.02, 0.02, 0.02, 1)
    mix.inputs["B"].default_value = (1.0, 0.78, 0.05, 1)
    nt.links.new(ab.outputs[0], mix.inputs["Factor"])
    nt.links.new(mix.outputs["Result"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.4
    return m


# ── the crash-test dummy (our recurring tester) ──────────────────────────────
def build_dummy(at=(0, 0, 0), yaw=0.0):
    """~1.75 m segmented dummy. Returns dict of pivots: root, pelvis, chest, head, sh-1/sh1, el-1/el1,
    hip-1/hip1, kn-1/kn1. Arms hang along -Z; rotate pivots to pose."""
    if DUMMY_VERSION == 2:
        return build_dummy_v2(at, yaw)
    yel = mat("dummy_yellow", (0.95, 0.66, 0.08), rough=0.42, coat=0.25)
    blk = mat("dummy_black", (0.025, 0.025, 0.028), rough=0.35, metallic=0.3)
    grey = mat("dummy_grey", (0.12, 0.12, 0.13), rough=0.6)
    tgt = mat_target()
    P = {}
    root = P["root"] = pivot("dummy", at, rot=(0, 0, yaw))
    pelvis = P["pelvis"] = pivot("pelvis", (0, 0, 0.95), root)
    box("hips", (0.32, 0.2, 0.16), (0, 0, 0.02), yel, pelvis, bevel=0.05)
    chest = P["chest"] = pivot("chest", (0, 0, 0.1), pelvis)
    box("belly", (0.26, 0.17, 0.14), (0, 0, 0.1), grey, chest, bevel=0.04)
    box("torso", (0.4, 0.23, 0.36), (0, 0, 0.33), yel, chest, bevel=0.07)
    cylinder("chest_tgt", 0.038, 0.004, (0.0, -0.117, 0.36), tgt, chest, rot=(math.radians(90), 0, 0))
    cylinder("neck", 0.045, 0.11, (0, 0, 0.55), blk, chest, bevel=0.01)
    head = P["head"] = pivot("head", (0, 0, 0.6), chest)
    ellipsoid("skull", (0.1, 0.115, 0.13), (0, 0.0, 0.12), yel, head)
    ellipsoid("brow", (0.075, 0.03, 0.022), (0, -0.098, 0.15), yel, head)
    ellipsoid("nose", (0.018, 0.03, 0.032), (0, -0.112, 0.1), yel, head)
    ellipsoid("chin", (0.06, 0.04, 0.03), (0, -0.075, 0.02), yel, head)
    for s in (-1, 1):
        cylinder(f"head_tgt{s}", 0.038, 0.004, (s * 0.099, 0.0, 0.13), tgt, head, rot=(0, math.radians(90), 0))
        sh = P[f"sh{s}"] = pivot(f"sh{s}", (s * 0.24, 0, 0.47), chest)
        ellipsoid(f"shj{s}", (0.06, 0.06, 0.06), (0, 0, 0), blk, sh)
        ellipsoid(f"upper{s}", (0.05, 0.05, 0.15), (0, 0, -0.16), yel, sh)
        el = P[f"el{s}"] = pivot(f"el{s}", (0, 0, -0.32), sh)
        ellipsoid(f"elj{s}", (0.045, 0.045, 0.045), (0, 0, 0), blk, el)
        ellipsoid(f"fore{s}", (0.043, 0.043, 0.14), (0, 0, -0.15), yel, el)
        ellipsoid(f"hand{s}", (0.04, 0.025, 0.07), (0, 0, -0.33), yel, el)
        hip = P[f"hip{s}"] = pivot(f"hip{s}", (s * 0.1, 0, -0.04), pelvis)
        ellipsoid(f"hipj{s}", (0.065, 0.065, 0.065), (0, 0, 0), blk, hip)
        ellipsoid(f"thigh{s}", (0.07, 0.07, 0.22), (0, 0, -0.23), yel, hip)
        kn = P[f"kn{s}"] = pivot(f"kn{s}", (0, 0, -0.46), hip)
        ellipsoid(f"knj{s}", (0.055, 0.055, 0.05), (0, 0, 0), blk, kn)
        ellipsoid(f"shin{s}", (0.055, 0.055, 0.2), (0, 0, -0.21), yel, kn)
        box(f"foot{s}", (0.1, 0.24, 0.07), (0, -0.05, -0.44), grey, kn, bevel=0.03)
    return P


# ── the dummy, v2 (owner approved an upgrade, 2026-11-09) ────────────────────
# v1 above is kept unchanged so the published Shorts re-render identically. v2 has the same pivots and joint
# positions (every pose and camera still works) but reads as an engineered test dummy, not a toy:
# ribbed chest plates, a stack of rubber neck discs, bolted elbows/knees, hands with a thumb, a sculpted face,
# worn painted plastic and a stencilled test number.
def mat_painted(name, color, grime=(0.36, 0.25, 0.08), rough=(0.28, 0.55), coat=0.35, scale=9.0):
    """Painted plastic that has been through tests: low-frequency grime, roughness variation, fine scuffs."""
    m, b, nt = bk._principled(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value, nz.inputs["Detail"].default_value = scale, 8.0
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[1].position = 0.55, 0.78
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
    mix.inputs["A"].default_value, mix.inputs["B"].default_value = (*color, 1), (*grime, 1)
    fac = nt.nodes.new("ShaderNodeMath"); fac.operation = "MULTIPLY"; fac.inputs[1].default_value = 0.45
    nt.links.new(ramp.outputs["Color"], fac.inputs[0])
    nt.links.new(fac.outputs[0], mix.inputs["Factor"])
    nt.links.new(mix.outputs["Result"], b.inputs["Base Color"])
    sc = nt.nodes.new("ShaderNodeTexNoise")                      # stretched noise = fine scuffs
    sc.inputs["Scale"].default_value, sc.inputs["Detail"].default_value = 60.0, 4.0
    mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1.0, 1.0, 9.0)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"]); nt.links.new(mp.outputs[0], sc.inputs["Vector"])
    rr = nt.nodes.new("ShaderNodeMapRange")
    rr.inputs["To Min"].default_value, rr.inputs["To Max"].default_value = rough
    nt.links.new(sc.outputs["Fac"], rr.inputs["Value"])
    nt.links.new(rr.outputs["Result"], b.inputs["Roughness"])
    b.inputs["Coat Weight"].default_value = coat
    bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.05
    nt.links.new(sc.outputs["Fac"], bump.inputs["Height"]); nt.links.new(bump.outputs[0], b.inputs["Normal"])
    return m


def stencil(name, text, center, size, mat, parent, rot=(math.radians(90), 0, 0)):
    """Flat stencilled lettering (Bebas), as a thin mesh just proud of a surface."""
    cu = bpy.data.curves.new(name, "FONT")
    cu.body, cu.size, cu.align_x, cu.align_y, cu.extrude = text, size, "CENTER", "CENTER", 0.0008
    fp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "BebasNeue-Regular.ttf")
    if os.path.exists(fp):
        cu.font = bpy.data.fonts.load(fp, check_existing=True)
    ob = bpy.data.objects.new(name, cu)
    ob.location, ob.rotation_euler = center, rot
    cu.materials.append(mat)
    return link(ob, parent)


def sculpted_head(name, mat, parent, center=(0, 0, 0.125), radii=(0.098, 0.11, 0.128)):
    """A dummy head as ONE smooth surface: brow ridge, eye sockets, a modest nose, cheekbones, mouth groove,
    a narrower jaw and a chin, all as soft displacements of an ellipsoid (front = -Y)."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=96, v_segments=64, radius=1.0)
    def g(x, z, cx, cz, sx, sz):
        return math.exp(-(((x - cx) / sx) ** 2 + ((z - cz) / sz) ** 2))
    for v in bm.verts:
        d = v.co.copy()
        x, y, z = d.x * radii[0], d.y * radii[1], d.z * radii[2]
        if z < 0:                                                  # narrower, squarer jaw
            k = 1.0 - 0.22 * min(1.0, -z / radii[2]) ** 1.3
            x *= k
            y = y * (k if y > 0 else 1.0)
        p = Vector((x, y, z))
        if y < 0:
            front = min(1.0, -y / radii[1]) ** 1.5
            zz = z + center[2]                                     # feature heights in head-pivot space
            off = 0.0
            off += 0.010 * g(x, zz, 0.0, 0.158, 0.065, 0.012)                     # brow ridge
            off -= 0.013 * (g(x, zz, 0.040, 0.128, 0.020, 0.014) + g(x, zz, -0.040, 0.128, 0.020, 0.014))
            off += 0.024 * g(x, zz, 0.0, 0.098, 0.012, 0.024)                     # nose
            off += 0.006 * (g(x, zz, 0.055, 0.095, 0.02, 0.016) + g(x, zz, -0.055, 0.095, 0.02, 0.016))
            off -= 0.004 * g(x, zz, 0.0, 0.058, 0.024, 0.004)                     # mouth groove
            off += 0.006 * g(x, zz, 0.0, 0.025, 0.028, 0.016)                     # chin
            p = p + d.normalized() * off * front
        v.co = p
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for poly in me.polygons:
        poly.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    ob.location = center
    me.materials.append(mat)
    return link(ob, parent)


def capsule(name, r, h, center, mat, parent, rot=(0, 0, 0)):
    """A limb segment: a cylinder with fully rounded ends (reads as moulded plastic, not a sausage)."""
    return cylinder(name, r, h, center, mat, parent, rot=rot, segs=40, bevel=r * 0.9)


def build_dummy_v2(at=(0, 0, 0), yaw=0.0, label="TEST 04"):
    """Same pivots as build_dummy (root, pelvis, chest, head, sh+-1, el+-1, hip+-1, kn+-1)."""
    yel = mat_painted("dummy2_yellow", (1.0, 0.56, 0.0))
    blk = mat("dummy2_rubber", (0.022, 0.022, 0.024), rough=0.62)
    steel = mat("dummy2_steel", (0.62, 0.62, 0.64), rough=0.28, metallic=1.0)
    seam = mat("dummy2_seam", (0.05, 0.04, 0.02), rough=0.8)
    ink = mat("dummy2_ink", (0.03, 0.03, 0.03), rough=0.7)
    face = mat_painted("dummy2_face", (1.0, 0.58, 0.01), scale=14.0)
    tgt = mat_target()
    P = {}
    root = P["root"] = pivot("dummy", at, rot=(0, 0, yaw))
    pelvis = P["pelvis"] = pivot("pelvis", (0, 0, 0.95), root)
    box("hips", (0.32, 0.2, 0.15), (0, 0, 0.01), yel, pelvis, bevel=0.05)
    box("belt", (0.33, 0.205, 0.035), (0, 0, 0.075), blk, pelvis, bevel=0.012)
    for s in (-1, 1):
        cylinder(f"hipbolt{s}", 0.022, 0.012, (s * 0.163, 0, 0.0), steel, pelvis, rot=(0, math.radians(90), 0),
                 bevel=0.003)
    chest = P["chest"] = pivot("chest", (0, 0, 0.1), pelvis)
    for j, z in enumerate((0.035, 0.075, 0.115)):                # rubber lumbar spine, not a grey box
        o = cylinder(f"lumbar{j}", 0.115, 0.032, (0, 0, z), blk, chest, bevel=0.01)
        o.scale = (1.0, 0.68, 1.0)
    box("torso", (0.4, 0.23, 0.34), (0, 0, 0.32), yel, chest, bevel=0.07)
    for j, z in enumerate((0.29, 0.335, 0.38, 0.425)):           # rib plates: seams on the front and both sides
        box(f"ribF{j}", (0.27, 0.006, 0.007), (0, -0.1152, z), seam, chest)
        for s in (-1, 1):
            box(f"ribS{j}{s}", (0.006, 0.1, 0.007), (s * 0.2002, 0, z), seam, chest)
    box("sternum", (0.1, 0.012, 0.16), (0, -0.112, 0.365), yel, chest, bevel=0.005)
    cylinder("chest_tgt", 0.034, 0.004, (0.1, -0.118, 0.40), tgt, chest, rot=(math.radians(90), 0, 0))
    stencil("chest_label", label, (0, -0.1162, 0.222), 0.06, ink, chest)
    for s in (-1, 1):
        ellipsoid(f"shcap{s}", (0.085, 0.13, 0.05), (s * 0.17, 0, 0.47), yel, chest)
    for j, z in enumerate((0.505, 0.54, 0.575)):                  # neck: rubber discs between steel spacers
        cylinder(f"neckdisc{j}", 0.055, 0.022, (0, 0, z), blk, chest, bevel=0.007)
    for j, z in enumerate((0.5225, 0.5575)):
        cylinder(f"neckspacer{j}", 0.035, 0.012, (0, 0, z), steel, chest)
    cylinder("neckpost", 0.026, 0.07, (0, 0, 0.6), steel, chest)          # the neck cable into the skull
    head = P["head"] = pivot("head", (0, 0, 0.6), chest)
    sculpted_head("skull", face, head)
    ellipsoid("mouth", (0.026, 0.003, 0.0025), (0, -0.0915, 0.058), seam, head)
    for s in (-1, 1):
        ellipsoid(f"eye{s}", (0.018, 0.003, 0.008), (s * 0.04, -0.0905, 0.128), seam, head)  # painted, in socket
        ellipsoid(f"ear{s}", (0.012, 0.03, 0.04), (s * 0.1, 0.0, 0.11), face, head)
        cylinder(f"head_tgt{s}", 0.03, 0.004, (s * 0.098, 0.03, 0.17), tgt, head, rot=(0, math.radians(90), 0))
        sh = P[f"sh{s}"] = pivot(f"sh{s}", (s * 0.24, 0, 0.47), chest)
        ellipsoid(f"shj{s}", (0.06, 0.06, 0.06), (0, 0, 0), blk, sh)
        cylinder(f"shbolt{s}", 0.02, 0.014, (s * 0.058, 0, 0), steel, sh, rot=(0, math.radians(90), 0), bevel=0.003)
        capsule(f"upper{s}", 0.05, 0.27, (0, 0, -0.165), yel, sh)
        el = P[f"el{s}"] = pivot(f"el{s}", (0, 0, -0.32), sh)
        ellipsoid(f"elj{s}", (0.046, 0.046, 0.046), (0, 0, 0), blk, el)
        cylinder(f"elbolt{s}", 0.017, 0.096, (0, 0, 0), steel, el, rot=(0, math.radians(90), 0), bevel=0.003)
        capsule(f"fore{s}", 0.043, 0.24, (0, 0, -0.145), yel, el)
        ellipsoid(f"wrist{s}", (0.036, 0.036, 0.02), (0, 0, -0.27), blk, el)
        ellipsoid(f"hand{s}", (0.038, 0.024, 0.065), (0, 0, -0.335), yel, el)
        o = ellipsoid(f"thumb{s}", (0.013, 0.013, 0.035), (-s * 0.034, -0.012, -0.315), yel, el)
        o.rotation_euler = (0, math.radians(-s * 35), 0)
        hip = P[f"hip{s}"] = pivot(f"hip{s}", (s * 0.1, 0, -0.04), pelvis)
        ellipsoid(f"hipj{s}", (0.065, 0.065, 0.065), (0, 0, 0), blk, hip)
        capsule(f"thigh{s}", 0.07, 0.4, (0, 0, -0.235), yel, hip)
        kn = P[f"kn{s}"] = pivot(f"kn{s}", (0, 0, -0.46), hip)
        ellipsoid(f"knj{s}", (0.056, 0.056, 0.05), (0, 0, 0), blk, kn)
        cylinder(f"knbolt{s}", 0.02, 0.124, (0, 0, 0), steel, kn, rot=(0, math.radians(90), 0), bevel=0.003)
        ellipsoid(f"kneecap{s}", (0.045, 0.02, 0.045), (0, -0.05, 0.0), yel, kn)
        capsule(f"shin{s}", 0.054, 0.36, (0, 0, -0.215), yel, kn)
        box(f"foot{s}", (0.1, 0.24, 0.07), (0, -0.05, -0.44), blk, kn, bevel=0.03)
    return P


DUMMY_VERSION = int(os.environ.get("DUMMY_VERSION", "1"))


# ── 1. penny ──────────────────────────────────────────────────────────────────
def mat_facade():
    m, b, nt = bk._principled("facade")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    mp = nt.nodes.new("ShaderNodeCombineXYZ")                     # facade lies in the y-z plane
    nt.links.new(sep.outputs[1], mp.inputs[0])
    nt.links.new(sep.outputs[2], mp.inputs[1])
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Brick Width"].default_value = 1.5
    br.inputs["Row Height"].default_value = 3.6
    br.inputs["Mortar Size"].default_value = 0.45
    br.offset, br.squash = 0.0, 1.0
    br.inputs["Color1"].default_value = (0.32, 0.42, 0.55, 1)      # glass (reflects the sky)
    br.inputs["Color2"].default_value = (0.26, 0.36, 0.5, 1)
    br.inputs["Mortar"].default_value = (0.78, 0.72, 0.62, 1)     # limestone
    nt.links.new(mp.outputs[0], br.inputs["Vector"])
    nt.links.new(br.outputs["Color"], b.inputs["Base Color"])
    rmap = nt.nodes.new("ShaderNodeMapRange")
    rmap.inputs["To Min"].default_value, rmap.inputs["To Max"].default_value = 0.06, 0.75
    nt.links.new(br.outputs["Fac"], rmap.inputs["Value"])
    nt.links.new(rmap.outputs["Result"], b.inputs["Roughness"])
    met = nt.nodes.new("ShaderNodeMath"); met.operation = "SUBTRACT"
    met.inputs[0].default_value = 1.0
    nt.links.new(br.outputs["Fac"], met.inputs[1])
    nt.links.new(met.outputs[0], b.inputs["Metallic"])
    return m


def scene_penny(samples):
    sc = bk.new_scene(fps=FPS, samples=samples, frames=49)
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.5
    world(sc, (0.55, 0.7, 0.95), 1.25)
    light("sun", "SUN", (0, 0, 50), 6.0, size=1.5, color=(1.0, 0.93, 0.8),
          rot=(math.radians(28), math.radians(-18), math.radians(25)))
    fac = mat_facade()
    # main tower: its face is the plane x = -3, running up beside the falling camera
    t = box("tower", (20, 60, 400), (-13, 0, 200), fac)
    stone = mat("stone", (0.7, 0.64, 0.54), rough=0.7)
    for k in range(1, 40):                                        # stone ledge every floor: speed lines
        box(f"ledge{k}", (0.3, 60, 0.16), (-2.88, 0, k * 3.6), stone)
    box("tower_far", (20, 60, 120), (31, 0, 60), fac)            # across the street
    asphalt = add_bump(mat("asphalt", (0.04, 0.04, 0.045), rough=0.85), 300, 0.2)
    box("road", (12, 300, 0.1), (6, 0, -0.05), asphalt)
    side = mat("sidewalk", (0.45, 0.44, 0.42), rough=0.8)
    box("walk_near", (3.2, 300, 0.25), (-1.4, 0, 0.0), side)
    box("walk_far", (3.2, 300, 0.25), (13.6, 0, 0.0), side)
    white = mat("paint", (0.85, 0.85, 0.8), rough=0.6)
    for k in range(-30, 31):
        box(f"lane{k}", (0.15, 3.0, 0.02), (6, k * 6, 0.01), mat("yline", (0.95, 0.75, 0.1), rough=0.6) if k % 2 else white)
    for k in range(8):                                             # crosswalk
        box(f"zebra{k}", (0.6, 3.0, 0.02), (0.6 + k * 1.45, 9.0, 0.012), white)
    taxi = mat("taxi", (0.98, 0.72, 0.05), rough=0.35, coat=0.6)
    glass = mat("carglass", (0.02, 0.03, 0.04), rough=0.08)
    rnd = random.Random(4)
    for k, (x, y) in enumerate([(3.0, -14), (8.8, -4), (3.2, 18), (9.0, 26), (8.7, -22)]):
        c = box(f"car{k}", (1.9, 4.6, 0.9), (x, y, 0.55), taxi if k % 2 == 0 else
                mat(f"car{k}", (rnd.random() * 0.6, 0.1, 0.12), rough=0.3, coat=0.5), bevel=0.25)
        box(f"cab{k}", (1.6, 2.2, 0.6), (x, y + 0.3, 1.25), glass, bevel=0.2)
    P = build_dummy(at=(-1.2, 9.0, 0.12), yaw=math.radians(180))
    P["head"].rotation_euler = (math.radians(-40), 0, 0)         # looking up
    P["sh-1"].rotation_euler = (math.radians(-150), math.radians(-25), 0)   # hand up shading his eyes
    P["el-1"].rotation_euler = (math.radians(-70), 0, 0)
    P["sh1"].rotation_euler = (0, math.radians(8), 0)
    # the penny and the camera fall together; the street rushes up
    copper = add_bump(mat("copper", (1.0, 0.62, 0.42), rough=0.16, metallic=1.0), 1400, 0.08)
    pen = pivot("penny_fall", (0, 0, 0))
    coin = cylinder("penny", 0.0095, 0.00125, (0, 0, 0), copper, pen, bevel=0.0003, segs=160)
    for side in (-1, 1):                                            # raised rim, a bust and LIBERTY on both faces
        rim = cylinder(f"rim{side}", 0.0095, 0.0003, (0, 0, side * 0.00072), copper, coin, bevel=0.0001, segs=160)
        inner = cylinder(f"rimcut{side}", 0.0086, 0.0004, (0, 0, side * 0.00072), copper, coin, segs=160)
        bo = rim.modifiers.new("cut", "BOOLEAN")
        bo.object, bo.operation = inner, "DIFFERENCE"
        inner.hide_render = True
        bust = ellipsoid(f"bust{side}", (0.0036, 0.0046, 0.00025), (0.0003, -0.0004, side * 0.00062), copper, coin, segs=32, rings=12)
        cu = bpy.data.curves.new(f"liberty{side}", "FONT")
        cu.body, cu.size, cu.extrude, cu.align_x = "LIBERTY", 0.0019, 0.00012, "CENTER"
        tx = link(bpy.data.objects.new(f"liberty{side}", cu), coin)
        tx.location = (0, 0.0056, side * 0.00068)
        tx.rotation_euler = (0, 0 if side > 0 else math.pi, 0)
        tx.data.materials.append(copper)
        cu2 = bpy.data.curves.new(f"cent{side}", "FONT")
        cu2.body, cu2.size, cu2.extrude, cu2.align_x = "ONE CENT", 0.0015, 0.0001, "CENTER"
        tx2 = link(bpy.data.objects.new(f"cent{side}", cu2), coin)
        tx2.location = (0, -0.0072, side * 0.00068)
        tx2.rotation_euler = (0, 0 if side > 0 else math.pi, 0)
        tx2.data.materials.append(copper)
    target = Vector((-1.2, 9.0, 0.9))
    for f, z in ((0, 19.0), (12, 16.5), (24, 14.0), (48, 9.0)):           # falling with the penny; the street rushes up
        cam_loc = Vector((-0.3, -2.5, z))
        cam = sc.camera or cam_free(sc, 18, cam_loc, target)
        aim(cam, cam_loc, target + Vector((0.6, 4.5, 0)))
        key(cam, "location", f, interp="LINEAR")
        key(cam, "rotation_euler", f, interp="LINEAR")
        pen.location = cam_loc + cam.rotation_euler.to_matrix() @ Vector((-0.006, 0.019, -0.088))
        key(pen, "location", f, interp="LINEAR")
    for f in range(0, 49, 4):                                      # tumbling flip
        coin.rotation_euler = (math.radians(40 + f * 11), math.radians(18 + f * 2), math.radians(f * 4))
        key(coin, "rotation_euler", f, interp="LINEAR")
    cam.data.dof.use_dof = False                 # the penny AND the street below must both read
    return sc


# ── 2. hail ───────────────────────────────────────────────────────────────────
def lumpy(name, r, center, mat_, parent=None, seed=1, amp=0.12):
    ob = ellipsoid(name, (r, r * 0.93, r * 0.88), center, mat_, parent, segs=64, rings=32)
    rnd = random.Random(seed)
    tex = bpy.data.textures.new(name + "_n", "CLOUDS")
    tex.noise_scale = r * 1.4
    m = ob.modifiers.new("lumps", "DISPLACE")
    m.texture, m.strength, m.mid_level = tex, r * amp, 0.5
    m.texture_coords = "OBJECT"
    ob.rotation_euler = (rnd.random() * 6, rnd.random() * 6, rnd.random() * 6)
    return ob


def umbrella(parent, canopy_mat, hole_at=None, hole_r=0.0):
    """Canopy (8 panels, radius 0.55) on a shaft along +Z from the parent's origin. Faces inside hole_r of hole_at
    (local xy) are removed and replaced by torn flaps bent down."""
    R, H, segs, rings = 0.58, 0.2, 64, 22
    bm = bmesh.new()
    rows = []
    for i in range(rings + 1):
        rr = R * i / rings
        row = []
        for j in range(segs):
            a = 2 * math.pi * j / segs
            scallop = 1.0 - 0.06 * abs(math.sin(a * 4)) * (i / rings) ** 2     # panels sag between ribs
            z = H * (1 - (i / rings) ** 1.6) - 0.03 * (i / rings) ** 3
            row.append(bm.verts.new((rr * scallop * math.cos(a), rr * scallop * math.sin(a), z + 0.62)))
        rows.append(row)
    for i in range(rings):
        for j in range(segs):
            q = (rows[i][j], rows[i][(j + 1) % segs], rows[i + 1][(j + 1) % segs], rows[i + 1][j])
            c = sum((v.co for v in q), Vector()) / 4
            if hole_at is not None and (Vector((c.x, c.y)) - Vector(hole_at)).length < hole_r:
                continue
            bm.faces.new(q)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context="VERTS")
    me = bpy.data.meshes.new("canopy")
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(canopy_mat)
    can = link(bpy.data.objects.new("canopy", me), parent)
    sol = can.modifiers.new("thick", "SOLIDIFY")
    sol.thickness = 0.003
    metal = mat("shaft", (0.75, 0.75, 0.78), rough=0.25, metallic=1.0)
    cylinder("shaft", 0.008, 0.85, (0, 0, 0.4), metal, parent)
    cylinder("handle", 0.016, 0.13, (0, 0, -0.02), mat("handle", (0.05, 0.03, 0.02), rough=0.5), parent)
    def cz(x, y):                                                    # canopy height (local) at x, y
        t = min(1.0, Vector((x, y)).length / R)
        return H * (1 - t ** 1.6) - 0.03 * t ** 3 + 0.62
    for j in range(8):                                               # ribs, just under the fabric
        a = 2 * math.pi * j / 8
        p0, p1 = Vector((0, 0, cz(0, 0) - 0.006)), Vector((R * 0.98 * math.cos(a), R * 0.98 * math.sin(a), 0))
        p1.z = cz(p1.x, p1.y) - 0.006
        d = p1 - p0
        rib = cylinder(f"rib{j}", 0.0028, d.length, (p0 + p1) / 2, metal, parent, segs=8)
        rib.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    flaps = []
    if hole_at is not None:
        hx, hy = hole_at
        for k in range(6):                                           # torn flaps hanging into the hole
            a = 2 * math.pi * k / 6 + 0.3
            bmf = bmesh.new()
            w = 0.05
            p0 = Vector((hx + hole_r * math.cos(a - 0.5), hy + hole_r * math.sin(a - 0.5), 0))
            p1 = Vector((hx + hole_r * math.cos(a + 0.5), hy + hole_r * math.sin(a + 0.5), 0))
            tip = Vector((hx + (hole_r - 0.05) * math.cos(a), hy + (hole_r - 0.05) * math.sin(a), -0.09 - 0.025 * (k % 3)))
            for q in (p0, p1):
                q.z = cz(q.x, q.y) - cz(hx, hy) - 0.004
            vs = [bmf.verts.new(p) for p in (p0, p1, tip)]
            bmf.faces.new(vs)
            mf = bpy.data.meshes.new(f"flap{k}")
            bmf.to_mesh(mf)
            bmf.free()
            mf.materials.append(canopy_mat)
            zc = cz(hx, hy)
            fl = link(bpy.data.objects.new(f"flap{k}", mf), parent)
            fl.location = (0, 0, zc)
            fl.modifiers.new("thick", "SOLIDIFY").thickness = 0.003
            flaps.append(fl)
    return can, flaps


def scene_hail(samples):
    sc = bk.new_scene(fps=FPS, samples=samples, frames=49)
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.35
    world(sc, (0.16, 0.19, 0.24), 0.9)
    light("key", "AREA", (2.5, -3.0, 4.0), 420, size=3.0, color=(0.82, 0.88, 1.0), aim=(0, 0, 1.4))
    light("rim", "AREA", (-1.8, 3.2, 3.0), 650, size=1.5, color=(0.7, 0.8, 1.0), aim=(0, 0, 1.6))
    light("fill", "AREA", (-3, -2.5, 1.2), 90, size=4.0, aim=(0, 0, 1.0))
    wet = add_bump(mat("wet_asphalt", (0.035, 0.037, 0.042), rough=0.12), 160, 0.25)
    box("ground", (40, 40, 0.1), (0, 6, -0.05), wet)
    box("curb", (40, 0.3, 0.15), (0, 2.6, 0.07), mat("curb", (0.4, 0.4, 0.4), rough=0.7))
    box("wall", (40, 0.5, 6), (0, 9, 3), add_bump(mat("brick_wall", (0.22, 0.12, 0.09), rough=0.85), 4, 0.4))
    P = build_dummy(at=(0, 0, 0.0), yaw=math.radians(8))
    red = mat("canopy_red", (0.75, 0.04, 0.05), rough=0.55, sss=0.0)
    # right hand holds the umbrella overhead
    P["sh1"].rotation_euler = (math.radians(-30), math.radians(-6), 0)    # usual grip: hand in front of the chest
    P["el1"].rotation_euler = (math.radians(-100), 0, 0)
    hand = pivot("grip", (0, 0, -0.33), P["el1"])
    up = pivot("umb", (0, 0, 0), hand)
    bpy.context.view_layer.update()
    # orient the umbrella straight up in world space, whatever the arm does
    mw = hand.matrix_world.to_3x3().inverted()
    up.rotation_euler = (mw @ Euler((math.radians(-6), math.radians(4), 0)).to_matrix()).to_euler()
    hole = (0.17, -0.12)
    can, flaps = umbrella(up, red, hole_at=hole, hole_r=0.115)
    ice = mat("ice", (0.92, 0.96, 1.0), rough=0.12, transmission=0.35, ior=1.31, coat=1.0, sss=0.3)
    core = mat("ice_core", (0.96, 0.98, 1.0), rough=0.4, sss=0.6)
    light("ice_light", "AREA", (0.9, -1.6, 2.1), 240, size=0.8, color=(0.9, 0.95, 1.0), aim=(0.35, -0.4, 1.8))
    light("ice_ground", "AREA", (1.2, -1.4, 0.9), 90, size=0.6, color=(0.9, 0.95, 1.0), aim=(0.45, -0.3, 0.1))
    bpy.context.view_layer.update()
    hole_w = up.matrix_world @ Vector((hole[0], hole[1], 0.62 + 0.2 * (1 - (Vector(hole).length / 0.58) ** 1.6)))
    stone = pivot("stone", hole_w)
    lumpy("hail", 0.1, (0, 0, 0), ice, stone, seed=3, amp=0.3)
    lumpy("hail_core", 0.072, (0, 0, 0), core, stone, seed=5, amp=0.2)
    rk = random.Random(31)
    for j in range(9):                                                # knobby lobes, like the real record stone
        d = Vector((rk.uniform(-1, 1), rk.uniform(-1, 1), rk.uniform(-1, 1))).normalized()
        lumpy(f"knob{j}", rk.uniform(0.018, 0.032), d * 0.092, ice, stone, seed=40 + j, amp=0.7)
    ground_hit = Vector((0.45, -0.3, 0.1))                                 # lands beside his right foot, in frame
    # 0: half through the canopy; 3: past the shoulder; 6: hits the ground; bounces and settles
    for f, loc, interp in ((0, hole_w + Vector((0, 0, -0.13)), "LINEAR"), (3, hole_w + Vector((0.12, -0.08, -1.1)), "LINEAR"),
                           (5, ground_hit, "BEZIER"), (9, ground_hit + Vector((0.12, -0.1, 0.18)), "BEZIER"),
                           (14, ground_hit + Vector((0.22, -0.18, 0.0)), "BEZIER"), (48, ground_hit + Vector((0.24, -0.2, 0.0)), "CONSTANT")):
        key(stone, "location", f, loc, interp)
    for f, r in ((0, (0.3, 0.2, 0)), (14, (2.2, 1.0, 0.6)), (48, (2.3, 1.05, 0.6))):
        key(stone, "rotation_euler", f, r)
    # ice chips: burst from the canopy at frame 0, and from the ground hit at frame 5
    rnd = random.Random(9)
    chip_m = mat("chip", (0.9, 0.95, 1.0), rough=0.05, transmission=0.9, ior=1.31)
    for k in range(26):
        origin = hole_w if k < 12 else ground_hit
        f0 = 0 if k < 12 else 5
        c = lumpy(f"chip{k}", rnd.uniform(0.006, 0.016), origin, chip_m, seed=20 + k, amp=0.5)
        v = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(0.2, 1.2) if k >= 12 else rnd.uniform(-0.6, 0.6))).normalized()
        sp = rnd.uniform(1.5, 3.5)
        for df in (0, 4, 8, 12):
            t = df / FPS
            p = origin + v * sp * t + Vector((0, 0, -4.9 * t * t))
            p.z = max(p.z, 0.01)
            key(c, "location", f0 + df, p, "LINEAR")
        if f0:
            hide_until(c, f0)
    # pose beats: flinch at the impact, then look at the stone, then up through the hole
    head, ch = P["head"], P["chest"]
    for f, hr, cr, sh, el in ((0, (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0)),
                              (6, (math.radians(12), 0, math.radians(-20)), (math.radians(6), 0, math.radians(8)),
                               (math.radians(-95), math.radians(-30), 0), (math.radians(-110), 0, 0)),
                              (24, (math.radians(30), 0, math.radians(-38)), (math.radians(10), 0, math.radians(-10)),
                               (math.radians(-60), math.radians(-20), 0), (math.radians(-60), 0, 0)),
                              (40, (math.radians(-38), 0, math.radians(-8)), (math.radians(-4), 0, 0),
                               (math.radians(-10), math.radians(-12), 0), (math.radians(-15), 0, 0)),
                              (48, (math.radians(-40), 0, math.radians(-8)), (math.radians(-4), 0, 0),
                               (math.radians(-10), math.radians(-12), 0), (math.radians(-15), 0, 0))):
        key(head, "rotation_euler", f, hr)
        key(ch, "rotation_euler", f, cr)
        key(P["sh-1"], "rotation_euler", f, sh)
        key(P["el-1"], "rotation_euler", f, el)
    # rain
    rain = mat("rain", (0.8, 0.85, 0.95), rough=0.1, alpha=0.35)
    for k in range(420):
        x, y, z = rnd.uniform(-2.5, 2.8), rnd.uniform(-2.0, 6.0), rnd.uniform(0.0, 3.6)
        cylinder(f"rain{k}", 0.0012, rnd.uniform(0.12, 0.3), (x, y, z), rain, rot=(math.radians(6), 0, 0), segs=6)
    cam = cam_free(sc, 24, (1.0, -3.3, 1.0), (0.15, -0.3, 1.2))
    for f, loc, at in ((0, (0.72, -1.85, 1.55), (0.22, -0.3, 1.86)), (6, (0.85, -2.6, 1.25), (0.2, -0.35, 1.45)),
                       (12, (1.0, -3.3, 1.0), (0.22, -0.4, 1.15)), (24, (0.98, -3.2, 0.98), (0.25, -0.4, 1.1)),
                       (48, (0.75, -2.3, 1.15), (0.2, -0.3, 1.75))):
        aim(cam, loc, at)
        key(cam, "location", f)
        key(cam, "rotation_euler", f)
    cam.data.dof.use_dof = True
    cam.data.dof.focus_distance = 3.2
    cam.data.dof.aperture_fstop = 5.6
    return sc


# ── 3. popcorn ────────────────────────────────────────────────────────────────
def kernel_petals(parent, hull_mat, n=4):
    """Hull of a kernel (flattened teardrop, ~9 mm tall) cut into n petals that hinge at the tip (base)."""
    petals = []
    rx, ry, rz = 0.0042, 0.0026, 0.0047
    for k in range(n):
        a0, a1 = 2 * math.pi * k / n + 0.05, 2 * math.pi * (k + 1) / n - 0.05
        bm = bmesh.new()
        rows = []
        for i in range(13):
            v = math.pi * i / 12                                      # 0 = top, pi = tip
            row = []
            for j in range(9):
                a = a0 + (a1 - a0) * j / 8
                taper = 1.0 - 0.45 * (i / 12) ** 2                     # pointed tip
                x = rx * math.sin(v) * math.cos(a) * taper
                y = ry * math.sin(v) * math.sin(a) * taper
                z = rz * math.cos(v) + rz
                row.append(bm.verts.new((x, y, z)))
            rows.append(row)
        for i in range(12):
            for j in range(8):
                bm.faces.new((rows[i][j], rows[i][j + 1], rows[i + 1][j + 1], rows[i + 1][j]))
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
        me = bpy.data.meshes.new(f"petal{k}")
        bm.to_mesh(me)
        bm.free()
        for p in me.polygons:
            p.use_smooth = True
        me.materials.append(hull_mat)
        hinge = pivot(f"hinge{k}", (0, 0, 0), parent, rot=(0, 0, (a0 + a1) / 2))
        pet = link(bpy.data.objects.new(f"petal{k}", me), hinge)
        pet.rotation_euler = (0, 0, -(a0 + a1) / 2)
        pet.modifiers.new("thick", "SOLIDIFY").thickness = 0.00025
        petals.append(hinge)
    return petals


def scene_popcorn(samples):
    sc = bk.new_scene(fps=FPS, samples=samples, frames=49)
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.3
    world(sc, (0.01, 0.008, 0.006), 1.0)
    light("key", "AREA", (-0.06, -0.05, 0.07), 0.45, size=0.05, color=(1.0, 0.88, 0.72), aim=(0, 0, 0.005))
    light("rim", "AREA", (0.05, 0.08, 0.04), 0.9, size=0.04, color=(1.0, 0.5, 0.15), aim=(0, 0, 0.006))
    light("fill", "AREA", (0.07, -0.06, 0.02), 0.1, size=0.08, color=(0.75, 0.8, 1.0), aim=(0, 0, 0.004))
    iron = add_bump(mat("iron", (0.05, 0.045, 0.04), rough=0.35, metallic=0.9), 2500, 0.3, distance=0.0003)
    cylinder("pan", 0.15, 0.004, (0, 0, -0.002), iron)
    hull = mat("hull", (1.0, 0.38, 0.01), rough=0.14, sss=0.12, coat=0.35)
    hull.node_tree.nodes["Principled BSDF"].inputs["Subsurface Radius"].default_value = (0.002, 0.0012, 0.0004)
    foam = add_bump(mat("foam", (0.97, 0.93, 0.82), rough=0.65, sss=0.25), 2600, 0.6, distance=0.0004)
    foam.node_tree.nodes["Principled BSDF"].inputs["Subsurface Radius"].default_value = (0.001, 0.0008, 0.0005)
    k = pivot("kernel", (0, 0, 0.0))
    body = pivot("kernel_body", (0, 0, 0), k, rot=(math.radians(90), 0, math.radians(105)))   # lying on its broad face
    petals = kernel_petals(body, hull)
    tip = ellipsoid("tip_cap", (0.0016, 0.0011, 0.0012), (0, 0, 0.0004), mat("tipcap", (0.85, 0.75, 0.55), rough=0.6), body)
    # starch foam: metaballs that swell out of the split, then a "leg" lobe that pushes on the pan
    mb = bpy.data.metaballs.new("foam")
    mb.resolution, mb.render_resolution, mb.threshold = 0.0003, 0.00018, 0.6
    fo = link(bpy.data.objects.new("foam", mb), body)
    mb.materials.append(foam)
    rnd = random.Random(2)
    blobs = []
    for i in range(14):
        e = mb.elements.new()
        d = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.2, 1))).normalized()
        e.co = Vector((0, 0, 0.0048)) + d * 0.0012
        blobs.append((e, d))
    leg = mb.elements.new()
    def grow(f, s, spread, legv):
        for e, d in blobs:
            e.radius = 0.0029 * s
            e.co = Vector((0, 0, 0.0052)) + d * 0.0026 * spread
            e.keyframe_insert("radius", frame=f)
            e.keyframe_insert("co", frame=f)
        leg.radius = 0.0034 * legv
        leg.co = Vector((0.0, -0.0048 * legv, 0.0035))                 # toward the pan (body is lying)
        leg.keyframe_insert("radius", frame=f)
        leg.keyframe_insert("co", frame=f)
    for f, s, spread, legv in ((0, 0.7, 0.5, 0.0), (12, 1.05, 1.0, 0.3), (24, 1.35, 1.5, 1.0), (48, 1.55, 1.8, 1.1)):
        grow(f, s, spread, legv)
    for f, opening in ((0, 14), (12, 34), (24, 48), (48, 55)):
        for h in petals:
            h.rotation_euler = (0, math.radians(opening * 0.7), h.rotation_euler.z)
            # hinge opens by tilting each petal outward about its own axis
            key(h, "rotation_euler", f)
    # the jump: the leg pushes, the kernel lifts and flips
    for f, loc, rot in ((0, (0, 0, 0.0026), (0, 0, 0)), (24, (0.0, 0.0, 0.0034), (math.radians(-18), 0, 0)),
                        (30, (0.0005, 0.001, 0.007), (math.radians(-70), 0, math.radians(10))),
                        (48, (0.003, 0.004, 0.021), (math.radians(-200), math.radians(20), math.radians(25)))):
        key(k, "location", f, loc)
        key(k, "rotation_euler", f, rot)
    # out-of-focus neighbours: raw kernels and popped ones
    for i in range(12):
        a, r = rnd.uniform(0.15 * math.pi, 0.85 * math.pi), rnd.uniform(0.022, 0.06)    # behind the kernel only
        x, y = r * math.cos(a), r * math.sin(a)
        if i % 3 == 0:
            for j in range(6):
                ellipsoid(f"pop{i}_{j}", (0.0035, 0.003, 0.003), (x + rnd.uniform(-0.003, 0.003), y + rnd.uniform(-0.003, 0.003),
                          0.003 + rnd.uniform(0, 0.003)), foam, segs=24, rings=12)
        else:
            ellipsoid(f"raw{i}", (0.0042, 0.0026, 0.0045), (x, y, 0.0025), hull, segs=24, rings=12).rotation_euler = \
                (math.radians(90), 0, rnd.uniform(0, 6))
    cam = cam_free(sc, 90, (0.0, -0.08, 0.03), (0, 0, 0.005))
    for f, loc, at in ((0, (0.0, -0.072, 0.024), (0.0005, 0.0, 0.0045)), (24, (0.0, -0.078, 0.026), (0.0005, 0.0, 0.006)),
                       (48, (0.002, -0.095, 0.036), (0.002, 0.003, 0.014))):
        aim(cam, loc, at)
        key(cam, "location", f)
        key(cam, "rotation_euler", f)
    cam.data.dof.use_dof = True
    cam.data.dof.focus_object = k
    cam.data.dof.aperture_fstop = 64.0          # macro: the scene is millimetres, so the physical aperture must be tiny
    return sc


# ── 3b. quicksand (replaces popcorn: the macro kernel looked like candy) ─────
def mat_sand(name, color, rough, wet=0.0):
    m = add_bump(mat(name, color, rough=rough, coat=wet), 900, 0.35, distance=0.002)
    return m


def scene_quicksand(samples):
    sc = bk.new_scene(fps=FPS, samples=samples, frames=49)
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.4
    world(sc, (0.5, 0.66, 0.9), 0.9)
    light("sun", "SUN", (0, 0, 20), 4.6, size=2.0, color=(1.0, 0.84, 0.62),
          rot=(math.radians(62), 0, math.radians(-35)))
    light("fill", "AREA", (-2.5, -3.0, 1.5), 120, size=3.0, color=(0.75, 0.82, 1.0), aim=(0, 0, 0.4))
    dry = mat_sand("dry_sand", (0.62, 0.47, 0.3), 0.9)
    box("desert", (60, 60, 0.1), (0, 10, -0.06), dry)
    rnd = random.Random(12)
    for k in range(7):                                                  # dunes on the horizon
        ellipsoid(f"dune{k}", (rnd.uniform(5, 12), rnd.uniform(3, 6), rnd.uniform(0.8, 2.2)),
                  (rnd.uniform(-18, 18), rnd.uniform(10, 26), -0.3), dry, segs=48, rings=24)
    # the quicksand pool: darker, wet, rippling rings around the dummy
    m, b, nt = bk._principled("quicksand")
    b.inputs["Base Color"].default_value = (0.2, 0.135, 0.075, 1)
    b.inputs["Roughness"].default_value = 0.5
    b.inputs["Coat Weight"].default_value = 0.22
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.wave_type, wave.rings_direction = "RINGS", "SPHERICAL"
    wave.inputs["Scale"].default_value = 2.2
    wave.inputs["Distortion"].default_value = 1.5
    nt.links.new(tc.outputs["Object"], wave.inputs["Vector"])
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 900
    add = nt.nodes.new("ShaderNodeMath"); add.operation = "ADD"
    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = 0.25
    nt.links.new(wave.outputs["Fac"], add.inputs[0])
    nt.links.new(noise.outputs["Fac"], mul.inputs[0])
    nt.links.new(mul.outputs[0], add.inputs[1])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.6
    bump.inputs["Distance"].default_value = 0.01
    nt.links.new(add.outputs[0], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    pool = cylinder("pool", 4.0, 0.02, (0, 0, 0.0), m, segs=128)
    for f, ph in ((0, 0.0), (48, -9.0)):                                 # ripples spread outward
        wave.inputs["Phase Offset"].default_value = ph
        wave.inputs["Phase Offset"].keyframe_insert("default_value", frame=f)
    P = build_dummy(at=(0, 0, 0), yaw=math.radians(-10))
    wetlip = mat_sand("wet_lip", (0.26, 0.18, 0.1), 0.3, wet=0.5)
    for k in range(18):                                                  # a lumpy rim of wet sand heaped around him
        a = 2 * math.pi * k / 18
        lumpy(f"rim{k}", rnd.uniform(0.07, 0.11), (0.27 * math.cos(a), 0.2 * math.sin(a), 0.0), wetlip, seed=80 + k, amp=0.5)
    root = P["root"]
    # sinking fast at 0.0 s, then he stops at the waist: he floats (quicksand ~2x denser than a body)
    for f, z in ((0, -0.74), (6, -0.86), (12, -0.95), (20, -1.03), (28, -1.06), (40, -1.045), (48, -1.055)):
        key(root, "location", f, (0, 0, z))
    poses = {   # frame: (sh-1, el-1, sh1, el1, head, chest)
        0: ((-165, -35, 0), (-20, 0, 0), (-160, 35, 0), (-25, 0, 0), (25, 0, 10), (8, 0, 0)),
        6: ((-150, -45, 0), (-35, 0, 0), (-170, 25, 0), (-15, 0, 0), (20, 0, -12), (6, 0, 4)),
        12: ((-170, -30, 0), (-15, 0, 0), (-150, 40, 0), (-30, 0, 0), (15, 0, 8), (4, 0, -4)),
        24: ((-25, 70, 0), (-10, 0, 0), (-25, -70, 0), (-10, 0, 0), (30, 0, 0), (6, 0, 0)),
        36: ((-10, 64, 0), (-8, 0, 0), (-10, -64, 0), (-8, 0, 0), (-5, 0, 6), (0, 0, 0)),
        48: ((-10, 63, 0), (-8, 0, 0), (-10, -63, 0), (-8, 0, 0), (-8, 0, 10), (0, 0, 0)),
    }
    for f, (a, b2, c, d, h, ch) in poses.items():
        for name, v in (("sh-1", a), ("el-1", b2), ("sh1", c), ("el1", d), ("head", h), ("chest", ch)):
            key(P[name], "rotation_euler", f, tuple(math.radians(x) for x in v))
    # sand clumps flicked up by his flailing at the start
    clump = mat_sand("clump", (0.4, 0.29, 0.18), 0.6)
    for k in range(26):
        c = lumpy(f"clump{k}", rnd.uniform(0.02, 0.045), (0, 0, 0), clump, seed=60 + k, amp=0.5)
        v = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 0.4), rnd.uniform(0.6, 1.4)))
        o = Vector((rnd.uniform(-0.35, 0.35), rnd.uniform(-0.25, 0.1), 0.02))
        for df in (0, 6, 12, 18):
            t = df / FPS
            p = o + v * 2.2 * t + Vector((0, 0, -4.9 * t * t))
            p.z = max(p.z, 0.0)
            key(c, "location", df, p, "LINEAR")
    cam = cam_free(sc, 28, (1.0, -2.9, 0.6), (0, 0, 0.5))
    for f, loc, at in ((0, (1.0, -2.9, 0.62), (0.0, 0.0, 0.62)), (12, (0.95, -2.8, 0.55), (0.0, 0.0, 0.45)),
                       (24, (0.9, -2.6, 0.5), (0.0, 0.0, 0.3)), (48, (0.7, -2.0, 0.42), (0.0, 0.0, 0.3))):
        aim(cam, loc, at)
        key(cam, "location", f)
        key(cam, "rotation_euler", f)
    cam.data.dof.use_dof = True
    cam.data.dof.focus_distance = 2.7
    cam.data.dof.aperture_fstop = 5.6
    return sc


SCENES = {"penny": scene_penny, "hail": scene_hail, "popcorn": scene_popcorn, "quicksand": scene_quicksand}

if __name__ == "__main__":
    out, which = sys.argv[1], sys.argv[2]
    frames = [int(f) for f in sys.argv[3:]] or [0, 12, 24, 48]
    samples = int(os.environ.get("PITCH_SAMPLES", "24"))
    sc = SCENES[which](samples)
    os.makedirs(out, exist_ok=True)
    for f in frames:
        sc.frame_set(f)
        sc.render.filepath = os.path.join(out, f"{which}_{f:03d}.png")
        bpy.ops.render.render(write_still=True)
        print("saved", sc.render.filepath, flush=True)
