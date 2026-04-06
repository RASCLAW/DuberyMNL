"""
WF-UGC Pipeline Runner — Plan UGC batches and generate social proof images.

Three-phase workflow:

  Phase 0 — Status: show current ugc_pipeline.json status counts
  Phase A — Plan: creates PENDING entries in ugc_pipeline.json
  Phase B — Generate: processes PROMPT_READY entries through kie.ai
             (runs fidelity gatekeeper before dispatching to kie.ai)

Usage:
    # Show status of all UGC pipeline entries
    python tools/pipeline/run_ugc.py --status

    # Phase A: plan a batch of 5 mixed-scenario images (9:16 portrait by default)
    python tools/pipeline/run_ugc.py --plan --count 5

    # Phase A: plan 3 beach candid images (also 9:16 by default)
    python tools/pipeline/run_ugc.py --plan --count 3 --scenario BEACH_CANDID

    # Phase A: override to 4:5 feed format if needed
    python tools/pipeline/run_ugc.py --plan --count 3 --ratio 4:5

    # Phase B: generate images for all PROMPT_READY entries
    python tools/pipeline/run_ugc.py --generate

    # Phase B: generate specific IDs only
    python tools/pipeline/run_ugc.py --generate --ids UGC-20260318-001 UGC-20260318-002

    # Phase B: skip fidelity gatekeeper (use with caution)
    python tools/pipeline/run_ugc.py --generate --skip-fidelity

    # Skip review server after generation
    python tools/pipeline/run_ugc.py --generate --no-review
"""

import argparse
import json
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent.parent
TMP_DIR = PROJECT_DIR / ".tmp"
OUTPUT_DIR = PROJECT_DIR / "output" / "ugc"
UGC_PIPELINE_FILE = TMP_DIR / "ugc_pipeline.json"
VENV_PYTHON = PROJECT_DIR / ".venv" / "bin" / "python"

VALID_SCENARIOS = [
    # Person-anchor
    "SELFIE_OUTDOOR",
    "BEACH_CANDID",
    "CAR_SELFIE",
    "OOTD_STREET",
    "COMMUTE_FLEX",
    "WEEKEND_GROUP",
    "FESTIVAL",
    "FUN_RUN",
    "BIKING",
    "BADMINTON",
    "SUNSET_VIBE",
    # Product-anchor
    "COD_DELIVERY",
    "PRODUCT_HOLD",
    "REVIEW_UNBOX",
    "DASHBOARD_FLEX",
    "CAFE_TABLE",
    "BEACH_SURFACE",
    "GYM_BAG",
    "DESK_SHOT",
    "SUNSET_PRODUCT",
    "TRAVEL_FLATLAY",
    "OUTDOOR_SURFACE",
]

# Default mix for random scenario assignment when --scenario is not specified
SCENARIO_MIX = [
    "SELFIE_OUTDOOR",
    "BEACH_CANDID",
    "FUN_RUN",
    "COD_DELIVERY",
    "OOTD_STREET",
    "FESTIVAL",
    "BIKING",
    "CAR_SELFIE",
    "PRODUCT_HOLD",
    "BADMINTON",
    "COMMUTE_FLEX",
    "SUNSET_VIBE",
    "WEEKEND_GROUP",
    "SELFIE_OUTDOOR",
    "BEACH_CANDID",
    "FESTIVAL",
]

GENDER_MIX = ["male", "female", "male", "female", "male", "female", "male", "female"]


# ── Pipeline store helpers ────────────────────────────────────────────────────

def load_ugc_pipeline() -> list:
    if not UGC_PIPELINE_FILE.exists():
        return []
    return json.loads(UGC_PIPELINE_FILE.read_text())


def save_ugc_pipeline(entries: list):
    UGC_PIPELINE_FILE.write_text(json.dumps(entries, indent=2, ensure_ascii=False))


def update_ugc_entry(ugc_id: str, fields: dict):
    entries = load_ugc_pipeline()
    for entry in entries:
        if entry.get("id") == ugc_id:
            entry.update(fields)
            break
    save_ugc_pipeline(entries)


def next_ugc_id(entries: list) -> str:
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"UGC-{today}-"
    existing = [
        int(e["id"].split("-")[-1])
        for e in entries
        if e["id"].startswith(prefix) and e["id"].split("-")[-1].isdigit()
    ]
    seq = (max(existing) + 1) if existing else 1
    return f"{prefix}{seq:03d}"


