"""
sfx.py — Original sound effects synthesized with numpy (zero copyright, no
downloads -- the stock SFX URLs in git_asset_manifest.json are unreachable
from cloud sessions).

Every function returns a mono float32 array at SR. build_track() lays a list
of (time_s, samples) events onto one timeline and writes a .wav that
motion_shorts mixes under the voice.

Why: retention drops hardest right after the hook (GROWTH_PLAN.md). Sound is
half of the pattern interrupt the top Shorts use: a whoosh on every cut, an
impact on every reveal, a riser before a payoff, ticking on counters.
"""
import numpy as np

SR = 44100
_rng = np.random.default_rng(7)


def _env(n, attack=0.005, decay=8.0):
    t = np.arange(n) / SR
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    return a * np.exp(-decay * t)


def _lowpass(x, cutoff_hz):
    """One-pole lowpass with a per-sample (array) or fixed cutoff."""
    cutoff = np.broadcast_to(np.asarray(cutoff_hz, dtype=np.float64), x.shape)
    alpha = 1 - np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += alpha[i] * (x[i] - acc)
        y[i] = acc
    return y


def tick(pitch=1.0, amp=0.35):
    """Short mechanical click -- one per counter step."""
    n = int(SR * 0.025)
    t = np.arange(n) / SR
    click = np.sin(2 * np.pi * 2600 * pitch * t) * _env(n, 0.0005, 260)
    noise = _rng.standard_normal(n) * _env(n, 0.0002, 500) * 0.4
    return ((click + noise) * amp).astype(np.float32)


def whoosh(dur=0.45, amp=0.5):
    """Filtered-noise swoosh for transitions (cutoff sweeps up then down)."""
    n = int(SR * dur)
    x = _rng.standard_normal(n)
    p = np.linspace(0, 1, n)
    cutoff = 300 + 5200 * np.sin(np.pi * p) ** 2
    y = _lowpass(x, cutoff) - _lowpass(x, cutoff * 0.25)
    env = np.sin(np.pi * p) ** 1.5
    y = y * env
    return (y / (np.abs(y).max() + 1e-9) * amp).astype(np.float32)


def impact(amp=0.9, low=True):
    """Cinematic hit: pitch-dropping sine boom + noise transient, saturated."""
    n = int(SR * (0.9 if low else 0.45))
    t = np.arange(n) / SR
    f0, f1 = (110, 38) if low else (220, 90)
    freq = f1 + (f0 - f1) * np.exp(-t * 9)
    phase = 2 * np.pi * np.cumsum(freq) / SR
    boom = np.sin(phase) * np.exp(-t * (4.5 if low else 9))
    crack = _lowpass(_rng.standard_normal(n), 3500) * np.exp(-t * 60) * 1.6
    y = np.tanh((boom + crack) * 2.2)
    return (y / (np.abs(y).max() + 1e-9) * amp).astype(np.float32)


def riser(dur=0.8, amp=0.5):
    """Tension build into a reveal: rising tone + opening noise, hard stop."""
    n = int(SR * dur)
    p = np.linspace(0, 1, n)
    freq = 180 + 1100 * p ** 2
    tone = np.sin(2 * np.pi * np.cumsum(freq) / SR)
    noise = _lowpass(_rng.standard_normal(n), 200 + 6000 * p ** 2)
    y = (0.45 * tone + 0.8 * noise / (np.abs(noise).max() + 1e-9)) * p ** 2
    return (y / (np.abs(y).max() + 1e-9) * amp).astype(np.float32)


def crowd(dur=2.5, amp=0.35):
    """Stadium roar swell: band-limited noise with slow, uneven modulation."""
    n = int(SR * dur)
    x = _rng.standard_normal(n)
    y = _lowpass(x, 2200) - _lowpass(x, 280)
    t = np.arange(n) / SR
    wobble = 1 + 0.25 * np.sin(2 * np.pi * 3.1 * t) + 0.15 * np.sin(2 * np.pi * 5.7 * t + 1)
    env = np.clip(t / 0.35, 0, 1) * np.clip((dur - t) / 0.9, 0, 1)
    y = y * wobble * env
    return (y / (np.abs(y).max() + 1e-9) * amp).astype(np.float32)


def pop(amp=0.45):
    """Bright UI pop for text/badges appearing."""
    n = int(SR * 0.09)
    t = np.arange(n) / SR
    f = 900 + 900 * np.exp(-t * 40)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(n, 0.001, 45)
    return (y * amp).astype(np.float32)


def thump(amp=0.6):
    """One soft, low heartbeat thump (use two ~0.18s apart for lub-dub)."""
    n = int(SR * 0.22)
    t = np.arange(n) / SR
    f = 48 + 30 * np.exp(-t * 30)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(n, 0.004, 22)
    return (np.tanh(y * 1.8) / np.tanh(1.8) * amp).astype(np.float32)


