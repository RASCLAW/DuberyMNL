# WF4 — Lead Capture

## Objective
Collect leads from the DuberyMNL landing page form, save them to Google Sheets, and prepare personalized follow-up messages for RA to send.

## Trigger
RA runs Claude Code and says: *"Process new leads"* (or similar)

## Required Inputs
- Google credentials (credentials.json + token.json)
- `GOOGLE_SHEETS_SPREADSHEET_ID` in `.env`
- Leads already in the `leads` sheet (populated by Tally.so form integration)

## One-Time Setup (Do Once)

### 1. Create the landing page form
Use [Tally.so](https://tally.so) (free):
1. Create a new form with fields: Name, Phone, Email (all required)
2. Add a hidden field `source` = `landing_page`
3. In Tally integrations → connect to Google Sheets → select the DuberyMNL Master spreadsheet → map to the `leads` sheet
4. Tally will auto-write: Timestamp, Name, Phone, Email, Source

### 2. Set up the Carrd landing page
1. Create a Carrd.co page for DuberyMNL
2. Add a form block or embed the Tally form via iframe
3. Include: product photo, tagline, CTA ("Order na / Get your pair")
4. Link to `facebook.com/duberymnl` for social proof
5. Publish the Carrd page and share the URL in the Facebook Page bio + ad captions

### 3. Seed the leads sheet
Verify the `leads` sheet has these headers (already seeded by setup_spreadsheet.py):
```
Timestamp | Name | Phone | Email | Source | PSID | Status | Notes
```
Tally writes to: Timestamp, Name, Phone, Email, Source
Set initial `Status` = `NEW` (can configure in Tally or update manually)

---

## Steps (Run When RA Asks)

### 1. Fetch new leads
Run:
```
python tools/sheets/read_sheet.py --sheet leads --filter "Status=NEW"
```

### 2. For each new lead — draft follow-up message
Write a personalized Messenger/SMS follow-up message:

**Template (Filipino-English mix):**
```
Hi [Name]! 😎 Salamat sa interest mo sa DuberyMNL shades!

Narito ang aming pinakabagong styles at presyo:
• Single pair: ₱[price]
• Bundle ng 5: ₱1,200 lang!

Available in [list key models]. Pwede kang pumili ng color at style.

Para mag-order, i-DM mo lang kami dito sa Facebook o mag-reply sa message na ito ng:
"Gusto ko ng [model] [color]"

Salamat ulit! 🙌 — DuberyMNL Team
```

Customize per lead if Notes or Source give context (e.g. "from commuter ad" → mention commuter-relevant style).

### 3. Update leads sheet
Run:
```
python tools/sheets/write_sheet.py --sheet leads --action update \
  --filter "Phone=[phone]" \
  --data '{"Status":"CONTACTED","Notes":"Follow-up drafted [date]"}'
```

### 4. Report to RA
```
✓ [N] new leads processed.

Follow-up messages to send:

---
Lead: [Name] | [Phone] | Source: [source]
Message:
[drafted message]
---
Lead: [Name] | [Phone] | Source: [source]
Message:
[drafted message]
---

Send these via Facebook Messenger (search the phone number) or SMS.
After sending, the leads are already marked as CONTACTED in the sheet.
```

## Lead Status Lifecycle
| Status | Meaning |
|--------|---------|
| NEW | Just captured, not yet processed |
| CONTACTED | Follow-up message drafted / sent by RA |
| INTERESTED | Lead replied, actively interested |
| ORDERED | Converted to sale |
| COLD | No response after follow-up |

RA updates Status manually in Google Sheets as leads progress.

## Edge Cases
- **No new leads**: Tell RA: "No new leads found. Check if the Tally form is connected to the sheet."
- **Duplicate phone numbers**: Skip duplicates (check if phone already exists in sheet before drafting).
- **Missing name or phone**: Flag to RA — "Lead from [timestamp] is missing [field]. Check Tally form settings."

## Future Enhancements (Phase 2)
- Messenger bot: auto-reply to DMs and comments using Meta Graph API
- PSID capture: link Messenger interactions to leads in the sheet
- Auto-send follow-up via Messenger API instead of manual sending
