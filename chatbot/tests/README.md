# chatbot/tests

Test scripts for the live Messenger chatbot. Promoted from `.tmp/` (2026-06-05) so they stop decaying in un-backed-up scratch — these are the closest thing the bot has to a test suite.

Run from the **repo root** (results write to `.tmp/`):

| Script | What it does | Target | Notes |
|--------|--------------|--------|-------|
| `chatbot_smoke_test.py` | 10 critical first-contact cases (greeting, Taglish, price, color list, image key, order intent…) via `/chat-test` | `http://localhost:8080` | Bot must be running locally. Uses `TEST_*` sender IDs (no CRM pollution). |
| `chatbot_regression_test.py` | Session-99 refactor regression — each case opens a fresh session to verify first-contact behavior | `http://localhost:8080` | Bot must be running locally. |
| `chatbot_stress_test.py` | Fires fake Meta webhook payloads, then reads `/conversations` to inspect would-be replies | ⚠️ hard-coded to the **old Cloud Run URL** (`duberymnl-chatbot-*.run.app`), which is **defunct** — Cloud Run was decided against. Update `WEBHOOK_URL` to the laptop+tunnel endpoint before running. | Uses `TEST_BATTERY_*` sender IDs (easy to purge from CRM). |

```
# from c:\Users\RAS\projects\DuberyMNL
python chatbot/tests/chatbot_smoke_test.py
python chatbot/tests/chatbot_regression_test.py
```

Results land in `.tmp/chatbot_*_results.json`.
