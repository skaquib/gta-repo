"""
blender_whatif.py — scenes for the "What If You ..." Shorts (dummy_shorts.py; notes/trends/2026-11-11_turning_points.md).

The subject is the viewer: the figure is a plain human mannequin, and the inside of the body is shown close up as a
cutaway block of skin, fat, muscle and bone with its labels, so each line of the explanation has its own picture.

  lavayou   "What If You Fell Into Lava for 10 Seconds?": you land ON the lava, skin chars, water flashes to
            steam, fat melts and burns, muscle cooks, bone is untouched (a cremation oven needs ~2 hours)
"""
import math
import random

import bpy
from mathutils import Vector

import blender_pitches as bp
import blender_tensec as ts
from blender_tensec import EPS, FPS, O, emit, flames, k, kval, linear, no_light, pose, puffs, shot, shown, splash

SKIN_TONE = (0.80, 0.50, 0.36)
AWAY = 60.0            # where the figure or the block waits while the other one is on screen


def humanise():
    """The crash-test dummy becomes a plain human mannequin: skin tone, no stencils, no targets."""
    for name, col in (("dummy2_yellow", SKIN_TONE), ("dummy2_face", SKIN_TONE)):
        nt = bpy.data.materials[name].node_tree
        for n in nt.nodes:
            if n.type == "RGB":
                n.outputs[0].default_value = (*col, 1)
            if n.type == "MIX" and n.data_type == "RGBA":
                for key in ("A", "B"):
                    if not n.inputs[key].is_linked:
                        c = n.inputs[key].default_value
                        if c[0] > 0.5 and c[2] < 0.3:                    # the yellows
                            n.inputs[key].default_value = (*col, 1)
        b = nt.nodes["Principled BSDF"]
        if not b.inputs["Base Color"].is_linked:
            b.inputs["Base Color"].default_value = (*col, 1)
    for name, col in (("dummy2_rubber", (0.42, 0.24, 0.17)), ("dummy2_seam", (0.6, 0.36, 0.26)),
                      ("dummy2_steel", (0.5, 0.3, 0.22))):
        m = bpy.data.materials.get(name)
        if m:
            b = m.node_tree.nodes["Principled BSDF"]
            b.inputs["Base Color"].default_value = (*col, 1)
            b.inputs["Metallic"].default_value = 0.0
            b.inputs["Roughness"].default_value = 0.6
    for o in bpy.data.objects:
        if o.name.startswith(("chest_label", "chest_tgt", "head_tgt", "tgt", "ribF", "ribS")) or "label" in o.name:
            o.hide_render = True


def charrable(m, ember=1.1, to=(0.012, 0.009, 0.007)):
    """Adds a `char` value (0-1) to a plain material: it glows as it goes, then is black."""
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    base = tuple(b.inputs["Base Color"].default_value)
    v = nt.nodes.new("ShaderNodeValue")
    v.name = "char"
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["A"].default_value = base
    mix.inputs["B"].default_value = (*to, 1)
    nt.links.new(v.outputs[0], mix.inputs["Factor"])
    nt.links.new(mix.outputs["Result"], b.inputs["Base Color"])
    inv = nt.nodes.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    nt.links.new(v.outputs[0], inv.inputs[1])
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    nt.links.new(v.outputs[0], mul.inputs[0])
    nt.links.new(inv.outputs[0], mul.inputs[1])
    tex = nt.nodes.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = 28.0
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(tc.outputs["Object"], tex.inputs["Vector"])
    m2 = nt.nodes.new("ShaderNodeMath")
    m2.operation = "MULTIPLY"
    nt.links.new(mul.outputs[0], m2.inputs[0])
    nt.links.new(tex.outputs["Fac"], m2.inputs[1])
    gain = nt.nodes.new("ShaderNodeMath")
    gain.operation = "MULTIPLY"
    gain.inputs[1].default_value = ember * 8.0                   # v(1-v) peaks at 0.25, the noise averages 0.5
    nt.links.new(m2.outputs[0], gain.inputs[0])
    b.inputs["Emission Color"].default_value = (1.0, 0.2, 0.02, 1)
    nt.links.new(gain.outputs[0], b.inputs["Emission Strength"])
    return v.outputs[0]


LAYERS = (  # name, bottom, top, colour, label
    ("skin", 0.0, 0.07, SKIN_TONE, "SKIN"),
    ("fat", 0.07, 0.21, (0.95, 0.74, 0.22), "FAT"),
    ("muscle", 0.21, 0.42, (0.55, 0.06, 0.05), "MUSCLE"),
    ("bone", 0.42, 0.56, (0.95, 0.93, 0.88), "BONE"),
)
BLOCK_W, BLOCK_D = 0.44, 0.34


def tissue_block():
    """A magnified slice of you, skin side down on the lava: skin, fat, muscle, bone, each with its label."""
    root = bp.pivot("block", (AWAY, 0, 0))
    white = emit("label_white", (1.0, 1.0, 1.0), 1.6)
    ch = {}
    for name, z0, z1, col, label in LAYERS:
        m = bp.mat(f"tissue_{name}", col, rough=0.55 if name != "bone" else 0.4, sss=0.15 if name in ("skin", "fat") else 0.0)
        if name == "fat":
            bp.add_bump(m, 22.0, 0.9, distance=0.01)
        if name == "muscle":
            nt = m.node_tree
            wave = nt.nodes.new("ShaderNodeTexWave")                 # fibres running along the slice
            wave.inputs["Scale"].default_value, wave.inputs["Distortion"].default_value = 26.0, 1.2
            wave.bands_direction = "Z"
            tc = nt.nodes.new("ShaderNodeTexCoord")
            nt.links.new(tc.outputs["Object"], wave.inputs["Vector"])
            bump = nt.nodes.new("ShaderNodeBump")
            bump.inputs["Strength"].default_value, bump.inputs["Distance"].default_value = 0.8, 0.01
            nt.links.new(wave.outputs["Fac"], bump.inputs["Height"])
            nt.links.new(bump.outputs["Normal"], nt.nodes["Principled BSDF"].inputs["Normal"])
        if name == "bone":
            bp.add_bump(m, 60.0, 0.4, distance=0.003)
        ch[name] = charrable(m, 0.0, (0.2, 0.1, 0.06)) if name == "muscle" else charrable(m)   # muscle cooks brown, no glow
        bp.box(f"layer_{name}", (BLOCK_W, BLOCK_D, z1 - z0 - 0.004), (0, 0, (z0 + z1) / 2), m, root, bevel=0.012)
        zc = (z0 + z1) / 2
        t = bp.stencil(f"lab_{name}", label, (-BLOCK_W / 2 - 0.2, -BLOCK_D / 2, zc), 0.062, white, root)
        ts.no_light(t)
        ts.no_light(bp.box(f"lead_{name}", (0.05, 0.006, 0.007), (-BLOCK_W / 2 - 0.04, -BLOCK_D / 2, zc), white, root))
    O.update(block=root, tissue=ch)
    return root


def scene_lavayou(samples):
    sc = ts.scene_lava(samples)
    for o in list(bpy.data.objects):                             # no steel skeleton: this one is a person
        if o.name.startswith("b_"):
            bpy.data.objects.remove(o, do_unlink=True)
    humanise()
    tissue_block()
    O["steam"] = (0.92, 0.92, 0.95)
    O["drip"] = emit("fat_drip", (1.0, 0.6, 0.08), 3.0)
    return sc


