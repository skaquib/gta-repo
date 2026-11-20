"""
Phase 5 — YouTube Upload
Uses YouTube Data API v3 with OAuth2 to upload the final video.
Also uploads to Rumble if API key is configured.
Handles the 2026 'Altered Content' label requirement for AI content.
"""

import os
import json
import pickle
import datetime
import requests
import config
from logger import log

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube",
          "https://www.googleapis.com/auth/youtube.force-ssl",  # required for captions.insert
          "https://www.googleapis.com/auth/yt-analytics.readonly"]  # CTR/AVD reporting
TOKEN_FILE = "youtube_token.pickle"


def get_credentials():
    """Authenticate and return cached OAuth2 credentials, shared by the
    YouTube Data API client (get_youtube_client) and the YouTube Analytics
    API client (youtube_analytics_client.py). If youtube_token.pickle was
    cached before yt-analytics.readonly was added to SCOPES, delete it once
    so the next auth run re-prompts for the new scope's consent."""
    creds = None

    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)

    # Headless hosts (cloud sessions, CI) can't run the browser login below,
    # so accept a refresh token from the environment instead of a pickle.
    env_refresh = os.getenv("YT_REFRESH_TOKEN")
    if (not creds or not creds.valid) and env_refresh:
        creds = Credentials(
            token=None,
            refresh_token=env_refresh,
            client_id=os.getenv("YT_CLIENT_ID"),
            client_secret=os.getenv("YT_CLIENT_SECRET"),
            token_uri="https://oauth2.googleapis.com/token",
        )
        creds.refresh(Request())
        return creds

    if not creds or not creds.valid:
        refreshed = False
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                refreshed = True
            except Exception as e:
                # Refresh token itself rejected (commonly: OAuth consent screen
                # is in "Testing" mode, where Google auto-expires refresh
                # tokens after 7 days) -- fall through to a fresh interactive
                # login instead of failing every upload until someone notices.
                log(f"Token refresh failed ({e}) -- re-authenticating interactively")

        if not refreshed:
            flow = InstalledAppFlow.from_client_secrets_file(
                config.YOUTUBE_CLIENT_SECRETS, SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)

    return creds


def get_youtube_client():
    """Authenticate and return a YouTube Data API client. Caches token locally."""
    return build("youtube", "v3", credentials=get_credentials())


def _to_rfc3339(dt: datetime.datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")



# Two-slot daily cadence, 12:30pm and 6:00pm IST. Locked 2026-09-10 from a
# full-channel analysis (110 uploads, 2026-03-25..2026-09-09). Supersedes the
# 9am/7pm pair set 2026-08-21.
#
# WHY THESE TIMES -- the three facts that decide it:
#
# 1. The day-1 burst is the whole game. Pulled per-day view curves for the
#    three most recent >100-view videos: THREE YELLOWS 322/322 views on day 1
#    (100%), Arsenal/Jesus 532 of 540 (99%), Euro-1968 coin flip 379 of 397
#    (95%, then 8/10/0/3 over the next four days). These Shorts get ONE feed
#    push and then flatline. So the publish instant places that burst -- this
#    is not the "Shorts resurface for weeks" case where timing is moot.
#
# 2. The audience is India-dominant, so IST is the right clock. Viewer
#    geography: IN 47.8% (28d) / 59.4% (90d). Nothing else is close -- JP
#    10.4%, US 9.3%, ID 8.6%, PH 5.1%. There is no Western cluster worth
#    optimizing a slot for. And 95.2% of all traffic is the SHORTS feed
#    (SUBSCRIBER 0.1%, NOTIFICATION 0.2%), so the slot is about catching the
#    Indian swipe-feed scroll, not about pinging subscribers.
#
# 3. 18:00 is where our winners actually cluster. Four of the eight best
#    post-World-Cup videos published between 18:00 and 19:30 IST (marathon
#    1687v @18:04, Djokovic/Sabalenka 1201v @18:01, golf dimples 927v @19:30,
#    Shelton upset 792v @19:00). Moving 19:00 -> 18:00 puts the video in the
#    feed at the START of the Indian evening ramp, giving it ~2h to gather the
#    early-signal impressions that decide whether it scales INTO the 6-9pm
#    peak that Studio's audience tab reports, rather than landing mid-peak.
#
# The 9am slot is dropped because it never actually fired: zero uploads landed
# in the 08:00-10:00 band in the whole 2-slot era (2026-08-21 onward). Midday
# replaces it on evidence -- the 11:00-15:00 IST block is the best-performing
# non-evening band in the post-WC window (n=9, median 328 vs the 05-11 morning
# band's n=5). 12:30 also keeps ~5.5h of spacing from the 18:00 slot, well
# clear of the same-hour clustering that MAX_PER_DAY exists to prevent.
#
# HONEST CAVEAT, do not over-trust this: hour is a WEAK lever next to topic.
# Across the 48 post-WC uploads the mean within-block view stdev is 350 while
# the spread between hour-block medians is only 230 -- i.e. which topic you
# pick moves views more than which hour you post it. The 18:00-22:00 band
# shows the worst median (128) purely because it holds the most attempts and
# therefore the most duds; its mean (322) is mid-pack and its max is the
# channel record. These slots are a small, free optimization. They are not a
# fix for a weak hook.
_DAILY_SLOTS_IST = [(12, 30), (18, 0)]
_IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))


