"""
run_werro_800m_short.py — Today's video (2026-08-15): Audrey Werro fell in
her 800m semifinal at the European Athletics Championships but was
reinstated to the final by the track referee. She then held off Olympic
champion Keely Hodgkinson and a full home crowd to win gold in 1:54.81 --
a new championship record, breaking a mark that had stood for 44 years.
Her first senior title, at 22. Real, fresh (yesterday, Aug 14), verified.

Trending-topic pick: the top of YouTube's Sports chart right now is
dominated by raw viral clips of specific real athletes (a Haaland/Mbappe
livestream prank at 32M views) that this pipeline cannot legally recreate
without their real likeness. Track/athletics stock footage genuinely
depicts running/racing/finish-line action, so this keeps the "visuals
actually match the script" bar the marathon video hit, while still being
a real, current, verified story rather than a generic explainer.
"""
import os
import config

config.assert_safe_pipeline()

import pro_shorts_creator as psc
import copyright_compliance as cc
from logger import log

SCRIPT = {
    "hook": "She fell in the semifinal. The next day, she broke a 44-year record.",
    "body": (
        "Audrey Werro was reinstated to the 800m final after falling in "
        "her semifinal. She then held off Olympic champion Keely "
        "Hodgkinson and a full home crowd to win gold in 1:54.81 -- a new "
        "European Championship record that had stood for 44 years. It's "
        "her first senior title, at 22 years old."
    ),
    "cta": "Is Werro the new queen of the 800m? Comment your take and subscribe!",
    "title": "She Fell in the Semifinal. Then Broke a 44-Year Record #shorts",
    "tags": ["audreywerro", "keelyhodgkinson", "europeanchampionships", "800m", "athletics", "trackandfield", "shorts", "viral"],
    "seo_description": "Audrey Werro fell in her semifinal, then beat Olympic champion Keely Hodgkinson to break a 44-year-old European 800m record. #athletics #trackandfield",
    "queries": ["800m runner race", "athletics track stadium", "runners finish line sprint"],
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
    cc.save_compliance_report(check, video_id="werro_800m_short")
    if not check["passed"]:
        raise RuntimeError(f"COMPLIANCE FAILED: {check['issues']}")
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "werro_800m_short.mp4")
    log(f"Assembling video -> {out_path}")
    psc.assemble(clip_paths, SCRIPT, vo_path, music_path, out_path)

    log(f"BUILD COMPLETE (not uploaded yet) -> {out_path}")
    return out_path, vo_path


if __name__ == "__main__":
    build()
