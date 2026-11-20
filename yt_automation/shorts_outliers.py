"""
shorts_outliers.py — read-only: which Shorts of the last 30 days broke out from SMALL channels, across 24 topics.
Basis of CHANNEL_DIAGNOSIS.md. Costs ~2,500 of the 10,000 daily API quota units: run at most weekly.

  python shorts_outliers.py [out.json]
"""
import datetime, json, os, re, sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import phase5_upload as p5
yt = p5.get_youtube_client()
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "notes", "trends", f"shorts_outliers_{datetime.date.today()}.json")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
after = (datetime.datetime.utcnow() - datetime.timedelta(days=30)).strftime("%Y-%m-%dT00:00:00Z")
Q = ["funny animals", "animal facts", "cute animals", "wild animals", "did you know", "science facts", "history facts",
     "what if", "3d animation", "funny animation", "cartoon", "animated story", "comedy skit", "funny", "relatable",
     "satisfying", "how it's made", "size comparison", "life hacks", "cooking", "football", "cricket", "ai video", "pov"]
seen = {}
for q in Q:
    try:
        r = yt.search().list(part="snippet", q=q, type="video", videoDuration="short", order="viewCount",
                             publishedAfter=after, relevanceLanguage="en", maxResults=50).execute()
    except Exception as e:
        print("search fail", q, str(e)[:120]); break
    for it in r["items"]:
        seen.setdefault(it["id"]["videoId"], q)
ids = list(seen)
vids = {}
for k in range(0, len(ids), 50):
    for v in yt.videos().list(part="snippet,statistics,contentDetails", id=",".join(ids[k:k+50])).execute()["items"]:
        m = re.match(r"P(?:\d+D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", v["contentDetails"]["duration"])
        secs = sum(int(x or 0) * f for x, f in zip(m.groups(), (3600, 60, 1)))
        s = v["statistics"]
        vids[v["id"]] = dict(q=seen[v["id"]], title=v["snippet"]["title"], ch=v["snippet"]["channelId"], chname=v["snippet"]["channelTitle"],
                             pub=v["snippet"]["publishedAt"][:10], secs=secs, views=int(s.get("viewCount", 0)), likes=int(s.get("likeCount", 0)),
                             comments=int(s.get("commentCount", 0)), tags=v["snippet"].get("tags", [])[:8],
                             desc=v["snippet"].get("description", "")[:200])
chs = list({d["ch"] for d in vids.values()})
cinfo = {}
for k in range(0, len(chs), 50):
    for c in yt.channels().list(part="snippet,statistics", id=",".join(chs[k:k+50])).execute()["items"]:
        cinfo[c["id"]] = dict(subs=int(c["statistics"].get("subscriberCount", 0)), nvid=int(c["statistics"].get("videoCount", 0)),
                              created=c["snippet"]["publishedAt"][:10], country=c["snippet"].get("country"))
for d in vids.values():
    d.update({"ch_" + k: v for k, v in cinfo.get(d["ch"], {}).items()})
json.dump(vids, open(OUT, "w"), indent=1, ensure_ascii=False)
print("queries", len(Q), "videos", len(vids), "channels", len(cinfo))
