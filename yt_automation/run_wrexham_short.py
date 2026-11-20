"""
run_wrexham_short.py — Today's video (2026-08-17). Genuinely trending-topic
research, per explicit direction to stop defaulting to evergreen facts and
find what's actually being searched/watched TODAY. Checked current news:
55 European nations threatening a World Cup boycott over FIFA's private
equity plan is the single biggest current football story, but it's
governance/political -- no real visual referent, would repeat the exact
"visuals don't connect" problem already flagged. Wrexham AFC is the better
match: three consecutive promotions (2022-23 National League -> EFL,
2023-24 -> League One, 2024-25 -> Championship) under Ryan Reynolds/Rob
McElhenney ownership since Nov 2020, and TODAY (Aug 17) is their actual
first-ever EFL Championship match, against Cardiff City. Genuinely
trending right now (not evergreen), globally known well beyond core
football fans via the Hulu/Disney+ documentary, and has the same
"surprising number" hook pattern already proven on this channel (26.2
miles, 10 feet). Verified via si.com, npr.org, nbcnews.com, aljazeera.com.

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
    "hook": "Non-league to England's second division. In just 3 years.",
    "body": (
        "Wrexham AFC has been promoted three years in a row -- from the "
        "National League all the way to the Championship. Owned by Ryan "
        "Reynolds and Rob McElhenney since 2020, they're now one step "
        "from the Premier League. Today, they play their first-ever "
        "Championship match, against Cardiff City."
    ),
    "cta": "Can Wrexham make it four promotions in a row? Comment your prediction and subscribe!",
    "title": "3 Promotions in 3 Years. Today's Their Biggest Game Yet #shorts",
    "tags": ["wrexham", "wrexhamafc", "ryanreynolds", "robmcelhenney", "championship", "football", "soccer", "shorts", "viral"],
    "seo_description": "Wrexham AFC has been promoted three years running, from non-league to the Championship. They play their first-ever Championship match today. #wrexham #football",
    "queries": ["soccer stadium promotion celebration", "football pitch crowd", "soccer team celebration trophy"],
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
    cc.save_compliance_report(check, video_id="wrexham_short")
    if not check["passed"]:
        raise RuntimeError(f"COMPLIANCE FAILED: {check['issues']}")
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "wrexham_short.mp4")
    log(f"Assembling video -> {out_path}")
    psc.assemble(clip_paths, SCRIPT, vo_path, music_path, out_path)

    log(f"BUILD COMPLETE (not uploaded yet) -> {out_path}")
    return out_path, vo_path


if __name__ == "__main__":
    build()
