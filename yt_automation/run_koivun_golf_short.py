"""
run_koivun_golf_short.py — Today's video: 21-year-old rookie Jackson Koivun
beat World No. 1 Scottie Scheffler by 3 strokes at the 3M Open, in just his
third professional tournament. Real, fresh, different sport (golf) --
deliberately not another football story, both to avoid the exact-title
duplicate that just happened and to keep matching the channel's broadened
"football, tennis, basketball, and beyond" niche.
"""
import os
import config

config.assert_safe_pipeline()

import pro_shorts_creator as psc
import copyright_compliance as cc
from logger import log

SCRIPT = {
    "hook": "21 years old. Third professional start. He just beat the best golfer alive.",
    "body": (
        "Jackson Koivun turned pro this year. In just his third tournament, "
        "he faced World Number One Scottie Scheffler at the 3M Open. Koivun "
        "won by three strokes. Scheffler has dominated golf for years. A "
        "21-year-old rookie just beat him on one of his first tries."
    ),
    "cta": "Is Koivun the next big thing in golf? Comment your take and subscribe!",
    "title": "21-Year-Old Rookie Just Beat World No. 1 Scottie Scheffler #shorts",
    "tags": ["golf", "jacksonkoivun", "scottiescheffler", "3mopen", "sports", "shorts", "viral", "underdog", "rookie"],
    "seo_description": "21-year-old Jackson Koivun beat World No. 1 Scottie Scheffler by 3 strokes in just his third pro tournament. #golf #sports",
    "queries": ["golf player swing", "golf course green", "golf crowd applause"],
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
    cc.save_compliance_report(check, video_id="koivun_golf_short")
    if not check["passed"]:
        log(f"COMPLIANCE FAILED: {check['issues']}")
        return
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "koivun_golf_short.mp4")
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
