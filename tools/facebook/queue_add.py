"""
CLI to append a feed-post item to the queue.

Examples:
    python tools/facebook/queue_add.py --images contents/ready/brand/foo.png \
        --caption "Polarized for the view." --time "2026-05-22 19:00"

    python tools/facebook/queue_add.py --images a.png b.png --mode collage --layout 2h \
        --caption "Before / After" --time "2026-05-22 19:00"
"""

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from queue_helpers import add_item, load_queue  # noqa: E402

PROJECT_DIR = Path(__file__).parent.parent.parent
PHT = timezone(timedelta(hours=8))

VALID_MODES = ("multi", "collage")
VALID_LAYOUTS = ("2h", "2v", "1p2", "2x2", "3h", "hero3", "ba")
VALID_SOURCES = ("manual", "bank", "cli")

LAYOUT_IMAGE_COUNT = {
    "2h": 2,
    "2v": 2,
    "1p2": 3,
    "2x2": 4,
    "3h": 3,
    "hero3": 4,
    "ba": 2,
}


def parse_time(text: str) -> datetime:
    dt = datetime.strptime(text, "%Y-%m-%d %H:%M")
    return dt.replace(tzinfo=PHT)


def resolve_image(p: str) -> Path:
    path = Path(p)
    if not path.is_absolute():
        path = (PROJECT_DIR / path).resolve()
    return path


def make_id(scheduled: datetime) -> str:
    stem = scheduled.strftime("feed-%Y%m%d-%H%M")
    items = load_queue()
    existing = [it.get("id", "") for it in items if it.get("id", "").startswith(stem)]
    seq = len(existing) + 1
    return f"{stem}-{seq:03d}"


def main():
    p = argparse.ArgumentParser(description="Queue a FB feed post.")
    p.add_argument("--images", nargs="+", required=True, help="1-10 image paths (relative to project root or absolute)")
    p.add_argument("--caption", required=True)
    p.add_argument("--time", required=True, help='Scheduled time in PHT, "YYYY-MM-DD HH:MM"')
    p.add_argument("--mode", choices=VALID_MODES, default="multi")
    p.add_argument("--layout", choices=VALID_LAYOUTS, default=None)
    p.add_argument("--source", choices=VALID_SOURCES, default="cli")
    args = p.parse_args()

    if not args.caption.strip():
        print("error: caption is empty", file=sys.stderr)
        sys.exit(2)

    if not (1 <= len(args.images) <= 10):
        print(f"error: must supply 1-10 images, got {len(args.images)}", file=sys.stderr)
        sys.exit(2)

    resolved = []
    for img in args.images:
        path = resolve_image(img)
        if not path.exists():
            print(f"error: image not found: {img} (resolved {path})", file=sys.stderr)
            sys.exit(2)
        rel = path.relative_to(PROJECT_DIR) if path.is_relative_to(PROJECT_DIR) else path
        resolved.append(str(rel).replace("\\", "/"))

    try:
        scheduled = parse_time(args.time)
    except ValueError as exc:
        print(f"error: bad --time format ({exc}); expected YYYY-MM-DD HH:MM", file=sys.stderr)
        sys.exit(2)

    if scheduled <= datetime.now(PHT):
        print(f"error: --time must be in the future PHT (got {scheduled.isoformat()})", file=sys.stderr)
        sys.exit(2)

    if args.mode == "collage":
        if not args.layout:
            print("error: --layout is required when --mode=collage", file=sys.stderr)
            sys.exit(2)
        expected = LAYOUT_IMAGE_COUNT[args.layout]
        if len(resolved) != expected:
            print(f"error: layout {args.layout} expects {expected} images, got {len(resolved)}", file=sys.stderr)
            sys.exit(2)
    else:
        if args.layout:
            print("error: --layout only applies when --mode=collage", file=sys.stderr)
            sys.exit(2)

    item = {
        "id": make_id(scheduled),
        "image_paths": resolved,
        "caption": args.caption,
        "scheduled_for": scheduled.isoformat(),
        "mode": args.mode,
        "layout": args.layout,
        "composed_path": None,
        "status": "APPROVED",
        "fb_post_id": None,
        "fb_scheduled_post_id": None,
        "handoff_attempted_at": None,
        "handoff_error": None,
        "handoff_attempts": 0,
        "added_at": datetime.now(PHT).isoformat(),
        "posted_at": None,
        "error": None,
        "source": args.source,
    }

    new_id = add_item(item)

    # Meta-native handoff (CLI parity with /api/schedule/add).
    handed_off = False
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from tools.facebook.scheduled_handoff import handoff_to_meta, eligible_for_handoff
        from tools.facebook.queue_helpers import update_item
        now = datetime.now(PHT)
        if eligible_for_handoff(item, now):
            ok, result = handoff_to_meta(item)
            patch = {"handoff_attempted_at": now.isoformat(), "handoff_attempts": 1}
            if ok:
                patch["status"] = "SCHEDULED_AT_META"
                patch["fb_scheduled_post_id"] = result
                if item.get("composed_path"):
                    patch["composed_path"] = item["composed_path"]
                handed_off = True
            else:
                patch["handoff_error"] = result
            update_item(new_id, patch)
    except Exception as exc:
        print(f"warning: handoff attempt errored: {type(exc).__name__}: {exc}", file=sys.stderr)

    print(f"{new_id} handed_off={str(handed_off).lower()}")


if __name__ == "__main__":
    main()
