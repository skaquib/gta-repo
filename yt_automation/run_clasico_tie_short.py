"""
run_clasico_tie_short.py — "El Clásico is DEAD LEVEL after 264 games"
(researched 2026-10-23, for the Oct 25 Clásico).

RESEARCH (trend_now.py, output/research/trend_now_20261023T1521Z.json):
  - Last 48h football Shorts: Champions League matchday 3 dominates (top
    riser 152K views/h); El Clásico build-up rising ("Se viene el Clásico"
    883K in 17h; "Flick's Barça head into El Clásico in a very dark state of
    mind" 648K); Yamal is the most frequent name in the top 60 risers.
  - "Who will win?" debate Shorts break out from small channels (708K in 32h
    from a 21K-sub channel) -> binary comment prompt at the end.
  - The channel's audiences (IN, ID, BR) follow Barça/Madrid more than any
    other football rivalry.

FACTS (verified 2026-10-23):
  - All-time official Clásicos: 264 played, 106 wins each, 52 draws, last
    meeting Barcelona 2-0 on 10 May 2026 (Wikipedia "El Clásico", Yahoo
    Sports, fcbarcelona.com/en/el-clasico, NamuWiki agree; Sports Mole is
    the lone outlier at 107-106).
  - Clásico #265: Sunday 25 Oct 2026, 21:00 CEST, Spotify Camp Nou
    (realmadrid.com, fcbarcelona.com).
  - PSG 4-2 Barcelona, 20 Oct 2026 -- Barça's first defeat of the season
    (Khaleej Times/AFP, The National, La Nación/AP).
  - Real Madrid 4-1 RB Leipzig, 21 Oct 2026 (Real Madrid's official channel
    highlights).

HOOK (engineered, see GROWTH_PLAN.md retention evidence):
  - Voice on frame 1 (no lead silence, no title card).
  - 0.0-1.5s: scoreboard counts 0 -> 106 on both sides with ticking, locks
    at 106-106 with an impact, flash and shake.
  - 7-word spoken hook with stakes; payoff ("someone breaks it on Sunday")
    within 6s; debate prompt at the end.
  - Club names/colours only: no crests or logos.
"""
import math
import numpy as np
from PIL import Image, ImageDraw

import config

config.assert_safe_pipeline()

import motion_shorts as ms
import sfx

VIDEO_ID = "clasico_tie_short"
W, H = ms.W, ms.H

SEGMENTS = [
    {"line": "264 Clásicos. 106 wins each.", "say": "264 Klah-see-kohs. 106 wins each."},
    {"line": "Dead level. Plus 52 draws."},
    {"line": "On Sunday, Clásico 265 breaks the tie.", "say": "On Sunday, Klah-see-ko 265 breaks the tie."},
    {"line": "Barça just lost 4-2 to PSG. Their first defeat this season."},
    {"line": "Madrid just beat Leipzig 4-1."},
    {"line": "Who takes the lead? Comment Madrid or Barça."},
]

SCRIPT = {
    "hook": SEGMENTS[0]["line"],
    "body": " ".join(s["line"] for s in SEGMENTS[1:-1]),
    "cta": SEGMENTS[-1]["line"],
    "title": "El Clásico Is DEAD LEVEL After 264 Games 😳 #shorts",
    "tags": ["el clasico", "real madrid", "barcelona", "barca", "laliga", "clasico",
             "real madrid vs barcelona", "head to head", "yamal", "mbappe", "football", "shorts"],
    "seo_description": (
        "264 official Clásicos: Real Madrid 106 wins, Barcelona 106 wins, 52 draws. "
        "Clásico #265 on Sunday 25 October at the Spotify Camp Nou breaks the tie. "
        "Barça come in after their first defeat of the season (PSG 4-2), Madrid after a 4-1 win "
        "over Leipzig. Who takes the lead? #elclasico #realmadrid #barcelona #shorts"
    ),
}

LOCK_T = 1.5          # scoreboard locks at 106-106 (seconds into segment 0)
SPLIT_TOP, SPLIT_BOTTOM = 600, 480   # diagonal split x at top / bottom
GOLD = (245, 196, 66)
MADRID_TXT = (24, 38, 74)
BARCA_BLUE, BARCA_RED = (0, 77, 152), (165, 0, 68)


def _split_x(y):
    return SPLIT_TOP + (SPLIT_BOTTOM - SPLIT_TOP) * y / H


