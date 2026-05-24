"""
Pull Microsoft Clarity metrics for DuberyMNL via the Data Export API.

Saves the full payload to .tmp/clarity_metrics.json and prints a console summary.

Limits: 10 API calls per project per day. Each call returns up to 3 days, with
up to 3 dimensions. This script uses 3 calls by default:
  1) totals (no dimensions) -- topline metrics
  2) by URL  -- which pages cause friction
  3) by Device -- mobile vs desktop split

Usage:
    python tools/clarity/pull_metrics.py
    python tools/clarity/pull_metrics.py --days 1
    python tools/clarity/pull_metrics.py --dim Device OS Browser
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
TMP_DIR.mkdir(exist_ok=True)
OUT_FILE = TMP_DIR / "clarity_metrics.json"

TOKEN = os.environ.get("CLARITY_API_TOKEN")
ENDPOINT = "https://www.clarity.ms/export-data/api/v1/project-live-insights"
PHT = timezone(timedelta(hours=8))


def call(num_days: int, dimensions: list[str]) -> list[dict]:
    """One Clarity API call. dimensions can be 0..3 items."""
    params = {"numOfDays": num_days}
    for i, d in enumerate(dimensions, 1):
        params[f"dimension{i}"] = d
    headers = {"Authorization": f"Bearer {TOKEN}"}
    r = requests.get(ENDPOINT, params=params, headers=headers, timeout=30)
    if r.status_code == 429:
        print("API quota hit (10 calls/day). Try again tomorrow or skip dimensions.", file=sys.stderr)
        sys.exit(2)
    if not r.ok:
        print(f"Clarity API error {r.status_code}: {r.text[:400]}", file=sys.stderr)
        sys.exit(1)
    return r.json()


def _normalize_url(url: str) -> str:
    """Strip query string so /products/?fbclid=... and /products/?utm=... fold together."""
    if not url:
        return "(unknown)"
    return url.split("?", 1)[0].rstrip("/") or "/"


def summarize_friction_by_url(rows: list[dict], metric_name: str, limit: int = 5):
    """Group url-keyed rows by path, sum sessions, show top offenders."""
    for row in rows:
        if row.get("metricName") != metric_name:
            continue
        info = row.get("information") or []
        bucket: dict[str, int] = {}
        for item in info:
            url = _normalize_url(item.get("Url", ""))
            sess = int(item.get("sessionsCount", 0) or 0)
            bucket[url] = bucket.get(url, 0) + sess
        if not bucket:
            print(f"   (none)")
            return
        for url, sess in sorted(bucket.items(), key=lambda x: -x[1])[:limit]:
            print(f"   {sess:>4} sess  {url}")
        return
    print(f"   (no data for {metric_name})")


def summarize_metric_simple(rows: list[dict], metric_name: str, key_field: str, value_field: str = "sessionsCount", limit: int = 5):
    """Print a flat breakdown sorted by sessions."""
    for row in rows:
        if row.get("metricName") != metric_name:
            continue
        info = row.get("information") or []
        sortable = []
        for item in info:
            key = item.get(key_field, "(none)")
            val = float(item.get(value_field, 0) or 0)
            sortable.append((key, val, item))
        sortable.sort(key=lambda x: -x[1])
        for k, v, raw in sortable[:limit]:
            print(f"   {int(v):>4}  {k}  {raw}")
        return
    print(f"   (no data for {metric_name})")


def main():
    if not TOKEN:
        print("CLARITY_API_TOKEN missing from .env", file=sys.stderr)
        sys.exit(1)

    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=3, choices=[1, 2, 3])
    ap.add_argument("--dim", nargs="*", default=None, help="Override dimensions for a single ad-hoc call")
    args = ap.parse_args()

    pulled_at = datetime.now(PHT).isoformat()
    out = {"pulled_at": pulled_at, "days": args.days, "calls": {}}

    if args.dim is not None:
        # Single ad-hoc call mode
        print(f"Pulling Clarity (days={args.days}, dims={args.dim})...")
        out["calls"]["adhoc"] = call(args.days, args.dim)
    else:
        # Standard 3-call sweep
        print(f"Pulling Clarity (days={args.days})...")
        print("  [1/3] totals (no dimensions)")
        out["calls"]["totals"] = call(args.days, [])
        print("  [2/3] by URL")
        out["calls"]["by_url"] = call(args.days, ["URL"])
        print("  [3/3] by Device")
        out["calls"]["by_device"] = call(args.days, ["Device"])

    OUT_FILE.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nSaved: {OUT_FILE}")

    # Console summary -- friendlier than raw JSON
    print("\n" + "=" * 60)
    print(f"CLARITY SUMMARY (last {args.days}d, pulled {pulled_at[:19]})")
    print("=" * 60)

    if "totals" in out["calls"]:
        rows = out["calls"]["totals"]
        print("\nTopline:")
        for row in rows:
            name = row.get("metricName", "?")
            info = row.get("information") or []
            if not info:
                continue
            # Single-value metrics: just dump the dict
            if len(info) == 1 and not any(isinstance(v, (dict, list)) for v in info[0].values()):
                print(f"  {name}: {info[0]}")
            else:
                print(f"  {name}: ({len(info)} entries)")

    if "by_url" in out["calls"]:
        rows = out["calls"]["by_url"]
        print("\nTraffic by URL path (top 8):")
        # Use any sessions-bearing metric -- Traffic if present, else fall through.
        summarize_friction_by_url(rows, "Traffic", limit=8) if any(r.get("metricName")=="Traffic" for r in rows) else summarize_friction_by_url(rows, "RageClickCount", limit=8)
        print("\nFriction by URL path (top 5 per metric):")
        for metric in ("QuickbackClick", "DeadClickCount", "RageClickCount", "ScriptErrorCount"):
            print(f"\n  {metric}:")
            summarize_friction_by_url(rows, metric, limit=5)

    if "by_device" in out["calls"]:
        rows = out["calls"]["by_device"]
        print("\nBy Device:")
        for metric in ("Traffic", "EngagedSessions", "ScrollDepth"):
            print(f"\n  {metric}:")
            summarize_metric_simple(rows, metric, key_field="Device", limit=5)


if __name__ == "__main__":
    main()
