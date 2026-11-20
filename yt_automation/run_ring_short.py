"""
run_ring_short.py — built 2026-09-25. LIVE today.

FORMAT: "Why is X...?" curiosity facts. The 2026-09-25 multi-country trending
scan had few hard-news sports stories but showed this exact format winning
globally: "THE REAL REASON GOLF BALLS ARE WHITE" (1.3M, trending in 3
countries) and "Why Is There Electricity?" (3.5M). It is also this channel's
best series (marathon 1,687; bowling 1,124; 90 minutes 1,065). Combat sport
is topical too -- UFC 331 was trending in GB/AU/IN the same day.

VERIFIED (Wikipedia "Boxing ring"; World Boxing Association; Today I Found
Out; ScienceABC):
- Early fights had no fixed enclosure: spectators crowded round the fighters
  in a rough circle, sometimes scratched on the ground.
- The London Prize Ring Rules (1838) specified a ring "four-and-twenty feet
  square", formed of eight stakes and ropes.
- The word "ring" stayed anyway; the modern square is still nicknamed "the
  squared circle".
NOT CLAIMED: no invented reason for choosing 24 feet -- no source gives one.
"""
import os

import config

config.assert_safe_pipeline()

import pro_shorts_creator as psc
from logger import log

SCRIPT = {
    "hook": "A boxing ring is a square. So why does everyone call it a ring?",
    "hook_card": "WHY IS IT CALLED A RING?",
    "body": (
        "Because it used to be one. Before boxing had rules, there was no "
        "enclosure at all. A crowd simply formed a circle around the two "
        "fighters, sometimes scratched into the ground, and that circle was "
        "the ring. Then came the London Prize Ring Rules of eighteen thirty "
        "eight. They fixed the fighting area at twenty four feet square, made "
        "with eight stakes and ropes. The shape changed. The word never did. "
        "Nearly two hundred years later, fighters still walk into what people "
        "call the squared circle."
    ),
    "cta": "What other sports word makes no sense any more? Comment and subscribe!",
    "title": "A Boxing Ring Is a Square. So Why Is It Called a RING? 🥊😳 #shorts #boxing",
    "tags": ["boxing", "boxing ring", "squared circle", "sports facts", "shorts",
             "why is it called a ring", "boxing history", "ufc", "sportshistory"],
    "seo_description": (
        "Boxing rings are square, but the name comes from the days before rules, when a "
        "crowd formed a circle around the fighters. The London Prize Ring Rules of 1838 "
        "fixed the area at 24 feet square -- and the word 'ring' stuck. #boxing #sportsfacts"
    ),
    "queries": ["boxing ring", "boxing gloves training", "boxing gym"],
}


def build_audio():
    log("Generating voiceover (cloned voice)...")
    vo_path = psc.generate_voiceover(SCRIPT)
    from moviepy import AudioFileClip
    vo_dur = min(AudioFileClip(vo_path).duration + 1.5, 90.0)
    log("Generating background music...")
    music_path = psc.get_music(duration=vo_dur, script=SCRIPT)
    print("VO_PATH=" + vo_path, flush=True)
    print("MUSIC_PATH=" + (music_path or ""), flush=True)
    return vo_path, music_path


if __name__ == "__main__":
    build_audio()
