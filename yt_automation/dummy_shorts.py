"""
dummy_shorts.py — "The Dummy Tests": three Shorts the owner approved on 2026-11-06 ("All 3"), one opening style each,
posted one a day and judged on STAYED TO WATCH at 24-48 h (CHANNEL_DIAGNOSIS.md, LESSONS rules 17-18, PITCHES.md).

Rule 18 is built in: frame 1 is an event (blender_pitches.py openings), the first second carries only the 2-4 word
hook, captions start at 1.0 s, captions/calls to action stay above y 1500, sound from 0.0 s.
Free: Blender on this machine, local Kokoro voices, our synthesized music and sound effects.

  python dummy_shorts.py voice NAME            # Kokoro narration (+ the dummy's own voice) -> timing.json
  python dummy_shorts.py still NAME F [F ..]   # Blender look-test frames
  python dummy_shorts.py frames NAME A B       # Blender: render frames A..B
  python dummy_shorts.py compose NAME          # overlays + voice + sfx + music -> mp4, then the clarity check
  python dummy_shorts.py clarity NAME          # narration vs sfx+music in the speech band (>= 12 dB, rule 19)
  python dummy_shorts.py sheet NAME            # first-second sheet of the finished mp4 (QA, rule 18)
  python dummy_shorts.py upload NAME [RFC3339]  # private, YouTube release time set, captions, cover; id -> dummy_uploads.json
  python dummy_shorts.py golive NAME           # public now, first comment, read back
  python dummy_shorts.py publish NAME          # both, going live now
NAME: penny | hail | quicksand | lightning | sinking | lava | venus | ocean
"""
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import motion_shorts as ms
import sfx

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 24
GOLD, CREAM, WHITE, DARK = (255, 208, 70), (250, 240, 222), (255, 255, 255), (12, 10, 10)
FONT_T = os.path.join(HERE, "fonts", "BebasNeue-Regular.ttf")
BLENDER_PY = "/root/.venvs/blender/bin/python"
NARRATOR, NARR_SPEED = "am_michael", 1.04
DUMMY = {"voice": "bm_lewis", "speed": 0.88}          # the dummy: dry, slow, British
END_GAP = 1.6
# Owner, 2026-11-08: "we don't get engagement from the audience" -- every ending asks for both, with a reason
# (the next test), inside the last line (rule 20: no long end card; the hail lost ~20 points on a 3 s card).
END_LINE = "What should he test next? Comment, and subscribe to see it."
END_COMMENT = "What should we test on him next? Most-liked idea gets made 👇 Subscribe so you see it when it drops 🔔"
# "10 Seconds in ___" (owner, 2026-11-11: "start work on this and post when ready"): he is dropped somewhere impossible,
# a clock counts 10 to 0, and physics does the acting (LESSONS rule 21). One title pattern for the whole series.
DROP_LINE = "Where should we drop him next? Comment, and subscribe to see it."
DROP_CARD = ("WHERE DO WE DROP", "HIM NEXT?")
DROP_COMMENT = ("Where should we drop him for 10 seconds next? Most-liked idea gets made 👇 "
                "Subscribe so you see it when it drops 🔔")
SOURCES_TAIL = ("\n\nSubscribe for the next Dummy Test, and comment what he should test next."
                "\n\nAnimated in 3D by FramedFacts. #shorts #science #mythbusting")

