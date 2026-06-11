"""
Mark an order's Status = DELIVERED in the DuberyMNL Orders sheet (col K).

The Orders sheet is the source of truth. Its Status column (K) has NO header row
(see sync_orders.py), so this writes the raw cell directly via the Sheets REST API.
Transport = requests + bearer token: googleapiclient/httplib2 TIMES OUT on
sheets.googleapis.com from this laptop (WinError 10060), so write_sheet.py's
googleapiclient path is unreliable here -- requests works (same as sync_orders.py).

Usage:
    python tools/orders/mark_delivered.py --name "Roy Cañete" --dry-run
    python tools/orders/mark_delivered.py --name "Roy Cañete"          # write
    python tools/orders/mark_delivered.py --name "Roy" --phone 0949    # disambiguate
    python tools/orders/mark_delivered.py --row 10                     # write K10 directly

After writing, re-run sync_orders.py to refresh orders.json, then inventory_report.py.
NOTE: orders dated on/before inventory.json `_as_of` do NOT auto-decrement `remaining`
(compute_report uses strict odt > as_of) -- reconcile on_hand manually for any
pre-baseline pending pair that was kept in on_hand until delivery.
"""

import argparse
import io
import re
import sys
from pathlib import Path
from urllib.parse import quote

import requests
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from auth import get_credentials  # noqa: E402

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
load_dotenv(Path(__file__).parent.parent.parent / ".env")

SHEET_ID = "1vS-yuFWovqHYWrFte4QXJLtH3Q2-BRDi6i9P4-vXbkA"
SHEET_TAB = "Orders"
STATUS_COL = "K"          # col K (index 10) -- manual Status, no header
NAME_IDX = 1              # col B = Name
PHONE_IDX = 2            # col C = Phone
STATUS_IDX = 10          # col K = Status


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def fetch_rows(token: str) -> list[list[str]]:
    rng = quote(f"{SHEET_TAB}!A:L", safe="")
    r = requests.get(
        f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{rng}",
        headers={"Authorization": f"Bearer {token}"}, timeout=45,
    )
    r.raise_for_status()
    return r.json().get("values", [])


def write_status(token: str, sheet_row: int, value: str) -> dict:
    cell = f"{SHEET_TAB}!{STATUS_COL}{sheet_row}"
    rng = quote(cell, safe="")
    r = requests.put(
        f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{rng}",
        params={"valueInputOption": "USER_ENTERED"},
        headers={"Authorization": f"Bearer {token}"},
        json={"values": [[value]]}, timeout=45,
    )
    r.raise_for_status()
    return r.json()


def main():
    ap = argparse.ArgumentParser(description="Mark an order DELIVERED in the Orders sheet")
    ap.add_argument("--name", help="Customer name (case-insensitive substring match)")
    ap.add_argument("--phone", help="Phone substring to disambiguate")
    ap.add_argument("--row", type=int, help="Write this 1-based sheet row directly (skips name match)")
    ap.add_argument("--status", default="DELIVERED", help="Status value to write (default DELIVERED)")
    ap.add_argument("--dry-run", action="store_true", help="Show the matched row; do not write")
    args = ap.parse_args()

    if not args.row and not args.name:
        ap.error("provide --name or --row")

    token = get_credentials().token
    rows = fetch_rows(token)
    if not rows:
        print("No rows returned from the Orders sheet.")
        sys.exit(1)

    if args.row:
        targets = [args.row]
    else:
        name_q = _norm(args.name)
        targets = []
        for i, row in enumerate(rows[1:], start=2):  # 1-based, skip header
            row = row + [""] * (12 - len(row))
            if name_q not in _norm(row[NAME_IDX]):
                continue
            if args.phone and args.phone.strip() not in (row[PHONE_IDX] or ""):
                continue
            cur = (row[STATUS_IDX] or "").strip()
            flag = "  <-- already DELIVERED" if cur.upper() == "DELIVERED" else ""
            print(f"  row {i}: {row[NAME_IDX]} | {row[4]} | {row[7]} | Status={cur or '(blank)'}{flag}")
            if cur.upper() != "DELIVERED":
                targets.append(i)

        if not targets:
            print(f"No writable match for name '{args.name}' (already delivered, or not found).")
            sys.exit(1)
        if len(targets) > 1:
            print(f"\n{len(targets)} matches -- refine with --phone or pass --row. Nothing written.")
            sys.exit(1)

    row_n = targets[0]
    if args.dry_run:
        print(f"\n[dry-run] would set {SHEET_TAB}!{STATUS_COL}{row_n} = '{args.status}'")
        return

    res = write_status(token, row_n, args.status)
    print(f"\nWrote {res.get('updatedCells', '?')} cell -> {SHEET_TAB}!{STATUS_COL}{row_n} = '{args.status}'")


if __name__ == "__main__":
    main()
