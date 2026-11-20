"""
run_critic_short.py — "A Food Critic Tries What Animals Eat" (2026-11-05). Costs nothing: Blender/Cycles on this
machine, the local Kokoro voice, our own synthesized music and sound effects. No AI images, video or paid voice.

Owner, 2026-11-05: animation that looks good (not realistic, not a kids' cartoon), humour so people in
entertainment mode connect, information delivered with jokes rather than a lesson, monetization first.
Format check (topic_validate, Shorts, last 12 months): "How different water animals eat 😂" 60.8M,
"Ranking animals eating lemons 😂" 13.3M; pandas eating bamboo 12 h a day 18.1M; dung beetles steering by the
Milky Way 12.2M (Zack D. Films). Our own format and writing: a deadpan fine-dining critic, a silver cloche
lifting on each "course", a star rating after each.

FACTS (checked 2026-11-05, 2+ sources each):
  - koala: eucalyptus is toxic to most animals and low in energy; koalas sleep ~18-22 h a day (Guinness
    "sleepiest marsupial"; Friends of the Koala; Australian wildlife parks) -> "about eighteen hours"
  - giant panda: up to ~14 h a day eating bamboo, digests ~17% (Xue et al. 2015, mBio; NZ Herald; The Week)
    -> "less than a fifth"
  - vampire bats regurgitate blood to feed hungry roostmates (Wilkinson 1984, Nature; Carter & Wilkinson
    2015, Proc. R. Soc. B; phys.org)
  - blue whale: ~16 tonnes of krill a day in the feeding season (Savoca et al. 2021, Nature; Smithsonian Ocean;
    Reuters) -> "up to sixteen tonnes"
  - some (African ball-rolling) dung beetles hold a straight line by the Milky Way (Dacke et al. 2013,
    Current Biology; phys.org; Audubon)

Steps (each re-runnable):
  python run_critic_short.py voice          # Kokoro voice -> timing.json
  python run_critic_short.py still N [..]   # Blender: single look-test frames
  python run_critic_short.py frames A B     # Blender: render frames A..B (Cycles)
  python run_critic_short.py compose        # overlays + voice + sfx + music -> mp4 (never uploads)
"""
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import config

import motion_shorts as ms
import sfx

VIDEO_ID = "critic_animal_menu"
W, H = 1080, 1920
HERE = os.path.dirname(os.path.abspath(__file__))
FONT_T = os.path.join(HERE, "fonts", "BebasNeue-Regular.ttf")
GOLD, CREAM, WHITE, DARK = (240, 196, 92), (250, 240, 222), (255, 255, 255), (16, 12, 10)
WORK = os.path.join(HERE, "output", "blender", VIDEO_ID)
BLENDER_PY = "/root/.venvs/blender/bin/python"
FPS = 24
VOICE, SPEED = "bf_emma", 1.05          # posh, deadpan British critic (local Kokoro voice: free)
BEAT, CUT = 0.5, 0.3                    # pause before each rating (the joke lands), and before the next course

