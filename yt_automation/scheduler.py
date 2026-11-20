"""
scheduler.py — Runs the pipeline on a weekly schedule.
Run this once and leave it running: python scheduler.py
It will automatically produce and upload a new video every week.
"""

import schedule
import time
from logger import log
from main import run_pipeline


def job():
    log("Scheduler: Triggering weekly pipeline run...")
    try:
        run_pipeline()
        log("Scheduler: Run complete. Next run in 7 days.")
    except Exception as e:
        log(f"Scheduler ERROR: {e}")
        log("Will retry next scheduled run.")


# Run every Monday at 09:00
schedule.every().monday.at("09:00").do(job)

log("Scheduler started — pipeline runs every Monday at 09:00.")
log("Press Ctrl+C to stop.")

# Also run immediately on first start
log("Running initial pipeline now...")
job()

while True:
    schedule.run_pending()
    time.sleep(60)
