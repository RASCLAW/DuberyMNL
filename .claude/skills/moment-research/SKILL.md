---
name: moment-research
description: Daily DuberyMNL "Moment Scout" — research upcoming PH holidays, sports/events, and viral/weather moments relevant to sunglasses, score them, write a sunglasses angle, write suggestions to the content calendar, and send the morning Telegram digest. Suggest-only; RA approves angles. Run daily (cloud routine / Task Scheduler) or on demand.
---

# DuberyMNL Moment Scout (daily content-calendar researcher)

Keeps DuberyMNL content from going stale by surfacing timely moments **before** their window opens. Writes to the `content_calendar` Sheet tab via the `tools/moments/` helpers, then sends a Telegram digest. **You only ever SUGGEST** — never set status to approved/posted, never generate or publish content. RA approves angles in the Command Center.

## What to track
- **Holidays & observances** (PH) — mostly seeded as fixed anchors; your job is to verify variable-date ones.
- **Sports & events** — PBA, Gilas (FIBA windows), NBA, MPL esports, major concerts/festivals in PH. Short windows, easy to miss.
- **Viral trends & weather** — Google Trends PH, TikTok/X moments that fit fashion/lifestyle/sunglasses; PAGASA heat-index spikes, typhoon/rainy spells (drives the polarized "glare" counter-angle).

Do NOT track ecommerce mega-sales (RA excluded them).

## Flow

1. **Materialize fixed anchors.** Run:
   `python tools/moments/seed_from_anchors.py --live`
   (deterministic; brings any PH anchor entering the ~120-day horizon into the calendar, idempotent).

2. **Load current calendar** to avoid duplicates and see what's already there:
   `python tools/moments/list_moments.py --json`

3. **Verify variable-date anchors.** For any anchor row whose `notes` says "variable" (Holy Week, Father's/Mother's Day, Sinulog/Ati-Atihan), WebSearch the exact date for the current year and, if the window is wrong, correct it:
   `python tools/moments/upsert_moment.py --data '{"id":"<existing-id>","window_start":"YYYY-MM-DD","window_end":"YYYY-MM-DD","notes":"verified"}'`
   (If the corrected start date changes, prefer dismissing the mis-dated row by upserting `"status":"dismissed"` and adding a correctly-dated new row, so the id stays `{window_start}-{slug}`.)

4. **Research dynamic moments** (horizon ~60–90 days from today). Run a few targeted WebSearches per lane:
   - sports: upcoming PBA / Gilas / FIBA window / NBA milestone / MPL PH dates in the next 2–3 months
   - trends: current PH viral / TikTok / Google Trends moments that a sunglasses brand could ride
   - weather: PAGASA seasonal outlook, heat-index spikes, incoming typhoons/habagat spells
   Keep only what a sunglasses brand can authentically join.

5. **Score & write the angle.** For each kept moment, decide:
   - `relevance` 1–10 = how naturally sunglasses fit (be honest; a stretch is a 3–4, not a 7).
   - `angle` = the specific sunglasses hook to shoot (lead with English, natural Taglish only where it fits — see the brand voice rules).
   - `format` = ugc-story | single | carousel | video.
   - `window_start` = when to START posting (give real lead time); `window_end` = the peak/day.
   - `type` = holiday | event | trend | weather.

6. **Upsert suggestions** (one call per moment), `source=researcher`, `status=suggested`, `id = {window_start}-{slug}`:
   `python tools/moments/upsert_moment.py --data '{"id":"2026-08-10-gilas-fiba-window","title":"Gilas FIBA window","type":"event","window_start":"2026-08-10","window_end":"2026-08-18","relevance":"7","angle":"...","format":"ugc-story","source":"researcher","status":"suggested","added":"<today>","lead_time_days":"<days>"}'`
   - **Cap ~6–8 new dynamic suggestions per run** — quality over noise. Skip anything already in the calendar (dedup by id / same moment).

7. **Send the digest:**
   `python tools/moments/send_digest.py`
   (add `--dry-run` when testing).

## Rules
- **Suggest-only.** Never set `approved`/`posted`, never call image/video generation, never post to Meta. RA owns approval.
- **Be honest about relevance.** Low-fit moments get low scores or are skipped — a stale-but-on-trend post still has to make sense for sunglasses.
- **Brand voice** for angles: English-led, natural Taglish, authentic/relatable, not corporate. (See the DuberyMNL voice rules / chatbot persona.)
- **Dedup.** Always load the calendar (step 2) first; don't re-add a moment that already exists.
- **No secrets in output.** The digest goes to RA's private TG channel only.

## Done when
- Fixed anchors are materialized + variable ones verified.
- ≤8 fresh, honestly-scored dynamic moments added as `suggested`.
- The Content Radar digest has been sent (or printed, in dry-run).
