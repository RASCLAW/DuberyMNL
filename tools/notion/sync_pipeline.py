"""
DuberyMNL Pipeline → Notion + Google Sheets Sync

Reads .tmp/pipeline.json and .tmp/rejected_captions.json
and upserts each caption as a row in the Notion pipeline database
and overwrites the DuberyMNL Pipeline Google Sheet.

Run:
    python tools/notion/sync_pipeline.py
"""

import os
import sys
import json
import argparse
import requests
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent.parent
TMP_DIR = PROJECT_DIR / ".tmp"
ENV_PATH = PROJECT_DIR / ".env"

NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

SHEET_ID = "1LVshSQP5Ob9RNqt35PoSjbUuAiu9dneyHHhUiUZKYrg"
SHEET_HEADERS = [
    "Caption ID", "Status", "Headline", "Caption Text", "Vibe",
    "Angle", "Visual Anchor", "Rating", "Product Ref", "Card Image", "Image URL", "Image Status",
    "Has Image", "Has Prompt", "Image Feedback", "Notes", "Prompt", "Source",
]


# ── Config ──────────────────────────────────────────────────────────────────

def load_env():
    env = {}
    if not ENV_PATH.exists():
        return env
    for line in ENV_PATH.read_text().splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"\'')
    return env


# ── Notion API helpers ───────────────────────────────────────────────────────

def notion_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def ensure_properties(token, db_id):
    """Add missing properties to the Notion database."""
    required = {
        "Caption ID":     {"rich_text": {}},
        "Status":         {"select": {}},
        "Vibe":           {"rich_text": {}},
        "Angle":          {"select": {}},
        "Visual Anchor":  {"select": {}},
        "Rating":         {"number": {}},
        "Caption Text":   {"rich_text": {}},
        "Notes":          {"rich_text": {}},
        "Prompt":         {"rich_text": {}},
        "Image URL":      {"files": {}},
        "Image Status":   {"select": {}},
        "Image Feedback": {"rich_text": {}},
        "Has Prompt":     {"checkbox": {}},
        "Has Image":      {"checkbox": {}},
        "Headline":       {"rich_text": {}},
        "Product Ref":    {"rich_text": {}},
        "Card Image":     {"rich_text": {}},
    }

    resp = requests.get(f"{NOTION_API}/databases/{db_id}", headers=notion_headers(token))
    resp.raise_for_status()
    existing = set(resp.json().get("properties", {}).keys())

    to_add = {k: v for k, v in required.items() if k not in existing}
    if not to_add:
        return

    print(f"Adding {len(to_add)} properties to database: {list(to_add.keys())}")
    resp = requests.patch(
        f"{NOTION_API}/databases/{db_id}",
        headers=notion_headers(token),
        json={"properties": to_add},
    )
    resp.raise_for_status()


def find_page_by_caption_id(token, db_id, caption_id):
    """Query database for existing page with matching Caption ID."""
    resp = requests.post(
        f"{NOTION_API}/databases/{db_id}/query",
        headers=notion_headers(token),
        json={
            "filter": {
                "property": "Caption ID",
                "rich_text": {"equals": str(caption_id)},
            }
        },
    )
    resp.raise_for_status()
    results = resp.json().get("results", [])
    return results[0]["id"] if results else None


def to_embed_url(url):
    """Convert any Drive URL to Google's thumbnail endpoint (serves image directly)."""
    if not url:
        return ""
    import re
    m = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
    if m:
        return f"https://drive.google.com/thumbnail?id={m.group(1)}&sz=w1000"
    m = re.search(r"[?&]id=([a-zA-Z0-9_-]+)", url)
    if m:
        return f"https://drive.google.com/thumbnail?id={m.group(1)}&sz=w1000"
    return url


