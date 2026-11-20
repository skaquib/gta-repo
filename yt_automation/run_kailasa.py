"""
run_kailasa.py: build series episode 1, "How Did They Carve a Temple From ONE Rock?" (vertical Short).

Owner, 2026-11-19: series "How Did They Build It Without Machines?". Title 1, thumbnail A, opening A, "mixed" visuals:
4 AI hero clips on the free credit (visuals only), the step-by-step 3D in Blender (free), a free local voice.
From 0.0 s the spoken words, the on-screen words and the picture say the same thing (LESSONS.md).

  python run_kailasa.py voice        # free Kokoro voice -> timing (segment starts, 3D shot frame ranges)
  python run_kailasa.py ai           # hero stills + Veo clips (free credit)
  python run_kailasa.py stills       # 3D look-test stills, one per 3D shot
  python run_kailasa.py frames       # full 3D render (15 fps)
  python run_kailasa.py build        # compose -> output/videos/kailasa_ep1.mp4
"""
import json
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import config
import motion_shorts as ms
import realistic_video as rv

LANG = os.environ.get("LANG_VER", "en")          # "en" or "hi" (owner, 2026-11-19: a Hindi version for India)
ASSET = "kailasa_ep1"                             # the pictures and clips are shared by both versions
VID = ASSET if LANG == "en" else ASSET + "_hi"
HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "output", "build_series", VID)
FR3D = os.path.join(WORK, "frames3d")
TIMING = os.path.join(WORK, "timing.json")
THUMBS = os.path.join(HERE, "output", "build_series", "thumbs")
W, H, FPS, F3D = 1080, 1920, 30, 15
VOICE, SPEED = ("am_michael", 1.0) if LANG == "en" else ("hf_beta", 0.95)      # owner picked hf_beta
FONT = os.path.join(HERE, "fonts", "BebasNeue-Regular.ttf")                 # Hinglish is written in Roman letters
GOLD, WHITE, DARK = (255, 214, 40), (255, 255, 255), (0, 0, 0)
BLENDER_PY = "/root/.venvs/blender/bin/python"


def S(line, shot, label=None, say=None, big=False, cta=None):
    d = dict(line=line, shot=shot, label=label, big=big, cta=cta)
    if say:
        d["say"] = say
    return d


SEGMENTS = [
    S("This entire temple is ONE rock.", "clip:open", "1 ROCK", big=True),
    S("No bricks. No machines. Just hammers, chisels... and a mountain.", "clip:chisel", "NO MACHINES"),
    S("Normal buildings go up. This one went down.", "d2:updown"),
    S("They started at the top of a cliff,", "clip:hill"),
    S("and cut a giant pit around one huge block of rock.", "clip:trench", "STEP 1: THE PIT"),
    S("Then they carved that block from the top down: roof first, then walls, then the floors below.", "clip:carve",
      "STEP 2: TOP DOWN"),
    S("And there was no undo. One wrong cut, and that piece of the temple was gone forever.", "clip:crack", "NO UNDO"),
    S("By the end, they had removed up to two hundred thousand tonnes of rock.", "clip:rubble", "200,000 TONNES"),
    S("That's as heavy as tens of thousands of elephants.", "d2:elephants"),
    S("What's left is a temple about as tall as a ten-storey building,", "clip:storeys", "≈ 10 STOREYS"),
    S("with bridges, pillars, and life-size stone elephants, all still part of the same mountain.", "clip:courtyard"),
    S("It was begun about twelve hundred years ago, under the Rashtrakuta king Krishna the First,", "clip:sunset",
      "ELLORA, INDIA · 8TH CENTURY", say="It was begun about twelve hundred years ago, under the Rashtra-koota king, "
                                         "Krishna the First,"),
    S("and it is still the largest monolithic temple in the world.", "clip:sunset", "WORLD'S LARGEST MONOLITH"),
    S("Could we carve this today, even with machines? Comment: yes or no.", "img:open", "YES OR NO?", cta="comment"),
    S("And send this to someone who thinks ancient people were primitive.", "clip:chisel", "SEND THIS TO THEM",
      cta="share"),
    S("Next: ancient India made an iron pillar that still hasn't rusted in sixteen hundred years. How? Follow, so you "
      "see it tomorrow.", "img:pillar", "NEXT: THE IRON PILLAR", cta="subscribe"),
]

