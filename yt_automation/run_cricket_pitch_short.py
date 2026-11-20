"""
run_cricket_pitch_short.py — Built 2026-08-29, video 5 of the fresh
8-video batch. Curiosity-gap evergreen format (see run_olympic_pool_short.py
docstring for the data-driven reasoning).

Verified via ESPNcricinfo, Martin Berrill Sports (2026-08-29): cricket's
22-yard pitch length dates to the earliest known Laws of Cricket (the
1744 Code), but the real origin traces back further -- to Edmund
Gunter's 1620 surveying chain, exactly 22 yards (66 feet) long, the
standard tool used to measure farmland in England. Early cricket was
played on common land measured with that same chain, so "one chain"
became the pitch length by default and was never changed. trend_research
confirms real interest ("cricket pitch length" returns live suggestions).
topic_checker: not a duplicate.

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
    "hook": "A cricket pitch is exactly 22 yards long -- and it has nothing to do with cricket.",
    "body": (
        "In 1620, a mathematician named Edmund Gunter invented a "
        "22-yard measuring chain to survey farmland across England. "
        "Early cricket was played on that same common land, so pitches "
        "were laid out using the same chain -- one chain, 22 yards -- "
        "and it's never changed since."
    ),
    "cta": "Did you know a farming tool decided this? Comment and subscribe!",
    "title": "Why Is a Cricket Pitch EXACTLY 22 Yards Long? #shorts",
    "tags": ["cricket", "cricketfacts", "shorts", "viral", "sportsfacts"],
    "seo_description": "A cricket pitch is exactly 22 yards -- the length of a 1620 farmland surveying chain. #cricket #sportsfacts #shorts",
    "queries": ["cricket match", "cricket player", "cricket stadium"],
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
    cc.save_compliance_report(check, video_id="cricket_pitch_short")
    if not check["passed"]:
        raise RuntimeError(f"COMPLIANCE FAILED: {check['issues']}")
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "cricket_pitch_short.mp4")
    log(f"Assembling video -> {out_path}")
    psc.assemble(clip_paths, SCRIPT, vo_path, music_path, out_path)

    log(f"BUILD COMPLETE (not uploaded yet) -> {out_path}")
    return out_path, vo_path


if __name__ == "__main__":
    build()
