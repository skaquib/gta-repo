"""
longform_creator.py — long-form documentary pipeline (8-12 min).

WHY THIS EXISTS (decision made 2026-09-08, grounded in real numbers):
The channel ran 108 Shorts in ~5 months and reached 28 subscribers. Measured
gaps to monetization at that point:
    subscribers   28      / 1,000    -> ~2,187 days (6 years) at 0.44/day
    Shorts views  44,777  / 10,000,000 per 90d
    watch hours   86.7    / 4,000 per 90d
Shorts RPM is $0.02-$0.12 (avg ~$0.05), so even 1,000,000 Shorts views is
about $50. Long-form RPM is $1.65-$24.75 -- 10-100x per view. Shorts are a
discovery tool, not an income source.

FORMAT: faceless business-documentary (the MagnatesMedia model) -- voiceover
over archive photos, documents, maps and charts. No face, no filming, no
rights-managed footage required. Proven to work faceless at scale.

NICHE: sports MONEY. Sports alone is low-CPM entertainment; sports finance
sits in the business/finance category advertisers pay for, while still being
the subject this channel already researches well.

THE EDGE: research depth. AI voice and AI b-roll are commodities in 2026 --
a genuinely researched script is what out-retains automated competitors. The
verification discipline already built for Shorts (cross-checking every claim
across multiple sources, rejecting stale or disputed numbers) is worth little
on a 22-second Short and is the entire moat here.

STRUCTURE: cold open -> acts -> payoff -> outro, with per-beat visuals.
A DocScript is a list of Beat(narration, visual_query, kind); the builder
maps each beat to its own visual so a 10-minute video gets 40-80 distinct
images rather than 3 stills stretched thin.
"""
import os
import json
from dataclasses import dataclass, field, asdict
from typing import List, Optional

import config
from logger import log

# Narration rate is ENGINE-dependent and this matters for runtime targets.
# Measured 2026-09-11: ElevenLabs ~155 wpm, but the local cloned voice runs
# ~207 wpm. A 957-word script validated as "6.2 min" against the ElevenLabs
# figure and actually rendered at 4.55 min on the cloned voice. With the
# ElevenLabs quota at zero, the cloned rate is the honest default.
WORDS_PER_MINUTE_ELEVENLABS = 155
WORDS_PER_MINUTE_CLONED = 207
WORDS_PER_MINUTE = WORDS_PER_MINUTE_CLONED
MAX_BEAT_SECONDS = 12.0


@dataclass
class Beat:
    """One narration beat and the visual that carries it."""
    narration: str
    visual: str                      # search term OR a local file path
    kind: str = "stock"              # stock | photo | chart | card
    source: str = ""                 # citation, for the description + on-screen credit

    def word_count(self) -> int:
        return len(self.narration.split())


@dataclass
class Chapter:
    title: str
    beats: List[Beat] = field(default_factory=list)

    def word_count(self) -> int:
        return sum(b.word_count() for b in self.beats)


@dataclass
class DocScript:
    title: str
    hook_card: str
    description: str
    tags: List[str]
    chapters: List[Chapter] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    # Per-documentary search terms, merged over THEME_QUERIES. REQUIRED
    # whenever the subject's sport is ambiguous. "football" means American
    # football in the US and soccer everywhere else, and stock libraries
    # answer to whichever phrasing you use. Reproduced twice: an NFL
    # documentary rendered over soccer pitches (2026-09-09), then a soccer
    # documentary rendered over an American football field (2026-09-11)
    # because the theme had been hardcoded to NFL terms to fix the first one.
    theme_queries: dict = field(default_factory=dict)
    # Optional per-SUBJECT clip buckets, checked before the broad THEMES:
    #   {name: {"match": [substrings of Beat.visual], "queries": [...], "n": clips}}
    # First bucket whose match list hits the beat's visual query wins, so put
    # specific buckets (referee, trophy) above general ones (soccer action).
    # Six broad themes could not keep a 115-beat documentary on-topic: doc #3
    # put a US tax form on a debut hat-trick and a bar on a contracts beat.
    visual_buckets: dict = field(default_factory=dict)

    def word_count(self) -> int:
        return sum(c.word_count() for c in self.chapters)

    def estimated_minutes(self) -> float:
        return self.word_count() / WORDS_PER_MINUTE

    def all_beats(self) -> List[Beat]:
        return [b for c in self.chapters for b in c.beats]

    def narration_text(self) -> str:
        return " ".join(b.narration.strip() for b in self.all_beats())

    def report(self) -> str:
        lines = [f"=== {self.title} ==="]
        lines.append(f"words: {self.word_count()}  |  est. runtime: {self.estimated_minutes():.1f} min"
                     f"  |  beats: {len(self.all_beats())}")
        for c in self.chapters:
            lines.append(f"  [{c.title}] {c.word_count()}w / {len(c.beats)} beats")
        lines.append(f"sources: {len(self.sources)}")
        return "\n".join(lines)

    def validate(self) -> List[str]:
        """Fail loudly rather than silently shipping something malformed --
        the same principle that caught the black-tail and mirrored-photo bugs."""
        issues = []
        if self.estimated_minutes() < 6:
            issues.append(f"too short for long-form monetization value: {self.estimated_minutes():.1f} min")
        if not self.sources:
            issues.append("no sources listed -- research depth is the whole edge, cite them")
        for i, b in enumerate(self.all_beats()):
            if not b.narration.strip():
                issues.append(f"beat {i} has empty narration")
            if not b.visual.strip():
                issues.append(f"beat {i} has no visual assigned")
            secs = b.word_count() / WORDS_PER_MINUTE * 60
            if secs > MAX_BEAT_SECONDS:
                issues.append(f"beat {i} runs ~{secs:.0f}s (>{MAX_BEAT_SECONDS:.0f}s) -- split it, "
                              f"long static holds are what made the Shorts feel dead")
        return issues

    def save(self, path: str):
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2)
        log(f"Script saved -> {path}")


