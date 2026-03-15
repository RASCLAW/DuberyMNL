"""
DuberyMNL Pipeline → Notion Sync

Reads .tmp/captions.json, .tmp/rejected_captions.json, .tmp/pending_post.json
and upserts each caption as a row in the Notion pipeline database.

Run:
    python tools/notion/sync_pipeline.py

Or after image review:
    python tools/notion/sync_pipeline.py --source pending_post
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
        "Image URL":      {"url": {}},
        "Image Status":   {"select": {}},
        "Image Feedback": {"rich_text": {}},
        "Has Prompt":     {"checkbox": {}},
        "Has Image":      {"checkbox": {}},
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
                "number": {"equals": int(caption_id)},
            }
        },
    )
    resp.raise_for_status()
    results = resp.json().get("results", [])
    return results[0]["id"] if results else None


def build_properties(caption):
    status = caption.get("status", "")
    prompt_file = PROJECT_DIR / ".tmp" / f"{caption['id']}_prompt_structured.json"
    has_prompt = prompt_file.exists()
    has_image = Path(PROJECT_DIR / "output" / "images" / f"dubery_{caption['id']}.jpg").exists()
    image_url = caption.get("image_url", "") or ""

    # Load prompt text from structured JSON if available
    prompt_text = ""
    if has_prompt:
        try:
            prompt_data = json.loads(prompt_file.read_text())
            prompt_text = json.dumps(prompt_data, ensure_ascii=False)[:2000]
        except Exception:
            pass

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
    }
    if image_url:
        props["Image URL"] = {"url": image_url}
    return props


def upsert_caption(token, db_id, caption):
    props = build_properties(caption)
    existing_id = find_page_by_caption_id(token, db_id, caption["id"])

    if existing_id:
        resp = requests.patch(
            f"{NOTION_API}/pages/{existing_id}",
            headers=notion_headers(token),
            json={"properties": props},
        )
        resp.raise_for_status()
        print(f"  Updated #{caption['id']} ({caption.get('status', '')})")
    else:
        resp = requests.post(
            f"{NOTION_API}/pages",
            headers=notion_headers(token),
            json={
                "parent": {"database_id": db_id},
                "properties": props,
            },
        )
        resp.raise_for_status()
        print(f"  Created #{caption['id']} ({caption.get('status', '')})")


# ── Main ─────────────────────────────────────────────────────────────────────

def load_all_captions():
    captions = []
    for fname in ["captions.json", "rejected_captions.json", "pending_post.json"]:
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

    print("\nSyncing captions...")
    errors = []
    for caption in sorted(captions, key=lambda x: x["id"]):
        try:
            upsert_caption(token, db_id, caption)
        except Exception as e:
            print(f"  ERROR #{caption['id']}: {e}")
            errors.append(caption["id"])

    print(f"\nDone. {len(captions) - len(errors)} synced, {len(errors)} errors.")
    if errors:
        print(f"Failed IDs: {errors}")
        sys.exit(1)


if __name__ == "__main__":
    main()
