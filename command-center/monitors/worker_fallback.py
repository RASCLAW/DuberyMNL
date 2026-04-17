"""Cloudflare Worker fallback monitor -- checks dubery-chatbot-fallback is reachable.

The Worker sits in front of chatbot.duberymnl.com. A GET may return 200 or 405
(Worker rejects non-POST) -- both mean alive.
"""
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

DEFAULT_WORKER_URL = "https://dubery-chatbot-fallback.reasarinas.workers.dev/"
TIMEOUT_SEC = 3


def check() -> ServiceStatus:
    env_url = os.environ.get("WORKER_URL")
    url = env_url or DEFAULT_WORKER_URL
    try:
        resp = requests.get(url, timeout=TIMEOUT_SEC)
        status = resp.status_code
        if status in (200, 405):
            return ServiceStatus.now("worker_fallback", "active", f"HTTP {status}")
        return ServiceStatus.now("worker_fallback", "degraded", f"HTTP {status}")
    except Exception as exc:
        if env_url is None:
            return ServiceStatus.now(
                "worker_fallback", "not_wired", "WORKER_URL env not set"
            )
        return ServiceStatus.now(
            "worker_fallback", "offline", f"{type(exc).__name__}: {exc}"
        )


if __name__ == "__main__":
    print(check())
