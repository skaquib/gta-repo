"""Resume the Garrincha build from the voiceover and music already on disk.

Only the visuals and the render are redone. The voiceover and music from the
first run are reused verbatim -- regenerating them costs ~10 minutes and they
were verified fine (rms 0.045-0.056 in 5s windows, matching the source VO).

History of why this file keeps changing:
  1. build() passed source_pool()'s {theme: [paths]} dict straight into
     render() -- every beat failed with "'<theme>' not found".
  2. 115 beats exhausted RAM at concatenation -> _concat_batched().
  3. The render completed but was unwatchable: the theme table had no
     "soccer", so 81/115 beats fell to generic "mood" clips, and filler was
     dealt into topical themes -- a US tax form over his debut hat-trick.
     Now sourced per SUBJECT via visual_buckets, and render() only swaps in
     a longer clip from the same subject.
"""
import os
import config
config.assert_safe_pipeline()

import longform_creator as lf
from doc_garrincha import SCRIPT
from logger import log

VO = os.path.join(config.AUDIO_DIR, "lf_voice_1789313495.mp3")
MUSIC = os.path.join(config.AUDIO_DIR, "original_beat_emotional_72bpm_370s.mp3")
OUT = os.path.join(config.VIDEOS_DIR, "doc_garrincha.mp4")

if __name__ == "__main__":
    assert os.path.exists(VO), VO
    missing = lf.unmatched_beats(SCRIPT)
    if missing:
        raise RuntimeError(f"beats with no visual bucket (would render off-topic): {missing}")

    # Reuse the 38 vision-gated clips already downloaded (recovered from the
    # 2026-09-14 01:37-01:51 sourcing run). Re-sourcing marks them used and
    # downloads 38 MORE, which is slow and burns fresh stock for nothing.
    import json
    pool_file = os.path.join(config.OUTPUT_DIR, "garrincha_bucket_pool.json")
    pool = None
    if os.path.exists(pool_file):
        pool = json.load(open(pool_file))
        if not all(os.path.exists(pp) for v in pool.values() for pp in v):
            log("  saved pool has missing files -- re-sourcing")
            pool = None
    if pool is None:
        log("Sourcing per-SUBJECT footage via visual_buckets...")
        pool = lf.source_buckets(SCRIPT)
        json.dump(pool, open(pool_file, "w"), indent=1)
    else:
        log(f"Reusing saved bucket pool: {sum(len(v) for v in pool.values())} clips")
    beat_clips = lf.assign_visuals(SCRIPT, pool)
    alternates = lf.beat_alternates(SCRIPT, pool)
    log(f"{len(beat_clips)} beats from {len(set(beat_clips))} distinct clips")

    music = MUSIC if os.path.exists(MUSIC) else None
    lf.render(SCRIPT, beat_clips, VO, music, OUT, alternates=alternates)
    log(f"DONE -> {OUT}")
    print("VO_PATH=" + VO)
