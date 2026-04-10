"""
DuberyMNL product catalog, pricing, and FAQ.

Pure data module -- no API calls, no side effects.
Returns strings for injection into the chatbot system prompt.

Last updated: 2026-04-10
"""

# --- Product Catalog ---

CATALOG = {
    "Bandits": {
        "code": "D518",
        "variants": ["Glossy Black", "Matte Black", "Blue", "Green", "Tortoise"],
        "style": (
            "Square frame with a slim, clean profile. Chrome metal DUBERY badge on the temple hinge. "
            "Refined and versatile -- clean lines, flat front, slightly rounded edges."
        ),
        "variant_notes": {
            "Glossy Black": "Glossy black frame, dark lenses",
            "Matte Black": "Matte black frame, orange/gold mirror lenses. Has a colorful pattern on the INSIDE of the temples only (not visible from the front).",
            "Blue": "Black frame with blue accents, blue mirror lenses (two-tone)",
            "Green": "Black frame with green/yellow accents and tropical pattern on temples, blue-green mirror lenses (two-tone)",
            "Tortoise": "Dark tortoiseshell pattern (black + red/brown), amber/brown lenses",
        },
        "best_for": "Everyday wear, driving, versatile style",
    },
    "Outback": {
        "code": "D918",
        "variants": ["Black", "Blue", "Red", "Green"],
        "style": (
            "Blockier, angular square frame with a flat top edge. Wider temples. "
            "Colored DUBERY badge that matches the lens color. Bold and rugged."
        ),
        "variant_notes": {
            "Black": "All matte black, dark lenses",
            "Blue": "Matte black frame, blue mirror lenses, black/white pattern on inner temples, white DUBERY badge",
            "Green": "Matte black frame, green-blue mirror lenses, green DUBERY badge",
            "Red": "Matte black frame, gold/amber mirror lenses, red DUBERY badge, purple pattern on inner temples",
        },
        "best_for": "Streetwear, outdoor activities, bold style",
    },
    "Rasta": {
        "code": "D008",
        "variants": ["Brown", "Red"],
        "style": (
            "Oversized aviator-style square frame. Noticeably bigger and wider than Bandits and Outback. "
            "Gold/bronze metallic accents on the temples with a red-green-yellow rasta stripe. "
            "Circular Dubery logo medallion on the temple. Statement piece."
        ),
        "variant_notes": {
            "Brown": "Brown/amber lenses, gold temple accents",
            "Red": "Red/orange mirror lenses, gold temple accents",
        },
        "best_for": "Standing out, lifestyle, fashion-forward",
    },
}

# --- Technical Specs (shared) ---

SPECS = {
    "polarization": "99.9% polarized efficiency, UV400",
    "coatings": "Scratch resistant, shatter resistant, hydrophobic, anti-reflective inner coating",
    "rating": "ANSI Z80.3",
    "weight": "~31.6g (lightweight)",
    "dimensions": "Frame width 146mm, lens width 58mm, lens height 47mm, bridge 16mm, temple 131mm",
    "bandits_outback_frame": "TR90 flexible frame, polycarbonate lenses",
    "rasta_frame": "Polycarbonate frame, TAC (tri-acetate cellulose) lenses",
    "fit": "One size fits most adults",
}

# --- Pricing ---

PRICING = {
    "single": 699,
    "bundle_2": 1200,
    "currency": "PHP",
    "metro_delivery_single": 99,
    "bundle_note": "Any mix of models/colors",
}

# --- Discount Codes ---

DISCOUNT_CODES = {
    "DUBERY50": {
        "description": "P50 off first order",
        "discount_amount": 50,
        "discount_type": "fixed",
        "applies_to": "first order",
        "active": True,
        "rule": "Only mention when the customer brings it up. Do NOT offer proactively.",
    },
}

# --- FAQ ---

