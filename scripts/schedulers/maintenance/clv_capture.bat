@echo off
REM ============================================================================
REM  Edge-Radar - S8 CLV closing-book capture
REM
REM  Samples the market book shortly BEFORE each open position's event starts,
REM  and writes it to the trade row. This is the only moment the closing line
REM  exists: by settlement it is gone, which is why the previous approach
REM  (deriving it from the settlement-time snapshot) produced 0 CLV across 426
REM  settlements for five months.
REM
REM  READ-ONLY at the venue. It calls get_market() and never places, cancels or
REM  modifies an order. Safe to run at any frequency.
REM
REM  Runs every 5 minutes. A pass with nothing due costs one trade-log read and
REM  ZERO API calls, so the idle cost is negligible; the frequency is what buys
REM  capture coverage, and coverage is what makes the mean CLV trustworthy
REM  (S9 prints n_captured/n_settled beside every figure for that reason).
REM
REM  Safe alongside the execute tasks: the venue reads happen outside the M2
REM  cross-process lock, and the captures are re-applied by trade_id against a
REM  fresh read taken inside it, so a row appended mid-run is never clobbered.
REM
REM  Output: logs\clv_capture.log (appended - one line per capture).
REM ============================================================================

cd /d "%~dp0..\..\.."

.venv\Scripts\python.exe scripts\kalshi\clv_capture.py >> logs\clv_capture.log 2>&1
