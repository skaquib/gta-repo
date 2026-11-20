"""
run_hull_united_short.py — Built 2026-08-25, replaces Sabalenka in the
8-video private batch. Swapped after Pixabay's tennis-adjacent inventory
on this account came up completely dry across every query tried (tennis,
tennis court/ball/racket/player, sports court, stadium crowd, crowd
cheering -- all 0 unused matches) following the Sinner video's build.
Rather than force two more tennis builds through the same expensive
workaround, swapped to football, where inventory has been reliable all
session. Different match/story from every other video in this batch
(Everton, Brentford, Leeds, Inter, Bayern) -- no repeat.

Verified via ESPN, Sky Sports, beIN Sports, NBC Sports (2026-08-22, 7+
independent sources agree): Hull City beat Manchester United 2-0 at MKM
Stadium on opening day -- Semi Ajayi (17') and Nobel Mendy (38', on his
Premier League debut, from a Slater free-kick) scored. This was Hull's
first-ever Premier League victory over Manchester United. A "0-1"
autocomplete suggestion was checked and found to be noise/unrelated --
7+ independent sources agree on 2-0. trend_research confirms real
interest ("hull city manchester united" returns live suggestions).
topic_checker.py: not a duplicate (distinct from the existing Hull
promotion video, which covers the 9-year return story, not this result).

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
    "hook": "Hull City just beat Manchester United for the first time ever.",
    "body": (
        "Semi Ajayi and Nobel Mendy scored as newly promoted Hull won "
        "2-0 at home. Mendy's goal came on his Premier League debut. "
        "Hull had never beaten Manchester United in the league before "
        "this."
    ),
    "cta": "Is this the start of a special season for Hull? Comment your prediction and subscribe!",
    "title": "Hull City Just Beat Manchester United for the First Time Ever #shorts",
    "tags": ["hullcity", "manchesterunited", "premierleague", "football", "soccer", "shorts", "viral"],
    "seo_description": "Hull City beat Manchester United 2-0, their first-ever Premier League win over United, with goals from Semi Ajayi and Nobel Mendy. #hullcity #manchesterunited #premierleague",
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
    cc.save_compliance_report(check, video_id="hull_united_short")
    if not check["passed"]:
        raise RuntimeError(f"COMPLIANCE FAILED: {check['issues']}")
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "hull_united_short.mp4")
    log(f"Assembling video -> {out_path}")
    psc.assemble(clip_paths, SCRIPT, vo_path, music_path, out_path)

    log(f"BUILD COMPLETE (not uploaded yet) -> {out_path}")
    return out_path, vo_path


if __name__ == "__main__":
    build()
