"""
blender_tensec.py — scenes and timelines for the "10 Seconds in ___" Shorts (dummy_shorts.py; LESSONS rule 21).

The dummy is dropped somewhere impossible and a clock counts 10 to 0. Physics does the acting: he falls, burns, is
crushed or floats; he never has to perform a fine action. One place and a handful of cameras per Short, nothing slow
to render (no glass, no volumes): the budget is 2 hours of rendering per Short.

  lava   he lands ON the lava (it is ~3x as dense as he is), his vinyl skin and foam burn off, and the steel
         skeleton underneath glows but does not melt (steel ~1,400 C, Hawaiian lava ~1,170 C)
"""
import math
import random

import bmesh
import bpy
from mathutils import Vector

import blender_kit as bk
import blender_pitches as bp

FPS = 24
EPS = 0.02
RES = (540, 960)      # on a phone this is indistinguishable from 720x1280 and renders in 56% of the time
SAMPLES = 8           # render with DUMMY_SAMPLES=8: emission-lit scenes denoise cleanly
O = {}


# ── small helpers ─────────────────────────────────────────────────────────────
def k(o, path, f, value, interp="BEZIER"):
    setattr(o, path, value)
    o.keyframe_insert(path, frame=f)
    if o.animation_data and o.animation_data.action:
        for fc in curves(o.animation_data.action):
            kp = fc.keyframe_points[-1] if abs(fc.keyframe_points[-1].co[0] - f) < 1e-3 else next(
                (q for q in fc.keyframe_points if abs(q.co[0] - f) < 1e-3), None)
            if kp is not None and fc.data_path == path:
                kp.interpolation = interp


def kval(sock, f, v):
    sock.default_value = v
    sock.keyframe_insert("default_value", frame=f)


def curves(action):
    c = getattr(action, "fcurves", None)
    if c is None:
        c = [fc for layer in action.layers for strip in layer.strips for bag in strip.channelbags for fc in bag.fcurves]
    return c


def linear(idblock):
    if idblock.animation_data and idblock.animation_data.action:
        for fc in curves(idblock.animation_data.action):
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"


def shown(o, f0, f1=None):
    """Rendered only in [f0, f1)."""
    keys = [(0, True), (f0, False)] + ([(f1, True)] if f1 is not None else [])
    for f, h in keys:
        o.hide_render = h
        o.keyframe_insert("hide_render", frame=f)


def gone(o, f):
    """Rendered until frame f, then never again."""
    for fr, h in ((0, False), (f, True)):
        o.hide_render = h
        o.keyframe_insert("hide_render", frame=fr)


def shot(cam, f0, f1, loc0, at0, loc1=None, at1=None, lens=None):
    loc1, at1 = loc1 or loc0, at1 or at0
    for f, loc, at in ((f0, loc0, at0), (f1 - EPS, loc1, at1)):
        bp.aim(cam, Vector(loc), Vector(at))
        k(cam, "location", f, cam.location.copy(), "LINEAR")
        k(cam, "rotation_euler", f, cam.rotation_euler.copy(), "LINEAR")
        if lens:
            cam.data.lens = lens
            cam.data.keyframe_insert("lens", frame=f)


def pose(P, f, **rots):
    """sh/el/hip/kn set both sides (mirrored in y and z); sh_1 / sh1 etc. set one side."""
    for name, deg in rots.items():
        if name in ("sh", "el", "hip", "kn"):
            for s in (-1, 1):
                k(P[f"{name}{s}"], "rotation_euler", f, (math.radians(deg[0]), math.radians(deg[1] * -s),
                                                         math.radians(deg[2] * -s)))
        else:
            k(P[name.replace("_", "-") if name.endswith("_1") else name], "rotation_euler", f,
              tuple(math.radians(x) for x in deg))