# ── Phase A: Plan ─────────────────────────────────────────────────────────────

def plan_batch(count: int, scenario_filter: str | None, ratio: str, notes: str):
    entries = load_ugc_pipeline()

    new_entries = []
    for i in range(count):
        ugc_id = next_ugc_id(entries + new_entries)
        scenario = scenario_filter or SCENARIO_MIX[i % len(SCENARIO_MIX)]
        gender = GENDER_MIX[i % len(GENDER_MIX)]
        entry = {
            "id": ugc_id,
            "scenario_type": scenario,
            "subject_gender": gender,
            "product_ref": args.product or "Outback Red",
            "aspect_ratio": ratio,
            "caption_id": None,
            "notes": notes,
            "status": "PENDING",
            "prompt_file": f".tmp/{ugc_id}_ugc_prompt.json",
            "output_file": f"output/ugc/ugc_{ugc_id}.jpg",
            "drive_url": "",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "reviewed": False,
        }
        entries.append(entry)
        new_entries.append(entry)

    save_ugc_pipeline(entries)

    print(f"\nWF-UGC Plan — {count} entr{'y' if count == 1 else 'ies'} created")
    print(f"{'─' * 50}")
    for e in new_entries:
        print(f"  {e['id']}  {e['scenario_type']:<18}  {e['subject_gender']:<8}  {e['aspect_ratio']}")
    print(f"\nStatus: PENDING in .tmp/ugc_pipeline.json")
    print(f"\nNext step: run the dubery-ugc-prompt-writer skill to write prompts.")
    print(f"  Claude will process all PENDING entries in ugc_pipeline.json.")
    print(f"  Then run: python tools/pipeline/run_ugc.py --generate")


# ── Status ───────────────────────────────────────────────────────────────────

def show_status():
    entries = load_ugc_pipeline()
    if not entries:
        print("\nugc_pipeline.json is empty or does not exist.")
        return

    # Count by status
    status_counts = {}
    for e in entries:
        s = e.get("status", "UNKNOWN")
        status_counts[s] = status_counts.get(s, 0) + 1

    print(f"\nWF-UGC Pipeline Status")
    print(f"{'─' * 50}")
    print(f"  Total entries: {len(entries)}")
    for status, count in sorted(status_counts.items()):
        print(f"    {status:<20} {count}")

    # Show recent entries
    recent = entries[-10:]
    print(f"\n  Last {len(recent)} entries:")
    print(f"  {'ID':<22} {'Status':<18} {'Scenario':<18} {'Product'}")
    print(f"  {'─' * 75}")
    for e in recent:
        print(f"  {e['id']:<22} {e.get('status', '?'):<18} {e.get('scenario_type', '?'):<18} {e.get('product_ref', '?')}")


# ── Phase B: Generate ─────────────────────────────────────────────────────────

def find_generate_targets(entries: list, ids_filter: set | None) -> list:
    targets = []
    for e in entries:
        ugc_id = e["id"]
        if ids_filter and ugc_id not in ids_filter:
            continue
        if e.get("status") != "PROMPT_READY":
            continue
        prompt_path = PROJECT_DIR / e["prompt_file"]
        if not prompt_path.exists():
            print(f"  SKIP {ugc_id}: prompt file missing at {e['prompt_file']}")
            continue
        targets.append(ugc_id)
    return targets


def run_image_gen(ugc_id: str, entry: dict) -> tuple[str, bool, str, Path]:
    """Generate one UGC image. Returns (id, success, drive_url, log_path)."""
    prompt_file = PROJECT_DIR / entry["prompt_file"]
    output_file = PROJECT_DIR / entry["output_file"]
    log_file = TMP_DIR / f"ugc_{ugc_id}.log"

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    cmd = [
        str(VENV_PYTHON),
        "tools/image_gen/generate_kie.py",
        str(prompt_file),
        str(output_file),
    ]

    with open(log_file, "w") as log:
        result = subprocess.run(cmd, cwd=PROJECT_DIR, stdout=log, stderr=log)

    # Extract drive URL from log (generate_kie.py prints "Backed up to Drive: <url>")
    drive_url = ""
    try:
        log_text = log_file.read_text()
        match = re.search(r"Backed up to Drive:\s*(https?://\S+)", log_text)
        if match:
            drive_url = match.group(1).strip()
    except Exception:
        pass

    return ugc_id, result.returncode == 0, drive_url, log_file


