# orders — Orders sync, inventory, low-stock alert, reorder

Per-SKU inventory + sales tracking for DuberyMNL. `inventory.json` (repo root) is the
authoritative on-hand count; source orders = the DuberyMNL Orders Google Sheet.

**Backorder model:** stock-out does NOT pause ads (see `delivery-pricing-policy` memory).
This system tracks stock, auto-decrements on delivered orders, and pings RA to reorder.

## Files
| Script | Purpose |
|--------|---------|
| `sync_orders.py` | Fetch the Orders sheet (A:L) → `orders/orders.json`. requests transport (googleapiclient times out here). |
| `mark_delivered.py` | Set an order's Status (col K) → DELIVERED in the Orders sheet by `--name`/`--row`. `--dry-run` first. requests transport. |
| `inventory_report.py` | `compute_report()`: per-SKU on_hand / sold_history / sold_after_baseline / pending / **remaining**. CLI prints a flagged table (OOS/LOW). |
| `stock_alert.py` | Low-stock **Telegram** alert (remaining ≤ threshold). Reads local files only → runs anywhere. Deduped. |
| `reorder_report.py` | Sold / Pending / On Hand / Target / To Order per SKU (vs `orders/reorder.json`). |
| `run_stock_cron.bat` | Hourly job: `sync_orders` → `stock_alert`. Wired to Task Scheduler **DuberyMNL-StockAlert**. |

## Auto-decrement model (the key mechanic)
- `inventory.json` `on_hand` = physical count **as of `_as_of`** (date key).
- `remaining = max(0, on_hand − delivered-since-_as_of)`. Orders with `Status=DELIVERED` (col K) dated AFTER `_as_of` auto-decrement; `CANCELED` skipped; blank Status = pending.
- **On restock:** set each `on_hand` to the new physical total AND bump `_as_of` to that date (so prior deliveries don't re-subtract). Keep `orders/reorder.json` on_hand in sync.
- Threshold: `LOW_THRESHOLD = 1` in `inventory_report.py` (remaining ≤ 1 = LOW, 0 = OOS).

## SKU map
`inventory_report._DISPLAY_MAP` maps order `Items` text → SKU slug. Includes `outback-stripe`
and **"bandits red" → bandits-matte-black** (RA's name for the matte/ruby model);
"bandits black" → glossy-black.

## Run
```bash
python tools/orders/sync_orders.py         # refresh orders.json (laptop network)
python tools/orders/mark_delivered.py --name "Roy Cañete" --dry-run   # then drop --dry-run to write
python tools/orders/inventory_report.py    # stock table (OOS/LOW)
python tools/orders/stock_alert.py [--dry] # low-stock TG alert (deduped)
python tools/orders/reorder_report.py      # reorder quantities
```

## Cron
Task Scheduler **DuberyMNL-StockAlert** runs `run_stock_cron.bat` hourly (basic logon task,
registered 2026-05-31; logs to `.tmp/stock_cron.log`). To survive reboots without a login,
upgrade it to S4U + at-startup (elevated) like the services in `reference_service_resilience_tasks`.

## Auth / env
- `sync_orders.py` → `tools/auth.py::get_credentials()` (googleapiclient/httplib2) — works on the laptop; hangs from some sandboxes.
- `stock_alert.py` → local files + `requests` for Telegram (`TELEGRAM_BOT_TOKEN` + `TG_CHAT_ID` in `.env`) — runs anywhere.

## Gotchas
- Run `sync_orders.py` before the reports (they read `orders/orders.json`).
- Two on_hand copies: `inventory.json` (reports) + `orders/reorder.json` (reorder). Keep in sync.
- `.tmp/orders_stock_alerted.json` dedupes alerts; delete it to force a re-ping.
