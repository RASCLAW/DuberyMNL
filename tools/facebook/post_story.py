"""
Post a photo story to the DuberyMNL Facebook Page.

Usage:
    python tools/facebook/post_story.py --image path/to/image.png
    python tools/facebook/post_story.py --image path/to/image.png --dry-run
"""

import argparse
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_DIR / ".env")

META_PAGE_ACCESS_TOKEN = os.environ.get("META_PAGE_ACCESS_TOKEN")
META_PAGE_ID = os.environ.get("META_PAGE_ID")
GRAPH_API_VERSION = "v25.0"
BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


def post_photo_story(image_path, dry_run=False):
    """Post a photo story to the Facebook Page (2-step process)."""
    image_path = Path(image_path)
    if not image_path.exists():
        print(f"Error: Image not found: {image_path}", file=sys.stderr)
        sys.exit(1)

    if not META_PAGE_ACCESS_TOKEN or not META_PAGE_ID:
        print("Error: META_PAGE_ACCESS_TOKEN or META_PAGE_ID not set in .env", file=sys.stderr)
        sys.exit(1)

    print(f"Image: {image_path}")
    print(f"Size: {image_path.stat().st_size / 1024:.0f} KB")

    if dry_run:
        print("[DRY RUN] Would post story -- skipping API calls.")
        return

    # Step 1: Upload image as unpublished photo
    print("Step 1: Uploading image as unpublished photo...")
    with open(image_path, "rb") as f:
        resp = requests.post(
            f"{BASE}/{META_PAGE_ID}/photos",
            data={
                "published": "false",
                "access_token": META_PAGE_ACCESS_TOKEN,
            },
            files={"source": (image_path.name, f, "image/png")},
        )

    if resp.status_code != 200:
        print(f"Error uploading photo: {resp.status_code} {resp.text}", file=sys.stderr)
        sys.exit(1)

    photo_id = resp.json().get("id")
    print(f"  Photo ID: {photo_id}")

    # Step 2: Publish as story
    print("Step 2: Publishing as story...")
    resp = requests.post(
        f"{BASE}/{META_PAGE_ID}/photo_stories",
        data={
            "photo_id": photo_id,
            "access_token": META_PAGE_ACCESS_TOKEN,
        },
    )

    if resp.status_code != 200:
        print(f"Error publishing story: {resp.status_code} {resp.text}", file=sys.stderr)
        sys.exit(1)

    result = resp.json()
    post_id = result.get("post_id", "unknown")
    print(f"  Story published! Post ID: {post_id}")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Post a photo story to DuberyMNL Facebook Page")
    parser.add_argument("--image", required=True, help="Path to image file")
    parser.add_argument("--dry-run", action="store_true", help="Validate without posting")
    args = parser.parse_args()

    post_photo_story(args.image, dry_run=args.dry_run)
