"""
topic_validate.py — Proven-demand check for topic ideas BEFORE production.

For each (label, query): YouTube Shorts from the last 365 days, ranked by
views. A topic is "proven" when a version has already broken out; how many
1M+ versions exist shows how crowded it is; Devanagari titles show whether a
Hindi audience is already watching it. Topics are not owned -- we make our
own version (own research, script and visuals), never a copy of another
channel's video (YouTube reused/inauthentic content rules).

Quota: ~101 units per topic. Writes output/research/topic_validation_<ts>.json.

Usage: python topic_validate.py [key1,key2,...] [--long]   (default: every topic in TOPICS)
--long checks 4-20 minute videos instead of Shorts (long-form demand).
Only titles matching a topic's "must" keyword groups count toward its numbers.
"""
import re
import json
import datetime

import phase5_upload as p5
from googleapiclient.discovery import build

DEVANAGARI = re.compile(r"[ऀ-ॿ]")

# Each topic: key, category, label, search query, and "must" -- keyword groups
# that the TITLE has to match (one word from every group), so broad queries
# don't count unrelated hits. (Found 2026-10-24: "what's inside a football"
# returned a 484M stadium video; "cow stomach" returned a butchering video.)
TOPICS = [
    # animals
    dict(key="snake_egg", cat="Animals", label="A snake swallowing an egg bigger than its head",
         q="snake swallows egg inside", must=[["snake", "सांप"], ["egg", "अंडा"]]),
    dict(key="cow_stomach", cat="Animals", label="How a cow's 4 stomachs digest grass",
         q="how cow digests food 4 stomachs", must=[["cow", "गाय"], ["stomach", "digest", "पेट", "rumen"]]),
    dict(key="camel_hump", cat="Animals", label="What's really inside a camel's hump",
         q="what is inside a camel hump", must=[["camel", "ऊंट", "উট"], ["hump", "कूबड़", "কুঁজ"]]),
    dict(key="chick_egg", cat="Animals", label="How a chick grows inside the egg",
         q="how chick grows inside egg", must=[["chick", "चूजा"], ["egg", "अंडे"]]),
    dict(key="bees_honey", cat="Animals", label="How bees make honey", q="how bees make honey inside",
         must=[["bee", "मधुमक्खी"], ["honey", "शहद"]]),
    dict(key="fish_gills", cat="Animals", label="How fish breathe underwater", q="how fish breathe underwater gills",
         must=[["fish", "मछली"], ["breathe", "gill", "सांस"]]),
    dict(key="elephant_trunk", cat="Animals", label="How an elephant's trunk works", q="how elephant trunk works",
         must=[["trunk", "सूंड"], ["elephant", "हाथी"]]),
    dict(key="octopus_colour", cat="Animals", label="How an octopus changes colour", q="how octopus changes color skin",
         must=[["octopus"], ["color", "colour", "camouflage", "skin"]]),
    dict(key="spider_silk", cat="Animals", label="How a spider makes silk", q="how spider makes silk inside",
         must=[["spider", "मकड़ी"], ["silk", "web", "जाल"]]),
    dict(key="woodpecker", cat="Animals", label="Why woodpeckers don't get headaches", q="why woodpecker doesn't get headache",
         must=[["woodpecker", "कठफोड़वा"]]),
    dict(key="mosquito_needles", cat="Animals", label="A mosquito bite uses six needles",
         q="mosquito bite 6 needles inside skin", must=[["mosquito", "मच्छर"], ["needle", "bite", "skin", "blood", "inside"]]),
    dict(key="strange_eggs", cat="Animals", label="The strangest animal eggs", q="strangest animal eggs",
         must=[["egg", "अंडे", "अंडा"], ["strange", "weird", "unusual", "craziest", "अजीब"]]),
    dict(key="kiwi_egg", cat="Animals", label="The kiwi bird's giant egg", q="kiwi bird giant egg x-ray",
         must=[["kiwi"], ["egg"]]),
    dict(key="catfish_cuckoo", cat="Animals", label="The cuckoo catfish tricks fish into raising its babies",
         q="cuckoo catfish eggs mouthbrooder", must=[["catfish"], ["egg", "baby", "babies", "trick", "cuckoo"]]),
    # long-form animal <-> human questions (2026-11-02, Quark case study; check with --long)
    dict(key="lf_dogs_sad", cat="Long", label="Do dogs know when you're sad?", q="do dogs know when you are sad",
         must=[["dog", "pet"], ["sad", "feel", "emotion", "cry"]]),
    dict(key="lf_dream", cat="Long", label="Do animals dream?", q="do animals dream", must=[["animal", "dog", "cat"], ["dream"]]),
    dict(key="lf_mirror", cat="Long", label="Do animals recognize themselves in a mirror?", q="do animals recognize themselves in mirror",
         must=[["animal", "dog", "cat"], ["mirror"]]),
    dict(key="lf_jealous", cat="Long", label="Do animals get jealous?", q="do animals get jealous", must=[["animal", "dog", "cat", "pet"], ["jealous"]]),
    dict(key="lf_talk", cat="Long", label="What would animals say if they could talk?", q="what would animals say if they could talk",
         must=[["animal", "dog", "cat"], ["talk", "speak", "say"]]),
    dict(key="lf_pain", cat="Long", label="Do animals feel pain like we do?", q="do animals feel pain like humans",
         must=[["animal", "fish", "insect"], ["pain"]]),
    dict(key="lf_dog_think", cat="Long", label="What do dogs think about all day?", q="what do dogs think about",
         must=[["dog"], ["think", "mind", "brain"]]),
    dict(key="lf_cat_think", cat="Long", label="What do cats think of their owners?", q="what do cats think of their owners",
         must=[["cat"], ["think", "owner", "human"]]),
    dict(key="lf_remember", cat="Long", label="Do animals remember people?", q="do animals remember people who were kind",
         must=[["animal", "dog", "cat", "elephant", "crow"], ["remember", "memory", "forget"]]),
    dict(key="lf_love", cat="Long", label="Can animals feel love?", q="can animals feel love", must=[["animal", "dog", "cat"], ["love"]]),
    dict(key="chrysalis", cat="Animals", label="What happens inside a chrysalis (caterpillar turns to soup)",
         q="what happens inside a chrysalis caterpillar butterfly", must=[["chrysalis", "cocoon", "caterpillar", "pupa"],
                                                                         ["inside", "butterfly", "soup", "turn"]]),
    dict(key="pearl", cat="Animals", label="How a pearl forms inside an oyster", q="how pearls are formed inside oyster",
         must=[["pearl", "मोती"], ["oyster", "form", "made", "inside", "बनता"]]),
    dict(key="egg_sizes", cat="Animals", label="Egg sizes: smallest to biggest bird egg", q="smallest vs biggest egg in the world",
         must=[["egg", "अंडा"], ["biggest", "largest", "smallest", "size", "compare", "comparison"]]),
    dict(key="woodpecker_tongue", cat="Animals", label="A woodpecker's tongue wraps around its skull",
         q="woodpecker tongue wraps around skull", must=[["woodpecker"], ["tongue", "skull", "brain"]]),
    dict(key="pufferfish", cat="Animals", label="What happens inside a pufferfish when it puffs up",
         q="how pufferfish inflate inside", must=[["puffer", "blowfish"], ["inflate", "puff", "inside", "how", "why"]]),
    dict(key="frog_eyes", cat="Animals", label="Frogs use their eyes to swallow", q="frogs use their eyes to swallow",
         must=[["frog", "मेंढक"], ["eye", "swallow", "आंख"]]),
    dict(key="starfish_stomach", cat="Animals", label="A starfish pushes its stomach out to eat",
         q="starfish stomach outside body eating", must=[["starfish", "sea star"], ["stomach", "eat"]]),
    dict(key="snake_jaw", cat="Animals", label="How a snake swallows prey bigger than its head",
         q="how snake swallows prey bigger than head jaw", must=[["snake", "python", "सांप"], ["swallow", "jaw", "eat", "निगल"]]),
    dict(key="snake_digest", cat="Animals", label="What happens inside a python after it eats",
         q="what happens inside python after eating digest", must=[["python", "snake"], ["inside", "digest", "after"]]),
    dict(key="giraffe_heart", cat="Animals", label="How a giraffe pumps blood up its neck",
         q="giraffe heart blood neck how", must=[["giraffe"], ["heart", "blood", "neck"]]),
    # how things work
    dict(key="pen_glue", cat="How it works", label="Ballpoint pen: why new pens have glue on the tip", q="how ballpoint pen works",
         must=[["pen"], ["why", "how", "inside", "ink", "glue"]]),
    dict(key="lock_key", cat="How it works", label="How a lock works inside", q="how a lock works inside pin tumbler",
         must=[["lock"], ["how", "inside", "works", "pin"]]),
    dict(key="fridge", cat="How it works", label="How a fridge makes cold", q="how refrigerator works explained",
         must=[["fridge", "refrigerator", "फ्रिज"], ["how", "works", "कैसे", "cold", "ठंडा"]]),
    dict(key="ac", cat="How it works", label="How an AC makes cold air", q="how AC works explained",
         must=[["air conditioner", "how ac", "ac work", "ac kaise", "एसी", "ac kaam"]]),
    dict(key="pressure_cooker", cat="How it works", label="Pressure cooker: why it whistles",
         q="how pressure cooker works whistle science",
         must=[["pressure cooker", "कुकर", "cooker"], ["how", "why", "works", "whistle", "सीटी", "कैसे", "क्यों"]]),
    dict(key="ceiling_fan", cat="How it works", label="What's inside a ceiling fan", q="how ceiling fan works inside",
         must=[["fan", "पंखा"], ["how", "inside", "works", "कैसे"]]),
    dict(key="toilet_flush", cat="How it works", label="How a toilet flush works", q="how toilet flush works",
         must=[["toilet", "flush"], ["how", "works", "inside"]]),
    # food science (no health claims)
    dict(key="chocolate", cat="Food science", label="How chocolate is made from cocoa", q="how chocolate is made from cocoa",
         must=[["chocolate", "चॉकलेट"], ["made", "cocoa", "cacao", "factory", "बनती"]]),
    dict(key="onion_cry", cat="Food science", label="Why onions make you cry", q="why onions make you cry science",
         must=[["onion", "प्याज"], ["cry", "tear", "आंसू", "रुला"]]),
    dict(key="popcorn", cat="Food science", label="Why popcorn pops", q="why popcorn pops science",
         must=[["popcorn"], ["pop", "why", "how", "inside", "science"]]),
    # body curiosities (explanations, not health advice)
    dict(key="yawn", cat="Body curiosity", label="Why we yawn", q="why do we yawn explained",
         must=[["yawn", "उबासी", "जम्हाई"]]),
    dict(key="hiccup", cat="Body curiosity", label="Why we hiccup", q="why do we hiccup explained",
         must=[["hiccup", "हिचकी"]]),
    dict(key="knuckles", cat="Body curiosity", label="What happens when you crack your knuckles", q="what happens when you crack knuckles",
         must=[["knuckle"]]),
    dict(key="goosebumps", cat="Body curiosity", label="Why we get goosebumps", q="why do we get goosebumps",
         must=[["goosebump", "रोंगटे", "tüy"]]),
    dict(key="sneeze", cat="Body curiosity", label="What happens when you sneeze", q="what happens when you sneeze inside body",
         must=[["sneeze", "छींक"]]),
    # sports objects (keeps a sports link)
    dict(key="football_inside", cat="Sports object", label="What's inside a football", q="what is inside a football ball cut open",
         must=[["football", "soccer ball"], ["inside", "cut open", "made", "बनता"]]),
    dict(key="cricket_ball", cat="Sports object", label="How a cricket ball is made", q="how cricket ball is made factory",
         must=[["cricket ball", "क्रिकेट बॉल"], ["made", "factory", "inside", "बनती", "बनता"]]),
    dict(key="gk_gloves_made", cat="Sports object", label="How goalkeeper gloves are made", q="how goalkeeper gloves are made factory",
         must=[["goalkeeper", "goalie"], ["glove"]]),
    dict(key="cricket_bat", cat="Sports object", label="How a cricket bat is made", q="how cricket bat is made factory",
         must=[["bat", "बैट"], ["made", "factory", "बनता", "बनती", "willow"]]),
    dict(key="shuttlecock", cat="Sports object", label="How a shuttlecock is made", q="how shuttlecock is made feathers factory",
         must=[["shuttle"], ["made", "factory", "feather", "बनती"]]),
    dict(key="tennis_ball", cat="Sports object", label="How tennis balls are made", q="how tennis balls are made factory",
         must=[["tennis ball"], ["made", "factory", "inside"]]),
    dict(key="football_made", cat="Sports object", label="How a football is made", q="how footballs are made factory",
         must=[["football", "soccer ball"], ["made", "factory", "stitch", "बनता", "बनती"]]),
    dict(key="basketball_made", cat="Sports object", label="How a basketball is made", q="how basketball is made factory",
         must=[["basketball"], ["made", "factory"]]),
    # Dummy Tests as survival stories (2026-11-10, owner: "story wise ... people get attached till end")
    dict(key="car_water", cat="Survival", label="Escaping a car sinking in water",
         q="escape sinking car underwater", must=[["car"], ["sink", "water", "underwater", "drown", "flood", "lake", "river"]]),
    dict(key="train_tracks", cat="Survival", label="Car stalled on train tracks, train coming",
         q="car stuck on railroad tracks train coming", must=[["train", "railroad", "railway", "tracks"], ["car", "stuck", "stall"]]),
    dict(key="lava", cat="Survival", label="What happens if you fall into lava (viewer's pick)",
         q="what happens if you fall into lava", must=[["lava"]]),
    dict(key="elevator", cat="Survival", label="Falling elevator: does jumping save you?",
         q="falling elevator jump survive", must=[["elevator", "lift"], ["fall", "jump", "drop", "snap", "cable"]]),
    dict(key="avalanche", cat="Survival", label="Buried in an avalanche",
         q="buried in avalanche survive", must=[["avalanche"]]),
]


