# March 2026

## 2026-03-20 -- Session 44

Big milestone day. The DuberyMNL Facebook ads content generator is working end-to-end.

One trigger ("generate content") kicks off the whole pipeline: 15 captions generated, reviewed on phone, then prompts, validation, and image generation all run automatically. 14 out of 14 images passed the gatekeeper on first attempt -- first time that's ever happened.

Hit an API 500 error mid-run that crashed the pipeline. Used that as an opportunity to add retry logic (3 attempts, 30s wait) and make the orchestrator resilient to partial failures. Rebuilt `run_post_review.py` to be batch-aware so it recovers gracefully instead of leaving orphaned captions.

Also started thinking about cloud deployment for scheduled runs and client work. Not building it yet but saved the plan. This is the kind of system that could be packaged as a service.

The portfolio piece is taking shape. Not just "I built a thing" but "I built a thing that runs itself."

Also tackled WF3b (Meta Ads staging). Learned how Meta Ads actually works -- campaigns, ad sets, ads, the budget structure. Discovered stage_ad.py was creating 1 campaign per caption (36 campaigns = P7,200/day). Restructured to 1 campaign, 1 ad set, N ads -- the way Meta recommends. Budget shared at P200/day across all ads. Ready for a real API test once the batch 20260320 images are reviewed.

Two big things done in one session. Content pipeline working, ads staging restructured. The system is getting close to portfolio-ready.
