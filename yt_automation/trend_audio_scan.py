"""Measure the AUDIO of this week's top-performing Shorts in our niche.

The YouTube API returns titles and view counts but nothing about sound, and
the owner asked that research cover what people like to HEAR as well as
see. For each Short this downloads only the audio track (never the video)
into a scratch folder and measures:
  - speech density (words/second, via the same whisper step the pipeline
    uses): ~0 = music/original audio only, 2+ = continuous voiceover
  - loudness (RMS) against our own voiceover target
  - how soon the first spoken word lands (hook timing)

Input: output/trend_scan_<date>.json from the metadata scan.
"""
import glob
import json
import os
import subprocess
import sys

import numpy as np

import pro_shorts_creator as psc
from moviepy import AudioFileClip

SCAN = sys.argv[1]
OUT_DIR = sys.argv[2]
TOP_N = int(sys.argv[3]) if len(sys.argv) > 3 else 8

os.makedirs(OUT_DIR, exist_ok=True)
rows = json.load(open(SCAN, encoding="utf-8"))[:TOP_N]
results = []
for r in rows:
    vid = r["id"]
    dest = os.path.join(OUT_DIR, vid)
    wav = dest + ".wav"
    if not os.path.exists(wav):
        raw = [f for f in glob.glob(dest + ".*") if not f.endswith(".wav")]
        if not raw:
            # Audio track only. No "-x": yt-dlp needs ffmpeg on PATH for that,
            # and this machine only has the copy bundled with imageio-ffmpeg.
            subprocess.run([sys.executable, "-m", "yt_dlp", "-q", "--no-warnings",
                            "-f", "bestaudio", "-o", dest + ".%(ext)s",
                            f"https://www.youtube.com/shorts/{vid}"],
                           capture_output=True, text=True, timeout=180)
            raw = [f for f in glob.glob(dest + ".*") if not f.endswith(".wav")]
        if not raw:
            print(f"{vid}: download failed")
            continue
        import imageio_ffmpeg
        subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
                        "-i", raw[0], "-ac", "1", "-ar", "16000", wav],
                       capture_output=True, text=True, timeout=120)
    if not os.path.exists(wav):
        print(f"{vid}: conversion failed")
        continue
    clip = AudioFileClip(wav)
    dur = clip.duration
    arr = clip.to_soundarray(fps=16000)
    clip.close()
    rms = float(np.sqrt((arr ** 2).mean()))
    words = psc.get_word_timestamps(wav) or []
    wps = len(words) / dur if dur else 0.0
    first = words[0]["start"] if words else None
    kind = "voiceover" if wps >= 1.5 else ("some speech" if wps >= 0.4 else "music/original audio")
    results.append({**{k: r[k] for k in ("views", "secs", "channel", "title")},
                    "rms": round(rms, 4), "words_per_sec": round(wps, 2),
                    "first_word_s": first, "kind": kind,
                    "sample_words": " ".join(w["word"] for w in words[:12])})

json.dump(results, open(os.path.join(OUT_DIR, "audio_results.json"), "w", encoding="utf-8"), indent=1)
for x in results:
    fw = "-" if x["first_word_s"] is None else f"{x['first_word_s']:.1f}s"
    print(f"{x['views']:>9} {x['secs']:>3}s rms {x['rms']:.3f} | {x['words_per_sec']:>4} w/s first {fw:>5} | "
          f"{x['kind']:21} | {x['title'][:40]}")
    if x["sample_words"]:
        print(f"{'':12}says: {x['sample_words'][:90]}")
