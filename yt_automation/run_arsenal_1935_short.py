"""
run_arsenal_1935_short.py — Today's video (2026-08-19). Decided from real
research, not assumption, per explicit direction to check globally what's
actually trending before locking a topic.

Checked three live candidates: Premier League season start (Fri Aug 21),
US Open tennis (qualifying starts Aug 23, main draw Aug 30), and general
transfer-window news (window closes Sept 1). US Open has no live drama yet
-- 4-11 days out, nothing has actually happened. Premier League is 2 days
out AND already generating breaking news today (Chelsea signing Quenda,
Man City's post-Guardiola spending spree, Tchouameni committing to Real
Madrid over United). Confirmed via Al Jazeera's season preview
(aljazeera.com/sports/2026/8/18) and ESPN/Sky Sports transfer coverage.

Picked the single cleanest verified fact over the more complex, still-
developing transfer sagas: Arsenal ended a 22-year title wait last season,
but the last time Arsenal specifically retained the league title --
won it back-to-back -- was 1935 (91 years ago), per Al Jazeera's reporting.
This is NOT "no team has done this since 1935" (Man City alone won four
straight 2021-2024) -- it's specific to Arsenal's own history. Script
below is worded to keep that distinction accurate.

Real search-interest check (trend_research.py autocomplete, not assumed):
"arsenal premier league" surfaces "arsenal premier league champions",
"arsenal premier league title" as live suggestions -- genuine current
interest, not manufactured.

topic_checker.py verdict: GO. Not a duplicate title. Confirmed footage
available and duration-safe (>=15s) for "soccer stadium" (5 clips),
"soccer match" (3 clips), "football training" (1 clip) -- used as the
`queries` list below. Generic queries only: stock libraries don't carry
Arsenal/Premier League brand-specific footage, so the script's specificity
comes from narration, not from footage pretending to be Arsenal-specific.

Per standing process: does NOT auto-upload. Builds and renders, then stops
for local verification (frame check + full-duration check) before anything
goes live.
"""
import os
import config

config.assert_safe_pipeline()

import pro_shorts_creator as psc
import copyright_compliance as cc
from logger import log

SCRIPT = {
    "hook": "It's been 91 years since Arsenal did this.",
    "body": (
        "Arsenal just ended a 22-year wait for the Premier League title. "
        "Now they're defending it. But the last time Arsenal actually "
        "retained the title -- won it back-to-back -- was 1935. Every "
        "other major English club has done it since. Arsenal haven't. "
        "Their title defense starts this weekend against Coventry City."
    ),
    "cta": "Do they finally break the 91-year streak? Comment your prediction and subscribe!",
    "title": "It's Been 91 Years Since Arsenal Did This #shorts",
    "tags": ["arsenal", "arsenalfc", "premierleague", "football", "soccer", "shorts", "viral", "premierleague2026"],
    "seo_description": "Arsenal are defending the Premier League title, but they haven't retained it back-to-back since 1935. Their defense starts this weekend. #arsenal #premierleague #football",
    "queries": ["soccer stadium", "soccer match", "football training"],
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
    cc.save_compliance_report(check, video_id="arsenal_1935_short")
    if not check["passed"]:
        raise RuntimeError(f"COMPLIANCE FAILED: {check['issues']}")
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "arsenal_1935_short.mp4")
    log(f"Assembling video -> {out_path}")
    psc.assemble(clip_paths, SCRIPT, vo_path, music_path, out_path)

    log(f"BUILD COMPLETE (not uploaded yet) -> {out_path}")
    return out_path, vo_path


if __name__ == "__main__":
    build()
