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
import fcntl
import json
import subprocess
import sys
import time
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent.parent
TMP_DIR = PROJECT_DIR / ".tmp"
OUTPUT_DIR = PROJECT_DIR / "output" / "images"
PIPELINE_FILE = TMP_DIR / "pipeline.json"
PIPELINE_LOCK = TMP_DIR / "pipeline.json.lock"
REJECTED_FILE = TMP_DIR / "rejected_captions.json"
VENV_PYTHON = PROJECT_DIR / ".venv" / "bin" / "python"
MAX_GATE_ATTEMPTS = 2


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


def run_gatekeeper(caption_id):
    """Run the prompt validator before image generation.
    Returns verdict dict. Defaults to PASS on validator failure (non-blocking)."""
    prompt_file = TMP_DIR / f"{caption_id}_prompt_structured.json"
    gate_result_file = TMP_DIR / f"{caption_id}_gate_result.json"

    gate_prompt = (
        f"run dubery-prompt-validator on {prompt_file}. "
        f"Output only the raw JSON verdict."
    )

    try:
        result = subprocess.run(
            ["claude", "--print", gate_prompt],
            cwd=PROJECT_DIR, capture_output=True, text=True, timeout=120
        )
        # Extract JSON from output (may have surrounding text)
        output = result.stdout.strip()
        start = output.find("{")
        end = output.rfind("}") + 1
        if start >= 0 and end > start:
            verdict = json.loads(output[start:end])
            gate_result_file.write_text(json.dumps(verdict, indent=2))
            return verdict
    except Exception as e:
        print(f"  Gatekeeper error for #{caption_id} ({e}) — defaulting to PASS")

    return {"verdict": "PASS"}


def update_pipeline_status(caption_id, fields):
    """Update fields for a caption in pipeline.json (file-locked for thread safety)."""
    if not PIPELINE_FILE.exists():
        return
    with open(PIPELINE_LOCK, "w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        try:
            captions = json.loads(PIPELINE_FILE.read_text())
            PIPELINE_FILE.with_suffix(".json.bak").write_text(
                json.dumps(captions, indent=2, ensure_ascii=False)
            )
            for c in captions:
                if str(c.get("id")) == caption_id:
                    c.update(fields)
                    break
            PIPELINE_FILE.write_text(json.dumps(captions, indent=2, ensure_ascii=False))
        finally:
            fcntl.flock(lf, fcntl.LOCK_UN)


def run_prompt_writer(caption_id):
    """Call dubery-prompt-writer to fix a prompt using the validator feedback file."""
    regen_prompt = (
        f"Run dubery-prompt-writer for caption {caption_id}. "
        f"A validator feedback file exists at .tmp/{caption_id}_validator_feedback.json — "
        f"read it before generating and fix only the flagged issues."
    )
    result = subprocess.run(
        ["claude", "--print", regen_prompt],
        cwd=PROJECT_DIR, capture_output=True, text=True, timeout=300
    )
    return result.returncode == 0


def run_gatekeeper_loop(caption_id):
    """Run gatekeeper → retry with prompt writer if needed. Returns True if ready for image gen."""
    feedback_file = TMP_DIR / f"{caption_id}_validator_feedback.json"
    log_file = TMP_DIR / f"generate_{caption_id}.log"

    gate_verdict = "REGENERATE"
    reasons = []

    for attempt in range(1, MAX_GATE_ATTEMPTS + 1):
        print(f"  Gatekeeper check #{caption_id} (attempt {attempt}/{MAX_GATE_ATTEMPTS})...")
        verdict = run_gatekeeper(caption_id)
        gate_verdict = verdict.get("verdict", "PASS")

        if gate_verdict != "REGENERATE":
            feedback_file.write_text("{}")  # clear feedback on pass/patch
            break

        reasons = verdict.get("regenerate_reasons", [])
        print(f"  GATEKEEPER FAIL #{caption_id} — {'; '.join(reasons)}")

        if attempt < MAX_GATE_ATTEMPTS:
            feedback_file.write_text(json.dumps(verdict, indent=2))
            print(f"  Sending to prompt writer for fixes (attempt {attempt}/{MAX_GATE_ATTEMPTS})...")
            ok = run_prompt_writer(caption_id)
            if not ok:
                print(f"  Prompt writer failed for #{caption_id} — marking PROMPT_FAILED")
                update_pipeline_status(caption_id, {"status": "PROMPT_FAILED", "gate_failure": reasons})
                return False

    if gate_verdict == "REGENERATE":
        print(f"  Max attempts reached for #{caption_id} — marking PROMPT_FAILED")
        update_pipeline_status(caption_id, {"status": "PROMPT_FAILED", "gate_failure": reasons})
        return False

    if gate_verdict == "PATCH":
        print(f"  Gatekeeper patched #{caption_id} — proceeding to generate")
    else:
        print(f"  Gatekeeper PASS #{caption_id} — ready for image gen")

    return True


def run_image_gen(caption_id):
    """Run generate_kie.py for a single caption (gatekeeper already passed)."""
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
    """Move successfully regenerated IMAGE_REJECTED entries from rejected → pipeline (file-locked)."""
    if not REJECTED_FILE.exists() or not succeeded_ids:
        return

    with open(PIPELINE_LOCK, "w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        try:
            rejected = json.loads(REJECTED_FILE.read_text())
            pipeline = json.loads(PIPELINE_FILE.read_text())

            to_move = [c for c in rejected if str(c["id"]) in succeeded_ids]
            if not to_move:
                return

            for c in to_move:
                c["status"] = "DONE"
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
        finally:
            fcntl.flock(lf, fcntl.LOCK_UN)
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

    # Phase 1: Run gatekeeper sequentially (LLM-bound, no parallelism needed)
    print(f"\nPhase 1 — Gatekeeper validation ({len(targets)} captions, sequential)...")
    gate_passed = []
    gate_failed = []

    for cid in targets:
        if run_gatekeeper_loop(cid):
            gate_passed.append(cid)
        else:
            gate_failed.append(cid)

    if gate_failed:
        print(f"\n  Gatekeeper: {len(gate_passed)} passed, {len(gate_failed)} failed")
        print(f"  Failed IDs: {', '.join(gate_failed)}")

    if not gate_passed:
        print("\nAll prompts failed gatekeeper. Nothing to generate.")
        sys.exit(1)

    # Phase 2: Generate images sequentially (wait for each download before next)
    print(f"\nPhase 2 — Generating {len(gate_passed)} image(s) sequentially...")
    print(f"  IDs: {', '.join(gate_passed)}\n")

    succeeded = []
    failed = list(gate_failed)

    for i, cid in enumerate(gate_passed):
        print(f"  [{i + 1}/{len(gate_passed)}] Generating image for #{cid}...")
        cid, ok, log_file = run_image_gen(cid)
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
