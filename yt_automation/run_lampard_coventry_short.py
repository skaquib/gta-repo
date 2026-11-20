"""
run_lampard_coventry_short.py — Rebuilt 2026-08-22 with the real result.
Originally built 2026-08-21 with future-tense "tonight...can Lampard pull
off the upset" framing, but the same-day guard pushed the scheduled
publish past kickoff, so that version was deleted before it could go live
with stale framing (never publish about a future event as if it hasn't
happened once it has).

Real result, verified via ESPN (2026-08-22): Arsenal 3-0 Coventry City,
Emirates Stadium, 2026-08-21. Kai Havertz (15'), Bukayo Saka (23'), and
Martin Odegaard (49') scored. Coventry's return to the Premier League
after 25 years under Frank Lampard started with a comfortable defeat, not
an upset -- script rewritten to reflect that honestly rather than force
the original "can he pull it off" angle.

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
    "hook": "Frank Lampard's first Premier League match in 25 years ended in a 3-0 defeat.",
    "body": (
        "Coventry City returned to the top flight for the first time in a "
        "quarter century, and their opener came away at Arsenal, the "
        "defending champions. Kai Havertz, Bukayo Saka, and Martin "
        "Odegaard all scored as Arsenal won 3-0 at the Emirates."
    ),
    "cta": "Can Lampard turn it around from here? Comment your prediction for the season and subscribe!",
    "title": "Frank Lampard's Coventry Lost 3-0 in Their First Premier League Match in 25 Years #shorts",
    "tags": ["franklampard", "coventrycity", "coventry", "premierleague", "arsenal", "football", "soccer", "shorts", "viral"],
    "seo_description": "Frank Lampard managed Coventry City back into the Premier League for the first time in 25 years, but their opener ended in a 3-0 defeat away at Arsenal. #coventry #lampard #premierleague",
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
    cc.save_compliance_report(check, video_id="lampard_coventry_short")
    if not check["passed"]:
        raise RuntimeError(f"COMPLIANCE FAILED: {check['issues']}")
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "lampard_coventry_short.mp4")
    log(f"Assembling video -> {out_path}")
    psc.assemble(clip_paths, SCRIPT, vo_path, music_path, out_path)

    log(f"BUILD COMPLETE (not uploaded yet) -> {out_path}")
    return out_path, vo_path


if __name__ == "__main__":
    build()