def build_narration_file(script: DocScript, out_dir: str = None) -> str:
    """Write the full narration to a text file for review before any
    expensive TTS/render. Cheap to eyeball, catches problems early."""
    out_dir = out_dir or config.OUTPUT_DIR
    path = os.path.join(out_dir, "scripts", f"{_slug(script.title)}.txt")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"{script.title}\n{'=' * len(script.title)}\n\n")
        for c in script.chapters:
            f.write(f"\n## {c.title}\n\n")
            for b in c.beats:
                f.write(b.narration.strip() + "\n")
                f.write(f"    [visual: {b.kind} :: {b.visual}]\n")
        f.write("\n\n## SOURCES\n")
        for s in script.sources:
            f.write(f"- {s}\n")
    log(f"Narration written -> {path}")
    return path


def _slug(text: str) -> str:
    keep = [c.lower() if c.isalnum() else "_" for c in text]
    return "".join(keep).strip("_")[:60]


# ══════════════════════════════════════════════════════════════════════════
#  VISUAL SOURCING
# ══════════════════════════════════════════════════════════════════════════
# A 70-beat script has 70 distinct visual queries, but fetching 70 unique
# clips is neither possible nor desirable: it is 70 API calls plus 70 vision
# gate checks, free stock runs dry long before that, and real documentaries
# reuse footage constantly. Instead we group queries into themes, fetch a
# handful per theme, and rotate within the theme so consecutive beats never
# repeat the same shot.

THEMES = {
    # "soccer" and its vocabulary were missing: this table was written for the
    # NFL documentary, so on doc #3 (Garrincha) 81 of 115 beats -- nearly every
    # "soccer player dribbling" / "soccer match action" beat -- matched nothing
    # and fell through to DEFAULT_THEME "mood" (sunsets, empty streets, a bar).
    "football": ["football", "soccer", "helmet", "field", "stadium", "pitch",
                 "locker", "goal posts", "tunnel", "referee", "trophy",
                 "dribbling", "tackle", "header", "scoreboard"],
    "crowd":    ["crowd", "people", "seats", "lecture", "audience"],
    "money":    ["money", "cash", "coins", "wallet", "bank", "vault", "calculator", "salary"],
    "docs":     ["document", "paper", "newspaper", "magazine", "archive", "book",
                 "dictionary", "contract", "notebook", "filing", "textbook", "chalkboard"],
    "business": ["business", "office", "meeting", "handshake", "suit", "briefcase",
                 "desk", "interview", "courthouse", "signing"],
    "data":     ["chart", "graph", "data", "screen", "research", "television", "broadcast"],
    "home":     ["house", "living room", "driveway", "home", "hospital", "corridor", "hallway"],
    "mood":     ["sunset", "night", "light", "silhouette", "walking", "glass", "clock",
                 "calendar", "scales", "car", "keys", "camera", "microphone", "closed sign",
                 "worried", "piggy", "restaurant"],
}
DEFAULT_THEME = "mood"


def theme_for(query: str) -> str:
    q = query.lower()
    best, best_hits = DEFAULT_THEME, 0
    for theme, words in THEMES.items():
        hits = sum(1 for w in words if w in q)
        if hits > best_hits:
            best, best_hits = theme, hits
    return best


# Search terms used to actually fill each theme's pool. Deliberately plain
# and highly-stocked -- the vision gate rejects anything off-subject, staged,
# or cartoon, so broad-but-real beats clever-but-empty.
THEME_QUERIES = {
    # NOTE 2026-09-09: "football field aerial" and "american football stadium"
    # both return SOCCER pitches -- outside the US "football" means soccer, and
    # soccer dominates stock libraries. A documentary narrating "NFL" over
    # soccer footage undermines the one thing this format sells (research
    # rigour), so these must be queries only American football can satisfy.
    # Verified available on Pexels: exciting american football gameplay
    # (34396408), high school football highlights (32006306), american
    # football players (8266312), nfl hall of fame (26801995).
    "football": ["exciting american football gameplay",
                 "american football players",
                 "high school football game highlights"],
    "crowd":    ["stadium crowd cheering", "crowd of people walking", "audience seats"],
    "money":    ["counting money cash", "coins stack", "bank building"],
    "docs":     ["old documents paper", "newspaper printing", "books library shelves"],
    "business": ["business meeting office", "signing contract desk", "man in suit walking"],
    "data":     ["financial charts screen", "stock market graph", "data analytics screen"],
    "home":     ["suburban house exterior", "empty living room", "hospital hallway"],
    "mood":     ["city street night", "sunset silhouette", "clock ticking close up"],
}


def source_pool(script: DocScript, per_theme: int = 3, clip_dir: str = None) -> dict:
    """Fetch a small pool of real clips per theme actually used by the script.

    Uses the same vision-gated fetchers as the Shorts pipeline, so cartoons,
    3D renders and staged product shots are rejected automatically.
    """
    import visual_shorts_creator as vsc
    clip_dir = clip_dir or os.path.join(config.OUTPUT_DIR, "raw_clips")

    needed = sorted({theme_for(b.visual) for b in script.all_beats()})
    log(f"Themes needed: {needed}")

    used = set(int(x) for x in vsc._load_used_clip_ids().get("pexels", []))
    pool = {}
    for theme in needed:
        pool[theme] = []
        queries = (script.theme_queries or {}).get(theme) or THEME_QUERIES.get(theme, [theme])
        for q in queries:
            if len(pool[theme]) >= per_theme:
                break
            try:
                path, cid = vsc.fetch_pexels_clip(q, clip_dir, exclude_ids=used)
                vsc._record_used_clip_ids("pexels", {cid})
                used.add(cid)
                pool[theme].append(path)
                log(f"  [{theme}] {q} -> {os.path.basename(path)}")
            except Exception as e:
                log(f"  [{theme}] '{q}' failed: {e}")
        if not pool[theme]:
            log(f"  WARNING: theme '{theme}' is empty")

    # Heavy reuse is what produces black frames (see the note in render()).
    # If sourcing came up short, top the pool up with broad, reliably-stocked
    # terms until there is enough footage to keep reuse low.
    MIN_POOL_CLIPS = 22
    have = {p for paths in pool.values() for p in paths}
    if len(have) < MIN_POOL_CLIPS:
        log(f"  pool only {len(have)} clips -- topping up to {MIN_POOL_CLIPS}")
        filler = ["stadium crowd", "city street", "documents desk", "people walking",
                  "sunset sky", "empty room", "money cash", "sports field",
                  "office building", "night lights", "aerial town", "man walking"]
        themes_cycle = list(pool.keys()) or ["mood"]
        ti = 0
        for q in filler:
            if len(have) >= MIN_POOL_CLIPS:
                break
            try:
                path, cid = vsc.fetch_pexels_clip(q, clip_dir, exclude_ids=used)
                vsc._record_used_clip_ids("pexels", {cid})
                used.add(cid)
                have.add(path)
                # Filler is off-topic by definition ("documents desk", "city
                # street"). It used to be dealt round-robin INTO the topical
                # themes, which put a US tax form on Garrincha's debut hat-trick.
                # Keep it in its own bucket: assign_visuals() only reaches it
                # through the all-clips fallback when a beat's theme is empty.
                pool.setdefault("_filler", []).append(path)
                ti += 1
                log(f"  top-up '{q}' -> {os.path.basename(path)}")
            except Exception as e:
                log(f"  top-up '{q}' failed: {e}")
    log(f"  pool total: {len(have)} distinct clips")
    return pool


