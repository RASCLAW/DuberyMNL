"""
Stage a PAUSED click-to-Messenger (Messages) campaign for DuberyMNL.

Creates a fresh OUTCOME_ENGAGEMENT campaign whose ad set sends clicks straight
into Messenger (destination MESSENGER, optimized for CONVERSATIONS) so the live
chatbot closes the sale in-chat. Audience MIRRORS the proven "DuberyMNL Traffic"
converter (Metro Manila, 24-45, sunglasses/COD/outdoor/engaged-shopper stack) so
this is a clean channel A/B vs Traffic. Creative = the Father's Day images in
FD_ADS (uploaded from contents/), copy adapted "shop now" -> "message us".

Everything is created PAUSED -- nothing spends until RA unpauses in Ads Manager.

Usage:
    # fresh campaign + adset + ads (PAUSED)
    python tools/meta_ads/stage_messages_ad.py --dry-run
    python tools/meta_ads/stage_messages_ad.py

    # only (re)build the ad layer on an existing adset; --clear removes its ads first
    python tools/meta_ads/stage_messages_ad.py --adset-id 52528754163880 --clear

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
OUT_IDS = PROJECT_DIR / ".tmp" / "messages_fd_ids.json"

# ---- Campaign spec ----------------------------------------------------------

CAMPAIGN_NAME = "DuberyMNL - Messages - Father's Day Test"
ADSET_NAME = "Messages FD - MM Proven Aud"
DAILY_BUDGET_PESOS = 100

# Primary text: live FD copy, CTA flipped from "shop now" -> "message us".
FD_TEXT = (
    "One for Dad, one for you. This Father's Day, give him the pair that actually "
    "protects his eyes — Dubery polarized cuts the glare so every drive and every "
    "adventure looks sharper.\n\n"
    "2-pair bundle ₱998 with FREE nationwide delivery. Cash on delivery, nationwide.\n\n"
    "Message us to claim yours — we'll help you pick the colors in chat."
)

# Father's Day creatives (RA-picked), uploaded from local files.
FD_ADS = [
    {"name": "Messages FD - Father+Son v6",
     "file": "contents/new/2026-06-16_fathers_day_bespoke_v6_1.png"},
    {"name": "Messages FD - BD Blue Stencil Porch",
     "file": "contents/new/2026-06-17_BESPOKE-FDV3-07-BD-BLUE-STENCIL-FRONT-PORCH.png"},
    {"name": "Messages FD - Bespoke v2_8",
     "file": "contents/new/2026-06-16_fathers_day_bespoke_v2_8.png"},
    {"name": "Messages FD - Bespoke v2_7",
     "file": "contents/new/2026-06-16_fathers_day_bespoke_v2_7.png"},
]

# Mirror of the proven "DuberyMNL Traffic" converter audience (adset 6981526931476).
TARGETING = {
    "geo_locations": {
        "regions": [{"key": "4179"}],  # Metro Manila
        "location_types": ["frequently_in", "home", "recent"],
    },
    "age_min": 24,
    "age_max": 45,
    "flexible_spec": [
        {
            "interests": [
                {"id": "411914522311422"},  # Cash on delivery
                {"id": "6002979499920"},    # Fishing
                {"id": "6002984573619"},    # Surfing
                {"id": "6002985584323"},    # Outdoor recreation
                {"id": "6003255640088"},    # Sunglasses
                {"id": "6003348604581"},    # Fashion accessories
                {"id": "6003348662930"},    # Camping
                {"id": "6003397496347"},    # Running
                {"id": "6003431201869"},    # Beaches
                {"id": "6003437568354"},    # Mountaineering
                {"id": "6003466585319"},    # Online banking
                {"id": "6003469834063"},    # Driving
            ],
            "behaviors": [{"id": "6002714895372"}],  # Frequent Travelers
        },
        {"behaviors": [{"id": "6071631541183"}]},     # Engaged Shoppers
    ],
    "targeting_automation": {"advantage_audience": 0},
}


def api_post(endpoint, payload):
    payload["access_token"] = TOKEN
    r = requests.post(f"{BASE}/{endpoint}", json=payload, timeout=60)
    if not r.ok:
        raise RuntimeError(f"POST {endpoint} -> {r.status_code}: {r.text}")
    return r.json()


def api_delete(obj_id):
    r = requests.delete(f"{BASE}/{obj_id}", params={"access_token": TOKEN}, timeout=60)
    if not r.ok:
        raise RuntimeError(f"DELETE {obj_id} -> {r.status_code}: {r.text}")
    return r.json()


def list_adset_ads(adset_id):
    r = requests.get(f"{BASE}/{adset_id}/ads",
                     params={"access_token": TOKEN, "fields": "id,name"}, timeout=60)
    r.raise_for_status()
    return r.json().get("data", [])


def upload_image(path):
    p = PROJECT_DIR / path
    if not p.exists():
        raise FileNotFoundError(p)
    mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
    with open(p, "rb") as f:
        r = requests.post(f"{BASE}/{ACCOUNT}/adimages",
                          params={"access_token": TOKEN},
                          files={"filename": (p.name, f, mime)}, timeout=180)
    if not r.ok:
        raise RuntimeError(f"image upload {path} -> {r.status_code}: {r.text}")
    for _, meta in r.json().get("images", {}).items():
        return meta["hash"]
    raise ValueError(f"unexpected upload response: {r.text}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--adset-id", help="(re)build ads on this existing adset; skip campaign/adset create")
    ap.add_argument("--clear", action="store_true", help="delete existing ads in --adset-id first")
    args = ap.parse_args()

    for name, val in [("META_ADS_ACCESS_TOKEN", TOKEN), ("META_AD_ACCOUNT_ID", ACCOUNT),
                      ("META_PAGE_ID", PAGE_ID)]:
        if not val:
            sys.exit(f"Error: {name} not set in .env")

    page_link = f"https://www.facebook.com/{PAGE_ID}"
    mode = f"ads-only -> adset {args.adset_id}" if args.adset_id else "new campaign"

    print(f"\n{'DRY RUN -- ' if args.dry_run else ''}Messages FD campaign (PAUSED)  [{mode}]")
    print("=" * 62)
    if not args.adset_id:
        print(f"  Campaign  : {CAMPAIGN_NAME}  (OUTCOME_ENGAGEMENT)")
        print(f"  Ad set    : {ADSET_NAME}")
        print(f"  Budget    : ₱{DAILY_BUDGET_PESOS}/day")
        print(f"  Optimize  : CONVERSATIONS  ->  destination MESSENGER")
        print(f"  Audience  : MM, 24-45, proven interest stack (mirrors Traffic)")
    print(f"  Page link : {page_link}")
    print(f"  Clear old : {bool(args.clear)}")
    print(f"  Ads       : {len(FD_ADS)}")
    for i, a in enumerate(FD_ADS, 1):
        ok = "ok" if (PROJECT_DIR / a["file"]).exists() else "MISSING"
        print(f"    {i}. {a['name']:34} [{ok}] {Path(a['file']).name}")
    print(f"\n  Primary text:\n    " + FD_TEXT.replace("\n", "\n    "))

    if args.dry_run:
        print("\nDry run only -- no API calls made.")
        return

    created = {"ads": []}
    try:
        if args.adset_id:
            adset_id = args.adset_id
            if args.clear:
                for ad in list_adset_ads(adset_id):
                    api_delete(ad["id"])
                    print(f"  deleted  : {ad['id']}  {ad.get('name','')}")
        else:
            camp = api_post(f"{ACCOUNT}/campaigns", {
                "name": CAMPAIGN_NAME, "objective": "OUTCOME_ENGAGEMENT",
                "status": "PAUSED", "special_ad_categories": [],
                "is_adset_budget_sharing_enabled": False,
            })
            created["campaign_id"] = camp["id"]
            print(f"\n  campaign : {camp['id']}")
            adset = api_post(f"{ACCOUNT}/adsets", {
                "name": ADSET_NAME, "campaign_id": camp["id"],
                "billing_event": "IMPRESSIONS",
                "optimization_goal": "CONVERSATIONS",
                "destination_type": "MESSENGER",
                "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
                "daily_budget": DAILY_BUDGET_PESOS * 100,
                "targeting": TARGETING,
                "status": "PAUSED",
            })
            adset_id = adset["id"]
            created["adset_id"] = adset_id
            print(f"  ad set   : {adset_id}")

        for a in FD_ADS:
            h = upload_image(a["file"])
            creative = api_post(f"{ACCOUNT}/adcreatives", {
                "name": a["name"] + " creative",
                "object_story_spec": {
                    "page_id": PAGE_ID,
                    "link_data": {
                        "link": page_link,
                        "message": FD_TEXT,
                        "image_hash": h,
                        "call_to_action": {
                            "type": "MESSAGE_PAGE",
                            "value": {"app_destination": "MESSENGER"},
                        },
                    },
                },
            })
            ad = api_post(f"{ACCOUNT}/ads", {
                "name": a["name"], "adset_id": adset_id,
                "creative": {"creative_id": creative["id"]}, "status": "PAUSED",
            })
            created["ads"].append({"name": a["name"], "ad_id": ad["id"],
                                   "creative_id": creative["id"], "image_hash": h})
            print(f"  ad       : {ad['id']}  {a['name']}")

    except Exception as e:
        print(f"\nFAILED: {e}", file=sys.stderr)
        if created.get("campaign_id") or created.get("ads"):
            OUT_IDS.write_text(json.dumps(created, indent=2))
            print(f"Partial objects created (for cleanup): {OUT_IDS}", file=sys.stderr)
        sys.exit(1)

    OUT_IDS.write_text(json.dumps(created, indent=2))
    acct = ACCOUNT.replace("act_", "")
    print(f"\n  ALL PAUSED. IDs -> {OUT_IDS}")
    print(f"  Review/activate: https://www.facebook.com/adsmanager/manage/campaigns?act={acct}")


if __name__ == "__main__":
    main()
