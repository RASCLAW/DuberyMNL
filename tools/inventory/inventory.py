"""
DuberyMNL inventory -- v1 core module.

Source of truth: an "Inventory" tab in the Orders spreadsheet (ORDERS_SHEET_ID).
SKU key format: "<Series> <EN-DASH> <Color>" -- matches the Orders sheet "Items"
cells + chatbot/crm_sync.py::_parse_items output, so decrement mapping is exact.

Transport: requests + bearer token against the Sheets REST API. We deliberately
do NOT use googleapiclient/httplib2 -- it hangs on sheets.googleapis.com from
this host (see memory reference_googleapi_httplib2_fallback). Auth creds come
from token.json (repo root, Sheets scope) / ADC on Cloud Run.

NOT an ad-gate. Stock-out never pauses ads (backorder model). Low-stock
threshold default = 1 (alert when qty <= 1).

CLI:
  python tools/inventory/inventory.py --check-auth        # verify Sheets access
  python tools/inventory/inventory.py --init              # create+seed Inventory tab
  python tools/inventory/inventory.py --add-order-columns # add Fulfilled/Decremented to Orders
  python tools/inventory/inventory.py --list              # print current stock
  python tools/inventory/inventory.py --adjust "Bandits – Green" -1
"""
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone, timedelta
from urllib.parse import quote

import requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

try:
    sys.stdout.reconfigure(encoding="utf-8")  # en-dash SKUs crash cp1252 console otherwise
except Exception:
    pass

# --- Config ---
ORDERS_SHEET_ID = "1vS-yuFWovqHYWrFte4QXJLtH3Q2-BRDi6i9P4-vXbkA"
INVENTORY_TAB = "Inventory"
TOKEN_FILE = Path(__file__).resolve().parent.parent.parent / "token.json"  # DuberyMNL/token.json
SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
BASE = "https://sheets.googleapis.com/v4/spreadsheets"
DEFAULT_THRESHOLD = 1  # RA 2026-05-31: low stock = 1 (alert when qty <= 1)
TIMEOUT = 30

DASH = "–"  # EN-DASH, matches _parse_items separator


def sku(series: str, color: str) -> str:
    return f"{series} {DASH} {color}"


# Canonical catalog from contents/assets/product-specs.json (2026-05-31).
CATALOG = [
    ("Outback", "Black"), ("Outback", "Blue"), ("Outback", "Green"),
    ("Outback", "Red"), ("Outback", "Stripe"),
    ("Bandits", "Matte Black"), ("Bandits", "Blue"), ("Bandits", "Green"),
    ("Bandits", "Glossy Black"), ("Bandits", "Tortoise"),
    ("Rasta", "Brown"), ("Rasta", "Red"),
]

# Seed quantities -- RA manual stock count, delivery arrived 2026-05-31.
SEED_QTY = {
    ("Outback", "Black"): 0, ("Outback", "Blue"): 5, ("Outback", "Green"): 3,
    ("Outback", "Red"): 3, ("Outback", "Stripe"): 4,
    ("Bandits", "Matte Black"): 3, ("Bandits", "Blue"): 3, ("Bandits", "Green"): 3,
    ("Bandits", "Glossy Black"): 3, ("Bandits", "Tortoise"): 1,
    ("Rasta", "Brown"): 2, ("Rasta", "Red"): 2,
}

# Aliases: colloquial / order-text SKU -> canonical SKU.
# RA refers to the matte-black/ruby-lens Bandits as "Red".
SKU_ALIASES = {
    sku("Bandits", "Red"): sku("Bandits", "Matte Black"),
    sku("Bandits", "Black"): sku("Bandits", "Matte Black"),
}

INVENTORY_COLUMNS = [
    "SKU", "Model", "Color", "Qty", "Status", "Threshold", "Last Updated", "Notes",
]

_creds = None


def _now_pht() -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")


def _get_creds():
    global _creds
    if _creds is not None and _creds.valid:
        return _creds
    creds = None
    if os.environ.get("K_SERVICE"):
        try:
            import google.auth
            creds, _ = google.auth.default(scopes=SHEETS_SCOPES)
        except Exception as e:
            print(f"ADC unavailable: {e}", file=sys.stderr)
            creds = None
    if creds is None and TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SHEETS_SCOPES)
    if creds is None:
        raise RuntimeError(f"No credentials: token.json missing at {TOKEN_FILE} and no ADC")
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            if not os.environ.get("K_SERVICE"):
                TOKEN_FILE.write_text(creds.to_json())
        else:
            creds.refresh(Request())
    _creds = creds
    return creds


def _headers():
    return {"Authorization": f"Bearer {_get_creds().token}"}


def _qrange(rng: str) -> str:
    return quote(rng, safe="")


def _values_get(rng: str) -> list:
    r = requests.get(f"{BASE}/{ORDERS_SHEET_ID}/values/{_qrange(rng)}",
                     headers=_headers(), timeout=TIMEOUT)
    r.raise_for_status()
    return r.json().get("values", [])


