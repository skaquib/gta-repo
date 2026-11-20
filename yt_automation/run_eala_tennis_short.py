"""
run_eala_tennis_short.py — Today's video: 21-year-old Filipina Alex Eala
(world No. 28) came back from a set and a break down to upset Olympic gold
medalist Zheng Qinwen at the DC Open (July 28, 2026), winning 9 of the last
10 games. Real, fresh, verified underdog comeback -- tennis, keeping content
varied from the recent football/golf run.
"""
import os
import config

config.assert_safe_pipeline()

import pro_shorts_creator as psc
import copyright_compliance as cc
from logger import log

SCRIPT = {
    "hook": "Down a set and a break. Then she won 9 of the last 10 games.",
    "body": (
        "Alex Eala is 21 years old, ranked World Number 28, from the "
        "Philippines. At the DC Open, she faced Olympic gold medalist Zheng "
        "Qinwen -- a former World Number 4. Zheng took the first set. Eala "
        "was down a break in the second. Then she flipped the match "
        "completely, winning nine of the last ten games, including seven in "
        "a row, to win 4-6, 6-4, 6-1."
    ),
    "cta": "Is Alex Eala the Philippines' next tennis star? Comment your take and subscribe!",
    "title": "Down a Set, She Upset an Olympic Champion #shorts #tennis",
    "tags": ["tennis", "alexeala", "zhengqinwen", "dcopen", "philippines", "sports", "shorts", "viral", "underdog"],
    "seo_description": "21-year-old Alex Eala came back from a set down to upset Olympic gold medalist Zheng Qinwen at the DC Open. #tennis #alexeala",
    "queries": ["tennis player serve", "tennis match crowd", "tennis court celebration"],
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
    cc.save_compliance_report(check, video_id="eala_tennis_short")
    if not check["passed"]:
        log(f"COMPLIANCE FAILED: {check['issues']}")
        return
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "eala_tennis_short.mp4")
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
