"""Pad any image to a clean 1080x1920 (9:16) Facebook/IG story frame.

Fills the frame with a blurred, darkened cover of the same image (no black bars),
then centers the original spanning the full width. Looks intentional, not letterboxed.

Usage:
    python tools/image_ops/story_pad.py <out_dir> <img1> [img2 ...]
    python tools/image_ops/story_pad.py contents/assets/stories-x/ contents/new/a.png
"""
import sys
from pathlib import Path

from PIL import Image, ImageFilter, ImageEnhance

W, H = 1080, 1920


def pad_to_story(src: Path, out: Path, blur: int = 42, darken: float = 0.62) -> Path:
    """Render src onto a 1080x1920 story canvas with a blurred-cover background."""
    img = Image.open(src).convert("RGB")

    # --- background: cover the whole 9:16 canvas, blurred + darkened ---
    iw, ih = img.size
    scale = max(W / iw, H / ih)
    bw, bh = int(iw * scale), int(ih * scale)
    bg = img.resize((bw, bh), Image.LANCZOS).crop(
        ((bw - W) // 2, (bh - H) // 2, (bw - W) // 2 + W, (bh - H) // 2 + H))
    bg = bg.filter(ImageFilter.GaussianBlur(blur))
    bg = ImageEnhance.Brightness(bg).enhance(darken)

    # --- foreground: span full width, cap to frame height, centered ---
    fw = W
    fh = int(ih * (W / iw))
    if fh > H:
        fh = H
        fw = int(iw * (H / ih))
    fg = img.resize((fw, fh), Image.LANCZOS)
    bg.paste(fg, ((W - fw) // 2, (H - fh) // 2))

    out.parent.mkdir(parents=True, exist_ok=True)
    if out.suffix.lower() in (".jpg", ".jpeg"):
        bg.save(out, "JPEG", quality=88, optimize=True)
    else:
        bg.save(out, "PNG", optimize=True)
    return out


def main():
    if len(sys.argv) < 3:
        print("Usage: python story_pad.py <out_dir> <img1> [img2 ...]", file=sys.stderr)
        sys.exit(1)
    out_dir = Path(sys.argv[1])
    for s in sys.argv[2:]:
        src = Path(s)
        if not src.exists():
            print(f"skip (missing): {src}", file=sys.stderr)
            continue
        out = out_dir / f"{src.stem}-9x16.png"
        pad_to_story(src, out)
        print(f"  {src.name} -> {out}")


if __name__ == "__main__":
    main()
