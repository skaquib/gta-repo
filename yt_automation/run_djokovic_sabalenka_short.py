"""
run_djokovic_sabalenka_short.py — Built 2026-08-30 for the 7pm IST slot.
Named-opponent upset drama format (the other data-proven strong format
alongside curiosity-gap evergreen facts, per the mid-session strategy
pivot -- see run_virtanen_shelton_short.py's docstring for the full
reasoning).

Verified via usopen.org (official), ESPN, Sky Sports, Washington Times
(2026-08-30): top-seeded Novak Djokovic and Aryna Sabalenka were
eliminated in the very first round of the 2026 US Open mixed doubles by
Katerina Siniakova (world No. 1 in women's doubles) and Henry Patten,
losing 1-4, 4-2, 10-2 -- Siniakova closed out the match with an ace
serving directly to Djokovic. Match played Tuesday Aug 25; the wider US
Open singles main draw began today, Aug 30, so this is live, ongoing
tournament context, not closed news. topic_checker: not a duplicate
(check_title_duplicate returned False).

Real, name-matched visuals per standing requirement (no generic footage
standing in for named players): tries a real Wikimedia Commons photo of
Djokovic for the hook via psc.try_athlete_photo_hook(), same
EXIF-corrected pipeline used for Shelton/Virtanen. Tennis stock footage
was previously exhausted on Pixabay all session -- now backed by a
working Pexels fallback (found and fixed 2026-08-30: the API key env var
name mismatch) plus a Gemini vision gate on every candidate clip's real
thumbnail before download (also added 2026-08-30), so a fresh footage
attempt is safe to trust here in a way it wasn't earlier this session.

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
    "hook": "Novak Djokovic and Aryna Sabalenka just got eliminated -- in the FIRST round, as the top seeds.",
    "body": (
        "At the 2026 US Open mixed doubles, top-seeded Djokovic and "
        "Sabalenka fell 1-4, 4-2, 10-2 to Katerina Siniakova and Henry "
        "Patten -- the actual world number 1 doubles specialists. "
        "Siniakova closed it out with an ace, served directly at "
        "Djokovic."
    ),
    "cta": "Would you bet against Djokovic? Comment and subscribe!",
    "title": "Djokovic & Sabalenka Got ELIMINATED by Doubles Specialists #shorts",
    "tags": ["djokovic", "sabalenka", "usopen", "tennis", "shorts", "viral", "upset", "sportsfacts"],
    "seo_description": "Top seeds Novak Djokovic and Aryna Sabalenka were eliminated in the first round of 2026 US Open mixed doubles by specialist doubles players. #tennis #usopen #djokovic #sportsfacts",
    "queries": ["tennis match", "tennis doubles", "tennis crowd"],
}


def build():
    photo = psc.try_athlete_photo_hook("Novak Djokovic tennis")
    print("Photo:", photo)

    log("Downloading remaining stock footage...")
    clip_paths_all = psc.download_clips(SCRIPT)
    if photo:
        clip_paths = [photo["video_path"]] + clip_paths_all[:2]
    else:
        clip_paths = clip_paths_all

    log("Generating voiceover (cloned voice + persona sign-off)...")
    vo_path = psc.generate_voiceover(SCRIPT)

    from moviepy import AudioFileClip
    vo_dur = min(AudioFileClip(vo_path).duration + 1.5, 90.0)
    log("Generating background music...")
    music_path = psc.get_music(duration=vo_dur, script=SCRIPT)

    log("Running compliance check...")
    check = cc.validate_before_upload(SCRIPT, clip_paths, music_path)
    cc.save_compliance_report(check, video_id="djokovic_sabalenka_short")
    if not check["passed"]:
        raise RuntimeError(f"COMPLIANCE FAILED: {check['issues']}")
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "djokovic_sabalenka_short.mp4")
    log(f"Assembling video -> {out_path}")
    psc.assemble(clip_paths, SCRIPT, vo_path, music_path, out_path)

    log(f"BUILD COMPLETE (not uploaded yet) -> {out_path}")
    return out_path, vo_path


if __name__ == "__main__":
    build()
