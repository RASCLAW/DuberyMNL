# DuberyMNL -- Project Instructions

DuberyMNL-specific context. Global EA identity and rules live in `~/.claude/CLAUDE.md` and `~/.claude/rules/`.

## Tools Directory

Production Python scripts in `tools/`. Always check here before building new ones.

Each dir has a `README.md` (linked below) -- the convention is: every tool gets a short README, indexed here at creation, kept current via `/savepointplus`.

| Directory | Purpose |
|-----------|---------|
| [`pipeline/`](tools/pipeline/README.md) | Content pipeline orchestration: WF1 validate, WF2 image gen, UGC, regenerate |
| [`image_gen/`](tools/image_gen/README.md) | AI image/video gen (kie.ai/NB2 + Vertex/Gemini), scene randomizers, review UIs, dedup |
| [`image_ops/`](tools/image_ops/README.md) | Pillow image optimization (`-opt.jpg`) + multi-layout collage composition |
| [`captions/`](tools/captions/README.md) | WF1 caption review (Flask approve/reject UI) + Gmail review-email notifier |
| [`facebook/`](tools/facebook/README.md) | FB Page posting, feed-queue scheduling, story rotation, comment auto-response (Graph API) |
| [`meta_ads/`](tools/meta_ads/README.md) | Meta Marketing API: ad/pixel insights, stage PAUSED ads, audiences, daily TG digest |
| [`meta/`](tools/meta/README.md) | Meta Commerce catalog management via Graph API |
| [`clarity/`](tools/clarity/README.md) | Pull Microsoft Clarity site metrics (Data Export API) → `.tmp/clarity_metrics.json` |
| [`sheets/`](tools/sheets/README.md) | Google Sheets read/write + one-time Master/CRM spreadsheet setup |
| [`drive/`](tools/drive/README.md) | Google Drive upload/sync/backup (images, banks, secrets) |
| [`orders/`](tools/orders/README.md) | Sync orders from Sheets + per-SKU inventory + reorder reports |
| [`landing/`](tools/landing/README.md) | Export IMAGE_APPROVED entries → `dubery-landing` captions.json + copy ad images |
| [`notion/`](tools/notion/README.md) | Sync pipeline captions (approved + rejected) to a Notion DB + Sheet (upsert) |
| [`upwork/`](tools/upwork/README.md) | Job scout (RemoteOK/Jobicy/WWR) + rolling market-intel for the remote-AI job hunt |
| [`gmail/`](tools/GOOGLE_CLI.md) | Gmail CLI -- list/read/send/label/draft/trash (`gog gmail`) |
| [`gcal/`](tools/GOOGLE_CLI.md) | Google Calendar CLI -- agenda/create/edit/delete/quickadd (`gog cal`). Dir is `gcal` not `calendar` (stdlib shadow). |
| [`tasks/`](tools/GOOGLE_CLI.md) | Google Tasks CLI -- lists/add/complete/delete (`gog tasks`) |
| `chatbot/` | STALE legacy chatbot code -- do not edit. Active chatbot is at project-root `chatbot/` (see "Chatbot" section below). |

### `gog` -- Google services CLI

