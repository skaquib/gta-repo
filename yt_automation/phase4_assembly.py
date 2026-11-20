"""
Phase 4 — Video Assembly via Shotstack
Sends scene data + audio to Shotstack cloud renderer.
Returns a rendered MP4 download URL.
"""

import time
import requests
import config
from logger import log

BASE_URL = f"https://api.shotstack.io/{config.SHOTSTACK_ENV}"

HEADERS = {
    "x-api-key": config.SHOTSTACK_API_KEY,
    "Content-Type": "application/json",
}

STYLE_COLORS = {
    "Hook":         {"bg": "#1a1a2e", "text": "#e94560"},
    "Introduction": {"bg": "#16213e", "text": "#0f3460"},
    "Point1":       {"bg": "#0f3460", "text": "#e94560"},
    "Point2":       {"bg": "#533483", "text": "#ffffff"},
    "Point3":       {"bg": "#1a1a2e", "text": "#f5a623"},
    "Point4":       {"bg": "#16213e", "text": "#4ecdc4"},
    "Point5":       {"bg": "#0f3460", "text": "#ffffff"},
    "CTA":          {"bg": "#e94560", "text": "#ffffff"},
}


def build_timeline(script: dict, audio_path_url: str) -> dict:
    """
    Build a Shotstack timeline from script scenes.
    Each scene = a title card with the visual description as caption.
    Audio track = the full stitched voiceover.
    For Shorts, mixes background music and uses portrait dimensions.
    """
    clips = []
    current_time = 0.0
    is_shorts = getattr(config, "VIDEO_TYPE", "long") == "shorts"
    width, height = (1080, 1920) if is_shorts else (1920, 1080)

    for scene in script["scenes"]:
        duration = float(scene.get("duration_seconds", 5))
        section = scene.get("section", "Point1")
        colors = STYLE_COLORS.get(section, {"bg": "#1a1a2e", "text": "#ffffff"})
        visual = scene.get("visual_description", "")[:80]
        voiceover = scene.get("voiceover_en", "")

        # Background colour clip with linear gradient for Shorts to make it look premium
        if is_shorts:
            bg_color = colors.get("bg", "#1a1a2e")
            bg_html = f'<div style="width:{width}px;height:{height}px;background:linear-gradient(180deg, {bg_color} 0%, #000000 100%);"></div>'
        else:
            bg_html = f'<div style="width:{width}px;height:{height}px;background:{colors["bg"]};"></div>'

        clips.append({
            "asset": {"type": "html", "html": bg_html, "width": width, "height": height},
            "start": current_time,
            "length": duration,
        })

        # Main title text
        max_chars = 120 if is_shorts else 50
        text_to_show = voiceover[:max_chars] if voiceover else visual[:max_chars]

        title_clip = {
            "asset": {
                "type": "title",
                "text": text_to_show,
                "style": "chunk" if is_shorts else "future",
                "color": colors["text"],
                "size": "large" if is_shorts else "medium",
            },
            "start": current_time,
            "length": duration,
            "position": "center",
        }
        if not is_shorts:
            title_clip["transition"] = {"in": "fade", "out": "fade"}
        clips.append(title_clip)

        # Visual description caption (only in landscape mode, too crowded for Shorts)
        if not is_shorts:
            clips.append({
                "asset": {
                    "type": "title",
                    "text": visual,
                    "style": "minimal",
                    "color": "#aaaaaa",
                    "size": "x-small",
                },
                "start": current_time,
                "length": duration,
                "position": "bottom",
            })

        current_time += duration

    # Channel watermark
    clips.append({
        "asset": {
            "type": "title",
            "text": config.CHANNEL_NAME,
            "style": "minimal",
            "color": "#ffffff",
            "size": "x-small",
        },
        "start": 0,
        "length": current_time,
        "position": "top" if is_shorts else "topRight",
        "opacity": 0.5,
    })

    # For Shorts, we mix background music as the timeline soundtrack (at low volume),
    # and put the ElevenLabs voiceover as a separate audio track.
    if is_shorts:
        timeline = {
            "soundtrack": {
                "src": config.BG_MUSIC_URL,
                "volume": 0.18,
                "effect": "fadeOut",
            },
            "tracks": [
                {"clips": clips},  # Visual and overlay clips
                {
                    "clips": [
                        {
                            "asset": {
                                "type": "audio",
                                "src": audio_path_url,
                            },
                            "start": 0,
                            "length": current_time,
                        }
                    ]
                }
            ],
        }
    else:
        timeline = {
            "soundtrack": {
                "src": audio_path_url,
                "effect": "fadeOut",
            },
            "tracks": [{"clips": clips}],
        }

    return timeline


def submit_render(script: dict, audio_url: str, topic_id: int) -> str:
    """Submit render job to Shotstack. Returns render ID."""
    log("Phase 4: Building Shotstack timeline...")

    timeline = build_timeline(script, audio_url)
    is_shorts = getattr(config, "VIDEO_TYPE", "long") == "shorts"

    if is_shorts:
        output_config = {
            "format": "mp4",
            "size": {
                "width": 1080,
                "height": 1920
            },
            "fps": 24,
            "quality": "high",
        }
    else:
        output_config = {
            "format": "mp4",
            "resolution": "hd",
            "fps": 24,
            "quality": "high",
        }

    payload = {
        "timeline": timeline,
        "output": output_config,
    }

    resp = requests.post(f"{BASE_URL}/render", headers=HEADERS, json=payload, timeout=30)

    if resp.status_code in (200, 201):
        render_id = resp.json()["response"]["id"]
        log(f"Phase 4: Render submitted — ID: {render_id}")
        return render_id
    else:
        log(f"Phase 4 ERROR: {resp.status_code} — {resp.text[:300]}")
        raise Exception(f"Shotstack render failed: {resp.status_code}")


def poll_render(render_id: str, timeout_minutes: int = 20) -> str:
    """Poll until render is done. Returns download URL."""
    log(f"Phase 4: Waiting for render {render_id}...")
    deadline = time.time() + timeout_minutes * 60

    while time.time() < deadline:
        resp = requests.get(f"{BASE_URL}/render/{render_id}", headers=HEADERS, timeout=15)
        data = resp.json()["response"]
        status = data.get("status")

        if status == "done":
            url = data["url"]
            log(f"Phase 4: Render complete → {url}")
            return url
        elif status == "failed":
            log(f"Phase 4 ERROR: Render failed — {data}")
            raise Exception("Shotstack render failed")
        else:
            log(f"  Status: {status} — waiting 20s...")
            time.sleep(20)

    raise TimeoutError("Shotstack render timed out after 20 minutes")


def download_video(url: str, topic_id: int, lang_code: str = "en") -> str:
    """Download the rendered MP4 to local disk."""
    import os
    os.makedirs(config.VIDEOS_DIR, exist_ok=True)
    out_path = f"{config.VIDEOS_DIR}/video_{topic_id}_{lang_code}.mp4"

    log(f"Phase 4: Downloading video → {out_path}")
    resp = requests.get(url, stream=True, timeout=120)
    with open(out_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)

    log(f"Phase 4: Video saved ({os.path.getsize(out_path) // 1024 // 1024} MB)")
    return out_path
