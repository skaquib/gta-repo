"""
blender_panda_anim.py — animates "Being a Panda Is a Scam 🐼" on top of the owner-approved look
(blender_panda_scene.py builds the panda, the forest and the opening pose; this file adds the extra props and keys
every shot to the voice timing from run_panda_short.py).

  /root/.venvs/blender/bin/python blender_panda_anim.py FRAMES_DIR TIMING.json still F [F ...]
  /root/.venvs/blender/bin/python blender_panda_anim.py FRAMES_DIR TIMING.json A B

Shots (one per line of the script): open (talks while chewing), belly (looks down, pats it), stalk (holds the
bamboo up, disappointed, then deadpan to camera), shrug, poo (a dropping plops down, the panda looks away),
thumb (waves its paw at the camera), baby (flashback: a newborn cub next to a stick of butter), sigh (big sigh,
back to chewing) and the end card. The jaw follows the voice's loudness frame by frame.
"""
import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from mathutils import Matrix, Quaternion, Vector  # noqa: E402

import blender_kit as bk  # noqa: E402
import blender_panda_scene as ps  # noqa: E402
from blender_critic_scene import box, leaf_mesh  # noqa: E402

FPS = ps.FPS
D = math.radians
rng = random.Random(11)


def F(t):
    return int(round(t * FPS))


# ── keyframe helpers ──────────────────────────────────────────────────────────
def _key(ob, path, f, interp):
    ob.keyframe_insert(path, frame=f)
    bk._set_interp(ob.animation_data.action, f, interp)


def track(ob, path, keys, interp="BEZIER"):
    """keys: [(frame, value)] in any order; later duplicates of a frame win. Quaternions are kept sign-continuous."""
    last = None
    for f, v in sorted(dict(keys).items()):
        if path == "rotation_quaternion":
            ob.rotation_mode = "QUATERNION"
            v = v.copy()
            if last is not None and last.dot(v) < 0:
                v.negate()
            last = v
        setattr(ob, path, v)
        _key(ob, path, f, interp)


def orient(sh, d_world, palm_world):
    """Shoulder-pivot rotation (in its parent's rest space): local -Z along d_world, local -Y toward palm_world."""
    R = sh.parent.matrix_world.to_3x3().normalized().inverted()
    z = -(R @ Vector(d_world)).normalized()
    y0 = -(R @ Vector(palm_world))
    y = (y0 - z * y0.dot(z)).normalized()
    x = y.cross(z)
    return Matrix((x, y, z)).transposed().to_quaternion()


def cam_loc(at, dist, elev, azim):
    e, a = D(elev), D(azim)
    return Vector((at[0] + dist * math.cos(e) * math.sin(a), at[1] - dist * math.cos(e) * math.cos(a),
                   at[2] + dist * math.sin(e)))


# ── extra props ───────────────────────────────────────────────────────────────
def add_paw_pads(P):
    """Palm pad and the 'thumb' (an enlarged wrist bone under a pad) on each paw, with no fur over them."""
    pad = bk.mat_basic("palm_pad", (0.16, 0.13, 0.12), rough=0.42, coat=0.35)
    for s in (-1, 1):
        sh = P[f"arm{s}"]
        arm = bpy.data.objects[f"arm{s}"]
        arm.vertex_groups.new(name="palmfree")
        g = arm.vertex_groups["palmfree"]
        for v in arm.data.vertices:
            c = v.co
            w = 1 - ps.smooth(-0.03, -0.06, c.y) * ps.smooth(-0.22, -0.27, c.z)
            g.add([v.index], max(0.0, w), "REPLACE")
        arm.particle_systems[0].vertex_group_density = "palmfree"
        palm = ps.link(ps.blob(f"palm{s}", (0.05, 0.012, 0.058)), sh)
        palm.location = (0, -0.083, -0.345)
        palm.rotation_euler = (D(-12), 0, 0)
        palm.data.materials.append(pad)
        thumb = ps.link(ps.blob(f"thumbpad{s}", (0.03, 0.018, 0.04)), sh)
        thumb.location = (s * 0.045, -0.07, -0.27)
        thumb.data.materials.append(pad)
        for k in range(5):
            a = D(-48 + k * 24)
            toe = ps.link(ps.blob(f"fpad{s}{k}", (0.011, 0.008, 0.011), segs=20, rings=10), sh)
            toe.location = (0.05 * math.sin(a), -0.07, -0.41 - 0.012 * math.cos(a))
            toe.data.materials.append(pad)


