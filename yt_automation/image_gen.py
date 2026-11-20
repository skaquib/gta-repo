"""
image_gen.py — One call for "make this image", with fallbacks:

  1. Google image models (genai_clients.py): Vertex AI on the GCP Free Credit first,
     then the AI Studio key (GEMINI_API_KEY) -- about $0.034-0.067 per image
  2. Amazon Bedrock -- Stability Stable Image Ultra (best, ~$0.14/image),
     falling back to SD3.5 Large (~$0.08) and Stable Image Core (~$0.04).
     (Amazon Nova Canvas / Titan are end-of-life on Bedrock as of 2026-10.)

Bedrock key: BEDROCK_API_KEY from the environment (must start with "ABSK"),
or -- only when a run explicitly sets BEDROCK_KEY_FILE -- the "API key"
column of that CSV (owner authorized the repo's key file on 2026-10-25).

generate(prompt, out_path) -> out_path (cached: an existing file is reused).
Raises RuntimeError listing why every backend failed.
"""
import os
import json
import base64

import requests

SAFE_SUFFIX = ("vertical 9:16, no text, no letters, no watermark, no logos, "
               "no recognizable real people")


def _gemini(prompt, out_path, aspect="9:16"):
    """Google image models: Vertex AI (paid by the GCP Free Credit) first, then the AI Studio key."""
    from google.genai import types
    import genai_clients
    routes = genai_clients.clients()
    if not routes:
        raise RuntimeError("no Google AI route (GCP_SA_KEY_JSON + GCP_PROJECT_ID, or GEMINI_API_KEY)")
    errors = []
    import time
    for name, client in routes:
        last = None
        for model in ("gemini-3.1-flash-image", "gemini-3-pro-image", "gemini-3.1-flash-lite-image", "gemini-2.5-flash-image"):
            for attempt in range(6):
                try:
                    genai_clients.charge("image", 1, os.path.basename(out_path))
                    r = client.models.generate_content(
                        model=model, contents=prompt,
                        config=types.GenerateContentConfig(response_modalities=["IMAGE"],
                                                           image_config=types.ImageConfig(aspect_ratio=aspect)))
                    part = next(p for p in r.candidates[0].content.parts if p.inline_data)
                    with open(out_path, "wb") as f:
                        f.write(part.inline_data.data)
                    print(f"[image_gen] {os.path.basename(out_path)} via {name}/{model}")
                    return out_path
                except Exception as e:
                    last = e
                    if name == "vertex" and ("429" in str(e) or "RESOURCE_EXHAUSTED" in str(e)):
                        time.sleep(15 * (attempt + 1))     # per-minute limit: wait and retry on the FREE route
                        continue
                    break
            if "402" in str(last) or "PERMISSION_DENIED" in str(last):
                break   # this route can't pay or isn't allowed -- other models on it won't help
        if name == "vertex":                      # Imagen is Vertex-only and GA: try it before leaving the free credit
            for model in ("imagen-4.0-generate-001", "imagen-4.0-fast-generate-001"):
                try:
                    r = client.models.generate_images(model=model, prompt=prompt,
                                                      config=types.GenerateImagesConfig(number_of_images=1, aspect_ratio=aspect))
                    with open(out_path, "wb") as f:
                        f.write(r.generated_images[0].image.image_bytes)
                    return out_path
                except Exception as e:
                    last = e
        errors.append(f"{name}: {str(last)[:120]}")
    raise RuntimeError("gemini: " + " | ".join(errors))


def _bedrock_key():
    key = os.getenv("BEDROCK_API_KEY", "").strip()
    if key.startswith("ABSK"):
        return key
    path = os.getenv("BEDROCK_KEY_FILE", "")
    if path and os.path.exists(path):
        import csv
        rows = list(csv.reader(open(path)))
        if len(rows) > 1 and rows[1][-1].strip().startswith("ABSK"):
            return rows[1][-1].strip()
    raise RuntimeError("bedrock: no valid key (BEDROCK_API_KEY must start with ABSK, or set BEDROCK_KEY_FILE)")


BEDROCK_IMAGE_MODELS = ["stability.stable-image-ultra-v1:1", "stability.sd3-5-large-v1:0",
                        "stability.stable-image-core-v1:1"]


def _bedrock_stability(prompt, out_path, region="us-west-2"):
    key = _bedrock_key()
    last = None
    for model in BEDROCK_IMAGE_MODELS:
        body = {"prompt": prompt[:2000], "aspect_ratio": "9:16", "output_format": "png",
                "negative_prompt": "text, letters, words, watermark, logo, blurry, deformed, extra limbs"}
        r = requests.post(f"https://bedrock-runtime.{region}.amazonaws.com/model/{model}/invoke",
                          headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                                   "Accept": "application/json"},
                          data=json.dumps(body), timeout=180)
        if r.status_code == 200:
            data = r.json()
            reasons = data.get("finish_reasons") or [None]
            if reasons[0] not in (None, "SUCCESS"):
                last = f"{model}: filtered ({reasons[0]})"
                continue
            with open(out_path, "wb") as f:
                f.write(base64.b64decode(data["images"][0]))
            return out_path
        last = f"{model}: {r.status_code} {r.text[:120]}"
    raise RuntimeError(f"bedrock: {last}")


def generate(prompt, out_path):
    if os.path.exists(out_path) and os.path.getsize(out_path) > 10_000:
        return out_path
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    full = f"{prompt} {SAFE_SUFFIX}"
    errors = []
    for backend in (_gemini, _bedrock_stability):
        try:
            return backend(full, out_path)
        except Exception as e:
            errors.append(str(e))
    raise RuntimeError("no image backend available -> " + " | ".join(errors))


def available():
    """Cheap check (no image generated): which backends look usable."""
    ok = {}
    try:
        from google import genai
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))   # keep a reference:
        client.models.generate_content(model="gemini-3.5-flash", contents="ok")  # inline clients get closed
        ok["gemini"] = True
    except Exception as e:
        ok["gemini"] = str(e)[:80]
    try:
        _bedrock_key()
        ok["bedrock_key"] = True
    except Exception as e:
        ok["bedrock_key"] = str(e)[:80]
    return ok


if __name__ == "__main__":
    print(available())
