"""Top up specific buckets of a saved documentary clip pool, then write a
contact sheet of ONLY the newly added clips so they can be checked by eye
before any render.

Why this exists: generic stock queries ("team celebration", "fans",
"stadium") return whatever sport dominates the library -- doc #5 got football
players, an American-football stadium and Turkish club flags inside a cricket
story, plus male batsmen on the women's-final beats. The Gemini gate checks
"does this match the query", so a sport-less query lets the wrong sport in.
Fix the query, not just the clip.

Usage: python topup_pool.py <pool.json> <contact_sheet.jpg> bucket:target:q1|q2|q3 ...
"""
import json
import os
import sys

from PIL import Image, ImageDraw
from moviepy import VideoFileClip

import config
import longform_creator as lf
import visual_shorts_creator as vsc


def main():
    pool_file, sheet_path = sys.argv[1], sys.argv[2]
    pool = json.load(open(pool_file))
    clip_dir = os.path.join(config.OUTPUT_DIR, "raw_clips")
    used = set(int(x) for x in vsc._load_used_clip_ids().get("pexels", []))
    added = []
    for spec in sys.argv[3:]:
        bucket, target, qs = spec.split(":", 2)
        target = int(target)
        queries = qs.split("|")
        pool.setdefault(bucket, [])
        attempts, qi = 0, 0
        while len(pool[bucket]) < target and attempts < target * 4:
            q = queries[qi % len(queries)]
            qi += 1
            attempts += 1
            try:
                path, cid = vsc.fetch_pexels_clip(q, clip_dir, exclude_ids=used)
                vsc._record_used_clip_ids("pexels", {cid})
                used.add(cid)
                if not lf._clip_readable(path):
                    print(f"  [{bucket}] {os.path.basename(path)} unreadable/dark -- discarded")
                    continue
                pool[bucket].append(path)
                added.append((bucket, q, path))
                print(f"  [{bucket}] {q} -> {os.path.basename(path)}")
            except Exception as e:
                print(f"  [{bucket}] '{q}' failed: {e}")
    json.dump(pool, open(pool_file, "w"), indent=1)
    print("pool now:", {k: len(v) for k, v in pool.items()})

    W, H = 320, 180
    cells = []
    for bucket, q, p in added:
        c = VideoFileClip(p, audio=False)
        im = Image.fromarray(c.get_frame(c.duration * 0.5)).resize((W, H))
        c.close()
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, W, 22], fill=(0, 0, 0))
        d.text((4, 4), f"{bucket}:{os.path.basename(p)[7:-4]}", fill=(255, 255, 0))
        cells.append(im)
    if cells:
        cols = min(4, len(cells))
        rows = (len(cells) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * W, rows * H), (40, 40, 40))
        for i, im in enumerate(cells):
            sheet.paste(im, ((i % cols) * W, (i // cols) * H))
        sheet.save(sheet_path, quality=85)
        print(f"{len(cells)} new clips -> {sheet_path}")


if __name__ == "__main__":
    main()
