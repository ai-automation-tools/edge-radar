# Edge-Radar

> Multi-agent edge-detection and execution system for prediction markets and sports betting on **Kalshi**. (Polymarket US was removed 2026-09-29 — *CHANGELOG 2026-09-29*.)
> Research-first, execute-second. No action without documented rationale, risk check, and position-size calculation.

---

## How to Use This File

- This file (`AGENTS.md`) is read by every coding agent. `CLAUDE.md` imports it and adds the Claude Code-only notes (memory index, skill junctions).
- **This file holds the rules. `docs/CHANGELOG.md` holds the reasoning and evidence behind each one**, under its dated entry (cited below as e.g. *CHANGELOG 2026-07-27*). When a rule changes, update both.
- Working branch: **`mike_desktop`** (deploy/default: `master`). `mike_win-desktop` is retired — do not commit to it.
- The Risk Limits block lists **code defaults**; the live `.env` overrides several. `python scripts/doctor.py` is the source of truth for what is actually running.
- **The homepage's data-flow diagram is generated and pinned to code.** `docs/diagrams/betting-data-flow.json` cites line ranges in `edge_detector.py`, `kalshi_executor.py`, `kalshi_settler.py`, `odds_cache.py` and friends. When a change touches the betting path (sources, filter, fair value, edge, gates, sizing, order, trade log, settlement, calibration), or `python scripts/diagrams/build_betting_diagram.py --check` reports drift, update the diagram in the same PR: commit the code, re-read the changed ranges, fix the JSON (line ranges, labels, flows, cards), then `--pin-head`. Never hand-edit the `.html`/`.png`. Steps: `docs/diagrams/README.md`.

---

## What's Live

| Domain | Coverage | Data Sources |
|:-------|:---------|:-------------|
| **Sports betting** | NBA, NHL, MLB, NFL, NCAA, MLS, soccer, UFC, boxing, F1, NASCAR, PGA, IPL, Wimbledon tennis, esports (31 game filters, 8 futures). **World Cup (F3) is OFF; NFL and NCAAF are both on a 0.06 pilot floor (S1b/S21c, lowered from 0.08 on 2026-09-19)** | The Odds API, ESPN, NHL/MLB Stats, NWS |
| **Prediction markets** | Crypto (BTC, ETH, XRP, DOGE, SOL), weather (13 cities), S&P 500 | CoinGecko, Yahoo Finance, NWS |
| **Championship futures** | NFL, NBA, NHL, MLB, PGA | Sportsbook futures odds |
| **Execution pipeline** | Unified scan → risk-check → size → execute | Kalshi API (RSA-signed) |

**Planned, not built:** Manifold, Alpaca stocks/options, Coinbase/Binance, DFS + sportsbook APIs, Fed/CPI/GDP markets.

---

## Strategy Profiles (P1)

Two strategies, **one codebase**, two Kalshi wallets. A profile is a named
overlay file, `.env.<name>`, applied on top of the base `.env`.
**The `longshot` profile was retired 2026-09-27** (its scheduled task is gone);
the mechanism stays, and the examples below show its syntax:

```bash
python scripts/scan.py sports  --profile longshot --filter mlb --date today
python scripts/scan.py futures --profile longshot --filter nba-futures
EDGE_RADAR_PROFILE=longshot python scripts/doctor.py    # non-scan entry points
```

| Profile | Wallet | `DRY_RUN` | Overrides |
|:--|:--|:--|:--|
| `main` (default) | subaccount 0 | `false` — **live** | none; the base `.env` |
| ~~`longshot`~~ | subaccount 1 (~$40) | `true` | **Retired 2026-09-27** — strategy abandoned, `Longshot` task deleted. Was `MIN_MARKET_PRICE=0.08`, `MAX_PER_EVENT_FUTURES=3` |

- **`KALSHI_SUBACCOUNT` is the only thing that isolates money.** Not a second
  API key, and not a second checkout of this repo — both still draw on one
  balance, and each copy's `MAX_DAILY_LOSS` and exposure gates would see only
  their own activity, never the combined draw-down. A subaccount is an
  exchange-enforced separate wallet under one login (Advanced API tier).
  Bankroll isolation is an **account**-level fact, so it never justified a fork.
- **Only what the overlay names differs; everything else is inherited** —
  risk gates, fee model, calibration, per-sport floors, the NFL pilot floor, and
  every future fix, in lockstep across both books. This is the point. The
  forked repo it replaced ran `MAX_OPEN_EXPOSURE_PCT=0`,
  `MAX_SEGMENT_EXPOSURE_PCT=0`, `MAX_DAYS_TO_EVENT_FOR_GAME_MARKETS=0`,
  `MAX_BET_SIZE=100` and `MAX_DAILY_LOSS=250` — not by decision, but because
  nobody re-tightened the shipped defaults after cloning.
- **It fails CLOSED.** A missing `.env.<name>` raises rather than falling back
  to the base `.env`, because the base `.env` is the live-money wallet: a
  typo'd `--profile longshto` that silently resolved to `main` would run one
  strategy's intent against the other's bankroll, live. Same reasoning as S3's
  venue-eligibility check.
- **Every trade row carries `"profile"`**, mirroring the `"venue"` field one level
  up. Absent on pre-P1 rows, so **readers must default to `"main"`**. One trade
  log holds both books — and this is *better* evidence than two repos gave,
  because both now run identical code, odds cache, fees and calibration, so a
  comparison measures the strategies rather than the codebase versions.
- **`--profile` is consumed by `scan.py`**, not forwarded to the scanners, and
  reaches the child as `EDGE_RADAR_PROFILE`. `load_dotenv()` does not override
  variables already set, so the overlay survives the child's own `.env` load.
- **Do not fork this repo to try a strategy.** The Edge-Radar-Longshot fork
  lasted six days and, on a delta of two env vars, drifted into a live defect
  in each direction: it scanned zero college football all September on a stale
  `KXNCAAFBGAME` prefix and was missing S26/S27, while this side was missing
  its `dry_run` trade-row fix. Add a profile instead.
  *CHANGELOG 2026-09-10 (P1).*
- **How the two books stay separate, end to end** — selection, settings, money
  and data as four independent layers, plus what is deliberately *shared* and
  the surfaces that are still pooled:
  **[docs/longshot/README.md](docs/longshot/README.md)**.

---

## Project Structure

