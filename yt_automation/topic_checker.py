"""
topic_checker.py — Pre-production checklist. Run this BEFORE writing a
full script, not after building the video.

Catches two concrete, historically-costly failure modes on this channel:
  1. Thin/no stock footage inventory for the topic's queries -- this is
     exactly what caused the bacon, flower, dog-fetching-a-ball, and
     wrestler mismatches this week. If a query returns 0 tag-confirmed,
     not-yet-used clips, that's a hard signal to rewrite the query or
     pick a different topic BEFORE the script and voiceover get built.
  2. Duplicate content -- same title already published.

What this deliberately does NOT do: predict virality. No honest tool can
score "will this specific video hit 10K views" -- that depends on real-time
algorithmic distribution no one outside YouTube can see. The actual
trending-research step (what's genuinely being searched/watched today,
verified against comparable-channel view data) has to stay a real
WebSearch-driven research pass done by hand before locking a topic --
same as was done for the marathon/basketball/tennis-can/Wrexham videos.
This script only verifies the topic is PRODUCIBLE without a mismatch and
isn't a repeat, which is a real, checkable precondition.
"""
import sys
import json

import visual_shorts_creator as vsc
import viral_analytics as va
from logger import log


# A correctly-tagged clip can still break a video if it's shorter than the
# segment it gets assigned to: the soccer-vest video used a real, on-topic
# 14.3s football clip for a segment needing 17.9s, and MoviePy silently
# froze on the last frame for the remaining ~3.5s while captions kept
# advancing -- same-looking "1 usable clip" result, broken video anyway.
# The body segment is consistently the longest in this pipeline's 3-segment
# layout, so require this minimum for a clip to count as safely usable.
MIN_SAFE_DURATION = 15.0


def check_footage_availability(queries: list) -> dict:
    """For each candidate query, check how many tag-confirmed, NOT-YET-USED,
    and long-enough (>= MIN_SAFE_DURATION) clips exist on Pixabay right now.
    0 for a query is a hard stop for that query specifically."""
    used = vsc._load_used_clip_ids()
    already_used = set(int(x) for x in used.get("pixabay", []))
    results = {}
    for q in queries:
        try:
            hits = vsc._search_pixabay(q, already_used)
            confirmed = vsc._filter_by_tag_relevance(hits, q) if hits else []
            long_enough = [h for h in confirmed if h.get("duration", 0) >= MIN_SAFE_DURATION]
            short = len(confirmed) - len(long_enough)
            if short:
                log(f"  ('{q}': {short} tag-confirmed clip(s) excluded for being under {MIN_SAFE_DURATION:.0f}s)")
            results[q] = len(long_enough)
        except Exception as e:
            log(f"  Footage check failed for '{q}': {e}")
            results[q] = 0
    return results


def check_final_script_footage(script: dict) -> dict:
    """Same check as check_footage_availability, but for the queries the
    real pipeline will actually use -- download_clips() calls
    vsc._generate_search_terms_from_script(script) and only falls back to
    script['queries'] if that returns nothing, so a check run against
    hand-picked queries before the script exists can pass while the real
    build searches for entirely different terms (confirmed live 2026-08-19:
    checked "soccer stadium"/"soccer match"/"football training", the real
    build searched "Vintage Football"/"Arsenal Football Team"/"Title
    Defense" instead, and one of those matched a too-short clip that froze
    the video). Run this AFTER the script is finalized, right before
    calling download_clips() for the real build, as a second checkpoint --
    check_footage_availability is still useful earlier for a quick sanity
    check that the general subject has stock footage at all."""
    queries = vsc._generate_search_terms_from_script(script) or script.get(
        "queries", ["soccer goal", "football stadium", "soccer player"])
    log(f"Real pipeline queries for this script: {queries}")
    return check_footage_availability(queries)


def check_title_duplicate(title: str) -> bool:
    """True if this exact title already exists on the channel."""
    try:
        existing = {v["title"].strip().lower() for v in va.fetch_recent_video_stats(max_results=50)}
        return title.strip().lower() in existing
    except Exception as e:
        log(f"Duplicate check unavailable ({e}) -- proceeding without it")
        return False


def run_checklist(title: str, queries: list) -> dict:
    log("=" * 60)
    log("PRE-PRODUCTION CHECKLIST")
    log("=" * 60)

    dup = check_title_duplicate(title)
    log(f"Duplicate title check: {'FAIL -- this exact title already exists' if dup else 'pass'}")

    footage = check_footage_availability(queries)
    weak_queries = [q for q, n in footage.items() if n == 0]
    for q, n in footage.items():
        flag = " -- NONE FOUND, rewrite this query" if n == 0 else ""
        log(f"  '{q}': {n} usable clip(s){flag}")

    go = (not dup) and (len(weak_queries) < len(queries))
    if dup:
        verdict = "NO-GO -- duplicate title"
    elif len(weak_queries) == len(queries):
        verdict = "NO-GO -- no query has usable footage"
    elif weak_queries:
        verdict = f"GO, but rewrite: {', '.join(weak_queries)}"
    else:
        verdict = "GO"
    log(f"RECOMMENDATION: {verdict}")
    log("-" * 60)
    log("This does NOT predict virality. Verify real trending signal by "
        "hand (WebSearch what's actually being searched/watched today, "
        "cross-check comparable-channel view data) before locking the "
        "topic -- this only confirms it's producible and not a repeat.")

    return {"title": title, "duplicate": dup, "footage": footage,
            "weak_queries": weak_queries, "verdict": verdict, "go": go}


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: topic_checker.py '<title>' '<query1>|<query2>|<query3>'")
        sys.exit(1)
    title = sys.argv[1]
    queries = sys.argv[2].split("|")
    result = run_checklist(title, queries)
    print(json.dumps(result, indent=2))
