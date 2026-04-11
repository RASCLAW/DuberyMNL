# Decision Log

Append-only. Format: [YYYY-MM-DD] DECISION: ... | REASONING: ... | CONTEXT: ...

---

[2026-04-12] DECISION: v2 content skill rewrite pattern validated, v1 ad skills parked permanently | REASONING: Session 107 rewrote brand-callout, brand-collection, ugc-prompt-writer to v2 (variety banks + WF2 fidelity + build-fresh). Smoke test on 4 samples produced 3 approved outputs. RA directly confirmed brand-collection HERO_CAST output is "much better than prior v1 attempts on the same prompt" — A/B validation. v1 ad-creative patch attempt (A1) discovered dubery-prompt-validator PF-4 enforces exact v1 coercive phrase as required field, can't patch piecemeal. | CONTEXT: Session 107 Phase A commit 6080ada

[2026-04-12] DECISION: /dubery-prompt-reviewer is mandatory quality gate before any batch image gen spend | REASONING: New skill built session 107 with V1-V7 universal + per-skill checks, PASS/PATCH/FAIL verdicts. First use on 4-sample batch correctly flagged UGC R3 violation (reflecting→catching) and collection angle randomization note. Skill-based reviewer is auditable and composable; Python linter would be harder to tune. | CONTEXT: Session 107 B2

[2026-04-12] DECISION: 36 IMAGE_APPROVED ads pipeline scrapped, focus = brand + UGC only | REASONING: RA direction — v1 ad-creative workflow no longer used. DuberyMNL ads will be rebuilt v2 from scratch when paid ads resume (currently paused during chatbot recovery). Brand content already serves as ads in the Messenger-pivot strategy per feedback at v1 vs v2 iteration discussion. | CONTEXT: Session 107 posting audit

[2026-04-12] DECISION: DuberyMNL aesthetic = clean premium, not gritty/weathered | REASONING: Session 107 smoke test BOLD-001 rejected — RA "looks AI, nail thru product doesn't make sense, don't like the dirty and gritty scene". brand-bold TEXTURE surface bank (rusted metal, mossy stone, corrugated steel, dark brick, wet asphalt) is aesthetically biased against the brand. Next session A7.2 refines or retires TEXTURE. | CONTEXT: Session 107 B6

[2026-04-12] DECISION: UGC framing rule required — no whole-body shots, product must be recognizable | REASONING: Session 107 smoke test UGC-005 was a wide BGC street shot where sunglasses occupied <10% of frame. RA "we need to keep the UGC away from whole body shots, the sunglasses are barely recognizable". Next session A7.1 adds R6 + tight-crop photographic treatment bank (waist-up / chest-up / face-shoulders / tight face crop / over-the-shoulder), bans wide environmental shots for person-anchor. | CONTEXT: Session 107 B6

[2026-04-12] DECISION: Image bank schema refactor -- each image is {url, caption} dict | REASONING: Gemini needs per-image captions to pick the right image for conversational context (proof shots for skeptical customers, feedback for social proof, collection for series asks). Bare URL strings worked at 21 images in one category but don't scale to 48 across 8 categories. | CONTEXT: Session 106 chatbot image bank restore

[2026-04-12] DECISION: Restore 48-image bank, reverse session 101 shrink | REASONING: Session 101 called the 48->21 cut "over-correction, parked for next session". That session is now. Collection/feedback/proof/brand/model categories are all back. Enables Gemini to send social proof, series showcases, and legitimacy shots that were previously unavailable. | CONTEXT: Session 106

[2026-04-12] DECISION: Replace "never describe scenes" IMAGE RULE with "trust caption, don't invent beyond" | REASONING: Old rule was right in session 98/101 when Gemini had no caption data and would hallucinate scene details. Now that every image has a one-line caption, Gemini can lightly reference scene content (e.g. "at a cafe" from the caption) without inventing. Prevents the robotic product-only description pattern. | CONTEXT: Session 106 conversation_engine IMAGE RULES rewrite

[2026-04-12] DECISION: Hero shots double as inclusions shots -- encode into category hint | REASONING: Visual verification revealed every card shot is a flat-lay with the full unboxing set (box, pouch, cloth, warranty card). Sending support-inclusions AFTER a hero is redundant and feels robotic. Hero category hint now says "don't also send support-inclusions after a hero". | CONTEXT: Session 106 visual inspection of all 11 hero shots

