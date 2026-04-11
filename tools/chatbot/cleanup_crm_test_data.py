"""
Delete TEST_ rows from the DuberyMNL CRM Google Sheet.

Scans 4 tabs and deletes rows where the lead identifier starts with "TEST_"
(rows written by the /chat-test webapp, which enforces a TEST_ prefix).

- Leads:          column A (Lead ID)
- Orders:         column B (Lead ID)  -- column A is Order ID (ORD-...)
- Lead Score Log: column A (Lead ID)
- Conversations:  column A (sender_id)

Usage:
    python tools/chatbot/cleanup_crm_test_data.py           # dry-run (default)
    python tools/chatbot/cleanup_crm_test_data.py --confirm # actually deletes

Auth: OAuth2 via token.json at the project root (same pattern as read_sheet.py).
The sheet must be accessible by the Google account the token was issued for.
"""

import argparse
import sys
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SHEET_ID = "1wVn9WGdY8pK7c68pZpnNSWoNkhhZvYUywcGqLCqcewA"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
TOKEN_FILE = Path(__file__).parent.parent.parent / "token.json"

# tab_name -> (0-indexed column to check, range to read)
TAB_FILTERS = {
    "Leads":          {"check_col": 0, "read_range": "A:K"},
    "Orders":         {"check_col": 1, "read_range": "A:K"},
    "Lead Score Log": {"check_col": 0, "read_range": "A:E"},
    "Conversations":  {"check_col": 0, "read_range": "A:E"},
}


def get_service():
    if not TOKEN_FILE.exists():
        raise FileNotFoundError(f"token.json not found at {TOKEN_FILE}")
    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE))
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return build("sheets", "v4", credentials=creds, cache_discovery=False)


def get_sheet_metadata(service):
    """Return {tab_name: numeric_sheet_id} for batchUpdate requests."""
    meta = service.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
    return {s["properties"]["title"]: s["properties"]["sheetId"] for s in meta["sheets"]}


def find_test_rows(service, tab_name, filter_cfg):
    """Return (list of 0-indexed row numbers that match TEST_, total non-header rows)."""
    range_str = f"'{tab_name}'!{filter_cfg['read_range']}"
    result = service.spreadsheets().values().get(
        spreadsheetId=SHEET_ID, range=range_str
    ).execute()
    values = result.get("values", [])
    if not values:
        return [], 0
    check_col = filter_cfg["check_col"]
    matches = []
    # Skip header (index 0)
    for i, row in enumerate(values[1:], start=1):
        if len(row) > check_col and str(row[check_col]).startswith("TEST_"):
            matches.append(i)
    return matches, len(values) - 1


def delete_rows(service, tab_sheet_id, row_indices):
    """Delete rows by 0-indexed position. Sorts descending so indices don't shift."""
    if not row_indices:
        return
    sorted_desc = sorted(row_indices, reverse=True)
    requests = [
        {
            "deleteDimension": {
                "range": {
                    "sheetId": tab_sheet_id,
                    "dimension": "ROWS",
                    "startIndex": idx,
                    "endIndex": idx + 1,
                }
            }
        }
        for idx in sorted_desc
    ]
    service.spreadsheets().batchUpdate(
        spreadsheetId=SHEET_ID, body={"requests": requests}
    ).execute()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--confirm", action="store_true",
        help="Actually delete rows. Without this flag, dry-run only."
    )
    args = parser.parse_args()

    service = get_service()
    metadata = get_sheet_metadata(service)

    print(f"DuberyMNL CRM sheet: {SHEET_ID}")
    print(f"Mode: {'DELETE' if args.confirm else 'DRY-RUN (no changes)'}")
    print()

    total_to_delete = 0
    per_tab_results = []

    for tab_name, filter_cfg in TAB_FILTERS.items():
        if tab_name not in metadata:
            print(f"  [skip] Tab '{tab_name}' not found in sheet")
            continue

        matches, total = find_test_rows(service, tab_name, filter_cfg)
        per_tab_results.append((tab_name, len(matches), total))
        print(f"  {tab_name:16s}  {len(matches):>4d} TEST_ rows / {total:>4d} total")
        total_to_delete += len(matches)

        if args.confirm and matches:
            delete_rows(service, metadata[tab_name], matches)
            print(f"                    -> deleted {len(matches)} rows")

    print()
    verb = "deleted" if args.confirm else "would be deleted"
    print(f"Total: {total_to_delete} rows {verb}")

    if not args.confirm and total_to_delete > 0:
        print()
        print("Dry-run complete. Re-run with --confirm to actually delete:")
        print("  python tools/chatbot/cleanup_crm_test_data.py --confirm")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
