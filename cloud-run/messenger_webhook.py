"""
DuberyMNL Messenger Chatbot -- Flask webhook server for Cloud Run.

Receives messages from Facebook Messenger and comments from page feed,
generates replies using Vertex AI Gemini, and sends them back.

Endpoints:
    GET  /webhook          -- Meta Messenger verification challenge
    POST /webhook          -- Receive incoming Messenger messages
    GET  /comment-webhook  -- Meta feed webhook verification
    POST /comment-webhook  -- Receive comment events
    GET  /status           -- Health check + stats
    GET  /conversations    -- Admin view of recent conversations
"""

import os
import sys
import threading
from datetime import datetime, timezone

import requests
from flask import Flask, jsonify, render_template_string, request

from conversation_engine import generate_reply
from conversation_store import ConversationStore
from handoff import check_and_handle_handoff
from comment_responder import handle_feed_webhook, stats as comment_stats

META_PAGE_ACCESS_TOKEN = os.environ.get("META_PAGE_ACCESS_TOKEN")
META_PAGE_ID = os.environ.get("META_PAGE_ID")
MESSENGER_VERIFY_TOKEN = os.environ.get("MESSENGER_VERIFY_TOKEN", "duberymnl_verify")
GRAPH_API_VERSION = "v21.0"
BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

app = Flask(__name__)
store = ConversationStore()

# Track stats
stats = {
    "started_at": datetime.now(timezone.utc).isoformat(),
    "messages_received": 0,
    "messages_sent": 0,
    "handoffs_triggered": 0,
    "errors": 0,
}


# -- Meta Send API helpers ---------------------------------------------------