[2026-04-12] DECISION: Fix CATALOG variant_notes for 4 variants -- Bandits Green/Tortoise, Outback Red/Green | REASONING: Session 98 committed "rewrote from actual visual inspection" but 4 variants had errors inherited from supplier text (Outback Red was said gold/amber but is red/orange, Outback Green was said green-blue but is green/purple iridescent, Bandits Green was said black with accents but is bicolor, Bandits Tortoise was said dark but is brown dominant). Generalizable lesson: even memories claiming verified may need re-verification. | CONTEXT: Session 106 visual inspection caught 4 errors

[2026-04-12] DECISION: Cloudflare migration = Path B (prep now, execute in dedicated session) | REASONING: Path A (execute now) was 45-60 min focused with nameserver flip + DNS propagation watch + tunnel setup. Path B splits into prep (runbook + DNS discovery, done session 106) and execute (account + Email Routing + cut-over + tunnel, separate 45-60 min session). Lower risk of half-finished state if interrupted. Runbook at references/cloudflare-migration-runbook.md. | CONTEXT: Session 106

[2026-04-12] DECISION: Cloudflare Email Routing over MX-mirroring | REASONING: Namecheap Private Email Forwarding is documented as tied to Namecheap nameservers. Mirroring the eforward MX records onto Cloudflare would break forwarding because Namecheap's backend expects its own DNS to be authoritative. Cloudflare Email Routing is free, native, and survives the cutover cleanly. | CONTEXT: Session 106 DNS discovery showed MX actively routing ras@duberymnl.com despite RA thinking "only for verification"

[2026-04-12] DECISION: CRM cleanup tool uses token.json OAuth2, not ADC | REASONING: First attempt with google.auth.default() returned 403 insufficient scopes because ADC on RA's Windows PC was set up without the spreadsheets scope. Re-running gcloud auth application-default login --scopes would change global ADC and risk affecting Vertex AI + Veo tools. token.json already has 5 scopes including sheets, scoped to the user account, no side effects. | CONTEXT: Session 106 cleanup_crm_test_data.py auth fix

---

[2026-04-11] DECISION: Delete Cloud Run duberymnl-chatbot service entirely instead of scaling to zero | REASONING: Cloud Run does not allow max-instances=0. Delete is the only complete shutdown. Reversible via `bash cloud-run/deploy.sh` from source. Docker image stays in Artifact Registry. | CONTEXT: Session 101, stopping ~$50/mo credit burn during chatbot refactor outage

[2026-04-11] DECISION: Pivot DuberyMNL chatbot from Cloud Run to local Flask + Cloudflare Tunnel
Context: Cloud Run was burning $50/mo of GCP free trial credits. Oracle Cloud signup rejected (PH fraud detection). Chatbot also had 6 production bugs from session 98 that needed a refactor.
Alternatives: Wait for Oracle retry, pay Hetzner €3.29/mo, stay on Cloud Run with Option A throttle (~$7-8/mo)
Why: Free forever, home PC already runs 24/7 for Rasclaw + VSCode tunnel so uptime baseline is acceptable for ~15 msgs/day pre-revenue volume. No cloud signup friction. Migration to Hetzner/Oracle later is trivial (same Docker image).
Consequences: Chatbot depends on home PC uptime. PC sleep/reboot = bot down. Needs auto-start script + uptimerobot monitoring + eventual Cloudflare Worker fallback for PC-offline grace. Cloud Run service can be recreated instantly if needed.

[2026-04-11] DECISION: Delete comment_responder.py + comment_templates.py entirely | REASONING: Daemon-thread pattern is known broken on Cloud Run (session 97). Was contributing to Jonathan flooding bug. Comment-to-DM funnel is a backlog item and will need a ground-up rewrite anyway. Zero runtime value right now. | CONTEXT: Session 101 chatbot refactor

[2026-04-11] DECISION: Chatbot shorthand "Hm" = "how much" must be in system prompt | REASONING: Gemini doesn't know Filipino customer shorthand natively. "Hm" is the most common price shorthand RA sees from real customers. Saved to reference_ph_customer_shorthand.md for future expansion. | CONTEXT: Session 101, RA corrected my initial assumption that "Hm" was a confused noise

[2026-04-11] DECISION: First-message customer service behavior is a rule, not a hardcoded reply | REASONING: Real CS agents always open with warm greeting + name (if known) + thank for interest + THEN answer. Gemini is told to apply this behavior when conversation history is empty. Dynamic context injected per call tells it first_contact + customer_name state. Not a canned spiel. | CONTEXT: Session 101, RA feedback

