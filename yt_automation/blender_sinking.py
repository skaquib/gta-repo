"""
blender_sinking.py -- Dummy Test #5 ("60 seconds underwater": his car goes into a river): the scene and the opening
options for the owner to pick from (rule 14, rule 18). Same car and dummy (v2) as the lightning Short.

  /root/.venvs/blender/bin/python blender_sinking.py OUT_DIR A|B|C [FRAME ...]     (default 0 12 24 48)

A  waterline: the lens half in the river -- above, him at the side window; below, the nose sinking in murky green
   water, headlight beams and bubbles
B  windshield: from just above the water in front, the river pouring over the hood against the glass, him behind it
C  inside: his face big from the passenger seat, water bursting in from the footwell, green water outside the glass

The river is one closed box (wavy top) with a water surface and a murky volume, so anything below z=0 -- the nose,
the footwell, later the whole cabin -- is underwater with no extra work.
"""
import math
import os
import random
import sys

import bpy  # noqa: I001
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_kit as bk  # noqa: E402
import blender_pitches as bp  # noqa: E402
import blender_lightning as bl  # noqa: E402

O, VIS = bl.O, bl.VIS
R = random.Random(5)


# ── materials ─────────────────────────────────────────────────────────────────
def river_mat(split=False):
    """Water surface (clear, rippled) + murky green volume below it. split: camera rays cross the surface without
    bending, as through a half-submerged lens -- from just above the water you could not see sideways under it."""
    m = bpy.data.materials.new("river")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (0.75, 0.9, 0.85, 1)
    b.inputs["Roughness"].default_value = 0.03
    b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["IOR"].default_value = 1.33
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value, nz.inputs["Detail"].default_value = 9.0, 4.0
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value, bump.inputs["Distance"].default_value = 0.25, 0.01
    nt.links.new(nz.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    ab = nt.nodes.new("ShaderNodeVolumeAbsorption")
    ab.inputs["Color"].default_value = (0.32, 0.72, 0.6, 1)       # reds go first: green-teal river
    ab.inputs["Density"].default_value = 0.32
    scat = nt.nodes.new("ShaderNodeVolumeScatter")
    scat.inputs["Color"].default_value = (0.45, 0.8, 0.7, 1)
    scat.inputs["Density"].default_value = 0.2
    scat.inputs["Anisotropy"].default_value = 0.45                # forward scatter: headlight beams show
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(ab.outputs[0], add.inputs[0])
    nt.links.new(scat.outputs[0], add.inputs[1])
    # shadow rays pass straight through the surface, or lights above the river never reach under it
    # (refractive caustics are off): the sunk nose, his legs and the beams get lit through the water
    lp = nt.nodes.new("ShaderNodeLightPath")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(b.outputs[0], mx.inputs[1])
    nt.links.new(tr.outputs[0], mx.inputs[2])
    sv = nt.nodes.new("ShaderNodeValue")                       # keyable: on only for the waterline shots
    sv.name = "split"
    sv.outputs[0].default_value = 1.0 if split else 0.0
    cam = nt.nodes.new("ShaderNodeMath")
    cam.operation = "MULTIPLY"
    nt.links.new(lp.outputs["Is Camera Ray"], cam.inputs[0])
    nt.links.new(sv.outputs[0], cam.inputs[1])
    mxm = nt.nodes.new("ShaderNodeMath")
    mxm.operation = "MAXIMUM"
    nt.links.new(lp.outputs["Is Shadow Ray"], mxm.inputs[0])
    nt.links.new(cam.outputs[0], mxm.inputs[1])
    nt.links.new(mxm.outputs[0], mx.inputs[0])
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(mx.outputs[0], o.inputs["Surface"])
    nt.links.new(add.outputs[0], o.inputs["Volume"])
    return m


def foam_mat():
    """White foam with a noise mask (alpha), for the splash ring and the water pouring in."""
    m = bpy.data.materials.new("foam")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (0.85, 0.92, 0.95, 1)
    b.inputs["Roughness"].default_value = 0.35
    b.inputs["Emission Color"].default_value = (0.7, 0.85, 0.95, 1)
    b.inputs["Emission Strength"].default_value = 0.25           # reads at night without a light on it
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value, nz.inputs["Detail"].default_value = 6.0, 8.0
    rr = nt.nodes.new("ShaderNodeMapRange")
    rr.inputs["From Min"].default_value, rr.inputs["From Max"].default_value = 0.56, 0.7     # patchy, not a blanket
    nt.links.new(nz.outputs["Fac"], rr.inputs["Value"])
    nt.links.new(rr.outputs["Result"], b.inputs["Alpha"])
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(b.outputs[0], o.inputs["Surface"])
    return m


def drop_mat():
    m = bp.mat("drop", (0.8, 0.9, 0.95), rough=0.05)
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Emission Color"].default_value = (0.75, 0.88, 1.0, 1)
    b.inputs["Emission Strength"].default_value = 0.3
    return m


# ── the river ─────────────────────────────────────────────────────────────────
def river(size=26.0, cuts=260, depth=9.0, amp=0.035, split=False):
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=cuts, y_subdivisions=cuts, size=size, location=(0, 0, 0))
    ob = bpy.context.active_object
    ob.name = "river"
    for p in ob.data.polygons:
        p.use_smooth = True
    tex = bpy.data.textures.new("waves", "CLOUDS")
    tex.noise_scale, tex.noise_depth = 0.9, 2
    drift = bp.pivot("wave_drift", (0, 0, 0))
    dm = ob.modifiers.new("waves", "DISPLACE")
    dm.texture, dm.strength, dm.mid_level = tex, amp, 0.5
    dm.texture_coords, dm.texture_coords_object = "OBJECT", drift
    so = ob.modifiers.new("depth", "SOLIDIFY")
    so.thickness, so.offset, so.use_rim = depth, -1.0, True
    O["river_mat"] = river_mat(split)
    ob.data.materials.append(O["river_mat"])
    for f, x in ((0, 0.0), (720, 4.0)):                       # the waves roll slowly downstream
        drift.location = (x, x * 0.3, 0)
        drift.keyframe_insert("location", frame=f)
    bk._set_interp(drift.animation_data.action, 0, "LINEAR")
    O["drift"] = drift
    return ob


