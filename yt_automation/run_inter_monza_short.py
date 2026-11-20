"""
run_inter_monza_short.py — Built 2026-08-22, video 7 of an 8-video
private batch. Uploaded PRIVATE only, not published.

Correction caught before writing: research initially said Inter's title
defense "starts tomorrow" -- rechecked and it was actually today, kicked
off 18:30 CEST, so waited for the real result instead of using
future-tense framing that would have gone stale (the exact Coventry
mistake, avoided this time by re-verifying before writing).

Verified via ESPN, Yahoo Sports (2026-08-22): Inter Milan beat newly
promoted Monza 4-1 at San Siro to open their Serie A title defense --
Hakan Calhanoglu, Piotr Zielinski, Francesco Pio Esposito, and Yann
Bisseck scored for Inter. topic_checker.py: not a duplicate.

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
    "hook": "Inter Milan just started their title defense with a 4-1 win.",
    "body": (
        "Hakan Calhanoglu opened the scoring early against newly "
        "promoted Monza, and second-half goals from Piotr Zielinski, "
        "Francesco Pio Esposito, and Yann Bisseck secured a comfortable "
        "afternoon for the defending Serie A champions."
    ),
    "cta": "Can Inter go back-to-back this season? Comment your prediction and subscribe!",
    "title": "Inter Milan Just Started Their Title Defense With a 4-1 Win #shorts",
    "tags": ["intermilan", "seriea", "calhanoglu", "football", "soccer", "shorts", "viral"],
    "seo_description": "Inter Milan beat newly promoted Monza 4-1 to open their Serie A title defense. #intermilan #seriea #football",
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
    cc.save_compliance_report(check, video_id="inter_monza_short")
    if not check["passed"]:
        raise RuntimeError(f"COMPLIANCE FAILED: {check['issues']}")
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "inter_monza_short.mp4")
    log(f"Assembling video -> {out_path}")
    psc.assemble(clip_paths, SCRIPT, vo_path, music_path, out_path)

    log(f"BUILD COMPLETE (not uploaded yet) -> {out_path}")
    return out_path, vo_path


if __name__ == "__main__":
    build()
