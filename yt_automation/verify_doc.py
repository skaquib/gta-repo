"""Pre-publish verification for any long-form documentary.

Usage:
  python verify_doc.py <video.mp4> <voiceover> <scratch_dir> word:label[:after] ...

Checks the defects that actually shipped or nearly shipped before:
  - video shorter than the narration (closing line cut, 2026-09-14)
  - black frames: dark AND no bright pixels (mean alone flagged a deliberate
    low-key shot)
  - quiet audio, measured in 5s windows
  - a frame at each anchor word, with the words spoken around it printed so
    the burned-in caption can be compared by eye (captions once ran 4.6s
    ahead of the voice). Use plain English anchors: whisper misspells proper
    nouns. `after` skips earlier occurrences (e.g. a cold-open teaser).
"""
import json
import os
import re
import sys

import numpy as np
from moviepy import AudioFileClip, VideoFileClip


def main():
    video, vo, scratch = sys.argv[1], sys.argv[2], sys.argv[3]
    anchors = []
    for spec in sys.argv[4:]:
        parts = spec.split(":")
        anchors.append((parts[0].lower(), parts[1], float(parts[2]) if len(parts) > 2 else 0.0))
    os.makedirs(scratch, exist_ok=True)
    problems = []

    v = VideoFileClip(video)
    a = AudioFileClip(vo)
    print(f"duration {v.duration:.1f}s | voiceover {a.duration:.1f}s | size {v.size} | fps {v.fps}")
    if list(v.size) != [1920, 1080]:
        problems.append(f"size {v.size}")

    with open(vo + ".words.json", encoding="utf-8") as f:
        words = json.load(f)
    if words and words[-1]["end"] > v.duration - 0.2:
        problems.append(f"narration ends {words[-1]['end']:.1f}s but video is {v.duration:.1f}s")

    black = [round(float(t), 1) for t in np.arange(1.0, v.duration - 0.5, 3.0)
             if (lambda fr: fr.mean() < 12 and fr.max() < 40)(v.get_frame(float(t)))]
    print(f"black frames: {len(black)} {black[:10]}")
    if black:
        problems.append(f"{len(black)} black frames")

    # Dark stretches: mean brightness < 20 for a second or more. The black
    # test above passed doc #4 while 2.5s of near-black (a night fireworks
    # clip, mean ~5, a few bright sparks) sat under its climax line.
    dark = [float(t) for t in np.arange(0.25, v.duration - 0.1, 0.5)
            if v.get_frame(float(t)).mean() < 20]
    runs, cur = [], []
    for t in dark:
        if cur and t - cur[-1] > 0.6:
            runs.append((cur[0], cur[-1]))
            cur = []
        cur.append(t)
    if cur:
        runs.append((cur[0], cur[-1]))
    long_runs = [(round(a, 1), round(b, 1)) for a, b in runs if b - a >= 1.0]
    print(f"dark stretches >=1s: {long_runs}")
    if long_runs:
        problems.append(f"dark stretches {long_runs}")

    rms = []
    for t in np.linspace(10, max(11, v.duration - 12), 6):
        w = v.audio.subclipped(float(t), float(t) + 5).to_soundarray(fps=22050)
        rms.append(round(float(np.sqrt((w ** 2).mean())), 4))
    print(f"audio rms (5s windows): {rms}")
    if min(rms) < 0.02:
        problems.append(f"quiet audio window {min(rms)}")

    norm = [(re.sub(r"[^a-z]", "", w["word"].lower()), w["start"]) for w in words]
    for key, label, after in anchors:
        hit = next((t for w, t in norm if w.startswith(key) and t >= after), None)
        if hit is None:
            print(f"  (no timing for '{key}')")
            problems.append(f"anchor '{key}' not found")
            continue
        t = min(hit + 0.6, v.duration - 0.2)
        path = os.path.join(scratch, f"{int(t):03d}s_{label}.jpg")
        v.save_frame(path, t=t)
        spoken = " ".join(w["word"] for w in words if t - 1.5 <= w["start"] <= t + 0.2)
        print(f"  {label:20} t={t:6.1f}s spoken: {spoken!r}")

    v.close()
    a.close()
    print("RESULT:", "PASS (frames still need eyeballing)" if not problems else f"FAIL {problems}")


if __name__ == "__main__":
    main()