def run_fidelity_check(ugc_id: str, entry: dict) -> tuple[str, bool, list]:
    """Run the UGC fidelity gatekeeper on a prompt. Returns (id, passed, reasons)."""
    prompt_path = PROJECT_DIR / entry["prompt_file"]
    if not prompt_path.exists():
        return ugc_id, False, [f"Prompt file missing: {entry['prompt_file']}"]

    try:
        prompt_data = json.loads(prompt_path.read_text())
    except (json.JSONDecodeError, OSError) as e:
        return ugc_id, False, [f"Cannot read prompt file: {e}"]

    reasons = []

    # FG-1: Verbatim product fidelity block
    prompt_text = prompt_data.get("prompt", "")
    if "This image MUST feature the exact style" not in prompt_text:
        reasons.append("FG-1: Missing verbatim product fidelity instruction")

    # FG-2: Reference image present and valid
    image_input = prompt_data.get("image_input", [])
    valid_paths = {
        "outback-red.png", "outback-black.png", "outback-blue.png", "outback-green.png",
        "bandits-glossy-black.png", "bandits-matte-black.png", "bandits-blue.png",
        "bandits-green.png", "bandits-tortoise.png", "rasta-brown.png", "rasta-red.png",
    }
    if not image_input:
        reasons.append("FG-2: No reference image in image_input")
    elif not any(
        any(vp in str(p) for vp in valid_paths) for p in image_input
    ):
        reasons.append(f"FG-2: image_input does not contain a valid product variant path")

    # FG-7: UGC authenticity flags
    ugc_auth = prompt_data.get("ugc_authenticity", {})
    if not ugc_auth.get("no_brand_overlays"):
        reasons.append("FG-7: ugc_authenticity.no_brand_overlays is not true")
    if not ugc_auth.get("product_logo_only_as_worn"):
        reasons.append("FG-7: ugc_authenticity.product_logo_only_as_worn is not true")
    if "No text overlays, no price banners, no brand graphics, no logo graphics" not in prompt_text:
        reasons.append("FG-7: Missing verbatim no-overlays block in prompt")

    # FG-3/4/8: Banned appearance words in product context
    # These are basic automated checks — the skill-based gatekeeper does deeper analysis
    banned_product_patterns = [
        r"(?:black|gold|silver|tortoise|matte|glossy)\s+frame",
        r"(?:acetate|polycarbonate|metal|plastic|nylon)\s+frame",
        r"(?:amber|blue|red|green|gold|dark|mirrored|tinted|smoke)\s+lens",
        r"(?:warm|cool|honey)\s*-?\s*(?:red|blue|amber|green|brown)\s*-?\s*tinted",
    ]
    # Only check the prompt narrative, skip the verbatim fidelity block
    fidelity_block = "This image MUST feature the exact style, frame shape, material, and lens color"
    check_text = prompt_text.replace(fidelity_block, "")
    for pattern in banned_product_patterns:
        match = re.search(pattern, check_text, re.IGNORECASE)
        if match:
            reasons.append(f"FG-3/4/8: Banned product appearance term found: '{match.group()}'")

    passed = len(reasons) == 0
    return ugc_id, passed, reasons


