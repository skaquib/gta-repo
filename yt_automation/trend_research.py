"""
trend_research.py — Real search-behavior signal for topic research, free
and unblocked (unlike Google Trends' unofficial API, which returns 429
Too Many Requests immediately from this environment).

Uses YouTube's own search-autocomplete endpoint -- the same one that
powers the dropdown when you type in YouTube's search box. It's not an
official public API, but it's a simple, unauthenticated GET request that
reflects real aggregated search behavior on YouTube specifically, which
is a better-targeted signal for this channel than generic Google Trends
would be anyway.

Usage:
    python trend_research.py "why does soccer"
    python trend_research.py "why is" "why do" "why does" --sport
"""
import sys
import json
import requests


def suggest(query: str, timeout: int = 15) -> list:
    """Real-time YouTube search-autocomplete suggestions for `query`."""
    r = requests.get(
        "http://suggestqueries.google.com/complete/search",
        params={"client": "youtube", "ds": "yt", "q": query},
        timeout=timeout,
    )
    r.raise_for_status()
    text = r.text
    start = text.index("(") + 1
    end = text.rindex(")")
    data = json.loads(text[start:end])
    return [item[0] for item in data[1]]


def scan_prefixes(prefixes: list) -> dict:
    """Run several curiosity-gap prefixes ("why does X", "why is X") and
    return {prefix: [suggestions]} -- a quick scan across multiple sports/
    subjects in one pass."""
    results = {}
    for p in prefixes:
        try:
            results[p] = suggest(p)
        except Exception as e:
            results[p] = [f"ERROR: {e}"]
    return results


if __name__ == "__main__":
    queries = sys.argv[1:] or ["why does"]
    for q in queries:
        print(f"=== {q!r} ===")
        for s in suggest(q):
            print("  ", s)
