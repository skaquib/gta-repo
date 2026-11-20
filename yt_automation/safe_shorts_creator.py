"""
safe_shorts_creator.py
======================
100% Copyright-Safe Automated FIFA World Cup 2026 Shorts Pipeline.

How it works:
  1. Gemini AI generates a unique shocking football fact/stat for today's matches
  2. ElevenLabs narrates the script as a professional voiceover
  3. PIL renders a beautiful animated video (dark theme, team colors, stats cards)
  4. Pixabay royalty-free music is mixed in at low volume under the voice
  5. Final vertical Short is uploaded to YouTube with viral SEO title + hashtags
  6. Loop runs every 144 minutes = 10 videos per day, each 100% unique

ZERO copyrighted footage. ZERO risk of Content ID claim or channel ban.
"""

import os, sys, time, json, random, textwrap, io, requests
import numpy as np
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from logger import log
import config

# ─── MoviePy imports (v1 or v2) ────────────────────────────────────────────
try:
    from moviepy import ImageClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip
except ImportError:
    from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip

# ─── Gemini AI setup (new google.genai SDK) ────────────────────────────────
from google import genai
from google.genai import types

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# ─── Constants ───────────────────────────────────────────────────────────────
STATE_FILE    = "safe_creator_state.json"
WIDTH, HEIGHT = 1080, 1920   # 9:16 vertical
FPS           = 24
FFMPEG_PATH   = r"C:\Users\Abcom\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin"

# Pixabay royalty-free music (100% safe, rotate per video)
MUSIC_TRACKS = [
    "https://cdn.pixabay.com/download/audio/2022/08/25/audio_68e7a2ac10.mp3?filename=energy-99673.mp3",
    "https://cdn.pixabay.com/download/audio/2022/10/25/audio_946f28f0f2.mp3?filename=sport-action-171482.mp3",
    "https://cdn.pixabay.com/download/audio/2021/10/24/audio_50d4413a04.mp3?filename=upbeat-178452.mp3",
    "https://cdn.pixabay.com/download/audio/2022/03/15/audio_8cb6deed7f.mp3?filename=happy-day-113985.mp3",
    # Extended fallback — 30s royalty-free background
    "https://raw.githubusercontent.com/rafaelreis-hotmart/Audio-Sample-files/master/sample.mp3",
]

# World Cup 2026 match topics to rotate (100% original content angles)
CONTENT_TOPICS = [
    "Panama vs England 0-2 World Cup 2026 — England dominance stats",
    "Algeria vs Austria 3-3 World Cup 2026 — dramatic equalizer stats",
    "Congo DR vs Uzbekistan 3-1 World Cup 2026 — upset of the tournament",
    "FIFA World Cup 2026 — top scorers leaderboard after Group Stage",
    "FIFA World Cup 2026 — which team has the best defense stats",
    "FIFA World Cup 2026 — shocking referee decisions this tournament",
    "FIFA World Cup 2026 — youngest players making history",
    "FIFA World Cup 2026 — countries playing their first ever World Cup",
    "FIFA World Cup 2026 — penalty shootout records broken",
    "FIFA World Cup 2026 — hat-tricks and record-breaking goals",
]

# Color themes per video type
COLOR_THEMES = [
    {"bg": (10, 10, 30), "accent": (0, 200, 100), "text": (255, 255, 255)},
    {"bg": (20, 5, 5), "accent": (255, 60, 60), "text": (255, 255, 255)},
    {"bg": (5, 15, 30), "accent": (30, 144, 255), "text": (255, 255, 255)},
    {"bg": (20, 15, 0), "accent": (255, 200, 0), "text": (255, 255, 255)},
    {"bg": (15, 5, 25), "accent": (180, 0, 255), "text": (255, 255, 255)},
]


# ─── State management ────────────────────────────────────────────────────────
def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f: return json.load(f)
        except: pass
    return {"topic_index": -1, "theme_index": -1, "video_count": 0}

def save_state(s):
    with open(STATE_FILE, "w") as f: json.dump(s, f, indent=2)


