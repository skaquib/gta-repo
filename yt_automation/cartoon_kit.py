"""
cartoon_kit.py — Flat 2D cartoon building blocks for long-form explainers
(FramedFacts, 2026-11-02).

Why: the Quark case study (notes/2026-11-02_quark_case_study.md) shows that
simple, bright cartoon visuals that change every ~2 s can carry 5-7 minute
animal-psychology videos to 100K-1.8M views. This kit draws our OWN art in
code (no AI images, no other channel's assets): thick dark outlines, flat
fills, big friendly eyes.

Everything is drawn at S x resolution and downscaled (smooth edges).
Coordinates are in the 1920x1080 output space unless noted.

  bg = background("living")                      # cached RGBA 1920x1080
  cat = cat_sprite(pose="walk", tail="up", eyes="open", mouth="smile")
  human = human_sprite(pose="stand", shirt=(70, 130, 220))
  frame = compose(bg, [(cat, x, y_feet, scale, flip), ...], props=[...])
"""
import math
import os
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont

W, H, S = 1920, 1080, 2
OUT = (45, 35, 40)
LW = 7
HERE = os.path.dirname(os.path.abspath(__file__))
FONT_BIG = os.path.join(HERE, "fonts", "BebasNeue-Regular.ttf")
FONT_UI = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

ORANGE, CREAM, PINK = (243, 153, 66), (255, 238, 214), (242, 128, 140)
SKIN, HAIR = (246, 200, 165), (70, 46, 36)


def _s(v):
    return [c * S for c in v] if isinstance(v, (list, tuple)) else v * S


def _ell(d, cx, cy, rx, ry, fill, out=OUT, lw=LW):
    d.ellipse(_s((cx - rx, cy - ry, cx + rx, cy + ry)), fill=fill, outline=out, width=lw * S if out else 0)


def _poly(d, pts, fill, out=OUT, lw=LW):
    d.polygon([(x * S, y * S) for x, y in pts], fill=fill, outline=out, width=lw * S if out else 0)


def _rrect(d, box, r, fill, out=OUT, lw=LW):
    d.rounded_rectangle(_s(box), r * S, fill=fill, outline=out, width=lw * S if out else 0)


def _stroke(d, pts, color, width, out=OUT, lw=LW):
    """Thick rounded stroke with an outline (tails, arms, legs)."""
    P = [(x * S, y * S) for x, y in pts]
    if out:
        d.line(P, fill=out, width=(width + 2 * lw) * S, joint="curve")
        for x, y in (P[0], P[-1]):
            r = (width / 2 + lw) * S
            d.ellipse((x - r, y - r, x + r, y + r), fill=out)
    d.line(P, fill=color, width=width * S, joint="curve")
    for x, y in (P[0], P[-1]):
        r = width / 2 * S
        d.ellipse((x - r, y - r, x + r, y + r), fill=color)


def _line(d, pts, color=OUT, width=5):
    d.line([(x * S, y * S) for x, y in pts], fill=color, width=width * S, joint="curve")


def _bezier(p0, p1, p2, n=24):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in (i / n for i in range(n + 1))]


