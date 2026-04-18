"""
v3 Pipeline Scene Randomizer -- numbered banks, sidecar-driven fidelity.

Picks random scene for a product + category, loading frame_direction and
visible_details from the per-kraft sidecar. All bank items have numeric IDs
so layout_history dedup is exact-match, not string-slice.

Usage:
    python tools/image_gen/v3_randomizer.py                    # 1 assignment
    python tools/image_gen/v3_randomizer.py --count 3
    python tools/image_gen/v3_randomizer.py --product outback-blue
    python tools/image_gen/v3_randomizer.py --category UGC_PERSON_WEARING

Output: JSON to stdout. Summary to stderr.
"""

import argparse
import json
import random
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent.parent

# --- Categories ---

CATEGORIES = [
    "UGC_PRODUCT",
    "UGC_PERSON_WEARING",
    "UGC_PERSON_HOLDING",
    "UGC_SELFIE",
    "UGC_FLATLAY",
    "UGC_UNBOXING",
    "UGC_GIFTED",
    "UGC_WHAT_YOU_GET",
    "UGC_DELIVERY",
    "UGC_OUTFIT_MATCH",
]

CATEGORY_WEIGHTS = [12, 18, 10, 10, 10, 10, 8, 8, 8, 6]

PERSON_CATEGORIES = {
    "UGC_PERSON_WEARING", "UGC_PERSON_HOLDING", "UGC_SELFIE",
    "UGC_UNBOXING", "UGC_OUTFIT_MATCH",
}
PRODUCT_CATEGORIES = {
    "UGC_PRODUCT", "UGC_FLATLAY",
    "UGC_GIFTED", "UGC_WHAT_YOU_GET", "UGC_DELIVERY",
}

# Prodref file per category.
# "hero" points to contents/assets/hero/hero-{product}.png (full packaging shot).
# Anything else (01-hero, 06-front, 07-flat) lives in contents/assets/prodref-kraft/{product}/
CATEGORY_PRODREF = {
    "UGC_PRODUCT": "01-hero",
    "UGC_PERSON_WEARING": "01-hero",
    "UGC_PERSON_HOLDING": "01-hero",
    "UGC_SELFIE": "01-hero",
    "UGC_FLATLAY": "06-front",
    "UGC_UNBOXING": "hero",
    "UGC_GIFTED": "hero",
    "UGC_WHAT_YOU_GET": "hero",
    "UGC_DELIVERY": "hero",
    "UGC_OUTFIT_MATCH": "01-hero",
}

# --- Numbered banks ---