def _next_standing_slot(after: datetime.datetime) -> datetime.datetime:
    """Earliest of the standing daily slots (9am/7pm IST) strictly after
    `after`. Shared by _compute_preferred_publish_dt() (next slot after
    now) and reserve_publish_slot()'s same-day-cap advancement (next slot
    after a candidate that turned out to be full)."""
    after_ist = after.astimezone(_IST)
    for hour, minute in _DAILY_SLOTS_IST:
        candidate = after_ist.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if candidate > after_ist:
            return candidate.astimezone(datetime.timezone.utc)
    tomorrow = after_ist + datetime.timedelta(days=1)
    hour, minute = _DAILY_SLOTS_IST[0]
    candidate = tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)
    return candidate.astimezone(datetime.timezone.utc)


def _compute_preferred_publish_dt() -> datetime.datetime:
    """Preferred publish moment before the same-day guard adjusts it: if a
    real match is kicking off soon (match_calendar.py), publish shortly after
    full-time so the content rides the freshness/news-cycle window;
    otherwise the next standing daily slot (9am or 7pm IST)."""
    now = datetime.datetime.now(datetime.timezone.utc)
    try:
        import match_calendar
        upcoming = match_calendar.next_match_window(hours_ahead=6.0)
        if upcoming:
            kickoff = match_calendar.parse_kickoff(upcoming[0])
            if kickoff:
                publish_at = kickoff + datetime.timedelta(hours=2)  # after full-time
                if publish_at > now:
                    return publish_at
    except Exception as e:
        log(f"Phase 5: match calendar unavailable for scheduling ({e})")

    return _next_standing_slot(now)


def _compute_publish_at() -> str:
    """Back-compat string wrapper around _compute_preferred_publish_dt()."""
    return _to_rfc3339(_compute_preferred_publish_dt())


# ── Same-day upload guard ────────────────────────────────────────────────
# A cluster of same-day uploads (12 in one day on 2026-07-02, including 4
# near-duplicate videos within an hour) triggered this channel's algorithmic
# suppression. This guard makes it structurally impossible for this
# pipeline to publish more than MAX_PER_DAY videos live on the same
# calendar day, regardless of SCHEDULE_MODE -- immediate uploads get
# silently upgraded to the next free standing slot if the day is already
# at cap. Raised from 1/day to 2/day on 2026-08-21 (direct instruction) --
# two uploads 10 hours apart is a different pattern from the clustered
# same-hour uploads that caused the original incident, so this stays a
# real cap, not a removal of the guard.
MAX_PER_DAY = 2
PUBLISH_LEDGER_FILE = os.path.join("output", "publish_ledger.json")


