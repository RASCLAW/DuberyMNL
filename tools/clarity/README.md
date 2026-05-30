# clarity — Pull Microsoft Clarity site metrics for DuberyMNL

**What it does**
- Calls the Clarity Data Export API and saves the full payload to `.tmp/clarity_metrics.json`.
- By default makes 3 API calls: topline totals, breakdown by URL, breakdown by Device.
- Prints a console summary (traffic by page, friction metrics, device split) on top of the saved JSON.
- Respects the Clarity quota of 10 API calls per project per day; exits with code 2 on 429.

**Key files**

| File | Purpose |
|------|---------|
| `pull_metrics.py` | Single entrypoint — fetches Clarity metrics and saves + prints summary |

**Run**

```bash
# Default: last 3 days, 3 calls (totals + by URL + by Device)
python tools/clarity/pull_metrics.py

# Last 1 day only
python tools/clarity/pull_metrics.py --days 1

# Ad-hoc single call with custom dimensions (up to 3)
python tools/clarity/pull_metrics.py --dim Device OS Browser
```

`--days` accepts `1`, `2`, or `3` (Clarity API limit per call).
`--dim` overrides the standard 3-call sweep with a single call using the given dimensions.

**Inputs / outputs**

| Direction | Target |
|-----------|--------|
| Reads | Clarity Data Export API (`https://www.clarity.ms/export-data/api/v1/project-live-insights`) |
| Writes | `.tmp/clarity_metrics.json` (full payload, overwritten each run) |
| Prints | Console summary: topline metrics, top URLs by traffic/friction, device breakdown |

**Auth / env**

| Env var | Required | Description |
|---------|----------|-------------|
| `CLARITY_API_TOKEN` | Yes | Bearer token for the Clarity Data Export API |

Loaded from project-root `.env` via `python-dotenv`.

**Gotchas**
- Clarity enforces **10 API calls per project per day**. The default run uses 3. Using `--dim` adds 1 more. Plan accordingly.
- Each API call covers at most 3 days and up to 3 dimensions simultaneously.
