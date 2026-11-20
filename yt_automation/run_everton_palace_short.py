"""
run_everton_palace_short.py — Built 2026-08-22, video 4 of an 8-video
private batch. Uploaded PRIVATE only, not published.

Verified via ESPN, VAVEL (2026-08-22): Everton beat Crystal Palace 2-0
at home on opening day, Kiernan Dewsbury-Hall scoring in the 42nd minute
and Thierno Barry adding a second in the 53rd. trend_research
autocomplete confirms real interest ("everton crystal palace" and
score-specific variants return live suggestions). topic_checker.py: not
a duplicate.

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
    "hook": "Everton just beat Crystal Palace 2-0 to start the season.",
    "body": (
        "Kiernan Dewsbury-Hall opened the scoring just before half-time, "
        "and Thierno Barry doubled the lead early in the second half. A "
        "clean, comfortable opening-day win at home."
    ),
    "cta": "Is this the start of a big season for Everton? Comment your prediction and subscribe!",
    "title": "Everton Just Beat Crystal Palace 2-0 to Start the Season #shorts",
    "tags": ["everton", "crystalpalace", "premierleague", "football", "soccer", "shorts", "viral"],
    "seo_description": "Everton beat Crystal Palace 2-0 on opening day, with goals from Kiernan Dewsbury-Hall and Thierno Barry. #everton #premierleague #football",
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
    cc.save_compliance_report(check, video_id="everton_palace_short")
    if not check["passed"]:
        raise RuntimeError(f"COMPLIANCE FAILED: {check['issues']}")
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "everton_palace_short.mp4")
    log(f"Assembling video -> {out_path}")
    psc.assemble(clip_paths, SCRIPT, vo_path, music_path, out_path)

    log(f"BUILD COMPLETE (not uploaded yet) -> {out_path}")
    return out_path, vo_path


if __name__ == "__main__":
    build()
