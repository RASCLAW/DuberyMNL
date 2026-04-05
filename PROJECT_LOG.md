# DuberyMNL Project Log

Previous sessions (1-72) archived in `archives/pre-ea-rebuild/PROJECT_LOG.md`.

---

## Session 73 -- 2026-04-03 (EA rebuild + Claude Code docs study)

### What
- Full EA rebuild using Executive Assistant Initialize Prompt as blueprint
- Created ~/projects/EA-brain/ as dedicated global brain repo (context/, decisions/, projects/, templates/, references/, archives/)
- Set up global ~/.claude/CLAUDE.md with @imports from EA-brain context files
- Created 3 global rules: communication-style.md, build-quality.md, tool-development.md
- Moved 6 cross-project skills to ~/.claude/skills/ (skill-builder, pre-compact, frontend-design, nano-banana-2, vscode-tunnel, video-to-website)
- Slimmed DuberyMNL CLAUDE.md to project-specific only (tools, pipeline, skills, kie.ai quirks)
- Archived old WAT framework, workflows, docs, journal, scripts, 125K PROJECT_LOG to archives/pre-ea-rebuild/
- Reset auto-memory (old 13 files archived to EA-brain, fresh MEMORY.md)
- Added verification section to DuberyMNL CLAUDE.md
- Updated README.md to reflect current state
- Added .worktreeinclude for worktree credential copying
- Added Windows notification hook to global settings
- Set auto mode as default permission mode in VS Code
- Added $schema to settings.json files for autocomplete
- Added session naming to global CLAUDE.md session rhythm
- Re-authenticated GDrive MCP (token.json was missing after PC rebuild)
- Installed prompt-master skill globally (from github.com/nidhinjs/prompt-master)
- Installed excalidraw-diagram skill globally (from GDrive collection)
- Comprehensive Claude Code docs study session covering: skills, hooks, subagents, agent teams, MCP, channels, plugins, settings, CLI, commands, env vars, tools, security, costs, setup
- Saved 3 reference docs to EA-brain: claude-code-what-we-know.md, claude-code-docs-reference.md, claude-code-changelog.md
- Saved skill templates from GDrive: frontend-website, n8n-workflow-builder, trigger-dev CLAUDE.md files + skill debugging guide

---

## Session 74 -- 2026-04-03 (remote-access-setup)

### What
- Rewrote `/vscode-tunnel` skill from WSL2 to Windows native (code-tunnel.exe with built-in status/kill/restart)
- Started tunnel, verified remote access works from vscode.dev with Claude Code extension
- Installed tunnel as Windows service -- auto-starts on boot, auto-restarts on crash, no manual intervention
- Changed power settings: AC lid close = do nothing, DC lid close = do nothing + sleep after 30min idle
- Git-tracked `~/.claude/` as private repo (RASCLAW/claude-config) -- skills, rules, memory, commands, agents all backed up
- Built `tools/drive/backup_secrets.py` -- backs up .env, credentials.json, token.json, .credentials.json to Google Drive
- Ran first secrets backup (4 files to DuberyMNL/Backups/secrets/ on Drive)
- Upgraded `/log` command -- context review, double-check with RA, memory save, secrets backup, multi-repo commit

### Decisions
- VSCode tunnel as Windows service instead of manual background process -- auto-start, auto-restart, zero maintenance
- AC lid close = do nothing (tunnel stays alive), DC = do nothing + 30min sleep (saves battery)
- ~/.claude/ backed up via git (claude-config), secrets backed up via Google Drive -- two-layer protection
- projects/ in claude-config only tracks memory/ dirs, ignores conversation logs (ephemeral, large)

### Deployed
- claude-config repo created and pushed to github.com/RASCLAW/claude-config (private)
- Secrets backed up to Google Drive (DuberyMNL/Backups/secrets/)
- VSCode tunnel service running (dubery-dev)

### Blockers
- None

### Decisions
- EA brain lives in dedicated repo (not inside ~/.claude/ or DuberyMNL) -- git-tracked, portable, clean
- Global CLAUDE.md imports context from EA-brain via @ absolute paths
- Cross-project skills at ~/.claude/skills/, DuberyMNL-specific at .claude/skills/ -- clear separation
- Auto-memory symlink to ra-sync kept for phone sync via ClaudeMob
- n8n deferred to backlog (high Upwork demand but no Docker setup yet)
- Rasclaw as Claude Code channel plugin added to backlog (replaces standalone bot approach)

