"""
run_sinner_withdrawal_short.py — Built 2026-08-22, part of an 8-video
private batch (direct instruction: "make trending sport topic diffrent
scrpt videos make private 8 videos"). Uploaded PRIVATE only, not
published -- held for review before any go live.

Verified via ESPN, SI.com (2026-08-22): Jannik Sinner, world No. 1, has
withdrawn from the 2026 US Open due to an ongoing right knee injury --
his first missed Grand Slam since 2019, having not played since winning
Wimbledon. trend_research autocomplete confirms real current interest
("sinner withdraws", "jannik sinner withdraws" both return live
suggestions). topic_checker.py: not a duplicate; footage confirmed for
"tennis" (2 clips), "tennis ball" (1), "tennis racket" (1).

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
    "hook": "Jannik Sinner just withdrew from the US Open for the first time since 2019.",
    "body": (
        "The world number one has an ongoing knee injury and hasn't "
        "played since winning Wimbledon. This is the first Grand Slam "
        "he's missed in seven years."
    ),
    "cta": "Who do you think benefits most from Sinner's absence? Comment and subscribe!",
    "title": "Jannik Sinner Just Withdrew From the US Open for the First Time Since 2019 #shorts",
    "tags": ["janniksinner", "usopen", "tennis", "shorts", "viral", "grandslam"],
    "seo_description": "World No. 1 Jannik Sinner has withdrawn from the US Open with a knee injury -- his first missed Grand Slam since 2019. #sinner #usopen #tennis",
    "queries": ["tennis", "tennis ball", "tennis racket"],
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
    cc.save_compliance_report(check, video_id="sinner_withdrawal_short")
    if not check["passed"]:
        raise RuntimeError(f"COMPLIANCE FAILED: {check['issues']}")
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "sinner_withdrawal_short.mp4")
    log(f"Assembling video -> {out_path}")
    psc.assemble(clip_paths, SCRIPT, vo_path, music_path, out_path)

    log(f"BUILD COMPLETE (not uploaded yet) -> {out_path}")
    return out_path, vo_path


if __name__ == "__main__":
    build()
