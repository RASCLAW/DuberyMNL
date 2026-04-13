"""
v3 Pipeline Scene Randomizer -- true RNG for all scene dimensions.

Picks random combinations for: category, direction, location, lighting,
subject (person cats) or surface (product cats), objects, and camera.

Checks layout_history.json to avoid repeats.

Usage:
    python tools/image_gen/v3_randomizer.py                    # 1 assignment
    python tools/image_gen/v3_randomizer.py --count 3          # 3 assignments
    python tools/image_gen/v3_randomizer.py --category UGC_PERSON_WEARING
    python tools/image_gen/v3_randomizer.py --product outback-blue

Output: JSON array of assignments to stdout
"""

import json
import random
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent.parent

# --- Load assets ---

def load_json(path: str) -> dict:
    return json.loads((PROJECT_DIR / path).read_text(encoding="utf-8"))


# --- Categories ---

CATEGORIES = [
    "UGC_PRODUCT",
    "UGC_PERSON_WEARING",
    "UGC_PERSON_HOLDING",
    "UGC_HEADBAND",
    "BRAND_MODEL",
]

# Weighted: 25% product, 30% wearing, 15% holding, 10% headband, 20% brand_model
CATEGORY_WEIGHTS = [25, 30, 15, 10, 20]

PERSON_CATEGORIES = {"UGC_PERSON_WEARING", "UGC_PERSON_HOLDING", "UGC_HEADBAND", "BRAND_MODEL"}
PRODUCT_CATEGORIES = {"UGC_PRODUCT"}

# --- Variety Banks ---

LOCATIONS = [
    # Beach / water
    "tropical beach with white sand and turquoise water",
    "rocky coastline with crashing waves",
    "resort infinity pool overlooking the ocean",
    "fishing boat on calm morning water",
    "lakeside dock with misty mountains behind",
    # Urban
    "Manila BGC rooftop bar with city skyline",
    "colorful Manila street with jeepney passing behind",
    "urban skatepark with concrete ramps and graffiti walls",
    "outdoor night market with hanging string lights and food stalls",
    "modern coffee shop patio with exposed brick",
    "basketball court at a neighborhood park",
    "university campus lawn with old stone buildings behind",
    "motorcycle parked on a coastal highway overlook",
    # Nature
    "Banaue rice terrace overlook at sunrise",
    "mountain trail viewpoint above the clouds",
    "dense tropical jungle path with dappled sunlight",
    "waterfall pool in a hidden cove",
    "coconut palm grove with hammock",
    # Indoor / lifestyle
    "gym with dumbbells and rubber mats",
    "co-working space with big windows and natural light",
    "vintage barbershop with leather chair",
    "hotel lobby with marble floors and tropical plants",
    "food truck park with picnic tables",
]

LIGHTING = [
    # Warm
    "golden hour sunlight from the left, warm orange tones",
    "sunrise light from behind, soft pink and gold rim glow",
    "warm tungsten cafe lights mixed with fading daylight",
    # Neutral
    "bright midday sun from directly above, clean hard shadows",
    "overcast sky with soft even diffused light, no harsh shadows",
    "morning light through scattered clouds, gentle and directional",
    # Cool / dramatic
    "blue hour twilight, deep blue sky with city lights starting up",
    "neon signs casting colored light -- pink, blue, and green spill",
    "harsh afternoon sun with deep contrasty shadows",
    "dappled shade under tropical trees, shifting light patches",
    # Moody
    "dramatic storm clouds with a single break of golden light",
    "foggy morning with soft milky light and low visibility",
    "late afternoon side-light raking across at a low angle",
    "backlit silhouette lighting with strong rim glow and dark face fill",
]

# --- Person banks ---

GENDERS = ["male", "female"]

MALE_AGES = ["early 20s", "mid 20s", "late 20s", "early 30s"]
FEMALE_AGES = ["early 20s", "mid 20s", "late 20s", "early 30s"]

MALE_HAIR = [
    "short cropped fade",
    "textured messy top",
    "buzz cut",
    "slicked back",
    "curly medium length",
]

FEMALE_HAIR = [
    "long straight dark hair",
    "wavy beach hair past shoulders",
    "short bob with side part",
    "ponytail pulled back",
    "braids with loose strands",
    "messy bun",
]

MALE_OUTFITS = [
    "plain white crew-neck t-shirt",
    "black tank top",
    "unbuttoned cream linen shirt over bare chest",
    "navy blue polo shirt",
    "grey hoodie with sleeves pushed up",
    "denim jacket over white tee",
    "basketball jersey",
    "plain black t-shirt",
    "flannel shirt rolled to elbows",
    "fitted rash guard",
]

FEMALE_OUTFITS = [
    "black bikini top",
    "white cropped tank top",
    "denim jacket over sundress",
    "off-shoulder floral blouse",
    "fitted activewear sports bra and leggings",
    "oversized vintage band tee",
    "linen wrap top in earth tone",
    "plain white t-shirt knotted at the waist",
    "colorful swimsuit coverup",
    "casual striped button-up tied at front",
]

