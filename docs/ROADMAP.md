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

### 🩹 Money-path defects: fix next

- [ ] **B2** **Unmapped sports fall back to a 12.0 stdev** (`edge_detector.py:861, 1028`). This is latent while those sports only trade moneylines. Fail closed (`None`, no edge) and add the soccer-league and WNCAAB entries. *(effort S)*
- [ ] **M2** **Tennis markets are fetched but never scored outside Wimbledon.** `KALSHI_TO_ODDS_SPORT` maps `KXATPMATCH`/`KXWTAMATCH` only to `tennis_*_wimbledon`. Map tour-level Odds API keys per tournament, or drop tennis from the default scan deliberately. Surfaced by Integration-Drift-Check's "no fresh odds feed" line. *(effort S)*
- [ ] **M3** **Kalshi's web dialog now defaults new API keys to Ed25519**; `kalshi_client.py` signs RSA only. Document "choose RSA" in `docs/setup`, or add Ed25519 signing before the next key rotation. Confirmed 2026-10-05 at docs.kalshi.com/changelog: Ed25519 keys supported since 2026-09-24, web-app default since 2026-10-01, RSA still an option. *(effort S)*
- [ ] **X2** **A `resting` trade row is never refreshed.** The settler skips `fill_status == "resting"` rows (no exposure at placement) and nothing re-reads them, so a limit that fills *after* the create-order response is an untracked position until it settles, and a venue-side cancel (`SETTLEMENT_BOUNDS_CANCEL`, 2026-10-01) leaves the row `resting` forever. Checked 2026-10-05: the 3 live rows in that state have zero fills at the venue, so no P&L was missed. Add a pre-settle pass that re-reads each open resting row's order (`fill_count_fp`, `status`) and promotes it to `filled`/`partial` or closes it as cancelled. Touches `kalshi_settler.py`; the executor comments at `_place_order_batch` that say "the settler will reconcile" are wrong until it does. *(effort S)*
- [ ] **K1** **Kalshi `GET /portfolio/balance` now has its own rate bucket: 1 request per second on Basic and Advanced tiers, no burst, `429` above it** (docs.kalshi.com/changelog, entry dated 2026-10-15). `get_balance()` and `get_shard_balance()` in `kalshi_client.py` are called from the executor, `shard_funding` (which re-reads the destination balance after each transfer), the settler, `doctor.py` and the daily summary. A batch that sizes, then funds, then re-reads in quick succession can trip the limit; a `429` on the re-read would look like a transfer that did not settle (fails closed, so orders get skipped). Audit the call sites for back-to-back reads, add a 1 s spacing or one cached read per batch, and make a `429` on a balance read retry rather than abort. Done when a mocked burst of balance reads never exceeds 1/s and a `429` is retried. Also note: since 2026-10-08 the Kalshi app/web no longer auto-moves capital between shards (our `shard_funding` is unaffected; it moves cash itself). *(effort S)*
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
- [ ] **T3** CI: import smoke, lint, detect-secrets. **(2026-11-11)** pytest on PRs and pushes to `master` shipped 2026-11-09 (#358, `.github/workflows/ci.yml`); the rest is still open. *(effort S)*
- [ ] **T1/T2** Mocked integration tests (scan→risk→execute, settle→report→CLV) plus deterministic API fixtures. *(effort M)*
- [ ] **R24c** Make `install_windows_task.py status` reflect every live task under the owner's `\AI-Automation-Tools-Org-LocalApps\Edge-Radar-MikesAILab\` folder (the installer's own default is `Edge-Radar`, overridable with `--task-folder`), and replace the old `\AI-Projects\Edge-Radar-MikesAILab\` path in `docs/task-schedules/README.md` in the same change. *(effort S)*
- [ ] **Templates for the rest of the scheduled jobs** *(Automation)* — **What:** installer profiles and Cronsole templates for `daily-summary`, `reconcile`, `clv-capture`, `backtest` and `weekly-analysis` (read-only), and `futures` (Mode defaults to `preview`, like execute). **Done when:** `tests/test_cronsole_registry.py` passes with one template per profile, and the homepage's Schedule section lists them. Open question: which of these jobs may go public. *(effort S)* 🔒 Needs owner
- [ ] **GT2** Add one reference table of the 8 sizing-cap steps near `size_order`. *(effort XS)*
- [ ] **H7** Move `BOOK_WEIGHTS` into config (pruned to arriving keys in B7). *(effort S)*
- [ ] **H8** Write a runbook for rotating the Kalshi RSA key. *(effort XS)*
- [ ] **H2 / H3** Split `requirements.txt` into core, dev and research. Separate runtime state from the source tree. *(effort S)*
- [ ] **Q6** Package `scripts/` and retire the `sys.path` hacks. *(effort L)*
- [ ] **R19** Complete `FUTURES_ALIASES` for NBA/NHL/MLB. See the archive for the rest of the scope. *(effort M)*
- [ ] `small` **One risk-gate count everywhere (21)** *(Docs)* — `docs/setup/ARCHITECTURE.md` says 18 (badge and pipeline table) and `skills/edge-radar/SKILL.md` says fifteen, while the README says 21. **Done when:** every count matches the gates the risk check actually runs. *(effort XS)*
- [ ] `small` **Link ROADMAP from the homepage's resources** *(Site)* — `site/index.html` links the CHANGELOG, README and three docs, not `docs/ROADMAP.md`. **Done when:** `tests/test_site.py` pins the link. *(effort XS)*
- [ ] `small` **Security headers on the public page** *(Site)* — the Vercel page sends HSTS only. A `vercel.json` for the site sends `nosniff`, a CSP that allows the registry fetch and the diagram iframe, and `frame-ancestors 'self'`. **Done when:** `curl -sI https://edge-radar.ai-automation-tools.dev/` shows all three and the Schedule section still loads. *(effort XS)*
- [ ] **About text: Kalshi only** *(Metadata)* — the GitHub About still names Polymarket, removed 2026-09-29. 🔒 Needs owner

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
