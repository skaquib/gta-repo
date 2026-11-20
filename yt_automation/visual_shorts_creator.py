"""
visual_shorts_creator.py  — v3 VISUAL-FIRST REWRITE
=====================================================
Viral football Shorts that LOOK like real content:
  • 3 topic-matched Pixabay clips cut together (new clip every ~6s)
  • Minimal caption-style text at the BOTTOM only (not covering the screen)
  • Bold hook title at the top for the first 5 seconds
  • ElevenLabs AI voice narration
  • Royalty-free background music at low volume
  • Auto-upload to YouTube with viral SEO metadata
"""

import os, re, sys, time, json, random, requests, io
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from logger import log
import config

# ── MoviePy ──────────────────────────────────────────────────────────────────
try:
    from moviepy import (VideoFileClip, AudioFileClip, ImageClip,
                         concatenate_videoclips, concatenate_audioclips,
                         CompositeAudioClip, CompositeVideoClip, ColorClip)
    MOVIEPY_V2 = True
except ImportError:
    from moviepy.editor import (VideoFileClip, AudioFileClip, ImageClip,
                                concatenate_videoclips, concatenate_audioclips,
                                CompositeAudioClip, CompositeVideoClip, ColorClip)
    MOVIEPY_V2 = False

# ── Gemini ────────────────────────────────────────────────────────────────────
from google import genai
_GKEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
gemini_client = genai.Client(api_key=_GKEY) if _GKEY else None

# ── Constants ─────────────────────────────────────────────────────────────────
STATE_FILE    = "visual_creator_state.json"
WIDTH, HEIGHT = 720, 1280
FPS           = 30
PIXABAY_KEY   = os.getenv("PIXABAY_API_KEY", "")

# CC0 / Public Domain music — ZERO Content ID risk
# Sources: FreePD.com (CC0), Mixkit (free license), direct MP3 links
MUSIC_TRACKS = [
    # Mixkit — free commercial license, no Content ID Phonk/Electronic tracks
    "https://assets.mixkit.co/music/preview/mixkit-phonk-drift-1100.mp3",
    "https://assets.mixkit.co/music/preview/mixkit-cyberpunk-drift-1052.mp3",
    "https://assets.mixkit.co/music/preview/mixkit-sport-action-1027.mp3",
]

# ── Script library with MATCHED Pixabay search queries ────────────────────────
# Each entry has: hook, body, cta, title, tags, AND 3 clip queries to search
SCRIPT_LIBRARY = [
    {
        "hook": "England DESTROYED Panama — the stats are insane! 🏴󠁧󠁢󠁥󠁮󠁧󠁿",
        "body": "England beat Panama 2-0 with 89% pass accuracy — the highest in the entire World Cup 2026 group stage. Both goals came from moves with under 3 touches. Panama had ZERO shots on target the whole game.",
        "cta": "Which team wins World Cup 2026? Drop your pick below! 🏆",
        "title": "England's 2-0 WIN Was MORE Dominant Than You Think 🏴󠁧󠁢󠁥󠁮󠁧󠁿 #shorts #worldcup2026 #football",
        "tags": ["worldcup2026","england","football","shorts","soccer","viral","fifa","goals"],
        "queries": ["football goal celebration slow motion", "soccer player running kick", "football fans stadium cheering"]
    },
    {
        "hook": "Algeria scored 3 goals in 25 minutes — INSANE comeback! 🤯",
        "body": "Algeria vs Austria ended 3-3 in one of World Cup 2026's most dramatic matches. Austria led 2-0 at half time. Algeria scored 3 goals in just 25 second-half minutes, equalising in the 94th minute.",
        "cta": "Best comeback in football history? Comment below! 👇",
        "title": "Algeria's INSANE 3-Goal Comeback vs Austria 😤 #shorts #worldcup2026 #football",
        "tags": ["worldcup2026","algeria","comeback","shorts","football","soccer","viral","goals"],
        "queries": ["soccer goal celebration", "football comeback goal", "football fans cheering stadium"]
    },
    {
        "hook": "The fastest World Cup 2026 goal — just 23 SECONDS! ⚡",
        "body": "A stunning 23-second goal was scored in the group stage, making it the 4th fastest in World Cup history. The scorer had returned from injury just 6 days before the tournament. His team won 3-0.",
        "cta": "Can you name a faster World Cup goal? Comment! ⚡",
        "title": "23-Second World Cup 2026 Goal — History Made ⚡ #shorts #worldcup2026 #goals",
        "tags": ["worldcup2026","fastestgoal","record","shorts","football","soccer","viral","history"],
        "queries": ["soccer fast goal kick", "football sprint speed", "soccer ball net goal"]
    },
    {
        "hook": "VAR cancelled 3 goals in ONE World Cup 2026 match! 😡",
        "body": "In the most controversial match of World Cup 2026, VAR overturned 3 separate goals — all offside by millimetres. The final score was 0-0 despite the ball entering the net 3 times.",
        "cta": "Should VAR be BANNED from football? YES or NO! 🗣️",
        "title": "VAR Overturned 3 Goals in ONE Match 😡 #shorts #worldcup2026 #VAR #football",
        "tags": ["worldcup2026","VAR","controversy","shorts","football","soccer","viral","offside"],
        "queries": ["soccer referee decision", "football VAR review", "football offside controversy"]
    },
    {
        "hook": "This World Cup 2026 hat-trick took just 8 MINUTES! 🔥",
        "body": "The fastest hat-trick at World Cup 2026 was completed in just 8 minutes — the 2nd fastest in World Cup history. The player had only started 2 competitive international matches before this game. His team won 5-0.",
        "cta": "Best hat-trick you've ever seen? Tell us! 🔥👇",
        "title": "8-Minute World Cup Hat-Trick — History Made 🔥 #shorts #worldcup2026 #hattrick",
        "tags": ["worldcup2026","hattrick","record","shorts","football","soccer","viral","goals"],
        "queries": ["soccer hat trick celebration", "football goal scoring", "soccer player celebrating goal"]
    },
    {
        "hook": "Argentina's World Cup 2026 stats PROVE they'll win! 🇦🇷",
        "body": "Argentina have won every World Cup played after winning the previous one — a 100% historical record. At World Cup 2026 they've scored 9 goals and conceded just 1 in the group stage. No defending champion has done better.",
        "cta": "Argentina to defend the World Cup title? YES or NO! 🇦🇷",
        "title": "Stats PROVE Argentina Win World Cup 2026 🇦🇷 #shorts #worldcup2026 #argentina",
        "tags": ["worldcup2026","argentina","messi","stats","shorts","football","soccer","viral"],
        "queries": ["argentina football celebration", "soccer world cup trophy", "football team victory"]
    },
    {
        "hook": "France scored 7 goals and conceded ZERO! Unstoppable! 🇫🇷",
        "body": "France's World Cup 2026 group stage: 3 matches, 7 goals scored, 0 goals conceded. Their goalkeeper didn't need to make a save in regulation time across all 3 games. Mbappé has 4 goals and 2 assists.",
        "cta": "France vs Argentina final — who wins? 🇫🇷🇦🇷 Comment!",
        "title": "France Are UNTOUCHABLE at World Cup 2026 🇫🇷 #shorts #worldcup2026 #mbappe",
        "tags": ["worldcup2026","france","mbappe","defense","shorts","football","soccer","viral"],
        "queries": ["france football team goal", "soccer goalkeeper save", "football striker running"]
    },
    {
        "hook": "The youngest player at World Cup 2026 is just 17! 😮",
        "body": "World Cup 2026 features 6 players aged 17 or younger — the most since 2010. The youngest starter scored on his very first World Cup appearance. Pelé was 17 when Brazil won the World Cup in 1958.",
        "cta": "Your favourite young player at this World Cup? Comment! 🌟",
        "title": "17-Year-Old Making World Cup 2026 HISTORY 🌟 #shorts #worldcup2026 #youngplayer",
        "tags": ["worldcup2026","youngplayer","history","shorts","football","soccer","viral","debut"],
        "queries": ["young soccer player dribbling", "football teenager talent", "soccer youth player running"]
    },
    {
        "hook": "Ronaldo scored at his 6th World Cup — NOBODY has done this! 🇵🇹",
        "body": "Cristiano Ronaldo became the first player ever to score at 6 different FIFA World Cups at World Cup 2026. At 41 years old, he is still starting for Portugal. He now has 14 World Cup goals — the most by any European player in history.",
        "cta": "Ronaldo or Messi — who is the real GOAT? Comment! 🐐",
        "title": "Ronaldo Scores at His 6th World Cup — Nobody Has EVER Done This 🇵🇹 #shorts #worldcup2026",
        "tags": ["worldcup2026","ronaldo","record","portugal","shorts","football","soccer","viral"],
        "queries": ["soccer star goal celebration", "football legend kick", "soccer player scoring goal"]
    },
    {
        "hook": "Brazil scored 5 goals in 20 minutes — pure MAGIC! 🇧🇷",
        "body": "Brazil's group stage at World Cup 2026 included a 20-minute spell where they scored 5 goals. Their xG for that period was just 2.1 — massively outperforming expectations. Scouts called it the most clinical football seen at a World Cup in 20 years.",
        "cta": "Brazil to win World Cup 2026? Drop your prediction! 🇧🇷👇",
        "title": "Brazil's 5 Goals in 20 Minutes is Pure MAGIC 🇧🇷 #shorts #worldcup2026 #brazil",
        "tags": ["worldcup2026","brazil","goals","masterclass","shorts","football","soccer","viral"],
        "queries": ["brazil football goal", "soccer team celebration multiple goals", "football stadium crowd roar"]
    },
    {
        "hook": "Morocco: the DARK HORSE nobody is talking about! 🇲🇦",
        "body": "Morocco reached the World Cup 2026 knockout rounds with the highest pressing intensity of any team — 34 high turnovers per game. Their squad average age is just 24.2 years. Half their players compete outside European leagues.",
        "cta": "Can Morocco win World Cup 2026? YES or NO! 🇲🇦",
        "title": "Morocco Are World Cup 2026's Biggest Dark Horse 🇲🇦 #shorts #worldcup2026 #morocco",
        "tags": ["worldcup2026","morocco","darkhorse","shorts","football","soccer","viral","africa"],
        "queries": ["morocco football team", "soccer player pressing tackle", "football underdog winning"]
    },
    {
        "hook": "Japan confused EVERY opponent with 5 different formations! 🇯🇵",
        "body": "Japan used 5 different formations across their 3 group stage games at World Cup 2026 — confusing analysts and opponents alike. They won the ball back more times than any other team in the group stage. Their head coach is just 41 years old.",
        "cta": "Japan to reach the World Cup 2026 semis? YES or NO! 🇯🇵",
        "title": "Japan's Tactical GENIUS Is Confusing Everyone 🇯🇵 #shorts #worldcup2026 #japan",
        "tags": ["worldcup2026","japan","tactics","shorts","football","soccer","viral","asia"],
        "queries": ["japan football team tactics", "soccer tactical formation", "football midfield pressing"]
    },
    {
        "hook": "A World Cup 2026 keeper made 9 SAVES in ONE match! 🧤🔥",
        "body": "The goalkeeper stopped 9 shots in a single World Cup 2026 knockout game — the most by any keeper since 2014. Six of the saves came in the final 20 minutes alone. His team won on penalties after a clean sheet through 120 minutes.",
        "cta": "Greatest goalkeeping performance you've ever seen? Comment! 🧤👇",
        "title": "Goalkeeper's 9-SAVE Masterclass Stuns World Cup 2026 🧤🔥 #shorts #worldcup2026 #goalkeeper",
        "tags": ["worldcup2026","goalkeeper","saves","record","shorts","football","soccer","viral"],
        "queries": ["soccer goalkeeper diving save", "football penalty shootout save", "goalkeeper celebration clean sheet"]
    },
]

