"""
Generate an image using Gemini 3.1 Flash via Vertex AI.

Reads a UGC/NB2 prompt JSON, loads reference images as multimodal Parts,
sends to Gemini, saves the result locally.

Usage:
    python generate_vertex.py <prompt_json_file> [output_file] [aspect_ratio] [--exact]

If output_file is omitted, saves to contents/new/YYYY-MM-DD_{prompt_stem}.png

--exact is the pipeline mode: write to the given path verbatim (no auto-version,
transcode to the requested extension), derive the caption id from the filename
stem, back the image up to Drive, and write status back to .tmp/pipeline.json.
Without it, ad-hoc behaviour applies -- extension follows the model's mime type
and an existing file is auto-versioned to -v2, -v3, ...

Example:
    python tools/image_gen/generate_vertex.py .tmp/UGC-TEST-001_prompt.json
    python tools/image_gen/generate_vertex.py .tmp/UGC-TEST-001_prompt.json contents/new/custom_name.jpg
    python tools/image_gen/generate_vertex.py .tmp/4_prompt_structured.json contents/new/dubery_4.jpg --exact
"""

try:
    import fcntl
except ImportError:
    fcntl = None
    import msvcrt
import io
import json
import os
import subprocess
import sys
import time
import ctypes

def _hide_file(path):
    if sys.platform == "win32":
        try:
            ctypes.windll.kernel32.SetFileAttributesW(str(path), 0x2)
        except Exception:
            pass
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import errors as genai_errors
from google.genai.types import GenerateContentConfig, ImageConfig, Modality, Part, Blob

PROJECT_DIR = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_DIR / ".env")

CAPTIONS_FILE = PROJECT_DIR / ".tmp" / "pipeline.json"
PIPELINE_LOCK = PROJECT_DIR / ".tmp" / "pipeline.json.lock"

VALID_RATIOS = {"1:1", "4:5", "5:4", "9:16", "16:9", "3:4", "4:3"}

# Vertex per-minute quota recovery -- on 429, back off and retry.
# Pattern from feedback_vertex_quota_parallel_4_blows: 30s+ backoff is the safe minimum.
RETRY_MAX_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = [30, 60, 90]


