"""
social_cross_poster.py
========================
Cross-platform repurposing of the same rendered vertical MP4 that already
goes to YouTube — generalizes the upload_to_rumble() pattern in
phase5_upload.py to TikTok and Instagram Reels. Cross-posting multiplies
reach per unit of production cost, since it's the same file.

Both are off by default and only attempt a real post once you configure
their credentials -- otherwise they log why they were skipped and return "",
exactly like upload_to_rumble() does when RUMBLE_API_KEY is unset. Gated by
config.assert_safe_pipeline() upstream (see phase5_upload.upload_all): never
call these with anything other than the same safe, already-uploaded MP4.

TikTok (Content Posting API v2, FILE_UPLOAD source — needs a TikTok developer
app with the video.publish scope; unaudited apps can only post to private/
draft, see TikTok's docs for audit requirements):
  TIKTOK_ACCESS_TOKEN

Instagram (Meta Graph API, Reels publishing — needs a Facebook Developer app,
an Instagram professional account linked to a Facebook Page, and the video
hosted at a public URL since the API pulls from a URL rather than accepting
a raw file upload):
  INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_ACCOUNT_ID
"""

import os
import time
import requests

import config
from logger import log


def upload_to_tiktok(video_path: str, script: dict, topic: dict) -> str:
    """Post to TikTok via the Content Posting API v2 (FILE_UPLOAD source).
    Returns the publish_id, or "" if not configured/failed."""
    access_token = getattr(config, "TIKTOK_ACCESS_TOKEN", "")
    if not access_token:
        log("Cross-post: TIKTOK_ACCESS_TOKEN not set — skipping TikTok.")
        return ""

    title = (script.get("video_title") or script.get("title") or topic.get("title", ""))[:150]
    video_size = os.path.getsize(video_path)
    chunk_size = video_size  # single chunk for typical Shorts-length files
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

    init_body = {
        "post_info": {
            "title": title,
            "privacy_level": "SELF_ONLY",  # flip to PUBLIC_TO_EVERYONE once your app is audited
            "disable_duet": False,
            "disable_comment": False,
            "disable_stitch": False,
        },
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": video_size,
            "chunk_size": chunk_size,
            "total_chunk_count": 1,
        },
    }

    try:
        log("Cross-post: Initializing TikTok upload...")
        init_resp = requests.post(
            "https://open.tiktokapis.com/v2/post/publish/video/init/",
            headers=headers, json=init_body, timeout=30,
        )
        init_resp.raise_for_status()
        init_data = init_resp.json().get("data", {})
        publish_id = init_data.get("publish_id", "")
        upload_url = init_data.get("upload_url", "")
        if not upload_url:
            log(f"Cross-post: TikTok init failed: {init_resp.text[:300]}")
            return ""

        with open(video_path, "rb") as f:
            video_bytes = f.read()
        put_headers = {
            "Content-Range": f"bytes 0-{video_size - 1}/{video_size}",
            "Content-Type": "video/mp4",
        }
        put_resp = requests.put(upload_url, headers=put_headers, data=video_bytes, timeout=300)
        if put_resp.status_code not in (200, 201):
            log(f"Cross-post: TikTok video upload failed {put_resp.status_code}: {put_resp.text[:300]}")
            return ""

        log(f"Cross-post: TikTok upload complete (publish_id={publish_id}, privacy=SELF_ONLY until app audit)")
        return publish_id
    except Exception as e:
        log(f"Cross-post: TikTok upload error: {e}")
        return ""


def upload_to_instagram(video_path: str, script: dict, topic: dict, public_video_url: str = "") -> str:
    """Post to Instagram as a Reel via the Meta Graph API. Instagram's API
    pulls the video from a public URL rather than accepting a raw file
    upload, so `public_video_url` (the same file hosted somewhere reachable)
    must be provided. Returns the published media ID, or "" if not
    configured/failed."""
    access_token = getattr(config, "INSTAGRAM_ACCESS_TOKEN", "")
    account_id = getattr(config, "INSTAGRAM_ACCOUNT_ID", "")
    if not access_token or not account_id:
        log("Cross-post: INSTAGRAM_ACCESS_TOKEN/INSTAGRAM_ACCOUNT_ID not set — skipping Instagram.")
        return ""
    if not public_video_url:
        log("Cross-post: Instagram requires a public_video_url (the API pulls from a "
            "hosted URL, not a file upload) — skipping.")
        return ""

    caption = (script.get("seo_description") or script.get("title") or topic.get("title", ""))[:2200]
    graph_url = f"https://graph.facebook.com/v19.0/{account_id}/media"

    try:
        log("Cross-post: Creating Instagram Reels media container...")
        create_resp = requests.post(graph_url, data={
            "media_type": "REELS",
            "video_url": public_video_url,
            "caption": caption,
            "access_token": access_token,
        }, timeout=30)
        create_resp.raise_for_status()
        container_id = create_resp.json().get("id", "")
        if not container_id:
            log(f"Cross-post: Instagram container creation failed: {create_resp.text[:300]}")
            return ""

        status_url = f"https://graph.facebook.com/v19.0/{container_id}"
        for _ in range(30):  # up to ~5 minutes
            status_resp = requests.get(status_url, params={
                "fields": "status_code", "access_token": access_token,
            }, timeout=15)
            status_code = status_resp.json().get("status_code", "")
            if status_code == "FINISHED":
                break
            if status_code == "ERROR":
                log(f"Cross-post: Instagram container processing failed: {status_resp.text[:300]}")
                return ""
            time.sleep(10)
        else:
            log("Cross-post: Instagram container processing timed out")
            return ""

        publish_resp = requests.post(
            f"https://graph.facebook.com/v19.0/{account_id}/media_publish",
            data={"creation_id": container_id, "access_token": access_token},
            timeout=30,
        )
        publish_resp.raise_for_status()
        media_id = publish_resp.json().get("id", "")
        log(f"Cross-post: Instagram Reel published (media_id={media_id})")
        return media_id
    except Exception as e:
        log(f"Cross-post: Instagram upload error: {e}")
        return ""
