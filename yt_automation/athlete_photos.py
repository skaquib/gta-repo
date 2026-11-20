"""
athlete_photos.py
==================
Fetches real, legally-reusable photos of named athletes/managers from
Wikimedia Commons, for use instead of generic anonymous stock footage
when a script names a specific real person.

Direct feedback 2026-08-25: "the video you show the name of player
should show there face" -- free stock libraries (Pixabay/Pexels) have
no rights to real broadcast footage of named professional athletes;
that footage is owned by leagues/broadcasters. Wikimedia Commons hosts
genuine press/editorial photos of named athletes under Creative Commons
licenses that DO permit reuse (including commercial), with attribution.
Verified live 2026-08-25: real, high-res Jannik Sinner photos exist
there under CC BY-SA 4.0.

Only licenses that permit commercial reuse with attribution are used
(CC0, public domain, CC BY, CC BY-SA). "Non-commercial" and
"no-derivatives" licenses are excluded -- a monetized channel applying
a Ken Burns pan/zoom is a derivative commercial use those licenses
don't cover.
"""
import os
import re
import requests
from urllib.parse import urlparse

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
HEADERS = {"User-Agent": "FramedFactsBot/1.0 (sports facts YouTube Shorts channel; contact via channel)"}

_SAFE_LICENSE_PREFIXES = (
    "cc0", "public domain", "pd", "cc by", "cc by-sa",
)


def _license_is_safe(license_short_name: str) -> bool:
    name = (license_short_name or "").strip().lower()
    return any(name.startswith(p) for p in _SAFE_LICENSE_PREFIXES)


def find_athlete_photo(name: str, out_dir: str) -> dict:
    """Search Wikimedia Commons for a real, safely-licensed photo of
    `name`. Returns {"path", "attribution", "source_url", "license"} on
    success, or None if nothing safely-licensed and large enough was
    found. Never raises -- callers should treat None as "fall back to
    generic stock footage", not as an error."""
    try:
        r = requests.get(COMMONS_API, params={
            "action": "query", "list": "search", "srsearch": name,
            "srnamespace": 6, "format": "json", "srlimit": 8,
        }, headers=HEADERS, timeout=15)
        r.raise_for_status()
        titles = [x["title"] for x in r.json().get("query", {}).get("search", [])]
    except Exception:
        return None

    for title in titles:
        try:
            r2 = requests.get(COMMONS_API, params={
                "action": "query", "titles": title, "prop": "imageinfo",
                "iiprop": "url|extmetadata|size", "format": "json",
            }, headers=HEADERS, timeout=15)
            r2.raise_for_status()
            pages = r2.json()["query"]["pages"]
            page = next(iter(pages.values()))
            info = page.get("imageinfo", [{}])[0]
            meta = info.get("extmetadata", {})
            license_name = meta.get("LicenseShortName", {}).get("value", "")
            width = info.get("width", 0) or 0
            height = info.get("height", 0) or 0

            if not _license_is_safe(license_name):
                continue
            if width < 400 or height < 400:
                continue  # too small to look good on a 1080x1920 frame

            url = info.get("url")
            # Real Commons URLs carry tracking query params after the
            # extension (...jpg?utm_source=...), so check the URL PATH,
            # not the raw string -- an .endswith() on the full URL always
            # fails and silently rejects every real photo.
            url_path = urlparse(url or "").path
            if not url or not url_path.lower().endswith((".jpg", ".jpeg", ".png")):
                continue  # skip svg/other non-photo formats

            os.makedirs(out_dir, exist_ok=True)
            fname = re.sub(r"[^A-Za-z0-9._-]", "_", title)[:80]
            if not fname.lower().endswith((".jpg", ".jpeg", ".png")):
                fname += ".jpg"
            fpath = os.path.join(out_dir, fname)

            img_r = requests.get(url, headers=HEADERS, timeout=30)
            img_r.raise_for_status()
            with open(fpath, "wb") as f:
                f.write(img_r.content)

            artist_html = meta.get("Artist", {}).get("value", "Unknown")
            artist = re.sub(r"<[^>]+>", "", artist_html).strip() or "Unknown"
            attribution = f"Photo of {name}: {artist}, {license_name}, via Wikimedia Commons"

            return {"path": fpath, "attribution": attribution,
                    "source_url": url, "license": license_name}
        except Exception:
            continue

    return None
