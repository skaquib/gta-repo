"""
trend_watch.py — what is breaking out in our niche right now (run weekly by the daily check).

Finds English medium/long videos published in the last N days (default 30) for our niche's
queries, keeps the "small-channel explainer breakouts" (>= 100K views, channel < 100K subs,
no vlogs/challenges/gaming) and writes a dated report with titles, length and chapter
structure to notes/trends/YYYY-MM-DD.md, so new topics and formats feed the next scripts
(VIRAL_PLAYBOOK.md). Costs ~2,500 of the 10,000 daily API quota units, so run it once a
week, never on an upload-heavy day.

  python trend_watch.py [days]
"""
import datetime
import os
import re
import statistics as st
import sys
import warnings

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

QUERIES = {
    "deep sea": ["deep sea creatures", "deep ocean animals explained", "what lives at the bottom of the ocean"],
    "predators": ["most dangerous animals", "animals that could kill you", "apex predator explained"],
    "prehistoric": ["prehistoric animals", "prehistoric ocean monsters", "ice age animals"],
    "scale / size": ["animal size comparison", "biggest animals ever", "animals to scale"],
}
NOISE = re.compile(r"minecraft|roblox|blox|\blive\b|vlog|camping|i caught|i tested|i got|i cooked|i found|i secretly|"
                   r"challenge|asmr|full episode|cleaning|timelapse|harvesting|bushcraft|fishing", re.I)


def _secs(d):
    m = re.match(r"P(?:\d+D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", d)
    h, mi, s = (int(x or 0) for x in m.groups())
    return h * 3600 + mi * 60 + s


def _chapters(desc):
    ch = re.findall(r"^\s*\(?(\d{1,2}:\d{2}(?::\d{2})?)\)?\s*[-–—]?\s*(.+)$", desc or "", re.M)
    return [c[1].strip()[:45] for c in ch] if len(ch) >= 3 else []


def scan(days=30):
    import phase5_upload as p5
    from googleapiclient.discovery import build
    yt = build("youtube", "v3", credentials=p5.get_credentials())
    after = (datetime.datetime.utcnow() - datetime.timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    now = datetime.datetime.utcnow()
    out = {}
    for niche, qs in QUERIES.items():
        ids = []
        for q in qs:
            for dur in ("medium", "long"):
                r = yt.search().list(part="id", q=q, type="video", order="viewCount", publishedAfter=after,
                                     videoDuration=dur, maxResults=15, relevanceLanguage="en").execute()["items"]
                ids += [i["id"]["videoId"] for i in r if i["id"]["videoId"] not in ids]
        vids = []
        for k in range(0, len(ids), 50):
            vids += yt.videos().list(part="snippet,statistics,contentDetails", id=",".join(ids[k:k + 50])).execute()["items"]
        chs = {}
        cids = list({v["snippet"]["channelId"] for v in vids})
        for k in range(0, len(cids), 50):
            for c in yt.channels().list(part="snippet,statistics", id=",".join(cids[k:k + 50])).execute()["items"]:
                chs[c["id"]] = c
        rows = []
        for v in vids:
            c, title = chs.get(v["snippet"]["channelId"]), v["snippet"]["title"]
            if not c or NOISE.search(title) or re.search(r"[^\x00-\x7F‘’“”—–…]", title):
                continue
            views, subs = int(v["statistics"].get("viewCount", 0)), int(c["statistics"].get("subscriberCount", 0))
            if views < 100_000 or subs >= 100_000:
                continue
            age = max(1, (now - datetime.datetime.fromisoformat(v["snippet"]["publishedAt"][:19])).days)
            rows.append(dict(title=title, views=views, vpd=views // age, subs=subs, ch=c["snippet"]["title"],
                             dur=_secs(v["contentDetails"]["duration"]), chapters=_chapters(v["snippet"].get("description"))))
        out[niche] = sorted(rows, key=lambda r: -r["vpd"])
    return out


def write_report(data, days):
    day = datetime.date.today().isoformat()
    path = os.path.join(HERE, "notes", "trends", f"{day}.md")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    lines = [f"# Niche breakouts, last {days} days (run {day})", "",
             "Small-channel explainer breakouts: 100K+ views, channel under 100K subscribers. Sorted by views per day.",
             "Use these for topics and formats, never copy a title.", ""]
    for niche, rows in data.items():
        lines.append(f"## {niche}: {len(rows)} breakouts" + (f", median length {int(st.median(r['dur'] for r in rows) / 60)} min" if rows else ""))
        for r in rows[:8]:
            lines.append(f"- {r['vpd']:,}/day, {r['views']:,} views, {r['subs']:,} subs, {r['dur'] // 60} min: "
                         f"\"{r['title']}\" ({r['ch']})" + (f"\n  chapters: {' / '.join(r['chapters'][:8])}" if r['chapters'] else ""))
        lines.append("")
    open(path, "w").write("\n".join(lines))
    return path


if __name__ == "__main__":
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    print("report:", write_report(scan(days), days))
