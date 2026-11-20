"""Publish the invisible-trophy Short LIVE immediately, linked to today's
Asia Cup documentary (Jf0CLeDQNfA) so Short viewers can find the full story.
Run only after the render has been verified."""
import os
import sys

import config

config.VIDEO_TYPE = "shorts"
config.VISUAL_STYLE = "footage"
config.SCHEDULE_MODE = "immediate"
config.assert_safe_pipeline()

import phase5_upload as p5
import publish_optimized as po
import pro_shorts_creator as psc
from run_invisible_trophy_short import SCRIPT

VID = os.path.join(config.VIDEOS_DIR, "invisible_trophy_short.mp4")

if __name__ == "__main__":
    vo = sys.argv[1]
    assert os.path.exists(VID), VID
    assert os.path.exists(vo), vo
    topic = {"title": SCRIPT["title"], "subject": SCRIPT["seo_description"], "category": "Sports"}
    url, is_public = p5.upload_to_youtube(VID, SCRIPT, topic)
    vid = url.rsplit("=", 1)[1]
    print("VIDEO_ID", vid, "public_now", is_public)

    try:
        words = psc.get_word_timestamps(vo)
        srt = os.path.splitext(vo)[0] + ".srt"
        psc.generate_srt(words, srt)
        print("captions:", bool(p5.upload_captions(vid, srt)))
    except Exception as e:
        print("captions failed:", e)

    result = po.apply_all(
        vid, SCRIPT, VID,
        thumb_line1="INVISIBLE", thumb_line2="TROPHY",
        playlist_name="Sounds Fake. 100% Real.",
        related_id="Jf0CLeDQNfA",
        related_title="India Won the Asia Cup Twice. Both Times, They Refused the Trophy",
        sources=["2025 Asia Cup -- Wikipedia",
                 "Asia Cup 2025: India refuses to receive trophy from Mohsin Naqvi -- Forbes",
                 "India refuse to accept Women's Asia Cup trophy from Mohsin Naqvi -- The National",
                 # CC BY / CC BY-SA require crediting the photographers.
                 *[v["attribution"] for v in __import__("json").load(open(
                     os.path.join(config.OUTPUT_DIR, "trophy_short_photos.json"),
                     encoding="utf-8")).values() if v]],
        make_public=True,
    )
    print(result)
    print("URL", url)
