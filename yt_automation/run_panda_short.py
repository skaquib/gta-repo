"""
run_panda_short.py — "Being a Panda Is a Scam 🐼" (owner approved: script A, the sample frame, voice 1; 2026-11-05).

A tired, grumpy panda complains to camera; every complaint is a true fact. Costs nothing: Blender/Cycles on this
machine, the local Kokoro voice, our own synthesized music and sound effects. No AI images, video or paid voice.
The planned series: "Animals Complain" (the end card asks which animal should complain next).

FACTS (checked 2026-11-05, 2+ sources each):
  - giant pandas feed 10-16 h a day (Smithsonian's National Zoo; WWF) -> "eleven hours", "fourteen hours a day"
  - a carnivore's digestive tract and gut microbes; digests ~17% of its bamboo (Xue et al. 2015, mBio;
    Live Science; CBS News) -> "less than a fifth"
  - bamboo is a grass (Poaceae)
  - defecates dozens of times a day (popular figure "~40" has no primary source, so: "dozens")
  - the "thumb" is an enlarged wrist bone, the radial sesamoid (Smithsonian; Endo et al. 1999, Nature)
  - newborns weigh ~100 g, about 1/900 of the mother (Smithsonian; National Geographic; Guinness) -> "the size of
    a stick of butter" (a US stick is 113 g)

Steps (each re-runnable):
  python run_panda_short.py voice          # Kokoro voice -> timing.json (+ per-frame mouth envelope)
  python run_panda_short.py still F [..]   # Blender: single look-test frames
  python run_panda_short.py frames A B     # Blender: render frames A..B (Cycles)
  python run_panda_short.py compose        # overlays + voice + sfx + music -> mp4 (never uploads)
  python run_panda_short.py publish        # owner said publish without asking: upload, go public, read back
"""
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

import motion_shorts as ms
import sfx

VIDEO_ID = "panda_scam"
W, H = 1080, 1920
HERE = os.path.dirname(os.path.abspath(__file__))
FONT_T = os.path.join(HERE, "fonts", "BebasNeue-Regular.ttf")
GOLD, CREAM, WHITE, DARK = (255, 208, 70), (250, 240, 222), (255, 255, 255), (12, 10, 10)
WORK = os.path.join(HERE, "output", "blender", VIDEO_ID)
BLENDER_PY = "/root/.venvs/blender/bin/python"
FPS = 24
VOICE, SPEED = "am_michael", 0.95       # owner picked voice 1; a touch slow: tired
END_CARD = 2.2                          # silent end card: "Who complains next? Sloth or koala?"

# shot: what the Blender timeline does during the line; callout: the fact, big, at the top of the frame
SEGMENTS = [
    {"line": "I've been eating for eleven hours. I'm still hungry.", "shot": "open", "callout": "11 HOURS OF EATING",
     "gap": 0.3},
    {"line": "My body was built for meat. I have a meat-eater's gut.", "shot": "belly", "callout": "A MEAT-EATER'S GUT",
     "gap": 0.25},
    {"line": "And I eat... grass. Yes, bamboo is grass.", "say": "And I eat... grass. Yes. Bamboo is grass.",
     "shot": "stalk", "callout": "BAMBOO IS A GRASS", "gap": 0.3},
    {"line": "So I digest less than a fifth of it.", "shot": "shrug", "callout": "DIGESTS LESS THAN 1/5", "gap": 0.3},
    {"line": "The rest comes out. Dozens of times a day.", "shot": "poo", "callout": "DOZENS OF TIMES A DAY",
     "gap": 0.3},
    {"line": "I don't even have a real thumb. It's a wrist bone, pretending.", "shot": "thumb",
     "callout": "IT'S A WRIST BONE", "gap": 0.3},
    {"line": "When I was born, I was the size of a stick of butter.", "shot": "baby", "callout": "ABOUT 100 GRAMS",
     "gap": 0.35},
    {"line": "Anyway. Back to work. Fourteen hours a day.", "shot": "sigh", "callout": "UP TO 14 HOURS A DAY",
     "gap": END_CARD},
]