def _load_publish_ledger() -> set:
    if os.path.exists(PUBLISH_LEDGER_FILE):
        try:
            with open(PUBLISH_LEDGER_FILE, encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            pass
    return set()


def _save_publish_ledger(dates: set):
    os.makedirs(os.path.dirname(PUBLISH_LEDGER_FILE), exist_ok=True)
    with open(PUBLISH_LEDGER_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(dates), f, indent=2)


def _live_publish_dates() -> list:
    """Real check against the channel's actual public uploads -- catches
    collisions caused by anything outside this pipeline (e.g. a manual
    Studio upload), which a local ledger alone can't see. One entry per
    live video's publish date, so a day with 2 real uploads counts twice
    against MAX_PER_DAY."""
    try:
        import viral_analytics as va
        videos = va.fetch_recent_video_stats(max_results=20)
        return [v["published_at"][:10] for v in videos if v.get("published_at")]
    except Exception as e:
        log(f"Phase 5: same-day guard could not check live channel state ({e})")
        return []


def reserve_publish_slot(preferred: datetime.datetime = None) -> datetime.datetime:
    """Find the earliest standing slot (9am/7pm IST) >= preferred whose
    calendar day has fewer than MAX_PER_DAY videos already live or
    claimed, reserve it in a local ledger, and return it. Ledger entries
    are full timestamps (a day's worth of old single-slot "YYYY-MM-DD"
    entries still count correctly -- both formats slice to the same
    10-char date for the per-day count)."""
    preferred = preferred or datetime.datetime.now(datetime.timezone.utc)
    ledger = _load_publish_ledger()
    live_dates = _live_publish_dates()

    now_s = _to_rfc3339(datetime.datetime.now(datetime.timezone.utc))

    def day_count(day_str: str) -> int:
        # A ledger slot already in the past has gone live, so it is also in
        # live_dates (public uploads). Adding both counted every pipeline
        # upload twice -- one real video filled the 2-per-day cap. Count
        # distinct videos: max(live, past ledger) absorbs search-index lag on
        # a just-published video, plus slots still scheduled for later.
        live = sum(1 for x in live_dates if x == day_str)
        past = sum(1 for x in ledger if x[:10] == day_str and x <= now_s)
        future = sum(1 for x in ledger if x[:10] == day_str and x > now_s)
        return max(live, past) + future

    candidate = preferred
    # Also skip a slot already claimed -- two Shorts reserved on the same day
    # used to both land on the same 07:00Z publishAt and compete head to head.
    while (day_count(candidate.strftime("%Y-%m-%d")) >= MAX_PER_DAY
           or _to_rfc3339(candidate) in ledger):
        candidate = _next_standing_slot(candidate)

    ledger.add(_to_rfc3339(candidate))
    _save_publish_ledger(ledger)

    if candidate != preferred:
        log(f"Phase 5: same-day guard adjusted publish slot from "
            f"{_to_rfc3339(preferred)} to {_to_rfc3339(candidate)} "
            f"(day already at the {MAX_PER_DAY}-video cap)")
    return candidate


def _check_title_not_duplicate(title: str):
    """Refuse to upload a title that exactly matches a video already on the
    channel. Two videos titled "Messi's Last World Cup Final Is Here" went
    live 6 days apart because nothing checked for repeated content -- the
    same-day guard only catches same-day clustering, not re-covering a
    story that was already published. Raises rather than silently skipping,
    since a caller producing a specific story needs to know it already ran."""
    try:
        import viral_analytics as va
        existing_titles = {v["title"].strip().lower() for v in va.fetch_recent_video_stats(max_results=50)}
    except Exception as e:
        log(f"Phase 5: duplicate-title check could not reach the channel ({e}) — proceeding")
        return
    if title.strip().lower() in existing_titles:
        raise ValueError(
            f"Refusing upload: a video titled {title!r} is already on the channel. "
            f"This exact story/script already ran -- write a new angle or title instead."
        )


def _extract_debate_question(script: dict) -> str:
    """Pull the provocative debate question out of the script's CTA, used
    both in the video description and as an auto-posted engagement comment."""
    raw_cta = script.get("cta", "")
    debate_q = raw_cta.split("—")[0].split("and subscribe")[0].split("subscribe")[0].strip()
    # Only add "?" when the CTA has no closing punctuation -- "...or Barça."
    # used to become "...or Barça.?" in the posted comment.
    if debate_q and debate_q[-1] not in ".?!" and len(debate_q) > 5:
        debate_q += "?"
    return debate_q


def upload_to_youtube(video_path: str, script: dict, topic: dict) -> tuple:
    """Upload video to YouTube. Returns (video_url, is_public_now) -- the
    latter tells the caller whether commentThreads().insert() is even
    possible yet (YouTube rejects public comment threads on a video that
    isn't public yet, which is what a same-day-guard-scheduled upload is)."""
    hold = os.path.join(os.path.dirname(os.path.abspath(__file__)), "POSTING_HOLD")
    if os.path.exists(hold):          # owner, 2026-11-19: make videos, post nothing until they say so
        raise RuntimeError("POSTING HOLD: the owner paused all uploads (see yt_automation/POSTING_HOLD).")
    log("Phase 5: Uploading to YouTube...")

    youtube = get_youtube_client()

    title = script.get("video_title", topic["title"])
    if (script.get("format") != "long" and getattr(config, "VIDEO_TYPE", "long") == "shorts"
            and "#shorts" not in title.lower()):
        title = f"{title[:90]} #shorts"

    _check_title_not_duplicate(title[:100])

    # Prepend provocative debate question to drive comment engagement
    debate_q = _extract_debate_question(script)

    description = script.get("seo_description", topic["subject"])
    if len(debate_q) > 5 and script.get("format") != "long":     # long-form: first lines are kept for search
        description = f"📌 COMMUNITY DEBATE: {debate_q}\n\n{description}"

    # Only the script's own topic tags. The channel name, region code ("IN") and
    # broad category ("Sports"/"Animals") used to be appended here; they tell
    # YouTube nothing about the video and kept tagging animal videos as sports.
    tags = list(dict.fromkeys(script.get("tags", ["animation", "facts", "education"])))

    # Spoken-audio/metadata language -- must match the actual narration so
    # YouTube surfaces the video to the right audience and (for Hindi) does
    # NOT offer to auto-dub it back into English over itself.
    content_lang = script.get("lang", "en")

    # A script can also declare AI-generated visuals directly (e.g. Gemini
    # image scenes) when VISUAL_STYLE is "footage" for the channel overall.
    has_altered = (getattr(config, "VISUAL_STYLE", "ai_animation") == "ai_animation"
                   or bool(script.get("ai_generated_visuals")))

    status = {
        "privacyStatus": config.UPLOAD_PRIVACY,
        "selfDeclaredMadeForKids": False,
        # The API field for YouTube's "altered or synthetic content" disclosure. (This used to be sent as
        # "hasAlteredContentLabel", which the API does not know and silently ignored.)
        "containsSyntheticMedia": has_altered,
    }

    # Same-day upload guard runs regardless of SCHEDULE_MODE: even an
    # "immediate" upload gets silently upgraded to a scheduled slot on the
    # next free day if today is already claimed (by this pipeline or by
    # anything else, per a live channel check).
    if script.get("publish_at"):
        # An exact release time the owner chose (RFC 3339, UTC): upload private, YouTube publishes it then.
        status["privacyStatus"] = "private"
        status["publishAt"] = script["publish_at"]
        log(f"Phase 5: Scheduled by the owner to publish at {status['publishAt']}")
    else:
        schedule_mode = getattr(config, "SCHEDULE_MODE", "immediate")
        preferred_dt = (_compute_preferred_publish_dt() if schedule_mode == "scheduled"
                         else datetime.datetime.now(datetime.timezone.utc))
        reserved_dt = reserve_publish_slot(preferred_dt)
        today_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

        if schedule_mode == "scheduled" or reserved_dt.strftime("%Y-%m-%d") != today_str:
            # publishAt only auto-transitions a video from private -> public at
            # the given time, so privacyStatus must be private at upload time
            # regardless of config.UPLOAD_PRIVACY.
            if status["privacyStatus"] != "private":
                log(f"Phase 5: scheduling requires privacyStatus=private "
                    f"at upload time (was {status['privacyStatus']}) — overriding.")
            status["privacyStatus"] = "private"
            status["publishAt"] = _to_rfc3339(reserved_dt)
            log(f"Phase 5: Scheduled to auto-publish at {status['publishAt']}")

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags[:30],
            "categoryId": str(script.get("category_id", getattr(config, "VIDEO_CATEGORY_ID", "27"))),
            "defaultLanguage": content_lang,
            # defaultAudioLanguage (the spoken-audio language) is what
            # automatic dubbing actually needs to know what to translate
            # *from* -- without it, YouTube shows "This video cannot be
            # automatically translated" regardless of channel eligibility.
            "defaultAudioLanguage": script.get("audio_lang", content_lang),
        },
        "status": status,
    }

    is_public_now = body["status"]["privacyStatus"] == "public"
    media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True, chunksize=1024*1024*5)

    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        upload_status, response = request.next_chunk()
        if upload_status:
            pct = int(upload_status.progress() * 100)
            log(f"  Upload progress: {pct}%")

    video_id = response["id"]
    url = f"https://www.youtube.com/watch?v={video_id}"
    log(f"Phase 5: YouTube upload complete → {url}")
    return url, is_public_now


