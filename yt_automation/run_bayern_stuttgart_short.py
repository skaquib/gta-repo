"""
run_bayern_stuttgart_short.py — Built 2026-08-22, video 8 of an 8-video
private batch. Uploaded PRIVATE only, not published.

Deliberately kept to settled, non-outcome-dependent facts: Bayern's match
is genuinely in the future (Friday Aug 28, confirmed via fcbayern.com and
bundesliga.com official fixture announcements), so the script does not
predict or assume a result -- same lesson as the Coventry rewrite, applied
proactively this time instead of after a mistake.

Verified via fcbayern.com, bundesliga.com (2026-08-22): Bayern Munich, the
defending Bundesliga champions, open their 2026-27 title defense at home
to VfB Stuttgart on Friday, August 28. topic_checker.py: not a duplicate.

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
    "hook": "Bayern Munich open their Bundesliga title defense on Friday.",
    "body": (
        "The defending champions host VfB Stuttgart to kick off the new "
        "season, renewing one of German football's long-standing "
        "rivalries as Bayern look to extend their dominance."
    ),
    "cta": "Can anyone actually stop Bayern this season? Comment your prediction and subscribe!",
    "title": "Bayern Munich Open Their Bundesliga Title Defense This Week #shorts",
    "tags": ["bayernmunich", "bundesliga", "vfbstuttgart", "football", "soccer", "shorts", "viral"],
    "seo_description": "Defending champions Bayern Munich open their Bundesliga title defense at home to VfB Stuttgart on Friday. #bayernmunich #bundesliga #football",
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
    cc.save_compliance_report(check, video_id="bayern_stuttgart_short")
    if not check["passed"]:
        raise RuntimeError(f"COMPLIANCE FAILED: {check['issues']}")
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "bayern_stuttgart_short.mp4")
    log(f"Assembling video -> {out_path}")
    psc.assemble(clip_paths, SCRIPT, vo_path, music_path, out_path)

    log(f"BUILD COMPLETE (not uploaded yet) -> {out_path}")
    return out_path, vo_path


if __name__ == "__main__":
    build()
