"""
realistic_video.py — engine for realistic AI-visual long videos: "extreme animals, shown to scale".

Owner, 2026-11-04: high quality, trending story and visuals. Follows VIRAL_PLAYBOOK.md:
a new picture every 2-4 s, realistic cinematic stills (Gemini on the Vertex free credit)
with slow camera moves, short Veo clips for key moments, and our own code-drawn layer on
top: a depth meter with pressure, chapter cards, labels and "shown next to you" scale cards.
Every number and word on screen is drawn here, never by the AI.

Segment = dict(line, chapter=None, depth=None, label=None, sfx=None, shots=[...]) where a
shot is "img:key", "clip:key" or "scale:key" (scale cards are defined in SCALES).
"""
import concurrent.futures as cf
import math
import os
import shutil

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import config

W, H = 1920, 1080
HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "fonts", "Montserrat[wght].ttf")
STYLE = ("photorealistic, cinematic underwater wildlife photography, natural colours, physically accurate anatomy, "
         "high detail, soft volumetric light, 16:9, no text, no letters, no numbers, no watermark, no logos, no people's faces")
CUT_STYLE = ("full body in exact side profile, entire animal visible with space around it, isolated on a pure black "
             "background, dramatic rim lighting, scientifically accurate anatomy and proportions, photorealistic, "
             "no text, no letters, no watermark")


def font(size, weight=800):
    f = ImageFont.truetype(FONT, int(size))
    try:
        f.set_variation_by_axes([weight])
    except (OSError, AttributeError):
        pass
    return f


def asset_dir(vid):
    d = os.path.join(config.OUTPUT_DIR, "real_assets", vid)
    os.makedirs(d, exist_ok=True)
    return d


# ── asset generation (Vertex AI free credit first, see genai_clients.py) ──────
def gen_images(prompts: dict, vid: str, cutouts=(), workers=4, aspect="16:9"):
    """prompts: key -> description. Keys in `cutouts` get the isolated-on-black style (scale cards)."""
    import image_gen
    d = asset_dir(vid)

    def one(item):
        key, p = item
        path = os.path.join(d, f"{key}.png")
        if os.path.exists(path):
            return key, "cached"
        full = f"{p}. {CUT_STYLE if key in cutouts else STYLE.replace('16:9', aspect + ' vertical' if aspect == '9:16' else aspect)}"
        try:
            image_gen._gemini(full, path, aspect=aspect)
            return key, "ok"
        except Exception as e:
            return key, f"FAILED {str(e)[:120]}"

    with cf.ThreadPoolExecutor(workers) as ex:
        res = dict(ex.map(one, prompts.items()))
    return res


def gen_clips(clips: dict, vid: str, seconds=8, model="veo-3.1-lite-generate-001", batch=6, rounds=6, aspect="16:9",
              style=None):
    """clips: key -> motion prompt; animates the still of the same key (image-to-video) on Vertex AI.
    Submits `batch` jobs at a time and retries failures (quota limits) for a few rounds. Cached by file."""
    import time
    from google.genai import types
    import genai_clients
    client = genai_clients.vertex_client("us-central1")
    d = asset_dir(vid)
    status = {}
    for _ in range(rounds):
        todo = [k for k in clips if not os.path.exists(os.path.join(d, f"{k}.mp4"))]
        if not todo:
            break
        for n in range(0, len(todo), batch):
            ops = {}
            for k in todo[n:n + batch]:
                img = types.Image(image_bytes=open(os.path.join(d, f"{k}.png"), "rb").read(), mime_type="image/png")
                prompt = (f"{clips[k]}. Keep every animal's anatomy, proportions and colours exactly as in the starting image. "
                          + (style or "Photorealistic, cinematic, natural motion, widescreen 16:9, no text, no captions, no logos."))
                try:
                    genai_clients.charge("veo-lite-s" if "lite" in model else ("veo-fast-s" if "fast" in model else "veo-std-s"),
                                         seconds, f"{vid}/{k}")
                    ops[k] = client.models.generate_videos(
                        model=model, prompt=prompt, image=img,
                        config=types.GenerateVideosConfig(duration_seconds=seconds, aspect_ratio=aspect, resolution="720p",
                                                          generate_audio=False, number_of_videos=1))
                except Exception as e:
                    status[k] = f"submit failed: {str(e)[:100]}"
            deadline = time.time() + 600
            while ops and time.time() < deadline:
                time.sleep(8)
                for k, op in list(ops.items()):
                    try:
                        op = client.operations.get(op)
                    except Exception as e:
                        status[k] = f"poll failed: {str(e)[:80]}"
                        continue
                    if not op.done:
                        ops[k] = op
                        continue
                    del ops[k]
                    try:
                        v = op.response.generated_videos[0].video
                        with open(os.path.join(d, f"{k}.mp4"), "wb") as f:
                            f.write(v.video_bytes)
                        status[k] = "ok"
                    except Exception as e:
                        status[k] = f"failed: {str(getattr(op, 'error', None) or e)[:100]}"
        time.sleep(20)
    return status


