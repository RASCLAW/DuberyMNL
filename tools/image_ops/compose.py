"""
Pillow-based collage composer for the feed scheduler.

Each layout outputs a 1080x1080 PNG with 2-px black gutters between cells.
Cells are center-cropped and resized to fit. The dispatcher routes by layout key.

Layouts:
  2h      side-by-side (2 images, 540x1080 each)
  2v      stacked vertical (2 images, 1080x540 each)
  1p2     hero left + 2 stacked right (3 images)
  2x2     2x2 grid (4 images)
  3h      3-column strip (3 images)
  hero3   big hero on top + 3 below (4 images)
  ba      before/after side-by-side with divider (2 images)

CLI:
    python tools/image_ops/compose.py --layout 2x2 --inputs a.png b.png c.png d.png --output .tmp/test.png
"""

import argparse
import sys
from pathlib import Path

from PIL import Image

CANVAS_SIZE = 1080
GUTTER = 2
BG_COLOR = (0, 0, 0)


LAYOUTS = {
    "2h": {"count": 2, "fn": "compose_2h"},
    "2v": {"count": 2, "fn": "compose_2v"},
    "1p2": {"count": 3, "fn": "compose_1p2"},
    "2x2": {"count": 4, "fn": "compose_2x2"},
    "3h": {"count": 3, "fn": "compose_3h"},
    "hero3": {"count": 4, "fn": "compose_hero3"},
    "ba": {"count": 2, "fn": "compose_ba"},
}


def _open(path: str) -> Image.Image:
    img = Image.open(path)
    if img.mode != "RGB":
        img = img.convert("RGB")
    return img


def _fit(img: Image.Image, w: int, h: int) -> Image.Image:
    """Center-crop + resize to exactly (w, h)."""
    src_w, src_h = img.size
    src_ratio = src_w / src_h
    dst_ratio = w / h
    if src_ratio > dst_ratio:
        new_w = int(src_h * dst_ratio)
        left = (src_w - new_w) // 2
        img = img.crop((left, 0, left + new_w, src_h))
    elif src_ratio < dst_ratio:
        new_h = int(src_w / dst_ratio)
        top = (src_h - new_h) // 2
        img = img.crop((0, top, src_w, top + new_h))
    return img.resize((w, h), Image.LANCZOS)


def _canvas() -> Image.Image:
    return Image.new("RGB", (CANVAS_SIZE, CANVAS_SIZE), BG_COLOR)


def compose_2h(paths: list, output: str) -> str:
    canvas = _canvas()
    cell_w = (CANVAS_SIZE - GUTTER) // 2
    canvas.paste(_fit(_open(paths[0]), cell_w, CANVAS_SIZE), (0, 0))
    canvas.paste(_fit(_open(paths[1]), cell_w, CANVAS_SIZE), (cell_w + GUTTER, 0))
    canvas.save(output, "PNG")
    return output


def compose_2v(paths: list, output: str) -> str:
    canvas = _canvas()
    cell_h = (CANVAS_SIZE - GUTTER) // 2
    canvas.paste(_fit(_open(paths[0]), CANVAS_SIZE, cell_h), (0, 0))
    canvas.paste(_fit(_open(paths[1]), CANVAS_SIZE, cell_h), (0, cell_h + GUTTER))
    canvas.save(output, "PNG")
    return output


def compose_1p2(paths: list, output: str) -> str:
    canvas = _canvas()
    hero_w = int((CANVAS_SIZE - GUTTER) * 2 / 3)
    side_w = CANVAS_SIZE - hero_w - GUTTER
    cell_h = (CANVAS_SIZE - GUTTER) // 2
    canvas.paste(_fit(_open(paths[0]), hero_w, CANVAS_SIZE), (0, 0))
    canvas.paste(_fit(_open(paths[1]), side_w, cell_h), (hero_w + GUTTER, 0))
    canvas.paste(_fit(_open(paths[2]), side_w, cell_h), (hero_w + GUTTER, cell_h + GUTTER))
    canvas.save(output, "PNG")
    return output


def compose_2x2(paths: list, output: str) -> str:
    canvas = _canvas()
    cell_w = (CANVAS_SIZE - GUTTER) // 2
    cell_h = (CANVAS_SIZE - GUTTER) // 2
    positions = [(0, 0), (cell_w + GUTTER, 0), (0, cell_h + GUTTER), (cell_w + GUTTER, cell_h + GUTTER)]
    for path, pos in zip(paths, positions):
        canvas.paste(_fit(_open(path), cell_w, cell_h), pos)
    canvas.save(output, "PNG")
    return output


def compose_3h(paths: list, output: str) -> str:
    canvas = _canvas()
    cell_w = (CANVAS_SIZE - GUTTER * 2) // 3
    x = 0
    for i, path in enumerate(paths):
        canvas.paste(_fit(_open(path), cell_w, CANVAS_SIZE), (x, 0))
        x += cell_w + GUTTER
    canvas.save(output, "PNG")
    return output


def compose_hero3(paths: list, output: str) -> str:
    canvas = _canvas()
    hero_h = int((CANVAS_SIZE - GUTTER) * 2 / 3)
    row_h = CANVAS_SIZE - hero_h - GUTTER
    cell_w = (CANVAS_SIZE - GUTTER * 2) // 3
    canvas.paste(_fit(_open(paths[0]), CANVAS_SIZE, hero_h), (0, 0))
    x = 0
    for path in paths[1:4]:
        canvas.paste(_fit(_open(path), cell_w, row_h), (x, hero_h + GUTTER))
        x += cell_w + GUTTER
    canvas.save(output, "PNG")
    return output


def compose_ba(paths: list, output: str) -> str:
    """Before / After: same as 2h with a slightly thicker black divider."""
    canvas = _canvas()
    divider = 6
    cell_w = (CANVAS_SIZE - divider) // 2
    canvas.paste(_fit(_open(paths[0]), cell_w, CANVAS_SIZE), (0, 0))
    canvas.paste(_fit(_open(paths[1]), cell_w, CANVAS_SIZE), (cell_w + divider, 0))
    canvas.save(output, "PNG")
    return output


def compose(layout: str, paths: list, output: str) -> str:
    if layout not in LAYOUTS:
        raise ValueError(f"unknown layout: {layout}")
    expected = LAYOUTS[layout]["count"]
    if len(paths) != expected:
        raise ValueError(f"layout {layout} expects {expected} images, got {len(paths)}")
    fn_name = LAYOUTS[layout]["fn"]
    return globals()[fn_name](paths, output)


def main():
    p = argparse.ArgumentParser(description="Compose a collage from N images using a layout template.")
    p.add_argument("--layout", choices=sorted(LAYOUTS.keys()), required=True)
    p.add_argument("--inputs", nargs="+", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()

    for path in args.inputs:
        if not Path(path).exists():
            print(f"error: input not found: {path}", file=sys.stderr)
            sys.exit(2)

    out = compose(args.layout, args.inputs, args.output)
    print(out)


if __name__ == "__main__":
    main()