def build_properties(caption):
    status = caption.get("status", "")
    prompt_file = PROJECT_DIR / ".tmp" / f"{caption['id']}_prompt_structured.json"
    has_prompt = prompt_file.exists()
    has_image = Path(PROJECT_DIR / "output" / "images" / f"dubery_{caption['id']}.jpg").exists()
    image_url = caption.get("image_url", "") or ""

    # Load prompt text and headline from structured JSON if available
    prompt_text = ""
    headline = caption.get("headline", "")
    if has_prompt:
        try:
            prompt_data = json.loads(prompt_file.read_text())
            prompt_text = json.dumps(prompt_data, ensure_ascii=False)[:2000]
            headline = (prompt_data.get("overlays", {}).get("headline") or {}).get("text", "") or headline
        except Exception:
            pass

    def rt(text):
        return {"rich_text": [{"text": {"content": str(text or "")[:2000]}}]}

    def sel(value):
        return {"select": {"name": str(value)}} if value else {"select": None}

    props = {
        "Name":           {"title": [{"text": {"content": f"#{caption['id']} — {caption.get('vibe', '')}"}}]},
        "Caption ID":     {"rich_text": [{"text": {"content": str(caption["id"])}}]},
        "Status":         sel(status),
        "Vibe":           rt(caption.get("vibe", "")),
        "Angle":          sel(caption.get("angle", "")),
        "Visual Anchor":  sel(caption.get("visual_anchor", "")),
        "Rating":         {"number": caption.get("rating") or 0},
        "Caption Text":   rt(caption.get("caption_text", "")),
        "Notes":          rt(caption.get("notes", "")),
        "Prompt":         rt(prompt_text),
        "Image Status":   sel(status if "IMAGE" in status else ""),
        "Image Feedback": rt(caption.get("image_feedback", "")),
        "Has Prompt":     {"checkbox": has_prompt},
        "Has Image":      {"checkbox": has_image},
        "Headline":       rt(headline),
        "Product Ref":    rt(caption.get("product_ref", "")),
        "Card Image":     rt(caption.get("card_image", "")),
    }
    embed_url = to_embed_url(image_url)
    if embed_url:
        props["Image URL"] = {"files": [{"type": "external", "name": f"dubery_{caption['id']}.jpg", "external": {"url": embed_url}}]}
    return props


def build_cover(caption):
    url = to_embed_url(caption.get("image_url", "") or "")
    if url:
        return {"type": "external", "external": {"url": url}}
    return None


def upsert_caption(token, db_id, caption):
    props = build_properties(caption)
    cover = build_cover(caption)
    existing_id = find_page_by_caption_id(token, db_id, caption["id"])

    payload = {"properties": props}
    if cover:
        payload["cover"] = cover

    if existing_id:
        resp = requests.patch(
            f"{NOTION_API}/pages/{existing_id}",
            headers=notion_headers(token),
            json=payload,
        )
        resp.raise_for_status()
        print(f"  Updated #{caption['id']} ({caption.get('status', '')})")
    else:
        body = {"parent": {"database_id": db_id}, "properties": props}
        if cover:
            body["cover"] = cover
        resp = requests.post(
            f"{NOTION_API}/pages",
            headers=notion_headers(token),
            json=body,
        )
        resp.raise_for_status()
        print(f"  Created #{caption['id']} ({caption.get('status', '')})")


# ── Google Sheets sync ───────────────────────────────────────────────────────

def get_sheets_service():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    token_file = PROJECT_DIR / "token.json"
    creds_file = PROJECT_DIR / "credentials.json"

    creds = None
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), scopes)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_file), scopes)
            creds = flow.run_local_server(port=0)
        token_file.write_text(creds.to_json())
    return build("sheets", "v4", credentials=creds)


