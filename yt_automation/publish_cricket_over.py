"""Publish today's cricket-over Short LIVE immediately (owner asked for live,
not scheduled). Run only after the render has been verified."""
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
from run_cricket_over_short import SCRIPT

VID = os.path.join(config.VIDEOS_DIR, "cricket_over_short.mp4")

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
        thumb_line1="WHY 6", thumb_line2="BALLS?",
        playlist_name="Sounds Fake. 100% Real.",
        related_id="Khve3d6P17U",
        related_title="Why Is a Football Match EXACTLY 90 Minutes?",
        sources=["Over (cricket) -- Wikipedia",
                 "From 4 to 6 balls: the history of length of overs -- sportsdigest.in",
                 "Cricket once had 8-ball overs -- Sunday Guardian"],
        make_public=True,
    )
    print(result)
    print("URL", url)
