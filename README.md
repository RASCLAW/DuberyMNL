# DuberyMNL

AI-powered social media automation for **DuberyMNL Polarized Sunglasses**, a real e-commerce brand on Facebook.

The system automates the creative pipeline end-to-end: caption generation, AI image creation, ad staging, and posting. Built as a live portfolio project demonstrating agentic automation with Claude Code.

---

## What It Does

```
Marketing idea
  -> WF1: Caption generation + human approval
  -> WF2: AI image generation (kie.ai / Nano Banana 2)
  -> WF3a: Auto-post to Facebook (pending Meta verification)
  -> WF3b: Meta Ads staging
```

- Captions generated from product context, audience, and promotional strategy
- Captions transformed into structured JSON prompts for image generation
- Images produced via kie.ai (Gemini-backed) with precise parametric control
- Pipeline tracked in Google Sheets as source of truth
- Ad creatives staged directly via Meta Ads API

---

## Stack

| Layer | Tool | Role |
|-------|------|------|
| Orchestration | Claude Code (Opus) | Agent -- reads context, makes decisions, calls tools |
| Image Gen | kie.ai / Nano Banana 2 | Hyper-realistic product photos from JSON prompts |
| Data | Google Sheets + Drive | Pipeline tracker, asset storage |
| Ads | Meta Ads API | Creative upload, ad staging, insights |
| Posting | Facebook Graph API | Scheduled organic posts |
| Hosting | Vercel | Landing page (duberymnl.com) |
| Scripts | Python | 30+ deterministic tools for execution |

---

## Repository Structure

```
DuberyMNL/
├── tools/                  # Python scripts (pipeline, image gen, ads, sheets, drive, etc.)
├── dubery-landing/         # Live landing page (Vercel)
├── chatbot/                # Messenger chatbot -- Flask + Cloudflare Tunnel + Worker fallback
├── contents/
│   ├── assets/             # Runtime deps: fonts, logos, product-refs (committed)
│   ├── new/                # Staging for pre-review content (gitignored)
│   ├── ready/              # Approved content (gitignored, synced to Drive)
│   └── failed/             # Rejected content (gitignored)
├── archives/               # Historical backups (gitignored, synced to Drive)
├── references/             # Technical reference docs + supplier images (partially gitignored)
├── .claude/
│   ├── skills/             # DuberyMNL-specific Claude Code skills
│   ├── agents/             # Subagent definitions
│   ├── commands/           # Custom slash commands
│   └── hooks/              # Git hooks
├── decisions/log.md        # Append-only decision log
├── CLAUDE.md               # Project-specific agent instructions
└── .env                    # API keys (gitignored)
```