# course: which dish is on the table (one continuous shot per course); stars: rating shown on this line.
# SEGMENTS_ALL is the full script the Blender timeline was built from; SEGMENTS is what ships.
SEGMENTS_ALL = [
    {"line": "I'm a food critic. Tonight, I eat like animals.", "course": "hook", "gap": 0.2},
    {"line": "Dessert is a ball of poo.", "course": "hook", "gap": 0.45},
    {"line": "Starter: eucalyptus. Toxic to most animals, so koalas sleep about eighteen hours a day to digest it.",
     "course": "koala", "gap": BEAT},
    {"line": "Relatable. Two stars.", "course": "koala", "stars": 2, "gap": CUT},
    {"line": "Main course: bamboo. Pandas eat it up to fourteen hours a day, and digest less than a fifth.",
     "course": "panda", "gap": BEAT},
    {"line": "All that chewing. One star.", "course": "panda", "stars": 1, "gap": CUT},
    {"line": "The wine: blood. Vampire bats throw it up to feed hungry friends.", "course": "bat", "gap": BEAT},
    {"line": "Disgusting. Also adorable. Four stars.", "course": "bat", "stars": 4, "gap": CUT},
    {"line": "For the blue whale: up to sixteen tonnes of krill. In one day.", "course": "whale", "gap": BEAT},
    {"line": "Portion size: yes. Three stars.", "course": "whale", "stars": 3, "gap": CUT},
    {"line": "And dessert. Some dung beetles roll their poo home in a straight line, steering by the Milky Way.",
     "course": "dessert", "gap": BEAT},
    {"line": "Taste: zero stars. Navigation: five.", "course": "dessert", "stars": "nav", "gap": 0.35},
    {"line": "Which course would you send back?", "course": "cta", "gap": 0.2},
]
# Owner, Nov 5: "learn from others". The format's winners run 22-38 s (Zack D. Films median 33 s, Nick Wilkins
# 27 s, Pawesome Ranks 24 s); the full menu ran 45 s. The two courses with the weakest proven demand (koala
# 9K, vampire bat 18K top Shorts) are cut: ~29 s. Their frames are never rendered.
KEEP = ("hook", "panda", "whale", "dessert", "cta")
SEGMENTS = [s for s in SEGMENTS_ALL if s["course"] in KEEP]
COURSE_CARD = {"koala": ("STARTER", "FOR THE KOALA"), "panda": ("MAIN COURSE", "FOR THE PANDA"),
               "bat": ("THE WINE", "FOR THE VAMPIRE BAT"), "whale": ("SHARING PLATTER", "FOR THE BLUE WHALE"),
               "dessert": ("DESSERT", "FOR THE DUNG BEETLE")}

SCRIPT = {
    "format": "short",
    "hook": SEGMENTS[0]["line"] + " " + SEGMENTS[1]["line"],
    "body": " ".join(s["line"] for s in SEGMENTS[2:-1]),
    "cta": SEGMENTS[-1]["line"],
    "title": "A Food Critic Rates What Animals Eat 🤢 #shorts",
    "category_id": "23",          # Comedy
    "tags": ["food critic", "what animals eat", "funny animal facts", "animal facts", "panda", "bamboo",
             "blue whale", "krill", "dung beetle", "milky way", "3d animation", "comedy", "shorts"],
    "seo_description": (
        "A very serious food critic rates what animals actually eat. Pandas eat bamboo up to 14 hours a day and "
        "digest less than a fifth of it, a blue whale can eat about 16 tonnes of krill in a single day, and some "
        "dung beetles roll their ball home in a straight line by following the Milky Way.\n\n"
        "Animated in 3D by FramedFacts. Sources: Xue et al. (2015) mBio; Savoca et al. (2021) Nature; "
        "Dacke et al. (2013) Current Biology.\n\n"
        "#animals #funny #shorts"),
    "ai_generated_visuals": False,
    "topic_category": "Animals",
}


def step_voice():
    os.makedirs(WORK, exist_ok=True)
    vo, starts, total = ms.build_voice(SEGMENTS_ALL, VIDEO_ID + "_full", voice=VOICE, speed=SPEED)
    with open(os.path.join(WORK, "timing.json"), "w") as f:
        json.dump({"starts": starts, "total": total,
                   "segments": [{k: s.get(k) for k in ("course", "stars")} for s in SEGMENTS_ALL]}, f)
    print("timing", [round(s, 2) for s in starts], round(total, 2), "->", int(round((total + 0.6) * FPS)) + 1, "frames")


def _blender(*args):
    cmd = [BLENDER_PY, os.path.join(HERE, "blender_critic_scene.py"), os.path.join(WORK, "timing.json"),
           os.path.join(WORK, "frames"), *map(str, args)]
    subprocess.run(cmd, check=True)


# ── overlays (drawn on the rendered frames) ──────────────────────────────────
_cache = {"idx": None, "img": None}