LOCATIONS_PERSON = [
    (1,  "tropical white-sand beach with turquoise water and scattered palm trees"),
    (2,  "rocky coastline with waves crashing against dark volcanic rocks"),
    (3,  "resort infinity pool deck overlooking the ocean"),
    (4,  "fishing boat on calm morning water with distant islands"),
    (5,  "lakeside wooden dock with misty green mountains behind"),
    (6,  "Manila BGC rooftop bar with afternoon city skyline"),
    (8,  "urban skatepark with concrete ramps and graffiti walls"),
    (9,  "modern coffee shop patio with exposed brick and string plants"),
    (10, "outdoor basketball court at a neighborhood park mid-afternoon"),
    (11, "university campus lawn with old stone buildings behind"),
    (12, "motorcycle parked on a coastal highway overlook"),
    (13, "Banaue rice terrace overlook at mid-morning"),
    (14, "mountain trail viewpoint above rolling green hills"),
    (17, "coconut palm grove with hammock strung between trees"),
    (18, "outdoor gym with pull-up rig and kettlebells on wooden deck"),
    (19, "co-working space with big windows and natural daylight flooding in"),
    (20, "vintage barbershop with leather chair near a bright window"),
    (21, "hotel lobby with marble floors and tropical plants, sunlit atrium"),
    (22, "food truck park with wooden picnic tables under string lights in daytime"),
    (23, "beach boardwalk with ocean horizon behind the subject"),
    (24, "outdoor patio under a pergola wrapped in flowering vines"),
    (25, "surf shack dock with surfboards leaning against wooden posts"),
    (27, "cliff edge viewpoint with open sky and distant sea"),
    (28, "tropical garden path lined with bird-of-paradise plants"),
    (30, "bamboo grove with light filtering through tall stalks"),
    (31, "countryside dirt road with carabao grazing in the background"),
    (32, "mangrove boardwalk at low tide"),
    (34, "open schoolyard basketball half-court with chainlink fence"),
    (35, "pier fishing spot with rods leaning against a wooden railing and a tackle box nearby"),
    (36, "coastal cycling road with open ocean view and palm trees along the shoulder"),
    (37, "beachside running track along the ocean horizon at mid-morning"),
    (38, "beach with a surfboard planted in the sand and waves rolling behind"),
    (39, "tide-line shoreline with a skimboard partially in the wet sand"),
    (40, "longboarding spot on a palm-lined boulevard with smooth pavement"),
    (41, "outdoor bouldering crag with a chalk bag and climbing shoes on a nearby ledge"),
    (42, "resort pool deck with turquoise water and lounge chairs behind"),
    (43, "rooftop parking garage overlooking the city mid-afternoon"),
    (44, "classic car show with polished vintage cars lined up under clear skies"),
    (45, "motorcycle show with custom bikes on display under an open-sky pavilion"),
    (46, "hot air balloon festival field with multiple balloons inflating in bright morning light"),
]

LOCATIONS_PRODUCT = [
    (1,  "weathered wooden table with visible grain and knots"),
    (2,  "smooth polished concrete ledge on a rooftop"),
    (3,  "white Carrara marble cafe table with subtle veining"),
    (4,  "woven rattan tray with natural texture"),
    (5,  "matte black leather ottoman surface"),
    (6,  "sun-bleached driftwood log on sand"),
    (7,  "flat volcanic rock beside tide pools"),
    (8,  "wooden surfboard deck laying on beach sand"),
    (9,  "stacked vintage hardcover books on a desk"),
    (10, "clean white linen cloth on a cafe table"),
    (11, "rustic terracotta clay tile"),
    (12, "bamboo floor mat with subtle weave"),
    (13, "chrome motorcycle tank with reflections"),
    (14, "gym bench with black rubber padding"),
    (15, "wooden park bench slat with painted edge"),
    (16, "corner of a vinyl record with the sleeve beside it"),
    (17, "denim jacket folded on a wooden bench"),
    (18, "marble bathroom counter next to a folded towel"),
    (19, "wooden cafe tray with a ceramic coffee cup"),
    (20, "skateboard deck with grip tape next to spare wheels"),
    (21, "airplane window tray table with a boarding pass"),
    (22, "leather wallet and brass keys on a wooden dresser"),
    (23, "open paperback book face-down with reading glasses case"),
    (24, "hotel bedside table with phone and watch"),
    (25, "picnic blanket spread on grass with wicker basket corner visible"),
    (26, "kraft paper wrapping with twine"),
    (27, "pebble-lined garden planter edge"),
    (28, "slate stone coaster on a dark dining table"),
]

LIGHTING = [
    (1,  "bright warm afternoon sun with clean directional shadows"),
    (2,  "golden hour sunlight from the left, warm orange tones"),
    (3,  "sunrise light from behind, soft pink and gold rim glow"),
    (4,  "bright midday tropical sun from directly above, hard shadows"),
    (5,  "overcast sky with soft even diffused light, no harsh shadows"),
    (6,  "morning light through scattered clouds, gentle and directional"),
    (7,  "harsh afternoon sun with deep contrasty shadows"),
    (8,  "dappled shade under tropical trees, shifting light patches"),
    (9,  "dramatic storm clouds with a single break of golden light"),
    (10, "foggy morning with soft milky light and low visibility"),
    (11, "late afternoon side-light raking across at a low angle"),
    (12, "backlit silhouette lighting with strong rim glow and bright ambient fill"),
    (13, "warm window light indoors, late morning quality"),
    (14, "bright open shade with soft cool fill"),
    (15, "sunny day with bright white clouds creating gentle reflected light"),
]

