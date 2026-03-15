"""
DuberyMNL Pipeline Status
Quick snapshot of the pipeline without opening Notion or the Sheet.

Run:
    python tools/status.py
"""

import json
from pathlib import Path
from datetime import date

PROJECT_DIR = Path(__file__).parent.parent
TMP_DIR = PROJECT_DIR / ".tmp"
IMAGES_DIR = PROJECT_DIR / "output" / "images"

STATUS_ORDER = [
    "PENDING",
    "APPROVED",
    "PROMPT_READY",
    "DONE",
    "IMAGE_APPROVED",
    "IMAGE_REJECTED",
    "IMAGE_FAILED",
    "POSTED",
]


def load_pipeline():
    path = TMP_DIR / "pipeline.json"
    return json.loads(path.read_text()) if path.exists() else []


def load_rejected():
    path = TMP_DIR / "rejected_captions.json"
    return json.loads(path.read_text()) if path.exists() else []


def get_unmapped_images(pipeline_ids):
    if not IMAGES_DIR.exists():
        return []
    mapped = {f"dubery_{i}.jpg" for i in pipeline_ids}
    unmapped = []
    for f in IMAGES_DIR.iterdir():
        if f.is_file() and f.name not in mapped and f.parent.name != "rejected":
            # Skip zone identifier files
            if not f.name.endswith(".Identifier"):
                unmapped.append(f.name)
    return sorted(unmapped)


def main():
    pipeline = load_pipeline()
    rejected = load_rejected()
    all_captions = pipeline + rejected

    # Count by status
    counts = {}
    ids_by_status = {}
    for c in all_captions:
        s = c.get("status", "UNKNOWN")
        counts[s] = counts.get(s, 0) + 1
        ids_by_status.setdefault(s, []).append(c["id"])

    # Rejected captions (caption-level, not image-level)
    caption_rejected = [c for c in rejected if c.get("status") == "REJECTED"]
    counts["REJECTED"] = len(caption_rejected)

    # Has image / has prompt
    pipeline_ids = [c["id"] for c in pipeline]
    has_image = sum(
        1 for c in pipeline
        if (IMAGES_DIR / f"dubery_{c['id']}.jpg").exists()
        or (IMAGES_DIR / "rejected" / f"dubery_{c['id']}.jpg").exists()
    )
    has_prompt = sum(
        1 for c in all_captions
        if (TMP_DIR / f"{c['id']}_prompt_structured.json").exists()
    )
    unmapped = get_unmapped_images(pipeline_ids)

    # Print
    W = 38
    today = date.today().strftime("%Y-%m-%d")
    print(f"\nDuberyMNL Pipeline \u2014 {today}")
    print("\u2501" * W)

    for s in STATUS_ORDER:
        n = counts.get(s, 0)
        id_list = ids_by_status.get(s, [])
        id_str = f"  \u2190 {id_list}" if id_list and n <= 6 else ""
        print(f"  {s:<20} {n:>4}{id_str}")

    if caption_rejected:
        ids = [c["id"] for c in caption_rejected]
        print(f"  {'REJECTED (caption)':<20} {len(caption_rejected):>4}  \u2190 {ids}")

    print("\u2501" * W)
    total = len(all_captions)
    print(f"  {'Total tracked':<20} {total:>4}")
    print(f"  {'Has image':<20} {has_image:>4} / {total}")
    print(f"  {'Has prompt':<20} {has_prompt:>4} / {total}")
    if unmapped:
        print(f"  {'Unmapped files':<20} {len(unmapped):>4}  \u2190 {unmapped[:4]}{'...' if len(unmapped) > 4 else ''}")
    print()


if __name__ == "__main__":
    main()
