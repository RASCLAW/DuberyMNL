"""
Stage a PAUSED Meta catalog *Collection* ad for a product series.

A Collection ad = a cover image + a swipeable product strip pulled from a
catalog product set + an auto-generated Instant Experience storefront (opens on
"Shop now"). Unlike a carousel, the strip is NOT hand-uploaded -- it shows each
product's catalog image (here: the clean -open-opt shots) live from the set.

Everything is created PAUSED.

Usage:
    python tools/meta_ads/stage_collection_ad.py --dry-run
    python tools/meta_ads/stage_collection_ad.py

Reads .env: META_ADS_ACCESS_TOKEN, META_AD_ACCOUNT_ID, META_PAGE_ID
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

TOKEN = os.environ.get("META_ADS_ACCESS_TOKEN")
ACCOUNT = os.environ.get("META_AD_ACCOUNT_ID")
PAGE_ID = os.environ.get("META_PAGE_ID")
GRAPH = "v21.0"
BASE = f"https://graph.facebook.com/{GRAPH}"
SITE = "https://www.duberymnl.com"
OUT_IDS = PROJECT_DIR / ".tmp" / "outback_collection_ids.json"

# ---- Collection spec (clone for other series) -------------------------------

CAMPAIGN_NAME = "DuberyMNL - Outback Collection"
ADSET_NAME = "Outback Collection - LuzVis - LAL Chatters"
DAILY_BUDGET_PESOS = 100
LOOKALIKE_ID = "6287648023676"                  # Lookalike (PH 1%) - Chatters (PH-wide)
IG_ACTOR_ID = "17841440993912065"               # page-backed IG account (Collection ads require an IG identity)
PRODUCT_SET_ID = "3434113226812319"             # Outback Polarized (5 SKUs, open shots)
COVER = "contents/new/2026-05-31_outback-blue-hero-3pair.png"
NAME = "The Outback Series"

# PH minus 6 Mindanao regions + Cagayan Valley (4182) -> Luzon + Visayas
EXCLUDED_REGIONS = ["4193", "4192", "2825", "4190", "4191", "2932", "4182"]
UTM = "utm_source=facebook&utm_medium=paid&utm_campaign=outback-collection&utm_content={{ad.id}}"

PRIMARY_TEXT = (
    "Looks expensive. It's not. ₱499 a pair.\n"
    "The Outback series — polarized lenses that block glare, 99.9% UV, sharper "
    "contrast. One tough matte frame, 5 colors.\n"
    "Free shipping on 2+. Cash on delivery, nationwide. Shop the series →"
)


def api_post(endpoint, payload):
    payload["access_token"] = TOKEN
    r = requests.post(f"{BASE}/{endpoint}", json=payload, timeout=60)
    if not r.ok:
        raise RuntimeError(f"POST {endpoint} -> {r.status_code}: {r.text}")
    return r.json()


def upload_cover(path):
    p = PROJECT_DIR / path
    if not p.exists():
        raise FileNotFoundError(p)
    mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
    with open(p, "rb") as f:
        r = requests.post(f"{BASE}/{ACCOUNT}/adimages", params={"access_token": TOKEN},
                          files={"filename": (p.name, f, mime)}, timeout=120)
    if not r.ok:
        raise RuntimeError(f"cover upload -> {r.status_code}: {r.text}")
    return list(r.json()["images"].values())[0]["hash"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    for name, val in [("META_ADS_ACCESS_TOKEN", TOKEN), ("META_AD_ACCOUNT_ID", ACCOUNT),
                      ("META_PAGE_ID", PAGE_ID)]:
        if not val:
            sys.exit(f"Error: {name} not set in .env")

    link = f"{SITE}/products/?series=outback&{UTM}"
    cover_ok = (PROJECT_DIR / COVER).exists()

    print(f"\n{'DRY RUN -- ' if args.dry_run else ''}Outback Collection ad (PAUSED)")
    print("=" * 56)
    print(f"  Campaign    : {CAMPAIGN_NAME}  (Traffic)")
    print(f"  Ad set      : {ADSET_NAME}  | P{DAILY_BUDGET_PESOS}/day")
    print(f"  Geo         : PH minus Mindanao + Cagayan Valley (Luzon + Visayas)")
    print(f"  Audience    : Lookalike {LOOKALIKE_ID} (Chatters, PH-wide), age 24-45")
    print(f"  Cover       : {COVER}  [{'ok' if cover_ok else 'MISSING'}]")
    print(f"  Strip set   : {PRODUCT_SET_ID} (Outback Polarized, 5 SKUs -> open shots)")
    print(f"  Link        : {link.split('&utm')[0]}")

    if args.dry_run:
        print("\nDry run only -- no API calls made.")
        return

    created = {}
    try:
        # 1. Cover + Collection creative (link_data cover + product_set_id)
        cover_hash = upload_cover(COVER)
        created["cover_hash"] = cover_hash
        print(f"\n  cover    : {cover_hash[:14]}...")
        creative = api_post(f"{ACCOUNT}/adcreatives", {
            "name": "Outback Collection creative",
            "object_story_spec": {
                "page_id": PAGE_ID,
                "link_data": {
                    "image_hash": cover_hash, "link": link, "message": PRIMARY_TEXT,
                    "name": NAME, "call_to_action": {"type": "SHOP_NOW"},
                },
            },
            "product_set_id": PRODUCT_SET_ID,
        })
        created["creative_id"] = creative["id"]
        print(f"  creative : {creative['id']}")

        # 2. Campaign
        camp = api_post(f"{ACCOUNT}/campaigns", {
            "name": CAMPAIGN_NAME, "objective": "OUTCOME_TRAFFIC", "status": "PAUSED",
            "special_ad_categories": [], "is_adset_budget_sharing_enabled": False,
        })
        created["campaign_id"] = camp["id"]
        print(f"  campaign : {camp['id']}")

        # 3. Ad set
        adset = api_post(f"{ACCOUNT}/adsets", {
            "name": ADSET_NAME, "campaign_id": camp["id"],
            "billing_event": "IMPRESSIONS", "optimization_goal": "LANDING_PAGE_VIEWS",
            "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
            "daily_budget": DAILY_BUDGET_PESOS * 100,
            "targeting": {
                "geo_locations": {"countries": ["PH"]},
                "excluded_geo_locations": {"regions": [{"key": k} for k in EXCLUDED_REGIONS]},
                "age_min": 24, "age_max": 45,
                "custom_audiences": [{"id": LOOKALIKE_ID}],
                "targeting_automation": {"advantage_audience": 0},
                # FB-only: Collection ads need an IG identity for IG placements;
                # no IG business account is linked yet, so restrict to Facebook.
                "publisher_platforms": ["facebook"],
            },
            "status": "PAUSED",
        })
        created["adset_id"] = adset["id"]
        print(f"  ad set   : {adset['id']}")

        # 4. Ad
        ad = api_post(f"{ACCOUNT}/ads", {
            "name": "Outback Collection", "adset_id": adset["id"],
            "creative": {"creative_id": creative["id"]}, "status": "PAUSED",
        })
        created["ad_id"] = ad["id"]
        print(f"  ad       : {ad['id']}")

    except Exception as e:
        print(f"\nFAILED: {e}", file=sys.stderr)
        if created:
            OUT_IDS.write_text(json.dumps(created, indent=2))
            print(f"Partial objects (for cleanup): {created}", file=sys.stderr)
        sys.exit(1)

    OUT_IDS.write_text(json.dumps(created, indent=2))
    acct = ACCOUNT.replace("act_", "")
    print(f"\n  ALL PAUSED. IDs -> {OUT_IDS}")
    print(f"  Review: https://www.facebook.com/adsmanager/manage/campaigns?act={acct}")


if __name__ == "__main__":
    main()
