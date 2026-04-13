# DuberyMNL Project Log

Previous sessions (1-72) archived in `archives/pre-ea-rebuild/PROJECT_LOG.md`.
Sessions 73-97 archived in `archives/PROJECT_LOG-sessions-73-97.md`.

---

## Session 118 -- 2026-04-13 (v3-pipeline-batch)

### What
- Ran v3 fidelity-spec pipeline 6x on Outback Blue: 5 PASS, 1 FAIL
  - PASS: UGC_PERSON_WEARING (rooftop golden hour), UGC_PRODUCT (poolside morning), UGC_PERSON_HOLDING (boardwalk sunset), UGC_PERSON_WEARING (bikini beach), BRAND_MODEL (Siargao editorial)
  - FAIL: UGC_PERSON_WEARING (basketball court blue hour) -- product fidelity lost in cool lighting
- Removed inner temple arm zebra detail from outback-blue product spec (Gemini hallucinated wood-tone arms)
- Added "Clean branding visible on the temple" to outback-blue spec (fixed missing emblem on holding shots)
- Hardcoded -1.png angle in v3 pipeline skill (stopped repetitive front-view results)
- Built `tools/image_gen/v3_randomizer.py` -- true RNG scene randomizer with variety banks: 24 locations, 14 lighting setups, gendered subject banks, 15 surfaces, camera presets per category
- Killed 3 orphan sessions (1434MB freed)

### Decisions
- Always use -1.png prodref for all products -- 3/4 view shows branding + more visual interest
- "Clean branding visible on the temple" as explicit required_detail -- Gemini doesn't reliably read it from ref alone
- Remove interior-only details from specs -- Gemini can't distinguish inside/outside temple arms
- Built dedicated v3_randomizer.py to replace biased manual scene picking

### Deployed
- Nothing deployed

### Blockers
- Basketball court blue hour shot failed -- retry or investigate cool-lighting fidelity
- Expand v3_randomizer variety banks if combos feel limited
- Test remaining categories: UGC_HEADBAND, BRAND_CALLOUT, BRAND_BOLD, BRAND_COLLECTION
- Validate other product specs beyond Outback Blue

---

## Session 117 -- 2026-04-13 (chatbot-recovery-live)

### What
- SSL cert confirmed live on chatbot.duberymnl.com -- blocker from session 111 cleared
- Added dotenv loading to Flask messenger_webhook.py (was missing for local runs, worked on Cloud Run via injected env vars)
- Fixed verify token fallback (empty .env value overrode default)
- Wired Meta webhook to chatbot.duberymnl.com/webhook (recovery step d)
- Auto-start on boot via Task Scheduler: DuberyMNL-Chatbot + DuberyMNL-Tunnel (step e)
- UptimeRobot confirmed already configured by RA (step f)
- Built smart message flood debounce (3s normal, 8s when image keywords like "this"/"ito"/"check" detected)
- Built customer image vision -- downloads customer-sent images, base64 encodes, sends to Gemini 2.5 Flash as inlineData
- Single image processing cap (1 at a time) with polite multi-image acknowledgment message
- Fixed security gate false positive -- bot detection triggered on augmented context text (brackets matched JSON regex)
- Fixed JSON leak in Gemini fallback parser -- regex extracts reply_text from malformed JSON instead of dumping raw
- Rewrote all 10 FAQ answers from spec-sheet format to conversational Filipino shop assistant tone
- Fixed CRM Sheets auth -- switched from ADC (google.auth.default) to token.json (same as pipeline tools)
- Built Cloudflare Worker fallback (dubery-chatbot-fallback) -- intercepts webhook when origin down, sends away message via Meta Send API
- Added startup attachment warmup -- background thread pre-uploads all 48 images to Meta CDN on boot (48/48, zero failures)
- Stress tested chatbot: 16/16 scenarios passed (greetings, pricing, shipping, injection, skeptic, comparison, order flow, follow-ups)
- Fallback Worker tested end-to-end: stopped Flask, sent Messenger message, received away reply

