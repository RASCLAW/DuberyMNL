# Upwork Job Scout

## Trigger
"scout jobs", "job report", "find jobs", "upwork scout"

## Quick Run (RemoteOK only)
```bash
python3 tools/upwork/scout.py
```

## Full Run (RemoteOK + Upwork/LinkedIn via WebSearch)

### Step 1: Agent runs WebSearch queries
Run 4-6 of these (parallel):
1. `upwork.com freelance-jobs "AI automation" OR "AI agent" OR "agentic"`
2. `upwork.com freelance-jobs "n8n" OR "make.com" OR "workflow automation"`
3. `upwork.com freelance-jobs "Claude" OR "Claude Code" OR "Anthropic"`
4. `upwork.com freelance-jobs "AI chatbot" OR "chatbot automation"`
5. `upwork.com freelance-jobs "Meta Ads automation" OR "Facebook Ads automation"`
6. `upwork.com freelance-jobs "CRM automation" OR "CRM setup" AI`

### Step 2: Save results
Combine all WebSearch link results into `.tmp/upwork_raw.json`:
```json
[{"title": "...", "url": "..."}]
```

### Step 3: Run scout
```bash
python3 tools/upwork/scout.py --web-results .tmp/upwork_raw.json
```

Add `--telegram` to send via Rasclaw. Add `--no-dedup` to include previously seen jobs.

## Scoring
5 criteria, 1-5 each: skill fit, portfolio proof, budget, comfort, growth.
- APPLY NOW: avg >= 3.5
- WORTH CONSIDERING: 2.5-3.49
- SKIP: < 2.5

## Automation (Phase 2)
- Cron at 6 PM PHT: `python3 tools/upwork/scout.py --telegram`
- RemoteOK runs standalone. WebSearch supplement needs `claude --print`.
