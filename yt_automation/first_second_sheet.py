"""
first_second_sheet.py — the first 2 seconds of one or more Shorts side by side (0.0, 0.5, 1.0, 2.0 s).

The swipe decision happens in the first second (CHANNEL_DIAGNOSIS.md, LESSONS rule 18), so this sheet is what the
owner approves before any render, and what QA checks before any upload: the 0.0 s and 0.5 s frames must look
clearly different (something is already happening), and frame 0.0 must work as the thumbnail.

  python first_second_sheet.py OUT.png VIDEO.mp4 [VIDEO2.mp4 ...]
"""
import os
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

T = [0.0, 0.5, 1.0, 2.0]
W, H = 216, 384


def sheet(out, videos):
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 15)
    img = Image.new("RGB", (190 + W * len(T), 30 + H * len(videos)), (20, 20, 20))
    d = ImageDraw.Draw(img)
    for j, t in enumerate(T):
        d.text((190 + j * W + 80, 6), f"{t:.1f}s", fill="white", font=font)
    with tempfile.TemporaryDirectory() as tmp:
        for i, v in enumerate(videos):
            y = 30 + i * H
            d.text((8, y + 170), os.path.splitext(os.path.basename(v))[0][:22], fill="white", font=font)
            for j, t in enumerate(T):
                p = os.path.join(tmp, f"{i}_{j}.png")
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", v, "-frames:v", "1",
                                "-vf", f"scale={W}:{H}", p], check=True)
                img.paste(Image.open(p), (190 + j * W, y))
    img.save(out)
    return out


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    print(sheet(sys.argv[1], sys.argv[2:]))