SEGMENTS_HI = [   # Hinglish (owner, 2026-11-19): Roman Hinglish on screen, the voice reads the Devanagari 'say'
    S('Ye poora temple... ek hi rock hai.', 'clip:open', '1 ROCK', say='ये पूरा टेंपल... एक ही रॉक है।', big=True),
    S('Na bricks, na machines. Bas hathauda, chheni... aur ek pahaad.', 'clip:chisel', 'KOI MACHINE NAHI', say='ना ब्रिक्स, ना मशीन्स। बस हथौड़ा, छेनी... और एक पहाड़।'),
    S('Normal buildings upar bante hain. Ye neeche ki taraf bana.', 'd2:updown', None, say='नॉर्मल बिल्डिंग्स ऊपर बनती हैं। ये नीचे की तरफ़ बना।'),
    S('Shuruaat hui ek pahaad ki choti se,', 'clip:hill', None, say='शुरुआत हुई एक पहाड़ की चोटी से,'),
    S('phir ek huge rock ke chaaron taraf gehra gaddha khoda gaya.', 'clip:trench', 'STEP 1: GADDHA', say='फिर एक ह्यूज रॉक के चारों तरफ़ गहरा गड्ढा खोदा गया।'),
    S('Phir us rock ko top se neeche tak taraasha: pehle chhat, phir deewarein, phir neeche ke floors.', 'clip:carve', 'STEP 2: TOP SE NEECHE', say='फिर उस रॉक को टॉप से नीचे तक तराशा: पहले छत, फिर दीवारें, फिर नीचे के फ़्लोर्स।'),
    S('Aur koi undo nahi tha. Ek galat cut, aur wo hissa hamesha ke liye gaya.', 'clip:crack', 'NO UNDO', say='और कोई अनडू नहीं था। एक गलत कट, और वो हिस्सा हमेशा के लिए गया।'),
    S('End tak, do lakh ton tak rock hataya gaya.', 'clip:rubble', '2,00,000 TON', say='एंड तक, दो लाख टन तक रॉक हटाया गया।'),
    S('Itna weight, jitna hazaaron haathiyon ka.', 'd2:elephants', None, say='इतना वेट, जितना हज़ारों हाथियों का।'),
    S('Aur jo bacha, wo lagbhag das-manzila building jitna uncha temple hai,', 'clip:storeys', '≈ 10 MANZIL', say='और जो बचा, वो लगभग दस मंज़िला बिल्डिंग जितना ऊँचा टेंपल है,'),
    S('Bridges, pillars, aur life-size patthar ke haathi, sab usi pahaad ka hissa.', 'clip:courtyard', None, say='ब्रिजेस, पिलर्स, और लाइफ़-साइज़ पत्थर के हाथी, सब उसी पहाड़ का हिस्सा।'),
    S('Ise lagbhag 1200 saal pehle, Rashtrakuta raja Krishna pratham ke time shuru kiya gaya,', 'clip:sunset', 'ELLORA · 8VI SADI', say='इसे लगभग बारह सौ साल पहले, राष्ट्रकूट राजा कृष्ण प्रथम के टाइम शुरू किया गया,'),
    S('Aur aaj bhi ye duniya ka sabse bada ek-chattani temple hai.', 'clip:sunset', 'DUNIYA MEIN SABSE BADA', say='और आज भी ये दुनिया का सबसे बड़ा एक-चट्टानी टेंपल है।'),
    S('Kya aaj, machines ke saath bhi, hum aisa bana sakte hain? Comment karo: haan ya na.', 'img:open', 'HAAN YA NA?', say='क्या आज, मशीन्स के साथ भी, हम ऐसा बना सकते हैं? कमेंट करो: हाँ या ना।', cta='comment'),
    S('Aur ye video us dost ko bhejo, jo sochta hai ki purane log pichhde the.', 'clip:chisel', 'DOST KO BHEJO', say='और ये वीडियो उस दोस्त को भेजो, जो सोचता है कि पुराने लोग पिछड़े थे।', cta='share'),
    S('Next: ancient India ka iron pillar, jismein 1600 saal mein bhi zang nahi laga. Kaise? Follow karo, taaki kal ka video miss na ho.', 'img:pillar', 'NEXT: IRON PILLAR', say='नेक्स्ट: एंशिएंट इंडिया का आयरन पिलर, जिसमें सोलह सौ साल में भी ज़ंग नहीं लगा। कैसे? फ़ॉलो करो, ताकि कल का वीडियो मिस ना हो।', cta='subscribe'),
]
if LANG == "hi":
    SEGMENTS = [dict(s, lang="hi") for s in SEGMENTS_HI]

