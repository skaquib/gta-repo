"""
run_invisible_trophy_short.py — built 2026-09-18.

TOPIC FROM THE TRENDING CHART, not a guess: YouTube's mostPopular chart for
Sports / India (output/trending_sports_IN_2026-09-18.json) had ABP Ananda,
News18 Odia, BBC News Hindi, TV9 Telugu and Republic Bharat all covering
India refusing the Asia Cup trophy from Mohsin Naqvi. Evergreen trivia is
failing (cricket-over Short: 42 views; boxing: 197), so this Short rides the
live story -- and sends viewers to today's full documentary on it
(Jf0CLeDQNfA): Short = discovery, long-form = watch time.

FACTS: identical to doc_asiacup.py's verified list (Wikipedia 2025 Asia Cup;
Forbes, Gulf News, NBC, All India Radio for the 2025 ceremony; The National
and Dawn for the 2026 women's final). Only facts stated there are used here.
"""
import os
import config

config.assert_safe_pipeline()

import pro_shorts_creator as psc
import copyright_compliance as cc
from logger import log

SCRIPT = {
    "hook": "India won the Asia Cup final, and celebrated with a trophy that was not there.",
    "hook_card": "THE INVISIBLE TROPHY",
    "body": (
        "September 2025, Dubai. India beat Pakistan in the final. But the man "
        "presenting the cup, Mohsin Naqvi, was the Asian Cricket Council "
        "president, Pakistan's cricket board chairman, and Pakistan's Interior "
        "Minister. India refused to take it from him. After more than an hour, "
        "officials carried the trophy away, and Suryakumar Yadav lifted an "
        "invisible one. This month, India's women won the Asia Cup, and did "
        "exactly the same thing."
    ),
    "cta": "Was India right? The full story is on the channel. Comment and subscribe!",
    "title": "India Won the Asia Cup and Lifted an INVISIBLE Trophy 🏆😳 #shorts #cricket",
    "tags": ["asia cup", "invisible trophy", "suryakumar yadav", "mohsin naqvi",
             "india vs pakistan", "cricket", "shorts", "cricketnews", "indiancricket"],
    "seo_description": (
        "India beat Pakistan in the 2025 Asia Cup final but refused to take the trophy "
        "from ACC president Mohsin Naqvi, so Suryakumar Yadav lifted an invisible one. "
        "In September 2026, India's women won the Asia Cup and did the same. Full story "
        "on the channel. #cricket #asiacup"
    ),
    # Every query names cricket: sport-less terms pulled football and
    # American-football footage into the Asia Cup documentary this morning.
    "queries": ["cricket team celebration", "cricket stadium night", "gold trophy close up"],
}


def build():
    import topic_checker as tc
    check = tc.check_final_script_footage(SCRIPT)
    weak = [q for q, n in check.items() if n == 0]
    if weak:
        log(f"WARNING: real pipeline queries with 0 usable footage: {weak} -- proceeding, download_clips() will broaden/retry")

    log("Downloading real stock footage (vision-gated)...")
    clip_paths = psc.download_clips(SCRIPT)

    log("Generating voiceover (cloned voice)...")
    vo_path = psc.generate_voiceover(SCRIPT)

    from moviepy import AudioFileClip
    vo_dur = min(AudioFileClip(vo_path).duration + 1.5, 90.0)
    log("Generating background music...")
    music_path = psc.get_music(duration=vo_dur, script=SCRIPT)

    log("Running compliance check...")
    check = cc.validate_before_upload(SCRIPT, clip_paths, music_path)
    cc.save_compliance_report(check, video_id="invisible_trophy_short")
    if not check["passed"]:
        raise RuntimeError(f"COMPLIANCE FAILED: {check['issues']}")
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "invisible_trophy_short.mp4")
    log(f"Assembling video -> {out_path}")
    psc.assemble(clip_paths, SCRIPT, vo_path, music_path, out_path)

    log(f"BUILD COMPLETE (not uploaded yet) -> {out_path}")
    print("VO_PATH=" + vo_path)
    print("CLIPS=" + "|".join(clip_paths))
    return out_path, vo_path


if __name__ == "__main__":
    build()