SCRIPT = {
    "format": "short",
    "hook": SEGMENTS[0]["line"],
    "body": " ".join(s["line"] for s in SEGMENTS[1:]),
    "cta": "Sloth or koala: who should complain next?",   # a two-way pick is easier to answer than an open question
    "title": "Being a Panda Is a Scam 🐼 #shorts",
    "category_id": "23",          # Comedy
    "tags": ["panda", "giant panda", "funny panda", "panda facts", "bamboo", "funny animal facts", "animal facts",
             "3d animation", "comedy", "animals complain", "shorts"],
    "seo_description": (
        "Send this to the friend who is always hungry 🐼\n\n"
        "A very tired panda explains why its life is a scam. Giant pandas spend 10-16 hours a day eating bamboo, "
        "yet they have a meat-eater's digestive system and digest only about a fifth of it. Bamboo is a grass. "
        "Their 'thumb' is an enlarged wrist bone, and a newborn cub weighs about 100 grams, roughly 1/900 of its "
        "mother.\n\n"
        "Animated in 3D by FramedFacts. Sources: Smithsonian's National Zoo; Xue et al. (2015) mBio; "
        "Endo et al. (1999) Nature.\n\n"
        "#panda #funny #shorts"),
    "ai_generated_visuals": False,
    "topic_category": "Animals",
}


def step_voice():
    import soundfile as sf
    os.makedirs(WORK, exist_ok=True)
    vo, starts, total = ms.build_voice(SEGMENTS, VIDEO_ID, voice=VOICE, speed=SPEED)
    x, sr = sf.read(vo)
    if x.ndim > 1:
        x = x.mean(axis=1)
    n = int(round((total + 0.6) * FPS)) + 1
    hop = sr // FPS
    rms = np.array([np.sqrt(np.mean(x[k * hop:(k + 1) * hop] ** 2)) if k * hop < len(x) else 0.0 for k in range(n)])
    mouth = np.clip(rms / (np.percentile(rms[rms > 0.01], 90) if (rms > 0.01).any() else 1.0), 0, 1)
    ends = []                                   # when each line's speech ends (the end card starts after the last)
    for i, st in enumerate(starts):
        nxt = starts[i + 1] if i + 1 < len(starts) else total
        seg = x[int(st * sr):int(nxt * sr)]
        loud = np.nonzero(np.abs(seg) > 0.02)[0]
        ends.append(st + (loud[-1] / sr if len(loud) else 0.0))
    with open(os.path.join(WORK, "timing.json"), "w") as f:
        json.dump({"starts": starts, "ends": ends, "total": total, "fps": FPS, "frames": n,
                   "shots": [s["shot"] for s in SEGMENTS], "mouth": [round(float(v), 3) for v in mouth]}, f)
    print("timing", [round(s, 2) for s in starts], "ends", [round(e, 2) for e in ends], round(total, 2), "->", n,
          "frames")


def _blender(*args):
    cmd = [BLENDER_PY, os.path.join(HERE, "blender_panda_anim.py"), os.path.join(WORK, "frames"),
           os.path.join(WORK, "timing.json"), *map(str, args)]
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


def _flashback(img):
    """Warm, soft, vignetted: reads as a memory."""
    rgb = img.convert("RGB")
    warm = ImageEnhance.Color(rgb).enhance(0.55)
    r, g, b = warm.split()
    warm = Image.merge("RGB", (r.point(lambda v: min(255, int(v * 1.08 + 10))), g, b.point(lambda v: int(v * 0.86))))
    yy, xx = np.mgrid[0:H, 0:W]
    v = np.clip(1.25 - 1.1 * np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.6)) ** 2), 0.25, 1.0)
    arr = (np.asarray(warm).astype(np.float32) * v[..., None]).clip(0, 255).astype(np.uint8)
    edge = Image.fromarray(arr).filter(ImageFilter.GaussianBlur(6))
    mask = Image.fromarray(((1 - np.clip((v - 0.55) / 0.4, 0, 1)) * 255).astype(np.uint8))
    out = Image.composite(edge, Image.fromarray(arr), mask)
    return out.convert("RGBA")


