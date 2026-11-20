"""
run_mancity_maresca_short.py — Tomorrow's video (built 2026-08-20, scheduled
to publish 2026-08-21 08:30am IST via the new standing SCHEDULE_MODE). Real
research, different angle from today's Arsenal video (never repeat the same
day's story/topic).

Verified via ESPN, beIN Sports, Goal.com (2026-08-20): Pep Guardiola's
10-year Manchester City spell ended this summer, having won every major
trophy available to a club manager (completed the full set with the FIFA
Club World Cup, Dec 2023). Enzo Maresca -- his former assistant, most
recently Chelsea's manager -- has taken over on a 3-year contract. City's
actual first match under Maresca is Sunday Aug 23 vs Bournemouth (NOT
Aug 21) -- script deliberately says "this weekend", not "today", to stay
accurate against the 8:30am Aug 21 publish date.

trend_research.py autocomplete confirms real, current search interest:
"guardiola manchester city" and "maresca manchester city" both return
active suggestions. topic_checker.py: not a duplicate title; footage
confirmed for "soccer stadium" (4 clips) and "soccer match" (2 clips),
enough for a 3-segment video given the pipeline reuses across segments
when fewer than 3 distinct clips are available.

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
    "hook": "Manchester City have a new manager for the first time in 10 years.",
    "body": (
        "Pep Guardiola's decade at Manchester City ended after winning "
        "every major trophy available to a club manager. Now Enzo "
        "Maresca -- his former assistant -- takes over. Manchester City "
        "play their first Premier League match of the post-Guardiola era "
        "this weekend, against Bournemouth."
    ),
    "cta": "Can Maresca live up to a decade of Guardiola? Comment your prediction and subscribe!",
    "title": "Manchester City Have a New Manager For the First Time in 10 Years #shorts",
    "tags": ["mancity", "manchestercity", "guardiola", "maresca", "premierleague", "football", "soccer", "shorts", "viral"],
    "seo_description": "Pep Guardiola's decade at Manchester City has ended. Enzo Maresca takes charge for their first Premier League match of the new era. #mancity #guardiola #premierleague",
    "queries": ["soccer stadium", "soccer match", "soccer coach"],
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
    cc.save_compliance_report(check, video_id="mancity_maresca_short")
    if not check["passed"]:
        raise RuntimeError(f"COMPLIANCE FAILED: {check['issues']}")
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "mancity_maresca_short.mp4")
    log(f"Assembling video -> {out_path}")
    psc.assemble(clip_paths, SCRIPT, vo_path, music_path, out_path)

    log(f"BUILD COMPLETE (not uploaded yet) -> {out_path}")
    return out_path, vo_path


if __name__ == "__main__":
    build()
