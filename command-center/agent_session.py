"""Persistent Claude Agent SDK session wrapper for the Command Center.

One module-level singleton holds the active session_id. First `.ask()` call
creates a new session (pays cache-create cost, ~$0.24). Subsequent calls
resume that session (cached tokens, much cheaper).

The agent inherits DuberyMNL's project context via settingSources=['project'],
so all .claude/skills/ and the project CLAUDE.md are loaded automatically.
"""
from __future__ import annotations

import asyncio
import threading
import time
from pathlib import Path
from typing import AsyncIterator, Optional

from claude_agent_sdk import query, ClaudeAgentOptions

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class AgentSession:
    """Singleton-ish wrapper around claude_agent_sdk.query with session reuse."""

    _instance: Optional["AgentSession"] = None

    def __init__(self) -> None:
        self.session_id: Optional[str] = None
        self.last_ok_ts: Optional[float] = None
        self.last_error: Optional[str] = None
        self._lock = threading.Lock()

    def status(self) -> dict:
        """Snapshot of agent health for /api/agent/status."""
        now = time.time()
        age = (now - self.last_ok_ts) if self.last_ok_ts else None
        # Alive if a successful response happened in the last 10 minutes.
        # Warming if no calls yet. Dead if last call errored with no later success.
        if self.last_ok_ts and age is not None and age < 600:
            state = "live"
        elif self.last_error and not self.last_ok_ts:
            state = "dead"
        elif self.session_id is None and self.last_ok_ts is None:
            state = "warming"
        else:
            state = "stale"
        return {
            "state": state,
            "session_id": self.session_id,
            "last_ok_ts": self.last_ok_ts,
            "age_seconds": age,
            "last_error": self.last_error,
        }

    @classmethod
    def get(cls) -> "AgentSession":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _build_options(self, resume: Optional[str]) -> ClaudeAgentOptions:
        # cwd as POSIX string avoids Windows backslash quirks in settingSources.
        cwd = PROJECT_ROOT.as_posix()
        kwargs: dict = {
            "cwd": cwd,
            "setting_sources": ["project"],
            "max_turns": 30,
            "permission_mode": "bypassPermissions",
        }
        if resume:
            kwargs["resume"] = resume
        return ClaudeAgentOptions(**kwargs)

    async def ask(self, prompt: str) -> AsyncIterator[str]:
        """Send a prompt; yield assistant text chunks as they arrive.

        Captures session_id from the first SystemMessage(init) so subsequent
        calls resume the same session.
        """
        with self._lock:
            options = self._build_options(resume=self.session_id)
            got_text = False
            try:
                async for msg in query(prompt=prompt, options=options):
                    cls_name = type(msg).__name__
                    if cls_name == "SystemMessage":
                        # subtype='init' carries session_id for first turn
                        data = getattr(msg, "data", {}) or {}
                        sid = data.get("session_id")
                        if sid and not self.session_id:
                            self.session_id = sid
                    elif cls_name == "AssistantMessage":
                        content = getattr(msg, "content", []) or []
                        for block in content:
                            text = getattr(block, "text", None)
                            if text:
                                got_text = True
                                yield text
                    # ResultMessage / RateLimitEvent ignored for streaming purposes
            except Exception as e:
                self.last_error = f"{type(e).__name__}: {e}"
                raise
            if got_text:
                self.last_ok_ts = time.time()
                self.last_error = None


async def _smoke() -> None:
    """Standalone smoke test. Run: python agent_session.py"""
    session = AgentSession.get()
    print("session.ask('say exactly SESSION_OK')", flush=True)
    chunks = []
    async for chunk in session.ask("Reply with exactly SESSION_OK and nothing else."):
        chunks.append(chunk)
    full = "".join(chunks).strip()
    print("REPLY:", repr(full))
    print("SESSION_ID:", session.session_id)
    print("PASS" if "SESSION_OK" in full else "FAIL")


if __name__ == "__main__":
    asyncio.run(_smoke())
