"""
WF2 Regeneration Runner — REGENERATE → edit or full regen → DONE

Two modes:
  EDIT:  Send existing image + user instructions to NB2. Small fixes only.
  REGEN: Rewrite prompt from scratch via Claude, generate entirely new image.

Auto-classification reads the user's instructions and picks the right mode.

Usage:
    python tools/pipeline/run_regenerate.py                    # auto-classify all
    python tools/pipeline/run_regenerate.py --ids 1 16         # specific IDs
    python tools/pipeline/run_regenerate.py --mode edit        # force edit mode
    python tools/pipeline/run_regenerate.py --mode regen       # force full regen
    python tools/pipeline/run_regenerate.py --dry-run          # classify only, no generation
"""

import argparse
try:
    import fcntl
except ImportError:
    fcntl = None
    import msvcrt
import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent.parent
TMP_DIR = PROJECT_DIR / ".tmp"
OUTPUT_DIR = PROJECT_DIR / "contents" / "new"
PIPELINE_FILE = TMP_DIR / "pipeline.json"
PIPELINE_LOCK = TMP_DIR / "pipeline.json.lock"
VENV_PYTHON = PROJECT_DIR / ".venv" / "bin" / "python"

# Keywords that suggest a full regen is needed
REGEN_KEYWORDS = [
    "change the scene", "change scene", "different scene", "new scene",
    "change the setting", "change setting", "different location",
    "change the person", "different person", "change the subject",
    "change the concept", "completely different", "start over",
    "wrong product", "change the product", "different product",
    "new concept", "redo everything", "full redo",
]

# Keywords that suggest an edit is sufficient
EDIT_KEYWORDS = [
    "move", "adjust", "fix", "change the text", "change text",
    "change the header", "change header", "change headline",
    "change the subheader", "change subheader",
    "remove", "add", "make bigger", "make smaller",
    "more creative", "less", "too much", "not enough",
    "higher", "lower", "left", "right", "center",
    "replace the sunglasses", "replace sunglasses",
    "zoom in", "zoom out", "crop", "resize",
    "fix the overlay", "fix overlay", "change overlay",
    "change the font", "change font", "change color",
]


def load_pipeline():
    if not PIPELINE_FILE.exists():
        return []
    return json.loads(PIPELINE_FILE.read_text())


