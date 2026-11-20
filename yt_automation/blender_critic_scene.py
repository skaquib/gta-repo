"""
blender_critic_scene.py — Blender scene for "A Food Critic Tries What Animals Eat" (run_critic_short.py drives it).
Runs in the Blender env:

  /root/.venvs/blender/bin/python blender_critic_scene.py TIMING.json OUT_DIR [START END | still F1 F2 ...]

A candlelit fine-dining table: white linen, a porcelain plate with a gold rim, a polished silver cloche, cutlery,
a crystal wine glass of "blood", a candle and warm restaurant lights far behind (bokeh). Each course is a
continuous shot: the cloche lifts to reveal eucalyptus (koala), a pile of bamboo (panda), a mountain of krill
spilling over the table (blue whale) and a ball of dung with a mint garnish (dung beetle). For dessert the ball
rolls away in a straight line and the restaurant fades into the Milky Way. Stylized-premium, not photoreal:
clean shapes, soft light, shallow focus.
"""
import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import bmesh  # noqa: E402
import blender_kit as bk  # noqa: E402

FPS = 24
PLATE_TOP = 0.0045
HIDE_Z = -5.0


# ── geometry helpers ──────────────────────────────────────────────────────────
def _link(ob):
    bpy.context.scene.collection.objects.link(ob)
    return ob


def lathe(name, profile, mat, segs=96, location=(0, 0, 0), smooth=True):
    """Surface of revolution around Z from a (radius, z) polyline."""
    verts, faces = [], []
    n = len(profile)
    for k in range(segs):
        a = 2 * math.pi * k / segs
        verts += [(r * math.cos(a), r * math.sin(a), z) for r, z in profile]
    for k in range(segs):
        k2 = (k + 1) % segs
        for j in range(n - 1):
            faces.append((k * n + j, k2 * n + j, k2 * n + j + 1, k * n + j + 1))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    for p in me.polygons:
        p.use_smooth = smooth
    ob = _link(bpy.data.objects.new(name, me))
    ob.location = location
    me.materials.append(mat)
    return ob


def leaf_mesh(name, length, width, mat, curl=0.25, cup=0.15, asym=0.0):
    """A lance-shaped leaf along +X from the origin, cupped and gently curled."""
    nu, nv = 28, 9
    verts, faces = [], []
    for i in range(nu):
        u = i / (nu - 1)
        w = width * (math.sin(math.pi * min(1.0, u * 1.05)) ** 0.85) * (1 - 0.35 * u)
        for j in range(nv):
            v = -1 + 2 * j / (nv - 1)
            x = u * length
            y = v * w * (1 + asym * v)
            z = curl * length * 0.25 * math.sin(math.pi * u) * u + cup * w * v * v
            verts.append((x, y, z))
    for i in range(nu - 1):
        for j in range(nv - 1):
            a = i * nv + j
            faces.append((a, a + nv, a + nv + 1, a + 1))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    me.materials.append(mat)
    mod = ob.modifiers.new("thick", "SOLIDIFY")
    mod.thickness = 0.0007
    return ob


def cylinder(name, r, length, mat, segs=32, axis="X"):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r, depth=length)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    if axis == "X":
        ob.rotation_euler = (0, math.pi / 2, 0)
    elif axis == "Y":
        ob.rotation_euler = (math.pi / 2, 0, 0)
    me.materials.append(mat)
    return ob


def sphere(name, r, mat, segs=48, rings=24):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=r)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    me.materials.append(mat)
    return ob


