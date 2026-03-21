"""
Handoff system for DuberyMNL Messenger chatbot.

Detects when a conversation needs human intervention,
flags the conversation, logs the handoff, and emails RA.

Usage:
    from handoff import check_and_handle_handoff
    check_and_handle_handoff(store, sender_id, "order_complete")
"""

import json
import os
import smtplib
import sys
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_DIR / ".env")

TMP_DIR = PROJECT_DIR / ".tmp"
HANDOFFS_FILE = TMP_DIR / "chatbot_handoffs.json"

GMAIL_SENDER = os.getenv("GMAIL_SENDER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
RECIPIENT = os.getenv("REVIEW_EMAIL_RECIPIENT")

REASON_LABELS = {
    "explicit_request": "Customer asked for a human",
    "complaint": "Complaint or frustration detected",
    "order_complete": "Order info collected -- ready for confirmation",
    "low_confidence": "Bot unsure how to respond",
    "outside_knowledge": "Question outside bot's knowledge",
    "bot_triggered": "Bot flagged for handoff",
    "technical_failure": "Technical error during processing",
}


def check_and_handle_handoff(store, sender_id: str, reason: str):
    """Flag conversation for handoff, log it, and notify RA."""
    # Flag in conversation store
    store.flag_handoff(sender_id, reason)

    # Get conversation summary
    conv = store.get_or_create(sender_id)
    messages = conv.get("messages", [])
    last_messages = messages[-6:] if messages else []

    # Log to handoffs file
    handoff_entry = {
        "sender_id": sender_id,
        "sender_name": conv.get("sender_name", ""),
        "reason": reason,
        "reason_label": REASON_LABELS.get(reason, reason),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message_count": len(messages),
        "last_messages": [
            {"role": m["role"], "content": m["content"][:200]}
            for m in last_messages
        ],
    }
    _append_handoff_log(handoff_entry)

    # Email RA
    _send_handoff_email(handoff_entry)

    print(f"Handoff triggered for {sender_id}: {reason}")


def _append_handoff_log(entry: dict):
    """Append a handoff entry to the log file."""
    handoffs = []
    if HANDOFFS_FILE.exists():
        try:
            handoffs = json.loads(HANDOFFS_FILE.read_text())
        except (json.JSONDecodeError, FileNotFoundError):
            handoffs = []
    handoffs.append(entry)
    HANDOFFS_FILE.write_text(json.dumps(handoffs, indent=2, ensure_ascii=False))


def _send_handoff_email(entry: dict):
    """Email RA about the handoff."""
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD or not RECIPIENT:
        print("Handoff email skipped: Gmail credentials not configured", file=sys.stderr)
        return

    reason_label = entry.get("reason_label", entry["reason"])
    sender_name = entry.get("sender_name") or entry["sender_id"]

    # Format recent messages
    msg_lines = []
    for m in entry.get("last_messages", []):
        role = "Customer" if m["role"] == "user" else "Bot"
        msg_lines.append(f"  {role}: {m['content']}")
    msg_summary = "\n".join(msg_lines) if msg_lines else "  (no messages)"

    subject = f"DuberyMNL Chatbot -- Handoff: {reason_label}"
    body = f"""Hi RA,

The chatbot has flagged a conversation for your attention.

Customer: {sender_name}
Reason: {reason_label}
Messages: {entry.get('message_count', 0)} total

Recent conversation:
{msg_summary}

Please check Messenger and reply to the customer directly.

-- DuberyMNL Chatbot
"""

    msg = MIMEMultipart()
    msg["From"] = GMAIL_SENDER
    msg["To"] = RECIPIENT
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_SENDER, RECIPIENT, msg.as_string())
        print(f"Handoff email sent to {RECIPIENT}")
    except Exception as e:
        print(f"Handoff email failed: {e}", file=sys.stderr)
