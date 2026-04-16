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


# --- Complaint / trust-objection keywords (customer-side) ------------------
# Catches the "scam/burned before/going elsewhere" signals that should trigger
# a handoff instead of another template reply. Triage surfaces RA faster when
# the bot is about to lose a conversation on trust grounds.
# Match is case-insensitive substring. Phrases stay permissive (PH shorthand,
# typos).
COMPLAINT_KEYWORDS = [
    # Trust / scam
    "naloko",
    "niloko",
    "loko lang",
    "scam",
    "scammer",
    "panloloko",
    "panlolok",
    "nandaya",
    "niloloko",
    # "Been burned before" signals
    "2beses",
    "2 beses",
    "dalawang beses",
    "2x naloko",
    "2x na",
    "hindi na ako",
    "ayaw ko na",
    "ayoko na",
    "takot ako",
    # Walking-away / competitor deflection
    "try ko na lang sa",
    "try ko nlang sa",
    "sa tiktok",
    "sa ticktook",
    "sa ticktok",
    "sa shopee",
    "sa lazada",
    "order na lang ako sa",
    "order nlang ako sa",
    # Direct complaint
    "reklamo",
    "magrereklamo",
    "mag-reklamo",
    "hindi tama",
    "mali yung",
    "sira yung",
    "sira ang",
]


def detect_complaint(text: str) -> str | None:
    """Return the matched complaint keyword if the customer's message looks
    like a trust/scam/complaint/walking-away signal, else None.

    Runs BEFORE Gemini so we skip the template reply and go straight to
    handoff. Saves tokens and prevents the bot from re-firing the same
    policy paragraph at a frustrated customer."""
    if not text:
        return None
    lower = text.lower()
    for kw in COMPLAINT_KEYWORDS:
        if kw in lower:
            return kw
    return None


# --- Bot-reply categorization (for repetition-guard handoff) ---------------
# Not a true semantic classifier -- just a presence-of-key-phrase signature.
# The goal is to notice when the bot is saying the same THING three replies
# in a row (same policy + same ask) even if the wording varies.
_SALES_TEMPLATE_MARKER = "mode of payments"
_QR_MARKERS = ("qr", "instapay", "gcash qr")


def categorize_reply(reply_text: str) -> str:
    """Return a coarse theme signature for a bot reply. Replies with the same
    signature across 3 consecutive turns indicate a loop -- the bot is stuck
    saying the same thing to a customer who isn't converting.

    Returns a pipe-joined, sorted string like 'ask_model|cod_metro|prepay'.
    Empty/other replies return 'other'.
    """
    if not reply_text:
        return "other"
    lower = reply_text.lower()

    # First-contact sales template has its own signature -- if the bot sends
    # this 3x in a row, something is badly wrong (customer is re-asking
    # pricing every turn). Still flaggable.
    if _SALES_TEMPLATE_MARKER in lower and "free shipping" in lower:
        return "sales_template"

    tags = []
    if any(w in lower for w in ("prepayment", "prepaid", "pay first", "payment first", "prepay")):
        tags.append("prepay")
    if "metro manila" in lower and ("cod" in lower or "cash on delivery" in lower):
        tags.append("cod_metro")
    if any(w in lower for w in _QR_MARKERS):
        tags.append("qr")
    if ("which model" in lower or "which color" in lower
            or "model and color" in lower or "model+color" in lower
            or "what model" in lower):
        tags.append("ask_model")
    if "order 2" in lower or "2 or more pairs" in lower or "2+ pairs" in lower:
        tags.append("promo_2plus")

    return "|".join(sorted(tags)) if tags else "other"


# --- Policy "one-shot" enforcement -----------------------------------------
# DuberyMNL has a small set of non-negotiable policies. The bot's job is to
# explain each one ONCE, then shut up. If the customer pushes back on a
# policy already delivered, the bot must not re-explain -- RA takes over.
# This is the "disciplined employee" rule: policies aren't re-negotiated in
# DMs, and the bot recognizing that is what separates it from a retry-loop
# chatbot.

# Each policy is a self-contained recognizer: given bot text, does the bot
# appear to be delivering this policy right now? Given customer text, is the
# customer pushing back on it?

POLICY_DEFINITIONS = {
    "prepay_provincial": {
        "label": "Provincial orders require prepayment; COD is Metro Manila only",
        "delivered_when_all": [
            # At least one "prepay" phrasing...
            ("prepayment", "prepay", "pay first", "payment first", "prepaid"),
            # ...AND a provincial/Metro-Manila context cue so we don't
            # stamp the policy just because "prepaid" appears in an
            # unrelated sentence.
            ("provincial", "metro manila", "outside metro", "province"),
        ],
        # Customer saying any of these AFTER policy delivered = pushback.
        # PH shorthand included ("tsaka", "staka", "narcve", "bago magbayad").
        "pushback_keywords": (
            "cod",
            "cash on delivery",
            "bago magbayad",
            "bago ako magbayad",
            "bgo ako",
            "tsaka nlang",
            "tsaka na lang",
            "staka nlang",
            "staka na lang",
            "pagdating",
            "pag dumating",
            "pag dating",
            "pay on delivery",
            "pay upon",
            "pay when",
            "receive first",
            "narcve",
            "narcv",
            "narecv",
            "narecve",
            "tsaka ko na lang",
            "tsaka na lng",
            "pera mo",
            "pera sa gcash mo",
            "pera sa cgash mo",
        ),
    },
    "no_discount": {
        "label": "No active discount codes; 2+ pairs free shipping is the promo",
        "delivered_when_all": [
            (
                "no active discount",
                "don't have any active discount",
                "do not have any active discount",
                "code is no longer active",
                "no discount codes",
                "dubery50 is retired",
            ),
        ],
        "pushback_keywords": (
            "dubery50",
            "discount code",
            "promo code",
            "may promo po",
            "may promo ba",
            "may discount",
            "tawad",
            "pababa naman",
            "pwede pababa",
            "bawas naman",
            "bawas po",
        ),
    },
}


def _all_groups_match(text: str, groups) -> bool:
    """True iff text contains at least one phrase from every group."""
    for group in groups:
        if not any(phrase in text for phrase in group):
            return False
    return True


def extract_policies_from_reply(reply_text: str) -> list:
    """Return a list of policy IDs the bot appears to be delivering in this
    reply. Caller uses the list to stamp the conversation so subsequent
    customer pushback triggers handoff instead of a re-explain loop."""
    if not reply_text:
        return []
    lower = reply_text.lower()
    hits = []
    for policy_id, spec in POLICY_DEFINITIONS.items():
        if _all_groups_match(lower, spec["delivered_when_all"]):
            hits.append(policy_id)
    return hits


def detect_policy_pushback(customer_text: str, policies_delivered: list) -> str | None:
    """Given a customer message and the list of policies already delivered
    to that customer, return the policy_id the customer is pushing back on,
    or None if the message isn't policy pushback.

    If no policies have been delivered yet, returns None -- first mention of
    the topic is not pushback, it's an initial question."""
    if not customer_text or not policies_delivered:
        return None
    lower = customer_text.lower()
    for policy_id in policies_delivered:
        spec = POLICY_DEFINITIONS.get(policy_id)
        if not spec:
            continue
        for kw in spec["pushback_keywords"]:
            if kw in lower:
                return policy_id
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