FAQ = [
    {
        "topic": "Payment methods",
        "answer": "COD (Metro Manila only), GCash, or bank transfer/InstaPay. For provincial orders, prepaid only.",
    },
    {
        "topic": "Delivery - Metro Manila",
        "answer": "Same-day, next-day, or urgent available. Delivery fee ~P99 for single pair. FREE delivery on 2-pair bundle. COD available.",
    },
    {
        "topic": "Delivery - Provincial",
        "answer": "No COD. Prepaid only via GCash or bank transfer. Shipping cost varies by location.",
    },
    {
        "topic": "Returns",
        "answer": "All sunglasses are quality-checked before delivery. Defective items replaced free -- message within 24 hours with photos.",
    },
    {
        "topic": "Polarized",
        "answer": "Yes, all Dubery lenses are polarized with UV400 protection. Explain it simply: 'polarized' means the lens blocks harsh reflections and glare (from the sun, road, water, car windows), so you see clearer and your eyes don't get tired as fast. UV400 means it also blocks harmful sun rays. Don't use technical terms like 'ANSI Z80.3' or '99.9% efficiency' unless the customer is clearly into specs.",
    },
    {
        "topic": "What's included",
        "answer": "Branded Dubery box, microfiber cleaning cloth, and drawstring soft pouch. Optional zippered hard case available for +P100.",
    },
    {
        "topic": "How to order",
        "answer": "Send: (1) full name, (2) complete address, (3) landmarks nearby, (4) phone number, (5) model + color, (6) delivery preference (same-day/next-day/urgent), (7) preferred time.",
    },
    {
        "topic": "Urgent orders",
        "answer": "Yes, urgent delivery available in Metro Manila. Ask for the customer's number and tell them we'll call ASAP.",
    },
    {
        "topic": "Sizing",
        "answer": "One size fits most adults. Frame width ~146mm, lightweight at ~31.6g.",
    },
    {
        "topic": "Frame and lens material",
        "answer": "Bandits and Outback: TR90 flexible frame with polycarbonate lenses. Rasta: PC frame with TAC lenses.",
    },
]

# --- Brand info ---

BRAND = {
    "name": "DuberyMNL",
    "tagline": "Premium polarized shades at everyday prices",
    "page_url": "https://www.facebook.com/DuberyMNL",
    "website_url": "https://duberymnl.com",
}

# --- Links (for sharing with customers) ---

LINKS = {
    "website": "https://duberymnl.com",
    "facebook_page": "https://www.facebook.com/DuberyMNL",
    "messenger": "https://m.me/DuberyMNL",
}

# --- Image Bank ---
# STRICT RULE: 2 images per model max (1 hero + 1 secondary).
# Hero shots served from Vercel (duberymnl.com). Secondary shots served from
# Google Drive via lh3.googleusercontent.com CDN.

SITE = "https://duberymnl.com"

def _drive(file_id: str) -> str:
    """Construct a CDN URL for a Google Drive file."""
    return f"https://lh3.googleusercontent.com/d/{file_id}"

# Hero shots (product card photos) -- one per variant, 11 total.
PRODUCT_IMAGES = {
    "bandits-glossy-black": f"{SITE}/assets/cards/bandits-glossy-black-card-shot.jpg",
    "bandits-matte-black": f"{SITE}/assets/cards/bandits-matte-black-card-shot.jpg",
    "bandits-blue": f"{SITE}/assets/cards/bandits-blue-card-shot.jpg",
    "bandits-green": f"{SITE}/assets/cards/bandits-green-card-shot.jpg",
    "bandits-tortoise": f"{SITE}/assets/cards/bandits-tortoise-card-shot.jpg",
    "outback-black": f"{SITE}/assets/cards/outback-black-card-shot.jpg",
    "outback-blue": f"{SITE}/assets/cards/outback-blue-card-shot.jpg",
    "outback-red": f"{SITE}/assets/cards/outback-red-card-shot.jpg",
    "outback-green": f"{SITE}/assets/cards/outback-green-card-shot.jpg",
    "rasta-red": f"{SITE}/assets/cards/rasta-red-card-shot.jpg",
    "rasta-brown": f"{SITE}/assets/cards/rasta-brown-card-shot.jpg",
}

# Secondary shots (on-face or lifestyle "how it looks worn/in use").
# One per variant where available. Variants without a secondary only get the hero.
# Key format: "{variant}-lifestyle" so Gemini can discover them from the catalog.
SECONDARY_IMAGES = {
    "bandits-glossy-black-lifestyle": _drive("15tjjvXJRw0G-ppkA8jtQ-ezX2MVKxOQ-"),  # cafe
    "bandits-matte-black-lifestyle": _drive("1cLkc7jkcqgHL0XMFa9EPWrjFauQTMx9F"),  # cafe
    "bandits-green-lifestyle": _drive("17HMZv8Er50HVGrwM_SYjImX0Ovzmx6z0"),        # model on-face
    "bandits-tortoise-lifestyle": _drive("1bdEOKu4zvQ8yTnSu3vQL_4Zxf6a2cgH6"),     # cafe
    "outback-red-lifestyle": _drive("1tPRYgNPEYzTE5D_zVa8ViMt9aIMyuTwo"),           # model on-face
    "outback-green-lifestyle": _drive("1vecLcGctkLAzLI8vmeM3nCVZspPvJOTh"),         # river
    "rasta-brown-lifestyle": _drive("1BO-TFy_y4DCTZacvIrGIVm13g9v31UwB"),           # campus
    "rasta-red-lifestyle": _drive("1-56HRbuRZ7W2RNMIaoNOX_D6vHKdw_Ra"),             # beach
}

