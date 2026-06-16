"""
Stage a PAUSED Meta carousel ad for the DuberyMNL Father's Day 2-pair offer.

6-card storyboard arc -- HOOK, PROOF, DUO, PERKS, GIFT, CTA. All cards link to
/products/?series=outback so the visitor lands on the full Outback range and can
mix-and-match for the 2-pair offer.

Everything is created PAUSED -- nothing spends until RA unpauses in Ads Manager.

Usage:
    python tools/meta_ads/stage_fd_carousel.py --dry-run  # validate, no API writes
    python tools/meta_ads/stage_fd_carousel.py            # create everything PAUSED

Reads from .env: META_ADS_ACCESS_TOKEN, META_AD_ACCOUNT_ID, META_PAGE_ID
"""
import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

import requests
from dotenv import load_dotenv
from PIL import Image

PROJECT_DIR = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_DIR / ".env")

TOKEN = os.environ.get("META_ADS_ACCESS_TOKEN")
ACCOUNT = os.environ.get("META_AD_ACCOUNT_ID")
PAGE_ID = os.environ.get("META_PAGE_ID")
GRAPH = "v21.0"
BASE = f"https://graph.facebook.com/{GRAPH}"
SITE = "https://www.duberymnl.com"
OUT_IDS = PROJECT_DIR / ".tmp" / "fd_carousel_ids.json"
JPG_TMP_DIR = PROJECT_DIR / ".tmp" / "fd-carousel-jpg"

# ---- Carousel spec ---------------------------------------------------------

CAMPAIGN_NAME = "DuberyMNL - Father's Day 2-Pair Carousel"
ADSET_NAME = "FD 2-Pair - LuzVis - LAL Chatters"
DAILY_BUDGET_PESOS = 100
LOOKALIKE_ID = "6287648023676"  # Lookalike (PH 1%) - Chatters
UTM = "utm_source=facebook&utm_medium=paid&utm_campaign=fathers-day-2-pair&utm_content={{ad.id}}"

# PH country, minus the 6 Mindanao regions + Cagayan Valley (Region II, far N. Luzon)
EXCLUDED_REGIONS = ["4193", "4192", "2825", "4190", "4191", "2932", "4182"]

PRIMARY_TEXT = (
    "Father's Day is 6 days away.\n"
    "Get 2 Outback pairs for P998 -- one for you, one for tatay.\n"
    "Free delivery, no COD fee, delivered to your door.\n"
    "Polarized lenses that block the glare. 4 colorways: black, blue, green, red.\n"
    "Mix and match. Swipe to find your pair ->"
)

LANDING = f"{SITE}/products/?series=outback"

NEW = "contents/new"
CARDS = [
    {"img": f"{NEW}/2026-06-15_BESPOKE-OUTBACK-BLACK-FD-V4-01-HOOK.png",
     "name": "Father's Day 06.21",
     "desc": "6 days left. Get 2, give 1."},
    {"img": f"{NEW}/2026-06-15_BESPOKE-OUTBACK-BLACK-FD-V4-02-PROOF.png",
     "name": "Matching pair",
     "desc": "One for you, one for tatay."},
    {"img": f"{NEW}/2026-06-15_BESPOKE-OUTBACK-BLACK-FD-V6-03-DUO.png",
     "name": "P998 for 2",
     "desc": "Two pairs + complete inclusions."},
    {"img": f"{NEW}/2026-06-15_BESPOKE-OUTBACK-BLACK-FD-V4-04-PERKS.png",
     "name": "Free delivery",
     "desc": "No COD fee. To your door."},
    {"img": f"{NEW}/2026-06-15_BESPOKE-OUTBACK-BLACK-FD-V3-02-GIFT.png",
     "name": "Comes ready to give",
     "desc": "FOR DAD tag included."},
    {"img": f"{NEW}/2026-06-15_BESPOKE-OUTBACK-SERIES-FD-V9-06-CTA.png",
     "name": "Mix & match",
     "desc": "Pick any 2 from the Outback series."},
]


def tagged(url):
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}{UTM}"


def png_to_jpg(png_path: Path, jpg_path: Path, quality: int = 90) -> Path:
    """Convert PNG to JPG (Meta prefers JPG for ads). Returns the JPG path."""
    jpg_path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.open(png_path)
    if img.mode in ("RGBA", "LA", "P"):
        bg = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "P":
            img = img.convert("RGBA")
        bg.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
        img = bg
    elif img.mode != "RGB":
        img = img.convert("RGB")
    img.save(jpg_path, "JPEG", quality=quality, optimize=True)
    return jpg_path


