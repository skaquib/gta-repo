"""
run_veo_pele_short.py — One-shot: assemble and publish the "3 World Cups, one
player" Short (Pele's unmatched 1958/1962/1970 record) from the Veo-generated
clip in output/anime_clips/, narrated in the cloned voice, real word-synced
captions, animated like+subscribe button, then upload (thumbnail + engagement
comment + captions) via the existing pipeline.
"""
import os
import config

config.assert_safe_pipeline()

import pro_shorts_creator as psc
import copyright_compliance as cc
from logger import log

VEO_CLIP = os.path.join(config.OUTPUT_DIR, "anime_clips", "veo_pele_3wc.mp4")

SCRIPT = {
    "hook": "Three World Cups. One player. Nobody else has ever done it.",
    "body": (
        "Pele won it in 1958, then 1962, then 1970 — three different eras. "
        "He was just 17 for his first title. Messi has one. Ronaldo has zero. "
        "In 68 years, nobody has matched three."
    ),
    "cta": "Will 2026 finally be the year? Comment your pick and subscribe!",
    "title": "3 WORLD CUPS. ONE PLAYER. Unmatched in 68 Years #shorts #worldcup2026 #football",
    "tags": ["worldcup2026", "pele", "football", "record", "history", "shorts", "soccer", "viral", "brazil"],
    "seo_description": "Pele is still the only player to win 3 World Cups -- 1958, 1962, 1970. #worldcup2026 #football #history",
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
    cc.save_compliance_report(check, video_id="pele_3wc_short")
    if not check["passed"]:
        log(f"COMPLIANCE FAILED: {check['issues']}")
        return
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "pele_3wc_short.mp4")
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
