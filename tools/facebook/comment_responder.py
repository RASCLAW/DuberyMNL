"""
DuberyMNL Comment Auto-Responder + Auto-DM.

When a user comments on a DuberyMNL Facebook post:
  1. Like the comment (engagement signal)
  2. Reply with a short Taglish response
  3. Send a DM to the commenter with product info + CTA

Designed to be integrated into the chatbot webhook server (messenger_webhook.py)
or run standalone for testing.

Usage:
    # Standalone server (for testing)
    python tools/facebook/comment_responder.py --port 5003

    # Test with a simulated comment event
    python tools/facebook/comment_responder.py --test

Webhook setup:
    Subscribe page to 'feed' webhook field via Graph API.
    Verify endpoint: GET /comment-webhook
    Receive events: POST /comment-webhook
"""

import json
import os
import random
import sys
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_DIR / ".env")

sys.path.insert(0, str(Path(__file__).parent))
from comment_templates import COMMENT_REPLIES, DM_OPENERS, SPAM_KEYWORDS

META_PAGE_ACCESS_TOKEN = os.environ.get("META_PAGE_ACCESS_TOKEN")
META_PAGE_ID = os.environ.get("META_PAGE_ID")
MESSENGER_VERIFY_TOKEN = os.environ.get("MESSENGER_VERIFY_TOKEN", "duberymnl_verify")
GRAPH_API_VERSION = "v21.0"
BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

TMP_DIR = PROJECT_DIR / ".tmp"
DEDUP_FILE = TMP_DIR / "comment_dedup.json"
RESPONSE_LOG = TMP_DIR / "comment_responses.json"
COOLDOWN_HOURS = 24

# Track stats
stats = {
    "started_at": datetime.now(timezone.utc).isoformat(),
    "comments_received": 0,
    "comments_replied": 0,
    "dms_sent": 0,
    "skipped_spam": 0,
    "skipped_dedup": 0,
    "skipped_self": 0,
    "errors": 0,
}


# -- Dedup store ---------------------------------------------------------------

