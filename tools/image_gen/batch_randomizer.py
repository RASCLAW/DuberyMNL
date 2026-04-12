"""
Batch Randomizer -- picks random skill + product + layout + angle combos.

Outputs a JSON assignment list. Each assignment is fed to the corresponding
Claude skill to generate the actual prompt, then to generate_vertex.py.

Usage:
    python tools/image_gen/batch_randomizer.py                     # 11 mixed (one per product)
    python tools/image_gen/batch_randomizer.py --count 5            # 5 mixed
    python tools/image_gen/batch_randomizer.py --type ugc           # UGC only
    python tools/image_gen/batch_randomizer.py --type brand-bold    # Bold only
    python tools/image_gen/batch_randomizer.py --count 3 --type brand-collection

Output: JSON array of assignments to stdout
"""

import json
import random
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent.parent
REFS_DIR = PROJECT_DIR / "contents" / "assets" / "product-refs"

# --- Products and angles ---

PRODUCTS = [
    "Bandits Blue", "Bandits Glossy Black", "Bandits Green",
    "Bandits Matte Black", "Bandits Tortoise",
    "Outback Black", "Outback Blue", "Outback Green", "Outback Red",
    "Rasta Brown", "Rasta Red",
]

PRODUCT_FINISH = {
    "Bandits Blue": "glossy", "Bandits Glossy Black": "glossy",
    "Bandits Green": "glossy", "Bandits Matte Black": "matte",
    "Bandits Tortoise": "matte", "Outback Black": "matte",
    "Outback Blue": "matte", "Outback Green": "matte",
    "Outback Red": "matte", "Rasta Brown": "matte", "Rasta Red": "matte",
}

def product_to_folder(name: str) -> str:
    return name.lower().replace(" ", "-")

def available_angles(product: str) -> list[int]:
    """Return usable single-view angles (excludes -2 and -multi)."""
    folder = REFS_DIR / product_to_folder(product)
    angles = []
    for n in [1, 3, 4]:
        if (folder / f"{product_to_folder(product)}-{n}.png").exists():
            angles.append(n)
    return angles

def ref_path(product: str, angle: int) -> str:
    slug = product_to_folder(product)
    return f"contents/assets/product-refs/{slug}/{slug}-{angle}.png"

# --- Skill types and their options ---

UGC_PRODUCT_SCENARIOS = [
    "PRODUCT_HOLD", "COD_DELIVERY", "REVIEW_UNBOX", "DASHBOARD_FLEX",
    "CAFE_TABLE", "BEACH_SURFACE", "GYM_BAG", "DESK_SHOT",
    "SUNSET_PRODUCT", "TRAVEL_FLATLAY", "OUTDOOR_SURFACE",
]

UGC_PERSON_SCENARIOS = [
    "SELFIE_OUTDOOR", "BEACH_CANDID", "OOTD_STREET", "COMMUTE_FLEX",
    "WEEKEND_GROUP", "FESTIVAL", "FUN_RUN", "BIKING",
    "BADMINTON", "SUNSET_VIBE",
]

CALLOUT_LAYOUTS = ["RADIAL", "SPLIT", "EXPLODED", "NUMBERED", "TOP_BOTTOM"]
BOLD_LAYOUTS = ["TYPE_COLLAGE", "TEXTURE", "SPLIT_TEXT", "KNOCKOUT"]
COLLECTION_LAYOUTS = ["FLAT_LAY", "HERO_CAST", "DIAGONAL", "FAN_SPREAD", "UNBOX_FLATLAY"]

SKILL_TYPES = ["ugc", "brand-callout", "brand-bold", "brand-collection"]

# Weighted: 40% UGC, 20% callout, 20% bold, 20% collection
SKILL_WEIGHTS = [40, 20, 20, 20]


def pick_ugc_scenario() -> tuple[str, str]:
    """Return (scenario, anchor_type) with 70/30 product/person bias."""
    if random.random() < 0.70:
        return random.choice(UGC_PRODUCT_SCENARIOS), "product"
    else:
        return random.choice(UGC_PERSON_SCENARIOS), "person"


def pick_gender() -> str:
    return random.choice(["male", "female"])


