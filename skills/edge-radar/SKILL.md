---
name: edge-radar
description: Unified Edge-Radar skill for scanning markets, placing wagers, managing portfolio, settling bets, and researching edge across Kalshi sports, futures, and prediction markets. Covers all scripts, filters, risk gates, and workflows.
argument-hint: <action> [market/filter] [flags] — e.g., "scan nba", "bet mlb --unit-size 2", "status", "settle", "detail TICKER"
user-invocable: true
model: opus
disable-model-invocation: true
allowed-tools: Read, Bash, Glob, Grep
---

# Edge-Radar Skill

You are executing the `/edge-radar` skill. This is the unified command center for all Edge-Radar operations: scanning for edge, placing wagers, managing portfolio, settling bets, and researching markets.

## Parse Arguments

Arguments: `$ARGUMENTS`

Parse the user's intent from the arguments. The skill supports natural language — interpret what the user wants and route to the correct action.

### Action Routing

| User Says | Action | Notes |
|-----------|--------|-------|
| `status`, `portfolio`, `balance`, `positions` | **Status** | Show portfolio dashboard |
| `daily-summary`, `morning`, `digest` | **Daily Summary** | Morning P&L digest — yesterday + open exposure + today pending + 7d context |
| `settle`, `results`, `pnl` | **Settle & Report** | Settle completed bets, show P&L |
| `reconcile`, `sync` | **Reconcile** | Compare local log vs Kalshi API |
| `risk`, `limits`, `dashboard` | **Risk Dashboard** | Full risk check with limits |
| `scan <filter>`, `check <filter>`, `find <filter>` | **Scan** | Preview opportunities (no execution) |
| `bet <filter>`, `play <filter>`, `wager <filter>` | **Scan & Bet** | Scan then prompt to execute |
| `detail <TICKER>`, `lookup <TICKER>` | **Detail** | Deep dive on a single market |
| `odds <sport>` | **Raw Odds** | Show sportsbook odds without edge detection |
| `data <type>` | **Market Data** | Fetch stock/crypto/prediction market data |
| `backtest`, `analyze`, `performance` | **Backtest** | Run backtester on settled trades |
| Any sport/market name alone (e.g., `nba`, `mlb`, `crypto`) | **Scan** | Default to scan for that filter |

### Flag Parsing

| Flag | Default | Description |
|------|---------|-------------|
| `--unit-size N` or `$N` (dollar amount) | `$1.00` | Dollar amount per bet |
| `--max-bets N` | `5` | Maximum bets to place |
| `--min-edge N` | `0.03` global | Minimum edge; per-sport floors via `MIN_EDGE_THRESHOLD_<SPORT>` (run `doctor.py` for the live values) |
| `--execute`, `--go`, `--send-it` | off | Skip preview, execute immediately |
| `--dry-run`, `--preview` | on (default) | Preview only, no orders |
| `--save` | off | Save results as markdown report to `reports/` |
| `--date DATE` | (none) | Filter by date: `today`, `tomorrow`, `YYYY-MM-DD`, `mar31`, `03-30` |
| `--exclude-open` | off | Skip markets with existing open positions |
| `--budget X` | (none) | Max total batch cost — `10%` (of bankroll) or `15` (flat dollars). Scales contracts down to fit while preserving Kelly edge-weighting, but never below a bet's flat unit floor; drops lowest-composite bets if the floors alone don't fit (C11b) |
| `--pick '1,3,5'` | (none) | Cherry-pick specific rows from preview |
| `--ticker TICKER` | (none) | Target a specific Kalshi ticker |
| `--category CAT` | (none) | Market type: `game`, `spread`, `total`, `player_prop` |
| `--top N` | `20` | Number of opportunities to show |
| `--detail` | off | Show per-trade breakdown (for reports) |
| `--report-dir PATH` | (none) | Override report output directory (used in batch jobs) |
| `--rescan` | off | R26 (2026-04-29): force a live rescan even when a fresh scan-cache exists. Default behavior for `--execute --pick/--ticker` is to replay the cached preview so row indices match what you saw — this opts out per-call. |

---

## Unified Scanner Entry Point

**All scans should use `scripts/scan.py`** — the unified router that forwards to the correct scanner:

```bash
python scripts/scan.py sports --filter mlb --date today --save
python scripts/scan.py sports --unit-size 1 --max-bets 5 --budget 10% --date today --exclude-open --execute
python scripts/scan.py futures --filter nba-futures
python scripts/scan.py prediction --filter crypto
```

Market types: `sports`, `futures`, `prediction`. (`polymarket` / `poly` / `pm` were removed 2026-09-29 with the Polymarket venue — see CHANGELOG.)
Aliases: `sport` = `sports`, `pred` = `prediction`.

The `scan` subcommand is auto-inserted if omitted. All flags are forwarded directly.

---

## Action: Status

Show portfolio dashboard — balance, open positions, P&L, resting orders.

```bash
python scripts/kalshi/kalshi_executor.py status
```

