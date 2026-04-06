# UGC Pipeline Ultraplan Prompt

*Created: 2026-04-07*
*Status: Ready to paste into ultraplan*

## Context
Built with /prompt-master in ra-dashboard session. Covers:
1. UGC caption generation (lifestyle/flex, not sales)
2. Caption-driven image prompt derivation (caption -> scene -> parsed JSON)
3. NEW product fidelity gatekeeper (zero tolerance, no patching)
4. Posting automation (4/week)
5. Comment auto-responder + auto-DM
6. Messenger chatbot (WF4)

## Prompt

```
/ultraplan

## Goal
Plan and build the DuberyMNL UGC content pipeline — from UGC caption generation to caption-driven image prompt derivation to product fidelity validation to AI image generation to automated Facebook posting to comment auto-response and Messenger-based sales conversion via chatbot.

## Current State
- WF1 (caption generation + approval) and WF2 (AI image generation via kie.ai / Nano Banana 2) are DONE and working for ad creatives
- WF3a (auto-posting to Facebook) is BUILT but not yet active — Meta Business Verification is now approved
- WF4 (chatbot) is ON HOLD — needs to be designed and built
- Existing skills in .claude/skills/:
  - dubery-caption-gen: generates sales captions (WF1), outputs JSON with angle/hook/vibe/visual_anchor
  - dubery-prompt-writer: converts approved caption into structured NB2 JSON prompt (ad-style, full overlays, pricing)
  - dubery-ad-creative: like prompt-writer but strips all pricing — engagement-driven ads
  - dubery-ugc-prompt-writer: generates UGC image prompts in Dense Narrative JSON format — no overlays, candid Filipino UGC style, 70% product-anchor / 30% person-anchor scenarios
  - dubery-prompt-parser: takes a plain text NB2 prompt and extracts it into structured JSON — extraction only, no creative additions
  - dubery-prompt-validator: validates ad prompts before kie.ai — checks overlays, pricing, positioning (NOT suitable for UGC since UGC has no overlays)
  - dubery-content-pipeline: captions + prompts in one shot, stops at PROMPT_READY
  - dubery-content-pipeline-full: end-to-end including image gen + review + ad staging
  - dubery-infographic-ad: hand-drawn callout infographic format
  - dubery-chatbot: Messenger bot persona + conversation architecture (tools/chatbot/)
- kie.ai execution: python scripts/generate_kie.py prompts/prompt.json images/output.jpg "4:5"
- 36 IMAGE_APPROVED ad images exist in the pipeline
- All secrets are in .env (PAGE_ACCESS_TOKEN, KIE_AI_API_KEY, etc.)
- DuberyMNL Pipeline Sheet: 1LVshSQP5Ob9RNqt35PoSjbUuAiu9dneyHHhUiUZKYrg

## Target State

### 1. UGC Caption Generation
- New caption generator specifically for UGC — NOT sales-focused like ad creatives
- UGC caption themes: flex/lifestyle, sulit/value-for-money, build quality, benefits of polarized lenses, everyday use, outdoor adventures — not limited to these
- Tone: organic, relatable, Taglish-friendly, feels like a real person posting — not a brand pushing a sale
- NO pricing in captions (no P699, no P1,200, no bundle deals)
- Captions go through the same approval flow as WF1 (generate -> review -> approve)
- Output: approved UGC captions stored in pipeline sheet or ugc_pipeline.json

### 2. Image Prompt Derivation (Caption -> Scene -> Parsed JSON)
- Each approved UGC caption DRIVES the image prompt — the visual scene is derived FROM the caption's mood, theme, and energy
- Flow: UGC caption -> dubery-ugc-prompt-writer (generates Dense Narrative JSON with scene derived from caption) -> dubery-prompt-parser (extracts to structured JSON for storage and traceability)
- Image style: same hyper-realistic quality as ad creatives but ZERO overlays, ZERO pricing, ZERO brand graphics — only the physical Dubery logo on the sunglasses frame as worn
- Two-phase validation:
  - Phase A: Output the prompt text for manual paste-and-test in Gemini web app (free)
  - Phase B: Once validated, run through kie.ai API via generate_kie.py

### 3. UGC Product Fidelity Gatekeeper (NEW — Critical)
- Build a NEW validator specifically for UGC prompts — NOT the existing dubery-prompt-validator (which checks overlays/pricing that UGC doesn't have)
- This gatekeeper's SOLE PURPOSE: ensure 100% product fidelity and visual likeness of the sunglasses
- An image with failed product fidelity is TRASH — reject immediately, no patching
- Checks must include:
  - Does the prompt preserve exact frame shape from the reference image?
  - Does the prompt avoid describing frame color, material, texture, lens color? (these come from the reference image ONLY)
  - Is the product.instruction verbatim block present? ("This image MUST feature the exact style...")
  - Does the prompt avoid lens reflection descriptions that could alter appearance?
  - Is the reference image path present and correct in image_input?
  - Does any field contain banned appearance words (R2 from prompt-writer: frame colors, lens descriptors, materials)?
  - Could any scene description cause the AI to visually alter the product? (e.g., colored lighting that changes how the lens looks)
- Verdict: PASS (proceed to kie.ai) or REJECT (product fidelity compromised — do not generate, flag for rewrite)
- No PATCH option — if product fidelity is at risk, the prompt gets rewritten, not band-aided
- Run AFTER dubery-prompt-parser, BEFORE kie.ai

### 4. Posting Automation
- Activate WF3a — scheduled auto-posting to Facebook Page (4/week cadence)
- Use approved Meta Page Access Token
- Posts pair the UGC caption + its generated image
- Scheduling mechanism: GitHub Actions (like existing dayparting in schedulers repo) or local cron

### 5. Comment Auto-Responder + Auto-DM (NEW)
- When a user comments on any UGC or ad post, automatically:
  - Like the comment (engagement signal)
  - Reply to the comment with a short, natural Taglish response (e.g., "DM sent po!" or "Check your inbox!")
  - Send a DM to the commenter with product info, pricing, and a CTA to order
- DM template should feel personal, not automated — match the dubery-chatbot voice
- Must use Meta Page API (comments webhook + messaging API)
- Filter: don't auto-respond to spam, own page replies, or repeat commenters within 24hrs

### 6. Messenger Chatbot (WF4)
- Once the auto-DM opens the conversation, the chatbot takes over
- Chatbot handles: product inquiries, order-taking (COD, P699 single / P1,200 bundle), Metro Manila free delivery, handoff to human when needed
- Discount code support: DUBERY50
- Chatbot persona: friendly, Taglish, not corporate — defined in dubery-chatbot skill
- Architecture already scaffolded in tools/chatbot/ — needs wiring and testing
- Escalation triggers: customer asks for human, complaint, order info complete, low confidence

## Constraints
- Windows 11 Pro, no WSL2 — all scripts must run natively
- Python for tools layer, HTML/Tailwind for any web UI
- No paid APIs for prompt testing phase — use Gemini web app for free validation
- Do not break existing working workflows (WF1, WF2, existing ad pipeline)
- Do not restructure the pipeline Google Sheet without confirming first
- Budget-conscious: P100/day ad spend, minimize kie.ai API costs
- Product fidelity is NON-NEGOTIABLE — any prompt that could cause the AI to alter the sunglasses' appearance in any way (frame shape, lens color, logo, material) must be rejected

## Deliverables
- Architecture diagram of the full UGC pipeline (caption -> prompt -> parse -> validate -> generate -> post -> auto-respond -> messenger funnel)
- Implementation plan with phases and dependencies
- File-by-file breakdown of what to build, modify, or connect
- Spec for the new UGC Product Fidelity Gatekeeper skill
- Spec for the comment auto-responder + auto-DM system
- Risk assessment: what could break, what needs human review gates
```
