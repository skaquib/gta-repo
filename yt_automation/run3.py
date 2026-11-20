"""run3.py — Create 3 drafts in a row for review in dashboard.py."""
from pro_shorts_creator import create_draft
from logger import log

log("=" * 60)
log("  Creating 3 Draft Videos For Review")
log("=" * 60)

for i in range(1, 4):
    log(f"\n>>> DRAFT {i}/3 <<<")
    create_draft()

log("=" * 60)
log("  All 3 drafts ready -- run `python dashboard.py` to review them.")
log("=" * 60)