def push_video_public(video_id: str) -> dict:
    """Flip an uploaded (private, or private+publishAt scheduled) video to
    public right now -- the manual "push" half of this channel's standing
    workaround for YouTube's publishAt being unreliable (confirmed multiple
    times: scheduled videos have gone live early/unpredictably regardless
    of the scheduled time).

    videos().update(part="status", ...) REPLACES the whole status object
    with whatever you send, it doesn't merge -- sending only
    {"privacyStatus": "public"} silently resets every other status field
    (embeddable, publicStatsViewable, etc.) to API defaults. Reproduced
    live 2026-08-30: a partial update flipped embeddable/publicStatsViewable
    to False as a side effect. This reads the current status first and
    only changes privacyStatus (dropping publishAt, which has no effect
    once actually public), so nothing else gets clobbered.
    """
    youtube = get_youtube_client()
    current = youtube.videos().list(part="status", id=video_id).execute()
    items = current.get("items", [])
    if not items:
        raise Exception(f"No video found for id {video_id}")
    status = items[0]["status"]
    status.pop("publishAt", None)
    status["privacyStatus"] = "public"
    resp = youtube.videos().update(part="status", body={"id": video_id, "status": status}).execute()
    log(f"Phase 5: {video_id} is now public — https://www.youtube.com/watch?v={video_id}")
    return resp["status"]


