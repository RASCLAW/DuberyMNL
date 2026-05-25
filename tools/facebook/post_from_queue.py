"""
Worker that posts due items from the feed queue to the DuberyMNL FB Page.

Runs hourly via Windows Task Scheduler (task name: DuberyMNL_FeedScheduler).

Usage:
    python tools/facebook/post_from_queue.py             -- live mode (fires posts)
    python tools/facebook/post_from_queue.py --dry-run   -- prints due items, exits 0
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))
from queue_helpers import load_queue, update_item  # noqa: E402

PROJECT_DIR = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_DIR / ".env")

sys.path.insert(0, str(PROJECT_DIR))
from tools.image_ops.compose import compose as compose_collage  # noqa: E402
from tools.facebook.scheduled_handoff import (  # noqa: E402
    handoff_to_meta, verify_published, eligible_for_handoff,
)

TMP_DIR = PROJECT_DIR / ".tmp"
LAST_RUN_FILE = TMP_DIR / "feed_worker_last_run.json"

META_PAGE_ACCESS_TOKEN = os.environ.get("META_PAGE_ACCESS_TOKEN")
META_PAGE_ID = os.environ.get("META_PAGE_ID")
GRAPH_API_VERSION = "v25.0"
BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")

PHT = timezone(timedelta(hours=8))


def now_iso() -> str:
    return datetime.now(PHT).isoformat()


def parse_iso(text: str) -> datetime:
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=PHT)
    return dt


def due_items(items: list) -> list:
    """APPROVED items past their scheduled_for -- the last-resort local publish path."""
    now = datetime.now(PHT)
    return [it for it in items if it.get("status") == "APPROVED" and parse_iso(it["scheduled_for"]) <= now]


def handoff_pending_items(items: list) -> list:
    """APPROVED items that are eligible for Meta-native handoff (Task 9)."""
    now = datetime.now(PHT)
    return [it for it in items if eligible_for_handoff(it, now)]


def verify_pending_items(items: list) -> list:
    """SCHEDULED_AT_META items whose scheduled_for + 5min has passed (Task 9).

    The 5-minute buffer lets Meta finish its own internal fire+ingest before
    we ask 'is_published?'.
    """
    now = datetime.now(PHT)
    out = []
    for it in items:
        if it.get("status") != "SCHEDULED_AT_META":
            continue
        try:
            sched = parse_iso(it.get("scheduled_for", ""))
        except Exception:
            continue
        if sched + timedelta(minutes=5) <= now:
            out.append(it)
    return out


def print_due_table(items: list) -> None:
    if not items:
        print("Nothing due.")
        return
    print(f"{len(items)} due item(s):")
    print(f"{'ID':<28} {'MODE':<8} {'LAYOUT':<7} {'#IMG':<5} {'SCHEDULED':<28} CAPTION")
    print("-" * 110)
    for it in items:
        cap = (it.get("caption") or "")[:40].replace("\n", " ")
        layout = it.get("layout") or "-"
        n = len(it.get("image_paths") or [])
        print(f"{it['id']:<28} {it.get('mode',''):<8} {layout:<7} {n:<5} {it['scheduled_for']:<28} {cap}")


def print_groups(groups: dict) -> None:
    """Print three labelled sections (HANDOFF / VERIFY / DUE_LOCAL) for dry-run.

    Each section uses the same column layout as print_due_table plus a STATUS col.
    """
    any_rows = False
    for label, items in groups.items():
        print(f"=== {label} ({len(items)} item[s]) ===")
        if not items:
            print("  (none)")
            print()
            continue
        any_rows = True
        print(f"{'ID':<28} {'STATUS':<19} {'MODE':<8} {'LAY':<5} {'#IMG':<4} {'SCHEDULED':<26} CAPTION")
        print("-" * 120)
        for it in items:
            cap = (it.get("caption") or "")[:30].replace("\n", " ")
            layout = (it.get("layout") or "-")[:5]
            n = len(it.get("image_paths") or [])
            status = (it.get("status") or "")[:18]
            print(f"{it['id']:<28} {status:<19} {it.get('mode',''):<8} {layout:<5} {n:<4} {it['scheduled_for']:<26} {cap}")
        print()
    if not any_rows:
        print("Nothing to do.")


def _tg_send(text: str) -> None:
    """Fire-and-forget Telegram send. Silent if token/chat not set."""
    if not TELEGRAM_BOT_TOKEN or not TG_CHAT_ID:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data={"chat_id": TG_CHAT_ID, "text": text, "disable_web_page_preview": "true"},
            timeout=10,
        )
    except Exception as exc:
        print(f"tg send failed: {exc}", file=sys.stderr)


def tg_notify_success(item: dict, fb_post_id: str) -> None:
    paths = item.get("image_paths") or []
    n = len(paths)
    mode = item.get("mode", "multi")
    layout = item.get("layout")
    mode_tag = f"{mode}/{layout}" if mode == "collage" and layout else mode
    first = Path(paths[0]).name if paths else "?"
    text = (
        f"Posted feed: {item['id']} ({mode_tag})\n"
        f"{n} photo(s) -- {first}{(' +' + str(n-1)) if n > 1 else ''}\n"
        f"https://www.facebook.com/{fb_post_id}"
    )
    _tg_send(text)


def tg_notify_failure(item: dict, error: str) -> None:
    paths = item.get("image_paths") or []
    first = Path(paths[0]).name if paths else "(no images)"
    text = (
        f"Feed post FAILED: {item.get('id','?')}\n"
        f"{first}\n"
        f"Reason: {error[:300]}"
    )
    _tg_send(text)


def prepare_post(item: dict) -> tuple:
    """Returns (image_paths_to_send, caption, post_type, composed_path_or_none).

    post_type is "single" (one image), or "multi" (FB multi-photo grid).
    composed_path is non-null only when a collage was just built; the caller
    should persist it back to the queue item.
    """
    caption = item.get("caption", "")
    paths = item.get("image_paths") or []
    mode = item.get("mode", "multi")

    if mode == "collage":
        layout = item.get("layout")
        if not layout:
            raise ValueError(f"item {item.get('id')} is collage mode but missing layout")
        TMP_DIR.mkdir(parents=True, exist_ok=True)
        composed = TMP_DIR / f"collage_{item['id']}.png"
        abs_inputs = [
            str((PROJECT_DIR / p).resolve()) if not Path(p).is_absolute() else p
            for p in paths
        ]
        compose_collage(layout, abs_inputs, str(composed))
        return ([str(composed)], caption, "single", str(composed))

    # mode == "multi"
    if len(paths) == 1:
        return (paths, caption, "single", None)
    return (paths, caption, "multi", None)


def post_single_photo(image_path: str, caption: str) -> tuple:
    """POST /{page-id}/photos with published=true. Returns (ok, fb_post_id_or_error)."""
    abs_path = image_path if Path(image_path).is_absolute() else str((PROJECT_DIR / image_path).resolve())
    if not Path(abs_path).exists():
        return (False, f"file not found: {abs_path}")
    url = f"{BASE}/{META_PAGE_ID}/photos"
    try:
        with open(abs_path, "rb") as f:
            r = requests.post(
                url,
                data={
                    "message": caption,
                    "published": "true",
                    "access_token": META_PAGE_ACCESS_TOKEN,
                },
                files={"source": (Path(abs_path).name, f, "image/png")},
                timeout=60,
            )
    except Exception as exc:
        return (False, f"network: {exc}")
    if not r.ok:
        return (False, f"http {r.status_code}: {r.text[:200]}")
    data = r.json()
    return (True, data.get("post_id") or data.get("id", ""))


def _upload_unpublished_photo(abs_path: str) -> tuple:
    """Upload a photo with published=false. Returns (ok, fb_media_id_or_error)."""
    if not Path(abs_path).exists():
        return (False, f"file not found: {abs_path}")
    url = f"{BASE}/{META_PAGE_ID}/photos"
    try:
        with open(abs_path, "rb") as f:
            r = requests.post(
                url,
                data={
                    "published": "false",
                    "access_token": META_PAGE_ACCESS_TOKEN,
                },
                files={"source": (Path(abs_path).name, f, "image/png")},
                timeout=60,
            )
    except Exception as exc:
        return (False, f"network: {exc}")
    if not r.ok:
        return (False, f"http {r.status_code}: {r.text[:200]}")
    return (True, r.json().get("id", ""))


def post_multi_photo(image_paths: list, caption: str) -> tuple:
    """Upload N photos unpublished, then POST /feed with attached_media."""
    media_ids = []
    for path in image_paths:
        abs_path = path if Path(path).is_absolute() else str((PROJECT_DIR / path).resolve())
        ok, result = _upload_unpublished_photo(abs_path)
        if not ok:
            return (False, f"upload of {Path(path).name}: {result}")
        media_ids.append(result)

    attached = [{"media_fbid": mid} for mid in media_ids]
    url = f"{BASE}/{META_PAGE_ID}/feed"
    try:
        r = requests.post(
            url,
            data={
                "message": caption,
                "attached_media": json.dumps(attached),
                "access_token": META_PAGE_ACCESS_TOKEN,
            },
            timeout=60,
        )
    except Exception as exc:
        return (False, f"network: {exc}")
    if not r.ok:
        return (False, f"http {r.status_code}: {r.text[:200]}")
    data = r.json()
    return (True, data.get("id", ""))


def _write_last_run(posted: int, failed: int, handed_off: int = 0, verified: int = 0) -> None:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    LAST_RUN_FILE.write_text(
        json.dumps({
            "last_run_at": now_iso(),
            "posted": posted,
            "failed": failed,
            "handed_off": handed_off,
            "verified": verified,
        }, indent=2),
        encoding="utf-8",
    )


def process_handoff_pending(items: list) -> int:
    """Retry handoff for APPROVED items that didn't make it on first attempt.

    Returns count of items successfully handed off. Defensive: if an item
    already has fb_scheduled_post_id, verify it first instead of double-handing.
    """
    n = 0
    for item in items:
        item_id = item["id"]
        existing_sched_id = item.get("fb_scheduled_post_id")
        if existing_sched_id:
            # Already has a Meta id -- check if it's actually scheduled there
            # before re-uploading (avoid double-fire).
            is_pub, err = verify_published(existing_sched_id)
            if not err:
                # Meta knows the id, regardless of pub state -- treat as scheduled.
                print(f"[handoff:{item_id}] already on Meta as {existing_sched_id}, flipping to SCHEDULED_AT_META")
                update_item(item_id, {"status": "SCHEDULED_AT_META"})
                n += 1
                continue
        print(f"[handoff:{item_id}] attempt {item.get('handoff_attempts', 0) + 1}/3")
        ok, result = handoff_to_meta(item)
        attempts = item.get("handoff_attempts", 0) + 1
        patch: dict = {
            "handoff_attempted_at": now_iso(),
            "handoff_attempts": attempts,
        }
        if ok:
            patch["status"] = "SCHEDULED_AT_META"
            patch["fb_scheduled_post_id"] = result
            patch["handoff_error"] = None
            if item.get("composed_path"):
                patch["composed_path"] = item["composed_path"]
            print(f"  -> SCHEDULED_AT_META id={result}")
            n += 1
        else:
            patch["handoff_error"] = result
            print(f"  -> FAILED ({attempts}/3): {result[:140]}")
        update_item(item_id, patch)
    return n


def process_verify_pending(items: list) -> int:
    """Check SCHEDULED_AT_META items past their fire time.

    Flips to POSTED if Meta confirms is_published=True. Leaves as-is otherwise
    (next tick will retry). Stamps FAILED if 30+ min past fire time with
    is_published still False.
    """
    now = datetime.now(PHT)
    n = 0
    for item in items:
        item_id = item["id"]
        sched_id = item.get("fb_scheduled_post_id")
        if not sched_id:
            continue
        is_pub, err = verify_published(sched_id)
        if err:
            print(f"[verify:{item_id}] error: {err[:140]}")
            continue
        if is_pub:
            # The fired post's id is the same as the scheduled-post id Meta gave us.
            fb_post_id = sched_id
            print(f"[verify:{item_id}] POSTED (fb_post_id={fb_post_id})")
            patch = {"status": "POSTED", "fb_post_id": fb_post_id, "posted_at": now_iso()}
            update_item(item_id, patch)
            updated = {**item, **patch}
            tg_notify_success(updated, fb_post_id)
            n += 1
            continue
        # Not published yet -- if 30+ min past sched, mark FAILED
        try:
            sched = parse_iso(item.get("scheduled_for", ""))
        except Exception:
            sched = now
        if sched + timedelta(minutes=30) <= now:
            err_msg = f"Meta did not fire within 30 min of {sched.isoformat()}"
            print(f"[verify:{item_id}] FAILED: {err_msg}")
            update_item(item_id, {"status": "FAILED", "error": err_msg, "posted_at": now_iso()})
            tg_notify_failure(item, err_msg)
    return n


def process_due(items: list) -> tuple:
    posted_n = 0
    failed_n = 0
    for item in items:
        item_id = item["id"]
        print(f"[{item_id}] mode={item.get('mode')} layout={item.get('layout')} images={len(item.get('image_paths') or [])}")
        try:
            send_paths, caption, post_type, composed = prepare_post(item)
        except Exception as exc:
            err = f"prepare_post failed: {exc}"
            print(f"  FAIL: {err}")
            update_item(item_id, {"status": "FAILED", "error": err, "posted_at": now_iso()})
            tg_notify_failure(item, err)
            failed_n += 1
            continue

        if post_type == "single":
            ok, result = post_single_photo(send_paths[0], caption)
        else:
            ok, result = post_multi_photo(send_paths, caption)

        if ok:
            print(f"  POSTED: {result}")
            patch = {"status": "POSTED", "fb_post_id": result, "posted_at": now_iso()}
            if composed:
                patch["composed_path"] = composed
            update_item(item_id, patch)
            updated = {**item, **patch}
            tg_notify_success(updated, result)
            posted_n += 1
        else:
            print(f"  FAIL: {result}")
            update_item(item_id, {"status": "FAILED", "error": result, "posted_at": now_iso()})
            tg_notify_failure(item, result)
            failed_n += 1

    return (posted_n, failed_n)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", help="Print due items, do not post")
    args = p.parse_args()

    items = load_queue()
    handoff = handoff_pending_items(items)
    verify = verify_pending_items(items)
    due = due_items(items)

    if args.dry_run:
        print_groups({"HANDOFF": handoff, "VERIFY": verify, "DUE_LOCAL": due})
        return 0

    if not (handoff or verify or due):
        print("Nothing to do.")
        _write_last_run(0, 0)
        return 0

    if not META_PAGE_ACCESS_TOKEN or not META_PAGE_ID:
        print("error: META_PAGE_ACCESS_TOKEN / META_PAGE_ID not set", file=sys.stderr)
        return 1

    # Pass 1: hand off pending APPROVED items to Meta
    handed_off_n = 0
    if handoff:
        print(f"=== HANDOFF ({len(handoff)} item[s]) ===")
        handed_off_n = process_handoff_pending(handoff)

    # Pass 2: verify SCHEDULED_AT_META items past their fire time
    verified_n = 0
    if verify:
        print(f"\n=== VERIFY ({len(verify)} item[s]) ===")
        verified_n = process_verify_pending(verify)

    # Pass 3: local publish for APPROVED items past sched (handoff didn't take
    # in time -- e.g., <10 min lead or 3 handoff fails). RELOAD items after
    # the earlier passes since handoff may have moved some out of `due`.
    posted_n = failed_n = 0
    if due:
        # Refresh -- handoff pass may have moved items to SCHEDULED_AT_META
        fresh = load_queue()
        still_due = [it for it in due if next((x for x in fresh if x["id"] == it["id"]), {}).get("status") == "APPROVED"]
        if still_due:
            print(f"\n=== DUE_LOCAL ({len(still_due)} item[s]) ===")
            print_due_table(still_due)
            posted_n, failed_n = process_due(still_due)

    _write_last_run(posted_n, failed_n, handed_off_n, verified_n)
    print(f"\nRun complete. handed_off={handed_off_n} verified={verified_n} posted={posted_n} failed={failed_n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
