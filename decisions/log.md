# Decision Log

Append-only. Format: [YYYY-MM-DD] DECISION: ... | REASONING: ... | CONTEXT: ...

---

[2026-03-20] DECISION: Switch image gen from parallel to sequential | REASONING: RA wants to see each image land in Drive before next one starts -- easier to monitor, less risk of overloading kie.ai | CONTEXT: Session 44, run_wf2.py ThreadPoolExecutor removed

[2026-03-20] DECISION: Auto-trigger WF2 after caption review submit | REASONING: Eliminates manual handoff between WF1 review and WF2 -- full automation goal | CONTEXT: Session 44, start_review.sh hooks into run_post_review.py

[2026-03-20] DECISION: Add retry logic to claude --print calls | REASONING: API 500 crashed the pipeline mid-run, left orphaned captions -- retry with 30s wait handles transient errors | CONTEXT: Session 44, _run_claude_with_retry in run_post_review.py

[2026-03-20] DECISION: Make run_post_review.py batch-aware with re-scan | REASONING: Crashed run left 4 captions at PROMPT_READY that were missed on retry -- re-scan catches all PROMPT_READY in the batch | CONTEXT: Session 44

[2026-03-20] DECISION: Content pipeline trigger is "generate content" not a skill | REASONING: The workflow is just two steps (run caption gen skill + start_review.sh) -- wrapping in a skill adds a layer without adding logic. Automation lives in the scripts. | CONTEXT: Session 44

[2026-03-20] DECISION: Restructure stage_ad.py to 1 campaign + 1 ad set + N ads | REASONING: Previous 1-campaign-per-caption structure would cost P7,200/day for 36 ads. Meta best practice is shared campaign/ad set so the algorithm optimizes across creatives and budget is shared. | CONTEXT: Session 44, WF3b audit

[2026-03-20] DECISION: Keep WF3b manual (no auto-trigger after image review) | REASONING: Not all IMAGE_APPROVED images should become ads. RA should choose which ones to stage. Auto-staging could waste ad budget. | CONTEXT: Session 44

[2026-03-20] DECISION: Store campaign/ad set IDs in .tmp/ads_config.json | REASONING: IDs are mutable state (campaigns can be deleted in Ads Manager), not secrets. .env is for credentials. JSON state file follows pipeline.json pattern. | CONTEXT: Session 44

[2026-03-20] DECISION: Create content pipeline skill that skips review server | REASONING: Claude-generated captions are good enough to go straight to APPROVED. RA confirmed during branding test -- 3 captions went caption -> prompt writer -> done with zero edits needed. Removing the review step cuts the pipeline from 6 steps to 3. | CONTEXT: Session 45, branding test for Rule 5a headline identity

[2026-03-20] DECISION: Add product line headline branding (Rule 5a) to prompt writer | REASONING: NB2 was rendering all headlines in plain white text. Each line (Outback/Bandits/Rasta) now has a default visual identity (color, typography, feel) that makes content instantly recognizable per line. Defaults are overridable ("not limited to"). | CONTEXT: Session 45

[2026-03-20] DECISION: Tighten headline position to top 15-20% of frame (Rule 7) | REASONING: Gemini test images had headlines at 30-40% from top, eating into the subject zone. Tighter constraint pushes headlines up and gives more breathing room. | CONTEXT: Session 45, branding test review

[2026-03-20] DECISION: Add anti-CGI lens reflection clause to R4 | REASONING: Bandits test image had digital/CGI-looking blue glow on lenses instead of natural optical reflection. Explicit ban on digital glow, CGI sheen, artificially enhanced lens flare. | CONTEXT: Session 45, branding test review

[2026-03-20] DECISION: Small batches (3-5) preferred over full 15-caption batches for content pipeline | REASONING: Faster feedback loop, less waste if direction is wrong, more variety over time, cheaper image gen. Validator not needed for small batches -- agent self-checks are sufficient. | CONTEXT: Session 45

[2026-03-20] DECISION: Content pipeline reads last 20 captions for context, not all | REASONING: Prevents repeating recent angles/vibes/products without reading the entire pipeline history. 20 is enough for dedup without performance cost. | CONTEXT: Session 45

