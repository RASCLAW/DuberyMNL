"""
Stage PAUSED Meta Ads from IMAGE_APPROVED captions.

Uses a shared campaign + ad set structure (1 campaign, 1 ad set, N ads).
Campaign and ad set are reused across runs via .tmp/ads_config.json.

Usage:
    python tools/meta_ads/stage_ad.py --id 20260320-001
    python tools/meta_ads/stage_ad.py --all
    python tools/meta_ads/stage_ad.py --all --dry-run
    python tools/meta_ads/stage_ad.py --all --budget 300
    python tools/meta_ads/stage_ad.py --all --new-campaign
"""

import argparse
import fcntl
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
                {"id": "6003107902433", "name": "Sunglasses"},
                {"id": "6003348604616", "name": "Fashion accessories"},
                {"id": "6003634657498", "name": "Motorcycle"},
            ]
        }
    ],
}

DEFAULT_DAILY_BUDGET = int(os.environ.get("META_ADS_DAILY_BUDGET", 200)) * 100  # pesos to centavos

LANDING_PAGE_BASE = "https://duberymnl.vercel.app"


# ── Ads Config (persistent campaign/ad set state) ─────────────────────────────

def load_ads_config():
    if ADS_CONFIG_FILE.exists():
        return json.loads(ADS_CONFIG_FILE.read_text())
    return {}


def save_ads_config(config):
    if ADS_CONFIG_FILE.exists():
        ADS_CONFIG_FILE.with_suffix(".json.bak").write_text(
            ADS_CONFIG_FILE.read_text()
        )
    ADS_CONFIG_FILE.write_text(json.dumps(config, indent=2, ensure_ascii=False))


# ── Pipeline helpers ──────────────────────────────────────────────────────────

def load_pipeline():
    if not PIPELINE_FILE.exists():
        print("Error: .tmp/pipeline.json not found", file=sys.stderr)
        sys.exit(1)
    return json.loads(PIPELINE_FILE.read_text())


def update_pipeline_entry(caption_id, fields):
    """Update fields for a caption in pipeline.json (file-locked)."""
    with open(PIPELINE_LOCK, "w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
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
            fcntl.flock(lf, fcntl.LOCK_UN)


# ── Meta API helpers ─────────────────────────────────────────────────────────

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


# ── Resolve or create ────────────────────────────────────────────────────────

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
        },
    )
    campaign_id = data["id"]
    config["campaign_id"] = campaign_id
    config["campaign_name"] = campaign_name
    config["created_at"] = datetime.now(timezone.utc).isoformat()
    save_ads_config(config)
    print(f"  Campaign created: {campaign_id}")
    return campaign_id


def resolve_ad_set(config, campaign_id, daily_budget, dry_run=False):
    """Get existing ad set or create new one. Returns ad_set_id."""
    ad_set_id = config.get("ad_set_id")

    if ad_set_id:
        if dry_run:
            print(f"  Ad Set: {ad_set_id} (from config, skip verify in dry-run)")
            return ad_set_id
        if verify_ad_set(ad_set_id):
            print(f"  Ad Set: {ad_set_id} (reusing existing)")
            return ad_set_id
        print("  Creating new ad set (previous one deleted)...")

    ad_set_name = "DuberyMNL - PH 18-45 Sunglasses"

    if dry_run:
        print(f"  Ad Set: NEW -- \"{ad_set_name}\" | Budget: P{daily_budget // 100}/day (dry-run, not created)")
        return "DRY_RUN_AD_SET"

    print(f"  Creating ad set: \"{ad_set_name}\" | Budget: P{daily_budget // 100}/day...")
    data = api_post(
        f"{META_AD_ACCOUNT_ID}/adsets",
        {
            "name": ad_set_name,
            "campaign_id": campaign_id,
            "billing_event": "IMPRESSIONS",
            "optimization_goal": "LANDING_PAGE_VIEWS",
            "daily_budget": daily_budget,
            "targeting": DEFAULT_TARGETING,
            "status": "PAUSED",
        },
    )
    ad_set_id = data["id"]
    config["ad_set_id"] = ad_set_id
    config["ad_set_name"] = ad_set_name
    config["daily_budget"] = daily_budget
    save_ads_config(config)
    print(f"  Ad Set created: {ad_set_id}")
    return ad_set_id


