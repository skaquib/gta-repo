"""Re-assemble the invisible-trophy Short with fast cuts and real faces.

Reuses the voiceover, music and vision-gated stock clips from the first
build (read from its log) and adds licensed Wikimedia photos of the actual
people. With FAST_CUT_SECONDS=2.4 the shots below play in this order, one
per ~2.4s, lining up with the narration:

  hook   "India won the Asia Cup final, celebrated with a trophy not there"
         -> celebration, trophy
  body   "September 2025, Dubai. India beat Pakistan in the final."
         -> stadium, celebration
         "the man presenting the cup, Mohsin Naqvi, ACC president, PCB
          chairman, Pakistan's Interior Minister" -> Naqvi x3
         "India refused to take it from him." -> trophy
         "officials carried the trophy away" -> stadium
         "Suryakumar Yadav lifted an invisible one" -> Suryakumar
         "India's women won the Asia Cup, and did exactly the same" -> Harmanpreet x2
  cta    -> celebration, stadium

Photos (CC licensed, via Wikimedia Commons): Suryakumar Yadav (CC BY 3.0),
Mohsin Raza Naqvi (CC BY 3.0), Harmanpreet Kaur (CC BY-SA 4.0).
"""
import os
import re

import config

config.assert_safe_pipeline()

import pro_shorts_creator as psc
from logger import log
from run_invisible_trophy_short import SCRIPT

LOG = os.path.join(config.OUTPUT_DIR, "logs", "trophy_short_stdout.log")
OUT = os.path.join(config.VIDEOS_DIR, "invisible_trophy_short.mp4")
PHOTO = {k: os.path.join(config.OUTPUT_DIR, "raw_clips", f"photo_{k}.mp4")
         for k in ("naqvi", "suryakumar", "harmanpreet")}


def _from_log():
    text = open(LOG, encoding="utf-8", errors="replace").read()
    vo = re.findall(r"VO_PATH=(.+)", text)[-1].strip()
    clips = re.findall(r"CLIPS=(.+)", text)[-1].strip().split("|")
    music = re.findall(r"Music: (\S+\.mp3)", text)
    music = os.path.join(config.AUDIO_DIR, music[-1]) if music else None
    return vo, clips, music


if __name__ == "__main__":
    vo, _stock, music = _from_log()
    # The first build's stock download returned ONE Pixabay clip three times,
    # and the Asia Cup pool clips were gone from disk by 23:10. Fresh
    # cricket-specific clips (topup_pool.py), each checked on a contact sheet;
    # a novelty "World Champion Dad" mug was rejected.
    rc = lambda cid: os.path.join(config.OUTPUT_DIR, "raw_clips", f"pexels_{cid}.mp4")
    batsman, trophy, dubai = rc("32543231"), rc("6532230"), rc("35296036")
    oval, ground, local = rc("36747621"), rc("27778852"), rc("35782969")
    fans = rc("6104300")
    for p in [vo, batsman, trophy, dubai, oval, ground, local, fans, *PHOTO.values()]:
        assert os.path.exists(p), p
    # Shot k covers ~[k*2.4s]; placed against measured word times:
    # Naqvi described 9-16s ("Interior" 16.3), Suryakumar ~22-24s
    # ("invisible" 24.0), women 26-28s.
    order = [batsman, trophy,                   # 0-4.1   hook
             dubai, oval,                       # 4.1-8.9 "September 2025, Dubai..."
             PHOTO["naqvi"], PHOTO["naqvi"], PHOTO["naqvi"],   # 8.9-16.1
             trophy, ground,                    # 16.1-20.9 refused / an hour
             PHOTO["suryakumar"], PHOTO["suryakumar"],         # 20.9-25.7
             PHOTO["harmanpreet"], PHOTO["harmanpreet"],       # 25.7-30.3
             fans, local, oval]                 # CTA
    log(f"Re-assembling with {len(order)} shots, {len(set(order))} distinct sources")
    psc.assemble(order, SCRIPT, vo, music, OUT)
    log(f"REASSEMBLED -> {OUT}")
    print("VO_PATH=" + vo)
