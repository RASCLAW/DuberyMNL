"""
WF2 Regeneration Runner — REGENERATE → prompt refinement → PROMPT_READY

Finds all REGENERATE captions in pipeline.json, uses Claude to refine
the prompt based on user feedback, then sets status to PROMPT_READY
so run_wf2.py can pick them up for image generation.

Usage:
    python tools/pipeline/run_regenerate.py              # all REGENERATE entries
    python tools/pipeline/run_regenerate.py --ids 1 16   # specific IDs only
    python tools/pipeline/run_regenerate.py --generate   # also run image gen after
"""

import argparse
import fcntl
import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent.parent
TMP_DIR = PROJECT_DIR / ".tmp"
PIPELINE_FILE = TMP_DIR / "pipeline.json"
PIPELINE_LOCK = TMP_DIR / "pipeline.json.lock"


def load_pipeline():
    if not PIPELINE_FILE.exists():
        return []
    return json.loads(PIPELINE_FILE.read_text())


def update_pipeline_status(caption_id: str, fields: dict):
    """Update fields for a caption in pipeline.json (file-locked)."""
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


def find_regenerate_targets(captions, ids_filter=None):
    targets = []
    for c in captions:
        if c.get("status") != "REGENERATE":
            continue
        cid = str(c["id"])
        if ids_filter and cid not in ids_filter:
            continue
        targets.append(c)
    return targets


def refine_prompt(caption: dict) -> bool:
    """Use Claude to refine the prompt based on regeneration instructions."""
    cid = str(caption["id"])
    instructions = caption.get("regeneration_instructions", "")
    prompt_file = TMP_DIR / f"{cid}_prompt_structured.json"
    original_prompt_text = caption.get("prompt", "")

    if not instructions:
        print(f"  SKIP #{cid}: no regeneration instructions")
        return False

    # Read existing structured prompt if available
    existing_prompt = ""
    if prompt_file.exists():
        existing_prompt = prompt_file.read_text()

    # Build the refinement prompt for Claude
    refinement_prompt = f"""You are refining an image generation prompt for a DuberyMNL Facebook ad.

The user reviewed the generated image and wants changes. Your job is to update the
structured prompt JSON to incorporate their feedback while keeping everything else intact.

CAPTION ID: {cid}

USER'S REGENERATION INSTRUCTIONS:
{instructions}

EXISTING STRUCTURED PROMPT (JSON):
{existing_prompt if existing_prompt else "No structured prompt found."}

ORIGINAL NATURAL LANGUAGE PROMPT:
{original_prompt_text[:2000] if original_prompt_text else "Not available."}

RULES:
1. Output ONLY valid JSON — the updated structured prompt. No explanation, no markdown fences.
2. Preserve all fields from the existing prompt that the user did NOT ask to change.
3. Apply the user's instructions precisely:
   - If they say "change scene to X" → update scene.location and scene.atmosphere
   - If they say "fix overlays" → update the overlays section
   - If they say "change header/headline to X" → update overlays.headline.text
   - If they say "remove X" → remove that element
   - If they say "change price to X" → update overlays.price and fixed_strings
   - If they say "use bundle pricing" → adjust price overlay for bundle
   - If they say "zoom in" → adjust scene framing notes
   - If they say "change person/clothes" → update the subject description
   - If they say "be more creative with overlays" → redesign overlay layout/styles
   - If they say "add bubbles for products" → add bubble overlay entries
4. Keep image_input and api_parameters if they exist in the original.
5. Keep product reference images unchanged unless explicitly asked.
6. The output must be parseable JSON matching the existing prompt structure.
"""

    print(f"  Refining prompt for #{cid}...")
    try:
        env = os.environ.copy()
        env.pop("CLAUDECODE", None)
        result = subprocess.run(
            ["claude", "--print", refinement_prompt],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
        )

        output = result.stdout.strip()

        # Extract JSON from output (may have surrounding text)
        start = output.find("{")
        end = output.rfind("}") + 1
        if start < 0 or end <= start:
            print(f"  ERROR #{cid}: no JSON found in Claude output")
            print(f"  Output: {output[:300]}")
            return False

        json_str = output[start:end]
        refined = json.loads(json_str)

        # Back up old prompt
        if prompt_file.exists():
            backup = TMP_DIR / f"{cid}_prompt_structured.prev.json"
            backup.write_text(prompt_file.read_text())

        # Write refined prompt
        prompt_file.write_text(json.dumps(refined, indent=2, ensure_ascii=False))
        print(f"  OK #{cid}: prompt refined and saved")
        return True

    except json.JSONDecodeError as e:
        print(f"  ERROR #{cid}: invalid JSON from Claude — {e}")
        return False
    except subprocess.TimeoutExpired:
        print(f"  ERROR #{cid}: Claude timed out (120s)")
        return False
    except Exception as e:
        print(f"  ERROR #{cid}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Regenerate images from review feedback")
    parser.add_argument("--ids", nargs="+", help="Specific caption IDs to regenerate")
    parser.add_argument("--generate", action="store_true",
                        help="Also run image generation (run_wf2.py) after prompt refinement")
    args = parser.parse_args()

    captions = load_pipeline()
    ids_filter = set(args.ids) if args.ids else None
    targets = find_regenerate_targets(captions, ids_filter)

    print(f"\nWF2 Regeneration Runner")
    print(f"{'─' * 40}")
    print(f"  REGENERATE entries: {len(targets)}")

    if not targets:
        print("\nNothing to regenerate.")
        sys.exit(0)

    for t in targets:
        cid = str(t["id"])
        instr = t.get("regeneration_instructions", "")[:80]
        print(f"  #{cid}: {instr}{'...' if len(t.get('regeneration_instructions', '')) > 80 else ''}")

    print(f"\nPhase 1 — Prompt refinement...")
    succeeded = []
    failed = []

    for caption in targets:
        cid = str(caption["id"])
        if refine_prompt(caption):
            update_pipeline_status(cid, {"status": "PROMPT_READY"})
            succeeded.append(cid)
        else:
            update_pipeline_status(cid, {"status": "REGENERATE_FAILED"})
            failed.append(cid)

    print(f"\n{'─' * 40}")
    print(f"  Refined: {len(succeeded)}, Failed: {len(failed)}")
    if succeeded:
        print(f"  Ready for generation: {', '.join(succeeded)}")
    if failed:
        print(f"  Failed: {', '.join(failed)}")

    if succeeded and args.generate:
        print(f"\nPhase 2 — Running image generation for {len(succeeded)} caption(s)...")
        venv_python = PROJECT_DIR / ".venv" / "bin" / "python"
        cmd = [
            str(venv_python),
            "tools/pipeline/run_wf2.py",
            "--ids",
        ] + succeeded
        subprocess.run(cmd, cwd=PROJECT_DIR)
    elif succeeded and not args.generate:
        print(f"\nPrompts are ready. Run image generation with:")
        print(f"  python tools/pipeline/run_wf2.py --ids {' '.join(succeeded)}")


if __name__ == "__main__":
    main()
