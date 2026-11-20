"""
genai_clients.py — which Google AI account pays for image/video generation.

Two routes to the same Google models (Gemini image, Imagen, Veo):

1. Vertex AI (Google Cloud), paid by the billing account's GCP Free Credit.
   The owner's account had ~Rs 28,569 of it on 2026-11-04, expiring 2027-02-03.
   That credit is "not applicable to Gemini API" (AI Studio), so it only reaches
   the models through Vertex AI. Needs, in the environment (never in chat or git):
     GCP_SA_KEY_B64   the service-account key file, base64-encoded on one line (easiest to paste into
                      the environment settings), or GCP_SA_KEY_JSON with the raw JSON. The account needs
                      the "Agent Platform user" role (Vertex AI was renamed Agent Platform in 2026; the
                      role is still roles/aiplatform.user)
     GCP_PROJECT_ID   the project the key belongs to (linked to the billing account with the credit)
     GCP_LOCATION     optional, default "global"
2. Gemini API (AI Studio), paid by prepaid AI Studio credit: PERMANENTLY DISABLED. The owner said
   never use paid credit, whatever happens; the key is stripped from the environment.

vertex_client() / studio_client() return a google-genai Client or None. clients() returns only
the free Vertex route unless the paid route is explicitly allowed.
"""
import datetime
import json
import os
import threading

# Never spend paid credit (owner, 2026-11-04): drop the paid keys even if config wasn't imported first.
for _k in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "BEDROCK_API_KEY", "BEDROCK_KEY_FILE"):
    os.environ.pop(_k, None)

_cache = {}

# ── free-credit spending cap ──────────────────────────────────────────────────
# The GCP Free Credit (~Rs 28,569 = ~$320, expires 2027-02-03) pays for Vertex AI. Once it is used up,
# Google would bill the card, which is paid money, so every Vertex job is booked here with a
# CONSERVATIVE price and refused once the booked total reaches CAP_USD (well below the credit).
CAP_USD = 260.0
PRICE_USD = {"image": 0.05, "veo-lite-s": 0.08, "veo-fast-s": 0.15, "veo-std-s": 0.50, "text": 0.001,
             "tts-char": 0.00006}     # Chirp 3 HD list ~$30 per 1M characters; booked at 2x to stay safe
LEDGER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "free_credit_ledger.json")


_lock = threading.Lock()


def _ledger():
    """The booked spend. A missing file starts at zero; an unreadable one STOPS the job: resetting the
    total to zero would silently switch off the cap (this happened once when parallel image threads
    read a half-written file)."""
    if not os.path.exists(LEDGER):
        return {"spent_usd": 0.0, "entries": []}
    with open(LEDGER) as f:
        return json.load(f)              # ValueError propagates on purpose


def spent_usd():
    with _lock:
        return _ledger()["spent_usd"]


