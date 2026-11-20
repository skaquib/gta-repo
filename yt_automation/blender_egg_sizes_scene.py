"""
blender_egg_sizes_scene.py — Blender scene for "smallest to biggest egg"
(run_egg_sizes_blender_short.py drives it). Runs in the Blender env:

  /root/.venvs/blender/bin/python blender_egg_sizes_scene.py TIMING.json OUT_DIR [START END | anchors]

Real-scale eggs standing in a studio group shot (metres): vervain
hummingbird ~1 cm, chicken ~5.8 cm, ostrich ~15.5 cm, elephant bird ~32 cm.
The camera starts on the giant, whips down to a macro of the tiny egg, then
pulls back as each bigger egg is introduced; the ostrich and elephant bird
shells turn x-ray and fill with chicken eggs (24 and 150).
"""
import os
import sys
import json
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_kit as bk  # noqa: E402

FPS = 24
EGGS = {   # name: (length, radius, position x, y)
    "hb": (0.0098, 0.0034, 0.0, -0.178),        # sits on the ruler
    "ch": (0.058, 0.0215, 0.048, -0.128),
    "os": (0.155, 0.065, -0.10, -0.02),
    "el": (0.32, 0.115, 0.05, 0.12),
}


def fill_points(n, axes, center, seed):
    """n points packed inside an ellipsoid, filled from the bottom up."""
    rng = random.Random(seed)
    ax, ay, az = (a * 0.8 for a in axes)
    best = None
    for k in range(40):
        s = 0.3 + 0.02 * k
        pts = []
        steps = int(1 / s) + 2
        for i in range(-steps, steps + 1):
            for j in range(-steps, steps + 1):
                for m in range(-steps, steps + 1):
                    p = (i * s + (m % 2) * s / 2, j * s + (m % 2) * s / 2, m * s * 0.82)
                    if p[0] ** 2 + p[1] ** 2 + p[2] ** 2 <= 1.0:
                        pts.append(p)
        if len(pts) >= n:
            best = (s, pts)
        else:
            break
    s, pts = best
    pts.sort(key=lambda p: p[0] ** 2 + p[1] ** 2 + p[2] ** 2)
    pts = pts[:n]
    pts.sort(key=lambda p: (p[2], rng.random()))
    return [(center[0] + p[0] * ax, center[1] + p[1] * ay, center[2] + p[2] * az) for p in pts], s