SPECS = {
    "penny": {
        "test_no": 1,
        "hook": "WOULD THIS KILL HIM?",
        "music": "lounge",
        "segments": [
            {"line": "A penny, dropped from the top of a skyscraper.", "shot": "fall", "gap": 0.2},
            {"line": "Our dummy is right underneath.", "shot": "fall2", "callout": "OUR TEST DUMMY", "gap": 0.25},
            {"line": "The myth says it hits like a bullet.", "shot": "myth", "callout": "THE MYTH: DEADLY", "gap": 0.25},
            {"line": "But a penny is flat and light. It flips, it flutters, and the air slows it down.",
             "shot": "flutter", "callout": "FLAT + LIGHT = AIR BRAKE", "gap": 0.25},
            {"line": "It stops speeding up long before the ground.", "shot": "terminal", "callout": "TOP SPEED REACHED",
             "gap": 0.65},
            dict(DUMMY, line="Ow.", shot="hit", callout="A STING. NOT A HOLE.", gap=0.45),
            {"line": "MythBusters tested it. It stings. That's it.", "say": "Mythbusters tested it. It stings. That's it.",
             "shot": "after", "callout": "TESTED: IT STINGS", "gap": 0.25},
            {"line": "And on the Empire State Building, the wind usually blows it onto a lower roof anyway.",
             "shot": "roof", "callout": "UPDRAFT + LOWER ROOFS", "gap": 0.3},
            {"line": "What should we test on him next?", "shot": "end", "gap": END_GAP},
        ],
        "script": {
            "title": "The Penny Myth Everyone Believes 🪙 #shorts",
            "tags": ["penny drop", "empire state building penny", "penny myth", "terminal velocity", "myth busting",
                     "physics", "crash test dummy", "science shorts", "3d animation", "shorts"],
            "seo_description": (
                "Would a penny dropped from a skyscraper kill someone below? No. A penny is flat and light, so it "
                "tumbles and the air brakes it: it stops speeding up long before the ground and lands with a sting, "
                "not a hole. MythBusters busted the myth in 2003, and at the Empire State Building updrafts and the "
                "lower roofs usually stop a penny from reaching the street at all.\n\nSources: MythBusters (2003, "
                "'Penny Drop'); Today I Found Out; USC Folklore Archives."),
        },
    },
    "hail": {
        "test_no": 2,
        "hook": "USA'S BIGGEST HAIL",
        "music": "lounge",
        "segments": [
            {"line": "That is the biggest hailstone ever found in the US.", "shot": "impact", "gap": 0.25},
            {"line": "Eight inches across. Almost two pounds. South Dakota, 2010.", "shot": "closeup",
             "callout": "8 IN · 1.94 LB · 2010", "gap": 0.3},
            {"line": "Let's start small.", "shot": "reset", "gap": 0.2},
            {"line": "Pea-size hail falls at up to about twenty-five miles an hour. It bounces off.",
             "shot": "pea", "callout": "PEA SIZE · ~25 MPH", "gap": 0.25},
            {"line": "Golf-ball size: about forty.", "shot": "golf", "callout": "GOLF BALL · ~40 MPH", "gap": 0.25},
            {"line": "Baseball size: up to about seventy. Now it tears.", "shot": "baseball",
             "callout": "BASEBALL · ~70 MPH", "gap": 0.25},
            {"line": "And the record? Close to a hundred miles an hour.", "shot": "record",
             "callout": "RECORD · ~100 MPH", "gap": 0.45},
            dict(DUMMY, line="I need a stronger umbrella.", shot="lookup", gap=0.35),
            {"line": "What should fall on him next?", "shot": "end", "gap": END_GAP},
        ],
        "script": {
            "title": "Hail Can Fall Faster Than You Drive 🧊 #shorts",
            "tags": ["hail", "hailstone", "biggest hailstone", "vivian south dakota hailstone", "hail size",
                     "weather facts", "crash test dummy", "science shorts", "3d animation", "shorts"],
            "seo_description": (
                "The biggest hailstone ever found in the US fell near Vivian, South Dakota on 23 July 2010: 8.0 inches "
                "across and 1.9375 pounds. Small hail (under 1 inch) falls at about 9-25 mph, 1-1.75 inch hail at "
                "25-40 mph, 2-4 inch hail at roughly 44-72 mph, and stones over 4 inches can approach 100 mph "
                "(estimates vary with shape and melting).\n\nSources: NWS Aberdeen; NOAA NCEI; NOAA National Severe "
                "Storms Laboratory."),
        },
    },
    "quicksand": {
        "test_no": 3,
        "hook": "WILL IT SWALLOW HIM?",
        "music": "lounge",
        "segments": [
            {"line": "Our dummy just stepped into quicksand.", "shot": "sink", "gap": 0.2},
            {"line": "In movies, this is where he disappears.", "shot": "sink2", "callout": "IN MOVIES: GONE",
             "gap": 0.25},
            {"line": "But quicksand is about twice as dense as a human body.", "shot": "density",
             "callout": "QUICKSAND: ~2× DENSER", "gap": 0.25},
            {"line": "So he sinks to about his waist, and then he floats.", "shot": "float",
             "callout": "STOPS AT THE WAIST", "gap": 0.3},
            {"line": "The bad news? Pulling a leg out takes about the force needed to lift a car.", "shot": "pull",
             "callout": "= LIFTING A CAR", "gap": 0.25},
            {"line": "The trick is to wiggle, slowly, so water gets in around the leg.", "shot": "wiggle",
             "callout": "WIGGLE. SLOWLY.", "gap": 0.25},
            {"line": "The real danger is getting stuck when the tide comes in.", "shot": "tide",
             "callout": "REAL DANGER: THE TIDE", "gap": 0.45},
            dict(DUMMY, line="So... I live here now.", shot="resigned", gap=0.35),
            {"line": "What should we test on him next?", "shot": "end", "gap": END_GAP},
        ],
        "script": {
            "title": "Why Quicksand Can't Swallow You 🫠 #shorts",
            "tags": ["quicksand", "can quicksand kill you", "quicksand myth", "how to escape quicksand", "physics",
                     "myth busting", "crash test dummy", "science shorts", "3d animation", "shorts"],
            "seo_description": (
                "Quicksand can't pull you under: it is about twice as dense as a human body (about 2 g/ml vs 1), so "
                "you sink to about the waist and float. Getting a leg out is the hard part: researchers estimated "
                "the force is like lifting a medium-sized car. Wiggling slowly lets water in around the leg; the real "
                "danger is being stuck as the tide rises.\n\nSources: Khaldoun, Eiser, Wegdam & Bonn, 'Liquefaction "
                "of quicksand under stress', Nature (2005), and Nature's news story; National Geographic."),
        },
    },
    "lightning": {
        "test_no": 4,
        "hook": "IS HE ALIVE?",
        "music": "analytical",
        "segments": [
            {"line": "Lightning just hit his car.", "shot": "strike", "gap": 0.35},
            {"line": "Everyone thinks the rubber tires saved him.", "shot": "myth", "callout": "MYTH: THE TIRES",
             "gap": 0.25},
            {"line": "That bolt just tore through the sky. A little rubber won't stop it.", "shot": "jump",
             "callout": "RUBBER? NO CHANCE", "gap": 0.3},
            {"line": "The metal shell saved him. The current races around the outside of the car, and into the "
                     "ground.", "shot": "shell", "callout": "THE METAL SHELL", "gap": 0.3},
            {"line": "The car pays for it: a blown tire, fried electronics.", "shot": "damage",
             "callout": "BLOWN TIRE, DEAD DASH", "gap": 0.3},
            dict(DUMMY, line="...My radio's dead.", shot="radio", gap=0.45),
            {"line": "And in a convertible? No metal roof. No protection.", "shot": "convertible",
             "callout": "NO ROOF = NO SHELTER", "gap": 0.3},
            {"line": END_LINE, "shot": "end", "gap": 0.5},     # short tail: loop straight back into the strike (rule 20)
        ],
        "script": {
            "title": "Do Tires Really Save You From Lightning? ⚡ #shorts",
            "tags": ["lightning", "lightning hits car", "car struck by lightning", "faraday cage", "lightning myths",
                     "rubber tires lightning", "crash test dummy", "science shorts", "3d animation", "shorts"],
            "seo_description": (
                "If lightning hits a car, the rubber tires are not what protects the people inside: the metal roof and "
                "sides carry the current around the outside of the car and into the ground (a partial Faraday "
                "cage). The car can still be damaged: blown tires, a fried electrical system, antenna and rear "
                "window. Convertibles and vehicles without a metal roof offer no protection; the safest place in a "
                "storm is a substantial building.\n\nSources: US National Weather Service lightning safety (myths "
                "and facts); National Lightning Safety Council; UCAR Center for Science Education."),
        },
    },    "sinking": {
        "test_no": 5,
        "hook": "CAN HE GET OUT?",
        "music": "deep",
        # story-time countdown on screen (rule 20: a question that stays open to the end): per segment, the clock
        # runs from the first number to the second; None hides it (the end card)
        "clock": [(60, 57), (55, 45), (44, 33), (31, 22), (20, 12), (10, 4), (3, 3), None],
        "segments": [
            {"line": "His car just went into a river. He has about one minute.", "shot": "plunge", "gap": 0.3},
            {"line": "First instinct: grab the phone. Wrong. That call eats the minute.", "shot": "phone",
             "callout": "MISTAKE 1: PHONE", "gap": 0.3},
            {"line": "The door? The river is pushing it shut. It won't budge.", "shot": "door",
             "callout": "MISTAKE 2: DOOR", "gap": 0.3},
            {"line": "What works: seatbelt off. Window down, now, while the power still works.", "shot": "window",
             "callout": "SEATBELT. WINDOW. OUT.", "gap": 0.3},
            {"line": "Stuck? Break a side window. Never the windshield. It won't break.", "shot": "stuck",
             "callout": "WINDOW STUCK?", "gap": 0.3},
            {"line": "Then get out. Fast.", "shot": "out", "callout": "OUT!", "gap": 0.35},
            dict(DUMMY, line="...I'm buying a window hammer.", shot="surface", gap=0.45),
            {"line": END_LINE, "shot": "end", "gap": 0.5},
        ],
        "script": {
            "title": "He Has 60 Seconds to Escape a Sinking Car 🌊 #shorts",
            "tags": ["sinking car", "how to escape a sinking car", "car underwater", "car in water", "survival tips",
                     "car safety", "crash test dummy", "science shorts", "3d animation", "shorts"],
            "seo_description": (
                "If your car goes into water you have about a minute to act. Don't call first: the call uses up the "
                "time. The door is very hard to open against the water outside. What works, in order: seatbelt off, "
                "window open (electric windows usually still work at first, so do it early), then get out. If the "
                "window won't open, break a side window with a window hammer; the windshield is laminated and won't "
                "break. Keep a window hammer within reach.\n\nSources: Dr. Gordon Giesbrecht, University of Manitoba "
                "(seatbelts, window, out); AAA vehicle escape tool tests (2019); ADAC sinking-car test; "
                "KUOW / CBS News reports."),
        },
    },
    "lava": {
        "test_no": 6,
        "hook": "10 SECONDS IN LAVA",
        "music": "deep",
        "end_card": DROP_CARD,
        "end_comment": DROP_COMMENT,
        # the 10 seconds, stretched: the clock holds at 10 until he lands and reaches 0 on "Time's up"
        "clock": [(10, 10), (10, 8), (8, 6), (6, 4), (4, 1), (1, 0), (0, 0), None],
        "segments": [
            {"line": "Ten seconds in lava. What's left of him?", "shot": "drop", "gap": 0.3},
            {"line": "First surprise: he doesn't sink. Lava is three times denser than he is.", "shot": "float",
             "callout": "HE DOESN'T SINK", "gap": 0.3},
            {"line": "It's over eleven hundred degrees. His vinyl skin bursts into flame.", "shot": "burn",
             "callout": "1,170°C", "gap": 0.3},
            {"line": "Skin and foam burn away. The metal underneath starts to glow.", "shot": "strip",
             "callout": "SKIN: GONE", "gap": 0.3},
            {"line": "But steel melts at about fourteen hundred degrees. This lava can't do it.", "shot": "steel",
             "callout": "STEEL WON'T MELT", "gap": 0.3},
            {"line": "Time's up. A red-hot steel skeleton, still in one piece.", "shot": "timesup",
             "callout": "TIME'S UP", "gap": 0.4},
            dict(DUMMY, line="...I'm fine.", shot="fine", gap=0.45),
            {"line": DROP_LINE, "shot": "end", "gap": 0.5},
        ],
        "script": {
            "title": "10 Seconds in Lava 🌋 #shorts",
            "tags": ["lava", "what if you fell in lava", "falling into lava", "volcano", "what if", "10 seconds",
                     "crash test dummy", "science shorts", "3d animation", "shorts"],
            "seo_description": (
                "What happens to a crash-test dummy in 10 seconds on lava? It doesn't plunge in like in the movies: "
                "basalt lava is about three times as dense as water and far thicker, so a body lands on it. Erupting "
                "Hawaiian lava is about 1,170 C (2,140 F), so the dummy's vinyl skin and foam burn at once. But its "
                "skeleton is mostly steel, and steel melts at roughly 1,370-1,540 C: hotter than the lava. "
                "A real person would not survive this; never go near active lava.\n\nSources: USGS, 'How hot is a "
                "Hawaiian volcano?' and Hawaiian Volcano Observatory Volcano Watch; Erik Klemetti, 'The Right (and "
                "Wrong) Way to Die When You Fall Into Lava' (Wired / Discover); Humanetics Hybrid III specifications "
                "and IEEE Spectrum, 'Anatomy of a Crash-Test Dummy'."),
        },
    },
    "lavayou": {
        # "What If You ..." series (turning-point study, 2026-11-11): the subject is the viewer, and the inside
        # of the body is shown close up in layers
        "hook": "YOU FELL INTO LAVA",
        "music": "deep",
        "end_card": ("WHAT HAPPENS TO", "YOU NEXT?"),
        "sub_text": "SUBSCRIBE FOR THE NEXT ONE",
        "end_comment": ("What should happen to you next? Most-liked idea gets made 👇 "
                        "Subscribe so you see it 🔔"),
        "tail": ("\n\nSubscribe for the next What If, and comment what should happen to you next."
                 "\n\nAnimated in 3D by FramedFacts. #shorts #science #whatif"),
        "clock": [(10, 10), (10, 9), (9, 7), (7, 5), (5, 3), (3, 0), (0, 0), None],
        "segments": [
            {"line": "You just fell into lava. You have ten seconds.", "shot": "fall", "gap": 0.3},
            {"line": "First surprise: you don't sink. Lava is three times denser than you, so you land on top.",
             "shot": "land", "callout": "YOU DON'T SINK", "gap": 0.3},
            {"line": "It's over eleven hundred degrees. Your skin is two millimetres thick. It chars almost instantly.",
             "shot": "skin", "callout": "UNDER YOUR SKIN", "gap": 0.3},
            {"line": "You are sixty percent water. It boils into steam and bursts out.", "shot": "steam",
             "callout": "60% WATER", "gap": 0.3},
            {"line": "Under the skin is fat. It melts, then it catches fire.", "shot": "fat",
             "callout": "FAT BURNS", "gap": 0.3},
            {"line": "Your muscles cook. But your bones? Even a cremation oven needs two hours for those.",
             "shot": "bone", "callout": "BONE: UNTOUCHED", "gap": 0.3},
            {"line": "Time's up. You didn't sink, and you didn't melt. You burned, on top.", "shot": "timesup",
             "callout": "TIME'S UP", "gap": 0.4},
            {"line": "What should happen to you next? Comment, and subscribe to see it.", "shot": "end", "gap": 0.5},
        ],
        "script": {
            "title": "What If You Fell Into Lava for 10 Seconds? 🌋 #shorts",
            "tags": ["what if", "what if you fell into lava", "lava", "falling into lava", "volcano", "human body",
                     "10 seconds", "science shorts", "3d animation", "shorts"],
            "seo_description": (
                "What if you fell into lava for 10 seconds? You would not plunge in like in the movies: basalt lava "
                "is about three times as dense as water and far thicker, so a body lands on top. Erupting Hawaiian "
                "lava is about 1,170 C (2,140 F). Skin is only a few millimetres thick and chars at once; the water "
                "that makes up about 60% of the body boils to steam; fat melts and burns. Bone lasts far longer: a "
                "cremation oven at 760-980 C needs about two hours. This is a 3D illustration, not a real person; "
                "nobody survives this, and you should never go near active lava.\n\nSources: USGS and the Hawaiian "
                "Volcano Observatory on lava temperature; Erik Klemetti, 'The Right (and Wrong) Way to Die When You "
                "Fall Into Lava' (Discover); NBC News, 'What would happen if you fell into a volcano?'; ICCFA, "
                "'What happens during the cremation process?'."),
        },
    },
    "oxygen": {
        "hook": "THE OXYGEN IS GONE",
        "music": "deep",
        "end_card": ("WHAT SHOULD", "VANISH NEXT?"),
        "sub_text": "SUBSCRIBE FOR THE NEXT ONE",
        "end_comment": ("What should vanish next? Most-liked idea gets made 👇 Subscribe so you see it 🔔"),
        "tail": ("\n\nSubscribe for the next What If, and comment what should vanish next."
                 "\n\nAnimated in 3D by FramedFacts. #shorts #science #whatif"),
        "clock": [(5, 5), (5, 4), (4, 4), (4, 3), (3, 2), (2, 0), (0, 0), None],
        "segments": [
            {"line": "All the oxygen on Earth just vanished. You have five seconds.", "shot": "gone", "gap": 0.3},
            {"line": "A fifth of the air is missing, so the pressure drops like you shot two kilometres up. "
                     "Your ears pop.", "shot": "ears", "callout": "YOUR EARS POP", "gap": 0.3},
            {"line": "Every flame on the planet goes out. Fire needs oxygen. So do engines.", "shot": "fire",
             "callout": "EVERY FIRE DIES", "gap": 0.3},
            {"line": "Now look inside your lungs. Normally, oxygen passes from the air into your blood.",
             "shot": "lung", "callout": "INSIDE YOUR LUNGS", "gap": 0.3},
            {"line": "With none in the air, it runs backwards. Breathe in, and oxygen leaves your blood.",
             "shot": "back", "callout": "IT RUNS BACKWARDS", "gap": 0.3},
            {"line": "One or two breaths like that and you black out, with no warning at all.", "shot": "faint",
             "callout": "NO WARNING", "gap": 0.3},
            {"line": "Time's up. The oxygen is back. Five seconds is about one breath, so you make it.",
             "shot": "timesup", "callout": "TIME'S UP", "gap": 0.4},
            {"line": "What should vanish next? Comment, and subscribe to see it.", "shot": "end", "gap": 0.5},
        ],
        "script": {
            "title": "What If the Oxygen Vanished for 5 Seconds? 😮 #shorts",
            "tags": ["what if", "what if oxygen vanished", "oxygen", "no oxygen for 5 seconds", "human body", "lungs",
                     "5 seconds", "science shorts", "3d animation", "shorts"],
            "seo_description": (
                "What if all the oxygen in the air vanished for 5 seconds? Oxygen is about 21% of the air, so the "
                "pressure would fall by about a fifth, roughly what you feel 2 km (6,500 ft) up. Nothing could "
                "burn. In your lungs, oxygen normally moves from the air sacs into the blood; if the air has none, "
                "it moves the other way, which is why oxygen-free gas can knock a person out in one or two breaths "
                "with no warning. Five seconds is about one breath, so you would recover. This is a simplified 3D "
                "illustration of a thought experiment: only the oxygen gas in the air is removed, not the oxygen "
                "in water or rock.\n\nSources: U.S. Chemical Safety Board, 'Hazards of Nitrogen Asphyxiation' "
                "(2003); Wikipedia, 'Inert gas asphyxiation'; NOAA/NASA on the composition of air; the "
                "International Standard Atmosphere for pressure at altitude."),
        },
    },
    "spin": {
        # Jems, owner-approved 2026-11-17 ("Yes"): bigger stakes and a mid-disaster first frame, after the scan
        # showed "What if Earth lost its air for 5 seconds simulation" (2.95M views, 2.8K-sub channel)
        "hook": "EARTH STOPPED SPINNING",
        "music": "deep",
        "voice": "am_puck", "speed": 1.05, "lipsync": True,
        "end_card": ("WHAT SHOULD", "STOP NEXT?"),
        "sub_text": "SUBSCRIBE FOR JEMS' NEXT ONE",
        "end_comment": ("What should stop next? Jems will try the most-liked idea 👇 Subscribe so you see it 🔔"),
        "tail": ("\n\nJems is FramedFacts' 3D character. Subscribe for his next What If, and comment what should "
                 "stop next.\n\nAnimated in 3D by FramedFacts. #shorts #science #whatif #simulation"),
        "clock": [(5, 5), (5, 4), (4, 3), (3, 2), (2, 1), (1, 0), (0, 0), None],
        "segments": [
            {"line": "Earth just stopped spinning. But I'm still moving, at sixteen hundred kilometres an hour.",
             "shot": "fling", "gap": 0.3},
            {"line": "Earth turns once a day. At the equator, the ground moves at sixteen hundred and seventy "
                     "kilometres an hour. Faster than sound.", "shot": "globe", "callout": "1,670 KM/H", "gap": 0.3},
            {"line": "The ground stops. Nothing else does. Cars, people, anything not anchored to rock keeps flying "
                     "east.", "shot": "street", "callout": "EVERYTHING FLIES EAST", "gap": 0.3},
            {"line": "The air keeps going too. That's wind four times stronger than the worst hurricane ever "
                     "measured.", "shot": "wind", "callout": "4X THE WORST HURRICANE", "gap": 0.3},
            {"line": "So do the oceans. Giant waves slam into the coasts.", "shot": "ocean",
             "callout": "THE OCEANS KEEP MOVING", "gap": 0.3},
            {"line": "And inside my head, my brain floats in fluid. When I hit something, my skull stops, but my "
                     "brain keeps going and hits the bone. That's a concussion.", "shot": "brain",
             "callout": "INSIDE YOUR HEAD", "gap": 0.3},
            {"line": "Time's up. Good news: Earth can't really stop like this. Its spin slows by less than two "
                     "thousandths of a second per century.", "shot": "timesup", "callout": "TIME'S UP", "gap": 0.4},
            {"line": "What should stop next? Comment, and subscribe to see it.", "shot": "end", "gap": 0.5},
        ],
        "script": {
            "title": "What If the Earth Stopped Spinning for 5 Seconds? (3D Simulation) 🌪️ #shorts",
            "tags": ["what if", "what if earth stopped spinning", "earth stopped spinning", "simulation",
                     "3d simulation", "jems", "5 seconds", "science shorts", "space", "shorts"],
            "seo_description": (
                "What if the Earth stopped spinning for 5 seconds? At the equator the ground moves east at about "
                "1,670 km/h (1,040 mph), faster than sound. If the planet stopped, everything not anchored to rock, "
                "including the air and the oceans, would keep moving east at that speed: winds about four times the "
                "strongest hurricane gust ever measured, and huge waves. In a sudden stop the skull stops but the "
                "brain keeps moving and strikes the inside of the skull, which is what a concussion is. Good news: "
                "Earth can't stop like this; its spin slows by only about 1.8 milliseconds per century. A simplified "
                "3D simulation of a thought experiment.\n\nSources: Live Science, 'What would happen if Earth "
                "suddenly stopped spinning?'; Space.com, 'What would happen if Earth stopped spinning?' (with NASA's "
                "Sten Odenwald); BBC Sky at Night Magazine; Scientific American, 'What happens to the brain during a "
                "concussion?'; Queensland Brain Institute, 'What is concussion?'; Stephenson et al., Proc. R. Soc. A "
                "(2016), reported by Space.com and Live Science; World Meteorological Organization, highest recorded "
                "wind gust (408 km/h, Barrow Island, 1996)."),
        },
    },
    "friction": {
        # Jems (blender_hero.py), the channel's recurring character, owner-approved 2026-11-16: he narrates and
        # his mouth follows the voice ("lipsync"); idea from a viewer comment on the gravity Short
        "hook": "FRICTION IS GONE",
        "music": "deep",
        "voice": "am_puck", "speed": 1.05, "lipsync": True,
        "end_card": ("WHAT SHOULD", "DISAPPEAR NEXT?"),
        "sub_text": "SUBSCRIBE FOR JEMS' NEXT ONE",
        "end_comment": ("What should disappear next? Jems will try the most-liked idea 👇 Subscribe so you see it 🔔"),
        "tail": ("\n\nJems is FramedFacts' 3D character. Subscribe for his next What If, and comment what should "
                 "disappear next.\n\nAnimated in 3D by FramedFacts. #shorts #science #whatif"),
        "clock": [(5, 5), (5, 4), (4, 3), (3, 2), (2, 1), (1, 0), (0, 0), None],
        "segments": [
            {"line": "Friction just disappeared. I have five seconds.", "shot": "slip", "gap": 0.3},
            {"line": "I try to walk, but I can't. Walking means pushing the ground backwards, and my shoes just "
                     "slide.", "shot": "walk", "callout": "YOU CAN'T WALK", "gap": 0.3},
            {"line": "Up close, every surface is covered in tiny bumps that catch on each other. That's friction. "
                     "Now they slide right past.", "shot": "micro", "callout": "TINY BUMPS", "gap": 0.3},
            {"line": "My phone slips out of my hand. Holding anything needs friction too.", "shot": "phone",
             "callout": "YOU CAN'T HOLD ANYTHING", "gap": 0.3},
            {"line": "My shoelaces untie themselves. Knots only hold because the string rubs on itself.",
             "shot": "laces", "callout": "KNOTS COME UNDONE", "gap": 0.3},
            {"line": "Even nails hold wood by friction. This bench is falling apart.", "shot": "nails",
             "callout": "NAILS SLIDE OUT", "gap": 0.3},
            {"line": "Time's up. Friction is back. And I'm stuck in the splits.", "shot": "timesup",
             "callout": "TIME'S UP", "gap": 0.4},
            {"line": "What should disappear next? Comment, and subscribe to see it.", "shot": "end", "gap": 0.5},
        ],
        "script": {
            "title": "What If Friction Disappeared for 5 Seconds? 😱 #shorts",
            "tags": ["what if", "what if friction disappeared", "friction", "no friction", "physics", "jems",
                     "5 seconds", "science shorts", "3d animation", "shorts"],
            "seo_description": (
                "What if friction disappeared for 5 seconds? You couldn't walk: walking works by pushing the ground "
                "backwards, and friction is what pushes you forward. Surfaces that look smooth are covered in tiny "
                "bumps that catch on each other; without friction they slide straight past. You couldn't hold "
                "anything, most knots would slip undone because they hold by the string rubbing on itself, and "
                "nails, which hold wood by friction, would slide out. A simplified 3D illustration of a thought "
                "experiment: friction can't actually switch off.\n\nSources: The Average Scientist, 'Explore a "
                "World Without Friction' (2023); Science Insights, 'What Would Happen Without Friction on Earth?'; "
                "Encyclopaedia Britannica, 'Friction'; F. P. Bowden and D. Tabor, 'The Friction and Lubrication of "
                "Solids' (1950)."),
        },
    },
    "gravity": {
        "hook": "GRAVITY IS OFF",
        "music": "deep",
        "end_card": ("WHAT SHOULD", "SWITCH OFF NEXT?"),
        "sub_text": "SUBSCRIBE FOR THE NEXT ONE",
        "end_comment": ("What should switch off next? Most-liked idea gets made 👇 Subscribe so you see it 🔔"),
        "tail": ("\n\nSubscribe for the next What If, and comment what should switch off next."
                 "\n\nAnimated in 3D by FramedFacts. #shorts #science #whatif"),
        "clock": [(5, 5), (5, 4), (4, 3), (3, 2), (2, 0), (0, 0), (0, 0), None],
        "segments": [
            {"line": "Gravity just switched off. You have five seconds.", "shot": "off", "gap": 0.3},
            {"line": "You don't shoot into space. The Earth spins at sixteen hundred kilometres an hour, and the "
                     "ground curves away beneath you.", "shot": "globe", "callout": "THE GROUND CURVES AWAY",
             "gap": 0.3},
            {"line": "In five seconds you rise about forty centimetres. So does everything that isn't bolted down.",
             "shot": "rise", "callout": "YOU RISE 40 CM", "gap": 0.3},
            {"line": "Inside your ear, tiny crystals tell your brain which way is down. Now they float.",
             "shot": "ear", "callout": "INSIDE YOUR EAR", "gap": 0.3},
            {"line": "Your brain reads that as falling. It's why most astronauts get sick in space.", "shot": "fall",
             "callout": "YOU FEEL LIKE FALLING", "gap": 0.3},
            {"line": "Then gravity snaps back, and everything drops at once.", "shot": "drop",
             "callout": "GRAVITY IS BACK", "gap": 0.3},
            {"line": "Time's up. You land on your feet. But after five minutes, you'd fall from one and a half "
                     "kilometres.", "shot": "timesup", "callout": "TIME'S UP", "gap": 0.4},
            {"line": "What should switch off next? Comment, and subscribe to see it.", "shot": "end", "gap": 0.5},
        ],
        "script": {
            "title": "What If Gravity Stopped for 5 Seconds? 🌍 #shorts",
            "tags": ["what if", "what if gravity stopped", "gravity", "no gravity for 5 seconds", "human body",
                     "inner ear", "5 seconds", "science shorts", "3d animation", "shorts"],
            "seo_description": (
                "What if gravity stopped for 5 seconds? You would not shoot into space. The Earth turns at about "
                "1,670 km/h (1,040 mph) at the equator, and with nothing holding you down you keep going in a "
                "straight line while the ground curves away: after 5 seconds you are about 40 cm (16 in) up, and "
                "so is everything else that is not fixed down. The otolith crystals in your inner ear, which tell "
                "the brain which way is down, stop pressing on their sensors, which is the feeling of falling "
                "that makes most astronauts space-sick. After 5 minutes the same sum puts you about 1.5 km up. "
                "This is a simplified 3D illustration of a thought experiment; gravity cannot switch off.\n\n"
                "The heights are our own calculation at the equator (rise = v squared x t squared / 2R).\n\n"
                "Sources: NASA on Earth's rotation speed; NASA on the vestibular system and space motion "
                "sickness; HowStuffWorks, 'What if Earth Lost Gravity for Five Seconds?'; Live Science, 'What If "
                "There Were No Gravity?'."),
        },
    },
    "venus": {
        "test_no": 7,
        "hook": "10 SECONDS ON VENUS",
        "music": "deep",
        "end_card": DROP_CARD,
        "end_comment": DROP_COMMENT,
        # he drifts down through the first two lines; the clock starts when his feet touch
        "clock": [(10, 10), (10, 10), (10, 7), (7, 4), (4, 1), (1, 0), (0, 0), None],
        "segments": [
            {"line": "Ten seconds on Venus. What's left of him?", "shot": "fall", "gap": 0.3},
            {"line": "The air is so thick, he sinks through it like water.", "shot": "thick",
             "callout": "AIR LIKE WATER", "gap": 0.3},
            {"line": "It presses ninety times harder than on Earth. His foam padding is crushed flat.",
             "shot": "press", "callout": "CRUSHED", "gap": 0.3},
            {"line": "It's four hundred and sixty degrees: hot enough to melt lead.", "shot": "heat",
             "callout": "465°C", "gap": 0.3},
            {"line": "But no oxygen means no flames. He doesn't burn. He bakes.", "shot": "bake",
             "callout": "NO OXYGEN = NO FIRE", "gap": 0.3},
            {"line": "Time's up. Baked and squeezed, but still in one piece.", "shot": "timesup",
             "callout": "TIME'S UP", "gap": 0.4},
            dict(DUMMY, line="...I miss the lava.", shot="miss", gap=0.45),
            {"line": DROP_LINE, "shot": "end", "gap": 0.5},
        ],
        "script": {
            "title": "10 Seconds on Venus 🔥 #shorts",
            "tags": ["venus", "what if you stood on venus", "surface of venus", "space", "what if", "10 seconds",
                     "crash test dummy", "science shorts", "3d animation", "shorts"],
            "seo_description": (
                "What happens to a crash-test dummy in 10 seconds on the surface of Venus? The air is about 96% "
                "carbon dioxide and so dense that a falling body drifts down slowly, the way the Soviet Venera "
                "landers did. The pressure is about 92 times Earth's (like being 900 m under the sea), which "
                "squeezes the air out of foam. The surface is about 465 C (870 F), hotter than the melting point "
                "of lead (327 C). With no free oxygen nothing burns with a flame: things bake and char. The "
                "longest any lander has lasted there is 127 minutes (Venera 13, 1982).\n\nSources: NASA Venus "
                "facts; Space.com and BBC Sky at Night Venus fact files; OpenStax Astronomy, 'The Massive "
                "Atmosphere of Venus'; Guinness World Records and the Venera programme records (Venera 13)."),
        },
    },
    "ocean": {
        "test_no": 8,
        "hook": "10 SECONDS, 11 KM DOWN",
        "music": "deep",
        "end_card": DROP_CARD,
        "end_comment": DROP_COMMENT,
        "clock": [(10, 10), (10, 8), (8, 6), (6, 4), (4, 1), (1, 0), (0, 0), None],
        "segments": [
            {"line": "Ten seconds on the ocean floor. What's left of him?", "shot": "sink", "gap": 0.3},
            {"line": "Eleven kilometres of water press down: a thousand times the pressure up top.", "shot": "press",
             "callout": "PRESSURE x1,100", "gap": 0.3},
            {"line": "Anything full of air gets crushed. His foam padding shrinks like a cup.", "shot": "foam",
             "callout": "AIR GETS CRUSHED", "gap": 0.3},
            {"line": "But he isn't flattened. Solid steel doesn't squeeze.", "shot": "solid",
             "callout": "NOT FLATTENED", "gap": 0.3},
            {"line": "It's two degrees, pitch black. And he's not alone.", "shot": "cold",
             "callout": "2°C. PITCH BLACK.", "gap": 0.3},
            {"line": "Time's up. Thinner, colder, and the locals are curious.", "shot": "timesup",
             "callout": "TIME'S UP", "gap": 0.4},
            dict(DUMMY, line="...Something's on my head.", shot="head", gap=0.45),
            {"line": DROP_LINE, "shot": "end", "gap": 0.5},
        ],
        "script": {
            "title": "10 Seconds at the Bottom of the Ocean 🌊 #shorts",
            "tags": ["mariana trench", "bottom of the ocean", "challenger deep", "deep sea pressure", "what if",
                     "10 seconds", "crash test dummy", "science shorts", "3d animation", "shorts"],
            "seo_description": (
                "What happens to a crash-test dummy in 10 seconds at the bottom of the Mariana Trench? The "
                "Challenger Deep is almost 11 km down, where the water presses with about 1,086 bar: more than "
                "1,000 times the pressure at the surface. Anything with air in it is crushed: a sealed drum "
                "implodes, and foam shrinks the way the foam cups scientists send down do. Solids and liquids "
                "barely compress, so a body is not flattened. It is 1 to 4 C and completely dark, and animals "
                "live there: amphipods and sea cucumbers have been found at these depths. A real person would "
                "not survive this.\n\nSources: NOAA Ocean Exploration (pressure and the shrinking foam cups); "
                "NOAA PMEL Challenger Deep mooring (depth, 2.5 C at the seafloor); Live Science and Deep Sea "
                "News on amphipods (Hirondellea gigas) in the Challenger Deep."),
        },
    },
}


