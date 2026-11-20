"""
run_olympic_pool_short.py — Built 2026-08-29, video 3 of the fresh
8-video batch. Curiosity-gap evergreen format -- real 30-day data showed
this format (e.g. "Why Is a Marathon EXACTLY 26.2 Miles?") gets the
highest raw view counts on this channel (819-1686 views), even above
recent named-star match-recap videos.

Verified via SwimSwam, PoolMagazine, Myrtha Pools (2026-08-29): FINA
standardized the 50-meter Olympic pool at the 1924 Paris Olympics. The
precision required is strict -- pools must measure exactly 50.000 meters
once timing equipment is installed, since even small variations would
affect fairness (times run faster in shorter pools due to more wall
push-offs). trend_research confirms real interest ("olympic pool
length", "olympic pool size" both return live suggestions).
topic_checker: not a duplicate; footage confirmed for "swimming pool" (9
clips) and "swimmer" (12 clips).

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
    "hook": "An Olympic swimming pool has to be exactly 50 meters long -- to the millimeter.",
    "body": (
        "FINA set this standard at the 1924 Paris Olympics. The rule is "
        "so strict that once timing equipment is installed, the pool "
        "must measure exactly 50.000 meters -- because swimmers get a "
        "small speed boost every time they push off the wall, so even a "
        "tiny difference in length would make times impossible to "
        "compare fairly."
    ),
    "cta": "Did you know it had to be THAT precise? Comment and subscribe!",
    "title": "Why Is an Olympic Swimming Pool EXACTLY 50 Meters? #shorts",
    "tags": ["olympics", "swimming", "olympicpool", "shorts", "viral", "sportsfacts"],
    "seo_description": "An Olympic swimming pool must measure exactly 50.000 meters -- here's why FINA made the rule that strict. #olympics #swimming #sportsfacts",
    "queries": ["swimming pool", "swimmer", "swimming race"],
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
    cc.save_compliance_report(check, video_id="olympic_pool_short")
    if not check["passed"]:
        raise RuntimeError(f"COMPLIANCE FAILED: {check['issues']}")
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "olympic_pool_short.mp4")
    log(f"Assembling video -> {out_path}")
    psc.assemble(clip_paths, SCRIPT, vo_path, music_path, out_path)

    log(f"BUILD COMPLETE (not uploaded yet) -> {out_path}")
    return out_path, vo_path


if __name__ == "__main__":
    build()