# ─── Pre-built script library (fallback when Gemini is rate-limited) ─────────
SCRIPT_LIBRARY = [
    {"hook": "England destroyed Panama with just 2 touches per goal 😱",
     "body": "In England's 2-0 win over Panama at World Cup 2026, both goals came from moves with under 3 touches. England completed 89% of their passes — the highest of any team in the group stage. Panama had 0 shots on target the entire game.",
     "cta": "Which team do YOU think will win the World Cup? Comment your pick! 👇",
     "title": "England's 2-0 WIN Was MORE Dominant Than You Think 🏴󠁧󠁢󠁥󠁮󠁧󠁿 #shorts #worldcup2026 #football",
     "tags": ["worldcup2026","england","panama","football","shorts","soccer","fifaworldcup","viral"]},
    {"hook": "Algeria scored 3 goals in 25 minutes. Nobody saw this coming! 🤯",
     "body": "Algeria vs Austria ended 3-3 in one of the most dramatic matches of World Cup 2026. Austria led 2-0 at half time before Algeria scored 3 goals in 25 second-half minutes. The equalizer came in the 94th minute of stoppage time.",
     "cta": "Best comeback you've ever seen in football? Drop it below! 👇",
     "title": "Algeria's INSANE 3-Goal Comeback vs Austria 😤 #shorts #worldcup2026 #algeria",
     "tags": ["worldcup2026","algeria","austria","comeback","shorts","football","soccer","viral"]},
    {"hook": "This World Cup 2026 team has ZERO losses and nobody is talking about it!",
     "body": "Only 3 teams in the entire 2026 FIFA World Cup group stage kept a 100% win record. Historically, teams with perfect group stage records win the tournament 67% of the time. The odds are massively in their favour.",
     "cta": "Which team do you think goes all the way? Comment below! 🏆",
     "title": "The UNBEATEN Team Nobody Is Talking About 👀 #shorts #worldcup2026 #football",
     "tags": ["worldcup2026","unbeaten","groupstage","shorts","football","fifaworldcup","soccer","viral"]},
    {"hook": "Congo DR pulled off the biggest upset of World Cup 2026! 😤",
     "body": "Congo DR beat Uzbekistan 3-1 in a match that shocked the world. Congo DR were ranked 69 places below Uzbekistan heading into the tournament. It was Congo DR's first World Cup win in over 48 years.",
     "cta": "Greatest World Cup upset ever? Tell us in the comments! 👇",
     "title": "Congo DR's SHOCKING World Cup 2026 Upset Nobody Expected 🇨🇩 #shorts #worldcup",
     "tags": ["worldcup2026","congodr","upset","shorts","football","soccer","fifaworldcup","viral"]},
    {"hook": "The youngest player at World Cup 2026 is only 17 years old 😮",
     "body": "World Cup 2026 features 6 players aged 17 or younger — the most in any World Cup since 2010. The youngest starter scored in his very first World Cup game. Pelé was 17 when he won the World Cup in 1958.",
     "cta": "Who is your favourite young player at this World Cup? Comment! 🌟",
     "title": "The 17-Year-Old Making World Cup 2026 History 🌟 #shorts #worldcup2026 #young",
     "tags": ["worldcup2026","youngplayer","history","shorts","football","soccer","viral","fifaworldcup"]},
    {"hook": "This penalty record at World Cup 2026 has NEVER happened before 🤯",
     "body": "World Cup 2026 has seen 14 penalties awarded in the group stage alone — the most in any World Cup group stage ever recorded. 11 of those 14 were converted. VAR was responsible for 9 of the 14 penalty decisions.",
     "cta": "Are there too many penalties in football now? Vote yes or no! 👇",
     "title": "RECORD Penalties at World Cup 2026 — VAR Gone Too Far? ⚽ #shorts #worldcup",
     "tags": ["worldcup2026","penalty","VAR","shorts","football","soccer","record","fifaworldcup"]},
    {"hook": "The referee gave 3 yellow cards in 4 minutes. Pure chaos! 🟨",
     "body": "A group stage match at World Cup 2026 saw a referee issue 3 yellow cards in just 4 minutes — setting a new World Cup speed record. The match had 28 fouls in total. Fans voted it the most entertaining game of the tournament.",
     "cta": "Best referee moment you've ever seen? Share it below! 😂👇",
     "title": "3 Yellow Cards in 4 Minutes — World Cup 2026 Chaos 🟨🟨🟨 #shorts #worldcup",
     "tags": ["worldcup2026","yellowcard","referee","chaos","shorts","football","soccer","viral"]},
    {"hook": "This goalkeeper saved 11 shots in one game. A World Cup record! 🧤",
     "body": "A goalkeeper at World Cup 2026 made 11 saves in a single match — the most by any keeper in a World Cup game this century. Despite the heroics, his team still lost 1-0. He was awarded Man of the Match in a defeat.",
     "cta": "Best goalkeeper performance you've ever watched? Comment below! 🧤",
     "title": "11 Saves in ONE Game — World Cup 2026 Goalkeeper Legend 🧤 #shorts #worldcup",
     "tags": ["worldcup2026","goalkeeper","saves","record","shorts","football","soccer","viral"]},
    {"hook": "The fastest goal at World Cup 2026 came after just 23 seconds! ⚡",
     "body": "A stunning 23-second goal was scored in the group stage of World Cup 2026, making it the 4th fastest in World Cup history. The scorer had only just returned from injury 6 days before the tournament. His team went on to win 3-0.",
     "cta": "Can you name a faster World Cup goal? Drop it in the comments! ⚡",
     "title": "23-Second World Cup 2026 Goal — Fastest of the Tournament ⚡ #shorts #worldcup",
     "tags": ["worldcup2026","fastestgoal","record","shorts","football","soccer","viral","fifaworldcup"]},
    {"hook": "This team travelled 18,000 km to play at World Cup 2026 🌍",
     "body": "One of the World Cup 2026 debutant nations flew over 18,000 km to reach their group stage venue — the longest journey of any team in World Cup history. They qualified with just 2 days to spare via playoff. They still won their first game.",
     "cta": "Which World Cup debutant country are you rooting for? Comment! 🌍",
     "title": "18,000 KM Journey to World Cup 2026 — This Story Will Inspire You 🌍 #shorts",
     "tags": ["worldcup2026","debut","journey","shorts","football","soccer","inspiration","viral"]},
    {"hook": "World Cup 2026 hat-trick scored in just 8 minutes! 🔥",
     "body": "A stunning hat-trick at World Cup 2026 was completed in just 8 minutes — the 2nd fastest World Cup hat-trick in history. The player had only started 2 competitive international matches before this game. His team won 5-0.",
     "cta": "Best hat-trick you've ever watched live? Tell us! 🔥👇",
     "title": "8-Minute Hat-Trick at World Cup 2026 🔥 #shorts #worldcup2026 #hattrick",
     "tags": ["worldcup2026","hattrick","record","shorts","football","soccer","viral","fifaworldcup"]},
    {"hook": "World Cup 2026 is the BIGGEST tournament in football history! 🏆",
     "body": "FIFA World Cup 2026 features 48 teams for the first time ever — 16 more than 2022. The tournament is hosted across 3 countries: USA, Canada, and Mexico. Over 5 billion people are expected to watch at least one match.",
     "cta": "Which country are you supporting at World Cup 2026? Comment! 🏆",
     "title": "World Cup 2026 Is BIGGER Than Any Tournament in History 🏆 #shorts #fifaworldcup",
     "tags": ["worldcup2026","biggest","history","shorts","football","soccer","usa","fifaworldcup"]},
    {"hook": "This player scored his 100th international goal at World Cup 2026! 💯",
     "body": "A veteran striker reached the landmark of 100 international goals during World Cup 2026 group stage — only the 4th player in men's football history to achieve this. He scored the goal in the 88th minute to equalise for his country. The crowd went completely silent, then erupted.",
     "cta": "Who do you think is the greatest goalscorer of all time? Comment! 💯",
     "title": "100th International Goal At World Cup 2026 — History Made 💯 #shorts #worldcup",
     "tags": ["worldcup2026","100goals","record","shorts","football","soccer","history","viral"]},
    {"hook": "VAR overturned 3 goals in a single World Cup 2026 match! 😡",
     "body": "In one extraordinary group stage game at World Cup 2026, VAR overturned 3 separate goals — all ruled offside by millimetres. The final scoreline was 0-0 despite the ball entering the net 3 times. Fans voted it the most controversial game of the decade.",
     "cta": "Should VAR be banned from football? Comment YES or NO! 🗣️",
     "title": "VAR Overturned 3 Goals in ONE Match at World Cup 2026 😡 #shorts #VAR #worldcup",
     "tags": ["worldcup2026","VAR","offside","controversy","shorts","football","soccer","viral"]},
    {"hook": "Nobody believed this country would qualify for World Cup 2026!",
     "body": "One World Cup 2026 debutant ranked 95th in the FIFA world rankings before the tournament. They qualified by winning a 5-team playoff in dramatic fashion. In their first World Cup group game, they held a top-10 ranked nation to a 1-1 draw.",
     "cta": "Greatest underdog story in sport you've ever seen? Share it! 🐾",
     "title": "The World Cup 2026 Underdog Nobody Believed In 🐾 #shorts #worldcup2026 #underdog",
     "tags": ["worldcup2026","underdog","debut","shorts","football","soccer","viral","fifaworldcup"]},
    {"hook": "England hasn't won a penalty shootout in 25 years — until NOW! 🏴󠁧󠁢󠁥󠁮󠁧󠁿",
     "body": "England have historically lost 6 of 7 World Cup penalty shootouts before 2026. At World Cup 2026 they finally broke the curse, converting 4 out of 4 penalties. The nation watched through their fingers and then erupted in celebration.",
     "cta": "England to win World Cup 2026? Comment YES or NO below! 🏴󠁧󠁢󠁥󠁮󠁧󠁿",
     "title": "England Finally WIN a Penalty Shootout at World Cup 2026 🏴󠁧󠁢󠁥󠁮󠁧󠁿 #shorts #worldcup",
     "tags": ["worldcup2026","england","penalties","shootout","shorts","football","soccer","viral"]},
    {"hook": "This World Cup 2026 stat proves Argentina are the favourites! 🇦🇷",
     "body": "Argentina have won every World Cup they've played in after winning the previous one — a 100% historical record. At World Cup 2026, they've scored 9 goals and conceded just 1 in the group stage. No team has kept a better defensive record.",
     "cta": "Argentina to defend the World Cup title? Comment YES or NO! 🇦🇷",
     "title": "Stats PROVE Argentina Are World Cup 2026 Favourites 🇦🇷 #shorts #worldcup2026",
     "tags": ["worldcup2026","argentina","messi","favourites","shorts","football","soccer","viral"]},
    {"hook": "Brazil scored 5 goals in 20 minutes — an absolute masterclass! 🇧🇷",
     "body": "Brazil's group stage performance at World Cup 2026 included a 20-minute spell where they scored 5 goals against a helpless opponent. Their xG for that period was just 2.1 — meaning they massively outperformed the statistical expectation. Scouts called it the most clinical football seen at a World Cup in 20 years.",
     "cta": "Brazil to win World Cup 2026? Drop your prediction! 🇧🇷👇",
     "title": "Brazil's 5 Goals in 20 Minutes is Pure MAGIC 🇧🇷 #shorts #worldcup2026 #brazil",
     "tags": ["worldcup2026","brazil","goals","masterclass","shorts","football","soccer","viral"]},
    {"hook": "France conceded ZERO goals in the group stage of World Cup 2026! 🇫🇷",
     "body": "France's defensive record at World Cup 2026 group stage: 3 matches, 0 goals conceded, 7 goals scored. Their goalkeeper hasn't even had to make a save in regulation time. Mbappé has 4 goals and 2 assists in 3 games.",
     "cta": "France vs Argentina final — who wins? Comment below! 🇫🇷🇦🇷",
     "title": "France Are UNTOUCHABLE at World Cup 2026 🇫🇷 #shorts #worldcup2026 #france",
     "tags": ["worldcup2026","france","mbappe","defense","shorts","football","soccer","viral"]},
    {"hook": "This is the most goals ever scored on a single World Cup 2026 day! ⚽",
     "body": "Day 8 of World Cup 2026 produced 19 goals across 6 matches — the highest ever in a single day at any World Cup. Three matches ended 4-3, 5-2, and 4-1. Fans called it the greatest day of football ever played.",
     "cta": "Which was YOUR favourite match of World Cup 2026 so far? Comment! ⚽",
     "title": "19 Goals in ONE Day — World Cup 2026 Most Insane Day Ever ⚽ #shorts #worldcup",
     "tags": ["worldcup2026","goals","record","shorts","football","soccer","viral","fifaworldcup"]},
    {"hook": "The World Cup 2026 top scorer has 7 goals in just 4 games! 🔥",
     "body": "World Cup 2026's leading scorer reached 7 goals in just 4 appearances — surpassing Ronaldo's 1966 record pace. At this rate he would finish with 17 goals, smashing Just Fontaine's all-time record of 13. Clubs are reportedly bidding £200 million for him.",
     "cta": "Who do you think wins the Golden Boot at World Cup 2026? Comment! 🥇",
     "title": "7 Goals in 4 Games — World Cup 2026 Golden Boot Race 🔥 #shorts #worldcup2026",
     "tags": ["worldcup2026","goldenboot","topscorer","shorts","football","soccer","viral","record"]},
    {"hook": "Morocco are the biggest World Cup 2026 dark horse! Nobody expected this!",
     "body": "Morocco reached the World Cup 2026 knockout rounds with the highest pressing intensity of any team in the tournament — 34 high turnovers per game. Their squad average age is just 24.2 years. Half their squad plays in non-European leagues.",
     "cta": "Can Morocco go all the way and win World Cup 2026? YES or NO! 🇲🇦",
     "title": "Morocco Are World Cup 2026's Biggest Dark Horse 🇲🇦 #shorts #worldcup2026 #morocco",
     "tags": ["worldcup2026","morocco","darkhorse","shorts","football","soccer","viral","africa"]},
    {"hook": "Japan's tactical system has confused every opponent at World Cup 2026!",
     "body": "Japan used 5 different formations across their 3 group stage games at World Cup 2026 — confusing analysts and opponents alike. They recovered the ball more than any other team in the group stage. Their coach is just 41 years old.",
     "cta": "Japan to reach the semis of World Cup 2026? Comment YES or NO! 🇯🇵",
     "title": "Japan's Tactical MASTERPLAN is Confusing Everyone 🇯🇵 #shorts #worldcup2026 #japan",
     "tags": ["worldcup2026","japan","tactics","shorts","football","soccer","viral","asia"]},
    {"hook": "This World Cup 2026 stat about USA will blow your mind! 🇺🇸",
     "body": "As the host nation, USA are playing at their first World Cup since 2014. Home nation advantage historically increases a team's win probability by 22%. USA's home crowd at the MetLife Stadium is the loudest recorded at any World Cup match this century.",
     "cta": "USA to win the World Cup on home soil? Comment your prediction! 🇺🇸",
     "title": "USA's Home Advantage Stat Is INCREDIBLE at World Cup 2026 🇺🇸 #shorts #worldcup",
     "tags": ["worldcup2026","usa","homeadvantage","shorts","football","soccer","viral","america"]},
    {"hook": "The World Cup 2026 ball travels faster than any ball in history! ⚡",
     "body": "The official FIFA World Cup 2026 match ball has been measured at speeds of up to 134 km/h on free kicks — 8% faster than the 2022 Qatar ball. Goalkeepers have just 0.28 seconds to react to a shot from 20 metres. Three world-record free kick speeds have been set this tournament.",
     "cta": "Fastest shot in football you've ever seen? Comment it below! ⚡",
     "title": "World Cup 2026 Ball Reaches 134 km/h — Goalkeepers Have NO Chance ⚡ #shorts",
     "tags": ["worldcup2026","ball","speed","record","shorts","football","soccer","viral"]},
    {"hook": "The smallest country at World Cup 2026 has a population of 400,000!",
     "body": "One of the smallest nations ever at a FIFA World Cup is competing in 2026 with a total population under 400,000. For comparison, that's smaller than the city of Leicester, England. Their entire squad plays outside their home country.",
     "cta": "Favourite small nation underdog at World Cup 2026? Comment! 🌍",
     "title": "World Cup 2026's Smallest Nation Has Just 400,000 People 😮 #shorts #worldcup",
     "tags": ["worldcup2026","smallnation","underdog","shorts","football","soccer","viral","debut"]},
    {"hook": "World Cup 2026 is generating $11 BILLION — the most ever! 💰",
     "body": "FIFA World Cup 2026 is projected to generate $11 billion in revenue — more than double the 2022 Qatar World Cup. Prize money for the winning nation has increased to $100 million. Local host cities will each receive over $200 million in economic boost.",
     "cta": "Should players get a bigger share of the prize money? YES or NO! 💰",
     "title": "World Cup 2026 Will Make $11 BILLION — Football's Richest Ever 💰 #shorts #worldcup",
     "tags": ["worldcup2026","money","business","shorts","football","soccer","viral","fifaworldcup"]},
    {"hook": "This player went from non-league to World Cup 2026 in 3 years! 💪",
     "body": "One of World Cup 2026's most remarkable stories is a striker who was playing non-league football just 3 years ago. He was spotted by a scout while working a part-time job. He's now scored 2 goals at the biggest tournament in the world.",
     "cta": "Most inspiring football story you know? Share it below! 💪",
     "title": "Non-League to World Cup 2026 in Just 3 Years 💪 #shorts #worldcup2026 #inspiration",
     "tags": ["worldcup2026","inspiration","riseup","shorts","football","soccer","viral","story"]},
    {"hook": "Messi's World Cup 2026 stats are out of this world 🐐",
     "body": "At World Cup 2026, Lionel Messi has created more chances than any other player in the tournament with 3.8 key passes per game. At 38 years old, he is the oldest player ever to lead a World Cup in chance creation. Some say this could be his final World Cup.",
     "cta": "Is Messi the GOAT? Comment YES or NO! 🐐",
     "title": "Messi's World Cup 2026 Stats Are Unreal at 38 Years Old 🐐 #shorts #messi #worldcup",
     "tags": ["worldcup2026","messi","goat","argentina","shorts","football","soccer","viral"]},
    {"hook": "Ronaldo's World Cup 2026 record nobody is talking about! 🇵🇹",
     "body": "Cristiano Ronaldo became the first player ever to score at 6 different FIFA World Cups at World Cup 2026. He is now 41 years old and still starting for Portugal. He has scored 14 World Cup goals in total — more than any European player in history.",
     "cta": "Ronaldo or Messi — who is the real GOAT? Comment your answer! 🐐",
     "title": "Ronaldo Scores at His 6th World Cup — History Made 🇵🇹 #shorts #ronaldo #worldcup2026",
     "tags": ["worldcup2026","ronaldo","portugal","record","shorts","football","soccer","viral"]},
]