def _frame_img(idx):
    if _cache["idx"] != idx:
        p = os.path.join(WORK, "frames", f"f_{idx:04d}.png")
        _cache["img"] = Image.open(p).convert("RGBA").resize((W, H), Image.LANCZOS)
        _cache["idx"] = idx
    return _cache["img"]


def _font(size):
    return ImageFont.truetype(FONT_T, size)


def _star(d, cx, cy, r, filled, color=GOLD):
    import math
    pts = []
    for k in range(10):
        rr = r if k % 2 == 0 else r * 0.45
        a = -math.pi / 2 + k * math.pi / 5
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=color if filled else None, outline=(0, 0, 0))
    if not filled:
        d.line(pts + [pts[0]], fill=color, width=5)


def _stars_row(d, y, n, shown, label=None, scale=1.0):
    r, gap = 46 * scale, 108 * scale
    x0 = W / 2 - 2 * gap
    if label:
        d.text((W / 2, y - 78 * scale), label, font=_font(int(64 * scale)), fill=CREAM, anchor="mm",
               stroke_width=5, stroke_fill=DARK)
    for k in range(5):
        if k < shown:
            _star(d, x0 + k * gap, y, r * (1.0 + 0.25 * max(0.0, 1 - (shown - k))), k < n)


def _course_starts(segs, starts):
    out = {}
    for k, sg in enumerate(segs):
        out.setdefault(sg["course"], starts[k])
    return out


def to_render_time(t, course, starts):
    """Map a time in the shipped (cut) video to the same moment in the full render's timeline: every kept course
    keeps its exact length, so only the course's start moves."""
    timing = _cache.setdefault("timing", json.load(open(os.path.join(WORK, "timing.json"))))
    orig = _course_starts(SEGMENTS_ALL, timing["starts"])
    new = _course_starts(SEGMENTS, starts)
    return orig[course] + (t - new[course])


def frame(t, i, t_in, starts):
    timing = _cache.setdefault("timing", json.load(open(os.path.join(WORK, "timing.json"))))
    if "checked" not in _cache:                          # every kept line must sit where it sat in the render
        for k, sg in enumerate(SEGMENTS):
            j = SEGMENTS_ALL.index(sg)
            if abs(to_render_time(starts[k], sg["course"], starts) - timing["starts"][j]) > 0.02:
                raise RuntimeError(f"line {k} moved relative to the Blender render -- re-run voice and frames")
        _cache["checked"] = True
    seg = SEGMENTS[i]
    order = [s["course"] for s in SEGMENTS_ALL]
    nxt = [timing["starts"][j] for j in range(len(SEGMENTS_ALL)) if order.index(order[j]) > order.index(seg["course"])]
    last = int(round((nxt[0] if nxt else timing["total"] + 0.6) * FPS)) - 1     # never step into a cut course
    img = _frame_img(min(int(to_render_time(t, seg["course"], starts) * FPS), last)).copy()
    d = ImageDraw.Draw(img)
    course = seg["course"]
    first = next(k for k, s in enumerate(SEGMENTS) if s["course"] == course)
    c_in = t - starts[first]                          # time since this course began
    pop = 0.85 + 0.15 * ms.ease(min(1.0, c_in / 0.25))
    if course == "hook":
        d.text((W / 2, 230), "ANIMAL TASTING MENU", font=_font(int(122 * pop)), fill=GOLD, anchor="mm",
               stroke_width=8, stroke_fill=DARK)
        d.text((W / 2, 330), "REVIEWED BY A VERY SERIOUS CRITIC", font=_font(50), fill=CREAM, anchor="mm",
               stroke_width=4, stroke_fill=DARK)
    elif course in COURSE_CARD:
        top, sub = COURSE_CARD[course]
        d.text((W / 2, 215), top, font=_font(int(128 * pop)), fill=GOLD, anchor="mm", stroke_width=8, stroke_fill=DARK)
        d.text((W / 2, 318), sub, font=_font(58), fill=CREAM, anchor="mm", stroke_width=5, stroke_fill=DARK)
    else:
        d.text((W / 2, 250), "WHICH WOULD YOU", font=_font(int(120 * pop)), fill=GOLD, anchor="mm",
               stroke_width=8, stroke_fill=DARK)
        d.text((W / 2, 370), "SEND BACK?", font=_font(int(150 * pop)), fill=WHITE, anchor="mm",
               stroke_width=8, stroke_fill=DARK)
    st = seg.get("stars")
    if st is not None:
        shown_t = max(0.0, t_in - 0.55)                # stars pop in one by one as the rating is spoken
        panel = Image.new("RGBA", (W, H), (0, 0, 0, 0))   # a dark rounded backing so the stars read on any dish
        box = (W / 2 - 300, 1255, W / 2 + 300, 1580) if st == "nav" else (W / 2 - 300, 1345, W / 2 + 300, 1495)
        ImageDraw.Draw(panel).rounded_rectangle(box, 44, fill=(10, 8, 8, 165))
        img.alpha_composite(panel)
        d = ImageDraw.Draw(img)
        if st == "nav":
            _stars_row(d, 1362, 0, min(5, int(shown_t / 0.07) + 1), "TASTE", 0.7)   # below the ball, not over it
            if t_in > 1.15:
                _stars_row(d, 1512, 5, min(5, int((t_in - 1.15) / 0.07) + 1), "NAVIGATION", 0.7)
        else:
            _stars_row(d, 1420, st, min(5, int(shown_t / 0.09) + 1))
    ms.caption(d, 1640, seg["line"], size=44)
    ms.watermark(d)
    return np.array(img.convert("RGB"))


