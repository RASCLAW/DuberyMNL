# March 2026

## 2026-03-20 -- Session 44

Big milestone day. The DuberyMNL Facebook ads content generator is working end-to-end.

One trigger ("generate content") kicks off the whole pipeline: 15 captions generated, reviewed on phone, then prompts, validation, and image generation all run automatically. 14 out of 14 images passed the gatekeeper on first attempt -- first time that's ever happened.

Hit an API 500 error mid-run that crashed the pipeline. Used that as an opportunity to add retry logic (3 attempts, 30s wait) and make the orchestrator resilient to partial failures. Rebuilt `run_post_review.py` to be batch-aware so it recovers gracefully instead of leaving orphaned captions.

Also started thinking about cloud deployment for scheduled runs and client work. Not building it yet but saved the plan. This is the kind of system that could be packaged as a service.

The portfolio piece is taking shape. Not just "I built a thing" but "I built a thing that runs itself."

Also tackled WF3b (Meta Ads staging). Learned how Meta Ads actually works -- campaigns, ad sets, ads, the budget structure. Discovered stage_ad.py was creating 1 campaign per caption (36 campaigns = P7,200/day). Restructured to 1 campaign, 1 ad set, N ads -- the way Meta recommends. Budget shared at P200/day across all ads. Ready for a real API test once the batch 20260320 images are reviewed.

Two big things done in one session. Content pipeline working, ads staging restructured. The system is getting close to portfolio-ready.

## 2026-03-21 -- Session 46

First real regeneration run. 15 images in the queue, ran through them with Claude as orchestrator -- writing prompts inline, calling generate_kie.py for the API work. The WAT pattern held: agent does creative, tools do execution.

13 out of 14 generated before kie.ai credits ran out. Reviewed all 14 (6 were reverted originals). 22 approved, 8 rejected. Five of the regen results weren't good enough. The lesson: NB2 edit prompts were too literal. "Fix the lens" doesn't work -- you need to describe what the whole image should look like, not just the delta. EDITs only work for simple text fixes. Everything else should be a full regen with a complete visual prompt.

Spent the second half of the session fixing sheet sync issues. The Approved sheet has 16 columns but the sync function was only writing 8 -- wrong schema. Also found duplicates everywhere because `_sync_to_sheet` was appending without checking if the row already existed. Fixed both: schema-aware row builder + dedup check before append.

Added an edit/regen toggle to the review page so the mode is explicit instead of auto-classified from keywords. Also added auto-sync -- when you finish reviewing all images, it triggers pipeline sync automatically.

All 60 entries accounted for. 36 approved, 24 rejected. Local and Drive perfectly synced. Pipeline is fully processed for the first time.

## 2026-03-22 -- Session 47

Long landing page session. Went from "functional but rough" to something that actually looks like a real product page.

Big changes: custom variant dropdown with product thumbnails, customer feedback section with auto-scrolling cards, swipeable polarized benefits, image preview with cart + Facebook buttons. Green accent from the bundle pricing ties everything together.

Also made a key architectural decision: Google Sheet is now the source of truth for manual data. I kept running into sync issues because sync_pipeline.py was overwriting my edits in the sheet. Now the flow is reversed -- I edit the sheet, Claude pulls from it. Makes way more sense since I'm always looking at the sheet anyway.

10 ads are selected and tagged. Landing page is filtered to just those 10. Next step is Vercel deploy and the real stage_ad.py run. Getting close to actually running paid ads.

Also got the car's brake drum regrooved today. Preparing for the Daet trip end of month with Arabelle and Jah.

## 2026-03-22 -- Session 47b

Late night landing page QC session. Went through every single ad in the preview, found and fixed a bunch of issues -- wrong descriptions, wrong card images, accent colors not working.

Spent a while figuring out the right color scheme. Tried green, blue, charcoal, then landed on Dubery's own red from the logo for accent badges, black for CTA buttons, and Facebook blue for social links. Simple but it works.

The variant dropdown now reorders based on the ad -- if the ad features Rasta Red, that shows up first in the picker. Disabled auto-populate too because seeing 4 items pre-filled with a P2,800 total is instant price shock.

Card titles cleaned up -- just "OUTBACK BLACK" instead of "DUBERY OUTBACK BLACK POLARIZED". Less noise.

Landing page is at 100% approval. Next is Vercel deploy and the first real ad run.

## 2026-03-22 -- Session 47c

Could not stop building. What started as "let me just check the desktop view" turned into a full desktop layout, dark mode, and a complete order UX overhaul.

Dark mode is default now. The products look so much better against dark backgrounds. Added a toggle in the corner that fades away on mobile after 15 seconds -- clean touch.

Built a two-column hero for desktop (ad image left, product card right). The rest stays single-column but centered at 1120px with dark margins. Looks intentional, not stretched.

The order form got two submit buttons -- regular and express delivery. The express one sends a flag so I know to prioritize. Added a heartbeat animation on the "add 1 more for free delivery" nudge and a green congrats box when they hit 2 pairs. Small things that make it feel alive.

Removed Google Places autocomplete -- it kept injecting Plus Codes and fighting with Chrome's autofill. Just using native browser suggestions now. Will confirm addresses on the call anyway.

Polarized benefits section has 6 cards now with emojis (added fishing -- big market in PH). Delivery section got emoji icons too. Everything centers properly on desktop.

This landing page is ready. Next: Vercel deploy and first real Meta ads run.

## 2026-03-22 -- Session 47d

Deployed to Vercel. duberymnl.vercel.app is live. Shared links with friends -- no more ngrok warning pages.

Submitted test orders and they landed in the Google Sheet. The full pipeline works end to end: someone clicks an ad, lands on the page, picks their shades, submits, and it shows up in my Sheet. That's the whole thing.

Four sessions today (47, 47b, 47c, 47d). Started with a basic landing page and ended with dark mode, desktop layout, custom dropdowns, auto-scrolling feedback, heartbeat animations, and a live deployed site receiving orders. Probably the most productive day on this project so far.

Next is the real ad run. Everything is in place.

## 2026-03-22 -- Session 47e

Added variant galleries to the landing page. Every single variant now has 4-6 photos you can swipe through when you tap the product thumbnail in the order form. Uploaded all the photos from old Facebook posts -- real product shots, not AI generated. That authenticity matters.

Also made the variant dropdown smart -- once you pick Outback Blue in one row, it disappears from the other rows. No duplicate orders.

Five sessions today. Started the day with a basic landing page and ended with a fully deployed, dark-mode, gallery-enabled, order-receiving e-commerce page. duberymnl.vercel.app is live and ready for ads.

Time to sleep. For real this time.

---

## 2026-03-20 -- Session 44b (continued)

Came back after work to harden the pipeline and plan next steps. Confirmed the "generate content" trigger runs the full flow -- WF1 through image review -- with auto-triggers between stages.

Started thinking about n8n workflows for portfolio. Not porting the existing CLI pipeline -- building new workflows natively in n8n to show versatility. "I built the same automation in two architectures." The n8n MCP tools can teach me current node schemas, so the outdated knowledge problem is solved.

Also had a real conversation about how Meta Ads actually works. Campaigns, ad sets, ads, budget hierarchy, the learning phase. Understanding the platform before connecting the automation. That's the builder mindset -- understand first, automate second.

18 images pending review from batch 20260320. Tunnel and watchdog running. Ready to review on phone.
