"""
Site-wide image optimizer for dubery-landing-v3.

Discovers and optimizes every image referenced by the live site:
  1. products/data.json     -- thumb / hover / hero / gallery / feature_image(s)
  2. shop-social/data.json  -- image
  3. HTML / CSS / JS files  -- <img src>, background: url(), src='...'

For each referenced image, generates a `<original>-opt.jpg` sibling
(960px wide for catalog thumbs / shop-social tiles; 1800px for hero/gallery/feature;
JPEG quality 92). Originals are never touched.

Default mode is DRY-RUN PREVIEW. With --apply, the consumers (data.json files
and HTML/CSS/JS) are rewritten in place to point at the -opt versions.

Usage:
    python tools/image_ops/optimize_site_images.py             # dry-run
    python tools/image_ops/optimize_site_images.py --force     # regen even if cached
    python tools/image_ops/optimize_site_images.py --apply     # rewrite consumers
    python tools/image_ops/optimize_site_images.py --revert    # undo --apply
"""

import argparse
import json
import re
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("PIL/Pillow missing. Install: pip install Pillow", file=sys.stderr)
    sys.exit(1)


PROJECT_DIR = Path(__file__).parent.parent.parent
SITE_DIR = PROJECT_DIR / "dubery-landing-v3"
PRODUCTS_DATA = SITE_DIR / "products" / "data.json"
SHOP_SOCIAL_DATA = SITE_DIR / "shop-social" / "data.json"
TMP_DIR = PROJECT_DIR / ".tmp"
TMP_DIR.mkdir(exist_ok=True)
REWRITES_LOG = TMP_DIR / "site-optimize-rewrites.json"

# Field-name / context -> max width.
# - catalog/UGC thumb cards display ~250-300px max, so 960px source = 3x retina, plenty.
# - social bumped to 1800 because the lightbox previews the image full-screen.
# - hero/gallery/feature kept at 1800 for PDP main + zoom; source images are already <=1361px wide
#   so the cap rarely fires and files stay at native size after Q92 re-encode.
WIDTHS = {
    "thumb": 960, "hover": 960,
    "social": 1800,
    "hero": 1800, "gallery": 1800,
    "feature_image": 1800, "feature_images": 1800,
    "html": 1800,
}

# Regex catches every quoted asset path of recognised image type
IMG_REF_RE = re.compile(
    r"(?P<q>[\"'(])(?P<path>(?:\.\.?/)?(?:assets|shop-social|products)/[^\"'()\s\?#]+\.(?:jpg|jpeg|png|webp))",
    re.IGNORECASE,
)


def resolve_site_path(rel: str, from_file: Path | None = None) -> Path | None:
    """Resolve a path-string from a data.json or HTML file to an absolute Path."""
    if not rel or rel.startswith("http"):
        return None
    rel = rel.lstrip("./")
    candidates: list[Path] = []
    if from_file is not None:
        candidates.append((from_file.parent / rel).resolve())
    candidates.append((SITE_DIR / rel).resolve())
    for c in candidates:
        if c.exists():
            return c
    return candidates[0] if candidates else None


def optimized_path(p: Path) -> Path:
    return p.with_name(f"{p.stem}-opt.jpg")


def site_relative(p: Path, anchor_file: Path) -> str:
    """Render p as a relative path string the way the anchor file expects."""
    try:
        # Use posix-style separator for HTML/CSS/JSON compatibility.
        rel = Path("/").joinpath(p.relative_to(SITE_DIR)).as_posix()
        # Strip leading slash so it stays relative (consumers use './...' or 'assets/...')
        return "./" + rel.lstrip("/")
    except ValueError:
        return str(p)


def relpath_for_file(target: Path, source_file: Path) -> str:
    """Render `target` as a relative path that works when source_file resolves links."""
    try:
        rel = Path(
            os_relpath := __import__("os").path.relpath(target, source_file.parent)
        ).as_posix()
        return rel
    except Exception:
        return target.as_posix()


