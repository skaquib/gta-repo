"""
thumb_kit.py — high-click-rate thumbnails for the cartoon long videos.

Why (owner, 2026-11-03): the first thumbnails (small calm characters on a flat
colour card) looked like a children's book. A thumbnail has ~0.2 s on a phone,
so it needs:
  - BIG faces with strong emotion (shock, judging side-eye, snarl): faces filling
    half the frame, cropped by the edge, not small full-body sprites;
  - a contrast or conflict the eye reads at once (judging cat vs shocked owner,
    snarling "alpha" wolf crossed out vs loving dog);
  - saturated burst backgrounds, white sticker outlines and a drop shadow so the
    characters pop off any feed colour;
  - 2-4 words in a heavy font with a thick black stroke, plus red arrows / X marks.

All art is drawn here in code (our own characters), sized for a 1920x1080 canvas
and saved at 1280x720. Check every thumbnail at phone size with small_preview().
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import cartoon_kit as ck
from cartoon_kit import (CREAM, GOLDEN, HAIR, ORANGE, OUT, PINK, SKIN, WOLF_GREY, W, H, _bezier, _ell, _line,
                         _poly, _rrect, _stroke)

FONT_HEAVY = os.path.join(ck.HERE, "fonts", "Montserrat[wght].ttf")
RED, YELLOW, WHITE = (235, 35, 45), (255, 222, 40), (255, 255, 255)
MOUTH, TONGUE = (120, 25, 45), (240, 110, 130)


def font(size, weight=900):
    f = ImageFont.truetype(FONT_HEAVY, int(size))
    try:
        f.set_variation_by_axes([weight])
    except (OSError, AttributeError):
        pass
    return f


# ── backgrounds ───────────────────────────────────────────────────────────────
def burst(inner, outer, cx=0.5, cy=0.55, rays=20, ray_alpha=0.16):
    """Saturated radial gradient with sun rays and a dark vignette."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dist = np.sqrt(((xx - cx * W) / W) ** 2 + ((yy - cy * H) / W) ** 2)
    t = np.clip(dist / 0.75, 0, 1)[..., None]
    img = np.array(inner, np.float32) * (1 - t) + np.array(outer, np.float32) * t
    ang = np.arctan2(yy - cy * H, xx - cx * W)
    ray = (np.sin(ang * rays) > 0.35).astype(np.float32)[..., None] * ray_alpha * (1 - t * 0.6)
    img = img * (1 - ray) + 255 * ray
    vig = np.clip(1 - 0.55 * np.clip((dist - 0.35) / 0.5, 0, 1), 0, 1)[..., None]
    return Image.fromarray(np.clip(img * vig, 0, 255).astype(np.uint8)).convert("RGBA")


def split(left_bg, right_bg, slant=180):
    """Two backgrounds split by a diagonal: 'wrong' on the left, 'right' on the right."""
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).polygon([(W / 2 + slant, 0), (W, 0), (W, H), (W / 2 - slant, H)], fill=255)
    out = left_bg.copy()
    out.paste(right_bg, (0, 0), mask)
    d = ImageDraw.Draw(out)
    d.line([(W / 2 + slant, 0), (W / 2 - slant, H)], fill=WHITE, width=18)
    return out


# ── sticker compositing ───────────────────────────────────────────────────────
def layer():
    """A transparent S-x drawing layer (cartoon_kit primitives take 1x coordinates)."""
    return ck.overlay()


def stick(canvas, lay, outline=16, shadow=(14, 18)):
    """Composite an S-x layer as a 'sticker': white outline + soft drop shadow."""
    lay = lay.resize((W, H), Image.LANCZOS)
    a = lay.getchannel("A")
    grown = a.filter(ImageFilter.GaussianBlur(outline * 0.55)).point(lambda v: 255 if v > 10 else 0)
    grown = grown.filter(ImageFilter.GaussianBlur(1.5))
    if shadow:
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sh.putalpha(grown.filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * 0.55)))
        canvas.alpha_composite(sh, shadow)
    white = Image.new("RGBA", (W, H), WHITE + (0,))
    white.putalpha(grown)
    canvas.alpha_composite(white)
    canvas.alpha_composite(lay)


# ── faces ─────────────────────────────────────────────────────────────────────
def _eye_white(d, x, y, rx, ry):
    _ell(d, x, y, rx, ry, WHITE, lw=6)


def _pupil(d, x, y, r, look=(0, 0), reach=0.0, color=(30, 24, 28), shine=True):
    px, py = x + look[0] * reach, y + look[1] * reach
    _ell(d, px, py, r, r * 1.08, color, out=None)
    if shine:
        _ell(d, px - r * 0.35, py - r * 0.4, r * 0.32, r * 0.32, WHITE, out=None)


