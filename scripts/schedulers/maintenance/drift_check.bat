@echo off
REM ============================================================================
REM  Edge-Radar - Integration-Drift-Check (daily 4:15 AM PT)
REM
REM  M1 (CHANGELOG 2026-10-03): Kalshi reworded NFL rules ("Pro Football") and
REM  the scanner silently stopped scoring 13 of 14 NFL games for ~2 weeks.
REM  integration_drift.py measures, per series, whether fetched markets actually
REM  parse and pair with an odds event. Deterministic, Kalshi GETs only, zero
REM  Odds API quota (cached odds). On WARN/FAIL -- and every Monday -- it runs a
REM  tool-restricted, READ-ONLY `claude -p` analysis and appends it to the report.
REM  Never edits code or .env, never places orders.
REM
REM  Action 2 of the task emails the report (render_report_email.py drift-check).
REM  Output: reports\Maintenance\drift\drift_<date>.md, logs\drift_check.log
REM  Exit: 0 on any probe verdict (the verdict is in the email); 1 only if the
REM  probe itself crashed.
REM ============================================================================

cd /d "%~dp0..\..\.."

echo ==== %date% %time% ==== >> logs\drift_check.log
.venv\Scripts\python.exe scripts\kalshi\integration_drift.py --save --analyze auto --autofix >> logs\drift_check.log 2>&1
if %ERRORLEVEL% EQU 1 exit /b 1
exit /b 0
