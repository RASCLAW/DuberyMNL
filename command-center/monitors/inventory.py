"""Inventory monitor -- reads inventory.json + orders.json, flags low/OOS SKUs."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from monitors import ServiceStatus  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def check() -> ServiceStatus:
    try:
        sys.path.insert(0, str(PROJECT_ROOT / "tools" / "orders"))
        from inventory_report import compute_report  # noqa: E402

        report = compute_report()
        report.pop("_unmatched", None)

        if not report:
            return ServiceStatus.now("inventory", "not_wired", "inventory.json missing")

        oos = [sku for sku, d in report.items() if d["remaining"] == 0]
        low = [sku for sku, d in report.items() if 0 < d["remaining"] < 3]
        total_remaining = sum(d["remaining"] for d in report.values())

        if oos:
            msg = f"OOS: {', '.join(oos)}"
            return ServiceStatus.now("inventory", "offline", msg)
        if low:
            msg = f"Low stock: {', '.join(low)} | {total_remaining} units total"
            return ServiceStatus.now("inventory", "degraded", msg)

        return ServiceStatus.now("inventory", "active", f"{total_remaining} units across {len(report)} SKUs")
    except Exception as exc:
        return ServiceStatus.now("inventory", "offline", f"{type(exc).__name__}: {exc}")


if __name__ == "__main__":
    print(check())
