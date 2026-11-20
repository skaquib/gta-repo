"""
run_cricket_over_short.py — built 2026-09-17.

FORMAT: "Why Is X EXACTLY Y?" -- the channel's best series (marathon 1,687,
bowling 1,124 at 95.2% retention, 90 minutes 1,065). The boxing entry
(2026-09-16) did only 105 in its first 7 hours: the number has to belong to
a sport THIS audience (~50-64% India) actually plays and watches. So today
stays on cricket/football.

TIMING: India v Afghanistan, 3rd T20I, Arun Jaitley Stadium, Delhi, is on
2026-09-17 -- cricket has live demand in the core audience today.

REJECTED:
  - "Why 11 players a side?" -> sources only offer theories (cricket
    influence, pitch size); the reason is undocumented, so there is no
    payoff to deliver.

VERIFIED (2026-09-17 -- Wikipedia "Over (cricket)"; cross-checked against
sportsdigest.in, Sunday Guardian, cricketnmore):
- Early overs were 4 balls (England 1880-1888; Australia 1876/77-1887/88).
- England used 5-ball overs 1889-1899 and 6-ball overs from 1900.
- 8-ball overs were used by Australia (1924/25, and 1936/37-1978/79),
  New Zealand (1968/69-1978/79) and Pakistan (1974/75-1977/78), among others.
- Before the 1980 Laws of Cricket the number was not universally fixed; it
  could be "agreed by the two captains prior to the toss".
- "Since 1979/80, all Test cricket has been played with six balls per over."

NOT CLAIMED: sources disagree on when Australia first used 8-ball overs
(1922/23 vs 1924/25), so no start year is given. No reason for 8-ball overs
is stated -- Wikipedia gives none, and the secondary explanations are
unsourced.
"""
import os
import config

config.assert_safe_pipeline()

import pro_shorts_creator as psc
import copyright_compliance as cc
from logger import log

SCRIPT = {
    "hook": "A cricket over is exactly six balls -- but until 1979, that number was not fixed at all.",
    "hook_card": "WHY 6 BALLS?",
    "body": (
        "The first overs were just four balls. England moved to five in "
        "eighteen eighty nine, then six in nineteen hundred. But Australia, "
        "New Zealand and Pakistan were still bowling eight-ball overs in the "
        "late nineteen seventies. And before 1980, the laws did not even "
        "settle it: the number of balls could be agreed by the two captains "
        "before the toss. Only since the nineteen seventy-nine eighty season "
        "has every Test match "
        "used six. So the most basic unit of cricket has been universal for "
        "less than fifty years."
    ),
    "cta": "Would you bring back eight-ball overs? Comment and subscribe!",
    # Emojis: 2026-09-17 trend scan -- every top-20 cricket Short in IN used
    # them in the title; this channel's titles had none.
    "title": "Why Is a Cricket Over EXACTLY 6 Balls? 🏏😳 #shorts #cricket",
    "tags": ["cricket", "cricketfacts", "cricketnews", "indiancricket",
             "shorts", "viral", "sportsfacts", "testcricket"],
    "seo_description": (
        "A cricket over is 6 balls -- but overs were once 4, 5 and even 8 balls, and "
        "before 1980 the two captains could agree the number before the toss. Six "
        "balls has only been universal in Test cricket since 1979-80. #cricket #sportsfacts"
    ),
    "queries": ["cricket bowler bowling", "cricket match stadium", "cricket ball close up"],
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
    cc.save_compliance_report(check, video_id="cricket_over_short")
    if not check["passed"]:
        raise RuntimeError(f"COMPLIANCE FAILED: {check['issues']}")
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "cricket_over_short.mp4")
    log(f"Assembling video -> {out_path}")
    psc.assemble(clip_paths, SCRIPT, vo_path, music_path, out_path)

    log(f"BUILD COMPLETE (not uploaded yet) -> {out_path}")
    print("VO_PATH=" + vo_path)
    return out_path, vo_path


if __name__ == "__main__":
    build()
