"""
Phase 3 — Voiceover Generation
Calls ElevenLabs API to generate .mp3 per scene per language.
Stitches all scene audio into one full voiceover file per language.
"""

import os
import requests
import config
from logger import log

ELEVENLABS_BASE = "https://api.elevenlabs.io/v1"

HEADERS = {
    "xi-api-key": config.ELEVENLABS_API_KEY,
    "Content-Type": "application/json",
}


def generate_scene_audio(text: str, scene_id: int, lang_code: str) -> str:
    """Generate audio for one scene. Returns path to .mp3 file."""
    os.makedirs(config.AUDIO_DIR, exist_ok=True)
    out_path = f"{config.AUDIO_DIR}/scene_{scene_id:03d}_{lang_code}.mp3"

    if os.path.exists(out_path):
        log(f"  Audio exists, skipping: {out_path}")
        return out_path

    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.4,
            "similarity_boost": 0.85,
            "style": 0.3,
            "use_speaker_boost": True,
        },
    }

    url = f"{ELEVENLABS_BASE}/text-to-speech/{config.ELEVENLABS_VOICE_ID}"
    response = requests.post(url, headers=HEADERS, json=payload, timeout=60)

    if response.status_code == 200:
        with open(out_path, "wb") as f:
            f.write(response.content)
        log(f"  Audio generated: scene {scene_id} [{lang_code}]")
        return out_path
    else:
        log(f"  ElevenLabs ERROR {response.status_code}: {response.text[:200]}")
        raise Exception(f"ElevenLabs failed for scene {scene_id}: {response.status_code}")


def generate_all_voiceovers(script: dict, topic_id: int) -> dict:
    """
    Generate audio for all scenes in all languages.
    Returns dict: { "en": ["path1.mp3", ...], "hi": [...], ... }
    """
    log("Phase 3: Generating voiceovers...")

    lang_codes = {"english": "en", "hindi": "hi", "spanish": "es", "german": "de"}
    audio_map = {}

    for scene in script["scenes"]:
        scene_id = scene["scene_id"]

        # English is always generated
        en_text = scene.get("voiceover_en", "")
        if en_text:
            path = generate_scene_audio(en_text, scene_id, "en")
            audio_map.setdefault("en", []).append(path)

        # Additional languages
        for lang in config.TARGET_LANGUAGES:
            lang = lang.strip().lower()
            if lang == "english":
                continue
            code = lang_codes.get(lang, lang[:2])
            key = f"voiceover_{code}"
            text = scene.get(key, "")
            if text:
                path = generate_scene_audio(text, scene_id, code)
                audio_map.setdefault(code, []).append(path)

    log(f"Phase 3: Voiceovers complete — {sum(len(v) for v in audio_map.values())} files generated.")
    return audio_map


def stitch_audio(audio_files: list[str], lang_code: str, topic_id: int) -> str:
    """
    Concatenate scene mp3s into one full audio track using binary append.
    For production use, replace with ffmpeg concat for proper stitching.
    Returns path to combined .mp3.
    """
    os.makedirs(config.AUDIO_DIR, exist_ok=True)
    out_path = f"{config.AUDIO_DIR}/full_voiceover_{topic_id}_{lang_code}.mp3"

    with open(out_path, "wb") as out_f:
        for mp3 in audio_files:
            if os.path.exists(mp3):
                with open(mp3, "rb") as f:
                    out_f.write(f.read())

    log(f"Phase 3: Stitched audio → {out_path}")
    return out_path
        if clips:
            concat_clip = concatenate_audioclips(clips)
            concat_clip.write_audiofile(out_path, logger=None)
            for c in clips:
                c.close()
            concat_clip.close()
            log(f"Phase 3: Stitched audio (MoviePy) → {out_path}")
            return out_path
    except Exception as e:
        log(f"Phase 3: MoviePy audio stitching failed ({e}) — falling back to binary write")

    with open(out_path, "wb") as out_f:
        for mp3 in audio_files:
            if os.path.exists(mp3):
                with open(mp3, "rb") as f:
                    out_f.write(f.read())

    log(f"Phase 3: Stitched audio → {out_path}")
    return out_path
