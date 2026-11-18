<h1 align="center">🗺️ Roadmap</h1>

<p align="center">
  <em>Open work on a live, real-money Kalshi system: execution correctness first, then measurement, risk controls, data quality, UX and features.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/now-after_public_release-F59E0B?style=for-the-badge" alt="Now: after public release">
  <img src="https://img.shields.io/badge/stage-public,_in_the_org_since_2026--09--10-2ea44f?style=for-the-badge" alt="Stage: public, in the org since 2026-09-10">
  <a href="README.md"><img src="https://img.shields.io/badge/↩-docs_home-6B7280?style=for-the-badge" alt="Back to docs"></a>
</p>

---

Worked by hand. This repo places real money, so no roadmap routine builds from it and the org PR
sweep never merges its PRs; the Edge-Radar upstream check only adds money-path findings here for
Mike. **Every item above `## After public release` is a release gate**, and all of them are ticked.
Ticking an item adds its entry to the [changelog](CHANGELOG.md) and updates any doc it made stale,
in the same commit. Shipped items, review findings, performance history and the reasoning behind
each item are in the changelog; the pre-cleanup roadmap is archived verbatim at the end of it, and
every item ID below resolves there.

Work in this order: **execution correctness, then measurement, then risk controls, then data
quality, then UX, then features.** Hold all sizing (`KELLY_FRACTION` <= 0.5, `UNIT_SIZE=1.00`)
until S15 says otherwise.

Markers: `- [ ]` open, `- [-]` claimed by a run in progress, `- [x]` done, `- [!]` blocked (the
reason follows on the line). `small` marks an item a check verifies; `🔒 Needs owner` marks one only
Mike can do. Each item keeps its ID in bold and its effort (XS to L) in italics at the end.

## 🧭 Phase 0: Build and live trading (done 2026-03-22)

Collapsed: the build, from the first scanners to live trading on 2026-03-22, is in the
[changelog](CHANGELOG.md), with the pre-cleanup roadmap archived verbatim at its end.

## 🚦 Public release

- [x] Repo public in the `ai-automation-tools` org, transferred from `michaelschecht/Edge-Radar` — done 2026-09-10: wave 3 of the org migration
- [x] Real dollar figures off the public repo's site: the account-growth graph stays local under the git-ignored `docs/my-documents/` — done 2026-09-07 (earlier snapshots remain in `master`'s history by decision)
- [x] Public page live at `https://edge-radar.ai-automation-tools.dev` — done 2026-10-04

## After public release

Nothing below blocks go-live.

### 🔎 Audit follow-ups, 2026-11-16

A full audit at `610b403` raised 53 items (`ER-01` to `ER-53`); the P0 and P1 ones are below in work
order, then each later one as it landed. Security and privacy detail stays in the owner's private audit report, not in public issues.
One item per PR, titled `fix(ER-xx): …`.