def optimize_one(src: Path, target_width: int, quality: int, force: bool) -> tuple[int, int, bool]:
    """Generate -opt.jpg sibling. Returns (orig_bytes, opt_bytes, skipped)."""
    if not src.exists():
        return (0, 0, True)
    dst = optimized_path(src)
    orig = src.stat().st_size
    if (not force) and dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
        return (orig, dst.stat().st_size, True)
    im = Image.open(src)
    if im.mode in ("RGBA", "LA"):
        bg = Image.new("RGB", im.size, (255, 255, 255))
        bg.paste(im, mask=im.split()[-1])
        im = bg
    elif im.mode == "P":
        im = im.convert("RGBA")
        bg = Image.new("RGB", im.size, (255, 255, 255))
        bg.paste(im, mask=im.split()[-1])
        im = bg
    elif im.mode != "RGB":
        im = im.convert("RGB")
    if im.width > target_width:
        new_h = int(im.height * (target_width / im.width))
        im = im.resize((target_width, new_h), Image.LANCZOS)
    im.save(dst, "JPEG", quality=quality, optimize=True, progressive=True)
    return (orig, dst.stat().st_size, False)


def fmt_bytes(n: int) -> str:
    if n < 1024: return f"{n}B"
    if n < 1024 * 1024: return f"{n/1024:.0f}K"
    return f"{n/1024/1024:.2f}M"


# ---------- Discovery ----------

def discover_products() -> list[tuple[str, Path, list]]:
    """Yield (consumer_kind, source_file, list_of_tasks). Tasks are
    (field, current_string, width_key, set_fn(new_string))."""
    if not PRODUCTS_DATA.exists():
        return []
    data = json.loads(PRODUCTS_DATA.read_text(encoding="utf-8"))
    tasks = []
    for product in data:
        for field in ("thumb", "hover", "hero", "feature_image"):
            v = product.get(field)
            if v:
                tasks.append((field, v, field, ("product_field", product, field, None)))
        for field in ("gallery", "feature_images"):
            v = product.get(field) or []
            for idx, item in enumerate(v):
                if item:
                    tasks.append((field, item, field, ("product_list", product, field, idx)))
    return [("products_data", PRODUCTS_DATA, tasks, data)]


def discover_shop_social() -> list[tuple[str, Path, list, list]]:
    if not SHOP_SOCIAL_DATA.exists():
        return []
    data = json.loads(SHOP_SOCIAL_DATA.read_text(encoding="utf-8"))
    tasks = []
    for entry in data:
        v = entry.get("image")
        if v:
            tasks.append(("image", v, "social", ("shop_social", entry, "image", None)))
    return [("shop_social_data", SHOP_SOCIAL_DATA, tasks, data)]


def discover_html_css_js() -> list[tuple[str, Path, list, str]]:
    """For each HTML/CSS/JS file in dubery-landing-v3, gather image refs.
    Tasks are (label, current_string, width_key, (kind, file_path, match_span))."""
    results = []
    for f in list(SITE_DIR.rglob("*.html")) + list(SITE_DIR.rglob("*.css")) + list(SITE_DIR.rglob("*.js")):
        if "node_modules" in str(f) or "__pycache__" in str(f):
            continue
        text = f.read_text(encoding="utf-8", errors="ignore")
        tasks = []
        for m in IMG_REF_RE.finditer(text):
            path_str = m.group("path")
            tasks.append(("inline", path_str, "html", ("html_ref", f, path_str)))
        if tasks:
            results.append(("html_css_js", f, tasks, text))
    return results


# ---------- Apply ----------

def _rel_to(target: Path, anchor_dir: Path) -> str:
    """Return target as a path string relative to anchor_dir, posix slashes."""
    import os
    return Path(os.path.relpath(target, anchor_dir)).as_posix()


