# sheets — Google Sheets read/write and one-time spreadsheet setup

**What it does**
- Reads any tab from the DuberyMNL Master spreadsheet, optionally filtering by a column=value expression, and prints JSON to stdout.
- Appends new rows or updates existing rows in any tab using JSON key/value pairs.
- One-time setup: creates the DuberyMNL Master spreadsheet (6 tabs: captions, rejected_captions, images, ad_drafts, leads, brand) and seeds it with brand reference data.
- One-time setup: creates the DuberyMNL CRM spreadsheet (3 tabs: Leads, Orders, Lead Score Log) with formatted headers, then moves it into a `DuberyMNL` Drive folder and saves a manifest to `tools/chatbot/crm_sheet_info.json`.

**Key files**

| File | Purpose |
|------|---------|
| `read_sheet.py` | Read rows from a spreadsheet tab; optional `Key=Value` filter; outputs JSON array |
| `write_sheet.py` | Append a new row or update matching rows in a spreadsheet tab |
| `setup_spreadsheet.py` | One-time: create the DuberyMNL Master spreadsheet and seed all tabs + brand data |
| `create_crm_sheet.py` | One-time: create the DuberyMNL CRM spreadsheet (idempotent — skips if it already exists) |

**Run**

```sh
# Read all rows from the captions tab
python tools/sheets/read_sheet.py --sheet captions

# Read only APPROVED rows from the captions tab
python tools/sheets/read_sheet.py --sheet captions --filter "Status=APPROVED"

# Append a new row to the captions tab
python tools/sheets/write_sheet.py --sheet captions --action append --data '{"Vibe":"commuter","Caption":"...","Status":"PENDING"}'

# Update Status to APPROVED for the row where ID=42
python tools/sheets/write_sheet.py --sheet captions --action update --filter "ID=42" --data '{"Status":"APPROVED"}'

# One-time: create the Master spreadsheet (prints the new GOOGLE_SHEETS_SPREADSHEET_ID)
python tools/sheets/setup_spreadsheet.py

# One-time: create the CRM spreadsheet (idempotent)
python tools/sheets/create_crm_sheet.py
```

**Inputs / outputs**

- **Reads from:** `GOOGLE_SHEETS_SPREADSHEET_ID` spreadsheet (all scripts except `create_crm_sheet.py` which creates its own).
- **Writes to:** the same spreadsheet (append/update rows); `create_crm_sheet.py` also writes a JSON manifest to `tools/chatbot/crm_sheet_info.json`.
- `read_sheet.py` and `write_sheet.py` output JSON to stdout.
- `setup_spreadsheet.py` prints the new spreadsheet ID to stdout for manual copy into `.env`.

**Auth / env**

- `GOOGLE_SHEETS_SPREADSHEET_ID` — required in `.env` for `read_sheet.py` and `write_sheet.py`.
- Google OAuth via shared `tools/auth.py` (`get_credentials()`): reads `credentials.json` and `token.json` from the project root. Scopes include `spreadsheets` and `drive`.
- First run triggers a browser OAuth consent flow; subsequent runs use the cached `token.json`.

**Gotchas**

- `write_sheet.py --action update` requires `--filter`; omitting it exits with an error.
- `write_sheet.py --action append` requires that the target tab already has headers in row 1 (run `setup_spreadsheet.py` first if starting fresh).
- If `token.json` is expired or revoked, run the reauth helper: `python -c "import sys;sys.path.insert(0,'tools');from auth import reauth;reauth()"`.
