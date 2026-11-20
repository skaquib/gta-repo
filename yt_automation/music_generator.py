"""
music_generator.py
==================
Generates original royalty-free background music using pure Python synthesis.
No downloads. No copyright. No Content ID. Ever.

Creates two styles:
  "energetic"  — 128 BPM, 4-on-the-floor kick, punchy for facts Shorts
  "analytical" — 90 BPM, cinematic, sparse, for tactical analysis videos

Output: MP3 file via ffmpeg (already installed on your system)
"""

import math
import os, time, subprocess, tempfile
import numpy as np

SAMPLE_RATE = 44100

def _find_ffmpeg() -> str:
    """Prefer a system ffmpeg on PATH; fall back to moviepy's bundled binary."""
    import shutil
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()

FFMPEG = _find_ffmpeg()

# ─── Synthesis primitives ──────────────────────────────────────────────────────

def sine(freq, dur, amp=0.5, sr=SAMPLE_RATE):
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    return amp * np.sin(2 * np.pi * freq * t)

def noise(dur, amp=0.5, sr=SAMPLE_RATE):
    return amp * np.random.randn(int(sr * dur)).astype(np.float32)

def env_exp(signal, decay=10.0, sr=SAMPLE_RATE):
    n = len(signal)
    t = np.linspace(0, n/sr, n, endpoint=False)
    return signal * np.exp(-decay * t)

def mix(*signals):
    """Mix signals of different lengths into one array."""
    max_len = max(len(s) for s in signals)
    out = np.zeros(max_len, dtype=np.float32)
    for s in signals:
        out[:len(s)] += s.astype(np.float32)
    return out


# ─── Drum sounds ──────────────────────────────────────────────────────────────

def kick(sr=SAMPLE_RATE):
    """Deep punchy kick drum — frequency sweep 150→40 Hz."""
    dur = 0.45
    n   = int(sr * dur)
    t   = np.linspace(0, dur, n, endpoint=False)
    freq = 150 * np.exp(-18 * t) + 40
    phase = np.cumsum(freq) / sr
    wave  = np.sin(2 * np.pi * phase)
    click = env_exp(noise(0.01, amp=0.4, sr=sr), decay=200, sr=sr)
    body  = env_exp(wave, decay=7, sr=sr)
    out   = mix(click, body) * 0.85
    return out.astype(np.float32)

def snare(sr=SAMPLE_RATE):
    """Crisp snare — noise transient + 200 Hz tone body."""
    dur = 0.25
    t   = np.linspace(0, dur, int(sr * dur), endpoint=False)
    tone  = env_exp(np.sin(2 * np.pi * 200 * t) * 0.4, decay=18, sr=sr)
    crack = env_exp(noise(dur, amp=0.7, sr=sr), decay=22, sr=sr)
    # High-pass noise for crack (simple diff)
    hp = np.diff(crack, prepend=crack[0])
    return (tone + hp * 0.5).astype(np.float32)

def hihat(dur=0.06, amp=0.25, sr=SAMPLE_RATE):
    """Closed hi-hat — very short filtered noise."""
    return env_exp(noise(dur, amp=amp, sr=sr), decay=80, sr=sr).astype(np.float32)

def openhat(dur=0.18, amp=0.20, sr=SAMPLE_RATE):
    """Open hi-hat — longer decay."""
    return env_exp(noise(dur, amp=amp, sr=sr), decay=18, sr=sr).astype(np.float32)

def clap(sr=SAMPLE_RATE):
    """Hand clap — layered noise bursts."""
    layers = []
    for delay in [0, 0.005, 0.010]:
        n_delay = int(delay * sr)
        s = env_exp(noise(0.12, amp=0.5, sr=sr), decay=30, sr=sr)
        padded = np.concatenate([np.zeros(n_delay), s])
        layers.append(padded)
    return mix(*layers).astype(np.float32)

