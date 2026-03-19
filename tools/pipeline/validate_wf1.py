"""
WF1 Caption Batch Validator

Runs after caption generation, before the review server starts.
Checks the generated batch for quota violations, missing fields,
invalid product names, and distribution issues.

Usage:
    python tools/pipeline/validate_wf1.py --last 15
    python tools/pipeline/validate_wf1.py --ids 20260318-001 20260318-002 ...
"""

import argparse
import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent.parent
PIPELINE_FILE = PROJECT_DIR / ".tmp" / "pipeline.json"
REJECTED_FILE = PROJECT_DIR / ".tmp" / "rejected_captions.json"

# ── Active product catalog ────────────────────────────────────────────────────

ACTIVE_PRODUCTS = {
    "Bandits - Glossy Black",
    "Bandits - Matte Black",
    "Bandits - Blue",
    "Bandits - Green",
    "Bandits - Tortoise",
    "Outback - Black",
    "Outback - Blue",
    "Outback - Red",
    "Outback - Green",
    "Rasta - Red",
    "Rasta - Brown",
}

REQUIRED_FIELDS = [
    "angle",
    "hook_type",
    "vibe",
    "creative_hypothesis",
    "visual_anchor",
    "caption_text",
    "hashtags",
]

VALID_VISUAL_ANCHORS = {"PERSON", "PRODUCT"}
VALID_ANGLES = {
    "Pain Relief",
    "Identity",
    "Lifestyle",
    "Status / Glow Up",
    "Value / Deal",
    "Convenience / Fast Delivery",
}

BUNDLE_SIGNALS = ["₱1,200", "2 pairs", "dalawang pares", "bundle"]

# ── Checks ────────────────────────────────────────────────────────────────────

def check_count(captions, expected=15):
    if len(captions) != expected:
        return f"Expected {expected} captions, got {len(captions)}"
    return None


def check_required_fields(captions):
    issues = []
    for c in captions:
        missing = [f for f in REQUIRED_FIELDS if not c.get(f)]
        if missing:
            issues.append(f"  #{c['id']}: missing fields — {', '.join(missing)}")
    return issues


def check_visual_anchor_distribution(captions):
    issues = []
    anchors = [c.get("visual_anchor", "") for c in captions]
    invalid = [c["id"] for c in captions if c.get("visual_anchor") not in VALID_VISUAL_ANCHORS]
    if invalid:
        issues.append(f"  Invalid visual_anchor values on: {', '.join(str(i) for i in invalid)}")

    product_count = anchors.count("PRODUCT")
    person_count = anchors.count("PERSON")
    total = len(captions)

    if total > 0:
        product_pct = product_count / total
        if product_pct < 0.60 or product_pct > 0.80:
            issues.append(
                f"  Visual anchor distribution off: {product_count} PRODUCT / {person_count} PERSON "
                f"(expected ~70/30, got {product_pct:.0%}/{1-product_pct:.0%})"
            )
    return issues


def check_hook_type_cap(captions, cap=3):
    issues = []
    counts = {}
    for c in captions:
        ht = c.get("hook_type", "")
        counts[ht] = counts.get(ht, 0) + 1
    for ht, n in counts.items():
        if n > cap:
            issues.append(f"  Hook type '{ht}' appears {n} times (max {cap})")
    return issues


def check_bundle_quota(captions, minimum=3):
    bundle_count = 0
    for c in captions:
        text = c.get("caption_text", "").lower()
        if any(signal.lower() in text for signal in BUNDLE_SIGNALS):
            bundle_count += 1
    if bundle_count < minimum:
        return f"  Only {bundle_count} bundle caption(s) found (minimum {minimum})"
    return None


def check_product_names(captions):
    issues = []
    for c in captions:
        rp = c.get("recommended_products", "")
        if not rp:
            continue
        names = [n.strip() for n in rp.split(",")]
        invalid = [n for n in names if n and n not in ACTIVE_PRODUCTS]
        if invalid:
            issues.append(f"  #{c['id']}: invalid product(s) — {', '.join(invalid)}")
    return issues


def check_duplicate_vibe_angle(captions):
    """Flag vibe+angle combos that already exist in rejected_captions.json."""
    issues = []
    if not REJECTED_FILE.exists():
        return issues

    rejected = json.loads(REJECTED_FILE.read_text())
    rejected_combos = {
        (r.get("vibe", ""), r.get("angle", ""))
        for r in rejected
        if r.get("status") == "REJECTED"
    }

    for c in captions:
        combo = (c.get("vibe", ""), c.get("angle", ""))
        if combo in rejected_combos:
            issues.append(f"  #{c['id']}: vibe+angle combo '{combo[0]} / {combo[1]}' was previously rejected")
    return issues


def check_angle_distribution(captions):
    """Warn if fewer than 3 distinct angles used."""
    angles = {c.get("angle", "") for c in captions}
    if len(angles) < 3:
        return f"  Only {len(angles)} distinct angle(s) used: {', '.join(angles)}"
    return None


