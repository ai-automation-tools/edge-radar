@echo off
REM ============================================================================
REM  Weekly Calibration Report
REM  Brier score, calibration curve, dimension breakdowns + C8 stdev recalibration
REM  Recommended run time: Sun 7:00 PM PST (10:00 PM ET)
REM
REM  2026-07-31: --days 7 -> 30. The 7-day window silently disabled the C8
REM  stdev loop. save_calibration_stdevs() receives the DAY-FILTERED list and
REM  needs _MIN_CALIB_SAMPLES=20 settled bets per (sport, category); only ~22
REM  bets settle in a 7-day window across ALL sports, so no pair ever reached
REM  the bar. Every weekly run skipped every sport and wrote the hardcoded
REM  defaults straight back -- the cache was byte-identical to the defaults for
REM  as long as it has existed. At --days 30 MLB totals goes 17 -> 28 settled
REM  and the loop actually calibrates (3.45 -> 4.005 on the first real run).
REM  The report section still reads as a trailing window; 30d matches the
REM  MIN_EDGE / calibration review cadence used everywhere else.
REM ============================================================================

cd /d "%~dp0..\..\.."

echo ============================================================
echo  Edge-Radar Weekly Calibration
echo  %date% %time%
echo ============================================================

.venv\Scripts\python.exe scripts\kalshi\model_calibration.py --days 30 --save
