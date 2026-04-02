---
paths:
  - "tools/**/*.py"
  - "scripts/**/*.py"
---

# Tool Development Rules

- WAT framework: tools are deterministic executors -- no AI reasoning inside scripts
- All secrets via `.env` only -- never hardcode keys
- If a tool makes a paid API call (kie.ai, Meta, Anthropic), log the call and check with RA before retrying on failure
- Tools must be runnable standalone: `python tools/[category]/[script].py`
- Errors should print clearly and exit with a non-zero code
- No silent failures -- if something goes wrong, the script must say so
- Intermediates go to `.tmp/` -- never commit `.tmp/` contents
- Deliverables go to cloud (Google Sheets, Drive) -- not local files
