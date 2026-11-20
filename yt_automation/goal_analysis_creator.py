"""
goal_analysis_creator.py
========================
Fully animated tactical goal analysis videos.
100% original content — ZERO copyright risk.

What it generates:
  - Animated football pitch (top-down tactical view)
  - Player dots + animated run arrows + pass lines
  - Animated stat bars and comparison charts
  - ElevenLabs AI narration (analytical, expert voice)
  - CC0 background music
  - Auto-upload to YouTube

Visual style: Dark premium (like Tifo Football / StatsBomb)
"""

import os, sys, time, json, random, math, io
import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from logger import log
import config

# ── MoviePy ──────────────────────────────────────────────────────────────────
try:
    from moviepy import (VideoFileClip, AudioFileClip, ImageClip,
                         concatenate_videoclips, concatenate_audioclips,
                         CompositeAudioClip)
    MOVIEPY_V2 = True
except ImportError:
    from moviepy.editor import (VideoFileClip, AudioFileClip, ImageClip,
                                concatenate_videoclips, concatenate_audioclips,
                                CompositeAudioClip)
    MOVIEPY_V2 = False

# ── Gemini ────────────────────────────────────────────────────────────────────
from google import genai
_GKEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
gemini_client = genai.Client(api_key=_GKEY) if _GKEY else None

# ── Constants ─────────────────────────────────────────────────────────────────
STATE_FILE    = "analysis_creator_state.json"
WIDTH, HEIGHT = 1080, 1920
FPS           = 30
DURATION      = 55   # seconds — analysis videos are longer than facts Shorts

MUSIC_TRACKS = [
    "https://assets.mixkit.co/music/preview/mixkit-sport-action-1027.mp3",
    "https://assets.mixkit.co/music/preview/mixkit-winning-is-everything-2142.mp3",
    "https://freepd.com/music/Sports%20News%20Intro.mp3",
    "https://raw.githubusercontent.com/rafaelreis-hotmart/Audio-Sample-files/master/sample.mp3",
]

# ── Colour palette ─────────────────────────────────────────────────────────────
BG          = (10, 14, 20)          # near-black background
PITCH_GREEN = (22, 68, 40)          # dark football green
PITCH_LINE  = (255, 255, 255, 90)   # semi-transparent white lines
TEAM_A      = (0, 200, 255)         # cyan — attacking team
TEAM_B      = (255, 80, 80)         # red — defending team
ACCENT      = (255, 215, 0)         # gold accent
TEXT_WHITE  = (255, 255, 255)
TEXT_GREY   = (180, 180, 180)
NEON_GREEN  = (57, 255, 20)