def spec(name):
    s = SPECS[name]
    vid = f"dummy_{name}"
    script = dict(s["script"], format="short", hook=s["segments"][0]["line"],
                  body=" ".join(x["line"] for x in s["segments"][1:]),
                  cta=s["segments"][-1]["line"], category_id="28", ai_generated_visuals=False,
                  topic_category="Science")
    tail = SOURCES_TAIL
    if s.get("end_card"):                               # the "10 Seconds" series asks where, not what
        tail = tail.replace("comment what he should test next", "comment where we should drop him next").replace(
            "#mythbusting", "#whatif")
    script["seo_description"] = script["seo_description"] + s.get("tail", tail)
    return s, vid, script, os.path.join(HERE, "output", "blender", vid)


# ── voice / timing ───────────────────────────────────────────────────────────
def step_voice(name):
    import soundfile as sf
    s, vid, _, work = spec(name)
    os.makedirs(work, exist_ok=True)
    vo, starts, total = ms.build_voice(s["segments"], vid, voice=s.get("voice", NARRATOR), speed=s.get("speed", NARR_SPEED))
    x, sr = sf.read(vo)
    if x.ndim > 1:
        x = x.mean(axis=1)
    ends = []
    for i, st in enumerate(starts):
        nxt = starts[i + 1] if i + 1 < len(starts) else total
        seg = x[int(st * sr):int(nxt * sr)]
        loud = np.nonzero(np.abs(seg) > 0.02)[0]
        ends.append(st + (loud[-1] / sr if len(loud) else 0.0))
    n = int(round((total + 0.6) * FPS)) + 1
    data = {"starts": starts, "ends": ends, "total": total, "fps": FPS, "frames": n,
            "shots": [x["shot"] for x in s["segments"]]}
    if s.get("lipsync"):                                     # per frame: how open (loudness) and how wide (ee vs oo)
        hop = sr / FPS
        mouth, wide = [], []
        for q in range(n):
            seg = x[int(q * hop):int((q + 1) * hop)]
            if len(seg) < 32:
                mouth.append(0.0), wide.append(0.5)
                continue
            mouth.append(float(np.sqrt(np.mean(seg ** 2))))
            sp = np.abs(np.fft.rfft(seg * np.hanning(len(seg))))
            fq = np.fft.rfftfreq(len(seg), 1 / sr)
            c = float((sp * fq).sum() / (sp.sum() + 1e-9))
            wide.append(float(np.clip((c - 900) / 2200, 0, 1)))
        m = np.array(mouth)
        ref = np.percentile(m[m > 0.01], 90) if (m > 0.01).any() else 1.0
        data["mouth"] = [round(float(v), 3) for v in np.clip((m - 0.008) / ref, 0, 1)]
        data["wide"] = [round(v, 3) for v in wide]
    with open(os.path.join(work, "timing.json"), "w") as f:
        json.dump(data, f)
    print(name, "starts", [round(v, 2) for v in starts], "total", round(total, 2), "frames", n)


