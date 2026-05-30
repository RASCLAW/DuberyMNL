# orders — Sync orders from Sheets and report inventory / reorder needs

**What it does**
- Pulls the Orders tab from the DuberyMNL Google Sheet and saves it to `orders/orders.json`.
- Aggregates sold and pending units per SKU against `inventory.json` to produce an on-hand / sold-history report.
- Cross-references `orders/reorder.json` target-stock levels to show how many units to order per SKU.

**Key files**

| Script | Purpose |
|--------|---------|
| `sync_orders.py` | Fetches the Orders sheet (cols A–L) via Google Sheets API and writes `orders/orders.json`. |
| `inventory_report.py` | Reads `orders/orders.json` + `inventory.json`; computes per-SKU on_hand / sold_history / pending; prints a flagged table (OOS / LOW). |
| `reorder_report.py` | Imports `compute_report()` from `inventory_report`; reads `orders/reorder.json` for target_stock; prints Sold / Pending / On Hand / Target / To Order per SKU. |

**Run**

```bash
# 1. Pull latest orders from Sheets
python tools/orders/sync_orders.py

# 2. Print inventory status (OOS / LOW flags)
python tools/orders/inventory_report.py

# 3. Print reorder quantities against target stock levels
python tools/orders/reorder_report.py
```

**Inputs / outputs**

| Script | Reads | Writes |
|--------|-------|--------|
| `sync_orders.py` | Google Sheet `1vS-yuFWovqHYWrFte4QXJLtH3Q2-BRDi6i9P4-vXbkA` tab `Orders` (cols A:L) | `orders/orders.json` |
| `inventory_report.py` | `orders/orders.json`, `inventory.json` | stdout only |
| `reorder_report.py` | `orders/orders.json`, `inventory.json`, `orders/reorder.json` | stdout only |

**Auth / env**

- Uses the shared `tools/auth.py` helper (`get_credentials()`); expects OAuth credentials in `.env` (loaded from repo root).
- Google OAuth scope: `spreadsheets.readonly` (Sheets API v4).
- No paid API calls — no extra confirmation needed before running.

**Gotchas**

- `sync_orders.py` must be run first before `inventory_report.py` or `reorder_report.py` (both read `orders/orders.json`).
- Column K (Status) and L (PickupTimestamp) have no sheet headers; `sync_orders.py` synthesizes them automatically.
- `inventory.json` is the authoritative on-hand count and must be updated manually after each restock or shipment.
- Orders with Status `CANCELED` are skipped entirely in inventory calculations; blank Status is treated as pending (not delivered).