def caption_to_sheet_row(caption):
    prompt_file = PROJECT_DIR / ".tmp" / f"{caption['id']}_prompt_structured.json"
    has_prompt = prompt_file.exists()
    has_image = (PROJECT_DIR / "output" / "images" / f"dubery_{caption['id']}.jpg").exists()

    headline = caption.get("headline", "")
    prompt_text = ""
    if has_prompt:
        try:
            prompt_data = json.loads(prompt_file.read_text())
            hl = (prompt_data.get("overlays", {}).get("headline") or {})
            headline = (hl.get("text", "") if isinstance(hl, dict) else hl) or headline
            prompt_text = json.dumps(prompt_data, ensure_ascii=False)[:5000]
        except Exception:
            pass

    status = caption.get("status", "")
    image_status = status if "IMAGE" in status else ""

    return [
        str(caption.get("id", "")),
        status,
        headline,
        caption.get("caption_text", ""),
        caption.get("vibe", ""),
        caption.get("angle", ""),
        caption.get("visual_anchor", ""),
        str(caption.get("rating") or ""),
        caption.get("product_ref", ""),
        caption.get("card_image", ""),
        caption.get("image_url", ""),
        image_status,
        "YES" if has_image else "NO",
        "YES" if has_prompt else "NO",
        caption.get("image_feedback", ""),
        caption.get("notes", ""),
        prompt_text,
        caption.get("source", ""),
    ]


def sync_to_sheet(captions):
    try:
        service = get_sheets_service()
    except Exception as e:
        print(f"  Sheet sync skipped (auth error): {e}")
        return

    rows = [SHEET_HEADERS]
    for caption in sorted(captions, key=lambda x: str(x["id"])):
        rows.append(caption_to_sheet_row(caption))

    service.spreadsheets().values().clear(
        spreadsheetId=SHEET_ID, range="Sheet1"
    ).execute()

    service.spreadsheets().values().update(
        spreadsheetId=SHEET_ID,
        range="Sheet1!A1",
        valueInputOption="RAW",
        body={"values": rows},
    ).execute()

    print(f"  Sheet synced: {len(rows) - 1} rows written")


# ── Main ─────────────────────────────────────────────────────────────────────

def load_all_captions():
    captions = []
    for fname in ["pipeline.json", "rejected_captions.json"]:
        fpath = TMP_DIR / fname
        if fpath.exists():
            data = json.loads(fpath.read_text())
            captions.extend(data)
            print(f"Loaded {len(data):>3} from {fname}")
    return captions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Print what would be synced without writing")
    parser.add_argument("--sheets-only", action="store_true", help="Sync to Google Sheet only, skip Notion")
    args = parser.parse_args()

    env = load_env()
    token = env.get("NOTION_TOKEN")
    db_id = env.get("NOTION_DATABASE_ID")

    if not token:
        print("ERROR: NOTION_TOKEN not found in .env")
        sys.exit(1)
    if not db_id:
        print("ERROR: NOTION_DATABASE_ID not found in .env")
        sys.exit(1)

    captions = load_all_captions()
    if not captions:
        print("No captions found in .tmp/")
        sys.exit(0)

    print(f"\nTotal: {len(captions)} captions to sync")

    if args.dry_run:
        for c in sorted(captions, key=lambda x: str(x["id"])):
            print(f"  #{c['id']:>2}  {c.get('status', ''):>20}  {c.get('vibe', '')}")
        return

    if not args.sheets_only:
        print("\nEnsuring database properties...")
        ensure_properties(token, db_id)

        print("\nSyncing captions to Notion...")
        errors = []
        for caption in sorted(captions, key=lambda x: str(x["id"])):
            try:
                upsert_caption(token, db_id, caption)
            except Exception as e:
                print(f"  ERROR #{caption['id']}: {e}")
                errors.append(caption["id"])

        print(f"\nDone. {len(captions) - len(errors)} synced, {len(errors)} errors.")
    else:
        errors = []

    print("\nSyncing to Google Sheet...")
    sync_to_sheet(captions)

    if errors:
        print(f"Failed IDs: {errors}")
        sys.exit(1)


if __name__ == "__main__":
    main()
