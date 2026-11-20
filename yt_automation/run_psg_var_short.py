"""
run_psg_var_short.py — Today's video (2026-08-13): PSG beat Aston Villa
2-1 in the UEFA Super Cup, defending their title for the second year in a
row. Khvicha Kvaratskhelia opened the scoring, 17-year-old Brian Madjo
equalized for Villa right before halftime, and Desire Doue's 61st-minute
winner was overturned from offside to legal after a VAR review. Real,
fresh, verified.

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
    "hook": "The goal was ruled offside. Then VAR said it counts.",
    "body": (
        "PSG beat Aston Villa 2-1 to defend their UEFA Super Cup title for "
        "the second year in a row. Khvicha Kvaratskhelia opened the "
        "scoring, and 17-year-old Brian Madjo equalized for Villa right "
        "before halftime. Desire Doue's 61st-minute winner was first "
        "ruled offside, then overturned after a video review."
    ),
    "cta": "Was VAR right to overturn that call? Comment your take and subscribe!",
    "title": "PSG Win Back-to-Back... After a VAR Reversal #shorts",
    "tags": ["psg", "astonvilla", "uefasupercup", "football", "soccer", "var", "shorts", "viral"],
    "seo_description": "PSG beat Aston Villa 2-1 to defend their UEFA Super Cup title, with the winning goal overturned from offside by VAR. #football #psg #uefasupercup",
    "queries": ["soccer stadium celebration", "football trophy lift", "soccer referee video review"],
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
    cc.save_compliance_report(check, video_id="psg_var_short")
    if not check["passed"]:
        raise RuntimeError(f"COMPLIANCE FAILED: {check['issues']}")
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "psg_var_short.mp4")
    log(f"Assembling video -> {out_path}")
    psc.assemble(clip_paths, SCRIPT, vo_path, music_path, out_path)

    log(f"BUILD COMPLETE (not uploaded yet) -> {out_path}")
    return out_path, vo_path


if __name__ == "__main__":
    build()
