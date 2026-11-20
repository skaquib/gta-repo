"""
rebuild_doc.py — re-render the documentary with CORRECT theme->visual mapping.

WHY THIS EXISTS (bug found 2026-09-09):
A previous re-render assigned clips to themes by arbitrary list index:

    pool[t] = clips[i*3:(i+1)*3]      # WRONG

That maps whatever files happen to sit at that index to a theme, with no
relationship to what the footage actually shows. Result: a documentary about
NFL players going broke opened on a night-time city street with parked cars.
Visuals were effectively random against the narration for the whole video --
the same script/visual mismatch flagged repeatedly on the Shorts, and the
clearest "AI slop" signal there is.

The fix is to use longform_creator.source_pool(), which fetches per theme
using that theme's own search terms and runs every candidate through the
vision gate (rejects off-subject, staged, and cartoon footage).

Reuses the EXISTING voiceover so this costs render time only -- no repeat
TTS spend, and the narration is already verified.
"""
import os
import config
import longform_creator as lf
from doc_athletes_broke import SCRIPT
from logger import log

# Already-generated, already-verified narration (6.77 min).
VO_PATH = "output/audio/lf_voice_1788862343.mp3"
OUT_PATH = os.path.join(config.VIDEOS_DIR, "doc_athletes_broke_v3.mp4")


def main():
    if not os.path.exists(VO_PATH):
        raise FileNotFoundError(f"voiceover missing: {VO_PATH}")

    log("Sourcing themed pool with CORRECT per-theme queries + vision gate...")
    pool = lf.source_pool(SCRIPT, per_theme=3)

    for theme, paths in sorted(pool.items()):
        log(f"  {theme}: {len(paths)} clips -> {[os.path.basename(p) for p in paths]}")

    empty = [t for t, p in pool.items() if not p]
    if empty:
        log(f"WARNING: empty themes {empty} -- those beats fall back across themes")

    beat_clips = lf.assign_visuals(SCRIPT, pool)
    log(f"Assigned {len(beat_clips)} beats from {len(set(beat_clips))} distinct clips")

    music_path = None
    try:
        import pro_shorts_creator as psc
        music_path = psc.get_music(duration=420,
                                   script={"hook": SCRIPT.title,
                                           "body": SCRIPT.description, "cta": ""})
    except Exception as e:
        log(f"Music skipped ({e})")

    # Writes to a NEW filename -- the earlier mistake was re-rendering over
    # the only working copy, which left nothing pushable while a fix encoded.
    lf.render(SCRIPT, beat_clips, VO_PATH, music_path, OUT_PATH)
    log(f"DONE -> {OUT_PATH}")


if __name__ == "__main__":
    main()
