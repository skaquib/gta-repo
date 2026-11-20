"""
run_salah_short.py — built 2026-09-20.

GLOBAL topic, as the owner asked ("not only Indian base"). Multi-country
trending scan (GB/US/NG/ZA/AU/ES/BR/IN, output/trending_sports_global_2026-09-20.json)
showed football everywhere; Salah's hat-trick was covered across Nigeria,
South Africa, the UK and Spain. Chosen over Brighton 3-0 Arsenal because a
freely licensed photo of Salah exists (no legal face for that story) and the
arc is stronger.

VERIFIED (Sky Sports; Al Jazeera; RTE; The National; OneFootball; AllFootball;
Wikipedia "Mohamed Salah"):
- Left Liverpool in August 2026 on a free transfer after nine years, having
  mutually terminated his contract a year early; signed a two-year deal with
  Trabzonspor reported at EUR 17m a season. He was 34.
- At Liverpool: 257 goals in 442 appearances, two league titles and the
  Champions League among eight major honours.
- 19/20 September 2026: hat-trick plus an assist as Trabzonspor beat
  Galatasaray 4-0; two of the goals came from solo runs.
- First player in over ten Super Lig seasons to be involved in four goals
  against Galatasaray in a single league match.
- Six league games in: 7 goals and 2 assists, top of the Super Lig charts.
NOT CLAIMED: nothing about why he left, and no transfer-fee figure (it was a
free); the EUR 17m salary is reported, so the script says "reported".
"""
import os

import config

config.assert_safe_pipeline()

import pro_shorts_creator as psc
from logger import log

SCRIPT = {
    "hook": "In August, Mohamed Salah left Liverpool on a free transfer at thirty four, and plenty of people said he was finished.",
    "hook_card": "THEY SAID HE WAS FINISHED",
    "body": (
        "Nine years at Anfield. Two league titles, a Champions League, two "
        "hundred and fifty seven goals. Then a two year deal in Turkey, with "
        "Trabzonspor. On Saturday he faced Galatasaray. He scored a hat-trick, "
        "two of them from solo runs, and set up a fourth. Trabzonspor won four "
        "nil. No player in over ten Super Lig seasons had been involved in four "
        "goals against Galatasaray in a single match. Six games into his new "
        "league, Salah has seven goals and two assists, top of the charts."
    ),
    "cta": "Finished, or the best free transfer of the year? Comment and subscribe!",
    "title": "They Said Salah Was Finished at 34. Then He Did THIS 🔥⚽ #shorts #football",
    "tags": ["mohamed salah", "salah trabzonspor", "salah hat trick", "galatasaray",
             "super lig", "liverpool", "football", "shorts", "free transfer"],
    "seo_description": (
        "Mohamed Salah left Liverpool on a free transfer at 34 after nine years, 257 goals, "
        "two league titles and a Champions League. Six games into the Turkish Super Lig he "
        "has 7 goals and 2 assists -- including a hat-trick and an assist in Trabzonspor's "
        "4-0 win over Galatasaray. #salah #football #trabzonspor"
    ),
    "queries": ["football stadium night", "soccer player shooting goal", "football fans crowd"],
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
