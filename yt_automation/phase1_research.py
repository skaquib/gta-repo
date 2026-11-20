"""
Phase 1 — Strategic Topic Research
Uses Claude to identify 5 trending, low-competition animation topics.
Returns a list of topic dicts with title, keywords, hook angle.
"""

import json
import anthropic
import config
from logger import log

client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)


RESEARCH_PROMPT = """You are a YouTube growth strategist specializing in educational animation channels.

Channel niche: {niche}
Target region: {region}
Channel name: {channel}

Analyze current trending topics for educational/infographic animation on YouTube for {region}.
Identify exactly 5 high-demand, low-competition topics.

Requirements for each topic:
- Evergreen or trending (not breaking news)
- Suitable for infographic/animation format (no face needed)
- High CPM potential (history, science, psychology, finance, geopolitics, mysteries)
- Not already saturated by top channels

Return ONLY valid JSON, no markdown, no explanation. Format:
{{
  "topics": [
    {{
      "id": 1,
      "title": "viral-potential YouTube title (under 60 chars)",
      "subject": "one-line topic description",
      "category": "History|Science|Psychology|Finance|Geopolitics|Mystery",
      "keywords": ["keyword1", "keyword2", "keyword3"],
      "hook_angle": "what makes this emotionally compelling",
      "estimated_cpm_usd": 12,
      "competition_level": "low|medium"
    }}
  ]
}}"""


RESEARCH_PROMPT_SHORTS = """You are a YouTube growth strategist specializing in viral football/soccer YouTube Shorts.

Channel niche: {niche}
Target region: {region}
Channel name: {channel}

Analyze current trending topics and viral hooks about FIFA, the World Cup 2026, soccer history, player dramas, and mind-blowing football mysteries for {region}.
Identify exactly 5 high-demand, low-competition topics.

Requirements for each topic:
- High viral potential on YouTube Shorts (fast pacing, controversial or mind-blowing facts, player debates, underdog stories)
- Suitable for faceless kinetic text and stylized graphical/visual format
- Not already saturated by top channels

Return ONLY valid JSON, no markdown, no explanation. Format:
{{
  "topics": [
    {{
      "id": 1,
      "title": "viral-potential YouTube title (under 50 chars, hooks instantly)",
      "subject": "one-line topic description",
      "category": "FIFA World Cup|Football Trivia|Player Secrets|Mysteries",
      "keywords": ["keyword1", "keyword2", "keyword3"],
      "hook_angle": "what makes the first 3 seconds of the Short impossible to scroll away from",
      "estimated_cpm_usd": 6,
      "competition_level": "low|medium"
    }}
  ]
}}"""


def research_topics() -> list[dict]:
    log("Phase 1: Researching trending topics...")

    if getattr(config, "VIDEO_TYPE", "long") == "shorts":
        prompt = RESEARCH_PROMPT_SHORTS.format(
            niche=config.CHANNEL_NICHE,
            region=config.REGION_LABEL,
            channel=config.CHANNEL_NAME,
        )
    else:
        prompt = RESEARCH_PROMPT.format(
            niche=config.CHANNEL_NICHE,
            region=config.REGION_LABEL,
            channel=config.CHANNEL_NAME,
        )

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()

    try:
        data = json.loads(raw)
        topics = data["topics"]
        log(f"Phase 1 complete — {len(topics)} topics found:")
        for t in topics:
            log(f"  [{t['category']}] {t['title']} | CPM est. ${t['estimated_cpm_usd']}")
        return topics
    except json.JSONDecodeError as e:
        log(f"Phase 1 ERROR: Could not parse JSON — {e}")
        log(f"Raw response: {raw[:300]}")
        raise


def pick_best_topic(topics: list[dict]) -> dict:
    scored = sorted(
        topics,
        key=lambda t: (
            t.get("estimated_cpm_usd", 0) * (1 if t.get("competition_level") == "low" else 0.7)
        ),
        reverse=True,
    )
    best = scored[0]
    log(f"Phase 1: Selected topic — '{best['title']}'")
    return best