Report the key numbers clearly: balance, number of open positions, today's P&L, any resting orders. Positions display Sport, Bet (matchup), Type (ML/Spread/Total/Prop), Pick (e.g., "Spurs win", "Over 220.5"), When, Qty, Cost, P&L. Done.

For a more detailed risk dashboard:

```bash
python scripts/kalshi/risk_check.py
```

Add `--save` to either command to persist as markdown report.

---

## Action: Daily Summary

Morning P&L digest. Joins yesterday's settlements (rolling 24h window) with currently open trade-log positions and today's pending events; optional live Kalshi balance + 7-day rolling context. Empty-day proof-of-life — still renders every section so a zero-bet day shows "the system ran" rather than going silent.

```bash
.venv/Scripts/python.exe scripts/kalshi/daily_summary.py --save
.venv/Scripts/python.exe scripts/kalshi/daily_summary.py --hours 48 --save     # custom window
.venv/Scripts/python.exe scripts/kalshi/daily_summary.py --no-bankroll         # skip Kalshi balance fetch
```

`--hours N` (default 24), `--out PATH`, `--no-bankroll` (offline), `--no-ops` (skip the ops-health table).

Sections: **Ops health** first (scheduled tasks, settlement, backup), then **Yesterday**, **Open Exposure**, **Pending Today**, **Context**. The `Daily-Summary` task runs it at 4:50 AM PT and emails it (`docs/task-schedules/README.md`).

---

## Action: Settle & Report

Update trade log with settled results, then show performance report.

```bash
python scripts/kalshi/kalshi_settler.py settle
python scripts/kalshi/kalshi_settler.py report --detail
python scripts/kalshi/kalshi_settler.py report --days 7          # Last week only
python scripts/kalshi/kalshi_settler.py report --days 30 --save  # Last month, save to file
```

Add `--save` to persist the report as markdown. Use `--days N` to filter to recent trades.

Reports include: P&L summary, win/loss record, edge calibration, CLV, plus dimensional breakdowns by confidence, category (ML/Spread/Total), sport, and edge bucket (3-5%, 5-10%, 10-15%, 15%+).

Summarize: total settled, wins, losses, net P&L, ROI, best/worst bets, which dimensions are profitable. Done.

---

## Action: Reconcile

Compare local trade log against the Kalshi API to catch discrepancies.

```bash
python scripts/kalshi/kalshi_settler.py reconcile
```

Report any mismatches. Done.

---

## Action: Risk Dashboard

Full portfolio risk check with limit status. Pulls live data from Kalshi API.

```bash
python scripts/kalshi/risk_check.py
```

| Report Flag | Shows |
|-------------|-------|
| `--report all` | Everything (default) |
| `--report positions` | Just open positions |
| `--report pnl` | Just P&L |
| `--report limits` | Just risk limit status |
| `--report reconciliation` | R5 (2026-04-27): trade-log ↔ settlement join audit. Counts, `trade_id` overlap %, orphan-window dates, and per-field coverage matrix for the R5 settlement-schema additions. |
| `--gate` | Exit code 1 if limits breached (for automation) |
| `--save` | Save dashboard as markdown |

---

## Action: Detail (Single Market Deep Dive)

```bash
python scripts/kalshi/edge_detector.py detail <TICKER>
```

Shows: matched sportsbook odds, de-vigged probabilities, fair value, edge, and confidence breakdown.

---

## Action: Raw Odds

Show sportsbook odds without running edge detection.

```bash
python scripts/kalshi/fetch_odds.py --market <sport>
```

Sports: `nba`, `nfl`, `mlb`, `nhl`, `ncaafb`, `ncaabb`, `soccer`, `mma`, `all`.

---

## Action: Market Data

Fetch market data for research.

```bash
python scripts/kalshi/fetch_market_data.py --type <type> [--symbols SYM1 SYM2] [--source kalshi]
```

Types: `stocks`, `prediction`, `crypto`, `account`, `all`.

---

## Action: Scan (Preview Only)

Run the appropriate scanner based on the filter. **No orders are placed.**

### Step 1: Check Status First

```bash
python scripts/kalshi/kalshi_executor.py status
```

If the daily loss limit is breached, **STOP** and inform the user. No new bets today.

### Step 2: Route to the Correct Scanner

**Use the unified entry point `scan.py`** — it routes to the correct scanner automatically.

**Sports (game betting):**
```bash
python scripts/scan.py sports \
  [--filter <sport>] \
  [--category <game|spread|total|player_prop>] \
  [--min-edge <threshold>] \
  [--top <N>] \
  [--date <DATE>] \
  [--exclude-open] \
  [--report-dir <PATH>] \
  [--save]
```

**Futures (championships):**
```bash
python scripts/scan.py futures \
  [--filter <sport>-futures] \
  [--min-edge <threshold>] \
  [--top <N>] \
  [--date <DATE>] \
  [--exclude-open] \
  [--save]
```

