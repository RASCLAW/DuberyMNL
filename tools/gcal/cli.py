"""
Google Calendar CLI -- agenda, list, create, edit, delete, quick-add.

Reuses the shared OAuth token via tools/auth.py (scope: calendar = full r/w).
NOTE: this lives in tools/gcal/ (not tools/calendar/) on purpose -- a top-level
package named `calendar` would shadow Python's stdlib calendar module once the
gog dispatcher imports it by name, breaking email/httplib2 internals.

Usage (direct, or via `gog cal <cmd>`):
    python tools/gcal/cli.py agenda --days 7
    python tools/gcal/cli.py list --max 10
    python tools/gcal/cli.py create --summary "Call" --start 2026-06-01T14:00:00+08:00 --end 2026-06-01T15:00:00+08:00 [--dry-run]
    python tools/gcal/cli.py create --summary "Holiday" --start 2026-06-12 --end 2026-06-13   # all-day (no T)
    python tools/gcal/cli.py edit <event_id> --summary "New title" [--dry-run]
    python tools/gcal/cli.py delete <event_id> [--dry-run]
    python tools/gcal/cli.py quickadd "Lunch with Sam tomorrow 1pm" [--dry-run]

Timed events: pass RFC3339 with a UTC offset (e.g. +08:00). A bare YYYY-MM-DD is
treated as an all-day date. All mutating commands support --dry-run.
Output: JSON to stdout. Errors to stderr, exit 1.
"""

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from auth import service  # noqa: E402


def _fmt(e):
    start = e.get("start", {})
    end = e.get("end", {})
    return {
        "id": e.get("id"),
        "summary": e.get("summary", ""),
        "start": start.get("dateTime") or start.get("date"),
        "end": end.get("dateTime") or end.get("date"),
        "location": e.get("location", ""),
        "description": e.get("description", ""),
    }


def _timepoint(value):
    """YYYY-MM-DD -> all-day date; anything with 'T' -> dateTime."""
    return {"date": value} if "T" not in value else {"dateTime": value}


def cmd_agenda(svc, args):
    now = datetime.now(timezone.utc)
    resp = (
        svc.events()
        .list(
            calendarId=args.cal,
            timeMin=now.isoformat(),
            timeMax=(now + timedelta(days=args.days)).isoformat(),
            singleEvents=True,
            orderBy="startTime",
            maxResults=2500,
        )
        .execute()
    )
    return [_fmt(e) for e in resp.get("items", [])]


def cmd_list(svc, args):
    resp = (
        svc.events()
        .list(
            calendarId=args.cal,
            timeMin=datetime.now(timezone.utc).isoformat(),
            singleEvents=True,
            orderBy="startTime",
            maxResults=args.max,
        )
        .execute()
    )
    return [_fmt(e) for e in resp.get("items", [])]


def cmd_create(svc, args):
    body = {"summary": args.summary, "start": _timepoint(args.start), "end": _timepoint(args.end)}
    if args.desc:
        body["description"] = args.desc
    if args.dry_run:
        return {"dry_run": True, "action": "create", "cal": args.cal, "event": body}
    e = svc.events().insert(calendarId=args.cal, body=body).execute()
    return {"created": True, "id": e.get("id"), "htmlLink": e.get("htmlLink")}


def cmd_edit(svc, args):
    patch = {}
    if args.summary is not None:
        patch["summary"] = args.summary
    if args.desc is not None:
        patch["description"] = args.desc
    if args.start:
        patch["start"] = _timepoint(args.start)
    if args.end:
        patch["end"] = _timepoint(args.end)
    if not patch:
        raise ValueError("edit requires at least one of --summary/--desc/--start/--end")
    if args.dry_run:
        return {"dry_run": True, "action": "edit", "id": args.event_id, "patch": patch}
    e = svc.events().patch(calendarId=args.cal, eventId=args.event_id, body=patch).execute()
    return {"updated": True, "id": e.get("id")}


def cmd_delete(svc, args):
    if args.dry_run:
        return {"dry_run": True, "action": "delete", "id": args.event_id, "cal": args.cal}
    svc.events().delete(calendarId=args.cal, eventId=args.event_id).execute()
    return {"deleted": True, "id": args.event_id}


def cmd_quickadd(svc, args):
    if args.dry_run:
        return {"dry_run": True, "action": "quickadd", "text": args.text, "cal": args.cal}
    e = svc.events().quickAdd(calendarId=args.cal, text=args.text).execute()
    return {"created": True, "id": e.get("id"), "summary": e.get("summary"), "htmlLink": e.get("htmlLink")}


def build_parser():
    p = argparse.ArgumentParser(prog="gog cal", description="Google Calendar CLI")
    p.add_argument("--cal", default="primary", help="calendar id (default: primary)")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("agenda", help="events in the next N days")
    s.add_argument("--days", type=int, default=7)
    s.set_defaults(func=cmd_agenda)

    s = sub.add_parser("list", help="next N upcoming events")
    s.add_argument("--max", type=int, default=10)
    s.set_defaults(func=cmd_list)

    s = sub.add_parser("create", help="create an event")
    s.add_argument("--summary", required=True)
    s.add_argument("--start", required=True, help="RFC3339 dateTime w/ offset, or YYYY-MM-DD for all-day")
    s.add_argument("--end", required=True)
    s.add_argument("--desc")
    s.add_argument("--dry-run", action="store_true")
    s.set_defaults(func=cmd_create)

    s = sub.add_parser("edit", help="patch an event")
    s.add_argument("event_id")
    s.add_argument("--summary")
    s.add_argument("--start")
    s.add_argument("--end")
    s.add_argument("--desc")
    s.add_argument("--dry-run", action="store_true")
    s.set_defaults(func=cmd_edit)

    s = sub.add_parser("delete", help="delete an event")
    s.add_argument("event_id")
    s.add_argument("--dry-run", action="store_true")
    s.set_defaults(func=cmd_delete)

    s = sub.add_parser("quickadd", help="natural-language event")
    s.add_argument("text")
    s.add_argument("--dry-run", action="store_true")
    s.set_defaults(func=cmd_quickadd)

    return p


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    args = build_parser().parse_args(argv)
    try:
        result = args.func(service("calendar", "v3"), args)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