def far_bank():
    dark = bp.mat("bank", (0.01, 0.012, 0.012), rough=0.9)
    bp.box("bank", (60, 6, 1.6), (0, 16, 0.5), dark)
    for j in range(14):                         # a few houses and street lights on the far bank: night, a river
        c = (R.uniform(1.0, 0.75), R.uniform(0.55, 0.75), R.uniform(0.25, 0.4))
        bp.ellipsoid(f"banklight{j}", (0.06, 0.06, 0.06), (R.uniform(-20, 20), R.uniform(13.5, 15), R.uniform(1.4, 2.2)),
                     bl.emit(f"bl{j}", c, 40))


def build(samples=24, which="A"):
    VIS.clear(), O.clear()
    sc = bk.new_scene(fps=24, samples=samples, frames=73)
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.35
    sc.view_settings.exposure = 0.45
    sc.cycles.volume_bounces = 0
    bp.world(sc, (0.022, 0.03, 0.05), 0.55)
    river(split=(which == "A"))
    far_bank()
    bl.make_car(sc, label="TEST 05")
    car = O["car"]
    car.rotation_mode = "XYZ"
    for k in [k for k in O if k.startswith(("tire", "hub"))]:   # loose in the lightning Short (the blowout)
        O[k].parent = car
    for s in (-1, 1):                                          # headlights still on: beams in the murky water
        hl = bp.light(f"beam{s}", "SPOT", (s * 0.6, -2.25, 0.76), 260, color=(1.0, 0.92, 0.78),
                      rot=(math.radians(-90), 0, 0))
        hl.data.spot_size, hl.data.spot_blend, hl.data.shadow_soft_size = math.radians(42), 0.35, 0.05
        hl.parent = car
    O["drop_m"] = drop_mat()
    O["foam_m"] = foam_mat()
    O["glass_m"] = bl.glass("bubble")
    # moon, rim and a key from the camera side (above the water: a light under it would be swallowed)
    bp.light("moon", "SUN", (0, 0, 10), 1.6, size=2.0, color=(0.62, 0.72, 1.0),
             rot=(math.radians(50), 0, math.radians(200)))
    bp.light("rim", "AREA", (2.5, 4.0, 3.2), 700, size=2.0, color=(0.75, 0.85, 1.0), aim=(0, -0.5, 0.6))
    bp.light("key", "AREA", (-3.8, -2.4, 2.8), 520, size=2.5, color=(0.78, 0.86, 1.0), aim=(-0.6, -0.4, 0.6))
    cf = bp.light("cabin_fill", "AREA", (0.25, -0.45, 1.5), 22, size=0.4, color=(0.9, 0.95, 1.0),
                  aim=(-0.4, 0.3, 1.3))
    cf.parent = car
    for ob in sc.objects:
        if ob.type == "LIGHT":
            ob.visible_camera = False
            if ob.name in ("rim", "cabin_fill"):              # their reflections were white squares on the glass
                ob.visible_glossy = False
    return sc