- [x] **ER-01** (P0) **Enforce human approval and a client-level hard cap before any live order.** A committed PreToolUse hook that blocks agent-run order commands in every permission mode, `.claude/settings.json` deny rules for `.env` and `keys/`, `disable-model-invocation` on the `edge-radar` skill, a `MAX_BET_SIZE` notional cap and a `data/KILL` kill switch inside `KalshiClient.create_order` (the switch also stops shard transfers), and the `scan.py --execute` help text no longer promises a confirmation. Done 2026-11-17; pinned by `tests/test_client_guards.py`.
- [x] **ER-02** (P0) **The ledger misses real fills.** Done 2026-11-17: the settler re-reads open resting/partial orders before settling (closes **X2**); janitor cancels keep a partly filled row open; an accepted order whose log write fails retries, then journals, and is never booked as an error. Pinned by `tests/test_ledger_fills.py`. `kalshi_settler.py audit-fills` checks closed rows (read-only). **Before S15:** let it run a week, then review `audit-fills` and correct the rows it names (🔒 owner approves ledger edits).
- [x] **ER-03** (P1) **Scan-cache replay (`--pick` / `--ticker --execute`) skips Gate 2, Gate 4.8 and the `MAX_BET_SIZE` re-clamp.** Done 2026-11-17: the replay loop drops rows past `MAX_OPEN_POSITIONS` or on a started game and clamps contracts to the current `MAX_BET_SIZE`; `--pick` now indexes the previewed menu, not the re-gated one. Pinned by `tests/test_replay_gates.py`. The single gate list (ER-19) has since replaced the hand-kept subset.
- [x] **ER-07** (P1) **Failed live-execute runs are silent.** Done 2026-11-17: execute wrappers log the scan to `logs/scan_*.log` with its exit code and `exit /b` it; the email action sends `[FAILED]` with the log tail and exits 1 when the scan failed or wrote no report. Pinned by `tests/test_render_report_email.py`. Also fixed `kalshi_executor.py status`, which had crashed on every call since B7 (2026-11-05). Tracking the wrappers themselves is ER-27.
- [x] **ER-08** (P1) **Back up the trade ledger and settlements.** Done 2026-11-17: `scripts/shared/backup_ledger.py` zips the ledger nightly (Reconcile action 2) with 30-day retention; restore steps and a quarterly drill in `data/history/README.md`. Pinned by `tests/test_backup_ledger.py`.
- [x] **ER-09** (P1) **Tool-restrict unattended agent sessions.** Done 2026-11-17: `betting_audit` goes through `agent_cli` with `Read,Grep,Glob`; `agent_command` raises without an allowlist unless `unrestricted=True` is passed. Pinned by `tests/test_agent_cli.py`, which also fails if any tracked script but `agent_cli.py` builds a `claude` argv.
- [x] **ER-04** (P1) **Contain the daily drift auto-fix** (what it may edit, which environment it runs in). Done 2026-11-17: `kalshi_client.py` off the editable list; reads scoped to the worktree; the analysis (web-capable) no longer reaches the fix prompt; tests and probe run with no `.env`, no credentials and `DRY_RUN=true`; the probe reads markets unsigned; the public PR carries a diff stat, not the session's text. Pinned by `tests/test_integration_drift.py`.
- [x] **ER-10** (P1) **Risk, eligibility and responsible-gambling notice.** Done 2026-11-17: a "Risk and eligibility" block under the README hero and in the site footer (whole-stake loss, one operator's sample, Kalshi age and location rules, 1-800-GAMBLER, not affiliated with Kalshi or The Odds API), linked from the hero; disclaimer text moved to `--fg-3` (4.5:1 or better in both themes); the two ROI lines in the gate cards tagged as one operator's sample. Pinned by `tests/test_site.py`.
- [x] **ER-11** (P1) **Halt and manual-run commands pointed at a Task Scheduler folder that no longer exists.** Every doc and the ops deck now name the current folder and put `DRY_RUN=true` first; closes **R24c**. Done 2026-11-17.
- [x] **ER-12** (P1) **Say LIVE or DRY RUN everywhere, and report what was placed, not what was requested.** Done 2026-11-17: `mode_banner()` (`LIVE · REAL MONEY · PROD`, `DRY RUN · nothing sent`, `DEMO · paper orders`, `PREVIEW · …`) titles the console table, opens the execution report and is appended to the email subject. Each order carries an outcome (placed, failed, blocked, not attempted, dry run, preview); reports and the run summary count those, and a live run that placed nothing says `0 placed`. The scan report's in-play column says `in play`, not `LIVE`.
- [ ] **ER-05** (P1) Kalshi key rotation, with the **H8** runbook and the **M3** key-type choice. *(effort S)* 🔒 Needs owner
- [ ] **ER-06** (P1) Public-repo data hygiene: stale branches and a history decision. *(effort S / L)* 🔒 Needs owner
- [x] **ER-22** (P2) **Report emails rendered raw HTML from report text.** Done 2026-11-17: the renderer escapes HTML (`html=False`); placeholders like `<TN>` now show instead of vanishing. Pinned by `tests/test_render_report_email.py`.
- [x] **ER-14** (P2) **`--budget 1%` meant 100% of bankroll.** Done 2026-11-17: a trailing `%` always means percent, a bare `1` is refused as ambiguous, the executor's duplicate parser is gone, and the executor, sports and futures `--budget` help texts match the code (a bare `15` is 15%, not $15; `prediction_scanner.py`'s waits for that file's lint cleanup). Pinned by `tests/test_executor_cli.py`.
- [x] **ER-17** (P2) **The Telegram bot could switch live trading on with one message.** Done 2026-11-17: the bot was dormant (no task, log last written April), so it is deleted, with its config and `.env.example` keys. Nothing tracked writes `DRY_RUN` to `.env` any more.
- [x] **ER-15** (P2) **Void and scalar settlements were booked as total losses.** Done 2026-11-17: `scalar` pays each YES contract the settlement `value` (NO gets the rest), anything else other than yes/no is booked as a refund, and `won` is `None` for both so `calibration_study` and the daily Brier skip them (`model_calibration.py` and `risk_check.py` still count them as losses; both predate black/flake8). Pinned by `tests/test_calculate_pnl_void.py`.
- [x] **ER-13** (P2) **Order placement idempotent and resting-order aware; one execute run per profile.** Done 2026-11-17: every POST carries a `client_order_id`; after a transport error the executor looks the order up by that id and books it if the venue has it (otherwise the UNKNOWN row now names the id); resting orders count for Gate 5 (duplicate ticker) and Gate 6 (per event); an execute run holds `.execute_<profile>.lock` from state gathering through placement (a second run waits up to 15 min, then fails). Not done: a pending ledger row written before the POST, for a process that dies mid-request. Pinned by `tests/test_order_idempotency.py`.
- [x] **ER-25** (P2) **Execute prompts previewed nothing and waited for nothing.** Done 2026-11-17: the nine prompts that place orders now run a sizing preview without `--execute`, wait for **go**, then place only the chosen rows (`--pick` for sports, which replays the cached preview; `--ticker` for futures and predictions, which don't cache). Pinned by `tests/test_prompts.py`.
- [x] **ER-19** (P2) **The gate chain was written three times and the copies drifted.** Done 2026-11-17: one ordered `GATES` list in `kalshi_executor.py` runs the fresh scan, the scan preview and the `--pick`/`--ticker` replay, which now checks every gate against current state and config. The test suite no longer reads the operator's `.env`. Not done: a frozen `RiskConfig` in place of the module globals. Pinned by `tests/test_gate_list.py`.
- [x] **ER-33** (P2) **Report emails didn't say what happened until opened, and clipped on phones.** Done 2026-11-17: subjects read `Edge-Radar | Same-Day | LIVE · 2 placed · 1 failed · $2.08 | Mon Nov 16` (no more one-thread-per-preset), a status banner and preheader open each email, wide tables stack into cards under 600px, report times show UTC · PT · ET, counts are pluralised and the footer meets contrast. Pinned by `tests/test_render_report_email.py` and `tests/test_report_writer.py`.
- [x] **ER-18** (P2) **Scripts failed to import on a fresh clone.** Done 2026-11-17: every entry point puts `scripts/shared` on `sys.path` itself, so no venv `.pth` file is needed. Pinned by `tests/test_fresh_clone_imports.py`.
- [x] **ER-21** (P2) **CI ran no lint or secret scan, and only one Python.** Done 2026-11-17: tests on 3.11 and 3.12, the pre-commit hooks on each PR's changed files, one required `ci` gate (see T3).
- [x] **ER-20** (P2) **Dependencies were unpinned.** Done 2026-11-17: hashed `requirements.txt` / `requirements-dev.txt` built by `make lock`, CI installs with `--require-hashes`, Actions pinned by SHA. Python is out of Dependabot, whose re-lock dropped the Windows-only pins; re-lock with `make lock`.
- [x] **ER-27** (P2) **The scheduled wrappers and the email sender were untracked.** Done 2026-11-17: the 15 task `.bat` wrappers and the hidden launcher are tracked (change them by PR), and `scripts/schedulers/automation/send_report_email.py` is the one send path (`--check` probes Resend). Not done: a weekly export of the task XML. Pinned by `tests/test_scheduler_wrappers.py`.
- [x] **ER-35, 37, 38, 40, 41, 43, 44, 46** (P3) **Money-path hardening.** Done 2026-11-17: exact demo-host check, read retries (never on order POSTs), paginated positions and orders, a `no_bankroll` reject at $0, dollar-first balances and null-safe accounting helpers, Gate 7 ignores error and dry-run rows, shard funding covers the fee, and the scan cache and `risk_check` are per wallet. Pinned by `tests/test_money_path_p3.py`.
- [x] **ER-28** (P2) **`logs/` grew without limit.** Done 2026-11-18: the nightly Reconcile runs `scripts/shared/prune_logs.py`, which deletes dated logs past 90 days and trims fixed-name logs over 5 MB. The stale `venv/` folder is gone. Not done: the shadow book is still one JSON file rewritten daily; split it into monthly JSONL if it gets slow. Pinned by `tests/test_prune_logs.py`.
- [x] **ER-26** (P2) **Dead AI tooling.** Done 2026-11-18: the four off-scope skills, both project agents (the stale `kalshi-bettor` and a generic writer) and the fictional agent roster are gone; the Kelly, scoring-rule and betting-theory notes moved to `skills/betting-logic-review/references/`; `/repo-review` is `/edge-radar-repo-review`; `docs/setup/mcp-servers.md` says no MCP is needed; memory is the project's auto-memory only. Owner: revoke the aX tokens and retire the user-scope coordination skill.
- [x] **ER-30** (P2) **Homepage accessibility.** Done 2026-11-18: Lighthouse accessibility 100 on desktop, mobile and the light theme (was 91 / 88 / 88). The command palette is a native `<dialog>` with a combobox and listbox; the Quick start tabs are a real tablist with arrow keys; text no longer uses `--fg-5`; sliders and search show focus; a Pause motion button stops the loops, and the radar stops off-screen. Pinned by `tests/test_site.py`.
- [ ] **Still open from the audit:** P2 ER-31, 32 and owner items ER-16, 24, 34; P3 ER-36, 39, 42, 45, 47 to 53. Smaller leftovers: a pending ledger row before each order POST (ER-13), one balance read per batch, a frozen `RiskConfig` (ER-19), Gate 1b in the AGENTS.md gate table and the site's gate grid together.

### 🩹 Money-path defects: fix next

- [ ] **B2** **Unmapped sports fall back to a 12.0 stdev** (`edge_detector.py:861, 1028`). This is latent while those sports only trade moneylines. Fail closed (`None`, no edge) and add the soccer-league and WNCAAB entries. *(effort S)*
- [ ] **M2** **Tennis markets are fetched but never scored outside Wimbledon.** `KALSHI_TO_ODDS_SPORT` maps `KXATPMATCH`/`KXWTAMATCH` only to `tennis_*_wimbledon`. Map tour-level Odds API keys per tournament, or drop tennis from the default scan deliberately. Surfaced by Integration-Drift-Check's "no fresh odds feed" line. *(effort S)*
- [ ] **M3** **Kalshi's web dialog now defaults new API keys to Ed25519**; `kalshi_client.py` signs RSA only. Document "choose RSA" in `docs/setup`, or add Ed25519 signing before the next key rotation. Confirmed 2026-10-05 at docs.kalshi.com/changelog: Ed25519 keys supported since 2026-09-24, web-app default since 2026-10-01, RSA still an option. *(effort S)*
- [x] **X2** **A `resting` trade row is never refreshed.** The settler skips `fill_status == "resting"` rows (no exposure at placement) and nothing re-reads them, so a limit that fills *after* the create-order response is an untracked position until it settles, and a venue-side cancel (`SETTLEMENT_BOUNDS_CANCEL`, 2026-10-01) leaves the row `resting` forever. Checked 2026-10-05: the 3 live rows in that state have zero fills at the venue, so no P&L was missed. Add a pre-settle pass that re-reads each open resting row's order (`fill_count_fp`, `status`) and promotes it to `filled`/`partial` or closes it as cancelled. Touches `kalshi_settler.py`; the executor comments at `_place_order_batch` that say "the settler will reconcile" are wrong until it does. *(effort S)* Done 2026-11-17 with ER-02.
- [ ] **K1** **Kalshi `GET /portfolio/balance` now has its own rate bucket: 1 request per second on Basic and Advanced tiers, no burst, `429` above it** (docs.kalshi.com/changelog, entry dated 2026-10-15). `get_balance()` and `get_shard_balance()` in `kalshi_client.py` are called from the executor, `shard_funding` (which re-reads the destination balance after each transfer), the settler, `doctor.py` and the daily summary. A batch that sizes, then funds, then re-reads in quick succession can trip the limit; a `429` on the re-read would look like a transfer that did not settle (fails closed, so orders get skipped). Audit the call sites for back-to-back reads, add a 1 s spacing or one cached read per batch, and make a `429` on a balance read retry rather than abort. Done when a mocked burst of balance reads never exceeds 1/s and a `429` is retried. Also note: since 2026-10-08 the Kalshi app/web no longer auto-moves capital between shards (our `shard_funding` is unaffected; it moves cash itself). *(effort S)*
- [ ] **K2** **Kalshi renamed the order-error status `market_closed` to `market_inactive`, and orders on a halted market now return it** (docs.kalshi.com/changelog, entry dated 2026-11-05). `venue_eligibility._TRANSIENT_PATTERNS` exempts only `market (is )?closed`, so the new code is not on the never-disable-a-venue list. It matches no structural pattern today, so nothing blocks, but the exemption is by omission, not by rule. Add `market (?:is )?inactive` to `_TRANSIENT_PATTERNS`, check how `kalshi_executor.py` and `kalshi_settler.py` treat a market `status` of `closed` vs `inactive`, and pin both in `tests/test_venue_eligibility.py`. Same entry: `no_sub_title` is deprecated in favour of `yes_sub_title`; `edge_detector.py:1369` already reads `yes_sub_title` first, so only the `tests/test_edge_detection.py:638` fixture still models it. Also 2026-11-12: the insufficient-shard-balance error `details` now say API orders are not funded automatically; `shard_funding` already moves cash itself, so no change expected. Done when `market_inactive` is asserted non-structural and the status handling is documented. *(effort XS)*
- [ ] **B6(a-c)** (a) The weather adjustment is applied after the side is chosen. (b) `CATEGORY_MAP` prefix shadowing sends a future `KXEPLSPREAD` to `game`. (c) Lower the log level of the "0 candidate events" warnings to DEBUG, and check why June markets still get scanned. *(effort S)*

### 📏 Measurement: CLV and strategy state (Priority 0a, phases 2-4)

S8 (CLV capture) shipped 2026-09-10 and S9 (the CLV section of `betting_analysis.py`) on 2026-09-29. Everything below reads from them.

- [ ] **S10** **`strategy_state.json`, protective only.** Per segment it records `last_settled_at`, `evidence_status`, `expires_after_days` and a default of dry-run when stale. It can demote a segment to dry-run, raise a floor or cap a stake, and nothing else. **Once it ships, remove the `.env` pilot floors** (`MIN_EDGE_THRESHOLD_NFL`, `_NCAAF`, `_MLB_SPREAD`). *(effort M)*
- [ ] **S6** **`risk_config_fingerprint()`**: hash the inputs the executor actually runs with (`.env`, `.bat` overrides, post-import module globals, strategy-state and eligibility-cache versions). Print it from `doctor.py` and the daily summary. This also closes S23 (balances quoted in docs going stale): `doctor.py` becomes the only place a balance is stated. *(effort S)*
- [ ] **S11** **Shadow diagnostics, log only:** `calibrated_edge` at lambda 0.16/0.25/0.40, `gate3_ceiling_would_reject` at 0.20/0.30, and a `legacy_gateset` label. Review firing rates after one full cycle. *(effort S)*
- [ ] **S12** **Six-line daily scoreboard:** eligibility, fingerprint, open exposure, 30d CLV with CI and coverage, segments in dry-run, and distance to each kill switch. *(effort S)*
- [ ] **S16** **Kill switches:** global negative CLV sends everything to dry-run, segment negative CLV sends that segment to dry-run, and fewer than 150 captures in 120 days sends everything to dry-run. Distances are computed mechanically for S12. *(effort S)*
- [ ] **S13** **Re-run `calibration_study.py` and `correlation_check.py` against CLV** once enough captures exist. Lambda's CI is currently [-0.04, +0.42]. *(effort S)*
- [ ] **S14** **Maker-fill A/B.** Every fill today is a taker fill, and fees cost 3.14pt of ROI. Assign by deterministic ticker hash, 25% maker / 75% taker, with sizing unchanged. Recompute edge at the limit price, and log scan, limit and fill prices plus fee role. *(effort M)*
- [ ] **S15** **Day-90 checkpoint, around 2026-12-09.** If coverage is below 60%, fix capture first. If the CI straddles zero, shrink the book or stop. If the lower bound is above 0 with 150 or more captures, raise `UNIT_SIZE` to $1.50, and only that. *(effort S)* 🔒 Needs owner

### 🎯 Model and gate follow-ups

- [ ] **B5** **Futures N-way devig is proportional**, which inflates longshot fair values. Switch to power or Shin devig, and skip incomplete books (raw implied total < 1.05). Affects Kalshi futures (`futures_edge.py`). *(effort M)*
- [ ] **T4** **Newly covered market types flood the book before they can be calibrated.** Options: a higher floor until first calibration, a per-shape batch cap, or a per-(sport, category) share cap. *(effort S-M)*
- [ ] **GT1** **Three unaligned NO-side knobs** (Gate 4.6, 4.6b and F4 damping). Check whether one edge-vs-price surface can reproduce all three before merging any of them. *(effort M)*
- [ ] **MLB** Re-check MLB totals after about 20 more settles under Gate 3.55. Align the totals `n_books` floor (3) with moneyline (5). Once rows carry `n_books`, re-run `book_width_check.py` in direct mode. *(effort S)*
- [ ] **B7b** Turn on `ODDS_API_REGIONS_EXECUTE=us,eu` in the live `.env` (B7 shipped the knob, default off; it doubles Odds API cost on `--execute` runs only). Once on, log `n_books` and re-check the R29/MLB book-count floors, which were tuned on a 9-book us-only pool. *(effort XS)* 🔒 Needs owner
- [ ] **R23b** On a 429, back off and retry the same key. Only mark a key exhausted on a 401. *(effort S)*
- [ ] **C9** Soccer total stdev is 1.5, but realized data shows 1.86. Change it only with a backtest, because soccer totals are currently profitable. *(effort S)*
- [ ] **C4b** Cap the edge for the `high` confidence label. Measure first, since High underperforms even at low edge. *(effort S)*

### ⏰ Scheduled checks and watch items

- [ ] **NCAA-BB** *(when: ~Nov 2026)* Run a live scan to confirm `KXNCAAMB*`/`KXNCAAWB*` markets resolve end to end. No code change expected.
- [ ] **R7-exp** *(when: ~30 more settles)* Is the live `MIN_MARKET_PRICE=0.10` longshot lane worth keeping? Judge it on CLV, not ROI.
- [ ] **GT3** *(when: once the gate has rejected real candidates)* Is `MAX_MARKET_PRICE=0.75` actually binding? It shipped without evidence.
- [ ] **S26b** *(when: one quota cycle)* Keep the daily `x-requests-used` readings per key to learn the Odds API reset model. Check the key that returns 401 (likely a typo in `ODDS_API_KEYS`).
- [ ] **S24** *(when: next occurrence)* MLS LAG-NE 09-05 produced no edge because `find_market_event` found 0 candidates, likely a team-name mapping miss.

### 🧹 Hygiene and tooling

- [ ] **S22** Report ROI as `net_pnl / (cost + fees)`. A total loss currently prints -107%. *(effort XS)*
- [x] **T3** CI: import smoke, lint, detect-secrets. Pytest on PRs and pushes to `master` shipped 2026-11-09 (#358). Done 2026-11-17 with ER-18/ER-21: tests on Python 3.11 and 3.12, the fresh-clone import test, and the pre-commit hooks (black, flake8, detect-secrets, the `os.getenv` guard) on each PR's changed files, all behind the one required `ci` check.
- [ ] **T1/T2** Mocked integration tests (scan→risk→execute, settle→report→CLV) plus deterministic API fixtures. *(effort M)*
- [x] **R24c** Make `install_windows_task.py status` reflect every live task under the owner's `\AI-Automation-Tools-Org-LocalApps\Edge-Radar-MikesAILab\` folder (the installer's own default is `Edge-Radar`, overridable with `--task-folder`), and replace the old folder path in `docs/task-schedules/README.md` in the same change. Done 2026-11-17 with ER-11: `status` also lists tasks it didn't install.
- [ ] **Templates for the rest of the scheduled jobs** *(Automation)* — **What:** installer profiles and Cronsole templates for `daily-summary`, `reconcile`, `clv-capture`, `backtest` and `weekly-analysis` (read-only), and `futures` (Mode defaults to `preview`, like execute). **Done when:** `tests/test_cronsole_registry.py` passes with one template per profile, and the homepage's Schedule section lists them. Open question: which of these jobs may go public. *(effort S)* 🔒 Needs owner
- [ ] **GT2** Add one reference table of the 8 sizing-cap steps near `size_order`. *(effort XS)*
- [ ] **H7** Move `BOOK_WEIGHTS` into config (pruned to arriving keys in B7). *(effort S)*
- [ ] **H8** Write a runbook for rotating the Kalshi RSA key. *(effort XS)*
- [ ] **H2 / H3** ~~Split `requirements.txt` into core, dev and research.~~ Core/dev split done 2026-11-17 with ER-20 (hashed `requirements.txt` + `requirements-dev.txt`); nothing needs a research set yet. Still open: separate runtime state from the source tree. *(effort S)*
- [ ] **Q6** Package `scripts/` and retire the `sys.path` hacks. *(effort L)*
- [ ] **R19** Complete `FUTURES_ALIASES` for NBA/NHL/MLB. See the archive for the rest of the scope. *(effort M)*
- [x] `small` **One risk-gate count everywhere (21)** *(Docs)* — done 2026-11-18 (ER-29): every doc says 21 and both gate tables list all 21; `tests/test_doc_accuracy.py` fails on a stray count or a missing row.
- [ ] `small` **Link ROADMAP from the homepage's resources** *(Site)* — `site/index.html` links the CHANGELOG, README and three docs, not `docs/ROADMAP.md`. **Done when:** `tests/test_site.py` pins the link. *(effort XS)*
- [x] `small` **Security headers on the public page** *(Site)* — done 2026-11-18 (ER-23): `site/vercel.json` sends a CSP (own origin plus consent.js and Google Fonts, `frame-ancestors 'self'`, `object-src 'none'`), `nosniff`, `Referrer-Policy` and `Permissions-Policy`, and caches the favicon and diagram for a day. `tests/test_site.py` fails if the page loads a script or stylesheet from an origin the CSP doesn't list. consent.js gets no SRI: it is the org's one shared copy and changes upstream.
- [x] **About text: Kalshi only** *(Metadata)* — the GitHub About no longer names Polymarket, removed 2026-09-29. Done 2026-11-13 by the owner.

### 💤 Dormant until prediction markets are re-enabled

`ALLOW_PREDICTION_BETS=false` (Gate 4.7) blocks all of these today. If it is ever flipped, **C10c must land first.**

- [ ] **R25b** Add TTLs to the prediction-module caches (crypto 1h, weather 6h, spx 5min, mentions/companies 24h). *(effort M)*
- [ ] **R25c** Rebuild the crypto model with tests, then port the same pattern to the others. *(effort L)*
- [ ] **C10c** Replace `edge * 20` with `min(edge / 0.01, 10)` in all 7 prediction scanners, as part of R25c. *(effort S)*
- [ ] **M1-M4** Crypto ensemble, SPX vol model, weather calibration, mentions seasonality. Gated on R25b and R25c. *(effort L)*

### 🔭 Later

No committed date.

- [ ] **Sports data:** bullpen availability, injury impact scoring, wind direction vs stadium, umpire tendencies, platoon splits.
- [ ] **UX:** interactive pick mode (U3), and a single `scan.py session` command (U4).
- [ ] **Service/web track (A2-A9):** service layer, then DB, then FastAPI plus idempotent execution, then job runner, locks and secrets, then a UI. No web surface exists today.

---

<p align="center">
  <a href="README.md">← Docs home</a> ·
  <a href="CHANGELOG.md">Changelog →</a>
</p>
