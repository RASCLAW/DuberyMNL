"""
Sync orders from Google Sheets -> orders/orders.json

Usage:
    python tools/orders/sync_orders.py

Output: orders/orders.json (array of order dicts, newest last)

Transport: requests + bearer token against the Sheets REST API. googleapiclient/
httplib2 currently TIMES OUT on sheets.googleapis.com from this laptop
(WinError 10060) -- see memory reference_googleapi_httplib2_fallback. requests works.
Auth creds still come from tools/auth.py::get_credentials() (headless-safe refresh).
"""

import json
import sys
import io
from pathlib import Path
from urllib.parse import quote

import requests
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from auth import get_credentials  # noqa: E402

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
load_dotenv(Path(__file__).parent.parent.parent / '.env')

SHEET_ID  = '1vS-yuFWovqHYWrFte4QXJLtH3Q2-BRDi6i9P4-vXbkA'
SHEET_TAB = 'Orders'
OUT_FILE  = Path(__file__).parent.parent.parent / 'orders' / 'orders.json'


def fetch_orders():
    token = get_credentials().token
    rng = quote(f'{SHEET_TAB}!A:L', safe='')  # explicit A:L -- col K + L have no headers
    r = requests.get(
        f'https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{rng}',
        headers={'Authorization': f'Bearer {token}'}, timeout=45,
    )
    r.raise_for_status()
    rows = r.json().get('values', [])
    if not rows:
        return []
    headers = rows[0]
    # Append synthetic headers for col K + L (manual status, pickup timestamp)
    # so they survive the dict(zip(...)) flattening.
    while len(headers) < 12:
        headers.append('Status' if len(headers) == 10 else 'PickupTimestamp')
    return [
        dict(zip(headers, row + [''] * (len(headers) - len(row))))
        for row in rows[1:]
    ]


def main():
    print('Fetching orders from Sheets (requests transport)...')
    orders = fetch_orders()
    OUT_FILE.parent.mkdir(exist_ok=True)
    OUT_FILE.write_text(json.dumps(orders, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'{len(orders)} orders saved -> {OUT_FILE}')
    if orders:
        latest = orders[-1]
        print(f'Latest: [{latest.get("Timestamp")}] {latest.get("Name")} | {latest.get("Items")} | {latest.get("Total Amount")}'.encode('ascii', 'replace').decode())


if __name__ == '__main__':
    main()
