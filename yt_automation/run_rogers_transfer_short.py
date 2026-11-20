"""
run_rogers_transfer_short.py — SECOND video for 2026-07-29, explicitly
requested by the channel owner after being warned this overrides the
same-day publish guard (the guard exists because a 12-video same-day
cluster on 2026-07-02 triggered this channel's algorithmic suppression).

Story: Chelsea signed Morgan Rogers from Aston Villa for a British-record
£117m -- breaking the record Manchester City set just three weeks earlier
with Elliot Anderson. Real, fresh, verified transfer news.

This script monkeypatches phase5_upload.reserve_publish_slot() in-process
so THIS run publishes immediately today instead of being shifted to
tomorrow. It does not modify phase5_upload.py on disk, so every future
script import gets the real, unmodified guard back -- this is a one-time,
explicitly-authorized exception, not a permanent weakening.
"""
import os
import datetime
import config

config.assert_safe_pipeline()

import phase5_upload as p5
import pro_shorts_creator as psc
import copyright_compliance as cc
from logger import log

_original_reserve = p5.reserve_publish_slot


def _reserve_today_override(preferred: datetime.datetime = None) -> datetime.datetime:
    """One-time override: publish at the preferred (now) moment even if
    today is already claimed. Still records today's date in the ledger via
    the original function's bookkeeping semantics, so tomorrow's guard
    behaves normally again."""
    preferred = preferred or datetime.datetime.now(datetime.timezone.utc)
    ledger = p5._load_publish_ledger()
    ledger.add(preferred.strftime("%Y-%m-%d"))
    p5._save_publish_ledger(ledger)
    log("Phase 5: same-day guard EXPLICITLY OVERRIDDEN for this run (user-authorized 2nd video today)")
    return preferred


p5.reserve_publish_slot = _reserve_today_override

SCRIPT = {
    "hook": "Two British transfer records. Broken three weeks apart.",
    "body": (
        "Manchester City set a new British transfer record signing Elliot "
        "Anderson. Three weeks later, Chelsea broke it -- by just one "
        "million pounds -- signing Morgan Rogers from Aston Villa for one "
        "hundred and seventeen million pounds. Rogers is only twenty-three. "
        "Last season he had twenty-five goals and assists, won the Europa "
        "League with Villa, and played for England at the World Cup. Now "
        "he's a record signing at Stamford Bridge."
    ),
    "cta": "Was Chelsea right to break the bank for Rogers? Comment your take and subscribe!",
    "title": "Chelsea Broke the British Transfer Record -- Again #shorts",
    "tags": ["chelsea", "morganrogers", "astonvilla", "transfer", "premierleague", "football", "soccer", "shorts", "viral"],
    "seo_description": "Chelsea signed Morgan Rogers for a British-record £117m, breaking the record Manchester City set just three weeks earlier. #chelsea #transfer #premierleague",
    "queries": ["soccer stadium fans", "football training session", "soccer player celebration"],
}


def main():
    log("Downloading real stock footage (tag-verified, cross-video deduped)...")
    clip_paths = psc.download_clips(SCRIPT)

    log("Generating voiceover (cloned voice + persona sign-off)...")
    vo_path = psc.generate_voiceover(SCRIPT)

    log("Generating background music...")
    music_path = psc.get_music(duration=26.0)

    log("Running compliance check...")
    check = cc.validate_before_upload(SCRIPT, clip_paths, music_path)
    cc.save_compliance_report(check, video_id="rogers_transfer_short")
    if not check["passed"]:
        log(f"COMPLIANCE FAILED: {check['issues']}")
        return
    for w in check["warnings"]:
        log(f"  Warning: {w}")

    out_path = os.path.join(config.VIDEOS_DIR, "rogers_transfer_short.mp4")
    log(f"Assembling video -> {out_path}")
    psc.assemble(clip_paths, SCRIPT, vo_path, music_path, out_path)

    log("Uploading...")
    url = psc.upload(out_path, SCRIPT, vo_path)
    if url:
        log(f"DONE — live at {url}")
    else:
        log("Upload did not return a URL — check logs above.")


if __name__ == "__main__":
    main()
