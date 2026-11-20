"""
run_vanishing_spray_short.py — "everyday-object WHY" format (see
GROWTH_PLAN.md). Proven demand: "Why did FIFA stop using foam spray?" 8M
(2024), "Rare Moments with Sprays" 6M (2024). Target <=20s.

Facts (checked 2026-10-22): the can holds water, a foaming agent (surfactant)
and butane/isobutane/propane; out of the can the gas expands into
water-coated foam bubbles, then evaporates, so the line is gone in about a
minute. Introduced to stop walls creeping forward at free kicks; first used
at a World Cup in 2014. Who invented it is disputed (Heine Allemagne's
"Spuni" patent 2000-02 vs Pablo Silva's "9-15" brand), so the script names
neither. Sources: livescience.com, cbsnews.com, en.wikipedia.org/wiki/Vanishing_spray.
"""
import config

config.assert_safe_pipeline()
config.PERSONA_SIGNOFF = ""  # format ends on the comment prompt

import gemini_studio as gs

VIDEO_ID = "vanishing_spray_short"

SCRIPT = {
    "hook": "Why does the referee's spray disappear?",
    "body": (
        "It was invented in South America because players kept sneaking the wall forward "
        "at free kicks. The can holds water, foam and butane gas. On the grass, the gas "
        "expands into foam, then evaporates, and within about a minute the line is gone."
    ),
    "cta": "Should refs use it for penalties too? Comment below!",
    "title": "Why Does the Referee's Spray Disappear? 🤔 #shorts",
    "tags": ["vanishing spray", "referee spray", "free kick", "football facts", "soccer facts",
             "why", "referee", "football", "soccer", "shorts"],
    "seo_description": (
        "Referee vanishing spray is water, a foaming agent and butane: the gas expands into foam "
        "and then evaporates, so the free-kick line disappears in about a minute. "
        "#football #referee #shorts"
    ),
    "cut_seconds": 1.3,
    "ai_generated_visuals": True,
}

SCENES = [
    "Close-up from behind a referee's hand spraying a bright white foam line onto green grass in "
    "front of a row of player boots, floodlit night stadium.",
    "Low shot of a defensive wall's boots shuffling forward over the grass toward the ball, "
    "inch by inch, slow motion.",
    "Macro shot of white foam bubbles on blades of grass, the bubbles slowly popping and "
    "shrinking, shallow depth of field.",
    "Time-lapse close-up: a white spray line on a football pitch fading away until only green "
    "grass remains.",
    "A football on the grass with a foam line in front of it, a player's boot strikes the ball, "
    "slow motion, stadium lights.",
]

if __name__ == "__main__":
    gs.build_short(SCRIPT, SCENES, VIDEO_ID)
