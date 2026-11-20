"""
run_newmanagers_short.py — Built 2026-08-21. Chosen specifically to be
publish-time-independent: unlike a Coventry/Lampard "tonight" angle, this
fact is already settled and doesn't go stale waiting for the same-day
guard to find a slot.

Verified via Al Jazeera (2026-08-18 season preview, already sourced
earlier this session): a record nine Premier League clubs opened the
season with a new permanent manager, including four of the league's
biggest -- Chelsea, Liverpool, Manchester City, and Manchester United.
trend_research autocomplete: the full compound phrase returns nothing
(too long/unnatural a query for autocomplete), but the individual club
angles are confirmed live ("chelsea new manager 2026", "liverpool new
manager arne slot" both return real current suggestions) -- the topic is
real, just not searched as one six-word sentence.

Hook fix applied per direct feedback on the last two videos: all four
recognizable names land in the first sentence, no easing in.

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
    "hook": "Chelsea, Liverpool, Man City, and Man United all have a new manager right now.",
    "body": (
        "Nine Premier League clubs enter this season with someone new "
        "standing on the touchline. Four of the league's biggest "
        "stadiums -- Stamford Bridge, Anfield, the Etihad, and Old "
        "Trafford -- have a different voice shouting instructions from "
        "the sideline this year. It's never happened to this many "
        "clubs in the same summer."
    ),
    "cta": "Which new manager succeeds first? Comment your pick and subscribe!",
    "title": "Chelsea, Liverpool, Man City, and Man United All Have a New Manager Right Now #shorts",
    "tags": ["chelsea", "liverpool", "mancity", "manutd", "premierleague", "football", "soccer", "shorts", "viral"],
    "seo_description": "A record nine Premier League clubs started the season with a new manager, including Chelsea, Liverpool, Manchester City and Manchester United. #premierleague #football #chelsea #liverpool",
    "queries": ["soccer stadium", "football training", "soccer coach"],
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
    cc.save_compliance_report(check, video_id="newmanagers_short")
    if not check["passed"]:
        raise RuntimeError(f"COMPLIANCE FAILED: {check['issues']}")
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "newmanagers_short.mp4")
    log(f"Assembling video -> {out_path}")
    psc.assemble(clip_paths, SCRIPT, vo_path, music_path, out_path)

    log(f"BUILD COMPLETE (not uploaded yet) -> {out_path}")
    return out_path, vo_path


if __name__ == "__main__":
    build()
