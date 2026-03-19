"""
WF2 Post-Review Orchestrator

Runs after caption review to chain WF2a (prompt writing) → WF2b (image gen).
Can be run manually after caption review or triggered automatically.

Smart detection: finds APPROVED captions that don't have a prompt file yet.
This naturally excludes old IMAGE_APPROVED/DONE captions (they already have prompts).

Usage:
    python tools/pipeline/run_post_review.py
    python tools/pipeline/run_post_review.py --ids 20260318-001 20260318-002
    python tools/pipeline/run_post_review.py --dry-run
    python tools/pipeline/run_post_review.py --prompts-only
    python tools/pipeline/run_post_review.py --images-only
    python tools/pipeline/run_post_review.py --delay 180
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


def find_prompt_targets(captions, ids_filter=None):
    """APPROVED captions that don't have a prompt file yet (WF2a targets)."""
    targets = []
    for c in captions:
        cid = str(c["id"])
        if ids_filter and cid not in ids_filter:
            continue
        if c.get("status") != "APPROVED":
            continue
        prompt_file = TMP_DIR / f"{cid}_prompt_structured.json"
        if not prompt_file.exists():
            targets.append(cid)
    return targets


def find_image_targets(captions, ids_filter=None):
    """PROMPT_READY captions that have prompt files (WF2b targets for --images-only)."""
    targets = []
    for c in captions:
        cid = str(c["id"])
        if ids_filter and cid not in ids_filter:
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


def run_prompt_writer(caption_id):
    """Call Claude CLI to run dubery-prompt-writer for one caption."""
    prompt = (
        f"run dubery-prompt-writer for caption {caption_id}. "
        f"Process only caption ID {caption_id} from .tmp/pipeline.json. "
        f"Generate the structured NB2 prompt, save to .tmp/{caption_id}_prompt_structured.json, "
        f"and update status to PROMPT_READY in pipeline.json."
    )
    result = subprocess.run(
        ["claude", "--print", "--dangerously-skip-permissions", prompt],
        cwd=PROJECT_DIR,
        env=_claude_env(),
    )
    return result.returncode == 0


def run_prompt_parser(caption_id):
    """Call Claude CLI to run dubery-prompt-parser for one caption."""
    prompt = (
        f"run dubery-prompt-parser for caption {caption_id}. "
        f"Read .tmp/{caption_id}_prompt_structured.json, parse it to the correct generate_kie.py schema, "
        f"and overwrite .tmp/{caption_id}_prompt_structured.json with the parsed JSON."
    )
    result = subprocess.run(
        ["claude", "--print", "--dangerously-skip-permissions", prompt],
        cwd=PROJECT_DIR,
        env=_claude_env(),
    )
    return result.returncode == 0


def run_single_image_gen(caption_id):
    """Run image gen for one caption via run_wf2.py (no review, no sync)."""
    result = subprocess.run(
        [str(VENV_PYTHON), "tools/pipeline/run_wf2.py",
         "--ids", caption_id,
         "--no-review", "--no-sync"],
        cwd=PROJECT_DIR,
    )
    return result.returncode == 0


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
    parser.add_argument("--dry-run", action="store_true", help="Show what would run without executing")
    parser.add_argument("--prompts-only", action="store_true", help="Run WF2a only, skip image gen")
    parser.add_argument("--images-only", action="store_true", help="Run WF2b only, skip prompt writing")
    parser.add_argument("--delay", type=int, default=300, help="Seconds between image gen jobs (default: 300)")
    args = parser.parse_args()

    captions = load_pipeline()

    # ID filter: --ids > queue file > smart detection
    ids_filter = None
    if args.ids:
        ids_filter = set(args.ids)
    elif QUEUE_FILE.exists():
        queue = json.loads(QUEUE_FILE.read_text())
        if queue:
            ids_filter = set(queue)
            print(f"Using session queue: {len(ids_filter)} IDs from wf2_queue.json")

    print(f"\nWF2 Post-Review Orchestrator")
    print(f"{'─' * 40}")

    if args.images_only:
        targets = find_image_targets(captions, ids_filter)
        print(f"  PROMPT_READY (will generate images): {len(targets)}")
    else:
        targets = find_prompt_targets(captions, ids_filter)
        print(f"  New APPROVED (no prompt yet): {len(targets)}")

    if targets:
        print(f"  IDs: {', '.join(targets)}")

    if not targets:
        if args.images_only:
            print("\nNo PROMPT_READY captions with prompt files found.")
            print("Run without --images-only to write prompts first.")
        else:
            print("\nNo new APPROVED captions to process.")
            print("All APPROVED captions already have prompts — use --images-only if image gen is still needed.")
        sys.exit(0)

    if args.dry_run:
        print("\nDRY RUN — no actions taken")
        if not args.images_only:
            print(f"  Would run dubery-prompt-writer + parser for {len(targets)} caption(s)")
        if not args.prompts_only:
            print(f"  Would generate {len(targets)} image(s) with {args.delay}s intervals")
        sys.exit(0)

    # ── WF2a: Prompt writing ──────────────────────────────────────────────────
    prompt_succeeded = []
    prompt_failed = []

    if not args.images_only:
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

        if args.prompts_only:
            print("\n--prompts-only: stopping before image gen.")
            sys.exit(0 if not prompt_failed else 1)

        image_targets = prompt_succeeded
    else:
        image_targets = targets

    if not image_targets:
        print("\nNo captions ready for image gen. Exiting.")
        sys.exit(1)

    # ── WF2b: Image generation (sequential with delay) ────────────────────────
    print(f"\nWF2b — Generating images ({len(image_targets)} captions, {args.delay}s intervals)...")
    image_succeeded = []
    image_failed = []

    for i, cid in enumerate(image_targets):
        print(f"\n  [{i + 1}/{len(image_targets)}] Generating image for #{cid}...")
        ok = run_single_image_gen(cid)
        if ok:
            image_succeeded.append(cid)
            print(f"  OK  #{cid}")
        else:
            image_failed.append(cid)
            print(f"  FAIL #{cid}")

        if i < len(image_targets) - 1:
            print(f"\n  Waiting {args.delay}s before next image gen job...")
            time.sleep(args.delay)

    print(f"\n{'─' * 40}")
    print(f"  Images: {len(image_succeeded)} succeeded, {len(image_failed)} failed")
    if image_failed:
        print(f"  Failed IDs: {', '.join(image_failed)}")

    # Clear processed IDs from queue
    if QUEUE_FILE.exists():
        try:
            queue = json.loads(QUEUE_FILE.read_text())
            remaining = [cid for cid in queue if cid not in set(image_succeeded)]
            QUEUE_FILE.write_text(json.dumps(remaining, indent=2))
            if not remaining:
                print("  Queue cleared.")
        except Exception:
            pass

    # Sync sheet (full batch — captures DONE + IMAGE_FAILED updates)
    sync_sheet()

    # Start image review server if any images were generated
    if image_succeeded:
        start_image_review()
    else:
        print("\nAll image gen failed — skipping review server.")
        sys.exit(1)


if __name__ == "__main__":
    main()
