# WF-UGC — UGC-Style Image Generation

## Overview

This workflow generates **social proof images** — photos that look like real DuberyMNL customers flexing their sunglasses on their timelines, stories, and feeds.

These are NOT ads. No overlays. No price banners. No AIDA structure.
They look like organic posts from happy customers.

**Use UGC images for:**
- Facebook feed posts showing lifestyle/authenticity
- Story reposts (screenshot-style social proof)
- Pairing with captions that reference customers, reviews, or word-of-mouth

**Use WF2 ad images for:**
- Conversion campaigns (price, delivery, CTA overlays)
- Facebook Ads Manager creatives
- Product hero shots

---

## Scenario Library

| Scenario | Description | Typical Setting |
|---|---|---|
| SELFIE_OUTDOOR | Front-cam selfie, harsh sun | Tagaytay, UP Diliman, Luneta |
| BEACH_CANDID | Shot by a friend, natural | Palawan, Batangas, La Union |
| CAR_SELFIE | Driver/passenger flex | EDSA traffic, open road |
| OOTD_STREET | Shades completing the fit | SM North, Trinoma, BGC, Katipunan |
| COMMUTE_FLEX | Shades mid-commute | MRT, jeepney, Grab backseat |
| WEEKEND_GROUP | Friends outing, 2–3 people | Intramuros, Tagaytay Picnic Grove, Nuvali |
| REVIEW_UNBOX | Just arrived energy | Home — bedsheet, table, couch |
| SUNSET_VIBE | Golden hour flex | Manila Bay, rooftop, ridgeline |

---

## Phase A — Plan the Batch

Creates entries in `.tmp/ugc_pipeline.json` with `status=PENDING`.

```bash
# 5 images, mixed scenarios — 9:16 portrait by default
python tools/pipeline/run_ugc.py --plan --count 5

# 3 beach images — still 9:16 by default
python tools/pipeline/run_ugc.py --plan --count 3 --scenario BEACH_CANDID

# Override to 4:5 feed format if needed
python tools/pipeline/run_ugc.py --plan --count 3 --ratio 4:5

# With optional notes for the prompt writer
python tools/pipeline/run_ugc.py --plan --count 4 --notes "Tagaytay trip vibe"
```

**Output:** `ugc_pipeline.json` entries, status `PENDING`. Runner prints the scenario mix for review.

Review the planned entries before proceeding. Adjust `ugc_pipeline.json` manually if needed
(change scenario, gender, notes).

---

## Phase B — Write UGC Prompts

Run the `dubery-ugc-prompt-writer` skill to process all `PENDING` entries.

Trigger in Claude: just say **"write UGC prompts"** or **"run dubery-ugc-prompt-writer"**.

The skill will:
1. Read all `PENDING` entries from `ugc_pipeline.json`
2. Run internal analysis per entry (scene, subject, camera simulation)
3. Write a Dense Narrative NB2 prompt to `.tmp/{id}_ugc_prompt.json`
4. Update `ugc_pipeline.json`: `status=PROMPT_READY`

**Output:** `.tmp/UGC-YYYYMMDD-NNN_ugc_prompt.json` files, status `PROMPT_READY`.

---

## Phase C — Generate Images

```bash
# Generate all PROMPT_READY UGC entries
python tools/pipeline/run_ugc.py --generate

# Generate specific IDs
python tools/pipeline/run_ugc.py --generate --ids UGC-20260318-001 UGC-20260318-002

# Skip review server (generate only)
python tools/pipeline/run_ugc.py --generate --no-review
```

The runner:
- Processes PROMPT_READY entries in parallel (max 3 workers)
- Calls `generate_kie.py` for each (kie.ai Nano Banana 2)
- Downloads image to `output/ugc/ugc_{id}.jpg`
- Backs up to Google Drive folder: `DuberyMNL/UGC Images/`
- Updates `ugc_pipeline.json`: `status=DONE`, `drive_url`
- Starts image review server at `http://localhost:5001`

**Logs:** `.tmp/ugc_{id}.log` per image

---

## Review and Approval

The review server serves UGC images for approve/reject/skip.

```bash
python tools/image_gen/image_review_server.py --ugc
```

- **Approve** → `status=IMAGE_APPROVED`
- **Reject** → moved to `.tmp/ugc_rejected.json`, image moved to `output/ugc/rejected/`
- **Skip** → stays DONE, reappears next session

---

## Output Locations

| Item | Location |
|---|---|
| Generated images | `output/ugc/ugc_{id}.jpg` |
| Rejected images | `output/ugc/rejected/ugc_{id}.jpg` |
| Google Drive | `My Drive/DuberyMNL/UGC Images/` |
| Pipeline store | `.tmp/ugc_pipeline.json` |
| Prompt files | `.tmp/{id}_ugc_prompt.json` |
| Generation logs | `.tmp/ugc_{id}.log` |

---

## Status Flow

```
PENDING
  → (dubery-ugc-prompt-writer skill)
PROMPT_READY
  → (run_ugc.py --generate)
GENERATING → DONE
  → (image_review_server.py --ugc)
IMAGE_APPROVED | IMAGE_REJECTED
```

---

## Edge Cases

**NB2 still looks too polished:**
- First batch commonly needs prompt tuning. The negative prompt stack is aggressive,
  but NB2 has beauty bias.
- Fix: add more specific imperfections to the prompt (e.g., "slight motion blur on
  forearm, one highlight zone blown on forehead from direct sun").
- Check: if the image looks like a nice lifestyle photo, it's too polished.

**Stories ratio (9:16) framing:**
- At 9:16, the vertical space changes composition significantly.
- In Phase B, the skill adjusts framing: subject fills 60–70% of height,
  background compressed. Works best for SELFIE_OUTDOOR, CAR_SELFIE, SUNSET_VIBE.

**Product not visible or wrong:**
- `product_image_url` must be passed in the prompt's `image_input` field.
- If product looks wrong: re-run the prompt writer with a clearer reference URL.

**Drive upload fails (non-critical):**
- Image is saved locally and status is still set to DONE.
- Re-upload manually: `python tools/drive/upload_image.py --file output/ugc/ugc_{id}.jpg --folder "DuberyMNL/UGC Images"`

---

## Comparing UGC vs. WF2 Prompts

| | WF2 (Ad) | WF-UGC |
|---|---|---|
| Goal | Facebook ad conversion | Organic social proof |
| Overlays | Price, logo, delivery bar | None |
| Camera | Professional DSLR energy | Smartphone, ISO 400–640 |
| Imperfections | Minimal | Compression, blown highlights, slight blur |
| Composition | Rule of thirds, centered | Slightly off, candid |
| Setting | Curated Philippine location | Named casual spot |
| Negative prompt | Avoid stock photo look | Block all studio/ad aesthetics |