def load_dedup() -> dict:
    """Load the dedup store: {commenter_id: last_responded_iso}."""
    if DEDUP_FILE.exists():
        try:
            return json.loads(DEDUP_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_dedup(store: dict):
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    DEDUP_FILE.write_text(json.dumps(store, indent=2))


def is_on_cooldown(commenter_id: str) -> bool:
    """Check if commenter was DM'd within the last COOLDOWN_HOURS."""
    store = load_dedup()
    last = store.get(commenter_id)
    if not last:
        return False
    try:
        last_dt = datetime.fromisoformat(last)
        return datetime.now(timezone.utc) - last_dt < timedelta(hours=COOLDOWN_HOURS)
    except (ValueError, TypeError):
        return False


def mark_responded(commenter_id: str):
    """Record that we responded to this commenter."""
    store = load_dedup()
    store[commenter_id] = datetime.now(timezone.utc).isoformat()
    # Prune entries older than 7 days
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    store = {
        k: v for k, v in store.items()
        if datetime.fromisoformat(v) > cutoff
    }
    save_dedup(store)


# -- Response log --------------------------------------------------------------

def log_response(commenter_id: str, comment_id: str, comment_text: str, post_id: str):
    """Log the auto-response for analytics."""
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    entries = []
    if RESPONSE_LOG.exists():
        try:
            entries = json.loads(RESPONSE_LOG.read_text())
        except (json.JSONDecodeError, OSError):
            entries = []
    entries.append({
        "commenter_id": commenter_id,
        "comment_id": comment_id,
        "comment_text": comment_text[:200],
        "post_id": post_id,
        "responded_at": datetime.now(timezone.utc).isoformat(),
    })
    # Keep last 500 entries
    if len(entries) > 500:
        entries = entries[-500:]
    RESPONSE_LOG.write_text(json.dumps(entries, indent=2, ensure_ascii=False))


# -- Spam filter ---------------------------------------------------------------

def is_spam(comment_text: str) -> bool:
    """Check if comment text looks like spam."""
    if not comment_text or len(comment_text.strip()) < 3:
        return True  # Too short (emoji-only or empty)
    text_lower = comment_text.lower()
    return any(kw in text_lower for kw in SPAM_KEYWORDS)


# -- Graph API actions ---------------------------------------------------------

def like_comment(comment_id: str) -> bool:
    """Like a comment via Graph API."""
    url = f"{BASE}/{comment_id}/likes"
    try:
        resp = requests.post(url, data={"access_token": META_PAGE_ACCESS_TOKEN}, timeout=10)
        return resp.ok
    except Exception as e:
        print(f"Like failed for {comment_id}: {e}", file=sys.stderr)
        return False


def reply_to_comment(comment_id: str) -> bool:
    """Reply to a comment with a random template."""
    url = f"{BASE}/{comment_id}/comments"
    reply_text = random.choice(COMMENT_REPLIES)
    try:
        resp = requests.post(
            url,
            data={"message": reply_text, "access_token": META_PAGE_ACCESS_TOKEN},
            timeout=10,
        )
        if resp.ok:
            stats["comments_replied"] += 1
            return True
        print(f"Reply failed for {comment_id}: {resp.status_code} {resp.text}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Reply exception for {comment_id}: {e}", file=sys.stderr)
        return False


def send_dm(commenter_id: str, source_context: str = "") -> bool:
    """Send a DM to the commenter via Messenger Send API."""
    url = f"{BASE}/me/messages"
    dm_text = random.choice(DM_OPENERS)
    payload = {
        "recipient": {"id": commenter_id},
        "message": {"text": dm_text},
        "access_token": META_PAGE_ACCESS_TOKEN,
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.ok:
            stats["dms_sent"] += 1
            return True
        print(f"DM failed for {commenter_id}: {resp.status_code} {resp.text}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"DM exception for {commenter_id}: {e}", file=sys.stderr)
        return False


# -- Core processing -----------------------------------------------------------

def process_comment(comment_id: str, commenter_id: str, comment_text: str, post_id: str):
    """Process a single comment: filter, like, reply, DM."""
    stats["comments_received"] += 1

    # Skip own page comments
    if commenter_id == META_PAGE_ID:
        stats["skipped_self"] += 1
        return

    # Skip spam
    if is_spam(comment_text):
        stats["skipped_spam"] += 1
        print(f"  SKIP spam: {comment_id} ({comment_text[:50]})")
        return

    # Skip if on cooldown
    if is_on_cooldown(commenter_id):
        stats["skipped_dedup"] += 1
        print(f"  SKIP dedup: {commenter_id} (responded within {COOLDOWN_HOURS}h)")
        return

    print(f"  Processing comment {comment_id} from {commenter_id}: {comment_text[:80]}")

    # 1. Like the comment
    like_comment(comment_id)

    # 2. Reply to the comment
    reply_to_comment(comment_id)

    # 3. Send DM
    dm_ok = send_dm(commenter_id, source_context=f"comment on post {post_id}")

    if dm_ok:
        # Mark as responded (for dedup)
        mark_responded(commenter_id)
        # Log the interaction
        log_response(commenter_id, comment_id, comment_text, post_id)

        # Store auto-DM context for chatbot (so it knows the customer came from a comment)
        _store_autodm_context(commenter_id, comment_text, post_id)


def _store_autodm_context(commenter_id: str, comment_text: str, post_id: str):
    """Store context so the chatbot knows this customer arrived via auto-DM."""
    conversations_dir = TMP_DIR / "conversations"
    conversations_dir.mkdir(parents=True, exist_ok=True)

    safe_id = commenter_id.replace("/", "_").replace("..", "_")
    context_file = conversations_dir / f"{safe_id}_autodm.json"
    context_file.write_text(json.dumps({
        "source": "auto_dm",
        "post_id": post_id,
        "comment_text": comment_text[:200],
        "sent_at": datetime.now(timezone.utc).isoformat(),
    }, indent=2))


# -- Webhook handler (for integration into messenger_webhook.py) ---------------

def handle_feed_webhook(body: dict):
    """
    Process a Facebook feed webhook event (comments on posts).
    Call this from the main webhook server's POST handler.
    """
    for entry in body.get("entry", []):
        for change in entry.get("changes", []):
            if change.get("field") != "feed":
                continue
            value = change.get("value", {})
            if value.get("item") != "comment":
                continue

            comment_id = value.get("comment_id")
            commenter_id = value.get("from", {}).get("id")
            comment_text = value.get("message", "")
            post_id = value.get("post_id", "")

            if not comment_id or not commenter_id:
                continue

            # Process in background thread
            thread = threading.Thread(
                target=process_comment,
                args=(comment_id, commenter_id, comment_text, post_id),
                daemon=True,
            )
            thread.start()


# -- Standalone server (for testing) -------------------------------------------

def run_standalone(port: int):
    """Run as a standalone Flask server for testing."""
    from flask import Flask, jsonify, request

    app = Flask(__name__)

    @app.route("/comment-webhook", methods=["GET"])
    def verify():
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == MESSENGER_VERIFY_TOKEN:
            return challenge, 200
        return "Forbidden", 403

    @app.route("/comment-webhook", methods=["POST"])
    def webhook():
        body = request.get_json()
        if not body or body.get("object") != "page":
            return "Not a page event", 404
        handle_feed_webhook(body)
        return "OK", 200

    @app.route("/comment-status")
    def status():
        return jsonify({"status": "running", "stats": stats})

    print(f"Comment responder starting on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)


def run_test():
    """Simulate a comment event for local testing."""
    print("Simulating comment event...")
    fake_body = {
        "object": "page",
        "entry": [{
            "changes": [{
                "field": "feed",
                "value": {
                    "item": "comment",
                    "comment_id": "test_comment_001",
                    "from": {"id": "test_user_001", "name": "Test User"},
                    "message": "Wow nice shades! Where can I buy?",
                    "post_id": "test_post_001",
                },
            }],
        }],
    }
    handle_feed_webhook(fake_body)
    time.sleep(2)  # Let background thread finish
    print(f"\nStats: {json.dumps(stats, indent=2)}")


# -- Main ----------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(description="DuberyMNL Comment Auto-Responder")
    parser.add_argument("--port", type=int, default=5003, help="Server port (default: 5003)")
    parser.add_argument("--test", action="store_true", help="Simulate a comment event")
    args = parser.parse_args()

    if not META_PAGE_ACCESS_TOKEN:
        print("ERROR: META_PAGE_ACCESS_TOKEN not set in .env", file=sys.stderr)
        sys.exit(1)

    if args.test:
        run_test()
    else:
        run_standalone(args.port)


if __name__ == "__main__":
    main()
