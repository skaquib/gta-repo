"""
run_derby_short.py — built 2026-09-21.

GLOBAL topic. Multi-country trending scan (GB/US/NG/ZA/AU/ES/BR/IN, saved to
output/trending_sports_global_2026-09-21.json): the Madrid derby was trending
in five countries at once (LaLiga's highlights 4.3M, CazeTV's full match 9.7M
in Brazil). Biggest genuinely global football story of the day.

VERIFIED (Al Jazeera "Atletico Madrid beat 10-man Real Madrid 2-1 in feisty
La Liga derby"; ESPN match report; VAVEL):
- 20 September 2026, Riyadh Air Metropolitano.
- Dean Huijsen was sent off early in the second half for pulling down
  Giuliano Simeone in the penalty area.
- Alejandro Grimaldo scored the resulting penalty.
- Jonathan David doubled the lead -- his third goal in three games.
- Antonio Rudiger pulled one back late; it finished 2-1.
- Atletico rose to second, five points behind Barcelona and one ahead of
  Real Madrid, whose second defeat of the season it was.
NOT CLAIMED: no opinion on whether the red card was correct (the CTA asks
the viewer instead), and no minute-by-minute timings beyond "early in the
second half" and "late", which is what the sources support.
"""
import os

import config

config.assert_safe_pipeline()

import pro_shorts_creator as psc
from logger import log

SCRIPT = {
    "hook": "Real Madrid went into the Madrid derby chasing the title. Then one tackle changed the whole game.",
    "hook_card": "ONE RED CARD DECIDED IT",
    "body": (
        "The Riyadh Air Metropolitano, Sunday night. Early in the second half, "
        "Dean Huijsen pulled down Giuliano Simeone inside the box. Referee's "
        "decision: red card, and a penalty. Alejandro Grimaldo scored it. Ten "
        "man Real Madrid never recovered. Jonathan David doubled it, his third "
        "goal in three games. Antonio Rudiger pulled one back late, but it "
        "finished two one. Atletico are now second, five points behind "
        "Barcelona, and one point ahead of Real Madrid, who have already lost "
        "twice this season."
    ),
    "cta": "Was that really a red card? Tell me below. Comment and subscribe!",
    "title": "One Red Card Decided the Madrid Derby 😳🔴 #shorts #football",
    "tags": ["madrid derby", "atletico madrid", "real madrid", "huijsen red card",
             "grimaldo", "jonathan david", "rudiger", "laliga", "football", "shorts"],
    "seo_description": (
        "Atletico Madrid beat 10-man Real Madrid 2-1 in the derby at the Riyadh Air "
        "Metropolitano. Dean Huijsen was sent off early in the second half for pulling "
        "down Giuliano Simeone, Grimaldo scored the penalty, Jonathan David made it two "
        "and Rudiger replied late. Atletico go second. #laliga #realmadrid #atleticomadrid"
    ),
    "queries": ["football referee red card", "soccer stadium night", "football fans crowd"],
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
