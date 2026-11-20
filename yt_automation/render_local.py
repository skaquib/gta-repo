"""
render_local.py — Pure Python Local Video Renderer for YouTube Shorts
Bypasses Shotstack entirely. Uses moviepy and PIL.
"""

import os
import json
import requests
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from logger import log
import config

# Install fallback imports safely
try:
    from moviepy import ImageClip, concatenate_videoclips, AudioFileClip, CompositeAudioClip
except ImportError:
    try:
        from moviepy.video.VideoClip import ImageClip
        from moviepy.video.compositing.concatenate import concatenate_videoclips
        from moviepy.audio.io.AudioFileClip import AudioFileClip
        from moviepy.audio.AudioClip import CompositeAudioClip
    except ImportError as e:
        log(f"Import Error: {e}. Please ensure moviepy is installed.")
        raise

# Visual constants matching our styled theme
STYLE_COLORS = {
    "Hook":         {"bg": "#0c2c12", "text": "#00ff66"}, # Soccer green style
    "Introduction": {"bg": "#121824", "text": "#00d2ff"},
    "Point1":       {"bg": "#1a0b2e", "text": "#ff007f"},
    "Point2":       {"bg": "#2e1c0b", "text": "#ffcc00"},
    "Point3":       {"bg": "#0c2c12", "text": "#ffffff"},
    "Point4":       {"bg": "#121824", "text": "#00ff66"},
    "Point5":       {"bg": "#1a0b2e", "text": "#ffffff"},
    "CTA":          {"bg": "#ff007f", "text": "#ffffff"},
}

def download_bg_music(url: str, dest_path: str):
    """Download background music if it doesn't exist locally."""
    if os.path.exists(dest_path):
        log(f"Background music already exists at {dest_path}")
        return
    log(f"Downloading background music from {url}...")
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    resp = requests.get(url, timeout=60)
    if resp.status_code == 200:
        with open(dest_path, "wb") as f:
            f.write(resp.content)
        log("Background music downloaded successfully.")
    else:
        raise Exception(f"Failed to download background music: {resp.status_code}")

