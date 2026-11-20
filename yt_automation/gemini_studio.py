"""
gemini_studio.py — Visuals, voice and caption timing using only the Gemini API.

Works on hosts where Pexels/Pixabay/ElevenLabs/Edge-TTS/Hugging Face are
unreachable (cloud sessions) -- one GEMINI_API_KEY covers everything:
  - generate_veo_clips():   real-motion 9:16 clips (Veo) -> output/ai_images/
  - generate_image_clips(): still scenes (Gemini image) + Ken Burns zoom
  - gemini_voiceover():     Gemini TTS narration as .wav (assemblers expect .wav)
  - cache_word_timestamps(): caption timing by aligning the known script text
                            to the voiced parts of the audio (no ASR model needed)

All outputs land in output/ai_images/, one of copyright_compliance's
SAFE_ASSET_SUBDIRS. Scripts using these visuals should set
"ai_generated_visuals": True so the upload carries YouTube's altered-content
label.
"""
import os
import json
import time
import wave

import config
from google import genai
from google.genai import types

import pro_shorts_creator as psc
from logger import log

AI_DIR = os.path.join(config.OUTPUT_DIR, "ai_images")

# Appended to every visual prompt: no real people's likeness, no branding,
# no garbled AI text.
SAFE_STYLE = ("Cinematic, photorealistic, vertical 9:16 composition, no text, no logos, "
              "no club crests, no recognizable real people, faces not visible.")

import genai_clients
# Free-credit Vertex AI first (GCP_SA_KEY_B64 + GCP_PROJECT_ID), else the AI Studio key.
_client = genai_clients.vertex_client() or genai.Client(api_key="")   # free Vertex route only, never the paid key
# Veo on Vertex AI needs a regional endpoint (tested 2026-11-04: veo-3.1-fast-generate-001 works on the free credit).
_video = genai_clients.vertex_client("us-central1")


def generate_veo_clips(scenes: list, video_id: str, model: str = None, aspect: str = "9:16",
                       seconds: int = 8, images: list = None) -> list:
    """One Veo clip per scene prompt, submitted in parallel. Cached by filename, so re-runs only
    generate what's missing. images: optional list of still paths (same length as scenes) to
    animate (image-to-video keeps the look consistent with our stills). Returns paths in scene order."""
    client = _video or _client
    model = model or ("veo-3.1-fast-generate-001" if _video else "veo-3.1-fast-generate-preview")
    os.makedirs(AI_DIR, exist_ok=True)
    paths = [os.path.join(AI_DIR, f"{video_id}_veo{i}.mp4") for i in range(len(scenes))]
    ops = {}
    for i, scene in enumerate(scenes):
        if os.path.exists(paths[i]):
            continue
        try:
            cfg = dict(aspect_ratio=aspect, number_of_videos=1, duration_seconds=seconds)
            if _video:
                cfg.update(generate_audio=False, resolution="720p")   # our own narration/music go on top
            kw = {}
            if images and images[i]:
                kw["image"] = types.Image(image_bytes=open(images[i], "rb").read(), mime_type="image/png")
            style = SAFE_STYLE.replace("vertical 9:16 composition",
                                       "vertical 9:16 composition" if aspect == "9:16" else "widescreen 16:9 composition")
            if images and images[i]:
                style += " Keep every animal's anatomy, proportions and colours exactly as in the starting image."
            genai_clients.charge("veo-fast-s" if "fast" in model else ("veo-lite-s" if "lite" in model else "veo-std-s"),
                                 seconds, f"{video_id}/{i}")
            ops[i] = client.models.generate_videos(model=model, prompt=f"{scene} {style}",
                                                   config=types.GenerateVideosConfig(**cfg), **kw)
            log(f"  Veo scene {i} submitted")
        except Exception as e:
            log(f"  Veo scene {i} submit failed: {e}")
    deadline = time.time() + 900
    while ops and time.time() < deadline:
        time.sleep(10)
        for i, op in list(ops.items()):
            op = client.operations.get(op)
            if not op.done:
                ops[i] = op
                continue
            del ops[i]
            try:
                vid = op.response.generated_videos[0].video
                if getattr(vid, "video_bytes", None):           # Vertex AI returns the clip inline
                    with open(paths[i], "wb") as f:
                        f.write(vid.video_bytes)
                else:                                           # AI Studio returns a file to download
                    client.files.download(file=vid)
                    vid.save(paths[i])
                log(f"  Veo scene {i}: {paths[i]}")
            except Exception as e:
                log(f"  Veo scene {i} failed: {getattr(op, 'error', None) or e}")
    return [p for p in paths if os.path.exists(p)]


