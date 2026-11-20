"""
run_davis_steel_short.py — Today's video (2026-08-03): Davis Steel (formerly
Eberlein Drive) went undefeated through the entire 2026 TBT, beating La
Familia 67-59 in the championship to win the $2 million winner-take-all
prize -- capping a 14-year quest with two prior runner-up finishes (2018,
2025). Real, fresh, verified redemption story -- basketball, keeping
content varied after two tennis videos in a row.
"""
import os
import config

config.assert_safe_pipeline()

import pro_shorts_creator as psc
import copyright_compliance as cc
from logger import log

SCRIPT = {
    "hook": "14 years chasing it. Two runner-up finishes. Then they won $2 million.",
    "body": (
        "Davis Steel, formerly known as Eberlein Drive, went undefeated "
        "through the entire 2026 TBT, winning five straight games. In the "
        "championship, they beat La Familia 67 to 59. Terry Taylor dropped "
        "24 points and 7 rebounds in one of the greatest performances in "
        "TBT Championship history. After 14 years and two runner-up "
        "finishes, in 2018 and 2025, Davis Steel finally has the title -- "
        "and the two million dollar prize."
    ),
    "cta": "Is TBT the best format in basketball? Comment your take and subscribe!",
    "title": "14 Years Chasing It. They Just Won $2 Million #shorts",
    "tags": ["tbt", "basketball", "davissteel", "terrytaylor", "shorts", "viral", "underdog", "sports"],
    "seo_description": "Davis Steel went undefeated to win the 2026 TBT championship and $2 million prize, capping a 14-year quest for the title. #basketball #tbt",
    "queries": ["basketball championship trophy", "basketball crowd celebration", "basketball player dunk"],
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
    cc.save_compliance_report(check, video_id="davis_steel_short")
    if not check["passed"]:
        log(f"COMPLIANCE FAILED: {check['issues']}")
        return
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "davis_steel_short.mp4")
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
