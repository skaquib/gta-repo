"""
run_deep_teaser_short.py — vertical teaser Short for "The Biggest Monster in Every Ocean Layer, Shown Next to You".

Native 9:16 Veo motion clips (no cropped or letterboxed 16:9), full screen, every shot moving. Hook in the first
words ("This eye is the size of a dinner plate"), one fast escalating story (giant squid -> the whale that hunts it
-> the scars -> the bottom of the ocean), and an open ending that points to the full video. The link goes in the
description and the first comment; the owner sets the Short's Related video in YouTube Studio (the API can't).

  python run_deep_teaser_short.py assets | build | publish <long_video_id> <publish_at RFC3339>
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import config

import motion_shorts as ms
import realistic_video as rv
import sfx

VIDEO_ID = "deep_teaser_short"
VOICE = "en-US-Chirp3-HD-Charon"
W, H = 1080, 1920
HERE = os.path.dirname(os.path.abspath(__file__))
FONT_T = os.path.join(HERE, "fonts", "BebasNeue-Regular.ttf")
GOLD, WHITE = (255, 214, 70), (255, 255, 255)
THUMB = os.path.join(HERE, "output", "thumbnails", f"{VIDEO_ID}.jpg")
NOANI = ", completely empty water: no animals, no fish, no creatures"

PROMPTS = {
    "v_eye": "Extreme close-up of a giant squid's enormous dark eye filling the frame, reddish-brown skin around it, "
             "faint light reflection on the eye, deep sea darkness",
    "v_squid": "Giant squid Architeuthis rising toward the camera through dark blue water, long reddish-brown "
               "torpedo-shaped body with two small fins at the tip, eight thick arms and two much longer thin feeding "
               "tentacles with club ends, one huge eye",
    "v_whale_dive": "Seen from directly above and behind: a sperm whale diving head-first down into the dark blue "
                    "depths, its long wrinkled dark grey back and huge blunt box-shaped head pointing down, wide flat "
                    "triangular tail flukes at the top, flippers hidden under the body, sunlight fading to black below",
    "v_scars": "Close-up of a sperm whale's wrinkled dark grey skin marked with many circular scars from squid suckers",
    "v_descend": "Looking straight down into the deep ocean, the last light shafts fading into black, marine snow "
                 "drifting" + NOANI,
    "v_bottom": "The floor of the deepest ocean trench lit by a submersible's lights, smooth pale grey sediment, marine "
                "snow drifting" + NOANI + ", no tracks",
}
MOTION = {
    "v_eye": "The huge eye slowly turns toward the camera, the pupil shifting, skin rippling, particles drifting past",
    "v_squid": "The giant squid rises slowly toward the camera, arms and long tentacles trailing and curling",
    "v_whale_dive": "The sperm whale dives steadily away from the camera, down into the darkness, its tail flukes "
                    "beating slowly, the body shrinking into the black",
    "v_scars": "The camera glides slowly along the scarred skin as the whale swims past",
    "v_descend": "The camera sinks fast into the darkness, marine snow streaming upward past the lens; no animals appear",
    "v_bottom": "The camera glides forward low over the empty sediment, its lights sweeping, sediment puffing up; "
                "no animals appear",
}
CLIP_TRIM = {"v_squid": 3.5, "v_scars": 2.4, "v_bottom": 4.5, "v_descend": 5.0, "v_whale_dive": 1.8}   # before anatomy drift / fade

SEGMENTS = [
    {"line": "This eye is the size of a dinner plate.", "head": "DINNER-PLATE EYE", "shots": ["v_eye"]},
    {"line": "It belongs to a giant squid, as long as a city bus, hunting up to a kilometre below you.",
     "head": "AS LONG AS A BUS", "shots": ["v_squid"]},
    {"line": "Its worst enemy is a whale that dives two kilometres into total darkness to eat it.",
     "head": "2 KM DOWN", "shots": ["v_whale_dive", "v_descend"]},
    {"line": "Those circles on its skin? Sucker scars, from the fight.", "head": "SUCKER SCARS", "shots": ["v_scars"]},
    {"line": "And the deeper you go, the stranger it gets.", "head": "DEEPER...", "shots": ["v_descend@2.2"]},
    {"line": "Eleven kilometres down, at the very bottom, scientists found something nobody expected.",
     "head": "11 KM DOWN", "shots": ["v_bottom"]},
    {"line": "The full dive, every ocean layer shown next to you, is on our channel.", "head": "THE FULL DIVE",
     "shots": ["v_bottom@2.0", "v_eye@3.0"], "end": True},     # ends on the eye: the Short loops into its own hook
]

SCRIPT = {
    "format": "short",
    "hook": SEGMENTS[0]["line"],
    "body": " ".join(s["line"] for s in SEGMENTS[1:-1]),
    "cta": "Would you go down to the bottom?",
    "title": "This Eye Is the Size of a Dinner Plate #shorts",
    "category_id": "27",
    "tags": ["giant squid", "sperm whale", "deep sea creatures", "deep sea", "ocean", "mariana trench", "kraken",
             "sea monsters", "thalassophobia", "ocean facts", "animals", "shorts"],
    "ai_generated_visuals": True,
    "topic_category": "Animals",
}


def description(long_id):
    return (f"Full video, every ocean layer shown next to you: https://www.youtube.com/watch?v={long_id}\n\n"
            "A giant squid's eye can be about the size of a dinner plate, and the animal can reach roughly the length of "
            "a bus. Its main predator, the sperm whale, dives two kilometres down to hunt it and carries sucker scars "
            "from the fight. And at the bottom of the Mariana Trench, 11 km down, scientists found something nobody "
            "expected.\n\n"
            "Visuals are AI-generated reconstructions (Google Gemini and Veo). Sources: Smithsonian Ocean; Nilsson et "
            "al. (2012), Current Biology; American Museum of Natural History; Chiba et al. (2018), Marine Policy.\n\n"
            "#deepsea #giantsquid #shorts")


_clips = {}


def clip_frame(key, t_in, dur):
    """Full-screen vertical clip; slow motion when the slot is long, drifts back instead of freezing.
    "key@2.0" starts 2 s into the clip, so a clip used twice shows a different part."""
    key, _, st = key.partition("@")
    if key not in _clips:
        from moviepy import VideoFileClip
        _clips[key] = VideoFileClip(os.path.join(rv.asset_dir(VIDEO_ID), f"{key}.mp4"), audio=False)
    c = _clips[key]
    usable = min(c.duration, CLIP_TRIM.get(key, c.duration)) - 0.05
    start = min(float(st or 0), max(0.0, usable - 0.45 * dur))
    speed = min(1.0, max(0.45, (usable - start) / max(dur, 0.1)))
    pos = start + t_in * speed
    if pos > usable:
        pos = max(0.0, usable - (pos - usable))
    return Image.fromarray(c.get_frame(pos)).resize((W, H), Image.BICUBIC).convert("RGBA")


def frame(t, i, t_in, starts):
    seg = SEGMENTS[i]
    dur = (starts[i + 1] - starts[i]) if i + 1 < len(starts) else 3.0
    n = len(seg["shots"])
    k = min(n - 1, int(t_in / (dur / n)))
    img = clip_frame(seg["shots"][k], t_in - k * dur / n, dur / n)
    # darken top and bottom a little so the text reads on any shot
    shade = np.zeros((H, W, 4), np.uint8)
    yy = np.linspace(0, 1, H)[:, None]
    shade[..., 3] = (np.clip(np.maximum((0.28 - yy) / 0.28, (yy - 0.55) / 0.45), 0, 1) * 150).astype(np.uint8)
    img.alpha_composite(Image.fromarray(shade, "RGBA"))
    d = ImageDraw.Draw(img)
    pop = 0.85 + 0.15 * ms.ease(t_in / 0.2)
    head = seg["head"]
    d.text((W / 2, 300), head, font=ImageFont.truetype(FONT_T, int((150 if len(head) < 14 else 124) * pop)),
           fill=GOLD, anchor="mm", stroke_width=8, stroke_fill=(0, 0, 0))
    ms.caption(d, 1310, seg["line"], size=68)
    if seg.get("end"):
        d.rounded_rectangle([140, 1640, W - 140, 1750], 40, fill=(230, 40, 40))
        d.text((W / 2, 1695), "FULL VIDEO ON OUR CHANNEL", font=ImageFont.truetype(FONT_T, 70), fill=WHITE, anchor="mm")
    if t < 4.0:
        d.text((W - 40, H - 60), "AI-generated visuals", font=ImageFont.truetype(FONT_T, 34), fill=(230, 235, 240),
               anchor="rm")
    ms.watermark(d)
    return np.array(img.convert("RGB"))


def sound_events(starts, total):
    ev = [(0.0, sfx.deep_boom(0.8))]
    ev += [(s - 0.05, sfx.whoosh(0.3, 0.3)) for s in starts[1:]]
    ev += [(starts[5] + 0.1, sfx.deep_boom(0.7))]
    return ev


def make_thumbnail():
    """A cover frame for the Short (the giant squid eye with the headline)."""
    starts = [0.0, 2.0]
    Image.fromarray(frame(1.0, 0, 1.0, starts)).save(THUMB, quality=92)


def publish(long_id, publish_at=None):
    """Uploads PRIVATE. The channel's standing rule: publishAt has gone live early before, so the video is
    flipped public at the owner's time with phase5_upload.push_video_public (publish_at is only a fallback)."""
    import phase5_upload as p5
    import pro_shorts_creator as psc
    out = os.path.join(config.VIDEOS_DIR, f"{VIDEO_ID}.mp4")
    vo = os.path.join(config.AUDIO_DIR, f"{VIDEO_ID}_vo.wav")
    script = dict(SCRIPT, video_title=SCRIPT["title"], seo_description=description(long_id))
    if publish_at:
        script["publish_at"] = publish_at
    config.UPLOAD_PRIVACY = "private"
    url, _ = p5.upload_to_youtube(out, script, {"title": SCRIPT["title"], "subject": SCRIPT["hook"], "category": "Animals"})
    vid = url.rsplit("=", 1)[-1]
    srt = os.path.splitext(vo)[0] + ".srt"
    psc.generate_srt(psc.get_word_timestamps(vo), srt)
    p5.upload_captions(vid, srt)
    return vid


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    if cmd == "assets":
        print(rv.gen_images(PROMPTS, VIDEO_ID, aspect="9:16"))
        print(rv.gen_clips(MOTION, VIDEO_ID, seconds=8, model="veo-3.1-lite-generate-001", aspect="9:16"))
    if cmd == "build":
        out, _ = ms.render_short(SCRIPT, SEGMENTS, VIDEO_ID, frame, voice=VOICE, speed=1.0, music_style="deep",
                                 sfx_fn=sound_events, music_vol=0.10, hook_hit=False, gap_s=0.12)
        import subprocess
        tmp = out.replace(".mp4", "_norm.mp4")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", out, "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5:LRA=9",
                        "-ar", "48000", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", tmp], check=True)
        os.replace(tmp, out)
        make_thumbnail()
    if cmd == "publish":
        print(publish(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None))