# Camera presets per category -- range from close to wide
CAMERAS = {
    "UGC_PRODUCT": [
        (1, "50mm, f/2.8, slightly elevated angle looking down at product, sharp focus"),
        (2, "50mm, f/2.8, eye-level angle straight on, sharp focus on product"),
        (3, "35mm, f/2.0, low angle looking up at product with sky/ceiling behind"),
        (4, "85mm, f/2.8, tight crop with shallow DOF around product"),
    ],
    "UGC_PERSON_WEARING": [
        (1, "50mm, f/2.0, natural handheld framing, chest up"),
        (2, "85mm, f/1.8, tight headshot framing, sharp focus on sunglasses"),
        (3, "135mm, f/2.0, close portrait shot, face fills frame, sharp focus on sunglasses and branding"),
    ],
    "UGC_PERSON_HOLDING": [
        (1, "50mm, f/2.8, macro-style product-forward shot with sunglasses filling most of the frame held close to the lens, face softly blurred behind"),
        (2, "35mm, f/2.0, wide product-forward framing with sunglasses held close to the lens dominating the composition, subject partial behind"),
        (3, "85mm, f/2.0, tight product hero shot with sunglasses as the clear focal point pushed toward camera, shallow DOF on the hand and subject"),
    ],
    "UGC_SELFIE": [
        (1, "24mm wide angle, f/2.0, arm-length selfie distance, slight wide-angle distortion, sharp focus on face"),
        (2, "28mm, f/2.0, arm-length selfie, less distortion, natural framing"),
    ],
    "UGC_FLATLAY": [
        (1, "50mm, f/4, shot directly from above looking straight down, everything in focus"),
        (2, "35mm, f/5.6, slightly wider overhead shot with more surrounding surface visible"),
    ],
    "UGC_UNBOXING": [
        (1, "24mm wide angle, f/2.0, POV looking down at hands and package"),
        (2, "50mm, f/2.8, overhead shot of package and accessories laid out"),
        (3, "35mm, f/2.8, chest-level POV with hands opening the box"),
    ],
    "UGC_GIFTED": [
        (1, "35mm, f/2.8, slightly elevated angle with gift prominent, soft depth of field"),
        (2, "50mm, f/4, overhead flat-lay of gift arrangement"),
        (3, "50mm, f/2.8, natural handheld framing of gift being handed over"),
    ],
    "UGC_WHAT_YOU_GET": [
        (1, "50mm, f/4, shot directly from above looking straight down, everything in focus"),
        (2, "35mm, f/5.6, slightly wider overhead showing full contents arrangement"),
    ],
    "UGC_DELIVERY": [
        (1, "35mm, f/2.8, natural handheld eye-level shot of package on surface"),
        (2, "50mm, f/2.8, slightly elevated angle showing package in context"),
        (3, "24mm wide angle, f/2.0, POV looking down at package just received"),
    ],
    "UGC_OUTFIT_MATCH": [
        (1, "35mm, f/2.0, full body shot from waist up, outfit and sunglasses prominent"),
        (2, "50mm, f/2.0, three-quarter body shot, sharp focus on face and sunglasses"),
        (3, "85mm, f/2.0, chest-up portrait with detailed outfit texture"),
    ],
}

