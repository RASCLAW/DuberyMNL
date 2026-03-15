# WF2 — Image Prompt Generation + Image Generation

## Overview

Split into two phases. Phase 1 is the current active build. Phase 2 is wired up later when going fully agentic.

```
WF2a — Prompt Writer  →  saves prompts to .tmp/captions.json  →  STOP
WF2b — Image Generator  →  triggered separately by RA  →  generates image  →  saves image_url to .tmp/captions.json
```

---

## WF2a — Prompt Writer

### Trigger
RA says: *"Write prompts for approved captions"* (or similar)

### Required Inputs
- `.tmp/captions.json` with at least one entry where `status=APPROVED` and `prompt` is empty

### Selection Logic
1. Load `.tmp/captions.json`
2. Collect all entries where `status=APPROVED` and `prompt` is empty
3. Filter to 5-star pool (`rating=5`) -- pick one at random
4. If 5-star pool is empty, fall back to 4-star pool (`rating=4`) -- pick one at random

### Steps

**1. Read captions pool from .tmp/captions.json**
Load the file, filter to entries where `status=APPROVED` and `prompt=""`. Apply rating-based random selection.

**2. For each caption — compose NB2 prompt**
Apply the `dubery-prompt-writer` skill.

Inputs read from each entry:
- `caption_text` — approved caption text
- `angle` — persuasion strategy from WF1
- `vibe` — scene/lifestyle context
- `visual_anchor` — PERSON or PRODUCT
- `notes` — RA's image direction brief (scene, mood, setting)
- `recommended_products` — maps to reference image URLs
- `overlays` — comma-separated checked overlays from review

**3. Save prompt to .tmp/captions.json**
Write the generated prompt to the `prompt` field for that entry.
Update `status` → `PROMPT_READY`.
Do NOT write to Google Sheets at this stage.

**4. Report to RA**
List all captions processed with their IDs and a one-line summary of the content type chosen.
Tell RA: "Prompts written to captions.json. Test in Gemini/NB2. Say 'generate images' when ready."

---

## WF2b — Image Generator

### Trigger
RA says: *"Generate images"* (or similar)

### Required Inputs
- `.tmp/captions.json` with at least one entry where `status=PROMPT_READY`
- `KIE_API_KEY` in `.env`

### Steps

**1. Read PROMPT_READY entries from .tmp/captions.json**
Load the file, filter to entries where `status=PROMPT_READY`.

**2. Generate image**
Build the kie.ai JSON payload from the saved prompt + reference image URLs:
```json
{
  "prompt": "[prompt from captions.json prompt field]",
  "image_input": ["[reference image URL(s) from recommended_products]"],
  "api_parameters": {
    "aspect_ratio": "4:5",
    "resolution": "1K",
    "output_format": "jpg"
  }
}
```
Run:
```
python tools/image_gen/generate_kie.py --input .tmp/[caption_id]_prompt.json
```
Poll for completion via `tools/image_gen/get_kie_image.py`.

**3. Upload to Google Drive**
```
python tools/drive/upload_image.py --file .tmp/[caption_id].jpg --folder-id 1N3lH4GE7EPUQBIcojYDwdPkPUJKoXp_y
```
Returns `drive_url`.

**4. Write image_url to .tmp/captions.json and update status**
Update the entry in captions.json:
- `image_url` → Drive URL
- `status` → `DONE`

Do NOT write to Google Sheets at this stage.

---

## Edge Cases
- **No approved captions**: Tell RA: "No approved captions found. Review pending captions first."
- **Prompt already filled**: Skip that entry — do not overwrite.
- **notes field empty**: Proceed with caption + vibe alone. Do not block.
- **recommended_products empty**: Default to Classic - Black as reference image.

## Final Archive (WF3)
After WF2b completes and RA approves the generated image, write all `status=DONE` entries from `.tmp/captions.json` to Google Sheets as the final archive. This is the only time Sheets is written during the pipeline.
