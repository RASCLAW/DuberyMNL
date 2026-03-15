# DuberyMNL Project Log

Running log of progress across all workflows. Updated at each session closeout.

---

## Pipeline Overview
```
WF1 Caption Gen → Review → WF2 Image Gen → WF3a Organic FB Post
                                          → WF3b Meta Ads (parallel)
```

---

## WF1 — Caption Generation
**Status: COMPLETE**
- 15 captions/batch, 7-8 vibes, 1-2 per vibe
- Bundle quota: 3, elevated tone: 2-3
- Output: Google Sheet (captions tab)

## Caption Review Server
**Status: COMPLETE — CAPTION REVIEW DONE. UPGRADES PLANNED.**
- Flask app, runs locally via ngrok tunnel
- Star ratings, notes, product recommendations (cascading dropdowns)
- Rejected rows auto-move to rejected_captions tab
- Relaunch: `bash tools/captions/start_review.sh`
- Caption review complete (batch reviewed and processed)
- Planned upgrades (not yet built):
  - Sheet tabs: WF1 writes to `pending`, review moves approved to `captions`, feedback saved to `feedback`
  - Two input boxes: comment (→ WF2 image brief) + feedback (→ next WF1 batch)
  - Overlay tick boxes: Header, Header 2, Price, Accessories (PRODUCT only), Bubble
  - Feedback is batch-level (shapes next WF1 run, not per-caption regeneration)

## WF2 — Image Generation
**Status: SKILL REBUILT + ARCHITECTURE LOCKED**

### Session 2026-03-15 — Skill rebuild + data architecture
- dubery-prompt-writer rebuilt from git original (d836b34) as clean base
- SKILL_maybe.md = parked over-engineered version (kept for reference)
- Improvements grafted onto original:
  - Step 1 rewritten: 5 steps, angle inherited from WF1 (not re-derived), AIDA map preserved
  - Product primacy rule, 4:5 format rule, bottom-right clear zone added
  - Angle inheritance table: maps 6 angles to visual energy
  - 60/40 batch target, PERSON rule tightened (TYPE A only when human experience is undeniable hook)
  - COD + CTA as auto-always overlays
  - Auto-conditional: deal badge (2+ products), series label (same family)
  - Checkbox-driven overlays: headline, price, bubble, accessories — read from overlays field in captions.json
  - Language rule + headline rule added
- dubery-prompt-parser skill created — converts NB2 prompts to structured JSON
- Data architecture locked: captions.json = primary store for full pipeline; Sheets written only at WF3
- WF1→WF2 handoff fixed: angle, hook_type, creative_hypothesis now survive to WF2 (were previously dropped)
- Workflow docs updated: caption_generation.md + image_generation.md now reference captions.json
- Overlays: review_server.py already has checkbox UI (headline, price, bubble, accessories) — confirmed working

**Previous status:**
- Architecture confirmed: WF2a picks caption (5-star pool → random) → composes NB2 prompt → saves to col K → Status=PROMPT_READY
- WF2b reads PROMPT_READY rows → generates image → writes Image_URL col L + Image_Status=DONE col M
- workflows/image_generation.md updated to reflect final architecture
- Prompt generation tested on captions: 20260309-001, 20260309-015, 20260309-016, 20260309-006
- Opus confirmed as WF2a model (richer scene detail, better lighting, more cinematic vs Sonnet)
- Skill rules updated (cumulative):
  - Portrait format: 4:5 verbatim at end of SCENE
  - Product bubble: 3/4+ body shot → freshly rendered close-up beside ₱699/POLARIZED; no white bg, no reference photo paste; Dubery logo must be legible inside bubble
  - Language: English overlays primary, Taglish ok, pure Tagalog rarely
  - Headline: independent billboard copy, max 5 words, NOT a caption restatement
  - Model tag: [MODEL: SONNET] or [MODEL: OPUS] prepended to every prompt
  - Safe zone: bottom 5% clear of all overlays (kie.ai watermark mitigation)
  - Product primacy: scene exists to serve product; sparse scene = NB2 focuses on product
  - Batch composition: 60% PRODUCT / 40% PERSON
