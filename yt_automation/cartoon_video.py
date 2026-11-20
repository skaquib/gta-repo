"""
cartoon_video.py — Shared engine for long-form cartoon explainers built with
cartoon_kit.py (first used by run_cat_thinks_long.py, 2026-11-02).

A video is a list of SEGMENTS: {"line", optional "say"/"chapter", "shots": [...]}.
Each narrated line gets 1-4 shots; long shots auto-cut to close-ups of each
character in turn, so the picture changes about every 2.5 s (the Quark
lesson, notes/2026-11-02_quark_case_study.md).

Shot DSL:
    shot(bg, chars=[cat(...), dog(...), hum(...), mouse(x, y)], props=[...], late=[...],
         zoom=(z0, z1, cx, cy), move={char_index: (dx, dy)})
    props: ("text"|"heart"|"bubble"|"waves"|"scent"|"q"|"ring"|"clock"|"bowl"|"laptop"|
            "book"|"speaker"|"mark"|"drops"|"ears"|"sub"|"scanner"|"brain"|"box"|"pill", ...)
    T("HEADLINE") = screen-space headline, drawn after the camera zoom.
    late = characters drawn on top of the props (e.g. inside a thought bubble).
"""
import math
import sys

import numpy as np
from PIL import Image

import cartoon_kit as ck
import motion_shorts as ms
import sfx


def cat(pose="sit", x=960, y=1000, s=0.8, flip=False, **kw):
    return ("cat", tuple(sorted(dict(pose=pose, **kw).items())), x, y, s, flip)


def dog(pose="sit", x=960, y=1000, s=0.8, flip=False, **kw):
    return ("dog", tuple(sorted(dict(pose=pose, **kw).items())), x, y, s, flip)


def hum(pose="stand", x=960, y=1000, s=0.85, flip=False, **kw):
    return ("human", tuple(sorted(dict(pose=pose, **kw).items())), x, y, s, flip)


def mouse(x, y, s=0.8):
    return ("mouse", (), x, y, s, False)


def shot(bg, chars=(), props=(), late=(), zoom=(1.0, 1.06, 0.5, 0.55), move=None):
    return dict(bg=bg, chars=list(chars), props=list(props), late=list(late), zoom=zoom, move=move or {})


def T(s, x=960, y=150, size=140, color=(255, 214, 70)):
    """Headline in SCREEN space: drawn after the camera zoom, so zooms never crop it."""
    return ("stext", x, y, s, size, color)


# ── sprites ───────────────────────────────────────────────────────────────────
def _sprite(spec, t, blink=False, paw=0):
    kind, kw, *_ = spec
    kw = dict(kw)
    if kind in ("cat", "dog", "human") and blink and kw.get("eyes", "open") == "open":
        kw["eyes"] = "closed"
    if kind == "cat":
        if kw.get("pose") == "knead":
            kw["paw"] = paw
        return ck.cat_sprite(**kw)
    if kind == "dog":
        if kw.get("tail") == "wag":                      # a happy, wagging tail (~4 swings a second)
            kw["tail"] = "wagL" if int(t * 8) % 2 else "wagR"
        return ck.dog_sprite(**kw)
    if kind == "human":
        return ck.human_sprite(**kw)
    return ck.mouse_sprite()


_scaled = {}


def _place(canvas, spec, t, idx, dx=0.0, dy=0.0, blink=False, paw=0):
    kind, kw, x, y, s, flip = spec
    spr = _sprite(spec, t, blink, paw)
    key = (id(spr[0]), s, flip)
    if key not in _scaled:
        im, (ax, ay) = spr
        if flip:
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
            ax = im.width - ax
        im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
        _scaled[key] = (im, (ax * s, ay * s))
    im, (ax, ay) = _scaled[key]
    animal = kind in ("cat", "dog")
    bob = 3 * math.sin(2 * math.pi * 1.1 * t + idx * 1.7) if animal else 1.5 * math.sin(2 * math.pi * 0.7 * t + idx)
    canvas.alpha_composite(im, (int(x + dx - ax), int(y + dy - ay + bob)))


def _draw_props(d, props):
    for p in props:
        k = p[0]
        if k == "text":
            ck.text(d, p[1], p[2], p[3], p[4], fill=p[5])
        elif k == "heart":
            ck.heart(d, p[1], p[2], p[3])
        elif k == "bubble":
            _, x, y, w, h, s, size, tail, *think = p
            ck.bubble(d, x, y, w, h, s, size, tail, think=bool(think and think[0]))
        elif k == "waves":
            ck.sound_waves(d, p[1], p[2], p[3] if len(p) > 3 else 3, p[4] if len(p) > 4 else 1)
        elif k == "scent":
            ck.scent(d, p[1], p[2], p[3], *(p[4:6] if len(p) > 4 else ()))
        elif k == "q":
            ck.qmark(d, p[1], p[2], p[3])
        elif k == "ring":
            ck.percent_ring(d, p[1], p[2], p[3], p[4], p[5], p[6])
        elif k == "clock":
            ck.clock(d, p[1], p[2], p[3], p[4], p[5])
        elif k == "bowl":
            ck.bowl(d, p[1], p[2])
        elif k == "laptop":
            ck.laptop(d, p[1], p[2], p[3])
        elif k == "book":
            ck.book(d, p[1], p[2], p[3])
        elif k == "speaker":
            ck.speaker(d, p[1], p[2], p[3])
        elif k == "mark":
            ck.mark(d, p[1], p[2], p[3], p[4])
        elif k == "drops":
            ck.drops(d, p[1], p[2])
        elif k == "ears":
            ck.cat_ears(d, p[1], p[2], p[3])
        elif k == "dogears":
            ck.dog_ears(d, p[1], p[2], p[3])
        elif k == "sub":
            ck.subscribe(d, p[1], p[2])
        elif k == "scanner":
            ck.scanner(d, p[1], p[2], p[3])
        elif k == "brain":
            ck.brain(d, p[1], p[2], p[3], p[4] if len(p) > 4 else None)
        elif k == "box":
            ck.puzzle_box(d, p[1], p[2], p[3])
        elif k == "pill":
            ck.pill(d, p[1], p[2], p[3], *(p[4:5]))