def sonar(amp=0.35, freq=1180):
    """Sonar ping with a long tail and two faint echoes -- depth-meter milestones."""
    n = int(SR * 2.6)
    t = np.arange(n) / SR
    ping = np.sin(2 * np.pi * freq * t) * np.exp(-2.6 * t) * np.clip(t / 0.004, 0, 1)
    out = ping.copy()
    for d, g in ((0.55, 0.35), (1.1, 0.15)):
        k = int(d * SR)
        out[k:] += g * ping[: n - k]
    return (amp * out).astype(np.float32)


def deep_boom(amp=0.8):
    """Low, slow sub-bass hit for big reveals (the size of an animal, the bottom)."""
    n = int(SR * 2.2)
    t = np.arange(n) / SR
    f = 52 * np.exp(-0.6 * t) + 28
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-1.8 * t)
    air = _rng.standard_normal(n) * np.exp(-9 * t) * 0.15
    return (amp * (body + air) * np.clip(t / 0.01, 0, 1)).astype(np.float32)



def wind(dur=2.5, amp=0.45):
    """Falling-air rush: low noise that swells, with a slow flutter (a penny's tumble)."""
    n = int(SR * dur)
    t = np.arange(n) / SR
    c = 700 + 500 * np.sin(2 * np.pi * 1.7 * t) ** 2
    x = _lowpass(_lowpass(_lowpass(_rng.standard_normal(n), c), c), c)   # 3 poles: an air rush, not a hiss
    env = np.clip(t / 0.08, 0, 1) * np.clip((dur - t) / 0.4, 0, 1)
    return (amp * x / (np.abs(x).max() + 1e-9) * env).astype(np.float32)


def clink(amp=0.5):
    """Small metal object hitting something hard: bright partials, fast decay (penny on a dummy's head)."""
    n = int(SR * 0.6)
    t = np.arange(n) / SR
    y = sum(g * np.sin(2 * np.pi * f * t) * np.exp(-d * t) for f, g, d in
            ((3150, 1.0, 14), (5230, 0.6, 20), (7810, 0.35, 28), (1890, 0.4, 10)))
    return (amp * y / 2.35 * np.clip(t / 0.0008, 0, 1)).astype(np.float32)


def rip(dur=0.35, amp=0.6):
    """Fabric tearing: a crackle of short noise bursts that thins out."""
    n = int(SR * dur)
    t = np.arange(n) / SR
    bursts = (_rng.random(n) < 0.004 * np.exp(-3 * t / dur)).astype(np.float64)
    x = np.convolve(bursts, np.exp(-np.arange(400) / 60.0), mode="same") * _rng.standard_normal(n)
    x = x - _lowpass(x, 900)
    return (amp * x / (np.abs(x).max() + 1e-9)).astype(np.float32)


def crack(amp=0.8):
    """Ice cracking on impact: sharp broadband snap + a short low thud under it."""
    n = int(SR * 0.5)
    t = np.arange(n) / SR
    snap = _rng.standard_normal(n) * np.exp(-60 * t)
    thud = np.sin(2 * np.pi * np.cumsum(90 + 60 * np.exp(-t * 40)) / SR) * np.exp(-14 * t)
    return (amp * np.tanh(1.6 * (0.8 * snap + thud)) / np.tanh(1.6)).astype(np.float32)


def squelch(dur=0.55, amp=0.6):
    """Wet sand sucking at a leg: low gloopy wobble with a filtered-noise slurp."""
    n = int(SR * dur)
    t = np.arange(n) / SR
    f = 110 + 70 * np.sin(2 * np.pi * 7 * t) * np.exp(-3 * t)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR)
    slurp = _lowpass(_rng.standard_normal(n), 380 + 300 * t / dur)
    env = np.clip(t / 0.02, 0, 1) * np.exp(-3.2 * t)
    y = (0.7 * body + 1.8 * slurp / (np.abs(slurp).max() + 1e-9)) * env
    return (amp * y / (np.abs(y).max() + 1e-9)).astype(np.float32)


def splash(amp=0.5):
    """Water rushing in: a broad noise swell (the tide)."""
    n = int(SR * 1.6)
    t = np.arange(n) / SR
    x = _lowpass(_rng.standard_normal(n), 1800)
    env = np.clip(t / 0.25, 0, 1) * np.exp(-1.4 * t)
    return (amp * x / (np.abs(x).max() + 1e-9) * env).astype(np.float32)


