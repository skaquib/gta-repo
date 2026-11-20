"""
publish_optimized.py — one publish path that applies EVERY optimization.

Built 2026-09-11 after auditing the channel against a YouTube-growth guide.
The audit found we had been doing the hard part (daily uploads, verified
research, working pipeline) while skipping the cheap parts that drive clicks:

    designed thumbnails ....... 1 of 110 videos
    playlists ................. 0 of 110
    end screens / cards ....... 0
    description length ........ avg 289 chars
    next-video suggestion ..... none
    Short -> long-form link ... none

This routine closes all of the above that the API can reach, in order, so no
upload can silently skip one again.

API LIMITATION, stated honestly: YouTube Data API v3 has NO endpoint for end
screens or info cards ("i" button). There is no endScreens or cards resource.
Those two must be set in YouTube Studio by hand. Everything else here is
automated, and print_manual_steps() prints the exact clicks needed.
"""
import os
import json
import config
from logger import log

PLAYLISTS_FILE = "output/playlists.json"


def _playlists():
    if os.path.exists(PLAYLISTS_FILE):
        return json.load(open(PLAYLISTS_FILE))
    return {}


def build_description(script: dict, next_video_id: str = None,
                      next_video_title: str = None,
                      related_id: str = None, related_title: str = None,
                      sources: list = None, playlist_id: str = None) -> str:
    """Rich description. The audit found ours averaged 289 characters; a
    description is free ranking context and the only place a Short can carry
    a real 'watch next' link."""
    parts = [script.get("seo_description", "").strip()]

    if next_video_id:
        parts.append(
            f"\nWATCH NEXT -- {next_video_title or 'the full story'}:\n"
            f"https://www.youtube.com/watch?v={next_video_id}")

    if related_id:
        parts.append(
            f"\nFULL DOCUMENTARY -- {related_title or ''}:\n"
            f"https://www.youtube.com/watch?v={related_id}")

    if playlist_id:
        parts.append(
            f"\nMORE IN THIS SERIES:\n"
            f"https://www.youtube.com/playlist?list={playlist_id}")

    if sources:
        parts.append("\nSOURCES:\n" + "\n".join(f"- {s}" for s in sources))

    parts.append(
        "\nEvery fact on this channel is checked against primary sources "
        "before it is published. If we get something wrong, tell us in the "
        "comments and we will correct it.")

    tags = script.get("tags", [])
    if tags:
        parts.append("\n" + " ".join(f"#{t.replace(' ', '')}" for t in tags[:12]))

    return "\n".join(p for p in parts if p).strip()[:5000]


def apply_all(video_id: str, script: dict, video_path: str,
              thumb_line1: str, thumb_line2: str = "",
              playlist_name: str = None, next_video_id: str = None,
              next_video_title: str = None, related_id: str = None,
              related_title: str = None, sources: list = None,
              make_public: bool = True) -> dict:
    """Apply thumbnail, rich description, playlist, public status, comment."""
    import phase5_upload as p5
    from phase5_upload import get_youtube_client
    import make_thumbnail

    yt = get_youtube_client()
    done = {}

    # 1. custom thumbnail (audit: 1 of 110 videos had one)
    try:
        thumb = f"output/thumbnails/{video_id}.jpg"
        make_thumbnail.make(video_path, thumb, thumb_line1, thumb_line2)
        done["thumbnail"] = p5.upload_thumbnail(video_id, thumb)
    except Exception as e:
        log(f"thumbnail failed: {e}")
        done["thumbnail"] = False

    # 2. rich description + playlist link
    pls = _playlists()
    pid = pls.get(playlist_name) if playlist_name else None
    try:
        cur = yt.videos().list(part="snippet", id=video_id).execute()["items"][0]["snippet"]
        cur["description"] = build_description(
            script, next_video_id, next_video_title,
            related_id, related_title, sources, pid)
        yt.videos().update(part="snippet", body={"id": video_id, "snippet": cur}).execute()
        done["description_chars"] = len(cur["description"])
    except Exception as e:
        log(f"description failed: {e}")
        done["description_chars"] = 0

    # 3. add to series playlist (audit: 0 playlists existed)
    if pid:
        try:
            yt.playlistItems().insert(part="snippet", body={"snippet": {
                "playlistId": pid,
                "resourceId": {"kind": "youtube#video", "videoId": video_id}}}).execute()
            done["playlist"] = playlist_name
        except Exception as e:
            log(f"playlist failed: {e}")

    # 4. public
    if make_public:
        try:
            done["status"] = p5.push_video_public(video_id)["privacyStatus"]
        except Exception as e:
            log(f"publish failed: {e}")

    # 5. engagement comment
    try:
        q = p5._extract_debate_question(script)
        done["comment"] = bool(p5.post_engagement_comment(video_id, q))
    except Exception as e:
        log(f"comment failed: {e}")

    return done


def print_manual_steps(video_id: str, suggest_id: str = None):
    """The two things the API genuinely cannot do."""
    url = f"https://studio.youtube.com/video/{video_id}/editor"
    print("\n" + "=" * 62)
    print("MANUAL STEPS -- YouTube Data API v3 has no endpoint for these")
    print("=" * 62)
    print(f"Open: {url}")
    print()
    print('1. END SCREEN  (last 5-20s, drives the "next video")')
    print("   Editor -> End screen -> Video -> Best for viewer")
    if suggest_id:
        print(f"   or pick specifically: {suggest_id}")
    print("   Add a Subscribe element next to it.")
    print()
    print('2. CARDS  (the "i" button, mid-video)')
    print("   Editor -> Cards -> Video -> choose the related video")
    print("   Place around 30-50% through the runtime.")
    print()
    print("NOTE: end screens require 25s+ of runtime, so they apply to the")
    print("long-form documentary. Shorts do not support end screens/cards.")
    print("=" * 62 + "\n")
