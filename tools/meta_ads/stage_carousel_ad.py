"""
Stage a PAUSED Meta carousel ad for a DuberyMNL product series.

Builds one carousel creative (lineup hero card + per-colorway cards), each card
linking to its own PDP, in a fresh dedicated campaign. Everything is created
PAUSED -- nothing spends until RA unpauses in Ads Manager.

Reusable: clone the SERIES/CARDS block to make a Bandits or Rasta carousel.

Usage:
    python tools/meta_ads/stage_carousel_ad.py --dry-run    # validate, no API writes
    python tools/meta_ads/stage_carousel_ad.py              # create everything PAUSED

Reads from .env: META_ADS_ACCESS_TOKEN, META_AD_ACCOUNT_ID, META_PAGE_ID
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
OUT_IDS = PROJECT_DIR / ".tmp" / "outback_carousel_ids.json"

# ---- Carousel spec (clone this block for other series) ----------------------

CAMPAIGN_NAME = "DuberyMNL - Outback Carousel"
ADSET_NAME = "Outback Carousel - LuzVis - LAL Chatters"
DAILY_BUDGET_PESOS = 100
LOOKALIKE_ID = "6287648023676"          # Lookalike (PH 1%) - Chatters (PH-wide)
UTM = "utm_source=facebook&utm_medium=paid&utm_campaign=outback-carousel&utm_content={{ad.id}}"

# PH country, minus the 6 Mindanao regions + Cagayan Valley (Region II, far N. Luzon)
# -> Luzon (excl. Cagayan Valley) + Visayas
EXCLUDED_REGIONS = ["4193", "4192", "2825", "4190", "4191", "2932", "4182"]

PRIMARY_TEXT = (
    "Looks expensive. It's not. ₱499 a pair.\n"
    "The Outback series — polarized lenses that block glare, 99.9% UV, sharper "
    "contrast. One tough matte frame, 5 colors.\n"
    "Free shipping on 2+. Cash on delivery, nationwide. Swipe to find your pair →"
)

CAT = "dubery-landing-v3/assets/catalog"
CARDS = [
    {"img": "contents/favorites/2026-05-28_outback-arc-03-lineup-fav.png",
     "name": "The Outback Series", "desc": "5 colors · ₱499 each",
     "link": f"{SITE}/products/?series=outback"},
    {"img": f"{CAT}/outback-red-open-opt.jpg",
     "name": "Outback Red", "desc": "Ruby-mirror polarized · ₱499",
     "link": f"{SITE}/products/item.html?slug=outback-red"},
    {"img": f"{CAT}/outback-black-open-opt.jpg",
     "name": "Outback Black", "desc": "Smoked polarized · ₱499",
     "link": f"{SITE}/products/item.html?slug=outback-black"},
    {"img": f"{CAT}/outback-blue-open-opt.jpg",
     "name": "Outback Blue", "desc": "Sapphire-mirror polarized · ₱499",
     "link": f"{SITE}/products/item.html?slug=outback-blue"},
    {"img": f"{CAT}/outback-green-open-opt.jpg",
     "name": "Outback Green", "desc": "Emerald-mirror polarized · ₱499",
     "link": f"{SITE}/products/item.html?slug=outback-green"},
    {"img": f"{CAT}/outback-stripe-open-opt.jpg",
     "name": "Outback Stripe", "desc": "Limited print · ₱499",
     "link": f"{SITE}/products/item.html?slug=outback-stripe"},
]


def tagged(url):
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}{UTM}"


def api_post(endpoint, payload):
    payload["access_token"] = TOKEN
    r = requests.post(f"{BASE}/{endpoint}", json=payload, timeout=60)
    if not r.ok:
        raise RuntimeError(f"POST {endpoint} -> {r.status_code}: {r.text}")
    return r.json()


def upload_image(path):
    p = PROJECT_DIR / path
    if not p.exists():
        raise FileNotFoundError(p)
    with open(p, "rb") as f:
        r = requests.post(f"{BASE}/{ACCOUNT}/adimages",
                          params={"access_token": TOKEN},
                          files={"filename": (p.name, f, "image/jpeg")}, timeout=120)
    if not r.ok:
        raise RuntimeError(f"image upload {path} -> {r.status_code}: {r.text}")
    for _, meta in r.json().get("images", {}).items():
        return meta["hash"]
    raise ValueError(f"unexpected upload response: {r.text}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    for name, val in [("META_ADS_ACCESS_TOKEN", TOKEN), ("META_AD_ACCOUNT_ID", ACCOUNT),
                      ("META_PAGE_ID", PAGE_ID)]:
        if not val:
            sys.exit(f"Error: {name} not set in .env")

    print(f"\n{'DRY RUN -- ' if args.dry_run else ''}Outback Carousel (PAUSED)")
    print("=" * 56)
    print(f"  Campaign : {CAMPAIGN_NAME}  (Traffic)")
    print(f"  Ad set   : {ADSET_NAME}")
    print(f"  Budget   : P{DAILY_BUDGET_PESOS}/day")
    print(f"  Geo      : PH minus Mindanao + Cagayan Valley (Luzon + Visayas)")
    print(f"  Audience : Lookalike {LOOKALIKE_ID} (Chatters, PH-wide)")
    print(f"  Cards    : {len(CARDS)}")
    for i, c in enumerate(CARDS, 1):
        ok = "ok" if (PROJECT_DIR / c["img"]).exists() else "MISSING"
        print(f"    {i}. {c['name']:18} [{ok}] -> {c['link'].split('duberymnl.com')[-1]}")

    if args.dry_run:
        print("\nDry run only -- no API calls made.")
        return

    created = {}
    try:
        # 1. Campaign
        camp = api_post(f"{ACCOUNT}/campaigns", {
            "name": CAMPAIGN_NAME, "objective": "OUTCOME_TRAFFIC",
            "status": "PAUSED", "special_ad_categories": [],
            "is_adset_budget_sharing_enabled": False,
        })
        created["campaign_id"] = camp["id"]
        print(f"\n  campaign : {camp['id']}")

        # 2. Ad set
        adset = api_post(f"{ACCOUNT}/adsets", {
            "name": ADSET_NAME, "campaign_id": camp["id"],
            "billing_event": "IMPRESSIONS", "optimization_goal": "LANDING_PAGE_VIEWS",
            "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
            "daily_budget": DAILY_BUDGET_PESOS * 100,
            "targeting": {
                "geo_locations": {"countries": ["PH"]},
                "excluded_geo_locations": {
                    "regions": [{"key": k} for k in EXCLUDED_REGIONS]},
                "age_min": 24, "age_max": 45,
                "custom_audiences": [{"id": LOOKALIKE_ID}],
                "targeting_automation": {"advantage_audience": 0},
            },
            "status": "PAUSED",
        })
        created["adset_id"] = adset["id"]
        print(f"  ad set   : {adset['id']}")

        # 3. Upload images
        child = []
        for i, c in enumerate(CARDS, 1):
            h = upload_image(c["img"])
            child.append({
                "link": tagged(c["link"]), "image_hash": h,
                "name": c["name"], "description": c["desc"],
                "call_to_action": {"type": "SHOP_NOW"},
            })
            print(f"  image {i}  : {h[:12]}...  {c['name']}")

        # 4. Carousel creative (order locked, no auto end card)
        creative = api_post(f"{ACCOUNT}/adcreatives", {
            "name": "Outback Carousel creative",
            "object_story_spec": {
                "page_id": PAGE_ID,
                "link_data": {
                    "message": PRIMARY_TEXT,
                    "link": tagged(f"{SITE}/products/?series=outback"),
                    "child_attachments": child,
                    "multi_share_optimized": False,
                    "multi_share_end_card": False,
                    "call_to_action": {"type": "SHOP_NOW"},
                },
            },
        })
        created["creative_id"] = creative["id"]
        print(f"  creative : {creative['id']}")

        # 5. Ad
        ad = api_post(f"{ACCOUNT}/ads", {
            "name": "Outback Carousel", "adset_id": adset["id"],
            "creative": {"creative_id": creative["id"]}, "status": "PAUSED",
        })
        created["ad_id"] = ad["id"]
        print(f"  ad       : {ad['id']}")

    except Exception as e:
        print(f"\nFAILED: {e}", file=sys.stderr)
        if created:
            OUT_IDS.write_text(json.dumps(created, indent=2))
            print(f"Partial objects created (for cleanup): {created}", file=sys.stderr)
        sys.exit(1)

    OUT_IDS.write_text(json.dumps(created, indent=2))
    acct = ACCOUNT.replace("act_", "")
    print(f"\n  ALL PAUSED. IDs -> {OUT_IDS}")
    print(f"  Review: https://www.facebook.com/adsmanager/manage/campaigns?act={acct}")


if __name__ == "__main__":
    main()
