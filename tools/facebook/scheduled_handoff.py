"""
Meta-native scheduled publish handoff for the DuberyMNL feed scheduler.

Hands off APPROVED queue items to Facebook via `scheduled_publish_time` at
queue time so posts fire from Meta's servers even when our laptop is off.
Local cron (`post_from_queue.py`) becomes the retry safety net + the verifier
that flips SCHEDULED_AT_META -> POSTED after Meta fires.

## Graph API contracts (v25.0)

### Endpoints
- Single photo scheduled:
    POST {BASE}/{PAGE_ID}/photos  (multipart)
      message=<caption>
      published=false
      scheduled_publish_time=<unix>
      access_token=<token>
      source=(name, file, "image/png")
    -> {"id": "<scheduled_post_id>"}

- Multi-photo upload (unpublished, no per-photo schedule):
    POST {BASE}/{PAGE_ID}/photos  (multipart)
      published=false
      access_token=<token>
      source=(name, file, "image/png")
    -> {"id": "<media_fbid>"}

- Multi-photo attach + schedule:
    POST {BASE}/{PAGE_ID}/feed
      message=<caption>
      attached_media=[{"media_fbid":"<id1>"},...]  (JSON string)
      published=false
      scheduled_publish_time=<unix>
      access_token=<token>
    -> {"id": "<scheduled_post_id>"}

- Cancel:
    DELETE {BASE}/{scheduled_id}?access_token=<token>
    -> {"success": true}

- Verify:
    GET {BASE}/{scheduled_id}?fields=is_published,scheduled_publish_time
    -> {"id": "<id>", "is_published": bool, "scheduled_publish_time": <unix>}

### Rules
- scheduled_publish_time must be >=10 min and <=6 months in the future.
- Value is unix seconds UTC -- use `int(tz_aware_dt.timestamp())`.
- For multi-photo, schedule time goes only on the /feed POST, not on each /photos upload.
- Returns standardize on `id` (single-photo non-scheduled also returns `post_id`;
  scheduled posts only return `id`).

### Eligibility
An item is handed off iff: status=APPROVED, lead_sec >= MIN_LEAD_SECONDS,
lead_sec <= MAX_LEAD_DAYS*86400, handoff_attempts < 3.

## State machine
    APPROVED  --handoff ok-->  SCHEDULED_AT_META  --verify-->  POSTED
       |                              |
       |                              +--cancel-->  CANCELLED (FB deleted)
       |
       +--cron fire (<10min lead or 3 handoff fails)-->  local publish -> POSTED/FAILED
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

META_PAGE_ACCESS_TOKEN = os.environ.get("META_PAGE_ACCESS_TOKEN")
META_PAGE_ID = os.environ.get("META_PAGE_ID")
GRAPH_API_VERSION = "v25.0"
BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

PHT = timezone(timedelta(hours=8))

# Meta requires >=10 min lead. 660s gives a 60s safety buffer.
MIN_LEAD_SECONDS = 660
MAX_LEAD_DAYS = 180


def _abs(path: str) -> Path:
    """Resolve a queue-relative path to absolute under PROJECT_DIR."""
    p = Path(path)
    return p if p.is_absolute() else (PROJECT_DIR / p).resolve()


def _compose_if_needed(item: dict) -> tuple[Path | None, str | None]:
    """For collage mode, compose to .tmp/collage_<id>.png. Returns (path, err)."""
    if item.get("mode") != "collage":
        return (None, None)
    layout = item.get("layout")
    if not layout:
        return (None, f"item {item.get('id')} is collage mode but missing layout")
    try:
        sys.path.insert(0, str(PROJECT_DIR))
        from tools.image_ops.compose import compose as compose_collage
    except Exception as exc:
        return (None, f"compose import failed: {exc}")
    tmp_dir = PROJECT_DIR / ".tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    composed = tmp_dir / f"collage_{item['id']}.png"
    abs_inputs = [str(_abs(p)) for p in (item.get("image_paths") or [])]
    try:
        compose_collage(layout, abs_inputs, str(composed))
    except Exception as exc:
        return (None, f"compose failed: {exc}")
    return (composed, None)


def _scheduled_unix(item: dict) -> tuple[int | None, str | None]:
    """Convert item['scheduled_for'] to unix seconds UTC. (unix, err)."""
    sched = item.get("scheduled_for")
    if not sched:
        return (None, "no scheduled_for")
    try:
        return (int(_parse_iso(sched).timestamp()), None)
    except (TypeError, ValueError) as exc:
        return (None, f"bad scheduled_for: {exc}")


def _post_single_scheduled(abs_path: Path, caption: str, unix_t: int) -> tuple[bool, str]:
    """POST /{page}/photos with published=false + scheduled_publish_time."""
    if not abs_path.exists():
        return (False, f"file not found: {abs_path}")
    url = f"{BASE}/{META_PAGE_ID}/photos"
    try:
        with open(abs_path, "rb") as f:
            r = requests.post(
                url,
                data={
                    "message": caption,
                    "published": "false",
                    "scheduled_publish_time": str(unix_t),
                    "access_token": META_PAGE_ACCESS_TOKEN,
                },
                files={"source": (abs_path.name, f, "image/png")},
                timeout=60,
            )
    except Exception as exc:
        return (False, f"network: {exc}")
    if not r.ok:
        return (False, f"http {r.status_code}: {r.text[:200]}")
    return (True, r.json().get("id", ""))


def handoff_to_meta(item: dict) -> tuple[bool, str]:
    """Hand off a queue item to FB as a scheduled post.

    Returns (True, scheduled_post_id) on success or (False, "error msg") on failure.
    For collage mode, composes the collage first; the composed path is written
    to item['composed_path'] in-place so the caller can persist it.
    """
    unix_t, err = _scheduled_unix(item)
    if err:
        return (False, err)

    paths = item.get("image_paths") or []
    if not paths:
        return (False, "no image_paths on item")

    caption = item.get("caption", "")
    mode = item.get("mode", "multi")

    # Collage mode: compose first, then single-photo upload of the composed file
    if mode == "collage":
        composed, err = _compose_if_needed(item)
        if err:
            return (False, err)
        item["composed_path"] = str(composed)
        return _post_single_scheduled(composed, caption, unix_t)

    # Single-photo (mode=multi, 1 image)
    if len(paths) == 1:
        return _post_single_scheduled(_abs(paths[0]), caption, unix_t)

    # Multi-photo: upload each unpublished, then attach + schedule on /feed
    media_ids = []
    for path in paths:
        abs_p = _abs(path)
        ok, result = _upload_unpublished_photo(abs_p)
        if not ok:
            return (False, f"upload of {abs_p.name}: {result}")
        media_ids.append(result)

    url = f"{BASE}/{META_PAGE_ID}/feed"
    attached = [{"media_fbid": mid} for mid in media_ids]
    try:
        r = requests.post(
            url,
            data={
                "message": caption,
                "attached_media": json.dumps(attached),
                "published": "false",
                "scheduled_publish_time": str(unix_t),
                "access_token": META_PAGE_ACCESS_TOKEN,
            },
            timeout=60,
        )
    except Exception as exc:
        return (False, f"network: {exc}")
    if not r.ok:
        return (False, f"http {r.status_code}: {r.text[:200]}")
    return (True, r.json().get("id", ""))


def _upload_unpublished_photo(abs_path: Path) -> tuple[bool, str]:
    """Upload a single photo with published=false. Returns (ok, media_fbid_or_err)."""
    if not abs_path.exists():
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
                files={"source": (abs_path.name, f, "image/png")},
                timeout=60,
            )
    except Exception as exc:
        return (False, f"network: {exc}")
    if not r.ok:
        return (False, f"http {r.status_code}: {r.text[:200]}")
    return (True, r.json().get("id", ""))


def cancel_at_meta(scheduled_id: str) -> tuple[bool, str]:
    """Delete a scheduled post on Meta side. Returns (True, "") on 200 or (False, "error msg")."""
    if not scheduled_id:
        return (False, "no scheduled_id")
    url = f"{BASE}/{scheduled_id}"
    try:
        r = requests.delete(url, params={"access_token": META_PAGE_ACCESS_TOKEN}, timeout=30)
    except Exception as exc:
        return (False, f"network: {exc}")
    if not r.ok:
        return (False, f"http {r.status_code}: {r.text[:200]}")
    return (True, "")


def _verify_one(scheduled_id: str) -> tuple[bool, str, int]:
    """Single GET attempt. Returns (is_published, error_msg, http_status)."""
    url = f"{BASE}/{scheduled_id}"
    try:
        r = requests.get(
            url,
            params={
                "fields": "is_published,scheduled_publish_time",
                "access_token": META_PAGE_ACCESS_TOKEN,
            },
            timeout=30,
        )
    except Exception as exc:
        return (False, f"network: {exc}", 0)
    if not r.ok:
        return (False, f"http {r.status_code}: {r.text[:200]}", r.status_code)
    try:
        return (bool(r.json().get("is_published", False)), "", 200)
    except Exception as exc:
        return (False, f"parse: {exc}", 200)


def verify_published(scheduled_id: str) -> tuple[bool, str]:
    """Check whether a scheduled post has fired. Returns (is_published, "") or (False, "msg").

    Handles two id formats: scheduled-id (bare photo_id, returned by /photos at handoff)
    works while the post is still scheduled. Once it fires Meta converts it to a
    page-post-id (`<page_id>_<post_id>`); the bare form then returns a deprecation
    error. We try bare first, fall back to compound on that specific failure.

    Note: ('not yet published' is (False, ""); errors are (False, "...non-empty msg")).
    """
    if not scheduled_id:
        return (False, "no scheduled_id")
    is_pub, err, status = _verify_one(scheduled_id)
    # Meta deprecation error for fired posts -- retry with compound id
    if err and ("singular statuses API is deprecated" in err or status == 400):
        if META_PAGE_ID and "_" not in scheduled_id:
            compound = f"{META_PAGE_ID}_{scheduled_id}"
            return _verify_one(compound)[:2]
    return (is_pub, err)


def _parse_iso(s: str) -> datetime:
    """Parse ISO 8601 to a tz-aware datetime. Naive input is treated as PHT."""
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=PHT)
    return dt


def eligible_for_handoff(item: dict, now: datetime) -> bool:
    """Return True iff the item is in a state to be handed off to Meta.

    Conditions:
    - status == APPROVED
    - scheduled_for is >=MIN_LEAD_SECONDS and <=MAX_LEAD_DAYS in future
    - handoff_attempts (default 0) < 3
    """
    if item.get("status") != "APPROVED":
        return False
    if item.get("handoff_attempts", 0) >= 3:
        return False
    sched = item.get("scheduled_for")
    if not sched:
        return False
    try:
        sched_dt = _parse_iso(sched)
    except (TypeError, ValueError):
        return False
    lead_sec = (sched_dt - now).total_seconds()
    if lead_sec < MIN_LEAD_SECONDS:
        return False
    if lead_sec > MAX_LEAD_DAYS * 86400:
        return False
    return True


def _smoke_eligible() -> None:
    """Smoke-check eligible_for_handoff() with 4 cases. Prints True False False False."""
    now = datetime(2026, 5, 25, 8, 0, 0, tzinfo=PHT)
    eligible = {
        "status": "APPROVED",
        "scheduled_for": (now + timedelta(hours=1)).isoformat(),
        "handoff_attempts": 0,
    }
    too_soon = {
        "status": "APPROVED",
        "scheduled_for": (now + timedelta(minutes=5)).isoformat(),
    }
    too_far = {
        "status": "APPROVED",
        "scheduled_for": (now + timedelta(days=200)).isoformat(),
    }
    max_attempts = {
        "status": "APPROVED",
        "scheduled_for": (now + timedelta(hours=1)).isoformat(),
        "handoff_attempts": 3,
    }
    results = [
        eligible_for_handoff(eligible, now),
        eligible_for_handoff(too_soon, now),
        eligible_for_handoff(too_far, now),
        eligible_for_handoff(max_attempts, now),
    ]
    print(" ".join(str(r) for r in results))


def _dry_run_payload(item_id: str) -> None:
    """Build (but don't send) the handoff payload for a queue item, print it."""
    sys.path.insert(0, str(PROJECT_DIR / "tools" / "facebook"))
    from queue_helpers import load_queue
    items = load_queue()
    item = next((it for it in items if it.get("id") == item_id), None)
    if not item:
        print(f"item not found: {item_id}", file=sys.stderr)
        sys.exit(1)

    unix_t, err = _scheduled_unix(item)
    print(f"=== item {item_id} ===")
    print(f"  status: {item.get('status')}")
    print(f"  mode:   {item.get('mode')}")
    print(f"  paths:  {len(item.get('image_paths') or [])}")
    print(f"  scheduled_for: {item.get('scheduled_for')}")
    if err:
        print(f"  ERROR: {err}")
        return
    print(f"  scheduled_publish_time (unix UTC): {unix_t}")
    print()

    paths = item.get("image_paths") or []
    mode = item.get("mode", "multi")

    if mode == "collage" or len(paths) == 1:
        # Single-photo path (collage composes to one file)
        if mode == "collage":
            print(f"  collage mode: would compose to .tmp/collage_{item_id}.png first")
        target = paths[0] if mode != "collage" else f".tmp/collage_{item_id}.png"
        print(f"  Single-photo POST {BASE}/{META_PAGE_ID}/photos")
        print(f"    data: message=<{len(item.get('caption',''))} char caption>, published=false, "
              f"scheduled_publish_time={unix_t}, access_token=<{len(META_PAGE_ACCESS_TOKEN or '')} char token>")
        print(f"    files: source=({Path(target).name}, <file bytes>, image/png)")
        return

    # Multi-photo (Task 5)
    print(f"  Multi-photo upload sequence ({len(paths)} photos):")
    for i, p in enumerate(paths, 1):
        print(f"    [{i}] POST {BASE}/{META_PAGE_ID}/photos -- published=false, source=({Path(p).name}, ...)")
    print(f"  Then attach + schedule:")
    print(f"    POST {BASE}/{META_PAGE_ID}/feed")
    print(f"    data: message=<caption>, attached_media=[{{media_fbid:<id>}},...], "
          f"published=false, scheduled_publish_time={unix_t}, access_token=<token>")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1].strip() if __doc__ else "")
    ap.add_argument("--check", metavar="ID", help="Run verify_published against a scheduled-post id and print result.")
    ap.add_argument("--dry-run-payload", metavar="QUEUE_ITEM_ID", help="Build + print the handoff payload for a queue item without sending.")
    ap.add_argument("--smoke", action="store_true", help="Run eligibility smoke check (Task 3 acceptance).")
    args = ap.parse_args()
    if args.smoke:
        _smoke_eligible()
        sys.exit(0)
    if args.dry_run_payload:
        _dry_run_payload(args.dry_run_payload)
        sys.exit(0)
    if args.check:
        is_pub, err = verify_published(args.check)
        if err:
            print(f"ERROR: {err}")
            sys.exit(1)
        print(f"{args.check}: is_published={is_pub}")
        sys.exit(0)
    if not (args.check or args.dry_run_payload):
        _smoke_eligible()
