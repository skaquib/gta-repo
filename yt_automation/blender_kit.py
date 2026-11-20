"""
blender_kit.py — Reusable Blender (bpy) building blocks for FramedFacts 3D
Shorts. Runs ONLY inside the Blender environment (/root/.venvs/blender,
`pip install bpy`), never in the main pipeline env: bpy pins numpy 1.26,
which breaks Kokoro (numpy >= 2) -- see blender_setup notes in GROWTH_PLAN.md.

Why Blender (owner, 2026-11-01): the home-made numpy renderer (render3d.py)
had no shadows, textures or real materials, so animals looked like toys.
Cycles gives physically based light, soft shadows, subsurface skin/shell,
depth of field -- for free. CPU only here (4 cores): 720x1280, ~8-16 spp
+ OpenImageDenoise is ~10-20 s/frame; the frames are upscaled to 1080x1920
and the text overlays are drawn afterwards in the main env.

Typical use in a scene script:
    import blender_kit as bk
    sc = bk.new_scene(fps=24, res=(720, 1280), samples=12)
    bk.studio(sc)                         # cyclorama + 3 soft lights
    egg = bk.egg("ostrich", length=0.155, radius=0.065, mat=bk.mat_shell(...))
    cam, target = bk.camera(sc)
    bk.shot(cam, target, frame, target_xyz, dist, elev_deg, lens)
    bk.export_anchors(sc, cam, {"name": obj}, path)   # 2D label positions per frame
    bk.render(sc, out_dir, start, end)
"""
import json
import math

import bpy
import bmesh
from bpy_extras.object_utils import world_to_camera_view


# ── scene / render settings ───────────────────────────────────────────────────
def new_scene(fps=24, res=(720, 1280), samples=12, frames=1):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.fps = fps
    sc.frame_start, sc.frame_end = 0, frames - 1
    sc.render.engine = "CYCLES"
    c = sc.cycles
    c.device = "CPU"
    c.samples = samples
    c.use_adaptive_sampling = True
    c.adaptive_threshold = 0.05
    c.use_denoising = True
    c.denoiser = "OPENIMAGEDENOISE"
    c.max_bounces, c.diffuse_bounces, c.glossy_bounces = 4, 2, 2
    c.transmission_bounces, c.transparent_max_bounces = 4, 16
    c.caustics_reflective = c.caustics_refractive = False
    sc.render.use_persistent_data = True
    sc.render.image_settings.file_format = "PNG"
    try:
        sc.view_settings.view_transform = "AgX"
        sc.view_settings.look = "AgX - Punchy"
    except TypeError:
        pass
    return sc