def _values_update(rng: str, values: list) -> dict:
    r = requests.put(f"{BASE}/{ORDERS_SHEET_ID}/values/{_qrange(rng)}",
                     headers=_headers(), params={"valueInputOption": "RAW"},
                     json={"values": values}, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def _batch_update(reqs: list) -> dict:
    r = requests.post(f"{BASE}/{ORDERS_SHEET_ID}:batchUpdate",
                      headers=_headers(), json={"requests": reqs}, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def _meta() -> dict:
    r = requests.get(f"{BASE}/{ORDERS_SHEET_ID}", headers=_headers(),
                     params={"fields": "properties.title,sheets.properties.title"},
                     timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def compute_status(qty: int, threshold: int = DEFAULT_THRESHOLD) -> str:
    if qty <= 0:
        return "OOS"
    if qty <= threshold:
        return "LOW"
    return "OK"


def normalize_sku(text: str) -> str:
    """Map a raw Items-cell line to a canonical SKU. Reuses crm_sync._parse_items
    so both channels resolve identically, then applies aliases."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "chatbot"))
        from crm_sync import _parse_items  # type: ignore
        parsed = _parse_items(text)
        if parsed:
            canonical = parsed[0][0]  # "Series – Color"
            return SKU_ALIASES.get(canonical, canonical)
    except Exception:
        pass
    s = (text or "").strip()
    return SKU_ALIASES.get(s, s)


def _tab_titles() -> list:
    return [s["properties"]["title"] for s in _meta().get("sheets", [])]


def _first_tab_title() -> str:
    return _meta()["sheets"][0]["properties"]["title"]


def ensure_inventory_tab() -> None:
    if INVENTORY_TAB in _tab_titles():
        return
    _batch_update([{"addSheet": {"properties": {"title": INVENTORY_TAB}}}])


def seed(threshold: int = DEFAULT_THRESHOLD) -> int:
    ensure_inventory_tab()
    now = _now_pht()
    rows = [INVENTORY_COLUMNS]
    for series, color in CATALOG:
        qty = SEED_QTY.get((series, color), 0)
        rows.append([sku(series, color), series, color, qty,
                     compute_status(qty, threshold), threshold, now, ""])
    _values_update(f"'{INVENTORY_TAB}'!A1", rows)
    return len(rows) - 1


def read_inventory() -> dict:
    vals = _values_get(f"'{INVENTORY_TAB}'!A:H")
    out = {}
    for i, row in enumerate(vals[1:], start=2):
        row = row + [""] * (len(INVENTORY_COLUMNS) - len(row))
        key = row[0].strip()
        if not key:
            continue
        try:
            qty = int(row[3] or 0)
        except ValueError:
            qty = 0
        try:
            thr = int(row[5] or DEFAULT_THRESHOLD)
        except ValueError:
            thr = DEFAULT_THRESHOLD
        out[key] = {"row": i, "qty": qty, "status": row[4], "threshold": thr, "notes": row[7]}
    return out


def set_qty(sku_key: str, qty: int) -> int:
    sku_key = SKU_ALIASES.get(sku_key, sku_key)
    inv = read_inventory()
    if sku_key not in inv:
        raise KeyError(f"Unknown SKU: {sku_key!r}")
    r = inv[sku_key]["row"]
    thr = inv[sku_key]["threshold"]
    _values_update(f"'{INVENTORY_TAB}'!D{r}:G{r}",
                   [[qty, compute_status(qty, thr), thr, _now_pht()]])
    return qty


def adjust(sku_key: str, delta: int) -> int:
    sku_key = SKU_ALIASES.get(sku_key, sku_key)
    inv = read_inventory()
    if sku_key not in inv:
        raise KeyError(f"Unknown SKU: {sku_key!r}")
    return set_qty(sku_key, inv[sku_key]["qty"] + delta)


def add_order_columns() -> str:
    """Add 'Fulfilled' (K) + 'Decremented' (L) headers to the Orders tab.
    Only writes the header cells; leaves A:J untouched."""
    tab = _first_tab_title()
    existing = _values_get(f"'{tab}'!K1:L1")
    if existing and existing[0] and existing[0][0]:
        return f"{tab} (K/L already present: {existing[0]})"
    _values_update(f"'{tab}'!K1:L1", [["Fulfilled", "Decremented"]])
    return tab


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-auth", action="store_true")
    ap.add_argument("--init", action="store_true", help="create + seed the Inventory tab")
    ap.add_argument("--add-order-columns", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--adjust", nargs=2, metavar=("SKU", "DELTA"))
    args = ap.parse_args()

    try:
        _get_creds()
    except Exception as e:
        print(f"AUTH FAILED: {e}", file=sys.stderr)
        sys.exit(2)

    if args.check_auth:
        m = _meta()
        print(f"AUTH OK -- spreadsheet: {m['properties']['title']!r}; tabs: {_tab_titles()}")
        return
    if args.init:
        print(f"Inventory tab seeded: {seed()} SKUs.")
    if args.add_order_columns:
        print(f"Order columns ensured on tab: {add_order_columns()}")
    if args.adjust:
        print(f"{args.adjust[0]} -> {adjust(args.adjust[0], int(args.adjust[1]))}")
    if args.list or not any([args.init, args.add_order_columns, args.adjust]):
        inv = read_inventory()
        if not inv:
            print("(Inventory tab empty -- run --init)")
            return
        print(f"{'SKU':<26}{'QTY':>4}  STATUS")
        for k, v in inv.items():
            print(f"{k:<26}{v['qty']:>4}  {v['status']}")
        total = sum(v["qty"] for v in inv.values())
        lows = [k for k, v in inv.items() if v["status"] in ("LOW", "OOS")]
        print(f"-- total {total} units; {len(lows)} at/under threshold: {', '.join(lows) or 'none'}")


if __name__ == "__main__":
    main()