**Prediction markets:**
```bash
python scripts/scan.py prediction \
  [--filter <category>] \
  [--min-edge <threshold>] \
  [--top <N>] \
  [--date <DATE>] \
  [--exclude-open] \
  [--save]
```

**Direct scanner access** (still works for all scanners):
```bash
python scripts/kalshi/edge_detector.py scan [flags]
python scripts/kalshi/futures_edge.py scan [flags]
python scripts/prediction/prediction_scanner.py scan [flags]
```

### Step 3: Present Results

The scan table shows: **Sport** (NBA/NHL/MLB/etc.), **Bet** (matchup), **Type** (ML/Spread/Total/Prop), **Pick** (e.g., "Spurs win", "Over 220.5", "Blazers -7.5"), **When**, **Mkt**, **Fair**, **Edge**, **Conf**, **Score**, **Gate** (R18 — `ok` or a short label like `off` / `illiq` / `far` / `score` / `conf` / `no-fav` / `pred-off` / `live-off` showing which risk gate would reject this row at execute time).

When `--unit-size` is passed, the executor table shows: **Sport**, **Bet**, **Type**, **Pick**, **When**, **Qty**, **Price**, **Cost**, **Edge**.

Explain:
- How many opportunities were found and at what edge threshold
- Top 2-3 picks and why they have edge (plain language)
- Total estimated cost if all were executed
- For futures: note that capital is tied up for weeks/months
- For prediction markets: note settlement timing

---

## Action: Scan & Bet

Same as Scan above, but with execution. Follow all scan steps first, then:

### Step 4: Get Confirmation

Unless `--execute` or `--go` was passed, **always ask the user to confirm** before placing orders:

> "Found X opportunities. Ready to execute Y bets for ~$Z total. Go ahead?"

### Step 5: Execute

Once confirmed, add `--execute` to the scan command and **give it to the user to run themselves** as `! <command>` in the prompt. A PreToolUse hook (`scripts/hooks/guard_live_orders.py`, ER-01) blocks any agent-run command that can place orders, in every permission mode. All 4 scanners support `--execute`, `--unit-size`, `--max-bets`, and `--pick` directly.

**Sports:**
```bash
python scripts/scan.py sports \
  --filter <sport> --execute \
  [--unit-size <N>] [--max-bets <N>] [--budget <X>] [--min-edge <N>] \
  [--pick '1,3,5'] [--ticker <TICKER>] [--date <DATE>] [--exclude-open]
```

**Futures:**
```bash
python scripts/scan.py futures \
  --filter <sport>-futures --execute \
  [--unit-size <N>] [--max-bets <N>] [--budget <X>] [--min-edge <N>] \
  [--pick '1,3,5'] [--ticker <TICKER>]
```

**Prediction:**
```bash
python scripts/scan.py prediction \
  --filter <category> --execute \
  [--unit-size <N>] [--max-bets <N>] [--budget <X>] [--min-edge <N>] \
  [--pick '1,3,5'] [--ticker <TICKER>]
```

### Step 6: Report

After execution, summarize:
- Number of orders placed and total cost
- Updated balance
- Reminder to run `/edge-radar settle` after events complete

---

## References

Read the one a request needs; each holds sections moved verbatim from this file (ER-47).

| File | Read it for |
|:--|:--|
| [references/filters.md](references/filters.md) | Every `--filter` name per scanner, raw ticker prefixes |
| [references/risk-limits.md](references/risk-limits.md) | Long-form gate and sizing notes, the preview **Gate** column labels |
| [references/operations.md](references/operations.md) | Makefile targets, daily workflow, Task Scheduler and `.bat` wrappers |
| [references/internals.md](references/internals.md) | Routing examples, report output, low-level API, signals, trade logging, calibration, backtesting |

---

## Safety Rules

1. **Always check status first** before any scan or bet — if daily loss limit is breached, STOP.
2. **Never execute yourself.** Order-placing commands are the user's to run (`! <command>`); the ER-01 hook blocks them for agents.
3. **Preview is the default** — every scan shows a table first, orders only placed with `--execute`.
4. **All 21 risk gates** in the AGENTS.md table are checked before every order, plus the resting-order janitor at the top of every live execute run. Gate notes: [references/risk-limits.md](references/risk-limits.md).
5. **API keys are in `.env`** — never print, log, or expose them.
6. **R26 row-order lock for `--pick`** — when running `--execute --pick/--ticker`, keep filter args identical to the previous preview so the cached row→ticker mapping replays. If anything differs, the executor prints a bold red banner and rescans (different rows). Pass `--rescan` only when you intend a fresh ranking.
7. **R8 cross-category dedup is opt-in** — by default ML+Total+Spread on the same game survive as 3 distinct bets (current behavior). To collapse them per sport, set `CROSS_CATEGORY_DEDUP_<SPORT>=true` (e.g. `CROSS_CATEGORY_DEDUP_NBA=true`); when active, the dedup banner names the sports (`Deduped correlated brackets: 12 -> 8 opportunities (cross-category: ['nba'])`). Per-sport `false` overrides the global flag in either direction.
