"""
run_barca_record_short.py — Trending topic (2026-10-20). Barcelona beat Real
Betis 5-2 on Oct 17 to go 9 wins from 9 in La Liga (39 goals), equalling the
best start in the league's history -- Real Madrid's 1968-69 run, 58 years
ago. Their next league game is El Clasico against Real Madrid on Oct 25, so
they can break Madrid's record against Madrid. Verified via grounded search
(fcbarcelona.com "FC Barcelona equal record for best league start",
laliga.com, beinsports.com, koreaherald.com, livescore.com).

Built in a cloud session where Pexels/Pixabay/ElevenLabs/Edge-TTS were all
network-blocked, so this script only depends on the Gemini API (via
gemini_studio):
  - visuals: Gemini image generation -> Ken Burns clips in output/ai_images/
    (no real faces, crests or logos -- generic atmosphere only)
  - voice:   Gemini TTS, falling back to psc.generate_voiceover()
  - timing:  local energy-based alignment of the known script text
             (faster-whisper's model host is blocked)
Music is synthesized locally by music_generator as usual.

Does NOT upload -- renders to output/videos/ for review first.
"""
import os
import config

config.assert_safe_pipeline()

import gemini_studio as gs
import pro_shorts_creator as psc
import copyright_compliance as cc
from logger import log

VIDEO_ID = "barca_record_short"

SCRIPT = {
    "hook": "Nine games. Nine wins. A record nobody has beaten in 58 years.",
    "body": (
        "Barcelona just won 5-2 at Real Betis, with Lamine Yamal curling one "
        "into the top corner. That's nine La Liga wins out of nine and 39 "
        "goals, equalling the best start in league history, set by Real "
        "Madrid back in 1968. And the twist? Their next league game is El "
        "Clasico, against Real Madrid themselves."
    ),
    "cta": "Will Barca break Madrid's record against Madrid? Comment your score prediction and subscribe!",
    "title": "Barca Can Break Madrid's 58-Year Record... vs MADRID #shorts",
    "tags": ["barcelona", "fcbarcelona", "laliga", "elclasico", "realmadrid", "lamineyamal",
             "football", "soccer", "record", "shorts", "viral"],
    "seo_description": (
        "Barcelona have won all 9 La Liga games this season, equalling Real Madrid's "
        "1968-69 record for the best start in league history. Next up: El Clasico "
        "vs Real Madrid on October 25. #barcelona #laliga #elclasico"
    ),
    "ai_generated_visuals": True,  # Gemini image scenes -> YouTube altered-content label
}

# Narration order -- assemble() rotates through clips in this order, so each
# shot lands roughly on the line it illustrates. gemini_studio.SAFE_STYLE
# is appended to each (no real people, crests, logos or text).
SCENES = [
    "A packed football stadium at night, fans waving deep blue and garnet flags and flares, "
    "floodlights cutting through smoke, shot from high in the stands.",
    "Close-up of a football curling into the top corner of the net, net rippling, motion blur, "
    "stadium lights glowing behind.",
    "Nine bright floodlight towers glowing in a row above a dark football stadium at dusk, "
    "epic wide shot.",
    "A grainy black-and-white 1960s football stadium, vintage crowd in coats and hats, "
    "old-fashioned leather ball on muddy pitch, film grain.",
    "A football stadium split down the middle: one half of the crowd in white and gold, the other "
    "half in blue and garnet, a single ball on the centre spot, tense atmosphere before kickoff.",
    "A lone football on the centre spot under a single spotlight in a dark empty stadium, "
    "dramatic, moody.",
]


def build():
    log("Generating AI scenes (Gemini image -> Ken Burns clips)...")
    clip_paths = gs.generate_image_clips(SCENES, VIDEO_ID)

    log("Generating voiceover...")
    vo_path = gs.gemini_voiceover(SCRIPT, VIDEO_ID)

    from moviepy import AudioFileClip
    gs.cache_word_timestamps(vo_path, SCRIPT)
    vo_dur = min(AudioFileClip(vo_path).duration + 1.5, 90.0)

    log("Generating background music...")
    music_path = psc.get_music(duration=vo_dur, script=SCRIPT)

    log("Running compliance check...")
    check = cc.validate_before_upload(SCRIPT, clip_paths, music_path)
    cc.save_compliance_report(check, video_id=VIDEO_ID)
    if not check["passed"]:
        raise RuntimeError(f"COMPLIANCE FAILED: {check['issues']}")

    out_path = os.path.join(config.VIDEOS_DIR, f"{VIDEO_ID}.mp4")
    log(f"Assembling video -> {out_path}")
    psc.assemble(clip_paths, SCRIPT, vo_path, music_path, out_path)

    log(f"BUILD COMPLETE (not uploaded yet) -> {out_path}")
    return out_path, vo_path


if __name__ == "__main__":
    build()