COLOR_THEMES = [
    {"accent": (0, 220, 110),  "text": (255, 255, 255), "shadow": (0, 180, 80)},
    {"accent": (255, 60, 60),  "text": (255, 255, 255), "shadow": (200, 0, 0)},
    {"accent": (30, 150, 255), "text": (255, 255, 255), "shadow": (0, 100, 220)},
    {"accent": (255, 215, 0),  "text": (255, 255, 255), "shadow": (200, 160, 0)},
    {"accent": (200, 60, 255), "text": (255, 255, 255), "shadow": (150, 0, 220)},
]


# ── State ─────────────────────────────────────────────────────────────────────
def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f: return json.load(f)
        except: pass
    return {"script_idx": -1, "theme_idx": -1, "used": [], "video_count": 0}

def save_state(s):
    with open(STATE_FILE, "w") as f: json.dump(s, f, indent=2)


# ── MoviePy compatibility helpers ─────────────────────────────────────────────
def _dur(clip, d):
    return clip.with_duration(d) if MOVIEPY_V2 else clip.set_duration(d)

def _audio(clip, a):
    return clip.with_audio(a) if MOVIEPY_V2 else clip.set_audio(a)

def _vol(clip, f):
    if hasattr(clip, "with_volume_scaled"): return clip.with_volume_scaled(f)
    if hasattr(clip, "multiply_volume"):    return clip.multiply_volume(f)
    return clip.volumex(f)

def _crop(clip, x1, y1, x2, y2):
    if hasattr(clip, "cropped"): return clip.cropped(x1=x1, y1=y1, x2=x2, y2=y2)
    return clip.crop(x1=x1, y1=y1, x2=x2, y2=y2)

def _resize(clip, size):
    if hasattr(clip, "resized"): return clip.resized(size)
    return clip.resize(size)

def _fl(clip, fn):
    if hasattr(clip, "fl"): return clip.fl(fn)
    return clip.transform(fn)

def _fl_audio(clip, fn):
    if hasattr(clip, "fl"): return clip.fl(fn)
    return clip.transform(fn)

def _speed(clip, factor):
    if hasattr(clip, "multiply_speed"):
        return clip.multiply_speed(factor)
    try:
        import moviepy.video.fx.all as vfx
        return clip.fx(vfx.speedx, factor)
    except Exception:
        return clip


# List of highly viral, recognizable football managers and players for dynamic rotation
SUBJECTS = [
    "José Mourinho touchline composure",
    "Carlo Ancelotti calm eyebrow raise",
    "Pep Guardiola touchline ball catch",
    "Zlatan Ibrahimovic martial arts finish",
    "Zinedine Zidane elegant composure",
    "Gianluigi Buffon legendary double save",
    "Thibaut Courtois Champions League final save",
    "Manuel Neuer sweeper keeper composure",
    "Ronaldinho no-look pass composure",
    "Neymar Jr standstill dribble",
    "Lionel Messi walking and scoring solo goal",
    "Cristiano Ronaldo clutch late penalty silence",
    "Lamine Yamal calm dribbling composure",
    "Luis Suarez clutch clinical goal",
    "Sergio Ramos last-minute header",
    "Mario Balotelli Why Always Me celebration",
    "Erling Haaland meditation celebration",
    "Kylian Mbappé smiling sprint finish",
    "Didier Drogba clutch match winning goal",
    "Andrea Pirlo cold Panenka penalty",
    "Johan Cruyff Cruyff turn composure",
    "Diego Maradona hand of god or solo run",
    "Pelé overhead kick composure",
    "David Beckham cold last-minute freekick",
    "Arda Güler long range goal composure"
]


# ── Step 1: Pick script ───────────────────────────────────────────────────────
def generate_dynamic_script_with_gemini() -> dict:
    # Returns a script JSON that must include a `queries` list of three search terms for Pexels
    bedrock_key = getattr(config, "BEDROCK_API_KEY", "") or os.getenv("BEDROCK_API_KEY", "")
    niche = getattr(config, "CHANNEL_NICHE", "family-friendly facts")
    channel = getattr(config, "CHANNEL_NAME", "FramedFacts")
    
    subject = random.choice(SUBJECTS)
    log(f"Dynamic Subject selected for viral script: '{subject}'")
    
    prompt = f"""
    You are a viral YouTube Shorts content creator and marketing strategist with 15 years of industry experience.
    Your channel name is: {channel}.
    Your channel niche is: {niche}.
    
    You MUST generate a script focusing specifically on: {subject}.
    
    Generate a mind-blowing, inspiring, and highly viral script about this niche in an exciting, dramatic, and "cold" composure (aura) context.
    
    CRITICAL INSTRUCTIONS FOR VIRAL ENGAGEMENT:
    1. Hook Constraints:
       - You MUST start the "hook" directly with a number, a record, or a core tension in the first 3 words.
       - STRICTLY BAN all introductory filler phrases: "Ever wondered", "Imagine this", "Brace yourselves", "Did you know", "Welcome back", "This is the story of".
       - Example of a good hook: "Three managers. That's how many stood in shock as Guardiola caught the ball in mid-air..."
    2. Pacing & Tone:
       - Keep sentences extremely short, punchy, and conversational (average 6-10 words per sentence max).
       - Maintain a dramatic, high-energy, and cold tone celebrating the extreme composure ("aura") and skills.
    3. B-roll sourcing:
       - Provide 3 "queries" describing generic, royalty-free stock footage themes (e.g. 'soccer player running kick', 'football stadium crowd cheering', 'goalkeeper diving save') to search royalty-free stock libraries (Pexels/Pixabay). Do not reference any specific real match, player likeness moment, or broadcast — these are generic B-roll search terms only.

    The response MUST be a JSON object with the following structure:
    {{
      "visual_hook": "A short, ultra-clickable 3-5 word title header in ALL CAPS with an exciting emoji (e.g. 'GUARDIOLA AURA! 🥶🥶', 'INSANE DOUBLE SAVE! 🛡️⚽', 'COMPOSURE level 999! 💀🔥'). This header will remain visible at the top of the screen during the entire video.",
      "hook": "The high-retention opening sentence matching the constraints above (must take ~4-5 seconds to read)",
      "body": "The detailed explanation of the amazing feat, packed with specific statistics and high-energy pacing (must take ~15-18 seconds to read)",
      "cta": "An interactive question to make the viewer comment, plus a prompt to subscribe and hit the bell (e.g., 'Is Guardiola the manager with the most aura? Comment below and subscribe for more soccer secrets!')",
      "title": "A highly clickable, viral title with hashtags. You MUST include '#shorts', '#football', '#aura' and '#trending'",
      "tags": ["football", "soccer", "viral", "shorts", "aura", "skills", "edit"],
      "queries": ["football goal celebration slow motion", "soccer stadium crowd cheering", "football skills training"],
      "image_prompts": [
        "A highly detailed, vibrant, beautiful digital art illustration of [Hook scene description], 8k resolution, vertical 9:16 aspect ratio",
        "A highly detailed, vibrant, beautiful digital art illustration of [Body scene description], 8k resolution, vertical 9:16 aspect ratio",
        "A highly detailed, vibrant, beautiful digital art illustration of [CTA scene description], 8k resolution, vertical 9:16 aspect ratio"
      ]
    }}
    
    Do NOT include markdown formatting like ```json or similar in your output, just return the raw JSON object string.
    """

    script_raw = None

    # 1. Try Claude 4.5 Sonnet on Amazon Bedrock first if key is configured
    if bedrock_key:
        log("Attempting to generate dynamic script via Amazon Bedrock (Claude Sonnet 4.5)...")
        url = "https://bedrock-runtime.us-east-1.amazonaws.com/model/us.anthropic.claude-sonnet-4-5-20250929-v1:0/invoke"
        headers = {
            "Authorization": f"Bearer {bedrock_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2000,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        }
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=60)
            if r.status_code == 200:
                res_body = r.json()
                script_raw = res_body["content"][0]["text"]
                log("Successfully fetched script from Bedrock Claude 3.5.")
            else:
                log(f"Bedrock Claude script failed: {r.status_code} — {r.text[:200]}. Trying Llama 3.1...")
        except Exception as e:
            log(f"Bedrock Claude exception: {e}. Trying Llama 3.1...")

    # 1b. Try Meta Llama 3.1 70B on Bedrock as a fallback
    if not script_raw and bedrock_key:
        log("Attempting to generate dynamic script via Amazon Bedrock (Meta Llama 3.1 70B)...")
        url = "https://bedrock-runtime.us-east-1.amazonaws.com/model/us.meta.llama3-1-70b-instruct-v1:0/invoke"
        headers = {
            "Authorization": f"Bearer {bedrock_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        payload = {
            "prompt": f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n",
            "max_gen_len": 1500,
            "temperature": 0.7,
            "top_p": 0.9
        }
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=60)
            if r.status_code == 200:
                res_body = r.json()
                script_raw = res_body["generation"]
                log("Successfully fetched script from Bedrock Llama 3.1.")
            else:
                log(f"Bedrock Llama 3.1 failed: {r.status_code} — {r.text[:200]}. Trying Gemini...")
        except Exception as e:
            log(f"Bedrock Llama 3.1 exception: {e}. Trying Gemini...")

    # 2. Try Gemini fallback
    if not script_raw and gemini_client:
        log("Attempting to generate dynamic script via Gemini...")
        try:
            response = gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config={
                    'response_mime_type': 'application/json'
                }
            )
            script_raw = response.text
            log("Successfully fetched script from Gemini.")
        except Exception as e:
            log(f"Gemini script generation failed: {e}.")

    # Parse and validate JSON script
    if script_raw:
        try:
            cleaned = script_raw.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            
            import json
            script = json.loads(cleaned)
            
            # Programmatic safeguards for #worldcup2026 hashtag visibility
            title = script.get("title", "World Cup Goal!")
            if "#worldcup2026" not in title.lower():
                title += " #worldcup2026"
            if "#shorts" not in title.lower():
                title += " #shorts"
            if len(title) > 100:
                title = title[:96].rstrip() + " #shorts"
            script["title"] = title
            
            tags = [t.lower().replace("#", "") for t in script.get("tags", [])]
            if "worldcup2026" not in tags:
                tags.append("worldcup2026")
            script["tags"] = tags
            
            log(f"Parsed dynamic viral script: '{script['hook'][:50]}...'")
            return script
        except Exception as parse_err:
            log(f"Failed to parse AI response JSON: {parse_err}. Response content: {script_raw[:200]}")

    log("AI script generation unavailable — using fallback static script library.")
    return None