def mat_poo():
    m, b, nt = bk._principled("poo")
    N, L = nt.nodes, nt.links
    b.inputs["Roughness"].default_value = 0.62
    tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (12, 90, 90)          # fibres run along the dropping
    L.new(tc.outputs["Object"], mp.inputs["Vector"])
    nz = N.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 2.0
    nz.inputs["Detail"].default_value = 6
    L.new(mp.outputs[0], nz.inputs["Vector"])
    ramp = N.new("ShaderNodeValToRGB")
    e = ramp.color_ramp.elements
    e[0].position, e[0].color = 0.35, (0.12, 0.13, 0.035, 1)
    e[1].position, e[1].color = 0.68, (0.36, 0.34, 0.11, 1)
    L.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    L.new(ramp.outputs["Color"], b.inputs["Base Color"])
    bump = N.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.7
    bump.inputs["Distance"].default_value = 0.003
    L.new(nz.outputs["Fac"], bump.inputs["Height"])
    L.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def build_poo(at):
    """A small heap of spindle-shaped, bamboo-fibre droppings (giant panda droppings are green-yellow ovals)."""
    m = mat_poo()
    tex = bpy.data.textures.new("poo_noise", "CLOUDS")
    tex.noise_scale = 0.25
    out = []
    spots = [(0, 0, 0.018, 0.3), (0.07, 0.03, 0.018, -0.5), (-0.06, 0.04, 0.017, 1.2), (0.02, 0.08, 0.017, 2.0),
             (0.03, 0.035, 0.05, 0.9), (-0.02, -0.04, 0.017, -1.1)]
    for k, (x, y, z, rz) in enumerate(spots + [(0.0, 0.02, 0.07, 0.4)]):
        x, y, z = x * 1.3, y * 1.3, z * 1.3
        ob = ps.link(ps.blob(f"poo{k}", (0.055, 0.026, 0.024), segs=40, rings=20,
                             deform=lambda a, b_, c: (a, b_ * (1 - 0.25 * a * a), c * (1 - 0.25 * a * a))))
        dm = ob.modifiers.new("lumpy", "DISPLACE")
        dm.texture = tex
        dm.strength = 0.004
        ob.data.materials.append(m)
        ob.location = (at[0] + x, at[1] + y, z)
        ob.rotation_euler = (rng.uniform(-0.2, 0.2), rng.uniform(-0.2, 0.2), rz)
        out.append(ob)
    return out          # the last one is the one that drops in


