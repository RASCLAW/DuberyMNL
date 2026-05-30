# facebook — Facebook Page posting, feed scheduling, story rotation, and comment auto-response

**What it does**
- Schedules and publishes organic feed posts (single photo, multi-photo grid, or pre-composed collage) to the DuberyMNL FB Page via the Graph API, using either Meta-native `scheduled_publish_time` or local cron as a fallback.
- Maintains a local feed queue (`feed_queue.json`) that the hourly Task Scheduler worker reads to hand off, verify, and fire posts.
- Rotates through a curated story image pool every 3 hours (time-based, no state file) and posts photo stories.
- Auto-responds to post comments: likes the comment, replies from a Taglish template pool, and sends a DM to the commenter with product info.

**Key files**

| File | Purpose |
|------|---------|
| `queue_add.py` | CLI to append an item to the feed queue (mode: multi or collage, 1-10 images, scheduled time). |
| `post_from_queue.py` | Hourly worker: hands off APPROVED items to Meta, verifies SCHEDULED_AT_META items, locally publishes anything past due. Sends Telegram success/failure pings. |
| `scheduled_handoff.py` | Library + debug CLI for Meta-native scheduled publish handoff; also handles cancel and verify-published logic. |
| `queue_helpers.py` | Atomic file-locked read/write helpers for `feed_queue.json`. |
| `schedule_post.py` | Schedule or immediately publish a single caption from `pipeline.json` or `ugc_pipeline.json`. |
| `schedule_batch.py` | Batch-schedule multiple pipeline captions across Tue/Thu/Sat/Sun @ 12PM PHT (or UGC slots). |
| `post_story.py` | Post a single image as a Facebook photo story (two-step: upload unpublished → publish as story). |
| `story_rotation.py` | Time-based story rotation from `contents/assets/fb-stories-pool-2026-04.json`; runs unattended via cron. |
| `upload_album.py` | Create a silent FB Page album and upload ordered photos from a JSON config (no feed story). |
| `comment_responder.py` | Comment auto-responder: Flask webhook server or `--test` mode. Integrates into `chatbot/messenger_webhook.py` via `handle_feed_webhook()`. |
| `comment_templates.py` | Pure-data module: Taglish reply strings, DM opener templates, spam keyword list. |

**Run**

Queue a feed post:
```
python tools/facebook/queue_add.py --images contents/ready/brand/foo.png --caption "Polarized for the view." --time "2026-05-22 19:00"
```

Queue a collage post:
```
python tools/facebook/queue_add.py --images a.png b.png --mode collage --layout 2h --caption "Before / After" --time "2026-05-22 19:00"
```

Run the hourly worker (dry-run):
```
python tools/facebook/post_from_queue.py --dry-run
```

Schedule a single pipeline caption:
```
python tools/facebook/schedule_post.py --id 20260320-001 --dry-run
python tools/facebook/schedule_post.py --id 20260320-001 --time "2026-03-29 12:00"
python tools/facebook/schedule_post.py --id 20260320-001 --now
```

Batch-schedule all eligible captions:
```
python tools/facebook/schedule_batch.py --all --dry-run
python tools/facebook/schedule_batch.py --ids 1 3 5 --start "2026-03-29"
```

Post a photo story:
```
python tools/facebook/post_story.py --image path/to/image.png --dry-run
```

Run story rotation (called by cron):
```
python tools/facebook/story_rotation.py --dry-run
```

Create an album from a JSON config:
```
python tools/facebook/upload_album.py --config path/to/album.json --dry-run
```

Test the comment responder:
```
python tools/facebook/comment_responder.py --test
python tools/facebook/comment_responder.py --port 5003
```

**Inputs / outputs**

- Reads: `tools/facebook/feed_queue.json` (feed queue), `.tmp/pipeline.json` / `.tmp/ugc_pipeline.json` (caption pipeline), `contents/assets/fb-stories-pool-2026-04.json` (story pool), `contents/ads/dubery_<id>.*` / `contents/ugc/ugc_<id>.*` (images), album JSON config (user-supplied).
- Writes: `tools/facebook/feed_queue.json` (queue status updates), `.tmp/scheduled_posts.json` (schedule log), `.tmp/feed_worker_last_run.json` (worker run record), `.tmp/comment_dedup.json`, `.tmp/comment_responses.json`, `.tmp/conversations/<uid>_autodm.json`.
- Calls: Facebook Graph API v21.0–v25.0 (`/photos`, `/feed`, `/photo_stories`, `/albums`, `/comments`, `/likes`, `/me/messages`), Telegram Bot API (success/failure pings).

**Auth / env**

| Variable | Used by |
|----------|---------|
| `META_PAGE_ACCESS_TOKEN` | All scripts — Graph API calls |
| `META_PAGE_ID` | All scripts — page-scoped endpoints |
| `MESSENGER_VERIFY_TOKEN` | `comment_responder.py` webhook verification |
| `TELEGRAM_BOT_TOKEN` | `post_from_queue.py` — success/failure pings |
| `TG_CHAT_ID` | `post_from_queue.py` — success/failure pings |

Required Graph API permissions: `pages_manage_posts`, `pages_read_engagement`, `pages_messaging` (for DMs).

**Gotchas**

- `schedule_batch.py` imports from `schedule_post.py` via a relative import; run it from the project root or with `sys.path` intact.
- `post_from_queue.py` is designed to run via Windows Task Scheduler (task: `DuberyMNL_FeedScheduler`) using `pythonw.exe` — `python.exe` exits with 0xC000013A on laptop sleep.
- `story_rotation.py` reads image paths from the pool JSON; the pool currently references local `contents/` files committed to git (~113 MB). A runtime-fetch fix from Drive/R2 is in the backlog.
- `upload_album.py` requires `PYTHONIOENCODING=utf-8` on Windows to avoid cp1252 encoding errors in captions.
- Meta's `scheduled_publish_time` must be ≥10 min and ≤6 months in the future; `eligible_for_handoff()` in `scheduled_handoff.py` enforces this (660 s minimum with a 60 s buffer).