def build(timing):
    st, total = timing["starts"], timing["total"]
    F = lambda t: int(round(t * FPS))
    d = [b - a for a, b in zip(st, st[1:] + [total])]
    sc = bk.new_scene(fps=FPS, res=(720, 1280), samples=8, frames=F(total) + 1)   # 8 spp + OIDN looks like 12, ~35% faster
    bk.studio(sc)

    mats = {
        "hb": bk.mat_shell("hb", (0.93, 0.92, 0.88), rough=0.35, sss=0.25),
        "ch": bk.mat_shell("ch", (0.72, 0.47, 0.30), speck=(0.45, 0.27, 0.16), speck_amount=0.5, speck_scale=220,
                           pits=0.08, pit_scale=900, rough=0.5, sss=0.1),
        "os": bk.mat_shell("os", (0.93, 0.89, 0.78), pits=0.25, pit_scale=380, rough=0.4, sss=0.12),
        "el": bk.mat_shell("el", (0.84, 0.74, 0.58), pits=0.18, pit_scale=260, rough=0.62, sss=0.06, mottle=0.35),
    }
    bk.ruler("ruler", 0.5, 0.022, (0.03, -0.178, 0.0))      # centimetre ticks: scale cue for the small eggs
    obj = {}
    for k, (L, R, x, y) in EGGS.items():
        obj[k] = bk.egg(k, L, R, mats[k], location=(x, y, 0), pointy=-0.11, lying=False)
    obj["hb"].location.z += 0.0012                              # on top of the ruler
    # label anchors: top / bottom of each egg, centres of the two big ones
    anchors = {}
    for k, (L, R, x, y) in EGGS.items():
        anchors[k + "_top"] = bk.empty(k + "_top", (x + R * 1.25, y, L))
        anchors[k + "_bot"] = bk.empty(k + "_bot", (x + R * 1.25, y, 0.0))
        anchors[k + "_c"] = bk.empty(k + "_c", (x, y, L / 2))

    # x-ray + fill with chicken eggs: ostrich (24) in segment 3, elephant bird (150) in segment 4
    pops = {}
    for k, seg, n, seed in (("os", 3, 24, 1), ("el", 4, 150, 2)):
        L, R, x, y = EGGS[k]
        on, full = F(st[seg] + 0.30 * d[seg]), F(st[seg] + 0.42 * d[seg])
        bk.xray_fade(mats[k], on, full, alpha=0.14)
        pts, spacing = fill_points(n, (R, R, L / 2), (x, y, L / 2), seed)
        scale = min(spacing * min(R, L / 2) * 0.62 / (EGGS["ch"][0] / 2), 1.0)
        t0, t1 = st[seg] + 0.45 * d[seg], st[seg] + 0.92 * d[seg]
        rng = random.Random(seed)
        times = []
        for m, p in enumerate(pts):
            t = t0 + (t1 - t0) * m / max(1, n - 1)
            mini = bk.instance(obj["ch"], f"{k}_mini{m}", (p[0], p[1], p[2] - EGGS["ch"][0] / 2 * scale), 0.0,
                               (rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5), rng.uniform(0, 6.28)))
            bk.pop_in(mini, F(t), dur=3, final_scale=scale)
            times.append(round(t, 3))
        pops[k] = times

    cam, target = bk.camera(sc)
    c = {k: (x, y, L / 2) for k, (L, R, x, y) in EGGS.items()}
    hb, ch, os_, el = c["hb"], c["ch"], c["os"], c["el"]
    mid_hc = ((hb[0] + ch[0]) / 2, (hb[1] + ch[1]) / 2, 0.018)
    group = (0.02, 0.0, 0.14)
    keys = [   # (time, at, dist, elev, azim, lens, fstop)
        (0.0, (0.03, 0.05, 0.14), 0.75, 6, -12, 35, 5.6),             # hook: the giant
        (st[1] - 0.45, (0.04, 0.06, 0.15), 0.62, 8, -4, 35, 5.6),
        (st[1] + 0.15, hb, 0.085, 20, -8, 50, 8),                       # whip down to the tiny egg (on the ruler)
        (st[2] - 0.2, hb, 0.07, 18, 6, 50, 8),
        (st[2] + 0.6, mid_hc, 0.24, 12, -5, 35, 8),                     # + chicken egg (both in frame)
        (st[3] - 0.1, mid_hc, 0.23, 12, 3, 35, 8),
        (st[3] + 0.6, (-0.04, -0.06, 0.06), 0.55, 12, -4, 50, 8),       # + ostrich
        (st[3] + 0.42 * d[3], os_, 0.40, 10, -12, 50, 8),               # ostrich x-ray fills
        (st[4] - 0.1, os_, 0.38, 10, -4, 50, 8),
        (st[4] + 0.8, group, 1.0, 12, 0, 35, 8),                        # + elephant bird
        (st[4] + 0.45 * d[4], el, 0.75, 10, 8, 35, 8),                  # elephant bird x-ray fills
        (st[5], el, 0.72, 10, 12, 35, 8),
        (st[5] + 0.6, group, 1.0, 14, -8, 35, 8),                       # CTA: everything
        (total, group, 0.95, 14, 8, 35, 8),
    ]
    times = [k[0] for k in keys]
    assert times == sorted(times), f"camera keys out of order: {times}"
    for t, at, dist, elev, azim, lens, fstop in keys:
        bk.shot(cam, target, F(t), at, dist, elev, azim, lens, fstop)
    return sc, cam, anchors, pops


if __name__ == "__main__":
    timing_path, out_dir = sys.argv[1], sys.argv[2]
    timing = json.load(open(timing_path))
    sc, cam, anchors, pops = build(timing)
    os.makedirs(out_dir, exist_ok=True)
    if sys.argv[3:] == ["anchors"]:
        bk.export_anchors(sc, cam, anchors, os.path.join(out_dir, "anchors.json"))
        with open(os.path.join(out_dir, "pops.json"), "w") as fh:
            json.dump(pops, fh)
        print("ANCHORS OK", sc.frame_end + 1, "frames")
    else:
        start, end = int(sys.argv[3]), int(sys.argv[4])
        bk.render(sc, out_dir, start, min(end, sc.frame_end))
        print("RENDERED", start, end)
