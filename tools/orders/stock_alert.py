"""
Low-stock Telegram alert for DuberyMNL (extends tools/orders/).

Reads the local inventory report (inventory.json + orders.json via
inventory_report.compute_report) -- NO Sheets call, so it runs anywhere.
Pings RA's Telegram when a SKU's `remaining` is at/under LOW_THRESHOLD (<=1)
or 0 (OOS), so he can reorder. Deduped via .tmp/orders_stock_alerted.json so a
still-low SKU doesn't re-ping every run; restocking above threshold resets it.

NOTE: stock-out does NOT pause ads (backorder model -- see delivery-pricing-policy).
This only nudges RA to reorder.

Hourly cron should run `sync_orders.py` (refresh orders.json from Sheets) THEN
this. This script alone does not refresh the sheet.

Run:
  python tools/orders/stock_alert.py          # check + TG if new low SKUs
  python tools/orders/stock_alert.py --dry     # print only, no TG, no state write
"""
import os
import sys
import io
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone, timedelta

import requests
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent))
from inventory_report import compute_report, LOW_THRESHOLD  # noqa: E402

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parent.parent.parent
load_dotenv(REPO / ".env")
STATE_FILE = REPO / ".tmp" / "orders_stock_alerted.json"


def _now_pht():
    return (datetime.now(timezone.utc) + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")


def _low_skus() -> dict:
    report = compute_report()
    report.pop("_unmatched", None)
    return {sku: d for sku, d in report.items() if d["remaining"] <= LOW_THRESHOLD}


def _load_alerted() -> set:
    if STATE_FILE.exists():
        try:
            return set(json.loads(STATE_FILE.read_text()).get("alerted", []))
        except Exception:
            return set()
    return set()


def _save_alerted(skus):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps({"alerted": sorted(skus), "updated": _now_pht()}, indent=2))


def _send_tg(text: str) -> bool:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat = os.environ.get("TG_CHAT_ID", "")
    if not token or not chat:
        print("TG creds missing -- skipping send", file=sys.stderr)
        return False
    r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                      json={"chat_id": chat, "text": text}, timeout=30)
    return r.status_code == 200


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    low = _low_skus()
    low_keys = set(low.keys())
    alerted = _load_alerted()
    new = low_keys - alerted

    def fmt(sku, d):
        tag = "OOS" if d["remaining"] == 0 else "LOW"
        return f"• {sku}: {d['remaining']} ({tag})"

    if not low:
        print("All SKUs above threshold. No alert.")
        if not args.dry:
            _save_alerted(set())
        return

    lines = ["\U0001F4E6 DuberyMNL low stock (≤{}):".format(LOW_THRESHOLD)]
    lines += [fmt(s, low[s]) for s in sorted(low_keys)]
    lines.append("Reorder check: python tools/orders/reorder_report.py")
    msg = "\n".join(lines)
    print(msg)
    print(f"\n(new since last alert: {sorted(new) or 'none'})")

    if args.dry:
        return
    if new:
        ok = _send_tg(msg)
        print(f"TG sent: {ok}")
    else:
        print("No NEW low SKUs -- not re-pinging.")
    _save_alerted(low_keys)


if __name__ == "__main__":
    main()