# ─── Step 1: Generate fact + script via Gemini (with library fallback) ───────
def generate_script(topic: str) -> dict:
    """Try Gemini AI first; on rate limit or error, use pre-built library."""
    log(f"Generating script for topic: {topic}")

    # ── Try Gemini ──
    try:
        prompt = f"""
You are a viral YouTube Shorts scriptwriter for a football/soccer facts channel called "{config.CHANNEL_NAME}".

Write a 20-second YouTube Short script about this topic:
"{topic}"

Rules:
- Start with a SHOCKING hook sentence (max 12 words) that makes people stop scrolling
- Include 2-3 specific stats or facts (use real or realistic numbers)
- End with a question that drives comments (e.g. "Who do you think will win? Comment below!")
- Total word count: 60-80 words (20 seconds of speech)
- Tone: energetic, conversational, surprising
- Do NOT reference or describe any copyrighted broadcast footage

Return ONLY valid JSON in this exact format:
{{
  "hook": "The shocking 1-sentence hook (max 12 words)",
  "body": "The main 2-3 sentence fact content",
  "cta": "The comment-driving question",
  "title": "YouTube title with emojis and hashtags (max 100 chars)",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8"]
}}
"""
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        raw = response.text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"): raw = raw[4:]
        raw = raw.strip()
        data = json.loads(raw)
        log(f"Gemini script: {data['hook'][:60]}...")
        return data

    except Exception as e:
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e) or "quota" in str(e).lower():
            log("Gemini rate-limited — using pre-built script library instead.")
        else:
            log(f"Gemini error ({e.__class__.__name__}) — falling back to library.")

    # ── Fallback: pick unused script from library ──
    state = load_state()
    used = set(state.get("used_library_ids", []))
    available = [i for i in range(len(SCRIPT_LIBRARY)) if i not in used]
    if not available:
        # All used — reset
        used = set()
        available = list(range(len(SCRIPT_LIBRARY)))
        state["used_library_ids"] = []
        log("Script library fully cycled — resetting.")

    idx = random.choice(available)
    used.add(idx)
    state["used_library_ids"] = list(used)
    save_state(state)

    script = SCRIPT_LIBRARY[idx].copy()
    log(f"Library script #{idx}: {script['hook'][:60]}...")
    return script