`tools/gog.py` is one dispatcher over the Google CLIs: `python tools/gog.py <service> <cmd>` (or `gog <service> <cmd>` via the repo-root `gog.cmd` shim once on PATH). Services: `gmail`, `cal`, `tasks`. All share the single OAuth token via `tools/auth.py` (`service()` builds a client; `reauth()` forces consent after adding a scope to `SCOPES`). Every mutating verb supports `--dry-run` (prints the intended action, no API write). Drive + Sheets keep their own scripts (`tools/drive/`, `tools/sheets/`). Google Photos is intentionally absent (Library API can't move/edit/delete an existing library); Google Keep has no API (migrate via Takeout).

**Full docs:** [tools/GOOGLE_CLI.md](tools/GOOGLE_CLI.md) -- commands, auth model, how to add a new Google service, troubleshooting.

## Pipeline Data Flow

```
Google Sheet (source of truth)
  -> WF1: Caption gen + approval
  -> WF2: Image gen (kie.ai / NB2)
  -> WF3a: Auto-post to Facebook (blocked on Meta verification)
  -> WF3b: Meta Ads staging (manual)
```

- Pipeline Sheet = source of truth. pipeline.json = local cache. Sync before/after.
- Use fcntl file locking on pipeline.json.
- No manual DB injection -- all data flows through the pipeline.

## Chatbot (active)

Live Messenger bot lives at [chatbot/](chatbot/) (project root), NOT `tools/chatbot/`. See [chatbot/README.md](chatbot/README.md) for architecture, guardrails, and admin endpoints. `tools/chatbot/` is legacy and stale -- never edit.

## Skills (DuberyMNL-specific)

| Skill | Purpose |
|-------|---------|
| `/dubery-content-pipeline` | Captions to image prompts (no review) |
| `/dubery-content-pipeline-full` | Full pipeline with image gen + review |
| `/dubery-ugc-prompt-writer` | UGC-style prompt generation (agent) |
| `/dubery-chatbot` | Messenger bot persona + guidelines |
| `/dubery-caption-gen` | Caption generation |
| `/dubery-ugc-caption-gen` | UGC caption generation |
| `/dubery-prompt-parser` | Parse image prompts |
| `/dubery-ugc-prompt-parser` | Parse UGC prompts |
| `/dubery-prompt-reviewer` | v2 quality gate -- run before image gen spend |
| `/dubery-brand-content` | Brand content orchestrator -- routes to sub-skills |
| `/dubery-brand-callout` | Feature callout images (5 layouts) |
| `/dubery-brand-bold` | Bold statement images (4 layouts) |
| `/dubery-brand-collection` | Collection showcase images (5 layouts + carousel) |
| `/dubery-ugc-pipeline` | End-to-end UGC pipeline |
| `/ad-reverse-engineer` | Reverse-engineer reference ads |

Archived v1 skills (in `.claude/skills-archive-v1/`): dubery-ad-creative, dubery-prompt-writer, dubery-prompt-validator, dubery-infographic-ad, dubery-ugc-fidelity-gatekeeper

## Commands

- `/pipeline` -- Run content pipeline end to end

## Agents (subagent_type)

- `dubery-content` -- Content pipeline specialist (Sonnet)
- `dubery-ads` -- Meta ads analysis and staging (Sonnet)
- `dashboard` -- ra-dashboard UI and data (Sonnet)

## kie.ai Quirks

- Google Drive URLs don't work for reference images. Need CDN pre-upload.
- lh3.googleusercontent.com/d/{ID} works as CDN URL.
- Logo URL breaks the API -- don't include it.
- Default resolution is 2K.

## Verification

After making changes, verify your work:

- **Pipeline tools:** `python tools/status.py` -- confirms pipeline.json loads and prints status counts
- **Sheet access:** `python tools/sheets/read_sheet.py` -- confirms Google Sheets auth works
- **Image gen:** `python tools/image_gen/generate_image.py --dry-run` -- validates prompt without spending credits
- **Landing page:** Open `dubery-landing/index.html` in browser or check with Playwright
- **Env health:** Confirm `.env` exists and has required keys: `python -c "from dotenv import load_dotenv; load_dotenv(); import os; [print(f'{k}: {'SET' if os.getenv(k) else 'MISSING'}') for k in ['ANTHROPIC_API_KEY','KIE_AI_API_KEY','PAGE_ACCESS_TOKEN']]"`
- **After any tool edit:** Run the tool standalone to confirm it exits cleanly

No test suite exists yet. When writing new tools, add basic smoke tests inline (`if __name__ == '__main__'` block).

## File Rules

- `.tmp/` -- Temporary files (regenerated as needed, gitignored)
- `contents/` -- All generated content (ads, ugc, brand, carousel, product)
- `contents/new/` -- Staging area for newly generated images (pre-review)
- `contents/failed/` -- Rejected images
- `contents/ready/` -- Tagged + reviewed images (source of truth for banks)
  - `contents/ready/person/{model}/` -- Person shots by model color
  - `contents/ready/product/{model}/` -- Product shots by model color
  - `contents/ready/brand/` -- Brand content (callouts, bold, collection)
  - `contents/ready/metadata.json` -- Per-file metadata
  - `contents/ready/manifest.json` -- Tags (5-tag system)
- `contents/assets/` -- Curated banks + references (permanent)
  - `chatbot-image-bank-2026-04.json` -- 44 picks, consumed by chatbot/ Gemini handler
  - `fb-stories-pool-2026-04.json` -- 74 picks, consumed by story_rotation.py
  - `hero/` -- Hero product shots (one per model)
  - `prodref-kraft/` -- Kraft-bg product references for NB2 generation
  - `product-refs/` -- Multi-angle product reference photos
  - `product-specs.json` -- Per-model SKU/identity specs
  - `prodref-metadata.json` -- Prodref sidecar data
- `dubery-landing/` -- Live landing page on Vercel (duberymnl.com)
- `.env` -- All secrets (gitignored)
- `decisions/log.md` -- DuberyMNL-specific decision log
- `references/` -- DuberyMNL-specific reference docs
- `archives/` -- Old organizational material (pre-EA-rebuild)