def plunge(amp=0.8):
    """A car hitting water, carved around the voice: a low boom (< 250 Hz) and high spray (> 3.5 kHz) with almost
    nothing in the speech band, so it can sit under the first words (rule 19)."""
    n = int(SR * 1.4)
    t = np.arange(n) / SR
    low = _lowpass(_lowpass(_rng.standard_normal(n), 220), 220)
    low = low / (np.abs(low).max() + 1e-9) * np.clip(t / 0.015, 0, 1) * np.exp(-3.2 * t)
    thud = np.sin(2 * np.pi * np.cumsum(70 + 50 * np.exp(-t * 25)) / SR) * np.exp(-7 * t)
    x = _rng.standard_normal(n)
    hi = x - _lowpass(_lowpass(x, 3800), 3800)
    hi = hi / (np.abs(hi).max() + 1e-9) * np.clip(t / 0.01, 0, 1) * np.exp(-4.5 * t)
    return (amp * np.tanh(1.4 * (0.9 * low + 0.7 * thud + 0.5 * hi)) / np.tanh(1.4)).astype(np.float32)


def thunder(dur=3.0, amp=0.9, crack_amp=0.8):
    """A close strike: a short high snap, then a deep rumble that rolls and fades. The rumble is filtered below
    ~150 Hz so it can sit under narration without masking words (rule 19)."""
    n = int(SR * dur)
    t = np.arange(n) / SR
    snap = _rng.standard_normal(n) * np.exp(-38 * t)
    snap = snap - _lowpass(snap, 400)
    rum = _lowpass(_lowpass(_lowpass(_rng.standard_normal(n), 150), 150), 150)
    rum = rum / (np.abs(rum).max() + 1e-9) * np.clip(t / 0.06, 0, 1) * np.exp(-1.5 * t) * \
        (1 + 0.45 * np.sin(2 * np.pi * 2.3 * t + 1.0))
    y = crack_amp * snap / (np.abs(snap).max() + 1e-9) + rum
    return (amp * y / (np.abs(y).max() + 1e-9)).astype(np.float32)


def zap(dur=0.5, amp=0.4):
    """Electric crackle: dense random clicks over a faint mains buzz, high-passed."""
    n = int(SR * dur)
    t = np.arange(n) / SR
    clicks = (_rng.random(n) < 0.015) * _rng.standard_normal(n)
    x = np.convolve(clicks, np.exp(-np.arange(90) / 14.0), mode="same")
    x = x + 0.15 * np.sign(np.sin(2 * np.pi * 120 * t)) * (_rng.random(n) * 0.5 + 0.5)
    x = x - _lowpass(x, 1200)
    y = x * np.clip(t / 0.01, 0, 1) * np.exp(-3.5 * t)
    return (amp * y / (np.abs(y).max() + 1e-9)).astype(np.float32)

def fire(dur=3.0, amp=0.2):
    """A burning body: a low roar (below ~250 Hz) with sparse crackles above 4 kHz and almost nothing in the
    speech band, so it can run under narration (rule 19)."""
    n = int(SR * dur)
    t = np.arange(n) / SR
    roar = _lowpass(_lowpass(_rng.standard_normal(n), 230), 230)
    roar = roar / (np.abs(roar).max() + 1e-9) * (0.75 + 0.25 * np.sin(2 * np.pi * 0.9 * t + 1.0) ** 2)
    x = _rng.standard_normal(n)
    hi = x - _lowpass(_lowpass(x, 4200), 4200)
    gate = np.zeros(n)
    for c in _rng.integers(0, n, size=max(1, int(dur * 9))):             # crackles: tiny bursts at random moments
        m = min(n - c, int(SR * 0.012))
        gate[c:c + m] += np.exp(-np.arange(m) / (SR * 0.003)) * _rng.uniform(0.4, 1.0)
    crack_ = hi / (np.abs(hi).max() + 1e-9) * gate
    env = np.clip(t / 0.25, 0, 1) * np.clip((dur - t) / 0.5, 0, 1)
    return (amp * (roar + 0.55 * crack_) * env).astype(np.float32)


def sizzle(dur=1.2, amp=0.3):
    """Something landing on lava: a hiss above 3.5 kHz that dies away (outside the speech band)."""
    n = int(SR * dur)
    t = np.arange(n) / SR
    x = _rng.standard_normal(n)
    hi = x - _lowpass(_lowpass(x, 3600), 3600)
    env = np.clip(t / 0.01, 0, 1) * np.exp(-3.0 * t / dur * 1.6)
    return (amp * hi / (np.abs(hi).max() + 1e-9) * env).astype(np.float32)


def build_track(events: list, duration: float, out_path: str) -> str:
    """events: [(time_s, samples)] -> one normalized mono .wav at SR."""
    import soundfile as sf
    track = np.zeros(int(SR * (duration + 1.0)), dtype=np.float32)
    for t, s in events:
        i = max(0, int(t * SR))
        j = min(len(track), i + len(s))
        track[i:j] += s[: j - i]
    peak = np.abs(track).max()
    if peak > 0.95:
        track *= 0.95 / peak
    sf.write(out_path, track[: int(SR * duration)], SR)
    return out_path