def contact_sheet(vid, keys, out, cols=6, tw=320):
    d = asset_dir(vid)
    th = int(tw * 9 / 16)
    rows = (len(keys) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * (th + 22)), (0, 0, 0))
    dr = ImageDraw.Draw(sheet)
    for n, k in enumerate(keys):
        p = os.path.join(d, f"{k}.png")
        x, y = (n % cols) * tw, (n // cols) * (th + 22)
        if os.path.exists(p):
            sheet.paste(Image.open(p).convert("RGB").resize((tw, th)), (x, y))
        dr.text((x + 4, y + th + 3), k[:34], fill=(255, 255, 0), font=font(15, 600))
    sheet.save(out, quality=85)
    return out


# ── look: grade, vignette, grain ──────────────────────────────────────────────
def _vignette():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    return np.clip(1.08 - 0.38 * r ** 2, 0.55, 1.0)[..., None]


_VIG = None
_GRAIN = np.random.default_rng(3).normal(0, 4.0, (H + 64, W + 64)).astype(np.float32)


def grade(arr, t):
    global _VIG
    if _VIG is None:
        _VIG = _vignette()
    a = arr.astype(np.float32) * _VIG
    ox, oy = int(t * 37) % 64, int(t * 53) % 64
    a += _GRAIN[oy:oy + H, ox:ox + W, None]
    return np.clip(a, 0, 255).astype(np.uint8)


# ── stills and clips ──────────────────────────────────────────────────────────
_stills, _clips = {}, {}


def still(vid, key):
    if key not in _stills:
        im = Image.open(os.path.join(asset_dir(vid), f"{key}.png")).convert("RGB")
        im = im.resize((int(W * 1.18), int(H * 1.18)), Image.LANCZOS)   # headroom for slow moves
        _stills[key] = im
    return _stills[key]


def _move(seed, p):
    """Slow push-in or pull-out with a gentle drift; seed picks the variant."""
    rng = np.random.default_rng(seed)
    z0, z1 = (1.0, 1.12) if seed % 2 == 0 else (1.12, 1.0)
    cx0, cy0 = 0.5 + rng.uniform(-0.05, 0.05), 0.5 + rng.uniform(-0.04, 0.04)
    cx1, cy1 = 0.5 + rng.uniform(-0.05, 0.05), 0.5 + rng.uniform(-0.04, 0.04)
    e = p * p * (3 - 2 * p)
    return z0 + (z1 - z0) * e, cx0 + (cx1 - cx0) * e, cy0 + (cy1 - cy0) * e


def frame_still(vid, key, p, seed):
    im = still(vid, key)
    z, cx, cy = _move(seed, p)
    w, h = im.width / z, im.height / z          # z=1 shows the whole still, z=1.12 a 12% push-in
    x0 = min(max(cx * im.width - w / 2, 0), im.width - w)
    y0 = min(max(cy * im.height - h / 2, 0), im.height - h)
    return np.asarray(im.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + w, y0 + h)))


CLIP_TRIM = {}     # key -> seconds of the clip that passed anatomy QA (AI video can drift later in a clip)


MIN_SPEED = 0.45


