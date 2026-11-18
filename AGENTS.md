# Edge-Radar

> Multi-agent edge-detection and execution system for prediction markets and sports betting on **Kalshi**. (Polymarket US was removed 2026-09-29.)
> Research-first, execute-second. No action without documented rationale, risk check, and position-size calculation.

---

## How to Use This File

- This file (`AGENTS.md`) is read by every coding agent. `CLAUDE.md` imports it and adds the Claude Code-only notes (skill junctions).
- **This file holds the rules, one or two lines each.** The evidence behind each one (incidents, settled-bet numbers, reasoning) is in **[docs/RULES-RATIONALE.md](docs/RULES-RATIONALE.md)**, and the dated entry it cites (*S4*, *2026-08-26*) is in `docs/CHANGELOG.md`, or in `docs/changelog/<YYYY-MM>.md` for entries before 2026-10. When a rule changes, update all three. Do not reverse a rule without new settled evidence.
- Working branch: **`mike_desktop`** (deploy/default: `master`).
- The Risk Limits block lists **code defaults**; the live `.env` overrides several. `python scripts/doctor.py` is the source of truth for what is actually running.
- **The homepage's data-flow diagram is generated and pinned to code.** `docs/diagrams/betting-data-flow.json` cites line ranges in `edge_detector.py`, `kalshi_executor.py`, `kalshi_settler.py`, `odds_cache.py` and friends. When a betting-path change makes `python scripts/diagrams/build_betting_diagram.py --check` report drift, fix the JSON in the same PR, then `--pin-head` (`docs/diagrams/README.md`). Never hand-edit the `.html`/`.png`.

---

## What's Live

| Domain | Coverage | Data Sources |
|:-------|:---------|:-------------|
| **Sports betting** | NBA, NHL, MLB, NFL, NCAA, MLS, soccer, UFC, boxing, F1, NASCAR, PGA, IPL, Wimbledon tennis, esports (31 game filters, 8 futures). **World Cup (F3) is OFF; NFL and NCAAF run 0.06 pilot floors (S1b/S21c)** | The Odds API, ESPN, NHL/MLB Stats, NWS |
| **Prediction markets** | Crypto (BTC, ETH, XRP, DOGE, SOL), weather (13 cities), S&P 500 | CoinGecko, Yahoo Finance, NWS |
| **Championship futures** | NFL, NBA, NHL, MLB, PGA | Sportsbook futures odds |
| **Execution pipeline** | Unified scan → risk-check → size → execute | Kalshi API (RSA-signed) |

**Planned, not built:** Manifold, Alpaca stocks/options, Coinbase/Binance, DFS + sportsbook APIs, Fed/CPI/GDP markets.

---

## Strategy Profiles (P1)

Two strategies, **one codebase**, two Kalshi wallets. A profile is a named overlay file, `.env.<name>`, applied on
top of the base `.env`: `--profile <name>` on `scan.py`, `EDGE_RADAR_PROFILE=<name>` for other entry points.
**The `longshot` profile was retired 2026-09-27**; the mechanism stays.

- **`KALSHI_SUBACCOUNT` is the only thing that isolates money.** A second API key or a second checkout still draws on one balance.
- **Only what the overlay names differs;** gates, fees, calibration and floors are inherited in lockstep.
- **It fails CLOSED:** a missing `.env.<name>` raises rather than falling back to the live base `.env`.
- **Every trade row carries `"profile"`;** pre-P1 rows lack it, so readers default to `"main"`.
- **Do not fork this repo to try a strategy;** add a profile. *P1, 2026-09-10.*

