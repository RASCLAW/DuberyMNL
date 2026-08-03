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

---

## `oj_scout.py` — OnlineJobs.ph demand scout

Scrapes the **public** OnlineJobs.ph job board (no login, never touches RA's
account) across a keyword list, parses each job card, and writes deduped rows to
`oj_jobs2.json`.

```bash
python tools/upwork/oj_scout.py     # run from c:/tmp or any writable cwd
```

Fields per job: `id, title, type, salary, posted, url, kw`.

**Why it exists:** to check what OnlineJobs.ph employers actually pay for before
building portfolio pieces blind. First run (2026-08-02) found OJ demand differs
sharply from Upwork — see `reference_oj_demand_data` memory.

**Gotchas**

- Parse each card between `<!-- Start -->` and `<!-- End -->`. A single regex with
  `.*?` across the whole page **bleeds across card boundaries** and silently pairs
  one job's title with another's salary and URL. This produced wrong numbers on the
  first pass; always spot-check that the title agrees with the URL slug.
- `jobkeyword` is a loose full-text match and the result count displays a cap of
  300 for almost any term — treat the count as meaningless and read the returned
  titles instead.
- Salary strings are free text and wildly inconsistent: `1500-2000`, `$8.00/hr`,
  `Php100,000 – Php160,000`, `26K - 35K Php`, `$120/week`, `TBD`. Any normalizer
  is an estimate; keep the raw string alongside it.
- Responses are cached to `ojcache/` — delete that folder to force a refetch.

## `oj_role_deep.py` — deep scan of one OJ role type

Sweeps a keyword list, filters job titles to a role pattern, then fetches each
matching job's **full detail page** (type of work, wage, hours/week, date, and the
whole description body). Public pages only. Writes `oj_image_jobs.json`.

Edit `KEYWORDS` and the `IMG` regex at the top to retarget it at a different role.

**Gotchas**

- **Normalize hourly pay using the job's own `HOURS PER WEEK`, not a flat 160
  hrs/month.** Many OJ roles are part-time; assuming full-time inflated a
  $5-10/hr 10-hr/week role into a fake ~$1,200/mo. Use `rate x hours x 4.33`.
- Wage strings are free text and frequently mis-encoded (`?80,000 per month` is a
  mangled peso sign). Always keep the raw string next to any computed figure.
- Detail bodies run past the job text into "SKILL REQUIREMENT" and related-jobs
  boilerplate — truncate on those markers.
