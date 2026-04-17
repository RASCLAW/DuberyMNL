"""Tunnel monitor -- Cloudflare tunnel + cloudflared.exe process check.

Two-check logic:
  1. HTTP GET https://chatbot.duberymnl.com/status (3s timeout)
  2. tasklist for cloudflared.exe

States:
  - both pass        -> active   ("tunnel + process healthy")
  - only process up  -> degraded ("process up but HTTP unreachable")
  - process down     -> offline  ("cloudflared.exe not running")
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from monitors import ServiceStatus  # noqa: E402

TUNNEL_URL = "https://chatbot.duberymnl.com/status"
HTTP_TIMEOUT = 3
PROC_TIMEOUT = 5


def _http_ok() -> bool:
    try:
        r = requests.get(TUNNEL_URL, timeout=HTTP_TIMEOUT)
        return r.status_code == 200
    except requests.RequestException:
        return False


def _process_running() -> bool:
    try:
        r = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq cloudflared.exe", "/FO", "CSV"],
            capture_output=True,
            text=True,
            timeout=PROC_TIMEOUT,
            shell=False,
        )
    except (subprocess.SubprocessError, OSError):
        return False
    return "cloudflared.exe" in r.stdout


def check() -> ServiceStatus:
    proc_up = _process_running()
    if not proc_up:
        return ServiceStatus.now(
            name="tunnel",
            state="offline",
            message="cloudflared.exe not running",
            log_source=None,
        )
    if _http_ok():
        return ServiceStatus.now(
            name="tunnel",
            state="active",
            message="tunnel + process healthy",
            log_source=None,
        )
    return ServiceStatus.now(
        name="tunnel",
        state="degraded",
        message="process up but HTTP unreachable",
        log_source=None,
    )


if __name__ == "__main__":
    print(check())