# ── story props (the full Short) ──────────────────────────────────────────────
def quad(name, verts, mat, parent):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], [list(range(len(verts)))])
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    bp.link(ob)
    ob.parent = parent
    return ob


def story_props():
    """Driver window that can move and break, seatbelt, phone, window hammer, water-pressure arrows."""
    car, P = O["car"], O["P"]
    cab = bpy.data.objects["cabin"]
    hole = bpy.data.materials.new("hole")                      # the driver-side face becomes an opening
    hole.use_nodes = True
    hn = hole.node_tree
    for n in list(hn.nodes):
        hn.nodes.remove(n)
    out = hn.nodes.new("ShaderNodeOutputMaterial")
    hn.links.new(hn.nodes.new("ShaderNodeBsdfTransparent").outputs[0], out.inputs["Surface"])
    cab.data.materials.append(hole)
    cab.data.polygons[3].material_index = len(cab.data.materials) - 1
    # glass whose mirror reflection a shot can turn down: seen from beside the car, the windshield and the driver's
    # window mirror the key light as a pale slab right across the cabin
    def dimmable(name):
        m = bl.glass(name)
        nt = m.node_tree
        refl = nt.nodes.new("ShaderNodeValue")
        refl.name, refl.outputs[0].default_value = "refl", 1.0
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        mix = next(n for n in nt.nodes if n.type == "MIX_SHADER")
        nt.links.new(next(n for n in nt.nodes if n.type == "LAYER_WEIGHT").outputs["Fresnel"], mul.inputs[0])
        nt.links.new(refl.outputs[0], mul.inputs[1])
        nt.links.new(mul.outputs[0], mix.inputs[0])
        return m
    ws, win = dimmable("windshield"), dimmable("driver_glass")
    O["dim_glass"] = [ws, win]
    cab.data.materials.append(ws)
    cab.data.polygons[0].material_index = len(cab.data.materials) - 1
    O["pane"] = quad("pane", [(-0.815, -0.93, 0.95), (-0.815, 0.24, 0.95), (-0.705, 0.29, 1.62),
                              (-0.705, -0.2, 1.62)], win, car)
    # a pale line along the glass's top edge: clear glass is invisible, so this is what shows the window moving
    O["pane_edge"] = bl.rod("pane_edge", (-0.705, -0.2, 1.615), (-0.705, 0.29, 1.615), 0.006,
                            bl.emit("pane_edge", (0.7, 1.0, 0.95), 1.3), O["pane"])
    quad("rear_pane", [(-0.815, 0.26, 0.95), (-0.815, 1.29, 0.95), (-0.705, 0.79, 1.62), (-0.705, 0.31, 1.62)], win, car)
    web = bp.mat("webbing", (0.03, 0.03, 0.035), rough=0.85)
    O["belt"] = [bl.poly("belt", [Vector(v) for v in ((-0.6, 0.36, 1.24), (-0.52, 0.17, 1.12), (-0.38, 0.16, 0.93),
                                                       (-0.2, 0.22, 0.74))], 0.02, web),
                 bl.poly("lap", [Vector(v) for v in ((-0.66, 0.34, 0.74), (-0.42, 0.13, 0.7), (-0.2, 0.22, 0.73))],
                         0.02, web)]
    O["belt_loose"] = bl.poly("belt_loose", [Vector(v) for v in ((-0.6, 0.36, 1.24), (-0.66, 0.4, 0.95))], 0.02, web)
    bp.box("buckle", (0.05, 0.03, 0.02), (-0.2, 0.22, 0.73), bp.mat("buckle", (0.6, 0.6, 0.62), rough=0.3,
                                                                     metallic=1.0), car)
    for o in O["belt"] + [O["belt_loose"]]:
        o.parent = car
    dark = bp.mat("phone", (0.02, 0.02, 0.025), rough=0.3)
    # sized up from a real phone so it reads at Shorts size; hold_phone() seats it in his hand for the shot
    O["phone"] = [bp.box("phone", (0.09, 0.014, 0.18), (0, -0.032, -0.38), dark, P["el-1"], bevel=0.008),
                  bp.box("screen", (0.08, 0.002, 0.16), (0, -0.04, -0.38), bl.emit("screen", (0.55, 0.8, 1.0), 12),
                         P["el-1"])]
    gd = bpy.data.lights.new("phone_glow", "POINT")            # the screen's blue light on his face
    gd.energy, gd.color, gd.shadow_soft_size = 6.0, (0.55, 0.8, 1.0), 0.03
    glow = O["phone_glow"] = bpy.data.objects.new("phone_glow", gd)
    bpy.context.scene.collection.objects.link(glow)
    glow.parent = P["el-1"]
    glow.visible_camera = glow.visible_glossy = False
    # the window hammer: red handle, steel head. Built at the origin; hold_hammer() seats it in his fist
    red = bp.mat("hammer", (0.85, 0.05, 0.03), rough=0.4)
    rb = red.node_tree.nodes["Principled BSDF"]
    rb.inputs["Emission Color"].default_value, rb.inputs["Emission Strength"].default_value = (1.0, 0.06, 0.03, 1), 0.5
    O["hammer"] = [bp.cylinder("hammer_grip", 0.024, 0.27, (0, 0, 0), red, P["el-1"]),
                   bp.box("hammer_head", (0.2, 0.06, 0.06), (0, 0, 0), bp.mat("hammer_steel", (0.62, 0.62, 0.66),
                                                                              rough=0.25, metallic=1.0),
                          P["el-1"], bevel=0.008)]
    blue = bl.emit("pressure", (0.15, 0.5, 1.0), 4.5)
    O["arrows"] = []
    # the camera looks along +x at the door, so the arrows come in diagonally from both sides: they read as
    # converging on the door instead of pointing away from the lens
    for j, (yc, z, sgn) in enumerate(((-0.1, 0.45, 1), (-0.1, 0.45, -1), (0.0, 0.72, 1), (0.0, 0.72, -1))):
        tail = Vector((-1.5, yc - sgn * 0.75, z))
        tip = Vector((-0.97, yc - sgn * 0.18, z))
        d = (tip - tail).normalized()
        shaft = bl.rod(f"arrow{j}", tail, tip - d * 0.1, 0.028, blue, car)
        bpy.ops.mesh.primitive_cone_add(radius1=0.075, radius2=0.0, depth=0.16, location=tuple(tip - d * 0.06))
        cone = bpy.context.active_object
        cone.name, cone.parent = f"arrowtip{j}", car
        cone.rotation_mode = "QUATERNION"
        cone.rotation_quaternion = d.to_track_quat("Z", "Y")
        cone.data.materials.append(blue)
        O["arrows"] += [shaft, cone]
    for o in O["phone"] + O["hammer"] + O["arrows"] + [O["belt_loose"], O["phone_glow"], O["pane_edge"]]:
        bl.on(o, set())                                        # hidden until a shot shows them


