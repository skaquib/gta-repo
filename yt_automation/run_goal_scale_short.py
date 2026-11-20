"""
run_goal_scale_short.py — "Every sport's goal, drawn TO SCALE" (2026-10-23).

Why this format (data, see GROWTH_PLAN.md): every Short so far -- three
topics, English and Hindi narration -- stopped at ~1K views. The test
audiences are mixed-language (Barca Short: ID, IN, BR, BD, UZ), and the
channel's best retention (bowling lane, 0.63) and the 4.9M "fastest speeds"
countdown both SHOW the answer instead of illustrating it with generic
clips. So this Short is visual-first: the fact is the picture, readable
with the sound off, with a countdown that makes viewers wait for the reveal.

Fully original and free: motion graphics drawn in code (no stock, no AI
images -- no altered-content label needed), local Kokoro voice, synthesized
music. Each narration line is generated separately so every goal appears
exactly when it's named.

Facts (checked 2026-10-23): ice hockey 1.83 x 1.22 m (6 x 4 ft); water polo
3 x 0.9 m (crossbar 0.9 m above water in deep pools); handball 3 x 2 m;
field hockey 3.66 x 2.14 m (FIH); football 7.32 x 2.44 m (IFAB Law 1).
Football area 17.86 m^2 / ice hockey 2.23 m^2 = 8.0x. Lacrosse was dropped
(dimensions not verified).
"""
import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import config

config.assert_safe_pipeline()

import pro_shorts_creator as psc
import music_generator
import copyright_compliance as cc
from logger import log

VIDEO_ID = "goal_scale_short"
W, H, FPS = 1080, 1920, 30
GROUND_Y = 1240

# (name, width m, height m, colour)
GOALS = [
    ("ICE HOCKEY",   1.83, 1.22, (255, 80, 80)),
    ("WATER POLO",   3.00, 0.90, (80, 200, 255)),
    ("HANDBALL",     3.00, 2.00, (255, 200, 60)),
    ("FIELD HOCKEY", 3.66, 2.14, (190, 120, 255)),
    ("FOOTBALL",     7.32, 2.44, (255, 255, 255)),
]

# (spoken line, goals shown, headline, subline)
SEGMENTS = [
    ("Every sport's goal, drawn to scale. Which one is the biggest?", 0,
     "EVERY SPORT'S GOAL", "DRAWN TO SCALE"),
    ("Ice hockey. One point eight metres wide.", 1, "ICE HOCKEY", "1.83 m × 1.22 m"),
    ("Water polo. Three metres, but under a metre high.", 2, "WATER POLO", "3 m × 0.9 m"),
    ("Handball. Three metres by two.", 3, "HANDBALL", "3 m × 2 m"),
    ("Field hockey. Three point six six.", 4, "FIELD HOCKEY", "3.66 m × 2.14 m"),
    ("And football. Seven point three two metres.", 5, "FOOTBALL", "7.32 m × 2.44 m"),
    ("That's eight times the size of an ice hockey goal.", 5, "8× BIGGER", "than an ice hockey goal"),
    ("Which goal would you want to defend? Comment below.", 5, "WHICH WOULD", "YOU DEFEND?"),
]

SCRIPT = {
    "hook": SEGMENTS[0][0],
    "body": " ".join(s[0] for s in SEGMENTS[1:-1]),
    "cta": SEGMENTS[-1][0],
    "title": "Every Sport's Goal, Drawn to SCALE ⚽🏒 #shorts",
    "tags": ["goal size", "to scale", "football facts", "sports facts", "soccer facts",
             "ice hockey", "handball", "water polo", "field hockey", "comparison", "shorts"],
    "seo_description": (
        "Every sport's goal drawn to scale next to a 1.8 m person: ice hockey (1.83 x 1.22 m), "
        "water polo (3 x 0.9 m), handball (3 x 2 m), field hockey (3.66 x 2.14 m) and football "
        "(7.32 x 2.44 m) -- 8x the area of an ice hockey goal. #football #sports #shorts"
    ),
}

_FONT = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
_fonts = {}