def _blender(name, *args):
    _, _, _, work = spec(name)
    subprocess.run([BLENDER_PY, os.path.join(HERE, "blender_dummy_anim.py"), name, os.path.join(work, "frames"),
                    os.path.join(work, "timing.json"), *map(str, args)], check=True)


# ── overlays ─────────────────────────────────────────────────────────────────
_cache = {}


def _font(size):
    return ImageFont.truetype(FONT_T, size)


def _img(work, idx):
    if _cache.get("idx") != (work, idx):
        _cache["img"] = Image.open(os.path.join(work, "frames", f"f_{idx:04d}.png")).convert("RGB").resize(
            (W, H), Image.LANCZOS)
        _cache["idx"] = (work, idx)
    return _cache["img"]


def _meter(d, x0, y0, w, h, frac, label, color):
    d.rounded_rectangle((x0, y0, x0 + w, y0 + h), radius=h // 2, fill=(20, 20, 24), outline=WHITE, width=4)
    if frac > 0.01:
        d.rounded_rectangle((x0 + 6, y0 + 6, x0 + 6 + (w - 12) * frac, y0 + h - 6), radius=(h - 12) // 2, fill=color)
    d.text((x0 + w / 2, y0 - 34), label, font=_font(54), fill=WHITE, anchor="mm", stroke_width=5, stroke_fill=DARK)


def extras(name, shot, t_in, d):
    """Small diagrams that make a number visible (drawn above y 1500)."""
    e = ms.ease
    if name == "penny" and shot in ("flutter", "terminal"):
        # speed climbs, then flattens: terminal velocity
        frac = min(1.0, 0.25 + 0.75 * (1 - np.exp(-1.6 * (t_in + (0 if shot == "flutter" else 4.0)))))
        frac = min(frac, 0.62)
        _meter(d, 190, 1150, 700, 64, frac, "PENNY'S SPEED", (235, 120, 50))      # clear of the penny (upper half)
        if shot == "terminal" and t_in > 0.6:
            d.text((W / 2, 1270), "...AND STAYS THERE", font=_font(58), fill=CREAM, anchor="mm", stroke_width=5,
                   stroke_fill=DARK)
    if name == "lava" and shot == "steel":                 # the two numbers side by side: the lava loses
        k = e(min(1.0, t_in / 0.6))
        _meter(d, 190, 1090, 700, 60, 0.78 * k, "THIS LAVA  1,170°C", (255, 110, 25))
        _meter(d, 190, 1225, 700, 60, 0.95 * k, "STEEL MELTS  ~1,400°C", (185, 195, 210))
    if name == "venus" and shot == "heat":
        k = e(min(1.0, t_in / 0.6))
        _meter(d, 190, 1090, 700, 60, 0.93 * k, "VENUS  465°C", (255, 110, 25))
        _meter(d, 190, 1225, 700, 60, 0.65 * k, "LEAD MELTS  327°C", (185, 195, 210))
    if name == "ocean" and shot == "press":
        k = e(min(1.0, t_in / 0.8))
        _meter(d, 70, 1150, 540, 60, 0.02 + 0.96 * k, f"PRESSURE  x{int(round(1 + 1099 * k)):,}", (120, 190, 255))  # left: clear of the drum
    if name == "oxygen" and shot == "ears":
        k = e(min(1.0, t_in / 0.8))
        _meter(d, 190, 1150, 700, 60, 1.0 - 0.21 * k, f"AIR PRESSURE  {int(round(100 - 21 * k))}%", (120, 190, 255))
    if name == "gravity" and shot == "timesup" and t_in > 3.0:
        d.text((W / 2, 1180), "5 MINUTES = 1.5 KM UP", font=_font(84), fill=CREAM, anchor="mm", stroke_width=7,
               stroke_fill=DARK)
    if name == "venus" and shot == "press":
        k = e(min(1.0, t_in / 0.8))
        _meter(d, 190, 1150, 700, 60, 0.02 + 0.93 * k, f"PRESSURE  x{int(round(1 + 91 * k))}", (120, 190, 255))
    if name == "quicksand" and shot == "density":
        k = e(min(1.0, t_in / 0.6))
        _meter(d, 190, 480, 700, 60, 0.92 * k, "QUICKSAND  ~2 G/ML", (190, 140, 80))
        _meter(d, 190, 620, 700, 60, 0.46 * k, "HUMAN BODY  ~1 G/ML", (255, 200, 60))


def frame_for(name):
    s, vid, _, work = spec(name)
    timing = json.load(open(os.path.join(work, "timing.json")))
    segs = s["segments"]

    def frame(t, i, t_in, starts):
        if "checked" not in _cache:
            drift = max(abs(a - b) for a, b in zip(starts, timing["starts"]))
            if drift > 0.02:
                raise RuntimeError(f"voice moved {drift:.3f}s from the render -- re-run voice and frames")
            _cache["checked"] = True
        img = _img(work, min(int(t * FPS), timing["frames"] - 1)).copy()
        d = ImageDraw.Draw(img)
        seg = segs[i]
        if i == 0:                                          # the hook: alone in the first second (rule 18)
            hook = s["hook"]
            d.text((W / 2, 250), hook, font=_font(128 if len(hook) <= 18 else 112), fill=GOLD, anchor="mm",
                   stroke_width=9, stroke_fill=DARK)
            if t >= 1.0:
                ms.caption(d, 1380, seg["line"], size=62)
        elif seg["shot"] == "end":
            pop = 0.85 + 0.15 * ms.ease(min(1.0, t_in / 0.25))
            top, big = s.get("end_card", ("WHAT SHOULD WE TEST", "ON HIM NEXT?"))
            d.text((W / 2, 260), top, font=_font(int(104 * pop)), fill=GOLD, anchor="mm",
                   stroke_width=8, stroke_fill=DARK)
            d.text((W / 2, 380), big, font=_font(int(150 * pop)), fill=WHITE, anchor="mm",
                   stroke_width=9, stroke_fill=DARK)
            if (s.get("test_no") or s.get("sub_text")) and t_in > 0.3:   # subscribe, with a reason: the next one
                k = 0.85 + 0.15 * ms.ease(min(1.0, (t_in - 0.3) / 0.25))
                txt = s.get("sub_text") or f"SUBSCRIBE FOR TEST #{s['test_no'] + 1}"
                f = _font(int(84 * k))
                tw = d.textlength(txt, font=f)
                d.rounded_rectangle((W / 2 - tw / 2 - 44, 1180 - 62 * k, W / 2 + tw / 2 + 44, 1180 + 62 * k),
                                    radius=int(62 * k), fill=(204, 0, 0), outline=WHITE, width=5)
                d.text((W / 2, 1184), txt, font=f, fill=WHITE, anchor="mm")
            if t_in > 0.5:
                d.text((W / 2, 1420), "COMMENT BELOW", font=_font(96), fill=CREAM, anchor="mm",
                       stroke_width=7, stroke_fill=DARK)
        else:
            if s.get("test_no"):                            # the series name, so viewers remember it (not in second 1)
                d.text((24, 62), f"DUMMY TEST #{s['test_no']}", font=_font(56), fill=GOLD, stroke_width=5,
                       stroke_fill=DARK)
            if seg.get("callout"):
                pop = 0.85 + 0.15 * ms.ease(min(1.0, t_in / 0.22))
                txt = seg["callout"]
                d.text((W / 2, 250), txt, font=_font(int((124 if len(txt) <= 18 else 104) * pop)), fill=GOLD,
                       anchor="mm", stroke_width=8, stroke_fill=DARK)
            extras(name, seg["shot"], t_in, d)
            ms.caption(d, 1380, seg["line"], size=62)
        if s.get("clock") and s["clock"][i]:
            clock(d, s["clock"][i], t, starts, i, timing["total"])
        ms.watermark(d)
        return np.array(img)
    return frame


def clock_value(span, t, starts, i, total):
    """Story-time seconds left: runs from span[0] to span[1] across segment i."""
    a = starts[i]
    b = starts[i + 1] if i + 1 < len(starts) else total
    u = min(1.0, max(0.0, (t - a) / max(0.01, b - a)))
    return int(round(span[0] + (span[1] - span[0]) * u))


def clock(d, span, t, starts, i, total):
    """The countdown: top right, clear of the badge and the callout; red from 0:30, pulsing from 0:10."""
    v = clock_value(span, t, starts, i, total)
    red = v <= 30
    pulse = 1.0 + (0.08 * abs(np.sin(t * 2 * np.pi)) if v <= 10 else 0.0)
    w, h = 250 * pulse, 120 * pulse
    cx, cy = W - 165, 130
    d.rounded_rectangle((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), radius=int(26 * pulse), fill=(15, 15, 18),
                        outline=(230, 30, 30) if red else WHITE, width=6)
    d.text((cx, cy + 2), f"{v // 60}:{v % 60:02d}", font=_font(int(104 * pulse)),
           fill=(235, 35, 35) if red else WHITE, anchor="mm")


# ── sound ────────────────────────────────────────────────────────────────────
def sound_for(name):
    s, _, _, work = spec(name)
    segs = s["segments"]
    shot_at = lambda shot, starts: starts[[x["shot"] for x in segs].index(shot)]

    def events(starts, total):
        ev = []
        for k, seg in enumerate(segs):
            if k:
                ev.append((starts[k] - 0.05, sfx.whoosh(0.25, 0.16)))
            if k and seg.get("callout"):
                ev.append((starts[k] + 0.05, sfx.pop(0.28)))
        if name == "penny":
            # A noise bed under narration must stay far below the voice (the first mix had this wind only
            # ~5 dB under it and the owner could not hear the narrator): quiet, and gone by the first cut.
            ev.append((0.0, sfx.wind(starts[1], 0.09)))                      # falling air from frame 1
            ev.append((shot_at("hit", starts) - 0.32, sfx.clink(0.6)))
            ev.append((shot_at("roof", starts) + 0.4, sfx.wind(1.6, 0.05)))
        if name == "hail":
            ev.append((0.0, sfx.rip(0.3, 0.6)))
            ev.append((0.18, sfx.crack(0.85)))
            for j in range(6):
                ev.append((shot_at("pea", starts) + 0.15 + 0.33 * j, sfx.tick(1.6, 0.25)))
            ev.append((shot_at("golf", starts) + 0.2, sfx.thump(0.7)))
            ev.append((shot_at("baseball", starts) + 0.25, sfx.rip(0.35, 0.6)))
            ev.append((shot_at("record", starts) + 0.35, sfx.crack(0.9)))
        if name == "quicksand":
            # Under narration: kept >= 12 dB below the voice in the speech band (voice_clarity, rule 19).
            ev.append((0.0, sfx.squelch(0.6, 0.3)))
            ev.append((0.9, sfx.squelch(0.5, 0.18)))
            ev.append((shot_at("pull", starts) + 0.4, sfx.squelch(0.7, 0.1)))
            ev.append((shot_at("wiggle", starts) + 0.3, sfx.squelch(0.45, 0.12)))
            ev.append((shot_at("tide", starts) + 0.1, sfx.splash(0.08)))
        if name == "lightning":
            # the strike is the opening; replays and the burst are kept short and quiet under narration (rule 19)
            ev.append((0.0, sfx.thunder(3.0, 0.9)))
            ev.append((0.04, sfx.zap(0.45, 0.16)))
            ev.append((shot_at("jump", starts) + 8 / FPS, sfx.thunder(2.4, 0.55, crack_amp=0.35)))
            ev.append((shot_at("jump", starts) + 14 / FPS, sfx.zap(1.2, 0.07)))
            ev.append((shot_at("shell", starts) - 0.25, sfx.zap(0.4, 0.12)))
            dmg = shot_at("damage", starts)
            ev.append((dmg + 10 / FPS, sfx.thump(0.7)))
            ev.append((dmg + 10 / FPS, sfx.pop(0.3)))
            mid = dmg + ((shot_at("radio", starts) - dmg) * FPS // 2) / FPS
            ev.append((mid + 6 / FPS, sfx.zap(0.5, 0.12)))
            rad = shot_at("radio", starts)
            for f in (4, 16):
                ev.append((rad + f / FPS, sfx.tick(1.4, 0.18)))
            cv = shot_at("convertible", starts)
            ev.append((cv + 22 / FPS, sfx.thunder(2.5, 0.35, crack_amp=0.0)))
            ev.append((shot_at("end", starts) - 3 / FPS, sfx.thunder(2.6, 0.85, crack_amp=0.7)))
        if name == "sinking":
            # the splash is the opening; under narration everything stays short and quiet (rule 19)
            ev.append((0.0, sfx.plunge(0.85)))
            end_t = shot_at("end", starts)
            t, step = 1.0, 1.0                                   # the clock ticks; faster once it turns red
            while t < end_t - 0.3:
                ev.append((t, sfx.tick(1.7, 0.07 if t < shot_at("window", starts) else 0.09)))
                step = 0.5 if t >= shot_at("stuck", starts) else 1.0
                t += step
            door = shot_at("door", starts)
            for f in range(8, int((shot_at("window", starts) - door) * FPS) - 4, 10):
                ev.append((door + f / FPS, sfx.thump(0.22)))     # shoulder into the door
            win = shot_at("window", starts)
            ev.append((win + 14 / FPS, sfx.clink(0.12)))         # belt off
            ev.append((win + 36 / FPS, sfx.tick(0.8, 0.22)))     # window button
            stk = shot_at("stuck", starts)
            for f in range(2, 40, 7):
                ev.append((stk + f / FPS, sfx.tick(0.9, 0.16)))  # pressing a dead button
            ev.append((stk + 19 / FPS, sfx.zap(0.35, 0.08)))     # the power dies
            out = shot_at("out", starts)
            ev.append((out + 3 / FPS, sfx.crack(0.6)))           # the glass shatters
            ev.append((out + 5 / FPS, sfx.splash(0.3)))          # the river pours in
            ev.append((shot_at("surface", starts) + 0.05, sfx.splash(0.12)))
        if name == "lava":
            # the landing is the opening; the fire is a low roar and high crackle that leaves the speech band free
            ev.append((0.0, sfx.thump(0.8)))
            ev.append((0.02, sfx.sizzle(1.3, 0.3)))
            ev.append((20 / FPS, sfx.squelch(0.5, 0.14)))        # he sits down in it
            burn, end_t = shot_at("burn", starts), shot_at("end", starts)
            ev.append((burn + 1 / FPS, sfx.whoosh(0.5, 0.22)))   # he catches
            ev.append((burn + 2 / FPS, sfx.fire(total - burn - 0.2, 0.16)))
            strip = shot_at("strip", starts)
            for f in (8, 18, 30, 42, 58):                        # each piece of skin going
                ev.append((strip + f / FPS, sfx.sizzle(0.35, 0.14)))
            ev.append((shot_at("steel", starts) + 0.1, sfx.clink(0.16)))
            ev.append((shot_at("timesup", starts) + 0.02, sfx.clink(0.3)))
        if name == "lavayou":
            hit = 13 / FPS
            ev.append((0.0, sfx.wind(hit, 0.06)))                # the fall
            ev.append((hit, sfx.thump(0.8)))
            ev.append((hit + 0.02, sfx.sizzle(1.2, 0.28)))
            ev.append((hit + 20 / FPS, sfx.squelch(0.5, 0.14)))
            skin, steam, fat = (shot_at(x, starts) for x in ("skin", "steam", "fat"))
            ev.append((skin + 8 / FPS, sfx.sizzle(0.9, 0.2)))    # the skin goes
            for j in range(4):                                   # steam jets
                ev.append((steam + (4 + 14 * j) / FPS, sfx.sizzle(0.5, 0.2)))
            ev.append((steam + 10 / FPS, sfx.fire(total - steam - 0.5, 0.15)))
            ev.append((fat + 10 / FPS, sfx.whoosh(0.5, 0.2)))    # the fat catches
            ev.append((shot_at("bone", starts) + 0.1, sfx.clink(0.16)))
            ev.append((shot_at("timesup", starts) + 0.02, sfx.clink(0.3)))
        if name == "oxygen":
            ev.append((9 / FPS, sfx.whoosh(0.6, 0.3)))           # the oxygen goes
            ev.append((0.0, sfx.fire(shot_at("fire", starts) + 0.7, 0.07)))
            ears = shot_at("ears", starts)
            ev.append((ears + 6.17, sfx.pop(0.3))), ev.append((ears + 6.36, sfx.pop(0.22)))   # after "Your ears pop."
            ev.append((shot_at("fire", starts) + 18 / FPS, sfx.sizzle(1.0, 0.16)))   # the campfire dies
            ev.append((shot_at("back", starts) + 5 / FPS, sfx.whoosh(0.4, 0.16)))
            ev.append((shot_at("faint", starts) + 49 / FPS, sfx.thump(0.5)))         # your knees hit the ground
            tu = shot_at("timesup", starts)
            ev.append((tu + 0.02, sfx.clink(0.3)))
            ev.append((tu + 10 / FPS, sfx.whoosh(0.7, 0.26)))    # the oxygen is back
        if name == "gravity":
            ev.append((8 / FPS, sfx.riser(0.9, 0.22)))           # the switch
            ev.append((shot_at("fall", starts), sfx.wind(shot_at("drop", starts) - shot_at("fall", starts), 0.05)))
            back = shot_at("drop", starts) + 17 / FPS            # everything lands
            ev.append((back, sfx.thump(0.8)))
            for j in range(5):
                ev.append((back + 0.04 + 0.07 * j, sfx.clink(0.12)))
            ev.append((shot_at("timesup", starts) + 0.02, sfx.clink(0.3)))
        if name == "friction":
            ev.append((6 / FPS, sfx.whoosh(0.5, 0.26)))          # the foot shoots away
            ev.append((30 / FPS, sfx.thump(0.6)))                # down into the splits
            walk = shot_at("walk", starts)
            for j in range(5):
                ev.append((walk + 1.2 + 0.3 * j, sfx.whoosh(0.2, 0.08)))   # shoes skating
            ph = shot_at("phone", starts)
            ev.append((ph + 20 / FPS, sfx.whoosh(0.3, 0.14)))
            ev.append((ph + 31 / FPS, sfx.clink(0.25)))          # the phone hits the road...
            la = shot_at("laces", starts)
            ev.append((la + 1.4, sfx.whoosh(0.35, 0.1)))
            na = shot_at("nails", starts)
            for j in range(4):
                ev.append((na + 0.5 + 0.25 * j, sfx.pop(0.16)))   # nails popping
            ev.append((na + 2.1, sfx.thump(0.45)))               # planks down
            ev.append((na + 2.2, sfx.clink(0.18)))
            ev.append((shot_at("timesup", starts) + 0.02, sfx.clink(0.3)))
        if name == "venus":
            ev.append((0.0, sfx.wind(starts[2] - 0.6, 0.07)))    # thick air rushing past as he sinks through it
            land = starts[2] - 26 / FPS
            ev.append((land, sfx.thump(0.55)))
            ev.append((land + 0.03, sfx.squelch(0.5, 0.12)))     # a soft, dusty touchdown
            press = shot_at("press", starts)
            ev.append((press + 12 / FPS, sfx.rip(0.45, 0.4)))    # the foam gives
            ev.append((press + 24 / FPS, sfx.rip(0.3, 0.22)))
            ev.append((press + 14 / FPS, sfx.thump(0.4)))
            heat = shot_at("heat", starts)
            ev.append((heat + 10 / FPS, sfx.sizzle(1.6, 0.2)))   # the lead goes
            ev.append((shot_at("bake", starts) + 0.2, sfx.sizzle(2.2, 0.14)))
            ev.append((shot_at("timesup", starts) + 0.02, sfx.clink(0.3)))
        if name == "ocean":
            ev.append((0.0, sfx.sonar(0.3, 3700)))               # pitched above the speech band: at 1180 Hz it buried the narrator
            ev.append((0.0, sfx.wind(starts[1] - 0.8, 0.05)))    # water rushing past as he sinks
            land = starts[1] - 20 / FPS
            ev.append((land, sfx.thump(0.5)))
            press = shot_at("press", starts)
            ev.append((press + 16 / FPS, sfx.crack(0.55)))       # the sealed drum implodes
            ev.append((press + 16 / FPS, sfx.deep_boom(0.6)))
            foam = shot_at("foam", starts)
            ev.append((foam + 10 / FPS, sfx.rip(0.45, 0.35)))    # his foam gives
            ev.append((foam + 22 / FPS, sfx.rip(0.3, 0.2)))
            solid = shot_at("solid", starts)
            for f in (30, 38):
                ev.append((solid + f / FPS, sfx.clink(0.22)))    # he knocks on his own chest
            ev.append((shot_at("cold", starts) + 0.1, sfx.sonar(0.22, 3700)))
            ev.append((shot_at("timesup", starts) + 0.02, sfx.clink(0.3)))
        if s.get("clock") and name != "sinking":                 # one tick each time the countdown drops a second
            prev, t = None, 0.0
            while t < shot_at("end", starts):
                i = max(j for j in range(len(starts)) if starts[j] <= t + 1e-6) if t >= starts[0] else 0
                v = clock_value(s["clock"][i], t, starts, i, total) if s["clock"][i] else None
                if prev is not None and v is not None and v != prev:
                    ev.append((t, sfx.tick(1.7 if v > 3 else 2.1, 0.09 if v > 3 else 0.13)))
                prev = v if v is not None else prev
                t += 1 / FPS
        ev.append((shot_at("end", starts) + 0.05, sfx.pop(0.4)))
        return ev
    return events


def voice_clarity(name, music_vol=0.09, min_db=12.0, win=0.5):
    """Speech-band (300-3400 Hz) level of the narration vs everything under it (sfx + music), per window
    where the narrator is speaking, with the same gains render_short mixes them at. A sustained bed less
    than `min_db` under the voice makes words hard to hear; returns the failing windows."""
    import numpy as np
    import soundfile as sf
    import config
    import music_generator
    s, vid, _, _ = spec(name)
    def mono(path, sr_to):
        tmp = os.path.join(config.AUDIO_DIR, f"_clarity_{os.getpid()}.wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-ac", "1", "-ar", str(sr_to), tmp], check=True)
        x, _ = sf.read(tmp)
        os.remove(tmp)
        return x
    sr = 24000
    vo = mono(os.path.join(config.AUDIO_DIR, f"{vid}_vo.wav"), sr) * 1.5
    n = len(vo)
    def fit(x):
        return np.pad(x, (0, max(0, n - len(x))))[:n]
    bed = fit(mono(os.path.join(config.AUDIO_DIR, f"{vid}_sfx.wav"), sr) * 0.75)
    mp = music_generator.get_original_music(s["music"], audio_dir=config.AUDIO_DIR, duration=n / sr + END_GAP)
    bed = bed + fit(mono(mp, sr) * music_vol)
    def band_db(x):
        X = np.fft.rfft(x)
        f = np.fft.rfftfreq(len(x), 1 / sr)
        X[(f < 300) | (f > 3400)] = 0
        return 20 * np.log10(np.sqrt(np.mean(np.fft.irfft(X, len(x)) ** 2)) + 1e-12)
    w = int(win * sr)
    low = []                               # (time, gap) for speech windows where the bed is too close
    for i in range(0, n - w, w):
        v = band_db(vo[i:i + w])
        if v < -32:                        # narrator not clearly speaking here (pause, breath, word tail)
            continue
        gap = float(v - band_db(bed[i:i + w]))
        if gap < min_db:
            low.append((round(i / sr, 1), round(gap, 1)))
    # A one-window dip is a short hit (pop, clink, whoosh at a cut): fine. A run of 2+ windows (>= 1 s)
    # is a bed burying the narration: that fails.
    times = {t for t, _ in low}
    bad = [(t, g) for t, g in low if round(t - win, 1) in times or round(t + win, 1) in times]
    print(f"voice clarity {name}: {'FAIL, narration buried at ' + str(bad) if bad else 'OK'}"
          f" (short hits under {min_db:.0f} dB: {[x for x in low if x not in bad] or 'none'})")
    return bad


def step_compose(name):
    s, vid, script, _ = spec(name)
    out, vo = ms.render_short(script, s["segments"], vid, frame_for(name), voice=s.get("voice", NARRATOR), speed=s.get("speed", NARR_SPEED),
                              music_style=s["music"], sfx_fn=sound_for(name), music_vol=0.09, hook_hit=False)
    tmp = out.replace(".mp4", "_norm.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", out, "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5:LRA=9",
                    "-ar", "48000", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", tmp], check=True)
    os.replace(tmp, out)
    print(out)
    return out


def step_sheet(name):
    import config
    import first_second_sheet as fss
    _, vid, _, work = spec(name)
    out = fss.sheet(os.path.join(work, "first_second.png"), [os.path.join(config.VIDEOS_DIR, f"{vid}.mp4")])
    print(out)


def step_preview(name, frames):
    """Look test WITH the real text on top (rule 22): small stills of the given frames, drawn over with the hook,
    label, meters, clock and caption exactly as compose will draw them. Run it before the full render: whatever
    the line names must be in clear view, not under the words about it."""
    _, _, _, work = spec(name)
    timing = json.load(open(os.path.join(work, "timing.json")))
    env = dict(os.environ, DUMMY_RES="270x480", DUMMY_SAMPLES=os.environ.get("DUMMY_SAMPLES", "6"))
    subprocess.run([BLENDER_PY, os.path.join(HERE, "blender_dummy_anim.py"), name, os.path.join(work, "frames"),
                    os.path.join(work, "timing.json"), "still", *map(str, frames)], check=True, env=env)
    frame, starts, tiles = frame_for(name), timing["starts"], []
    for f in frames:
        t = (f + 0.5) / FPS
        i = max([j for j, st in enumerate(starts) if st <= t] or [0])
        _cache["img"] = Image.open(os.path.join(work, "stills", f"s_{f:04d}.png")).convert("RGB").resize(
            (W, H), Image.LANCZOS)
        _cache["idx"] = (work, min(int(t * FPS), timing["frames"] - 1))
        tiles.append(Image.fromarray(frame(t, i, t - starts[i], starts)).resize((360, 640), Image.LANCZOS))
    _cache.pop("idx", None)
    cols = min(6, len(tiles))
    rows = -(-len(tiles) // cols)
    sheet = Image.new("RGB", (cols * 364, rows * 644), (0, 0, 0))
    for j, im in enumerate(tiles):
        sheet.paste(im, ((j % cols) * 364, (j // cols) * 644))
    out = os.path.join(work, "preview.png")
    sheet.save(out)
    print(out)


# ── publish (owner approved all three, one a day) ────────────────────────────
UPLOADS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dummy_uploads.json")   # tracked in git


def _uploads():
    return json.load(open(UPLOADS)) if os.path.exists(UPLOADS) else {}


def upload(name, at=None):
    """Upload private with YouTube's own release time set to the slot (`at`, RFC 3339 UTC), add captions and
    the frame-1 thumbnail, and record the id in git. If this machine is lost before the slot, YouTube still
    releases it and `golive` can finish from the recorded id."""
    import datetime
    import config
    import phase5_upload as p5
    import pro_shorts_creator as psc
    s, vid_id, script, work = spec(name)
    out = os.path.join(config.VIDEOS_DIR, f"{vid_id}.mp4")
    vo = os.path.join(config.AUDIO_DIR, f"{vid_id}_vo.wav")
    at = at or (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    sc = dict(script, video_title=script["title"], publish_at=at)
    config.UPLOAD_PRIVACY = "private"
    url, _ = p5.upload_to_youtube(out, sc, {"title": script["title"], "subject": script["hook"],
                                            "category": "Science"})
    vid = url.rsplit("=", 1)[-1]
    srt = os.path.splitext(vo)[0] + ".srt"
    try:                                   # a caption failure must not leave the video stuck private
        psc.generate_srt(psc.get_word_timestamps(vo), srt)
        p5.upload_captions(vid, srt)
    except Exception as e:
        print("captions failed:", e)
    thumb = os.path.join(config.OUTPUT_DIR, "thumbnails", f"{vid_id}.jpg")      # frame 1 IS the thumbnail
    os.makedirs(os.path.dirname(thumb), exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "0.3", "-i", out, "-frames:v", "1", "-q:v", "3", thumb],
                   check=True)
    p5.upload_thumbnail(vid, thumb)
    # The hail upload came back with 0 tags (still 0 after processing) while the same code gave the penny 10:
    # read them back and set them again if YouTube dropped them.
    import time
    yt = p5.get_youtube_client()
    time.sleep(10)
    sn = yt.videos().list(part="snippet", id=vid).execute()["items"][0]["snippet"]
    if not sn.get("tags") and script.get("tags"):
        body = {k: sn[k] for k in ("title", "description", "categoryId", "defaultLanguage", "defaultAudioLanguage")
                if k in sn}
        body["tags"] = script["tags"]
        yt.videos().update(part="snippet", body={"id": vid, "snippet": body}).execute()
        print("tags were dropped on upload; set again:", len(script["tags"]))
    ups = _uploads()
    ups[name] = {"id": vid, "publishAt": at, "title": script["title"]}
    with open(UPLOADS, "w") as f:
        json.dump(ups, f, indent=1, ensure_ascii=False)
    print("uploaded", vid, "release", at)
    return vid


def golive(name, vid=None):
    """Flip the uploaded Short public now, post the seeded comment, read everything back."""
    import config
    import phase5_upload as p5
    s, vid_id, script, work = spec(name)
    vid = vid or _uploads()[name]["id"]
    p5.push_video_public(vid)
    p5.post_engagement_comment(vid, s.get("end_comment", END_COMMENT))
    import time
    time.sleep(20)                         # reads lag right after upload (LESSONS: re-read before "fixing")
    yt = p5.get_youtube_client()
    v = yt.videos().list(part="snippet,status,contentDetails", id=vid).execute()["items"][0]
    caps = yt.captions().list(part="snippet", videoId=vid).execute().get("items", [])
    check = {"id": vid, "url": f"https://youtube.com/shorts/{vid}", "title": v["snippet"]["title"],
             "category": v["snippet"]["categoryId"], "privacy": v["status"]["privacyStatus"],
             "publishAt": v["status"].get("publishAt"), "madeForKids": v["status"].get("selfDeclaredMadeForKids"),
             "synthetic": v["status"].get("containsSyntheticMedia"), "duration": v["contentDetails"]["duration"],
             "captions": [c["snippet"]["language"] for c in caps], "tags": len(v["snippet"].get("tags", []))}
    print(json.dumps(check, indent=1, ensure_ascii=False))
    with open(os.path.join(work, "published.json"), "w") as f:
        json.dump(check, f, indent=1, ensure_ascii=False)
    return vid


if __name__ == "__main__":
    cmd, name = sys.argv[1], sys.argv[2]
    if cmd == "voice":
        step_voice(name)
    elif cmd == "still":
        _blender(name, "still", *sys.argv[3:])
    elif cmd == "frames":
        _blender(name, sys.argv[3], sys.argv[4])
    elif cmd == "compose":
        step_compose(name)
        voice_clarity(name)
    elif cmd == "clarity":
        voice_clarity(name)
    elif cmd == "sheet":
        step_sheet(name)
    elif cmd == "preview":                 # preview NAME F1 F2 ...: look-test stills with the real text on top
        step_preview(name, [int(x) for x in sys.argv[3:]])
    elif cmd == "publish":                 # upload and go live now
        golive(name, upload(name))
    elif cmd == "upload":                  # upload NAME [RELEASE_RFC3339]
        upload(name, sys.argv[3] if len(sys.argv) > 3 else None)
    elif cmd == "golive":
        golive(name)
    else:
        print(__doc__)
