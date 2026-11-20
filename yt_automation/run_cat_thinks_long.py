"""
run_cat_thinks_long.py — LONG-FORM (~5.5 min, 16:9): "What Does Your Cat
Really Think You Are?" FramedFacts' first long video (2026-11-02).

Why: notes/2026-11-02_quark_case_study.md -- long-form animal-psychology
explainers with simple cartoon visuals that change every ~2 s earn ~50x more
per view than Shorts, and one ~100K-view video covers the 4,000-hour YPP
rule. topic_validate.py --long: cat psychology has 8 long videos over 100K in
the last year ("How Cats See Humans" 314K, "Your Cat Doesn't Think You're
Feeding Them" 237K). Our angle (what cats think we ARE) differs from Quark's
"Do Cats Actually Love Humans?".

FACTS (checked 2026-11-02, 2+ sources each):
  - Bradshaw (Cat Sense, 2013): cats treat people much like other cats, a
    "larger, non-hostile cat" (TIME, Apartment Therapy, Bustle coverage)
  - tail-up = friendly greeting between cats; kneading = kitten nursing
    behaviour; cheek rubbing (TIME/Bustle/Apartment Therapy; Hill's)
  - adult cats rarely meow at each other; adult meowing at people is an
    extension of kitten meowing (Wikipedia "Meow" citing Bradshaw 2016,
    J. Vet. Behavior; Kinship)
  - Saito & Shinozuka 2013 (Animal Cognition): cats tell owner's voice from
    strangers'; Saito et al. 2019 (Scientific Reports): cats discriminate
    their own names from similar words (EurekAlert, National Geographic)
  - Vitale, Behnke & Udell 2019 (Current Biology, Oregon State): 2-min
    strange-situation test; ~64% kittens / ~66% adults securely attached,
    ~65% in human infants; some experts dispute the interpretation (NBC,
    Science News, PBS NOVA, Guardian)
  - Humphrey et al. 2020 (Scientific Reports, Sussex/Portsmouth): cats
    slow-blink back to owners; approach strangers more after a slow blink
  - prey "gifts": no good evidence for the teaching idea -> said honestly
Stylized cartoon (our own art, cartoon_kit.py) -> no altered-content label.

  python run_cat_thinks_long.py preview   # contact sheet of every shot
  python run_cat_thinks_long.py build     # voice + frames + mix -> mp4 + thumbnail
"""
import os
import sys

from PIL import Image

import config

config.assert_safe_pipeline()

import cartoon_kit as ck
import cartoon_video as cv
import thumb_kit as tk
import motion_shorts as ms

VIDEO_ID = "cat_thinks_long"
HERE = os.path.dirname(os.path.abspath(__file__))
THUMB = os.path.join(HERE, "output", "thumbnails", f"{VIDEO_ID}.jpg")
Y = (255, 214, 70)
GREY = (172, 172, 178)
BLUE_SHIRT, GREEN_SHIRT, PINK_SHIRT = (70, 130, 220), (90, 170, 110), (220, 90, 110)


from cartoon_video import cat, hum, mouse, shot, T  # noqa: E402  (shared shot DSL)

