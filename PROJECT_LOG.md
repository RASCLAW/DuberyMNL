# DuberyMNL Project Log

Previous sessions (1-72) archived in `archives/pre-ea-rebuild/PROJECT_LOG.md`.

---

## Session 105 -- 2026-04-12 (niche-strategy-lock)

### What
- Loadout: dubery-dev tunnel healthy, power plugged, 3 active local Claude sessions (no orphans).
- Cleaned up uncommitted pre-session-98 state across both repos.
  - DuberyMNL `04e458e`: settings.local.json carry-over — 54 permission entries accumulated across sessions 97-104 (WebFetch for supplier/Meta docs, gcloud, curl, mkdir for supplier-image scraping).
  - ~/.claude `60797a6`: 3655 files. Upstream plugin sync included **telegram 0.0.4 → 0.0.5 upgrade** with orphan-kill poller (fixes the 409 Conflict bug when a prior `bun run` grandchild survives as an orphan), SIGHUP handling, reparent watchdog, PID file lifecycle. Session-report plugin got per-session timeline + by-day view. Slack plugin removed. Session-report LICENSE added. Runtime state: 17 new telegram inbox captures + bot.pid + telegram 0.0.5 plugin cache (25MB incl. node_modules, matching existing 0.0.4 pattern).
  - Both pushed to their origins.
- **Rasclaw-as-channel-plugin backlog item confirmed WORKING** — the telegram 0.0.5 upgrade IS this. Two-way chat + permission relay is operational. Backlog item struck.
- Strategic discussion of RAS Creative SOLUTIONS launch prep:
  - Challenged the "after chatbot recovery, execute..." sequencing from current-priorities — only step (e) case study page is strictly blocked on chatbot data; (a) repricing, (c) portfolio hero, (d) cold outreach drafts have zero dependency on chatbot recovery.
  - Surfaced 6 strategic questions: parallel vs sequential with chatbot recovery, send-before-proof yes/no, first sub-niche, PH-first or international-first, portfolio hero proof without DuberyMNL screenshots, sender identity for v1 outreach.
  - RA's dental/spa "sellout" intuition: correct at pitch layer globally.
- Ranked 10+ niche candidates (original 4 + 7 sleeper picks: solar, tour operators, review centers, wedding photographers, interior designers, immigration, car detailing) against ticket × competition × chatbot fit × moat fit × PH market size.
- **Surfaced email-first businesses as a valid frame** (RA introduced this explicitly) — unlocks solar commercial, immigration, architects, IT managed services that Messenger-first had been filtering out.
- Reframed RA's "research → source → personalize → send" workflow as both the deliverable AND the sales engine (workflow = product flywheel). Build once, fork per niche.
- Locked the full 6-niche prioritized list. Dropped dental/spa + review centers + generic home services.
- Wrote `project_ras_creative_niches.md` memory with full strategic lock, workflow flywheel diagram, passive reading track, "how to apply" + "do not drift" enforcement sections.
- Cross-linked bidirectionally: `project_positioning_locked.md` `related:` extended + Niche section points to narrowed list; `MEMORY.md` indexed new entry directly below positioning lock line.

### Decisions
- **Solar panel installers = RAS Creative SOLUTIONS primary niche.** RA's passion + desire to learn solar + battery tech = compounding moat nobody else can build (Filipino AI agencies have zero domain knowledge). Highest ticket per deal (P200K-P2M, one install = 12-24 months retainer paid). Near-zero AI agency competition in PH. Growing market (Meralco rates climbing, grid reliability degrading, battery storage boom). Fallout leads moat maps 1:1 to tire-kicker filtering at high volume.
- **Battery storage paired with solar, not a separate niche.** Same customer (most PH solar installers sell both), same sales flow (quote-driven, email-first, technical, long consideration), same knowledge base, zero forking cost. Frame as "PH clean energy installers" = one market, two pitch angles.
- **Strict gate: DuberyMNL must be COMPLETE before any RAS Creative SOLUTIONS build begins.** "Complete" = all 9 recovery steps including step 9 (1 week clean production data capture). Not a soft preference. Steps 1-8 are 2-3 active sessions; step 9 is a full week of waiting, which is the window where the passive reading track runs.
- **Final 6-niche prioritized list:** solar (primary) → battery (paired) → tour operators → wedding photographers → real estate → immigration → car detailing.
- **Dropped from consideration:** dental/spa (pitch saturation globally), review centers (RA "out of my league"), generic home services (retainer math too tight for solo operators).
- **Solar scope: residential + commercial, PH + international, email-first primary.** Automation handles both drafting angles. If international cold email doesn't land, fallback to Upwork / LinkedIn / industry forums.
- **Email-first businesses are valid targets.** Frame broadened beyond Messenger-first.
- **Workflow = product.** "Research → source → personalize → send" is BOTH the deliverable RAS Creative SOLUTIONS sells AND the sales engine for landing the first clients. Build ONE template, fork per niche. Flywheel: outreach engine lands solar client → same engine becomes their lead qualification system → their live data becomes the case study → stronger outreach → more solar → fork template to niche #2.
- **Sequential niche fork > parallel niche build.** Pick ONE niche (solar), ship it, land a client or learn why not, then fork template. Parallel dilutes personalization.
- **Passive reading track during DuberyMNL recovery window:** ~30 min/day idle reading on PH installers (Solaric, Buskowitz, Freedom Solar, Ram Mendoza), solar/battery FB groups, slow-reply complaint screenshots (pitch ammunition), technical articles (string inverters, net metering, LFP vs NMC, grid-tied vs hybrid), installer brand research (Solis, Sungrow, Deye, Huawei, BYD, Pylontech, Dyness). Zero-cost prep that compounds — by DuberyMNL step 9, RA will know more than 90% of "AI agency" pitchers.

### Deployed
- Cleanup commits only, no production code changes:
  - DuberyMNL `04e458e` (settings.local.json) → pushed origin/main
  - ~/.claude `60797a6` (plugin sync + TG state) → pushed origin/master
- Session 105 closeout commits to follow.

### Blockers
- **Chatbot recovery remains top priority (unchanged).** No work on RAS Creative SOLUTIONS build until complete.
- **Image bank expansion is the next actionable step** (step 1 of recovery path) but requires coordination — 2 other active Claude sessions were editing `cloud-run/knowledge_base.py` during this session. Can't start this in the current window without collision risk.
- **Named Cloudflare tunnel migration (recovery steps 2-4) still deferred** — RA hasn't carved out the dedicated ~15-20 min window yet.
- **RAS Creative SOLUTIONS strategy locked but gated.** Niche decisions are durable; no build work authorized until step 9 of chatbot recovery completes.

---

## Session 104 -- 2026-04-11 (positioning-lock)

