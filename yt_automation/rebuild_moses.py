"""
rebuild_moses.py — correct rebuild of documentary #2.

FIXES THREE FAULTS THE CHANNEL OWNER CAUGHT IN THE PUBLISHED CUT:
1. Visuals were random (a skyscraper in a footballer's story). Cause: an
   ad-hoc re-render built the pool as clips[i*3:(i+1)*3] -- mapping footage
   to themes BY LIST POSITION. That is the same bug already documented as
   "# WRONG" in rebuild_doc.py, reintroduced by taking a shortcut around
   source_pool(). This file calls source_pool() properly so each theme is
   filled with its own searched, vision-gated footage.
2. No captions on screen. longform_creator.render() drew no overlay at all;
   every caption/hook/subscribe element lived in the Shorts pipeline only.
   render_lf_overlay() now draws word-synced captions from MEASURED timings.
3. No subscribe ask. Now shown early and again near the end.

Reuses the existing narration so this costs render time only.
"""
import os
import config
import longform_creator as lf
from doc_moses import SCRIPT
from logger import log

VO = "output/audio/lf_voice_1789150361.mp3"
OUT = os.path.join(config.VIDEOS_DIR, "doc_moses_v2.mp4")


def main():
    assert os.path.exists(VO), VO

    log("Sourcing per-theme SOCCER footage via source_pool (no index slicing)...")
    pool = lf.source_pool(SCRIPT, per_theme=3)
    for theme, paths in sorted(pool.items()):
        log(f"  {theme}: {[os.path.basename(p) for p in paths]}")

    beat_clips = lf.assign_visuals(SCRIPT, pool)
    log(f"{len(beat_clips)} beats from {len(set(beat_clips))} distinct clips")

    music = None
    try:
        import pro_shorts_creator as psc
        music = psc.get_music(duration=380, script={"hook": SCRIPT.title,
                                                    "body": SCRIPT.description, "cta": ""})
    except Exception as e:
        log(f"music skipped ({e})")

    lf.render(SCRIPT, beat_clips, VO, music, OUT)
    log(f"DONE -> {OUT}")


if __name__ == "__main__":
    main()
