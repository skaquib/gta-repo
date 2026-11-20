"""
run_sock_holes_short.py — "everyday-object WHY" format (see GROWTH_PLAN.md).
Proven demand: "Why are footballers destroying their socks?" 7.4M (2023);
"how to" socks with Bellingham 7.9M (2025). Target <=20s (~57 words) --
the goalkeeper Short ran 25s at 70 words.

Facts (checked 2026-10-22): players cut holes to relieve calf pressure from
tight match socks as calves swell during a game; Gareth Bale is widely
credited with starting it (2016, while managing calf problems); Kyle Walker
gives the same reason. Sports-medicine experts say no study shows it reduces
cramps or pain. Sources: axahealth.co.uk (physio), flashscore.com,
talesfromthetopflight.com.
"""
import config

config.assert_safe_pipeline()
config.PERSONA_SIGNOFF = ""  # format ends on the comment prompt

import gemini_studio as gs

VIDEO_ID = "sock_holes_short"

SCRIPT = {
    "hook": "Why do footballers cut holes in their socks?",
    "body": (
        "It's not fashion. Match socks are tight, and as your calves swell during a game, "
        "the pressure builds. Gareth Bale started cutting holes to release it, and now "
        "players everywhere copy him. The twist? No study has proven it actually helps."
    ),
    "cta": "Would you cut yours? Yes or no?",
    "title": "Why Do Footballers Cut Holes in Their Socks? 🧦 #shorts",
    "tags": ["football socks", "holes in socks", "football facts", "soccer facts", "why",
             "gareth bale", "football", "soccer", "shorts"],
    "seo_description": (
        "Footballers cut holes in their socks to relieve calf pressure as their muscles swell "
        "during a match -- but no study has proven it actually helps. #football #soccer #shorts"
    ),
    "cut_seconds": 1.3,
    "ai_generated_visuals": True,
}

SCENES = [
    "Extreme close-up: scissors snipping a hole into the back of a white football sock pulled up "
    "over a muscular calf in a dressing room, slow motion.",
    "Close-up of a footballer's calf in a tight white match sock, the fabric stretched and "
    "straining as he jogs, stadium floodlights behind.",
    "Slow-motion macro: a calf muscle flexing through several round holes cut in a football sock "
    "during a sprint on grass.",
    "Low-angle shot of several players' legs lined up in a tunnel, every sock dotted with cut "
    "holes, floodlit pitch at the end of the tunnel.",
    "Close-up of a player pulling up a hole-filled sock over shin guards, then stamping a boot "
    "on the grass, dramatic floodlight.",
]

if __name__ == "__main__":
    gs.build_short(SCRIPT, SCENES, VIDEO_ID)
