"""
Stage PAUSED Meta Ads from IMAGE_APPROVED captions.

Supports single ad set (legacy) or multi-ad-set from a plan file.

Usage:
    # Legacy: single ad set
    python tools/meta_ads/stage_ad.py --id 20260320-001
    python tools/meta_ads/stage_ad.py --all
    python tools/meta_ads/stage_ad.py --all --dry-run
    python tools/meta_ads/stage_ad.py --all --budget 300

    # Multi-ad-set from plan file
    python tools/meta_ads/stage_ad.py --plan .tmp/ads_plan.json --dry-run
    python tools/meta_ads/stage_ad.py --plan .tmp/ads_plan.json --budget 200
    python tools/meta_ads/stage_ad.py --plan .tmp/ads_plan.json --new-campaign
"""

import argparse
try:
    import fcntl
except ImportError:
    fcntl = None
    import msvcrt
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_DIR / ".env")

TMP_DIR = PROJECT_DIR / ".tmp"
IMAGES_DIR = PROJECT_DIR / "output" / "images"
PIPELINE_FILE = TMP_DIR / "pipeline.json"
PIPELINE_LOCK = TMP_DIR / "pipeline.json.lock"
ADS_CONFIG_FILE = TMP_DIR / "ads_config.json"

META_ADS_ACCESS_TOKEN = os.environ.get("META_ADS_ACCESS_TOKEN")
META_AD_ACCOUNT_ID = os.environ.get("META_AD_ACCOUNT_ID")
META_PAGE_ID = os.environ.get("META_PAGE_ID")
GRAPH_API_VERSION = "v21.0"
BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

DEFAULT_TARGETING = {
    "geo_locations": {"countries": ["PH"]},
    "age_min": 18,
    "age_max": 45,
    "flexible_spec": [
        {
            "interests": [
                {"id": "6003255640088", "name": "Sunglasses"},
                {"id": "6004233997787", "name": "Eyewear"},
                {"id": "6003353550130", "name": "Motorcycles"},
                {"id": "6002985584323", "name": "Outdoor recreation"},
                {"id": "6003346592981", "name": "Online shopping"},
                {"id": "6003263791114", "name": "Shopping"},
                {"id": "6004160395895", "name": "Travel"},
            ]
        }
    ],
}

DEFAULT_DAILY_BUDGET = int(os.environ.get("META_ADS_DAILY_BUDGET", 200)) * 100  # pesos to centavos

LANDING_PAGE_BASE = "https://duberymnl.com"


# -- Ads Config (persistent campaign/ad set state) ----------------------------

def load_ads_config():
    if ADS_CONFIG_FILE.exists():
        config = json.loads(ADS_CONFIG_FILE.read_text())
        # Migrate legacy single ad set to ad_sets dict
        if "ad_set_id" in config and "ad_sets" not in config:
            config["ad_sets"] = {
                "default": {
                    "ad_set_id": config.pop("ad_set_id"),
                    "ad_set_name": config.pop("ad_set_name", ""),
                    "daily_budget": config.pop("daily_budget", 0),
                }
            }
        return config
    return {}


def save_ads_config(config):
    if ADS_CONFIG_FILE.exists():
        ADS_CONFIG_FILE.with_suffix(".json.bak").write_text(
            ADS_CONFIG_FILE.read_text()
        )
    ADS_CONFIG_FILE.write_text(json.dumps(config, indent=2, ensure_ascii=False))


# -- Plan file ----------------------------------------------------------------

def load_ads_plan(plan_path):
    path = Path(plan_path)
    if not path.exists():
        print(f"Error: plan file not found: {plan_path}", file=sys.stderr)
        sys.exit(1)
    plan = json.loads(path.read_text())
    if "ad_sets" not in plan or not isinstance(plan["ad_sets"], list):
        print("Error: plan file must have an 'ad_sets' array", file=sys.stderr)
        sys.exit(1)
    for i, ad_set in enumerate(plan["ad_sets"]):
        if "name" not in ad_set or "ids" not in ad_set:
            print(f"Error: ad_sets[{i}] must have 'name' and 'ids'", file=sys.stderr)
            sys.exit(1)
        if not ad_set["ids"]:
            print(f"Warning: ad_sets[{i}] '{ad_set['name']}' has no IDs, will skip")
    return plan


# -- Pipeline helpers ----------------------------------------------------------

def load_pipeline():
    if not PIPELINE_FILE.exists():
        print("Error: .tmp/pipeline.json not found", file=sys.stderr)
        sys.exit(1)
    return json.loads(PIPELINE_FILE.read_text())


