"""
run_virtanen_shelton_short.py — Built 2026-08-29. Part of a fresh
8-video batch, corrected strategy: real data (30-day retention/views
pulled live) showed the recent "Team X beat Team Y 2-0" recap format
underperforming two formats already proven to work on this channel --
curiosity-gap evergreen explainers (highest raw views) and named-opponent
underdog/upset drama (highest retention). This batch leans into both,
not generic match recaps.

Verified via ATP Tour, CBS Sports, WSB-TV (checked exact date carefully
after a near-miss: an initial "underdog" candidate, Victoria Mboko,
turned out to be from August 2025, a full year stale, surfaced by a
misleading "2026 season review" article): unranked Finnish qualifier
Otto Virtanen beat No. 4 seed Ben Shelton 6-4, 3-6, 6-7(8), 6-2, 7-6(11-9)
in the first round of Wimbledon on June 30, 2026 -- a four-hour,
21-minute five-set thriller in which Shelton held match point at 9-8 in
the final-set tiebreak before Virtanen won three straight points.
Virtanen became the first Finnish man ever to beat a top-5 seed at a
major in the Open Era. trend_research confirms real interest ("ben
shelton wimbledon", "otto virtanen wimbledon" both return live
suggestions). topic_checker: not a duplicate.

No tennis stock footage exists on this account right now (confirmed dry
across every query this whole session) -- used real, safely-licensed
photos of both players instead (Ben Shelton, Roland Garros 2023, CC
BY-SA 4.0; Otto Virtanen, US Open 2023, CC BY-SA 4.0), animated with a
Ken Burns pan/zoom. Both photos needed an EXIF-orientation fix (found
and fixed 2026-08-29) since they loaded sideways otherwise.

Per standing process: does NOT auto-upload from this file. Builds and
renders only; upload happens as a separate, explicit step after local
frame/duration verification.
"""
import os
import config

config.assert_safe_pipeline()

import pro_shorts_creator as psc
import copyright_compliance as cc
from logger import log

SCRIPT = {
    "hook": "An unranked qualifier just beat Ben Shelton, the world's top-ranked American, at Wimbledon.",
    "body": (
        "Otto Virtanen had never beaten a top-5 seed before. Shelton "
        "even held match point in the fifth-set tiebreak -- but Virtanen "
        "won three straight points to complete one of the biggest upsets "
        "of the tournament, in a five-set thriller lasting over four "
        "hours."
    ),
    "cta": "Would you have seen that coming? Comment your reaction and subscribe!",
    "title": "An Unranked Qualifier Just Beat Ben Shelton at Wimbledon #shorts",
    "tags": ["benshelton", "ottovirtanen", "wimbledon", "tennis", "shorts", "viral", "upset"],
    "seo_description": "Unranked qualifier Otto Virtanen beat No. 4 seed Ben Shelton in a five-set Wimbledon thriller, saving a match point along the way. #wimbledon #tennis #benshelton",
    "queries": ["tennis", "tennis court", "sports fans"],
}


def build():
    photo = psc.try_athlete_photo_hook("Ben Shelton tennis")
    print("Photo:", photo)

    log("Downloading remaining stock footage...")
    clip_paths_all = psc.download_clips(SCRIPT)
    if photo:
        clip_paths = [photo["video_path"]] + clip_paths_all[:2]
    else:
        clip_paths = clip_paths_all

    log("Generating voiceover (cloned voice + persona sign-off)...")
    vo_path = psc.generate_voiceover(SCRIPT)

    from moviepy import AudioFileClip
    vo_dur = min(AudioFileClip(vo_path).duration + 1.5, 90.0)
    log("Generating background music...")
    music_path = psc.get_music(duration=vo_dur, script=SCRIPT)

    log("Running compliance check...")
    check = cc.validate_before_upload(SCRIPT, clip_paths, music_path)
    cc.save_compliance_report(check, video_id="virtanen_shelton_short")
    if not check["passed"]:
        raise RuntimeError(f"COMPLIANCE FAILED: {check['issues']}")
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "virtanen_shelton_short.mp4")
    log(f"Assembling video -> {out_path}")
    psc.assemble(clip_paths, SCRIPT, vo_path, music_path, out_path)

    log(f"BUILD COMPLETE (not uploaded yet) -> {out_path}")
    return out_path, vo_path


if __name__ == "__main__":
    build()
