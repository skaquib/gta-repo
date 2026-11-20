"""
One-shot: generate 1 video using the downloaded viral sound
(sound_KjtcO6wwgtY.mp3) as background music, then upload.
"""
import os, sys, shutil

# Force the viral sound as the only music track
SOUND_FILE = os.path.join(os.path.dirname(__file__), "sound_KjtcO6wwgtY.mp3")
if not os.path.exists(SOUND_FILE):
    print(f"ERROR: Sound file not found at {SOUND_FILE}")
    sys.exit(1)

# Monkey-patch MUSIC_TRACKS and get_music before importing the creator
import visual_shorts_creator as vsc

# Copy the sound into audio dir so MoviePy can use it
os.makedirs(vsc.config.AUDIO_DIR, exist_ok=True)
music_dest = os.path.join(vsc.config.AUDIO_DIR, "viral_sound.mp3")
shutil.copy2(SOUND_FILE, music_dest)
print(f"[*] Copied viral sound to {music_dest}")

# Override get_music to always return the viral sound
_original_get_music = vsc.get_music
def patched_get_music(duration=30.0):
    print(f"[*] Using viral sound: {music_dest}")
    return music_dest
vsc.get_music = patched_get_music

# Now run one job
vsc.run_one_job()
