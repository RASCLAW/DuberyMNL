"""
Create the DuberyMNL CRM Google Sheet with 3 tabs:
- Leads: customer profiles with scoring
- Orders: order records linked to leads
- Lead Score Log: history of status changes

Run once. Idempotent -- skips if sheet with the same name already exists.
"""

import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

load_dotenv(Path(__file__).parent.parent.parent / ".env")

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]
TOKEN_FILE = Path(__file__).parent.parent.parent / "token.json"
SHEET_NAME = "DuberyMNL CRM"


def get_services():
    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return (
        build("sheets", "v4", credentials=creds),
        build("drive", "v3", credentials=creds),
    )


def find_existing(drive, name):
    query = f"name='{name}' and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false"
    results = drive.files().list(q=query, fields="files(id,name)").execute()
    files = results.get("files", [])
    return files[0] if files else None


def get_or_create_folder(drive, folder_name, parent_id="root"):
    query = (
        f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' "
        f"and '{parent_id}' in parents and trashed=false"
    )
    results = drive.files().list(q=query, fields="files(id)").execute()
    files = results.get("files", [])
    if files:
        return files[0]["id"]
    folder_meta = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    folder = drive.files().create(body=folder_meta, fields="id").execute()
    return folder["id"]


# Tab definitions: (name, headers, column widths)
TABS = {
    "Leads": [
        "Lead ID", "Name", "Phone", "Address", "Landmarks", "Source",
        "First Contact", "Last Contact", "Model Interest", "Status", "Notes",
    ],
    "Orders": [
        "Order ID", "Lead ID", "Items", "Quantity", "Total", "Discount Code",
        "Payment Method", "Delivery Preference", "Delivery Time",
        "Order Date", "Status",
    ],
    "Lead Score Log": [
        "Lead ID", "Timestamp", "Previous Status", "New Status", "Trigger",
    ],
}


def main():
    sheets, drive = get_services()

    existing = find_existing(drive, SHEET_NAME)
    if existing:
        print(f"Sheet already exists: {SHEET_NAME} (id={existing['id']})")
        print(f"URL: https://docs.google.com/spreadsheets/d/{existing['id']}")
        return

    print(f"Creating {SHEET_NAME}...")

    # Create the spreadsheet with all 3 tabs
    spreadsheet_body = {
        "properties": {"title": SHEET_NAME},
        "sheets": [
            {"properties": {"title": name, "index": i}}
            for i, name in enumerate(TABS.keys())
        ],
    }
    created = sheets.spreadsheets().create(body=spreadsheet_body, fields="spreadsheetId,sheets").execute()
    sheet_id = created["spreadsheetId"]
    print(f"Created sheet: {sheet_id}")

    # Write headers to each tab
    requests_batch = []
    for sheet in created["sheets"]:
        tab_name = sheet["properties"]["title"]
        tab_id = sheet["properties"]["sheetId"]
        headers = TABS[tab_name]

        # Write headers
        sheets.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=f"'{tab_name}'!A1",
            valueInputOption="RAW",
            body={"values": [headers]},
        ).execute()

        # Bold header row + freeze
        requests_batch.append({
            "repeatCell": {
                "range": {
                    "sheetId": tab_id,
                    "startRowIndex": 0,
                    "endRowIndex": 1,
                },
                "cell": {
                    "userEnteredFormat": {
                        "textFormat": {"bold": True},
                        "backgroundColor": {"red": 0.92, "green": 0.92, "blue": 0.92},
                    }
                },
                "fields": "userEnteredFormat(textFormat,backgroundColor)",
            }
        })
        requests_batch.append({
            "updateSheetProperties": {
                "properties": {
                    "sheetId": tab_id,
                    "gridProperties": {"frozenRowCount": 1},
                },
                "fields": "gridProperties.frozenRowCount",
            }
        })

    # Apply formatting in one batch
    sheets.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id,
        body={"requests": requests_batch},
    ).execute()

    # Move to DuberyMNL folder in Drive
    duberymnl_folder_id = get_or_create_folder(drive, "DuberyMNL")
    file_info = drive.files().get(fileId=sheet_id, fields="parents").execute()
    prev_parents = ",".join(file_info.get("parents", []))
    drive.files().update(
        fileId=sheet_id,
        addParents=duberymnl_folder_id,
        removeParents=prev_parents,
        fields="id,parents",
    ).execute()

    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}"
    print(f"\nDone!")
    print(f"Sheet ID: {sheet_id}")
    print(f"URL: {url}")

    # Save ID for chatbot reference
    output = {
        "sheet_id": sheet_id,
        "sheet_name": SHEET_NAME,
        "url": url,
        "tabs": {k: v for k, v in TABS.items()},
    }
    manifest_path = Path(__file__).parent.parent / "chatbot" / "crm_sheet_info.json"
    with open(manifest_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"Manifest saved: {manifest_path}")


if __name__ == "__main__":
    main()
