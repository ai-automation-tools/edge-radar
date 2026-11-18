@echo off
REM ============================================================================
REM  Same-Day Execute -- All Sports
REM
REM  Scans NFL, NBA, NHL, MLB together for today's games and EXECUTES the
REM  top picks ranked by composite score across all sports.
REM
REM  Recommended run time: 8 AM ET (all markets posted, sportsbook lines sharp,
REM  Kalshi lag window open)
REM
REM  Sizing, caps and dates: the flags on the scan command below are the only copy (ER-27).
REM  Report saved to: reports\Sports\schedulers\same-day-executions
REM
REM  WARNING: This script places live orders. Verify DRY_RUN setting in .env.
REM ============================================================================

cd /d "%~dp0..\..\.."

REM ER-07: scan output + exit code go to logs\scan_same_day.log for the email action.
set PYTHONIOENCODING=utf-8

echo ============================================================
echo  Edge-Radar Same-Day EXECUTE
echo  %date% %time%
echo ============================================================
echo.

echo --- Portfolio Status (Before) ---
.venv\Scripts\python.exe scripts\kalshi\kalshi_executor.py status
echo.

echo --- Scanning and Executing ---
echo ===== %date% %time% >> logs\scan_same_day.log
.venv\Scripts\python.exe scripts\scan.py sports --unit-size 1 --max-bets 5 --min-bets 1 --budget 12%% --date today --exclude-open --save --report-dir "reports\Sports\schedulers\same-day-executions" --execute >> logs\scan_same_day.log 2>&1
set RC=%ERRORLEVEL%
echo exit code %RC% >> logs\scan_same_day.log
echo.

echo --- Portfolio Status (After) ---
.venv\Scripts\python.exe scripts\kalshi\kalshi_executor.py status
echo.

echo ============================================================
echo  Execution complete. Run 'make status' to verify positions.
echo ============================================================

exit /b %RC%
