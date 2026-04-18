# DuberyMNL Command Center

Local web dashboard with a persistent Claude Agent SDK backend. One interface
to generate content, monitor services, and manage the DuberyMNL business.

Built as a portfolio piece and future multi-tenant template for RAS Creative clients.

`http://localhost:8090`

---

## Architecture

```
Browser  <->  Flask (app.py, :8090)  <->  Claude Agent SDK  <->  Claude
                    |                              |
                    +-- /api/home/summary          |
                    +-- /api/monitor/status         |
                    +-- /api/monitor/fix/<service>  |
                    +-- /api/content-stats          |
                    +-- /api/products               |
                    +-- /api/upload-concept          |
                    +-- /api/log-generation          |
                    +-- /api/generation-history      |
                    +-- /api/images/<path>           |
                    +-- /api/agent/chat (SSE)  -----+
                              inherits DuberyMNL skills + CLAUDE.md
```

- **Frontend:** Vanilla HTML + CSS + JS (no framework). Light warm theme (Claude AI inspired).
- **Backend:** Flask serves templates, static assets, JSON APIs, and one SSE stream endpoint.
- **Agent:** Single persistent `AgentSession` reuses the Claude session ID across requests. First call pays ~$0.24 cache-create, subsequent calls are cheap. Agent sees the full DuberyMNL project via `setting_sources=['project']`.
- **Auth:** `permission_mode=bypassPermissions` for single-user local use. Must swap to allowlist before any multi-tenant exposure.

---

## Setup

```bash
pip install -r command-center/requirements.txt
python command-center/app.py
```

Requires Claude Code CLI logged in (subscription auth inherited) and a `.env` in the project root with API keys.

### At-logon autostart (Windows)

`boot.bat` registered as `DuberyMNL-CommandCenter` in Task Scheduler, trigger = at logon. Same pattern as `DuberyMNL-Chatbot` + `DuberyMNL-Tunnel`.

---

## Content Gen Tab

The main feature. Three generation modes:

### UGC Mode
Standard pipeline: randomizer picks scene dimensions, fidelity-prompt builds the image spec, validator checks it, Vertex AI generates.
- **Type:** Person (wearing/selfie/outfit) or Product (flatlay/held/delivery)
- **Product:** Pick specific or random
- **Count:** 1-10 images per run

### Brand Mode
Routes through the brand randomizer for callout/bold/collection layouts with headlines and product angles.

### Bespoke Mode
Concept recreation. Paste any reference image (competitor ad, art, mood photo), type one sentence of direction. The agent:
1. Reads the concept image
2. Interprets the visual direction
3. Color-matches scene accents to the selected product
4. Builds a fidelity prompt from the concept (skips randomizer)
5. Validates and generates

This mode produces the highest quality results. Best prompt pattern:
> "use the concept of the image attached for duberymnl. use duberymnl fonts logo and product."

### Direction Chat
Mini-chat in the left column. Paste images, type direction, hit Ask. The agent confirms its understanding before you hit Generate. Conversational -- refine back and forth until the vision is clear.

### Output
- **Progress log:** Collapsible, shows agent's pipeline steps in real-time
- **Image result cards:** Generated image + product/category/scene details + V1-V8 validation checklist
- **Reference section:** Shows concept image + product reference side by side
- **Feedback composer:** Send follow-up requests without clearing output
- **History:** Server-side persistence, survives page refresh. Shows all past generations with thumbnails.

---

## Tabs

| Tab | Status | What it does |
|---|---|---|
| **Home** | Done | Revenue, active convos, pending approvals, system health |
| **Content Gen** | Done | UGC / Brand / Bespoke image generation with Direction chat |
| **Marketing** | Planned | Caption gen, creative picker, ad launch |
| **CRM** | Planned | Orders pipeline, source attribution |
| **Chatbot** | Planned | Live conversations, handoff queue |
| **Monitoring** | Done | 9 service status rows, auto-poll, Fix buttons, log viewer |
| **Image Bank** | Planned | Chatbot bank, FB stories pool, prodref library |
| **Inventory** | Planned | Per-SKU counts, low-stock alerts |

---

## Monitoring

| Service | Active means | Fix button |
|---|---|---|
| Chatbot Flask | HTTP 200 on localhost:8080 | Start chatbot server |
| Cloudflare Tunnel | chatbot.duberymnl.com reachable + cloudflared running | Start tunnel |
| Worker Fallback | WORKER_URL responds | -- |
| Meta Ads | 1+ active adset (expensive check) | -- |
| Story Rotation | GH Actions run <4h + success (expensive) | -- |
| Rasclaw TG | Telegram getMe ok | -- |
| DuberyMNL TG | Telegram getMe ok | -- |
| CRM Sheet | Google Sheets header read ok | -- |
| Inventory | Placeholder | -- |

Fix buttons appear on offline/degraded services with known remediation. Click to auto-start. Toast notification confirms success/failure.

---

## Toast Notifications

Slide-in notifications (top-right) for generation events, fix results, and errors. Color-coded: green (success), yellow (warning), red (error), orange (info).

---

## API Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/health` | GET | Server health check |
| `/api/home/summary` | GET | Home tab tile data |
| `/api/monitor/status` | GET | All 9 service states (parallel) |
| `/api/monitor/logs/<service>` | GET | Last 50 lines from service log |
| `/api/monitor/fix/<service>` | POST | Run fix command for a service |
| `/api/products` | GET | Product keys from product-specs.json |
| `/api/content-stats` | GET | Image counts per product per type |
| `/api/upload-concept` | POST | Upload pasted concept image to .tmp/ |
| `/api/log-generation` | POST | Log generation event with full metadata |
| `/api/generation-history` | GET | All past generation entries (JSON) |
| `/api/images/<path>` | GET | Serve images from project directory |
| `/api/agent/chat` | POST | SSE stream from Claude agent session |

---

## Port Map

| Port | Service |
|---|---|
| 8080 | Chatbot (Flask) |
| 8090 | Command Center (this) |
| 8123 | review.duberymnl.com tunnel |
| 8124 | tag.duberymnl.com tunnel |

---

## Files

```
command-center/
  app.py                    # Flask server + all API routes
  agent_session.py          # Claude Agent SDK session wrapper (max_turns=30)
  boot.bat                  # Windows startup script
  requirements.txt
  .env.example
  monitors/
    __init__.py             # ServiceStatus dataclass + registry
    registry.py             # Wire all 9 monitors
    chatbot.py / tunnel.py / worker_fallback.py / meta_ads.py
    story_rotation.py / rasclaw_tg.py / chatbot_tg.py
    crm_sheet.py / inventory.py
  templates/
    shell.html              # Single-page app shell
    tabs/
      home.html / content_gen.html / marketing.html
      crm.html / chatbot.html / monitor.html
      image_bank.html / inventory.html
  static/
    css/main.css            # Light Claude AI theme
    js/
      shell.js              # Hash-based tab routing
      home.js               # Home tab polling
      monitor.js            # Monitor rows + fix buttons + logs modal
      content_gen.js         # Content Gen: pills, direction chat, SSE, image cards
      bot.js                # Floating AI chat FAB
      toast.js              # Toast notification system
    favicon.ico
```

---

## Roadmap

| Phase | Status | Scope |
|---|---|---|
| 1 | Done | Backend, shell, Home, Monitoring, floating bot |
| 2 | Partial | Content Gen (done), Marketing + proactive bubbles (remaining) |
| 3 | Planned | CRM, Chatbot feed, Image Bank, Inventory, demo video |