def frame(t, i, t_in, starts):
    timing = _cache.setdefault("timing", json.load(open(os.path.join(WORK, "timing.json"))))
    if "checked" not in _cache:            # the voice must sit exactly where the Blender animation was keyed to it
        drift = max(abs(a - b) for a, b in zip(starts, timing["starts"]))
        if drift > 0.02:
            raise RuntimeError(f"voice moved {drift:.3f}s from the render -- re-run voice and frames")
        _cache["checked"] = True
    seg = SEGMENTS[i]
    img = _frame_img(min(int(t * FPS), timing["frames"] - 1)).copy()
    if seg["shot"] == "baby":
        img = _flashback(img)
    d = ImageDraw.Draw(img)
    end_card = i == len(SEGMENTS) - 1 and t > timing["ends"][-1] + 0.15
    if end_card:
        _end_card(d, t - timing["ends"][-1] - 0.15)
    else:
        pop = 0.85 + 0.15 * ms.ease(min(1.0, t_in / 0.22))
        text = seg["callout"]
        d.text((W / 2, 290), text, font=_font(int((132 if len(text) <= 16 else 112) * pop)), fill=GOLD, anchor="mm",
               stroke_width=8, stroke_fill=DARK)
        if seg["shot"] == "baby":
            d.text((W / 2, 400), "FLASHBACK", font=_font(54), fill=CREAM, anchor="mm", stroke_width=4,
                   stroke_fill=DARK)
        # above YouTube's own title/channel text (roughly y > 1550 on a phone); the droppings sit at 1340-1530
        ms.caption(d, 1130 if seg["shot"] == "poo" else 1380, seg["line"], size=62)
    ms.watermark(d)
    return np.array(img.convert("RGB"))


def _end_card(d, c_in):
    """A two-way pick (one word to type) gets more comments than an open question; the comment line lands a beat
    later, low, near the comment button but above YouTube's own text."""
    pop = 0.85 + 0.15 * ms.ease(min(1.0, c_in / 0.25))
    d.text((W / 2, 285), "WHO COMPLAINS NEXT?", font=_font(int(104 * pop)), fill=GOLD, anchor="mm",
           stroke_width=8, stroke_fill=DARK)
    d.text((W / 2, 410), "SLOTH OR KOALA?", font=_font(int(164 * pop)), fill=WHITE, anchor="mm",
           stroke_width=9, stroke_fill=DARK)
    if c_in > 0.45:
        p2 = 0.85 + 0.15 * ms.ease(min(1.0, (c_in - 0.45) / 0.22))
        d.text((W / 2, 1420), "COMMENT YOUR PICK", font=_font(int(96 * p2)), fill=CREAM, anchor="mm",
               stroke_width=7, stroke_fill=DARK)


def end_card_preview():
    """The end card over a look-test still of the last shot (the final frames aren't rendered yet)."""
    img = Image.open(os.path.join(WORK, "stills", "s_0720.png")).convert("RGBA").resize((W, H), Image.LANCZOS)
    d = ImageDraw.Draw(img)
    _end_card(d, 1.5)
    ms.watermark(d)
    out = os.path.join(WORK, "stills", "endcard_preview.png")
    img.convert("RGB").save(out)
    print(out)


