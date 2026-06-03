# meta_ads — Meta Marketing API tools for pulling insights, staging ads, and managing audiences

**What it does**
- Pulls campaign/adset/ad performance insights and pixel event stats from the Meta Graph API, writing JSON to `.tmp/`.
- Stages new PAUSED ads on Meta from pipeline captions (`stage_ad.py`) or from image-file creative plans (`stage_creatives.py`), reusing or creating campaigns and adsets as needed.
- Sends a daily Telegram digest of yesterday's spend, ROAS, orders, and best/worst performers (`daily_digest.py`).
- Lists and creates custom/saved audiences, and uploads individual images to the Meta ad-image library.

**Key files**

| Script | What it does |
|--------|--------------|
| `pull_insights.py` | Pulls campaign/adset/ad performance metrics for a date range; saves `.tmp/ad_insights.json` |
| `pull_live_meta.py` | Pulls adset statuses, budgets, and ad creative thumbnails; saves `.tmp/marketing_live_meta.json` |
| `pull_pixel_stats.py` | Pulls Pixel event totals (PageView/ViewContent/AddToCart/Purchase); saves `.tmp/pixel_stats.json` |
| `daily_digest.py` | Composes a daily ad-performance digest (spend, ROAS, top ad) and sends it to Telegram; archives to `.tmp/daily_digest/YYYY-MM-DD.md` |
| `stage_ad.py` | Stages PAUSED ads from `IMAGE_APPROVED` pipeline.json captions; supports single ID, `--all`, or a multi-adset plan file |
| `stage_creatives.py` | Stages PAUSED ads from a creative plan JSON (image paths + caption + audience preset); companion to `stage_ad.py` |
| `stage_carousel_ad.py` | Stages a PAUSED multi-card **carousel** ad in a fresh dedicated campaign (per-card image + headline + own PDP link). Spec is a `CARDS` block at the top — clone it to make a Bandits/Rasta carousel |
| `upload_creative.py` | Uploads a single image file to the Meta ad-image library; prints the resulting `image_hash` |
| `create_custom_audience.py` | Creates a Page-Engager custom audience on the ad account; saves the ID to `command-center/presets/marketing.json` |
| `list_custom_audiences.py` | Lists custom audiences on the ad account (read-only) |
| `list_saved_audiences.py` | Lists saved audiences on the ad account (read-only) |
| `install_daily_digest_task.ps1` | PowerShell script to register `daily_digest.py` as a 9 AM PHT Windows Task Scheduler job |

**Run**

```sh
# Pull last 7 days of insights (summary)
python tools/meta_ads/pull_insights.py

# Pull with daily breakdown for 14 days
python tools/meta_ads/pull_insights.py --days 14 --daily

# Pull live adset/ad metadata
python tools/meta_ads/pull_live_meta.py

# Pull pixel event totals
python tools/meta_ads/pull_pixel_stats.py --days 7

# Daily digest to console only (no TG send)
python tools/meta_ads/daily_digest.py --dry

# Stage all IMAGE_APPROVED pipeline captions as PAUSED ads (dry-run first)
python tools/meta_ads/stage_ad.py --all --dry-run
python tools/meta_ads/stage_ad.py --all --budget 200

# Stage from a creative plan file
python tools/meta_ads/stage_creatives.py --plan .tmp/marketing-plan.json --dry-run
python tools/meta_ads/stage_creatives.py --plan .tmp/marketing-plan.json

# Stage a carousel ad (PAUSED) -- dry-run validates images/links first
python tools/meta_ads/stage_carousel_ad.py --dry-run
python tools/meta_ads/stage_carousel_ad.py

# Upload a single image, get its hash
python tools/meta_ads/upload_creative.py --file contents/ads/dubery_001.jpg --ad-account-id act_XXXXXXXXX

# List audiences
python tools/meta_ads/list_custom_audiences.py
python tools/meta_ads/list_saved_audiences.py --match "metro manila"

# Create a Page Engager audience (dry-run first)
python tools/meta_ads/create_custom_audience.py --dry-run
python tools/meta_ads/create_custom_audience.py --name "Page Engagers 365d" --retention-days 365
```

