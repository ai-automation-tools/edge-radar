@echo off
REM ============================================================================
REM  No Date Filter Execute (Midday) -- All Sports
REM
REM  Daily midday variant of no_date_filter_execution.bat. Scheduled 11:00 AM PT
REM  to capture intraday edge that the 5:05 AM same-day run misses: confirmed
REM  MLB starters, NBA/NHL morning-skate news, mid-morning sharp-money moves.
REM
REM  Sizing, caps and dates: the flags on the scan command below are the only copy (ER-27).
REM  (header said 8%% until 2026-07-23; 12%% on every intraday run is deliberate --
REM  operator-confirmed. Do not lower this to match the old header text.)
REM  Lower max-bets / budget than the Mon-Thu 5:20 AM run since this is the
REM  second (or third on Mon/Thu) wide-net scan of the day. Gate 5 (--exclude-open)
REM  prevents re-betting markets already held.
REM
REM  Report saved to: reports\Sports\schedulers\no-date-filter-midday-executions
REM
REM  WARNING: This script places live orders. Verify DRY_RUN setting in .env.
REM ============================================================================

cd /d "%~dp0..\..\.."

REM ER-07: scan output + exit code go to logs\scan_nodatefilter_midday.log for the email action.
set PYTHONIOENCODING=utf-8

echo ============================================================
echo  Edge-Radar No Date Filter MIDDAY EXECUTE
echo  %date% %time%
echo ============================================================
echo.

echo --- Portfolio Status (Before) ---
.venv\Scripts\python.exe scripts\kalshi\kalshi_executor.py status
echo.

echo --- Scanning and Executing ---
echo ===== %date% %time% >> logs\scan_nodatefilter_midday.log
.venv\Scripts\python.exe scripts\scan.py sports --unit-size 1 --max-bets 5 --min-bets 1 --budget 12%% --exclude-open --save --report-dir "reports\Sports\schedulers\no-date-filter-midday-executions" --execute >> logs\scan_nodatefilter_midday.log 2>&1
set RC=%ERRORLEVEL%
echo exit code %RC% >> logs\scan_nodatefilter_midday.log
echo.

echo --- Portfolio Status (After) ---
.venv\Scripts\python.exe scripts\kalshi\kalshi_executor.py status
echo.

echo ============================================================
echo  Execution complete. Run 'make status' to verify positions.
echo ============================================================

exit /b %RC%
