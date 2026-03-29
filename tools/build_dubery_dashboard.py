#!/usr/bin/env python3
"""
Build DuberyMNL Dashboard Data
Aggregates pipeline.json + ad_insights.json + ads_config.json into
.tmp/dubery-dashboard-data.json for the dashboard UI.
"""
import json
from pathlib import Path
from datetime import datetime
from collections import Counter

TMP = Path(__file__).resolve().parent.parent / ".tmp"
PIPELINE = TMP / "pipeline.json"
AD_INSIGHTS = TMP / "ad_insights.json"
ADS_CONFIG = TMP / "ads_config.json"
CAPTIONS = TMP / "captions.json"
OUTPUT = TMP / "dubery-dashboard-data.json"


def load_json(path):
    if path.exists():
        return json.loads(path.read_text())
    return None


def extract_action(actions, action_type):
    """Pull a specific action value from Meta's actions array."""
    if not actions:
        return 0
    for a in actions:
        if a.get("action_type") == action_type:
            return int(a["value"])
    return 0


def build_creative(pipeline):
    """Build creative tab data from pipeline."""
    statuses = Counter(item.get("status", "unknown") for item in pipeline)
    angles = Counter(item.get("angle", "Unknown") for item in pipeline if item.get("angle"))
    products = Counter(item.get("product_ref", "Unassigned") for item in pipeline if item.get("product_ref"))

    ratings = [item["rating"] for item in pipeline if item.get("rating")]
    avg_rating = round(sum(ratings) / len(ratings), 1) if ratings else 0

    approved_count = statuses.get("IMAGE_APPROVED", 0) + statuses.get("AD_STAGED", 0) + statuses.get("POSTED", 0)
    total = len(pipeline)
    approval_rate = round((approved_count / total) * 100) if total else 0

    # Queue: items with caption but no approved image yet
    queue = []
    for item in pipeline:
        if item.get("status") in ("PENDING", "PROMPT_READY"):
            queue.append({
                "id": item["id"],
                "angle": item.get("angle", ""),
                "vibe": item.get("vibe", ""),
                "hook_type": item.get("hook_type", ""),
                "product_ref": item.get("product_ref", ""),
                "has_caption": bool(item.get("caption_text", "").strip()),
                "has_prompt": bool(item.get("prompt", "").strip()),
                "caption_preview": (item.get("caption_text", "") or "")[:80],
            })

    # Approved: items with images ready
    approved = []
    for item in pipeline:
        if item.get("status") in ("IMAGE_APPROVED", "AD_STAGED", "POSTED"):
            approved.append({
                "id": item["id"],
                "angle": item.get("angle", ""),
                "vibe": item.get("vibe", ""),
                "product_ref": item.get("product_ref", ""),
                "rating": item.get("rating"),
                "image_url": item.get("image_url", ""),
                "drive_url": item.get("drive_url", ""),
                "caption_preview": (item.get("caption_text", "") or "")[:80],
                "has_ad": bool(item.get("ad_id")),
                "has_organic": item.get("organic_status") in ("SCHEDULED", "POSTED"),
                "generated": True,
            })

    return {
        "summary": {
            "total": total,
            "by_status": dict(statuses.most_common()),
            "approval_rate": approval_rate,
            "avg_rating": avg_rating,
            "angles": dict(angles.most_common()),
            "products": dict(products.most_common()),
        },
        "queue": queue,
        "approved": approved,
    }