_overlays = {}


def _overlay(key, props):
    if key not in _overlays:
        ov, d = ck.overlay()
        _draw_props(d, props)
        _overlays[key] = ov.resize((ck.W, ck.H), Image.LANCZOS)
    return _overlays[key]


_stexts = {}


def _screen_text(key, props):
    if key not in _stexts:
        ov, d = ck.overlay()
        for q in props:
            ck.text(d, q[1], q[2], q[3], q[4], fill=q[5], sw=9)
        _stexts[key] = ov.resize((ck.W, ck.H), Image.LANCZOS)
    return _stexts[key]


def render_shot(sh, key, t, t_shot, dur, zoom=None):
    p = min(1.0, t_shot / max(dur, 0.1))
    c = ck.background(sh["bg"]).copy()
    blink = (t % 3.4) < 0.13
    paw = int(t * 3) % 2
    for i, spec in enumerate(sh["chars"]):
        dx, dy = sh["move"].get(i, (0, 0))
        e = ms.ease(p)
        _place(c, spec, t, i, dx * e, dy * e, blink, paw)
    world = [q for q in sh["props"] if q[0] != "stext"]
    if world or sh["late"]:
        ov = _overlay(key, world)
        fade = min(1.0, t_shot / 0.25)
        if fade < 1.0:
            ov = ov.copy()
            ov.putalpha(ov.getchannel("A").point(lambda v: int(v * fade)))
        c.alpha_composite(ov)
    ears = [q for q in sh["late"] if q[0] in ("ears", "dogears")]
    for i, spec in enumerate(q for q in sh["late"] if q[0] not in ("ears", "dogears")):
        _place(c, spec, t, i + 10, blink=blink)
    if ears:                                              # ears go on top of the late human
        c.alpha_composite(_overlay(key + ("ears",), ears))
    z0, z1, cx, cy = zoom or sh["zoom"]
    out = ck.camera(c, z0 + (z1 - z0) * ms.ease(p), cx, cy)
    st = [q for q in sh["props"] if q[0] == "stext"]
    if st:
        out.alpha_composite(_screen_text(key, st))
    return out


# ── whole-video helpers ───────────────────────────────────────────────────────
def frame_fn(segments, vid):
    """frame(t, i, t_in, starts) for motion_shorts.render_short."""
    def frame(t, i, t_in, starts):
        seg = segments[i]
        dur = (starts[i + 1] - starts[i]) if i + 1 < len(starts) else 3.0
        n = len(seg["shots"])
        k = min(n - 1, int(t_in / (dur / n)))
        sd = dur / n
        sh, ts = seg["shots"][k], t_in - k * sd
        # a new picture about every 2.5 s: long shots cut to a close-up of each character in turn
        nsub = max(1, round(sd / 2.6))
        sub = min(nsub - 1, int(ts / (sd / nsub)))
        zoom = None
        if sub and sh["chars"]:
            _, _, x, y, sc, _ = sh["chars"][(sub - 1) % len(sh["chars"])]
            zoom = (1.22, 1.3, x / ck.W, max(0.35, (y - 330 * sc) / ck.H))
        elif sub:
            zoom = (1.12, 1.2, 0.5, 0.5)
        return np.array(render_shot(sh, (vid, i, k), t, ts - sub * sd / nsub, sd / nsub, zoom).convert("RGB"))
    return frame


def section_sounds(segments):
    def sound_events(starts, total):
        ev = [(0.0, sfx.pop(0.35))]
        for k, seg in enumerate(segments):
            if seg.get("chapter") and k:
                ev.append((starts[k] - 0.05, sfx.whoosh(0.5, 0.25)))
        return ev
    return sound_events


def chapters_text(segments, starts):
    rows = []
    for seg, st in zip(segments, starts):
        if seg.get("chapter"):
            s = 0 if not rows else int(st)
            rows.append(f"{s // 60}:{s % 60:02d} {seg['chapter']}")
    return "\n".join(rows)


def preview(segments, path, cols=8):
    tiles = []
    for i, seg in enumerate(segments):
        for k, sh in enumerate(seg["shots"]):
            tiles.append(render_shot(sh, ("preview", i, k), 1.0, 0.6, 2.0).convert("RGB").resize((320, 180)))
    sheet = Image.new("RGB", (320 * cols, 180 * ((len(tiles) + cols - 1) // cols)), (0, 0, 0))
    for n, im in enumerate(tiles):
        sheet.paste(im, (320 * (n % cols), 180 * (n // cols)))
    sheet.save(path, quality=85)
    return len(tiles)


if __name__ == "__main__":
    sys.exit("library module: use a run_*_long.py script")
