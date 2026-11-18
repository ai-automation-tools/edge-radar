@echo off
REM ============================================================================
REM  Weekly Performance Analysis Report
REM  Generates the 7-day betting_analysis report using the /edge-radar-analysis skill's
REM  underlying script. Headline, by-sport, by-category, by-side, edge buckets,
REM  confidence, market price, calibration, longshots, streaks, daily P&L, trade ledger.
REM
REM  Recommended run time: Sun 11:45 PM PST (after NightlySettle at 11 PM + Reconcile at 11:30 PM)
REM  Output: reports\Performance\betting_analysis_YYYY-MM-DD_7d.md
REM          reports\Maintenance\betting-audit\betting_audit_<date>.md
REM
REM  2026-10-27: runs the weekly betting audit first (every sport, read-only,
REM  Claude analysis only when flagged). Action 2's email opens with its flags.
REM ============================================================================

cd /d "%~dp0..\..\.."

echo ============================================================
echo  Edge-Radar Weekly Performance Analysis
echo  %date% %time%
echo ============================================================

.venv\Scripts\python.exe scripts\backtest\betting_audit.py --save --analyze auto >> logs\betting_audit.log 2>&1
.venv\Scripts\python.exe scripts\kalshi\betting_analysis.py --days 7 --save