SEGMENTS = [
    # ── intro ──
    {"chapter": "Intro", "line": "Your cat follows you everywhere.",
     "shots": [shot("living", [cat("walk", 640, 1010, 0.75, tail="up"), hum("stand", 1350, 1000)], move={0: (220, 0)})]},
    {"line": "It watches you cook, sits on your laptop, and stares at you at three in the morning.",
     "shots": [shot("living", [hum("stand", 1100, 1000), cat("sit", 760, 1010, 0.7, look=(1, -1))], [("bowl", 1450, 1010)]),
               shot("plain_blue", [cat("sit", 960, 900, 0.8, look=(0, 1))], [("laptop", 960, 1000, 520)]),
               shot("night", [cat("sit", 1300, 1010, 0.85)], zoom=(1.0, 1.12, 0.62, 0.55))]},
    {"line": "But have you ever wondered what your cat actually thinks you are?",
     "shots": [shot("plain_yellow", [cat("sit", 1300, 1010, 1.0, look=(-1, -1))],
                    [("bubble", 640, 430, 560, 460, None, 0, (1, 1), True), ("q", 820, 300, 200)],
                    late=[hum("stand", 600, 620, 0.42)])]},
    {"line": "Its owner? Its servant? Or just a giant, clumsy machine that makes food appear?",
     "shots": [shot("plain_blue", [hum("stand", 960, 1000)], [T("OWNER?")]),
               shot("plain_green", [hum("stand", 860, 1000), cat("sit", 1250, 1010, 0.6)], [("bowl", 1080, 1010), T("SERVANT?")]),
               shot("plain_pink", [hum("arms_open", 960, 1000), cat("sit", 1350, 1010, 0.6, mouth="open")],
                    [("bowl", 700, 1010), ("bowl", 1180, 1010), T("FOOD MACHINE?")])]},
    {"line": "Scientists have actually studied this.",
     "shots": [shot("lab", [hum("point", 520, 1000, 0.9, shirt=(90, 90, 160), coat=True, glasses=True),
                            cat("sit", 980, 1010, 0.6)])]},
    {"line": "And the answer is stranger, and sweeter, than you'd think.",
     "shots": [shot("plain_pink", [cat("sit", 960, 1000, 1.0, eyes="closed")],
                    [("heart", 700, 380, 110), ("heart", 1220, 330, 90), ("heart", 1300, 560, 70)])]},
    # ── big cat ──
    {"chapter": "You're a big cat", "line": "Let's start with the big idea.",
     "shots": [shot("plain_purple", [cat("sit", 1450, 1010, 0.7)], [T("THE BIG IDEA", 860, 480, 220)])]},
    {"line": "John Bradshaw is a scientist who has studied cats for decades.", "say": "John Brad-shaw is a scientist who has studied cats for decades.",
     "shots": [shot("lab", [hum("stand", 560, 1000, 0.9, shirt=(90, 90, 160), coat=True, glasses=True),
                            cat("sit", 1000, 1010, 0.6, look=(-1, -1))], [T("CAT EXPERT")])]},
    {"line": "In his book, Cat Sense, he argues that cats don't really treat us as a different kind of animal.",
     "shots": [shot("plain_green", [cat("sit", 1350, 1010, 0.8)], [("book", 680, 540, "CAT SENSE")]),
               shot("plain_blue", [hum("stand", 700, 1000), cat("sit", 1250, 1010, 0.8)], [("q", 960, 360, 200)])]},
    {"line": "They treat us a lot like other cats.",
     "shots": [shot("living", [cat("sit", 700, 1010, 0.7), cat("sit", 1000, 1010, 0.7, color=GREY), hum("stand", 1450, 1000)],
                    [("text", 1050, 420, "=", 220, Y)])]},
    {"line": "Just bigger, clumsier, and luckily, not dangerous.",
     "shots": [shot("plain_yellow", [hum("stand", 820, 1040, 1.15), cat("sit", 1350, 1010, 0.5, look=(-1, -1))],
                    [("text", 1350, 260, "BIGGER", 110, (255, 255, 255))]),
               shot("plain_yellow", [hum("arms_open", 820, 1040, 1.15, mouth="open"), cat("sit", 1350, 1010, 0.5)],
                    [("text", 1350, 260, "CLUMSIER", 110, (255, 255, 255)), ("mark", 1350, 520, 160, True)])]},
    {"line": "Basically, a large, friendly cat.",
     "shots": [shot("plain_pink", [cat("sit", 1350, 1010, 0.9, look=(-1, -1))],
                    [("bubble", 640, 440, 600, 520, None, 0, (1, 1), True)],
                    late=[hum("stand", 640, 650, 0.48), ("ears", 640, 352, 40)])]},
    {"line": "And you can see it in how your cat greets you.",
     "shots": [shot("doorstep", [hum("wave", 960, 860, 0.75), cat("walk", 520, 1010, 0.7, tail="up")], move={1: (150, 0)})]},
    # ── tail up ──
    {"chapter": "Tail up: the cat hello", "line": "When two friendly cats meet, one often lifts its tail straight up, like a little flag.",
     "shots": [shot("living", [cat("walk", 560, 1010, 0.75, tail="up"), cat("walk", 1360, 1010, 0.75, tail="down", color=GREY, flip=True)],
                    move={0: (120, 0), 1: (-120, 0)}),
               shot("living", [cat("walk", 700, 1010, 0.9, tail="up")], [T("TAIL UP")], zoom=(1.0, 1.15, 0.33, 0.6))]},
    {"line": "It's a cat's way of saying, hi, I'm friendly.",
     "shots": [shot("plain_green", [cat("walk", 760, 1010, 0.95, tail="up")], [("bubble", 1350, 400, 560, 180, "HI! I'M FRIENDLY", 64, (-1, 1))])]},
    {"line": "Now watch your cat the next time you come home.",
     "shots": [shot("doorstep", [hum("wave", 960, 860, 0.75), cat("sit", 1350, 1010, 0.7, look=(-1, -1))])]},
    {"line": "That tail goes straight up.",
     "shots": [shot("living", [cat("walk", 500, 1010, 0.85, tail="up"), hum("stand", 1350, 1000)], move={0: (300, 0)},
                    zoom=(1.0, 1.2, 0.3, 0.6))]},
    {"line": "You just got the same hello a cat gives its friends.",
     "shots": [shot("living", [cat("walk", 860, 1010, 0.8, tail="up"), hum("stand", 1300, 1000)],
                    [("heart", 1080, 420, 110), T("SAME HELLO")])]},
    # ── rubbing ──
    {"chapter": "Rubbing: you smell like family", "line": "Then comes the rubbing.",
     "shots": [shot("plain_purple", [cat("rub", 960, 1010, 1.0)], [T("THE RUB", 960, 140, 160)])]},
    {"line": "Your cat pushes its head against your legs and winds around you.",
     "shots": [shot("living", [hum("stand", 1100, 1000), cat("rub", 860, 1010, 0.7)]),
               shot("living", [hum("stand", 900, 1000), cat("rub", 1150, 1010, 0.7, flip=True)], zoom=(1.0, 1.15, 0.5, 0.75))]},
    {"line": "Friendly cats do the same thing to each other.",
     "shots": [shot("plain_green", [cat("rub", 720, 1010, 0.85), cat("rub", 1200, 1010, 0.85, color=GREY, flip=True)],
                    [("heart", 960, 400, 90)])]},
    {"line": "Cats have scent glands on their cheeks, so every rub leaves a little of their smell on you.",
     "shots": [shot("plain_blue", [cat("sit", 960, 1050, 1.3)], [T("SCENT GLANDS"), ("scent", 420, 640, 260), ("scent", 1240, 640, 260, (120, 190, 110), 1.5)],
                    zoom=(1.0, 1.1, 0.5, 0.45)),
               shot("living", [hum("stand", 1100, 1000), cat("rub", 860, 1010, 0.7)],
                    [("scent", 1000, 700, 240), ("scent", 1020, 820, 220, (120, 190, 110), 1.2)])]},
    {"line": "In cat terms, you're being marked as part of the family.",
     "shots": [shot("plain_pink", [hum("stand", 960, 1000), cat("sit", 1360, 1010, 0.6), cat("sit", 560, 1010, 0.6, color=GREY)],
                    [("scent", 760, 560, 400), ("heart", 960, 230, 100), T("FAMILY", 960, 110, 120)])]},
    # ── kneading ──
    {"chapter": "Kneading: you're like mom", "line": "Sometimes your cat climbs onto your lap and starts pushing its paws up and down, like it's kneading dough.",
     "shots": [shot("living", [hum("sit", 1490, 880, 0.9, shirt=PINK_SHIRT), cat("knead", 1490, 960, 0.55)]),
               shot("living", [hum("sit", 1490, 880, 0.9, shirt=PINK_SHIRT), cat("knead", 1490, 960, 0.55, eyes="closed")],
                    zoom=(1.1, 1.35, 0.78, 0.72))]},
    {"line": "Kittens do this to their mother's belly when they nurse, to get the milk flowing.",
     "shots": [shot("plain_yellow", [cat("lie", 960, 960, 1.35, color=GREY, eyes="closed"),
                                     cat("knead", 780, 1075, 0.42, kitten=True), cat("knead", 960, 1080, 0.42, kitten=True, color=GREY)],
                    [("drops", 870, 760), T("KITTENS KNEAD MOM")])]},
    {"line": "Many cats keep doing it as adults, especially when they feel safe and happy.",
     "shots": [shot("plain_pink", [cat("knead", 960, 1010, 1.0, eyes="closed")], [("heart", 650, 380, 100), ("heart", 1290, 330, 80)])]},
    {"line": "So when your cat kneads you, it may be treating you a little bit like its mother.",
     "shots": [shot("living", [hum("sit", 1490, 880, 0.9, shirt=PINK_SHIRT), cat("knead", 1490, 960, 0.55, eyes="closed")],
                    [T("YOU = MOM?", 760, 300, 160)])]},
    # ── meowing ──
    {"chapter": "Meowing is just for you", "line": "Here's something that surprises most people.",
     "shots": [shot("plain_purple", [cat("sit", 960, 1010, 0.9, mouth="open")], [T("!", 960, 250, 260)])]},
    {"line": "Adult cats hardly ever meow at each other.",
     "shots": [shot("living", [cat("sit", 700, 1010, 0.75), cat("sit", 1200, 1010, 0.75, color=GREY)],
                    [("bubble", 640, 380, 220, 140, "...", 80, (1, 1)), ("bubble", 1270, 380, 220, 140, "...", 80, (-1, 1)),
                     T("NO MEOWS", 960, 140, 130)])]},
    {"line": "Kittens meow to get their mother's attention.",
     "shots": [shot("plain_green", [cat("lie", 760, 1000, 1.0, color=GREY), cat("sit", 1300, 1060, 0.45, kitten=True, mouth="open")],
                    [("bubble", 1420, 560, 260, 130, "MEW!", 64, (-1, 1))])]},
    {"line": "But grown up cats mostly save their meows for one special audience.",
     "shots": [shot("plain_blue", [cat("sit", 960, 1010, 0.95)], [("q", 1350, 420, 220)])]},
    {"line": "Us.",
     "shots": [shot("plain_yellow", [hum("wave", 960, 1040, 1.1)], [T("US!", 960, 160, 220, (255, 255, 255))])]},
    {"line": "Scientists think cats kept this kitten habit because it works so well on humans.",
     "shots": [shot("living", [hum("stand", 1250, 1000), cat("sit", 800, 1010, 0.7, mouth="open", look=(1, -1))],
                    [("bubble", 680, 520, 250, 130, "MEOW!", 64, (1, 1)), ("bowl", 1000, 1010)]),
               shot("living", [hum("arms_open", 1250, 1000, mouth="open"), cat("sit", 800, 1010, 0.7, eyes="closed")],
                    [("bowl", 1000, 1010), ("heart", 1000, 420, 90)])]},
    {"line": "So every meow you hear is a message made just for you.",
     "shots": [shot("night", [hum("sit", 520, 840, 0.8), cat("sit", 1150, 1010, 0.8, mouth="open")],
                    [("bubble", 1350, 560, 260, 130, "MEOW!", 64, (-1, 1)), ("waves", 1000, 700, 3, -1)])]},
    # ── voice & name ──
    {"chapter": "They know your voice", "line": "And your cat is listening more than you think.",
     "shots": [shot("plain_blue", [cat("sit", 1150, 1010, 1.0)], [("waves", 760, 520, 4, -1)], zoom=(1.0, 1.12, 0.6, 0.45))]},
    {"line": "In a 2013 study in Japan, cats heard recordings of people calling their names.",
     "say": "In a twenty thirteen study in Japan, cats heard recordings of people calling their names.",
     "shots": [shot("lab", [cat("sit", 1150, 1010, 0.7)], [("speaker", 760, 640, 220), T("JAPAN, 2013")])]},
    {"line": "They reacted more to their owner's voice than to a stranger's.",
     "shots": [shot("plain_green", [hum("call", 480, 1000, 0.8), hum("call", 1440, 1000, 0.8, shirt=(150, 150, 150)), cat("sit", 960, 1010, 0.6, look=(-1, 0))],
                    [("mark", 480, 220, 130, True), ("mark", 1440, 220, 130, False),
                     ("text", 480, 360, "OWNER", 80, Y), ("text", 1440, 360, "STRANGER", 80, Y)])]},
    {"line": "In 2019, the same team found that cats can pick out their own name from similar sounding words.",
     "say": "In twenty nineteen, the same team found that cats can pick out their own name from similar sounding words.",
     "shots": [shot("plain_purple", [cat("sit", 1350, 1010, 0.8)], [("speaker", 600, 600, 220), ("text", 960, 300, "MAT... BAT...", 110, (255, 255, 255))]),
               shot("plain_purple", [cat("sit", 1350, 1010, 0.8, look=(-1, 0))], [("speaker", 600, 600, 220), ("text", 960, 300, "MOCHI!", 140, Y),
                                                                                  ("mark", 1350, 420, 120, True)])]},
    {"line": "Even when they don't come when you call.",
     "shots": [shot("living", [hum("call", 1350, 1000), cat("lie", 650, 1010, 0.8, eyes="closed")],
                    [("bubble", 1680, 380, 280, 130, "MOCHI!", 64, (-1, 1))])]},
    {"line": "They hear you. They're just choosing not to answer.",
     "shots": [shot("living", [cat("lie", 650, 1010, 0.8, eyes="half")], [T("THEY HEARD YOU", 960, 140, 130)], zoom=(1.1, 1.35, 0.33, 0.78))]},
    # ── attachment ──
    {"chapter": "Do cats really love you?", "line": "But do cats actually care about us?",
     "shots": [shot("plain_pink", [cat("sit", 960, 1010, 0.95)], [("heart", 700, 400, 100), ("q", 1250, 380, 200)])]},
    {"line": "In 2019, researchers at Oregon State University tested cats with an experiment first used on human babies.",
     "say": "In twenty nineteen, researchers at Oregon State University tested cats with an experiment first used on human babies.",
     "shots": [shot("lab", [hum("point", 520, 1000, 0.9, shirt=(90, 90, 160), coat=True, glasses=True), cat("sit", 980, 1010, 0.6)],
                    [T("THE BABY TEST")])]},
    {"line": "A cat and its owner spend two minutes together in a strange room.",
     "shots": [shot("room", [hum("stand", 420, 1000, 0.85), cat("walk", 900, 1010, 0.6, tail="up")], [("clock", 960, 200, 80, 0, 10)],
                    move={1: (160, 0)})]},
    {"line": "Then the owner leaves, and the cat is alone for two minutes.",
     "shots": [shot("room", [cat("sit", 900, 1010, 0.6, look=(1, 0))], [("clock", 960, 200, 80, 0, 20), ("q", 1200, 520, 140)])]},
    {"line": "Then the owner comes back.",
     "shots": [shot("room", [hum("wave", 1580, 1000, 0.85), cat("sit", 900, 1010, 0.6, look=(1, -1))])]},
    {"line": "Most cats greeted their person, then calmly went back to exploring.",
     "shots": [shot("room", [hum("stand", 1350, 1000, 0.85), cat("walk", 950, 1010, 0.6, tail="up")], [("heart", 1150, 520, 80)],
                    move={1: (200, 0)}),
               shot("room", [hum("stand", 1350, 1000, 0.85), cat("walk", 900, 1010, 0.6, tail="up", flip=True)], move={1: (-260, 0)})]},
    {"line": "Scientists call that a secure attachment.",
     "shots": [shot("lab", [hum("point", 520, 1000, 0.9, shirt=(90, 90, 160), coat=True, glasses=True)],
                    [T("SECURE ATTACHMENT")])]},
    {"line": "About two out of three cats showed it, almost the same share as human babies.",
     "shots": [shot("plain_blue", [], [("ring", 620, 500, 200, 65, (243, 153, 66), "~65%"), ("ring", 1300, 500, 200, 65, (90, 170, 230), "~65%"),
                                       ("text", 620, 800, "CATS", 110, (255, 255, 255)), ("text", 1300, 800, "BABIES", 110, (255, 255, 255))])]},
    {"line": "Not every scientist agrees on what that means, but it's a strong hint that your cat sees you as its safe place.",
     "shots": [shot("plain_purple", [hum("stand", 700, 1000, 0.85, shirt=(90, 90, 160), coat=True, glasses=True),
                                     hum("stand", 1250, 1000, 0.85, shirt=(150, 150, 150), coat=True)], [("q", 960, 320, 180)]),
               shot("living", [hum("sit", 1490, 880, 0.9, shirt=PINK_SHIRT), cat("knead", 1490, 960, 0.55, eyes="closed")],
                    [("heart", 1490, 360, 110), T("SAFE PLACE", 700, 300, 150)])]},
    # ── slow blink ──
    {"chapter": "Say I love you in cat", "line": "There's even a way to tell your cat you love it, in its own language.",
     "shots": [shot("plain_yellow", [hum("stand", 620, 1000), cat("sit", 1300, 1010, 0.9)], [("heart", 960, 380, 100)])]},
    {"line": "In 2020, scientists at the University of Sussex studied the cat slow blink.",
     "say": "In twenty twenty, scientists at the University of Sussex studied the cat slow blink.",
     "shots": [shot("lab", [hum("stand", 520, 1000, 0.9, shirt=(90, 90, 160), coat=True, glasses=True), cat("sit", 1000, 1010, 0.7, eyes="closed")],
                    [T("SLOW BLINK")])]},
    {"line": "When owners narrowed their eyes and blinked slowly, their cats were more likely to blink slowly back.",
     "shots": [shot("plain_yellow", [hum("stand", 620, 1000, eyes="closed"), cat("sit", 1300, 1010, 0.9)], zoom=(1.0, 1.08, 0.35, 0.5)),
               shot("plain_yellow", [hum("stand", 620, 1000), cat("sit", 1300, 1010, 0.9, eyes="closed")], [("heart", 960, 380, 100)],
                    zoom=(1.0, 1.08, 0.68, 0.5))]},
    {"line": "And with strangers, cats were more likely to walk over after a slow blink.",
     "shots": [shot("room", [hum("point", 1400, 1000, 0.85, shirt=GREEN_SHIRT, eyes="closed"), cat("walk", 600, 1010, 0.6, tail="up")],
                    move={1: (420, 0)})]},
    {"line": "So try it tonight.",
     "shots": [shot("night", [hum("sit", 520, 840, 0.8), cat("sit", 1150, 1010, 0.8)], [T("TRY IT TONIGHT", 960, 120, 120)])]},
    {"line": "Look at your cat, soften your eyes, and blink, slowly.",
     "shots": [shot("plain_yellow", [hum("stand", 960, 1080, 1.4)], zoom=(1.2, 1.5, 0.5, 0.35)),
               shot("plain_yellow", [hum("stand", 960, 1080, 1.4, eyes="closed")], zoom=(1.5, 1.6, 0.5, 0.35)),
               shot("plain_pink", [cat("sit", 960, 1100, 1.5, eyes="closed")], [("heart", 1400, 300, 110)], zoom=(1.1, 1.3, 0.5, 0.4))]},
    # ── prey ──
    {"chapter": "The dead mouse mystery", "line": "And then, there's the gift nobody wants.",
     "shots": [shot("doorstep", [cat("sit", 560, 1010, 0.7, eyes="closed"), mouse(960, 850, 0.8)], [T("THE GIFT", 960, 80, 130)])]},
    {"line": "A dead mouse on the doorstep.",
     "shots": [shot("doorstep", [mouse(960, 850, 0.8)], zoom=(1.2, 1.6, 0.5, 0.78))]},
    {"line": "Is your cat feeding you? Is it teaching you to hunt, because you're terrible at it?",
     "shots": [shot("plain_green", [hum("stand", 700, 1000, mouth="open"), cat("sit", 1250, 1010, 0.7), mouse(960, 1010, 0.7)],
                    [T("FEEDING YOU?")]),
               shot("plain_green", [hum("arms_open", 700, 1000, mouth="open"), cat("sit", 1250, 1010, 0.7, eyes="half"), mouse(960, 1010, 0.7)],
                    [T("TEACHING YOU?")])]},
    {"line": "The honest answer is, scientists aren't sure.",
     "shots": [shot("lab", [hum("arms_open", 960, 1000, 0.9, shirt=(90, 90, 160), coat=True, glasses=True)],
                    [("q", 600, 360, 180), ("q", 1320, 330, 220)])]},
    {"line": "Mother cats do bring prey to their kittens.",
     "shots": [shot("plain_yellow", [cat("walk", 640, 1010, 0.8, color=GREY, tail="up"), mouse(860, 1010, 0.6),
                                     cat("sit", 1250, 1060, 0.4, kitten=True), cat("sit", 1420, 1060, 0.4, kitten=True, color=GREY)],
                    move={0: (120, 0), 1: (120, 0)})]},
    {"line": "But nobody has proven your cat is trying to teach you.",
     "shots": [shot("plain_purple", [cat("sit", 960, 1010, 0.9, look=(0, -1))], [T("NOT PROVEN", 960, 160, 160), ("mark", 1400, 500, 160, False)])]},
    {"line": "What do you think it means? Tell us in the comments.",
     "shots": [shot("plain_blue", [cat("sit", 1300, 1010, 0.8)], [("bubble", 700, 460, 640, 240, "COMMENT BELOW!", 80, (1, 1))])]},
    # ── conclusion ──
    {"chapter": "So what are you?", "line": "So, what does your cat really think you are?",
     "shots": [shot("plain_yellow", [cat("sit", 1300, 1010, 1.0, look=(-1, -1))],
                    [("bubble", 640, 430, 560, 460, None, 0, (1, 1), True), ("q", 820, 300, 200)],
                    late=[hum("stand", 600, 620, 0.42)])]},
    {"line": "Not a servant, and not a stranger.",
     "shots": [shot("plain_blue", [hum("stand", 600, 1000, 0.8), hum("stand", 1320, 1000, 0.8, shirt=(150, 150, 150))],
                    [("text", 600, 180, "SERVANT", 100, (255, 255, 255)), ("text", 1320, 180, "STRANGER", 100, (255, 255, 255)),
                     ("mark", 600, 420, 220, False), ("mark", 1320, 420, 220, False)])]},
    {"line": "Science suggests you're something like a big, friendly cat.",
     "shots": [shot("plain_pink", [cat("sit", 1350, 1010, 0.9, eyes="closed")],
                    [("bubble", 640, 440, 600, 520, None, 0, (1, 1), True)],
                    late=[hum("stand", 640, 650, 0.48), ("ears", 640, 352, 40)])]},
    {"line": "A family member it greets with its tail up, marks with its scent, kneads like a mother, and talks to with meows it saves just for you.",
     "shots": [shot("living", [cat("walk", 760, 1010, 0.8, tail="up"), hum("stand", 1300, 1000)], [T("TAIL UP")]),
               shot("living", [hum("stand", 1100, 1000), cat("rub", 860, 1010, 0.7)], [("scent", 1000, 700, 240), T("SCENT")]),
               shot("living", [hum("sit", 1490, 880, 0.9, shirt=PINK_SHIRT), cat("knead", 1490, 960, 0.55, eyes="closed")], [T("KNEADING", 760, 300)]),
               shot("night", [hum("sit", 520, 840, 0.8), cat("sit", 1150, 1010, 0.8, mouth="open")],
                    [("bubble", 1350, 560, 260, 130, "MEOW!", 64, (-1, 1)), T("MEOWS", 960, 120)])]},
    {"line": "Not bad for an animal people call cold and distant.",
     "shots": [shot("living", [hum("sit", 1490, 880, 0.9, shirt=PINK_SHIRT), cat("knead", 1490, 960, 0.55, eyes="closed")],
                    [("heart", 1300, 380, 90), ("heart", 1680, 330, 80)])]},
    {"line": "If you learned something new about your cat, subscribe to FramedFacts.",
     "say": "If you learned something new about your cat, subscribe to Framed Facts.",
     "shots": [shot("plain_yellow", [cat("sit", 1350, 1010, 0.9, eyes="closed")], [("sub", 700, 540)])]},
    {"line": "Next time, we'll find out what your dog really thinks of you.",
     "shots": [shot("plain_blue", [cat("sit", 1400, 1010, 0.8, look=(-1, 0))], [T("NEXT: YOUR DOG", 760, 460, 170), ("q", 760, 680, 200)])]},
]