# ── Image upload ─────────────────────────────────────────────────────────────

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


# ── Per-caption staging ──────────────────────────────────────────────────────

def stage_one(caption, campaign_id, ad_set_id, dry_run=False):
    """Stage a single IMAGE_APPROVED caption under the shared campaign/ad set.
    Returns True on success, False on skip/failure."""
    cid = str(caption["id"])

    if caption.get("status") != "IMAGE_APPROVED":
        print(f"  SKIP #{cid}: status is '{caption.get('status')}' -- only IMAGE_APPROVED can be staged")
        return False

    if caption.get("ad_id"):
        print(f"  SKIP #{cid}: already staged (ad: {caption['ad_id']})")
        return False

    image_path = IMAGES_DIR / f"dubery_{cid}.jpg"
    if not image_path.exists():
        print(f"  SKIP #{cid}: image not found at {image_path}")
        return False

    caption_text = caption.get("caption_text", "")
    headline = caption.get("headline", caption_text[:40])
    landing_url = f"{LANDING_PAGE_BASE}/?id={cid}"

    if dry_run:
        print(f"  DRY RUN #{cid}: {headline[:50]}")
        print(f"    Image: {image_path.name} | CTA: SHOP_NOW -> {landing_url}")
        return True

    print(f"  Staging #{cid}: {headline[:50]}")

    try:
        # Upload image
        image_hash = upload_image(image_path, META_AD_ACCOUNT_ID)

        # Create ad creative
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

        # Create ad
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

        # Update pipeline entry (file-locked)
        update_pipeline_entry(cid, {
            "status": "AD_STAGED",
            "ad_campaign_id": campaign_id,
            "ad_set_id": ad_set_id,
            "ad_creative_id": creative_id,
            "ad_id": ad_id,
            "ad_staged_at": datetime.now(timezone.utc).isoformat(),
        })

        print(f"    -> PAUSED | ad: {ad_id}")
        return True

    except Exception as e:
        print(f"  FAIL #{cid}: {e}")
        return False


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Stage PAUSED Meta Ads from pipeline")
    id_group = parser.add_mutually_exclusive_group(required=True)
    id_group.add_argument("--id", type=str, help="Single caption ID")
    id_group.add_argument("--all", action="store_true", help="Stage all IMAGE_APPROVED, unstaged captions")
    parser.add_argument("--dry-run", action="store_true", help="Preview without making API calls")
    parser.add_argument("--budget", type=int, default=None, help="Daily budget in pesos (default: 200 or META_ADS_DAILY_BUDGET)")
    parser.add_argument("--new-campaign", action="store_true", help="Create fresh campaign + ad set (ignore saved config)")
    args = parser.parse_args()

    # Validate env
    for var_name, var_val in [("META_ADS_ACCESS_TOKEN", META_ADS_ACCESS_TOKEN),
                               ("META_AD_ACCOUNT_ID", META_AD_ACCOUNT_ID),
                               ("META_PAGE_ID", META_PAGE_ID)]:
        if not var_val:
            print(f"Error: {var_name} not set in .env", file=sys.stderr)
            sys.exit(1)

    # Budget: CLI arg > .env > default (200 pesos)
    daily_budget = (args.budget * 100) if args.budget else DEFAULT_DAILY_BUDGET

    pipeline = load_pipeline()

    # Determine targets
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
    print(f"  Budget: P{daily_budget // 100}/day")

    if not targets:
        print("\nNo IMAGE_APPROVED captions to stage.")
        sys.exit(0)

    # Resolve shared campaign + ad set (once, before loop)
    config = {} if args.new_campaign else load_ads_config()

    campaign_id = resolve_campaign(config, dry_run=args.dry_run)
    ad_set_id = resolve_ad_set(config, campaign_id, daily_budget, dry_run=args.dry_run)

    # Stage each caption
    print(f"\nStaging {len(targets)} ad(s)...")
    succeeded, failed = 0, 0

    for caption in targets:
        ok = stage_one(caption, campaign_id, ad_set_id, dry_run=args.dry_run)
        if ok:
            succeeded += 1
        else:
            failed += 1

    print(f"\n{'─' * 40}")
    print(f"  Done: {succeeded} staged, {failed} skipped/failed")

    # Sync sheet
    if not args.dry_run and succeeded > 0:
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