TITLE = {"en": "How Did They Carve a Temple From ONE Rock? 🛕 #shorts",
         "hi": "Ek Hi Rock Se Poora Temple Kaise Bana? 🛕 Kailasa Temple #shorts"}
SCRIPT = {"title": TITLE[LANG], "hook": SEGMENTS[0]["line"],
          "body": " ".join(s["line"] for s in SEGMENTS[1:]), "cta": SEGMENTS[-1]["line"]}

# ── AI hero shots (free credit: visuals only) ─────────────────────────────────
STYLE = ("stylized 3D render, clean cinematic diorama look, warm golden light, strong contrast, vertical 9:16, "
         "no text, no letters, no logos, no watermark, no modern objects, no hard hats")
AI = {
    "open": (None, "the camera slowly dives down toward the rock-cut temple, tiny workers move, dust drifts in the sunlight"),
    "chisel": ("Extreme close-up of an ancient Indian stone carver's hand holding an iron chisel against dark basalt rock, "
               "a wooden mallet striking it, rock chips flying, warm sunlight, 8th century",
               "the mallet strikes the chisel again and again, chips and dust fly"),
    "courtyard": ("Inside the courtyard of the rock-cut Kailasa temple at Ellora: life-size carved stone elephants along the "
                  "base, a carved stone bridge between two halls, tall carved pillars, sunlight sweeping across, low angle",
                  "slow camera glide past the stone elephants, sunlight moves across the carvings"),
    "hill": ("High aerial view of a flat black basalt plateau on a cliff in the Deccan, India, 8th century, a huge rectangle "
             "marked out on the rock with white ropes and stakes, tiny workers with hammers and chisels lined up along the "
             "rope, nothing carved yet", "slow aerial drift forward, tiny workers begin to strike the rock, dust puffs"),
    "trench": ("Aerial view of a black basalt plateau with a deep rectangular trench being dug around one giant solid block "
               "of rock left standing in the middle, hundreds of tiny workers with chisels in the trench, dust",
               "the trench gets deeper, workers chip away, dust rises, slow camera orbit"),
    "carve": ("A giant solid block of black rock standing in a deep pit, its TOP already carved into an ornate temple spire "
              "and roof while the lower half is still a rough uncarved block, tiny workers on scaffolding of wood carving "
              "downward", "workers carve downward, the carved part grows, chips fall, slow push-in"),
    "crack": ("Close-up of a carved stone pillar on an ancient rock temple breaking off at a crack and falling, an ancient "
              "Indian stone carver stepping back in shock, dust exploding", "the pillar snaps and topples, dust bursts out"),
    "rubble": ("A colossal mountain of broken black rock rubble next to a deep temple pit, a single tiny ancient Indian worker "
               "standing at its base for scale, long line of workers carrying baskets of rock up the pile",
               "workers carry baskets up the pile, dust drifts, slow camera tilt up the pile"),
    "storeys": ("The finished Kailasa rock-cut temple in its pit, and right beside it, for scale, a glowing transparent blue "
                "outline of a modern 10-storey building of exactly the same height, clear and simple",
                "slow orbit around the temple and the glowing outline building"),
    "sunset": ("Wide view at sunset of the giant Kailasa rock-cut temple standing inside the deep pit cut into a black "
               "basalt cliff at Ellora, India, warm orange sky", "slow push-in, the sunset light shifts, birds fly past"),
}