# ─────────────────────────────────────────────────────────────────────────────
# ANALYSIS SCRIPT LIBRARY
# Each entry has:
#   hook        — opening line (first 3s)
#   sections    — list of {t_start, t_end, narration, animation_type, data}
#   title       — YouTube title
#   tags        — YouTube tags
#   description — YouTube description
# ─────────────────────────────────────────────────────────────────────────────
ANALYSIS_LIBRARY = [
    {
        "hook": "Here's EXACTLY how that hat-trick happened in 8 minutes",
        "title": "The 8-Minute Hat-Trick EXPLAINED — Tactical Breakdown 🔥 #worldcup2026 #analysis",
        "tags": ["worldcup2026","tactics","hattrick","analysis","football","shorts","breakdown"],
        "description": "A deep dive tactical breakdown of the fastest hat-trick at World Cup 2026. Using animated diagrams to show exactly how the 3 goals were set up. #worldcup2026 #football #analysis",
        "narration": "In just 8 minutes, a World Cup 2026 hat-trick rewrote history. But HOW did it happen? Let's break it down tactically. Goal 1 came from a high press — the striker forced an error in the defensive third. Goal 2 exploited the gap left when the centre-back stepped out. Goal 3 was pure execution — a third-man run nobody tracked. The opposing defense made the same mistake three times: committing too early. Once you see the pattern, it's obvious. That's why this hat-trick was not luck. It was a system breakdown.",
        "sections": [
            {"label": "THE PRESS", "t": 0.0, "t_end": 0.30,
             "anim": "press",
             "attackers": [(0.50,0.30),(0.35,0.45),(0.65,0.45)],
             "defenders": [(0.50,0.50),(0.35,0.60),(0.65,0.60),(0.50,0.70)],
             "arrows": [((0.50,0.30),(0.50,0.48)), ((0.35,0.45),(0.35,0.58))],
             "label_pos": (0.50, 0.22), "label_text": "HIGH PRESS"},
            {"label": "GOAL 1", "t": 0.30, "t_end": 0.52,
             "anim": "goal",
             "attackers": [(0.50,0.30),(0.35,0.45),(0.65,0.45)],
             "defenders": [(0.50,0.52),(0.35,0.62),(0.65,0.62),(0.50,0.72)],
             "arrows": [((0.50,0.30),(0.50,0.20)), ((0.35,0.45),(0.50,0.30))],
             "label_pos": (0.50, 0.14), "label_text": "GOAL 1 ⚽"},
            {"label": "GOAL 2", "t": 0.52, "t_end": 0.74,
             "anim": "gap",
             "attackers": [(0.72,0.35),(0.50,0.45),(0.30,0.55)],
             "defenders": [(0.45,0.52),(0.65,0.52),(0.30,0.65),(0.80,0.65)],
             "arrows": [((0.72,0.35),(0.72,0.20)), ((0.50,0.45),(0.72,0.35))],
             "label_pos": (0.72, 0.14), "label_text": "GAP EXPLOITED ⚽"},
            {"label": "GOAL 3", "t": 0.74, "t_end": 1.0,
             "anim": "third_man",
             "attackers": [(0.50,0.55),(0.30,0.40),(0.70,0.30)],
             "defenders": [(0.50,0.60),(0.35,0.65),(0.65,0.65),(0.50,0.75)],
             "arrows": [((0.30,0.40),(0.50,0.55)), ((0.50,0.55),(0.70,0.30)), ((0.70,0.30),(0.70,0.18))],
             "label_pos": (0.70, 0.13), "label_text": "THIRD MAN RUN ⚽"},
        ],
        "stats": [
            {"label": "Shots on target", "team_a": 3, "team_b": 1, "max": 5},
            {"label": "Goals", "team_a": 3, "team_b": 0, "max": 5},
            {"label": "High turnovers", "team_a": 7, "team_b": 2, "max": 10},
            {"label": "xG", "team_a": 1.8, "team_b": 0.3, "max": 3},
        ],
    },
    {
        "hook": "Algeria's comeback is the most tactical recovery at World Cup 2026",
        "title": "Algeria's 3-Goal Comeback EXPLAINED — How Did They Do It? 🤯 #worldcup2026 #tactics",
        "tags": ["worldcup2026","algeria","comeback","tactics","analysis","football","breakdown"],
        "description": "A tactical breakdown of Algeria's incredible 3-3 comeback vs Austria at World Cup 2026. Using animated pitch diagrams to show the pressing triggers and positional shifts that changed the game.",
        "narration": "Algeria were 2-nil down at half time. Austria looked comfortable. Then Algeria's coach made one tactical switch that changed everything. They shifted from a 4-4-2 to a 3-4-3 pressing high and hard. Watch how the pitch changes. The wide midfielders became inverted, overloading Austria's right channel. Three times Austria tried to play out from the back. Three times Algeria stole the ball in dangerous positions. This was not a lucky comeback. It was a calculated tactical decision that exposed Austria's build-up weaknesses. The final goal in the 94th minute came directly from the same press trigger they'd rehearsed all game.",
        "sections": [
            {"label": "HALF TIME", "t": 0.0, "t_end": 0.25,
             "anim": "formation",
             "attackers": [(0.25,0.30),(0.50,0.30),(0.75,0.30),(0.15,0.50),(0.40,0.50),(0.60,0.50),(0.85,0.50),(0.25,0.70),(0.50,0.70),(0.75,0.70)],
             "defenders": [(0.50,0.55),(0.30,0.60),(0.70,0.60),(0.50,0.75)],
             "arrows": [],
             "label_pos": (0.50, 0.20), "label_text": "4-4-2 → 3-4-3 SWITCH"},
            {"label": "TRIGGER 1", "t": 0.25, "t_end": 0.50,
             "anim": "press",
             "attackers": [(0.25,0.35),(0.50,0.35),(0.75,0.35),(0.20,0.52),(0.80,0.52)],
             "defenders": [(0.50,0.52),(0.30,0.62),(0.70,0.62),(0.50,0.72)],
             "arrows": [((0.25,0.35),(0.35,0.50)),((0.50,0.35),(0.50,0.50)),((0.75,0.35),(0.65,0.50))],
             "label_pos": (0.50, 0.25), "label_text": "HIGH PRESS TRIGGER"},
            {"label": "GOAL 1", "t": 0.50, "t_end": 0.70,
             "anim": "goal",
             "attackers": [(0.25,0.35),(0.50,0.35),(0.75,0.35)],
             "defenders": [(0.50,0.55),(0.30,0.65),(0.70,0.65),(0.50,0.75)],
             "arrows": [((0.75,0.35),(0.75,0.20)),((0.50,0.35),(0.75,0.35))],
             "label_pos": (0.75, 0.13), "label_text": "TURNOVER → GOAL ⚽"},
            {"label": "94th MIN", "t": 0.70, "t_end": 1.0,
             "anim": "third_man",
             "attackers": [(0.50,0.40),(0.30,0.35),(0.70,0.30)],
             "defenders": [(0.50,0.55),(0.35,0.65),(0.65,0.65),(0.50,0.75)],
             "arrows": [((0.30,0.35),(0.50,0.40)),((0.50,0.40),(0.70,0.30)),((0.70,0.30),(0.70,0.16))],
             "label_pos": (0.70, 0.10), "label_text": "94' EQUALISER ⚽"},
        ],
        "stats": [
            {"label": "2nd Half Possession", "team_a": 58, "team_b": 42, "max": 100},
            {"label": "High Turnovers", "team_a": 9, "team_b": 3, "max": 12},
            {"label": "Goals 2nd Half", "team_a": 3, "team_b": 0, "max": 4},
            {"label": "Chances Created", "team_a": 7, "team_b": 2, "max": 10},
        ],
    },
    {
        "hook": "France's defense at World Cup 2026 is historically dominant",
        "title": "Why France's Defense Is UNBEATABLE — Tactical Analysis 🇫🇷 #worldcup2026 #france",
        "tags": ["worldcup2026","france","defense","tactics","analysis","football","mbappe"],
        "description": "A deep-dive tactical analysis of France's 0 goals conceded at World Cup 2026. Animated diagrams explain their defensive shape, pressing triggers, and why no team has broken through.",
        "narration": "France conceded ZERO goals across their entire World Cup 2026 group stage. 3 games. 270 minutes. Not a single goal. Here's exactly why their defense is historically dominant. Their defensive shape is a compact 4-4-2 block that shifts as one unit. When the ball goes wide, the entire block shifts. No gaps. When opponents try to play through the middle, France's defensive midfielder drops into the line, creating a 5-man wall. And their pressing triggers are automatic — any backward pass from the opposition triggers an immediate press. Opponents can't build up. They're forced into mistakes. That's not just talent. That's a system that works perfectly.",
        "sections": [
            {"label": "THE BLOCK", "t": 0.0, "t_end": 0.28,
             "anim": "formation",
             "attackers": [(0.50,0.70),(0.30,0.70),(0.70,0.70),(0.50,0.80)],
             "defenders": [(0.25,0.55),(0.42,0.55),(0.58,0.55),(0.75,0.55),(0.20,0.65),(0.40,0.65),(0.60,0.65),(0.80,0.65)],
             "arrows": [],
             "label_pos": (0.50, 0.45), "label_text": "COMPACT 4-4-2 BLOCK"},
            {"label": "SHIFT", "t": 0.28, "t_end": 0.55,
             "anim": "shift",
             "attackers": [(0.80,0.65),(0.80,0.55),(0.70,0.75)],
             "defenders": [(0.35,0.52),(0.52,0.52),(0.68,0.52),(0.85,0.52),(0.30,0.62),(0.50,0.62),(0.70,0.62),(0.88,0.62)],
             "arrows": [((0.25,0.55),(0.35,0.52)),((0.42,0.55),(0.52,0.52)),((0.58,0.55),(0.68,0.52)),((0.75,0.55),(0.85,0.52))],
             "label_pos": (0.50, 0.42), "label_text": "WHOLE BLOCK SHIFTS →"},
            {"label": "5-MAN WALL", "t": 0.55, "t_end": 0.78,
             "anim": "wall",
             "attackers": [(0.50,0.70),(0.35,0.60),(0.65,0.60)],
             "defenders": [(0.20,0.55),(0.35,0.55),(0.50,0.50),(0.65,0.55),(0.80,0.55),(0.35,0.65),(0.65,0.65)],
             "arrows": [((0.50,0.70),(0.50,0.58))],
             "label_pos": (0.50, 0.42), "label_text": "5-MAN DEFENSIVE WALL"},
            {"label": "PRESS TRIGGER", "t": 0.78, "t_end": 1.0,
             "anim": "press",
             "attackers": [(0.50,0.35),(0.30,0.40),(0.70,0.40),(0.50,0.50)],
             "defenders": [(0.30,0.55),(0.50,0.52),(0.70,0.55),(0.50,0.65)],
             "arrows": [((0.30,0.55),(0.30,0.43)),((0.50,0.52),(0.50,0.38)),((0.70,0.55),(0.70,0.43))],
             "label_pos": (0.50, 0.25), "label_text": "PRESS ON BACK PASS"},
        ],
        "stats": [
            {"label": "Goals Conceded", "team_a": 0, "team_b": 6, "max": 8},
            {"label": "Clean Sheets", "team_a": 3, "team_b": 0, "max": 3},
            {"label": "Saves Required", "team_a": 0, "team_b": 14, "max": 16},
            {"label": "High Turnovers Won", "team_a": 12, "team_b": 3, "max": 15},
        ],
    },
    {
        "hook": "Morocco's pressing is the most intense at World Cup 2026 — here's why",
        "title": "Morocco's PRESSING SYSTEM EXPLAINED — World Cup 2026 Tactics 🇲🇦 #worldcup2026",
        "tags": ["worldcup2026","morocco","pressing","tactics","analysis","football","darkhorse"],
        "description": "How Morocco became the highest-pressing team at World Cup 2026. Animated tactical breakdown of their triggers, traps, and how they dominate possession in the final third.",
        "narration": "Morocco have the highest pressing intensity of any team at World Cup 2026. 34 high turnovers per match. How? Their pressing is not random. It's triggered. When the opposition goalkeeper has the ball, Morocco's striker presses the near centre-back. This forces a rushed pass wide. Then Morocco's winger presses the full-back, cutting the escape route. The ball is trapped in the corner. Morocco win it back in dangerous positions. This is called a positional press. Every player knows exactly where to go based on where the ball is. The result? Opponents can't breathe. They rush. They make mistakes. And Morocco score from those mistakes.",
        "sections": [
            {"label": "TRIGGER", "t": 0.0, "t_end": 0.28,
             "anim": "press",
             "attackers": [(0.50,0.30),(0.30,0.42),(0.70,0.42)],
             "defenders": [(0.50,0.80),(0.30,0.65),(0.70,0.65),(0.50,0.55),(0.15,0.55),(0.85,0.55)],
             "arrows": [((0.50,0.30),(0.30,0.62)),((0.30,0.42),(0.15,0.53))],
             "label_pos": (0.50, 0.20), "label_text": "GK PRESS TRIGGER"},
            {"label": "TRAP", "t": 0.28, "t_end": 0.55,
             "anim": "trap",
             "attackers": [(0.15,0.40),(0.15,0.55),(0.30,0.48)],
             "defenders": [(0.15,0.65),(0.30,0.65),(0.50,0.70),(0.70,0.65)],
             "arrows": [((0.15,0.65),(0.05,0.55)),((0.15,0.40),(0.10,0.58)),((0.15,0.55),(0.08,0.63))],
             "label_pos": (0.20, 0.30), "label_text": "CORNERED — NO ESCAPE"},
            {"label": "TURNOVER", "t": 0.55, "t_end": 0.78,
             "anim": "goal",
             "attackers": [(0.15,0.40),(0.30,0.35),(0.50,0.40)],
             "defenders": [(0.15,0.65),(0.30,0.65),(0.50,0.70)],
             "arrows": [((0.15,0.40),(0.30,0.35)),((0.30,0.35),(0.50,0.40)),((0.50,0.40),(0.50,0.18))],
             "label_pos": (0.50, 0.12), "label_text": "TURNOVER → CHANCE ⚽"},
            {"label": "STATS", "t": 0.78, "t_end": 1.0,
             "anim": "stats_only",
             "attackers": [],
             "defenders": [],
             "arrows": [],
             "label_pos": (0.50, 0.25), "label_text": "34 HIGH TURNOVERS/GAME"},
        ],
        "stats": [
            {"label": "High Turnovers/Game", "team_a": 34, "team_b": 12, "max": 40},
            {"label": "PPDA (lower = more press)", "team_a": 6, "team_b": 14, "max": 20},
            {"label": "Wins in Danger Zone", "team_a": 18, "team_b": 6, "max": 25},
            {"label": "Goals from Turnovers", "team_a": 4, "team_b": 1, "max": 6},
        ],
    },
    {
        "hook": "This is how Argentina will defend their World Cup title",
        "title": "Argentina's Title Defence TACTICS — World Cup 2026 Analysis 🇦🇷 #worldcup2026",
        "tags": ["worldcup2026","argentina","tactics","analysis","football","messi","champion"],
        "description": "A tactical analysis of how Argentina are defending their World Cup title. Animated pitch diagrams showing their defensive transitions, counter-attack setup, and why they're the team to beat.",
        "narration": "Argentina are the defending World Cup champions. And at 2026, their tactical setup is even more refined. In possession, they play a 4-3-3 that becomes a 3-4-3 with the fullbacks pushed high. But the magic is in their defensive transitions. The moment they lose the ball, all 10 outfield players drop below the ball line within 3 seconds. This instant defensive shape stops counter-attacks completely. Then Argentina build from the back, patient, precise. De Paul controls the tempo. Mac Allister connects the lines. And the front three wait for the single moment of chaos they can exploit. Argentina don't chase games. They control them. And that's why they're favourites to win back-to-back.",
        "sections": [
            {"label": "POSSESSION", "t": 0.0, "t_end": 0.28,
             "anim": "formation",
             "attackers": [(0.25,0.30),(0.50,0.28),(0.75,0.30),(0.35,0.45),(0.50,0.42),(0.65,0.45),(0.15,0.58),(0.38,0.60),(0.62,0.60),(0.85,0.58)],
             "defenders": [(0.50,0.65),(0.30,0.70),(0.70,0.70),(0.50,0.80)],
             "arrows": [((0.15,0.58),(0.15,0.40)),((0.85,0.58),(0.85,0.40))],
             "label_pos": (0.50, 0.18), "label_text": "FULLBACKS PUSH HIGH"},
            {"label": "TRANSITION", "t": 0.28, "t_end": 0.55,
             "anim": "transition",
             "attackers": [(0.25,0.48),(0.50,0.46),(0.75,0.48),(0.35,0.54),(0.50,0.54),(0.65,0.54),(0.25,0.62),(0.50,0.60),(0.75,0.62),(0.50,0.70)],
             "defenders": [(0.50,0.60),(0.30,0.68),(0.70,0.68)],
             "arrows": [],
             "label_pos": (0.50, 0.36), "label_text": "ALL 10 DROP IN 3 SECS"},
            {"label": "BUILD-UP", "t": 0.55, "t_end": 0.78,
             "anim": "buildup",
             "attackers": [(0.50,0.80),(0.30,0.72),(0.70,0.72),(0.35,0.58),(0.50,0.52),(0.65,0.58),(0.30,0.38),(0.50,0.35),(0.70,0.38)],
             "defenders": [(0.50,0.50),(0.35,0.58),(0.65,0.58),(0.50,0.65)],
             "arrows": [((0.50,0.80),(0.30,0.72)),((0.30,0.72),(0.35,0.58)),((0.35,0.58),(0.50,0.52)),((0.50,0.52),(0.50,0.35))],
             "label_pos": (0.50, 0.25), "label_text": "PATIENT BUILD-UP"},
            {"label": "COUNTER", "t": 0.78, "t_end": 1.0,
             "anim": "goal",
             "attackers": [(0.30,0.38),(0.50,0.35),(0.70,0.38)],
             "defenders": [(0.50,0.50),(0.35,0.60),(0.65,0.60),(0.50,0.70)],
             "arrows": [((0.50,0.35),(0.50,0.18)),((0.30,0.38),(0.50,0.35))],
             "label_pos": (0.50, 0.12), "label_text": "CLINICAL COUNTER ⚽"},
        ],
        "stats": [
            {"label": "Goals Scored", "team_a": 9, "team_b": 4, "max": 12},
            {"label": "Goals Conceded", "team_a": 1, "team_b": 5, "max": 8},
            {"label": "Possession %", "team_a": 62, "team_b": 38, "max": 100},
            {"label": "Pass Accuracy %", "team_a": 91, "team_b": 78, "max": 100},
        ],
    },
    {
        # Real match: Spain 1-0 Portugal, World Cup 2026 Round of 16, Dallas
        # Stadium, July 6 2026. Verified facts: Mikel Merino scored a
        # stoppage-time winner assisted by Ferran Torres; Mikel Oyarzabal
        # shot wide after a Dani Olmo through-ball; Nuno Mendes's deflected
        # drive hit the crossbar for Portugal. The result ended Cristiano
        # Ronaldo's World Cup career.
        "hook": "This one stoppage-time goal ended Ronaldo's World Cup career",
        "title": "How Spain's Stoppage-Time Winner Eliminated Portugal #shorts #worldcup2026 #analysis",
        "tags": ["worldcup2026","spain","portugal","tactics","analysis","football","shorts"],
        "description": "A tactical breakdown of Spain's 1-0 stoppage-time win over Portugal in the World Cup 2026 Round of 16 — the match that ended Cristiano Ronaldo's World Cup career. #worldcup2026 #football #analysis",
        "narration": "Portugal had the better of the half-chances. Nuno Mendes's deflected drive rattled the crossbar, and for a moment it looked like Portugal's night. But Spain kept probing. Dani Olmo played Mikel Oyarzabal clean through — he pulled it just wide. Then, deep into stoppage time, Ferran Torres found space down the right and squared it low. Mikel Merino arrived on cue and finished with a powerful, precise strike. One clinical moment settled a game of fine margins. Spain move on to the quarter-finals. And Cristiano Ronaldo's World Cup story ends here.",
        "sections": [
            {"label": "CROSSBAR", "t": 0.0, "t_end": 0.30,
             "anim": "press",
             "attackers": [(0.30,0.35),(0.50,0.40),(0.70,0.35)],
             "defenders": [(0.50,0.55),(0.35,0.62),(0.65,0.62),(0.50,0.72)],
             "arrows": [((0.30,0.35),(0.50,0.25)), ((0.50,0.25),(0.50,0.15))],
             "label_pos": (0.50, 0.10), "label_text": "MENDES HITS THE BAR"},
            {"label": "OYARZABAL WIDE", "t": 0.30, "t_end": 0.55,
             "anim": "gap",
             "attackers": [(0.45,0.45),(0.60,0.40),(0.30,0.50)],
             "defenders": [(0.50,0.55),(0.35,0.62),(0.65,0.62),(0.50,0.72)],
             "arrows": [((0.30,0.50),(0.60,0.40)), ((0.60,0.40),(0.75,0.20))],
             "label_pos": (0.60, 0.14), "label_text": "OLMO THROUGH-BALL"},
            {"label": "MERINO WINNER", "t": 0.55, "t_end": 1.0,
             "anim": "goal",
             "attackers": [(0.75,0.45),(0.50,0.40),(0.35,0.50)],
             "defenders": [(0.50,0.55),(0.35,0.62),(0.65,0.62),(0.50,0.72)],
             "arrows": [((0.75,0.45),(0.50,0.35)), ((0.50,0.35),(0.50,0.16))],
             "label_pos": (0.50, 0.10), "label_text": "MERINO 90+ ⚽"},
        ],
        "stats": [
            {"label": "Shots on target", "team_a": 5, "team_b": 3, "max": 8},
            {"label": "Goals", "team_a": 1, "team_b": 0, "max": 3},
            {"label": "Possession %", "team_a": 58, "team_b": 42, "max": 100},
            {"label": "Big chances", "team_a": 2, "team_b": 1, "max": 4},
        ],
    },
]


