"""
DuberyMNL product catalog, pricing, and FAQ.

Pure data module -- no API calls, no side effects.
Returns strings for injection into the chatbot system prompt.
"""

# --- Product Catalog ---

CATALOG = {
    "Bandits": {
        "variants": ["Glossy Black", "Matte Black", "Blue", "Green", "Tortoise"],
        "style": "Two-tone sporty wrap frame",
        "best_for": "Active lifestyle, sports, motorcycling, outdoors",
    },
    "Outback": {
        "variants": ["Black", "Blue", "Red", "Green"],
        "style": "Classic rectangular frame, slightly curved",
        "best_for": "Daily wear, commuting, driving",
    },
    "Rasta": {
        "variants": ["Red", "Brown"],
        "style": "Reggae-inspired colorway, lightweight frame",
        "best_for": "Casual/lifestyle, standing out",
    },
}

# --- Pricing ---

PRICING = {
    "single": 599,
    "bundle_2": 1099,
    "currency": "PHP",
    "bundle_note": "Any mix of models/colors. Free shipping on bundle.",
}

# --- Discount Codes ---

DISCOUNT_CODES = {}

# --- FAQ ---

FAQ = [
    {
        "topic": "Payment",
        "answer": "GCash, bank transfer, or InstaPay. If you're in Metro Manila, COD (Cash on Delivery) is also available -- no extra fee. Provincial orders are prepaid only.",
    },
    {
        "topic": "Delivery - Metro Manila",
        "answer": "Same-day or next-day via Grab/Lalamove/MoveIt. Single pair: delivery fee minimum P100, varies by address. 2-pair bundle: FREE delivery.",
    },
    {
        "topic": "Delivery - Provincial",
        "answer": "1-3 business days via J&T or LBC. Single pair: shipping fee minimum P100, varies by location. 2-pair bundle: FREE shipping.",
    },
    {
        "topic": "COD Fee",
        "answer": "P0 -- no extra charge for COD.",
    },
    {
        "topic": "Returns",
        "answer": "Defective items replaced free. Message within 24 hours of receiving with photos of the defect.",
    },
    {
        "topic": "Polarized",
        "answer": "Yes, all Dubery lenses are polarized with UV400 protection. Blocks glare and protects your eyes from harmful UV rays.",
    },
    {
        "topic": "What's included",
        "answer": "Every pair comes with a branded Dubery box, microfiber cleaning cloth, and a soft drawstring pouch. A zippered hard case is available as an add-on for P100 if the customer asks.",
    },
    {
        "topic": "How to order",
        "answer": "Send us: (1) full name, (2) complete delivery address with nearby landmarks, (3) phone number, (4) model + color (can be multiple), (5) delivery preference (same-day / next-day / urgent), (6) preferred delivery time. We'll confirm and ship.",
    },
    {
        "topic": "Sizing",
        "answer": "One size fits most adults. Frame width is about 146mm (14.6cm), lightweight at around 31g.",
    },
]

# --- Brand info ---

BRAND = {
    "name": "DuberyMNL",
    "tagline": "Polarized shades that don't break the bank",
    "page_url": "https://www.facebook.com/DuberyMNL",
    "website_url": "https://duberymnl.vercel.app",
}

# --- Links (for sharing with customers) ---

LINKS = {
    "website": "https://duberymnl.vercel.app",
    "order_form": "https://duberymnl.vercel.app#order",
    "facebook_page": "https://www.facebook.com/DuberyMNL",
    "messenger": "https://m.me/DuberyMNL",
}


def get_catalog_text():
    """Format the product catalog as readable text for the system prompt."""
    lines = ["PRODUCT CATALOG:"]
    for name, info in CATALOG.items():
        variants = ", ".join(info["variants"])
        lines.append(f"  {name} -- {info['style']}")
        lines.append(f"    Colors: {variants}")
        lines.append(f"    Best for: {info['best_for']}")
    return "\n".join(lines)


def get_pricing_text():
    """Format pricing as readable text for the system prompt."""
    p = PRICING
    return (
        f"PRICING:\n"
        f"  Single pair: P{p['single']} (+ shipping P100 min, varies by address)\n"
        f"  2 pairs bundle: P{p['bundle_2']} ({p['bundle_note']})\n"
        f"  Bundle gets FREE shipping -- surface this when customer asks about single"
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
        "LINKS (share these when relevant):\n"
        f"  Website & order form: {LINKS['website']}\n"
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
            lines.append(f"  Note: {info['note']}")
            lines.append("")
    return "\n".join(lines)


def get_full_knowledge():
    """Return the complete knowledge base as a single string."""
    sections = [
        get_catalog_text(),
        get_pricing_text(),
        get_discount_text(),
        get_faq_text(),
        get_links_text(),
    ]
    return "\n\n".join(s for s in sections if s)
