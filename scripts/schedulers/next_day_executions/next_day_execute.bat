@echo off
REM ============================================================================
REM  Next-Day Execute -- All Sports
REM
REM  Scans NFL, NBA, NHL, MLB together for tomorrow's games and EXECUTES the
REM  top picks ranked by composite score across all sports.
REM
REM  Note: Tomorrow's markets may not all be posted yet. For maximum coverage,
REM  prefer the same-day scripts run at 8 AM ET instead. Use this script when
REM  you want to lock in early lines the night before (recommended 9 PM ET).
REM
REM  Sizing, caps and dates: the flags on the scan command below are the only copy (ER-27).
REM  Report saved to: reports\Sports\schedulers\next-day-executions
REM
REM  WARNING: This script places live orders. Verify DRY_RUN setting in .env.
REM ============================================================================

cd /d "%~dp0..\..\.."

REM ER-07: scan output + exit code go to logs\scan_next_day.log for the email action.
set PYTHONIOENCODING=utf-8

echo ============================================================
echo  Edge-Radar Next-Day EXECUTE
echo  %date% %time%
echo ============================================================
echo.

echo --- Portfolio Status (Before) ---
.venv\Scripts\python.exe scripts\kalshi\kalshi_executor.py status
echo.

echo --- Scanning and Executing ---
echo ===== %date% %time% >> logs\scan_next_day.log
.venv\Scripts\python.exe scripts\scan.py sports --unit-size 1 --max-bets 5 --min-bets 1 --budget 12%% --date tomorrow --exclude-open --save --report-dir "reports\Sports\schedulers\next-day-executions" --execute >> logs\scan_next_day.log 2>&1
set RC=%ERRORLEVEL%
echo exit code %RC% >> logs\scan_next_day.log
echo.

echo --- Portfolio Status (After) ---
.venv\Scripts\python.exe scripts\kalshi\kalshi_executor.py status
echo.

echo ============================================================
echo  Execution complete. Run 'make status' to verify positions.
echo ============================================================

exit /b %RC%
