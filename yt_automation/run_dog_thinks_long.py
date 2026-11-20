"""
run_dog_thinks_long.py — LONG-FORM (~6 min, 16:9): "What Does Your Dog Really
Think You Are?" FramedFacts' second long video (2026-11-02), promised at the
end of the cat video (iROMkiiM8aE).

Demand (topic_validate --long, 2026-11-02): "Your Dog Doesn't See You as
Human - Here's What You Really Are to Them" 3.6M and 432K (two channels),
11 long videos over 100K in the last year.

FACTS (checked 2026-11-02, 2+ sources each; caveats kept in the script):
  - alpha myth: "alpha" came from captive, unrelated wolves; wild packs are
    families (Mech 1999, Can. J. Zoology; Turpentine Creek, A-Z Animals,
    Gizmodo coverage)
  - Nagasawa et al. 2015 (Science): dog-owner mutual gaze raised owners'
    oxytocin, then the dogs'; not in hand-raised wolves; disputed by some
    (National Geographic, TIME, Frontiers commentary)
  - Kaminski et al. 2019 (PNAS): dogs have the inner-eyebrow raiser muscle
    (LAOM), wolves only a trace; dogs use it more; selection by human
    preference is the authors' hypothesis (sci.news, PubMed)
  - Berns et al. 2015 (Behavioural Processes): awake, unrestrained dogs in
    fMRI; caudate responded most to a familiar human's scent (ScienceDaily,
    National Geographic)
  - Andics et al. 2016 (Science): word meaning mostly left hemisphere,
    intonation right; reward response only when praise words AND praising
    tone matched (Nature news, sci.news, CS Monitor)
  - Topal et al. 1998: adult dogs show attachment to owners analogous to
    child-parent (strange situation adapted to dogs) (Family Dog Project,
    PMC review)
  - Miklosi et al. 2003: dogs look back at humans in an unsolvable task,
    hand-raised wolves don't (Family Dog Project, Animal Cognition papers)
Stylized cartoon (our own art) -> no altered-content label.

  python run_dog_thinks_long.py preview [path]
  python run_dog_thinks_long.py build
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
from cartoon_video import cat, dog, hum, shot, T  # noqa: E402

VIDEO_ID = "dog_thinks_long"
HERE = os.path.dirname(os.path.abspath(__file__))
THUMB = os.path.join(HERE, "output", "thumbnails", f"{VIDEO_ID}.jpg")
CAT_VIDEO = "https://youtu.be/iROMkiiM8aE"
W_ = (255, 255, 255)
GREY = ck.WOLF_GREY
BROWN = (130, 90, 62)
SCI = dict(shirt=(90, 90, 160), coat=True, glasses=True)
PINK_SHIRT = (220, 90, 110)


def wolf(pose="sit", x=960, y=1000, s=0.8, flip=False, **kw):
    return dog(pose, x, y, s, flip, color=GREY, ear="pointy", mouth=kw.pop("mouth", "smile"), **kw)


SEGMENTS = [
    # ── intro ──
    {"chapter": "Intro", "line": "Your dog greets you like you've been gone for years, even if you just took out the trash.",
     "shots": [shot("doorstep", [hum("wave", 960, 860, 0.75), dog("walk", 420, 1010, 0.75, tail="wag")], move={1: (260, 0)}),
               shot("plain_yellow", [dog("sit", 960, 1010, 1.0, tail="wag")], [("heart", 650, 380, 100), ("heart", 1280, 330, 90)])]},
    {"line": "It follows you from room to room. It watches every bite you eat.",
     "shots": [shot("living", [hum("stand", 1250, 1000), dog("walk", 760, 1010, 0.7, tail="wag")], move={0: (160, 0), 1: (160, 0)}),
               shot("living", [hum("sit", 1490, 880, 0.9, shirt=PINK_SHIRT), dog("sit", 1100, 1010, 0.7, eyes="puppy", mouth="smile", look=(1, -1))],
                    [("bowl", 1320, 830)])]},
    {"line": "So what does your dog actually think you are?",
     "shots": [shot("plain_blue", [dog("sit", 1300, 1010, 1.0, look=(-1, -1))],
                    [("bubble", 640, 430, 560, 460, None, 0, (1, 1), True), ("q", 820, 300, 200)], late=[hum("stand", 600, 620, 0.42)])]},
    {"line": "Its owner? Its pack leader? Its best friend?",
     "shots": [shot("plain_green", [hum("stand", 820, 1000), dog("sit", 1250, 1010, 0.65)], [T("OWNER?")]),
               shot("plain_purple", [hum("point", 820, 1000), dog("sit", 1250, 1010, 0.65, eyes="puppy", mouth="smile")], [T("PACK LEADER?")]),
               shot("plain_pink", [hum("arms_open", 820, 1000), dog("sit", 1250, 1010, 0.65, tail="wag")], [T("BEST FRIEND?")])]},
    {"line": "Scientists have scanned dog brains, measured their hormones, and even tested them like human babies.",
     "shots": [shot("lab", [], [("scanner", 1200, 560, 280), T("BRAIN SCANS")], late=[dog("lie", 1000, 680, 0.42, eyes="closed")]),
               shot("lab", [hum("point", 520, 1000, 0.9, **SCI), dog("sit", 1000, 1010, 0.6)], [("pill", 1450, 560, "HORMONES"), T("HORMONES")]),
               shot("room", [hum("stand", 450, 1000, 0.85), dog("sit", 900, 1010, 0.6)], [T("THE BABY TEST")])]},
    {"line": "And the answer is pretty heartwarming.",
     "shots": [shot("plain_pink", [dog("sit", 960, 1010, 1.0, eyes="closed", tail="wag")], [("heart", 660, 380, 110), ("heart", 1260, 340, 90)])]},
    # ── alpha myth ──
    {"chapter": "The alpha myth", "line": "Let's start with a myth.",
     "shots": [shot("plain_purple", [wolf("sit", 1450, 1010, 0.7)], [T("THE ALPHA MYTH", 860, 480, 200)])]},
    {"line": "For years, people said your dog sees you as its pack leader, the alpha, and wants to take your place.",
     "shots": [shot("living", [hum("point", 1250, 1000), dog("sit", 760, 1010, 0.75, mouth="smile", look=(1, -1))], [T("THE ALPHA?")]),
               shot("plain_yellow", [dog("sit", 1250, 1010, 0.8, look=(-1, -1))],
                    [("bubble", 640, 430, 560, 460, "BOSS?", 110, (1, 1), True)])]},
    {"line": "That idea came from studies of wolves in captivity.",
     "shots": [shot("enclosure", [wolf("sit", 640, 1010, 0.6), wolf("walk", 1250, 1010, 0.6, flip=True)], [T("CAPTIVE WOLVES")])]},
    {"line": "Unrelated adult wolves, put together in an enclosure, competing for rank.",
     "shots": [shot("enclosure", [wolf("walk", 700, 1010, 0.65, mouth="open"), wolf("walk", 1220, 1010, 0.65, mouth="open", flip=True)],
                    [("text", 960, 560, "VS", 160, (230, 70, 70))], move={0: (90, 0), 1: (-90, 0)})]},
    {"line": "But when wolf scientist David Mech studied wolves in the wild, he found something very different.",
     "say": "But when wolf scientist David Meech studied wolves in the wild, he found something very different.",
     "shots": [shot("forest", [hum("stand", 450, 1000, 0.8, **SCI), wolf("sit", 1300, 1010, 0.6)], [T("WILD WOLVES")])]},
    {"line": "A wild wolf pack is usually just a family. Two parents, and their pups.",
     "shots": [shot("forest", [wolf("sit", 640, 1010, 0.8), wolf("sit", 1280, 1010, 0.8, look=(-1, 0)),
                               wolf("sit", 880, 1060, 0.38, puppy=True), wolf("sit", 1040, 1060, 0.38, puppy=True)],
                    [("heart", 960, 520, 90), T("A FAMILY")])]},
    {"line": "The parents lead because they're the parents, not because they won a fight.",
     "shots": [shot("forest", [wolf("walk", 700, 1010, 0.75, tail="up"), wolf("walk", 1050, 1060, 0.4, puppy=True), wolf("walk", 1250, 1060, 0.4, puppy=True)],
                    move={0: (180, 0), 1: (180, 0), 2: (180, 0)})]},
    {"line": "Young wolves don't overthrow their parents. They grow up, leave, and start families of their own.",
     "shots": [shot("forest", [wolf("walk", 700, 1010, 0.6, tail="up"), wolf("walk", 1200, 1010, 0.6, flip=True, tail="up")],
                    [("heart", 960, 560, 80)], move={0: (-200, 0), 1: (200, 0)})]},
    {"line": "Mech has spent years asking people to stop using the alpha idea.",
     "say": "Meech has spent years asking people to stop using the alpha idea.",
     "shots": [shot("plain_blue", [hum("arms_open", 960, 1000, 0.9, **SCI)], [("text", 960, 300, "ALPHA", 150, W_), ("mark", 960, 300, 220, False)])]},
    {"line": "So your dog isn't secretly plotting to become the boss of the house.",
     "shots": [shot("living", [dog("lie", 900, 1010, 0.8, eyes="closed", mouth="smile")], [T("NOT PLOTTING")], zoom=(1.0, 1.15, 0.47, 0.75))]},
    # ── oxytocin ──
    {"chapter": "The love stare", "line": "Have you ever caught your dog just looking at you?",
     "shots": [shot("living", [hum("sit", 1490, 880, 0.9, shirt=PINK_SHIRT), dog("sit", 1050, 1010, 0.75, look=(1, -1))], zoom=(1.0, 1.15, 0.65, 0.6))]},
    {"line": "In 2015, scientists in Japan measured oxytocin, a bonding hormone that also rises between mothers and babies.",
     "say": "In twenty fifteen, scientists in Japan measured oxytocin, a bonding hormone that also rises between mothers and babies.",
     "shots": [shot("lab", [hum("point", 520, 1000, 0.9, **SCI)], [("pill", 1350, 400, "OXYTOCIN"), T("JAPAN, 2015")]),
               shot("plain_pink", [hum("stand", 700, 1000), dog("sit", 1250, 1010, 0.8)], [("pill", 960, 300, "OXYTOCIN"), ("heart", 960, 500, 100)])]},
    {"line": "When dogs and their owners gazed at each other, the owners' oxytocin went up.",
     "shots": [shot("plain_yellow", [hum("stand", 620, 1000), dog("sit", 1300, 1010, 0.9, look=(-1, -1))], [("pill", 620, 220, "OXYTOCIN UP")])]},
    {"line": "And then, it went up in the dogs too.",
     "shots": [shot("plain_yellow", [hum("stand", 620, 1000, eyes="closed"), dog("sit", 1300, 1010, 0.9, eyes="closed", tail="wag")],
                    [("pill", 620, 220, "UP"), ("pill", 1300, 220, "UP TOO!"), ("heart", 960, 460, 110)])]},
    {"line": "The longer a dog gazed at its owner, the bigger the change.",
     "shots": [shot("plain_yellow", [hum("stand", 620, 1000), dog("sit", 1300, 1010, 0.9, look=(-1, -1))],
                    [("clock", 960, 300, 90, 0, 40), ("pill", 960, 520, "MORE GAZE = MORE")])]},
    {"line": "A little loop of good feelings, passed back and forth through a look.",
     "shots": [shot("plain_pink", [hum("stand", 620, 1000), dog("sit", 1300, 1010, 0.9)],
                    [("heart", 960, 330, 80), ("heart", 820, 480, 70), ("heart", 1100, 480, 70), T("THE LOVE LOOP")])]},
    {"line": "When they tried the same thing with wolves raised by people, the loop didn't happen.",
     "shots": [shot("plain_blue", [hum("stand", 620, 1000), wolf("sit", 1300, 1010, 0.9)], [("mark", 960, 420, 180, False), T("WOLVES: NO LOOP")])]},
    {"line": "Not every scientist agrees on what it means, but that stare seems to do something real to both of you.",
     "shots": [shot("plain_purple", [hum("stand", 700, 1000, 0.85, **SCI), hum("stand", 1250, 1000, 0.85, shirt=(150, 150, 150), coat=True)],
                    [("q", 960, 320, 180)]),
               shot("living", [hum("sit", 1490, 880, 0.9, shirt=PINK_SHIRT), dog("sit", 1050, 1010, 0.75, eyes="closed", tail="wag")],
                    [("heart", 1270, 450, 100)])]},
    # ── puppy eyes ──
    {"chapter": "Puppy dog eyes", "line": "And dogs have a secret weapon for that stare.",
     "shots": [shot("plain_yellow", [dog("sit", 960, 1100, 1.5, eyes="puppy", mouth="smile")], [T("PUPPY EYES")], zoom=(1.1, 1.3, 0.5, 0.4))]},
    {"line": "In 2019, scientists compared the faces of dogs and wolves.",
     "say": "In twenty nineteen, scientists compared the faces of dogs and wolves.",
     "shots": [shot("lab", [dog("sit", 760, 1010, 0.75), wolf("sit", 1250, 1010, 0.75)], [T("DOG VS WOLF")])]},
    {"line": "Dogs have a small muscle that lifts the inner eyebrow. It makes their eyes look bigger, and a little sad.",
     "shots": [shot("plain_green", [dog("sit", 960, 1100, 1.5, mouth="smile")], zoom=(1.3, 1.5, 0.5, 0.33)),
               shot("plain_green", [dog("sit", 960, 1100, 1.5, eyes="puppy", mouth="smile")], [T("EYEBROW MUSCLE")], zoom=(1.3, 1.5, 0.5, 0.33))]},
    {"line": "Wolves barely have that muscle at all.",
     "shots": [shot("forest", [wolf("sit", 960, 1100, 1.4)], [("mark", 1450, 400, 180, False)], zoom=(1.2, 1.4, 0.5, 0.35))]},
    {"line": "Funny enough, one dog breed didn't have the muscle either. The Siberian husky.",
     "shots": [shot("plain_blue", [dog("sit", 960, 1010, 1.0, color=(150, 156, 170), ear="pointy", mouth="tongue")], [T("SIBERIAN HUSKY")])]},
    {"line": "And dogs make that eyebrow move far more often.",
     "shots": [shot("plain_pink", [dog("sit", 700, 1010, 0.9, eyes="puppy", mouth="smile"), wolf("sit", 1300, 1010, 0.9)],
                    [("text", 700, 220, "OFTEN", 110, W_), ("text", 1300, 220, "RARELY", 110, W_)])]},
    {"line": "The scientists think that over thousands of years, people favored dogs with those puppy eyes, because the look makes us want to care for them.",
     "shots": [shot("plain_blue", [hum("arms_open", 700, 1000), dog("sit", 1250, 1010, 0.8, eyes="puppy", mouth="smile")], [("heart", 960, 420, 100)]),
               shot("living", [hum("sit", 1490, 880, 0.9, shirt=PINK_SHIRT), dog("sit", 1050, 1010, 0.75, eyes="puppy", mouth="smile")],
                    [("bowl", 1270, 1010), T("WE CAN'T RESIST")])]},
    {"line": "So when your dog gives you that look, it's using a face made for you.",
     "shots": [shot("plain_yellow", [dog("sit", 960, 1100, 1.5, eyes="puppy", mouth="smile")], [("heart", 1400, 300, 110)], zoom=(1.1, 1.3, 0.5, 0.4))]},
    # ── scent ──
    {"chapter": "You smell amazing", "line": "Dogs understand the world through their noses.",
     "shots": [shot("living", [dog("walk", 700, 1010, 0.8, tail="wag")], [("scent", 980, 740, 300)], zoom=(1.0, 1.15, 0.45, 0.65))]},
    {"line": "In 2015, scientist Gregory Berns trained dogs to lie still, awake, inside a brain scanner.",
     "say": "In twenty fifteen, scientist Gregory Berns trained dogs to lie still, awake, inside a brain scanner.",
     "shots": [shot("lab", [hum("point", 450, 1000, 0.85, **SCI)], [("scanner", 1250, 560, 280), T("BRAIN SCANNER")]),
               shot("lab", [], [("scanner", 1200, 560, 280)], late=[dog("lie", 1000, 680, 0.42, mouth="smile")])]},
    {"line": "Twelve dogs took part, all awake and free to leave.",
     "shots": [shot("lab", [dog("sit", 560, 1010, 0.5), dog("sit", 760, 1010, 0.5, color=BROWN), dog("sit", 960, 1010, 0.5, color=(250, 240, 230)),
                            dog("sit", 1160, 1010, 0.5, color=(60, 55, 60)), dog("sit", 1360, 1010, 0.5)], [T("12 DOGS, AWAKE")])]},
    {"line": "Then the dogs sniffed different smells. Strange dogs, familiar dogs, strangers, and a familiar person.",
     "shots": [shot("plain_green", [dog("sit", 960, 1010, 0.7), dog("sit", 330, 560, 0.4, color=(200, 200, 205)), dog("sit", 1590, 560, 0.4, color=BROWN),
                                    hum("stand", 330, 1010, 0.5, shirt=(150, 150, 150)), hum("stand", 1590, 1010, 0.5)],
                    [("text", 330, 610, "STRANGE DOG", 56, W_), ("text", 1590, 610, "FAMILIAR DOG", 56, W_),
                     ("text", 330, 1050, "STRANGER", 56, W_), ("text", 1590, 1050, "FAMILIAR PERSON", 56, W_),
                     ("scent", 470, 470, 300), ("scent", 1150, 470, 300, (120, 190, 110), 1.3),
                     ("scent", 470, 820, 300, (120, 190, 110), 2.1), ("scent", 1150, 820, 300)])]},
    {"line": "The brain's reward area lit up the most for the smell of their familiar human. More than for the other dogs.",
     "shots": [shot("plain_purple", [], [("brain", 960, 520, 360, (255, 225, 110)), T("REWARD AREA LIGHTS UP")]),
               shot("living", [hum("stand", 1250, 1000), dog("sit", 800, 1010, 0.75, eyes="closed", tail="wag")], [("scent", 980, 700, 240), ("heart", 980, 450, 90)])]},
    {"line": "The scientists are careful about what that feels like to a dog, but your scent clearly means something special.",
     "shots": [shot("plain_pink", [dog("sit", 960, 1010, 1.0, eyes="closed", tail="wag")], [("scent", 520, 500, 260), ("heart", 1350, 360, 100)])]},
    # ── words and tone ──
    {"chapter": "They hear how you say it", "line": "Your dog also listens to you more closely than you might think.",
     "shots": [shot("plain_blue", [dog("sit", 1150, 1010, 1.0, look=(-1, 0))], [("waves", 760, 520, 4, -1)], zoom=(1.0, 1.12, 0.6, 0.45))]},
    {"line": "In 2016, scientists in Hungary scanned dogs while a trainer talked to them.",
     "say": "In twenty sixteen, scientists in Hungary scanned dogs while a trainer talked to them.",
     "shots": [shot("lab", [], [("scanner", 1200, 560, 280), ("speaker", 420, 600, 200), T("HUNGARY, 2016")],
                    late=[dog("lie", 1000, 680, 0.42)])]},
    {"line": "Dog brains handled the meaning of words mostly on the left side, and the tone of voice on the right.",
     "shots": [shot("plain_green", [], [("brain", 960, 560, 400), ("text", 700, 320, "WORDS", 120, W_), ("text", 1220, 320, "TONE", 120, W_)])]},
    {"line": "And here's the twist. The reward area only lit up when the words were praise and the tone was happy.",
     "shots": [shot("plain_yellow", [hum("call", 600, 1000), dog("sit", 1300, 1010, 0.9, tail="wag")],
                    [("bubble", 780, 300, 360, 140, "GOOD BOY!!", 72, (-1, 1)), ("mark", 1300, 300, 150, True)])]},
    {"line": "Good boy, in a bored voice? Not so rewarding.",
     "shots": [shot("plain_blue", [hum("stand", 600, 1000, eyes="closed"), dog("sit", 1300, 1010, 0.9)],
                    [("bubble", 780, 300, 360, 140, "good boy.", 72, (-1, 1)), ("mark", 1300, 300, 150, False)])]},
    {"line": "Random words, in a happy voice? Not that either.",
     "shots": [shot("plain_purple", [hum("call", 600, 1000), dog("sit", 1300, 1010, 0.9, look=(-1, 0))],
                    [("bubble", 780, 300, 360, 140, "TOASTER!!", 72, (-1, 1)), ("mark", 1300, 300, 150, False)])]},
    {"line": "Your dog wants you to mean it.",
     "shots": [shot("plain_pink", [hum("arms_open", 700, 1000), dog("sit", 1250, 1010, 0.9, eyes="closed", tail="wag")], [T("MEAN IT!")])]},
    # ── attachment ──
    {"chapter": "Your dog's parent", "line": "So how does your dog feel about you?",
     "shots": [shot("plain_yellow", [dog("sit", 960, 1010, 1.0)], [("heart", 700, 400, 100), ("q", 1250, 380, 200)])]},
    {"line": "Back in 1998, scientists in Hungary tried a test first designed for human babies and their parents.",
     "say": "Back in nineteen ninety-eight, scientists in Hungary tried a test first designed for human babies and their parents.",
     "shots": [shot("lab", [hum("point", 520, 1000, 0.9, **SCI), dog("sit", 1000, 1010, 0.6)], [T("THE BABY TEST")])]},
    {"line": "A dog spends a few minutes in a strange room with its owner, then with a stranger, then alone.",
     "shots": [shot("room", [hum("stand", 420, 1000, 0.85), dog("walk", 900, 1010, 0.6, tail="up")], move={1: (160, 0)}),
               shot("room", [hum("stand", 450, 1000, 0.85, shirt=(150, 150, 150)), dog("sit", 950, 1010, 0.6, look=(1, 0))]),
               shot("room", [dog("sit", 900, 1010, 0.6, eyes="puppy", mouth="smile", look=(1, 0))], [("q", 1200, 520, 140)])]},
    {"line": "Dogs acted a lot like young children with a parent.",
     "shots": [shot("plain_green", [hum("stand", 700, 1000), dog("sit", 1150, 1010, 0.6, puppy=True, tail="wag")], [("heart", 930, 450, 90)])]},
    {"line": "Not every dog reacted the same way, but the overall pattern was clear.",
     "shots": [shot("plain_purple", [dog("sit", 560, 1010, 0.6), dog("sit", 960, 1010, 0.6, color=BROWN, eyes="puppy", mouth="smile"),
                                     dog("sit", 1360, 1010, 0.6, color=(250, 240, 230), tail="wag")], [("heart", 960, 420, 90)])]},
    {"line": "They stayed close to their owner, searched for them when they left, and greeted them happily when they came back.",
     "shots": [shot("room", [hum("stand", 600, 1000, 0.85), dog("sit", 820, 1010, 0.6)]),
               shot("room", [dog("walk", 600, 1010, 0.6, tail="down")], move={0: (700, 0)}),
               shot("room", [hum("wave", 1580, 1000, 0.85), dog("walk", 900, 1010, 0.6, tail="wag")], [("heart", 1300, 500, 90)], move={1: (300, 0)})]},
    # ── look back ──
    {"chapter": "When stuck, they look at you", "line": "Another experiment shows how much dogs count on us.",
     "shots": [shot("plain_purple", [dog("sit", 960, 1010, 0.9, look=(0, -1))], [T("THEY COUNT ON US")])]},
    {"line": "Scientists gave dogs, and wolves raised by people, a box with food they couldn't get out.",
     "shots": [shot("lab", [dog("sit", 760, 1010, 0.7), wolf("sit", 1250, 1010, 0.7)], [("box", 1000, 1010, 230), T("THE IMPOSSIBLE BOX")])]},
    {"line": "The wolves kept working on the box by themselves.",
     "shots": [shot("forest", [wolf("sit", 860, 1010, 0.8, mouth="open")], [("box", 1150, 1010, 260)], zoom=(1.0, 1.15, 0.5, 0.65))]},
    {"line": "The dogs soon turned around and looked at the human, as if asking for help.",
     "shots": [shot("living", [hum("stand", 1350, 1000), dog("sit", 760, 1010, 0.75, eyes="puppy", mouth="smile", look=(1, -1))],
                    [("box", 540, 1010, 230), ("bubble", 960, 420, 280, 130, "HELP?", 70, (-1, 1))])]},
    {"line": "Later studies have argued about exactly what that look means. But most dog owners know it well.",
     "shots": [shot("plain_pink", [dog("sit", 960, 1100, 1.4, eyes="puppy", mouth="smile", look=(0, -1))], zoom=(1.05, 1.2, 0.5, 0.4))]},
    {"line": "To a dog, you're the one who can fix things.",
     "shots": [shot("living", [hum("arms_open", 1250, 1000), dog("sit", 760, 1010, 0.75, eyes="closed", tail="wag")], [("bowl", 1000, 1010), T("YOU FIX THINGS")])]},
    # ── conclusion ──
    {"chapter": "So what are you?", "line": "So, what does your dog really think you are?",
     "shots": [shot("plain_blue", [dog("sit", 1300, 1010, 1.0, look=(-1, -1))],
                    [("bubble", 640, 430, 560, 460, None, 0, (1, 1), True), ("q", 820, 300, 200)], late=[hum("stand", 600, 620, 0.42)])]},
    {"line": "Not an alpha to fight. Not just another dog.",
     "shots": [shot("plain_purple", [wolf("sit", 600, 1010, 0.7), dog("sit", 1320, 1010, 0.7)],
                    [("mark", 600, 360, 200, False), ("mark", 1320, 360, 200, False), ("text", 600, 180, "ALPHA", 100, W_), ("text", 1320, 180, "JUST A DOG", 100, W_)])]},
    {"line": "The science points to something closer to family.",
     "shots": [shot("plain_pink", [dog("sit", 1350, 1010, 0.9, eyes="closed", tail="wag")], [("bubble", 640, 440, 600, 520, None, 0, (1, 1), True)],
                    late=[hum("stand", 640, 650, 0.48), ("dogears", 640, 400, 40)])]},
    {"line": "Someone whose gaze makes them feel good, whose smell lights up their brain, whose voice they read closely, and who they turn to for help.",
     "shots": [shot("plain_yellow", [hum("stand", 620, 1000), dog("sit", 1300, 1010, 0.9, tail="wag")], [("heart", 960, 420, 100), T("YOUR LOOK")]),
               shot("plain_purple", [], [("brain", 960, 560, 360, (255, 225, 110)), T("YOUR SMELL")]),
               shot("plain_yellow", [hum("call", 600, 1000), dog("sit", 1300, 1010, 0.9, tail="wag")],
                    [("bubble", 780, 300, 360, 140, "GOOD BOY!!", 72, (-1, 1)), T("YOUR VOICE")]),
               shot("living", [hum("stand", 1350, 1000), dog("sit", 760, 1010, 0.75, eyes="puppy", mouth="smile", look=(1, -1))],
                    [("box", 540, 1010, 230), T("YOUR HELP")])]},
    {"line": "In other words, you might be the closest thing your dog has to a parent.",
     "shots": [shot("living", [hum("sit", 1490, 880, 0.9, shirt=PINK_SHIRT), dog("sit", 1050, 1010, 0.75, eyes="closed", tail="wag")],
                    [("heart", 1270, 420, 110), T("YOU = PARENT?")])]},
    {"line": "Does your dog give you puppy eyes? Tell us in the comments.",
     "shots": [shot("plain_blue", [dog("sit", 1300, 1010, 0.9, eyes="puppy", mouth="smile")], [("bubble", 700, 460, 640, 240, "COMMENT BELOW!", 80, (1, 1))])]},
    {"line": "And if you missed it, find out what your cat thinks you are in our last video.",
     "shots": [shot("plain_yellow", [cat("sit", 1350, 1010, 0.9)], [T("WATCH NEXT: YOUR CAT", 760, 460, 140)])]},
    {"line": "Subscribe to FramedFacts for more animal secrets.", "say": "Subscribe to Framed Facts for more animal secrets.",
     "shots": [shot("plain_pink", [dog("sit", 1350, 1010, 0.9, eyes="closed", tail="wag")], [("sub", 700, 540)])]},
]

SCRIPT = {
    "format": "long",
    "hook": SEGMENTS[0]["line"] + " " + SEGMENTS[1]["line"],
    "body": " ".join(s["line"] for s in SEGMENTS[2:-3]),
    "cta": "Does your dog give you puppy eyes? Tell us in the comments!",
    "title": "Your Dog Doesn't See You as Its Boss. It Sees You as Its Parent",
    "category_id": "15",
    "tags": ["dog psychology", "what do dogs think of humans", "dog behavior", "do dogs love their owners", "puppy dog eyes",
             "alpha dog myth", "dog brain", "dog facts", "dogs", "animal psychology", "pets"],
    "ai_generated_visuals": False,
    "topic_category": "Animals",
    "thumbnail_path": THUMB,
}

SOURCES = (
    "Sources:\n"
    "- Mech, L. D. (1999) Alpha status, dominance, and division of labor in wolf packs, Canadian Journal of Zoology\n"
    "- Nagasawa et al. (2015) Oxytocin-gaze positive loop and the coevolution of human-dog bonds, Science\n"
    "- Kaminski et al. (2019) Evolution of facial muscle anatomy in dogs, PNAS\n"
    "- Berns, Brooks & Spivak (2015) Scent of the familiar: an fMRI study of canine brain responses, Behavioural Processes\n"
    "- Andics et al. (2016) Neural mechanisms for lexical processing in dogs, Science\n"
    "- Topal et al. (1998) Attachment behavior in dogs: a new application of Ainsworth's Strange Situation Test, J. Comparative Psychology\n"
    "- Miklosi et al. (2003) A simple reason for a big difference: wolves do not look back at humans, but dogs do, Current Biology"
)

render_shot = cv.render_shot
frame = cv.frame_fn(SEGMENTS, VIDEO_ID)
sound_events = cv.section_sounds(SEGMENTS)


def make_thumbnail(path=THUMB):
    """Conflict thumbnail (thumb_kit): snarling 'alpha' wolf crossed out vs a loving dog."""
    left = tk.burst((200, 30, 30), (40, 0, 5), cx=0.25, cy=0.6)
    right = tk.burst((255, 210, 80), (230, 90, 20), cx=0.75, cy=0.6)
    c = tk.split(left, right, slant=120)
    lay, d = tk.layer()
    tk.wolf_head(d, 470, 690, 330)
    tk.stick(c, lay)
    lay, d = tk.layer()
    tk.red_x(d, 470, 640, 250)
    tk.stick(c, lay, outline=10, shadow=(8, 10))
    lay, d = tk.layer()
    tk.dog_head(d, 1450, 700, 340)
    tk.hearts(d, [(1140, 470, 110), (1760, 430, 90), (1700, 880, 70)])
    tk.stick(c, lay)
    tk.headline(c, [("ALPHA IS", 120, tk.WHITE), ("A MYTH", 190, tk.YELLOW)], 960, 170, rotate=-3)
    return tk.save(c, path)


def chapters_text(starts):
    return cv.chapters_text(SEGMENTS, starts)


def build():
    make_thumbnail()
    return ms.render_short(SCRIPT, SEGMENTS, VIDEO_ID, frame, speed=1.05, music_style="emotional",
                           sfx_fn=sound_events, music_vol=0.05)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "preview"
    if cmd == "preview":
        p = sys.argv[2] if len(sys.argv) > 2 else "dog_preview.jpg"
        n = cv.preview(SEGMENTS, p)
        make_thumbnail()
        print(n, "shots ->", p, "| thumbnail ->", THUMB, "| words:", sum(len(s["line"].split()) for s in SEGMENTS))
    elif cmd == "build":
        print(build())
