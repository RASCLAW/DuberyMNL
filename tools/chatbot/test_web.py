"""
DuberyMNL Chatbot -- Web test interface.

Test the chatbot conversation engine in a Messenger-like UI.
Uses claude --print with the chatbot system prompt.

Usage:
    python tools/chatbot/test_web.py
    Open http://localhost:5003
"""

import json
import subprocess
import sys
from pathlib import Path

from flask import Flask, jsonify, request, render_template_string, send_from_directory

sys.path.insert(0, str(Path(__file__).parent))
from knowledge_base import get_full_knowledge

app = Flask(__name__)

# In-memory conversation history for the test session
conversation_history = []

# Write system prompt to file for claude --system-prompt-file
PROMPT_FILE = Path(__file__).parent.parent.parent / ".tmp" / "chatbot_system_prompt.txt"
PROMPT_FILE.parent.mkdir(parents=True, exist_ok=True)

SYSTEM_PROMPT = f"""You are DuberyMNL's Messenger assistant. You sell polarized sunglasses online in the Philippines.

You're friendly, casual, and helpful -- like a real person running a small online shop. Keep it natural. 95% English, sprinkle Filipino only where it feels right (like "sige", "naman", "po" if they use it first). Don't force Tagalog.

Keep replies short. 1-2 sentences max. Customer is on mobile.

FIRST MESSAGE:
When there is no conversation history (this is the customer's first message), ALWAYS respond with ALL 3 parts below:

Part 1 - Acknowledge what they said in one short line.
Part 2 - Thank them and ask how you can help.
Part 3 - Show the catalog using EXACTLY this format (copy it verbatim, including the [IMG:...] tags):

Check out our lineup:

BANDITS Series
[IMG:bandits-matte-black-card-shot.png]

OUTBACK Series
[IMG:outback-blue-card-shot.png]

RASTA Series
[IMG:rasta-red-card-shot.png]

P699 per pair, P1,200 for 2 pairs (any mix). Free delivery in Metro Manila. COD available!

Which one catches your eye?

IMPORTANT: The [IMG:filename] tags MUST appear exactly as shown above with the square brackets and IMG: prefix. Do not remove the brackets. Do not output just the filename. The system renders these as images.

After the first message, switch to normal short replies. Don't show the catalog again.

PRODUCT IMAGES:
When a customer asks to see a specific product, use [IMG:filename] to show it.
Available: bandits-glossy-black-card-shot.png, bandits-matte-black-card-shot.png, bandits-blue-card-shot.png, bandits-green-card-shot.png, bandits-tortoise-card-shot.png, outback-black-card-shot.png, outback-blue-card-shot.png, outback-green-card-shot.png, outback-red-card-shot.png, rasta-brown-card-shot.png, rasta-red-card-shot.png

MOBILE FORMATTING:
- Assume the customer is on a phone. Small screen.
- Use line breaks between ideas. Don't write a wall of text.
- For lists, use simple format with line breaks:

1. Item one
2. Item two
3. Item three

- Or use bullet-style with dashes:

- Option A
- Option B

- Keep each line short. Max 40-50 characters per line ideally.
- Separate key info with blank lines for readability.

{get_full_knowledge()}

DISCOUNT: DUBERY50 = P50 off. Single becomes P649, bundle becomes P1,150. Only mention if they bring it up.

ORDERING: When they want to order, ask for details one step at a time:
1. Which model + color?
2. Name and delivery address?
3. Phone number?
4. Confirm and done.
Or offer: "You can also order at duberymnl.com with code DUBERY50."

IMAGES: When they ask to see a product, show the hero card photo with [IMG:filename].
These show the full package (sunglasses + box + pouch + cloth + polarization card).
Available: bandits-glossy-black-card-shot.png, bandits-matte-black-card-shot.png, bandits-blue-card-shot.png, bandits-green-card-shot.png, bandits-tortoise-card-shot.png, outback-black-card-shot.png, outback-blue-card-shot.png, outback-green-card-shot.png, outback-red-card-shot.png, rasta-brown-card-shot.png, rasta-red-card-shot.png
Example: "Eto siya! [IMG:outback-blue-card-shot.png]"

PRICING: P699 single, P1,200 bundle (2 pairs any mix). COD, free delivery on bundle.
DELIVERY: Same-day Metro Manila, 1-3 days provincial.

Keep it natural. Short. One thing at a time."""


