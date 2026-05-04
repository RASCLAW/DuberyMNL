"""
Read rows from a Google Sheets tab.

Usage:
    python read_sheet.py --sheet captions --filter "Status=APPROVED"
    python read_sheet.py --sheet brand
    python read_sheet.py --sheet leads --filter "Status=NEW"

Output: JSON array of row dicts to stdout.
"""

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from googleapiclient.discovery import build

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from auth import get_credentials

load_dotenv(Path(__file__).parent.parent.parent / ".env")


def get_sheets_service():
    return build("sheets", "v4", credentials=get_credentials())


def read_sheet(sheet_name: str, filter_expr: str = None) -> list[dict]:
    spreadsheet_id = os.environ["GOOGLE_SHEETS_SPREADSHEET_ID"]
    service = get_sheets_service()

    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=sheet_name)
        .execute()
    )

    values = result.get("values", [])
    if not values:
        return []

    headers = values[0]
    rows = [dict(zip(headers, row + [""] * (len(headers) - len(row)))) for row in values[1:]]

    if filter_expr:
        key, value = filter_expr.split("=", 1)
        rows = [r for r in rows if r.get(key.strip()) == value.strip()]

    return rows


def main():
    parser = argparse.ArgumentParser(description="Read rows from a Google Sheets tab")
    parser.add_argument("--sheet", required=True, help="Sheet tab name (e.g. captions, leads)")
    parser.add_argument("--filter", help='Filter expression e.g. "Status=APPROVED"')
    args = parser.parse_args()

    rows = read_sheet(args.sheet, args.filter)
    print(json.dumps(rows, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