SCRIPT = {
    "format": "long",
    "hook": SEGMENTS[0]["line"] + " " + SEGMENTS[1]["line"],
    "body": " ".join(s["line"] for s in SEGMENTS[2:-2]),
    "cta": "What do you think the dead mouse means? Comment below and subscribe.",
    "title": "Your Cat Probably Thinks You're a Giant, Clumsy Cat",
    "category_id": "15",
    "tags": ["cat psychology", "what do cats think of humans", "cat behavior", "do cats love their owners", "cat slow blink",
             "why cats knead", "why cats meow", "cat facts", "cats", "animal psychology", "pets"],
    "ai_generated_visuals": False,
    "topic_category": "Animals",
    "thumbnail_path": THUMB,
}

SOURCES = (
    "Sources:\n"
    "- Bradshaw, J. (2013) Cat Sense; Bradshaw (2016) Sociality in cats, Journal of Veterinary Behavior\n"
    "- Saito & Shinozuka (2013) Vocal recognition of owners by domestic cats, Animal Cognition\n"
    "- Saito et al. (2019) Domestic cats discriminate their names from other words, Scientific Reports\n"
    "- Vitale, Behnke & Udell (2019) Attachment bonds between domestic cats and humans, Current Biology\n"
    "- Humphrey et al. (2020) The role of cat eye narrowing movements in cat-human communication, Scientific Reports"
)


