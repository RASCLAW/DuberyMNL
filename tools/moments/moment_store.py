"""
Shared core for the DuberyMNL content calendar ("Moment Engine"), backed by a
Google Sheet tab. Imported by the CLI helpers in this directory.

The calendar lives in the `content_calendar` tab of the spreadsheet identified by
GOOGLE_SHEETS_SPREADSHEET_ID (.env). One row per moment, keyed by `id`.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from googleapiclient.discovery import build

# tools/ on path so we can reuse the shared OAuth helper
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from auth import get_credentials  # noqa: E402

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

SHEET_NAME = "content_calendar"
HEADERS = [
    "id", "title", "type", "window_start", "window_end", "relevance",
    "angle", "format", "source", "status", "notes", "added", "lead_time_days",
]


def spreadsheet_id() -> str:
    sid = os.environ.get("GOOGLE_SHEETS_SPREADSHEET_ID", "")
    if not sid:
        raise SystemExit("GOOGLE_SHEETS_SPREADSHEET_ID is not set in .env")
    return sid


def get_service():
    return build("sheets", "v4", credentials=get_credentials())


def _col_letter(idx: int) -> str:
    """0-based column index -> A1 letter (supports beyond Z)."""
    letters = ""
    idx += 1
    while idx:
        idx, rem = divmod(idx - 1, 26)
        letters = chr(ord("A") + rem) + letters
    return letters


def read_moments(service=None) -> list[dict]:
    """Return all calendar rows as dicts. Empty list if the tab has no data."""
    service = service or get_service()
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id(), range=SHEET_NAME)
        .execute()
    )
    values = result.get("values", [])
    if not values:
        return []
    headers = values[0]
    return [
        dict(zip(headers, row + [""] * (len(headers) - len(row))))
        for row in values[1:]
    ]


def upsert_moment(data: dict, dry_run: bool = False, service=None) -> dict:
    """Insert a new moment or update the existing row with the same `id`.

    Returns a small result dict. On update, only the provided fields change.
    """
    if not data.get("id"):
        raise ValueError("moment data must include a non-empty 'id'")

    service = service or get_service()
    sid = spreadsheet_id()

    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=sid, range=SHEET_NAME)
        .execute()
    )
    values = result.get("values", [])
    headers = values[0] if values else HEADERS
    id_idx = headers.index("id")

    existing_rownum = None
    for i, row in enumerate(values[1:], start=2):  # 1-based, skip header
        padded = row + [""] * (len(headers) - len(row))
        if padded[id_idx] == data["id"]:
            existing_rownum = i
            break

    if dry_run:
        return {
            "action": "update" if existing_rownum else "append",
            "id": data["id"],
            "dry_run": True,
        }

    if existing_rownum:
        updates = []
        for key, val in data.items():
            if key in headers:
                col = _col_letter(headers.index(key))
                updates.append({
                    "range": f"{SHEET_NAME}!{col}{existing_rownum}",
                    "values": [[val]],
                })
        if updates:
            service.spreadsheets().values().batchUpdate(
                spreadsheetId=sid,
                body={"valueInputOption": "USER_ENTERED", "data": updates},
            ).execute()
        return {"action": "update", "id": data["id"], "row": existing_rownum,
                "fields_changed": len(updates)}

    row = [data.get(h, "") for h in headers]
    service.spreadsheets().values().append(
        spreadsheetId=sid,
        range=SHEET_NAME,
        valueInputOption="USER_ENTERED",
        body={"values": [row]},
    ).execute()
    return {"action": "append", "id": data["id"]}
