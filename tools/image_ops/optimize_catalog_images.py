"""
Optimize images referenced by dubery-landing-v3/products/data.json.

For every thumb / hover / hero / gallery image, generates a `<original>-opt.jpg`
next to it (480px wide for thumb/hover, 1200px max for hero/gallery, JPEG @ 85%).

Default mode is DRY-RUN-PREVIEW: writes optimized files and reports before/after
sizes, but does NOT modify data.json. Pass --apply to also rewrite data.json so
the site picks up the optimized versions.

Usage:
    python tools/image_ops/optimize_catalog_images.py             # dry-run preview
    python tools/image_ops/optimize_catalog_images.py --quality 80
    python tools/image_ops/optimize_catalog_images.py --apply     # also update data.json
    python tools/image_ops/optimize_catalog_images.py --revert    # restore data.json from backup

Safe to re-run -- skips files where the *-opt.jpg already exists and is fresh.
"""

import argparse
import json
import sys
import time
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("PIL/Pillow missing. Install: pip install Pillow", file=sys.stderr)
    sys.exit(1)


PROJECT_DIR = Path(__file__).parent.parent.parent
SITE_DIR = PROJECT_DIR / "dubery-landing-v3"
DATA_PATH = SITE_DIR / "products" / "data.json"
BACKUP_PATH = DATA_PATH.with_suffix(".json.pre-optimize.bak")

# Field name -> max width in px. 960px Q92 confirmed crisp on big monitor / retina;
# 1800px for hero/gallery/feature gives clean PDP zoom-in.
FIELD_WIDTHS = {
    "thumb": 960,
    "hover": 960,
    "hero": 1800,
    "gallery": 1800,
    "feature_image": 1800,
    "feature_images": 1800,
}


def resolve_path(rel: str) -> Path | None:
    """Resolve a data.json path (typically './assets/...' or 'assets/...') to absolute."""
    if not rel or rel.startswith("http"):
        return None
    return (SITE_DIR / rel.lstrip("./")).resolve()


def optimized_path(p: Path) -> Path:
    """Sibling -opt.jpg next to the original. Always .jpg regardless of source format."""
    return p.with_name(f"{p.stem}-opt.jpg")


def site_relative(p: Path) -> str:
    """Path string in the same './assets/...' shape data.json uses."""
    try:
        rel = p.relative_to(SITE_DIR)
    except ValueError:
        return str(p)
    return "./" + rel.as_posix()


def optimize_one(src: Path, target_width: int, quality: int, force: bool = False) -> tuple[int, int, bool]:
    """Generate -opt.jpg if needed. Returns (original_bytes, optimized_bytes, skipped)."""
    if not src.exists():
        return (0, 0, True)
    dst = optimized_path(src)
    orig_bytes = src.stat().st_size

    # Skip if optimized already exists and is newer than source (unless --force)
    if not force and dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
        return (orig_bytes, dst.stat().st_size, True)

    im = Image.open(src)
    if im.mode in ("RGBA", "LA", "P"):
        bg = Image.new("RGB", im.size, (255, 255, 255))
        bg.paste(im, mask=im.split()[-1] if im.mode == "RGBA" else None)
        im = bg
    elif im.mode != "RGB":
        im = im.convert("RGB")

    if im.width > target_width:
        new_h = int(im.height * (target_width / im.width))
        im = im.resize((target_width, new_h), Image.LANCZOS)

    im.save(dst, "JPEG", quality=quality, optimize=True, progressive=True)
    return (orig_bytes, dst.stat().st_size, False)


def collect_paths(product: dict) -> list[tuple[str, str]]:
    """Yield (field_name, path_string) for every image reference on a product."""
    out: list[tuple[str, str]] = []
    for field in ("thumb", "hover", "hero", "feature_image"):
        v = product.get(field)
        if v:
            out.append((field, v))
    for field in ("gallery", "feature_images"):
        v = product.get(field) or []
        for item in v:
            if item:
                out.append((field, item))
    return out


