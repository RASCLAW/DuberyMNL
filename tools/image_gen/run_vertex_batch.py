"""
Sequential Vertex batch runner with safe pacing.

Replaces ad-hoc bash for-loops. Runs `generate_vertex.py` once per prompt file
with a 30s gap between successful calls (default) to stay under the per-minute
quota documented in feedback_vertex_quota_parallel_4_blows.

The retry-on-429 logic lives inside generate_vertex.py itself, so a transient
quota hit is self-healed (up to 3 attempts, 30/60/90s backoff). This runner
adds the steady-state cadence on top.

Usage:
    python tools/image_gen/run_vertex_batch.py <prompt_file> [<prompt_file> ...]
    python tools/image_gen/run_vertex_batch.py --interval 45 .tmp/foo_prompt.json .tmp/bar_prompt.json

Exit code: 0 if all succeeded, 1 if any failed (failed list printed at end).
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent.parent
GENERATE_SCRIPT = PROJECT_DIR / "tools" / "image_gen" / "generate_vertex.py"

DEFAULT_INTERVAL_SECONDS = 30


def run_one(prompt_file: str) -> bool:
    print(f"\n=== Generating {Path(prompt_file).name} ===", flush=True)
    try:
        result = subprocess.run(
            [sys.executable, str(GENERATE_SCRIPT), prompt_file],
            cwd=str(PROJECT_DIR),
            check=False,
        )
        return result.returncode == 0
    except Exception as e:
        print(f"ERROR launching subprocess: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Sequential Vertex batch runner with paced cadence.")
    parser.add_argument("prompt_files", nargs="+", help="Prompt JSON/TXT files to generate.")
    parser.add_argument(
        "--interval", type=int, default=DEFAULT_INTERVAL_SECONDS,
        help=f"Seconds to sleep between successful calls (default: {DEFAULT_INTERVAL_SECONDS}).",
    )
    args = parser.parse_args()

    succeeded = []
    failed = []

    for i, prompt_file in enumerate(args.prompt_files):
        if not Path(prompt_file).exists():
            print(f"SKIP {prompt_file}: file not found", file=sys.stderr)
            failed.append(prompt_file)
            continue

        ok = run_one(prompt_file)
        (succeeded if ok else failed).append(prompt_file)

        # Sleep between calls, except after the last one
        if i < len(args.prompt_files) - 1:
            print(f"--- sleeping {args.interval}s before next call ---", flush=True)
            time.sleep(args.interval)

    print(f"\n=== Batch complete: {len(succeeded)} succeeded, {len(failed)} failed ===")
    if failed:
        print("Failed:")
        for f in failed:
            print(f"  - {f}")
        sys.exit(1)


if __name__ == "__main__":
    main()