def bass_note(freq, dur, sr=SAMPLE_RATE):
    """Sub bass note — sine + slight second harmonic."""
    t    = np.linspace(0, dur, int(sr * dur), endpoint=False)
    wave = 0.7 * np.sin(2 * np.pi * freq * t) + 0.15 * np.sin(2 * np.pi * freq * 2 * t)
    env  = np.ones(len(wave))
    fade = min(int(0.05 * sr), len(wave)//4)
    env[:fade]  = np.linspace(0, 1, fade)
    env[-fade:] = np.linspace(1, 0, fade)
    return (wave * env * 0.6).astype(np.float32)


# ─── Song builder ─────────────────────────────────────────────────────────────

def place(track, sound, sample_offset):
    """Place a sound at sample_offset in track array."""
    end = min(sample_offset + len(sound), len(track))
    n   = end - sample_offset
    if n > 0:
        track[sample_offset:end] += sound[:n]


def generate_energetic(duration_sec=30, bpm=128, sr=SAMPLE_RATE) -> np.ndarray:
    """
    Energetic sports beat — 128 BPM.
    Pattern: 4-on-floor kick | snare 2&4 | 16th hi-hats | driving bass line
    """
    total = int(sr * duration_sec)
    track = np.zeros(total, dtype=np.float32)

    beat  = sr * 60.0 / bpm         # samples per beat
    bar   = beat * 4                 # samples per bar (4/4)

    # Bass note sequence (root, fifth, fourth, fifth — sports-energy)
    bass_freqs = [55, 82.4, 73.4, 82.4]   # A1, E2, D2, E2

    k = kick(sr)
    s = snare(sr)
    hh_c = hihat(0.06, 0.22, sr)
    hh_o = openhat(0.14, 0.15, sr)

    bar_idx = 0
    pos = 0
    while pos < total:
        beat_num = bar_idx % 4
        pos_b = int(bar_idx * beat)

        # Kick — every beat
        place(track, k, pos_b)

        # Snare on beat 2 & 4
        if beat_num in (1, 3):
            place(track, s, pos_b)

        # 16th hi-hats (4 per beat)
        for sixteenth in range(4):
            hh_pos = pos_b + int(sixteenth * beat / 4)
            if sixteenth == 2 and beat_num in (0, 2):
                place(track, hh_o, hh_pos)   # open hat on off-beat
            else:
                place(track, hh_c, hh_pos)

        # Bass note per beat
        bf  = bass_freqs[bar_idx % len(bass_freqs)]
        bn  = bass_note(bf, 60.0/bpm * 0.9, sr)
        place(track, bn, pos_b)

        bar_idx += 1
        pos = int(bar_idx * beat)

    # Normalize & soft limiter
    peak = np.max(np.abs(track)) + 1e-9
    track = track / peak * 0.75
    track = np.tanh(track * 1.2) * 0.70   # soft clip / warmth
    return track


def generate_funk(duration_sec=30, bpm=130, sr=SAMPLE_RATE) -> np.ndarray:
    """
    Rhythmic Brazilian Baile Funk (Tamborzão) beat — 130 BPM.
    Pattern: Kick on 1 & 3, syncopated snares on off-beats, sub-bass pulse.
    """
    total = int(sr * duration_sec)
    track = np.zeros(total, dtype=np.float32)

    beat  = sr * 60.0 / bpm         # samples per beat
    sixteenth = beat / 4.0          # samples per 16th note

    k = kick(sr)
    s = snare(sr)
    hh = hihat(0.06, 0.20, sr)

    # Bass line in A minor (A1, C2, D2, G1)
    bass_freqs = [55.0, 65.4, 73.4, 49.0]

    bar_idx = 0
    pos = 0
    while pos < total:
        bar_start = int(bar_idx * beat * 4)
        if bar_start >= total: break

        # Each bar has 16 sixteenth notes
        # Kick on: 0, 8, 12
        for k_idx in [0, 8, 12]:
            k_pos = bar_start + int(k_idx * sixteenth)
            place(track, k, k_pos)

        # Snare on: 4, 6, 10, 14 (classic Baile Funk syncopation)
        for s_idx in [4, 6, 10, 14]:
            s_pos = bar_start + int(s_idx * sixteenth)
            place(track, s * 0.9, s_pos)

        # Hi-hat on every 8th note (off-beats)
        for hh_idx in range(16):
            if hh_idx % 2 == 1:
                hh_pos = bar_start + int(hh_idx * sixteenth)
                place(track, hh, hh_pos)

        # Bass note on beat 1 and 3 (indices 0 and 8)
        bf1 = bass_freqs[(bar_idx) % len(bass_freqs)]
        bf2 = bass_freqs[(bar_idx + 1) % len(bass_freqs)]
        
        bn1 = bass_note(bf1, beat * 1.5 / sr, sr)
        bn2 = bass_note(bf2, beat * 1.5 / sr, sr)
        
        place(track, bn1, bar_start)
        place(track, bn2, bar_start + int(8 * sixteenth))

        bar_idx += 1
        pos = int(bar_idx * beat * 4)

    # Normalize & soft clip
    peak = np.max(np.abs(track)) + 1e-9
    track = track / peak * 0.85
    track = np.tanh(track * 1.3) * 0.78
    return track


def generate_analytical(duration_sec=55, bpm=90, sr=SAMPLE_RATE) -> np.ndarray:
    """
    Cinematic analytical beat — 90 BPM.
    Pattern: Sparse kick | clap on 3 | quarter hi-hats | slow bass pulse
    """
    total = int(sr * duration_sec)
    track = np.zeros(total, dtype=np.float32)

    beat  = sr * 60.0 / bpm
    bar   = beat * 4

    k  = kick(sr)
    cl = clap(sr)
    hh = hihat(0.10, 0.18, sr)

    bass_freqs = [41.2, 41.2, 49.0, 36.7]   # E1, E1, G1, D1 — minor feel

    bar_idx = 0
    while True:
        pos_b = int(bar_idx * beat)
        if pos_b >= total: break
        beat_num = bar_idx % 4

        # Kick on beat 1 and 3
        if beat_num in (0, 2):
            place(track, k, pos_b)

        # Clap on beat 3 only
        if beat_num == 2:
            place(track, cl, pos_b)

        # Quarter hi-hat on every beat
        place(track, hh, pos_b)

        # Half-note bass pulse (every 2 beats)
        if beat_num % 2 == 0:
            bf  = bass_freqs[(bar_idx // 2) % len(bass_freqs)]
            bn  = bass_note(bf, 60.0/bpm * 1.8, sr)
            place(track, bn, pos_b)

        bar_idx += 1

    peak = np.max(np.abs(track)) + 1e-9
    track = track / peak * 0.75
    track = np.tanh(track * 1.1) * 0.70
    return track


def generate_emotional(duration_sec=30, bpm=72, sr=SAMPLE_RATE) -> np.ndarray:
    """
    Soft emotional bed -- no drums, slow layered sine-wave chords with a
    gentle sub-bass pulse. Added 2026-08-22 per direct feedback that every
    video (a last-minute promotion, a heavy defeat, a 91-year drought)
    was getting the same punchy 128 BPM sports beat regardless of the
    story's actual tone. For reflective/bittersweet/heartfelt stories --
    a loss, a long wait, a career ending -- where a hype beat works
    against the mood instead of with it.
    """
    total = int(sr * duration_sec)
    track = np.zeros(total, dtype=np.float32)

    beat = sr * 60.0 / bpm
    bar = beat * 4
    bar_dur = bar / sr

    # Slow chord progression, one chord per bar (root, 3rd, 5th)
    progression = [
        (220.00, 261.63, 329.63),  # A minor
        (196.00, 246.94, 293.66),  # G
        (174.61, 220.00, 261.63),  # F
        (196.00, 246.94, 293.66),  # G
    ]

    bar_idx = 0
    while True:
        pos = int(bar_idx * bar)
        if pos >= total:
            break
        chord = progression[bar_idx % len(progression)]
        pad = mix(*[env_exp(sine(f, bar_dur * 1.15, amp=0.16, sr=sr), decay=0.6, sr=sr)
                    for f in chord])
        place(track, pad, pos)

        # Gentle sub-bass pulse, once per bar, soft
        bn = bass_note(chord[0] / 2, bar_dur * 0.9, sr) * 0.5
        place(track, bn, pos)

        bar_idx += 1

    peak = np.max(np.abs(track)) + 1e-9
    track = track / peak * 0.55
    return track


def generate_deep(duration_sec=60, bpm=60, sr=SAMPLE_RATE) -> np.ndarray:
    """Deep-ocean ambience for the extreme-animals videos: a slow low drone (D minor), a soft
    filtered-noise "pressure" rumble and an occasional distant whale-like glide. No drums, no
    melody to fight the narration. Fully vectorised so 15-minute tracks render in seconds."""
    n = int(duration_sec * sr)
    t = np.arange(n, dtype=np.float32) / sr
    out = np.zeros(n, dtype=np.float32)
    for f, a, lfo in ((36.71, 0.30, 0.031), (55.0, 0.22, 0.047), (73.42, 0.16, 0.023),
                      (110.0, 0.06, 0.017), (146.83, 0.035, 0.041)):
        swell = 0.6 + 0.4 * np.sin(2 * np.pi * lfo * t + f)
        out += a * swell * np.sin(2 * np.pi * f * t + 0.3 * np.sin(2 * np.pi * 0.07 * t))
    rng = np.random.default_rng(11)
    noise = rng.standard_normal(n).astype(np.float32)
    spec = np.fft.rfft(noise)
    freqs = np.fft.rfftfreq(n, 1 / sr)
    spec *= np.exp(-freqs / 120.0)                      # dark, distant rumble
    rumble = np.fft.irfft(spec, n).astype(np.float32)
    rumble /= (np.abs(rumble).max() + 1e-9)
    out += 0.18 * rumble * (0.7 + 0.3 * np.sin(2 * np.pi * 0.013 * t))
    for start in np.arange(25.0, duration_sec - 8, 47.0):  # a far-off glide every ~47 s
        i0, length = int(start * sr), int(5.5 * sr)
        tt = np.arange(length, dtype=np.float32) / sr
        f = 180 + 140 * np.sin(np.pi * tt / 5.5)
        ph = 2 * np.pi * np.cumsum(f) / sr
        env = np.sin(np.pi * tt / 5.5) ** 2
        seg = 0.05 * env * np.sin(ph)
        out[i0:i0 + length] += seg[: max(0, min(length, n - i0))]
    fade = int(3 * sr)
    out[:fade] *= np.linspace(0, 1, fade, dtype=np.float32)
    out[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)
    return out / (np.abs(out).max() + 1e-9) * 0.8


def generate_hook_hit(sr=SAMPLE_RATE) -> np.ndarray:
    """A short riser-into-impact 'drop' for the hook moment -- a rising
    pitch sweep building tension for ~0.4s, then a hard hit (kick body +
    noise burst + sub-thump) right on the beat. Added 2026-08-22 per
    direct feedback: "understand the hook and drop something ... use
    beatbox drum". Meant to be mixed in once at the top of the hook, not
    looped like the background beds."""
    riser_dur = 0.4
    n = int(sr * riser_dur)
    t = np.linspace(0, riser_dur, n, endpoint=False)
    freq = 200 * np.power(2000 / 200, t / riser_dur)  # exponential sweep 200Hz -> 2000Hz
    phase = np.cumsum(freq) / sr
    riser = np.sin(2 * np.pi * phase) * np.linspace(0.05, 0.5, n)

    hit_kick  = env_exp(kick(sr), decay=6, sr=sr) * 1.2
    hit_noise = env_exp(noise(0.15, amp=0.6, sr=sr), decay=25, sr=sr)
    sub       = env_exp(sine(55, 0.35, amp=0.6, sr=sr), decay=8, sr=sr)
    impact = mix(hit_kick, hit_noise, sub)

    out = np.concatenate([riser.astype(np.float32), impact.astype(np.float32)])
    peak = np.max(np.abs(out)) + 1e-9
    return (out / peak * 0.9).astype(np.float32)


def get_hook_hit(audio_dir: str = "output/audio") -> str:
    """Cached riser+impact hit for the hook moment. Returns path to MP3."""
    os.makedirs(audio_dir, exist_ok=True)
    path = os.path.join(audio_dir, "hook_hit.mp3")
    if os.path.exists(path) and os.path.getsize(path) > 1_000:
        return path
    save_mp3(generate_hook_hit(), path)
    return path


# ─── Export to MP3 ────────────────────────────────────────────────────────────

def save_mp3(audio: np.ndarray, out_path: str, sr=SAMPLE_RATE) -> str:
    """Write WAV then convert to MP3 with ffmpeg."""
    # Stereo
    stereo = np.stack([audio, audio], axis=1)
    stereo = (np.clip(stereo, -1, 1) * 32767).astype(np.int16)

    tmp_wav = out_path.replace(".mp3", "_tmp.wav")
    import wave, struct
    with wave.open(tmp_wav, "w") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(stereo.tobytes())

    # Convert to MP3 via ffmpeg
    cmd = [
        FFMPEG, "-y", "-i", tmp_wav,
        "-codec:a", "libmp3lame", "-b:a", "192k", "-ar", str(sr),
        out_path,
    ]
    result = subprocess.run(cmd, capture_output=True)
    try: os.remove(tmp_wav)
    except: pass

    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg MP3 encode failed: {result.stderr.decode()[:200]}")
    return out_path


def generate_lounge(duration_sec=40, bpm=92, sr=SAMPLE_RATE) -> np.ndarray:
    """Fine-dining lounge jazz: soft Rhodes-style chords (ii-V-I-VI in C), a walking upright bass,
    brushed snare swirls and a light ride cymbal. Quiet and classy -- for comedy that plays it straight."""
    n = int(duration_sec * sr)
    t = np.arange(n) / sr
    out = np.zeros(n)
    beat = 60.0 / bpm
    bar = 4 * beat
    def hz(m):
        return 440.0 * 2 ** ((m - 69) / 12)
    # Dm9, G13, Cmaj9, A7(b9)  -- voicings as MIDI notes
    chords = [[50, 53, 57, 60, 64], [43, 53, 57, 59, 64], [48, 52, 55, 59, 62], [45, 49, 55, 58, 61]]
    roots = [38, 43, 36, 45]
    walk = [[0, 3, 5, 7], [0, 4, 5, 6], [0, 2, 4, 7], [0, 4, 7, 6]]
    rng = np.random.default_rng(7)
    nb = int(duration_sec / bar) + 2
    for b in range(nb):
        ci = b % 4
        t0 = b * bar
        # Rhodes: two comping hits per bar (beat 1 and the "and" of 2), sine + soft bell partial, slow decay
        for hit, length in ((0.0, 1.6), (1.5 * beat, 1.1)):
            s0 = int((t0 + hit + rng.uniform(0, 0.02)) * sr)
            m = int(length * sr)
            if s0 >= n:
                continue
            m = min(m, n - s0)
            tt = np.arange(m) / sr
            env = (1 - np.exp(-tt * 60)) * np.exp(-tt * 2.2)
            for note in chords[ci]:
                f = hz(note + 12)
                tone = np.sin(2 * np.pi * f * tt + 0.6 * np.sin(2 * np.pi * f * 2 * tt) * np.exp(-tt * 6))
                out[s0:s0 + m] += 0.045 * env * tone
        # walking bass, one note per beat
        for k in range(4):
            s0 = int((t0 + k * beat) * sr)
            if s0 >= n:
                continue
            m = min(int(beat * sr * 0.95), n - s0)
            tt = np.arange(m) / sr
            f = hz(roots[ci] + walk[ci][k])
            env = (1 - np.exp(-tt * 200)) * np.exp(-tt * 3.5)
            out[s0:s0 + m] += 0.16 * env * (np.sin(2 * np.pi * f * tt) + 0.25 * np.sin(4 * np.pi * f * tt))
        # ride cymbal (swing: 1, 2, 2-and-a-third... ) and brushed snare on 2 and 4
        for k in range(4):
            for sw in ((0.0, 0.05), (2 / 3, 0.03)) if k % 2 else ((0.0, 0.05),):
                s0 = int((t0 + (k + sw[0]) * beat) * sr)
                if s0 >= n:
                    continue
                m = min(int(0.35 * sr), n - s0)
                tt = np.arange(m) / sr
                noise = rng.standard_normal(m)
                noise = noise - np.convolve(noise, np.ones(6) / 6, mode="same")      # keep the highs
                out[s0:s0 + m] += sw[1] * 0.5 * noise * np.exp(-tt * 14)
            if k in (1, 3):
                s0 = int((t0 + k * beat) * sr)
                if s0 < n:
                    m = min(int(0.4 * sr), n - s0)
                    tt = np.arange(m) / sr
                    brush = rng.standard_normal(m) * np.exp(-tt * 9) * (1 - np.exp(-tt * 40))
                    out[s0:s0 + m] += 0.035 * np.convolve(brush, np.ones(12) / 12, mode="same")
    fade = np.minimum(1.0, np.minimum(t / 1.0, (duration_sec - t) / 1.5))
    out *= np.clip(fade, 0, 1)
    return (out / (np.abs(out).max() + 1e-9) * 0.8).astype(np.float32)


# ─── Public API ───────────────────────────────────────────────────────────────

def get_original_music(style: str = "energetic", audio_dir: str = "output/audio",
                       duration: float = None) -> str:
    """
    Generate and cache an original beat.
    style: "energetic" (128 BPM sports) | "analytical" (90 BPM cinematic) |
           "funk" (130 BPM Brazilian Funk) | "emotional" (72 BPM soft pad,
           no drums -- for reflective/bittersweet stories) | "deep" (deep-ocean
           drone and rumble, no beat -- extreme-animals long videos) | "lounge"
           (92 BPM fine-dining jazz trio -- deadpan comedy)
    Returns path to MP3 file.
    """
    os.makedirs(audio_dir, exist_ok=True)
    if style == "funk":
        bpm = 130
    elif style == "energetic":
        bpm = 128
    elif style == "emotional":
        bpm = 72
    elif style == "deep":
        bpm = 60
    elif style == "lounge":
        bpm = 92
    else:
        bpm = 90
    dur  = duration or (30 if style in ["energetic", "funk"] else 45 if style == "emotional" else 55)
    # round UP (+1 s spare): a cache keyed on int(dur) handed a 20.5 s track to a 21.3 s video
    dur  = math.ceil(dur) + 1
    name = f"original_beat_{style}_{bpm}bpm_{int(dur)}s.mp3"
    path = os.path.join(audio_dir, name)

    if os.path.exists(path) and os.path.getsize(path) > 10_000:
        return path   # use cached version

    print(f"[music_gen] Generating {style} beat @ {bpm}BPM for {dur:.0f}s...")
    if style == "funk":
        audio = generate_funk(duration_sec=dur, bpm=bpm)
    elif style == "energetic":
        audio = generate_energetic(duration_sec=dur, bpm=bpm)
    elif style == "emotional":
        audio = generate_emotional(duration_sec=dur, bpm=bpm)
    elif style == "deep":
        audio = generate_deep(duration_sec=dur, bpm=bpm)
    elif style == "lounge":
        audio = generate_lounge(duration_sec=dur, bpm=bpm)
    else:
        audio = generate_analytical(duration_sec=dur, bpm=bpm)

    save_mp3(audio, path)
    sz = os.path.getsize(path) / 1024
    print(f"[music_gen] Saved: {name} ({sz:.0f}KB) — 100% original, zero copyright")
    return path


# ─── CLI test ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Generating energetic beat (30s)...")
    p1 = get_original_music("energetic", duration=30)
    print(f"[OK] {p1}")

    print("Generating analytical beat (55s)...")
    p2 = get_original_music("analytical", duration=55)
    print(f"[OK] {p2}")
    print("Done! Both beats are 100% original - zero copyright possible.")
