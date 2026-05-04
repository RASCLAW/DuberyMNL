"""
Upload a local image file to Google Drive.

Creates the target folder if it doesn't exist. Returns the Drive file ID and shareable URL.

Usage:
    python upload_image.py --file .tmp/image.jpg --folder "DuberyMNL/Images"

Output: JSON with drive_file_id and drive_url.
"""

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from auth import get_credentials

load_dotenv(Path(__file__).parent.parent.parent / ".env")


def get_drive_service():
    return build("drive", "v3", credentials=get_credentials())


def get_or_create_folder(service, folder_path: str) -> str:
    """Traverse/create nested folder path in Drive. Returns final folder ID."""
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


def upload_file(service, file_path: Path, folder_id: str) -> dict:
    """Upload file to Drive folder. Returns file metadata."""
    file_metadata = {
        "name": file_path.name,
        "parents": [folder_id],
    }
    media = MediaFileUpload(str(file_path), mimetype="image/jpeg", resumable=True)
    uploaded = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id,name,webViewLink,webContentLink")
        .execute()
    )

    # Make file readable by anyone with the link
    service.permissions().create(
        fileId=uploaded["id"],
        body={"type": "anyone", "role": "reader"},
    ).execute()

    return uploaded


def main():
    parser = argparse.ArgumentParser(description="Upload image to Google Drive")
    parser.add_argument("--file", required=True, help="Local image file path")
    parser.add_argument("--folder", required=True, help='Drive folder path e.g. "DuberyMNL/Images"')
    args = parser.parse_args()

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: file not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    service = get_drive_service()
    folder_id = get_or_create_folder(service, args.folder)
    uploaded = upload_file(service, file_path, folder_id)

    output = {
        "success": True,
        "drive_file_id": uploaded["id"],
        "drive_url": uploaded.get("webViewLink", ""),
        "file_name": uploaded["name"],
        "folder_id": folder_id,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
