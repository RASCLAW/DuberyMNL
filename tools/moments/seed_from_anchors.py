"""
Materialize upcoming fixed PH anchors (contents/calendar/anchors_ph.json) into
dated rows in the content_calendar Sheet. Purely deterministic (date math only) —
the AI researcher adds dynamic/trend moments and refines angles on top.

    python tools/moments/seed_from_anchors.py                  # DRY-RUN (default), 120-day horizon
    python tools/moments/seed_from_anchors.py --live           # actually write to the Sheet
    python tools/moments/seed_from_anchors.py --horizon-days 200 --live

Each anchor becomes a moment whose window is the next upcoming occurrence whose
END date is still in the future. Re-running is safe: upsert is keyed by id, so an
already-seeded moment is updated in place, not duplicated.
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from moment_store import upsert_moment

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

ANCHORS_FILE = Path(__file__).resolve().parent.parent.parent / "contents" / "calendar" / "anchors_ph.json"


def _mmdd(s: str):
    m, d = s.split("-")
    return int(m), int(d)


def next_window(start_mmdd: str, end_mmdd: str, today: date):
    """Next occurrence whose end >= today. Handles windows that cross year-end."""
    sm, sd = _mmdd(start_mmdd)
    em, ed = _mmdd(end_mmdd)
    for year in (today.year, today.year + 1):
        start = date(year, sm, sd)
        end_year = year if (em, ed) >= (sm, sd) else year + 1
        end = date(end_year, em, ed)
        if end >= today:
            return start, end
    return None


def main():
    parser = argparse.ArgumentParser(description="Seed upcoming PH anchors into the content calendar")
    parser.add_argument("--horizon-days", type=int, default=120,
                        help="Only seed anchors whose window starts within N days (default 120)")
    parser.add_argument("--live", action="store_true", help="Write to the Sheet (default is dry-run)")
    args = parser.parse_args()

    today = date.today()
    anchors = json.loads(ANCHORS_FILE.read_text(encoding="utf-8")).get("anchors", [])

    seeded, skipped = [], 0
    for a in anchors:
        win = next_window(a["window_start_mmdd"], a["window_end_mmdd"], today)
        if not win:
            skipped += 1
            continue
        start, end = win
        lead = (start - today).days
        if lead > args.horizon_days:
            skipped += 1
            continue

        moment = {
            "id": f"{start.isoformat()}-{a['slug']}",
            "title": a["title"],
            "type": a["type"],
            "window_start": start.isoformat(),
            "window_end": end.isoformat(),
            "relevance": a.get("relevance", ""),
            "angle": a.get("angle", ""),
            "format": a.get("format", ""),
            "source": "anchor",
            "status": "suggested",
            "notes": a.get("date_note", ""),
            "added": today.isoformat(),
            "lead_time_days": max(lead, 0),
        }
        result = upsert_moment(moment, dry_run=not args.live)
        seeded.append((result.get("action"), moment["id"], start.isoformat(), end.isoformat()))

    mode = "LIVE" if args.live else "DRY-RUN"
    print(f"[{mode}] horizon={args.horizon_days}d  today={today.isoformat()}")
    for action, mid, s, e in sorted(seeded, key=lambda x: x[2]):
        print(f"  {action:<7} {s} -> {e}  {mid}")
    print(f"\n{len(seeded)} anchor(s) in window, {skipped} outside horizon."
          + ("" if args.live else "  (dry-run - re-run with --live to write)"))


if __name__ == "__main__":
    main()