def _lid(d, x, y, rx, ry, color, cover=0.45, tilt=0.0):
    """Heavy upper eyelid (judging / angry): covers the top `cover` of the eye."""
    top, cut = y - ry * 1.05, y - ry + 2 * ry * cover
    _poly(d, [(x - rx * 1.08, top), (x + rx * 1.08, top), (x + rx * 1.08, cut + tilt * ry), (x - rx * 1.08, cut - tilt * ry)],
          color, out=None)
    _line(d, [(x - rx * 1.02, cut - tilt * ry), (x + rx * 1.02, cut + tilt * ry)], OUT, 9)


def _brow(d, x, y, w, angle, sx, width=16):
    """Eyebrow over the eye at x on side sx (-1 left, +1 right of the face centre).
    angle > 0: inner end lower (angry); angle < 0: inner end higher (worried, pleading, shocked)."""
    dx, dy = w * math.cos(math.radians(angle)), w * math.sin(math.radians(angle))
    _stroke(d, [(x + sx * dx, y - dy), (x - sx * dx, y + dy)], OUT, width, out=None)


def cat_head(d, cx, cy, r, expr="judge", look=(1, 0), color=ORANGE, body=True):
    """Big cat head. expr: judge (heavy-lidded side-eye), shock, hiss, happy."""
    stripe = tuple(int(c * 0.8) for c in color)
    if body:                                   # shoulders running off the bottom edge
        _ell(d, cx, cy + r * 1.55, r * 1.1, r * 0.9, color)
        _ell(d, cx, cy + r * 1.3, r * 0.5, r * 0.5, CREAM, out=None)
    flat = expr == "hiss"
    for sx in (-1, 1):
        if flat:                               # ears pinned back sideways
            tip = (cx + sx * r * 1.35, cy - r * 0.55)
            _poly(d, [(cx + sx * r * 0.85, cy - r * 0.15), tip, (cx + sx * r * 0.45, cy - r * 0.75)], color)
        else:
            _poly(d, [(cx + sx * r * 0.88, cy - r * 0.3), (cx + sx * r * 0.66, cy - r * 1.2), (cx + sx * r * 0.16, cy - r * 0.8)],
                  color)
            _poly(d, [(cx + sx * r * 0.72, cy - r * 0.43), (cx + sx * r * 0.63, cy - r * 0.95), (cx + sx * r * 0.32, cy - r * 0.72)],
                  PINK, out=None)
    for sx in (-1, 1):                         # cheek fluff
        _poly(d, [(cx + sx * r * 0.9, cy + r * 0.05), (cx + sx * r * 1.12, cy + r * 0.3), (cx + sx * r * 0.88, cy + r * 0.42),
                  (cx + sx * r * 1.05, cy + r * 0.58), (cx + sx * r * 0.7, cy + r * 0.62)], color)
    _ell(d, cx, cy, r, r * 0.9, color)
    _ell(d, cx, cy + r * 0.36, r * 0.5, r * 0.34, CREAM, out=None)
    for k in (-1, 0, 1):
        _line(d, [(cx + k * r * 0.17, cy - r * 0.86), (cx + k * r * 0.12, cy - r * 0.58)], stripe, 12)
    ex, ey, er = r * 0.4, cy - r * 0.1, r * 0.25
    for sx in (-1, 1):
        x = cx + sx * ex
        if expr == "happy":                    # closed, smiling eyes
            _line(d, _bezier((x - er, ey + er * 0.25), (x, ey - er * 0.75), (x + er, ey + er * 0.25), 12), OUT, 11)
        elif expr == "shock":
            _eye_white(d, x, ey, er * 0.95, er * 1.15)
            _pupil(d, x, ey + er * 0.05, er * 0.22, shine=False)
            _brow(d, x, ey - er * 1.75, er * 0.8, -14, sx, 13)
        else:
            _eye_white(d, x, ey, er, er * 0.95)
            _ell(d, x + look[0] * er * 0.45, ey + er * 0.18, er * 0.5, er * 0.62, (60, 140, 70), out=None)   # green iris
            _ell(d, x + look[0] * er * 0.5, ey + er * 0.2, er * 0.16, er * 0.5, (25, 22, 26), out=None)       # slit pupil
            _ell(d, x + look[0] * er * 0.5 - er * 0.18, ey - er * 0.05, er * 0.13, er * 0.13, WHITE, out=None)
            _lid(d, x, ey, er, er * 0.95, color, cover=0.5 if expr == "judge" else 0.42, tilt=-sx * 0.12)
            _brow(d, x, ey - er * 1.3, er * 0.85, 18, sx, 15)
    ny = cy + r * 0.24
    _poly(d, [(cx - r * 0.11, ny - r * 0.06), (cx + r * 0.11, ny - r * 0.06), (cx, ny + r * 0.07)], PINK, lw=6)
    if expr == "shock":
        _ell(d, cx, ny + r * 0.3, r * 0.15, r * 0.2, MOUTH, lw=7)
        _ell(d, cx, ny + r * 0.42, r * 0.09, r * 0.06, TONGUE, out=None)
    elif expr == "hiss":
        _ell(d, cx, ny + r * 0.3, r * 0.3, r * 0.2, MOUTH, lw=7)
        for sx in (-1, 1):
            _poly(d, [(cx + sx * r * 0.2, ny + r * 0.14), (cx + sx * r * 0.1, ny + r * 0.14), (cx + sx * r * 0.15, ny + r * 0.32)],
                  WHITE, lw=4)
    elif expr == "happy":                       # "w" smile
        for sx in (-1, 1):
            _line(d, _bezier((cx, ny + r * 0.08), (cx + sx * r * 0.07, ny + r * 0.24), (cx + sx * r * 0.18, ny + r * 0.12), 10), OUT, 7)
    else:                                       # unimpressed flat mouth
        _line(d, _bezier((cx - r * 0.16, ny + r * 0.2), (cx, ny + r * 0.14), (cx + r * 0.16, ny + r * 0.2), 8), OUT, 8)
    for sx in (-1, 1):
        for k in (-1, 0, 1):
            _line(d, [(cx + sx * r * 0.34, ny + r * 0.1 + k * r * 0.07), (cx + sx * r * 0.95, ny + k * r * 0.15)], OUT, 5)


