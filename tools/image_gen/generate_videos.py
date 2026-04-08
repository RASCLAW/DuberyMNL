"""
Generate a video using Veo 3.1 via Vertex AI.

Supports text-to-video, image-to-video (starting frame), and
start+end frame interpolation for controlled animations.

Usage:
    python generate_videos.py --prompt "description" --output .tmp/output.mp4
    python generate_videos.py --prompt "description" --image start.png --output .tmp/output.mp4
    python generate_videos.py --prompt "description" --image start.png --last-frame end.png --output .tmp/output.mp4
    python generate_videos.py --prompt "description" --image start.png --ref-image product.png --output .tmp/output.mp4

Models:
    veo-3.1-fast-generate-001  (default, ~$1/video, audio+speech)
    veo-3.1-generate-001       (hero content, ~$3-4/video)
    veo-3.1-lite-generate-001  (budget, ~$0.50-1/video)
"""

import argparse
import json
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai.types import GenerateVideosConfig, Image, RawReferenceImage

PROJECT_DIR = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_DIR / ".env")

MODELS = {
    "fast": "veo-3.1-fast-generate-001",
    "full": "veo-3.1-generate-001",
    "lite": "veo-3.1-lite-generate-001",
}


def load_image(path: str) -> Image:
    """Load an image file into a Veo Image object."""
    p = Path(path)
    if not p.exists():
        print(f"ERROR: Image not found: {path}", file=sys.stderr)
        sys.exit(1)
    img_bytes = p.read_bytes()
    ext = p.suffix.lower().lstrip(".")
    mime = f"image/{'jpeg' if ext in ('jpg', 'jpeg') else ext}"
    print(f"Loaded: {p.name} ({len(img_bytes)//1024}KB)", file=sys.stderr)
    return Image(image_bytes=img_bytes, mime_type=mime)