def timeline_lavayou(sc, T):
    fr = [int(round(t * FPS)) for t in T["starts"]] + [T["frames"]]
    S = dict(zip(T["shots"], zip(fr[:-1], fr[1:])))
    end = T["frames"] + 2
    sc.render.motion_blur_position = "START"
    cam, P, rnd = bpy.data.objects["cam"], O["P"], O["rnd"]
    root, block, tis = P["root"], O["block"], O["tissue"]
    kval(O["lava_w"], 0, 0.0)
    kval(O["lava_w"], end, end / FPS * 0.22)
    linear(bpy.data.materials["lava"].node_tree)
    Z = ts.SEAT_Z
    loc = lambda f, x, zz, i="LINEAR": k(root, "location", f, Vector((x, 0, zz)), i)

    # 1 fall: frame 0 is you in the air right above it; you hit before the first sentence ends
    a, b = S["fall"]
    hit = 13
    shot(cam, a, b, (1.15, -3.7, 0.5), (0, -0.1, 1.75), (1.0, -3.4, 0.6), (0, -0.2, 0.55), lens=28)
    loc(0, 0, 1.25), loc(hit, 0, 0.3), loc(hit + 3, 0, -0.05), loc(hit + 7, 0, -0.12, "BEZIER")
    loc(hit + 22, 0, Z + 0.04, "BEZIER"), loc(hit + 30, 0, Z, "BEZIER")
    pose(P, 0, sh_1=(-160, -35, 0), sh1=(-95, 0, -50), el=(-35, 0, 0), hip_1=(-40, 0, 0), hip1=(10, 0, 0),
         kn_1=(70, 0, 0), kn1=(30, 0, 0), chest=(-8, 0, 8), head=(-18, 0, 0))
    pose(P, 7, sh_1=(-100, 0, -50), sh1=(-160, 35, 0), el=(-50, 0, 0), hip_1=(5, 0, 0), hip1=(-40, 0, 0),
         kn_1=(30, 0, 0), kn1=(70, 0, 0), chest=(6, 0, -8), head=(14, 0, 0))
    pose(P, hit, sh=(-150, -30, 0), el=(-25, 0, 0), hip=(-12, 0, 0), kn=(18, 0, 0), chest=(6, 0, 0), head=(18, 0, 0))
    pose(P, hit + 4, sh=(-125, -50, 0), el=(-40, 0, 0), hip=(-35, 0, 0), kn=(60, 0, 0), chest=(14, 0, 0), head=(-12, 0, 0))
    pose(P, hit + 12, sh=(-100, 0, -40), el=(-30, 0, 0), hip=(-70, 0, 0), kn=(95, 0, 0), chest=(4, 0, 0), head=(10, 0, 6))
    pose(P, hit + 24, sh=(-35, 30, 0), el=(-35, 0, 0), hip=(-88, 0, -8), kn=(26, 0, 0), chest=(-6, 0, 0), head=(14, 0, -8))
    pose(P, hit + 34, sh=(-22, 22, 0), el=(-48, 0, 0), hip=(-90, 0, -9), kn=(14, 0, 0), chest=(3, 0, 0), head=(4, 0, 6))
    splash("hit", (0, -0.05, 0.02), hit - 4, 40, rnd, O["blob"], life=30)
    splash("sit", (0, -0.1, 0.02), hit + 20, 16, rnd, O["blob"], speed=1.7, up=(1.0, 2.6), life=22)
    ts.embers(46, rnd, end)

    # 2 land: level with the surface -- you rest ON it, nothing goes under
    a, b = S["land"]
    shot(cam, a, b, (2.9, -1.5, 0.1), (0, -0.32, 0.36), (2.65, -1.2, 0.1), (0, -0.32, 0.36), lens=34)
    pose(P, a, sh=(-22, 22, 0), el=(-48, 0, 0), chest=(3, 0, 0), head=(4, 0, 14))
    pose(P, b - 4, sh=(-30, 26, 0), el=(-60, 0, 0), chest=(6, 0, 0), head=(16, 0, 0))
    for c in O["char"]:                                          # the figure's own skin, over the whole Short
        kval(c, a, 0.0), kval(c, S["steam"][0], 0.35), kval(c, S["steam"][1], 0.8), kval(c, S["timesup"][0], 1.0)

    def swap(a, b):                                              # the block is on screen from a to b, the figure waits
        loc(a - EPS, 0, Z), loc(a, AWAY, Z), loc(b - EPS, AWAY, Z), loc(b, 0, Z)
        for f, x in ((a - EPS, AWAY), (a, 0), (b - EPS, 0), (b, AWAY)):
            k(block, "location", f, Vector((x, 0, -0.012)), "LINEAR")
    k(block, "location", 0, Vector((AWAY, 0, -0.012)), "LINEAR")

    # 3 skin: the slice of you that touches the lava -- the bottom layer chars almost at once
    a, b = S["skin"]
    swap(a, b)
    shot(cam, a, b, (-0.13, -3.0, 0.4), (-0.13, 0, 0.05), (-0.13, -2.7, 0.4), (-0.13, 0, 0.04), lens=40)
    kval(tis["skin"], a + 8, 0.0), kval(tis["skin"], a + 26, 1.0)
    for j, f in enumerate((a + 16, a + 30, a + 44)):
        puffs(f"skinsmoke{j}", (rnd.uniform(-0.2, 0.2), -BLOCK_D / 2 - 0.02, 0.03), f, 3, rnd, (0.2, 0.18, 0.17),
              spread=0.3, rise=0.5, life=30, size=0.07, dense=0.45, ring=False)

    # 4 steam: back to you -- the water in you boils and bursts out as steam; you slump
    a, b = S["steam"]
    shot(cam, a, b, (-0.95, -2.7, 0.75), (0, -0.25, 0.5), (-0.8, -2.4, 0.72), (0, -0.2, 0.52), lens=32)
    pose(P, a, sh=(-30, 26, 0), el=(-60, 0, 0), chest=(6, 0, 0), head=(16, 0, 0))
    pose(P, a + 24, sh=(-14, 14, 0), el=(-24, 0, 0), chest=(16, 0, 4), head=(30, 0, 6))
    pose(P, b - 4, sh=(-8, 10, 0), el=(-12, 0, 0), chest=(22, 0, 6), head=(38, 0, 8))
    for j, f in enumerate(range(a + 4, b - 8, 7)):               # jets from the legs and seat, where you touch it
        at = (rnd.uniform(-0.25, 0.25), rnd.uniform(-0.8, 0.05), 0.12)
        puffs(f"steam{j}", at, f, 4, rnd, O["steam"], spread=0.5, rise=1.3, life=26, size=0.2, dense=0.55, glow=0.25,
              ring=False)
    legs = [(s * 0.1, y, 0.95, 0.07, 0.1, a + 10 + int(abs(y + 0.5) * 12)) for s in (-1, 1) for y in
            (-0.1, -0.34, -0.58, -0.82)]
    seat = [(x, 0.05, 0.97, 0.08, 0.12, a + 16) for x in (-0.16, 0.0, 0.16)]
    torso = [(x, y, zz, 0.085, 0.13, S["fat"][1] + int((zz - 1.05) * 40)) for x, y in
             ((-0.22, -0.04), (0.22, -0.04), (0.0, 0.13)) for zz in (1.08, 1.3)]
    back = [(0.0, 0.16, 1.12, 0.17, 0.3, S["fat"][1]), (0.0, -0.5, 0.93, 0.13, 0.17, a + 14)]
    flames(root, back + legs + seat + torso, end, rnd)
    fire = O["fire"]
    fire.parent = root
    fire.location = (0, -0.5, 1.5)
    for f in range(a, end, 3):
        k(fire.data, "energy", f, min(1.0, (f - a) / 30) * rnd.uniform(30, 60), "LINEAR")

    # 5 fat: closer on the slice -- the fat melts, runs and burns
    a, b = S["fat"]
    swap(a, S["bone"][1])                                        # one stay for both block shots
    shot(cam, a, b, (-0.75, -2.6, 0.4), (-0.13, 0, 0.04), (-0.6, -2.5, 0.4), (-0.13, 0, 0.04), lens=40)
    kval(tis["fat"], a + 4, 0.0), kval(tis["fat"], b, 0.5)
    for j in range(9):                                           # drips of melted fat run down to the lava
        f0 = a + 8 + j * 6
        x = rnd.uniform(-BLOCK_W / 2 + 0.05, BLOCK_W / 2 - 0.05)
        o = ts.no_light(bp.ellipsoid(f"drip{j}", (0.012, 0.012, 0.022), (x, -BLOCK_D / 2 - 0.006, 0.12), O["drip"]))
        k(o, "location", f0, (x, -BLOCK_D / 2 - 0.006, rnd.uniform(0.08, 0.16)), "LINEAR")
        k(o, "location", f0 + 12, (x, -BLOCK_D / 2 - 0.006, 0.0), "LINEAR")
        shown(o, f0, f0 + 12)
    bf = [(x, -BLOCK_D / 2 - 0.02, 0.04, 0.05, 0.11, a + 10 + j * 5) for j, x in enumerate((-0.22, -0.05, 0.12, 0.26))]
    bf += [(s * (BLOCK_W / 2 + 0.02), y, 0.05, 0.05, 0.12, a + 14) for s in (-1, 1) for y in (-0.1, 0.1)]
    flames(block, bf, S["bone"][1], rnd)

    # 6 bone: the muscle cooks from below, the bone on top has not changed at all
    a, b = S["bone"]
    shot(cam, a, b, (0.35, -2.75, 0.62), (-0.13, 0, 0.13), (0.25, -2.55, 0.6), (-0.13, 0, 0.13), lens=40)
    kval(tis["fat"], b, 0.8)
    kval(tis["muscle"], a, 0.0), kval(tis["muscle"], b, 0.75)

    # 7 time's up: wide -- a burning figure sitting on top of the lava, not sunk and not melted
    a, b = S["timesup"]
    shot(cam, a, b, (0.42, -2.9, 0.95), (0, -0.15, 0.5), (0.36, -2.55, 0.86), (0, -0.15, 0.5), lens=28)
    pose(P, a, sh=(-8, 10, 0), el=(-12, 0, 0), chest=(22, 0, 6), head=(38, 0, 8))
    pose(P, b - 4, chest=(26, 0, 6), head=(42, 0, 8))

    # 8 end: pull back
    a, b = S["end"]
    shot(cam, a, b, (0.5, -2.9, 0.9), (0, -0.1, 0.5), (0.8, -4.2, 1.3), (0, -0.05, 0.5), lens=28)
    pose(P, a, chest=(26, 0, 6), head=(42, 0, 8))


