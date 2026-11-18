@echo off
REM ============================================================================
REM  Daily Summary Report
REM  Generates the morning P&L digest: yesterday's settled P&L + per-sport
REM  breakdown, currently open exposure, today's pending positions, optional
REM  live Kalshi balance, 7-day rolling context.
REM
REM  Recommended run time: Daily 4:50 AM PST
REM    (after the 11:00 PM PST NightlySettle so yesterday's bets are settled,
REM     before the 5:05 AM PST same-day Execute so the digest stays focused on
REM     yesterday rather than getting mixed with today's new fills)
REM
REM  Output: reports\Performance\daily_summary_YYYY-MM-DD.md
REM ============================================================================

cd /d "%~dp0..\..\.."

echo ============================================================
echo  Edge-Radar Daily Summary
echo  %date% %time%
echo ============================================================

.venv\Scripts\python.exe scripts\kalshi\daily_summary.py --save
