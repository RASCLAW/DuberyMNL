"""
List ALL campaigns on the ad account with status + ads (read-only).

Complements pull_live_meta.py (single-campaign) with an account-wide view:
every campaign, its effective_status/objective/budget, and optionally each ad's
status. Read-only -- never mutates. Used to decide what to un-pause/pause.

Usage:
    python tools/meta_ads/list_campaigns.py            # all campaigns, summary
    python tools/meta_ads/list_campaigns.py --ads      # include each campaign's ads
    python tools/meta_ads/list_campaigns.py --active   # only ACTIVE effective_status
    python tools/meta_ads/list_campaigns.py --json      # raw JSON dump
"""

import argparse
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

# Windows consoles default to cp1252; campaign names carry curly quotes/emoji.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PROJECT_DIR = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_DIR / ".env")

ACCESS_TOKEN = os.environ.get("META_ADS_ACCESS_TOKEN")
AD_ACCOUNT_ID = os.environ.get("META_AD_ACCOUNT_ID")
BASE = "https://graph.facebook.com/v21.0"


def api_get(endpoint, params=None):
    params = params or {}
    params["access_token"] = ACCESS_TOKEN
    resp = requests.get(f"{BASE}/{endpoint}", params=params, timeout=20)
    if not resp.ok:
        err = resp.json().get("error", {}) if resp.text else {}
        print(f"API error on {endpoint}: {err.get('message', resp.text[:300])}", file=sys.stderr)
        sys.exit(1)
    return resp.json()


def peso(raw):
    return f"P{int(raw)/100:.0f}" if raw else "-"


def main():
    p = argparse.ArgumentParser(description="List all campaigns (read-only)")
    p.add_argument("--ads", action="store_true", help="Include each campaign's ads")
    p.add_argument("--active", action="store_true", help="Only ACTIVE effective_status")
    p.add_argument("--json", action="store_true", help="Raw JSON dump")
    args = p.parse_args()

    if not ACCESS_TOKEN or not AD_ACCOUNT_ID:
        print("Error: META_ADS_ACCESS_TOKEN and META_AD_ACCOUNT_ID must be set in .env", file=sys.stderr)
        sys.exit(1)

    filtering = None
    if args.active:
        filtering = json.dumps([{"field": "effective_status", "operator": "IN", "value": ["ACTIVE"]}])

    params = {
        "fields": "id,name,status,effective_status,objective,daily_budget,lifetime_budget,updated_time",
        "limit": 200,
    }
    if filtering:
        params["filtering"] = filtering

    camps = api_get(f"{AD_ACCOUNT_ID}/campaigns", params).get("data", [])

    result = []
    for c in camps:
        entry = {
            "campaign_id": c.get("id"),
            "name": c.get("name", ""),
            "status": c.get("status", ""),
            "effective_status": c.get("effective_status", ""),
            "objective": c.get("objective", ""),
            "daily_budget_php": (int(c["daily_budget"]) / 100.0) if c.get("daily_budget") else None,
            "updated_time": c.get("updated_time", ""),
        }
        if args.ads:
            ads = api_get(f"{c['id']}/ads", {
                "fields": "id,name,status,effective_status,adset{id,name,status,effective_status,daily_budget}",
                "limit": 200,
            }).get("data", [])
            entry["ads"] = [{
                "ad_id": a.get("id"),
                "name": a.get("name", ""),
                "status": a.get("status", ""),
                "effective_status": a.get("effective_status", ""),
                "adset_id": (a.get("adset") or {}).get("id", ""),
                "adset_name": (a.get("adset") or {}).get("name", ""),
                "adset_status": (a.get("adset") or {}).get("status", ""),
            } for a in ads]
        result.append(entry)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    for c in result:
        budget = f" {peso(c['daily_budget_php']*100) if c['daily_budget_php'] else '-'}/day" if c["daily_budget_php"] else ""
        print(f"[{c['effective_status']:<12}] {c['name']}  ({c['objective']}){budget}")
        print(f"             id={c['campaign_id']}  status={c['status']}  updated={c['updated_time'][:10]}")
        if args.ads:
            for a in c.get("ads", []):
                print(f"    - [{a['effective_status']:<10}] {a['name']}  ad={a['ad_id']}  adset={a['adset_name']} ({a['adset_status']})")
        print()


if __name__ == "__main__":
    main()
