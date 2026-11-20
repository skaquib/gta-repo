"""
run_chaliha_hindi_short.py — Today's video (2026-08-09), Hindi-primary.
Ashmita Chaliha won her first BWF World Tour title at the Korea Masters,
coming back from losing the first game to beat China's Han Qian Xi
14-21, 21-14, 21-14 -- only the 5th Indian woman ever to win a Super 300+
BWF title. Real, fresh, verified, India-relevant story for the Hindi
audience segment.

Per the fresh process fix: this script does NOT auto-upload. It builds and
renders the video, then stops so the visuals/audio can be verified locally
(frame extraction) BEFORE anything goes live -- no more publish-then-check.
Run upload separately once the render is confirmed correct.
"""
import os
import config

config.assert_safe_pipeline()

import pro_shorts_creator as psc
import copyright_compliance as cc
from logger import log

SCRIPT_EN = {
    "hook": "She was down a game. Then she made history.",
    "body": (
        "Ashmita Chaliha just won her first BWF World Tour title at the "
        "Korea Masters. She lost the first game 14-21, then won the next "
        "two 21-14, 21-14, beating China's Han Qian Xi. She's only the "
        "fifth Indian woman ever to win a Super 300 or higher BWF title."
    ),
    "cta": "Is Ashmita Chaliha India's next badminton star? Comment your take and subscribe!",
    "title": "She's Only the 5th Indian Woman To Do This #shorts",
    "tags": ["badminton", "ashmitachaliha", "koreamasters", "india", "bwf", "sports", "shorts", "viral"],
    "seo_description": "Ashmita Chaliha won her first BWF World Tour title at the Korea Masters, becoming only the 5th Indian woman to win a Super 300+ title. #badminton #india",
    "queries": ["badminton player serve", "badminton match crowd", "badminton trophy celebration"],
}


def build():
    log("Translating script to Hindi...")
    script_hi = psc.translate_script_to_hindi(SCRIPT_EN)
    if script_hi.get("lang") != "hi":
        raise RuntimeError("Hindi translation did not succeed -- aborting rather than "
                            "building an English video under a Hindi-primary request.")
    log(f"Hindi hook: {script_hi['hook']}")

    log("Downloading real stock footage (English search terms, tag-verified, cross-video deduped)...")
    clip_paths = psc.download_clips(script_hi)

    log("Generating Hindi voiceover (Edge-TTS hi-IN-MadhurNeural)...")
    vo_path = psc.generate_hindi_voiceover(script_hi)

    from moviepy import AudioFileClip
    vo_dur = min(AudioFileClip(vo_path).duration + 1.5, 26.0)
    log("Generating background music...")
    music_path = psc.get_music(duration=vo_dur, script=SCRIPT)

    log("Running compliance check...")
    check = cc.validate_before_upload(script_hi, clip_paths, music_path)
    cc.save_compliance_report(check, video_id="chaliha_hindi_short")
    if not check["passed"]:
        raise RuntimeError(f"COMPLIANCE FAILED: {check['issues']}")
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "chaliha_hindi_short.mp4")
    log(f"Assembling video -> {out_path}")
    psc.assemble(clip_paths, script_hi, vo_path, music_path, out_path)

    log(f"BUILD COMPLETE (not uploaded yet) -> {out_path}")
    log("Verify frames locally before calling psc.upload().")
    return out_path, script_hi, vo_path


if __name__ == "__main__":
    build()
