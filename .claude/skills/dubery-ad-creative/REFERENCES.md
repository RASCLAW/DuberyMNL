# References -- dubery-ad-creative

## Reads
- .tmp/pipeline.json (caption by ID)
- .tmp/{id}_validator_feedback.json (if regeneration run)
- Product reference table (11 Dubery variants + logo paths)

## Writes
- .tmp/{id}_ad_prompt_structured.json (completed prompt -- different filename from dubery-prompt-writer to avoid conflicts)
- .tmp/pipeline.json (status: APPROVED -> PROMPT_READY)

## Depends On
- No external tools (pure prompt engineering)

## Referenced By
- dubery-content-pipeline (runs in parallel agents)
- nano-banana-2 (consumes output for image gen)
