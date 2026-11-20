"""Publish documentary #3 (Garrincha) immediately, fully optimised.

Run only AFTER the rendered file has been verified (duration, black frames,
audio level, frames on-topic, captions in sync).

SCHEDULE_MODE is forced to "immediate": the standing-slot scheduler would
otherwise defer this to the next 12:30/18:00 IST slot. MAX_PER_DAY is left
alone -- it guards against the 2026-07-02 same-day upload cluster that got
this channel suppressed, and one documentary does not come near it.
"""
import os
import config

config.VIDEO_TYPE = "long"
config.VISUAL_STYLE = "footage"
config.SCHEDULE_MODE = "immediate"
config.assert_safe_pipeline()

import phase5_upload as p5
import publish_optimized as po
import pro_shorts_creator as psc
from doc_garrincha import SCRIPT
from resume_garrincha import VO, OUT

SCRIPT_DICT = {
    "video_title": SCRIPT.title,
    "seo_description": SCRIPT.description,
    "tags": list(SCRIPT.tags),
    "hook": SCRIPT.hook_card,
    "body": SCRIPT.description,
    "cta": "Should Garrincha be remembered alongside Pele?",
}

if __name__ == "__main__":
    assert os.path.exists(OUT), OUT
    topic = {"title": SCRIPT.title, "subject": SCRIPT.description, "category": "Sports"}
    url, is_public = p5.upload_to_youtube(OUT, SCRIPT_DICT, topic)
    vid = url.rsplit("=", 1)[1]
    print("VIDEO_ID", vid, "public_now", is_public)

    try:
        words = psc.get_word_timestamps(VO)
        srt = os.path.splitext(VO)[0] + ".srt"
        psc.generate_srt(words, srt)
        print("captions:", bool(p5.upload_captions(vid, srt)))
    except Exception as e:
        print("captions failed:", e)

    result = po.apply_all(
        vid, SCRIPT_DICT, OUT,
        thumb_line1="THEY SAID", thumb_line2="HE'D NEVER WALK",
        playlist_name="Sounds Fake. 100% Real.",
        related_id="20ajg5P3z2k",
        related_title="He Was Playing Football in the Street When They Told Him",
        sources=list(SCRIPT.sources),
        make_public=True,
    )
    print(result)
    print("URL", url)
