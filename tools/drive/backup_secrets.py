"""
Backup secret files (.env, credentials.json, token.json) to Google Drive.

Uploads to DuberyMNL/Backups/secrets/ folder. Overwrites existing files with same name.

Usage:
    python tools/drive/backup_secrets.py
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

PROJECT_ROOT = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]
CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"
TOKEN_FILE = PROJECT_ROOT / "token.json"
BACKUP_FOLDER = "DuberyMNL/Backups/secrets"

SECRET_FILES = [
    PROJECT_ROOT / ".env",
    PROJECT_ROOT / "credentials.json",
    PROJECT_ROOT / "token.json",
    Path.home() / ".claude" / ".credentials.json",
]


def get_drive_service():
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
    return build("drive", "v3", credentials=creds)


def get_or_create_folder(service, folder_path: str) -> str:
    parts = [p for p in folder_path.split("/") if p]
    parent_id = "root"
    for part in parts:
        query = (
            f"name='{part}' and mimeType='application/vnd.google-apps.folder' "
            f"and '{parent_id}' in parents and trashed=false"
        )
        results = service.files().list(q=query, fields="files(id)").execute()
        files = results.get("files", [])
        if files:
            parent_id = files[0]["id"]
        else:
            folder_meta = {
                "name": part,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [parent_id],
            }
            folder = service.files().create(body=folder_meta, fields="id").execute()
            parent_id = folder["id"]
    return parent_id


def upload_or_update(service, file_path: Path, folder_id: str) -> dict:
    """Upload file, replacing existing file with same name if it exists."""
    query = (
        f"name='{file_path.name}' "
        f"and '{folder_id}' in parents and trashed=false"
    )
    results = service.files().list(q=query, fields="files(id)").execute()
    existing = results.get("files", [])

    media = MediaFileUpload(str(file_path), mimetype="application/octet-stream", resumable=True)

    if existing:
        # Update existing file
        uploaded = (
            service.files()
            .update(fileId=existing[0]["id"], media_body=media, fields="id,name,modifiedTime")
            .execute()
        )
    else:
        # Create new file
        file_metadata = {"name": file_path.name, "parents": [folder_id]}
        uploaded = (
            service.files()
            .create(body=file_metadata, media_body=media, fields="id,name,modifiedTime")
            .execute()
        )

    return uploaded


def main():
    service = get_drive_service()
    folder_id = get_or_create_folder(service, BACKUP_FOLDER)

    results = []
    for secret_file in SECRET_FILES:
        if not secret_file.exists():
            print(f"  SKIP: {secret_file.name} (not found)")
            continue
        uploaded = upload_or_update(service, secret_file, folder_id)
        print(f"  OK: {secret_file.name} -> Drive ({uploaded['id']})")
        results.append({"file": secret_file.name, "drive_id": uploaded["id"]})

    print(f"\n{len(results)} secret files backed up to Drive: {BACKUP_FOLDER}")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