[2026-04-11] DECISION: "Describe the product, not the image scene" rule added to IMAGE RULES | REASONING: Gemini was hallucinating scene content ("on someone at a cafe") because it only sees image key names, not contents. Fix: explicit rule to describe PRODUCT attributes only (frame color, lens, material). | CONTEXT: Session 101, bug spotted during /chat-test

[2026-04-11] DECISION: Strict "2 per model" image bank was over-correction -- plan to expand to ~35-40 with captions
Context: Shrank 48 → 21 in the refactor. RA flagged during testing that real customers need feedback/proof/on-face/lifestyle shots we no longer have.
Alternatives: Keep 21 lean, go back to 48 raw, target 35-40 with metadata
Why: Customers ask "pwede makita review?", "how does it look worn?", "legit ba to?" — need variety, but each image should come with a short caption so Gemini knows what it is (avoids scene hallucination from earlier bug). Lazy loading means no OOM risk.
Consequences: Image bank expansion is the highest-priority next-session task. Do NOT wire Meta webhook back to tunnel until this is done.

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

[2026-04-08] DECISION: FFmpeg installed via winget (Gyan.FFmpeg), not manual download | REASONING: winget manages updates, adds to PATH automatically, cleaner than manual bin folder | CONTEXT: Session 91, video-to-website skill test

[2026-04-08] DECISION: generate_videos.py supports --image, --last-frame, --ref-image, --negative-prompt, --seed, --duration | REASONING: start+end frame interpolation (last_frame) was the key discovery -- enables controlled product animations. Negative prompt reduces hallucination. Duration 4/6/8s only for image-to-video. | CONTEXT: Session 91

[2026-04-08] DECISION: Veo prompts must be motion-only when using image param | REASONING: Google docs say "prompt for motion only" -- re-describing objects in the image confuses the model and causes hallucination (pieces disappearing, multiplying). 5 iterations to learn this. | CONTEXT: Session 91, ~$8 spent on iterations

[2026-04-08] DECISION: /video-to-website skill upgraded from 7 to 13 animation types + brand analysis + AI video gen | REASONING: Competitive analysis against Jay E (30+ modules) and Nate Herk showed gaps. Added: text-scramble, parallax-layers, color-shift, split-reveal, typewriter, horizontal-scroll, SVG draw, velocity effects, sticky progress, before/after slider. Brand analysis step extracts design tokens from client website. | CONTEXT: Session 91

[2026-04-08] DECISION: Dark slate stone texture as standard product photography background | REASONING: White backgrounds look sterile. Dark slate gives studio feel, lighting cues for reflections/shadows. Tested on Rasta Red, regenerated all 11 card shots. | CONTEXT: Session 91

[2026-04-10] DECISION: KNOWLEDGE_BASE.md markdown as editable source of truth for chatbot knowledge
Context: RA couldn't easily edit knowledge_base.py (Python dicts). Needed a single document he could review + edit.
Alternatives: Admin UI, Google Doc, direct Python edits
Why: Markdown is easiest to edit in VSCode, versioned with git, round-trips cleanly to Python. Human-readable for review, machine-parseable on sync.
Consequences: Knowledge updates are a 2-step process (edit markdown, sync to Python, redeploy). Future: auto-sync via CI.

[2026-04-10] DECISION: Chatbot image bank split -- Vercel for hero shots, Google Drive lh3 CDN for 7 other categories | REASONING: Hero shots already served from Vercel and working reliably with Messenger. Other 37 images had no Vercel hosting. Drive lh3.googleusercontent.com/d/{id} is free and works as direct CDN. Avoided breaking what works. | CONTEXT: Session 98

[2026-04-10] DECISION: Pre-upload all 48 chatbot images to Meta at startup for reusable attachment IDs | REASONING: First-send via URL had 2-3s loading circle on user's phone (especially 1.4MB PNGs). Pre-upload eliminates fetch latency. Adds ~30-60s to Cloud Run boot but min-instances=1 means it only runs once per deploy. | CONTEXT: Session 98

[2026-04-10] DECISION: Multi-part Messenger replies via reply_parts array, not \n line breaks
Context: RA wanted the bot to split long replies into multiple messages for readability.
Alternatives: \n line breaks in single message, new endpoint per part
Why: Multiple Messenger bubbles look more natural than one long message with line breaks. Array lets Gemini decide the split points semantically. Webhook loops through and sends each with typing indicator between.
Consequences: Webhook send logic is longer but each bubble can have natural typing delay.

