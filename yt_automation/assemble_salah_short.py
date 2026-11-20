"""Assemble the Salah Short: fast cuts (~2.4s) over his licensed photo,
designed stat cards and contact-sheet-checked football clips, placed against
the measured word timings:

  "finished" 5.3 | Anfield 6.6 | goals 10.4 | Turkey 12.3 | Saturday 14.3
  hat-trick 17.0 | solo 18.3 | fourth 19.9 | seasons 23.9 | six 28.1
  seven 30.5 | charts 32.7 | CTA 34.1
"""
import os
import re

import config

config.assert_safe_pipeline()

import pro_shorts_creator as psc
from logger import log
from run_salah_short import SCRIPT

LOG = os.path.join(config.OUTPUT_DIR, "logs", "salah_audio_stdout.log")
OUT = os.path.join(config.VIDEOS_DIR, "salah_short.mp4")
RC = os.path.join(config.OUTPUT_DIR, "raw_clips")

if __name__ == "__main__":
    text = open(LOG, encoding="utf-8", errors="replace").read()
    vo = re.findall(r"VO_PATH=(.+)", text)[-1].strip()
    music = re.findall(r"MUSIC_PATH=(.+)", text)[-1].strip() or None
    p = lambda n: os.path.join(RC, n)
    SAL = p("photo_salah.mp4")
    LIV, FREE, HAT, STATS = p("card_liverpool.mp4"), p("card_free.mp4"), p("card_hattrick.mp4"), p("card_stats.mp4")
    NIGHT = p("pexels_2657261.mp4")     # packed stadium at night
    AERIAL = p("pexels_39134046.mp4")   # pitch from above
    MATCH = p("pexels_15449383.mp4")    # match action
    NET = p("pexels_10397876.mp4")      # ball hitting the net
    KEEPER = p("pexels_15436954.mp4")   # keeper beaten at the goal
    FANS1 = p("pexels_37635975.mp4")    # fans with flags
    FANS2 = p("pexels_4036306.mp4")     # packed terrace
    for f in [vo, SAL, LIV, FREE, HAT, STATS, NIGHT, AERIAL, MATCH, NET, KEEPER, FANS1, FANS2]:
        assert os.path.exists(f), f
    order = [SAL, FREE, NIGHT,          # hook: left Liverpool, free, "finished"
             LIV, LIV,                  # 9 years, 257 goals
             AERIAL, MATCH,             # Turkey / faced Galatasaray
             HAT, NET, HAT,             # hat-trick, solo runs, 4-0
             KEEPER, FANS1,             # the 10-season stat
             STATS, STATS,              # 7 goals, 2 assists, top
             SAL, FANS2, NIGHT]         # CTA
    log(f"Assembling Salah Short: {len(order)} shots, {len(set(order))} sources")
    psc.assemble(order, SCRIPT, vo, music, OUT)
    log(f"ASSEMBLED -> {OUT}")
    print("VO_PATH=" + vo)
