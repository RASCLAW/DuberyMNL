"""
DuberyMNL Voice Chatbot -- Flask backend.

Browser handles STT (Web Speech API) and TTS (SpeechSynthesis).
This server receives transcribed text, calls claude --print, returns reply text.

Port: 5003
Requires: Chrome browser (Web Speech API support)

Usage:
    python tools/chatbot/voice_server.py
    Open http://localhost:5003 in Chrome
"""

import subprocess
import sys
from pathlib import Path

from flask import Flask, request, jsonify, send_file

# Import knowledge base from existing chatbot
CHATBOT_DIR = Path(__file__).parent
sys.path.insert(0, str(CHATBOT_DIR))
from knowledge_base import get_full_knowledge

app = Flask(__name__)

# In-memory conversation history (resets on server restart)
conversation_history = []

PROJECT_DIR = CHATBOT_DIR.parent.parent

SYSTEM_PROMPT = f"""You are DuberyMNL's voice assistant. You're having a live voice conversation with a customer.

VOICE:
- Always reply in English. You can understand Tagalog and Taglish, but your voice output is English only.
- Warm and direct, like a smart friend who sells shades on the side.
- Keep responses SHORT -- 1-2 sentences max. This is a voice conversation, not a text chat.
- Speak naturally. No bullet points, no numbered lists, no markdown, no formatting.
- NEVER say: "Dear valued customer", "Thank you for reaching out", "I'd be happy to assist", "As an AI"

{get_full_knowledge()}

RULES:
- Always provide accurate pricing. Single: P699. Bundle (2 pairs, any mix): P1,200.
- Never make up shipping times. Say "usually same-day Metro Manila" or "1-3 days provincial."
- If you don't know something, say: "Let me check with the owner, saglit lang."
- When the customer shows buying intent, guide them to provide: name, address, phone, which model and color.
- Keep it conversational. You're talking, not typing.
- Reply with plain text only. No JSON, no markdown, no special formatting.
"""

MAX_HISTORY = 20


def _format_history(messages):
    """Format conversation history for the claude --print prompt."""
    if not messages:
        return ""
    lines = ["CONVERSATION SO FAR:"]
    for msg in messages:
        role = "Customer" if msg["role"] == "user" else "DuberyMNL"
        lines.append(f"{role}: {msg['content']}")
    return "\n".join(lines)


@app.route("/")
def index():
    """Serve the voice chat frontend."""
    return send_file(CHATBOT_DIR / "voice_chat.html")


@app.route("/chat", methods=["POST"])
def chat():
    """Receive transcribed text, call claude --print, return reply."""
    data = request.json
    user_text = data.get("text", "").strip()
    if not user_text:
        return jsonify({"error": "empty message"}), 400

    conversation_history.append({"role": "user", "content": user_text})

    # Build prompt with history
    history_text = _format_history(conversation_history[-MAX_HISTORY:])
    prompt_parts = [SYSTEM_PROMPT]
    if history_text:
        prompt_parts.append(history_text)
    prompt_parts.append(f"Customer: {user_text}")
    prompt_parts.append("Reply naturally in plain text:")

    full_prompt = "\n\n".join(prompt_parts)

    try:
        result = subprocess.run(
            ["claude", "--print", full_prompt],
            cwd=str(PROJECT_DIR),
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            print(f"claude --print failed: {result.stderr}", file=sys.stderr)
            reply = "Pasensya, may technical issue. Saglit lang."
        else:
            reply = result.stdout.strip()
            # If Claude accidentally returned JSON, extract the text
            if reply.startswith("{"):
                import json
                try:
                    parsed = json.loads(reply)
                    reply = parsed.get("reply_text", reply)
                except (json.JSONDecodeError, KeyError):
                    pass

    except subprocess.TimeoutExpired:
        reply = "Pasensya, medyo matagal yung response. Try mo ulit?"
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        reply = "Pasensya, may technical issue. Saglit lang."

    conversation_history.append({"role": "assistant", "content": reply})
    return jsonify({"reply": reply})


@app.route("/reset", methods=["POST"])
def reset():
    """Clear conversation history."""
    conversation_history.clear()
    return jsonify({"status": "ok"})


@app.route("/status")
def status():
    """Health check."""
    return jsonify({
        "status": "running",
        "messages": len(conversation_history),
        "port": 5003,
    })


if __name__ == "__main__":
    print("=" * 50)
    print("  DuberyMNL Voice Assistant")
    print("  http://localhost:5003")
    print("  Open in Chrome (required for speech recognition)")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5003, debug=False)