ASPECT_RATIOS = {
    "UGC_PRODUCT": [(1, "1:1"), (2, "4:5")],
    "UGC_PERSON_WEARING": [(1, "9:14")],
    "UGC_PERSON_HOLDING": [(1, "9:14")],
    "UGC_SELFIE": [(1, "9:14")],
    "UGC_FLATLAY": [(1, "1:1"), (2, "4:5")],
    "UGC_UNBOXING": [(1, "9:14"), (2, "1:1")],
    "UGC_GIFTED": [(1, "1:1"), (2, "4:5")],
    "UGC_WHAT_YOU_GET": [(1, "1:1"), (2, "4:5")],
    "UGC_DELIVERY": [(1, "1:1"), (2, "4:5"), (3, "9:14")],
    "UGC_OUTFIT_MATCH": [(1, "9:14")],
}

BLUR = {
    "UGC_PRODUCT": 0.4,
    "UGC_PERSON_WEARING": 0.4,
    "UGC_PERSON_HOLDING": 0.5,
    "UGC_SELFIE": 0.3,
    "UGC_FLATLAY": 0.2,
    "UGC_UNBOXING": 0.3,
    "UGC_GIFTED": 0.3,
    "UGC_WHAT_YOU_GET": 0.2,
    "UGC_DELIVERY": 0.4,
    "UGC_OUTFIT_MATCH": 0.4,
}

# --- Person banks ---

GENDERS = ["male", "female"]
AGES = ["early 20s", "mid 20s", "late 20s", "early 30s"]

MALE_HAIR = [
    "short cropped fade", "textured messy top", "buzz cut",
    "slicked back", "curly medium length", "undercut with longer top",
]
FEMALE_HAIR = [
    "long straight dark hair", "wavy beach hair past shoulders",
    "short bob with side part", "ponytail pulled back",
    "braids with loose strands", "messy bun", "shoulder-length waves",
]

MALE_OUTFITS = [
    "plain white crew-neck t-shirt", "black tank top",
    "unbuttoned cream linen shirt over bare chest", "navy blue polo shirt",
    "grey hoodie with sleeves pushed up", "denim jacket over white tee",
    "basketball jersey", "plain black t-shirt",
    "flannel shirt rolled to elbows", "fitted rash guard", "olive bomber jacket",
]

FEMALE_OUTFITS = [
    "black bikini top", "white cropped tank top", "denim jacket over sundress",
    "off-shoulder floral blouse", "fitted activewear sports bra and leggings",
    "oversized vintage band tee", "linen wrap top in earth tone",
    "plain white t-shirt knotted at the waist", "colorful swimsuit coverup",
    "casual striped button-up tied at front", "beige trench coat over white tee",
]

EXPRESSIONS = [
    "relaxed confident smile", "laughing mid-conversation",
    "focused and looking into the distance", "candid mid-action, not looking at camera",
    "serene and peaceful with eyes slightly down", "grinning wide, carefree energy",
    "cool and composed, slight smirk",
]

POSES_WEARING = [
    "looking off-camera to the side", "looking directly at camera",
    "chin slightly raised, confident", "leaning forward with elbows on knees",
    "arms crossed, relaxed stance",
    "one {hand} hand touching the temple arm of the sunglasses",
    "mid-stride walking",
]

POSES_HOLDING = [
    "holding sunglasses extended close to the camera lens with {hand} hand, product dominating the frame, face softly blurred behind",
    "holding sunglasses up close to the camera with both hands, product filling most of the frame, face partially visible behind",
    "holding sunglasses pushed forward toward the lens with {hand} hand, product as the clear focal point, subject partial behind product",
]

POSES_SELFIE = [
    "arm extended toward camera holding phone in {hand} hand, free hand adjusting sunglasses",
    "arm extended selfie with phone in {hand} hand, giving a small peace sign with the other",
    "selfie with phone in {hand} hand, sunglasses on, looking slightly up at lens",
]

POSES_UNBOXING = [
    "hands opening Dubery box with {hand} hand pulling back the lid",
    "both hands unfolding the drawstring pouch to reveal sunglasses inside",
    "laying out accessories in a row with {hand} hand",
]

