"""Chatbot service monitor -- checks Flask chatbot /status on localhost:8080."""
from __future__ import annotations

import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from monitors import ServiceStatus  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATUS_URL = "http://localhost:8085/status"
TIMEOUT_SEC = 2


def _log_source() -> str | None:
    log_path = PROJECT_ROOT / "chatbot" / "logs" / "app.log"
    return log_path.as_posix() if log_path.exists() else None


def check() -> ServiceStatus:
    log_src = _log_source()
    try:
        resp = requests.get(STATUS_URL, timeout=TIMEOUT_SEC)
        if resp.status_code == 200:
            resp.json()  # validate JSON parses
            return ServiceStatus.now("chatbot", "active", "200 OK", log_src)
        return ServiceStatus.now(
            "chatbot", "offline", f"HTTP {resp.status_code}", log_src
        )
    except Exception as exc:
        return ServiceStatus.now(
            "chatbot", "offline", f"{type(exc).__name__}: {exc}", log_src
        )


if __name__ == "__main__":
    print(check())