def bucket_for(script: DocScript, query: str) -> Optional[str]:
    """Name of the first visual bucket whose match terms appear in query."""
    q = query.lower()
    for name, spec in (script.visual_buckets or {}).items():
        if any(m in q for m in spec.get("match", [])):
            return name
    return None


def unmatched_beats(script: DocScript) -> List[str]:
    """Visual queries that no bucket claims -- these would render off-topic."""
    if not script.visual_buckets:
        return []
    return sorted({b.visual for b in script.all_beats() if bucket_for(script, b.visual) is None})


def _clip_readable(path: str) -> bool:
    """A downloaded clip that cannot produce a frame is worse than no clip:
    render() silently substitutes the previous beat. Reproduced 2026-09-14
    (pexels_8061370.mp4, 25MB, 'failed to read the first frame')."""
    from moviepy import VideoFileClip
    try:
        c = VideoFileClip(path, audio=False)
        c.get_frame(min(0.5, max(0.0, c.duration - 0.1)))
        ok = c.duration > 1.0 and _clip_brightness(c) >= MIN_CLIP_BRIGHTNESS
        c.close()
        return ok
    except Exception:
        return False


# Median frame brightness (0-255) a clip must reach to be used. A night
# fireworks clip averaging ~5 put 2.5s of near-black under the climax line
# of doc #4 ("Rinku Singh is a T20 World Cup champion", 2026-09-17). It beat
# the black-frame check because a few sparks were bright, and render()'s
# per-window _lit() probe could not help because every window was dark.
MIN_CLIP_BRIGHTNESS = 25.0


def _clip_brightness(clip) -> float:
    import numpy as _np
    ts = [clip.duration * f for f in (0.1, 0.3, 0.5, 0.7, 0.9)]
    return float(_np.median([clip.get_frame(t).mean() for t in ts]))


