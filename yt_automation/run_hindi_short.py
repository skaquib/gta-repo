"""
run_hindi_short.py
===================
Produces one real Hindi-language Short for the Indian audience segment
(confirmed via YouTube Studio Geography analytics to be the channel's largest
viewer base): a real, current sports story -> Hindi script translation ->
Hindi voiceover (Edge-TTS hi-IN-MadhurNeural, a fast ready-made voice) ->
Hindi word-level captions (faster-whisper auto-detects Hindi) -> real,
tag-matched stock footage via download_clips() (visual queries stay in
English on purpose, since they're never narrated or shown as text) ->
upload with Hindi title/description and defaultAudioLanguage=hi.

Today: ready-made Edge-TTS Hindi voice.
Tomorrow (once a Hindi reference recording is provided): swap
generate_hindi_voiceover() for the cloned-voice path -- see the note in
pro_shorts_creator.py's generate_hindi_voiceover().
"""

import os
import config
config.assert_safe_pipeline()

import pro_shorts_creator as psc
import copyright_compliance as cc
from logger import log


def main():
    log("=" * 60)
    log("  HINDI SHORT -- one-shot run")
    log("=" * 60)

    state = psc.load_state()
    state["count"] = state.get("count", 0) + 1
    script_en = psc.generate_script(state)
    psc.save_state(state)
    log(f"English script: {script_en['hook'][:70]}")

    script_hi = psc.translate_script_to_hindi(script_en)
    if script_hi.get("lang") != "hi":
        raise RuntimeError("Hindi translation did not succeed -- aborting rather than "
                            "uploading an English video under a Hindi-intent run.")
    log(f"Hindi script: {script_hi['hook'][:70]}")

    clip_paths = psc.download_clips(script_hi)

    vo_path = psc.generate_hindi_voiceover(script_hi)

    vo_dur = 21.0
    try:
        from moviepy import AudioFileClip
    except ImportError:
        from moviepy.editor import AudioFileClip
    try:
        vc = AudioFileClip(vo_path)
        vo_dur = min(vc.duration + 1.5, 26.0)
        vc.close()
    except Exception:
        pass
    music_path = psc.get_music(duration=vo_dur, script=SCRIPT)

    check = cc.validate_before_upload(script_hi, clip_paths, music_path)
    cc.save_compliance_report(check, f"hindi_{int(vo_dur)}")
    if not check["passed"]:
        raise RuntimeError(f"Compliance check failed: {check['issues']}")

    import time
    out_path = os.path.join(config.VIDEOS_DIR, f"hindi_{int(time.time())}.mp4")
    psc.assemble(clip_paths, script_hi, vo_path, music_path, out_path)

    url = psc.upload(out_path, script_hi, vo_path)
    log(f"HINDI VIDEO COMPLETE! YouTube: {url or '(saved, not uploaded)'}")
    return url


if __name__ == "__main__":
    main()
