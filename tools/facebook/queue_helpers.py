"""
Feed queue helpers for the DuberyMNL FB Page scheduler.

Backing store: tools/facebook/feed_queue.json (gitignored).
File locked via fcntl (POSIX) or msvcrt (Windows). Atomic write via tmp+replace.
Auto-creates an empty queue file if missing.
"""

import json
import os
import sys
from pathlib import Path

try:
    import fcntl
except ImportError:
    fcntl = None
    import msvcrt

PROJECT_DIR = Path(__file__).parent.parent.parent
QUEUE_FILE = PROJECT_DIR / "tools" / "facebook" / "feed_queue.json"
QUEUE_LOCK = QUEUE_FILE.with_suffix(".json.lock")
QUEUE_TMP = QUEUE_FILE.with_suffix(".json.tmp")
QUEUE_BAK = QUEUE_FILE.with_suffix(".json.bak")


def _ensure_queue_file():
    if not QUEUE_FILE.exists():
        QUEUE_FILE.write_text("[]", encoding="utf-8")


def _lock(lf):
    if fcntl:
        fcntl.flock(lf, fcntl.LOCK_EX)
    else:
        msvcrt.locking(lf.fileno(), msvcrt.LK_LOCK, 1)


def _unlock(lf):
    if fcntl:
        fcntl.flock(lf, fcntl.LOCK_UN)
    else:
        msvcrt.locking(lf.fileno(), msvcrt.LK_UNLCK, 1)


def load_queue() -> list:
    """Read the queue. Auto-creates empty file if missing."""
    _ensure_queue_file()
    try:
        return json.loads(QUEUE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"queue_helpers: corrupted queue file ({exc}); refusing to read", file=sys.stderr)
        raise


def save_queue(items: list) -> None:
    """Atomic write: tmp → replace, with .bak of previous contents."""
    _ensure_queue_file()
    payload = json.dumps(items, indent=2, ensure_ascii=False)
    with open(QUEUE_LOCK, "w", encoding="utf-8") as lf:
        _lock(lf)
        try:
            if QUEUE_FILE.exists():
                QUEUE_BAK.write_text(QUEUE_FILE.read_text(encoding="utf-8"), encoding="utf-8")
            QUEUE_TMP.write_text(payload, encoding="utf-8")
            os.replace(QUEUE_TMP, QUEUE_FILE)
        finally:
            _unlock(lf)


def add_item(item: dict) -> str:
    """Append item to queue. Returns item id."""
    items = load_queue()
    items.append(item)
    save_queue(items)
    return item.get("id", "")


def update_item(item_id: str, fields: dict) -> None:
    """Patch an item's fields in place."""
    items = load_queue()
    for it in items:
        if it.get("id") == item_id:
            it.update(fields)
            break
    else:
        raise KeyError(f"queue item not found: {item_id}")
    save_queue(items)


if __name__ == "__main__":
    print(load_queue())