- Dual-model workflow confirmed: both Sonnet + Opus run per caption; RA picks winner in Gemini
- Sheet structure updated: K=Prompt_Sonnet, N=Prompt_Opus (both saved per caption)
- Model scores: Opus 3 — Sonnet 1 — Tie 1. Opus consistently wins on scene richness and prop storytelling.
- Skill rule added: Bottom bar (replaces safe zone rule). Full-width dark strip flush at bottom, all overlays sit above it. Resolves kie.ai watermark overlap.
- Skill rule added: Explicit approval required before editing any skill file.
- Captions with PROMPT_READY: 006 (Sonnet), 008 (Opus), 010 (Opus), 014 (Tie), 017 (Opus)
- Next: continue batch prompts for remaining APPROVED captions, then sheet restructure (remove Generated_At + Hashtags cols)

## Landing Page — dubery-landing/
**Status: BUILT — READY FOR REAL TRAFFIC TESTING**

### Session 2026-03-15 — Initial build
- Mobile-first direct-response landing page for Facebook ads
- Vanilla HTML/CSS/JS, no frameworks — `dubery-landing/` folder in project root
- 7 sections: Hero → Benefits → Product Showcase → Offer Cards → Delivery → Final CTA → Order Modal
- Dark theme: `#111111` bg, `#ff6a00` accent, Poppins + Inter typography
- Order modal: slides up on mobile, centered on desktop
- Dynamic product picker: variant dropdown + thumbnail preview + qty stepper
- Live order summary + form validation + confirmation message on submit
- All 10 product variants mapped with real PNG images from Downloads
- Hero: dubery_5.jpg ("Stop Squinting" lifestyle shot)
- Showcase: dubery_14.jpg (multi-variant bundle flat lay)
- Assets: `dubery-landing/assets/` — all PNGs + hero.jpg + bundle.jpg

**Next steps:**
- Add Dubery logo to hero or nav area
- Connect form to Google Sheets or email via a backend/n8n trigger
- A/B test hero headline variants

---

## WF3a — Organic Facebook Post
**Status: NOT STARTED**
- Tool: tools/meta/post_to_page.py (to be built)
- Inputs: approved caption + generated image
- Requires: pages_manage_posts permission (pending Meta app approval)

## WF3b — Meta Ads
**Status: NOT STARTED**
- Parallel to WF3a
- Uses same caption + image assets
- Requires: confirmed ad account + campaign setup

---

## Session Log

### 2026-03-15 (Session 15) — Drive consolidation + pipeline housekeeping

**What was built:**
- `tools/status.py` — CLI pipeline snapshot (`python tools/status.py`), shows all status counts, has_image, has_prompt, unmapped files
- `tools/image_gen/image_review_server.py` — reject now physically moves image to `output/images/rejected/`
- `dubery-caption-gen/SKILL.md` — WF1 feedback loop added (step 0: reads rejected_captions.json before generating, avoids repeated vibe/angle combos, uses notes as negative creative direction)
- `.claude/skills/dubery-prompt-writer/overlay-formula.md` — 8 design rules reverse-engineered from 8 approved ads (badge color = lens accent, shape = concept energy, 6 POLARIZED treatments, delivery zone styles, headline typography, logo placement)
- `dubery-prompt-writer/SKILL.md` — overlay section rebuilt to reference overlay-formula.md; pills are the correct default for lifestyle shots (old rule said "never pills" — wrong)

