"""
niche_trends.py — What is trending RIGHT NOW in our niche (animals / "what
happens inside" / science facts / 3D animation), not over the last year.

Two live signals:
  1. search: Shorts (<= 3 min) published in the last N hours for each niche
     query, ranked by views per hour since upload (velocity, not totals);
  2. charts: YouTube's mostPopular chart for Pets & Animals (15) and
     Science & Technology (28) in US / IN / GB, kept to short videos.
     (Education, 27, has no mostPopular chart in these regions -- 404.)

Quota: ~100 units per search query + ~1 per chart/videos call.
Writes output/research/niche_trends_<ts>.json.

Usage: python niche_trends.py [hours=168]
"""
import re
import sys
import json
import datetime

import phase5_upload as p5
from googleapiclient.discovery import build

QUERIES = [
    "animal facts", "what happens inside", "3d animation facts", "how animals",
    "animal x-ray", "nature facts", "science facts", "how it works 3d",
    "did you know animals", "inside body animation",
]
CHARTS = [("US", "15"), ("US", "28"), ("IN", "15"), ("IN", "28"), ("GB", "15"), ("GB", "28")]


def _secs(iso):
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m:
        return 0
    h, mi, s = (int(x) if x else 0 for x in m.groups())
    return h * 3600 + mi * 60 + s


def _details(yt, ids):
    out = {}
    for k in range(0, len(ids), 50):
        r = yt.videos().list(part="snippet,statistics,contentDetails", id=",".join(ids[k:k + 50])).execute()
        for v in r["items"]:
            out[v["id"]] = v
    return out


def _row(v, now, source):
    pub = datetime.datetime.fromisoformat(v["snippet"]["publishedAt"].replace("Z", "+00:00"))
    hours = max(1.0, (now - pub).total_seconds() / 3600)
    views = int(v["statistics"].get("viewCount", 0))
    return {
        "id": v["id"], "title": v["snippet"]["title"], "channel": v["snippet"]["channelTitle"],
        "published": v["snippet"]["publishedAt"][:16], "hours": round(hours, 1), "views": views,
        "views_per_hour": round(views / hours), "likes": int(v["statistics"].get("likeCount", 0)),
        "comments": int(v["statistics"].get("commentCount", 0)),
        "secs": _secs(v["contentDetails"].get("duration")), "source": source,
    }


def scan(hours=168):
    yt = build("youtube", "v3", credentials=p5.get_credentials())
    now = datetime.datetime.now(datetime.timezone.utc)
    after = (now - datetime.timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    found = {}
    for q in QUERIES:
        try:
            r = yt.search().list(part="id", q=q, type="video", videoDuration="short", order="viewCount",
                                 publishedAfter=after, maxResults=25, relevanceLanguage="en").execute()
        except Exception as e:
            print(f"search failed ({q}): {str(e)[:120]}")
            break
        for it in r["items"]:
            found.setdefault(it["id"]["videoId"], f"search:{q}")
    det = _details(yt, list(found))
    rows = [_row(v, now, found[vid]) for vid, v in det.items()]
    for region, cat in CHARTS:
        try:
            r = yt.videos().list(part="snippet,statistics,contentDetails", chart="mostPopular", regionCode=region,
                                 videoCategoryId=cat, maxResults=50).execute()
        except Exception as e:
            print(f"chart {region}/{cat} failed: {str(e)[:100]}")
            continue
        for v in r["items"]:
            if _secs(v["contentDetails"].get("duration")) <= 180 and v["id"] not in found:
                found[v["id"]] = f"chart:{region}/{cat}"
                rows.append(_row(v, now, found[v["id"]]))
    rows = [x for x in rows if x["secs"] <= 180]
    rows.sort(key=lambda x: -x["views_per_hour"])
    path = f"output/research/niche_trends_{now.strftime('%Y%m%dT%H%M%SZ')}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=1, ensure_ascii=False)
    return rows, path


if __name__ == "__main__":
    hrs = int(sys.argv[1]) if len(sys.argv) > 1 else 168
    rows, path = scan(hrs)
    print(f"{'views/h':>8} {'views':>11} {'age h':>6} {'sec':>4}  title  [channel]  <- source")
    for x in rows[:45]:
        print(f"{x['views_per_hour']:>8,} {x['views']:>11,} {x['hours']:>6} {x['secs']:>4}  {x['title'][:62]}  "
              f"[{x['channel'][:22]}]  <- {x['source']}")
    print(f"\n{len(rows)} short videos. Saved: {path}")
