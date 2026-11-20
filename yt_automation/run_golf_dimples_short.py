"""
run_golf_dimples_short.py — First video in a new format test: curiosity-gap
sports-science explainer, modeled on mrfact (103K subs, 74M views) whose
top performers ("This Basketball Net Installs Itself" - 4.96M views, "Why
basketball hoops actually have nets" - 780K) are evergreen "why does this
everyday sports object work that way" videos, not news tied to a famous
athlete. This removes the two structural problems the news-commentary
format had: (1) dependent on something big happening that day, (2) views
riding someone else's pre-existing fame instead of the channel's own hook.

Topic: why golf balls have dimples -- a genuinely counter-intuitive physics
fact (a dimpled ball flies roughly double the distance of a smooth one).
Script drafted with Gemini (gemini-2.5-flash), then fit into the existing
compliant pipeline (real stock footage, cloned voice, compliance checks).
"""
import os
import config

config.assert_safe_pipeline()

import pro_shorts_creator as psc
import copyright_compliance as cc
from logger import log

SCRIPT = {
    "hook": "A smooth golf ball would fly less than half as far. Here's why.",
    "body": (
        "Without dimples, air breaks away from the ball early, creating a "
        "huge drag-inducing wake that kills its flight. Dimples create a "
        "thin, turbulent layer of air that hugs the surface longer. That "
        "turbulence cuts drag and adds lift, letting a dimpled ball fly "
        "roughly double the distance of a smooth one."
    ),
    "cta": (
        "Honestly, sports physics like this feels a little like magic to "
        "me. What's the wildest sports science fact you know? Drop it below."
    ),
    "title": "The Real Reason Golf Balls Have Dimples #shorts #golf",
    "tags": ["golf", "golfballs", "sportsscience", "physics", "funfacts", "shorts", "viral", "sports"],
    "seo_description": "Golf balls have dimples for a real physics reason -- they fly roughly double the distance of a smooth ball. #golf #sportsscience #shorts",
    "queries": ["golf ball close up", "golf ball flying slow motion", "golf driving range"],
}


def main():
    log("Downloading real stock footage (tag-verified, cross-video deduped)...")
    clip_paths = psc.download_clips(SCRIPT)

    log("Generating voiceover (cloned voice + persona sign-off)...")
    vo_path = psc.generate_voiceover(SCRIPT)

    log("Generating background music...")
    music_path = psc.get_music(duration=26.0)

    log("Running compliance check...")
    check = cc.validate_before_upload(SCRIPT, clip_paths, music_path)
    cc.save_compliance_report(check, video_id="golf_dimples_short")
    if not check["passed"]:
        log(f"COMPLIANCE FAILED: {check['issues']}")
        return
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "golf_dimples_short.mp4")
    log(f"Assembling video -> {out_path}")
    psc.assemble(clip_paths, SCRIPT, vo_path, music_path, out_path)

    log("Uploading...")
    url = psc.upload(out_path, SCRIPT, vo_path)
    if url:
        log(f"DONE — live at {url}")
    else:
        log("Upload did not return a URL — check logs above.")


if __name__ == "__main__":
    main()
