import os
import socket
import sys
from dotenv import load_dotenv

load_dotenv()

# Owner, 2026-11-04: "make sure not use paid credit now whatever happen".
# Paid AI keys are removed from this process before any module can read them: the AI Studio
# prepaid key (GEMINI_API_KEY / GOOGLE_API_KEY) and the AWS Bedrock key. Google AI runs only on
# the Vertex free credit (genai_clients.py, which also enforces a spending cap below the credit).
PAID_KEYS_BLOCKED = [k for k in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "BEDROCK_API_KEY", "BEDROCK_KEY_FILE")
                     if os.environ.pop(k, None) is not None]

# --- Force IPv4 for all outbound sockets -------------------------------
# Reproduced live 2026-09-12: every googleapis.com call died with
# WinError 10060 while general internet was healthy (4ms to 8.8.8.8).
# Cause: this host resolves googleapis.com to an IPv6 address
# (2001:4860:4847:400::) it has no working route to, so every upload,
# analytics read and caption push hung until timeout. IPv4 to the same
# host answers in 5ms. Google publishes AAAA records everywhere, so this
# is not specific to one endpoint -- pin the whole process to IPv4.
# Set YT_ALLOW_IPV6=1 in .env to opt back out if the route is ever fixed.
FORCE_IPV4 = os.getenv("YT_ALLOW_IPV6", "0") != "1"

if FORCE_IPV4 and not getattr(socket, "_ipv4_forced", False):
    _orig_getaddrinfo = socket.getaddrinfo

    def _getaddrinfo_v4(host, port, family=0, *args, **kwargs):
        return _orig_getaddrinfo(host, port, socket.AF_INET, *args, **kwargs)

    socket.getaddrinfo = _getaddrinfo_v4
    socket._ipv4_forced = True

ANTHROPIC_API_KEY     = os.getenv("ANTHROPIC_API_KEY")
BEDROCK_API_KEY       = os.getenv("BEDROCK_API_KEY", "")
ELEVENLABS_API_KEY    = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID   = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
SHOTSTACK_API_KEY     = os.getenv("SHOTSTACK_API_KEY")
SHOTSTACK_ENV         = os.getenv("SHOTSTACK_ENV", "stage")
YOUTUBE_CLIENT_SECRETS = os.getenv("YOUTUBE_CLIENT_SECRETS", "client_secrets.json")
YOUTUBE_CHANNEL_ID    = os.getenv("YOUTUBE_CHANNEL_ID")
RUMBLE_API_KEY        = os.getenv("RUMBLE_API_KEY", "")
TIKTOK_ACCESS_TOKEN   = os.getenv("TIKTOK_ACCESS_TOKEN", "")
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
INSTAGRAM_ACCOUNT_ID  = os.getenv("INSTAGRAM_ACCOUNT_ID", "")
PIXABAY_API_KEY       = os.getenv("PIXABAY_API_KEY", "")
PEXELS_API_KEY        = os.getenv("PEXELS_API_KEY") or os.getenv("PEXEL_API_KEY")  # accept both spellings -- .env uses PEXEL_API_KEY (no S)
HF_TOKEN              = os.getenv("HF_TOKEN", "")
FOOTBALL_DATA_API_URL = os.getenv("FOOTBALL_DATA_API_URL", "")  # optional, for match_calendar.py
FOOTBALL_DATA_API_KEY = os.getenv("FOOTBALL_DATA_API_KEY", "")
CHANNEL_NAME          = os.getenv("CHANNEL_NAME", "FramedFacts")
# Owner, 2026-10-24: FramedFacts is a facts channel shown in 3D -- any topic.
CHANNEL_NICHE         = os.getenv("CHANNEL_NICHE", "Facts you can see, in 3D -- what's inside animals and objects, how things work, how things are made, the human body, science and space")
# YouTube category for uploads (27 = Education, 28 = Science & Technology,
# 17 = Sports). A script can override with SCRIPT["category_id"].
VIDEO_CATEGORY_ID     = os.getenv("VIDEO_CATEGORY_ID", "27")

