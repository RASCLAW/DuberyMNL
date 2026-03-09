"""
Generate an image using kie.ai API.

Submits a job, polls until complete, and saves the result locally.

Usage:
    python generate_image.py --prompt "your prompt here" --output .tmp/image.jpg

Output: saves image to --output path, prints JSON result to stdout.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

KIE_AI_API_KEY = os.environ.get("KIE_AI_API_KEY")
KIE_AI_BASE_URL = "https://api.kie.ai"

MAX_RETRIES = 15
POLL_INTERVAL_SECONDS = 30


def submit_job(prompt: str) -> str:
    """Submit image generation job to kie.ai. Returns job_id."""
    headers = {
        "Authorization": f"Bearer {KIE_AI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "prompt": prompt,
        "aspect_ratio": "4:5",
        "output_format": "jpeg",
    }
    response = requests.post(f"{KIE_AI_BASE_URL}/v1/images/generate", headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()
    job_id = data.get("job_id") or data.get("id") or data.get("task_id")
    if not job_id:
        raise ValueError(f"No job_id in response: {data}")
    return job_id


def poll_job(job_id: str) -> dict:
    """Poll kie.ai for job result. Returns result dict with image URL."""
    headers = {"Authorization": f"Bearer {KIE_AI_API_KEY}"}
    for attempt in range(1, MAX_RETRIES + 1):
        response = requests.get(f"{KIE_AI_BASE_URL}/v1/images/{job_id}", headers=headers)
        response.raise_for_status()
        data = response.json()
        status = data.get("status", "").lower()

        if status in ("completed", "succeeded", "done", "success"):
            return data
        elif status in ("failed", "error"):
            raise RuntimeError(f"kie.ai job failed: {data.get('error', data)}")

        print(f"[{attempt}/{MAX_RETRIES}] Status: {status} — waiting {POLL_INTERVAL_SECONDS}s...", file=sys.stderr)
        time.sleep(POLL_INTERVAL_SECONDS)

    raise TimeoutError(f"kie.ai job {job_id} did not complete after {MAX_RETRIES} retries")


def download_image(image_url: str, output_path: Path):
    """Download image from URL to local path."""
    response = requests.get(image_url, stream=True)
    response.raise_for_status()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)


def extract_image_url(result: dict) -> str:
    """Extract image URL from kie.ai result (handles different response shapes)."""
    # Try common result shapes
    for key in ("output", "images", "results", "data"):
        val = result.get(key)
        if isinstance(val, list) and val:
            first = val[0]
            if isinstance(first, str):
                return first
            if isinstance(first, dict):
                return first.get("url") or first.get("image_url") or first.get("src", "")
        if isinstance(val, str):
            return val
    return result.get("url") or result.get("image_url", "")


def main():
    if not KIE_AI_API_KEY:
        print("Error: KIE_AI_API_KEY not set in .env", file=sys.stderr)
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Generate image via kie.ai")
    parser.add_argument("--prompt", required=True, help="Image generation prompt")
    parser.add_argument("--output", required=True, help="Output file path (e.g. .tmp/image.jpg)")
    args = parser.parse_args()

    output_path = Path(args.output)

    print(f"Submitting job to kie.ai...", file=sys.stderr)
    job_id = submit_job(args.prompt)
    print(f"Job ID: {job_id}", file=sys.stderr)

    result = poll_job(job_id)
    image_url = extract_image_url(result)

    if not image_url:
        print(f"Error: could not extract image URL from result: {result}", file=sys.stderr)
        sys.exit(1)

    print(f"Downloading image...", file=sys.stderr)
    download_image(image_url, output_path)

    output = {
        "success": True,
        "job_id": job_id,
        "image_url": image_url,
        "output_path": str(output_path),
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