def emit(name, color, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value, e.inputs["Strength"].default_value = (*color, 1), strength
    nt.links.new(e.outputs[0], nt.nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
    return m


def no_light(o):
    """A glowing prop that is seen but neither lights nor shadows the scene (keeps the render clean and fast)."""
    o.visible_shadow = o.visible_diffuse = o.visible_glossy = False
    return o


# ── the steel skeleton under the skin ─────────────────────────────────────────
SKIN = {
    "legs": ["thigh{s}", "kneecap{s}", "shin{s}", "foot{s}", "knj{s}", "hipj{s}"],
    "hips": ["hips", "belt", "lumbar0", "lumbar1", "lumbar2"],
    "torso": ["torso", "sternum", "chest_tgt", "chest_label", "shcap{s}", "neckdisc0", "neckdisc1", "neckdisc2"]
             + [f"ribF{j}" for j in range(4)] + [f"ribS{j}{{s}}" for j in range(4)],
    "arms": ["upper{s}", "fore{s}", "wrist{s}", "hand{s}", "thumb{s}", "shj{s}", "elj{s}"],
    "head": ["skull", "mouth", "eye{s}", "ear{s}", "head_tgt{s}"],
}


def skin_objects(region):
    out = []
    for n in SKIN[region]:
        for s in ((-1, 1) if "{s}" in n else (0,)):
            out.append(bpy.data.objects[n.format(s=s)])
    return out


def heat_steel():
    """Bare steel that glows as it heats: the `heat` value (0-1) drives an orange emission."""
    m, b, nt = bk._principled("bone_steel")
    b.inputs["Base Color"].default_value = (0.13, 0.13, 0.14, 1)
    b.inputs["Metallic"].default_value, b.inputs["Roughness"].default_value = 1.0, 0.32
    heat = nt.nodes.new("ShaderNodeValue")
    heat.name = "heat"
    ramp = nt.nodes.new("ShaderNodeValToRGB")                    # dull red -> orange -> yellow
    e = ramp.color_ramp.elements
    e[0].position, e[0].color = 0.0, (0.2, 0.0, 0.0, 1)
    e[1].position, e[1].color = 1.0, (1.0, 0.2, 0.01, 1)
    mid = ramp.color_ramp.elements.new(0.55)
    mid.color = (0.9, 0.06, 0.0, 1)
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = 0.9
    nt.links.new(heat.outputs[0], ramp.inputs["Fac"])
    nt.links.new(heat.outputs[0], mul.inputs[0])
    nt.links.new(ramp.outputs["Color"], b.inputs["Emission Color"])
    nt.links.new(mul.outputs[0], b.inputs["Emission Strength"])
    O["heat"] = heat.outputs[0]
    return m


def skeleton(P):
    """Steel bones inside every skin part (same pivots), so burning the skin off reveals them."""
    st = heat_steel()
    dark = bp.mat("socket", (0.005, 0.004, 0.004), rough=0.9)
    pel, ch, hd = P["pelvis"], P["chest"], P["head"]
    bp.box("b_pelvis", (0.22, 0.12, 0.1), (0, 0, 0.01), st, pel, bevel=0.02)
    bp.cylinder("b_spine", 0.026, 0.58, (0, 0, 0.3), st, ch, bevel=0.005)
    for j, z in enumerate((0.25, 0.31, 0.37, 0.43)):             # rib hoops
        bpy.ops.mesh.primitive_torus_add(major_radius=0.15, minor_radius=0.012, major_segments=40, minor_segments=10)
        rib = bpy.context.active_object
        rib.name = f"b_rib{j}"
        rib.location, rib.scale = (0, -0.005, z), (1.0 + 0.06 * (j - 1.5) * -1, 0.6, 1.0)
        rib.data.materials.append(st)
        for p in rib.data.polygons:
            p.use_smooth = True
        rib.parent = ch
    bp.cylinder("b_collar", 0.018, 0.48, (0, 0, 0.47), st, ch, rot=(0, math.radians(90), 0), bevel=0.004)
    bp.sculpted_head("b_skull", st, hd, center=(0, 0.004, 0.125), radii=(0.086, 0.096, 0.114))
    for s in (-1, 1):
        bp.ellipsoid(f"b_socket{s}", (0.021, 0.012, 0.019), (s * 0.036, -0.078, 0.128), dark, hd)
    bp.box("b_nose", (0.012, 0.01, 0.026), (0, -0.092, 0.093), dark, hd)
    for j in range(5):                                           # a grille where the mouth was
        bp.box(f"b_tooth{j}", (0.006, 0.008, 0.02), ((j - 2) * 0.012, -0.083, 0.052), dark, hd)
    for s in (-1, 1):
        sh, el, hip, kn = P[f"sh{s}"], P[f"el{s}"], P[f"hip{s}"], P[f"kn{s}"]
        bp.ellipsoid(f"b_shj{s}", (0.034, 0.034, 0.034), (0, 0, 0), st, sh)
        bp.cylinder(f"b_upper{s}", 0.017, 0.3, (0, 0, -0.16), st, sh, bevel=0.004)
        bp.ellipsoid(f"b_elj{s}", (0.027, 0.027, 0.027), (0, 0, 0), st, el)
        bp.cylinder(f"b_fore{s}", 0.014, 0.27, (0, 0, -0.15), st, el, bevel=0.004)
        bp.box(f"b_hand{s}", (0.05, 0.018, 0.08), (0, 0, -0.325), st, el, bevel=0.006)
        bp.ellipsoid(f"b_hipj{s}", (0.04, 0.04, 0.04), (0, 0, 0), st, hip)
        bp.cylinder(f"b_thigh{s}", 0.022, 0.44, (0, 0, -0.235), st, hip, bevel=0.005)
        bp.ellipsoid(f"b_knj{s}", (0.034, 0.034, 0.034), (0, 0, 0), st, kn)
        bp.cylinder(f"b_shin{s}", 0.018, 0.4, (0, 0, -0.215), st, kn, bevel=0.005)
        bp.box(f"b_foot{s}", (0.06, 0.2, 0.03), (0, -0.05, -0.44), st, kn, bevel=0.008)


def charring(names=("dummy2_yellow", "dummy2_face"), color=(0.012, 0.009, 0.007), embers_on=True):
    """The painted skin blackens (and, with oxygen around, smoulders) as the shared `char` value goes 0 -> 1."""
    for name in names:
        nt = bpy.data.materials[name].node_tree
        b = nt.nodes["Principled BSDF"]
        src = b.inputs["Base Color"].links[0].from_socket
        char = nt.nodes.new("ShaderNodeValue")
        char.name = "char"
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        nt.links.new(src, mix.inputs["A"])
        mix.inputs["B"].default_value = (*color, 1)
        nt.links.new(char.outputs[0], mix.inputs["Factor"])
        nt.links.new(mix.outputs["Result"], b.inputs["Base Color"])
        O.setdefault("char", []).append(char.outputs[0])
        if not embers_on:
            rgh = nt.nodes.new("ShaderNodeMix")                  # baked paint goes matt and loses its clear coat
            rgh.data_type = "FLOAT"
            old = b.inputs["Roughness"].links[0].from_socket
            nt.links.new(old, rgh.inputs["A"])
            rgh.inputs["B"].default_value = 0.92
            nt.links.new(char.outputs[0], rgh.inputs["Factor"])
            nt.links.new(rgh.outputs["Result"], b.inputs["Roughness"])
            coat = nt.nodes.new("ShaderNodeMath")
            coat.operation = "SUBTRACT"
            coat.inputs[0].default_value = 1.0
            nt.links.new(char.outputs[0], coat.inputs[1])
            cm = nt.nodes.new("ShaderNodeMath")
            cm.operation = "MULTIPLY"
            cm.inputs[1].default_value = 0.35
            nt.links.new(coat.outputs[0], cm.inputs[0])
            nt.links.new(cm.outputs[0], b.inputs["Coat Weight"])
            continue
        tc = nt.nodes.new("ShaderNodeTexCoord")
        nz = nt.nodes.new("ShaderNodeTexNoise")                  # embers creeping through the char
        nz.inputs["Scale"].default_value, nz.inputs["Detail"].default_value = 55.0, 6.0
        nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[1].position = 0.6, 0.7
        nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        nt.links.new(ramp.outputs["Color"], mul.inputs[0])
        nt.links.new(char.outputs[0], mul.inputs[1])
        gain = nt.nodes.new("ShaderNodeMath")
        gain.operation = "MULTIPLY"
        gain.inputs[1].default_value = 2.5
        nt.links.new(mul.outputs[0], gain.inputs[0])
        b.inputs["Emission Color"].default_value = (1.0, 0.16, 0.01, 1)
        nt.links.new(gain.outputs[0], b.inputs["Emission Strength"])


# ── fire ──────────────────────────────────────────────────────────────────────
def flame_mat():
    """A flame tongue: bright core at the base, orange to red toward the tip, torn by an animated noise."""
    m = bpy.data.materials.new("flame")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    t = nt.nodes.new("ShaderNodeMapRange")                       # 0 at the base, 1 at the tip (mesh z in -1..1)
    t.inputs["From Min"].default_value, t.inputs["From Max"].default_value = -1.0, 1.0
    nt.links.new(sep.outputs["Z"], t.inputs["Value"])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.noise_dimensions = "4D"
    nz.inputs["Scale"].default_value, nz.inputs["Detail"].default_value = 3.4, 4.0
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0, 1.0, 0.4)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs[0], nz.inputs["Vector"])
    O["flame_w"] = nz.inputs["W"]
    a = nt.nodes.new("ShaderNodeMath")                           # alpha = 1.25 - t - 0.9 * noise, sharpened
    a.operation = "SUBTRACT"
    a.inputs[0].default_value = 1.12
    nt.links.new(t.outputs["Result"], a.inputs[1])
    nmul = nt.nodes.new("ShaderNodeMath")
    nmul.operation = "MULTIPLY"
    nmul.inputs[1].default_value = 1.25
    nt.links.new(nz.outputs["Fac"], nmul.inputs[0])
    a2 = nt.nodes.new("ShaderNodeMath")
    a2.operation = "SUBTRACT"
    nt.links.new(a.outputs[0], a2.inputs[0])
    nt.links.new(nmul.outputs[0], a2.inputs[1])
    sharp = nt.nodes.new("ShaderNodeMapRange")
    sharp.inputs["From Min"].default_value, sharp.inputs["From Max"].default_value = 0.0, 0.22
    nt.links.new(a2.outputs[0], sharp.inputs["Value"])
    lw = nt.nodes.new("ShaderNodeLayerWeight")                   # soft silhouette: fade where the surface turns away
    lw.inputs["Blend"].default_value = 0.35
    inv = nt.nodes.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    nt.links.new(lw.outputs["Facing"], inv.inputs[1])
    base = nt.nodes.new("ShaderNodeMapRange")                    # nothing at the very base: no bulb under the flame
    base.inputs["From Min"].default_value, base.inputs["From Max"].default_value = 0.02, 0.2
    nt.links.new(t.outputs["Result"], base.inputs["Value"])
    e0 = nt.nodes.new("ShaderNodeMath")
    e0.operation = "MULTIPLY"
    nt.links.new(sharp.outputs["Result"], e0.inputs[0])
    nt.links.new(base.outputs["Result"], e0.inputs[1])
    edge = nt.nodes.new("ShaderNodeMath")
    edge.operation = "MULTIPLY"
    nt.links.new(e0.outputs[0], edge.inputs[0])
    nt.links.new(inv.outputs[0], edge.inputs[1])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    e = ramp.color_ramp.elements
    e[0].position, e[0].color = 0.0, (1.0, 0.42, 0.05, 1)
    e[1].position, e[1].color = 1.0, (0.45, 0.01, 0.0, 1)
    mid = ramp.color_ramp.elements.new(0.4)
    mid.color = (1.0, 0.13, 0.0, 1)
    nt.links.new(t.outputs["Result"], ramp.inputs["Fac"])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 2.6
    nt.links.new(ramp.outputs["Color"], em.inputs["Color"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(edge.outputs[0], mx.inputs[0])
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(em.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], nt.nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
    return m


def flame_mesh():
    """A teardrop on z in -1..1: fat at the base, a point at the tip."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=14, radius=1.0)
    for v in bm.verts:
        t = (v.co.z + 1) / 2
        w = 1.75 * t ** 0.4 * (1 - t) ** 0.9                     # closed at the base, widest low down, a point on top
        r = math.hypot(v.co.x, v.co.y)
        if r > 1e-6:
            v.co.x, v.co.y = v.co.x / r * w, v.co.y / r * w
    me = bpy.data.meshes.new("flame")
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    return me


def flames(parent, spots, f_end, rnd):
    """spots: (x, y, z, radius, height, frame it lights). Each tongue flickers on its own rhythm until f_end."""
    mat_, me = flame_mat(), flame_mesh()
    me.materials.append(mat_)
    out = []
    for j, (x, y, z, r, h, f0) in enumerate(spots):
        o = bpy.data.objects.new(f"flame{j}", me)
        bp.link(o, parent)
        no_light(o)
        k(o, "scale", 0, (0.001, 0.001, 0.001), "LINEAR")
        k(o, "scale", max(0, f0 - 1), (0.001, 0.001, 0.001), "LINEAR")
        f = f0
        grow = 0.35
        while f < f_end:
            grow = min(1.0, grow + 0.2)
            hh = h * grow * rnd.uniform(0.7, 1.25)
            rr = r * grow * rnd.uniform(0.85, 1.15)
            k(o, "scale", f, (rr, rr, hh), "LINEAR")
            k(o, "location", f, (x + rnd.uniform(-0.012, 0.012), y + rnd.uniform(-0.012, 0.012), z + hh * 0.9),
              "LINEAR")
            k(o, "rotation_euler", f, (rnd.uniform(-0.16, 0.16), rnd.uniform(-0.16, 0.16), rnd.uniform(0, 6.28)),
              "LINEAR")
            f += rnd.choice((2, 3, 3, 4))
        out.append(o)
    w = O["flame_w"]
    kval(w, 0, 0.0)
    kval(w, f_end, f_end * 0.11)                                 # the tearing noise keeps boiling upward
    linear(mat_.node_tree)
    return out


def embers(n, rnd, f_end, around=(0, 0), spread=2.2, mat_=None):
    """Sparks drifting up from the lava for the whole Short."""
    mat_ = mat_ or emit("ember", (1.0, 0.35, 0.03), 8.0)
    for j in range(n):
        o = no_light(bp.ellipsoid(f"ember{j}", (0.008, 0.008, 0.008), (0, 0, 0), mat_, segs=8, rings=6))
        f = rnd.randint(-40, 0)
        while f < f_end:
            life = rnd.randint(30, 60)
            x0, y0 = around[0] + rnd.uniform(-spread, spread), around[1] + rnd.uniform(-spread * 0.8, spread * 0.5)
            sway = rnd.uniform(-0.25, 0.25)
            top = rnd.uniform(1.2, 2.4)
            for q in range(0, life + 1, max(6, life // 4)):
                u = q / life
                k(o, "location", f + q, (x0 + sway * math.sin(u * 5), y0 + sway * u, 0.02 + top * u), "LINEAR")
            k(o, "scale", f, (0, 0, 0), "LINEAR"), k(o, "scale", f + 2, (1, 1, 1), "LINEAR")
            k(o, "scale", f + life - 5, (1, 1, 1), "LINEAR"), k(o, "scale", f + life, (0, 0, 0), "LINEAR")
            k(o, "location", f + life, (x0 + sway * math.sin(5), y0 + sway, 0.02 + top), "CONSTANT")
            f += life + rnd.randint(4, 20)


def splash(name, at, f0, n, rnd, mat_, speed=2.4, up=(1.6, 4.2), size=(0.02, 0.055), life=26):
    """Blobs of lava thrown up by an impact, on ballistic paths; they fall back and vanish into the surface."""
    for j in range(n):
        r = rnd.uniform(*size)
        o = no_light(bp.lumpy(f"{name}{j}", r, tuple(at), mat_, seed=300 + j, amp=0.4))
        a = rnd.uniform(0, 2 * math.pi)
        sp = rnd.uniform(0.4, 1.0) * speed
        v = Vector((math.cos(a) * sp, math.sin(a) * sp, rnd.uniform(*up)))
        for f in range(f0, f0 + life + 1, 2):
            t = (f - f0) / FPS
            p = Vector(at) + v * t + Vector((0, 0, -4.9 * t * t))
            k(o, "location", f, (p.x, p.y, p.z), "LINEAR")
        shown(o, max(0, f0), f0 + life)


# ── lava ──────────────────────────────────────────────────────────────────────
def lava_mat():
    """Dark crust plates with glowing cracks, and open, brighter lava around the spot where he lands."""
    m, b, nt = bk._principled("lava")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    warp = nt.nodes.new("ShaderNodeTexNoise")
    warp.inputs["Scale"].default_value, warp.inputs["Detail"].default_value = 0.9, 3.0
    wm = nt.nodes.new("ShaderNodeVectorMath")
    wm.operation = "SCALE"
    wm.inputs["Scale"].default_value = 0.55
    nt.links.new(tc.outputs["Object"], warp.inputs["Vector"])
    nt.links.new(warp.outputs["Color"], wm.inputs[0])
    add = nt.nodes.new("ShaderNodeVectorMath")
    nt.links.new(tc.outputs["Object"], add.inputs[0])
    nt.links.new(wm.outputs[0], add.inputs[1])
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.feature = "DISTANCE_TO_EDGE"
    vor.inputs["Scale"].default_value = 1.15
    nt.links.new(add.outputs[0], vor.inputs["Vector"])
    crack = nt.nodes.new("ShaderNodeMapRange")                   # 1 in the cracks, 0 on the plates
    crack.inputs["From Min"].default_value, crack.inputs["From Max"].default_value = 0.0, 0.11
    crack.inputs["To Min"].default_value, crack.inputs["To Max"].default_value = 1.0, 0.0
    nt.links.new(vor.outputs["Distance"], crack.inputs["Value"])
    grad = nt.nodes.new("ShaderNodeVectorMath")                  # distance from the landing spot
    grad.operation = "LENGTH"
    nt.links.new(tc.outputs["Object"], grad.inputs[0])
    pool = nt.nodes.new("ShaderNodeMapRange")                    # open lava within ~1.3 m, crust beyond ~3 m
    pool.inputs["From Min"].default_value, pool.inputs["From Max"].default_value = 0.9, 3.0
    pool.inputs["To Min"].default_value, pool.inputs["To Max"].default_value = 1.0, 0.0
    nt.links.new(grad.outputs["Value"], pool.inputs["Value"])
    churn = nt.nodes.new("ShaderNodeTexNoise")                   # slow swirls in the open lava
    churn.noise_dimensions = "4D"
    churn.inputs["Scale"].default_value, churn.inputs["Detail"].default_value = 1.8, 4.0
    nt.links.new(add.outputs[0], churn.inputs["Vector"])
    O["lava_w"] = churn.inputs["W"]
    cm = nt.nodes.new("ShaderNodeMapRange")
    cm.inputs["From Min"].default_value, cm.inputs["From Max"].default_value = 0.3, 0.75
    cm.inputs["To Min"].default_value, cm.inputs["To Max"].default_value = 0.45, 1.0
    nt.links.new(churn.outputs["Fac"], cm.inputs["Value"])
    open_ = nt.nodes.new("ShaderNodeMath")
    open_.operation = "MULTIPLY"
    nt.links.new(pool.outputs["Result"], open_.inputs[0])
    nt.links.new(cm.outputs["Result"], open_.inputs[1])
    heat = nt.nodes.new("ShaderNodeMath")
    heat.operation = "MAXIMUM"
    nt.links.new(crack.outputs["Result"], heat.inputs[0])
    nt.links.new(open_.outputs[0], heat.inputs[1])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    e = ramp.color_ramp.elements
    e[0].position, e[0].color = 0.0, (0.06, 0.002, 0.0, 1)
    e[1].position, e[1].color = 1.0, (1.0, 0.4, 0.04, 1)
    mid = ramp.color_ramp.elements.new(0.5)
    mid.color = (0.9, 0.09, 0.0, 1)
    nt.links.new(heat.outputs[0], ramp.inputs["Fac"])
    gain = nt.nodes.new("ShaderNodeMath")
    gain.operation = "MULTIPLY"
    gain.inputs[1].default_value = 2.0
    nt.links.new(heat.outputs[0], gain.inputs[0])
    b.inputs["Base Color"].default_value = (0.012, 0.01, 0.01, 1)
    b.inputs["Roughness"].default_value = 0.85
    nt.links.new(ramp.outputs["Color"], b.inputs["Emission Color"])
    nt.links.new(gain.outputs[0], b.inputs["Emission Strength"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.invert = True
    bump.inputs["Strength"].default_value, bump.inputs["Distance"].default_value = 0.8, 0.06
    nt.links.new(heat.outputs[0], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def scene_lava(samples):
    rnd = random.Random(21)
    sc = bk.new_scene(fps=FPS, res=RES, samples=samples, frames=49)
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.4
    sc.cycles.max_bounces, sc.cycles.diffuse_bounces, sc.cycles.glossy_bounces = 3, 1, 2
    sc.cycles.transparent_max_bounces = 8
    sc.cycles.adaptive_min_samples = 4                           # the black sky needs no more
    sc.view_settings.view_transform = "Standard"                 # AgX turns bright orange into peach; fire should clip to yellow
    sc.view_settings.look = "None"
    w = bp.world(sc, (0.02, 0.005, 0.002), 1.0)                 # the glow hanging in the crater
    O["world"] = w
    lava = bp.box("lava", (120, 120, 0.2), (0, 0, -0.1), lava_mat())
    lava.visible_shadow = False
    O["lava"] = lava
    rock = bp.add_bump(bp.mat("basalt", (0.02, 0.017, 0.016), rough=0.9), 3.0, 0.9, distance=0.08)
    for j in range(16):                                          # crater wall: dark lumps on the horizon
        a = math.radians(-70 + 220 * j / 15) + rnd.uniform(-0.08, 0.08)
        d = rnd.uniform(15, 24)
        bp.lumpy(f"wall{j}", rnd.uniform(4.5, 8.5), (d * math.cos(a), 6 + d * math.sin(a), rnd.uniform(-1.5, 0.5)),
                 rock, seed=40 + j, amp=0.35)
    for j in range(9):                                           # crust blocks riding the lava behind him
        a, d = rnd.uniform(0.25, 2.9), rnd.uniform(3.2, 8.0)      # never between him and a camera
        o = bp.lumpy(f"block{j}", rnd.uniform(0.25, 0.7), (d * math.cos(a), 0.8 + d * math.sin(a), -0.05), rock,
                     seed=70 + j, amp=0.5)
        o.scale = (1.0, 1.0, 0.35)
    # light: the lava itself from below, a warm key from the camera side so his front reads, a cool rim from behind
    bp.light("key", "AREA", (-1.8, -3.6, 1.2), 50, size=3.0, color=(1.0, 0.62, 0.36), aim=(0, 0, 0.6))
    bp.light("under", "AREA", (0, -0.6, -0.4), 130, size=3.5, color=(1.0, 0.33, 0.06), rot=(math.radians(180), 0, 0))
    bp.light("rim", "AREA", (2.2, 3.4, 3.2), 300, size=2.5, color=(0.55, 0.7, 1.0), aim=(0, 0, 0.7))
    fire = bp.light("fire", "POINT", (0, -0.5, 0.8), 0.0, color=(1.0, 0.45, 0.1))
    fire.data.shadow_soft_size = 0.5
    O["fire"] = fire
    P = bp.build_dummy_v2(at=(0, 0, 0), yaw=math.radians(-18), label="TEST 06")
    skeleton(P)
    charring()
    O["P"], O["rnd"] = P, rnd
    O["blob"] = emit("lava_blob", (1.0, 0.2, 0.01), 2.4)
    cam = bp.cam_free(sc, 26, (0.9, -3.4, 0.6), (0, 0, 0.8))
    cam.data.dof.use_dof = False
    return sc


SEAT_Z = -0.86          # root height when he sits on the lava: hips a few centimetres into it, no deeper


def timeline_lava(sc, T):
    fr = [int(round(t * FPS)) for t in T["starts"]] + [T["frames"]]
    S = dict(zip(T["shots"], zip(fr[:-1], fr[1:])))
    end = T["frames"] + 2
    sc.render.motion_blur_position = "START"
    cam, P, rnd = bpy.data.objects["cam"], O["P"], O["rnd"]
    root = P["root"]
    z = lambda f, v, i="BEZIER": k(root, "location", f, Vector((0, 0, v)), i)
    kval(O["lava_w"], 0, 0.0)
    kval(O["lava_w"], end, end / FPS * 0.22)
    linear(bpy.data.materials["lava"].node_tree)

    # 1 drop: frame 0 is the impact -- he comes down feet first, lava flies, his legs give and he sits ON it
    a, b = S["drop"]
    shot(cam, a, b, (1.25, -4.2, 0.72), (0, -0.1, 0.98), (1.0, -3.4, 0.6), (0, -0.2, 0.5), lens=28)
    z(0, 0.34, "LINEAR"), z(3, -0.05, "LINEAR"), z(7, -0.12), z(22, SEAT_Z + 0.04), z(30, SEAT_Z), z(end, SEAT_Z - 0.03)
    pose(P, 0, sh=(-150, -30, 0), el=(-25, 0, 0), hip=(-12, 0, 0), kn=(18, 0, 0), chest=(6, 0, 0), head=(18, 0, 0))
    pose(P, 4, sh=(-125, -50, 0), el=(-40, 0, 0), hip=(-35, 0, 0), kn=(60, 0, 0), chest=(14, 0, 0), head=(-12, 0, 0))
    pose(P, 12, sh=(-100, 0, -40), el=(-30, 0, 0), hip=(-70, 0, 0), kn=(95, 0, 0), chest=(4, 0, 0), head=(10, 0, 6))
    pose(P, 24, sh=(-35, 30, 0), el=(-35, 0, 0), hip=(-88, 0, -8), kn=(26, 0, 0), chest=(-6, 0, 0), head=(14, 0, -8))
    pose(P, 34, sh=(-22, 22, 0), el=(-48, 0, 0), hip=(-90, 0, -9), kn=(14, 0, 0), chest=(3, 0, 0), head=(4, 0, 6))
    splash("hit", (0, -0.05, 0.02), -4, 40, rnd, O["blob"], life=30)
    splash("sit", (0, -0.1, 0.02), 20, 16, rnd, O["blob"], speed=1.7, up=(1.0, 2.6), life=22)
    embers(46, rnd, end)

    # 2 float: level with the surface -- his hips rest on it, his legs lie along it; nothing goes under
    a, b = S["float"]
    shot(cam, a, b, (2.9, -1.5, 0.1), (0, -0.32, 0.36), (2.65, -1.2, 0.1), (0, -0.32, 0.36), lens=34)
    for j, f in enumerate(range(a, b, 14)):                      # the thick lava gives a little under him
        pose(P, f, chest=(3 + (2 if j % 2 else -2), 0, 0), head=(4, 0, 30 if j % 2 else 14))
    pose(P, a, sh=(-22, 22, 0), el=(-48, 0, 0))

    # 3 burn: the heat lights him from the lava upward
    a, b = S["burn"]
    shot(cam, a, b, (-0.95, -2.7, 0.75), (0, -0.25, 0.5), (-0.8, -2.4, 0.72), (0, -0.2, 0.52), lens=32)
    pose(P, a, sh=(-22, 22, 0), el=(-48, 0, 0), chest=(3, 0, 0), head=(4, 0, 0))
    pose(P, a + 10, sh=(-70, 40, 0), el=(-70, 0, 0), chest=(8, 0, 0), head=(24, 0, 0))       # he looks down at himself
    pose(P, a + 30, sh=(-85, 0, -35), el=(-55, 0, 0), chest=(-4, 0, 0), head=(-8, 0, 12))
    pose(P, b - 4, sh=(-60, 35, 0), el=(-60, 0, 0), chest=(0, 0, 0), head=(6, 0, -8))
    for c in O["char"]:
        kval(c, a + 2, 0.0), kval(c, a + 34, 0.55), kval(c, S["strip"][0] + 10, 1.0)
    # flames in root space for the seated pose (legs along -y at z ~0.93, torso up from 0.95)
    legs = [(s * 0.1 + dx, y, 0.95, 0.07, 0.1, a + 2 + int(abs(y + 0.5) * 12)) for s in (-1, 1) for y in
            (-0.1, -0.26, -0.42, -0.58, -0.74, -0.88) for dx in (-0.03, 0.03)]
    seat = [(x, y, 0.97, 0.08, 0.12, a + 6) for x in (-0.16, 0.0, 0.16) for y in (-0.06, 0.1)]
    torso = [(x, y, zz, 0.085, 0.13, a + 12 + int((zz - 1.05) * 40)) for x, y in
             ((-0.22, -0.04), (0.22, -0.04), (-0.14, 0.12), (0.14, 0.12), (0.0, 0.13)) for zz in (1.08, 1.26, 1.44)]
    arms = [(s * 0.29, yy, zz, 0.06, 0.1, a + 24) for s in (-1, 1) for yy, zz in ((-0.02, 1.5), (-0.18, 1.32))]
    head = [(0.0, 0.0, 1.83, 0.075, 0.13, a + 32), (0.06, 0.05, 1.78, 0.06, 0.1, a + 36),
            (-0.06, -0.02, 1.76, 0.06, 0.1, a + 38)]
    back = [(0.0, 0.16, 1.12, 0.17, 0.3, a + 16), (-0.22, 0.13, 1.0, 0.14, 0.24, a + 12),
            (0.22, 0.13, 1.0, 0.14, 0.24, a + 14), (0.0, -0.5, 0.93, 0.13, 0.17, a + 8), (0.0, 0.12, 1.5, 0.13, 0.24, a + 28)]
    f_out = S["end"][1] + 2
    O["flames"] = flames(root, back + legs + seat + torso + arms + head, f_out, rnd)
    fire = O["fire"]
    fire.parent = root
    fire.location = (0, -0.5, 1.5)
    for f in range(a, f_out, 3):                                 # the firelight flickers on him and the lava
        k(fire.data, "energy", f, (0 if f < a + 2 else min(1.0, (f - a) / 30)) * rnd.uniform(30, 60), "LINEAR")

    # 4 strip: part by part the skin is gone and the steel shows
    a, b = S["strip"]
    shot(cam, a, b, (0.75, -2.1, 0.62), (0, -0.2, 0.5), (0.55, -1.75, 0.66), (0, -0.12, 0.6), lens=34)
    pose(P, a, sh=(-60, 35, 0), el=(-60, 0, 0), chest=(0, 0, 0), head=(6, 0, -8))
    order = [("legs", a + 8), ("hips", a + 18), ("arms", a + 30), ("torso", a + 42), ("head", a + 58)]
    for region, f in order:
        for o in skin_objects(region):
            gone(o, f)
    pose(P, a + 40, sh=(-38, 26, 0), el=(-75, 0, 0), chest=(4, 0, 0), head=(26, 0, 0))       # he watches his chest go
    pose(P, a + 66, sh=(-30, 22, 0), el=(-80, 0, 0), chest=(0, 0, 0), head=(4, 0, 14))
    kval(O["heat"], a, 0.0), kval(O["heat"], a + 20, 0.12), kval(O["heat"], b, 0.5)

    # 5 steel: the skeleton glows hotter and holds
    a, b = S["steel"]
    shot(cam, a, b, (-1.25, -2.15, 0.5), (0, -0.15, 0.48), (-1.05, -1.85, 0.52), (0, -0.12, 0.5), lens=32)
    pose(P, a, sh=(-30, 22, 0), el=(-80, 0, 0), chest=(0, 0, 0), head=(4, 0, 14))
    pose(P, a + 30, sh=(-55, 28, 0), el=(-95, 0, 0), head=(18, 0, -10))                      # he looks at his hands
    pose(P, b - 6, sh=(-34, 22, 0), el=(-70, 0, 0), head=(2, 0, 10))
    kval(O["heat"], b, 0.85)

    # 6 time's up: wide -- a red-hot skeleton sitting on the lava
    a, b = S["timesup"]
    shot(cam, a, b, (0.42, -2.75, 0.9), (0, -0.15, 0.45), (0.36, -2.45, 0.84), (0, -0.15, 0.47), lens=28)
    pose(P, a, sh=(-34, 22, 0), el=(-70, 0, 0), chest=(0, 0, 0), head=(2, 0, 10))
    pose(P, b - 4, sh=(-24, 20, 0), el=(-50, 0, 0), chest=(2, 0, 0), head=(0, 0, 0))
    kval(O["heat"], b, 1.0)

    # 7 "...I'm fine.": the skull turns to the lens
    a, b = S["fine"]
    shot(cam, a, b, (0.42, -1.45, 0.86), (0.0, -0.02, 0.9), (0.38, -1.32, 0.87), (0.0, -0.02, 0.9), lens=46)
    pose(P, a, head=(0, 0, -30), chest=(2, 0, -6))
    pose(P, a + 10, head=(2, 0, 34), chest=(2, 0, 6))
    for j, f in enumerate(range(a + 12, b, 4)):                  # a small nod on each word
        pose(P, f, head=(2 + (5 if j % 2 else 0), 0, 34))

    # 8 end: pull back; the last frame matches the first (the loop restarts on the drop)
    a, b = S["end"]
    shot(cam, a, b, (0.5, -2.9, 0.9), (0, -0.1, 0.5), (0.75, -4.1, 1.3), (0, -0.05, 0.5), lens=28)
    pose(P, a, head=(0, 0, 10), chest=(0, 0, 0), sh=(-24, 20, 0), el=(-50, 0, 0))
    pose(P, a + 16, sh_1=(-150, -20, 0), el_1=(-30, 0, 0), head=(-6, 0, 10))                 # a small wave
    for j, f in enumerate(range(a + 20, b, 5)):
        pose(P, f, el_1=(-30 - (25 if j % 2 else 0), 0, 0))


# ── dust and smoke ────────────────────────────────────────────────────────────
def puff_mat(name, color, glow=0.0):
    """A torn cloudlet (dust, smoke): its keyed `fade` value takes it from dense (1) to gone (0)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value, nz.inputs["Detail"].default_value = 2.2, 4.0
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    torn = nt.nodes.new("ShaderNodeMapRange")
    torn.inputs["From Min"].default_value, torn.inputs["From Max"].default_value = 0.38, 0.62
    nt.links.new(nz.outputs["Fac"], torn.inputs["Value"])
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.3
    inv = nt.nodes.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    nt.links.new(lw.outputs["Facing"], inv.inputs[1])
    fade = nt.nodes.new("ShaderNodeValue")
    fade.name = "fade"
    m1 = nt.nodes.new("ShaderNodeMath")
    m1.operation = "MULTIPLY"
    nt.links.new(torn.outputs["Result"], m1.inputs[0])
    nt.links.new(inv.outputs[0], m1.inputs[1])
    m2 = nt.nodes.new("ShaderNodeMath")
    m2.operation = "MULTIPLY"
    nt.links.new(m1.outputs[0], m2.inputs[0])
    nt.links.new(fade.outputs[0], m2.inputs[1])
    body = nt.nodes.new("ShaderNodeBsdfDiffuse")
    body.inputs["Color"].default_value = (*color, 1)
    sh = body.outputs[0]
    if glow:                                                     # a little self-light so it reads against a dark ground
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value, em.inputs["Strength"].default_value = (*color, 1), glow
        add = nt.nodes.new("ShaderNodeAddShader")
        nt.links.new(body.outputs[0], add.inputs[0])
        nt.links.new(em.outputs[0], add.inputs[1])
        sh = add.outputs[0]
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(m2.outputs[0], mx.inputs[0])
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(sh, mx.inputs[2])
    nt.links.new(mx.outputs[0], nt.nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
    return m, fade.outputs[0]


def puffs(name, at, f0, n, rnd, color, spread=0.9, rise=0.25, life=44, size=0.32, dense=0.75, glow=0.0, ring=True):
    """n cloudlets billowing out from `at` (a ring along the ground, or straight up), swelling and thinning."""
    m, fade = puff_mat(name, color, glow)
    for f, v in ((max(0, f0 - 1), 0.0), (f0 + 2, dense), (f0 + life, 0.0)):
        kval(fade, f, v)
    linear(m.node_tree)
    for j in range(n):
        o = bp.lumpy(f"{name}{j}", 1.0, tuple(at), m, seed=500 + j + f0, amp=0.25)
        o.visible_shadow = False
        a = 2 * math.pi * (j + rnd.uniform(-0.3, 0.3)) / n
        d = Vector((math.cos(a), math.sin(a), 0)) * spread * rnd.uniform(0.6, 1.0) if ring else \
            Vector((rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), 0)) * spread
        up = rise * rnd.uniform(0.5, 1.2)
        sz = size * rnd.uniform(0.7, 1.2)
        for u, f in ((0.0, f0), (0.62, f0 + life // 3), (1.0, f0 + life)):
            k(o, "location", f, tuple(Vector(at) + d * u + Vector((0, 0, up * u))), "LINEAR")
            k(o, "scale", f, (sz * (0.25 + 0.75 * u),) * 3, "LINEAR")
        shown(o, max(0, f0), f0 + life)


# ── venus ─────────────────────────────────────────────────────────────────────
HAZE = (0.78, 0.43, 0.13)


def venus_ground():
    """Flat, cracked basalt plates dusted orange, fading into the haze toward the horizon."""
    m, b, nt = bk._principled("venus_ground")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.feature = "DISTANCE_TO_EDGE"
    vor.inputs["Scale"].default_value = 0.85
    nt.links.new(tc.outputs["Object"], vor.inputs["Vector"])
    crack = nt.nodes.new("ShaderNodeMapRange")
    crack.inputs["From Min"].default_value, crack.inputs["From Max"].default_value = 0.0, 0.06
    nt.links.new(vor.outputs["Distance"], crack.inputs["Value"])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value, nz.inputs["Detail"].default_value = 3.0, 8.0
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    col = nt.nodes.new("ShaderNodeMix")
    col.data_type = "RGBA"
    col.inputs["A"].default_value, col.inputs["B"].default_value = (0.1, 0.06, 0.035, 1), (0.34, 0.2, 0.09, 1)
    nt.links.new(nz.outputs["Fac"], col.inputs["Factor"])
    dark = nt.nodes.new("ShaderNodeMix")                         # the cracks between plates stay dark
    dark.data_type = "RGBA"
    dark.inputs["A"].default_value = (0.02, 0.012, 0.008, 1)
    nt.links.new(col.outputs["Result"], dark.inputs["B"])
    nt.links.new(crack.outputs["Result"], dark.inputs["Factor"])
    dist = nt.nodes.new("ShaderNodeVectorMath")
    dist.operation = "LENGTH"
    nt.links.new(tc.outputs["Object"], dist.inputs[0])
    far = nt.nodes.new("ShaderNodeMapRange")                     # 0 near him, 1 at the horizon
    far.inputs["From Min"].default_value, far.inputs["From Max"].default_value = 6.0, 34.0
    nt.links.new(dist.outputs["Value"], far.inputs["Value"])
    near = nt.nodes.new("ShaderNodeMix")
    near.data_type = "RGBA"
    nt.links.new(dark.outputs["Result"], near.inputs["A"])
    near.inputs["B"].default_value = (0, 0, 0, 1)
    nt.links.new(far.outputs["Result"], near.inputs["Factor"])
    nt.links.new(near.outputs["Result"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.9
    b.inputs["Emission Color"].default_value = (*HAZE, 1)
    nt.links.new(far.outputs["Result"], b.inputs["Emission Strength"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value, bump.inputs["Distance"].default_value = 0.9, 0.05
    hsum = nt.nodes.new("ShaderNodeMath")
    hsum.operation = "ADD"
    nt.links.new(crack.outputs["Result"], hsum.inputs[0])
    nt.links.new(nz.outputs["Fac"], hsum.inputs[1])
    nt.links.new(hsum.outputs[0], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


CRUSH = {  # skin part -> how much of it is left once the air is squeezed out of the foam (x, y, z)
    "upper": (0.62, 0.62, 1.0), "fore": (0.64, 0.64, 1.0), "thigh": (0.6, 0.6, 1.0), "shin": (0.64, 0.64, 1.0),
    "kneecap": (0.7, 0.6, 0.7), "hand": (0.8, 0.7, 0.9), "shcap": (0.75, 0.75, 0.7),
}


def squeeze_rig(P):
    """Pressure squeezes the air out of his foam: limbs thin, the chest plate and hips narrow (steel keeps its length)."""
    sq = bp.pivot("squeeze", (0, 0, 0.32), P["chest"])           # everything on the chest plate squeezes together
    for n in ["torso", "sternum", "chest_tgt", "chest_label"] + [f"ribF{j}" for j in range(4)] + \
             [f"ribS{j}{s_}" for j in range(4) for s_ in (-1, 1)]:
        o = bpy.data.objects[n]
        o.parent = sq
        o.location = Vector(o.location) - Vector((0, 0, 0.32))
    sq2 = bp.pivot("squeeze_hips", (0, 0, 0.01), P["pelvis"])
    for n in ("hips", "belt"):
        o = bpy.data.objects[n]
        o.parent = sq2
        o.location = Vector(o.location) - Vector((0, 0, 0.01))
    O["squeeze"] = [(sq, (0.84, 0.66, 0.95)), (sq2, (0.86, 0.72, 0.9))]
    for part, sc_ in CRUSH.items():
        for s_ in (-1, 1):
            O["squeeze"].append((bpy.data.objects[f"{part}{s_}"], sc_))


def squeeze(c0, c1):
    """The crush itself: a first bite, a creak back, then all the way."""
    for o, target in O["squeeze"]:
        k(o, "scale", 0, (1, 1, 1), "LINEAR"), k(o, "scale", c0, (1, 1, 1), "LINEAR")
        k(o, "scale", c0 + 8, tuple(1 - (1 - v) * 0.45 for v in target), "LINEAR")
        k(o, "scale", c0 + 12, tuple(1 - (1 - v) * 0.38 for v in target), "LINEAR")
        k(o, "scale", c1, target, "LINEAR")


def scene_venus(samples):
    rnd = random.Random(33)
    sc = bk.new_scene(fps=FPS, res=RES, samples=samples, frames=49)
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.4
    sc.cycles.max_bounces, sc.cycles.diffuse_bounces, sc.cycles.glossy_bounces = 3, 1, 2
    sc.cycles.transparent_max_bounces = 8
    sc.cycles.adaptive_min_samples = 4
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    bp.world(sc, HAZE, 0.75)                                     # the whole sky is one glowing orange overcast
    ground = bp.box("ground", (160, 160, 0.2), (0, 0, -0.1), venus_ground())
    slab = bp.add_bump(bp.mat("slab", (0.12, 0.075, 0.045), rough=0.9), 5.0, 0.8, distance=0.04)
    for j in range(22):                                          # loose plates and stones, none in a camera's way
        a, d = rnd.uniform(0.2, 2.95), rnd.uniform(2.2, 13.0)
        o = bp.lumpy(f"stone{j}", rnd.uniform(0.2, 0.9), (d * math.cos(a), 0.6 + d * math.sin(a), 0.0), slab,
                     seed=90 + j, amp=0.45)
        o.scale = (1.0, 1.0, rnd.uniform(0.12, 0.3))
    for j in range(6):                                           # a few small ones in the foreground corners
        x = rnd.choice((-1, 1)) * rnd.uniform(1.6, 3.2)
        o = bp.lumpy(f"pebble{j}", rnd.uniform(0.08, 0.2), (x, rnd.uniform(-3.0, -0.6), 0.0), slab, seed=140 + j, amp=0.45)
        o.scale = (1.0, 1.0, 0.3)
    bp.light("sky", "AREA", (0, -1.0, 9.0), 2600, size=14.0, color=(1.0, 0.72, 0.4), aim=(0, 0, 0))
    bp.light("key", "AREA", (-2.6, -4.2, 2.6), 320, size=3.5, color=(1.0, 0.8, 0.55), aim=(0, 0, 1.1))
    bp.light("rim", "AREA", (2.4, 3.6, 3.4), 380, size=2.5, color=(1.0, 0.6, 0.3), aim=(0, 0, 1.2))
    P = bp.build_dummy_v2(at=(0, 0, 0), yaw=math.radians(-14), label="TEST 07")
    charring(color=(0.03, 0.019, 0.012), embers_on=False)
    squeeze_rig(P)
    # the test prop: a bar of lead on a slab beside him
    lead = bp.mat("lead", (0.62, 0.65, 0.7), rough=0.35, metallic=1.0)
    bp.box("plinth", (0.8, 0.66, 0.09), (0.95, -0.55, 0.025), slab, bevel=0.035, rot=(0, 0, math.radians(12)))
    bar = bp.box("lead_bar", (0.11, 0.11, 0.36), (0.95, -0.55, 0.25), lead, bevel=0.016)    # an ingot stood on end
    bar.rotation_euler = (0, 0, math.radians(25))
    O.update(P=P, rnd=rnd, lead=bar, lead_mat=lead)
    cam = bp.cam_free(sc, 28, (2.2, -6.0, 1.0), (0, 0, 2.0))
    cam.data.dof.use_dof = False
    return sc


def timeline_venus(sc, T):
    fr = [int(round(t * FPS)) for t in T["starts"]] + [T["frames"]]
    S = dict(zip(T["shots"], zip(fr[:-1], fr[1:])))
    end = T["frames"] + 2
    sc.render.motion_blur_position = "START"
    cam, P, rnd = bpy.data.objects["cam"], O["P"], O["rnd"]
    root = P["root"]
    z = lambda f, v, i="LINEAR": k(root, "location", f, Vector((0, 0, v)), i)
    dust = (0.5, 0.3, 0.14)

    # 1 fall + 2 thick: he drifts down through air as dense as a thin liquid, limbs paddling, and touches down softly
    a, b = S["fall"]
    a2, b2 = S["thick"]
    land = b2 - 26
    z(0, 2.7), z(land, 0.0), z(land + 6, -0.07, "BEZIER"), z(land + 16, 0.0, "BEZIER")
    shot(cam, a, b, (1.5, -4.6, 0.4), (0.15, 0, 2.95), (1.4, -4.3, 0.45), (0.1, 0, 2.3), lens=22)
    shot(cam, a2, b2, (-2.6, -3.3, 0.8), (0, 0, 1.9), (-2.4, -3.0, 0.95), (0, 0, 1.0), lens=30)
    for j, f in enumerate(range(0, land, 9)):                    # slow swimming strokes all the way down
        o = j % 2
        pose(P, f, sh_1=(-70 if o else -130, -40 if o else -30, 0), el_1=(-50 if o else -15, 0, 0),
             sh1=(-130 if o else -70, 30 if o else 40, 0), el1=(-15 if o else -50, 0, 0),
             hip_1=(-28 if o else 12, 0, 0), kn_1=(40 if o else 12, 0, 0), hip1=(12 if o else -28, 0, 0),
             kn1=(12 if o else 40, 0, 0), chest=(8, 0, 6 if o else -6), head=(16, 0, -8 if o else 8))
    pose(P, land, sh=(-60, 45, 0), el=(-30, 0, 0), hip=(-8, 0, 0), kn=(12, 0, 0), chest=(4, 0, 0), head=(14, 0, 0))
    pose(P, land + 6, sh=(-40, 50, 0), el=(-40, 0, 0), hip=(-34, 0, 0), kn=(58, 0, 0), chest=(12, 0, 0), head=(6, 0, 0))
    pose(P, land + 18, sh=(-12, 14, 0), el=(-14, 0, 0), hip=(-4, 0, 0), kn=(6, 0, 0), chest=(0, 0, 0), head=(-6, 0, 10))
    puffs("land", (0, 0, 0.05), land, 12, rnd, dust, spread=1.3, rise=0.35, life=56, size=0.36, dense=0.7)

    # 3 press: 92 atmospheres -- the air is squeezed out of his foam and he thins on the spot
    a, b = S["press"]
    shot(cam, a, b, (0.7, -3.9, 1.25), (0, 0, 1.02), (0.55, -3.4, 1.2), (0, 0, 1.04), lens=34)
    pose(P, a, sh=(-12, 14, 0), el=(-14, 0, 0), chest=(0, 0, 0), head=(-6, 0, 10))
    c0, c1 = a + 12, a + 40
    squeeze(c0, c1)
    pose(P, c0 + 4, sh=(-70, 30, 0), el=(-80, 0, 0), chest=(-6, 0, 0), head=(-10, 0, 0))      # arms jerk up as it bites
    pose(P, c1 + 10, sh=(-62, 20, 0), el=(-95, 0, 0), chest=(4, 0, 0), head=(22, 0, 0))       # he looks at his thin arms
    pose(P, b - 8, sh=(-30, 18, 0), el=(-40, 0, 0), chest=(2, 0, 0), head=(8, 0, -10))

    # 4 heat: the lead bar beside him slumps into a puddle; his paint starts to brown
    a, b = S["heat"]
    # the bar is the picture here: a high insert that keeps it above the meters and the caption (it was under them)
    shot(cam, a, b, (1.75, -1.75, 0.95), (0.82, -0.5, -0.06), (1.69, -1.67, 0.92), (0.82, -0.5, -0.06), lens=32)
    pose(P, a, sh=(-30, 18, 0), el=(-40, 0, 0), chest=(2, 0, 0), head=(8, 0, -10))
    pose(P, a + 24, sh=(-20, 14, 0), el=(-30, 0, 0), chest=(8, 0, 10), head=(26, 0, 34))      # he looks down at the bar
    bar = O["lead"]
    base = bar.location.z - 0.18
    for f, sxy, sz in ((0, 1, 1), (a + 8, 1, 1), (a + 30, 1.5, 0.62), (a + 58, 2.6, 0.2), (b, 3.3, 0.09)):
        k(bar, "scale", f, (sxy, sxy, sz), "LINEAR")                                          # it slumps into a puddle
        k(bar, "location", f, (bar.location.x, bar.location.y, base + 0.18 * sz), "LINEAR")
    rough = O["lead_mat"].node_tree.nodes["Principled BSDF"].inputs["Roughness"]
    kval(rough, a + 8, 0.35), kval(rough, a + 40, 0.07)                                       # molten: mirror bright
    for c in O["char"]:
        kval(c, a, 0.0), kval(c, b, 0.3), kval(c, S["bake"][0] + 60, 0.9), kval(c, S["bake"][1], 1.0)

    # 5 bake: no flames -- he darkens, smokes and wilts
    a, b = S["bake"]
    shot(cam, a, b, (-1.0, -3.2, 1.2), (0, 0, 1.02), (-0.85, -2.8, 1.15), (0, 0, 0.98), lens=34)
    pose(P, a, sh=(-20, 14, 0), el=(-30, 0, 0), chest=(4, 0, 0), head=(10, 0, 0))
    pose(P, a + 40, sh=(-10, 10, 0), el=(-16, 0, 0), chest=(14, 0, 4), head=(24, 0, 6), hip=(-6, 0, 0), kn=(10, 0, 0))
    pose(P, b - 6, sh=(-4, 6, 0), el=(-8, 0, 0), chest=(24, 0, 6), head=(38, 0, 8), hip=(-10, 0, 0), kn=(16, 0, 0))
    for j, f in enumerate(range(a + 6, S["end"][1], 16)):                                     # thin smoke, straight up
        puffs(f"smoke{j}", (rnd.uniform(-0.15, 0.15), rnd.uniform(-0.1, 0.1), rnd.uniform(1.1, 1.7)), f, 3, rnd,
              (0.13, 0.11, 0.1), spread=0.25, rise=1.5, life=60, size=0.17, dense=0.32, ring=False)

    # 6 time's up: wide -- thin, black, wilted, and still standing
    a, b = S["timesup"]
    shot(cam, a, b, (0.7, -4.6, 1.15), (0, 0, 0.95), (0.6, -4.1, 1.1), (0, 0, 0.95), lens=30)
    pose(P, a, sh=(-4, 6, 0), el=(-8, 0, 0), chest=(24, 0, 6), head=(38, 0, 8), hip=(-10, 0, 0), kn=(16, 0, 0))
    pose(P, b - 4, chest=(26, 0, 4), head=(40, 0, 4))

    # 7 "...I miss the lava.": he lifts his head to the lens
    a, b = S["miss"]
    shot(cam, a, b, (0.5, -1.55, 1.52), (0.0, -0.22, 1.6), (0.45, -1.42, 1.53), (0.0, -0.2, 1.62), lens=44)
    pose(P, a, chest=(22, 0, 4), head=(34, 0, 4))
    pose(P, a + 10, chest=(14, 0, 8), head=(-2, 0, 30))
    for j, f in enumerate(range(a + 12, b, 4)):
        pose(P, f, head=(-2 + (5 if j % 2 else 0), 0, 30))

    # 8 end: pull back; a small wave
    a, b = S["end"]
    shot(cam, a, b, (0.7, -3.9, 1.2), (0, 0, 1.0), (1.0, -5.4, 1.5), (0, 0, 1.0), lens=30)
    pose(P, a, chest=(10, 0, 4), head=(4, 0, 14), sh=(-4, 6, 0), el=(-8, 0, 0))
    pose(P, a + 16, sh_1=(-150, -20, 0), el_1=(-30, 0, 0), head=(0, 0, 14))
    for j, f in enumerate(range(a + 20, b, 5)):
        pose(P, f, el_1=(-30 - (25 if j % 2 else 0), 0, 0))


# ── the ocean floor (Challenger Deep) ─────────────────────────────────────────
def drifting(n, rnd, f_end, mat_, size=0.006, box=(3.2, 3.0, 3.4), fall=-0.25, prefix="snow"):
    """Specks that never stop: marine snow sinking (fall < 0) or bubbles rising (fall > 0)."""
    for j in range(n):
        o = no_light(bp.ellipsoid(f"{prefix}{j}", (size,) * 3, (0, 0, 0), mat_, segs=8, rings=6))
        x, y = rnd.uniform(-box[0], box[0]), rnd.uniform(-box[1], box[1] * 0.6)
        z0 = rnd.uniform(0.1, box[2])
        sway = rnd.uniform(-0.2, 0.2)
        for f in range(-10, f_end + 30, 30):
            u = (f + 10) / FPS
            zz = z0 + fall * u
            k(o, "location", f, (x + sway * math.sin(u * 0.9 + j), y + sway * math.cos(u * 0.7 + j), zz), "LINEAR")


def bubbles(name, at, f0, n, rnd, mat_, spread=0.25, speed=1.3, every=2, size=(0.012, 0.03)):
    """A stream of bubbles from `at`, one every `every` frames, wobbling upward and out of the light."""
    for j in range(n):
        r = rnd.uniform(*size)
        o = no_light(bp.ellipsoid(f"{name}{j}", (r, r, r * 0.85), tuple(at), mat_, segs=12, rings=8))
        f = f0 + j * every
        x0, y0 = at[0] + rnd.uniform(-spread, spread), at[1] + rnd.uniform(-spread, spread)
        life = 34
        for q in range(0, life + 1, 6):
            u = q / FPS
            k(o, "location", f + q, (x0 + 0.05 * math.sin(q * 0.7 + j), y0 + 0.05 * math.cos(q * 0.6 + j),
                                     at[2] + rnd.uniform(-0.1, 0.1) * (q == 0) + speed * u), "LINEAR")
        shown(o, max(0, f), f + life)


def amphipod(name, mat_):
    """A pale, curled, shrimp-like scavenger: a segmented body, a tail tucked under, two feelers."""
    root = bp.pivot(name, (0, 0, -5))
    for j in range(6):                                           # body segments along +x, arching
        a = math.radians(-34 + 17 * j)
        bp.ellipsoid(f"{name}_s{j}", (0.017, 0.015 - 0.0012 * j, 0.019 - 0.0015 * j),
                     (0.055 * math.sin(a), 0, 0.028 * math.cos(a) - 0.028), mat_, root, segs=12, rings=8)
    for s_ in (-1, 1):
        o = bp.cylinder(f"{name}_f{s_}", 0.0016, 0.05, (-0.052, s_ * 0.008, 0.012), mat_, root,
                        rot=(0, math.radians(70), math.radians(s_ * 12)), segs=6)
    return root


LAMPS = (820, 560)      # our two lamps, in watts: a pool of light and nothing beyond it


def scene_ocean(samples):
    rnd = random.Random(52)
    sc = bk.new_scene(fps=FPS, res=RES, samples=samples, frames=49)
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.4
    sc.cycles.max_bounces, sc.cycles.diffuse_bounces, sc.cycles.glossy_bounces = 3, 1, 2
    sc.cycles.transparent_max_bounces = 8
    sc.cycles.adaptive_min_samples = 4
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    bp.world(sc, (0.0, 0.006, 0.016), 1.0)                       # no sunlight has ever reached here
    silt = bp.add_bump(bp.mat("silt", (0.3, 0.285, 0.25), rough=0.95), 1.6, 0.9, detail=5.0, distance=0.06)
    bp.box("seabed", (120, 120, 0.2), (0, 0, -0.1), silt)
    rock = bp.add_bump(bp.mat("nodule", (0.06, 0.055, 0.05), rough=0.8), 6.0, 0.8, distance=0.03)
    for j in range(16):                                          # manganese nodules scattered on the silt
        a, d = rnd.uniform(0.15, 3.0), rnd.uniform(1.8, 7.0)
        bp.lumpy(f"nodule{j}", rnd.uniform(0.06, 0.2), (d * math.cos(a), 0.4 + d * math.sin(a), 0.02), rock,
                 seed=200 + j, amp=0.4)
    # our own lights are the only light: two lamps from above the camera, cold and narrow
    for j, (x, e) in enumerate(((-2.2, LAMPS[0]), (2.6, LAMPS[1]))):
        l = bp.light(f"lamp{j}", "SPOT", (x, -5.2, 4.6), e, color=(0.72, 0.9, 1.0), aim=(0, 0.2, 0.7))
        l.data.spot_size, l.data.spot_blend, l.data.shadow_soft_size = math.radians(42), 0.75, 0.25
        O[f"lamp{j}"] = l
    bp.light("fill", "AREA", (0.5, -3.5, 0.8), 14, size=3.0, color=(0.3, 0.6, 1.0), aim=(0, 0, 1.0))
    P = bp.build_dummy_v2(at=(0, 0, 0), yaw=math.radians(-14), label="TEST 08")
    squeeze_rig(P)
    aim0 = bpy.data.objects["lamp0_aim"]                         # the main lamp follows him all the way down
    aim0.parent = P["root"]
    aim0.location = (0, 0, 1.0)
    # test props: a sealed steel drum (full of air) and a foam cup
    blue = bp.mat("drum_paint", (0.03, 0.16, 0.5), rough=0.4, metallic=0.6)
    drum = bp.cylinder("drum", 0.29, 0.88, (1.15, 0.15, 0.44), blue, bevel=0.02)
    hoops = [bp.cylinder(f"drum_hoop{j}", 0.3, 0.03, (0, 0, zz), blue, drum, bevel=0.008) for j, zz in
             enumerate((-0.2, 0.2))]
    crushed = bp.cylinder("drum_crushed", 0.29, 0.88, (1.15, 0.15, 0.4), blue, segs=64)
    crushed.data.polygons.foreach_set("use_smooth", [True] * len(crushed.data.polygons))
    bm = bmesh.new()
    bm.from_mesh(crushed.data)
    bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 0.5], cuts=12)
    r2 = random.Random(5)
    waves = [(r2.uniform(0, 6.28), r2.uniform(-0.3, 0.3), r2.uniform(0.5, 0.75)) for _ in range(3)]
    for v in bm.verts:                                           # caved in from every side, like a stamped-on can
        ang = math.atan2(v.co.y, v.co.x)
        zz = v.co.z / 0.44
        pinch = 1.0
        for a0, z0, depth in waves:
            pinch -= depth * math.exp(-((math.sin((ang - a0) / 2)) ** 2) / 0.12) * math.exp(-((zz - z0) ** 2) / 0.5) * 0.9
        pinch = max(0.16, pinch) * (0.62 + 0.3 * abs(zz) ** 3)
        v.co.x, v.co.y = v.co.x * pinch, v.co.y * pinch
    bm.to_mesh(crushed.data)
    bm.free()
    foam = bp.mat("foam_cup", (0.92, 0.92, 0.9), rough=0.7, sss=0.2)
    # the cup stands on a waist-high block: on the floor it sat behind the caption and nobody saw it shrink
    bp.box("cup_stand", (0.46, 0.4, 0.9), (-0.85, -0.6, 0.45), rock, bevel=0.05, rot=(0, 0, math.radians(-10)))
    cup = bp.pivot("cup", (-0.85, -0.6, 0.9))
    cup.scale = (1.5, 1.5, 1.5)
    bmc = bmesh.new()
    bmesh.ops.create_cone(bmc, cap_ends=True, segments=40, radius1=0.085, radius2=0.125, depth=0.3)
    mc = bpy.data.meshes.new("cup_mesh")
    bmc.to_mesh(mc)
    bmc.free()
    for p_ in mc.polygons:
        p_.use_smooth = abs(p_.normal.z) < 0.9
    mc.materials.append(foam)
    co = bpy.data.objects.new("cup_body", mc)
    co.location = (0, 0, 0.15)
    bp.link(co, cup)
    lip = bp.cylinder("cup_lip", 0.132, 0.022, (0, 0, 0.295), foam, cup, bevel=0.008)
    O.update(P=P, rnd=rnd, drum=drum, crushed=crushed, cup=cup)
    O["bubble"] = emit("bubble", (0.75, 0.95, 1.0), 2.2)
    O["snow"] = emit("snow", (0.8, 0.9, 1.0), 1.4)
    pale = bp.mat("amphipod", (0.95, 0.72, 0.62), rough=0.45, sss=0.3)
    pale.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (0.9, 0.55, 0.45, 1)
    pale.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 0.12
    O["pods"] = [amphipod(f"pod{j}", pale) for j in range(11)]
    cam = bp.cam_free(sc, 24, (1.5, -4.6, 0.5), (0, 0, 2.0))
    cam.data.dof.use_dof = False
    return sc


def timeline_ocean(sc, T):
    fr = [int(round(t * FPS)) for t in T["starts"]] + [T["frames"]]
    S = dict(zip(T["shots"], zip(fr[:-1], fr[1:])))
    end = T["frames"] + 2
    sc.render.motion_blur_position = "START"
    cam, P, rnd = bpy.data.objects["cam"], O["P"], O["rnd"]
    root = P["root"]
    z = lambda f, v, i="LINEAR": k(root, "location", f, Vector((0, 0, v)), i)
    drifting(90, rnd, end, O["snow"])
    silt = (0.62, 0.6, 0.55)

    # 1 sink: he comes down out of the black into our lights and lands in a cloud of silt
    a, b = S["sink"]
    land = b - 22
    z(0, 2.3), z(land, 0.0), z(land + 6, -0.06, "BEZIER"), z(land + 16, 0.0, "BEZIER")
    shot(cam, a, b, (1.6, -4.7, 0.42), (0.1, 0, 2.5), (1.45, -4.3, 0.5), (0.05, 0, 1.15), lens=22)
    for j, f in enumerate(range(0, land, 9)):
        o = j % 2
        pose(P, f, sh_1=(-70 if o else -130, -40 if o else -30, 0), el_1=(-50 if o else -15, 0, 0),
             sh1=(-130 if o else -70, 30 if o else 40, 0), el1=(-15 if o else -50, 0, 0),
             hip_1=(-28 if o else 12, 0, 0), kn_1=(40 if o else 12, 0, 0), hip1=(12 if o else -28, 0, 0),
             kn1=(12 if o else 40, 0, 0), chest=(8, 0, 6 if o else -6), head=(16, 0, -8 if o else 8))
    pose(P, land, sh=(-60, 45, 0), el=(-30, 0, 0), hip=(-8, 0, 0), kn=(12, 0, 0), chest=(4, 0, 0), head=(14, 0, 0))
    pose(P, land + 6, sh=(-40, 50, 0), el=(-40, 0, 0), hip=(-34, 0, 0), kn=(58, 0, 0), chest=(12, 0, 0), head=(6, 0, 0))
    pose(P, land + 18, sh=(-12, 14, 0), el=(-14, 0, 0), hip=(-4, 0, 0), kn=(6, 0, 0), chest=(0, 0, 0), head=(-6, 0, 10))
    puffs("silt", (0, 0, 0.05), land, 12, rnd, silt, spread=1.4, rise=0.4, life=70, size=0.4, dense=0.6)
    for f0 in range(-6, land, 7):                                # a few bubbles trail behind him on the way down
        zz = 2.3 * (1 - max(0, f0) / land) + 1.5
        bubbles(f"trail{f0 + 6}", (rnd.uniform(-0.15, 0.15), 0.0, zz), f0, 2, rnd, O["bubble"], speed=0.9)

    # 2 press: the sealed drum beside him is full of air -- it implodes
    a, b = S["press"]
    shot(cam, a, b, (-1.2, -4.1, 1.0), (0.55, 0.05, 0.86), (-1.0, -3.7, 0.95), (0.55, 0.05, 0.86), lens=30)
    pose(P, a, sh=(-12, 14, 0), el=(-14, 0, 0), chest=(0, 0, 0), head=(-6, 0, 10))
    bang = a + 16
    drum, crushed = O["drum"], O["crushed"]
    k(drum, "scale", 0, (1, 1, 1), "LINEAR"), k(drum, "scale", bang - 3, (1, 1, 1), "LINEAR")
    k(drum, "scale", bang, (0.7, 0.62, 0.96), "LINEAR")
    gone(drum, bang)
    for o in drum.children:
        gone(o, bang)
    shown(crushed, bang)
    k(crushed, "scale", bang, (1.25, 1.2, 1.05), "LINEAR"), k(crushed, "scale", bang + 3, (1, 1, 1), "LINEAR")
    k(crushed, "rotation_euler", bang, (0, 0, 0), "LINEAR"), k(crushed, "rotation_euler", bang + 14, (0.1, -0.06, 0.2))
    bubbles("pop", (1.15, 0.15, 0.6), bang, 26, rnd, O["bubble"], spread=0.3, speed=1.8, every=1, size=(0.02, 0.05))
    puffs("popsilt", (1.15, 0.15, 0.05), bang, 8, rnd, silt, spread=0.8, rise=0.3, life=50, size=0.3, dense=0.5)
    pose(P, bang + 3, sh=(-80, 30, 0), el=(-70, 0, 0), chest=(-8, 0, -14), head=(-8, 0, -40))  # he flinches away
    pose(P, bang + 30, sh=(-20, 14, 0), el=(-24, 0, 0), chest=(2, 0, 10), head=(14, 0, 44))   # then looks at it
    pose(P, b - 6, sh=(-12, 14, 0), el=(-14, 0, 0), chest=(0, 0, 4), head=(4, 0, 20))

    # 3 foam: the air is squeezed out of him as bubbles, and the cup beside him shrinks to a thimble
    a, b = S["foam"]
    shot(cam, a, b, (-0.25, -3.7, 0.95), (-0.22, 0.0, 0.79), (-0.25, -3.5, 0.95), (-0.22, 0.0, 0.79), lens=24)
    pose(P, a, sh=(-12, 14, 0), el=(-14, 0, 0), chest=(0, 0, 0), head=(0, 0, 0))
    c0, c1 = a + 10, a + 40
    squeeze(c0, c1)
    cup = O["cup"]
    k(cup, "scale", 0, (1.5, 1.5, 1.5), "LINEAR"), k(cup, "scale", c0, (1.5, 1.5, 1.5), "LINEAR")
    k(cup, "scale", c0 + 10, (0.9, 0.9, 0.93), "LINEAR"), k(cup, "scale", c1 + 6, (0.42, 0.42, 0.45), "LINEAR")
    pose(P, c0 + 4, sh=(-70, 30, 0), el=(-80, 0, 0), chest=(-6, 0, 0), head=(-10, 0, 0))
    pose(P, c1 + 10, sh=(-62, 20, 0), el=(-95, 0, 0), chest=(4, 0, 0), head=(22, 0, 0))
    pose(P, b - 6, sh=(-30, 18, 0), el=(-40, 0, 0), chest=(4, 0, -8), head=(6, 0, -40))       # he looks at the cup
    for zz in (0.5, 1.0, 1.35):
        bubbles(f"air{int(zz * 100)}", (0, -0.05, zz), c0, 16, rnd, O["bubble"], spread=0.22, speed=1.5)
    bubbles("cupair", (-0.85, -0.6, 1.15), c0, 10, rnd, O["bubble"], spread=0.08, speed=1.2, size=(0.008, 0.02))

    # 4 solid: thin, but whole -- he knocks on his own chest
    a, b = S["solid"]
    shot(cam, a, b, (0.7, -3.6, 1.25), (0, 0, 1.04), (0.6, -3.2, 1.2), (0, 0, 1.06), lens=34)
    pose(P, a, sh=(-30, 18, 0), el=(-40, 0, 0), chest=(2, 0, 0), head=(6, 0, 0))
    pose(P, a + 24, sh_1=(-38, 0, 30), el_1=(-118, 0, 0), sh1=(-14, -14, 0), el1=(-20, 0, 0), head=(20, 0, 0))
    for j, f in enumerate((a + 30, a + 34, a + 38, a + 42)):     # knock, knock
        pose(P, f, el_1=(-118 + (0 if j % 2 == 0 else 14), 0, 0))
    pose(P, b - 6, sh=(-14, 14, 0), el=(-20, 0, 0), head=(0, 0, 8))

    # 5 cold: the lamps gutter, and pale shapes come in from the dark
    a, b = S["cold"]
    shot(cam, a, b, (-0.9, -4.3, 1.1), (0, 0, 0.98), (-0.75, -3.9, 1.05), (0, 0, 1.0), lens=28)
    pose(P, a, sh=(-14, 14, 0), el=(-20, 0, 0), chest=(0, 0, 0), head=(0, 0, 8))
    for lamp, base in ((O["lamp0"], LAMPS[0]), (O["lamp1"], LAMPS[1])):
        k(lamp.data, "energy", 0, base, "LINEAR"), k(lamp.data, "energy", a + 4, base, "LINEAR")
        for f in range(a + 6, a + 26, 3):
            k(lamp.data, "energy", f, base * rnd.choice((0.08, 0.7, 0.15, 0.9, 0.05)), "LINEAR")
        k(lamp.data, "energy", a + 28, base * 0.8, "LINEAR")
    pose(P, a + 30, head=(-6, 0, -38), chest=(0, 0, -10))        # he hears something: looks one way...
    pose(P, a + 52, head=(-4, 0, 40), chest=(0, 0, 10))          # ...then the other
    pose(P, b - 4, head=(0, 0, 0), chest=(0, 0, 0))
    pods = O["pods"]
    hero = pods[0]
    hero.scale = (1.7, 1.7, 1.7)
    t_end = S["end"][1] + 2
    for j, pod in enumerate(pods):
        f0 = a + 16 + j * 3
        ang = rnd.uniform(0, 6.28)
        start = Vector((6.5 * math.cos(ang), 2.0 + 5.5 * math.sin(ang), rnd.uniform(0.6, 2.4)))
        ring = rnd.uniform(0.6, 1.25)
        a1 = rnd.uniform(0, 6.28)
        stop = Vector((ring * math.cos(a1), ring * math.sin(a1) * 0.8 - 0.1, rnd.uniform(0.35, 1.3)))   # below his face
        if pod is hero:
            stop = Vector((0.0, -0.02, 1.95))                    # this one settles on top of his head
        arrive = f0 + (46 if pod is not hero else S["timesup"][0] + 18 - f0)
        k(pod, "location", 0, tuple(start), "LINEAR")
        prev = start
        for q in range(0, 11):
            u = q / 10
            p = start.lerp(stop, u * u * (3 - 2 * u)) + Vector((0, 0, 0.12 * math.sin(u * 14 + j))) * (1 - u)
            f = f0 + int((arrive - f0) * u)
            k(pod, "location", f, tuple(p), "LINEAR")
            d = p - prev
            if d.length > 1e-4:
                k(pod, "rotation_euler", f, (0, -math.asin(max(-1, min(1, d.z / d.length))) * 0.6,
                                             math.atan2(d.y, d.x)), "LINEAR")
            prev = p
        if pod is hero:
            k(pod, "rotation_euler", arrive + 4, (0, 0, math.radians(-100)), "LINEAR")
            for jj, f in enumerate(range(arrive + 8, t_end, 7)):  # it shuffles about up there
                k(pod, "rotation_euler", f, (0, 0, math.radians(-100 + (22 if jj % 2 else -18))), "LINEAR")
        else:
            for jj, f in enumerate(range(arrive + 6, t_end, 12)):  # the others hover around him
                w = Vector((0.07 * math.sin(jj * 1.7 + j), 0.07 * math.cos(jj * 1.3 + j), 0.06 * math.sin(jj + j)))
                k(pod, "location", f, tuple(stop + w), "LINEAR")

    # 6 time's up: wide -- a thin dummy in a pool of light, shrimp all round him
    a, b = S["timesup"]
    shot(cam, a, b, (0.7, -4.9, 1.25), (0.15, 0, 0.98), (0.6, -4.4, 1.2), (0.15, 0, 0.98), lens=28)
    pose(P, a, head=(0, 0, 0), chest=(0, 0, 0), sh=(-14, 14, 0), el=(-20, 0, 0))
    pose(P, a + 30, head=(-10, 0, 0))                            # something lands on him
    pose(P, b - 4, head=(-14, 0, 6))

    # 7 "...Something's on my head.": close on the head and its passenger
    a, b = S["head"]
    shot(cam, a, b, (0.45, -1.5, 1.86), (0.0, -0.02, 1.83), (0.4, -1.38, 1.86), (0.0, -0.02, 1.84), lens=44)
    pose(P, a, head=(-14, 0, 6), chest=(0, 0, 0))
    pose(P, a + 10, head=(-4, 0, 28))
    for j, f in enumerate(range(a + 12, b, 4)):
        pose(P, f, head=(-4 + (4 if j % 2 else 0), 0, 28))

    # 8 end: pull back; a small wave
    a, b = S["end"]
    shot(cam, a, b, (0.7, -3.9, 1.25), (0, 0, 1.02), (1.0, -5.4, 1.5), (0, 0, 1.0), lens=30)
    pose(P, a, chest=(0, 0, 4), head=(0, 0, 14), sh=(-14, 14, 0), el=(-20, 0, 0))
    pose(P, a + 16, sh_1=(-150, -20, 0), el_1=(-30, 0, 0), head=(0, 0, 14))
    for j, f in enumerate(range(a + 20, b, 5)):
        pose(P, f, el_1=(-30 - (25 if j % 2 else 0), 0, 0))
