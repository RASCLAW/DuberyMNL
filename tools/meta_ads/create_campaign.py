"""
Create a full PAUSED Meta Ads campaign: campaign → ad set → ad creative → ad.

Usage:
    python create_campaign.py \
      --name "DuberyMNL - Commuter - 20260309" \
      --caption "Your caption text here" \
      --image-hash "abc123def456" \
      --ad-account-id "act_XXXXXXXXX" \
      --page-id "123456789"

Output: JSON with campaign_id, ad_set_id, ad_id.
"""

import argparse
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

META_ADS_ACCESS_TOKEN = os.environ.get("META_ADS_ACCESS_TOKEN")
META_PAGE_ID = os.environ.get("META_PAGE_ID")
GRAPH_API_VERSION = "v21.0"
BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

# Default targeting: Philippines, 18-45, sunglasses/fashion/motorcycle interests
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

DEFAULT_DAILY_BUDGET = 20000  # in centavos (₱200)


def api_post(endpoint: str, payload: dict) -> dict:
    url = f"{BASE}/{endpoint}"
    payload["access_token"] = META_ADS_ACCESS_TOKEN
    response = requests.post(url, json=payload)
    if not response.ok:
        raise RuntimeError(f"API error {response.status_code}: {response.text}")
    return response.json()


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


def create_ad_set(ad_account_id: str, campaign_id: str, name: str) -> str:
    data = api_post(
        f"{ad_account_id}/adsets",
        {
            "name": name,
            "campaign_id": campaign_id,
            "billing_event": "IMPRESSIONS",
            "optimization_goal": "LINK_CLICKS",
            "daily_budget": DEFAULT_DAILY_BUDGET,
            "targeting": DEFAULT_TARGETING,
            "status": "PAUSED",
            "destination_type": "FACEBOOK",
        },
    )
    return data["id"]


def create_ad_creative(ad_account_id: str, page_id: str, name: str, caption: str, image_hash: str) -> str:
    data = api_post(
        f"{ad_account_id}/adcreatives",
        {
            "name": name,
            "object_story_spec": {
                "page_id": page_id,
                "link_data": {
                    "message": caption,
                    "link": f"https://www.facebook.com/{page_id}",
                    "image_hash": image_hash,
                    "call_to_action": {
                        "type": "SHOP_NOW",
                        "value": {"link": f"https://www.facebook.com/{page_id}"},
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


def main():
    if not META_ADS_ACCESS_TOKEN:
        print("Error: META_ADS_ACCESS_TOKEN not set in .env", file=sys.stderr)
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Create a PAUSED Meta Ads campaign")
    parser.add_argument("--name", required=True, help="Campaign name")
    parser.add_argument("--caption", required=True, help="Ad primary text (caption)")
    parser.add_argument("--image-hash", required=True, help="Image hash from upload_creative.py")
    parser.add_argument("--ad-account-id", required=True, help="Meta Ad Account ID")
    parser.add_argument("--page-id", default=META_PAGE_ID, help="Facebook Page ID")
    args = parser.parse_args()

    if not args.page_id:
        print("Error: --page-id required or set META_PAGE_ID in .env", file=sys.stderr)
        sys.exit(1)

    print(f"Creating campaign: {args.name}", file=sys.stderr)
    campaign_id = create_campaign(args.ad_account_id, args.name)

    print(f"Creating ad set...", file=sys.stderr)
    ad_set_id = create_ad_set(args.ad_account_id, campaign_id, f"{args.name} - Ad Set")

    print(f"Creating ad creative...", file=sys.stderr)
    creative_id = create_ad_creative(
        args.ad_account_id, args.page_id, f"{args.name} - Creative", args.caption, args.image_hash
    )

    print(f"Creating ad...", file=sys.stderr)
    ad_id = create_ad(args.ad_account_id, ad_set_id, creative_id, f"{args.name} - Ad")

    output = {
        "success": True,
        "campaign_id": campaign_id,
        "ad_set_id": ad_set_id,
        "creative_id": creative_id,
        "ad_id": ad_id,
        "status": "PAUSED",
        "ads_manager_url": f"https://www.facebook.com/adsmanager/manage/campaigns?act={args.ad_account_id.replace('act_', '')}",
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