def generate_image_clips(scenes: list, video_id: str, duration: float = 8.0) -> list:
    """Gemini still image per scene -> Ken Burns clip. Cheaper than Veo."""
    os.makedirs(AI_DIR, exist_ok=True)
    clip_paths = []
    for i, scene in enumerate(scenes):
        img_path = os.path.join(AI_DIR, f"{video_id}_{i}.png")
        clip_path = os.path.join(AI_DIR, f"{video_id}_{i}.mp4")
        if not os.path.exists(img_path):
            for model in ("gemini-3.1-flash-image", "gemini-2.5-flash-image"):
                try:
                    r = _client.models.generate_content(
                        model=model, contents=f"{scene} {SAFE_STYLE}",
                        config=types.GenerateContentConfig(
                            response_modalities=["IMAGE"],
                            image_config=types.ImageConfig(aspect_ratio="9:16")))
                    part = next(p for p in r.candidates[0].content.parts if p.inline_data)
                    with open(img_path, "wb") as f:
                        f.write(part.inline_data.data)
                    log(f"  Image {i} ({model}): {img_path}")
                    break
                except Exception as e:
                    log(f"  Image {i} via {model} failed: {e}")
        if not os.path.exists(img_path):
            continue
        if not os.path.exists(clip_path):
            psc.make_athlete_photo_clip(img_path, clip_path, duration=duration)
        clip_paths.append(clip_path)
    return clip_paths


def spoken_text(script: dict) -> str:
    """Exactly what generate_voiceover()/assemble() treat as the narration."""
    s = psc._with_persona_signoff(script)
    hook = s["hook"].rstrip()
    sep = " " if hook[-1:] in ".?!" else ". "  # "gloves?. It" otherwise
    return f"{hook}{sep}{s['body']} {s['cta']}"


def gemini_voiceover(script: dict, video_id: str, voice: str = "Charon",
                     style: str = "Read this like an energetic, clear sports-facts narrator, quick pace",
                     fresh: bool = False) -> str:
    """Gemini TTS -> normalized .wav. Falls back to psc.generate_voiceover().
    Reuses an existing take unless fresh=True (re-renders keep the same voice)."""
    os.makedirs(config.AUDIO_DIR, exist_ok=True)
    out_wav = os.path.join(config.AUDIO_DIR, f"{video_id}_vo.wav")
    if os.path.exists(out_wav) and not fresh:
        log(f"Reusing voice take: {out_wav}")
        return out_wav
    try:
        r = _client.models.generate_content(
            model="gemini-2.5-pro-preview-tts",
            contents=f"{style}: {spoken_text(script)}",
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)))))
        pcm = r.candidates[0].content.parts[0].inline_data.data
        with wave.open(out_wav, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000)
            w.writeframes(pcm)
        log(f"Voice saved (Gemini TTS, {voice}): {out_wav}")
        return psc.normalize_voice(out_wav)
    except Exception as e:
        log(f"Gemini TTS failed ({e}) -- falling back to standard voice chain")
        return psc.generate_voiceover(script)


def kokoro_voiceover(script: dict, video_id: str, voice: str = "am_michael",
                     speed: float = 1.1, fresh: bool = False) -> str:
    """Local Kokoro TTS (free, no API, works offline) -> normalized .wav.
    Hindi scripts (script['lang'] == 'hi') default to the hm_omega voice.
    Model files: kokoro-v1.0.onnx + voices.bin next to this file, from
    github.com/thewh1teagle/kokoro-onnx/releases (model-files-v1.0)."""
    import soundfile as sf
    os.makedirs(config.AUDIO_DIR, exist_ok=True)
    out_wav = os.path.join(config.AUDIO_DIR, f"{video_id}_vo.wav")
    if os.path.exists(out_wav) and not fresh:
        log(f"Reusing voice take: {out_wav}")
        return out_wav
    hindi = script.get("audio_lang", script.get("lang")) == "hi"
    if hindi and voice.startswith("a"):
        voice = "hm_omega"
    k = psc._get_kokoro()
    samples, sr = k.create(spoken_text(script), voice=voice, speed=speed,
                           lang="hi" if hindi else "en-us")
    sf.write(out_wav, samples, sr)
    log(f"Voice saved (Kokoro, {voice}): {out_wav}")
    return psc.normalize_voice(out_wav)