def create_text_frame(text: str, width: int = 1080, height: int = 1920, bg_hex: str = "#121824", text_hex: str = "#ffffff") -> Image.Image:
    """Create a single vertical video frame with wrapped, centered text and a watermark."""
    # Convert hex colors to RGB tuples
    def hex_to_rgb(hex_str):
        hex_str = hex_str.lstrip('#')
        return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

    bg_color = hex_to_rgb(bg_hex)
    text_color = hex_to_rgb(text_hex)

    # We use a linear gradient from the bg_color to pure black for a premium look
    img = Image.new("RGB", (width, height), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw gradient background manually
    for y in range(height):
        ratio = y / height
        # Blend from bg_color (top) to black (bottom)
        r = int(bg_color[0] * (1 - ratio))
        g = int(bg_color[1] * (1 - ratio))
        b = int(bg_color[2] * (1 - ratio))
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Font setup: Impact is bold and viral for sports memes/shorts
    font_path = "C:\\Windows\\Fonts\\impact.ttf"
    if not os.path.exists(font_path):
        font_path = "C:\\Windows\\Fonts\\arialbd.ttf" # Bold Arial fallback
    if not os.path.exists(font_path):
        font_path = "C:\\Windows\\Fonts\\arial.ttf"

    font_size = 75
    font = ImageFont.truetype(font_path, font_size) if os.path.exists(font_path) else ImageFont.load_default()

    # Draw channel watermark at the top
    watermark_font = ImageFont.truetype(font_path, 35) if os.path.exists(font_path) else ImageFont.load_default()
    watermark_text = config.CHANNEL_NAME.upper()
    w_bbox = draw.textbbox((0, 0), watermark_text, font=watermark_font)
    w_w = w_bbox[2] - w_bbox[0]
    draw.text(((width - w_w) // 2, 180), watermark_text, font=watermark_font, fill=(160, 160, 160))

    # Wrap the voiceover/visual text to fit inside width (with padding)
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        current_line.append(word)
        line_str = " ".join(current_line)
        bbox = draw.textbbox((0, 0), line_str, font=font)
        w = bbox[2] - bbox[0]
        if w > width - 160: # 80px padding each side
            current_line.pop()
            lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))

    # Draw each line centered vertically and horizontally
    line_heights = []
    total_text_height = 0
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        h = bbox[3] - bbox[1]
        line_heights.append(h)
        total_text_height += h + 25
    total_text_height -= 25

    start_y = (height - total_text_height) // 2
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        h = line_heights[i]
        x = (width - w) // 2
        
        # Draw text shadow for ultimate readability
        draw.text((x + 4, start_y + 4), line, font=font, fill=(0, 0, 0))
        draw.text((x, start_y), line, font=font, fill=text_color)
        start_y += h + 25

    return img

def set_clip_duration(clip, duration):
    """Backward compatibility helper for moviepy duration setter."""
    if hasattr(clip, "with_duration"):
        return clip.with_duration(duration)
    else:
        return clip.set_duration(duration)

def set_clip_audio(clip, audio):
    """Backward compatibility helper for moviepy audio setter."""
    if hasattr(clip, "with_audio"):
        return clip.with_audio(audio)
    else:
        return clip.set_audio(audio)

def add_progress_bar_to_frame(frame, t, total_duration):
    """Draws a neon-green progress bar at the bottom of the current frame array."""
    pil_img = Image.fromarray(frame)
    draw = ImageDraw.Draw(pil_img)
    
    # Progress bar parameters
    bar_y = 1750
    bar_height = 12
    width = 1080
    
    # Draw gray track
    draw.line([(0, bar_y), (width, bar_y)], fill=(50, 50, 50), width=bar_height)
    
    # Draw progress line (neon green)
    progress_x = int((t / total_duration) * width)
    if progress_x > 0:
        draw.line([(0, bar_y), (progress_x, bar_y)], fill=(0, 255, 102), width=bar_height)
        
    return np.array(pil_img)

def render_video():
    log("=" * 55)
    log("  LOCAL VIDEO RENDERER — STARTING")
    log("=" * 55)

    topic_id = 1
    script_path = os.path.join(config.SCRIPTS_DIR, f"script_{topic_id}.json")
    
    if not os.path.exists(script_path):
        log(f"ERROR: Script not found at {script_path}")
        return

    with open(script_path, "r", encoding="utf-8") as f:
        script = json.load(f)

    # 1. Download/Verify background music
    bg_music_path = os.path.join(config.AUDIO_DIR, "bg_music.mp3")
    download_bg_music(config.BG_MUSIC_URL, bg_music_path)

    # 2. Verify voiceover exists
    voiceover_path = os.path.join(config.AUDIO_DIR, f"full_voiceover_{topic_id}_en.mp3")
    if not os.path.exists(voiceover_path):
        log(f"ERROR: Voiceover file not found: {voiceover_path}. Run pipeline/generate voiceover first.")
        return

    # 3. Create scene visual clips using PIL
    log("Rendering visual clips with PIL...")
    scene_clips = []
    for scene in script["scenes"]:
        duration = float(scene.get("duration_seconds", 6))
        section = scene.get("section", "Point1")
        colors = STYLE_COLORS.get(section, {"bg": "#121824", "text": "#ffffff"})
        
        voiceover_text = scene.get("voiceover_en", "")
        visual_desc = scene.get("visual_description", "")
        text_content = voiceover_text if voiceover_text else visual_desc
        
        # Create text frame
        pil_frame = create_text_frame(text_content, bg_hex=colors["bg"], text_hex=colors["text"])
        frame_arr = np.array(pil_frame)
        
        # Create ImageClip
        clip = ImageClip(frame_arr)
        clip = set_clip_duration(clip, duration)
        scene_clips.append(clip)

    # Concatenate visual clips
    log("Concatenating visual scenes...")
    video = concatenate_videoclips(scene_clips, method="compose")
    total_duration = video.duration
    log(f"Visual timeline complete. Duration: {total_duration} seconds.")

    # 4. Process and mix audio
    log("Mixing voiceover and background music...")
    voiceover_audio = AudioFileClip(voiceover_path)
    
    bg_music_audio = AudioFileClip(bg_music_path)
    bg_music_audio = set_clip_duration(bg_music_audio, total_duration)
    
    # Apply volume ducking to background music
    if hasattr(bg_music_audio, "with_volume_scaled"):
        bg_music_audio = bg_music_audio.with_volume_scaled(0.18)
    elif hasattr(bg_music_audio, "multiply_volume"):
        bg_music_audio = bg_music_audio.multiply_volume(0.18)
    else:
        bg_music_audio = bg_music_audio.volumex(0.18)

    mixed_audio = CompositeAudioClip([voiceover_audio, bg_music_audio])
    mixed_audio = set_clip_duration(mixed_audio, total_duration)

    # Attach mixed audio to the video
    video = set_clip_audio(video, mixed_audio)

    # 5. Apply dynamic progress bar using image transformer filter
    log("Applying dynamic progress bar filter...")
    filter_fn = lambda gf, t: add_progress_bar_to_frame(gf(t), t, total_duration)
    if hasattr(video, "transform"):
        video_with_bar = video.transform(filter_fn)
    else:
        video_with_bar = video.fl(filter_fn)

    # 6. Write final video file
    os.makedirs(config.VIDEOS_DIR, exist_ok=True)
    out_video_path = os.path.join(config.VIDEOS_DIR, f"video_{topic_id}_en.mp4")
    
    log(f"Writing final vertical MP4 video to {out_video_path}...")
    # Render settings: fps=24, threads=4 for speed
    video_with_bar.write_videofile(
        out_video_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        logger="bar"
    )
    
    # Close resources safely
    video_with_bar.close()
    video.close()
    voiceover_audio.close()
    bg_music_audio.close()
    mixed_audio.close()

    log("=" * 55)
    log("  LOCAL RENDER COMPLETE!")
    log(f"  Final Video Saved To: {out_video_path}")
    log("=" * 55)
    
    return out_video_path

if __name__ == "__main__":
    render_video()
