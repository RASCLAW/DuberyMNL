# `gog` — DuberyMNL Google Services CLI

One CLI over Gmail, Google Calendar, and Google Tasks, all sharing a **single OAuth
token** via [`auth.py`](auth.py). Built so terminal/agent work needs no Google MCP
connectors. Drive + Sheets keep their own scripts ([`drive/`](drive/), [`sheets/`](sheets/)).

> Built 2026-05-31 (session 188). Replaces the local `gdrive` MCP for scripted work.

## Index
- [Quick start](#quick-start) · [Commands](#commands) · [Auth model](#auth-model)
- [Adding a new Google service](#adding-a-new-google-service) · [Troubleshooting](#troubleshooting)
- [What this does NOT cover](#what-this-does-not-cover)
- Source: [`gog.py`](gog.py) (dispatcher) · [`gmail/cli.py`](gmail/cli.py) · [`gcal/cli.py`](gcal/cli.py) · [`tasks/cli.py`](tasks/cli.py) · [`auth.py`](auth.py)

---

## Quick start

```bash
# from repo root
python tools/gog.py gmail list --max 5
python tools/gog.py cal agenda --days 30
python tools/gog.py tasks lists
```

Or, after putting the repo root on PATH (so the `gog.cmd` shim resolves):

```bash
gog gmail list --max 5
gog cal agenda --days 7
gog tasks add --title "Restock Bandits Green"
```

`python tools/gog.py` with no args prints usage + the service list.

**Prerequisites** (already satisfied on the build machine):
- Python deps: `google-api-python-client`, `google-auth-oauthlib`, `python-dotenv`
- `credentials.json` + `token.json` at the repo root (gitignored secrets)

## Commands

Output is JSON to stdout. Errors print to stderr and exit non-zero.
**Every mutating verb supports `--dry-run`** — it prints the intended action and makes
no API write.

### `gog gmail` — scope `gmail.modify`
| Command | What |
|---|---|
| `list [--query Q] [--max N]` | search/list messages (`--query` is Gmail search syntax, e.g. `"is:unread from:meta"`) |
| `read <message_id>` | full message: from/to/subject/date/body (text/plain preferred) |
| `send --to --subject --body [--dry-run]` | send mail |
| `label <message_id> --add L --remove L [--dry-run]` | add/remove labels (`--add`/`--remove` repeatable; names or system ids like `STARRED`/`UNREAD`) |
| `draft --to --subject --body [--dry-run]` | create a draft |
| `trash <message_id> [--dry-run]` | move to trash |

> `gmail.modify` covers read/search/label/draft/trash **and send**. The only thing it can't do is permanent-delete (would need the full-mail scope).

### `gog cal` — scope `calendar`  (global flag: `--cal <id>`, default `primary`)
| Command | What |
|---|---|
| `agenda [--days N]` | events in the next N days (default 7) |
| `list [--max N]` | next N upcoming events |
| `create --summary --start --end [--desc] [--dry-run]` | create event |
| `edit <event_id> [--summary] [--start] [--end] [--desc] [--dry-run]` | patch event |
| `delete <event_id> [--dry-run]` | delete event |
| `quickadd "text" [--dry-run]` | natural-language event ("Lunch with Sam tomorrow 1pm") |

> **Time formats:** a bare `YYYY-MM-DD` is treated as an **all-day** date; pass a full
> RFC3339 dateTime **with an offset** for timed events, e.g. `2026-06-01T14:00:00+08:00`.

### `gog tasks` — scope `tasks`  (`--tasklist`, default `@default` = your primary list)
| Command | What |
|---|---|
| `lists` | all task lists (id + title) |
| `list [--tasklist] [--show-completed]` | tasks in a list |
| `add --title [--notes] [--due ISO] [--tasklist] [--dry-run]` | add a task |
| `complete <task_id> [--tasklist] [--dry-run]` | mark completed |
| `delete <task_id> [--tasklist] [--dry-run]` | delete a task |

## Auth model

[`auth.py`](auth.py) holds one `SCOPES` list and one `token.json`. Three entry points:

- **`get_credentials()`** — load/refresh/first-auth. **Gentle by design:** a valid token is
  returned as-is, so it never surprises a headless caller (cron, Command Center, chatbot)
  with a browser prompt. It does **not** auto-reauth when you add a new scope.
- **`service(name, version)`** — `build()` an authorized client, e.g. `service("gmail", "v1")`.
- **`reauth()`** — force a fresh browser consent for the current `SCOPES` (a token *refresh*
  cannot widen scopes, so this is how a newly-added scope gets granted).

All Google tools in this repo share this token: Drive, Sheets, Gmail, Calendar, Tasks, YouTube.

## Adding a new Google service

1. **Enable the API** in the Cloud Console for project **`845810529681`**
   (`https://console.cloud.google.com/apis/library/<api>.googleapis.com?project=845810529681`).
   *Having the OAuth scope is not enough — the API must be enabled or calls 403.*
2. If it needs a **new scope**, add it to `SCOPES` in [`auth.py`](auth.py), then run once:
   ```bash
   python -c "import sys;sys.path.insert(0,'tools');from auth import reauth;reauth()"
   ```
3. Add `tools/<service>/cli.py` with a `def main(argv=None)` (mirror [`tasks/cli.py`](tasks/cli.py) — it's the smallest).
4. Register it in `SERVICES` in [`gog.py`](gog.py).
5. Give mutating verbs `--dry-run`. Smoke-test read first, then a dry-run, then a live write.

> **Naming gotcha:** don't name a service dir after a stdlib module. `calendar` is taken
> (used by `email`/`httplib2`), which is why the Calendar code lives in `gcal/`.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `HttpError 403 ... API has not been used in project ... or it is disabled` | The API isn't enabled in the Cloud project. Enable it (step 1 above), wait a minute, retry. |
| `403 ... insufficient ... scopes` / `ACCESS_TOKEN_SCOPE_INSUFFICIENT` | Scope missing from the token. Add to `SCOPES`, run `reauth()`. |
| `WinError 10060` connection timeout | IPv6 egress hang on a runner whose DNS returns IPv6 first. Real machines are usually fine; if it persists, force IPv4 (see [[project_gog_google_cli]] memory) or ask to add IPv4-preference to `auth.py`. |
| Browser prompt on a background job | A scope was added but `reauth()` not run, or `token.json` is missing/invalid. Run `reauth()` interactively once. |

## What this does NOT cover

- **Drive / Sheets** — already have dedicated scripts in [`drive/`](drive/) and [`sheets/`](sheets/); not folded into `gog`.
- **Google Photos** — *intentionally absent.* The Library API (post-Mar-2025) can only manage
  media an app itself uploaded — it cannot move/edit/delete your existing library. Manage those
  images as **Drive files** instead.
- **Google Keep** — no public API for personal accounts. Plan: export via
  [Google Takeout](https://takeout.google.com) and import into Tasks/a Doc/a Sheet (not built yet).