def _principled(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m, m.node_tree.nodes["Principled BSDF"], m.node_tree


def mat_basic(name, color, rough=0.5, sss=0.0, coat=0.0, metallic=0.0):
    m, b, _ = _principled(name)
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metallic
    if sss:
        b.inputs["Subsurface Weight"].default_value = sss
        b.inputs["Subsurface Radius"].default_value = (0.4, 0.25, 0.12)
    if coat:
        b.inputs["Coat Weight"].default_value = coat
    return m


def mat_shell(name, base, speck=None, speck_amount=0.0, speck_scale=180.0, pits=0.0, pit_scale=600.0,
              rough=0.45, sss=0.15, mottle=0.0):
    """Eggshell: base colour, optional dark speckles, optional pitted bump,
    optional large-scale mottling, a little subsurface glow."""
    m, b, nt = _principled(name)
    N, L = nt.nodes, nt.links
    b.inputs["Roughness"].default_value = rough
    b.inputs["Subsurface Weight"].default_value = sss
    b.inputs["Subsurface Radius"].default_value = (0.5, 0.35, 0.2)
    col = N.new("ShaderNodeRGB")
    col.outputs[0].default_value = (*base, 1)
    out = col.outputs[0]
    if mottle:
        nz = N.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = 18.0
        mix = N.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.inputs["Factor"].default_value = mottle
        mul = N.new("ShaderNodeMix")
        mul.data_type = "RGBA"
        mul.blend_type = "MULTIPLY"
        mul.inputs["Factor"].default_value = 1.0
        L.new(out, mul.inputs[6])
        L.new(nz.outputs["Fac"], mul.inputs[7])
        L.new(out, mix.inputs[6])
        L.new(mul.outputs[2], mix.inputs[7])
        out = mix.outputs[2]
    if speck and speck_amount:
        nz = N.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = speck_scale
        nz.inputs["Detail"].default_value = 2.0
        ramp = N.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 1 - speck_amount * 0.35
        ramp.color_ramp.elements[1].position = 1 - speck_amount * 0.35 + 0.04
        L.new(nz.outputs["Fac"], ramp.inputs["Fac"])
        mix = N.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        sp = N.new("ShaderNodeRGB")
        sp.outputs[0].default_value = (*speck, 1)
        L.new(ramp.outputs["Color"], mix.inputs["Factor"])
        L.new(out, mix.inputs[6])
        L.new(sp.outputs[0], mix.inputs[7])
        out = mix.outputs[2]
    L.new(out, b.inputs["Base Color"])
    if pits:
        vor = N.new("ShaderNodeTexVoronoi")
        vor.inputs["Scale"].default_value = pit_scale
        bump = N.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = pits
        L.new(vor.outputs["Distance"], bump.inputs["Height"])
        L.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def xray_fade(mat, frame_on, frame_full, alpha=0.18, rim=(0.25, 0.8, 1.0), rim_strength=2.5):
    """Animate a material from solid to an x-ray look: alpha drops and a
    fresnel-driven cyan rim glow fades in between frame_on and frame_full."""
    nt = mat.node_tree
    b = nt.nodes["Principled BSDF"]
    fr = nt.nodes.new("ShaderNodeFresnel")
    fr.inputs["IOR"].default_value = 1.6
    nt.links.new(fr.outputs["Fac"], b.inputs["Emission Strength"])
    b.inputs["Emission Color"].default_value = (*rim, 1)
    mult = nt.nodes.new("ShaderNodeMath")
    mult.operation = "MULTIPLY"
    nt.links.new(fr.outputs["Fac"], mult.inputs[0])
    nt.links.new(mult.outputs[0], b.inputs["Emission Strength"])
    for f, a, s in ((frame_on, 1.0, 0.0), (frame_full, alpha, rim_strength)):
        b.inputs["Alpha"].default_value = a
        b.inputs["Alpha"].keyframe_insert("default_value", frame=f)
        mult.inputs[1].default_value = s
        mult.inputs[1].keyframe_insert("default_value", frame=f)


# ── geometry ──────────────────────────────────────────────────────────────────
def egg(name, length, radius, mat, location=(0, 0, 0), pointy=0.12, rot_z=0.0, lying=True):
    """An egg (blunt end toward +X), smooth-shaded. lying=True rests it on
    its side on the floor at `location` (x, y; z is computed)."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=96, v_segments=48, radius=1.0)
    for v in bm.verts:
        a = v.co.z
        k = 1 + pointy * a
        v.co = (a * length / 2, v.co.x * radius * k, v.co.y * radius * k) if lying else \
               (v.co.x * radius * k, v.co.y * radius * k, a * length / 2)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    zmin = min(v.co.z for v in me.vertices)
    ob.location = (location[0], location[1], -zmin + 0.0002)
    ob.rotation_euler = (0, 0, rot_z)
    me.materials.append(mat)
    return ob


def ruler(name, length, width, location, color=(0.82, 0.82, 0.8)):
    """A flat measuring ruler along X with procedural centimetre ticks
    (longer every 5 cm and 10 cm) -- an instant scale cue in macro shots."""
    me = bpy.data.meshes.new(name)
    h = 0.0012
    x0, x1, y0, y1 = -length / 2, length / 2, -width / 2, width / 2
    me.from_pydata([(x0, y0, 0), (x1, y0, 0), (x1, y1, 0), (x0, y1, 0),
                    (x0, y0, h), (x1, y0, h), (x1, y1, h), (x0, y1, h)], [],
                   [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = location
    m, b, nt = _principled(name)
    N, L = nt.nodes, nt.links
    b.inputs["Roughness"].default_value = 0.35
    b.inputs["Metallic"].default_value = 0.6
    tc, sep = N.new("ShaderNodeTexCoord"), N.new("ShaderNodeSeparateXYZ")
    L.new(tc.outputs["Object"], sep.inputs[0])

    def node(op, a, b_=None, val=None):
        n = N.new("ShaderNodeMath")
        n.operation = op
        L.new(a, n.inputs[0])
        if b_ is not None:
            L.new(b_, n.inputs[1])
        elif val is not None:
            n.inputs[1].default_value = val
        return n.outputs[0]

    yn = node("ADD", node("DIVIDE", sep.outputs["Y"], val=width), val=0.5)   # 0 front edge .. 1 back edge
    marks = None
    for per_m, thick, reach in ((100, 0.09, 0.38), (20, 0.02, 0.55), (10, 0.009, 0.75)):   # ticks from the front edge
        tick = node("LESS_THAN", node("FRACT", node("MULTIPLY", sep.outputs["X"], val=per_m)), val=thick)
        tick = node("MULTIPLY", tick, node("LESS_THAN", yn, val=reach))
        marks = tick if marks is None else node("MAXIMUM", marks, tick)
    mix = N.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs[6].default_value = (*color, 1)
    mix.inputs[7].default_value = (0.02, 0.02, 0.02, 1)
    L.new(marks, mix.inputs["Factor"])
    L.new(mix.outputs[2], b.inputs["Base Color"])
    me.materials.append(m)
    return ob


def instance(src, name, location, scale=1.0, rotation=(0, 0, 0), mat=None):
    ob = bpy.data.objects.new(name, src.data)
    bpy.context.scene.collection.objects.link(ob)
    ob.location, ob.rotation_euler = location, rotation
    ob.scale = (scale, scale, scale)
    if mat is not None:
        ob.material_slots[0].link = "OBJECT"
        ob.material_slots[0].material = mat
    return ob


def empty(name, location, parent=None):
    ob = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = location
    if parent is not None:
        ob.parent = parent
    return ob


def studio(sc, wall_color=(0.05, 0.075, 0.09), floor_rough=0.32, key=600, rim=450, fill=120, size=8.0):
    """Infinite cyclorama (floor curving up into a back wall) with a large
    softbox key, a cool rim light from behind and a soft fill."""
    w = bpy.data.worlds.new("world")
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.01, 0.012, 0.016, 1)
    # cyclorama profile in (y, z): floor -> quarter circle -> wall
    prof = [(y, 0.0) for y in (-size, -2.0, 0.0)]
    r = 1.6
    for k in range(1, 13):
        a = math.pi / 2 * k / 12
        prof.append((r * math.sin(a), r - r * math.cos(a)))
    prof += [(r, r + 2.0), (r, size)]
    verts, faces = [], []
    for x in (-size, size):
        verts += [(x, y + 1.2, z) for y, z in prof]
    n = len(prof)
    for k in range(n - 1):
        faces.append((k, k + 1, n + k + 1, n + k))
    me = bpy.data.meshes.new("cyc")
    me.from_pydata(verts, [], faces)
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new("cyclorama", me)
    sc.collection.objects.link(ob)
    me.materials.append(mat_basic("cyc", wall_color, rough=floor_rough))

    def area(name, loc, energy, sz, color=(1, 1, 1)):
        l = bpy.data.lights.new(name, "AREA")
        l.energy, l.size, l.color = energy, sz, color
        o = bpy.data.objects.new(name, l)
        o.location = loc
        sc.collection.objects.link(o)
        c = o.constraints.new("TRACK_TO")
        c.target = empty(name + "_aim", (0.2, 0, 0.05))
        c.track_axis, c.up_axis = "TRACK_NEGATIVE_Z", "UP_Y"
        return o

    area("key", (-1.6, -2.2, 2.6), key, 2.4, (1.0, 0.97, 0.92))
    area("rim", (1.9, 2.0, 1.8), rim, 1.6, (0.55, 0.78, 1.0))
    area("fill", (2.4, -2.6, 0.9), fill, 3.0)
    return ob


# ── camera ────────────────────────────────────────────────────────────────────
def camera(sc, lens=50):
    cd = bpy.data.cameras.new("cam")
    cd.lens = lens
    cd.sensor_fit = "VERTICAL"
    cd.sensor_height = 24.0
    cd.clip_start = 0.002
    cam = bpy.data.objects.new("cam", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    target = empty("cam_target", (0, 0, 0))
    c = cam.constraints.new("TRACK_TO")
    c.target = target
    c.track_axis, c.up_axis = "TRACK_NEGATIVE_Z", "UP_Y"
    cd.dof.use_dof = True
    cd.dof.focus_object = target
    return cam, target


def shot(cam, target, frame, at, dist, elev_deg=10.0, azim_deg=0.0, lens=50, fstop=4.0, interp="BEZIER"):
    """Keyframe the camera to look at `at` from `dist` metres away."""
    e, a = math.radians(elev_deg), math.radians(azim_deg)
    cam.location = (at[0] + dist * math.cos(e) * math.sin(a), at[1] - dist * math.cos(e) * math.cos(a),
                    at[2] + dist * math.sin(e))
    target.location = at
    cam.data.lens = lens
    cam.data.dof.aperture_fstop = fstop
    for ob, path in ((cam, "location"), (target, "location")):
        ob.keyframe_insert(path, frame=frame)
    cam.data.keyframe_insert("lens", frame=frame)
    cam.data.dof.keyframe_insert("aperture_fstop", frame=frame)
    for ob in (cam, target, cam.data):
        if ob.animation_data and ob.animation_data.action:
            _set_interp(ob.animation_data.action, frame, interp)


def _set_interp(action, frame, interp):
    curves = getattr(action, "fcurves", None)
    if curves is None:      # Blender 5 layered actions
        curves = [fc for layer in action.layers for strip in layer.strips
                  for bag in strip.channelbags for fc in bag.fcurves]
    for fc in curves:
        for kp in fc.keyframe_points:
            if int(round(kp.co[0])) == frame:
                kp.interpolation = interp


def pop_in(ob, frame, dur=4, final_scale=1.0):
    """Scale an object up from zero with a small overshoot."""
    for f, s in ((frame - 1, 0.0), (frame, 0.001), (frame + dur, final_scale * 1.12),
                 (frame + dur + 3, final_scale)):
        ob.scale = (s, s, s)
        ob.keyframe_insert("scale", frame=max(0, f))


# ── output ────────────────────────────────────────────────────────────────────
def export_anchors(sc, cam, named, path):
    """Per-frame 2D pixel positions (in the render resolution) of named
    objects, so the main pipeline can draw labels / brackets exactly on them."""
    W, H = sc.render.resolution_x, sc.render.resolution_y
    out = {}
    for f in range(sc.frame_start, sc.frame_end + 1):
        sc.frame_set(f)
        row = {}
        for name, ob in named.items():
            v = world_to_camera_view(sc, cam, ob.matrix_world.translation)
            row[name] = [round(v.x * W, 1), round((1 - v.y) * H, 1), round(v.z, 4)]
        out[f] = row
    with open(path, "w") as fh:
        json.dump({"res": [W, H], "fps": sc.render.fps, "frames": out}, fh)


def render(sc, out_dir, start, end):
    sc.frame_start, sc.frame_end = start, end
    sc.render.use_overwrite = False          # frames already on disk are skipped (resume / partial re-renders)
    sc.render.filepath = out_dir.rstrip("/") + "/f_"
    bpy.ops.render.render(animation=True)
