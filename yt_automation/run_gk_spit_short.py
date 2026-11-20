"""
run_gk_spit_short.py — First Short in the "everyday-object WHY" format
(competitor research 2026-10-20, output/research/):

  - Last 30 days, the biggest small/mid-channel sports Shorts were all one
    format: a "Why do/are X?" question about something viewers see but never
    questioned, answered in 16-22s ("Why are football gloves sticky" 11.7M,
    "Why Do Goalkeepers Wear Sticky Gloves?" 9.1M, "Why Are Shin Guards So
    Small" 7.7M, "Why do players sniff the tennis ball" 30M).
  - Our own best-retained Short was the same shape (bowling lane, 95%).
  - This topic: a Japanese version did 7.3M (Apr 2026) while the top English
    one is 735K from 2023 -- proven demand, English gap.

Format rules applied: question hook over a tactile close-up in 0-2s;
misconception -> problem -> answer; ~3.5 words/sec; cut every ~1.3s; ending
loop trap ("how many times did I say gloves?") instead of the persona
sign-off, which added ~3s of dead air after the payoff.

Facts (grounded search: theoneglove.com, keeperstop.com, gloveglu.com,
advantagegk.com): GK palms are latex foam; dry latex is stiffer and less
grippy, damp latex softens and conforms to the ball; manufacturers tell
keepers to dampen palms before/during play. Spit vs water: no evidence
spit is better -- the script doesn't claim it is.
"""
import os
import config

config.assert_safe_pipeline()
# This format ends on the loop trap -- no sign-off after the payoff.
config.PERSONA_SIGNOFF = ""

import gemini_studio as gs

VIDEO_ID = "gk_spit_short"

SCRIPT = {
    "hook": "Why do goalkeepers spit on their gloves?",
    "body": (
        "It looks gross, but it's actually science. The palms are made of latex "
        "foam, and dry latex goes stiff and slippery. Wet it, and it softens and "
        "moulds around the ball, so the ball sticks instead of skidding off. "
        "That's why glove makers tell keepers to wet their gloves before every match."
    ),
    "cta": "So, how many times did I say gloves? Comment the number!",
    "title": "Why Do Goalkeepers Spit on Their Gloves? 🧤 #shorts",
    "tags": ["goalkeeper", "goalkeeper gloves", "football facts", "soccer facts", "why",
             "football", "soccer", "goalkeeping", "shorts"],
    "seo_description": (
        "Goalkeepers spit on (or wet) their gloves because dry latex palms are stiff and "
        "slippery -- damp latex softens and grips the ball. Glove makers actually recommend "
        "wetting your gloves before every match. #football #goalkeeper #shorts"
    ),
    "cut_seconds": 1.3,
    "ai_generated_visuals": True,
}

# Narration order. Each is an 8s Veo clip; assemble() takes different
# windows of each on reuse.
SCENES = [
    # hook
    "Over-the-shoulder shot from behind a goalkeeper in a night stadium: he spits into the palms "
    "of his yellow latex goalkeeper gloves and claps them together, droplets flying, floodlights glaring.",
    # "dry latex goes stiff and slippery"
    "Macro close-up: a football skids and slips straight out of dry, dusty goalkeeper gloves in "
    "slow motion, on a training pitch.",
    # "wet it"
    "Extreme close-up macro shot of a goalkeeper's latex glove palm, a stream of water squirted from "
    "a sports bottle onto the palm, droplets beading on the textured latex, hands rubbing together, "
    "stadium floodlights bokeh behind. Cinematic, shallow depth of field.",
    # "moulds around the ball"
    "Super slow-motion macro: a wet latex goalkeeper glove palm presses onto a white football, the "
    "foam visibly compressing and moulding around the ball's surface.",
    # "the ball sticks"
    "Slow-motion low-angle shot: a goalkeeper dives full stretch and catches a powerful shot cleanly "
    "in both gloves, rain spray in the floodlights, face hidden by motion and shadow.",
    # loop back to the hook visual
    "Close-up of goalkeeper gloves clapping together hard, water droplets exploding outward in "
    "slow motion against stadium floodlights.",
]


def build():
    # Reuse the Veo test clip generated during research as scene 2 if present.
    test_clip = os.path.join(gs.AI_DIR, "veo_test.mp4")
    scene2 = os.path.join(gs.AI_DIR, f"{VIDEO_ID}_veo2.mp4")
    if os.path.exists(test_clip) and not os.path.exists(scene2):
        os.rename(test_clip, scene2)

    return gs.build_short(SCRIPT, SCENES, VIDEO_ID)


if __name__ == "__main__":
    build()
