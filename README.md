# DuberyMNL

AI-powered social media automation for **DuberyMNL Polarized Sunglasses**, a real e-commerce brand on Facebook.

The system automates the creative pipeline end-to-end: caption generation, AI image creation, ad staging, and posting. Built as a live portfolio project demonstrating agentic automation with Claude Code.

---

## What It Does

```
Marketing idea
  -> WF1: Caption generation + human approval
  -> WF2: AI image generation (kie.ai / Nano Banana 2)
  -> WF3a: Auto-post to Facebook (LIVE -- queue + hourly cron; single, multi-photo, collage modes)
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

- **2026-05-26** **CC Experiment Mode v1 built (session 178).** Toggle in `Content Gen > Settings` flips the form into "client-mode": pick a saved client profile (Optikhaus seeded), paste/upload N product references + brand-context caption, hit Generate. A server-side orchestrator at `tools/image_gen/batch_experiment.py` (~190 lines, deterministic only) shells out to `generate_vertex.py` sequentially with the manual-Optikhaus pacing baked in (30s sleep between calls when count > 5, 45s + retry on 429/RESOURCE_EXHAUSTED). Outputs land in `contents/experiments/<ts>_<slug>/` with a `run.json` manifest, `refs/` copies, and `NN_<slug>.png + _prompt.json` pairs. UI polls `/api/experiment/status/<run_id>` every 2s for live progress; Stop cancels polling but the server batch always finishes (no orphaned Vertex calls). 5 new Flask routes added between lines 491-494 of `command-center/app.py` (~205 lines: GET/POST `/api/clients`, POST `/api/experiment/upload-ref`, POST `/api/experiment/start`, GET `/api/experiment/status/<run_id>`). Seed `contents/clients/profiles.json` ships with Optikhaus Optometry pre-loaded. Mode pills (`ugc / brand / bespoke`) untouched -- Experiment is a meta layer, not a replacement. v1 prompt template is intentionally bare (`<brand_context truncated to 800 chars>` + standard ad-shot frame); branching the template on Mode/Type is a v2 lever once we see first real client deliverables. Pattern generalizes the manually-validated Optikhaus workflow from earlier the same session (12 ad-ready images for a Malaysian eyewear retailer using Oakley products) -- this is the demo asset for the RAS Creative SOLUTIONS cold-outreach pitch. Backend live-test still pending a proper CC restart (current pythonw on :8090 is pre-edit, returns 405 for the new routes). See `project_cc_experiment_mode_shipped.md`.
- **2026-05-26** **IG @duberymnl.ph identity stack live + warmup plan drafted (sessions 175 sidequest + 177).** Old `@duberymnl` IG recovery abandoned (yahoo + SMS recovery vectors both dead). Fresh `@duberymnl.ph` created on master `duberymnl@gmail.com` + current PH phone; Business / Retail; linked to Dubery MNL FB Page via Meta Business Suite (IG auto-eligible as ad placement, Page admin recovery channel locked in). Lifestyle-led bio drafted, ready to paste. 5-phase warmup plan: Phase 0 profile completion -> Phase 1 social proof signals -> Phase 2 FB cross-promote -> Phase 3 first posts every 2 days -> Phase 4 normal cadence -> Phase 5 ads. Manual mobile-only posting for week 1-2 to avoid spam-flag (Meta watches "human signals" on fresh accounts); IG posting tool build (extending CC Schedule tab, ~1-2 hrs) explicitly deferred until organic activity is established. Older brand Gmail `duberymanila@gmail.com` also recovered same day via FB-inbox clipboard trick (separate from IG, kept as secondary brand inbox). See `reference_dubery_instagram_account.md`, `project_ig_warmup_plan.md`, `feedback_ig_api_vs_manual_warmup.md`, `reference_duberymanila_gmail_account.md`, `reference_dubery_gmail_account.md`.
- **2026-05-26** **Ads-report builder prototype + Meta attribution gap discovered (session 176).** New `.tmp/build_ad_report.py` builds a one-shot HTML ad-performance report combining Meta insights, Orders sheet truth-source, and rule-based per-ad verdict / why / opportunity (9 ordered patterns). Reveals: Meta reports 2 purchases over 30d but Orders sheet shows 7 orders / 13 units / ~₱7.5K gross -- Pixel install 5/20 + 7d-click window + non-ad source mismatch stack into a 5-order gap. Visual pattern analysis from reading 6 actual ad images surfaces 4 rules driving CTR (high-contrast lens vs bg / big typography hooks / monochromatic palette commitment / industrial > leisure settings). Six funnel KPIs codified with Dubery-specific targets (CTR ≥ 2.0% / CPC ≤ ₱1.30 / LPV-rate ≥ 40% / Msg-rate ≥ 0.8% / Cost-per-Msg ≤ ₱150 / Cost-per-order ≤ ₱320). Report includes Creative Pattern Breakdown grouping ads by Format / Product / Colorway / Style with one-line takeaway each. Filter+sort+mark toolbar with localStorage-persisted picks tray. Prototype lives in `.tmp/` (gitignored) pending CC migration: `tools/meta_ads/pull_creative_report.py` + new Marketing tab "Creative Performance" section + Sunday 8pm cron + TG ping. Recommended Meta consolidation move next session: pause Bespoke UGC adset, lift `bandits-tortoise-edit` into Brand Graphics, bump daily budget ₱140 → ₱200-250 (Path 2 -- triggers "Learning Limited" not full relearn, keeps 20d audience signal). See `project_ad_report_builder.md`, `feedback_meta_attribution_gap_2026_05_26.md`, `feedback_meta_relearning_paths_2026_05_26.md`, `feedback_dubery_visual_ad_patterns.md`, `reference_ad_kpi_targets.md`.
- **2026-05-25** **CC Marketing tab v2 — analytics dashboard (session 174 add).** Rewrote the Marketing tab from staging-only UI to analytics-first dashboard following the Home tab pattern. 6 sections: account snapshot strip (Spend / Impr / Clicks / LPV / Msgs / Pixel Purchases over 7d), adsets-running table with daily budgets + statuses, sortable live-ads leaderboard with Meta creative thumbnails (default sort Cost/LPV ascending, green/red color cues on CTR + Cost/LPV based on per-batch averages), Pixel funnel events (PageView / ViewContent / AddToCart / Purchase) with gap callout against Orders sheet, 14-day SVG trend chart (Spend + LPV + CTR, no Chart.js dep), Page Analytics + Needs Attention split (pause candidates / top spender / watching / gap derived from the data). Existing creative-staging UI preserved in a `<details>` collapse at the bottom, lazily initialized. Two new standalone Python pullers: `tools/meta_ads/pull_live_meta.py` (adset budgets + statuses + ad statuses + creative thumbnails) and `tools/meta_ads/pull_pixel_stats.py` (site-wide Pixel events, not just ad-attributed). `tools/meta_ads/pull_insights.py` gained `--output` flag so the 14d daily breakdown doesn't clobber the 7d summary. Single consolidated `GET /api/marketing/summary` reads cached files (no Meta API calls from Flask); manual `POST /api/marketing/refresh` button subprocesses all 4 pullers sequentially (~10-15s) with per-step status return. No mutation endpoints from this UI — refresh is read-only; existing PAUSED-only Stage flow unchanged. Live data validated at ship: ₱882 spend / 251 LPV / 4 messages / 1 Pixel purchase, 24 active+spending ads with thumbnails rendered. Bug surfaced mid-build: Meta's `/{pixel_id}/stats?aggregation=event` response shape has nested `data: [{value, count}]` per bin, NOT the `value: {Name: N}` dict the docs implied — captured as `feedback_meta_pixel_stats_shape.md`. See `project_cc_marketing_tab_v2.md`.
- **2026-05-25** **CC dashboard overhaul (session 174).** CRM tab is now production-ready: 5 tiles (Total Leads / Total Orders / Total Revenue excl. cancelled / Orders 24h rolling / Units Sold 30d) with hover-tooltips explaining source + rule; click any row in Leads or Orders tables → modal with full detail; Page Analytics tiles populated for first time (Reach 283K / Engagements 8.7K / Page Views 3.9K) after rotating Meta Page Access Token through the Use Cases panel with `read_insights` + 4 other scopes (13 total now). Schedule tab gained click-to-detail on every queue card → FB-styled preview modal (capped 560px feed-width, real fb-grid logic) with Edit button on Upcoming → caption textarea + datetime-local input → Save via new `POST /api/schedule/edit` endpoint (validates future-PHT + status=APPROVED). Columns collapse to 4 newest with "Show N more" toggle. Schedule picker now scans `contents/runs/{ts}_bespoke/` (was invisible), got a zoom slider (80-280px), hides filename + DRAFT pill on thumbs, resizable modal. Same zoom slider added to Image Bank tab (100-320px). Favorites unified: Image Bank + Schedule picker share `contents/ready/favorites.json` via `/api/schedule/favorites`; one-time localStorage migration on first load. AI Suggest agent rewritten from "3 fixed-menu options" to a thinking skill: 4-step framework (READ IMAGE → MATCH REGISTER → 5-8 OPTIONS with labels emerging from the image → PICK + INVITE NEXT MOVE); brand voice evolution baked in ("same 499, but imagery leveled up — voice follows image"); `duberymnl.com` CTA cadence ~1-of-3-4 captions weighted to product-forward angles; iteration rule deepens threads on followup. Chat history persists to `.tmp/sched_chat_history/<sid>.json` after every turn (survives CC restart with Claude resume_id intact); `GET /api/schedule/chat/sessions` lists past brainstorms. Emoji picker in Schedule chat composer (5 groups, 40 emojis). Cloudflare Worker first-touch gate shipped (v `625f9589`) — when laptop is asleep, worker only auto-replies to senders not seen in 24h; active conversations get silence. CC perf: bearer-token Sheets reader (urllib3) + 30s TTL cache = cold 2.77s, warm ~50ms; Refresh button bypasses via `?fresh=1`. Sheet writes: Jeffrey Arragona DELIVERED, Apollo Planas CANCELED. See `project_cc_dashboard_overhaul_2026_05_25.md`, `project_ai_suggest_skill_rewrite.md`, `reference_meta_use_cases_picker.md`, `feedback_thumb_url_for_grids.md`.
- **2026-05-21** **Schedule v2 SHIPPED + image bank overhaul.** All 21 v2 plan tasks landed: top-tab pill bar `[Compose | ✨ AI Suggest | 📅 Calendar]` on Schedule tab; Calendar with PH holidays + manual events JSON (`references/ph_holidays_2026.json` + `ph_events_manual.json`) + month grid + tooltip + selected-day panel; AI Suggest chat backed by Sonnet 4.6 via `claude_agent_sdk` with auto-injected upcoming-holidays system prompt, preset Quick Ask chips, OPTION-card parser with Copy buttons, per-tab session + Reset. Image bank rebuilt: scans `contents/ready/` + `contents/new/` (was POST-tagged-only) so **570 images** now visible vs prior 214; new `/api/thumb/<path>?w=240` endpoint with on-demand Pillow JPEG cache (~106× smaller, 1.5MB → 15KB per tile); click-to-preview lightbox; ★ Favorites + Archive + Delete actions (server-persisted to `contents/ready/favorites.json` + `archived.json`; delete soft-moves to `.tmp/bank_trash/<YYYY-MM-DD>/`); Drafts chip surfaces `contents/new/` with purple badge; Model + Sort dropdowns + Refresh button. CC now runs in the background via `pythonw.exe` + new `command-center/boot-bg.bat` + VBS shim (no visible cmd window; logs tail to `.tmp/cc.log`); subprocess monkey-patch with `CREATE_NO_WINDOW` so child Claude CLI processes don't pop console windows on each chat call. Content Gen got the "Check this week's PH context" preset + auto-injection of upcoming PH holidays into every Direction prompt. Bug fixes: regex char-class crash `[-:--]+` (range out of order) was killing the entire `schedule_chat.js` IIFE; `sched:images-changed` custom event added so AI Suggest reacts live to composer image changes.
- **2026-05-21** **Ops recovery: HKCU user PATH wiped on reboot, killed chatbot + Command Center + Rasclaw TG startup.** Diagnosed via `reg query HKCU\Environment /v Path` (key absent). Fixed with `setx PATH` (Python312 + npm dirs) — next reboot will auto-recover. `chatbot/start-monitor.bat` + `command-center/boot.bat` also patched to use full python.exe path as belt-and-suspenders. VBS-shim launch pattern (`WScript.Shell.Run`) documented for relaunching `claude --channels` from MINGW bash — `start ""` from bash doesn't give the child a real TTY, claude falls back to `--print` mode and errors. All three services back online; cloudflared tunnel never went down. See `feedback_user_path_wipe_2026_05_20.md` memory.
- **2026-05-21** **Feed scheduler v1 SHIPPED.** Queue-based FB Page scheduler with multi-image + 7-layout Pillow collage support (`tools/facebook/queue_helpers.py` + `queue_add.py` + `post_from_queue.py` + `tools/image_ops/compose.py`). CC Schedule tab live at `https://cc.duberymnl.com/#schedule` with 3-column queue (Upcoming/Posted/Failed), bank picker modal, live FB-style preview, drag-reorder image strip. Windows Task `DuberyMNL_FeedScheduler` registered (hourly). CC sidebar now collapsible (chevron + localStorage). 4 live posts validated incl. one cron-fired unattended. WF3a unblock confirmed -- no Meta verification required, current `META_PAGE_ACCESS_TOKEN` has `pages_manage_posts`. v2 plan ready at `.tmp/plan_v2.md` (AI Suggest chat + PH-holiday-aware calendar, 21 tasks ~5-6 hr); paused to use v1 in real workflow first.
- **2026-05-20** Evaluated Printing Press CLI factory (mvanhorn's `cli-printing-press`, 144-CLI library at printingpress.dev) as a token-efficient replacement pattern for MCP servers. Installed Go 1.26.3, factory binary v4.9.0, and coingecko-pp-cli as a no-auth test target — validated depth across 12 endpoints including live prices for AXS / RON in USD+PHP, SQLite sync of 17K coins, and `agent-context` capability discovery. Measured ~64% token reduction in `--agent` mode. Reference saved at `reference_printing_press.md`. CapCut is NOT a candidate (desktop app, no HTTP surface); CapCut Web or template API would be.
- **2026-05-20** Video dissection workflow developed: extract frames at 3fps + 480px wide, read 1→N in continuous sequence, output motion-focused markdown (frame-by-frame walkthrough, transition vocabulary, repurpose ideas). Validated on the ElevenLabs Scribe v2 Realtime trailer — see `.tmp/HnVideoEditor_2026_05_19_231144031_dissection.md` for reference output. Pre-skill stage before promoting to `/dissect-video`. Critical learning: sparse frame sampling captures composition but loses motion entirely — must read consecutive frames.
- **2026-05-19/20** Cross-project cleanup roadmap complete (Sessions A-I from EA-brain Session 133). 23 local commits across 11 repos. `duberymnl-automation-v2` moved to `~/projects/_archive/` + GitHub archived. ra-sync confirmed as the auto-memory backing store — `ra-sync/memory/` is the physical files, `~/.claude/projects/c--Users-RAS-projects-DuberyMNL/memory/` is a Windows junction pointing into it. Not stale, do not archive. Tooling: bun 1.3.14 + `bunx` shim + rclone v1.74.1 installed.
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
- **WF3a** Auto-posting: **LIVE** -- queue-based scheduler + hourly Windows cron (`DuberyMNL_FeedScheduler`); supports single-photo, multi-photo, and 7-layout Pillow collage modes; CC Schedule tab + 4 live FB posts validated 2026-05-21
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