def box(name, sx, sy, sz, mat, bevel=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= sx
        v.co.y *= sy
        v.co.z *= sz
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    me.materials.append(mat)
    if bevel:
        m = ob.modifiers.new("bev", "BEVEL")
        m.width, m.segments = bevel, 3
        for p in me.polygons:
            p.use_smooth = True
    return ob


def keyloc(ob, frame, loc, interp="CONSTANT"):
    ob.location = loc
    ob.keyframe_insert("location", frame=frame)
    bk._set_interp(ob.animation_data.action, frame, interp)


def keyrot(ob, frame, rot, interp="CONSTANT"):
    ob.rotation_euler = rot
    ob.keyframe_insert("rotation_euler", frame=frame)
    bk._set_interp(ob.animation_data.action, frame, interp)


def keyval(sock, frame, val, owner=None, interp="LINEAR"):
    sock.default_value = val
    sock.keyframe_insert("default_value", frame=frame)


# ── materials ─────────────────────────────────────────────────────────────────
def mat_linen():
    m, b, nt = bk._principled("linen")
    N, L = nt.nodes, nt.links
    b.inputs["Base Color"].default_value = (0.035, 0.03, 0.034, 1)        # charcoal linen: the plate pops
    b.inputs["Roughness"].default_value = 0.8
    b.inputs["Sheen Weight"].default_value = 0.6
    b.inputs["Sheen Tint"].default_value = (0.6, 0.55, 0.5, 1)
    wave = N.new("ShaderNodeTexWave")
    wave.inputs["Scale"].default_value = 900.0
    wave.inputs["Distortion"].default_value = 1.5
    wave2 = N.new("ShaderNodeTexWave")
    wave2.bands_direction = "Y"
    wave2.inputs["Scale"].default_value = 900.0
    add = N.new("ShaderNodeMath")
    L.new(wave.outputs["Fac"], add.inputs[0])
    L.new(wave2.outputs["Fac"], add.inputs[1])
    bump = N.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.12
    L.new(add.outputs[0], bump.inputs["Height"])
    L.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def mat_leaf(name, color, vein):
    """Leaf: waxy, a little translucent, with a lighter midrib along the leaf's local X axis."""
    m, b, nt = bk._principled(name)
    N, L = nt.nodes, nt.links
    b.inputs["Roughness"].default_value = 0.38
    b.inputs["Coat Weight"].default_value = 0.25
    b.inputs["Subsurface Weight"].default_value = 0.12
    b.inputs["Subsurface Radius"].default_value = (0.3, 0.5, 0.2)
    tc, sep = N.new("ShaderNodeTexCoord"), N.new("ShaderNodeSeparateXYZ")
    L.new(tc.outputs["Object"], sep.inputs[0])
    ab = N.new("ShaderNodeMath")
    ab.operation = "ABSOLUTE"
    L.new(sep.outputs["Y"], ab.inputs[0])
    mr = N.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.0005
    mr.inputs["From Max"].default_value = 0.0013
    L.new(ab.outputs[0], mr.inputs["Value"])
    nz = N.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 140.0
    mix0 = N.new("ShaderNodeMix")
    mix0.data_type = "RGBA"
    mix0.inputs["Factor"].default_value = 0.12
    mix0.inputs[6].default_value = (*color, 1)
    L.new(nz.outputs["Color"], mix0.inputs[7])
    mix = N.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    L.new(mr.outputs["Result"], mix.inputs["Factor"])
    mix.inputs[6].default_value = (*vein, 1)
    L.new(mix0.outputs[2], mix.inputs[7])
    L.new(mix.outputs[2], b.inputs["Base Color"])
    return m


def mat_glass(name, color=(1, 1, 1), rough=0.0, ior=1.45):
    m, b, _ = bk._principled(name)
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["Roughness"].default_value = rough
    b.inputs["IOR"].default_value = ior
    return m


def mat_emit(name, color, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type == "BSDF_PRINCIPLED":
            nt.nodes.remove(n)
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    return m, em


def mat_dung():
    m, b, nt = bk._principled("dung")
    N, L = nt.nodes, nt.links
    b.inputs["Roughness"].default_value = 0.92
    nz = N.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 35.0
    nz.inputs["Detail"].default_value = 10.0
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.06, 0.035, 0.015, 1)
    ramp.color_ramp.elements[1].color = (0.25, 0.16, 0.07, 1)
    L.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    L.new(ramp.outputs["Color"], b.inputs["Base Color"])
    fib = N.new("ShaderNodeTexWave")
    fib.wave_type = "RINGS"
    fib.inputs["Scale"].default_value = 70.0
    fib.inputs["Distortion"].default_value = 12.0
    add = N.new("ShaderNodeMath")
    L.new(nz.outputs["Fac"], add.inputs[0])
    L.new(fib.outputs["Fac"], add.inputs[1])
    bump = N.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.6
    L.new(add.outputs[0], bump.inputs["Height"])
    L.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def mat_wall_sky():
    """Restaurant back wall that can fade into a Milky Way night sky (input 'Fac' keyed 0 -> 1)."""
    m = bpy.data.materials.new("wall_sky")
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    for n in list(N):
        if n.type == "BSDF_PRINCIPLED":
            N.remove(n)
    wall = N.new("ShaderNodeBsdfDiffuse")
    wall.inputs["Color"].default_value = (0.05, 0.028, 0.017, 1)
    tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(tc.outputs["Object"], sep.inputs[0])

    def math_node(op, a=None, b=None, va=None, vb=None):
        n = N.new("ShaderNodeMath")
        n.operation = op
        if a is not None:
            L.new(a, n.inputs[0])
        elif va is not None:
            n.inputs[0].default_value = va
        if b is not None:
            L.new(b, n.inputs[1])
        elif vb is not None:
            n.inputs[1].default_value = vb
        return n.outputs[0]

    # the band: a diagonal glow, broken up by noise and dark dust lanes
    d = math_node("SUBTRACT", sep.outputs["Z"], math_node("MULTIPLY", sep.outputs["X"], vb=0.45))
    d = math_node("DIVIDE", math_node("ADD", d, vb=0.85), vb=0.2)
    band = math_node("EXPONENT", math_node("MULTIPLY", math_node("MULTIPLY", d, d), vb=-1.0))
    nz = N.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 2.2
    nz.inputs["Detail"].default_value = 12.0
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    lanes = N.new("ShaderNodeValToRGB")
    lanes.color_ramp.elements[0].position = 0.45
    lanes.color_ramp.elements[1].position = 0.72
    L.new(nz.outputs["Fac"], lanes.inputs["Fac"])
    glow = math_node("MULTIPLY", band, lanes.outputs["Color"])
    # stars: tiny bright points everywhere, denser in the band
    vor = N.new("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = 24.0
    L.new(tc.outputs["Object"], vor.inputs["Vector"])
    st = N.new("ShaderNodeMapRange")
    st.inputs["From Min"].default_value = 0.0
    st.inputs["From Max"].default_value = 0.11
    st.inputs["To Min"].default_value = 1.0
    st.inputs["To Max"].default_value = 0.0
    L.new(vor.outputs["Distance"], st.inputs["Value"])
    stars = math_node("POWER", st.outputs["Result"], vb=9.0)
    sepc = N.new("ShaderNodeSeparateColor")
    L.new(vor.outputs["Color"], sepc.inputs[0])
    bright = math_node("POWER", sepc.outputs[0], vb=3.0)                 # a few bright stars, many faint
    stars = math_node("MULTIPLY", math_node("MULTIPLY", stars, bright), math_node("ADD", band, vb=0.5))
    col = N.new("ShaderNodeCombineColor")
    sky_r = math_node("ADD", math_node("MULTIPLY", glow, vb=0.2), math_node("MULTIPLY", stars, vb=7.0))
    sky_g = math_node("ADD", math_node("MULTIPLY", glow, vb=0.21), math_node("MULTIPLY", stars, vb=7.0))
    sky_b = math_node("ADD", math_node("ADD", math_node("MULTIPLY", glow, vb=0.32), math_node("MULTIPLY", stars, vb=7.5)), vb=0.006)
    L.new(sky_r, col.inputs[0])
    L.new(sky_g, col.inputs[1])
    L.new(sky_b, col.inputs[2])
    em = N.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 1.6
    L.new(col.outputs[0], em.inputs["Color"])
    mix = N.new("ShaderNodeMixShader")
    mix.inputs["Fac"].default_value = 0.0
    L.new(wall.outputs[0], mix.inputs[1])
    L.new(em.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], N["Material Output"].inputs["Surface"])
    return m, mix.inputs["Fac"]


# ── the scene ─────────────────────────────────────────────────────────────────
def build(timing):
    starts, total = timing["starts"], timing["total"]
    segs = timing["segments"]
    n_frames = int(round((total + 0.6) * FPS)) + 1
    sc = bk.new_scene(fps=FPS, res=(720, 1280), samples=10, frames=n_frames)
    sc.cycles.transmission_bounces = 8
    sc.cycles.max_bounces = 8
    sc.cycles.glossy_bounces = 3
    F = lambda s: int(round(s * FPS))       # noqa: E731

    course_t = {}
    for k, s in enumerate(segs):
        course_t.setdefault(s["course"], [starts[k], None])
    order = list(course_t)
    for a, b in zip(order, order[1:]):
        course_t[a][1] = course_t[b][0]
    course_t[order[-1]][1] = total + 0.6

    # world + room
    w = bpy.data.worlds.new("world")
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.004, 0.003, 0.0025, 1)
    table = box("table", 1.8, 1.3, 0.04, mat_linen())
    _link(table).location = (0, 0.05, -0.02)
    wall_m, sky_fac = mat_wall_sky()
    wall = box("wall", 9.0, 0.05, 6.0, wall_m)
    _link(wall).location = (0, 2.6, 1.2)
    rnd = random.Random(11)
    bokeh = []
    for k in range(34):
        m, em = mat_emit(f"bokeh{k}", rnd.choice([(1.0, 0.62, 0.28), (1.0, 0.75, 0.42), (1.0, 0.52, 0.22)]),
                         rnd.uniform(18, 40))
        b = _link(sphere(f"bokeh{k}", rnd.uniform(0.012, 0.024), m, 16, 8))
        b.location = (rnd.uniform(-1.3, 1.3), rnd.uniform(1.1, 2.3), rnd.uniform(0.04, 0.75))
        bokeh.append((em, b))

    # tableware
    porcelain = bk.mat_basic("porcelain", (0.93, 0.92, 0.9), rough=0.12, coat=0.6, sss=0.05)
    gold = bk.mat_basic("gold", (1.0, 0.72, 0.32), rough=0.22, metallic=1.0)
    silver = bk.mat_basic("silver", (0.93, 0.93, 0.95), rough=0.11, metallic=1.0)
    plate = lathe("plate", [(0.0005, 0.0), (0.085, 0.0), (0.095, 0.0012), (0.10, PLATE_TOP - 0.003),
                            (0.12, 0.009), (0.142, 0.0135), (0.146, 0.0128), (0.1435, 0.0105), (0.12, 0.0068),
                            (0.10, PLATE_TOP), (0.0005, PLATE_TOP)], porcelain)
    rim_t = lathe("gold_ring", [(0.1395, 0.0118), (0.1405, 0.0124), (0.1415, 0.0128), (0.1405, 0.0131),
                                (0.1395, 0.0126)], gold)
    del plate, rim_t

    cl_prof = []
    R = 0.124
    for k in range(25):
        a = math.pi / 2 * k / 24
        cl_prof.append((R * math.cos(a), R * 0.82 * math.sin(a)))
    cl_prof = [(R + 0.006, 0.0), (R + 0.006, 0.004)] + cl_prof
    cloche = lathe("cloche", [(r, z) for r, z in cl_prof] + [(0.0005, R * 0.82)], silver)
    knob = _link(sphere("knob", 0.014, silver))
    knob.location = (0, 0, R * 0.82 + 0.016)
    knob.parent = cloche
    stem = _link(cylinder("knob_stem", 0.006, 0.012, silver, axis="Z"))
    stem.location = (0, 0, R * 0.82 + 0.004)
    stem.parent = cloche

    # cutlery
    fork = bpy.data.objects.new("fork", None)
    _link(fork)
    h = _link(box("fork_handle", 0.014, 0.12, 0.004, silver, bevel=0.002))
    h.location = (0, -0.07, 0.003)
    h.parent = fork
    for k in range(4):
        tine = _link(box(f"tine{k}", 0.0022, 0.045, 0.0025, silver, bevel=0.0008))
        tine.location = (-0.0075 + k * 0.005, 0.03, 0.004)
        tine.parent = fork
    neck = _link(box("fork_neck", 0.02, 0.02, 0.003, silver, bevel=0.001))
    neck.location = (0, 0.0, 0.0035)
    neck.parent = fork
    fork.location = (-0.205, 0.0, 0.0)
    knife = bpy.data.objects.new("knife", None)
    _link(knife)
    kb = _link(box("knife_blade", 0.018, 0.1, 0.0018, silver, bevel=0.0008))
    kb.location = (0, 0.04, 0.002)
    kb.parent = knife
    kh = _link(box("knife_handle", 0.016, 0.1, 0.006, silver, bevel=0.003))
    kh.location = (0, -0.07, 0.003)
    kh.parent = knife
    knife.location = (0.205, -0.01, 0.0)

    # wine glass with "blood"
    glass = mat_glass("crystal")
    gp = [(0.0005, 0.0), (0.034, 0.0), (0.035, 0.002), (0.006, 0.006), (0.0042, 0.02), (0.0042, 0.075),
          (0.012, 0.085), (0.032, 0.105), (0.041, 0.13), (0.039, 0.16), (0.034, 0.185), (0.0335, 0.1855),
          (0.0375, 0.16), (0.0395, 0.13), (0.031, 0.106), (0.011, 0.087), (0.0005, 0.083)]
    wine_glass = lathe("wine_glass", gp, glass)
    blood = mat_glass("blood", color=(0.55, 0.01, 0.02), ior=1.34)
    bb = blood.node_tree.nodes["Principled BSDF"]
    vol = blood.node_tree.nodes.new("ShaderNodeVolumeAbsorption")
    vol.inputs["Color"].default_value = (0.6, 0.02, 0.03, 1)
    vol.inputs["Density"].default_value = 60.0
    blood.node_tree.links.new(vol.outputs[0], blood.node_tree.nodes["Material Output"].inputs["Volume"])
    del bb
    lp = [(0.0005, 0.0875), (0.0105, 0.0885), (0.0305, 0.1075), (0.038, 0.13), (0.0005, 0.13)]
    liquid = lathe("blood", lp, blood)
    liquid.parent = wine_glass
    wine_glass.location = (0.2, 0.17, 0.0)

    # candle
    wax = bk.mat_basic("wax", (0.92, 0.86, 0.74), rough=0.4, sss=0.4)
    candle = _link(cylinder("candle", 0.022, 0.13, wax, axis="Z"))
    candle.location = (-0.25, 0.26, 0.065)
    holder = lathe("holder", [(0.0005, 0.0), (0.045, 0.0), (0.046, 0.004), (0.03, 0.006), (0.024, 0.012),
                              (0.0005, 0.012)], silver)
    holder.location = (-0.25, 0.26, 0.0)
    fm, fem = mat_emit("flame", (1.0, 0.55, 0.18), 60.0)
    flame = _link(sphere("flame", 0.006, fm, 24, 12))
    flame.scale = (1.0, 1.0, 2.4)
    flame.location = (-0.25, 0.26, 0.145)
    pl = bpy.data.lights.new("candle_light", "POINT")
    pl.energy, pl.color, pl.shadow_soft_size = 4.0, (1.0, 0.58, 0.28), 0.01
    plo = _link(bpy.data.objects.new("candle_light", pl))
    plo.location = (-0.25, 0.26, 0.15)

    def area(name, loc, aim, energy, size, color):
        l = bpy.data.lights.new(name, "AREA")
        l.energy, l.size, l.color = energy, size, color
        o = _link(bpy.data.objects.new(name, l))
        o.location = loc
        c = o.constraints.new("TRACK_TO")
        c.target = bk.empty(name + "_aim", aim)
        c.track_axis, c.up_axis = "TRACK_NEGATIVE_Z", "UP_Y"
        return o

    area("pendant", (0.05, -0.05, 0.75), (0, 0, 0), 9.0, 0.3, (1.0, 0.82, 0.62))      # a warm pool on the plate
    area("rim", (0.5, 0.9, 0.4), (0, 0, 0.05), 14.0, 0.5, (0.7, 0.8, 1.0))            # silver and glass edges
    area("fill", (-0.8, -0.9, 0.4), (0, 0, 0.05), 1.5, 1.2, (1.0, 0.9, 0.8))

    # ── the dishes (each on a root that is parked under the floor when not served) ──
    roots = {}

    def root(name):
        r = bpy.data.objects.new(name, None)
        _link(r)
        roots[name] = r
        return r

    # koala: eucalyptus leaves fanned out, with a twig
    r = root("koala")
    euc = mat_leaf("eucalyptus", (0.13, 0.22, 0.19), (0.42, 0.5, 0.36))
    twig = bk.mat_basic("twig", (0.25, 0.14, 0.08), rough=0.7)
    rr = random.Random(3)
    for k in range(9):
        lf = _link(leaf_mesh(f"euc{k}", rr.uniform(0.085, 0.115), rr.uniform(0.017, 0.022), euc, curl=0.5, cup=0.3,
                             asym=rr.uniform(-0.15, 0.15)))
        a = -1.9 + k * 0.42 + rr.uniform(-0.1, 0.1)
        lf.location = (0.012 * math.cos(a), 0.012 * math.sin(a), PLATE_TOP + 0.002 + k * 0.0012)
        lf.rotation_euler = (rr.uniform(-0.1, 0.1), rr.uniform(-0.12, 0.05), a)
        lf.parent = r
    tw = _link(cylinder("twig", 0.0028, 0.09, twig, axis="X"))
    tw.location = (-0.03, -0.02, PLATE_TOP + 0.016)
    tw.rotation_euler = (0, math.pi / 2, 0.5)
    tw.parent = r

    # panda: a heap of bamboo culms with node rings and a few leaves
    r = root("panda")
    bam = bk.mat_basic("bamboo", (0.24, 0.45, 0.1), rough=0.32, coat=0.5)
    node_m = bk.mat_basic("bamboo_node", (0.55, 0.62, 0.25), rough=0.4)
    bleaf = mat_leaf("bamboo_leaf", (0.12, 0.32, 0.06), (0.4, 0.55, 0.2))
    rr = random.Random(5)
    for k in range(7):
        rad = rr.uniform(0.011, 0.015)
        ln = rr.uniform(0.3, 0.42)
        cul = bpy.data.objects.new(f"culm{k}", None)
        _link(cul)
        c = _link(cylinder(f"culm_body{k}", rad, ln, bam))
        c.parent = cul
        for j in range(-2, 3):
            ring = _link(cylinder(f"node{k}_{j}", rad * 1.08, 0.006, node_m))
            ring.location = (j * 0.085 + rr.uniform(-0.01, 0.01), 0, 0)
            ring.parent = cul
        layer = k // 3
        cul.location = (rr.uniform(-0.03, 0.03), -0.05 + (k % 3) * 0.045 + rr.uniform(-0.01, 0.01),
                        PLATE_TOP + rad + layer * 0.022)
        cul.rotation_euler = (0, 0, rr.uniform(-0.55, 0.55) + (0.9 if layer == 1 else 0))
        cul.parent = r
    for k in range(4):
        lf = _link(leaf_mesh(f"bleaf{k}", 0.1, 0.012, bleaf, curl=0.8, cup=0.2))
        lf.location = (rr.uniform(-0.04, 0.05), rr.uniform(-0.04, 0.04), PLATE_TOP + 0.05)
        lf.rotation_euler = (rr.uniform(-0.3, 0.3), rr.uniform(-0.4, 0.1), rr.uniform(0, 6.28))
        lf.parent = r

    # blue whale: a mountain of krill spilling off the plate and over the table
    r = root("whale")
    kr = bk.mat_basic("krill", (0.95, 0.38, 0.24), rough=0.35, sss=0.25, coat=0.4)
    eye_m = bk.mat_basic("krill_eye", (0.01, 0.01, 0.01), rough=0.2)
    base = bk.egg("krill_src", 0.034, 0.005, kr, location=(0, 0, 0), pointy=0.35)
    base.location = (0, 0, HIDE_Z)
    eye = _link(sphere("krill_eye_src", 0.0016, eye_m, 12, 6))
    eye.location = (0.0148, 0.0034, 0.0018)
    eye.parent = base
    eye2 = _link(sphere("krill_eye_src2", 0.0016, eye_m, 12, 6))
    eye2.location = (0.0148, -0.0034, 0.0018)
    eye2.parent = base
    rr = random.Random(9)
    pts = []
    core = lathe("krill_core", [(0.0005, PLATE_TOP)] + [(0.165 * math.cos(math.pi / 2 * k / 16),
                 PLATE_TOP + 0.17 * math.sin(math.pi / 2 * k / 16)) for k in range(17)], kr)
    core.parent = r                 # a solid heart, so the pile never looks hollow
    for k in range(1400):         # a mountain taller than the cloche: krill over the dome, several layers deep
        a, rad = rr.uniform(0, 2 * math.pi), 0.19 * math.sqrt(rr.random())
        top = 0.2 * (1 - (rad / 0.19) ** 2) ** 0.75
        pts.append((rad * math.cos(a), rad * math.sin(a), PLATE_TOP + 0.004 + max(0.0, top - rr.uniform(0, 0.03))))
    for k in range(220):          # spilled across the table
        a, rad = rr.uniform(0, 2 * math.pi), rr.uniform(0.18, 0.4)
        pts.append((rad * math.cos(a), rad * math.sin(a) * 0.9, 0.005))
    for k, p in enumerate(pts):
        ob = bk.instance(base, f"krill{k}", p, scale=rr.uniform(0.75, 1.2),
                         rotation=(rr.uniform(-0.6, 0.6), rr.uniform(-0.6, 0.6), rr.uniform(0, 6.28)))
        ob.parent = r
        for e in (eye, eye2):
            ee = bpy.data.objects.new(f"{e.name}_{k}", e.data)
            _link(ee)
            ee.location = e.location
            ee.parent = ob
    root_whale = r

    # dessert: a ball of dung with a mint-leaf garnish (it later rolls away)
    r = root("dessert")
    ball = _link(sphere("dung_ball", 0.042, mat_dung(), 96, 48))
    tex = bpy.data.textures.new("dung_noise", type="CLOUDS")
    tex.noise_scale = 0.012
    disp = ball.modifiers.new("disp", "DISPLACE")
    disp.texture = tex
    disp.strength = 0.004
    ball.location = (0, 0, PLATE_TOP + 0.042)
    ball.parent = r
    mint = mat_leaf("mint", (0.06, 0.3, 0.05), (0.3, 0.55, 0.2))
    for k, ang in enumerate((0.3, 1.9, 3.8)):
        lf = _link(leaf_mesh(f"mint{k}", 0.028, 0.012, mint, curl=0.6, cup=0.5))
        lf.location = (0.004 * math.cos(ang), 0.004 * math.sin(ang), 0.041)
        lf.rotation_euler = (0.0, -0.5, ang)
        lf.parent = ball

    # ── animation, keyed to the voice ──────────────────────────────────────────
    cues = {"cloche": [], "clank": []}
    for name, ob in roots.items():
        keyloc(ob, 0, (0, 0, HIDE_Z))
    served = {"hook": "dessert", "koala": "koala", "panda": "panda", "bat": None, "whale": "whale",
              "dessert": "dessert", "cta": "dessert"}
    for c in order:
        f0 = 0 if c == order[0] else F(course_t[c][0])
        for name, ob in roots.items():
            keyloc(ob, f0, (0, 0, 0) if served[c] == name else (0, 0, HIDE_Z))

    closed = (0, 0, 0.0092)
    keyloc(cloche, 0, closed)
    keyrot(cloche, 0, (0, 0, 0))

    def lift(t):
        f = F(t)
        keyloc(cloche, f - 1, closed)
        keyrot(cloche, f - 1, (0, 0, 0))
        keyloc(cloche, f, closed, "BEZIER")
        keyrot(cloche, f, (0, 0, 0), "BEZIER")
        keyloc(cloche, f + 6, (0.02, 0.06, 0.16), "BEZIER")
        keyrot(cloche, f + 6, (-0.35, 0.12, 0), "BEZIER")
        keyloc(cloche, f + 14, (0.08, 0.2, 0.62), "CONSTANT")
        keyrot(cloche, f + 14, (-0.7, 0.2, 0), "CONSTANT")
        cues["cloche"].append(round(t, 3))

    for c in ("koala", "panda", "whale", "dessert"):
        t0 = course_t[c][0]
        keyloc(cloche, F(t0), closed)
        keyrot(cloche, F(t0), (0, 0, 0))
        lift(t0 + 0.35)
    bt = course_t["bat"][0]
    keyloc(cloche, F(bt), closed)
    keyrot(cloche, F(bt), (0, 0, 0))
    # hook tease: on "Dessert is a ball of poo" the cloche peeks open... and slams shut
    tz = starts[1] + 0.45
    keyloc(cloche, F(tz), closed, "BEZIER")
    keyloc(cloche, F(tz) + 5, (0, 0.035, 0.085), "BEZIER")
    keyrot(cloche, F(tz), (0, 0, 0), "BEZIER")
    keyrot(cloche, F(tz) + 5, (-0.5, 0, 0), "BEZIER")
    keyloc(cloche, F(tz) + 16, (0, 0.035, 0.085), "BEZIER")
    keyrot(cloche, F(tz) + 16, (-0.5, 0, 0), "BEZIER")
    keyloc(cloche, F(tz) + 19, closed, "CONSTANT")
    keyrot(cloche, F(tz) + 19, (0, 0, 0), "CONSTANT")
    cues["cloche"].append(round(tz, 3))
    cues["clank"].append(round(tz + 19 / FPS, 3))

    # dessert: the ball rolls away in a dead-straight line toward the back of the table
    d0 = course_t["dessert"][0]
    roll0, roll1 = d0 + 2.0, d0 + 5.4
    keyloc(ball, F(roll0), (0, 0, PLATE_TOP + 0.042), "BEZIER")
    keyrot(ball, F(roll0), (0, 0, 0), "BEZIER")
    steps = 12
    for k in range(1, steps + 1):
        u = k / steps
        e = u * u * (3 - 2 * u)
        y = 0.52 * e
        over = math.exp(-((y - 0.14) / 0.02) ** 2) * 0.012                 # up and over the plate rim
        z = (PLATE_TOP if y < 0.145 else 0.0) + 0.042 + over
        keyloc(ball, F(roll0 + u * (roll1 - roll0)), (0, y, z), "LINEAR")
        keyrot(ball, F(roll0 + u * (roll1 - roll0)), (-y / 0.042, 0, 0), "LINEAR")
    cues["roll"] = round(roll0, 3)
    # ...and the restaurant fades into the Milky Way
    s0, s1 = roll0 + 1.2, roll0 + 3.0
    keyval(sky_fac, 0, 0.0)
    keyval(sky_fac, F(s0), 0.0)
    keyval(sky_fac, F(s1), 1.0)
    for em, ob in bokeh:
        st = em.inputs["Strength"]
        v = st.default_value
        keyval(st, 0, v)
        keyval(st, F(s0), v)
        keyval(st, F(s1), 0.0)
        for f, sc_ in ((0, 1.0), (F(s0), 1.0), (F(s1), 0.0)):
            ob.scale = (sc_, sc_, sc_)
            ob.keyframe_insert("scale", frame=f)

    # cameras: one continuous move per course, hard cuts between courses
    cam, target = bk.camera(sc, lens=35)
    plate_c = (0, 0, 0.04)

    def key(fr, at, dist, elev, azim, lens=35, fstop=2.8):
        bk.shot(cam, target, fr, at, dist, elev, azim, lens, fstop, interp="BEZIER")

    h0, h1 = course_t["hook"]
    key(0, (0.02, 0.05, 0.05), 0.95, 30, -12, 35, 4.0)
    key(F(h1) - 1, (0.0, 0.01, 0.05), 0.68, 33, -6, 35, 3.5)
    for c, azim in (("koala", 8), ("panda", -14), ("whale", 4)):
        t0, t1 = course_t[c]
        key(F(t0), plate_c, 0.6, 40, azim)
        if c == "whale":
            key(F(t0 + 0.9), plate_c, 0.62, 40, azim)
            key(F(t1) - 1, (0, 0.03, 0.09), 0.82, 30, azim - 10, 32, 4.0)
        else:
            key(F(t1) - 1, plate_c, 0.47, 42, azim + 6)
    t0, t1 = course_t["bat"]
    gl = (0.2, 0.17, 0.12)
    key(F(t0), gl, 0.42, 9, -28, 40, 2.8)
    key(F(t1) - 1, gl, 0.34, 11, -4, 40, 2.8)
    t0 = course_t["dessert"][0]
    tend = course_t["cta"][1]
    key(F(t0), plate_c, 0.55, 40, 0)
    key(F(roll0), (0, 0.0, 0.045), 0.46, 40, 0)
    key(F(roll1), (0, 0.38, 0.12), 0.72, 16, 0, 30, 6.0)
    key(F(tend) - 1, (0, 0.42, 0.2), 0.95, 13, 0, 28, 7.0)
    return sc, cam, cues, n_frames


if __name__ == "__main__":
    timing_path, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    timing = json.load(open(timing_path))
    sc, cam, cues, n = build(timing)
    with open(os.path.join(out_dir, "cues.json"), "w") as f:
        json.dump(cues, f)
    args = sys.argv[3:]
    if args and args[0] == "still":
        for fr in args[1:]:
            sc.frame_set(int(fr))
            sc.render.filepath = os.path.join(out_dir, f"still_{int(fr):04d}.png")
            bpy.ops.render.render(write_still=True)
    elif len(args) == 2:
        bk.render(sc, out_dir, int(args[0]), min(int(args[1]), n - 1))
    print("frames:", n)
