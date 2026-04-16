"""
Post the next story in rotation from the chatbot-image-bank JSON.

Uses time-based rotation (no state file needed):
  index = (hours_since_epoch / 3) % total_images

Reads from contents/assets/fb-stories-pool-2026-04.json (picks array)
on each run, so bank edits take effect on the next cron tick (no
redeploy needed).

Usage:
    python tools/facebook/story_rotation.py
    python tools/facebook/story_rotation.py --dry-run
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests

PROJECT_DIR = Path(__file__).parent.parent.parent
QUEUE_FILE = PROJECT_DIR / "contents" / "assets" / "fb-stories-pool-2026-04.json"

META_PAGE_ACCESS_TOKEN = os.environ.get("META_PAGE_ACCESS_TOKEN")
META_PAGE_ID = os.environ.get("META_PAGE_ID")
GRAPH_API_VERSION = "v25.0"
BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


def load_queue():
    """Load the story rotation queue from the chatbot-image-bank."""
    if not QUEUE_FILE.exists():
        print(f"Error: {QUEUE_FILE} not found", file=sys.stderr)
        sys.exit(1)
    data = json.loads(QUEUE_FILE.read_text(encoding="utf-8"))
    picks = data.get("picks", [])
    if not picks:
        print(f"Error: {QUEUE_FILE} has empty picks list", file=sys.stderr)
        sys.exit(1)
    return picks


def get_current_index(total):
    """Time-based rotation: changes every 3 hours."""
    hours = int(time.time() // 3600)
    return (hours // 3) % total


def post_photo_story(image_path):
    """Post a photo story (2-step: upload unpublished, then publish as story)."""
    if not META_PAGE_ACCESS_TOKEN or not META_PAGE_ID:
        print("Error: META_PAGE_ACCESS_TOKEN or META_PAGE_ID not set", file=sys.stderr)
        sys.exit(1)

    with open(image_path, "rb") as f:
        resp = requests.post(
            f"{BASE}/{META_PAGE_ID}/photos",
            data={"published": "false", "access_token": META_PAGE_ACCESS_TOKEN},
            files={"source": (Path(image_path).name, f, "image/png")},
        )

    if resp.status_code != 200:
        print(f"Error uploading: {resp.status_code} {resp.text}", file=sys.stderr)
        sys.exit(1)

    photo_id = resp.json()["id"]

    resp = requests.post(
        f"{BASE}/{META_PAGE_ID}/photo_stories",
        data={"photo_id": photo_id, "access_token": META_PAGE_ACCESS_TOKEN},
    )

    if resp.status_code != 200:
        print(f"Error publishing: {resp.status_code} {resp.text}", file=sys.stderr)
        sys.exit(1)

    return resp.json()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    rotation = load_queue()
    idx = get_current_index(len(rotation))
    entry = rotation[idx]
    image_rel = entry["path"]
    image_path = PROJECT_DIR / image_rel

    variant = entry.get("model", "?")
    kind = entry.get("type", "?")
    print(f"Rotation: {idx + 1}/{len(rotation)} -- {image_rel} ({variant} / {kind})")

    if not image_path.exists():
        print(f"Error: {image_path} not found", file=sys.stderr)
        sys.exit(1)

    if args.dry_run:
        print("[DRY RUN] Would post story -- skipping.")
        sys.exit(0)

    result = post_photo_story(image_path)
    print(f"Story posted! Post ID: {result.get('post_id', 'unknown')}")
