"""
voice_clone_generator.py — Clones the creator's voice (Recording (2).wav) onto
narration text using MeloTTS (base speech synthesis) + OpenVoice V2 (tone-color
conversion). Runs under venv_openvoice's Python, invoked as a subprocess from
pro_shorts_creator.py (main env).

Usage: venv_openvoice/Scripts/python.exe voice_clone_generator.py <job.json>
  job.json: {"text": "...", "out_path": "..."}
Prints {"ok": true/false, "out_path": ..., "error": ...} as JSON to stdout.
"""

import json
import os
import sys

import torch
from huggingface_hub import hf_hub_download

REPO = "myshell-ai/OpenVoiceV2"
CKPT_DIR = os.path.join(os.path.dirname(__file__), "openvoice_checkpoints")
REFERENCE_AUDIO = os.path.join(os.path.dirname(__file__), "Recording (2).wav")
TARGET_SE_CACHE = os.path.join(CKPT_DIR, "target_se.pth")
DEVICE = "cuda:0" if torch.cuda.is_available() else "cpu"


def ensure_checkpoints():
    os.makedirs(CKPT_DIR, exist_ok=True)
    converter_dir = os.path.join(CKPT_DIR, "converter")
    os.makedirs(converter_dir, exist_ok=True)
    for fname in ["converter/config.json", "converter/checkpoint.pth", "base_speakers/ses/en-default.pth"]:
        local_path = os.path.join(CKPT_DIR, fname)
        if not os.path.exists(local_path):
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            downloaded = hf_hub_download(repo_id=REPO, filename=fname)
            import shutil
            shutil.copy(downloaded, local_path)
    return converter_dir


def get_target_se(tone_color_converter):
    from openvoice import se_extractor
    if os.path.exists(TARGET_SE_CACHE):
        return torch.load(TARGET_SE_CACHE, map_location=DEVICE)
    target_se, _ = se_extractor.get_se(REFERENCE_AUDIO, tone_color_converter, vad=False)
    torch.save(target_se, TARGET_SE_CACHE)
    return target_se


def main():
    job_path = sys.argv[1]
    with open(job_path, encoding="utf-8") as f:
        job = json.load(f)

    try:
        from openvoice.api import ToneColorConverter
        from melo.api import TTS as MeloTTS

        converter_dir = ensure_checkpoints()
        tone_color_converter = ToneColorConverter(os.path.join(converter_dir, "config.json"), device=DEVICE)
        tone_color_converter.load_ckpt(os.path.join(converter_dir, "checkpoint.pth"))

        target_se = get_target_se(tone_color_converter)
        source_se = torch.load(os.path.join(CKPT_DIR, "base_speakers/ses/en-default.pth"), map_location=DEVICE)

        melo = MeloTTS(language="EN", device=DEVICE)
        speaker_ids = melo.hps.data.spk2id
        speaker_key = "EN-Default" if "EN-Default" in speaker_ids else list(speaker_ids.keys())[0]

        base_wav = job["out_path"] + ".base.wav"
        melo.tts_to_file(job["text"], speaker_ids[speaker_key], base_wav, speed=1.0)

        tone_color_converter.convert(
            audio_src_path=base_wav, src_se=source_se, tgt_se=target_se,
            output_path=job["out_path"], message="@MyShell",
        )
        os.remove(base_wav)
        print(json.dumps({"ok": True, "out_path": job["out_path"], "error": None}))
    except Exception as e:
        import traceback
        traceback.print_exc(file=sys.stderr)
        print(json.dumps({"ok": False, "out_path": job.get("out_path"), "error": str(e)}))


if __name__ == "__main__":
    main()
