"""
trend_now.py — Real-time research step to run BEFORE every video.

Owner, 2026-09-18: "you didnt check the trending what you make taking low
views videos". Owner, 2026-10-23: research deeply every video creation --
what people are watching right now. This answers "what is spiking in
football TODAY", from YouTube itself:

  1. chart=mostPopular, category 17 (Sports) for the channel's audience
     countries -- what YouTube is pushing right now.
  2. Football Shorts published in the last N hours, ranked by views/hour
     (velocity), across several queries -- what is breaking out right now.
  3. Which players/clubs/stories recur across the fastest risers -- many
     channels on one story = live demand.

Saves output/research/trend_now_<UTC timestamp>.json and prints a ranked
report. Quota: ~100 units per query + ~1 per chart -- keep QUERIES short
(the channel's daily budget also covers uploads at ~2,100 units each).

Usage: python trend_now.py [hours=48]
"""
import os
import re
import sys
import json
import datetime
from collections import Counter

import phase5_upload as p5
from googleapiclient.discovery import build

REGIONS = ["IN", "ID", "US", "GB", "BR"]  # channel's top audience countries
QUERIES = ["football", "soccer", "el clasico", "champions league", "premier league",
           "football shorts", "futbol"]

# Entities worth counting across titles (lowercase match).
ENTITIES = ["messi", "ronaldo", "yamal", "mbappe", "mbappé", "haaland", "vinicius", "bellingham",
            "salah", "neymar", "kane", "pedri", "raphinha", "palmer", "saka", "rodri", "modric",
            "real madrid", "barcelona", "barca", "arsenal", "liverpool", "man city", "chelsea",
            "man united", "psg", "bayern", "inter", "juventus", "clasico", "ballon d'or",
            "champions league", "world cup", "penalty", "red card", "var", "goal", "save",
            "skill", "celebration", "referee", "fans", "transfer", "injury"]


def _dur(iso):
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    return (int(m[1] or 0) * 3600 + int(m[2] or 0) * 60 + int(m[3] or 0)) if m else 0


def scan(hours: int = 48) -> dict:
    yt = build("youtube", "v3", credentials=p5.get_credentials())
    now = datetime.datetime.now(datetime.timezone.utc)
    after = (now - datetime.timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")

    charts = {}
    for rc in REGIONS:
        try:
            r = yt.videos().list(part="snippet,statistics", chart="mostPopular", regionCode=rc,
                                 videoCategoryId="17", maxResults=25).execute()
            charts[rc] = [{"id": v["id"], "title": v["snippet"]["title"],
                           "channel": v["snippet"]["channelTitle"],
                           "views": int(v["statistics"].get("viewCount", 0))} for v in r["items"]]
        except Exception as e:
            charts[rc] = [{"error": str(e)[:200]}]

    ids = {}
    for q in QUERIES:
        try:
            r = yt.search().list(part="snippet", q=q, type="video", videoDuration="short",
                                 order="viewCount", publishedAfter=after, maxResults=50).execute()
            for it in r["items"]:
                ids.setdefault(it["id"]["videoId"], q)
        except Exception as e:
            print(f"search '{q}' failed: {str(e)[:150]}")
    vids = []
    idl = list(ids)
    for i in range(0, len(idl), 50):
        for v in yt.videos().list(part="snippet,statistics,contentDetails",
                                  id=",".join(idl[i:i + 50])).execute()["items"]:
            pub = datetime.datetime.fromisoformat(v["snippet"]["publishedAt"].replace("Z", "+00:00"))
            age_h = max((now - pub).total_seconds() / 3600, 1.0)
            views = int(v["statistics"].get("viewCount", 0))
            vids.append({"id": v["id"], "title": v["snippet"]["title"],
                         "channel": v["snippet"]["channelTitle"], "channel_id": v["snippet"]["channelId"],
                         "lang": v["snippet"].get("defaultAudioLanguage") or v["snippet"].get("defaultLanguage"),
                         "dur": _dur(v["contentDetails"]["duration"]), "age_h": round(age_h, 1),
                         "views": views, "views_per_h": round(views / age_h),
                         "likes": int(v["statistics"].get("likeCount", 0)),
                         "comments": int(v["statistics"].get("commentCount", 0)),
                         "query": ids[v["id"]]})
    chs = list({v["channel_id"] for v in vids})
    subs = {}
    for i in range(0, len(chs), 50):
        for c in yt.channels().list(part="statistics", id=",".join(chs[i:i + 50])).execute()["items"]:
            subs[c["id"]] = int(c["statistics"].get("subscriberCount", 0))
    for v in vids:
        v["subs"] = subs.get(v["channel_id"], 0)
    vids.sort(key=lambda v: -v["views_per_h"])

    top = vids[:60]
    ent = Counter()
    for v in top:
        t = v["title"].lower()
        for e in ENTITIES:
            if e in t:
                ent[e] += 1

    report = {"scanned_at": now.isoformat(), "hours": hours, "charts": charts,
              "rising_shorts": vids, "entities_in_top60": ent.most_common(25)}
    os.makedirs("output/research", exist_ok=True)
    path = f"output/research/trend_now_{now.strftime('%Y%m%dT%H%MZ')}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1, ensure_ascii=False)
    report["path"] = path
    return report


def print_report(rep: dict, n: int = 40):
    print(f"=== Football Shorts, last {rep['hours']}h, by views/hour ===")
    for v in rep["rising_shorts"][:n]:
        print(f"{v['views_per_h']:>8,}/h {v['views']:>10,} {v['age_h']:>5}h {v['dur']:>3}s "
              f"subs{v['subs']:>10,} | {v['title'][:80]}")
    print("\n=== Recurring entities in the top 60 risers ===")
    print(", ".join(f"{e}:{c}" for e, c in rep["entities_in_top60"]))
    print("\n=== Sports trending charts (top 8 per region) ===")
    for rc, items in rep["charts"].items():
        print(f"-- {rc}")
        for it in items[:8]:
            print(f"   {it.get('views', 0):>10,} {it.get('channel', '')[:18]:18} | {it.get('title', it.get('error', ''))[:75]}")
    print(f"\nSaved: {rep['path']}")


if __name__ == "__main__":
    print_report(scan(int(sys.argv[1]) if len(sys.argv) > 1 else 48))
