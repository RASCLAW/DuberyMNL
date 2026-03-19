"""
Stage a PAUSED Meta Ads campaign for one IMAGE_APPROVED caption.

Reads from .tmp/pipeline.json, uploads the image, creates a full
campaign → ad set → creative → ad structure (all PAUSED), then
writes the campaign IDs back to pipeline.json and syncs Notion.

Usage:
    python tools/meta_ads/stage_ad.py --id 5
    python tools/meta_ads/stage_ad.py --id 5 --dry-run
"""

import argparse
import json
import os
import shutil
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

META_ADS_ACCESS_TOKEN = os.environ.get("META_ADS_ACCESS_TOKEN")
META_AD_ACCOUNT_ID = os.environ.get("META_AD_ACCOUNT_ID")
META_PAGE_ID = os.environ.get("META_PAGE_ID")
GRAPH_API_VERSION = "v21.0"
BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


# ── Pipeline helpers ────────────────────────────────────────────────────────

def load_pipeline():
    path = TMP_DIR / "pipeline.json"
    if not path.exists():
        print("Error: .tmp/pipeline.json not found", file=sys.stderr)
        sys.exit(1)
    return json.loads(path.read_text())


def save_pipeline(pipeline):
    path = TMP_DIR / "pipeline.json"
    bak = TMP_DIR / "pipeline.json.bak"
    shutil.copy2(path, bak)
    path.write_text(json.dumps(pipeline, indent=2, ensure_ascii=False))


# ── Meta API helpers ─────────────────────────────────────────────────────────

def api_post(endpoint: str, payload: dict) -> dict:
    url = f"{BASE}/{endpoint}"
    payload["access_token"] = META_ADS_ACCESS_TOKEN
    response = requests.post(url, json=payload)
    if not response.ok:
        raise RuntimeError(f"API error {response.status_code}: {response.text}")
    return response.json()


def upload_image(file_path: Path, ad_account_id: str) -> str:
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


def create_campaign(ad_account_id: str, name: str) -> str:
    data = api_post(
        f"{ad_account_id}/campaigns",
        {
            "name": name,
            "objective": "OUTCOME_TRAFFIC",
            "status": "PAUSED",
            "special_ad_categories": [],
        },
    )
    return data["id"]


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

DEFAULT_DAILY_BUDGET = 20000  # centavos = ₱200


LANDING_PAGE_BASE = "https://duberymnl.vercel.app"


def create_ad_set(ad_account_id: str, campaign_id: str, name: str) -> str:
    data = api_post(
        f"{ad_account_id}/adsets",
        {
            "name": name,
            "campaign_id": campaign_id,
            "billing_event": "IMPRESSIONS",
            "optimization_goal": "LANDING_PAGE_VIEWS",
            "daily_budget": DEFAULT_DAILY_BUDGET,
            "targeting": DEFAULT_TARGETING,
            "status": "PAUSED",
        },
    )
    return data["id"]


def create_ad_creative(ad_account_id: str, page_id: str, name: str, caption: str, image_hash: str, caption_id: str) -> str:
    landing_url = f"{LANDING_PAGE_BASE}/?id={caption_id}"
    data = api_post(
        f"{ad_account_id}/adcreatives",
        {
            "name": name,
            "object_story_spec": {
                "page_id": page_id,
                "link_data": {
                    "message": caption,
                    "link": landing_url,
                    "image_hash": image_hash,
                    "call_to_action": {
                        "type": "SHOP_NOW",
                    },
                },
            },
        },
    )
    return data["id"]


def create_ad(ad_account_id: str, ad_set_id: str, creative_id: str, name: str) -> str:
    data = api_post(
        f"{ad_account_id}/ads",
        {
            "name": name,
            "adset_id": ad_set_id,
            "creative": {"creative_id": creative_id},
            "status": "PAUSED",
        },
    )
    return data["id"]


# ── Per-caption staging ───────────────────────────────────────────────────────