### What
- Ran in parallel with session 103 (sonnet-delegation-policy) in the other VSCode window. No file collisions — different topic.
- Analyzed GCP billing CSV (Apr 6-11): $31.61 total, Vertex AI dominated ($29.42, 93%). Traced Apr 7 spike to UGC pipeline + Vertex migration (session 87) and Apr 8 to Veo 3.1 video gen testing (session 90). No ongoing burn concern (Cloud Run already deleted in session 101).
- Ingested Jordan Platten YouTube "Top 3 AI Systems Clients Pay $4K+/Month For" (KqjWm2bexUc) via `/ingest` skill. Archived raw transcript, wrote full summary with 6 action items + 7 bidirectional cross-refs, updated INDEX + ingest-log.
- Deep strategic repositioning discussion: walked RA through Jordan's "closer to revenue" framework, identified that DuberyMNL is already the System 1 + System 3 bundle Jordan describes, surfaced the contradiction with current Make/Zapier/n8n portfolio positioning.
- **Unlocked the Google fallout leads moat.** RA realized mid-conversation that his years at TDCX/Google weren't generic "leads qualification" — he was on Google's worldwide fallout leads team, rescuing stalled Google Ads registrations, free trial dropouts, and high-intent signals that went cold. He was literally the human version of Jordan's AI qualification layer, at Google TOS quality standards, worldwide. This is the moat.
- Helped RA shape the services > products insight: higher margins justify higher CPAs, trust-building fits Messenger culture, services genuinely need funnels (unlike products that fall back on marketplaces), repeat customers built in.
- Drafted 17 one-liner variants (A-Q) across authority/outcome/pain/contrast framings. RA iterated on prose structure (pain-first → fix → who-we-are) and finalized covering top/middle/bottom funnel leaks explicitly.
- **Locked the positioning statement** verbatim. Brand renamed: RAS AI SOLUTIONS → RAS Creative SOLUTIONS (Creative frames outcome; AI is the how). Niche locked: service businesses only. Pricing locked: retainer, not project fees.
- Rewrote `EA-brain/context/work.md` RAS service offering section with full niche, offer stack, retainer pricing, proof stack, outbound strategy, ascension path, DuberyMNL role.
- Rewrote `EA-brain/context/me.md` background with Google fallout leads moat framing.
- Created `project_positioning_locked.md` with verbatim statement + explicit "do not drift" rules listing what future sessions must push back on.
- Updated `project_portfolio_rebuild.md` with POSITIONING CONTRADICTION block referencing Jordan summary + positioning_locked.
- Added bidirectional back-links from `project_valor_internal_pitch.md`, `project_messenger_strategy.md`, `project_brand_pipeline.md` to `project_positioning_locked.md`.
- Updated MEMORY.md index with Jordan Platten summary + positioning_locked entries.

### Decisions
- **Brand rename: RAS AI SOLUTIONS → RAS Creative SOLUTIONS.** Deliberate positioning move — "Creative" frames the outcome and escapes the crowded AI vendor bucket. AI is the how, not the what.
- **Niche locked: service businesses only** (dental, med spa, aesthetics, real estate, law, home services, gyms, coaches, photographers, tutoring). Not product e-commerce.
- **Pricing model locked: retainer, not project fees.** Starter $1.5K-$3K/mo, Bundled $3K-$7K/mo, Premium $7K-$15K/mo. Old "$1K-$2.5K end-to-end" pricing killed.
- **Outbound strategy: small-scale targeted (20-50/day), not volume.** Matches RA's bandwidth + leverages Google fallout leads muscle memory (qualification > scale).
- **Public portfolio framing shifts** from "automation builder" to the locked positioning statement. Tool learning (Make/Zapier/n8n) stays as internal skill-building, but public positioning sells outcomes, not tools.
- **Valor internal pitch demoted** from co-primary to fallback. External service-business retainers are the primary play now.
- **Chatbot recovery reframed** from "DuberyMNL task" to "critical path to first paid client." Every day unwired is a day the case study page can't launch.
- **AI qualification layer is the unique IP.** RA can build scoring logic that actually works because he has years of manual qualification muscle memory from Google. Future sessions should emphasize this as the moat.

### Deployed
- Nothing deployed. Session was strategy + context work only. No code changes, no cloud-run/, no contents/, no tools/.

### Blockers
- `me.md` one-liner still says "AI systems builder by day" — RA explicitly paused next actions (chose option d, come back fresh). Not updated this session.
- First paid-client path unlocked but not actionable until DuberyMNL case study data exists (1 week of clean production runs). Chatbot recovery remains the gating milestone.
- Session 103 (sonnet-delegation-policy) ran in parallel in the other VSCode window — already committed its own closeout. Orphan PID 12952 idle 88min. No file collisions in shared files (EA-brain decisions/log.md, current-priorities.md) because the two sessions edited different sections.

---

## Session 103 -- 2026-04-11 (sonnet-delegation-policy)

### What
- Loadout killed 1 orphan `claude.exe` (PID 4292, 407MB freed). Orphan was session `9d630c24` from 2 days ago — VSCode `/clear` spawned a new process without terminating the old one.
- Walked backlog from recent sessions (98-102). Top chatbot blocker confirmed: image bank expansion (21 → ~35-40 with per-image captions) before re-wiring Meta webhook.
- Evaluated backlog item "convert /closeout, /savepoint, /loadout to Sonnet" → **rejected**. The thinking part (session analysis, memory drafting) can't leave Opus because only Opus has conversation context. Mechanical parts (Write/Edit/Bash) are cheap regardless of model, so delegating buys nothing. Backlog item crossed off.
- Built a Sonnet delegation policy for daily coding: delegate when input spec is short + work is long + summary-only output needed + no mid-task decisions. Unilateral delegate list: test runs, log scans, scraping, doc lookups, bounded audits. Never delegate: conversation-dependent work, decisions, closeout-style tasks.
- Saved `feedback_sonnet_delegation.md` with bidirectional back-links to `feedback_diagnostic_depth.md` + `feedback_claude_code_layers.md`. Indexed in MEMORY.md.
- Chatbot go-live gate-check: Flask DOWN, cloudflared DOWN, ephemeral quick-tunnel URL dead. Named Cloudflare tunnel path (`chatbot.duberymnl.com`) surfaced as prerequisite because quick tunnels get a new URL on every restart → Meta webhook would break on every reboot. Named tunnel requires moving whole `duberymnl.com` zone from Namecheap → Cloudflare nameservers.
- Chatbot go-live **deferred** — RA can't do the nameserver migration tonight.

### Decisions
- Don't convert `/closeout`, `/savepoint`, `/loadout` to Sonnet. The thinking part needs Opus context; mechanical part is cheap either way. (Cross-project decision logged in EA-brain.)
- Sonnet delegation policy: unilateral delegate for bounded grunt work (tests, log scans, scraping, doc lookups, audits). Ask first for bulk edits + live service work. Never delegate conversation-dependent work. Saved as feedback memory.
- Chatbot go-live path = **named Cloudflare tunnel at `chatbot.duberymnl.com`** (Option B), not ephemeral quick tunnel. Quick tunnel URLs rotate on every cloudflared restart → Meta webhook would need re-wiring on every reboot. Named tunnel requires full zone migration from Namecheap → Cloudflare.
- Named tunnel work deferred to a dedicated session (not tonight). Adds ~15-20 min best case to chatbot recovery path.

### Deployed
- Nothing deployed. Chatbot still DOWN.

