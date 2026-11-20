"""
PREMIUM ONE-SHOT: Generate 1 best-quality video using the viral sound.
NO auto-upload — just renders locally and prints the file path.
"""
import os, sys, shutil, time

# ── Setup ─────────────────────────────────────────────────────────────────────
SOUND_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sound_KjtcO6wwgtY.mp3")
if not os.path.exists(SOUND_FILE):
    print(f"ERROR: Sound file not found at {SOUND_FILE}")
    sys.exit(1)

import visual_shorts_creator as vsc
from visual_shorts_creator import (
    generate_dynamic_script_with_gemini, download_clips, generate_voiceover,
    assemble, log, AudioFileClip, config
)


def pick_theme():
    try:
        return vsc.COLOR_THEMES[0]
    except Exception:
        return {"accent": (0, 220, 110), "text": (255, 255, 255), "shadow": (0, 180, 80)}

# ── Copy viral sound into audio dir ───────────────────────────────────────────
os.makedirs(config.AUDIO_DIR, exist_ok=True)
music_dest = os.path.join(config.AUDIO_DIR, "viral_sound.mp3")
shutil.copy2(SOUND_FILE, music_dest)
log(f"Using viral sound: {music_dest}")

# ── Override get_music ────────────────────────────────────────────────────────
def patched_get_music(duration=30.0):
    log(f"[VIRAL SOUND] Using downloaded viral sound ({os.path.getsize(music_dest)/1e6:.1f}MB)")
    return music_dest
vsc.get_music = patched_get_music

# ── Override upload to SKIP ───────────────────────────────────────────────────
def skip_upload(video_path, script):
    log("SKIPPED UPLOAD — local file only (as requested)")
    return None
vsc.upload = skip_upload

# ── Generate ──────────────────────────────────────────────────────────────────
log("=" * 60)
log("  PREMIUM VIDEO — BEST QUALITY — LOCAL ONLY")
log("  Viral sound + Cloned voice + Pexels HD footage")
log("=" * 60)

# 1. Script
script = generate_dynamic_script_with_gemini()
theme = pick_theme()
log(f"Subject: {script.get('title','?')}")

# 2. Clips
clip_paths = download_clips(script)
log(f"Got {len(clip_paths)} clip(s)")

# 3. Voiceover
try:
    vo_path = generate_voiceover(script)
except Exception as e:
    log(f"Voice failed ({e}) — instrumental only")
    vo_path = None

# 4. Music (viral sound)
vo_duration = 21.0
if vo_path:
    try:
        vo_clip = AudioFileClip(vo_path)
        vo_duration = min(vo_clip.duration + 1.5, 58.0)
        vo_clip.close()
    except Exception:
        pass

# 5. Assemble (NO upload)
os.makedirs(config.VIDEOS_DIR, exist_ok=True)
out_path = os.path.join(config.VIDEOS_DIR, f"BEST_viral_{int(time.time())}.mp4")
assemble(clip_paths, script, vo_path, music_dest, theme, out_path, is_image_clips=False)

abs_path = os.path.abspath(out_path)
log("")
log("=" * 60)
log("  VIDEO RENDER COMPLETE!")
log(f"  Title: {script.get('title','')[:80]}")
log(f"  FILE: {abs_path}")
log("=" * 60)
print(f"\n\n>>> YOUR VIDEO IS READY <<<")
print(f">>> {abs_path}")
print(f">>> Open this file to preview it!\n")
