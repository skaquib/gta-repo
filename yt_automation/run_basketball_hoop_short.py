"""
run_basketball_hoop_short.py — Today's video (2026-08-16). Deep research
first, per explicit direction: pulled real view data from a comparable
channel (mrfact, 103K subs) showing its exact-number curiosity-gap format
consistently wins -- "Why NBA Rims Are Exactly 10 Feet High" (478K views),
"Why Tennis Balls Come in Sealed Cans" (616K) -- the same pattern as our
own top performer, "Why Is a Marathon EXACTLY 26.2 Miles?" (1,506 views,
our #1 by 2x). Also cross-checked our own real numbers: both explainer
videos (marathon 1506, golf dimples 927) beat every news-story video
(83-723) on this channel. Locking that proven format+pattern rather than
guessing.

Topic: the basketball rim is exactly 10 feet high purely by accident --
in 1891, James Naismith nailed peach baskets to a Springfield YMCA gym's
running-track railing, which happened to be 10 feet up. Codified into
official rules by 1893, unchanged 130+ years later at every level of the
sport worldwide. Verified via xbotgo, brobible, trigonsports, sportsgeardaily.

Basketball is a globally famous subject (like "marathon"), never covered
on this channel before, and hoop/rim/court stock footage is specific and
abundant -- should match the script the way the marathon video did.

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
    "hook": "The basketball hoop height has zero scientific reason behind it.",
    "body": (
        "In 1891, James Naismith needed somewhere to hang peach baskets "
        "for a new indoor game. The gym's running-track railing happened "
        "to be exactly 10 feet high, so he just nailed the baskets there. "
        "That accidental height got written into the official rules by "
        "1893, and it's never changed -- over 130 years later, every hoop "
        "in the world is still exactly 10 feet."
    ),
    "cta": "Would basketball be different at a different rim height? Comment below and subscribe!",
    "title": "Why Is a Basketball Hoop EXACTLY 10 Feet? #shorts",
    "tags": ["basketball", "nba", "funfacts", "sportshistory", "jamesnaismith", "shorts", "viral"],
    "seo_description": "The basketball rim is exactly 10 feet high purely by accident -- a gym railing height from 1891 that's never changed. #basketball #nba #funfacts",
    "queries": ["basketball hoop rim close up", "basketball dunk net", "basketball court gym"],
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
    cc.save_compliance_report(check, video_id="basketball_hoop_short")
    if not check["passed"]:
        raise RuntimeError(f"COMPLIANCE FAILED: {check['issues']}")
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "basketball_hoop_short.mp4")
    log(f"Assembling video -> {out_path}")
    psc.assemble(clip_paths, SCRIPT, vo_path, music_path, out_path)

    log(f"BUILD COMPLETE (not uploaded yet) -> {out_path}")
    return out_path, vo_path


if __name__ == "__main__":
    build()
