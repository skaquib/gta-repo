"""
upload_video.py — Uploads the locally compiled video using Phase 5 logic.
"""

import os
import json
from logger import log
import phase5_upload as p5
import config

def main():
    script_path = os.path.join(config.SCRIPTS_DIR, "script_1.json")
    video_path = os.path.join(config.VIDEOS_DIR, "video_fifa_worldcup.mp4")
    
    if not os.path.exists(script_path):
        log(f"ERROR: Script file not found at {script_path}")
        return
    if not os.path.exists(video_path):
        log(f"ERROR: Video file not found at {video_path}")
        return
        
    with open(script_path, "r", encoding="utf-8") as f:
        script = json.load(f)
        
    topic = {
        "id": 1,
        "title": script.get("video_title", "FIFA Referee Controversy"),
        "subject": "The ref who gave 3 yellow cards in a single World Cup match.",
        "category": "FIFA World Cup"
    }
    
    log(f"Uploading {video_path} to platforms...")
    
    secrets_path = getattr(config, "YOUTUBE_CLIENT_SECRETS", "client_secrets.json")
    if not os.path.exists(secrets_path) and not os.path.exists("youtube_token.pickle"):
        log("=" * 55)
        log("ERROR: YouTube authentication file is missing!")
        log("To upload to YouTube, you must download your OAuth 2.0 client secrets file:")
        log("1. Go to Google Cloud Console (https://console.cloud.google.com)")
        log("2. Enable the YouTube Data API v3.")
        log("3. Create OAuth Credentials, download the JSON client secret, and save it in this directory as:")
        log(f"   {secrets_path}")
        log("=" * 55)
        return
        
    try:
        results = p5.upload_all(video_path, script, topic)
        log("=" * 55)
        log("UPLOAD STATUS:")
        log(f"  YouTube: {results.get('youtube', 'Not uploaded')}")
        log(f"  Rumble:  {results.get('rumble', 'Not configured')}")
        log("=" * 55)
    except Exception as e:
        log(f"Upload process failed: {e}")

if __name__ == "__main__":
    main()
