"""
DuberyMNL comment auto-responder templates.

Pure data module -- no API calls, no side effects.
Used by comment_responder.py for reply text and DM content.
"""

# -- Comment reply templates (short, natural Taglish) --------------------------
# Rotated randomly when replying to a comment. Keep them varied.

COMMENT_REPLIES = [
    "DM sent! Check your inbox 😎",
    "Sent you a message! 📩",
    "Check your inbox! 😉",
    "Message sent! 📩",
    "Just sent you a DM! 😎",
    "Check your DMs! 📩",
    "We sent you a message 😊",
    "DM sent! Check it out 😎",
    "Just messaged you! 📩",
    "Sent you a DM — check your inbox! 😎",
]

# -- DM opening templates (personal, not automated) ---------------------------
# Sent to the commenter's Messenger inbox. Must match dubery-chatbot voice.

DM_OPENERS = [
    (
        "Hi! Nakita namin comment mo sa post namin 😎\n\n"
        "We sell polarized sunglasses -- solid build, real UV protection.\n\n"
        "Single pair: P699\n"
        "2 pairs (any mix): P1,200 + FREE delivery Metro Manila\n\n"
        "Interested ka? Just reply with your preferred style and we'll set it up 🤙"
    ),
    (
        "Hello! Thanks sa comment 😊\n\n"
        "DuberyMNL sunglasses -- polarized, UV400, solid quality.\n\n"
        "P699 per pair or P1,200 for 2 (any color mix) with free delivery sa Metro Manila.\n\n"
        "Gusto mo malaman available colors? Just reply! 😎"
    ),
    (
        "Uy hi! Saw your comment 😎\n\n"
        "Our shades are polarized with UV400 protection -- great for driving, beach, everyday.\n\n"
        "P699 each / P1,200 for 2 pairs + FREE Metro Manila delivery.\n\n"
        "Message mo lang kami kung interested ka or may tanong ka! 🤙"
    ),
]

# -- Spam filter keywords ------------------------------------------------------
# Comments containing these (case-insensitive) are likely spam -- skip auto-response.

SPAM_KEYWORDS = [
    "scam",
    "fake",
    "bot",
    "visit my page",
    "check my profile",
    "earn money",
    "bitcoin",
    "crypto",
    "dm me for",
    "free iphone",
    "giveaway",
    "click here",
    "bit.ly",
    "tinyurl",
]
