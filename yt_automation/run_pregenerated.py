"""
run_pregenerated.py — Run the automation pipeline using a pre-generated script JSON.
Usage: python run_pregenerated.py
"""

import sys
import json
import datetime
import os
from logger import log

import phase3_voiceover as p3
import phase4_assembly  as p4
import phase5_upload    as p5
import config

def run_pipeline():
    start = datetime.datetime.now()
    log("=" * 55)
    log("  YT AUTOMATION PIPELINE — PRE-GENERATED SHORTS RUN")
    log("=" * 55)

    topic_id = 1
    script_path = os.path.join(config.SCRIPTS_DIR, f"script_{topic_id}.json")
    
    if not os.path.exists(script_path):
        log(f"ERROR: Pregenerated script not found at {script_path}")
        sys.exit(1)
        
    with open(script_path, "r", encoding="utf-8") as f:
        script = json.load(f)
        
    topic = {
        "id": topic_id,
        "title": script.get("video_title", "FIFA Referee Controversy"),
        "subject": "The ref who gave 3 yellow cards in a single World Cup match.",
        "category": "FIFA World Cup"
    }

    log(f"Loaded pregenerated script for topic {topic_id}: '{topic['title']}'")

    # ── Phase 3: Voiceover ────────────────────────────────
    audio_map = p3.generate_all_voiceovers(script, topic_id)

    # Stitch English as primary track
    en_files = audio_map.get("en", [])
    if not en_files:
        log("ERROR: No English audio generated. Aborting.")
        sys.exit(1)

    en_audio_path = p3.stitch_audio(en_files, "en", topic_id)

    # ── Phase 4: Video Assembly ───────────────────────────
    audio_public_url = upload_audio_to_shotstack(en_audio_path)

    render_id  = p4.submit_render(script, audio_public_url, topic_id)
    video_url  = p4.poll_render(render_id)
    video_path = p4.download_video(video_url, topic_id, "en")

    # ── Phase 5: Upload ───────────────────────────────────
    # Check if client_secrets.json exists for YouTube upload
    secrets_path = getattr(config, "YOUTUBE_CLIENT_SECRETS", "client_secrets.json")
    
    if not os.path.exists(secrets_path):
        log("=" * 55)
        log("WARNING: 'client_secrets.json' is missing.")
        log("Your video has been generated successfully and saved to:")
        log(f"  {video_path}")
        log("To enable automated YouTube uploads, please download your 'client_secrets.json'")
        log("from the Google Cloud Console and place it in this folder.")
        log("=" * 55)
        results = {"youtube": "skipped (no client_secrets.json)"}
    else:
        try:
            results = p5.upload_all(video_path, script, topic)
        except Exception as e:
            log(f"YouTube Upload Failed: {e}")
            log("Your video is saved locally at:")
            log(f"  {video_path}")
            results = {"youtube": f"failed — {e}"}

    # ── Summary ───────────────────────────────────────────
    elapsed = (datetime.datetime.now() - start).seconds // 60
    log("=" * 55)
    log(f"  PIPELINE COMPLETE in {elapsed} minutes")
    log(f"  Video Path : {video_path}")
    log(f"  YouTube    : {results.get('youtube', 'not uploaded')}")
    log(f"  Rumble     : {results.get('rumble',  'not configured')}")
    log("=" * 55)

    return results


def upload_audio_to_shotstack(local_path: str) -> str:
    """
    Upload audio file to Shotstack Ingest API.
    Returns public URL for use in timeline.
    """
    import requests
    import time
    from logger import log
    
    url = f"https://api.shotstack.io/ingest/{config.SHOTSTACK_ENV}/upload"
    headers = {
        "Accept": "application/json",
        "x-api-key": config.SHOTSTACK_API_KEY
    }
    
    log(f"Requesting Shotstack Ingest signed URL from {url}...")
    resp = requests.post(url, headers=headers, timeout=30)
    if resp.status_code not in (200, 201):
        log(f"Failed to get signed URL: {resp.status_code} — {resp.text}")
        raise Exception("Failed to get signed upload URL")
        
    res_json = resp.json()
    response_data = res_json.get("response", res_json)
    data_obj = response_data.get("data", response_data)
    source_id = data_obj.get("id")
    attributes = data_obj.get("attributes", {})
    signed_url = attributes.get("url", "")
    
    if not signed_url:
        log(f"Signed URL not found in response: {res_json}")
        raise Exception("Could not find signed upload URL in response")

    log(f"Uploading file raw binary to signed URL (ID: {source_id})...")
    with open(local_path, "rb") as f:
        put_resp = requests.put(signed_url, data=f, timeout=120)
        
    if put_resp.status_code != 200:
        log(f"PUT upload failed: {put_resp.status_code} — {put_resp.text}")
        raise Exception("PUT upload to signed URL failed")
        
    status_url = f"https://api.shotstack.io/ingest/{config.SHOTSTACK_ENV}/sources/{source_id}"
    log(f"Waiting for Shotstack Ingest to process source {source_id}...")
    
    for _ in range(30):  # max 5 minutes
        status_resp = requests.get(status_url, headers=headers, timeout=15)
        if status_resp.status_code == 200:
            status_json = status_resp.json()
            log(f"DEBUG Ingest status JSON: {status_json}")
            status_data = status_json.get("response", status_json)
            # handle nested data object if present
            status_data = status_data.get("data", status_data)
            attributes = status_data.get("attributes", status_data)
            
            status = attributes.get("status", "")
            if status == "ready":
                public_url = attributes.get("source", attributes.get("url", ""))
                log(f"Shotstack Ingest complete! Public URL: {public_url}")
                return public_url
            elif status == "failed":
                log(f"Shotstack Ingest failed: {status_json}")
                raise Exception("Ingest processing failed")
            else:
                log(f"  Status: {status} — waiting 10s...")
                time.sleep(10)
        else:
            log(f"Failed to poll status: {status_resp.status_code} — {status_resp.text}")
            time.sleep(10)
            
    raise TimeoutError("Ingest processing timed out")


if __name__ == "__main__":
    run_pipeline()
