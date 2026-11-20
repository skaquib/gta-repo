"""
git_asset_library.py
====================
Curated royalty-free music, SFX, and stock video from public GitHub repos
and verified CC0/Pixabay sources. Local cache + license attribution tracking.
"""

import json
import os
import random
import re
import requests
import config
from logger import log

MANIFEST_PATH = os.path.join(os.path.dirname(__file__), "git_asset_manifest.json")
CACHE_DIR = os.path.join(config.OUTPUT_DIR, "git_assets")
ATTRIBUTION_FILE = os.path.join(CACHE_DIR, "attributions.json")


def _load_manifest() -> dict:
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        return json.load(f)


def _safe_name(asset_id: str, ext: str) -> str:
    clean = re.sub(r"[^\w\-]", "_", asset_id)
    return f"{clean}.{ext}"


def download_asset(url: str, asset_id: str, category: str, min_bytes: int = 5000) -> str:
    """Download asset to local cache. Returns local path."""
    ext = url.split("?")[0].split(".")[-1].lower()
    if ext not in ("mp3", "mp4", "wav", "ogg", "webm"):
        ext = "mp3" if category in ("music", "sfx") else "mp4"

    cat_dir = os.path.join(CACHE_DIR, category)
    os.makedirs(cat_dir, exist_ok=True)
    path = os.path.join(cat_dir, _safe_name(asset_id, ext))

    if os.path.exists(path) and os.path.getsize(path) >= min_bytes:
        return path

    log(f"Git assets: downloading {asset_id} ({category})...")
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=120, stream=True)
    r.raise_for_status()
    with open(path, "wb") as f:
        for chunk in r.iter_content(65536):
            f.write(chunk)

    if os.path.getsize(path) < min_bytes:
        os.remove(path)
        raise Exception(f"Download too small for {asset_id}")

    log(f"Git assets: cached {path} ({os.path.getsize(path) / 1e6:.1f}MB)")
    return path


def _record_attribution(assets: list):
    os.makedirs(CACHE_DIR, exist_ok=True)
    existing = []
    if os.path.exists(ATTRIBUTION_FILE):
        try:
            with open(ATTRIBUTION_FILE, encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = []

    seen = {a.get("id") for a in existing}
    for a in assets:
        if a.get("id") not in seen:
            existing.append({
                "id": a["id"],
                "license": a.get("license", ""),
                "attribution": a.get("attribution", ""),
                "url": a.get("url", ""),
            })

    with open(ATTRIBUTION_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)


def pick_music(tags: list = None) -> tuple:
    """Return (local_path, asset_meta) for background music."""
    manifest = _load_manifest()
    pool = manifest.get("music", [])
    if tags:
        tagged = [a for a in pool if any(t in a.get("tags", []) for t in tags)]
        if tagged:
            pool = tagged
    asset = random.choice(pool)
    path = download_asset(asset["url"], asset["id"], "music", min_bytes=10000)
    _record_attribution([asset])
    return path, asset


def pick_sfx(tags: list = None, count: int = 1) -> list:
    """Return list of (local_path, asset_meta) for sound effects."""
    manifest = _load_manifest()
    pool = [a for a in manifest.get("sfx", []) if not a.get("optional")]
    if tags:
        tagged = [a for a in pool if any(t in a.get("tags", []) for t in tags)]
        if tagged:
            pool = tagged
    chosen = random.sample(pool, min(count, len(pool)))
    results = []
    for asset in chosen:
        try:
            path = download_asset(asset["url"], asset["id"], "sfx", min_bytes=1000)
            results.append((path, asset))
        except Exception as e:
            log(f"SFX skip {asset['id']}: {e}")
    _record_attribution(chosen)
    return results


def _score_clip(asset: dict, keywords: list) -> int:
    tags = " ".join(asset.get("tags", [])).lower()
    return sum(1 for kw in keywords if kw.lower() in tags)


def pick_video_clips(script: dict, count: int = 3) -> list:
    """
    Pick topic-matched royalty-free video clips.
    Returns list of local file paths.
    """
    manifest = _load_manifest()
    pool = manifest.get("video_clips", [])

    text = " ".join([
        script.get("hook", ""),
        script.get("body", ""),
        " ".join(script.get("queries", [])),
        script.get("yt_query", ""),
    ]).lower()

    keywords = []
    for word in re.findall(r"[a-z]{4,}", text):
        keywords.append(word)
    for q in script.get("queries", []):
        keywords.extend(q.lower().split())

    scored = sorted(pool, key=lambda a: _score_clip(a, keywords), reverse=True)
    top = scored[: max(count * 2, count)]
    random.shuffle(top)
    selected = top[:count]

    paths = []
    used_assets = []
    for asset in selected:
        try:
            path = download_asset(asset["url"], asset["id"], "video", min_bytes=50000)
            paths.append(path)
            used_assets.append(asset)
        except Exception as e:
            log(f"Video clip skip {asset['id']}: {e}")

    if used_assets:
        _record_attribution(used_assets)

    return paths


def get_attribution_text() -> str:
    """Build description footer with all used asset credits."""
    if not os.path.exists(ATTRIBUTION_FILE):
        return ""
    try:
        with open(ATTRIBUTION_FILE, encoding="utf-8") as f:
            items = json.load(f)
    except Exception:
        return ""

    lines = ["\n--- Royalty-Free Assets ---"]
    for a in items[-20:]:
        attr = a.get("attribution") or a.get("id", "")
        lic = a.get("license", "")
        lines.append(f"• {attr} ({lic})")
    return "\n".join(lines)


def get_pixabay_fallback_queries(script: dict) -> list:
    manifest = _load_manifest()
    fb = manifest.get("pixabay_search_fallback", {})
    text = script.get("hook", "").lower()
    if any(w in text for w in ("aura", "composure", "cold", "manager", "goalkeeper")):
        return fb.get("aura", fb.get("football", []))
    if any(w in text for w in ("stat", "record", "percent", "goal")):
        return fb.get("stats", fb.get("football", []))
    return script.get("queries") or fb.get("football", [])