def human_head(d, cx, cy, r, expr="shock", shirt=(70, 130, 220), hands=True, ears=None):
    """Big human head + shoulders. expr: shock (wide eyes, O mouth, hands on cheeks)."""
    _rrect(d, (cx - r * 1.25, cy + r * 0.95, cx + r * 1.25, cy + r * 2.4), r * 0.6, shirt)
    _rrect(d, (cx - r * 0.25, cy + r * 0.6, cx + r * 0.25, cy + r * 1.05), r * 0.1, SKIN, lw=6)
    _ell(d, cx, cy - r * 0.15, r * 1.04, r * 0.88, HAIR)
    if ears == "cat":
        ck.cat_ears(d, cx, cy - r * 0.02, r * 0.62)
    _ell(d, cx, cy, r * 0.9, r * 0.95, SKIN)
    _poly(d, [(cx - r * 0.8, cy - r * 0.32), (cx - r * 0.35, cy - r * 0.9), (cx + r * 0.5, cy - r * 0.86),
              (cx + r * 0.85, cy - r * 0.32), (cx + r * 0.25, cy - r * 0.58)], HAIR, out=None)
    for sx in (-1, 1):
        x, y = cx + sx * r * 0.33, cy + r * 0.02
        _eye_white(d, x, y, r * 0.17, r * 0.21)
        _pupil(d, x, y + r * 0.02, r * 0.055, shine=False)
        _brow(d, x, y - r * 0.4, r * 0.15, -18, sx, 12)
        _ell(d, cx + sx * r * 0.58, cy + r * 0.38, r * 0.13, r * 0.08, (245, 150, 150), out=None)
    _ell(d, cx, cy + r * 0.56, r * 0.17, r * 0.22, MOUTH, lw=7)
    _ell(d, cx, cy + r * 0.68, r * 0.1, r * 0.07, TONGUE, out=None)
    if hands:                                   # hands on cheeks
        for sx in (-1, 1):
            hx, hy = cx + sx * r * 0.88, cy + r * 0.48
            _ell(d, hx, hy, r * 0.22, r * 0.32, SKIN, lw=6)
            for k in range(3):
                _line(d, [(hx - sx * r * 0.05, hy - r * 0.12 + k * r * 0.1), (hx + sx * r * 0.14, hy - r * 0.16 + k * r * 0.1)],
                      OUT, 4)


