"""
Conversation engine for DuberyMNL Messenger chatbot.

Uses Vertex AI Gemini 2.5 Flash via REST API for response generation.
Uses direct HTTP calls instead of the google-genai SDK to avoid
initialization hangs on Cloud Run.

Usage:
    from conversation_engine import generate_reply
    result = generate_reply("Magkano po?", history=[])
    print(result["reply_text"])
"""

import json
import sys

import google.auth
import google.auth.transport.requests
import requests

from knowledge_base import get_full_knowledge

MODEL = "gemini-2.5-flash"
PROJECT = "dubery"
LOCATION = "global"
API_URL = f"https://aiplatform.googleapis.com/v1/projects/{PROJECT}/locations/{LOCATION}/publishers/google/models/{MODEL}:generateContent"

# Cache credentials
_credentials = None


def _get_access_token() -> str:
    """Get a valid access token via ADC (works locally and on Cloud Run)."""
    global _credentials
    if _credentials is None:
        _credentials, _ = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
    _credentials.refresh(google.auth.transport.requests.Request())
    return _credentials.token


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


def generate_reply(user_message: str, history: list = None) -> dict:
    """
    Generate a reply using Vertex AI Gemini via REST API.

    Args:
        user_message: The customer's message
        history: List of prior messages [{"role": "user"|"assistant", "content": "..."}]

    Returns:
        dict with keys: reply_text, should_handoff, handoff_reason, detected_intent, confidence
    """
    if history is None:
        history = []

    # Build multi-turn conversation
    contents = []
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})
    contents.append({"role": "user", "parts": [{"text": user_message}]})

    payload = {
        "contents": contents,
        "systemInstruction": {
            "parts": [{"text": SYSTEM_PROMPT}]
        },
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 500,
            "responseMimeType": "application/json",
        },
    }

    try:
        token = _get_access_token()
        print(f"Calling Gemini {MODEL}...", flush=True)

        resp = requests.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=15,
        )

        if not resp.ok:
            print(f"Gemini API error {resp.status_code}: {resp.text[:200]}", file=sys.stderr, flush=True)
            return _fallback_response()

        data = resp.json()
        output = ""
        for candidate in data.get("candidates", []):
            for part in candidate.get("content", {}).get("parts", []):
                if "text" in part:
                    output += part["text"]

        output = output.strip()
        if not output:
            print("Gemini returned empty response", file=sys.stderr, flush=True)
            return _fallback_response()

        print(f"Gemini replied: {output[:100]}...", flush=True)

        parsed = _extract_json(output)
        if parsed:
            parsed.setdefault("reply_text", "Pasensya na, may technical issue. Saglit lang.")
            parsed.setdefault("should_handoff", False)
            parsed.setdefault("handoff_reason", None)
            parsed.setdefault("detected_intent", "unknown")
            parsed.setdefault("confidence", 0.5)
            return parsed

        print("Could not extract JSON from Gemini output, using raw text", file=sys.stderr, flush=True)
        return {
            "reply_text": output[:500],
            "should_handoff": False,
            "handoff_reason": None,
            "detected_intent": "unknown",
            "confidence": 0.5,
        }

    except requests.Timeout:
        print("Gemini API timed out after 15s", file=sys.stderr, flush=True)
        return _fallback_response()
    except Exception as e:
        print(f"conversation_engine error: {e}", file=sys.stderr, flush=True)
        return _fallback_response()


def _extract_json(text: str) -> dict | None:
    """Extract the first JSON object from text."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass
    return None


def _fallback_response() -> dict:
    """Return a safe fallback when Gemini fails."""
    return {
        "reply_text": "Pasensya na, nagka-technical issue. Saglit lang -- babalik kami agad!",
        "should_handoff": True,
        "handoff_reason": "technical_failure",
        "detected_intent": "unknown",
        "confidence": 0.0,
    }