POSES_OUTFIT = [
    "standing full body pose, sunglasses worn on face, looking off to the side with casual confidence",
    "leaning against a wall, sunglasses hanging from shirt collar, relaxed stance",
    "mid-stride walking pose, sunglasses on face, outfit visible",
    "sitting on a bench or low wall, sunglasses in {hand} hand, outfit styled",
    "holding sunglasses in {hand} hand as part of a fit check, other hand on hip",
    "adjusting sunglasses with {hand} hand while posing for an OOTD shot",
]

# --- Scene banks for hero-based categories ---

LOCATIONS_INDOOR = [
    (101, "wooden desk with scattered work items and a notebook"),
    (102, "marble kitchen counter near the coffee maker"),
    (103, "bed with crumpled white sheets and a pillow"),
    (104, "sofa with throw pillows and a folded blanket"),
    (105, "cafe table with a latte and a pastry"),
    (106, "dining table with morning light from a window"),
    (107, "entryway console with house keys and a small candle"),
    (108, "home office desk with laptop open to Shopee order confirmation"),
    (109, "hardwood floor with a fluffy area rug"),
    (110, "bedside table with a phone and a paperback book"),
    (111, "clean studio apartment floor with late afternoon light"),
    (112, "coworking space desk with plants nearby"),
]

LOCATIONS_GIFTED = [
    (201, "wrapped gift box with red ribbon on a kraft paper surface"),
    (202, "present on a wooden table beside a handwritten greeting card"),
    (203, "unwrapped gift box with scattered wrapping paper around"),
    (204, "gift on a neutral linen surface with dried flowers"),
    (205, "package beside a small potted plant on a dining table"),
    (206, "gift on a marble counter with a coffee cup and notebook"),
    (207, "present on a cream-colored throw blanket"),
    (208, "gift box with a pastel bow on a soft pastel background"),
    (209, "simple brown-paper wrapped gift with twine on a wooden desk"),
    (210, "gift on a sunlit window ledge with morning light"),
    (211, "gift box with balloons and confetti on a dining table"),
    (212, "anniversary-style gift setup with roses and a handwritten note"),
]

LOCATIONS_DELIVERY = [
    (301, "brown Shopee cardboard box on a tiled apartment doorstep"),
    (302, "package on a wooden entryway console next to house keys"),
    (303, "unopened delivery box on a kitchen counter with morning coffee"),
    (304, "package half-opened on a sofa with cushions"),
    (305, "cardboard box on a white marble dining table"),
    (306, "delivery box on a desk with laptop open to a confirmation email"),
    (307, "package on a bed with crumpled blanket and phone nearby"),
    (308, "Lazada cardboard box on a floor mat by the front door"),
    (309, "unopened delivery box on a cafe table next to iced coffee"),
    (310, "package on a condo balcony with plants and city view behind"),
    (311, "Shopee box on a stool next to a pair of worn sneakers"),
    (312, "delivery box on a rattan chair with natural window light"),
]

# --- Helpers ---

def load_json(path: str) -> dict:
    return json.loads((PROJECT_DIR / path).read_text(encoding="utf-8"))


def load_sidecar(product_key: str, prodref_name: str) -> dict:
    if prodref_name == "hero":
        path = PROJECT_DIR / f"contents/assets/hero/hero-{product_key}.json"
    else:
        path = PROJECT_DIR / f"contents/assets/prodref-kraft/{product_key}/{prodref_name}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Sidecar missing: {path} "
            f"(product '{product_key}' needs {prodref_name}.png + .json)"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def prodref_paths(product_key: str, prodref_name: str) -> tuple:
    """Return (png_path, json_path) for a given product + prodref name."""
    if prodref_name == "hero":
        return (
            f"contents/assets/hero/hero-{product_key}.png",
            f"contents/assets/hero/hero-{product_key}.json",
        )
    return (
        f"contents/assets/prodref-kraft/{product_key}/{prodref_name}.png",
        f"contents/assets/prodref-kraft/{product_key}/{prodref_name}.json",
    )