def font(size):
    if size not in _fonts:
        try:
            _fonts[size] = ImageFont.truetype(_FONT, size)
        except OSError:
            _fonts[size] = psc.get_font(size, bold=True)
    return _fonts[size]


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def build_voice():
    """One Kokoro take per segment -> (concatenated wav, segment start times)."""
    import soundfile as sf
    k = psc._get_kokoro()
    pieces, starts, t = [], [], 0.25
    sr = 24000
    gap = np.zeros(int(sr * 0.18), dtype=np.float32)
    pieces.append(np.zeros(int(sr * 0.25), dtype=np.float32))
    for line, *_ in SEGMENTS:
        samples, sr = k.create(line, voice="am_michael", speed=1.12, lang="en-us")
        starts.append(t)
        pieces += [samples.astype(np.float32), gap]
        t += len(samples) / sr + len(gap) / sr
    os.makedirs(config.AUDIO_DIR, exist_ok=True)
    out = os.path.join(config.AUDIO_DIR, f"{VIDEO_ID}_vo.wav")
    sf.write(out, np.concatenate(pieces), sr)
    out = psc.normalize_voice(out)
    return out, starts, t


def draw_person(d, cx, s, alpha=200):
    """1.8 m silhouette, feet on the ground line."""
    h = 1.8 * s
    col = (170, 180, 195, alpha)
    head_r = h * 0.065
    top = GROUND_Y - h
    d.ellipse([cx - head_r, top, cx + head_r, top + 2 * head_r], fill=col)
    bw = h * 0.13
    d.rounded_rectangle([cx - bw, top + 2.2 * head_r, cx + bw, top + h * 0.55],
                        radius=max(2, bw * 0.4), fill=col)
    lw = bw * 0.42
    d.rectangle([cx - bw * 0.95, top + h * 0.53, cx - bw * 0.95 + lw * 2, GROUND_Y], fill=col)
    d.rectangle([cx + bw * 0.95 - lw * 2, top + h * 0.53, cx + bw * 0.95, GROUND_Y], fill=col)


def draw_goal(d, gw, gh, s, col, grow=1.0, alpha=255, net=True, cx=W / 2):
    w, h = gw * s, gh * s * grow
    x0, x1 = cx - w / 2, cx + w / 2
    y0 = GROUND_Y - h
    t = max(5, 0.12 * s)
    c = col + (alpha,)
    if net and h > 4:
        nc = col + (int(alpha * 0.28),)
        step = max(10, 0.25 * s)
        x = x0
        while x <= x1:
            d.line([(x, y0), (x, GROUND_Y)], fill=nc, width=2)
            x += step
        y = GROUND_Y
        while y >= y0:
            d.line([(x0, y), (x1, y)], fill=nc, width=2)
            y -= step
    d.rectangle([x0 - t, y0 - t, x0, GROUND_Y], fill=c)
    d.rectangle([x1, y0 - t, x1 + t, GROUND_Y], fill=c)
    d.rectangle([x0 - t, y0 - t, x1 + t, y0], fill=c)


