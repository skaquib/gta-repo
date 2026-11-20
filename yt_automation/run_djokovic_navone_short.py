"""
run_djokovic_navone_short.py — Built 2026-09-02, first video produced under
the standing pre-push research checklist (see memory: pre-push-viral-research).

TOPIC DEMAND (the thing that was missing all August):
Novak Djokovic lost in the FIRST round of the 2026 US Open to Mariano Navone,
vomiting on court, cramping, taking a medical timeout, and weeping. This is
the biggest tennis story in the world right now and carries the largest name
in the sport. Verified 2026-09-02 across Bleacher Report, Fox/OutKick, TMZ,
Defector, and Northeastern News: Navone won 7-6(5), 5-7, 4-6, 6-2, 6-1 over
4h36m; Djokovic (39, 24 majors) had not lost a first-round major since the
2006 Australian Open; his pursuit of a record 25th major now waits until 2027.

WHY THIS TOPIC (real data, pulled 2026-09-02):
Monthly medians -- Jun (World Cup) 1131, Jul 353, Aug (evergreen trivia) 128.
August produced 1 subscriber from 29 videos. Every Jun/Jul top performer was
a live global event with a huge name. Evergreen trivia ("why is a bowling
lane 60 feet") is the lowest-demand content this channel has ever made. This
video deliberately returns to named-star + live-event + shock-result.

LENGTH (our own data, Jun 1 - Sep 2, retention by duration bucket):
  <=20s -> 97.7% avg retention | 21-25s -> 117.4% (>100% = loops/replays)
  26-30s -> 49.0% | 31-35s -> 38.7% | 36-45s -> 36.1% | 46s+ -> 25.6%
Recent videos have been 31-37s, sitting in the two worst retention buckets.
This script is deliberately cut to ~55 words (~22-25s with persona sign-off)
to land in the 21-25s loop-friendly band.

Per standing process: does NOT auto-upload. Builds and renders only; upload
happens as a separate explicit step after local frame/duration/tail verification.
"""
import os
import config

config.assert_safe_pipeline()

import pro_shorts_creator as psc
import copyright_compliance as cc
from logger import log

SCRIPT = {
    "hook": "Novak Djokovic just lost in the first round of the US Open -- while throwing up on court.",
    "body": (
        "He vomited, cramped, and broke down in tears as Mariano "
        "Navone beat him in five sets. Djokovic hasn't lost a "
        "first-round major since 2006. The chase for number 25 now "
        "waits until 2027."
    ),
    "cta": "Is this the end? Comment below!",
    "title": "Djokovic Threw Up and Lost in the FIRST Round of the US Open #shorts",
    "tags": ["djokovic", "usopen", "tennis", "navone", "shorts", "viral", "upset", "sportsnews"],
    "seo_description": "Novak Djokovic lost in the first round of the 2026 US Open to Mariano Navone, vomiting and cramping on court. His first opening-round major exit since 2006. #djokovic #usopen #tennis",
    "queries": ["tennis match", "tennis player serve", "tennis stadium crowd"],
}


def build():
    photo = psc.try_athlete_photo_hook("Novak Djokovic")
    print("Photo:", photo)

    log("Downloading remaining stock footage...")
    clip_paths_all = psc.download_clips(SCRIPT)
    if photo:
        clip_paths = [photo["video_path"]] + clip_paths_all[:2]
    else:
        clip_paths = clip_paths_all

    log("Generating voiceover...")
    vo_path = psc.generate_voiceover(SCRIPT)

    from moviepy import AudioFileClip
    vo_dur = min(AudioFileClip(vo_path).duration + 1.5, 90.0)
    log(f"Voiceover length: {AudioFileClip(vo_path).duration:.1f}s (target: 21-25s band)")
    music_path = psc.get_music(duration=vo_dur, script=SCRIPT)

    log("Running compliance check...")
    check = cc.validate_before_upload(SCRIPT, clip_paths, music_path)
    cc.save_compliance_report(check, video_id="djokovic_navone_short")
    if not check["passed"]:
        raise RuntimeError(f"COMPLIANCE FAILED: {check['issues']}")
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "djokovic_navone_short.mp4")
    log(f"Assembling video -> {out_path}")
    psc.assemble(clip_paths, SCRIPT, vo_path, music_path, out_path)

    log(f"BUILD COMPLETE (not uploaded yet) -> {out_path}")
    return out_path, vo_path


if __name__ == "__main__":
    build()