# On-screen/narrated persona -- the named, recurring "host" voice for the
# channel brand above. Consistency here (same name, same sign-off, same
# voice) is what turns "an AI account posting facts" into "a creator with
# a POV," per the persona/commentary/format/cadence growth framework.
PERSONA_NAME    = os.getenv("PERSONA_NAME", "Alex Rivera")
PERSONA_SIGNOFF = os.getenv("PERSONA_SIGNOFF", "I'm {name}, catch you in the next one.")
# Hindi sign-off for translated videos -- kept separate so a Hindi CTA never
# gets an English phrase stitched onto the end of it (see _with_persona_signoff).
PERSONA_SIGNOFF_HI = os.getenv("PERSONA_SIGNOFF_HI", "main hoon {name}, agli video mein milte hain.")
TARGET_REGION         = os.getenv("TARGET_REGION", "IN")
TARGET_LANGUAGES      = os.getenv("TARGET_LANGUAGES", "Hindi,English,Spanish").split(",")
VIDEO_TYPE            = os.getenv("VIDEO_TYPE", "shorts")
BG_MUSIC_URL          = os.getenv("BG_MUSIC_URL", "https://raw.githubusercontent.com/effacestudios/Royalty-Free-Music-Pack/master/Sports%20Spirit.mp3")


REGION_NAMES = {"IN": "India", "US": "United States", "BR": "Brazil", "GB": "United Kingdom"}
REGION_LABEL = REGION_NAMES.get(TARGET_REGION, TARGET_REGION)

OUTPUT_DIR  = "output"
SCRIPTS_DIR = f"{OUTPUT_DIR}/scripts"
AUDIO_DIR   = f"{OUTPUT_DIR}/audio"
VIDEOS_DIR  = f"{OUTPUT_DIR}/videos"
LOGS_DIR    = f"{OUTPUT_DIR}/logs"
# "footage" (real, tag-matched Pexels/Pixabay stock clips -- current default:
# AnimateDiff's local-SD1.5 output was rated unusable for the 2-second hook
# window real footage of recognizable action wins instantly) or "ai_animation"
# (AnimateDiff-generated clips -- triggers YouTube's Altered Content label).
VISUAL_STYLE = os.getenv("VISUAL_STYLE", "footage")
USE_GIT_ASSETS = os.getenv("USE_GIT_ASSETS", "false").lower() == "true"
VIRAL_VIEW_THRESHOLD = int(os.getenv("VIRAL_VIEW_THRESHOLD", "1000000"))
DOUBLE_DOWN_THRESHOLD = int(os.getenv("DOUBLE_DOWN_THRESHOLD", "50000"))

# "private", "unlisted", or "public" — controls YouTube upload visibility and
# gates whether Rumble auto-publishes. Keep "private" until videos are reviewed.
UPLOAD_PRIVACY        = os.getenv("UPLOAD_PRIVACY", "private")
LOOP_INTERVAL_MINUTES = int(os.getenv("LOOP_INTERVAL_MINUTES", "150"))

# "immediate" publishes on upload; "scheduled" sets publishAt and uploads private
# until that time (see phase5_upload.upload_to_youtube).
SCHEDULE_MODE = os.getenv("SCHEDULE_MODE", "immediate")

# 0.0-1.0: how much of the beat-synced "aura-freeze" (speed ramp + monochrome
# freeze on the hook segment) to apply. 0 disables it entirely.
FREEZE_INTENSITY = float(os.getenv("FREEZE_INTENSITY", "1.0"))

_SAFE_VISUAL_STYLES = {"ai_animation", "footage"}


def assert_safe_pipeline():
    """
    Fail loudly at startup if anything points back at the deprecated
    real-broadcast-footage-download path (see deprecated/). All active content
    sources must be either AI-generated or licensed/royalty-free stock
    (git asset library, Pexels, Pixabay) — never downloaded broadcast footage.
    """
    if VISUAL_STYLE not in _SAFE_VISUAL_STYLES:
        raise RuntimeError(
            f"config.VISUAL_STYLE={VISUAL_STYLE!r} is not a recognized safe style "
            f"({_SAFE_VISUAL_STYLES}). Refusing to start."
        )
    if os.getenv("USE_REAL_FOOTAGE", "false").lower() == "true":
        raise RuntimeError(
            "USE_REAL_FOOTAGE=true is set in the environment. Downloading real "
            "broadcast footage and evading Content ID risks channel termination "
            "under YouTube's Reused Content and Community Guidelines policies. "
            "This path has been removed — unset USE_REAL_FOOTAGE."
        )
    for banned_module in ("auto_shorts_creator", "generate_worldcup_short", "generate_viral_short"):
        if banned_module in sys.modules:
            raise RuntimeError(
                f"Deprecated module '{banned_module}' is loaded. It downloads real "
                "broadcast footage and evades Content ID — do not import it."
            )