def generate_video(
    prompt: str,
    image_path: str | None = None,
    last_frame_path: str | None = None,
    ref_image_path: str | None = None,
    model: str = "fast",
    aspect_ratio: str = "16:9",
    audio: bool = True,
    negative_prompt: str | None = None,
    enhance_prompt: bool | None = None,
    seed: int | None = None,
    duration: int | None = None,
) -> bytes:
    """Generate video via Veo 3.1 and return MP4 bytes."""
    client = genai.Client(vertexai=True, project="dubery", location="us-central1")
    model_id = MODELS.get(model, model)

    # Starting frame (image-to-video)
    start_image = load_image(image_path) if image_path else None

    # Build config
    config_kwargs = {
        "aspect_ratio": aspect_ratio,
        "number_of_videos": 1,
    }
    if "3.1" in model_id:
        config_kwargs["generate_audio"] = audio
    if negative_prompt:
        config_kwargs["negative_prompt"] = negative_prompt
    if enhance_prompt is not None:
        config_kwargs["enhance_prompt"] = enhance_prompt
    if seed is not None:
        config_kwargs["seed"] = seed
    if duration is not None:
        config_kwargs["duration_seconds"] = duration

    # Last frame (start+end frame interpolation for controlled animation)
    if last_frame_path:
        config_kwargs["last_frame"] = load_image(last_frame_path)
        print(f"Added last frame (start+end interpolation)", file=sys.stderr)

    # Reference images (ASSET type for product fidelity)
    if ref_image_path:
        ref_img = load_image(ref_image_path)
        config_kwargs["reference_images"] = [
            RawReferenceImage(reference_image=ref_img)
        ]
        print(f"Added reference image", file=sys.stderr)

    config = GenerateVideosConfig(**config_kwargs)

    print(f"Model: {model_id}", file=sys.stderr)
    print(f"Aspect ratio: {aspect_ratio}", file=sys.stderr)
    print(f"Audio: {audio}", file=sys.stderr)
    print(f"Prompt: {prompt[:150]}{'...' if len(prompt) > 150 else ''}", file=sys.stderr)
    print(f"Sending to Veo...", file=sys.stderr)

    # Generate (async operation)
    gen_kwargs = {
        "model": model_id,
        "prompt": prompt,
        "config": config,
    }
    if start_image:
        gen_kwargs["image"] = start_image

    operation = client.models.generate_videos(**gen_kwargs)

    # Poll until done
    poll_count = 0
    while not operation.done:
        poll_count += 1
        wait = min(15, 5 + poll_count * 2)  # ramp up: 7, 9, 11, 13, 15, 15...
        print(f"  Waiting... (poll #{poll_count}, next check in {wait}s)", file=sys.stderr)
        time.sleep(wait)
        operation = client.operations.get(operation)

    # Extract video
    if not operation.response or not operation.response.generated_videos:
        print("ERROR: No video in response", file=sys.stderr)
        if hasattr(operation, "error") and operation.error:
            print(f"Error: {operation.error}", file=sys.stderr)
        sys.exit(1)

    video = operation.response.generated_videos[0].video
    if not video:
        print("ERROR: No video in response", file=sys.stderr)
        sys.exit(1)

    if video.uri:
        print(f"Downloading from URI...", file=sys.stderr)
        return client.files.download(file=video)
    elif video.video_bytes:
        print(f"Got inline video ({len(video.video_bytes)//1024}KB)", file=sys.stderr)
        return video.video_bytes
    else:
        print("ERROR: No URI or inline bytes in response", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Generate video with Veo 3.1")
    parser.add_argument("--prompt", required=True, help="Video generation prompt")
    parser.add_argument("--image", help="Starting frame image path (image-to-video)")
    parser.add_argument("--last-frame", help="End frame image path (start+end interpolation)")
    parser.add_argument("--ref-image", help="Reference image path (visual guidance)")
    parser.add_argument("--model", default="fast", choices=["fast", "full", "lite"],
                        help="Veo model tier (default: fast)")
    parser.add_argument("--aspect-ratio", default="16:9",
                        help="Aspect ratio (default: 16:9)")
    parser.add_argument("--no-audio", action="store_true", help="Disable audio generation")
    parser.add_argument("--negative-prompt", help="Unwanted elements (as nouns, e.g. 'morphing, dissolving')")
    parser.add_argument("--no-enhance", action="store_true", help="Disable AI prompt enhancement")
    parser.add_argument("--seed", type=int, help="Seed for reproducibility")
    parser.add_argument("--duration", type=int, help="Video duration in seconds")
    parser.add_argument("--output", default=".tmp/veo_output.mp4",
                        help="Output MP4 path (default: .tmp/veo_output.mp4)")
    args = parser.parse_args()

    video_bytes = generate_video(
        prompt=args.prompt,
        image_path=args.image,
        last_frame_path=args.last_frame,
        ref_image_path=args.ref_image,
        model=args.model,
        aspect_ratio=args.aspect_ratio,
        audio=not args.no_audio,
        negative_prompt=args.negative_prompt,
        enhance_prompt=False if args.no_enhance else None,
        seed=args.seed,
        duration=args.duration,
    )

    # Save video
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(video_bytes)
    print(f"Saved: {out_path} ({len(video_bytes)//1024}KB)", file=sys.stderr)

    # Save prompt sidecar
    prompt_path = out_path.with_suffix(".prompt.json")
    prompt_path.write_text(json.dumps({
        "prompt": args.prompt,
        "image": args.image,
        "last_frame": args.last_frame,
        "ref_image": args.ref_image,
        "model": args.model,
        "aspect_ratio": args.aspect_ratio,
        "audio": not args.no_audio,
    }, indent=2), encoding="utf-8")
    print(f"Prompt saved: {prompt_path}", file=sys.stderr)

    # JSON output for pipeline integration
    print(json.dumps({
        "success": True,
        "output_path": str(out_path),
        "prompt_path": str(prompt_path),
        "size_kb": len(video_bytes) // 1024,
    }))


if __name__ == "__main__":
    main()
