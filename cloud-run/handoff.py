"""
Handoff system for DuberyMNL Messenger chatbot.

Flags conversations that need human attention and stops the bot
from responding further. RA will see the flag in the /conversations
dashboard and can pick up the conversation manually.

Usage:
    from handoff import check_and_handle_handoff
    check_and_handle_handoff(store, sender_id, "order_complete")
"""

from datetime import datetime, timezone

REASON_LABELS = {
    "explicit_request": "Customer asked for a human",
    "complaint": "Complaint or frustration detected",
    "order_complete": "Order info collected -- ready for confirmation",
    "low_confidence": "Bot unsure how to respond",
    "outside_knowledge": "Question outside bot's knowledge",
    "bot_triggered": "Bot flagged for handoff",
    "technical_failure": "Technical error during processing",
    "prompt_injection": "Suspicious input -- possible prompt injection",
    "flood": "Too many messages from same sender in short window",
    "bot_suspected": "Input looks like it's from another bot",
}


def check_and_handle_handoff(store, sender_id: str, reason: str):
    """Flag conversation for handoff. Bot will stop responding to this sender."""
    store.flag_handoff(sender_id, reason)
    label = REASON_LABELS.get(reason, reason)
    print(f"Handoff flagged for {sender_id}: {label}", flush=True)
