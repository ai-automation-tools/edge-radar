@echo off
REM ============================================================================
REM  Same-Day Execute (Late) -- All Sports
REM
REM  Daily 2:00 PM PT variant of same_day_execute.bat. Catches late-breaking news
REM  on today's evening games: NBA/NHL pre-game scratches, goalie confirmations,
REM  weather updates, sharp-money line moves on tonight's slate.
REM
REM  Sizing, caps and dates: the flags on the scan command below are the only copy (ER-27).
REM  This is the third bite at the same-day apple (after 5:05 AM SameDay +
REM  11:00 AM Midday NoDateFilter). Gate 5 (--exclude-open) prevents re-betting
REM  markets already held.
REM
REM  NOTE (2026-07-23): this header previously claimed "Max bets: 4 | Budget: 5%%",
REM  describing a de-escalating ladder across the day (12%% -> 8%% -> 5%%). That
REM  ladder was never implemented and is NOT wanted -- 12%% on all three intraday
REM  runs is deliberate (operator-confirmed 2026-07-23). Header corrected to match
REM  the command. Do not "restore" the ladder.
REM
REM  The three intraday runs therefore share a ~36%% of-bankroll daily ceiling, not
REM  ~25%%. In practice it is nowhere near binding: --budget is a per-batch cap, and
REM  Gate 5 (--exclude-open) plus series dedup keep actual daily deployment to a
REM  few dollars against a ~$89 bankroll.
REM
REM  Report saved to: reports\Sports\schedulers\same-day-late-executions
REM
REM  WARNING: This script places live orders. Verify DRY_RUN setting in .env.
REM ============================================================================

cd /d "%~dp0..\..\.."

REM ER-07: scan output + exit code go to logs\scan_same_day_late.log for the email action.
set PYTHONIOENCODING=utf-8

echo ============================================================
echo  Edge-Radar Same-Day LATE EXECUTE
echo  %date% %time%
echo ============================================================
echo.

echo --- Portfolio Status (Before) ---
.venv\Scripts\python.exe scripts\kalshi\kalshi_executor.py status
echo.

echo --- Scanning and Executing ---
echo ===== %date% %time% >> logs\scan_same_day_late.log
.venv\Scripts\python.exe scripts\scan.py sports --unit-size 1 --max-bets 5 --min-bets 1 --budget 12%% --date today --exclude-open --save --report-dir "reports\Sports\schedulers\same-day-late-executions" --execute >> logs\scan_same_day_late.log 2>&1
set RC=%ERRORLEVEL%
echo exit code %RC% >> logs\scan_same_day_late.log
echo.

echo --- Portfolio Status (After) ---
.venv\Scripts\python.exe scripts\kalshi\kalshi_executor.py status
echo.

echo ============================================================
echo  Execution complete. Run 'make status' to verify positions.
echo ============================================================

exit /b %RC%
