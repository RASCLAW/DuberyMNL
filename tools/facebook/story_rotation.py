"""
Post the next story in rotation from the story queue.

Uses time-based rotation (no state file needed):
  index = (hours_since_epoch / 4) % total_images

Usage:
    python tools/facebook/story_rotation.py
    python tools/facebook/story_rotation.py --dry-run
"""

import argparse
import os
import sys
import time
from pathlib import Path

import requests

PROJECT_DIR = Path(__file__).parent.parent.parent

META_PAGE_ACCESS_TOKEN = os.environ.get("META_PAGE_ACCESS_TOKEN")
META_PAGE_ID = os.environ.get("META_PAGE_ID")
GRAPH_API_VERSION = "v25.0"
BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

# 12 images, rotating every 4 hours = 48 hour full cycle, then repeats
STORY_IMAGES = [
    "contents/ready/model-shots/MODEL-BANDITS-TORTOISE_output.png",
    "contents/ready/ugc/image_e64c2a80.png",
    "contents/ready/brand-bold/BOLD-002_output.png",
    "contents/ready/model-shots/MODEL-BANDITS-MATTE-BLACK_output.png",
    "contents/ready/ugc/image_e636a1f6.png",
    "contents/ready/model-shots/MODEL-BANDITS-GLOSSY-BLACK_output.png",
    "contents/ready/ugc/image_c0741e0d.png",
    "contents/ready/brand-bold/BOLD-004_output.png",
    "contents/ready/model-shots/MODEL-OUTBACK-RED_output.png",
    "contents/ready/ugc/vertex_ugc_fidelity.png",
    "contents/ready/model-shots/MODEL-RASTA-BROWN_output.png",
    "contents/ready/ugc/ugc_UGC-20260407-006.png",
]


def get_current_index():
    """Time-based rotation: changes every 4 hours."""
    hours = int(time.time() // 3600)
    return (hours // 4) % len(STORY_IMAGES)


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

    idx = get_current_index()
    image_rel = STORY_IMAGES[idx]
    image_path = PROJECT_DIR / image_rel

    print(f"Rotation: {idx + 1}/{len(STORY_IMAGES)} -- {image_rel}")

    if not image_path.exists():
        print(f"Error: {image_path} not found", file=sys.stderr)
        sys.exit(1)

    if args.dry_run:
        print("[DRY RUN] Would post story -- skipping.")
        sys.exit(0)

    result = post_photo_story(image_path)
    print(f"Story posted! Post ID: {result.get('post_id', 'unknown')}")
