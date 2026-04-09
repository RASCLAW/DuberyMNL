"""
DuberyMNL Comment Auto-Responder + Auto-DM.

When a user comments on a DuberyMNL Facebook post:
  1. Like the comment (engagement signal)
  2. Reply with a short Taglish response
  3. Send a DM to the commenter with product info + CTA

Integrated into messenger_webhook.py as the /comment-webhook handler.
"""

import os
import random
import sys
import threading
from datetime import datetime, timedelta, timezone

import requests

from comment_templates import COMMENT_REPLIES, DM_OPENERS, SPAM_KEYWORDS

META_PAGE_ACCESS_TOKEN = os.environ.get("META_PAGE_ACCESS_TOKEN")
META_PAGE_ID = os.environ.get("META_PAGE_ID")
GRAPH_API_VERSION = "v21.0"
BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

COOLDOWN_HOURS = 24

# In-memory dedup store: {commenter_id: last_responded_iso}
_dedup_store = {}
_dedup_lock = threading.Lock()

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


# -- Dedup (in-memory) --------------------------------------------------------

def is_on_cooldown(commenter_id: str) -> bool:
    """Check if commenter was DM'd within the last COOLDOWN_HOURS."""
    with _dedup_lock:
        last = _dedup_store.get(commenter_id)
    if not last:
        return False
    try:
        last_dt = datetime.fromisoformat(last)
        return datetime.now(timezone.utc) - last_dt < timedelta(hours=COOLDOWN_HOURS)
    except (ValueError, TypeError):
        return False


def mark_responded(commenter_id: str):
    """Record that we responded to this commenter."""
    with _dedup_lock:
        _dedup_store[commenter_id] = datetime.now(timezone.utc).isoformat()
        # Prune entries older than 7 days
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        to_delete = [
            k for k, v in _dedup_store.items()
            if datetime.fromisoformat(v) < cutoff
        ]
        for k in to_delete:
            del _dedup_store[k]


# -- Spam filter ---------------------------------------------------------------

def is_spam(comment_text: str) -> bool:
    """Check if comment text looks like spam."""
    if not comment_text or len(comment_text.strip()) < 3:
        return True
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
        mark_responded(commenter_id)


# -- Webhook handler -----------------------------------------------------------

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

            thread = threading.Thread(
                target=process_comment,
                args=(comment_id, commenter_id, comment_text, post_id),
                daemon=True,
            )
            thread.start()
