# image_gen — AI image and video generation pipeline for DuberyMNL ad content

**What it does**
- Generates product and UGC ad images via Gemini 3.1 Flash on Vertex AI, using kraft product references for fidelity.
- Randomizes scene assignments (product, category, location, lighting, camera, aspect ratio) while avoiding cross-session duplicates tracked in `contents/headline_history.json` and `contents/layout_history.json`.
- Provides Flask-based browser UIs for the two-stage review workflow: Stage 1 quality gate (approve/reject recent images → `contents/ready/` or `contents/failed/`), Stage 2 tag assignment (POST/STORY/AD/LANDING/ARCHIVE → `contents/ready/manifest.json`), and a model gallery for picking chatbot image bank anchors.
- Generates videos via Veo 3.1 on Vertex AI (text-to-video, image-to-video, start+end frame interpolation).

**Key files**

| Script | Purpose |
|---|---|
| `generate_vertex.py` | **The** image generator -- the only one. Reads a prompt JSON or TXT + optional `_config.json` sidecar, sends to Gemini 3.1 Flash via Vertex AI. Two modes: ad-hoc (extension follows the model's mime type, auto-versions on collision to -v2, -v3) and `--exact` pipeline mode (writes the requested path verbatim, transcoding PNG→JPEG as needed, derives the caption id from the filename stem, backs up to Google Drive, updates `.tmp/pipeline.json` status). |
| `generate_videos.py` | Veo 3.1 video generator. Supports text-to-video and image-to-video. Saves MP4 + prompt sidecar JSON. |
| `run_vertex_batch.py` | Sequential batch runner over a list of prompt files. Enforces 30s pacing between calls to avoid Vertex 429 quota errors. |
| `run_veo_batch.py` | Sequential Veo batch animator. Reads a JSON jobs list (each: `image` start-frame + motion `prompt` + `output` mp4 + optional `negative_prompt`) and calls `generate_videos.py` per job with shared flags (model/aspect/duration/audio). Continues past failures. For animating a whole storyboard bank of stills into clips. |
| `batch_experiment.py` | Experiment-mode batch orchestrator called from the Command Center. Reads a `run.json` manifest in a `contents/experiments/<run_id>/` directory, generates N images with 429 backoff, writes live progress to `run.json`. Also runnable standalone. |
| `v3_randomizer.py` | v3 pipeline scene randomizer. Picks product + category + location + lighting + camera + aspect ratio using numbered banks and kraft prodref sidecars. Deduplicates against `contents/layout_history.json`. |
| `batch_randomizer.py` | v2 batch randomizer. Picks skill type (ugc/brand-callout/brand-bold/brand-collection), product, layout, and headline, checking `contents/headline_history.json` and `contents/layout_history.json`. Outputs a JSON assignment list. |
| `schema_parser.py` | Converts v2 skill output JSON to Master Schema format (IDENTITY_LOCK mode) for Vertex generation. Adds `interaction_physics` (lighting, reflections, contact points) and camera presets per content type. |
| `image_review_recent.py` | Stage 1 review server. Scans `contents/` (and `.tmp/`) for images modified within a configurable lookback window, grouped by category. Approve moves to `contents/ready/`; reject moves to `contents/failed/`. |
| `image_review_server.py` | Pipeline-mode review server (WF3 image review). Reads `DONE` entries from `.tmp/pipeline.json`, presents cards with approve/reject/regenerate/skip actions, syncs decisions back to pipeline.json and Google Sheets. Supports `--ugc` flag for UGC pipeline. |
| `image_tag_approved.py` | Stage 2 tag server. Presents images from `contents/ready/` and lets RA assign tags (POST/STORY/AD/LANDING/ARCHIVE) saved to `contents/ready/manifest.json`. |
| `model_gallery.py` | Browses `contents/ready/` grouped by product model (person + product sections). Click to select anchors for the chatbot image bank; exports picks to `.tmp/chatbot_image_bank_picks.json`. |
| `fidelity_scorecard.py` | Generates one standardized test image per product against a fixed marble-surface prompt, calling `generate_vertex.py`. Isolates product fidelity from scene complexity. Outputs to `contents/new/scorecard/`. |
| `content_history.py` | Tracks used headlines and skill+layout+product combos in `contents/headline_history.json` and `contents/layout_history.json`. Used by randomizers to prevent feed repetition. Subcommands: `record`, `check`, `list`. |

**Run**

```sh
# Generate one image (Vertex / Gemini)
python tools/image_gen/generate_vertex.py .tmp/my_prompt.json
python tools/image_gen/generate_vertex.py .tmp/my_prompt.json contents/new/custom.png

# Generate one image into the pipeline (exact path + Drive backup + pipeline.json status)
python tools/image_gen/generate_vertex.py .tmp/4_prompt_structured.json contents/ads/dubery_4.jpg 4:5 --exact

# Generate a video (Veo 3.1)
python tools/image_gen/generate_videos.py --prompt "waves crashing" --output contents/new/out.mp4
python tools/image_gen/generate_videos.py --prompt "waves" --image start.png --output contents/new/out.mp4

# Run a batch of prompt files sequentially with 30s pacing
python tools/image_gen/run_vertex_batch.py .tmp/a_prompt.json .tmp/b_prompt.json
python tools/image_gen/run_vertex_batch.py --interval 45 .tmp/*.json

# Animate a bank of stills into Veo clips (jobs JSON: image + prompt + output)
python tools/image_gen/run_veo_batch.py .tmp/veo_jobs.json --no-audio
python tools/image_gen/run_veo_batch.py .tmp/veo_jobs.json --model lite --duration 4

# Randomize scene assignments (v3 pipeline)
python tools/image_gen/v3_randomizer.py --count 3
python tools/image_gen/v3_randomizer.py --product outback-blue --category UGC_PERSON_WEARING

# Randomize skill+layout batch (v2 pipeline)
python tools/image_gen/batch_randomizer.py --count 5 --type ugc
python tools/image_gen/batch_randomizer.py --count 11 --type mix

# Stage 1 review (last 4 days, port 8123)
python tools/image_gen/image_review_recent.py
python tools/image_gen/image_review_recent.py --days 7 --port 8124

# Pipeline-mode review (ad images, port 5001)
python tools/image_gen/image_review_server.py
python tools/image_gen/image_review_server.py --ugc

# Stage 2 tag approved images (port 8124)
python tools/image_gen/image_tag_approved.py

# Model gallery for chatbot image bank picks (port 8125)
python tools/image_gen/model_gallery.py

# Fidelity scorecard (all products, angle 1)
python tools/image_gen/fidelity_scorecard.py
python tools/image_gen/fidelity_scorecard.py bandits-green --angle 3 --dry-run

# Content history
python tools/image_gen/content_history.py list
python tools/image_gen/content_history.py record --batch .tmp/batch_001.json
python tools/image_gen/content_history.py check --headline "BLOCK THE NOISE."
```

**Inputs / outputs**

- Reads: prompt JSON files from `.tmp/` (must have a top-level `prompt` key); kraft product reference images from `contents/assets/prodref-kraft/` and `contents/assets/product-refs/`; per-product sidecar JSONs at the same paths; `contents/assets/product-specs.json` for model identity data; `.tmp/pipeline.json` for pipeline-mode review.
- Writes: generated images to `contents/new/` (default), `contents/new/scorecard/`, or paths specified by the caller; `contents/ready/` and `contents/failed/` after review; `contents/ready/manifest.json` for tags; `contents/headline_history.json` and `contents/layout_history.json` for dedup; `.tmp/chatbot_image_bank_picks.json` from model gallery; MP4 + `.prompt.json` sidecars for videos; Drive backup via `tools/drive/upload_image.py` (called as a subprocess by `generate_vertex.py` in `--exact` mode).

**Auth / env**

- Vertex AI / Gemini — uses Application Default Credentials. Billing project defaults to `dubery`; override with `VERTEX_PROJECT` in `.env` to bill a different GCP project (e.g. a separate $300-trial account). Location is fixed per modality: `us-central1` (videos) or `global` (images). Credentials resolve via `GOOGLE_APPLICATION_CREDENTIALS` (service-account key) if set, else interactive ADC (`gcloud auth application-default login`). To run a separate account, point `GOOGLE_APPLICATION_CREDENTIALS` at that project's SA key and set `VERTEX_PROJECT` to its project ID — both projects then coexist and flip by env var.
- Google Sheets — `image_review_server.py` syncs to the pipeline sheet using OAuth tokens at `token.json` + `credentials.json` in the repo root. Optional; skips sync if files are absent.

**Gotchas**

- Parallel Vertex calls instantly hit 429 quota. `run_vertex_batch.py` enforces 30s sequential pacing; `generate_vertex.py` adds 30/60/90s backoff on 429. Never fire 4+ calls in parallel.
- `generate_vertex.py` bills the GCP project in `VERTEX_PROJECT` (default `dubery`); `VERTEX_IMAGE_MODEL` overrides the model.
- Reference images are read from local paths and sent inline as multimodal Parts — no CDN pre-upload step.
- `generate_vertex.py` auto-versions output on filename collision (`-v2`, `-v3`, ...) rather than overwriting — required to avoid the sidecar `PermissionError` on Windows when the file is locked.
- `image_review_server.py` runs on port 5001; `image_review_recent.py` on 8123; `image_tag_approved.py` on 8124; `model_gallery.py` on 8125. All bind to localhost only (except `image_review_recent.py --tunnel` which optionally opens an ngrok public URL).
