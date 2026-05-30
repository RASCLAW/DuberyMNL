# upwork — Job scout and market intelligence tools for RA's job hunt

**What it does**
- Fetches remote job listings from RemoteOK, Jobicy, and We Work Remotely (last 48 h), scores each against RA's skill profile, and prints a tiered report (Apply Now / Consider / Skip).
- Deduplicates jobs across runs using `.tmp/scout_seen.json` so repeat listings don't surface again.
- Accumulates skill frequency data across scout runs into `.tmp/scout_skills_log.json` for trend analysis.
- Analyzes the rolling skill log to show which skills are in demand, RA's coverage gap, and recommended next skills to learn; can push a summary to the ra-dashboard JSON.

**Key files**

| File | What it does |
|---|---|
| `scout.py` | Fetches jobs from 3 free APIs + optional WebSearch JSON, scores and categorizes them, optionally sends report via Telegram |
| `market_intel.py` | Reads the accumulated `scout_skills_log.json`, builds a demand/gap/learning-rec report, optionally writes to `dashboard-data.json` |

**Run**

```bash
# Basic fetch + print report
python tools/upwork/scout.py

# Fetch, save skill frequencies, and send report to Telegram
python tools/upwork/scout.py --save-skills --telegram

# Include extra results from a WebSearch JSON file
python tools/upwork/scout.py --web-results .tmp/search_results.json

# Show all jobs, including previously seen ones
python tools/upwork/scout.py --no-dedup

# Clear the seen-job cache (forces re-showing all jobs on next run)
python tools/upwork/scout.py --reset-seen

# Print market intel report (requires prior scout runs with --save-skills)
python tools/upwork/market_intel.py

# Market intel with Telegram delivery and dashboard write
python tools/upwork/market_intel.py --telegram --dashboard

# Adjust lookback window (default is 7 days)
python tools/upwork/market_intel.py --days 14

# Supplement market intel with a WebSearch trend JSON
python tools/upwork/market_intel.py --web .tmp/trend_results.json
```

**Inputs / outputs**

| Direction | What |
|---|---|
| Reads | RemoteOK API, Jobicy API, We Work Remotely RSS (all fetched at runtime) |
| Reads | Optional `--web-results` / `--web` JSON (array of `{url, title, snippet}` objects from a WebSearch agent) |
| Reads | `.tmp/scout_seen.json` — cross-run dedup cache |
| Reads | `.tmp/scout_skills_log.json` — rolling skill frequency log (input to `market_intel.py`) |
| Writes | `.tmp/scout_seen.json` — updated after each scout run |
| Writes | `.tmp/scout_skills_log.json` — appended when `--save-skills` is used (keeps last 30 days) |
| Writes | `~/projects/ra-dashboard/dashboard-data.json` — `briefing.market_intel` key, only when `--dashboard` is passed |
| Prints | HTML-formatted report to stdout (suitable for Telegram HTML parse mode) |

**Auth / env**

No env vars or OAuth are required for the public API sources. The `--telegram` flag imports `send_message.send_to_ra` from `~/projects/ra-dashboard/tools/telegram/` — that module handles its own Telegram bot token.

**Gotchas**

- `market_intel.py` produces no useful output until `scout.py --save-skills` has been run at least once to populate the skills log.
- The `--telegram` flag uses Telegram HTML parse mode; if the report contains unescaped `<` or `>` characters from job descriptions, Telegram may reject the message.
- The dashboard write (`--dashboard`) silently no-ops if `~/projects/ra-dashboard/dashboard-data.json` does not exist.