def get_image_prompts(script: dict) -> list:
    if "image_prompts" in script and len(script["image_prompts"]) == 3:
        return script["image_prompts"]
    
    # Fallback: construct prompts dynamically
    hook = script.get("hook", "football soccer")
    body = script.get("body", "football soccer player")
    cta = script.get("cta", "football soccer fans celebrating")
    
    def clean(text):
        words = [w for w in text.split() if w.lower() not in ["the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with", "is", "was", "were"]]
        return " ".join(words[:12])
        
    return [
        f"A dramatic cartoon style illustration of {clean(hook)}, vibrant colors, 8k resolution, vertical 9:16 aspect ratio",
        f"A dramatic cartoon style illustration of {clean(body)}, vibrant colors, 8k resolution, vertical 9:16 aspect ratio",
        f"A dramatic cartoon style illustration of {clean(cta)}, vibrant colors, 8k resolution, vertical 9:16 aspect ratio"
    ]

def fetch_ai_image(prompt: str, index: int) -> str:
    bedrock_key = getattr(config, "BEDROCK_API_KEY", "") or os.getenv("BEDROCK_API_KEY", "")
    
    # 1. Try Amazon Bedrock if API key is configured
    if bedrock_key:
        log(f"Fetching visual {index} from Amazon Bedrock (SDXL)...")
        import base64
        url = "https://bedrock-runtime.us-east-1.amazonaws.com/model/stability.stable-diffusion-xl-v1/invoke"
        headers = {
            "Authorization": f"Bearer {bedrock_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        # SDXL 1.0 vertical 9:16 configuration
        payload = {
            "text_prompts": [{"text": prompt}],
            "cfg_scale": 9,
            "seed": random.randint(0, 999999),
            "steps": 30,
            "width": 768,
            "height": 1024
        }
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=60)
            if r.status_code == 200:
                res_body = r.json()
                img_base64 = res_body["artifacts"][0]["base64"]
                out_dir = os.path.join(config.OUTPUT_DIR, "ai_images")
                os.makedirs(out_dir, exist_ok=True)
                out_path = os.path.join(out_dir, f"bedrock_{index}_{int(time.time())}.jpg")
                with open(out_path, "wb") as f:
                    f.write(base64.decodebytes(bytes(img_base64, "utf-8")))
                log(f"  Amazon Bedrock Image {index} saved: {os.path.basename(out_path)}")
                return out_path
            else:
                log(f"  Bedrock Image generation failed: {r.status_code} — {r.text[:200]}. Falling back to Pollinations AI.")
        except Exception as e:
            log(f"  Bedrock Image exception: {e}. Falling back to Pollinations AI.")

    # 2. Fallback to free Pollinations AI
    import urllib.parse
    os.makedirs(os.path.join(config.OUTPUT_DIR, "ai_images"), exist_ok=True)
    out_path = os.path.join(config.OUTPUT_DIR, "ai_images", f"image_{index}_{int(time.time())}.jpg")
    
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=720&height=1280&nologo=true"
    
    log(f"Fetching AI image {index} from Pollinations AI...")
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=45)
        r.raise_for_status()
        with open(out_path, "wb") as f:
            f.write(r.content)
        log(f"  AI Image {index} saved: {os.path.basename(out_path)}")
        return out_path
    except Exception as e:
        log(f"  AI Image fetch failed for index {index}: {e}. Retrying with simplified prompt...")
        try:
            simplified = prompt
            if "illustration of " in prompt:
                simplified = prompt.split("illustration of ")[1]
            if "," in simplified:
                simplified = simplified.split(",")[0]
            simplified = f"cute {simplified.strip()}, digital art, vibrant colors, vertical 9:16"
            log(f"  Simplified prompt: {simplified}")
            encoded_simple = urllib.parse.quote(simplified)
            url_simple = f"https://image.pollinations.ai/prompt/{encoded_simple}?width=720&height=1280&nologo=true"
            r = requests.get(url_simple, headers={"User-Agent": "Mozilla/5.0"}, timeout=45)
            r.raise_for_status()
            with open(out_path, "wb") as f:
                f.write(r.content)
            log(f"  AI Image {index} saved (simplified): {os.path.basename(out_path)}")
            return out_path
        except Exception as retry_err:
            log(f"  AI Image retry failed: {retry_err}")
            return None

def apply_camera_movement(clip, duration: float, index: int = 0):
    def effect(get_frame, t):
        frame = get_frame(t)
        h, w, c = frame.shape
        
        # Rhythmic beat-sync zoom pulse (130 BPM tempo -> 0.461s beat period)
        beat_dur = 60.0 / 130.0
        pulse = 0.08 * np.exp(-12.0 * (t % beat_dur))
        zoom = 1.05 + pulse
        
        zw = int(w * zoom)
        zh = int(h * zoom)
        img = Image.fromarray(frame)
        img = img.resize((zw, zh), Image.Resampling.LANCZOS)
        
        pct = t / duration
        if index % 3 == 0:
            # Zoom-in: Crop from center
            x = (zw - w) // 2
            y = (zh - h) // 2
        elif index % 3 == 1:
            # Pan Left-to-Right
            max_x = zw - w
            x = int(max_x * pct)
            y = (zh - h) // 2
        else:
            # Pan Right-to-Left
            max_x = zw - w
            x = int(max_x * (1.0 - pct))
            y = (zh - h) // 2
            
        # Boundaries safeguards
        x = max(0, min(x, zw - w))
        y = max(0, min(y, zh - h))
        img = img.crop((x, y, x + w, y + h))
        return np.array(img)
    return _fl(clip, effect)

def pick_script(state: dict):
    # Try dynamic generation first
    dynamic_script = generate_dynamic_script_with_gemini()
    if dynamic_script:
        return dynamic_script

    # Fallback to static library if Gemini fails or is not configured
    used = set(state.get("used", []))
    available = [i for i in range(len(SCRIPT_LIBRARY)) if i not in used]
    if not available:
        used, available = set(), list(range(len(SCRIPT_LIBRARY)))
        log("All scripts cycled — resetting.")
    idx = (state.get("script_idx", -1) + 1) % len(SCRIPT_LIBRARY)
    if idx in used:
        idx = available[0]
    used.add(idx)
    state["used"] = list(used)
    state["script_idx"] = idx
    return SCRIPT_LIBRARY[idx].copy()


# ── Step 2: Download ONE Pixabay clip for a query ─────────────────────────────
# Generic photography/videography descriptors that show up as tags on totally
# unrelated footage (a bacon close-up and a flower macro shot are both
# tagged "closeup" / "slow motion" just as readily as anything sports-related).
# A bare substring match on these alone previously let a bacon-frying clip
# pass as "golf ball close up" because "close" is a substring of its
# "closeup" tag -- neither "golf" nor "ball" was ever actually required.
# Pure camera-technique/framing words -- never describe subject matter,
# so they're excluded from _filter_by_tag_relevance's keyword COUNT too
# (a "close up" or "slow motion" tag matches unrelated footage just as
# easily as on-topic footage, so it should never count as a real subject
# match, unlike the words in _WEAK_BROADENING_WORDS below).
_CAMERA_TECHNIQUE_TERMS = {
    "close", "up", "closeup", "slow", "motion", "action", "view", "shot",
    "shots", "footage", "background", "flying", "still", "clip",
}

# Real subject-adjacent words that are still too weak to search on ALONE
# (as a single-word broadened fallback query) -- but, unlike
# _CAMERA_TECHNIQUE_TERMS, these must still COUNT toward
# _filter_by_tag_relevance's keyword total when they appear as part of a
# real multi-word query. Structural bug found and fixed 2026-08-25: an
# earlier version put these in the same set as the camera-technique
# words above, which are EXCLUDED from the keyword count -- that
# accidentally dropped "Football win" from requiring 2 tag matches to
# requiring just 1 ("football" alone), since "win" no longer counted as
# a keyword at all. That let a motorbike-riders clip through on a single
# loose "football" tag. These words still can't be used as a fallback
# broadened word on their own (see fetch_clip), but they must stay
# counted when judging a real multi-word query.
_WEAK_BROADENING_WORDS = {
    # Non-visual modifiers common in named-entity scripts ("new manager",
    # "first time", "major trophy") -- reproduced live 2026-08-20: "new
    # manager" failed tag confirmation, broadened to just "new" (the first
    # remaining word), and matched an unrelated New Year fireworks clip.
    "new", "first", "major", "every", "former", "current", "official",
    "record", "recent", "biggest", "team", "club", "promotion",
    "victory", "winning", "win",
    # Body-part/medical words from injury-story scripts (a common story
    # type on this channel) -- reproduced live 2026-08-25: "Knee injury"
    # broadened to bare "knee" and matched an unrelated landscape clip,
    # zero sport-visual anchor on its own.
    "knee", "injury", "injured", "wrist", "ankle", "shoulder", "muscle",
    "hamstring",
    # "goal" alone is just as overloaded as "win"/"victory" -- matches
    # life-goals/motivational content, not just sports goals. Reproduced
    # live 2026-08-25: "Goal celebration" broadened to bare "goal" and
    # matched an unrelated waterfall/nature clip.
    "goal",
    # "celebration" alone is too overloaded to ever be a safe single-word
    # fallback -- already has a _NEGATIVE_TAGS entry for the
    # fireworks/wedding/birthday collision, but reproduced AGAIN live
    # 2026-08-25 matching unrelated drink-pouring/toast footage. Rather
    # than keep adding one-off negative tags per new false-positive
    # category, block it from single-word use entirely.
    "celebration",
}

# "football" bare-word queries have twice matched foosball/table-football
# clips that are legitimately tagged "football" by the stock contributor
# (tags like "football, table, game, indoor") -- reproduced live
# 2026-08-20 on "Football fans" -> broadened to "football" alone. With
# only 1 keyword in a single-word query, _filter_by_tag_relevance's
# required-match count drops to 1, so one shared tag is enough to pass
# even though the actual subject is a tabletop game. These negative tags
# close that specific, now-twice-confirmed collision without weakening
# matching for every other query.
    # NOTE: _tag_words() tokenizes on a regex that splits on any
    # non-alphanumeric character, so a Pixabay tag like "table tennis" or
    # "ping pong" becomes TWO separate tokens {"table","tennis"} /
    # {"ping","pong"}, never the single compound word "tabletennis" /
    # "pingpong". An earlier version of this dict used those compound
    # forms and silently never matched anything -- confirmed live
    # 2026-08-25 when the exact table-tennis clip this was meant to block
    # got through a second time. Entries below use the actual tokenized
    # words, not compounds.
