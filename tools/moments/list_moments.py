"""
Read the content_calendar Sheet and print upcoming moments.

    python tools/moments/list_moments.py                      # all, sorted by window_start
    python tools/moments/list_moments.py --status suggested   # filter by status
    python tools/moments/list_moments.py --type holiday       # filter by type
    python tools/moments/list_moments.py --upcoming-days 60    # window active within 60 days
    python tools/moments/list_moments.py --json                # raw JSON for piping

Used by the daily digest and for debugging.
"""

import argparse
import json
import sys
from datetime import date, timedelta

from moment_store import read_moments

# Angles/titles can contain em-dashes and Tagalog text; force UTF-8 so headless
# runs (digest, cron) don't crash on a cp1252 console.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass


def _d(s: str):
    try:
        return date.fromisoformat((s or "").strip())
    except ValueError:
        return None


def main():
    parser = argparse.ArgumentParser(description="List content-calendar moments")
    parser.add_argument("--status", help="Filter by status (e.g. suggested, approved)")
    parser.add_argument("--type", dest="mtype", help="Filter by type (holiday/event/trend/weather)")
    parser.add_argument("--upcoming-days", type=int, help="Only moments whose window is active within N days")
    parser.add_argument("--json", action="store_true", help="Emit raw JSON")
    args = parser.parse_args()

    rows = read_moments()

    if args.status:
        rows = [r for r in rows if (r.get("status") or "").lower() == args.status.lower()]
    if args.mtype:
        rows = [r for r in rows if (r.get("type") or "").lower() == args.mtype.lower()]
    if args.upcoming_days is not None:
        today = date.today()
        horizon = today + timedelta(days=args.upcoming_days)
        kept = []
        for r in rows:
            start, end = _d(r.get("window_start")), _d(r.get("window_end"))
            # active = ends in the future and starts on/before the horizon
            if (end or start or today) >= today and (start or today) <= horizon:
                kept.append(r)
        rows = kept

    rows.sort(key=lambda r: (r.get("window_start") or "9999"))

    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        return

    if not rows:
        print("(no moments match)")
        return

    print(f"{'WINDOW':<25} {'TYPE':<9} {'REL':<4} {'STATUS':<10} TITLE / ANGLE")
    print("-" * 92)
    for r in rows:
        window = f"{r.get('window_start','?')} -> {r.get('window_end','?')}"
        title = r.get("title", "")
        angle = (r.get("angle", "") or "")[:46]
        print(f"{window:<25} {r.get('type',''):<9} {str(r.get('relevance','')):<4} "
              f"{r.get('status',''):<10} {title} — {angle}")
    print(f"\n{len(rows)} moment(s).")


if __name__ == "__main__":
    main()
