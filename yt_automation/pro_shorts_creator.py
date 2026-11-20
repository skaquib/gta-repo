"""
pro_shorts_creator.py — PROFESSIONAL Expert-Level Video Creator
================================================================
Clean, minimal, expert football Shorts like Tifo Football / The Athletic FC:

  - Original anime-style AI-generated video clips (AnimateDiff), 1080x1920
  - Clean word-by-word caption overlay (white text, black stroke, no boxes)
  - AI voice narration (ElevenLabs cloned voice > Kokoro local > Edge-TTS)
  - Original synthesized background music (zero copyright)
  - Stylistic visual variety (zoom, flip, color grade)
  - CRF 18 + slow preset = broadcast-quality output
  - Auto-upload to YouTube

NO bouncing balls. NO avatars. NO other gimmicks.
Optional subtle hook-segment freeze frame, tuned via config.FREEZE_INTENSITY.
"""

import os, sys, time, json, random, re, math, requests
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter, ImageOps
from logger import log
import config

# ── MoviePy v2 ────────────────────────────────────────────────────────────────
try:
    from moviepy import (VideoFileClip, AudioFileClip, ImageClip, VideoClip,
                         concatenate_videoclips, concatenate_audioclips,
                         CompositeAudioClip, CompositeVideoClip, ColorClip)
    from moviepy.video.fx import CrossFadeIn, CrossFadeOut
    MOVIEPY_V2 = True
except ImportError:
    from moviepy.editor import (VideoFileClip, AudioFileClip, ImageClip, VideoClip,
                                concatenate_videoclips, concatenate_audioclips,
                                CompositeAudioClip, CompositeVideoClip, ColorClip)
    CrossFadeIn = CrossFadeOut = None
    MOVIEPY_V2 = False

CROSSFADE_DUR = 0.35  # seconds, cinematic transition between scenes

# ── Gemini ────────────────────────────────────────────────────────────────────
from google import genai
_GKEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
gemini_client = genai.Client(api_key=_GKEY) if _GKEY else None

# ── Constants ─────────────────────────────────────────────────────────────────
STATE_FILE    = "pro_creator_state.json"
WIDTH, HEIGHT = 1080, 1920          # Full HD vertical
FPS           = 30
CHANNEL       = getattr(config, "CHANNEL_NAME", "FramedFacts")

# Fallback CC0 music URLs (only used if music_generator fails)
MUSIC_FALLBACK = [
    "https://assets.mixkit.co/music/preview/mixkit-sport-action-1027.mp3",
    "https://assets.mixkit.co/music/preview/mixkit-winning-is-everything-2142.mp3",
]


# ══════════════════════════════════════════════════════════════════════════════
#  MOVIEPY COMPATIBILITY
# ══════════════════════════════════════════════════════════════════════════════

def _dur(c, d):
    return c.with_duration(d) if MOVIEPY_V2 else c.set_duration(d)

def _audio(c, a):
    return c.with_audio(a) if MOVIEPY_V2 else c.set_audio(a)

def _vol(c, f):
    if hasattr(c, "with_volume_scaled"): return c.with_volume_scaled(f)
    if hasattr(c, "multiply_volume"):    return c.multiply_volume(f)
    return c.volumex(f)

def _crop(c, x1, y1, x2, y2):
    if hasattr(c, "cropped"): return c.cropped(x1=x1, y1=y1, x2=x2, y2=y2)
    return c.crop(x1=x1, y1=y1, x2=x2, y2=y2)

def _resize(c, sz):
    if hasattr(c, "resized"): return c.resized(sz)
    return c.resize(sz)

def _fl(c, fn):
    if hasattr(c, "fl"): return c.fl(fn)
    return c.transform(fn)

def _speed(c, f):
    if hasattr(c, "multiply_speed"): return c.multiply_speed(f)
    try:
        import moviepy.video.fx.all as vfx
        return c.fx(vfx.speedx, f)
    except: return c


# ══════════════════════════════════════════════════════════════════════════════
#  STATE
# ══════════════════════════════════════════════════════════════════════════════

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f: return json.load(f)
        except: pass
    return {"count": 0, "used_topics": []}

def save_state(s):
    with open(STATE_FILE, "w") as f: json.dump(s, f, indent=2)


# ══════════════════════════════════════════════════════════════════════════════
#  1. SCRIPT GENERATION (Gemini)
# ══════════════════════════════════════════════════════════════════════════════

TOPICS = [
    {"topic": "World Cup 2026 group stage shocking statistics", "style": "factual"},
    {"topic": "fastest goals in World Cup 2026 history", "style": "factual"},
    {"topic": "greatest World Cup comebacks of all time", "style": "factual"},
    {"topic": "most dominant World Cup 2026 team performances", "style": "factual"},
    {"topic": "youngest players making World Cup 2026 history", "style": "factual"},
    {"topic": "World Cup 2026 goalkeeper heroics and impossible saves", "style": "factual"},
    {"topic": "tactical masterclasses at World Cup 2026", "style": "factual"},
    {"topic": "World Cup 2026 records that may never be broken", "style": "factual"},
    {"topic": "underdog teams shocking favorites at World Cup 2026", "style": "factual"},
    {"topic": "hat-tricks and multi-goal performances at World Cup 2026", "style": "factual"},
    {"topic": "VAR controversies that changed World Cup 2026 matches", "style": "factual"},
    {"topic": "defending champions performance at World Cup 2026", "style": "factual"},
    {"topic": "greatest NBA basketball buzzer-beaters of all time", "style": "factual"},
    {"topic": "cricket's most dramatic last-over finishes", "style": "factual"},
    {"topic": "tennis Grand Slam comebacks from match point down", "style": "factual"},
    {"topic": "Olympic sprinting records that shocked the world", "style": "factual"},
    {"topic": "boxing's most legendary knockouts", "style": "factual"},
    {"topic": "gymnastics routines that scored perfect 10s", "style": "factual"},
    {"topic": "Formula 1's most audacious overtakes", "style": "factual"},
    {"topic": "swimming world records broken by the slimmest margins", "style": "factual"},
    {"topic": "rugby's most bone-crunching defensive stands", "style": "factual"},
    {"topic": "volleyball's most improbable comebacks", "style": "factual"},
    # Evergreen "banned/illegal/rules nobody knows" -- validated against real
    # competitive view-count data in this niche (multiple unrelated channels
    # getting 1M-48M+ views on this exact angle). Doesn't depend on any live
    # tournament being in season, so it survives World Cup 2026 ending.
    {"topic": "equipment and accessories banned in professional football", "style": "rules_shock"},
    {"topic": "the weirdest football rule casual fans have never heard of", "style": "rules_shock"},
    {"topic": "actions that get a football player sent off that fans think are legal", "style": "rules_shock"},
    {"topic": "basketball rules that sound made up but are real", "style": "rules_shock"},
    {"topic": "tennis rules that can get a player disqualified mid-match", "style": "rules_shock"},
    {"topic": "cricket dismissals almost nobody knows exist", "style": "rules_shock"},
    {"topic": "boxing fouls that end a fight instantly", "style": "rules_shock"},
    {"topic": "Formula 1 technical rules that got a car disqualified after winning", "style": "rules_shock"},
    {"topic": "Olympic equipment regulations that shocked athletes", "style": "rules_shock"},
    {"topic": "rugby laws that look illegal in every other sport", "style": "rules_shock"},
    {"topic": "swimming rules about what you cannot wear or do at the start", "style": "rules_shock"},
    {"topic": "golf rules that have disqualified players over the tiniest technicality", "style": "rules_shock"},
    {"topic": "the strangest rule change in football history and why it happened", "style": "rules_shock"},
    {"topic": "jewelry and clothing rules referees actually enforce in professional sports", "style": "rules_shock"},
    {"topic": "celebrations that are technically against the rules in football", "style": "rules_shock"},
    # Object/equipment history
    {"topic": "how the tennis ball evolved from wool-stuffed leather to pressurized rubber fuzz", "style": "factual"},
    {"topic": "the soccer ball's evolution from stitched leather panels to thermally-bonded panels", "style": "factual"},
    {"topic": "why baseballs are stitched with exactly 108 red stitches", "style": "factual"},
    {"topic": "how the cricket bat's shape evolved over 150 years", "style": "factual"},
    {"topic": "how the basketball's bounce was engineered for the perfect dribble", "style": "factual"},
    # Future/speculative
    {"topic": "smart balls with embedded sensors already used in football and tennis officiating", "style": "speculative"},
    {"topic": "what sports equipment could look like in 2050", "style": "speculative"},
    {"topic": "AI referees replacing human judgment calls in sports", "style": "speculative"},
    # Satire/comedy
    {"topic": "a day in the life of a football -- deadpan complaints about being kicked around", "style": "satire"},
    {"topic": "the tennis ball's existential crisis -- served, smashed, forgotten in a bag", "style": "satire"},
    {"topic": "referee decision history reimagined as an absurd courtroom drama", "style": "satire"},
    {"topic": "things only a golf ball has seen -- mockumentary tone", "style": "satire"},
]

STYLE_GUIDANCE = {
    "factual": "Tone: professional sports analyst, NOT hype/clickbait. Ground everything in real, "
               "verifiable facts, stats, and history.",
    "rules_shock": "Tone: still a credible analyst grounded in the REAL rule/regulation (verifiable, "
                   "not an urban legend) -- but lean into genuine surprise: most fans assume the "
                   "opposite is true, so the hook should land as a real 'wait, what?' moment. Name "
                   "the specific rule, the real penalty/consequence, and (if known) a real instance "
                   "it was enforced. This is the highest-performing content angle in this niche per "
                   "real competitive view data -- don't undersell it with a flat delivery.",
    "speculative": "Tone: thoughtful sports-tech futurist speculating on where equipment, officiating, "
                   "or the sport itself is headed -- grounded in real current trends (VAR, Hawk-Eye, "
                   "wearable sensors, AI) before extrapolating forward. NOT hype/clickbait.",
    "satire": "Tone: deadpan comedic monologue, often narrated from the equipment/object's own point "
              "of view, or framed as an absurd mockumentary/courtroom drama. Should be genuinely funny "
              "and dry, self-aware -- think a sports-desk version of The Onion, not slapstick.",
}

def _topic_subject_key(topic: str) -> str:
    """Crude subject fingerprint (first capitalized word/name) for the
    repetition guard -- good enough to catch 'same player/team again'."""
    for word in topic.split():
        w = word.strip(".,!?'\"")
        if w[:1].isupper() and w.lower() not in ("the", "a", "an", "in", "at", "on"):
            return w.lower()
    return topic.strip().lower()[:24]


def get_current_sports_topic(recent_subjects: list) -> str:
    """Ask Gemini (grounded with live Google Search) for one specific, real,
    current sports storyline -- so content rides real search traffic instead
    of being generic/historical. Returns '' if unavailable or too similar to
    a recently-used subject (repetition guard)."""
    if not gemini_client:
        return ""
    try:
        from google.genai import types
        avoid = f" Avoid these already-covered subjects: {', '.join(recent_subjects)}." if recent_subjects else ""
        resp = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=(
                "In one sentence, name one specific, real, notable sports moment, result, or "
                "storyline from the last 7 days (any sport worldwide). Be concrete: names, "
                "numbers, what actually happened. No commentary, just the fact." + avoid
            ),
            config={"tools": [types.Tool(google_search=types.GoogleSearch())]},
        )
        topic = resp.text.strip()
        if _topic_subject_key(topic) in recent_subjects:
            return ""
        return topic
    except Exception as e:
        log(f"Current-events topic fetch failed: {e} -- using static topic list")
        return ""


