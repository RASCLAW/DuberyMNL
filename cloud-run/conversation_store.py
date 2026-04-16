"""
Persistent conversation store for the laptop-Flask deployment.

Stores conversations in a thread-safe dict, persisted to disk so that
restarts (Task Scheduler restarts, code redeploys, laptop reboots)
don't wipe customer history. Without persistence, returning customers
get re-greeted as fresh contacts -- e.g., Kingpin Dela Cruz's Apr 16
follow-up was treated as a first message because Flask restarted between
his Apr 15 order and the next-day question.

Persistence is best-effort: file write happens after every modification,
atomically (write-then-rename), with conversations older than 30 days
pruned on save to keep the file small.

Same interface as the original in-memory version. Adds:
    store.save()        -- explicit flush
    store.load()        -- explicit reload (auto-called on init)
"""

import json
import os
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

MAX_HISTORY_FOR_CLAUDE = 20

# Persist beside the cloud-run code so it travels with the bot but stays
# out of git (.tmp/ is gitignored at project root).
_DEFAULT_STORE_PATH = (
    Path(__file__).resolve().parent.parent / ".tmp" / "conversation_store.json"
)
_PRUNE_AGE_DAYS = 30


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
    """Thread-safe, disk-persisted conversation storage."""

    def __init__(self, store_path: Path = None):
        self._conversations = {}
        self._lock = threading.RLock()
        self._store_path = Path(store_path) if store_path else _DEFAULT_STORE_PATH
        self.load()

    # -- persistence helpers --

    def load(self):
        """Load conversations from disk. Best-effort; missing/corrupt file = empty start."""
        with self._lock:
            if not self._store_path.exists():
                return
            try:
                data = json.loads(self._store_path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    self._conversations = data
            except (json.JSONDecodeError, OSError) as e:
                # Don't crash startup on corrupt file; preserve it for inspection
                backup = self._store_path.with_suffix(".corrupt.json")
                try:
                    self._store_path.rename(backup)
                except OSError:
                    pass
                print(f"conversation_store load failed ({e}); started empty, "
                      f"corrupt file backed up to {backup.name}")

    def save(self):
        """Atomically write conversations to disk. Prunes old entries first."""
        with self._lock:
            self._prune_old()
            self._store_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._store_path.with_suffix(".tmp")
            try:
                tmp.write_text(
                    json.dumps(self._conversations, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                os.replace(tmp, self._store_path)
            except OSError as e:
                print(f"conversation_store save failed: {e}")

    def _prune_old(self):
        """Drop conversations whose updated_at is older than _PRUNE_AGE_DAYS."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=_PRUNE_AGE_DAYS)
        to_drop = []
        for sid, data in self._conversations.items():
            updated = data.get("updated_at")
            if not updated:
                continue
            try:
                if datetime.fromisoformat(updated) < cutoff:
                    to_drop.append(sid)
            except (ValueError, TypeError):
                continue
        for sid in to_drop:
            del self._conversations[sid]

    # -- core API (auto-saves on every mutating call) --

    def get_or_create(self, sender_id: str, sender_name: str = "") -> dict:
        with self._lock:
            if sender_id not in self._conversations:
                self._conversations[sender_id] = _new_conversation(sender_id, sender_name)
                self.save()
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
            self.save()

    def flag_handoff(self, sender_id: str, reason: str = ""):
        with self._lock:
            conv = self.get_or_create(sender_id)
            conv["metadata"]["handoff_flagged"] = True
            conv["metadata"]["handoff_reason"] = reason
            conv["metadata"]["handoff_at"] = _now_iso()
            conv["updated_at"] = _now_iso()
            self.save()

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
