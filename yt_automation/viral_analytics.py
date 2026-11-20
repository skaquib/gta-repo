"""
viral_analytics.py
==================
Fetch YouTube performance data, identify viral winners (1M+ views goal),
and update strategy to double down on what works.

View counts alone are an outcome, not a cause: they tell you a video did
well after the algorithm already decided to push it. CTR (thumbnail+title)
and average-view-percentage (content/pacing) are the two signals YouTube's
recommender actually uses to make that decision, so this module pulls both
(via youtube_analytics_client.py) and diagnoses *why* a video over/under-
performed, not just *how much* it got.
"""

import json
import os
import re
import time
import config
from logger import log

STATE_FILE = os.path.join(config.OUTPUT_DIR, "viral_strategy.json")
VIRAL_VIEW_THRESHOLD = int(os.getenv("VIRAL_VIEW_THRESHOLD", "1000000"))
DOUBLE_DOWN_THRESHOLD = int(os.getenv("DOUBLE_DOWN_THRESHOLD", "50000"))

# Rough strong/weak bands for CTR and average-view-percentage. There's no
# universal "good" number, but these separate a thumbnail/title problem
# (low CTR) from a content/pacing problem (low AVD) clearly enough to be
# a useful diagnostic signal.
CTR_STRONG, CTR_WEAK = 0.06, 0.02
AVD_STRONG, AVD_WEAK = 50.0, 25.0


def _load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "winners": [],
        "subjects": {},
        "hook_patterns": {},
        "last_sync": 0,
        "total_videos_tracked": 0,
    }


def _save_state(state: dict):
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def _get_youtube_client():
    try:
        import phase5_upload as p5
        return p5.get_youtube_client()
    except Exception as e:
        log(f"Analytics: YouTube client unavailable ({e})")
        return None


def fetch_recent_video_stats(max_results: int = 25) -> list:
    """Return list of {video_id, title, views, likes, comments, published_at}."""
    yt = _get_youtube_client()
    if not yt:
        return []

    channel_id = config.YOUTUBE_CHANNEL_ID
    if not channel_id:
        log("Analytics: YOUTUBE_CHANNEL_ID not set")
        return []

    try:
        resp = yt.search().list(
            part="snippet",
            channelId=channel_id,
            type="video",
            order="date",
            maxResults=max_results,
        ).execute()

        video_ids = [item["id"]["videoId"] for item in resp.get("items", [])]
        if not video_ids:
            return []

        stats_resp = yt.videos().list(
            part="statistics,snippet",
            id=",".join(video_ids),
        ).execute()

        results = []
        for item in stats_resp.get("items", []):
            stats = item.get("statistics", {})
            snip = item.get("snippet", {})
            results.append({
                "video_id": item["id"],
                "title": snip.get("title", ""),
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
                "published_at": snip.get("publishedAt", ""),
            })
        return results
    except Exception as e:
        log(f"Analytics fetch error: {e}")
        return []


def _extract_subject(title: str) -> str:
    """Heuristic: pull player/manager name from title."""
    known = [
        "messi", "ronaldo", "mbappé", "mbappe", "neymar", "haaland", "guardiola",
        "mourinho", "ancelotti", "zidane", "buffon", "modric", "salah", "de bruyne",
        "yamal", "beckham", "maradona", "pele", "ronaldinho", "drogba", "suarez",
    ]
    t = title.lower()
    for name in known:
        if name in t:
            return name.title()
    return ""


def _extract_hook_pattern(title: str) -> str:
    t = title.lower()
    if "?" in title:
        return "question_hook"
    if any(w in t for w in ["insane", "shocking", "nobody", "secret", "destroyed"]):
        return "shock_hook"
    if any(w in t for w in ["aura", "composure", "cold", "calm"]):
        return "aura_hook"
    if any(w in t for w in ["record", "fastest", "ever", "history"]):
        return "record_hook"
    return "general"


def _diagnose(ctr: float, avg_view_pct: float) -> str:
    """Diagnose *why* a video did or didn't perform, using the two signals
    YouTube's recommender actually weighs: CTR (thumbnail+title) and average
    view percentage (content/pacing)."""
    high_ctr, low_ctr = ctr >= CTR_STRONG, ctr < CTR_WEAK
    high_avd, low_avd = avg_view_pct >= AVD_STRONG, avg_view_pct < AVD_WEAK

    if high_ctr and low_avd:
        return "hook/thumbnail over-promises — viewers click but bounce; fix script pacing/payoff"
    if low_ctr and high_avd:
        return "content holds attention but isn't getting clicked — retest thumbnail/title, not the script"
    if low_ctr and low_avd:
        return "both thumbnail/title and content need work"
    if high_ctr and high_avd:
        return "winning formula on both signals — double down on this style"
    return "mixed signals — inconclusive"