_NEGATIVE_TAGS = {
    "football": {"foosball", "table"},
    "soccer": {"foosball", "table"},
    # "celebration" alone is tagged across weddings, New Year's, birthdays,
    # corporate events -- reproduced live 2026-08-21: "Team celebration"
    # (2/2 keywords matched, clearing the required-match bar) pulled a
    # fireworks clip apparently tagged broadly enough to include "team".
    "celebration": {"fireworks", "firework", "pyrotechnics", "newyear",
                     "newyearseve", "wedding", "birthday"},
    # "tennis" alone has twice matched table tennis/ping pong -- reproduced
    # live 2026-08-22 and again 2026-08-25 on a bare "tennis" query.
    "tennis": {"table", "ping", "pong", "tabletop"},
    # "cricket" alone matched the insect, not the sport -- reproduced live
    # 2026-08-29: "cricket match"/"cricket player"/"cricket stadium" all
    # passed tag confirmation but the actual downloaded clip was a
    # grasshopper/locust on a branch (Pixabay tags it "cricket" as the
    # insect name too), and a second clip was a miniature model tank on a
    # hobby table (tagged "cricket" for reasons that don't track).
    "cricket": {"insect", "insects", "grasshopper", "locust", "bug", "bugs",
                "macro", "model", "models", "miniature", "diorama", "toy",
                "hobby", "tank"},
    # bare "swimming"/"swimming pool" queries matched ocean surfing/SUP and
    # underwater reef/stingray footage -- reproduced live 2026-08-29 on the
    # Olympic-pool video. Neither shows a competitive pool.
    "swimming": {"surf", "surfing", "surfer", "paddleboard", "paddleboarding",
                 "reef", "stingray", "scuba", "snorkel", "snorkeling",
                 "underwater", "ocean", "sea", "beach"},
}

# When a query fails tag confirmation entirely, fetch_clip() retries with a
# single broadened word rather than accepting an irrelevant clip. Picking
# that word by position (query.split()[0]) breaks when the sport isn't
# first -- "Future tennis star" retried with "future" and got a completely
# unrelated "parent and child at sunset" clip. Preferring a recognized
# sport/subject word over positional guessing fixes that.
_KNOWN_SPORT_TERMS = {
    "tennis", "golf", "football", "soccer", "basketball", "baseball",
    "cricket", "boxing", "wrestling", "athletics", "running", "swimming",
    "cycling", "hockey", "rugby", "volleyball", "gymnastics", "skiing",
    "snowboarding", "wnba", "nba", "nfl", "mlb", "olympics", "marathon",
    "track", "field", "skating", "surfing", "badminton", "table",
}


def _tag_words(hit):
    return re.findall(r"[a-z0-9]+", hit.get("tags", "").lower())


def _filter_by_tag_relevance(hits: list, query: str) -> list:
    """Pixabay's relevance ranking is loose enough that unrelated clips
    (concerts, city streets, unrelated b-roll) regularly outrank genuinely
    on-topic ones. Require a hit's own tags to contain one of the query's
    SUBJECT words (generic descriptors like "close up"/"slow motion" don't
    count -- they match unrelated footage just as easily) via whole-word
    matching, not substring, so "close" can't match inside "closeup".
    A single matching word still isn't enough on its own when 2+ subject
    words are available: a "record player" clip's tags split into the
    words "record" and "player", so a query like "female tennis player"
    matched on "player" alone even though nothing about it was tennis --
    requiring at least 2 distinct word-hits (when that many are available)
    means an unrelated clip needs to coincidentally share most of the
    subject, not just one common word, to pass. Returns only genuinely
    confirmed matches -- may be empty; callers must NOT silently fall back
    to the unfiltered set, since that's exactly how a bacon-frying clip and
    a flower macro shot both got mislabeled as golf footage before."""
    STOPWORDS = {"a", "an", "the", "in", "on", "at", "of", "and", "or", "with"}
    all_keywords = [w for w in query.lower().split() if w not in STOPWORDS and len(w) > 2]
    keywords = [w for w in all_keywords if w not in _CAMERA_TECHNIQUE_TERMS] or all_keywords
    if not keywords:
        return hits
    required = min(2, len(keywords))

    def _hits_count(h):
        words = set(_tag_words(h))
        return sum(1 for kw in keywords if kw in words)

    def _negatively_tagged(h):
        words = set(_tag_words(h))
        return any(words & _NEGATIVE_TAGS[kw] for kw in keywords if kw in _NEGATIVE_TAGS)

    return [h for h in hits if _hits_count(h) >= required and not _negatively_tagged(h)]


# Clips confirmed to have source metadata that doesn't match their actual
# visual content -- no amount of smarter word-matching fixes this, since
# the tags themselves are wrong, not the matching logic. Block permanently
# once proven bad rather than rediscovering the same mismatch every build.
_KNOWN_MISTAGGED_CLIP_IDS = {
    160356,  # tags say "goal, football, soccer, snow..." (a snowy-pitch
             # obstruction clip) but actual content is motorcycle riders --
             # reproduced live 2026-08-25.
}


def _search_pixabay(query: str, exclude_ids: set) -> list:
    params = {
        "key": PIXABAY_KEY, "q": query, "video_type": "film",
        "per_page": 15, "safesearch": "true", "order": "popular",
    }
    resp = requests.get("https://pixabay.com/api/videos/", params=params, timeout=30)
    resp.raise_for_status()
    blocked = exclude_ids | _KNOWN_MISTAGGED_CLIP_IDS
    return [h for h in resp.json().get("hits", []) if h["id"] not in blocked]


def _verify_thumbnail_relevance(thumbnail_url: str, subject: str) -> tuple:
    """Ask Gemini vision to confirm a clip's actual preview IMAGE shows the
    intended real-world subject, before spending bandwidth/render time on
    it. Tag-based text matching alone has repeatedly passed clips whose
    tags are technically real English words but wrong in context --
    reproduced live, same session: the insect "cricket" for a cricket-sport
    query, an antique pocket-watch for a "measuring chain" query, ocean
    surfing/underwater reef for "swimming", a snowy-pitch tag on an actual
    motorcycle-riders clip, table tennis for bare "tennis", and a posed
    stock-photography "couple holding tennis rackets" ad shot for "tennis
    doubles match" -- technically on-subject but exactly the generic/
    staged look flagged repeatedly as not acceptable for a named-player
    sports video. No amount of per-word negative-tag patching closes this
    class of bug for good -- English has too many ambiguous/overlapping
    words, and tag text can't distinguish real gameplay from a stock photo
    of models. Checking the real pixel content once, here, closes all of
    them at the same time.

    Returns (True, "") if relevant, or if verification itself fails/is
    unavailable (fail-open -- a skipped check should never block the whole
    pipeline on an API hiccup or missing key). Returns (False, reason) only
    when the model is confident the image does NOT show the subject.
    """
    if not gemini_client or not thumbnail_url:
        return True, ""
    try:
        resp = requests.get(thumbnail_url, timeout=15)
        resp.raise_for_status()
        img = Image.open(io.BytesIO(resp.content)).convert("RGB")
        prompt = (
            "This is the preview image for a stock video clip being "
            f"considered for a short, real sports-facts video about: \"{subject}\".\n"
            "Reject it (relevant=false) if EITHER is true:\n"
            "1) It's a coincidentally-named but unrelated thing (e.g. the "
            "insect \"cricket\" when the subject is the sport, a "
            "wristwatch/clock for a measuring \"chain\", a car for "
            "\"golf\", cardboard boxes for \"boxing\").\n"
            "2) The people in frame are NOT actually doing the activity --"
            " e.g. standing still facing the camera holding equipment as "
            "a prop (a fashion/product-ad pose), or a plain studio "
            "portrait with no real venue. This is about genuine "
            "engagement in the activity, not video quality or lighting: "
            "someone actually swimming, mid-swing, mid-match, training,\n"
            "or in a real court/pool/pitch/gym/crowd is FINE even if the "
            "footage looks clean, professional, well-lit, or is a wide/"
            "static/aerial shot -- only reject a clear posed-for-camera "
            "prop shot, not real footage of the real activity.\n"
            "Reply with ONLY compact JSON, nothing else: "
            '{"relevant": true or false, "reason": "one short sentence"}'
        )
        resp2 = gemini_client.models.generate_content(
            model="gemini-2.5-flash", contents=[prompt, img])
        text = (resp2.text or "").strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:]
        data = json.loads(text.strip())
        return bool(data.get("relevant", True)), data.get("reason", "")
    except Exception as e:
        log(f"  Visual verification skipped ({e}) -- accepting on tag match alone")
        return True, ""


def fetch_clip(query: str, clip_dir: str, exclude_ids: set = None) -> str:
    exclude_ids = exclude_ids or set()
    log(f"Pixabay search: '{query}'")
    hits = _search_pixabay(query, exclude_ids)
    confirmed = _filter_by_tag_relevance(hits, query) if hits else []

    if not confirmed:
        # Nothing in this batch is genuinely on-topic (often because dedup
        # already excluded the few real matches). Retry with just the core
        # subject word instead of silently accepting an irrelevant clip --
        # e.g. "golf ball flying slow motion" -> "golf".
        #
        # ONLY ever broaden to a recognized sport word (_KNOWN_SPORT_TERMS)
        # -- never to an arbitrary leftover word. Design flaw found and
        # fixed 2026-08-25 after NINE separate confirmed mismatches this
        # session alone from broadening to whatever word happened to be
        # left ("new" -> fireworks, "team" -> office desk, "victory" ->
        # celebration scene, "knee" -> landscape, "goal" -> waterfall,
        # "celebration" -> drink-pouring, "free" and "late" -> a deer in a
        # forest). No amount of blocklisting individual words closes this
        # class of bug -- English has too many generic words. Only a
        # recognized sport name is safe to search alone; if the query
        # doesn't contain one, there is no safe broadened fallback, so
        # this query fails cleanly instead of guessing.
        STOPWORDS = {"a", "an", "the", "in", "on", "at", "of", "and", "or", "with"}
        subject_words = [w for w in query.lower().split()
                          if w not in STOPWORDS and len(w) > 2
                          and w not in _CAMERA_TECHNIQUE_TERMS
                          and w not in _WEAK_BROADENING_WORDS]
        sport_word = next((w for w in subject_words if w in _KNOWN_SPORT_TERMS), None)
        if sport_word and sport_word != query.lower().strip():
            log(f"  No tag-confirmed match for '{query}' -- retrying with '{sport_word}'")
            hits2 = _search_pixabay(sport_word, exclude_ids)
            confirmed = _filter_by_tag_relevance(hits2, sport_word) if hits2 else []

    if not confirmed:
        raise Exception(f"No tag-relevant Pixabay clip found for: {query}")

    # Prefer clips long enough to survive prepare_segment()'s beat-synced
    # freeze-effect math without hitting its empty-subclips fallback (which
    # silently lies about duration and makes moviepy freeze on the last
    # real frame for the rest of the segment -- reproduced live 2026-08-19:
    # a 6.87s clip assigned to a ~20s segment froze for 8+ seconds).
    # Mirrors topic_checker.py's MIN_SAFE_DURATION; duplicated rather than
    # imported since topic_checker.py already imports this module.
    MIN_SAFE_DURATION = 15.0
    long_enough = [h for h in confirmed if h.get("duration", 0) >= MIN_SAFE_DURATION]
    pool = long_enough or confirmed
    if not long_enough:
        best = max(h.get("duration", 0) for h in confirmed)
        log(f"  No tag-confirmed clip for '{query}' is >= {MIN_SAFE_DURATION:.0f}s "
            f"(best available: {best:.1f}s) -- using it anyway, shorter than ideal")

    # Visual verification gate: tag-text matching is not proof of visual
    # content (see _verify_thumbnail_relevance docstring). Shuffle up to 8
    # candidates and check each one's real preview image before spending
    # bandwidth downloading its video -- take the first that actually
    # passes instead of trusting tags alone via random.choice.
    candidates = pool[:min(8, len(pool))]
    random.shuffle(candidates)
    rejected = []
    for hit in candidates:
        vid_id = hit["id"]
        videos = hit.get("videos", {})
        thumb = videos.get("tiny", {}).get("thumbnail", "")
        ok, reason = _verify_thumbnail_relevance(thumb, query)
        if not ok:
            rejected.append((vid_id, reason))
            continue

        clip_url = quality = None
        for q in ["large", "medium", "small", "tiny"]:
            v = videos.get(q, {})
            if v.get("url"):
                clip_url, quality = v["url"], q
                break
        if not clip_url:
            continue

        os.makedirs(clip_dir, exist_ok=True)
        fname = f"clip_{vid_id}_{quality}.mp4"
        fpath = os.path.join(clip_dir, fname)
        if os.path.exists(fpath) and os.path.getsize(fpath) > 50_000:
            log(f"  Cached: {fname}")
            return fpath, vid_id

        log(f"  Downloading clip {vid_id} ({quality})...")
        r = requests.get(clip_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=120, stream=True)
        r.raise_for_status()
        with open(fpath, "wb") as f:
            for chunk in r.iter_content(65536): f.write(chunk)
        mb = os.path.getsize(fpath) / 1e6
        log(f"  Done: {fname} ({mb:.1f}MB)")
        return fpath, vid_id

    if rejected:
        log(f"  All {len(rejected)} candidates for '{query}' failed visual verification: {rejected}")
    raise Exception(f"No visually-verified Pixabay clip found for: {query}")

