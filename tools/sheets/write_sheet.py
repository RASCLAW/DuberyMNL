"""
Append or update rows in a Google Sheets tab.

Usage:
    # Append a new row
    python write_sheet.py --sheet captions --action append --data '{"Vibe":"commuter","Caption":"...","Status":"PENDING"}'

    # Update rows matching a filter (e.g. set Status=APPROVED where ID=42)
    python write_sheet.py --sheet captions --action update --filter "ID=42" --data '{"Status":"APPROVED"}'

Output: JSON result to stdout.
"""

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

load_dotenv(Path(__file__).parent.parent.parent / ".env")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CREDENTIALS_FILE = Path(__file__).parent.parent.parent / "credentials.json"
TOKEN_FILE = Path(__file__).parent.parent.parent / "token.json"


def get_sheets_service():
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return build("sheets", "v4", credentials=creds)


def get_headers(service, spreadsheet_id: str, sheet_name: str) -> list[str]:
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=f"{sheet_name}!1:1")
        .execute()
    )
    values = result.get("values", [])
    return values[0] if values else []


def append_row(sheet_name: str, data: dict) -> dict:
    spreadsheet_id = os.environ["GOOGLE_SHEETS_SPREADSHEET_ID"]
    service = get_sheets_service()

    headers = get_headers(service, spreadsheet_id, sheet_name)
    if not headers:
        raise ValueError(f"Sheet '{sheet_name}' has no headers. Seed the sheet first.")

    row = [data.get(h, "") for h in headers]

    result = (
        service.spreadsheets()
        .values()
        .append(
            spreadsheetId=spreadsheet_id,
            range=sheet_name,
            valueInputOption="USER_ENTERED",
            body={"values": [row]},
        )
        .execute()
    )
    return {"action": "append", "sheet": sheet_name, "result": result.get("updates", {})}


def update_rows(sheet_name: str, filter_expr: str, data: dict) -> dict:
    """Update specific columns for all rows matching filter_expr."""
    spreadsheet_id = os.environ["GOOGLE_SHEETS_SPREADSHEET_ID"]
    service = get_sheets_service()

    full_range = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=sheet_name)
        .execute()
    )
    values = full_range.get("values", [])
    if not values:
        return {"action": "update", "rows_updated": 0}

    headers = values[0]
    filter_key, filter_value = filter_expr.split("=", 1)
    filter_key = filter_key.strip()
    filter_value = filter_value.strip()

    if filter_key not in headers:
        raise ValueError(f"Filter column '{filter_key}' not found in headers: {headers}")

    filter_col_idx = headers.index(filter_key)
    updates = []

    for i, row in enumerate(values[1:], start=2):  # row index is 1-based, skip header
        row_padded = row + [""] * (len(headers) - len(row))
        if row_padded[filter_col_idx] == filter_value:
            for col_name, new_value in data.items():
                if col_name in headers:
                    col_idx = headers.index(col_name)
                    col_letter = chr(ord("A") + col_idx)
                    updates.append({
                        "range": f"{sheet_name}!{col_letter}{i}",
                        "values": [[new_value]],
                    })

    if updates:
        service.spreadsheets().values().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"valueInputOption": "USER_ENTERED", "data": updates},
        ).execute()

    return {"action": "update", "sheet": sheet_name, "rows_updated": len(updates)}


def main():
    parser = argparse.ArgumentParser(description="Write or update rows in Google Sheets")
    parser.add_argument("--sheet", required=True, help="Sheet tab name")
    parser.add_argument("--action", required=True, choices=["append", "update"])
    parser.add_argument("--data", required=True, help="JSON object of column:value pairs")
    parser.add_argument("--filter", help='For update: filter expression e.g. "ID=42"')
    args = parser.parse_args()

    data = json.loads(args.data)

    if args.action == "append":
        result = append_row(args.sheet, data)
    elif args.action == "update":
        if not args.filter:
            print("Error: --filter is required for update action", file=sys.stderr)
            sys.exit(1)
        result = update_rows(args.sheet, args.filter, data)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
