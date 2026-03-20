"""
WF2 Post-Review Orchestrator

End-to-end automation: caption review → prompt writing → image gen → image review.
Triggered automatically by start_review.sh after caption review submit.

Handles recovery: after WF2a, re-scans pipeline for ALL PROMPT_READY captions
(catches any from a previous crashed run). Calls run_wf2.py once with all IDs
for sequential gatekeeper + image gen. Image review launches only after ALL
images are generated.

Usage:
    python tools/pipeline/run_post_review.py
    python tools/pipeline/run_post_review.py --ids 20260318-001 20260318-002
    python tools/pipeline/run_post_review.py --dry-run
    python tools/pipeline/run_post_review.py --prompts-only
    python tools/pipeline/run_post_review.py --images-only
    python tools/pipeline/run_post_review.py --batch 20260320
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent.parent
TMP_DIR = PROJECT_DIR / ".tmp"
PIPELINE_FILE = TMP_DIR / "pipeline.json"
QUEUE_FILE = TMP_DIR / "wf2_queue.json"
VENV_PYTHON = PROJECT_DIR / ".venv" / "bin" / "python"


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_pipeline():
    if not PIPELINE_FILE.exists():
        print("ERROR: .tmp/pipeline.json not found")
        sys.exit(1)
    return json.loads(PIPELINE_FILE.read_text())


def detect_batch_id(captions):
    """Detect the most recent batch_id from APPROVED/PROMPT_READY captions."""
    batch_ids = set()
    for c in captions:
        if c.get("status") in ("APPROVED", "PROMPT_READY"):
            bid = c.get("batch_id", "")
            if bid:
                batch_ids.add(bid)
    if batch_ids:
        return max(batch_ids)  # most recent batch
    return None


def find_prompt_targets(captions, ids_filter=None, batch_id=None):
    """APPROVED captions that don't have a prompt file yet (WF2a targets)."""
    targets = []
    for c in captions:
        cid = str(c["id"])
        if ids_filter and cid not in ids_filter:
            continue
        if batch_id and c.get("batch_id") != batch_id:
            continue
        if c.get("status") != "APPROVED":
            continue
        prompt_file = TMP_DIR / f"{cid}_prompt_structured.json"
        if not prompt_file.exists():
            targets.append(cid)
    return targets


def find_image_targets(captions, ids_filter=None, batch_id=None):
    """PROMPT_READY + IMAGE_FAILED captions with prompt files (WF2b targets)."""
    targets = []
    for c in captions:
        cid = str(c["id"])
        if ids_filter and cid not in ids_filter:
            continue
        if batch_id and c.get("batch_id") != batch_id:
            continue
        if c.get("status") not in ("PROMPT_READY", "IMAGE_FAILED"):
            continue
        prompt_file = TMP_DIR / f"{cid}_prompt_structured.json"
        if prompt_file.exists():
            targets.append(cid)
    return targets


def _claude_env():
    """Return env dict with CLAUDECODE unset to allow nested claude --print calls."""
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)
    return env


