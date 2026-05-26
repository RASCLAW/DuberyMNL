"""
Experiment Mode batch orchestrator.

Reads a run directory (created by /api/experiment/start), generates N images
by calling generate_vertex.py once per shot, with deterministic pacing to dodge
Vertex's 429 quota. Updates run.json after each shot for the polling endpoint.

Called in-process from command-center/app.py via run_batch(run_dir, state_dict).
Also runnable standalone for debugging:

    python tools/image_gen/batch_experiment.py --run-dir contents/experiments/<run_id>

Deterministic only -- no AI reasoning inside this script.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
GENERATE_VERTEX = PROJECT_ROOT / "tools" / "image_gen" / "generate_vertex.py"

# Pacing config -- matched to the manual workflow that worked tonight (Optikhaus run)
PACE_SLEEP_SECS = 30        # gap between successful calls when count > 5
PACE_THRESHOLD = 5          # only sleep when batch is "large"
QUOTA_BACKOFF_SECS = 45     # extra sleep when 429 / RESOURCE_EXHAUSTED hits
BRAND_CONTEXT_MAX_CHARS = 800


def _truncate(s: str, n: int) -> str:
    s = (s or "").strip()
    if len(s) <= n:
        return s
    return s[:n].rstrip() + " ..."


def _build_prompt(brand_context: str, aspect_ratio: str, ref_abs_path: str) -> dict:
    """v1 template -- bare and consistent. Mode/type are recorded in run.json but
    do not branch the prompt; that's a v2 lever."""
    ctx = _truncate(brand_context, BRAND_CONTEXT_MAX_CHARS)
    text = (
        f"{ctx}\n\n"
        "Create an ad-ready product shot. Reference image attached for product "
        "fidelity. Composition: clean, retail-forward, no competing branding. "
        f"Aspect ratio: {aspect_ratio}."
    )
    return {
        "prompt": text,
        "image_input": [ref_abs_path],
        "aspect_ratio": aspect_ratio,
    }


