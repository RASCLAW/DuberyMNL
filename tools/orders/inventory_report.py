"""
Inventory report -- aggregates sold units from orders.json and computes
remaining stock against inventory.json.

Usage:
    python tools/orders/inventory_report.py

Returns: dict keyed by SKU slug with {initial, sold, remaining}
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
INVENTORY_FILE = PROJECT_ROOT / "inventory.json"
ORDERS_FILE = PROJECT_ROOT / "orders" / "orders.json"

# RA 2026-05-31: low-stock alert threshold (remaining <= this = LOW; 0 = OOS).
LOW_THRESHOLD = 1

# Map normalized display-name fragments → SKU key.
# Normalization: lowercase, collapse whitespace, replace em-dash/en-dash with hyphen.
_DISPLAY_MAP = {
    "outback black":        "outback-black",
    "outback blue":         "outback-blue",
    "outback green":        "outback-green",
    "outback red":          "outback-red",
    "outback stripe":       "outback-stripe",
    "bandits matte black":  "bandits-matte-black",
    # RA calls the matte-black / ruby-lens Bandits "Red"
    "bandits red":          "bandits-matte-black",
    "bandits glossy black": "bandits-glossy-black",
    # "Bandits – Black" without qualifier is treated as glossy black
    "bandits black":        "bandits-glossy-black",
    "bandits blue":         "bandits-blue",
    "bandits green":        "bandits-green",
    "bandits tortoise":     "bandits-tortoise",
    "rasta brown":          "rasta-brown",
    "rasta red":            "rasta-red",
}


def _normalize(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[–—\-]", " ", s)  # en-dash, em-dash, hyphen → space
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _parse_items(items_str: str, qty_str: str) -> list[tuple[str, int]]:
    """Parse multiline Items + Qty fields into (display_name, qty) pairs."""
    items = [i.strip() for i in items_str.split("\n") if i.strip()]
    qtys = [q.strip() for q in qty_str.split("\n") if q.strip()]
    pairs = []
    for i, item in enumerate(items):
        try:
            qty = int(qtys[i]) if i < len(qtys) else 1
        except ValueError:
            qty = 1
        pairs.append((item, qty))
    return pairs


def _item_to_sku(display: str) -> str | None:
    norm = _normalize(display)
    # Exact match first
    if norm in _DISPLAY_MAP:
        return _DISPLAY_MAP[norm]
    # Partial match: find the longest key that is a substring of norm
    best = None
    best_len = 0
    for key, sku in _DISPLAY_MAP.items():
        if key in norm and len(key) > best_len:
            best = sku
            best_len = len(key)
    return best


def _parse_ts(ts: str):
    """Parse an Orders 'Timestamp' like '5/14/2026 16:17:08' -> datetime, else None."""
    ts = (ts or "").strip()
    for fmt in ("%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M", "%m/%d/%Y"):
        try:
            return datetime.strptime(ts, fmt)
        except ValueError:
            continue
    return None


def compute_report() -> dict:
    """Return per-SKU {on_hand, sold_history, sold_after_baseline, pending, remaining}.

    on_hand: physical count as of inventory.json `_as_of` (manual; bumped on restock).
    sold_history: ALL-TIME delivered units (informational).
    sold_after_baseline: DELIVERED units dated AFTER `_as_of` -- these AUTO-DECREMENT.
    pending: non-delivered, non-canceled committed units (col K blank/other).
    remaining: max(0, on_hand - sold_after_baseline) -- the live sellable count.
    CANCELED rows skipped entirely. Keys starting with "_" in inventory.json are metadata.
    """
    if not INVENTORY_FILE.exists():
        return {}
    inventory = json.loads(INVENTORY_FILE.read_text(encoding="utf-8"))
    try:
        as_of = datetime.strptime(inventory.get("_as_of", ""), "%Y-%m-%d")
    except (ValueError, TypeError):
        as_of = None
    skus = {k: v for k, v in inventory.items() if not k.startswith("_")}

    sold_history = {sku: 0 for sku in skus}
    sold_after = {sku: 0 for sku in skus}
    pending = {sku: 0 for sku in skus}
    unmatched: list[str] = []

    if ORDERS_FILE.exists():
        orders = json.loads(ORDERS_FILE.read_text(encoding="utf-8"))
        for order in orders:
            status_k = (order.get("Status") or "").strip().upper()
            if status_k == "CANCELED":
                continue
            is_pending = status_k != "DELIVERED"
            odt = _parse_ts(order.get("Timestamp", ""))
            pairs = _parse_items(order.get("Items", ""), order.get("Qty", ""))
            for display, qty in pairs:
                sku = _item_to_sku(display)
                if sku and sku in skus:
                    if is_pending:
                        pending[sku] += qty
                    else:
                        sold_history[sku] += qty
                        if as_of and odt and odt > as_of:
                            sold_after[sku] += qty
                else:
                    unmatched.append(display)

    report = {}
    for sku, meta in skus.items():
        on_hand = meta.get("on_hand", 0)
        report[sku] = {
            "on_hand": on_hand,
            "sold_history": sold_history[sku],
            "sold_after_baseline": sold_after[sku],
            "pending": pending[sku],
            "remaining": max(0, on_hand - sold_after[sku]),
        }

    if unmatched:
        report["_unmatched"] = unmatched

    return report


if __name__ == "__main__":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")  # cp1252 guard
    report = compute_report()
    unmatched = report.pop("_unmatched", [])
    print(f"{'SKU':<25} {'OnHand':>7} {'Sold*':>6} {'Remain':>7}")
    print("-" * 49)
    for sku, d in sorted(report.items()):
        flag = " OOS" if d["remaining"] == 0 else (" LOW" if d["remaining"] <= LOW_THRESHOLD else "")
        print(f"{sku:<25} {d['on_hand']:>7} {d['sold_after_baseline']:>6} {d['remaining']:>7}{flag}")
    total = sum(d["remaining"] for d in report.values())
    print("-" * 49)
    print(f"{'TOTAL REMAINING':<25} {'':>7} {'':>6} {total:>7}")
    print("* Sold = delivered since baseline (_as_of); auto-decrements remaining.")
    if unmatched:
        print(f"\nUnmatched items (not in map): {sorted(set(unmatched))}")