def make_assignment(skill_type: str, product: str, used_combos: set, used_layouts: dict) -> dict:
    """Build one assignment, avoiding duplicate combos and layouts within same skill."""
    angles = available_angles(product)
    angle = random.choice(angles)

    if skill_type == "ugc":
        scenario, anchor = pick_ugc_scenario()
        combo_key = f"ugc-{scenario}-{product}"
        # Retry scenario if duplicate
        for _ in range(10):
            if combo_key not in used_combos:
                break
            scenario, anchor = pick_ugc_scenario()
            combo_key = f"ugc-{scenario}-{product}"
        used_combos.add(combo_key)

        assignment = {
            "skill": "dubery-ugc-prompt-writer",
            "input": {
                "scenario_type": scenario,
                "subject_gender": pick_gender() if anchor == "person" else None,
                "product_ref": product,
                "aspect_ratio": "9:16",
                "anchor_type": anchor,
            },
            "product_angle": angle,
            "image_input": [ref_path(product, angle)],
        }

    elif skill_type == "brand-callout":
        unused_layouts = [l for l in CALLOUT_LAYOUTS if l not in used_layouts.get("callout", set())]
        layout = random.choice(unused_layouts) if unused_layouts else random.choice(CALLOUT_LAYOUTS)
        used_layouts.setdefault("callout", set()).add(layout)
        combo_key = f"callout-{layout}-{product}"
        used_combos.add(combo_key)

        assignment = {
            "skill": "dubery-brand-callout",
            "input": {
                "layout": layout,
                "product_ref": product,
                "headline": None,
                "features": None,
            },
            "product_angle": angle,
            "image_input": [ref_path(product, angle)],
        }

    elif skill_type == "brand-bold":
        unused_layouts = [l for l in BOLD_LAYOUTS if l not in used_layouts.get("bold", set())]
        layout = random.choice(unused_layouts) if unused_layouts else random.choice(BOLD_LAYOUTS)
        used_layouts.setdefault("bold", set()).add(layout)
        combo_key = f"bold-{layout}-{product}"
        used_combos.add(combo_key)

        assignment = {
            "skill": "dubery-brand-bold",
            "input": {
                "layout": layout,
                "product_ref": product,
                "headline": None,
            },
            "product_angle": angle,
            "image_input": [ref_path(product, angle)],
        }

    elif skill_type == "brand-collection":
        unused_layouts = [l for l in COLLECTION_LAYOUTS if l not in used_layouts.get("collection", set())]
        layout = random.choice(unused_layouts) if unused_layouts else random.choice(COLLECTION_LAYOUTS)
        used_layouts.setdefault("collection", set()).add(layout)
        # Pick 3 products from the same series when possible
        series = product.split(" ")[0]  # Bandits / Outback / Rasta
        series_products = [p for p in PRODUCTS if p.startswith(series)]
        if len(series_products) >= 3:
            collection = random.sample(series_products, 3)
        else:
            collection = series_products[:]
            while len(collection) < 3:
                extra = random.choice([p for p in PRODUCTS if p not in collection])
                collection.append(extra)

        combo_key = f"collection-{layout}-{'-'.join(sorted(collection))}"
        used_combos.add(combo_key)

        # All products in collection use same angle
        shared_angles = set(available_angles(collection[0]))
        for p in collection[1:]:
            shared_angles &= set(available_angles(p))
        shared_angle = random.choice(list(shared_angles)) if shared_angles else 1

        assignment = {
            "skill": "dubery-brand-collection",
            "input": {
                "layout": layout,
                "product_refs": collection,
                "hero": collection[0],
                "headline": None,
            },
            "product_angle": shared_angle,
            "image_input": [ref_path(p, shared_angle) for p in collection],
        }

    return assignment


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Batch Randomizer")
    parser.add_argument("--count", type=int, default=11)
    parser.add_argument("--type", choices=["ugc", "brand-callout", "brand-bold", "brand-collection", "mix"], default="mix")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    # Shuffle products for variety
    products = PRODUCTS[:]
    random.shuffle(products)

    assignments = []
    used_combos = set()
    used_layouts = {}

    for i in range(args.count):
        product = products[i % len(products)]

        if args.type == "mix":
            skill_type = random.choices(SKILL_TYPES, weights=SKILL_WEIGHTS, k=1)[0]
        else:
            skill_type = args.type

        assignment = make_assignment(skill_type, product, used_combos, used_layouts)
        assignment["batch_index"] = i + 1
        assignments.append(assignment)

    # Print summary to stderr
    skill_counts = {}
    for a in assignments:
        s = a["skill"]
        skill_counts[s] = skill_counts.get(s, 0) + 1

    print(f"Batch: {len(assignments)} assignments", file=sys.stderr)
    for skill, count in sorted(skill_counts.items()):
        print(f"  {skill}: {count}", file=sys.stderr)

    products_used = set()
    for a in assignments:
        if "product_refs" in a.get("input", {}):
            products_used.update(a["input"]["product_refs"])
        elif "product_ref" in a.get("input", {}):
            products_used.add(a["input"]["product_ref"])
    print(f"  Products: {len(products_used)}/11 represented", file=sys.stderr)

    angles_used = set(a.get("product_angle") for a in assignments)
    print(f"  Angles: {sorted(angles_used)}", file=sys.stderr)

    # Output JSON
    print(json.dumps(assignments, indent=2))


if __name__ == "__main__":
    main()