def _background():
    img = Image.new("RGB", (W, H))
    px = np.zeros((H, W, 3), dtype=np.uint8)
    ys = np.arange(H)[:, None]
    xs = np.arange(W)[None, :]
    left = xs < (SPLIT_TOP + (SPLIT_BOTTOM - SPLIT_TOP) * ys / H)
    # Madrid: white-to-silver with faint gold diagonal pinstripes
    shade = (238 - 40 * ys / H).astype(np.int32)
    stripe = ((xs + ys) // 46) % 2 == 0
    mad = np.stack([shade, shade, shade + 4], -1).repeat(W, 1)
    mad = np.where(stripe[..., None], mad, mad - np.array([6, 10, 22]))
    # Barça: vertical blaugrana stripes, darker toward the bottom
    band = (xs // 90) % 2 == 0
    dark = (1 - 0.35 * ys / H)[..., None]
    bar = np.where(band[..., None], np.array(BARCA_BLUE), np.array(BARCA_RED)) * dark
    px[:] = np.where(left[..., None], np.clip(mad, 0, 255), np.clip(bar, 0, 255)).astype(np.uint8)
    img = Image.fromarray(px)
    d = ImageDraw.Draw(img)
    d.line([(SPLIT_TOP, 0), (SPLIT_BOTTOM, H)], fill=GOLD, width=10)
    # top and bottom vignettes so text and the YouTube UI stay readable
    shade_top = Image.new("L", (1, 380))
    for y in range(380):
        shade_top.putpixel((0, y), int(200 * (1 - y / 380)))
    img.paste((0, 0, 0), (0, 0, W, 380), shade_top.resize((W, 380)))
    shade_bot = Image.new("L", (1, 560))
    for y in range(560):
        shade_bot.putpixel((0, y), int(225 * (y / 560)))
    img.paste((0, 0, 0), (0, H - 560, W, H), shade_bot.resize((W, 560)))
    return img


_BG = _background()
_PARTICLES = np.random.default_rng(3).uniform(0, 1, size=(70, 3))


def _text(d, xy_center, text, size, fill, stroke=(0, 0, 0), anchor="mm"):
    f = ms.font(size)
    d.text(xy_center, text, font=f, fill=fill, anchor=anchor,
           stroke_width=max(3, size // 14), stroke_fill=stroke)


def _pill(d, cx, cy, text, size, fill, txt=(255, 255, 255)):
    f = ms.font(size)
    w = d.textlength(text, font=f) + size * 1.1
    h = size * 1.6
    d.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], radius=h / 2, fill=fill,
                        outline=(0, 0, 0, 255), width=4)
    d.text((cx, cy), text, font=f, fill=txt, anchor="mm")


def frame(t, i, t_in, starts):
    img = _BG.copy().convert("RGBA")
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    # drifting light particles (constant low-level motion)
    for k, (px, py, sp) in enumerate(_PARTICLES):
        y = (py * H - t * (40 + 90 * sp)) % H
        x = px * W + 14 * math.sin(t * 1.5 + k)
        r = 2 + 3 * sp
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, 60 + int(80 * sp)))

    # context strip (top)
    _text(d, (W / 2, 250), "EL CLÁSICO · ALL-TIME", 46, GOLD)
    _text(d, (W / 2, 322), "264 OFFICIAL MATCHES", 40, (255, 255, 255))

    # scoreboard
    t_abs = t
    counting = i == 0 and t_in < LOCK_T
    n = int(round(106 * ms.ease(t_in / LOCK_T))) if counting else 106
    jitter = (6 * math.sin(t_abs * 90)) if counting else 0
    lx, rx, ny = 250, 840, 760 + jitter
    _text(d, (lx, 560), "REAL MADRID", 60, MADRID_TXT, stroke=(255, 255, 255))
    _text(d, (rx, 560), "BARÇA", 72, (255, 255, 255))
    pulse = 1.0
    if i == 0 and LOCK_T <= t_in < LOCK_T + 0.35:
        pulse = 1.0 + 0.18 * (1 - (t_in - LOCK_T) / 0.35)
    size = int(205 * pulse)
    _text(d, (lx, ny), str(n), size, MADRID_TXT, stroke=GOLD)
    _text(d, (rx, ny), str(n), size, (255, 255, 255), stroke=(10, 10, 30))

    # centre badge on the split line
    cx, cy = _split_x(ny), ny
    badge = "?" if i >= 2 else "VS"
    br = 62 + (7 * math.sin(t * 7) if i >= 2 else 0)
    d.ellipse([cx - br, cy - br, cx + br, cy + br], fill=(15, 15, 20, 255), outline=GOLD + (255,), width=8)
    _text(d, (cx, cy + 2), badge, 54 if badge == "VS" else 80, GOLD)

    # segment overlays
    def appear(seconds=0.25):
        return ms.ease(t_in / seconds)

    if i == 1:
        a = appear(0.2)
        stamp = Image.new("RGBA", (760, 200), (0, 0, 0, 0))
        sd = ImageDraw.Draw(stamp)
        sd.rounded_rectangle([8, 8, 752, 192], radius=26, outline=(230, 40, 40, 255), width=12,
                             fill=(255, 255, 255, 235))
        sd.text((380, 100), "DEAD LEVEL", font=ms.font(118), fill=(230, 40, 40, 255), anchor="mm")
        sc = 1.6 - 0.6 * a
        stamp = stamp.resize((int(760 * sc), int(200 * sc))).rotate(-7, expand=True, resample=Image.BICUBIC)
        layer.alpha_composite(stamp, (int(W / 2 - stamp.width / 2), int(1010 - stamp.height / 2)))
        if t_in > 0.6:
            _pill(d, W / 2, 1210, "+ 52 DRAWS", 54, (20, 20, 28, 240))
    elif i == 2:
        a = appear(0.3)
        y = 1100 + (1 - a) * 300
        d.rounded_rectangle([110, y - 150, W - 110, y + 150], radius=34, fill=(12, 12, 18, 235),
                            outline=GOLD + (255,), width=6)
        _text(d, (W / 2, y - 62), "CLÁSICO #265", 92, GOLD)
        _text(d, (W / 2, y + 30), "SUN 25 OCT · 21:00 CEST", 50, (255, 255, 255))
        _text(d, (W / 2, y + 96), "SPOTIFY CAMP NOU", 40, (200, 200, 210))
    elif i in (3, 4):
        # form cards: Barça (right) from seg 3, Madrid (left) from seg 4
        if i >= 3:
            a = appear(0.25) if i == 3 else 1.0
            x = 805 + (1 - a) * 400
            d.rounded_rectangle([x - 250, 980, x + 250, 1240], radius=30, fill=(18, 10, 14, 235),
                                outline=(230, 50, 50, 255), width=6)
            _text(d, (x, 1045), "LOST 2-4", 76, (255, 80, 80))
            _text(d, (x, 1125), "vs PSG", 50, (255, 255, 255))
            _text(d, (x, 1192), "1st DEFEAT", 40, (255, 200, 200))
        if i == 4:
            a = appear(0.25)
            x = 285 - (1 - a) * 400
            d.rounded_rectangle([x - 250, 980, x + 250, 1240], radius=30, fill=(10, 18, 12, 235),
                                outline=(60, 200, 90, 255), width=6)
            _text(d, (x, 1045), "WON 4-1", 76, (90, 230, 120))
            _text(d, (x, 1125), "vs LEIPZIG", 50, (255, 255, 255))
            _text(d, (x, 1192), "UCL", 40, (200, 255, 210))
    elif i == 5:
        a = appear(0.25)
        _text(d, (W / 2, 1030), "WHO TAKES THE LEAD?", int(78 * (0.8 + 0.2 * a)), GOLD)
        bob = 10 * math.sin(t * 6)
        _pill(d, 285, 1185 + bob, "MADRID", 58, (245, 245, 245, 255), txt=MADRID_TXT)
        _pill(d, 805, 1185 - bob, "BARÇA", 58, BARCA_RED + (255,))
        _text(d, (W / 2, 1300), "comment below ↓", 40, (255, 255, 255))

    # sound-off caption (kept left of the Shorts action rail)
    ms.caption(d, 1445, SEGMENTS[i]["line"], size=48)
    ms.watermark(d)

    img.alpha_composite(layer)

    # lock flash + shake
    if i == 0 and LOCK_T <= t_in < LOCK_T + 0.3:
        k = 1 - (t_in - LOCK_T) / 0.3
        flash = Image.new("RGBA", (W, H), (255, 255, 255, int(150 * k)))
        img.alpha_composite(flash)
        dx, dy = int(14 * k * math.sin(t * 120)), int(10 * k * math.cos(t * 97))
        img = Image.fromarray(np.roll(np.array(img), (dy, dx), axis=(0, 1)))
    return np.array(img.convert("RGB"))


