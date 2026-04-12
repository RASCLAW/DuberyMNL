# References -- dubery-prompt-validator

## Reads
- .tmp/{id}_prompt_structured.json (input to validate)
- Product reference table (local asset paths for 11 variants)

## Writes
- Verdict JSON to stdout (PASS / PATCH / REGENERATE)
- Patches .tmp/{id}_prompt_structured.json in place (if PATCH)

## Depends On
- No external tools (pure validation logic)

## Referenced By
- dubery-content-pipeline (Step 5 -- validate after prompt writing)
- dubery-content-pipeline-full (Step 5 -- validate after prompt writing)
