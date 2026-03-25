# References -- dubery-ugc-prompt-writer

## Reads
- JSON input: {scenario_type, subject_gender, product_ref, aspect_ratio, caption_id, notes}
- Product reference table (11 Dubery variants)

## Writes
- .tmp/{id}_ugc_prompt.json (dense narrative UGC prompt)
- ugc_pipeline.json (status: PENDING -> PROMPT_READY)

## Depends On
- No external tools (pure prompt engineering)

## Referenced By
- Independent workflow (UGC-specific, not part of main ad pipeline)
- Output feeds to nano-banana-2 / kie.ai for image generation
