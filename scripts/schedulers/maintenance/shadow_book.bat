@echo off
REM ============================================================================
REM  Edge-Radar - S21b shadow book (NCAAF)
REM
REM  The exit ramp for the S21 NCAAF freeze. A freeze stops orders, so it also
REM  stops the settlements that would ever justify lifting it -- NFL escaped
REM  that only because 19 positions were already in flight when S1 landed.
REM  NCAAF was frozen holding nothing, so without this its settled count is
REM  pinned at 11 forever, permanently under nfl_week1_review's bar of 20.
REM
REM  PLACES NO ORDERS AND RISKS NO MONEY. `collect` calls the scanner and
REM  writes rows to data\history\shadow_book.json; `settle` calls get_market()
REM  read-only. Neither touches .env, the trade log, or the executor, and the
REM  freeze stays fully in force throughout -- these rows are scored, never bet.
REM
REM  It taps UPSTREAM of the risk gates on purpose: last_scan.json is written
REM  post-gate, so at NCAAF's 1.0 floor it holds nothing. scan_all_markets()
REM  applies only the GLOBAL min-edge, never the per-sport min_edge_for(), so
REM  what gets logged is what the MODEL said while the gates remain the thing
REM  under judgement.
REM
REM  settle runs BEFORE collect: it closes out yesterday's finals before the
REM  day's new lines are added. Both are idempotent -- collect keeps the first
REM  sighting of a (ticker, side) and settle only queries rows still open.
REM
REM  Read it with:
REM    python scripts\backtest\shadow_book.py review --sport ncaaf --save
REM
REM  Output: logs\shadow_book.log (appended).
REM ============================================================================

cd /d "%~dp0..\..\.."

.venv\Scripts\python.exe scripts\backtest\shadow_book.py settle  >> logs\shadow_book.log 2>&1
.venv\Scripts\python.exe scripts\backtest\shadow_book.py collect --filter ncaafb >> logs\shadow_book.log 2>&1
REM 2026-09-27: MLB spreads, pre-gate. They went 0-9 at the 0.03 floor and now
REM sit behind MIN_EDGE_THRESHOLD_MLB_SPREAD=0.08; this records every strike the
REM model scores so the floor can be judged on evidence, not on 9 selected bets.
REM   python scripts\backtest\shadow_book.py review --sport mlb --save
.venv\Scripts\python.exe scripts\backtest\shadow_book.py collect --filter KXMLBSPREAD >> logs\shadow_book.log 2>&1
REM 2026-10-26: NHL spreads (switched off) and NCAAB spreads (0.08 pilot), pre-gate.
REM Both showed the over-priced-tail pattern. See docs\my-documents\repo-reviews\2026-10-26.
REM   python scripts\backtest\shadow_book.py review --sport nhl --save
REM   python scripts\backtest\shadow_book.py review --sport ncaab --save
.venv\Scripts\python.exe scripts\backtest\shadow_book.py collect --filter KXNHLSPREAD >> logs\shadow_book.log 2>&1
.venv\Scripts\python.exe scripts\backtest\shadow_book.py collect --filter KXNCAAMBSPREAD >> logs\shadow_book.log 2>&1
REM 2026-10-27: European soccer (pilot 0.08, spreads off). Never scored before -- the
REM series prefixes were wrong -- so it has no settled history to judge the pilot by.
REM   python scripts\backtest\shadow_book.py review --sport epl --save  (or laliga/ucl/seriea/bundesliga/ligue1)
.venv\Scripts\python.exe scripts\backtest\shadow_book.py collect --filter eurosoccer >> logs\shadow_book.log 2>&1
REM 2026-10-27: MLS totals, pre-gate, to fit the soccer total stdev (1.5 in code, 1.86
REM realised over 74 WC matches). Every candidate the model likes is an Under 4.5/5.5.
.venv\Scripts\python.exe scripts\backtest\shadow_book.py collect --filter KXMLSTOTAL >> logs\shadow_book.log 2>&1
REM 2026-11-03: NFL spreads + totals, pre-gate. 25 of 45 live NFL spread bets
REM were YES "wins by over 7.5" -- suspected key-number (3/7) blind spot in the
REM normal margin model. This gives the S18 Brier pair on every strike.
REM   python scripts\backtest\shadow_book.py review --sport nfl --save
.venv\Scripts\python.exe scripts\backtest\shadow_book.py collect --filter KXNFLSPREAD >> logs\shadow_book.log 2>&1
.venv\Scripts\python.exe scripts\backtest\shadow_book.py collect --filter KXNFLTOTAL >> logs\shadow_book.log 2>&1
