"""
shorts_scheduler.py
====================
Single consolidated scheduler for the football-Shorts pipelines, replacing
the scattered `while True: time.sleep(...)` loops previously duplicated in
goal_analysis_creator.py, match_analysis_creator.py, pro_shorts_creator.py,
and viral_shorts_engine.py --loop. Each pipeline's own main()/run_one_job()
still works standalone for manual/one-off runs -- this is the recommended
way to run continuous, scheduled output across all of them at once.

Cadence is biased by config.TARGET_REGION's rough audience-active hours
(publish when the target audience is actually awake, not on a blind fixed
timer) and, once match_calendar_data.json has fixtures, toward real match/
news moments (see match_calendar.py) rather than firing regardless of
what's actually happening in the sport that day.

Run: python shorts_scheduler.py
"""

import time
import random
import datetime

import config
from logger import log

# Rough local-audience-active-hours UTC offset per region.
_REGION_UTC_OFFSET = {"IN": 5.5, "US": -5.0, "BR": -3.0, "GB": 0.0}


def _jobs():
    """name -> (callable, base_cadence_minutes). Imported lazily so this
    module can be imported (e.g. by tests) without pulling in every
    pipeline's heavy dependencies (moviepy, TTS, etc.) at import time."""
    import goal_analysis_creator as gac
    import match_analysis_creator as mac
    import pro_shorts_creator as psc
    import visual_shorts_creator as vsc
    import viral_shorts_engine as vse

    return {
        "goal_analysis":  (gac.run_one_analysis, 360),
        "match_analysis": (mac.run_one, 360),
        "pro_shorts_draft": (psc.create_draft, config.LOOP_INTERVAL_MINUTES),
        "visual_shorts":  (vsc.run_one_job, 144),
        "viral_shorts":   (vse.run_one_viral_short, 144),
    }


def _is_audience_active(now_utc: datetime.datetime = None) -> bool:
    """True during a rough 08:00-23:00 local-audience-time window for
    config.TARGET_REGION, so scheduled jobs cluster when viewers are likely
    awake rather than firing on a blind timer regardless of time of day."""
    now_utc = now_utc or datetime.datetime.now(datetime.timezone.utc)
    offset = _REGION_UTC_OFFSET.get(config.TARGET_REGION, 0.0)
    local_hour = (now_utc + datetime.timedelta(hours=offset)).hour
    return 8 <= local_hour <= 23


def _next_run_delay(base_minutes: float) -> float:
    """Jitter the base cadence +/-15% so jobs don't all fire in lockstep,
    and pull the next run in closer to a real match's post-full-time window
    when match_calendar.py has an upcoming fixture within range."""
    delay = base_minutes + base_minutes * random.uniform(-0.15, 0.15)

    try:
        import match_calendar
        upcoming = match_calendar.next_match_window(hours_ahead=delay / 60.0 + 3.0)
        if upcoming:
            kickoff = match_calendar.parse_kickoff(upcoming[0])
            if kickoff:
                now = datetime.datetime.now(datetime.timezone.utc)
                post_match_minutes = (kickoff - now).total_seconds() / 60.0 + 130.0  # ~2h after kickoff
                if 0 < post_match_minutes < delay:
                    return post_match_minutes
    except Exception as e:
        log(f"Scheduler: match calendar unavailable ({e})")

    return max(5.0, delay)


def run():
    log("=" * 60)
    log("  SHORTS SCHEDULER — consolidated cadence for all pipelines")
    log(f"  Region: {config.TARGET_REGION}")
    log("=" * 60)

    jobs = _jobs()
    now = time.time()
    next_run_at = {name: now for name in jobs}  # run each once immediately

    while True:
        now = time.time()
        for name, (fn, cadence_minutes) in jobs.items():
            if now < next_run_at[name]:
                continue
            if not _is_audience_active():
                log(f"Scheduler: skipping '{name}' — outside audience-active hours for {config.TARGET_REGION}")
                next_run_at[name] = now + 30 * 60
                continue

            log(f"Scheduler: running '{name}'...")
            try:
                fn()
            except Exception as e:
                log(f"Scheduler: '{name}' failed: {e}")

            delay_minutes = _next_run_delay(cadence_minutes)
            next_run_at[name] = time.time() + delay_minutes * 60
            log(f"Scheduler: next '{name}' run in {delay_minutes:.0f} minutes")

        time.sleep(60)


if __name__ == "__main__":
    run()
