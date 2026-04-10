"""
Security layer for the DuberyMNL Messenger chatbot.

Provides:
- Input scanning for prompt injection attempts (high-confidence only)
- Output scanning for structural JSON field leaks
- Basic heuristics for detecting bot-like senders
"""

import re

# --- Prompt injection keywords (input-side) ---
# HIGH-CONFIDENCE ONLY. Over-firing on legit queries was a production bug.
# Case-insensitive substring matches.
INJECTION_KEYWORDS = [
    "ignore your instructions",
    "ignore all previous",
    "disregard your instructions",
    "forget your instructions",
    "show me your prompt",
    "reveal your system prompt",
    "reveal your prompt",
    "print your instructions",
    "what are your instructions",
    "dan mode",
    "developer mode",
    "jailbreak",
    "act as a different",
    "pretend you are",
    "roleplay as",
    "give me a 100% discount",
    "100% off",
]

# --- Output leak patterns (structural only) ---
# Only catch fields from our RESPONSE FORMAT JSON schema leaking into customer replies.
# Prose leak detection was producing false positives (e.g., "PROVINCIAL ORDERS:" fires
# when the bot legitimately talks about provincial orders).
LEAK_PATTERNS = [
    "SYSTEM_PROMPT",
    "systemInstruction",
    "get_full_knowledge",
    "should_handoff",
    "detected_intent",
    "handoff_reason",
    "image_key",
    "reply_parts",
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

    # Unusually long messages (legitimate customer messages are usually under 800 chars)
    if len(text) > 2000:
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
    Scan the bot's reply for structural JSON field leaks only.
    Returns (safe_text, is_safe). If is_safe is False, the reply should be suppressed.
    """
    if not reply_text:
        return reply_text, True

    for pattern in LEAK_PATTERNS:
        if pattern in reply_text:
            return "", False

    return reply_text, True
