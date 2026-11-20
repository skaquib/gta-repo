"""
run_louisiana_upset_short.py — Built 2026-08-29, video 2 of the fresh
8-video batch (corrected strategy: see run_virtanen_shelton_short.py's
docstring for the data-driven reasoning).

Verified via Yahoo Sports (2026-08-29): Louisiana Christian, an NAIA-level
program, beat Northwestern State -- a Division I FCS team that offers
athletic scholarships -- 42-37 in Week 0 of the 2026 college football
season. It's the first time in history an NAIA team has beaten a
scholarship-offering Division I opponent. Louisiana Christian trailed
10-0 and 27-14 before outscoring Northwestern State 28-10 in the second
half. trend_research confirms real interest ("louisiana christian
northwestern state" returns live suggestions). topic_checker: not a
duplicate.

Real American-football stock footage is thin on this account (0-1 usable
clips across most queries) -- built with whatever generic sport/stadium
footage passes the tag-relevance filter; verified visually before
publish rather than assumed safe.

Per standing process: does NOT auto-upload from this file. Builds and
renders only; upload happens as a separate, explicit step after local
frame/duration verification.
"""
import os
import config

config.assert_safe_pipeline()

import pro_shorts_creator as psc
import copyright_compliance as cc
from logger import log

SCRIPT = {
    "hook": "An NAIA team just beat a Division I scholarship program for the first time ever.",
    "body": (
        "Louisiana Christian trailed Northwestern State 27-14 in the "
        "second half. They outscored them 28-10 the rest of the way to "
        "win 42-37 -- the first time in history an NAIA team has beaten "
        "a scholarship-offering Division I opponent."
    ),
    "cta": "Is this the biggest college football upset of the year? Comment and subscribe!",
    "title": "An NAIA Team Just Beat a Division I Team for the First Time Ever #shorts",
    "tags": ["collegefootball", "louisianachristian", "northwesternstate", "naia", "shorts", "viral", "upset"],
    "seo_description": "Louisiana Christian became the first NAIA team ever to beat a scholarship Division I opponent, rallying to beat Northwestern State 42-37. #collegefootball #upset #naia",
    "queries": ["sports stadium", "stadium crowd", "athletes running"],
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
    cc.save_compliance_report(check, video_id="louisiana_upset_short")
    if not check["passed"]:
        raise RuntimeError(f"COMPLIANCE FAILED: {check['issues']}")
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "louisiana_upset_short.mp4")
    log(f"Assembling video -> {out_path}")
    psc.assemble(clip_paths, SCRIPT, vo_path, music_path, out_path)

    log(f"BUILD COMPLETE (not uploaded yet) -> {out_path}")
    return out_path, vo_path


if __name__ == "__main__":
    build()
