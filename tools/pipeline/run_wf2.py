"""
WF2 Pipeline Runner — PROMPT_READY → image gen → review → sync

Finds all PROMPT_READY captions, generates images in parallel,
starts the image review server + ngrok, sends email, syncs sheet.

Usage:
    python tools/pipeline/run_wf2.py
    python tools/pipeline/run_wf2.py --ids 20260318-001 20260318-002
    python tools/pipeline/run_wf2.py --force   # re-generate even if image exists
"""

import argparse
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent.parent
TMP_DIR = PROJECT_DIR / ".tmp"
OUTPUT_DIR = PROJECT_DIR / "output" / "images"
PIPELINE_FILE = TMP_DIR / "pipeline.json"
REJECTED_FILE = TMP_DIR / "rejected_captions.json"
VENV_PYTHON = PROJECT_DIR / ".venv" / "bin" / "python"


# ── Helpers ──────────────────────────────────────────────────────────────────

def load_pipeline():
    captions = []
    if PIPELINE_FILE.exists():
        captions.extend(json.loads(PIPELINE_FILE.read_text()))
    if REJECTED_FILE.exists():
        captions.extend(json.loads(REJECTED_FILE.read_text()))
    return captions


def find_targets(captions, ids_filter=None, force=False):
    """Return list of caption IDs ready for image generation."""
    targets = []
    skipped_approved = []
    skipped_done = []

    for c in captions:
        cid = str(c["id"])
        status = c.get("status", "")

        if ids_filter and cid not in ids_filter:
            continue

        prompt_file = TMP_DIR / f"{cid}_prompt_structured.json"
        output_file = OUTPUT_DIR / f"dubery_{cid}.jpg"

        if status == "APPROVED" and not prompt_file.exists():
            skipped_approved.append(cid)
            continue

        if status not in ("PROMPT_READY", "IMAGE_REJECTED", "IMAGE_FAILED"):
            if not (force and status == "DONE"):
                skipped_done.append(cid)
                continue

        if not prompt_file.exists():
            print(f"  SKIP #{cid}: prompt file missing")
            continue

        if output_file.exists() and not force:
            # Already generated — only skip if status is already IMAGE_APPROVED/DONE
            if status in ("IMAGE_APPROVED", "DONE") and c.get("image_url"):
                skipped_done.append(cid)
                continue

        targets.append(cid)

    return targets, skipped_approved, skipped_done


def run_image_gen(caption_id):
    """Run generate_kie.py for one caption. Returns (caption_id, success, log_path)."""
    prompt_file = TMP_DIR / f"{caption_id}_prompt_structured.json"
    output_file = OUTPUT_DIR / f"dubery_{caption_id}.jpg"
    log_file = TMP_DIR / f"generate_{caption_id}.log"

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    cmd = [
        str(VENV_PYTHON),
        "tools/image_gen/generate_kie.py",
        str(prompt_file),
        str(output_file),
    ]

    with open(log_file, "w") as log:
        result = subprocess.run(cmd, cwd=PROJECT_DIR, stdout=log, stderr=log)

    return caption_id, result.returncode == 0, log_file


def promote_rejections(succeeded_ids):
    """Move successfully regenerated IMAGE_REJECTED entries from rejected → pipeline."""
    if not REJECTED_FILE.exists() or not succeeded_ids:
        return

    rejected = json.loads(REJECTED_FILE.read_text())
    pipeline = json.loads(PIPELINE_FILE.read_text())

    to_move = [c for c in rejected if str(c["id"]) in succeeded_ids]
    if not to_move:
        return

    for c in to_move:
        c["status"] = "DONE"
        # Backfill product_ref from prompt file if missing
        if not c.get("product_ref"):
            prompt_file = TMP_DIR / f"{c['id']}_prompt_structured.json"
            if prompt_file.exists():
                try:
                    models = json.loads(prompt_file.read_text()).get("product", {}).get("models", [])
                    if models:
                        c["product_ref"] = " + ".join(models)
                except Exception:
                    pass
        pipeline.append(c)

    remaining = [c for c in rejected if str(c["id"]) not in succeeded_ids]

    PIPELINE_FILE.write_text(json.dumps(pipeline, indent=2, ensure_ascii=False))
    REJECTED_FILE.write_text(json.dumps(remaining, indent=2, ensure_ascii=False))
    print(f"  Moved {len(to_move)} regenerated caption(s) back to pipeline.json as DONE")


def sync_sheet():
    print("\nSyncing to Google Sheet...")
    result = subprocess.run(
        [str(VENV_PYTHON), "tools/notion/sync_pipeline.py", "--sheets-only"],
        cwd=PROJECT_DIR,
    )
    if result.returncode != 0:
        print("  Sheet sync failed.")
    else:
        print("  Sheet synced.")


def start_image_review():
    print("\nStarting image review server...")
    subprocess.run(
        ["bash", "tools/image_gen/start_image_review.sh"],
        cwd=PROJECT_DIR,
    )


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="WF2 pipeline runner")
    parser.add_argument("--ids", nargs="+", help="Specific caption IDs to process")
    parser.add_argument("--force", action="store_true", help="Re-generate even if image exists")
    parser.add_argument("--no-review", action="store_true", help="Skip starting the review server")
    parser.add_argument("--no-sync", action="store_true", help="Skip sheet sync")
    args = parser.parse_args()

    captions = load_pipeline()
    ids_filter = set(args.ids) if args.ids else None

    targets, skipped_approved, skipped_done = find_targets(captions, ids_filter, args.force)

    print(f"\nWF2 Pipeline Runner")
    print(f"{'─' * 40}")
    print(f"  PROMPT_READY (will generate): {len(targets)}")
    if skipped_approved:
        print(f"  APPROVED, no prompt yet (run dubery-prompt-writer first): {len(skipped_approved)}")
        for cid in skipped_approved:
            print(f"    #{cid}")
    if skipped_done:
        print(f"  Already done / skipped: {len(skipped_done)}")

    if not targets:
        print("\nNothing to generate.")
        if skipped_approved:
            print("Run the dubery-prompt-writer skill first to generate prompts for APPROVED captions.")
        sys.exit(0)

    print(f"\nGenerating {len(targets)} image(s) in parallel...")
    print(f"  IDs: {', '.join(targets)}\n")

    succeeded = []
    failed = []

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(run_image_gen, cid): cid for cid in targets}
        for future in as_completed(futures):
            cid, ok, log_file = future.result()
            if ok:
                succeeded.append(cid)
                print(f"  OK  #{cid}")
            else:
                failed.append(cid)
                print(f"  FAIL #{cid} — see {log_file.name}")

    print(f"\n{'─' * 40}")
    print(f"  Done: {len(succeeded)} succeeded, {len(failed)} failed")
    if failed:
        print(f"  Failed IDs: {', '.join(failed)}")
        print(f"  Logs: .tmp/generate_[id].log")

    # Promote successfully regenerated IMAGE_REJECTED entries back to pipeline
    if succeeded:
        promote_rejections(set(succeeded))

    # Always sync sheet after generation (captures any DONE/IMAGE_FAILED updates)
    if not args.no_sync:
        sync_sheet()

    # Start review server if any succeeded
    if succeeded and not args.no_review:
        start_image_review()
    elif failed and not succeeded:
        print("\nAll jobs failed — skipping review server.")
        sys.exit(1)


if __name__ == "__main__":
    main()
