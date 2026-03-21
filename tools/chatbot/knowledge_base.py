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
    "single": 699,
    "bundle_2": 1200,
    "currency": "PHP",
    "bundle_note": "Any mix of models/colors",
}

# --- FAQ ---

FAQ = [
    {
        "topic": "Payment",
        "answer": "COD (Cash on Delivery) only. Pay when you receive the package. No online payment yet.",
    },
    {
        "topic": "Delivery - Metro Manila",
        "answer": "Same-day or next-day via Grab/Lalamove/MoveIt. Delivery fee around P100+, varies by location. Free delivery on 2-pair bundle.",
    },
    {
        "topic": "Delivery - Provincial",
        "answer": "1-3 business days via J&T or LBC. Shipping fee varies by location. Free delivery on 2-pair bundle.",
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
        "answer": "Every pair comes with a zippered hard case, microfiber cleaning cloth, and branded box.",
    },
    {
        "topic": "How to order",
        "answer": "Message us with: (1) your full name, (2) complete delivery address, (3) phone number, and (4) which model + color you want. We'll confirm and ship.",
    },
    {
        "topic": "Sizing",
        "answer": "One size fits most adults. Frame width is around 14cm.",
    },
]

# --- Brand info ---

BRAND = {
    "name": "DuberyMNL",
    "tagline": "Polarized shades that don't break the bank",
    "page_url": "https://www.facebook.com/DuberyMNL",
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
        f"  Single pair: P{p['single']}\n"
        f"  2 pairs bundle: P{p['bundle_2']} ({p['bundle_note']})\n"
        f"  Free delivery on 2-pair bundle"
    )


def get_faq_text():
    """Format FAQ as readable text for the system prompt."""
    lines = ["FAQ:"]
    for item in FAQ:
        lines.append(f"  Q: {item['topic']}")
        lines.append(f"  A: {item['answer']}")
        lines.append("")
    return "\n".join(lines)


def get_full_knowledge():
    """Return the complete knowledge base as a single string."""
    return "\n\n".join([
        get_catalog_text(),
        get_pricing_text(),
        get_faq_text(),
    ])
