"""
Security layer for the DuberyMNL Messenger chatbot.

Provides:
- Input scanning for prompt injection attempts
- Output scanning for system prompt leaks
- Basic heuristics for detecting bot-like senders
"""

import re

# --- Prompt injection keywords (input-side) ---
# Case-insensitive substring matches. Triggers a "suspicious" flag.
INJECTION_KEYWORDS = [
    "ignore your instructions",
    "ignore previous instructions",
    "ignore all previous",
    "disregard your instructions",
    "forget your instructions",
    "forget previous instructions",
    "your system prompt",
    "show me your prompt",
    "reveal your prompt",
    "print your instructions",
    "repeat your instructions",
    "what are your instructions",
    "you are now",
    "act as",
    "pretend you are",
    "pretend to be",
    "roleplay as",
    "new instructions:",
    "new task:",
    "dan mode",
    "jailbreak",
    "developer mode",
    "admin mode",
    "system:",
    "system>",
    "<system>",
    "###",
    "[[",
    "```system",
    "prompt injection",
    "reveal your rules",
    "bypass your",
    "override your",
    "give me a 100% discount",
    "free shipping forever",
    "100% off",
]

# --- System prompt leakage patterns (output-side) ---
# If the bot's reply contains these, something's wrong -- suppress and flag.
LEAK_PATTERNS = [
    "SYSTEM_PROMPT",
    "VOICE:",
    "FORMATTING:",
    "ORDER FLOW:",
    "HANDOFF RULES:",
    "IMAGE RULES:",
    "PROVINCIAL ORDERS:",
    "AUTO-DM CONTEXT:",
    "RESPONSE FORMAT:",
    "should_handoff",
    "detected_intent",
    "reply_parts",
    "image_key",
    "DUBERY50 is P50 off first order",
    "get_full_knowledge",
]

# --- Bot-like sender heuristics ---
URL_ONLY_RE = re.compile(r"^https?://\S+$")
JSON_LIKE_RE = re.compile(r"^\s*[\{\[].*[\}\]]\s*$", re.DOTALL)


def detect_injection(text: str) -> str | None:
    """
    Check if the user's message looks like a prompt injection attempt.
    Returns a reason string if suspicious, None otherwise.
    """
    if not text:
        return None
    lower = text.lower()

    for keyword in INJECTION_KEYWORDS:
        if keyword in lower:
            return f"injection_keyword:{keyword}"

    # Unusually long messages (legitimate customer messages are usually under 300 chars)
    if len(text) > 800:
        return "message_too_long"

    return None


def detect_bot_sender(text: str) -> str | None:
    """
    Check if the sender looks like another bot.
    Returns a reason string if suspicious, None otherwise.
    """
    if not text:
        return None
    stripped = text.strip()

    # Pure URL with no other content
    if URL_ONLY_RE.match(stripped):
        return "url_only"

    # JSON/structured format
    if JSON_LIKE_RE.match(stripped) and len(stripped) > 20:
        return "json_format"

    # All caps spam (>20 chars, >80% uppercase)
    if len(stripped) > 20:
        letters = [c for c in stripped if c.isalpha()]
        if letters and sum(1 for c in letters if c.isupper()) / len(letters) > 0.8:
            return "all_caps"

    return None


def sanitize_output(reply_text: str) -> tuple[str, bool]:
    """
    Scan the bot's reply for system prompt leaks.
    Returns (safe_text, is_safe). If is_safe is False, the reply should be suppressed.
    """
    if not reply_text:
        return reply_text, True

    for pattern in LEAK_PATTERNS:
        if pattern in reply_text:
            return "", False

    return reply_text, True
