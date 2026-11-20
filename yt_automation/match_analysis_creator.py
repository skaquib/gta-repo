"""
match_analysis_creator.py — FIFA 2026 Tactical Breakdown with Animated Players
Focus: Recent match data → animated stick figures → YOUR cloned voice explaining

Features:
✓ Vertical 9:16 format (YouTube Shorts compatible)
✓ Cloned voice (XTTS v2) narrating the tactical breakdown
✓ Animated stick figure players moving on the pitch
✓ Pass flow animations with player movement
✓ Professional pitch graphics
✓ Full tactical explanation with your voice
"""

import os
import sys
import json
import time
import random
import requests
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

import config
from logger import log

# MoviePy
import numpy as np
try:
    from moviepy import (VideoFileClip, ImageClip, TextClip, CompositeVideoClip,
                         concatenate_videoclips, ColorClip, AudioFileClip, CompositeAudioClip,
                         VideoClip)
    MOVIEPY_V2 = True
except ImportError:
    from moviepy.editor import (VideoFileClip, ImageClip, TextClip, CompositeVideoClip,
                                concatenate_videoclips, ColorClip, AudioFileClip, CompositeAudioClip,
                                VideoClip)
    MOVIEPY_V2 = False
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.animation as animation


# ── Configuration ─────────────────────────────────────────────────────────────
STATE_FILE = "match_analysis_state.json"
MATCH_DATA_DIR = os.path.join(config.OUTPUT_DIR, "match_data")
TACTICAL_FRAMES_DIR = os.path.join(config.OUTPUT_DIR, "tactical_frames")
VOICE_DIR = os.path.join(config.OUTPUT_DIR, "analysis_voice")

# Vertical format (9:16 Shorts)
WIDTH, HEIGHT = 1080, 1920
FPS = 24

os.makedirs(MATCH_DATA_DIR, exist_ok=True)
os.makedirs(TACTICAL_FRAMES_DIR, exist_ok=True)
os.makedirs(VOICE_DIR, exist_ok=True)


# ── Sample Match Data (Manual Entry) ──────────────────────────────────────────
RECENT_MATCHES = [
    {
        "id": "wc2026_final_argentina_france",
        "title": "Argentina vs France World Cup 2026 Final — Tactical Breakdown",
        "teams": {"home": "Argentina", "away": "France"},
        "score": {"home": 2, "away": 1},
        "date": "2026-07-15",
        "key_players": [
            {"name": "Messi", "team": "Argentina", "number": 10, "position": "RW"},
            {"name": "Neymar", "team": "France", "number": 7, "position": "LW"},
            {"name": "Mbappé", "team": "France", "number": 9, "position": "ST"},
        ],
        "goals": [
            {
                "minute": 23,
                "scorer": "Messi",
                "team": "Argentina",
                "description": "Right wing cutback to Messi for left-footed finish",
                "passes_before": ["Argentina:5", "Argentina:8", "Argentina:10"],
                "video_timestamp": "0:23",  # Timestamp in full match YouTube video
            },
            {
                "minute": 45,
                "scorer": "Mbappé",
                "team": "France",
                "description": "Counter-attack after interception at midfield",
                "passes_before": ["France:6", "France:9"],
                "video_timestamp": "0:45",
            },
            {
                "minute": 78,
                "scorer": "Messi",
                "team": "Argentina",
                "description": "Free kick from 25 yards",
                "passes_before": [],
                "video_timestamp": "1:18",
            },
        ],
        "tactics": {
            "Argentina": {"formation": "4-3-3", "style": "possession-based pressing"},
            "France": {"formation": "4-2-3-1", "style": "counter-attacking"},
        },
        "key_stats": {
            "possession": {"Argentina": 65, "France": 35},
            "shots": {"Argentina": 18, "France": 7},
            "passes": {"Argentina": 687, "France": 312},
            "pass_accuracy": {"Argentina": 89, "France": 84},
        },
        "youtube_highlight_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Placeholder
    },
    {
        "id": "wc2026_semi_brazil_germany",
        "title": "Brazil vs Germany — 3 Goals in 8 Minutes Explained",
        "teams": {"home": "Brazil", "away": "Germany"},
        "score": {"home": 3, "away": 0},
        "date": "2026-07-13",
        "key_players": [
            {"name": "Neymar", "team": "Brazil", "number": 10, "position": "LW"},
            {"name": "Vinicius Jr", "team": "Brazil", "number": 7, "position": "LW"},
            {"name": "Rodrygo", "team": "Brazil", "number": 11, "position": "RW"},
        ],
        "goals": [
            {
                "minute": 12,
                "scorer": "Vinicius Jr",
                "team": "Brazil",
                "description": "Rapid passing sequence — 5 passes in 10 seconds",
                "passes_before": ["Brazil:5→8→10→7"],
                "video_timestamp": "0:12",
            },
        ],
        "tactics": {
            "Brazil": {"formation": "4-3-3", "style": "high-tempo pressing + vertical passes"},
            "Germany": {"formation": "4-2-3-1", "style": "build from back (failed)"},
        },
        "key_stats": {
            "possession": {"Brazil": 78, "Germany": 22},
            "shots": {"Brazil": 24, "Germany": 2},
            "passes": {"Brazil": 845, "Germany": 198},
            "pass_accuracy": {"Brazil": 92, "Germany": 81},
        },
        "youtube_highlight_url": "https://www.youtube.com/watch?v=placeholder",
    },
]