**Storage model:** Git holds code and runtime-dependency assets (anything skills/website read at runtime). Generated content, archives, and supplier reference material are gitignored and backed up to Google Drive. See [Setup](#setup) for bootstrap on a fresh machine.

Global EA config lives at `~/.claude/` (CLAUDE.md, rules, cross-project skills).
Context files live in `~/projects/EA-brain/`.

---

## Recent Changes

- **2026-05-20** Evaluated Printing Press CLI factory (mvanhorn's `cli-printing-press`, 144-CLI library at printingpress.dev) as a token-efficient replacement pattern for MCP servers. Installed Go 1.26.3, factory binary v4.9.0, and coingecko-pp-cli as a no-auth test target — validated depth across 12 endpoints including live prices for AXS / RON in USD+PHP, SQLite sync of 17K coins, and `agent-context` capability discovery. Measured ~64% token reduction in `--agent` mode. Reference saved at `reference_printing_press.md`. CapCut is NOT a candidate (desktop app, no HTTP surface); CapCut Web or template API would be.
- **2026-05-20** Video dissection workflow developed: extract frames at 3fps + 480px wide, read 1→N in continuous sequence, output motion-focused markdown (frame-by-frame walkthrough, transition vocabulary, repurpose ideas). Validated on the ElevenLabs Scribe v2 Realtime trailer — see `.tmp/HnVideoEditor_2026_05_19_231144031_dissection.md` for reference output. Pre-skill stage before promoting to `/dissect-video`. Critical learning: sparse frame sampling captures composition but loses motion entirely — must read consecutive frames.
- **2026-05-19/20** Cross-project cleanup roadmap complete (Sessions A-I from EA-brain Session 133). 23 local commits across 11 repos. `duberymnl-automation-v2` moved to `~/projects/_archive/` + GitHub archived. ra-sync confirmed as the auto-memory backing store (Windows junction) — not stale, do not archive. Tooling: bun 1.3.14 + `bunx` shim + rclone v1.74.1 installed.
- **2026-05-16** CC Video tab fully iterated: paste-to-frame (image absorbed into chat on Ask), preset chip with fidelity instructions, pulsing progress timer, compact video bank (80px thumbnail rows + play toggle), `/api/video-bank` endpoint. Fixed `upload-concept` multipart bug, Windows path normalization for `--image`. Pipeline: direct Veo 3.1 via `generate_videos.py` (not kie.ai). First video confirmed: `video_1778937670574.mp4` (lite, 2.2MB).
- **2026-05-15** COD fee (50) added to single-pair checkout with upsell bar; waived on 2+ pairs. Chatbot knowledge base updated to match. **Deploy note:** `vercel --prod` CLI produces UNKNOWN/0ms builds when Cloudflare proxy is active -- always deploy via `git push` to trigger Vercel's GitHub integration instead.
- **2026-05-15** Order notifications live: Apps Script webhook now pings Telegram (RasClaw bot) on every new order from duberymnl.com. Chatbot autostart fixed -- `monitor.log` file lock on boot resolved by removing shell redirect from `start-monitor.bat`.
- **2026-05-06** Ads staging overhauled: `stage_creatives.py` now supports per-creative captions, messages objective (OUTCOME_ENGAGEMENT / CONVERSATIONS / MESSAGE_PAGE), and multi-objective campaign tracking. Fixed Meta API targeting bug (saved_audience ID invalid; full spec now stored in `command-center/presets/marketing.json`). 4 plan files ready in `.tmp/` (traffic + messages × bespoke + brand).
- **2026-05-05** Meta Commerce Catalog wired via Graph API -- all 11 products live (Bandits x5, Outback x4, Rasta x2), PHP 699/499 pricing. See `tools/meta/`
- **2026-05-04** CC Content Gen tab: Ask button fix, pipeline prompt hardened, fidelity anchor wired permanently into dubery-fidelity-prompt skill
- **2026-04-26** Landing page v3 (Knockaround-style) live on Vercel at duberymnl.com

---

## Pipeline Status

- **WF1** Caption generation + approval: Done
- **WF2** AI image generation: Done
- **WF3a** Auto-posting: Built, blocked on Meta Business Verification
- **WF3b** Ad staging: Manual via API
- **WF4** Chatbot: Live (Flask + Cloudflare Tunnel)
- **WF5** Catalog: Done -- 11 products in Facebook Commerce catalog via Graph API

---

## How It Works

The project follows a separation of concerns:

- **Agent (Claude)** handles reasoning, orchestration, and decision-making
- **Tools (Python scripts)** handle deterministic execution -- API calls, data transforms, file ops
- **Skills (Claude Code)** provide reusable workflows triggered by name or context

This keeps AI focused on what it's good at (judgment calls) while scripts handle what they're good at (consistent execution).

---

## Setup

Bootstrapping a fresh clone on a new machine:

```bash
# 1. Clone
git clone https://github.com/Rasclaw/DuberyMNL.git
cd DuberyMNL

# 2. Python env
python -m venv .venv
.venv/Scripts/activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install -r requirements.txt

# 3. Secrets (not in git)
#    Copy .env from Google Drive: My Drive/DuberyMNL/secrets/
#    Copy token.json + credentials.json from same location

# 4. Content backup (not in git -- code works without, but skills need assets)
#    Skills that run image generation require product refs, supplier images,
#    and archived content. Pull from Drive:
#
#    Source:  My Drive/DuberyMNL/backup/
#    Targets:
#      contents/new/                 -- pre-review staging (optional)
#      contents/ready/               -- approved content  (optional)
#      contents/failed/              -- rejected content  (optional)
#      archives/                     -- historical backups (optional)
#      references/supplier-images/   -- supplier product shots (optional, reference only)
#
#    Sync any direction with tools/drive/sync_folder.py (see --help).

# 5. Verify
python tools/status.py          # prints pipeline counts
```

**Note:** `contents/assets/` (fonts, logos, product-refs) IS in git — skills depend on it at runtime. Everything else under `contents/` is output/staging and lives only on the working machine + Drive.

---

## Author

**Ronald Adrian Sarinas (RA)**
AI automation builder. Building agentic systems as proof of work for a career pivot into AI/automation.