def dog_head(d, cx, cy, r, expr="love", color=GOLDEN, body=True):
    """Big friendly dog head. expr: love (huge shiny puppy eyes, tongue, blush)."""
    ear_c = tuple(int(c * 0.75) for c in color)
    if body:
        _ell(d, cx, cy + r * 1.5, r * 1.05, r * 0.85, color)
        _ell(d, cx, cy + r * 1.25, r * 0.45, r * 0.5, (252, 236, 206), out=None)
    _ell(d, cx, cy, r, r * 0.9, color)
    for sx in (-1, 1):
        _ell(d, cx + sx * r * 0.98, cy + r * 0.12, r * 0.33, r * 0.66, ear_c)
    _ell(d, cx, cy + r * 0.4, r * 0.55, r * 0.4, (252, 236, 206), out=None)
    ex, ey, er = r * 0.38, cy - r * 0.12, r * 0.25
    for sx in (-1, 1):
        x = cx + sx * ex
        _eye_white(d, x, ey, er, er * 1.08)
        _ell(d, x, ey + er * 0.12, er * 0.78, er * 0.85, (55, 35, 25), out=None)
        _ell(d, x - er * 0.28, ey - er * 0.22, er * 0.3, er * 0.3, WHITE, out=None)
        _ell(d, x + er * 0.3, ey + er * 0.35, er * 0.13, er * 0.13, WHITE, out=None)
        _brow(d, x, ey - er * 1.45, er * 0.7, -20, sx, 13)            # raised inner brows
        _ell(d, cx + sx * r * 0.62, cy + r * 0.3, r * 0.13, r * 0.08, (245, 140, 140), out=None)
    ny = cy + r * 0.22
    _ell(d, cx, ny, r * 0.18, r * 0.13, (35, 28, 30), lw=6)
    _rrect(d, (cx - r * 0.13, ny + r * 0.22, cx + r * 0.13, ny + r * 0.62), r * 0.12, TONGUE, lw=7)
    _line(d, [(cx, ny + r * 0.28), (cx, ny + r * 0.48)], (200, 80, 100), 5)
    _line(d, _bezier((cx - r * 0.28, ny + r * 0.18), (cx, ny + r * 0.34), (cx + r * 0.28, ny + r * 0.18), 10), OUT, 8)


def wolf_head(d, cx, cy, r, color=WOLF_GREY, body=True):
    """Big snarling wolf: angry brows, amber narrowed eyes, bared fangs."""
    if body:
        _ell(d, cx, cy + r * 1.5, r * 1.1, r * 0.85, color)
        _ell(d, cx, cy + r * 1.25, r * 0.45, r * 0.5, (225, 222, 218), out=None)
    for sx in (-1, 1):
        _poly(d, [(cx + sx * r * 0.88, cy - r * 0.25), (cx + sx * r * 0.78, cy - r * 1.3), (cx + sx * r * 0.18, cy - r * 0.78)], color)
        _poly(d, [(cx + sx * r * 0.74, cy - r * 0.42), (cx + sx * r * 0.72, cy - r * 1.02), (cx + sx * r * 0.36, cy - r * 0.72)],
              (235, 210, 210), out=None)
        _poly(d, [(cx + sx * r * 0.92, cy), (cx + sx * r * 1.2, cy + r * 0.25), (cx + sx * r * 0.92, cy + r * 0.38),
                  (cx + sx * r * 1.1, cy + r * 0.6), (cx + sx * r * 0.7, cy + r * 0.62)], color)
    _ell(d, cx, cy, r, r * 0.9, color)
    _ell(d, cx, cy + r * 0.5, r * 0.5, r * 0.45, (225, 222, 218))
    ex, ey, er = r * 0.4, cy - r * 0.16, r * 0.21
    for sx in (-1, 1):
        x = cx + sx * ex
        _eye_white(d, x, ey, er, er * 0.85)
        _ell(d, x, ey + er * 0.1, er * 0.62, er * 0.62, (235, 165, 40), out=None)
        _ell(d, x, ey + er * 0.1, er * 0.28, er * 0.34, (20, 16, 14), out=None)
        _lid(d, x, ey, er, er * 0.85, color, cover=0.38, tilt=-sx * 0.35)
        _brow(d, x, ey - er * 1.0, er * 1.0, 26, sx, 18)                # angry: inner ends down
    for k in (-1, 1):                                                    # nose wrinkles
        _line(d, [(cx + k * r * 0.08, cy + r * 0.08), (cx + k * r * 0.2, cy + r * 0.16)], OUT, 6)
    ny = cy + r * 0.34
    _ell(d, cx, ny, r * 0.17, r * 0.12, (30, 24, 26), lw=6)
    _rrect(d, (cx - r * 0.34, ny + r * 0.18, cx + r * 0.34, ny + r * 0.5), r * 0.12, MOUTH, lw=7)
    for k in range(4):                                                   # teeth, fangs at the ends
        tx = cx - r * 0.24 + k * r * 0.16
        fang = k in (0, 3)
        _poly(d, [(tx - r * 0.06, ny + r * 0.19), (tx + r * 0.06, ny + r * 0.19), (tx, ny + r * (0.36 if fang else 0.27))],
              WHITE, lw=4)
        _poly(d, [(tx - r * 0.05, ny + r * 0.49), (tx + r * 0.05, ny + r * 0.49), (tx, ny + r * (0.36 if fang else 0.42))],
              WHITE, lw=4)