def gen_ai():
    from google.genai import types
    import shutil
    import genai_clients as g
    d = rv.asset_dir(ASSET)
    src = os.path.join(THUMBS, "kailasa_A_raw.png")          # the first frame IS the thumbnail picture
    if not os.path.exists(os.path.join(d, "open.png")):
        shutil.copy(src, os.path.join(d, "open.png"))
    pil = os.path.join(THUMBS, "pillar_A_raw.png")
    if not os.path.exists(os.path.join(d, "pillar.png")):
        shutil.copy(pil, os.path.join(d, "pillar.png"))
    c = dict(g.clients())["vertex"]
    for k, (prompt, _) in AI.items():
        out = os.path.join(d, f"{k}.png")
        if prompt is None or os.path.exists(out):
            continue
        for model in ("gemini-3-pro-image", "gemini-3.1-flash-image"):
            try:
                g.charge("image", 1, f"{VID}/{k}")
                r = c.models.generate_content(model=model, contents=prompt + ". Style: " + STYLE,
                                              config=types.GenerateContentConfig(response_modalities=["IMAGE"],
                                                                                 image_config=types.ImageConfig(aspect_ratio="9:16")))
                open(out, "wb").write(next(p for p in r.candidates[0].content.parts if p.inline_data).inline_data.data)
                print(k, model, flush=True)
                break
            except Exception as e:
                print(k, "ERR", str(e)[:120], flush=True)
    clips = {k: v[1] for k, v in AI.items()}
    return rv.gen_clips(clips, VID, seconds=6, batch=2, aspect="9:16",
                        style="stylized 3D render, cinematic, smooth natural motion, keep the exact look of the starting "
                              "image, vertical 9:16, no text, no captions, no logos, no morphing")


# ── voice and timing ──────────────────────────────────────────────────────────
def step_voice():
    os.makedirs(WORK, exist_ok=True)
    vo, starts, total = ms.build_voice(SEGMENTS, VID, voice=VOICE, speed=SPEED, gap_s=0.22)
    ends = starts[1:] + [total]
    b3d, f = [], 0
    for s, a, b in zip(SEGMENTS, starts, ends):
        if s["shot"].startswith("b3d:"):
            n = max(8, int(round((b - a) * F3D)) + 2)
            b3d.append(dict(name=s["shot"][4:], f0=f, f1=f + n - 1, t0=a, t1=b))
            f += n
    json.dump(dict(starts=starts, total=total, b3d=b3d, b3d_frames=f), open(TIMING, "w"), indent=1)
    print(json.dumps(dict(total=round(total, 2), b3d_frames=f)))


def step_3d(args):
    env = dict(os.environ, DUMMY_SAMPLES=os.environ.get("DUMMY_SAMPLES", "12"))
    subprocess.run([BLENDER_PY, os.path.join(HERE, "blender_kailasa.py"), TIMING, FR3D, *args], check=True, env=env)


# ── 2D animations (code-drawn) ────────────────────────────────────────────────
def font(sz):
    return ImageFont.truetype(FONT, sz)


