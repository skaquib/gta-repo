"""
ypp_tracker.py
===============
Tracks progress toward YouTube Partner Program (YPP) eligibility, so
monetization readiness is visible before assuming AdSense/memberships/Super
Thanks are available. YPP requires 1,000 subscribers AND EITHER:
  - 4,000 public watch hours in the trailing 12 months, OR
  - 10,000,000 Shorts views in the trailing 90 days

This module only tracks/reports the gap to eligibility on both paths --
monetization enrollment itself still happens manually in YouTube Studio
once eligible.
"""

import datetime

import config
from logger import log

SUB_THRESHOLD = 1000
WATCH_HOURS_THRESHOLD = 4000
SHORTS_VIEWS_THRESHOLD = 10_000_000


def _get_subscriber_count() -> int:
    import phase5_upload as p5
    yt = p5.get_youtube_client()
    channel_id = config.YOUTUBE_CHANNEL_ID
    try:
        if channel_id:
            resp = yt.channels().list(part="statistics", id=channel_id).execute()
        else:
            resp = yt.channels().list(part="statistics", mine=True).execute()
        items = resp.get("items", [])
        return int(items[0]["statistics"].get("subscriberCount", 0)) if items else 0
    except Exception as e:
        log(f"YPP tracker: subscriber count fetch failed: {e}")
        return 0


def _get_watch_hours(days: int = 365) -> float:
    """Cumulative estimated public watch time (hours) over the trailing
    `days` window, via the YouTube Analytics API."""
    channel_id = config.YOUTUBE_CHANNEL_ID
    if not channel_id:
        return 0.0

    try:
        import youtube_analytics_client as yta_client
        yta = yta_client.get_analytics_client()
    except Exception as e:
        log(f"YPP tracker: analytics client unavailable: {e}")
        return 0.0

    end = datetime.date.today()
    start = end - datetime.timedelta(days=days)
    try:
        resp = yta.reports().query(
            ids=f"channel=={channel_id}",
            startDate=start.isoformat(),
            endDate=end.isoformat(),
            metrics="estimatedMinutesWatched",
        ).execute()
    except Exception as e:
        log(f"YPP tracker: watch time query failed: {e}")
        return 0.0

    rows = resp.get("rows", [])
    minutes = rows[0][0] if rows else 0
    return minutes / 60.0


def _get_shorts_views(days: int = 90) -> int:
    """Views on Shorts specifically over the trailing `days` window."""
    channel_id = config.YOUTUBE_CHANNEL_ID
    if not channel_id:
        return 0

    try:
        import youtube_analytics_client as yta_client
        yta = yta_client.get_analytics_client()
    except Exception as e:
        log(f"YPP tracker: analytics client unavailable: {e}")
        return 0

    end = datetime.date.today()
    start = end - datetime.timedelta(days=days)
    try:
        resp = yta.reports().query(
            ids=f"channel=={channel_id}",
            startDate=start.isoformat(),
            endDate=end.isoformat(),
            metrics="views",
            filters="creatorContentType==SHORTS",
        ).execute()
    except Exception as e:
        log(f"YPP tracker: Shorts views query failed ({e}) — treating as 0")
        return 0

    rows = resp.get("rows", [])
    return int(rows[0][0]) if rows else 0


def check_eligibility() -> dict:
    """Return current YPP eligibility status and the remaining gap on both
    qualifying paths (whichever is closer is the one to chase)."""
    subs = _get_subscriber_count()
    watch_hours = _get_watch_hours(365)
    shorts_views = _get_shorts_views(90)

    subs_met = subs >= SUB_THRESHOLD
    watch_hours_path = subs_met and watch_hours >= WATCH_HOURS_THRESHOLD
    shorts_views_path = subs_met and shorts_views >= SHORTS_VIEWS_THRESHOLD
    eligible = watch_hours_path or shorts_views_path

    result = {
        "eligible": eligible,
        "subscribers": subs,
        "subscribers_needed": max(0, SUB_THRESHOLD - subs),
        "watch_hours_12mo": round(watch_hours, 1),
        "watch_hours_needed": max(0.0, round(WATCH_HOURS_THRESHOLD - watch_hours, 1)),
        "shorts_views_90d": shorts_views,
        "shorts_views_needed": max(0, SHORTS_VIEWS_THRESHOLD - shorts_views),
        "qualifying_path": "watch_hours" if watch_hours_path else ("shorts_views" if shorts_views_path else None),
    }

    log(f"YPP tracker: subs={subs} watch_hours={watch_hours:.0f}/{WATCH_HOURS_THRESHOLD} "
        f"shorts_views_90d={shorts_views}/{SHORTS_VIEWS_THRESHOLD} eligible={eligible}")
    return result
