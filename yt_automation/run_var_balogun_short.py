"""
run_var_balogun_short.py — One-shot: the Balogun red-card / presidential-call
controversy Short. Controversy/drama is the best-performing format in this
channel's real data (918 avg views vs 470-650 for other formats), and this
story is completely fresh -- not covered by any of the prior 50 videos.
Real Pixabay stock footage, cloned voice, real captions, custom thumbnail,
public immediate (same-day guard decides the actual publish slot).
"""
import os
import config

config.VISUAL_STYLE = "footage"
config.assert_safe_pipeline()

import pro_shorts_creator as psc
import visual_shorts_creator as vsc
import copyright_compliance as cc
from logger import log

SCRIPT = {
    "hook": "A red card. A presidential phone call. The ban reversed in hours.",
    "body": (
        "Folarin Balogun was shown a red card at World Cup 2026 -- an automatic "
        "ban under FIFA rules. Then the President of the United States called "
        "FIFA's president directly. Within hours, the ban was suspended. "
        "It's one of the strangest interventions in World Cup history."
    ),
    "cta": "Should politics ever get involved in football decisions? Comment your take and subscribe!",
    "title": "The Red Card Ban That Got Reversed By a Presidential Call #shorts #worldcup2026",
    "tags": ["worldcup2026", "var", "usmnt", "football", "shorts", "soccer", "controversy", "viral", "fifa"],
    "seo_description": "A World Cup 2026 red card ban got suspended after a direct call to FIFA's president. #worldcup2026 #var #football",
    "queries": ["soccer red card referee", "football stadium controversy", "soccer crowd reaction shock"],
}


def main():
    log("Downloading real stock footage (tag-verified, cross-video deduped)...")
    clip_paths = vsc.download_clips(SCRIPT)

    log("Generating voiceover (cloned voice first)...")
    vo_path = psc.generate_voiceover(SCRIPT)

    log("Generating background music...")
    music_path = psc.get_music(duration=26.0)

    log("Running compliance check...")
    check = cc.validate_before_upload(SCRIPT, clip_paths, music_path)
    cc.save_compliance_report(check, video_id="var_balogun_short")
    if not check["passed"]:
        log(f"COMPLIANCE FAILED: {check['issues']}")
        return
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "var_balogun_short.mp4")
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
