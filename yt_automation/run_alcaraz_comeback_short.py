"""
run_alcaraz_comeback_short.py — Built 2026-08-22, video 3 of an 8-video
private batch. Uploaded PRIVATE only, not published.

Verified via Al Jazeera, NBC Sports (2026-08-20/22): Carlos Alcaraz, the
defending US Open champion, has been out since April with a right wrist
injury -- missing the French Open, Wimbledon, and the North American
hard-court events in Toronto and Cincinnati. He confirmed his return at
the US Open, ending a four-month-plus absence, to defend his title.
trend_research autocomplete confirms real interest ("carlos alcaraz
injury", "alcaraz us open 2026" both return live suggestions; an "ankle
injury" suggestion was checked and is stale, from a 2024 issue, not this
one -- confirmed the current injury is the wrist via a second, more
specific search before writing this). topic_checker.py: not a duplicate.

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
    "hook": "Carlos Alcaraz is back after 4 months out with a wrist injury.",
    "body": (
        "The defending US Open champion missed the French Open, "
        "Wimbledon, and two North American hard-court tournaments while "
        "recovering. Now he's returning to New York to try to defend "
        "his title."
    ),
    "cta": "Can Alcaraz defend his title after 4 months away? Comment your prediction and subscribe!",
    "title": "Carlos Alcaraz Is Back After 4 Months Out Injured #shorts",
    "tags": ["carlosalcaraz", "usopen", "tennis", "shorts", "viral", "grandslam"],
    "seo_description": "Defending champion Carlos Alcaraz returns to the US Open after 4 months out with a wrist injury that cost him the French Open and Wimbledon. #alcaraz #usopen #tennis",
    "queries": ["tennis", "tennis ball", "tennis court"],
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
    cc.save_compliance_report(check, video_id="alcaraz_comeback_short")
    if not check["passed"]:
        raise RuntimeError(f"COMPLIANCE FAILED: {check['issues']}")
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "alcaraz_comeback_short.mp4")
    log(f"Assembling video -> {out_path}")
    psc.assemble(clip_paths, SCRIPT, vo_path, music_path, out_path)

    log(f"BUILD COMPLETE (not uploaded yet) -> {out_path}")
    return out_path, vo_path


if __name__ == "__main__":
    build()
