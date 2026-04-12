# References -- dubery-ugc-fidelity-gatekeeper

## Reads
- .tmp/{id}_ugc_prompt.json (UGC prompt to validate)
- contents/assets/product-refs/{model}/ (product reference for fidelity check)

## Writes
- .tmp/ugc_pipeline.json (updates fidelity_verdict: PASS or REJECT)

## Depends On
- No external tools (prompt analysis only)

## Referenced By
- dubery-ugc-pipeline (runs gatekeeper before image generation)
- tools/pipeline/run_ugc.py (calls gatekeeper in Phase B)