def d2_updown(p):
    im = Image.new("RGB", (W, H), (24, 22, 30))
    d = ImageDraw.Draw(im)
    d.line((W / 2, 300, W / 2, 1300), fill=(80, 80, 90), width=4)
    # left: a brick tower rising
    rows = int(12 * min(1, p / 0.55))
    for r in range(rows):
        y = 1250 - r * 60
        for c_ in range(4):
            d.rectangle((110 + c_ * 80 + (r % 2) * 20, y, 180 + c_ * 80 + (r % 2) * 20, y + 52), fill=(180, 90, 60),
                        outline=(110, 50, 30), width=3)
    d.text((W / 4, 380), "UP" if LANG == "en" else "UPAR", font=font(150), fill=WHITE, anchor="mm", stroke_width=6, stroke_fill=DARK)
    d.polygon([(W / 4, 470), (W / 4 - 50, 540), (W / 4 + 50, 540)], fill=WHITE)
    # right: a hill being cut down into a temple
    q = min(1, max(0, (p - 0.35) / 0.6))
    d.rectangle((W / 2 + 60, 560, W - 60, 1310), fill=(70, 62, 56))
    cut = 560 + q * 600
    d.rectangle((W / 2 + 160, 560, W - 160, cut), fill=(24, 22, 30))
    for t_ in range(4):                                       # the spire tiers appear as the cut goes down
        y = 640 + t_ * 120
        if cut > y + 60:
            w = 70 + t_ * 40
            d.rectangle((W * 3 / 4 - w, y, W * 3 / 4 + w, y + 110), fill=(160, 136, 110))
    d.text((W * 3 / 4, 380), "DOWN" if LANG == "en" else "NEECHE", font=font(150), fill=GOLD, anchor="mm", stroke_width=6, stroke_fill=DARK)
    d.polygon([(W * 3 / 4, 540), (W * 3 / 4 - 50, 470), (W * 3 / 4 + 50, 470)], fill=GOLD)
    return np.asarray(im)


def _elephant(d, x, y, s, col):
    d.ellipse((x - 40 * s, y - 26 * s, x + 40 * s, y + 22 * s), fill=col)                # body
    d.ellipse((x + 26 * s, y - 34 * s, x + 58 * s, y + 2 * s), fill=col)                 # head
    d.rectangle((x + 46 * s, y - 6 * s, x + 56 * s, y + 34 * s), fill=col)               # trunk
    for lx in (-30, -12, 8, 24):
        d.rectangle((x + lx * s, y + 10 * s, x + (lx + 11) * s, y + 40 * s), fill=col)   # legs


def d2_elephants(p):
    im = Image.new("RGB", (W, H), (24, 22, 30))
    d = ImageDraw.Draw(im)
    n = int(140 * min(1, p / 0.8))
    for i in range(n):
        r, c_ = divmod(i, 10)
        _elephant(d, 90 + c_ * 100, 420 + r * 74, 0.95, (150, 150, 160) if i % 7 else (200, 200, 210))
    d.text((W / 2, 300), "× TENS OF THOUSANDS" if LANG == "en" else "× HAZAARON HAATHI", font=font(110), fill=GOLD, anchor="mm", stroke_width=6, stroke_fill=DARK)
    return np.asarray(im)


D2 = {"updown": d2_updown, "elephants": d2_elephants}


# ── compose ───────────────────────────────────────────────────────────────────
_cache = {}


def _f3d(idx):
    p = os.path.join(FR3D, f"f_{idx:04d}.png")
    if p not in _cache:
        _cache.clear()
        _cache[p] = np.asarray(Image.open(p).convert("RGB").resize((W, H), Image.LANCZOS))
    return _cache[p]


