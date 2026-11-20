"""
run_veo_fontaine_short.py — One-shot: assemble and publish the Just Fontaine
13-goal record Short from the Veo-generated clip in output/anime_clips/,
narrated in the cloned voice, real word-synced captions, then upload
(thumbnail + engagement comment + captions) via the existing pipeline.
"""
import os
import config

config.assert_safe_pipeline()

import pro_shorts_creator as psc
import copyright_compliance as cc
from logger import log

VEO_CLIP = os.path.join(config.OUTPUT_DIR, "anime_clips", "veo_fontaine_1958.mp4")

SCRIPT = {
    "hook": "13 goals. One tournament. A record that's outlived 17 World Cups.",
    "body": (
        "In 1958, France's Just Fontaine scored 13 goals in just 6 matches — "
        "a scoring rate no player has matched since. Messi's best World Cup? "
        "7 goals, across 3 tournaments. Ronaldo? 8 goals, across 4 tournaments. "
        "Fontaine did nearly double that in ONE. He wasn't even France's "
        "first-choice striker — he only started because of an injury. Since "
        "1958, 17 more World Cups have been played. Nobody has come within "
        "4 goals of him."
    ),
    "cta": "Could someone finally break it at World Cup 2026? Drop your pick below and subscribe for more football history!",
    "title": "13 GOALS in ONE World Cup — Unbroken in 68 Years #shorts #worldcup2026 #football",
    "tags": ["worldcup2026", "justfontaine", "football", "record", "history", "shorts", "soccer", "viral", "france"],
    "seo_description": "Just Fontaine's 13-goal record has survived 17 World Cups since 1958. #worldcup2026 #football #history",
}


def main():
    if not os.path.exists(VEO_CLIP):
        raise FileNotFoundError(f"Veo clip not found: {VEO_CLIP}")

    clip_paths = [VEO_CLIP, VEO_CLIP, VEO_CLIP]  # single continuous clip, sliced per segment

    log("Generating voiceover (cloned voice first)...")
    vo_path = psc.generate_voiceover(SCRIPT)

    log("Generating background music...")
    music_path = psc.get_music(duration=26.0)

    log("Running compliance check...")
    check = cc.validate_before_upload(SCRIPT, clip_paths, music_path)
    cc.save_compliance_report(check, video_id="fontaine_short")
    if not check["passed"]:
        log(f"COMPLIANCE FAILED: {check['issues']}")
        return
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "fontaine_1958_short.mp4")
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
