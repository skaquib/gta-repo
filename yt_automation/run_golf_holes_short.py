"""
run_golf_holes_short.py — Built 2026-08-29, video 6 of the fresh
8-video batch. Curiosity-gap evergreen format (see run_olympic_pool_short.py
docstring for the data-driven reasoning). Distinct from the earlier
golf-ball-dimples video already on the channel -- this is about the
18-hole round format, not dimples.

Verified via Scottish Golf History, treetops.com, golferhive.com
(2026-08-29): the Old Course at St Andrews originally had 12 holes,
played as a 22-hole round (10 holes played twice). In 1764, the Royal &
Ancient Golf Club judged some holes too short and merged the first four
into two, creating the 18-hole round. St Andrews' prestige as "the Home
of Golf" made other clubs worldwide adopt the format. trend_research
confirms real interest ("why is golf 18 holes" returns a live
suggestion). topic_checker: not a duplicate; footage confirmed for "golf
course" (8 clips).

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
    "hook": "Golf has exactly 18 holes because of a decision made in 1764.",
    "body": (
        "The Old Course at St Andrews originally had 12 holes, played "
        "twice for a 22-hole round. In 1764, the Royal and Ancient Golf "
        "Club decided some holes were too short and merged four of them "
        "into two -- creating 18 holes. St Andrews was so influential "
        "that every course in the world eventually copied it."
    ),
    "cta": "Did you know it wasn't always 18? Comment and subscribe!",
    "title": "Why Golf Has Exactly 18 Holes -- Not 10 or 20 #shorts",
    "tags": ["golf", "golffacts", "standrews", "shorts", "viral", "sportsfacts"],
    "seo_description": "Golf has exactly 18 holes because of a 1764 decision at St Andrews, the Home of Golf. #golf #sportsfacts #shorts",
    "queries": ["golf course", "golf swing", "golf player"],
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
    cc.save_compliance_report(check, video_id="golf_holes_short")
    if not check["passed"]:
        raise RuntimeError(f"COMPLIANCE FAILED: {check['issues']}")
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "golf_holes_short.mp4")
    log(f"Assembling video -> {out_path}")
    psc.assemble(clip_paths, SCRIPT, vo_path, music_path, out_path)

    log(f"BUILD COMPLETE (not uploaded yet) -> {out_path}")
    return out_path, vo_path


if __name__ == "__main__":
    build()
