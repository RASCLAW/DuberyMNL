"""
Pull Meta Ads performance insights and save to .tmp/ad_insights.json.

Usage:
    python tools/meta_ads/pull_insights.py                  # Last 7 days, summary
    python tools/meta_ads/pull_insights.py --days 14        # Last 14 days
    python tools/meta_ads/pull_insights.py --daily           # Daily breakdown
    python tools/meta_ads/pull_insights.py --daily --days 3  # Last 3 days, daily
    python tools/meta_ads/pull_insights.py --campaign-id 123 # Specific campaign
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
INSIGHTS_FILE = TMP_DIR / "ad_insights.json"

ACCESS_TOKEN = os.environ.get("META_ADS_ACCESS_TOKEN")
AD_ACCOUNT_ID = os.environ.get("META_AD_ACCOUNT_ID")
GRAPH_API_VERSION = "v21.0"
BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

PHT = timezone(timedelta(hours=8))

INSIGHT_FIELDS = [
    "campaign_name", "campaign_id",
    "adset_name", "adset_id",
    "ad_name", "ad_id",
    "impressions", "clicks", "ctr", "cpc", "cpm", "spend",
    "actions", "cost_per_action_type",
]


def api_get(endpoint, params=None):
    """Make a GET request to the Meta Graph API."""
    params = params or {}
    params["access_token"] = ACCESS_TOKEN
    resp = requests.get(f"{BASE}/{endpoint}", params=params)
    if not resp.ok:
        err = resp.json().get("error", {})
        print(f"API error: {err.get('message', resp.text)}", file=sys.stderr)
        sys.exit(1)
    return resp.json()


def extract_actions(actions_list):
    """Convert actions array to a flat dict."""
    if not actions_list:
        return {}
    return {a["action_type"]: int(a["value"]) for a in actions_list}


def extract_costs(cost_list):
    """Convert cost_per_action_type array to a flat dict."""
    if not cost_list:
        return {}
    return {a["action_type"]: float(a["value"]) for a in cost_list}


def pull_insights(campaign_id, date_from, date_to, daily=False):
    """Pull insights at campaign, ad set, and ad level."""
    time_range = json.dumps({"since": date_from, "until": date_to})
    time_increment = "1" if daily else "all_days"

    results = {"meta": {}, "campaign": [], "adsets": [], "ads": []}
    results["meta"] = {
        "pulled_at": datetime.now(PHT).isoformat(),
        "date_from": date_from,
        "date_to": date_to,
        "campaign_id": campaign_id,
        "daily": daily,
    }

    # Campaign level
    data = api_get(f"{campaign_id}/insights", {
        "fields": ",".join(INSIGHT_FIELDS),
        "time_range": time_range,
        "time_increment": time_increment,
        "level": "campaign",
    })
    results["campaign"] = data.get("data", [])

    # Ad set level
    data = api_get(f"{campaign_id}/insights", {
        "fields": ",".join(INSIGHT_FIELDS),
        "time_range": time_range,
        "time_increment": time_increment,
        "level": "adset",
    })
    results["adsets"] = data.get("data", [])

    # Ad level
    data = api_get(f"{campaign_id}/insights", {
        "fields": ",".join(INSIGHT_FIELDS),
        "time_range": time_range,
        "time_increment": time_increment,
        "level": "ad",
    })
    results["ads"] = data.get("data", [])

    return results


def print_summary(results):
    """Print a formatted summary to terminal."""
    meta = results["meta"]
    print(f"\nMeta Ads Insights -- {meta['date_from']} to {meta['date_to']}")
    print(f"Pulled: {meta['pulled_at']}")
    print("=" * 95)

    # Campaign totals
    for c in results["campaign"]:
        actions = extract_actions(c.get("actions"))
        costs = extract_costs(c.get("cost_per_action_type"))
        lpv = actions.get("landing_page_view", 0)
        cost_lpv = costs.get("landing_page_view", 0)
        period = f"{c.get('date_start', '?')} to {c.get('date_stop', '?')}"

        print(f"\nCampaign: {c.get('campaign_name')} ({period})")
        print(f"  Spend: P{c.get('spend', '0')} | Impressions: {c.get('impressions', '0')} | "
              f"Clicks: {c.get('clicks', '0')} | CTR: {float(c.get('ctr', 0)):.2f}%")
        print(f"  CPC: P{float(c.get('cpc', 0)):.2f} | CPM: P{float(c.get('cpm', 0)):.2f} | "
              f"LPV: {lpv} | Cost/LPV: P{cost_lpv:.2f}")
        print(f"  Reactions: {actions.get('post_reaction', 0)} | "
              f"Saves: {actions.get('onsite_conversion.post_save', 0)} | "
              f"Link clicks: {actions.get('link_click', 0)}")

    # Ad set breakdown
    adsets = [a for a in results["adsets"] if not results["meta"]["daily"]]
    if adsets:
        print(f"\n{'Ad Set':<45s} | {'Spend':>8s} | {'Impr':>6s} | {'CTR':>6s} | {'CPC':>6s} | {'LPV':>4s} | {'Cost/LPV':>9s}")
        print("-" * 95)
        for a in adsets:
            actions = extract_actions(a.get("actions"))
            costs = extract_costs(a.get("cost_per_action_type"))
            lpv = actions.get("landing_page_view", 0)
            cost_lpv = costs.get("landing_page_view", 0)
            print(f"  {a.get('adset_name', '?'):<43s} | P{float(a.get('spend', 0)):>6.2f} | "
                  f"{a.get('impressions', '0'):>6s} | {float(a.get('ctr', 0)):>5.2f}% | "
                  f"P{float(a.get('cpc', 0)):>4.2f} | {lpv:>4d} | P{cost_lpv:>7.2f}")

    # Ad breakdown
    ads = [a for a in results["ads"] if not results["meta"]["daily"]]
    if ads:
        print(f"\n{'Ad':<35s} | {'Ad Set':<20s} | {'Spend':>8s} | {'Impr':>6s} | {'CTR':>6s} | {'LPV':>4s} | {'Cost/LPV':>9s} | {'React':>5s}")
        print("-" * 115)
        for a in sorted(ads, key=lambda x: float(x.get("ctr", 0)), reverse=True):
            actions = extract_actions(a.get("actions"))
            costs = extract_costs(a.get("cost_per_action_type"))
            lpv = actions.get("landing_page_view", 0)
            cost_lpv = costs.get("landing_page_view", 0)
            reactions = actions.get("post_reaction", 0)
            adset_short = a.get("adset_name", "?")[:20]
            print(f"  {a.get('ad_name', '?'):<33s} | {adset_short:<20s} | P{float(a.get('spend', 0)):>6.2f} | "
                  f"{a.get('impressions', '0'):>6s} | {float(a.get('ctr', 0)):>5.2f}% | "
                  f"{lpv:>4d} | P{cost_lpv:>7.2f} | {reactions:>5d}")

    # Daily breakdown
    if results["meta"]["daily"] and results["campaign"]:
        print(f"\n{'Date':<12s} | {'Spend':>8s} | {'Impr':>6s} | {'Clicks':>6s} | {'CTR':>6s} | {'CPC':>6s} | {'LPV':>4s}")
        print("-" * 70)
        for c in sorted(results["campaign"], key=lambda x: x.get("date_start", "")):
            actions = extract_actions(c.get("actions"))
            lpv = actions.get("landing_page_view", 0)
            print(f"  {c.get('date_start', '?'):<10s} | P{float(c.get('spend', 0)):>6.2f} | "
                  f"{c.get('impressions', '0'):>6s} | {c.get('clicks', '0'):>6s} | "
                  f"{float(c.get('ctr', 0)):>5.2f}% | P{float(c.get('cpc', 0)):>4.2f} | {lpv:>4d}")

    print()


def find_active_campaign():
    """Find the active traffic campaign."""
    data = api_get(f"{AD_ACCOUNT_ID}/campaigns", {
        "fields": "id,name,status,objective",
        "filtering": json.dumps([{"field": "effective_status", "operator": "IN", "value": ["ACTIVE"]}]),
    })
    for c in data.get("data", []):
        if c.get("objective") in ("OUTCOME_TRAFFIC", "OUTCOME_SALES", "OUTCOME_LEADS"):
            return c["id"]
    # Fallback: return first active
    if data.get("data"):
        return data["data"][0]["id"]
    return None


def main():
    parser = argparse.ArgumentParser(description="Pull Meta Ads insights")
    parser.add_argument("--days", type=int, default=7, help="Number of days to look back (default: 7)")
    parser.add_argument("--daily", action="store_true", help="Show daily breakdown")
    parser.add_argument("--campaign-id", type=str, help="Specific campaign ID (default: auto-detect active)")
    parser.add_argument("--no-save", action="store_true", help="Don't save to file")
    parser.add_argument("--quiet", action="store_true", help="Save only, no terminal output")
    args = parser.parse_args()

    if not ACCESS_TOKEN or not AD_ACCOUNT_ID:
        print("Error: META_ADS_ACCESS_TOKEN and META_AD_ACCOUNT_ID must be set in .env", file=sys.stderr)
        sys.exit(1)

    campaign_id = args.campaign_id
    if not campaign_id:
        campaign_id = find_active_campaign()
        if not campaign_id:
            print("Error: no active campaign found", file=sys.stderr)
            sys.exit(1)

    now = datetime.now(PHT)
    date_to = now.strftime("%Y-%m-%d")
    date_from = (now - timedelta(days=args.days)).strftime("%Y-%m-%d")

    results = pull_insights(campaign_id, date_from, date_to, daily=args.daily)

    if not args.no_save:
        TMP_DIR.mkdir(exist_ok=True)
        INSIGHTS_FILE.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
        if not args.quiet:
            print(f"Saved to {INSIGHTS_FILE}")

    if not args.quiet:
        print_summary(results)


if __name__ == "__main__":
    main()
