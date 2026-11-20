"""
viral_shorts_engine.py
======================
Main orchestrator for copyright-safe viral YouTube Shorts.

Pipeline:
  1. Sync YouTube analytics → double down on winning subjects/hooks
  2. AI script generation (viral hooks, guideline-safe)
  3. Free git/Pixabay assets (music, SFX, stock clips) — NO broadcast footage
  4. Human-like editing (variable cuts, beat drops, SFX, natural voice)
  5. Copyright + Community Guidelines check before upload
  6. Upload with attribution in description

Run:
  python viral_shorts_engine.py          # one video
  python viral_shorts_engine.py --loop   # 10/day auto loop
  python viral_shorts_engine.py --check  # compliance dry-run only
  python viral_shorts_engine.py --stats  # sync analytics only
"""

import os
import sys
import time
import random
import argparse
import numpy as np

import config
from logger import log

# Force safest defaults for this engine
os.environ.setdefault("USE_GIT_ASSETS", "true")
os.environ.setdefault("USE_REAL_FOOTAGE", "false")
os.environ.setdefault("VISUAL_STYLE", "footage")

import git_asset_library as gal
import copyright_compliance as compliance
import viral_analytics as analytics

import visual_shorts_creator as vsc

try:
    from moviepy import AudioFileClip, concatenate_audioclips, CompositeAudioClip
    MOVIEPY_V2 = True
except ImportError:
    from moviepy.editor import AudioFileClip, concatenate_audioclips, CompositeAudioClip
    MOVIEPY_V2 = False


def _human_segment_durations(total: float, n: int = 3) -> list:
    """Variable cut lengths — feels hand-edited, not robotic equal splits."""
    base = total / n
    jitter = [random.uniform(-0.8, 0.8) for _ in range(n)]
    durs = [max(2.5, base + j) for j in jitter]
    scale = total / sum(durs)
    return [d * scale for d in durs]


def download_git_clips(script: dict) -> list:
    """Priority: git manifest clips → Pixabay fallback. Never yt-dlp."""
    paths = gal.pick_video_clips(script, count=3)
    if len(paths) >= 2:
        log(f"Git assets: using {len(paths)} royalty-free clips")
        return paths

    log("Git assets: falling back to Pixabay search...")
    queries = gal.get_pixabay_fallback_queries(script)
    script_copy = dict(script)
    script_copy["queries"] = queries

    clip_dir = os.path.join(config.OUTPUT_DIR, "raw_clips")
    paths, used_ids = [], set()
    for q in queries:
        try:
            path, vid_id = vsc.fetch_clip(q, clip_dir, exclude_ids=used_ids)
            paths.append(path)
            used_ids.add(vid_id)
        except Exception as e:
            log(f"  Pixabay fallback failed for '{q}': {e}")

    if not paths:
        raise Exception("Could not fetch any royalty-free video clips")
    return paths


def get_git_music(duration: float = 30.0) -> str:
    """Git/CC0 music first, then synthesized, then Mixkit."""
    try:
        path, asset = gal.pick_music(tags=["sport", "football", "energy"])
        log(f"Git music: {asset['id']} ({asset.get('license', '')})")
        return path
    except Exception as e:
        log(f"Git music failed ({e}) — trying synthesizer")

    return vsc.get_music(duration=duration)


def mix_sfx_on_hook(music_path: str, hook_duration: float = 3.0) -> str:
    """Layer impact/crowd SFX at hook start for human editor feel."""
    try:
        sfx_list = gal.pick_sfx(tags=["hook", "impact"], count=1)
        if not sfx_list:
            return music_path

        sfx_path, sfx_meta = sfx_list[0]
        log(f"Human edit: SFX '{sfx_meta['id']}' on hook")

        music = AudioFileClip(music_path)
        sfx = AudioFileClip(sfx_path)
        sfx = sfx.with_duration(min(sfx.duration, 1.2)) if hasattr(sfx, "with_duration") else sfx.set_duration(min(sfx.duration, 1.2))
        if hasattr(sfx, "with_volume_scaled"):
            sfx = sfx.with_volume_scaled(0.45)
        elif hasattr(sfx, "volumex"):
            sfx = sfx.volumex(0.45)

        if MOVIEPY_V2:
            sfx = sfx.with_start(0)
        else:
            sfx = sfx.set_start(0)

        mixed = CompositeAudioClip([music, sfx])
        out = os.path.join(config.AUDIO_DIR, f"mixed_{int(time.time())}.mp3")
        os.makedirs(config.AUDIO_DIR, exist_ok=True)
        mixed.write_audiofile(out, logger=None)
        mixed.close()
        music.close()
        sfx.close()
        return out
    except Exception as e:
        log(f"SFX mix skipped ({e})")
        return music_path