# ── oxygen: "What If the Oxygen Vanished for 5 Seconds?" ──────────────────────
O2_BLUE = (0.08, 0.42, 1.0)
LUNG = Vector((AWAY, 0.0, 1.0))        # the inside-your-lungs diagram stands here, far from the campfire
CELL_GAP, CELL_V = 0.21, 0.2           # red blood cells: spacing (m) and speed (m/s) along the vessel
POOR, RICH, WORSE = (0.3, 0.015, 0.05), (1.0, 0.05, 0.03), (0.07, 0.03, 0.22)


def night_ground(rnd):
    g = bp.add_bump(bp.mat("grass", (0.035, 0.06, 0.03), rough=0.9), 14.0, 0.8, distance=0.03)
    bp.box("ground", (160, 160, 0.2), (0, 0, -0.13), g)
    dark = bp.mat("bush", (0.012, 0.022, 0.014), rough=0.95)
    for j in range(14):                                          # a treeline, far behind
        a = math.radians(20 + 140 * j / 13) + rnd.uniform(-0.05, 0.05)
        d = rnd.uniform(11, 17)
        bp.lumpy(f"tree{j}", rnd.uniform(2.2, 4.2), (d * math.cos(a), d * math.sin(a), rnd.uniform(0.5, 1.6)), dark,
                 seed=20 + j, amp=0.3)
    star = emit("star", (0.9, 0.95, 1.0), 3.0)
    for j in range(70):
        a, e = math.radians(rnd.uniform(20, 160)), math.radians(rnd.uniform(14, 60))
        no_light(bp.ellipsoid(f"star{j}", (0.05,) * 3, (60 * math.cos(a) * math.cos(e), 60 * math.sin(a) * math.cos(e),
                                                       60 * math.sin(e)), star, segs=6, rings=4))


def molecules(n, rnd, box, prefix="o2", r=0.017):
    """Oxygen, drawn so it can be seen to vanish: pairs of small blue lights drifting in the air."""
    m = O.get("o2_mat") or emit("o2", O2_BLUE, 5.0)
    O["o2_mat"] = m
    out = []
    for j in range(n):
        p = bp.pivot(f"{prefix}{j}", tuple(rnd.uniform(lo, hi) for lo, hi in box))
        p.rotation_euler = (rnd.uniform(0, 3), rnd.uniform(0, 3), rnd.uniform(0, 3))
        for s in (-1, 1):
            no_light(bp.ellipsoid(f"{prefix}{j}_{s}", (r, r, r), (s * r * 0.85, 0, 0), m, p, segs=10, rings=6))
        out.append(p)
    return out


def lung_diagram(rnd):
    """One air sac of the lung against the blood vessel that wraps it, as a flat labelled cutaway."""
    root = bp.pivot("lung", tuple(LUNG))
    bp.box("lung_back", (5, 0.1, 4), (0, 0.5, 0.2), bp.mat("lung_back", (0.05, 0.012, 0.02), rough=0.9), root)
    sac_m = bp.add_bump(bp.mat("air_sac", (0.95, 0.66, 0.64), rough=0.6, sss=0.2), 30.0, 0.3, distance=0.004)
    bp.ellipsoid("sac", (0.37, 0.07, 0.27), (0, 0, 0.36), sac_m, root)
    bp.ellipsoid("sac_in", (0.33, 0.07, 0.235), (0, -0.012, 0.36),
                 bp.mat("air_in", (0.42, 0.2, 0.24), rough=0.8), root)   # the hollow where the air is
    wall = bp.mat("vessel", (0.5, 0.1, 0.1), rough=0.5, sss=0.1)
    bp.box("vessel", (3.0, 0.06, 0.17), (0, 0, -0.03), wall, root, bevel=0.03)
    bp.box("vessel_in", (3.0, 0.06, 0.125), (0, -0.012, -0.03), bp.mat("plasma", (0.2, 0.03, 0.04), rough=0.6), root)
    white, ink = emit("lung_white", (1.0, 1.0, 1.0), 1.6), emit("lung_blue", O2_BLUE, 3.0)
    for name, text, at, size, m in (("sac", "AIR SAC", (0, -0.1, 0.52), 0.07, white),
                                    ("blood", "BLOOD", (0.3, -0.05, -0.2), 0.06, white),
                                    ("oxy", "OXYGEN", (-0.24, -0.05, -0.2), 0.06, ink)):
        ts.no_light(bp.stencil(f"lunglab_{name}", text, at, size, m, root))
    for s in (-1, 1):
        no_light(bp.ellipsoid(f"legend{s}", (0.017,) * 3, (-0.385 + s * 0.015, -0.05, -0.2), O["o2_mat"], root, segs=10,
                              rings=6))
    bp.light("lung_key", "AREA", (LUNG.x - 0.8, -2.6, 2.0), 110, size=2.5, aim=(LUNG.x, 0, 1.1))
    O["lung"] = root
    return root


def scene_oxygen(samples):
    rnd = random.Random(8)
    sc = bk_scene(samples, (0.006, 0.012, 0.035))
    night_ground(rnd)
    bp.light("moon", "AREA", (-3.0, -4.0, 4.5), 420, size=4.0, color=(0.62, 0.74, 1.0), aim=(0, 0, 0.9))
    bp.light("rim", "AREA", (2.5, 3.5, 3.0), 260, size=2.5, color=(0.5, 0.65, 1.0), aim=(0, 0, 1.0))
    P = bp.build_dummy_v2(at=(0, 0, 0), yaw=math.radians(-14), label="")
    humanise()
    # the campfire, to his left (screen right), out of the opening frame
    fx, fy = 1.75, -0.25
    camp = bp.pivot("camp", (fx, fy, -0.03))
    wood = bp.add_bump(bp.mat("log", (0.1, 0.05, 0.025), rough=0.9), 20.0, 0.8, distance=0.01)
    for j in range(5):
        a = j * math.radians(72)
        bp.cylinder(f"log{j}", 0.045, 0.62, (0.1 * math.cos(a), 0.1 * math.sin(a), 0.1), wood, camp,
                    rot=(math.radians(72), 0, a + math.radians(90)), segs=14)
    stone = bp.mat("stone", (0.12, 0.12, 0.13), rough=0.85)
    for j in range(9):
        a = j * math.radians(40)
        bp.lumpy(f"stone{j}", rnd.uniform(0.07, 0.1), (0.42 * math.cos(a), 0.42 * math.sin(a), 0.03), stone, camp,
                 seed=90 + j, amp=0.25)
    fire = bp.light("fire", "POINT", (fx, fy, 0.5), 260.0, color=(1.0, 0.5, 0.14))
    fire.data.shadow_soft_size = 0.3
    O.update(P=P, rnd=rnd, camp=camp, fire=fire)
    O["air"] = molecules(90, rnd, ((-1.5, 1.5), (-2.6, 1.6), (0.15, 2.5)))
    lung_diagram(rnd)
    cam = bp.cam_free(sc, 28, (-0.5, -4.6, 1.0), (0, 0, 0.7))
    cam.data.dof.use_dof = False
    return sc


