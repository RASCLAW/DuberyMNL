# WF3 — Ad Publishing

## Objective
Take approved images and their captions, create PAUSED Meta Ads campaigns for RA to review, then let RA activate them directly in Meta Ads Manager.

## Trigger
RA runs Claude Code and says: *"Stage ads for ready images"* (or similar)

## Required Inputs
- `META_ADS_ACCESS_TOKEN` in `.env`
- `META_AD_ACCOUNT_ID` in `.env` (format: `act_XXXXXXXXX`)
- `META_PAGE_ID` in `.env`
- At least one row in `images` with `Status=READY`

## Prerequisites
Complete `workflows/meta_setup.md` before running this workflow for the first time.

## Steps

### 1. Fetch images ready for ads
Run:
```
python tools/sheets/read_sheet.py --sheet images --filter "Status=READY"
```
Cross-reference with `ad_drafts` sheet to exclude images already staged:
```
python tools/sheets/read_sheet.py --sheet ad_drafts
```
Filter out Image_IDs already present in `ad_drafts`. Process only new ones.

### 2. For each new image — get caption
Look up the caption using `Caption_ID` from the `images` row:
```
python tools/sheets/read_sheet.py --sheet captions
```
Find the row where `ID = Caption_ID`. Extract: Caption text, Vibe, Visual_Anchor.

### 3. Upload image to Meta Ads creative library
Run:
```
python tools/meta_ads/upload_creative.py --file .tmp/[image_id].jpg --ad-account-id [META_AD_ACCOUNT_ID]
```
If the image is not in `.tmp/`, download it from Drive first using the `Drive_URL`.

Returns: `image_hash`

### 4. Create PAUSED campaign
Run:
```
python tools/meta_ads/create_campaign.py \
  --name "DuberyMNL - [Vibe] - [YYYYMMDD]" \
  --caption "[caption text]" \
  --image-hash "[hash]" \
  --ad-account-id "[META_AD_ACCOUNT_ID]" \
  --page-id "[META_PAGE_ID]"
```

Campaign settings:
- Status: PAUSED (RA activates manually)
- Objective: OUTCOME_TRAFFIC
- Targeting: Philippines, age 18-45, interests: [Sunglasses, Fashion accessories, Motorcycle, Commuting]
- Placement: Facebook Feed + Instagram Feed
- Budget: Daily budget ₱200 (default — RA can adjust in Ads Manager)

Returns: `campaign_id`

### 5. Log to ad_drafts sheet
Run:
```
python tools/sheets/write_sheet.py --sheet ad_drafts --action append \
  --data '{"ID":"AD-[timestamp]","Caption_ID":"[id]","Image_ID":"[image_id]","Drive_URL":"[url]","Campaign_ID":"[campaign_id]","Ad_Name":"DuberyMNL - [Vibe] - [date]","Status":"STAGED","Created_At":"[ISO datetime]","Launched_At":""}'
```

### 6. Report to RA
```
✓ [N] ad campaigns staged in Meta Ads Manager (status: PAUSED).

Staged ads:
- [Vibe] — Campaign ID: [id] → [direct Ads Manager link]
- [Vibe] — Campaign ID: [id] → [direct Ads Manager link]
...

Next step: Go to Meta Ads Manager, review each campaign, then click "Publish" on the ones you want to run.

Meta Ads Manager: https://www.facebook.com/adsmanager/manage/campaigns?act=[META_AD_ACCOUNT_ID]
```

After you publish a campaign, update the `ad_drafts` sheet:
- Set `Status` = `LIVE`
- Set `Launched_At` = launch date

## Edge Cases
- **Meta API token expired**: Stop. Tell RA to refresh the token (see `workflows/meta_setup.md` — Token Refresh section).
- **Image upload fails**: Skip that image, report error, continue with others.
- **Ad account not found / permissions error**: Stop. Tell RA to verify `META_AD_ACCOUNT_ID` and token permissions.
- **No ready images**: Tell RA: "No images with Status=READY found. Run image generation first."

## Output
New rows in `ad_drafts` with `Status=STAGED`.
PAUSED campaigns visible in Meta Ads Manager, ready for RA to activate.
