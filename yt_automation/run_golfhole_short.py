"""
run_golfhole_short.py — built 2026-09-25, for SCHEDULED publish.

WHY THIS TOPIC: the channel's "Why is X EXACTLY Y?" videos are its four best
ever, and golf already travels here -- "Why Dimpled Golf Balls Fly TWICE as
Far" did 927 views, well above the channel average. 4.25 inches is exactly
the kind of oddly specific number the format needs, and the answer is a
genuine accident.

VERIFIED (Golf Monthly "What size is the golf hole -- and how was it
decided?"; LiveAbout; GolfBit; researched 2026-09-12, re-used here):
- The first known hole-cutter was made at Royal Musselburgh in 1829, and is
  believed to have been built from a piece of drainpipe lying around the
  links, 4.25 inches across.
- When the R&A wrote the first national rules of golf in 1891 it fixed the
  hole diameter at 4.25 inches, the size that piece of pipe happened to be.
- Sources agree the original choice was arbitrary; the exact reasoning is
  lost.
NOT CLAIMED: no invented rationale about "fairness" or ball size -- the
sources say the reason is simply lost.
"""
import os

import config

config.assert_safe_pipeline()

import pro_shorts_creator as psc
from logger import log

SCRIPT = {
    "hook": "Every golf hole on earth is four and a quarter inches wide. Because of a piece of drainpipe.",
    "hook_card": "4.25 INCHES. WHY?",
    "body": (
        "Golf had no standard hole size for centuries. Groundsmen cut holes by "
        "hand, and they came out whatever size the tool made them. Then, in "
        "eighteen twenty nine, at Royal Musselburgh in Scotland, someone built "
        "the first hole cutter. The story is that they used a spare piece of "
        "drainpipe lying around the links. That pipe was four and a quarter "
        "inches across. In eighteen ninety one, when golf's rules were written "
        "down nationally for the first time, that measurement became the law. "
        "Every hole, at every course, in every major championship since, is "
        "the size of a random Scottish drainpipe."
    ),
    "cta": "Should the hole be bigger? Comment and subscribe!",
    "title": "Why Is a Golf Hole EXACTLY 4.25 Inches? Blame a Drainpipe ⛳😳 #shorts #golf",
    "tags": ["golf", "golf hole", "4.25 inches", "sports facts", "shorts",
             "golf history", "royal musselburgh", "randa", "why is a golf hole"],
    "seo_description": (
        "Every golf hole is 4.25 inches wide because of a hole-cutter built at Royal "
        "Musselburgh in 1829 -- reportedly from a spare piece of drainpipe. The R&A "
        "made it the standard in 1891, and it has never changed. #golf #sportsfacts"
    ),
    "queries": ["golf hole close up", "golf course green", "golf ball putting"],
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