**Pipeline changes:**
- Gemini batch (#23-#32) catalogued and added to pipeline.json with full metadata
- 6 legacy images (#33-#38) reverse-engineered from visual content and added
- Caption #26 deleted (duplicate of #12 — same image, same vibe)
- All 35 entries synced to Notion + Sheet

**Drive cleanup:**
- All 35 images consolidated into single folder: `My Drive → DuberyMNL → Generated Images`
- All image URLs normalized to thumbnail format (`drive.google.com/thumbnail?id=...&sz=w1000`)
- 24 orphan/duplicate files deleted from Drive (2 duplicates + 12 unmapped PNGs + 10 legacy dated JPGs)
- 6 Sample Content files moved to `My Drive → DuberyMNL → Sample Content`
- OAuth token re-authorized with Drive + Sheets scopes (was Sheets-only, caused upload failures)

**Milestones:**
- Pipeline fully in sync across all 4 locations: local files + Drive + Notion + Google Sheet
- 34 IMAGE_APPROVED, 1 IMAGE_REJECTED (#2), 35 total tracked
- Drive folder is clean and organized for the first time

**Struggles:**
- token.json only had Sheets scope — Drive uploads failed with 403 until re-auth
- Re-auth requires browser interaction from WSL (can't auto-open browser) — had to manually copy URL
- Accidentally deleted 6 images RA wanted to keep — restored from Drive trash manually
- "The user" vs "RA" — noted and saved to memory

**Next:**
- WF3a: post_to_page.py — blocked on Meta `pages_manage_posts` permission
- IMAGE_REJECTED #2 — needs WF2a retry with rejection feedback
- 7 entries still missing local image files (dubery_1, 8, 9, 10, 11, 12 stored as Gemini PNGs on Drive, not renamed locally)

---

### 2026-03-10 (Session 1 -- from work via VSCode tunnel)
- EA second brain initialized at /home/ra/
- facts.md created, auto-loads via CLAUDE.md
- FIGGY backlog cleaned, principles + self-improvement loop adapted
- Journal system created at journal/2026/03.md
- Decision log upgraded to two-tier format (one-liner + ADR)
- PROJECT_LOG.md created (this file)
- Session closeout + trigger words added to EA CLAUDE.md
- Resume pulled from Drive -- needs AI-focused rewrite (parked until DuberyMNL done)
- Brand guidelines: none exist yet -- to be defined before WF2 scales up
- No public web presence for RA yet -- LinkedIn + GitHub needed post-DuberyMNL

### 2026-03-13 (Session 4)
- Caption review confirmed complete (was pending last session)
- Locked sheet tab architecture: pending / captions / rejected_captions / feedback
- Locked WF2a/WF2b split logic:
  - WF2a picks caption (5-star pool random, fallback 4-star) → composes prompt → Status=PROMPT_READY
  - WF2b processes PROMPT_READY → generates image → Image_Status=DONE
- Added Image_Status column (col M) to captions sheet structure
- Updated workflows/image_generation.md to reflect final architecture
- Tested WF2a prompt generation on 3 captions with Opus model -- all strong output
- Skill updates to dubery-prompt-writer:
  - Portrait format rule added (4:5, verbatim in SCENE)
  - Product bubble rule: full/3/4 body shot → floating bubble beside ₱699 or POLARIZED label
  - Language rule: English overlays primary, Taglish allowed, Tagalog rarely
  - Headline rule: independent billboard copy, NOT caption restatement, max 5 words
- Next: regenerate 20260309-015 with updated rules → save prompts to sheet → proceed to WF2b

### 2026-03-12 (Session 3 -- from work, day shift)
- Read both n8n workflows (Caption Generator + Image Generator) for full context
- Confirmed prompt format: labeled sections plain text (not NB2 JSON schema)
- Confirmed reference image mechanism: `image_input` Drive URLs passed to kie.ai API directly
- No Pillow overlay needed -- NB2 handles scene + all text + product via reference image
- Created dubery-caption-gen skill (WF1 CCO brain, 182 lines)
- Created dubery-prompt-writer skill (WF2 prompt composer, 233 lines)
- Both skills audited with skill-builder: frontmatter fixed, disable-model-invocation set
- DuberyMNL Content sheet (n8n) ID: 1OwWHwlhHfFgMMokMS3GGtH1fHptahbg2OscB07c8bkk (reference only)
- n8n workflows scrapped -- going full agentic (Claude Code as orchestrator)

### 2026-03-11 (Session 2 -- from work, night shift ~midnight)
- No DuberyMNL build work -- side session focused on EA personal tooling
- Discovered Google Workspace CLI (gws) v0.9.1 -- official Google tool, just released
- Installed gws CLI on home PC (`npm install -g @googleworkspace/cli`)
- Configured credentials.json (~/.config/gws/client_secret.json)
- Auth attempted -- blocked by OAuth localhost redirect not working via VSCode tunnel
- Parked: run `gws auth login` locally when home tonight
- Once authed: gws can access Gmail + Drive + Calendar + Docs from terminal (I operate it as EA)

### 2026-03-15 (Session 14) — File consolidation + Google Sheet

Local file consolidation:
- captions.json + pending_post.json merged into single pipeline.json (20 active captions)
- rejected_captions.json retained as discard pile
- All 6 tools updated: generate_kie.py, review_server.py, image_review_server.py, start_review.sh, start_image_review.sh, sync_pipeline.py
- image_review_server.py: approve now updates status in pipeline.json (no more move to pending_post); reject moves to rejected_captions.json

Google Sheet:
- New sheet created: "DuberyMNL Pipeline" (ID: 1LVshSQP5Ob9RNqt35PoSjbUuAiu9dneyHHhUiUZKYrg)
- 16 columns mirroring Notion: Caption ID, Status, Headline, Caption Text, Vibe, Angle, Visual Anchor, Rating, Image URL, Image Status, Has Image, Has Prompt, Image Feedback, Notes, Prompt, Source
- sync_pipeline.py now writes to both Notion + Sheet on every run
- Sheet is overwritten fresh each sync (full refresh)

### 2026-03-15 (Session 13) — Pipeline cleanup + Notion finalized

Pipeline cleanup:
- #21 (Class Dismissed / Classic Blue) added to pending_post.json — sourced from n8n image_log tab (dubery-2026-03-08-114349.jpg), uploaded to Drive
- #22 (Pure Value Truepa / Rasta Red + Brown) added to pending_post.json — sourced from n8n image_log row 5
- #13 and #15 (REJECTED, no images) deleted from Notion and removed from rejected_captions.json — will not re-sync
- #2 set to IMAGE_REJECTED (product fidelity failure, confirmed by RA)
- All remaining 20 active captions set to IMAGE_APPROVED
- sync_pipeline.py updated: inline `headline` field used as fallback when no prompt file exists

Headlines filled for pending_post.json entries (#16-22):
- #16 MAY PLANO KA SA BUHAY. | #17 DALAWANG PAIRS. ISANG DEAL. | #18 CONTENT KA NA, IDOL.
- #19 BAHALA NA SILA SA AKIN. | #20 SHADES LANG ANG TIYAK. | #21 CLASS DISMISSED. TIME TO FLEX. | #22 PURE VALUE, TRUEPA!

Notion state (22 total, 13 + 15 archived):
- 20 IMAGE_APPROVED (ready for WF3)
- 1 IMAGE_REJECTED (#2)
- 2 archived (#13, #15 — no image, deleted from view)

Creative insight saved to memory:
- Overlay accent color follows product lens/frame color
- Price (₱699/₱1,200) is a visual design element, not just a label
- Favorites analysis: RA prefers captions with specific Metro Manila moments, felt pain points, natural Filipino voice

Next: WF3a — post_to_page.py (blocked on Meta pages_manage_posts permission)

### 2026-03-15 (Session 12) — Notion dashboard upgrades + image mapping

Notion improvements:
- Image URL property changed from url → Files & Media type (enables thumbnails)
- Page cover set per caption row via sync_pipeline.py (enables Gallery view card previews)
- Headline property added — extracted from overlays.headline.text in _prompt_structured.json
- Gallery view now shows image thumbnails as card covers (Drive thumbnail URL format)
- Sheets batch (20260309) imported: 5 image-approved captions added as #16-20 to pending_post.json
- All 20 captions synced to Notion (0 errors)

Image mapping — matched orphaned output/images files to captions by headline:
- Gemini_Generated_Image_rlomi4rlomi4rlom.png → #1 (Cut the Glare)
- image_342ca09.png → #8 (DM. Order. Delivered.)
- image_dd7344d1.png → #9 (Delivered Before Lunch)
- Gemini_Generated_Image_z5l723z5l723z5l7.png → #12 (The Fit Just Hit)
- Gemini_Generated_Image_ujds2nujds2nujds.png → #11 (Stay Classy)
- Gemini_Generated_Image_4v6tki4v6tki4v6t.png → #10 (Delivered Today)
- All uploaded to Drive, image_url + status=DONE set in captions.json

Still unmapped (5 files, dated 2026-03-07/08):
- dubery-2026-03-07-071410.jpg
- dubery-2026-03-07-071958.jpg
- dubery-2026-03-07-073303.jpg
- dubery-2026-03-07-085050.jpg
- dubery-2026-03-08-114349.jpg

Captions still at PROMPT_READY with images (need status fix + image review):
- #4 Palenke / Market Day
- #5 Walking the Dog
- #7 Lifestyle / Pinoy Culture
- #14 Content Creator Setup

Next: finish image mapping → fix #4 #5 #7 #14 status → run image review on all DONE captions

---

### 2026-03-15 (Session 11) — Pipeline hardening + Notion dashboard

**Pipeline audit completed — 12 gaps identified across 3 sprints**

Sprint 1 (pipeline-critical fixes):
- generate_kie.py: now auto-updates captions.json on success (DONE + image_url) and failure (IMAGE_FAILED)
- run_batch.sh: per-job logs (.tmp/generate_[id].log), exit codes tracked, summary at end
- captions.json: backup written to .json.bak before every write (all 3 servers)
- Cron deactivated (was a test, hardcoded to dead IDs)

Sprint 2 (close the loops):
- run_batch.sh: auto-launches start_image_review.sh when all jobs succeed
- review_server.py: REJECTED captions move to rejected_captions.json on submit
- image_review_server.py: IMAGE_REJECTED → rejected_captions.json, IMAGE_APPROVED → pending_post.json
- generate_kie.py: Drive upload after save, URL saved back to captions.json
- 7 existing images (#2-7, #14) uploaded to Drive, URLs patched in captions.json

Notion dashboard:
- Notion MCP connected (@notionhq/notion-mcp-server in ~/.claude.json)
- NOTION_TOKEN + NOTION_DATABASE_ID added to .env
- tools/notion/sync_pipeline.py: reads all 3 JSON files, upserts to Notion with 14 properties
- All 15 captions synced with prompt text + Drive image URLs

Data architecture finalized:
- captions.json = active pipeline (PENDING → APPROVED → PROMPT_READY → DONE)
- rejected_captions.json = all rejects (caption + image level) with feedback
- pending_post.json = IMAGE_APPROVED queue for WF3 FB post

### 2026-03-15 (Session 10)
- Built WF3 image review server: tools/image_gen/image_review_server.py (Flask, port 5001)
- Built tools/image_gen/start_image_review.sh — same pattern as caption review (ngrok + email)
- Image review UI: card per image, 4:5 display, caption/vibe/angle/anchor/stars, feedback textarea
- Actions: Approve (IMAGE_APPROVED) + Reject (IMAGE_REJECTED + image_feedback) + Skip (stays DONE)
- Fixed cron: added `cd /home/ra/projects/DuberyMNL &&` prefix (was failing due to wrong working dir)
- Generated images #2, #3, #6 (run_batch.sh) — all saved to output/images/
- Updated statuses manually: #2/#3/#6 → DONE after generation
- Image review results: #3 APPROVED, #6 APPROVED, #2 REJECTED (product fidelity 0%)
- Moved all Mar 15 images from Windows Downloads/approved/ → output/images/
- output/images/ established as single destination for all generated images (run_batch.sh updated)
- Next: update captions #4 #5 #7 #14 to DONE → run image review on them

### 2026-03-15 (Session 9)
- WF2b pipeline unblocked: generate_kie.py fixed (.env path + KIE_AI_API_KEY key name)
- run_batch.sh created: tools/image_gen/run_batch.sh — runs multiple captions in parallel
- Cron scheduled: 9:40am daily, runs #2 #3 #6 — log at /tmp/dubery_batch.log
- Confirmed parallel WF2a+WF2b flow: #5 (Walking the Dog), #14 (Content Creator), #4 (Palengke), #7 (Sala table) — all generated and saved to Downloads
- SKILL.md updated: overlay shape rule — shapes must be named explicitly and earned by concept (no pill default)
- Badge shape feedback saved to memory (confirmed across multiple images)
- All 13 approved captions now PROMPT_READY
- WF2b images generated: #5, #14, #4, #7 (4 new) + #1, #9, #12 confirmed from Session 8
- Scheduled for 9:40am: #2 (Outback Series / outdoor ridge), #3 (Bandits Camo / motorbike helmet), #6 (Rasta Series / commuter bundle)
- Pipeline architecture confirmed: cron runs scripts directly, no Claude approval prompts needed at execution layer
- Next: image review UI (approve to post) + WF3 organic FB post

### 2026-03-15 (Session 8)
- Generated and passed prompts for captions #12, #9, #1 — all tested in NB2, all passed
  - #12: Mirror Selfie / Glow Up / Outback Blue — bedroom, pills, blue-grey badge treatment
  - #9: Gen Z Hangout / Antipolo inihaw / Outback Black — stamped/block badge treatment, grill smoke tones
  - #1: Commuter / EDSA footbridge / Outback Red — sharp rectangular badges, red lens reflection in bubble
- Saved 4 passed prompts as reference (incl. #8 from Session 7)
- Key learning: overlay badge shapes are per-concept, not locked to pills — derive shape from scene energy
- skill_original.md locked as main SKILL.md — SKILL_overengineered.md archived
- Feedback saved to memory:
  - Overlay shapes not hardcoded (derive from concept)
  - No [MODEL: SONNET] tag in prompts
  - Always show caption text before generating prompt
- Captions PROMPT_READY: #1, #8, #9, #10, #11, #12 (6 of 13 approved)
- Remaining APPROVED: #2, #3, #4, #5, #6, #7, #14 (7 to go)
- Next: continue batch prompt generation for remaining 7 APPROVED captions

### 2026-03-15 (Session 7)
- Tested caption #11 (barbershop/Status/PERSON) and caption #8 (Lalamove delivery/Convenience/PERSON)
- Discovered root cause of overlay quality regression: over-prescribed rules (compact row, left-half, never-white) were fighting NB2's natural creative output
- Found original skill file (AGENT 1) — the version that produced the reference-quality ads last week
- skill_original.md saved to .claude/skills/dubery-prompt-writer/ as the clean base
- Added to skill_original.md:
  - Bubble rule: circular crop lifted from main ad image, zoom circle effect
  - DUBERY logo note: D icon + wordmark description (red D swoosh, bold italic black wordmark, red outline)
  - Logo Drive URLs: Logo2 (DUBERY) + Logo4 (DUBERY MNL) added for image_input reference
- Caption #8 regenerated using skill_original — cleaner overlay intent, NB2 gets creative freedom
- Next: rebuild SKILL.md using skill_original as base + graft back only confirmed-valuable fixes
  (bottom-right clear zone, overlay zone split, product primacy, lens darkness rule, angle inheritance, COD auto-always)

### 2026-03-15 (Session 6)
- 6 skill fixes applied from caption #10 v2 test (product distortion, scene brevity, headline clarity, COD clustering, no random icons, delivery prominence)
- Brand rule update: same-day/next-day delivery now FREE; ₱1,200 bundle is free shipping — both skills updated
- Overlay zone rule added: revised Product primacy rule + overlay description instruction — overlays now constrained to top and bottom zones only, center = product space
- Caption #10 regenerated (v3) with all fixes — tested in Gemini — CONFIRMED WORKING
- Result: clean professional ad, product fills center unobstructed, overlay hierarchy correct
- Skill approach confirmed: surgical edits to existing rules, never stack new rules on top of old ones
- Next: generate prompts for remaining 11 APPROVED captions using final skill

### 2026-03-14 (Session 5)
- Major architecture shift: dropped Google Sheets as working store → .tmp/captions.json as primary working data
- Google Sheets retained as final archive only (written once after image generated)
- review_server.py fully rewritten: removed all Sheets API code, reads/writes .tmp/captions.json directly
- start_review.sh updated: count + angles now pulled from .tmp/captions.json
- WF1 skill replaced with new angle-based architecture:
  - 15 captions per batch (3 angles x 5)
  - Angle Library: Pain Relief, Identity, Lifestyle, Status/Glow Up, Value/Deal, Convenience/Fast Delivery
  - Hook Type Library with max-3-per-type rule
  - Visual anchor distribution: 60% PRODUCT / 40% PERSON
  - Voice reference file: research/filipino_caption_voice.md (RA-authored, cached)
  - Output: valid JSON only, no markdown
- WF1 first real run: 15 captions generated, 13 approved, 2 rejected (#13, #15 Status/Glow Up)
  - 10 captions rated 5-star
  - 6 captions have detailed image direction notes from RA
- WF2 comparison test started:
  - Two skill versions under evaluation: current (detailed) vs new (simplified, from promptest.txt)
  - Caption #9 selected randomly from 5-star pool for test
  - Both prompts generated and saved to .tmp/captions.json as prompt_current + prompt_new
  - Caption #9: POV/Convenience/Gen Z Hangout/Outback-Black | Scene: inihaw grilling at Antipolo resort
  - Headline chosen: "Delivered Before Lunch."
  - Pending: test both prompts in kie.ai, pick winner → set as prompt field → PROMPT_READY
- Known issue: Bandits - Glossy Black (#11) not in reference image map — nearest match is banditsblack
- banditstortoise still has placeholder Drive ID in new skill