def post_engagement_comment(video_id: str, text: str) -> str:
    """Post a top-level comment (as the channel owner) on the video to seed
    engagement -- pinned comments and early replies are a proven, low-effort
    comment-count driver. Note: the YouTube Data API v3 has no public
    endpoint to pin a comment; pin it manually in YouTube Studio if desired,
    this only posts it. Returns the comment ID, or "" on failure/no text."""
    if not text:
        return ""

    log(f"Phase 5: Posting engagement comment on {video_id}...")
    youtube = get_youtube_client()
    body = {
        "snippet": {
            "videoId": video_id,
            "topLevelComment": {"snippet": {"textOriginal": text}},
        }
    }
    try:
        resp = youtube.commentThreads().insert(part="snippet", body=body).execute()
        comment_id = resp.get("id", "")
        log(f"Phase 5: Comment posted ({comment_id}) — pin it manually in Studio if desired")
        return comment_id
    except Exception as e:
        log(f"Phase 5: Comment post failed for {video_id}: {e}")
        return ""


def upload_thumbnail(video_id: str, thumb_path: str) -> bool:
    """Upload a custom thumbnail for a video. Returns True on success."""
    if not thumb_path or not os.path.exists(thumb_path):
        log(f"Phase 5: No thumbnail to upload for {video_id}")
        return False

    log(f"Phase 5: Uploading thumbnail for {video_id}...")
    youtube = get_youtube_client()
    media = MediaFileUpload(thumb_path, mimetype="image/jpeg")
    try:
        youtube.thumbnails().set(videoId=video_id, media_body=media).execute()
        log(f"Phase 5: Thumbnail uploaded for {video_id}")
        return True
    except Exception as e:
        log(f"Phase 5: Thumbnail upload failed for {video_id}: {e}")
        return False


