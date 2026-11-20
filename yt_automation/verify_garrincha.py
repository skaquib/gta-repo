"""Pre-publish verification for documentary #3 (Garrincha).

Checks the things that actually went wrong on earlier renders, not just
generic health:
  - duration matches the voiceover (black-tail / truncation bugs)
  - no black frames (shared-reader collisions, faded clip tails)
  - voice audible, measured in 5s windows (a whole-file to_soundarray read
    produced a false "silent" alarm on 2026-09-14)
  - frames pulled at the EXACT narration moments that rendered off-topic
    before: the debut hat-trick showed a US tax form, the blank-contracts
    line showed a bar. Evenly spaced sampling would miss those.
"""
import os
import re
import sys

import numpy as np
from moviepy import AudioFileClip, VideoFileClip

import config
import pro_shorts_creator as psc
from resume_garrincha import VO, OUT

SCRATCH = sys.argv[1] if len(sys.argv) > 1 else os.path.join(config.OUTPUT_DIR, "verify_garrincha")

# narration word -> label for the frame that should match it
# Plain-English anchors only: whisper does not reliably spell proper nouns
# ("Bonsucesso" came out "bonesoceso", "wren" is missing), and a missed
# anchor silently skips exactly the frame that went wrong last time.
# Third value = earliest start: "injured" also occurs in the cold-open
# teaser at 31.8s, but the beat to check is Pele's 1962 injury.
KEY_WORDS = [
    ('sentence', 'doctor_sentence', 0),
    ('bird', 'bird_wren', 0),
    ('debut', 'debut_hattrick', 0),
    ('sweden', 'final_1958', 0),
    ('injured', 'pele_injured', 170),
    ('header', 'semi_header', 170),
    ('blank', 'blank_contracts', 0),
    ('rotting', 'cash_rotting', 0),
    ('lorry', 'crash_lorry', 0),
    ('maracana', 'funeral_procession', 0),
    ('grave', 'epitaph', 0),
]


def _word_times(path):
    words = psc.get_word_timestamps(path) or []
    out = []
    for w in words:
        if isinstance(w, dict):
            text = w.get("word") or w.get("text") or ""
            start = w.get("start", w.get("start_time"))
        else:
            text, start = w[0], w[1]
        if start is not None:
            out.append((re.sub(r"[^a-z]", "", str(text).lower()), float(start)))
    return out


def main():
    os.makedirs(SCRATCH, exist_ok=True)
    problems = []

    v = VideoFileClip(OUT)
    vo = AudioFileClip(VO)
    print(f"duration {v.duration:.1f}s | voiceover {vo.duration:.1f}s | size {v.size} | fps {v.fps}")
    if abs(v.duration - vo.duration) > 4.0:
        problems.append(f"duration {v.duration:.1f}s vs voiceover {vo.duration:.1f}s")
    if list(v.size) != [1920, 1080]:
        problems.append(f"size {v.size}")
    import json as _json
    with open(VO + ".words.json", encoding="utf-8") as _f:
        _words = _json.load(_f)
    if _words and _words[-1]["end"] > v.duration - 0.2:
        problems.append(f"narration ends {_words[-1]['end']:.1f}s but video is "
                        f"{v.duration:.1f}s -- closing line cut")

    # Black = dark AND no bright pixels. Mean alone flagged a deliberate
    # low-key shot (player + ball on black, max 255) as a defect.
    black = [round(float(t), 1) for t in np.arange(1.0, v.duration - 0.5, 3.0)
             if (lambda f: f.mean() < 12 and f.max() < 40)(v.get_frame(float(t)))]
    print(f"black frames: {len(black)} {black[:10]}")
    if black:
        problems.append(f"{len(black)} black frames")

    rms = []
    for t in np.linspace(10, max(11, v.duration - 12), 6):
        w = v.audio.subclipped(float(t), float(t) + 5).to_soundarray(fps=22050)
        rms.append(round(float(np.sqrt((w ** 2).mean())), 4))
    print(f"audio rms (5s windows): {rms}")
    if min(rms) < 0.02:
        problems.append(f"quiet audio window {min(rms)}")

    times = _word_times(VO)
    # Words actually spoken around each frame, so the burned-in caption can
    # be compared by eye: they must match (captions drifted 4.6s early once).
    raw_words = [(w["word"], w["start"]) for w in _words]
    print(f"word timings: {len(times)}")
    for word, label, after in KEY_WORDS:
        key = word.lower()
        hit = next((t for w, t in times if w.startswith(key) and t >= after), None)
        if hit is None:
            print(f"  (no timing for '{word}')")
            continue
        t = min(hit + 0.6, v.duration - 0.2)
        path = os.path.join(SCRATCH, f"{int(t):03d}s_{label}.jpg")
        v.save_frame(path, t=t)
        spoken = " ".join(w for w, ts in raw_words if t - 1.5 <= ts <= t + 0.2)
        print(f"  {label:20} t={t:6.1f}s spoken: {spoken!r} -> {path}")

    v.close()
    vo.close()
    print("RESULT:", "PASS (frames still need eyeballing)" if not problems else f"FAIL {problems}")


if __name__ == "__main__":
    main()
