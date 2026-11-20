"""
motion_shorts.py — Shared engine for visual-first Shorts drawn entirely in
code (to-scale comparisons, countdowns, records on a pitch).

Why: every footage/AI-clip Short stopped at the ~1K-view test batch; the
formats breaking out for small sports channels in 2026 show the fact itself
(size comparisons, km/h rankings, longest goals on a pitch -- see
output/research/visual_format_shorts.json). These cost nothing to make: PIL
graphics, local Kokoro voice, synthesized music, no stock or AI imagery.

A Short is a list of SEGMENTS, each a dict with at least "line" (spoken) plus
whatever the frame function needs. render_short() voices each line
separately (so visuals switch exactly on the spoken line), calls
frame_fn(t, seg_index, t_into_segment, starts) for every frame, mixes
voice + music + hook hit, and writes the .words.json cache psc.upload()
uses for the caption track.
"""
import os
import json
import numpy as np
from PIL import ImageDraw, ImageFont

import config
import pro_shorts_creator as psc
import music_generator
import copyright_compliance as cc
from logger import log

W, H, FPS = 1080, 1920, 30
_FONT = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
_fonts = {}


def font(size: int):
    if size not in _fonts:
        try:
            _fonts[size] = ImageFont.truetype(_FONT, size)
        except OSError:
            _fonts[size] = psc.get_font(size, bold=True)
    return _fonts[size]