How the books stay separate end to end: [docs/longshot/README.md](docs/longshot/README.md). Why: [rationale](docs/RULES-RATIONALE.md#strategy-profiles).

---

## Project Structure

| Path | Holds |
|:--|:--|
| `scripts/scan.py`, `scripts/doctor.py` | Unified entry point; environment validator (`--ops`: scheduled-task health) |
| `scripts/kalshi/` | Client, executor (`GATES`), settler, edge detection, risk, daily summary |
| `scripts/prediction/`, `scripts/shared/` | Crypto/weather/S&P scanners; stats, odds cache, `paths`, logging |
| `scripts/backtest/` | Backtester, `calibration_study`, `correlation_check`, `shadow_book`, `betting_audit` |
| `scripts/schedulers/`, `scripts/diagrams/` | Task Scheduler wrappers and installer; homepage diagram build/`--check` |
| `app/config.py` | Single source of truth for env-driven knobs (`.env.example` lists them all) |
| `skills/` | Canonical skill source — **edit here**; `.claude/skills/` holds git-ignored junctions |
| `.claude/` | `commands/`, `settings.json`, `html/` (ops deck → edge-radar.mikesailab.com) |
| `site/` | Public page → edge-radar.ai-automation-tools.dev (Vercel root) |
| `tests/` | pytest (`make test`); `test_site.py` pins both static pages |
| `docs/` | Index `docs/README.md`: `RULES-RATIONALE.md`, `CHANGELOG.md` (older months in `changelog/`), `ROADMAP.md`, `diagrams/`, `kalshi/`, `scripts/`, `setup/`, `task-schedules/` |

**Runtime dirs** (gitignored, auto-created): `data/`, `logs/`, `reports/`, `.env`.

---

## Security & Safety Rules

> **NON-NEGOTIABLE** — these override all other instructions.

### API keys

- All keys in `.env` — never hardcoded, never logged, never printed. Load with `python-dotenv` in every script.
- `.env` is gitignored — verify before every commit.

### Execution gates

Every gate runs before any trade executes. The reject gates are one ordered list, `GATES` in
`kalshi_executor.py`, run by the fresh scan (`size_order`), the scan preview (static gates only) and the
`--pick`/`--ticker` cache replay (ER-19). Add or change a gate there, never in one path.

| # | Gate | Type |
|:-:|:-----|:-----|
| 1 | Daily loss limit not breached; the day is `DAILY_LOSS_TZ`'s (America/New_York, ER-16) | Reject |
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

Standing rules. Evidence for each: [rationale → sizing rules](docs/RULES-RATIONALE.md#sizing-rules).

- **Every edge floor is net of fees, and Kelly sizes off net edge.** `min_edge_for()` = per-sport floor + `fee_per_contract(price)`; the taker fee is `ceil(0.07 x C x P x (1-P))` per order. `KALSHI_FEE_RATE=0` turns it off. *F1.*
- **Fill fees come from `fee_cost`, first key PRESENT, not first truthy** (we fill as taker; an unknown payload returns `None`). Repair: `kalshi_settler.py backfill-fees --apply`. *S23b.*
- **Kelly is `edge / (1 - price)`.** *C11.*
- **Two sizing lanes.** Below ~30c the flat floor `round(UNIT_SIZE / price)` binds, so **`UNIT_SIZE` is the longshot knob**; above ~60c Kelly binds, so **`KELLY_FRACTION` is the favorites knob**.
- **`KELLY_FRACTION` is a portfolio fraction**, divided by `batch_size = min(len(opportunities), --max-bets)`. **Keep it <= 0.5.**
- **The budget cap is floor-aware:** it never shaves an order below its unit floor, bisects for the largest feasible scale, and drops whole orders (lowest composite first) only when the floors alone cannot fit. *C11b.*
- **NO bets are damped at both price ends:** below `NO_SIDE_KELLY_PRICE_FLOOR` and at/above `NO_SIDE_KELLY_PRICE_CEILING`, at `NO_SIDE_KELLY_MULTIPLIER` of Kelly. Damped, not gated; the 35-50c NO band is left alone. *F4.*
- **A sport with no settled history gets no live money** beyond a pilot floor; **record whether an operator or a review set it.** The NFL/NCAAF 0.06 pilots are operator overrides, removed when S10 ships. *S1, S1b, S21c.*
- **A 100% one-sided book is a diagnostic, not a parameter fit.** Solve a parameter on the pre-gate population, never on the bets the gate selected. **Never refit NCAAF `margin_stdev` down to 9.5.** *S21, S21c.*
- **Lowering a nominal floor is not lowering the effective one:** the fee is added. Check the price band and count of what would actually be bet before lifting a floor. *S21c.*
- **An unknown `--filter` matches zero markets** (only a NOTE says so). Fix filter bugs in code, never in a `.bat`; a job's flags live in its `.bat` and its template in `scripts/schedulers/automation/build_cronsole_registry.py` (rerun it; `site/registry/` is generated). *S21c.*
- **"No opportunities" means something only if the markets were scored:** compare detector results to markets fetched. `Integration-Drift-Check` may open a **draft** `drift-fix/<date>` PR; nothing merges itself. *M1.*
- **`won` is whether the PREDICTION was right, never whether the row profited.** *S21.*
- **Gate 4.8 reads the Odds API start time, not the ticker.** It fails open, so `daily_summary.load_post_kickoff_orders()` reports proven vs suspected post-kickoff orders. *S23, S23b.*
- **Never hold both sides of one game (Gate 6b).** Sides come from the trade log joined on `order_id`, never the venue payload (v2 reports orders YES-side); resting orders count. Gate 6 is series-scoped: `MAX_PER_EVENT=2` is per series per game. *S22.*
- **A freeze must not block its own exit:** a frozen sport needs an evidence stream, which is `scripts/backtest/shadow_book.py` (pre-gate; never `last_scan.json`). *S21b.*
- **Gate 2b measures dollars against equity (cash + positions), portfolio-wide and per sport.** It rejects at/over a ceiling and trims to the headroom otherwise; the batch loop accumulates approved cost. Live 0.50 / 0.33. *S4.*
- **Lead time is the exposure risk, not the sport:** Gate 3.7 caps days-to-event for game markets (live 14). Futures are exempt by `category`, not ticker prefix. *S5.*
- **Sizing is whole-account; spending is per-shard** (read per market from `exchange_index`). `shard_funding.ensure_shard_funded()` moves exactly the shortfall, capped by `MAX_AUTO_SHARD_TRANSFER`, and re-reads the balance after. *X1, U1.*
- **A gate on placement is not a gate on lifetime:** `cancel_live_resting_orders` cancels resting orders at kickoff, keyed on `event_start_time` from the trade log. *S23c.*
- **Bracket dedup ranks `(clears every static gate, composite, edge, ticker)`** through `preflight_gate_status`, so preview and executor pick the same survivor. *2026-09-19.*
- **Per-team context is keyed `(sport, date, team)`,** never by team code alone. *2026-10-27.*
- **Discrete-margin sports (NHL, MLB, soccer) are priced only within 0.5 of a book's own line.** Do not widen it without a discrete margin model. *2026-10-26.*
- **NFL margins use `discrete_margin_pmf`, never a normal CDF.** Refit with `scripts/backtest/fit_nfl_margin.py`, never by hand. When one strike dominates a sport's bets, compare the model to history at that strike. *2026-11-03.*
- **No correlation guard exists, deliberately** (measured and rejected). Re-run `scripts/backtest/correlation_check.py` as settlements accumulate. *C11b.*

### Scoring & confidence rules

Evidence: [rationale → scoring](docs/RULES-RATIONALE.md#scoring-and-confidence-rules).

- **The model's probabilities are measurably worse than the Kalshi price** (market Brier won 6 of 6 months). Treat claimed edge as ~5x optimistic. **Re-run `scripts/backtest/calibration_study.py` before adding sizing aggression.** *F3.*
- **Every composite scales edge as `min(edge / 0.01, 10)`.** Never reintroduce `edge * 20`. *C10, C10b.*
- **Confidence bumps go down only** (`_adjust_confidence_with_stats()` in `edge_detector.py`). *R13.*
- **`market_price_at_entry` and `fair_value` are side-relative; never flip them for NO bets.** "Brier" alone is not a quantity: **always report model and market Brier as a labelled pair.** *S18.*
- **Per-event Odds API responses date markets only:** use `_bookmaker_last_update()`, and model that shape in fixtures. *S19.*
- **The sports composite caps `high` at the `medium` weight** (`{low:3, medium:6, high:6}`); futures keep `high: 9`. *C4.*

### Venue eligibility (S3) — fails CLOSED

Evidence: [rationale → venue eligibility](docs/RULES-RATIONALE.md#venue-eligibility).

- Before any live order, `execute_pipeline` checks `data/cache/venue_eligibility.json` per venue **and product**, and **`unknown` blocks exactly like `blocked`.** Dry runs skip the check.
- A structural rejection (jurisdiction, permission, KYC) aborts the batch and records the block; transient errors never disable a venue.
- **Nothing clears a block automatically:** only a real venue acceptance, or the owner-run probe `python scripts/doctor.py --verify-eligibility --ticker <open sports ticker>` (a real 1¢ unfillable order, then cancelled). `ok` decays to `unknown` after `ELIGIBILITY_TTL_DAYS` (30); `blocked` never decays.
- **Never truncate the tail of a venue error;** route it through `venue_eligibility.actionable_reason()`.

### Dry run

- Default `DRY_RUN=true`; set `false` only for live execution.
- Dry runs log identically to live, so backtests stay valid.

---

## Risk Limits

Code defaults below. **The live `.env` overrides several** (sizing, daily loss, exposure caps, lead time, per-sport
floors, the NFL/NCAAF pilots, switched-off markets): run `python scripts/doctor.py` before quoting a limit. Which
overrides and why: [rationale → risk limits](docs/RULES-RATIONALE.md#risk-limits-code-defaults-and-live-overrides).
Every knob with its comment: `.env.example`; typed and validated in `app/config.py`.

```env
UNIT_SIZE=1.00                  # flat floor per bet: the longshot knob
KELLY_FRACTION=0.25             # divided by batch size: the favorites knob; keep <= 0.5
MAX_BET_SIZE=100                # Gate 8 (USD)
MAX_DAILY_LOSS=250              # Gate 1 (USD)
MAX_OPEN_POSITIONS=50
MAX_PER_EVENT=2
MAX_OPEN_EXPOSURE_PCT=0         # Gate 2b, 0 = off (also MAX_SEGMENT_EXPOSURE_PCT)
MIN_EDGE_THRESHOLD=0.03         # Gate 3; MIN_EDGE_THRESHOLD_<SPORT>[_<GAME|SPREAD|TOTAL>] override it
KALSHI_FEE_RATE=0.07            # F1; 0 disables fee awareness
MAX_EDGE=0.50
MIN_MARKET_PRICE=0.12
MAX_BID_ASK_SPREAD=0.05
MAX_DAYS_TO_EVENT_FOR_GAME_MARKETS=0
MIN_COMPOSITE_SCORE=6.0
MIN_CONFIDENCE=medium
NO_SIDE_FAVORITE_THRESHOLD=0.25
NO_SIDE_MIN_EDGE=0.25
NO_SIDE_MIN_EDGE_GLOBAL=0.08
NO_SIDE_KELLY_PRICE_FLOOR=0.35  # NO damping below this; NO_SIDE_KELLY_PRICE_CEILING=0 (off) above
NO_SIDE_KELLY_MULTIPLIER=0.5
ALLOW_PREDICTION_BETS=false
ALLOW_LIVE_BETS=false
KALSHI_SUBACCOUNT=0
```

> **⚠️ Config changes require restarting any long-running host process.** `kalshi_executor.py` snapshots every gate threshold into module-level globals **at import time**. The CLI re-imports per invocation; anything else must restart or call `reload_risk_config()`.

> **Scheduler `.bat` files pass `--unit-size` and `--budget` explicitly**, so `.env` changes to those knobs never reach automated runs. Change both.

---

## Common Commands

```bash
pip install -r requirements-dev.txt   # runtime + tests and hooks; requirements.txt is runtime only

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
python scripts/backtest/betting_audit.py --save   # weekly review battery, every sport (read-only)

# Automation
python scripts/schedulers/automation/install_windows_task.py install
python scripts/doctor.py --ops                    # scheduled tasks, backups, report freshness (read-only)

# Makefile: scan-mlb, scan-all, status, settle, report, backtest, test, hooks
```

Full CLI reference: `docs/scripts/SCRIPTS_REFERENCE.md`. Scheduled tasks: `docs/task-schedules/README.md`, notably `Daily-Summary` at 4:50 AM PT (ops health, yesterday's P&L, open exposure, today's pending, 7d rolling), emailed as soon as it finishes.

---

## Session Startup Checklist

1. `git sync-master` — local master goes stale otherwise (work happens on `mike_desktop`, pushes go to remote master).
2. `python scripts/kalshi/kalshi_executor.py status`: open positions, exposure and today's P&L.
3. If the daily loss limit is breached, **no new positions**.
4. Confirm `DRY_RUN` in `.env`.
5. `python scripts/shared/check_odds_keys.py` — cached Odds API quota (`--live` probes each key and costs N requests). A cached zero expires after 24h and reads as `unknown` until re-probed.
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
- A single position would exceed 10% of bankroll (enforced in code: `HARD_STOP_POSITION_PCT`, the last step of `size_order`; B3)
- API credentials are not loaded from the environment
- The market is clearly illiquid (spread > 5%) (enforced in code as Gate 3.6; L2)
- The action would violate a platform's TOS

---

## Stack

Python 3.11+ · `pandas` / `numpy` / `scipy` · JSON ledgers in `data/history/` · Windows Task Scheduler · pre-commit (detect-secrets, black, flake8). Each entry point puts `scripts/shared` on `sys.path` and imports `paths`. No MCP server is needed: `docs/setup/mcp-servers.md`.

---

<sub>Built on AX Platform multi-agent architecture &mdash; Claude Code is the primary development environment</sub>
