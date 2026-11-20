"""
run_ipswich_sunderland_short.py — Built 2026-08-25, replaces Alcaraz in
the 8-video private batch. Swapped for the same reason as the Hull/Man
United replacement -- Pixabay's tennis-adjacent inventory on this account
is completely dry right now, and forcing a third tennis build through
the same expensive workaround isn't a good use of the remaining batch.

Verified via ESPN, VAVEL (2026-08-22): Jack Clarke scored a 90th-minute
winner to give newly-promoted Ipswich Town a 2-1 win over his old club
Sunderland on opening day. Emersonn scored first for Ipswich (24'),
Nilson Angulo equalized for Sunderland with a free kick, before Clarke's
late winner. trend_research confirms real interest ("ipswich sunderland",
"jack clarke ipswich goal" both return live suggestions). topic_checker:
not a duplicate.

Per standing process: does NOT auto-upload from this file. Builds and
renders only; upload happens as a separate, explicit step after local
frame/duration verification, and per this batch's instruction goes up
as private, not public.
"""
import os
import config

config.assert_safe_pipeline()

import pro_shorts_creator as psc
import copyright_compliance as cc
from logger import log

SCRIPT = {
    "hook": "Jack Clarke beat his old club with a 90th-minute winner.",
    "body": (
        "Ipswich Town were level with Sunderland at 1-1 deep into "
        "stoppage time when Clarke scored to win it 2-1 -- against the "
        "club that let him go, on opening day of the new season."
    ),
    "cta": "Is there a better feeling than beating your old club? Comment and subscribe!",
    "title": "Jack Clarke Beat His Old Club With a 90th-Minute Winner #shorts",
    "tags": ["jackclarke", "ipswichtown", "sunderland", "premierleague", "football", "shorts", "viral"],
    "seo_description": "Jack Clarke scored a 90th-minute winner as Ipswich Town beat his old club Sunderland 2-1 on opening day. #ipswichtown #sunderland #premierleague",
    "queries": ["soccer stadium", "soccer match", "football training"],
}


def build():
    import topic_checker as tc
    check = tc.check_final_script_footage(SCRIPT)
    weak = [q for q, n in check.items() if n == 0]
    if weak:
        log(f"WARNING: real pipeline queries with 0 usable footage: {weak} -- proceeding, download_clips() will broaden/retry")

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
    cc.save_compliance_report(check, video_id="ipswich_sunderland_short")
    if not check["passed"]:
        raise RuntimeError(f"COMPLIANCE FAILED: {check['issues']}")
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "ipswich_sunderland_short.mp4")
    log(f"Assembling video -> {out_path}")
    psc.assemble(clip_paths, SCRIPT, vo_path, music_path, out_path)

    log(f"BUILD COMPLETE (not uploaded yet) -> {out_path}")
    return out_path, vo_path


if __name__ == "__main__":
    build()
