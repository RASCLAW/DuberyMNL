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
# Hero shots served from Vercel (duberymnl.com) for proven reliability.
# Other categories served from Google Drive via lh3.googleusercontent.com CDN.

SITE = "https://duberymnl.com"

def _drive(file_id: str) -> str:
    """Construct a CDN URL for a Google Drive file."""
    return f"https://lh3.googleusercontent.com/d/{file_id}"

# Hero shots (product card photos) -- single photo per variant
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

# Model shots (on-face, "how does it look worn?")
MODEL_SHOTS = {
    "bandits-glossy-black": _drive("1ZXb1ZYD_3YGKYQug2NTtVkODiY2JrMh5"),
    "bandits-green": _drive("17HMZv8Er50HVGrwM_SYjImX0Ovzmx6z0"),
    "bandits-matte-black": _drive("1qq5QmjmIYc3a8tIWE5mUtpyvogt24VrZ"),
    "bandits-tortoise": _drive("1ItU65ZTG8g8eZC2jd6t6svzAqIUKOuLy"),
    "outback-red": _drive("1tPRYgNPEYzTE5D_zVa8ViMt9aIMyuTwo"),
    "rasta-brown": _drive("1bpKrPUNAxN6UYbnImediYjcmdaiL8Voh"),
}

# Lifestyle shots (mood, real environments, for browsing customers)
LIFESTYLE_SHOTS = {
    "bandits-tortoise-cafe": _drive("1bdEOKu4zvQ8yTnSu3vQL_4Zxf6a2cgH6"),
    "bandits-glossy-black-cafe": _drive("15tjjvXJRw0G-ppkA8jtQ-ezX2MVKxOQ-"),
    "rasta-brown-campus": _drive("1BO-TFy_y4DCTZacvIrGIVm13g9v31UwB"),
    "outback-green-river": _drive("1vecLcGctkLAzLI8vmeM3nCVZspPvJOTh"),
    "bandits-matte-black-cafe": _drive("1cLkc7jkcqgHL0XMFa9EPWrjFauQTMx9F"),
    "rasta-red-beach": _drive("1-56HRbuRZ7W2RNMIaoNOX_D6vHKdw_Ra"),
}

# Collection shots (series showcases)
COLLECTION_SHOTS = {
    "bandits-series": _drive("1x2nfk4fwK0JVInobskHrBPr18D_6TOkX"),
    "outback-series": _drive("1ddu1nMpFTPk24k4YBR0PA5g9r_sQ7U3g"),
    "rasta-series-1": _drive("1_wzvnR0f8i_wusaYeTYrdv0sj1mN1PO_"),
    "rasta-series-2": _drive("1-v-V1kcJUvc-wr4GToVOaQQeVDVGZ9-i"),
}

# Brand graphics (features, benefits, typography)
BRAND_GRAPHICS = {
    "feature-callout": _drive("1nkwuekP24rA85-Z8l27HCWIz9Xxq4qbD"),
    "see-clear": _drive("1tbk3K9oYsOK82fc08Ou1Vdl2X0uFOFJx"),
    "made-for-the-grind": _drive("1kBQ9-r8t2NHXCmKYTdJITPj7raD6Rrp9"),
    "outback-red-callout": _drive("1H_tU6E1NdWcKVVtHjBIevLK8u5dND7Gu"),
    "style-that-protects": _drive("1Yqek982iv_Q0bdq7TugF4U58KGO_5cVs"),
}

# Real customer feedback (social proof)
CUSTOMER_FEEDBACK = {
    "feedback-bandits-green": _drive("1SmeVrBPhMgMBG8W7ZZZmBMXto6tdMcvA"),
    "feedback-outback-blue": _drive("1CN-SlRdPtDJ1g5djpz0lVZTmbfd9xHf5"),
    "feedback-rasta-red": _drive("1BfbPQRwK0Idd0AgaeIwAUpZOS-Gc5KvK"),
    "feedback-bandits-tortoise": _drive("19B3YfqcPrkI3CgkFttcNtsp6m5x0F8Xj"),
    "feedback-outback-black": _drive("1isXQe9MQLN_YgZUkjggBzlRgK0GKbHLB"),
    "feedback-outback-red": _drive("1MO6vlkCo_8_yaDFeiNX-YGIippebDvdb"),
    "feedback-outback-green": _drive("1KIYOCR23L66feY_zZx4m0bEgFmUnKfv9"),
    "feedback-bandits-black": _drive("1YFe5GC7S1sbcVVWK0PKQbcHYRpxaQ_--"),
}

