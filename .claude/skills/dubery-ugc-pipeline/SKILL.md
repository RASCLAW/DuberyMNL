---
name: dubery-ugc-pipeline
description: End-to-end UGC content pipeline -- captions, image prompts, fidelity validation. Use when running the UGC pipeline, generating UGC content, or creating social proof assets.
---

# DuberyMNL UGC Content Pipeline

Generate UGC captions AND image prompts in one shot with fidelity validation.
Stops at PROMPT_READY (validated). Image generation is a separate step to control kie.ai spend.

## Trigger

Say:

```
ugc pipeline
```

or

```
run ugc pipeline
```

Optional arguments:
- `--count N` -- number of UGC captions to generate (default: 5)
- `--product PRODUCT_REF` -- lock all entries to one product (default: rotate)
- `--gemini` -- output prompt text for manual paste-test in Gemini web app (Phase A validation)
- `--test` -- use test IDs and clean up after showing results

---

## Prerequisites

- `.tmp/ugc_pipeline.json` exists (or will be created)
- dubery-ugc-caption-gen skill available (caption generation rules)
- dubery-ugc-prompt-writer skill available (image prompt generation)
- dubery-ugc-fidelity-gatekeeper skill available (product fidelity validation)

---

## Flow

```
STEP 0: Context Load
    ├── Read last 20 entries from .tmp/ugc_pipeline.json
    ├── Note recent themes, moods, scenario_hints, product_refs
    └── Avoid repeating recent combinations

STEP 1: Generate UGC Captions
    ├── Find next available UGC ID from ugc_pipeline.json
    ├── Generate N captions following dubery-ugc-caption-gen rules:
    │   - theme, mood, scenario_hint, product_ref
    │   - caption_text, hashtags
    │   - NO pricing, NO CTAs, NO sales language
    ├── Set status to CAPTION_APPROVED (skip review for pipeline mode)
    └── Write each caption to ugc_pipeline.json immediately

STEP 2: Derive Image Prompts (sequential)
    ├── For each new caption, run dubery-ugc-prompt-writer:
    │   a. Read caption from ugc_pipeline.json
    │   b. Use caption_text + mood + scenario_hint to derive scene
    │   c. Generate Dense Narrative JSON prompt
    │   d. Save to .tmp/{id}_ugc_prompt.json
    │   e. Update ugc_pipeline.json: status = PROMPT_READY
    └── Process one at a time — save each before moving to next

STEP 3: Run Fidelity Gatekeeper (sequential)
    ├── For each PROMPT_READY entry:
    │   a. Read the prompt JSON
    │   b. Run all 8 fidelity checks (dubery-ugc-fidelity-gatekeeper)
    │   c. If PASS: status stays PROMPT_READY (ready for --generate)
    │   d. If REJECT: set status to FIDELITY_FAILED, log reasons
    │   e. If REJECT: attempt ONE rewrite (re-run prompt writer)
    │   f. Re-run gatekeeper on rewrite. If still REJECT: final FIDELITY_FAILED.
    └── Report: N passed, M failed, reasons for failures

STEP 4: Report Results
    ├── Summary table: ID | Theme | Scenario | Product | Fidelity
    ├── PROMPT_READY entries: ready for `python tools/pipeline/run_ugc.py --generate`
    ├── FIDELITY_FAILED entries: need manual review or skip
    └── If --gemini flag: output each PROMPT_READY prompt text for paste-test
```

---

## Caption-to-Image Bridge

This is the critical innovation: the caption DRIVES the image.

When generating the image prompt (Step 2), the prompt writer must:

1. Read the caption's `caption_text`, `mood`, and `scenario_hint`
2. Derive the visual scene FROM the caption's story:
   - Caption about a road trip → scene at a highway or scenic overlook
   - Caption about beach day → scene at a specific Filipino beach
   - Caption about everyday carry → scene at a cafe, office, or street
3. The `scenario_hint` from the caption determines the scenario type
4. The `mood` from the caption shapes the lighting, composition, and energy
5. The result: image and caption tell the same story

**Do NOT generate random scenes unconnected to the caption.**

---

## UGC Pipeline Entry Schema

Each entry in `ugc_pipeline.json`:

```json
{
  "id": "UGC-20260406-001",
  "caption_text": "...",
  "hashtags": "#DuberyMNL ...",
  "theme": "flex",
  "mood": "flexing",
  "scenario_hint": "PRODUCT_HOLD",
  "scenario_type": "PRODUCT_HOLD",
  "subject_gender": "male",
  "product_ref": "Outback Red",
  "aspect_ratio": "9:16",
  "status": "CAPTION_APPROVED | PROMPT_READY | FIDELITY_FAILED | GENERATING | DONE | IMAGE_FAILED",
  "prompt_file": ".tmp/UGC-20260406-001_ugc_prompt.json",
  "output_file": "contents/new/ugc_UGC-20260406-001.jpg",
  "fidelity_verdict": null,
  "fidelity_reasons": [],
  "drive_url": "",
  "created_at": "2026-04-06T12:00:00",
  "reviewed": false,
  "notes": ""
}
```

---

## Status Flow

```
PENDING → (caption gen) → CAPTION_APPROVED → (prompt writer) → PROMPT_READY
                                                                     │
                                              ┌──────────────────────┤
                                              ▼                      ▼
                                      FIDELITY_FAILED         (gatekeeper PASS)
                                              │                      │
                                              ▼                 PROMPT_READY
                                        (rewrite once)              │
                                              │              (run_ugc.py --generate)
                                              ▼                      │
                                      FIDELITY_FAILED           GENERATING
                                        (final)                     │
                                                              ┌─────┴─────┐
                                                              ▼           ▼
                                                            DONE    IMAGE_FAILED
```

---

## Gemini Paste-Test (Phase A Validation)

When `--gemini` is specified:

For each PROMPT_READY entry, output a formatted block:

```
=== UGC-20260406-001 | Outback Red | PRODUCT_HOLD ===

[Full prompt text from the prompt field — copy and paste into Gemini]

Reference image: [path]
Negative prompt: [negative_prompt text]
```

This lets RA test prompts for free in Gemini's web app before spending kie.ai credits.

---

## After Pipeline Completes

Tell RA:

```
UGC Pipeline complete.
  ✓ N captions generated
  ✓ N prompts written
  ✓ N passed fidelity gatekeeper
  ✗ N failed fidelity (see reasons above)

Next steps:
  • Review PROMPT_READY entries
  • (Optional) Paste prompts into Gemini for free visual test
  • When ready: python tools/pipeline/run_ugc.py --generate
  • After generation: python tools/pipeline/run_ugc.py --generate (starts review server)
```
