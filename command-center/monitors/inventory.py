"""Inventory monitor -- placeholder for Phase 3 wiring."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from monitors import ServiceStatus  # noqa: E402


def check() -> ServiceStatus:
    return ServiceStatus.now(
        name="inventory",
        state="not_wired",
        message="Phase 3",
    )


if __name__ == "__main__":
    print(check())
