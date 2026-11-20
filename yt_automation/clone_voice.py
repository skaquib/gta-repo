"""
clone_voice.py — One-time setup: clone the creator's own voice via ElevenLabs
Instant Voice Cloning, then write the resulting voice_id into .env so the
main pipeline (pro_shorts_creator.py) narrates in that voice instead of a
generic TTS voice.

Run once: python clone_voice.py
"""

import os
import sys
import requests
from dotenv import set_key
import config
from logger import log

ENV_PATH = ".env"
SAMPLES = ["Recording (2).m4a", "Recording (2).wav"]
VOICE_NAME = "FramedFacts Creator Voice"


def add_voice(sample_path: str) -> str:
    log(f"Uploading {sample_path} to ElevenLabs for voice cloning...")
    with open(sample_path, "rb") as f:
        files = {"files": (os.path.basename(sample_path), f)}
        data = {"name": VOICE_NAME}
        r = requests.post(
            "https://api.elevenlabs.io/v1/voices/add",
            headers={"xi-api-key": config.ELEVENLABS_API_KEY},
            data=data, files=files, timeout=120,
        )
    if r.status_code not in (200, 201):
        raise Exception(f"ElevenLabs voices/add failed {r.status_code}: {r.text[:300]}")
    voice_id = r.json().get("voice_id")
    if not voice_id:
        raise Exception(f"No voice_id in response: {r.text[:300]}")
    return voice_id


def main():
    if not config.ELEVENLABS_API_KEY:
        log("ERROR: ELEVENLABS_API_KEY is not set in .env")
        sys.exit(1)

    samples = [p for p in SAMPLES if os.path.exists(p)]
    if not samples:
        log(f"ERROR: none of {SAMPLES} found in {os.getcwd()}")
        sys.exit(1)

    last_err = None
    for sample_path in samples:
        try:
            voice_id = add_voice(sample_path)
            log(f"Voice cloned successfully: voice_id={voice_id}")
            set_key(ENV_PATH, "ELEVENLABS_VOICE_ID", voice_id)
            log(f"Updated {ENV_PATH}: ELEVENLABS_VOICE_ID={voice_id}")
            return
        except Exception as e:
            log(f"Failed with {sample_path}: {e}")
            last_err = e

    log("ERROR: all samples failed to clone.")
    if last_err:
        log(f"Last error: {last_err}")
    sys.exit(1)


if __name__ == "__main__":
    main()
