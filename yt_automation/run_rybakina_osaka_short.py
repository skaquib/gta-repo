"""
run_rybakina_osaka_short.py — Today's video (2026-08-12): Elena Rybakina
came back from a set down to beat 4-time Grand Slam champion Naomi Osaka
4-6, 7-6(5), 6-4 in the Toronto (Canadian Open) quarterfinals -- 13 aces,
broke serve mid-decider, 2h33m. Rybakina is the reigning Australian Open
champion. Real, fresh, verified.

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
    "hook": "Down a set. Then she took out a 4-time Grand Slam champion.",
    "body": (
        "Elena Rybakina just beat Naomi Osaka 4-6, 7-6, 6-4 in the Toronto "
        "quarterfinals. She fired 13 aces and broke Osaka's serve right in "
        "the middle of the deciding set. The match took two hours and "
        "thirty-three minutes. Rybakina is the reigning Australian Open "
        "champion."
    ),
    "cta": "Is Rybakina the player to beat this summer? Comment your take and subscribe!",
    "title": "The Reigning Champ Just Beat Naomi Osaka #shorts #tennis",
    "tags": ["tennis", "elenarybakina", "naomiosaka", "torontoopen", "wta", "sports", "shorts", "viral"],
    "seo_description": "Elena Rybakina came back from a set down to beat Naomi Osaka 4-6, 7-6, 6-4 in the Toronto quarterfinals. #tennis #rybakina",
    "queries": ["tennis player serve", "tennis match crowd", "tennis trophy celebration"],
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
    cc.save_compliance_report(check, video_id="rybakina_osaka_short")
    if not check["passed"]:
        raise RuntimeError(f"COMPLIANCE FAILED: {check['issues']}")
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "rybakina_osaka_short.mp4")
    log(f"Assembling video -> {out_path}")
    psc.assemble(clip_paths, SCRIPT, vo_path, music_path, out_path)

    log(f"BUILD COMPLETE (not uploaded yet) -> {out_path}")
    return out_path, vo_path


if __name__ == "__main__":
    build()
