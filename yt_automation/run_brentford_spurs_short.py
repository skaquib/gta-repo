"""
run_brentford_spurs_short.py — Built 2026-08-22, video 5 of an 8-video
private batch. Uploaded PRIVATE only, not published.

Verified via VAVEL (2026-08-22): Brentford beat Tottenham Hotspur 3-0 on
opening day, with goals including Michael Kayode and Vitaly Janelt.
trend_research autocomplete confirms real interest ("brentford
tottenham" returns live suggestions, including score-specific variants).
topic_checker.py: not a duplicate.

Per standing process: does NOT auto-upload from this file. Builds and
renders only; upload happens as a separate, explicit step after local
frame/duration verification, and per this batch's instruction goes up
as private, not public.
"""
import os
import config

config.assert_safe_pipeline()

import pro_shorts_creator as psc
import copyright_compliance as cc
from logger import log

SCRIPT = {
    "hook": "Brentford just beat Tottenham 3-0 on opening day.",
    "body": (
        "Michael Kayode and Vitaly Janelt were among the scorers as "
        "Brentford ran out comfortable winners at home, a statement "
        "result against one of the Premier League's bigger names."
    ),
    "cta": "Did anyone see this result coming? Comment your prediction for the season and subscribe!",
    "title": "Brentford Just Beat Tottenham 3-0 on Opening Day #shorts",
    "tags": ["brentford", "tottenham", "premierleague", "football", "soccer", "shorts", "viral"],
    "seo_description": "Brentford beat Tottenham Hotspur 3-0 on the opening day of the Premier League season. #brentford #tottenham #premierleague",
    "queries": ["soccer stadium", "soccer match", "football training"],
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
    cc.save_compliance_report(check, video_id="brentford_spurs_short")
    if not check["passed"]:
        raise RuntimeError(f"COMPLIANCE FAILED: {check['issues']}")
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "brentford_spurs_short.mp4")
    log(f"Assembling video -> {out_path}")
    psc.assemble(clip_paths, SCRIPT, vo_path, music_path, out_path)

    log(f"BUILD COMPLETE (not uploaded yet) -> {out_path}")
    return out_path, vo_path


if __name__ == "__main__":
    build()