def _write_state(run_dir: Path, state: dict) -> None:
    """Atomic-ish write of run.json. Best effort -- if it fails, polling endpoint
    falls back to in-memory state."""
    try:
        manifest = {k: v for k, v in state.items() if k != "run_dir"}
        (run_dir / "run.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except Exception as e:
        print(f"[batch_experiment] state write failed: {e}", file=sys.stderr, flush=True)


def _run_one(prompt_path: Path, output_path: Path) -> tuple[bool, str, str]:
    """Invoke generate_vertex.py. Returns (ok, stdout, stderr)."""
    try:
        proc = subprocess.run(
            [sys.executable, str(GENERATE_VERTEX), str(prompt_path), str(output_path)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=str(PROJECT_ROOT),
        )
        return proc.returncode == 0, proc.stdout or "", proc.stderr or ""
    except Exception as e:
        return False, "", f"subprocess raised: {e}"


def _is_quota_error(stderr: str) -> bool:
    s = (stderr or "").upper()
    return "429" in s or "RESOURCE_EXHAUSTED" in s or "QUOTA" in s


def run_batch(run_dir: str | Path, state: dict) -> None:
    """Main worker. Mutates `state` in place and writes run.json after each shot.

    state must contain: client_slug, count, aspect_ratio, brand_context,
    product_refs (relative to run_dir), and the manifest fields seeded by Flask.
    """
    run_dir_p = Path(run_dir)
    refs_dir = run_dir_p / "refs"

    slug = state.get("client_slug", "experiment")
    count = int(state.get("count", 0))
    aspect_ratio = state.get("aspect_ratio", "1:1")
    brand_context = state.get("brand_context", "")
    refs_rel = state.get("product_refs") or []

    if count < 1 or not refs_rel:
        state["status"] = "failed"
        state["errors"].append("invalid payload: count<1 or no refs")
        _write_state(run_dir_p, state)
        return

    # Resolve refs to absolute paths
    ref_abs: list[Path] = []
    for rel in refs_rel:
        p = (run_dir_p / rel).resolve()
        if not p.exists():
            state["status"] = "failed"
            state["errors"].append(f"ref missing on disk: {rel}")
            _write_state(run_dir_p, state)
            return
        ref_abs.append(p)

    state["status"] = "running"
    state["current_stage"] = "starting"
    _write_state(run_dir_p, state)

    pace = count > PACE_THRESHOLD

    for i in range(1, count + 1):
        ref = ref_abs[(i - 1) % len(ref_abs)]
        prompt_dict = _build_prompt(brand_context, aspect_ratio, str(ref))
        prompt_name = f"{i:02d}_{slug}_prompt.json"
        prompt_path = run_dir_p / prompt_name
        prompt_path.write_text(
            json.dumps(prompt_dict, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        output_path = run_dir_p / f"{i:02d}_{slug}.png"
        state["current_stage"] = f"generating {i}/{count}"
        _write_state(run_dir_p, state)

        ok, _, err = _run_one(prompt_path, output_path)

        if not ok and _is_quota_error(err):
            print(f"[batch_experiment] quota hit on shot {i}; backing off {QUOTA_BACKOFF_SECS}s", file=sys.stderr, flush=True)
            state["current_stage"] = f"quota backoff on {i}/{count}"
            _write_state(run_dir_p, state)
            time.sleep(QUOTA_BACKOFF_SECS)
            ok, _, err = _run_one(prompt_path, output_path)

        # generate_vertex.py may auto-version the output filename if a collision
        # exists. Resolve the actual file written by scanning the dir.
        actual_image = None
        if ok:
            # Most likely path is exactly output_path; otherwise check -v2/-v3 variants
            candidates = sorted(run_dir_p.glob(f"{i:02d}_{slug}*.png"))
            for c in candidates:
                if c.is_file():
                    actual_image = c
                    break

        if ok and actual_image:
            rel_img = actual_image.relative_to(PROJECT_ROOT).as_posix()
            rel_prompt = (actual_image.with_name(actual_image.stem + "_prompt.json")
                          .relative_to(PROJECT_ROOT)).as_posix() \
                if (actual_image.with_name(actual_image.stem + "_prompt.json")).exists() \
                else (prompt_path.relative_to(PROJECT_ROOT)).as_posix()
            state["images"].append(rel_img)
            state["prompts"].append(rel_prompt)
            state["completed"] = i
        else:
            state["errors"].append(f"shot {i:02d} failed: {err[:300] if err else 'unknown'}")
            # Don't abort the whole batch -- keep going so partial results land

        _write_state(run_dir_p, state)

        if pace and i < count and ok:
            time.sleep(PACE_SLEEP_SECS)

    # Final status
    state["status"] = "complete" if not state["errors"] else (
        "complete_with_errors" if state["images"] else "failed"
    )
    state["current_stage"] = "done"
    state["finished_at"] = datetime.now().isoformat(timespec="seconds")
    _write_state(run_dir_p, state)


def _cli_main() -> int:
    ap = argparse.ArgumentParser(description="Run an experiment batch from an existing run dir.")
    ap.add_argument("--run-dir", required=True, help="Path to contents/experiments/<run_id>/")
    args = ap.parse_args()

    run_dir_p = Path(args.run_dir).resolve()
    manifest_path = run_dir_p / "run.json"
    if not manifest_path.exists():
        print(f"ERROR: {manifest_path} not found", file=sys.stderr)
        return 1

    state = json.loads(manifest_path.read_text(encoding="utf-8"))
    state.setdefault("images", [])
    state.setdefault("prompts", [])
    state.setdefault("errors", [])
    state.setdefault("completed", 0)

    run_batch(run_dir_p, state)
    print(json.dumps({"status": state.get("status"), "completed": state.get("completed"), "errors": state.get("errors")}))
    return 0 if state.get("status") in {"complete", "complete_with_errors"} else 2


if __name__ == "__main__":
    sys.exit(_cli_main())
