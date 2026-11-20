"""
channel_branding.py — FramedFacts channel identity.

2026-11-03: the channel is now animal psychology (GROWTH_PLAN.md). YouTube still
labelled it "Sport / Association football", and the page said "facts in 3D", so
render_pets_banner()/render_pets_avatar() draw the cartoon cat and dog from
thumb_kit.py, and apply() also sets the channel trailer. Later the same day the niche
research (notes/2026-11-03_niche_research.md) moved the main niche to extreme animals
shown to scale, so the live banner is render_scale_banner() (dark ocean + depth ruler). The older 3D banner
functions are kept below for reference.

Owner, 2026-10-24: FramedFacts was never only about football -- it is a
facts channel shown in 3D, any topic. This renders the banner and profile
picture in code (no AI credits needed) and applies the banner, description
and keywords through the YouTube Data API.

  python channel_branding.py render   # writes output/branding/banner.png, avatar.png
  python channel_branding.py apply    # backs up current branding, uploads banner,
                                      # updates description + keywords

The YouTube API cannot change the profile picture -- upload avatar.png in
YouTube Studio (Customization > Branding > Picture).

Banner: 2560x1440. YouTube shows only the centre band on desktop
(2560x423, y 508-931) and on phones (1546x423, x 507-2053), so the title and
tagline stay inside that phone-safe box; the 3D wireframes sit at the sides
(desktop/TV only).
"""
import os
import sys
import json
import math
import datetime

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output", "branding")
FONT_TITLE = os.path.join(HERE, "fonts", "BebasNeue-Regular.ttf")
FONT_BODY = os.path.join(HERE, "fonts", "Montserrat[wght].ttf")

CYAN = (56, 217, 255)
WHITE = (240, 244, 255)

DESCRIPTION = (
    "FramedFacts: animal facts you can SEE.\n\n"
    "The deadliest predators, the strangest deep-sea monsters, prehistoric giants, and the pets on your sofa: "
    "explained, and shown to scale next to a human so you get it in seconds. "
    "Every claim is checked against real research, with sources in each description.\n\n"
    "🦈 Deep sea · 🐊 Predators · 🦖 Prehistoric giants · 🐶 Animal minds\n\n"
    "New long videos every week, with short clips in between. Got an animal you want explained? "
    "Ask in the comments and it may become the next video.")

KEYWORDS = ('"animal facts" "deep sea creatures" "most dangerous animals" "prehistoric animals" "animals to scale" '
            '"size comparison" "predators" "animal behavior explained" "animal psychology" "ocean animals"')

# The channel trailer non-subscribers see on the channel page (set by apply()).
TRAILER_VIDEO = "G6bFaS7npX4"


