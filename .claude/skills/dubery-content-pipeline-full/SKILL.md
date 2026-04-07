---
name: dubery-content-pipeline-full
description: Full end-to-end pipeline -- captions, prompts, image generation, review, and optional ad staging. Uses existing Python tools for API calls.
---

# DuberyMNL Full Content Pipeline

Generates captions, writes image prompts, generates images via kie.ai, waits for review,
and optionally stages Meta ads. End-to-end, one command.

## Trigger

Say:

```
full pipeline
```

or

```
run full pipeline
```

Optional arguments:
- `--count N` -- number of captions to generate (default: 3)
- `--line OUTBACK|BANDITS|RASTA|MIX` -- target product line(s) (default: MIX)
- `--skip-images` -- stop after prompts (same as content pipeline)
- `--skip-ads` -- stop after image review (don't stage ads)
- `--dry-run-ads` -- stage ads in dry-run mode (no Meta API calls)

---

## Prerequisites

- `.tmp/pipeline.json` exists
- `.venv` activated at `C:/Users/RAS/projects/DuberyMNL/.venv`
- `.env` has all required keys (kie.ai, Meta, Google)
- dubery-caption-gen skill available (caption rules)
- dubery-prompt-writer skill available (prompt rules)

---

## Flow

```
STEP 1: Context Load
    ├── Read last 20 entries from .tmp/pipeline.json
    ├── Note recent angles, vibes, hook_types, products used
    └── Avoid repeating recent combinations

STEP 2: Generate Captions (agent)
    ├── Generate N captions following dubery-caption-gen rules
    ├── Deduplicate against last 20 (angles, vibes, products)
    ├── Set status: APPROVED (skip review server)
    └── Write to pipeline.json immediately

STEP 3: Run Prompt Writer (parallel agents)
    ├── For each caption, run dubery-prompt-writer skill
    ├── Apply all rules (R1-R9, Overlay Rules 1-8, Rule 5a branding)
    ├── Self-check, save to .tmp/{id}_prompt_structured.json
    └── Update status: APPROVED --> PROMPT_READY

    ** Show prompt summary table to RA **
    ** If --skip-images: stop here **

STEP 4: Generate Images (sequential, tool)
    ├── Run: .venv/bin/python tools/pipeline/run_wf2.py --ids {id1} {id2} ...
    ├── Images generate one at a time (sequential)
    ├── Each image: kie.ai API call --> poll --> download --> Drive backup
    ├── Status: PROMPT_READY --> DONE
    └── Report each image as it completes

STEP 5: Image Review (human checkpoint)
    ├── Image review server should already be running (localhost:5001)
    ├── If not running: start with bash tools/image_gen/start_image_review.sh
    ├── Tell RA: "N images ready for review at localhost:5001"
    ├── WAIT for RA to confirm review is done
    ├── Do NOT proceed until RA says "done" or "reviewed"
    └── Status after review: DONE --> IMAGE_APPROVED or IMAGE_REJECTED

    ** If --skip-ads: stop here **

STEP 6: Stage Ads (tool, optional)
    ├── Only run on IMAGE_APPROVED captions from this batch
    ├── Run: .venv/bin/python tools/meta_ads/stage_ad.py --id {id}
    │   (or --all for all IMAGE_APPROVED, or --dry-run to preview)
    ├── Ads are staged as PAUSED -- RA launches manually in Ads Manager
    ├── Status: IMAGE_APPROVED --> AD_STAGED
    └── Report: ad IDs, campaign, ad set

STEP 7: Summary
    ├── Show final status of all captions in this batch
    ├── Table: ID | Product | Status | Image | Ad
    └── Flag any failures or items needing attention
```

---

## Human Checkpoints

There is ONE mandatory stop in this pipeline:

| Step | Checkpoint | Why |
|------|-----------|-----|
| Step 5 | Image review | RA decides which images are good enough to become ads |

Everything else runs automatically. Step 6 (ad staging) only runs on images RA approved.

---

## Tool Usage

| Step | Who executes | Tool |
|------|-------------|------|
| 1. Context load | Agent | Read pipeline.json |
| 2. Captions | Agent | Follow caption-gen rules |
| 3. Prompts | Agent (parallel) | Follow prompt-writer rules |
| 4. Image gen | Python script | `tools/pipeline/run_wf2.py` |
| 5. Image review | RA (human) | `tools/image_gen/image_review_server.py` |
| 6. Ad staging | Python script | `tools/meta_ads/stage_ad.py` |
| 7. Summary | Agent | Read pipeline.json |

Agent reasons, tools execute. Creative work (steps 2-3) is agent. API work (steps 4, 6) is tools.

---

## Product Line Selection

Same as content pipeline:

| Flag | Products to draw from |
|------|----------------------|
| OUTBACK | Outback - Black, Blue, Green, Red |
| BANDITS | Bandits - Glossy Black, Matte Black, Blue, Green, Tortoise |
| RASTA | Rasta - Brown, Red |
| MIX | One from each line (default for --count 3), or spread evenly |

---

## Caption Generation Rules

Follow ALL rules from `dubery-caption-gen` skill:

- Language: ~80% English / ~20% Tagalog
- Emoji: 1-2 per caption, never zero
- CTA: last line, one of: "DM us" / "Message us" / "Order now" / "Order na ngayon"
- Hashtags: #DuberyMNL #PolarizedSunglasses #DuberyOptics #CODMetroManila #SameDayDelivery
- Creative hypothesis: one-line explanation of why the ad should work
- Vary hooks, tones, rhythms -- no two captions should feel like rewrites
- Bundle quota: if N >= 5, at least 1 must feature the bundle (P1,200 / 2 pairs)

---

## Error Handling

| Failure | Action |
|---------|--------|
| kie.ai API error | run_wf2.py retries automatically (90 polls, 4s each). If still fails, status goes IMAGE_FAILED. Report to RA. |
| Prompt self-check fails | Fix before saving. Never generate an image from a failing prompt. |
| Meta API error | stage_ad.py reports the error. Do NOT retry without RA's approval (costs money). |
| Image review server not running | Start it: `bash tools/image_gen/start_image_review.sh` |

---

## Important Notes

- Image generation is SEQUENTIAL. One at a time. Never parallel.
- Ads are always staged as PAUSED. RA launches manually.
- This skill uses paid APIs (kie.ai for images, Meta for ads). Always confirm with RA before step 4 if --count is large.
- For free testing: use `content pipeline` (stops at prompts) and paste into Gemini.
- The `--skip-images` flag makes this behave exactly like the basic content pipeline.
