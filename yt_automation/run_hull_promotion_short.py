"""
run_hull_promotion_short.py — Built 2026-08-22, today's second video
(9am/7pm daily cadence). Deliberately picked a topic with zero
outcome-dependency: Hull City play Manchester United today (kickoff
11:30 UTC), but this script is NOT about that match or its result --
learned from the Coventry incident not to write "today/tonight" framing
around an uncertain live outcome again. This is a fully settled,
already-decided fact instead.

Verified via ESPN, EFL.com, ITV (2026-08-22): Hull City beat Middlesbrough
1-0 in the Championship play-off final at Wembley (Oli McBurnie scoring
in stoppage time), returning to the Premier League for the first time
since 2017 -- a 9-year absence. trend_research autocomplete confirms real
current interest ("hull city promoted to premier league", "oli mcburnie
hull city" both return live suggestions). topic_checker.py: not a
duplicate; footage confirmed for "soccer stadium" (2 clips).

Per direct instruction 2026-08-22: uploaded as PRIVATE with no publishAt
scheduling at all, since publishAt has now gone public early/unpredictably
on three consecutive videos. This one stays private until explicitly
pushed public (by the user or on their explicit word), sidestepping
whatever is causing the scheduling bug entirely.

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
    "hook": "Hull City scored a stoppage-time winner to end a 9-year wait for the Premier League.",
    "body": (
        "Oli McBurnie's goal beat Middlesbrough 1-0 in the play-off final "
        "at Wembley, sending Hull City back to the top flight for the "
        "first time since 2017."
    ),
    "cta": "Do you think Hull City can stay up this season? Comment your prediction and subscribe!",
    "title": "Hull City Scored a Stoppage-Time Winner to End a 9-Year Wait #shorts",
    "tags": ["hullcity", "premierleague", "olimcburnie", "football", "soccer", "shorts", "viral", "championship"],
    "seo_description": "Hull City are back in the Premier League for the first time since 2017, after a stoppage-time play-off final winner from Oli McBurnie. #hullcity #premierleague #football",
    "queries": ["soccer stadium", "football training", "soccer players"],
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
    cc.save_compliance_report(check, video_id="hull_promotion_short")
    if not check["passed"]:
        raise RuntimeError(f"COMPLIANCE FAILED: {check['issues']}")
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "hull_promotion_short.mp4")
    log(f"Assembling video -> {out_path}")
    psc.assemble(clip_paths, SCRIPT, vo_path, music_path, out_path)

    log(f"BUILD COMPLETE (not uploaded yet) -> {out_path}")
    return out_path, vo_path


if __name__ == "__main__":
    build()
