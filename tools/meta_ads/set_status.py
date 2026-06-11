"""
Set ACTIVE/PAUSED status on Meta campaigns / adsets / ads (the un-pause action).

The rest of meta_ads stages PAUSED ads and tells you to flip them on in Ads
Manager. This does the flip from the CLI. Mutates LIVE ads -> spends money, so:
  - DRY-RUN by default. Nothing is sent without --live.
  - Every live mutation is appended to .tmp/set_status.log.

The same /{object_id} POST with field `status` works for campaign, adset, or ad.

Usage:
    # dry-run (default) -- prints what WOULD change, sends nothing
    python tools/meta_ads/set_status.py --activate 6968215093276 --pause 52519154176080,52510655419880

    # actually apply
    python tools/meta_ads/set_status.py --activate 6968215093276 --pause 52519154176080,52510655419880 --live
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

ACCESS_TOKEN = os.environ.get("META_ADS_ACCESS_TOKEN")
BASE = "https://graph.facebook.com/v21.0"
PHT = timezone(timedelta(hours=8))
LOG = PROJECT_DIR / ".tmp" / "set_status.log"


def ids(s):
    return [x.strip() for x in s.split(",") if x.strip()] if s else []


def lookup(obj_id):
    """Read current name + status for a campaign/adset/ad id (read-only)."""
    r = requests.get(f"{BASE}/{obj_id}", params={
        "fields": "name,status,effective_status",
        "access_token": ACCESS_TOKEN,
    }, timeout=20)
    if not r.ok:
        return {"name": "(lookup failed)", "status": "?", "effective_status": "?"}
    return r.json()


def set_status(obj_id, status):
    r = requests.post(f"{BASE}/{obj_id}", data={
        "status": status,
        "access_token": ACCESS_TOKEN,
    }, timeout=20)
    ok = r.ok and r.json().get("success", True)
    return ok, (r.json() if r.text else {})


def main():
    p = argparse.ArgumentParser(description="Set ACTIVE/PAUSED on Meta objects")
    p.add_argument("--activate", type=str, help="Comma-separated ids to set ACTIVE")
    p.add_argument("--pause", type=str, help="Comma-separated ids to set PAUSED")
    p.add_argument("--live", action="store_true", help="Actually apply (default: dry-run)")
    args = p.parse_args()

    if not ACCESS_TOKEN:
        print("Error: META_ADS_ACCESS_TOKEN must be set in .env", file=sys.stderr)
        sys.exit(1)

    ops = [(i, "ACTIVE") for i in ids(args.activate)] + [(i, "PAUSED") for i in ids(args.pause)]
    if not ops:
        print("Nothing to do. Pass --activate and/or --pause with ids.", file=sys.stderr)
        sys.exit(1)

    mode = "LIVE" if args.live else "DRY-RUN"
    print(f"=== set_status [{mode}] ===\n")
    for obj_id, target in ops:
        cur = lookup(obj_id)
        arrow = f"{cur.get('status','?')} -> {target}"
        print(f"  {obj_id}  {cur.get('name','?')[:48]!r}")
        print(f"      effective={cur.get('effective_status','?')}   change: {arrow}")
        if cur.get("status") == target:
            print("      (already in target state -- will skip)")
        print()

    if not args.live:
        print("DRY-RUN: no changes sent. Re-run with --live to apply.")
        return

    LOG.parent.mkdir(exist_ok=True, parents=True)
    stamp = datetime.now(PHT).isoformat()
    results = []
    for obj_id, target in ops:
        cur = lookup(obj_id)
        if cur.get("status") == target:
            results.append((obj_id, target, "skipped (already set)"))
            continue
        ok, resp = set_status(obj_id, target)
        outcome = "OK" if ok else f"FAILED: {resp.get('error', {}).get('message', resp)}"
        results.append((obj_id, target, outcome))
        with LOG.open("a", encoding="utf-8") as f:
            f.write(f"{stamp}\t{obj_id}\t{cur.get('name','?')}\t{cur.get('status')}->{target}\t{outcome}\n")

    print("=== RESULTS ===")
    for obj_id, target, outcome in results:
        print(f"  {obj_id} -> {target}: {outcome}")
    print(f"\nLogged to {LOG}")
    if any("FAILED" in o for _, _, o in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