### Blockers
- **Chatbot still DOWN.** Flask + cloudflared not running. Meta webhook pointing at deleted Cloud Run URL. Boosted ads paused.
- **Top chatbot recovery path (in order):** (1) image bank expansion 21 → ~35-40 with per-image captions, (2) named Cloudflare tunnel migration (`duberymnl.com` nameservers → Cloudflare), (3) wire webhook to `chatbot.duberymnl.com`, (4) unpause ads
- **Named tunnel prerequisites before starting:** confirm `ras@duberymnl.com` email routing (break if Namecheap forwarding is active), inventory any other subdomains/MX records on duberymnl.com, verify Vercel CNAME stays intact through migration
- `.claude/settings.local.json` still unstaged (shared between active sessions, leave alone)
- Other IDE session has in-flight work on MEMORY.md + `project_portfolio_rebuild.md` + cloud-run/ files — not touched per multi-session safety rule

---

## Session 102 -- 2026-04-11 (refactor-recovery-drive-workflow)

### What
- Loadout caught 2 orphan claude.exe sessions (PIDs 7776, 10572 -- 756MB freed)
- Enhanced `pc-status.ps1` with orphan detection (`--SessionsOnly` mode). Cross-references claude.exe PIDs with JSONL mtimes; idle >30min = ORPHAN. Updated loadout memory so it runs `remote-status.sh` + `pc-status.ps1 --SessionsOnly` every session going forward.
- Audited + verified the crashed pre-session-98 Karpathy/Nate Herk work sitting uncommitted: 53 deleted files (51 in archives/, 2 landing assets intentionally deleted), 13 skill rewrites, 12 tool scripts rewired to new paths, brand-bold with full WF2 fidelity port (R2/R3/R4), brand-callout + brand-collection with path updates only (fidelity port parked).
- **Committed `fc3bddf`**: 144 files, 524+/284-, the full refactor recovery. Git auto-detected the `packaging.png` rename (delete + add staged together).
- Built `tools/drive/sync_folder.py` -- local → Drive mirror, direct REST (not googleapiclient), idempotent, dry-run, unbuffered progress.
- Initially misattributed Google API timeouts to httplib2. Other IDE session's parallel diagnosis corrected it: **IPv6 is the root cause**. Python's `socket.getaddrinfo` returns IPv6 first for some Google endpoints, RA's home ISP doesn't route IPv6, TCP waits ~60s for timeout before falling back. Added IPv4-only `getaddrinfo` monkey-patch at top of `sync_folder.py`. 30× speedup.
- **Drive backup populated** via sync_folder.py: 155 files, ~98MB at `My Drive/DuberyMNL/backup/`. Contents: `references/supplier-images/` (69 files, 11MB), `contents/new/` (43, 32MB), `contents/ready/` (43, 55MB).
- Accidentally synced `contents/failed/` (58MB rejected trash). RA caught it. Built `tools/drive/delete_folder.py` to clean up. Removed 98 files + 1 folder from Drive cleanly.
- Updated `.gitignore`: dropped stale `output/images/`, added `contents/{new,ready,failed}/`, `contents/assets/hero/`, `archives/`, `references/supplier-images/`.
- Updated `README.md` with fresh directory structure + Setup/bootstrap section.
- **Edited `~/.claude/commands/closeout.md`**: Step 5 now runs Drive content sync for `contents/new/` + `contents/ready/` in the parallel background batch. This closeout is the first run.

### Decisions
- Content storage is **3 tiers**, not 2: git for code + runtime-deps, Drive for valuable content (new/, ready/, supplier-refs), local-only for trash (`contents/failed/`) + redundant (`archives/` -- git history has the originals)
- IPv4 monkey-patch is canonical for all future Python tools hitting Google APIs on RA's Windows machine. Include at top of module before HTTP imports
- `/savepoint` stays memory-only (fast checkpoint), `/closeout` handles full git + Drive + secrets batch
- Archives/ stays local-only -- optional `rm -rf archives/` after push to reclaim 87MB disk
- "Session 99" naming in memory files kept as conversational shorthand (actual session number is 102). No retroactive rename.

### Deployed
- `fc3bddf` pushed to GitHub (via this closeout)
- `log: session 102 ...` follow-up commit pushed
- Drive backup populated at `My Drive/DuberyMNL/backup/{contents/new, contents/ready, references/supplier-images}`

### Blockers
- `brand-callout` + `brand-collection` WF2 fidelity port parked (needs QA testing bandwidth)
- `cloud-run/*` has 4 modified + 2 deleted files belonging to RA's other IDE session -- left untouched per multi-session safety rule
- `.claude/settings.local.json` unstaged (shared between active sessions)
- Drive at 8.5GB / 15GB (56%) -- watch growth
- `.git/` at 325MB on DuberyMNL -- worth auditing for old large blobs in a future session
- Subagent conversion for /closeout, /savepoint, /loadout to Sonnet (save cost) -- next session

---

## Session 101 -- 2026-04-11 (chatbot-refactor-local-hosting)

### What
- Diagnosed 4 live production bugs in session 98 chatbot code via customer screenshots: Tagalog "Pasensya" fallback silencing conversations, 15+ message flood on single customer question (Jonathan case), triple-fire "Sorry, I can only help..." injection defense on legit questions (Teddy case), "Hm" failing JSON parse and triggering fallback
- Root-caused each bug via 2 parallel Explore agents diffing session 97 → 98 commits; found `_fallback_response()` returns Tagalog + `should_handoff=True`, `reply_parts` array has no cap, `security.py` has 33 over-aggressive injection keywords, `warm_attachment_cache()` tries all 48 images at startup causing OOM
- **Rewrote `cloud-run/conversation_engine.py`**: English-only fallback with no auto-handoff, removed `reply_parts` schema (single message per turn), stricter image rules ("you cannot see the image, describe the product"), new FIRST MESSAGE BEHAVIOR section (greet warmly + use name + thank + answer), list formatting rules (newlines + numbered/bulleted, no inline `(1)(2)`), Filipino shorthand recognition ("Hm" = "how much"), customer_name kwarg injected into dynamic system prompt per call
- **Rewrote `cloud-run/messenger_webhook.py`**: removed `reply_parts` loop, removed `_human_delay` typing delay, removed `warm_attachment_cache()` startup call, deleted `/comment-webhook` routes, added `/chat-test` GET (Messenger-style web UI) + POST (process-without-Meta) + `/chat-test/reset`, added `get_customer_first_name()` Meta profile lookup, added customer name input field with localStorage persistence in /chat-test UI, added image_key to meta display line
- **Shrank `cloud-run/knowledge_base.py` image bank**: 48 → 21 images (11 hero + 8 lifestyle + 2 support). **This was over-correction** — real customer needs (feedback/proof/on-face shots) were lost. Expansion with per-image captions is parked for next session.
- **Relaxed `cloud-run/security.py`**: INJECTION_KEYWORDS 33 → 17 high-confidence only. LEAK_PATTERNS trimmed to structural JSON field names only (removed prose patterns that false-fired on legit "PROVINCIAL ORDERS:" replies)
- **Deleted `cloud-run/comment_responder.py` + `cloud-run/comment_templates.py`** — daemon-thread pattern was known broken on Cloud Run (session 97) and caused Jonathan flooding when triggered
- **Critical fix: IPv6 latency bug.** Python HTTP calls to `aiplatform.googleapis.com` were ~60s each (curl = 1.4s) because `socket.getaddrinfo` returned IPv6 first, home ISP couldn't route IPv6, TCP waited ~60s before IPv4 fallback. Fixed with an `socket.getaddrinfo` monkey-patch at top of `conversation_engine.py` (IPv4 filter). **60× speedup** — 5.00s avg regression test latency after fix vs. 61s before.
- Ran 10-test regression battery in `.tmp/chatbot_regression_test.py` — 10/10 passing covering first-contact greeting (with + without name), Hm shorthand, list formatting, image_key strict matching, injection defense, out-of-scope handling, Bandits vs Outback comparison
- **Infrastructure pivot:** Deleted Cloud Run `duberymnl-chatbot` service entirely (stopped ~$50/mo credit burn, clean slate). Installed `cloudflared.exe` directly from GitHub releases to `~/bin/cloudflared.exe` (winget install was stuck). Started Cloudflare Quick Tunnel → `https://compute-believe-distributors-rocky.trycloudflare.com`. Local Flask on `localhost:8080` is now publicly reachable via the tunnel.
- **Oracle Cloud signup rejected** ("error processing transaction", common for PH individual signups). Retry option parked. Hetzner CX11 (€3.29/mo) identified as backup option if Oracle keeps rejecting.
- **Commands rework:** Created new `/savepoint` command (mid-session save point — always writes memory + bidirectional cross-links + appends to in-progress PROJECT_LOG block). Renamed `/log` → `/closeout` (avoids `/login` tab-completion collision). Added bidirectional cross-linking rule + IN PROGRESS block consolidation logic to `/closeout`.
- Created plan file at `~/.claude/plans/melodic-whistling-book.md` (comprehensive chatbot recovery plan)
- **Meta boosted ads: PAUSED** on RA's side during the chatbot outage window

