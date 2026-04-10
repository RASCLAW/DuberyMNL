"""
Batch upload chatbot image bank to Google Drive.

Creates folder structure under DuberyMNL/Chatbot Images/ and uploads all files.

Usage:
    python tools/drive/upload_chatbot_images.py
"""

import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

load_dotenv(Path(__file__).parent.parent.parent / ".env")

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]
TOKEN_FILE = Path(__file__).parent.parent.parent / "token.json"
PROJECT_ROOT = Path(__file__).parent.parent.parent


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


def upload_file(service, local_path, folder_id, drive_name):
    # Check if file already exists in folder
    query = f"name='{drive_name}' and '{folder_id}' in parents and trashed=false"
    existing = service.files().list(q=query, fields="files(id)").execute().get("files", [])
    if existing:
        print(f"  SKIP (exists): {drive_name}")
        return existing[0]["id"]

    suffix = local_path.suffix.lower()
    mimetype = "image/png" if suffix == ".png" else "image/jpeg"

    file_metadata = {"name": drive_name, "parents": [folder_id]}
    media = MediaFileUpload(str(local_path), mimetype=mimetype, resumable=True)
    uploaded = service.files().create(
        body=file_metadata, media_body=media, fields="id,name"
    ).execute()

    # Make readable by anyone with link
    service.permissions().create(
        fileId=uploaded["id"],
        body={"type": "anyone", "role": "reader"},
    ).execute()

    print(f"  OK: {drive_name}")
    return uploaded["id"]


# Image manifest: (local_path_relative_to_project, drive_subfolder, drive_filename)
MANIFEST = [
    # hero-shots (from cards/)
    ("dubery-landing/assets/cards/bandits-glossy-black-card-shot.jpg", "hero-shots", "bandits-glossy-black.jpg"),
    ("dubery-landing/assets/cards/bandits-matte-black-card-shot.jpg", "hero-shots", "bandits-matte-black.jpg"),
    ("dubery-landing/assets/cards/bandits-blue-card-shot.jpg", "hero-shots", "bandits-blue.jpg"),
    ("dubery-landing/assets/cards/bandits-green-card-shot.jpg", "hero-shots", "bandits-green.jpg"),
    ("dubery-landing/assets/cards/bandits-tortoise-card-shot.jpg", "hero-shots", "bandits-tortoise.jpg"),
    ("dubery-landing/assets/cards/outback-black-card-shot.jpg", "hero-shots", "outback-black.jpg"),
    ("dubery-landing/assets/cards/outback-blue-card-shot.jpg", "hero-shots", "outback-blue.jpg"),
    ("dubery-landing/assets/cards/outback-green-card-shot.jpg", "hero-shots", "outback-green.jpg"),
    ("dubery-landing/assets/cards/outback-red-card-shot.jpg", "hero-shots", "outback-red.jpg"),
    ("dubery-landing/assets/cards/rasta-brown-card-shot.jpg", "hero-shots", "rasta-brown.jpg"),
    ("dubery-landing/assets/cards/rasta-red-card-shot.jpg", "hero-shots", "rasta-red.jpg"),

    # model-shots
    ("contents/ready/model-shots/MODEL-BANDITS-GLOSSY-BLACK_output.png", "model-shots", "bandits-glossy-black.png"),
    ("contents/ready/model-shots/MODEL-BANDITS-GREEN_output.png", "model-shots", "bandits-green.png"),
    ("contents/ready/model-shots/MODEL-BANDITS-MATTE-BLACK_output.png", "model-shots", "bandits-matte-black.png"),
    ("contents/ready/model-shots/MODEL-BANDITS-TORTOISE_output.png", "model-shots", "bandits-tortoise.png"),
    ("contents/ready/model-shots/MODEL-OUTBACK-RED_output.png", "model-shots", "outback-red.png"),
    ("contents/ready/model-shots/MODEL-RASTA-BROWN_output.png", "model-shots", "rasta-brown.png"),

    # lifestyle
    ("contents/product/bandits-tortoise.png", "lifestyle", "bandits-tortoise-cafe.png"),
    ("contents/product/bandits-glossy-black.png", "lifestyle", "bandits-glossy-black-cafe.png"),
    ("contents/product/rasta-brown.png", "lifestyle", "rasta-brown-campus.png"),
    ("contents/product/outback-green.png", "lifestyle", "outback-green-river.png"),
    ("contents/ready/ugc/image_c0741e0d.png", "lifestyle", "bandits-matte-black-cafe.png"),
    ("contents/ready/ugc/image_e636a1f6.png", "lifestyle", "rasta-red-beach.png"),

    # collections
    ("contents/brand/BRAND-COLL-D_output.png", "collections", "bandits-series.png"),
    ("contents/brand/BRAND-COLL-B_output.png", "collections", "outback-series.png"),
    ("contents/carousel/BRAND-V2-004c_panel1.png", "collections", "rasta-series-1.png"),
    ("contents/carousel/BRAND-V2-004c_panel2.png", "collections", "rasta-series-2.png"),

    # brand
    ("contents/brand/BRAND-001_output.png", "brand", "feature-callout.png"),
    ("contents/brand/BRAND-BOLD-D_output.png", "brand", "see-clear.png"),
    ("contents/ready/brand-bold/BOLD-003_output.png", "brand", "made-for-the-grind.png"),
    ("contents/ready/brand/BRAND-V3-TOPBOTTOM_output.png", "brand", "outback-red-callout.png"),
    ("contents/ready/brand-bold/BOLD-010_output.png", "brand", "style-that-protects.png"),

    # customer-feedback
    ("dubery-landing/assets/feedback/feedback-1-bandits-green.jpg", "customer-feedback", "feedback-bandits-green.jpg"),
    ("dubery-landing/assets/feedback/feedback-2-outback-blue.jpg", "customer-feedback", "feedback-outback-blue.jpg"),
    ("dubery-landing/assets/feedback/feedback-3-rasta-red.jpg", "customer-feedback", "feedback-rasta-red.jpg"),
    ("dubery-landing/assets/feedback/feedback-4-bandits-tortoise.jpg", "customer-feedback", "feedback-bandits-tortoise.jpg"),
    ("dubery-landing/assets/feedback/feedback-5-outback-black.jpg", "customer-feedback", "feedback-outback-black.jpg"),
    ("dubery-landing/assets/feedback/feedback-6-outback-red.jpg", "customer-feedback", "feedback-outback-red.jpg"),
    ("dubery-landing/assets/feedback/feedback-7-outback-green.jpg", "customer-feedback", "feedback-outback-green.jpg"),
    ("dubery-landing/assets/feedback/feedback-8-bandits-black.jpg", "customer-feedback", "feedback-bandits-black.jpg"),

    # proof
    ("dubery-landing/assets/proofs/proof1.jpg", "proof", "cod-packages.jpg"),
    ("dubery-landing/assets/proofs/proof2.jpg", "proof", "branded-boxes-bundle.jpg"),
    ("dubery-landing/assets/proofs/proof3.jpg", "proof", "inventory-stock.jpg"),
    ("dubery-landing/assets/proofs/proof4.jpg", "proof", "jnt-shipments.jpg"),
    ("dubery-landing/assets/proofs/proof5.jpg", "proof", "labeled-inventory.jpg"),
    ("dubery-landing/assets/proofs/proof6.jpg", "proof", "lbc-dropoff.jpg"),

    # sales-support
    ("dubery-landing/assets/inclusions.png", "sales-support", "inclusions.png"),
    ("dubery-landing/assets/duberymnl-instapay-qr.jpg", "sales-support", "instapay-qr.jpg"),
]


