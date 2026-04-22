"""Chatbot monitor process health check -- confirms monitor.py watchdog is running."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from monitors import ServiceStatus  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MONITOR_SCRIPT = PROJECT_ROOT / "chatbot" / "monitor.py"


def check() -> ServiceStatus:
    log_src = None
    log_path = PROJECT_ROOT / "chatbot" / "logs" / "monitor.log"
    if log_path.exists():
        log_src = log_path.as_posix()

    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-WmiObject Win32_Process | Where-Object {$_.CommandLine -like '*monitor.py*'} | Measure-Object | Select-Object -ExpandProperty Count"],
            capture_output=True, text=True, timeout=5,
        )
        count = int(result.stdout.strip() or "0")
        if count > 0:
            return ServiceStatus.now("chatbot_monitor", "active", f"{count} process(es) running", log_src)
        return ServiceStatus.now("chatbot_monitor", "offline", "monitor.py not found in process list", log_src)
    except Exception as exc:
        return ServiceStatus.now("chatbot_monitor", "offline", f"{type(exc).__name__}: {exc}", log_src)


if __name__ == "__main__":
    print(check())
