# March 2026

## 2026-03-25 -- Session 55

Short session. Learned how VS Code workspaces actually work with Claude Code -- the file context passing, status bar, and remote tunnel. Big "aha" moment when I realized opening a file in Explorer automatically tells Claude what I'm looking at. Found the direct workspace URL for mobile access too.

Also caught up on phone data from Drive (FolderSync had DNS errors from Doze mode). Processed parking receipt, hospital lookup (ACE Pateros confirmed for PhilCare), BPI transfers, CCTV. Dashboard updated.

Small session but good learning day. The workspace stuff will change how I work going forward.

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

## 2026-03-22 -- Session 47f

Six sessions in one day. Started at landing page polish, ended at registering a business with DTI and buying a domain name. What a ride.

duberymnl.com is live. Custom domain, proper business email (ras@duberymnl.com), Vercel hosting. The landing page went from localhost to a real website in one day.

Tried to run the first real Meta ads campaign. Got the campaign and both ad sets created (PERSON Anchor + PRODUCT Anchor), but the actual ads failed because the app needs Business Verification. Submitted verification to Meta with the domain and email. Also registered DUBERYMNL with DTI -- P200, waiting for the certificate. Once that comes in, upload to Meta, app goes live, re-run the staging script, and ads are up.

The campaign is sitting there waiting. Everything is built, tested, and ready. Just need Meta to approve.

Bought a domain, registered a business, and built a complete e-commerce landing page with dark mode and variant galleries -- all in one day. This is the kind of day that changes the trajectory.

## 2026-03-22 -- Session 47g

The ads are live. Actually live. Green dots, Learning status, money about to be spent.

Seven sessions in one day. Started with landing page CSS tweaks and ended with 10 real Facebook ads running on Meta, targeting Metro Manila, pointing to duberymnl.com. Every click goes to a dark-mode landing page with swipeable product galleries, a heartbeat free delivery nudge, and an order form that writes to a Google Sheet.

Had to create the ads manually because the app needs Business Verification (DTI cert pending). But it doesn't matter how they got there -- they're there. P200/day, 10 ads, 2 ad sets testing PERSON vs PRODUCT creative approaches.

Tomorrow I'll check if anyone clicked. If orders come in, they'll be in the Google Sheet. If not, we adjust. That's the whole point of Phase 1 -- learn, not just sell.

This is the moment the project stops being a portfolio exercise and starts being a real business.

## 2026-03-22 -- Session 47h

Last session of the marathon. Updated all the Messenger auto-replies -- the old ones still said P499, no COD, payment first. Now everything matches: P699, COD, same-day delivery, duberymnl.com link.

Eight sessions in one day. From CSS tweaks to a fully operational e-commerce system. Ads running, landing page live, orders flowing to a Sheet, auto-replies updated. Everything is connected.

Check the Google Sheet tomorrow morning. If there are orders, we ship. If not, we learn from the data and adjust. Either way, DuberyMNL is officially in business.

## 2026-03-23 -- Session 48

Woke up to ads running. 77 landing page views, P116 spent. No orders yet but it's day 1 -- Meta is still learning. #22 and #6 are the early winners.

Cleaned up my entire Google Drive. Went from 100+ files scattered in root to 12 clean items. Career folder with all my resumes, Skateboarding folder with Skate Pilipinas and Freeride stuff, everything else archived properly. Found Baby Jah's birth certificate hiding as "IMG_4984_Original.jpeg" and renamed it properly. Also found my crypto seed phrases in a screenshot on Drive -- moved those to memory and deleted the file.

Started thinking about Google Photos integration so Claude can see photos I take on my phone without manually uploading to Drive. That's a future build.

The Drive cleanup was overdue. Now when I open Drive it's clean -- DuberyMNL stuff front and center, everything else organized. Small thing but it feels good to have a clean workspace.

---

## 2026-03-24 -- Session 51

Built the organic Facebook posting tool (WF3a). Two scripts: schedule_post.py for single posts, schedule_batch.py for batch scheduling across Tue/Thu/Sat/Sun at 12PM PHT. Picked 6 posts for the first batch (#12, #11, #17, #6, #20260318-018, #20260320-018).

Ran the batch and hit a wall -- same blocker as WF3b. The access token is a User token, not a Page token, and it's missing `pages_manage_posts` permission. That permission requires Meta Business Verification, which is still pending. DTI certificate was received on March 22 and uploaded, now waiting for Facebook to approve.

Both organic posting (WF3a) and automated ad staging (WF3b) are blocked by the same gate. Tools are built and tested. Once Meta approves, it's one command to schedule everything.

Also updated memory: DTI status changed from pending to certificate received. Meta Business Verification is the only remaining blocker.

## 2026-03-20 -- Session 44b (continued)

Came back after work to harden the pipeline and plan next steps. Confirmed the "generate content" trigger runs the full flow -- WF1 through image review -- with auto-triggers between stages.

Started thinking about n8n workflows for portfolio. Not porting the existing CLI pipeline -- building new workflows natively in n8n to show versatility. "I built the same automation in two architectures." The n8n MCP tools can teach me current node schemas, so the outdated knowledge problem is solved.

Also had a real conversation about how Meta Ads actually works. Campaigns, ad sets, ads, budget hierarchy, the learning phase. Understanding the platform before connecting the automation. That's the builder mindset -- understand first, automate second.

18 images pending review from batch 20260320. Tunnel and watchdog running. Ready to review on phone.

## 2026-03-25

Resubmitted Meta Business Verification. Previous attempt failed because business details (name + address) were blank in Meta Business Settings. Updated to match DTI certificate exactly: "DUBERYMNL ONLINE SHOP", San Joaquin, City of Pasig, NCR. DTI certificate (Business Name No. 8052442, valid until 2031-03-22) uploaded as supporting document. Expect response by March 27. Also confirmed ras@duberymnl.com email forwarding is working -- Facebook verification emails landing in Gmail.

Morning: Made lugaw with egg for Baby Jah's breakfast. Baby Jah pooped -- 3 small round shapes, slightly hard. Straining/having hard time pushing it out (mild constipation signs). Changed diaper. Second poop later -- hard round shapes, bigger, straining again, bit of blood (likely small anal fissure from hard stool -- monitor closely, see pediatrician if bleeding continues). Need to increase water + fiber intake. Gave him water bottle after. Bujah finished eating -- lugaw with egg (P30). Went out for a walk with Bujah. Gave Ara P600 from pocket money.