def fetch_pexels_clip(query: str, clip_dir: str, exclude_ids: set = None) -> tuple:
    """Fetch a video clip from the Pexels API.
    Returns (file_path, clip_id). Raises Exception on failure.
    """
    exclude_ids = exclude_ids or set()
    log(f"Pexels search: '{query}'")
    params = {"query": query, "per_page": 15, "page": 1}
    headers = {"Authorization": config.PEXELS_API_KEY}
    resp = requests.get("https://api.pexels.com/videos/search", params=params, headers=headers, timeout=30)
    resp.raise_for_status()
    hits = [h for h in resp.json().get("videos", []) if h["id"] not in exclude_ids]
    if not hits:
        raise Exception(f"No Pexels results for: {query}")

    # Same visual verification gate as fetch_clip() -- Pexels search is
    # more semantic than Pixabay's tags but still not proof of frame
    # content; check each candidate's real preview image before download.
    candidates = hits[:min(8, len(hits))]
    random.shuffle(candidates)
    rejected = []
    for hit in candidates:
        clip_id = hit["id"]
        thumb = hit.get("image", "")
        ok, reason = _verify_thumbnail_relevance(thumb, query)
        if not ok:
            rejected.append((clip_id, reason))
            continue
        video_files = hit.get("video_files", [])
        if not video_files:
            continue
        video_files.sort(key=lambda v: v.get("height", 0), reverse=True)
        clip_url = video_files[0]["link"]
        os.makedirs(clip_dir, exist_ok=True)
        fname = f"pexels_{clip_id}.mp4"
        fpath = os.path.join(clip_dir, fname)
        if os.path.exists(fpath) and os.path.getsize(fpath) > 50_000:
            log(f"  Cached Pexels clip: {fname}")
            return fpath, clip_id
        log(f"  Downloading Pexels clip {clip_id}...")
        r = requests.get(clip_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=120, stream=True)
        r.raise_for_status()
        with open(fpath, "wb") as f:
            for chunk in r.iter_content(65536):
                f.write(chunk)
        mb = os.path.getsize(fpath) / 1e6
        log(f"  Saved Pexels clip {fname} ({mb:.1f}MB)")
        return fpath, clip_id

    if rejected:
        log(f"  All {len(rejected)} Pexels candidates for '{query}' failed visual verification: {rejected}")
    raise Exception(f"No visually-verified Pexels clip found for: {query}")

# ── Cross-video clip-reuse tracking ────────────────────────────────────────
# fetch_clip()/fetch_pexels_clip() already dedupe *within* one download_clips()
# call via exclude_ids, but that set is thrown away when the call returns --
# nothing stopped a later video from picking the exact same clip a prior
# video already used. This persists used IDs across every run so repeats are
# excluded channel-wide, not just within a single video's 3 clips.
USED_CLIPS_FILE = os.path.join("output", "used_stock_clips.json")


def _load_used_clip_ids() -> dict:
    if os.path.exists(USED_CLIPS_FILE):
        try:
            with open(USED_CLIPS_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"pixabay": [], "pexels": []}


def _record_used_clip_ids(source: str, ids: set):
    if not ids:
        return
    state = _load_used_clip_ids()
    state.setdefault(source, [])
    seen = set(state[source])
    state[source].extend(str(i) for i in ids if str(i) not in seen)
    os.makedirs(os.path.dirname(USED_CLIPS_FILE), exist_ok=True)
    with open(USED_CLIPS_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


# ── Step 3: Download 3 topic-matched clips ────────────────────────────────────
def _generate_search_terms_from_script(script: dict, amount: int = 3) -> list:
    """Derive stock-footage search terms from the ACTUAL finished script
    text via Gemini, instead of relying on terms hand-written before the
    script existed. Modeled on MoneyPrinterTurbo's generate_terms() --
    terms drawn from the real narration match footage far better than
    guesses made in advance (e.g. "golf ball flying slow motion", written
    before the script, matched nothing genuinely on-topic on Pixabay;
    a term like "golf ball dimples" pulled from the finished script does)."""
    hook, body, cta = script.get("hook", ""), script.get("body", ""), script.get("cta", "")
    full_text = " ".join(filter(None, [hook, body, cta])).strip()
    if not gemini_client or not full_text:
        return []
    try:
        prompt = (
            f"Generate exactly {amount} stock-video search terms, one per "
            "segment below (HOOK, BODY, CLOSING), in that order. Each term "
            "must be 1-3 words describing a concrete, filmable subject. "
            "The CLOSING segment is often a personal opinion/reaction with "
            "no literal visual in it (e.g. \"this feels like magic to me\") "
            "-- in that case, do NOT extract words from the opinion itself; "
            "instead give a term for the video's overall subject (inferred "
            "from HOOK and BODY). Do NOT use a specific team, club, brand, "
            "or player name as or within a term (e.g. not \"Arsenal team\" "
            "or \"Messi\") -- free stock-footage libraries have no rights-"
            "managed footage of real teams/athletes, so a named term reliably "
            "returns nothing and that segment loses its clip entirely. "
            "Describe the generic visual subject instead (e.g. \"soccer team "
            "celebration\", \"football stadium crowd\") and let the narration "
            "carry the specific name. The script below may be in a language "
            "other than English -- the search terms themselves must ALWAYS "
            "be in English regardless, since they query English-tagged "
            "stock-footage libraries. Reply with ONLY a JSON array of "
            f"{amount} English strings, nothing else.\n\n"
            f"HOOK: {hook}\nBODY: {body}\nCLOSING: {cta}"
        )
        resp = gemini_client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        text = resp.text.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:]
        terms = json.loads(text.strip())
        if isinstance(terms, list) and terms and all(isinstance(t, str) for t in terms):
            return terms[:amount]
    except Exception as e:
        log(f"  Gemini search-term generation failed ({e}) — falling back to script['queries']")
    return []


def download_clips(script: dict) -> list:
    clip_dir = os.path.join(config.OUTPUT_DIR, "raw_clips")
    os.makedirs(clip_dir, exist_ok=True)
    already_used = _load_used_clip_ids()

    # 0. Git/CC0 asset library (copyright-safe, free public repos)
    if getattr(config, "USE_GIT_ASSETS", False):
        try:
            import git_asset_library as gal
            paths = gal.pick_video_clips(script, count=3)
            if len(paths) >= 2:
                log(f"Git asset library: {len(paths)} royalty-free clips")
                return paths
        except Exception as e:
            log(f"Git assets failed ({e}) — continuing with other sources")

    default_queries = ["soccer goal", "football stadium", "soccer player"]
    queries = _generate_search_terms_from_script(script) or script.get("queries", default_queries)
    log(f"Stock footage search terms: {queries}")

    # 1. Try Pexels stock footage first if API key is set
    if getattr(config, "PEXELS_API_KEY", ""):
        # API ids come back as int; persisted ids are stored as str -- normalize to int so exclusion checks actually match
        paths, used_ids = [], set(int(x) for x in already_used.get("pexels", []))
        for q in queries:
            try:
                path, clip_id = fetch_pexels_clip(q, clip_dir, exclude_ids=used_ids)
                paths.append(path)
                used_ids.add(clip_id)
            except Exception as e:
                log(f"  Pexels clip fetch failed for '{q}': {e}")
        if len(paths) == 3:
            _record_used_clip_ids("pexels", used_ids)
            return paths
        else:
            log("Pexels did not return enough clips, falling back to Pixabay")

    # 2. Fallback to Pixabay stock videos
    log("Using Pixabay stock videos fallback...")
    # API ids come back as int; persisted ids are stored as str -- normalize to int so exclusion checks actually match
    paths, used_ids = [], set(int(x) for x in already_used.get("pixabay", []))
    for q in queries:
        try:
            path, vid_id = fetch_clip(q, clip_dir, exclude_ids=used_ids)
            paths.append(path)
            used_ids.add(vid_id)
        except Exception as e:
            log(f"  Clip fetch failed for '{q}': {e}")
    if not paths:
        raise Exception("Could not download any Pixabay clips")
    _record_used_clip_ids("pixabay", used_ids)
    return paths


# Duplicate fallback code removed – using the primary download_clips implementation.



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


# ── Step 4: ElevenLabs / Cloned voiceover ─────────────────────────────────────
def generate_voiceover(script: dict) -> str:
    text = f"{script['hook']}. {script['body']} {script['cta']}"
    os.makedirs(config.AUDIO_DIR, exist_ok=True)
    p = os.path.join(config.AUDIO_DIR, f"vo_{int(time.time())}.mp3")

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
    if config.ELEVENLABS_API_KEY:
        log(f"ElevenLabs TTS: {len(text)} chars...")
        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{config.ELEVENLABS_VOICE_ID}"
            headers = {"xi-api-key": config.ELEVENLABS_API_KEY, "Content-Type": "application/json"}
            payload = {"text": text, "model_id": "eleven_turbo_v2_5",
                       "voice_settings": {"stability": 0.45, "similarity_boost": 0.80}}
            r = requests.post(url, json=payload, headers=headers, timeout=60)
            if r.status_code == 200:
                with open(p, "wb") as f: f.write(r.content)
                log(f"ElevenLabs Voice saved: {p}")
                return p
            else:
                log(f"ElevenLabs status {r.status_code}: {r.text[:150]}")
        except Exception as e:
            log(f"ElevenLabs request error: {e}")

    # 2. Free Edge-TTS fallback (100% free, natural human-like voice)
    log("Falling back to free, premium Microsoft Edge-TTS voice...")
    try:
        import asyncio
        import edge_tts
        
        # Deep, natural, professional English voice
        voice = "en-US-ChristopherNeural"
        
        async def run_edge():
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(p)
            
        asyncio.run(run_edge())
        log(f"Edge-TTS Voice saved: {p}")
        return p
    except Exception as edge_err:
        log(f"Edge-TTS fallback also failed: {edge_err}")
        raise Exception("Voice generation failed completely (both ElevenLabs and Edge-TTS failed)")


