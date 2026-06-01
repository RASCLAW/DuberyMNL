"""
Sequential Veo batch runner -- animate a list of stills via generate_videos.py.

Reads a JSON jobs file: a list of objects, each:
  { "name": "...", "image": "<start frame png>", "prompt": "<motion prompt>",
    "negative_prompt": "<optional>", "output": "<mp4 path>" }

Calls generate_videos.py once per job with shared flags (model/aspect/duration/
audio). Continues past failures (logs them) so one bad clip never kills the batch.
Veo runs are inherently slow + sequential, which also keeps us well under quota.

Usage:
    python tools/image_gen/run_veo_batch.py .tmp/veo_jobs.json
    python tools/image_gen/run_veo_batch.py .tmp/veo_jobs.json --model lite --duration 4 --no-audio
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent.parent
GEN = PROJECT_DIR / "tools" / "image_gen" / "generate_videos.py"


def run_one(job, model, aspect, duration, no_audio):
    cmd = [
        sys.executable, str(GEN),
        "--prompt", job["prompt"],
        "--image", job["image"],
        "--model", model,
        "--aspect-ratio", aspect,
        "--output", job["output"],
    ]
    if duration:
        cmd += ["--duration", str(duration)]
    if no_audio:
        cmd += ["--no-audio"]
    if job.get("negative_prompt"):
        cmd += ["--negative-prompt", job["negative_prompt"]]
    print(f"\n=== {job['name']} -> {job['output']} ===", flush=True)
    try:
        r = subprocess.run(cmd, cwd=str(PROJECT_DIR), check=False)
        return r.returncode == 0
    except Exception as e:
        print(f"ERROR launching subprocess: {e}", file=sys.stderr)
        return False


def main():
    ap = argparse.ArgumentParser(description="Sequential Veo batch animator.")
    ap.add_argument("jobs_file")
    ap.add_argument("--model", default="lite", choices=["fast", "full", "lite"])
    ap.add_argument("--aspect-ratio", default="9:16")
    ap.add_argument("--duration", type=int, default=4)
    ap.add_argument("--no-audio", action="store_true")
    args = ap.parse_args()

    jobs = json.loads(Path(args.jobs_file).read_text(encoding="utf-8"))
    ok, fail = [], []
    for i, job in enumerate(jobs):
        if not (PROJECT_DIR / job["image"]).exists():
            print(f"SKIP {job['name']}: image not found {job['image']}", file=sys.stderr)
            fail.append(job["name"])
            continue
        success = run_one(job, args.model, args.aspect_ratio, args.duration, args.no_audio)
        (ok if success else fail).append(job["name"])
        print(f"--- {len(ok)} ok, {len(fail)} fail, {len(jobs) - i - 1} left ---", flush=True)

    print(f"\n=== VEO BATCH DONE: {len(ok)} ok, {len(fail)} failed ===")
    if fail:
        print("Failed: " + ", ".join(fail))
        sys.exit(1)


if __name__ == "__main__":
    main()
