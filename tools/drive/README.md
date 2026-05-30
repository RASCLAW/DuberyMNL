# drive — Google Drive upload, sync, and backup utilities

**What it does**
- Uploads individual images or batches of images to Drive with public read links.
- Syncs a full local folder tree to Drive (MD5-based, idempotent, parallel workers).
- Backs up project secrets (`.env`, `credentials.json`, `token.json`) with pinned revision history.
- Enriches the chatbot image bank JSON with `lh3.googleusercontent.com` CDN URLs after upload.
- Deletes Drive folders permanently (non-trash).

**Key files**

| Script | What it does |
|---|---|
| `upload_image.py` | Upload a single local image to an arbitrary Drive folder path; prints JSON with `drive_file_id` and `drive_url`. |
| `upload_bank_to_drive.py` | Upload every pick in a chatbot image bank JSON to Drive under `DuberyMNL/Chatbot Bank 2026-04/`, then write the `lh3` CDN URL + `drive_file_id` back into the bank JSON. Idempotent. |
| `upload_chatbot_images.py` | Upload a hardcoded manifest of ~45 chatbot-facing images (hero shots, model shots, lifestyle, brand, proof, sales-support) to `DuberyMNL/Chatbot Images/`; saves a `drive_image_manifest.json` for the chatbot to reference. |
| `sync_folder.py` | Mirror a local folder tree to Drive. Two-phase: bulk-list existing files per folder, then upload new/changed files in parallel. Compares by MD5; skips unchanged files. Appends a run summary to `.tmp/drive-sync.log`. |
| `delete_folder.py` | Permanently delete a Drive folder and all its contents (recursive, no trash). Supports `--dry-run`. |
| `backup_secrets.py` | Upload `.env`, `credentials.json`, `token.json`, and `~/.claude/.credentials.json` to `DuberyMNL/Backups/secrets/`. Overwrites in place and pins the new revision as `keepForever=True` for rollback. |

**Run**

```bash
# Upload a single image
python tools/drive/upload_image.py --file .tmp/image.jpg --folder "DuberyMNL/Images"

# Upload and enrich the default chatbot bank (adds CDN URLs back to the JSON)
python tools/drive/upload_bank_to_drive.py
python tools/drive/upload_bank_to_drive.py --dry-run
python tools/drive/upload_bank_to_drive.py --bank contents/assets/other-bank.json

# Upload the hardcoded chatbot image manifest
python tools/drive/upload_chatbot_images.py

# Sync a local folder to Drive (idempotent, MD5-based)
python tools/drive/sync_folder.py --local contents/failed --remote "DuberyMNL/backup/content/failed"
python tools/drive/sync_folder.py --local archives --remote "DuberyMNL/backup/archives" --dry-run
python tools/drive/sync_folder.py --local contents --remote "DuberyMNL/backup/contents" --workers 4

# Delete a Drive folder permanently
python tools/drive/delete_folder.py --remote "DuberyMNL/backup/contents/failed"
python tools/drive/delete_folder.py --remote "DuberyMNL/backup/contents/failed" --dry-run

# Backup secrets to Drive
python tools/drive/backup_secrets.py
```

**Inputs / outputs**

| Script | Reads | Writes |
|---|---|---|
| `upload_image.py` | Local file at `--file` | Drive file; prints JSON to stdout |
| `upload_bank_to_drive.py` | Bank JSON at `--bank` (default: `contents/assets/chatbot-image-bank-2026-04.json`) + local image files | Drive folder; mutates bank JSON in place with CDN URLs |
| `upload_chatbot_images.py` | Hardcoded local paths (landing page cards, `contents/`, `dubery-landing/assets/`) | Drive under `DuberyMNL/Chatbot Images/`; writes `tools/chatbot/drive_image_manifest.json` |
| `sync_folder.py` | Local folder tree at `--local` | Drive at `--remote`; appends to `.tmp/drive-sync.log` |
| `delete_folder.py` | Drive folder at `--remote` | Permanently deletes that folder from Drive |
| `backup_secrets.py` | `.env`, `credentials.json`, `token.json`, `~/.claude/.credentials.json` | Drive at `DuberyMNL/Backups/secrets/` |

**Auth / env**

- All scripts call `tools/auth.get_credentials()`, which reads `credentials.json` + `token.json` from the project root via standard Google OAuth2 (`google-auth-oauthlib`).
- No env vars are read directly by these scripts; `load_dotenv()` is called but credentials come from the OAuth token files, not `.env`.
- OAuth scope required: `https://www.googleapis.com/auth/drive` (full Drive access for upload, update, delete, and permissions).

**Gotchas**

- `sync_folder.py` and `delete_folder.py` apply an IPv4-only monkey-patch to `socket.getaddrinfo` at import time. This works around a 60s-per-call hang on RA's home ISP (no IPv6 routing). Harmless on cloud environments.
- `upload_bank_to_drive.py` mutates the bank JSON in place — run `--dry-run` first to check for missing local files before committing.
- Uploaded files in `upload_image.py` and `upload_bank_to_drive.py` are set to anyone-readable (`role: reader`). Files in `sync_folder.py` and `backup_secrets.py` are NOT made public.
- Drive does not support MD5 for Google-native files (Docs, Sheets, etc.); `sync_folder.py` falls back to re-uploading those if MD5 is unavailable.
