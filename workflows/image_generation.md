# WF2 — Image Generation

## Objective
For each APPROVED caption, generate an AI ad image using kie.ai, upload it to Google Drive, and log the result in the `images` sheet.

## Trigger
RA runs Claude Code and says: *"Generate images for approved captions"* (or similar)

## Required Inputs
- `KIE_AI_API_KEY` in `.env`
- Google credentials (credentials.json + token.json)
- `GOOGLE_SHEETS_SPREADSHEET_ID` in `.env`
- At least one caption with `Status=APPROVED` in the `captions` sheet

## Steps

### 1. Fetch approved captions not yet imaged
Run:
```
python tools/sheets/read_sheet.py --sheet captions --filter "Status=APPROVED"
```
Cross-reference with the `images` sheet to find captions without a corresponding image:
```
python tools/sheets/read_sheet.py --sheet images
```
Filter out Caption_IDs already present in `images`. Process only new ones.

### 2. For each unimaged caption — write image prompt
Analyze the caption:
- What is the core message / emotion?
- What does `Visual_Anchor` say — PERSON or PRODUCT?
- What vibe is it (from `Vibe` column)?

Write a kie.ai image generation prompt following these rules:

**Content type based on Visual_Anchor:**
- `PERSON` → person wearing DuberyMNL sunglasses in a scene matching the vibe. Face partially visible or obscured by shades. Metro Manila / Philippine setting. Natural light.
- `PRODUCT` → sunglasses on a surface or floating, styled shot. Clean background or matching vibe environment. No people.

**Prompt structure:**
```
[Shot type], [subject with product], [vibe/scene], [lighting], [style], [aspect ratio: 4:5], [no text in image]
```

**Hard rules:**
- Always: 4:5 aspect ratio (mobile vertical)
- Always: photo-realistic, not illustration
- No text overlaid in the image (text will be added in post)
- If PERSON: shades must be on the face and visible
- Philippine/Metro Manila setting where appropriate
- No generic stock-photo feel — scene must match the vibe specifically

**Example prompt (commuter vibe, PERSON anchor):**
```
Street-level shot, young Filipino man wearing wraparound sunglasses on an LRT platform, Manila rush hour crowd in background slightly blurred, golden hour light, candid urban fashion photography style, 4:5 vertical, photorealistic, no text
```

### 3. Generate image via kie.ai
Run:
```
python tools/image_gen/generate_image.py --prompt "[prompt]" --output .tmp/[caption_id].jpg
```
This script:
- Submits job to kie.ai API
- Polls until complete (up to 10 retries, 30 seconds apart)
- Saves result to `.tmp/[caption_id].jpg`

If generation fails after retries: log the error, skip this caption, continue with the rest. Report failures at the end.

### 4. Upload to Google Drive
Run:
```
python tools/drive/upload_image.py --file .tmp/[caption_id].jpg --folder DuberyMNL/Images
```
Returns `drive_url` and `drive_file_id`.

### 5. Log to images sheet
Run:
```
python tools/sheets/write_sheet.py --sheet images --action append \
  --data '{"ID":"IMG-[timestamp]","Caption_ID":"[id]","Prompt":"[prompt]","Drive_URL":"[url]","Drive_File_ID":"[file_id]","Generated_At":"[ISO datetime]","Status":"READY"}'
```

### 6. Report to RA
```
✓ [N] images generated and uploaded to Google Drive.

Summary:
- [Caption ID] → [Drive URL]
- [Caption ID] → [Drive URL]
...

[If failures:]
⚠ Failed: [Caption ID] — [error reason]

Next step: Review images in Google Drive, then say "Stage ads for ready images" to create Meta Ads campaigns.

Drive folder: https://drive.google.com/drive/folders/[FOLDER_ID]
```

## Edge Cases
- **kie.ai job times out**: Skip caption, report as failed. Do not block other images.
- **Drive upload fails**: Retry once. If still fails, skip and report.
- **No approved captions**: Tell RA: "No approved captions found. Review the `captions` sheet first."
- **All captions already imaged**: Tell RA: "All approved captions already have images. Approve more captions or generate a new batch."

## Output
New rows in `images` sheet with `Status=READY` and Google Drive links.
Cleaned up `.tmp/` files after upload.