def generate_batch(ids_filter: set | None, no_review: bool, skip_fidelity: bool = False):
    entries = load_ugc_pipeline()
    entry_map = {e["id"]: e for e in entries}

    targets = find_generate_targets(entries, ids_filter)

    print(f"\nWF-UGC Generate")
    print(f"{'─' * 50}")
    print(f"  PROMPT_READY (will generate): {len(targets)}")

    if not targets:
        pending = [e["id"] for e in entries if e.get("status") == "PENDING"]
        caption_approved = [e["id"] for e in entries if e.get("status") == "CAPTION_APPROVED"]
        if pending:
            print(f"\n  {len(pending)} entr{'y' if len(pending)==1 else 'ies'} still PENDING.")
            print("  Run dubery-ugc-prompt-writer skill first to write prompts.")
        elif caption_approved:
            print(f"\n  {len(caption_approved)} entr{'y' if len(caption_approved)==1 else 'ies'} CAPTION_APPROVED.")
            print("  Run dubery-ugc-prompt-writer skill to write image prompts.")
        else:
            print("\nNothing to generate.")
        sys.exit(0)

    print(f"  IDs: {', '.join(targets)}\n")

    # Run fidelity gatekeeper before generation
    if not skip_fidelity:
        print("Running fidelity gatekeeper...")
        fidelity_passed = []
        fidelity_failed = []
        for ugc_id in targets:
            uid, passed, reasons = run_fidelity_check(ugc_id, entry_map[ugc_id])
            if passed:
                fidelity_passed.append(uid)
                print(f"  PASS  {uid}")
            else:
                fidelity_failed.append(uid)
                update_ugc_entry(uid, {
                    "status": "FIDELITY_FAILED",
                    "fidelity_verdict": "REJECT",
                    "fidelity_reasons": reasons,
                })
                print(f"  REJECT {uid}")
                for r in reasons:
                    print(f"         {r}")

        if fidelity_failed:
            print(f"\n  {len(fidelity_failed)} prompt(s) failed fidelity — skipped.")
        targets = fidelity_passed
        if not targets:
            print("\nNo prompts passed fidelity gatekeeper. Nothing to generate.")
            sys.exit(1)
        print()
    else:
        print("  (fidelity gatekeeper skipped)\n")

    # Mark all as GENERATING before dispatching
    for ugc_id in targets:
        update_ugc_entry(ugc_id, {"status": "GENERATING"})

    succeeded = []
    failed = []

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(run_image_gen, cid, entry_map[cid]): cid
            for cid in targets
        }
        for future in as_completed(futures):
            ugc_id, ok, drive_url, log_file = future.result()
            if ok:
                fields = {"status": "DONE"}
                if drive_url:
                    fields["drive_url"] = drive_url
                update_ugc_entry(ugc_id, fields)
                succeeded.append(ugc_id)
                print(f"  OK    {ugc_id}  {drive_url or '(no Drive URL)'}")
            else:
                update_ugc_entry(ugc_id, {"status": "IMAGE_FAILED"})
                failed.append(ugc_id)
                print(f"  FAIL  {ugc_id} — see .tmp/ugc_{ugc_id}.log")

    print(f"\n{'─' * 50}")
    print(f"  Done: {len(succeeded)} succeeded, {len(failed)} failed")
    if failed:
        print(f"  Failed IDs: {', '.join(failed)}")
        print(f"  Logs: .tmp/ugc_[id].log")

    if succeeded and not no_review:
        print("\nStarting UGC image review server at http://localhost:5001 ...")
        subprocess.run(
            [str(VENV_PYTHON), "tools/image_gen/image_review_server.py", "--ugc"],
            cwd=PROJECT_DIR,
        )
    elif not succeeded:
        print("\nAll jobs failed — skipping review server.")
        sys.exit(1)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="WF-UGC pipeline runner")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan", action="store_true", help="Phase A: create PENDING entries")
    mode.add_argument("--generate", action="store_true", help="Phase B: generate PROMPT_READY images")
    mode.add_argument("--status", action="store_true", help="Show pipeline status")

    # Plan-phase args
    parser.add_argument("--count", type=int, default=5, help="Number of images to plan (default: 5)")
    parser.add_argument(
        "--scenario",
        choices=VALID_SCENARIOS,
        help="Lock all planned entries to one scenario type",
    )
    parser.add_argument("--ratio", default="9:16", help="Aspect ratio (default: 9:16 portrait for mobile)")
    parser.add_argument("--notes", default="", help="Optional notes to include in entries")
    parser.add_argument("--product", default=None, help="Product ref e.g. 'Bandits Black' (default: Outback Red)")

    # Generate-phase args
    parser.add_argument("--ids", nargs="+", help="Specific UGC IDs to generate")
    parser.add_argument("--no-review", action="store_true", help="Skip starting the review server")
    parser.add_argument("--skip-fidelity", action="store_true", help="Skip fidelity gatekeeper (use with caution)")

    args = parser.parse_args()

    if args.status:
        show_status()
    elif args.plan:
        plan_batch(args.count, args.scenario, args.ratio, args.notes)
    else:
        ids_filter = set(args.ids) if args.ids else None
        generate_batch(ids_filter, args.no_review, args.skip_fidelity)


if __name__ == "__main__":
    main()