def frame_clip(vid, key, t_in, dur, start=0.0):
    if key not in _clips:
        from moviepy import VideoFileClip
        _clips[key] = VideoFileClip(os.path.join(asset_dir(vid), f"{key}.mp4"), audio=False)
    c = _clips[key]
    usable = min(c.duration, CLIP_TRIM.get(key, c.duration)) - 0.05
    start = min(start, max(0.0, usable - min(dur, usable) * 0.7))
    if usable - start < MIN_SPEED * dur:                     # a later start would run out: start earlier instead
        start = max(0.0, usable - MIN_SPEED * dur)
    avail = usable - start
    speed = min(1.0, max(MIN_SPEED, avail / max(dur, 0.1)))  # stretch gently (slow motion) rather than freeze
    pos = start + t_in * speed
    if pos > usable:                                         # never hold a frozen frame: drift back (ping-pong)
        pos = max(0.0, usable - (pos - usable))
    fr = c.get_frame(pos)
    return np.asarray(Image.fromarray(fr).resize((W, H), Image.BILINEAR))


def has_clip(vid, key):
    return os.path.exists(os.path.join(asset_dir(vid), f"{key}.mp4"))


# ── scale cards ("shown next to you") ─────────────────────────────────────────
def _human(height_px):
    """Simple standing-person silhouette, white with a soft glow, feet at the bottom."""
    s = height_px / 175.0
    im = Image.new("RGBA", (int(80 * s) + 8, int(180 * s) + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = (235, 245, 255, 255)
    cx = im.width / 2
    d.ellipse((cx - 11 * s, 2 * s, cx + 11 * s, 26 * s), fill=c)
    d.rounded_rectangle((cx - 17 * s, 28 * s, cx + 17 * s, 95 * s), radius=8 * s, fill=c)
    d.rounded_rectangle((cx - 26 * s, 30 * s, cx - 18 * s, 90 * s), radius=4 * s, fill=c)
    d.rounded_rectangle((cx + 18 * s, 30 * s, cx + 26 * s, 90 * s), radius=4 * s, fill=c)
    d.rounded_rectangle((cx - 16 * s, 92 * s, cx - 2 * s, 176 * s), radius=5 * s, fill=c)
    d.rounded_rectangle((cx + 2 * s, 92 * s, cx + 16 * s, 176 * s), radius=5 * s, fill=c)
    return im


def _phone(h_px):
    w_px = h_px * 0.48
    im = Image.new("RGBA", (int(w_px) + 6, int(h_px) + 6), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((3, 3, 3 + w_px, 3 + h_px), radius=w_px * 0.15, fill=(30, 34, 44, 255),
                        outline=(235, 245, 255, 255), width=max(2, int(h_px * 0.03)))
    return im


def _cutout(vid, key):
    """Animal image on black -> RGBA with alpha from brightness, cropped to the animal."""
    im = Image.open(os.path.join(asset_dir(vid), f"{key}.png")).convert("RGB")
    a = np.asarray(im).astype(np.float32)
    # background = median colour of the image border (often near-black, sometimes dark blue)
    border = np.concatenate([a[:12].reshape(-1, 3), a[-12:].reshape(-1, 3), a[:, :12].reshape(-1, 3), a[:, -12:].reshape(-1, 3)])
    bg = np.median(border, axis=0)
    dist = np.abs(a - bg).max(axis=2)
    alpha = np.clip((dist - 18) / 30, 0, 1)
    mask = Image.fromarray((alpha * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))
    rgba = im.convert("RGBA")
    rgba.putalpha(mask)
    box = Image.fromarray(((alpha > 0.35) * 255).astype(np.uint8)).getbbox() or (0, 0, im.width, im.height)
    return rgba.crop(box)


_scale_bg = None
_scale_cache = {}


def scale_card(vid, spec, p, bg=None):
    """spec: dict(cut=image key, name, length_m, ref='human'|'phone', note, bg=clip key).
    bg: the current frame of a moving, empty-water clip; it is softened and darkened so the animal reads."""
    global _scale_bg
    if _scale_bg is None:
        yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
        top, bot = np.array((14, 52, 78), np.float32), np.array((2, 8, 20), np.float32)
        _scale_bg = np.broadcast_to(top * (1 - yy) + bot * yy, (H, W, 3)).astype(np.uint8)
    key = spec["cut"]
    if key not in _scale_cache:
        _scale_cache[key] = _cutout(vid, key)
    animal = _scale_cache[key]
    ref = spec.get("ref", "human")
    ref_m = 1.75 if ref == "human" else 0.15
    L = spec["length_m"]
    span_m = max(L, ref_m) * 1.12 + ref_m * 1.6
    x0, x1, ground = 150, W - 150, 820
    ppm = (x1 - x0) / span_m
    if bg is not None:                                       # moving water behind the comparison
        soft = Image.fromarray(bg).resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(2))
        soft = np.asarray(soft.resize((W, H), Image.BILINEAR), dtype=np.float32)
        base = (soft * 0.62 + _scale_bg.astype(np.float32) * 0.38).clip(0, 255).astype(np.uint8)
    else:
        base = _scale_bg.copy()
    img = Image.fromarray(base).convert("RGBA")
    d = ImageDraw.Draw(img)
    # ruler: 4-7 labelled ticks with a "nice" step, minor ticks in between
    lab_step = next(x for x in (0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20) if x >= span_m / 6.5)
    minor = lab_step / (5 if lab_step in (0.5, 5, 10) else 2)
    d.line([(x0, ground + 18), (x1, ground + 18)], fill=(170, 220, 255, 220), width=4)
    n_minor = int(span_m / minor + 1e-6)
    per = int(round(lab_step / minor))
    for k in range(n_minor + 1):
        m = k * minor
        x = x0 + m * ppm
        if x > x1 + 1:
            break
        big = k % per == 0
        d.line([(x, ground + 18), (x, ground + (40 if big else 30))], fill=(170, 220, 255, 220), width=3 if big else 2)
        if big:
            lab = f"{m:g} m" if lab_step >= 1 else f"{round(m * 100):.0f} cm"
            d.text((x, ground + 46), lab, font=font(24, 600), fill=(170, 220, 255), anchor="mt")
    # reference (you / your phone) at the left
    rx = x0 + ref_m * 0.3 * ppm
    refim = _human(ref_m * ppm) if ref == "human" else _phone(ref_m * ppm)
    img.alpha_composite(refim, (int(rx), int(ground - refim.height + 4)))
    d.text((rx + refim.width / 2, ground - refim.height - 14), "YOU" if ref == "human" else "YOUR PHONE",
           font=font(30, 800), fill=(255, 255, 255), anchor="mb")
    # the animal, sliding in, scaled to its true length
    aw = L * ppm
    ah = animal.height * aw / animal.width
    e = min(1.0, p / 0.35)
    e = e * e * (3 - 2 * e)
    ax = x0 + (ref_m * 1.6) * ppm + (1 - e) * 220
    a_im = animal.resize((max(1, int(aw)), max(1, int(ah))), Image.LANCZOS)
    if e < 1:
        a_im = a_im.copy()
        a_im.putalpha(a_im.getchannel("A").point(lambda v: int(v * e)))
    bob = 0 if e < 1 else 7 * math.sin(p * 2 * math.pi * 0.9)        # the animal keeps swimming gently in place
    if e >= 1:                                                         # ...with a slow tilt, like a real swim
        a_im = a_im.rotate(1.3 * math.sin(p * 2 * math.pi * 0.6), resample=Image.BICUBIC, expand=False)
    img.alpha_composite(a_im, (int(ax + (0 if e < 1 else 10 * math.sin(p * math.pi))), int(ground - ah + ah * 0.08 + bob)))
    # length bracket over the animal
    by = int(ground - ah - 30)
    d = ImageDraw.Draw(img)
    d.line([(ax, by), (ax + aw, by)], fill=(255, 214, 70, int(255 * e)), width=4)
    for x in (ax, ax + aw):
        d.line([(x, by - 12), (x, by + 12)], fill=(255, 214, 70, int(255 * e)), width=4)
    txt = f"{spec['name'].upper()}  ·  {spec.get('size_text', f'{L:g} m')}"
    d.text((ax + aw / 2, by - 18), txt, font=font(40, 800), fill=(255, 214, 70), anchor="mb",
           stroke_width=3, stroke_fill=(0, 0, 0))
    if spec.get("note"):
        d.text((W / 2, 150), spec["note"], font=font(46, 800), fill=(255, 255, 255), anchor="mm",
               stroke_width=4, stroke_fill=(0, 0, 0))
    return np.asarray(img.convert("RGB"))


# ── overlays: depth meter, chapter cards, labels ──────────────────────────────
ZONES = [(0, "SUNLIGHT"), (200, "TWILIGHT"), (1000, "MIDNIGHT"), (4000, "ABYSS"), (6000, "HADAL"), (11000, "")]


def _depth_y(depth, top=150, bottom=930):
    """Piecewise scale: each zone gets an equal slice of the meter so all five are readable."""
    n = len(ZONES) - 1
    for i in range(n):
        a, b = ZONES[i][0], ZONES[i + 1][0]
        if depth <= b or i == n - 1:
            f = (min(depth, b) - a) / (b - a)
            return top + (i + max(0.0, f)) / n * (bottom - top)
    return bottom


_meter_base = None
MW, MX = 300, 196          # meter panel width and bar x inside it


def depth_meter(depth):
    """RGBA panel (300 x 1080) for the right edge: zone bar, zone names on the right,
    a marker with the current depth and pressure on the left."""
    global _meter_base
    if _meter_base is None:
        im = Image.new("RGBA", (MW, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        cols = [(90, 190, 240), (50, 110, 190), (30, 50, 120), (25, 25, 70), (40, 10, 40)]
        for i in range(len(ZONES) - 1):
            y0, y1 = _depth_y(ZONES[i][0]), _depth_y(ZONES[i + 1][0])
            d.rectangle((MX - 4, y0, MX + 4, y1), fill=cols[i] + (235,))
            d.text((MX + 14, (y0 + y1) / 2), ZONES[i][1], font=font(16, 700), fill=(205, 228, 245, 210), anchor="lm",
                   stroke_width=2, stroke_fill=(0, 0, 0, 160))
        for dep in (0, 200, 1000, 4000, 6000, 11000):
            y = _depth_y(dep)
            d.line([(MX - 8, y), (MX + 8, y)], fill=(220, 235, 250, 230), width=2)
        _meter_base = im
    im = _meter_base.copy()
    d = ImageDraw.Draw(im)
    y = _depth_y(depth)
    d.polygon([(MX - 7, y), (MX - 22, y - 9), (MX - 22, y + 9)], fill=(255, 214, 70, 255))
    d.text((MX - 28, y - 13), f"{depth:,.0f} m", font=font(26, 800), fill=(255, 255, 255), anchor="rm",
           stroke_width=3, stroke_fill=(0, 0, 0))
    d.text((MX - 28, y + 15), f"{1 + depth / 10.0:,.0f} atm", font=font(19, 700), fill=(255, 214, 70), anchor="rm",
           stroke_width=2, stroke_fill=(0, 0, 0))
    return im


_cards = {}


def chapter_card(title, depth):
    if title not in _cards:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        vert = np.clip((yy - 560) / 260, 0, 1) ** 1.5                 # fades in from mid-frame to the bottom
        horiz = np.clip(1.15 - xx / (W * 0.62), 0, 1) ** 1.3           # fades out towards the right
        g = np.zeros((H, W, 4), np.uint8)
        g[..., 3] = (185 * vert * horiz).astype(np.uint8)
        im = Image.fromarray(g)
        d = ImageDraw.Draw(im)
        dep = "" if depth is None else f"{depth:,.0f} m"
        d.text((110, 690), dep, font=font(110, 900), fill=(255, 214, 70), stroke_width=5, stroke_fill=(0, 0, 0))
        d.text((114, 830), title.upper(), font=font(52, 800), fill=(255, 255, 255), stroke_width=4, stroke_fill=(0, 0, 0))
        _cards[title] = im
    return _cards[title]


_labels = {}


def label_tag(text):
    if text not in _labels:
        f = font(40, 800)
        tw = int(ImageDraw.Draw(Image.new("RGB", (1, 1))).textlength(text, font=f))
        im = Image.new("RGBA", (tw + 70, 76), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, tw + 70, 76), radius=14, fill=(0, 0, 0, 150))
        d.rectangle((0, 0, 9, 76), fill=(255, 214, 70, 255))
        d.text((38, 38), text, font=f, fill=(255, 255, 255), anchor="lm")
        _labels[text] = im
    return _labels[text]


def _fade(im, a):
    if a >= 0.999:
        return im
    im = im.copy()
    im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    return im


# ── the frame function for motion_shorts.render_short ─────────────────────────
def frame_fn(segments, vid, scales):
    depth_at = []
    cur = 0
    for s in segments:
        if s.get("depth") is not None:
            cur = s["depth"]
        depth_at.append(cur)

    uses, offset = {}, {}
    for i, s in enumerate(segments):
        for k, sh in enumerate(s["shots"]):
            kind, key = sh.split(":", 1)
            if kind != "scale":
                n = uses.get(key, 0)
                offset[(i, k)] = (n * 2.7) % 5.5          # 1st use from 0 s, 2nd from 2.7 s, 3rd from 5.4 s ...
                uses[key] = n + 1

    def frame(t, i, t_in, starts):
        seg = segments[i]
        dur = (starts[i + 1] - starts[i]) if i + 1 < len(starts) else 4.0
        shots = seg["shots"]
        n = len(shots)
        k = min(n - 1, int(t_in / (dur / n)))
        sd, ts = dur / n, t_in - k * (dur / n)
        kind, key = shots[k].split(":", 1)
        if kind in ("img", "clip") and has_clip(vid, key):
            kind = "clip"                                  # real motion wherever a clip exists
        # long stills cut to a second framing halfway, so the picture changes every ~2-4 s
        sub = 1 if (kind == "img" and sd > 4.6 and ts > sd / 2) else 0
        p = (ts - sub * sd / 2) / (sd / 2 if kind == "img" and sd > 4.6 else sd)
        seed = hash((i, k, sub)) & 0xFFFF
        if kind == "img":
            base = frame_still(vid, key, min(1.0, p), seed)
        elif kind == "clip":
            base = frame_clip(vid, key, ts, sd, start=offset.get((i, k), 0.0))
        else:
            bgk = scales[key].get("bg", "deep_cold")
            base = scale_card(vid, scales[key], min(1.0, ts / sd),
                              bg=frame_clip(vid, bgk, ts, sd) if has_clip(vid, bgk) else None)
        out = Image.fromarray(grade(base, t) if kind != "scale" else base).convert("RGBA")
        # depth meter: glides to the new depth over 1.6 s
        prev = depth_at[i - 1] if i else 0
        dep = depth_at[i] if t_in > 1.6 or prev == depth_at[i] else prev + (depth_at[i] - prev) * (t_in / 1.6) ** 0.7
        out.alpha_composite(depth_meter(dep), (W - MW, 0))
        if seg.get("chapter") and seg.get("chapter_card", True):
            a = min(1.0, t_in / 0.4) * min(1.0, max(0.0, (3.4 - t_in) / 0.5))
            if a > 0:
                out.alpha_composite(_fade(chapter_card(seg["chapter"], depth_at[i] if i else None), a))
        if seg.get("label") and kind != "scale":
            a = min(1.0, max(0.0, (t_in - 0.3) / 0.35)) * min(1.0, max(0.0, (dur - t_in) / 0.4))
            if a > 0:
                tag = _fade(label_tag(seg["label"]), a)
                out.alpha_composite(tag, (90, H - 150))
        if seg.get("cta"):
            out.alpha_composite(cta_overlay(seg["cta"], min(1.0, t_in / dur)))
        if t < 9.0:      # honest on-screen note for the first seconds (also labelled on YouTube)
            d = ImageDraw.Draw(out)
            d.text((W - 260, H - 34), "AI-generated visuals", font=font(20, 600), fill=(220, 230, 240, 170), anchor="rm")
        d = ImageDraw.Draw(out)
        d.text((40, 34), "FramedFacts", font=font(24, 800), fill=(255, 255, 255, 120))
        return np.asarray(out.convert("RGB"))
    return frame


# ── end card: subscribe, bell, share (drawn in code) ─────────────────────────
def _ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def _cursor(scale=1.0):
    im = Image.new("RGBA", (int(60 * scale), int(80 * scale)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pts = [(4, 4), (4, 62), (18, 49), (29, 74), (39, 70), (28, 45), (47, 45)]
    d.polygon([(x * scale, y * scale) for x, y in pts], fill=(255, 255, 255, 255), outline=(0, 0, 0, 255), width=max(2, int(3 * scale)))
    return im


def _bell(size, on):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = (255, 255, 255, 255)
    s = size / 100
    d.pieslice((22 * s, 14 * s, 78 * s, 70 * s), 180, 360, fill=c)        # dome
    d.polygon([(22 * s, 42 * s), (78 * s, 42 * s), (88 * s, 74 * s), (12 * s, 74 * s)], fill=c)   # skirt
    d.rounded_rectangle((8 * s, 72 * s, 92 * s, 80 * s), radius=3 * s, fill=c)
    d.ellipse((42 * s, 80 * s, 58 * s, 94 * s), fill=c)                     # clapper
    d.ellipse((45 * s, 6 * s, 55 * s, 16 * s), fill=c)
    if on:                                                                 # ring lines
        for side in (-1, 1):
            for k, r in enumerate((10, 18)):
                x0 = 50 * s + side * (44 + r) * s
                d.arc((x0 - 12 * s, 18 * s, x0 + 12 * s, 58 * s), 300 if side > 0 else 120, 60 if side > 0 else 240,
                      fill=(255, 214, 70, 255), width=max(3, int(4 * s)))
    return im


def _pill(text, w, h, fill, fg=(255, 255, 255, 255), icon=None):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=h // 2, fill=fill)
    f = font(int(h * 0.42), 800)
    tw = d.textlength(text, font=f)
    x = (w - tw) / 2 + (h * 0.32 if icon else 0)
    if icon == "share":                                                     # curved share arrow
        ix, iy, r = x - h * 0.62, h / 2, h * 0.2
        d.arc((ix - r, iy - r * 0.2, ix + r * 1.6, iy + r * 2.2), 200, 300, fill=fg, width=max(4, h // 14))
        d.polygon([(ix + r * 1.2, iy - r * 1.2), (ix + r * 2.2, iy - r * 0.15), (ix + r * 1.1, iy + r * 0.8)], fill=fg)
    d.text((x, h / 2), text, font=f, fill=fg, anchor="lm")
    return im


def cta_overlay(kind, p):
    """kind 'subscribe': SUBSCRIBE is clicked (turns SUBSCRIBED), then the bell is clicked and rings.
    kind 'share': the subscribed state stays and a SHARE button pops in and is clicked."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # soft dark band so the buttons read over any clip
    band = np.zeros((H, W, 4), np.uint8)
    yy = np.linspace(0, 1, H)[:, None]
    band[..., 3] = (np.clip((yy - 0.55) / 0.45, 0, 1) * 170).astype(np.uint8)
    layer.alpha_composite(Image.fromarray(band, "RGBA"))
    a_in = _ease(p / 0.08) if kind == "subscribe" else 1.0
    by = int(H - 250 + (1 - a_in) * 80)
    bw, bh = 470, 110
    bx = W // 2 - bw // 2 - (180 if kind == "share" else 70)
    bell_x, bell_size = bx + bw + 40, 104
    share_x = bell_x + bell_size + 46
    click_sub, click_bell, click_share = 0.33, 0.62, 0.42
    subscribed = kind == "share" or p >= click_sub
    press = 0.94 if (kind == "subscribe" and click_sub <= p < click_sub + 0.035) else 1.0
    btn = _pill("SUBSCRIBED" if subscribed else "SUBSCRIBE", bw, bh,
                (70, 70, 74, 255) if subscribed else (230, 33, 23, 255))
    if press != 1.0:
        btn = btn.resize((int(bw * press), int(bh * press)), Image.LANCZOS)
    btn.putalpha(btn.getchannel("A").point(lambda v: int(v * a_in)))
    layer.alpha_composite(btn, (bx + (bw - btn.width) // 2, by + (bh - btn.height) // 2))
    bell_on = kind == "share" or p >= click_bell
    bell = _bell(bell_size, bell_on)
    if kind == "subscribe" and click_bell <= p < click_bell + 0.25:      # it rings
        bell = bell.rotate(18 * math.sin((p - click_bell) * 60) * (1 - (p - click_bell) / 0.25), resample=Image.BICUBIC)
    bell.putalpha(bell.getchannel("A").point(lambda v: int(v * a_in)))
    layer.alpha_composite(bell, (bell_x, by + 3))
    if bell_on:
        d.text((bell_x + bell_size / 2, by + bh + 22), "ALL NOTIFICATIONS", font=font(24, 800), fill=(255, 214, 70, 255), anchor="mm")
    if kind == "share":
        a_s = _ease(p / 0.12)
        sw = 330
        sh = _pill("SHARE", sw, bh, (255, 255, 255, 255) if p < click_share else (255, 214, 70, 255),
                   fg=(20, 20, 24, 255), icon="share")
        sc = (0.6 + 0.4 * a_s) * (0.94 if click_share <= p < click_share + 0.035 else 1.0)
        sh = sh.resize((int(sw * sc), int(bh * sc)), Image.LANCZOS)
        sh.putalpha(sh.getchannel("A").point(lambda v: int(v * a_s)))
        layer.alpha_composite(sh, (share_x + (sw - sh.width) // 2, by + (bh - sh.height) // 2))
    # the cursor glides to each target and clicks
    if kind == "subscribe":
        path = [(0.08, (W - 220, H - 60)), (click_sub, (bx + bw * 0.55, by + bh * 0.55)),
                (click_sub + 0.12, (bx + bw * 0.55, by + bh * 0.55)), (click_bell, (bell_x + 52, by + 58)),
                (1.0, (bell_x + 70, by + 90))]
    else:
        path = [(0.0, (bell_x + 70, by + 90)), (click_share, (share_x + sw * 0.5, by + bh * 0.55)),
                (1.0, (share_x + sw * 0.6, by + bh * 0.7))]
    if p >= path[0][0]:
        for (p0, a0), (p1, a1) in zip(path, path[1:]):
            if p <= p1:
                e = _ease((p - p0) / max(1e-6, p1 - p0))
                cx, cy = a0[0] + (a1[0] - a0[0]) * e, a0[1] + (a1[1] - a0[1]) * e
                break
        else:
            cx, cy = path[-1][1]
        clicking = any(c <= p < c + 0.035 for c in ((click_sub, click_bell) if kind == "subscribe" else (click_share,)))
        layer.alpha_composite(_cursor(0.9 if clicking else 1.0), (int(cx), int(cy)))
    return layer


def section_sounds(segments):
    import sfx

    def events(starts, total):
        ev = []
        for st, seg in zip(starts, segments):
            if seg.get("chapter"):
                ev.append((max(0.0, st - 0.1), sfx.sonar(0.32)))
            if seg.get("sfx") == "boom" or any(s.startswith("scale:") for s in seg["shots"][:1]):
                ev.append((st + 0.15, sfx.deep_boom(0.7)))
        return ev
    return events


def chapters_text(segments, starts):
    rows = []
    for seg, st in zip(segments, starts):
        if seg.get("chapter"):
            s = 0 if not rows else int(st)
            rows.append(f"{s // 60}:{s % 60:02d} {seg['chapter']}")
    return "\n".join(rows)


def preview(segments, vid, scales, path, cols=8):
    """One tile per shot, rendered with overlays, for QA before the full render."""
    fake_starts = [i * 6.0 for i in range(len(segments) + 1)]
    fr = frame_fn(segments, vid, scales)
    tiles = []
    for i, seg in enumerate(segments):
        n = len(seg["shots"])
        for k in range(n):
            t_in = (k + 0.5) * 6.0 / n
            tiles.append(Image.fromarray(fr(fake_starts[i] + t_in, i, t_in, fake_starts)).resize((320, 180)))
    sheet = Image.new("RGB", (320 * cols, 180 * ((len(tiles) + cols - 1) // cols)), (0, 0, 0))
    for n, im in enumerate(tiles):
        sheet.paste(im, (320 * (n % cols), 180 * (n // cols)))
    sheet.save(path, quality=82)
    return len(tiles)
