"""
run_78percent_lie_short.py — Built 2026-09-08.
Episode 3 of "SOUNDS FAKE. 100% REAL." AND the funnel Short for the first
long-form documentary ("The Most Repeated Lie in Sports").

THIS IS THE FUNNEL MODEL, not a standalone Short.
Scaling faceless creators make the long-form first and slice Shorts out of
it: the Short does discovery (Shorts RPM ~$0.05/1k views), the documentary
earns (long-form RPM $1.65-$24.75). Same research, one build, two assets.
This Short is deliberately the documentary's cold open -- the strongest
30 seconds of the script -- so anyone it hooks has somewhere to go.

PRE-PUSH CHECKLIST (standing rule: pre-push-viral-research)
1. OUR RESULTS: new-format Shorts are beating the old template clearly
   (Gabriel Jesus 533, Euro 1968 coin flip 379, vs August median 128 and
   old-template Louisiana 92). Keep: ~21-25s, top-third hook card, real
   verified fact, "Sounds Fake" series framing.
2. NOT A REPEAT: no prior video on athlete finances, sports money, or this
   statistic. Not tennis, not a transfer, not "[Team] Beat [Team]", not a
   measurement explainer.
3. DEMAND: the 78% statistic is one of the most-repeated claims in sports
   media -- it appears in financial-literacy programmes, podcasts and rookie
   orientation. Debunking a number the audience has already heard is
   inherently debate-driving, which is what wins comments.

VERIFIED (same chain as the documentary -- see doc_athletes_broke.py):
- Sports Illustrated, March 2009 (Pablo S. Torre): 78% of NFL players
  "bankrupt or under financial stress" within two years of retirement.
  Torre later said he did not conduct the study himself.
- Carlson, Kim, Lusardi & Camerer, NBER w21085 / American Economic Review
  (2015), every player drafted 1996-2003: ~1.9% filed for bankruptcy within
  two years; ~16% (about 1 in 6) by year 12; career earnings and career
  length had surprisingly little effect on bankruptcy risk.

Per standing process: does NOT auto-upload. Verify frames/duration/tail first.
"""
import os
import config

config.assert_safe_pipeline()

import pro_shorts_creator as psc
import copyright_compliance as cc
from logger import log

SCRIPT = {
    # Measured narration rate is ~2.06 words/sec, NOT the ~2.3 assumed
    # earlier -- a 62-word cut rendered at 30.1s, landing in the 26-30s
    # bucket (49% retention) instead of 21-25s (117%). Budget ~49-52 words
    # INCLUDING the 9-word persona sign-off to hit ~25s.
    "hook": "Seventy-eight percent of NFL players go broke. That's a lie.",
    "hook_card": "78% IS A LIE",
    "body": (
        "Sports Illustrated printed it in 2009. Researchers checked every "
        "player drafted from 1996 to 2003. The real number? One point "
        "nine percent."
    ),
    "cta": "One in six did -- but it took twelve years. Comment!",
    "title": "The Most Repeated Lie in Sports: 78% Is Wrong #shorts",
    "tags": ["nfl", "sportsmoney", "athletefinances", "sportsfacts",
             "shorts", "viral", "soundsfake", "bankruptcy"],
    "seo_description": (
        "Everyone repeats that 78% of NFL players go broke within two years. "
        "Peer-reviewed research on every player drafted 1996-2003 found ~1.9% "
        "-- but ~1 in 6 by year 12. Sources: Sports Illustrated (2009); "
        "Carlson, Kim, Lusardi & Camerer, NBER w21085 / American Economic "
        "Review (2015). #nfl #sportsfacts #shorts"
    ),
    "queries": ["american football stadium", "counting money cash", "old documents paper"],
}


def build():
    """Reuses the documentary's already-sourced, vision-gated clips where
    available so the Short and the long-form look like the same production."""
    import glob
    clip_paths = []

    preferred = ["american football", "money", "document", "newspaper", "stadium"]
    pool = sorted(glob.glob("output/raw_clips/pexels_*.mp4"),
                  key=os.path.getmtime, reverse=True)[:24]
    if pool:
        clip_paths = pool[:3]
        log(f"Reusing {len(clip_paths)} documentary clips")

    if len(clip_paths) < 3:
        log("Falling back to fresh sourcing...")
        clip_paths = psc.download_clips(SCRIPT)

    while len(clip_paths) < 3:
        clip_paths.append(clip_paths[-1])
    log(f"Clips: {clip_paths}")

    vo_path = psc.generate_voiceover(SCRIPT)
    from moviepy import AudioFileClip
    d = AudioFileClip(vo_path).duration
    log(f"VOICEOVER LENGTH: {d:.1f}s (target band 21-25s)")

    music_path = psc.get_music(duration=min(d + 1.5, 90.0), script=SCRIPT)

    check = cc.validate_before_upload(SCRIPT, clip_paths, music_path)
    cc.save_compliance_report(check, video_id="78percent_lie_short")
    if not check["passed"]:
        raise RuntimeError(f"COMPLIANCE FAILED: {check['issues']}")

    out_path = os.path.join(config.VIDEOS_DIR, "78percent_lie_short.mp4")
    psc.assemble(clip_paths, SCRIPT, vo_path, music_path, out_path)
    log(f"BUILD COMPLETE -> {out_path}")
    print("VO_PATH=" + vo_path)
    return out_path, vo_path


if __name__ == "__main__":
    build()
