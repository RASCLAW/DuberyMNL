"""
DuberyMNL product catalog, pricing, and FAQ.

Pure data module -- no API calls, no side effects.
Returns strings for injection into the chatbot system prompt.

Last updated: 2026-04-15
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
            "Green": "Green + black bicolor frame, blue-green mirror lenses, green/yellow tropical pattern on temples",
            "Tortoise": "Brown + dark brown tortoiseshell pattern frame, brown/amber lenses",
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
            "Green": "Matte black frame, green/purple iridescent mirror lenses, green DUBERY badge",
            "Red": "Matte black frame, red/orange mirror lenses, red DUBERY badge, purple pattern on inner temples",
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
    "per_pair": 599,
    "currency": "PHP",
    "shipping_min_single": 100,
    "promo_note": "FREE shipping when customer orders 2 or more pairs (any mix of models/colors). No bundle discount -- each pair stays at 599.",
}

# --- Discount Codes ---
# DUBERY50 retired 2026-04-15 -- bundle pricing replaces the discount lever.

DISCOUNT_CODES = {}

# --- FAQ ---

FAQ = [
    {
        "topic": "Payment methods",
        "answer": "We accept GCash, bank transfer, or InstaPay. If you're in Metro Manila, COD is also available -- just pay the rider when it arrives. For orders outside Metro Manila, we'll need payment first before we ship.",
    },
    {
        "topic": "Delivery - Metro Manila",
        "answer": "We deliver within Metro Manila -- same-day or next-day depending on when you order. Shipping for a single pair starts at 100 and depends on your address. Buy 2 or more pairs and shipping is FREE. COD is available here too.",
    },
    {
        "topic": "Delivery - Provincial",
        "answer": "We ship nationwide! For provincial orders we just need payment first (GCash, bank transfer, or InstaPay) since COD is Metro Manila only. Shipping on a single pair starts at 100 and varies by area -- send me your location and I'll check. Buy 2 or more pairs and shipping is FREE wherever you are.",
    },
    {
        "topic": "Returns",
        "answer": "We check every pair before shipping, but if anything's off when you receive it, just message us within 24 hours with a photo and we'll replace it right away -- no hassle.",
    },
    {
        "topic": "Polarized",
        "answer": "Yep, all our lenses are polarized with UV400 protection. Basically, polarized means it cuts out the harsh glare from the sun, road, and water -- so your eyes don't strain as much and everything looks clearer. UV400 means it blocks harmful sun rays too. It's like getting the lens quality of expensive brands without the price tag.",
    },
    {
        "topic": "What's included",
        "answer": "Every pair comes with the full set -- a branded Dubery box, microfiber cleaning cloth, and a soft drawstring pouch. If you want extra protection, we have a zippered hard case you can add for 100.",
    },
    {
        "topic": "How to order",
        "answer": "Just send me these details and we're good: your full name, complete delivery address (with landmarks nearby), phone number, which model and color you want, and when you'd like it delivered. I'll confirm everything and get it sorted.",
    },
    {
        "topic": "Urgent orders",
        "answer": "Need it ASAP? We can do urgent delivery within Metro Manila. Just drop your number and we'll call you right away to arrange it.",
    },
    {
        "topic": "Sizing",
        "answer": "One size fits most adults. The frame is about 146mm wide and super lightweight at around 31g -- you'll barely feel it. If you're worried about fit, most people find it comfortable.",
    },
    {
        "topic": "Frame and lens material",
        "answer": "The Bandits and Outback use TR90 frames -- that's a flexible material that won't snap easily, even if you sit on them. Lenses are polycarbonate, which is impact-resistant. The Rasta series uses a PC frame with TAC lenses, also solid quality.",
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
# 48 images across 8 categories. Each image has a URL and a one-line caption
# so Gemini knows what the photo actually depicts and can pick the right one
# for the conversational context.
#
# Hero shots served from Vercel (duberymnl.com). All other categories served
# from Google Drive via lh3.googleusercontent.com CDN.
#
# Naming convention: category prefix + variant, except hero shots which use
# bare variant keys (e.g. "bandits-green" = hero, "lifestyle-bandits-green-cafe"
# = lifestyle). Meta attachment caching is lazy (first-send upload), no warmup.

SITE = "https://duberymnl.com"


def _drive(file_id: str) -> str:
    """Construct a CDN URL for a Google Drive file."""
    return f"https://lh3.googleusercontent.com/d/{file_id}"


def _img(url: str, caption: str) -> dict:
    """Build an image entry with url + caption."""
    return {"url": url, "caption": caption}


# Hero shots (one per variant — 11 total).
# FORMAT NOTE: all 11 hero shots are flat-lay photos on a kraft/tan background
# showing the sunglasses alongside the full unboxing set (Dubery branded box,
# black drawstring pouch, microfiber cloth, blue warranty/info card). This
# means every hero shot also doubles as a "what's in the box" image — the
# bot does NOT need to send support-inclusions separately when a hero has
# already been sent.
PRODUCT_IMAGES = {
    "bandits-glossy-black": _img(
        f"{SITE}/assets/cards/bandits-glossy-black-card-shot.jpg",
        "Bandits Glossy Black — flat-lay with Dubery box, pouch, cloth, warranty card. Glossy black frame, dark polarized lenses.",
    ),
    "bandits-matte-black": _img(
        f"{SITE}/assets/cards/bandits-matte-black-card-shot.jpg",
        "Bandits Matte Black — flat-lay with Dubery box, pouch, cloth, warranty card. Matte black frame, orange/gold mirror lenses, colorful pattern on inside of temples.",
    ),
    "bandits-blue": _img(
        f"{SITE}/assets/cards/bandits-blue-card-shot.jpg",
        "Bandits Blue — flat-lay with Dubery box, pouch, cloth, warranty card. Black frame with blue accents, blue mirror lenses, blue wave pattern on temples.",
    ),
    "bandits-green": _img(
        f"{SITE}/assets/cards/bandits-green-card-shot.jpg",
        "Bandits Green — flat-lay with Dubery box, pouch, cloth, warranty card. Green + black bicolor frame, blue-green mirror lenses, green/yellow tropical pattern on temples.",
    ),
    "bandits-tortoise": _img(
        f"{SITE}/assets/cards/bandits-tortoise-card-shot.jpg",
        "Bandits Tortoise — flat-lay with Dubery box, pouch, cloth, warranty card. Brown + dark brown tortoiseshell pattern frame, brown/amber lenses.",
    ),
    "outback-black": _img(
        f"{SITE}/assets/cards/outback-black-card-shot.jpg",
        "Outback Black — flat-lay with Dubery box, pouch, cloth, warranty card. All matte black, dark polarized lenses.",
    ),
    "outback-blue": _img(
        f"{SITE}/assets/cards/outback-blue-card-shot.jpg",
        "Outback Blue — flat-lay with Dubery box, pouch, cloth, warranty card. Matte black frame, blue mirror lenses, white DUBERY badge, black/white pattern on inner temples.",
    ),
    "outback-red": _img(
        f"{SITE}/assets/cards/outback-red-card-shot.jpg",
        "Outback Red — flat-lay with Dubery box, pouch, cloth, warranty card. Matte black frame, red/orange mirror lenses, red DUBERY badge, purple pattern on inner temples.",
    ),
    "outback-green": _img(
        f"{SITE}/assets/cards/outback-green-card-shot.jpg",
        "Outback Green — flat-lay with Dubery box, pouch, cloth, warranty card. Matte black frame, green/purple iridescent mirror lenses, green DUBERY badge.",
    ),
    "rasta-red": _img(
        f"{SITE}/assets/cards/rasta-red-card-shot.jpg",
        "Rasta Red — flat-lay with Dubery box, pouch, cloth, warranty card. Oversized aviator-style square frame (bigger than Outback), matte black frame, red/orange mirror lenses, gold accents + red-green-yellow rasta stripe on temples.",
    ),
    "rasta-brown": _img(
        f"{SITE}/assets/cards/rasta-brown-card-shot.jpg",
        "Rasta Brown — flat-lay with Dubery box, pouch, cloth, warranty card. Oversized aviator-style square frame (bigger than Outback), matte black frame, brown/amber lenses, gold accents + red-green-yellow rasta stripe on temples.",
    ),
}

# Model shots (on-face, "how does it look worn?" — 6 variants covered).
MODEL_SHOTS = {
    "model-bandits-glossy-black": _img(
        _drive("1ZXb1ZYD_3YGKYQug2NTtVkODiY2JrMh5"),
        "Male model wearing Bandits Glossy Black on-face, studio portrait",
    ),
    "model-bandits-green": _img(
        _drive("17HMZv8Er50HVGrwM_SYjImX0Ovzmx6z0"),
        "Male model wearing Bandits Green on-face, close-up portrait",
    ),
    "model-bandits-matte-black": _img(
        _drive("1qq5QmjmIYc3a8tIWE5mUtpyvogt24VrZ"),
        "Male model wearing Bandits Matte Black on-face, studio portrait",
    ),
    "model-bandits-tortoise": _img(
        _drive("1ItU65ZTG8g8eZC2jd6t6svzAqIUKOuLy"),
        "Male model wearing Bandits Tortoise on-face, close-up portrait",
    ),
    "model-outback-red": _img(
        _drive("1tPRYgNPEYzTE5D_zVa8ViMt9aIMyuTwo"),
        "Male model wearing Outback Red on-face, studio portrait",
    ),
    "model-rasta-brown": _img(
        _drive("1bpKrPUNAxN6UYbnImediYjcmdaiL8Voh"),
        "Male model wearing Rasta Brown on-face, close-up portrait",
    ),
}

# Lifestyle shots (real environments — mood/browsing, 6 variants).
LIFESTYLE_SHOTS = {
    "lifestyle-bandits-tortoise-cafe": _img(
        _drive("1bdEOKu4zvQ8yTnSu3vQL_4Zxf6a2cgH6"),
        "Person wearing Bandits Tortoise at a cafe, lifestyle mood shot",
    ),
    "lifestyle-bandits-glossy-black-cafe": _img(
        _drive("15tjjvXJRw0G-ppkA8jtQ-ezX2MVKxOQ-"),
        "Person wearing Bandits Glossy Black at a cafe, lifestyle mood shot",
    ),
    "lifestyle-bandits-matte-black-cafe": _img(
        _drive("1cLkc7jkcqgHL0XMFa9EPWrjFauQTMx9F"),
        "Person wearing Bandits Matte Black at a cafe, lifestyle mood shot",
    ),
    "lifestyle-rasta-brown-campus": _img(
        _drive("1BO-TFy_y4DCTZacvIrGIVm13g9v31UwB"),
        "Person wearing Rasta Brown on a campus walkway, lifestyle mood shot",
    ),
    "lifestyle-outback-green-river": _img(
        _drive("1vecLcGctkLAzLI8vmeM3nCVZspPvJOTh"),
        "Person wearing Outback Green by a river/outdoors, lifestyle mood shot",
    ),
    "lifestyle-rasta-red-beach": _img(
        _drive("1-56HRbuRZ7W2RNMIaoNOX_D6vHKdw_Ra"),
        "Person wearing Rasta Red at the beach, lifestyle mood shot",
    ),
}

# Collection shots (series showcases — 4 total).
COLLECTION_SHOTS = {
    "collection-bandits-series": _img(
        _drive("1x2nfk4fwK0JVInobskHrBPr18D_6TOkX"),
        "All 5 Bandits variants laid out together — Glossy Black, Matte Black, Blue, Green, Tortoise",
    ),
    "collection-outback-series": _img(
        _drive("1ddu1nMpFTPk24k4YBR0PA5g9r_sQ7U3g"),
        "All 4 Outback variants laid out together — Black, Blue, Red, Green",
    ),
    "collection-rasta-series-1": _img(
        _drive("1_wzvnR0f8i_wusaYeTYrdv0sj1mN1PO_"),
        "Both Rasta variants together (Red and Brown), series showcase shot",
    ),
    "collection-rasta-series-2": _img(
        _drive("1-v-V1kcJUvc-wr4GToVOaQQeVDVGZ9-i"),
        "Both Rasta variants together (Red and Brown), alt series showcase angle",
    ),
}

# Brand graphics (features, benefits, typography — 5 total).
BRAND_GRAPHICS = {
    "brand-feature-callout": _img(
        _drive("1nkwuekP24rA85-Z8l27HCWIz9Xxq4qbD"),
        "Dubery feature callout graphic showing polarization + UV400 + TR90 frame benefits",
    ),
    "brand-see-clear": _img(
        _drive("1tbk3K9oYsOK82fc08Ou1Vdl2X0uFOFJx"),
        "'See Clear' brand typography graphic highlighting the polarization benefit",
    ),
    "brand-made-for-the-grind": _img(
        _drive("1kBQ9-r8t2NHXCmKYTdJITPj7raD6Rrp9"),
        "'Made for the Grind' brand typography graphic, durability messaging",
    ),
    "brand-outback-red-callout": _img(
        _drive("1H_tU6E1NdWcKVVtHjBIevLK8u5dND7Gu"),
        "Outback Red with feature callouts (matte black frame, gold mirror lenses, red badge)",
    ),
    "brand-style-that-protects": _img(
        _drive("1Yqek982iv_Q0bdq7TugF4U58KGO_5cVs"),
        "'Style That Protects' brand typography graphic combining style + UV protection messaging",
    ),
}

# Customer feedback (real Messenger review screenshots — 8 total, social proof).
CUSTOMER_FEEDBACK = {
    "feedback-bandits-green": _img(
        _drive("1SmeVrBPhMgMBG8W7ZZZmBMXto6tdMcvA"),
        "Real customer feedback screenshot for Bandits Green",
    ),
    "feedback-bandits-tortoise": _img(
        _drive("19B3YfqcPrkI3CgkFttcNtsp6m5x0F8Xj"),
        "Real customer feedback screenshot for Bandits Tortoise",
    ),
    "feedback-bandits-black": _img(
        _drive("1YFe5GC7S1sbcVVWK0PKQbcHYRpxaQ_--"),
        "Real customer feedback screenshot for Bandits Black",
    ),
    "feedback-outback-blue": _img(
        _drive("1CN-SlRdPtDJ1g5djpz0lVZTmbfd9xHf5"),
        "Real customer feedback screenshot for Outback Blue",
    ),
    "feedback-outback-black": _img(
        _drive("1isXQe9MQLN_YgZUkjggBzlRgK0GKbHLB"),
        "Real customer feedback screenshot for Outback Black",
    ),
    "feedback-outback-red": _img(
        _drive("1MO6vlkCo_8_yaDFeiNX-YGIippebDvdb"),
        "Real customer feedback screenshot for Outback Red",
    ),
    "feedback-outback-green": _img(
        _drive("1KIYOCR23L66feY_zZx4m0bEgFmUnKfv9"),
        "Real customer feedback screenshot for Outback Green",
    ),
    "feedback-rasta-red": _img(
        _drive("1BfbPQRwK0Idd0AgaeIwAUpZOS-Gc5KvK"),
        "Real customer feedback screenshot for Rasta Red",
    ),
}

# Proof shots (shipping / stock / legitimacy — 6 total, for skeptical customers).
PROOF_SHOTS = {
    "proof-cod-packages": _img(
        _drive("1wGfa5y2h0a3J-3bVvJzjotr0k2sBSQb1"),
        "Stack of COD packages ready for dispatch — proof of real daily shipments",
    ),
    "proof-branded-boxes-bundle": _img(
        _drive("1IVwh7ku0JM6GISwGAemFZyTCh4InZtCK"),
        "Bundle of branded Dubery boxes — shows real packaging and stock",
    ),
    "proof-inventory-stock": _img(
        _drive("1mJNjT5IuZeoyAt04uezFZbVtGz7V_iAt"),
        "Warehouse inventory stock — proof we carry real inventory",
    ),
    "proof-jnt-shipments": _img(
        _drive("1X2vSmisP7tTD1_sXgyBOL2spmzIeu_d6"),
        "J&T courier pickup photo — proof of real shipment pickups",
    ),
    "proof-labeled-inventory": _img(
        _drive("1G7Jnxo8GoX8O6j0v9EiaBSU4j9VNQdn2"),
        "Labeled inventory organized by model — proof of operations",
    ),
    "proof-lbc-dropoff": _img(
        _drive("1kAVFPbcfmjpkGyxYgnOfHyHKr0wPDYEO"),
        "LBC branch drop-off photo — proof of provincial shipping",
    ),
}

# Sales support (functional images for specific order flows — 2 total).
SALES_SUPPORT = {
    "support-inclusions": _img(
        _drive("11OZkBiNVDp4sbeXZZ_YkkY2KbhFznQ2h"),
        "Flat lay showing what comes in the box — branded Dubery box, microfiber cloth, drawstring pouch",
    ),
    "support-instapay-qr": _img(
        _drive("1EIVKQlBsCJR6cvaEF3dtFfvegj8gKRgP"),
        "InstaPay QR code for provincial customers to prepay via GCash or bank transfer",
    ),
}

# Flat lookup across all 48 images. Values are dicts with "url" and "caption".
ALL_IMAGES = {
    **PRODUCT_IMAGES,
    **MODEL_SHOTS,
    **LIFESTYLE_SHOTS,
    **COLLECTION_SHOTS,
    **BRAND_GRAPHICS,
    **CUSTOMER_FEEDBACK,
    **PROOF_SHOTS,
    **SALES_SUPPORT,
}


def get_catalog_text():
    """Format the product catalog as readable text for the system prompt.

    NOTE: The internal model codes (D518, D918, D008) are deliberately omitted
    from the system prompt. They are internal SKU references only -- customers
    should never see them in chatbot replies.
    """
    lines = ["PRODUCT CATALOG:"]
    for name, info in CATALOG.items():
        lines.append(f"\n{name} -- {info['style']}")
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
        f"  Per pair: {p['per_pair']} (each pair is priced independently -- no bundle discount)\n"
        f"  2 pairs total: {p['per_pair'] * 2}\n"
        f"  Single-pair shipping: starts at {p['shipping_min_single']}, varies by address (nationwide)\n"
        f"  PROMO: {p['promo_note']}\n"
        f"  COD: Metro Manila only. Provincial orders require prepayment (GCash, bank transfer, or InstaPay)."
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
    if not DISCOUNT_CODES:
        return ""
    lines = ["DISCOUNT CODES:"]
    for code, info in DISCOUNT_CODES.items():
        if info["active"]:
            lines.append(f"  Code: {code}")
            lines.append(f"  Effect: {info['description']}")
            lines.append(f"  Rule: {info['rule']}")
            lines.append("")
    return "\n".join(lines)


def _format_category(title: str, hint: str, images: dict) -> list:
    """Format one category block for the image bank text."""
    lines = [f"{title} ({hint}):"]
    for key, entry in images.items():
        lines.append(f"  {key} — {entry['caption']}")
    lines.append("")
    return lines


def get_image_bank_text():
    """
    Format the full image bank for the system prompt.

    Each image is listed with its key and a one-line caption so the model can
    pick the right photo for the conversational context (e.g. social proof for
    skeptical customers, lifestyle for browsing, hero for direct product asks).
    """
    lines = [
        "IMAGE BANK (return image_key to send a photo — only use keys listed here):",
        "",
    ]
    lines += _format_category(
        "Hero shots",
        "flat-lay with full unboxing set (box, pouch, cloth, warranty card) — default when customer asks what a variant looks like, also doubles as 'what's in the box' so don't also send support-inclusions after sending a hero",
        PRODUCT_IMAGES,
    )
    lines += _format_category(
        "Model shots", "on-face studio portraits — use when customer wants to see it worn",
        MODEL_SHOTS,
    )
    lines += _format_category(
        "Lifestyle shots", "real-environment mood shots — use when customer is browsing/vibing",
        LIFESTYLE_SHOTS,
    )
    lines += _format_category(
        "Collection shots", "series lineup — use when customer says 'show me all X' or wants to compare a series",
        COLLECTION_SHOTS,
    )
    lines += _format_category(
        "Brand graphics", "feature/benefit/typography — use when explaining polarization, UV, durability",
        BRAND_GRAPHICS,
    )
    lines += _format_category(
        "Customer feedback", "social proof — use when customer is hesitant, asks if legit, or wants reviews",
        CUSTOMER_FEEDBACK,
    )
    lines += _format_category(
        "Proof shots", "shipping/stock legitimacy — use when customer asks if you're real or ships on time",
        PROOF_SHOTS,
    )
    lines += _format_category(
        "Sales support", "functional — use in specific order flows",
        SALES_SUPPORT,
    )
    return "\n".join(lines).rstrip()


def get_image_url(image_key: str) -> str | None:
    """Look up an image URL by key across all categories."""
    entry = ALL_IMAGES.get(image_key)
    if not entry:
        return None
    return entry["url"]


def get_image_caption(image_key: str) -> str | None:
    """Look up an image caption by key across all categories."""
    entry = ALL_IMAGES.get(image_key)
    if not entry:
        return None
    return entry["caption"]


def get_brand_text():
    """Format brand info."""
    return f"BRAND:\n  Name: {BRAND['name']}\n  Tagline: {BRAND['tagline']}"


def get_full_knowledge():
    """Return the complete knowledge base as a single string."""
    sections = [
        get_brand_text(),
        get_catalog_text(),
        get_specs_text(),
        get_pricing_text(),
        get_discount_text(),
        get_faq_text(),
        get_links_text(),
        get_image_bank_text(),
    ]
    return "\n\n".join(s for s in sections if s)
