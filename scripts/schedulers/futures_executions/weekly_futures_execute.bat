@echo off
REM ============================================================================
REM  Weekly Futures Execute -- Championship / Outright Winners
REM
REM  Scans all supported futures series (NFL Super Bowl, NBA Finals, NHL Stanley
REM  Cup, MLB World Series, NCAAB MOP, Golf majors) and EXECUTES the top picks
REM  ranked by composite score. Most series are seasonal -- offseason series
REM  (no Odds API outright data) are skipped automatically. Golf only prices the
REM  4 majors during their play weeks.
REM
REM  Recommended run time: Saturday 9:00 AM PST (12:00 PM ET) -- weekly. Outright
REM  lines are posted and sharp; golf majors (Thu-Sun) are mid-tournament.
REM
REM  Sizing, caps and dates: the flags on the scan command below are the only copy (ER-27).
REM  All risk gates enforced (composite >= 6.0, MIN_MARKET_PRICE floor, NO-favorite
REM  guard, Kelly sizing, MAX_BET_SIZE cap, per-event cap, duplicate/series dedup).
REM  Report saved to: reports\Futures\schedulers
REM
REM  WARNING: This script places live orders. Verify DRY_RUN setting in .env.
REM ============================================================================

cd /d "%~dp0..\..\.."

REM ER-07: scan output + exit code go to logs\scan_weekly_futures.log for the email action.
set PYTHONIOENCODING=utf-8

echo ============================================================
echo  Edge-Radar Weekly Futures EXECUTE
echo  %date% %time%
echo ============================================================
echo.

echo --- Portfolio Status (Before) ---
.venv\Scripts\python.exe scripts\kalshi\kalshi_executor.py status
echo.

echo --- Scanning and Executing Futures ---
echo ===== %date% %time% >> logs\scan_weekly_futures.log
.venv\Scripts\python.exe scripts\scan.py futures --unit-size 1 --max-bets 3 --min-bets 1 --budget 10%% --exclude-open --save --report-dir "reports\Futures\schedulers" --execute >> logs\scan_weekly_futures.log 2>&1
set RC=%ERRORLEVEL%
echo exit code %RC% >> logs\scan_weekly_futures.log
echo.

echo --- Portfolio Status (After) ---
.venv\Scripts\python.exe scripts\kalshi\kalshi_executor.py status
echo.

echo ============================================================
echo  Futures execution complete. Run 'make status' to verify positions.
echo ============================================================

exit /b %RC%