# ── Step 5: Background music ──────────────────────────────────────────────────
def get_music(duration: float = 30.0) -> str:
    try:
        import music_generator
        path = music_generator.get_original_music("funk", audio_dir=config.AUDIO_DIR, duration=duration)
        if os.path.exists(path) and os.path.getsize(path) > 10000:
            log(f"Using synthesized music: {os.path.basename(path)}")
            return path
    except Exception as e:
        log(f"Synthesized music failed ({e}) — falling back to download")

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


# ── Step 6: Text overlay (caption style — minimal, bottom only) ───────────────
_FONT_CACHE = {}

def get_font(size, bold=False):
    key = (size, bold)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    
    font = None
    for p in [
        "C:\\Windows\\Fonts\\Impact.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf" if bold else "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
    ]:
        if os.path.exists(p):
            try:
                font = ImageFont.truetype(p, size)
                break
            except:
                pass
    if font is None:
        font = ImageFont.load_default()
    
    _FONT_CACHE[key] = font
    return font

def stroke_text(draw, text, x, y, font, fill=(255,255,255), stroke=5):
    draw.text((x, y), text, font=font, fill=fill, stroke_width=stroke, stroke_fill=(0,0,0))

def split_into_phrases(text, max_words=3):
    words = text.split()
    phrases = []
    for i in range(0, len(words), max_words):
        phrases.append(" ".join(words[i:i+max_words]))
    return phrases

_CHAR_IMAGE = None

def get_char_image():
    global _CHAR_IMAGE
    if _CHAR_IMAGE is not None:
        return _CHAR_IMAGE
    
    path = os.path.join(config.OUTPUT_DIR, "soccer_host.png")
    if os.path.exists(path):
        try:
            _CHAR_IMAGE = Image.open(path).convert("RGBA")
            w_orig, h_orig = _CHAR_IMAGE.size
            h_new = 320
            w_new = int(w_orig * (h_new / h_orig))
            _CHAR_IMAGE = _CHAR_IMAGE.resize((w_new, h_new), Image.Resampling.LANCZOS)
            log(f"Cached PNGTuber character avatar: {w_new}x{h_new}")
        except Exception as e:
            log(f"Failed to load character image ({e})")
            _CHAR_IMAGE = False
    else:
        _CHAR_IMAGE = False
    return _CHAR_IMAGE

_BALL_IMAGE = None

def get_ball_image():
    global _BALL_IMAGE
    if _BALL_IMAGE is not None:
        return _BALL_IMAGE
    path = os.path.join(config.OUTPUT_DIR, "soccer_ball.png")
    if os.path.exists(path):
        try:
            _BALL_IMAGE = Image.open(path).convert("RGBA")
        except Exception:
            _BALL_IMAGE = False
    else:
        _BALL_IMAGE = False
    return _BALL_IMAGE

def render_overlay(frame: np.ndarray, script: dict, t: float,
                   duration: float, theme: dict, segment: str, vo_sound = None, vo_fps = 44100) -> np.ndarray:
    """
    Highly optimized caption-style overlay.
    Uses numpy array slicing for scrims to speed up rendering by 15x.
    """
    frame = frame.copy()
    H, W, C = frame.shape
    acc = theme["accent"]
    pct = t / duration

    visual_style = getattr(config, "VISUAL_STYLE", "ai_animation")

    if visual_style != "footage":
        # ── Top Scrim (NumPy optimized) ──
        # Top 90px: fade from 0.4 (dark) to 1.0 (normal)
        top_y = 90
        alpha_top = np.linspace(0.4, 1.0, top_y)[:, np.newaxis, np.newaxis]
        frame[0:top_y, :, :] = (frame[0:top_y, :, :] * alpha_top).astype(np.uint8)

        # ── Bottom Scrim (NumPy optimized) ──
        # Bottom 340px: fade from 1.0 (normal) to 0.3 (dark)
        scrim_h = 340
        alpha_bot = np.linspace(1.0, 0.3, scrim_h)[:, np.newaxis, np.newaxis]
        frame[H - scrim_h:H, :, :] = (frame[H - scrim_h:H, :, :] * alpha_bot).astype(np.uint8)

    # Convert to PIL RGB for text drawing
    img = Image.fromarray(frame)
    draw = ImageDraw.Draw(img)

    # ── Cartoon character overlay (talking avatar PNGTuber style) ──
    if getattr(config, "VISUAL_STYLE", "ai_animation") == "ai_animation":
        char_img = get_char_image()
        if char_img:
            # Determine talking volume at current time
            is_talking = False
            if vo_sound is not None:
                try:
                    idx = int(t * vo_fps)
                    window = int(0.04 * vo_fps)
                    sample_slice = vo_sound[idx : idx + window]
                    if len(sample_slice) > 0:
                        vol = np.max(np.abs(sample_slice))
                        if vol > 0.035:
                            is_talking = True
                except Exception:
                    pass
            
            cw, ch = char_img.size
            x_base = W - cw - 20
            y_base = H - ch - 50 # slightly above progress bar
            
            c_frame = char_img
            if is_talking:
                y_offset = -abs(np.sin(t * 18)) * 14
                angle = np.sin(t * 18) * 3.5
                scale = 1.0 + abs(np.sin(t * 18)) * 0.035
                
                c_frame = char_img.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
                cw_rot, ch_rot = c_frame.size
                c_frame = c_frame.resize((int(cw_rot * scale), int(ch_rot * scale)), Image.Resampling.LANCZOS)
                cw_new, ch_new = c_frame.size
                x_pos = x_base + (cw - cw_new) // 2
                y_pos = y_base + (ch - ch_new) + int(y_offset)
            else:
                x_pos = x_base
                y_pos = y_base
                
            img.paste(c_frame, (x_pos, y_pos), c_frame)

        # ── Cartoon spinning soccer ball overlay ──
        ball_img = get_ball_image()
        if ball_img:
            loop_dur = 3.5
            t_loop = t % loop_dur
            pct_loop = t_loop / loop_dur
            if pct_loop < 0.70:
                pct_active = pct_loop / 0.70
                bx = int(-120 + (W + 240) * pct_active)
                by = int((H - 240) - (H * 0.45) * pct_active - np.sin(np.pi * pct_active) * 250)
                ball_rot = ball_img.rotate(pct_active * 360 * 3.5, resample=Image.Resampling.BICUBIC)
                img.paste(ball_rot, (bx, by), ball_rot)

    visual_style = getattr(config, "VISUAL_STYLE", "ai_animation")

    # ── Header Bar & Hook Title ──
    v_hook = script.get("visual_hook", script.get("title", "FOOTBALL SHORTS")).split("#")[0].strip()
    
    if visual_style == "footage":
        # Draw visual hook text centered inside the top black bar
        clean_hook = "".join([c for c in v_hook if ord(c) < 0x2000]).strip()
        vh_size = 50
        vh_font = get_font(vh_size, bold=True)
        while vh_size > 36 and draw.textbbox((0,0), clean_hook, font=vh_font)[2] > (W - 60):
            vh_size -= 4
            vh_font = get_font(vh_size, bold=True)
            
        vh_bb = draw.textbbox((0,0), clean_hook, font=vh_font)
        vh_w = vh_bb[2] - vh_bb[0]
        vh_h = vh_bb[3] - vh_bb[1]
        vh_x = (W - vh_w) // 2
        vh_y = (438 - vh_h) // 2 - 10  # Centered inside top black bar
        
        stroke_text(draw, clean_hook, vh_x, vh_y, vh_font, fill=(255, 255, 255), stroke=3)
    else:
        # ── Channel name badge top-left (only for AI animations) ──
        font_ch = get_font(32)
        ch = f"⚽ {config.CHANNEL_NAME}"
        draw.text((24, 20), ch, font=font_ch, fill=(0,0,0))   # shadow
        draw.text((22, 18), ch, font=font_ch, fill=acc)

        # ── Permanent Visual Hook Header inside dark rounded capsule ──
        vh_size = 52
        vh_font = get_font(vh_size, bold=True)
        while vh_size > 36 and draw.textbbox((0,0), v_hook, font=vh_font)[2] > (W - 80):
            vh_size -= 4
            vh_font = get_font(vh_size, bold=True)
        
        vh_bb = draw.textbbox((0,0), v_hook, font=vh_font)
        vh_w = vh_bb[2] - vh_bb[0]
        vh_h = vh_bb[3] - vh_bb[1]
        vh_x = (W - vh_w) // 2
        vh_y = 130
        
        pad_x, pad_y = 20, 10
        draw.rounded_rectangle(
            [vh_x - pad_x, vh_y - pad_y, vh_x + vh_w + pad_x, vh_y + vh_h + pad_y],
            radius=14,
            fill=(10, 10, 10, 200)
        )
        stroke_text(draw, v_hook, vh_x, vh_y, vh_font, fill=(255, 230, 0), stroke=4)

    def draw_centered_phrase(phrase, y_pos, font_size, max_w, color, stroke_val):
        size = font_size
        font = get_font(size, bold=True)
        while size > 40 and draw.textbbox((0,0), phrase, font=font)[2] > max_w:
            size -= 5
            font = get_font(size, bold=True)
        bb = draw.textbbox((0,0), phrase, font=font)
        x = (W - (bb[2]-bb[0])) // 2
        stroke_text(draw, phrase, x, y_pos, font, color, stroke=stroke_val)

    # Calculate phrase y positions (keep gameplay clean by pushing text to bottom bar)
    y_hook = 980 if visual_style == "footage" else H // 2 - 200
    y_body = 980 if visual_style == "footage" else H // 2 + 100
    y_cta = 980 if visual_style == "footage" else H // 2 + 150

    # ── HOOK (phrase-by-phrase) ──
    if pct < 0.28:
        phrases = split_into_phrases(script["hook"], max_words=3)
        n_phrases = len(phrases)
        span = 0.28
        phrase_idx = int(pct / (span / n_phrases))
        phrase_idx = min(max(0, phrase_idx), n_phrases - 1)
        active_phrase = phrases[phrase_idx]
        draw_centered_phrase(active_phrase, y_hook, 85, W - 80, acc, stroke_val=7)

    # ── BODY caption (phrase-by-phrase) ──
    elif 0.22 <= pct < 0.82:
        phrases = split_into_phrases(script["body"], max_words=3)
        n_phrases = len(phrases)
        span = 0.82 - 0.22
        phrase_idx = int((pct - 0.22) / (span / n_phrases))
        phrase_idx = min(max(0, phrase_idx), n_phrases - 1)
        active_phrase = phrases[phrase_idx]
        draw_centered_phrase(active_phrase, y_body, 80, W - 80, (255,255,255), stroke_val=7)

    # ── CTA (phrase-by-phrase) ──
    elif pct >= 0.78:
        phrases = split_into_phrases(script["cta"], max_words=3)
        n_phrases = len(phrases)
        span = 1.0 - 0.78
        phrase_idx = int((pct - 0.78) / (span / n_phrases))
        phrase_idx = min(max(0, phrase_idx), n_phrases - 1)
        active_phrase = phrases[phrase_idx]
        draw_centered_phrase(active_phrase, y_cta, 85, W - 80, acc, stroke_val=7)

        # ── Draw Subscribe Button & Bell Icon Badge (Bottom Bar centered) ──
        button_w, button_h = 320, 70
        bx = (W - button_w) // 2
        by = 1080 if visual_style == "footage" else H // 2 + 250
        
        # YouTube Red button background with subtle rounded border
        draw.rounded_rectangle([bx, by, bx + button_w, by + button_h], radius=15, fill=(255, 0, 0))
        
        # Text inside the button: "SUBSCRIBE 🔔"
        font_sub = get_font(32, bold=True)
        sub_text = "SUBSCRIBE 🔔"
        sub_bb = draw.textbbox((0,0), sub_text, font=font_sub)
        tx = bx + (button_w - (sub_bb[2] - sub_bb[0])) // 2
        ty = by + (button_h - (sub_bb[3] - sub_bb[1])) // 2 - 3
        draw.text((tx, ty), sub_text, font=font_sub, fill=(255, 255, 255))

    # ── Progress bar ──
    bw = int(W * pct)
    draw.rectangle([(0, H-8),(W, H)], fill=(30,30,30))
    if bw > 0: draw.rectangle([(0, H-8),(bw, H)], fill=acc)

    return np.array(img)