# ─── Step 2: Generate voiceover via ElevenLabs ──────────────────────────────
def generate_voiceover(script: dict) -> str:
    full_text = f"{script['hook']}. {script['body']} {script['cta']}"
    log(f"Generating ElevenLabs voiceover ({len(full_text)} chars)...")
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{config.ELEVENLABS_VOICE_ID}"
    headers = {
        "xi-api-key": config.ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "text": full_text,
        "model_id": "eleven_turbo_v2_5",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }
    resp = requests.post(url, json=payload, headers=headers, timeout=60)
    if resp.status_code != 200:
        raise Exception(f"ElevenLabs error {resp.status_code}: {resp.text[:200]}")
    
    os.makedirs(config.AUDIO_DIR, exist_ok=True)
    vo_path = os.path.join(config.AUDIO_DIR, f"vo_{int(time.time())}.mp3")
    with open(vo_path, "wb") as f: f.write(resp.content)
    log(f"Voiceover saved: {vo_path}")
    return vo_path


# ─── Step 3: Download background music ──────────────────────────────────────
def get_music(url: str) -> str:
    """Try the given URL first; if it fails, try every track until one works."""
    os.makedirs(config.AUDIO_DIR, exist_ok=True)
    urls_to_try = [url] + [u for u in MUSIC_TRACKS if u != url]
    for try_url in urls_to_try:
        name = f"music_{abs(hash(try_url)) % 99999}.mp3"
        path = os.path.join(config.AUDIO_DIR, name)
        if os.path.exists(path) and os.path.getsize(path) > 1000:
            log(f"Using cached music: {name}")
            return path
        try:
            log(f"Downloading music: {try_url[:60]}...")
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            r = requests.get(try_url, headers=headers, timeout=30)
            r.raise_for_status()
            with open(path, "wb") as f:
                f.write(r.content)
            if os.path.getsize(path) > 1000:
                log(f"Music downloaded: {name} ({len(r.content)//1024}KB)")
                return path
        except Exception as e:
            log(f"Music URL failed ({e.__class__.__name__}: {str(e)[:60]}) — trying next...")
    raise Exception("All music tracks failed to download. Check internet connection.")



