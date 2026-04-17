# DuberyMNL Command Center

Local web dashboard with a persistent Claude Agent SDK backend. Portfolio-facing,
future multi-tenant template for RAS Creative clients.

Runs on `http://localhost:8090`. Dark theme, sidebar nav, 8 tabs, a floating AI
assistant, and live service monitoring.

---

## Architecture

```
Browser  ⇄  Flask (app.py, port 8090)  ⇄  Claude Agent SDK  ⇄  Claude
                    │                                ▲
                    ├── /api/home/summary            │
                    ├── /api/monitor/status          │
                    │    └─ 9 monitors in parallel   │
                    ├── /api/monitor/logs/<service>  │
                    └── /api/agent/chat (SSE)  ──────┘
                                 inherits DuberyMNL .claude/ skills + CLAUDE.md
```

- Vanilla HTML + CSS + JS frontend (no framework).
- Flask serves shell.html + static assets + JSON APIs + one SSE stream.
- One persistent `AgentSession` holds the Claude session ID; every chat
  prompt resumes the same session so cached context is reused (first call
  pays ~$0.24 cache-create, subsequent calls are cheap).
- Agent sees the full DuberyMNL project via `setting_sources=['project']` +
  `cwd=PROJECT_ROOT`, so every skill in `.claude/skills/` and the project
  `CLAUDE.md` are auto-loaded.

---

## Setup

1. Install the Claude Code CLI and log in (subscription auth is inherited).
2. `pip install -r command-center/requirements.txt`
3. Copy `.env.example` into the project root `.env` (merge with existing
   `.env`). Fill the optional monitor tokens as available.
4. `python command-center/app.py` → open `http://localhost:8090/`

### At-logon autostart (Windows)

`boot.bat` is the entry script. Register with Task Scheduler as
`DuberyMNL-CommandCenter`, trigger = At logon of RA, run with highest
privileges NO, wake the computer to run YES. Pattern matches
`DuberyMNL-Chatbot` + `DuberyMNL-Tunnel`.

---

## Tabs

| Tab | Status | What it shows |
|---|---|---|
| **Home** | Phase 1 ✓ | Revenue today, active convos, pending approvals, system health |
| **Content Gen** | Phase 2 | Product → category → location → scene → Claude runs `/ugc-pipeline` or `/dubery-content-pipeline-full` |
| **Marketing** | Phase 2 | Caption gen, creative picker, ad launch |
| **CRM** | Phase 3 | Orders pipeline, source attribution, LTV |
| **Chatbot** | Phase 3 | Live conversations, handoff queue, /mark-sale captures |
| **Monitoring** | Phase 1 ✓ | 9 service rows (Option B layout). Auto-polls cheap checks every 30s. Expensive checks (Meta Ads, GH Actions) manual only. Per-row logs modal. |
| **Image Bank** | Phase 3 | Chatbot bank, FB stories pool, hero shots, prodref library |
| **Inventory** | Phase 3 | Per-SKU counts, low-stock alerts |

## Floating AI bot

Bottom-right FAB. Click to open. Every message streams from Claude via
`/api/agent/chat` (SSE). History persists to `localStorage` (last 20
messages). Proactive suggestions arrive in Phase 2.

---

## Monitors

| Name | What "active" means | Expensive? | Log source |
|---|---|---|---|
| chatbot | HTTP 200 on `localhost:8080/status` | no | `chatbot/logs/app.log` if present |
| tunnel | `chatbot.duberymnl.com/status` 200 AND `cloudflared.exe` running | no | — |
| worker_fallback | `WORKER_URL` responds 200/405 | no | — |
| meta_ads | ≥1 ACTIVE adset on account | **yes** | — |
| story_rotation | Latest GH Actions run <4h + success | **yes** | — |
| rasclaw_tg | `getMe` ok via `RASCLAW_BOT_TOKEN` | no | — |
| chatbot_tg | `getMe` ok via `TELEGRAM_BOT_TOKEN` | no | — |
| crm_sheet | CRM sheet header read succeeds | no | `token.json` |
| inventory | (placeholder) | no | — |

Cheap batch returns in <2s (9 parallel). Expensive batch adds ~3–4s. Manual
"Refresh expensive checks" button on the Monitoring tab triggers the full run.

---

## Security

- Secrets live in `.env` (gitignored). Never commit.
- Binds to `127.0.0.1` only. Expose via Cloudflare tunnel or VSCode
  port-forward when remote access is needed; both terminate TLS upstream.
- The Agent SDK runs with `permission_mode=bypassPermissions` — fine for a
  single-user local tool, **must** be replaced with an allowlist before this
  backend is ever multi-tenant or client-facing.

---

## Roadmap

| Phase | Scope |
|---|---|
| 1 ✓ | Backend, shell, Home, Monitoring, click-to-chat bot |
| 2 | Content Gen form, Marketing actions, proactive bubble suggestions (hybrid event + periodic triggers) |
| 3 | CRM, Chatbot live feed, Image Bank, Inventory, demo video, polish |

See `.tmp/plan.md` in the repo root for the detailed Phase 1 task log.
