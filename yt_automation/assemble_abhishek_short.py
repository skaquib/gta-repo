"""Assemble the Abhishek Sharma Short: fast cuts (~2.4s) over stat cards,
Rohit Sharma's licensed photo and contact-sheet-checked cricket clips, each
placed against the measured word timings of the voiceover:

  Abhishek 9.0s | Rohit 12.2s | "stood since 2017" 15.2s | Zimbabwe 19.4s
  New Zealand 21.2s | "beat them both" 24.2s | "finished" 24.7s
  "swept" 28.8s | CTA 31.1s
"""
import os
import re

import config

config.assert_safe_pipeline()

import pro_shorts_creator as psc
from logger import log
from run_abhishek_short import SCRIPT

LOG = os.path.join(config.OUTPUT_DIR, "logs", "abhishek_audio_stdout.log")
OUT = os.path.join(config.VIDEOS_DIR, "abhishek_short.mp4")
RC = os.path.join(config.OUTPUT_DIR, "raw_clips")

if __name__ == "__main__":
    text = open(LOG, encoding="utf-8", errors="replace").read()
    vo = re.findall(r"VO_PATH=(.+)", text)[-1].strip()
    music = re.findall(r"MUSIC_PATH=(.+)", text)[-1].strip() or None
    p = lambda name: os.path.join(RC, name)
    A, R, RCARD = p("card_100in30.mp4"), p("photo_rohit.mp4"), p("card_rohit.mp4")
    C, N, S = p("card_compare.mp4"), p("card_108.mp4"), p("card_series.mp4")
    B = p("pexels_32543231.mp4")   # batsman playing a shot
    M = p("pexels_15199714.mp4")   # big cricket stadium, aerial
    E = p("pexels_27745649.mp4")   # international cricket ground
    F = p("pexels_38641442.mp4")   # cricket crowd
    G = p("pexels_27308556.mp4")   # cricket ground aerial
    X = p("pexels_38481435.mp4")   # match in progress, aerial
    for f in [vo, A, R, RCARD, C, N, S, B, M, E, F, G, X]:
        assert os.path.exists(f), f
    # Open on action, not the card: the hook banner and the card's top line
    # collided at 1.3s in the first render.
    order = [B, A,                 # hook: 100 in 30 balls
             M, B, A,              # Delhi / Abhishek / hundred in 30
             R, RCARD,             # Rohit's record, since 2017
             E, C, C,              # Test-nation record: Raza, Allen, 33
             N, F,                 # 108 off 34, eleven sixes
             S,                    # swept 3-0
             B, X, G]              # CTA
    log(f"Assembling Abhishek Short: {len(order)} shots, {len(set(order))} sources")
    psc.assemble(order, SCRIPT, vo, music, OUT)
    log(f"ASSEMBLED -> {OUT}")
    print("VO_PATH=" + vo)
