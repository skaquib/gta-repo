"""
thumbnail_generator.py
=======================
Generates YouTube thumbnail candidates from a rendered video: grabs a few
candidate frames, overlays high-contrast hook text, and tracks which variant
was uploaded per video so a future CTR pass (youtube_analytics_client.py /
viral_analytics.py) can learn which style wins and bias future generation.

CTR is driven almost entirely by thumbnail + title, and no thumbnail was ever
being uploaded to YouTube before this module existed.
"""

import os
import re
import json
import time
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter

try:
    from moviepy import VideoFileClip
except ImportError:
    from moviepy.editor import VideoFileClip

import config
from logger import log

THUMB_DIR   = os.path.join(config.OUTPUT_DIR, "thumbnails")
TESTS_FILE  = os.path.join(config.OUTPUT_DIR, "thumbnail_tests.json")
THUMB_SIZE  = (1280, 720)  # YouTube's recommended thumbnail size

_FONT_CACHE = {}


def _get_font(size: int, bold: bool = True, hindi: bool = False) -> ImageFont.FreeTypeFont:
    key = (size, bold, hindi)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    if hindi:
        # Impact/Arial have no Devanagari glyphs -- Nirmala UI ships on Windows.
        paths = ["C:\\Windows\\Fonts\\Nirmala.ttc", "C:\\Windows\\Fonts\\mangal.ttf"]
    else:
        paths = [
            "C:\\Windows\\Fonts\\Impact.ttf",
            "C:\\Windows\\Fonts\\arialbd.ttf" if bold else "C:\\Windows\\Fonts\\arial.ttf",
        ]
    font = None
    for p in paths:
        if os.path.exists(p):
            try:
                font = ImageFont.truetype(p, size)
                break
            except Exception:
                pass
    if not font:
        font = ImageFont.load_default()
    _FONT_CACHE[key] = font
    return font


def _extract_thumbnail_fragment(script: dict) -> str:
    """Pull a short, punchy FRAGMENT for the thumbnail -- not the full hook.
    A thumbnail that just restates the title/hook verbatim collapses the
    curiosity gap that actually drives the click: the strongest thumbnail/
    title pairs show a piece of the puzzle each, not the same sentence
    twice. Prefer a leading number/stat (most of our hooks open with one --
    "13 goals", "2-1", "3 World Cups"); fall back to a short clause."""
    hook = (script.get("visual_hook") or script.get("hook", "") or script.get("title", "")).strip()
    words = hook.split()

    def _clean(w: str) -> str:
        return w.strip(".,!?\"'")

    # Find the first number-like token anywhere in the opening words (not
    # just position 0 -- "England's 2-1 win" has the number 2nd), and take
    # a tight window around it for a short, punchy fragment.
    for i, w in enumerate(words[:8]):
        if re.search(r"\d", w):
            return " ".join(_clean(x) for x in words[i:i + 2]).upper()

    return " ".join(_clean(w) for w in words[:4]).upper()


def _frame_energy(img: Image.Image) -> float:
    """Rough proxy for how 'dynamic'/attention-grabbing a frame looks --
    edge density as a stand-in for motion/action detail, since this
    pipeline has no face/emotion detector. Frames with more visual
    complexity read as an action/climax moment rather than a flat,
    static establishing shot -- closer to the expressive-frame principle
    behind high-CTR thumbnails."""
    gray = img.convert("L").resize((160, 284))  # downsample for speed
    edges = gray.filter(ImageFilter.FIND_EDGES)
    return float(np.array(edges, dtype=np.float32).std())


def _grab_frame(video_path: str, t: float) -> Image.Image:
    vc = VideoFileClip(video_path)
    t = min(max(0.0, t), max(0.0, vc.duration - 0.1))
    frame = vc.get_frame(t)
    vc.close()
    return Image.fromarray(frame)


def _fill_crop(img: Image.Image, size: tuple) -> Image.Image:
    """Resize+center-crop to exactly `size`, filling the frame (no letterboxing)."""
    target_w, target_h = size
    src_w, src_h = img.size
    src_ratio, target_ratio = src_w / src_h, target_w / target_h
    if src_ratio > target_ratio:
        new_h = target_h
        new_w = int(new_h * src_ratio)
    else:
        new_w = target_w
        new_h = int(new_w / src_ratio)
    img = img.resize((new_w, new_h))
    x1, y1 = (new_w - target_w) // 2, (new_h - target_h) // 2
    return img.crop((x1, y1, x1 + target_w, y1 + target_h))