def generate_script(state: dict) -> dict:
    """Use Gemini to generate a professional script. Falls back to static."""
    recent_subjects = state.get("recent_subjects", [])

    topic = get_current_sports_topic(recent_subjects)
    style = "factual"
    if topic:
        log(f"Current-events topic: {topic[:70]}")
    else:
        # Fall back to the static, already-exhausted-tracked topic list
        used = set(state.get("used_topics", []))
        available = [i for i in range(len(TOPICS)) if i not in used]
        if not available:
            used, available = set(), list(range(len(TOPICS)))
        topic_idx = random.choice(available)
        used.add(topic_idx)
        state["used_topics"] = list(used)
        entry = TOPICS[topic_idx]
        topic = entry["topic"]
        style = entry.get("style", "factual")

    subject_key = _topic_subject_key(topic)
    recent_subjects = ([subject_key] + recent_subjects)[:5]
    state["recent_subjects"] = recent_subjects

    prompt = f"""You are a professional sports content writer creating a YouTube Short for the channel "{CHANNEL}".
Topic: {topic}

Generate the script. {STYLE_GUIDANCE.get(style, STYLE_GUIDANCE["factual"])}
Visuals for this video are real, licensed stock-footage clips found via keyword search (Pixabay/
Pexels), NOT AI-generated -- so scene descriptions must be short stock-footage SEARCH QUERIES
(3-6 words, no commas, no full sentences), the way you'd actually type into a stock-video search
box, not a descriptive prompt for an image/video generator.

This is a SHORT-FORM video (target 20-25 seconds total) structured in 3 acts, matching how the
YouTube Shorts algorithm actually rewards retention:
- ACT 1 / Hook (0-3s): the single most surprising fact, stated immediately. No windup.
- ACT 2 / Body (up to ~15s): a second, escalating detail or twist -- not just more of the same
  stat, an actual turn ("but here's the part nobody talks about...").
- ACT 3 / CTA + loop (final few seconds): a concrete, specific, easy-to-answer-in-one-line
  question tied directly to the fact just stated (not a generic "what do you think?"), AND the
  closing line should echo or call back to the hook's opening words or image -- so the ending
  flows back into the beginning (loop-friendly, drives replays).

Rules:
- Hook: Start with a specific stat or fact, but withhold WHY it matters or the full story -- create
  an open question the body then resolves (the curiosity gap: the brain treats an unresolved
  question as something it needs to close, which is what actually drives someone to keep watching
  instead of scrolling past). E.g. "2-1. England's narrowest win since 1990" states the score
  without yet saying why that's notable -- the body pays it off. Don't front-load the full
  explanation in the hook. NO filler ("Ever wondered", "Did you know", etc.). Keep it under 12 words if possible.
- Body: 2-3 sentences max, tighter than before. Include exactly one short first-person editorial beat — a genuine opinion or reaction (e.g. "What's wild is...", "The number that gets me is...").
- CTA: A specific, concrete question directly about the fact just stated (e.g. "Was that offside or not — yes or no?" not "What do you think?"). Must be answerable in one word or short phrase to lower the barrier to commenting. End on a phrase/image that echoes the hook.
- Title: This is the ONE piece of marketing copy in the whole video -- it is never spoken, so it
  can (and per real competitive data on this niche, should) be punchier and more emotion-coded than
  the narration. Use ONE relevant emoji placed for impact (start or end), and shock/curiosity
  framing: "BANNED", "ILLEGAL", numbers, "nobody talks about", callouts in caps for the single most
  surprising word. E.g. "3 Things BANNED in Football ⚽😱" or "The Rule Nobody Knew Existed 😳" --
  NOT a flat restatement of the hook. This does not change the narration's tone -- hook/body/cta
  stay grounded and credible either way, only the title is the attention-grabbing layer.
- Queries: 3 short stock-footage search queries (3-6 words each, no commas/sentences) -- this is
  the single most important rule for these: DERIVE EACH QUERY FROM WHAT THAT SPECIFIC HOOK/BODY/CTA
  SENTENCE ACTUALLY SAYS, not a generic sports-highlight template. Read the actual sentence and ask
  "what is the SPORT and the EMOTIONAL OUTCOME of this specific moment" before picking words --
  do NOT default to "sprint / diving save / team celebrating" for every video regardless of story.
  A few worked examples of matching the query to the ACTUAL content:
    * Hook is about a team being ELIMINATED/losing/upset -> query should read as dejection/shock
      ("dejected player pitch", "stunned stadium reaction"), NOT a celebration shot.
    * Hook is about a RECORD or WIN -> celebration/triumph imagery is correct there.
    * Hook is about a specific RULE or technical detail (e.g. goalkeepers handling throw-ins) ->
      query should show that exact action described, not an unrelated generic highlight
      ("goalkeeper catching ball" for a handling-rule story, not "team celebrating trophy").
    * Hook is about a controversy/foul/card -> query should show the specific incident type
      ("referee showing red card", "VAR review screen"), not a generic crowd shot.
  Only echo the 1st (hook) query's subject/action in the 3rd (CTA) query if that echo is actually
  true to both moments -- never force a loop that misrepresents what body/cta are really about.
  CRITICAL: never put a real person's name in a query — describe them generically instead (kit
  color, sport, build, action), e.g. "tennis player white kit" not "Muchova". Real names belong
  only in hook/body/cta/title; the stock-footage search must never be asked to find a named real
  person's actual likeness.

Return ONLY a JSON object:
{{
  "hook": "Opening line with a specific stat (short, punchy, 2-3s to read)",
  "body": "Escalating detail/twist, tight (10-12s to read)",
  "cta": "Concrete one-word-answerable question that echoes the hook",
  "title": "Punchy, emoji-coded, shock/curiosity-framed title under 80 chars with #shorts #sports",
  "tags": ["sports", "shorts", "facts"],
  "queries": ["short search query 1", "short search query 2 (twist)", "short search query 3 (echoes query 1)"]
}}"""

    if gemini_client:
        try:
            response = gemini_client.models.generate_content(
                model='gemini-2.5-flash', contents=prompt,
                config={'response_mime_type': 'application/json'}
            )
            raw = response.text.strip()
            if raw.startswith("```json"): raw = raw[7:]
            if raw.endswith("```"): raw = raw[:-3]
            script = json.loads(raw.strip())

            # Ensure required tags
            title = script.get("title", "")
            if "#shorts" not in title.lower(): title += " #shorts"
            script["title"] = title[:100]
            script["tags"] = list(set(script.get("tags", []) + ["sports", "shorts", "facts"]))
            log(f"Script: {script['hook'][:60]}")
            return script
        except Exception as e:
            log(f"Gemini failed ({e}) -- using fallback")

    # Static fallback
    return {
        "hook": "Argentina have won every World Cup after defending - a 100% record.",
        "body": "At World Cup 2026, Argentina scored 9 goals and conceded just 1 in the group stage. No defending champion has matched this in over 60 years. Their midfield completed 94% passing accuracy across 3 matches.",
        "cta": "Can Argentina defend the title? Drop your prediction below.",
        "title": "Argentina's World Cup 2026 Stats Are HISTORIC #shorts #sports",
        "tags": ["sports", "shorts", "facts", "worldcup2026"],
        "queries": [
            "footballer sprinting past defenders",
            "goalkeeper diving save",
            "team celebrating trophy",
        ],
    }


def translate_script_to_hindi(script: dict) -> dict:
    """Translate hook/body/cta/title into natural, colloquial *spoken* Hindi
    (Devanagari) for the Indian-audience version of this video. `queries`
    (AI/stock visual-search prompts) are left in English -- they're never
    narrated or shown on screen, so translating them would only make the
    footage/animation search worse. Marks the result script['lang'] = 'hi'
    so downstream caption/font/sign-off code picks the Hindi path."""
    if not gemini_client:
        log("Hindi translation: no Gemini client configured -- returning script untranslated")
        return script

    prompt = f"""Translate this YouTube Shorts script into natural, colloquial SPOKEN Hindi
(Devanagari script), the way a young Indian sports creator would actually say it out loud on
camera -- not formal/literary Hindi, not a stiff word-for-word translation. Keep proper nouns
(player/team/tournament names), scores, and numerals exactly as they are (numerals stay in
standard Arabic numeral form, e.g. "2-1", not Devanagari numerals). It's fine to keep a common
English sports/tech word as-is if that's how Indian viewers actually say it (e.g. "goal",
"match", "record") -- natural Hinglish sprinkling is more authentic than forcing pure Hindi.
Keep the same structure, meaning, and energy as the original -- hook stays a punchy open
question, cta stays a concrete one-word-answerable question.

Original (English):
hook: {script.get('hook', '')}
body: {script.get('body', '')}
cta: {script.get('cta', '')}
title: {script.get('title', '')}

Return ONLY a JSON object with the translated fields:
{{"hook": "...", "body": "...", "cta": "...", "title": "..."}}"""

    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash', contents=prompt,
            config={'response_mime_type': 'application/json'}
        )
        raw = response.text.strip()
        if raw.startswith("```json"): raw = raw[7:]
        if raw.endswith("```"): raw = raw[:-3]
        translated = json.loads(raw.strip())

        hi_script = dict(script)
        hi_script["hook"] = translated.get("hook", script.get("hook", ""))
        hi_script["body"] = translated.get("body", script.get("body", ""))
        hi_script["cta"] = translated.get("cta", script.get("cta", ""))
        title = translated.get("title", script.get("title", ""))
        if "#shorts" not in title.lower():
            title += " #shorts"
        hi_script["title"] = title[:100]
        hi_script["lang"] = "hi"
        # queries (visual search/animation prompts) stay in English on purpose.
        log(f"Hindi script: {hi_script['hook'][:60]}")
        return hi_script
    except Exception as e:
        log(f"Hindi translation failed ({e}) -- falling back to English script")
        return script


# ══════════════════════════════════════════════════════════════════════════════
#  2. DOWNLOAD CLIPS (Pexels > Pixabay) -- delegates to visual_shorts_creator's
#     fetcher, which has two fixes this module's own copy never got: tag-
#     relevance filtering (Pixabay's own relevance ranking regularly surfaces
#     off-topic clips) and cross-VIDEO clip-reuse tracking (output/used_stock_
#     clips.json), not just within-one-video dedup. Real, specific, tag-matched
#     footage reads as recognizable action in the first frame -- which is what
#     actually earns the 2-second attention window a Short lives or dies on --
#     where AnimateDiff's local-SD1.5 output was rated unusable for that job.
# ══════════════════════════════════════════════════════════════════════════════

def download_clips(script: dict) -> list:
    """Download 3 topic-matched real stock clips. See module docstring above --
    this delegates to visual_shorts_creator.download_clips() rather than
    duplicating its tag-relevance filter and cross-video dedup tracking."""
    import visual_shorts_creator as vsc
    return vsc.download_clips(script)