[2026-04-10] DECISION: Chatbot handoff behavior -- flag + silence, no email to RA
Context: Original handoff sent email to RA and let bot continue. RA said "just flag it and dont respond."
Why: Email notifications are noise. RA monitors /conversations dashboard directly. Bot silence on flagged conversations prevents it from making things worse.
Consequences: handoff.py stripped down, no SMTP code. Flagged conversations visible only in admin dashboard. RA must actively check.

[2026-04-10] DECISION: Prompt injection defense -- 3 layers (input scan, prompt hardening, output scan) | REASONING: Chatbot had no defenses. Added security.py with 40+ injection keywords, SECURITY RULES at top of system prompt, output leak detection patterns. Triggered inputs silently flag + silence bot (same as handoff). | CONTEXT: Session 98

[2026-04-10] DECISION: CRM v1 in Google Sheets, Supabase later as portfolio piece
Context: RA wanted customer data tracking for the chatbot. Asked if should be Sheets or more sophisticated.
Alternatives: Sheets now, Supabase now, Firestore
Why: Sheets is visible, editable, zero setup. Sufficient for v1. Supabase comes later as a portfolio piece showing real CRM with Postgres + dashboard. Same schema maps 1:1.
Consequences: CRM sync uses Sheets API inline. Migration path to Supabase is clean (same columns).

[2026-04-10] DECISION: Conversation history persisted to Conversations tab, loaded on cold-start | REASONING: Cloud Run in-memory store wipes on restart. Customer returning after a deploy had no context. Adding message sync + cold-start load makes conversations persistent across restarts. | CONTEXT: Session 98

[2026-04-10] DECISION: Unified content directory + Karpathy REFERENCES.md pattern | REASONING: Scattered output/images/, output/ugc/, and absolute Windows paths in skills caused churn. Canonical contents/{new,ready,failed,assets}/ structure, old files moved to archives/, tool scripts rewired, brand/UGC skills got lightweight I/O manifests (reads/writes/depends-on/referenced-by) per Karpathy wiki pattern. brand-bold also got WF2 fidelity rules port (R2/R3/R4). | CONTEXT: Recovered from session that crashed mid-refactor before chatbot pivot. brand-callout and brand-collection still need WF2 fidelity port — parked pending QA bandwidth.

[2026-04-11] DECISION: Content storage is 3 tiers, not 2 | REASONING: Earlier rule was "git for code, Drive for everything else" — but that would back up 87MB archives (redundant with git history) and 58MB contents/failed (rejected trash) to Drive, wasting quota. Refined: tier 1 git for code + runtime-deps, tier 2 Drive for valuable content only (contents/new, contents/ready, supplier-images), tier 3 local-only for trash + redundant. | CONTEXT: Session 102, RA caught me uploading archives first, then failed second. See feedback_content_storage_rule.md.

[2026-04-11] DECISION: Drive content sync wired into /closeout step 5 parallel batch | REASONING: sync_folder.py existed as a tool but no workflow invoked it. Closeout now runs sync for contents/new and contents/ready in parallel with git pushes + secret backup. Idempotent (skip-exists), adds 10-30s wall time, fails independently. Tonight's closeout is the first run. | CONTEXT: Session 102, edit in ~/.claude/commands/closeout.md

[2026-04-11] DECISION: IPv4-only getaddrinfo monkey-patch for Python HTTP to Google APIs on Windows | REASONING: Python HTTP calls to googleapis.com were ~60s each because socket.getaddrinfo returned IPv6 first, home ISP doesn't route IPv6, TCP waited ~60s before IPv4 fallback. Monkey-patch filters IPv6 from getaddrinfo results at module load time. 30x speedup (60s → 1.5s). Process-wide, harmless in cloud environments. | CONTEXT: Session 102, discovered during Drive sync tool development. Corrects earlier httplib2 misdiagnosis. Reference: tools/drive/sync_folder.py, cloud-run/conversation_engine.py.

[2026-04-11] DECISION: archives/ stays local-only, not synced to Drive | REASONING: Archives are moved-aside historical files from the pre-refactor output/images/ directory. Git history (pre-fc3bddf) already has every file that was in output/images/, so Drive backup is literal duplicate storage. The archives/ folder is just a local safety net during transition. | CONTEXT: Session 102, RA's call after I'd queued archives/ for sync.

[2026-04-11] DECISION: contents/failed/ also stays local-only | REASONING: Rejected generated content is disposable trash. Backing up failures wastes Drive quota. After RA caught the mistake, I cleaned up the 58MB contents/failed/ from Drive and refined the storage rule to exclude it. | CONTEXT: Session 102, built tools/drive/delete_folder.py as the cleanup mechanism.
