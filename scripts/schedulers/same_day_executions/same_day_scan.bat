@echo off
REM ============================================================================
REM  Same-Day Scan (Preview Only) -- All Sports
REM
REM  Scans NFL, NBA, NHL, MLB together for today's games. Ranks the best
REM  opportunities across all sports and shows the top 10. Saves report but
REM  does NOT place any bets.
REM
REM  Recommended run time: 8 AM ET (all markets posted, sportsbook lines sharp,
REM  Kalshi lag window open)
REM
REM  Sizing, caps and dates: the flags on the scan command below are the only copy (ER-27).
REM  Report saved to: reports\Sports\schedulers\same-day-executions
REM ============================================================================

cd /d "%~dp0..\..\.."

echo ============================================================
echo  Edge-Radar Same-Day Scan (Preview Only)
echo  %date% %time%
echo ============================================================
echo.

.venv\Scripts\python.exe scripts\scan.py sports --unit-size 1 --max-bets 7 --min-bets 1 --budget 12%% --date today --exclude-open --save --report-dir "reports\Sports\schedulers\same-day-executions"

echo.
echo ============================================================
echo  Scan complete. Review report before running execute script.
echo ============================================================