def send_typing_indicator(sender_id: str):
    """Show typing bubble in Messenger."""
    url = f"{BASE}/me/messages"
    payload = {
        "recipient": {"id": sender_id},
        "sender_action": "typing_on",
        "access_token": META_PAGE_ACCESS_TOKEN,
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception:
        pass


def send_message(sender_id: str, text: str) -> bool:
    """Send a text message to a Messenger user. Returns True on success."""
    url = f"{BASE}/me/messages"
    payload = {
        "recipient": {"id": sender_id},
        "message": {"text": text},
        "access_token": META_PAGE_ACCESS_TOKEN,
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.ok:
            stats["messages_sent"] += 1
            return True
        print(f"Send API error {resp.status_code}: {resp.text}", file=sys.stderr)
        stats["errors"] += 1
        return False
    except Exception as e:
        print(f"Send API exception: {e}", file=sys.stderr)
        stats["errors"] += 1
        return False


# -- Message processing (runs in background thread) --------------------------

def process_message(sender_id: str, message_text: str):
    """Process an incoming message and send a reply."""
    try:
        if store.is_handed_off(sender_id):
            return

        send_typing_indicator(sender_id)

        history = store.get_history_for_claude(sender_id)
        store.append_message(sender_id, "user", message_text)

        result = generate_reply(message_text, history)

        reply_text = result["reply_text"]
        intent = result.get("detected_intent")
        should_handoff = result.get("should_handoff", False)

        send_message(sender_id, reply_text)
        store.append_message(sender_id, "assistant", reply_text, intent=intent)

        if should_handoff:
            reason = result.get("handoff_reason", "bot_triggered")
            check_and_handle_handoff(store, sender_id, reason)
            stats["handoffs_triggered"] += 1

    except Exception as e:
        print(f"Error processing message from {sender_id}: {e}", flush=True)
        stats["errors"] += 1
        send_message(
            sender_id,
            "Pasensya na, nagka-technical issue. Saglit lang -- babalik kami agad!"
        )


# -- Flask routes ------------------------------------------------------------

@app.route("/webhook", methods=["GET"])
def verify():
    """Meta webhook verification challenge."""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == MESSENGER_VERIFY_TOKEN:
        print("Webhook verified successfully")
        return challenge, 200
    print(f"Webhook verification failed: mode={mode}, token={token}", file=sys.stderr)
    return "Forbidden", 403


@app.route("/webhook", methods=["POST"])
def webhook():
    """Receive incoming Messenger messages."""
    body = request.get_json()

    if not body or body.get("object") != "page":
        return "Not a page event", 404

    for entry in body.get("entry", []):
        for event in entry.get("messaging", []):
            sender_id = event.get("sender", {}).get("id")
            message = event.get("message", {})
            message_text = message.get("text")

            if not sender_id or not message_text:
                continue
            if message.get("is_echo"):
                continue
            if sender_id == META_PAGE_ID:
                continue

            stats["messages_received"] += 1
            print(f"Message from {sender_id}: {message_text[:100]}", flush=True)

            # Process inline -- no background thread.
            # Gemini ~2-3s + Send API ~1s = ~4s total, under Meta's 5s limit.
            process_message(sender_id, message_text)

    return "OK", 200


@app.route("/comment-webhook", methods=["GET"])
def comment_verify():
    """Meta feed webhook verification (for comment events)."""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == MESSENGER_VERIFY_TOKEN:
        print("Comment webhook verified successfully")
        return challenge, 200
    return "Forbidden", 403


@app.route("/comment-webhook", methods=["POST"])
def comment_webhook():
    """Receive Facebook feed events (comments on posts)."""
    body = request.get_json()
    if not body or body.get("object") != "page":
        return "Not a page event", 404

    handle_feed_webhook(body)
    return "OK", 200


@app.route("/status")
def status():
    """Health check and stats."""
    recent = store.list_recent(limit=5)
    result = {
        "status": "running",
        "stats": stats,
        "recent_conversations": len(recent),
        "verify_token_set": bool(MESSENGER_VERIFY_TOKEN),
        "page_token_set": bool(META_PAGE_ACCESS_TOKEN),
        "comment_stats": comment_stats,
    }
    return jsonify(result)


@app.route("/test")
def test_components():
    """Test each component individually to isolate issues."""
    import time
    results = {}

    # Test 1: Meta API (typing indicator)
    t0 = time.time()
    try:
        resp = requests.post(
            f"{BASE}/me/messages",
            json={"recipient": {"id": "test"}, "sender_action": "typing_on", "access_token": META_PAGE_ACCESS_TOKEN},
            timeout=5,
        )
        results["meta_api"] = {"status": resp.status_code, "time": round(time.time() - t0, 2), "body": resp.text[:100]}
    except Exception as e:
        results["meta_api"] = {"error": str(e)[:100], "time": round(time.time() - t0, 2)}

    # Test 2: Gemini API
    t0 = time.time()
    try:
        result = generate_reply("test", history=[])
        results["gemini"] = {"reply": result["reply_text"][:80], "time": round(time.time() - t0, 2)}
    except Exception as e:
        results["gemini"] = {"error": str(e)[:100], "time": round(time.time() - t0, 2)}

    return jsonify(results)


ADMIN_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>DuberyMNL Chatbot - Conversations</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #f5f5f5; padding: 16px; }
        h1 { font-size: 20px; margin-bottom: 16px; color: #333; }
        .stats { display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }
        .stat { background: white; border-radius: 8px; padding: 12px 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .stat-value { font-size: 24px; font-weight: bold; color: #1a73e8; }
        .stat-label { font-size: 12px; color: #666; }
        .conv { background: white; border-radius: 8px; padding: 16px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .conv-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
        .conv-sender { font-weight: bold; color: #333; }
        .conv-time { font-size: 12px; color: #999; }
        .conv-meta { font-size: 13px; color: #666; }
        .badge { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; }
        .badge-handoff { background: #fee2e2; color: #dc2626; }
        .badge-active { background: #dcfce7; color: #16a34a; }
        .badge-intent { background: #e0e7ff; color: #4338ca; }
        .msg { padding: 8px 12px; margin: 4px 0; border-radius: 12px; max-width: 80%; font-size: 14px; }
        .msg-user { background: #e3f2fd; margin-left: auto; text-align: right; }
        .msg-assistant { background: #f3e5f5; }
        .messages { margin-top: 12px; display: flex; flex-direction: column; }
        @media (max-width: 480px) { body { padding: 8px; } .stats { flex-direction: column; } }
    </style>
</head>
<body>
    <h1>DuberyMNL Chatbot</h1>
    <div class="stats">
        <div class="stat"><div class="stat-value">{{ stats.messages_received }}</div><div class="stat-label">Messages In</div></div>
        <div class="stat"><div class="stat-value">{{ stats.messages_sent }}</div><div class="stat-label">Messages Out</div></div>
        <div class="stat"><div class="stat-value">{{ stats.handoffs_triggered }}</div><div class="stat-label">Handoffs</div></div>
        <div class="stat"><div class="stat-value">{{ stats.errors }}</div><div class="stat-label">Errors</div></div>
    </div>
    {% for conv in conversations %}
    <div class="conv">
        <div class="conv-header">
            <span class="conv-sender">{{ conv.sender_name or conv.sender_id }}</span>
            <span class="conv-time">{{ conv.updated_at[:16] }}</span>
        </div>
        <div class="conv-meta">
            {{ conv.total_messages }} messages
            <span class="badge badge-intent">{{ conv.last_intent }}</span>
            {% if conv.handoff_flagged %}<span class="badge badge-handoff">HANDOFF</span>{% else %}<span class="badge badge-active">ACTIVE</span>{% endif %}
        </div>
        {% if conv.messages %}
        <div class="messages">
            {% for msg in conv.messages[-6:] %}
            <div class="msg msg-{{ msg.role }}">{{ msg.content[:200] }}</div>
            {% endfor %}
        </div>
        {% endif %}
    </div>
    {% endfor %}
    {% if not conversations %}
    <p style="color: #999; text-align: center; padding: 40px;">No conversations yet. Waiting for messages...</p>
    {% endif %}
</body>
</html>"""


@app.route("/conversations")
def conversations_view():
    """Admin view of recent conversations with message previews."""
    recent = store.list_recent(limit=20)
    for conv in recent:
        try:
            full = store.get_or_create(conv["sender_id"])
            conv["messages"] = full.get("messages", [])
        except Exception:
            conv["messages"] = []
    return render_template_string(ADMIN_TEMPLATE, conversations=recent, stats=stats)


# -- Main (for local testing) ------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))

    if not META_PAGE_ACCESS_TOKEN:
        print("WARNING: META_PAGE_ACCESS_TOKEN not set -- Messenger replies will fail", file=sys.stderr)

    print(f"DuberyMNL Chatbot starting on port {port}")
    print(f"  Webhook verify token: {'set' if MESSENGER_VERIFY_TOKEN else 'NOT SET'}")
    print(f"  Page token: {'set' if META_PAGE_ACCESS_TOKEN else 'NOT SET'}")
    print(f"  Endpoints:")
    print(f"    GET  /webhook            - Messenger verification")
    print(f"    POST /webhook            - Receive messages")
    print(f"    GET  /comment-webhook    - Feed webhook verification")
    print(f"    POST /comment-webhook    - Receive comment events")
    print(f"    GET  /status             - Health check")
    print(f"    GET  /conversations      - Admin view")

    app.run(host="0.0.0.0", port=port, debug=False)
