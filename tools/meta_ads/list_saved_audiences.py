"""
List Meta Ads Saved Audiences on the current ad account.

Read-only. Prints name + ID for each saved audience so we can grab IDs to
reference in plan files or presets.

Usage:
    python tools/meta_ads/list_saved_audiences.py
    python tools/meta_ads/list_saved_audiences.py --match "metro manila"
"""

import argparse
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_DIR / ".env")

META_ADS_ACCESS_TOKEN = os.environ.get("META_ADS_ACCESS_TOKEN")
META_AD_ACCOUNT_ID = os.environ.get("META_AD_ACCOUNT_ID")

GRAPH_API_VERSION = "v21.0"
GRAPH_API_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--match", default="", help="Case-insensitive substring filter on name")
    args = parser.parse_args()

    if not META_ADS_ACCESS_TOKEN or not META_AD_ACCOUNT_ID:
        print("Error: missing META_ADS_ACCESS_TOKEN or META_AD_ACCOUNT_ID", file=sys.stderr)
        sys.exit(1)

    url = f"{GRAPH_API_BASE}/{META_AD_ACCOUNT_ID}/saved_audiences"
    params = {
        "access_token": META_ADS_ACCESS_TOKEN,
        "fields": "id,name,approximate_count_lower_bound,approximate_count_upper_bound,targeting",
        "limit": 100,
    }
    resp = requests.get(url, params=params, timeout=30)
    if resp.status_code != 200:
        print(f"Error ({resp.status_code}): {resp.text}", file=sys.stderr)
        sys.exit(2)

    data = resp.json().get("data", [])
    needle = args.match.strip().lower()
    shown = 0
    for a in data:
        name = a.get("name", "")
        if needle and needle not in name.lower():
            continue
        shown += 1
        lo = a.get("approximate_count_lower_bound")
        hi = a.get("approximate_count_upper_bound")
        size = f"{lo:,}-{hi:,}" if lo and hi else "unknown"
        print(f"[{a['id']}] {name}  (~{size})")

    if shown == 0:
        print(f"No saved audiences matching '{args.match}'." if needle else "No saved audiences found.")
    else:
        print(f"\n{shown} saved audience(s).")


if __name__ == "__main__":
    main()
