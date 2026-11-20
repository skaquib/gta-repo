"""
youtube_analytics_client.py
============================
Thin wrapper around the YouTube Analytics API (reports().query()) — the data
source that actually carries CTR and audience-retention numbers.

The YouTube Data API (used elsewhere for uploads and viral_analytics.py's
view/like/comment sync) only exposes raw counts, which are outcomes. CTR
(impressionClickThroughRate) and average-view-duration/percentage are the
signals YouTube's recommender actually uses to decide whether to keep
pushing a video, and they weren't being read anywhere in this codebase.

Requires the yt-analytics.readonly OAuth scope (see phase5_upload.SCOPES).
If youtube_token.pickle was cached before that scope was added, delete it
once so the next auth run re-prompts for consent.
"""

import datetime

from googleapiclient.discovery import build

import config
from logger import log


def get_analytics_client():
    import phase5_upload as p5
    creds = p5.get_credentials()
    return build("youtubeAnalytics", "v2", credentials=creds)


def get_video_metrics(days: int = 28, max_results: int = 50) -> list:
    """
    Return per-video metrics for the trailing `days` window:
      [{video_id, views, avg_view_duration, avg_view_pct, impressions,
        ctr, top_traffic_source}, ...]
    """
    channel_id = config.YOUTUBE_CHANNEL_ID
    if not channel_id:
        log("YT Analytics: YOUTUBE_CHANNEL_ID not set")
        return []

    try:
        yta = get_analytics_client()
    except Exception as e:
        log(f"YT Analytics: client unavailable ({e})")
        return []

    end = datetime.date.today()
    start = end - datetime.timedelta(days=days)

    # Core playback metrics -- confirmed working against this channel's
    # actual account tier (verified 2026-08-19). "impressions" and
    # "impressionClickThroughRate" are the OLD metric names Google replaced
    # in a Jan 2026 update; the new names (videoThumbnailImpressions,
    # videoThumbnailImpressionsClickRate) are recognized by the API but
    # every query shape tried against this channel (no dimension, video
    # dimension, day dimension, single-video filter) returned "query is
    # not supported". Confirmed via Studio's own Reach tab (2026-08-19,
    # checked on the channel's top-performing video, 1.7K views) that this
    # isn't a threshold that unlocks with more data: Studio shows no
    # impressions/CTR section for Shorts at all. Shorts autoplay full-screen
    # in a swipe feed -- there's no discrete "thumbnail shown, user decides
    # to click" moment for it to measure, so the metric doesn't exist for
    # this content type, on this channel or the API either. Queried
    # separately (and left as a harmless no-op) in case any future upload
    # on this channel is ever a non-Shorts video, where it would apply.
    try:
        resp = yta.reports().query(
            ids=f"channel=={channel_id}",
            startDate=start.isoformat(),
            endDate=end.isoformat(),
            metrics="views,averageViewDuration,averageViewPercentage",
            dimensions="video",
            sort="-views",
            maxResults=max_results,
        ).execute()
    except Exception as e:
        log(f"YT Analytics: metrics query failed ({e})")
        return []

    headers = [h["name"] for h in resp.get("columnHeaders", [])]
    rows = resp.get("rows", [])

    ctr_by_video = {}
    try:
        ctr_resp = yta.reports().query(
            ids=f"channel=={channel_id}",
            startDate=start.isoformat(),
            endDate=end.isoformat(),
            metrics="videoThumbnailImpressions,videoThumbnailImpressionsClickRate",
            dimensions="video",
            sort="-videoThumbnailImpressions",
            maxResults=max_results,
        ).execute()
        ctr_headers = [h["name"] for h in ctr_resp.get("columnHeaders", [])]
        for row in ctr_resp.get("rows", []):
            rec = dict(zip(ctr_headers, row))
            ctr_by_video[rec.get("video")] = rec
    except Exception as e:
        log(f"YT Analytics: thumbnail-impression/CTR data unavailable on this "
            f"account tier ({e}) -- proceeding with views/retention only")

    results = []
    for row in rows:
        rec = dict(zip(headers, row))
        ctr_rec = ctr_by_video.get(rec.get("video"), {})
        results.append({
            "video_id": rec.get("video"),
            "views": rec.get("views", 0),
            "avg_view_duration": rec.get("averageViewDuration", 0),
            "avg_view_pct": rec.get("averageViewPercentage", 0.0),
            "impressions": ctr_rec.get("videoThumbnailImpressions", 0),
            "ctr": ctr_rec.get("videoThumbnailImpressionsClickRate", 0.0),
        })

    video_ids = [r["video_id"] for r in results if r.get("video_id")]
    traffic = _get_top_traffic_sources(yta, channel_id, start, end, video_ids)
    for r in results:
        r["top_traffic_source"] = traffic.get(r["video_id"], "")

    return results


def _get_top_traffic_sources(yta, channel_id: str, start: datetime.date, end: datetime.date,
                               video_ids: list) -> dict:
    """Return {video_id: top_traffic_source_type} for the same window.

    The channel-wide "dimensions=video,insightTrafficSourceType" combo always
    returns "query is not supported" (confirmed 2026-08-19 across every
    dimension/filter shape). A single-video "filters=video==ID,
    dimensions=insightTrafficSourceType" query works fine -- verified live,
    e.g. mRQMd5z74KI came back SHORTS=1626, YT_OTHER_PAGE=28, YT_CHANNEL=15,
    YT_SEARCH=14, SUBSCRIBER=2. So this loops per-video instead of trying one
    channel-wide call. Cost is one extra query per video already in
    `results`, which is bounded by max_results.
    """
    best = {}
    for vid in video_ids:
        try:
            resp = yta.reports().query(
                ids=f"channel=={channel_id}",
                startDate=start.isoformat(),
                endDate=end.isoformat(),
                metrics="views",
                dimensions="insightTrafficSourceType",
                filters=f"video=={vid}",
                sort="-views",
                maxResults=1,
            ).execute()
        except Exception as e:
            log(f"YT Analytics: traffic source query failed for {vid} ({e})")
            continue

        rows = resp.get("rows", [])
        if rows:
            headers = [h["name"] for h in resp.get("columnHeaders", [])]
            rec = dict(zip(headers, rows[0]))
            best[vid] = rec.get("insightTrafficSourceType", "")

    return best