def caption(d, line, t_in, dur):
    """Word-by-word caption: the current phrase (up to 4 words) with the spoken word in gold."""
    words = line.split()
    k = min(len(words) - 1, int(len(words) * t_in / max(dur - 0.15, 0.1)))
    a = (k // 4) * 4
    chunk = words[a:a + 4]
    f = font(92)
    tw = sum(d.textlength(w + " ", font=f) for w in chunk)
    x = (W - tw) / 2
    for j, w in enumerate(chunk):
        d.text((x, 1450), w, font=f, fill=GOLD if a + j == k else WHITE, stroke_width=7, stroke_fill=DARK)
        x += d.textlength(w + " ", font=f)


LAT = os.path.join(HERE, "fonts", "BebasNeue-Regular.ttf")


def _pill(d, cx, cy, w, h, fill, text, fnt, fg=WHITE):
    d.rounded_rectangle((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), radius=h / 2, fill=fill)
    d.text((cx, cy), text, font=fnt, fill=fg, anchor="mm")


def cta_layer(kind, t_in, dur):
    """Vertical call-to-action buttons drawn in code: a comment bubble, a share button, a subscribe button that is
    pressed (turns grey, SUBSCRIBED) with the bell ringing. A cursor taps each one."""
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    a = ms.ease(min(1.0, t_in / 0.3))
    y = int(1180 + (1 - a) * 80)
    fb = ImageFont.truetype(LAT, 76)
    tap = min(1.0, max(0.0, (t_in - 0.9) / 0.4))
    if kind == "comment":
        d.rounded_rectangle((300, y - 80, 780, y + 70), radius=40, fill=(255, 255, 255, 235))
        d.polygon([(380, y + 60), (360, y + 130), (450, y + 66)], fill=(255, 255, 255, 235))
        d.text((540, y - 5), ("YES" if LANG == "en" else "HAAN") + "  /  " + ("NO" if LANG == "en" else "NA"),
               font=ImageFont.truetype(FONT, 80), fill=(20, 20, 20), anchor="mm")
    elif kind == "share":
        _pill(d, 540, y, 420, 130, (255, 255, 255, 240), "", fb)
        d.polygon([(400, y + 10), (470, y - 40), (470, y - 15), (520, y - 15), (520, y + 35), (470, y + 35), (470, y + 60)],
                  fill=(20, 20, 20))
        d.text((600, y + 8), "SHARE", font=fb, fill=(20, 20, 20), anchor="mm")
    else:
        pressed = t_in > 1.3
        _pill(d, 470, y, 460, 130, (90, 90, 90, 240) if pressed else (220, 20, 20, 245),
              "SUBSCRIBED" if pressed else "SUBSCRIBE", fb)
        bx, by = 780, y                                          # bell
        sw = math.sin(t_in * 18) * 10 if pressed and t_in < 2.4 else 0
        d.ellipse((bx - 50, by - 50, bx + 50, by + 50), fill=(255, 255, 255, 240))
        d.polygon([(bx - 26 + sw, by + 18), (bx + 26 + sw, by + 18), (bx + 18 + sw, by - 20), (bx - 18 + sw, by - 20)],
                  fill=(20, 20, 20))
        d.ellipse((bx - 7 + sw, by + 18, bx + 7 + sw, by + 32), fill=(20, 20, 20))
    if 0.6 < t_in < 2.2:                                         # the cursor taps the button
        cx, cy = 600 + 120 * (1 - tap), y + 40 + 60 * (1 - tap)
        r = 22 if tap < 1 else 16
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255, 230), outline=(0, 0, 0, 255), width=4)
    return L


