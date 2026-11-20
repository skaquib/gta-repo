"""Assemble the Madrid derby Short: fast cuts (~2.4s) over licensed player
photos, designed stat cards and checked football clips, placed against the
measured word timings:

  "tackle" 3.6 | "second half" 8.3 | "the box" 11.8 | penalty 14.8
  Grimaldo 16.1 | "recovered" 18.8 | Jonathan 19.8 | "third" 21.2
  "finished" 25.2 | "second" 27.3 | "behind" 28.7 | "ahead" 30.8
  "twice" 32.7 | CTA 34.3

One downloaded clip tagged "football referee red card" is an empty pitch
(the vision gate rejected every other candidate for showing no card), so the
RED CARD graphic carries that beat instead.
"""
import os
import re

import config

config.assert_safe_pipeline()

import pro_shorts_creator as psc
from logger import log
from run_derby_short import SCRIPT

LOG = os.path.join(config.OUTPUT_DIR, "logs", "derby_audio_stdout.log")
OUT = os.path.join(config.VIDEOS_DIR, "derby_short.mp4")
RC = os.path.join(config.OUTPUT_DIR, "raw_clips")

if __name__ == "__main__":
    text = open(LOG, encoding="utf-8", errors="replace").read()
    vo = re.findall(r"VO_PATH=(.+)", text)[-1].strip()
    music = re.findall(r"MUSIC_PATH=(.+)", text)[-1].strip() or None
    p = lambda n: os.path.join(RC, n)
    HUI, GRI, DAV, RUD = p("photo_huijsen.mp4"), p("photo_grimaldo.mp4"), p("photo_david.mp4"), p("photo_rudiger.mp4")
    CRED, CGRI, CDAV, CTAB = p("card_red.mp4"), p("card_grimaldo.mp4"), p("card_david.mp4"), p("card_table.mp4")
    NIGHT, AERIAL = p("pexels_2657261.mp4"), p("pexels_39134046.mp4")
    MATCH, REF = p("pexels_15449383.mp4"), p("pexels_32614272.mp4")
    FANS1, FANS2 = p("pexels_37635975.mp4"), p("pexels_4036306.mp4")
    for f in [vo, HUI, GRI, DAV, RUD, CRED, CGRI, CDAV, CTAB, NIGHT, AERIAL, MATCH, REF, FANS1, FANS2]:
        assert os.path.exists(f), f
    order = [NIGHT, MATCH,             # hook: derby, "one tackle"
             AERIAL, HUI, REF, CRED,   # Metropolitano / Huijsen / the box / red + pen
             GRI, CGRI,                # Grimaldo scores it, 1-0
             DAV, CDAV,                # Jonathan David, 2-0, 3 in 3
             RUD, CTAB, CTAB, FANS1,   # Rudiger late / table / lost twice
             CRED, FANS2, NIGHT]       # CTA: was it a red card?
    log(f"Assembling derby Short: {len(order)} shots, {len(set(order))} sources")
    psc.assemble(order, SCRIPT, vo, music, OUT)
    log(f"ASSEMBLED -> {OUT}")
    print("VO_PATH=" + vo)
