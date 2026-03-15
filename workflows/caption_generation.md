# WF1 — Caption Generation

## Objective
Generate a fresh batch of 15 on-brand captions for DuberyMNL Facebook content, write them to Google Sheets, start the local review server, and email RA the review link.

## Trigger
RA runs Claude Code and says: *"Generate captions for this week"* (or similar)

## Required Inputs
- Google Sheets access (credentials.json + token.json)
- `GOOGLE_SHEETS_SPREADSHEET_ID` in `.env`
- `GMAIL_SENDER`, `GMAIL_APP_PASSWORD`, `REVIEW_EMAIL_RECIPIENT` in `.env`
- Brand reference data in the `brand` sheet

---

## Steps

### Step 1 — Load brand reference
```
python tools/sheets/read_sheet.py --sheet brand
```
Parse into a key-value dict. Key fields:
- `single_price` — ₱699
- `bundle_price` — ₱1,200 for 2 pairs
- `pricing_rule`, `never_say`, `delivery`
- `language_ratio` — 60% English / 40% Tagalog
- `vibes` — full list of 17 content vibes
- `caption_quotas` — 10 product-anchored, 5 bundle, 3 elevated tone
- `hashtags` — fixed set
- `cta_phrases` — available CTAs to choose from per vibe
- `product_models` — Classic, Outback, Bandits, Rasta
- `target_market`

If brand sheet is missing or empty: stop and tell RA to run `python tools/sheets/setup_spreadsheet.py` first.

---

### Step 2 — Load calibration data
```
python tools/sheets/read_sheet.py --sheet captions --filter "Status=APPROVED"
python tools/sheets/read_sheet.py --sheet rejected_captions
```
Use the **last 10 APPROVED** and **last 10 REJECTED** rows to calibrate tone, length, and style.

From approved history extract:
- Which vibes got approved most
- What opening hooks appeared in approved captions
- Caption length patterns that dominate approvals

From rejected history extract:
- Phrases or structures that keep getting rejected
- Vibes or tones that consistently fail → treat as avoidance list

If no history exists, skip calibration and proceed.

---

### Step 3 — Web research (do before generating)
Search for:
- `"Angkas Philippines Facebook posts captions 2025 2026"`
- `"Philippines sunglasses brand Facebook posts 2025 2026"`
- `"Filipino brand kanto-chic social media captions"`

**Angkas is the gold standard voice reference:**
- Short (1–3 lines), self-deprecating, meta, meme-aware
- "Sabog pero brillante" — chaotic energy but extremely intentional
- Masters of "ikaw yung tao na..." identity hooks

Also note what PH sunglasses sellers (Sunnies Studios, local sellers) are doing — what hooks, formats, and slang are getting engagement right now.

Extract 3–5 observations. Use them to inform style this batch. Do not copy directly.

---

### Step 4 — Select 10 vibes for this batch

**17-vibe library:**
1. Commuter / NCR Streets
2. Outdoor / Trail + Adventure
3. Urban / Streetwear
4. Lifestyle / Pinoy Culture
5. Mirror Selfie / Glow Up
6. New Haircut / Barbershop
7. Content Creator / Reels Energy
8. Motovlogger
9. Moto Camping
10. Palenke / Market Day
11. Church / Sunday Vibes
12. Walking the Dog
13. Cat Parent Vibes
14. Toddler / Young Parent
15. Teenager / Gen Z
16. Chaos Energy (Bahala Na Sila)
17. Sale / Urgency

**Selection rules:**
- Pick any 7–8 from the library
- Avoid repeating vibes used in the last 2 batches (check recent `Generated_At` timestamps)
- Aim for variety: mix commuter, lifestyle, sub-culture, product-forward, and sale vibes
- Declare selected vibes in the JSON output as `selected_vibes`

---

### Step 5 — Generate captions

Generate **1–2 captions per selected vibe = 15 captions total**. Distribute unevenly as needed — prioritize vibes with more potential for that batch.

