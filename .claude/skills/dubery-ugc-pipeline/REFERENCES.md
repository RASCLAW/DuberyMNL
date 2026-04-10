# References -- dubery-ugc-pipeline

## Reads
- .tmp/ugc_pipeline.json (UGC pipeline state)
- contents/assets/product-refs/{model}/ (product references)
- contents/assets/logos/dubery-logo.png (logo)

## Writes
- .tmp/ugc_pipeline.json (status updates through lifecycle)
- .tmp/{id}_ugc_prompt.json (generated prompts)
- contents/new/ugc_{id}.jpg (generated images)

## Depends On
- dubery-ugc-caption-gen (caption generation)
- dubery-ugc-prompt-writer (prompt generation)
- dubery-ugc-fidelity-gatekeeper (prompt validation)
- tools/pipeline/run_ugc.py (image generation orchestrator)
- tools/image_gen/generate_vertex.py (Gemini image gen)

## Referenced By
- Used directly via /dubery-ugc-pipeline
