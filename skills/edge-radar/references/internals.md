# Internals

*Reference for the [`/edge-radar` skill](../SKILL.md).* Routing examples, report output, low-level API access, edge signals, trade logging, calibration and backtesting.

---

## Routing Examples

| User Says | Command |
|-----------|---------|
| `/edge-radar nba` | `scan.py sports --filter nba` |
| `/edge-radar bet mlb --unit-size 2 --max-bets 10` | `scan.py sports --filter mlb --unit-size 2 --max-bets 10` then confirm then `--execute` |
| `/edge-radar mlb --date tomorrow --exclude-open` | `scan.py sports --filter mlb --date tomorrow --exclude-open` |
| `/edge-radar nba --category spread` | `scan.py sports --filter nba --category spread` |
| `/edge-radar nba-futures` | `scan.py futures --filter nba-futures` |
| `/edge-radar superbowl` | `scan.py futures --filter nfl-futures` |
| `/edge-radar status` | `kalshi_executor.py status` |
| `/edge-radar settle` | `kalshi_settler.py settle` + `report --detail` |
| `/edge-radar reconcile` | `kalshi_settler.py reconcile` |
| `/edge-radar risk` | `risk_check.py` |
| `/edge-radar detail KXNBAGAME-26MAR25LALBOS-LAL` | `edge_detector.py detail KXNBAGAME-26MAR25LALBOS-LAL` |
| `/edge-radar bet nba --go --unit-size 1 --max-bets 3` | `scan.py sports --filter nba --execute --unit-size 1 --max-bets 3` (skips the preview step; the user runs it as `! <command>`, since the ER-01 hook blocks agent-run order commands) |
| `/edge-radar scan all` | `scan.py sports` (no filter = all sports) |
| `/edge-radar scan all --date today` | `scan.py sports --date today` (all sports, today only) |
| `/edge-radar bet all --unit-size 1 --max-bets 10` | `scan.py sports --unit-size 1 --max-bets 10` then confirm then `--execute` |
| `/edge-radar bet mlb --pick '1,3,5'` | `scan.py sports --filter mlb --execute --pick '1,3,5'` (R26: replays last `--filter mlb` preview from `data/cache/last_scan.json`; mismatched filter args trigger a red banner + rescan) |
| Two-call pattern (preview, then pick) | `scan.py sports --filter mlb --exclude-open` (preview), then `scan.py sports --filter mlb --exclude-open --pick '1,3' --execute` — keep the same flags so R26 replays cleanly. Add `--rescan` to force a live rescan. |
| `/edge-radar bet mlb --budget 10% --max-bets 5` | `scan.py sports --filter mlb --budget 10% --max-bets 5` then confirm then `--execute` |
| `/edge-radar bet all --budget 15 --unit-size 1` | `scan.py sports --budget 15 --unit-size 1` then confirm then `--execute` |

---

## Report Output

When `--save` is used, the report format depends on whether `--unit-size` was passed:

**With `--unit-size` (execution report):** Sport, Bet, Type, Pick, Qty, Price, Cost, Edge, total cost.

**Without `--unit-size` (scan report):** Sport, Bet, Type, Pick, When, Mkt, Fair, Edge, Conf, Score, Gate.

| Scanner | Report Path |
|---------|-------------|
| Sports (scan) | `reports/Sports/{date}_{sport}_sports_scan.md` |
| Sports (execution) | `reports/Sports/{date}_{sport}_sports_execution.md` |
| Futures | `reports/Futures/{date}_{category}_futures_scan.md` |
| Settle/P&L | `reports/Accounts/Kalshi/` |
| Automated | `reports/Sports/schedulers/same-day-executions/` |

---

## Low-Level API Access

For debugging or raw market queries:

```bash
python scripts/kalshi/kalshi_client.py balance
python scripts/kalshi/kalshi_client.py positions
python scripts/kalshi/kalshi_client.py orders
python scripts/kalshi/kalshi_client.py markets --limit 50
python scripts/kalshi/kalshi_client.py market --ticker <TICKER>
```

---

## Edge Detection Signals

The scanner uses 9 signals to detect mispriced contracts:

| Signal | Source | What It Does |
|--------|--------|-------------|
| Normal CDF Model | Math | Spread/total probabilities via bell curve with sport-specific stdev |
| Sharp Book Weighting | Odds API | Pinnacle 3x, DraftKings 0.7x — sharp lines pull consensus |
| Team Stats | ESPN/NHL/MLB APIs | Win%, goal/run differential validates book fair value |
| Sharp Money | ESPN | Open-vs-close odds detect reverse line movement |
| Pitcher Matchups | MLB Stats API | ERA, FIP, WHIP, K/9, rest days — adjusts total stdev |
| Rest Days / B2B | ESPN | NBA/NHL back-to-back detection — fatigue adjusts stdev + confidence |
| Weather | NWS | 61 NFL/MLB venue forecasts adjust total expectations |
| Book Disagreement | Odds API | >4pt spread range flags injury news |
| CLV Tracking | Kalshi | Closing line value validates model accuracy over time |

MLB pitcher data is fetched in parallel (ThreadPoolExecutor, 8 workers) for speed.

---

## Trade Logging

Orders are logged to `data/history/kalshi_trades.json` with **fill-based accounting**:
- `requested_contracts` / `requested_cost` — what we asked for
- `filled_contracts` / `filled_cost` — what the exchange actually executed
- `fill_status` — `resting` | `partial` | `filled`
- `venue` — always `kalshi` now (added with PM2c for Polymarket, which was removed 2026-09-29; older records lack the field, and readers default to `kalshi`)

Resting orders (zero fills) are excluded from exposure calculations and settlement. The settler, risk dashboard, and P&L reports all use filled values, not requested. Writes go through a cross-process lock (M2) so concurrent settle/execute merge safely.

> **The trade log accumulates orphans that never close out.** Two known kinds: records with `status: "error"` (an API rejection — e.g. six World Cup rows from the 2026-06-20 v1→v2 410 outage, four of which were successfully re-placed two days later) and zero-fill `resting` orders whose market has since closed. Both sit in the log as permanently "open." This does **not** affect risk gating — Gate 5 reads live positions from the Kalshi API, not the log — but it inflates any open-position count derived from the log, so cross-check against `kalshi_executor.py status` before reporting exposure.

---

## Calibration

```bash
python scripts/kalshi/model_calibration.py --save        # Full calibration report
python scripts/kalshi/model_calibration.py --days 30     # Last 30 days only
```

Reports: Brier score, calibration curve (predicted vs realized), dimension breakdowns, confidence x category cross-tab, prioritized recommendations.

---

## Backtesting

```bash
python scripts/backtest/backtester.py                        # Full analysis
python scripts/backtest/backtester.py --simulate --save       # Strategy comparison + save
python scripts/backtest/backtester.py --sport mlb             # MLB only
python scripts/backtest/backtester.py --category total        # Totals only
python scripts/backtest/backtester.py --confidence medium     # Medium confidence only
python scripts/backtest/backtester.py --min-edge 0.10         # Edge >= 10%
python scripts/backtest/backtester.py --after 2026-04-01      # Recent trades only
```

Reports: equity curve, max drawdown, Sharpe ratio, profit factor, win/lose streaks, breakdowns by sport/category/confidence/edge bucket, calibration curve (predicted prob vs actual win rate), strategy simulation comparing filter strategies.

Flags: `--sport`, `--category`, `--confidence`, `--min-edge`, `--after`, `--simulate`, `--save`, `--quiet`.