[2026-03-20] DECISION: R4 changed to ban ALL lens reflection language | REASONING: Both Gemini and NB2 interpret any mention of "reflects the surrounding environment" as an instruction to paint the scene inside the lens -- creating a digital miniature landscape effect. Tried "subtle and physically accurate", tried anti-CGI clause, both failed. Only fix: say nothing about reflections at all and let the reference image handle it. | CONTEXT: Session 45, Gemini test of 20260318-019

[2026-03-21] DECISION: Regeneration has two modes: EDIT and FULL REGEN | REASONING: Full regen rewrote 019's entire scene when only the header position needed moving. Original image was better. EDIT mode sends existing image + instructions to NB2 for targeted fixes. Auto-classifies based on feedback keywords. | CONTEXT: Session 45

[2026-03-21] DECISION: pipeline.json is single source of truth, Sheets are view layers | REASONING: DuberyMNL Pipeline sheet was out of sync (stale statuses, missing entries). If sheet had been authoritative, we'd have lost work. Always write to pipeline.json first, sync TO sheets after. | CONTEXT: Session 45, sheet sync discovery

[2026-03-21] DECISION: DuberyMNL Pipeline sheet replaces DuberyMNL Master as main sheet | REASONING: Master sheet (12eQniol...) has old data from March 9. Pipeline sheet (1LVshSQP...) is the active tracker synced with pipeline.json. Updated facts.md. | CONTEXT: Session 45

[2026-03-21] DECISION: Agent does all creative work inline, no claude --print subprocess | REASONING: Content pipeline architecture separates agent (creative/reasoning) from tools (API execution). Using claude --print loses context, adds latency, and duplicates what the agent already does better. | CONTEXT: Session 46

[2026-03-21] DECISION: NB2 edits only for simple text fixes, everything else full regen | REASONING: First regen batch -- 5/13 failed RA's taste. Edit prompts described deltas ("fix the lens") instead of target state. NB2 interprets literally without composition awareness. Full regens with holistic prompts produce better results. | CONTEXT: Session 46

[2026-03-21] DECISION: _sync_to_sheet must dedup before appending | REASONING: Review server was appending rows without checking if caption ID already existed in the sheet. Session 46 produced 6 duplicate rows in Approved, 2 in Rejected. Fixed: check column A for existing ID before append. | CONTEXT: Session 46

[2026-03-21] DECISION: Approved sheet uses different schema from Rejected/Regenerate | REASONING: Approved has 16 columns (Caption ID through Notes), Rejected/Regenerate have 8 columns (Caption ID through Date). _build_sheet_row now takes sheet_name parameter and outputs the correct format. | CONTEXT: Session 46

[2026-03-21] DECISION: Default image resolution changed to 2K | REASONING: RA requested higher quality output. 1K was the old default. All api_parameters.resolution now set to "2K". | CONTEXT: Session 46

[2026-03-22] DECISION: Google Sheet is source of truth for manual data, sync direction flipped | REASONING: sync_pipeline.py kept overwriting RA's manual edits (product refs, feedback, ad tags) by pushing pipeline.json -> Sheet. RA edits the sheet directly as his dashboard. Now: Sheet -> pipeline.json for manual fields. | CONTEXT: Session 47

[2026-03-22] DECISION: sync_pipeline.py deprecated, agent handles all sheet syncing via MCP | REASONING: The bulk clear-and-rewrite approach kept causing problems: wrong columns, stale data, overwritten edits. Agent has context on what changed and updates specific rows/tabs surgically. | CONTEXT: Session 47

[2026-03-22] DECISION: Never commit or push without RA's explicit permission | REASONING: RA noticed multiple auto-commits and pushes without being asked. "savepoint" means save memory + logs, not git commit. | CONTEXT: Session 47

[2026-03-22] DECISION: captions.json is output only, not a source of ad selection data | REASONING: Was checking captions.json to see which ads were selected. That file is just an export for the browser. Ad selections live in pipeline.json (ad_set field) and Approved sheet (column S). | CONTEXT: Session 47

[2026-03-22] DECISION: Fixed accent color scheme -- red accent + black buttons | REASONING: Tried dynamic extraction (wrong colors per ad), green (clashed with Facebook), blue (too similar to Facebook), charcoal (too muted). Dubery logo red for badges/highlights, black for CTA buttons, Facebook blue for social links. | CONTEXT: Session 47b

