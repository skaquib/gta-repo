"""
run_messi_final_short.py — Today's video: the World Cup 2026 Final is set
(Argentina vs Spain, July 19, MetLife Stadium) and it's being reported as
Messi's last World Cup at 39 -- the single biggest, freshest story available
right now, one day ahead of the actual final. Legend-farewell format (proven
with Ronaldo/Neymar) + real stock footage + persona voice + Hindi audio
language fix, same pipeline as every other video this batch.
"""
import os
import config

config.assert_safe_pipeline()

import pro_shorts_creator as psc
import copyright_compliance as cc
from logger import log

SCRIPT = {
    "hook": "One match. One legend. Possibly his last World Cup ever.",
    "body": (
        "Sunday, July 19th. Argentina faces Spain in the World Cup Final at "
        "MetLife Stadium. Messi, at 39, leads Argentina into what's believed "
        "to be his final World Cup. He hasn't confirmed retirement -- just "
        "taking it one day at a time. Spain enters as favorites, led by teen "
        "sensation Lamine Yamal. Defending champions versus European champions."
    ),
    "cta": "Who wins -- Messi's Argentina or Yamal's Spain? Comment your pick and subscribe!",
    "title": "Messi's Last World Cup Final Is Here #shorts #worldcup2026 #messi",
    "tags": ["worldcup2026", "messi", "argentina", "spain", "football", "soccer", "shorts", "final", "viral"],
    "seo_description": "The World Cup 2026 Final is set: Argentina vs Spain, and it may be Messi's last World Cup. #worldcup2026 #messi #football",
    "queries": ["soccer stadium final", "football crowd cheering flags", "soccer trophy celebration"],
}


def main():
    log("Downloading real stock footage (tag-verified, cross-video deduped)...")
    clip_paths = psc.download_clips(SCRIPT)

    log("Generating voiceover (cloned voice + persona sign-off)...")
    vo_path = psc.generate_voiceover(SCRIPT)

    log("Generating background music...")
    music_path = psc.get_music(duration=26.0)

    log("Running compliance check...")
    check = cc.validate_before_upload(SCRIPT, clip_paths, music_path)
    cc.save_compliance_report(check, video_id="messi_final_short")
    if not check["passed"]:
        log(f"COMPLIANCE FAILED: {check['issues']}")
        return
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "messi_final_short.mp4")
    log(f"Assembling video -> {out_path}")
    psc.assemble(clip_paths, SCRIPT, vo_path, music_path, out_path)

    log("Uploading...")
    url = psc.upload(out_path, SCRIPT, vo_path)
    if url:
        log(f"DONE — live at {url}")
    else:
        log("Upload did not return a URL — check logs above.")


if __name__ == "__main__":
    main()
