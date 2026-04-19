"""
Stage PAUSED Meta Ads from contents/ready/ images + manual captions.

Sibling to stage_ad.py. Where stage_ad.py is pipeline.json-driven (caption IDs),
this tool is creative-plan-driven: you hand it image paths + one caption +
an audience/budget preset, it stages N ads (multi-creative adset pattern).

Plan file shape:
    {
      "ad_set": {
        "name": "Cold - Metro Manila",
        "targeting_preset": "metro_manila_cold",
        "daily_budget_php": 100,
        "caption": "...",
        "headline": "...",
        "creatives": [
          {"image_path": "contents/ready/person/rasta-brown/abc.png"},
          ...
        ]
      }
    }

Usage:
    python tools/meta_ads/stage_creatives.py --plan .tmp/marketing-plan.json --dry-run
    python tools/meta_ads/stage_creatives.py --plan .tmp/marketing-plan.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_DIR / ".env")

sys.path.insert(0, str(PROJECT_DIR / "tools" / "meta_ads"))
from stage_ad import (
    api_post,
    load_ads_config,
    save_ads_config,
    resolve_campaign,
    verify_ad_set,
)

TMP_DIR = PROJECT_DIR / ".tmp"
PRESETS_FILE = PROJECT_DIR / "command-center" / "presets" / "marketing.json"
STAGED_LOG = TMP_DIR / "marketing-staged.json"

META_ADS_ACCESS_TOKEN = os.environ.get("META_ADS_ACCESS_TOKEN")
META_AD_ACCOUNT_ID = os.environ.get("META_AD_ACCOUNT_ID")
META_PAGE_ID = os.environ.get("META_PAGE_ID")
GRAPH_API_VERSION = "v21.0"
BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

LANDING_PAGE_BASE = "https://duberymnl.com"


# -- Preset resolvers ---------------------------------------------------------

def load_presets() -> dict:
    if not PRESETS_FILE.exists():
        raise FileNotFoundError(f"Presets file not found: {PRESETS_FILE}")
    return json.loads(PRESETS_FILE.read_text(encoding="utf-8"))


def build_targeting_from_preset(preset_key: str) -> dict:
    """Resolve a marketing.json audience preset key to a Meta targeting dict."""
    presets = load_presets()
    aud = presets.get("audiences", {}).get(preset_key)
    if not aud:
        raise ValueError(f"Unknown audience preset: {preset_key}")

    aud_type = aud.get("type")
    aud_id = aud.get("id")
    if not aud_id:
        raise ValueError(f"Preset '{preset_key}' missing id")

    if aud_type == "saved_audience":
        return {"saved_audiences": [{"id": str(aud_id)}]}

    if aud_type == "custom_audience":
        return {
            "custom_audiences": [{"id": str(aud_id)}],
            "geo_locations": {"countries": ["PH"]},
            "age_min": 18,
            "age_max": 45,
        }

    raise ValueError(f"Preset '{preset_key}' has unknown type: {aud_type}")


def pesos_to_centavos(daily_php: int | float) -> int:
    return int(daily_php) * 100


# -- Plan validation ----------------------------------------------------------

REQUIRED_AD_SET_KEYS = {
    "name", "targeting_preset", "daily_budget_php", "caption", "creatives",
}


def load_and_validate_plan(plan_path: str) -> dict:
    p = Path(plan_path)
    if not p.exists():
        print(f"Error: plan file not found: {plan_path}", file=sys.stderr)
        sys.exit(1)
    plan = json.loads(p.read_text(encoding="utf-8"))
    ad_set = plan.get("ad_set")
    if not isinstance(ad_set, dict):
        print("Error: plan must have 'ad_set' object", file=sys.stderr)
        sys.exit(1)
    missing = REQUIRED_AD_SET_KEYS - set(ad_set.keys())
    if missing:
        print(f"Error: ad_set missing keys: {sorted(missing)}", file=sys.stderr)
        sys.exit(1)
    if not ad_set["creatives"]:
        print("Error: ad_set.creatives is empty", file=sys.stderr)
        sys.exit(1)
    for i, c in enumerate(ad_set["creatives"]):
        if not c.get("image_path"):
            print(f"Error: creatives[{i}] missing image_path", file=sys.stderr)
            sys.exit(1)
    return plan


# -- Image upload (content-type aware) ----------------------------------------

def upload_image_typed(file_path: Path, ad_account_id: str) -> str:
    """Upload an image to Meta ad library, auto-detecting content type."""
    ext = file_path.suffix.lower()
    if ext == ".png":
        content_type = "image/png"
    elif ext in (".jpg", ".jpeg"):
        content_type = "image/jpeg"
    elif ext == ".webp":
        content_type = "image/webp"
    else:
        raise ValueError(f"Unsupported image extension: {ext}")

    url = f"{BASE}/{ad_account_id}/adimages"
    with open(file_path, "rb") as f:
        response = requests.post(
            url,
            params={"access_token": META_ADS_ACCESS_TOKEN},
            files={"filename": (file_path.name, f, content_type)},
        )
    if not response.ok:
        raise RuntimeError(f"Image upload error {response.status_code}: {response.text}")
    data = response.json()
    images = data.get("images", {})
    for _name, meta in images.items():
        return meta["hash"]
    raise ValueError(f"Unexpected image upload response: {data}")


# -- Ad Set with preset targeting ---------------------------------------------

def resolve_ad_set_with_targeting(
    config: dict,
    campaign_id: str,
    daily_budget_centavos: int,
    ad_set_name: str,
    targeting: dict,
    dry_run: bool = False,
) -> str:
    """Get existing ad set or create new with caller-supplied targeting."""
    ad_sets = config.setdefault("ad_sets", {})
    key = ad_set_name
    existing = ad_sets.get(key, {})
    ad_set_id = existing.get("ad_set_id")

    if ad_set_id:
        if dry_run:
            print(f"  Ad Set [{key}]: {ad_set_id} (from config, dry-run)")
            return ad_set_id
        if verify_ad_set(ad_set_id):
            print(f"  Ad Set [{key}]: {ad_set_id} (reusing)")
            return ad_set_id
        print(f"  Creating new ad set [{key}] (previous deleted)...")

    if dry_run:
        print(f"  Ad Set [{key}]: NEW -- '{ad_set_name}' | Budget: P{daily_budget_centavos // 100}/day (dry-run)")
        return f"DRY_RUN_AD_SET_{key}"

    print(f"  Creating ad set: '{ad_set_name}' | Budget: P{daily_budget_centavos // 100}/day")
    data = api_post(
        f"{META_AD_ACCOUNT_ID}/adsets",
        {
            "name": ad_set_name,
            "campaign_id": campaign_id,
            "billing_event": "IMPRESSIONS",
            "optimization_goal": "LANDING_PAGE_VIEWS",
            "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
            "daily_budget": daily_budget_centavos,
            "targeting": targeting,
            "status": "PAUSED",
        },
    )
    ad_set_id = data["id"]
    ad_sets[key] = {
        "ad_set_id": ad_set_id,
        "ad_set_name": ad_set_name,
        "daily_budget": daily_budget_centavos,
        "targeting": targeting,
    }
    save_ads_config(config)
    print(f"  Ad Set created: {ad_set_id}")
    return ad_set_id


# -- Stage one creative -------------------------------------------------------

def stage_one_creative(
    creative: dict,
    caption: str,
    headline: str,
    ad_set_id: str,
    ad_set_name: str,
    campaign_id: str,
    dry_run: bool = False,
) -> dict | None:
    """Upload image + create adcreative + ad (PAUSED). Returns staged entry or None."""
    img_rel = creative["image_path"].replace("\\", "/")
    img_path = (PROJECT_DIR / img_rel).resolve()

    if not img_path.exists():
        print(f"    SKIP: image not found: {img_rel}")
        return None

    short_id = img_path.stem[:40]
    landing_url = f"{LANDING_PAGE_BASE}/?ref=ads-{short_id}"

    if dry_run:
        print(f"    would stage: {img_path.name}")
        print(f"      CTA: SHOP_NOW -> {landing_url}")
        return {
            "image_path": str(img_rel),
            "dry_run": True,
        }

    print(f"    Staging: {img_path.name}")
    try:
        image_hash = upload_image_typed(img_path, META_AD_ACCOUNT_ID)

        creative_name = f"DuberyMNL - {short_id}"
        link_data = {
            "message": caption,
            "link": landing_url,
            "image_hash": image_hash,
            "call_to_action": {"type": "SHOP_NOW"},
        }
        if headline:
            link_data["name"] = headline

        creative_data = api_post(
            f"{META_AD_ACCOUNT_ID}/adcreatives",
            {
                "name": creative_name,
                "object_story_spec": {
                    "page_id": META_PAGE_ID,
                    "link_data": link_data,
                },
            },
        )
        creative_id = creative_data["id"]

        ad_name = f"DuberyMNL - {short_id}"
        ad_data = api_post(
            f"{META_AD_ACCOUNT_ID}/ads",
            {
                "name": ad_name,
                "adset_id": ad_set_id,
                "creative": {"creative_id": creative_id},
                "status": "PAUSED",
            },
        )
        ad_id = ad_data["id"]
        print(f"      -> PAUSED | ad: {ad_id}")

        return {
            "image_path": str(img_rel),
            "image_hash": image_hash,
            "creative_id": creative_id,
            "ad_id": ad_id,
            "ad_set_id": ad_set_id,
            "ad_set_name": ad_set_name,
            "campaign_id": campaign_id,
            "staged_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        print(f"    FAIL: {e}")
        return None


# -- Main ---------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Stage PAUSED Meta Ads from creative plan")
    parser.add_argument("--plan", required=True, help="Path to creative plan JSON")
    parser.add_argument("--dry-run", action="store_true", help="Preview without calling Meta API")
    parser.add_argument("--new-campaign", action="store_true", help="Create fresh campaign (ignore saved config)")
    args = parser.parse_args()

    for var_name, var_val in [
        ("META_ADS_ACCESS_TOKEN", META_ADS_ACCESS_TOKEN),
        ("META_AD_ACCOUNT_ID", META_AD_ACCOUNT_ID),
        ("META_PAGE_ID", META_PAGE_ID),
    ]:
        if not var_val:
            print(f"Error: {var_name} not set in .env", file=sys.stderr)
            sys.exit(1)

    plan = load_and_validate_plan(args.plan)
    ad_set_def = plan["ad_set"]

    print("\nMeta Ads Staging (Creative Plan)")
    print("=" * 50)
    print(f"  Ad Set: {ad_set_def['name']}")
    print(f"  Targeting preset: {ad_set_def['targeting_preset']}")
    print(f"  Budget: P{ad_set_def['daily_budget_php']}/day")
    print(f"  Creatives: {len(ad_set_def['creatives'])}")
    print(f"  Dry-run: {args.dry_run}")

    try:
        targeting = build_targeting_from_preset(ad_set_def["targeting_preset"])
    except (ValueError, FileNotFoundError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)

    daily_centavos = pesos_to_centavos(ad_set_def["daily_budget_php"])
    caption = ad_set_def["caption"]
    headline = ad_set_def.get("headline", "")

    config = {} if args.new_campaign else load_ads_config()
    campaign_id = resolve_campaign(config, dry_run=args.dry_run)
    ad_set_id = resolve_ad_set_with_targeting(
        config,
        campaign_id,
        daily_centavos,
        ad_set_def["name"],
        targeting,
        dry_run=args.dry_run,
    )

    print(f"\nStaging {len(ad_set_def['creatives'])} creative(s)...")
    staged = []
    for creative in ad_set_def["creatives"]:
        result = stage_one_creative(
            creative,
            caption,
            headline,
            ad_set_id,
            ad_set_def["name"],
            campaign_id,
            dry_run=args.dry_run,
        )
        if result:
            staged.append(result)

    print(f"\n{'=' * 50}")
    print(f"  {'Would stage' if args.dry_run else 'Staged'}: {len(staged)}/{len(ad_set_def['creatives'])}")

    if not args.dry_run and staged:
        TMP_DIR.mkdir(exist_ok=True)
        log = []
        if STAGED_LOG.exists():
            try:
                log = json.loads(STAGED_LOG.read_text(encoding="utf-8"))
            except Exception:
                log = []
        log.extend(staged)
        STAGED_LOG.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  Logged to {STAGED_LOG.relative_to(PROJECT_DIR)}")

    account_numeric = META_AD_ACCOUNT_ID.replace("act_", "")
    print(f"\nAds Manager: https://www.facebook.com/adsmanager/manage/campaigns?act={account_numeric}")


if __name__ == "__main__":
    main()
