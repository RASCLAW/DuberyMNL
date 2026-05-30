# pipeline — Content pipeline orchestration (WF1 validation, WF2 image gen, UGC, regeneration)

**What it does**
- Validates freshly-generated caption batches (WF1) against quota rules, field requirements, and distribution targets before any image is generated.
- Orchestrates the full WF2 flow: APPROVED captions → prompt writing → gatekeeper validation → kie.ai image generation → image review server → Google Sheet sync.
- Runs UGC social-proof images through a three-phase plan/generate/review cycle with a built-in fidelity gatekeeper.
- Handles regeneration of rejected images, auto-classifying each as a lightweight NB2 edit or a full Claude prompt rewrite.

**Key files**

| Script | Purpose |
|--------|---------|
| `validate_wf1.py` | Batch validator for WF1 caption output — checks required fields, visual anchor ratios, hook type caps, bundle quota, emoji count, CTA presence |
| `run_post_review.py` | Primary WF2 orchestrator — prompt writing (WF2a) then image gen (WF2b); triggered automatically after caption review |
| `run_wf2.py` | WF2 image-gen runner — gatekeeper loop + sequential kie.ai generation for PROMPT_READY captions |
| `run_regenerate.py` | Regeneration runner — classifies REGENERATE entries as edit or full regen, then calls kie.ai or Claude accordingly |
| `run_ugc.py` | UGC pipeline — plan batches, track status, run fidelity gatekeeper, generate via kie.ai |
| `run_post_image_review.py` | Post-image-review finisher — syncs Google Sheet, exports landing page captions.json, sends email notification |
| `batch_clean_render_notes.py` | One-time cleanup utility — strips color/material descriptions from existing prompt JSON render_notes fields |

**Run**

```bash
# WF1: validate the 15 most recent PENDING captions
python tools/pipeline/validate_wf1.py --last 15

# WF1: validate specific IDs
python tools/pipeline/validate_wf1.py --ids 20260318-001 20260318-002

# WF2: full post-caption-review run (auto-detects batch, writes prompts + generates images)
python tools/pipeline/run_post_review.py

# WF2: prompts only (skip image gen)
python tools/pipeline/run_post_review.py --prompts-only

# WF2: image gen only (prompts already written)
python tools/pipeline/run_post_review.py --images-only

# WF2: specific IDs or batch
python tools/pipeline/run_post_review.py --ids 20260318-001 20260318-002
python tools/pipeline/run_post_review.py --batch 20260320

# WF2 image gen directly (lower-level, called by run_post_review.py)
python tools/pipeline/run_wf2.py
python tools/pipeline/run_wf2.py --ids 20260318-001 20260318-002
python tools/pipeline/run_wf2.py --force

# Regeneration (auto-classifies edit vs full regen)
python tools/pipeline/run_regenerate.py
python tools/pipeline/run_regenerate.py --ids 1 16
python tools/pipeline/run_regenerate.py --mode edit
python tools/pipeline/run_regenerate.py --mode regen
python tools/pipeline/run_regenerate.py --dry-run

# UGC pipeline
python tools/pipeline/run_ugc.py --status
python tools/pipeline/run_ugc.py --plan --count 5
python tools/pipeline/run_ugc.py --plan --count 3 --scenario BEACH_CANDID
python tools/pipeline/run_ugc.py --plan --count 3 --ratio 4:5 --product "Bandits Black"
python tools/pipeline/run_ugc.py --generate
python tools/pipeline/run_ugc.py --generate --ids UGC-20260318-001
python tools/pipeline/run_ugc.py --generate --skip-fidelity

# Post-image-review finisher
python tools/pipeline/run_post_image_review.py
python tools/pipeline/run_post_image_review.py --dry-run
python tools/pipeline/run_post_image_review.py --no-email

# Render notes cleanup (one-time, preview first)
python tools/pipeline/batch_clean_render_notes.py --dry-run
python tools/pipeline/batch_clean_render_notes.py
```

**Inputs / outputs**

| What | Where |
|------|-------|
| Caption pipeline state | `.tmp/pipeline.json` (file-locked on write; `.json.bak` backup kept) |
| Rejected captions | `.tmp/rejected_captions.json` |
| UGC pipeline state | `.tmp/ugc_pipeline.json` |
| Session queue | `.tmp/wf2_queue.json` (optional, consumed by `run_post_review.py`) |
| Structured prompt JSONs | `.tmp/<id>_prompt_structured.json` |
| Generated images | `contents/new/dubery_<id>.jpg` (WF2), `contents/new/ugc_<id>.jpg` (UGC) |
| Generation logs | `.tmp/generate_<id>.log`, `.tmp/ugc_<id>.log` |
| Google Sheet | Synced via `tools/notion/sync_pipeline.py --sheets-only` |
| Landing page data | `dubery-landing/captions.json` (exported by `tools/landing/export_captions.py`) |

**Auth / env**

- `GMAIL_SENDER`, `GMAIL_APP_PASSWORD`, `REVIEW_EMAIL_RECIPIENT` — email notification in `run_post_image_review.py`
- Google Sheets OAuth — used by `sync_pipeline.py` (called as a subprocess); credentials managed separately in `tools/sheets/`
- kie.ai API key — used by `tools/image_gen/generate_kie.py` (called as a subprocess)
- `ANTHROPIC_API_KEY` — used by `run_regenerate.py` and `run_post_review.py` via `claude --print` subprocess calls

**Gotchas**

- `run_wf2.py` runs image generation **sequentially** (not parallel) to avoid kie.ai 429 rate errors. Do not add parallelism here.
- `run_ugc.py --generate` runs up to 3 parallel workers; kie.ai quota still applies — watch for 429s.
- `run_post_review.py` is the correct entry point for the full WF2 flow. Calling `run_wf2.py` directly skips prompt writing (WF2a).
- `batch_clean_render_notes.py` is a one-time cleanup tool — always run with `--dry-run` first and confirm output before applying.
- On Windows, `fcntl` is unavailable; the scripts fall back to `msvcrt.locking` for file locking on `pipeline.json`.
