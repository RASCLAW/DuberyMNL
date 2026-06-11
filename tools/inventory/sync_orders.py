"""
DuberyMNL inventory -- order sync + low-stock alert (v1).

1. Scan the Orders sheet for rows where Fulfilled (col K) is truthy AND
   Decremented (col L) is blank. For each, parse Items + Qty, decrement the
   matching Inventory SKU, then stamp Decremented = timestamp. Idempotent.
2. After syncing, find SKUs at qty <= threshold and send ONE Telegram alert
   (deduped via .tmp/inventory_alerted.json so the same SKU doesn't re-ping).

Stock-out does NOT pause ads (backorder model) -- this only alerts so RA reorders.

Run:
  python tools/inventory/sync_orders.py            # sync + alert
  python tools/inventory/sync_orders.py --dry      # report only, no writes/TG
"""
import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone, timedelta

import requests
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent))
import inventory as inv  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO = Path(__file__).resolve().parent.parent.parent
load_dotenv(REPO / ".env")
ALERT_STATE = REPO / ".tmp" / "inventory_alerted.json"
TRUE_VALUES = {"true", "yes", "y", "1", "x", "done", "shipped", "fulfilled", "ok"}


def _now_pht():
    return (datetime.now(timezone.utc) + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")


def _is_truthy(cell: str) -> bool:
    return (cell or "").strip().lower() in TRUE_VALUES


def _parse_row_items(items_cell: str, qty_cell: str):
    """Stored Orders format: Items + Qty are newline-joined parallel lists.
    Returns [(canonical_sku, qty), ...] or None if unparseable."""
    names = [n.strip() for n in (items_cell or "").split("\n") if n.strip()]
    qtys_raw = [q.strip() for q in (qty_cell or "").split("\n") if q.strip()]
    if not names:
        return None
    pairs = []
    for idx, name in enumerate(names):
        try:
            q = int(qtys_raw[idx]) if idx < len(qtys_raw) else 1
        except ValueError:
            q = 1
        pairs.append((inv.normalize_sku(name), q))
    return pairs


def sync_orders(dry: bool = False) -> dict:
    tab = inv._first_tab_title()
    rows = inv._values_get(f"'{tab}'!A:L")
    catalog = set(inv.read_inventory().keys())
    processed, skipped = [], []
    for i, row in enumerate(rows[1:], start=2):
        row = row + [""] * (12 - len(row))
        fulfilled, decremented = row[10], row[11]
        if not _is_truthy(fulfilled) or decremented.strip():
            continue
        pairs = _parse_row_items(row[4], row[5])
        unknown = [s for s, _ in (pairs or []) if s not in catalog]
        if not pairs or unknown:
            note = f"SKIP: unparseable/unknown {unknown or row[4]!r}"
            skipped.append((i, note))
            if not dry:
                inv._values_update(f"'{tab}'!L{i}", [[note]])
            continue
        for s, q in pairs:
            if not dry:
                inv.adjust(s, -q)
            processed.append((i, s, q))
        if not dry:
            inv._values_update(f"'{tab}'!L{i}", [[f"decremented {_now_pht()}"]])
    return {"processed": processed, "skipped": skipped}


def _load_alerted() -> set:
    if ALERT_STATE.exists():
        try:
            return set(json.loads(ALERT_STATE.read_text()).get("alerted", []))
        except Exception:
            return set()
    return set()


def _save_alerted(skus: set):
    ALERT_STATE.parent.mkdir(parents=True, exist_ok=True)
    ALERT_STATE.write_text(json.dumps({"alerted": sorted(skus), "updated": _now_pht()}, indent=2))


def _send_tg(text: str) -> bool:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat = os.environ.get("TG_CHAT_ID", "")
    if not token or not chat:
        print("TG creds missing -- skipping alert", file=sys.stderr)
        return False
    r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                      json={"chat_id": chat, "text": text}, timeout=30)
    return r.status_code == 200


def low_stock_check(dry: bool = False):
    data = inv.read_inventory()
    low = {k: v for k, v in data.items() if v["status"] in ("LOW", "OOS")}
    low_skus = set(low.keys())
    alerted = _load_alerted()
    new = low_skus - alerted
    if new and not dry:
        lines = ["\U0001F4E6 DuberyMNL stock alert (≤ threshold):"]
        for k in sorted(low_skus):
            lines.append(f"• {k}: {low[k]['qty']} ({low[k]['status']})")
        lines.append("Reorder the new ones?")
        _send_tg("\n".join(lines))
        _save_alerted(low_skus)
    elif not dry:
        _save_alerted(low_skus)  # drop restocked SKUs from state
    return {"low": low_skus, "new_alerts": new}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()
    try:
        inv._get_creds()
    except Exception as e:
        print(f"AUTH FAILED: {e}", file=sys.stderr)
        sys.exit(2)
    s = sync_orders(dry=args.dry)
    print(f"Sync: {len(s['processed'])} decrements, {len(s['skipped'])} skipped.")
    for i, sku_, q in s["processed"]:
        print(f"  row {i}: {sku_} -{q}")
    for i, note in s["skipped"]:
        print(f"  row {i}: {note}")
    a = low_stock_check(dry=args.dry)
    print(f"Low/OOS: {sorted(a['low']) or 'none'}; new alerts: {sorted(a['new_alerts']) or 'none'}")


if __name__ == "__main__":
    main()