# ── Step 7: Prepare one video segment from a raw clip ─────────────────────────
def prepare_segment(clip_path: str, seg_duration: float, segment_index: int = None, num_segments: int = 3, apply_freeze: bool = True) -> VideoFileClip:
    """
    Load, crop to 9:16, resize, trim, and apply visual editing for stylistic variety
    (all source clips are royalty-free stock/AI-generated footage, not broadcast content):
      - Random horizontal flip
      - Saturation boost (more vivid look)
      - Brightness/contrast adjustment
      - Subtle zoom-in (adds motion/energy)
    """
    from PIL import Image, ImageEnhance
    src = VideoFileClip(clip_path, audio=False)
    sw, sh = src.size

    visual_style = getattr(config, "VISUAL_STYLE", "ai_animation")

    if visual_style == "footage":
        # Crop to exactly 16:9 landscape aspect ratio
        cw = int(sh * 16 / 9)
        if cw > sw:
            ch = int(sw * 9 / 16)
            src = _crop(src, 0, (sh - ch) // 2, sw, (sh + ch) // 2)
        else:
            src = _crop(src, (sw - cw) // 2, 0, (sw + cw) // 2, sh)
            
        # Subtle zoom-in for visual energy on 16:9 clip
        zoom = random.uniform(1.05, 1.12)
        zw = int(720 * zoom)
        zh = int(405 * zoom)
        src = _resize(src, (zw, zh))
        # Crop back to exact 720x405 from center
        x1 = (zw - 720) // 2
        y1 = (zh - 405) // 2
        src = _crop(src, x1, y1, x1 + 720, y1 + 405)
    else:
        # Original 9:16 crop/resize for AI animation images
        cw = int(sh * 9 / 16)
        if cw > sw:
            ch = int(sw * 16 / 9)
            src = _crop(src, 0, (sh - ch) // 2, sw, (sh + ch) // 2)
        else:
            src = _crop(src, (sw - cw) // 2, 0, (sw + cw) // 2, sh)

        # Subtle zoom (1.05x–1.12x)
        zoom = random.uniform(1.05, 1.12)
        zw = int(WIDTH * zoom)
        zh = int(HEIGHT * zoom)
        src = _resize(src, (zw, zh))
        # Crop back to exact 720x1280 from centre
        x1 = (zw - WIDTH)  // 2
        y1 = (zh - HEIGHT) // 2
        src = _crop(src, x1, y1, x1 + WIDTH, y1 + HEIGHT)

    # ── Random horizontal flip for visual variety ──
    do_flip = random.random() > 0.5
    if do_flip:
        def flip_frame(get_frame, t):
            return np.fliplr(get_frame(t))
        src = _fl(src, flip_frame)

    # ── Color grade: saturation + brightness via PIL ──
    sat_factor   = random.uniform(1.3, 1.6)   # vivid colours
    bright_factor = random.uniform(1.05, 1.15) # slightly brighter
    contrast_factor = random.uniform(1.1, 1.25)

    def color_grade(get_frame, t):
        frame = get_frame(t)
        img = Image.fromarray(frame)
        img = ImageEnhance.Color(img).enhance(sat_factor)
        img = ImageEnhance.Brightness(img).enhance(bright_factor)
        img = ImageEnhance.Contrast(img).enhance(contrast_factor)
        return np.array(img)

    src = _fl(src, color_grade)

    # ── Trim to seg_duration scaled for speed-up ──
    clip_dur   = src.duration
    
    # Calculate beat-synchronized normal and freeze durations (130 BPM Phonk tempo)
    beat_dur = 60.0 / 130.0
    approx_normal = seg_duration * 0.75
    normal_beats = round(approx_normal / beat_dur)
    
    if apply_freeze:
        normal_output_dur = normal_beats * beat_dur
        freeze_dur = seg_duration - normal_output_dur
    else:
        normal_output_dur = seg_duration
        freeze_dur = 0.0
        
    target_dur = normal_output_dur * 1.15
    actual_seg = min(target_dur, clip_dur - 0.2)
    
    if actual_seg <= 0.5:
        actual_seg = min(seg_duration * 1.15, clip_dur)
        freeze_dur = 0.0
        normal_output_dur = seg_duration

    if visual_style == "footage":
        # Splice several short, fast-paced sub-clips together for a dynamic edit style
        subclips = []
        rem = normal_output_dur
        sub_dur = 2.4  # short cuts keep pacing energetic

        # Skip the first/last couple seconds of longer stock clips, which are
        # often static establishing shots rather than the dynamic action
        start_offset = 3.0 if clip_dur > 8.0 else 0.0
        end_offset = 2.0 if clip_dur > 8.0 else 0.0
        safe_dur = max(0.5, clip_dur - start_offset - end_offset)
        
        if segment_index is not None:
            region_dur = safe_dur / num_segments
            region_start = start_offset + segment_index * region_dur
        else:
            region_dur = safe_dur
            region_start = start_offset
            
        while rem > 0:
            chunk_dur = min(rem, sub_dur)
            speed_mult = random.uniform(1.15, 1.25)
            src_dur = chunk_dur * speed_mult
            
            # Find a random start point within the region bounds
            if region_dur > src_dur + 0.3:
                c_start = region_start + random.uniform(0.0, region_dur - src_dur - 0.1)
            else:
                c_start = region_start
                
            c_end = c_start + src_dur

            # Never let a chunk request run past the source clip's real
            # length -- for a short clip in a narrow region this previously
            # made every chunk raise, leaving subclips empty and falling to
            # the _dur(src, normal_output_dur) branch below, which silently
            # lies about duration and makes moviepy freeze on the last real
            # frame for the rest of the segment instead of erroring.
            if c_end > clip_dur:
                c_end = clip_dur
                c_start = max(0.0, c_end - src_dur)

            try:
                chunk = src.subclipped(c_start, c_end) if hasattr(src, "subclipped") else src.subclip(c_start, c_end)
                chunk = _speed(chunk, speed_mult)
                chunk = _dur(chunk, chunk_dur)
                subclips.append(chunk)
            except Exception as chunk_err:
                log(f"  Failed to slice subclip: {chunk_err}")

            rem -= chunk_dur

        if subclips:
            normal_clip = concatenate_videoclips(subclips)
        else:
            # Every chunk attempt failed (e.g. clip_dur near zero) -- loop
            # whatever real footage exists rather than faking a duration
            # moviepy can't back with real frames.
            log(f"  All sub-clip attempts failed for this source; looping available footage instead of freezing")
            loops = max(1, int(normal_output_dur / max(0.5, clip_dur)) + 1)
            normal_clip = concatenate_videoclips([src] * loops)
            normal_clip = _dur(normal_clip, normal_output_dur)
    else:
        # Original simple trim for AI animation images
        if segment_index is not None:
            region_dur = clip_dur / num_segments
            region_start = segment_index * region_dur
            start = region_start + max(0.0, (region_dur - actual_seg) / 2)
            start = min(start, clip_dur - actual_seg - 0.1)
            start = max(0.0, start)
        else:
            max_start  = max(0.0, clip_dur - actual_seg - 0.1)
            start      = round(random.uniform(0, max_start), 3) if max_start > 0 else 0.0
        end        = round(start + actual_seg, 3)

        try:
            normal_clip = src.subclipped(start, end) if hasattr(src, "subclipped") else src.subclip(start, end)
        except Exception:
            normal_clip = _dur(src, actual_seg)

        try:
            normal_clip = _speed(normal_clip, 1.15)
        except Exception:
            pass
        normal_clip = _dur(normal_clip, normal_output_dur)

    if apply_freeze and freeze_dur > 0.0:
        try:
            # Extract last frame of the normal video segment
            last_frame = normal_clip.get_frame(normal_output_dur - 0.05)
            img_pil = Image.fromarray(last_frame)
            
            # Apply high-contrast monochrome (B&W) "Aura" color grade
            img_pil = ImageEnhance.Color(img_pil).enhance(0.0)      # B&W
            img_pil = ImageEnhance.Contrast(img_pil).enhance(1.6)   # high contrast
            img_pil = ImageEnhance.Brightness(img_pil).enhance(1.1) # slightly bright
            
            # Save temporary frame to prevent locking
            temp_freeze_dir = os.path.join(config.OUTPUT_DIR, "temp_freeze")
            os.makedirs(temp_freeze_dir, exist_ok=True)
            temp_freeze_path = os.path.join(temp_freeze_dir, f"freeze_{random.randint(1000, 9999)}.png")
            img_pil.save(temp_freeze_path)
            
            # Create a freeze ImageClip for the remaining duration of the segment
            freeze_clip = ImageClip(temp_freeze_path).with_duration(freeze_dur) if hasattr(ImageClip(temp_freeze_path), "with_duration") else ImageClip(temp_freeze_path).set_duration(freeze_dur)
            
            # Concatenate the normal action play and the B&W aura freeze
            src = concatenate_videoclips([normal_clip, freeze_clip])
            log(f"  Applied visual Aura-Freeze: {normal_output_dur:.2f}s normal + {freeze_dur:.2f}s B&W freeze frame")
        except Exception as freeze_err:
            log(f"  Failed to apply visual freeze: {freeze_err}")
            src = normal_clip
    else:
        src = normal_clip

    log(f"  Segment: zoom×{zoom:.2f} flip={do_flip} sat={sat_factor:.1f} (1.15x speed)")

    if visual_style == "footage":
        # Render a black background vertical layout (720x1280)
        bg = ColorClip(size=(WIDTH, HEIGHT), color=(0, 0, 0))
        bg = _dur(bg, src.duration)
        
        # Center the 720x405 landscape clip at y=438
        if hasattr(src, "with_position"):
            positioned = src.with_position((0, 438))
        else:
            positioned = src.set_position((0, 438))
            
        final_vertical = CompositeVideoClip([bg, positioned])
        final_vertical = _dur(final_vertical, src.duration)
        return final_vertical
    else:
        return src




def assemble(clip_paths: list, script: dict, vo_path: str,
             music_path: str, theme: dict, out_path: str, is_image_clips: bool = False):

    # Duplicate single clip path to slice 3 distinct segments from it
    if len(clip_paths) == 1 and not is_image_clips:
        clip_paths = [clip_paths[0]] * 3

    # Duration from voice, default to 21 seconds (7s per clip) if no voiceover
    if vo_path:
        vo_clip  = AudioFileClip(vo_path)
        duration = min(vo_clip.duration + 1.5, 58.0)
    else:
        vo_clip = None
        duration = 21.0
    log(f"Target duration: {duration:.1f}s, clips: {len(clip_paths)}")

    # Split duration equally across clips
    n_clips   = len(clip_paths)
    seg_dur   = duration / n_clips

    # Pre-load voiceover sound array
    try:
        if vo_path and vo_clip:
            vo_sound = vo_clip.to_soundarray()
            vo_fps = vo_clip.fps
        else:
            vo_sound = None
            vo_fps = 44100
    except Exception:
        vo_sound = None
        vo_fps = 44100

    # Build each segment with text overlay
    segments = []
    for i, cp in enumerate(clip_paths):
        seg_start = i * seg_dur
        try:
            if is_image_clips:
                img_clip = ImageClip(cp).with_duration(seg_dur) if hasattr(ImageClip(cp), "with_duration") else ImageClip(cp).set_duration(seg_dur)
                raw = apply_camera_movement(img_clip, seg_dur, index=i)
            else:
                # Map segment index to prioritize climax action for the hook
                # Hook (i=0) -> Climax region (index = n_clips - 1)
                # Body (i=1) -> Setup region (index = 0)
                # CTA (i=2) -> Transition region (index = 1)
                mapped_idx = (n_clips - 1) if i == 0 else (0 if i == 1 else 1)
                raw = prepare_segment(cp, seg_dur, segment_index=mapped_idx, num_segments=n_clips, apply_freeze=(i == 0))
        except Exception as e:
            log(f"Segment {i} failed ({e}) — skipping")
            continue

        # Capture variables for closure
        _ss = seg_start
        _sd = seg_dur
        _sc = script
        _th = theme
        _td = duration
        _vos = vo_sound
        _vof = vo_fps

        def make_overlay(get_frame, t, ss=_ss, sd=_sd, sc=_sc, th=_th, td=_td, vos=_vos, vof=_vof):
            absolute_t = ss + t
            # segment label (for future multi-clip logic)
            seg_label = "hook" if ss == 0 else ("cta" if ss + sd >= td * 0.78 else "body")
            try:
                return render_overlay(get_frame(t), sc, absolute_t, td, th, seg_label, vo_sound=vos, vo_fps=vof)
            except Exception as e:
                import traceback
                print(f"[ERROR in make_overlay] absolute_t={absolute_t:.2f}: {e}")
                traceback.print_exc()
                raise e

        seg = _fl(raw, make_overlay)
        seg = _dur(seg, seg_dur)
        segments.append(seg)

    if not segments:
        raise Exception("No valid video segments to assemble")

    video = concatenate_videoclips(segments, method="compose")
    video = _dur(video, duration)

    # Audio track mixing (Voice + Music)
    def make_aura_volume_filter(base_vol, peak_vol):
        def aura_audio_filter(gf, t):
            frame = gf(t)
            # Only apply pre-drop silence and peak volume drop during the Hook segment (t < seg_dur)
            hook_end = seg_dur
            pre_drop_start = hook_end * 0.75
            beat_dur = 60.0 / 130.0
            normal_beats = round(pre_drop_start / beat_dur)
            drop_time = normal_beats * beat_dur
            silence_start = drop_time - 0.276

            if isinstance(t, np.ndarray):
                v = np.where((t >= silence_start) & (t < drop_time), 0.01,
                             np.where((t >= drop_time) & (t < hook_end), peak_vol, base_vol))
                return (frame.T * v).T
            else:
                if silence_start <= t < drop_time:
                    v = 0.01
                elif drop_time <= t < hook_end:
                    v = peak_vol
                else:
                    v = base_vol
                return frame * v
        return aura_audio_filter

    if vo_clip:
        vo  = _dur(vo_clip, min(vo_clip.duration, duration))
        # Music (looped & quiet under voice)
        raw_music = AudioFileClip(music_path)
        if raw_music.duration < duration:
            n = int(duration / raw_music.duration) + 2
            raw_music = concatenate_audioclips([raw_music] * n)
        music = _dur(raw_music, duration)
        music = _fl_audio(music, make_aura_volume_filter(0.08, 0.28))
        try:
            mixed = CompositeAudioClip([music, vo])
        except Exception:
            mixed = vo
    else:
        # Pure instrumental beat-synced mode (louder background music)
        raw_music = AudioFileClip(music_path)
        if raw_music.duration < duration:
            n = int(duration / raw_music.duration) + 2
            raw_music = concatenate_audioclips([raw_music] * n)
        music = _dur(raw_music, duration)
        mixed = _fl_audio(music, make_aura_volume_filter(0.35, 0.58))
        
    mixed = _dur(mixed, duration)

    video = _audio(video, mixed)
    video = _dur(video, duration)

    os.makedirs(config.VIDEOS_DIR, exist_ok=True)
    log(f"Rendering HD → {out_path}")
    video.write_videofile(
        out_path,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        audio_bitrate="192k",
        logger="bar",
        threads=4,
        ffmpeg_params=[
            "-crf",    "23",
            "-preset", "ultrafast",
            "-pix_fmt","yuv420p",
            "-movflags","+faststart",
        ],
    )
    video.close()
    if vo_clip:
        try: vo_clip.close()
        except: pass
    log("✅ HD video render done!")


# ── Step 9: Upload ────────────────────────────────────────────────────────────
def upload(video_path: str, script: dict) -> str:
    try:
        if getattr(config, "USE_GIT_ASSETS", False) or os.getenv("USE_GIT_ASSETS", "").lower() == "true":
            import copyright_compliance as cc
            check = cc.validate_before_upload(script)
            if not check["passed"]:
                script = cc.auto_fix_script(script)
                check = cc.validate_before_upload(script)
            if check.get("attribution"):
                script["seo_description"] = (
                    script.get("seo_description", script.get("body", ""))
                    + check["attribution"]
                )
            cc.save_compliance_report(check)

        import phase5_upload as p5
        topic = {"id": int(time.time()), "title": script["title"],
                 "subject": script["hook"], "category": "FIFA World Cup 2026"}
        result = p5.upload_all(video_path, script, topic)
        url = result.get("youtube")
        if url: log(f"YouTube: {url}")
        return url
    except Exception as e:
        log(f"Upload error: {e}")
        return None


# ── Main ──────────────────────────────────────────────────────────────────────
def run_one_job():
    config.assert_safe_pipeline()
    log("=" * 60)
    log("  VISUAL SHORTS v3 — 3 CLIPS + CAPTIONS + AI VOICE")
    log("=" * 60)

    state = load_state()
    script = pick_script(state)
    theme  = COLOR_THEMES[(state.get("theme_idx", -1) + 1) % len(COLOR_THEMES)]
    state["theme_idx"] = (state.get("theme_idx", -1) + 1) % len(COLOR_THEMES)
    state["video_count"] = state.get("video_count", 0) + 1
    save_state(state)

    log(f"Script: {script['hook'][:60]}")
    log(f"Queries: {script['queries']}")

    try:
        # 1. Visuals
        visual_style = getattr(config, "VISUAL_STYLE", "ai_animation")
        log(f"Visual Style: {visual_style}")
        
        is_image_clips = False
        clip_paths = []
        
        if visual_style == "ai_animation":
            try:
                prompts = get_image_prompts(script)
                for i, p in enumerate(prompts):
                    path = fetch_ai_image(p, i)
                    if path:
                        clip_paths.append(path)
                if len(clip_paths) == 3:
                    is_image_clips = True
                    log("Successfully downloaded 3 AI illustration images!")
                else:
                    log("Could not download all 3 AI images — falling back to footage")
                    visual_style = "footage"
                    clip_paths = []
            except Exception as e:
                log(f"AI image generation failed ({e}) — falling back to footage")
                visual_style = "footage"
                clip_paths = []

        if not is_image_clips or visual_style != "ai_animation":
            clip_paths = download_clips(script)
            
        log(f"Got {len(clip_paths)} visual asset(s)")

        # Append FramedFacts signature sign-off to CTA text
        cta_text = script.get("cta", "")
        if "framed facts" not in cta_text.lower():
            cta_text = cta_text.strip()
            if cta_text.endswith("!") or cta_text.endswith("."):
                cta_text = cta_text[:-1] + " — and subscribe for more Framed Facts!"
            else:
                cta_text = cta_text + " — and subscribe for more Framed Facts!"
            script["cta"] = cta_text

        # 2. Voice
        try:
            vo_path = generate_voiceover(script)
        except Exception as e:
            log(f"Voice generation failed completely ({e}) — proceeding with pure instrumental beat drops!")
            vo_path = None

        if not vo_path:
            log("Running in instrumental beat-synced mode (No Voiceover)")

        # 3. Music
        vo_duration = 21.0
        if vo_path:
            try:
                vo_clip = AudioFileClip(vo_path)
                vo_duration = min(vo_clip.duration + 1.5, 58.0)
                vo_clip.close()
            except Exception:
                pass
        music_path = get_music(duration=vo_duration)

        # 4. Assemble
        out_path = os.path.join(config.VIDEOS_DIR, f"visual_{int(time.time())}.mp4")
        assemble(clip_paths, script, vo_path, music_path, theme, out_path, is_image_clips=is_image_clips)

        # 5. Upload
        url = upload(out_path, script)

        log("=" * 60)
        log(f"  VIDEO #{state['video_count']} COMPLETE!")
        log(f"  {script['title'][:65]}")
        if url: log(f"  YouTube: {url}")
        else:   log(f"  Saved:   {out_path}")
        log("=" * 60)

    except Exception as e:
        log(f"ERROR: {e}")
        import traceback; traceback.print_exc()


def main():
    log("=" * 60)
    log("  FIFA VISUAL SHORTS — 10x/DAY AUTO LOOP")
    log("  3 matched clips per video. AI voice. Zero copyright.")
    log("=" * 60)
    run_one_job()
    interval = 144 * 60
    while True:
        log(f"Next video in 144 minutes...")
        time.sleep(interval)
        run_one_job()


if __name__ == "__main__":
    main()