def check_emoji_count(captions):
    """Each caption must have 1-2 emojis, never zero."""
    import re
    emoji_pattern = re.compile(
        "[\U0001f600-\U0001f64f\U0001f300-\U0001f5ff\U0001f680-\U0001f6ff"
        "\U0001f1e0-\U0001f1ff\U00002702-\U000027b0\U0001f900-\U0001f9ff"
        "\U0001fa00-\U0001fa6f\U0001fa70-\U0001faff\U00002600-\U000026ff"
        "\U0000fe0f\U0000200d]+"
    )
    issues = []
    for c in captions:
        text = c.get("caption_text", "")
        emojis = emoji_pattern.findall(text)
        count = len(emojis)
        if count == 0:
            issues.append(f"  #{c['id']}: no emojis (minimum 1)")
        elif count > 2:
            issues.append(f"  #{c['id']}: {count} emojis (maximum 2)")
    return issues


def check_cta_presence(captions):
    """Every caption must end with a CTA on its own line."""
    cta_phrases = ["dm us", "message us", "order now", "order na ngayon"]
    issues = []
    for c in captions:
        text = c.get("caption_text", "").strip()
        last_line = text.split("\n")[-1].strip().lower()
        # Remove trailing period/punctuation for matching
        last_clean = last_line.rstrip(".!,")
        if not any(cta in last_clean for cta in cta_phrases):
            issues.append(f"  #{c['id']}: missing CTA on last line")
    return issues


def check_batch_id(captions):
    """All captions in a batch should share the same batch_id."""
    issues = []
    batch_ids = set()
    missing = []
    for c in captions:
        bid = c.get("batch_id", "")
        if not bid:
            missing.append(str(c["id"]))
        else:
            batch_ids.add(bid)
    if missing:
        issues.append(f"  Missing batch_id on: {', '.join(missing)}")
    if len(batch_ids) > 1:
        issues.append(f"  Multiple batch_ids found: {', '.join(sorted(batch_ids))}")
    return issues


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Validate a WF1 caption batch")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--last", type=int, metavar="N", help="Validate the N most recently added PENDING captions")
    group.add_argument("--ids", nargs="+", help="Explicit caption IDs to validate")
    args = parser.parse_args()

    if not PIPELINE_FILE.exists():
        print("Error: pipeline.json not found", file=sys.stderr)
        sys.exit(1)

    pipeline = json.loads(PIPELINE_FILE.read_text())

    if args.ids:
        id_set = set(str(i) for i in args.ids)
        captions = [c for c in pipeline if str(c["id"]) in id_set]
        if not captions:
            print("Error: none of the specified IDs found in pipeline.json", file=sys.stderr)
            sys.exit(1)
    else:
        # --last N: grab N most recent PENDING captions by position (last added)
        pending = [c for c in pipeline if c.get("status") == "PENDING"]
        captions = pending[-args.last:]
        if not captions:
            print("No PENDING captions found in pipeline.json", file=sys.stderr)
            sys.exit(1)

    print(f"\nWF1 Validator — checking {len(captions)} caption(s)")
    print("─" * 50)

    issues = []
    warnings = []

    # Count check
    if args.last:
        count_issue = check_count(captions, expected=args.last)
        if count_issue:
            issues.append(count_issue)

    # Required fields
    field_issues = check_required_fields(captions)
    issues.extend(field_issues)

    # Visual anchor distribution
    anchor_issues = check_visual_anchor_distribution(captions)
    issues.extend(anchor_issues)

    # Hook type cap
    hook_issues = check_hook_type_cap(captions)
    issues.extend(hook_issues)

    # Bundle quota
    bundle_issue = check_bundle_quota(captions)
    if bundle_issue:
        warnings.append(bundle_issue)

    # Product names
    product_issues = check_product_names(captions)
    issues.extend(product_issues)

    # Duplicate vibe+angle from rejects
    dupe_issues = check_duplicate_vibe_angle(captions)
    warnings.extend(dupe_issues)

    # Angle distribution
    angle_issue = check_angle_distribution(captions)
    if angle_issue:
        warnings.append(angle_issue)

    # Emoji count (1-2 per caption)
    emoji_issues = check_emoji_count(captions)
    issues.extend(emoji_issues)

    # CTA presence
    cta_issues = check_cta_presence(captions)
    issues.extend(cta_issues)

    # Batch ID consistency
    batch_issues = check_batch_id(captions)
    warnings.extend(batch_issues)

    # ── Output ────────────────────────────────────────────────────────────────

    if issues:
        print(f"FAIL — {len(issues)} issue(s) found:\n")
        for issue in issues:
            print(f"[FAIL] {issue}")
        if warnings:
            print()
            for w in warnings:
                print(f"[WARN] {w}")
        print()
        sys.exit(1)
    elif warnings:
        print(f"PASS with warnings — {len(warnings)} warning(s):\n")
        for w in warnings:
            print(f"[WARN] {w}")
        print()
        sys.exit(0)
    else:
        print("PASS — all checks passed")
        print(f"  {len(captions)} captions | anchors OK | hooks OK | products OK")
        sys.exit(0)


if __name__ == "__main__":
    main()
