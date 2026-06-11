"""Reorder report -- prints sold/on-hand/target/to-order per SKU."""
import json
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from inventory_report import compute_report  # noqa: E402

REORDER_FILE = Path(__file__).resolve().parent.parent.parent / "orders" / "reorder.json"

data = json.loads(REORDER_FILE.read_text(encoding="utf-8"))
skus = data["skus"]

inv = compute_report()
inv.pop("_unmatched", None)

print(f"{'SKU':<25} {'Sold':>5} {'Pending':>8} {'On Hand':>8} {'Target':>7} {'To Order':>9}")
print("-" * 69)
total_to_order = 0
total_sold = 0
total_pending = 0
for sku in sorted(skus):
    sold = inv.get(sku, {}).get("sold_history", 0)
    pending = inv.get(sku, {}).get("pending", 0)
    on_hand = skus[sku]["on_hand"]
    target = skus[sku]["target_stock"]
    to_order = max(0, target - on_hand)
    total_to_order += to_order
    total_sold += sold
    total_pending += pending
    print(f"{sku:<25} {sold:>5} {pending:>8} {on_hand:>8} {target:>7} {to_order:>9}")
print("-" * 69)
print(f"{'TOTAL':<25} {total_sold:>5} {total_pending:>8} {'':>8} {'':>7} {total_to_order:>9}")
