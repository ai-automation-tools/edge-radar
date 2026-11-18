# Operations

*Reference for the [`/edge-radar` skill](../SKILL.md).* Makefile shortcuts, the daily workflow, Task Scheduler automation and the `.bat` wrappers.

---

## Makefile Shortcuts


For quick access, the Makefile provides 22 targets:

```bash
make scan-mlb          # Scan MLB today, exclude open, save report
make scan-nba          # Scan NBA
make scan-nhl          # Scan NHL
make scan-nfl          # Scan NFL
make scan-sports       # All sports
make scan-futures      # All futures
make scan-all          # Everything
make status            # Portfolio status
make risk              # Risk dashboard
make settle            # Settle completed bets
make report            # P&L report
make reconcile         # Compare local log vs API
make backtest          # Full backtest analysis
make backtest-sim      # Strategy-comparison simulation + save
make doctor            # Environment validator (shows the config actually in force)
make test              # Run full test suite (667 tests)
make test-quick        # Quick test run (stop on first failure)
make lint-config       # Guard: block new os.getenv from bypassing app/config.py
make install           # Install dependencies
make hooks             # Install pre-commit hooks
make help              # List all targets
```

---

## Daily Workflow Reference

### Morning
```bash
.venv/Scripts/python.exe scripts/kalshi/daily_summary.py --save  # U2 (2026-04-30) — yesterday + open exposure + 7d context
make status                    # Check balance & positions
make settle                    # Settle overnight results
make report                    # Quick P&L summary
make risk                      # Check if limits breached
```

### Scanning
```bash
make scan-mlb                  # MLB today, exclude open, save
make scan-nba                  # NBA scan
make scan-futures              # All futures
make scan-all                  # Everything
```

Or with full control:
```bash
python scripts/scan.py sports --filter mlb --date today --exclude-open --save
python scripts/scan.py sports --filter nba
python scripts/scan.py futures --filter nba-futures
```

### Executing
```bash
python scripts/scan.py sports --filter mlb --execute --unit-size 1 --max-bets 10
python scripts/scan.py sports --filter mlb --execute --unit-size 1 --max-bets 5 --budget 10%
python scripts/scan.py sports --filter nba --execute --pick '1,3,5'
```

### Evening
```bash
make settle                    # Settle completed bets
make report                    # Detailed P&L
make reconcile                 # Compare local vs API
```

---

## Automation

See **[Automation Guide](../../../docs/setup/AUTOMATION_GUIDE.md)** for the full setup walkthrough.

### Windows Task Scheduler (Recommended)

```powershell
# Install morning execution + nightly settlement
python scripts/schedulers/automation/install_windows_task.py install execute
python scripts/schedulers/automation/install_windows_task.py install settle

# Or install all four tasks at once
python scripts/schedulers/automation/install_windows_task.py install all

# Check task status
python scripts/schedulers/automation/install_windows_task.py status

# Trigger a task immediately (test)
python scripts/schedulers/automation/install_windows_task.py run execute
```

Installer profiles (`install_windows_task.py`):

| Profile | Schedule | Description |
|---------|----------|-------------|
| `daily-summary` | 4:50 AM PT | Morning P&L digest (U2, 2026-04-30) — yesterday + open exposure + today pending + 7d context. Emailed at 5:00 AM PT |
| `scan` | 8:00 AM | Preview scan — saves report, no bets |
| `execute` | 8:00 AM | Scan + execute — places live orders |
| `settle` | 11:00 PM | Settle bets, update P&L |
| `next-day` | 9:00 PM | Scan + execute tomorrow's games |
| `calibration` | 2:00 AM, 1st of month | 30-day calibration report (R16) — Brier, calibration curve, prescriptive recommendations |

**What is actually registered** under `\Edge-Radar-MikesAILab\` differs from the installer profiles above — the live schedule has grown well past them. Read it from the machine rather than this table:

```powershell
Get-ScheduledTask -TaskPath "\Edge-Radar-MikesAILab\*" |
  ForEach-Object { $i = $_ | Get-ScheduledTaskInfo
    [PSCustomObject]@{ Task=$_.TaskName; State=[string]$_.State
                       LastRun=$i.LastRunTime; Result=$i.LastTaskResult; NextRun=$i.NextRunTime } } |
  Sort-Object LastRun -Descending | Format-Table -AutoSize
```

The live execution cadence is four Kalshi runs a day, each emailing its report as a second action (since 2026-09-23; `Daily-Polymarket-Execution` was removed 2026-09-29):

| Time (PT) | Task | Notes |
|---|---|---|
| 4:50 AM | `Daily-Summary` | emailed 5:00 AM |
| 5:05 AM | `All-Sports-SameDay-Execution` | `--date today` |
| 11:00 AM | `All-Sports-NoDateFilter-Midday-Execution` | no date filter — *can bet games several days out* |
| 2:00 PM | `All-Sports-SameDay-Late-Execution` | |
| 8:30 PM | `All-Sports-NextDay-Execution` | `--date tomorrow` |
| hourly :35 | `Hourly-Settle` | U1 (2026-07-20) |
| 11:30 PM | `Reconcile` | nightly drift check (`NightlySettle` retired 2026-09-23 — `Hourly-Settle` covers it) |
| weekly/monthly | `Backtest`, `Weekly-Analysis`, `Calibration`, `MonthlyCalibration`, `WeeklyAccountGraph` | |

`Weekly-Futures-Execution` has been live again since 2026-08-24 and emails its own report as a second action. `R8-Review` and `U2-Review` are registered with one-shot triggers whose start boundaries have passed — they have **never run and will never fire** until re-registered.

> **The three intraday Kalshi executes each pass `--budget 12%` — this is deliberate** (operator-confirmed 2026-07-23). Stale `.bat` headers had long described a de-escalating 12% → 8% → 5% ladder that was never implemented and is not wanted; the headers were corrected to match the flags. **Don't "fix" these back down to the ladder.** The shared ceiling is ~36% of bankroll per day in theory, but `--budget` is a per-batch cap and Gate 5 (`--exclude-open`) plus series dedup keep real deployment to a few dollars a day.

### Bat Scripts (Manual)

```bash
# Preview only (no bets)
scripts\schedulers\same_day_executions\same_day_scan.bat

# Scan + execute (places live orders)
scripts\schedulers\same_day_executions\same_day_execute.bat
```

Config: `--unit-size 1`, `--max-bets 5`, `--budget 12%`, `--date today`, `--exclude-open`, `--save`.

> `scripts/schedulers/*` is **gitignored** — the `.bat` files are local-only and won't appear in `git status` or diffs. Edits there don't propagate to a fresh clone. Only `scripts/schedulers/automation/*.py` is tracked.

### Per-Sport Scan-Only Scripts

```
scripts/schedulers/same_day_scans/     # Today's games by sport
scripts/schedulers/next_day_scans/     # Tomorrow's games by sport
```