### Decisions
- Smart debounce (3s/8s) over fixed window -- keyword detection for common Filipino image-follow patterns ("this", "ito", "check")
- Security gates check original customer text, not augmented context -- prevents false positives from system-injected brackets/context
- Cloudflare Worker fallback over Facebook away message -- auto-detects origin down without manual toggle, handles webhook verification too
- Startup warmup in background thread -- server starts immediately, warmup runs parallel, URL fallback during ~60s window
- CRM uses token.json not ADC -- ADC from gcloud auth doesn't include Sheets write scope

### Deployed
- chatbot.duberymnl.com -- LIVE, receiving real Messenger messages
- dubery-chatbot-fallback Worker on Cloudflare -- LIVE on chatbot.duberymnl.com/*
- Meta webhook wired to new URL
- Task Scheduler tasks registered (DuberyMNL-Chatbot + DuberyMNL-Tunnel)

### Blockers
- (h) Unpause boosted ads -- RA manual action in Ads Manager
- (i) 1-week clean production data capture -- starts after (h)
- Chatbot image bank refresh (stale hero shots + add worn shot per variant) -- backlogged
- Landing page asset update -- backlogged
- Pricing decision P699/P1200 vs P599/P999 -- discussed, not decided

---

## Session 116 -- 2026-04-13 (superpowers-cherry-pick)

### What
- Restored YouTube OAuth -- re-ran `tools/reauth_token.py`, all 6 scopes granted (drive, sheets, gmail, calendar, youtube). YouTube now has full API access (liked videos, subscriptions, playlists)
- Fetched 392 liked videos via YouTube Data API to verify OAuth works
- Ingested "Unlock the Next Evolution of Claude Code with One Plugin" (Nate Herk) -- Superpowers plugin analysis
- Built custom Superpowers-inspired build flow (path B: cherry-pick, not install):
  - `/brainstorm` -- visual companion, localhost dashboard with clickable option cards + server.py
  - `/plan` -- hyper-detailed plans to .tmp/plan.md (2-5 min tasks, exact file paths, acceptance criteria)
  - `/execute` -- task-by-task execution with safety stops, subagent dispatch, post-task review
  - `/debug` -- 4-phase systematic debugging (investigate > analyze > hypothesize > fix)
  - Verification gate wired into `/closeout` (step 4b) and `/pipeline` (step 7)
  - Orchestrator rule `~/.claude/rules/build-flow.md` -- chains full flow on non-trivial builds
- Updated YouTube skill SKILL.md with OAuth operations documentation
- Updated YouTube skill memory with OAuth scope-loss warning

### Decisions
- Cherry-pick Superpowers patterns (custom build) instead of installing plugin wholesale -- avoids 14 extra skill descriptions loading into context on top of RA's 34 existing skills

### Deployed
- Nothing deployed

### Blockers
- YouTube token scope will get overwritten when other tools re-auth with narrower scopes -- no permanent fix yet
- New skills untested in real production use -- first test will be chatbot recovery or portfolio build

---

## Session 115 -- 2026-04-13 (context-optimization)

### What
- Applied Brad's power-ups: `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=75` + `BASH_MAX_OUTPUT_LENGTH=150000` in settings.json env
- Removed `@decisions/log.md` from global CLAUDE.md (45KB/message savings)
- Moved me.md, work.md, facts.md from @-includes to on-demand pointers (~10KB/message)
- Archived 8 pre-April decisions to `decisions/archive/log-2026-q1.md`
- Archived 5 parked v1 skills to `.claude/skills-archive-v1/`
- Cleaned settings.local.json: 153 → 45 allow patterns (~14.7KB savings)
- Trimmed MEMORY.md: 120 → ~95 entries, organized by section (~6KB savings)
- Trimmed current-priorities.md: 11.2KB → 3.0KB (cut completed section)
- Added deny rules for node_modules, .git/objects, dist, lock files, archives
- Disconnected 4 unused MCPs (Gmail, Calendar, Drive auth, Telegram)
- Archived PROJECT_LOG sessions 73-97 (94KB → 53KB)
- Audited backlog: removed 1 done item, reworded 3 stale items
- Result: ~91% reduction in per-message preloaded context (~29K → ~2.5K tokens)

### Decisions
- Progressive disclosure for CLAUDE.md: only current-priorities + goals always loaded; everything else on-demand
- Parked v1 skills archived (not deleted) to .claude/skills-archive-v1/
- PROJECT_LOG archived at session 97 boundary

### Deployed
- Nothing deployed

### Blockers
- Env var changes take effect next session
- MCP disconnect is per-session habit (not persistent)
- Further global skill audit possible (skill-builder 29KB, video-to-website 28KB)

---

## Session 114 -- 2026-04-13 (content-engine-v3-fidelity) [IN PROGRESS]

### Savepoint 03:00 UTC+8
- Built fidelity scorecard + batch randomizer (v2), batches 001 (9/11) and 002 (~6/9)
- Built cross-session headline dedup + layout history tracking
- Headline dedup and layout history confirmed working (zero reuse in batch 002)

### Savepoint 07:30 UTC+8

**Done:**
- Discovered v2 narrative prompts fail product fidelity -- RA introduced D918 fidelity-spec JSON approach (product as locked asset, scene as variable)
- A/B tested narrative vs fidelity-spec on Outback Blue (hardest product) -- narrative failed, fidelity-spec passed consistently
- Built 3 new skills: `/dubery-fidelity-prompt` (prompt generator), `/dubery-v3-pipeline` (orchestrator), `/dubery-v3-validator` (6-check validator)
- Built `product-specs.json` (11 products) + `prodref-metadata.json` (all angles with clock directions, compatible_directions, strengths)
- Added `outback-blue-0.png` multi-view reference (covers most angles in one image)
- Updated `schema_parser.py` for formatted JSON (indent=2)
- Tested Outback Blue across ~15 scenes (gym, cafe, boat, dashboard, desk, park, barbershop, Cebu coast, Pampanga, Seoul, Subic pier, jeepney, Doha, Riyadh, Palawan, Hong Kong) -- consistent passes with D918 spec
- Removed KNOCKOUT from bold layouts, updated V5 validator to not penalize -1 angle

**Decisions:**
- v3 fidelity-spec replaces v2 narrative prompts for ALL image gen
- Product is "locked asset" with structural details, scene is "variable"
- Don't describe emblem -- let Gemini read from reference photo (unless spec file includes it)
- "oversized" in proportions inflates product -- use "standard"
- reflection_logic simplified to fixed string, contact_points removed
- Prodref angle drives prompt direction -- text and image must agree
- Front-facing refs (-2, -3) don't work for person-wearing -- arm detail missing
- outback-blue-0.png (multi-view) works as single ref for all categories
- Mandatory prompt prefix: "Generate an image based on the following JSON parameters and the attached reference image:"

**Learnings:**
- Gemini follows text descriptions too literally -- describing the emblem wrong produces wrong emblems, not describing it lets Gemini read from the photo correctly
- Same headline = same-looking image (not just text repetition, functional duplication)
- Camera lens choice matters: 85mm for brand premium, 50mm for candid, 24mm for selfie
- Formatted JSON (indent=2) works better than one-liner -- Gemini can parse the hierarchy

**In flight:**
- v3 pipeline validated on Outback Blue only -- 10 other products need D918-quality specs
- Brand categories (callout, bold, collection) untested with v3

**Memories saved:**
- [v3 Fidelity Approach](project_v3_fidelity_approach.md) -- product-as-locked-asset JSON schema, validated on Outback Blue
- [Prodref Drives Direction](feedback_prodref_drives_direction.md) -- ref angle determines prompt direction, never conflict
- [Oversized Inflates Product](feedback_oversized_inflates.md) -- don't use "oversized" in proportions
- [Sequential Prompt Planning](feedback_sequential_prompt_planning.md) -- already saved earlier

---

## Session 113 -- 2026-04-12 (content-engine-v2-polish)

### What
- A7.1: Added R6 person-anchor framing rule to UGC skill -- banned whole-body/wide shots, added 6-option Framing Bank
- A7.2: Replaced all 8 gritty TEXTURE surfaces in brand-bold with clean premium (marble, walnut, slate, leather, bamboo, acrylic, metal, concrete-smooth)
- Bank rebalancing across all 4 v2 skills -- swapped gritty locations/surfaces/atmospheres for clean premium, added AESTHETIC DEFAULT note
- Banned `-2` (multi-angle strip) and `-multi` (composite) product ref angles across all 7 content skills
- Updated `generate_vertex.py` to default output to `contents/new/YYYY-MM-DD_{name}.png`
- Added 4 loadout auto-allow patterns to settings.json
- Generated 8 test images: 4 passed (011, 013b, 014, BOLD-002), 2 failed fidelity (012, 012b ~50%), 1 failed missing ref (013), 1 layout repetitive (BOLD-003)
- Added backlog: trend researcher agent, content batch randomizer, OFW location sub-bank
- Killed orphan Claude process PID 17656

### Decisions
- Ban `-2`/`-multi` angles for all image generation (catalog/reference use only)
- Clean premium is the default aesthetic across all content skills
- TEXTURE layout refined with clean premium surfaces (not retired)
- Python `random.choice()` from banks produces better variety than LLM-picked combos

### Deployed
- Nothing deployed

### Blockers
- Product fidelity scorecard needed (Bandits Green ~50% fidelity)
- Narrow scenarios (CAFE_TABLE) produce repetitive outputs
- Cross-session prompt combo deduplication still open
- First real batch volume + cadence undecided

---

## Session 112 -- 2026-04-12 (youtube-account-integration)

### What
- Added YouTube OAuth scope to token.json (readonly -> full read/write). Created `tools/reauth_token.py` with all 6 scopes
- Fixed scope drift -- token was down to 2 scopes, restored all 6 (drive, sheets, gmail.modify, gmail.settings.basic, calendar, youtube)
- Pulled full YouTube account: 390 liked videos, 228 subscriptions, 13 playlists, channel info
- Analyzed YouTube profile -- identity layers: longboarder (core), drummer, PH punk music, Axie/Web3 past, sailing, AI learner
- Assessed 5 liked videos for ingest, ingested 3: Jack Roberts ($10k websites), Aaron Young (Claude+Google Ads), Brad (Claude Code usage limits)
- Extracted power-ups from Brad's video (autoCompact 75%, BASH_MAX_OUTPUT_LENGTH, MCP hygiene)

### Decisions
- Upgraded to full `youtube` scope (not just readonly) for playlist creation/management
- Ingest #1 (Jack Roberts), #2 (Aaron Young), #4 (Brad). Skip #3 (entertainment). #7 already ingested session 94.

### Deployed
- Nothing deployed

### Blockers
- Power-ups not yet applied: autoCompactPercentageOverride 75 + BASH_MAX_OUTPUT_LENGTH=150000
- A7 content engine tasks still queued (UGC R6 framing, brand-bold TEXTURE bank, batch volume)

---

## Session 111 -- 2026-04-12 (cloudflare-chatbot-tunnel)

### What
- Migrated duberymnl.com DNS from Namecheap to Cloudflare (free plan). Phases 1-3 complete.
- Set up Cloudflare Email Routing: ras@duberymnl.com -> sarinasmedia@gmail.com (replaced 5 Namecheap eforward MX records)
- Cut nameservers to Cloudflare (jerome.ns + ursula.ns). Propagation confirmed instantly via Google DNS.
- Created named Cloudflare Tunnel `dubery-chatbot` (UUID f2e8c4e2-7911-4fdf-bf05-af6dc9d9a6b2)
- Routed chatbot.duberymnl.com CNAME to tunnel, wrote config.yml, started Flask + tunnel successfully
- Killed orphan Claude process PID 13752
- Cloudflare account: sarinasmedia+rasclaw@gmail.com

### Decisions
- Cloudflare account uses plus-addressed gmail (sarinasmedia+rasclaw@gmail.com) for inbox filtering

### Deployed
- Nothing deployed (waiting on Cloudflare SSL cert provisioning)

### Blockers
- Cloudflare zone still "waiting for nameserver propagation" internally -- SSL cert not yet provisioned for chatbot.duberymnl.com
- Once SSL is live: verify tunnel, wire Meta webhook (Phase 6), auto-start (Phase 5), monitoring, unpause ads

---

## Session 110 -- 2026-04-12 (dashboard)

### What
- Researched Beyblade tournaments for today (Metro Manila) -- no confirmed event, pointed RA to FB groups + pabeybey.com calendar
- Found Ten-O BBX Ranked Tournament #10 at Guijo Suites Makati (6 PM reg, P400, 3G RANKED SWISS, 50 slots)
- Researched Star City vs X-Site Festival Mall for family outing -- Festival Mall won (P399 ride-all-you-can, indoor, cheaper, Toy Town Beyblade possible)
- Updated ra-dashboard: Baby Jah feed 11:30 AM, Iver's bday (Apr 11), Pyro Musical (Apr 11), Festival Mall outing (Apr 12). Deployed to Vercel.

### Decisions
- None this session

### Deployed
- ra-dashboard updated + deployed to Vercel (family timeline + baby tracker)

### Blockers
- None

---

## Session 109 -- 2026-04-12 (savesession-command)

### What
- Created `/savesession` command — standalone shortcut for `/closeout --defer`. Harness hot-reloaded.
- Added 9 auto-allow permission patterns to `settings.local.json` for closeout + sendit operations (git add/commit/push for 3 repos, backup_secrets.py, sync_folder.py both conditional forms).

### Decisions
- `/savesession` as standalone command instead of `/closeout --defer` flag | cleaner UX, no flag to remember | RA preference

### Deployed
- `/savesession` command live and hot-reloaded. First use = this session.

### Blockers
- `/sendit` still needs first real-world test

---

## Session 108 -- 2026-04-12 (session-workflow-redesign)

### What
- Diagnosed closeout slowness: session entry length NOT the bloat (25-45 lines consistent across 34 sessions). Real cost = ADR format creep + bidirectional cross-link overhead.
- Saved `feedback_closeout_format.md`: one-liner decisions default, full ADR only for architectural. Conservative back-linking (forward-only unless ≥2 related). Pushed `cb15cc8`.
- Saved `feedback_multi_session_workflow.md`: consolidated multi-window best practices.
- Explained `~/.claude` three-repo backup architecture + two-layer secret backup to RA.
- **Modified `backup_secrets.py`**: added `pin_latest_revision()` — keepForever=True on each upload. Verified 28 existing revisions per file, latest pinned. Pushed `01b3813`.
- **Designed + implemented `/closeout --defer` + `/sendit`:**
  - Modified `closeout.md`: `--defer` skips push + backup + Drive sync, commits locally only.
  - Created `sendit.md`: 6-task parallel ship (secret backup, Drive sync x2, git push x3 with pull-rebase fallback).
  - RA's key insight: secrets + Drive sync belong with push ("local vs ship" decomposition).
  - Harness hot-reloaded both commands immediately.
- **Saved `feedback_session_rename_drift.md`**: proactive mid-session rename when topic drifts. Trigger conditions + anti-nagging rules. Session 105 was the reference case (5 unrelated topic shifts, none caught).
- **Updated `feedback_loadout_remote_status.md`**: conditional rename prompt at loadout (hard ask for multi-session + unnamed, soft for single-session).
- Updated `feedback_multi_session_workflow.md` with defer+sendit pattern + mid-session rename pointer.
- **First ever `/closeout --defer` run** — this session is the inaugural use.

### Decisions
- One-liner decisions default, ADR for architectural only | entry length isn't the bloat, ADR creep is | closeout timing analysis
- Conservative back-linking: forward-only unless ≥2 related | below threshold = wasted overhead | same analysis
- Drive revision pinning via keepForever=True | 28 revisions exist, prevents 30-day auto-delete | RA backup audit
- `/closeout --defer` + `/sendit` for multi-window | decouple save from ship, eliminate push races | RA's "local vs ship" insight
- `/flush` renamed `/sendit` | RA's voice, action-oriented | RA preference
- Secrets + Drive sync defer with push | all cloud-ship ops should defer together | RA's decomposition
- Session drift detection as behavioral rule, not hook | Claude notices, no code needed | RA observed session drift pattern
- Conditional rename at loadout: hard ask for multi-session only | only nag when useful | multi-window design

### Deployed
- `backup_secrets.py` keepForever pinning: pushed `01b3813` to DuberyMNL
- `/closeout --defer` + `/sendit` commands: created + hot-reloaded, inaugural use this session
- 3 feedback memories created, 2 updated, MEMORY.md indexed

### Blockers
- Chatbot recovery still top priority (unchanged)
- `/sendit` needs first real-world test — RA runs it after this closeout
- PROJECT_LOG archive (Tier 1 audit): discussed, not decided. Backlog candidate.
- Rasclaw-as-channel-plugin struck from backlog (confirmed working session 105)

---

## Session 107 -- 2026-04-12 (content-engine-v2)

### What
- Loadout: tunnel healthy, Meta scheduled queue = 0 (content bottleneck surfaced)
- **Phase A -- v2 skill rewrites** (all 3 active content skills upgraded to variety-banks + WF2 fidelity pattern):
  - A1 reverted: attempted naturalism patch on `dubery-ad-creative`, `dubery-prompt-validator` PF-4 enforces the exact v1 coercive phrase — reverted. Wrote `project_content_skill_iterations.md` locking v1 skills (ad-creative / prompt-writer / validator / infographic-ad / ugc-fidelity-gatekeeper) as parked.
  - A2 `dubery-brand-callout`: 5 "Reference prompt" templates removed, 20 per-layout variety banks added (129 options), R2/R3/R4 fidelity ported, angle randomization rule
  - A3 `dubery-brand-collection`: same pattern (18 banks, 106 options), L2 angle consistency + render_notes "applies uniformly to all products"
  - A4 `dubery-ugc-prompt-writer`: 7 global variety banks added (Location PH-specific / Lighting / Surface / Subject Archetype / Outfit / Atmosphere / Photographic Treatment) + batch diversity check in execution order
  - A6 structural smoke test passed across all 4 skills
- **Committed Phase A as `6080ada`** -- feat: v2 rewrite for brand-callout + brand-collection, UGC variety banks (+698 / -170)
- **Phase B -- posting audit + smoke test:**
  - B1: Story Rotation GH Actions cron HEALTHY (15/15 green, fires every 4h). UGC cadence is NOT a cron — uses Meta-native scheduled posts via `schedule_batch.py --ugc`. Meta token valid. **Scheduled post queue = 0** (drained during chatbot recovery — the actual "resume posting" bottleneck)
  - **36 IMAGE_APPROVED ads pipeline SCRAPPED** per RA — focus = brand + UGC only going forward
  - B2: Built new skill `/dubery-prompt-reviewer` — v2 quality gate, V1-V7 universal + per-skill checks, PASS/PATCH/FAIL verdicts, applies only to v2 skills
  - B3: Generated 4 sample prompts — bold TEXTURE/Outback Red, callout RADIAL/Bandits Green, collection HERO_CAST/Outback trio, UGC OOTD_STREET regen
  - B4: Reviewer returned 2 PASS + 2 PATCH. Applied UGC 1-word patch (`reflecting` → `catching`). Collection angle flagged as next-batch reminder only
  - B5: Generated 4 images via Vertex AI Gemini 3.1 Flash, ~$0.28 spend
  - B6: RA reviewed:
    - **CALLOUT-001 APPROVED**: "looks perfect". RA insight: the aged-leather + window-light scene bank could cross-pollinate to UGC if labels/arrows removed
    - **COLL-001 APPROVED + v2 VALIDATED**: "prompt was already used, this version is much better, reflection and product fidelity top notch, can be used as ads or UGC" — direct RA confirmation v2 > v1 on same input
    - **UGC-005 PARTIAL**: "whole-body, sunglasses barely recognizable" — framing rule missing from skill
    - **BOLD-001 REJECTED**: "looks AI, nail thru product doesn't make sense, don't like the dirty and gritty scene" — TEXTURE surface bank aesthetically biased wrong
  - RA also flagged: 3 of 4 prompts were "already used" across sessions — variety banks don't track cross-session history

### Decisions
- **v1 content skills parked permanently** — validator chain enforces v1 coercive phrase as required, can't patch piecemeal. Any v2 ad workflow = build new from scratch when paid ads resume. Locked in `project_content_skill_iterations.md`
- **v2 skill rewrite pattern VALIDATED** — RA confirmation on collection ("much better than prior") is direct A/B evidence. Pattern is the new template for all content skills. See `project_v2_skills_validated.md`
- **36 IMAGE_APPROVED ads pipeline scrapped** — brand + UGC only going forward
- **`/dubery-prompt-reviewer` is a required quality gate** before any batch image gen spend
- **DuberyMNL aesthetic = clean premium, NOT gritty/weathered** — session 107 smoke test BOLD-001 rejection. See `feedback_ra_aesthetic_preference.md`
- **UGC framing rule required** — product must be recognizable, no whole-body wides. See `feedback_ugc_framing.md`

### Deployed
- `6080ada` DuberyMNL main: Phase A skill rewrites (committed in session, pushed in closeout)
- `/dubery-prompt-reviewer` skill (committed in closeout)
- 4 sample images → `contents/new/SAMPLE-*.png` (Drive-synced in closeout, tier 2 per content storage rule)

### Blockers
- **A7.1** next session: apply UGC R6 framing rule + tight-crop photographic treatment bank
- **A7.2** next session: refine brand-bold TEXTURE surface bank (swap gritty for clean premium) OR retire TEXTURE layout entirely — RA to decide
- **A7.3** next session: regenerate BOLD-001 sample after A7.1/A7.2 fixes
- Backlog: cross-session prompt combo deduplication (variety banks don't track history)
- Backlog: cross-pollinate brand-callout scene bank into UGC as "product-hero" variant
- Decision pending: first real brand + UGC batch volume + cadence after A7 fixes

---

## Session 106 -- 2026-04-12 (chatbot-image-bank-v2)

### What
- Loadout: dubery-dev tunnel healthy, plugged in, killed 1 orphan + 1 rasclaw plugin per RA, kept this session only.
- **Recovery path (a) -- image bank restored 21 -> 48 with per-image captions.** Pulled session 98 manifest (d942c44), refactored schema so each image is `{url, caption}` dict, restored all 8 categories (11 hero + 6 model + 6 lifestyle + 4 collection + 5 brand + 8 customer-feedback + 6 proof + 2 support). Added `get_image_caption()` helper. Smoke test: 48 loaded, full knowledge 10819 chars.
- **Updated conversation_engine.py IMAGE RULES.** Removed "collection-/comparison- don't exist" ban (restored collection category). Replaced "never describe the scene" rule with "trust the caption, don't invent beyond" -- old rule was right when Gemini was blind, wrong now that captions exist. Added category-by-category picking guidance.
- **Visual verification of all 11 hero shots via local Read().** Discovered every hero shot is a **flat-lay on kraft background showing the full unboxing set** (Dubery box, drawstring pouch with microfiber cloth, warranty card) -- NOT a "clean product shot." Rewrote all 11 captions to lead with the flat-lay context.
- **CATALOG variant_notes errors fixed** (inherited from session 98 "visually verified" text that wasn't actually verified): Outback Red `gold/amber` -> `red/orange`, Outback Green `green-blue` -> `green/purple iridescent`, Bandits Green `black with green accents` -> `green + black bicolor`, Bandits Tortoise `dark tortoiseshell` -> `brown + dark brown tortoiseshell`.
- **Anchoring bias caught:** My first pass comparing Rasta and Outback hero shots concluded they were the same shape. RA pushed back. Second look: Rasta has curved top edge, visibly wider frame, taller lens -- the CATALOG "oversized aviator-style square" description is correct. Logged as feedback memory update.
- **Hero shots also double as inclusions shots.** Encoded into hero category hint: "don't also send support-inclusions after a hero" -- prevents redundant double-sends since every hero already shows the inclusions.
- **Recovery path (b-c) -- Cloudflare migration prep complete.** Discovered cloudflared 2026.3.0 already installed. Pulled full DNS state (A->Vercel, CNAME www->Vercel, 5 MX->Namecheap eforward email forwarding IS actively routing, SPF TXT, no DMARC/DKIM). Wrote comprehensive 6-phase runbook at `references/cloudflare-migration-runbook.md` with rollback plans + 3 open questions.
- **Recovery path (g) -- CRM test data cleanup done.** Wrote `tools/chatbot/cleanup_crm_test_data.py` (token.json OAuth2, --dry-run default, --confirm to delete). First attempt used ADC -> 403 insufficient scopes -> switched to token.json. Deleted 61 TEST_ rows: 8 leads, 7 log entries, 46 conversation messages. **Preserved 146 production rows** (25 real leads, 27 log entries, 94 conversation messages from session 97-98 live run) -- case-study material for RAS Creative SOLUTIONS.
- Did NOT execute Option 1 smoke test (Quick Tunnel + local Flask chat-test scenarios) -- RA chose closeout over it.

### Decisions
- **Image bank schema refactor: each image -> `{url, caption}` dict.** Gemini needs per-image captions to pick the right image for conversational context (proof for skeptical, feedback for social proof, collection for series asks). Bare URL strings worked at 21 in one category; 48 across 8 categories demands captions.
- **Restore 48-image bank (reverses session 101's 21-image shrink).** Session 101 called the shrink an "over-correction, expansion parked" -- this session unparks it.
- **Replace "never describe scenes" IMAGE RULE with "trust caption, don't invent beyond".** Old rule was right when Gemini was blind to photos, wrong now that captions describe scenes.
- **CATALOG variant_notes corrections for 4 variants.** Visual inspection revealed session 98 "visually verified" claim was partially wrong. Generalizable lesson: even memories that claim verification may need re-verification.
- **Hero shots double as inclusions shots -- encode into category hint.** Every card shot is a flat-lay with box/pouch/cloth/warranty card. Sending support-inclusions AFTER a hero is redundant.
- **Cloudflare migration: Path B (prep now, execute next session).** Lower risk of half-finished state if interrupted. Runbook at `references/cloudflare-migration-runbook.md`.
- **Cloudflare Email Routing over MX-mirroring.** Namecheap email forwarding is documented as tied to Namecheap NS. Email Routing survives the cutover cleanly.
- **CRM cleanup tool pattern: token.json OAuth2, --dry-run default, --confirm to delete.** ADC is missing the spreadsheets scope on this machine. Using token.json avoids touching global ADC state (which would affect Vertex AI + Veo tools).

### Deployed
- Nothing deployed. Chatbot still DOWN. All work was code/config/data changes for the recovery path.

### Blockers
- **Cloudflare migration execution** -- needs dedicated 45-60 min session. Gated on 3 open questions in runbook: (1) Cloudflare account fresh or existing? (2) Namecheap 2FA status? (3) ras@duberymnl.com verification dependencies?
- **Quick Tunnel smoke test of new image bank** -- deferred. Still valuable: proves Gemini picks sensible image_keys with new captions before committing to permanent URL migration. ~15-25 min, can attach to the migration session.
- **Recovery path remainder after migration:** (d) wire Meta webhook, (e) auto-start Flask + cloudflared, (f) uptimerobot, (h) unpause boosted ads, (i) 1 week clean production data capture.

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