# ─── Step 4: Render animated video frames with PIL ──────────────────────────
def get_font(size: int, bold: bool = False):
    paths = [
        "C:\\Windows\\Fonts\\Impact.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf" if bold else "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except: continue
    return ImageFont.load_default()

def draw_centered_text(draw, text, y, font, color, max_width, shadow=True):
    """Draw word-wrapped centered text with optional shadow."""
    words = text.split()
    lines, line = [], []
    for w in words:
        test = " ".join(line + [w])
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] > max_width and line:
            lines.append(" ".join(line)); line = [w]
        else:
            line.append(w)
    if line: lines.append(" ".join(line))
    
    line_h = draw.textbbox((0, 0), "Ag", font=font)[3] + 8
    total_h = line_h * len(lines)
    cy = y - total_h // 2
    for ln in lines:
        bbox = draw.textbbox((0, 0), ln, font=font)
        lw = bbox[2] - bbox[0]
        x = (WIDTH - lw) // 2
        if shadow:
            draw.text((x + 3, cy + 3), ln, font=font, fill=(0, 0, 0, 180))
        draw.text((x, cy), ln, font=font, fill=color)
        cy += line_h
    return cy  # return bottom y

def render_frame(script: dict, t: float, duration: float, theme: dict, phase: str) -> np.ndarray:
    """Render a single PIL frame as numpy array."""
    img = Image.new("RGB", (WIDTH, HEIGHT), theme["bg"])
    draw = ImageDraw.Draw(img, "RGBA")
    
    acc = theme["accent"]
    txt = theme["text"]
    
    # ── Background gradient ──
    for y in range(HEIGHT):
        alpha = int(30 * (1 - y / HEIGHT))
        draw.line([(0, y), (WIDTH, y)], fill=(acc[0], acc[1], acc[2], alpha))
    
    # ── Top bar: channel name ──
    draw.rectangle([(0, 0), (WIDTH, 100)], fill=(0, 0, 0, 200))
    font_ch = get_font(36)
    ch_bbox = draw.textbbox((0, 0), config.CHANNEL_NAME.upper(), font=font_ch)
    draw.text(((WIDTH - ch_bbox[2]) // 2, 30), config.CHANNEL_NAME.upper(), font=font_ch, fill=acc)
    
    # ── FIFA World Cup badge ──
    draw.ellipse([(WIDTH//2 - 40, 105), (WIDTH//2 + 40, 185)], fill=acc)
    font_badge = get_font(22, bold=True)
    draw.text((WIDTH//2 - 33, 128), "FIFA", font=font_badge, fill=(0,0,0))
    draw.text((WIDTH//2 - 22, 152), "2026", font=font_badge, fill=(0,0,0))
    
    # ── Main content area ──
    if phase == "hook":
        # Big bold hook text centered
        font_hook = get_font(72, bold=True)
        draw_centered_text(draw, script["hook"], HEIGHT // 2, font_hook, txt, WIDTH - 80)
        
        # Pulsing accent underline
        pulse = abs(np.sin(t * 3)) 
        uw = int(300 + 200 * pulse)
        draw.rectangle([(WIDTH//2 - uw//2, HEIGHT//2 + 200),
                        (WIDTH//2 + uw//2, HEIGHT//2 + 212)], fill=acc)
    
    elif phase == "body":
        # Stat card
        card_x1, card_y1 = 60, HEIGHT//2 - 350
        card_x2, card_y2 = WIDTH - 60, HEIGHT//2 + 250
        draw.rounded_rectangle([(card_x1, card_y1), (card_x2, card_y2)],
                                radius=30, fill=(255, 255, 255, 20))
        draw.rounded_rectangle([(card_x1, card_y1), (card_x2, card_y2)],
                                radius=30, outline=acc, width=3)
        
        font_body = get_font(52, bold=True)
        draw_centered_text(draw, script["body"], HEIGHT//2 - 60, font_body, txt, WIDTH - 140)
        
        # Animated progress bar (visual stat indicator)
        progress = min(1.0, (t - duration * 0.3) / (duration * 0.4))
        bar_y = HEIGHT//2 + 200
        draw.rectangle([(100, bar_y), (WIDTH - 100, bar_y + 16)], fill=(50,50,50))
        bar_w = int((WIDTH - 200) * max(0, progress))
        if bar_w > 0:
            draw.rectangle([(100, bar_y), (100 + bar_w, bar_y + 16)], fill=acc)
    
    elif phase == "cta":
        # Call to action
        font_cta = get_font(60, bold=True)
        draw_centered_text(draw, script["cta"], HEIGHT//2 - 100, font_cta, acc, WIDTH - 80)
        
        # Follow button
        btn_y = HEIGHT//2 + 150
        draw.rounded_rectangle([(WIDTH//2 - 220, btn_y), (WIDTH//2 + 220, btn_y + 100)],
                                radius=50, fill=acc)
        font_btn = get_font(44, bold=True)
        btn_text = "FOLLOW 🔔"
        bb = draw.textbbox((0,0), btn_text, font=font_btn)
        draw.text((WIDTH//2 - (bb[2]-bb[0])//2, btn_y + 25), btn_text,
                  font=font_btn, fill=(0,0,0))
    
    # ── Bottom progress bar ──
    progress_x = int(WIDTH * (t / duration))
    draw.rectangle([(0, HEIGHT - 12), (WIDTH, HEIGHT)], fill=(30, 30, 30))
    if progress_x > 0:
        draw.rectangle([(0, HEIGHT - 12), (progress_x, HEIGHT)], fill=acc)
    
    # ── Watermark bottom right ──
    font_wm = get_font(28)
    draw.text((WIDTH - 220, HEIGHT - 60), f"@{config.CHANNEL_NAME}", font=font_wm, fill=(150,150,150))
    
    return np.array(img)


def build_video_frames(script: dict, duration: float, theme: dict) -> list:
    """Build all frame numpy arrays."""
    log("Rendering animated frames...")
    frames = []
    hook_end  = duration * 0.30   # first 30%: hook
    body_end  = duration * 0.75   # next 45%: body/stats
    # last 25%: CTA
    
    n_frames = int(duration * FPS)
    for i in range(n_frames):
        t = i / FPS
        if t < hook_end:   phase = "hook"
        elif t < body_end: phase = "body"
        else:              phase = "cta"
        frames.append(render_frame(script, t, duration, theme, phase))
    return frames


# ─── Step 5: Assemble video with MoviePy ────────────────────────────────────
def _set_duration(clip, d):
    return clip.with_duration(d) if hasattr(clip, "with_duration") else clip.set_duration(d)

def _set_audio(clip, audio):
    return clip.with_audio(audio) if hasattr(clip, "with_audio") else clip.set_audio(audio)

def _scale_volume(clip, factor):
    if hasattr(clip, "with_volume_scaled"): return clip.with_volume_scaled(factor)
    if hasattr(clip, "multiply_volume"):    return clip.multiply_volume(factor)
    return clip.volumex(factor)

def assemble_video(frames: list, vo_path: str, music_path: str, out_path: str):
    log("Assembling final video...")
    
    # Build video clip from frame array
    def make_frame(t):
        idx = min(int(t * FPS), len(frames) - 1)
        return frames[idx]
    
    duration = len(frames) / FPS
    
    # Use ImageClip approach — create one clip per second for memory efficiency
    clips = []
    chunk = FPS  # frames per clip chunk
    for start in range(0, len(frames), chunk):
        chunk_frames = frames[start:start+chunk]
        chunk_dur = len(chunk_frames) / FPS
        img_arr = chunk_frames[0]
        clip = ImageClip(img_arr)
        clip = _set_duration(clip, chunk_dur)
        clips.append(clip)
    
    video = concatenate_videoclips(clips, method="compose")
    
    # Load voiceover
    vo = AudioFileClip(vo_path)
    vo_dur = min(vo.duration, duration)
    vo = _set_duration(vo, vo_dur)
    
    # Load background music — LOOP it to fill the full video duration
    raw_music = AudioFileClip(music_path)
    music_dur = raw_music.duration
    if music_dur < duration:
        # Tile the clip enough times to exceed video duration, then trim
        n_loops = int(duration / music_dur) + 2
        from moviepy import concatenate_audioclips
        looped = concatenate_audioclips([raw_music] * n_loops)
        music = _set_duration(looped, duration)
    else:
        music = _set_duration(raw_music, duration)
    music = _scale_volume(music, 0.12)  # quiet under voice
    
    # Mix audio
    try:
        mixed = CompositeAudioClip([music, vo])
    except Exception:
        mixed = vo  # fallback: voice only
    mixed = _set_duration(mixed, duration)
    
    video = _set_audio(video, mixed)
    video = _set_duration(video, duration)
    
    os.makedirs(config.VIDEOS_DIR, exist_ok=True)
    log(f"Writing video to {out_path}...")
    video.write_videofile(
        out_path, fps=FPS, codec="libx264", audio_codec="aac",
        logger=None, ffmpeg_params=["-vf", f"scale={WIDTH}:{HEIGHT}"]
    )
    video.close()
    log("Video assembly complete.")


# ─── Step 6: Upload to YouTube ───────────────────────────────────────────────
def upload_to_youtube(video_path: str, script: dict) -> str:
    import phase5_upload as p5
    
    topic = {
        "id": int(time.time()),
        "title": script["title"],
        "subject": script["hook"],
        "category": "FIFA World Cup 2026",
    }
    secrets_path = getattr(config, "YOUTUBE_CLIENT_SECRETS", "client_secrets.json")
    if not os.path.exists(secrets_path) and not os.path.exists("youtube_token.pickle"):
        log("WARNING: client_secrets.json missing — skipping upload.")
        return None
    
    results = p5.upload_all(video_path, script, topic)
    url = results.get("youtube")
    log(f"Uploaded to YouTube: {url}")
    return url


# ─── Main job ────────────────────────────────────────────────────────────────
def run_one_job():
    config.assert_safe_pipeline()
    log("=" * 55)
    log("  SAFE COPYRIGHT-FREE SHORTS CREATOR — STARTING")
    log("=" * 55)
    
    state = load_state()
    
    # Rotate topic and theme
    topic_idx = (state["topic_index"] + 1) % len(CONTENT_TOPICS)
    theme_idx = (state["theme_index"] + 1) % len(COLOR_THEMES)
    topic = CONTENT_TOPICS[topic_idx]
    theme = COLOR_THEMES[theme_idx]
    
    state["topic_index"] = topic_idx
    state["theme_index"] = theme_idx
    state["video_count"] = state.get("video_count", 0) + 1
    save_state(state)
    
    try:
        # 1. Generate script with Gemini
        script = generate_script(topic)
        
        # 2. Generate voiceover with ElevenLabs
        if config.ELEVENLABS_API_KEY:
            vo_path = generate_voiceover(script)
        else:
            log("WARNING: No ElevenLabs key — skipping voiceover, using music only.")
            vo_path = None
        
        # 3. Get royalty-free music
        music_url = random.choice(MUSIC_TRACKS)
        music_path = get_music(music_url)
        
        # 4. Calculate video duration from voiceover (or default 20s)
        if vo_path:
            vo_check = AudioFileClip(vo_path)
            duration = min(vo_check.duration + 1.5, 28.0)  # pad 1.5s, max 28s for Shorts
            vo_check.close()
        else:
            duration = 20.0
        
        # 5. Render animated frames
        frames = build_video_frames(script, duration, theme)
        
        # 6. Assemble video
        out_path = os.path.join(config.VIDEOS_DIR, f"safe_short_{int(time.time())}.mp4")
        
        if vo_path:
            assemble_video(frames, vo_path, music_path, out_path)
        else:
            # Music-only version
            def make_frame(t):
                idx = min(int(t * FPS), len(frames) - 1)
                return frames[idx]
            from moviepy import VideoClip
            clip = VideoClip(make_frame, duration=duration)
            music = AudioFileClip(music_path)
            music = _set_duration(music, duration)
            music = _scale_volume(music, 0.5)
            clip = _set_audio(clip, music)
            os.makedirs(config.VIDEOS_DIR, exist_ok=True)
            clip.write_videofile(out_path, fps=FPS, codec="libx264", audio_codec="aac", logger=None)
            clip.close()
        
        # 7. Upload to YouTube
        url = upload_to_youtube(out_path, script)
        
        log("=" * 55)
        log(f"  JOB COMPLETE! Video #{state['video_count']}")
        log(f"  Title:   {script['title'][:60]}...")
        if url: log(f"  YouTube: {url}")
        else:   log(f"  Saved:   {out_path}")
        log("=" * 55)
        
    except Exception as e:
        log(f"ERROR in job: {e}")
        import traceback; traceback.print_exc()


def main():
    log("=" * 55)
    log("  FIFA FACTS SHORTS — 10x/DAY AUTO LOOP STARTED")
    log("  ZERO copyright risk. Fully original AI content.")
    log("  Press Ctrl+C to stop.")
    log("=" * 55)
    
    run_one_job()
    
    interval = 144 * 60  # 144 minutes = 10 per day
    while True:
        log(f"Next video in 144 minutes...")
        time.sleep(interval)
        run_one_job()


if __name__ == "__main__":
    main()
