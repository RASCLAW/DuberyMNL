"""
Generate an image using Gemini 3.1 Flash via Vertex AI.

Reads a UGC/NB2 prompt JSON, loads reference images as multimodal Parts,
sends to Gemini, saves the result locally.

Usage:
    python generate_vertex.py <prompt_json_file> <output_file>

Example:
    python tools/image_gen/generate_vertex.py .tmp/UGC-TEST-001_ugc_prompt.json contents/new/test_001.jpg
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai.types import GenerateContentConfig, Modality, Part, Blob

PROJECT_DIR = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_DIR / ".env")


def load_prompt(prompt_file: str) -> tuple[str, list[str]]:
    """Load prompt text and image_input paths from JSON or TXT file."""
    path = Path(prompt_file)

    if path.suffix == ".txt":
        prompt_text = path.read_text(encoding="utf-8").strip()
        # Check for sidecar config
        stem = path.stem.replace("_prompt", "")
        sidecar = path.parent / f"{stem}_config.json"
        if sidecar.exists():
            cfg = json.loads(sidecar.read_text(encoding="utf-8"))
            image_input = cfg.get("image_input", [])
        else:
            image_input = []
    else:
        data = json.loads(path.read_text(encoding="utf-8"))
        prompt_text = data.get("prompt", "")
        image_input = data.get("image_input", [])

    return prompt_text, image_input


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


def generate(parts: list) -> tuple[bytes, str]:
    """Send to Gemini 3.1 Flash and return (image_bytes, mime_type)."""
    client = genai.Client(vertexai=True, project="dubery", location="global")
    print("Sending to Gemini 3.1 Flash...", file=sys.stderr)

    response = client.models.generate_content(
        model="gemini-3.1-flash-image-preview",
        contents=parts,
        config=GenerateContentConfig(response_modalities=[Modality.IMAGE]),
    )

    # Extract image from response
    for candidate in response.candidates:
        for part in candidate.content.parts:
            if part.inline_data and part.inline_data.data:
                return part.inline_data.data, part.inline_data.mime_type

    print("ERROR: No image in Gemini response", file=sys.stderr)
    if response.text:
        print(f"Model said: {response.text}", file=sys.stderr)
    sys.exit(1)


def main():
    if len(sys.argv) < 3:
        print("Usage: python generate_vertex.py <prompt_json_file> <output_file>")
        sys.exit(1)

    prompt_file = sys.argv[1]
    output_file = sys.argv[2]

    prompt_text, image_paths = load_prompt(prompt_file)
    if not prompt_text:
        print("ERROR: Empty prompt text", file=sys.stderr)
        sys.exit(1)

    print(f"Prompt: {prompt_text[:120]}...", file=sys.stderr)
    parts = build_parts(prompt_text, image_paths)
    image_bytes, mime_type = generate(parts)

    # Determine extension from mime_type
    ext = "jpg" if "jpeg" in mime_type else mime_type.split("/")[-1]
    out_path = Path(output_file)
    if out_path.suffix.lstrip(".") != ext:
        out_path = out_path.with_suffix(f".{ext}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(image_bytes)
    print(f"Saved: {out_path} ({len(image_bytes)//1024}KB)", file=sys.stderr)

    # Move prompt JSON alongside the image (same ID, _prompt.json suffix)
    prompt_src = Path(prompt_file)
    if prompt_src.exists():
        prompt_dest = out_path.with_name(out_path.stem + "_prompt.json")
        import shutil
        shutil.move(str(prompt_src), str(prompt_dest))
        print(f"Prompt saved: {prompt_dest}", file=sys.stderr)

    # JSON output for pipeline integration
    print(json.dumps({
        "success": True,
        "output_path": str(out_path),
        "prompt_path": str(prompt_dest) if prompt_src.exists() else None,
        "size_kb": len(image_bytes) // 1024,
        "mime_type": mime_type,
    }))


if __name__ == "__main__":
    main()