def hold_hammer(sc, f):
    """Seat the window hammer in his door-side fist as posed at frame f: handle along the forearm and out past the
    fist, steel head across its top, pointing at his window."""
    from mathutils import Matrix
    keep = sc.frame_current
    sc.frame_set(f)
    el = O["P"]["el-1"].matrix_world
    u = (el.to_3x3() @ Vector((0, 0, -1))).normalized()       # along the forearm
    h = O["car"].matrix_world.to_3x3() @ Vector((-1, 0, 0))    # toward the driver's window
    h = (h - u * h.dot(u)).normalized()
    rot = Matrix((h, u.cross(h), u)).transposed().to_4x4()     # columns x (head), y, z (handle)
    palm = (el.to_3x3() @ Vector((0, -1, 0))).normalized()
    fist = el @ Vector((0, 0, -0.335)) + palm * 0.03           # the handle lies in his palm, not through his hand
    grip, head = O["hammer"]
    grip.matrix_world = Matrix.Translation(fist + u * 0.085) @ rot
    head.matrix_world = Matrix.Translation(fist + u * 0.235 + h * 0.01) @ rot
    sc.frame_set(keep)


def hold_phone(sc, f):
    """Seat the phone upright in his right hand as posed at frame f, screen turned to his face, so the camera sees
    its dark back against his yellow chest and the screen's glow on his face (the old forearm offset buried it
    inside the mitten hand)."""
    from mathutils import Matrix
    keep = sc.frame_current
    sc.frame_set(f)
    P = O["P"]
    hand = P["el-1"].matrix_world @ Vector((0, 0, -0.36))
    face = P["head"].matrix_world.translation + Vector((0, -0.05, 0.11))
    n = (face - hand).normalized()                             # screen normal (the phone's local -y)
    z = (Vector((0, 0, 1)) - n * n.z).normalized()             # long axis: as upright as the tilt allows
    y = -n
    rot = Matrix((y.cross(z), y, z)).transposed().to_4x4()     # columns x, y, z
    centre = hand + z * 0.06                                   # his hand grips the lower third
    phone, screen = O["phone"]
    phone.matrix_world = Matrix.Translation(centre) @ rot
    screen.matrix_world = Matrix.Translation(centre + n * 0.008) @ rot
    O["phone_glow"].matrix_world = Matrix.Translation(centre + n * 0.14)   # nearer his face than his hands
    sc.frame_set(keep)