def build_cub(at):
    """A newborn giant panda: pink, eyes shut, a fuzz of fine white hair, about the size of a stick of butter."""
    skin = bk.mat_basic("cub_skin", (0.92, 0.48, 0.5), rough=0.45, sss=0.35)
    hairm = ps.mat_fur("cub_fur", 0.03, 0.4, rough=0.3, rand=0.05)
    dark = bk.mat_basic("cub_dark", (0.12, 0.04, 0.05), rough=0.5)
    root = ps.pivot("cub_root", at, rot=(0, 0, D(90)))
    body = ps.link(ps.blob("cub_body", (0.06, 0.035, 0.03), (0, 0, 0.028),
                           lambda x, y, z: (x, y * (1 + 0.12 * x), z * (1 + 0.08 * x))), root)
    body.data.materials.append(skin)
    ps.fur(body, "cub_f", hairm, 350, 4, 0.0035, (0, 0, 0), clump=0.0, rough=0.0005, radius=0.00022, seed=21)
    head_p = ps.pivot("cub_head_p", (-0.048, 0, 0.034), root)
    head = ps.link(ps.blob("cub_head", (0.028, 0.025, 0.023), (-0.022, 0, 0.004)), head_p)
    head.data.materials.append(skin)
    ps.fur(head, "cub_hf", hairm, 160, 4, 0.003, (0, 0, 0), clump=0.0, rough=0.0005, radius=0.00022, seed=22)
    snout = ps.link(ps.blob("cub_snout", (0.012, 0.012, 0.01), (-0.047, 0, -0.003)), head_p)
    snout.data.materials.append(skin)
    mouth = ps.link(ps.blob("cub_mouth", (0.006, 0.008, 0.004), (-0.055, 0, -0.01)), head_p)
    mouth.data.materials.append(dark)
    for s in (-1, 1):
        eye = ps.link(ps.blob(f"cub_eye{s}", (0.006, 0.0018, 0.0016)), head_p)       # shut: a dark line
        eye.location = (-0.034, s * 0.016, 0.013)
        eye.rotation_euler = (0, 0, s * D(70))
        eye.data.materials.append(dark)
        ear = ps.link(ps.blob(f"cub_ear{s}", (0.007, 0.004, 0.006)), head_p)
        ear.location = (-0.016, s * 0.02, 0.024)
        ear.data.materials.append(skin)
    limbs = []
    for k, (x, y) in enumerate(((-0.03, -0.03), (-0.03, 0.03), (0.035, -0.028), (0.035, 0.028))):
        lp = ps.pivot(f"cub_limb_p{k}", (x, y * 0.9, 0.02), root)
        limb = ps.link(ps.blob(f"cub_limb{k}", (0.009, 0.009, 0.017), (0, 0, -0.014)), lp)
        limb.data.materials.append(skin)
        lp.rotation_euler = (D(-60) if y < 0 else D(60), 0, 0)
        limbs.append(lp)
    tail = ps.link(ps.blob("cub_tail", (0.02, 0.007, 0.007), (0.072, 0, 0.022)), root)
    tail.data.materials.append(skin)
    # the stick of butter, half unwrapped, and a bed of dry leaves
    butter = ps.link(box("butter", 0.12, 0.032, 0.032, bk.mat_basic("butter", (0.98, 0.78, 0.28), rough=0.35,
                                                                     sss=0.2), bevel=0.0015))
    butter.location = (at[0] + 0.08, at[1] + 0.005, 0.017)
    butter.rotation_euler = (0, 0, D(92))
    wrap = ps.link(box("wrapper", 0.062, 0.034, 0.034, bk.mat_basic("wrapper", (0.9, 0.9, 0.87), rough=0.3),
                       bevel=0.001))
    wrap.parent = butter
    wrap.location = (0.03, 0, 0)
    dry = bk.mat_basic("leaf_dry_bed", (0.42, 0.3, 0.12), rough=0.7)
    for k in range(26):
        lf = ps.link(leaf_mesh(f"bed{k}", rng.uniform(0.12, 0.17), 0.024, dry, curl=0.15, cup=0.1))
        lf.location = (at[0] + rng.uniform(-0.18, 0.18), at[1] + rng.uniform(-0.12, 0.2), 0.003 + rng.uniform(0, 0.004))
        lf.rotation_euler = (rng.uniform(-0.1, 0.1), rng.uniform(-0.1, 0.1), rng.uniform(0, 6.28))
    light = bpy.data.lights.new("cub_key", "AREA")
    light.energy, light.size, light.color = 22, 0.5, (1.0, 0.9, 0.78)
    lo = ps.link(bpy.data.objects.new("cub_key", light))
    lo.location = (at[0] - 0.35, at[1] - 0.45, 0.55)
    ps.aim(lo, (0.35, 0.45, -0.55), "-Z")
    return {"root": root, "head": head_p, "limbs": limbs}


