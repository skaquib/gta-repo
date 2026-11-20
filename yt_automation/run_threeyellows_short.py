"""
run_threeyellows_short.py — Built 2026-09-07.
Episode 2 of "SOUNDS FAKE. 100% REAL."

PRE-PUSH CHECKLIST (standing rule: pre-push-viral-research)
1. OUR OWN RESULTS FIRST (pulled 2026-09-07 -- this is what drove the call):
     Gabriel Jesus -> Barcelona (new format, 21.5s, top-third hook) = 533 views
     Euro 1968 coin flip ("Sounds Fake" ep.1, 25.7s)                = 379 views
     Louisiana NAIA upset (old template)                            =  92 views
   August median was 128. Both new-format videos beat it clearly; the old
   template did not. So: continue the series, keep the short runtime, keep
   the top-third hook. Do NOT fall back to the queued "Why Is X EXACTLY Y"
   builds (golf holes / shot clock / boxing rounds) -- that is the template
   the data says underperforms.
2. DEMAND CHECK: no single dominant breaking story on 2026-09-07 (US Open
   still at QF stage, no final yet; NFL/college seasons just opening). With
   no strong live event to ride, the proven-series play beats forcing a weak
   news hook -- and a recurring series is what builds returning viewers,
   which is the channel's actual deficit (26 subs / 98 videos).
3. NOT A REPEAT: not tennis (done 2026-08-31), not a transfer (done
   2026-09-06), not a measurement explainer, not "[Team] Just Beat [Team]".

THE FACT (verified 2026-09-07 across These Football Times, GiveMeSport,
myKhel, Football Whispers, and Wikipedia's "List of 2006 FIFA World Cup
controversies"):
2006 World Cup, Croatia v Australia. Referee Graham Poll booked Josip
Simunic in the 61st minute, booked him AGAIN in the 90th without issuing
the mandatory red, then showed a third yellow plus red in the 93rd after
Simunic shoved him following the final whistle. The cause is the best part:
Simunic was born in Australia and lived there until 19, so he spoke with an
Australian accent -- in the heat of the match Poll recorded the first
booking against AUSTRALIA's number 3 (Craig Moore) instead of Croatia's
number 3. Poll and his whole crew were sent home from the tournament.

VISUALS: real Wikimedia photo of Simunic (Dinamo Zagreb, 2012 -- his club
and era) with arms outstretched mid-protest, which reads exactly as "what
did I do?", plus real filmed match footage. NOTE: stock has no "referee
showing a yellow card" clip -- checked 2026-09-07, every result for
'referee yellow card' / 'football referee card' was generic gameplay. Same
gap that made the coin-toss shot impossible. Do not substitute a cartoon.

LENGTH: ~54 words targeting 21-25s (our data: 21-25s = 117.4% retention vs
38.7% at 31-35s). Persona sign-off still costs ~9 words / ~4s.

Per standing process: does NOT auto-upload. Verify frames/duration/tail first.
"""
import os
import config

config.assert_safe_pipeline()

import pro_shorts_creator as psc
import copyright_compliance as cc
from logger import log

SCRIPT = {
    "hook": "A referee gave the same player three yellow cards in one World Cup game.",
    "hook_card": "THREE YELLOWS. ONE PLAYER.",
    "body": (
        "Graham Poll booked Josip Simunic, booked him again, and "
        "forgot the red card. Simunic was born in Australia and "
        "sounded Australian -- so Poll had written the first booking "
        "against the wrong team."
    ),
    "cta": "Poll was sent home. Worst ever? Comment!",
    "title": "A Referee Gave the Same Player THREE Yellow Cards #shorts",
    "tags": ["football", "worldcup", "referee", "soccer", "shorts", "viral", "soundsfake", "sportsfacts"],
    "seo_description": "At the 2006 World Cup, referee Graham Poll showed Josip Simunic three yellow cards in one match -- because Simunic's Australian accent made Poll book the wrong team. Sounds fake. 100% real. #football #worldcup #shorts",
    "queries": ["soccer match stadium", "football players field", "football crowd"],
}

SIMUNIC_PHOTO = "output/raw_clips/File____________________-_________________2-0._3_________2012________276854.jpg"


def build():
    clip_paths = []

    if os.path.exists(SIMUNIC_PHOTO):
        p = psc.make_athlete_photo_clip(SIMUNIC_PHOTO, "output/raw_clips/simunic.mp4", duration=12.0)
        clip_paths.append(p)
        log(f"  photo clip (Simunic, Dinamo Zagreb 2012): {p}")

    # Real filmed match footage for the remaining beats. Vision-gated, so a
    # cartoon/3D render cannot slip in (rule 3 in _verify_thumbnail_relevance).
    import visual_shorts_creator as vsc
    used = set(int(x) for x in vsc._load_used_clip_ids().get("pexels", []))
    for q in ["soccer teams lining up stadium", "soccer match action", "football stadium crowd"]:
        if len(clip_paths) >= 3:
            break
        try:
            path, cid = vsc.fetch_pexels_clip(q, "output/raw_clips", exclude_ids=used)
            vsc._record_used_clip_ids("pexels", {cid})
            used.add(cid)
            clip_paths.append(path)
            log(f"  match clip ('{q}'): {path}")
        except Exception as e:
            log(f"  '{q}' failed: {e}")

    if not clip_paths:
        raise RuntimeError("No usable visuals")
    while len(clip_paths) < 3:
        clip_paths.append(clip_paths[-1])
    log(f"Clips: {clip_paths}")

    vo_path = psc.generate_voiceover(SCRIPT)
    from moviepy import AudioFileClip
    d = AudioFileClip(vo_path).duration
    log(f"VOICEOVER LENGTH: {d:.1f}s (target band 21-25s)")

    music_path = psc.get_music(duration=min(d + 1.5, 90.0), script=SCRIPT)

    check = cc.validate_before_upload(SCRIPT, clip_paths, music_path)
    cc.save_compliance_report(check, video_id="threeyellows_short")
    if not check["passed"]:
        raise RuntimeError(f"COMPLIANCE FAILED: {check['issues']}")

    out_path = os.path.join(config.VIDEOS_DIR, "threeyellows_short.mp4")
    psc.assemble(clip_paths, SCRIPT, vo_path, music_path, out_path)
    log(f"BUILD COMPLETE -> {out_path}")
    print("VO_PATH=" + vo_path)
    return out_path, vo_path


if __name__ == "__main__":
    build()
