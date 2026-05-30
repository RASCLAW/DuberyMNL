# image_ops — Pillow-based image optimization and collage composition

**What it does**
- Composes multi-image collages (7 layouts) into 1080x1080 PNG files for the feed scheduler.
- Generates `<original>-opt.jpg` siblings for every image referenced by the landing site — resized and JPEG-compressed — without touching the originals.
- Operates in dry-run mode by default; writes to consumers (data.json, HTML, CSS, JS) only with `--apply`.
- Backs up every modified file as a `.pre-optimize.bak` sibling; `--revert` restores them all.

**Key files**

| File | Purpose |
|------|---------|
| `compose.py` | Pillow collage composer. Accepts `--layout`, `--inputs`, `--output`. Used by the feed scheduler to build multi-image posts. |
| `optimize_catalog_images.py` | Optimizes images referenced by `dubery-landing-v3/products/data.json` (thumb, hover, hero, gallery, feature fields). Rewrites data.json with `--apply`. |
| `optimize_site_images.py` | Site-wide optimizer. Discovers all image refs across `products/data.json`, `shop-social/data.json`, and all HTML/CSS/JS files in `dubery-landing-v3/`. |

**Run**

```bash
# Collage: compose a 2x2 grid
python tools/image_ops/compose.py --layout 2x2 --inputs a.png b.png c.png d.png --output .tmp/test.png

# Available layouts: 2h, 2v, 1p2, 2x2, 3h, hero3, ba

# Optimize catalog images (dry-run preview — writes -opt files, data.json untouched)
python tools/image_ops/optimize_catalog_images.py

# Optimize catalog images and rewrite data.json to point at -opt versions
python tools/image_ops/optimize_catalog_images.py --apply

# Restore data.json from backup
python tools/image_ops/optimize_catalog_images.py --revert

# Site-wide optimization (dry-run)
python tools/image_ops/optimize_site_images.py

# Site-wide optimization — rewrite all consumers (data.json + HTML/CSS/JS)
python tools/image_ops/optimize_site_images.py --apply

# Undo --apply across all modified files
python tools/image_ops/optimize_site_images.py --revert

# Common optional flags (both optimizers)
--quality 80   # JPEG quality, default 92
--force        # Re-generate -opt files even if cached
```

**Inputs / outputs**

- `compose.py` — reads local image files passed via `--inputs`; writes a single PNG to `--output`.
- `optimize_catalog_images.py` — reads `dubery-landing-v3/products/data.json`; writes `*-opt.jpg` siblings next to each referenced image; optionally rewrites `data.json` in place.
- `optimize_site_images.py` — reads `dubery-landing-v3/products/data.json`, `dubery-landing-v3/shop-social/data.json`, and all `.html`/`.css`/`.js` files under `dubery-landing-v3/`; writes `*-opt.jpg` siblings; optionally rewrites all consumer files in place; logs HTML/CSS/JS rewrites to `.tmp/site-optimize-rewrites.json`.

**Auth / env**

None. No API calls, no `.env` required. Depends only on Pillow (`pip install Pillow`).

**Gotchas**

- `optimize_site_images.py` replaces path strings by exact string match (longest-first), so references that share a filename prefix could collide — review the rewrite log at `.tmp/site-optimize-rewrites.json` after `--apply`.
- Both optimizers skip re-generating an `-opt.jpg` if it already exists and is newer than the source. Pass `--force` to override.
- After `--apply`, deploy via `git push` (Vercel/Cloudflare picks up the rewritten files automatically).
