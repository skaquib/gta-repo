"""
run_soccer_vest_short.py — Topic sourced from real YouTube search-
autocomplete data (suggestqueries.google.com/complete/search?client=youtube),
not a guess. Querying "why does soccer" surfaced "why do soccer players
wear bras" as a live, real autocomplete suggestion -- direct evidence of
actual search behavior on YouTube, not just news coverage. Cross-checked:
multiple NBC affiliates (Miami, Bay Area, Philadelphia) and Slate have
independently covered this exact question, confirming it's a recurring,
widely-asked one, not a one-off.

Fact, verified via playermaker.com, catapultsports.com, kinexon-sports.com:
the "sports bra"-looking vest holds a GPS pod between the shoulder blades
-- a 10Hz GPS unit plus accelerometer and magnetometer capturing over
1,250 data points per second, tracking speed, distance, sprint load, and
recovery. Never covered on this channel; soccer explainer (not news), a
sport we haven't done in this format yet.

Passed topic_checker.py before this script was written: no duplicate
title, all three footage queries return real, unused, tag-confirmed clips.

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
    "hook": "Why do professional soccer players wear what looks like a sports bra?",
    "body": (
        "It's not a bra -- it's a GPS tracking vest. The pod sits between "
        "the shoulder blades and holds a GPS unit, an accelerometer, and "
        "a magnetometer, capturing over 1,250 data points every second. "
        "Coaches use it to track a player's speed, distance, sprint load, "
        "and how well they're recovering, all in real time."
    ),
    "cta": "Did you know that vest was tracking 1,250 data points a second? Comment below and subscribe!",
    "title": "Why Do Soccer Players Wear Those Vests? #shorts",
    "tags": ["soccer", "football", "gps", "sportsscience", "funfacts", "shorts", "viral"],
    "seo_description": "That vest soccer players wear isn't a bra -- it's a GPS tracker capturing over 1,250 data points a second. #soccer #football #funfacts",
    "queries": ["soccer training vest", "soccer player closeup training", "soccer team training session"],
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
    cc.save_compliance_report(check, video_id="soccer_vest_short")
    if not check["passed"]:
        raise RuntimeError(f"COMPLIANCE FAILED: {check['issues']}")
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "soccer_vest_short.mp4")
    log(f"Assembling video -> {out_path}")
    psc.assemble(clip_paths, SCRIPT, vo_path, music_path, out_path)

    log(f"BUILD COMPLETE (not uploaded yet) -> {out_path}")
    return out_path, vo_path


if __name__ == "__main__":
    build()
