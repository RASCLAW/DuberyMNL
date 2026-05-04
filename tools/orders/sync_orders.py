"""
Sync orders from Google Sheets → local orders/orders.json

Usage:
    python tools/orders/sync_orders.py

Output: orders/orders.json (array of order dicts, newest last)
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from googleapiclient.discovery import build

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from auth import get_credentials

load_dotenv(Path(__file__).parent.parent.parent / '.env')

SHEET_ID   = '1vS-yuFWovqHYWrFte4QXJLtH3Q2-BRDi6i9P4-vXbkA'
SHEET_TAB  = 'Orders'
OUT_FILE   = Path(__file__).parent.parent.parent / 'orders' / 'orders.json'


def fetch_orders():
    creds = get_credentials()
    svc = build('sheets', 'v4', credentials=creds)
    res = svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID,
        range=SHEET_TAB
    ).execute()
    rows = res.get('values', [])
    if not rows:
        return []
    headers = rows[0]
    return [
        dict(zip(headers, row + [''] * (len(headers) - len(row))))
        for row in rows[1:]
    ]


def main():
    print('Fetching orders from Sheets...')
    orders = fetch_orders()
    OUT_FILE.parent.mkdir(exist_ok=True)
    OUT_FILE.write_text(json.dumps(orders, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'{len(orders)} orders saved -> {OUT_FILE}')
    if orders:
        latest = orders[-1]
        print(f'Latest: [{latest.get("Timestamp")}] {latest.get("Name")} | {latest.get("Items")} | {latest.get("Total Amount")}'.encode('ascii', 'replace').decode())


if __name__ == '__main__':
    main()
