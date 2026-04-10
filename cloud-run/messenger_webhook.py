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
import time
from datetime import datetime, timezone

import requests
from flask import Flask, jsonify, render_template_string, request

from conversation_engine import generate_reply
from conversation_store import ConversationStore
from handoff import check_and_handle_handoff
from comment_responder import handle_feed_webhook, stats as comment_stats
from knowledge_base import get_image_url
from security import detect_injection, detect_bot_sender, sanitize_output
from crm_sync import (
    upsert_lead,
    create_order,
    log_status_change,
    infer_status,
    append_message as crm_append_message,
    load_history as crm_load_history,
)

META_PAGE_ACCESS_TOKEN = os.environ.get("META_PAGE_ACCESS_TOKEN")
META_PAGE_ID = os.environ.get("META_PAGE_ID")
MESSENGER_VERIFY_TOKEN = os.environ.get("MESSENGER_VERIFY_TOKEN", "duberymnl_verify")
GRAPH_API_VERSION = "v21.0"
BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

app = Flask(__name__)
store = ConversationStore()

# Message dedup -- skip retries from Meta
_processed_messages = set()

# Track stats
stats = {
    "started_at": datetime.now(timezone.utc).isoformat(),
    "messages_received": 0,
    "messages_sent": 0,
    "messages_deduped": 0,
    "handoffs_triggered": 0,
    "errors": 0,
}


# -- Meta Send API helpers ---------------------------------------------------