### Decisions
- **Delete Cloud Run service entirely** instead of scale-to-zero (max-instances=0 not allowed by Cloud Run). Reversible via `bash cloud-run/deploy.sh`. Cleanest complete shutdown.
- **Pivot to local hosting via Cloudflare Tunnel**. Free forever, fastest path after Oracle rejection. Home PC already runs 24/7 for Rasclaw + VSCode tunnel, so the uptime baseline is acceptable for a pre-revenue business (~15 msgs/day).
- **Keep agentic (Gemini) brain, not n8n/Make**. Agentic is the right tool for Taglish conversation + recommendations. The problem was infrastructure + code bugs, not the approach.
- **Session 98 introduced all 6 bugs in one commit (d942c44)**. Bugs were not caused by session 99's CPU throttle test or session 101's refactor-in-progress. Corrected earlier misattribution.
- **Strict "2 per model" image bank was over-correction** — RA flagged real customer needs for proofs/on-face/lifestyle shots during /chat-test testing. Expansion to ~35-40 with per-image captions is parked as the highest-priority next-session task.
- **First-message greeting is a behavior rule, not a hardcoded reply**. System prompt instructs Gemini to greet warmly + use name + thank for interest + THEN answer, all in one natural message. Dynamic context per call tells Gemini whether it's first contact and whether a name is known.
- **Filipino "hm" = "how much"**. PH customer shorthand that Gemini doesn't know natively — must be in the prompt. Saved as `reference_ph_customer_shorthand.md`.
- **"You cannot see the image" prompt rule**. Gemini was hallucinating scene descriptions ("here's Bandits on someone at a cafe") because it only knows image KEY names, not contents. Fixed by explicit rule to describe the PRODUCT (frame color, lens color, material) only.
- **Valor Global internal pitch strategy**: use DuberyMNL as proof-of-concept, ladder up from free Informdata KB chatbot demo → onboarding automation → Valor/client FB chatbots → HR automation → potential internal AI role. Low-risk internal career pivot attempt.

### Deployed
- **Cloud Run `duberymnl-chatbot` DELETED** (state change, not a deploy)
- **Local Flask + Cloudflare Tunnel LIVE** on home PC: `https://compute-believe-distributors-rocky.trycloudflare.com` → `localhost:8080`
- **Nothing pushed to remote prod** — refactored code is committed only to working copy so far (closeout commit pending)
- Meta webhook still points at deleted Cloud Run URL (returns 404) — intentional, will wire to tunnel URL after image bank expansion
- Boosted ads paused on RA's side