def prepare_script() -> dict:
    """Generate script with analytics-informed subject priority."""
    vsc.SUBJECTS[:] = analytics.get_priority_subjects(vsc.SUBJECTS)

    hints = analytics.get_viral_script_hints()
    if hints:
        log(f"Viral strategy hints: {hints}")

    state = vsc.load_state()
    script = vsc.pick_script(state)
    vsc.save_state(state)

    script = compliance.auto_fix_script(script)

    if hints and "aura_hook" in hints:
        if "aura" not in script.get("title", "").lower():
            script["title"] = script["title"].replace("#football", "#football #aura")

    return script


def assemble_human(script: dict, clip_paths: list, vo_path: str, music_path: str, theme: dict, out_path: str):
    """Wrap visual_shorts_creator.assemble with human-like timing."""
    music_path = mix_sfx_on_hook(music_path, hook_duration=3.0)
    vsc.assemble(clip_paths, script, vo_path, music_path, theme, out_path, is_image_clips=False)


def run_one_viral_short(dry_run: bool = False) -> dict:
    config.assert_safe_pipeline()
    log("=" * 60)
    log("  VIRAL SHORTS ENGINE — GIT ASSETS + COMPLIANCE + ANALYTICS")
    log("=" * 60)

    recs = analytics.sync_and_analyze()
    for r in recs.get("recommendations", []):
        log(f"  Strategy: {r}")

    state = vsc.load_state()
    script = prepare_script()
    theme = vsc.COLOR_THEMES[(state.get("theme_idx", -1) + 1) % len(vsc.COLOR_THEMES)]
    state["theme_idx"] = (state.get("theme_idx", -1) + 1) % len(vsc.COLOR_THEMES)
    state["video_count"] = state.get("video_count", 0) + 1
    vsc.save_state(state)

    log(f"Hook: {script['hook'][:70]}")

    clip_paths = download_git_clips(script)
    log(f"Clips ready: {len(clip_paths)}")

    cta = script.get("cta", "")
    if "framed facts" not in cta.lower() and config.CHANNEL_NAME.lower() in ("framedfacts", "framed facts"):
        script["cta"] = cta.rstrip(".! ") + " — subscribe for more Framed Facts!"

    try:
        vo_path = vsc.generate_voiceover(script)
    except Exception as e:
        log(f"Voice failed ({e}) — instrumental mode")
        vo_path = None

    vo_duration = 21.0
    if vo_path:
        try:
            vo_clip = AudioFileClip(vo_path)
            vo_duration = min(vo_clip.duration + 1.5, 58.0)
            vo_clip.close()
        except Exception:
            pass

    music_path = get_git_music(duration=vo_duration)

    check = compliance.validate_before_upload(script, clip_paths, music_path)
    if check["attribution"]:
        script["seo_description"] = (
            script.get("seo_description", script.get("body", ""))
            + check["attribution"]
        )

    if not check["passed"]:
        compliance.save_compliance_report(check)
        if not dry_run:
            script = compliance.auto_fix_script(script)
            check = compliance.validate_before_upload(script, clip_paths, music_path)
            if not check["passed"]:
                raise Exception(f"Compliance failed: {check['issues']}")

    if dry_run:
        log("DRY RUN — compliance passed, skipping render/upload")
        return {"script": script, "compliance": check, "clips": clip_paths}

    out_path = os.path.join(config.VIDEOS_DIR, f"viral_{int(time.time())}.mp4")
    assemble_human(script, clip_paths, vo_path, music_path, theme, out_path)

    final_check = compliance.validate_before_upload(script, clip_paths, music_path)
    compliance.save_compliance_report(final_check, video_id=os.path.basename(out_path))

    if not final_check["passed"]:
        log(f"Post-render compliance warning: {final_check['issues']}")

    url = vsc.upload(out_path, script)

    log("=" * 60)
    log(f"  VIRAL SHORT #{state['video_count']} COMPLETE")
    log(f"  {script['title'][:65]}")
    if url:
        log(f"  YouTube: {url}")
    else:
        log(f"  Local: {out_path}")
    log("=" * 60)

    return {"url": url, "path": out_path, "script": script}


def main():
    parser = argparse.ArgumentParser(description="Viral Shorts Engine")
    parser.add_argument("--loop", action="store_true", help="Run every 144 min (10/day)")
    parser.add_argument("--check", action="store_true", help="Dry-run compliance only")
    parser.add_argument("--stats", action="store_true", help="Sync analytics only")
    args = parser.parse_args()

    if args.stats:
        result = analytics.sync_and_analyze()
        log(f"Tracked {result.get('state', {}).get('total_videos_tracked', 0)} videos")
        for r in result.get("recommendations", []):
            log(f"  → {r}")
        winners = result.get("winners", [])
        if winners:
            log(f"  {len(winners)} viral winner(s) over {analytics.VIRAL_VIEW_THRESHOLD:,} views")
        return

    run_one_viral_short(dry_run=args.check)

    if args.loop:
        interval = 144 * 60
        while True:
            log(f"Next viral Short in {interval // 60} minutes...")
            time.sleep(interval)
            run_one_viral_short()


if __name__ == "__main__":
    main()