def sync_and_analyze() -> dict:
    """
    Pull latest stats plus real CTR/retention analytics, update winners list,
    and return strategy recommendations that diagnose *why* something did or
    didn't perform, not just rank by view count.
    """
    state = _load_state()
    videos = fetch_recent_video_stats()

    if not videos:
        log("Analytics: no videos to analyze")
        return {"winners": state.get("winners", []), "recommendations": []}

    try:
        import youtube_analytics_client as yta_client
        metrics_by_id = {m["video_id"]: m for m in yta_client.get_video_metrics()}
    except Exception as e:
        log(f"Analytics: YouTube Analytics API unavailable ({e}) — view counts only")
        metrics_by_id = {}

    video_metrics = state.setdefault("video_metrics", {})
    new_winners = []
    for v in videos:
        views = v["views"]
        subject = _extract_subject(v["title"])
        pattern = _extract_hook_pattern(v["title"])
        m = metrics_by_id.get(v["video_id"], {})

        if m:
            ctr = m.get("ctr", 0.0)
            avg_view_pct = m.get("avg_view_pct", 0.0)
            video_metrics[v["video_id"]] = {
                "title": v["title"],
                "ctr": ctr,
                "avg_view_duration": m.get("avg_view_duration", 0),
                "avg_view_pct": avg_view_pct,
                "traffic_source": m.get("top_traffic_source", ""),
                "diagnosis": _diagnose(ctr, avg_view_pct),
                "synced_at": time.time(),
            }

        if views >= DOUBLE_DOWN_THRESHOLD:
            entry = {
                "video_id": v["video_id"],
                "title": v["title"],
                "views": views,
                "subject": subject,
                "hook_pattern": pattern,
                "ctr": m.get("ctr", 0.0),
                "avg_view_pct": m.get("avg_view_pct", 0.0),
                "synced_at": time.time(),
            }
            if views >= VIRAL_VIEW_THRESHOLD:
                new_winners.append(entry)
                log(f"VIRAL WINNER: {v['title'][:50]} — {views:,} views")

            if subject:
                state["subjects"][subject] = state["subjects"].get(subject, 0) + views
            state["hook_patterns"][pattern] = state["hook_patterns"].get(pattern, 0) + views

    existing_ids = {w["video_id"] for w in state.get("winners", [])}
    for w in new_winners:
        if w["video_id"] not in existing_ids:
            state.setdefault("winners", []).append(w)

    state["last_sync"] = time.time()
    state["total_videos_tracked"] = len(videos)
    _save_state(state)

    recommendations = build_recommendations(state)
    return {"winners": state.get("winners", []), "recommendations": recommendations, "state": state}


def build_recommendations(state: dict) -> list:
    recs = []
    subjects = state.get("subjects", {})
    patterns = state.get("hook_patterns", {})

    if subjects:
        top_subject = max(subjects, key=subjects.get)
        recs.append(f"Double down on '{top_subject}' — highest total views across Shorts")

    if patterns:
        top_pattern = max(patterns, key=patterns.get)
        recs.append(f"Use more '{top_pattern}' style hooks in scripts")

    winners = state.get("winners", [])
    if winners:
        best = max(winners, key=lambda w: w.get("views", 0))
        recs.append(f"Remake/sequel angle on: '{best['title'][:60]}' ({best['views']:,} views)")

    for m in state.get("video_metrics", {}).values():
        diagnosis = m.get("diagnosis", "")
        if diagnosis and diagnosis != "mixed signals — inconclusive":
            recs.append(
                f"'{m['title'][:50]}' (CTR {m['ctr']*100:.1f}%, AVD {m['avg_view_pct']:.0f}%): {diagnosis}"
            )

    return recs


def get_priority_subjects(default_subjects: list) -> list:
    """
    Re-order subject list to prioritize proven winners (double-down strategy).
    """
    state = _load_state()
    subject_scores = state.get("subjects", {})

    if not subject_scores:
        return default_subjects

    def score(s):
        s_lower = s.lower()
        total = 0
        for name, views in subject_scores.items():
            if name.lower() in s_lower:
                total += views
        return total

    ranked = sorted(default_subjects, key=score, reverse=True)
    if ranked != default_subjects:
        log(f"Analytics: reordered subjects — top pick '{ranked[0][:40]}'")
    return ranked


def get_viral_script_hints() -> str:
    """Extra prompt context for AI script gen based on what's working."""
    state = _load_state()
    hints = []

    patterns = state.get("hook_patterns", {})
    if patterns:
        top = max(patterns, key=patterns.get)
        hints.append(f"Proven hook style on this channel: {top}")

    subjects = state.get("subjects", {})
    if subjects:
        top_subj = max(subjects, key=subjects.get)
        hints.append(f"Top performing subject: {top_subj}")

    winners = state.get("winners", [])
    if winners:
        hints.append(f"Channel has {len(winners)} video(s) over {VIRAL_VIEW_THRESHOLD:,} views")

    return " | ".join(hints) if hints else ""
