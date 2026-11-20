"""
run_wnba_stewart_short.py — Next video in the queue (today, 2026-07-31,
already has 2 videos live -- this one is expected to be auto-scheduled to
tomorrow by the normal same-day guard, no override).

Story: Breanna Stewart moved into the WNBA's all-time top-10 career scoring
list, but A'ja Wilson (33 pts/10 reb) and Jackie Young (27 pts, career-high
22 in the first half) led the Aces past the Liberty 104-99 on Thursday,
July 30, 2026. Real, fresh, verified -- basketball, adding variety after
today's tennis and football stories.
"""
import os
import config

config.assert_safe_pipeline()

import pro_shorts_creator as psc
import copyright_compliance as cc
from logger import log

SCRIPT = {
    "hook": "She just joined the WNBA's all-time top 10 scorers. And still lost.",
    "body": (
        "Thursday night, Breanna Stewart dropped 26 points, moving into "
        "10th on the WNBA's all-time career scoring list. It wasn't enough. "
        "A'ja Wilson answered with 33 points and 10 rebounds, and Jackie "
        "Young added 27 points, including a career-high 22 in the first "
        "half alone. The Las Vegas Aces held on late to beat the New York "
        "Liberty, 104 to 99."
    ),
    "cta": "Is A'ja Wilson still the best player in the WNBA? Comment your take and subscribe!",
    "title": "She Made WNBA History... And Still Lost #shorts #wnba",
    "tags": ["wnba", "ajawilson", "jackieyoung", "breannastewart", "lasvegasaces", "basketball", "shorts", "viral"],
    "seo_description": "Breanna Stewart moved into the WNBA's all-time top 10 scorers, but A'ja Wilson and Jackie Young led the Aces past the Liberty 104-99. #wnba #basketball",
    "queries": ["basketball player dunk", "basketball arena crowd", "basketball game action"],
}


def main():
    log("Downloading real stock footage (tag-verified, cross-video deduped)...")
    clip_paths = psc.download_clips(SCRIPT)

    log("Generating voiceover (cloned voice + persona sign-off)...")
    vo_path = psc.generate_voiceover(SCRIPT)

    log("Generating background music...")
    music_path = psc.get_music(duration=26.0)

    log("Running compliance check...")
    check = cc.validate_before_upload(SCRIPT, clip_paths, music_path)
    cc.save_compliance_report(check, video_id="wnba_stewart_short")
    if not check["passed"]:
        log(f"COMPLIANCE FAILED: {check['issues']}")
        return
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "wnba_stewart_short.mp4")
    log(f"Assembling video -> {out_path}")
    psc.assemble(clip_paths, SCRIPT, vo_path, music_path, out_path)

    log("Uploading...")
    url = psc.upload(out_path, SCRIPT, vo_path)
    if url:
        log(f"DONE — live at {url}")
    else:
        log("Upload did not return a URL — check logs above.")


if __name__ == "__main__":
    main()
