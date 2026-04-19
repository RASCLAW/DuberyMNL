"""
Create a Meta Ads Custom Audience of Page Engagers (likes/shares/reactions/etc).

Creates an ENGAGEMENT-type custom audience targeting everyone who engaged with
the DuberyMNL Facebook Page within the retention window. New audiences take
30-60 min to populate before ads can use them.

Usage:
    # Dry-run: print the payload, don't call the API
    python tools/meta_ads/create_custom_audience.py --dry-run

    # Default: 365-day retention, name "Page Engagers 365d"
    python tools/meta_ads/create_custom_audience.py

    # Custom name + retention
    python tools/meta_ads/create_custom_audience.py --name "Page Engagers 180d" --retention-days 180

Output: prints audience ID + name on success. ID gets saved to
command-center/presets/marketing.json under audiences.
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
META_PAGE_ID = os.environ.get("META_PAGE_ID")

GRAPH_API_VERSION = "v21.0"
GRAPH_API_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

PRESETS_FILE = PROJECT_DIR / "command-center" / "presets" / "marketing.json"


def build_rule(page_id: str, retention_seconds: int) -> dict:
    """Everyone who engaged with the Page (page_engaged covers likes, shares,
    reactions, saves, clicks, messages, post engagement)."""
    return {
        "inclusions": {
            "operator": "or",
            "rules": [
                {
                    "event_sources": [{"id": page_id, "type": "page"}],
                    "retention_seconds": retention_seconds,
                    "filter": {
                        "operator": "and",
                        "filters": [
                            {"field": "event", "operator": "eq", "value": "page_engaged"}
                        ],
                    },
                }
            ],
        }
    }


def create_audience(name: str, retention_days: int, dry_run: bool) -> dict:
    retention_seconds = retention_days * 86400
    rule = build_rule(META_PAGE_ID, retention_seconds)

    payload = {
        "name": name,
        "subtype": "ENGAGEMENT",
        "rule": json.dumps(rule),
        "description": f"Everyone who engaged with DuberyMNL page in last {retention_days} days (auto-created)",
    }

    if dry_run:
        print("DRY-RUN payload:")
        print(json.dumps({**payload, "rule": rule}, indent=2))
        return {"dry_run": True}

    url = f"{GRAPH_API_BASE}/{META_AD_ACCOUNT_ID}/customaudiences"
    resp = requests.post(
        url,
        data={**payload, "access_token": META_ADS_ACCESS_TOKEN},
        timeout=30,
    )
    if resp.status_code != 200:
        print(f"Error ({resp.status_code}): {resp.text}", file=sys.stderr)
        sys.exit(2)
    return resp.json()


def save_preset(audience_id: str, name: str, retention_days: int) -> None:
    PRESETS_FILE.parent.mkdir(parents=True, exist_ok=True)
    presets = {}
    if PRESETS_FILE.exists():
        presets = json.loads(PRESETS_FILE.read_text())

    audiences = presets.setdefault("audiences", {})
    key = f"page_engagers_{retention_days}d"
    audiences[key] = {"id": audience_id, "name": name, "retention_days": retention_days}
    PRESETS_FILE.write_text(json.dumps(presets, indent=2))
    print(f"Saved preset -> {PRESETS_FILE.relative_to(PROJECT_DIR)} [{key}]")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default="Page Engagers 365d")
    parser.add_argument("--retention-days", type=int, default=365)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    missing = [k for k, v in {
        "META_ADS_ACCESS_TOKEN": META_ADS_ACCESS_TOKEN,
        "META_AD_ACCOUNT_ID": META_AD_ACCOUNT_ID,
        "META_PAGE_ID": META_PAGE_ID,
    }.items() if not v]
    if missing:
        print(f"Error: missing env vars: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    result = create_audience(args.name, args.retention_days, args.dry_run)
    if args.dry_run:
        return

    audience_id = result.get("id")
    print(f"Created custom audience: {args.name} (id={audience_id})")
    print("Populating now. Wait 30-60 min before using in an adset.")
    save_preset(audience_id, args.name, args.retention_days)


if __name__ == "__main__":
    main()
