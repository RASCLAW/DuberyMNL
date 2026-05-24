"""
Pull Meta Pixel stats — site-wide events, not just ad-attributed.

The Pixel 1513349880261420 lives on v3.duberymnl.com and fires
PageView / ViewContent / AddToCart / Purchase. This tool reports the
full event totals (anyone who hit the site, ads or organic), which is
what the CC Marketing tab's "Pixel events" section needs.

Note: requires ads_management or ads_read scope on the token, plus
business-asset access to the pixel. The same META_ADS_ACCESS_TOKEN
that pulls insights should already have this.

Writes .tmp/pixel_stats.json:
{
  "meta": {"pulled_at", "pixel_id", "days"},
  "events": {"PageView": N, "ViewContent": N, "AddToCart": N, "Purchase": N, ...}
}

Usage:
    python tools/meta_ads/pull_pixel_stats.py            # last 7 days
    python tools/meta_ads/pull_pixel_stats.py --days 14  # last 14 days
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_DIR / ".env")

TMP_DIR = PROJECT_DIR / ".tmp"
DEFAULT_OUT = TMP_DIR / "pixel_stats.json"

ACCESS_TOKEN = os.environ.get("META_ADS_ACCESS_TOKEN")
PIXEL_ID = os.environ.get("META_PIXEL_ID", "1513349880261420")
GRAPH_API_VERSION = "v21.0"
BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

PHT = timezone(timedelta(hours=8))


def main():
    parser = argparse.ArgumentParser(description="Pull Meta Pixel event totals")
    parser.add_argument("--days", type=int, default=7, help="Lookback window in days (default 7)")
    parser.add_argument("--output", type=str, help="Output path (default: .tmp/pixel_stats.json)")
    parser.add_argument("--quiet", action="store_true", help="Suppress non-error output")
    args = parser.parse_args()

    if not ACCESS_TOKEN:
        print("Error: META_ADS_ACCESS_TOKEN must be set in .env", file=sys.stderr)
        sys.exit(1)

    now = datetime.now(PHT)
    start_ts = int((now - timedelta(days=args.days)).timestamp())
    end_ts = int(now.timestamp())

    # Meta endpoint: GET /{pixel_id}/stats?aggregation=event&start_time=X&end_time=Y
    url = f"{BASE}/{PIXEL_ID}/stats"
    params = {
        "aggregation": "event",
        "start_time": start_ts,
        "end_time": end_ts,
        "access_token": ACCESS_TOKEN,
    }

    resp = requests.get(url, params=params, timeout=15)
    if not resp.ok:
        err = resp.json().get("error", {}) if resp.text else {}
        print(f"Pixel stats API error: {err.get('message', resp.text[:300])}", file=sys.stderr)
        sys.exit(1)

    payload = resp.json()

    # Response shape:
    # {"data": [{"start_time": "...", "aggregation": "event",
    #            "data": [{"value": "PageView", "count": 24}, ...]}, ...]}
    # Aggregate event counts across all hourly bins.
    events: dict[str, int] = {}
    for bin_row in payload.get("data", []):
        for ev in (bin_row.get("data") or []):
            ev_name = ev.get("value")
            try:
                count = int(ev.get("count", 0))
            except (TypeError, ValueError):
                continue
            if not ev_name:
                continue
            events[ev_name] = events.get(ev_name, 0) + count

    result = {
        "meta": {
            "pulled_at": now.isoformat(),
            "pixel_id": PIXEL_ID,
            "days": args.days,
            "start_time": start_ts,
            "end_time": end_ts,
        },
        "events": events,
    }

    out_path = Path(args.output) if args.output else DEFAULT_OUT
    out_path.parent.mkdir(exist_ok=True, parents=True)
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    if not args.quiet:
        print(f"Saved {len(events)} pixel events to {out_path}")
        for k, v in sorted(events.items(), key=lambda x: -x[1])[:10]:
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
