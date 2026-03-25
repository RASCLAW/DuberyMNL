# References -- dubery-content-pipeline-full

## Reads
- .tmp/pipeline.json (last 20 entries for context)
- .env (kie.ai API key, Meta API keys, Google credentials)
- dubery-caption-gen SKILL.md (caption rules)
- dubery-prompt-writer SKILL.md (prompt rules)

## Writes
- .tmp/pipeline.json (captions + status updates through full lifecycle)
- .tmp/{id}_prompt_structured.json (one per caption)
- output/images/ (generated images from kie.ai)
- Google Drive backup of images
- Meta Ads (staged as PAUSED via stage_ad.py)

## Depends On
- dubery-caption-gen (caption rules)
- dubery-prompt-writer (prompt rules, parallel agents)
- dubery-prompt-validator (validates prompts)
- tools/pipeline/run_wf2.py (kie.ai image generation)
- tools/image_gen/image_review_server.py (human checkpoint, localhost:5001)
- tools/meta_ads/stage_ad.py (ad staging)
- .venv (Python virtual environment)
- kie.ai API (costs money)

## Referenced By
- CLAUDE.md (trigger: "content pipeline full")
- One mandatory human checkpoint: image review
