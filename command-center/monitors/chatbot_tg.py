"""DuberyMNL chatbot Telegram ping bot monitor -- calls Telegram getMe to confirm bot token is live."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from monitors import ServiceStatus  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

TIMEOUT_SEC = 3


def check() -> ServiceStatus:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        return ServiceStatus.now(
            "chatbot_tg", "not_wired", "TELEGRAM_BOT_TOKEN env not set"
        )
    try:
        resp = requests.get(
            f"https://api.telegram.org/bot{token}/getMe", timeout=TIMEOUT_SEC
        )
        data = resp.json()
        if resp.ok and data.get("ok") is True:
            username = data.get("result", {}).get("username", "unknown")
            return ServiceStatus.now("chatbot_tg", "active", f"@{username}")
        return ServiceStatus.now(
            "chatbot_tg", "offline", data.get("description", "api error")
        )
    except Exception as exc:
        return ServiceStatus.now(
            "chatbot_tg", "offline", f"{type(exc).__name__}: {exc}"
        )


if __name__ == "__main__":
    print(check())