EXPRESSIONS = [
    "relaxed confident smile",
    "laughing mid-conversation",
    "focused and looking into the distance",
    "candid mid-action, not looking at camera",
    "serene and peaceful with eyes slightly down",
    "grinning wide, carefree energy",
    "cool and composed, slight smirk",
]

POSES_WEARING = [
    "looking off-camera to the side",
    "looking directly at camera",
    "chin slightly raised, confident",
    "leaning forward with elbows on knees",
    "arms crossed, relaxed stance",
    "one hand touching the temple arm of the sunglasses",
    "mid-stride walking",
]

POSES_HOLDING = [
    "holding sunglasses up toward camera with one hand, arm extended",
    "holding sunglasses at chest level, about to put them on",
    "dangling sunglasses from one hand at their side",
    "holding sunglasses near face with both hands",
]

POSES_HEADBAND = [
    "sunglasses pushed up on top of head, looking at camera",
    "sunglasses on top of head, looking down at phone",
    "sunglasses pushed up as headband, wind blowing hair",
    "sunglasses on head, hands behind head stretching",
]

# --- Product surface banks ---

SURFACES = [
    "weathered wooden table with visible grain",
    "smooth polished concrete ledge",
    "white marble cafe table",
    "woven rattan tray",
    "matte black leather surface",
    "sun-bleached driftwood log",
    "flat volcanic rock",
    "wooden surfboard laying on sand",
    "stacked old hardcover books",
    "clean white linen cloth on a table",
    "rustic clay tile",
    "bamboo mat",
    "chrome motorcycle tank",
    "gym bench with rubber padding",
    "wooden park bench slat",
]

NEARBY_OBJECTS_PRODUCT = [
    "iced coffee in a clear glass with condensation",
    "cold coconut with a straw",
    "small potted succulent",
    "folded linen towel",
    "leather wallet and keys",
    "phone face-down on the surface",
    "half-eaten tropical fruit",
    "bottle of sunscreen",
    "worn baseball cap nearby",
    "earbuds case",
    "nothing -- clean surface, product only",
    "seashell and small pebbles scattered naturally",
    "open paperback book face-down",
]

NEARBY_OBJECTS_PERSON = [
    "city skyline in background",
    "surfboard leaning against a wall",
    "motorcycle behind them",
    "cold drink in hand",
    "skateboard underfoot",
    "backpack slung over one shoulder",
    "friend blurred in background",
    "food stall / vendor behind",
    "palm trees framing the shot",
    "graffiti wall behind",
    "nothing extra -- clean background focus on subject",
    "bicycle leaning nearby",
]

# --- Camera presets ---

CAMERA_PRESETS = {
    "UGC_PRODUCT": [
        "50mm, f/2.8, slightly elevated angle looking down at product",
        "50mm, f/2.8, eye-level angle straight on",
        "35mm, f/2.0, low angle looking up at product with sky behind",
    ],
    "UGC_PERSON_WEARING": [
        "50mm candid, f/2.0, natural handheld framing, chest up",
        "50mm, f/1.8, tight headshot framing",
        "35mm, f/2.8, wider environmental portrait showing full scene",
        "24mm selfie angle, f/2.0, arm-length distance",
    ],
    "UGC_PERSON_HOLDING": [
        "50mm, f/2.0, focus on sunglasses in hand, face soft behind",
        "50mm, f/1.8, close-up on hand and product",
    ],
    "UGC_HEADBAND": [
        "50mm, f/2.0, natural portrait framing, head and shoulders",
        "35mm, f/2.8, wider shot showing outfit and sunglasses on head",
    ],
    "BRAND_MODEL": [
        "50mm, f/1.8, premium shallow DOF, magazine editorial framing, chest up",
        "85mm, f/1.4, tight beauty shot, face fills frame, extreme bokeh",
        "35mm, f/2.0, environmental editorial, full upper body with scene context",
    ],
}

ASPECT_RATIOS = {
    "UGC_PRODUCT": "1:1",
    "UGC_PERSON_WEARING": "1:1",
    "UGC_PERSON_HOLDING": "1:1",
    "UGC_HEADBAND": "1:1",
    "BRAND_MODEL": "4:5",
}

BLUR_PRESETS = {
    "UGC_PRODUCT": 0.4,
    "UGC_PERSON_WEARING": 0.4,
    "UGC_PERSON_HOLDING": 0.5,
    "UGC_HEADBAND": 0.5,
    "BRAND_MODEL": 0.4,
}


def load_history() -> set:
    """Load used layout combos from layout_history.json."""
    path = PROJECT_DIR / "contents" / "layout_history.json"
    if not path.exists():
        return set()
    data = json.loads(path.read_text(encoding="utf-8"))
    combos = set()
    for entry in data:
        key = f"{entry.get('layout', '')}|{entry.get('product', '')}|{entry.get('scenario', '')}"
        combos.add(key)
    return combos


