"""
blender_dummy_look.py -- before/after look-test of the crash-test dummy (v1 vs v2), same pose, light and camera,
for the owner's approval before v2 is used in a Short (rule 14).

  /root/.venvs/blender/bin/python blender_dummy_look.py OUT.png v1|v2 full|head [SAMPLES]

Studio: dark backdrop, warm key, cool fill and a strong rim light behind him (so he separates from any background,
which v1 did not in the hail storm).
"""
import math
import os
import sys

import bpy  # noqa: I001

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_kit as bk  # noqa: E402
import blender_pitches as bp  # noqa: E402

out, ver, shot = sys.argv[1:4]
samples = int(sys.argv[4]) if len(sys.argv) > 4 else 48

sc = bk.new_scene(fps=24, res=(720, 1280), samples=samples, frames=1)
bp.world(sc, (0.02, 0.025, 0.035), 1.0)
floor = bp.box("floor", (12, 12, 0.02), (0, 0, -0.01), bp.mat("floor", (0.05, 0.05, 0.055), rough=0.7))
wall = bp.box("wall", (12, 0.02, 6), (0, 3.0, 3), bp.mat("wall", (0.035, 0.04, 0.05), rough=0.9))
bp.light("key", "AREA", (-2.2, -2.4, 2.8), 300, size=1.6, color=(1.0, 0.93, 0.84), aim=(0, 0, 1.2))
bp.light("fill", "AREA", (2.6, -1.8, 1.6), 120, size=2.0, color=(0.75, 0.85, 1.0), aim=(0, 0, 1.1))
bp.light("rim", "AREA", (0.8, 2.2, 2.4), 900, size=0.8, color=(1.0, 0.97, 0.92), aim=(0, 0, 1.4))

P = bp.build_dummy_v2() if ver == "v2" else bp.build_dummy()
rots = {"sh-1": (-15, 22, 0), "el-1": (-45, 0, 0), "sh1": (-15, -22, 0), "el1": (-45, 0, 0),
        "head": (-4, 0, 16), "chest": (0, 0, -8), "hip-1": (4, 0, 0), "hip1": (-4, 0, 0)}
for k, r in rots.items():
    P[k].rotation_euler = tuple(math.radians(a) for a in r)

cd = bpy.data.cameras.new("cam")
cd.sensor_fit, cd.sensor_height = "VERTICAL", 24.0
cam = bpy.data.objects.new("cam", cd)
sc.collection.objects.link(cam)
sc.camera = cam
if shot == "head":
    cam.location, aim, cd.lens = (-0.45, -1.25, 1.8), (0.0, 0.0, 1.74), 55
else:
    cam.location, aim, cd.lens = (-1.35, -2.75, 1.3), (0.0, 0.0, 0.98), 36
c = cam.constraints.new("TRACK_TO")
c.target = bp.pivot("cam_aim", aim)
c.track_axis, c.up_axis = "TRACK_NEGATIVE_Z", "UP_Y"
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print("saved", out, flush=True)
