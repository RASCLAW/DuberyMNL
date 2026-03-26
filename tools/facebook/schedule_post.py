"""
Schedule organic Facebook photo posts from IMAGE_APPROVED captions.

Usage:
    python tools/facebook/schedule_post.py --id 20260320-001
    python tools/facebook/schedule_post.py --id 20260320-001 --time "2026-03-29 12:00"
    python tools/facebook/schedule_post.py --id 20260320-001 --now
    python tools/facebook/schedule_post.py --id 20260320-001 --dry-run
"""

import argparse
import fcntl
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_DIR / ".env")

TMP_DIR = PROJECT_DIR / ".tmp"
IMAGES_DIR = PROJECT_DIR / "output" / "images"
PIPELINE_FILE = TMP_DIR / "pipeline.json"
PIPELINE_LOCK = TMP_DIR / "pipeline.json.lock"
SCHEDULE_LOG = TMP_DIR / "scheduled_posts.json"

META_PAGE_ACCESS_TOKEN = os.environ.get("META_PAGE_ACCESS_TOKEN")
META_PAGE_ID = os.environ.get("META_PAGE_ID")
GRAPH_API_VERSION = "v21.0"
BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

PHT = timezone(timedelta(hours=8))

# Posting schedule: Tue, Thu, Sat, Sun at 12:00 PM PHT
POSTING_DAYS = [1, 3, 5, 6]  # Monday=0, Tue=1, Thu=3, Sat=5, Sun=6
POSTING_HOUR = 12  # 12:00 PM PHT


# -- Pipeline helpers ----------------------------------------------------------

def load_pipeline():
    if not PIPELINE_FILE.exists():
        print("Error: .tmp/pipeline.json not found", file=sys.stderr)
        sys.exit(1)
    return json.loads(PIPELINE_FILE.read_text())


def update_pipeline_entry(caption_id, fields):
    """Update fields for a caption in pipeline.json (file-locked)."""
    with open(PIPELINE_LOCK, "w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        try:
            pipeline = json.loads(PIPELINE_FILE.read_text())
            PIPELINE_FILE.with_suffix(".json.bak").write_text(
                json.dumps(pipeline, indent=2, ensure_ascii=False)
            )
            for c in pipeline:
                if str(c.get("id")) == caption_id:
                    c.update(fields)
                    break
            PIPELINE_FILE.write_text(json.dumps(pipeline, indent=2, ensure_ascii=False))
        finally:
            fcntl.flock(lf, fcntl.LOCK_UN)


# -- Helpers -------------------------------------------------------------------

def find_image(caption_id):
    """Find the local image file for a caption."""
    for ext in [".jpg", ".jpeg", ".png"]:
        p = IMAGES_DIR / f"dubery_{caption_id}{ext}"
        if p.exists():
            return p
    return None


def build_message(caption):
    """Build the Facebook post message from caption text + hashtags."""
    text = caption.get("caption_text", "")
    hashtags = caption.get("hashtags", "")
    if hashtags:
        return f"{text}\n\n{hashtags}"
    return text


def next_available_slot(from_time=None):
    """Calculate the next valid posting slot (Tue/Thu/Sat/Sun 12PM PHT)."""
    now = (from_time or datetime.now(PHT)).astimezone(PHT)
    # Start from next hour to ensure 10+ min buffer
    candidate = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)

    for _ in range(60):  # Look up to 60 days ahead
        if candidate.weekday() in POSTING_DAYS:
            slot = candidate.replace(hour=POSTING_HOUR, minute=0)
            if slot > now + timedelta(minutes=10):
                return slot
        candidate += timedelta(days=1)

    return None


def generate_slots(count, start_from=None):
    """Generate `count` future posting slots."""
    slots = []
    current = start_from or datetime.now(PHT)

    for _ in range(count * 10):  # Safety limit
        slot = next_available_slot(current)
        if slot is None:
            break
        slots.append(slot)
        current = slot + timedelta(hours=1)  # Move past this slot
        if len(slots) >= count:
            break

    return slots


def load_schedule_log():
    """Load the scheduled posts tracking log."""
    if SCHEDULE_LOG.exists():
        return json.loads(SCHEDULE_LOG.read_text())
    return []


def save_schedule_log(log):
    """Save the scheduled posts tracking log."""
    SCHEDULE_LOG.write_text(json.dumps(log, indent=2, ensure_ascii=False))


# -- Core scheduling ----------------------------------------------------------