def sound_events(starts, total):
    ev = [(0.0, sfx.whoosh(0.35, 0.45))]
    # counter ticks up to the lock, slightly rising in pitch
    t, k = starts[0], 0
    while t < starts[0] + LOCK_T:
        ev.append((t, sfx.tick(1.0 + 0.012 * k, 0.32)))
        t += 0.06
        k += 1
    lock = starts[0] + LOCK_T
    ev += [(lock, sfx.impact(0.95)), (lock + 0.05, sfx.crowd(2.6, 0.30))]
    ev += [(starts[1] + 0.02, sfx.impact(0.75, low=False))]                 # DEAD LEVEL stamp
    ev += [(starts[1] + 0.62, sfx.pop(0.4))]                                # + 52 draws
    ev += [(max(0, starts[2] - 0.7), sfx.riser(0.7, 0.45)), (starts[2], sfx.impact(0.85))]
    ev += [(starts[3], sfx.whoosh(0.4, 0.5)), (starts[4], sfx.whoosh(0.4, 0.5))]
    ev += [(starts[5], sfx.impact(0.6, low=False)), (starts[5] + 0.3, sfx.crowd(2.2, 0.22))]
    return ev


if __name__ == "__main__":
    ms.render_short(SCRIPT, SEGMENTS, VIDEO_ID, frame, speed=1.15, sfx_fn=sound_events,
                    music_vol=0.08)
