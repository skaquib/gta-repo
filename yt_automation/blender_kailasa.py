"""
blender_kailasa.py: the 3D "how they did it" steps for build-series episode 1 (Kailasa Temple, Ellora).

One scene at real scale (metres). The temple stands inside a pit cut into a basalt plateau. Each step is a shot with its
own frame range, taken from the voice timing (run_kailasa.py writes timing.json at 15 fps):
  hill     the untouched plateau with the outline of the future pit
  trench   the pit sinks around one huge block (the fill's top lowers)
  carve    the block is cut away from the TOP DOWN: the spire appears first, then the hall, then the base
  crack    one wrong cut: a carved column breaks off and falls
  rubble   the pile of removed rock grows beside the pit, next to a person for scale
  storeys  the finished temple next to a 10-storey building

  /root/.venvs/blender/bin/python blender_kailasa.py TIMING.json FRAMES_DIR start end
  /root/.venvs/blender/bin/python blender_kailasa.py TIMING.json FRAMES_DIR still F1 F2 ...
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

FPS = 15
TOP = 35.0                         # plateau height above the pit floor
PIT = (42.0, 24.0)                 # half-size of the pit (x, y)
BLOCK = (30.0, 17.0)               # half-size of the block left standing in it
rnd = random.Random(7)


def lin(c):
    return tuple(((v / 255) ** 2.2) for v in c)


def basalt(name, color, bump=0.35, var=0.35, scale=0.08):
    """Rock: the colour varies in soft patches (noise -> ramp between a darker and a lighter tone), with bump."""
    m = bp.mat(name, lin(color), rough=0.85)
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 10.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    lo = tuple(v * (1 - var) for v in lin(color))
    hi = tuple(min(1.0, v * (1 + var)) for v in lin(color))
    ramp.color_ramp.elements[0].color = lo + (1,)
    ramp.color_ramp.elements[1].color = hi + (1,)
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bp.add_bump(m, 0.6, bump, detail=8.0, distance=0.3)
    return m


def column_box(name, x0, x1, y0, y1, z0, z1, m):
    """A box spanning the given ranges, with its origin on the BOTTOM face so scale.z lowers its top."""
    o = bp.box(name, (x1 - x0, y1 - y0, z1 - z0), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), m)
    me = o.data
    for v in me.vertices:
        v.co.z += (z1 - z0) / 2
    o.location.z = z0
    return o


def person(name, loc, m_skin, m_cloth, h=1.7):
    body = bp.cylinder(name + "_b", h * 0.13, h * 0.62, (loc[0], loc[1], loc[2] + h * 0.31), m_cloth, segs=10)
    bp.ellipsoid(name + "_h", (h * 0.09,) * 3, (loc[0], loc[1], loc[2] + h * 0.72), m_skin, segs=12, rings=8)
    return body


def temple(m):
    """A simplified Kailasa: plinth with an elephant frieze, a pillared hall, a tiered spire, a front shrine and
    two flag pillars. Everything sits inside the block (x +-30, y +-17), under 32 m tall."""
    parts = []
    parts.append(bp.box("plinth", (54, 30, 8), (0, 0, 4), m, bevel=0.3))
    m_el = basalt("elephant", (120, 104, 88))
    for i in range(13):                                     # life-size elephants along the plinth
        x = -24 + i * 4.0
        for sy in (-1, 1):
            bp.ellipsoid(f"el_{i}_{sy}", (1.6, 0.9, 1.3), (x, sy * 15.6, 2.4), m_el, segs=14, rings=8)
            bp.ellipsoid(f"elh_{i}_{sy}", (0.8, 0.7, 0.8), (x + 1.4, sy * 15.8, 3.0), m_el, segs=12, rings=8)
    parts.append(bp.box("hall", (40, 24, 11), (2, 0, 13.5), m, bevel=0.2))
    for i in range(9):                                      # pilasters
        x = -17 + i * 4.6
        for sy in (-1, 1):
            bp.box(f"pil_{i}_{sy}", (1.2, 0.8, 11), (x, sy * 12.2, 13.5), m)
    tiers = [(26, 20, 21.5), (21, 16, 24.5), (16, 12, 27.0), (11, 8, 29.0)]
    for n, (sx, sy_, z) in enumerate(tiers):                # the spire, stepping in as it rises
        bp.box(f"tier_{n}", (sx, sy_, 2.6), (10, 0, z), m, bevel=0.3)
    for n, (sx, sy_, z) in enumerate(tiers):
        for cx in (-1, 1):
            for cy in (-1, 1):
                bp.box(f"turret_{n}_{cx}_{cy}", (1.6, 1.6, 2.2), (10 + cx * (sx / 2 - 1), cy * (sy_ / 2 - 1), z + 2.2), m)
    bp.cylinder("kalasha", 2.2, 2.0, (10, 0, 31.0), m, segs=24, bevel=0.3)
    for i in range(6):                                      # roof shrines on the hall
        bp.box(f"roof_{i}", (2.4, 2.4, 2.4), (-14 + i * 4, 9 * (1 if i % 2 else -1), 20.2), m)
    bp.box("nandi", (8, 8, 9), (-24, 0, 12.5), m, bevel=0.2)      # front shrine on its bridge
    bp.box("bridge", (6, 3, 1.2), (-21, 0, 16.2), m)
    cols = []
    for sy in (-1, 1):                                      # two flag pillars in the courtyard
        cols.append(bp.cylinder(f"flag_{sy}", 0.9, 17, (-27, sy * 13, 8.5), m, segs=16))
    return cols


def build(samples):
    sc = bk.new_scene(fps=FPS, res=(540, 960), samples=samples, frames=10)
    sc.view_settings.view_transform, sc.view_settings.look = "AgX", "AgX - Medium High Contrast"
    bp.world(sc, lin((120, 158, 210)), 0.55)
    bp.light("sun", "SUN", (0, 0, 80), 5.5, size=1.5, color=(1.0, 0.82, 0.62),
             rot=(math.radians(62), math.radians(6), math.radians(-40)))      # low warm sun: long shadows
    m_rock = basalt("rock", (64, 58, 54))
    m_top = basalt("plateau", (120, 100, 78), bump=0.25, var=0.4, scale=0.03)
    m_fill = basalt("fill", (78, 70, 64))
    m_tem = basalt("temple", (176, 146, 112), bump=0.2, var=0.2, scale=0.2)
    m_skin, m_cloth = bp.mat("skin", lin((150, 100, 70)), 0.6), bp.mat("cloth", lin((235, 228, 210)), 0.8)
    # plateau around the pit: four slabs, wide enough to fill the frame
    W = 260
    column_box("plat_n", -W, W, PIT[1], W, 0, TOP, m_top)
    column_box("plat_s", -W, W, -W, -PIT[1], 0, TOP, m_top)
    column_box("plat_e", PIT[0], W, -PIT[1], PIT[1], 0, TOP, m_top)
    column_box("plat_w", -W, -PIT[0], -PIT[1], PIT[1], 0, TOP, m_top)
    bp.box("floor", (2 * PIT[0], 2 * PIT[1], 0.4), (0, 0, -0.2), m_rock)
    # the trench fill (ring between pit edge and block) and the block itself
    fills = [column_box("fill_n", -PIT[0], PIT[0], BLOCK[1], PIT[1], 0, TOP, m_fill),
             column_box("fill_s", -PIT[0], PIT[0], -PIT[1], -BLOCK[1], 0, TOP, m_fill),
             column_box("fill_e", BLOCK[0], PIT[0], -BLOCK[1], BLOCK[1], 0, TOP, m_fill),
             column_box("fill_w", -PIT[0], -BLOCK[0], -BLOCK[1], BLOCK[1], 0, TOP, m_fill)]
    block = column_box("block", -BLOCK[0], BLOCK[0], -BLOCK[1], BLOCK[1], 0, TOP, m_rock)
    cols = temple(m_tem)
    # outline ropes marking the cut on the plateau
    m_rope = bp.mat("rope", lin((240, 230, 200)), 0.6)
    ropes = []
    for (hx, hy, nm) in ((PIT[0], PIT[1], "pit"), (BLOCK[0], BLOCK[1], "blk")):
        for sx, sy, w, h in ((0, hy, 2 * hx, 0.25), (0, -hy, 2 * hx, 0.25), (hx, 0, 0.25, 2 * hy), (-hx, 0, 0.25, 2 * hy)):
            ropes.append(bp.box(f"rope_{nm}_{sx}_{sy}", (w, h, 0.12), (sx, sy, TOP + 0.08), m_rope))
    # workers on top of the plateau and the block
    workers = []
    for i in range(40):
        x, y = rnd.uniform(-40, 40), rnd.choice([-1, 1]) * rnd.uniform(18, 23)
        workers.append(person(f"w{i}", (x, y, TOP), m_skin, m_cloth))
    # the rubble pile (a cone that grows) and the person next to it, outside the pit
    pile = bp.cylinder("pile", 1.0, 1.0, (70, -55, TOP), m_fill, segs=48)
    bpy.context.view_layer.objects.active = pile
    for v in pile.data.vertices:                             # cone: shrink the top ring to a point, origin at the base
        if v.co.z > 0:
            v.co.x *= 0.02
            v.co.y *= 0.02
        v.co.z += 0.5
    pile.location.z = TOP
    scale_guy = person("scale_guy", (50, -70, TOP), m_skin, m_cloth, h=1.8)
    # 10-storey building for scale, standing in the courtyard gap beside the temple
    m_bld = bp.mat("bld", lin((120, 170, 230)), 0.4, alpha=1.0)
    bld = bp.box("building", (9, 9, 32), (36, -19, 16), m_bld)
    m_win = bp.mat("win", lin((250, 250, 240)), 0.3)
    floors = [bp.box(f"floor_{i}", (9.2, 9.2, 0.25), (36, -19, 3.2 * i), m_win) for i in range(1, 10)]
    # a separate breakable column for the "no undo" close-up (sits on the plinth front)
    m_col = basalt("col", (150, 128, 104), bump=0.25)
    col_low = bp.cylinder("col_low", 0.8, 4.0, (-27, -6, 10.0), m_col, segs=24)
    col_up = bp.cylinder("col_up", 0.8, 4.0, (-27, -6, 14.0), m_col, segs=24)
    cam = bp.cam_free(sc, 30, (0, -120, 120), (0, 0, 10))
    return sc, dict(fills=fills, block=block, ropes=ropes, workers=workers, pile=pile, guy=scale_guy, bld=[bld] + floors,
                    cols=cols, col_up=col_up, col_low=col_low, cam=cam)


def vis(o, f0, f1):
    """Visible only in [f0, f1]."""
    for f, h in ((0, True), (f0, False), (f1 + 1, True)):
        o.hide_render = h
        o.keyframe_insert("hide_render", frame=f)
        o.hide_viewport = h
        o.keyframe_insert("hide_viewport", frame=f)
    for fc in o.animation_data.action.fcurves if hasattr(o.animation_data.action, "fcurves") else []:
        for kp in fc.keyframe_points:
            kp.interpolation = "CONSTANT"


def key_cam(cam, f, loc, at, lens=30):
    cam.location = loc
    bp.aim(cam, loc, at)
    cam.keyframe_insert("location", frame=f)
    cam.keyframe_insert("rotation_euler", frame=f)
    cam.data.lens = lens
    cam.data.keyframe_insert("lens", frame=f)


def zkey(o, f, z):
    o.scale.z = max(z, 1e-4)
    o.keyframe_insert("scale", index=2, frame=f)


def timeline(sc, S, T):
    sh = {s["name"]: (s["f0"], s["f1"]) for s in T["b3d"]}
    end = T["b3d_frames"] - 1
    for o in S["fills"] + [S["block"]]:
        zkey(o, 0, 1.0)
    for o in S["bld"] + [S["pile"], S["guy"]] + S["ropes"]:
        vis(o, end + 10, end + 11)                           # hidden unless a shot shows it
    for o in S["ropes"]:
        vis(o, *sh["hill"])
    f0, f1 = sh["hill"]
    key_cam(S["cam"], f0, (-14, -88, 110), (0, 0, TOP), 28)
    key_cam(S["cam"], f1, (-10, -72, 92), (0, 0, TOP), 28)
    f0, f1 = sh["trench"]
    key_cam(S["cam"], f0, (-24, -70, 84), (0, 0, 16), 26)
    key_cam(S["cam"], f1, (-40, -62, 70), (0, 0, 10), 26)
    for o in S["fills"]:
        zkey(o, f0, 1.0)
        zkey(o, f0 + int((f1 - f0) * 0.85), 0.0)
    f0, f1 = sh["carve"]
    key_cam(S["cam"], f0, (-46, -58, 62), (0, 0, 16), 26)
    key_cam(S["cam"], f1, (-56, -44, 46), (0, 0, 12), 26)
    zkey(S["block"], f0, 1.0)
    zkey(S["block"], f0 + int((f1 - f0) * 0.9), 0.0)
    f0, f1 = sh["crack"]                                    # close on the breakable column, upper part tips and falls
    key_cam(S["cam"], f0, (-39, -16, 11), (-27, -6, 12), 34)
    key_cam(S["cam"], f1, (-38.5, -16.5, 10.5), (-27, -6, 11), 34)
    up = S["col_up"]
    fb = f0 + int((f1 - f0) * 0.35)
    for f, rot, loc in ((f0, 0.0, (-27, -6, 14.0)), (fb, 0.0, (-27, -6, 14.0)), (fb + 6, math.radians(25), (-27.6, -6.4, 13.4)),
                        (fb + 14, math.radians(88), (-30.5, -7.5, 9.2)), (f1, math.radians(90), (-30.6, -7.5, 9.0))):
        up.rotation_euler = (0, -rot, 0)
        up.location = loc
        up.keyframe_insert("rotation_euler", frame=f)
        up.keyframe_insert("location", frame=f)
    up.location, up.rotation_euler = (-27, -6, 14.0), (0, 0, 0)
    up.keyframe_insert("location", frame=f1 + 1)
    up.keyframe_insert("rotation_euler", frame=f1 + 1)
    f0, f1 = sh["rubble"]
    vis(S["pile"], f0, f1)
    vis(S["guy"], f0, f1)
    S["pile"].scale = (0.01, 0.01, 0.01)
    S["pile"].keyframe_insert("scale", frame=f0)
    S["pile"].scale = (34, 34, 30)
    S["pile"].keyframe_insert("scale", frame=f0 + int((f1 - f0) * 0.85))
    key_cam(S["cam"], f0, (44, -84, 40), (62, -55, 48), 30)
    key_cam(S["cam"], f1, (40, -92, 44), (64, -55, 50), 30)
    f0, f1 = sh["storeys"]
    for o in S["bld"]:
        vis(o, f0, f1)
    key_cam(S["cam"], f0, (64, -66, 72), (16, -8, 14), 28)
    key_cam(S["cam"], f1, (70, -58, 66), (16, -8, 14), 28)
    # every shot holds its own camera: constant jumps between shots
    for d in (S["cam"], S["cam"].data):
        act = d.animation_data.action
        for fc in getattr(act, "fcurves", []):
            for kp in fc.keyframe_points:
                kp.interpolation = "BEZIER"
    sc.frame_end = end


if __name__ == "__main__":
    tpath, frames_dir = sys.argv[1:3]
    rest = sys.argv[3:]
    T = json.load(open(tpath))
    sc, S = build(int(os.environ.get("DUMMY_SAMPLES", "12")))
    timeline(sc, S, T)
    os.makedirs(frames_dir, exist_ok=True)
    if rest and rest[0] == "still":
        for f in rest[1:]:
            sc.frame_set(int(f))
            sc.render.filepath = os.path.join(frames_dir, f"s_{int(f):04d}.png")
            bpy.ops.render.render(write_still=True)
            print("saved", sc.render.filepath, flush=True)
    else:
        bk.render(sc, frames_dir, int(rest[0]), int(rest[1]))
