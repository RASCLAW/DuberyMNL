# References -- dubery-ugc-prompt-writer

## Reads
- .tmp/ugc_pipeline.json (caption + product_ref for prompt)
- contents/assets/product-refs/{model}/ (product reference photos)
- contents/assets/logos/dubery-logo.png (logo)

## Writes
- .tmp/{id}_ugc_prompt.json (structured UGC prompt)
- .tmp/ugc_pipeline.json (status: CAPTION_APPROVED -> PROMPT_READY)

## Depends On
- No external tools (pure prompt engineering)

## Referenced By
- dubery-ugc-pipeline (invokes prompt generation)
- dubery-ugc-fidelity-gatekeeper (validates output)