[2026-03-22] DECISION: Disable auto-populate variants in order form | REASONING: Pre-filling 4 variants causes price shock -- customer sees P2,800 before they even decided to buy. Empty picker lets them choose at their own pace. | CONTEXT: Session 47b

[2026-03-22] DECISION: Dark mode as default landing page | REASONING: RA loved the dark mode look. Products pop more against dark backgrounds. Toggle available for light mode. On mobile, toggle fades after 15s. | CONTEXT: Session 47c

[2026-03-22] DECISION: Google Places removed, using browser native autocomplete | REASONING: Google Places returned Plus Codes in addresses, Chrome's autofill bubble kept appearing on top. Native browser autocomplete is simpler -- address confirmed via call/SMS anyway. | CONTEXT: Session 47c

[2026-03-22] DECISION: Dual submit buttons (regular + express delivery) | REASONING: Gives customer urgency option without forcing it. Express sends flag in payload so RA knows to prioritize. Regular order is the safe default. | CONTEXT: Session 47c

[2026-03-22] DECISION: Bought duberymnl.com custom domain | REASONING: Required for Meta Business Verification (vercel.app rejected as shared domain). Also makes ads look professional and enables business email. P500-800/year. | CONTEXT: Session 47f

[2026-03-22] DECISION: Registered DUBERYMNL with DTI | REASONING: Meta requires official business document for verification. DTI sole proprietorship registration is the cheapest/fastest option (P200, 1-2 days). Ref: BVZE438718986529. | CONTEXT: Session 47f

[2026-03-22] DECISION: Manual ad creation in Ads Manager while API blocked | REASONING: App in development mode blocks ad creative creation via API. Manual creation works immediately. 10 ads created manually -- will switch to automated stage_ad.py once Business Verification approved. | CONTEXT: Session 47g

[2026-03-22] DECISION: Targeting Metro Manila only for Phase 1 | REASONING: Delivery area is Metro Manila. Tight targeting = faster learning, cleaner data. Advantage+ audience disabled to maintain control. | CONTEXT: Session 47g

[2026-03-23] DECISION: Google Drive reorganized, DuberyMNL folder untouched | REASONING: 100+ root items was unmanageable. Organized into Career, Skateboarding, Archive (6 subfolders), Junk. DuberyMNL folder has workflow dependencies -- never modify. | CONTEXT: Session 48

[2026-03-24] DECISION: Organic posting schedule is Tue/Thu/Sat/Sun at 12:00 PM PHT | REASONING: 4 posts/week hits RA's 3-4/week target. 12PM is peak Filipino lunch-scroll engagement. One post per day keeps it natural. | CONTEXT: Session 51, WF3a

[2026-03-24] DECISION: Wait for Meta Business Verification before scheduling organic posts | REASONING: API requires pages_manage_posts permission which is locked behind verification. Manual posting is possible but RA prefers to wait. Tools are built and ready. | CONTEXT: Session 51

[2026-03-25] DECISION: Remove session_log.md from loadout skill Step 3 | REASONING: session_log.md has no session boundaries or dates -- reading it during loadout caused cross-session confusion (attributed old overlay work to current session). session_checkpoint.md (closeout) + ra-sync/context.md already answer "what happened last session" better. Log kept for crash recovery via checkpoint cron. | CONTEXT: Session 56, loadout skill audit

[2026-03-25] DECISION: Automate dashboard sync as local cron pipeline (15 min interval) | REASONING: Dashboard data processing was embedded in loadout, making startup heavy and data stale between sessions. Local cron pipeline: Stage 1 DETECT (poll Drive), Stage 2 TRIAGE (filename sort + OCR + Quick Log), Stage 3 PROCESS (Sonnet via claude --print for photos + unknown screenshots, dedup against Quick Log), Stage 4 BUILD (merge + push). No API costs -- uses Max plan. | CONTEXT: Session 56

[2026-03-25] DECISION: Split dashboard-data.json into display layer + database | REASONING: Long-term, dashboard-data.json will bloat as transactions/feeding/timeline grow. Split into dashboard-data.json (recent, lean, what the UI reads -- regenerated from DB) and dashboard-db.json (full history, append-only, local only). Display file is disposable and regenerated from DB on every sync. | CONTEXT: Session 56