def ease(x: float) -> float:
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def centered(d: ImageDraw.ImageDraw, y: float, text: str, size: int, fill=(255, 255, 255)):
    """Centered, stroked text that shrinks to fit the frame width."""
    f = font(size)
    while d.textlength(text, font=f) > W - 80 and size > 30:
        size -= 4
        f = font(size)
    d.text(((W - d.textlength(text, font=f)) / 2, y), text, font=f, fill=fill,
           stroke_width=max(3, size // 14), stroke_fill=(0, 0, 0))


def caption(d: ImageDraw.ImageDraw, y: float, line: str, size: int = 50):
    """Sound-off caption: the spoken line, wrapped and centered."""
    f = font(size)
    rows, cur = [], ""
    for w in line.split():
        trial = (cur + " " + w).strip()
        if d.textlength(trial, font=f) > W - 140:
            rows.append(cur)
            cur = w
        else:
            cur = trial
    rows.append(cur)
    for i, row in enumerate(rows):
        d.text(((W - d.textlength(row, font=f)) / 2, y + i * int(size * 1.3)), row, font=f,
               fill=(255, 255, 255), stroke_width=4, stroke_fill=(0, 0, 0))


def watermark(d: ImageDraw.ImageDraw):
    d.text((24, 20), getattr(config, "CHANNEL_NAME", "FramedFacts"), font=font(30),
           fill=(255, 255, 255, 170))


def build_voice(segments: list, video_id: str, voice: str = "am_michael", speed: float = 1.12,
                lang: str = "en-us", gap_s: float = 0.18, lead_s: float = 0.05, chapter_pause_s: float = 0.0):
    """One Kokoro take per segment line -> (normalized wav, segment start times, end time).
    A segment's optional "say" overrides what is spoken (pronunciation fixes,
    e.g. "Klah-see-ko" for "Clásico") while "line" stays the on-screen text.
    lead_s defaults to 0.05: the voice must start on frame 1 -- silence at the
    top of a Short is where the swipe happens."""
    import soundfile as sf
    cloud = "Chirp3-HD" in voice          # Google Cloud natural voice (free credit), else local Kokoro
    k = None if cloud else psc._get_kokoro()
    sr = 24000
    pieces, starts, t = [np.zeros(int(sr * lead_s), dtype=np.float32)], [], lead_s
    for i, seg in enumerate(segments):
        seg_start = t
        if i and seg.get("chapter") and chapter_pause_s:      # chapter card + sonar land in a beat of silence,
            pieces.append(np.zeros(int(sr * chapter_pause_s), dtype=np.float32))   # then the voice comes in
            t += chapter_pause_s
        if cloud:
            import genai_clients
            samples, sr = genai_clients.cloud_tts(seg.get("say", seg["line"]), voice=seg.get("voice", voice),
                                                  rate=seg.get("speed", speed),
                                                  cache_dir=os.path.join(config.AUDIO_DIR, "tts_cache"))
            nz = np.nonzero(np.abs(samples) > 0.01)[0]           # trim the voice's own lead/tail silence
            if len(nz):
                samples = samples[max(0, nz[0] - int(0.03 * sr)): nz[-1] + int(0.08 * sr)]
        else:
            samples, sr = k.create(seg.get("say", seg["line"]), voice=seg.get("voice", voice),   # a line may have its
                                   speed=seg.get("speed", speed), lang=seg.get("lang", lang))                    # own voice (a character)
        starts.append(seg_start)
        gap = np.zeros(int(sr * seg.get("gap", gap_s)), dtype=np.float32)     # a segment may set its own gap
        pieces += [samples.astype(np.float32), gap]
        t += (len(samples) + len(gap)) / sr
    os.makedirs(config.AUDIO_DIR, exist_ok=True)
    out = os.path.join(config.AUDIO_DIR, f"{video_id}_vo.wav")
    sf.write(out, np.concatenate(pieces), sr)
    return psc.normalize_voice(out), starts, t


def render_short(script: dict, segments: list, video_id: str, frame_fn, voice: str = "am_michael",
                 speed: float = 1.12, music_style: str = "energetic", sfx_fn=None,
                 music_vol: float = 0.10, hook_hit: bool = True, gap_s: float = 0.18,
                 chapter_pause_s: float = 0.0) -> tuple:
    """Voice -> frames -> mix -> mp4 in output/videos/. Never uploads.
    sfx_fn(starts, total) -> [(time_s, samples)] adds a synthesized sound
    effects layer (see sfx.py)."""
    from moviepy import VideoClip, AudioFileClip, CompositeAudioClip
    log(f"Voice ({voice}, per-segment for exact sync)...")
    vo_path, starts, total = build_voice(segments, video_id, voice=voice, speed=speed, gap_s=gap_s,
                                         chapter_pause_s=chapter_pause_s)
    duration = total + 0.6
    log(f"Duration {duration:.1f}s, segment starts: {[round(x, 2) for x in starts]}")

    music_path = music_generator.get_original_music(music_style, audio_dir=config.AUDIO_DIR,
                                                    duration=duration)
    check = cc.validate_before_upload(script, [], music_path)
    cc.save_compliance_report(check, video_id=video_id)
    if not check["passed"]:
        raise RuntimeError(f"COMPLIANCE FAILED: {check['issues']}")

    def seg_at(t):
        i = 0
        for k, st in enumerate(starts):
            if t >= st:
                i = k
        return i

    def make_frame(t):
        i = seg_at(t)
        return frame_fn(t, i, t - starts[i], starts)

    video = VideoClip(make_frame, duration=duration)
    layers = [psc._vol(psc._dur(AudioFileClip(music_path), duration), music_vol),
              psc._vol(AudioFileClip(vo_path), 1.5)]
    if sfx_fn:
        import sfx
        sfx_path = sfx.build_track(sfx_fn(starts, total), duration,
                                   os.path.join(config.AUDIO_DIR, f"{video_id}_sfx.wav"))
        layers.append(psc._vol(AudioFileClip(sfx_path), 0.75))
    elif hook_hit:
        try:
            layers.append(psc._vol(AudioFileClip(music_generator.get_hook_hit()), 0.8))
        except Exception as e:
            log(f"No hook hit ({e})")
    video = psc._audio(video, psc._dur(CompositeAudioClip(layers), duration))

    out = os.path.join(config.VIDEOS_DIR, f"{video_id}.mp4")
    os.makedirs(config.VIDEOS_DIR, exist_ok=True)
    video.write_videofile(out, fps=FPS, codec="libx264", audio_codec="aac", audio_bitrate="192k",
                          threads=8, logger=None,
                          ffmpeg_params=["-crf", "18", "-preset", "faster", "-pix_fmt", "yuv420p",
                                         "-movflags", "+faststart"])

    # Word timings for the uploaded caption track (psc.upload reads this cache).
    words = []
    for seg, st, nxt in zip(segments, starts, starts[1:] + [total]):
        toks = seg["line"].split()
        step = (nxt - st - 0.18) / len(toks)
        words += [{"word": w, "start": round(st + k * step, 2), "end": round(st + (k + 1) * step, 2)}
                  for k, w in enumerate(toks)]
    with open(vo_path + ".words.json", "w", encoding="utf-8") as f:
        json.dump(words, f)
    log(f"BUILD COMPLETE (not uploaded yet) -> {out}")
    return out, vo_path
