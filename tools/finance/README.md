# finance/

Turns Gmail into a near-real-time feed of BPI deposit-account activity.

BPI emails a confirmation within seconds of every deposit-account movement, so
the transaction history is already sitting in Gmail. This reads it — no bank
scraping, no stored banking credentials, no fragile browser automation.

| Script | Purpose |
|--------|---------|
| `sync_bpi_email.py` | Parse BPI notification emails → structured transactions → `EA-brain/finance/bpi-transactions.json` |

## Usage

```bash
python tools/finance/sync_bpi_email.py                # last 90 days, merge + write
python tools/finance/sync_bpi_email.py --days 365     # wider window
python tools/finance/sync_bpi_email.py --summary      # monthly in/out/net rollup
python tools/finance/sync_bpi_email.py --dry-run      # parse + report, write nothing
```

Merges on Gmail message id, so re-running is safe — it never duplicates.

## What it captures

| Direction | Kind | Email |
|---|---|---|
| in | `instapay_in` | "Incoming Interbank Funds Transfer Confirmation" |
| out | `instapay_out` | "Interbank Funds Transfer Confirmation" |
| out | `qr_payment` | "Pay \<merchant\> via QR" |
| out | `transfer` | "Funds Transfer Confirmation" / Transfer Money |
| out | `prepaid_load` | "Load Prepaid Phone Confirmation" |
| internal | any | Counterparty matches `OWN_ACCOUNTS` |

## What it does NOT capture

These are structural gaps in what BPI emails, not parser bugs:

- **Credit card purchases.** No email is sent. Card spend appears only on the
  monthly eSOA — see `EA-brain/finance/README.md` for that flow.
- **Payroll / salary credits.** Posted internally with no notification.
- **Cash deposits, ATM, over-the-counter.** No email.

So this file is a *partial* picture by construction. The monthly deposit-account
eStatement is the only ground truth for total inflow.

## `OWN_ACCOUNTS` — read this before trusting any total

Moving money between RA's own accounts generates the same email as a real
payment. Left unhandled, a ₱40k Floater→Savings shuffle inflates outflow by ₱40k
and the burn figure becomes fiction. Accounts listed in `OWN_ACCOUNTS` at the top
of the script are reclassified `internal` and excluded from both in and out.

`--summary` prints any counterparty seen on **both** sides of the ledger — a
strong hint it's another of RA's own accounts. Confirm and add it, or totals stay
wrong. Currently listed: PAYROLL ACCOUNT, Floater, SAVINGS, GoTyme `01XXXXX48927`.

## Auth

Uses the shared Google OAuth token via `tools/auth.py` — same one behind `gog`.
Read-only against Gmail.