def _body_font(size, weight=800):
    f = ImageFont.truetype(FONT_BODY, size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


def _background(w, h, glow_center, glow_radius):
    ys, xs = np.mgrid[0:h, 0:w]
    t = ys / h
    base = np.stack([6 + 16 * t, 10 + 0 * t, 26 + 22 * t], -1)
    gx, gy = glow_center
    d = np.sqrt((xs - gx) ** 2 + ((ys - gy) * 1.6) ** 2) / glow_radius
    glow = np.clip(1 - d, 0, 1) ** 2
    img = base + glow[..., None] * np.array([30, 70, 200])
    rng = np.random.default_rng(11)
    img = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(img)
    for _ in range(int(w * h / 9000)):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        r = rng.choice([1, 1, 1, 2, 2, 3])
        a = int(rng.uniform(60, 200))
        d.ellipse([x - r, y - r, x + r, y + r], fill=(200, 230, 255, a))
    return img


def _project(p, cx, cy, scale, dist=4.0):
    x, y, z = p
    f = scale / (dist - z)
    return cx + x * f, cy - y * f


def _rot(p, ax, ay):
    x, y, z = p
    x, z = x * math.cos(ay) + z * math.sin(ay), -x * math.sin(ay) + z * math.cos(ay)
    y, z = y * math.cos(ax) - z * math.sin(ax), y * math.sin(ax) + z * math.cos(ax)
    return x, y, z


def _globe(d, cx, cy, r, col=CYAN):
    scale = r * 3.0
    for lat in range(-60, 90, 30):
        pts = []
        for lon in range(0, 361, 6):
            la, lo = math.radians(lat), math.radians(lon)
            p = _rot((math.cos(la) * math.cos(lo), math.sin(la), math.cos(la) * math.sin(lo)), 0.45, 0.5)
            pts.append(_project(p, cx, cy, scale))
        d.line(pts, fill=col + (150,), width=3)
    for lon in range(0, 180, 20):
        pts = []
        for lat in range(-90, 91, 6):
            la, lo = math.radians(lat), math.radians(lon)
            p = _rot((math.cos(la) * math.cos(lo), math.sin(la), math.cos(la) * math.sin(lo)), 0.45, 0.5)
            pts.append(_project(p, cx, cy, scale))
        d.line(pts, fill=col + (170,), width=3)


def _cube(d, cx, cy, size, col=CYAN):
    v = [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    edges = [(a, b) for a in range(8) for b in range(a + 1, 8)
             if sum(1 for k in range(3) if v[a][k] != v[b][k]) == 1]
    pv = [_project(_rot(p, 0.55, 0.75), cx, cy, size * 2.6) for p in v]
    for a, b in edges:
        d.line([pv[a], pv[b]], fill=col + (190,), width=4)
    for p in pv:
        d.ellipse([p[0] - 7, p[1] - 7, p[0] + 7, p[1] + 7], fill=col + (230,))


def _extruded(img, xy, text, font, top=WHITE, depth=18, side=(18, 42, 110)):
    """Fake 3D extrusion: stacked offset layers under the front face."""
    d = ImageDraw.Draw(img)
    x, y = xy
    for i in range(depth, 0, -1):
        k = i / depth
        c = tuple(int(s * (0.55 + 0.45 * (1 - k))) for s in side) + (255,)
        d.text((x + i * 1.3, y + i * 1.3), text, font=font, fill=c)
    d.text((x, y), text, font=font, fill=top + (255,))


def render_banner(path):
    W, H = 2560, 1440
    img = _background(W, H, (1280, 720), 1100)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    _globe(d, 300, 720, 165)          # desktop/TV only
    _cube(d, 2265, 720, 120)          # desktop/TV only
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(0.6)))

    title_font = ImageFont.truetype(FONT_TITLE, 250)
    a, b = "FRAMED", "FACTS"
    wa = ImageDraw.Draw(img).textlength(a, font=title_font)
    wb = ImageDraw.Draw(img).textlength(b, font=title_font)
    gap = 26
    x0 = (W - (wa + gap + wb)) / 2
    y0 = 520
    _extruded(img, (x0, y0), a, title_font, top=WHITE)
    _extruded(img, (x0 + wa + gap, y0), b, title_font, top=CYAN, side=(8, 60, 90))

    d = ImageDraw.Draw(img)
    tag = "FACTS YOU CAN SEE  —  IN 3D"
    f2 = _body_font(62, 800)
    d.text(((W - d.textlength(tag, font=f2)) / 2, 790), tag, font=f2, fill=WHITE + (255,))
    topics = "SCIENCE  •  ANIMALS  •  HUMAN BODY  •  HOW IT WORKS  •  SPACE"
    f3 = _body_font(36, 600)
    d.text(((W - d.textlength(topics, font=f3)) / 2, 878), topics, font=f3, fill=CYAN + (220,))
    img.convert("RGB").save(path, quality=95)
    return path


