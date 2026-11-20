"""
anime_video_generator.py — AnimateDiff (SD1.5 + motion adapter) anime-style
clip generator. Runs under venv_animate's Python (CUDA torch + diffusers),
invoked as a subprocess from pro_shorts_creator.py (main env).

Usage: venv_animate/Scripts/python.exe anime_video_generator.py <jobs.json>
  jobs.json: [{"prompt": "...", "out_path": "...", "seconds": 8}, ...]
Writes each clip to its out_path (looped/boomeranged to reach ~seconds long)
and prints a JSON list of {"out_path", "ok", "error"} to stdout.
"""

import json
import sys
import torch
from diffusers import AnimateDiffPipeline, MotionAdapter, DDIMScheduler
from diffusers.utils import export_to_video

BASE_MODEL = "stable-diffusion-v1-5/stable-diffusion-v1-5"
MOTION_ADAPTER = "guoyww/animatediff-motion-adapter-v1-5-3"
FPS = 8
NEGATIVE_PROMPT = "low quality, worst quality, blurry, static, still image, watermark, text"


def load_pipeline():
    adapter = MotionAdapter.from_pretrained(MOTION_ADAPTER, torch_dtype=torch.float16)
    pipe = AnimateDiffPipeline.from_pretrained(BASE_MODEL, motion_adapter=adapter, torch_dtype=torch.float16)
    pipe.scheduler = DDIMScheduler.from_pretrained(
        BASE_MODEL, subfolder="scheduler",
        clip_sample=False, timestep_spacing="linspace", beta_schedule="linear", steps_offset=1,
    )
    pipe.enable_vae_slicing()
    pipe.enable_model_cpu_offload()
    return pipe


def generate_clip(pipe, prompt: str, out_path: str, seconds: float = 8.0, seed: int = None):
    output = pipe(
        prompt=f"anime style, {prompt}, dramatic mid-action motion, fast movement, dynamic pose, motion blur, high quality, detailed",
        negative_prompt=NEGATIVE_PROMPT,
        num_frames=16,
        guidance_scale=8.5,
        num_inference_steps=30,
        generator=torch.Generator("cuda").manual_seed(seed) if seed is not None else None,
    )
    frames = output.frames[0]

    # Boomerang-loop the short (2s) clip to fill the requested duration, so
    # the existing assemble()/prepare_segment() pipeline (which just trims,
    # doesn't loop) gets a long-enough source clip. Avoids a jump-cut at the
    # loop point since it plays forward then backward.
    boomerang = frames + frames[::-1]
    cycle_seconds = len(boomerang) / FPS
    reps = max(1, round(seconds / cycle_seconds))
    looped = boomerang * reps

    export_to_video(looped, out_path, fps=FPS)
    return out_path


def main():
    jobs_path = sys.argv[1]
    with open(jobs_path, encoding="utf-8") as f:
        jobs = json.load(f)

    print(f"Loading AnimateDiff pipeline (one-time)...", file=sys.stderr)
    pipe = load_pipeline()

    results = []
    for i, job in enumerate(jobs):
        try:
            print(f"[{i+1}/{len(jobs)}] Generating: {job['prompt'][:60]}...", file=sys.stderr)
            generate_clip(pipe, job["prompt"], job["out_path"], job.get("seconds", 8.0), job.get("seed"))
            results.append({"out_path": job["out_path"], "ok": True, "error": None})
        except Exception as e:
            results.append({"out_path": job["out_path"], "ok": False, "error": str(e)})

    print(json.dumps(results))


if __name__ == "__main__":
    main()
