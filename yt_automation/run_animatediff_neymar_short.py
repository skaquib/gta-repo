"""
run_animatediff_neymar_short.py — One-shot: generate original AnimateDiff
clips locally (free, no external API credits), assemble Neymar's retirement
tribute Short with cloned-voice narration, real word-synced captions,
animated like+subscribe button, then upload via the existing pipeline.
"""
import config

config.assert_safe_pipeline()

import pro_shorts_creator as psc
import copyright_compliance as cc
from logger import log
import os

SCRIPT = {
    "hook": "One stadium. Sixteen years apart. His story ended where it began.",
    "body": (
        "August 2010. Neymar's first cap for Brazil. MetLife Stadium, New York. "
        "July 5th, 2026. His last cap for Brazil. The same stadium. Eighty goals. "
        "One hundred twenty-nine caps. Brazil's all-time top scorer. And then, he cried."
    ),
    "cta": "Sixteen years, one stadium, a career complete. What's your favorite Neymar moment? Comment and subscribe!",
    "title": "One Stadium. Sixteen Years. Neymar's Story Complete #shorts #neymar #worldcup2026",
    "tags": ["neymar", "brazil", "worldcup2026", "football", "soccer", "shorts", "viral", "selecao", "retirement"],
    "seo_description": "Neymar's international career began and ended at the same stadium, sixteen years apart. #worldcup2026 #neymar #football",
    "queries": [
        "young athletic footballer walking through a stadium tunnel toward bright light, hopeful determined expression, first steps of a journey",
        "footballer standing alone at center of stadium pitch, emotional tears, teammates comforting him, dramatic lighting",
        "stadium crowd cheering with flags waving, warm golden light, celebratory atmosphere",
    ],
}


def main():
    log("Generating original AnimateDiff clips locally (free, no external credits)...")
    clip_paths = psc.generate_anime_clips(SCRIPT)
    log(f"Generated {len(clip_paths)} clip(s): {clip_paths}")

    log("Generating voiceover (cloned voice first)...")
    vo_path = psc.generate_voiceover(SCRIPT)

    log("Generating background music...")
    music_path = psc.get_music(duration=26.0)

    log("Running compliance check...")
    check = cc.validate_before_upload(SCRIPT, clip_paths, music_path)
    cc.save_compliance_report(check, video_id="neymar_tribute_short")
    if not check["passed"]:
        log(f"COMPLIANCE FAILED: {check['issues']}")
        return
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "neymar_tribute_short.mp4")
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