def frame_fn(T):
    b3d = {s["name"]: s for s in T["b3d"]}

    def frame(t, i, t_in, starts):
        seg = SEGMENTS[i]
        dur = (starts[i + 1] - starts[i]) if i + 1 < len(starts) else 3.0
        kind, key = seg["shot"].split(":", 1)
        if kind == "clip":
            off = 3.0 if ((key == "sunset" and i == 12) or (key == "chisel" and i > 1)) else 0.0   # 2nd use continues
            base = rv.frame_clip(ASSET, key, t_in, dur, start=off) if rv.has_clip(ASSET, key) else \
                rv.frame_still(ASSET, key, min(1.0, t_in / dur), i)
            if base.shape[:2] != (H, W):
                base = np.asarray(Image.fromarray(base).resize((W, H)))
        elif kind == "img":
            im = Image.open(os.path.join(rv.asset_dir(ASSET), f"{key}.png")).convert("RGB")
            z = 1.0 + 0.08 * t_in / dur
            w_, h_ = im.width / z, im.height / z
            base = np.asarray(im.resize((W, H), Image.LANCZOS, box=((im.width - w_) / 2, (im.height - h_) / 2,
                                                                     (im.width + w_) / 2, (im.height + h_) / 2)))
        elif kind == "b3d":
            s = b3d[key]
            base = _f3d(min(s["f1"], s["f0"] + int(t_in * F3D)))
        else:
            base = D2[key](min(1.0, t_in / dur))
        out = Image.fromarray(base).convert("RGBA")
        d = ImageDraw.Draw(out)
        if seg.get("label"):
            sz = 210 if seg.get("big") else 120
            pop = 0.85 + 0.15 * ms.ease(min(1.0, t_in / 0.2))
            lab = seg["label"]
            if lab in ("200,000 TONNES", "2,00,000 TON"):             # counter climbs with the pile
                n = int(200000 * ms.ease(min(1.0, t_in / (dur * 0.8))))
                if LANG == "en":
                    lab = f"{n:,} TONNES"
                else:                                                # Indian grouping: 2,00,000
                    s_ = str(n)
                    lab = (f"{s_[:-5]},{s_[-5:-3]},{s_[-3:]}" if n >= 100000 else f"{n:,}") + " TON"
            d.text((W / 2, 300), lab, font=font(int(sz * pop)), fill=GOLD, anchor="mm", stroke_width=10, stroke_fill=DARK)
            if i == 0:
                d.text((W / 2, 300 + 170), "NO MACHINES." if LANG == "en" else "KOI MACHINE NAHI.", font=font(120), fill=WHITE, anchor="mm", stroke_width=9,
                       stroke_fill=DARK)
        if i == 6 and 0.35 * dur < t_in < 0.35 * dur + 0.5:            # red flash on the wrong cut
            out.alpha_composite(Image.new("RGBA", (W, H), (220, 20, 20, 90)))
        if seg.get("cta"):
            out.alpha_composite(cta_layer(seg["cta"], t_in, dur))
            d = ImageDraw.Draw(out)
        caption(d, seg["line"], t_in, dur)
        d.text((40, 40), "FramedFacts · HOW DID THEY BUILD IT?" if LANG == "en" else "FramedFacts · YE KAISE BANA?",
               font=ImageFont.truetype(os.path.join(HERE, "fonts", "BebasNeue-Regular.ttf"), 40), fill=(255, 255, 255, 170))
        return np.asarray(out.convert("RGB"))
    return frame


def sound_events(starts, total):
    import sfx
    ev = [(0.0, sfx.deep_boom(0.6)), (starts[1], sfx.thump(0.5)), (starts[1] + 0.6, sfx.thump(0.45)),
          (starts[4], sfx.whoosh(0.5, 0.35)), (starts[5], sfx.riser(1.0, 0.3)),
          (starts[6] + 0.35 * (starts[7] - starts[6]), sfx.crack(0.7)), (starts[7], sfx.deep_boom(0.5)),
          (starts[13], sfx.whoosh(0.6, 0.35))]
    return ev