def _matches(title: str, must) -> bool:
    t = title.lower()
    return all(any(w.lower() in t for w in group) for group in must)


def validate(topics=TOPICS, days=365, duration="short"):
    yt = build("youtube", "v3", credentials=p5.get_credentials())
    now = datetime.datetime.now(datetime.timezone.utc)
    after = (now - datetime.timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows = []
    for tp in topics:
        cat, label, q = tp["cat"], tp["label"], tp["q"]
        try:
            r = yt.search().list(part="snippet", q=q, type="video", videoDuration=duration,
                                 order="viewCount", publishedAfter=after, maxResults=25).execute()
        except Exception as e:
            print(f"search failed for {label}: {str(e)[:120]}")
            break
        ids = [i["id"]["videoId"] for i in r["items"]]
        vids = yt.videos().list(part="statistics,snippet", id=",".join(ids)).execute()["items"] if ids else []
        allv = sorted([(int(v["statistics"].get("viewCount", 0)), v["snippet"]["publishedAt"][:10],
                        v["snippet"]["title"], v["snippet"]["channelTitle"]) for v in vids], reverse=True)
        vs = [v for v in allv if _matches(v[2], tp.get("must", []))]
        rows.append({
            "key": tp["key"], "category": cat, "label": label, "query": q, "duration": duration,
            "results": len(allv), "on_topic": len(vs),
            "top_views": vs[0][0] if vs else 0,
            "top_title": vs[0][2] if vs else "", "top_date": vs[0][1] if vs else "",
            "n_1m": sum(1 for v in vs if v[0] >= 1_000_000),
            "n_100k": sum(1 for v in vs if v[0] >= 100_000),
            "hindi_versions": sum(1 for v in vs if DEVANAGARI.search(v[2])),
            "on_topic_videos": vs,
        })
    rows.sort(key=lambda x: -x["top_views"])
    path = f"output/research/topic_validation_{now.strftime('%Y%m%dT%H%M%SZ')}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=1, ensure_ascii=False)
    return rows, path


if __name__ == "__main__":
    import sys
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    keys = set(args[0].split(",")) if args else None
    rows, path = validate([t for t in TOPICS if not keys or t["key"] in keys],
                          duration="medium" if "--long" in sys.argv else "short")
    print(f"{'top on-topic':>12} {'1M+':>4} {'100k+':>6} {'hindi':>5} {'match':>6}  topic")
    for x in rows:
        print(f"{x['top_views']:>12,} {x['n_1m']:>4} {x['n_100k']:>6} {x['hindi_versions']:>5} "
              f"{x['on_topic']:>2}/{x['results']:<3}  [{x['category']}] {x['label']}  <- {x['top_title'][:42]}")
    print(f"\nSaved: {path}")
