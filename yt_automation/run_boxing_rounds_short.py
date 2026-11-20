"""
run_boxing_rounds_short.py — rewritten 2026-09-15.

FORMAT, from channel data: the "Why Is X EXACTLY Y?" series is the best
performer here. Marathon 26.2 miles = 1,687 (channel record), bowling lane
60ft = 1,124 at 95.2% retention (best ever measured), football match 90
minutes = 1,065 in its first two days. Ref/news Shorts pull views but bleed
retention (3 yellow cards: 841 at 43%). The separating variable is a number
that is famous enough to have been half-wondered about and odd enough to
demand an answer, about something the viewer has encountered. Round/obscure
numbers die (Olympic pool 50m = 11, cricket pitch 22 yards = 144).

WHY THIS NUMBER, AND WHAT WAS REJECTED (2026-09-15):
  - Penalty spot 12 yards -> sources document WHEN (1891 line, 1902 spot)
    but not WHY 12. No payoff = a claim, not an answer. That is exactly the
    shape of "78% Is Wrong", which got 8 views.
  - NFL Week 1 scoring records -> real live demand, but this audience is
    ~50-64% India and the channel's NFL attempts have never travelled.
  - Lamine Yamal Ballon d'Or talk -> agent quotes and speculation, which
    fails the verified-facts standard.
The earlier draft of THIS file claimed 3 minutes was chosen as "long enough
for real action, short enough that fighters could actually survive it". No
source says that -- it was invented rationale, so it is gone. The honest and
more shocking payoff is what the rule REPLACED.

VERIFIED (2026-09-15 -- Wikipedia (London Prize Ring Rules; Bare-knuckle
boxing); Britannica (London Prize Ring rules; Marquess of Queensberry
rules); WBA):
- Under the London Prize Ring rules a round ended when a man was put down
  by a punch or a throw -- not on a clock. He then had 30 seconds of rest
  plus 8 seconds to "come to scratch" (return to a line scratched in the
  centre of the ring). Failing to come to scratch lost the fight.
- Consequently there were no round limits at all.
- Longest recorded bare-knuckle fight: 6 hours 15 minutes, James Kelly v
  Jonathan Smith, near Fiery Creek, Australia, 3 December 1855.
- The 1867 Marquess of Queensberry Rules, written by John Graham Chambers
  of the Amateur Athletic Club, set rounds at 3 minutes with 1 minute of
  rest, and required gloves.

NOT CLAIMED: no reason is given for why Chambers picked three minutes --
no source explains it, so the script does not pretend one exists. Sources
disagree on the round COUNT of the Kelly-Smith fight (17 vs 276), so only
the duration, which they agree on, is used.
"""
import os
import config

config.assert_safe_pipeline()

import pro_shorts_creator as psc
import copyright_compliance as cc
from logger import log

SCRIPT = {
    "hook": "A boxing round is exactly three minutes -- and before 1867, a round had no time limit at all.",
    "body": (
        "Under the old rules, a round ended only when a man hit the ground. "
        "Then he got thirty seconds to recover, and eight more to walk back "
        "to a line scratched in the dirt. If he could not reach it, he lost. "
        "So a fight lasted as long as two men could stand up. The longest on "
        "record ran six hours and fifteen minutes. Then in eighteen sixty "
        "seven, a man named John Graham Chambers wrote a new rulebook, and "
        "put a clock on it. Three minutes, one minute rest. Nobody has "
        "changed it since."
    ),
    "cta": "Could you last one three-minute round? Comment and subscribe!",
    "title": "Why Is a Boxing Round EXACTLY 3 Minutes? #shorts",
    "tags": ["boxing", "boxinghistory", "boxingrules", "shorts", "viral",
             "sportsfacts", "queensberry"],
    "seo_description": (
        "A boxing round is exactly 3 minutes because of the 1867 Queensberry Rules. "
        "Before that a round ended only when a man was knocked down -- and the longest "
        "bare-knuckle fight on record lasted 6 hours 15 minutes. #boxing #sportsfacts"
    ),
    "queries": ["boxing gloves training", "boxing gym punching bag", "boxing ring"],
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
    cc.save_compliance_report(check, video_id="boxing_rounds_short")
    if not check["passed"]:
        raise RuntimeError(f"COMPLIANCE FAILED: {check['issues']}")
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "boxing_rounds_short.mp4")
    log(f"Assembling video -> {out_path}")
    psc.assemble(clip_paths, SCRIPT, vo_path, music_path, out_path)

    log(f"BUILD COMPLETE (not uploaded yet) -> {out_path}")
    return out_path, vo_path


if __name__ == "__main__":
    build()