def apply_products(consumer_meta, rewrites: dict[Path, Path]):
    _, src_file, tasks, data = consumer_meta
    anchor = src_file.parent
    for label, current, _wkey, target in tasks:
        kind = target[0]
        cur_abs = resolve_site_path(current, from_file=src_file)
        if not cur_abs or cur_abs not in rewrites:
            continue
        new_rel = _rel_to(rewrites[cur_abs], anchor)
        if kind == "product_field":
            _, product, field, _ = target
            product[field] = new_rel
        elif kind == "product_list":
            _, product, field, idx = target
            product[field][idx] = new_rel
    bak = src_file.with_suffix(src_file.suffix + ".pre-optimize.bak")
    if not bak.exists():
        bak.write_text(src_file.read_text(encoding="utf-8"), encoding="utf-8")
    src_file.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def apply_shop_social(consumer_meta, rewrites: dict[Path, Path]):
    _, src_file, tasks, data = consumer_meta
    anchor = src_file.parent
    for label, current, _wkey, target in tasks:
        kind, entry, field, _ = target
        cur_abs = resolve_site_path(current, from_file=src_file)
        if not cur_abs or cur_abs not in rewrites:
            continue
        entry[field] = _rel_to(rewrites[cur_abs], anchor)
    bak = src_file.with_suffix(src_file.suffix + ".pre-optimize.bak")
    if not bak.exists():
        bak.write_text(src_file.read_text(encoding="utf-8"), encoding="utf-8")
    src_file.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def apply_html_css_js(consumer_meta, rewrites: dict[Path, Path], log_buckets: list):
    _, src_file, tasks, original_text = consumer_meta
    text = original_text
    seen: dict[str, str] = {}  # old_path -> new_path (string replacements)
    for label, current, _wkey, (kind, file_path, path_str) in tasks:
        cur_abs = resolve_site_path(current, from_file=src_file)
        if not cur_abs or cur_abs not in rewrites:
            continue
        # Determine new path relative to source_file's directory
        new_abs = rewrites[cur_abs]
        new_rel = Path(__import__("os").path.relpath(new_abs, src_file.parent)).as_posix()
        seen[path_str] = new_rel
    if not seen:
        return
    new_text = text
    # Sort keys longest first so we don't substring-collide
    for old in sorted(seen.keys(), key=len, reverse=True):
        new_text = new_text.replace(old, seen[old])
    if new_text != text:
        bak = src_file.with_suffix(src_file.suffix + ".pre-optimize.bak")
        if not bak.exists():
            bak.write_text(text, encoding="utf-8")
        src_file.write_text(new_text, encoding="utf-8")
        log_buckets.append({"file": str(src_file), "replaced": seen})


def revert_all():
    # Restore from .pre-optimize.bak siblings
    count = 0
    for bak in SITE_DIR.rglob("*.pre-optimize.bak"):
        target = bak.with_suffix("")  # strip .bak
        target = target.with_suffix(target.suffix)  # keep original ext
        # bak has .pre-optimize.bak; the original suffix is whatever came before
        # easier: bak path string ends with '.pre-optimize.bak'; target = remove that
        s = str(bak)
        if not s.endswith(".pre-optimize.bak"):
            continue
        original_path = Path(s[: -len(".pre-optimize.bak")])
        original_path.write_text(bak.read_text(encoding="utf-8"), encoding="utf-8")
        bak.unlink()
        count += 1
    print(f"Reverted {count} consumer file(s) from .pre-optimize.bak siblings.")
    if REWRITES_LOG.exists():
        REWRITES_LOG.unlink()


