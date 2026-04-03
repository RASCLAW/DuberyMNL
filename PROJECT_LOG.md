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