def centered(d, y, text, size, fill=(255, 255, 255)):
    f = font(size)
    while d.textlength(text, font=f) > W - 80 and size > 30:
        size -= 4
        f = font(size)
    d.text(((W - d.textlength(text, font=f)) / 2, y), text, font=f, fill=fill,
           stroke_width=max(3, size // 14), stroke_fill=(0, 0, 0))


def make_frame_fn(starts, duration):
    def scale_for(n_goals):
        maxw = max([g[1] for g in GOALS[:n_goals]] or [1.83])
        return min(420.0, 1010.0 / (maxw + 1.0))

    seg_scales = [scale_for(s[1]) for s in SEGMENTS]

    bg = Image.new("RGB", (W, H))
    bd = ImageDraw.Draw(bg)
    for y in range(H):
        if y < GROUND_Y:
            r = y / GROUND_Y
            bd.line([(0, y), (W, y)], fill=(int(8 + 10 * r), int(14 + 22 * r), int(30 + 20 * r)))
        else:
            stripe = ((y - GROUND_Y) // 70) % 2
            bd.line([(0, y), (W, y)], fill=(20, 92, 44) if stripe else (16, 78, 37))
    bd.line([(0, GROUND_Y), (W, GROUND_Y)], fill=(235, 245, 235), width=6)

    def seg_at(t):
        i = 0
        for k, st in enumerate(starts):
            if t >= st:
                i = k
        return i

    def frame(t):
        i = seg_at(t)
        t_in = t - starts[i]
        prev_scale = seg_scales[i - 1] if i > 0 else seg_scales[0]
        s = prev_scale + (seg_scales[i] - prev_scale) * ease(t_in / 0.7)
        # slow push-in so the frame is never static
        s *= 1.0 + 0.015 * math.sin(t * 1.3)

        img = bg.copy().convert("RGBA")
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)

        n = SEGMENTS[i][1]
        cx = W / 2 - 0.45 * s  # leave room on the right for the person
        for gi in range(n):
            gw, gh, col = GOALS[gi][1], GOALS[gi][2], GOALS[gi][3]
            newest = gi == n - 1 and SEGMENTS[i][1] != SEGMENTS[i - 1][1] if i > 0 else False
            grow = ease(t_in / 0.35) if newest else 1.0
            alpha = 255 if gi == n - 1 else 150
            draw_goal(d, gw, gh, s, col, grow=grow, alpha=alpha, net=(gi == n - 1), cx=cx)
        # person stands just right of the widest goal shown
        maxw = max([g[1] for g in GOALS[:n]] or [1.83])
        draw_person(d, cx + (maxw / 2 + 0.55) * s, s)

        head, sub = SEGMENTS[i][2], SEGMENTS[i][3]
        pop = 0.85 + 0.15 * ease(t_in / 0.25)
        hs = int(118 * pop)
        col = GOALS[n - 1][3] if (n and i > 0 and i < 6) else (255, 230, 80) if i >= 6 else (255, 255, 255)
        centered(d, 470, head, hs, fill=col)
        centered(d, 470 + hs + 20, sub, 72)
        if i == 0:
            q = int(260 + 20 * math.sin(t * 6))
            centered(d, 720, "?", q, fill=(255, 230, 80))

        # spoken-line caption, sound-off friendly
        line = SEGMENTS[i][0]
        f = font(50)
        words, rows, cur = line.split(), [], ""
        for w_ in words:
            trial = (cur + " " + w_).strip()
            if d.textlength(trial, font=f) > W - 140:
                rows.append(cur)
                cur = w_
            else:
                cur = trial
        rows.append(cur)
        for r_i, row in enumerate(rows):
            d.text(((W - d.textlength(row, font=f)) / 2, 1400 + r_i * 66), row, font=f,
                   fill=(255, 255, 255), stroke_width=4, stroke_fill=(0, 0, 0))
        d.text((24, 20), getattr(config, "CHANNEL_NAME", "FramedFacts"), font=font(30),
               fill=(255, 255, 255, 170))

        img.alpha_composite(layer)
        return np.array(img.convert("RGB"))

    return frame


def build():
    from moviepy import VideoClip, AudioFileClip, CompositeAudioClip
    log("Voice (Kokoro, per-segment for exact sync)...")
    vo_path, starts, total = build_voice()
    duration = total + 0.6
    log(f"Duration {duration:.1f}s, segment starts: {[round(x, 2) for x in starts]}")

    music_path = music_generator.get_original_music("energetic", audio_dir=config.AUDIO_DIR,
                                                    duration=duration)
    check = cc.validate_before_upload(SCRIPT, [], music_path)
    cc.save_compliance_report(check, video_id=VIDEO_ID)
    if not check["passed"]:
        raise RuntimeError(f"COMPLIANCE FAILED: {check['issues']}")

    video = VideoClip(make_frame_fn(starts, duration), duration=duration)
    vo = AudioFileClip(vo_path)
    music = psc._vol(psc._dur(AudioFileClip(music_path), duration), 0.10)
    layers = [music, psc._vol(vo, 1.5)]
    try:
        layers.append(psc._vol(AudioFileClip(music_generator.get_hook_hit()), 0.8))
    except Exception as e:
        log(f"No hook hit ({e})")
    video = psc._audio(video, psc._dur(CompositeAudioClip(layers), duration))

    out = os.path.join(config.VIDEOS_DIR, f"{VIDEO_ID}.mp4")
    os.makedirs(config.VIDEOS_DIR, exist_ok=True)
    video.write_videofile(out, fps=FPS, codec="libx264", audio_codec="aac", audio_bitrate="192k",
                          threads=8, logger=None,
                          ffmpeg_params=["-crf", "18", "-preset", "faster", "-pix_fmt", "yuv420p",
                                         "-movflags", "+faststart"])
    # Word timings for the uploaded caption track (psc.upload reads this cache).
    words = []
    for (line, *_), st, nxt in zip(SEGMENTS, starts, starts[1:] + [total]):
        toks = line.split()
        step = (nxt - st - 0.18) / len(toks)
        words += [{"word": w_, "start": round(st + k * step, 2), "end": round(st + (k + 1) * step, 2)}
                  for k, w_ in enumerate(toks)]
    import json
    with open(vo_path + ".words.json", "w", encoding="utf-8") as f:
        json.dump(words, f)
    log(f"BUILD COMPLETE (not uploaded yet) -> {out}")
    return out, vo_path


if __name__ == "__main__":
    build()
