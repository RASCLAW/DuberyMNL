# DuberyMNL Project Log

Running log of progress across all workflows. Updated at each session closeout.

---

### Session 42 -- Pipeline Audit + Fixes continued (2026-03-19)

**Workflow docs cleanup:**
- Deleted 5 redundant workflow docs (caption_generation, caption_review, image_generation, ugc_generation, ad_publishing)
- Moved meta_setup.md + lead_capture.md to references/
- Removed workflows/ directory entirely -- skills are now the sole operative instructions

**WF1 final fixes (6 items):**
- validate_wf1.py: added emoji count check (1-2), CTA presence check, batch_id consistency check
- SKILL.md: added batch_id + string ID to output JSON example, explicit "minimum 3" bundle quota
- setup_spreadsheet.py: fixed stale 60/40 language ratio to 80/20

**WF2 Opus audit -- 18 findings (2 critical, 4 high, 6 medium, 6 low, 12 verified):**

Fixes applied (14 total):
1. CRITICAL: Fixed 3 wrong product variant file paths (outback-black, rasta-brown, rasta-red) in prompt-writer + prompt-validator skills
2. CRITICAL: Added fcntl locking to image_review_server.py (update_caption + reject_caption)
3. HIGH: generate_kie.py now aborts with IMAGE_FAILED on reference image upload failure (was silently sending local paths to kie.ai)
4. HIGH: run_wf2.py separated gatekeeper (sequential) from image gen (parallel) -- no more 4 concurrent claude --print calls
5. HIGH: Added fcntl locking to promote_rejections() in run_wf2.py
6. MEDIUM: Parser schema product.model (singular) changed to product.models (array) to match validator
7. MEDIUM: generate_kie.py .env path uses PROJECT_DIR instead of fragile relative path
8. MEDIUM: run_post_review.py now validates parser output is valid JSON with product key
9. MEDIUM: Fixed Python 3.12 SyntaxError -- removed broken global statement in image_review_server.py
10. MEDIUM: start_image_review.sh exits 1 (not 0) when no images ready
11. LOW: Parser SKILL.md captions.json reference updated to pipeline.json
12. LOW: Polling timeout increased 60 to 90 attempts (4min to 6min)
13. LOW: Added .bak backup to update_pipeline_status in run_wf2.py
14. LOW: Removed dead courier fields from parser schema

