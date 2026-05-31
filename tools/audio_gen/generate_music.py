"""
Generate music with Lyria via the Vertex AI predict endpoint.

Text (or image-guided) prompt -> royalty-free 48kHz WAV instrumental clip,
for scoring DuberyMNL video ads / animated carousels.

Usage:
    python generate_music.py --prompt "warm tropical lo-fi, upbeat" [--output contents/new/track.wav]
    python generate_music.py --prompt "..." --model lyria-002 --negative-prompt "vocals, lyrics" --seed 7

Billing project comes from VERTEX_PROJECT (default `dubery`) -- the same toggle
as generate_vertex.py / generate_videos.py. Set VERTEX_PROJECT +
GOOGLE_APPLICATION_CREDENTIALS in .env to bill a different account.

Models (per the Vertex AI pricing page):
    lyria-002   Lyria 2  -- $0.06 / 30s clip (~32.8s, 48kHz WAV). Confirmed.
    (Lyria 3 / Lyria 3 Pro are public preview; confirm model IDs before use.)
"""

import argparse
import base64
import json
import os
import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
import google.auth
from google.auth.transport.requests import AuthorizedSession

PROJECT_DIR = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_DIR / ".env")

LOCATION = "us-central1"


def generate_music(prompt: str, model: str = "lyria-002",
                   negative_prompt: str | None = None,
                   seed: int | None = None) -> bytes:
    """Call the Lyria :predict endpoint and return WAV bytes."""
    project = os.getenv("VERTEX_PROJECT", "dubery")
    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    session = AuthorizedSession(creds)

    url = (f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{project}"
           f"/locations/{LOCATION}/publishers/google/models/{model}:predict")

    instance = {"prompt": prompt}
    if negative_prompt:
        instance["negative_prompt"] = negative_prompt
    # seed and sample_count are mutually exclusive (Lyria API constraint).
    if seed is not None:
        instance["seed"] = seed
        parameters = {}
    else:
        parameters = {"sample_count": 1}

    body = {"instances": [instance], "parameters": parameters}

    print(f"Lyria {model} (project={project}) ...", file=sys.stderr)
    print(f"Prompt: {prompt[:120]}{'...' if len(prompt) > 120 else ''}", file=sys.stderr)

    resp = session.post(url, json=body, timeout=300)
    if resp.status_code != 200:
        print(f"ERROR {resp.status_code}: {resp.text[:600]}", file=sys.stderr)
        sys.exit(1)

    preds = resp.json().get("predictions", [])
    if not preds:
        print(f"ERROR: no predictions in response: {resp.text[:400]}", file=sys.stderr)
        sys.exit(1)

    p0 = preds[0]
    b64 = p0.get("audioContent") or p0.get("bytesBase64Encoded")
    if not b64:
        print(f"ERROR: no audio bytes in prediction (keys={list(p0.keys())})", file=sys.stderr)
        sys.exit(1)
    return base64.b64decode(b64)


def main():
    ap = argparse.ArgumentParser(description="Generate music with Lyria (Vertex AI)")
    ap.add_argument("--prompt", required=True, help="Music description (instrumental)")
    ap.add_argument("--model", default="lyria-002", help="Lyria model id (default: lyria-002)")
    ap.add_argument("--negative-prompt", help="Unwanted elements (e.g. 'vocals, lyrics')")
    ap.add_argument("--seed", type=int, help="Seed for reproducibility (excludes sample_count)")
    ap.add_argument("--output", help="Output WAV path (default: contents/new/YYYY-MM-DD_lyria.wav)")
    args = ap.parse_args()

    audio = generate_music(args.prompt, args.model, args.negative_prompt, args.seed)

    out = Path(args.output) if args.output else (
        PROJECT_DIR / "contents" / "new" / f"{date.today().isoformat()}_lyria.wav")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(audio)
    print(f"Saved: {out} ({len(audio)//1024}KB)", file=sys.stderr)

    print(json.dumps({"success": True, "output_path": str(out), "size_kb": len(audio) // 1024}))


if __name__ == "__main__":
    main()
