"""Designed stat cards for Shorts (1080x1920), turned into slow-zoom clips.

Used when a story's key facts are numbers and no licensed photo of the
person exists -- e.g. Abhishek Sharma (2026-09-19): Wikimedia has no free
image of the cricketer, and the only name match was a different man. Viral
cricket Shorts lean on big stat graphics anyway.

Layout keeps all text in the middle band (y ~ 560-1360): the hook card owns
the top third for the first seconds and burned-in captions sit near the
bottom, so nothing collides.
"""
import os

from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageFont
from moviepy import VideoFileClip

W, H = 1080, 1920
GOLD = (255, 205, 40)
WHITE = (255, 255, 255)
GREY = (200, 200, 210)
FONT = "C:/Windows/Fonts/impact.ttf"


def _bg(bg_clip: str) -> Image.Image:
    if bg_clip and os.path.exists(bg_clip):
        c = VideoFileClip(bg_clip, audio=False)
        frame = Image.fromarray(c.get_frame(c.duration * 0.5))
        c.close()
        s = max(W / frame.width, H / frame.height)
        frame = frame.resize((int(frame.width * s) + 1, int(frame.height * s) + 1))
        l, t = (frame.width - W) // 2, (frame.height - H) // 2
        img = frame.crop((l, t, l + W, t + H)).filter(ImageFilter.GaussianBlur(18))
        img = ImageEnhance.Brightness(img).enhance(0.35)
    else:
        img = Image.new("RGB", (W, H), (12, 16, 32))
    return img


def _center(d, y, text, size, fill):
    f = ImageFont.truetype(FONT, size)
    w = d.textbbox((0, 0), text, font=f)[2]
    d.text(((W - w) // 2, y), text, font=f, fill=fill, stroke_width=6, stroke_fill=(0, 0, 0))
    return y + int(size * 1.08)


def make_card(lines, out_jpg, bg_clip=None):
    """lines: [(text, size, colour), ...] stacked and centred vertically."""
    img = _bg(bg_clip)
    d = ImageDraw.Draw(img)
    total = sum(int(s * 1.08) for _, s, _ in lines)
    y = (H - total) // 2
    for text, size, col in lines:
        y = _center(d, y, text, size, col)
    img.save(out_jpg, quality=92)
    return out_jpg


def make_card_clip(lines, out_mp4, bg_clip=None, duration=10.0):
    import pro_shorts_creator as psc
    jpg = out_mp4.rsplit(".", 1)[0] + ".jpg"
    make_card(lines, jpg, bg_clip)
    return psc.make_athlete_photo_clip(jpg, out_mp4, duration=duration)
