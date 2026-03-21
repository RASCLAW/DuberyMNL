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

---

## 2026-03-20 -- Session 44b (continued)

Came back after work to harden the pipeline and plan next steps. Confirmed the "generate content" trigger runs the full flow -- WF1 through image review -- with auto-triggers between stages.

Started thinking about n8n workflows for portfolio. Not porting the existing CLI pipeline -- building new workflows natively in n8n to show versatility. "I built the same automation in two architectures." The n8n MCP tools can teach me current node schemas, so the outdated knowledge problem is solved.

Also had a real conversation about how Meta Ads actually works. Campaigns, ad sets, ads, budget hierarchy, the learning phase. Understanding the platform before connecting the automation. That's the builder mindset -- understand first, automate second.

18 images pending review from batch 20260320. Tunnel and watchdog running. Ready to review on phone.