def load_history() -> set:
    """Load used combo keys from layout_history.json. Supports new numeric format."""
    path = PROJECT_DIR / "contents" / "layout_history.json"
    if not path.exists():
        return set()
    data = json.loads(path.read_text(encoding="utf-8"))
    combos = set()
    for entry in data:
        if "location_id" in entry and "category" in entry and "product_key" in entry:
            combos.add((entry["category"], entry["product_key"], entry["location_id"]))
    return combos


def pick(bank: list) -> tuple:
    """Pick one (id, value) from a bank."""
    return random.choice(bank)


def build_subject(gender: str, category: str) -> dict:
    if gender == "male":
        hair = random.choice(MALE_HAIR)
        outfit = random.choice(MALE_OUTFITS)
        ethnicity = "Filipino"
        pronoun = "man"
        possessive = "his"
    else:
        hair = random.choice(FEMALE_HAIR)
        outfit = random.choice(FEMALE_OUTFITS)
        ethnicity = "Filipina"
        pronoun = "woman"
        possessive = "her"

    age = random.choice(AGES)
    expression = random.choice(EXPRESSIONS)
    hand = random.choice(["LEFT", "RIGHT"])

    if category == "UGC_PERSON_WEARING":
        pose_template = random.choice(POSES_WEARING)
    elif category == "UGC_PERSON_HOLDING":
        pose_template = random.choice(POSES_HOLDING)
    elif category == "UGC_SELFIE":
        pose_template = random.choice(POSES_SELFIE)
    elif category == "UGC_UNBOXING":
        pose_template = random.choice(POSES_UNBOXING)
    elif category == "UGC_OUTFIT_MATCH":
        pose_template = random.choice(POSES_OUTFIT)
    else:
        pose_template = ""

    pose = pose_template.replace("{hand}", hand) if pose_template else ""

    return {
        "description": f"{ethnicity} {pronoun} in {possessive} {age}, {expression}, {hair}, wearing {outfit}",
        "pose": pose,
        "gender": gender,
        "hand": hand,
    }


def filter_required_details(details: list, visible_indices: list) -> list:
    return [details[i] for i in visible_indices if i < len(details)]