def render_avatar(path):
    S = 800
    img = _background(S, S, (400, 400), 520)
    layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    _cube(d, 400, 400, 150, col=(40, 120, 200))
    img.alpha_composite(layer)
    f = ImageFont.truetype(FONT_TITLE, 470)
    dd = ImageDraw.Draw(img)
    w1 = dd.textlength("F", font=f)
    x0 = (S - (w1 * 2 + 10)) / 2
    _extruded(img, (x0, 150), "F", f, top=WHITE, depth=16)
    _extruded(img, (x0 + w1 + 10, 150), "F", f, top=CYAN, depth=16, side=(8, 60, 90))
    img.convert("RGB").save(path, quality=95)
    return path


def render_scale_banner(path):
    """2560x1440 'deep ocean + depth scale' banner (2026-11-03 niche: extreme animals shown to scale).
    The text and the depth ruler sit inside the phone-safe box (x 507-2053, y 508-931)."""
    import thumb_kit as tk
    BW, BH = 2560, 1440
    yy, xx = np.mgrid[0:BH, 0:BW].astype(np.float32)
    t = (yy / BH)[..., None]
    top, bot = np.array((20, 120, 150), np.float32), np.array((2, 8, 22), np.float32)
    arr = top * (1 - t) ** 1.4 + bot * (1 - (1 - t) ** 1.4)
    ray = np.zeros((BH, BW), np.float32)
    for x0, w, a in ((900, 120, 0.10), (1250, 200, 0.12), (1650, 140, 0.09), (2050, 90, 0.07), (600, 80, 0.06)):
        ray += a * np.clip(1 - np.abs(xx - (x0 + yy * 0.25)) / w, 0, 1) * np.clip(1 - yy / BH, 0, 1)
    arr = arr + 255 * ray[..., None] * 0.6
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    rng = np.random.default_rng(7)
    d = ImageDraw.Draw(img)
    for _ in range(260):                                   # drifting particles ("marine snow")
        x, y, r = rng.uniform(0, BW), rng.uniform(0, BH), rng.uniform(1.5, 4.5)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(200, 230, 255, int(rng.uniform(40, 140))))
    rx = 600                                               # depth ruler, left side of the safe box
    d.line([(rx, 530), (rx, 910)], fill=(150, 220, 255, 230), width=5)
    for k, lab in enumerate(("0 m", "1,000 m", "2,000 m", "3,000 m")):
        y = 540 + k * 120
        d.line([(rx - 22, y), (rx + 22, y)], fill=(150, 220, 255, 230), width=5)
        d.text((rx + 34, y), lab, font=tk.font(26, 700), fill=(170, 225, 255), anchor="lm")
    t = "FRAMEDFACTS"
    f1 = tk.font(132)
    w1 = d.textlength(t, font=f1)
    d.text(((BW - w1) / 2 + 60, 548), t, font=f1, fill=(255, 255, 255), stroke_width=9, stroke_fill=(0, 0, 0))
    t2 = "ANIMAL FACTS YOU CAN SEE"
    f2 = tk.font(58)
    d.text(((BW - d.textlength(t2, font=f2)) / 2 + 60, 728), t2, font=f2, fill=tk.YELLOW, stroke_width=6, stroke_fill=(0, 0, 0))
    t3 = "DEEP SEA  •  PREDATORS  •  PREHISTORIC GIANTS  •  SHOWN TO SCALE"
    f3 = tk.font(28, 700)
    d.text(((BW - d.textlength(t3, font=f3)) / 2 + 60, 832), t3, font=f3, fill=(255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0))
    img.convert("RGB").save(path, quality=95)
    return path