def update_caption_fields(caption_id: str, fields: dict):
    """Write status/image_url back to the caption entry in .tmp/pipeline.json (file-locked)."""
    if not CAPTIONS_FILE.exists():
        return
    with open(PIPELINE_LOCK, "w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX) if fcntl else msvcrt.locking(lf.fileno(), msvcrt.LK_LOCK, 1)
        try:
            # encoding is explicit: pipeline.json holds non-cp1252 bytes and Windows
            # would otherwise decode it with the ANSI codepage and blow up.
            captions = json.loads(CAPTIONS_FILE.read_text(encoding="utf-8"))
            CAPTIONS_FILE.with_suffix(".json.bak").write_text(
                json.dumps(captions, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            for caption in captions:
                if str(caption.get("id")) == caption_id:
                    caption.update(fields)
                    break
            CAPTIONS_FILE.write_text(
                json.dumps(captions, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        finally:
            fcntl.flock(lf, fcntl.LOCK_UN) if fcntl else msvcrt.locking(lf.fileno(), msvcrt.LK_UNLCK, 1)
    print(f"Caption #{caption_id} updated: {list(fields.keys())}", file=sys.stderr)


def backup_to_drive(output_file: str) -> str:
    """Upload the generated image to Drive. Returns the Drive URL, or "" on failure.

    Non-critical: a failed backup must never fail the generation.
    The "Backed up to Drive: <url>" line is parsed by tools/pipeline/run_ugc.py.
    """
    try:
        upload_result = subprocess.run(
            [sys.executable, "tools/drive/upload_image.py",
             "--file", output_file,
             "--folder", "DuberyMNL/Generated Images"],
            cwd=str(PROJECT_DIR), capture_output=True, text=True, timeout=60
        )
        if upload_result.returncode == 0:
            drive_url = json.loads(upload_result.stdout).get("drive_url", "")
            print(f"Backed up to Drive: {drive_url}")
            return drive_url
        print(f"Drive backup failed (non-critical): {upload_result.stderr.strip()}", file=sys.stderr)
    except Exception as e:
        print(f"Drive backup failed (non-critical): {e}", file=sys.stderr)
    return ""


def load_prompt(prompt_file: str) -> tuple[str, list[str], str, str | None]:
    """Load prompt text, image_input paths, aspect_ratio, image_size from JSON or TXT file."""
    path = Path(prompt_file)
    aspect_ratio = "1:1"
    image_size = None

    if path.suffix == ".txt":
        prompt_text = path.read_text(encoding="utf-8").strip()
        stem = path.stem.replace("_prompt", "")
        sidecar = path.parent / f"{stem}_config.json"
        if sidecar.exists():
            cfg = json.loads(sidecar.read_text(encoding="utf-8"))
            image_input = cfg.get("image_input", [])
            aspect_ratio = cfg.get("aspect_ratio", "1:1")
            image_size = cfg.get("image_size") or cfg.get("resolution")
        else:
            image_input = []
    else:
        data = json.loads(path.read_text(encoding="utf-8"))
        prompt_text = data.get("prompt", "")
        image_input = data.get("image_input", [])
        # Support both top-level "aspect_ratio" and nested "api_parameters.aspect_ratio"
        aspect_ratio = (
            data.get("aspect_ratio")
            or data.get("api_parameters", {}).get("aspect_ratio", "1:1")
        )
        # Output size: "1K" | "2K" | "4K". Top-level "image_size"/"resolution" or nested.
        image_size = (
            data.get("image_size")
            or data.get("resolution")
            or data.get("api_parameters", {}).get("image_size")
            or data.get("api_parameters", {}).get("resolution")
        )

    if aspect_ratio not in VALID_RATIOS:
        print(f"WARNING: Invalid aspect_ratio '{aspect_ratio}', falling back to 1:1", file=sys.stderr)
        aspect_ratio = "1:1"

    if image_size:
        image_size = str(image_size).upper()
        if image_size not in {"1K", "2K", "4K"}:
            print(f"WARNING: Invalid image_size '{image_size}', ignoring (model default)", file=sys.stderr)
            image_size = None

    return prompt_text, image_input, aspect_ratio, image_size


def build_parts(prompt_text: str, image_paths: list[str]) -> list:
    """Build multimodal Parts: reference images first, then text prompt."""
    parts = []

    for img_path in image_paths:
        p = Path(img_path)
        if not p.exists():
            print(f"WARNING: Reference image not found: {img_path}", file=sys.stderr)
            continue
        img_bytes = p.read_bytes()
        ext = p.suffix.lower().lstrip(".")
        mime = f"image/{'jpeg' if ext in ('jpg', 'jpeg') else ext}"
        parts.append(Part(inline_data=Blob(mime_type=mime, data=img_bytes)))
        print(f"Loaded reference: {p.name} ({len(img_bytes)//1024}KB)", file=sys.stderr)

    parts.append(Part(text=prompt_text))
    return parts


def generate(parts: list, aspect_ratio: str = "1:1", image_size: str | None = None) -> tuple[bytes, str]:
    """Send to Gemini 3.1 Flash and return (image_bytes, mime_type).

    Retries on 429 RESOURCE_EXHAUSTED with backoff -- Vertex per-minute quota is
    transient. Other ClientErrors fall through immediately.
    """
    # Billing project: defaults to the original `dubery` account. Set VERTEX_PROJECT
    # in .env to bill a different GCP project (e.g. the $300-trial test account).
    project = os.getenv("VERTEX_PROJECT", "dubery")
    # Image model: default Gemini 3.1 Flash; set VERTEX_IMAGE_MODEL to test Pro (gemini-3-pro-image).
    model = os.getenv("VERTEX_IMAGE_MODEL", "gemini-3.1-flash-image")
    client = genai.Client(vertexai=True, project=project, location="global")
    img_cfg_kwargs = {"aspect_ratio": aspect_ratio}
    if image_size:
        img_cfg_kwargs["image_size"] = image_size
    print(f"Sending to {model} (project={project}, aspect_ratio={aspect_ratio}, image_size={image_size or 'default'})...", file=sys.stderr)

    response = None
    last_429 = None
    for attempt in range(RETRY_MAX_ATTEMPTS):
        try:
            response = client.models.generate_content(
                model=model,
                contents=parts,
                config=GenerateContentConfig(
                    response_modalities=[Modality.IMAGE],
                    image_config=ImageConfig(**img_cfg_kwargs),
                ),
            )
            break
        except genai_errors.ClientError as e:
            status = getattr(e, "status_code", None) or getattr(e, "code", None)
            if status != 429:
                raise
            last_429 = e
            if attempt == RETRY_MAX_ATTEMPTS - 1:
                print(f"ERROR: 429 quota exhausted after {RETRY_MAX_ATTEMPTS} attempts", file=sys.stderr)
                raise
            backoff = RETRY_BACKOFF_SECONDS[attempt]
            print(f"WARNING: 429 quota hit (attempt {attempt + 1}/{RETRY_MAX_ATTEMPTS}); sleeping {backoff}s before retry...", file=sys.stderr)
            time.sleep(backoff)

    # Extract image from response
    for candidate in response.candidates:
        for part in candidate.content.parts:
            if part.inline_data and part.inline_data.data:
                return part.inline_data.data, part.inline_data.mime_type

    print("ERROR: No image in Gemini response", file=sys.stderr)
    if response.text:
        print(f"Model said: {response.text}", file=sys.stderr)
    sys.exit(1)


def default_output_path(prompt_file: str) -> str:
    """Generate default output path: contents/new/YYYY-MM-DD_{prompt_stem}.png"""
    stem = Path(prompt_file).stem.replace("_prompt", "")
    today = date.today().isoformat()
    return str(PROJECT_DIR / "contents" / "new" / f"{today}_{stem}.png")


def transcode(image_bytes: bytes, target_ext: str) -> bytes:
    """Convert raw image bytes to the requested extension (jpg/jpeg/png/webp).

    Pipeline consumers hard-code dubery_{id}.jpg, so a PNG from the model has to
    become a real JPEG rather than a PNG wearing a .jpg suffix.
    """
    from PIL import Image

    fmt = {"jpg": "JPEG", "jpeg": "JPEG", "png": "PNG", "webp": "WEBP"}[target_ext]
    img = Image.open(io.BytesIO(image_bytes))
    if fmt == "JPEG" and img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format=fmt, quality=95) if fmt == "JPEG" else img.save(buf, format=fmt)
    return buf.getvalue()


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    exact = "--exact" in sys.argv

    if not args:
        print("Usage: python generate_vertex.py <prompt_json_file> [output_file] [aspect_ratio] [--exact]")
        sys.exit(1)

    prompt_file = args[0]
    output_file = args[1] if len(args) >= 2 else default_output_path(prompt_file)
    aspect_override = args[2] if len(args) >= 3 else None

    # Pipeline mode derives the caption id from the output stem (dubery_4.jpg -> "4")
    caption_id = None
    if exact:
        stem = Path(output_file).stem
        caption_id = stem.split("_", 1)[1] if "_" in stem else None

    def fail(msg: str):
        print(msg, file=sys.stderr)
        if caption_id:
            update_caption_fields(caption_id, {"status": "IMAGE_FAILED"})
        sys.exit(1)

    prompt_text, image_paths, aspect_ratio, image_size = load_prompt(prompt_file)
    if aspect_override:
        if aspect_override in VALID_RATIOS:
            aspect_ratio = aspect_override
        else:
            print(f"WARNING: Invalid aspect_ratio arg '{aspect_override}', using {aspect_ratio}", file=sys.stderr)
    if not prompt_text:
        fail("ERROR: Empty prompt text")

    print(f"Prompt: {prompt_text[:120]}...", file=sys.stderr)
    parts = build_parts(prompt_text, image_paths)
    try:
        image_bytes, mime_type = generate(parts, aspect_ratio, image_size)
    except SystemExit:
        raise
    except Exception as e:
        fail(f"ERROR: generation failed: {e}")

    out_path = Path(output_file)
    model_ext = "jpg" if "jpeg" in mime_type else mime_type.split("/")[-1]

    if exact:
        # Write the requested path verbatim -- transcode instead of renaming.
        want_ext = out_path.suffix.lstrip(".").lower() or model_ext
        if want_ext != model_ext:
            try:
                image_bytes = transcode(image_bytes, want_ext)
            except Exception as e:
                fail(f"ERROR: could not transcode {model_ext} -> {want_ext}: {e}")
    else:
        # Ad-hoc: extension follows the model, and never clobber an existing file.
        if out_path.suffix.lstrip(".") != model_ext:
            out_path = out_path.with_suffix(f".{model_ext}")
        if out_path.exists():
            n = 2
            while True:
                candidate = out_path.with_name(f"{out_path.stem}-v{n}{out_path.suffix}")
                if not candidate.exists():
                    out_path = candidate
                    break
                n += 1
            print(f"Auto-versioned to: {out_path.name}", file=sys.stderr)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        out_path.write_bytes(image_bytes)
    except Exception as e:
        fail(f"ERROR saving image: {e}")
    print(f"Saved: {out_path} ({len(image_bytes)//1024}KB)", file=sys.stderr)

    # Copy prompt alongside the image (same ID, _prompt.json suffix).
    # Use copy2 (not move) so the source .txt in .tmp/ is preserved for re-runs/edits.
    prompt_src = Path(prompt_file)
    if prompt_src.exists():
        prompt_dest = out_path.with_name(out_path.stem + "_prompt.json")
        import shutil
        # A previous run marked this sidecar HIDDEN; on Windows copying over a
        # hidden file raises PermissionError, so drop it first.
        prompt_dest.unlink(missing_ok=True)
        shutil.copy2(str(prompt_src), str(prompt_dest))
        _hide_file(prompt_dest)
        print(f"Prompt saved: {prompt_dest}", file=sys.stderr)

    # Pipeline mode: Drive backup + write status back to pipeline.json
    drive_url = ""
    if exact:
        drive_url = backup_to_drive(str(out_path))
        if caption_id:
            fields = {"status": "DONE"}
            if drive_url:
                fields["image_url"] = drive_url
            update_caption_fields(caption_id, fields)

    # JSON output for pipeline integration
    print(json.dumps({
        "success": True,
        "output_path": str(out_path),
        "prompt_path": str(prompt_dest) if prompt_src.exists() else None,
        "size_kb": len(image_bytes) // 1024,
        "mime_type": mime_type,
        "drive_url": drive_url,
    }))


if __name__ == "__main__":
    main()