Intentionally skipped (low risk): IMAGE_REJECTED status edge case (#6), Drive folder name vs ID (#10), tuning (#15/#16)

**End-to-end test run:**
- Generated 1 caption (Value / Deal, Palenke / Market Day, Bandits Glossy Black)
- Followed skill rules properly (outdoor setting, all checklist items)
- Gatekeeper: PASS on first attempt
- kie.ai image generated successfully -- product hero, palengke scene, all overlays clean
- Caption 20260319-001: DONE, backed up to Drive

**Next:** WF3 audit

---

### Session 41 — Full Pipeline Audit (Opus) + Fixes (Sonnet) (2026-03-19)

**Opus audited all three workflows (WF1, WF2, WF3).** Found critical bugs, doc drift, missing validators.

**Fixes applied:**
1. `stage_ad.py` string ID bug -- `type=int` → `type=str` (WF3b was completely blocked)
2. Race condition on `pipeline.json` -- added `fcntl.flock` file locking to `generate_kie.py` + `run_wf2.py`
3. `feedback.json` now read before caption gen (WF1 step 0)
4. Approved caption calibration added (pipeline.json rating >= 4, positive signal)
5. `AD_STAGED` status + `--all` batch runner for `stage_ad.py`
6. Campaign/ad set mismatch fixed -- now `LANDING_PAGE_VIEWS` + `SHOP_NOW` CTA → `duberymnl.vercel.app/?id={id}`
7. WF1 output validator built (`validate_wf1.py` -- 8 checks, PASS/WARN/FAIL)
8. `caption_generation.md` rewritten from scratch to match SKILL.md
9. Language ratio standardized to 80/20 English/Tagalog
10. `start_review.sh` variable fixed (ANGLES → VIBES, reads actual vibe field)
11. `batch_id` added to caption generation

**Opus re-audited WF1 after fixes -- all 7 fixes verified PASS.** Minor items remain (emoji/CTA validator checks, setup_spreadsheet.py stale 60/40 ratio).

**Open question:** workflow docs are redundant now that skills exist. RA considering whether to delete or demote them.

**Still pending from priority list:**
- WF2/WF3 doc reconciliation
- WF1 validator: add batch_id, emoji, CTA checks
- `setup_spreadsheet.py` stale brand data (60/40 ratio)
- kie.ai transient failure retry
- Prompt writer/parser output validation

---

### Session 40 — Product Catalog Cleanup + Classic Series Archive (2026-03-19)

**Bandits series renamed:**
- Bandits Camo → Bandits Matte Black
- Bandits Black → Bandits Glossy Black
- Bandits Tortoise added as new variant

**Classic series retired (out of stock):**
- 9 Classic captions (IDs: 18, 20, 21, 25, 27, 29, 30, 36, 38) archived to `.tmp/archived_captions.json`
- Status set to ARCHIVED in pipeline.json and Google Sheet
- Images and Drive URLs preserved for future reuse
- `captions-classic.json` renamed to `captions-classic.archived.json`

**Files updated:**
- 3 skill files: dubery-prompt-writer, dubery-prompt-validator, dubery-ugc-prompt-writer (product tables)
- `tools/captions/review_server.py` (caption review product dropdown)
- `tools/sheets/setup_spreadsheet.py` (sheet metadata)
- `dubery-landing/data/captions.json` regenerated (33 active captions)

**Flagged for future session:**
- Google Drive reorganization (multiple DuberyMNL folders scattered) -- plan pending
- File reorg saved to memory: `project_file_reorg.md`

**Pipeline state:** 42 active captions (down from 51 -- 9 archived)

---

### Session 39 — Validator Feedback Loop + Overlay Separation Discussion (2026-03-19)

**Prompt validator tested live on 020 and 011**
- 020: validator returned REGENERATE (lens color in render_notes, missing supporting_line, wrong delivery format for TYPE A) -- gatekeeper subprocess returned PASS both times (consistency issue noted)
- 011: identified same PF-1/PF-2 violations as 019 -- explicit camo pattern + "dark lens" in render_notes
- 011 prompt manually regenerated with feedback file, re-ran image gen -- new image ~90% fidelity (yellow/gold lens confirmed correct for Bandits Camo; camo pattern on arm correct; minor: pattern visible on inside of arm)

**Validator feedback loop built**
- `.tmp/{id}_validator_feedback.json` -- written on REGENERATE, cleared to `{}` on PASS
- Prompt writer SKILL.md: added Feedback Check section -- reads feedback file before generating, fixes only flagged issues, preserves scene/concept
- `run_wf2.py`: retry loop added -- gatekeeper REGENERATE → write feedback → call prompt writer → re-validate → max 2 attempts → PROMPT_FAILED
- `run_wf2.py`: removed `--dangerously-skip-permissions` from both subprocess calls (gatekeeper + writer)

**Validator upgraded: direct patch approach (Session 39 continued)**
- PF-1/PF-2: changed from REGENERATE to PATCH — validator rewrites `product.render_notes` inline, removes frame/lens descriptions
- PF-5: now catches Drive URLs (not just empty/logo-only) — patches to correct local asset path using `product.models` lookup table
- OC (missing overlays): REGENERATE → PATCH — adds minimal overlay inline
- OD-1 (duplicate overlays): REGENERATE → PATCH — removes weaker duplicate
- LA-1 (missing D icon): REGENERATE → PATCH — adds D icon description
- REGENERATE now only for: missing verbatim instruction, no product reference at all, product clearly not hero
- Test confirmed: validator patched test_validator_011.json — 5 patches applied, 0 REGENERATE, all edits verified

**Open question (not yet resolved):**
- scene.lighting and scene.product_placement still had camo/frame descriptions after patching
- PF-1 currently only targets `product.render_notes` — needs decision whether to extend scope to scene fields

**Known issue: gatekeeper subprocess too lenient**
- Subprocess validator consistently returns PASS for prompts with clear violations (PF-1, PF-2)
- Root cause: `claude --print` subprocess uses different reasoning than main context
- Proposed fix (not yet built): validator edits the prompt file directly (extend PATCH behavior) instead of REGENERATE → feedback → writer loop

**Architecture discussion: separate overlay tool**
- Insight: NB2 splits attention between product fidelity AND overlay rendering -- they compete
- Proposed: NB2 generates clean product photo (no overlays), Pillow composites overlays programmatically
- Tools considered: Pillow (local, free, deterministic), Bannerbear, Canva API
- Decision pending RA direction

**Pipeline state:**
- 011: DONE (regenerated this session, ~90% fidelity)
- 020: DONE (generated this session, product fidelity confirmed good)
- Pending: image review for 011, 020 and remaining DONE captions

---

### Session 38 — Prompt Gatekeeper + Product Fidelity Fixes (2026-03-19)

**base64 upload field name fix in `generate_kie.py`**
- Bug: field was `fileBase64` but API expects `base64Data` → 400 Bad Request on every local file upload
- Fix: corrected field name -- uploads now confirmed working (bandits-camo.png + logo both uploaded to kie.ai CDN)

**Product fidelity root cause identified and fixed**
- Prompt writer was inferring product appearance from the product NAME ("Camo" → camo texture pattern)
- render_notes described "earthy green, tan, brown, dark olive patches" -- specific description overrode reference image
- Fix: added PRODUCT APPEARANCE RULE to SKILL.md -- never describe frame color/texture/pattern/material from name
- render_notes must only describe: position, angle, lighting direction, logo legibility

**Reflection rule overhauled**
- Old REFLECTION RULE told writer to describe specific scene content inside the lens → looked like a fake composite
- New rule: "Do NOT describe specific content inside the lens. Render a natural, physically accurate reflection."
- TYPE D description in SKILL.md also fixed (still had conflicting "sharp and recognizable" language)
- Confirmed working: 019 generated with natural lens reflection -- RA approved

**COLOR LOGIC RULE added to SKILL.md**
- Badge accent must be derived from reference image lens tint, not inferred from product name

**Confirmed baseline: product fidelity 100% + sunglasses as hero = auto-approved standard**
- Position, angle, lighting: always describe in prompts
- Appearance: reference image is the only authority

**Built `dubery-prompt-validator` -- Prompt Gatekeeper**
- New skill: `.claude/skills/dubery-prompt-validator/SKILL.md`
- Runs before every `generate_kie.py` call via `run_wf2.py`
- 7 check categories, 20 checks: product fidelity, hero treatment, color logic, overlay completeness, duplicate overlays, overlay positioning, logo accuracy
- Verdicts: PASS / PATCH (auto-fix) / REGENERATE (skip generation, mark PROMPT_FAILED)
- Integrated into `run_wf2.py`: `run_gatekeeper()` fires in `run_image_gen()` before subprocess call
- Defaults to PASS on validator failure (non-blocking)

**Pipeline state:**
- 019: DONE (multiple re-runs this session -- final image confirmed good, natural reflection, correct product)
- 020: DONE (generated last night, needs re-run with fixes -- next step)
- Gatekeeper not yet tested -- test on 019 (known good) is next step

---

### Session 37 — Image Gen Pipeline Fixes (2026-03-19)

**Root cause: logo URL was breaking kie.ai API**
- Logo lh3 URL (`1kJiHQd81IofqDcDcATfN62nzQDUSC89D`) redirects to Google login -- kie.ai couldn't fetch it, returned null response
- Fix: removed logo from `image_input` in all 4 stuck prompts (016/018/019/020)
- Removed logo URL from `dubery-prompt-writer/SKILL.md` permanently

**kie.ai image upload step added to `generate_kie.py`**
- Root cause of product fidelity issues: `image_input` URLs need to be pre-uploaded to kie.ai's own CDN
- Upload endpoint: `https://kieai.redpandaai.co/api/file-url-upload` (not `api.kie.ai` -- that's 404)
- Base64 upload also supported for local files: `https://kieai.redpandaai.co/api/file-base64-upload`
- generate_kie.py now detects local file paths vs URLs and uploads accordingly before generation

**Switched product reference images to local files**
- All lh3 URLs in SKILL.md replaced with local paths: `dubery-landing/assets/variants/*.png`
- Logo added as local path: `dubery-landing/assets/dubery-logo.png`
- All 4 stuck prompt files updated to use local paths + logo
- Prompt writer will now always append logo to `image_input`

**Natural language vs JSON test**
- Tested 016 with natural language prompt -- better visual composition but product fidelity failed
- JSON structured prompt: better product fidelity (confirmed 100% on 016)
- Decision: keep JSON structured prompts, parser stays in the chain

**Overlay rule fixes in SKILL.md**
- PRICE RULE: 1 product → ₱699 only. 2+ products → bundle ₱699 / 2 PAIRS ₱1,200
- COD RULE: always "COD" only, never "COD ₱0"

**Pipeline state:**
- 016: DONE (generated 3x this session during testing -- image in Drive)
- 018: DONE (generated with upload step working -- 100% product fidelity confirmed)
- 019, 020: PROMPT_READY -- ready to run with local file upload
- Next: run 019 + 020, then image review for all 4, then WF3

---

### Session 36 — Subprocess Fix Confirmed + Full Automation Run (2026-03-19)

**Fix applied:**
- `run_post_review.py`: added `--dangerously-skip-permissions` to both `claude --print` subprocess calls (writer + parser)
- Root cause: `claude --print` subprocess was pausing for tool permission approval with no interactive terminal to receive it; returned exit 0 without writing the file
- Previous fix (`CLAUDECODE` unset) was correct and necessary -- this was an additional blocker

**Subprocess test (--prompts-only --ids 20260318-016):**
- PASSED: writer ran, created `20260318-016_prompt_structured.json`, status updated to PROMPT_READY
- Parser ran, cleaned JSON (removed `model: SONNET`, added `resolution: 1K`)
- Full chain confirmed working

**Product reference URL fix:**
- Root cause of product inaccuracy: `drive.google.com/uc?export=view` URLs don't work with kie.ai (no redirect following)
- Fix: use `lh3.googleusercontent.com/d/{FILE_ID}` format -- direct CDN, no redirect, kie.ai accepts it
- Confirmed working: 20260318-017 regenerated with lh3 URLs → 100% product fidelity
- Updated `dubery-prompt-writer/SKILL.md`: added full product reference table (11 models, lh3 URLs), updated logo URLs
- Writer now automatically passes correct product image_input per `recommended_products` field

**Image gen still failing (016, 018, 019, 020):**
- All 4 return HTTP 200 but API responds with null -- root cause unknown
- 017 passed (lh3 URLs, 2 image_inputs) -- inconsistent behavior
- Added better error logging to generate_kie.py (status code + raw response body)
- Architectural decision pending: skip prompt parser, send natural language directly to kie.ai

**Architecture change planned (next session):**
- Current flow: writer → structured JSON → parser → JSON.dumps() → kie.ai (redundant)
- New flow: writer outputs natural language text → save as .txt → generate_kie.py sends directly
- Removes parser as a failure point, simplifies pipeline
- image_input + api_parameters will be handled via small sidecar config

**Session state:**
- 017: DONE, IMAGE_APPROVED (lh3 URL test passed, 100% product fidelity)
- 016, 018, 019, 020: PROMPT_READY (prompts written, image gen failed, retry pending)
- 42 earlier captions: IMAGE_APPROVED, waiting on WF3
- Next: implement natural language prompt flow, rerun image gen for 016/018/019/020

---

### Session 35 — Post-Review Orchestrators + WF1 Test Batch (2026-03-18)

**Plan revised (binary-swimming-parrot):**
- Changed approach: instead of modifying existing scripts, build NEW orchestrator scripts on top
- Existing manual paths (review_server.py, image_review_server.py, sync_pipeline.py, run_wf2.py) stay untouched

**Built:**
- `tools/pipeline/run_post_review.py` — new orchestrator: detects APPROVED captions without prompt files, runs WF2a (prompt-writer → parser) + WF2b (image gen with 5-min intervals), syncs sheet, starts image review server
- `tools/pipeline/run_post_image_review.py` — new orchestrator: syncs sheet, exports captions.json, gets ngrok URL, sends email with IMAGE_APPROVED count + landing page preview link

**SKILL.md updates:**
- `dubery-caption-gen`: visual anchor bias updated to 70% PRODUCT / 30% PERSON; sequential generation added to WF1 workflow
- `dubery-prompt-writer`: added Execution Order section — write one prompt → save → update status → next caption

**WF1 test batch (5 captions — Lifestyle angle):**
- Generated and appended IDs 20260318-016 through 20260318-020
- All 5 APPROVED with rating 5 by RA
- Started review server automatically after generation (WF1 step 7)

**run_post_review.py bugs found and fixed:**
- `CLAUDECODE` env var blocks nested `claude --print` calls — fixed: unset in subprocess env via `_claude_env()`
- `--allowedTools` flag syntax broke argument parsing — fixed: removed, not needed for `--print` mode

**Pending (next session):**
- Retest `run_post_review.py --prompts-only --ids 20260318-016` to confirm `claude --print` subprocess works
- If confirmed: run full batch (016–020) through WF2a → WF2b
- 5 captions (016–020) are APPROVED in pipeline.json, ready to process

---

### Session 34 — Automation Architecture + Pipeline Plan (2026-03-18)

**Automation audit — WF1 to image review:**
- Confirmed: two intentional human gates remain (caption review + image review)
- Everything between them can be fully automated once plan is built

**Plan approved (`binary-swimming-parrot`):**
- `review_server.py` — write `wf2_queue.json` (session-specific approved IDs) + auto-trigger `run_post_review.py` after submission
- `run_post_review.py` (new) — reads queue → Claude CLI: prompt-writer → parser → image gen (run_wf2.py) → clears queue
- `image_review_server.py` — auto-trigger sheet sync + `export_captions.py` after last image reviewed
- `sync_pipeline.py` — strip Notion sync, sheets-only permanently
- Landing page notification email after export_captions.py runs

**Architecture decisions:**
- WF2 queue file (`.tmp/wf2_queue.json`) solves the "old APPROVED bleed-in" problem — only IDs from latest review session
- Prompt writer + parser both run sequentially, one caption at a time, for quality focus
- Prompt parser is required: writer output format ≠ generate_kie.py expected schema
- Visual anchor bias: 70% PRODUCT / 30% PERSON
- Vibe list updated: Beach Day + Turista (replaced Cat Parent + Toddler/Young Parent)

**Pending (next session — build the plan):**
- Implement all 4 file changes from the approved plan
- Update SKILL.md files (sequential generation + bias changes)
- Test full chain end-to-end

---

### Session 33 — run_wf2.py + Pipeline Fixes (2026-03-18)

**run_wf2.py built (`tools/pipeline/run_wf2.py`):**
- Single command: finds PROMPT_READY/IMAGE_REJECTED captions → parallel image gen → promotes rejections → Drive upload → image review server → email → sheet sync
- Replaces manual run_batch.sh + start_image_review.sh chain
- Flags APPROVED captions without prompts (tells RA to run dubery-prompt-writer first)
- Flags: `--ids`, `--force`, `--no-review`, `--no-sync`

**Bugs fixed:**
- `generate_kie.py` Drive upload subprocess: `python3` → `sys.executable` (fixes dotenv import error in venv)
- IMAGE_REJECTED captions now auto-promoted back to pipeline.json as DONE after successful regen
- `run_wf2.py` post-processes regenerated rejections: removes from rejected_captions.json, inserts into pipeline.json with DONE status

**product_ref backfilled:**
- All 14 new batch captions (20260318-001 to 20260318-015) had empty product_ref
- Backfilled from `{id}_prompt_structured.json` → `product.models`
- Now visible in Google Sheet column I

**Vibe list updated (dubery-caption-gen skill):**
- Removed: Cat Parent, Toddler / Young Parent
- Added: Beach Day, Turista

**Sheet fixes:**
- 20260318-010 Drive URL was blank -- fixed last session, re-synced this session
- 50 rows synced (49 pipeline + 1 rejected = 20260318-008 REJECTED caption)

**Pipeline state at session close:**
- 49 entries in pipeline.json
- 42 IMAGE_APPROVED
- 7 DONE (pending image review -- 6 regenerated rejected + 1 holdover)
- 1 entry in rejected_captions.json (20260318-008, caption-level reject)
- Image review server live: 7 images pending RA review

**Pending:**
- RA to complete image review (7 images)
- Vercel deploy of landing page
- WF3 -- 42 IMAGE_APPROVED ads ready to stage
- stage_ad.py CTA swap to landing page URL after deploy

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

### 2026-03-17 (Session 25) — Landing Page: Ad Mapping, Vercel Deploy, Variant Fixes

**What was done:**
- Audited all 28 ads in `captions.json` against product refs and hero shots
- Removed 6 Classic series ads from `captions.json` (out of stock) → parked in `captions-classic.json`
- Moved `id: 31` (Purple variant) to `captions-classic.json`
- Fixed `id: 24` product_ref: Rasta Red → Outback Red
- Fixed `id: 32` product_ref: Rasta Red (Gold/Amber) → Rasta Red
- Fixed `id: 23` product_ref: Mixed (bundle display) → Rasta Brown, Rasta Red, Outback Green, Bandits Camo (carousel)
- **Deployed landing page to Vercel** → [duberymnl.vercel.app](https://duberymnl.vercel.app)
- Split `Bandits – Green Blue` (single variant) into two: `Bandits – Green` (idx 8) and `Bandits – Blue` (idx 9); Tortoise shifted to idx 10
- Updated VARIANTS array + PRODUCT_IMAGE_MAP variantIdx accordingly
- Built + removed hero swipe navigation (RA decided against it)
- Emailed full Ad ID → Product Ref mapping to sarinasmedia+claude@gmail.com

**Active ads: 22** (captions.json)
**Parked ads: 7** (captions-classic.json — restore when Classic series restocks)

**Pending (deferred to tonight):**
- Add missing picker thumbnails: Outback Red, Outback Blue, Bandits Green, Bandits Blue, Bandits Tortoise (single-angle shots saved in Screenshots + Downloads)
- Restrict Google Maps API key to `duberymnl.vercel.app` domain
- Connect order form to Google Apps Script (RA manual step) → fill `FORM_ENDPOINT` in script.js

### 2026-03-16 (Session 21) — Landing Page UX Polish (Floating FB Button + Card Preview)

**What was built:**
- Floating Facebook widget button (top-left, fixed position, scrolls with page)
  - Facebook blue pill, 70% opacity, restores to full on hover
  - Links to `facebook.com/duberymnl`
  - Label: "Visit our profile"
- Product card image now tappable — opens full image preview overlay (same behavior as variant thumbnails)
  - `cursor: zoom-in` hint on hover
  - Wired to existing `openImgPreview()` — no new overlay code needed

**Files changed:**
- `dubery-landing/index.html` — floating FB button HTML
- `dubery-landing/styles.css` — `.fb-float-btn` styles
- `dubery-landing/script.js` — product card click handler

**Pending (unchanged from last session):**
- Vercel deploy → live URL → restrict Google Maps API key to domain
- Google Apps Script setup (RA manual) → fill `FORM_ENDPOINT` in script.js
- Update stage_ad.py CTA to landing page URL (after Vercel deploy)
- Hero background image fit on mobile
- Update status.py — add "Has ad staged" line

---

### 2026-03-16 (Session 20) — Google Maps Autocomplete on Address Field

**What was built:**
- Google Maps Places Autocomplete on delivery address field
- API: Maps JavaScript API + Places API enabled in Google Cloud Console
- Restricted to Philippines only (`componentRestrictions: { country: 'ph' }`)
- All place types included (streets + establishments like Venice Grand Canal, Wells Fargo, etc.)
- Solid white dropdown (was semi-transparent — `--surface` is `rgba(255,255,255,0.55)`)
- Browser autofill disabled (`autocomplete="nope"` — browsers ignore `"off"`)
- Favicon added: dubery-logo.png shown in browser tab
- Fixed `hero.jpg` 404 → renamed to `hero.png` across all references
- Fixed `initMaps` not found in strict mode → `window.initMaps = function()`
- Stayed on old `google.maps.places.Autocomplete` (new `PlaceAutocompleteElement` triggers popup/redirect — not ready for use)

**Google Cloud setup (RA did manually):**
- API key: AIzaSyBWM01ElyeTUTBoTrlR2TxY7Pu8Po_f-MA
- Enabled: Maps JavaScript API, Places API, Places API (New)
- TODO: Restrict key to Vercel domain after deploy

**Pending:**
- Vercel deploy → live URL → restrict API key to domain
- Google Apps Script setup (RA manual)
- Update stage_ad.py CTA to landing page URL

---

### 2026-03-15 (Session 18) — Landing Page UI Polish (dubery-landing/)

**Hero image:**
- Swapped hero to dubery_32.jpg (portrait 4:5, warm golden sunset)
- Fixed background-position to center 30% for portrait fit
- hero.jpg is default fallback; ?id=N loads assets/ads/dubery_N.jpg dynamically

**Layout change:**
- Moved headline + subheadline out of hero overlay → below hero in .hero-below div
- Logo removed from hero
- Hero is now clean full-bleed image only

**Dynamic accent system (script.js):**
- extractAndApplyAccent(): uses Canvas API to scan hero image pixels, finds most saturated color
- applyTheme(): sets --accent, --accent-hover, --accent-active, --accent-glow CSS variables
- Also sets --surface, --surface-raised, --surface-border with accent hue tints
- Confirmed working: hue=41 sat=88% → accent=#e6a20f for golden sunset image

**Dynamic background system:**
- Added #page-bg fixed div behind all sections
- Background = blurred hero image (blur 32px, brightness 1.1, saturate 0.5) + white overlay
- Switches automatically when ad changes via ?id=
- Creates visual continuity between hero and content sections

**Light theme:**
- Switched from dark (#111) to light (transparent bg, white frosted surfaces)
- Text colors: --text: #111111, --text-muted: #444444
- Feature items now have card treatment: surface bg + border + border-radius + backdrop-filter blur
- .btn-outline updated: accent color border + text (was white/transparent)

**Mobile preview tool:**
- preview.html updated with "Simulate Ad" dropdown — all 20 available ad IDs
- Tests ?id=N URL parameter locally without needing Vercel deploy

**Pending:**
- Vercel deploy → live URL
- Google Apps Script setup (RA manual)
- Update stage_ad.py CTA to landing page URL

---

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

### 2026-03-15 (Session 18) — Comic Strip Format + Kiko Character Bible

**What was built:**

**2 new skills added:**
- `.claude/skills/dubery-infographic-ad/` — DuberyMNL hand-drawn callout bubble infographic format. Design DNA extracted from original Dubery Bandits ad (beach backdrop, granite surface, 3 oval callouts, Rule of Three, sparkle accent). Includes SKILL.md + README.md.
- `.claude/skills/ad-reverse-engineer/` — General-purpose skill for reverse-engineering any ad image into a structured NB2 prompt. 4-layer method: Backdrop / Hero / Graphics / Text. Includes SKILL.md + README.md.

**Ad reverse-engineering:**
- Reverse-engineered SAMPLE CONTENT 1 (Dubery Bandit Camo, comic strip style) — extracted full layer breakdown and design rules
- Identified new content type: Filipino street culture comic strip (wide horizontal, 3-character contrast panel, hand-drawn callouts, speech bubble)

**Comic strip format tested:**
- Concept: Beach barkada, Rasta Red, dreadlock protagonist
- First output: good structure, wrong orientation (16:9), no dreadlocks, too many bubbles
- Refined: 4:5 portrait, one speech bubble only, relaxed tone, Kiko character introduced
- `.tmp/comic_strip_rasta_red.json` — current working prompt for the beach strip

**Kiko character bible created:**
- Protagonist: Kiko, 24, Filipino, short thin dreadlocks (chin length, loose, natural), Dubery Rasta Red, calm half-smile, "hindi nagpapanic" archetype
- Barkada: Dodong (foil, over-reactor) + Ces (practical one)
- Universe: "KIKO" / "Si Kiko at ang Mundo" — Manila is chaotic, Kiko moves through it calm
- Strip formula locked: Setup (everyone suffers) → Contrast (Kiko is fine) → Punchline (one understated line)
- `.tmp/kiko_character_bible.json` — full character specs + prompt rules
- `characters/kiko_reference.png` — approved character portrait from Gemini
- `characters/kiko_description.json` — locked visual description for consistent generation

**Day 0 arc planned:**
- 8-panel origin story: night before swimming trip → discovers DuberyMNL on FB → landing page → order → COD → unboxing → ready
- Doubles as a live customer journey map (discovery, landing page, COD, delivery, unboxing)
- Panel generation priority: Panel 1 first (establishes Kiko's look), then Panel 7 (unboxing), then Panel 2 (scroll — direct FB ad)

**Milestones:**
- Comic strip format proven viable — first test output was strong
- Kiko locked as DuberyMNL's recurring comic protagonist
- 2 new reusable skills in the toolkit

**Next:**
- Generate Day 0 panels starting with Panel 1
- Lock `dubery-comic-strip` as a formal skill once format is fully proven
- Add Kiko reference image as `image_input` in all future comic strip prompts for consistency

---

### 2026-03-17 (Session 24) — Landing Page Major Upgrade + Facebook Page First Post

**What was built:**

**Facebook page (done by RA + assisted by Claude):**
- Cover photo updated (Gemini-generated Dubery MNL image)
- Bio rewritten: "Polarized sunglasses built for Manila. Starting at ₱699 -- same-day delivery, COD."
- Website field: `https://duberymnl.vercel.app`
- Action button: Shop Now → landing page
- First organic post in years: infographic (beach scene, 3 callouts), Taglish quick-facts caption
  - Caption: "Regular vs. polarized. Here's the difference: Glare? Wala na. Eye strain? Finish na. UV rays? Blocked."

**Landing page -- major upgrades:**

Product card:
- All product hero shots added (Outback Black/Blue/Red, Rasta Red/Brown, Bandits Camo/Black/Blue/Green/Tortoise)
- `PRODUCT_IMAGE_MAP` fully updated with all new filenames + `desc` + `variantIdx` fields
- `resolveProductImage` updated to return full entry (was stripping `desc` + `variantIdx`)
- Default hero background: `OUTBACK - BLACK - HERO SHOT.png`
- Default footer logo: `dubery-logo.png` (transparent, blends with black footer)

Multi-product carousel:
- `resolveMultiProducts()` -- detects comma-separated product refs, dedupes by image
- `renderProductCarousel()` -- builds swipeable carousel with dots + tap-to-preview per slide
- `initCarousel()` -- touch swipe + dot nav, updates description on slide change
- `prePopulatePicker()` -- auto-selects featured variants in order modal with qty 1 each
- Description updates per slide (swipe left/right to see each product's desc)
- Carousel triggers only for multi-product captions; single product stays as-is
- Tested on `?id=17` (DALAWANG PAIRS. ISANG DEAL. -- Rasta Red + Rasta Brown)

Proof of purchase strip:
- 6 proof photos added: proof1-6.jpg (COD packages, boxes, LBC counter)
- Rotated proof3, proof4 (then proof4 rotated back), proof5 rotated right
- Order: proof5 → proof3 → proof2 → proof1 → proof4 → proof6
- Section background set to solid `var(--bg)` to fix washed-out opacity issue

Order picker:
- Default thumbnail: `logo new.png` (shown before variant selected)
- `variant-selected` CSS class: switches from `contain` (logo) to `cover` (product) on selection
- Pre-populated from `prePopulatePicker` when ad caption loads

Pricing section:
- Bundle card moved first (was second)
- FREE DELIVERY green stamp added to bundle card
- `pricing-card` gets `align-items: flex-start` so stamp doesn't stretch full width
- `.pricing-card .btn { width: 100% }` keeps ORDER NOW button full width

Footer:
- Background: `#000` (full black)
- Logo: `dubery-logo.png` (transparent bg, 120px, no padding)
- Border removed

Spacing cleanup:
- `.lens-proof` padding: 60px → 24px (leaner)
- `.proof-strip` padding-top: 48px → 16px
- `.pricing.section` padding-top: 16px (override)
- `.final-cta.section` padding-top: 16px (override)

Missing assets fixed:
- `hero.png` (was 404) -- copied from OUTBACK - BLACK - HERO SHOT.png
- `dubery-logo.png` (was 404) -- downloaded from Drive (ID: 1kJiHQd81IofqDcDcATfN62nzQDUSC89D)
- `dubery_17.jpg` -- downloaded from Drive (ID: 1GNw5UVgDz0X_QS0MO7Nb7QwniR9pJEkc)
- Caption #17 added to `data/captions.json`

**Deployed:**
- Git pushed: `ea740ab`
- Vercel: `https://duberymnl.vercel.app` (live, updated)

**Milestones:**
- Facebook page is now active and presentable for the first time in years
- Landing page now has full product hero shots, social proof, working carousel
- All product descriptions written (10 variants)
- Multi-product ads now show carousel + auto-populate order modal

**Next:**
- 3-5 more FB posts before running paid traffic (feed is thin with 1 post)
- Google Apps Script setup (RA manual) → fill `FORM_ENDPOINT` in script.js
- stage_ad.py CTA swap: Messenger → `https://duberymnl.vercel.app?id=[id]`
- Outback Green hero shot missing (using old `outback-green.png` fallback)
- Carousel content direction for homepage: variants / social proof / lifestyle (TBD)

---

### 2026-03-16 (Session 23) — Facebook Page Update + Landing Page Carousel Planning

**What was done:**
- Updated Dubery MNL Facebook page for the first time in years:
  - New cover photo: Dubery MNL logo on black bg (clean, brand-forward)
  - Bio rewritten: from broken auto-translated copy to "Polarized sunglasses built for Manila. Starting at ₱699 -- same-day delivery, COD."
  - Website field: `https://duberymnl.vercel.app` (live landing page)
  - Action button: "Shop Now" → landing page
- First organic Facebook post published in years:
  - Used the infographic image (beach scene, 3 callout bubbles: Polarized Lenses, UV400 Protection, Lightweight Frame)
  - Caption: Option C (quick facts, Taglish punchlines) -- "Regular vs. polarized. Here's the difference: Glare? Wala na. Eye strain? Finish na. UV rays? Blocked. That's what you're getting."
  - Educational/brand-building angle, not sales-focused

**Carousel planning started:**
- RA asked about adding a carousel to the landing page
- Content direction not yet decided -- candidates: product variants, social proof, lifestyle shots
- Pending: RA to confirm content direction before build starts

**Milestones:**
- Facebook page now active and presentable -- cover, bio, website, and first post all live
- Page is ready to receive traffic from ads and landing page

**Next:**
- Decide carousel content direction (variants / social proof / lifestyle)
- 3-5 more FB posts before running paid ads (feed looks thin with 1 post)
- Google Apps Script setup (RA manual) → fill FORM_ENDPOINT in script.js
- stage_ad.py CTA swap: Messenger → `https://duberymnl.vercel.app`

---

### 2026-03-16 (Session 19) — Day 0 Arc: Cover + Panels 1 & 2

**What was built:**

**Storyboard locked:**
- `.tmp/kiko_day0_storyboard.json` — full 8-panel Day 0 arc documented with scene, dialogue, tone, and visual notes
- Arc premise: night before swimming trip → FB ad → landing page → COD order → delivery → unboxing → ready

**Panel 1 (v1 → v2):**
- v1 generated and approved — Kiko's look confirmed solid, scene reads correctly
- Feedback: room too bare, needs identity elements to tell who Kiko is
- v2 prompt updated: added tsinelas, electric fan, reggae poster, calendar (date circled), Bluetooth speaker, paperback, charging cable
- v2 generated — room now tells Kiko's story before the plot does. Strong improvement.

**Cover — "KIKO: Issue 01":**
- Concept: split composition — dark bedroom (left) / bright beach (right), Kiko centered with Rasta Red
- Typography: "KIKO" title + "Day 0: Bago pa ang Bukas" subtitle + DUBERY MNL / ISSUE 01 bottom strip
- Generated and approved — looks like a real komiks cover
- Files: `.tmp/kiko_day0_cover_prompt.txt` + `.tmp/kiko_day0_cover.json`

**Panel 2 prompt built:**
- Scene: Kiko in bed scrolling Facebook, DuberyMNL ad appears in feed, thumb stops
- Key visual: phone screen showing Rasta Red ad + "Same-day delivery. Metro Manila. COD."
- Caption: "Sinabi mo?" — quiet discovery, not excitement
- Files: `.tmp/kiko_day0_panel2_prompt.txt` + `.tmp/kiko_day0_panel2.json`

**Workflow rule added:**
- Memory: always run parser after generating prompt.txt — both outputs required (plain text + structured JSON)

**Notes on Kiko's look (carry forward):**
- Dreadlocks are rendering slightly long (shoulder-length) vs. spec (chin-length) — consistent across cover + Panel 1
- If this becomes the locked look, update the spec. If not, add: "Dreadlocks end exactly at chin level, thin and sparse."

**Next:**
- Panel 2 to be generated in Gemini
- Continue arc: Panel 3 (landing page), Panel 4 (order), Panel 5 (confirmation), Panel 6 (rider), Panel 7 (unboxing), Panel 8 (ready)
- Panel 7 is the most emotional beat and highest-priority standalone ad unit

---

### Session 17 — Landing Page Template Build

**tools/landing/export_captions.py** — built and run:
- Exports 28 IMAGE_APPROVED entries to `dubery-landing/data/captions.json`
- Copies `output/images/dubery_[id].jpg` → `dubery-landing/assets/ads/`
- 6 skipped (IDs 16-21, no local image)
- Run: `python3 tools/landing/export_captions.py`

**Landing page template built (3 files rewritten):**
- `index.html` — reference design layout: full-bleed hero, 2-col features, lens proof, delivery strip, pricing, modal
- `styles.css` — Barlow Condensed headlines, orange accent (#E8500A), dark editorial
- `script.js` — dynamic `?id=` loading + real form submit to `FORM_ENDPOINT` constant

Assets downloaded from Drive Misc folder → `assets/dubery-logo.png`, `assets/dubery-mnl-logo.png`

Dynamic JS: `?id=5` → swaps hero bg to `assets/ads/dubery_5.jpg` + loads headline/vibe from `data/captions.json`

`FORM_ENDPOINT` = empty string (template mode) — fill after Google Apps Script deploy

Preview: `cd dubery-landing && python3 -m http.server 8080`

**Pending fixes (next session):**
- Hero background image fit on mobile (sizing/positioning)
- Review in Chrome DevTools device mode
- Google Apps Script setup (RA manual) → fill FORM_ENDPOINT
- Vercel deploy → live URL → update stage_ad.py CTA

---

### 2026-03-15 (Session 16) — WF3b Meta Ads + Dynamic Landing Page

**What was built / decided:**
- Researched full Meta Graph API + Instagram Graph API + TikTok Content Posting API capabilities
- Confirmed: organic posting, Reels, Stories require separate tokens/permissions; reacting/commenting on external posts not possible in any API
- `tools/meta_ads/create_campaign.py` — CTA fixed: SHOP_NOW → SEND_MESSAGE (Messenger), destination_type FACEBOOK → MESSENGER, optimization_goal LINK_CLICKS → CONVERSATIONS
- `tools/meta_ads/stage_ad.py` — new orchestrator: reads pipeline.json → uploads image → creates PAUSED campaign → writes campaign IDs back to pipeline.json → syncs Notion
- `tools/landing/` — new directory created for landing page tools
- `dubery-landing/data/` + `dubery-landing/assets/ads/` — new directories for dynamic landing page data
- Plan finalized for dynamic landing page redesign (matches premium reference design)

**Key decisions:**
- Notion is the primary database; Google Sheet is backup mirror only
- Landing page: single HTML, dynamic via `?id=5` URL param, JS swaps hero image + headline per caption
- Order form backend: Google Sheet via Google Apps Script webhook (RA sets up manually)
- Hosting: Vercel (free static deploy)
- CTA: both "Order via Form" + "Chat on Messenger"
- Meta Ads CTA will swap from Messenger → landing page URL once deployed

**Landing page plan (pending execution):**
- Full redesign of `dubery-landing/` — bold lifestyle hero, features, polarized lens section, delivery, pricing
- `tools/landing/export_captions.py` — generates captions.json + copies ad images to assets/ads/
- Deploy via `npx vercel --prod` from dubery-landing/
- After URL is live: update stage_ad.py to point to `?id=[caption_id]`

**Milestones:**
- WF3b architecture fully designed and partially built
- Landing page strategy locked: dynamic per-ad personalization
- Explored full social media API landscape (FB, IG, TikTok)

**Struggles:**
- Realized mid-build that Meta Ads need a destination URL → needed landing page first
- stage_ad.py built but Meta Ads CTA still points to Messenger (interim until landing page live)

**Next:**
- Execute landing page redesign + export_captions.py
- Deploy to Vercel → get live URL
- Update stage_ad.py CTA to landing page
- Complete status.py update (Has ad staged line)
- WF3a organic posting (deprioritized — Meta Ads first)
- IMAGE_REJECTED #2 — needs WF2a retry

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

---

### 2026-03-16 (Session 19) — Landing Page Order Form Polish

**What was built:**

**card_image system:**
- New `card_image` field added to pipeline.json, export_captions.py, captions.json, sync_pipeline.py, script.js
- Product card now uses a direct asset filename per caption instead of keyword-matching on product_ref
- Card Image column added to Google Sheet + Notion DB
- rasta-red-card.png added as the first new-format product card asset

**Asset cleanup:**
- Removed all duplicate .jpg product images (kept .png + bundle.jpg)
- Renamed Rasta - red - asset.png → rasta-red-card.png, Inclusions.png → inclusions.png

**Hero / CTA section:**
- Product card moved above CTA buttons (product first, then buy)
- "BUY NOW" → "ORDER NOW — SAME-DAY DELIVERY"
- Chat on Messenger → Facebook blue (#0084FF), 70% opacity, smaller than primary CTA
- Lens badge + headline color → `--accent-active` (darker dynamic accent)

**Order form — variant picker:**
- Dropdown options: white background + dark text (was dark-on-dark — unreadable)
- Stepper overflow fix: `min-width: 0` on .picker-select so stepper doesn't bleed off screen
- Tap-to-preview overlay: tap any thumbnail to see full image, tap to dismiss or press Escape

**Order summary redesign:**
- "Order Summary" header moved outside the card (above it, not inside)
- Each summary line shows product thumbnail (tappable), product name, quantity
- Freebies row added: inclusions.png + "Freebies" auto-populates, qty matches total pairs
- Delivery nudge: "Add 1 more pair to avail FREE delivery!" — shows at exactly 1 pair
- Tiered pricing: ₱699 / ₱1,200 / ₱1,800 / ₱2,300 / +₱500 per extra pair
- Amount row + Est. Delivery Fee (₱99) + COD Fee (₱0) + separator line + Total row
- At 2+ pairs: delivery fee → FREE (green), Total = exact product price

**Discoveries / Learnings:**
- `display: flex` in CSS overrides the HTML `hidden` attribute — must add explicit `[hidden] { display: none }` rule
- `min-width: auto` on flex items prevents proper shrinking — `min-width: 0` is the fix for overflow in constrained containers
- Google Places Autocomplete identified as next UX upgrade for address field — needs Google Maps API key with Places API enabled, free up to 28k requests/month

**Pending:**
- Google Maps Places Autocomplete (RA to get API key)
- Vercel deploy → live URL
- Google Apps Script setup (manual, RA)
- stage_ad.py CTA swap to landing page URL

---

### Session 22 — Vercel Deploy + Modal Fix + FB Button

**Deployed to Vercel:** https://duberymnl.vercel.app
- CLI deploy via `vercel --prod` from dubery-landing/
- Google Maps API key restricted to duberymnl.vercel.app in Google Cloud Console
- LANDING_PAGE_URL saved to .env

**Modal pointer-events fix:**
- Hidden modal (translateY off-screen) was still intercepting all pointer events on desktop
- Symptom: ORDER NOW button and tap-to-view did nothing on desktop, browser autofill popup appeared over product card
- Fix: added `pointer-events: none; visibility: hidden` to `.modal`, restored on `.modal.active`
- Desktop modal CSS override also updated for opacity transition

**Facebook button:**
- Swapped Messenger button href from `m.me/111349974035733` → `facebook.com/duberymnl`
- m.me blocked by NET::ERR_CERT_AUTHORITY_INVALID on RA's machine (SSL interception)
- Both hero and final CTA Messenger buttons updated

**Tunnel watchdog:**
- tools/tunnel-watchdog.sh — checks every 5 min, auto-restarts code-tunnel if dead

**Pending:**
- Google Apps Script setup (manual, RA) — paste Web App URL into FORM_ENDPOINT in script.js
- stage_ad.py CTA swap to https://duberymnl.vercel.app
- Landing page content backlog: proof of purchases, correct product assets, polarized benefits explainer

---

### Session 31 — Landing Page Asset Rework + Maps Autocomplete Fix (2026-03-18)

**What was done:**
- Rearranged assets folder: ads/ (hero images), cards/ (product card shots), proofs/ (social proof), variants/ (order summary thumbnails)
- Updated script.js: PRODUCT_IMAGE_MAP, VARIANTS, PRODUCT_DEFAULT all pointing to new folder structure
- Updated index.html: default product photo and all proof images updated to new paths
- Replaced missing hero.png fallback with assets/ads/dubery_32.jpg
- Fixed Google Maps Places Autocomplete: migrated from deprecated `Autocomplete` to `AutocompleteSuggestion` API (new)
- Fixed `componentRestrictions` → `includedRegionCodes` (new API parameter)
- API key restrictions set: localhost:8080 + duberymnl.vercel.app (ngrok excluded -- URL changes every session)
- Removed debug log after Maps confirmed working

**Additional work (continued session):**
- Removed floating Facebook button (pending chatbot setup)
- Removed "Nationwide shipping via J&T, JRS, and LBC" text from proof strip
- Fixed export_captions.py: now accepts images already in assets/ads/ (not just output/images/)
- Added Classic series filter to export_captions.py -- Classic product_refs excluded from landing page
- Excluded ID 31 (Purple variant -- not a real product)
- Updated preview.html: ad dropdown now dynamically built from captions.json (was hardcoded)
- Added Classic series fallback mapping to PRODUCT_IMAGE_MAP in script.js
- pipeline.json confirmed as single source of truth for landing page via export_captions.py
- Final export: 22 active ads (IDs 16, 19 still missing local images)

**Pending:**
- Vercel deploy
- stage_ad.py CTA swap to https://duberymnl.vercel.app (on hold)
- Landing page content backlog: proof of purchases, correct product assets, polarized benefits explainer
- Google Maps works on localhost only -- ngrok preview blocks it (by design)
- Drop dubery_16.jpg + dubery_19.jpg into assets/ads/ then re-run export
- Facebook Messenger chatbot + comments bot (new initiative)

---

### Session 32 — WF2 Full Agentic Run: 14 New Captions Prompted + Batch Generated (2026-03-18)

**What was done:**
- Confirmed 14 APPROVED captions from earlier WF1 run (20260318-001 to 20260318-015, no 008) were saved in .tmp/captions.json
- Fixed data architecture: review_server.py was pointing to captions.json instead of pipeline.json. Updated to pipeline.json as single source of truth
- Migrated 14 APPROVED entries from captions.json → pipeline.json (one-time migration). pipeline.json now has 49 entries
- Fixed image_review_server.py: route was `<int:caption_id>` — broke for string IDs like 20260318-001. Changed to `<path:caption_id>`
- WF2 made fully agentic: prompt write → parse → batch generate → auto image review, no manual Gemini review step
- Batch 1 (7 captions: 001-007): 6/7 succeeded first run, 003 failed server-side, retried and succeeded. All 7 DONE with Drive URLs
- Wrote all 14 prompt_structured.json files (TYPE A/D per visual_anchor, full overlay spec per caption)
- Batch 2 (7 captions: 009-015): running in background at time of save

**Captions in this run:**
- 001: Bandits Green — Summit squinting (Outdoor/Trail)
- 002: Outback Green+Blue — Trail prepared product duo (Outdoor/Trail)
- 003: Outback Blue — 4am moto camping departure (Moto Camping)
- 004: Bandits Camo+Green+Blue — Dalawang riders bundle (Moto Camping)
- 005: Rasta Brown — Sunday best complete (Church/Sunday)
- 006: Bandits Glossy Black — Sunday light product hero (Church/Sunday)
- 007: Outback Black — Kunot ang noo cat parent humor (Cat Parent)
- 009: Bandits Glossy Black — Over-prepared parent playground (Toddler/Young Parent)
- 010: Outback Blue — Protect yourself too, park bench (Toddler/Young Parent)
- 011: Bandits Camo — Fresh cut glow-up barbershop (New Haircut)
- 012: Bandits Camo — Motovlogger glare helmet cam (Motovlogger)
- 013: Outback Green+Red — Long ride crew two riders (Motovlogger)
- 014: Outback Black — Manila sun never rests (Lifestyle/Pinoy)
- 015: Rasta Red — Ang araw hindi nagtatanong (Lifestyle/Pinoy)

**Pending:**
- Batch 2 generation still running
- Image review for all 14 (email will be sent automatically on batch completion)
- Sync to Notion + Google Sheet after review

---

### Session 30 — Upwork Continued + Real Estate Lead Automation Job (2026-03-18)

**What was done:**
- Continued Upwork browsing
- Evaluated one more posting: "AI Specialist Needed for Real Estate Lead Automation in Georgia"
  - Georgia-based real estate agency
  - Needs: lead gen automation, follow-up, appointment setting
  - Fit: strong -- DuberyMNL is a live lead capture system, TDCX background is a direct angle
  - Status: pending -- RA to check Connects cost and apply at home
- Committed and pushed home repo (context/me.md, context/work.md, journal/03.md)

**Pending (pick up at home):**
- Buy Connects bundle
- Apply to Real Estate Lead Automation job (posted ~1 hour ago at session end)
- Build Upwork profile bio using TDCX story + DuberyMNL proof
- Semaphore SMS setup
- Fix Google Maps Places Autocomplete

---

### Session 29 — Upwork Browsing + Job Evaluation (2026-03-18)

**What was done:**
- Browsed Upwork together -- evaluated 7 job postings for fit
- Built RA's job evaluation framework (what to filter in/out)

**Jobs evaluated:**
1. Automated Business Workflow Developer ($15-50/hr, Expert, n8n) -- Good fit but 16 already interviewing, only 10 Connects, 20 required. Skipped.
2. AI Systems Engineer (Claude/OpenAI/LLM Automation) -- Best fit seen. Claude in the title, WAT framework matches perfectly. Fresh post. Would apply but needs to buy Connects.
3. Appointment Setter (AI-assisted outreach) -- Skipped. Use your own account + Philippines not in location list.
4. Web Design Sales Partner (30% commission) -- Skipped. Commission-only referral, not a freelance role.
5. AI Automation to Find Company Websites + Submit Forms ($100 fixed) -- Skipped. Severely underpaid + ethical gray area (spam automation).
6. Accounting Department Automation Specialist -- Skipped. Requires proven accounting automation portfolio + Xero + ISO compliance. Out of scope.
7. AI Builders Wanted (revenue-generating products) -- Tentative. Open-ended, no rate shown. DuberyMNL qualifies as example. Would need to clarify comp structure before applying.
8. Google Meet Transcript Management -- Strong fit (Google Drive, n8n, well-scoped). 14 Connects required. Needs Connects purchase.
9. Google Meet form automation job (JotForm + Google Sheets + automation) -- Good entry-level fit. Make/Zapier gap (RA uses n8n). First Upwork review opportunity.

**Key learnings about Upwork:**
- Connects = currency for applying (roughly $0.15 each, sold in bundles)
- Expert-level jobs require Job Success Score 90%+ (new accounts get flagged)
- Philippines-friendly jobs are rare -- look for it explicitly in location filter
- Target: Intermediate level, under 10 proposals, posted under 24 hours, 6 Connects max
- Best search terms: n8n automation, Google Sheets automation, Facebook ads automation, Apps Script, AI workflow

**RA's Upwork positioning:**
- Title: "AI Automation Specialist | n8n | Facebook Ads Funnels | Lead Gen"
- Key differentiator: Google Leads Qualification background (TDCX/Google) + AI automation builder
- Portfolio anchor: DuberyMNL WAT framework as living proof of AI + automation work
- Needs to buy Connects before applying to anything

**Next for Upwork:**
- Buy minimum Connects bundle
- Apply to fresh intermediate postings (6 Connect cost, under 10 proposals)
- Build profile bio using Google story + DuberyMNL as proof

---

### Session 28 — Facebook Ads Education + WF2 Gap Identified (2026-03-18)

**Facebook ads fundamentals covered:**
- Campaign → Ad Set → Ad structure
- Objective: Traffic or Leads (not Engagement, not Awareness)
- Only metric that matters right now: cost per order
- Budget: ₱100-200/day to start, daily budget, don't touch during 7-day learning phase
- Targeting: broad (Metro Manila, 18-40, all genders) -- the creative does the targeting
- Advantage+ audience valid option for small budgets
- Creative priority order: image stops scroll → first caption line holds attention → CTA button converts
- CTA button: Shop Now or Order Now (not Learn More)

**Key decision:**
- 24 ads on duberymnl.vercel.app are ready to run ads on RIGHT NOW
- New 15-caption batch needs WF2 images first
- Launch ads on existing 24 while WF2 gets built

**WF2 gap identified:**
- Tools exist (generate_kie.py, image_review_server.py)
- End-to-end pipeline not wired: caption approved → prompt built → image generated → reviewed → ad-ready
- Next major build: complete WF2 as a clean single workflow

---

### Session 27 — WF1 Run + Workflow Upgrades (2026-03-18)

**WF1 caption generation run:**
- 15 new captions generated (IDs 20260318-001 to 20260318-015)
- Vibes: Outdoor/Trail+Adventure, Moto Camping, Church/Sunday Vibes, Cat Parent Vibes, Toddler/Young Parent, New Haircut/Barbershop, Motovlogger, Lifestyle/Pinoy Culture
- Bundle captions: IDs 004 (Moto crew), 008 (Cat parent barkada), 013 (Riding buddy)
- PRODUCT: 7 / PERSON: 8 (50/50 -- last time before bias change takes effect)
- Output appended to .tmp/captions.json (28 total entries)
- Review server live, email sent to sarinasmedia+claude@gmail.com

**WF1 workflow upgrades (caption_generation.md):**
- Research caching: Step 3 now checks .tmp/wf1_research_cache.json before web search (skip if < 7 days old)
- PRODUCT anchor bias: raised to 65-70% PRODUCT / 30-35% PERSON (was 50/50)
- Angkas voice rule hardened: energy reference only, no copying

**Scheduling:**
- WF1 cron job added to system crontab: every Monday 8pm PHT
- Command: `claude "run wf1 caption gen"` in DuberyMNL working dir
- Logs to .tmp/wf1_cron.log

---

### Session 26 — Lead Capture + Pipeline Sync (2026-03-18)

**Lead capture live:**
- Google Apps Script deployed as web app, linked to DuberyMNL Orders sheet
- Form POSTs via FormData to Apps Script endpoint
- Sheet columns: Timestamp, Name, Phone, Address, Items, Qty, Delivery Fee, Total Amount, Notes, Ad ID
- Items and Qty on separate lines per product (newline separator)
- Pricing logic from frontend: single pair ₱699 + ₱99 delivery = ₱798 total; 2+ pairs = bundle price (₱1,200+) FREE delivery
- FORM_ENDPOINT set in script.js, live on duberymnl.vercel.app
- SMS via Semaphore: script ready, pending Semaphore account + Sender ID registration (DUBERYMNL)

**Semaphore setup (pending):**
- Register at semaphore.co, submit Sender ID "DUBERYMNL" (1-3 day approval)
- Add API key to Apps Script line 2, redeploy as new version

**Pipeline audit:**
- Cross-checked captions.json vs Notion pipeline vs Google Sheet
- Removed all Classic series from active ads (IDs 18, 20, 21, 25, 27, 29, 30, 31, 36, 38 parked in captions-classic.json)
- Added IDs 16 (Bandits Black) and 19 (Bandits Blue) to captions.json -- were IMAGE_APPROVED but missing
- Fixed product refs in Notion: ID 23 → "Rasta Brown, Rasta Red, Outback Green, Bandits Camo"; ID 24 → "Outback Red"; ID 32 → "Rasta Red"
- Active ad count: 24

**Pending:**
- ID 2 (Outback Series) -- IMAGE_REJECTED in Notion for product fidelity, IMAGE_APPROVED in sheet -- RA to decide if it goes back in
- Add missing picker thumbnails: Outback Red, Outback Blue, Bandits Green, Bandits Blue, Bandits Tortoise
- Fix Google Maps Places Autocomplete (broken, debug via browser console at home)
- Restrict Google Maps API key confirmed set to duberymnl.vercel.app
- stage_ad.py CTA swap to https://duberymnl.vercel.app
