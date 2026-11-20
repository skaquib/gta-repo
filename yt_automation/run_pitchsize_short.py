"""
run_pitchsize_short.py — built 2026-09-25, for SCHEDULED publish.

WHY THIS TOPIC: same proven "Why is X...?" format as the channel's four best
videos, applied to the sport with the largest global audience. The surprise
is real -- most viewers assume every professional pitch is identical, the way
a basketball court or a tennis court is.

VERIFIED (IFAB Laws of the Game Law 1 via The FA; Wikipedia "Football pitch";
FIFA recommendation as reported by CCGrass and FootyPedia):
- The Laws allow 90-120 m long and 45-90 m wide for ordinary matches.
- FIFA recommends 105 m by 68 m, which most modern professional pitches use.
- Football's rules were codified in 19th-century England on whatever ground
  was available, and when the Football Association formed in 1863 the
  lawmakers formalised that existing variety instead of imposing one size.
- Many old stadiums are hemmed in by roads, housing and railway lines, so
  their pitches cannot be widened.
NOT CLAIMED: no claim that any specific club deliberately sizes its pitch for
tactical advantage -- that is argued, not documented.
"""
import os

import config

config.assert_safe_pipeline()

import pro_shorts_creator as psc
from logger import log

SCRIPT = {
    "hook": "Every basketball court is the same size. Every tennis court is the same size. Football pitches are not.",
    "hook_card": "NO TWO PITCHES MATCH",
    "body": (
        "The laws of the game allow a pitch to be anywhere from ninety to one "
        "hundred and twenty metres long, and forty five to ninety metres wide. "
        "That is a huge range. FIFA recommends one hundred and five by sixty "
        "eight, and most modern grounds use it, but they do not have to. The "
        "reason goes back to the eighteen hundreds. Football was codified in "
        "England on whatever land was free, bounded by a wall, a path, or a "
        "river. When the Football Association was formed in eighteen sixty "
        "three, instead of forcing every club to rebuild, the lawmakers simply "
        "wrote the variety into the rules. And old stadiums, boxed in by "
        "streets and railway lines, still cannot widen their pitch today."
    ),
    "cta": "Should every pitch be identical? Comment and subscribe!",
    "title": "Football Pitches Are NOT All the Same Size ⚽😳 #shorts #football",
    "tags": ["football", "soccer", "football pitch", "pitch size", "laws of the game",
             "sports facts", "shorts", "premier league", "fifa"],
    "seo_description": (
        "Basketball courts and tennis courts are fixed. Football pitches are not: the "
        "Laws of the Game allow 90-120m by 45-90m. FIFA recommends 105x68m, but clubs "
        "do not have to use it -- a rule written in 1863 around whatever land was "
        "available. #football #sportsfacts"
    ),
    "queries": ["soccer stadium aerial", "soccer pitch grass", "soccer match action"],
}


def build_audio():
    log("Generating voiceover (cloned voice)...")
    vo_path = psc.generate_voiceover(SCRIPT)
    from moviepy import AudioFileClip
    vo_dur = min(AudioFileClip(vo_path).duration + 1.5, 90.0)
    log("Generating background music...")
    music_path = psc.get_music(duration=vo_dur, script=SCRIPT)
    print("VO_PATH=" + vo_path, flush=True)
    print("MUSIC_PATH=" + (music_path or ""), flush=True)
    return vo_path, music_path


if __name__ == "__main__":
    build_audio()