# ── marks ─────────────────────────────────────────────────────────────────────
def red_x(d, cx, cy, size, width=60):
    for a, b in (((-1, -1), (1, 1)), ((-1, 1), (1, -1))):
        _stroke(d, [(cx + a[0] * size, cy + a[1] * size), (cx + b[0] * size, cy + b[1] * size)], RED, width, lw=9)


def arrow(d, p0, p1, p2, color=RED, width=46):
    """Thick curved arrow from p0 via p1 to the tip p2."""
    pts = _bezier(p0, p1, p2, 30)
    _stroke(d, pts[:-3], color, width, lw=9)
    (x1, y1), (x2, y2) = pts[-6], p2
    a = math.atan2(y2 - y1, x2 - x1)
    L, Wd = width * 2.1, width * 1.6
    bx, by = x2 - L * math.cos(a), y2 - L * math.sin(a)
    _poly(d, [(x2, y2), (bx + Wd * math.sin(a), by - Wd * math.cos(a)), (bx - Wd * math.sin(a), by + Wd * math.cos(a))],
          color, lw=9)


def shock_lines(d, cx, cy, r, n=7, a0=-160, a1=-20, color=YELLOW):
    for k in range(n):
        a = math.radians(a0 + (a1 - a0) * k / (n - 1))
        _stroke(d, [(cx + r * math.cos(a), cy + r * math.sin(a)), (cx + r * 1.25 * math.cos(a), cy + r * 1.25 * math.sin(a))],
                color, 22, lw=7)


def hearts(d, spots):
    for x, y, s in spots:
        ck.heart(d, x, y, s)


# ── text ──────────────────────────────────────────────────────────────────────
def headline(canvas, lines, x, y, rotate=-3, stroke=16, gap=0.92, shadow=True):
    """lines: [(text, size, fill)] stacked and centred on (x, y), heavy font, thick black stroke.
    A fill of ('box', colour) draws white text on a solid colour box."""
    pad = stroke + 30
    rows = []
    for s, size, fill in lines:
        f = font(size)
        l, t, r, b = f.getbbox(s, stroke_width=stroke)
        rows.append((s, f, fill, r - l, b - t, l, t))
    tw = max(r[3] for r in rows) + 2 * pad + 60
    th = int(sum(r[4] * gap for r in rows)) + 2 * pad + 40
    img = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    yy = pad
    for s, f, fill, w, h, l, t in rows:
        xx = (tw - w) / 2 - l
        if isinstance(fill, tuple) and len(fill) == 2 and fill[0] == "box":
            d.rounded_rectangle([xx + l - 26, yy - 6, xx + l + w + 26, yy + h + 6], 22, fill=fill[1], outline=(0, 0, 0), width=10)
            d.text((xx, yy - t), s, font=f, fill=WHITE, stroke_width=0)
        else:
            d.text((xx, yy - t), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0))
        yy += int(h * gap) + 18
    if rotate:
        img = img.rotate(rotate, resample=Image.BICUBIC, expand=True)
    px, py = int(x - img.width / 2), int(y - img.height / 2)
    if shadow:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        sh.putalpha(img.getchannel("A").filter(ImageFilter.GaussianBlur(8)).point(lambda v: int(v * 0.6)))
        canvas.alpha_composite(sh, (px + 10, py + 14))
    canvas.alpha_composite(img, (px, py))


# ── output ────────────────────────────────────────────────────────────────────
def save(canvas, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    out = canvas.convert("RGB").resize((1280, 720), Image.LANCZOS)
    out = out.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))
    out.save(path, quality=93)
    return path


def small_preview(paths, out, size=(320, 180)):
    """Phone-feed size check: the thumbnails as small as a viewer sees them, side by side."""
    tiles = [Image.open(p).convert("RGB").resize(size, Image.LANCZOS) for p in paths]
    sheet = Image.new("RGB", (size[0] * len(tiles) + 20 * (len(tiles) - 1), size[1]), (255, 255, 255))
    for k, t in enumerate(tiles):
        sheet.paste(t, (k * (size[0] + 20), 0))
    sheet.save(out)
    return out