[2026-03-26] DECISION: Hybrid pipeline -- cron detects + queues, Opus processes at session start | REASONING: Sonnet via claude --print lacks family context (can't tell RA from Arabelle, doesn't know schedules). Opus in session has full memory and produces dashboard-quality entries. Cron handles grunt work (polling, downloading), Opus handles understanding. | CONTEXT: Session 56

[2026-03-26] DECISION: All screenshots go to AI, no skips | REASONING: RA takes screenshots intentionally to communicate what's happening. Skipping Tapo/Chrome/Messenger screenshots means missing context. Screenshots are RA's way of talking through images. | CONTEXT: Session 56

[2026-03-26] DECISION: Split dashboard into dedicated moderator agent (separate Claude Code window) | REASONING: Dashboard work (image processing, Baby Jah monitoring, life data) was bloating the DuberyMNL loadout and competing for context. A dedicated window means: focused context, own memory, no cross-contamination with work tasks. Moderator is manual (RA opens it), not always-on. | CONTEXT: Session 57, tools/sync/ moved from DuberyMNL to ra-dashboard, cron updated, loadout/closeout slimmed down

[2026-03-26] DECISION: DuberyMNL dashboard is read-only monitoring + CRM, not a pipeline trigger | REASONING: Content pipeline needs agent context (memory, prompt rules, last 20 captions for dedup, product branding). Running headless via webhook or Flask endpoint loses all of that. Dashboard reads from Sheets/Meta APIs, Claude Code writes to them. Clean separation: browser = read layer, agent = write + orchestrate. | CONTEXT: Session 57, dashboard v1 build

[2026-04-07] DECISION: UGC captions must never contain pricing, CTAs, promo codes, or delivery mentions | REASONING: UGC is social proof, not ads. Pricing in a "personal post" breaks the illusion instantly. The sales funnel happens downstream (auto-DM + chatbot). | CONTEXT: Session 86, dubery-ugc-caption-gen skill

[2026-04-07] DECISION: UGC fidelity gatekeeper is binary PASS/REJECT with no PATCH option | REASONING: Patching product appearance descriptions creates subtle visual errors that slip through and waste kie.ai credits. A false reject costs one rewrite. A false pass costs credits + RA's time + a trash image. Reject and rewrite from scratch is safer. | CONTEXT: Session 86, dubery-ugc-fidelity-gatekeeper skill

[2026-04-07] DECISION: Combined server for chatbot + comment responder (single Flask app, port 5002) | REASONING: Two servers = two ngrok tunnels, two processes to manage, two points of failure. One server with /webhook (Messenger) + /comment-webhook (feed) is simpler to deploy and monitor. | CONTEXT: Session 86, messenger_webhook.py

[2026-04-07] DECISION: DUBERY50 discount code = P50 off single pair | REASONING: RA confirmed. Small enough to not hurt margins, meaningful enough to nudge hesitant buyers. Chatbot mentions it when customer seems on the fence. | CONTEXT: Session 86, knowledge_base.py

[2026-04-07] DECISION: UGC posting cadence is 2-3x/day at 9AM/12PM/6PM PHT | REASONING: RA confirmed. UGC is lightweight social proof content -- higher frequency is fine. Covers morning scroll, lunch break, and evening wind-down. Ad creatives stay at 4x/week. | CONTEXT: Session 86, schedule_post.py

[2026-04-07] DECISION: Comment reply templates must be English-forward, not heavy Tagalog | REASONING: RA rejected first draft (too Tagalog). Brand page replies should be clean English with natural tone. DM openers can have light Taglish since they're private messages. | CONTEXT: Session 86, comment_templates.py

[2026-04-07] DECISION: Caption drives image -- scenario_hint + mood from caption determine the visual scene | REASONING: Random scene selection produces disconnected caption+image pairs. When the caption is about a Tagaytay road trip, the image must be at Tagaytay. Caption-driven derivation ensures the post tells one coherent story. | CONTEXT: Session 86, dubery-ugc-prompt-writer caption-driven mode