def charge(kind, units=1.0, note=""):
    """Book an estimated cost BEFORE a Vertex job runs; raises if the cap would be passed.
    Safe across threads (lock) and processes (flock), written atomically (temp file + rename)."""
    import fcntl
    with _lock, open(LEDGER + ".lock", "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        led = _ledger()
        cost = PRICE_USD[kind] * units
        if led["spent_usd"] + cost > CAP_USD:
            raise RuntimeError(f"FREE-CREDIT CAP: booked ${led['spent_usd']:.2f} + ${cost:.2f} would pass ${CAP_USD:.0f}. "
                               "Stopping so nothing is billed to the card.")
        led["spent_usd"] = round(led["spent_usd"] + cost, 4)
        led["entries"].append([datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M"), kind, units, round(cost, 4), note[:60]])
        tmp = LEDGER + ".tmp"
        with open(tmp, "w") as f:
            json.dump(led, f, indent=0)
        os.replace(tmp, LEDGER)
        return cost


def _sa_key_json():
    """The service-account key JSON from GCP_SA_KEY_B64 (base64, one line) or GCP_SA_KEY_JSON (raw)."""
    b64 = os.getenv("GCP_SA_KEY_B64", "").strip()
    if b64:
        import base64
        b64 = "".join(b64.split())                      # tolerate spaces or line breaks from pasting
        return base64.b64decode(b64 + "=" * (-len(b64) % 4)).decode("utf-8-sig")
    return os.getenv("GCP_SA_KEY_JSON", "").strip()


def vertex_client(location=None):
    """Vertex AI client. Gemini models use the "global" endpoint; Veo and Imagen need a region
    (pass location="us-central1")."""
    loc = location or os.getenv("GCP_LOCATION", "global")
    key = f"vertex:{loc}"
    if key in _cache:
        return _cache[key]
    raw, project = _sa_key_json(), os.getenv("GCP_PROJECT_ID", "").strip()
    client = None
    if raw and project:
        from google import genai
        from google.oauth2 import service_account
        creds = service_account.Credentials.from_service_account_info(
            json.loads(raw), scopes=["https://www.googleapis.com/auth/cloud-platform"])
        client = genai.Client(vertexai=True, project=project, location=loc, credentials=creds)
    _cache[key] = client
    return client


def studio_client():
    """The paid AI Studio route is permanently disabled (owner: never use paid credit)."""
    return None


def cloud_tts(text, voice="en-US-Chirp3-HD-Charon", rate=1.0, cache_dir=None):
    """Natural narration from Google Cloud Text-to-Speech (Chirp 3 HD) on the free credit.
    Returns (float32 mono samples, sample_rate). Cached on disk by text+voice+rate."""
    import base64
    import hashlib
    import io
    import numpy as np
    import soundfile as sf
    from google.oauth2 import service_account
    from google.auth.transport.requests import AuthorizedSession
    key = hashlib.sha1(f"{voice}|{rate}|{text}".encode()).hexdigest()[:16]
    path = os.path.join(cache_dir, f"tts_{key}.wav") if cache_dir else None
    if path and os.path.exists(path):
        a, sr = sf.read(path, dtype="float32")
        return a, sr
    # Owner, 2026-11-19: the free credit is ONLY for visuals (anime pictures and clips). Voices use the free local
    # Kokoro voices, like the Shorts. Lines recorded before this rule stay usable from the cache above.
    raise RuntimeError("Google voice is off (owner rule: free credit only for visuals). Use a Kokoro voice such as "
                       "'am_michael', 'bm_george' or 'am_puck'.")
    charge("tts-char", len(text), voice)
    creds = service_account.Credentials.from_service_account_info(
        json.loads(_sa_key_json()), scopes=["https://www.googleapis.com/auth/cloud-platform"])
    body = {"input": {"text": text}, "voice": {"languageCode": voice[:5], "name": voice},
            "audioConfig": {"audioEncoding": "LINEAR16", "sampleRateHertz": 24000, "speakingRate": rate}}
    r = AuthorizedSession(creds).post("https://texttospeech.googleapis.com/v1/text:synthesize", json=body, timeout=60)
    r.raise_for_status()
    a, sr = sf.read(io.BytesIO(base64.b64decode(r.json()["audioContent"])), dtype="float32")
    if a.ndim > 1:
        a = a.mean(axis=1)
    if path:
        os.makedirs(cache_dir, exist_ok=True)
        sf.write(path, a, sr)
    return a, sr


def clients():
    """[(name, client)]: only the free-credit Vertex AI route, ever."""
    v = vertex_client()
    return [("vertex", v)] if v else []


if __name__ == "__main__":
    # Smoke test: one tiny text call on the free route (fractions of a cent), no secrets printed.
    print(f"free-credit booked so far: ${spent_usd():.2f} of the ${CAP_USD:.0f} cap")
    for name, c in clients():
        try:
            r = c.models.generate_content(model="gemini-3.5-flash-lite", contents="Reply with the single word OK.")
            print(f"{name}: WORKS ({r.text.strip()[:10]})")
        except Exception as e:
            print(f"{name}: FAILS ({str(e)[:160]})")
    if not clients():
        print("no route configured (set GCP_SA_KEY_B64 + GCP_PROJECT_ID, or GEMINI_API_KEY)")
