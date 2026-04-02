---
name: pipeline
description: Run the DuberyMNL content pipeline end to end -- captions, image prompts, generation, and review staging.
---

Run the DuberyMNL content pipeline:

1. Read `workflows/` to find the relevant pipeline workflow.
2. Check what's queued -- read the pipeline state or Google Sheet if connected.
3. Run caption generation if needed.
4. Run image prompt generation from captions.
5. Validate prompts before sending to kie.ai (paid -- confirm if unsure about credits).
6. Stage output for RA review -- never post directly.
7. Report: what was generated, what's ready for review, any errors.