def sound_events(starts, total):
    timing = json.load(open(os.path.join(WORK, "timing.json")))
    ev = []
    cues = json.load(open(os.path.join(WORK, "frames", "cues.json")))
    for c in cues.get("crunch", []):                    # bamboo crunches while it chews
        ev.append((c, sfx.tick(0.55, 0.22)))
    for k, s in enumerate(SEGMENTS):
        if k:
            ev.append((starts[k] - 0.04, sfx.whoosh(0.25, 0.18)))
        ev.append((starts[k] + 0.05, sfx.pop(0.3)))      # the callout pops in
    b = [k for k, s in enumerate(SEGMENTS) if s["shot"] == "baby"][0]
    ev.append((starts[b] - 0.25, sfx.riser(0.5, 0.2)))  # into the flashback
    for c in cues.get("thump", []):
        ev.append((c, sfx.thump(0.45)))
    ev.append((timing["ends"][-1] + 0.15, sfx.pop(0.4)))
    ev.append((timing["ends"][-1] + 0.6, sfx.pop(0.3)))   # "COMMENT YOUR PICK"
    return ev


def step_compose():
    out, vo = ms.render_short(SCRIPT, SEGMENTS, VIDEO_ID, frame, voice=VOICE, speed=SPEED, music_style="lounge",
                              sfx_fn=sound_events, music_vol=0.11, hook_hit=False)
    tmp = out.replace(".mp4", "_norm.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", out, "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5:LRA=9",
                    "-ar", "48000", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", tmp], check=True)
    os.replace(tmp, out)
    return out


# The first comment (owner pins it): the pick, plus a reason to come back and like answers. We keep the promise:
# the next Animals Complain Short is the most-liked pick (its script still goes to the owner first, rule 14).
COMMENT = "Sloth 🦥 or koala 🐨? The most-liked answer gets the next video 👇"


def publish():
    """Owner, 2026-11-05: "Now don't ask push video live". Uploads private (with a placeholder publishAt so the
    one-a-day slot picker can't move it to another day), adds captions and a cover, flips it public now
    (publishAt has gone live unpredictably before), seeds the question comment, then reads every setting back."""
    import datetime
    import config
    import phase5_upload as p5
    import pro_shorts_creator as psc
    out = os.path.join(config.VIDEOS_DIR, f"{VIDEO_ID}.mp4")
    vo = os.path.join(config.AUDIO_DIR, f"{VIDEO_ID}_vo.wav")
    soon = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    script = dict(SCRIPT, video_title=SCRIPT["title"], publish_at=soon)
    config.UPLOAD_PRIVACY = "private"
    url, _ = p5.upload_to_youtube(out, script, {"title": SCRIPT["title"], "subject": SCRIPT["hook"],
                                                "category": "Animals"})
    vid = url.rsplit("=", 1)[-1]
    srt = os.path.splitext(vo)[0] + ".srt"
    try:                                   # a caption failure must not leave the video stuck private
        psc.generate_srt(psc.get_word_timestamps(vo), srt)
        p5.upload_captions(vid, srt)
    except Exception as e:
        print("captions failed:", e)
    thumb = os.path.join(config.OUTPUT_DIR, "thumbnails", f"{VIDEO_ID}.jpg")
    os.makedirs(os.path.dirname(thumb), exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "1.0", "-i", out, "-frames:v", "1", "-q:v", "3", thumb],
                   check=True)
    p5.upload_thumbnail(vid, thumb)
    p5.push_video_public(vid)
    p5.post_engagement_comment(vid, COMMENT)
    yt = p5.get_youtube_client()
    v = yt.videos().list(part="snippet,status,contentDetails", id=vid).execute()["items"][0]
    caps = yt.captions().list(part="snippet", videoId=vid).execute().get("items", [])
    check = {"id": vid, "url": url, "title": v["snippet"]["title"], "category": v["snippet"]["categoryId"],
             "privacy": v["status"]["privacyStatus"], "publishAt": v["status"].get("publishAt"),
             "madeForKids": v["status"].get("selfDeclaredMadeForKids"), "duration": v["contentDetails"]["duration"],
             "captions": [c["snippet"]["language"] for c in caps], "tags": len(v["snippet"].get("tags", []))}
    print(json.dumps(check, indent=1))
    with open(os.path.join(WORK, "published.json"), "w") as f:
        json.dump(check, f, indent=1)
    return vid


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
    elif cmd == "endcard":
        end_card_preview()
    elif cmd == "publish":
        publish()
    else:
        print(__doc__)