def update_pipeline_entry(caption_id, fields):
    """Update fields for a caption in pipeline.json (file-locked)."""
    with open(PIPELINE_LOCK, "w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX) if fcntl else msvcrt.locking(lf.fileno(), msvcrt.LK_LOCK, 1)
        try:
            pipeline = json.loads(PIPELINE_FILE.read_text())
            PIPELINE_FILE.with_suffix(".json.bak").write_text(
                json.dumps(pipeline, indent=2, ensure_ascii=False)
            )
            for c in pipeline:
                if str(c.get("id")) == caption_id:
                    c.update(fields)
                    break
            PIPELINE_FILE.write_text(json.dumps(pipeline, indent=2, ensure_ascii=False))
        finally:
            fcntl.flock(lf, fcntl.LOCK_UN) if fcntl else msvcrt.locking(lf.fileno(), msvcrt.LK_UNLCK, 1)


# -- Meta API helpers ----------------------------------------------------------

def api_post(endpoint, payload):
    url = f"{BASE}/{endpoint}"
    payload["access_token"] = META_ADS_ACCESS_TOKEN
    response = requests.post(url, json=payload)
    if not response.ok:
        raise RuntimeError(f"API error {response.status_code}: {response.text}")
    return response.json()


def api_get(endpoint):
    url = f"{BASE}/{endpoint}"
    response = requests.get(url, params={"access_token": META_ADS_ACCESS_TOKEN})
    return response


def verify_campaign(campaign_id):
    """Check if a campaign still exists on Meta. Returns True if valid."""
    resp = api_get(f"{campaign_id}?fields=id,name,status")
    if resp.ok:
        return True
    print(f"  Campaign {campaign_id} no longer exists on Meta (status {resp.status_code})")
    return False


def verify_ad_set(ad_set_id):
    """Check if an ad set still exists on Meta. Returns True if valid."""
    resp = api_get(f"{ad_set_id}?fields=id,name,status")
    if resp.ok:
        return True
    print(f"  Ad set {ad_set_id} no longer exists on Meta (status {resp.status_code})")
    return False


# -- Resolve or create --------------------------------------------------------

def resolve_campaign(config, dry_run=False):
    """Get existing campaign or create new one. Returns campaign_id."""
    campaign_id = config.get("campaign_id")

    if campaign_id:
        if dry_run:
            print(f"  Campaign: {campaign_id} (from config, skip verify in dry-run)")
            return campaign_id
        if verify_campaign(campaign_id):
            print(f"  Campaign: {campaign_id} (reusing existing)")
            return campaign_id
        print("  Creating new campaign (previous one deleted)...")

    campaign_name = "DuberyMNL Traffic"

    if dry_run:
        print(f"  Campaign: NEW -- \"{campaign_name}\" (dry-run, not created)")
        return "DRY_RUN_CAMPAIGN"

    print(f"  Creating campaign: \"{campaign_name}\"...")
    data = api_post(
        f"{META_AD_ACCOUNT_ID}/campaigns",
        {
            "name": campaign_name,
            "objective": "OUTCOME_TRAFFIC",
            "status": "PAUSED",
            "special_ad_categories": [],
            "is_adset_budget_sharing_enabled": False,
        },
    )
    campaign_id = data["id"]
    config["campaign_id"] = campaign_id
    config["campaign_name"] = campaign_name
    config["created_at"] = datetime.now(timezone.utc).isoformat()
    save_ads_config(config)
    print(f"  Campaign created: {campaign_id}")
    return campaign_id


def resolve_ad_set(config, campaign_id, daily_budget, ad_set_name=None, ad_set_key=None, dry_run=False):
    """Get existing ad set or create new one. Returns ad_set_id.

    ad_set_key: key in config['ad_sets'] dict (plan mode). None = legacy 'default'.
    ad_set_name: display name for the ad set. None = default name.
    """
    key = ad_set_key or "default"
    name = ad_set_name or "DuberyMNL - PH 18-45 Sunglasses"

    # Look up existing ad set from config
    ad_sets = config.setdefault("ad_sets", {})
    existing = ad_sets.get(key, {})
    ad_set_id = existing.get("ad_set_id")

    if ad_set_id:
        if dry_run:
            print(f"  Ad Set [{key}]: {ad_set_id} (from config, skip verify in dry-run)")
            return ad_set_id
        if verify_ad_set(ad_set_id):
            print(f"  Ad Set [{key}]: {ad_set_id} (reusing existing)")
            return ad_set_id
        print(f"  Creating new ad set [{key}] (previous one deleted)...")

    if dry_run:
        print(f"  Ad Set [{key}]: NEW -- \"{name}\" | Budget: P{daily_budget // 100}/day (dry-run)")
        return f"DRY_RUN_AD_SET_{key}"

    print(f"  Creating ad set: \"{name}\" | Budget: P{daily_budget // 100}/day...")
    data = api_post(
        f"{META_AD_ACCOUNT_ID}/adsets",
        {
            "name": name,
            "campaign_id": campaign_id,
            "billing_event": "IMPRESSIONS",
            "optimization_goal": "LANDING_PAGE_VIEWS",
            "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
            "daily_budget": daily_budget,
            "targeting": DEFAULT_TARGETING,
            "status": "PAUSED",
        },
    )
    ad_set_id = data["id"]
    ad_sets[key] = {
        "ad_set_id": ad_set_id,
        "ad_set_name": name,
        "daily_budget": daily_budget,
    }
    save_ads_config(config)
    print(f"  Ad Set created: {ad_set_id}")
    return ad_set_id


# -- Image upload --------------------------------------------------------------

def upload_image(file_path, ad_account_id):
    url = f"{BASE}/{ad_account_id}/adimages"
    with open(file_path, "rb") as f:
        response = requests.post(
            url,
            params={"access_token": META_ADS_ACCESS_TOKEN},
            files={"filename": (file_path.name, f, "image/jpeg")},
        )
    if not response.ok:
        raise RuntimeError(f"Image upload error {response.status_code}: {response.text}")
    data = response.json()
    images = data.get("images", {})
    for _, meta in images.items():
        return meta["hash"]
    raise ValueError(f"Unexpected image upload response: {data}")


# -- Per-caption staging -------------------------------------------------------

def stage_one(caption, campaign_id, ad_set_id, ad_set_name="", dry_run=False):
    """Stage a single IMAGE_APPROVED caption. Returns True on success."""
    cid = str(caption["id"])

    if caption.get("status") != "IMAGE_APPROVED":
        print(f"    SKIP #{cid}: status is '{caption.get('status')}' -- only IMAGE_APPROVED can be staged")
        return False

    if caption.get("ad_id"):
        print(f"    SKIP #{cid}: already staged (ad: {caption['ad_id']})")
        return False

    # Check multiple extensions
    image_path = None
    for ext in [".jpg", ".jpeg", ".png"]:
        p = IMAGES_DIR / f"dubery_{cid}{ext}"
        if p.exists():
            image_path = p
            break
    if not image_path:
        print(f"    SKIP #{cid}: image not found")
        return False

    caption_text = caption.get("caption_text", "")
    headline = caption.get("headline", caption_text[:40])
    landing_url = f"{LANDING_PAGE_BASE}/?id={cid}"

    if dry_run:
        print(f"    #{cid}: {caption_text.split(chr(10))[0][:60]}")
        print(f"      Image: {image_path.name} | CTA: SHOP_NOW -> {landing_url}")
        return True

    print(f"    Staging #{cid}: {headline[:50]}")

    try:
        image_hash = upload_image(image_path, META_AD_ACCOUNT_ID)

        creative_name = f"DuberyMNL - {cid}"
        creative_data = api_post(
            f"{META_AD_ACCOUNT_ID}/adcreatives",
            {
                "name": creative_name,
                "object_story_spec": {
                    "page_id": META_PAGE_ID,
                    "link_data": {
                        "message": caption_text,
                        "link": landing_url,
                        "image_hash": image_hash,
                        "call_to_action": {"type": "SHOP_NOW"},
                    },
                },
            },
        )
        creative_id = creative_data["id"]

        ad_name = f"DuberyMNL - {cid}"
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

        update_pipeline_entry(cid, {
            "status": "AD_STAGED",
            "ad_campaign_id": campaign_id,
            "ad_set_id": ad_set_id,
            "ad_set_name": ad_set_name,
            "ad_creative_id": creative_id,
            "ad_id": ad_id,
            "ad_staged_at": datetime.now(timezone.utc).isoformat(),
        })

        print(f"      -> PAUSED | ad: {ad_id}")
        return True

    except Exception as e:
        print(f"    FAIL #{cid}: {e}")
        return False


# -- Main ----------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Stage PAUSED Meta Ads from pipeline")
    id_group = parser.add_mutually_exclusive_group(required=True)
    id_group.add_argument("--id", type=str, help="Single caption ID")
    id_group.add_argument("--all", action="store_true", help="Stage all IMAGE_APPROVED, unstaged captions")
    id_group.add_argument("--plan", type=str, help="Path to ads plan JSON (multi-ad-set)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without making API calls")
    parser.add_argument("--budget", type=int, default=None, help="Total daily budget in pesos (split across ad sets)")
    parser.add_argument("--new-campaign", action="store_true", help="Create fresh campaign (ignore saved config)")
    args = parser.parse_args()

    # Validate env
    for var_name, var_val in [("META_ADS_ACCESS_TOKEN", META_ADS_ACCESS_TOKEN),
                               ("META_AD_ACCOUNT_ID", META_AD_ACCOUNT_ID),
                               ("META_PAGE_ID", META_PAGE_ID)]:
        if not var_val:
            print(f"Error: {var_name} not set in .env", file=sys.stderr)
            sys.exit(1)

    total_budget = (args.budget * 100) if args.budget else DEFAULT_DAILY_BUDGET
    pipeline = load_pipeline()
    pipeline_by_id = {str(c["id"]): c for c in pipeline}
    config = {} if args.new_campaign else load_ads_config()

    # ── Plan mode (multi-ad-set) ──
    if args.plan:
        plan = load_ads_plan(args.plan)
        num_sets = len([s for s in plan["ad_sets"] if s.get("ids")])
        per_set_budget = total_budget // max(num_sets, 1)

        print(f"\nMeta Ads Staging (Plan Mode)")
        print(f"{'=' * 50}")
        print(f"  Ad Sets: {num_sets}")
        print(f"  Total Budget: P{total_budget // 100}/day (P{per_set_budget // 100}/day per ad set)")

        campaign_id = resolve_campaign(config, dry_run=args.dry_run)

        total_ok, total_fail = 0, 0
        seen_ids = set()

        for ad_set_def in plan["ad_sets"]:
            set_name = ad_set_def["name"]
            set_ids = ad_set_def["ids"]

            if not set_ids:
                print(f"\n  Skipping '{set_name}' (no IDs)")
                continue

            # Dedup across ad sets
            deduped_ids = []
            for cid in set_ids:
                if cid in seen_ids:
                    print(f"  Warning: #{cid} already in another ad set, skipping")
                else:
                    seen_ids.add(cid)
                    deduped_ids.append(cid)

            print(f"\n{'─' * 50}")
            print(f"  Ad Set: \"{set_name}\" | {len(deduped_ids)} ads | P{per_set_budget // 100}/day")
            print(f"{'─' * 50}")

            ad_set_id = resolve_ad_set(
                config, campaign_id, per_set_budget,
                ad_set_name=set_name, ad_set_key=set_name,
                dry_run=args.dry_run,
            )

            for cid in deduped_ids:
                caption = pipeline_by_id.get(str(cid))
                if not caption:
                    print(f"    SKIP #{cid}: not found in pipeline.json")
                    total_fail += 1
                    continue
                ok = stage_one(caption, campaign_id, ad_set_id, ad_set_name=set_name, dry_run=args.dry_run)
                if ok:
                    total_ok += 1
                else:
                    total_fail += 1

        print(f"\n{'=' * 50}")
        print(f"  Total: {total_ok} staged, {total_fail} skipped/failed")

    # ── Legacy mode (single ad set) ──
    else:
        if args.id:
            targets = [c for c in pipeline if str(c["id"]) == str(args.id)]
            if not targets:
                print(f"Error: caption #{args.id} not found in pipeline.json", file=sys.stderr)
                sys.exit(1)
        else:
            targets = [
                c for c in pipeline
                if c.get("status") == "IMAGE_APPROVED" and not c.get("ad_id")
            ]

        print(f"\nMeta Ads Staging")
        print(f"{'─' * 40}")
        print(f"  Targets: {len(targets)} IMAGE_APPROVED caption(s)")
        print(f"  Budget: P{total_budget // 100}/day")

        if not targets:
            print("\nNo IMAGE_APPROVED captions to stage.")
            sys.exit(0)

        campaign_id = resolve_campaign(config, dry_run=args.dry_run)
        ad_set_id = resolve_ad_set(
            config, campaign_id, total_budget,
            ad_set_key="default", dry_run=args.dry_run,
        )

        print(f"\nStaging {len(targets)} ad(s)...")
        total_ok, total_fail = 0, 0

        for caption in targets:
            ok = stage_one(caption, campaign_id, ad_set_id, dry_run=args.dry_run)
            if ok:
                total_ok += 1
            else:
                total_fail += 1

        print(f"\n{'─' * 40}")
        print(f"  Done: {total_ok} staged, {total_fail} skipped/failed")

    # Sync sheet
    if not args.dry_run and total_ok > 0:
        print("Syncing sheet...", end=" ", flush=True)
        result = subprocess.run(
            [sys.executable, str(PROJECT_DIR / "tools" / "notion" / "sync_pipeline.py"), "--sheets-only"],
            capture_output=True, text=True
        )
        print("done" if result.returncode == 0 else f"warning -- {result.stderr.strip()}")

    account_numeric = META_AD_ACCOUNT_ID.replace("act_", "")
    print(f"Ads Manager: https://www.facebook.com/adsmanager/manage/campaigns?act={account_numeric}")


if __name__ == "__main__":
    main()
