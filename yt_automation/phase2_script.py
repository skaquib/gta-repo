"""
Phase 2 — Script Generation & Localisation
Generates an 8-minute structured script as JSON.
Localises voiceover into target languages.
"""

import json
import os
import anthropic
import config
from logger import log

client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)


SCRIPT_PROMPT = """You are a top YouTube scriptwriter for educational animation channels.

Write a highly engaging 8-minute script about: "{title}"
Topic description: {subject}
Hook angle: {hook_angle}
Channel: {channel} ({niche})

Script requirements:
- 10-second high-retention hook (shocking fact or question)
- 5 clearly structured body sections with smooth transitions
- Strong CTA at the end ("Subscribe for more mind-bending facts")
- Conversational, punchy tone — not academic
- Each scene should be visually descriptive for animation

Return ONLY valid JSON, no markdown. Format:
{{
  "video_title": "final SEO-optimised title",
  "seo_description": "150-word YouTube description with keywords",
  "tags": ["tag1","tag2","tag3","tag4","tag5","tag6","tag7","tag8"],
  "total_duration_seconds": 480,
  "scenes": [
    {{
      "scene_id": 1,
      "section": "Hook|Introduction|Point1|Point2|Point3|Point4|Point5|CTA",
      "visual_description": "what the animation shows — detailed for AI image/video generation",
      "voiceover_en": "English voiceover text for this scene",
      "duration_seconds": 10,
      "animation_style": "flat-vector|3d-render|kinetic-text|infographic"
    }}
  ]
}}"""


TRANSLATE_PROMPT = """Translate the following English voiceover text to {language}.
Maintain emotional tone, local idioms, and conversational style.
Do NOT translate literally — localise culturally for {region} audiences.
Return ONLY the translated text, nothing else.

Text: {text}"""



SCRIPT_PROMPT_SHORTS = """You are a top YouTube scriptwriter specializing in viral football/soccer YouTube Shorts.

Write a highly engaging, fast-paced 45-second YouTube Short script about: "{title}"
Topic description: {subject}
Hook angle: {hook_angle}
Channel: {channel} ({niche})

Script requirements:
- Maximum 45 seconds total duration. (Keep voiceover concise so it reads naturally under 45 seconds. Total words should be around 110-130 words).
- Hook (first 3-5 seconds): Start with an extremely engaging hook (e.g. "Do not scroll! Did you know...?" or "This is the most illegal thing in FIFA history...").
- Fast structure: 7-9 scenes maximum, each lasting between 4 to 6 seconds.
- Every scene must have a very clear visual description (specifically optimized for styling text/graphics in portrait 1080x1920 layout).
- Use dynamic, punchy voiceover style (short sentences, bold claims).
- CTA at the end: Polarizing question (to drive comments) + quick sub prompt (e.g., "Would you play with these rules? Subscribe for more!").

Return ONLY valid JSON, no markdown. Format:
{{
  "video_title": "final SEO-optimised title (with hashtags like #shorts #fifa)",
  "seo_description": "short YouTube description with hashtags",
  "tags": ["shorts", "fifa", "soccer", "football", "worldcup"],
  "total_duration_seconds": 45,
  "scenes": [
    {{
      "scene_id": 1,
      "section": "Hook|Introduction|Point1|Point2|Point3|CTA",
      "visual_description": "what styling/animation to show. (Keep it descriptive for rendering, e.g. Neon text saying: RED CARD)",
      "voiceover_en": "English voiceover text for this scene (max 15-18 words per scene)",
      "duration_seconds": 5,
      "animation_style": "kinetic-text|flat-vector|infographic"
    }}
  ]
}}"""


def generate_script(topic: dict) -> dict:
    log(f"Phase 2: Generating script for '{topic['title']}'...")

    if getattr(config, "VIDEO_TYPE", "long") == "shorts":
        prompt = SCRIPT_PROMPT_SHORTS.format(
            title=topic["title"],
            subject=topic["subject"],
            hook_angle=topic["hook_angle"],
            channel=config.CHANNEL_NAME,
            niche=config.CHANNEL_NICHE,
        )
    else:
        prompt = SCRIPT_PROMPT.format(
            title=topic["title"],
            subject=topic["subject"],
            hook_angle=topic["hook_angle"],
            channel=config.CHANNEL_NAME,
            niche=config.CHANNEL_NICHE,
        )

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=6000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()

    try:
        script = json.loads(raw)
        log(f"Phase 2: Script generated — {len(script['scenes'])} scenes, title: {script['video_title']}")
        return script
    except json.JSONDecodeError as e:
        log(f"Phase 2 ERROR: JSON parse failed — {e}")
        raise


def localise_script(script: dict) -> dict:
    """Add localised voiceover columns for each target language."""
    languages = [l.strip() for l in config.TARGET_LANGUAGES if l.strip().lower() != "english"]

    for lang in languages:
        log(f"Phase 2: Localising to {lang}...")
        lang_key = f"voiceover_{lang.lower()[:2]}"

        for scene in script["scenes"]:
            en_text = scene.get("voiceover_en", "")
            if not en_text:
                scene[lang_key] = ""
                continue

            msg = client.messages.create(
                model="claude-opus-4-5",
                max_tokens=500,
                messages=[{
                    "role": "user",
                    "content": TRANSLATE_PROMPT.format(
                        language=lang,
                        region=config.REGION_LABEL,
                        text=en_text,
                    ),
                }],
            )
            scene[lang_key] = msg.content[0].text.strip()

        log(f"Phase 2: {lang} localisation complete.")

    return script


def save_script(script: dict, topic_id: int) -> str:
    os.makedirs(config.SCRIPTS_DIR, exist_ok=True)
    path = f"{config.SCRIPTS_DIR}/script_{topic_id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(script, f, indent=2, ensure_ascii=False)
    log(f"Phase 2: Script saved → {path}")
    return path