def bk_scene(samples, sky):
    import blender_kit as bk
    sc = bk.new_scene(fps=FPS, res=ts.RES, samples=samples, frames=49)
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.4
    sc.cycles.max_bounces, sc.cycles.diffuse_bounces, sc.cycles.glossy_bounces = 3, 1, 2
    sc.cycles.transparent_max_bounces = 8
    sc.cycles.adaptive_min_samples = 4
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    O["world"] = bp.world(sc, sky, 1.0)
    return sc


def timeline_oxygen(sc, T):
    fr = [int(round(t * FPS)) for t in T["starts"]] + [T["frames"]]
    S = dict(zip(T["shots"], zip(fr[:-1], fr[1:])))
    end = T["frames"] + 2
    sc.render.motion_blur_position = "START"
    cam, P, rnd = bpy.data.objects["cam"], O["P"], O["rnd"]
    root, L = P["root"], LUNG
    loc = lambda f, zz, i="BEZIER": k(root, "location", f, Vector((0, 0, zz)), i)
    loc(0, 0.0)
    back = S["timesup"][0] + 10

    # the oxygen in the air: there at frame 0, gone within the first second, back when time is up
    for j, p in enumerate(O["air"]):
        p0 = Vector(p.location)
        k(p, "location", 0, tuple(p0), "LINEAR")
        k(p, "location", end, tuple(p0 + Vector((rnd.uniform(-0.5, 0.5), rnd.uniform(-0.5, 0.5), rnd.uniform(-0.2, 0.4)))),
          "LINEAR")
        f0, f1 = 9 + int(rnd.uniform(0, 9)), back + int(rnd.uniform(0, 12))
        for f, s in ((0, 1.0), (f0, 1.0), (f0 + 2, 1.6), (f0 + 4, 0.0), (f1, 0.0), (f1 + 3, 1.5), (f1 + 6, 1.0)):
            k(p, "scale", f, (s, s, s), "LINEAR")

    # 1 gone: you, in the firelight; the blue lights around you blink out
    a, b = S["gone"]
    shot(cam, a, b, (-0.5, -4.7, 1.0), (0, 0, 0.62), (-0.42, -4.2, 1.0), (0, 0, 0.66), lens=28)
    pose(P, 0, sh=(-6, 8, 0), el=(-12, 0, 0), head=(0, 0, 0), chest=(0, 0, 0))
    pose(P, 12, sh=(-6, 8, 0), el=(-12, 0, 0), head=(-8, 0, 12))
    pose(P, 30, sh=(-30, 14, 0), el=(-60, 0, 0), head=(-14, 0, -16), chest=(-4, 0, -4))
    pose(P, 60, sh_1=(-62, 0, 14), sh1=(-20, -10, 0), el_1=(-128, 0, 0), el1=(-30, 0, 0), head=(6, 0, 10), chest=(4, 0, 0))
    pose(P, b - 4, sh_1=(-64, 0, 14), sh1=(-24, -10, 0), el_1=(-130, 0, 0), el1=(-36, 0, 0), head=(10, 0, -4), chest=(6, 0, 0))

    # 2 ears: close on the head -- both hands go to the ears
    a, b = S["ears"]
    shot(cam, a, b, (-0.55, -2.3, 1.55), (0, 0, 1.33), (-0.45, -2.05, 1.55), (0, 0, 1.33), lens=36)
    pose(P, a, sh_1=(-64, 0, 14), sh1=(-24, -10, 0), el_1=(-130, 0, 0), el1=(-36, 0, 0), head=(10, 0, -4), chest=(6, 0, 0))
    pose(P, a + 26, sh=(-58, -26, 0), el=(-142, 0, 0), head=(14, 0, 0), chest=(8, 0, 0))
    pose(P, a + 60, sh=(-60, -28, 0), el=(-144, 0, 0), head=(18, 0, 10), chest=(10, 0, 0))
    pose(P, b - 4, sh=(-58, -26, 0), el=(-142, 0, 0), head=(16, 0, -10), chest=(10, 0, 0))

    # 3 fire: the campfire beside you shrinks and dies; smoke
    a, b = S["fire"]
    fx, fy = O["camp"].location.x, O["camp"].location.y
    die = a + 18
    shot(cam, a, b, (fx - 0.5, fy - 2.9, 0.75), (fx - 0.05, fy, 0.3), (fx - 0.42, fy - 2.6, 0.72), (fx - 0.05, fy, 0.3),
         lens=32)
    spots = [(0, 0, 0.1, 0.1, 0.4, 0), (0.1, 0.04, 0.08, 0.07, 0.3, 0), (-0.09, -0.05, 0.08, 0.07, 0.32, 0),
             (0.0, 0.1, 0.08, 0.06, 0.26, 0), (0.03, -0.1, 0.08, 0.06, 0.24, 0)]
    for o in flames(O["camp"], spots, die, rnd):
        s = tuple(o.scale)
        k(o, "scale", die + 2, s, "LINEAR"), k(o, "scale", die + 16, (0.001, 0.001, 0.001), "LINEAR")
    fire = O["fire"]
    for f in range(0, die, 3):
        k(fire.data, "energy", f, rnd.uniform(200, 300), "LINEAR")
    k(fire.data, "energy", die, 240.0, "LINEAR"), k(fire.data, "energy", die + 16, 0.0, "LINEAR")
    glow = emit("coal", (1.0, 0.25, 0.03), 3.0)                  # the logs still glow for a moment, then that goes too
    coal = no_light(bp.ellipsoid("coals", (0.16, 0.16, 0.05), (0, 0, 0.07), glow, O["camp"]))
    e = glow.node_tree.nodes["Emission"].inputs["Strength"]
    kval(e, 0, 3.0), kval(e, die + 10, 3.0), kval(e, die + 50, 0.0)
    for j, f in enumerate(range(die + 8, b + 40, 12)):
        puffs(f"smoke{j}", (fx + rnd.uniform(-0.08, 0.08), fy, 0.25), f, 3, rnd, (0.5, 0.5, 0.52), spread=0.35,
              rise=1.5, life=48, size=0.2, dense=0.5, glow=0.12, ring=False)
    pose(P, a, sh=(-58, -26, 0), el=(-142, 0, 0), head=(16, 0, -10), chest=(10, 0, 0))
    pose(P, a + 30, sh=(-10, 10, 0), el=(-30, 0, 0), head=(4, 0, -40), chest=(2, 0, -14))

    # 4 lung / 5 back: one air sac and its blood vessel. Normally oxygen goes down into the blood; now it comes out
    a, b = S["lung"]
    a2, b2 = S["back"]
    shot(cam, a, b, (L.x, -3.1, L.z + 0.1), (L.x, 0, L.z + 0.08), (L.x, -2.9, L.z + 0.1), (L.x, 0, L.z + 0.08), lens=40)
    shot(cam, a2, b2, (L.x, -2.9, L.z + 0.1), (L.x, 0, L.z + 0.08), (L.x, -2.75, L.z + 0.1), (L.x, 0, L.z + 0.08), lens=40)
    lung = O["lung"]
    sac_air = molecules(16, rnd, ((-0.24, 0.24), (-0.1, -0.09), (0.2, 0.44)), prefix="sacO", r=0.015)
    for j, p in enumerate(sac_air):
        p.parent = lung
        p0 = Vector(p.location)
        for f in range(a - 2, a2 + 20, 16):
            k(p, "location", f, tuple(p0 + Vector((rnd.uniform(-0.05, 0.05), 0, rnd.uniform(-0.04, 0.04)))), "LINEAR")
        f0 = a2 + 3 + int(rnd.uniform(0, 8))
        for f, s in ((0, 1.0), (f0, 1.0), (f0 + 2, 1.6), (f0 + 4, 0.0)):
            k(p, "scale", f, (s, s, s), "LINEAR")
    span = (b2 - a) / FPS * CELL_V
    n = int((1.5 + span) / CELL_GAP) + 2
    step = CELL_V / FPS
    for j in range(n):
        m = bp.mat(f"cell{j}", POOR, rough=0.35, sss=0.1)
        col = m.node_tree.nodes["Principled BSDF"].inputs["Base Color"]
        x0 = 0.75 - CELL_GAP * j
        o = bp.ellipsoid(f"cell{j}", (0.052, 0.022, 0.052), (x0, -0.05, -0.03), m, lung, segs=24, rings=12)
        k(o, "location", a, (x0, -0.05, -0.03), "LINEAR")
        k(o, "location", b2, (x0 + span, -0.05, -0.03), "LINEAR")
        k(o, "rotation_euler", a, (0, rnd.uniform(0, 3), 0), "LINEAR")
        k(o, "rotation_euler", b2, (0, rnd.uniform(3, 7), 0), "LINEAR")
        fc = a + (0.0 - x0) / step                               # the frame this cell passes under the air sac
        if fc < a2 - 4:                                          # normal: it arrives dark and leaves bright red
            c0, c1 = (POOR, RICH) if fc > a else (RICH, RICH)
            col.default_value = (*c0, 1)
            col.keyframe_insert("default_value", frame=max(a, int(fc) - 6))
            col.default_value = (*c1, 1)
            col.keyframe_insert("default_value", frame=max(a, int(fc) + 4))
            if fc > a:
                for q in range(2):
                    d = no_light(bp.ellipsoid(f"in{j}_{q}", (0.016,) * 3, (0, 0, 0), O["o2_mat"], lung, segs=10, rings=6))
                    f0 = int(fc) - 12 + q * 3
                    xs = rnd.uniform(-0.12, 0.12)
                    k(d, "location", f0, (xs, -0.09, rnd.uniform(0.2, 0.34)), "LINEAR")
                    k(d, "location", f0 + 12, (x0 + (f0 + 12 - a) * step, -0.08, -0.03), "LINEAR")
                    shown(d, max(a, f0), f0 + 12)
            if x0 + (a2 - a) * step < 0.75:                      # still on screen in the next shot: it stays as it left
                col.default_value = (*c1, 1)
                col.keyframe_insert("default_value", frame=a2)
        else:                                                    # reversed: it arrives poor and leaves with even less
            col.default_value = (*POOR, 1)
            col.keyframe_insert("default_value", frame=max(a, int(fc) - 6))
            col.default_value = (*WORSE, 1)
            col.keyframe_insert("default_value", frame=int(fc) + 6)
            for q in range(2):
                d = no_light(bp.ellipsoid(f"out{j}_{q}", (0.016,) * 3, (0, 0, 0), O["o2_mat"], lung, segs=10, rings=6))
                f0 = int(fc) - 3 + q * 4
                xs = x0 + (f0 - a) * step
                k(d, "location", f0, (xs, -0.08, -0.03), "LINEAR")
                k(d, "location", f0 + 14, (xs + rnd.uniform(-0.1, 0.1), -0.09, rnd.uniform(0.3, 0.45)), "LINEAR")
                k(d, "scale", f0 + 14, (1, 1, 1), "LINEAR"), k(d, "scale", f0 + 20, (0, 0, 0), "LINEAR")
                k(d, "location", f0 + 20, (xs, -0.09, 0.62), "LINEAR")
                shown(d, max(a2, f0), f0 + 20)

    # 6 faint: back to you -- you sway, your knees go, you fold
    a, b = S["faint"]
    shot(cam, a, b, (0.7, -4.3, 0.8), (0, -0.1, 0.5), (0.6, -3.9, 0.75), (0, -0.15, 0.42), lens=28)
    pose(P, a, sh=(-10, 10, 0), el=(-30, 0, 0), head=(8, 0, 6), chest=(4, 0, 4), hip=(0, 0, 0), kn=(0, 0, 0))
    loc(a, 0.0)
    pose(P, a + 22, sh=(-6, 12, 0), el=(-14, 0, 0), head=(22, 0, -10), chest=(8, 0, -6), hip=(-4, 0, 0), kn=(8, 0, 0))
    loc(a + 22, -0.01)
    pose(P, a + 40, sh=(-12, 14, 0), el=(-10, 0, 0), head=(30, 0, -6), chest=(10, 0, 0), hip=(-22, 0, 0), kn=(70, 0, 0))
    loc(a + 40, -0.2)
    pose(P, a + 50, sh=(-8, 12, 0), el=(-8, 0, 0), head=(34, 0, 0), chest=(12, 0, 0), hip=(-6, 0, 0), kn=(92, 0, 0))
    loc(a + 50, -0.4)
    pose(P, a + 72, sh=(-4, 10, 0), el=(-6, 0, 0), head=(44, 0, 6), chest=(34, 0, 4), hip=(-34, 0, 0), kn=(118, 0, 0))
    loc(a + 72, -0.44)
    pose(P, b - 2, sh=(-4, 10, 0), el=(-6, 0, 0), head=(46, 0, 6), chest=(38, 0, 4), hip=(-36, 0, 0), kn=(120, 0, 0))
    puffs("kneel", (0, -0.1, 0.0), a + 49, 6, rnd, (0.25, 0.25, 0.2), spread=0.6, rise=0.15, life=30, size=0.16, dense=0.4)

    # 7 time's up: the blue lights pop back; your head comes up and you drag in a breath
    a, b = S["timesup"]
    shot(cam, a, b, (2.7, -3.3, 0.8), (0, -0.05, 0.4), (2.5, -3.0, 0.8), (0, -0.05, 0.45), lens=28)
    pose(P, a, sh=(-4, 10, 0), el=(-6, 0, 0), head=(46, 0, 6), chest=(38, 0, 4), hip=(-36, 0, 0), kn=(120, 0, 0))
    pose(P, a + 20, sh=(-4, 10, 0), el=(-6, 0, 0), head=(46, 0, 6), chest=(38, 0, 4))
    pose(P, a + 40, sh=(10, 26, 0), el=(-20, 0, 0), head=(-26, 0, 0), chest=(-8, 0, 0), hip=(-8, 0, 0), kn=(94, 0, 0))
    loc(a + 20, -0.44), loc(a + 40, -0.4)
    pose(P, a + 64, sh=(0, 16, 0), el=(-24, 0, 0), head=(-6, 0, 0), chest=(8, 0, 0))
    pose(P, a + 88, sh=(6, 22, 0), el=(-22, 0, 0), head=(-20, 0, 0), chest=(-4, 0, 0))
    pose(P, b - 2, sh=(0, 16, 0), el=(-24, 0, 0), head=(-4, 0, 6), chest=(8, 0, 0))

    # 8 end: pull back; you are on your knees, breathing, under the lights
    a, b = S["end"]
    shot(cam, a, b, (2.5, -3.0, 0.8), (0, -0.05, 0.45), (3.4, -4.4, 1.3), (0, 0, 0.55), lens=28)
    pose(P, a, sh=(0, 16, 0), el=(-24, 0, 0), head=(-4, 0, 6), chest=(8, 0, 0))
    pose(P, a + 30, sh=(4, 20, 0), el=(-22, 0, 0), head=(-16, 0, 0), chest=(-2, 0, 0))
    pose(P, a + 60, sh=(0, 16, 0), el=(-24, 0, 0), head=(-2, 0, -6), chest=(8, 0, 0))
    pose(P, b, sh=(4, 20, 0), el=(-22, 0, 0), head=(-14, 0, 0), chest=(0, 0, 0))