def randomize_one(product_key: str, specs: dict, history: set,
                   batch_combos: set, batch_categories: set,
                   batch_products: set, force_category: str = None,
                   force_type: str = None) -> dict:
    # product_key=None means pick randomly per image, avoiding batch repeats until exhausted
    if product_key is None:
        available = [p for p in specs.keys() if p not in batch_products]
        if not available:
            available = list(specs.keys())
        product_key = random.choice(available)
        batch_products.add(product_key)
    elif product_key not in specs:
        raise ValueError(f"Product '{product_key}' not in product-specs.json")

    spec = specs[product_key]

    # Category -- avoid repeats within batch until catalog is exhausted
    if force_category:
        category = force_category
    else:
        # Apply type filter (person/product) if specified
        if force_type == "person":
            pool = [c for c in CATEGORIES if c in PERSON_CATEGORIES]
        elif force_type == "product":
            pool = [c for c in CATEGORIES if c in PRODUCT_CATEGORIES]
        else:
            pool = CATEGORIES
        available = [c for c in pool if c not in batch_categories]
        if not available:
            available = list(pool)
        available_weights = [CATEGORY_WEIGHTS[CATEGORIES.index(c)] for c in available]
        category = random.choices(available, weights=available_weights, k=1)[0]
    batch_categories.add(category)

    # Prodref + sidecar
    prodref_name = CATEGORY_PRODREF[category]
    prodref_png, prodref_json = prodref_paths(product_key, prodref_name)
    sidecar = load_sidecar(product_key, prodref_name)
    # Hero sidecars don't have frame_direction (package layout, not product angle)
    frame_direction = sidecar.get("frame_direction")
    visible_details = sidecar.get("visible_details", list(range(len(spec["required_details"]))))

    # Location (with dedup retry) -- bank depends on category
    if category == "UGC_GIFTED":
        location_bank = LOCATIONS_GIFTED
    elif category == "UGC_DELIVERY":
        location_bank = LOCATIONS_DELIVERY
    elif category == "UGC_UNBOXING":
        location_bank = LOCATIONS_INDOOR
    elif category in {"UGC_PRODUCT", "UGC_FLATLAY", "UGC_WHAT_YOU_GET"}:
        location_bank = LOCATIONS_PRODUCT
    else:
        location_bank = LOCATIONS_PERSON
    for _ in range(25):
        loc_id, location = pick(location_bank)
        combo_key = (category, product_key, loc_id)
        if combo_key not in batch_combos and combo_key not in history:
            break
    batch_combos.add(combo_key)

    # Lighting
    light_id, lighting = pick(LIGHTING)

    # Camera
    cam_id, camera = pick(CAMERAS[category])

    # Aspect ratio
    ar_id, aspect_ratio = pick(ASPECT_RATIOS[category])

    # Subject or surface
    scene = {
        "location_id": loc_id,
        "location": location,
        "lighting_id": light_id,
        "lighting": lighting,
        "camera_id": cam_id,
        "camera": camera,
        "aspect_ratio_id": ar_id,
        "aspect_ratio": aspect_ratio,
        "blur": BLUR[category],
    }

    if category in PERSON_CATEGORIES:
        gender = random.choice(GENDERS)
        subject = build_subject(gender, category)
        scene["subject"] = subject["description"]
        scene["pose"] = subject["pose"]
        scene["gender"] = subject["gender"]
        scene["hand"] = subject["hand"]

    # FLATLAY and UGC_PRODUCT both need a surface too (location describes the setting)
    if category in PRODUCT_CATEGORIES:
        # For product categories the "location" IS the surface -- no separate field needed
        pass

    return {
        "product_key": product_key,
        "product_identity": spec["identity"],
        "required_details": filter_required_details(spec["required_details"], visible_details),
        "proportions": spec["proportions"],
        "finish": spec["finish"],
        "category": category,
        "prodref": prodref_png,
        "prodref_sidecar": prodref_json,
        "frame_direction": frame_direction,
        "visible_details": visible_details,
        "scene": scene,
    }


def main():
    parser = argparse.ArgumentParser(description="v3 Pipeline Scene Randomizer")
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--product", default=None,
                        help="Lock batch to one product. Omit to randomize per image.")
    parser.add_argument("--category", default=None, help="Force a specific category")
    parser.add_argument("--type", default=None, choices=["person", "product"],
                        help="Filter to person or product categories")
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    if args.category and args.category not in CATEGORIES:
        print(f"ERROR: category '{args.category}' not in {CATEGORIES}", file=sys.stderr)
        sys.exit(1)

    specs = load_json("contents/assets/product-specs.json")
    history = load_history()

    batch_combos = set()
    batch_categories = set()
    batch_products = set()
    assignments = []

    for i in range(args.count):
        try:
            a = randomize_one(args.product, specs, history, batch_combos,
                              batch_categories, batch_products,
                              force_category=args.category,
                              force_type=args.type)
        except (FileNotFoundError, ValueError) as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(1)
        a["batch_index"] = i + 1
        assignments.append(a)

    # Summary to stderr
    for a in assignments:
        s = a["scene"]
        print(
            f"  [{a['batch_index']}] {a['category']} | "
            f"loc#{s['location_id']} | light#{s['lighting_id']} | "
            f"cam#{s['camera_id']} | {s['aspect_ratio']}",
            file=sys.stderr,
        )

    # JSON to stdout
    if len(assignments) == 1:
        print(json.dumps(assignments[0], indent=2))
    else:
        print(json.dumps(assignments, indent=2))


if __name__ == "__main__":
    main()