# ══════════════════════════════════════════════════════════════════════════════
#  2b. ANIME CLIP GENERATION (AnimateDiff, runs in venv_animate via subprocess)
# ══════════════════════════════════════════════════════════════════════════════

ANIME_VENV_PYTHON = os.path.join(os.path.dirname(__file__), "venv_animate", "Scripts", "python.exe")
ANIME_GENERATOR_SCRIPT = os.path.join(os.path.dirname(__file__), "anime_video_generator.py")
ANIME_CLIP_SECONDS = 20.0  # boomerang-looped from the same generated frames (free, no extra GPU time) --
                           # must safely exceed the longest possible segment (body can run ~15s)


def generate_anime_clips(script: dict) -> list:
    """Generate original anime-style AI video clips for each scene description
    in script['queries'], via AnimateDiff running in the isolated venv_animate
    environment. Replaces download_clips() as the footage source."""
    import subprocess
    import tempfile

    scenes = script.get("queries") or ["athlete in a dramatic sports action moment"]
    clip_dir = os.path.join(config.OUTPUT_DIR, "anime_clips")
    os.makedirs(clip_dir, exist_ok=True)

    jobs = [
        {"prompt": scene, "out_path": os.path.join(clip_dir, f"anime_{int(time.time())}_{i}.mp4"),
         "seconds": ANIME_CLIP_SECONDS}
        for i, scene in enumerate(scenes)
    ]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(jobs, f)
        jobs_path = f.name

    log(f"Generating {len(jobs)} anime clip(s) via AnimateDiff (this can take several minutes)...")
    proc = subprocess.run(
        [ANIME_VENV_PYTHON, ANIME_GENERATOR_SCRIPT, jobs_path],
        capture_output=True, text=True, timeout=1800,
    )
    if proc.stderr:
        for line in proc.stderr.strip().splitlines()[-20:]:
            log(f"  [anime_video_generator] {line}")
    if proc.returncode != 0:
        raise Exception(f"anime_video_generator failed (exit {proc.returncode}): {proc.stderr[-500:]}")

    results = json.loads(proc.stdout.strip().splitlines()[-1])
    paths = [r["out_path"] for r in results if r["ok"]]
    if not paths:
        raise Exception(f"All anime clip generations failed: {results}")
    log(f"Generated {len(paths)}/{len(jobs)} anime clip(s)")
    return paths


# ══════════════════════════════════════════════════════════════════════════════
#  3. VOICEOVER (Your cloned voice (OpenVoice) > ElevenLabs > Kokoro local > Edge-TTS)
# ══════════════════════════════════════════════════════════════════════════════

# Kokoro model paths (downloaded once, reused)
_KOKORO_MODEL  = os.path.join(os.path.dirname(__file__), "kokoro-v1.0.onnx")
_KOKORO_VOICES = os.path.join(os.path.dirname(__file__), "voices.bin")
_kokoro_instance = None

def _get_kokoro():
    global _kokoro_instance
    if _kokoro_instance is None:
        from kokoro_onnx import Kokoro
        _kokoro_instance = Kokoro(_KOKORO_MODEL, _KOKORO_VOICES)
    return _kokoro_instance

VOICE_CLONE_VENV_PYTHON = os.path.join(os.path.dirname(__file__), "venv_openvoice", "Scripts", "python.exe")
VOICE_CLONE_SCRIPT = os.path.join(os.path.dirname(__file__), "voice_clone_generator.py")
VOICE_CLONE_REFERENCE = os.path.join(os.path.dirname(__file__), "Recording (2).wav")


def _generate_cloned_voice(text: str, out_wav: str) -> str:
    """Your own voice (OpenVoice tone-color conversion), via venv_openvoice subprocess."""
    import subprocess, tempfile

    if not (os.path.exists(VOICE_CLONE_VENV_PYTHON) and os.path.exists(VOICE_CLONE_REFERENCE)):
        raise Exception("voice clone env or reference recording not found")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump({"text": text, "out_path": out_wav}, f)
        job_path = f.name

    proc = subprocess.run(
        [VOICE_CLONE_VENV_PYTHON, VOICE_CLONE_SCRIPT, job_path],
        capture_output=True, text=True, timeout=600,
    )
    if proc.stderr:
        for line in proc.stderr.strip().splitlines()[-10:]:
            log(f"  [voice_clone_generator] {line}")
    result = json.loads(proc.stdout.strip().splitlines()[-1])
    if not result.get("ok"):
        raise Exception(result.get("error", "unknown voice clone error"))
    return out_wav


WHISPER_TIMING_SCRIPT = os.path.join(os.path.dirname(__file__), "whisper_timing.py")


def get_word_timestamps(vo_path: str) -> list:
    """Real word-level timestamps for the generated voiceover (via faster-whisper
    in venv_openvoice), so captions/segment cuts can sync to actual speech
    instead of a guessed constant rate. Cached alongside the audio file."""
    import subprocess

    cache_path = vo_path + ".words.json"
    if os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as f:
            return json.load(f)

    try:
        proc = subprocess.run(
            [VOICE_CLONE_VENV_PYTHON, WHISPER_TIMING_SCRIPT, vo_path],
            capture_output=True, text=True, timeout=300,
        )
        words = json.loads(proc.stdout.strip().splitlines()[-1])
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(words, f)
        return words
    except Exception as e:
        log(f"Word-timestamp transcription failed: {e} — falling back to estimated timing")
        return []


def _with_persona_signoff(script: dict) -> dict:
    """Append the persona's consistent sign-off to the CTA if it's not
    already there, so every video ends with the same recurring identity
    line instead of a different one-off closer each time. Language-aware:
    script['lang'] == 'hi' gets the Hindi sign-off, so a Hindi narration
    never gets an English phrase stitched onto the end of it."""
    lang = script.get("lang", "en")
    signoff_template = (getattr(config, "PERSONA_SIGNOFF_HI", "") if lang == "hi"
                         else getattr(config, "PERSONA_SIGNOFF", ""))
    signoff = signoff_template.format(name=getattr(config, "PERSONA_NAME", ""))
    if not signoff or signoff.lower() in script.get("cta", "").lower():
        return script
    s = dict(script)
    s["cta"] = f"{s.get('cta', '').rstrip()} {signoff}"
    return s



# Target loudness for ALL narration, whichever engine produced it.
# Measured 2026-09-11: the cloned voice came out at rms 0.0248 / peak 0.2405
# while ElevenLabs was rms 0.0460 / peak 0.4420 -- roughly half the level,
# which is why the cloned takes sounded thin and far away next to music.
# Normalising every voice to the same target means the narration is clear
# and consistently loud no matter which engine ran, instead of the viewer
# hearing a quieter video whenever a fallback fired.
_VOICE_TARGET_PEAK = 0.89
_VOICE_TARGET_RMS = 0.050


def normalize_voice(path: str) -> str:
    """Make narration clear and loud: strip DC offset, gently compress the
    peaks so quiet words come up, then normalise. Writes back in place."""
    try:
        import numpy as np
        import soundfile as sf
        from moviepy import AudioFileClip

        clip = AudioFileClip(path)
        sr = 44100
        arr = clip.to_soundarray(fps=sr)
        clip.close()
        if arr.ndim > 1:
            arr = arr.mean(axis=1)
        arr = arr.astype("float64")

        arr = arr - np.mean(arr)                       # DC offset
        peak = float(np.max(np.abs(arr)))
        if peak <= 1e-6:
            log("  normalize_voice: silent track, skipped")
            return path

        arr = arr / peak                               # provisional normalise
        # Soft knee above 0.5 pulls loud peaks down so the overall level can
        # rise without clipping -- this is what makes speech sound "present"
        # rather than simply louder.
        knee = 0.62
        over = np.abs(arr) > knee
        arr[over] = np.sign(arr[over]) * (knee + (np.abs(arr[over]) - knee) * 0.60)

        rms = float(np.sqrt(np.mean(arr ** 2)))
        if rms > 1e-6:
            arr = arr * min(_VOICE_TARGET_RMS / rms, 1.0 / (np.max(np.abs(arr)) + 1e-9))

        peak2 = float(np.max(np.abs(arr)))
        if peak2 > 1e-6:
            arr = arr * (_VOICE_TARGET_PEAK / peak2)

        # Peak-normalising can push the average level past target, which is
        # what made a first pass land 3.8x louder than the source and ~2x
        # ElevenLabs. Pull back if the average overshoots.
        rms2 = float(np.sqrt(np.mean(arr ** 2)))
        if rms2 > _VOICE_TARGET_RMS * 1.35:
            arr = arr * ((_VOICE_TARGET_RMS * 1.35) / rms2)

        arr = np.clip(arr, -1.0, 1.0)
        sf.write(path, arr.astype("float32"), sr)
        log(f"  normalized voice -> rms {float(np.sqrt(np.mean(arr**2))):.4f} "
            f"peak {float(np.max(np.abs(arr))):.3f}")
    except Exception as e:
        log(f"  normalize_voice skipped ({e})")
    return path