# ── gravity: "What If Gravity Stopped for 5 Seconds?" ─────────────────────────
GLOBE = Vector((-AWAY, 0.0, 1.0))      # the spinning-Earth diagram
EAR = Vector((AWAY, 0.0, 0.0))         # the inside-your-ear diagram
GLOBE_R = 0.55


def day_street(rnd):
    road = bp.add_bump(bp.mat("road", (0.2, 0.2, 0.21), rough=0.85), 60.0, 0.5, distance=0.004)
    bp.box("ground", (160, 160, 0.2), (0, 0, -0.13), road)
    bp.box("pavement", (160, 6, 0.12), (0, 5.4, -0.02), bp.mat("pave", (0.55, 0.53, 0.5), rough=0.8))
    for j in range(9):                                           # painted dashes down the middle of the road
        bp.box(f"dash{j}", (1.0, 0.12, 0.004), (-8 + j * 2.0, 1.3, -0.027), bp.mat(f"paint{j}", (0.85, 0.85, 0.8), rough=0.6))
    cols = ((0.75, 0.55, 0.42), (0.62, 0.66, 0.72), (0.8, 0.74, 0.6), (0.55, 0.45, 0.42), (0.7, 0.7, 0.66))
    x = -17.0
    j = 0
    while x < 17:                                                # a row of plain buildings across the street
        w, h = rnd.uniform(3.0, 5.0), rnd.uniform(5.0, 11.0)
        m = bp.mat(f"wall{j}", cols[j % len(cols)], rough=0.8)
        bp.box(f"house{j}", (w, 4, h), (x + w / 2, 10.5, h / 2), m)
        glass = bp.mat(f"glass{j}", (0.12, 0.2, 0.3), rough=0.15)
        for fl in range(int(h // 1.6)):
            for q in range(int(w // 1.1)):
                bp.box(f"win{j}_{fl}_{q}", (0.6, 0.05, 0.8), (x + 0.75 + q * 1.1, 8.49, 1.4 + fl * 1.6), glass)
        x += w + rnd.uniform(0.0, 0.5)
        j += 1
    leaf = bp.mat("leaf", (0.12, 0.3, 0.08), rough=0.9)
    bark = bp.mat("bark", (0.16, 0.1, 0.06), rough=0.9)
    for j, tx in enumerate((-5.5, 4.6)):
        bp.cylinder(f"trunk{j}", 0.16, 2.4, (tx, 4.2, 1.2), bark)
        bp.lumpy(f"crown{j}", 1.5, (tx, 4.2, 3.2), leaf, seed=60 + j, amp=0.3)
    steel = bp.mat("post", (0.25, 0.27, 0.3), rough=0.4, metallic=0.8)
    bp.cylinder("lamp_post", 0.05, 4.0, (2.4, 3.2, 2.0), steel)
    bp.box("lamp_arm", (0.9, 0.06, 0.06), (2.0, 3.2, 3.97), steel)


def loose_things(rnd):
    """Everything that is not bolted down: (object, rest position, how far it tumbles)."""
    out = []
    ball = bp.ellipsoid("ball", (0.11,) * 3, (0, 0, 0), bp.mat("ball", (0.9, 0.12, 0.08), rough=0.4))
    out.append((ball, Vector((-0.75, -0.55, 0.085)), 1.2))
    cone_m = bp.mat("cone", (1.0, 0.35, 0.02), rough=0.5)
    cone = bp.pivot("cone", (0, 0, 0))
    bm_cone = bp.cylinder("cone_body", 0.11, 0.42, (0, 0, 0.21), cone_m, cone, segs=24)
    for v in bm_cone.data.vertices:                              # taper it
        if v.co.z > 0:
            v.co.x *= 0.25
            v.co.y *= 0.25
    bp.box("cone_base", (0.3, 0.3, 0.03), (0, 0, 0.0), cone_m, cone)
    bp.cylinder("cone_band", 0.075, 0.07, (0, 0, 0.24), bp.mat("band", (0.95, 0.95, 0.95), rough=0.4), cone, segs=24)
    out.append((cone, Vector((0.95, 0.35, -0.01)), 0.5))
    crate = bp.box("crate", (0.34, 0.34, 0.3), (0, 0, 0), bp.add_bump(bp.mat("crate", (0.5, 0.33, 0.16), rough=0.8), 30, 0.6),
                   bevel=0.012)
    out.append((crate, Vector((-1.25, 0.75, 0.125)), 0.4))
    can = bp.cylinder("can", 0.035, 0.12, (0, 0, 0), bp.mat("can", (0.1, 0.5, 0.9), rough=0.25, metallic=0.9), segs=20)
    out.append((can, Vector((0.5, -0.8, 0.035)), 2.5))
    grit = bp.mat("grit", (0.4, 0.38, 0.35), rough=0.9)
    for j in range(16):
        o = bp.lumpy(f"pebble{j}", rnd.uniform(0.012, 0.03), (0, 0, 0), grit, seed=120 + j, amp=0.3)
        out.append((o, Vector((rnd.uniform(-1.6, 1.6), rnd.uniform(-1.3, 1.2), -0.015)), 3.0))
    lf = bp.mat("dry_leaf", (0.6, 0.35, 0.08), rough=0.8)
    for j in range(10):
        o = bp.ellipsoid(f"leaf{j}", (0.045, 0.028, 0.003), (0, 0, 0), lf, segs=12, rings=6)
        out.append((o, Vector((rnd.uniform(-1.5, 1.5), rnd.uniform(-1.2, 1.4), -0.025)), 3.5))
    water = bp.mat("water", (0.15, 0.4, 0.7), rough=0.05, coat=0.5)
    bp.cylinder("puddle", 0.34, 0.004, (0.72, -0.5, -0.027), water).scale = (1.0, 0.7, 1.0)
    for j in range(9):
        o = bp.lumpy(f"drop{j}", rnd.uniform(0.02, 0.05), (0, 0, 0), water, seed=160 + j, amp=0.25)
        out.append((o, Vector((0.72 + rnd.uniform(-0.25, 0.25), -0.5 + rnd.uniform(-0.16, 0.16), -0.01)), 1.5))
    return out


def ruler():
    """A marked post beside you so the forty centimetres can be read off."""
    root = bp.pivot("ruler", (0.5, 0.12, -0.03))
    bp.box("ruler_post", (0.07, 0.03, 0.9), (0, 0, 0.45), bp.mat("ruler", (0.95, 0.95, 0.92), rough=0.5), root)
    red = bp.mat("tick", (0.85, 0.05, 0.04), rough=0.5)
    for j in range(1, 9):
        bp.box(f"tick{j}", (0.07 if j % 2 == 0 else 0.04, 0.032, 0.012), (0, 0, j * 0.1), red, root)
    ink = emit("ruler_ink", (1.0, 1.0, 1.0), 1.3)
    ts.no_light(bp.stencil("ruler40", "40 CM", (0.2, -0.02, 0.4), 0.085, ink, root))
    ts.no_light(bp.box("ruler40_lead", (0.06, 0.006, 0.008), (0.07, -0.02, 0.4), ink, root))
    return root


def globe_diagram(rnd):
    """Looking down on the north pole: the ground turns with the Earth, you carry straight on."""
    root = bp.pivot("globe", tuple(GLOBE))
    bp.box("globe_back", (6, 0.1, 5), (0, 1.4, 0.3), bp.mat("space", (0.004, 0.006, 0.015), rough=1.0), root)
    m = bp.mat("earth", (0.05, 0.2, 0.55), rough=0.5)
    nt = m.node_tree
    tex = nt.nodes.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value, tex.inputs["Detail"].default_value = 2.6, 6.0
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(tc.outputs["Object"], tex.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "CONSTANT"
    ramp.color_ramp.elements[0].color = (0.03, 0.16, 0.5, 1)
    ramp.color_ramp.elements[1].position = 0.53
    ramp.color_ramp.elements[1].color = (0.1, 0.3, 0.09, 1)
    nt.links.new(tex.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    spin = bp.pivot("globe_spin", (0, 0, 0.18 - GLOBE_R), root)
    bp.ellipsoid("earth", (GLOBE_R,) * 3, (0, 0, 0), m, spin, segs=96, rings=48)
    pin = emit("pin", (1.0, 0.1, 0.05), 3.0)
    no_light(bp.box("pin", (0.014, 0.014, 0.07), (0, -GLOBE_R * 0.12, GLOBE_R * 0.993 + 0.03), pin, spin))   # where you stood
    you = emit("you", (1.0, 0.9, 0.2), 3.0)
    me = bp.pivot("globe_you", (0, -GLOBE_R * 0.12, 0.18 - GLOBE_R + GLOBE_R * 0.993), root)
    no_light(bp.ellipsoid("you_body", (0.016, 0.016, 0.035), (0, 0, 0.035), you, me, segs=12, rings=8))
    no_light(bp.ellipsoid("you_head", (0.015,) * 3, (0, 0, 0.085), you, me, segs=12, rings=8))
    white = emit("globe_white", (1.0, 1.0, 1.0), 1.5)
    path = no_light(bp.box("you_path", (1.0, 0.006, 0.006), (0.5, -GLOBE_R * 0.12, 0.18 - GLOBE_R + GLOBE_R * 0.993 + 0.035),
                           white, root))
    ts.no_light(bp.stencil("lab_you", "YOU", (0, -0.02, 0.15), 0.05, you, me))
    ts.no_light(bp.stencil("lab_scale", "NOT TO SCALE", (-0.08, -GLOBE_R - 0.02, 0.52), 0.04, white, root))
    bp.light("globe_key", "AREA", (GLOBE.x - 1.5, -3.0, 2.6), 160, size=2.5, aim=(GLOBE.x, 0, 0.6))
    O.update(globe=root, spin=spin, gyou=me, gpath=path)


def ear_diagram(rnd):
    """The gravity sensor of the inner ear: sensor hairs under a gel, weighed down by crystals."""
    root = bp.pivot("ear", tuple(EAR))
    bp.box("ear_back", (5, 0.1, 4), (0, 0.6, 0.5), bp.mat("ear_back", (0.03, 0.02, 0.05), rough=0.9), root)
    W_, D_ = BLOCK_W, BLOCK_D
    bp.box("ear_pad", (W_, D_, 0.07), (0, 0, 0.035), bp.mat("ear_pad", (0.85, 0.5, 0.5), rough=0.6, sss=0.15), root, bevel=0.012)
    hair_m = bp.mat("ear_hair", (0.95, 0.8, 0.35), rough=0.4)
    hairs = []
    for j in range(11):
        h = bp.pivot(f"hair{j}", (-W_ / 2 + 0.03 + j * (W_ - 0.06) / 10, -D_ / 2 + 0.01, 0.07), root)
        bp.cylinder(f"hair{j}_c", 0.007, 0.1, (0, 0, 0.05), hair_m, h, segs=10)
        hairs.append(h)
    gel = bp.mat("ear_gel", (0.45, 0.75, 0.85), rough=0.2, sss=0.3, coat=0.4)
    g = bp.box("ear_gel", (W_, D_ - 0.03, 0.09), (0, 0.015, 0.215), gel, root, bevel=0.02)
    rock = bp.mat("ear_rock", (0.97, 0.96, 0.92), rough=0.35)
    rocks = []
    for j in range(26):
        x = -W_ / 2 + 0.03 + (j % 13) * (W_ - 0.06) / 12 + rnd.uniform(-0.008, 0.008)
        y = -D_ / 2 + 0.03 + (j // 13) * 0.06 + rnd.uniform(-0.01, 0.01)
        o = bp.lumpy(f"rock{j}", rnd.uniform(0.014, 0.022), (x, y, 0.275), rock, root, seed=200 + j, amp=0.35)
        rocks.append(o)
    white = emit("ear_white", (1.0, 1.0, 1.0), 1.6)
    for name, text, z in (("rock", "CRYSTALS", 0.28), ("gel", "GEL", 0.2), ("hair", "SENSOR HAIRS", 0.11)):
        ts.no_light(bp.stencil(f"earlab_{name}", text, (-W_ / 2 - 0.24, -D_ / 2, z), 0.05, white, root))
        ts.no_light(bp.box(f"earlead_{name}", (0.05, 0.006, 0.007), (-W_ / 2 - 0.04, -D_ / 2, z), white, root))
    bp.light("ear_key", "AREA", (EAR.x - 1.0, -2.6, 1.6), 90, size=2.5, aim=(EAR.x, 0, 0.2))
    O.update(ear=root, hairs=hairs, rocks=rocks, gel=g)


def scene_gravity(samples):
    rnd = random.Random(5)
    sc = bk_scene(samples, (0.32, 0.55, 0.95))
    day_street(rnd)
    bp.light("sun", "SUN", (0, 0, 10), 3.2, size=1.5, color=(1.0, 0.95, 0.86),
             rot=(math.radians(50), math.radians(8), math.radians(-35)))
    bp.light("fill", "AREA", (-2.5, -4.5, 2.5), 120, size=4.0, color=(0.8, 0.88, 1.0), aim=(0, 0, 1.0))
    P = bp.build_dummy_v2(at=(0, 0, 0), yaw=math.radians(-14), label="")
    humanise()
    O.update(P=P, rnd=rnd, loose=loose_things(rnd))
    ruler()
    globe_diagram(rnd)
    ear_diagram(rnd)
    cam = bp.cam_free(sc, 28, (-0.5, -4.6, 1.0), (0, 0, 0.7))
    cam.data.dof.use_dof = False
    return sc


def timeline_gravity(sc, T):
    fr = [int(round(t * FPS)) for t in T["starts"]] + [T["frames"]]
    S = dict(zip(T["shots"], zip(fr[:-1], fr[1:])))
    end = T["frames"] + 2
    sc.render.motion_blur_position = "START"
    cam, P, rnd = bpy.data.objects["cam"], O["P"], O["rnd"]
    root = P["root"]
    back = S["drop"][0] + 10                                     # the frame gravity returns
    # how high everything loose has drifted, frame by frame (the 5 seconds are stretched over the whole Short)
    H = [(0, 0.0), (8, 0.0), (S["off"][1], 0.05), (S["rise"][0], 0.1), (S["rise"][1], 0.3), (S["fall"][1], 0.42),
         (back, 0.42), (back + 3, 0.37), (back + 5, 0.26), (back + 7, 0.0)]

    def height(f):
        for (f0, h0), (f1, h1) in zip(H, H[1:]):
            if f0 <= f <= f1:
                return h0 + (h1 - h0) * (f - f0) / max(1, f1 - f0)
        return 0.0
    for f, h in H:
        k(root, "location", f, Vector((0, 0, h)), "LINEAR")
    k(root, "location", back + 10, Vector((0, 0, -0.08)), "BEZIER")      # knees take the landing
    k(root, "location", back + 24, Vector((0, 0, 0.0)), "BEZIER")
    for j, (o, p0, spin) in enumerate(O["loose"]):
        lag, gain = rnd.uniform(0.8, 1.25), rnd.uniform(-0.25, 0.25)
        drift = Vector((rnd.uniform(-0.12, 0.12), rnd.uniform(-0.12, 0.12), 0))
        r0 = Vector((rnd.uniform(0, 6), rnd.uniform(0, 6), rnd.uniform(0, 6))) if spin > 1 else Vector((0, 0, rnd.uniform(0, 6)))
        ax = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))) * spin
        for f in sorted({f for f, _ in H} | set(range(0, back, 24))):
            u = height(f) / 0.42
            k(o, "location", f, tuple(p0 + Vector((0, 0, height(f) * lag)) + drift * u), "LINEAR")
            k(o, "rotation_euler", f, tuple(r0 + ax * u), "LINEAR")
        land = back + 7
        k(o, "location", land + 4, tuple(p0 + drift * (1 + gain) + Vector((0, 0, rnd.uniform(0.02, 0.09)))), "LINEAR")
        k(o, "location", land + 8, tuple(p0 + drift * (1 + gain)), "LINEAR")
        k(o, "rotation_euler", land + 8, tuple(r0 + ax * 1.15), "LINEAR")

    # 1 off: you on the street; your feet leave the road, and so does everything around you
    a, b = S["off"]
    shot(cam, a, b, (-0.6, -4.7, 0.7), (0, 0, 0.6), (-0.5, -4.2, 0.6), (0, 0, 0.62), lens=28)
    pose(P, 0, sh=(-6, 8, 0), el=(-12, 0, 0), head=(0, 0, 0), chest=(0, 0, 0), hip=(0, 0, 0), kn=(0, 0, 0))
    pose(P, 14, sh=(-10, 30, 0), el=(-30, 0, 0), head=(16, 0, 0), chest=(4, 0, 0), hip=(-4, 0, 0), kn=(8, 0, 0))
    pose(P, 40, sh=(-16, 62, 0), el=(-24, 0, 0), head=(24, 0, 8), chest=(6, 0, 0), hip_1=(-12, 0, 0), hip1=(4, 0, 0),
         kn_1=(22, 0, 0), kn1=(10, 0, 0))
    pose(P, b, sh=(-12, 70, 0), el=(-18, 0, 0), head=(20, 0, -10), chest=(2, 0, 0), hip_1=(2, 0, 0), hip1=(-14, 0, 0),
         kn_1=(8, 0, 0), kn1=(26, 0, 0))

    # 2 globe: seen from above the pole -- the ground turns away under you while you carry straight on
    a, b = S["globe"]
    G = GLOBE
    shot(cam, a, b, (G.x + 0.1, -3.1, G.z + 0.12), (G.x + 0.1, 0, G.z + 0.1), (G.x + 0.14, -2.9, G.z + 0.12),
         (G.x + 0.14, 0, G.z + 0.1), lens=40)
    reach = 0.44
    th = reach / GLOBE_R
    k(O["spin"], "rotation_euler", a, (0, -0.35, 0), "LINEAR")
    k(O["spin"], "rotation_euler", a + 20, (0, 0, 0), "LINEAR")
    k(O["spin"], "rotation_euler", b, (0, th * 1.0, 0), "LINEAR")
    y0, z0 = O["gyou"].location.y, O["gyou"].location.z
    cz = 0.18 - GLOBE_R
    for f in range(a, a + 21, 4):                                # until the switch you ride the ground
        ang = -0.35 * (1 - (f - a) / 20)
        k(O["gyou"], "location", f, (GLOBE_R * 0.993 * math.sin(ang), y0, cz + GLOBE_R * 0.993 * math.cos(ang)), "LINEAR")
        k(O["gyou"], "rotation_euler", f, (0, ang, 0), "LINEAR")
    k(O["gyou"], "location", b, (reach, y0, z0), "LINEAR")      # then: a straight line
    k(O["gpath"], "scale", a + 20, (0.001, 1, 1), "LINEAR"), k(O["gpath"], "scale", b, (reach, 1, 1), "LINEAR")
    k(O["gpath"], "location", a + 20, (0, O["gpath"].location.y, O["gpath"].location.z), "LINEAR")
    k(O["gpath"], "location", b, (reach / 2, O["gpath"].location.y, O["gpath"].location.z), "LINEAR")
    shown(O["gpath"], a + 20)

    # 3 rise: low and close on your feet, beside a marked post: forty centimetres of daylight under them
    a, b = S["rise"]
    shot(cam, a, b, (-0.9, -3.0, 0.22), (0.2, 0, 0.3), (-0.75, -2.7, 0.2), (0.2, 0, 0.36), lens=30)
    pose(P, a, sh=(-12, 70, 0), el=(-18, 0, 0), head=(20, 0, -10), chest=(2, 0, 0), hip_1=(2, 0, 0), hip1=(-14, 0, 0),
         kn_1=(8, 0, 0), kn1=(26, 0, 0))
    pose(P, (a + b) // 2, sh=(-20, 56, 0), el=(-30, 0, 0), head=(30, 0, 0), chest=(8, 0, 0), hip_1=(-16, 0, 0),
         hip1=(4, 0, 0), kn_1=(30, 0, 0), kn1=(10, 0, 0))
    pose(P, b, sh=(-8, 72, 0), el=(-16, 0, 0), head=(26, 0, 10), chest=(4, 0, 0), hip_1=(4, 0, 0), hip1=(-18, 0, 0),
         kn_1=(8, 0, 0), kn1=(32, 0, 0))

    # 4 ear: the crystals that rest on the gel lift off it; the sensor hairs under it stand up straight
    a, b = S["ear"]
    E = EAR
    shot(cam, a, b, (E.x - 0.12, -2.8, 0.45), (E.x - 0.12, 0, 0.2), (E.x - 0.12, -2.7, 0.43), (E.x - 0.12, 0, 0.22), lens=40)
    lift = a + int(2.6 * FPS)                                    # on "Now they float"
    for h in O["hairs"]:
        k(h, "rotation_euler", a, (0, math.radians(24), 0), "BEZIER")
        k(h, "rotation_euler", lift, (0, math.radians(24), 0), "BEZIER")
        k(h, "rotation_euler", lift + 22, (0, 0, 0), "BEZIER")
    g = O["gel"]
    gz = g.location.z
    k(g, "location", a, (0.022, g.location.y, gz - 0.008), "BEZIER"), k(g, "location", lift, (0.022, g.location.y, gz - 0.008), "BEZIER")
    k(g, "location", lift + 22, (0, g.location.y, gz), "BEZIER")
    for o in O["rocks"]:
        p0 = Vector(o.location)
        sag = Vector((0.022, 0, -0.008))
        k(o, "location", a, tuple(p0 + sag), "BEZIER"), k(o, "location", lift, tuple(p0 + sag), "BEZIER")
        up = Vector((rnd.uniform(-0.06, 0.06), 0, rnd.uniform(0.08, 0.3)))
        k(o, "location", b + 10, tuple(p0 + up), "BEZIER")
        k(o, "rotation_euler", lift, (0, 0, 0), "LINEAR")
        k(o, "rotation_euler", b + 10, (rnd.uniform(-2, 2), rnd.uniform(-2, 2), rnd.uniform(-2, 2)), "LINEAR")

    # 5 fall: on you, hanging in the air, arms and legs hunting for something to hold
    a, b = S["fall"]
    shot(cam, a, b, (1.0, -4.7, 0.9), (0, 0, 0.95), (0.85, -4.4, 0.9), (0, 0, 1.0), lens=28)
    for j, f in enumerate(range(a, b + 1, 16)):
        s = 1 if j % 2 else -1
        pose(P, f, sh_1=(-30 - 30 * s, 60 + 10 * s, 0), sh1=(-30 + 30 * s, -60 + 10 * s, 0), el=(-30 - 14 * s, 0, 0),
             head=(10 + 12 * s, 0, 14 * s), chest=(6 * s, 0, 6 * s), hip_1=(-20 - 18 * s, 0, 0), hip1=(-20 + 18 * s, 0, 0),
             kn_1=(34 + 16 * s, 0, 0), kn1=(34 - 16 * s, 0, 0))
    k(root, "rotation_euler", a, (0, 0, root.rotation_euler.z), "LINEAR")
    k(root, "rotation_euler", b, (math.radians(-9), math.radians(7), root.rotation_euler.z), "LINEAR")
    k(root, "rotation_euler", back + 6, (0, 0, root.rotation_euler.z), "LINEAR")

    # 6 drop: gravity is back -- you and everything else come down together
    a, b = S["drop"]
    shot(cam, a, b, (-0.7, -4.6, 0.5), (0, 0, 0.6), (-0.6, -4.3, 0.5), (0, 0, 0.55), lens=28)
    pose(P, back, sh=(-40, 60, 0), el=(-30, 0, 0), head=(10, 0, 0), chest=(4, 0, 0), hip=(-14, 0, 0), kn=(26, 0, 0))
    pose(P, back + 7, sh=(-30, 40, 0), el=(-40, 0, 0), head=(14, 0, 0), chest=(10, 0, 0), hip=(-20, 0, 0), kn=(30, 0, 0))
    pose(P, back + 10, sh=(-40, 30, 0), el=(-50, 0, 0), head=(24, 0, 0), chest=(22, 0, 0), hip=(-52, 0, 0), kn=(70, 0, 0))
    pose(P, back + 26, sh=(-10, 12, 0), el=(-20, 0, 0), head=(6, 0, 0), chest=(4, 0, 0), hip=(-4, 0, 0), kn=(6, 0, 0))
    puffs("landdust", (0, -0.05, 0.0), back + 7, 7, rnd, (0.55, 0.52, 0.48), spread=0.8, rise=0.18, life=30, size=0.2, dense=0.45)

    # 7 time's up: on your feet, the street scattered around you
    a, b = S["timesup"]
    shot(cam, a, b, (0.6, -4.5, 1.0), (0, 0, 0.62), (0.5, -4.1, 1.0), (0, 0, 0.66), lens=28)
    pose(P, a, sh=(-10, 12, 0), el=(-20, 0, 0), head=(6, 0, 0), chest=(4, 0, 0), hip=(-4, 0, 0), kn=(6, 0, 0))
    pose(P, a + 40, sh=(-4, 8, 0), el=(-14, 0, 0), head=(-20, 0, 0), chest=(-2, 0, 0), hip=(0, 0, 0), kn=(0, 0, 0))
    pose(P, b, sh=(-6, 10, 0), el=(-16, 0, 0), head=(-30, 0, 10), chest=(-4, 0, 0))

    # 8 end: pull back
    a, b = S["end"]
    shot(cam, a, b, (0.5, -4.1, 1.0), (0, 0, 0.66), (0.9, -5.8, 1.5), (0, 0, 0.7), lens=28)
    pose(P, a, head=(-30, 0, 10), chest=(-4, 0, 0))
    pose(P, b, head=(-6, 0, -8), chest=(0, 0, 0))