# ── Fonts ─────────────────────────────────────────────────────────────────────
def get_font(size, bold=False):
    for p in [
        "C:\\Windows\\Fonts\\Impact.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf" if bold else "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
    ]:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except: pass
    return ImageFont.load_default()

def stroke(draw, text, x, y, font, fill=(255,255,255), sw=4):
    for dx in range(-sw, sw+1, max(1,sw//2)):
        for dy in range(-sw, sw+1, max(1,sw//2)):
            draw.text((x+dx, y+dy), text, font=font, fill=(0,0,0))
    draw.text((x, y), text, font=font, fill=fill)

def wrap(text, font, max_w, draw):
    words, lines, line = text.split(), [], []
    for w in words:
        test = " ".join(line+[w])
        if draw.textbbox((0,0),test,font=font)[2] > max_w and line:
            lines.append(" ".join(line)); line=[w]
        else: line.append(w)
    if line: lines.append(" ".join(line))
    return lines


# ─────────────────────────────────────────────────────────────────────────────
# PITCH DRAWING ENGINE
# ─────────────────────────────────────────────────────────────────────────────
PITCH_RECT = (60, 280, WIDTH-60, 880)  # left, top, right, bottom

def draw_pitch(draw, alpha=255):
    """Draw a top-down football pitch with lines."""
    L, T, R, B = PITCH_RECT
    PW, PH = R-L, B-T
    # Main pitch
    draw.rectangle([L, T, R, B], fill=PITCH_GREEN)
    # Border
    draw.rectangle([L, T, R, B], outline=(255,255,255,alpha), width=3)
    # Halfway line
    mid_y = T + PH//2
    draw.line([(L, mid_y),(R, mid_y)], fill=(255,255,255,alpha), width=2)
    # Centre circle (radius ~55px)
    r = 55
    cx, cy = L+PW//2, mid_y
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=(255,255,255,alpha), width=2)
    draw.ellipse([cx-4, cy-4, cx+4, cy+4], fill=(255,255,255,alpha))
    # Penalty areas
    pa_w, pa_h = int(PW*0.55), int(PH*0.18)
    pa_x = L + (PW-pa_w)//2
    # Top penalty area
    draw.rectangle([pa_x, T, pa_x+pa_w, T+pa_h], outline=(255,255,255,alpha), width=2)
    # Bottom penalty area
    draw.rectangle([pa_x, B-pa_h, pa_x+pa_w, B], outline=(255,255,255,alpha), width=2)
    # Goals
    g_w = int(PW*0.18)
    g_x = L + (PW-g_w)//2
    draw.rectangle([g_x, T-12, g_x+g_w, T], fill=(200,200,200,alpha))
    draw.rectangle([g_x, B, g_x+g_w, B+12], fill=(200,200,200,alpha))
    # Striped grass (subtle alternating bands)
    band_h = PH // 8
    for i in range(8):
        if i % 2 == 0:
            y1 = T + i*band_h
            y2 = min(T + (i+1)*band_h, B)
            draw.rectangle([L+3, y1, R-3, y2], fill=(24,72,44))


def pitch_to_px(rx, ry):
    """Convert relative pitch coords (0-1) to pixel coords."""
    L, T, R, B = PITCH_RECT
    return int(L + rx*(R-L)), int(T + ry*(B-T))


def draw_player_dot(draw, rx, ry, colour, size=18, label=None):
    """Draw a glowing player dot at relative position."""
    px, py = pitch_to_px(rx, ry)
    # Outer glow
    for r in range(size+6, size, -2):
        a = int(60 * (1-(r-size)/6))
        draw.ellipse([px-r, py-r, px+r, py+r], fill=colour+(a,) if len(colour)==3 else colour)
    # Main dot
    draw.ellipse([px-size, py-size, px+size, py+size], fill=colour)
    # White centre
    draw.ellipse([px-size//3, py-size//3, px+size//3, py+size//3], fill=(255,255,255))


def draw_arrow(draw, rx1, ry1, rx2, ry2, colour, progress=1.0, width=4):
    """Draw an animated arrow showing progress (0→1)."""
    px1, py1 = pitch_to_px(rx1, ry1)
    px2, py2 = pitch_to_px(rx2, ry2)
    # Interpolate end point by progress
    ex = int(px1 + (px2-px1)*progress)
    ey = int(py1 + (py2-py1)*progress)
    draw.line([(px1, py1),(ex, ey)], fill=colour, width=width)
    # Arrowhead at end
    if progress > 0.8:
        angle = math.atan2(ey-py1, ex-px1)
        hs = 14
        for da in [0.4, -0.4]:
            ax = ex - int(hs*math.cos(angle-da))
            ay = ey - int(hs*math.sin(angle-da))
            draw.line([(ex,ey),(ax,ay)], fill=colour, width=width)


def draw_dashed_circle(draw, rx, ry, r_px, colour, alpha=180):
    """Draw a dashed circle to highlight an area."""
    px, py = pitch_to_px(rx, ry)
    for a in range(0, 360, 20):
        x1 = px + int(r_px*math.cos(math.radians(a)))
        y1 = py + int(r_px*math.sin(math.radians(a)))
        x2 = px + int(r_px*math.cos(math.radians(a+10)))
        y2 = py + int(r_px*math.sin(math.radians(a+10)))
        draw.line([(x1,y1),(x2,y2)], fill=colour, width=3)


# ─────────────────────────────────────────────────────────────────────────────
# STAT BARS
# ─────────────────────────────────────────────────────────────────────────────
STATS_TOP = 920    # y position where stats section starts

def draw_stat_bar(draw, stat, idx, progress, total_stats):
    """Draw one animated stat comparison bar."""
    bar_h    = 90
    y        = STATS_TOP + 20 + idx * bar_h
    bar_area_w = WIDTH - 80
    max_bar  = bar_area_w // 2 - 20

    label_font = get_font(32, bold=True)
    num_font   = get_font(40, bold=True)

    # Label
    draw.text((WIDTH//2, y), stat["label"], font=label_font,
              fill=TEXT_GREY, anchor="mm")

    # Team A bar (left, cyan)
    a_val   = stat["team_a"]
    a_ratio = (a_val / stat["max"]) * progress
    a_w     = int(max_bar * a_ratio)
    if a_w > 0:
        draw.rounded_rectangle(
            [WIDTH//2 - 15 - a_w, y+30, WIDTH//2 - 15, y+58],
            radius=6, fill=TEAM_A)
    # Team A label
    draw.text((WIDTH//2 - 20 - a_w, y+44), f"{a_val}", font=num_font,
              fill=TEAM_A, anchor="rm")

    # Team B bar (right, red)
    b_val   = stat["team_b"]
    b_ratio = (b_val / stat["max"]) * progress
    b_w     = int(max_bar * b_ratio)
    if b_w > 0:
        draw.rounded_rectangle(
            [WIDTH//2 + 15, y+30, WIDTH//2 + 15 + b_w, y+58],
            radius=6, fill=TEAM_B)
    draw.text((WIDTH//2 + 20 + b_w, y+44), f"{b_val}", font=num_font,
              fill=TEAM_B, anchor="lm")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN FRAME GENERATOR
# ─────────────────────────────────────────────────────────────────────────────
def make_frame(t: float, analysis: dict) -> np.ndarray:
    """Generate one frame of the analysis video at time t."""
    img  = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img, "RGBA")
    pct  = t / DURATION   # 0→1 overall progress

    # ── Background gradient ──
    for y in range(HEIGHT):
        r = max(0, int(10 - y*0.002))
        draw.line([(0,y),(WIDTH,y)], fill=(r, 14, 25))

    # ── Header ──
    # Channel badge
    ch_font = get_font(34)
    draw.text((WIDTH//2, 38), f"⚽ {config.CHANNEL_NAME} | TACTICAL ANALYSIS",
              font=ch_font, fill=ACCENT, anchor="mm")
    # Separator line
    draw.line([(60,65),(WIDTH-60,65)], fill=ACCENT, width=2)

    # ── Hook title (first 4 seconds) ──
    if t < 4.0:
        fade = min(1.0, t/0.5) * min(1.0, (4.0-t)/0.4)
        hook_font = get_font(60, bold=True)
        hook_lines = wrap(analysis["hook"], hook_font, WIDTH-80, draw)
        lh = 68
        y = 110
        for ln in hook_lines:
            bb = draw.textbbox((0,0), ln, font=hook_font)
            x  = (WIDTH - (bb[2]-bb[0]))//2
            stroke(draw, ln, x, y, hook_font, ACCENT, sw=5)
            y += lh

    # ── Section label (top of pitch area) ──
    section = None
    for s in analysis["sections"]:
        if s["t"] <= pct < s["t_end"]:
            section = s; break
    if section is None and analysis["sections"]:
        section = analysis["sections"][-1]

    sec_font = get_font(44, bold=True)
    if section:
        draw.text((WIDTH//2, 235), section["label_text"],
                  font=sec_font, fill=TEXT_WHITE, anchor="mm")

    # ── Draw pitch ──
    draw_pitch(draw)

    # ── Draw players and arrows for current section ──
    if section:
        # Section local progress (0→1)
        if section["t_end"] > section["t"]:
            sp = (pct - section["t"]) / (section["t_end"] - section["t"])
        else:
            sp = 1.0
        sp = max(0.0, min(1.0, sp))

        # Draw arrows first (behind players)
        for i, (p1, p2) in enumerate(section.get("arrows", [])):
            arrow_prog = max(0.0, min(1.0, (sp*len(section["arrows"])-i)))
            draw_arrow(draw, p1[0], p1[1], p2[0], p2[1],
                       NEON_GREEN, progress=arrow_prog, width=5)

        # Draw defending team
        for pos in section.get("defenders", []):
            draw_player_dot(draw, pos[0], pos[1], TEAM_B, size=16)

        # Draw attacking team
        for pos in section.get("attackers", []):
            draw_player_dot(draw, pos[0], pos[1], TEAM_A, size=18)

        # Highlight circle on goal/key position
        if section["anim"] in ("goal", "third_man") and sp > 0.6:
            lx, ly = section.get("label_pos", (0.5, 0.15))
            draw_dashed_circle(draw, lx, ly, 32, ACCENT)

    # ── Stats section ──
    # Draw team legend above stats
    legend_y = STATS_TOP - 30
    dot_r = 10
    draw.ellipse([WIDTH//2 - 180 - dot_r, legend_y-dot_r,
                  WIDTH//2 - 180 + dot_r, legend_y+dot_r], fill=TEAM_A)
    draw.text((WIDTH//2 - 163, legend_y), "TEAM A",
              font=get_font(28), fill=TEAM_A, anchor="lm")
    draw.ellipse([WIDTH//2 + 140 - dot_r, legend_y-dot_r,
                  WIDTH//2 + 140 + dot_r, legend_y+dot_r], fill=TEAM_B)
    draw.text((WIDTH//2 + 157, legend_y), "TEAM B",
              font=get_font(28), fill=TEAM_B, anchor="lm")
    # Divider
    draw.line([(60, STATS_TOP-5),(WIDTH-60, STATS_TOP-5)],
              fill=(60,60,60), width=1)

    # Animate stat bars in after first 40% of video
    stats_progress = max(0.0, min(1.0, (pct - 0.35) / 0.25))
    for i, stat in enumerate(analysis.get("stats",[])):
        draw_stat_bar(draw, stat, i, stats_progress, len(analysis["stats"]))

    # ── Bottom CTA (last 8 seconds) ──
    cta_start = (DURATION - 8) / DURATION
    if pct > cta_start:
        cta_fade  = min(1.0, (pct-cta_start)/0.1)
        cta_font  = get_font(48, bold=True)
        cta_lines = wrap("👆 FOLLOW for daily tactical breakdowns!", cta_font, WIDTH-80, draw)
        lh = 58
        y  = HEIGHT - 200
        for ln in cta_lines:
            bb = draw.textbbox((0,0), ln, font=cta_font)
            x  = (WIDTH-(bb[2]-bb[0]))//2
            stroke(draw, ln, x, y, cta_font, ACCENT, sw=4)
            y += lh

    # ── Progress bar ──
    bw = int(WIDTH * pct)
    draw.rectangle([(0,HEIGHT-8),(WIDTH,HEIGHT)], fill=(30,30,30))
    if bw > 0: draw.rectangle([(0,HEIGHT-8),(bw,HEIGHT)], fill=ACCENT)

    return np.array(img)


# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _dur(c,d):
    return c.with_duration(d) if MOVIEPY_V2 else c.set_duration(d)
def _audio(c,a):
    return c.with_audio(a) if MOVIEPY_V2 else c.set_audio(a)
def _vol(c,f):
    if hasattr(c,"with_volume_scaled"): return c.with_volume_scaled(f)
    if hasattr(c,"multiply_volume"):    return c.multiply_volume(f)
    return c.volumex(f)


def get_music() -> str:
    """Get high-quality royalty-free sports music."""
    os.makedirs(config.AUDIO_DIR, exist_ok=True)
    for url in random.sample(MUSIC_TRACKS, len(MUSIC_TRACKS)):
        name = f"music_{abs(hash(url)) % 99999}.mp3"
        path = os.path.join(config.AUDIO_DIR, name)
        if os.path.exists(path) and os.path.getsize(path) > 5000:
            return path
        try:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
            r.raise_for_status()
            with open(path, "wb") as f: f.write(r.content)
            if os.path.getsize(path) > 5000:
                log(f"Music: {name}")
                return path
        except Exception as e:
            log(f"Music failed ({e.__class__.__name__}) — next")
    raise Exception("All music tracks failed")



def generate_cloned_voiceover_via_gradio(text: str, output_path: str) -> bool:
    try:
        from gradio_client import Client, handle_file
        import re
        import shutil
        
        # Look for the user's voice clip inside the workspace directory
        m4a_path = os.path.join(os.path.dirname(__file__), "Recording (2).m4a")
        wav_path = os.path.join(os.path.dirname(__file__), "Recording (2).wav")
        
        if not os.path.exists(m4a_path) and not os.path.exists(wav_path):
            log("No voice clone recording found at 'Recording (2).m4a' or '.wav'")
            return False
            
        # Convert to WAV locally if only M4A exists
        if os.path.exists(m4a_path) and not os.path.exists(wav_path):
            log("Converting speaker M4A voice sample to WAV locally for XTTS v2...")
            ffmpeg_exe = r"C:\Users\Abcom\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe"
            cmd = [ffmpeg_exe, "-y", "-i", m4a_path, "-ar", "22050", "-ac", "1", wav_path]
            import subprocess
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            log("Successfully converted speaker voice clip to WAV!")
            
        # Upload WAV to tmpfiles.org with retries
        log("Uploading voice clone reference to tmpfiles.org...")
        direct_url = None
        for attempt in range(3):
            try:
                with open(wav_path, "rb") as f:
                    r = requests.post("https://tmpfiles.org/api/v1/upload", files={"file": f}, timeout=30)
                    r.raise_for_status()
                    data = r.json()
                    raw_url = data["data"]["url"]
                    direct_url = raw_url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
                    break
            except Exception as upload_err:
                log(f"  Upload attempt {attempt+1} failed: {upload_err}. Retrying in 3s...")
                time.sleep(3)
                
        if not direct_url:
            raise Exception("Failed to upload reference audio to tmpfiles.org after 3 attempts.")
            
        spaces = [
            "hasanbasbunar/Voice-Cloning-XTTS-v2",
            "JymNils/Voice-Cloning-XTTS-v2",
            "YemenEdu/Voice-Cloning-XTTS-v2"
        ]
        
        hf_token = getattr(config, "HF_TOKEN", "") or None
        if hf_token:
            log("Authenticating Gradio Client using HF_TOKEN from .env...")
        else:
            log("Gradio Client running unauthenticated (subject to ZeroGPU rate limits).")
            
        # Split text into clean sentences to bypass connection timeout/aborted issues on long texts
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
        log(f"Split script into {len(sentences)} sentence(s) for robust chunked synthesis...")
        
        chunk_files = []
        space_idx = 0
        
        for i, sentence in enumerate(sentences):
            # Throttle requests slightly to prevent trigger-happy rate limiters
            if i > 0:
                time.sleep(1.5)
                
            log(f"Synthesizing sentence {i+1}/{len(sentences)}: '{sentence[:50]}...'")
            chunk_result = None
            
            # Rotate across all listed spaces in case one hits ZeroGPU rate limit or has downtime
            max_global_attempts = len(spaces) * 2
            global_attempt = 0
            
            while global_attempt < max_global_attempts:
                current_space = spaces[space_idx]
                log(f"  [Space {space_idx+1}/{len(spaces)}] Connecting and predicting on {current_space}...")
                try:
                    client = Client(current_space, token=hf_token)
                    chunk_result = client.predict(
                        text=sentence,
                        reference_audio_url=direct_url,
                        example_audio_name=None,
                        language="English",
                        temperature=0.75,
                        speed=1.0,
                        do_sample=True,
                        repetition_penalty=5.0,
                        length_penalty=1.0,
                        gpt_cond_len=30,
                        top_k=50,
                        top_p=0.85,
                        remove_silence_enabled=True,
                        silence_threshold=-45,
                        min_silence_len=300,
                        keep_silence=100,
                        text_splitting_method="Native XTTS splitting",
                        max_chars_per_segment=250,
                        enable_preprocessing=False,
                        api_name="/voice_clone_synthesis"
                    )
                    break # Success! Break out of the rotation loop
                except Exception as pred_err:
                    err_msg = str(pred_err)
                    if "ZeroGPU quota" in err_msg or "quota" in err_msg.lower():
                        log(f"  Rate limit hit on {current_space}! Swapping space...")
                    else:
                        log(f"  Failed prediction on {current_space}: {pred_err}. Swapping space...")
                    
                    space_idx = (space_idx + 1) % len(spaces)
                    global_attempt += 1
                    time.sleep(2)
            
            if not chunk_result:
                raise Exception(f"Failed to synthesize sentence {i+1} after exhausting all fallback Gradio spaces.")
                
            # Copy to a persistent temp path in audio folder to avoid Gradio cache cleanup
            temp_chunk = os.path.join(config.AUDIO_DIR, f"temp_chunk_{i}_{int(time.time())}.mp3")
            shutil.copy(chunk_result, temp_chunk)
            chunk_files.append(temp_chunk)
            
        # Concatenate all sentence audio chunks using MoviePy
        log(f"Concatenating {len(chunk_files)} voice chunks...")
        audio_clips = [AudioFileClip(c) for c in chunk_files]
        final_audio = concatenate_audioclips(audio_clips)
        final_audio.write_audiofile(output_path, fps=44100, bitrate="192k", logger=None)
        
        # Close clips and clean up temporary chunk files
        for clip in audio_clips:
            clip.close()
        for chunk in chunk_files:
            try:
                os.remove(chunk)
            except:
                pass
                
        log(f"Cloned Voiceover generated successfully via chunked Gradio: {output_path}")
        return True
    except Exception as e:
        log(f"Failed to generate cloned voiceover via Gradio client: {e}")
        return False


def generate_voiceover(text: str) -> str:
    os.makedirs(config.AUDIO_DIR, exist_ok=True)
    p = os.path.join(config.AUDIO_DIR, f"analysis_vo_{int(time.time())}.mp3")

    # 1. Try free cloned voice via Gradio HF XTTS space first
    m4a_path = os.path.join(os.path.dirname(__file__), "Recording (2).m4a")
    wav_path = os.path.join(os.path.dirname(__file__), "Recording (2).wav")
    has_cloned_reference = os.path.exists(m4a_path) or os.path.exists(wav_path)
    
    if has_cloned_reference:
        log("Attempting to generate voiceover using your cloned voice (XTTS v2 Gradio)...")
        if generate_cloned_voiceover_via_gradio(text, p):
            return p
        else:
            raise Exception("Strict Voice-Cloning Enforcement: Cloned voice generation failed. Aborting compilation to prevent robotic/incorrect voice uploads.")

    # Try ElevenLabs first if key is configured
    if getattr(config, "ELEVENLABS_API_KEY", ""):
        log(f"Trying ElevenLabs TTS: {len(text)} chars...")
        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{config.ELEVENLABS_VOICE_ID}"
            headers = {"xi-api-key": config.ELEVENLABS_API_KEY, "Content-Type": "application/json"}
            # Use a different voice style for analysis — more authoritative
            payload = {
                "text": text,
                "model_id": "eleven_turbo_v2_5",
                "voice_settings": {"stability": 0.65, "similarity_boost": 0.80, "style": 0.20}
            }
            r = requests.post(url, json=payload, headers=headers, timeout=90)
            if r.status_code == 200:
                with open(p, "wb") as f: f.write(r.content)
                log(f"ElevenLabs voice saved: {p}")
                return p
            else:
                log(f"ElevenLabs TTS failed: {r.status_code} — {r.text[:100]}. Falling back to edge-tts.")
        except Exception as e:
            log(f"ElevenLabs exception: {e}. Falling back to edge-tts.")

    # Fallback to completely free, unlimited edge-tts
    log("Generating voiceover using edge-tts...")
    try:
        import asyncio
        import edge_tts
        
        async def save_tts():
            voice = "en-US-AndrewMultilingualNeural" # Natural male narrator
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(p)
            
        asyncio.run(save_tts())
        log(f"Edge-TTS voice saved: {p}")
        return p
    except Exception as tts_err:
        log(f"Edge-TTS failed: {tts_err}")
        raise Exception(f"All Text-To-Speech services failed. Edge-TTS error: {tts_err}")


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f: return json.load(f)
        except: pass
    return {"idx": -1, "count": 0}

def save_state(s):
    with open(STATE_FILE,"w") as f: json.dump(s,f,indent=2)


def pick_analysis(state: dict) -> dict:
    """Prefer a real match from match_calendar.py (recent_results() with a
    populated 'analysis_detail' payload matching this file's ANALYSIS_LIBRARY
    schema) over the bundled example breakdowns, so content tracks real,
    current matches once match_calendar_data.json has verified data. Falls
    back to rotating through the static ANALYSIS_LIBRARY otherwise."""
    try:
        import match_calendar
        for fixture in match_calendar.recent_results(days_back=7.0):
            detail = fixture.get("analysis_detail")
            if detail and "sections" in detail:
                return detail
    except Exception as e:
        log(f"Match calendar unavailable for analysis selection ({e}) — using bundled library")

    idx = (state.get("idx", -1) + 1) % len(ANALYSIS_LIBRARY)
    state["idx"] = idx
    return ANALYSIS_LIBRARY[idx]


def upload(video_path: str, analysis: dict) -> str:
    try:
        import phase5_upload as p5
        script = {
            "title": analysis["title"],
            "tags":  analysis["tags"],
            "hook":  analysis["hook"],
            "body":  analysis["narration"][:200],
            "cta":   "Follow for daily tactical breakdowns!",
        }
        topic = {"id": int(time.time()), "title": analysis["title"],
                 "subject": analysis["hook"], "category": "FIFA World Cup 2026"}
        result = p5.upload_all(video_path, script, topic)
        url = result.get("youtube")
        if url: log(f"YouTube: {url}")
        return url
    except Exception as e:
        log(f"Upload error: {e}"); return None


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def run_one_analysis():
    config.assert_safe_pipeline()
    log("=" * 60)
    log("  GOAL ANALYSIS CREATOR — ANIMATED TACTICAL BREAKDOWN")
    log("=" * 60)

    state = load_state()
    analysis = pick_analysis(state)
    state["count"] = state.get("count", 0) + 1
    save_state(state)

    log(f"Analysis #{state['count']}: {analysis['hook'][:55]}")

    try:
        # 1. Generate video frames as ImageClip sequence
        log(f"Generating {DURATION}s animated tactical diagram...")
        total_frames = DURATION * FPS

        def frame_fn(t):
            return make_frame(t, analysis)

        video = VideoFileClip.__new__(VideoFileClip)
        from moviepy import VideoClip
        video = VideoClip(frame_fn, duration=DURATION)

        # 2. Voiceover
        vo_path = generate_voiceover(analysis["narration"])
        vo_clip = AudioFileClip(vo_path)
        # Pad narration to video duration
        vo_dur  = min(vo_clip.duration, DURATION - 1)
        vo_clip = _dur(vo_clip, vo_dur)

        # 3. Music
        music_path = get_music()
        raw_music  = AudioFileClip(music_path)
        if raw_music.duration < DURATION:
            from moviepy import concatenate_audioclips
            raw_music = concatenate_audioclips(
                [raw_music] * (int(DURATION/raw_music.duration)+2))
        music  = _dur(raw_music, DURATION)
        music  = _vol(music, 0.08)   # very quiet under clear narration

        # 4. Mix audio
        try:
            mixed = CompositeAudioClip([music, vo_clip])
        except Exception:
            mixed = vo_clip
        mixed = _dur(mixed, DURATION)
        video = _audio(video, mixed)
        video = _dur(video, DURATION)

        # 5. Render
        os.makedirs(config.VIDEOS_DIR, exist_ok=True)
        out_path = os.path.join(config.VIDEOS_DIR, f"analysis_{int(time.time())}.mp4")
        log(f"Rendering HD → {out_path}")
        video.write_videofile(
            out_path, fps=FPS, codec="libx264", audio_codec="aac",
            audio_bitrate="384k", logger=None,
            ffmpeg_params=[
                "-vf",     f"scale={WIDTH}:{HEIGHT}",
                "-crf",    "18",
                "-preset", "slow",
                "-b:v",    "8M",
                "-pix_fmt","yuv420p",
                "-movflags","+faststart",
            ],
        )
        video.close()
        log("✅ Analysis video rendered!")

        # 6. Upload
        url = upload(out_path, analysis)
        log("=" * 60)
        log(f"  ANALYSIS #{state['count']} COMPLETE!")
        log(f"  {analysis['title'][:60]}")
        if url: log(f"  YouTube: {url}")
        else:   log(f"  Saved:   {out_path}")
        log("=" * 60)

    except Exception as e:
        log(f"ERROR: {e}")
        import traceback; traceback.print_exc()


def main():
    log("=" * 60)
    log("  ANALYSIS CREATOR — RUNS EVERY 6 HOURS")
    log("  Tactical diagrams. AI voice. Zero copyright.")
    log("=" * 60)
    run_one_analysis()
    # Run every 6 hours (alternating with facts Shorts)
    while True:
        log("Next analysis in 6 hours...")
        time.sleep(6 * 60 * 60)
        run_one_analysis()


if __name__ == "__main__":
    main()
