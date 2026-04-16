"""
Create a silent Facebook Page album and upload photos with captions.

Reads an album config (JSON) describing title, message, and ordered photos.
Uses no_story=true on the album AND every photo to avoid pushing feed stories.

Usage:
    PYTHONIOENCODING=utf-8 python tools/facebook/upload_album.py --config path/to/album.json
    PYTHONIOENCODING=utf-8 python tools/facebook/upload_album.py --config path/to/album.json --dry-run

Config schema:
    {
      "title": "Album title",
      "message": "Album description",
      "photos": [
        {"path": "contents/assets/hero/foo.png", "caption": "Foo"},
        ...
      ]
    }
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_DIR / ".env")

META_PAGE_ACCESS_TOKEN = os.environ.get("META_PAGE_ACCESS_TOKEN")
META_PAGE_ID = os.environ.get("META_PAGE_ID")
GRAPH_API_VERSION = "v25.0"
BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


def die(msg, code=1):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def create_album(title, message):
    print(f"Creating album: {title!r}")
    resp = requests.post(
        f"{BASE}/{META_PAGE_ID}/albums",
        data={
            "name": title,
            "message": message,
            "no_story": "true",
            "access_token": META_PAGE_ACCESS_TOKEN,
        },
        timeout=30,
    )
    if resp.status_code != 200:
        die(f"album create failed: {resp.status_code} {resp.text}")
    album_id = resp.json().get("id")
    if not album_id:
        die(f"album create returned no id: {resp.text}")
    print(f"  album_id={album_id}")
    return album_id


def upload_photo(album_id, image_path, caption, idx, total):
    image_path = Path(image_path)
    if not image_path.is_absolute():
        image_path = PROJECT_DIR / image_path
    if not image_path.exists():
        die(f"photo {idx}/{total} not found: {image_path}")
    print(f"  [{idx}/{total}] {image_path.name} -> {caption!r}")
    with open(image_path, "rb") as f:
        resp = requests.post(
            f"{BASE}/{album_id}/photos",
            data={
                "message": caption,
                "no_story": "true",
                "access_token": META_PAGE_ACCESS_TOKEN,
            },
            files={"source": (image_path.name, f, "image/png")},
            timeout=60,
        )
    if resp.status_code != 200:
        die(f"photo upload failed at {idx}/{total} ({image_path.name}): {resp.status_code} {resp.text}")
    photo_id = resp.json().get("id")
    if not photo_id:
        die(f"photo upload returned no id: {resp.text}")
    return photo_id


def get_album_url(album_id):
    resp = requests.get(
        f"{BASE}/{album_id}",
        params={"fields": "link,name,count", "access_token": META_PAGE_ACCESS_TOKEN},
        timeout=30,
    )
    if resp.status_code != 200:
        die(f"album fetch failed: {resp.status_code} {resp.text}")
    data = resp.json()
    return data.get("link"), data.get("count"), data.get("name")


def verify_url(url):
    """Open the album URL and confirm it returns 200."""
    try:
        r = requests.head(url, allow_redirects=True, timeout=15)
        return r.status_code == 200
    except Exception as e:
        print(f"  verify warning: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Create silent FB Page album + upload photos.")
    parser.add_argument("--config", required=True, help="Path to album JSON config")
    parser.add_argument("--dry-run", action="store_true", help="Validate config + env, no API calls")
    parser.add_argument("--sleep", type=float, default=1.0, help="Seconds between photo uploads (default 1.0)")
    args = parser.parse_args()

    if not META_PAGE_ACCESS_TOKEN or not META_PAGE_ID:
        die("META_PAGE_ACCESS_TOKEN or META_PAGE_ID missing in .env")

    config_path = Path(args.config)
    if not config_path.exists():
        die(f"config not found: {config_path}")
    cfg = json.loads(config_path.read_text(encoding="utf-8"))

    title = cfg["title"]
    message = cfg["message"]
    photos = cfg["photos"]
    if not photos:
        die("config has no photos")

    print(f"Album: {title}")
    print(f"Photos: {len(photos)}")
    print(f"Page ID: {META_PAGE_ID}")
    print(f"Graph API: {GRAPH_API_VERSION}")

    if args.dry_run:
        for i, p in enumerate(photos, 1):
            path = Path(p["path"])
            if not path.is_absolute():
                path = PROJECT_DIR / path
            ok = path.exists()
            print(f"  [{i}/{len(photos)}] {'OK' if ok else 'MISSING'}: {path}")
        print("[DRY RUN] no API calls made.")
        return

    album_id = create_album(title, message)

    print("Uploading photos...")
    for i, p in enumerate(photos, 1):
        upload_photo(album_id, p["path"], p["caption"], i, len(photos))
        if i < len(photos):
            time.sleep(args.sleep)

    link, count, name = get_album_url(album_id)
    print(f"Album: {name!r}, count={count}, link={link}")

    if not link:
        die("album has no public link yet — check Page settings")

    print("Verifying URL...")
    if not verify_url(link):
        print(f"WARNING: HEAD on {link} did not return 200 — open manually to confirm.", file=sys.stderr)

    print()
    print("ALBUM_URL:", link)


if __name__ == "__main__":
    main()
