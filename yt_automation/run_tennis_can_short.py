"""
run_tennis_can_short.py — Today's video (2026-08-17). Same validated
process as the basketball hoop video: locked to the proven explainer
format (famous subject + surprising mechanism), this time pulling directly
from mrfact's real top performer -- "Why Tennis Balls Come in Sealed Cans"
(616K views) -- a topic we hadn't covered yet.

Fact, verified via letsgotennis.com, mentalfloss.com, sportsboom.com,
tennislovers.com: tennis balls are pressurized to ~27 PSI inside, well
above normal air pressure. The rubber isn't airtight, so that pressure
slowly leaks out -- and unlike a basketball, a tennis ball can never be
re-inflated once it goes dead. The sealed can is pressurized to match the
ball's internal pressure, keeping it fresh until opened; the moment you
break the seal, the clock starts on it losing bounce for good.

Per the process fix: this script does NOT auto-upload. It builds and
renders, then stops so the visuals/audio can be verified locally before
anything goes live.
"""
import os
import config

config.assert_safe_pipeline()

import pro_shorts_creator as psc
import copyright_compliance as cc
from logger import log

SCRIPT = {
    "hook": "That hiss when you open a tennis ball can? That's the whole reason it bounces.",
    "body": (
        "Tennis balls are pressurized to about 27 PSI inside -- way more "
        "than normal air pressure. But the rubber isn't airtight, so that "
        "pressure leaks out over time, and unlike a basketball, you can "
        "never pump a tennis ball back up. The sealed can matches that "
        "internal pressure, keeping the ball fresh until you open it. The "
        "moment you do, it's already going dead."
    ),
    "cta": "Did you know a tennis ball can never be re-inflated? Comment below and subscribe!",
    "title": "Why Tennis Balls Come in Sealed Cans #shorts",
    "tags": ["tennis", "tennisball", "funfacts", "sportsscience", "shorts", "viral", "tennisfacts"],
    "seo_description": "Tennis balls are pressurized and can never be re-inflated once opened -- that's why they're sold in sealed, pressurized cans. #tennis #funfacts",
    "queries": ["tennis ball can opening", "tennis ball bounce closeup", "tennis ball court"],
}


def build():
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
    cc.save_compliance_report(check, video_id="tennis_can_short")
    if not check["passed"]:
        raise RuntimeError(f"COMPLIANCE FAILED: {check['issues']}")
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "tennis_can_short.mp4")
    log(f"Assembling video -> {out_path}")
    psc.assemble(clip_paths, SCRIPT, vo_path, music_path, out_path)

    log(f"BUILD COMPLETE (not uploaded yet) -> {out_path}")
    return out_path, vo_path


if __name__ == "__main__":
    build()
