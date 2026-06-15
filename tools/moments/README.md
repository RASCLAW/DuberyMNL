# moments — Content calendar + Moment Scout ("Moment Engine")

**What it does**
- Keeps a **content calendar** in the `content_calendar` tab of the Master spreadsheet (`GOOGLE_SHEETS_SPREADSHEET_ID`): one row per timely-content *moment* (holiday / event / trend / weather), each with a sunglasses angle, a publish window, a relevance score, and a status.
- Seeds the **fixed recurring PH anchors** (`contents/calendar/anchors_ph.json`) into dated calendar rows via deterministic date math.
- Provides the read/write primitives the daily **Moment Scout** researcher and the Command Center **Calendar** page build on.

> **Dir is `moments`, not `calendar`, on purpose.** These scripts put `tools/` on `sys.path` (to reuse `auth.py`); a `tools/calendar/` package would shadow Python's stdlib `calendar` module — the same reason `gcal/` isn't named `calendar/`.

**Key files**

| File | Purpose |
|------|---------|
| `moment_store.py` | Shared core: `read_moments()`, `upsert_moment(data, dry_run)`, the `content_calendar` sheet name + header schema. Imported by the others. |
| `setup_calendar_sheet.py` | Idempotent: create the `content_calendar` tab (if missing) + write/bold/freeze the header row. |
| `upsert_moment.py` | CLI to insert/update one moment by `id` (dedup, `--dry-run`). |
| `list_moments.py` | CLI to read + filter (`--status`, `--type`, `--upcoming-days N`) + pretty-print or `--json`. |
| `seed_from_anchors.py` | Materialize upcoming PH anchors into dated rows (`--horizon-days`, `--live`; dry-run by default). Re-run safe (upsert by id). |

**Data model** (`content_calendar` columns): `id, title, type, window_start, window_end, relevance, angle, format, source, status, notes, added, lead_time_days`.
- `type`: holiday | event | trend | weather
- `status`: suggested | approved | generated | posted | dismissed
- `source`: anchor | researcher | manual
- `id` convention: `{window_start}-{slug}` (e.g. `2026-12-25-christmas-gifting`) — stable dedup key.

**Run**

```sh
# One-time / safe: ensure the Sheet tab exists
python tools/moments/setup_calendar_sheet.py

# Seed upcoming fixed anchors (preview, then write)
python tools/moments/seed_from_anchors.py                 # dry-run, 120-day horizon
python tools/moments/seed_from_anchors.py --live

# Add / update a single moment
python tools/moments/upsert_moment.py --data '{"id":"2026-12-25-christmas-gifting","title":"Christmas gifting","type":"holiday","window_start":"2026-11-15","window_end":"2026-12-25","relevance":"10","angle":"Giftable shades","format":"carousel","source":"manual","status":"suggested"}'
python tools/moments/upsert_moment.py --data '{"id":"2026-12-25-christmas-gifting","status":"approved"}'

# List
python tools/moments/list_moments.py
python tools/moments/list_moments.py --status suggested --upcoming-days 60
python tools/moments/list_moments.py --json
```

**Inputs / outputs**
- Reads/writes the `content_calendar` tab of `GOOGLE_SHEETS_SPREADSHEET_ID`.
- Reads anchors from `contents/calendar/anchors_ph.json`.
- CLIs print JSON / a table to stdout (UTF-8 forced for headless/cron safety).

**Auth / env**
- `GOOGLE_SHEETS_SPREADSHEET_ID` in `.env`.
- Google OAuth via shared `tools/auth.py` (`get_credentials()`), same token as the other Sheets tools.

**Gotchas**
- `seed_from_anchors.py` is **dry-run by default** — pass `--live` to write.
- Anchor dates are MM-DD; variable-date holidays (Holy Week, Father's/Mother's Day, Sinulog) carry a `date_note` and an approximate window — the AI researcher verifies the exact date.
- The seeder only materializes anchors whose window starts within `--horizon-days` (default 120) and whose end is still in the future.

**Roadmap (Phase 2/3)**
- Phase 2: `.claude/skills/moment-research/` (daily researcher) + `send_digest.py` (TG) + a Claude cloud routine.
- Phase 3: Command Center `Calendar` tab (`/api/calendar` GET/POST over this tab).
