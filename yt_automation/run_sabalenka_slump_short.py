"""
run_sabalenka_slump_short.py — Built 2026-08-22, video 2 of an 8-video
private batch. Uploaded PRIVATE only, not published.

Verified via Olympics.com (2026-08-22): Aryna Sabalenka, two-time
defending US Open champion, has lost 5 of her last 7 three-set matches
since her Miami Open win in March, including a straight-sets upset to
unseeded 20-year-old Sara Bejlek in Cincinnati. Elena Rybakina is now
within 434 points of the world No. 1 ranking Sabalenka has held for two
years. trend_research autocomplete confirms real interest ("sabalenka
rybakina" returns live suggestions). topic_checker.py: not a duplicate;
footage confirmed for "tennis" (2 clips).

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
    "hook": "Aryna Sabalenka has lost 5 of her last 7 three-set matches.",
    "body": (
        "The two-time defending US Open champion was upset in straight "
        "sets by an unseeded 20-year-old in Cincinnati. Elena Rybakina "
        "is now just 434 points behind her for the world number one "
        "ranking Sabalenka has held for two years."
    ),
    "cta": "Is Sabalenka's number one reign about to end? Comment your prediction and subscribe!",
    "title": "Aryna Sabalenka Has Lost 5 of Her Last 7 Three-Set Matches #shorts",
    "tags": ["arynasabalenka", "elenarybakina", "usopen", "tennis", "shorts", "viral"],
    "seo_description": "Aryna Sabalenka has lost 5 of her last 7 three-set matches, and Elena Rybakina is closing in on world No. 1. #sabalenka #rybakina #tennis",
    "queries": ["tennis", "tennis court", "tennis ball"],
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
    cc.save_compliance_report(check, video_id="sabalenka_slump_short")
    if not check["passed"]:
        raise RuntimeError(f"COMPLIANCE FAILED: {check['issues']}")
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "sabalenka_slump_short.mp4")
    log(f"Assembling video -> {out_path}")
    psc.assemble(clip_paths, SCRIPT, vo_path, music_path, out_path)

    log(f"BUILD COMPLETE (not uploaded yet) -> {out_path}")
    return out_path, vo_path


if __name__ == "__main__":
    build()