def generate_voiceover(script: dict) -> str:
    """Generate voice narration. ElevenLabs (George -- warm storyteller) >
    cloned voice (OpenVoice) > Kokoro local > Edge-TTS.

    Priority changed 2026-08-29 per direct feedback ("sound should be more
    clear and clean pronunciation") -- the OpenVoice clone was succeeding
    every time, so ElevenLabs (professionally regarded for clear
    pronunciation) never actually got used despite being configured.
    George (JBFqnCBsd6RMkjVDRZzb, not "Rachel" -- that .env comment was
    stale) is a real, clear, warm British storyteller voice, a good fit
    for facts content. Cloned voice stays as the fallback."""
    script = _with_persona_signoff(script)
    text = f"{script['hook']}. {script['body']} {script['cta']}"
    os.makedirs(config.AUDIO_DIR, exist_ok=True)
    out_wav = os.path.join(config.AUDIO_DIR, f"pro_vo_{int(time.time())}.wav")
    out_mp3 = out_wav.replace(".wav", ".mp3")

    # 1. ElevenLabs (clear stock voice -- see docstring for why this is first now)
    out = out_mp3
    if config.ELEVENLABS_API_KEY:
        log(f"ElevenLabs TTS: {len(text)} chars...")
        # Retry before giving up. Reproduced live 2026-09-11: two builds in a
        # row fell through to the cloned voice on a single 401, yet the exact
        # same request returned 200 moments later from the same key -- i.e. a
        # transient concurrency/rate limit, not a bad key. Treating one 401 as
        # final silently downgraded the narration to a more robotic voice,
        # which is the one quality bar the channel owner has repeatedly set
        # ("sound should be more clear and clean pronunciation"). Fail loudly
        # and retry rather than quietly shipping the worse voice.
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{config.ELEVENLABS_VOICE_ID}"
        for attempt in range(1, 4):
            try:
                r = requests.post(url,
                    json={"text": text, "model_id": "eleven_turbo_v2_5",
                          "voice_settings": {"stability": 0.50, "similarity_boost": 0.80}},
                    headers={"xi-api-key": config.ELEVENLABS_API_KEY,
                             "Content-Type": "application/json"}, timeout=90)
                if r.status_code == 200:
                    with open(out, "wb") as f: f.write(r.content)
                    log(f"Voice saved (ElevenLabs): {out}")
                    return normalize_voice(out)
                body_txt = (r.text or "")[:300]
                # A 401 that says "exceeds your quota" is not transient --
                # measured 2026-09-11: "You have 15 credits remaining, while
                # 75 credits are required". Retrying an empty quota just
                # wastes 30s per video, so fail straight through to the
                # cloned voice instead.
                if "quota" in body_txt.lower() or "credits remaining" in body_txt.lower():
                    log(f"ElevenLabs quota exhausted — using cloned voice. {body_txt[:140]}")
                    break
                log(f"ElevenLabs {r.status_code} (attempt {attempt}/3)")
                if r.status_code in (401, 429, 500, 502, 503) and attempt < 3:
                    time.sleep(5 * attempt)
                    continue
                break
            except Exception as e:
                log(f"ElevenLabs error (attempt {attempt}/3): {e}")
                if attempt < 3:
                    time.sleep(5 * attempt)
        log("ElevenLabs unavailable after 3 attempts — falling back to cloned voice")

    # 2. Your cloned voice (OpenVoice, from Recording (2).wav)
    try:
        log("Cloned voice (OpenVoice)...")
        _generate_cloned_voice(text, out_wav)
        log(f"Voice saved (cloned): {out_wav}")
        return normalize_voice(out_wav)
    except Exception as e:
        log(f"Cloned voice failed: {e} — falling back to Kokoro")

    # 3. Kokoro local TTS — deep male narrator, runs in ~5s, zero internet
    if os.path.exists(_KOKORO_MODEL) and os.path.exists(_KOKORO_VOICES):
        log("Kokoro local TTS (am_michael)...")
        try:
            import soundfile as sf
            import subprocess
            import shutil
            import imageio_ffmpeg
            k = _get_kokoro()
            samples, sr = k.create(text, voice="am_michael", speed=0.95, lang="en-us")
            sf.write(out_wav, samples, sr)
            # Convert WAV -> MP3 via ffmpeg for consistency
            ffmpeg = shutil.which("ffmpeg") or imageio_ffmpeg.get_ffmpeg_exe()
            if os.path.exists(ffmpeg):
                subprocess.run([ffmpeg, "-y", "-i", out_wav, "-b:a", "192k", out_mp3],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                os.remove(out_wav)
                log(f"Voice saved (Kokoro): {out_mp3}")
                return out_mp3
            else:
                log(f"Voice saved (Kokoro WAV): {out_wav}")
                return out_wav
        except Exception as e:
            log(f"Kokoro failed: {e} — trying Edge-TTS")

    # 4. Edge-TTS (always works, natural Microsoft voice)
    log("Using Edge-TTS (Christopher Neural)...")
    try:
        import asyncio, edge_tts
        async def run():
            c = edge_tts.Communicate(text, "en-US-ChristopherNeural")
            await c.save(out)
        asyncio.run(run())
        log(f"Voice saved (Edge-TTS): {out}")
        return out
    except Exception as e:
        log(f"Edge-TTS failed: {e}")
        raise Exception("All voice generation methods failed")


def generate_hindi_voiceover(script: dict) -> str:
    """Hindi narration via Edge-TTS (hi-IN-MadhurNeural) -- a fast, natural,
    ready-made Hindi voice for today's video. The cloned-voice path (OpenVoice)
    is skipped here: its reference recording is English and the venv_openvoice
    base TTS isn't verified to handle Hindi text, so it's not a safe default
    yet. Swap this out once a Hindi reference recording is available --
    _generate_cloned_voice already takes arbitrary text/out_wav, so cloning
    a Hindi voice later is a reference-file swap, not a rewrite."""
    script = _with_persona_signoff(script)
    text = f"{script['hook']}. {script['body']} {script['cta']}"
    os.makedirs(config.AUDIO_DIR, exist_ok=True)
    out_mp3 = os.path.join(config.AUDIO_DIR, f"pro_vo_hi_{int(time.time())}.mp3")

    import asyncio, edge_tts
    for voice in ("hi-IN-MadhurNeural", "hi-IN-SwaraNeural"):
        try:
            log(f"Hindi Edge-TTS ({voice})...")
            async def run(v=voice):
                c = edge_tts.Communicate(text, v)
                await c.save(out_mp3)
            asyncio.run(run())
            log(f"Voice saved (Hindi Edge-TTS {voice}): {out_mp3}")
            return out_mp3
        except Exception as e:
            log(f"Hindi Edge-TTS ({voice}) failed: {e}")

    raise Exception("All Hindi voice generation methods failed")



# ══════════════════════════════════════════════════════════════════════════════
#  4. MUSIC (Synthesized > Download fallback)
# ══════════════════════════════════════════════════════════════════════════════

_MUSIC_STYLES = {"energetic", "emotional", "analytical", "funk"}


def classify_music_style(script: dict) -> str:
    """Pick the background-music mood that actually matches the story,
    instead of always using the same punchy sports beat regardless of
    tone (direct feedback 2026-08-22: a heavy defeat, a 91-year drought,
    and a last-minute promotion had all gotten identical music).
      energetic  -- triumph, a big win, an exciting record
      emotional  -- a loss, heartbreak, a long wait, something bittersweet
      analytical -- a historical/tactical fact, no strong emotional charge
      funk       -- lighthearted, fun, quirky
    Falls back to "energetic" (the previous universal default) if Gemini
    is unavailable or returns something unrecognized."""
    if not gemini_client:
        return "energetic"
    full_text = " ".join(filter(None, [script.get("hook", ""), script.get("body", ""),
                                        script.get("cta", "")])).strip()
    if not full_text:
        return "energetic"
    try:
        prompt = (
            "Read this short-form video script and pick exactly ONE word "
            "for its background music mood, from this list only: "
            "energetic, emotional, analytical, funk. energetic = triumph, "
            "a big win, an exciting record. emotional = a loss, "
            "heartbreak, a long wait finally ending, something "
            "bittersweet. analytical = a historical or tactical fact "
            "with no strong emotional charge. funk = lighthearted, fun, "
            "quirky. Reply with ONLY that one word, nothing else.\n\n"
            f"{full_text}"
        )
        resp = gemini_client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        style = resp.text.strip().lower()
        if style in _MUSIC_STYLES:
            return style
        log(f"Music style classification returned unrecognized '{style}' -- defaulting to energetic")
    except Exception as e:
        log(f"Music style classification failed ({e}) -- defaulting to energetic")
    return "energetic"


def get_music(duration: float = 30, script: dict = None) -> str:
    """Get background music matching the script's actual tone (see
    classify_music_style). Synthesized original first, download fallback.
    `script` is optional for backward compatibility -- omitting it keeps
    the previous universal "energetic" behavior."""
    style = classify_music_style(script) if script else "energetic"
    try:
        import music_generator
        path = music_generator.get_original_music(style, audio_dir=config.AUDIO_DIR, duration=duration)
        if os.path.exists(path) and os.path.getsize(path) > 10_000:
            log(f"Music: {os.path.basename(path)} (original, {style} mood)")
            return path
    except Exception as e:
        log(f"Synth music failed ({e})")

    os.makedirs(config.AUDIO_DIR, exist_ok=True)
    for url in MUSIC_FALLBACK:
        name = f"music_{abs(hash(url)) % 99999}.mp3"
        path = os.path.join(config.AUDIO_DIR, name)
        if os.path.exists(path) and os.path.getsize(path) > 5000:
            return path
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            with open(path, "wb") as f: f.write(r.content)
            if os.path.getsize(path) > 5000:
                log(f"Music: {name} (download)")
                return path
        except: pass
    raise Exception("All music sources failed")


def _music_ducking_filter(vo_clip, duration: float, quiet: float = 0.06, gap: float = 0.20):
    """Per-time music volume: quiet (`quiet`) while the voiceover is
    actually speaking, louder (`gap`) during any real pause -- a beat of
    silence, a pure-visual moment with no narration. Previously music sat
    at one flat level (0.06) for the entire video regardless of whether
    anyone was talking. Falls back to the flat quiet level if the
    voiceover audio can't be analyzed for any reason.

    Returns an `fl`-style filter: fn(get_frame, t) -> frame."""
    try:
        sr = 22050
        vo_array = vo_clip.to_soundarray(fps=sr, nbytes=2)
        if vo_array.ndim > 1:
            vo_array = vo_array.mean(axis=1)
        window = max(1, int(sr * 0.15))  # 150ms smoothing
        kernel = np.ones(window) / window
        rms = np.sqrt(np.convolve(vo_array.astype(np.float64) ** 2, kernel, mode="same") + 1e-9)
        thresh = np.percentile(rms, 35)  # adaptive silence threshold
        n = len(rms)
    except Exception as e:
        log(f"Music ducking envelope unavailable ({e}) -- using flat quiet level")
        rms = None

    def envelope_at(t: float) -> float:
        if rms is None:
            return quiet
        idx = int(t * sr)
        if idx < 0 or idx >= n:
            return gap  # past the end of speech -- outro/gap
        return quiet if rms[idx] > thresh else gap

    def fn(gf, t):
        frame = gf(t)
        if isinstance(t, np.ndarray):
            vols = np.array([envelope_at(tt) for tt in t])
            return (frame.T * vols).T
        return frame * envelope_at(t)

    return fn


def make_athlete_photo_clip(image_path: str, out_path: str, duration: float = 8.0) -> str:
    """Turn a real, safely-licensed athlete photo into a short vertical
    video with a Ken Burns pan/zoom, so it can flow through the normal
    clip pipeline (prepare_segment expects a video file on disk, not a
    still image). Reuses visual_shorts_creator's existing zoom/pan
    effect rather than duplicating it."""
    from moviepy import ImageClip
    import visual_shorts_creator as vsc

    # Real downloaded photos often carry an EXIF orientation tag (phone/
    # camera photos rotated in software, not in the actual pixel data).
    # ImageClip/PIL's default loader ignores this, so the photo can come
    # out sideways in the final video even though it looks upright in
    # every normal viewer -- reproduced live 2026-08-29 on a real tennis
    # action photo. Apply the correction and save a normalized copy before
    # loading it as a clip.
    fixed_path = image_path.rsplit(".", 1)[0] + "_upright.jpg"
    with Image.open(image_path) as im:
        im = ImageOps.exif_transpose(im)
        im.convert("RGB").save(fixed_path, "JPEG", quality=95)
    image_path = fixed_path

    img_clip = ImageClip(image_path)
    # libx264 requires even width/height -- a real downloaded photo can be
    # any odd size (reproduced live 2026-08-25: a 563x751 photo crashed
    # ffmpeg with "width not divisible by 2"). Crop 1px off if needed.
    w, h = img_clip.size
    ew, eh = w - (w % 2), h - (h % 2)
    if (ew, eh) != (w, h):
        img_clip = _crop(img_clip, 0, 0, ew, eh)
    img_clip = _dur(img_clip, duration)
    animated = vsc.apply_camera_movement(img_clip, duration, index=0)
    animated = _dur(animated, duration)
    animated.write_videofile(
        out_path, fps=FPS, codec="libx264", audio=False,
        ffmpeg_params=["-pix_fmt", "yuv420p"], logger=None,
    )
    # Mark this as a real photograph so prepare_segment never mirrors it
    # (see the do_flip note there -- a flipped photo renders sponsor text
    # and badges backwards, which looks fake).
    try:
        with open(out_path + ".noflip", "w") as f:
            f.write("real photograph -- do not horizontally flip\n")
    except Exception:
        pass
    return out_path


def try_athlete_photo_hook(name: str) -> dict:
    """Try to get a real, safely-licensed photo of `name` (a named
    player/manager the script is actually about) and turn it into a
    short clip for the hook segment, instead of anonymous generic stock
    footage. Direct feedback 2026-08-25: viewers should see the actual
    named person's face, not random b-roll -- free stock libraries have
    no rights to real broadcast footage, but Wikimedia Commons hosts
    genuine photos of named athletes under licenses that permit this.

    Returns {"video_path", "attribution"} on success. Returns None to
    signal "fall back to generic stock footage for this segment" if no
    safely-licensed photo exists -- never raises, since a missing photo
    should never block the whole build."""
    import athlete_photos
    photo_dir = os.path.join(config.OUTPUT_DIR, "athlete_photos")
    result = athlete_photos.find_athlete_photo(name, photo_dir)
    if not result:
        log(f"No safely-licensed photo found for '{name}' -- using generic stock footage for the hook instead")
        return None

    video_dir = os.path.join(config.OUTPUT_DIR, "raw_clips")
    os.makedirs(video_dir, exist_ok=True)
    out_path = os.path.join(video_dir, f"photo_hook_{abs(hash(name)) % 99999}.mp4")
    try:
        make_athlete_photo_clip(result["path"], out_path, duration=8.0)
    except Exception as e:
        log(f"Failed to animate athlete photo for '{name}' ({e}) -- using generic stock footage instead")
        return None

    log(f"Using a real photo of {name} for the hook segment ({result['license']})")
    return {"video_path": out_path, "attribution": result["attribution"]}


# ══════════════════════════════════════════════════════════════════════════════
#  5. SEGMENT PREPARATION (visual variety + HD crop)
# ══════════════════════════════════════════════════════════════════════════════

def _motion_energy(frame: np.ndarray) -> float:
    """Same edge-density-as-motion-proxy heuristic as thumbnail_generator's
    frame scoring -- used here to pick which moment of a stock clip to open
    the HOOK segment on. A Short lives or dies on whether the first ~2s reads
    as recognizable action instead of a static establishing shot, so the
    clip's most visually dynamic window should be biased toward the front,
    not whatever the geometric center of the trim region happens to land on."""
    gray = Image.fromarray(frame).convert("L").resize((160, 284))
    edges = gray.filter(ImageFilter.FIND_EDGES)
    return float(np.array(edges, dtype=np.float32).std())


def prepare_segment(clip_path: str, seg_dur: float, idx: int, total: int,
                     region_start_frac: float = None, region_dur_frac: float = None,
                     apply_freeze: bool = False, prefer_dynamic_start: bool = False) -> VideoFileClip:
    """
    Load a clip (any source aspect ratio -- stock footage, or a legacy
    roughly-square AnimateDiff clip) and fit it into 1080x1920: scaled to fill
    the full width, then either center-cropped (if that already overshoots the
    target height) or letterboxed with a blurred, zoomed copy of the same frame
    filling the empty top/bottom bars -- never stretched/cropped raw.
    Uses a single PIL frame transform — avoids MoviePy resize / PIL.ANTIALIAS issues.
    Compatible with Pillow 10+.
    """
    src = VideoFileClip(clip_path, audio=False)

    # Random horizontal flip is a cheap way to vary reused generic stock
    # footage -- but it must NEVER touch a real photograph of a real
    # person. Reproduced live 2026-09-03: a real Wikimedia photo of
    # Gabriel Jesus rendered mirrored, so his Arsenal shirt read "setarimE
    # / RETTEB YLF" backwards. Mirrored sponsor text instantly reads as
    # fake/AI-slop, which is the exact impression this channel cannot
    # afford. make_athlete_photo_clip() drops a ".noflip" sidecar next to
    # every photo-derived clip; honour it here.
    do_flip = random.random() > 0.5
    if os.path.exists(clip_path + ".noflip"):
        do_flip = False
    sat      = random.uniform(1.05, 1.15)
    bri      = random.uniform(1.0, 1.04)
    con      = random.uniform(1.0, 1.08)
    RESAMPLE = Image.Resampling.LANCZOS   # Pillow 10+ compatible (no ANTIALIAS)
    FLIP     = Image.Transpose.FLIP_LEFT_RIGHT
    BG_DIV   = 4                          # letterbox blur works at 1/4 scale
    BG_W, BG_H = WIDTH // BG_DIV, HEIGHT // BG_DIV

    def transform(gf, t):
        frame = gf(t)
        img = Image.fromarray(frame)
        sw, sh = img.size

        # Foreground: scale to fill the full target WIDTH, preserving all content
        fg_h = max(1, round(sh * (WIDTH / sw)))
        fg = img.resize((WIDTH, fg_h), RESAMPLE)

        if fg_h >= HEIGHT:
            # Taller than the frame -- center-crop vertically (no letterbox needed)
            canvas = fg.crop((0, (fg_h - HEIGHT) // 2, WIDTH, (fg_h - HEIGHT) // 2 + HEIGHT))
        else:
            # Blurred, cover-scaled background fills the letterbox bars.
            #
            # Built at QUARTER resolution, then upscaled. A radius-25
            # Gaussian on a full 1080x1920 frame costs ~162ms and runs on
            # EVERY frame of every letterboxed clip -- measured 2026-09-12
            # as the single most expensive step in prepare_segment. Blurring
            # a 270x480 copy at radius 6.25 (the same blur relative to image
            # size) and scaling it back up is ~4.4x cheaper and visually
            # indistinguishable: the output is a heavy smear darkened to
            # 0.55, so the detail a full-res blur preserves is destroyed by
            # the blur itself. Bilinear is used deliberately -- Lanczos
            # sharpening has nothing to sharpen here and costs more.
            bg_scale = max(BG_W / sw, BG_H / sh)
            bg_w, bg_h = max(1, round(sw * bg_scale)), max(1, round(sh * bg_scale))
            bg = img.resize((bg_w, bg_h), Image.Resampling.BILINEAR)
            bg = bg.crop(((bg_w - BG_W) // 2, (bg_h - BG_H) // 2,
                          (bg_w - BG_W) // 2 + BG_W, (bg_h - BG_H) // 2 + BG_H))
            bg = bg.filter(ImageFilter.GaussianBlur(radius=25 / BG_DIV))
            bg = ImageEnhance.Brightness(bg).enhance(0.55)
            bg = bg.resize((WIDTH, HEIGHT), Image.Resampling.BILINEAR)

            canvas = bg
            canvas.paste(fg, (0, (HEIGHT - fg_h) // 2))

        if do_flip:
            canvas = canvas.transpose(FLIP)
        # Each ImageEnhance pass is a full-frame op (~30-47ms at 1080x1920).
        # bri and con are drawn from ranges that start at exactly 1.0, so a
        # good fraction of clips pay for a no-op. Skip anything within 1%
        # of identity -- below that the shift is not visible anyway.
        canvas = ImageEnhance.Color(canvas).enhance(sat)
        if abs(bri - 1.0) > 0.01:
            canvas = ImageEnhance.Brightness(canvas).enhance(bri)
        if abs(con - 1.0) > 0.01:
            canvas = ImageEnhance.Contrast(canvas).enhance(con)
        return np.array(canvas)

    # Trim a section from this segment's region of the clip. By default the
    # source clip is divided into `total` EQUAL regions -- correct when the
    # segments are meant to be equal-length. When the caller instead knows
    # the real (unequal) proportion this segment should occupy of a single
    # continuous source clip (region_start_frac/region_dur_frac), use that
    # instead so e.g. a short hook doesn't get the same slice size as a much
    # longer body.
    clip_dur = src.duration
    if region_start_frac is not None and region_dur_frac is not None:
        region    = clip_dur * region_dur_frac
        reg_start = clip_dur * region_start_frac
    else:
        region    = clip_dur / total
        reg_start = idx * region
    need      = seg_dur * 1.1
    actual    = min(need, region - 0.1, clip_dur - 0.2)
    actual    = max(actual, 0.5)

    slack = region - actual
    if prefer_dynamic_start and slack > 1.0:
        # Probe a handful of candidate windows (on the RAW clip, before the
        # letterbox/color-grade transform below -- cheap decode-only frame
        # reads) and open on whichever is most visually dynamic, instead of
        # blindly trimming from the region's geometric center. This is what
        # actually earns the first ~2s of attention a Short lives or dies on.
        n_candidates = min(5, max(2, int(slack)))
        candidate_starts = [reg_start + slack * (i / (n_candidates - 1)) for i in range(n_candidates)]
        best_start, best_energy = candidate_starts[0], -1.0
        for cand in candidate_starts:
            probe_t = max(0.0, min(clip_dur - 0.05, cand + actual / 2))
            try:
                energy = _motion_energy(src.get_frame(probe_t))
            except Exception:
                continue
            if energy > best_energy:
                best_start, best_energy = cand, energy
        start = best_start
        log(f"  Hook clip: opening on t={start:.1f}s (energy={best_energy:.1f} "
            f"of {n_candidates} candidates)")
    else:
        start = reg_start + max(0, slack / 2)
    start     = max(0, min(start, clip_dur - actual - 0.1))
    end       = start + actual

    src = _fl(src, transform)

    try:
        seg = src.subclipped(start, end) if hasattr(src, "subclipped") else src.subclip(start, end)
    except:
        seg = _dur(src, actual)

    # Slight speed-up (1.08x)
    try: seg = _speed(seg, 1.08)
    except: pass

    # Optional brief hold on the last frame of the hook segment -- a toned-down,
    # full-color version of the "aura-freeze" retention device (no monochrome
    # grade, kept subtle to match this pipeline's clean/professional look).
    # config.FREEZE_INTENSITY (0.0-1.0) scales how much of the segment it eats.
    freeze_intensity = max(0.0, min(1.0, getattr(config, "FREEZE_INTENSITY", 0.0)))
    freeze_dur = seg_dur * 0.2 * freeze_intensity if apply_freeze else 0.0
    seg_dur_normal = seg_dur - freeze_dur

    seg = _dur(seg, seg_dur_normal)

    if freeze_dur > 0.05:
        try:
            last_frame = seg.get_frame(max(0.0, seg_dur_normal - 0.05))
            freeze_dir = os.path.join(config.OUTPUT_DIR, "temp_freeze")
            os.makedirs(freeze_dir, exist_ok=True)
            freeze_path = os.path.join(freeze_dir, f"pro_freeze_{random.randint(1000, 9999)}.png")
            Image.fromarray(last_frame).save(freeze_path)
            freeze_clip = _dur(ImageClip(freeze_path), freeze_dur)
            seg = concatenate_videoclips([seg, freeze_clip])
        except Exception as e:
            log(f"  Freeze frame skipped: {e}")
            seg = _dur(seg, seg_dur)

    log(f"  Segment {idx+1}: flip={do_flip} sat={sat:.2f} dur={seg_dur:.1f}s freeze={freeze_dur:.2f}s")
    return seg


# ══════════════════════════════════════════════════════════════════════════════
#  6. TEXT OVERLAY (Clean, professional — word-by-word captions)
# ══════════════════════════════════════════════════════════════════════════════

_FONT_CACHE = {}

def get_font(size: int, bold: bool = False, hindi: bool = False) -> ImageFont.FreeTypeFont:
    key = (size, bold, hindi)
    if key in _FONT_CACHE: return _FONT_CACHE[key]
    if hindi:
        # Impact/Arial have no Devanagari glyphs (render as tofu boxes) --
        # Nirmala UI ships on Windows and covers Devanagari.
        paths = ["C:\\Windows\\Fonts\\Nirmala.ttc", "C:\\Windows\\Fonts\\mangal.ttf",
                 # Bundled (OFL) for Linux/cloud renders.
                 os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "NotoSansDevanagari-Bold.ttf")]
    else:
        paths = [
            "C:\\Windows\\Fonts\\Impact.ttf",
            "C:\\Windows\\Fonts\\arialbd.ttf" if bold else "C:\\Windows\\Fonts\\arial.ttf",
            # Linux (cloud/CI renders) -- without these, load_default() gives
            # a tiny bitmap font and the captions are unreadable.
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
    font = None
    for p in paths:
        if os.path.exists(p):
            try: font = ImageFont.truetype(p, size); break
            except: pass
    if not font: font = ImageFont.load_default()
    _FONT_CACHE[key] = font
    return font


_END_CARD_VARIANTS = ["LIKE  &  SUBSCRIBE", "FOLLOW FOR MORE", "SUBSCRIBE FOR MORE", "MORE FACTS -- FOLLOW"]

# How long the bold top-third hook headline stays up. Kept short: it must
# cover the swipe decision (<=1s) and the first beat of narration, then get
# out of the way so it never competes with the word-by-word captions below.
HOOK_CARD_DUR = 3.2


def is_hindi_lang(script: dict) -> bool:
    return script.get("lang") == "hi"


def _wrap_to_width(draw, text: str, font, max_w: int) -> list:
    """Greedy word wrap so the hook headline never runs off-frame."""
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if draw.textbbox((0, 0), trial, font=font)[2] <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _auto_hook_card(hook: str) -> str:
    """Condense the spoken hook into a 3-7 word on-screen headline.

    A script can override this by setting SCRIPT["hook_card"] explicitly --
    prefer that for anything where the punchy phrasing matters. This is the
    fallback so every video gets *some* top-third promise rather than none.
    """
    if not hook:
        return ""
    text = hook.split("--")[0].split(". ")[0].strip(" .!?,")
    words = text.split()
    if len(words) > 7:
        text = " ".join(words[:7])
    return text.upper()


def render_overlay(frame: np.ndarray, script: dict, t: float,
                   duration: float, word_timestamps: list = None) -> np.ndarray:
    """
    Professional overlay — clean and minimal:
      - Small channel badge top-left
      - Word-by-word caption centered near bottom
      - Thin progress bar at very bottom
    """
    frame = frame.copy()
    H, W = frame.shape[:2]
    pct = t / duration

    img = Image.fromarray(frame)
    draw = ImageDraw.Draw(img)

    # ── Bottom scrim (subtle gradient for text readability) ──────────────
    scrim_h = 300
    for i in range(scrim_h):
        alpha = 0.55 * (i / scrim_h)    # 0 at top edge, 0.55 at bottom
        y = H - scrim_h + i
        for c in range(3):
            img_arr = np.array(img)
            # We'll do this with PIL instead for efficiency
        break  # Exit — use numpy approach below

    # Numpy scrim: darken bottom 300px gradually
    arr = np.array(img)
    alpha_col = np.linspace(1.0, 0.45, scrim_h)[:, np.newaxis, np.newaxis]
    arr[H - scrim_h:H, :, :] = (arr[H - scrim_h:H, :, :] * alpha_col).astype(np.uint8)
    img = Image.fromarray(arr)
    draw = ImageDraw.Draw(img)

    # ── Channel badge (top-left, small, subtle) ─────────────────────────
    font_ch = get_font(28)
    draw.text((26, 24), CHANNEL, font=font_ch, fill=(255,255,255,180),
              stroke_width=2, stroke_fill=(0,0,0))

    # ── TOP-THIRD HOOK HEADLINE (first HOOK_CARD_DUR seconds) ───────────
    # Viral-Shorts research (2026-09-02): the keep-or-swipe decision is
    # made at or before 1 second, and top performers stack a bold 3-7 word
    # headline in the TOP THIRD so the promise registers before the first
    # syllable finishes -- 85% of Shorts are watched muted at first, so the
    # hook has to be readable, not just spoken. This channel put every word
    # at the BOTTOM (y = H-460) with nothing up top but a small badge,
    # meaning a muted viewer saw no promise at all in second one.
    hook_headline = script.get("hook_card") or _auto_hook_card(script.get("hook", ""))
    if hook_headline and t < HOOK_CARD_DUR:
        fade = 1.0 if t < HOOK_CARD_DUR - 0.4 else max(0.0, (HOOK_CARD_DUR - t) / 0.4)
        hsize = 86
        hfont = get_font(hsize, bold=True, hindi=is_hindi_lang(script))
        lines = _wrap_to_width(draw, hook_headline, hfont, W - 90)
        while len(lines) > 3 and hsize > 54:
            hsize -= 6
            hfont = get_font(hsize, bold=True, hindi=is_hindi_lang(script))
            lines = _wrap_to_width(draw, hook_headline, hfont, W - 90)
        line_h = int(hsize * 1.18)
        block_h = line_h * len(lines)
        y0 = max(110, int(H * 0.30) - block_h // 2)   # sits in the top third
        band = int(255 * 0.55 * fade)
        if band > 0:
            ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
            ImageDraw.Draw(ov).rectangle(
                [(0, y0 - 26), (W, y0 + block_h + 26)], fill=(0, 0, 0, band))
            img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
            draw = ImageDraw.Draw(img)
        for i, ln in enumerate(lines):
            bb = draw.textbbox((0, 0), ln, font=hfont)
            lx = (W - (bb[2] - bb[0])) // 2
            shade = int(255 * fade)
            draw.text((lx, y0 + i * line_h), ln, font=hfont,
                      fill=(shade, shade, shade), stroke_width=6, stroke_fill=(0, 0, 0))

    # ── Word-by-word caption (center-bottom) ────────────────────────────
    is_hindi = script.get("lang") == "hi"
    full_text = f"{script['hook']}. {script['body']} {script['cta']}"
    # caption_text: on-screen words that differ from the spoken script (e.g.
    # Roman-letter captions over Hindi narration). Must have the same token
    # count as the narration; "~" tokens keep timing but aren't shown.
    words = (script.get("caption_text") or full_text).split()
    total_words = len(words)
    words_per_group = 3

    if word_timestamps and len(word_timestamps) >= total_words * 0.7:
        # Real timing: find the transcribed word whose window contains `t`
        # (or the most recent one spoken, during a pause) and show its group.
        n = min(total_words, len(word_timestamps))
        cur_idx = 0
        for i in range(n):
            if word_timestamps[i]["start"] <= t:
                cur_idx = i
            else:
                break
        group_idx = cur_idx // words_per_group
    else:
        # Fallback: guessed constant speech rate
        n_groups = max(1, (total_words + words_per_group - 1) // words_per_group)
        group_dur = duration / n_groups
        group_idx = min(int(t / group_dur), n_groups - 1)

    start_w = group_idx * words_per_group
    end_w = min(start_w + words_per_group, total_words)
    phrase = " ".join(w for w in words[start_w:end_w] if w != "~")

    # ── Stat-reveal "number pop": these are literal numeric-fact videos
    # (60 feet, 22 yards, 24 seconds...) and every prior build rendered the
    # payoff number as identical plain-white text to everything else --
    # zero pattern-interrupt at the one moment the video is actually
    # "about." Bigger, gold, brief punch-in scale exactly when a digit
    # group is on screen turns that into a real visual beat instead of a
    # missed opportunity.
    has_number = bool(re.search(r"\d", phrase))
    if word_timestamps and len(word_timestamps) >= total_words * 0.7 and start_w < len(word_timestamps):
        group_start_t = word_timestamps[start_w]["start"]
    else:
        group_start_t = group_idx * (duration / max(1, (total_words + words_per_group - 1) // words_per_group))
    punch_elapsed = t - group_start_t

    # Draw centered text
    base_size = 92 if has_number else 72
    punch_scale = 1.0
    if has_number and 0 <= punch_elapsed < 0.22:
        punch_scale = 1.35 - (punch_elapsed / 0.22) * 0.35  # overshoot-in, settle to 1.0x
    cap_size = max(40, int(base_size * punch_scale))
    cap_font = get_font(cap_size, bold=True, hindi=is_hindi)
    # Shrink if too wide
    while cap_size > 48 and draw.textbbox((0,0), phrase, font=cap_font)[2] > W - 80:
        cap_size -= 4
        cap_font = get_font(cap_size, bold=True, hindi=is_hindi)
    cap_fill = (255, 210, 40) if has_number else (255, 255, 255)

    bb = draw.textbbox((0,0), phrase, font=cap_font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    x = (W - tw) // 2
    y = H - 460  # well clear of YouTube's own Shorts UI chrome (like/comment/
                 # share icons + description bar cover roughly the bottom third)

    draw.text((x, y), phrase, font=cap_font, fill=cap_fill,
              stroke_width=5, stroke_fill=(0, 0, 0))

    # ── EARLY SUBSCRIBE PROMPT ──────────────────────────────────────────
    # The subscribe button used to appear ONLY in the last 5 seconds, which
    # means the ~50% of viewers who swipe before the end never saw it at
    # all. This channel's core problem is subscriber conversion (28 subs
    # from 110 videos), so the ask has to reach people who do not finish.
    # Placed AFTER the top-third hook card clears (HOOK_CARD_DUR = 3.2s) so
    # the two never compete for attention.
    early_start = HOOK_CARD_DUR + 0.3
    early_len = 3.0
    if early_start <= t < early_start + early_len:
        et = t - early_start
        if et < 0.25:
            esc = 1.15 * (et / 0.25)
        elif et < 0.4:
            esc = 1.15 - (et - 0.25) / 0.15 * 0.15
        elif et > early_len - 0.4:
            esc = max(0.01, (early_len - et) / 0.4)
        else:
            esc = 1.0 + 0.04 * math.sin((et - 0.4) * 6.0)
        esc = max(0.01, esc)

        ebw, ebh = int(360 * esc), int(78 * esc)
        ebx = (W - ebw) // 2
        eby = int(H * 0.20)
        eglow = int(14 * (0.5 + 0.5 * math.sin(et * 6.0)))
        draw.rounded_rectangle([ebx - eglow, eby - eglow,
                                ebx + ebw + eglow, eby + ebh + eglow],
                               radius=22, fill=(120, 0, 0))
        draw.rounded_rectangle([ebx, eby, ebx + ebw, eby + ebh],
                               radius=16, fill=(255, 0, 0))
        ef = get_font(max(1, int(31 * esc)), bold=True)
        etxt = "SUBSCRIBE"
        ebb = draw.textbbox((0, 0), etxt, font=ef)
        draw.text((ebx + (ebw - (ebb[2] - ebb[0])) // 2,
                   eby + (ebh - (ebb[3] - ebb[1])) // 2 - 2),
                  etxt, font=ef, fill=(255, 255, 255))

    # ── Animated Like + Subscribe button (pops in for the final CTA window) ──
    cta_window = 5.0
    if t >= duration - cta_window:
        appear_t = t - (duration - cta_window)
        if appear_t < 0.25:
            scale = 1.15 * (appear_t / 0.25)          # pop in, overshoot to 1.15x
        elif appear_t < 0.4:
            scale = 1.15 - (appear_t - 0.25) / 0.15 * 0.15  # settle back to 1.0x
        else:
            scale = 1.0 + 0.05 * math.sin((appear_t - 0.4) * 5.0)  # gentle pulse
        scale = max(0.01, scale)

        # Slide up from just below frame into resting position, well above
        # the word-caption line (now at H-460) so the two never overlap
        rest_y = H - 640
        slide_in = min(1.0, appear_t / 0.3)
        by = int(H - 40 + (rest_y - (H - 40)) * slide_in)

        base_w, base_h = 420, 90
        btn_w, btn_h = int(base_w * scale), int(base_h * scale)
        bx = (W - btn_w) // 2

        glow = int(20 * (0.5 + 0.5 * math.sin(appear_t * 5.0)))
        draw.rounded_rectangle([bx - glow, by - glow, bx + btn_w + glow, by + btn_h + glow],
                                radius=24, fill=(120, 0, 0))
        draw.rounded_rectangle([bx, by, bx + btn_w, by + btn_h], radius=18, fill=(255, 0, 0))

        # Plain text, no emoji glyphs -- this font has no emoji coverage and
        # renders them as empty tofu boxes.
        # Every prior video used the literal same end-card text -- one of
        # the identical-template elements making every FramedFacts short
        # visually interchangeable. Vary it per video (deterministic on the
        # title, so it's stable across this video's own frames) instead of
        # hardcoding the one phrase everywhere.
        sub_font = get_font(max(1, int(34 * scale)), bold=True)
        sub_text = _END_CARD_VARIANTS[hash(script.get("title", "")) % len(_END_CARD_VARIANTS)]
        sbb = draw.textbbox((0, 0), sub_text, font=sub_font)
        stx = bx + (btn_w - (sbb[2] - sbb[0])) // 2
        sty = by + (btn_h - (sbb[3] - sbb[1])) // 2 - 2
        draw.text((stx, sty), sub_text, font=sub_font, fill=(255, 255, 255))

    # ── Thin progress bar (very bottom, 4px) ────────────────────────────
    bar_w = int(W * pct)
    draw.rectangle([(0, H-4), (W, H)], fill=(40, 40, 40))
    if bar_w > 0:
        draw.rectangle([(0, H-4), (bar_w, H)], fill=(0, 200, 100))

    return np.array(img)


# ══════════════════════════════════════════════════════════════════════════════
#  6b. INTRO STING (channel identity card, solid background -- no alpha needed
#      so it can be flatly prepended before the hook clip starts)
# ══════════════════════════════════════════════════════════════════════════════

def generate_intro_sting(out_path: str = None, duration: float = 1.3) -> str:
    """Short channel-intro title card: a crisp scale+fade reveal of the
    channel name over a solid dark background, with a red accent underline
    that draws in after the name lands. Matches this pipeline's established
    minimal/professional tone (see module docstring: no bounce, no spin, no
    gimmicks) rather than a flashy logo-sting -- it's meant to read as a
    consistent identity beat at the top of every video, not a distraction."""
    out_path = out_path or os.path.join(config.VIDEOS_DIR, "intro_sting.mp4")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    title = CHANNEL

    def make_frame(t):
        img = Image.new("RGB", (WIDTH, HEIGHT), (8, 8, 10))
        draw = ImageDraw.Draw(img)

        # Ease-out scale+fade over the first ~0.45s, then a brief hold
        reveal = min(1.0, t / 0.45)
        eased = 1 - (1 - reveal) ** 3
        scale = 0.85 + 0.15 * eased

        size = max(1, int(96 * scale))
        font = get_font(size, bold=True)
        bbox = draw.textbbox((0, 0), title, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x, y = (WIDTH - tw) // 2, (HEIGHT - th) // 2

        fill = tuple(int(255 * eased) for _ in range(3))
        draw.text((x, y), title, font=font, fill=fill,
                  stroke_width=3, stroke_fill=(0, 0, 0))

        # Thin red accent underline, draws in left-to-right after the title lands
        if t > 0.45:
            line_progress = min(1.0, (t - 0.45) / 0.25)
            line_w = int(tw * line_progress)
            ly = y + th + 18
            draw.rectangle([x, ly, x + line_w, ly + 4], fill=(200, 30, 30))

        return np.array(img)

    clip = VideoClip(make_frame, duration=duration)
    clip.write_videofile(out_path, fps=FPS, codec="libx264", audio=False,
                         preset="medium", ffmpeg_params=["-crf", "18"], logger=None)
    log(f"Intro sting rendered: {out_path}")
    return out_path


# ══════════════════════════════════════════════════════════════════════════════
#  7. ASSEMBLY (clips + voice + music + overlay → final video)
# ══════════════════════════════════════════════════════════════════════════════

def compute_segment_bounds(script: dict, word_timestamps: list, duration: float) -> list:
    """Real hook/body/CTA segment (start, dur) boundaries from measured word
    timestamps, instead of guessing equal thirds. Falls back to equal division
    if timestamps are missing or don't line up with the script's word count."""
    hook_n = len(script.get("hook", "").split())
    body_n = len(script.get("body", "").split())
    cta_n  = len(script.get("cta", "").split())
    total_n = hook_n + body_n + cta_n

    MIN_SEG = 1.2  # never let a segment collapse to near-zero
    fallback = [(0.0, duration / 3), (duration / 3, duration / 3), (2 * duration / 3, duration / 3)]

    if not word_timestamps or total_n == 0 or len(word_timestamps) < total_n * 0.7:
        return fallback

    try:
        hook_end = word_timestamps[min(hook_n, len(word_timestamps)) - 1]["end"]
        body_end = word_timestamps[min(hook_n + body_n, len(word_timestamps)) - 1]["end"]
        hook_end = max(MIN_SEG, min(hook_end, duration - 2 * MIN_SEG))
        body_end = max(hook_end + MIN_SEG, min(body_end, duration - MIN_SEG))
        return [(0.0, hook_end), (hook_end, body_end - hook_end), (body_end, duration - body_end)]
    except Exception:
        return fallback


def assemble(clip_paths: list, script: dict, vo_path: str,
             music_path: str, out_path: str):
    """Assemble professional video. Clean, no gimmicks."""
    # Same deterministic transform generate_voiceover() applies -- since both
    # start from the same original script, this keeps captions and segment
    # timing in sync with the sign-off actually spoken in vo_path, without
    # requiring every caller to thread a modified script through manually.
    script = _with_persona_signoff(script)

    # If only 1 clip, reuse it for all 3 segments
    while len(clip_paths) < 3:
        clip_paths.append(clip_paths[-1])

    # Duration from voice. Never truncate shorter than the actual narration --
    # a Hindi voiceover ran 47.6s against this same hard-26s cap and the
    # video silently cut off mid-script, dropping the back half of the
    # content. The cap now only guards against a genuinely broken/runaway
    # audio file, not real content that happens to run past ~26s.
    vo_clip = AudioFileClip(vo_path)
    duration = min(vo_clip.duration + 1.5, 90.0)
    if vo_clip.duration > 26.0:
        log(f"Voiceover is {vo_clip.duration:.1f}s (longer than the usual ~26s) -- "
            f"keeping the full {duration:.1f}s rather than cutting the script short.")
    word_timestamps = get_word_timestamps(vo_path)
    bounds = compute_segment_bounds(script, word_timestamps, duration)
    log(f"Duration: {duration:.1f}s, clips: {len(clip_paths)}, "
        f"segment bounds: {[(round(s,1), round(d,1)) for s,d in bounds]}")

    # If every clip_path is the same file, it's one continuous story clip
    # (e.g. a single 20-25s Veo/Firefly generation) -- slice progressively
    # through its timeline per segment. If they're distinct files, each is
    # already its own independent, full-length scene (e.g. per-scene
    # AnimateDiff clips) -- use each one in full.
    single_continuous_clip = len(set(clip_paths)) == 1

    # Build segments (real per-beat durations, not equal thirds)
    # Long single-clip segments (the body beat routinely ran 15-20s) played
    # as one slow, static-feeling shot the whole time -- far below
    # Shorts-native cut frequency, and a real contributor to weak
    # retention. Split anything over this threshold into two hard cuts
    # using different halves of the SAME source clip's own timeline
    # (prepare_segment's region_start_frac/region_dur_frac already fraction
    # against the clip's own duration) -- a real mid-beat cut with zero
    # extra footage needed, which is the actual constraint on this account.
    PACING_SPLIT_THRESHOLD = 9.0
    # FAST CUTS (2026-09-18). Splitting only beats over 9s still left ~6
    # shots of 4-9s per Short. The week's top cricket Shorts in India cut
    # every 1-2s, and the owner called ours "cheap". Every beat is now cut
    # into ~FAST_CUT_SECONDS shots that ROTATE through all supplied clips
    # (real player photos included), each reuse taking a different window
    # of its source. Pass clip_paths in narration order and each shot lands
    # roughly on the line it illustrates.
    # A script can ask for faster cuts (the 2026-10 "why" format hits cut
    # every 1.2-1.5s) via script["cut_seconds"].
    FAST_CUT_SECONDS = float(script.get("cut_seconds", 2.4))
    shot_no, uses = 0, {}
    segments = []
    for i, cp in enumerate(clip_paths[:len(bounds)]):
        seg_start, seg_dur = bounds[i]
        sub_specs = [(seg_start, seg_dur)]
        if not single_continuous_clip:
            n = max(1, int(round(seg_dur / FAST_CUT_SECONDS)))
            step = seg_dur / n
            sub_specs = [(seg_start + k * step, step) for k in range(n)]

        for sub_idx, (sub_start, sub_dur) in enumerate(sub_specs):
            is_first_overall = (i == 0 and sub_idx == 0)
            # concatenate_videoclips' global `padding=-CROSSFADE_DUR` eats
            # CROSSFADE_DUR of overlap at EVERY transition between segments
            # -- this was true even before pacing-split existed (2
            # transitions in the original 3-segment hook/body/cta design),
            # it just wasn't enough to produce visibly-obvious black before.
            # Left uncompensated, the concatenated video ends up shorter
            # than `duration` by (num_transitions * CROSSFADE_DUR), and the
            # final _dur(video, duration) upsizing at the end of assemble()
            # then reads past real content on whichever clip landed last,
            # surfacing as true black frames (reproduced live 2026-08-30:
            # first found ~1.4s of black with 2 pacing-split transitions
            # added on top of the original 2 -- compensating only the 2 new
            # ones cut it to ~0.7s, proving the ORIGINAL 2 transitions were
            # already uncompensated too). Request that bit of extra real
            # footage on every incoming transition, not just split-added
            # ones, so the visible net duration actually matches the budget.
            working_dur = sub_dur + CROSSFADE_DUR if not is_first_overall else sub_dur
            try:
                if single_continuous_clip:
                    start_frac = sub_start / duration
                    dur_frac = sub_dur / duration
                    raw = prepare_segment(cp, working_dur, i, len(bounds),
                                           region_start_frac=start_frac, region_dur_frac=dur_frac,
                                           apply_freeze=is_first_overall, prefer_dynamic_start=is_first_overall)
                else:
                    shot_cp = clip_paths[shot_no % len(clip_paths)]
                    k = uses.get(shot_cp, 0)
                    uses[shot_cp] = k + 1
                    shot_no += 1
                    raw = prepare_segment(shot_cp, working_dur, 0, 1,
                                           region_start_frac=(k * 0.37) % 0.65,
                                           region_dur_frac=0.35,
                                           apply_freeze=is_first_overall, prefer_dynamic_start=is_first_overall)
            except Exception as e:
                log(f"Segment {i}.{sub_idx} failed: {e}")
                continue

            _ss, _sc, _td, _wt = sub_start, script, duration, word_timestamps
            def overlay(gf, t, sc=_sc, ss=_ss, td=_td, wt=_wt):
                try:
                    return render_overlay(gf(t), sc, ss + t, td, wt)
                except Exception as e:
                    return gf(t)  # Fail silently — show raw frame

            seg = _fl(raw, overlay)
            seg = _dur(seg, working_dur)

            # Cinematic crossfade into every segment after the very first
            # (creates a short overlap with the previous one via
            # concatenate's `padding`) -- including a mid-beat split cut.
            if not is_first_overall and CrossFadeIn is not None and working_dur > CROSSFADE_DUR * 2:
                try:
                    seg = seg.with_effects([CrossFadeIn(CROSSFADE_DUR)])
                except Exception:
                    pass

            segments.append(seg)

    if not segments:
        raise Exception("No valid segments")

    crossfade_padding = -CROSSFADE_DUR if (CrossFadeIn is not None and len(segments) > 1) else 0
    video = concatenate_videoclips(segments, method="compose", padding=crossfade_padding)
    video = _dur(video, duration)

    # Audio: voice (boosted -- cloned-voice output otherwise renders quiet
    # next to the music bed) + music that ducks under speech and breathes
    # in gaps, + a one-shot drop hit on the hook. Direct feedback
    # 2026-08-22: music should stay background under narration, but come
    # up during pauses/pure-visual moments, and the hook should land with
    # a real hit -- previously this was a single flat 0.06 volume for the
    # whole video regardless of what was happening.
    vo = _dur(vo_clip, min(vo_clip.duration, duration))
    vo = _vol(vo, 1.6)
    raw_music = AudioFileClip(music_path)
    if raw_music.duration < duration:
        raw_music = concatenate_audioclips([raw_music] * (int(duration / raw_music.duration) + 2))
    music = _dur(raw_music, duration)
    music = _fl(music, _music_ducking_filter(vo_clip, duration))

    audio_layers = [music, vo]
    try:
        import music_generator
        hit_path = music_generator.get_hook_hit()
        hit = AudioFileClip(hit_path)
        hit = _vol(hit, 0.9)
        audio_layers.append(hit)
    except Exception as e:
        log(f"Hook hit sound unavailable ({e}) -- continuing without it")

    try:
        mixed = CompositeAudioClip(audio_layers)
    except:
        mixed = vo
    mixed = _dur(mixed, duration)

    video = _audio(video, mixed)
    video = _dur(video, duration)

    # Render — broadcast quality
    os.makedirs(config.VIDEOS_DIR, exist_ok=True)
    log(f"Rendering HD 1080x1920 -> {out_path}")
    video.write_videofile(
        out_path, fps=FPS, codec="libx264", audio_codec="aac",
        audio_bitrate="192k", logger="bar", threads=8,
        ffmpeg_params=[
            "-crf",     "18",
            "-preset",  "faster",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
        ],
    )
    video.close()
    vo_clip.close()
    log("Video rendered successfully!")


# ══════════════════════════════════════════════════════════════════════════════
#  8. UPLOAD
# ══════════════════════════════════════════════════════════════════════════════

def _srt_timestamp(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def generate_srt(word_timestamps: list, out_path: str, words_per_group: int = 3) -> str:
    """Real .srt captions from measured word timestamps -- for upload as an
    actual YouTube caption track (accessibility + discoverability), separate
    from the burned-in on-screen captions."""
    lines = []
    idx = 1
    for i in range(0, len(word_timestamps), words_per_group):
        group = word_timestamps[i:i + words_per_group]
        if not group:
            continue
        start, end = group[0]["start"], group[-1]["end"]
        text = " ".join(w["word"] for w in group if w["word"] != "~")
        if not text:
            continue
        lines.append(f"{idx}\n{_srt_timestamp(start)} --> {_srt_timestamp(end)}\n{text}\n")
        idx += 1
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return out_path


def upload(video_path: str, script: dict, vo_path: str = None) -> str:
    """Upload to YouTube via existing phase5_upload module, plus real .srt
    captions (generated from the voiceover's measured word timestamps) if available."""
    try:
        import phase5_upload as p5
        topic = {"id": int(time.time()), "title": script["title"],
                 "subject": script["hook"], "category": script.get("topic_category", "Sports")}
        result = p5.upload_all(video_path, script, topic)
        url = result.get("youtube")
        if url: log(f"YouTube: {url}")

        if url and vo_path:
            word_timestamps = get_word_timestamps(vo_path)
            if word_timestamps:
                srt_path = vo_path.rsplit(".", 1)[0] + ".srt"
                generate_srt(word_timestamps, srt_path)
                video_id = url.rsplit("=", 1)[-1]
                try:
                    p5.upload_captions(video_id, srt_path,
                                       language=script.get("caption_lang", "en"),
                                       name=script.get("caption_name", "English"))
                except Exception as e:
                    log(f"Caption upload failed: {e}")

        return url
    except Exception as e:
        log(f"Upload error: {e}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
#  REVIEW QUEUE (draft -> approve/reject -> render & upload)
# ══════════════════════════════════════════════════════════════════════════════

QUEUE_FILE = os.path.join(config.OUTPUT_DIR, "review_queue.json")


def _load_queue() -> list:
    if os.path.exists(QUEUE_FILE):
        try:
            with open(QUEUE_FILE, encoding="utf-8") as f: return json.load(f)
        except: pass
    return []


def _save_queue(records: list):
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    with open(QUEUE_FILE, "w", encoding="utf-8") as f: json.dump(records, f, indent=2)


def _get_record(record_id: str) -> dict:
    for r in _load_queue():
        if r["id"] == record_id: return r
    raise KeyError(f"No record {record_id}")


def _update_record(record_id: str, **fields):
    records = _load_queue()
    for r in records:
        if r["id"] == record_id:
            r.update(fields)
            break
    _save_queue(records)


def _make_thumbnail(clip_path: str) -> str:
    """Grab one frame from a clip for the review dashboard."""
    thumb_path = clip_path.rsplit(".", 1)[0] + "_thumb.jpg"
    if os.path.exists(thumb_path):
        return thumb_path
    try:
        vc = VideoFileClip(clip_path)
        frame = vc.get_frame(min(1.0, max(0.0, vc.duration / 2)))
        vc.close()
        Image.fromarray(frame).save(thumb_path, quality=80)
    except Exception as e:
        log(f"Thumbnail failed for {clip_path}: {e}")
        return ""
    return thumb_path


def create_draft() -> dict:
    """Generate a script, footage, and a voice preview. Saves to the review
    queue as a pending record -- does NOT render or upload."""
    config.assert_safe_pipeline()
    log("=" * 60)
    log(f"  PRO SHORTS -- Creating draft for review")
    log("=" * 60)

    state = load_state()
    state["count"] = state.get("count", 0) + 1
    script = generate_script(state)
    save_state(state)

    clip_paths = download_clips(script)
    clip_thumbs = [_make_thumbnail(p) for p in clip_paths]

    vo_path = generate_voiceover(script)

    vo_dur = 21.0
    try:
        vc = AudioFileClip(vo_path)
        vo_dur = min(vc.duration + 1.5, 26.0)
        vc.close()
    except: pass
    music_path = get_music(duration=vo_dur)

    record = {
        "id": str(int(time.time() * 1000)),
        "created_at": time.time(),
        "topic": script.get("title", ""),
        "script": script,
        "clip_paths": clip_paths,
        "clip_thumbs": clip_thumbs,
        "voice_path": vo_path,
        "music_path": music_path,
        "status": "pending",
        "decision_notes": "",
        "video_path": None,
        "youtube_url": None,
        "views": None,
        "likes": None,
        "stats_synced_at": None,
    }
    records = _load_queue()
    records.append(record)
    _save_queue(records)
    log(f"Draft ready for review: {record['id']} -- {script['hook'][:60]}")
    return record


def render_and_publish(record_id: str) -> dict:
    """Render the approved draft's video and upload it (respects
    config.UPLOAD_PRIVACY). Updates the record's status in place."""
    record = _get_record(record_id)
    script = record["script"]

    import copyright_compliance as cc
    check = cc.validate_before_upload(script, record["clip_paths"], record["music_path"])
    cc.save_compliance_report(check, record_id)
    if not check["passed"]:
        log(f"Compliance check FAILED for {record_id}: {check['issues']}")
        _update_record(record_id, status="failed",
                        decision_notes=f"Compliance check failed: {'; '.join(check['issues'])}")
        return _get_record(record_id)

    _update_record(record_id, status="rendering")

    try:
        out_path = os.path.join(config.VIDEOS_DIR, f"pro_{record_id}.mp4")
        assemble(record["clip_paths"], script, record["voice_path"], record["music_path"], out_path)

        url = upload(out_path, script, record["voice_path"])
        _update_record(record_id, status="uploaded", video_path=out_path, youtube_url=url)
        log(f"  VIDEO {record_id} COMPLETE! YouTube: {url or '(saved, not uploaded)'}")
        return _get_record(record_id)

    except Exception as e:
        log(f"ERROR rendering {record_id}: {e}")
        import traceback; traceback.print_exc()
        _update_record(record_id, status="failed", decision_notes=str(e))
        return _get_record(record_id)


def run_one():
    """One-shot: draft immediately followed by render+upload, no review step."""
    record = create_draft()
    return render_and_publish(record["id"])


def main():
    log("=" * 60)
    log(f"  PRO SHORTS -- Draft Auto Loop")
    log(f"  Populates the review queue every {config.LOOP_INTERVAL_MINUTES} min.")
    log(f"  Run dashboard.py to review/approve drafts.")
    log("=" * 60)
    create_draft()
    while True:
        log(f"Next draft in {config.LOOP_INTERVAL_MINUTES} minutes...")
        time.sleep(config.LOOP_INTERVAL_MINUTES * 60)
        create_draft()


if __name__ == "__main__":
    main()
