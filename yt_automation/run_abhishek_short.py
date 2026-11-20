"""
run_abhishek_short.py — built 2026-09-19.

TOPIC: YouTube's Trending chart (Sports, India, 2026-09-19) was dominated by
Abhishek Sharma's 30-ball hundred -- GBB Cricket, News18 Odia, Filmy Poster,
The Lallantop, Amar Ujala, RJ Raunac and Raf Talks all covering it. Owner
asked for content "not only Indian base", so the angle is the INTERNATIONAL
record: fastest T20I hundred ever by a batter from a Test-playing nation,
beating Zimbabwe's Sikandar Raza and New Zealand's Finn Allen. A multi-
country trending check the same day found no football story with a clean,
verifiable hook (Barcelona 7-2 sources disagreed on the scorers).

VERIFIED (Sky Sports; ESPNcricinfo "fastest T20I hundred by a Full Member
batter"; Eastern Herald; NewsBook headline):
- 3rd T20I v Afghanistan, Arun Jaitley Stadium (Delhi); India batted first.
- Hundred off 30 balls; out for 108 off 34; 11 sixes and 9 fours.
- Beat Rohit Sharma's India record (35 balls, v Sri Lanka, Indore, 2017).
- Previous Full Member record: 33 balls, Sikandar Raza and Finn Allen.
- India swept the series 3-0.
NOT CLAIMED: not the overall T20I record (an Associate batter holds that);
winning margin (single source) left out.

VISUALS: no freely licensed photo of Abhishek Sharma the cricketer exists
on Wikimedia (the name match returned a different man in a suit), so his
beats use designed stat cards; Rohit Sharma's real CC BY 3.0 photo covers
his line.
"""
import os

import config

config.assert_safe_pipeline()

import pro_shorts_creator as psc
from logger import log

SCRIPT = {
    "hook": "No batter from a Test playing nation had ever scored a T20 international hundred this fast.",
    "hook_card": "100 IN 30 BALLS",
    "body": (
        "Delhi, the third T20 against Afghanistan. India's opener Abhishek "
        "Sharma reached a hundred in just thirty balls. Rohit Sharma's Indian "
        "record, thirty five balls, had stood since twenty seventeen. The "
        "record for any Test nation belonged to Zimbabwe's Sikandar Raza and "
        "New Zealand's Finn Allen, at thirty three. Abhishek beat them both. "
        "He finished with one hundred and eight off thirty four, with eleven "
        "sixes, and India swept the series three nil."
    ),
    "cta": "Is he the most dangerous opener in the world right now? Comment and subscribe!",
    "title": "100 in 30 Balls! Abhishek Sharma Just Beat Every Test Nation's Record 🤯🏏 #shorts #cricket",
    "tags": ["abhishek sharma", "fastest t20i century", "30 ball hundred", "india vs afghanistan",
             "rohit sharma", "finn allen", "sikandar raza", "cricket", "shorts", "cricket records"],
    "seo_description": (
        "Abhishek Sharma hit a 30-ball hundred against Afghanistan in Delhi -- the fastest "
        "T20I century ever by a batter from a Test-playing nation, beating Sikandar Raza "
        "and Finn Allen (33 balls) and Rohit Sharma's India record (35). 108 off 34 with "
        "11 sixes as India swept the series 3-0. #cricket #abhisheksharma"
    ),
    "queries": ["cricket batsman hitting six", "cricket stadium night", "cricket fans cheering"],
}


def build_audio():
    """Voice + music only. Visuals are assembled separately from vetted
    clips, designed stat cards and licensed photos."""
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
