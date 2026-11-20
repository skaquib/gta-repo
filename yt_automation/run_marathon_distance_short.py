"""
run_marathon_distance_short.py — Today's video (2026-08-14): curiosity-gap
explainer, not a news story. Deliberate pivot: news-story videos force
generic same-sport-but-wrong-context stock footage (we can't legally show
the actual match/player), which never truly "feels connected" no matter
how good the search terms are. An explainer about a generic object/fact
doesn't have that ceiling -- real stock footage of marathons/runners
directly IS the thing being described, sentence by sentence, the same way
the golf-dimples video verified frame-by-frame correct earlier.

Topic: why the marathon distance is oddly specific -- 26.2 miles. The 1908
London Olympics marathon was extended so the race could start at Windsor
Castle and finish in front of the royal box, adding exactly 385 yards.
That became the permanent official distance in 1921. Verified via
marathonhandbook.com, Britannica, HISTORY.com, Olympics.com.

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
    "hook": "The marathon distance is oddly specific. 26.2 miles. Here's why.",
    "body": (
        "The first Olympic marathon, in 1908, was supposed to be 25 miles. "
        "But organizers moved the start to Windsor Castle so the royal "
        "family could watch, and moved the finish right in front of the "
        "royal box. That added exactly 385 yards. In 1921, that number -- "
        "26 miles, 385 yards -- became the permanent official distance."
    ),
    "cta": "Would you have guessed a royal family set the marathon distance? Comment below and subscribe!",
    "title": "Why Is a Marathon EXACTLY 26.2 Miles? #shorts",
    "tags": ["marathon", "running", "olympics", "funfacts", "sportshistory", "shorts", "viral", "athletics"],
    "seo_description": "The marathon distance is 26.2 miles because of the British royal family's viewing box at the 1908 Olympics. #marathon #running #funfacts",
    "queries": ["marathon runners race", "running track finish line", "olympic stadium crowd"],
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
    cc.save_compliance_report(check, video_id="marathon_distance_short")
    if not check["passed"]:
        raise RuntimeError(f"COMPLIANCE FAILED: {check['issues']}")
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "marathon_distance_short.mp4")
    log(f"Assembling video -> {out_path}")
    psc.assemble(clip_paths, SCRIPT, vo_path, music_path, out_path)

    log(f"BUILD COMPLETE (not uploaded yet) -> {out_path}")
    return out_path, vo_path


if __name__ == "__main__":
    build()
