"""
run_batch_5_shorts.py — Produce 5 distinct Shorts today, fully free
(real Pixabay stock footage + cloned voice -- higher visual quality than
local AnimateDiff), and upload each with a staggered publishAt (today, +1d,
+2d, +3d, +4d) so nothing clusters into a single-day spam pattern -- the
exact behavior that triggered this channel's suppression on July 2nd.
One new video per day, same pipeline as Fontaine/Pele/Neymar.
"""
import datetime
import os

import config

config.VISUAL_STYLE = "footage"  # real Pixabay stock clips, not AI-generated
config.assert_safe_pipeline()

import pro_shorts_creator as psc
import visual_shorts_creator as vsc
import copyright_compliance as cc
import phase5_upload as p5
from logger import log

SCRIPTS = [
    {
        "id": "crazy_moments",
        "hook": "5 things happened at World Cup 2026 that nobody expected.",
        "body": (
            "A duck named Merlin became Mexico's official good-luck charm. "
            "A German tourist named Freddy became more famous than half the players. "
            "Fans from three continents bonded over gas-station Twinkies. "
            "Korean and Mexican fans became the internet's favorite friendship. "
            "And Germany won a match 7-1 -- and broke the internet doing it."
        ),
        "cta": "Which one did YOU see first? Comment below and subscribe for more!",
        "title": "5 CRAZIEST Moments From World Cup 2026 (You Missed These) #shorts #worldcup2026",
        "tags": ["worldcup2026", "viral", "funny", "football", "soccer", "shorts", "trending", "fifa"],
        "seo_description": "The 5 wildest, funniest moments from World Cup 2026 so far. #worldcup2026 #viral #football",
        "queries": ["soccer stadium crowd", "soccer fans celebration", "football stadium fireworks"],
    },
    {
        "id": "48_teams_record",
        "hook": "48 teams. One tournament. Nothing like this has ever happened.",
        "body": (
            "World Cup 2026 is the first in history with 48 teams -- up from just 32. "
            "That's 104 matches total, across three countries, in one summer. "
            "More nations get a shot at glory than ever before. "
            "It's the biggest World Cup ever played, by a massive margin."
        ),
        "cta": "Good change or bad change? Comment your take and subscribe for more!",
        "title": "Why World Cup 2026 Is Unlike Any Before It #shorts #worldcup2026 #football",
        "tags": ["worldcup2026", "football", "record", "history", "shorts", "soccer", "fifa", "viral"],
        "seo_description": "World Cup 2026 just became the biggest tournament in football history. #worldcup2026 #football #history",
        "queries": ["soccer stadium aerial view", "football stadium flags", "soccer stadium crowd cheering"],
    },
    {
        "id": "germany_7_1",
        "hook": "7 goals. 1 reply. The internet could not handle this scoreline.",
        "body": (
            "Germany didn't just win their World Cup 2026 group match -- they demolished it, 7-1. "
            "It was one of the most one-sided scorelines of the entire tournament. "
            "Social media exploded with over 25,000 posts within hours. "
            "Their opponents never had an answer."
        ),
        "cta": "Most one-sided scoreline you've ever seen? Comment and subscribe!",
        "title": "Germany's 7-1 Scoreline Broke The Internet #shorts #worldcup2026 #germany",
        "tags": ["worldcup2026", "germany", "football", "shorts", "soccer", "viral", "fifa", "shock"],
        "seo_description": "Germany's 7-1 World Cup 2026 win was one of the most dominant scorelines of the tournament. #worldcup2026 #germany",
        "queries": ["soccer goal celebration", "football stadium scoreboard", "soccer crowd celebration"],
    },
    {
        "id": "freddy_tourist",
        "hook": "He hasn't kicked a single ball. He's still one of the World Cup's biggest stars.",
        "body": (
            "A German tourist named Freddy set out to see every host city of World Cup 2026. "
            "He documented every stop -- the food, the fans, the chaos. "
            "Within weeks, he had hundreds of thousands of followers. "
            "He never played a minute, and he became part of the tournament's story anyway."
        ),
        "cta": "Would you go on a trip like this? Comment and subscribe for more!",
        "title": "The Tourist Who Became a World Cup 2026 Star #shorts #worldcup2026 #viral",
        "tags": ["worldcup2026", "viral", "travel", "football", "shorts", "funny", "fifa", "trending"],
        "seo_description": "How one tourist's World Cup 2026 road trip made him internet-famous. #worldcup2026 #viral #travel",
        "queries": ["football fan travel", "soccer stadium tourist", "soccer fans photos"],
    },
    {
        "id": "merlin_duck",
        "hook": "One country adopted a duck as their official good-luck charm.",
        "body": (
            "After Mexico's opening World Cup 2026 win, fans spotted a duck near the stadium. "
            "They named him Merlin. "
            "Clips of him went viral, racking up millions of views. "
            "Now fans track his every appearance like he's part of the squad."
        ),
        "cta": "Best sports mascot moment you've ever seen? Comment and subscribe!",
        "title": "How a Duck Became World Cup 2026's Biggest Good-Luck Charm #shorts #worldcup2026",
        "tags": ["worldcup2026", "viral", "funny", "mexico", "shorts", "cute", "fifa", "trending"],
        "seo_description": "Meet Merlin, the duck who became Mexico's unofficial World Cup 2026 mascot. #worldcup2026 #viral #funny",
        "queries": ["duck bird nature", "soccer fans smiling", "soccer stadium crowd happy"],
    },
]


def compute_schedule(n: int) -> list:
    """One publish slot per day starting now, so nothing clusters same-day."""
    base = datetime.datetime.now(datetime.timezone.utc)
    return [base + datetime.timedelta(days=i) for i in range(n)]


def run_one(script: dict, publish_at: datetime.datetime):
    log(f"=== Producing '{script['id']}' (scheduled {publish_at.isoformat()}) ===")

    clip_paths = vsc.download_clips(script)
    vo_path = psc.generate_voiceover(script)
    music_path = psc.get_music(duration=26.0)

    check = cc.validate_before_upload(script, clip_paths, music_path)
    cc.save_compliance_report(check, video_id=script["id"])
    if not check["passed"]:
        log(f"COMPLIANCE FAILED for {script['id']}: {check['issues']}")
        return None

    out_path = os.path.join(config.VIDEOS_DIR, f"{script['id']}.mp4")
    psc.assemble(clip_paths, script, vo_path, music_path, out_path)

    # Pin this video's exact publishAt regardless of match_calendar state.
    original_compute = p5._compute_publish_at
    p5._compute_publish_at = lambda: p5._to_rfc3339(publish_at)
    try:
        url = psc.upload(out_path, script, vo_path)
    finally:
        p5._compute_publish_at = original_compute

    log(f"'{script['id']}' -> {url or 'FAILED'} (publishAt {publish_at.isoformat()})")
    return url


def main():
    config.SCHEDULE_MODE = "scheduled"
    schedule = compute_schedule(len(SCRIPTS))
    results = {}
    for script, publish_at in zip(SCRIPTS, schedule):
        try:
            results[script["id"]] = run_one(script, publish_at)
        except Exception as e:
            log(f"ERROR producing {script['id']}: {e}")
            results[script["id"]] = None

    log("=== BATCH SUMMARY ===")
    for sid, url in results.items():
        log(f"  {sid}: {url or 'FAILED'}")


if __name__ == "__main__":
    main()