def _run_claude_with_retry(prompt, max_retries=3, wait_seconds=30):
    """Run claude --print with retry logic for transient API errors (500, timeout)."""
    for attempt in range(1, max_retries + 1):
        result = subprocess.run(
            ["claude", "--print", "--dangerously-skip-permissions", prompt],
            cwd=PROJECT_DIR,
            env=_claude_env(),
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return True

        stderr = result.stderr or ""
        stdout = result.stdout or ""
        is_transient = any(s in stderr + stdout for s in ["500", "Internal server error", "overloaded", "timeout", "ETIMEDOUT"])

        if is_transient and attempt < max_retries:
            print(f"    Transient API error (attempt {attempt}/{max_retries}), retrying in {wait_seconds}s...")
            time.sleep(wait_seconds)
            continue

        return False
    return False


def run_prompt_writer(caption_id):
    """Call Claude CLI to run dubery-prompt-writer for one caption (with retry)."""
    prompt = (
        f"run dubery-prompt-writer for caption {caption_id}. "
        f"Process only caption ID {caption_id} from .tmp/pipeline.json. "
        f"Generate the structured NB2 prompt, save to .tmp/{caption_id}_prompt_structured.json, "
        f"and update status to PROMPT_READY in pipeline.json."
    )
    return _run_claude_with_retry(prompt)


def run_prompt_parser(caption_id):
    """Call Claude CLI to run dubery-prompt-parser for one caption (with retry)."""
    prompt = (
        f"run dubery-prompt-parser for caption {caption_id}. "
        f"Read .tmp/{caption_id}_prompt_structured.json, parse it to the correct generate_kie.py schema, "
        f"and overwrite .tmp/{caption_id}_prompt_structured.json with the parsed JSON."
    )
    return _run_claude_with_retry(prompt)


def run_image_gen_batch(caption_ids):
    """Run gatekeeper + image gen for all captions via run_wf2.py (single call, sequential).
    Returns (succeeded, failed) lists."""
    result = subprocess.run(
        [str(VENV_PYTHON), "tools/pipeline/run_wf2.py",
         "--ids"] + caption_ids + ["--no-review", "--no-sync"],
        cwd=PROJECT_DIR,
    )
    # Re-read pipeline to check which succeeded/failed
    captions = json.loads(PIPELINE_FILE.read_text())
    succeeded = []
    failed = []
    for c in captions:
        cid = str(c["id"])
        if cid not in caption_ids:
            continue
        if c.get("status") == "DONE" and c.get("image_url"):
            succeeded.append(cid)
        elif c.get("status") in ("IMAGE_FAILED", "PROMPT_FAILED", "PROMPT_READY"):
            failed.append(cid)
    return succeeded, failed


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


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="WF2 post-review orchestrator")
    parser.add_argument("--ids", nargs="+", help="Specific caption IDs to process")
    parser.add_argument("--batch", type=str, help="Batch ID to process (e.g. 20260320)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would run without executing")
    parser.add_argument("--prompts-only", action="store_true", help="Run WF2a only, skip image gen")
    parser.add_argument("--images-only", action="store_true", help="Run WF2b only, skip prompt writing")
    parser.add_argument("--delay", type=int, default=0, help="Seconds between image gen jobs (default: 0)")
    args = parser.parse_args()

    captions = load_pipeline()

    # Determine scope: --ids > --batch > auto-detect batch > queue file
    ids_filter = None
    batch_id = None

    if args.ids:
        ids_filter = set(args.ids)
    elif args.batch:
        batch_id = args.batch
    elif QUEUE_FILE.exists():
        queue = json.loads(QUEUE_FILE.read_text())
        if queue:
            ids_filter = set(queue)
            print(f"Using session queue: {len(ids_filter)} IDs from wf2_queue.json")
    else:
        # Auto-detect: find the most recent batch with APPROVED/PROMPT_READY captions
        batch_id = detect_batch_id(captions)
        if batch_id:
            print(f"Auto-detected batch: {batch_id}")

    print(f"\nWF2 Post-Review Orchestrator")
    print(f"{'─' * 40}")
    if batch_id:
        print(f"  Batch: {batch_id}")

    if args.images_only:
        # Skip WF2a, go straight to image gen
        image_targets = find_image_targets(captions, ids_filter, batch_id)
        print(f"  PROMPT_READY (will generate images): {len(image_targets)}")
        if image_targets:
            print(f"  IDs: {', '.join(image_targets)}")

        if not image_targets:
            print("\nNo PROMPT_READY captions found.")
            sys.exit(0)

        if args.dry_run:
            print(f"\nDRY RUN — would generate {len(image_targets)} image(s)")
            sys.exit(0)

    else:
        targets = find_prompt_targets(captions, ids_filter, batch_id)
        print(f"  New APPROVED (no prompt yet): {len(targets)}")

        # Also show PROMPT_READY count for awareness
        existing_ready = find_image_targets(captions, ids_filter, batch_id)
        if existing_ready:
            print(f"  Already PROMPT_READY (will include in WF2b): {len(existing_ready)}")

        if targets:
            print(f"  IDs: {', '.join(targets)}")

        if not targets and not existing_ready:
            print("\nNo APPROVED or PROMPT_READY captions to process.")
            sys.exit(0)

        if args.dry_run:
            print(f"\nDRY RUN — no actions taken")
            if targets:
                print(f"  Would write prompts for {len(targets)} caption(s)")
            if not args.prompts_only:
                total_images = len(targets) + len(existing_ready)
                print(f"  Would generate up to {total_images} image(s)")
            sys.exit(0)

        # ── WF2a: Prompt writing ──────────────────────────────────────────────
        prompt_succeeded = []
        prompt_failed = []

        if targets:
            print(f"\nWF2a — Writing prompts ({len(targets)} captions, sequential)...")

            for cid in targets:
                print(f"\n  [{cid}] Running dubery-prompt-writer...")
                writer_ok = run_prompt_writer(cid)
                if not writer_ok:
                    print(f"  FAIL #{cid} — prompt-writer exited non-zero")
                    prompt_failed.append(cid)
                    continue

                print(f"  [{cid}] Running dubery-prompt-parser...")
                parser_ok = run_prompt_parser(cid)
                if not parser_ok:
                    print(f"  FAIL #{cid} — prompt-parser exited non-zero")
                    prompt_failed.append(cid)
                    continue

                prompt_file = TMP_DIR / f"{cid}_prompt_structured.json"
                if not prompt_file.exists():
                    print(f"  FAIL #{cid} — prompt file not created")
                    prompt_failed.append(cid)
                    continue

                # Validate parser output is valid JSON
                try:
                    parsed = json.loads(prompt_file.read_text())
                    if not isinstance(parsed, dict) or "product" not in parsed:
                        print(f"  FAIL #{cid} — parser output missing required 'product' key")
                        prompt_failed.append(cid)
                        continue
                except json.JSONDecodeError as e:
                    print(f"  FAIL #{cid} — parser output is not valid JSON: {e}")
                    prompt_failed.append(cid)
                    continue

                print(f"  OK  #{cid}")
                prompt_succeeded.append(cid)

            print(f"\n{'─' * 40}")
            print(f"  Prompts: {len(prompt_succeeded)} succeeded, {len(prompt_failed)} failed")
            if prompt_failed:
                print(f"  Failed IDs: {', '.join(prompt_failed)}")
        else:
            print("\nWF2a — No new APPROVED captions to write prompts for.")

        if args.prompts_only:
            print("\n--prompts-only: stopping before image gen.")
            sys.exit(0 if not prompt_failed else 1)

        # ── Re-scan for ALL PROMPT_READY captions in this batch ───────────────
        # This catches captions from previous crashed runs + just-written ones
        captions = load_pipeline()  # reload after WF2a writes
        image_targets = find_image_targets(captions, ids_filter, batch_id)

        if not image_targets:
            print("\nNo PROMPT_READY captions for image gen.")
            sys.exit(1 if prompt_failed else 0)

        print(f"\n  Total PROMPT_READY for WF2b: {len(image_targets)}")
        print(f"  IDs: {', '.join(image_targets)}")

    # ── WF2b: Image generation (single call to run_wf2.py) ────────────────
    print(f"\nWF2b — Generating {len(image_targets)} image(s) (gatekeeper + sequential gen)...")

    succeeded, failed = run_image_gen_batch(image_targets)

    print(f"\n{'─' * 40}")
    print(f"  Images: {len(succeeded)} succeeded, {len(failed)} failed")
    if failed:
        print(f"  Failed IDs: {', '.join(failed)}")

    # Clear processed IDs from queue
    if QUEUE_FILE.exists():
        try:
            queue = json.loads(QUEUE_FILE.read_text())
            remaining = [cid for cid in queue if cid not in set(succeeded)]
            QUEUE_FILE.write_text(json.dumps(remaining, indent=2))
            if not remaining:
                print("  Queue cleared.")
        except Exception:
            pass

    # Sync sheet (captures DONE + IMAGE_FAILED updates)
    sync_sheet()

    # Start image review server ONLY after ALL images are done
    if succeeded:
        start_image_review()
    else:
        print("\nAll image gen failed — skipping review server.")
        sys.exit(1)


if __name__ == "__main__":
    main()