def prep_jpg(src_path: str) -> Path:
    """Ensure each card's PNG has a matching JPG ready to upload."""
    src = PROJECT_DIR / src_path
    if not src.exists():
        raise FileNotFoundError(src)
    if src.suffix.lower() in (".jpg", ".jpeg"):
        return src
    jpg = JPG_TMP_DIR / (src.stem + ".jpg")
    if not jpg.exists() or jpg.stat().st_mtime < src.stat().st_mtime:
        png_to_jpg(src, jpg)
    return jpg


def api_post(endpoint, payload):
    payload["access_token"] = TOKEN
    r = requests.post(f"{BASE}/{endpoint}", json=payload, timeout=60)
    if not r.ok:
        raise RuntimeError(f"POST {endpoint} -> {r.status_code}: {r.text}")
    return r.json()


def upload_image(jpg_path: Path):
    with open(jpg_path, "rb") as f:
        r = requests.post(f"{BASE}/{ACCOUNT}/adimages",
                          params={"access_token": TOKEN},
                          files={"filename": (jpg_path.name, f, "image/jpeg")},
                          timeout=120)
    if not r.ok:
        raise RuntimeError(f"image upload {jpg_path.name} -> {r.status_code}: {r.text}")
    for _, meta in r.json().get("images", {}).items():
        return meta["hash"]
    raise ValueError(f"unexpected upload response: {r.text}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    for name, val in [("META_ADS_ACCESS_TOKEN", TOKEN),
                      ("META_AD_ACCOUNT_ID", ACCOUNT),
                      ("META_PAGE_ID", PAGE_ID)]:
        if not val:
            sys.exit(f"Error: {name} not set in .env")

    print(f"\n{'DRY RUN -- ' if args.dry_run else ''}FD 2-Pair Carousel (PAUSED)")
    print("=" * 60)
    print(f"  Campaign : {CAMPAIGN_NAME}  (Traffic)")
    print(f"  Ad set   : {ADSET_NAME}")
    print(f"  Budget   : P{DAILY_BUDGET_PESOS}/day")
    print(f"  Geo      : PH minus Mindanao + Cagayan Valley (Luzon + Visayas)")
    print(f"  Audience : Lookalike {LOOKALIKE_ID} (Chatters)")
    print(f"  Landing  : {LANDING}")
    print(f"  Cards    : {len(CARDS)}")
    for i, c in enumerate(CARDS, 1):
        ok = "ok" if (PROJECT_DIR / c["img"]).exists() else "MISSING"
        print(f"    {i}. {c['name']:24} [{ok}]")

    # Pre-convert all PNGs to JPGs (catches missing files / Pillow errors before any API call)
    print(f"\n  Converting PNG -> JPG in {JPG_TMP_DIR.relative_to(PROJECT_DIR)}/ ...")
    jpgs = [prep_jpg(c["img"]) for c in CARDS]
    total_kb = sum(p.stat().st_size for p in jpgs) // 1024
    print(f"  {len(jpgs)} JPGs ready ({total_kb} KB total)")

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
            "billing_event": "IMPRESSIONS",
            "optimization_goal": "LANDING_PAGE_VIEWS",
            "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
            "daily_budget": DAILY_BUDGET_PESOS * 100,
            "targeting": {
                "geo_locations": {"countries": ["PH"]},
                "excluded_geo_locations": {
                    "regions": [{"key": k} for k in EXCLUDED_REGIONS]},
                "age_min": 24, "age_max": 55,
                "custom_audiences": [{"id": LOOKALIKE_ID}],
                "targeting_automation": {"advantage_audience": 0},
            },
            "status": "PAUSED",
        })
        created["adset_id"] = adset["id"]
        print(f"  ad set   : {adset['id']}")

        # 3. Upload images
        child = []
        for i, (c, jpg) in enumerate(zip(CARDS, jpgs), 1):
            h = upload_image(jpg)
            child.append({
                "link": tagged(LANDING), "image_hash": h,
                "name": c["name"], "description": c["desc"],
                "call_to_action": {"type": "SHOP_NOW"},
            })
            print(f"  image {i}  : {h[:12]}...  {c['name']}")

        # 4. Carousel creative (order locked, no auto end card)
        creative = api_post(f"{ACCOUNT}/adcreatives", {
            "name": "FD 2-Pair Carousel creative",
            "object_story_spec": {
                "page_id": PAGE_ID,
                "link_data": {
                    "message": PRIMARY_TEXT,
                    "link": tagged(LANDING),
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
            "name": "FD 2-Pair Carousel",
            "adset_id": adset["id"],
            "creative": {"creative_id": creative["id"]},
            "status": "PAUSED",
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