CLAUDE_PATH = r"C:\Users\RAS\AppData\Roaming\npm\claude.cmd"

HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>DuberyMNL Chatbot Test</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f0f2f5; height: 100vh; display: flex; flex-direction: column; }
        .header { background: #1a1a2e; color: white; padding: 16px 20px; display: flex; align-items: center; gap: 12px; }
        .header .avatar { width: 40px; height: 40px; border-radius: 50%; background: #e74c3c; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 16px; }
        .header .info h2 { font-size: 16px; font-weight: 600; }
        .header .info p { font-size: 12px; opacity: 0.7; }
        .header .badge { margin-left: auto; background: #27ae60; color: white; font-size: 11px; padding: 3px 10px; border-radius: 12px; }
        .messages { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 8px; }
        .msg { max-width: 75%; padding: 10px 14px; border-radius: 18px; font-size: 14px; line-height: 1.4; word-wrap: break-word; animation: fadeIn 0.2s ease; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
        .msg-user { background: #0084ff; color: white; align-self: flex-end; border-bottom-right-radius: 4px; }
        .msg-bot { background: white; color: #1a1a1a; align-self: flex-start; border-bottom-left-radius: 4px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); white-space: pre-line; }
        .msg-bot img { max-width: 200px; border-radius: 12px; margin-top: 8px; display: block; }
        .msg-system { background: transparent; color: #999; align-self: center; font-size: 12px; padding: 4px; }
        .typing { align-self: flex-start; background: white; padding: 12px 18px; border-radius: 18px; border-bottom-left-radius: 4px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); display: none; }
        .typing span { display: inline-block; width: 8px; height: 8px; background: #999; border-radius: 50%; margin: 0 2px; animation: bounce 1.2s infinite; }
        .typing span:nth-child(2) { animation-delay: 0.2s; }
        .typing span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes bounce { 0%, 60%, 100% { transform: translateY(0); } 30% { transform: translateY(-6px); } }
        .input-area { background: white; padding: 12px 16px; display: flex; gap: 10px; border-top: 1px solid #e4e6eb; }
        .input-area input { flex: 1; border: 1px solid #e4e6eb; border-radius: 24px; padding: 10px 16px; font-size: 14px; outline: none; }
        .input-area input:focus { border-color: #0084ff; }
        .input-area button { background: #0084ff; color: white; border: none; border-radius: 50%; width: 40px; height: 40px; cursor: pointer; font-size: 18px; display: flex; align-items: center; justify-content: center; }
        .input-area button:hover { background: #0073e6; }
        .input-area button:disabled { background: #ccc; cursor: not-allowed; }
        .presets { padding: 8px 16px; background: white; border-top: 1px solid #e4e6eb; display: flex; gap: 6px; flex-wrap: wrap; }
        .presets button { background: #e4e6eb; border: none; border-radius: 16px; padding: 6px 14px; font-size: 12px; cursor: pointer; color: #333; }
        .presets button:hover { background: #d4d6db; }
    </style>
</head>
<body>
    <div class="header">
        <div class="avatar">D</div>
        <div class="info">
            <h2>Dubery MNL</h2>
            <p>Chatbot Test Mode</p>
        </div>
        <div class="badge">SONNET</div>
    </div>

    <div class="messages" id="messages">
        <div class="msg msg-system">Test the chatbot. Messages are not sent to Facebook.</div>
    </div>

    <div class="typing" id="typing"><span></span><span></span><span></span></div>

    <div class="presets">
        <button onclick="sendPreset('Magkano po?')">Magkano po?</button>
        <button onclick="sendPreset('What colors do you have?')">Colors?</button>
        <button onclick="sendPreset('May COD ba?')">COD?</button>
        <button onclick="sendPreset('I have a DUBERY50 code')">Discount code</button>
        <button onclick="sendPreset('I want to order')">Order</button>
        <button onclick="sendPreset('Anong difference ng Bandits at Outback?')">Compare</button>
        <button onclick="sendPreset('Pwede ba ireturn?')">Returns?</button>
        <button onclick="sendPreset('Patingin ng Outback Blue')">Show photo</button>
        <button onclick="clearChat()">Clear</button>
    </div>

    <div class="input-area">
        <input type="text" id="input" placeholder="Type a message..." autocomplete="off" />
        <button id="sendBtn" onclick="send()">&#10148;</button>
    </div>

    <script>
        const input = document.getElementById('input');
        const messages = document.getElementById('messages');
        const typing = document.getElementById('typing');
        const sendBtn = document.getElementById('sendBtn');

        input.addEventListener('keydown', e => { if (e.key === 'Enter' && !sendBtn.disabled) send(); });

        function addMessage(text, type) {
            const div = document.createElement('div');
            div.className = 'msg msg-' + type;
            if (type === 'bot') {
                // Parse [IMG:filename] tags
                const parts = text.split(/(\[IMG:[^\]]+\])/g);
                parts.forEach(part => {
                    const imgMatch = part.match(/\[IMG:([^\]]+)\]/);
                    if (imgMatch) {
                        const img = document.createElement('img');
                        img.src = '/product-image/' + imgMatch[1];
                        img.alt = imgMatch[1];
                        div.appendChild(img);
                    } else if (part.trim()) {
                        const span = document.createElement('span');
                        span.textContent = part;
                        div.appendChild(span);
                    }
                });
            } else {
                div.textContent = text;
            }
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
        }

        async function send() {
            const text = input.value.trim();
            if (!text) return;
            input.value = '';
            addMessage(text, 'user');
            sendBtn.disabled = true;
            typing.style.display = 'block';
            messages.scrollTop = messages.scrollHeight;

            try {
                const resp = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: text})
                });
                const data = await resp.json();
                typing.style.display = 'none';
                addMessage(data.reply, 'bot');
            } catch (e) {
                typing.style.display = 'none';
                addMessage('Error: ' + e.message, 'system');
            }
            sendBtn.disabled = false;
            input.focus();
        }

        function sendPreset(text) {
            input.value = text;
            send();
        }

        function clearChat() {
            fetch('/clear', {method: 'POST'});
            messages.innerHTML = '<div class="msg msg-system">Chat cleared. Start fresh.</div>';
        }

        input.focus();
    </script>
</body>
</html>"""


def generate_reply(user_message: str) -> str:
    """Generate a reply using claude --print."""
    # Build conversation context
    history_text = ""
    if conversation_history:
        lines = []
        for msg in conversation_history[-16:]:  # last 16 messages
            role = "Customer" if msg["role"] == "user" else "DuberyMNL"
            lines.append(f"{role}: {msg['content']}")
        history_text = "\n\nCONVERSATION SO FAR:\n" + "\n".join(lines)

    full_prompt = f"{history_text}\n\nCustomer: {user_message}"

    try:
        # Write system prompt to file (avoids command-line length issues)
        PROMPT_FILE.write_text(SYSTEM_PROMPT, encoding="utf-8")

        result = subprocess.run(
            [
                CLAUDE_PATH,
                "--print",
                "--system-prompt-file", str(PROMPT_FILE),
                "--model", "sonnet",
                "--no-session-persistence",
            ],
            input=full_prompt,
            capture_output=True,
            text=True,
            timeout=30,
            encoding="utf-8",
        )

        if result.returncode != 0:
            print(f"claude error: {result.stderr}", file=sys.stderr)
            return "Pasensya na, may technical issue. Saglit lang."

        return result.stdout.strip()

    except subprocess.TimeoutExpired:
        return "Pasensya na, medyo matagal mag-load. Try mo ulit."
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return f"Error: {e}"


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_msg = data.get("message", "").strip()
    if not user_msg:
        return jsonify({"reply": "?"})

    conversation_history.append({"role": "user", "content": user_msg})
    reply = generate_reply(user_msg)
    conversation_history.append({"role": "assistant", "content": reply})

    return jsonify({"reply": reply})


CARDS_DIR = Path(__file__).parent.parent.parent / "dubery-landing" / "assets" / "cards"


@app.route("/product-image/<filename>")
def product_image(filename):
    """Serve product card images."""
    return send_from_directory(str(CARDS_DIR), filename)


@app.route("/clear", methods=["POST"])
def clear():
    conversation_history.clear()
    return jsonify({"status": "cleared"})


if __name__ == "__main__":
    print("DuberyMNL Chatbot Test UI")
    print("Open http://localhost:5003")
    app.run(host="0.0.0.0", port=5003, debug=False)
