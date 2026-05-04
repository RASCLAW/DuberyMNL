"""
Backup secret files (.env, credentials.json, token.json) to Google Drive.

Uploads to DuberyMNL/Backups/secrets/ folder. Overwrites existing files with same name,
then pins the new revision as keepForever=True so Drive never auto-deletes it.

Rollback: Drive UI -> right-click file -> Manage versions -> pick a pinned revision.

Usage:
    python tools/drive/backup_secrets.py
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

PROJECT_ROOT = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from auth import get_credentials

BACKUP_FOLDER = "DuberyMNL/Backups/secrets"

SECRET_FILES = [
    PROJECT_ROOT / ".env",
    PROJECT_ROOT / "credentials.json",
    PROJECT_ROOT / "token.json",
    Path.home() / ".claude" / ".credentials.json",
]


def get_drive_service():
    return build("drive", "v3", credentials=get_credentials())


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


def pin_latest_revision(service, file_id: str) -> str | None:
    """Mark the latest revision of a file as keepForever=True.

    Drive auto-deletes revisions after 30 days or 100 revisions by default.
    keepForever=True pins a revision permanently (up to 200 per file).
    Returns the pinned revision ID, or None if pinning failed.
    """
    try:
        revisions = (
            service.revisions()
            .list(fileId=file_id, fields="revisions(id,modifiedTime,keepForever)")
            .execute()
            .get("revisions", [])
        )
        if not revisions:
            return None
        latest = revisions[-1]  # Drive returns revisions in chronological order
        if latest.get("keepForever"):
            return latest["id"]  # already pinned, no-op
        service.revisions().update(
            fileId=file_id,
            revisionId=latest["id"],
            body={"keepForever": True},
        ).execute()
        return latest["id"]
    except Exception as e:
        print(f"    WARN: could not pin revision for {file_id}: {e}")
        return None


def upload_or_update(service, file_path: Path, folder_id: str) -> dict:
    """Upload file, replacing existing file with same name if it exists.

    After upload, pins the new revision as keepForever=True so Drive
    never auto-deletes it (rollback protection).
    """
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

    # Pin the new revision so Drive never auto-deletes it
    pinned_rev = pin_latest_revision(service, uploaded["id"])
    if pinned_rev:
        uploaded["pinned_revision"] = pinned_rev

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
