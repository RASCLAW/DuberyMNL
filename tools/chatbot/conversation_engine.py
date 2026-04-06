"""
Conversation engine for DuberyMNL Messenger chatbot.

Uses `claude --print` subprocess (Max plan quota) to generate replies.
Clean interface so Anthropic SDK can be swapped in later.

Usage:
    from conversation_engine import generate_reply
    result = generate_reply("Magkano po?", history=[])
    print(result["reply_text"])
"""

import json
import subprocess
import sys
from pathlib import Path

from knowledge_base import get_full_knowledge

PROJECT_DIR = Path(__file__).parent.parent.parent

SYSTEM_PROMPT = f"""You are DuberyMNL's customer-facing Messenger assistant.

VOICE:
- Match the customer's language. If they message in Tagalog, reply in Tagalog. English -> English. Taglish -> Taglish.
- Warm and direct, like a smart friend who sells shades on the side. Not a corporate chatbot.
- Use "po" when the customer uses it, skip it when they don't.
- Short messages: 2-3 sentences max per reply. Messenger is chat, not email.
- OK to use common Filipino expressions: "uy", "sige", "noted", "ayos"
- NEVER say: "Dear valued customer", "Thank you for reaching out", "I'd be happy to assist", "As an AI"

{get_full_knowledge()}

RULES:
- Always provide accurate pricing. Single: P699. Bundle (2 pairs, any mix): P1,200.
- Never make up shipping times. Say "usually same-day Metro Manila" or "1-3 days provincial."
- If you don't know something, say so: "Let me check with the owner -- saglit lang."
- When the customer shows buying intent, guide them to provide: name, address, phone, variant(s).
- Once order info is complete, confirm the details back and say you'll connect them with the owner for final confirmation.
- Keep replies under 300 characters when possible. Break long info into multiple short messages if needed.
- No emojis unless the customer uses them first.
- If a customer mentions a discount code (like DUBERY50), acknowledge it: "Nice, may P50 off ka with that code!" Apply it to the order total.
- If the customer seems hesitant on price, you can mention DUBERY50 exists: "We have a code DUBERY50 for P50 off if that helps!"

AUTO-DM CONTEXT:
- Some customers arrive via auto-DM (we sent them a message after they commented on a post).
- If the conversation starts with our auto-DM message, the customer didn't initiate -- they commented on a post and we reached out.
- Be extra warm and natural. Don't repeat what was in the auto-DM. Pick up where it left off.
- If they reply to the auto-DM, treat it as normal interest and guide them through the catalog/ordering flow.

RESPONSE FORMAT:
You must respond with valid JSON only. No other text before or after. Use this exact structure:
{{
  "reply_text": "Your reply to the customer",
  "should_handoff": false,
  "handoff_reason": null,
  "detected_intent": "inquiry",
  "confidence": 0.9
}}

Valid intents: "greeting", "inquiry", "order", "complaint", "chitchat", "unknown"
Set should_handoff to true when:
- Customer explicitly asks for a human / the owner
- You detect a complaint or frustration
- Order info is complete (name + address + phone + variant collected)
- You're unsure how to respond (confidence < 0.5)
- Customer asks something outside your knowledge
"""


def _format_history(messages: list) -> str:
    """Format conversation history for the claude --print prompt."""
    if not messages:
        return ""
    lines = ["CONVERSATION SO FAR:"]
    for msg in messages:
        role = "Customer" if msg["role"] == "user" else "DuberyMNL Bot"
        lines.append(f"{role}: {msg['content']}")
    return "\n".join(lines)


def generate_reply(user_message: str, history: list = None) -> dict:
    """
    Generate a reply using claude --print.

    Args:
        user_message: The customer's message
        history: List of prior messages [{"role": "user"|"assistant", "content": "..."}]

    Returns:
        dict with keys: reply_text, should_handoff, handoff_reason, detected_intent, confidence
    """
    if history is None:
        history = []

    history_text = _format_history(history)

    prompt_parts = [SYSTEM_PROMPT]
    if history_text:
        prompt_parts.append(history_text)
    prompt_parts.append(f"Customer: {user_message}")
    prompt_parts.append("Respond with the JSON object only:")

    full_prompt = "\n\n".join(prompt_parts)

    try:
        result = subprocess.run(
            ["claude", "--print", full_prompt],
            cwd=str(PROJECT_DIR),
            capture_output=True,
            text=True,
            timeout=30,
        )

        output = result.stdout.strip()
        if result.returncode != 0:
            print(f"claude --print failed: {result.stderr}", file=sys.stderr)
            return _fallback_response()

        # Extract JSON from the output (claude may add surrounding text)
        parsed = _extract_json(output)
        if parsed:
            # Validate required fields
            parsed.setdefault("reply_text", "Pasensya na, may technical issue. Saglit lang.")
            parsed.setdefault("should_handoff", False)
            parsed.setdefault("handoff_reason", None)
            parsed.setdefault("detected_intent", "unknown")
            parsed.setdefault("confidence", 0.5)
            return parsed

        # If JSON extraction failed, treat the whole output as a plain reply
        print(f"Could not extract JSON from claude output, using raw text", file=sys.stderr)
        return {
            "reply_text": output[:500] if output else "Pasensya na, may technical issue. Saglit lang.",
            "should_handoff": False,
            "handoff_reason": None,
            "detected_intent": "unknown",
            "confidence": 0.5,
        }

    except subprocess.TimeoutExpired:
        print("claude --print timed out after 30s", file=sys.stderr)
        return _fallback_response()
    except Exception as e:
        print(f"conversation_engine error: {e}", file=sys.stderr)
        return _fallback_response()


def _extract_json(text: str) -> dict | None:
    """Extract the first JSON object from text."""
    # Try the whole string first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Find JSON boundaries
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass
    return None


def _fallback_response() -> dict:
    """Return a safe fallback when Claude fails."""
    return {
        "reply_text": "Pasensya na, nagka-technical issue. Saglit lang -- babalik kami agad!",
        "should_handoff": True,
        "handoff_reason": "technical_failure",
        "detected_intent": "unknown",
        "confidence": 0.0,
    }
