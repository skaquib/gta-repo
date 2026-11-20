"""
run_goal_width_hindi_short.py — Hindi-VOICE experiment on a new topic.

Experiment (2026-10-23): India is ~25% of the channel's views and the
format's biggest hits were Hindi-narrated. This Short changes ONE variable
against the English uploads: the narration is Hindi (local Kokoro TTS).
Everything a viewer reads stays in standard Latin letters: English title,
description and hook headline; captions are Roman-letter Hinglish so they
stay word-for-word in sync with the Hindi voice (caption_text).

Topic: "why EXACTLY" shape, which gave the channel's best-ever retention
(bowling lane, 0.63 relative). Facts (checked 2026-10-23): the FA's 1863
laws put the posts 8 yards apart -- historians don't know why 8 (appears
arbitrary); the first laws set no height, shots over the top caused
disputes, so a tape was strung at 8 feet (1866 FA rules); a wooden crossbar
later replaced the tape (sources disagree on the year, 1875-1883, so none is
stated). Sources: sheffieldhomeoffootball.org, leicestershirefootballarchive.com,
bundesliga.com, voor.sport.

Built with no paid API (Gemini credits were depleted): reuses this
channel's own previously generated AI clips/images.
"""
import os
import config

config.assert_safe_pipeline()
config.PERSONA_SIGNOFF = ""  # format ends on the comment prompt

import gemini_studio as gs

VIDEO_ID = "goal_width_hindi_short"

HOOK_HI = "फुटबॉल का गोल ठीक आठ गज चौड़ा क्यों होता है?"
HOOK_RO = "Football ka goal theek aath gaj chauda kyun hota hai?"
BODY_HI = ("अठारह सौ तिरसठ में इंग्लैंड ने पहले नियम लिखे, और पोस्ट आठ गज दूर रख दिए। "
           "क्यों आठ? आज तक कोई पक्का नहीं जानता। ऊंचाई का तो कोई नियम ही नहीं था, "
           "तो झगड़े होते थे। इसलिए आठ फुट पर एक टेप बांधा गया, जो बाद में लकड़ी का क्रॉसबार बना।")
BODY_RO = ("~ ~ 1863 mein England ne pehle niyam likhe, aur post aath gaj door rakh diye. "
           "Kyun aath? Aaj tak koi pakka nahi jaanta. Oonchai ka to koi niyam hi nahi tha, "
           "to jhagde hote the. Isliye aath foot par ek tape baandha gaya, jo baad mein lakdi ka crossbar bana.")
CTA_HI = "तो बताओ, क्या गोल और बड़ा होना चाहिए? कमेंट करो!"
CTA_RO = "To batao, kya goal aur bada hona chahiye? Comment karo!"

for hi, ro in ((HOOK_HI, HOOK_RO), (BODY_HI, BODY_RO), (CTA_HI, CTA_RO)):
    assert len(hi.split()) == len(ro.split()), (len(hi.split()), len(ro.split()), ro)

SCRIPT = {
    "lang": "en",          # title/description/on-screen text language
    "audio_lang": "hi",    # narration language (Kokoro voice + YouTube audio language)
    "hook": HOOK_HI,
    "body": BODY_HI,
    "cta": CTA_HI,
    "caption_text": f"{HOOK_RO} {BODY_RO} {CTA_RO}",
    "caption_lang": "hi-Latn",   # uploaded subtitle track: Hindi in Latin letters
    "caption_name": "Hinglish",
    "hook_card": "WHY IS A GOAL EXACTLY 8 YARDS WIDE?",
    "title": "Why Is a Football Goal EXACTLY 8 Yards Wide? ⚽ #shorts",
    "tags": ["football goal size", "8 yards", "football history", "football facts",
             "soccer facts", "why", "crossbar", "football", "soccer", "shorts"],
    "seo_description": (
        "Football's first rules in 1863 put the goalposts 8 yards apart -- and nobody really knows "
        "why 8. There was no height rule at all, so after arguments a tape was strung at 8 feet, "
        "later replaced by the wooden crossbar. #football #soccer #shorts"
    ),
    "cut_seconds": 1.3,
    "ai_generated_visuals": True,
}

# Narration order, from this channel's own previously generated AI assets.
_A = gs.AI_DIR
CLIPS = [os.path.join(_A, f) for f in (
    "barca_record_short_1.mp4",   # ball into the top corner -- the goal
    "barca_record_short_3.mp4",   # 1960s black-and-white stadium -- the old rules
    "barca_record_short_5.mp4",   # lone ball on the centre spot -- "nobody knows why"
    "gk_spit_short_veo4.mp4",     # keeper diving under the bar -- height disputes
    "barca_record_short_0.mp4",   # packed stadium -- the modern game
    "barca_record_short_4.mp4",   # split crowd -- comment debate
)]

if __name__ == "__main__":
    gs.build_short(SCRIPT, [], VIDEO_ID, voice="hm_omega", voice_engine="kokoro",
                   clip_paths=CLIPS)
