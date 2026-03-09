"""
Upload an image to the Meta Ads creative library.

Usage:
    python upload_creative.py --file .tmp/image.jpg --ad-account-id act_XXXXXXXXX

Output: JSON with image_hash (required for creating ads).
"""

import argparse
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

META_ADS_ACCESS_TOKEN = os.environ.get("META_ADS_ACCESS_TOKEN")
GRAPH_API_VERSION = "v21.0"
GRAPH_API_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


def upload_image(file_path: Path, ad_account_id: str) -> dict:
    url = f"{GRAPH_API_BASE}/{ad_account_id}/adimages"
    with open(file_path, "rb") as f:
        response = requests.post(
            url,
            params={"access_token": META_ADS_ACCESS_TOKEN},
            files={"filename": (file_path.name, f, "image/jpeg")},
        )
    response.raise_for_status()
    data = response.json()

    # Response shape: {"images": {"filename.jpg": {"hash": "...", ...}}}
    images = data.get("images", {})
    for name, meta in images.items():
        return {
            "success": True,
            "image_hash": meta["hash"],
            "image_url": meta.get("url", ""),
            "file_name": name,
        }

    raise ValueError(f"Unexpected response shape: {data}")


def main():
    if not META_ADS_ACCESS_TOKEN:
        print("Error: META_ADS_ACCESS_TOKEN not set in .env", file=sys.stderr)
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Upload image to Meta Ads creative library")
    parser.add_argument("--file", required=True, help="Local image file path")
    parser.add_argument("--ad-account-id", required=True, help="Meta Ad Account ID (e.g. act_XXXXXXXXX)")
    args = parser.parse_args()

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: file not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    result = upload_image(file_path, args.ad_account_id)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
