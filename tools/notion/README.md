# notion — Sync pipeline captions to Notion and Google Sheets

**What it does**
- Reads caption records from `.tmp/pipeline.json` and `.tmp/rejected_captions.json`.
- Upserts each caption as a page in a Notion database (create on first run, update on subsequent runs, keyed by Caption ID).
- Overwrites the DuberyMNL Pipeline Google Sheet with the full caption roster (all rows replaced each sync).
- Attaches Google Drive image URLs as embedded thumbnails on Notion pages when available.

**Key files**

| File | Purpose |
|------|---------|
| `sync_pipeline.py` | Single entrypoint — loads captions, ensures Notion DB properties exist, upserts pages, then writes the Google Sheet. |

**Run**

```bash
# Full sync (Notion + Google Sheet)
python tools/notion/sync_pipeline.py

# Preview what would be synced — no writes
python tools/notion/sync_pipeline.py --dry-run

# Google Sheet only — skip Notion
python tools/notion/sync_pipeline.py --sheets-only
```

**Inputs / outputs**

| Direction | Resource |
|-----------|----------|
| Reads | `.tmp/pipeline.json` — approved captions |
| Reads | `.tmp/rejected_captions.json` — rejected captions |
| Reads | `.tmp/<id>_prompt_structured.json` — per-caption prompt JSON (optional, enriches headline + prompt fields) |
| Reads | `contents/ads/dubery_<id>.jpg` — checks local existence to set Has Image flag |
| Writes | Notion database (upsert pages) |
| Writes | Google Sheet ID `1LVshSQP5Ob9RNqt35PoSjbUuAiu9dneyHHhUiUZKYrg` — Sheet1, full overwrite |

**Auth / env**

| Var | Purpose |
|-----|---------|
| `NOTION_TOKEN` | Notion integration token (required) |
| `NOTION_DATABASE_ID` | Target Notion database ID (required) |
| Google OAuth | Via `tools/auth.get_credentials()` — same OAuth flow used by other tools in this repo |

**Gotchas**
- Google Sheets auth uses the shared `tools/auth` helper; if the OAuth token is expired, the sheet sync is skipped with a warning but the Notion sync still completes.
- Drive image URLs are converted to `drive.google.com/thumbnail?id=...&sz=w1000` so Notion can embed them — raw Drive share links do not render inline.
- The Sheet is fully overwritten on every run (clear then write); partial updates are not supported.