def build_subject(gender: str, category: str) -> dict:
    """Build a randomized subject description."""
    if gender == "male":
        age = random.choice(MALE_AGES)
        hair = random.choice(MALE_HAIR)
        outfit = random.choice(MALE_OUTFITS)
        ethnicity = "Filipino"
    else:
        age = random.choice(FEMALE_AGES)
        hair = random.choice(FEMALE_HAIR)
        outfit = random.choice(FEMALE_OUTFITS)
        ethnicity = "Filipina"

    expression = random.choice(EXPRESSIONS)

    if category == "UGC_PERSON_WEARING" or category == "BRAND_MODEL":
        pose = random.choice(POSES_WEARING)
    elif category == "UGC_PERSON_HOLDING":
        pose = random.choice(POSES_HOLDING)
    elif category == "UGC_HEADBAND":
        pose = random.choice(POSES_HEADBAND)
    else:
        pose = ""

    return {
        "description": f"{ethnicity} {'man' if gender == 'male' else 'woman'} in {'his' if gender == 'male' else 'her'} {age}, {expression}, {hair}, wearing {outfit}",
        "pose": pose,
        "gender": gender,
    }


def randomize_one(product_key: str, specs: dict, metadata: dict,
                   history: set, batch_combos: set, force_category: str = None) -> dict:
    """Generate one fully randomized v3 assignment."""

    # Product
    spec = specs[product_key]
    product_name = spec["identity"]

    # Angle -- always -1.png
    angle_key = f"{product_key}-1.png"
    angle_meta = metadata.get(product_key, {}).get(angle_key, {})
    compatible = angle_meta.get("compatible_directions", ["8 o'clock", "4 o'clock"])

    # Category
    if force_category:
        category = force_category
    else:
        category = random.choices(CATEGORIES, weights=CATEGORY_WEIGHTS, k=1)[0]

    # Direction
    direction = random.choice(compatible)

    # Location
    location = random.choice(LOCATIONS)

    # Lighting
    lighting = random.choice(LIGHTING)

    # Scene objects + subject/surface
    if category in PERSON_CATEGORIES:
        gender = random.choice(GENDERS)
        subject = build_subject(gender, category)
        objects_in_scene = random.choice(NEARBY_OBJECTS_PERSON)
        surface = None
    else:
        subject = None
        surface = random.choice(SURFACES)
        objects_in_scene = random.choice(NEARBY_OBJECTS_PRODUCT)

    # Camera
    camera = random.choice(CAMERA_PRESETS[category])

    # Aspect ratio + blur
    aspect_ratio = ASPECT_RATIOS[category]
    blur = BLUR_PRESETS[category]

    # Build combo key for dedup
    combo_key = f"{category}|{product_key}|{location[:30]}"
    for _ in range(20):
        if combo_key not in batch_combos and combo_key not in history:
            break
        location = random.choice(LOCATIONS)
        combo_key = f"{category}|{product_key}|{location[:30]}"
    batch_combos.add(combo_key)

    assignment = {
        "product_key": product_key,
        "product_identity": product_name,
        "required_details": spec["required_details"],
        "proportions": spec["proportions"],
        "finish": spec["finish"],
        "category": category,
        "angle_file": f"contents/assets/product-refs/{product_key}/{product_key}-1.png",
        "direction": direction,
        "scene": {
            "location": location,
            "lighting": lighting,
            "camera": camera,
            "objects": objects_in_scene,
            "aspect_ratio": aspect_ratio,
            "blur": blur,
        },
    }

    if subject:
        assignment["scene"]["subject"] = subject["description"]
        assignment["scene"]["pose"] = subject["pose"]
        assignment["scene"]["gender"] = subject["gender"]
    else:
        assignment["scene"]["surface"] = surface

    return assignment


def main():
    import argparse
    parser = argparse.ArgumentParser(description="v3 Pipeline Scene Randomizer")
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--product", default="outback-blue")
    parser.add_argument("--category", default=None, help="Force a specific category")
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    specs = load_json("contents/assets/product-specs.json")
    metadata = load_json("contents/assets/prodref-metadata.json")
    history = load_history()

    if args.product not in specs:
        print(f"ERROR: product '{args.product}' not in product-specs.json", file=sys.stderr)
        print(f"Available: {', '.join(specs.keys())}", file=sys.stderr)
        sys.exit(1)

    batch_combos = set()
    assignments = []

    for i in range(args.count):
        a = randomize_one(args.product, specs, metadata, history, batch_combos,
                          force_category=args.category)
        a["batch_index"] = i + 1
        assignments.append(a)

    # Summary to stderr
    for a in assignments:
        cat = a["category"]
        loc = a["scene"]["location"][:50]
        light = a["scene"]["lighting"][:40]
        direction = a["direction"]
        print(f"  [{a['batch_index']}] {cat} | {direction} | {loc}... | {light}...", file=sys.stderr)

    # JSON to stdout
    if len(assignments) == 1:
        print(json.dumps(assignments[0], indent=2))
    else:
        print(json.dumps(assignments, indent=2))


if __name__ == "__main__":
    main()