def send_sender_action(sender_id: str, action: str):
    """Send a sender_action (typing_on, typing_off, mark_seen) to Messenger."""
    url = f"{BASE}/me/messages"
    payload = {
        "recipient": {"id": sender_id},
        "sender_action": action,
        "access_token": META_PAGE_ACCESS_TOKEN,
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception:
        pass


def send_typing_indicator(sender_id: str):
    """Show typing bubble in Messenger."""
    send_sender_action(sender_id, "typing_on")


def stop_typing_indicator(sender_id: str):
    """Explicitly turn off the typing bubble."""
    send_sender_action(sender_id, "typing_off")


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


# Cache of image URL -> Meta attachment_id (populated lazily)
# Reusable attachments load near-instantly on the user's phone since Meta already has them.
_attachment_cache: dict = {}


def _upload_attachment(image_url: str) -> str | None:
    """Upload an image URL to Meta as a reusable attachment. Returns attachment_id or None."""
    url = f"{BASE}/me/message_attachments"
    payload = {
        "message": {
            "attachment": {
                "type": "image",
                "payload": {"url": image_url, "is_reusable": True},
            }
        },
        "access_token": META_PAGE_ACCESS_TOKEN,
    }
    try:
        resp = requests.post(url, json=payload, timeout=20)
        if resp.ok:
            aid = resp.json().get("attachment_id")
            if aid:
                print(f"Uploaded attachment {aid} for {image_url[:60]}", flush=True)
                return aid
        print(f"Attachment upload error {resp.status_code}: {resp.text[:200]}", file=sys.stderr, flush=True)
        return None
    except Exception as e:
        print(f"Attachment upload exception: {e}", file=sys.stderr, flush=True)
        return None


def send_image(sender_id: str, image_url: str) -> bool:
    """Send an image to a Messenger user. Caches uploads so repeat sends are faster."""
    # First send: upload to Meta to get an attachment_id
    attachment_id = _attachment_cache.get(image_url)
    cache_hit = attachment_id is not None

    if not attachment_id:
        print(f"Image cache MISS, uploading: {image_url[:80]}", flush=True)
        attachment_id = _upload_attachment(image_url)
        if attachment_id:
            _attachment_cache[image_url] = attachment_id
    else:
        print(f"Image cache HIT (aid={attachment_id}): {image_url[:80]}", flush=True)

    url = f"{BASE}/me/messages"
    if attachment_id:
        # Fast path: send by attachment_id (Meta already has the image)
        payload = {
            "recipient": {"id": sender_id},
            "message": {
                "attachment": {
                    "type": "image",
                    "payload": {"attachment_id": attachment_id},
                }
            },
            "access_token": META_PAGE_ACCESS_TOKEN,
        }
    else:
        # Fallback: send by URL (slower, Meta fetches on demand)
        payload = {
            "recipient": {"id": sender_id},
            "message": {
                "attachment": {
                    "type": "image",
                    "payload": {"url": image_url, "is_reusable": True},
                }
            },
            "access_token": META_PAGE_ACCESS_TOKEN,
        }

    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.ok:
            mode = "cached" if cache_hit else "url"
            print(f"Image sent ({mode}): {resp.json()}", flush=True)
            return True
        print(f"Send image error {resp.status_code}: {resp.text[:200]}", file=sys.stderr, flush=True)
        return False
    except Exception as e:
        print(f"Send image exception: {e}", file=sys.stderr, flush=True)
        return False


def warm_attachment_cache():
    """Pre-upload all known images to Meta at startup. Runs in background thread."""
    try:
        from knowledge_base import ALL_IMAGES
        print(f"Warming attachment cache for {len(ALL_IMAGES)} images...", flush=True)
        uploaded = 0
        for key, image_url in ALL_IMAGES.items():
            if image_url in _attachment_cache:
                continue
            aid = _upload_attachment(image_url)
            if aid:
                _attachment_cache[image_url] = aid
                uploaded += 1
        print(f"Attachment cache warmed: {uploaded}/{len(ALL_IMAGES)} uploaded", flush=True)
    except Exception as e:
        print(f"Warmup error: {e}", file=sys.stderr, flush=True)


# -- Message processing -------------------------------------------------------

def _human_delay(text: str) -> float:
    """
    Calculate a natural 'thinking + typing' delay for a reply.
    Base reading time + per-char typing, capped so customers don't wait too long.
    """
    base = 1.2  # reading/thinking time
    per_char = 0.025  # ~25ms per character (fast typing)
    delay = base + per_char * len(text or "")
    return min(max(delay, 1.5), 4.5)


def process_message(sender_id: str, message_text: str):
    """Process an incoming message and send a reply."""
    try:
        if store.is_handed_off(sender_id):
            # Sender was flagged earlier -- stay silent
            return

        # --- Security gate 1: prompt injection ---
        injection_reason = detect_injection(message_text)
        if injection_reason:
            print(f"Injection attempt from {sender_id}: {injection_reason}", flush=True)
            store.append_message(sender_id, "user", message_text)
            crm_append_message(sender_id, "user", message_text)
            check_and_handle_handoff(store, sender_id, "prompt_injection")
            return

        # --- Security gate 2: bot-like sender ---
        bot_reason = detect_bot_sender(message_text)
        if bot_reason:
            print(f"Bot-like sender {sender_id}: {bot_reason}", flush=True)
            store.append_message(sender_id, "user", message_text)
            crm_append_message(sender_id, "user", message_text)
            check_and_handle_handoff(store, sender_id, "bot_suspected")
            return

        # Cold-start recovery: if this sender has no in-memory history,
        # try to load their past conversation from the CRM sheet.
        conv = store.get_or_create(sender_id)
        if not conv.get("messages"):
            loaded = crm_load_history(sender_id, limit=20)
            if loaded:
                print(f"Loaded {len(loaded)} messages from CRM for {sender_id}", flush=True)
                for m in loaded:
                    store.append_message(sender_id, m["role"], m["content"])

        history = store.get_history_for_claude(sender_id)
        store.append_message(sender_id, "user", message_text)
        crm_append_message(sender_id, "user", message_text)

        # Show typing indicator immediately so the customer knows we're responding
        send_typing_indicator(sender_id)

        result = generate_reply(message_text, history)

        reply_text = result.get("reply_text", "")
        reply_parts = result.get("reply_parts") or []
        intent = result.get("detected_intent")
        should_handoff = result.get("should_handoff", False)

        # --- Security gate 3: output leak scan ---
        # Check each reply part AND the main reply_text for system prompt leaks.
        # If anything looks like a leak, suppress the whole reply and flag.
        leak_detected = False
        _, text_safe = sanitize_output(reply_text)
        if not text_safe:
            leak_detected = True
        for part in reply_parts:
            _, part_safe = sanitize_output(part)
            if not part_safe:
                leak_detected = True
                break
        if leak_detected:
            print(f"Output leak detected for {sender_id} -- suppressing reply", flush=True)
            stop_typing_indicator(sender_id)
            check_and_handle_handoff(store, sender_id, "prompt_injection")
            return

        # Natural pause before sending -- makes the bot feel human, not instant
        first_text = reply_parts[0] if reply_parts else reply_text
        delay = _human_delay(first_text)
        time.sleep(delay)

        # Multi-part messages: send each as a separate bubble with natural typing delays
        # Fallback to reply_text if reply_parts is empty
        if reply_parts:
            for i, part in enumerate(reply_parts):
                if not part or not part.strip():
                    continue
                send_message(sender_id, part.strip())
                # Natural pause between parts so they arrive like a human typing
                if i < len(reply_parts) - 1:
                    next_part = reply_parts[i + 1]
                    send_typing_indicator(sender_id)
                    time.sleep(_human_delay(next_part) * 0.6)
            stored_text = "\n".join(p.strip() for p in reply_parts if p and p.strip())
        else:
            send_message(sender_id, reply_text)
            stored_text = reply_text

        # Send product image if Gemini included one
        image_key = result.get("image_key")
        if image_key:
            image_url = get_image_url(image_key)
            if image_url:
                send_image(sender_id, image_url)

        # Explicitly stop typing indicator after all sends complete
        stop_typing_indicator(sender_id)

        store.append_message(sender_id, "assistant", stored_text, intent=intent)
        crm_append_message(sender_id, "assistant", stored_text, intent=intent or "")

        # --- CRM sync ---
        # Upsert lead row with any extracted details, log status changes.
        # All errors are swallowed so sync failures never block customer replies.
        try:
            extracted = result.get("extracted") or {}
            conv = store.get_or_create(sender_id)
            message_count = conv["metadata"].get("total_messages", 0)
            previous_status = conv["metadata"].get("lead_status", "Cold")

            new_status = infer_status(
                message_count=message_count,
                has_name=bool(extracted.get("name")),
                has_phone=bool(extracted.get("phone")),
                has_address=bool(extracted.get("address")),
                asked_pricing=bool(extracted.get("asked_pricing")),
                asked_product=bool(extracted.get("asked_product")),
                order_complete=bool(extracted.get("order_complete")),
            )

            upsert_lead(
                lead_id=sender_id,
                name=extracted.get("name") or "",
                phone=extracted.get("phone") or "",
                address=extracted.get("address") or "",
                landmarks=extracted.get("landmarks") or "",
                model_interest=extracted.get("model_interest") or "",
                status=new_status,
            )

            if new_status != previous_status:
                conv["metadata"]["lead_status"] = new_status
                log_status_change(sender_id, previous_status, new_status, f"intent:{intent}")

            # If this turn completed an order, create an order row
            if extracted.get("order_complete"):
                if not conv["metadata"].get("order_recorded"):
                    create_order(
                        lead_id=sender_id,
                        items=extracted.get("order_items") or "",
                        total=extracted.get("order_total") or 0,
                        discount_code=extracted.get("discount_code") or "",
                        payment_method=extracted.get("payment_method") or "COD",
                        delivery_preference=extracted.get("delivery_preference") or "",
                        delivery_time=extracted.get("delivery_time") or "",
                    )
                    conv["metadata"]["order_recorded"] = True
        except Exception as e:
            print(f"CRM sync error (non-fatal): {e}", file=sys.stderr, flush=True)

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

            # Dedup -- Meta retries the same message on timeout
            mid = message.get("mid", "")
            if mid in _processed_messages:
                stats["messages_deduped"] += 1
                continue
            if mid:
                _processed_messages.add(mid)
                # Keep set small -- only need recent messages
                if len(_processed_messages) > 500:
                    _processed_messages.clear()

            stats["messages_received"] += 1
            print(f"Message from {sender_id}: {message_text[:100]}", flush=True)

            try:
                process_message(sender_id, message_text)
            except Exception as e:
                print(f"process_message crashed: {e}", flush=True)
                stats["errors"] += 1

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


@app.route("/backfill-crm", methods=["POST", "GET"])
def backfill_crm():
    """
    Backfill the CRM sheet from all in-memory conversations.
    For each conversation, runs the last user message through Gemini to extract
    customer details, then upserts the lead row.
    """
    results = {"scanned": 0, "upserted": 0, "failed": 0, "orders": 0}

    recent = store.list_recent(limit=200)
    for summary in recent:
        sender_id = summary["sender_id"]
        try:
            conv = store.get_or_create(sender_id)
            messages = conv.get("messages", [])
            if not messages:
                continue
            results["scanned"] += 1

            # Find the last user message
            last_user_msg = None
            for m in reversed(messages):
                if m["role"] == "user":
                    last_user_msg = m["content"]
                    break
            if not last_user_msg:
                continue

            # Run through Gemini to extract details from full history
            history = messages[:-1] if messages[-1]["role"] == "user" else messages
            result = generate_reply(last_user_msg, history)
            extracted = result.get("extracted") or {}

            # Score
            new_status = infer_status(
                message_count=len(messages),
                has_name=bool(extracted.get("name")),
                has_phone=bool(extracted.get("phone")),
                has_address=bool(extracted.get("address")),
                asked_pricing=bool(extracted.get("asked_pricing")),
                asked_product=bool(extracted.get("asked_product")),
                order_complete=bool(extracted.get("order_complete")),
            )

            ok = upsert_lead(
                lead_id=sender_id,
                name=extracted.get("name") or "",
                phone=extracted.get("phone") or "",
                address=extracted.get("address") or "",
                landmarks=extracted.get("landmarks") or "",
                model_interest=extracted.get("model_interest") or "",
                status=new_status,
                notes=f"Backfilled from {len(messages)} messages",
            )
            if ok:
                results["upserted"] += 1
                conv["metadata"]["lead_status"] = new_status
            else:
                results["failed"] += 1

            if extracted.get("order_complete") and not conv["metadata"].get("order_recorded"):
                create_order(
                    lead_id=sender_id,
                    items=extracted.get("order_items") or "",
                    total=extracted.get("order_total") or 0,
                    discount_code=extracted.get("discount_code") or "",
                    payment_method=extracted.get("payment_method") or "COD",
                    delivery_preference=extracted.get("delivery_preference") or "",
                    delivery_time=extracted.get("delivery_time") or "",
                )
                conv["metadata"]["order_recorded"] = True
                results["orders"] += 1
        except Exception as e:
            print(f"Backfill failed for {sender_id}: {e}", file=sys.stderr, flush=True)
            results["failed"] += 1

    return jsonify(results)


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


# -- Startup warmup ----------------------------------------------------------
# Run at module load so gunicorn workers warm the cache before accepting traffic.
# Takes ~30-60s but eliminates first-send loading delays for all 48 images.

if META_PAGE_ACCESS_TOKEN:
    try:
        warm_attachment_cache()
    except Exception as e:
        print(f"Startup warmup failed: {e}", file=sys.stderr, flush=True)


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