def build_marketing(pipeline, insights, config):
    """Build marketing tab data from ad insights + pipeline."""
    ads_data = {"campaign": {}, "adsets": [], "top_creatives": [], "budget": {}}
    organic_data = {"scheduled": [], "posted": [], "total_scheduled": 0, "total_posted": 0}

    # Ad insights
    if insights:
        camp = insights.get("campaign", [{}])
        if camp:
            c = camp[0]
            ads_data["campaign"] = {
                "name": c.get("campaign_name", ""),
                "id": c.get("campaign_id", ""),
                "total_spend": float(c.get("spend", 0)),
                "impressions": int(c.get("impressions", 0)),
                "clicks": int(c.get("clicks", 0)),
                "ctr": round(float(c.get("ctr", 0)), 2),
                "cpc": round(float(c.get("cpc", 0)), 2),
                "cpm": round(float(c.get("cpm", 0)), 2),
                "link_clicks": extract_action(c.get("actions"), "link_click"),
                "landing_page_views": extract_action(c.get("actions"), "landing_page_view"),
                "post_reactions": extract_action(c.get("actions"), "post_reaction"),
                "date_range": {
                    "from": c.get("date_start", ""),
                    "to": c.get("date_stop", ""),
                },
            }

            total_spend = float(c.get("spend", 0))
            date_from = c.get("date_start", "")
            date_to = c.get("date_stop", "")
            if date_from and date_to:
                try:
                    days = (datetime.strptime(date_to, "%Y-%m-%d") - datetime.strptime(date_from, "%Y-%m-%d")).days + 1
                except ValueError:
                    days = 1
            else:
                days = 1

            daily_budget = 200
            if config and config.get("ad_sets"):
                ad_sets = config["ad_sets"]
                if isinstance(ad_sets, dict):
                    ad_sets = ad_sets.values()
                for adset in ad_sets:
                    if isinstance(adset, dict) and adset.get("daily_budget"):
                        daily_budget = adset["daily_budget"] / 100  # Meta stores in cents
                        break

            ads_data["budget"] = {
                "daily_budget": daily_budget,
                "total_spent": total_spend,
                "days_running": days,
                "avg_daily_spend": round(total_spend / days, 2) if days else 0,
            }

        # Ad sets
        for adset in insights.get("adsets", []):
            ads_data["adsets"].append({
                "id": adset.get("adset_id", ""),
                "name": adset.get("adset_name", ""),
                "spend": float(adset.get("spend", 0)),
                "impressions": int(adset.get("impressions", 0)),
                "clicks": int(adset.get("clicks", 0)),
                "ctr": round(float(adset.get("ctr", 0)), 2),
                "link_clicks": extract_action(adset.get("actions"), "link_click"),
                "landing_page_views": extract_action(adset.get("actions"), "landing_page_view"),
            })

        # Top creatives (sorted by CTR descending)
        ad_list = sorted(
            insights.get("ads", []),
            key=lambda x: float(x.get("ctr", 0)),
            reverse=True,
        )
        for ad in ad_list[:10]:
            # Parse caption ID from ad name: "DuberyMNL - 6" -> 6
            ad_name = ad.get("ad_name", "")
            caption_id = ad_name.split(" - ")[-1] if " - " in ad_name else ""

            # Find matching pipeline entry for image
            image_url = ""
            for item in pipeline:
                if str(item.get("id")) == caption_id:
                    image_url = item.get("image_url", "")
                    break

            ads_data["top_creatives"].append({
                "ad_id": ad.get("ad_id", ""),
                "ad_name": ad_name,
                "caption_id": caption_id,
                "spend": float(ad.get("spend", 0)),
                "ctr": round(float(ad.get("ctr", 0)), 2),
                "clicks": int(ad.get("clicks", 0)),
                "impressions": int(ad.get("impressions", 0)),
                "link_clicks": extract_action(ad.get("actions"), "link_click"),
                "landing_page_views": extract_action(ad.get("actions"), "landing_page_view"),
                "image_url": image_url,
            })

    # Organic posts
    for item in pipeline:
        org = item.get("organic_status")
        if org == "SCHEDULED":
            organic_data["scheduled"].append({
                "id": item["id"],
                "caption_preview": (item.get("caption_text", "") or "")[:80],
                "scheduled_time": item.get("fb_scheduled_time", ""),
            })
        elif org == "POSTED":
            organic_data["posted"].append({
                "id": item["id"],
                "caption_preview": (item.get("caption_text", "") or "")[:80],
                "post_id": item.get("fb_post_id", ""),
            })
    organic_data["total_scheduled"] = len(organic_data["scheduled"])
    organic_data["total_posted"] = len(organic_data["posted"])

    # Ready to distribute: approved but no ad and no organic post
    ready = []
    for item in pipeline:
        if item.get("status") in ("IMAGE_APPROVED",) and not item.get("ad_id") and item.get("organic_status") not in ("SCHEDULED", "POSTED"):
            ready.append({
                "id": item["id"],
                "product_ref": item.get("product_ref", ""),
                "rating": item.get("rating"),
                "image_url": item.get("image_url", ""),
                "caption_preview": (item.get("caption_text", "") or "")[:80],
                "has_ad": False,
                "has_organic": False,
            })

    return {
        "ads": ads_data,
        "organic": organic_data,
        "ready_to_distribute": ready,
    }