# Functional support images -- small set kept because they serve specific order flows.
SUPPORT_IMAGES = {
    "support-inclusions": _drive("11OZkBiNVDp4sbeXZZ_YkkY2KbhFznQ2h"),   # what's in the box
    "support-instapay-qr": _drive("1EIVKQlBsCJR6cvaEF3dtFfvegj8gKRgP"),  # provincial prepay
}

# Flat lookup across all image categories.
ALL_IMAGES = {
    **PRODUCT_IMAGES,
    **SECONDARY_IMAGES,
    **SUPPORT_IMAGES,
}


def get_catalog_text():
    """Format the product catalog as readable text for the system prompt."""
    lines = ["PRODUCT CATALOG:"]
    for name, info in CATALOG.items():
        lines.append(f"\n{name} ({info['code']}) -- {info['style']}")
        lines.append(f"  Best for: {info['best_for']}")
        lines.append(f"  Variants:")
        for variant in info["variants"]:
            note = info["variant_notes"].get(variant, "")
            lines.append(f"    - {variant}: {note}")
    return "\n".join(lines)


def get_specs_text():
    """Format shared technical specs."""
    s = SPECS
    return (
        "SPECS (all series):\n"
        f"  Polarization: {s['polarization']}\n"
        f"  Coatings: {s['coatings']}\n"
        f"  Rating: {s['rating']}\n"
        f"  Weight: {s['weight']}\n"
        f"  Dimensions: {s['dimensions']}\n"
        f"  Bandits/Outback: {s['bandits_outback_frame']}\n"
        f"  Rasta: {s['rasta_frame']}\n"
        f"  Fit: {s['fit']}"
    )


def get_pricing_text():
    """Format pricing as readable text for the system prompt."""
    p = PRICING
    return (
        f"PRICING:\n"
        f"  Single pair: P{p['single']}\n"
        f"  2-pair bundle: P{p['bundle_2']} ({p['bundle_note']})\n"
        f"  Metro Manila delivery (single pair): ~P{p['metro_delivery_single']}\n"
        f"  FREE delivery on 2-pair bundle"
    )


def get_faq_text():
    """Format FAQ as readable text for the system prompt."""
    lines = ["FAQ:"]
    for item in FAQ:
        lines.append(f"  Q: {item['topic']}")
        lines.append(f"  A: {item['answer']}")
        lines.append("")
    return "\n".join(lines)


def get_links_text():
    """Format links as readable text for the system prompt."""
    return (
        "LINKS (share when relevant, orders stay in Messenger):\n"
        f"  Website (backup reference): {LINKS['website']}\n"
        f"  Facebook page: {LINKS['facebook_page']}\n"
        f"  Messenger: {LINKS['messenger']}"
    )


def get_discount_text():
    """Format discount codes as readable text for the system prompt."""
    lines = ["DISCOUNT CODES:"]
    for code, info in DISCOUNT_CODES.items():
        if info["active"]:
            lines.append(f"  Code: {code}")
            lines.append(f"  Effect: {info['description']}")
            lines.append(f"  Rule: {info['rule']}")
            lines.append("")
    return "\n".join(lines)


def get_image_bank_text():
    """Format the image bank keys the bot can send. Strict 2-per-model."""
    lines = [
        "IMAGE BANK (return an image_key to send a photo. Only use keys listed here):",
        "",
        "Hero shots (product card photo — use when customer asks what a variant looks like):",
        "  bandits-glossy-black, bandits-matte-black, bandits-blue, bandits-green, bandits-tortoise",
        "  outback-black, outback-blue, outback-green, outback-red",
        "  rasta-brown, rasta-red",
        "",
        "Lifestyle shots (real environment, 'how it looks worn/in use' — use when customer is browsing):",
        "  bandits-glossy-black-lifestyle, bandits-matte-black-lifestyle",
        "  bandits-green-lifestyle, bandits-tortoise-lifestyle",
        "  outback-red-lifestyle, outback-green-lifestyle",
        "  rasta-brown-lifestyle, rasta-red-lifestyle",
        "",
        "Support (functional):",
        "  support-inclusions (send when customer asks what's in the box)",
        "  support-instapay-qr (send to provincial customers ready to prepay)",
        "",
        "Note: bandits-blue, outback-black, and outback-blue only have hero shots (no lifestyle).",
    ]
    return "\n".join(lines)


def get_image_url(image_key: str) -> str | None:
    """Look up an image URL by key across all categories."""
    return ALL_IMAGES.get(image_key)


def get_brand_text():
    """Format brand info."""
    return f"BRAND:\n  Name: {BRAND['name']}\n  Tagline: {BRAND['tagline']}"


def get_full_knowledge():
    """Return the complete knowledge base as a single string."""
    return "\n\n".join([
        get_brand_text(),
        get_catalog_text(),
        get_specs_text(),
        get_pricing_text(),
        get_discount_text(),
        get_faq_text(),
        get_links_text(),
        get_image_bank_text(),
    ])
