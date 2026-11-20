"""
run_messi_result_short.py — Direct emotional follow-up to run_messi_final_short.py:
the actual result. Spain beat Argentina 1-0 in extra time (Ferran Torres,
106th minute); Messi left the field in tears in his likely final World Cup
appearance. Real, verified, and a natural next chapter for anyone who saw
yesterday's anticipation video.
"""
import os
import config

config.assert_safe_pipeline()

import pro_shorts_creator as psc
import copyright_compliance as cc
from logger import log

SCRIPT = {
    "hook": "He walked off in tears. Spain just ended Messi's World Cup story.",
    "body": (
        "Sunday, July 19th. Spain beat Argentina 1-0 in extra time. Ferran "
        "Torres scored the winner in the 106th minute. Messi, at 39, left "
        "the field in tears after the loss -- in what's believed to be his "
        "final World Cup. Spain wins their second title. Argentina's golden "
        "generation falls just short."
    ),
    "cta": "What will you remember most about Messi's World Cup career? Comment and subscribe!",
    "title": "Messi's World Cup Ends in Tears -- Spain Wins 2026 #shorts #worldcup2026",
    "tags": ["worldcup2026", "messi", "argentina", "spain", "football", "soccer", "shorts", "final", "viral"],
    "seo_description": "Spain beat Argentina 1-0 in extra time to win the World Cup 2026 final, ending Messi's international career in heartbreak. #worldcup2026 #messi",
    "queries": ["soccer player disappointed", "football stadium celebration", "soccer trophy lift"],
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
    cc.save_compliance_report(check, video_id="messi_result_short")
    if not check["passed"]:
        log(f"COMPLIANCE FAILED: {check['issues']}")
        return
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "messi_result_short.mp4")
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