# ── the animation ─────────────────────────────────────────────────────────────
def animate(sc, P, cam, target, T):
    starts, ends, n = T["starts"], T["ends"], T["frames"]
    S = {name: i for i, name in enumerate(T["shots"])}
    st = {name: starts[i] for name, i in S.items()}
    en = {name: ends[i] for name, i in S.items()}
    f0 = {name: (0 if i == 0 else F(starts[i])) for name, i in S.items()}
    f1 = {name: (F(starts[i + 1]) - 1 if i + 1 < len(starts) else n - 1) for name, i in S.items()}
    sc.frame_start, sc.frame_end = 0, n - 1
    bpy.context.view_layer.update()

    # props
    add_paw_pads(P)
    poo_at = (0.12, -0.7, 0.0)
    poos = build_poo(poo_at)
    cub_at = Vector((2.2, -1.5, 0.0))
    cub = build_cub(cub_at)
    stalk = bpy.data.objects["stalk"]
    arm_l, arm_r = P["arm-1"], P["arm1"]
    bpy.context.view_layer.update()
    grip = ps.pivot("grip", (0, 0, -0.4), arm_l)          # the paw; the stalk turns in it
    grip.rotation_mode = "QUATERNION"
    bpy.context.view_layer.update()
    stalk.parent = grip
    stalk.matrix_parent_inverse = grip.matrix_world.inverted()

    # arm poses
    belly_w = P["body"].matrix_world @ Vector((0.02, -0.36, 0.3))
    shr = arm_r.matrix_world.translation.copy()
    q_mouth = arm_l.rotation_quaternion.copy()
    Rl = arm_l.parent.matrix_world.to_3x3().normalized().inverted()

    def swing(d_world):            # turn the stalk arm the shortest way, so the stalk it holds turns with it
        d_now = q_mouth @ Vector((0, 0, -1))
        return d_now.rotation_difference((Rl @ Vector(d_world)).normalized()) @ q_mouth

    L = {"mouth": q_mouth, "lap": swing((0.12, -0.6, -0.79)), "raise": swing((-0.42, -0.72, 0.55)),
         "shrug": swing((-0.72, -0.55, -0.32))}
    q0 = Quaternion()

    def grip_for(q_arm, desired):
        """Grip rotation that points the stalk's long end along `desired` (world) when the arm is at q_arm."""
        arm_l.rotation_quaternion, grip.rotation_quaternion = q_arm, q0
        bpy.context.view_layer.update()
        cur = (stalk.matrix_world.to_3x3().normalized() @ Vector((0, 0, 1))).normalized()
        new_w = cur.rotation_difference(Vector(desired).normalized()) @ grip.matrix_world.to_3x3().normalized().to_quaternion()
        q = arm_l.matrix_world.to_3x3().normalized().to_quaternion().inverted() @ new_w
        arm_l.rotation_quaternion = q_mouth
        bpy.context.view_layer.update()
        return q

    G = {"mouth": q0, "lap": grip_for(L["lap"], (-0.45, -0.3, 0.84)), "raise": grip_for(L["raise"], (-0.08, -0.12, 1.0)),
         "shrug": grip_for(L["shrug"], (-0.3, -0.3, 0.9))}
    R = {"belly": orient(arm_r, belly_w - shr, (-0.6, 0.6, 0.2)),
         "pat": orient(arm_r, (belly_w + Vector((0, -0.09, 0.08))) - shr, (-0.6, 0.6, 0.2)),
         "shrug": orient(arm_r, (0.72, -0.55, -0.32), (0, 0, 1)),
         "wave": orient(arm_r, (0.25, -0.42, 0.87), (0, -1, 0.3))}
    wave_d = Vector((0.25, -0.42, 0.87)).normalized()

    def wiggle(a):
        palm = Quaternion(wave_d, a) @ Vector((0, -1, 0.3))
        return orient(arm_r, wave_d, palm)

    def world_at(ob, q, read, local, gq=None):
        old = ob.rotation_quaternion.copy()
        ob.rotation_quaternion = q
        if gq is not None:
            grip.rotation_quaternion = gq
        bpy.context.view_layer.update()
        p = read.matrix_world @ Vector(local)
        ob.rotation_quaternion = old
        grip.rotation_quaternion = q0
        bpy.context.view_layer.update()
        return p

    stalk_mid = world_at(arm_l, L["raise"], stalk, (0, 0, 0.5), G["raise"])
    paw_wave = world_at(arm_r, R["wave"], arm_r, (0, 0, -0.36))
    face = P["head"].matrix_world @ Vector((0, -0.21, 0.17))

    kl = [(0, L["mouth"]), (f1["open"], L["mouth"]), (f0["belly"], L["lap"]), (f0["stalk"], L["lap"]),
          (F(st["stalk"] + 0.45), L["raise"]), (f1["stalk"], L["raise"]), (f0["shrug"], L["lap"]),
          (F(st["shrug"] + 0.25), L["lap"]), (F(st["shrug"] + 0.55), L["shrug"]), (F(st["shrug"] + 1.9), L["shrug"]),
          (F(st["shrug"] + 2.4), L["lap"]), (F(st["sigh"] + 1.6), L["lap"]), (F(st["sigh"] + 2.4), L["mouth"]),
          (n - 1, L["mouth"])]
    track(arm_l, "rotation_quaternion", kl)
    inv = {id(v): k for k, v in L.items()}
    track(grip, "rotation_quaternion", [(f, G[inv[id(q)]]) for f, q in kl])
    b0 = st["belly"]
    kr = [(0, R["belly"]), (F(b0 + 0.5), R["belly"])]
    for k, tt in enumerate((0.7, 1.1, 2.0, 2.4)):
        kr += [(F(b0 + tt), R["pat"]), (F(b0 + tt + 0.2), R["belly"])]
    kr += [(F(st["shrug"] + 0.25), R["belly"]), (F(st["shrug"] + 0.55), R["shrug"]),
           (F(st["shrug"] + 1.9), R["shrug"]), (F(st["shrug"] + 2.4), R["belly"]),
           (f0["thumb"], R["belly"]), (F(st["thumb"] + 0.35), R["wave"])]
    t, k = st["thumb"] + 0.55, 0
    while t < st["thumb"] + 2.7:
        kr.append((F(t), wiggle(D(28) * (1 if k % 2 == 0 else -1))))
        t, k = t + 0.17, k + 1
    kr += [(F(st["thumb"] + 2.9), R["wave"]), (f1["thumb"], R["wave"]), (f0["baby"], R["belly"]), (n - 1, R["belly"])]
    track(arm_r, "rotation_quaternion", kr)
    for ob in poos:                                   # the heap only exists in its own shot
        for f, hide in ((0, True), (f0["poo"], False), (f1["poo"] + 1, True)):
            ob.hide_render = hide
            ob.keyframe_insert("hide_render", frame=f)
    for ob in bpy.data.objects:
        if ob.name.startswith(("palm", "thumbpad", "fpad")):
            for f, hide in ((0, True), (f0["thumb"], False), (f1["thumb"] + 1, True)):
                ob.hide_render = hide
                ob.keyframe_insert("hide_render", frame=f)

    # head (euler, degrees on top of the opening pose)
    HB = Vector(P["head"].rotation_euler[:])

    def hd(dx=0, dy=0, dz=0):
        return HB + Vector((D(dx), D(dy), D(dz)))

    s_dur = en["stalk"] - st["stalk"]
    kh = [(0, hd()), (F(0.9), hd(3, 0, 2)), (F(1.8), hd(-1, 0, -1)), (F(2.8), hd(2, 2, 0)), (f1["open"], hd()),
          (f0["belly"], hd()), (F(b0 + 0.35), hd(20, 0, -4)), (F(b0 + 1.6), hd(20, 0, -4)), (F(b0 + 2.0), hd(0, 3, 0)),
          (f1["belly"], hd(0, 3, 0)),
          (f0["stalk"], hd()), (F(st["stalk"] + 0.5), hd(-6, 0, -12)), (F(st["stalk"] + 0.55 * s_dur), hd(-6, 0, -12)),
          (F(st["stalk"] + 0.7 * s_dur), hd(2, -6, 0)), (f1["stalk"], hd(2, -6, 0)),
          (f0["shrug"], hd()), (F(st["shrug"] + 0.55), hd(0, 12, 4)), (F(st["shrug"] + 1.9), hd(0, 12, 4)),
          (F(st["shrug"] + 2.3), hd()), (f1["shrug"], hd()),
          (f0["poo"], hd()), (F(st["poo"] + 0.3), hd(10, 0, -38)), (f1["poo"], hd(12, 0, -40)),
          (f0["thumb"], hd()), (F(st["thumb"] + 0.4), hd(-4, 0, 10)), (F(st["thumb"] + 1.4), hd(0, -4, 2)),
          (f1["thumb"], hd(0, -4, 2)), (f0["baby"], hd()),
          (f0["sigh"], hd()), (F(st["sigh"] + 0.6), hd(-12, 0, 0)), (F(st["sigh"] + 1.3), hd(18, 0, 0)),
          (F(st["sigh"] + 1.9), hd()), (F(st["sigh"] + 3.0), hd(2, 0, 3)), (n - 1, hd(-1, 0, 1))]
    track(P["head"], "rotation_euler", kh)

    # body: breathing, the shrug and the big sigh (sampled every 2 frames)
    def bump(t, a, b, c, d):
        return ps.smooth(a, b, t) * (1 - ps.smooth(c, d, t))

    ks = []
    s3, s7 = st["shrug"], st["sigh"]
    for f in range(0, n, 2):
        t = f / FPS
        z = 1 + 0.007 * math.sin(2 * math.pi * t / 3.2)
        z += 0.03 * bump(t, s3 + 0.35, s3 + 0.6, s3 + 1.8, s3 + 2.2)
        inhale = bump(t, s7 + 0.05, s7 + 0.65, s7 + 0.7, s7 + 1.4)
        exhale = bump(t, s7 + 0.7, s7 + 1.4, s7 + 1.7, s7 + 2.4)
        z += 0.045 * inhale - 0.03 * exhale
        xy = 1 + 0.015 * inhale
        ks.append((f, Vector((xy, xy, z))))
    track(P["body"], "scale", ks)

    # eyelids: half shut (tired); blinks; squint when embarrassed; shut through the sigh
    for s in (-1, 1):
        lid = P[f"lid{s}"]
        base = Vector(lid.rotation_euler[:])

        def lv(a):
            return Vector((D(a), base.y, base.z))

        kk = [(0, lv(26)), (n - 1, lv(26))]
        for tb in (1.7, 5.4, 9.2, 12.9, 19.6, 29.6):
            fb = F(tb)
            kk += [(fb - 1, lv(26)), (fb + 1, lv(84)), (fb + 4, lv(26))]
        kk += [(f0["poo"], lv(26)), (F(st["poo"] + 0.3), lv(50)), (f1["poo"], lv(50)), (f0["thumb"], lv(26)),
               (F(s7 + 0.75), lv(26)), (F(s7 + 1.0), lv(80)), (F(s7 + 1.6), lv(80)), (F(s7 + 1.9), lv(26))]
        track(lid, "rotation_euler", kk)

    # jaw: follows the voice's loudness; chews (with crunches) once the talking is done
    mouth = T["mouth"]
    kj, crunch, m_prev = [], [], 0.0
    chew_from = ends[-1] + 0.15
    for f in range(n):
        t = f / FPS
        m = mouth[f] if f < len(mouth) else 0.0
        m = max(m, m_prev * 0.55)                     # quick open, softer close
        m_prev = m
        ang = 1.5 + 15.0 * m
        if t > chew_from:
            ph = 2 * math.pi * 1.6 * (t - chew_from)
            ang = 2.0 + 8.0 * (0.5 - 0.5 * math.cos(ph))
        kj.append((f, Vector((D(ang), 0, 0))))
    t = chew_from + 1 / 1.6
    while t < n / FPS:
        crunch.append(round(t, 3))
        t += 1 / 1.6
    track(P["jaw"], "rotation_euler", kj, interp="LINEAR")

    # the dropping that plops onto the heap
    drop = poos[-1]
    rest = drop.location.copy()
    td = st["poo"] + 0.8
    track(drop, "location", [(0, rest + Vector((0, 0, 4))), (F(td - 0.45) - 1, rest + Vector((0, 0, 4))),
                             (F(td - 0.45), rest + Vector((0, 0, 1.4))), (F(td), rest)], interp="LINEAR")
    track(drop, "scale", [(F(td) - 1, Vector((1, 1, 1))), (F(td), Vector((1.15, 1.15, 0.7))),
                          (F(td) + 3, Vector((0.95, 0.95, 1.08))), (F(td) + 6, Vector((1, 1, 1)))])

    # the cub squirms and squeaks
    b6 = st["baby"]
    track(cub["head"], "rotation_euler", [(f0["baby"], Vector((0, D(-8), 0))), (F(b6 + 0.6), Vector((0, D(-22), D(6)))),
                                          (F(b6 + 1.4), Vector((0, D(-6), D(-4)))), (F(b6 + 2.3), Vector((0, D(-24), D(-8)))),
                                          (f1["baby"], Vector((0, D(-10), 0)))])
    for k, lp in enumerate(cub["limbs"]):
        base = Vector(lp.rotation_euler[:])
        keys = []
        for f in range(f0["baby"], f1["baby"] + 1, 3):
            a = D(18) * math.sin(2 * math.pi * 2.2 * f / FPS + k * 1.7)
            keys.append((f, base + Vector((a, a * 0.5, 0))))
        track(lp, "rotation_euler", keys)

    # cameras, focus and where the eyes look
    shots = {
        "open": [((-0.05, 0, 0.64), 3.3, 5, -4, 38, 1.4), ((-0.03, 0, 0.72), 2.75, 4, -3, 38, 1.4)],
        "belly": [((0.02, -0.1, 0.6), 2.15, 9, 12, 40, 2.0), ((0.02, -0.1, 0.61), 2.0, 9, 10, 40, 2.0)],
        "stalk": [(tuple((face + stalk_mid) / 2), 1.95, 3, -10, 45, 2.4), (tuple((face + stalk_mid) / 2), 1.8, 3, -8, 45, 2.4)],
        "shrug": [((0, 0, 0.62), 3.0, 4, 0, 38, 2.0), ((0, 0, 0.64), 2.8, 4, 0, 38, 2.0)],
        "poo": [((0.05, -0.4, 0.34), 2.45, 21, 8, 34, 4.0), ((0.05, -0.4, 0.34), 2.3, 21, 7, 34, 4.0)],
        "thumb": [(tuple((paw_wave + face) / 2 + Vector((0, 0, -0.08))), 2.2, 3, 18, 45, 2.8),
                  (tuple((paw_wave + face) / 2 + Vector((0, 0, -0.08))), 2.05, 3, 16, 45, 2.8)],
        "baby": [((cub_at.x + 0.035, cub_at.y + 0.005, 0.025), 0.66, 50, 0, 40, 2.8),
                 ((cub_at.x + 0.035, cub_at.y + 0.005, 0.025), 0.6, 52, 0, 40, 2.8)],
        "sigh": [((-0.04, 0, 0.66), 2.9, 5, -3, 38, 1.6), ((-0.05, 0, 0.62), 3.35, 5, -4, 38, 1.6)],
    }
    focus = ps.pivot("focus_w", face)
    gaze = ps.pivot("gaze", (0, -3, 1))
    cam.data.dof.focus_object = focus
    for s in (-1, 1):
        P[f"eye{s}"].constraints["Damped Track"].target = gaze
    kf, kg = [], []
    for name, (a, b) in shots.items():
        bk.shot(cam, target, f0[name], *a)
        if name == "sigh":                            # hold through the lines, pull back for the end card
            bk.shot(cam, target, F(en["sigh"]), (-0.04, 0, 0.68), 2.75, 5, -3, 38, 1.6)
        bk.shot(cam, target, f1[name], *b)
        cl = cam_loc(*a[:4])
        kg += [(f0[name], cl), (f1[name], cam_loc(*b[:4]))]
        kf.append((f0[name], {"poo": Vector(poo_at) + Vector((0, 0, 0.03)), "thumb": paw_wave,
                              "baby": cub_at + Vector((0, -0.06, 0.04))}.get(name, face)))
        kf.append((f1[name], kf[-1][1]))
    kg += [(F(b0 + 0.35), belly_w), (F(b0 + 1.6), belly_w), (F(b0 + 2.0), cam_loc(*shots["belly"][0][:4])),
           (F(st["stalk"] + 0.4), stalk_mid), (F(st["stalk"] + 0.55 * s_dur), stalk_mid),
           (F(st["stalk"] + 0.65 * s_dur), cam_loc(*shots["stalk"][0][:4])),
           (F(st["poo"] + 0.3), Vector((-2.5, -1.6, 0.9))), (f1["poo"], Vector((-2.5, -1.6, 0.9))),
           (F(st["thumb"] + 0.35), paw_wave), (F(st["thumb"] + 1.2), paw_wave),
           (F(st["thumb"] + 1.45), cam_loc(*shots["thumb"][0][:4]))]
    track(gaze, "location", kg)
    track(focus, "location", kf, interp="CONSTANT")
    return {"crunch": crunch, "thump": [round(td, 3)]}


def build(T):
    sc, P, cam = ps.build_scene()
    target = bpy.data.objects["cam_target"]
    cues = animate(sc, P, cam, target, T)
    return sc, cues


if __name__ == "__main__":
    out, timing_path = sys.argv[1], sys.argv[2]
    T = json.load(open(timing_path))
    os.makedirs(out, exist_ok=True)
    sc, cues = build(T)
    with open(os.path.join(out, "cues.json"), "w") as f:
        json.dump(cues, f)
    if sys.argv[3] == "still":
        sdir = os.path.join(os.path.dirname(out.rstrip("/")), "stills")
        os.makedirs(sdir, exist_ok=True)
        for fr in map(int, sys.argv[4:]):
            sc.frame_set(fr)
            sc.render.filepath = os.path.join(sdir, f"s_{fr:04d}.png")
            bpy.ops.render.render(write_still=True)
            print("wrote", sc.render.filepath)
    else:
        bk.render(sc, out, int(sys.argv[3]), int(sys.argv[4]))