```
Edge-Radar/
├── AGENTS.md                  # This file — rules of engagement
├── CLAUDE.md                  # @AGENTS.md + Claude Code-only notes
├── .env.example               # Template for required env vars
├── Makefile                   # make scan-mlb, make test, make settle, ...
├── .claude/
│   ├── agents/                # Agent definitions (roster below)
│   ├── html/                  # Personal ops deck → edge-radar.mikesailab.com (GitHub Pages)
│   ├── memory/MEMORY.md       # Persistent memory index
│   └── skills/                # Junctions → /skills (git-ignored)
├── site/                      # Public page → edge-radar.ai-automation-tools.dev (Vercel root)
├── skills/                    # Canonical skill source — EDIT HERE
│   ├── edge-radar/            # /edge-radar — scan/bet/status/settle/risk
│   └── edge-radar-analysis/   # /edge-radar-analysis — performance report
├── app/
│   ├── config.py              # Single source of truth for env-driven knobs
│   └── domain/                # Opportunity, RiskDecision, Execution*, MarketClient
├── scripts/
│   ├── scan.py                # Unified entry point
│   ├── doctor.py              # Environment validator
│   ├── kalshi/                # client, executor, settler, edge, risk
│   ├── prediction/            # Crypto, weather, S&P
│   ├── shared/                # Stats, weather, logging, odds cache
│   ├── backtest/              # backtester.py, correlation_check.py
│   ├── diagrams/              # build_betting_diagram.py — rebuild/--check the homepage diagram
│   ├── schedulers/            # Automation + Windows Task Scheduler installer
│   └── setup/link_skills.ps1  # Recreate .claude/skills junctions after clone
├── tests/                     # pytest suite (make test); test_site.py pins both static pages
└── docs/                      # Index: docs/README.md
    ├── CHANGELOG.md           # Project history — the "why" behind the rules here
    ├── ROADMAP.md             # Open work only (history lives in CHANGELOG)
    ├── diagrams/              # Betting data-flow diagram: JSON source (edit) + generated HTML/PNG
    ├── kalshi/                # Sports, prediction, futures guides
    ├── scripts/               # SCRIPTS_REFERENCE.md + per-script docs
    ├── setup/                 # Setup, architecture, automation, MCP servers
    └── task-schedules/        # Scheduled task inventory
```

**Runtime dirs** (gitignored, auto-created): `data/`, `logs/`, `reports/`, `.env`.

**Skills:** `edge-radar` and `edge-radar-analysis` are tracked in `skills/` at the repo root — the canonical source; any agent can read their `SKILL.md`. **Edit `skills/`**; how Claude Code loads them is in `CLAUDE.md`.

---

## Agent Roster

`MARKET_RESEARCHER → DATA_ANALYST → RISK_MANAGER → TRADE_EXECUTOR → PORTFOLIO_MONITOR`

| Agent | Role | Access |
|:------|:-----|:-------|
| `MARKET_RESEARCHER` | Scan & score opportunities | Read-only — market data, news, odds |
| `DATA_ANALYST` | Quantitative modeling & backtesting | Read-only — builds models |
| `RISK_MANAGER` | Gate all executions | Veto authority over the executor |
| `TRADE_EXECUTOR` | Place & manage orders | Write — executes trades |
| `PORTFOLIO_MONITOR` | Real-time P&L & alerts | Read — positions, sends alerts |

---

## Security & Safety Rules

> **NON-NEGOTIABLE** — these override all other instructions.

### API keys

- All keys in `.env` — never hardcoded, never logged, never printed. Load with `python-dotenv` in every script.
- `.env` is gitignored — verify before every commit.

### Execution gates

Every gate runs before any trade executes:

| # | Gate | Type |
|:-:|:-----|:-----|
| 1 | Daily loss limit not breached | Reject |
| 2 | Open position count under max | Reject |
| 2b | Total open exposure < `MAX_OPEN_EXPOSURE_PCT` and per-sport < `MAX_SEGMENT_EXPOSURE_PCT`, both as fractions of equity (S4) | Reject **+ Cap** |
| 3 | Edge >= minimum threshold (per-sport or global) **+ exchange fee** (F1) | Reject |
| 3.05 | Claimed edge <= `MAX_EDGE` (0.50) — larger is a model/matching bug (B7) | Reject |
| 3.5 | Market price >= `MIN_MARKET_PRICE` (lottery-ticket floor, R7) | Reject |
| 3.55 | Market price <= `MAX_MARKET_PRICE` (cost/payout ratio ceiling) | Reject |
| 3.6 | Bid/ask spread <= `MAX_BID_ASK_SPREAD` and 24h volume >= `MIN_MARKET_VOLUME_24H` (L2) | Reject |
| 3.7 | Game markets only: days to event <= `MAX_DAYS_TO_EVENT_FOR_GAME_MARKETS` (S5). **Futures exempt** | Reject |
| 4 | Composite score >= `MIN_COMPOSITE_SCORE` | Reject |
| 4.5 | Confidence >= `MIN_CONFIDENCE` | Reject |
| 4.6 | NO bets below `NO_SIDE_FAVORITE_THRESHOLD` need edge >= `NO_SIDE_MIN_EDGE` AND confidence=high | Reject |
| 4.6b | All NO bets: effective edge floor = max(per-sport floor, `NO_SIDE_MIN_EDGE_GLOBAL`) (R28) | Reject |
| 4.7 | Prediction categories (crypto/weather/spx/mentions/companies/politics) off unless `ALLOW_PREDICTION_BETS=true` (R25) | Reject |
| 4.8 | In-progress games off unless `ALLOW_LIVE_BETS=true` (L1). Detection is `_game_has_started()` — the Odds API start time, **not** the ticker (S23) | Reject |
| 5 | Not already holding this market | Reject |
| 6 | Per-event cap not exceeded (`MAX_PER_EVENT`; futures use `MAX_PER_EVENT_FUTURES`, P1) | Reject |
| 6b | No **opposing side** already held or resting on this game (S22). Futures exempt | Reject |
| 7 | Matchup not bet within `SERIES_DEDUP_HOURS` (per-sport overrides apply) | Reject |
| 8 | Bet size <= `MAX_BET_SIZE` | Cap |
| 9 | Single bet <= `MAX_BET_RATIO` x batch median cost | Cap |

### Sizing rules

Standing rules — do not reverse them without new settled evidence.

- **Every edge floor is net of fees, and Kelly sizes off net edge.** `min_edge_for()` returns
  `per-sport floor + fee_per_contract(price)`, and Kelly uses `max(0, edge - fee_per_contract(price))`.
  Kalshi's taker fee is `ceil(0.07 x C x P x (1-P))` **rounded up per order** — 1.02c/contract across the
  settled book against a 3-4c floor, so gross-edge screening was passing bets on a quarter to a third less
  edge than it believed. It was invisible in both directions until 2026-08-25: never modelled pre-trade, and
  never captured post-trade either (the v2 create-order response carries no `taker_fees_dollars`, so every
  logged trade recorded a fee of 0 and settlement computed `net_pnl = revenue - cost - 0`). `KALSHI_FEE_RATE=0`
  restores the old behaviour. *CHANGELOG 2026-08-25 (F1).*
