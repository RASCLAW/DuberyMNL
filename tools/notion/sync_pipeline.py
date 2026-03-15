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
    "Angle", "Visual Anchor", "Rating", "Product Ref", "Image URL", "Image Status",
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
        "Caption ID":     {"number": {}},
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


def load_all_page_ids(token, db_id):
    """Fetch all existing pages in one paginated query and return {caption_id: page_id}."""
    page_map = {}
    cursor = None
    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        resp = requests.post(
            f"{NOTION_API}/databases/{db_id}/query",
            headers=notion_headers(token),
            json=body,
        )
        resp.raise_for_status()
        data = resp.json()
        for page in data.get("results", []):
            cid = page.get("properties", {}).get("Caption ID", {}).get("number")
            if cid is not None:
                page_map[int(cid)] = page["id"]
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
    return page_map


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


def _get_prompt_data(caption_id, headline_fallback=""):
    """Load prompt file once and return (has_prompt, has_image, headline, prompt_text).
    Results are cached so build_properties and caption_to_sheet_row share one disk read."""
    if caption_id in _prompt_cache:
        return _prompt_cache[caption_id]

    prompt_file = PROJECT_DIR / ".tmp" / f"{caption_id}_prompt_structured.json"
    has_prompt = prompt_file.exists()
    has_image = (PROJECT_DIR / "output" / "images" / f"dubery_{caption_id}.jpg").exists()
    headline = headline_fallback
    prompt_text = ""

    if has_prompt:
        try:
            prompt_data = json.loads(prompt_file.read_text())
            hl = prompt_data.get("overlays", {}).get("headline") or {}
            headline = (hl.get("text", "") if isinstance(hl, dict) else hl) or headline_fallback
            prompt_text = json.dumps(prompt_data, ensure_ascii=False)
        except Exception:
            pass

    result = (has_prompt, has_image, headline, prompt_text)
    _prompt_cache[caption_id] = result
    return result


_prompt_cache: dict = {}


def build_properties(caption):
    status = caption.get("status", "")
    image_url = caption.get("image_url", "") or ""

    has_prompt, has_image, headline, prompt_text = _get_prompt_data(
        caption["id"], headline_fallback=caption.get("headline", "")
    )

    def rt(text):
        return {"rich_text": [{"text": {"content": str(text or "")[:2000]}}]}

    def sel(value):
        return {"select": {"name": str(value)}} if value else {"select": None}

    props = {
        "Name":           {"title": [{"text": {"content": f"#{caption['id']} — {caption.get('vibe', '')}"}}]},
        "Caption ID":     {"number": int(caption["id"])},
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


def upsert_caption(token, db_id, caption, page_map):
    props = build_properties(caption)
    cover = build_cover(caption)
    existing_id = page_map.get(int(caption["id"]))

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
    has_prompt, has_image, headline, prompt_text = _get_prompt_data(
        caption["id"], headline_fallback=caption.get("headline", "")
    )
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
        caption.get("image_url", ""),
        image_status,
        "YES" if has_image else "NO",
        "YES" if has_prompt else "NO",
        caption.get("image_feedback", ""),
        caption.get("notes", ""),
        prompt_text[:5000],
        caption.get("source", ""),
    ]


def sync_to_sheet(captions):
    try:
        service = get_sheets_service()
    except Exception as e:
        print(f"  Sheet sync skipped (auth error): {e}")
        return

    rows = [SHEET_HEADERS]
    for caption in sorted(captions, key=lambda x: x["id"]):
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
        for c in sorted(captions, key=lambda x: x["id"]):
            print(f"  #{c['id']:>2}  {c.get('status', ''):>20}  {c.get('vibe', '')}")
        return

    print("\nEnsuring database properties...")
    ensure_properties(token, db_id)

    print("\nLoading existing Notion pages...")
    page_map = load_all_page_ids(token, db_id)
    print(f"  Found {len(page_map)} existing pages")

    print("\nSyncing captions...")
    errors = []
    for caption in sorted(captions, key=lambda x: x["id"]):
        try:
            upsert_caption(token, db_id, caption, page_map)
        except Exception as e:
            print(f"  ERROR #{caption['id']}: {e}")
            errors.append(caption["id"])

    print(f"\nDone. {len(captions) - len(errors)} synced, {len(errors)} errors.")

    print("\nSyncing to Google Sheet...")
    sync_to_sheet(captions)

    if errors:
        print(f"Failed IDs: {errors}")
        sys.exit(1)


if __name__ == "__main__":
    main()