def align_words_to_audio(vo_path: str, script: dict) -> list:
    """Offline aligner for when no ASR model is reachable: we know the exact
    narration text, so spread its words across the *voiced* parts of the
    audio in proportion to their length. Silences (sentence pauses) are
    skipped, so captions stay locked to speech instead of drifting the way
    a constant words-per-second estimate does."""
    import numpy as np
    import soundfile as sf
    tokens = spoken_text(script).split()
    data, sr = sf.read(vo_path, dtype="float32")
    if data.ndim > 1:
        data = data.mean(axis=1)
    hop = int(sr * 0.01)  # 10ms frames
    n = len(data) // hop
    rms = np.sqrt((data[: n * hop].reshape(n, hop) ** 2).mean(axis=1))
    voiced = rms > max(rms.max() * 0.04, 1e-4)
    # Close tiny gaps inside words (<120ms) so only real pauses are skipped.
    gap = 0
    for i in range(n):
        if voiced[i]:
            if 0 < gap < 12:
                voiced[i - gap:i] = True
            gap = 0
        else:
            gap += 1
    voiced_idx = np.flatnonzero(voiced)
    weights = np.array([len(t.strip(".,!?'\"")) + 2 for t in tokens], dtype=float)
    edges = np.concatenate([[0.0], np.cumsum(weights) / weights.sum()])
    pos = np.minimum((edges * len(voiced_idx)).astype(int), len(voiced_idx) - 1)
    frames = voiced_idx[pos]
    return [{"word": t, "start": round(float(frames[k]) * 0.01, 2), "end": round(float(frames[k + 1]) * 0.01, 2)}
            for k, t in enumerate(tokens)]


def cache_word_timestamps(vo_path: str, script: dict) -> list:
    """Write vo_path + '.words.json' -- the cache psc.get_word_timestamps()
    reads before trying faster-whisper."""
    words = align_words_to_audio(vo_path, script)
    # Store what's shown on screen (caption_text, same token count) so the
    # uploaded .srt track matches the burned-in captions, not the narration
    # script (e.g. Roman-letter captions over Hindi narration).
    shown = (script.get("caption_text") or "").split()
    if len(shown) == len(words):
        for w, s_ in zip(words, shown):
            w["word"] = s_
    with open(vo_path + ".words.json", "w", encoding="utf-8") as f:
        json.dump(words, f)
    log(f"Word timestamps from local energy alignment ({len(words)} words, "
        f"last word ends {words[-1]['end']:.1f}s)")
    return words


def build_short(script: dict, scenes: list, video_id: str, visuals: str = "veo",
                voice: str = "Puck", voice_engine: str = "gemini", clips_from: str = None,
                clip_paths: list = None,
                style: str = ("Read this like a fast, punchy, curious sports-facts Shorts narrator, "
                              "about 3.5 words per second, no long pauses")) -> tuple:
    """Full build for a Gemini-visual Short: scenes -> voice -> caption
    timing -> music -> compliance gate -> assemble. visuals="veo" (real
    motion, costs the most Gemini credit) or "images" (stills + Ken Burns,
    much cheaper). voice_engine="kokoro" uses free local TTS (voice is then a
    Kokoro voice id). clips_from reuses another video's cached clips (e.g. a
    Hindi version of an English Short); clip_paths uses an explicit list of
    existing clips instead of generating any. Renders to
    output/videos/<video_id>.mp4, never uploads."""
    import copyright_compliance as cc
    from moviepy import AudioFileClip

    log(f"Generating {visuals} scenes...")
    clip_id = clips_from or video_id
    if not clip_paths:
        clip_paths = (generate_veo_clips(scenes, clip_id) if visuals == "veo"
                      else generate_image_clips(scenes, clip_id))
    if len(clip_paths) < 3:
        raise RuntimeError(f"Only {len(clip_paths)} scenes generated")

    log("Generating voiceover...")
    vo_path = (kokoro_voiceover(script, video_id, voice=voice) if voice_engine == "kokoro"
               else gemini_voiceover(script, video_id, voice=voice, style=style))
    cache_word_timestamps(vo_path, script)
    vo_dur = min(AudioFileClip(vo_path).duration + 1.0, 60.0)

    log("Generating background music...")
    music_path = psc.get_music(duration=vo_dur, script=script)

    log("Running compliance check...")
    check = cc.validate_before_upload(script, clip_paths, music_path)
    cc.save_compliance_report(check, video_id=video_id)
    if not check["passed"]:
        raise RuntimeError(f"COMPLIANCE FAILED: {check['issues']}")

    out_path = os.path.join(config.VIDEOS_DIR, f"{video_id}.mp4")
    log(f"Assembling video -> {out_path}")
    psc.assemble(clip_paths, script, vo_path, music_path, out_path)
    log(f"BUILD COMPLETE (not uploaded yet) -> {out_path}")
    return out_path, vo_path