**Global quotas (apply across all captions):**
- **PRODUCT quota**: ~50% of captions = `visual_anchor: "PRODUCT"`. Caption centers on the product in a scene, not a person.
- **PERSON quota**: remaining ~50% = `visual_anchor: "PERSON"`. Caption centers on a human experience.
- **Bundle quota**: exactly 3 captions must feature ₱1,200 / 2 pairs. Spread across 3 different vibes. Frame as "dalawang pairs", "share with your buddy", "one for you, one for your lodi".
- **Elevated tone quota**: 2–3 captions must use composed, polished tone — not kanto-chic, not corporate. One clean line that hits differently.
- **Language ratio**: 60% English / 40% Tagalog — STRICT. Count words. Hard rule, do not drift.
- **Emojis**: at least 1, max 2 per caption. Never zero, never excessive.
- **CTA**: every caption ends with a CTA on its own line before hashtags. Choose CTA from `cta_phrases` based on vibe tone. Urgent vibes (Sale/Urgency, product launches) → urgent CTA ("Order na ngayon", "DM us now"). Lifestyle/culture vibes → softer CTA ("Message us", "Grab yours"). Never hardcode the same CTA across all captions.
- **Hashtags**: always `#DuberyMNL #PolarizedSunglasses #DuberyOptics #CODMetroManila #SameDayDelivery`
- **Hook variety**: vary opening format across the batch — POV, question, quote, statement, identity hook. No two captions in the same vibe start the same way.

**Never say:**
- ₱799, ₱1,300 (total-with-delivery prices)
- "Free shipping" / "Nationwide" / "PM is key"
- "Experience our polarized technology" or any corporate-sounding feature sentence
- Address terms (pre, pare, kuya, ate, beh, etc.) — do NOT use
- Inner arm detail — do NOT mention

**Always:**
- Write like a brilliant friend from Metro Manila who understands human behavior AND wears Dubery every day
- Never like a marketing agency. Never like a press release.
- Caption length is dynamic — calibrate from approved history. Short when that wins. Longer when that wins. Vary length across the batch.

**Output format — valid JSON only, nothing else:**
```json
{
  "selected_vibes": ["Vibe1", "Vibe2", "...", "Vibe10"],
  "captions": [
    {
      "id": 1,
      "vibe": "Vibe1",
      "visual_anchor": "PERSON",
      "caption_text": "caption body here\n\nGrab yours!",
      "hashtags": "#DuberyMNL #PolarizedSunglasses #DuberyOptics #CODMetroManila #SameDayDelivery"
    }
  ]
}
```

`visual_anchor` values: `"PERSON"` or `"PRODUCT"` only.

---

### Step 6 — Write captions to .tmp/captions.json

Google Sheets is NOT written to during processing. captions.json is the primary working store. Sheets is written only after the full pipeline completes (WF3).

Generate a unique ID per caption: `YYYYMMDD-001`, `YYYYMMDD-002`, etc.

Append each caption to `.tmp/captions.json` as a full entry preserving all WF1 fields:

```json
{
  "id": "YYYYMMDD-001",
  "generated_at": "[ISO datetime]",
  "angle": "[Pain Relief | Identity | Lifestyle | Status/Glow Up | Value/Deal | Convenience/Fast Delivery]",
  "hook_type": "[Question | POV | Identity | Pain | Flex | Speed | Price Shock | Statement]",
  "vibe": "[vibe]",
  "creative_hypothesis": "[one-line hypothesis]",
  "visual_anchor": "[PERSON | PRODUCT]",
  "caption_text": "[caption body]",
  "hashtags": "[hashtags]",
  "status": "PENDING",
  "notes": "",
  "rating": null,
  "recommended_products": "",
  "overlays": "",
  "prompt": "",
  "image_url": ""
}
```

If `.tmp/captions.json` already exists, load it and append. Do not overwrite existing entries.

---

### Step 7 — Start review server
```
bash tools/captions/start_review.sh
```
Starts the review server + ngrok tunnel. Prints a public URL (e.g. `https://abc123.ngrok-free.app`) that RA can open on his phone. Server shuts down automatically after RA submits the review.

---

### Step 8 — Send review email
```
python tools/captions/send_review_email.py --count [N] --vibes "[vibe1, vibe2, ...]"
```
Sends RA an email with the review link and vibe summary.

---

### Step 9 — Report to RA
Output:
```
✓ [N] captions written to .tmp/captions.json.

Vibes this batch: [list of 10 vibes]

Review server live at: [ngrok URL printed above — open on phone]
Email sent to [REVIEW_EMAIL_RECIPIENT].

Keep this terminal open. The review server will shut down after you submit.
```

---

## Edge Cases
- **Brand sheet missing or empty**: Stop. Tell RA to run `python tools/sheets/setup_spreadsheet.py` first.
- **No approved/rejected history**: Skip calibration step, proceed with brand rules only.
- **captions.json missing**: Create it as an empty array `[]` before appending.
- **Caption count falls short of 15**: Generate additional captions rather than skipping required quotas.
- **Review server port 5000 in use**: Check if a previous server is still running — kill it first, then start fresh.

---

## Output
- 15 new entries appended to `.tmp/captions.json` with `status=PENDING`
- Local review server running at `http://localhost:5000`
- Email sent to RA with review link
- Google Sheets is NOT written at this stage — final archive write happens after WF2 completes and image is approved (WF3)
