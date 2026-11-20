"""
whisper_timing.py — Transcribes a voiceover file and returns real word-level
timestamps, so captions and visual-segment cuts can be synced to what's
actually being spoken instead of a guessed constant speech rate.
Runs under venv_openvoice's Python (faster-whisper already installed there
for voice cloning's se_extractor).

Usage: venv_openvoice/Scripts/python.exe whisper_timing.py <audio_path>
Prints a JSON list of {"word": str, "start": float, "end": float} to stdout.
"""

import json
import sys

from faster_whisper import WhisperModel

_model = None


def get_model():
    global _model
    if _model is None:
        _model = WhisperModel("base", device="cpu", compute_type="int8")
    return _model


def transcribe_words(audio_path: str) -> list:
    model = get_model()
    segments, _ = model.transcribe(audio_path, word_timestamps=True)
    words = []
    for seg in segments:
        for w in seg.words:
            words.append({"word": w.word.strip(), "start": w.start, "end": w.end})
    return words


def main():
    audio_path = sys.argv[1]
    words = transcribe_words(audio_path)
    print(json.dumps(words))


if __name__ == "__main__":
    main()
