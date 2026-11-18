@echo off
REM ============================================================================
REM  Daily Reconciliation
REM  Compares local trade log against Kalshi API
REM  Recommended run time: 8:30 PM PST (11:30 PM ET), after settle
REM ============================================================================

cd /d "%~dp0..\..\.."

echo ============================================================
echo  Edge-Radar Reconcile
echo  %date% %time%
echo ============================================================

.venv\Scripts\python.exe scripts\kalshi\kalshi_settler.py reconcile
