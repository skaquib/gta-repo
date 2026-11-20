"""
copyright_compliance.py
=======================
Pre-upload validation: YouTube Community Guidelines, copyright-safe assets,
and script content checks. Blocks upload when risk is too high.
"""

import re
import os
import json
import config
from logger import log

# Phrases that suggest broadcast/TV footage or copyright evasion
BANNED_SCRIPT_PATTERNS = [
    r"\bbroadcast\b",
    r"\bhighlights?\s+reel\b",
    r"\bofficial\s+match\s+footage\b",
    r"\bcontent\s*id\b",
    r"\bmirror(?:ed|ing)?\s+(?:to\s+)?bypass\b",
    r"\bfox\s+sports\b",
    r"\bespn\b",
    r"\bbein\s+sports\b",
    r"\bsky\s+sports\b",
    r"\bbt\s+sport\b",
    r"\btelevision\b",
    r"\btv\s+clip\b",
]

# Directories (relative to config.OUTPUT_DIR) that only ever contain assets
# from a verified-safe source: AI-generated (AnimateDiff/image-gen) or
# licensed/royalty-free stock (Pexels, Pixabay, git asset library).
SAFE_ASSET_SUBDIRS = ("anime_clips", "raw_clips", "ai_images", "git_assets", "temp_freeze")

# Filenames produced by our own stock-footage fetchers (visual_shorts_creator.
# fetch_pexels_clip / fetch_clip) — licensed for commercial use (Pexels) or
# CC0 (Pixabay).
SAFE_FILENAME_PATTERNS = [
    re.compile(r"^pexels_\d+\.mp4$"),
    re.compile(r"^clip_\d+_\w+\.mp4$"),
]

# YouTube Community Guidelines checklist (automated heuristics)
GUIDELINE_CHECKS = [
    {
        "id": "no_misleading_title",
        "desc": "Title must not be empty and under 100 chars",
        "fn": lambda s, _: bool(s.get("title", "").strip()) and len(s.get("title", "")) <= 100,
    },
    {
        "id": "has_shorts_tag",
        "desc": "Shorts must include #shorts in title (long-form scripts set format='long')",
        "fn": lambda s, _: s.get("format") == "long" or "#shorts" in s.get("title", "").lower(),
    },
    {
        "id": "hook_present",
        "desc": "Script must have a hook in first 3 seconds",
        "fn": lambda s, _: len(s.get("hook", "").strip()) >= 10,
    },
    {
        "id": "cta_engagement",
        "desc": "Must include viewer engagement CTA",
        "fn": lambda s, _: any(w in s.get("cta", "").lower() for w in ["comment", "subscribe", "?", "vote", "drop"]),
    },
    {
        "id": "no_hate_speech",
        "desc": "No hate speech patterns",
        "fn": lambda s, _: not _has_hate_patterns(s),
    },
    {
        "id": "body_length_ok",
        "desc": "Body text reasonable length (Shorts 20-1500 chars, long-form 20-20000)",
        "fn": lambda s, _: 20 <= len(s.get("body", "")) <= (20000 if s.get("format") == "long" else 1500),
    },
]


def _has_hate_patterns(script: dict) -> bool:
    text = " ".join([script.get("hook", ""), script.get("body", ""), script.get("cta", "")]).lower()
    hate = ["kill all", "hate all", "racial slur", "nazi", "genocide"]
    return any(h in text for h in hate)


def check_script_copyright(script: dict) -> list:
    """Return list of copyright violation messages (empty = pass)."""
    issues = []
    full_text = " ".join([
        script.get("hook", ""), script.get("body", ""), script.get("cta", ""),
        script.get("title", ""),
    ]).lower()

    for pat in BANNED_SCRIPT_PATTERNS:
        if re.search(pat, full_text, re.I):
            issues.append(f"Script references risky content: pattern '{pat}'")

    return issues


def check_guidelines(script: dict) -> list:
    """Return list of failed guideline check descriptions."""
    failed = []
    for check in GUIDELINE_CHECKS:
        try:
            if not check["fn"](script, None):
                failed.append(check["desc"])
        except Exception as e:
            failed.append(f"{check['id']}: {e}")
    return failed


def _has_safe_provenance(path: str) -> bool:
    """True if a clip path lives under a known-safe asset directory or matches
    a filename pattern produced by our own licensed stock-footage fetchers."""
    norm = os.path.normpath(path)
    parts = norm.split(os.sep)
    if any(d in parts for d in SAFE_ASSET_SUBDIRS):
        return True
    fname = os.path.basename(norm)
    return any(pat.match(fname) for pat in SAFE_FILENAME_PATTERNS)


def check_asset_paths(clip_paths: list, music_path: str = None) -> list:
    """Verify assets exist, aren't suspiciously small (corrupt/placeholder),
    and come from a verified-safe source (AI-generated or licensed/royalty-free
    stock) rather than an arbitrary/unknown download."""
    issues = []
    for p in clip_paths or []:
        if not os.path.exists(p):
            issues.append(f"Missing clip: {p}")
            continue
        if os.path.getsize(p) < 50_000:
            issues.append(f"Clip too small (likely corrupt): {p}")
        if not _has_safe_provenance(p):
            issues.append(
                f"Clip provenance cannot be verified: {p} — must come from the "
                f"AI-generation pipeline, git asset library, Pexels, or Pixabay, "
                f"never an arbitrary download."
            )

    if music_path and not os.path.exists(music_path):
        issues.append(f"Missing music: {music_path}")

    return issues


def validate_before_upload(script: dict, clip_paths: list = None, music_path: str = None) -> dict:
    """
    Full compliance gate. Returns:
      {"passed": bool, "issues": [...], "warnings": [...], "attribution": str}
    """
    issues = []
    warnings = []

    issues.extend(check_script_copyright(script))
    issues.extend(check_guidelines(script))
    issues.extend(check_asset_paths(clip_paths, music_path))

    title = script.get("title", "")
    if len(title) > 70 and "?" not in title and "!" not in title[:30]:
        warnings.append("Title may be low-click — consider adding hook punctuation early")

    try:
        import git_asset_library as gal
        attribution = gal.get_attribution_text()
    except Exception:
        attribution = ""

    passed = len(issues) == 0
    result = {"passed": passed, "issues": issues, "warnings": warnings, "attribution": attribution}

    if passed:
        log("Copyright/guidelines check: PASSED")
        for w in warnings:
            log(f"  Warning: {w}")
    else:
        log("Copyright/guidelines check: FAILED")
        for i in issues:
            log(f"  Issue: {i}")

    return result


def auto_fix_script(script: dict) -> dict:
    """Apply safe auto-fixes so script passes guidelines where possible."""
    s = dict(script)

    if not s.get("title") and s.get("video_title"):
        s["title"] = s["video_title"]

    title = s.get("title", "").strip()
    if not title:
        hook = s.get("hook", "Football Short")[:60]
        s["title"] = f"{hook} #shorts #football"

    if "#shorts" not in s.get("title", "").lower():
        s["title"] = (s.get("title", "Football Facts") + " #shorts").strip()

    if len(s.get("title", "")) > 100:
        s["title"] = s["title"][:96].rstrip() + " #shorts"

    if not s.get("cta"):
        s["cta"] = "What do you think? Drop your take in the comments and subscribe!"

    return s


def save_compliance_report(result: dict, video_id: str = None):
    report_dir = os.path.join(config.OUTPUT_DIR, "compliance")
    os.makedirs(report_dir, exist_ok=True)
    fname = f"report_{video_id or int(__import__('time').time())}.json"
    path = os.path.join(report_dir, fname)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    return path
