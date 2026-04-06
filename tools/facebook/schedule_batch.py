"""
Batch schedule organic Facebook posts from IMAGE_APPROVED captions.

Distributes posts across Tue/Thu/Sat/Sun at 12:00 PM PHT (3-4 posts/week).

Usage:
    python tools/facebook/schedule_batch.py --ids 1 3 5 --dry-run
    python tools/facebook/schedule_batch.py --ids 1 3 5 --start "2026-03-29"
    python tools/facebook/schedule_batch.py --all --dry-run
    python tools/facebook/schedule_batch.py --all --max 10
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from schedule_post import (
    PROJECT_DIR,
    PHT,
    load_pipeline,
    generate_slots,
    schedule_one,
    find_image,
    UGC_PIPELINE_FILE,
)


def main():
    parser = argparse.ArgumentParser(description="Batch schedule Facebook posts")
    id_group = parser.add_mutually_exclusive_group(required=True)
    id_group.add_argument("--ids", nargs="+", type=str, help="Specific caption IDs")
    id_group.add_argument("--all", action="store_true", help="All eligible entries without organic_status")
    parser.add_argument("--ugc", action="store_true", help="Schedule from UGC pipeline instead of ad pipeline")
    parser.add_argument("--start", type=str, help="Start date: YYYY-MM-DD (default: today)")
    parser.add_argument("--max", type=int, help="Max number of posts to schedule")
    parser.add_argument("--dry-run", action="store_true", help="Preview schedule only")
    parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()

    is_ugc = args.ugc
    required_status = "DONE" if is_ugc else "IMAGE_APPROVED"
    source_name = "ugc_pipeline.json" if is_ugc else "pipeline.json"

    pipeline = load_pipeline(ugc=is_ugc)
    pipeline_by_id = {str(c["id"]): c for c in pipeline}

    # Select captions
    if args.ids:
        targets = []
        for cid in args.ids:
            caption = pipeline_by_id.get(cid)
            if not caption:
                print(f"  Warning: #{cid} not found in {source_name}, skipping")
            elif caption.get("status") != required_status:
                print(f"  Warning: #{cid} status is '{caption.get('status')}', skipping")
            elif caption.get("organic_status") == "SCHEDULED":
                print(f"  Warning: #{cid} already scheduled, skipping")
            elif not find_image(cid, ugc=is_ugc):
                print(f"  Warning: #{cid} image not found, skipping")
            else:
                targets.append(caption)
    else:
        targets = [
            c for c in pipeline
            if c.get("status") == required_status
            and not c.get("organic_status")
            and find_image(str(c["id"]), ugc=is_ugc)
        ]

    if args.max:
        targets = targets[:args.max]

    if not targets:
        print("\nNo eligible captions to schedule.")
        sys.exit(0)

    # Generate time slots
    start_from = None
    if args.start:
        start_from = datetime.strptime(args.start, "%Y-%m-%d").replace(
            hour=0, minute=0, tzinfo=PHT
        )

    slots = generate_slots(len(targets), start_from)

    if len(slots) < len(targets):
        print(f"Warning: could only generate {len(slots)} slots for {len(targets)} captions")
        targets = targets[:len(slots)]

    # Calculate schedule span
    first_date = slots[0].strftime("%a %Y-%m-%d")
    last_date = slots[-1].strftime("%a %Y-%m-%d")
    weeks = (slots[-1] - slots[0]).days / 7

    # Print schedule preview
    print(f"\nFacebook Organic Post Schedule")
    print(f"{'=' * 90}")
    print(f"  Captions:  {len(targets)}")
    print(f"  Schedule:  Tue / Thu / Sat / Sun @ 12:00 PM PHT")
    print(f"  Span:      {first_date}  -->  {last_date}  (~{weeks:.1f} weeks)")
    print(f"  Source:    {source_name}")
    print(f"  Mode:      {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"{'=' * 90}")
    print()
    print(f"  {'#':<4} {'Caption ID':<20} {'Scheduled Time':<28} {'Product':<22} {'Preview'}")
    print(f"  {'─' * 86}")

    for i, (caption, slot) in enumerate(zip(targets, slots), 1):
        cid = str(caption["id"])
        time_str = slot.strftime("%a %Y-%m-%d %I:%M %p PHT")
        product = caption.get("product_ref", caption.get("recommended_products", ""))[:20]
        preview = caption.get("caption_text", "")[:45].replace("\n", " ")
        print(f"  {i:<4} {cid:<20} {time_str:<28} {product:<22} {preview}")

    print(f"  {'─' * 86}")
    print()

    if args.dry_run:
        print("  Dry run complete. No posts were scheduled.")
        return

    # Confirmation gate
    if not args.yes:
        confirm = input(f"  Schedule {len(targets)} posts? (y/N): ").strip().lower()
        if confirm != "y":
            print("  Cancelled.")
            return

    # Schedule each post
    print(f"\nScheduling {len(targets)} posts...")
    total_ok, total_fail = 0, 0

    for caption, slot in zip(targets, slots):
        ok = schedule_one(caption, slot, dry_run=False, ugc=is_ugc)
        if ok:
            total_ok += 1
        else:
            total_fail += 1
        time.sleep(1)  # Gentle rate limiting

    print(f"\n{'=' * 50}")
    print(f"  Done: {total_ok} scheduled, {total_fail} skipped/failed")

    # Sync sheet
    if total_ok > 0:
        print("Syncing sheet...", end=" ", flush=True)
        result = subprocess.run(
            [sys.executable, str(PROJECT_DIR / "tools" / "notion" / "sync_pipeline.py"), "--sheets-only"],
            capture_output=True, text=True
        )
        print("done" if result.returncode == 0 else f"warning -- {result.stderr.strip()}")

    print(f"\nView scheduled posts: https://business.facebook.com/latest/posts/scheduled_posts")


if __name__ == "__main__":
    main()