def sound_events(starts, total):
    """Sound cues from the Blender timeline (cues.json), moved onto the shipped timeline; cues in cut courses drop."""
    timing = json.load(open(os.path.join(WORK, "timing.json")))
    orig = _course_starts(SEGMENTS_ALL, timing["starts"])
    new = _course_starts(SEGMENTS, starts)
    bounds = sorted(orig.items(), key=lambda kv: kv[1])

    def remap(tc):
        course = [c for c, st in bounds if st <= tc][-1] if tc >= bounds[0][1] else bounds[0][0]
        return new[course] + (tc - orig[course]) if course in new else None

    ev = [(0.0, sfx.tick(1.6, 0.4))]                                  # a fork on a glass: "ding"
    cues = json.load(open(os.path.join(WORK, "frames", "cues.json")))
    for c in map(remap, cues["cloche"]):
        if c is not None:
            ev += [(c, sfx.whoosh(0.35, 0.25)), (c + 0.05, sfx.tick(0.9, 0.3))]
    for c in map(remap, cues.get("clank", [])):
        if c is not None:
            ev.append((c, sfx.thump(0.5)))
    for k, s in enumerate(SEGMENTS):
        if s.get("stars") is not None:
            ev.append((starts[k] + 0.55, sfx.pop(0.35)))
    if cues.get("roll") and remap(cues["roll"]) is not None:
        ev.append((remap(cues["roll"]), sfx.riser(1.2, 0.25)))
    return ev


def step_compose():
    out, vo = ms.render_short(SCRIPT, SEGMENTS, VIDEO_ID, frame, voice=VOICE, speed=SPEED, music_style="lounge",
                              sfx_fn=sound_events, music_vol=0.12, hook_hit=False)
    tmp = out.replace(".mp4", "_norm.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", out, "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5:LRA=9",
                    "-ar", "48000", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", tmp], check=True)
    os.replace(tmp, out)
    return out


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "voice":
        step_voice()
    elif cmd == "still":
        _blender("still", *sys.argv[2:])
    elif cmd == "frames":
        _blender(sys.argv[2], sys.argv[3])
    elif cmd == "compose":
        print(step_compose())
    else:
        print(__doc__)