def step_build():
    T = json.load(open(TIMING)) if os.path.exists(TIMING) else {"b3d": []}     # no 3D shots left: timing is optional
    out, vo = ms.render_short(SCRIPT, SEGMENTS, VID, frame_fn(T), voice=VOICE, speed=SPEED, music_style="analytical",
                              sfx_fn=sound_events, music_vol=0.09, hook_hit=False, gap_s=0.22)
    print(out)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "voice":
        step_voice()
    elif cmd == "ai":
        print(gen_ai())
    elif cmd == "stills":
        T = json.load(open(TIMING))
        step_3d(["still"] + [str((s["f0"] + s["f1"]) // 2) for s in T["b3d"]])
    elif cmd == "frames":
        T = json.load(open(TIMING))
        step_3d(["0", str(T["b3d_frames"] - 1)])
    elif cmd == "build":
        step_build()
    else:
        print(__doc__)


# ── publishing (owner, 2026-11-19: "post the reel today") ────────────────────
SOURCES = ("Sources: Guinness World Records, 'Largest monolithic building'; Wikipedia, 'Kailasa Temple, Ellora'; "
           "Indian Culture portal (Govt. of India), 'Kailasa: majestic temple of Ellora'; Live History India, "
           "'Ellora's Kailasa Temple: Built from the Top'; Artnet News, 'The ancient temple carved out of a single rock'.")
DESC = {
    "en": ("The Kailasa Temple at Ellora (Cave 16, Maharashtra, India) was carved by hand from ONE rock, from the top "
           "down, starting in the 8th century under the Rashtrakuta king Krishna I. Up to 200,000 tonnes of rock were "
           "removed, and it is still the largest monolithic rock-cut temple in the world.\n\n"
           "Could we carve this today, even with machines? Yes or no in the comments.\n"
           "Series: How Did They Build It Without Machines? Next: the Iron Pillar of Delhi.\n\n"
           "Visuals: AI-generated illustrations (Google Gemini and Veo).\n" + SOURCES +
           "\n\n#kailasatemple #ellora #ancientindia #history #shorts"),
    "hi": ("Ellora ka Kailasa Temple (Cave 16, Maharashtra) ek hi rock se haath se taraasha gaya, top se neeche, 8vi "
           "sadi mein Rashtrakuta raja Krishna I ke time. Lagbhag 2 lakh ton tak rock hataya gaya, aur ye aaj bhi "
           "duniya ka sabse bada ek-chattani (monolithic) temple hai.\n\n"
           "Kya aaj machines ke saath bhi hum aisa bana sakte hain? Comment karo: haan ya na.\n"
           "Series: Ye Kaise Bana? Next: Delhi ka Iron Pillar.\n\n"
           "Visuals: AI-generated illustrations (Google Gemini aur Veo).\n" + SOURCES +
           "\n\n#kailasatemple #ellora #ancientindia #hindi #shorts"),
}
TAGS = ["kailasa temple", "kailash temple", "ellora", "ellora caves", "ancient india", "ancient engineering",
        "rock cut temple", "monolithic temple", "indian history", "how was it built", "shorts"]
PIN = {"en": "Could we build this today, even with machines? 🛕 Yes or no? And which ancient wonder should we explain next?",
       "hi": "Kya aaj machines ke saath bhi aisa ban sakta hai? 🛕 Haan ya na? Aur next kaunsa ancient wonder explain karein?"}
WHEN = {"en": "2026-11-19T13:00:00Z", "hi": "2026-11-19T15:00:00Z"}      # 6:30 PM and 8:30 PM IST


def publish():
    import phase5_upload as p5
    import pro_shorts_creator as psc
    out = os.path.join(config.VIDEOS_DIR, f"{VID}.mp4")
    vo = os.path.join(config.AUDIO_DIR, f"{VID}_vo.wav")
    script = dict(SCRIPT, video_title=SCRIPT["title"], seo_description=DESC[LANG], tags=TAGS, publish_at=WHEN[LANG],
                  category_id="27")
    config.UPLOAD_PRIVACY = "private"
    url, _ = p5.upload_to_youtube(out, script, {"title": SCRIPT["title"], "subject": SCRIPT["hook"], "category": "Education"})
    vid = url.rsplit("=", 1)[-1]
    thumb = os.path.join(THUMBS, "kailasa_A.jpg" if LANG == "en" else "kailasa_A_hi.jpg")
    p5.upload_thumbnail(vid, thumb)
    srt = os.path.splitext(vo)[0] + ".srt"
    psc.generate_srt(psc.get_word_timestamps(vo), srt)
    p5.upload_captions(vid, srt, language="en" if LANG == "en" else "hi", name="English" if LANG == "en" else "Hinglish")
    rec = os.path.join(HERE, "output", "build_series", "published.json")
    d = json.load(open(rec)) if os.path.exists(rec) else {}
    d[VID] = dict(id=vid, publishAt=WHEN[LANG], title=SCRIPT["title"], pin=PIN[LANG])
    json.dump(d, open(rec, "w"), indent=1, ensure_ascii=False)
    return vid


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "publish":
    print(publish())