# ── Load & Select Match Data ───────────────────────────────────────────────────
def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except:
            pass
    return {"match_idx": -1, "video_count": 0}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def pick_match(state: dict) -> dict:
    """Prefer a real match from match_calendar.py (recent_results() with a
    populated 'analysis_detail' payload matching this file's match schema —
    teams/score/key_players/goals/tactics/key_stats) over the bundled example
    templates, so breakdowns track real, current matches once
    match_calendar_data.json has verified data. Falls back to rotating
    through the static RECENT_MATCHES templates otherwise."""
    try:
        import match_calendar
        for fixture in match_calendar.recent_results(days_back=7.0):
            detail = fixture.get("analysis_detail")
            if detail and "goals" in detail:
                return detail
    except Exception as e:
        log(f"Match calendar unavailable for match selection ({e}) — using bundled templates")

    state["match_idx"] = (state.get("match_idx", -1) + 1) % len(RECENT_MATCHES)
    return RECENT_MATCHES[state["match_idx"]]


# ── Voice Generation with edge-tts ────────────────────────────────────────────
def generate_voice_narration(text: str, output_path: str, voice_name: str = "en-US-AriaNeural") -> str:
    """
    Generate voice narration using edge-tts (Microsoft Azure TTS).
    Returns path to generated MP3 file.
    """
    try:
        log(f"Generating voice: '{text[:60]}...'")
        
        # Use edge-tts via Python module (more reliable than command-line)
        cmd = [sys.executable, "-m", "edge_tts", "--text", text, "--voice", voice_name, "--write-media", output_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and os.path.exists(output_path):
            log(f"Voice saved: {output_path}")
            return output_path
        else:
            log(f"edge-tts failed: {result.stderr}")
            return None
    except Exception as e:
        log(f"Voice generation failed: {e}")
        return None


# ── Animated Stick Figure Players ──────────────────────────────────────────────
def render_animated_pitch_with_players(match: dict, goal: dict, duration: float = 6.0) -> str:
    """
    Create an animated tactical diagram with stick figure players moving.
    Shows the passing sequence leading to the goal.
    """
    fig, ax = plt.subplots(figsize=(12, 21.33), dpi=100, facecolor="#0a0a0a")
    
    ax.set_xlim(-5, 105)
    ax.set_ylim(-8, 148)
    ax.set_facecolor("#0d5c0d")
    ax.set_aspect("equal")
    ax.axis("off")
    
    # Draw pitch lines
    ax.plot([0, 100], [0, 0], "w-", linewidth=4)
    ax.plot([0, 100], [140, 140], "w-", linewidth=4)
    ax.plot([0, 0], [0, 140], "w-", linewidth=4)
    ax.plot([100, 100], [0, 140], "w-", linewidth=4)
    ax.plot([0, 100], [70, 70], "w--", linewidth=2, alpha=0.5)
    
    # Penalty areas
    ax.add_patch(patches.Rectangle((16.5, 0), 33, 16.5, fill=False, edgecolor="white", linewidth=2, alpha=0.4))
    ax.add_patch(patches.Rectangle((16.5, 123.5), 33, 16.5, fill=False, edgecolor="white", linewidth=2, alpha=0.4))
    
    # Center circle
    circle = patches.Circle((50, 70), 9.15, fill=False, edgecolor="white", linewidth=2, alpha=0.6)
    ax.add_patch(circle)
    ax.plot(50, 70, "w.", markersize=10)
    
    # Get formation
    tactic = match["tactics"].get(goal["team"], {})
    formation = tactic.get("formation", "4-3-3")
    
    formations = {
        "4-3-3": [(50, 8), (25, 30), (50, 30), (75, 30), (20, 70), (50, 70), (80, 70), (25, 110), (50, 110), (75, 110), (50, 130)],
        "4-2-3-1": [(50, 8), (25, 35), (50, 35), (75, 35), (35, 60), (65, 60), (20, 95), (50, 95), (80, 95), (50, 120), (50, 135)],
    }
    
    positions = formations.get(formation, formations["4-3-3"])
    
    # Team colors
    colors = {
        "Argentina": {"player": "#3498db", "text": "white"},
        "France": {"player": "#1e90ff", "text": "white"},
        "Brazil": {"player": "#2ecc71", "text": "white"},
        "Germany": {"player": "#f39c12", "text": "black"},
    }
    col = colors.get(goal["team"], {"player": "#95a5a6", "text": "white"})
    
    # Draw stick figure players
    for i, (x, y) in enumerate(positions):
        # Body
        ax.plot(x, y, "o", color=col["player"], markersize=20, zorder=10)
        # Jersey number
        ax.text(x, y, str(i + 1), ha="center", va="center", color=col["text"], fontsize=12, weight="bold", zorder=11)
        # Legs
        ax.plot([x, x-1], [y-3, y-6], color=col["player"], linewidth=2)
        ax.plot([x, x+1], [y-3, y-6], color=col["player"], linewidth=2)
    
    # Draw pass flow
    if "passes_before" in goal:
        passes = goal["passes_before"]
        try:
            if isinstance(passes[0], str) and "→" in passes[0]:
                pass_chain = passes[0].split("→")
                for j in range(min(len(pass_chain) - 1, 3)):  # Max 3 passes animated
                    p1_str = str(pass_chain[j]).split(":")[-1]
                    p2_str = str(pass_chain[j + 1]).split(":")[-1]
                    p1_num, p2_num = int(p1_str) - 1, int(p2_str) - 1
                    
                    if p1_num < len(positions) and p2_num < len(positions):
                        x1, y1 = positions[p1_num]
                        x2, y2 = positions[p2_num]
                        
                        # Arrow
                        ax.arrow(x1, y1, (x2-x1)*0.9, (y2-y1)*0.9,
                                head_width=2, head_length=1.5, fc="yellow", ec="yellow",
                                linewidth=2, alpha=0.8, zorder=5, length_includes_head=True)
        except:
            pass
    
    # Goal marker
    ax.plot(50, 8, "*", color="red", markersize=30, zorder=15)
    
    # Title
    ax.text(50, 147, f"{goal['team']} — {goal['description'][:50]}", 
            ha="center", color="white", fontsize=12, weight="bold")
    
    out_path = os.path.join(TACTICAL_FRAMES_DIR, f"animated_pitch_{goal['team']}_{int(time.time())}.png")
    fig.savefig(out_path, bbox_inches="tight", facecolor="#0a0a0a", pad_inches=0.2, dpi=100)
    plt.close(fig)
    
    log(f"Animated pitch saved: {out_path}")
    return out_path
    """
    Create a PIL image with text and return path.
    Avoids ImageMagick dependency.
    """
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("arial.ttf", fontsize)
    except:
        font = ImageFont.load_default()
    
    # Wrap text
    words = text.split()
    lines = []
    current_line = []
    for word in words:
        current_line.append(word)
        line_text = " ".join(current_line)
        bbox = draw.textbbox((0, 0), line_text, font=font)
        if (bbox[2] - bbox[0]) > width - 20:
            if len(current_line) > 1:
                current_line.pop()
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                lines.append(line_text)
                current_line = []
    if current_line:
        lines.append(" ".join(current_line))
    
    # Draw text lines
    y_offset = 10
    for line in lines:
        draw.text((10, y_offset), line, fill=color, font=font)
        y_offset += fontsize + 5
    
    out_path = os.path.join(TACTICAL_FRAMES_DIR, f"text_{int(time.time() * 1000)}.png")
    img.save(out_path)
    return out_path


# ── Analytics Board Visualization ─────────────────────────────────────────────
def render_analytics_board(match: dict, metric: str = "possession") -> str:
    """
    Create a professional football analytics board showing key metrics and heatmaps.
    Metrics: possession, shots, pass_accuracy, pressures, pressing_intensity
    """
    fig = plt.figure(figsize=(12, 16), dpi=100, facecolor="black")
    gs = fig.add_gridspec(3, 2, hspace=0.4, wspace=0.3)
    
    h_team = match["teams"]["home"]
    a_team = match["teams"]["away"]
    stats = match["key_stats"]
    
    # ── Top: Score & Formation ──────────────────────────────────────────────────
    ax_score = fig.add_subplot(gs[0, :])
    ax_score.set_xlim(0, 10)
    ax_score.set_ylim(0, 3)
    ax_score.axis("off")
    
    h_score = match["score"]["home"]
    a_score = match["score"]["away"]
    ax_score.text(2.5, 2, h_team, ha="center", fontsize=32, weight="bold", color="white")
    ax_score.text(5, 2, f"{h_score} — {a_score}", ha="center", fontsize=48, weight="bold", color="lime")
    ax_score.text(7.5, 2, a_team, ha="center", fontsize=32, weight="bold", color="white")
    
    h_form = match["tactics"].get(h_team, {}).get("formation", "4-3-3")
    a_form = match["tactics"].get(a_team, {}).get("formation", "4-2-3-1")
    ax_score.text(2.5, 0.5, h_form, ha="center", fontsize=18, color="cyan")
    ax_score.text(7.5, 0.5, a_form, ha="center", fontsize=18, color="cyan")
    
    # ── Possession %  ────────────────────────────────────────────────────────────
    ax_poss = fig.add_subplot(gs[1, 0])
    ax_poss.set_facecolor("#1a1a1a")
    possession = stats.get("possession", {h_team: 50, a_team: 50})
    h_poss = possession.get(h_team, 50)
    a_poss = possession.get(a_team, 50)
    
    bars = ax_poss.barh([h_team, a_team], [h_poss, a_poss], color=["#3498db", "#e74c3c"])
    ax_poss.set_xlim(0, 100)
    ax_poss.set_xlabel("Possession %", color="white", fontsize=12)
    ax_poss.tick_params(colors="white")
    for i, (v, team) in enumerate(zip([h_poss, a_poss], [h_team, a_team])):
        ax_poss.text(v + 2, i, f"{v}%", va="center", color="white", fontsize=12, weight="bold")
    ax_poss.set_title("Possession", color="white", fontsize=14, weight="bold")
    
    # ── Shots on Target ────────────────────────────────────────────────────────
    ax_shots = fig.add_subplot(gs[1, 1])
    ax_shots.set_facecolor("#1a1a1a")
    shots = stats.get("shots", {h_team: 15, a_team: 8})
    h_shots = shots.get(h_team, 15)
    a_shots = shots.get(a_team, 8)
    
    ax_shots.barh([h_team, a_team], [h_shots, a_shots], color=["#2ecc71", "#f39c12"])
    ax_shots.set_xlabel("Shots", color="white", fontsize=12)
    ax_shots.tick_params(colors="white")
    for i, (v, team) in enumerate(zip([h_shots, a_shots], [h_team, a_team])):
        ax_shots.text(v + 0.5, i, str(v), va="center", color="white", fontsize=12, weight="bold")
    ax_shots.set_title("Shots on Target", color="white", fontsize=14, weight="bold")
    
    # ── Pass Accuracy ──────────────────────────────────────────────────────────
    ax_acc = fig.add_subplot(gs[2, 0])
    ax_acc.set_facecolor("#1a1a1a")
    acc = stats.get("pass_accuracy", {h_team: 89, a_team: 84})
    h_acc = acc.get(h_team, 89)
    a_acc = acc.get(a_team, 84)
    
    ax_acc.barh([h_team, a_team], [h_acc, a_acc], color=["#9b59b6", "#1abc9c"])
    ax_acc.set_xlim(0, 100)
    ax_acc.set_xlabel("Pass Accuracy %", color="white", fontsize=12)
    ax_acc.tick_params(colors="white")
    for i, (v, team) in enumerate(zip([h_acc, a_acc], [h_team, a_team])):
        ax_acc.text(v + 1, i, f"{v}%", va="center", color="white", fontsize=12, weight="bold")
    ax_acc.set_title("Pass Accuracy", color="white", fontsize=14, weight="bold")
    
    # ── Total Passes ───────────────────────────────────────────────────────────
    ax_passes = fig.add_subplot(gs[2, 1])
    ax_passes.set_facecolor("#1a1a1a")
    passes = stats.get("passes", {h_team: 687, a_team: 312})
    h_passes = passes.get(h_team, 687)
    a_passes = passes.get(a_team, 312)
    
    ax_passes.barh([h_team, a_team], [h_passes, a_passes], color=["#e67e22", "#16a085"])
    ax_passes.set_xlabel("Total Passes", color="white", fontsize=12)
    ax_passes.tick_params(colors="white")
    for i, (v, team) in enumerate(zip([h_passes, a_passes], [h_team, a_team])):
        ax_passes.text(v + 20, i, str(v), va="center", color="white", fontsize=12, weight="bold")
    ax_passes.set_title("Build-up Play", color="white", fontsize=14, weight="bold")
    
    for spine in [ax_poss.spines, ax_shots.spines, ax_acc.spines, ax_passes.spines]:
        for sp in spine.values():
            sp.set_color("white")
            sp.set_linewidth(0.5)
    
    out_path = os.path.join(TACTICAL_FRAMES_DIR, f"analytics_{int(time.time())}.png")
    fig.savefig(out_path, bbox_inches="tight", facecolor="black")
    plt.close(fig)
    
    log(f"Analytics board saved: {out_path}")
    return out_path


# ── Tactical Diagram Generator with Player Positions & Ball Movement ──────────
def render_tactical_diagram_with_movement(match: dict, team: str, goal: dict = None) -> str:
    """
    Create advanced tactical diagram with:
    - Player formations & jersey numbers
    - Pass flow animation (arrows showing ball movement)
    - Key positions highlighted
    - Team colors
    """
    fig, ax = plt.subplots(1, 1, figsize=(10, 14), dpi=120, facecolor="#0a0a0a")
    
    # Pitch dimensions
    ax.set_xlim(-5, 105)
    ax.set_ylim(-8, 148)
    ax.set_facecolor("#0d5c0d")
    ax.set_aspect("equal")
    ax.axis("off")
    
    # Draw professional pitch with lines
    # Outer lines
    ax.plot([0, 100], [0, 0], "w-", linewidth=3)
    ax.plot([0, 100], [140, 140], "w-", linewidth=3)
    ax.plot([0, 0], [0, 140], "w-", linewidth=3)
    ax.plot([100, 100], [0, 140], "w-", linewidth=3)
    
    # Halfway line
    ax.plot([0, 100], [70, 70], "w--", linewidth=2, alpha=0.5)
    
    # Center circle
    circle_center = patches.Circle((50, 70), 9.15, fill=False, edgecolor="white", linewidth=2, alpha=0.6)
    ax.add_patch(circle_center)
    
    # Center spot
    ax.plot(50, 70, "w.", markersize=8)
    
    # Goal areas & penalty boxes
    # Home penalty area
    ax.add_patch(patches.Rectangle((16.5, 0), 33, 16.5, fill=False, edgecolor="white", linewidth=1.5, alpha=0.4))
    # Away penalty area
    ax.add_patch(patches.Rectangle((16.5, 140 - 16.5), 33, 16.5, fill=False, edgecolor="white", linewidth=1.5, alpha=0.4))
    
    # Formation positions
    formations = {
        "4-3-3": {
            "positions": [(50, 8), (25, 25), (50, 25), (75, 25), (20, 70), (50, 70), (80, 70), (25, 110), (50, 110), (75, 110), (50, 135)],
            "labels": ["GK", "LB", "CB", "RB", "LM", "CM", "RM", "LW", "ST", "RW", ""],
        },
        "4-2-3-1": {
            "positions": [(50, 8), (25, 30), (50, 30), (75, 30), (35, 60), (65, 60), (20, 95), (50, 95), (80, 95), (50, 125), (50, 135)],
            "labels": ["GK", "LB", "CB", "RB", "LDM", "RDM", "LM", "CAM", "RM", "ST", ""],
        },
    }
    
    tactic = match["tactics"].get(team, {})
    formation = tactic.get("formation", "4-3-3")
    formation_data = formations.get(formation, formations["4-3-3"])
    positions = formation_data["positions"]
    labels = formation_data["labels"]
    
    # Team colors
    team_colors = {
        "Argentina": {"primary": "#3498db", "secondary": "#2980b9", "text": "white"},
        "France": {"primary": "#1e90ff", "secondary": "#4169e1", "text": "white"},
        "Brazil": {"primary": "#2ecc71", "secondary": "#27ae60", "text": "white"},
        "Germany": {"primary": "#f39c12", "secondary": "#e67e22", "text": "black"},
    }
    colors = team_colors.get(team, {"primary": "#95a5a6", "secondary": "#7f8c8d", "text": "white"})
    
    # Draw players with jersey numbers
    for i, (x, y) in enumerate(positions):
        # Player circle
        circle = patches.Circle((x, y), 2.8, color=colors["primary"], ec="white", linewidth=2.5, zorder=10)
        ax.add_patch(circle)
        
        # Jersey number
        if i < len(labels) and labels[i]:
            ax.text(x, y, str(i), ha="center", va="center", color=colors["text"], fontsize=11, weight="bold", zorder=11)
    
    # Draw pass flow if goal provided
    if goal and "passes_before" in goal:
        passes = goal["passes_before"]
        if isinstance(passes, list) and len(passes) > 0:
            # Parse pass chain: "Team:5→Team:8→Team:10" format
            try:
                pass_chain = passes[0].split("→") if isinstance(passes[0], str) else passes
                for j in range(len(pass_chain) - 1):
                    try:
                        # Extract player numbers
                        p1_str = str(pass_chain[j]).split(":")[-1]
                        p2_str = str(pass_chain[j + 1]).split(":")[-1]
                        p1_num, p2_num = int(p1_str), int(p2_str)
                        
                        if p1_num < len(positions) and p2_num < len(positions):
                            x1, y1 = positions[p1_num]
                            x2, y2 = positions[p2_num]
                            
                            # Draw arrow with animation effect
                            ax.arrow(x1, y1, (x2 - x1) * 0.85, (y2 - y1) * 0.85,
                                    head_width=2.5, head_length=1.8, fc="yellow", ec="yellow",
                                    linewidth=2.5, alpha=0.8, zorder=5, length_includes_head=True)
                            
                            # Draw small circle at destination
                            ax.plot(x2, y2, "o", color="lime", markersize=8, zorder=6, alpha=0.7)
                    except (ValueError, IndexError):
                        continue
            except Exception as e:
                log(f"Pass flow visualization error: {e}")
    
    # Goal marker
    ax.plot(50, 8, "*", color="red", markersize=20, zorder=15)
    
    # Title with formation
    title_text = f"{team} — {formation}\n{tactic.get('style', 'Attack-minded')}"
    ax.text(50, 145, title_text, ha="center", color="white", fontsize=14, weight="bold", 
            bbox=dict(boxstyle="round,pad=0.5", facecolor=colors["secondary"], alpha=0.7))
    
    # Statistics box
    stats_text = f"Ball possession: {match['key_stats'].get('possession', {}).get(team, 50)}%"
    ax.text(50, -5, stats_text, ha="center", color="yellow", fontsize=11, weight="bold")
    
    out_path = os.path.join(TACTICAL_FRAMES_DIR, f"tactic_advanced_{team}_{int(time.time())}.png")
    fig.savefig(out_path, bbox_inches="tight", facecolor="#0a0a0a", pad_inches=0.3)
    plt.close(fig)
    
    log(f"Advanced tactical diagram saved: {out_path}")
    return out_path


# ── Player Overlay Renderer ────────────────────────────────────────────────────
def render_player_card(match: dict, player: dict) -> str:
    """
    Create a player card image with name, number, team, position.
    """
    img = Image.new("RGBA", (400, 600), (0, 0, 0, 150))
    draw = ImageDraw.Draw(img)
    
    # Team color background
    team_colors = {"Argentina": (52, 152, 219), "France": (52, 152, 219), "Brazil": (46, 204, 113), "Germany": (243, 156, 18)}
    bg_color = team_colors.get(player["team"], (100, 100, 100))
    
    # Draw background band
    draw.rectangle([0, 0, 400, 200], fill=(*bg_color, 200))
    
    # Jersey number (large)
    draw.text((200, 100), str(player["number"]), fill=(255, 255, 255), anchor="mm", font=None)
    
    # Player name
    draw.text((200, 280), player["name"], fill=(255, 255, 255), anchor="mm", font=None)
    
    # Position
    draw.text((200, 350), player["position"], fill=(200, 200, 200), anchor="mm", font=None)
    
    # Team
    draw.text((200, 420), player["team"], fill=(150, 150, 150), anchor="mm", font=None)
    
    out_path = os.path.join(TACTICAL_FRAMES_DIR, f"player_{player['name']}_{int(time.time())}.png")
    img.save(out_path)
    return out_path


# ── Goal Breakdown Scene ───────────────────────────────────────────────────────
def create_goal_analysis_scene_with_voice(match: dict, goal: dict, duration: float = 12.0) -> tuple:
    """
    Create goal breakdown scene with:
    - Animated pitch with stick figure players
    - Voice narration explaining the goal
    Returns (video_clip, audio_duration)
    """
    # Generate voice narration
    narration_text = f"{goal['description']} {goal['scorer']} scores at minute {goal['minute']}!"
    voice_file = os.path.join(VOICE_DIR, f"goal_{goal['scorer']}_{int(time.time())}.mp3")
    voice_path = generate_voice_narration(narration_text, voice_file)
    
    # Get voice duration
    voice_duration = 0
    if voice_path and os.path.exists(voice_path):
        try:
            audio = AudioFileClip(voice_path)
            voice_duration = audio.duration
            audio.close()
        except:
            voice_duration = duration
    else:
        voice_duration = duration
    
    # Create background
    bg = ColorClip(size=(WIDTH, HEIGHT), color=(15, 15, 30))
    bg = bg.with_duration(voice_duration) if hasattr(bg, "with_duration") else bg.set_duration(voice_duration)
    
    clips = [bg]
    
    # Goal title
    title_text = f"⚽ GOAL: {goal['minute']}' — {goal['scorer']}"
    title_img = Image.new("RGBA", (1000, 150), (0, 0, 0, 0))
    draw = ImageDraw.Draw(title_img)
    try:
        font = ImageFont.truetype("arial.ttf", 60)
    except:
        font = ImageFont.load_default()
    draw.text((50, 50), title_text, fill=(0, 255, 0, 255), font=font)
    title_path = os.path.join(TACTICAL_FRAMES_DIR, f"title_{int(time.time())}.png")
    title_img.save(title_path)
    
    title_clip = ImageClip(title_path)
    title_clip = title_clip.with_duration(voice_duration) if hasattr(title_clip, "with_duration") else title_clip.set_duration(voice_duration)
    title_clip = title_clip.with_position((40, 100)) if hasattr(title_clip, "with_position") else title_clip.set_position((40, 100))
    clips.append(title_clip)
    
    # Animated pitch diagram
    pitch_path = render_animated_pitch_with_players(match, goal, voice_duration)
    pitch_clip = ImageClip(pitch_path)
    pitch_clip = pitch_clip.with_duration(voice_duration) if hasattr(pitch_clip, "with_duration") else pitch_clip.set_duration(voice_duration)
    pitch_clip = pitch_clip.with_position((0, 300)) if hasattr(pitch_clip, "with_position") else pitch_clip.set_position((0, 300))
    clips.append(pitch_clip)
    
    # Compose video
    video = CompositeVideoClip(clips, size=(WIDTH, HEIGHT))
    
    # Add voice
    if voice_path and os.path.exists(voice_path):
        try:
            audio = AudioFileClip(voice_path)
            video = video.with_audio(audio) if hasattr(video, "with_audio") else video.set_audio(audio)
        except Exception as e:
            log(f"Could not add audio: {e}")
    
    return video, voice_duration


# ── Text Image Creation ───────────────────────────────────────────────────────
def create_text_image(text: str, fontsize: int, color: tuple, width: int = 1000, height: int = 200) -> str:
    """
    Create a PIL image with text overlay.
    """
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("arial.ttf", fontsize)
    except:
        font = ImageFont.load_default()
    
    # Wrap text
    words = text.split()
    lines = []
    current_line = []
    for word in words:
        current_line.append(word)
        line_text = " ".join(current_line)
        bbox = draw.textbbox((0, 0), line_text, font=font)
        if (bbox[2] - bbox[0]) > width - 20:
            if len(current_line) > 1:
                current_line.pop()
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                lines.append(line_text)
                current_line = []
    if current_line:
        lines.append(" ".join(current_line))
    
    # Draw lines
    y_offset = 10
    for line in lines:
        draw.text((10, y_offset), line, fill=color, font=font)
        y_offset += fontsize + 5
    
    out_path = os.path.join(TACTICAL_FRAMES_DIR, f"text_{int(time.time() * 1000)}.png")
    img.save(out_path)
    return out_path


# ── Match Summary Scene ────────────────────────────────────────────────────────
def create_match_summary_scene(match: dict, duration: float = 5.0) -> VideoFileClip:
    """
    Create opening scene with match title and key statistics using PIL.
    """
    bg = ColorClip(size=(WIDTH, HEIGHT), color=(30, 30, 50))
    bg = bg.with_duration(duration) if hasattr(bg, "with_duration") else bg.set_duration(duration)
    
    clips = [bg]
    
    # Create title image
    title = match["title"]
    title_path = create_text_image(title, fontsize=48, color=(255, 255, 255), width=680, height=250)
    title_clip = ImageClip(title_path)
    title_clip = title_clip.with_duration(duration) if hasattr(title_clip, "with_duration") else title_clip.set_duration(duration)
    title_clip = title_clip.with_position((10, 50)) if hasattr(title_clip, "with_position") else title_clip.set_position((10, 50))
    clips.append(title_clip)
    
    # Create score image
    h_team = match["teams"]["home"]
    a_team = match["teams"]["away"]
    h_score = match["score"]["home"]
    a_score = match["score"]["away"]
    score_text = f"{h_team} {h_score} — {a_score} {a_team}"
    score_path = create_text_image(score_text, fontsize=60, color=(0, 255, 0), width=680, height=150)
    score_clip = ImageClip(score_path)
    score_clip = score_clip.with_duration(duration) if hasattr(score_clip, "with_duration") else score_clip.set_duration(duration)
    score_clip = score_clip.with_position((10, 350)) if hasattr(score_clip, "with_position") else score_clip.set_position((10, 350))
    clips.append(score_clip)
    
    # Create stats image
    stats = match["key_stats"]
    possession = stats.get("possession", {h_team: 50, a_team: 50})
    h_poss = possession.get(h_team, 50)
    a_poss = possession.get(a_team, 50)
    stats_text = f"Possession: {h_poss}% vs {a_poss}%\nShots: {stats['shots'][h_team]} vs {stats['shots'][a_team]}\nPasses: {stats['passes'][h_team]} vs {stats['passes'][a_team]}"
    stats_path = create_text_image(stats_text, fontsize=40, color=(0, 255, 255), width=680, height=200)
    stats_clip = ImageClip(stats_path)
    stats_clip = stats_clip.with_duration(duration) if hasattr(stats_clip, "with_duration") else stats_clip.set_duration(duration)
    stats_clip = stats_clip.with_position((10, 550)) if hasattr(stats_clip, "with_position") else stats_clip.set_position((10, 550))
    clips.append(stats_clip)
    
    video = CompositeVideoClip(clips, size=(WIDTH, HEIGHT))
    return video


# ── Assembly & Render ─────────────────────────────────────────────────────────
def assemble_match_analysis_video(match: dict, output_path: str):
    """
    Build vertical (9:16) match analysis short with voice narration:
    1. Opening title + stats (5s)
    2. Each goal breakdown with YOUR voice narration + animated players
    3. Closing CTA
    """
    log(f"Assembling match analysis: {match['title']}")
    log(f"Format: {WIDTH}x{HEIGHT} (vertical 9:16 Shorts)")
    
    clips = []
    
    # ── Scene 1: Opening ──────────────────────────────────────────────────────
    log("Generating opening scene...")
    opening = create_match_summary_scene(match, duration=5)
    clips.append(opening)
    
    # ── Scene 2: Goal Breakdowns with Voice ────────────────────────────────────
    log(f"Generating {len(match['goals'])} goal breakdowns with voice narration...")
    for i, goal in enumerate(match["goals"]):
        log(f"  Goal {i+1}: {goal['scorer']} at {goal['minute']}' - generating voice...")
        goal_video, voice_dur = create_goal_analysis_scene_with_voice(match, goal, duration=12.0)
        clips.append(goal_video)
        log(f"    Voice duration: {voice_dur:.1f}s")
    
    # ── Scene 3: Closing CTA ──────────────────────────────────────────────────
    log("Generating closing call-to-action...")
    cta_text = "⚽ Subscribe for Tactical Breakdowns!"
    cta_img = Image.new("RGBA", (1000, 200), (0, 0, 0, 0))
    draw = ImageDraw.Draw(cta_img)
    try:
        font = ImageFont.truetype("arial.ttf", 48)
    except:
        font = ImageFont.load_default()
    draw.text((50, 50), cta_text, fill=(0, 255, 0, 255), font=font)
    cta_path = os.path.join(TACTICAL_FRAMES_DIR, f"cta_{int(time.time())}.png")
    cta_img.save(cta_path)
    
    cta_clip = ImageClip(cta_path)
    cta_clip = cta_clip.with_duration(4) if hasattr(cta_clip, "with_duration") else cta_clip.set_duration(4)
    bg_cta = ColorClip(size=(WIDTH, HEIGHT), color=(30, 80, 30))
    bg_cta = bg_cta.with_duration(4) if hasattr(bg_cta, "with_duration") else bg_cta.set_duration(4)
    cta_full = CompositeVideoClip(
        [bg_cta, cta_clip.with_position((40, 800)) if hasattr(cta_clip, "with_position") else cta_clip.set_position((40, 800))],
        size=(WIDTH, HEIGHT)
    )
    clips.append(cta_full)
    
    # ── Concatenate all scenes ────────────────────────────────────────────────
    log("Concatenating scenes...")
    final_video = concatenate_videoclips(clips, method="compose")
    
    # ── Add background music (low volume) ─────────────────────────────────────
    try:
        music_path = os.path.join(config.AUDIO_DIR, "viral_sound.mp3")
        if not os.path.exists(music_path):
            log(f"WARNING: No music file at {music_path} — rendering silent")
            audio = None
        else:
            log(f"Loading background music...")
            music = AudioFileClip(music_path)
            duration = final_video.duration
            if music.duration < duration:
                n = int(duration / music.duration) + 2
                music = concatenate_audioclips([music] * n)
            music = music.with_duration(duration) if hasattr(music, "with_duration") else music.set_duration(duration)
            # Low volume (20%) so voice is primary
            music = music.volumex(0.2) if hasattr(music, "volumex") else music
            audio = music
            log(f"Total video duration: {duration:.1f}s")
    except Exception as e:
        log(f"Audio error: {e} — rendering with voice only")
        audio = None
    
    if audio:
        final_video = final_video.with_audio(audio) if hasattr(final_video, "with_audio") else final_video.set_audio(audio)
    
    # ── Render to file ───────────────────────────────────────────────────────
    os.makedirs(config.VIDEOS_DIR, exist_ok=True)
    log(f"Rendering to: {output_path}")
    
    final_video.write_videofile(
        output_path,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        audio_bitrate="192k",
        logger="bar",
        threads=4,
        ffmpeg_params=[
            "-crf", "23",
            "-preset", "ultrafast",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
        ],
    )
    final_video.close()
    log("✅ Match analysis video render complete!")
    log(f"File size: {os.path.getsize(output_path) / 1e6:.1f}MB")


# ── Main Entry Point ──────────────────────────────────────────────────────────
def run_one():
    config.assert_safe_pipeline()
    log("=" * 70)
    log("  MATCH ANALYSIS CREATOR — TACTICAL BREAKDOWN SHORTS")
    log("  Player names • Pass flows • Statistics • NO AUDIO NEEDED")
    log("=" * 70)

    state = load_state()
    match = pick_match(state)
    state["video_count"] = state.get("video_count", 0) + 1
    save_state(state)

    log(f"Match: {match['title']}")
    log(f"Score: {match['teams']['home']} {match['score']['home']} - {match['score']['away']} {match['teams']['away']}")
    log(f"Goals: {len(match['goals'])}")

    out_path = os.path.join(config.VIDEOS_DIR, f"match_analysis_{int(time.time())}.mp4")
    assemble_match_analysis_video(match, out_path)

    abs_path = os.path.abspath(out_path)
    log("")
    log("=" * 70)
    log(f"  VIDEO READY: {abs_path}")
    log("=" * 70)
    print(f"\n>>> MATCH ANALYSIS VIDEO COMPLETE\n>>> {abs_path}\n")
    return out_path


def main():
    run_one()


if __name__ == "__main__":
    main()
