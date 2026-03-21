---
name: dubery-content-pipeline
description: End-to-end content generation -- captions straight to image prompts, no manual review needed.
---

# DuberyMNL Content Pipeline

Generate captions AND image prompts in one shot. Skips the review server -- captions go
straight to APPROVED and feed into the prompt writer.

## Trigger

Say:

```
content pipeline
```

or

```
run content pipeline
```

Optional arguments:
- `--count N` -- number of captions to generate (default: 3)
- `--line OUTBACK|BANDITS|RASTA|MIX` -- target product line(s) (default: MIX)
- `--test` -- use IDs 900+ and clean up after showing results (no permanent pipeline changes)

---

## Prerequisites

- `.tmp/pipeline.json` exists
- dubery-caption-gen skill is available (for caption generation rules)
- dubery-prompt-writer skill is available (for prompt generation)

---

## Flow

```
STEP 0: Context Load
    ├── Read last 20 entries from .tmp/pipeline.json
    ├── Note recent angles, vibes, hook_types, products used
    └── Avoid repeating recent combinations

STEP 1: Generate Captions
    ├── Find next available ID from pipeline.json
    ├── If --test: use IDs starting at 901, backup pipeline first
    ├── Generate N captions following dubery-caption-gen rules:
    │   - angle, hook_type, vibe, creative_hypothesis
    │   - visual_anchor (70% PRODUCT / 30% PERSON)
    │   - caption_text, hashtags, recommended_products, overlays
    ├── Set status directly to APPROVED (skip PENDING, skip review server)
    └── Write each caption to pipeline.json immediately

STEP 2: Run Prompt Writer (parallel)
    ├── For each new caption ID, run dubery-prompt-writer skill:
    │   a. Read caption from pipeline.json
    │   b. Caption Analysis (6 internal steps)
    │   c. Build structured JSON prompt (full schema)
    │   d. Apply all rules (R1-R9, Overlay Rules 1-8, Rule 5a line branding)
    │   e. Self-Check (9 items)
    │   f. Save to .tmp/{id}_prompt_structured.json
    │   g. Update status: APPROVED --> PROMPT_READY
    └── Run as parallel agents when possible (each writes to separate files)

STEP 3: Validate + Show
    ├── Read all generated prompt JSONs
    ├── Show headline branding comparison table:
    │   | ID | Line | Headline Style | Color | Typography |
    ├── Flag any self-check failures
    └── Report: "N prompts ready. Run WF2 to generate images, or paste into Gemini to test."
```

---

## Product Line Selection

When `--line` is specified:

| Flag | Products to draw from |
|------|----------------------|
| OUTBACK | Outback - Black, Blue, Green, Red |
| BANDITS | Bandits - Glossy Black, Matte Black, Blue, Green, Tortoise |
| RASTA | Rasta - Brown, Red |
| MIX | One from each line (default for --count 3), or spread evenly |

When MIX with --count 3: one Outback, one Bandits, one Rasta.
When MIX with --count > 3: distribute across lines as evenly as possible.

---

## Caption Generation Rules

Follow ALL rules from `dubery-caption-gen` skill, specifically:

- Language: ~80% English / ~20% Tagalog
- Emoji: 1-2 per caption, never zero
- CTA: last line, one of: "DM us" / "Message us" / "Order now" / "Order na ngayon"
- Hashtags: #DuberyMNL #PolarizedSunglasses #DuberyOptics #CODMetroManila #SameDayDelivery
- Creative hypothesis: one-line explanation of why the ad should work
- Vary hooks, tones, and rhythms -- no two captions should feel like rewrites of each other
- Bundle quota: if N >= 5, at least 1 must feature the bundle offer (P1,200 / 2 pairs)

---

## Test Mode (--test)

When --test is passed:
1. Backup pipeline.json to .tmp/test_branding/pipeline_backup.json
2. Use IDs starting at 901
3. After showing results, ask RA: "Keep these or clean up?"
4. If clean up: remove test entries from pipeline.json, restore backup
5. Leave the prompt JSONs in .tmp/ for reference

---

## Important Notes

- This skill SKIPS the review server. Captions go straight to APPROVED.
- This skill SKIPS image generation. It stops at PROMPT_READY.
- To generate images after: run WF2 (`python tools/pipeline/run_wf2.py`)
- To test prompts without spending money: paste the JSON into Gemini or another free model
- Prompt writer agents run in parallel -- all captions process simultaneously
