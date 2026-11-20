"""
run_tennisyellow_short.py — built 2026-09-25, for SCHEDULED publish.

WHY THIS TOPIC (channel data, not a guess): the four best videos this channel
has ever made are all "Why is X...?" facts -- marathon 26.2 (1,687), bowling
lane 60ft (1,124), football 90 minutes (1,065), basketball hoop 10ft (819).
News Shorts, even with real photos and fast cuts, land at 185-308. The same
format is trending globally right now: "THE REAL REASON GOLF BALLS ARE WHITE"
(1.3M, three countries) on 2026-09-25. A tennis ball is something almost
everyone has held, and its colour is odd enough to wonder about -- the test
the cricket-over Short (79 views) failed.

VERIFIED (Wikipedia "Tennis ball"; Reader's Digest; Tennis365; Yahoo Sports;
History Facts):
- Tennis balls were white (and sometimes black) before 1972.
- On colour television the white ball was hard for viewers to follow.
- The ITF approved "optic yellow" in 1972; the first Grand Slam use was the
  1973 US Open.
- Wimbledon kept white balls until 1986, the last major to switch.
- The change is widely credited to David Attenborough, then controller of
  BBC Two, who wanted the ball to show up in colour.
NOT CLAIMED: the Attenborough role is reported rather than documented in the
ITF minutes, so the script says "is credited to".
"""
import os

import config

config.assert_safe_pipeline()

import pro_shorts_creator as psc
from logger import log

SCRIPT = {
    "hook": "Tennis balls were white for about a hundred years. One television problem changed that.",
    "hook_card": "WHY ARE THEY YELLOW?",
    "body": (
        "When tennis moved to colour television, broadcasters had a problem. "
        "A white ball, moving fast, against a pale court, was almost "
        "impossible for viewers at home to follow. The fix is credited to "
        "David Attenborough, then the controller of BBC Two, who wanted a "
        "ball you could actually see. In nineteen seventy two, the "
        "International Tennis Federation approved a new colour: optic yellow. "
        "It was used at a Grand Slam for the first time at the nineteen "
        "seventy three US Open. And Wimbledon? Wimbledon refused, and kept "
        "using white balls until nineteen eighty six."
    ),
    "cta": "Did you know Wimbledon held out that long? Comment and subscribe!",
    "title": "Why Are Tennis Balls Yellow? A TV Problem Changed the Sport 🎾😳 #shorts #tennis",
    "tags": ["tennis", "tennis balls", "optic yellow", "wimbledon", "sports facts",
             "why are tennis balls yellow", "shorts", "david attenborough", "itf"],
    "seo_description": (
        "Tennis balls were white until colour TV made them hard to follow. The ITF "
        "approved optic yellow in 1972 -- credited to David Attenborough at BBC Two -- "
        "first used at a major at the 1973 US Open. Wimbledon held out with white balls "
        "until 1986. #tennis #sportsfacts"
    ),
    "queries": ["tennis ball close up", "tennis court", "tennis player serving"],
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
