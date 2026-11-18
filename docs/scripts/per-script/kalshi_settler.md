# kalshi_settler.py — Settlement & P&L Reporting

**Location:** `scripts/kalshi/kalshi_settler.py`

**When to use:** After games/events have resolved, to update your trade log with results and generate performance reports.

---

## `settle` -- Update Trade Log

```bash
python scripts/kalshi/kalshi_settler.py settle
```

Polls the Kalshi API for settlements, matches to your trade log, calculates P&L per trade, and updates records. No flags.

Run this after games complete to move trades from "open" to "settled" with realized P&L.

Before settling it recovers anything an execute run could not finish writing: pending order files over
15 minutes old (booked if Kalshi has the order filled or resting, dropped otherwise; ER-13), then the
trade journal (BUG-03), then it re-reads open resting and partial orders so late fills count (BUG-01).

---

## `report` -- Performance Report

```bash
python scripts/kalshi/kalshi_settler.py report [flags]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--detail` | off | Show per-trade breakdown table (with bet type and pick labels) |
| `--save` | off | Save markdown report to `reports/Accounts/Kalshi/kalshi_report_YYYY-MM-DD.md` |
| `--days N` | all time | Only include trades settled in the last N days |

### Examples

```bash
# Quick summary (win/loss, net P&L, ROI)
python scripts/kalshi/kalshi_settler.py report

# Last 7 days only
python scripts/kalshi/kalshi_settler.py report --days 7

# Last month with full detail
python scripts/kalshi/kalshi_settler.py report --days 30 --detail

# Full detail with file export
python scripts/kalshi/kalshi_settler.py report --detail --save
```

### Report Includes

- Win/loss record, net P&L, ROI, profit factor
- Best/worst trades
- Edge calibration (estimated vs. realized)
- CLV (Closing Line Value) tracking
- **By Confidence** — win rate, P&L, ROI, avg edge per confidence level
- **By Category** — ML vs Spread vs Total vs Prop performance
- **By Sport** — NBA vs NHL vs MLB vs NFL etc.
- **By Edge Bucket** — 3-5%, 5-10%, 10-15%, 15%+ win rates and ROI

---

## `reconcile` -- Verify Trade Integrity

```bash
python scripts/kalshi/kalshi_settler.py reconcile
```

Compares your local trade log against the Kalshi API to find:

- Trades in your log but not on Kalshi (demo/cancelled)
- Positions on Kalshi not in your log (placed manually)
- Quantity mismatches between local and API

No flags. Run periodically to keep your trade log accurate.

---

## `backfill-fees` -- Repair Recorded Fees (S23b)

```bash
python scripts/kalshi/kalshi_settler.py backfill-fees           # dry run
python scripts/kalshi/kalshi_settler.py backfill-fees --apply   # write
```

Re-stamps the real `fee_cost` from `/portfolio/fills` onto every trade row,
and moves each matching settlement's `net_pnl` by the difference.

Needed because `settle` only stamps fees on rows it is settling *now*, so a
fee-reading bug leaves the closed book behind it permanently wrong. That is
what happened: the reader looked for `fee_dollars` / `taker_fee_dollars` /
`fee`, and the field is **`fee_cost`**, so 133 rows recorded a measured $0.00
they never paid.

Only `fees` changes. `won`, `revenue`, `cost` and `contracts` are never
touched, and `roi` is recomputed from the new `net_pnl`. Dry run by default --
it prints the row count and the total movement before you commit to it.