# ── rendering (shared engine: cartoon_video.py) ──────────────────────────────
render_shot = cv.render_shot
frame = cv.frame_fn(SEGMENTS, VIDEO_ID)
sound_events = cv.section_sounds(SEGMENTS)


def make_thumbnail(path=THUMB):
    """Reaction thumbnail (thumb_kit): judging cat vs shocked owner wearing cat ears."""
    c = tk.burst((70, 190, 255), (10, 30, 120), cx=0.3, cy=0.6)
    lay, d = tk.layer()
    tk.cat_head(d, 520, 660, 390, "judge", look=(1, 0))
    tk.stick(c, lay)
    lay, d = tk.layer()
    tk.human_head(d, 1460, 700, 270, ears="cat")
    tk.shock_lines(d, 1460, 670, 380, n=5, a0=-25, a1=35)
    tk.stick(c, lay)
    tk.headline(c, [("YOU'RE A", 120, tk.WHITE), ("CAT?!", 230, tk.YELLOW)], 1020, 210, rotate=-4)
    return tk.save(c, path)


def chapters_text(starts):
    return cv.chapters_text(SEGMENTS, starts)


def build():
    make_thumbnail()
    out, vo = ms.render_short(SCRIPT, SEGMENTS, VIDEO_ID, frame, speed=1.05, music_style="emotional",
                              sfx_fn=sound_events, music_vol=0.05)
    return out, vo


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "preview"
    if cmd == "preview":
        p = sys.argv[2] if len(sys.argv) > 2 else "cat_preview.jpg"
        n = cv.preview(SEGMENTS, p)
        make_thumbnail()
        print(n, "shots ->", p, "| thumbnail ->", THUMB)
    elif cmd == "build":
        print(build())