def upload_captions(video_id: str, srt_path: str, language: str = "en", name: str = "English") -> str:
    """Upload a real .srt caption track to a YouTube video (separate from any
    burned-in on-screen captions) -- improves accessibility and discoverability."""
    log(f"Phase 5: Uploading captions for {video_id}...")
    youtube = get_youtube_client()

    body = {
        "snippet": {
            "videoId": video_id,
            "language": language,
            "name": name,
            "isDraft": False,
        }
    }
    media = MediaFileUpload(srt_path, mimetype="application/octet-stream")
    request = youtube.captions().insert(part="snippet", body=body, media_body=media)
    response = request.execute()
    log(f"Phase 5: Captions uploaded — {response.get('id')}")
    return response.get("id", "")


def upload_to_rumble(video_path: str, script: dict, topic: dict) -> str:
    """Upload to Rumble if API key is configured. Returns URL or empty string."""
    if not config.RUMBLE_API_KEY:
        log("Phase 5: Rumble API key not set — skipping.")
        return ""

    log("Phase 5: Uploading to Rumble...")

    upload_url = "https://rumble.com/api/Media/upload"
    headers = {"Authorization": f"Bearer {config.RUMBLE_API_KEY}"}

    with open(video_path, "rb") as f:
        files = {"file": (os.path.basename(video_path), f, "video/mp4")}
        data = {
            "title": script.get("video_title", topic["title"])[:100],
            "description": script.get("seo_description", "")[:2000],
            "tags": ",".join(script.get("tags", [])[:10]),
            "visibility": "public",
        }
        resp = requests.post(upload_url, headers=headers, files=files, data=data, timeout=300)

    if resp.status_code in (200, 201):
        rumble_url = resp.json().get("url", "")
        log(f"Phase 5: Rumble upload complete → {rumble_url}")
        return rumble_url
    else:
        log(f"Phase 5: Rumble upload failed {resp.status_code} — {resp.text[:200]}")
        return ""


def upload_all(video_path: str, script: dict, topic: dict) -> dict:
    """Upload to all configured platforms. Returns dict of URLs."""
    results = {}

    yt_url, is_public_now = upload_to_youtube(video_path, script, topic)
    results["youtube"] = yt_url

    if yt_url:
        video_id = yt_url.rsplit("=", 1)[-1]
        try:
            if script.get("thumbnail_path") and os.path.exists(script["thumbnail_path"]):
                upload_thumbnail(video_id, script["thumbnail_path"])      # designed thumbnail (long-form)
            else:
                import thumbnail_generator as thumbs
                variants = thumbs.generate_thumbnails(video_path, script)
                if variants:
                    if upload_thumbnail(video_id, variants[0]):
                        thumbs.record_variant(video_id, variants[0], 0)
        except Exception as e:
            log(f"Phase 5: Thumbnail generation/upload skipped: {e}")

        debate_q = _extract_debate_question(script)
        if debate_q:
            if is_public_now:
                post_engagement_comment(video_id, debate_q)
            else:
                # YouTube rejects commentThreads().insert() on a video that
                # isn't public yet -- this one was pushed to a future date by
                # the same-day guard, so post it manually once it goes live
                # (or re-run post_engagement_comment(video_id, debate_q) then).
                log(f"Phase 5: Skipping engagement comment for {video_id} -- "
                    f"video is scheduled, not public yet. Post manually once live.")

    if config.UPLOAD_PRIVACY == "public":
        rumble_url = upload_to_rumble(video_path, script, topic)
        if rumble_url:
            results["rumble"] = rumble_url

        try:
            import social_cross_poster as scp
            tiktok_id = scp.upload_to_tiktok(video_path, script, topic)
            if tiktok_id:
                results["tiktok"] = tiktok_id
            instagram_id = scp.upload_to_instagram(video_path, script, topic)
            if instagram_id:
                results["instagram"] = instagram_id
        except Exception as e:
            log(f"Phase 5: Cross-posting skipped: {e}")
    else:
        log(f"Phase 5: Skipping Rumble/cross-posting — UPLOAD_PRIVACY={config.UPLOAD_PRIVACY} "
            f"(no private/unlisted review mode on these platforms)")

    log(f"Phase 5: All uploads done — {results}")
    return results
