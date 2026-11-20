"""
live_package.py — a looping "What If Marathon" for the owner to stream live from their own PC with OBS
(owner, 2026-11-16: "going live ... show the content for subscriber and gain watching hours"; this machine
cannot stream: the network blocks YouTube's ingest and the container restarts on its own).

Before each of our Shorts, Jems asks a quiz question (his voice, A/B options, a 10-second countdown); the
Short then reveals the answer. A LIVE banner sits on top and a "vote what Jems tries next" bar at the bottom
the whole time, so the owner only has to read the chat and reply.

  python live_package.py            -> output/live/what_if_marathon.mp4 (720x1280, loops cleanly)
"""
import json
import os
import subprocess

import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFont

import config
import genai_clients as g

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output", "live")
W, H, FPS = 720, 1280, 30
VOICE, RATE = "am_puck", 1.05     # Jems' voice: free local Kokoro (owner, 2026-11-19)
FONT = os.path.join(HERE, "fonts", "BebasNeue-Regular.ttf")
GOLD, WHITE, DARK, RED = (255, 200, 40), (255, 255, 255), (12, 12, 16), (210, 20, 20)

# (Short, question, option A, option B) -- each answer is what that Short shows
QUIZ = [
    ("friction", "If friction disappeared, could you still walk?", "YES", "NO"),
    ("lavayou", "You fall into lava. What burns last?", "YOUR SKIN", "YOUR BONES"),
    ("oxygen", "All the oxygen vanishes for five seconds. What happens to your ears?", "THEY POP", "NOTHING"),
    ("gravity", "Gravity stops for five seconds. Do you fly off into space?", "YES", "NO"),
    ("penny", "A penny dropped from a skyscraper. Can it kill you?", "YES", "NO"),
    ("lightning", "Lightning hits your car. What saves you?", "THE RUBBER TIRES", "THE METAL BODY"),
    ("quicksand", "Can quicksand swallow you whole?", "YES", "NO"),
    ("sinking", "Your car sinks in a river. What do you do first?", "CALL FOR HELP", "OPEN THE WINDOW"),
    ("hail", "How fast can the biggest hailstones fall?", "LIKE A BIKE", "LIKE A CAR ON A HIGHWAY"),
    ("ocean", "At the bottom of the ocean, how much does the water press on you?", "10 TIMES", "OVER 1,000 TIMES"),
    ("venus", "Ten seconds on Venus. Does a dummy catch fire?", "YES", "NO"),
    ("lava", "Fall into lava: do you sink?", "YOU SINK", "YOU STAY ON TOP"),
    ("panda_scam", "How much of its bamboo does a panda actually digest?", "ALMOST ALL", "LESS THAN A FIFTH"),
    ("chick_egg_3d", "When does a chick's heart start beating inside the egg?", "DAY 2", "DAY 15"),
    ("snake_egg_3d", "How does an egg-eating snake crack the egg?", "WITH ITS TEETH", "SPIKES ON ITS SPINE"),
    ("egg_sizes_blender", "How many chicken eggs fit in an elephant bird egg?", "ABOUT 15", "ABOUT 150"),
    ("strange_eggs_3d", "Where do baby Surinam toads come out?", "FROM A NEST", "FROM MOM'S BACK"),
]
INTRO = ("Hey, I'm Jems! Welcome to the What If marathon. Before every video, guess the answer in the chat. "
         "Vote what I should try next, and subscribe, so you see the winner when I make it.")


def font(sz):
    return ImageFont.truetype(FONT, sz)


def wrap(d, text, f, width):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if d.textlength(t, font=f) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w_
    return lines + [cur]


def chrome(img):
    """The LIVE banner and the vote bar, drawn on every frame of the stream."""
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W, 64), fill=(0, 0, 0))
    d.rounded_rectangle((16, 12, 104, 52), radius=8, fill=RED)
    d.text((60, 33), "LIVE", font=font(34), fill=WHITE, anchor="mm")
    d.text((120, 33), "WHAT IF MARATHON  WITH JEMS", font=font(36), fill=GOLD, anchor="lm")
    d.rectangle((0, H - 88, W, H), fill=(0, 0, 0))
    d.text((W / 2, H - 64), "SUBSCRIBE + VOTE WHAT JEMS TRIES NEXT (TYPE 1, 2 OR 3)", font=font(30), fill=GOLD, anchor="mm")
    d.text((W / 2, H - 28), "1 TIME STOPS    2 THE SUN VANISHES    3 EARTH STOPS SPINNING", font=font(30), fill=WHITE,
           anchor="mm")
    return img