def render_pets_banner(path):
    """2560x1440 banner; the cat, dog and all text sit inside the phone-safe box (x 507-2053, y 508-931)."""
    import thumb_kit as tk
    BW, BH = 2560, 1440
    img = tk.burst((70, 190, 255), (10, 30, 120), cx=0.5, cy=0.5, rays=28).resize((BW, BH), Image.LANCZOS)
    heads = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    lay, d = tk.layer()
    tk.cat_head(d, 420, 600, 210, "happy", body=False)
    tk.stick(heads, lay, outline=12, shadow=(8, 10))
    lay, d = tk.layer()
    tk.dog_head(d, 1500, 600, 210, body=False)
    tk.stick(heads, lay, outline=12, shadow=(8, 10))
    for (x0, x1), cx in (((150, 700), 662), ((1220, 1780), 1876)):
        part = heads.crop((x0, 300, x1, 860))
        part = part.crop(part.getbbox())
        sc = 270 / part.height
        part = part.resize((int(part.width * sc), 270), Image.LANCZOS)
        img.alpha_composite(part, (int(cx - part.width / 2), 720 - 135))
    d = ImageDraw.Draw(img)
    t = "FRAMEDFACTS"
    f1 = tk.font(104)
    w1 = d.textlength(t, font=f1)
    d.text(((BW - w1) / 2 + 5, 575 + 7), t, font=f1, fill=(0, 0, 0, 120))
    d.text(((BW - w1) / 2, 575), t, font=f1, fill=(255, 255, 255), stroke_width=8, stroke_fill=(0, 0, 0))
    t2 = "WHY ANIMALS DO WHAT THEY DO"
    f2 = tk.font(44)
    d.text(((BW - d.textlength(t2, font=f2)) / 2, 718), t2, font=f2, fill=tk.YELLOW, stroke_width=6, stroke_fill=(0, 0, 0))
    t3 = "ANIMAL FACTS SHOWN TO SCALE  •  NEW VIDEOS EVERY WEEK"
    f3 = tk.font(27, 700)
    d.text(((BW - d.textlength(t3, font=f3)) / 2, 800), t3, font=f3, fill=(255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0))
    img.convert("RGB").save(path, quality=95)
    return path


def render_pets_avatar(path):
    """800x800 profile picture: the judging cat face (the channel's mascot). Upload it in YouTube Studio."""
    import thumb_kit as tk
    c = tk.burst((255, 210, 80), (230, 90, 20), cx=0.5, cy=0.5)
    lay, d = tk.layer()
    tk.cat_head(d, 960, 600, 330, "judge", look=(0, 0), body=False)
    tk.stick(c, lay, outline=14, shadow=(8, 10))
    img = c.crop((960 - 470, 600 - 470, 960 + 470, 600 + 470)).resize((800, 800), Image.LANCZOS)
    img.convert("RGB").save(path, quality=95)
    return path


def apply(banner_path):
    import phase5_upload as p5
    from googleapiclient.http import MediaFileUpload
    yt = p5.get_youtube_client()
    ch = yt.channels().list(part="brandingSettings", mine=True).execute()["items"][0]
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    with open(os.path.join(OUT, f"channel_backup_{ts}.json"), "w", encoding="utf-8") as f:
        json.dump(ch, f, indent=1, ensure_ascii=False)

    banner = yt.channelBanners().insert(
        media_body=MediaFileUpload(banner_path, mimetype="image/png")).execute()
    bs = ch["brandingSettings"]
    bs.setdefault("channel", {})
    bs["channel"]["description"] = DESCRIPTION
    bs["channel"]["keywords"] = KEYWORDS
    bs["channel"]["unsubscribedTrailer"] = TRAILER_VIDEO
    bs.setdefault("image", {})["bannerExternalUrl"] = banner["url"]
    res = yt.channels().update(part="brandingSettings",
                               body={"id": ch["id"], "brandingSettings": bs}).execute()
    return res["brandingSettings"]


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    banner = render_scale_banner(os.path.join(OUT, "banner.png"))
    avatar = render_pets_avatar(os.path.join(OUT, "avatar.png"))
    print("rendered:", banner, avatar)
    if len(sys.argv) > 1 and sys.argv[1] == "apply":
        print(json.dumps(apply(banner), indent=1, ensure_ascii=False)[:1500])