def main():
    service = get_drive_service()

    # Get or create root: DuberyMNL/Chatbot Images
    print("Setting up folder structure...")
    root_id = get_or_create_folder(service, "DuberyMNL/Chatbot Images")
    print(f"Root folder ID: {root_id}\n")

    # Pre-create all subfolders
    subfolder_ids = {}
    subfolders = sorted(set(item[1] for item in MANIFEST))
    for sf in subfolders:
        sf_id = get_or_create_folder(service, sf, parent_id=root_id)
        subfolder_ids[sf] = sf_id

    # Upload all files
    results = {"uploaded": 0, "skipped": 0, "failed": 0, "files": {}}
    for local_rel, subfolder, drive_name in MANIFEST:
        local_path = PROJECT_ROOT / local_rel
        if not local_path.exists():
            print(f"  MISSING: {local_rel}")
            results["failed"] += 1
            continue

        try:
            file_id = upload_file(service, local_path, subfolder_ids[subfolder], drive_name)
            results["files"][f"{subfolder}/{drive_name}"] = file_id
            results["uploaded"] += 1
        except Exception as e:
            print(f"  FAIL: {drive_name} -- {e}")
            results["failed"] += 1

    print(f"\nDone: {results['uploaded']} uploaded, {results['failed']} failed")

    # Save manifest for chatbot reference
    manifest_path = PROJECT_ROOT / "tools" / "chatbot" / "drive_image_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(results["files"], f, indent=2)
    print(f"Manifest saved: {manifest_path}")


if __name__ == "__main__":
    main()
