"""
match_calendar.py
==================
Fixture/result calendar the content pipeline schedules and writes around, so
publishing clusters near real match moments instead of a blind fixed-interval
timer, and tactical-breakdown scripts (goal_analysis_creator.py,
match_analysis_creator.py) can pull real recent matches instead of a static
hardcoded list.

Data comes from a local match_calendar_data.json file, refreshed by
fetch_fixtures_from_api() if you configure FOOTBALL_DATA_API_URL/_API_KEY
(provider-agnostic on purpose — plug in whatever football data API you have
access to). This module intentionally does NOT hardcode specific match
fixtures/scores itself: that data must come from a real, verified source,
not be guessed.

Fixture schema:
  {"id": str, "home": str, "away": str, "kickoff_utc": "2026-06-11T18:00:00Z",
   "status": "scheduled"|"finished", "home_score": int|None,
   "away_score": int|None, "competition": str,
   "analysis_detail": {...} (optional)}

`analysis_detail` is an optional, manually-populated (or richer-stats-API-
sourced) payload carrying the detailed tactical breakdown data that
goal_analysis_creator.py / match_analysis_creator.py need (per-goal
descriptions, formations, key stats, etc.) — those are richer than a bare
fixture result and deliberately not fabricated here. When present, both
creators prefer it over their bundled example templates; see their
pick_analysis()/pick_match() functions for the exact sub-schema each expects.
"""

import json
import os
import datetime
import requests

import config
from logger import log

CALENDAR_FILE = os.path.join(os.path.dirname(__file__), "match_calendar_data.json")


def _load() -> list:
    if os.path.exists(CALENDAR_FILE):
        try:
            with open(CALENDAR_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log(f"Match calendar: failed to read {CALENDAR_FILE}: {e}")
    return []


def _save(fixtures: list):
    with open(CALENDAR_FILE, "w", encoding="utf-8") as f:
        json.dump(fixtures, f, indent=2)


def parse_kickoff(fixture: dict):
    """Return the fixture's kickoff time as a timezone-aware UTC datetime, or
    None if missing/unparseable."""
    raw = fixture.get("kickoff_utc", "")
    try:
        dt = datetime.datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt
    except Exception:
        return None


def next_match_window(hours_ahead: float = 48.0) -> list:
    """Fixtures kicking off within the next `hours_ahead` hours — use this to
    cluster publishing around real match moments."""
    now = datetime.datetime.now(datetime.timezone.utc)
    cutoff = now + datetime.timedelta(hours=hours_ahead)
    upcoming = []
    for f in _load():
        kt = parse_kickoff(f)
        if kt and now <= kt <= cutoff:
            upcoming.append(f)
    return sorted(upcoming, key=lambda f: f["kickoff_utc"])


def recent_results(days_back: float = 3.0) -> list:
    """Finished matches from the last `days_back` days — use this to source
    real, current tactical-breakdown content instead of a static hardcoded
    match list."""
    now = datetime.datetime.now(datetime.timezone.utc)
    cutoff = now - datetime.timedelta(days=days_back)
    finished = []
    for f in _load():
        if f.get("status") != "finished":
            continue
        kt = parse_kickoff(f)
        if kt and cutoff <= kt <= now:
            finished.append(f)
    return sorted(finished, key=lambda f: f["kickoff_utc"], reverse=True)


def fetch_fixtures_from_api() -> bool:
    """Optionally refresh match_calendar_data.json from a football data API.
    Configure FOOTBALL_DATA_API_URL + FOOTBALL_DATA_API_KEY in .env to enable
    this. Deliberately provider-agnostic and off by default: fixture/result
    data must come from a real, verified source."""
    api_url = getattr(config, "FOOTBALL_DATA_API_URL", "")
    api_key = getattr(config, "FOOTBALL_DATA_API_KEY", "")
    if not api_url or not api_key:
        log("Match calendar: FOOTBALL_DATA_API_URL/KEY not configured — skipping live fetch")
        return False

    try:
        resp = requests.get(api_url, headers={"X-Auth-Token": api_key}, timeout=30)
        resp.raise_for_status()
        payload = resp.json()
    except Exception as e:
        log(f"Match calendar: API fetch failed: {e}")
        return False

    raw_matches = payload.get("matches", payload if isinstance(payload, list) else [])
    normalized = []
    for m in raw_matches:
        try:
            score = (m.get("score", {}) or {}).get("fullTime", {}) or {}
            normalized.append({
                "id": str(m.get("id", "")),
                "home": (m.get("homeTeam", {}) or {}).get("name", m.get("home", "")),
                "away": (m.get("awayTeam", {}) or {}).get("name", m.get("away", "")),
                "kickoff_utc": m.get("utcDate", m.get("kickoff_utc", "")),
                "status": "finished" if m.get("status") == "FINISHED" else "scheduled",
                "home_score": score.get("home"),
                "away_score": score.get("away"),
                "competition": (m.get("competition", {}) or {}).get("name", "FIFA World Cup 2026"),
            })
        except Exception:
            continue

    if normalized:
        _save(normalized)
        log(f"Match calendar: refreshed {len(normalized)} fixtures from API")
        return True
    return False
