# Decision Log

Append-only. Format: [YYYY-MM-DD] DECISION: ... | REASONING: ... | CONTEXT: ...

---

[2026-03-20] DECISION: Switch image gen from parallel to sequential | REASONING: RA wants to see each image land in Drive before next one starts -- easier to monitor, less risk of overloading kie.ai | CONTEXT: Session 44, run_wf2.py ThreadPoolExecutor removed

[2026-03-20] DECISION: Auto-trigger WF2 after caption review submit | REASONING: Eliminates manual handoff between WF1 review and WF2 -- full automation goal | CONTEXT: Session 44, start_review.sh hooks into run_post_review.py

[2026-03-20] DECISION: Add retry logic to claude --print calls | REASONING: API 500 crashed the pipeline mid-run, left orphaned captions -- retry with 30s wait handles transient errors | CONTEXT: Session 44, _run_claude_with_retry in run_post_review.py

[2026-03-20] DECISION: Make run_post_review.py batch-aware with re-scan | REASONING: Crashed run left 4 captions at PROMPT_READY that were missed on retry -- re-scan catches all PROMPT_READY in the batch | CONTEXT: Session 44

[2026-03-20] DECISION: Content pipeline trigger is "generate content" not a skill | REASONING: The workflow is just two steps (run caption gen skill + start_review.sh) -- wrapping in a skill adds a layer without adding logic. Automation lives in the scripts. | CONTEXT: Session 44

[2026-03-20] DECISION: Restructure stage_ad.py to 1 campaign + 1 ad set + N ads | REASONING: Previous 1-campaign-per-caption structure would cost P7,200/day for 36 ads. Meta best practice is shared campaign/ad set so the algorithm optimizes across creatives and budget is shared. | CONTEXT: Session 44, WF3b audit

[2026-03-20] DECISION: Keep WF3b manual (no auto-trigger after image review) | REASONING: Not all IMAGE_APPROVED images should become ads. RA should choose which ones to stage. Auto-staging could waste ad budget. | CONTEXT: Session 44

[2026-03-20] DECISION: Store campaign/ad set IDs in .tmp/ads_config.json | REASONING: IDs are mutable state (campaigns can be deleted in Ads Manager), not secrets. .env is for credentials. JSON state file follows pipeline.json pattern. | CONTEXT: Session 44