def fmt_bytes(n: int) -> str:
    if n < 1024:
        return f"{n}B"
    if n < 1024 * 1024:
        return f"{n/1024:.0f}K"
    return f"{n/1024/1024:.2f}M"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quality", type=int, default=92, help="JPEG quality (default 92)")
    ap.add_argument("--apply", action="store_true", help="Also rewrite data.json to point at -opt versions")
    ap.add_argument("--revert", action="store_true", help="Restore data.json from backup (.bak)")
    ap.add_argument("--force", action="store_true", help="Re-generate -opt files even if cached")
    args = ap.parse_args()

    if args.revert:
        if not BACKUP_PATH.exists():
            print(f"No backup found at {BACKUP_PATH}", file=sys.stderr)
            sys.exit(1)
        DATA_PATH.write_text(BACKUP_PATH.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"Restored {DATA_PATH} from {BACKUP_PATH}")
        return

    products = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    print(f"Optimizing images for {len(products)} products (quality={args.quality})...")
    print()

    grand_orig = 0
    grand_opt = 0
    rewrites: list[tuple[dict, str, str | list, int]] = []  # (product, field, new_val, idx-for-list)

    header = f"{'slug':<22} {'field':<14} {'orig':>8} {'opt':>8} {'saved':>8}"
    print(header)
    print("-" * len(header))

    for p in products:
        refs = collect_paths(p)
        per_product_orig = 0
        per_product_opt = 0
        # Track list-typed fields so we can rewrite in order
        list_field_updates: dict[str, list] = {}
        for field, rel in refs:
            src = resolve_path(rel)
            if src is None:
                continue
            width = FIELD_WIDTHS.get(field, 1800)
            orig, opt, skipped = optimize_one(src, width, args.quality, force=args.force)
            per_product_orig += orig
            per_product_opt += opt
            tag = "(cached)" if skipped else ""
            # Print per-image only for thumb/hover (biggest wins); gallery summarized
            if field in ("thumb", "hover"):
                saved = orig - opt
                print(f"{p['slug']:<22} {field:<14} {fmt_bytes(orig):>8} {fmt_bytes(opt):>8} {fmt_bytes(saved):>8} {tag}")
            # Stage rewrite
            opt_path = optimized_path(src)
            new_rel = site_relative(opt_path)
            if field in ("gallery", "feature_images"):
                list_field_updates.setdefault(field, []).append(new_rel)
            else:
                rewrites.append((p, field, new_rel, -1))
        # Gallery summary line
        if per_product_orig > 0:
            non_thumbnail = per_product_orig - sum(
                resolve_path(rel).stat().st_size for f, rel in refs if f in ("thumb", "hover") and resolve_path(rel) and resolve_path(rel).exists()
            )
            # one summary line per product
            print(f"{p['slug']:<22} {'(all-fields)':<14} {fmt_bytes(per_product_orig):>8} {fmt_bytes(per_product_opt):>8} {fmt_bytes(per_product_orig - per_product_opt):>8}")
            print()
        grand_orig += per_product_orig
        grand_opt += per_product_opt
        # Stage list rewrites
        for field, new_list in list_field_updates.items():
            rewrites.append((p, field, new_list, -1))

    print("=" * len(header))
    saved = grand_orig - grand_opt
    pct = (saved / grand_orig * 100) if grand_orig else 0
    print(f"TOTAL  orig: {fmt_bytes(grand_orig)}   opt: {fmt_bytes(grand_opt)}   saved: {fmt_bytes(saved)} ({pct:.1f}%)")

    # Catalog-page payload estimate (thumb + hover for all products)
    catalog_orig = 0
    catalog_opt = 0
    for p in products:
        for field in ("thumb", "hover"):
            src = resolve_path(p.get(field, ""))
            if not src or not src.exists():
                continue
            catalog_orig += src.stat().st_size
            opt = optimized_path(src)
            if opt.exists():
                catalog_opt += opt.stat().st_size
    print()
    print(f"Catalog page payload (thumb+hover, all {len(products)} cards):")
    print(f"   before: {fmt_bytes(catalog_orig)}   after: {fmt_bytes(catalog_opt)}   "
          f"reduction: {catalog_orig/catalog_opt:.1f}x" if catalog_opt else "after: 0")

    print()
    if args.apply:
        # Backup once
        if not BACKUP_PATH.exists():
            BACKUP_PATH.write_text(DATA_PATH.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"Backed up original data.json -> {BACKUP_PATH}")
        # Apply rewrites
        for product, field, new_val, _ in rewrites:
            product[field] = new_val
        DATA_PATH.write_text(json.dumps(products, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Rewrote {DATA_PATH} to point at -opt files.")
        print("Deploy via git push to publish.")
    else:
        print("DRY-RUN PREVIEW: optimized files written next to originals, data.json untouched.")
        print("To apply (rewrite data.json to point at -opt versions):  python tools/image_ops/optimize_catalog_images.py --apply")
        print("To revert later:  python tools/image_ops/optimize_catalog_images.py --revert")


if __name__ == "__main__":
    main()
