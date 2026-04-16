"""
Upload every pick in the chatbot image bank to Google Drive and write
the lh3 CDN URL back into the bank JSON.

Idempotent: skips files already uploaded (matched by name within the
target Drive folder). Re-runs are safe.

Usage:
    python tools/drive/upload_bank_to_drive.py
    python tools/drive/upload_bank_to_drive.py --dry-run
    python tools/drive/upload_bank_to_drive.py --bank contents/assets/other-bank.json
"""

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

PROJECT_ROOT = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]
TOKEN_FILE = PROJECT_ROOT / "token.json"
DEFAULT_BANK = PROJECT_ROOT / "contents" / "assets" / "chatbot-image-bank-2026-04.json"
DRIVE_ROOT = "DuberyMNL/Chatbot Bank 2026-04"

# lh3 CDN URL format (works for publicly-shared Drive files)
CDN_BASE = "https://lh3.googleusercontent.com/d"


def get_drive_service():
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            print("Error: token.json missing or invalid, need OAuth flow", file=sys.stderr)
            sys.exit(1)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return build("drive", "v3", credentials=creds)


def get_or_create_folder(service, folder_path, parent_id="root"):
    parts = [p for p in folder_path.split("/") if p]
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
            print(f"  Created folder: {part}")
    return parent_id


def upload_or_get(service, local_path: Path, folder_id: str, drive_name: str) -> str:
    """Upload file if missing, else return existing file id. Returns the Drive file id."""
    query = f"name='{drive_name}' and '{folder_id}' in parents and trashed=false"
    existing = service.files().list(q=query, fields="files(id)").execute().get("files", [])
    if existing:
        return existing[0]["id"]

    suffix = local_path.suffix.lower()
    mimetype = "image/png" if suffix == ".png" else "image/jpeg"

    media = MediaFileUpload(str(local_path), mimetype=mimetype, resumable=True)
    uploaded = service.files().create(
        body={"name": drive_name, "parents": [folder_id]},
        media_body=media,
        fields="id",
    ).execute()

    service.permissions().create(
        fileId=uploaded["id"],
        body={"type": "anyone", "role": "reader"},
    ).execute()

    return uploaded["id"]


def main():
    parser = argparse.ArgumentParser(description="Upload chatbot image bank to Drive")
    parser.add_argument("--bank", type=str, default=str(DEFAULT_BANK))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    bank_path = Path(args.bank)
    if not bank_path.exists():
        print(f"Error: bank not found at {bank_path}", file=sys.stderr)
        sys.exit(1)

    bank = json.loads(bank_path.read_text(encoding="utf-8"))
    picks = bank.get("picks", [])
    if not picks:
        print(f"Error: bank has no picks", file=sys.stderr)
        sys.exit(1)

    print(f"Bank: {bank_path}")
    print(f"Picks: {len(picks)}")
    print(f"Drive root: {DRIVE_ROOT}")

    if args.dry_run:
        missing = [p for p in picks if not (PROJECT_ROOT / p["path"]).exists()]
        print(f"Files missing: {len(missing)}")
        print("[DRY RUN] no upload")
        return

    service = get_drive_service()
    root_id = get_or_create_folder(service, DRIVE_ROOT)

    # Pre-create subfolders: {type}/{model}
    subfolder_ids = {}

    stats = {"uploaded": 0, "skipped": 0, "failed": 0}
    for i, pick in enumerate(picks, 1):
        local_path = PROJECT_ROOT / pick["path"]
        if not local_path.exists():
            print(f"  [{i}/{len(picks)}] MISSING: {pick['path']}")
            stats["failed"] += 1
            continue

        # Use {type}/{model} as subfolder (e.g. person/bandits-matte-black)
        subfolder = f"{pick['type']}/{pick['model']}"
        if subfolder not in subfolder_ids:
            subfolder_ids[subfolder] = get_or_create_folder(
                service, subfolder, parent_id=root_id
            )

        # Use the filename as the Drive name (collision-proof because subfolder is per-variant)
        drive_name = pick["file"]

        try:
            file_id = upload_or_get(
                service, local_path, subfolder_ids[subfolder], drive_name
            )
            url = f"{CDN_BASE}/{file_id}"

            # Check if already had this URL (re-run)
            was_new = pick.get("url") != url
            pick["url"] = url
            pick["drive_file_id"] = file_id

            if was_new:
                stats["uploaded"] += 1
                print(f"  [{i}/{len(picks)}] OK: {drive_name} -> {file_id}")
            else:
                stats["skipped"] += 1
                print(f"  [{i}/{len(picks)}] SKIP (already in bank): {drive_name}")

        except Exception as e:
            print(f"  [{i}/{len(picks)}] FAIL: {drive_name} -- {e}", file=sys.stderr)
            stats["failed"] += 1

    # Write enriched bank back
    bank_path.write_text(
        json.dumps(bank, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\nDone: {stats['uploaded']} uploaded, {stats['skipped']} skipped, {stats['failed']} failed")
    print(f"Bank updated: {bank_path}")


if __name__ == "__main__":
    main()
