# landing — Export approved caption data and ad images to the landing page

**What it does**
- Reads `.tmp/pipeline.json` and filters entries with `status == IMAGE_APPROVED` (excludes "classic" product refs and hardcoded ID 31).
- Writes `dubery-landing/data/captions.json` — a public JSON file consumed by the landing page's JS.
- Copies matching ad images from `contents/ads/dubery_<id>.jpg` into `dubery-landing/assets/ads/`.
- Skips entries that have no local image in either source or destination directory.

**Key files**

| File | Purpose |
|------|---------|
| `export_captions.py` | Single entrypoint — filters pipeline, writes captions.json, copies images |

**Run**

```bash
# Full export
python tools/landing/export_captions.py

# Preview what would be written without touching any files
python tools/landing/export_captions.py --dry-run

# Export only entries that have an ad_set tag
python tools/landing/export_captions.py --ads-only
```

**Inputs / outputs**

| Direction | Path | Notes |
|-----------|------|-------|
| Input | `.tmp/pipeline.json` | Local pipeline cache; script exits with error if missing |
| Input | `contents/ads/dubery_<id>.jpg` | Source ad images |
| Output | `dubery-landing/data/captions.json` | JSON array of approved caption records (id, headline, vibe, angle, visual_anchor, product_ref, card_image) |
| Output | `dubery-landing/assets/ads/dubery_<id>.jpg` | Ad images copied from source; dirs are created if absent |

**Auth / env**

None. No API calls, no OAuth, no `.env` required.

**Gotchas**

- `.tmp/pipeline.json` must exist (run the pipeline sync step first if it is missing).
- Headline falls back in order: `headline` field → first line of `caption_text` → `vibe` → hardcoded default.
- Entries already present in `dubery-landing/assets/ads/` are counted as valid even if the source file in `contents/ads/` is gone — they are not re-copied in that case.