def downscale_clip(path: str, max_short_side: int = 1080) -> bool:
    """Re-encode a clip in place so its short side is at most 1080px, no audio.

    The render is 1920x1080, but Pexels often serves 4K. Every open reader
    decodes at source size, so a 4K clip costs ~4x the RAM and CPU of a 1080p
    one for zero visible gain. Measured 2026-09-18 on doc #5: 24 of 44 clips
    were 1440p/4K, single ffmpeg readers held 1.1-1.2 GB each, free RAM hit
    0.4 GB, and batch 1 took 82 minutes instead of ~8. Returns True if the
    file was re-encoded.
    """
    import re
    import subprocess
    import imageio_ffmpeg
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    info = subprocess.run([exe, "-hide_banner", "-i", path], capture_output=True, text=True).stderr
    m = re.search(r"Video: .*?, (\d{3,5})x(\d{3,5})", info)
    if not m:
        return False
    w, h = int(m.group(1)), int(m.group(2))
    if min(w, h) <= max_short_side:
        return False
    vf = (f"scale=-2:{max_short_side}" if w >= h else f"scale={max_short_side}:-2")
    tmp = path + ".1080.mp4"
    r = subprocess.run([exe, "-y", "-loglevel", "error", "-i", path, "-vf", vf, "-an",
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                        "-pix_fmt", "yuv420p", tmp], capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(tmp) or os.path.getsize(tmp) < 10000:
        if os.path.exists(tmp):
            os.remove(tmp)
        return False
    os.replace(tmp, path)
    return True


def source_buckets(script: DocScript, clip_dir: str = None) -> dict:
    """Fill each visual bucket the script actually uses with `n` distinct,
    vision-gated, readable clips. No filler is ever dealt into a bucket."""
    import visual_shorts_creator as vsc
    clip_dir = clip_dir or os.path.join(config.OUTPUT_DIR, "raw_clips")
    used = set(int(x) for x in vsc._load_used_clip_ids().get("pexels", []))
    demand = {}
    for b in script.all_beats():
        name = bucket_for(script, b.visual)
        if name:
            demand[name] = demand.get(name, 0) + 1
    log(f"Bucket demand (beats): {demand}")

    pool = {}
    for name, spec in script.visual_buckets.items():
        if name not in demand:
            continue
        target = spec.get("n", 3)
        queries = spec.get("queries") or [name]
        pool[name] = []
        attempts, qi = 0, 0
        while len(pool[name]) < target and attempts < target * 3:
            q = queries[qi % len(queries)]
            qi += 1
            attempts += 1
            try:
                path, cid = vsc.fetch_pexels_clip(q, clip_dir, exclude_ids=used)
                vsc._record_used_clip_ids("pexels", {cid})
                used.add(cid)
                if downscale_clip(path):
                    log(f"  [{name}] {os.path.basename(path)} downscaled to 1080p")
                if not _clip_readable(path):
                    log(f"  [{name}] {os.path.basename(path)} unreadable -- discarded")
                    try:
                        os.remove(path)
                    except OSError:
                        pass
                    continue
                pool[name].append(path)
                log(f"  [{name}] {q} -> {os.path.basename(path)}")
            except Exception as e:
                log(f"  [{name}] '{q}' failed: {e}")
        if not pool[name]:
            log(f"  WARNING: bucket '{name}' is empty")
    log(f"  bucket pool: {sum(len(v) for v in pool.values())} distinct clips "
        f"across {len(pool)} buckets")
    return pool


def beat_alternates(script: DocScript, pool: dict) -> List[List[str]]:
    """For each beat, every clip on the same subject -- render() uses this to
    swap in a long-enough clip WITHOUT leaving the beat's subject."""
    out = []
    for beat in script.all_beats():
        key = (bucket_for(script, beat.visual) if script.visual_buckets else None) \
            or theme_for(beat.visual)
        out.append(list(pool.get(key) or []))
    return out


def assign_visuals(script: DocScript, pool: dict) -> List[Optional[str]]:
    """Map every beat to a clip, rotating within its theme so the same shot
    never lands on two consecutive beats. Falls back across themes if a
    theme came back empty, so a sourcing gap degrades instead of crashing."""
    all_clips = [p for paths in pool.values() for p in paths]
    if not all_clips:
        raise RuntimeError("No visuals sourced at all -- cannot build")

    counters = {t: 0 for t in pool}
    assigned, last = [], None
    for beat in script.all_beats():
        theme = ((bucket_for(script, beat.visual) if script.visual_buckets else None)
                 or theme_for(beat.visual))
        options = pool.get(theme) or all_clips
        if len(options) > 1 and last in options:
            rotated = [p for p in options if p != last]
        else:
            rotated = options
        idx = counters.get(theme, 0) % len(rotated)
        counters[theme] = counters.get(theme, 0) + 1
        choice = rotated[idx]
        assigned.append(choice)
        last = choice
    return assigned


# ══════════════════════════════════════════════════════════════════════════
#  VOICEOVER
# ══════════════════════════════════════════════════════════════════════════
# psc.generate_voiceover() is Shorts-shaped: it assembles hook/body/cta and
# appends the persona sign-off. Neither applies here -- a documentary has its
# own written outro, and the sign-off costs ~4s that a Short cannot spare but
# a 7-minute video does not need anyway. Long narration is also chunked at
# sentence boundaries so one failed request cannot lose the whole read.

TTS_CHUNK_CHARS = 2500


def _chunk_text(text: str, limit: int = TTS_CHUNK_CHARS) -> List[str]:
    import re
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    chunks, cur = [], ""
    for s in sentences:
        if len(cur) + len(s) + 1 > limit and cur:
            chunks.append(cur.strip())
            cur = s
        else:
            cur = f"{cur} {s}".strip()
    if cur:
        chunks.append(cur.strip())
    return chunks


def generate_long_voiceover(script: DocScript, out_dir: str = None) -> str:
    """Narrate the full documentary via ElevenLabs, chunked and concatenated."""
    import time
    import requests
    from moviepy import AudioFileClip, concatenate_audioclips

    out_dir = out_dir or config.AUDIO_DIR
    os.makedirs(out_dir, exist_ok=True)
    text = script.narration_text()
    chunks = _chunk_text(text)
    log(f"Narration: {len(text)} chars -> {len(chunks)} TTS chunks")

    # ElevenLabs first, but never let an empty quota block a documentary.
    # Measured 2026-09-11: the account sits at 0 of 10,000 credits, and one
    # documentary needs ~6,500 -- roughly 23x a Short. The cloned voice is
    # now loudness-normalised to the same level as ElevenLabs
    # (pro_shorts_creator.normalize_voice), so falling back costs clarity,
    # not volume.
    use_eleven = bool(config.ELEVENLABS_API_KEY)

    import pro_shorts_creator as psc

    stamp = int(time.time())
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{config.ELEVENLABS_VOICE_ID}"
    parts = []
    for i, chunk in enumerate(chunks):
        done = False
        if use_eleven:
            path = os.path.join(out_dir, f"lf_{stamp}_{i:02d}.mp3")
            try:
                r = requests.post(
                    url,
                    json={"text": chunk, "model_id": "eleven_turbo_v2_5",
                          "voice_settings": {"stability": 0.50, "similarity_boost": 0.80}},
                    headers={"xi-api-key": config.ELEVENLABS_API_KEY},
                    timeout=180,
                )
                if r.status_code == 200:
                    with open(path, "wb") as f:
                        f.write(r.content)
                    parts.append(path)
                    log(f"  chunk {i+1}/{len(chunks)} ElevenLabs ok ({len(chunk)} chars)")
                    done = True
                else:
                    body = (r.text or "")[:200]
                    if "quota" in body.lower() or "credits remaining" in body.lower():
                        log(f"  ElevenLabs quota exhausted -> cloned voice for all chunks")
                        use_eleven = False
                    else:
                        log(f"  ElevenLabs {r.status_code} -> cloned voice for this chunk")
            except Exception as e:
                log(f"  ElevenLabs error ({e}) -> cloned voice")

        if not done:
            path = os.path.join(out_dir, f"lf_{stamp}_{i:02d}.wav")
            psc._generate_cloned_voice(chunk, path)
            parts.append(path)
            log(f"  chunk {i+1}/{len(chunks)} cloned ok ({len(chunk)} chars)")

    out_path = os.path.join(out_dir, f"lf_voice_{stamp}.mp3")
    clips = [AudioFileClip(p) for p in parts]
    concatenate_audioclips(clips).write_audiofile(out_path, logger=None)
    for c in clips:
        try:
            c.close()
        except Exception:
            pass
    # Same loudness treatment the Shorts pipeline uses, so a documentary
    # narrated by the cloned voice is not quieter than one narrated by
    # ElevenLabs.
    psc.normalize_voice(out_path)
    dur = AudioFileClip(out_path).duration
    log(f"Voiceover complete: {out_path} ({dur/60:.1f} min)")
    return out_path


# ══════════════════════════════════════════════════════════════════════════
#  RENDER  (16:9 landscape -- long-form is NOT vertical)
# ══════════════════════════════════════════════════════════════════════════
LF_WIDTH, LF_HEIGHT, LF_FPS = 1920, 1080, 30


def _norm_tok(t: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]", "", t.lower())


def _script_to_word_index(script: DocScript, words: list) -> List[int]:
    """For every script token, the index of the measured word it was spoken as."""
    import difflib
    toks = script.narration_text().split()
    a = [_norm_tok(w["word"]) for w in words]
    b = [_norm_tok(t) for t in toks]
    j2i = [0] * len(b)
    last = len(words) - 1
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        for k in range(j2 - j1):
            j2i[j1 + k] = min(i1 + min(k, max(0, i2 - i1 - 1)), last)
    return j2i


def correct_word_timestamps(script: DocScript, vo_path: str) -> int:
    """Rewrite the cached word timings so captions show the SCRIPT words.

    Whisper does not know proper nouns: on doc #3 it rendered Garrincha as
    "Goringa", "Garica" and -- on screen, in the closing epitaph -- "Gariaka",
    plus "Botophago", "bonesoceso", "a ren". Captions and the uploaded SRT
    both read this cache, so both were wrong. Timings are kept as measured;
    only the text changes. Always rebuilt from the untouched raw copy, so
    running it twice is harmless.
    """
    import difflib
    import shutil
    cache = vo_path + ".words.json"
    raw = vo_path + ".words.whisper_raw.json"
    if not os.path.exists(cache):
        return 0
    if not os.path.exists(raw):
        shutil.copyfile(cache, raw)
    with open(raw, encoding="utf-8") as f:
        words = json.load(f)
    toks = script.narration_text().split()
    a = [_norm_tok(w["word"]) for w in words]
    b = [_norm_tok(t) for t in toks]
    out, changed = [], 0
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        block = [dict(w) for w in words[i1:i2]]
        span = toks[j1:j2]
        if op == "equal" or (op == "replace" and (i2 - i1) == (j2 - j1)):
            for k, w in enumerate(block):
                if w["word"] != span[k]:
                    w["word"] = span[k]
                    changed += 1
            out.extend(block)
        elif op == "replace" and any(ch.isdigit() for w in block for ch in w["word"]):
            # Keep numerals ("1933" reads better on screen than "nineteen
            # thirty three") but still repair names inside the block
            # ("1983, Gariaka" becomes "1983, Garrincha").
            for w in block:
                nw = _norm_tok(w["word"])
                if nw.isalpha() and len(nw) >= 4:
                    best = max(span, key=lambda t: difflib.SequenceMatcher(None, nw, _norm_tok(t)).ratio())
                    if difflib.SequenceMatcher(None, nw, _norm_tok(best)).ratio() >= 0.6:
                        w["word"] = best
                        changed += 1
            out.extend(block)
        elif op == "replace":
            # All-letter mismatch ("man will" -> "manual", "heres" -> "here is"):
            # one entry spanning the block, carrying the script text.
            merged = dict(block[0])
            merged["word"] = " ".join(span)
            merged["end"] = block[-1]["end"]
            out.append(merged)
            changed += 1
        elif op == "insert":
            if out:
                out[-1]["word"] = out[-1]["word"] + " " + " ".join(span)
                changed += 1
        else:
            out.extend(block)
    with open(cache, "w", encoding="utf-8") as f:
        json.dump(out, f)
    log(f"  captions aligned to script spelling: {changed} tokens corrected")
    return changed


def beat_timings(script: DocScript, vo_path: str) -> List[tuple]:
    """(start, duration) per beat, taken from the voiceover's MEASURED word
    timestamps rather than guessed from word counts. Falls back to
    proportional split if transcription is unavailable."""
    import pro_shorts_creator as psc
    from moviepy import AudioFileClip

    total = AudioFileClip(vo_path).duration
    beats = script.all_beats()
    counts = [max(1, b.word_count()) for b in beats]

    words = []
    try:
        words = psc.get_word_timestamps(vo_path) or []
    except Exception as e:
        log(f"  word timestamps unavailable ({e}) -- using proportional timing")

    if words:
        correct_word_timestamps(script, vo_path)
        words = psc.get_word_timestamps(vo_path) or words

    script_words = sum(counts)
    if len(words) >= script_words * 0.7:
        # Two bugs fixed here (2026-09-14, doc #3):
        #
        # 1. Beats used to walk the transcript by SCRIPT word counts. Whisper
        #    writes "nineteen thirty three" as ONE token ("1933"), so every
        #    number slipped the index and beat boundaries drifted. Boundaries
        #    now come from aligning script tokens to measured words.
        #
        # 2. Each beat spanned first-word-start to last-word-end, so the pause
        #    BETWEEN beats belonged to no beat. Across 115 beats that dropped
        #    ~4.4s: the video ended before the audio, cutting the closing
        #    "subscribe" line, and because overlays are timed by the audio
        #    clock while footage advanced by the shorter durations, captions
        #    ran up to 4.6s AHEAD of the voice by the end. Beats are now
        #    contiguous -- each runs to the next beat's first word, the last to
        #    the end of the audio -- so durations sum to the voiceover exactly.
        j2i = _script_to_word_index(script, words)
        firsts, j = [], 0
        for n in counts:
            firsts.append(j)
            j += n
        starts = [0.0]
        for jf in firsts[1:]:
            st = words[j2i[min(jf, len(j2i) - 1)]]["start"]
            starts.append(max(st, starts[-1]))
        timings = []
        for k, st in enumerate(starts):
            nxt = starts[k + 1] if k + 1 < len(starts) else total
            timings.append((st, max(0.3, nxt - st)))
        log(f"  timing from measured word timestamps ({len(words)} words, "
            f"contiguous, sum {sum(d for _, d in timings):.1f}s / audio {total:.1f}s)")
        return timings

    timings, t = [], 0.0
    for n in counts:
        d = total * (n / script_words)
        timings.append((t, d))
        t += d
    log("  timing proportional (transcription too sparse)")
    return timings


def _fit_landscape(clip):
    """Cover-fit any source clip into 1920x1080 without stretching."""
    import pro_shorts_creator as psc
    sw, sh = clip.size
    scale = max(LF_WIDTH / sw, LF_HEIGHT / sh)
    clip = psc._resize(clip, (int(sw * scale), int(sh * scale)))
    cw, ch = clip.size
    x, y = (cw - LF_WIDTH) // 2, (ch - LF_HEIGHT) // 2
    return psc._crop(clip, x, y, x + LF_WIDTH, y + LF_HEIGHT)




# ══════════════════════════════════════════════════════════════════════════
#  ON-SCREEN OVERLAY  (captions synced to the actual voice, hook, subscribe)
# ══════════════════════════════════════════════════════════════════════════
# This did not exist until 2026-09-12, and its absence was the real problem
# with the first two documentaries. Every overlay -- word captions, hook
# card, subscribe button -- lived in pro_shorts_creator.render_overlay and
# was used ONLY by the Shorts pipeline. Long-form rendered bare footage with
# an AI voice and NO text of any kind: no captions to follow, no subscribe
# ask, nothing on screen at all. Days were spent chasing black frames while
# the video was unwatchable for a much more basic reason.
#
# Captions here are driven by MEASURED word timestamps from the actual
# narration audio, so what is on screen is exactly what is being said at
# that moment, rather than a guess from word counts.

LF_HOOK_DUR = 4.0
LF_SUB_EARLY = (5.0, 4.0)     # (start, length) seconds
LF_SUB_LATE_BEFORE_END = 12.0


def _lf_font(size, bold=True):
    import pro_shorts_creator as psc
    return psc.get_font(size, bold=bold)


def render_lf_overlay(frame, script, t, duration, word_timestamps):
    """Draw synced captions + hook card + subscribe prompts on a 1920x1080 frame."""
    import math
    import numpy as np
    from PIL import Image, ImageDraw

    W, H = LF_WIDTH, LF_HEIGHT
    img = Image.fromarray(frame)
    draw = ImageDraw.Draw(img)

    # ---- word-synced caption band (bottom) ----------------------------
    words = word_timestamps or []
    phrase = ""
    if words:
        idx = 0
        for i, w in enumerate(words):
            if w["start"] <= t:
                idx = i
            else:
                break
        group = idx // 4
        chunk = words[group * 4:(group + 1) * 4]
        phrase = " ".join(w.get("word", "").strip() for w in chunk).strip()

    if phrase:
        size = 54
        font = _lf_font(size)
        while size > 34 and draw.textbbox((0, 0), phrase, font=font)[2] > W - 320:
            size -= 3
            font = _lf_font(size)
        bb = draw.textbbox((0, 0), phrase, font=font)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        x, y = (W - tw) // 2, H - 150

        ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(ov).rectangle(
            [(x - 34, y - 22), (x + tw + 34, y + th + 26)], fill=(0, 0, 0, 165))
        img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
        draw = ImageDraw.Draw(img)
        draw.text((x, y), phrase, font=font, fill=(255, 255, 255),
                  stroke_width=4, stroke_fill=(0, 0, 0))

    # ---- hook card, first seconds -------------------------------------
    card = getattr(script, "hook_card", "") or ""
    if card and t < LF_HOOK_DUR:
        fade = 1.0 if t < LF_HOOK_DUR - 0.5 else max(0.0, (LF_HOOK_DUR - t) / 0.5)
        hs = 104
        hf = _lf_font(hs)
        while hs > 60 and draw.textbbox((0, 0), card, font=hf)[2] > W - 180:
            hs -= 5
            hf = _lf_font(hs)
        hb = draw.textbbox((0, 0), card, font=hf)
        hx, hy = (W - (hb[2] - hb[0])) // 2, int(H * 0.17)
        band = int(255 * 0.55 * fade)
        if band > 0:
            ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
            ImageDraw.Draw(ov).rectangle(
                [(0, hy - 30), (W, hy + (hb[3] - hb[1]) + 34)], fill=(0, 0, 0, band))
            img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
            draw = ImageDraw.Draw(img)
        sh = int(255 * fade)
        draw.text((hx, hy), card, font=hf, fill=(sh, sh, sh),
                  stroke_width=6, stroke_fill=(0, 0, 0))

    # ---- subscribe button: early, and again near the end ---------------
    def _sub(et, length):
        if et < 0.3:
            sc = 1.12 * (et / 0.3)
        elif et > length - 0.5:
            sc = max(0.01, (length - et) / 0.5)
        else:
            sc = 1.0 + 0.04 * math.sin((et - 0.3) * 5.0)
        sc = max(0.01, sc)
        bw, bh = int(300 * sc), int(66 * sc)
        bx, by = W - bw - 70, int(H * 0.13)
        glow = int(12 * (0.5 + 0.5 * math.sin(et * 6.0)))
        draw.rounded_rectangle([bx - glow, by - glow, bx + bw + glow, by + bh + glow],
                               radius=20, fill=(120, 0, 0))
        draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=14, fill=(255, 0, 0))
        f = _lf_font(max(1, int(27 * sc)))
        txt = "SUBSCRIBE"
        tb = draw.textbbox((0, 0), txt, font=f)
        draw.text((bx + (bw - (tb[2] - tb[0])) // 2,
                   by + (bh - (tb[3] - tb[1])) // 2 - 2),
                  txt, font=f, fill=(255, 255, 255))

    s0, sl = LF_SUB_EARLY
    if s0 <= t < s0 + sl:
        _sub(t - s0, sl)
    late = duration - LF_SUB_LATE_BEFORE_END
    if late <= t < late + 8.0:
        _sub(t - late, 8.0)

    return np.array(img)


# Beats per intermediate file when batching. 115 beats (doc #3) exhausted
# 15.7GB of RAM and died allocating the 63MiB composite background; 90 beats
# (doc #2) only just fit. 25 keeps peak memory roughly flat no matter how
# long the script gets.
# Lowered 25 -> 12 on 2026-09-18: every clip in a batch holds an open
# ffmpeg reader (~350 MB each at 1080p), so 22 readers took ~8 GB of this
# 15.7 GB machine and left 0.6 GB for everything else. ~10 readers keeps
# the render near 3.5 GB at the cost of a few more parts to join.
CONCAT_BATCH = 12


def _concat_batched(segments, out_path):
    """Concatenate beat segments without holding them all in memory.

    Two separate problems are fixed here:

    1. method="compose" builds a CompositeVideoClip, which allocates a
       full-frame ColorClip background. Every segment is already normalised
       to the same size by _fit_landscape(), so that background buys nothing
       and costs a 1920x1080x4 int64 array. "chain" skips it entirely.

    2. Even chained, every segment stays open until the final encode reads
       it, so peak memory scales with beat count. Above CONCAT_BATCH beats,
       each batch is written to its own intermediate file and closed, then
       the (cheap, single-reader) intermediates are chained together.

    Reproduced 2026-09-13: 115 segments -> MemoryError before a single frame
    was written.
    """
    # render() imports concatenate_videoclips locally, so a module-level
    # helper has to import it itself.
    from moviepy import VideoFileClip, concatenate_videoclips

    if len(segments) <= CONCAT_BATCH:
        return concatenate_videoclips(segments, method="chain")

    tmp_dir = os.path.join(config.OUTPUT_DIR, "lf_parts")
    os.makedirs(tmp_dir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(out_path))[0]
    parts = []

    for bi in range(0, len(segments), CONCAT_BATCH):
        batch = segments[bi:bi + CONCAT_BATCH]
        part_path = os.path.join(tmp_dir, f"{stem}_part{bi // CONCAT_BATCH:02d}.mp4")
        log(f"  batch {bi // CONCAT_BATCH + 1}: {len(batch)} beats -> {os.path.basename(part_path)}")
        joined = concatenate_videoclips(batch, method="chain")
        # Video only -- the voiceover and music are mixed onto the final
        # timeline after all parts are joined.
        joined.write_videofile(
            part_path, fps=LF_FPS, codec="libx264", audio=False, logger=None,
            threads=8, ffmpeg_params=["-crf", "18", "-preset", "faster",
                                      "-pix_fmt", "yuv420p"],
        )
        joined.close()
        for s in batch:
            try:
                s.close()
            except Exception:
                pass
        parts.append(part_path)

    log(f"  joining {len(parts)} rendered parts")
    return concatenate_videoclips([VideoFileClip(p) for p in parts], method="chain")


def render(script: DocScript, beat_clips: List[str], vo_path: str,
           music_path: str, out_path: str,
           alternates: Optional[List[List[str]]] = None) -> str:
    """Assemble the documentary: one visual per beat, timed to the narration."""
    import pro_shorts_creator as psc
    from moviepy import (VideoFileClip, AudioFileClip, CompositeAudioClip,
                         concatenate_videoclips)

    timings = beat_timings(script, vo_path)
    beats = script.all_beats()
    log(f"Building {len(beats)} beats -> {out_path}")

    # Measured word timings drive the on-screen captions, so what is written
    # is exactly what is being spoken at that instant.
    try:
        words_all = psc.get_word_timestamps(vo_path) or []
        log(f"  caption sync: {len(words_all)} measured word timings")
    except Exception as e:
        words_all = []
        log(f"  caption sync unavailable ({e}) -- captions will be skipped")
    from moviepy import AudioFileClip as _AFC
    total_dur = _AFC(vo_path).duration

    # Measure every clip once so a beat can be given a clip long enough for it.
    durations = {}
    for cp in set(beat_clips) | {p for alts in (alternates or []) for p in alts}:
        try:
            probe = VideoFileClip(cp, audio=False)
            durations[cp] = probe.duration
            probe.close()
        except Exception as e:
            log(f"  cannot read {os.path.basename(cp)}: {e}")
            durations[cp] = 0.0

    # Readers are opened, used and CLOSED one batch at a time.
    # Building all 115 segments up front kept a reader open for every distinct
    # clip until the final encode. With 19 clips that fit; with the 38
    # subject-matched clips doc #3 needs, the 29th VideoFileClip() blocked
    # forever in read_frame waiting on ffmpeg (py-spy, 2026-09-14: 4 hours at
    # 0 CPU, 28 ffmpeg children, no part file). Per-batch readers cap open
    # handles at one batch's clips no matter how many the script uses.
    TAIL_PAD = 2.0
    tmp_dir = os.path.join(config.OUTPUT_DIR, "lf_parts")
    os.makedirs(tmp_dir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(out_path))[0]
    all_items = list(zip(beats, beat_clips, timings))
    parts = []
    for bi in range(0, len(all_items), CONCAT_BATCH):
        cache, segments, pending_front = {}, [], 0.0
        for i, (beat, clip_path, (start, dur)) in enumerate(
                all_items[bi:bi + CONCAT_BATCH], start=bi):
            try:
                # A clip shorter than its beat used to be looped by concatenating
                # the SAME clip object several times. That shares one ffmpeg
                # reader between copies, which fight over seek position and emit
                # BLACK frames -- reproduced 2026-09-12 as intermittent black at
                # 4s, 6s and 12s while every source clip measured perfectly fine.
                # Swapping in a clip that is genuinely long enough avoids the
                # whole class of problem; there is always a longer one in the pool.
                if durations.get(clip_path, 0) < dur + 0.3:
                    # Stay on the beat's SUBJECT. Swapping in the longest clip in
                    # the whole pool is how a bar on a street kept landing on
                    # unrelated beats in doc #3. Global longest is last resort.
                    same = [p for p in (alternates[i] if alternates and i < len(alternates) else [])
                            if durations.get(p, 0) >= dur + 0.3]
                    if same:
                        clip_path = max(same, key=lambda k: durations[k])
                    else:
                        longer = max(durations, key=lambda k: durations[k])
                        if durations[longer] >= dur + 0.3:
                            log(f"  beat {i}: no same-subject clip >= {dur:.1f}s, "
                                f"using {os.path.basename(longer)}")
                            clip_path = longer
                # Shared readers are fine PROVIDED clips are not reused heavily.
                # Measured 2026-09-12: 26 clips over 90 beats rendered clean,
                # 13 clips over the same 90 beats produced 20 black frames in 80
                # samples -- segments sharing one ffmpeg reader seek it to
                # different positions and collide. Opening a reader per beat was
                # tried and blew up ffmpeg with Errno 22 (too many handles), so
                # the real defence is guaranteeing enough distinct clips up front
                # -- see MIN_POOL_CLIPS in source_pool().
                if clip_path not in cache:
                    cache[clip_path] = VideoFileClip(clip_path, audio=False)
                src = cache[clip_path]
                # Walk through the source so repeated use of one clip shows a
                # different moment each time rather than the same three seconds.
                offset = (i * 2.7) % max(0.1, src.duration - dur - 0.2) if src.duration > dur + 0.4 else 0.0

                # Check the chosen window is actually LIT before committing to it.
                # Many stock clips fade to black at their tail, and the rotating
                # offset can land a beat squarely in that fade -- reproduced
                # 2026-09-12 as a 2s black gap at 120s while every clip measured
                # fine at t=1.0, because the sampling never looked at the end.
                def _lit(o):
                    try:
                        import numpy as _np
                        probe_t = min(src.duration - 0.05, o + dur * 0.5)
                        return float(_np.mean(src.get_frame(max(0.0, probe_t)))) > 8.0
                    except Exception:
                        return True

                if not _lit(offset):
                    for alt in (0.0, src.duration * 0.25, src.duration * 0.4,
                                src.duration * 0.1, src.duration * 0.55):
                        alt = max(0.0, min(alt, max(0.0, src.duration - dur - 0.1)))
                        if _lit(alt):
                            log(f"  beat {i}: window at {offset:.1f}s was black, moved to {alt:.1f}s")
                            offset = alt
                            break

                piece = src.subclipped(offset, min(offset + dur, src.duration))
                piece = piece.subclipped(0, min(dur, piece.duration))
                piece = _fit_landscape(piece)
                piece = psc._dur(piece, dur)

                # Draw the overlay for THIS beat, offset into the global timeline
                # so captions stay locked to the narration audio.
                _st = start
                def _ov(gf, tt, _st=_st):
                    try:
                        return render_lf_overlay(gf(tt), script, _st + tt, total_dur, words_all)
                    except Exception:
                        return gf(tt)
                piece = psc._fl(piece, _ov)
                piece = psc._dur(piece, dur)
                segments.append(piece)
            except Exception as e:
                log(f"  beat {i} failed ({e}) -- reusing neighbour")
                if segments:
                    segments.append(psc._dur(segments[-1], dur))
                else:
                    pending_front += dur
            if pending_front and len(segments) == 1:
                # A batch's first beat(s) failed: cover their time with the
                # first good segment so captions stay locked to the audio.
                segments.insert(0, psc._dur(segments[0], pending_front))
                pending_front = 0.0

        if not segments:
            raise RuntimeError(f"No segments built in batch starting at beat {bi}")
        if bi + CONCAT_BATCH >= len(all_items):
            # Pad the FINAL segment before concatenating. Extending a composite
            # to match the audio reads past real content and renders pure
            # black (Shorts 2026-08-30, long-form 2026-09-08). Build LONGER
            # than needed, then only ever TRIM: trimming is safe, extending is not.
            segments[-1] = psc._dur(segments[-1], segments[-1].duration + TAIL_PAD)

        part_path = os.path.join(tmp_dir, f"{stem}_part{bi // CONCAT_BATCH:02d}.mp4")
        log(f"  batch {bi // CONCAT_BATCH + 1}: {len(segments)} beats, "
            f"{len(cache)} readers -> {os.path.basename(part_path)}")
        joined = concatenate_videoclips(segments, method="chain")
        joined.write_videofile(
            part_path, fps=LF_FPS, codec="libx264", audio=False, logger=None,
            threads=8, ffmpeg_params=["-crf", "18", "-preset", "faster",
                                      "-pix_fmt", "yuv420p"],
        )
        joined.close()
        for seg in segments:
            try:
                seg.close()
            except Exception:
                pass
        for reader in cache.values():
            try:
                reader.close()
            except Exception:
                pass
        parts.append(part_path)

    log(f"  joining {len(parts)} rendered parts")
    video = concatenate_videoclips([VideoFileClip(pp) for pp in parts], method="chain")

    vo = AudioFileClip(vo_path)
    if video.duration >= vo.duration:
        video = video.subclipped(0, vo.duration)
    else:
        # Never extend into blackness -- trim the audio to the real footage.
        log(f"  video ({video.duration:.1f}s) shorter than audio "
            f"({vo.duration:.1f}s) -- trimming audio to match")
        vo = vo.subclipped(0, video.duration)
    tracks = [vo]
    if music_path and os.path.exists(music_path):
        try:
            m = AudioFileClip(music_path)
            loops = int(vo.duration // m.duration) + 1
            from moviepy import concatenate_audioclips
            m = psc._dur(concatenate_audioclips([m] * loops), vo.duration)
            tracks.append(psc._vol(m, 0.05))
        except Exception as e:
            log(f"  music skipped ({e})")
    video = psc._audio(video, CompositeAudioClip(tracks))

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    video.write_videofile(out_path, fps=LF_FPS, codec="libx264",
                          audio_codec="aac", preset="medium",
                          ffmpeg_params=["-pix_fmt", "yuv420p"], logger=None)
    for c in cache.values():
        try:
            c.close()
        except Exception:
            pass
    log(f"RENDER COMPLETE -> {out_path}")
    return out_path
