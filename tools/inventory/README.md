# tools/inventory

v1 inventory tracking for DuberyMNL. Source of truth = an **"Inventory" tab** in the
**Orders spreadsheet** (`ORDERS_SHEET_ID`). Built 2026-05-31.

**Not an ad-gate.** Stock-out never pauses ads (backorder model — see the
`delivery-pricing-policy` memory). This system only (a) tracks qty per SKU,
(b) auto-decrements on fulfilled orders, (c) alerts when stock is low so RA reorders.

## Files
| File | Purpose |
|------|---------|
| `inventory.py` | Core module + CLI. Catalog, seed data, SKU normalizer, read/adjust, status. |
| `sync_orders.py` | Decrement on fulfilled orders + low-stock Telegram alert. |

## SKU keys
Format `"<Series> – <Color>"` (EN-DASH), matching the Orders sheet `Items` cells and
`chatbot/crm_sync.py::_parse_items`. Aliases handle colloquial names —
e.g. **"Bandits – Red" → "Bandits – Matte Black"** (the matte-black/ruby-lens model).

## Transport
Uses **`requests` + a bearer token** against the Sheets REST API — NOT
`googleapiclient`/`httplib2`, which hangs on `sheets.googleapis.com` from some hosts
(see `reference_googleapi_httplib2_fallback`). Calls are slow (~30–60s) but reliable.
Auth: `token.json` (repo root, Sheets scope) locally / ADC on Cloud Run.

## Commands
```bash
python tools/inventory/inventory.py --check-auth          # verify Sheets access
python tools/inventory/inventory.py --init                # create + seed the Inventory tab
python tools/inventory/inventory.py --add-order-columns   # add Fulfilled/Decremented (K/L) to Orders
python tools/inventory/inventory.py --list                # print current stock + status
python tools/inventory/inventory.py --adjust "Bandits – Green" -1
python tools/inventory/sync_orders.py [--dry]             # decrement fulfilled orders + low-stock alert
```

## How decrement works
1. RA marks an order **Fulfilled** (column K on the Orders tab) — set it to `TRUE`/`yes`/`x`/`done` on dispatch.
2. `sync_orders.py` finds rows where `Fulfilled` is truthy and `Decremented` (col L) is blank,
   parses `Items`+`Qty`, decrements the matching SKU, and stamps `Decremented` = timestamp. Idempotent.
3. Unparseable/unknown SKUs are marked `SKIP: ...` in col L (not silently lost) — fix the row + clear L to retry.

## Low-stock alert
Threshold = **1** (alert when qty ≤ 1; 0 = OOS). After each sync, SKUs at/under threshold
trigger ONE Telegram message (same bot/chat as the daily digest). Deduped via
`.tmp/inventory_alerted.json` so a still-low SKU doesn't re-ping; restocking above
threshold resets it.

## Scheduling (run after `--init` succeeds)
Register `sync_orders.py` hourly via Task Scheduler (mirror the S4U + at-startup pattern in
`reference_service_resilience_tasks` so it survives reboots). Needs an elevated shell.

## Cron / dependencies
- Needs network to `sheets.googleapis.com` (works on the laptop; the chatbot already writes there).
- Reuses `chatbot/crm_sync.py::_parse_items` for SKU parsing — keep them in sync.
