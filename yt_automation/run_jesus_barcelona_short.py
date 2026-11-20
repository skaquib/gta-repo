"""
run_jesus_barcelona_short.py — Built 2026-09-03.

PRE-PUSH CHECKLIST (standing rule: pre-push-viral-research)
1. DEMAND TODAY: Transfer deadline day just closed. Gabriel Jesus
   completing an Arsenal -> Barcelona move is the biggest mainstream
   football story of 2026-09-03, involving two of the largest fanbases in
   the sport. Verified across ESPN, Sky Sports, FOX Sports and Al Jazeera.
2. NOT A REPEAT: not Djokovic (published 2026-08-31), not the
   "Why Is a [thing] EXACTLY [number]?" template, not "[Team] Just Beat
   [Team]". Different sport story-type entirely (a transfer).
3. OUR OWN RESULTS: Aug median 128 views, 1 sub from 29 videos, every
   video one of two templates. June (World Cup, huge names + live event)
   median was 1131. This returns to named-star + live-event demand.
4. VISUAL UPGRADE APPLIED: this is the first video using the new
   top-third bold hook headline (pro_shorts_creator.HOOK_CARD_DUR /
   SCRIPT["hook_card"]). Viral research: the keep-or-swipe decision lands
   at or before 1 second and 85% of Shorts start muted, so the promise has
   to be READABLE in the top third immediately. Every previous video put
   100% of its text at the bottom (y = H-460) with only a small channel
   badge up top -- a muted viewer saw no promise at all in second one.

FEE NOTE (verify-own-claims discipline): reported fee differs by source
-- Sky Sports says £8.6m, ESPN/AP say €15m (£12.85m) with a sell-on
clause, Barca Blaugranes says €10m. Because they disagree, the script
deliberately states NO figure and sticks to what every source agrees on:
deadline-day move, three-year deal, replacing Lewandowski.

LENGTH: ~53 words targeting the 21-25s band (our data: 21-25s = 117.4%
retention vs 38.7% at 31-35s). The persona sign-off still costs ~4s.

Per standing process: does NOT auto-upload. Verify frames/duration/tail first.
"""
import os
import config

config.assert_safe_pipeline()

import pro_shorts_creator as psc
import copyright_compliance as cc
from logger import log

SCRIPT = {
    "hook": "Arsenal just let a Premier League title winner walk to Barcelona on deadline day.",
    # Explicit on-screen headline -- the auto-condense can cut mid-phrase.
    "hook_card": "ARSENAL JUST LET HIM GO",
    "body": (
        "Gabriel Jesus won four league titles at Manchester City, then "
        "the Premier League with Arsenal. Now he's at Barcelona on a "
        "three-year deal, replacing Robert Lewandowski."
    ),
    "cta": "Mistake by Arsenal? Comment!",
    "title": "Arsenal Just Let a Premier League Title Winner Join Barcelona #shorts",
    "tags": ["gabrieljesus", "arsenal", "barcelona", "transfer", "football", "shorts", "viral", "deadlineday"],
    "seo_description": "Gabriel Jesus completed a deadline-day move from Arsenal to Barcelona on a three-year deal, replacing Robert Lewandowski. #gabrieljesus #arsenal #barcelona #football",
    "queries": ["football stadium crowd", "soccer player", "football pitch"],
}


def build():
    photo_clips = []
    for src, out, label in [
        ("output/raw_clips/File_1_gabriel_jesus_2026.jpg", "jesus2026.mp4", "Gabriel Jesus 2026"),
        ("output/raw_clips/File_LFP_-_Barcelona_vs_Mallorca_pre-match_-_Oct_3rd_2010.jpg", "barca.mp4", "Barcelona"),
        ("output/raw_clips/File_20180610_FIFA_Friendly_Match_Austria_vs._Brazil_Gabriel_Jesus_850_1688.jpg", "jesusbrazil.mp4", "Jesus Brazil"),
    ]:
        if os.path.exists(src):
            p = psc.make_athlete_photo_clip(src, "output/raw_clips/" + out, duration=12.0)
            photo_clips.append(p)
            log(f"  photo clip ({label}): {p}")
        else:
            log(f"  MISSING: {src}")

    clip_paths = photo_clips[:3]
    if not clip_paths:
        raise RuntimeError("No photos available")
    while len(clip_paths) < 3:
        clip_paths.append(clip_paths[-1])
    log(f"Clips: {clip_paths}")

    vo_path = psc.generate_voiceover(SCRIPT)
    from moviepy import AudioFileClip
    d = AudioFileClip(vo_path).duration
    log(f"VOICEOVER LENGTH: {d:.1f}s (target band 21-25s)")

    music_path = psc.get_music(duration=min(d + 1.5, 90.0), script=SCRIPT)

    check = cc.validate_before_upload(SCRIPT, clip_paths, music_path)
    cc.save_compliance_report(check, video_id="jesus_barcelona_short")
    if not check["passed"]:
        raise RuntimeError(f"COMPLIANCE FAILED: {check['issues']}")

    out_path = os.path.join(config.VIDEOS_DIR, "jesus_barcelona_short.mp4")
    psc.assemble(clip_paths, SCRIPT, vo_path, music_path, out_path)
    log(f"BUILD COMPLETE -> {out_path}")
    print("VO_PATH=" + vo_path)
    return out_path, vo_path


if __name__ == "__main__":
    build()
