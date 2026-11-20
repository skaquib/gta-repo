"""
run_gk_spit_hindi_short.py — Hindi version of run_gk_spit_short.py.

Why (data, 2026-10-23): India is the channel's #1 country (~25% of views),
and the two biggest hits in this exact format were Hindi -- "Why are
football gloves sticky" 11.7M and "Why do players sniff the tennis ball"
30M (SG Factree, Hindi narration, English title). The English goalkeeper
Short hit the usual ~1.1K ceiling in its first 24h.

Built with no paid API: reuses the English Short's Veo clips (our own
original footage) and narrates with local Kokoro TTS (hm_omega). Hindi
captions use the bundled Noto Sans Devanagari font. Same verified facts as
the English version (see its docstring). The script says "ग्लव्स" 5 times
for the count-the-word ending.
"""
import config

config.assert_safe_pipeline()
config.PERSONA_SIGNOFF_HI = ""  # format ends on the comment prompt

import gemini_studio as gs
from run_gk_spit_short import SCENES

VIDEO_ID = "gk_spit_hindi_short"

SCRIPT = {
    "lang": "hi",
    "hook": "गोलकीपर अपने ग्लव्स पर थूकते क्यों हैं?",
    "body": (
        "देखने में गंदा लगता है, पर ये साइंस है। ग्लव्स की हथेली लेटेक्स फोम से बनी होती है, "
        "और सूखा लेटेक्स सख्त और फिसलन भरा हो जाता है। गीला करते ही ये नरम होकर बॉल से "
        "चिपक जाता है, इसलिए बॉल फिसलती नहीं। तभी ग्लव्स बनाने वाली कंपनियां खुद कहती हैं, "
        "हर मैच से पहले ग्लव्स गीले करो।"
    ),
    "cta": "तो बताओ, मैंने कितनी बार ग्लव्स बोला? कमेंट में नंबर लिखो!",
    "title": "Why Goalkeepers Spit on Their Gloves? गोलकीपर ग्लव्स पर क्यों थूकते हैं 🧤 #shorts",
    "tags": ["goalkeeper", "goalkeeper gloves", "football facts in hindi", "football facts",
             "गोलकीपर", "फुटबॉल", "hindi facts", "football", "shorts"],
    "seo_description": (
        "गोलकीपर अपने ग्लव्स पर थूकते या पानी डालते हैं क्योंकि सूखा लेटेक्स सख्त और फिसलन भरा "
        "होता है -- गीला लेटेक्स बॉल को पकड़ता है। Why goalkeepers wet their gloves, explained "
        "in Hindi. #football #goalkeeper #shorts"
    ),
    "cut_seconds": 1.3,
    "ai_generated_visuals": True,
}

if __name__ == "__main__":
    gs.build_short(SCRIPT, SCENES, VIDEO_ID, voice="hm_omega", voice_engine="kokoro",
                   clips_from="gk_spit_short")
