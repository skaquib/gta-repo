"""
run_bowling_lane_short.py — Built 2026-08-29, video 4 of the fresh
8-video batch. Curiosity-gap evergreen format (see run_olympic_pool_short.py
docstring for the data-driven reasoning).

Verified via Bowling Buff, National Bowling Academy, flyingbowling.com
(2026-08-29): the American Bowling Congress standardized the regulation
lane at exactly 60 feet in 1895, after backyard/venue lanes had varied
wildly from 40 to over 75 feet, making consistent play impossible. The
60-foot distance was tuned to the physics of ball motion -- it's the
distance needed for a ball to skid, then hook, then fully roll before
reaching the pins. trend_research confirms real interest ("bowling lane
length", "bowling lane dimensions" both return live suggestions).
topic_checker: not a duplicate. Footage thin (bowling ball/alley/pins
each ~1 clip) -- verified visually before publish.

Per standing process: does NOT auto-upload from this file. Builds and
renders only; upload happens as a separate, explicit step after local
frame/duration verification.
"""
import os
import config

config.assert_safe_pipeline()

import pro_shorts_creator as psc
import copyright_compliance as cc
from logger import log

SCRIPT = {
    "hook": "A bowling lane is exactly 60 feet long -- and that number wasn't random.",
    "body": (
        "Before 1895, lanes varied from 40 to over 75 feet, so scores "
        "meant nothing from one alley to the next. The American Bowling "
        "Congress standardized it at 60 feet -- the exact distance a "
        "ball needs to skid, then hook, then roll cleanly into the "
        "pins."
    ),
    "cta": "Did you know there was real physics behind that number? Comment and subscribe!",
    "title": "Why Is a Bowling Lane EXACTLY 60 Feet? #shorts",
    "tags": ["bowling", "bowlinglane", "shorts", "viral", "sportsfacts"],
    "seo_description": "A regulation bowling lane is exactly 60 feet -- the precise distance a ball needs to skid, hook, and roll into the pins. #bowling #sportsfacts",
    "queries": ["bowling ball", "bowling alley", "bowling pins"],
}


def build():
    import topic_checker as tc
    check = tc.check_final_script_footage(SCRIPT)
    weak = [q for q, n in check.items() if n == 0]
    if weak:
        log(f"WARNING: real pipeline queries with 0 usable footage: {weak} -- proceeding, download_clips() will broaden/retry")

    log("Downloading real stock footage (Gemini-derived terms, tag-verified, cross-video deduped)...")
    clip_paths = psc.download_clips(SCRIPT)

    log("Generating voiceover (cloned voice + persona sign-off)...")
    vo_path = psc.generate_voiceover(SCRIPT)

    from moviepy import AudioFileClip
    vo_dur = min(AudioFileClip(vo_path).duration + 1.5, 90.0)
    log("Generating background music...")
    music_path = psc.get_music(duration=vo_dur, script=SCRIPT)

    log("Running compliance check...")
    check = cc.validate_before_upload(SCRIPT, clip_paths, music_path)
    cc.save_compliance_report(check, video_id="bowling_lane_short")
    if not check["passed"]:
        raise RuntimeError(f"COMPLIANCE FAILED: {check['issues']}")
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "bowling_lane_short.mp4")
    log(f"Assembling video -> {out_path}")
    psc.assemble(clip_paths, SCRIPT, vo_path, music_path, out_path)

    log(f"BUILD COMPLETE (not uploaded yet) -> {out_path}")
    return out_path, vo_path


if __name__ == "__main__":
    build()
