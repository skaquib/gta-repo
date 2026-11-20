"""
make_thumbnail.py — designed 1280x720 thumbnails for long-form videos.

WHY (gap identified 2026-09-09): all 108 videos on this channel use an
auto-picked frame as their thumbnail. On Shorts that barely matters -- the
feed decides and this account tier cannot even see impressions/CTR. On
LONG-FORM it is the primary click lever, so shipping a documentary with a
random b-roll frame wastes the format's main advantage.

Design rules applied (standard high-CTR practice: high contrast, one clear
subject, minimal text):
  - 3-5 words maximum, enormous type
  - heavy dark scrim so text survives any underlying frame
  - one accent colour for the payoff word
  - a real frame from the video as the base, so it is honest about content
"""
import os
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

W, H = 1280, 720


def _font(size, bold=True):
    from PIL import ImageFont
    for p in ["C:\\Windows\\Fonts\\Impact.ttf",
              "C:\\Windows\\Fonts\\arialbd.ttf",
              "C:\\Windows\\Fonts\\arial.ttf"]:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = f"{cur} {w}".strip()
        if draw.textbbox((0, 0), t, font=font)[2] <= max_w or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def make(video_path: str, out_path: str, line1: str, line2: str = "",
         accent=(255, 210, 40), frame_t: float = None) -> str:
    """Build a thumbnail from a real frame of the video."""
    from moviepy import VideoFileClip

    clip = VideoFileClip(video_path)
    t = frame_t if frame_t is not None else clip.duration * 0.12
    frame = clip.get_frame(min(t, clip.duration - 0.1))
    clip.close()

    img = Image.fromarray(frame).convert("RGB")
    # cover-fit to 1280x720
    sw, sh = img.size
    scale = max(W / sw, H / sh)
    img = img.resize((int(sw * scale), int(sh * scale)), Image.Resampling.LANCZOS)
    cw, ch = img.size
    img = img.crop(((cw - W) // 2, (ch - H) // 2, (cw - W) // 2 + W, (ch - H) // 2 + H))

    # darken + slight blur so type reads at any size (mobile is tiny)
    img = ImageEnhance.Brightness(img).enhance(0.45)
    img = img.filter(ImageFilter.GaussianBlur(radius=2))
    img = ImageEnhance.Contrast(img).enhance(1.15)

    draw = ImageDraw.Draw(img)

    # main line -- as large as will fit
    size = 150
    font = _font(size)
    lines = _wrap(draw, line1, font, W - 120)
    while (len(lines) > 2 or max(draw.textbbox((0, 0), l, font=font)[2] for l in lines) > W - 120) and size > 70:
        size -= 6
        font = _font(size)
        lines = _wrap(draw, line1, font, W - 120)

    line_h = int(size * 1.05)
    total_h = line_h * len(lines) + (90 if line2 else 0)
    y = (H - total_h) // 2

    for l in lines:
        bb = draw.textbbox((0, 0), l, font=font)
        x = (W - (bb[2] - bb[0])) // 2
        draw.text((x, y), l, font=font, fill=(255, 255, 255),
                  stroke_width=9, stroke_fill=(0, 0, 0))
        y += line_h

    if line2:
        f2 = _font(78)
        bb = draw.textbbox((0, 0), line2, font=f2)
        x = (W - (bb[2] - bb[0])) // 2
        draw.text((x, y + 14), line2, font=f2, fill=accent,
                  stroke_width=8, stroke_fill=(0, 0, 0))

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    img.save(out_path, "JPEG", quality=92)
    print(f"thumbnail -> {out_path} ({os.path.getsize(out_path)//1024} KB)")
    return out_path


if __name__ == "__main__":
    make("output/videos/doc_athletes_broke_v2.mp4",
         "output/thumbnails/athletes_broke.jpg",
         "78% IS A LIE",
         "the real number is worse")