def _draw_hook_text(img: Image.Image, text: str, hindi: bool = False) -> Image.Image:
    """High-contrast, mobile-legible hook text overlay — this is what actually
    drives CTR in the Shorts/browse feed at thumbnail size."""
    img = _fill_crop(img.convert("RGB"), THUMB_SIZE)
    target_w, target_h = THUMB_SIZE

    # Darken slightly so white stroked text stays legible over any frame
    img = ImageEnhance.Brightness(img).enhance(0.85)
    img = ImageEnhance.Contrast(img).enhance(1.1)

    draw = ImageDraw.Draw(img)
    font = _get_font(88, bold=True, hindi=hindi)

    # Devanagari has no concept of uppercase -- .upper() is a no-op there but
    # a harmless one, so this stays a single code path for both languages.
    words = text.upper().split()
    lines, cur = [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        bbox = draw.textbbox((0, 0), trial, font=font)
        if bbox[2] - bbox[0] > target_w - 80 and cur:
            lines.append(cur)
            cur = w
        else:
            cur = trial
    if cur:
        lines.append(cur)
    lines = lines[:3]

    line_h = font.size + 14
    y = 50
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        x = (target_w - w) // 2
        draw.text((x, y), line, font=font, fill=(255, 255, 255),
                   stroke_width=8, stroke_fill=(0, 0, 0))
        y += line_h

    return img


def generate_thumbnails(video_path: str, script: dict, count: int = 3) -> list:
    """Generate `count` candidate thumbnails from a rendered video. Samples
    several frames concentrated in the hook segment (where the highest-
    energy visual moments live), scores each by visual "energy" as a proxy
    for how expressive/dynamic it looks, and returns them ranked
    best-first -- index 0 (the default upload pick) is the highest-scoring
    frame, not just whatever was at a fixed timestamp."""
    os.makedirs(THUMB_DIR, exist_ok=True)
    fragment = _extract_thumbnail_fragment(script)
    is_hindi = script.get("lang") == "hi"

    try:
        vc = VideoFileClip(video_path)
        duration = vc.duration
        vc.close()
    except Exception as e:
        log(f"Thumbnail: could not read video duration: {e}")
        return []

    # Sample more candidates than we need, weighted toward the hook segment
    # (roughly the first 15-20% of the video), then rank by energy instead
    # of trusting a fixed timestamp to land on an expressive moment.
    sample_fracs = [0.05, 0.10, 0.15, 0.20, 0.30, 0.45, 0.60]
    candidates = []
    for frac in sample_fracs:
        t = min(duration - 0.1, max(0.0, duration * frac))
        try:
            frame = _grab_frame(video_path, t)
            candidates.append((_frame_energy(frame), t, frame))
        except Exception as e:
            log(f"Thumbnail: frame sample at {frac:.2f} failed: {e}")

    if not candidates:
        return []

    candidates.sort(key=lambda c: c[0], reverse=True)
    top = candidates[:count]

    base = os.path.splitext(os.path.basename(video_path))[0]
    paths = []
    for i, (energy, t, frame) in enumerate(top):
        try:
            thumb = _draw_hook_text(frame, fragment, hindi=is_hindi)
            out_path = os.path.join(THUMB_DIR, f"{base}_v{i}.jpg")
            thumb.save(out_path, quality=90)
            paths.append(out_path)
            log(f"  Thumbnail variant {i}: t={t:.1f}s energy={energy:.1f}")
        except Exception as e:
            log(f"Thumbnail variant {i} failed: {e}")

    return paths


def _load_tests() -> dict:
    if os.path.exists(TESTS_FILE):
        try:
            with open(TESTS_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def record_variant(video_id: str, thumb_path: str, variant_index: int):
    """Track which thumbnail variant was uploaded for a video so a later CTR
    pass can compare variants and bias future thumbnail generation."""
    tests = _load_tests()
    tests[video_id] = {
        "thumb_path": thumb_path,
        "variant_index": variant_index,
        "uploaded_at": time.time(),
    }
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    with open(TESTS_FILE, "w", encoding="utf-8") as f:
        json.dump(tests, f, indent=2)
