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
**Status: PROMPT GENERATION TESTED — SKILL RULES REFINED**
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
