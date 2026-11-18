<div align="center">

# ⏰ Edge-Radar Scheduled Tasks

**The repo owner's live Windows Task Scheduler setup: scan → execute → email → settle → reconcile → calibrate → review, unattended.**

[![Scheduler](https://img.shields.io/badge/Windows-Task%20Scheduler-0078D4?style=for-the-badge&logo=windows&logoColor=white)](#registering-the-tasks)
[![Pipeline](https://img.shields.io/badge/Pipeline-16%20Tasks-8B5CF6?style=for-the-badge)](#at-a-glance)
[![Times](https://img.shields.io/badge/Times-PT%20%C2%B7%20ET%20noted-2ea44f?style=for-the-badge)](#daily-fire-sequence)
[![Templates](https://img.shields.io/badge/Templates-Copy%20%26%20Adapt-F97316?style=for-the-badge)](#reproducing-this-on-your-own-machine)

</div>

> [!NOTE]
> **This is the schedule the repo owner actually runs, published as a reference, not a turnkey installer.** The `.bat` wrappers the owner's tasks run are tracked under `scripts/schedulers/` (paths from `%~dp0`, recipients from `.env`); this doc also carries **sanitized templates** — see [Reproducing this on your own machine](#reproducing-this-on-your-own-machine). For just the minimal "execute + settle + calibration" core, start with [`AUTOMATION_GUIDE.md`](../setup/AUTOMATION_GUIDE.md) and its one-command installer.

**Task Scheduler folder:** `\AI-Automation-Tools-Org-LocalApps\Edge-Radar-MikesAILab\` &nbsp;·&nbsp; **Times:** PT (ET in parentheses) &nbsp;·&nbsp; **History:** every add, change and retirement is in [`docs/CHANGELOG.md`](../CHANGELOG.md).

Task Scheduler is the only active scheduling mechanism. Every action launches through `scripts/schedulers/run-hidden.vbs` (no console flash; passes through the exit code of whatever it launches, so a `.bat` must end with `exit /b`; a scheduler stop kills the whole process tree via `run-hidden-guard.ps1`). `install_windows_task.py status --task-folder '<folder>'` lists every task in a folder, including ones it didn't install.

---

## At a Glance

⚠️ = **places real orders** (`DRY_RUN=false`). Every execute task emails its report as action 2 the moment the scan finishes.

| # | Task | Schedule (PT) | What it does |
|:-:|:-----|:--------------|:-------------|
| 1 | `Integration-Drift-Check` | Daily 4:15 AM | Probes Kalshi/odds integration for silent breakage (schema, rules wording, match rates); Claude analysis on WARN/FAIL or Mondays; on WARN/FAIL, may open a **draft PR** with a verified fix (never merges); emails the report |
| 2 | `Daily-Summary` | Daily 4:50 AM | Morning P&L digest (yesterday, open exposure, today pending, 7-day context), then emails it |
| 3 | `All-Sports-SameDay-Execution` ⚠️ | Daily 5:05 AM | Today's games, all sports — max 5 bets, 12% budget |
| 4 | `Shadow-Book-NCAAF` | Daily 6:00 AM | S21b shadow book: scores markets pre-gate (NCAAF; MLB/NHL/NCAAB spreads; MLS totals; European soccer). **No orders** |
| 5 | `Weekly-Futures-Execution` ⚠️ | Sat 9:00 AM | Championship/outright futures — max 3 bets, 10% budget |
| 6 | `WeeklyAccountGraph` | Sun 9:40 AM | Refreshes the private account-growth graph (local only) |
| 7 | `All-Sports-NoDateFilter-Midday-Execution` ⚠️ | Daily 11:00 AM | Wide net, all dates — max 5 bets, 12% budget |
| 8 | `All-Sports-SameDay-Late-Execution` ⚠️ | Daily 2:00 PM | Tonight's games, late news — max 5 bets, 12% budget |
| 9 | `WeeklyOddsKeyProbe` | Sun 6:00 PM | Live-probes every Odds API key, refreshes the quota cache |
| 10 | `Calibration` | Sun 7:00 PM | Brier refresh + C8 stdev recalibration (`--days 30`) |
| 11 | `Backtest` | Sun 7:30 PM | Equity curve, drawdown, Sharpe, strategy comparison |
| 12 | `All-Sports-NextDay-Execution` ⚠️ | Sun–Thu 8:30 PM | Tomorrow's games — max 5 bets, 12% budget |
| 13 | `Reconcile` | Daily 11:30 PM | Local trade log vs Kalshi positions; flags drift; then zips the ledger to a backed-up folder (ER-08) |
| 14 | `Weekly-Analysis` | Sun 11:45 PM | Weekly betting audit (every sport, read-only) + 7-day performance report; one email, audit flags first |
| 15 | `Hourly-Settle` | Hourly at :35 | `kalshi_settler.py settle` — keeps Gate 1 (daily loss) current intraday |
| 16 | `CLV-Capture` | Every 5 min | S8: samples the closing book before each open position's event. Read-only at the venue |

### Daily fire sequence

```
 4:15 AM  Daily    Integration-Drift-Check        [+email]
 4:50 AM  Daily    Daily-Summary                  [+email]
 5:05 AM  Daily    All-Sports-SameDay-Execution   [+email]  ⚠️
 6:00 AM  Daily    Shadow-Book-NCAAF
 9:00 AM  Sat      Weekly-Futures-Execution       [+email]  ⚠️
 9:40 AM  Sun      WeeklyAccountGraph
11:00 AM  Daily    All-Sports-NoDateFilter-Midday-Execution [+email] ⚠️
 2:00 PM  Daily    All-Sports-SameDay-Late-Execution [+email] ⚠️
 6:00 PM  Sun      WeeklyOddsKeyProbe
 7:00 PM  Sun      Calibration
 7:30 PM  Sun      Backtest
 8:30 PM  Sun-Thu  All-Sports-NextDay-Execution   [+email]  ⚠️
11:30 PM  Daily    Reconcile
11:45 PM  Sun      Weekly-Analysis                [+email]

  :35 every hour   Hourly-Settle
  every 5 min      CLV-Capture
```

### Fires per day (excluding Hourly-Settle and CLV-Capture)

| Day | Fires | Max new bets |
|:----|:-----:|:-------------|
| Mon–Thu | 8 | 5 + 5 + 5 + 5 (NextDay) = **20** |
| Fri | 7 | 5 + 5 + 5 = **15** (no NextDay) |
| Sat | 8 | 15 + 3 futures = **18** (no NextDay) |
| Sun | 13 | **20** |

The practical count is far lower: `--exclude-open`, Gate 7 series dedup, Gate 2b exposure caps and `--min-bets 1` all bind first. Gate 2 (`MAX_OPEN_POSITIONS`) is the hard ceiling.

### Halting live orders

**First, stop everything:** set `DRY_RUN=true` in `.env`. The CLI re-reads `.env` per run, so the next fire of every execute task is already dry.

To stop a single task instead, disable it. The folder below is a copy as of 2026-11-17; if it has moved, `Get-ScheduledTask | Where-Object TaskPath -match 'Edge-Radar'` finds it.

```powershell
Disable-ScheduledTask -TaskPath '\AI-Automation-Tools-Org-LocalApps\Edge-Radar-MikesAILab\' -TaskName '<task>'
```

---

## Task Details

The scheduled `.bat` wrappers live under `scripts/schedulers/` and are tracked (ER-27), so `git log` shows every change to a task's flags; old and one-off wrappers there stay gitignored. Execute wrappers print `kalshi_executor.py status` before and after the scan.

### Weekly betting audit (inside `Weekly-Analysis`, Sun 11:45 PM PT)

`weekly_analysis.bat` runs `scripts/backtest/betting_audit.py --save --analyze auto` **before** the 7-day
performance report, and the `weekly-analysis` email opens with the audit's status, **Flags** and (when flagged)
**Analysis** sections, then the full performance report. One Sunday email, not two.

The Analysis pass is a headless session through `scripts/shared/agent_cli.py` in which only `Read`, `Grep` and
`Glob` exist (ER-09). Every unattended session goes through `agent_cli`, which refuses to start one without an
allowlist unless the caller passes `unrestricted=True` by name.

| Property | Value |
|:--|:--|
| **Report** | `reports/Maintenance/betting-audit/betting_audit_<date>.md` (+ `.json`); log `logs/betting_audit.log` |
| **Cost** | Deterministic and local (settlement/trade logs, shadow book, detector logs, latest drift JSON). No Kalshi or Odds API calls. Model only when flagged |

**Flags:** a live series/side whose wins trail the model by ≥1.5σ over 60d (n ≥ 8); a series whose pre-gate
candidates are ≥90% one direction (n ≥ 20, 14d); rest-day data on any non-NBA/NHL market; post-kickoff, fee-less
settled, or errored orders; a "dark" sport in the latest drift probe. The analysis pass is `claude -p` restricted to
`Read,Grep,Glob`. It never edits code or `.env` and never places orders. Born from the 2026-10-26/27 manual reviews
(*CHANGELOG 2026-10-27*). `/betting-logic-review` starts from this report.

### 1. `Integration-Drift-Check` — Daily 4:15 AM PT (7:15 AM ET)

| Property | Value |
|:--|:--|
| **Action 1** | `run-hidden.vbs` → `maintenance\drift_check.bat` → `scripts/kalshi/integration_drift.py --save --analyze auto --autofix` |
| **Action 2** | `render_report_email.py drift-check` → subject `Edge-Radar \| Drift Check \| … \| <date>` |
| **Report** | `reports/Maintenance/drift/drift_<date>.md` |
| **Cost** | Probe is deterministic, no model, **zero Odds API quota** (reads cached odds only) |

**What the probe checks, per in-season sport series:** market schema fields present; team/strike parse rate from rules and subtitles; odds-event match rate against cached Odds API data; rules-wording templates not in the stored baseline; series prefixes returning zero markets; days since the last bet per sport.

**Claude analysis pass (read-only):** if the probe status is WARN/FAIL, **or** it is Monday, a headless `claude -p` session restricted to `Read,Grep,Glob,WebFetch,WebSearch` (no `--dangerously-skip-permissions`) diagnoses each flag, checks Kalshi's API changelog, and appends an **Analysis** section to the report.

**Auto-fix pass (WARN/FAIL days only, `scripts/kalshi/drift_autofix.py`):** a second Claude session gets edit access to a **throwaway git worktree** of `origin/mike_desktop`, never your checkout. Then deterministic checks decide whether a PR exists at all:

| Outcome of the fix session | Result |
|:--|:--|
| No files changed (false positive, or not confident) | **No PR.** Report says "No code change proposed" |
| Touched anything outside parsing/matching code + tests (`edge_detector.py`, `futures_edge.py`, `ticker_display.py`, `odds_api.py`, `market_client.py`, `tests/`), or deleted a file | **Rejected, no PR.** Diff saved as `drift_<date>.rejected.patch` |
| Fewer tests collected, or the full suite fails (one retry with the failure output) | **Rejected, no PR** |
| Probe re-run on the fixed tree not better than today's | **Rejected, no PR** |
| All checks pass | Pushes `drift-fix/<date>`, opens a **draft** PR into `mike_desktop` with the before/after probe table and test output. Link is in the email |

It **never merges**, never touches master, `mike_desktop`, `.env`, the executor or the risk gates, and can't edit the probe that grades it. While a `drift-fix/*` PR is open, later runs skip the fix pass so one unresolved break doesn't open a PR every day. Tests and the probe run through `drift_autofix.py --in-tree`, because the venv's `edge_radar.pth` would otherwise import the main checkout's code instead of the fix.

**Containment (ER-04).** Agent-written code runs in the worktree before anyone reviews it, so:

- The fix session can read only inside the worktree (`Read(./**)`, `Grep(./**)`, `Glob(./**)`). Its prompt carries the probe report and JSON (copied into the worktree's `data/drift_input/`), never the analysis section, whose session can fetch web pages.
- The worktree's tests and probe get an allowlisted environment: no `.env`, no API keys or tokens, `DRY_RUN=true`. The probe reads markets unsigned (`GET /markets` is public), here and in the daily run.
- The public commit and PR carry the probe table, a diff stat and the test tail. The session's own summary goes only into the emailed report.
- `kalshi_client.py` is off the editable list: it places orders.

**Why it exists:** M1 (CHANGELOG 2026-10-03). Kalshi reworded NFL rules to "... Pro Football game", team extraction failed silently, and the scanner was blind to 13 of 14 NFL games for ~2 weeks while every scan said "no opportunities". **Why 4:15 AM:** ahead of Daily-Summary (4:50) and the first execute (5:05), so a break is in the inbox before money moves.

### 2. `Daily-Summary` — Daily 4:50 AM PT (7:50 AM ET)

| Property | Value |
|:--|:--|
| **Action 1** | `maintenance\daily_summary.bat` → `daily_summary.py --save` |
| **Action 2** | `render_report_email.py daily-summary` → `Edge-Radar \| Daily Summary \| … \| <date>` |
| **Report** | `reports/Performance/daily_summary_YYYY-MM-DD.md` (written even on empty days — proof of life) |

Runs after the overnight settle passes and before the 5:05 execute, so "Open Exposure" reflects overnight carry, not today's fills. It opens with **Ops health** (ER-50, `scripts/shared/ops_health.py`): every task in this folder with its state, last run, result and next run, plus the newest settlement, ledger backup, report per preset and data/log size. A disabled or failing execute task is FAIL, and the email subject then reads `Edge-Radar | Daily Summary | FAIL | <date>`. `python scripts/doctor.py --ops` prints the same table on demand. Also reports post-kickoff orders (S23b). Three blank sections every morning for a week is a real signal: fills not captured, settler not finding settlements, or the pipeline paused.

### 3. `All-Sports-SameDay-Execution` ⚠️ — Daily 5:05 AM PT (8:05 AM ET)

| Property | Value |
|:--|:--|
| **Script** | `same_day_executions\same_day_execute.bat` |
| **Flags** | `--unit-size 1 --max-bets 5 --min-bets 1 --budget 12% --date today --exclude-open --save --execute` |
| **Report** | `reports/Sports/schedulers/same-day-executions/` |
| **Email** | `render_report_email.py same-day` → `Edge-Radar \| Same-Day \| … \| <date>` |

MLB starters announced, NHL morning skate done, weather stable, before sharp money fully lands.

### 4. `Shadow-Book-NCAAF` — Daily 6:00 AM PT

Runs `maintenance\shadow_book.bat`: `shadow_book.py settle`, then `collect --filter ncaafb` and `collect --filter KXMLBSPREAD` (log `logs/shadow_book.log`). **Places no orders.** A freeze stops orders and so stops the settlements that would justify lifting it; a Brier head-to-head needs only model probability, market price and outcome. Taps `scan_all_markets()` **upstream of the risk gates** (`last_scan.json` is post-gate and holds nothing at a 1.0 floor). Read it with `shadow_book.py review --sport ncaaf --save`. Despite the name it also tracks MLB spreads (frozen 2026-10-03), and on Saturdays `collect --futures` logs every priced futures market under both de-vig methods for the ER-42 A/B (`shadow_book.py devig-review`).

### 5. `Weekly-Futures-Execution` ⚠️ — Sat 9:00 AM PT (12:00 PM ET)

| Property | Value |
|:--|:--|
| **Script** | `futures_executions\weekly_futures_execute.bat` |
| **Flags** | `scan.py futures --unit-size 1 --max-bets 3 --min-bets 1 --budget 10% --exclude-open --save --report-dir "reports\Futures\schedulers" --execute` |
| **Email** | `render_report_email.py weekly-futures` → `Edge-Radar \| Weekly Futures \| … \| <date>` |

Thin, longshot-heavy boards — most weeks place **0 bets**, by design. `futures_edge.py` always writes a report on `--save`, so empty weeks still email. Offseason series with no outright odds are skipped; golf prices only the 4 majors.

### 6. `WeeklyAccountGraph` — Sun 9:40 AM PT

Direct `python.exe scripts\schedulers\automation\refresh_account_graph.py`. Pulls the live Kalshi snapshot and regenerates the interactive HTML + PNG into `docs/my-documents/account-graph/latest/` (gitignored), log `logs/account_graph_refresh.log`. **Never published** — it carries real balance figures and the repo is public (CHANGELOG 2026-09-07). Install: `install_windows_task.py install account-graph`.

### 7. `All-Sports-NoDateFilter-Midday-Execution` ⚠️ — Daily 11:00 AM PT (2:00 PM ET)

| Property | Value |
|:--|:--|
| **Script** | `no_date_filter_executions\no_date_filter_execution_midday.bat` |
| **Flags** | `--unit-size 1 --max-bets 5 --min-bets 1 --budget 12% --exclude-open --save --execute` (**no `--date`**) |
| **Email** | `render_report_email.py nodatefilter-midday` → `Edge-Radar \| Midday \| … \| <date>` |

The no-date-filter scan finds candidates nearly every run while `--date today` is empty most mornings; slate width was the bottleneck, not time of day (`timing-analysis-2026-05-17.md`). 11 AM also catches MLB pitcher confirmations and NBA/NHL morning-skate news. Gate 3.7 (14-day cap) bounds how far out it can buy game markets.

### 8. `All-Sports-SameDay-Late-Execution` ⚠️ — Daily 2:00 PM PT (5:00 PM ET)

| Property | Value |
|:--|:--|
| **Script** | `same_day_executions\same_day_execute_late.bat` |
| **Flags** | `--unit-size 1 --max-bets 5 --min-bets 1 --budget 12% --date today --exclude-open --save --execute` |
| **Email** | `render_report_email.py same-day-late` → `Edge-Radar \| Same-Day Late \| … \| <date>` |

Late-breaking news on tonight's slate: scratches, goalie confirmations, afternoon sharp moves.

### 9. `WeeklyOddsKeyProbe` — Sun 6:00 PM PT

`maintenance\odds_keys.bat` → `check_odds_keys.py --live` (~14 requests/week). Refreshes `data/cache/odds_api_quota.json` so a key going bad is caught before a scan needs it. Pairs with the `_ZERO_TTL_HOURS` expiry in `scripts/shared/odds_api.py` (CHANGELOG 2026-09-09).

### 10. `Calibration` — Sun 7:00 PM PT

`maintenance\calibration.bat` → `model_calibration.py --days 30 --save`. Brier score, calibration curves, per-sport/confidence/edge breakdowns, and the **C8 stdev recalibration** into `data/cache/calibration_stdevs.json`. The window must stay at 30: at `--days 7` no (sport, category) pair reached `_MIN_CALIB_SAMPLES=20` and the loop silently wrote the defaults back (CHANGELOG 2026-07-31; `tests/test_calibration_config.py` guards it).

### 11. `Backtest` — Sun 7:30 PM PT

`maintenance\backtest.bat` → `backtester.py --simulate --save`. Equity curve, drawdown, streaks, profit factor, Sharpe, ROI, breakdowns and filter-strategy simulation. Runs after Calibration.

### 12. `All-Sports-NextDay-Execution` ⚠️ — Sun–Thu 8:30 PM PT (11:30 PM ET)

| Property | Value |
|:--|:--|
| **Script** | `next_day_executions\next_day_execute.bat` |
| **Flags** | `--unit-size 1 --max-bets 5 --min-bets 1 --budget 12% --date tomorrow --exclude-open --save --execute` |
| **Email** | `render_report_email.py next-day` → `Edge-Radar \| Next-Day \| … \| <date>` |

8:30 PM PT gives books time to post next-day lines (it was empty 43% of the time at 6 PM). Fri/Sat are skipped; the Sunday 5:05 AM run covers Sunday NFL with fresher data. To run it ad hoc on a skipped night: `Start-ScheduledTask -TaskPath '\AI-Automation-Tools-Org-LocalApps\Edge-Radar-MikesAILab\' -TaskName 'All-Sports-NextDay-Execution'`.

### 13. `Reconcile` — Daily 11:30 PM PT

`maintenance\reconcile.bat` → `kalshi_settler.py reconcile`. Runs 55 minutes after the 10:35 PM settle pass, so drift it reports is real: a missed settlement, API lag, or local-log corruption.

Then `scripts/shared/prune_logs.py` (ER-28) keeps `logs/` bounded: it deletes `<name>_<date>.log` files more than 90 days old and cuts any fixed-name log (`clv_capture.log`, `shadow_book.log`, `scan_*.log`, ...) over 5 MB down to its newest 1 MB. The wrapper exits with the reconcile's code, not the prune's.

**Action 2 (ER-08):** `scripts/shared/backup_ledger.py --dest <backed-up folder>` zips `data/history/`'s ledger
files (trades, settlements, journal, shadow book) into `edge-radar-ledger_<UTC stamp>.zip` and deletes zips older
than 30 days. Point `--dest` at a folder a sync client backs up; the owner uses a OneDrive folder. Exits 1 if a
JSON file in the zip doesn't parse. Log: `logs/backup_ledger_<date>.log`. Restore steps:
[`data/history/README.md`](../../data/history/README.md#backups-and-restore).

### 14. `Weekly-Analysis` — Sun 11:45 PM PT

| Property | Value |
|:--|:--|
| **Action 1** | `maintenance\weekly_analysis.bat` → `betting_analysis.py --days 7 --save` |
| **Action 2** | `render_report_email.py weekly-analysis` → `Edge-Radar \| Weekly Analysis \| … \| <date>` |
| **Report** | `reports/Performance/betting_analysis_YYYY-MM-DD_7d.md` |

Runs after Reconcile and the 11:35 settle. The filename carries the UTC date (tomorrow's), which is why the emailer picks the newest fresh file rather than today's name.

### 15. `Hourly-Settle` — every hour at :35

Direct `python.exe scripts\kalshi\kalshi_settler.py settle`. Keeps the trade log fresh so Gate 1 sees intraday settlements and R4 / S23c resting-order cleanup runs on time. Safe alongside execute tasks thanks to the M2 cross-process trade-log lock. **:35** is the one minute slot clear of every other task. Install: `install_windows_task.py install settle`.

### 16. `CLV-Capture` — every 5 minutes

`maintenance\clv_capture.bat` → `clv_capture.py` (log `logs/clv_capture.log`). Samples the book shortly before each open position's event and writes the closing book + CLV to the trade row. Calls `get_market()` only — never places, cancels or modifies. A pass with nothing due makes **zero** API calls, which is what makes the cadence affordable. Venue reads happen outside the M2 lock; captures are re-applied by `trade_id` inside it.

---

## Reproducing this on your own machine

You need two kinds of files — `.bat` wrappers and `schtasks` registrations. You do **not** need all 16 tasks: the **minimal core is `All-Sports-SameDay-Execution` + `Hourly-Settle`**, then add `Calibration`, then emails and the extra execute runs as you trust the pipeline. Run the [dry-run workflow](#dry-run-testing-workflow) before any execute task can spend real money.

### Placeholders

| Placeholder | Meaning | Example |
|:--|:--|:--|
| `<REPO_ROOT>` | Absolute path to your Edge-Radar checkout | `C:\Users\you\Edge-Radar` |
| `<YOUR_EMAIL>` | Inbox reports go **to** (`.env` → `NOTIFY_EMAIL`) | `you@example.com` |
| `<YOUR_SENDER>` | Verified-domain address reports come **from** (`.env` → `RESEND_FROM`) | `Edge-Radar <fleet@send.yourdomain.com>` |
| `<FOLDER>` | Your Task Scheduler folder | `\Edge-Radar\` |

`RESEND_API_KEY` lives in the **OS environment**, not `.env` (`setx RESEND_API_KEY "re_..."`), so Task Scheduler picks up a rotated key on the next launch. A User-scoped variable is invisible to `SYSTEM`, which is why these tasks run as your own user.

> **Time zone:** Task Scheduler fires on your machine's local time. Pick times that suit your slate, not these literal values.

### Template A — execute wrapper (`.bat`)

```batch
@echo off
REM WARNING: places live orders when DRY_RUN=false in .env.
REM Self-locate the repo root (adjust ..\..\.. to your folder depth):
cd /d "%~dp0..\..\.."

REM Pin the log's encoding instead of leaving it to the machine's code page:
set PYTHONIOENCODING=utf-8
set LOG=logs\scan_same_day.log

.venv\Scripts\python.exe scripts\kalshi\kalshi_executor.py status
echo ===== %date% %time% >> %LOG%
.venv\Scripts\python.exe scripts\scan.py sports ^
  --unit-size 1 --max-bets 5 --min-bets 1 --budget 12%% ^
  --date today --exclude-open --save ^
  --report-dir "reports\Sports\schedulers\same-day-executions" --execute >> %LOG% 2>&1
set RC=%ERRORLEVEL%
echo exit code %RC% >> %LOG%
.venv\Scripts\python.exe scripts\kalshi\kalshi_executor.py status
exit /b %RC%
```

The `=====` banner and `exit code N` line are what the email action reads (ER-07): `LOG` must be the
preset's entry in `SCAN_LOGS` in `render_report_email.py` (`scan_same_day`, `scan_same_day_late`,
`scan_nodatefilter_midday`, `scan_next_day`, `scan_weekly_futures`).

`%%` is required: a literal `%` must be doubled inside a `.bat`. The owner's variants differ only in `--date` and `--report-dir`:

| Variant | `--date` | `--report-dir` |
|:--|:--|:--|
| Same-day | `today` | `same-day-executions` |
| Midday wide net | *(omit)* | `no-date-filter-midday-executions` |
| Late same-day | `today` | `same-day-late-executions` |
| Next-day | `tomorrow` | `next-day-executions` |

> Scheduler `.bat` files pass `--unit-size` and `--budget` explicitly, so `.env` changes to those knobs never reach automated runs. Change both.

### Template B — maintenance wrapper (`.bat`)

```batch
@echo off
cd /d "%~dp0..\..\.."
.venv\Scripts\python.exe scripts\kalshi\kalshi_settler.py settle
```

| Task | Last line |
|:--|:--|
| Settle / Reconcile | `scripts\kalshi\kalshi_settler.py settle` / `reconcile` |
| Calibration | `scripts\kalshi\model_calibration.py --days 30 --save` |
| Backtest | `scripts\backtest\backtester.py --simulate --save` |
| Weekly-Analysis | `scripts\kalshi\betting_analysis.py --days 7 --save` |
| Daily-Summary | `scripts\kalshi\daily_summary.py --save` |
| Odds key probe | `scripts\shared\check_odds_keys.py --live` |
| CLV capture | `scripts\kalshi\clv_capture.py >> logs\clv_capture.log 2>&1` |

### Template C — report emailer (tracked, nothing to copy)

`scripts/schedulers/automation/render_report_email.py <preset>` renders the report markdown to inline-styled HTML (markdown-it-py, tables byte-exact) and sends through `scripts/schedulers/automation/send_report_email.py` (Resend; `NOTIFY_EMAIL`, `RESEND_FROM` and `RESEND_API_KEY` must be set, `--check` probes without sending). **No model involved.**

| Preset | Task | Subject | Log |
|:--|:--|:--|:--|
| `drift-check` | `Integration-Drift-Check` | `Edge-Radar \| Drift Check \| … \| <date>` | `logs/email_drift_check.log` |
| `daily-summary` | `Daily-Summary` | `Edge-Radar \| Daily Summary \| … \| <date>` | `logs/email_daily_summary.log` |
| `same-day` | `All-Sports-SameDay-Execution` | `Edge-Radar \| Same-Day \| … \| <date>` | `logs/email_sameday.log` |
| `nodatefilter-midday` | `All-Sports-NoDateFilter-Midday-Execution` | `Edge-Radar \| Midday \| … \| <date>` | `logs/email_nodatefilter_midday.log` |
| `same-day-late` | `All-Sports-SameDay-Late-Execution` | `Edge-Radar \| Same-Day Late \| … \| <date>` | `logs/email_sameday_late.log` |
| `next-day` | `All-Sports-NextDay-Execution` | `Edge-Radar \| Next-Day \| … \| <date>` | `logs/email_nextday.log` |
| `weekly-futures` | `Weekly-Futures-Execution` | `Edge-Radar \| Weekly Futures \| … \| <date>` | `logs/email_futures.log` |
| `weekly-analysis` | `Weekly-Analysis` | `Edge-Radar \| Weekly Analysis \| … \| <date>` | `logs/email_weekly_analysis.log` |

- **Which report:** the newest file in the preset's folder modified within `--max-age-hours` (default 3) — not today's name, because filenames carry the UTC date.
- **Failed execute run (ER-07):** for the five execute presets, a non-zero `exit code` in the scan log or no
  fresh report sends `[FAILED] Edge-Radar | <label> | <reason> | <date>` with the log's last run and exits **1**. Every execute run writes a
  report, even with zero bets, so a missing one means the scan died.
- **Outcome in the subject (ER-12, ER-33):** an execution report opens with a mode line such as
  `**LIVE · REAL MONEY · PROD** · 2 placed · 1 failed`, and the subject reads
  `Edge-Radar | Same-Day | LIVE · 2 placed · 1 failed · $2.08 | Mon Nov 16`: mode, outcome, placed cost (sized
  cost on a dry run), then the PT date, which also stops Gmail threading every day into one conversation. A live
  run that placed nothing says `0 placed`. Reports with a `**Status: X**` line put X there (the drift check,
  the weekly audit); a failed run puts its reason, after `[FAILED]`.
- **Banner and phone layout (ER-33):** a three-cell banner (mode, orders, cost; or report, status, time) opens
  the email and doubles as the inbox preview line. Tables wider than six columns get a stacked copy, one card per
  row, that replaces them below 600px wide. Report times read UTC · PT · ET.
- **No fresh report, other presets:** exits 2 and sends nothing. A stale email is worse than none.
- **Preview:** `render_report_email.py same-day --dry-run out.html`. **Probe Resend without spending quota:** `send_report_email.py --check`.
- Every successful send stamps `logs/last_email_sent.json`, so a broken mail path is detectable on its own.

### Registering the tasks

**Action 1 (the `.bat`, launched hidden):**

```powershell
schtasks /Create /TN "<FOLDER>All-Sports-SameDay-Execution" `
  /TR "wscript.exe \"<REPO_ROOT>\scripts\schedulers\run-hidden.vbs\" \"<REPO_ROOT>\scripts\schedulers\same_day_executions\same_day_execute.bat\"" `
  /SC DAILY /ST 05:05 /F
```

**Action 2 (the email).** `schtasks` can only create one action; append the second with PowerShell. Task Scheduler runs action 2 even if action 1 exits non-zero:

```powershell
$t     = Get-ScheduledTask -TaskPath "<FOLDER>" -TaskName "All-Sports-SameDay-Execution"
$email = New-ScheduledTaskAction -Execute "wscript.exe" `
  -Argument '"<REPO_ROOT>\scripts\schedulers\run-hidden.vbs" "<REPO_ROOT>\.venv\Scripts\python.exe" "<REPO_ROOT>\scripts\schedulers\automation\render_report_email.py" same-day'
Set-ScheduledTask -TaskPath "<FOLDER>" -TaskName "All-Sports-SameDay-Execution" -Action $t.Actions[0],$email
```

> [!IMPORTANT]
> **Leave `StartWhenAvailable` off. No task here catches up.** Since 2026-09-30 this is the rule for every timed task on Mike's machine (only the two backups are exempt): a run whose trigger passes while the machine is off or asleep is skipped, and Mike runs it by hand if it matters. For execute tasks that is the safer default, because a caught-up run fires on wake against whatever slate is live then, not the one it was scheduled for. `install_windows_task.py` no longer sets the flag (it did until 2026-10-12), and the weekly Task Scheduler audit flags any task that has it on.
>
> The cost is that a missed trigger is silent: the task still reads `Ready`, and `LastTaskResult 267011` ("not yet run") looks the same as a task waiting for a future date. That is how two one-shot reviews were lost for ~4 months (see the retired-tasks table below). After a one-shot's date, check that it actually ran.

| Cadence | `schtasks` flags |
|:--|:--|
| Every day | `/SC DAILY /ST HH:MM` |
| Sun–Thu | `/SC WEEKLY /D SUN,MON,TUE,WED,THU /ST HH:MM` |
| One weekday | `/SC WEEKLY /D SUN /ST HH:MM` |
| Hourly at :35 | `/SC HOURLY /MO 1 /ST 00:35` |
| Every 5 min | `/SC MINUTE /MO 5` |

---

## Management Commands

```powershell
$F = '\AI-Automation-Tools-Org-LocalApps\Edge-Radar-MikesAILab\'

# Status: next run + last result (0 = success)
Get-ScheduledTask -TaskPath $F | ForEach-Object {
  $i = Get-ScheduledTaskInfo -TaskPath $_.TaskPath -TaskName $_.TaskName
  [pscustomobject]@{Name=$_.TaskName; State=$_.State; Next=$i.NextRunTime; Last=$i.LastRunTime; Result=$i.LastTaskResult}
} | Sort-Object Next | Format-Table -AutoSize

Start-ScheduledTask   -TaskPath $F -TaskName 'Reconcile'         # run now
Disable-ScheduledTask -TaskPath $F -TaskName 'Weekly-Futures-Execution'
Enable-ScheduledTask  -TaskPath $F -TaskName 'Weekly-Futures-Execution'
Export-ScheduledTask  -TaskPath $F -TaskName 'Daily-Summary'     # full XML — back up before editing
(Get-ScheduledTask -TaskPath $F -TaskName 'Daily-Summary').Actions | Format-Table Execute, Arguments
Unregister-ScheduledTask -TaskPath $F -TaskName '<task>' -Confirm:$false
```

From Git Bash, prefix `schtasks` with `MSYS_NO_PATHCONV=1` or the `/TN` path is mangled into a filesystem path:

```bash
MSYS_NO_PATHCONV=1 schtasks /run /tn "\AI-Automation-Tools-Org-LocalApps\Edge-Radar-MikesAILab\Daily-Summary"  # pragma: allowlist secret
```

---

## Troubleshooting

| Symptom | Meaning |
|:--|:--|
| `LastTaskResult` non-zero on a two-action task | Either action. Read the scan's report/log **and** the `logs/email_*.log` line before deciding which failed |
| Email action exit **1** + `[FAILED]` email | An execute run's scan exited non-zero or wrote no report. The email carries `logs/scan_*.log`'s last run |
| Email action exit **2** | Non-execute preset: no report modified within 3h. Nothing sent, by design |
| Send error in the email log | Unverified domain or revoked `RESEND_API_KEY`. `send_report_email.py --check` |
| `267009` (0x41301) | Still running |
| `267011` (0x41303) | Never run — or a missed trigger without `StartWhenAvailable` (see above) |
| Scan says "no opportunities" for days | Could be a quiet slate **or a silent matching failure** (M1). Check the latest `Integration-Drift-Check` report for parse/match rates |
| Unknown `--filter` name | Falls through to a literal prefix that matches nothing, and prints a NOTE. Fix filters in code, not the `.bat` |

**`DaysOfWeek` bitmask** (from `Get-ScheduledTask` triggers): Sun 1, Mon 2, Tue 4, Wed 8, Thu 16, Fri 32, Sat 64. So `31` = Sun–Thu, `64` = Sat.

**Folder targeting:** `schtasks /create /tn "MyTask"` lands in the root `\`; always pass the full folder path.

---

## Dry-Run Testing Workflow

1. Set `DRY_RUN=true` in `.env`.
2. Run, safest first: `Reconcile` → `Calibration` → `Backtest` → `Hourly-Settle` → `Integration-Drift-Check` → `All-Sports-NextDay-Execution` → `All-Sports-NoDateFilter-Midday-Execution` → `render_report_email.py <preset> --dry-run out.html`.
3. Check: report file exists, no positions opened, exit code 0, email renders and matches the file, settle/reconcile report no drift.
4. Set `DRY_RUN=false` when confident.

---

## Output Files

```
reports/
├── Sports/schedulers/
│   ├── same-day-executions/               ← #3   5:05 AM
│   ├── no-date-filter-midday-executions/  ← #7  11:00 AM
│   ├── same-day-late-executions/          ← #8   2:00 PM
│   └── next-day-executions/               ← #12  8:30 PM
├── Futures/schedulers/                    ← #5   Sat 9:00 AM
├── Maintenance/drift/drift_<date>.md      ← #1   4:15 AM
└── Performance/
    ├── daily_summary_YYYY-MM-DD.md        ← #2   4:50 AM
    └── betting_analysis_YYYY-MM-DD_7d.md  ← #14  Sun 11:45 PM

logs/   email_*.log · clv_capture.log · shadow_book.log · account_graph_refresh.log
data/history/kalshi_trades.json · kalshi_settlements.json · shadow_book.json
```

---

## Retired Tasks

None of these are registered any more. Reasons and evidence are in [`CHANGELOG.md`](../CHANGELOG.md) under the date given, or in [`changelog/`](../changelog/README.md) for months before 2026-10.

| Task | Retired | Why |
|:--|:--|:--|
| `Email-*` (9 tasks: SameDay, NextDay, Midday, Late, Daily-Summary, Weekly-Analysis, Weekly-Futures, Polymarket, Longshot) | 2026-09-23 | Folded into their scan tasks as action 2; `claude -p` emailers replaced by `render_report_email.py` |
| `NightlySettle` | 2026-09-23 | Duplicate of `Hourly-Settle` |
| `Daily-Polymarket-Execution` (ex `Daily-Polymarket-DryRun`) | 2026-09-29 | Polymarket venue removed |
| `Longshot-Scan` | 2026-09-27 | Longshot strategy abandoned (P1 profile mechanism kept) |
| `NFL-Week1-Review` | after 2026-09-15 | One-shot S1b review; fired 09-15, returned branch A (removal date not recorded) |
| `MonthlyCalibration` | 2026-07-31 | Duplicate of weekly `Calibration`; had never once run |
| `R8-Review`, `U2-Review` | 2026-09-10 | One-shots that never fired (no `StartWhenAvailable`); R8 run by hand, both deleted. XML in `scripts/schedulers/retired-task-xml/` |
| `All-Sports-NoDateFilter-Execution` (Mon/Thu 5:20 AM) | 2026-05-17 | Replaced by the daily Midday run |
| `*-Scan` preview tasks (SameDay, NoDateFilter, MLB/NBA/NHL/NFL-NextDay) | — | Preview-only or per-sport variants, superseded by the consolidated execute tasks; their `.bat` files remain as reference |

---

## References

- [`../../AGENTS.md`](../../AGENTS.md) — risk gates and limits
- [`../setup/AUTOMATION_GUIDE.md`](../setup/AUTOMATION_GUIDE.md) — one-command installer for the core tasks
- [`../../skills/edge-radar/SKILL.md`](../../skills/edge-radar/SKILL.md) — scanner reference
- [`../../.env.example`](../../.env.example) — every tunable, incl. `NOTIFY_EMAIL` / `RESEND_FROM`
- [`../CHANGELOG.md`](../CHANGELOG.md) — history of every schedule change

---

<p align="center">
  <a href="../README.md">Docs index</a>&nbsp;&nbsp;·&nbsp;&nbsp;<a href="../setup/AUTOMATION_GUIDE.md">Automation Guide</a>&nbsp;&nbsp;·&nbsp;&nbsp;<a href="../../AGENTS.md">Risk gates</a>&nbsp;&nbsp;·&nbsp;&nbsp;<a href="#-edge-radar-scheduled-tasks">Back to top</a>
</p>
