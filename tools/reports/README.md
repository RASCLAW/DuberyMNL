# tools/reports

Generated performance/analysis reports for DuberyMNL.

## `build_ad_report.py`

Builds an HTML ad-performance report with creative thumbnails — combines Meta ad insights, the Orders sheet, and a rule-based per-ad verdict / why / opportunity. Prototype from session 176 (memory `project_ad_report_builder.md`); promoted from `.tmp/` on 2026-06-05 and re-anchored to the repo root.

**Input:** a Meta ad-insights snapshot JSON. Defaults to `.tmp/ad_insights.json` (regenerable scratch); pass a different path as the first arg.

**Output:** `.tmp/ads_report.html` (deliverable; regenerable, so it stays in `.tmp`).

**Needs:** `META_ADS_ACCESS_TOKEN` in `.env`; Google Sheets auth via `tools/auth.py` (reads the Orders sheet). Makes live Meta + Sheets calls.

```
# from repo root
python tools/reports/build_ad_report.py                      # uses .tmp/ad_insights.json
python tools/reports/build_ad_report.py path/to/insights.json # explicit input
```

> Hard-coded dates (`CAMPAIGN_START`, `PIXEL_INSTALL`) and `ORDERS_SHEET_ID` are baked in near the top — update them when the reporting window changes.