# Shipping/stock proof (for hesitant/skeptical customers)
PROOF_SHOTS = {
    "cod-packages": _drive("1wGfa5y2h0a3J-3bVvJzjotr0k2sBSQb1"),
    "branded-boxes-bundle": _drive("1IVwh7ku0JM6GISwGAemFZyTCh4InZtCK"),
    "inventory-stock": _drive("1mJNjT5IuZeoyAt04uezFZbVtGz7V_iAt"),
    "jnt-shipments": _drive("1X2vSmisP7tTD1_sXgyBOL2spmzIeu_d6"),
    "labeled-inventory": _drive("1G7Jnxo8GoX8O6j0v9EiaBSU4j9VNQdn2"),
    "lbc-dropoff": _drive("1kAVFPbcfmjpkGyxYgnOfHyHKr0wPDYEO"),
}

# Sales support (inclusions, payment)
SALES_SUPPORT = {
    "inclusions": _drive("11OZkBiNVDp4sbeXZZ_YkkY2KbhFznQ2h"),
    "instapay-qr": _drive("1EIVKQlBsCJR6cvaEF3dtFfvegj8gKRgP"),
}

# Flat lookup across all image categories
ALL_IMAGES = {
    **PRODUCT_IMAGES,
    **{f"model-{k}": v for k, v in MODEL_SHOTS.items()},
    **{f"lifestyle-{k}": v for k, v in LIFESTYLE_SHOTS.items()},
    **{f"collection-{k}": v for k, v in COLLECTION_SHOTS.items()},
    **{f"brand-{k}": v for k, v in BRAND_GRAPHICS.items()},
    **{f"feedback-{k.replace('feedback-', '')}": v for k, v in CUSTOMER_FEEDBACK.items()},
    **{f"proof-{k}": v for k, v in PROOF_SHOTS.items()},
    **{f"support-{k}": v for k, v in SALES_SUPPORT.items()},
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
    """Format the image bank keys the bot can send."""
    lines = [
        "IMAGE BANK (return an image_key to send a photo):",
        "",
        "Hero shots (single product photo):",
        "  bandits-glossy-black, bandits-matte-black, bandits-blue, bandits-green, bandits-tortoise",
        "  outback-black, outback-blue, outback-green, outback-red",
        "  rasta-brown, rasta-red",
        "",
        "Model shots (on-face, 'how it looks worn'):",
        "  model-bandits-glossy-black, model-bandits-green, model-bandits-matte-black, model-bandits-tortoise",
        "  model-outback-red, model-rasta-brown",
        "",
        "Lifestyle shots (mood/browsing):",
        "  lifestyle-bandits-tortoise-cafe, lifestyle-bandits-glossy-black-cafe",
        "  lifestyle-bandits-matte-black-cafe, lifestyle-rasta-brown-campus",
        "  lifestyle-outback-green-river, lifestyle-rasta-red-beach",
        "",
        "Collection shots ('show me all [series]'):",
        "  collection-bandits-series, collection-outback-series",
        "  collection-rasta-series-1, collection-rasta-series-2",
        "",
        "Brand graphics (polarization/features):",
        "  brand-feature-callout, brand-see-clear, brand-made-for-the-grind",
        "  brand-outback-red-callout, brand-style-that-protects",
        "",
        "Customer feedback (real reviews, social proof):",
        "  feedback-bandits-green, feedback-bandits-tortoise, feedback-bandits-black",
        "  feedback-outback-blue, feedback-outback-black, feedback-outback-red, feedback-outback-green",
        "  feedback-rasta-red",
        "",
        "Proof shots ('is this legit?' / shipping proof):",
        "  proof-cod-packages, proof-branded-boxes-bundle, proof-inventory-stock",
        "  proof-jnt-shipments, proof-labeled-inventory, proof-lbc-dropoff",
        "",
        "Sales support:",
        "  support-inclusions (what's in the box)",
        "  support-instapay-qr (send to provincial customers for prepaid orders)",
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
