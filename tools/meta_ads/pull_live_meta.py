"""
Pull live ad/adset metadata from Meta Marketing API.

Complements pull_insights.py: pull_insights gives performance numbers,
this gives the structural metadata (status, daily budget, creative thumbs)
that insights doesn't carry. Together they populate the CC Marketing tab.

Writes .tmp/marketing_live_meta.json with shape:
{
  "meta": {"pulled_at", "campaign_id"},
  "adsets": [{adset_id, name, status, effective_status, daily_budget_php, lifetime_budget_php}],
  "ads": [{ad_id, adset_id, name, status, effective_status, creative_id, thumbnail_url}]
}

Budgets returned by Meta in account currency minor unit (centavos for PHP).
We divide by 100 here so the JSON is human-readable pesos.

Usage:
    python tools/meta_ads/pull_live_meta.py                  # auto-detect active campaign
    python tools/meta_ads/pull_live_meta.py --campaign-id X  # specific campaign
    python tools/meta_ads/pull_live_meta.py --output FILE    # custom output path
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_DIR / ".env")

TMP_DIR = PROJECT_DIR / ".tmp"
DEFAULT_OUT = TMP_DIR / "marketing_live_meta.json"

ACCESS_TOKEN = os.environ.get("META_ADS_ACCESS_TOKEN")
AD_ACCOUNT_ID = os.environ.get("META_AD_ACCOUNT_ID")
GRAPH_API_VERSION = "v21.0"
BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

PHT = timezone(timedelta(hours=8))


def api_get(endpoint, params=None):
    params = params or {}
    params["access_token"] = ACCESS_TOKEN
    resp = requests.get(f"{BASE}/{endpoint}", params=params, timeout=15)
    if not resp.ok:
        err = resp.json().get("error", {}) if resp.text else {}
        print(f"API error on {endpoint}: {err.get('message', resp.text[:300])}", file=sys.stderr)
        sys.exit(1)
    return resp.json()


def find_active_campaign():
    data = api_get(f"{AD_ACCOUNT_ID}/campaigns", {
        "fields": "id,name,status,objective",
        "filtering": json.dumps([
            {"field": "effective_status", "operator": "IN", "value": ["ACTIVE"]}
        ]),
    })
    for c in data.get("data", []):
        if c.get("objective") in ("OUTCOME_TRAFFIC", "OUTCOME_SALES", "OUTCOME_LEADS"):
            return c["id"]
    if data.get("data"):
        return data["data"][0]["id"]
    return None


def pull_adsets(campaign_id):
    data = api_get(f"{campaign_id}/adsets", {
        "fields": "id,name,status,effective_status,daily_budget,lifetime_budget",
        "limit": 100,
    })
    out = []
    for a in data.get("data", []):
        daily_raw = a.get("daily_budget")
        lifetime_raw = a.get("lifetime_budget")
        out.append({
            "adset_id": a.get("id"),
            "name": a.get("name", ""),
            "status": a.get("status", ""),
            "effective_status": a.get("effective_status", ""),
            "daily_budget_php": (int(daily_raw) / 100.0) if daily_raw else None,
            "lifetime_budget_php": (int(lifetime_raw) / 100.0) if lifetime_raw else None,
        })
    return out


def pull_ads(campaign_id):
    data = api_get(f"{campaign_id}/ads", {
        "fields": "id,name,status,effective_status,adset_id,creative{id,thumbnail_url,image_url}",
        "limit": 200,
    })
    out = []
    for a in data.get("data", []):
        creative = a.get("creative") or {}
        out.append({
            "ad_id": a.get("id"),
            "adset_id": a.get("adset_id", ""),
            "name": a.get("name", ""),
            "status": a.get("status", ""),
            "effective_status": a.get("effective_status", ""),
            "creative_id": creative.get("id"),
            "thumbnail_url": creative.get("thumbnail_url") or creative.get("image_url"),
        })
    return out


def main():
    parser = argparse.ArgumentParser(description="Pull live ad/adset metadata from Meta")
    parser.add_argument("--campaign-id", type=str, help="Campaign ID (default: auto-detect active)")
    parser.add_argument("--output", type=str, help="Output path (default: .tmp/marketing_live_meta.json)")
    parser.add_argument("--quiet", action="store_true", help="Suppress non-error output")
    args = parser.parse_args()

    if not ACCESS_TOKEN or not AD_ACCOUNT_ID:
        print("Error: META_ADS_ACCESS_TOKEN and META_AD_ACCOUNT_ID must be set in .env",
              file=sys.stderr)
        sys.exit(1)

    campaign_id = args.campaign_id or find_active_campaign()
    if not campaign_id:
        print("Error: no active campaign found", file=sys.stderr)
        sys.exit(1)

    adsets = pull_adsets(campaign_id)
    ads = pull_ads(campaign_id)

    result = {
        "meta": {
            "pulled_at": datetime.now(PHT).isoformat(),
            "campaign_id": campaign_id,
        },
        "adsets": adsets,
        "ads": ads,
    }

    out_path = Path(args.output) if args.output else DEFAULT_OUT
    out_path.parent.mkdir(exist_ok=True, parents=True)
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    if not args.quiet:
        print(f"Saved {len(adsets)} adsets and {len(ads)} ads to {out_path}")


if __name__ == "__main__":
    main()
