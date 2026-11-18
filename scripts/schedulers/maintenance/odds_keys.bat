@echo off
REM ============================================================================
REM  Weekly Odds API Key Probe
REM  Refreshes data/cache/odds_api_quota.json with live x-requests-remaining
REM  Recommended run time: Sun 6:00 PM PST (before Calibration at 7 PM)
REM
REM  Costs 1 request per key (14 keys == 14 requests/week == 56/month, well
REM  under a single key's 500 monthly allowance).
REM
REM  2026-09-09: added as the belt-and-braces half of the quota-cache fix.
REM  The root-cause fix is the _ZERO_TTL_HOURS expiry in scripts/shared/
REM  odds_api.py -- a cached zero used to be believed forever, so once a key
REM  drained it was never contacted again and any quota reset went
REM  unobserved. 12 of 14 keys read 0 while 5154 requests were actually
REM  available. The TTL re-probes stale zeros on its own; this task is what
REM  catches a key going bad (401/revoked) BEFORE a scan needs it, and keeps
REM  the whole pool's numbers honest rather than only the keys in active use.
REM ============================================================================

cd /d "%~dp0..\..\.."

echo ============================================================
echo  Edge-Radar Weekly Odds Key Probe
echo  %date% %time%
echo ============================================================

.venv\Scripts\python.exe scripts\shared\check_odds_keys.py --live
