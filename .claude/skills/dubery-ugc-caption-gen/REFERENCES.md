# References -- dubery-ugc-caption-gen

## Reads
- .tmp/ugc_pipeline.json (existing UGC captions to avoid repeats)

## Writes
- .tmp/ugc_pipeline.json (appends captions, status: CAPTION_APPROVED)

## Depends On
- No external tools (pure prompt engineering)

## Referenced By
- dubery-ugc-pipeline (invokes caption generation)
