# WF2 — Image Prompt Generation + Image Generation

## Overview

Split into two phases. Phase 1 is the current active build. Phase 2 is wired up later when going fully agentic.

```
WF2a — Prompt Writer  →  saves prompts to captions sheet  →  STOP
WF2b — Image Generator  →  triggered separately by RA  →  generates image  →  saves Image_URL
```

---

## WF2a — Prompt Writer

### Trigger
RA says: *"Write prompts for approved captions"* (or similar)

### Required Inputs
- Google credentials (credentials.json + token.json)
- `GOOGLE_SHEETS_SPREADSHEET_ID` in `.env`
- At least one caption with `Status=APPROVED`, `Image_Status=PENDING`, and empty `Prompt` column in the `captions` sheet

### Selection Logic
1. Collect all rows where `Status=APPROVED` and `Image_Status=PENDING` and `Prompt` is empty
2. Filter to 5-star pool (`Rating=5`) -- pick one at random
3. If 5-star pool is empty, fall back to 4-star pool (`Rating=4`) -- pick one at random

### Steps

**1. Read captions pool and select**
```
python tools/sheets/read_sheet.py --sheet captions --filter "Status=APPROVED"
```
Filter to rows where `Prompt` column (K) is empty and `Image_Status=PENDING`. Apply rating-based random selection.

**2. For each caption — compose NB2 prompt**
Apply the `dubery-prompt-writer` skill.

Inputs read from each row:
- `Caption` — approved caption text
- `Vibe` — scene/lifestyle context
- `Visual_Anchor` — PERSON or PRODUCT
- `Notes` — RA's image direction brief (scene, mood, setting)
- `Recommended_Products` — maps to reference image URLs
- `Overlays` — comma-separated checked overlays from review

**3. Save prompt to sheet**
Write the generated prompt to column K (`Prompt`) for that row.
Update `Status` → `PROMPT_READY`.
```
python tools/sheets/write_sheet.py --sheet captions --row [row_number] \
  --data '{"Prompt":"[prompt text]","Status":"PROMPT_READY"}'
```

**4. Report to RA**
List all captions processed with their IDs and a one-line summary of the content type chosen.
Tell RA: "Prompts saved. Check the captions sheet column K, then test in Gemini/NB2. Say 'generate images' when ready."

---

## WF2b — Image Generator

### Trigger
RA says: *"Generate images"* (or similar)

### Required Inputs
- Google credentials (credentials.json + token.json)
- `GOOGLE_SHEETS_SPREADSHEET_ID` in `.env`
- `KIE_API_KEY` in `.env`
- At least one caption with `Status=PROMPT_READY` in `captions` sheet

### Steps

**1. Read PROMPT_READY rows**
```
python tools/sheets/read_sheet.py --sheet captions --filter "Status=PROMPT_READY"
```

**2. Generate image**
Build the kie.ai JSON payload from the saved prompt + reference image URLs:
```json
{
  "prompt": "[prompt from sheet col K]",
  "image_input": ["[reference image URL(s) from Recommended_Products]"],
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

**4. Write Image_URL and update Image_Status**
```
python tools/sheets/write_sheet.py --sheet captions --row [row_number] \
  --data '{"Image_URL":"[drive_url]","Image_Status":"DONE"}'
```

---

## Edge Cases
- **No approved captions**: Tell RA: "No approved captions found. Review pending captions first."
- **Prompt column already filled**: Skip that row — do not overwrite.
- **Notes field empty**: Proceed with caption + vibe alone. Do not block.
- **Recommended_Products empty**: Default to Classic - Black as reference image.