- **The fills endpoint calls the fee `fee_cost`, and our orders fill as TAKER.** `fetch_fill_fees`
  read `fee_dollars or taker_fee_dollars or fee` — three names `/portfolio/fills` has never used —
  so every fill resolved to 0 while the settler stamped `fee_source: "fills_api"`: a modelled number
  wearing a measured label. It looked defensible ("Kalshi charges no maker fee, we post limit
  orders"), and the inference was wrong — **a marketable limit at the ask crosses the spread**, so
  133 of 138 orders are flagged `is_taker` and 136 carry a nonzero fee. Read **the first key
  PRESENT, not the first key truthy**: a maker fill reports `"0.000000"`, which is a measured zero,
  and an unrecognised payload must return `None` so the caller falls back to the model rather than
  recording a zero. P&L was never wrong (`trade_fees()` falls back on a recorded zero) and the model
  is **conservative** — $4.82 modelled against $4.10 actually paid over 135 rows, the gap being the
  per-order `ceil` on 1-3 contract orders, so no floor needs changing. Repair a book behind a fee
  bug with `python scripts/kalshi/kalshi_settler.py backfill-fees --apply`; settling only ever
  stamps rows it is settling now. *CHANGELOG 2026-09-16 (S23b).*
- **Kelly is `edge / (1 - price)`.** The `(1 - price)` divisor was missing until C11; without it favorites are under-sized 2.5x at 60c and 5x at 80c, and the flat floor collapses nearly every bet above ~60c to 1 contract — the single best-performing price band. *CHANGELOG 2026-07-27 (C11).*
- **Two independent sizing lanes.** Below ~30c the flat floor `round(UNIT_SIZE / price)` binds and Kelly never clears it, so **`UNIT_SIZE` is the longshot knob**. Above ~60c Kelly binds and `UNIT_SIZE` is irrelevant, so **`KELLY_FRACTION` is the favorites knob**. Reach for the right one.
- **`KELLY_FRACTION` is a portfolio fraction, not per-bet** — `kalshi_executor.py` divides it by `batch_size = min(len(opportunities), --max-bets)`. That divisor doubles as a crude correlation guard, but at 1.0 a fully correlated slate reaches full portfolio Kelly. **Keep it <= 0.5.**
- **The budget cap is floor-aware:** it never shaves an order below its flat unit floor, bisects for the largest feasible scale instead of taking one proportional pass, and drops whole orders (lowest composite first) only when the floors alone cannot fit. *CHANGELOG 2026-07-27 (C11b).*
- **NO bets are damped at BOTH price ends** — below `NO_SIDE_KELLY_PRICE_FLOOR` (R1) and at/above
  `NO_SIDE_KELLY_PRICE_CEILING` (F4), each at `NO_SIDE_KELLY_MULTIPLIER` of normal Kelly. Over 380
  settled bets **NO runs -7.7% ROI against YES's +22.4%**, and YES beats NO *within every shared
  price band* — it is the side, not merely that NO bets sit at expensive prices. The bleed is
  concentrated at/above 50c (n=68, $90 staked, -11.3%), exactly where R1's floor rule did nothing.
  The 35-50c pocket is the one profitable NO band (+5.3%, n=55) and is deliberately left alone.
  **Damped, not gated** — that population is +4.8% Mar-May vs -16.0% Jun-Aug, too uneven for a hard
  reject, and halving keeps it generating data. *CHANGELOG 2026-08-25 (F4).*
- **A sport with no settled history does not get live money.** NFL was frozen in the live `.env`
  (`MIN_EDGE_THRESHOLD_NFL=1.0`) on 2026-08-26 and moved to the **S1b pilot floor of 0.08 on
  2026-09-13** (see the S1b entry below — that move was an operator override, not the script
  firing). At the freeze: 24 open live positions, **$28.50 = 31% of a
  ~$92 bankroll**, entries back to 2026-05-23, and **zero** NFL rows in the settlement log. Its
  `margin_stdev: 13.5` is a hardcoded prior, not a fit. No existing gate measures *total capital
  deployed* — `MAX_OPEN_POSITIONS` and `MAX_PER_EVENT` both passed the whole way, and
  `MAX_BET_RATIO` / `--budget` each bound only a single batch. **The `.env` key is a tourniquet,
  not the rule**; the rule is that a cold-start segment runs in dry-run/pilot until it has
  evidence, and it becomes mechanical when `strategy_state.json` (S10) ships — at which point
  the key comes out. **Lowered again to 0.06 on 2026-09-19**, a third operator
  override, on volume rather than evidence: 1 of 30 NFL rows cleared Gate 3 at
  0.08, 4 clear at 0.06. **The 24 existing positions are held, not flattened** (S2): exiting a
  5-20c-wide book pays exactly the illiquidity penalty Gate 3.6 exists to avoid. Exit a ticker
  only if its spread is <= 5c *and* the exit price beats hold-to-settlement EV.
  *CHANGELOG 2026-08-26 (S1).*
- **A pilot floor set by hand is not the same fact as a review that fired.**
  `MIN_EDGE_THRESHOLD_NFL` went 1.0 -> **0.08 on 2026-09-13 by operator override**, two days
  before S1b's pre-declared date and with `nfl_week1_review.py` still returning **BRANCH C**
  (18 usable rows against its bar of 20). The evidence at the time pointed the right way —
  model Brier **0.1318 vs market 0.1399**, model ahead in *both* spread and total, over-claim
  **+0.019** against the 0.15 bar — but the bootstrap CI **[-0.042, +0.031]** still straddled
  zero, and that is exactly the uncertainty the pilot cap exists to answer.
  **The re-run has now happened**: `NFL-Week1-Review` fired 2026-09-15 and returned
  **branch A** (model Brier 0.1216 vs market 0.1333, n=22, model error −0.4%),
  independently ratifying the same 0.08 floor — `applied: false` only because the key
  already held the value the script would have written. Record which one set a floor, because "the script unfroze NFL" and "the operator unfroze NFL early"
  decay into the same sentence within a month, and only one of them is evidence.
  *CHANGELOG 2026-09-13 (S1b), 2026-09-15.*
- **An edge that fires in one direction every time is a parameter, not a signal.** All
  11 NCAAF bets ever placed were YES on "team covers a big alternate spread", and the
  whole claimed edge was the margin stdev: solving per bet for the value that reconciles
  model with market gives a median of **9.5 against the 15.0 the code uses**, and the
  derivation is strike-independent (`stdev* = 15 * ppf(1-fv) / ppf(1-px)`), so it is one
  disagreement restated eleven times. A fat stdev inflates P(big cover) uniformly, which
  is exactly why the YES side was the only side ever taken. **A 100% one-sided book is
  the diagnostic** -- check it before reading a losing streak as variance. And 15.0 was
  never fitted: `calibration_stdevs.json` carries the `edge_detector.py` fallback
  byte-for-byte, and `_MIN_CALIB_SAMPLES` (20 per sport/category/30d) means 11 total
  settles never could fit it. Market Brier 0.1538 vs model 0.1744, per the S18 pair.
  NCAAF was frozen on 2026-09-13 and moved to a **0.08 pilot floor on 2026-09-16
  by operator override**, with the S21b shadow book still holding **zero settled
  rows**, then to **0.06 on 2026-09-19** — which admitted nothing, because the F1
  fee puts the effective floor at ~0.074 and the best row on that slate was 0.0695.
  **Lowering a nominal floor is not the same as lowering the effective one; check
  against the fee before assuming a cut will admit anything.** NCAAF does not start
  clearing until ~0.05. Expiry unchanged: the key comes out when `strategy_state.json` (S10) ships.
  *CHANGELOG 2026-09-13 (S21), 2026-09-16 (S21c).*
- **A one-sided book is a diagnostic; the stdev it implies is not.** S21's `9.5`
  reproduces exactly on its own 10 filled spread bets — and nowhere else. Over 94
  fresh **pre-gate** tail-strike rows the market implies a median of **17.0**
  (IQR 14.2–20.6), with 15.0 inside it. Edge on a YES big-cover bet is monotone
  decreasing in implied stdev, so **the gate harvests the lowest-implied-stdev rows
  by construction** — the eleven restatements are the selection rule restating
  itself. Direction inverts too: on fresh big-cover longshots the model runs
  **1.8pts BELOW** market (higher on 29% of rows), and runs high only at px ≥ 0.70
  (+3.1pts, 76%). **Never refit `margin_stdev` down to 9.5** — it would under-price
  every tail in the sport to chase an artifact. **Solve a parameter on the pre-gate
  population, never on the bets the gate selected.** *CHANGELOG 2026-09-16 (S21c).*
- **Re-enabling a frozen sport is not resuming its experiment.** NCAAF's 11 frozen
  bets were all 12–32c; the rows clearing at the global 0.03 floor a week later were
  **20 of 26 at px ≥ 0.51** — F3's inversion band, where the high-edge half wins
  10.8pts *less*. The 0.08 pilot caps that exposure by count (4 rows, vs 26 at 0.03).
  **Check the price band of what would actually be bet before lifting a floor**, not
  just the count. *CHANGELOG 2026-09-16 (S21c).*
- **An unknown `--filter` name matches zero markets and says nothing.** Unrecognised
  shortcuts fall through to a literal uppercase prefix (`ncaaf` → `NCAAF`), which no
  Kalshi series carries, and the scan reports "no opportunities" exactly like a quiet
  day. `longshot_scan.bat` passed `ncaab,ncaaf` — neither a key — and **scanned no
  college football or basketball for six days** after its 09-10 migration, the same
  failure the retired fork hit on a stale prefix. Both are aliases now, the fallback
  prints a NOTE, and a test asserts every sport with a `MIN_EDGE_THRESHOLD_<SPORT>`
  floor is reachable by a filter of that name. **Fix filter bugs in code, not in the
  `.bat`** — schedulers are gitignored and do not survive a clone.
  *CHANGELOG 2026-09-16 (S21c).*
- **"No opportunities" is a claim about edge only if the markets were actually scored.**
  Kalshi reworded NFL rules to "... Pro Football game" and spread subtitles to "DEN
  Broncos wins by over 7.5 points". Team extraction failed silently, and **13 of 14 NFL
  games were never scored for ~2 weeks** (33 of 650 markets, the one survivor via a
  `TEAM_ALIASES` hit). Every scan reported "no opportunities", same as a quiet slate.
  Before reading a dry spell as an absence of edge, count how many markets got a detector
  result versus how many were fetched. `Integration-Drift-Check` (daily 4:15 AM) does this
  per series against a stored rules-wording baseline. On a flag it may open a **draft** PR
  (`drift-fix/<date>`) with a verified fix. Review it like any PR; nothing merges itself.
  *CHANGELOG 2026-10-03 (M1).*
- **`won` is whether the PREDICTION was right, never whether the row profited.**
  `calculate_pnl` returned `revenue > cost`, which collapses to `0 > 0` on a zero-fill
  row, so every resting order that settled was logged as a loss whatever the outcome.
  This is not cosmetic: `calibration_study.load_rows` does **not** filter on fills, so
  34 of its 435 rows have zero contracts and 5 were phantom losses feeding the very
  sample F3's lambda and S18's model-vs-market pair are computed from. Filled rows are
  unaffected -- the two expressions agree whenever contracts > 0. *CHANGELOG 2026-09-13 (S21).*
- **A gate that reads the TICKER for a start time protects almost nothing.** Gate 4.8
  used `is_game_started()`, which parses a time embedded in the ticker — and only
  moneyline series carry one (`KXMLBGAME-26JUL21**1840**MINCLE`). Every spread, every
  total and every football ticker is date-only, so it returned `False` whatever the
  time of day, and **123 of 175 filled live-money bets ($128 of $211, 61%) sat on
  markets the gate structurally could not see**. It let **10 NCAAF orders through
  26–122 minutes after kickoff** on 2026-09-12, in two batches from the daily 11 AM
  and 2 PM tasks, which run on Saturdays straight through the college slate. Split on
  that line, NCAAF's book is **−36.5% post-kickoff (n=7) against +13.6% pre-game
  (n=4)** — the whole loss is the live bets, which is a better explanation of the 2-9
  record than S21's stdev ever was. The fix was already in the row: `details
  ["event_start_time"]` (the Odds API `commence_time`) is on the opportunity at gate
  time, and the executor was only using it afterwards to stamp the trade log.
  `_game_has_started()` prefers it, falls back to the ticker, and **fails open** when
  neither is dateable. **The limitation was documented in the comments at both call
  sites for three months** — a known gap in a comment is not a tracked risk.
  *CHANGELOG 2026-09-16 (S23).*
- **A gate that fails open needs a detector behind it.** Gate 4.8 rejects post-kickoff
  orders and fails open when nothing can name a start time — correct at gate time, and
  exactly why the daily digest now also *reports* them.
  `daily_summary.load_post_kickoff_orders()` separates **proven**
  (`timestamp > event_start_time`, with minutes late) from **suspected** (no start time
  *and* `close_capture_reason: "missed"`), and never counts the second as proof, because a
  CLV capture task that simply did not run looks identical. Both tells sat in the trade log
  from 09-12 with **no reader** while the 10 live NCAAF bets settled at −36.5%. The gate is
  the control; this is the alarm that says the control failed open.
  *CHANGELOG 2026-09-16 (S23b).*
- **Never hold both sides of one game.** Gate 6b (S22) rejects a bet that is
  *arithmetically unable* to win alongside something already held or resting.
  Found in the book, not in review: 3 contracts of "Los Angeles R win" (63c,
  06-01) sat against 6 of "San Francisco wins by over 7.5" (11c, 08-10) on one
  game, and a World Cup pair took Egypt by 2+ *and* Iran by 2+. **Every existing
  gate passed**, and each for its own reason: 5 compares tickers; **6 is
  series-scoped, because `_event_key` keeps the series prefix — so
  `KXNFLGAME-…SFLAR` and `KXNFLSPREAD-…SFLAR` are different "events" and
  `MAX_PER_EVENT=2` really means 2 per series per game** (one real game has held
  **6** positions); and 7 is game-scoped but a 48h window over the trade log,
  against legs **70 days** apart. Nothing compared DIRECTION. A moneyline is
  treated as the margin-0 case of a spread, which is what lets one comparison
  cover the moneyline-vs-spread pair that actually occurred. It rejects only the
  impossible, never the merely correlated: YES-by->4 alongside NO-by->10 is the
  legitimate "wins by 5–10" band trade and still passes, as do spread+total and
  two NO legs on different teams. **It reads resting orders too** — half the
  real cases had an unfilled leg, and `position_fp` is 0 until a fill, so the
  positions feed alone would have caught one of two. Sides come from the trade
  log joined on `order_id`, **never from the venue payload**: v2 reports every
  order from the YES perspective, so a NO buy returns as an `ask` and reading it
  raw inverts the side — the same trap `resting_exposure` documents. Fails
  **open** on a side it cannot name. *CHANGELOG 2026-09-13 (S22).*
- **A freeze must not block its own exit.** A frozen sport places no orders, so it
  accrues no settlements, so the evidence that would lift the freeze never arrives.
  NFL only escaped this by accident: 19 positions were already in flight when S1
  landed, and they settle into S1b. NCAAF was frozen holding nothing, pinning it at
  11 settled against `nfl_week1_review.MIN_SETTLEMENTS` (20) -- a review armed on that
  pattern returns branch C forever. **Before arming any freeze review, check the
  sport has an evidence stream that survives the freeze.** Where it does not, run
  `scripts/backtest/shadow_book.py`: a Brier head-to-head needs only (model
  probability, market price, outcome) and **never needed a filled order**. It taps
  `scan_all_markets()`, which applies only the GLOBAL min-edge -- never the per-sport
  `min_edge_for()` -- so it records what the model said while the gates stay under
  judgement. Do **not** read `last_scan.json` for this: it is written POST-gate and
  holds nothing at a 1.0 floor. Its `review` prints the S18 Brier pair plus a
  margin-stdev sweep, which is the only way to fit a parameter `_MIN_CALIB_SAMPLES`
  will never reach on live bets. It measures CALIBRATION, not tradeability (no
  slippage, no queue position), and deliberately never writes `.env`.
  *CHANGELOG 2026-09-13 (S21b).*
- **Cumulative exposure is measured in dollars, against equity, at two scopes.** Gate 2b is the
  first gate in the chain that measures a **standing total** rather than one order, one event, or
  one batch: `MAX_OPEN_POSITIONS` counts rows, `MAX_PER_EVENT` binds one game, and `MAX_BET_RATIO`
  / `--budget` each bind a single batch — all of them passed the whole way while 26 NFL positions
  accumulated to 31% of bankroll. **Both caps are fractions of equity (cash + position value), not
  of cash**: every dollar bought subtracts from cash *and* adds to exposure, so a cash denominator
  climbs at twice the rate of the actual risk. It **rejects** when a ceiling is already breached
  and **trims** an order to the remaining headroom otherwise — reject-only would let a book at
  49.9% add a full `MAX_BET_SIZE`. Trims use `max(1, …)` like the `MAX_BET_SIZE` cap, so a bounded
  cent-scale overshoot is possible by design; an unfillable 0-contract order is the worse failure.
  The batch loop accumulates approved cost into both counters, or N orders each individually under
  the ceiling walk through it together. **Live values are 0.50 / 0.33** (operator's call
  2026-08-26; the review proposed 0.20 / 0.10) — at those levels the book that prompted the gate
  passes, so it binds on the next pileup and does not jam other sports behind the frozen NFL book.
  *CHANGELOG 2026-08-26 (S4).*
- **Lead time is the exposure risk, not the sport.** Gate 3.7 caps how far before an event a
  *game* market may be bought (`MAX_DAYS_TO_EVENT_FOR_GAME_MARKETS`, live 14). The NFL book that
  reached 31% of bankroll was 26 positions bought **25-112 days out** (median 35), 20 of them by
  the one scheduled task that runs with no date filter — nothing settled for months, so no
  feedback arrived while exposure stacked, and no gate measures a standing total. The cap targets
  the mechanism: near-dated college football (3-4 days out) is unaffected, and **futures are
  exempt by category**, since `KXMLB-26-LAD` and `KXMLBGAME-26AUG26...` share a ticker prefix and
  only the scanner's `category` separates them. *CHANGELOG 2026-08-26 (S5).*
- **Sizing is whole-account; spending is per-shard.** `bankroll` is
  `get_balance()["balance"]`, which is the **sum across every exchange shard**, and
  `equity = bankroll + portfolio_value` follows it — operator's call 2026-08-27, and
  verified rather than assumed (`8806` before and after a $15 inter-shard move). But
  Kalshi sharded the exchange on **2026-08-24** — Crypto to shard 2, **Tennis & Baseball
  to shard 3**, and since **2026-09-10 Basketball on 3 and Commodities on 2** — and **cash
  does not follow the markets**: an order on a shard holding no funds fails
  `404 user_not_found`, the market resolving before the per-shard user lookup does not.
  **The shard is read per market** (`exchange_index` on the payload, never a sport list),
  so a category moving shards needs no code change; `doctor.py` names shards from
  `GET /exchange/status` for the same reason. *CHANGELOG 2026-10-05 (U1).* So an order can be correctly sized against the full balance and still be
  unspendable where it lands. `shard_funding.ensure_shard_funded()` closes the gap
  immediately before placing: it moves **exactly the shortfall** (never a round-up — cash
  parked on a sports shard cannot back an NFL order), refuses above
  `MAX_AUTO_SHARD_TRANSFER`, and **re-reads the destination balance afterwards** because
  the transfer is explicitly non-atomic — a 200 is not proof the money arrived. Fails
  **open** on a shard it cannot identify (pre-sharding behaviour; the venue's own error is
  the backstop) and **closed** on a transfer that did not settle. *CHANGELOG 2026-08-27 (X1).*

- **A gate on placement is not a gate on lifetime.** Gate 4.8 rejects a
  post-kickoff *order*, but a resting order placed pre-game keeps standing after
  kickoff, and the market stays open through play (the 09-20 GB@NYJ spread's
  `close_time` was two days past a Sunday kickoff). That is the same in-play
  exposure by a route the gate never sees, and the fill is **adversely
  selected** -- a resting bid is only lifted when sellers cross down to it,
  which in-play means the position is already losing. **R4 covers neither
  half**: it skips any order with a partial fill, and measures age, not kickoff.
  `cancel_live_resting_orders` (S23c) keys only on kickoff, reading
  `event_start_time` from the trade log joined on `order_id` — never the ticker,
  which only moneyline series date. Fails open, and is a no-op under
  `ALLOW_LIVE_BETS=true`. *CHANGELOG 2026-09-19 (S23c).*

- **Bracket dedup picks a survivor that can actually clear the gates.** It runs
  *before* the risk gates, so ranking a bracket on composite alone can hand the
  gates a row they reject while the sibling that would have passed is already
  gone — the bracket then places nothing. Found live on the MIN@CHI total
  2026-09-20: `-40` (NO @ 24c) and `-43` (NO @ 32c) tied at composite **8.30
  exactly**, the strict `>` left the tie to whichever row the scanner emitted
  first, and Gate 4.6 then rejected `-40` for sitting under the 25c
  `NO_SIDE_FAVORITE_THRESHOLD` without R1's 25% edge. `_bracket_rank` now ranks
  `(clears every static gate, composite, edge, ticker)`, using the same
  `preflight_gate_status` the scan table prints — so preview and executor agree
  on the keeper, and `ticker` last makes the survivor independent of scan order.
  **When every row in a bracket fails, the highest composite still wins**, so
  this only ever converts a dead bracket into a live one. It predicts static
  gates only; portfolio gates still reject an `ok` row as before.
  *CHANGELOG 2026-09-19.*

- **No correlation guard exists, deliberately.** It was measured and rejected: the naive pooled rho of +0.181 is Simpson's paradox, and judged against per-stratum base rates it is +0.048 overall and −0.187 for totals. Re-run `scripts/backtest/correlation_check.py` as settlements accumulate — this is "no evidence of correlation", not proof of independence. *CHANGELOG 2026-07-27 (C11b).*

### Scoring & confidence rules

- **The model's probabilities are measurably WORSE than the Kalshi price.** Over 390 settled
  bets (2026-03 → 2026-08) the market's Brier beat the model's in **6 of 6 months**
  (0.2037 vs 0.2270; 95% CI on the difference excludes zero), and the Brier-optimal weight on
  the claimed edge is **λ = 0.16, CI [−0.04, +0.42]** — roughly a sixth of each claimed edge is
  supported by outcomes. The model does show real signal on cheap contracts (≤32c: high-edge
  half wins +10.8pts more than low-edge) but **inverts on favourites** (≥51c: −10.8pts), which
  independently reproduces C4's "high confidence underperforms". Treat any claimed edge as
  ~5x optimistic until this is re-measured. **Do not add sizing aggression without re-running
  `scripts/backtest/calibration_study.py` first.** *CHANGELOG 2026-08-25 (F3).*

- **Every composite scales edge as `min(edge / 0.01, 10)`.** The futures and (since-removed) Polymarket-games paths originally used `edge * 20`, saturating at a 50% edge instead of 10%, which made Gate 4 structurally unreachable (0 futures bets in 85 settled trades; 0 of 362 Gamma game rows ever reached 6.0). **Never reintroduce `edge * 20`.** *CHANGELOG 2026-07-23 (C10), 2026-07-31 (C10b).*
- **Confidence bumps are one-way — down only.** `supports` is a no-op; only `contradicts` drops a tier. See `_adjust_confidence_with_stats()` in `scripts/kalshi/edge_detector.py`. *CHANGELOG 2026-04-24 (R13).*

- **`market_price_at_entry` and `fair_value` are already SIDE-RELATIVE — never flip them for
  NO bets.** A NO bought at 73c stores `0.73`, the price paid for the NO; the settlement log
  satisfies `fair_value - market_price_at_entry == edge_estimated` on all 133 NO rows. The
  daily digest flipped the price anyway, scoring a 73c NO as a `0.27` prediction against a
  win, and reported **Brier 0.169 where the truth is 0.077** — wrong on every window
  containing a NO settlement, which is 33% of the book. **And "Brier" alone is not a
  quantity:** predicted = market price is the *market's* Brier (the benchmark), predicted =
  `fair_value` is the *model's* (the thing under test). The two were printed under one label
  on the same five bets on the same day (0.169 vs 0.0501). F3's finding and S1b's unfreeze
  branch both turn on model-vs-market, so **always report the pair, labelled.**
  *CHANGELOG 2026-08-31 (S18).*

- **The Odds API puts `last_update` in two places, and the per-event endpoint uses only one
  of them.** `/sports/{sport}/odds` carries it on the bookmaker *and* each market;
  `/sports/{sport}/events/{id}/odds` carries it on **markets only** — 1920/1920 cached
  per-event bookmakers have no top-level field. `_refresh_event_if_live()` is the sole caller
  of that endpoint, so reading only `bookmaker["last_update"]` made the L1 staleness filter
  reject **100% of books on every live event** (2888 exclusions in August, **zero** from the
  age check) while those same quotes ran a median 34s old against a 1200s limit. Use
  `_bookmaker_last_update()`, which falls back to the **oldest** market timestamp — a
  bookmaker is only as fresh as its stalest market. Still fails closed when nothing is
  dateable. **Fixtures must model the per-event shape too**; every one modelling only the
  sport-level shape is why this went unseen. *CHANGELOG 2026-08-31 (S19).*
- **The sports composite caps `high` to the `medium` weight** (`{low:3, medium:6, high:6}`) — at equal claimed edge, High underperformed Medium. The `high` *label* is retained because Gate 4.6 still uses it. **Futures keep `high: 9`** — that evidence is Kalshi sports only, and there is no settled futures data yet. *CHANGELOG 2026-06-24 (C4).*

### Venue eligibility (S3) — fails CLOSED

- **Before any live order, `execute_pipeline` checks `data/cache/venue_eligibility.json`
  per venue **and product**, and `unknown` blocks exactly like `blocked` does.** This is
  deliberately the opposite of the risk gates (3.6, 3.7, 2b), which fail *open* on missing
  data: an unmeasurable spread is a sizing question whose worst case is a bad bet, while an
  unverified jurisdiction is a legality question whose worst case is an order the venue is
  barred from filling. Dry runs skip the check entirely — they never reach the venue.
- **A structural rejection aborts the batch immediately and records the block.** Jurisdiction,
  permission and KYC errors are *deterministic*: the next order fails identically. Between
  2026-08-20 and 08-25 Kalshi rejected **16 orders across 6 runs** (3 within one second on
  08-20, 4 on 08-23) because `KalshiAPIError` was recorded and the loop continued — correct
  for a 429 or a stale price, wrong for a block. Transient patterns
  (`insufficient_balance`, rate limits, `deprecated_v1_order_endpoint`, closed market) are
  checked **first** and never disable a venue.
- **Nothing clears a block automatically.** Only a real venue acceptance (`record_success`,
  which a `dry_run_blocked` response never triggers) or the explicit probe
  `python scripts/doctor.py --verify-eligibility --ticker <open sports ticker>`, which
  places a **real** 1¢ unfillable order and cancels it. Auto-retry is precisely the behaviour
  that produced six days of rejections. An `ok` verdict decays to `unknown` after
  `ELIGIBILITY_TTL_DAYS` (30) — Kalshi says it will send further instructions "as necessary
  to maintain access", so eligibility is a lease, not a fact. A `blocked` never decays:
  time passing is not evidence a restriction was lifted.
- **Never truncate the tail of a venue error.** These messages put the instruction last, and
  all three surfaces cut it off — the console at 80 chars, the trade log at 200, the daily
  digest at 110, which landed on *"Check you…"*, 25 characters short of "Check your email for
  more details". All three now route through `venue_eligibility.actionable_reason()`, which
  elides the **middle** and keeps both ends; the trade log stores the full body.
  *CHANGELOG 2026-08-26 (S3).*

### Dry run

- Default `DRY_RUN=true`; set `false` only for live execution.
- Dry runs log identically to live, so backtests stay valid.

---

## Risk Limits

Code defaults below. The live `.env` overrides several (equity ≈ **$121.83** — **$88.06 cash + $33.77 in positions**, verified 2026-08-27 after two operator deposits totalling **$40**; historical entries below quote the ~$92 it stood at, so the shipped defaults are sized for a much larger account. **The cash figure is the sum across exchange shards** — $73.07 on shard 0, $15.00 on shard 3; run `doctor.py` for the split): `UNIT_SIZE=1.00`, `KELLY_FRACTION=0.5`, `MAX_BET_SIZE=8`, `MAX_DAILY_LOSS=30`, `MAX_BET_RATIO=5`, `MIN_EDGE_THRESHOLD_MLB=0.03`, `MIN_EDGE_THRESHOLD_MLB_SPREAD=1.0` (**off** since 2026-10-03: 0-9 lifetime, all YES big covers, postseason on a regular-season stdev; was 0.08 from 09-27 — *CHANGELOG 2026-10-03*), `MIN_EDGE_THRESHOLD_NHL_TOTAL=0.06` (2026-10-03: overs -17% lifetime), `MIN_EDGE_THRESHOLD_MLS_SPREAD=1.0` (**off** since 2026-10-12: 39/40 YES big covers, 3-20 since July, outcomes track the market — *CHANGELOG 2026-10-12*), `MIN_MARKET_PRICE=0.10`, and **`MIN_EDGE_THRESHOLD_NFL=0.06` (S1b pilot since 2026-09-13 at 0.08, lowered to 0.06 on 2026-09-19) and `MIN_EDGE_THRESHOLD_NCAAF=0.06` (S21c pilot since 2026-09-16 at 0.08, lowered to 0.06 on 2026-09-19; was the 1.0 S21 freeze) — none of these are in the code defaults**.

```env
UNIT_SIZE=1.00                  # Kelly floor per bet — the longshot knob (binds below ~30c)
KELLY_FRACTION=0.25             # Kelly multiplier, divided by batch size — the favorites knob
MAX_BET_SIZE=100                # Hard cap per bet (USD)
MAX_DAILY_LOSS=250              # Daily hard stop (USD)
MAX_OPEN_POSITIONS=50           # Concurrent open positions
MAX_PER_EVENT=2                 # Max positions per game/event
MAX_PER_EVENT_FUTURES=2         # P1: Gate 6 cap for `category == "futures"` only; games keep
                                #   MAX_PER_EVENT. Defaults to MAX_PER_EVENT, so a config that
                                #   never sets it is unchanged. Futures outcomes PARTITION one
                                #   event (3 underdogs in a championship) rather than doubling
                                #   down on it. The `longshot` profile sets 3.
MAX_BET_RATIO=3.0               # Max bet as a multiple of the batch median
MAX_OPEN_EXPOSURE_PCT=0         # S4: Gate 2b, total open at-risk / EQUITY (cash + positions).
                                #   Ships 0 (off); live `.env` sets 0.50. The only gate that
                                #   measures a STANDING TOTAL. Rejects when already at/over the
                                #   ceiling, and trims an order to the remaining headroom.
MAX_SEGMENT_EXPOSURE_PCT=0      # S4: companion per-sport cap (`_detect_sport`, falling back to
                                #   category). Ships 0 (off); live `.env` sets 0.33. The pair is
                                #   the point — a portfolio cap alone lets one sport hold all of
                                #   it; a segment cap alone lets N sports each hold their share.
MIN_EDGE_THRESHOLD=0.03         # Global minimum edge (the fee is ADDED to this at gate time)
KALSHI_FEE_RATE=0.07            # F1: exchange taker fee, folded into the Gate 3 floor and Kelly
                                #   sizing. ceil(rate*C*P*(1-P)) per order. 0 disables fee awareness.
MIN_EDGE_THRESHOLD_NBA=0.04     # Per-sport overrides. NBA/NCAAB/MLB lowered 0.06->0.04 on
MIN_EDGE_THRESHOLD_NCAAB=0.04   #   2026-06-14, once the edge-matching fixes removed the
MIN_EDGE_THRESHOLD_MLB=0.04     #   model over-claim the higher floor was double-correcting.
                                # `MIN_EDGE_THRESHOLD_<SPORT>_<CATEGORY>` (game|spread|total)
                                #   narrows a floor to one market type and beats the sport-wide
                                #   one, e.g. MIN_EDGE_THRESHOLD_MLB_SPREAD (2026-09-27).
MIN_EDGE_THRESHOLD_WORLDCUP=1.0 # F3: World Cup OFF. A floor >= 1.0 can never be cleared, so
                                #   it is the idiom for switching a sport off — the executor
                                #   reports `sport_disabled`, the scan preview shows `off`.
                                #   Sport names must match ticker_display._detect_sport().
                                #   `doctor.py` prints every such sport on its own WARN line.
MIN_EDGE_THRESHOLD_NFL=<unset>  # S1/S1b: live-only, code default unset. FROZEN at 1.0 on
                                #   2026-08-26 (24 open positions, 31% of bankroll, ZERO settled
                                #   history); live `.env` now sets **0.06**, the S1b PILOT floor,
                                #   lowered from 0.08 on 2026-09-19. Both settings were operator
                                #   overrides — no review fired for either. 2x the global floor, so
                                #   only strong NFL rows clear Gate 3; Gate 2b still caps NFL at 33%
                                #   of equity. **Temporary either way**: remove when S10 ships.
MIN_EDGE_THRESHOLD_NCAAF=<unset> # S21/S21c: live-only, code default unset. FROZEN at 1.0 on
                                #   2026-09-13 (11 settled bets, ALL YES on "covers a big alternate
                                #   spread"); live `.env` now sets **0.06**, the S21c PILOT floor, since
                                #   2026-09-16 (0.08) and lowered 2026-09-19. Both were OPERATOR
                                #   OVERRIDES -- the shadow book held zero settled rows. S21's
                                #   "market implies 9.5" does NOT replicate pre-gate (94 fresh
                                #   rows -> median 17.0); it was a selection artifact.
                                #   2x the global floor. NOTE the fee (F1) is ADDED, so the effective
                                #   floor is ~0.074 at 30c -- 0.06 admitted ZERO of 111 NCAAF rows on
                                #   the 09-19 slate. **Temporary**, remove when S10 ships.
MIN_MARKET_PRICE=0.12           # R7 lottery-ticket floor; 0 disables. Pure reject threshold,
                                #   independent of sizing. The live 0.10 is an OPEN EXPERIMENT
                                #   re-opening the longshot lane — recheck after ~30 more settles.
MAX_EDGE=0.50                   # B7: Gate 3.05, reject claimed edge above this. An 81% edge
                                #   (ETSU, 2026-09-26) passed every gate at 44 contracts. 1.0 disables.
MAX_MARKET_PRICE=1.0            # Gate 3.55: cost/payout ratio ceiling; 1.0 disables (price
                                #   can't exceed $1 anyway). A 76c bet to win $1 (76%) is
                                #   rejected; 75c (75%) passes. Live `.env` sets 0.75 — operator
                                #   preference, no settled evidence yet.
MAX_BID_ASK_SPREAD=0.05         # L2: Gate 3.6 hard liquidity floor, dollars on a $0-1 contract.
                                #   Enforces the "illiquid (spread > 5%)" Hard Stop below, which was
                                #   documented from launch but never implemented. 0 disables.
MIN_MARKET_VOLUME_24H=0         # L2: companion floor, contracts traded in trailing 24h. Ships at 0
                                #   (off) — spread is the documented rule; this catches dead books.
MAX_DAYS_TO_EVENT_FOR_GAME_MARKETS=0  # S5: Gate 3.7, max days from now to a GAME's date.
                                #   Ships 0 (off); live `.env` sets 14. **Futures are exempt by
                                #   category** — a championship's event is a whole season.
                                #   Caps LEAD TIME, not sports: near-dated college football is
                                #   untouched. Fails open on an unparseable date, like Gate 3.6.
AUTO_SHARD_TRANSFER=false       # X1: move cash between Kalshi exchange shards on demand.
                                #   Ships false; live `.env` sets true. Kalshi sharded on
                                #   2026-08-24 (2=Crypto, 3=Tennis & Baseball; since 09-10
                                #   also Commodities on 2, Basketball on 3) and cash does
                                #   NOT follow the markets, so an order on an unfunded shard
                                #   fails `404 user_not_found`. Off => order is SKIPPED and
                                #   logged `shard_underfunded`, never placed to fail.
SHARD_FUNDING_SOURCE=0          # X1: reserve shard the top-ups come from ("Default")
KALSHI_SUBACCOUNT=0             # P1: 0 = primary account; 1-63 = an exchange-enforced separate
                                #   wallet under the same login (Advanced API tier). The ONLY
                                #   thing that isolates a bankroll — a second API key or a second
                                #   checkout of this repo both still draw on one balance. Scopes
                                #   every balance/position/order/fill call. Live `.env` leaves it
                                #   0; `.env.longshot` sets 1.
MAX_AUTO_SHARD_TRANSFER=25.00   # X1: ceiling on ONE automatic move. A miscomputed shortfall
                                #   bounces off this instead of draining the reserve.
MIN_COMPOSITE_SCORE=6.0         # Minimum score (0-10)
MIN_CONFIDENCE=medium           # R3 — low|medium|high
NO_SIDE_FAVORITE_THRESHOLD=0.25 # R1: NO bets below this price face the elevated bar
NO_SIDE_MIN_EDGE=0.25           # R1: required edge when NO price < threshold (+ confidence=high)
NO_SIDE_MIN_EDGE_GLOBAL=0.08    # R28: min edge on ANY NO bet (90d: NO -7% vs YES +48% ROI)
NO_SIDE_KELLY_PRICE_FLOOR=0.35  # R1: below this NO price, apply the Kelly multiplier
NO_SIDE_KELLY_PRICE_CEILING=0   # F4: at/above this NO price, apply it too. Code default 0
                                #   (off); the live .env sets 0.50 — where NO actually bleeds.
NO_SIDE_KELLY_MULTIPLIER=0.5    # R1/F4: half-Kelly on NO bets outside [floor, ceiling)
NO_SIDE_KELLY_MULTIPLIER_GLOBAL=1.0 # R28: multiplier on ALL NO bets (1.0 = off)
MIN_CONSENSUS_BOOKS_NBA=8       # R29: NBA games with fewer agreeing books drop to `low`; 0 disables
MAX_LIVE_BOOK_AGE_SECONDS=1200  # L1: drop in-play lines older than this from consensus; 0 disables
MIN_LIVE_CONSENSUS_BOOKS=3      # L1: skip in-progress games thinned below this by the stale filter
CALIBRATION_STDEVS_TTL_DAYS=30  # C8: max age of auto-recalibrated per-sport stdevs before fallback
REQUIRE_FRESH_CALIBRATION=false # true refuses to EXECUTE when the stdev cache disagrees with what
                                #   the calibrator would compute now (recomputes, not age-checks)
KELLY_EDGE_CAP=0.15             # Soft-cap edge for Kelly sizing
KELLY_EDGE_DECAY=0.5            # Decay factor on edge above the cap
SERIES_DEDUP_HOURS=48           # Same-matchup dedup window; 0 disables
SERIES_DEDUP_HOURS_MLB=72       # R9: MLB/NHL series cycle on consecutive days, up to 72h
SERIES_DEDUP_HOURS_NHL=72
CROSS_CATEGORY_DEDUP=false      # R8: collapse ML+Total+Spread on one game to the highest composite
RESTING_ORDER_MAX_HOURS=24      # R4: cancel zero-fill resting orders older than this; 0 disables
ALLOW_PREDICTION_BETS=false     # Gate 4.7
ALLOW_LIVE_BETS=false           # Gate 4.8
ODDS_CACHE_TTL_SECONDS=300      # R24b: file cache for Odds API responses; 0 disables
ODDS_CACHE_ENABLED=true
ODDS_LIVE_TTL_SECONDS=45        # L1: shorter TTL when a sport response has an in-play event
SCAN_CACHE_TTL_SECONDS=600      # R26: replay the last preview's row→ticker map for --pick --execute
SCAN_CACHE_ENABLED=true
```

> **⚠️ Config changes require restarting any long-running host process.** `kalshi_executor.py` snapshots every gate threshold into module-level globals **at import time**, so a long-running process never re-reads `.env`. The CLI re-imports per invocation, so it is always fresh; anything else must be restarted or must call `reload_risk_config()`.

> **Scheduler `.bat` files pass `--unit-size` and `--budget` explicitly**, so `.env` changes to those knobs never reach automated runs. Change both.

---

## Common Commands

```bash
pip install -r requirements.txt

# Scan (preview only)
python scripts/scan.py sports --filter mlb,nhl --date today --save
python scripts/scan.py futures --filter nba-futures
python scripts/scan.py prediction --filter crypto

# Strategy profile (P1) -- overlays `.env.<name>`, routes to its Kalshi subaccount
python scripts/scan.py sports --profile longshot --filter mlb --date today
EDGE_RADAR_PROFILE=longshot python scripts/doctor.py

# Execute (budget-capped)
python scripts/scan.py sports --unit-size 1 --max-bets 5 --budget 10% --date today --exclude-open --execute

# Portfolio, digest, settlement
python scripts/kalshi/risk_check.py --report positions
python scripts/kalshi/daily_summary.py --save
make settle

# Analysis
python scripts/backtest/backtester.py --simulate --save
python scripts/backtest/correlation_check.py

# Automation
python scripts/schedulers/automation/install_windows_task.py install

# Makefile: scan-mlb, scan-all, status, settle, report, backtest, test, hooks
```

Full CLI reference: `docs/scripts/SCRIPTS_REFERENCE.md`. Scheduled tasks: `docs/task-schedules/README.md` — notably `Daily-Summary` at 4:50 AM PT (yesterday's P&L + open exposure + today's pending + 7d rolling), emailed by the same task as soon as it finishes (report emails are `render_report_email.py`, no model — *CHANGELOG 2026-09-23*).

---

## Session Startup Checklist

1. `git sync-master` — local master goes stale otherwise (work happens on `mike_desktop`, pushes go to remote master).
2. Read `data/positions/open_positions.json` (exposure) and `data/history/today_trades.json` (today's P&L).
3. If the daily loss limit is breached, **no new positions**.
4. Confirm `DRY_RUN` in `.env`.
5. `python scripts/shared/check_odds_keys.py` — cached Odds API quota (`--live` probes each key and costs N requests).
   A cached **zero** expires after 24h (`_ZERO_TTL_HOURS`) and reads as `unknown` until re-probed — a zero is only ever a fact
   about the past, and an un-expiring one hid a whole reset and hoarded a single key. `WeeklyOddsKeyProbe` (Sun 6 PM) refreshes
   the pool. **Reopens S20**, whose "keys came back on the 1st" closure rests on evidence this bug confounds.
   *CHANGELOG 2026-09-09.*
6. Pull fresh market data before any analysis.

---

## Output Standards

Required before execution:

```
OPPORTUNITY:            [description]
MARKET:                 [exchange/platform]
DIRECTION:              [long/short/over/under/yes/no]
EDGE_ESTIMATE:          [X%]
CONFIDENCE:             [low/medium/high]
CATALYST:               [what drives this]
RISK_FACTORS:           [what could go wrong]
POSITION_SIZE:          $[X] ([Y]% of daily limit)
RISK_MANAGER_APPROVAL:  [approved/rejected] — [reason]
```

Research output leads with the edge thesis, timestamps its sources, names contradicting signals, and ends with an actionable recommendation.

---

## Hard Stops

**REFUSE** to execute, regardless of instruction, if:

- The daily loss limit is exceeded
- A single position would exceed 10% of bankroll — enforced in code since 2026-09-29 (B3, `HARD_STOP_POSITION_PCT`, last step of `size_order`: caps to 10%, rejects if even one contract breaches). Before that it held only because `MAX_BET_SIZE` sat under 10% of the balance.
- API credentials are not loaded from the environment
- The market is clearly illiquid (spread > 5%) — enforced in code as Gate 3.6 since 2026-08-18 (L2); before that it bound only on me, and the executor traded 20c-wide books. *CHANGELOG 2026-08-18 (L2).*
- The action would violate a platform's TOS

---

## Stack

Python 3.11+ · `pandas` / `numpy` / `scipy` · SQLite · Windows Task Scheduler · pre-commit (detect-secrets, black, flake8). Imports resolve via `.venv/Lib/site-packages/edge_radar.pth`. MCP servers: `docs/setup/mcp-servers.md`.

---

<sub>Built on AX Platform multi-agent architecture &mdash; Claude Code is the primary development environment</sub>