**Inputs / outputs**

| Tool | Reads | Writes |
|------|-------|--------|
| `pull_insights.py` | Meta Graph API | `.tmp/ad_insights.json` |
| `pull_live_meta.py` | Meta Graph API | `.tmp/marketing_live_meta.json` |
| `pull_pixel_stats.py` | Meta Graph API | `.tmp/pixel_stats.json` |
| `daily_digest.py` | Meta Graph API, local CC at `:8090/api/crm/orders` | `.tmp/daily_digest/YYYY-MM-DD.md`, `.tmp/daily_digest.log`; sends Telegram message |
| `stage_ad.py` | `.tmp/pipeline.json`, `contents/ads/dubery_<id>.*` | Meta Ads (campaign/adset/ad), `.tmp/pipeline.json` (status updated to `AD_STAGED`), `.tmp/ads_config.json` |
| `stage_creatives.py` | Plan JSON, `command-center/presets/marketing.json`, image files | Meta Ads (campaign/adset/ad), `.tmp/marketing-staged.json`, `.tmp/ads_config.json` |
| `stage_carousel_ad.py` | `CARDS` spec + local card images (in-script) | Meta Ads (new campaign/adset/carousel creative/ad, all PAUSED), `.tmp/outback_carousel_ids.json` |
| `upload_creative.py` | Local image file | Meta ad-image library (prints `image_hash`) |
| `create_custom_audience.py` | — | Meta custom audience, `command-center/presets/marketing.json` |

**Auth / env**

All scripts load `.env` from the project root via `python-dotenv`.

| Env var | Required by |
|---------|-------------|
| `META_ADS_ACCESS_TOKEN` | All scripts |
| `META_AD_ACCOUNT_ID` | All except `pull_pixel_stats.py` |
| `META_PAGE_ID` | `stage_ad.py`, `stage_creatives.py`, `create_custom_audience.py` |
| `META_PIXEL_ID` | `pull_pixel_stats.py`, `daily_digest.py` (has hardcoded fallback `1513349880261420`) |
| `TELEGRAM_BOT_TOKEN` | `daily_digest.py` |
| `TG_CHAT_ID` | `daily_digest.py` |
| `META_ADS_DAILY_BUDGET` | `stage_ad.py` (default P200/day if unset) |

Token needs `ads_management` or `ads_read` scope. Pixel stats also require business-asset access to the pixel.

**Gotchas**

- `stage_ad.py` reads from `.tmp/pipeline.json` — run `python tools/status.py` first to confirm it exists and is current.
- `stage_creatives.py` resolves audience presets from `command-center/presets/marketing.json`; saved-audience entries must include a `targeting` dict (fetch it with `list_saved_audiences.py`), not just an ID — the saved-audience ID is invalid in the API adset create call.
- `daily_digest.py` degrades gracefully if the Command Center at `:8090` is down — orders section shows empty rather than crashing.
- All staging scripts create PAUSED ads. Activate them manually in Ads Manager.
- **Newer Meta API required flags** (as of 2026-06): campaign create needs `is_adset_budget_sharing_enabled: False` (when using adset-level budgets); adset create needs `targeting.targeting_automation.advantage_audience: 0|1`. Missing either returns a 400 — both are baked into `stage_carousel_ad.py`.
- **Geo by exclusion:** to target Luzon+Visayas, `stage_carousel_ad.py` targets country `PH` and *excludes* the 6 Mindanao region keys (+ Cagayan Valley) rather than listing every include — Meta's PH region search omits some regions (e.g. CALABARZON), so exclusion is the safe approach. Mindanao keys: ARMM `4193`, Caraga `4192`, Davao `2825`, N. Mindanao `4190`, Soccsksargen `4191`, Zamboanga `2932`.
- **UTM with `{{ad.id}}`:** carousel card links carry `utm_content={{ad.id}}` — Meta substitutes the real ad id at delivery; the v3 cart.js reads `utm_content` for order attribution.
- `stage_ad.py` calls `tools/notion/sync_pipeline.py --sheets-only` after a successful run to sync the sheet.