# ---------- Main ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quality", type=int, default=92)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--revert", action="store_true")
    args = ap.parse_args()

    if args.revert:
        revert_all()
        return

    print("Discovering image references across the site...")
    products = discover_products()
    shop_social = discover_shop_social()
    html_css_js = discover_html_css_js()

    # Build the unique set of images to optimize, paired with the widest width
    # asked across all references (so each image gets one canonical -opt).
    image_widths: dict[Path, int] = {}
    image_refs: list[tuple[str, str, Path]] = []  # (consumer_label, current_string, abs_path)

    def gather(consumers, source_anchor_fn):
        for cm in consumers:
            kind = cm[0]
            src_file = cm[1]
            tasks = cm[2]
            for label, current, wkey, _target in tasks:
                abs_path = resolve_site_path(current, from_file=src_file)
                if not abs_path or not abs_path.exists():
                    continue
                w = WIDTHS.get(wkey, 1800)
                image_widths[abs_path] = max(image_widths.get(abs_path, 0), w)
                image_refs.append((kind, current, abs_path))

    gather(products, lambda cm: cm[1])
    gather(shop_social, lambda cm: cm[1])
    gather(html_css_js, lambda cm: cm[1])

    n_consumers = len(products) + len(shop_social) + len(html_css_js)
    print(f"Found {len(image_refs)} refs across {n_consumers} files, {len(image_widths)} unique images.")
    print(f"Optimizing at quality={args.quality} (960px catalog/social, 1800px hero/gallery)...")
    print()

    # Optimize each unique image
    by_bucket = {"products_data": {"orig":0,"opt":0,"n":0},
                 "shop_social_data": {"orig":0,"opt":0,"n":0},
                 "html_css_js": {"orig":0,"opt":0,"n":0}}
    rewrites_map: dict[Path, Path] = {}
    for abs_path, width in image_widths.items():
        orig, opt, _skip = optimize_one(abs_path, width, args.quality, args.force)
        rewrites_map[abs_path] = optimized_path(abs_path)

    # Aggregate per-consumer payload (count each ref's image bytes)
    for kind, current, abs_path in image_refs:
        if not abs_path.exists():
            continue
        orig = abs_path.stat().st_size
        opt = rewrites_map[abs_path].stat().st_size if rewrites_map[abs_path].exists() else orig
        b = by_bucket[kind]
        b["orig"] += orig
        b["opt"] += opt
        b["n"] += 1

    print(f"{'consumer':<22} {'refs':>5} {'orig':>10} {'opt':>10} {'saved':>10} {'x':>5}")
    print("-" * 70)
    grand_orig = grand_opt = 0
    for k, v in by_bucket.items():
        if v["n"] == 0: continue
        saved = v["orig"] - v["opt"]
        x = (v["orig"]/v["opt"]) if v["opt"] else 0
        print(f"{k:<22} {v['n']:>5} {fmt_bytes(v['orig']):>10} {fmt_bytes(v['opt']):>10} {fmt_bytes(saved):>10} {x:>4.1f}x")
        grand_orig += v["orig"]
        grand_opt += v["opt"]
    print("-" * 70)
    print(f"{'TOTAL':<22} {len(image_refs):>5} {fmt_bytes(grand_orig):>10} {fmt_bytes(grand_opt):>10} "
          f"{fmt_bytes(grand_orig-grand_opt):>10} {(grand_orig/grand_opt if grand_opt else 0):>4.1f}x")

    print()
    if args.apply:
        log_buckets = []
        for cm in products:
            apply_products(cm, rewrites_map)
        for cm in shop_social:
            apply_shop_social(cm, rewrites_map)
        for cm in html_css_js:
            apply_html_css_js(cm, rewrites_map, log_buckets)
        REWRITES_LOG.write_text(json.dumps(log_buckets, indent=2), encoding="utf-8")
        print(f"Rewrote {len(products)+len(shop_social)+len(log_buckets)} consumer file(s).")
        print(f"Backups: .pre-optimize.bak siblings written next to each modified file.")
        print(f"Rewrite log: {REWRITES_LOG}")
        print("Deploy via git push to publish.")
    else:
        print("DRY-RUN PREVIEW: -opt.jpg files written next to originals; no consumer files modified.")
        print("To ship:   python tools/image_ops/optimize_site_images.py --apply")
        print("To revert: python tools/image_ops/optimize_site_images.py --revert")


if __name__ == "__main__":
    main()
