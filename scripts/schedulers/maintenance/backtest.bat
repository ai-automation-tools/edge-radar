@echo off
REM ============================================================================
REM  Weekly Backtest Report
REM  Equity curve, max drawdown, Sharpe, strategy simulation, dimensional breakdowns
REM  Recommended run time: Sun 7:30 PM PST (10:30 PM ET), after calibration
REM ============================================================================

cd /d "%~dp0..\..\.."

echo ============================================================
echo  Edge-Radar Weekly Backtest
echo  %date% %time%
echo ============================================================

.venv\Scripts\python.exe scripts\backtest\backtester.py --simulate --save
