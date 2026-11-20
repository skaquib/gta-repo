"""
run_90minutes_short.py -- Built 2026-09-12.

Format chosen from channel data, not instinct. The "Why Is X EXACTLY Y?"
series averages 757 views vs the 396 channel average, and owns the
channel record (marathon 26.2 miles, 1687v) plus the best retention ever
recorded here (bowling lane 60ft, 1124v @ 95.2% avg view pct). Series
spread is 1687 / 1124 / 819 / 144 / 11 -- the losers (Olympic pool 50m,
cricket pitch 22 yards) failed because the number was either too round
to feel mysterious or too obscure for anyone to have wondered about it.
Winners pair a famous, oddly specific number with an object the viewer
has personally encountered. "90 minutes" is the most-watched number in
world sport and almost nobody can explain it -- and football is this
channel's core sport and largest audience.

Verified 2026-09-12 via Wikipedia (London v Sheffield, 1866),
football-stadiums.co.uk, sportsdigest.in, alloftheball.com: the first
recorded 90-minute match was London v Sheffield at Battersea Park on
31 March 1866. Sheffield FA custom favoured two-hour games, London/FA
clubs favoured much shorter ones; 45 minutes a half was the compromise
struck for that single fixture. The two rulebooks amalgamated in 1877
and 90 minutes entered the FA laws.

topic_checker: not a duplicate -- no existing title contains "90
minute", "minutes", or "football match".

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
    "hook": "A football match is exactly 90 minutes -- and nobody ever actually chose that number.",
    "body": (
        "In 1866, London and Sheffield had never played each other, and "
        "their rulebooks disagreed. Sheffield played two-hour games. "
        "London wanted far shorter. Neither side would move, so at "
        "Battersea Park they split the difference -- forty-five minutes "
        "each way. It was meant to settle one single match. In 1877 the "
        "two rulebooks merged, ninety minutes went into the laws, and "
        "the entire planet has played to a one-off compromise ever since."
    ),
    "cta": "Did you know the most famous number in sport was just two cities refusing to budge? Comment and subscribe!",
    "title": "Why Is a Football Match EXACTLY 90 Minutes? #shorts",
    "tags": ["football", "soccer", "90minutes", "shorts", "viral", "sportsfacts", "footballfacts"],
    "seo_description": (
        "A football match lasts exactly 90 minutes because London and Sheffield "
        "couldn't agree in 1866 -- so they split the difference for one match, and "
        "the world never changed it. #football #soccer #sportsfacts"
    ),
    "queries": ["soccer match stadium", "soccer players running pitch", "soccer ball goal net"],
}


def build():
    import topic_checker as tc
    check = tc.check_final_script_footage(SCRIPT)
    weak = [q for q, n in check.items() if n == 0]
    if weak:
        log(f"WARNING: real pipeline queries with 0 usable footage: {weak} -- proceeding, download_clips() will broaden/retry")

    log("Downloading real stock footage (vision-gated for soccer relevance)...")
    clip_paths = psc.download_clips(SCRIPT)

    log("Generating voiceover (cloned voice + persona sign-off)...")
    vo_path = psc.generate_voiceover(SCRIPT)

    from moviepy import AudioFileClip
    vo_dur = min(AudioFileClip(vo_path).duration + 1.5, 90.0)
    log("Generating background music...")
    music_path = psc.get_music(duration=vo_dur, script=SCRIPT)

    log("Running compliance check...")
    check = cc.validate_before_upload(SCRIPT, clip_paths, music_path)
    cc.save_compliance_report(check, video_id="90minutes_short")
    if not check["passed"]:
        raise RuntimeError(f"COMPLIANCE FAILED: {check['issues']}")
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "90minutes_short.mp4")
    log(f"Assembling video -> {out_path}")
    psc.assemble(clip_paths, SCRIPT, vo_path, music_path, out_path)

    log(f"BUILD COMPLETE (not uploaded yet) -> {out_path}")
    return out_path, vo_path


if __name__ == "__main__":
    build()
