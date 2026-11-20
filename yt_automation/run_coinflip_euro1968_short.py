"""
run_coinflip_euro1968_short.py — Built 2026-09-02.

*** FORMAT CHANGE — episode 1 of a new series ***
"SOUNDS FAKE. 100% REAL." — absurd-but-true sports stories.

WHY THE FORMAT CHANGED (research done 2026-09-02, per the standing
pre-push-viral-research checklist):
Every one of the channel's last 25 videos was one of only two templates:
"Why Is a [thing] EXACTLY [number]?" or "[Team] Just Beat [Team]" -- one
of them ("Hull City Scored a Stoppage-Time Winner") was even published
twice, Aug 22 AND Aug 23. Zero variety. August median: 128 views, 1
subscriber from 29 videos.

Viral research finding: people do NOT love dry measurement trivia. The
same "sports facts" niche goes viral in a different emotional register --
absurd, funny, "no way that's real" (e.g. MLB umpires must wear black
underwear in case their trousers split; a referee once showed the same
player THREE yellow cards). Sources consistently cite: bizarre rules,
ranked/debatable claims, legendary moments, and content casual fans (not
just diehards) enjoy. Debate-driving content wins comments, and comments
are what build the returning audience this channel has never had.

This is designed as a REPEATABLE SERIES so viewers have a reason to come
back -- the thing 26-subscribers-from-98-videos says we never gave them.

THE FACT (verified 2026-09-02 on UEFA.com, the sport's own governing
body, plus Irish Times, Howler, These Football Times):
Euro 1968 semi-final, 5 June 1968, Naples. Italy 0-0 USSR after extra
time. Penalty shootouts did not yet exist in the competition -- tournament
rules decided all matches except the final by COIN TOSS. Italy captain
Giacinto Facchetti called correctly. Italy advanced, drew the final 1-1
with Yugoslavia, and won the replay 2-0 to become champions of Europe.

VISUALS: three real, safely-licensed Wikimedia Commons archive photos --
Giacinto Facchetti (Inter Milan 1966-67, the captain who actually called
the toss), the UEFA Euro 1968 Final Italy squad, and 1968 Italy match
action. An earlier version fetched a "coin flip" stock clip on the theory
it would be an exact visual match; it returned a cartoon Bitcoin emoji
instead (see the note in build()). Real archive photography beats a
literal-but-wrong stock match.

LENGTH: ~51 words. Verified render: 25.7s (an earlier 67-word cut came in
at 30.4s). Our own retention-by-length data (Jun 1-Sep 2): 21-25s = 117.4%
avg retention (>100% = replays/loops) vs 38.7% at 31-35s. Note the persona
sign-off ("I'm Alex Rivera, catch you in the next one") costs ~4s / 9 words
on EVERY video -- it is the main thing still pushing this past 25s.

Per standing process: does NOT auto-upload. Verify frames/duration/tail first.
"""
import os
import config

config.assert_safe_pipeline()

import pro_shorts_creator as psc
import copyright_compliance as cc
from logger import log

SCRIPT = {
    "hook": "Italy won a European Championship because their captain guessed a coin flip.",
    "body": (
        "1968 semi-final. Italy nil, Soviet Union nil. Penalty "
        "shootouts didn't exist -- the rules said flip a coin. "
        "Captain Giacinto Facchetti called it right. Italy went on "
        "to win the whole thing."
    ),
    "cta": "Fair? Comment below!",
    "title": "Italy Won a European Championship on a COIN FLIP #shorts",
    "tags": ["football", "soccer", "euro", "italy", "sportsfacts", "shorts", "viral", "soundsfake"],
    "seo_description": "In 1968 there were no penalty shootouts -- a European Championship semi-final was decided by a coin toss, and Italy's captain called it right. Sounds fake. 100% real. #football #sportsfacts #shorts",
    "queries": ["coin flip", "coin toss", "vintage football"],
}


def build():
    # DO NOT re-add a "coin flip" stock fetch here. Tried 2026-09-02 and
    # every usable Pexels result was a CARTOON 3D emoji hand holding a
    # Bitcoin on a black background -- it filled the middle 18s of a 1968
    # football-history video and passed the vision gate because it does
    # literally contain a coin. The only genuinely filmed coin clips were
    # an out-of-focus blur (856219) and an unrecognisable dark sliver
    # (7450200). The gate now rejects cartoons/3D renders outright (see
    # visual_shorts_creator._verify_thumbnail_relevance rule 3), but the
    # real fix is: use real archive photography for real history.
    photo_clips = []
    for src, out, label in [
        ("output/raw_clips/File_1966_67_Inter_Milan_-_Giacinto_Facchetti.jpg", "facchetti.mp4", "Facchetti (the captain who called it)"),
        ("output/raw_clips/File_UEFA_Euro_1968_Final_-_Italy.jpg", "euro68final.mp4", "Euro 1968 Final, Italy"),
        ("output/raw_clips/File_U23__Italy_v_England__Trieste__1968__-_Springett__Anastasi.jpg", "italy1968.mp4", "Italy 1968 match action"),
    ]:
        if os.path.exists(src):
            p = psc.make_athlete_photo_clip(src, "output/raw_clips/" + out, duration=12.0)
            photo_clips.append(p)
            log(f"  photo clip ({label}): {p}")

    clip_paths = photo_clips[:3]
    while len(clip_paths) < 3:
        clip_paths.append(clip_paths[-1])
    log(f"Clips: {clip_paths}")

    vo_path = psc.generate_voiceover(SCRIPT)
    from moviepy import AudioFileClip
    d = AudioFileClip(vo_path).duration
    log(f"VOICEOVER LENGTH: {d:.1f}s (target band 21-25s)")

    music_path = psc.get_music(duration=min(d + 1.5, 90.0), script=SCRIPT)

    check = cc.validate_before_upload(SCRIPT, clip_paths, music_path)
    cc.save_compliance_report(check, video_id="coinflip_euro1968_short")
    if not check["passed"]:
        raise RuntimeError(f"COMPLIANCE FAILED: {check['issues']}")

    out_path = os.path.join(config.VIDEOS_DIR, "coinflip_euro1968_short.mp4")
    psc.assemble(clip_paths, SCRIPT, vo_path, music_path, out_path)
    log(f"BUILD COMPLETE -> {out_path}")
    print("VO_PATH=" + vo_path)
    return out_path, vo_path


if __name__ == "__main__":
    build()