# ── events ────────────────────────────────────────────────────────────────────
def car_motion(keys):
    """keys: [(frame, z, pitch_deg, roll_deg, y)] -- pitch > 0 is nose down."""
    car = O["car"]
    for f, z, pitch, roll, y in keys:
        car.location = (0, y, z)
        car.rotation_euler = (math.radians(pitch), math.radians(roll), 0)
        car.keyframe_insert("location", frame=f)
        car.keyframe_insert("rotation_euler", frame=f)


def splash(f0, at, n=240, speed=2.6, up=(1.5, 4.8), size=0.011, life=30):
    bl.burst(f"splash{f0}", at, f0, n, speed=speed, up=up, mat=O["drop_m"], size=size, life=life)


def foam_ring(f0, f1, center=(0, -1.9, 0.012), radius=1.5):
    ring = bp.box("foam_ring", (radius * 2, radius * 2.6, 0.004), center, O["foam_m"])
    for f, s in ((f0, 0.35), (f0 + 6, 1.0), (f1, 1.25)):
        ring.scale = (s, s, 1)
        ring.keyframe_insert("scale", frame=f)
    bl.on(ring, range(f0, f1))
    return ring


def bubbles(f0, f1, n=70):
    for j in range(n):
        r = R.uniform(0.006, 0.022)
        b = bp.ellipsoid(f"bubble{j}", (r, r, r * 0.85), (0, 0, -3), O["glass_m"], segs=12, rings=8)
        start = R.randint(f0, f1 - 20)
        p = Vector((R.uniform(-0.9, 0.9), R.uniform(-2.0, -0.6), R.uniform(-1.6, -0.5)))
        rise = R.uniform(0.5, 0.9)
        for f in range(start, min(f1, start + 72) + 1, 3):
            t = (f - start) / 24
            q = p + Vector((0.04 * math.sin(6 * t + j), 0.03 * math.cos(5 * t + j), rise * t))
            if q.z > -0.02:
                break
            b.location = q
            b.keyframe_insert("location", frame=f)
        bl.on(b, range(start, f))


def gush(f0, f1):
    """Water bursting in under the dash (car space): flickering foam jets towards his legs."""
    jets = []
    for j in range(5):
        a = Vector((R.uniform(-0.75, -0.05), -0.86, R.uniform(0.45, 0.7)))
        b = a + Vector((R.uniform(-0.1, 0.1), R.uniform(0.45, 0.8), R.uniform(0.1, 0.35)))
        jet = bl.poly(f"jet{j}", bl.jagged(a, b, 3, 0.12), 0.03, O["foam_m"], taper=(1.4, 0.4))
        jet.parent = O["car"]
        jets.append(jet)
    bl.flicker(jets, f0, f1, pattern=(1, 1, 1, 0, 1, 1, 0, 1))
    return jets


