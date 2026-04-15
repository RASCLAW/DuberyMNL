"""
Per-user conversation history storage.

Stores one JSON file per Messenger sender_id in .tmp/conversations/.
Uses fcntl locking for safe concurrent access.

Usage:
    from conversation_store import ConversationStore
    store = ConversationStore()
    history = store.get_or_create("sender_123")
    store.append_message("sender_123", "user", "Magkano po?")
    store.append_message("sender_123", "assistant", "P599 per pair po!")
    messages = store.get_history_for_claude("sender_123")
"""

try:
    import fcntl
except ImportError:
    fcntl = None
    import msvcrt
import json
from datetime import datetime, timezone
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent.parent
CONVERSATIONS_DIR = PROJECT_DIR / ".tmp" / "conversations"
CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)

MAX_HISTORY_FOR_CLAUDE = 20  # last N messages sent to Claude (keeps token budget tight)


def _conversation_file(sender_id: str) -> Path:
    safe_id = sender_id.replace("/", "_").replace("..", "_")
    return CONVERSATIONS_DIR / f"{safe_id}.json"


def _lock_file(sender_id: str) -> Path:
    safe_id = sender_id.replace("/", "_").replace("..", "_")
    return CONVERSATIONS_DIR / f"{safe_id}.lock"


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
    """Thread-safe, file-backed conversation storage."""

    def get_or_create(self, sender_id: str, sender_name: str = "") -> dict:
        f = _conversation_file(sender_id)
        if f.exists():
            return json.loads(f.read_text())
        conv = _new_conversation(sender_id, sender_name)
        self._write(sender_id, conv)
        return conv

    def append_message(self, sender_id: str, role: str, content: str,
                       intent: str = None, products: list = None):
        lock = _lock_file(sender_id)
        with open(lock, "w") as lf:
            fcntl.flock(lf, fcntl.LOCK_EX) if fcntl else msvcrt.locking(lf.fileno(), msvcrt.LK_LOCK, 1)
            try:
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

                self._write(sender_id, conv)
            finally:
                fcntl.flock(lf, fcntl.LOCK_UN) if fcntl else msvcrt.locking(lf.fileno(), msvcrt.LK_UNLCK, 1)

    def flag_handoff(self, sender_id: str, reason: str = ""):
        lock = _lock_file(sender_id)
        with open(lock, "w") as lf:
            fcntl.flock(lf, fcntl.LOCK_EX) if fcntl else msvcrt.locking(lf.fileno(), msvcrt.LK_LOCK, 1)
            try:
                conv = self.get_or_create(sender_id)
                conv["metadata"]["handoff_flagged"] = True
                conv["metadata"]["handoff_reason"] = reason
                conv["metadata"]["handoff_at"] = _now_iso()
                conv["updated_at"] = _now_iso()
                self._write(sender_id, conv)
            finally:
                fcntl.flock(lf, fcntl.LOCK_UN) if fcntl else msvcrt.locking(lf.fileno(), msvcrt.LK_UNLCK, 1)

    def is_handed_off(self, sender_id: str) -> bool:
        conv = self.get_or_create(sender_id)
        return conv["metadata"].get("handoff_flagged", False)

    def get_history_for_claude(self, sender_id: str) -> list:
        """Return trimmed message list formatted for claude --print."""
        conv = self.get_or_create(sender_id)
        messages = conv.get("messages", [])
        # Keep last N messages, but always include the first user message
        # (often contains the customer's core intent)
        if len(messages) <= MAX_HISTORY_FOR_CLAUDE:
            return messages
        first_user = None
        for m in messages:
            if m["role"] == "user":
                first_user = m
                break
        trimmed = messages[-MAX_HISTORY_FOR_CLAUDE:]
        if first_user and first_user not in trimmed:
            trimmed = [first_user] + trimmed
        return trimmed

    def is_within_24h_window(self, sender_id: str) -> bool:
        """Check if the last user message was within Meta's 24-hour window."""
        conv = self.get_or_create(sender_id)
        last = conv["metadata"].get("last_user_message_at")
        if not last:
            return False
        last_dt = datetime.fromisoformat(last)
        now = datetime.now(timezone.utc)
        return (now - last_dt).total_seconds() < 86400

    def list_recent(self, limit: int = 20) -> list:
        """List recent conversations sorted by last update."""
        convs = []
        for f in CONVERSATIONS_DIR.glob("*.json"):
            try:
                data = json.loads(f.read_text())
                convs.append({
                    "sender_id": data["sender_id"],
                    "sender_name": data.get("sender_name", ""),
                    "updated_at": data["updated_at"],
                    "total_messages": data["metadata"]["total_messages"],
                    "handoff_flagged": data["metadata"].get("handoff_flagged", False),
                    "last_intent": (data["metadata"]["detected_intents"] or ["unknown"])[-1],
                })
            except (json.JSONDecodeError, KeyError):
                continue
        convs.sort(key=lambda c: c["updated_at"], reverse=True)
        return convs[:limit]

    def _write(self, sender_id: str, data: dict):
        f = _conversation_file(sender_id)
        f.write_text(json.dumps(data, indent=2, ensure_ascii=False))
