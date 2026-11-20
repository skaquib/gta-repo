"""
main.py — Full Pipeline Orchestrator
Runs all 5 phases in sequence for one video.
Call directly: python main.py
Or let scheduler.py call it weekly.
"""

import sys
import json
import datetime
from logger import log

import phase1_research  as p1
import phase2_script    as p2
import phase3_voiceover as p3
import phase4_assembly  as p4
import phase5_upload    as p5


def run_pipeline():
    start = datetime.datetime.now()
    log("=" * 55)
    log("  YT AUTOMATION PIPELINE — STARTING")
    log("=" * 55)

    # ── Phase 1: Research ─────────────────────────────────
    topics = p1.research_topics()
    topic  = p1.pick_best_topic(topics)
    topic_id = topic["id"]

    # ── Phase 2: Script + Localise ────────────────────────
    script = p2.generate_script(topic)
    script = p2.localise_script(script)
    script_path = p2.save_script(script, topic_id)
    log(f"Script saved: {script_path}")

    # ── Phase 3: Voiceover ────────────────────────────────
    audio_map = p3.generate_all_voiceovers(script, topic_id)

    # Stitch English as primary track
    en_files = audio_map.get("en", [])
    if not en_files:
        log("ERROR: No English audio generated. Aborting.")
        sys.exit(1)

    en_audio_path = p3.stitch_audio(en_files, "en", topic_id)

    # ── Phase 4: Video Assembly ───────────────────────────
    # NOTE: Shotstack requires audio hosted at a public URL.
    # For local dev, upload en_audio_path to S3/Cloudflare R2 first,
    # then paste the public URL below.
    # For fully automated setup, use the Shotstack hosted assets API.
    audio_public_url = upload_audio_to_shotstack(en_audio_path)

    render_id  = p4.submit_render(script, audio_public_url, topic_id)
    video_url  = p4.poll_render(render_id)
    video_path = p4.download_video(video_url, topic_id, "en")

    # ── Phase 5: Upload ───────────────────────────────────
    results = p5.upload_all(video_path, script, topic)

    # ── Summary ───────────────────────────────────────────
    elapsed = (datetime.datetime.now() - start).seconds // 60
    log("=" * 55)
    log(f"  PIPELINE COMPLETE in {elapsed} minutes")
    log(f"  YouTube : {results.get('youtube', 'not uploaded')}")
    log(f"  Rumble  : {results.get('rumble',  'not configured')}")
    log("=" * 55)

    return results


def upload_audio_to_shotstack(local_path: str) -> str:
    """
    Upload audio file to Shotstack Ingest API.
    Returns public URL for use in timeline.
    """
    import requests
    import time
    import config
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
    run_pipeline()