def card(title, body, a=None, b=None, count=None):
    img = Image.new("RGB", (W, H), (20, 24, 40))
    d = ImageDraw.Draw(img)
    for y in range(H):                                           # a soft vertical gradient
        c = int(20 + 30 * y / H)
        d.line((0, y, W, y), fill=(c, c + 4, c + 26))
    d.text((W / 2, 200), title, font=font(78), fill=GOLD, anchor="mm")
    f = font(64)
    y = 330
    for line in wrap(d, body.upper(), f, W - 90):
        d.text((W / 2, y), line, font=f, fill=WHITE, anchor="mm")
        y += 72
    if a:
        for j, (lab, txt) in enumerate((("A", a), ("B", b))):
            top = y + 50 + j * 150
            d.rounded_rectangle((60, top, W - 60, top + 120), radius=24, fill=(40, 46, 74), outline=GOLD, width=4)
            d.text((110, top + 60), lab, font=font(70), fill=GOLD, anchor="mm")
            d.text((W / 2 + 30, top + 60), txt, font=font(56 if len(txt) < 18 else 44), fill=WHITE, anchor="mm")
        if count is not None:
            d.ellipse((W / 2 - 70, 1000, W / 2 + 70, 1140), fill=RED if count <= 3 else (40, 46, 74), outline=WHITE,
                      width=5)
            d.text((W / 2, 1072), str(count), font=font(96), fill=WHITE, anchor="mm")
            d.text((W / 2, 960), "ANSWER IN THE CHAT", font=font(46), fill=GOLD, anchor="mm")
    return chrome(img)


def voice(text, path):
    import pro_shorts_creator as psc
    a, sr = psc._get_kokoro().create(text, voice=VOICE, speed=RATE, lang="en-us")
    sf.write(path, a, sr)
    return len(a) / sr


def run(cmd):
    subprocess.run(cmd, check=True)


def segment_card(name, frames, audio, dur):
    """frames: list of (png, seconds). Writes a 720x1280 30fps clip with the voice (or silence) under it."""
    lst = os.path.join(OUT, f"{name}_frames.txt")
    with open(lst, "w") as f:
        for p, s in frames:
            f.write(f"file '{p}'\nduration {s}\n")
        f.write(f"file '{frames[-1][0]}'\n")
    out = os.path.join(OUT, f"{name}.mp4")
    aud = ["-i", audio] if audio else ["-f", "lavfi", "-t", str(dur), "-i", "anullsrc=r=48000:cl=stereo"]
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, *aud, "-t", str(dur),
         "-vf", f"fps={FPS},format=yuv420p", "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
         "-af", "apad,aresample=48000", "-ac", "2", "-c:a", "aac", "-b:a", "128k", out])
    return out


def segment_short(name):
    src = os.path.join(HERE, "output", "videos", f"dummy_{name}.mp4")
    if not os.path.exists(src):                                  # our other 3D Shorts keep their own names
        src = os.path.join(HERE, "output", "videos", f"{name}.mp4")
    bar = os.path.join(OUT, "chrome.png")
    if not os.path.exists(bar):
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        chrome(img)
        img.save(bar)
    out = os.path.join(OUT, f"short_{name}.mp4")
    run(["ffmpeg", "-v", "error", "-y", "-i", src, "-i", bar, "-filter_complex",
         f"[0:v]scale={W}:{H},fps={FPS}[v];[v][1:v]overlay=0:0,format=yuv420p", "-c:v", "libx264", "-preset",
         "veryfast", "-crf", "23", "-af", "aresample=48000", "-ac", "2", "-c:a", "aac", "-b:a", "128k", out])
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    parts = []
    wav = os.path.join(OUT, "intro.wav")
    dur = voice(INTRO, wav) + 1.0
    p = os.path.join(OUT, "intro.png")
    card("WELCOME!", "Guess each answer in the chat before the video shows it").save(p)
    parts.append(segment_card("intro", [(p, dur)], wav, dur))
    for j, (name, q, a, b) in enumerate(QUIZ):
        wav = os.path.join(OUT, f"q{j}.wav")
        spoken = voice(f"{q} A: {a.lower()}, or B: {b.lower()}?", wav)
        frames = []
        p0 = os.path.join(OUT, f"q{j}_ask.png")
        card(f"QUIZ #{j + 1}", q, a, b).save(p0)
        frames.append((p0, spoken + 0.4))
        for c in range(10, 0, -1):
            pc = os.path.join(OUT, f"q{j}_{c}.png")
            card(f"QUIZ #{j + 1}", q, a, b, count=c).save(pc)
            frames.append((pc, 1.0))
        parts.append(segment_card(f"q{j}", frames, wav, spoken + 10.4))
        parts.append(segment_short(name))
    lst = os.path.join(OUT, "parts.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{p}'\n" for p in parts)
    final = os.path.join(OUT, "what_if_marathon_long.mp4")
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", final])
    print(final, json.dumps({"parts": len(parts)}))


if __name__ == "__main__":
    main()
