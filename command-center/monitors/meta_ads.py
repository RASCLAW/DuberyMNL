"""Meta Ads service monitor -- checks for any ACTIVE adsets via Graph API.

Marked EXPENSIVE so the Monitoring tab only polls on demand / slow interval.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from monitors import ServiceStatus  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

EXPENSIVE = True
GRAPH_API_VERSION = "v21.0"
TIMEOUT_SEC = 6


def check() -> ServiceStatus:
    ad_account_id = os.getenv("META_AD_ACCOUNT_ID", "").strip()
    token = (
        os.getenv("META_PAGE_ACCESS_TOKEN", "").strip()
        or os.getenv("META_ACCESS_TOKEN", "").strip()
    )

    if not ad_account_id or not token:
        return ServiceStatus.now(
            "meta_ads", "not_wired", "META credentials missing"
        )

    # Normalize: strip any existing "act_" prefix then re-add.
    if ad_account_id.startswith("act_"):
        ad_account_id = ad_account_id[len("act_"):]
    account_path = f"act_{ad_account_id}"

    url = (
        f"https://graph.facebook.com/{GRAPH_API_VERSION}/{account_path}/adsets"
    )
    params = {
        "effective_status": '["ACTIVE"]',
        "fields": "id,name,status",
        "limit": 5,
        "access_token": token,
    }

    try:
        resp = requests.get(url, params=params, timeout=TIMEOUT_SEC)
        if not resp.ok:
            return ServiceStatus.now(
                "meta_ads", "offline", f"HTTP {resp.status_code}: {resp.text[:120]}"
            )
        payload = resp.json()
        entries = payload.get("data") or []
        if len(entries) >= 1:
            return ServiceStatus.now(
                "meta_ads", "active", f"{len(entries)} active adsets"
            )
        return ServiceStatus.now(
            "meta_ads", "offline", "no active adsets (ads paused)"
        )
    except Exception as exc:
        return ServiceStatus.now(
            "meta_ads", "offline", f"{type(exc).__name__}: {exc}"
        )


if __name__ == "__main__":
    print(check())
