"""
run_shot_clock_short.py — Built 2026-08-29, video 7 of the fresh
8-video batch. Curiosity-gap evergreen format (see run_olympic_pool_short.py
docstring for the data-driven reasoning).

Verified via WBUR/Only A Game, HMDB, Snopes (2026-08-29): the NBA
introduced the 24-second shot clock in 1954 after scoring had collapsed
-- the 1950 Fort Wayne Pistons vs Minneapolis Lakers game finished 19-18,
the lowest-scoring game in NBA history, because teams simply held the
ball once ahead. Danny Biasone and Leo Ferris calculated 24 seconds by
dividing 2,880 (seconds in a 48-minute game) by 120 (average shots per
team). League scoring rose 13.6 points per game in the first season with
the clock. trend_research confirms real interest ("shot clock" returns
live suggestions). topic_checker: not a duplicate; footage confirmed for
"basketball" (7 clips).

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
    "hook": "The NBA's 24-second shot clock exists because of the worst game in league history.",
    "body": (
        "In 1950, the Fort Wayne Pistons beat the Minneapolis Lakers "
        "19 to 18 -- teams were just holding the ball once they were "
        "ahead. In 1954, Danny Biasone fixed it with math: divide 2,880 "
        "seconds in a game by 120 average shots, and you get 24. "
        "Scoring jumped by almost 14 points a game overnight."
    ),
    "cta": "Could basketball even work without it? Comment and subscribe!",
    "title": "Why Is the NBA Shot Clock EXACTLY 24 Seconds? #shorts",
    "tags": ["nba", "basketball", "shotclock", "shorts", "viral", "sportsfacts"],
    "seo_description": "The NBA's 24-second shot clock came from real math, invented after the lowest-scoring game in league history. #nba #basketball #sportsfacts",
    "queries": ["basketball", "basketball court", "basketball player"],
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
    cc.save_compliance_report(check, video_id="shot_clock_short")
    if not check["passed"]:
        raise RuntimeError(f"COMPLIANCE FAILED: {check['issues']}")
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "shot_clock_short.mp4")
    log(f"Assembling video -> {out_path}")
    psc.assemble(clip_paths, SCRIPT, vo_path, music_path, out_path)

    log(f"BUILD COMPLETE (not uploaded yet) -> {out_path}")
    return out_path, vo_path


if __name__ == "__main__":
    build()
