"""
Google Tasks CLI -- lists, list, add, complete, delete.

Reuses the shared OAuth token via tools/auth.py (scope: tasks).
Requires the one-time reauth that grants the tasks scope (see tools/auth.py).

Usage (direct, or via `gog tasks <cmd>`):
    python tools/tasks/cli.py lists
    python tools/tasks/cli.py list [--tasklist @default] [--show-completed]
    python tools/tasks/cli.py add --title "Buy stock" [--notes "..."] [--due 2026-06-05T00:00:00Z] [--dry-run]
    python tools/tasks/cli.py complete <task_id> [--tasklist @default] [--dry-run]
    python tools/tasks/cli.py delete <task_id> [--tasklist @default] [--dry-run]

`@default` is the Tasks API alias for your primary task list (no lookup needed).
All mutating commands support --dry-run. Output: JSON to stdout. Errors to stderr, exit 1.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from auth import service  # noqa: E402


def cmd_lists(svc, args):
    items = svc.tasklists().list(maxResults=100).execute().get("items", [])
    return [{"id": t["id"], "title": t.get("title", "")} for t in items]


def cmd_list(svc, args):
    items = (
        svc.tasks()
        .list(
            tasklist=args.tasklist,
            showCompleted=args.show_completed,
            showHidden=args.show_completed,
            maxResults=100,
        )
        .execute()
        .get("items", [])
    )
    return [
        {
            "id": t["id"],
            "title": t.get("title", ""),
            "status": t.get("status"),
            "due": t.get("due"),
            "notes": t.get("notes", ""),
        }
        for t in items
    ]


def cmd_add(svc, args):
    body = {"title": args.title}
    if args.notes:
        body["notes"] = args.notes
    if args.due:
        body["due"] = args.due
    if args.dry_run:
        return {"dry_run": True, "action": "add", "tasklist": args.tasklist, "task": body}
    t = svc.tasks().insert(tasklist=args.tasklist, body=body).execute()
    return {"created": True, "id": t.get("id"), "title": t.get("title")}


def cmd_complete(svc, args):
    if args.dry_run:
        return {"dry_run": True, "action": "complete", "id": args.task_id, "tasklist": args.tasklist}
    t = svc.tasks().patch(tasklist=args.tasklist, task=args.task_id, body={"status": "completed"}).execute()
    return {"completed": True, "id": t.get("id"), "status": t.get("status")}


def cmd_delete(svc, args):
    if args.dry_run:
        return {"dry_run": True, "action": "delete", "id": args.task_id, "tasklist": args.tasklist}
    svc.tasks().delete(tasklist=args.tasklist, task=args.task_id).execute()
    return {"deleted": True, "id": args.task_id}


def build_parser():
    p = argparse.ArgumentParser(prog="gog tasks", description="Google Tasks CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("lists", help="show all task lists")
    s.set_defaults(func=cmd_lists)

    s = sub.add_parser("list", help="tasks in a list")
    s.add_argument("--tasklist", default="@default")
    s.add_argument("--show-completed", action="store_true")
    s.set_defaults(func=cmd_list)

    s = sub.add_parser("add", help="add a task")
    s.add_argument("--title", required=True)
    s.add_argument("--tasklist", default="@default")
    s.add_argument("--notes")
    s.add_argument("--due", help="RFC3339, e.g. 2026-06-05T00:00:00Z (date portion is used)")
    s.add_argument("--dry-run", action="store_true")
    s.set_defaults(func=cmd_add)

    s = sub.add_parser("complete", help="mark a task completed")
    s.add_argument("task_id")
    s.add_argument("--tasklist", default="@default")
    s.add_argument("--dry-run", action="store_true")
    s.set_defaults(func=cmd_complete)

    s = sub.add_parser("delete", help="delete a task")
    s.add_argument("task_id")
    s.add_argument("--tasklist", default="@default")
    s.add_argument("--dry-run", action="store_true")
    s.set_defaults(func=cmd_delete)

    return p


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    args = build_parser().parse_args(argv)
    try:
        result = args.func(service("tasks", "v1"), args)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
