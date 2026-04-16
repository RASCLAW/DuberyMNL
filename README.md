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

## Pipeline Status

- **WF1** Caption generation + approval: Done
- **WF2** AI image generation: Done
- **WF3a** Auto-posting: Built, blocked on Meta Business Verification
- **WF3b** Ad staging: Manual via API
- **WF4** Chatbot: On hold

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
