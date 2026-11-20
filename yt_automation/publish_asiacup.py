"""Publish documentary #5 (Asia Cup trophy refusals) LIVE immediately.
Run only after verify_doc.py passes and the frames have been checked."""
import os

import config

config.VIDEO_TYPE = "long"
config.VISUAL_STYLE = "footage"
config.SCHEDULE_MODE = "immediate"
config.assert_safe_pipeline()

import phase5_upload as p5
import publish_optimized as po
import pro_shorts_creator as psc
from doc_asiacup import SCRIPT

OUT = os.path.join(config.VIDEOS_DIR, "doc_asiacup.mp4")
VO = open(os.path.join(config.OUTPUT_DIR, "asiacup_vo_path.txt")).read().strip()

SCRIPT_DICT = {
    "video_title": SCRIPT.title,
    "seo_description": SCRIPT.description,
    "tags": list(SCRIPT.tags),
    "hook": SCRIPT.hook_card,
    "body": SCRIPT.description,
    "cta": "Was India right to refuse the Asia Cup trophy? Tell us why.",
}

if __name__ == "__main__":
    assert os.path.exists(OUT), OUT
    assert os.path.exists(VO), VO
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
        thumb_line1="THEY WON", thumb_line2="BUT REFUSED IT",
        playlist_name="Sounds Fake. 100% Real.",
        related_id="3gUA65u-bpk",
        related_title="Why Is a Cricket Over EXACTLY 6 Balls?",
        sources=list(SCRIPT.sources),
        make_public=True,
    )
    print(result)
    print("URL", url)