def stage_one(caption, pipeline, dry_run=False):
    """Stage a single IMAGE_APPROVED caption. Updates pipeline in place on success.
    Returns True on success, False on skip/failure."""
    cid = str(caption["id"])

    if caption.get("status") != "IMAGE_APPROVED":
        print(f"  SKIP #{cid}: status is '{caption.get('status')}' — only IMAGE_APPROVED can be staged")
        return False

    if caption.get("ad_campaign_id"):
        print(f"  SKIP #{cid}: already staged (campaign: {caption['ad_campaign_id']})")
        return False

    image_path = IMAGES_DIR / f"dubery_{cid}.jpg"
    if not image_path.exists():
        print(f"  SKIP #{cid}: image not found at {image_path}")
        return False

    vibe = caption.get("vibe", "DuberyMNL")
    date_str = datetime.now().strftime("%Y%m%d")
    campaign_name = f"DuberyMNL - {vibe} - {date_str}"
    headline = caption.get("headline", caption.get("caption_text", "")[:40])

    if dry_run:
        print(f"  DRY RUN #{cid}: {headline[:50]}")
        print(f"    Vibe: {vibe} | Image: {image_path.name} | Budget: ₱{DEFAULT_DAILY_BUDGET // 100}/day")
        print(f"    CTA: SHOP_NOW → {LANDING_PAGE_BASE}/?id={cid}")
        return True

    print(f"  Staging #{cid}: {headline[:50]}")

    image_hash = upload_image(image_path, META_AD_ACCOUNT_ID)
    campaign_id = create_campaign(META_AD_ACCOUNT_ID, campaign_name)
    ad_set_id = create_ad_set(META_AD_ACCOUNT_ID, campaign_id, f"{campaign_name} - Ad Set")
    caption_text = caption.get("caption_text", "")
    creative_id = create_ad_creative(
        META_AD_ACCOUNT_ID, META_PAGE_ID,
        f"{campaign_name} - Creative",
        caption_text,
        image_hash,
        cid,
    )
    ad_id = create_ad(META_AD_ACCOUNT_ID, ad_set_id, creative_id, f"{campaign_name} - Ad")

    for entry in pipeline:
        if str(entry["id"]) == cid:
            entry["status"] = "AD_STAGED"
            entry["ad_campaign_id"] = campaign_id
            entry["ad_set_id"] = ad_set_id
            entry["ad_creative_id"] = creative_id
            entry["ad_id"] = ad_id
            entry["ad_staged_at"] = datetime.now(timezone.utc).isoformat()
            break

    save_pipeline(pipeline)
    print(f"    → PAUSED | campaign: {campaign_id}")
    return True


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Stage PAUSED Meta Ads campaigns from pipeline")
    id_group = parser.add_mutually_exclusive_group(required=True)
    id_group.add_argument("--id", type=str, help="Single caption ID (e.g. 20260318-001 or 5)")
    id_group.add_argument("--all", action="store_true", help="Stage all IMAGE_APPROVED, unstaged captions")
    parser.add_argument("--dry-run", action="store_true", help="Preview without making API calls")
    args = parser.parse_args()

    # Validate env
    if not META_ADS_ACCESS_TOKEN:
        print("Error: META_ADS_ACCESS_TOKEN not set in .env", file=sys.stderr)
        sys.exit(1)
    if not META_AD_ACCOUNT_ID:
        print("Error: META_AD_ACCOUNT_ID not set in .env", file=sys.stderr)
        sys.exit(1)
    if not META_PAGE_ID:
        print("Error: META_PAGE_ID not set in .env", file=sys.stderr)
        sys.exit(1)

    pipeline = load_pipeline()

    if args.id:
        caption = next((c for c in pipeline if str(c["id"]) == str(args.id)), None)
        if not caption:
            print(f"Error: caption #{args.id} not found in pipeline.json", file=sys.stderr)
            sys.exit(1)
        stage_one(caption, pipeline, dry_run=args.dry_run)
    else:
        # --all mode
        targets = [
            c for c in pipeline
            if c.get("status") == "IMAGE_APPROVED" and not c.get("ad_campaign_id")
        ]
        print(f"Staging {len(targets)} IMAGE_APPROVED caption(s)...")
        succeeded, skipped = 0, 0
        for caption in targets:
            ok = stage_one(caption, pipeline, dry_run=args.dry_run)
            if ok:
                succeeded += 1
            else:
                skipped += 1
        print(f"\nDone: {succeeded} staged, {skipped} skipped")

    # Sync sheet once at the end
    if not args.dry_run:
        print("Syncing sheet...", end=" ", flush=True)
        result = subprocess.run(
            [sys.executable, str(PROJECT_DIR / "tools" / "notion" / "sync_pipeline.py"), "--sheets-only"],
            capture_output=True, text=True
        )
        print("done" if result.returncode == 0 else f"warning — {result.stderr.strip()}")

    account_numeric = META_AD_ACCOUNT_ID.replace("act_", "")
    print(f"Ads Manager: https://www.facebook.com/adsmanager/manage/campaigns?act={account_numeric}")


if __name__ == "__main__":
    main()
