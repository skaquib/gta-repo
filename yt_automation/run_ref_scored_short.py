"""
run_ref_scored_short.py — 2026-09-11. "SOUNDS FAKE. 100% REAL." episode 4.

PRE-PUSH CHECKLIST (standing rule: pre-push-viral-research)
1. OUR RESULTS (pulled 2026-09-11) -- this drove the topic choice:
     Three Yellow Cards  (Sounds Fake ep.2, absurd MOMENT) = 843 views  <- best
     Arsenal -> Barcelona (news)                           = 541
     Coin Flip           (Sounds Fake ep.1, absurd MOMENT) = 385
     78% Is A Lie        (Sounds Fake ep.3, STATISTIC)     =   8  <- worst
   Clear split: absurd MOMENTS land, statistic-debunking does not. Episode 4
   is therefore a moment, not a number. Do not repeat the stat format.
2. NOT A REPEAT: no prior video on referees scoring, Turkish football, or
   Law 9. Not a transfer, not tennis, not a measurement explainer.
3. FORMAT: ~21-25s band (our data: 117.4% retention vs 38.7% at 31-35s),
   top-third hook card, series framing for return viewers.

VERIFIED (2026-09-11, ETV Bharat, Goal.com Turkey, Sportskeeda):
21 September 1986, Turkish 1. Lig week 5, Cebeci Inonu Stadium, Ankaragucu
v Besiktas. The ball struck referee Ahmet Akcay standing at the back post
and deflected into the net. Under the laws of the time the referee counted
as part of the field of play, so the goal STOOD. Besiktas lost; that season
Galatasaray won the title by ONE point over Besiktas, ending a 14-year
drought. IFAB changed Law 9 in 2019: a ball touching the referee that then
enters the goal is now a dropped ball, not a goal.

LENGTH: 42 script words + 9-word persona sign-off = 51, at the MEASURED
2.06 words/sec = ~24.8s.
"""
import os
import config

config.assert_safe_pipeline()

import pro_shorts_creator as psc
import copyright_compliance as cc
from logger import log

SCRIPT = {
    "hook": "Subscribe. A referee scored a goal -- and it counted.",
    "hook_card": "THE REF SCORED",
    "body": (
        "1986. The ball hit referee Ahmet Akcay and went in. The "
        "referee counted as part of the pitch, so it stood. "
        "Besiktas lost the title by a point."
    ),
    "cta": "Rule changed in 2019. Comment!",
    "title": "A Referee Scored a Goal -- And It Counted #shorts",
    "tags": ["football", "soccer", "referee", "besiktas", "shorts", "viral",
             "soundsfake", "sportsfacts", "turkishfootball"],
    "seo_description": (
        "In 1986 the ball hit referee Ahmet Akcay and went in -- and the goal "
        "stood, because back then the referee counted as part of the pitch. "
        "Besiktas lost the title by one point. IFAB changed the law in 2019."
    ),
    "queries": ["soccer referee match", "football stadium crowd", "soccer goal net"],
}


def build():
    clip_paths = psc.download_clips(SCRIPT)
    vo_path = psc.generate_voiceover(SCRIPT)
    from moviepy import AudioFileClip
    d = AudioFileClip(vo_path).duration
    log(f"VOICEOVER LENGTH: {d:.1f}s (target 21-25s)")
    music_path = psc.get_music(duration=min(d + 1.5, 90.0), script=SCRIPT)
    check = cc.validate_before_upload(SCRIPT, clip_paths, music_path)
    cc.save_compliance_report(check, video_id="ref_scored_short")
    if not check["passed"]:
        raise RuntimeError(f"COMPLIANCE FAILED: {check['issues']}")
    out_path = os.path.join(config.VIDEOS_DIR, "ref_scored_short.mp4")
    psc.assemble(clip_paths, SCRIPT, vo_path, music_path, out_path)
    log(f"BUILD COMPLETE -> {out_path}")
    print("VO_PATH=" + vo_path)
    return out_path, vo_path


if __name__ == "__main__":
    build()
