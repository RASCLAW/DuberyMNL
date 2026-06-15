"""
Idempotent setup: ensure the `content_calendar` tab exists in the Master
spreadsheet (GOOGLE_SHEETS_SPREADSHEET_ID) with the right headers, bold + frozen.

Safe to re-run: creates the tab only if missing, then (re)writes the header row.

Run:
    python tools/moments/setup_calendar_sheet.py
"""

from moment_store import HEADERS, SHEET_NAME, get_service, spreadsheet_id


def main():
    service = get_service()
    sid = spreadsheet_id()

    meta = service.spreadsheets().get(spreadsheetId=sid).execute()
    tabs = {s["properties"]["title"]: s["properties"]["sheetId"] for s in meta["sheets"]}

    if SHEET_NAME not in tabs:
        print(f"Creating tab '{SHEET_NAME}'...")
        resp = service.spreadsheets().batchUpdate(
            spreadsheetId=sid,
            body={"requests": [{"addSheet": {"properties": {"title": SHEET_NAME}}}]},
        ).execute()
        sheet_id = resp["replies"][0]["addSheet"]["properties"]["sheetId"]
    else:
        sheet_id = tabs[SHEET_NAME]
        print(f"Tab '{SHEET_NAME}' already exists (id={sheet_id}).")

    # Write/refresh the header row.
    service.spreadsheets().values().update(
        spreadsheetId=sid,
        range=f"{SHEET_NAME}!A1",
        valueInputOption="USER_ENTERED",
        body={"values": [HEADERS]},
    ).execute()

    # Bold the header row + freeze it.
    service.spreadsheets().batchUpdate(
        spreadsheetId=sid,
        body={"requests": [
            {"updateSheetProperties": {
                "properties": {"sheetId": sheet_id, "gridProperties": {"frozenRowCount": 1}},
                "fields": "gridProperties.frozenRowCount",
            }},
            {"repeatCell": {
                "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1},
                "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
                "fields": "userEnteredFormat.textFormat.bold",
            }},
        ]},
    ).execute()

    print(f"Done. '{SHEET_NAME}' ready with {len(HEADERS)} columns: {', '.join(HEADERS)}")


if __name__ == "__main__":
    main()