def _finish(img):
    """Downscale an S-x canvas to 1x and crop to content; returns (sprite, anchor offset)."""
    small = img.resize((img.width // S, img.height // S), Image.LANCZOS)
    box = small.getbbox()
    return small.crop(box), box


# ── faces ─────────────────────────────────────────────────────────────────────
def _cat_face(d, cx, cy, r, eyes="open", mouth="smile", look=(0, 0)):
    ex, ey, er = r * 0.42, cy - r * 0.08, r * 0.24
    for sx in (-1, 1):
        x = cx + sx * ex
        if eyes == "open":
            _ell(d, x, ey, er * 0.9, er, (255, 255, 255), lw=5)
            _ell(d, x + look[0] * er * 0.3, ey + look[1] * er * 0.3 + er * 0.1, er * 0.52, er * 0.62, (35, 30, 35), out=None)
            _ell(d, x + look[0] * er * 0.3 - er * 0.18, ey - er * 0.18, er * 0.17, er * 0.17, (255, 255, 255), out=None)
        elif eyes == "half":      # slow blink: soft, relaxed half-closed eyes
            d.chord(_s((x - er * 0.9, ey - er * 0.5, x + er * 0.9, ey + er)), 0, 180, fill=(255, 255, 255),
                    outline=OUT, width=5 * S)
            _ell(d, x, ey + er * 0.45, er * 0.42, er * 0.3, (35, 30, 35), out=None)
            _line(d, _bezier((x - er * 0.95, ey + er * 0.25), (x, ey + er * 0.05), (x + er * 0.95, ey + er * 0.25), 10),
                  OUT, 6)
        else:                     # closed, happy
            _line(d, _bezier((x - er, ey + er * 0.2), (x, ey - er * 0.7), (x + er, ey + er * 0.2), 10), OUT, 6)
    ny = cy + r * 0.22
    _poly(d, [(cx - r * 0.1, ny - r * 0.05), (cx + r * 0.1, ny - r * 0.05), (cx, ny + r * 0.07)], PINK, lw=4)
    if mouth == "open":
        _ell(d, cx, ny + r * 0.26, r * 0.17, r * 0.2, (150, 40, 60), lw=5)
        _ell(d, cx, ny + r * 0.36, r * 0.1, r * 0.07, PINK, out=None)
    else:
        for sx in (-1, 1):
            _line(d, _bezier((cx, ny + r * 0.07), (cx + sx * r * 0.06, ny + r * 0.2), (cx + sx * r * 0.17, ny + r * 0.1), 8),
                  OUT, 5)
    for sx in (-1, 1):
        for k in (-1, 0, 1):
            _line(d, [(cx + sx * r * 0.32, ny + r * 0.08 + k * r * 0.07), (cx + sx * r * 0.85, ny + k * r * 0.13)],
                  OUT, 3)


def _stripe(color):
    return tuple(int(c * 0.82) for c in color)


def _cat_head(d, cx, cy, r, color, eyes, mouth, look=(0, 0), stripes=True):
    for sx in (-1, 1):   # ears
        _poly(d, [(cx + sx * r * 0.85, cy - r * 0.35), (cx + sx * r * 0.62, cy - r * 1.15), (cx + sx * r * 0.18, cy - r * 0.8)],
              color)
        _poly(d, [(cx + sx * r * 0.7, cy - r * 0.45), (cx + sx * r * 0.6, cy - r * 0.92), (cx + sx * r * 0.33, cy - r * 0.72)],
              PINK, out=None)
    _ell(d, cx, cy, r, r * 0.9, color)
    _ell(d, cx, cy + r * 0.32, r * 0.48, r * 0.33, CREAM, out=None)
    if stripes:
        for k in (-1, 0, 1):
            _line(d, [(cx + k * r * 0.16, cy - r * 0.86), (cx + k * r * 0.12, cy - r * 0.6)], _stripe(color), 7)
    _cat_face(d, cx, cy, r, eyes, mouth, look)


# ── cats ──────────────────────────────────────────────────────────────────────
@lru_cache(maxsize=256)
def cat_sprite(pose="walk", tail="up", eyes="open", mouth="smile", color=ORANGE, kitten=False, paw=0, look=(0, 0)):
    """Returns (RGBA sprite, (anchor_x, anchor_y)) -- anchor = between the feet.
    poses: walk (side, faces right), sit (front), lie (side, faces right),
    knead (front, on a lap: paws alternate with `paw` 0/1), rub (side, head down)."""
    img = Image.new("RGBA", (700 * S, 700 * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    dark = tuple(int(c * 0.86) for c in color)
    hs = 1.25 if kitten else 1.0
    if pose in ("walk", "rub"):
        bx, by = 300, 430
        tail_pts = {"up": [(170, 420), (120, 300), (150, 170)], "down": [(170, 430), (90, 470), (60, 560)],
                    "curl": [(170, 420), (90, 360), (130, 280)]}[tail]
        _stroke(d, _bezier(*tail_pts), color, 34)
        for lx in (205, 395):                       # far legs
            _rrect(d, (lx, 470, lx + 42, 600), 18, dark)
        _ell(d, bx, by, 150, 82, color)
        for k in range(3):
            _line(d, _bezier((230 + k * 45, by - 78), (245 + k * 45, by - 40), (235 + k * 45, by - 8), 8), _stripe(color), 8)
        for lx in (235, 425):                       # near legs
            _rrect(d, (lx, 480, lx + 44, 610), 18, color)
            _ell(d, lx + 22, 606, 30, 14, color, lw=5)
        hx, hy = (480, 330) if pose == "walk" else (470, 420)
        _cat_head(d, hx, hy, 105 * hs, color, eyes, mouth, look)
    elif pose == "lie":
        _stroke(d, _bezier((150, 520), (70, 540), (60, 470)), color, 32)
        _ell(d, 330, 520, 200, 80, color)
        _ell(d, 360, 560, 120, 30, CREAM, out=None)
        for k in range(3):
            _line(d, _bezier((240 + k * 55, 445), (255 + k * 55, 485), (245 + k * 55, 515), 8), _stripe(color), 8)
        _ell(d, 505, 590, 55, 20, color, lw=5)
        _cat_head(d, 540, 450, 100 * hs, color, eyes, mouth, look)
    else:                                           # sit / knead (front view)
        cx = 350
        if pose == "sit":
            _stroke(d, _bezier((470, 600), (590, 590), (560, 460)), color, 32)
        _ell(d, cx, 470, 150 * (0.85 if kitten else 1), 150 * (0.85 if kitten else 1), color)
        _ell(d, cx, 500, 85, 100, CREAM, out=None)
        if pose == "knead":
            for sx, up in ((-1, paw == 0), (1, paw == 1)):
                _rrect(d, (cx + sx * 55 - 32, 555 - (40 if up else 0), cx + sx * 55 + 32, 640 - (40 if up else 0)), 26, color)
        else:
            for sx in (-1, 1):
                _ell(d, cx + sx * 58, 612, 44, 26, color, lw=6)
        _cat_head(d, cx, 290 + (25 if kitten else 0), 120 * hs, color, eyes, mouth, look)
    spr, box = _finish(img)
    feet_y = {"walk": 625, "rub": 625, "lie": 610, "sit": 640, "knead": 640}[pose]
    return spr, (350 - box[0], feet_y - box[1])


@lru_cache(maxsize=64)
def mouse_sprite():
    img = Image.new("RGBA", (300 * S, 200 * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    _stroke(d, _bezier((70, 140), (20, 150), (30, 100)), (180, 160, 170), 8)
    _ell(d, 140, 130, 75, 45, (160, 160, 170))
    _ell(d, 200, 95, 30, 30, (160, 160, 170))
    _ell(d, 222, 120, 9, 9, PINK, out=None)
    _line(d, [(195, 115), (210, 110)], OUT, 4)
    _line(d, [(196, 106), (206, 112)], OUT, 4)
    spr, box = _finish(img)
    return spr, (150 - box[0], 175 - box[1])


# ── dogs ──────────────────────────────────────────────────────────────────────
GOLDEN, WOLF_GREY = (232, 178, 96), (128, 132, 142)


def _dog_head(d, cx, cy, r, color, ear, eyes, mouth, look, brows):
    ear_c = tuple(int(c * 0.78) for c in color)
    if ear == "pointy":
        for sx in (-1, 1):
            _poly(d, [(cx + sx * r * 0.85, cy - r * 0.3), (cx + sx * r * 0.7, cy - r * 1.25), (cx + sx * r * 0.2, cy - r * 0.75)], color)
            _poly(d, [(cx + sx * r * 0.72, cy - r * 0.45), (cx + sx * r * 0.66, cy - r * 1.0), (cx + sx * r * 0.36, cy - r * 0.72)],
                  (235, 210, 210), out=None)
    _ell(d, cx, cy, r, r * 0.88, color)
    if ear == "floppy":
        for sx in (-1, 1):
            _ell(d, cx + sx * r * 0.95, cy + r * 0.05, r * 0.32, r * 0.62, ear_c)
    wolfish = ear == "pointy"
    if wolfish:                               # wolves: a longer, lighter muzzle
        _ell(d, cx, cy + r * 0.52, r * 0.46, r * 0.42, (225, 222, 218))
    else:
        _ell(d, cx, cy + r * 0.38, r * 0.52, r * 0.38, (252, 236, 206), out=None)
    ex, ey, er = r * 0.38, cy - r * 0.12, r * 0.2
    for sx in (-1, 1):
        x = cx + sx * ex
        if eyes == "closed":
            _line(d, _bezier((x - er, ey + er * 0.2), (x, ey - er * 0.7), (x + er, ey + er * 0.2), 10), OUT, 6)
        else:
            big = 1.25 if eyes == "puppy" else 1.0
            _ell(d, x, ey, er * 0.95 * big, er * big, (255, 255, 255), lw=5)
            if wolfish:                       # amber wolf eyes
                _ell(d, x + look[0] * er * 0.3, ey + look[1] * er * 0.3 + er * 0.1, er * 0.75, er * 0.8, (225, 170, 60), out=None)
                _ell(d, x + look[0] * er * 0.3, ey + look[1] * er * 0.3 + er * 0.1, er * 0.35, er * 0.42, (30, 24, 20), out=None)
            else:
                _ell(d, x + look[0] * er * 0.3, ey + look[1] * er * 0.3 + er * 0.1, er * 0.6 * big, er * 0.68 * big, (40, 28, 24), out=None)
            _ell(d, x + look[0] * er * 0.3 - er * 0.2, ey - er * 0.2, er * 0.2, er * 0.2, (255, 255, 255), out=None)
        if brows or eyes == "puppy":      # raised inner eyebrows: "puppy dog eyes"
            _line(d, [(x - sx * er * 1.0, ey - er * 1.6), (x + sx * er * 0.9, ey - er * 1.15)], OUT, 6)
    ny = cy + r * (0.36 if wolfish else 0.2)
    _ell(d, cx, ny, r * 0.17, r * 0.12, (35, 28, 30), lw=4)
    if mouth == "tongue":
        _rrect(d, (cx - r * 0.12, ny + r * 0.2, cx + r * 0.12, ny + r * 0.55), r * 0.1, (240, 110, 130), lw=5)
        _line(d, _bezier((cx - r * 0.25, ny + r * 0.16), (cx, ny + r * 0.3), (cx + r * 0.25, ny + r * 0.16), 10), OUT, 5)
    elif mouth == "open":
        _ell(d, cx, ny + r * 0.32, r * 0.2, r * 0.18, (150, 40, 60), lw=5)
    else:
        for sx in (-1, 1):
            _line(d, _bezier((cx, ny + r * 0.1), (cx + sx * r * 0.08, ny + r * 0.26), (cx + sx * r * 0.22, ny + r * 0.16), 8), OUT, 5)


@lru_cache(maxsize=256)
def dog_sprite(pose="sit", tail="up", eyes="open", mouth="tongue", color=GOLDEN, ear="floppy", puppy=False,
               look=(0, 0), brows=False):
    """Returns (RGBA sprite, anchor at the feet). poses: sit (front), walk (side, faces right), lie (side).
    tail: up / wagL / wagR / down (swap wagL/wagR for a wagging tail)."""
    img = Image.new("RGBA", (700 * S, 700 * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    dark = tuple(int(c * 0.86) for c in color)
    hs = 1.2 if puppy else 1.0
    cream = (252, 236, 206)
    if pose == "walk":
        tip = {"up": (120, 290), "wagL": (90, 320), "wagR": (150, 280), "down": (80, 520)}[tail]
        _stroke(d, _bezier((175, 410), (130, 380), tip), color, 30)
        for lx in (200, 400):
            _rrect(d, (lx, 470, lx + 46, 605), 20, dark)
        _ell(d, 305, 430, 160, 85, color)
        _ell(d, 330, 480, 100, 30, cream, out=None)
        for lx in (230, 430):
            _rrect(d, (lx, 480, lx + 48, 612), 20, color)
            _ell(d, lx + 24, 608, 32, 15, color, lw=5)
        _dog_head(d, 490, 330, 110 * hs, color, ear, eyes, mouth, look, brows)
    elif pose == "lie":
        tip = {"up": (60, 470), "wagL": (40, 500), "wagR": (70, 450), "down": (40, 560)}[tail]
        _stroke(d, _bezier((150, 530), (90, 540), tip), color, 28)
        _ell(d, 330, 530, 200, 78, color)
        _ell(d, 360, 570, 120, 26, cream, out=None)
        for x in (470, 540):
            _ell(d, x, 600, 52, 20, color, lw=5)
        _dog_head(d, 540, 450, 105 * hs, color, ear, eyes, mouth, look, brows)
    else:
        cx = 350
        tip = {"up": (560, 430), "wagL": (540, 400), "wagR": (590, 470), "down": (560, 610)}[tail]
        _stroke(d, _bezier((460, 600), (560, 600), tip), color, 30)
        _ell(d, cx, 470, 140 * (0.85 if puppy else 1), 150 * (0.85 if puppy else 1), color)
        _ell(d, cx, 500, 75, 105, cream, out=None)
        for sx in (-1, 1):
            _rrect(d, (cx + sx * 55 - 28, 470, cx + sx * 55 + 28, 630), 22, color)
            _ell(d, cx + sx * 58, 628, 42, 22, color, lw=6)
        _dog_head(d, cx, 290 + (25 if puppy else 0), 125 * hs, color, ear, eyes, mouth, look, brows)
    spr, box = _finish(img)
    feet_y = {"walk": 625, "lie": 620, "sit": 650}[pose]
    return spr, (350 - box[0], feet_y - box[1])


# ── science props ─────────────────────────────────────────────────────────────
def scanner(d, x, y, r=330):
    """A brain scanner (MRI) ring with a bed through it."""
    _ell(d, x, y, r, r, (235, 238, 245))
    _ell(d, x, y, r * 0.55, r * 0.55, (70, 80, 110))
    _rrect(d, (x - r * 1.5, y + r * 0.15, x + r * 0.9, y + r * 0.35), 18, (200, 205, 215))


def brain(d, x, y, size=220, glow=None):
    if glow:
        _ell(d, x, y, size * 0.75, size * 0.62, glow, out=None)
    _ell(d, x, y, size * 0.55, size * 0.42, (245, 175, 190))
    for k in range(4):
        _line(d, _bezier((x - size * 0.45 + k * size * 0.25, y - size * 0.3), (x - size * 0.3 + k * size * 0.25, y),
                         (x - size * 0.42 + k * size * 0.25, y + size * 0.3), 10), (200, 110, 130), 6)


def puzzle_box(d, x, y, w=300):
    _rrect(d, (x - w / 2, y - w * 0.6, x + w / 2, y), 16, (120, 190, 230))
    d.rectangle(_s((x - w * 0.38, y - w * 0.5, x + w * 0.38, y - w * 0.1)), fill=(200, 230, 245), outline=OUT, width=5 * S)
    _ell(d, x, y - w * 0.3, w * 0.12, w * 0.08, (190, 120, 70), lw=4)


def pill(d, x, y, s, color=(240, 120, 160)):
    f = ImageFont.truetype(FONT_BIG, int(80 * S))
    w = d.textlength(s, font=f) / S + 70
    _rrect(d, (x - w / 2, y - 55, x + w / 2, y + 55), 55, color)
    text(d, x, y, s, 80, fill=(255, 255, 255), sw=0)


# ── humans ────────────────────────────────────────────────────────────────────
@lru_cache(maxsize=128)
def human_sprite(pose="stand", shirt=(70, 130, 220), pants=(60, 64, 90), hair=HAIR, skin=SKIN, coat=False,
                 glasses=False, eyes="open", mouth="smile"):
    """Friendly round-headed character, front view. poses: stand, wave, arms_open, sit, point, call."""
    img = Image.new("RGBA", (600 * S, 900 * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = 300
    sit = pose == "sit"
    if not sit:
        for sx in (-1, 1):
            _rrect(d, (cx + sx * 45 - 28, 600, cx + sx * 45 + 28, 830), 22, pants)
            _ell(d, cx + sx * 50, 835, 42, 20, (50, 45, 50), lw=5)
    body_top, body_bot = 380, (640 if not sit else 600)
    arm_y = body_top + 40
    arms = {"stand": [((-95, arm_y), (-120, 520), (-110, 600)), ((95, arm_y), (120, 520), (110, 600))],
            "wave": [((-95, arm_y), (-120, 520), (-110, 600)), ((95, arm_y), (190, 340), (180, 230))],
            "arms_open": [((-95, arm_y), (-200, 380), (-250, 300)), ((95, arm_y), (200, 380), (250, 300))],
            "sit": [((-95, arm_y), (-110, 520), (-60, 560)), ((95, arm_y), (110, 520), (60, 560))],
            "point": [((-95, arm_y), (-120, 520), (-110, 600)), ((95, arm_y), (210, 420), (260, 400))],
            "call": [((-95, arm_y), (-140, 440), (-70, 330)), ((95, arm_y), (140, 440), (70, 330))]}[pose]
    for a, b, c in arms:
        _stroke(d, _bezier((cx + a[0], a[1]), (cx + b[0], b[1]), (cx + c[0], c[1])), coat and (240, 242, 245) or shirt, 40)
        _ell(d, cx + c[0], c[1], 24, 24, skin, lw=5)
    _rrect(d, (cx - 110, body_top, cx + 110, body_bot), 70, shirt)
    if coat:
        _rrect(d, (cx - 112, body_top, cx + 112, body_bot + 20), 60, (240, 242, 245))
        _poly(d, [(cx - 40, body_top + 4), (cx + 40, body_top + 4), (cx, body_top + 110)], shirt, lw=5)
    _rrect(d, (cx - 26, body_top - 40, cx + 26, body_top + 10), 12, skin, lw=5)
    hr = 120
    hy = body_top - 120
    _ell(d, cx, hy - 20, hr * 1.02, hr * 0.85, hair)
    _ell(d, cx, hy, hr * 0.9, hr * 0.92, skin)
    _poly(d, [(cx - 95, hy - 40), (cx - 40, hy - 105), (cx + 60, hy - 100), (cx + 100, hy - 40), (cx + 30, hy - 70)],
          hair, out=None)
    for sx in (-1, 1):
        if eyes == "open":
            _ell(d, cx + sx * 36, hy + 5, 11, 14, (35, 30, 35), out=None)
        else:
            _line(d, _bezier((cx + sx * 36 - 14, hy + 8), (cx + sx * 36, hy - 4), (cx + sx * 36 + 14, hy + 8), 8), OUT, 5)
        _ell(d, cx + sx * 62, hy + 38, 16, 10, (245, 160, 160), out=None)
        if glasses:
            d.ellipse(_s((cx + sx * 36 - 26, hy - 20, cx + sx * 36 + 26, hy + 30)), outline=OUT, width=5 * S)
    if glasses:
        _line(d, [(cx - 10, hy), (cx + 10, hy)], OUT, 5)
    if mouth == "open":
        _ell(d, cx, hy + 52, 20, 16, (150, 40, 60), lw=5)
    else:
        _line(d, _bezier((cx - 28, hy + 45), (cx, hy + 68), (cx + 28, hy + 45), 10), OUT, 6)
    spr, box = _finish(img)
    return spr, (cx - box[0], (850 if not sit else 610) - box[1])


# ── props ─────────────────────────────────────────────────────────────────────
def heart(d, x, y, size, color=(235, 70, 90)):
    r = size / 2
    _ell(d, x - r * 0.5, y - r * 0.2, r * 0.55, r * 0.55, color, lw=5)
    _ell(d, x + r * 0.5, y - r * 0.2, r * 0.55, r * 0.55, color, lw=5)
    _poly(d, [(x - r * 1.02, y - r * 0.05), (x + r * 1.02, y - r * 0.05), (x, y + r * 1.0)], color, lw=5)
    _ell(d, x - r * 0.5, y - r * 0.2, r * 0.5, r * 0.5, color, out=None)
    _ell(d, x + r * 0.5, y - r * 0.2, r * 0.5, r * 0.5, color, out=None)


def text(d, x, y, s, size, fill=(255, 255, 255), stroke=OUT, font=FONT_BIG, anchor="mm", sw=6):
    f = ImageFont.truetype(font, int(size * S))
    d.text((x * S, y * S), s, font=f, fill=fill, anchor=anchor, stroke_width=sw * S, stroke_fill=stroke)


def bubble(d, x, y, w, h, s=None, size=48, tail=(-1, 1), think=False, fill=(255, 255, 255)):
    """Speech (or thought) bubble centred at x, y with optional text."""
    if think:
        for k, (dx, dy, r) in enumerate(((0.55, 0.62, 16), (0.75, 0.82, 10))):
            _ell(d, x + tail[0] * w * dx, y + tail[1] * h * dy, r, r, fill, lw=5)
        _ell(d, x, y, w / 2, h / 2, fill)
    else:
        _poly(d, [(x + tail[0] * w * 0.12, y + tail[1] * h * 0.3), (x + tail[0] * w * 0.42, y + tail[1] * h * 0.9),
                  (x + tail[0] * w * 0.3, y + tail[1] * h * 0.2)], fill)
        _rrect(d, (x - w / 2, y - h / 2, x + w / 2, y + h / 2), min(w, h) * 0.35, fill)
        _poly(d, [(x + tail[0] * w * 0.1, y + tail[1] * h * 0.28), (x + tail[0] * w * 0.39, y + tail[1] * h * 0.84),
                  (x + tail[0] * w * 0.28, y + tail[1] * h * 0.18)], fill, out=None)
    if s:
        text(d, x, y, s, size, fill=(40, 35, 40), stroke=fill, font=FONT_UI, sw=0)


def sound_waves(d, x, y, n=3, direction=1, color=OUT):
    for k in range(n):
        r = 30 + k * 26
        box = _s((x - r, y - r, x + r, y + r))
        start, end = (-40, 40) if direction > 0 else (140, 220)
        d.arc(box, start, end, fill=color, width=7 * S)


def scent(d, x, y, length=220, color=(120, 190, 110), phase=0.0):
    pts = [(x + i * length / 30, y + 18 * math.sin(i / 30 * 3 * math.pi + phase)) for i in range(31)]
    for k in range(0, 30, 3):
        _line(d, pts[k:k + 2], color, 9)


def qmark(d, x, y, size, color=(255, 214, 70)):
    text(d, x, y, "?", size, fill=color, sw=7)


def clock(d, x, y, r, hour=3, minute=0):
    _ell(d, x, y, r, r, (255, 255, 255))
    for k in range(12):
        a = k / 12 * 2 * math.pi
        _line(d, [(x + math.sin(a) * r * 0.78, y - math.cos(a) * r * 0.78),
                  (x + math.sin(a) * r * 0.9, y - math.cos(a) * r * 0.9)], OUT, 4)
    ha, ma = (hour % 12 + minute / 60) / 12 * 2 * math.pi, minute / 60 * 2 * math.pi
    _line(d, [(x, y), (x + math.sin(ha) * r * 0.5, y - math.cos(ha) * r * 0.5)], OUT, 9)
    _line(d, [(x, y), (x + math.sin(ma) * r * 0.75, y - math.cos(ma) * r * 0.75)], OUT, 6)


def laptop(d, x, y, w=360):
    _rrect(d, (x - w / 2, y - w * 0.62, x + w / 2, y - w * 0.04), 14, (70, 75, 90))
    d.rectangle(_s((x - w / 2 + 18, y - w * 0.62 + 18, x + w / 2 - 18, y - w * 0.04 - 18)), fill=(150, 200, 240))
    _rrect(d, (x - w * 0.6, y - w * 0.06, x + w * 0.6, y + w * 0.04), 10, (150, 155, 170))


def book(d, x, y, title="CAT SENSE", w=300, h=400, color=(220, 90, 80)):
    _rrect(d, (x - w / 2, y - h / 2, x + w / 2, y + h / 2), 16, color)
    _rrect(d, (x - w / 2, y - h / 2, x - w / 2 + 34, y + h / 2), 10, tuple(int(c * 0.8) for c in color))
    for k, word in enumerate(title.split()):
        text(d, x + 14, y - 60 + k * 85, word, 80, fill=(255, 240, 210), sw=4)


def speaker(d, x, y, size=180):
    _rrect(d, (x - size * 0.35, y - size / 2, x + size * 0.35, y + size / 2), 24, (60, 64, 80))
    _ell(d, x, y + size * 0.15, size * 0.22, size * 0.22, (120, 125, 145))
    _ell(d, x, y - size * 0.25, size * 0.1, size * 0.1, (120, 125, 145))
    sound_waves(d, x + size * 0.45, y)


def mark(d, x, y, size, ok=True):
    if ok:
        _stroke(d, [(x - size * 0.45, y), (x - size * 0.1, y + size * 0.35), (x + size * 0.5, y - size * 0.4)],
                (80, 200, 110), 26)
    else:
        for a, b in (((-0.4, -0.4), (0.4, 0.4)), ((-0.4, 0.4), (0.4, -0.4))):
            _stroke(d, [(x + a[0] * size, y + a[1] * size), (x + b[0] * size, y + b[1] * size)], (235, 80, 80), 26)


def drops(d, x, y, n=3, color=(255, 255, 255)):
    for k in range(n):
        dx, dy = (k - (n - 1) / 2) * 34, (k % 2) * 26
        _ell(d, x + dx, y + dy, 11, 15, color, lw=4)


def cat_ears(d, x, y, r=60, color=ORANGE):
    # cat ears on a human head centred at (x, y): the "you're just a big cat" joke
    for sx in (-1, 1):
        _poly(d, [(x + sx * r * 1.25, y - r * 0.55), (x + sx * r * 0.95, y - r * 1.9), (x + sx * r * 0.2, y - r * 1.1)],
              color)
        _poly(d, [(x + sx * r * 1.08, y - r * 0.85), (x + sx * r * 0.92, y - r * 1.55), (x + sx * r * 0.45, y - r * 1.15)],
              PINK, out=None)


def dog_ears(d, x, y, r=60, color=(190, 140, 80)):
    # floppy dog ears on a human head centred at (x, y): the 'you're part of the pack' joke
    for sx in (-1, 1):
        _ell(d, x + sx * r * 1.05, y + r * 0.35, r * 0.38, r * 0.8, color)


def subscribe(d, x, y, w=460, h=120):
    _rrect(d, (x - w / 2, y - h / 2, x + w / 2, y + h / 2), 30, (230, 40, 40))
    text(d, x, y, "SUBSCRIBE", 86, fill=(255, 255, 255), sw=0)


def bowl(d, x, y, w=150, color=(90, 160, 220)):
    _poly(d, [(x - w / 2, y - 40), (x + w / 2, y - 40), (x + w * 0.36, y + 10), (x - w * 0.36, y + 10)], color)
    _ell(d, x, y - 40, w / 2, 12, (190, 130, 80))


def percent_ring(d, x, y, r, pct, color=(80, 200, 120), label=None):
    _ell(d, x, y, r, r, (235, 235, 235))
    d.pieslice(_s((x - r, y - r, x + r, y + r)), -90, -90 + 360 * pct / 100, fill=color)
    d.ellipse(_s((x - r, y - r, x + r, y + r)), outline=OUT, width=LW * S)
    _ell(d, x, y, r * 0.62, r * 0.62, (255, 255, 255))
    text(d, x, y, label or f"{pct}%", r * 0.55, fill=OUT, stroke=(255, 255, 255), sw=0)


# ── backgrounds ───────────────────────────────────────────────────────────────
FLOOR_Y = 860


def _floor(d, top, color, plank=True):
    d.rectangle(_s((0, top, W, H)), fill=color)
    dk = tuple(int(c * 0.85) for c in color)
    if plank:
        for k in range(1, 5):
            y = top + k * (H - top) / 5
            _line(d, [(0, y), (W, y)], dk, 3)
        for k in range(12):
            x = (k * 173 + (k % 2) * 60) % W
            _line(d, [(x, top + (k % 5) * (H - top) / 5), (x, top + (k % 5 + 1) * (H - top) / 5)], dk, 3)
    _line(d, [(0, top), (W, top)], OUT, 6)


def _window(d, x, y, w, h, sky=(150, 205, 245), night=False):
    _rrect(d, (x - 14, y - 14, x + w + 14, y + h + 14), 10, (255, 255, 255))
    d.rectangle(_s((x, y, x + w, y + h)), fill=sky)
    if night:
        _ell(d, x + w * 0.7, y + h * 0.3, 42, 42, (250, 240, 190), lw=4)
        _ell(d, x + w * 0.7 + 20, y + h * 0.3 - 12, 36, 36, sky, out=None)
        for k in range(7):
            sx, sy = x + (k * 97 % w), y + (k * 61 % int(h * 0.8)) + 15
            _ell(d, sx, sy, 4, 4, (255, 255, 220), out=None)
    else:
        for cx, cy in ((x + w * 0.3, y + h * 0.35), (x + w * 0.42, y + h * 0.3)):
            _ell(d, cx, cy, 55, 26, (255, 255, 255), out=None)
    _line(d, [(x + w / 2, y), (x + w / 2, y + h)], (255, 255, 255), 12)
    _line(d, [(x, y + h / 2), (x + w, y + h / 2)], (255, 255, 255), 12)
    d.rectangle(_s((x, y, x + w, y + h)), outline=OUT, width=6 * S)


def _sofa(d, x, y, w=620, color=(84, 160, 160)):
    dk = tuple(int(c * 0.82) for c in color)
    _rrect(d, (x, y - 230, x + w, y - 60), 50, dk)
    _rrect(d, (x - 40, y - 140, x + w + 40, y), 40, color)
    for k in range(2):
        _rrect(d, (x + 20 + k * (w - 40) / 2, y - 175, x + (k + 1) * (w - 40) / 2 + 10, y - 110), 30, color)
    for sx in (x - 40, x + w - 20):
        _rrect(d, (sx, y - 190, sx + 60, y - 10), 28, dk)


def _plant(d, x, y):
    for k, a in enumerate((-0.9, -0.4, 0.1, 0.6, 1.0)):
        _stroke(d, _bezier((x, y - 90), (x + a * 60, y - 200), (x + a * 110, y - 260 + k * 8)), (90, 170, 90), 26)
    _poly(d, [(x - 60, y - 100), (x + 60, y - 100), (x + 45, y), (x - 45, y)], (200, 110, 80))


@lru_cache(maxsize=32)
def background(kind="living"):
    img = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 255))
    d = ImageDraw.Draw(img)
    if kind == "living":
        d.rectangle(_s((0, 0, W, FLOOR_Y)), fill=(250, 231, 200))
        _window(d, 230, 170, 420, 330)
        _rrect(d, (1300, 210, 1560, 400), 8, (255, 255, 255))
        d.rectangle(_s((1325, 235, 1535, 375)), fill=(160, 210, 170))
        _poly(d, [(1325, 375), (1400, 290), (1470, 375)], (110, 170, 120), out=None)
        _floor(d, FLOOR_Y, (198, 142, 98))
        _sofa(d, 1180, FLOOR_Y + 10)
        _plant(d, 820, FLOOR_Y + 5)
    elif kind == "night":
        d.rectangle(_s((0, 0, W, FLOOR_Y)), fill=(48, 58, 102))
        _window(d, 1250, 160, 400, 320, sky=(25, 32, 70), night=True)
        _floor(d, FLOOR_Y, (78, 66, 92))
        _rrect(d, (150, FLOOR_Y - 230, 900, FLOOR_Y - 80), 40, (120, 140, 210))
        _rrect(d, (130, FLOOR_Y - 330, 210, FLOOR_Y + 20), 20, (150, 110, 90))
        _rrect(d, (230, FLOOR_Y - 280, 420, FLOOR_Y - 210), 30, (240, 240, 250))
        clock(d, 960, 300, 90, 3, 0)
    elif kind == "lab":
        d.rectangle(_s((0, 0, W, FLOOR_Y)), fill=(222, 238, 248))
        _rrect(d, (1150, 150, 1750, 560), 14, (255, 255, 255))
        for k, hgt in enumerate((120, 210, 160, 260)):
            _rrect(d, (1230 + k * 120, 500 - hgt, 1300 + k * 120, 500), 6, (90, 170, 230), lw=5)
        _floor(d, FLOOR_Y, (180, 186, 196), plank=False)
        _rrect(d, (120, FLOOR_Y - 230, 820, FLOOR_Y - 190), 10, (240, 240, 240))
        for k in range(3):
            _rrect(d, (200 + k * 160, FLOOR_Y - 330, 260 + k * 160, FLOOR_Y - 230), 14, (150, 220, 200), lw=5)
    elif kind == "room":       # bare test room (attachment experiment)
        d.rectangle(_s((0, 0, W, FLOOR_Y)), fill=(214, 220, 214))
        _rrect(d, (1450, 260, 1720, FLOOR_Y), 8, (176, 120, 80))
        _ell(d, 1690, 560, 14, 14, (240, 200, 90), lw=4)
        _floor(d, FLOOR_Y, (170, 172, 176), plank=False)
        _rrect(d, (300, FLOOR_Y - 260, 520, FLOOR_Y - 220), 12, (120, 140, 170))
        for x in (310, 490):
            _rrect(d, (x, FLOOR_Y - 230, x + 20, FLOOR_Y), 6, (120, 140, 170), lw=5)
    elif kind == "doorstep":
        d.rectangle(_s((0, 0, W, 760)), fill=(160, 210, 245))
        _rrect(d, (520, 120, 1400, 800), 6, (236, 196, 160))
        _rrect(d, (820, 330, 1100, 800), 8, (150, 90, 60))
        _ell(d, 1065, 580, 14, 14, (240, 200, 90), lw=4)
        d.rectangle(_s((0, 760, W, H)), fill=(120, 190, 100))
        _line(d, [(0, 760), (W, 760)], OUT, 6)
        _rrect(d, (760, 800, 1160, 860), 12, (190, 80, 70))
    elif kind in ("forest", "enclosure"):
        d.rectangle(_s((0, 0, W, 700)), fill=(170, 215, 240))
        for k, (mx, mh) in enumerate(((300, 330), (900, 420), (1500, 360))):
            _poly(d, [(mx - 420, 700), (mx, 700 - mh), (mx + 420, 700)], (150, 170, 190), out=None)
        d.rectangle(_s((0, 700, W, H)), fill=(120, 175, 95))
        _line(d, [(0, 700), (W, 700)], OUT, 6)
        for k, tx in enumerate((120, 420, 1580, 1830)):
            _rrect(d, (tx - 22, 520, tx + 22, 760), 10, (130, 90, 60))
            _ell(d, tx, 470 - (k % 2) * 30, 120, 140, (80, 150, 80))
        if kind == "enclosure":    # captive wolves: a fenced pen
            for x in range(0, W + 1, 90):
                _rrect(d, (x - 8, 380, x + 8, 980), 6, (120, 120, 130), lw=4)
            _rrect(d, (0, 400, W, 425), 6, (120, 120, 130), lw=4)
            _rrect(d, (0, 880, W, 905), 6, (120, 120, 130), lw=4)
    else:                      # plain coloured card
        colors = {"plain_blue": (90, 170, 230), "plain_yellow": (255, 210, 90), "plain_green": (130, 205, 140),
                  "plain_pink": (245, 160, 180), "plain_purple": (170, 140, 220)}
        d.rectangle(_s((0, 0, W, H)), fill=colors.get(kind, (90, 170, 230)))
    return img.resize((W, H), Image.LANCZOS)


# ── composition ───────────────────────────────────────────────────────────────
def place(canvas, sprite_anchor, x, y, scale=1.0, flip=False, alpha=1.0):
    spr, (ax, ay) = sprite_anchor
    if flip:
        spr = spr.transpose(Image.FLIP_LEFT_RIGHT)
        ax = spr.width - ax
    if scale != 1.0:
        spr = spr.resize((max(1, int(spr.width * scale)), max(1, int(spr.height * scale))), Image.LANCZOS)
        ax, ay = ax * scale, ay * scale
    if alpha < 1.0:
        a = spr.getchannel("A").point(lambda v: int(v * alpha))
        spr = spr.copy()
        spr.putalpha(a)
    canvas.alpha_composite(spr, (int(x - ax), int(y - ay)))


def overlay():
    """A transparent S-x canvas for props/text, composited with finish_overlay()."""
    img = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def finish_overlay(canvas, ov):
    canvas.alpha_composite(ov.resize((W, H), Image.LANCZOS))


def camera(img, zoom=1.0, cx=0.5, cy=0.5):
    """Crop-zoom toward (cx, cy) (fractions of the frame) and scale back to 1920x1080."""
    if zoom <= 1.001:
        return img
    w, h = W / zoom, H / zoom
    x0 = min(max(cx * W - w / 2, 0), W - w)
    y0 = min(max(cy * H - h / 2, 0), H - h)
    return img.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + w, y0 + h))
