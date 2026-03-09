# WF1b — Caption Review

## Objective
RA reviews generated captions in a local Facebook-style UI, edits them inline, rates with stars, adds feedback notes, and submits. Approved captions advance to image generation (WF2). Rejected captions are stored for agent calibration on the next run.

## Trigger
Automatically started at the end of WF1 (caption generation). RA receives an email with the review link.

## Required Inputs
- WF1 completed — captions written to Google Sheets with `Status=PENDING`
- Review server running at `http://localhost:5000`
- Terminal open (server must stay running during review)

---

## Steps (RA Action)

### 1. Check your email
Look for: **"DuberyMNL — X captions ready for review"**
- Subject includes the caption count
- Body lists the vibes and the link: `http://localhost:5000`
- Reminder: keep the terminal open

### 2. Open the review page
Navigate to: `http://localhost:5000`

You'll see a grid of Facebook post mockup cards — one per pending caption.

### 3. Review each card

**Each card contains:**
- Page header: DuberyMNL name + vibe badge
- Image placeholder zone with **visual anchor toggle** button (top-right of image area)
- Editable caption text (click to edit)
- Editable hashtags (click to edit)

**Actions per card:**

| Action | How | What it does |
|--------|-----|--------------|
| Edit caption | Click caption text → type | Saves your edited version (not the original) |
| Edit hashtags | Click hashtag line → type | Saves your edited hashtags |
| Toggle visual anchor | Click `👤 PERSON` / `📦 PRODUCT` button | Switches between PERSON and PRODUCT; saved value is what you see on submit |
| Rate caption | Hover over 👍 Like → star popup appears → click a star | ★1–5; ≥3 = APPROVED, <3 = REJECTED |
| Add feedback | Hover over 💬 Comment → type in field | Saved as Notes for agent calibration next run |
| Share | Click ↗ Share | Placeholder — no function |

### 4. Submit
Click **Submit All** when all cards are rated.

- If any card is unrated, the button will warn you and scroll to the first unrated card
- On submit: all data (edited caption, hashtags, visual anchor, rating, status, notes) is written back to Google Sheets
- Server shuts down automatically
- Confirmation shows: "X approved · Y rejected"

---

## What Gets Saved to Google Sheets

| Column | Value saved |
|--------|-------------|
| Caption | Edited caption text (or original if not edited) |
| Hashtags | Edited hashtags (or original if not edited) |
| Visual_Anchor | Toggled value at time of submit |
| Rating | Star rating (1–5) |
| Status | APPROVED (≥3 stars) or REJECTED (<3 stars) |
| Notes | Comment / feedback text |

---

## After Review

**APPROVED captions** → ready for WF2 (Image Generation)
- Run: `python tools/sheets/read_sheet.py --sheet captions --filter "Status=APPROVED"`
- Hand approved caption IDs to WF2

**REJECTED captions** → stored for calibration
- Agent reads last 10 REJECTED on next WF1 run
- Uses them as avoidance patterns (phrases, structures, vibes that failed)
- Notes column is also read — direct feedback for the agent to learn from

---

## Edge Cases

- **Review server not running**: Start it manually → `python tools/captions/review_server.py`
- **Port 5000 in use**: Kill the old process → `lsof -ti:5000 | xargs kill -9` → restart
- **Submitted but Sheets not updated**: Check terminal for error message; re-run submit or update manually in Sheets
- **Want to re-review**: Change `Status` back to `PENDING` in Google Sheets, restart the server

---

## Output
All pending captions updated in `captions` sheet with Status=APPROVED or REJECTED.