def update_pipeline_status(caption_id: str, fields: dict):
    """Update fields for a caption in pipeline.json (file-locked)."""
    if not PIPELINE_FILE.exists():
        return
    with open(PIPELINE_LOCK, "w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX) if fcntl else msvcrt.locking(lf.fileno(), msvcrt.LK_LOCK, 1)
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
            fcntl.flock(lf, fcntl.LOCK_UN) if fcntl else msvcrt.locking(lf.fileno(), msvcrt.LK_UNLCK, 1)


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


def classify_mode(instructions: str) -> str:
    """Classify whether instructions need EDIT or REGEN mode."""
    lower = instructions.lower()

    regen_score = sum(1 for kw in REGEN_KEYWORDS if kw in lower)
    edit_score = sum(1 for kw in EDIT_KEYWORDS if kw in lower)

    # If explicit scene/concept change, always regen
    if regen_score > 0 and edit_score == 0:
        return "regen"

    # If only small adjustments, edit
    if edit_score > 0 and regen_score == 0:
        return "edit"

    # Mixed signals -- if scene change is mentioned, regen wins
    if regen_score > 0:
        return "regen"

    # Default to edit (most feedback is small fixes)
    return "edit"


def find_existing_image(caption_id: str) -> str | None:
    """Find the existing generated image for a caption."""
    for ext in [".jpg", ".jpeg", ".png"]:
        path = OUTPUT_DIR / f"dubery_{caption_id}{ext}"
        if path.exists():
            return str(path)
    return None


def get_product_refs(caption: dict) -> list[str]:
    """Get product reference image paths from the structured prompt."""
    cid = str(caption["id"])
    prompt_file = TMP_DIR / f"{cid}_prompt_structured.json"
    if prompt_file.exists():
        prompt_data = json.loads(prompt_file.read_text())
        image_input = prompt_data.get("image_input", [])
        # Filter to only product refs (not the logo)
        return [p for p in image_input if "dubery-logo" not in p]
    return []


def run_edit(caption: dict) -> bool:
    """Edit mode: send existing image + instructions to NB2."""
    cid = str(caption["id"])
    instructions = caption.get("regeneration_instructions", "")

    existing_image = find_existing_image(cid)
    if not existing_image:
        print(f"  ERROR #{cid}: no existing image found for edit mode")
        return False

    product_refs = get_product_refs(caption)

    # Build image_input: existing image first, then product refs
    image_input = [existing_image] + product_refs
    # Add logo
    logo = str(PROJECT_DIR / "dubery-landing" / "assets" / "dubery-logo.png")
    if os.path.exists(logo):
        image_input.append(logo)

    # Build edit prompt
    edit_prompt = f"""Edit this existing ad image based on the following instructions.
Keep everything that is not mentioned in the instructions exactly as it is.
Only change what is explicitly requested.

INSTRUCTIONS: {instructions}

IMPORTANT:
- Product appearance must match the reference image exactly
- All text must be sharp, clean, and fully legible
- Maintain the same 4:5 vertical format
- Do not change elements that were not mentioned in the instructions"""

    # Write prompt file and config sidecar
    prompt_path = TMP_DIR / f"{cid}_edit_prompt.txt"
    config_path = TMP_DIR / f"{cid}_edit_config.json"

    prompt_path.write_text(edit_prompt)
    config_path.write_text(json.dumps({
        "image_input": image_input,
        "api_parameters": {
            "aspect_ratio": "4:5",
            "resolution": "1K",
            "output_format": "jpg"
        }
    }, indent=2))

    # Backup existing image
    backup_path = OUTPUT_DIR / f"dubery_{cid}_pre_edit{Path(existing_image).suffix}"
    if not backup_path.exists():
        import shutil
        shutil.copy2(existing_image, backup_path)
        print(f"  Backed up original to {backup_path.name}")

    # Run generate_kie.py with the edit prompt
    output_file = OUTPUT_DIR / f"dubery_{cid}.jpg"
    print(f"  Sending to NB2 for edit (existing image + instructions)...")

    cmd = [
        str(VENV_PYTHON),
        "tools/image_gen/generate_kie.py",
        str(prompt_path),
        str(output_file),
    ]

    result = subprocess.run(cmd, cwd=PROJECT_DIR, capture_output=True, text=True, timeout=600)

    if result.returncode == 0:
        print(f"  OK #{cid}: edit complete")
        # Clean up temp files
        prompt_path.unlink(missing_ok=True)
        config_path.unlink(missing_ok=True)
        return True
    else:
        print(f"  ERROR #{cid}: edit failed")
        print(f"  {result.stderr[:300]}")
        return False


def run_regen(caption: dict) -> bool:
    """Full regen mode: rewrite prompt via Claude, then generate new image."""
    cid = str(caption["id"])
    instructions = caption.get("regeneration_instructions", "")
    prompt_file = TMP_DIR / f"{cid}_prompt_structured.json"
    original_prompt_text = caption.get("prompt", "")

    if not instructions:
        print(f"  SKIP #{cid}: no regeneration instructions")
        return False

    existing_prompt = ""
    if prompt_file.exists():
        existing_prompt = prompt_file.read_text()

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
3. Apply the user's instructions precisely.
4. Keep image_input and api_parameters if they exist in the original.
5. Keep product reference images unchanged unless explicitly asked.
6. The output must be parseable JSON matching the existing prompt structure.
7. PRODUCT FIDELITY (CRITICAL — non-negotiable):
   - Do NOT add frame color, lens color, material, or texture descriptions to
     render_notes, scene.product_placement, visual_mood, or objects_in_scene.
   - render_notes MUST follow this 5-field template:
     "POSITION: [...]. ANGLE: [...]. LIGHTING: [...].
      LOGO: Dubery logo on temple arm must be sharp and legible.
      REFERENCE: Frame shape, color, material, and lens appearance are
      dictated entirely by the reference image."
   - The reference image is the ONLY authority on product appearance.
8. HEADLINE RULE: Use the product model name as the headline
   (e.g., "DUBERY OUTBACK", "DUBERY BANDITS SERIES").
   The caption hook becomes the supporting_line.
9. LENS REFLECTION RULE: Do NOT describe lens reflections at all.
   No reflection instructions in any field. The reference image dictates how the lens looks.
10. HEADLINE POSITION: Top 15-20% of frame, immediately below logo. No drifting to mid-frame.
"""

    print(f"  Rewriting prompt for #{cid} via Claude...")
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
        start = output.find("{")
        end = output.rfind("}") + 1
        if start < 0 or end <= start:
            print(f"  ERROR #{cid}: no JSON found in Claude output")
            return False

        json_str = output[start:end]
        refined = json.loads(json_str)

        # Back up old prompt
        if prompt_file.exists():
            backup = TMP_DIR / f"{cid}_prompt_structured.prev.json"
            backup.write_text(prompt_file.read_text())

        prompt_file.write_text(json.dumps(refined, indent=2, ensure_ascii=False))
        print(f"  OK #{cid}: prompt rewritten")

        # Now generate the image
        output_file = OUTPUT_DIR / f"dubery_{cid}.jpg"

        # Backup existing image if it exists
        existing = find_existing_image(cid)
        if existing:
            backup_path = OUTPUT_DIR / f"dubery_{cid}_pre_regen{Path(existing).suffix}"
            if not backup_path.exists():
                import shutil
                shutil.copy2(existing, backup_path)

        print(f"  Generating new image for #{cid}...")
        cmd = [
            str(VENV_PYTHON),
            "tools/image_gen/generate_kie.py",
            str(prompt_file),
            str(output_file),
        ]
        gen_result = subprocess.run(cmd, cwd=PROJECT_DIR, capture_output=True, text=True, timeout=600)

        if gen_result.returncode == 0:
            print(f"  OK #{cid}: new image generated")
            return True
        else:
            print(f"  ERROR #{cid}: image generation failed")
            print(f"  {gen_result.stderr[:300]}")
            return False

    except json.JSONDecodeError as e:
        print(f"  ERROR #{cid}: invalid JSON from Claude — {e}")
        return False
    except subprocess.TimeoutExpired:
        print(f"  ERROR #{cid}: timed out")
        return False
    except Exception as e:
        print(f"  ERROR #{cid}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Regenerate images from review feedback")
    parser.add_argument("--ids", nargs="+", help="Specific caption IDs to regenerate")
    parser.add_argument("--mode", choices=["auto", "edit", "regen"], default="auto",
                        help="Force edit or regen mode (default: auto-classify)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Classify and show plan without generating")
    args = parser.parse_args()

    captions = load_pipeline()
    ids_filter = set(args.ids) if args.ids else None
    targets = find_regenerate_targets(captions, ids_filter)

    print(f"\nWF2 Regeneration Runner")
    print(f"{'─' * 50}")
    print(f"  REGENERATE entries: {len(targets)}")
    print(f"  Mode: {args.mode}")

    if not targets:
        print("\nNothing to regenerate.")
        sys.exit(0)

    # Classify each target
    plan = []
    for t in targets:
        cid = str(t["id"])
        instructions = t.get("regeneration_instructions", "")

        if args.mode == "auto":
            # Use mode from review UI if set, otherwise classify from keywords
            stored_mode = t.get("regeneration_mode", "")
            if stored_mode in ("edit", "regen"):
                mode = stored_mode
            else:
                mode = classify_mode(instructions)
        else:
            mode = args.mode

        has_image = find_existing_image(cid) is not None

        # Can't edit without an existing image
        if mode == "edit" and not has_image:
            print(f"  #{cid}: no existing image, forcing REGEN")
            mode = "regen"

        plan.append({"caption": t, "mode": mode, "has_image": has_image})
        instr_short = instructions[:70] + ("..." if len(instructions) > 70 else "")
        print(f"  #{cid}: [{mode.upper()}] {instr_short}")

    if args.dry_run:
        print(f"\n{'─' * 50}")
        edit_count = sum(1 for p in plan if p["mode"] == "edit")
        regen_count = sum(1 for p in plan if p["mode"] == "regen")
        print(f"  Plan: {edit_count} edits, {regen_count} full regens")
        print("  (dry run — no changes made)")
        sys.exit(0)

    print(f"\nProcessing...")
    succeeded = []
    failed = []

    for item in plan:
        caption = item["caption"]
        mode = item["mode"]
        cid = str(caption["id"])

        print(f"\n  [{mode.upper()}] #{cid}")

        if mode == "edit":
            ok = run_edit(caption)
        else:
            ok = run_regen(caption)

        if ok:
            update_pipeline_status(cid, {
                "status": "DONE",
                "regeneration_instructions": "",
            })
            succeeded.append(cid)
        else:
            update_pipeline_status(cid, {"status": "REGENERATE_FAILED"})
            failed.append(cid)

    print(f"\n{'─' * 50}")
    print(f"  Succeeded: {len(succeeded)}, Failed: {len(failed)}")
    if succeeded:
        print(f"  Done: {', '.join(succeeded)}")
    if failed:
        print(f"  Failed: {', '.join(failed)}")


if __name__ == "__main__":
    main()