def build_crm():
    """Build CRM tab data (stub for now)."""
    return {
        "orders": [],
        "customers": [],
        "revenue": {"total": 0, "this_week": 0, "this_month": 0},
        "chatbot": {"status": "built", "deployed": False, "conversations_today": 0},
    }


def build_overview(pipeline, insights):
    """Build overview tab data."""
    statuses = Counter(item.get("status", "unknown") for item in pipeline)
    approved = statuses.get("IMAGE_APPROVED", 0) + statuses.get("AD_STAGED", 0) + statuses.get("POSTED", 0)
    pending = statuses.get("PENDING", 0) + statuses.get("PROMPT_READY", 0)
    ads_count = sum(1 for item in pipeline if item.get("ad_id"))
    organic_count = sum(1 for item in pipeline if item.get("organic_status") in ("SCHEDULED", "POSTED"))

    spend = 0
    lpv = 0
    if insights and insights.get("campaign"):
        c = insights["campaign"][0]
        spend = float(c.get("spend", 0))
        lpv = extract_action(c.get("actions"), "landing_page_view")

    return {
        "pipeline_health": {
            "wf1_caption": {"status": "active", "count": len(pipeline)},
            "wf2_image": {"status": "active", "approved": approved, "pending": pending},
            "wf3a_organic": {"status": "ready", "posted": organic_count},
            "wf3b_ads": {"status": "live", "ads_count": ads_count, "spend": spend},
            "wf4_chatbot": {"status": "built", "deployed": False},
        },
        "key_metrics": {
            "content_pieces": len(pipeline),
            "live_ads": ads_count,
            "total_spend": spend,
            "landing_page_views": lpv,
            "orders": 0,
        },
        "recent_activity": [],
    }


def main():
    pipeline = load_json(PIPELINE) or []
    insights = load_json(AD_INSIGHTS)
    config = load_json(ADS_CONFIG)

    sources = []
    if PIPELINE.exists():
        sources.append("pipeline.json")
    if AD_INSIGHTS.exists():
        sources.append("ad_insights.json")
    if ADS_CONFIG.exists():
        sources.append("ads_config.json")

    data = {
        "meta": {
            "built_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00"),
            "pipeline_count": len(pipeline),
            "source_files": sources,
        },
        "creative": build_creative(pipeline),
        "marketing": build_marketing(pipeline, insights, config),
        "crm": build_crm(),
        "overview": build_overview(pipeline, insights),
    }

    OUTPUT.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"Built: {OUTPUT}")
    print(f"  Pipeline: {len(pipeline)} items")
    print(f"  Queue: {len(data['creative']['queue'])} ready for generation")
    print(f"  Approved: {len(data['creative']['approved'])} with images")
    print(f"  Ready to distribute: {len(data['marketing']['ready_to_distribute'])}")
    if insights:
        print(f"  Ad spend: P{data['marketing']['ads']['campaign'].get('total_spend', 0):,.2f}")


if __name__ == "__main__":
    main()