def opening_poses(P, f0):
    bl.pose(P, f0, sh=(-75, 0, 0), el=(-20, 0, 0), head=(-14, 0, 0), chest=(-10, 0, 0), hip=(-90, 0, 0),
            kn=(90, 0, 0))                                                           # thrown forward on impact
    bl.pose(P, f0 + 4, sh=(-125, 8, 0), el=(-60, 0, 0), head=(16, 0, -10), chest=(6, 0, 0))   # arms fly up
    bl.pose(P, f0 + 14, sh=(-118, 14, 0), el=(-75, 0, 0), head=(20, 0, -24), chest=(4, 0, -6))
    bl.pose(P, f0 + 28, **{"sh-1": (-95, 40, 0), "el-1": (-35, 0, 0), "sh1": (-120, -10, 0), "el1": (-80, 0, 0),
                           "head": (8, 0, -34), "chest": (2, 0, -10)})                # turns to the window
    bl.pose(P, f0 + 48, **{"sh-1": (-100, 48, 0), "el-1": (-25, 0, 0), "sh1": (-70, -20, 0), "el1": (-40, 0, 0),
                           "head": (4, 0, -38), "chest": (0, 0, -12)})


def finalize(end):
    for ob, frames in VIS.items():
        prev = None
        for f in range(0, end + 1):
            h = f not in frames
            if h != prev:
                ob.hide_render = h
                ob.keyframe_insert("hide_render", frame=f)
                prev = h


# ── openings ──────────────────────────────────────────────────────────────────
LEAD = 4
OPENING_MOTION = [(0, 0.05, 28, 0, -0.35), (5, -0.32, 39, -3, -0.55), (16, -0.22, 33, 2, -0.6),
                  (30, -0.3, 36, -1, -0.62), (48, -0.36, 37, 1, -0.64), (72, -0.42, 38, 0, -0.65)]

CAMS = {   # (location, aim, lens, parented to the car)
    "A": ((-3.9, -2.1, 0.004), (-0.6, -1.6, 0.05), 17, False),
    "B": ((-0.42, -3.6, 0.42), (-0.42, -0.9, 0.75), 22, False),
    "C": ((0.05, -0.6, 1.32), (-0.4, 0.3, 1.3), 18, True),
}


def camera(sc, which):
    loc, aim, lens, on_car = CAMS[which]
    cd = bpy.data.cameras.new("cam")
    cd.sensor_fit, cd.sensor_height, cd.lens, cd.clip_start = "VERTICAL", 24.0, lens, 0.01
    cam = bpy.data.objects.new("cam", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.location = loc
    tgt = bp.pivot("cam_aim", aim)
    if on_car:
        cam.parent = tgt.parent = O["car"]
    c = cam.constraints.new("TRACK_TO")
    c.target = tgt
    c.track_axis, c.up_axis = "TRACK_NEGATIVE_Z", "UP_Y"
    return cam


if __name__ == "__main__":
    out, which = sys.argv[1], sys.argv[2]
    frames = [int(f) for f in sys.argv[3:]] or [0, 12, 24, 48]
    sc = build(int(os.environ.get("PITCH_SAMPLES", "24")), which)
    L = -LEAD                                                  # frame 0 is already the impact, not the moment before
    car_motion([(f + L, *rest) for f, *rest in OPENING_MOTION])
    opening_poses(O["P"], L)
    splash(L, (0.0, -2.2, 0.05))
    splash(L + 2, (-0.95, -1.4, 0.05), n=60, speed=1.6, up=(1.0, 3.0))
    splash(L + 2, (0.95, -1.4, 0.05), n=60, speed=1.6, up=(1.0, 3.0))
    foam_ring(L, 73)
    bubbles(0, 72)
    gush(0, 72)
    finalize(72)
    camera(sc, which)
    os.makedirs(out, exist_ok=True)
    for f in frames:
        sc.frame_set(f)
        sc.render.filepath = os.path.join(out, f"{which}_{f:03d}.png")
        bpy.ops.render.render(write_still=True)
        print("saved", sc.render.filepath, flush=True)