def schedule_one(caption, scheduled_time, dry_run=False):
    """Schedule a single organic photo post. Returns True on success."""
    cid = str(caption["id"])

    # Validate status
    if caption.get("status") != "IMAGE_APPROVED":
        print(f"    SKIP #{cid}: status is '{caption.get('status')}' -- only IMAGE_APPROVED")
        return False

    # Check if already scheduled
    if caption.get("organic_status") == "SCHEDULED":
        print(f"    SKIP #{cid}: already scheduled (fb_post_id: {caption.get('fb_post_id', '?')})")
        return False

    # Find image
    image_path = find_image(cid)
    if not image_path:
        print(f"    SKIP #{cid}: image not found at output/images/dubery_{cid}.*")
        return False

    # Validate schedule time
    now = datetime.now(PHT)
    if scheduled_time <= now + timedelta(minutes=10):
        print(f"    SKIP #{cid}: scheduled time must be at least 10 minutes in the future")
        return False

    if scheduled_time > now + timedelta(days=75):
        print(f"    SKIP #{cid}: scheduled time must be within 75 days")
        return False

    message = build_message(caption)
    scheduled_unix = int(scheduled_time.timestamp())
    time_str = scheduled_time.strftime("%a %Y-%m-%d %I:%M %p PHT")

    if dry_run:
        preview = caption.get("caption_text", "")[:60].replace("\n", " ")
        product = caption.get("product_ref", caption.get("recommended_products", ""))
        print(f"    #{cid:20s} | {time_str} | {product[:20]:20s} | {preview}")
        return True

    print(f"    Scheduling #{cid} for {time_str}...")

    try:
        url = f"{BASE}/{META_PAGE_ID}/photos"
        with open(image_path, "rb") as f:
            response = requests.post(
                url,
                data={
                    "message": message,
                    "published": "false",
                    "scheduled_publish_time": scheduled_unix,
                    "access_token": META_PAGE_ACCESS_TOKEN,
                },
                files={"source": (image_path.name, f, "image/jpeg")},
            )

        if not response.ok:
            print(f"    FAIL #{cid}: API error {response.status_code}: {response.text}")
            return False

        data = response.json()
        fb_post_id = data.get("id") or data.get("post_id", "")

        # Update pipeline
        update_pipeline_entry(cid, {
            "organic_status": "SCHEDULED",
            "fb_post_id": fb_post_id,
            "fb_scheduled_time": scheduled_time.isoformat(),
            "fb_scheduled_at": datetime.now(PHT).isoformat(),
        })

        # Log to schedule tracker
        log = load_schedule_log()
        log.append({
            "caption_id": cid,
            "fb_post_id": fb_post_id,
            "scheduled_time": scheduled_time.isoformat(),
            "scheduled_at": datetime.now(PHT).isoformat(),
            "status": "SCHEDULED",
            "message_preview": caption.get("caption_text", "")[:80],
        })
        save_schedule_log(log)

        print(f"      -> SCHEDULED | fb_post_id: {fb_post_id} | {time_str}")
        return True

    except Exception as e:
        print(f"    FAIL #{cid}: {e}")
        return False


def publish_now(caption, dry_run=False):
    """Publish a post immediately (not scheduled)."""
    cid = str(caption["id"])

    if caption.get("status") != "IMAGE_APPROVED":
        print(f"    SKIP #{cid}: status is '{caption.get('status')}'")
        return False

    image_path = find_image(cid)
    if not image_path:
        print(f"    SKIP #{cid}: image not found")
        return False

    message = build_message(caption)

    if dry_run:
        preview = caption.get("caption_text", "")[:60].replace("\n", " ")
        print(f"    #{cid}: PUBLISH NOW (dry-run) | {preview}")
        return True

    print(f"    Publishing #{cid} immediately...")

    try:
        url = f"{BASE}/{META_PAGE_ID}/photos"
        with open(image_path, "rb") as f:
            response = requests.post(
                url,
                data={
                    "message": message,
                    "published": "true",
                    "access_token": META_PAGE_ACCESS_TOKEN,
                },
                files={"source": (image_path.name, f, "image/jpeg")},
            )

        if not response.ok:
            print(f"    FAIL #{cid}: API error {response.status_code}: {response.text}")
            return False

        data = response.json()
        fb_post_id = data.get("id") or data.get("post_id", "")

        update_pipeline_entry(cid, {
            "organic_status": "POSTED",
            "fb_post_id": fb_post_id,
            "fb_posted_at": datetime.now(PHT).isoformat(),
        })

        print(f"      -> POSTED | fb_post_id: {fb_post_id}")
        return True

    except Exception as e:
        print(f"    FAIL #{cid}: {e}")
        return False


# -- CLI -----------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Schedule organic Facebook posts")
    parser.add_argument("--id", type=str, required=True, help="Caption ID")
    parser.add_argument("--time", type=str, help="Scheduled time in PHT: 'YYYY-MM-DD HH:MM'")
    parser.add_argument("--now", action="store_true", help="Publish immediately")
    parser.add_argument("--dry-run", action="store_true", help="Preview without posting")
    args = parser.parse_args()

    # Validate env
    if not META_PAGE_ACCESS_TOKEN:
        print("Error: META_PAGE_ACCESS_TOKEN not set in .env", file=sys.stderr)
        sys.exit(1)
    if not META_PAGE_ID:
        print("Error: META_PAGE_ID not set in .env", file=sys.stderr)
        sys.exit(1)

    pipeline = load_pipeline()
    caption = next((c for c in pipeline if str(c["id"]) == args.id), None)
    if not caption:
        print(f"Error: caption #{args.id} not found in pipeline.json", file=sys.stderr)
        sys.exit(1)

    if args.now:
        ok = publish_now(caption, dry_run=args.dry_run)
    else:
        if args.time:
            scheduled_time = datetime.strptime(args.time, "%Y-%m-%d %H:%M").replace(tzinfo=PHT)
        else:
            scheduled_time = next_available_slot()
            if not scheduled_time:
                print("Error: could not find a valid posting slot", file=sys.stderr)
                sys.exit(1)
        ok = schedule_one(caption, scheduled_time, dry_run=args.dry_run)

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
