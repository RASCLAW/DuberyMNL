"""
In-memory conversation store for Cloud Run deployment.

Stores conversations in a thread-safe dict. State is ephemeral --
resets when the Cloud Run instance scales down. This is acceptable
because Meta's 24h messaging window naturally bounds conversations
and the chatbot handles short sales flows (inquiry -> order -> handoff).

Same interface as the file-based version in tools/chatbot/.
"""

import threading
from datetime import datetime, timezone

MAX_HISTORY_FOR_CLAUDE = 20


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _new_conversation(sender_id: str, sender_name: str = "") -> dict:
    return {
        "sender_id": sender_id,
        "sender_name": sender_name,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "messages": [],
        "metadata": {
            "total_messages": 0,
            "detected_intents": [],
            "handoff_flagged": False,
            "products_mentioned": [],
            "last_user_message_at": None,
        },
    }


class ConversationStore:
    """Thread-safe, in-memory conversation storage."""

    def __init__(self):
        self._conversations = {}
        self._lock = threading.RLock()

    def get_or_create(self, sender_id: str, sender_name: str = "") -> dict:
        with self._lock:
            if sender_id not in self._conversations:
                self._conversations[sender_id] = _new_conversation(sender_id, sender_name)
            return self._conversations[sender_id]

    def append_message(self, sender_id: str, role: str, content: str,
                       intent: str = None, products: list = None):
        with self._lock:
            conv = self.get_or_create(sender_id)
            msg = {
                "role": role,
                "content": content,
                "timestamp": _now_iso(),
            }
            conv["messages"].append(msg)
            conv["updated_at"] = _now_iso()
            conv["metadata"]["total_messages"] = len(conv["messages"])

            if role == "user":
                conv["metadata"]["last_user_message_at"] = _now_iso()

            if intent and intent not in conv["metadata"]["detected_intents"]:
                conv["metadata"]["detected_intents"].append(intent)

            if products:
                for p in products:
                    if p not in conv["metadata"]["products_mentioned"]:
                        conv["metadata"]["products_mentioned"].append(p)

    def flag_handoff(self, sender_id: str, reason: str = ""):
        with self._lock:
            conv = self.get_or_create(sender_id)
            conv["metadata"]["handoff_flagged"] = True
            conv["metadata"]["handoff_reason"] = reason
            conv["metadata"]["handoff_at"] = _now_iso()
            conv["updated_at"] = _now_iso()

    def is_handed_off(self, sender_id: str) -> bool:
        with self._lock:
            conv = self.get_or_create(sender_id)
            return conv["metadata"].get("handoff_flagged", False)

    def get_history_for_claude(self, sender_id: str) -> list:
        """Return trimmed message list for the AI model."""
        with self._lock:
            conv = self.get_or_create(sender_id)
            messages = conv.get("messages", [])
            if len(messages) <= MAX_HISTORY_FOR_CLAUDE:
                return list(messages)
            first_user = None
            for m in messages:
                if m["role"] == "user":
                    first_user = m
                    break
            trimmed = list(messages[-MAX_HISTORY_FOR_CLAUDE:])
            if first_user and first_user not in trimmed:
                trimmed = [first_user] + trimmed
            return trimmed

    def is_within_24h_window(self, sender_id: str) -> bool:
        """Check if the last user message was within Meta's 24-hour window."""
        with self._lock:
            conv = self.get_or_create(sender_id)
            last = conv["metadata"].get("last_user_message_at")
            if not last:
                return False
            last_dt = datetime.fromisoformat(last)
            now = datetime.now(timezone.utc)
            return (now - last_dt).total_seconds() < 86400

    def list_recent(self, limit: int = 20) -> list:
        """List recent conversations sorted by last update."""
        with self._lock:
            convs = []
            for sender_id, data in self._conversations.items():
                convs.append({
                    "sender_id": data["sender_id"],
                    "sender_name": data.get("sender_name", ""),
                    "updated_at": data["updated_at"],
                    "total_messages": data["metadata"]["total_messages"],
                    "handoff_flagged": data["metadata"].get("handoff_flagged", False),
                    "last_intent": (data["metadata"]["detected_intents"] or ["unknown"])[-1],
                })
            convs.sort(key=lambda c: c["updated_at"], reverse=True)
            return convs[:limit]