### Blockers
- **Image bank expansion** is the top next-session task. Bring back feedback/proof/on-face/lifestyle shots with short captions per image so Gemini knows what each one depicts. Target ~35-40 images. Without this, do NOT wire Meta webhook back to tunnel — real customers need proof/lifestyle shots we currently don't have.
- Meta webhook still points at deleted Cloud Run URL, returning 404 for any incoming message. OK for now because ads are paused.
- Cloudflare Worker fallback (for PC-offline resilience) not deployed. Needs a free Cloudflare account + Wrangler CLI.
- Auto-start of Flask + cloudflared on PC logon not wired (like Rasclaw's `start-rasclaw.bat` pattern).
- uptimerobot.com monitoring not set up.
- CRM Google Sheet has ~30 `TEST_BATTERY_*` and `TEST_SMOKE_*` rows from testing — needs cleanup script.
- Oracle Cloud signup rejected — decide tomorrow whether to retry, pivot to Hetzner €3.29/mo, or stay local indefinitely.
- Memory files saved this session reference "Session 99" in body text (pre-closeout naming). Low-priority cleanup for /lint-memory later.

---

## Session 100 -- 2026-04-11 (rasclaw-mobile-permissions)

### What
- Expanded `~/.claude/settings.json` allow list for mobile Telegram workflow: `Read(**/channels/telegram/inbox/**)`, `Bash(cp *)`, `WebFetch`, `Bash(gh *)`, `Bash(curl *)`, `Read/Write/Edit(**/Rasclaw/**)`, `mcp__plugin_telegram_telegram__reply` + `__react`
- Added `C:\Users\RAS\projects\Rasclaw` to `additionalDirectories` so Write/Edit tools can reach the Rasclaw inbox
- Diagnosed permission matching quirks through two screenshot iterations with RA on Telegram: scoped `cp "..."` pattern never matched because Claude Code strips quotes before matching
- Confirmed path format: Claude's internal Windows path form is `C:/Users/RAS/...` forward-slash, not git-bash `//c/Users/...`

### Decisions
- Scope mobile auto-approve to Rasclaw only (not all projects) -- RA explicit constraint, enforced by Write/Edit path globs
- Broad `Bash(cp *)` over scoped quoted pattern -- quote normalization kills scoped forms
- Voice ffmpeg not pre-approved -- images only per RA, defer until voice workflow breaks
- Trust existing deny list (rm -rf, force push, .env) as sandbox floor instead of stacking more deny rules

### Deployed
- Nothing deployed (config only)

### Blockers
- Telegram claude session still runs with old perms until manual restart via `~/.claude/scripts/start-rasclaw.bat` -- RA accepted staleness for now
- Voice ffmpeg transcode still prompts per-file if voice workflow comes up

---

## Session 98 -- 2026-04-10 (chatbot-kb-rebuild)

### What
- Added Rasclaw to main.code-workspace
- Rebuilt chatbot knowledge base from draft to production: accurate product descriptions (Bandits slim square, Outback blocky angular, Rasta oversized aviator), specs (TR90/PC frames, dimensions, weight), provincial-prepaid delivery flow, corrected inclusions (drawstring pouch not hard case), DUBERY50 on-mention-only, new tagline "Premium polarized shades at everyday prices", order flow with landmarks + delivery preference + urgent handling, warm+direct persona (not jolly)
- Scraped Dubery supplier site (duberysunglasses.com): 80+ product images + specs for Bandits x5 + Outback x4 + Rasta (D008), saved to references/supplier-images/
- Built chatbot image bank: 48 images in 8 categories (hero/model/lifestyle/collections/brand/feedback/proof/sales-support) uploaded to Google Drive, wired via lh3 CDN URLs + manifest
- Chatbot deployed 10+ times with incremental fixes: English-first rule tightened with Tagalog sentence ban, multi-part messages via reply_parts array, typing_off fix, time import bug fix, Meta attachment_id caching for fast image sends, startup warmup pre-uploading all 48 images, natural typing delay (1.5-4.5s based on reply length)
- Prompt injection defense (3 layers): input scanning for 40+ keywords, SECURITY RULES at top of system prompt, output leak scanning. Flagged senders silenced, no email to RA
- Created DuberyMNL CRM Google Sheet with 4 tabs (Leads, Orders, Lead Score Log, Conversations), shared with Cloud Run service account
- CRM sync wired into chatbot: Gemini extracts customer data per turn, webhook upserts Lead rows with Hot/Warm/Cold/Converted scoring, creates Order rows on completion
- Conversation history persistence: every message synced to Conversations tab, cold-start recovery loads last 20 messages from sheet for returning customers
- Chatbot went LIVE and handled real customer conversations (visible in /conversations dashboard)

### Decisions
- KNOWLEDGE_BASE.md as editable source of truth, sync to cloud-run/knowledge_base.py
- Image bank split: Vercel for hero shots (proven), Drive lh3 CDN for 7 other categories
- Startup warmup all 48 images (+30-60s boot time, eliminates first-send loading circle)
- Multi-part messages via reply_parts array (not \n line breaks) for cleaner Messenger UX
- Natural typing delay: 1.2s base + 25ms/char, capped 4.5s, with typing indicator between parts
- Handoff behavior: flag conversation + bot stops responding + no email (RA explicit feedback)
- DUBERY50 only mentioned when customer brings it up first
- Provincial orders = prepaid only (GCash/InstaPay) because no business docs for Shopee/J&T COD
- CRM v1 in Google Sheets, Supabase later for portfolio value
- Conversation history persisted to sheet for cold-start recovery across Cloud Run restarts

### Deployed
- Cloud Run chatbot (duberymnl-chatbot): 10+ revisions deployed today, currently live with knowledge base rebuild + image bank + prompt injection defense + CRM sync + conversation persistence
- DuberyMNL CRM Google Sheet created (ID: 1wVn9WGdY8pK7c68pZpnNSWoNkhhZvYUywcGqLCqcewA)
- 48 images uploaded to Google Drive (folder: 1TnnaSmd_IzRbus3mCwYw--FO0k4pOByZ)

### Blockers
- Debounce (5s wait + message combining) -- not built
- Flood protection + bot detection (v2 heuristics) -- not built
- Re-engagement script (20-hour follow-up) -- not built
- Facebook page tagline needs manual update (API blocked by pages_manage_metadata permission)
- Website updates pending: align tagline, add discount code field, add provincial/GCash info
- Old 3 conversations lost on pre-CRM redeploy
- Shopee/J&T couriers discussion parked for later

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

---

## Session 83 -- 2026-04-06 (make-engagement-pipeline)

### What
- Built "AI Client Engagement Pipeline" Make.com scenario (ID: 5146141) -- 2nd of 2 free plan slots
- 9-module flow: Webhook -> AI Brief -> Google Sheets CRM -> Router (3 paths) -> AI Proposals + Gmail
- 3 conditional paths: Consulting (AI proposal), Automation (AI proposal), Fallback (templated email)
- Created "Client Engagement CRM" Google Sheet (ID: 1cwOlCpms8rMo99sNSsNIeRh9760UEaZxLFALfJ0HSIU)
- Fixed router fallback filter -- Make fires all matching paths, needed explicit exclusion
- Refined AI prompts to paraphrase client messages instead of verbatim copy
- Tested all 3 paths with 11 test leads -- routing correct, emails personalized
- Scenario activated on "Immediately as data arrives" schedule

### Decisions
- Webhook trigger (not Forms) to show different pattern from Lead Router for portfolio range
- Make routers fire ALL matching paths -- fallback needs explicit "does not contain" filters
- AI prompts must explicitly say "DO NOT copy verbatim" or it parrots input

### Deployed
- Make.com scenario live and activated (webhook-triggered)

### Blockers
- Export blueprint from Make UI to automation-workflows/make/blueprints/
- Build HTML simulator for portfolio demo
- Connect Lead Router to Engagement Pipeline (HTTP module on Hot path)
- Move to Zapier learning track

## Session 84 -- 2026-04-07 (kb-chatbot-fix)

### What
- Rebuilt Knowledgebase-informdata chatbot from scratch using DuberyMNL chatbot pattern
- Created knowledge_base.py (keyword-indexed SSG + MidAtlantic state loader, 21 files)
- Created conversation_engine.py (Claude wrapper, stdin piping bypasses Windows 32K limit)
- Created conversation_store.py (server-side history, prevents client contamination)
- Rewired app.py and index.html to use new modular architecture
- Fixed browser vs curl bug (root cause: cmd-line limit + CLAUDE.md persona override)
- Keyword indexing cuts 178K → 20-25K per query (70% reduction)
- Greeting bypass (zero tokens for "hi/hello")
- Switched to Haiku model (faster, lighter on 5-hour budget)
- Image/screenshot support with --tools Read
- Fixed UTF-8 encoding for subprocess output on Windows
- Added 9 MidAtlantic state files to keyword index

### Decisions
- Pipe full prompt via stdin (not cmd args) to bypass Windows 32K limit AND make context dominate over CLAUDE.md
- Don't fight CLAUDE.md -- flood context with domain knowledge instead
- Keyword-index knowledge files, load only relevant ones per query
- Haiku over Sonnet for KB chatbot (fast enough, conserves 5-hour usage budget)
- No web search tool (encyclopedia is source of truth, web results could contradict)

### Deployed
- KB chatbot live on ngrok (sheathier-endoblastic-graham.ngrok-free.dev)

### Blockers
- Pre-generate FAQ cache to reduce token usage for common questions
- Add remaining state files beyond MidAtlantic (Phase 2)
- Fixed server for teammates (Oracle VM + setup-token, or Anthropic API key)
- Tighten fallback (currently loads all 21 files / 112K when no keywords match)

## Session 85 -- 2026-04-07 (ultraplan-prompt)

### What
- Researched ultraplan (new Claude Code cloud-based planning feature)
- Confirmed DuberyMNL repo is public and secrets are gitignored
- Read all 11 DuberyMNL skills to understand the full pipeline architecture
- Crafted comprehensive ultraplan prompt for UGC content pipeline using /prompt-master
- Prompt covers 6 systems: UGC captions, caption-to-image derivation, product fidelity gatekeeper, posting automation, comment auto-responder + auto-DM, Messenger chatbot
- Saved plan to .claude/plans/ugc-pipeline-ultraplan.md

### Decisions
- Use dubery-prompt-parser (not validator) in UGC flow -- validator checks overlays/pricing that UGC doesn't have
- Build NEW UGC product fidelity gatekeeper with zero-tolerance (PASS/REJECT only, no PATCH)
- Comment auto-responder + auto-DM as separate system from chatbot (auto-responder triggers, chatbot takes over)

### Deployed
- Nothing deployed

### Blockers
- Paste ultraplan prompt into Claude Code on the web to generate the plan
- Buy kie.ai credits when ready for Phase B (image generation)
- Test image gen prompts in Gemini web app first (free)

## Session 86 -- 2026-04-06/07 (ugc-pipeline-build)

### What
- Executed the ultraplan prompt from Session 85 via Claude Code on the web (remote cloud session)
- Built full 6-phase UGC content pipeline end-to-end:
  - Phase 1: UGC caption generator skill (dubery-ugc-caption-gen) -- organic lifestyle captions, no pricing/CTAs, Taglish-friendly, theme/mood/scenario_hint drives image prompt
  - Phase 2: UGC product fidelity gatekeeper skill (dubery-ugc-fidelity-gatekeeper) -- 8-check binary PASS/REJECT, no patching, catches frame/lens descriptions, banned appearance words, scene lighting interference
  - Phase 3: UGC pipeline orchestrator skill (dubery-ugc-pipeline) -- one-shot caption -> prompt -> validate flow with optional Gemini paste-test output
  - Phase 4: Extended Facebook posting tools (schedule_post.py + schedule_batch.py) with --ugc flag to read from ugc_pipeline.json
  - Phase 5: Comment auto-responder + auto-DM (comment_responder.py + comment_templates.py) -- like + reply + DM funnel with 24h dedup, spam filter, auto-DM context for chatbot
  - Phase 6: Messenger chatbot wiring -- DUBERY50 discount code, auto-DM context awareness, combined server (/webhook + /comment-webhook on port 5002)
- Updated dubery-ugc-prompt-writer skill with caption-driven mode (caption_text + mood fields)
- Added --status command and fidelity gatekeeper integration to run_ugc.py
- Set UGC posting cadence: daily at 9AM / 12PM / 6PM PHT (2-3x/day)
- Rebalanced comment reply templates from heavy Tagalog to English-forward
- 12 files changed: 3 new skills, 2 new tools, 7 modified files

### Decisions
- UGC captions must NEVER contain pricing, CTAs, promo codes, or delivery mentions
- Fidelity gatekeeper is binary PASS/REJECT -- no PATCH option (if fidelity is at risk, full rewrite)
- Combined server (Option A) -- chatbot + comment responder on single Flask app, single port
- DUBERY50 set as P50 off single pair (confirmed by RA)
- UGC posting cadence: 2-3x/day (confirmed by RA), ad creatives keep existing Tue/Thu/Sat/Sun schedule
- Comment replies English-forward (confirmed by RA -- original Tagalog-heavy versions rejected)
- Caption drives image: scenario_hint + mood from caption determine the visual scene in prompt writer

### Deployed
- Branch pushed to GitHub: claude/plan-dubery-ugc-pipeline-QofJO (3 commits)
- All changes on remote cloud, need git pull to local Windows PC

### Blockers
- Pull branch to local PC and merge to main
- Test /dubery-ugc-pipeline skill end-to-end (generate captions + prompts)
- Subscribe page to feed webhook (one-time Meta setup for comment auto-responder)
- Buy kie.ai credits for Phase B image generation
- Test prompts in Gemini web app first (free validation)

## Session 87 -- 2026-04-07 (vertex-image-gen)

### What
- Set up Google Cloud project (371181189379, "dubery") with $300 free credits (88 days remaining)
- Enabled Vertex AI API + Generative Language API, created service-account-bound API key
- Added GOOGLE_API_KEY to .env, installed google-genai SDK v1.70.0
- Discovered `vertexai=True` + `api_key` works without gcloud CLI (no project/location needed)
- Tested Gemini 3.1 Flash (`gemini-3.1-flash-image-preview`) for image generation
- Key findings: `inline_data.data` is raw bytes (not base64), use `mime_type` to pick extension
- Ran full UGC pipeline end-to-end twice (caption -> prompt writer -> fidelity gatekeeper -> Vertex gen -> review)
- Tested plain text prompts vs JSON -- identical quality, JSON adds zero value for Gemini
- Tested multi-angle product references (4 angles) vs single -- multi-angle improves temple/detail fidelity
- RA uploaded 4-angle reference photos for all 5 Bandits variants to `C:\Users\RAS\Documents\PRODUCT REF\`
- Generated all 11 product variants as product-anchored UGC in one batch (~$0.75 total)
- Cost per image: ~$0.067 (1K) to ~$0.151 (4K). Budget supports 2,000-4,000 images.

### Decisions
- Gemini 3.1 Flash via Vertex AI replaces kie.ai for image generation (free $300 credits vs paid kie.ai)
- Plain text prompts replace JSON format -- simpler, no redundancy, same quality
- Multi-angle reference images (4 angles per product) improve product fidelity
- CAR_SELFIE and motorcycle scenarios removed from UGC pipeline (spatial errors confirmed)

### Deployed
- Nothing deployed (testing/validation session)

### Blockers
- Build `generate_vertex.py` as formal replacement for `generate_kie.py`
- Rebuild UGC pipeline skills around plain text prompts (drop JSON format)
- Bandits Matte Black lens fidelity issue (generates mirror/orange instead of dark lenses)
- Shoot multi-angle refs for Outback and Rasta series
- Update NB2 skill and pipeline tools to reflect Gemini 3.1 Flash as engine

## Session 88 -- 2026-04-08 (brand-content-pipeline)

### What
- Built `generate_vertex.py` -- Gemini 3.1 Flash image generation tool with auto prompt tracking
- Updated UGC prompt writer: naturalism-first replaces fidelity-first, R4 physical realism, product finish table
- Built `/dubery-brand-content` skill with 6 scenario types + research-backed rules
- Built `/dubery-brand-callout` -- 5 tested layout variants (RADIAL, SPLIT, EXPLODED, NUMBERED, TOP_BOTTOM)
- Built `/dubery-brand-bold` -- 4 tested layout variants (TYPE_COLLAGE, TEXTURE, SPLIT_TEXT, KNOCKOUT)
- Built `/dubery-brand-collection` -- 5 tested layout variants (FLAT_LAY, HERO_CAST, DIAGONAL, FAN_SPREAD, UNBOX_FLATLAY). GRID dropped.
- Tested 20+ image generations across all scenarios, iterated V1->V2->V3 based on RA feedback
- Researched brand content design: feature callouts, bold statements, collections, comparisons, flat lay techniques
- Added brand assets: 3 logo variants, font alphabet (4 sheets), packaging reference, infographic reference
- Added frontmatter to all 15 project skills
- Cleaned repo: moved excalidraw images to automation-workflows, deleted .playwright-mcp
- Downloaded phone uploads from GDrive (competitive intel for portfolio, family photos)

### Decisions
- Naturalism-first prompting replaces fidelity-first for all image generation
- Material finish (glossy/matte) stated explicitly in all prompts
- Real environments mandatory -- no plain solid backgrounds (products look CG without real surfaces)
- Single angle reference per product (multi-angle causes ghost pairs)
- Brand content split into individual skills per scenario type
- Grid layout dropped from COLLECTION (looked pasted/sterile)
- EDUCATIONAL and COMPARISON parked as article companions, not standalone posts
- Overloaded prompts cause Gemini 500 errors -- describe what, not how
- Carousel: wide 2:1/3:1 then slice, product-anchor only, person-anchor stays single frame
- No test card in unboxing flatlay
- Veo 2 video gen blocked on gcloud CLI install (needs home browser OAuth)

### Deployed
- 6 commits pushed to GitHub across session

### Blockers
- LIFESTYLE_CARD needs testing and own skill
- Orchestrator (/dubery-brand-content) needs update to route to sub-skills
- Apply research learnings to UGC + ad creative skills
- Install gcloud CLI from home for Veo 2
- Find Outback + Rasta multi-angle product reference photos

## Session 89 -- 2026-04-08 (engagement-pipeline-sim)

### What
- Built `engagement-pipeline-simulator.html` -- dark-themed interactive portfolio demo for AI Client Engagement Pipeline (Make.com scenario 2)
- 10 Filipino business inquiries animated through 5 stages: Webhook -> AI Brief -> CRM -> Keyword Router -> Email
- 3 routing paths visualized: Consulting (orange), Automation (blue), Fallback (gray)
- Keyword highlighting in router stage shows exact decision logic
- AI proposal generation sub-phase for consulting/automation paths
- Design inspired by dark-theme automation showcase post (GDrive reference)
- Hosted via ngrok for browser testing, iterated on animation timing (slowed ~2x after RA feedback)

### Decisions
- Dark theme for portfolio demos (diverges from lead-router's light cream) -- matches RA's preferred aesthetic
- Color coding: Consulting=#f5a623 orange, Automation=#3b9eff blue, Fallback=#888 gray

### Deployed
- Nothing deployed (local HTML demo)

### Blockers
- Iterate further on simulator polish (timing, visual tweaks)
- Export Make.com blueprints to automation-workflows/make/blueprints/
- Consider updating lead-router simulator to match dark theme
- Connect the two simulators for unified portfolio demo

## Session 90 -- 2026-04-08 (vertex-auth-veo)

### What
- Switched Vertex AI auth from API key to ADC (Application Default Credentials)
- Fixed Gemini 3.1 location from us-central1 to global
- Added Veo 3.1 video generation tool (generate_vertex_video.py)
- Tested video-to-website skill

### Decisions
- ADC auth over API key (auto-refreshes, no key management)
- Gemini 3.x requires location='global'
- Veo 3.1 Fast as default video gen model, Veo 2.0 rejected (no audio)

### Deployed
- Nothing deployed

### Blockers
- None

## Session 91 -- 2026-04-08 (virtudesk-application)

### What
- Spotted Virtudesk "AI & Automations VA" job posting -- near-perfect skill match
- Built interactive image picker gallery for portfolio image selection (16 images chosen)
- Upgraded portfolio: AI brand content, product photography, Make.com screenshots, Tools & Systems section, updated ads grid, tech stack
- Updated Command Center screenshot -- Creative tab with real product images and generated image in review stream
- Compressed images PNG->JPG (20MB -> 2.5MB)
- Deployed portfolio to GitHub Pages after Vercel outage (rasclaw.github.io/ras-portfolio/)
- Made ras-portfolio repo public
- Drafted cover letter mirroring Virtudesk JD with STAR examples, iterated 4+ times
- Built ATS-friendly 1-page resume (HTML->PDF via Selenium)
- Created Gmail draft with cover letter + portfolio URL

### Decisions
- Portfolio URL: GitHub Pages (rasclaw.github.io/ras-portfolio/) due to Vercel outage
- ras-portfolio repo made public (no secrets)
- Hero: "AI Automation Architect" -> "AI & Automation Specialist"
- Cover letter structured to mirror each JD bullet point directly
- Automation experience framed as journey (n8n -> Make -> agentic) with willingness to maintain traditional tools

### Deployed
- Portfolio to GitHub Pages (rasclaw.github.io/ras-portfolio/)
- Code pushed to GitHub (RASCLAW/ras-portfolio)

### Blockers
- Attach resume PDF to Gmail draft and send
- Vercel still down -- migrate fully to GitHub Pages or retry later
- Add phone number to cover letter before sending
- Build career-ops pipeline for future applications (santifer/career-ops reference)

## Session 92 -- 2026-04-09 (product-catalog)

### What
- Built product catalog page at duberymnl.com/products/ (dark theme, mobile-first, 11 products with gallery detail)
- Compressed all product images (cards 14MB->182KB, gallery 22MB->5MB)
- Added deep link ordering (?variant=INDEX&order=1) -- catalog links to order form with product pre-selected
- Added "Browse All Styles" button to main landing page
- Linked "RAS AI Solutions" footer to GitHub Pages portfolio
- Fixed VSCode tunnel -- reinstalled as Windows service (auto-starts, auto-restarts)
- Deployed to duberymnl.com
- First customer conversation (Nina -- Outback Red, GCash + delivery)
- Sent catalog link via Telegram

### Decisions
- Product catalog as separate /products/ page (shareable link for Messenger)
- VSCode tunnel as Windows service (survives crashes + reboots)

### Deployed
- duberymnl.com (landing page + product catalog)

### Blockers
- Nina follow-up -- waiting for product pick
- Full landing page UI revamp (separate session)

## Session 93 -- 2026-04-09 (file-organization)

### What
- Confirmed VSCode tunnel running as Windows service (auto-start on login, healthy pings)
- Confirmed power settings: lid close = do nothing, sleep on AC = never
- Built /remote-access-status skill + remote-status.sh script (tunnel + power check)
- Added to loadout routine, auto-approved in settings.local.json
- Reorganized DuberyMNL file system:
  - Moved DuberyMNL content from .tmp/ to review/
  - Built HTML review gallery (filter tabs, lightbox, click-to-select, clipboard export)
  - RA reviewed 109 images via ngrok -- sorted to passed/ (76) and failed/ (40)
  - Downloaded all 36 WF2 pipeline images from Google Drive with captions + prompts
  - Organized passed/ into 5 categories: ads (36), brand (20), product (9), ugc (7), carousel (4)
  - Moved rasta-scroll-test/ from .tmp/ to project root
- Created review/update_gallery.py for regenerating gallery data

### Decisions
- .tmp/ is for truly temporary files only -- DuberyMNL content lives in review/
- Passed images organized by use case (ads/brand/product/ugc/carousel), not pipeline source
- Remote access status check added to session loadout
- Gallery export copies to clipboard instead of downloading txt file

### Deployed
- Nothing deployed

### Continued
- Renamed review/ to contents/
- Flattened structure: ads/brand/product/ugc/carousel moved from passed/ to contents/ root
- Added contents/new/ as staging folder for fresh image generations
- Deleted ad-refs/ (quality benchmarks, not content), moved phone-uploads/ to EA-brain
- Cleaned 12 empty subfolders
- Recovered YouTube API key from GCP via gcloud CLI, saved to .env
- Fetched + saved transcript: "Claude Managed Agents Just Dropped" (Nick Saraev) to EA-brain/references/
- Added backlog: fix image gen skills to save to contents/new/, clean output/, study managed agents

### Decisions (continued)
- contents/new/ replaces passed/ as staging -- categories are direct children of contents/
- Image gen skills must update output path before next generation run

### Deployed
- Nothing deployed

### Blockers
- Update image gen skills to save to contents/new/ instead of .tmp/ (before next gen run)
- output/ has 39 duplicate files -- clean up later
- Old /vscode-tunnel skill folder not deleted (permission denied)
- 18 orphan prompt JSONs in .tmp/

## Session 94 -- 2026-04-09 (claude-code-mastery)

### What
- Studied Claude Code Workflow Cheatsheet -- identified hooks (L3) as gap in 4-layer setup
- Researched Karpathy's LLM Wiki video via YouTube API + gist
- Built /youtube skill (metadata + transcripts via Data API v3, replaces WebSearch for YT URLs)
- Built /ingest skill (formal source ingestion: raw archive + summary + cross-updates + log)
- Built /lint-memory skill (periodic audit: staleness, contradictions, orphans, cross-ref gaps)
- Established cross-referencing convention (related: field in memory frontmatter)
- Ran first /lint-memory audit: 62 files, 3 orphans, 5 possibly stale, 0/62 cross-refs
- First formal ingest: Karpathy LLM Wiki video (transcript + summary in EA-brain/references/)
- Updated EA-brain/CLAUDE.md with Knowledge System section
- Created references/summaries/ directory structure + INDEX.md + ingest-log.md
- Saved 6 memories, indexed 3 orphans in MEMORY.md

### Decisions
- LLM Wiki pattern adopted for EA-brain -- ingest/lint/cross-ref as three formal operations
- YouTube API preferred over WebSearch/WebFetch for all YouTube URLs
- Lint fixes saved to backlog, not fixed this session

### Deployed
- Nothing deployed

### Blockers
- Hooks (L3) setup deferred
- Lint fixes pending: retype project_meta_verified -> reference, archive make milestone memories
- Retroactively ingest managed-agents transcript (raw exists, needs summary)

---

## Session 95 -- 2026-04-09 (organic-posting)

### What
- Built image review dashboard at `contents/ready/index.html` (approve/reject/preview, localStorage state)
- Reorganized `ready/` into `contents/ready/` with subfolders (brand, product, ugc, model-shots, brand-bold)
- Researched Facebook posting API (posts, stories, reels, scheduling, rate limits) and cross-platform options (IG, X, TikTok, Buffer, n8n)
- Generated 27 captions in `contents/ready/captions.json` (no-price, Messenger-first, engagement CTAs)
- Replaced 11 product card images on landing page -- white bg unboxing shots replaced with styled hero images
- Deployed card image update to duberymnl.com (Vercel)
- Built `tools/facebook/post_story.py` -- photo story posting via Graph API v25.0
- Posted first live story (MODEL-BANDITS-GREEN) to DuberyMNL Facebook Page
- Built `tools/facebook/story_rotation.py` -- time-based rotation through 12 images, no state file needed
- Set up GitHub Actions cron (`story-rotation.yml`) -- 1 story every 4 hours (6/day, 8AM/12PM/4PM/8PM/12AM/4AM PHT)
- Added META_PAGE_ACCESS_TOKEN + META_PAGE_ID to GitHub Secrets
- First automated run confirmed working

### Decisions
- Facebook-first for organic posting (API built, Meta verified, zero friction)
- Stories API has no scheduling -- GitHub Actions cron for timed rotation
- Time-based index `(hours / 4) % 12` for rotation (stateless, deterministic)
- Platform expansion: FB (done) -> Instagram (App Review) -> X ($0.01/post) -> TikTok (audit)
- Hero images replace white bg card shots on landing page and products page

### Deployed
- Landing page card images updated on duberymnl.com (Vercel auto-deploy)
- Story rotation workflow live on GitHub Actions
- First live Facebook story posted

### Blockers
- Feed post scheduling (captions ready, need to wire up schedule_post.py)
- Convert card images from PNG-in-JPG to proper JPG (bandwidth)
- Upgrade schedule_post.py API version from v21.0 to v25.0
- Instagram: submit App Review for `instagram_content_publish`
- Update review dashboard to match new folder structure

## Session 96 -- 2026-04-10 (rasclaw-telegram)

### What
- Installed Bun runtime for Telegram channel plugin
- Configured and paired Rasclaw bot (@Rasclaw01_bot) as Claude Code Telegram channel
- Two-way text + photo messaging working from phone
- Auto-start via start-rasclaw.bat in Windows Startup folder
- Built Google STT transcribe.py (works but decided TG mic keyboard is better)
- Created ~/projects/Rasclaw/ project folder with CLAUDE.md, memory, organized structure
- Rasclaw launches from its own project folder with full context of all projects
- Git repo initialized

### Decisions
- TG mic-to-text keyboard over server-side voice transcription (zero latency, zero cost)
- Startup folder .bat over Task Scheduler (interactive CLI needs real terminal)
- Rasclaw gets its own project folder (organized, portfolio-worthy)
- Reactive DM chat for now, group topics for notifications later

### Deployed
- Rasclaw Telegram channel LIVE (DM @Rasclaw01_bot)
- Auto-start on Windows logon

### Blockers
- Test Rasclaw more from mobile
- DuberyMNL chatbot ready for testing (Cloud Run, cloud-run/ folder)
- Belle Telegram channel (same pattern, planned)
- HITL via Telegram (review from phone)
- Push Rasclaw repo to GitHub

## Session 97 -- 2026-04-10 (chatbot-cloudrun)

### What
- Deployed DuberyMNL Messenger chatbot + comment auto-responder to Cloud Run (18 revisions)
- Swapped conversation engine from `claude --print` to Vertex AI Gemini 2.5 Flash via REST API
- Built `cloud-run/` directory with 11 self-contained files (Dockerfile, deploy.sh, all Python modules)
- Configured Meta webhooks in App Dashboard (Messenger + feed, 8 subscription fields)
- Added image sending -- bot sends kraft product card photos when customer asks to see a product
- Added message dedup to skip Meta retries
- Fixed deadlock in conversation store (threading.Lock -> RLock)
- Granted roles/aiplatform.user to Cloud Run service account
- Enabled Cloud Run, Cloud Build, Artifact Registry APIs

### Decisions
- Gemini 2.5 Flash over 2.0 Flash (2.0 restricted to existing customers, sunset June 2026)
- REST API over google-genai SDK (SDK hangs on Cloud Run during client init)
- Synchronous inline processing over background threads (daemon threads die silently on Cloud Run)
- META_PAGE_ACCESS_TOKEN for Messenger Send API (ADS token returns 403 on /me/messages)
- RLock over Lock in conversation store (append_message calls get_or_create = deadlock)
- min-instances=1 for reliability (~$10-15/mo, covered by $300 credits)
- gunicorn --timeout 0 (Google official recommendation for Cloud Run)
- English-first chatbot tone (pending implementation)
- DUBERY50 discount should NOT be proactively offered by bot -- only via comment-to-DM funnel
- Discount code is website-only (drives traffic to duberymnl.com)

### Deployed
- Cloud Run: duberymnl-chatbot revision 20, asia-southeast1
- URL: https://duberymnl-chatbot-3y2d5wqigq-as.a.run.app
- Endpoints: /webhook (Messenger), /comment-webhook (feed), /status, /conversations, /test

### Blockers
- pages_messaging App Review needed before bot works for non-admin users
- Tone tuning (English-first, casual Filipino sprinkles only)
- Comment auto-responder untested
- Landing page HTML not yet using kraft card images
- Website chatbot widget (future -- same Gemini backend)
