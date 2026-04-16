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

# Persist beside the chatbot code so it travels with the bot but stays
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
            # Ad / referral attribution -- set by webhook when Meta fires a
            # `referral` event or message.referral payload. None until a known
            # entry-point is seen.
            "source_ad_id": None,
            "source_ref": None,
            "source_type": None,
            "source_first_seen_at": None,
            # Rolling FIFO of the last 3 bot-reply theme signatures. Used by
            # the repetition-guard handoff: if a new reply's signature matches
            # the most recent 2 in a row, bot is stuck in a loop and we force
            # handoff instead of sending the 4th copy of the same policy.
            "recent_reply_sigs": [],
            # Policies the bot has already explained to this customer. Once a
            # policy is stamped here, the bot MUST NOT re-explain it on
            # subsequent customer pushback -- hand off instead. Employee
            # discipline rule: policies are stated once; pushback is not a
            # re-negotiation.
            "policies_delivered": [],
            # Proactive nurture tracking. The background scanner checks
            # `nurture_sent` before firing; we only send ONE follow-up per
            # customer, ever. `nurture_sent_at` records when so we can
            # debug/analyze later.
            "nurture_sent": False,
            "nurture_sent_at": None,
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

    def release_handoff(self, sender_id: str):
        """Clear handoff flag so the bot resumes replying. Used when RA finishes
        a manual conversation and wants to hand control back to the bot."""
        with self._lock:
            conv = self.get_or_create(sender_id)
            conv["metadata"]["handoff_flagged"] = False
            conv["metadata"]["handoff_reason"] = ""
            conv["metadata"]["released_at"] = _now_iso()
            conv["updated_at"] = _now_iso()
            self.save()

    def is_handed_off(self, sender_id: str) -> bool:
        with self._lock:
            conv = self.get_or_create(sender_id)
            return conv["metadata"].get("handoff_flagged", False)

    def push_reply_signature(self, sender_id: str, signature: str) -> bool:
        """Append a reply signature to the rolling 3-slot FIFO and return
        True if this signature would make the bot repeat itself a 3rd time
        in a row (i.e. the last 2 stored sigs already match). Caller should
        short-circuit the outgoing reply and flag handoff when True.

        'other' signatures are stored but ignored for loop detection so we
        don't false-positive on generic chit-chat."""
        if not signature:
            return False
        with self._lock:
            conv = self.get_or_create(sender_id)
            sigs = list(conv["metadata"].get("recent_reply_sigs") or [])
            is_loop = (
                signature != "other"
                and len(sigs) >= 2
                and sigs[-1] == signature
                and sigs[-2] == signature
            )
            sigs.append(signature)
            conv["metadata"]["recent_reply_sigs"] = sigs[-3:]
            conv["updated_at"] = _now_iso()
            self.save()
            return is_loop

    def reset_reply_signatures(self, sender_id: str):
        """Clear the signature FIFO -- used after a handoff/release so a
        fresh bot-resumed exchange doesn't immediately re-trigger the loop
        guard on its first reply."""
        with self._lock:
            conv = self.get_or_create(sender_id)
            conv["metadata"]["recent_reply_sigs"] = []
            conv["updated_at"] = _now_iso()
            self.save()

    def add_policy_delivered(self, sender_id: str, policy_id: str) -> bool:
        """Stamp a policy as delivered for this customer. Returns True if
        newly added, False if already present. Idempotent -- the bot can
        call this every time it delivers the policy text; only the first
        call mutates state."""
        if not policy_id:
            return False
        with self._lock:
            conv = self.get_or_create(sender_id)
            delivered = conv["metadata"].setdefault("policies_delivered", [])
            if policy_id in delivered:
                return False
            delivered.append(policy_id)
            conv["updated_at"] = _now_iso()
            self.save()
            return True

    def get_policies_delivered(self, sender_id: str) -> list:
        """Return the list of policy IDs already explained to this customer."""
        with self._lock:
            conv = self.get_or_create(sender_id)
            return list(conv["metadata"].get("policies_delivered") or [])

    def count_assistant_replies(self, sender_id: str) -> int:
        """Count how many assistant messages this conversation has. Used by
        the turn-cap handoff: after N assistant replies without converting
        to an order, the bot bows out and RA takes over."""
        with self._lock:
            conv = self.get_or_create(sender_id)
            return sum(1 for m in conv.get("messages", []) if m.get("role") == "assistant")

    def mark_nurture_sent(self, sender_id: str) -> None:
        """Stamp that we've fired a proactive nurture message at this
        customer. Enforces the "one nudge per customer ever" rule in the
        nurture scanner."""
        with self._lock:
            conv = self.get_or_create(sender_id)
            conv["metadata"]["nurture_sent"] = True
            conv["metadata"]["nurture_sent_at"] = _now_iso()
            conv["updated_at"] = _now_iso()
            self.save()

    def snapshot_for_nurture(self) -> list:
        """Return a lightweight snapshot of all conversations for the nurture
        scanner. We copy only the fields the scanner needs, under the lock,
        so the Send API calls can happen outside the lock without racing
        against webhook writes."""
        with self._lock:
            out = []
            for sid, conv in self._conversations.items():
                meta = conv.get("metadata", {})
                out.append({
                    "sender_id": sid,
                    "first_name": meta.get("first_name"),
                    "handoff_flagged": meta.get("handoff_flagged", False),
                    "order_recorded": meta.get("order_recorded", False),
                    "nurture_sent": meta.get("nurture_sent", False),
                    "detected_intents": list(meta.get("detected_intents") or []),
                    "last_user_message_at": meta.get("last_user_message_at"),
                })
            return out

    def set_first_name(self, sender_id: str, first_name: str) -> bool:
        """Persist a first name on the conversation if one isn't already set.
        Returns True if newly written, False if skipped."""
        if not first_name:
            return False
        with self._lock:
            conv = self.get_or_create(sender_id)
            if conv["metadata"].get("first_name"):
                return False
            conv["metadata"]["first_name"] = first_name
            conv["updated_at"] = _now_iso()
            self.save()
            return True

    def set_source(self, sender_id: str, ad_id: str = None, ref: str = None,
                   source_type: str = None):
        """Record the ad/referral entry-point for a conversation. Only writes
        fields once (first-touch attribution) -- subsequent clicks on other
        ads don't overwrite the original source."""
        with self._lock:
            conv = self.get_or_create(sender_id)
            meta = conv["metadata"]
            touched = False
            if ad_id and not meta.get("source_ad_id"):
                meta["source_ad_id"] = ad_id
                touched = True
            if ref and not meta.get("source_ref"):
                meta["source_ref"] = ref
                touched = True
            if source_type and not meta.get("source_type"):
                meta["source_type"] = source_type
                touched = True
            if touched:
                meta["source_first_seen_at"] = _now_iso()
                conv["updated_at"] = _now_iso()
                self.save()

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