### Deployed
- EA-brain repo pushed to github.com/RASCLAW/EA-brain
- DuberyMNL restructure pushed to github.com/RASCLAW/DuberyMNL
- ra-sync memory reset pushed to github.com/RASCLAW/ra-sync
- Global Claude Code config active (~/.claude/CLAUDE.md, rules/, skills/)

---

## Session 75 -- 2026-04-03 (dashboard-revival)

### What
- Built `/dashboard-moderator` skill at ra-dashboard/.claude/skills/ using skill-builder
- Full dashboard-db.json sync: location (Daet->Pasig), finances (P3k BPI, P2k cash), bills updated, vehicles, trip completed
- Added 13 transactions (Mar 31 - Apr 2): car gas, food, groceries, laptop repair (HDD+labor+battery)
- Added Zach (Arabelle's first son) to DB with clickable profile card + school break badge
- Restructured family bar: parents row + kids row
- Added vehicle cards to overview (car + moto gas levels, SLEX/NLEX RFID balances)
- Fixed Quick Stats: "BILLS DUE" -> "UPCOMING BILLS", added payday-aware insight logic
- Fixed RA status ignoring PH holidays (Informdata shift is non-negotiable)
- Loading screen "LIFE OS" -> "PROJECT DASH", removed footer
- Logged Arabelle possible UTI: health alert, todo, calendar contingency, life-log entry
- Baby Jah dietary milestone: eating rice + ulam regularly
- Re-authenticated Vercel CLI, 7 deploys during session

### Decisions
- RA work status ignores PH holidays (night shift regardless)
- Upcoming bills shown separately, not deducted from balance -- payday context instead
- Zach is temporary DB entry (remove when school break ends, chip auto-hides)
- PhilCare = RA (Informdata), Maxicare = Arabelle (Wells Fargo)

### Deployed
- ra-dashboard-lake.vercel.app -- 7 production deploys
- Dashboard moderator skill created

### Blockers
- Wire dashboard-moderator as scheduled remote agent (future session)
- Arabelle UTI monitoring -- doctor visit Apr 5 if not improving

---

## Session 76 -- 2026-04-03 (smoke-test-and-strategy)

### What
- Full DuberyMNL smoke test from work via VSCode tunnel
- Fixed .env: added GOOGLE_SHEETS_SPREADSHEET_ID, swapped User token for real Page Access Token
- Fixed utf-8 encoding bug in status.py (Windows cp1252)
- Re-authed OAuth with full scopes (Sheets + Drive + Gmail + Calendar)
- Validated all 36 IMAGE_APPROVED pipeline URLs on Drive -- all live
- Verified Facebook posting works (Meta Business Verification approved)
- Pulled Meta Ads insights: 27.9K impressions, P716 spend, 0 sales in 7 days
- Built `/dubery-ad-creative` skill -- ad prompts without prices (engagement-driven)
- Updated `/dubery-ugc-prompt-writer` default to 2K resolution
- Generated 5 UGC prompts + 1 ad creative, tested in Gemini web -- good enough for v1
- Created UGC tab in pipeline spreadsheet with IMAGE() thumbnails
- Backed up prompts + images to Google Drive (UGC - gemini web folder)
- Fixed token scope narrowing bug in read_sheet.py and write_sheet.py
- Patched GDrive MCP (OAuth2 client_id fix, needs Claude Code restart)

### Decisions
- Strategy pivot: Traffic campaign -> Messenger-first engagement funnel
- Remove prices from ad images to drive "magkano?" curiosity comments
- Comment-triggered DMs: "Comment DUBERY for P50 off" -> auto-DM with dual path (Messenger or landing page with discount code)
- Two image workflows: /dubery-ad-creative (ads, no price) + /dubery-ugc-prompt-writer (daily organic)
- UGC at 2K resolution, ad creatives at 1K
- UGC premium quality -- authentic feel but magazine-adjacent, not raw phone snaps

### Deployed
- Nothing deployed (smoke test + strategy session)

### Blockers
- GDrive MCP patch needs Claude Code restart
- Next: build chatbot order flow (WF4) + comment-to-DM webhook
- Landing page needs checkout with discount code support
- Campaign objective switch from Traffic to Messages/Engagement
- Content gen refinement over the weekend

---

## Session 77 -- 2026-04-04 (chatbot-engine)

### What
- Installed Claude Code CLI globally via npm (v2.1.91) for chatbot subprocess
- Built chatbot test web UI (tools/chatbot/test_web.py) with Messenger-like interface
- Exposed test UI via ngrok for remote testing from work
- Fixed claude --print: path resolution, stdin piping, system-prompt-file approach
- Iterated chatbot system prompt through ~8 revisions, landed on 95% English with light Filipino
- Added product image support: [IMG:filename] tags rendered inline using hero card shots
- Researched MCP research tools: Brave Search (free, recommended), Perplexity, Firecrawl
- Built first-message catalog flow: acknowledge + welcome + show 3 series images

### Decisions
- Claude CLI installed globally for chatbot (Max plan, no API cost)
- Sonnet over Haiku for chatbot (similar speed, better quality)
- 95% English for chatbot voice -- forced Taglish produces worse output
- Hero card shots for product images (shows full package)
- Brave Search MCP recommended for future install (deferred, needs credit card)

### Deployed
- Chatbot test UI running locally + ngrok (test only, not production)

### Blockers
- Finalize chatbot voice/tone over the weekend
- Fix conversation_store.py fcntl for Windows
- Build comment-to-DM webhook
- Wire chatbot to actual Messenger
- Install Brave Search MCP when card available

## Session 78 -- 2026-04-04 (portfolio-plan)

### What
- Rewrote dashboard moderator skill with Taglish persona, caring family tone, smart branching (<48hrs vs >48hrs stale)
- Logged 2 meals to dashboard, deployed to Vercel
- Explored hirejps.com via Playwright -- 12 screenshots, full text extraction, sections map
- Wrote comprehensive reference doc analyzing JPS site (ras-portfolio/references/hirejps/README.md)
- Created full portfolio rebuild + tool learning plan (3 phases, 8 weeks, saved to ~/.claude/plans/)
- Signed up for Make.com (free, eu1) and Zapier (Pro trial until Apr 17)
- Set up 3 MCP servers: Make.com (connected), n8n (connected docs-only), Zapier (needs home auth)
- Researched pricing for Make/Zapier/n8n/GHL -- all free except GHL ($97/mo)
- Drafted 5 Make.com workflow ideas for portfolio (basic to intermediate)
- Served portfolio via ngrok for work network access

### Decisions
- Stay vanilla HTML + Tailwind CDN for portfolio rebuild (no React migration)
- Dark theme (#0e0e0e) with red accent for portfolio (market standard)
- Tool learning order: Make -> Zapier -> n8n -> GHL (free first, expensive last)
- Rename Certificates section to "Skills & Proof" (live demos > paper certs)
- GHL 14-day trial saved for Week 5 (strategic sprint, screenshot everything, cancel)
- Pricing section uses "Revealing Soon" overlay until rates validated

### Deployed
- Dashboard updated + deployed (2 meals logged)
- Dashboard moderator skill rewritten (ra-dashboard repo)

### Blockers
- Authenticate Zapier MCP from home (browser OAuth)
- Build Smart Lead Router (#3) in Make.com (weekend)
- Portfolio rebuild after tool demos are ready
- Take professional headshot for portfolio hero section

## Session 79 -- 2026-04-05 (make-mastery)

### What
- Deep research on Make.com platform (pricing, modules, job market, certifications)
- Built Make.com mastery curriculum (4 phases, project-based) in EA-brain
- Created first Make.com scenario: Smart Lead Router with AI Classification
  - Google Forms v2 -> AI Toolkit v2 -> Router -> Gmail v4 + Google Sheets v2
  - 3-way routing: Hot (email + sheet), Warm (sheet), Cold (sheet)
  - AI classification with strict budget-based rules, tested 30+ submissions
- Created automation-workflows repo (cross-platform: Make/Zapier/n8n)
- Built /make-scenario-builder skill for MCP-based scenario creation
- Prototyped automated demo video pipeline
  - TTS narration (edge-tts), screen recording (FFmpeg), animated explainer (Pillow)
  - 20s animated explainer generated frame-by-frame, uploaded to Google Drive
- Re-authenticated Google OAuth with Forms scope, created Google Form via API
- Set up dual monitor workstation

### Decisions
- automation-workflows as cross-platform repo (not make-specific)
- Always use latest Make.com module versions (v2 Forms, v4 Gmail, v2 Sheets, v2 AI)
- MCP can create but not update/delete scenarios on free plan
- Screen recording via FFmpeg (imageio_ffmpeg), no extra software needed

### Deployed
- automation-workflows repo created on GitHub (RASCLAW/automation-workflows)
- Make.com curriculum + research pushed to EA-brain
- Lead Router scenario live on Make.com (ID: 5134999)
- Demo video uploaded to Google Drive

### Blockers
- Polish demo video (combine screen recording + animated explainer + TTS)
- Make.com Phase 2: DuberyMNL content notifier scenario
- Zapier MCP auth needs home browser

## Session 80 -- 2026-04-05 (make-demo-video)

### What
- Built demo video pipeline: TTS (edge-tts), screen recording (FFmpeg), Pillow animation
- Generated animated explainer videos (v1 geometric, v2 emoji/typography, Claude AI theme)
- Excalidraw integration: programmatic drawing via Playwright (updateScene API + mouse drawing)
- Downloaded icons8 icons (Google Forms, Sheets, Gmail, AI, Router)
- Built interactive HTML simulator (lead-router-v2.html):
  - Auto-playing loop of 10 leads with typing animation
  - Horizontal pipeline with emoji icons + pulse arrows
  - AI classification with loading bar, Gmail alert with SVG icon
  - Fixed metrics footer (Leads / 🥵🤖🥶 / Emails)
  - Claude AI warm beige theme, embeddable via iframe
- Screen recorded Make.com scenario (big monitor, 1080p)

### Decisions
- HTML simulator > Pillow video for portfolio demos (smoother, interactive, embeddable)
- Emoji smiley faces for categories (🥵 Hot, 😐 Warm, 🥶 Cold)
- SVG Gmail icon instead of generic email emoji
- Rename /log to /closeout (avoid /login autocomplete conflict)

### Deployed
- automation-workflows repo updated (demo scripts, icons, simulator, animations)

### Blockers
- Deploy simulator to Vercel for embedding
- Wire demo modal into ras-portfolio
- Continue Make.com Phase 2 (DuberyMNL content notifier)

## Session 81 -- 2026-04-05 (gmail-organize)

### What
- Audited Gmail inbox (11,574 emails, 10,633 threads, ~201 unread) via Gmail MCP
- Identified top noise sources by volume: Finance/BPI (1,178), LinkedIn (676), Discord (214), Meta (90)
- Installed GWS CLI (Google Workspace CLI v0.22.5) via npm, authenticated with Gmail scopes
- Enabled Gmail API in GCP project (duberymnl-automation)
- Created 6 Gmail labels: DuberyMNL, Finance, Dev, Job Hunt, Shopping, Notifications
- Created 6 Gmail auto-sort filters via Python API (GWS CLI has POST bug #188)
- Bulk-labeled 2,273 existing emails retroactively across all 6 categories
- Notifications (Discord/Pinterest/Spotify/Netflix/YouTube) auto-archive from inbox
- Upgraded token.json scopes: added gmail.modify, gmail.settings.basic, calendar

### Decisions
- Gmail label structure: DuberyMNL / Finance / Dev / Job Hunt / Shopping / Notifications
- Notifications category skips inbox (auto-archive) -- it's noise
- Used Python Gmail API for filters because GWS CLI has known POST bug (Issue #188)

### Deployed
- Gmail labels + filters live on sarinasmedia@gmail.com

### Blockers
- Next: Gmail cleanup (archive/delete old noise, refine label coverage)
- GWS CLI POST bug may be fixed in future versions -- revisit
- Could clean up old unused labels (Personal, Work, Receipts)

## Session 82 -- 2026-04-06 (zach-video-pipeline)

### What
- Dashboard moderator: 2-day sync, health alerts card added to renderOverview(), full data update (finances, baby jah eczema, calendar cleanup, Arabelle UTI escalation, Zach activities)
- Apr 11 trip: Iver Sage birthday + Pyro Musical itinerary researched and added to dashboard trips
- Built personalized Minecraft video pipeline for Zach (edge-tts + Pillow + FFmpeg)
- Video 1: "AI is a /command for real life" (55s, Minecraft intro)
- Video 2: "AI = Permanent Buff" (65s, use cases + privacy, gaming terms)
- Iterated voice (Andrew winner), script (no personal data, AI is infinite, gaming terms), visuals (pixel art MC characters)
- Created ~/projects/zach-content/ repo, moved scripts + videos there
- Saved /zach-video skill + Zach memory profile
- Dashboard: vape P840 + Jollibee P309 from BPI (P2552 -> P1403)
- Deployed dashboard 2x to Vercel

### Decisions
- Andrew voice for Zach videos (+15% rate, +50% vol, no pitch shift)
- Don't recite personal details in kid videos (creepy), don't limit AI to niches (infinite), use gaming terms from his games
- Separate zach-content/ repo for Zach content projects
- Pillow pixel art over smooth vector (plays to Pillow's strengths)

### Deployed
- Dashboard with health alerts card + data sync (2x Vercel)

### Blockers
- Arabelle Maxicare doctor visit (UTI day 3+, urgent)
- Baby Jah eczema pedia derma consult
- Pyro Musical 2026 schedule confirmation (next session loadout)
- Buy Iver gift + unsubscribe Tapo by Apr 10
- Clean up remaining .tmp/ files
