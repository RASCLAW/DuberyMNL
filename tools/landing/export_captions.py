"""
Export caption data and ad images for the DuberyMNL landing page.

Reads .tmp/pipeline.json and generates:
  1. dubery-landing/data/captions.json  — public data file for dynamic JS
  2. dubery-landing/assets/ads/         — ad images copied from output/images/

Only IMAGE_APPROVED entries with a local image file are exported.

Usage:
    python tools/landing/export_captions.py
    python tools/landing/export_captions.py --dry-run
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent.parent
TMP_DIR = PROJECT_DIR / ".tmp"
IMAGES_DIR = PROJECT_DIR / "output" / "images"
LANDING_DIR = PROJECT_DIR / "dubery-landing"
DATA_DIR = LANDING_DIR / "data"
ADS_DIR = LANDING_DIR / "assets" / "ads"


def load_pipeline():
    path = TMP_DIR / "pipeline.json"
    if not path.exists():
        print("Error: .tmp/pipeline.json not found", file=sys.stderr)
        sys.exit(1)
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser(description="Export caption data + images for landing page")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing files")
    parser.add_argument("--ads-only", action="store_true", help="Export only entries tagged with an ad_set")
    args = parser.parse_args()

    pipeline = load_pipeline()
    EXCLUDED_IDS = {31}
    approved = [
        e for e in pipeline
        if e.get("status") == "IMAGE_APPROVED"
        and "classic" not in e.get("product_ref", "").lower()
        and e.get("id") not in EXCLUDED_IDS
    ]

    if args.ads_only:
        approved = [e for e in approved if e.get("ad_set")]
        print(f"Filtering to ad-tagged entries only ({len(approved)} found)")

    captions = []
    images_to_copy = []
    skipped = []

    for entry in approved:
        caption_id = entry["id"]
        image_src = IMAGES_DIR / f"dubery_{caption_id}.jpg"
        image_dst = ADS_DIR / f"dubery_{caption_id}.jpg"

        # Accept if image exists in output/images/ OR already in assets/ads/
        if not image_src.exists() and not image_dst.exists():
            skipped.append(caption_id)
            continue

        # Only queue for copy if source exists and destination doesn't
        if image_src.exists():
            images_to_copy.append((image_src, image_dst))

        # Headline: use headline field if present, else first line of caption_text, else vibe
        headline = entry.get("headline")
        if not headline:
            caption_text = entry.get("caption_text", "")
            first_line = caption_text.split("\n")[0].strip() if caption_text else ""
            headline = first_line[:80] if first_line else entry.get("vibe", "See Clearer. Look Sharper.")

        captions.append({
            "id": caption_id,
            "headline": headline,
            "vibe": entry.get("vibe", ""),
            "angle": entry.get("angle", ""),
            "visual_anchor": entry.get("visual_anchor", ""),
            "product_ref": entry.get("product_ref", ""),
            "card_image": entry.get("card_image", ""),
        })


    print(f"Exporting {len(captions)} captions ({len(skipped)} skipped — no local image: {skipped})")

    if args.dry_run:
        print("\nDRY RUN — no files written")
        print(f"  Would write: {DATA_DIR}/captions.json ({len(captions)} entries)")
        for src, dst in images_to_copy:
            print(f"  Would copy:  {src.name} → {dst.relative_to(PROJECT_DIR)}")
        return

    # Ensure output dirs exist
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ADS_DIR.mkdir(parents=True, exist_ok=True)

    # Write captions.json
    out_path = DATA_DIR / "captions.json"
    out_path.write_text(json.dumps(captions, indent=2, ensure_ascii=False))
    print(f"  Wrote: {out_path.relative_to(PROJECT_DIR)}")

    # Copy images
    copied = 0
    for src, dst in images_to_copy:
        shutil.copy2(src, dst)
        copied += 1
    print(f"  Copied: {copied} images → {ADS_DIR.relative_to(PROJECT_DIR)}/")

    print(f"\nDone. {len(captions)} captions exported.")


if __name__ == "__main__":
    main()
