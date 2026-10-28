# Changelog

---

## 2026-10-27 -- European soccer series fixed; rest/sharp/pitcher data scoped per sport and date

From the [2026-10-27 betting-logic review](my-documents/repo-reviews/2026-10-27-betting-logic-review.md).

- **Scanner** The six European leagues (EPL, La Liga, UCL, Serie A, Bundesliga, Ligue 1) were
  wired as bare `KX<LEAGUE>` series. Kalshi's are `KX<LEAGUE>GAME/SPREAD/TOTAL`, so every scan
  fetched **zero** markets for them, all season, and reported a quiet slate. Now wired as 18
  series (1,003 open markets today, 100% parsed and odds-matched), mapped to `soccer` for
  stdevs, the discrete-margin spread guard and the floor. New filter `eurosoccer`.
- **`.env`** `MIN_EDGE_THRESHOLD_SOCCER=0.08` (cold-start pilot, zero history) and
  `MIN_EDGE_THRESHOLD_SOCCER_SPREAD=1.0` (the alt-spread model already switched off for MLS and WC).
  At those floors nothing on today's slate clears Gate 3.
- **Model** `scan_all_markets` keyed NBA/NHL rest data by team abbreviation alone, so it reached
  every sport sharing one and the last date fetched overwrote the others. MLS totals took the
  NBA's **+1.5 back-to-back stdev on a 1.5-goal base** (361 log lines in October). NFL, NCAAF
  and MLB totals were also hit, including the Penguins' rest on MLB KC@PIT (placed 09-19). Rest is
  now keyed by (sport, date, team). MLB pitchers are keyed by (date, team) for the same reason.
- **Model** Sharp-money signals were one dict across sports, matched by substring ("ne" in
  "Tennessee"). They are now per sport and matched exactly. Effect: confidence on totals only.
- **Drift check** A sport whose every series is empty while its odds feed lists games is now a
  WARN, not a "No open markets" context line. That line is where the dead European prefixes sat.
- **Shadow book** (`shadow_book.bat`, local) collects `eurosoccer` and `KXMLSTOTAL` pre-gate.
  MLS totals NO: 11 wins vs 15.7 model / 13.7 market (−33%). Every candidate the model scores is
  an Under 4.5/5.5, consistent with the soccer total stdev of 1.5 being too narrow (1.86 measured).
  An approximate backtest on the 50 gated rows was inconclusive, so the stdev is unchanged (S21c).
- **Automation** The `Weekly-Analysis` task (Sun 11:45 PM) now runs a weekly betting audit first:
  `scripts/backtest/betting_audit.py` runs the review battery mechanically across every sport.
  It reports model-vs-market-vs-outcome z per series and side, one-way pre-gate candidate pools,
  rest data on non-NBA/NHL markets, order health, dark sports from the drift probe, and stdevs
  never fitted. When flagged, a `claude -p` pass restricted to `Read,Grep,Glob` appends an
  analysis. The `weekly-analysis` email opens with its flags, so it is one Sunday email. `/betting-logic-review`
  now starts from it and gained B9 (dead series prefixes), B10 (context scoping) and B11 (one-way
  candidates). `Shadow-Book-NCAAF` time limit raised from 20 to 45 min for the wider collection.
- **Open** The first audit run flags **NCAAF totals: 93% of 130 pre-gate candidates are Unders**
  (14d). The shadow Brier pair favours the market, 0.1399 vs model 0.1433 (n=860). Same shape as
  soccer totals. Not acted on yet.
- **Diagram** re-pinned to `4e69e1f`. The `edge_detector.py` ranges moved by +27 to +77 lines, and the
  "ESPN + league stats" range now covers the per-sport rest/pitcher/sharp caches. No label changes.

## 2026-10-26 -- Discrete-sport spreads priced only at a quoted line; NHL spreads off; NCAAB spread pilot; pick labels

From the [2026-10-26 betting-logic review](my-documents/repo-reviews/2026-10-26-betting-logic-review.md).
Live window since 09-28: 51 settled, −25.4% ROI, 19 wins against 24.3 model / 19.8 market.

- **Model** `consensus_spread_prob` refuses a strike that no book quotes for NHL, MLB and
  soccer (`_DISCRETE_MARGIN_SPORTS`). Books hang ±1.5; extrapolating a normal tail to Kalshi's
  2.5/3.5 over-priced big covers: **91 YES alt-spreads across MLB/NHL/WC/MLS, 14 wins against
  21.3 model / 14.6 market** (2 vs 7.0 since 08-01). This is the shared cause behind the WC,
  MLB and MLS switch-offs. Continuous sports (football, basketball) still extrapolate.
- **`.env`** `MIN_EDGE_THRESHOLD_NHL_SPREAD=1.0` (off). NHL spread YES 0-5; on 10-24 it produced the
  window's two largest edges and contract counts, both lost. The guard above now limits NHL to
  the ±1.5 line, so this key can come out once the shadow book supports it.
- **`.env`** `MIN_EDGE_THRESHOLD_NCAAB_SPREAD=0.08`, a pilot set before tip-off. Lifetime NCAAB
  spread YES: 8 wins against 14.4 model / 5.0 market (z −2.5), the largest miss in the book.
  The stdev 12.1 is the R2 fallback and has never been fitted.
- **Shadow book** (`shadow_book.bat`, local) now also collects `KXNHLSPREAD` and `KXNCAAMBSPREAD`
  pre-gate.
- **Digest** `daily_summary.load_one_sided_series()`: flags a series bet ≥90% one way over 60 days
  that trails its own model by ≥1.5σ. Series that are switched off are skipped. Replayed on
  history, it would have flagged MLB spreads (0 of 9, z −1.9) before the 10-03 manual switch-off.
- **Display** `ticker_display`: a ticker suffix N means "over N−0.5", but labels printed N+0.5,
  one point off on every spread and total ("Miami −4.5" for over 3.5, "Over 6.5" for 5.5).
  Pricing was never affected, since the model reads `floor_strike`. NO spread labels now name
  the other side of the line (`UTA +1.5`, not `Boston +2.5`). Team names now resolve within
  the ticker's own sport, so NFL `DAL` no longer shows as "Mavs".
- **Diagram** re-pinned to `b8a384b`. The `edge_detector.py` ranges moved by +12/+29 lines, and
  the "Fair probability" node's spread range now covers the new quoted-line guard. This also
  clears the earlier un-rebuilt JSON drift.

## 2026-10-26 -- README gate table and filter counts match the code

- **Docs** `README.md`: the risk-gate table listed 13 gates with old defaults (a $0.06 price floor among
  them). It now lists all 21 gates from the `AGENTS.md` gate table, without hard-coded thresholds; the
  defaults stay in `AGENTS.md`. Badge and intro say 21 gates.
- **Docs** Filter counts across `README.md` (27), `site/index.html` (30), `AGENTS.md` (30),
  `SCRIPTS_REFERENCE.md` and `ARCHITECTURE.md` (27) now say 31: the game entries in
  `edge_detector.FILTER_SHORTCUTS` (39 keys, 8 of them futures). Flagged by Org Upkeep.

## 2026-10-22 -- `betting-logic-review` frontmatter parses as YAML

- **Fix** `skills/betting-logic-review/SKILL.md`: the `argument-hint` value is now quoted. Unquoted, a value
  starting with `[` is read as a YAML list, and the text after `]` made the whole frontmatter invalid, so
  strict parsers (js-yaml, PyYAML) rejected the skill. Promptbook's My Library refresh failed on it.

## 2026-10-22 -- Org folder layout: AGENTS.md and lowercase evidence folders

- **Docs** `CLAUDE.md` is now `AGENTS.md`, the file every coding agent reads; the rules, gates and
  limits moved with it unchanged. The new `CLAUDE.md` imports it with `@AGENTS.md` and keeps only the
  Claude Code notes: the `.claude/memory/` index and the `.claude/skills/` junctions.
- **Docs** Live pointers follow it: `tests/test_site.py` now reads the gates, limits and commands
  from `AGENTS.md`; the GitHub links on `site/index.html` and `.claude/html/index.html` (same
  `#execution-gates` / `#dry-run` anchors); the docs, prompts, skills and `/repo-review` /
  `/sync-docs` references. Code comments on the money path and historical docs still say
  `CLAUDE.md`, which imports `AGENTS.md`.
- **Docs** `docs/longshot/fork-evidence-window/Futures/` and `Sports/` → `futures/` and `sports/`
  (org layout standard: lowercase folders; GitHub paths are case-sensitive).

---

## 2026-10-19 -- Data-flow diagram moves from the README to the homepage

- The README no longer shows the betting data-flow diagram; the [homepage](https://edge-radar.ai-automation-tools.dev/#pipeline) does, under
  *Pipeline*, linking to the interactive version. `docs/diagrams/` is still its source.
- `scripts/diagrams/build_betting_diagram.py` copies the HTML and PNG into `site/diagram/` (Vercel
  deploys only `site/`), and `--check` flags a copy that differs from the build.

## 2026-10-19 -- Upstream check: K1 queued

- **Roadmap** K1 added: Kalshi gave `GET /portfolio/balance` its own 1 req/s bucket (changelog 2026-10-15). Money path, so queued, not fixed.
- **Docs** `docs/UPSTREAMS.md` last-checked dates moved to 2026-10-19 for every row read this run. The Odds API now marks bookmaker-level `last_update` deprecated; `_bookmaker_last_update` already falls back to market level (S19), so no code change.

---

## 2026-10-19 -- Roadmap on the lab's roadmap standard

- **Docs** `docs/ROADMAP.md` reshaped to the lab roadmap standard: centred header and badges, a
  collapsed Phase 0, a ticked `🚦 Public release` gate list (org transfer 2026-09-10, dollar
  figures off the public site 2026-09-07, public page 2026-10-04), and every open item as a
  checkbox line under `## After public release`, in the old section order with IDs and effort
  kept. B7 is marked `- [!]` (blocked on the operator quota decision it already named). No items
  added or dropped. `/repo-review` and `/sync-docs` now point at `docs/ROADMAP.md` and describe
  the checkbox shape.

---

## 2026-10-18 -- README diagram: code-pinned Archify data flow

The README's pipeline image (`.claude/images/diagrams/data_flow/high_level_data_flow/`, a
hand-drawn Mermaid render) still showed the Polymarket node removed on 2026-09-29, and nothing
told anyone when it went stale. It is replaced by `docs/diagrams/betting-data-flow.*`.

- **Source of truth is one JSON.** 18 nodes and 20 flows from Kalshi markets to settlement and
  recalibration, each citing the code it describes by line range at a pinned commit (`8daeb154`).
  Archify renders it to an interactive HTML (each box links to its lines on GitHub) and the PNG
  the README shows.
- **Drift is detected, not remembered.** A build records the git blob of every cited file in
  `betting-data-flow.sources.lock.json`. `scripts/diagrams/build_betting_diagram.py --check`
  exits 1 when any of them changed; the `betting-diagram-drift` pre-commit hook prints the same
  warning on commits touching `scripts/` or `app/` without blocking. CLAUDE.md now says to update
  the diagram in the same PR. Steps in `docs/diagrams/README.md`.
- Generated files are excluded from the whitespace and secrets hooks, since their receipts pin
  exact bytes. The old `high_level_data_flow/` folder is deleted; the other diagrams under
  `.claude/images/diagrams/` are unchanged.

---

## 2026-10-13 -- Tests: 8 passed only with the live `.env`

The phone-layout PR (#333) reported 8 failures "on unmodified master in this environment". They
were real, and only showed in a checkout with no `.env`: three test files silently depended on the
operator's live values instead of setting their own.

- `MIN_MARKET_PRICE`: live 0.10, code default 0.12. `test_exposure_gate`'s trim tests (10c) and
  `test_opposing_side_gate`'s real SF leg (11c) were rejected by Gate 3.5 before reaching the gate
  under test. `test_without_the_held_position_it_passes_6b` was passing vacuously for the same reason.
- `KELLY_FRACTION`: live 0.5, code default 0.25. At 0.25 `test_no_side_ceiling`'s orders sit on the
  flat floor on both sides, so the damping cannot show (2 vs 2).
- Each test now pins the value it needs, the same opt-in pattern as `test_limit_price.py` and the
  conftest neutralisers. Suite: 1232 passed with `.env`, 1229 passed + 3 skipped without.

---

## 2026-10-13 -- Both static pages: phone layout pass

`site/index.html` and `.claude/html/index.html` get one `@media (max-width: 600px)` block each;
nothing outside it changes, so desktop renders identically (computed style and geometry of every
element diffed at 1400x900 before and after).

- **Ops deck schedule:** at 390px the table showed only `#` and the task name; Time and "What it
  does" sat off-screen behind a sideways scroll. Each row now stacks as a card: number, task and
  time on top, the description below.
- **Gate lab:** Side and Confidence sat side by side and clipped the `high` segment; they stack.
- **Touch targets:** chips, segments, presets, terminal tabs, copy buttons, the theme toggle, the
  menu and GitHub buttons, footer links and slider thumbs grow to 36-40px; timeline dots get a
  larger tap area without moving.
- **Inputs:** search fields, the edge-floor select and the command palette go to 16px so iOS
  Safari stops zooming in on focus.

## 2026-10-12 -- MLS spreads off; janitor-cancelled orders close in the trade log

**MLS spreads OFF** (`MIN_EDGE_THRESHOLD_MLS_SPREAD=1.0` in the live `.env`, operator override).
Same shape as the MLB-spread shutdown on 10-03, milder:

- **One-sided book:** 39 of 40 lifetime bets are YES on "wins by 2+".
- **Since July: 3-20, -$4.75.** Hit rate 13% against a 14.2c average price and a 20.2% model
  probability, so outcomes track the market, not the model. Market Brier 0.104 vs model 0.114
  since 08-01.
- **The lifetime +$40 is April-May**, mostly two hits at 6-7c (+$14.80, +$20.59).
- The open COLMIN-MIN2 position is held, not exited.

**Janitor cancellations now close the trade-log row.** Both janitors (R4 stale, S23c live)
cancelled at the venue but never wrote back, so a zero-fill row stayed `fill_status: "resting"`
forever. `trade_log.mark_cancelled()` now runs after each janitor and sets
`fill_status: "cancelled"`, `closed_at`, `net_pnl: 0`. A row with any fill is left alone,
because its filled part is real exposure the settler still reconciles. Three stale live rows
(07-16, 07-31, 08-16) were closed by hand: the venue returns 404 for their orders and holds no
position on them. Nine dry-run `longshot` rows that are also marked `resting` were left as they
are, because they never reached the venue.

## 2026-10-12 -- Task installer stops turning on catch-up

`install_windows_task.py` no longer sets `StartWhenAvailable` on the tasks it creates. Its
`_enable_catch_up` step and `tests/test_install_windows_task.py`, which only covered that step,
are gone. Since 2026-09-30 no timed task on Mike's machine catches up (only the two backups are
exempt), and missed runs are re-run by hand. This repo's docs still told every task to turn the
flag on, and the 2026-10-12 task audit found `Integration-Drift-Check` running with it on.

- **Execute tasks:** a missed run is now skipped instead of firing on wake against whatever
  slate is live then.
- **One-shot tasks:** a missed date is silent again (`267011`, see `docs/task-schedules/README.md`),
  so check that a dated review actually ran.
- The "every task needs it" warning in `docs/task-schedules/README.md` is rewritten to match.

## 2026-10-05 -- Both static pages: light/dark theme switch

`.claude/html/index.html` (`edge-radar.mikesailab.com`) and `site/index.html`
(`edge-radar.ai-automation-tools.dev`) get the org's two-button Sun/Moon switch at the right end
of the topbar, the same control as Cronsole's compact toolbar toggle. Both pages read and write
the same key, so one choice carries across.

- **Default stays dark.** A visitor who never clicks sees the page exactly as before. The choice
  is stored in `localStorage` under `edge-radar.theme` and applied as a `light`/`dark` class on
  `<html>` by a pre-paint script in `<head>`, so there is no flash; `meta theme-color` follows.
- **The light palette** is a `:root.light` token block plus a short override list for the
  hard-coded dark surfaces (topbar, next-fire card, code boxes, timeline, palette, toast). The
  accents step down to their -700 shades for text contrast on `#fafafa`: emerald 5.2:1, sky 5.7,
  amber 4.8, rose 6.1; the dimmest text tier (`--fg-5` `#6b6b73`) is 5.1:1, 4.8 on `#f4f4f5`.
- The inline series colours (`--c`, amber-400 and friends, set in the markup and in `SCHED`'s
  `KIND` map) stay as they are. Every label that mixed them toward white now mixes through
  `--cm`/`--cm-to`, which are unset in dark (falling back to the old 80-85% toward `#fff`) and
  50% toward black in light. Timeline markers darken to 65% in light so they clear 3:1.
- `site/` also themes what only it renders: the org source bar, the gate lab (range tracks,
  segmented controls, readouts, verdict and gate chips), the gate grid, the terminal, and the
  radar canvas, which picks a per-theme palette in JS (`RADAR`, `BLIP_LIGHT`) and redraws on a
  `themechange` event when reduced motion has stopped its animation loop.
- In the ops deck, the CSS rules for components it does not render (radar, gate lab, gate grid,
  terminal) were left unthemed; they are live only in `site/`.

---

## 2026-10-05 -- U1 reviewed: the shard is read per market, so Basketball moving to shard 3 needed no code

The 2026-10-05 upstream check (PR #315) queued three Kalshi changelog items against the money
path as ROADMAP **U1**. All three were checked against code and against the live venue; two are
closed here, the residue of the third is re-filed narrowly as **X2**.

- **(a) Basketball on shard 3, Commodities on shard 2 (Kalshi 2026-09-10).** Not a defect.
  `kalshi_executor._shard_for()` reads `exchange_index` off each market payload before the
  shard-funding step, so no sport-to-shard table exists on the money path to go stale. Verified
  live: `KXNBAGAME-26OCT11CHIDEN-DEN` reports `exchange_index: 3`, MLB 3, NFL and NHL 0, BTC 2,
  and `GET /exchange/status` now describes shard 2 as "Crypto & Commodities" and shard 3 as
  "Tennis, Baseball, Basketball". What *was* stale: `doctor.py` printed the 08-24 names from a
  hardcoded map, and four docs quoted the 08-24 mapping as current. `shard_funding.shard_names()`
  now reads the venue's list (new `KalshiClient.get_exchange_status()`), with
  `FALLBACK_SHARD_NAMES` only for a client that cannot answer; doctor enumerates the balance
  split from that list rather than from a fixed set of four. Display only -- the executor never
  consults it. Tests in `tests/test_shard_funding.py` pin that the venue's description wins and
  that an NBA ticker is funded on the shard its market reports.
- **(b) Sub-cent and half-cent price levels (Kalshi 2026-07-23, 09-03).** Not a defect, latent
  by construction. The money path already reads only the `*_dollars` fields (`edge_detector`,
  `clv_capture`, `fees`) and sends limits as four-decimal dollar strings; the one integer-cent
  step is `price_cents = ceil(price * 100)` in sizing (F2), which lands on a whole cent. A whole
  cent lies on every published grid (`price_ranges.step` is 0.01 on every sports market probed,
  and 0.005 or 0.001 elsewhere both divide 0.01), so an order is never off-tick; on a sub-cent
  book it pays at most the fraction of a cent up to the next whole one. The fee model is
  `rate * p * (1-p)` in dollars and is step-independent. Nothing to change.
- **(c) `SETTLEMENT_BOUNDS_CANCEL` (Kalshi 2026-10-01).** No money impact, but it exposed a
  pre-existing gap. A venue-cancelled resting order just drops out of `get_orders(status=
  "resting")`, so Gate 2b's resting exposure, the R4 janitor and S23c all see it correctly as
  gone. The trade-log row, however, stays `fill_status: "resting"` forever, because the settler
  skips resting rows and nothing re-reads them -- and the same gap means a limit that fills
  *after* the create-order response is an untracked position until settlement. Checked the
  three live rows in that state (07-16 MLS total, 07-31 MLB total, 08-16 NFL spread): zero
  fills at the venue on all three, so no P&L has been missed. Filed as **X2** with the fix
  shape: a pre-settle pass that re-reads each open resting row's order and promotes or closes it.

**Rule:** *when a venue publishes a category-to-shard mapping, read it; never carry it in
code.* The executor got this right from X1; the display path and the docs did not, and the
docs drifted within three weeks.

---

## 2026-10-05 -- Site redesign: public page and ops deck in the org design vocabulary

Both static pages were rebuilt to match the 2026-10-05 redesign of `ai-automation-tools.dev`
(its `docs/REDESIGN.md`): same `#060606` ground, dot grid, one hero glow, zinc surfaces,
Inter + JetBrains Mono, spotlight cards with a cursor-tracked ring, a sticky topbar with a
scroll-spy indicator, a terminal quick start with a bash/pwsh toggle, a `⌘K` palette, and
`prefers-reduced-motion` fallbacks for every animation. The accent is emerald `#34d399`, the
colour the org page assigns Edge-Radar. **No Tailwind CDN**: each page is one file with its
stylesheet inline, and the only external resources are fonts and the shared `consent.js`.

- **`site/index.html`** (public, `edge-radar.ai-automation-tools.dev`, Vercel). Keeps the org
  source bar at the very top and the optional hero repo button. New: a canvas **radar sweep**
  over twelve *illustrative* candidate markets (radius = ask price, colour = what the static
  gates would say; hover reads the row, click loads it); a **gate lab** that computes claimed
  edge, the per-contract fee `ceil(0.07·p·(1−p))`, net edge, the Gate 3 floor-plus-fee, a
  ¼-Kelly stake and the verdict of every static gate (3, 3.05, 3.5, 3.55, 4.5, 4.6, 4.6b)
  from CLAUDE.md's **code defaults**; a filterable, searchable grid of all **21 gates** with
  the one-line reason each exists, plus the two checks outside the chain (venue eligibility,
  fails closed; the 10% hard stop); the seven-stage stepper; coverage cards; a four-tab
  terminal whose commands are the README's Quick Start and CLAUDE.md's Common Commands,
  nothing guessed. The footer says plainly that the samples are illustrative and the lab is
  not a live book.
- **`.claude/html/index.html`** (personal, `edge-radar.mikesailab.com`, GitHub Pages). No
  source bar (that convention is for `*.ai-automation-tools.dev`), `noindex`. New: a
  **next-fire clock** in `America/Los_Angeles` that reads the schedule and names the next task,
  its time and a countdown, with the rest of today listed under it; a **24-hour timeline** with
  a `now` marker, weekly tasks drawn hollow and dimmed when they do not run today, hover for
  the row and click to jump to it; the **full 16-task inventory** from
  `docs/task-schedules/README.md` (the old page showed only the five wager tasks) with filter
  chips, search, a per-row copy of the `schtasks /run` trigger, the manual-trigger block and
  the halting instructions. No balance or P&L figures anywhere, per the 2026-09-07 decision.
- **`tests/test_site.py`** pins what drifts by hand: no Tailwind, consent wiring, the source
  bar on the public page only, `GATES` equal to CLAUDE.md's execution-gate rows in order, the
  gate-lab constants equal to the Risk Limits defaults, every terminal command present in the
  README or CLAUDE.md, and `SCHED` equal to the task-schedules README's 16 rows with matching
  times. Both pages were rendered headlessly at 1280px and 390px with no script errors and no
  horizontal overflow.
- Deploy paths are unchanged: `site/` is the Vercel root; `.claude/html/**` on `master` fires
  the Pages workflow. Edit `site/` for the public page, `.claude/html/` for the personal one.

---

## 2026-10-04 -- Public site for edge-radar.ai-automation-tools.dev

Every public org repo with a front end gets a `<repo>.ai-automation-tools.dev` page, and the
org landing page only had a footnote pointing at `edge-radar.mikesailab.com`. That page is the
personal ops deck (scheduler times, task paths), and it already holds this repo's one GitHub
Pages slot, so the public page could not be a second Pages site.

- **`site/`** -- new static page (Tailwind CDN, no build), deployed by a **Vercel** project
  with root directory `site/`, the same host as Edge Spectrum. Reuses the ops page's How It
  Works diagram and pipeline strip; drops schedulers, run commands and anything about the
  live bankroll; adds Coverage and Quick Start.
- Carries the org **source bar** (full-bleed, top of page, "View source") and the shared
  `consent.js`, per the `ai-automation-tools.github.io` README.
- `.claude/html/` and `edge-radar.mikesailab.com` are unchanged. Edit `site/` for the public
  page, `.claude/html/` for the personal one.
- Fixed two stale links on the ops page too: the skill lives at `skills/edge-radar/` (the
  `.claude/skills` junction is gitignored) and the scripts reference at `docs/scripts/`.

---

## 2026-10-03 -- M1: NFL/NBA team matching broken by Kalshi "Pro Football" wording; Integration-Drift-Check

Kalshi now words NFL rules "... in the DEN Broncos vs SF 49ers **Pro Football**
game" (NBA: "Pro Basketball") and NFL spread subtitles "DEN Broncos wins by over
7.5 points". Two failures, both silent:

- `extract_event_teams()` expected `professional|NFL|...` after the home team, so
  **every NFL and NBA moneyline** returned None. Spreads/totals fell to the
  fallback regex, which captured `'SF 49ers Pro Football'` as the home team.
- `extract_team_from_market()` returned the whole spread subtitle. Other sports
  only matched on the tier-1 first-word city ("tampa"); NFL's abbreviated "DEN"
  cannot hit that.

Net effect: tomorrow's slate scanned **33 of 650** NFL markets, all DEN@SF, which
matched only because `sf` sits in `TEAM_ALIASES`. The trade log shows the drought:
5 NFL bets since 09-01, the last (09-29) also DEN@SF. **"No opportunities" was
a matching failure, not an absence of edge** -- the same silent-zero shape as
the S21c `--filter` bug. Fix: accept `pro\b` in the rules regex and strip
" wins by over/more than ..." from subtitles. Post-fix: 650/650 markets, all 14
games. Regression tests in `TestProLeagueRulesWording`. The first post-fix
next-day run placed ARI -8.5 YES x4 @ 28c.

### Integration-Drift-Check: a detector for the M1 failure class

New scheduled task (daily 4:15 AM PT, 16th in `\AI-Projects\Edge-Radar-MikesAILab\`)
running `scripts/kalshi/integration_drift.py --save --analyze auto`. Per game/spread/total
series it measures schema fields, team/strike parse rate, suspect league filler in team
names, odds-event match rate (cached odds only -- zero Odds API quota; a miss counts only
when the feed carries both teams that day) and new `rules_primary` wording against
`data/cache/drift_baseline.json`. New wording is auto-accepted only while its series stays
healthy. On WARN/FAIL, and every Monday, it runs a headless `claude -p` restricted to
`Read,Grep,Glob,WebFetch,WebSearch` (no `--dangerously-skip-permissions`) that diagnoses
flags and reads Kalshi's API changelog; the analysis is appended to the report, which
action 2 emails (`render_report_email.py drift-check`). Read-only throughout.

**Auto-fix stage** (`scripts/kalshi/drift_autofix.py`, `--autofix`): on WARN/FAIL days a
second Claude session edits a throwaway worktree of `origin/mike_desktop`, and **a PR exists
only for a verified code change**. No diff means no PR. Paths outside parsing/matching code and
tests, a deletion, fewer collected tests, a failing suite (one retry), or a probe that is not
better on the fixed tree each mean rejected, no PR. A pass pushes `drift-fix/<date>` and opens a
**draft** into `mike_desktop`. It never merges and can't edit the probe that grades it. An open
`drift-fix/*` PR suppresses new attempts. Verification runs through `--in-tree`, because
`edge_radar.pth` puts the main checkout's script dirs first on `sys.path`, so a plain `pytest` in
the worktree would test the wrong code and pass.

Its first run found two more silent zeros, both fixed here:
- **Boxing had never been scored.** Rules read "... Murney vs Buczynskyj **boxing match**";
  neither `extract_event_teams` pattern accepted it. Parse 0% -> 100%.
- **College totals garbled the home team** as "teams collectively score more than 84.5
  points in the Eastern Washington" (`_clean_team` only stripped "teams in the ").
  Pairing survived only when the school shared a word with the Odds API name, so
  "Fresno St." failed. KXNCAAFTOTAL odds match 41% -> 92%.

Open, from the first Claude pass (ROADMAP **M2**, **M3**): ATP/WTA markets outside
Wimbledon have no odds feed and are never scored; Kalshi's web dialog now creates Ed25519
API keys by default, which `kalshi_client.py` (RSA-only) cannot sign with.

## 2026-10-03 -- B7 edge ceiling; MLB spreads off; NHL totals floor; relative stdev sweep

### B7: Gate 3.05 rejects claimed edges above `MAX_EDGE` (default 0.50)

`KXNCAAFSPREAD-26SEP26WCUETSU-ETSU15` (2026-09-26) claimed **80.7%** edge: model
0.937 against a 13c market, 7 books. It passed every gate, was sized to 44
contracts ($5.72, 5.4% of bankroll) and won $37.93 -- the whole two-week P&L
(+$34.74 on $38; about -$3 without it). An edge that size is a matching or sign
bug, not a signal, and nothing rejected it. Ex-ETSU, settled edges >= 0.30 made
+$4.72 on $38 over 40 bets. The scan preview labels it `edge-hi`; `MAX_EDGE=1.0`
disables.

### MLB alternate spreads off (live `.env`, `MIN_EDGE_THRESHOLD_MLB_SPREAD=1.0`)

Lifetime **0-9, -$8.68**, every bet YES on "wins by over N.5" -- the S21
one-sided-book diagnostic. The 0.08 floor of 09-27 still passed SD3 on 10-01.
Shadow book (all postseason, from 09-28): 37/37 rows YES, model above market on
every one, **2 of 22** settled hit against ~21% implied. `margin_stdev` 4.025 is
the R2 fallback, never fitted, and nothing distinguishes the postseason.
**Not refit**: the shadow book records only positive-edge rows, so a fit on it is
the S21c selection trap (the sweep pins to its 0.5x grid edge on 22 rows).
Revisit in spring.

### NHL totals floor (live `.env`, `MIN_EDGE_THRESHOLD_NHL_TOTAL=0.06`)

Overs are 16-15 lifetime at -17.3% (model Brier 0.243 vs market 0.221); unders
6-3, +21.8%. All 7 picks since 09-28 were YES over 5.5 at 4.9-6.5% edge; 0.06
blocks them while leaving NHL ML/spreads alone. The model's o5.5 probability is
not over-biased against a Poisson benchmark (-0.2pts, 25 events) -- Kalshi
prices o5.5 5-9pts below the books. Unverified: whether KXNHLTOTAL settles
differently (shootouts). **Correction:** a first pass called these preseason
games; the NHL schedule API puts the regular-season start at 2026-09-29, and a
same-day `MIN_EDGE_THRESHOLD_NHL=1.0` hold on that premise was reverted.

### `shadow_book.py review`: sweep is relative to the in-code stdev

The sweep was a fixed 7-18 grid sized for football's 15.0, so for MLB (4.025)
or NHL totals (2.2) it reported a meaningless "best fit 7.0". It now sweeps
0.5-1.4x each row's own stdev and prints both the multiple and its value.

---

## 2026-10-03 -- Task schedules: every action now launches through `run-hidden.vbs`

`All-Sports-NextDay-Execution`, `Weekly-Analysis` and `Weekly-Futures-Execution` were the
last three tasks whose first action ran the `.bat` directly. Since the wrapper gained
`run-hidden-guard.ps1`, a Task Scheduler stop or time limit kills the process tree only for
wrapped actions, so a direct `.bat` was the one path where a stop could leave a live-order
scan running. Action 1 is now `wscript.exe run-hidden.vbs <task>.bat`; the wrapper waits
and returns the `.bat`'s exit code, so action 2 (the email) and Last Result are unchanged.
Only action 1 changed; triggers, settings and history untouched. Pre-change XML:
`D:\AI_Agents\_maintenance\backups\task-xml-2026-10-03-optimize\`.

## 2026-09-29 -- Polymarket removed; B1 per-book consensus; S9 CLV reporting

### Polymarket US removed

Operator decision: the venue was not being used. In 67 days it never filled an
order, because every candidate stopped at Gate 3. It was, however, armed
(`POLYMARKET_DRY_RUN=false`), running `--execute` unattended every morning.

- The `Daily-Polymarket-Execution` task was unregistered. Its XML and
  `daily_polymarket_scan.bat` are in `.claude/temp/task-backup-2026-09-29/`.
  `\AI-Projects\Edge-Radar-MikesAILab\` now holds 15 tasks.
- Deleted `scripts/polymarket/`, `docs/polymarket/`,
  `docs/setup/polymarket-us-setup.md` and the four `tests/test_polymarket_*.py`
  files. Also removed:
  - the `polymarket`/`poly`/`pm` market type in `scan.py`
  - `PolymarketCredentials` and the `POLYMARKET_*` env vars
  - the venue in `market_client` (`VENUES = ("kalshi",)`)
  - the `reports/Polymarket` report dir
  - the email preset
  - the `pyproject` pythonpath entry
- The executor's venue min-share bump and its post-cap re-check are deleted.
  Only Polymarket set `min_order_shares`, so they were dead code.
- **Kept on purpose:**
  - the venue-neutral seam: the `venue` field on trade rows (now always
    `kalshi`), per-venue eligibility, and the `market_client` factory
  - the email renderer's generic scan-log mode, which is tested and belongs
    to no venue
- The two hand-placed iOS positions (`tec-mlb-champ-2026-09-27-mil`/`-nyy`) are
  still in that account. They were never system trades, and nothing here tracks
  them any more.
- Docs and skills were swept: CLAUDE.md, task-schedules, the three skills, the
  README files, UPSTREAMS and ARCHITECTURE. Historical docs were left as they were.
- The roadmap items PM2e, PM-games and PM3 are gone. B5 (futures devig) stays,
  because it applies to Kalshi futures too.

### B1 -- spread/total consensus inverts per book

`consensus_spread_prob` and `consensus_total_prob` used to take the weighted
median line and the weighted median probability *independently*, then invert
that pair through the normal CDF. The result was a quote no book made. Each
book's mean is now inferred from its own (line, devigged probability), and the
weighted median of those means is used. Measured 2026-08-25 over 37 cached odds
files:
- The error was near zero in the typical case (median 0.00pt, because books
  usually agree on the line).
- Its tail reached **8.8pt, mostly NFL**, and all 12 rows above 3pt pushed
  P(cover) *up*, toward YES, which is the side the gate then selects.

When the books agree, the result is unchanged (tested).

- `weighted_median` now returns the midpoint on an exact 50% weight tie,
  instead of always resolving down to the lower value (review #6).
- `median_book_spread`, `median_book_line` and `raw_median_implied` are still
  recorded, but for display only. Each `books[]` entry now carries its `mean`.
- `shadow_book.reproject` inverts the stored (median line, mean) pair, so it is
  now exact when the books share a line and approximate when they split. This
  is noted in its docstring.

### S9 -- CLV reporting slice

`betting_analysis.py` gets a **Closing Line Value** section directly after the
headline. It shows mean CLV in points with a seeded 95% bootstrap CI, overall
and by sport, category, side and entry-price band, and prints
`n_captured / n_settled` beside every figure. Below 60% coverage (S15's line)
it warns that the mean reads optimistic.

- **The denominator counts filled bets only.** The settlement log also holds
  zero-fill resting orders, which `clv_capture` skips by design because they
  have no entry price. Counting them made the 30-day coverage read 20% (19/93)
  and looked like a capture failure. Of the 19 post-launch rows that had a
  start time but no capture attempt, all 19 were zero-fill or dry-run, and two
  were the 09-15 S28 fractional fills. On filled bets the figure is **27%
  (19/70)**:
  - 41 have no attempt: mostly bets placed before capture shipped, which age
    out of the window by 2026-10-10
  - 10 are recorded `missed`: real capture gaps, worth a look if they keep
    accruing
- Fee role is not sliced. Settlement rows do not record it, and every fill to
  date has been a taker (S23b). The report says so rather than printing a
  constant column.
- First reading (30d): **-0.21 pts, CI [-0.97, +0.55]**, n=19. No signal
  either way yet, and not readable at this coverage anyway.

Tests: +8 (B1 per-book mean and agreeing books, tie-break, S9 coverage, warning,
empty case, bootstrap). The Polymarket suites (−89) are gone, leaving 1202 passing.

---

## 2026-09-29 -- S28 fractional fills, B3 10% Hard Stop, B6(d) DST-aware Eastern time

Three money-path fixes from the top of the roadmap.

- **S28: fractional fills were truncated to whole contracts.** Kalshi fills
  fractionally (`fill_count_fp: "0.01"`), and every parser did `int(float(...))`.
  A 0.01 fill logged as `contracts: 0` / `resting`, and a 1.99 fill as 1. That
  hid paid-for exposure from the trade log, settlement P&L and Gate 2b, and let
  R4's janitor cancel a 0.01-filled order as "zero-fill". All executor sites now
  go through `_order_count()` (float), and the status branch checks `<= 0`. The
  settler (`calculate_pnl`, `trade_fees`, `settle_trade` rows, `reconcile`) and
  `recover_trade_log.py` dropped their `int()` casts too; `taker_fee` already took
  a float. The 2026-09-15 rows still read 0: reconcile them against `position_fp`
  after they settle.
- **B3: the 10%-of-bankroll Hard Stop now exists in code.** `size_order` computed
  `bankroll_pct` and nothing read it. It is now the last sizing step, after the
  venue min-share bump, because the `max(1, ...)` floors and the bump can both push
  cost up. It caps to 10%, and rejects (`hard_stop_position_pct`) only when even
  the smallest legal order breaches it. It is a constant (`HARD_STOP_POSITION_PCT`),
  not an env knob, because config should not be able to loosen a Hard Stop. At
  today's ~$88 cash it does not bind (`MAX_BET_SIZE=8` < $8.80).
- **B6(d): Eastern time was a fixed UTC-4.** `edge_detector` (`_ticker_scheduled_utc`,
  `_commence_et_date`) and `ticker_display.ticker_scheduled_utc` now use
  `ZoneInfo("America/New_York")`. From November to March a game at 04:00-05:00 UTC
  (a late West Coast tip) resolved to the next ET date, so the exact-date
  spread/total and NBA/NHL match found nothing and skipped the market silently.
  The ticker fallback of Gate 4.8 also read every winter start an hour early.
  `tzdata` is already installed as a pandas dependency.
- Tests: +10 (fractional log_trade and the janitor, hard-stop cap/reject/untouched,
  winter parsing on both ET paths). Two existing classes pin
  `HARD_STOP_POSITION_PCT=1.0` to keep isolating Kelly and the min-share bump. 1283 pass.

## 2026-09-29 -- ROADMAP.md cut down to open work only

- `docs/ROADMAP.md` went from 1,048 lines to only the items still open, one line each.
  Performance tables, review findings, shipped and superseded rows, the Completed
  index and its item details were moved **verbatim** to the
  [archive at the end of this file](#archive----roadmapmd-as-it-stood-before-the-2026-09-29-cleanup).
- Each "open" row was checked against the code before being kept. Rows closed by
  later work were dropped rather than carried forward:
  - **B4** (Gate 4.8 read only the ticker): fixed by S23 on 2026-09-16.
  - **T1** (MLB high-strike totals): resolved 2026-07-31.
  - **S1b** (NFL Week 1 review): fired 2026-09-15, branch A.
  - **S2** (quarantine the pre-L2 NFL book): those positions settled 09-09 to 09-14.
  - **P1b** (longshot go-live criterion): the strategy was retired 2026-09-27.
  - **PM2** (Polymarket execution): shipped. S7 and S17 were context, not tasks.
- Confirmed still open in code: **S28** (`int(float(...))` on fill counts, now at
  `kalshi_executor.py:386/1065/1130/1724/1772-1773/2025`), **B3** (`bankroll_pct` is
  computed and never checked), **B2** (12.0 stdev fallback), **B6(d)**
  (`_ET_UTC_OFFSET_HOURS = 4`), **C10c** (`edge * 20` in 7 prediction scanners),
  **B7** (`regions=us`), and S9-S12/S16 (no CLV slice, `strategy_state`, fingerprint
  or kill switch in the code).
- Where old IDs collided (the sports-data S3-S9 against the strategy-review S-series),
  the sports-data features lost their IDs and moved to the backlog.

## 2026-09-29 -- docs/UPSTREAMS.md, and a biweekly upstream check

- New `docs/UPSTREAMS.md`: every external API and library Edge-Radar depends on
  (Kalshi, Polymarket US, The Odds API, ESPN/MLB/NHL feeds, NWS, CoinGecko,
  Resend, ...), what the code assumes about each, and where to check it.
- It is the worklist for the new **Edge-Radar Upstream Check** routine (every
  other Monday 08:00, `upstream/auto-*` PRs against `master`). The routine fixes
  integration-layer drift with tests and queues money-path findings as ROADMAP
  items. Its PRs are not auto-merged; Mike reviews them.

## 2026-09-27 -- Longshot strategy retired

- The longshot strategy (P1 `longshot` profile, Kalshi subaccount 1, `DRY_RUN=true`)
  was abandoned. The `Longshot` scheduled task was unregistered and its gitignored
  `maintenance/longshot_scan.bat` / `email_longshot_scan.bat` deleted; pre-delete
  XML in `.claude/temp/task-backup-2026-09-27/`.
- It never placed a real order, so no live money was affected. The P1 profile
  mechanism (`--profile`, `EDGE_RADAR_PROFILE`, `"profile"` on trade rows) stays.
- `\AI-Projects\Edge-Radar-MikesAILab\` now holds 16 tasks.

## 2026-09-27 -- MLB spreads get their own floor (0.08), and a shadow book

MLB spreads went **0-9**, every one YES on "team wins by over 2.5/3.5 runs" at
15-40c with claimed edges of 4.6-7.5%. The model expected 2.5 wins, the market
2.1; P(0 wins | market prices) = 0.091. MLB totals ran 11-2 over the same 30 days
on the same 0.03 sport floor, so a sport-wide change could not separate them.

- **The formula was checked and is not the cause.** The run-line -> strike
  conversion (normal margin, stdev 4.025) was replayed against 4,862 2024-25
  regular-season finals, bucketed by team strength (season run differential) and
  home/away, through both the favourite (-1.5) and underdog (+1.5) inference
  paths. P(win by 3+) and P(win by 4+) land within ~1-2pts of reality in every
  bucket. Unlike S21's NCAAF 15.0, this stdev fits.
- **The likely cause is selection.** With a ~1-2pt error from the transform alone
  and an effective floor of ~4.3% (0.03 + fee), the gate harvests positive noise.
  It is YES-only by construction, not model lean: a NO on "wins by over 2.5" costs
  75-85c, which Gate 3.55 (`MAX_MARKET_PRICE=0.75`) and R28's 8% NO floor block.
- New `MIN_EDGE_THRESHOLD_<SPORT>_<CATEGORY>` (categories `game`/`spread`/`total`),
  stored as `"<sport>_<category>"` in `_PER_SPORT_MIN_EDGE` and preferred by
  `min_edge_for()` over the sport-wide floor. The 1.0 "off" idiom works per
  category too. Live `.env`: `MIN_EDGE_THRESHOLD_MLB_SPREAD=0.08`.
- `shadow_book.bat` also collects `KXMLBSPREAD` pre-gate, so the floor can be
  judged on every scored strike rather than on the bets the gate chose. Read with
  `shadow_book.py review --sport mlb`. Regular season ended 2026-09-27, so the
  sample is postseason-only until spring.
- Also: `logging_setup.LOG_DIR` honours `EDGE_RADAR_LOG_DIR`, which
  `tests/conftest.py` points at a temp dir. Mocked failures (fake Nevada venue
  rejections, "API 500: API down") were being written into the live
  `logs/kalshi_executor_*.log`.

---

## 2026-09-23 -- Report emails are scripted, and each one rides on its own scan task

Every scheduled report email was a headless `claude --dangerously-skip-permissions -p`
session that read a file a script had already written, restyled it as HTML and called
`send_report_email.py`. That was ~42 sessions a week, about half of all scheduled Claude
sessions on the machine, and the prompts had to ask the model not to drop columns from a
real-money Orders table. Each email was also its own task, fired 10-20 minutes after its
scan and trusting the scan had finished. Consolidation audit 2026-09-23, #6 and #7.

- New `scripts/schedulers/automation/render_report_email.py <preset>` renders the report
  markdown to inline-styled HTML (`markdown-it-py`, now pinned in `requirements.txt`; it
  was already installed as a `rich` dependency) and sends through the unchanged
  `send_report_email.py`. Tables come out byte-exact. Subjects, tags and `logs/email_*.log`
  files are unchanged.
- It takes the **newest report modified in the last 3h**, not "today's date". Report
  filenames carry the UTC date, so the 8:30 PM NextDay and 11:45 PM Weekly-Analysis runs
  write tomorrow's name, and a local-date match misses them.
- No fresh report means exit 2 and no send. Polymarket is the exception: no report is its
  normal zero-opportunity case, so it sends proof-of-life, and it always leads with the
  scan log's last run (gate verdicts, whether an order was placed).
- The 13 scan->email pairs are now one task each with two actions (9 main, 4 in the
  Edge-Radar-Agy fork's folder). Task Scheduler runs the second action even when the
  first exits non-zero (checked with a probe task), so a failed scan still emails. The
  email can't drift from its scan across DST any more. 13 `Email-*` tasks unregistered;
  pre-change XML is in `.claude/temp/task-backup-2026-09-23/`.
- The eight `Run-Reports/*.sh` prompts (gitignored) moved to `_retired-2026-09-23/`.
  Weekly-Analysis loses its model-written summary bullets. Everything else is the same
  report, rendered deterministically.
- Checked: all 8 presets render; a live `same-day` send and a Task Scheduler run of
  `Daily-Summary` (`LastTaskResult=0`) both delivered.

---

## 2026-09-23 -- `NightlySettle` retired; `install settle` now registers `Hourly-Settle`

`NightlySettle` (daily 11 PM) ran the same `kalshi_settler.py settle` as
`Hourly-Settle` (every hour at :35). It was kept after U1 (2026-07-20) as a
validation-week backstop and never retired. `Hourly-Settle` shows 30 of 30
recent runs at `0` and no missed runs, and its 10:35/11:35 PM passes cover the
11 PM slot ahead of `Reconcile` at 11:30. Settle is idempotent, so the nightly
run only ever found nothing new. Flagged as #8 in the 2026-09-23 consolidation
audit.

- Task unregistered from `\AI-Projects\Edge-Radar-MikesAILab\`.
- `install_windows_task.py`'s `settle` profile now creates `Hourly-Settle`
  (`/SC HOURLY /ST 00:35`) instead of the nightly task, so a fresh install gets
  the cadence that keeps Gate 1's daily-loss view current intraday.
- Task-schedules doc, both skills, the automation guide, the longshot doc and
  the roadmap updated to match.

---

## 2026-09-22 -- `reconcile` was blind to every open position since June

`kalshi_settler.py reconcile` only counted local trades with `status == "executed"`.
The executor copies Kalshi's order status into that field, and it has come back
empty since 2026-06-13, so all 191 trades since then are logged as `"unknown"`.
Reconcile therefore saw **0** local positions and reported every live Kalshi
position as "placed manually". Found during the Repos-reorg scheduler
spot-check: 4 real positions were flagged even though all 4 were in the log.

- New `local_open_positions()` keys on **fills**, not status. It skips closed rows,
  `error` rows (whose missing fill fields would otherwise fall back to the
  requested size), unfilled resting and dry-run rows, and non-Kalshi venues.
- NO fills count negative, matching the API's signed `position`. Without that, the
  first NO position to reach the quantity check would read as a mismatch.
- Settle and the risk check's open-exposure count were never affected; they
  filter on `status != "error"`.
- Live run afterwards: 4 local / 4 Kalshi, all match. Three tests are added
  in `tests/test_reconciliation.py`; the suite is 1266 passed.

---

## 2026-09-21 -- S21c NCAAF pilot review: the Brier pair is a tie, and the 09-20 kickoff check passes with no exam taken

One-shot pilot review. **Report only** -- no config touched, no floor moved, no
parameter refit.

### The Brier pair

`shadow_book.py review --sport ncaaf` over **n = 510** settled shadow rows:

| measure | value | role |
|---|---:|---|
| MARKET Brier (predicted = Kalshi price) | **0.1539** | the benchmark |
| MODEL Brier (predicted = fair_value) | **0.1548** | the thing under test |
| difference (market - model) | -0.0009 | leans market |
| 95% CI on the difference | **[-0.0036, +0.0019]** | **straddles zero** |

The market wins the pair by 0.0009 and the CI straddles zero, so this is
**directional only**. Neither side is shown better than the other at this n.
Calibration gap: model claimed 61.6% on average, 57.3% happened, market said
58.0% -- the model over-claims ~4.3 points, the market is within 0.7.

### Stdev sweep -- pre-gate, and still not a refit

Best fit **13.0** over **474 rows**; shipped value is **15.0**. Flat across
12-15 (0.1593 to 0.1599).

These rows **are pre-gate**: `shadow_book.collect()` calls `scan_all_markets`
with `min_edge=0.0`, so no edge floor selected the sample. That is what makes
13.0 a different object from S21's 9.5, which was solved on *filled* bets --
the gate harvests the lowest-implied-stdev rows by construction, so a value fit
on fills restates the selection rule instead of measuring the sport.

**No refit recommended.** The 12-15 spread is 0.0006, smaller than a Brier
difference whose CI already straddles zero, and 15.0 sits inside the band fresh
pre-gate rows imply (~17.0, 15.0 in its IQR). Moving it here is fitting noise.

### The 09-20 kickoff check (first Saturday under S23)

**Zero NCAAF orders were placed on 2026-09-20**, therefore zero sit after their
`event_start_time`. Gate 4.8 passes -- but **vacuously**: it was never handed an
NCAAF order to reject, so 09-20 is not yet evidence the fix works.

The supporting evidence is historical, and it reproduces the 09-19 entry's
finding independently: an all-time trade-log sweep finds **10 post-kickoff NCAAF
orders, all on 2026-09-12** (pre-S23), and **none on or after 2026-09-16**.
Signature present before the fix, absent after. No live defect.

### Notes

- `shadow_book.py settle` returned checked 204 / settled 0 / **204 open** --
  benign. All 204 open rows are unplayed games (09-24: 4, 09-25: 8, 09-26: 173,
  09-27: 19). The 0 means the 06:00 daily task had already settled Saturday.
- Settled slate mix: 09-17 (7), 09-18 (7), **09-19 (419)**, 09-20 (77). The
  first Saturday under S23 is the thinnest-sampled day in the book by a wide
  margin -- a collector coverage question, not a model result.
- `kalshi_settler.py settle`: no unsettled trades in log.
- **Config drift vs. the review's own premise:** the review was scoped against
  an 0.08 pilot floor; the live value is `MIN_EDGE_THRESHOLD_NCAAF=0.06` per the
  09-19 operator override. Recorded so 09-20's zero volume is not later blamed
  on a floor that was no longer in force.

### What would settle the open questions

More settled rows to narrow the CI (two to three more 09-19-sized Saturdays
roughly halve the half-width); one NCAAF order actually reaching the board so
Gate 4.8 is tested non-vacuously; and, for the stdev, a margin wide enough to
clear the 12-15 flat zone.

**Standing caveat:** the shadow book measures **calibration only** -- no
slippage, no queue position, no fee drag. A model that wins on Brier is not
thereby tradeable.

---

## 2026-09-19 -- football pilot floors 0.08 -> 0.06, and the fee gap between nominal and effective

Operator override, prompted by "no NFL or college football bets are being
placed." The investigation found **no defect** -- the drought is the two pilot
floors plus S23's Gate 4.8 fix doing exactly what they were set up to do.

### What the 09-19 slate actually looked like

Re-scanned live with `min_edge=0.001` and tallied `preflight_gate_status`:

```
NCAAF  111 raw rows   0.08 -> ok=  0   edge-reject=98   price=3 live-off=6 no-fav=3 illiq=1
                      0.03 -> ok=  9   edge-reject=82
NFL     30 raw rows   0.08 -> ok=  1   edge-reject=26   no-fav=1 price=2
                      0.03 -> ok= 11   edge-reject=16
```

The best NCAAF row on the board missed by **0.2 percentage points** (edge
0.0952 against a floor of 0.0972). Six NCAAF rows rejected `live-off` -- Gate
4.8 firing on football for the first time, which it structurally could not do
before 2026-09-16 (S23).

### Last week's volume was not a clean baseline

The 09-12 NCAAF batch was 11 bets, and per S23 **10 of them were placed 26-122
minutes after kickoff** by the ticker-blind gate. Split on that line NCAAF ran
-36.5% post-kickoff (n=7) against +13.6% pre-game (n=4). "A lot was being
placed last week" and "the gate was broken last week" are the same sentence.

### The change, and the part that did not work

Both floors went to **0.06**. NFL 1 row -> 4. NCAAF **0 rows -> 0 rows.**

**The fee is added to the floor (F1), so the nominal floor is not the effective
one.** At 30c the fee is ~0.0147, so 0.06 screens at ~0.0747, and NCAAF's best
row was 0.0695. Sweeping the 9 rows that clear at the global 0.03:

| Nominal floor | NCAAF rows admitted | NFL rows admitted |
|:--|--:|--:|
| 0.08 | 0 | 1 |
| 0.06 | 0 | 4 |
| 0.05 | 1 | 7 |
| 0.04 | 7 | 9 |

**Check a proposed floor against the fee before assuming a cut admits
anything.** A floor cut of 2 points bought 3 NFL rows and nothing at all in
NCAAF, because the fee eats roughly a quarter of the nominal move at typical
longshot prices.

### One piece of counter-evidence worth keeping

S21c's OPEN RISK block justified 0.08 over 0.03 on the grounds that 20 of the
26 rows clearing at 0.03 sat at px >= 0.51 -- F3's inversion band. On the 09-19
slate the 9 NCAAF rows clearing at 0.03 are **17-43c, none of them at or above
0.51**. That was measured on the shadow book on 09-16 and on the live gate
population on 09-19, so the two are not directly comparable, but the price-band
argument for keeping NCAAF high does not reproduce on this slate. Re-measure it
before cutting further.

### What actually got placed, and a dedup finding

The 09-20 NFL slate was executed ad hoc the same evening, because
`All-Sports-NextDay-Execution` is a **Sun-Thu** task and does not fire on a
Saturday -- so nothing would have looked at Sunday's games until the 5:05 AM
same-day run, ~5h before a 10:00 AM PT kickoff. 3 orders, $2.20 filled:

```
KXNFLSPREAD-26SEP20CINHOU-HOU8  YES 4/4 @ $0.29  edge +8.0%
KXNFLSPREAD-26SEP20CARATL-CAR8  YES 3/3 @ $0.30  edge +7.7%
KXNFLSPREAD-26SEP20GBNYJ-NYJ8   YES 1/7 @ $0.14  edge +7.4%   (6 resting)
```

**The best row on the board never reached the executor.**
`KXNFLTOTAL-26SEP20MINCHI-43` (edge 11.7%, composite 8.3) was removed by
bracket dedup, which collapsed 20 rows to 13 and kept the **-40 strike** from
that bracket instead. The survivor then failed Gate 4.6:

```
SKIP KXNFLTOTAL-26SEP20MINCHI-40: REJECTED: no_side_favorite
     (price $0.24 < $0.25; needs edge >= 25% and confidence=high)
```

A NO at 24c got tested against R1's 25% bar while the 32c sibling that would
have cleared at 9.5% was already gone. **Dedup runs BEFORE the gates, so it can
hand a gate a row that fails where the row it discarded would have passed.**

**Root cause, found by reproducing the bracket: the two rows tied at composite
8.30 exactly.** It ranks by composite -- not by strike proximity, the other
hypothesis -- and `opp.composite_score > existing.composite_score` is a strict
comparison, so on a tie the first row the scanner emitted kept the slot. The
survivor was decided by scan order, and scan order knows nothing about gates.

Fixed in `_bracket_rank`, which ranks `(clears every static gate, composite,
edge, ticker)` instead of composite alone:

- a row that clears the static gates outranks one that does not, so a bracket
  no longer places nothing when a passing sibling exists;
- composite still decides among equals, so **when every row in a bracket fails,
  the highest composite still wins exactly as before** -- this is a strict
  improvement, not a re-ranking;
- `ticker` last makes the survivor independent of the order the scanner emitted
  rows in, which is what the original defect turned on.

The predicate is `preflight_gate_status`, the same static predictor the scan
table already prints, so the preview and the executor now agree on the keeper.
It covers per-opportunity gates only -- portfolio gates (daily loss, open
count, per-event cap, series dedup) still need live state and can still reject
an "ok" row, unchanged.

Five tests in `TestDedupPrefersGatePassingRow`; four fail on the old code and
the fifth is the unchanged-behaviour guard. Verified against the live bracket:
the survivor is now `-43` (`gate=ok`).

### S23c -- Gate 4.8 gates placement; nothing gated lifetime

Surfaced by the 6 contracts left resting at 14c on `GBNYJ-NYJ8` after the
execution above (1 of 7 filled).

**A resting buy order is a standing offer.** Once its game kicks off it is
precisely the in-play bet `ALLOW_LIVE_BETS=false` forbids -- entered through a
door Gate 4.8 cannot see, because the gate only ever runs *before* an order is
sent. And the market stays open through play: that spread carried

```
kickoff                   Sun 09-20 10:00 AM PT
expected_expiration_time  Sun 09-20 01:00 PM PT   <- "after a winner is declared"
close_time                Tue 09-22 10:00 AM PT
```

so there were ~3 hours of live play in which to fill.

**The fill is adversely selected.** A resting bid is lifted only when sellers
cross down to it, which in-play means the position is already going against us;
if it runs our way the price rises and we never fill. The order fills mostly in
the branch where the edge it was sized on is gone. S23 measured that exposure at
**-36.5% ROI (n=7) against +13.6% pre-game (n=4)** on NCAAF.

**R4 does not cover this, twice over.** `cancel_stale_resting_orders` skips any
order with `fill_count != 0`, and it measures age rather than kickoff -- its 24h
cutoff here landed 3.5h *after* the game ended. The partial-fill exemption
reasons about the **filled** portion ("real exposure the settler will
reconcile"), which is right; the **unfilled remainder** is not exposure yet, and
leaving it resting is a live ungated bet. That rationale was written in April,
before Gate 4.8 existed.

`cancel_live_resting_orders` therefore ignores both age and fill count and keys
only on kickoff. Start times come from **our own trade log joined on
`order_id`** -- the join S22 uses for sides -- because the executor already
stamps the Odds API `commence_time` there as `event_start_time`, and reading the
ticker instead would reproduce exactly the blindness S23 fixed (only moneyline
tickers carry a time). Venue is authoritative for which orders rest; the log for
when their game starts. Fails **open** on an order nothing can date, matching
Gate 4.8, and is a **no-op** when `ALLOW_LIVE_BETS=true`.

Ten tests in `TestLiveRestingOrderJanitor`, including
`test_r4_would_not_have_caught_it`, which asserts the gap directly: on the live
shape R4 returns `[]` while the new janitor cancels.

### Still an override, not a review

No review fired for either change. This is the **third** hand-set NFL floor
(1.0 -> 0.08 -> 0.06) and the **second** hand-set NCAAF floor. The S1b evidence
still has a bootstrap CI of [-0.042, +0.031] straddling zero, and the S21b
shadow book still has no settled rows. Lowering a floor does not add evidence;
it spends the pilot budget faster. Both keys still come out when S10 ships.

---

## 2026-09-16 (S23b) -- the fills endpoint calls it `fee_cost`, and nothing read the post-kickoff tell

S23 closed with two items it deliberately did not fix. Both are now fixed, and
the first was not the benign thing it looked like.

### `taker_fees` was 0.00 on all 67 `fills_api` rows because the key is wrong

The defensible reading was: Kalshi charges no maker fee, the executor posts
limit orders, so passive fills legitimately cost nothing. S23 flagged it for a
spot-check anyway, on the grounds that 52-of-52 is not a distribution. It is
not maker fills. Probing `/portfolio/fills` live:

```
KEYS: action book_side count_fp created_time exchange_index FEE_COST fill_id
      is_taker market_ticker no_price_dollars order_id outcome_side side
      subaccount_number ticker trade_id ts yes_price_dollars

fills fetched: 155, distinct orders: 138
orders with NONZERO fee_cost: 136   total $4.1106
orders flagged is_taker:      133
```

`fetch_fill_fees` read `fee_dollars or taker_fee_dollars or fee` -- **three
names the endpoint has never used**. Every fill resolved to 0, and the settler
stamped the result as `fee_source: "fills_api"`. A modelled number wearing a
measured label.

**A marketable limit at the ask crosses the spread, so it fills as taker.**
"We post limit orders" and "our orders rest on the book" are different facts,
and the fee model's own docstring says the first while the inference assumed the
second. 133 of 138 orders were takers.

**P&L was never wrong.** `trade_fees()` falls back to the modelled fee on a
recorded zero, which is exactly why this survived a month: the arithmetic was
right, only the provenance lied. The model turns out to be *conservative* --
over the 135 matched rows it charges $4.82 against $4.10 actually paid, the
15% gap being the per-order `ceil` on 1-3 contract orders. Gating was never too
loose, and F1's floor needs no change.

The read now takes **first key PRESENT, not first key truthy** -- a maker fill
reports `"0.000000"`, which must record as a measured zero rather than falling
through to the next name -- and an unrecognised payload returns `None`, not 0,
so the caller omits the order and the model takes over. A rename logs a warning
instead of silently zeroing the book again.

### Backfill: `kalshi_settler.py backfill-fees [--apply]`

Fixing the reader does not repair the 133 closed rows behind it -- the settler
only stamps fees on what it is settling now. The new subcommand walks the log
once. Only `fees` changes; `net_pnl` follows it, and `won`/`revenue`/`cost` are
untouched (asserted after the run).

```
Updated 133 trade rows; recorded fees move by $+4.0959

settlement log   fees $14.3519 -> $16.1351      net_pnl $51.8181 -> $50.0349
  76 rows fees UP   (+$2.2151)  -- pre-F1 settlements recorded fees of 0
  51 rows fees DOWN ( -$0.4319)  -- modelled ceil overstated the real fee
```

The book is $1.78 worse than it read, all of it fees genuinely paid before
2026-08-25 and never recorded.

### `close_capture_reason: "missed"` now has a reader

S23 noted the flag "has been a post-kickoff tell sitting in the trade log since
09-12". The fix for that is not another gate -- Gate 4.8 already rejects these,
and **fails open when neither `event_start_time` nor the ticker yields a
dateable start**, which is the right call at gate time and exactly why the
condition needs a detector behind it as well.

`daily_summary.load_post_kickoff_orders()` reports, above everything else in the
digest:

- **proven** -- `timestamp > event_start_time`, with minutes late, and
- **suspected** -- no start time on the row *and* `close_capture_reason:
  "missed"`, reported separately and never counted as proof, because a CLV
  capture task that simply did not run looks identical.

Replayed over the 09-12 window it returns exactly the 10 NCAAF orders S23 found,
+26 to +122 minutes, and nothing in the last 24h. Two independent tells sat in
the log for four days with no reader; the gate is the control, this is the
alarm that says the control failed open.

---

## 2026-09-16 (S23) -- Gate 4.8 had never fired on a spread, a total, or any football market

Operator asked whether the first week of college football had been analysed for
outstanding issues. It had not -- S21c reported bet-level P&L and never audited
the pipeline behind it. Doing so found the actual cause of the NCAAF losses,
and it is not `margin_stdev`.

### 10 of 16 NCAAF orders were placed AFTER kickoff, with ALLOW_LIVE_BETS=false

```
                                              placed    kickoff   delta
KXNCAAFSPREAD-26SEP12WSUKSU-KSU25            18:01:33   16:05Z   +117min
KXNCAAFSPREAD-26SEP12APPECU-ECU8             18:01:33   16:00Z   +122min
KXNCAAFSPREAD-26SEP12COLGCMU-CMU12           18:01:34   17:05Z    +57min
KXNCAAFSPREAD-26SEP12OKLAMICH-OKLA5          18:01:35   16:14Z   +107min
KXNCAAFSPREAD-26SEP12USFARMY-ARMY8           18:01:36   16:05Z   +117min
KXNCAAFSPREAD-26SEP12ALAUK-UK5               21:01:16   19:45Z    +76min
KXNCAAFTOTAL-26SEP12SHUMASS-55               21:01:17   19:30Z    +91min
  (+3 more that never filled)
```

Two batches, 18:01Z and 21:01Z: `All-Sports-NoDateFilter-Midday-Execution`
(daily 11:00 AM PT) and `All-Sports-SameDay-Late-Execution` (daily 2:00 PM PT).
Both run **daily, including Saturdays** -- dead in the middle of the slate.

Split the NCAAF book on that line and it stops being a sport problem:

| | n | W-L | staked | P&L | ROI |
|:--|--:|:--|--:|--:|--:|
| **post-kickoff** | 7 | 1-6 | $8.62 | **-$3.15** | **-36.5%** |
| pre-game | 4 | 1-3 | $4.20 | +$0.57 | **+13.6%** |

**The entire NCAAF loss is the live bets.** An alt-spread model priced off
pre-game consensus is catastrophically wrong two hours into a game, where much
of the margin distribution has already resolved. This is a far better
explanation of 11 one-sided YES bets going 2-9 than an unfitted stdev -- and it
is consistent with S21c's finding that the stdev disagreement did not replicate
on fresh pre-gate rows.

### Why the gate could not see them

`is_game_started()` parses the start time out of the **ticker**, and only
moneyline series embed one (`KXMLBGAME-26JUL21`**`1840`**`MINCLE-MIN`). Every
spread, every total, and every football ticker is date-only:

```
KXNCAAFSPREAD-26SEP12WSUKSU-KSU25   sched=None    started=False
KXNCAAFTOTAL-26SEP12SHUMASS-55      sched=None    started=False
KXNCAAFGAME-26SEP12WSUKSU-KSU       sched=None    started=False
KXNFLSPREAD-26SEP13ARILAC-LAC28     sched=None    started=False
KXMLBGAME-26JUL211840MINCLE-MIN     sched=2026-07-21 22:40Z   started=True
```

So Gate 4.8 returned False for them no matter the time of day. **123 of 175
filled live-money bets -- $128 of $211 staked, 61% -- sat on markets it
structurally could not protect**, led by KXWCSPREAD (36), KXMLSSPREAD (20),
KXMLSTOTAL (18), KXNFLTOTAL (11), KXNFLSPREAD (10), KXNCAAFSPREAD (10). The
limitation was *documented in the comments at both call sites* and never
connected to the fix sitting next to it.

### The fix

`details["event_start_time"]` -- the Odds API `commence_time` for the matched
event, carrying a real time -- was **already on the opportunity at gate time**.
The executor only read it *after* the fact, to stamp the trade row (line 1638).
New `_game_has_started(opp)` prefers it and falls back to the ticker; both Gate
4.8 call sites now use it. Fails **open** when neither source is dateable,
matching Gates 3.6/3.7 -- an unknown start time is a sizing question, not a
legality one.

Replaying all 16 real NCAAF orders through the fixed gate: **10 rejected
`live_betting_disabled`** (the 7 filled ones staking $8.62 for -$3.15), and the
**4-bet pre-game book survives untouched at +13.6%**.

**This also protects the live NFL pilot.** No NFL row carries
`event_start_time` (the S8 field postdates the whole NFL book), so no past NFL
bet can be proven live -- but NFL tickers are all date-only too, so the gate
never covered them either, and Sunday 1:00/4:25 PM ET kickoffs sit *before*
both the 11 AM and 2 PM PT tasks.

### Two open items, not fixed here

- **`taker_fees` is 0.00 on all 52 rows that carry `fee_source: fills_api`** --
  not one nonzero fee in the book. Kalshi charges no maker fee and the executor
  posts limit orders, so passive fills legitimately cost 0; but 52/52 wants a
  spot-check against a known taker fill before F1's "fees are now captured
  post-trade" is trusted. Gating and sizing use the *modelled* fee and are
  unaffected either way.
- **`close_capture_reason: "missed"` on exactly the 7 live bets.** Not an
  independent bug -- the t-minus-5 CLV window had already passed at order time.
  Worth noting that this flag has been a post-kickoff tell sitting in the trade
  log since 09-12.

---

## 2026-09-16 (S21c) -- NCAAF to a 0.08 pilot floor, and S21's mechanism does not replicate

Operator asked to re-enable college football. Checks first. The freeze came off
to a **0.08 pilot floor by operator override** -- the same shape as S1b, and
recorded as such, because the S21b shadow book had **zero settled rows** at the
time of the change.

### The evidence the freeze is waiting on had not arrived

```
$ python scripts/backtest/shadow_book.py review --sport ncaaf
  No settled shadow rows for NCAAF.

354 rows collected 09-13 -> 09-16, game dates:
  26SEP17   6
  26SEP18  14
  26SEP19 332   <- settles into the 09-20 06:00 pass
  26SEP26   2
```

The daily `Shadow-Book-NCAAF` task is healthy (09-16 pass: scanned 142, added
56). It simply started four days ago and college football plays on Saturdays.
**Re-run `review --sport ncaaf --save` on 09-21** -- the Brier pair and the
stdev sweep land on a ~350-row sample, 30x the 11 live bets, at zero risk.

### S21's margin-stdev finding was a selection artifact

S21 froze NCAAF on the reading that `margin_stdev` 15.0 is an unfitted prior
the market disagrees with at ~9.5, and that 11 straight YES bets were one
disagreement restated eleven times. Solving the same strike-independent
expression `stdev* = 15 * ppf(1-fv) / ppf(1-px)` reproduces that exactly -- and
then fails to reproduce it anywhere else:

| population | n | median implied `margin_stdev` |
|:--|--:|--:|
| 10 filled live spread bets (S21's sample) | 10 | **9.44** |
| fresh PRE-GATE shadow spread rows, tail strikes only | 94 | **17.04** (IQR 14.2-20.6) |

15.0 sits inside the fresh IQR. The reason is mechanical: **edge on a YES
big-cover bet is monotone decreasing in market-implied stdev**, so the gate
harvests the lowest-implied-stdev rows in the book by construction. The
"eleven restatements of one disagreement" is real, but it is the *selection
rule* restating itself, not a miscalibrated parameter.

The direction inverts too. If 15.0 were too fat, the model would sit *above*
the market on big covers. Signed to the YES event, on fresh pre-gate rows:

| YES-event price | n | mean(model - market) | model higher |
|:--|--:|--:|--:|
| <=0.30 (big-cover longshots) | 49 | **-0.018** | 29% |
| 0.30-0.70 | 107 | -0.004 | 50% |
| >=0.70 | 45 | **+0.031** | 76% |

**Do not refit `margin_stdev` down to 9.5.** It would under-price every tail in
the sport to chase an artifact of the selection rule.

### Why 0.08 and not the global 0.03

The rows that clear at 0.03 are not the population that got frozen. Simulating
gates 3-4.6b at live `.env` values over the 354 shadow rows:

| floor | rows clearing | of those, px >= 0.51 |
|:--|--:|--:|
| 0.03 (global) | 26 | **20** |
| 0.05 | 14 | 12 |
| **0.08 (shipped)** | **4** | 4 |
| 0.10 | 0 | 0 |

Last week's 11 NCAAF bets were all 12-32c and went 2-9, **-20% ROI on $12.82**.
This week's clearing rows are 52-75c -- **F3's inversion band**, where the
high-edge half wins 10.8pts *less*. Unfreezing to 0.03 would not resume the
frozen experiment; it would start a new one in the band the model is on record
as worst in. At 0.08 the band exposure is capped by count, not avoided, and
Gate 2b still holds NCAAF to 33% of equity.

Live check after the change: `doctor.py` reports `ncaaf=8.0%`, NCAAF is off the
sports-OFF line (only `worldcup` remains), the scanner fetches 4620 NCAAF
markets again, and **all 20 preview rows still show gate verdict `edge`** --
today's best NCAAF edge is 8.4% against a 0.08 floor plus a 2c fee. The pilot
is binding on day one, which is the point.

### Found while verifying: `--filter ncaaf` silently matched nothing

`scan.py sports --filter ncaaf` returned **0 markets**. The canonical shortcut
keys are `ncaafb`/`ncaamb`, but an unknown shortcut falls through to a literal
uppercase prefix -- `ncaaf` -> `NCAAF` -- which no Kalshi series carries. The
scan then reports "No opportunities found above edge threshold", which is
indistinguishable from a quiet day.

`longshot_scan.bat` passes `--filter ...,ncaab,ncaaf,...`. **Neither is a key,
so the longshot profile scanned zero college football and zero college
basketball from its 09-10 migration until today** -- the same failure the
retired Edge-Radar-Longshot fork hit on a stale `KXNCAAFBGAME` prefix, which
rode across with the `.bat`. Three fixes:

- `ncaaf` and `ncaab` added to `FILTER_SHORTCUTS` as aliases. Fixed in code
  rather than in the `.bat`, because the schedulers are gitignored and a
  `.bat`-only fix does not survive a clone.
- The raw-prefix fallback now prints a yellow NOTE naming the unrecognised
  token. It stays a feature (`--filter KXNHLGOAL` is legitimate), but it no
  longer fails quietly.
- `TestCollegeFilterAliases` asserts every shortcut maps to a `KX*` series and
  that every sport with a `MIN_EDGE_THRESHOLD_<SPORT>` floor is reachable by a
  filter of the same name -- a floor only binds rows a filter can fetch.

### Also settled: the NFL S1b review fired

`NFL-Week1-Review` ran 09-15 07:00 and returned **branch A** (model Brier
0.1216 vs market 0.1333, n=22, model error -0.4% against a 15% bar),
independently ratifying the 0.08 NFL floor the operator had set by hand on
09-13. `applied: false` -- the key was already at the value the script would
have written. CLAUDE.md's "re-run the review once MNF settles" is now
satisfied; the end state is correct and the path bypassed the gate.

---

## 2026-09-13 (S22) -- Gate 6b: never hold both sides of one game

Operator spotted it by eye: "multiple bets in the same game, but bets for the
opposing sides." Confirmed, twice, in 216 placed bets.

```
KXNFLGAME-26SEP10SFLAR-LAR    yes  3 @ 63c  06-01   "Los Angeles R win?"
KXNFLSPREAD-26SEP10SFLAR-SF8  yes  6 @ 11c  08-10   "San Francisco wins by over 7.5?"

KXWCSPREAD-26JUN26EGYIRI-EGY2 yes      resting 06-20   Egypt by 2+
KXWCSPREAD-26JUN26EGYIRI-IRI2 yes 13 @  8c  06-22   Iran by 2+
```

At most one leg of each pair can ever pay. The NFL pair went +$3.35 on luck;
the WC pair lost $1.04.

### Why every existing gate passed

Not one bug -- three independent blind spots that happened to line up:

| gate | why it missed |
|:--|:--|
| 5 duplicate ticker | different tickers |
| 6 per-event cap | **`_event_key` keeps the series prefix**, so `KXNFLGAME-...SFLAR` and `KXNFLSPREAD-...SFLAR` are different "events" |
| 7 series dedup | game-scoped and *would* have matched -- but it is a 48h window over the trade log, and the legs were **70 days** apart |

The middle row is the one worth keeping: **`MAX_PER_EVENT=2` actually means "2
per series per game."** Measured across the settled book, one real game has held
**6** positions and 13 games have held more than 2. The cap has been reading as
tighter than it is since it shipped.

And beneath all three: **nothing anywhere compared direction.** Every gate
counted tickers, positions, events or matchups.

### The gate

`opposing_position()` rejects only what is arithmetically unable to win
together. A moneyline is normalised as the margin-0 case of a spread, which is
what lets a single comparison cover the moneyline-vs-spread pair that actually
occurred:

    KXNFLGAME-26SEP10SFLAR-LAR    yes -> ('26SEP10SFLAR', 'LAR', 'yes', 0)
    KXNFLSPREAD-26SEP10SFLAR-SF8  yes -> ('26SEP10SFLAR', 'SF',  'yes', 8)

Two rules: different teams both YES; or same team, YES at margin `a` against a
held NO at margin `b` with `a >= b`. Everything else passes, deliberately --
YES-by->4 with NO-by->10 is the legitimate "wins by 5-10" band trade, and
spread+total, moneyline+spread on one team, and two NO legs on different teams
are all jointly satisfiable. **Totals never enter**: they say nothing about who
wins. **Futures are exempt**, for the reason Gate 6's own docstring already
gives -- their outcomes partition an event rather than contradict each other.

The game key is the ticker's date+teams segment verbatim, *not* `matchup_key`:
that one is deliberately date-invariant so Gate 7 can see a series across days,
and here two different games between the same teams must never collide. Keeping
the embedded start time also keeps MLB doubleheaders distinct.

### Resting orders count

Half the real cases had a leg that never filled, and a zero-fill order has
`position_fp == 0`, so the positions feed shows nothing -- the same blind spot
S21 closed for Gate 2b. `resting_sides()` adds them.

**Sides come from our own trade log, joined on `order_id`, never from the venue
payload.** v2 expresses every order from the YES perspective, so a NO buy comes
back as an `ask`; reading `side` raw inverts it. This is the identical trap
`resting_exposure` documents for price, and it is worth stating twice because
the payload looks perfectly readable when it is wrong.

Fails **open** on a side it cannot name -- omitted and logged at WARNING, the
same posture as 3.6/3.7 on unreadable data. Over-blocking on a guessed side
would reject coherent bets.

### Within-batch too

`open_sides` accumulates across the slate, or both sides of one game approved in
a single run walk through together -- the within-batch hole S4 had to close for
exposure. The R26 replay path re-checks 6b alongside 5/6/7 for the same reason.

### Verification

Replayed all **216** placed bets through the gate in entry order: **2 blocked,
both of them the real pairs, zero false positives.** 46 tests
(`tests/test_opposing_side_gate.py`), full suite 1221 passed, and flake8 on the
executor is unchanged at 42 (none introduced).

Live confirmation the same evening, on the NFL slate this was written for:

```
KXNFLSPREAD-26SEP13DALNYG-NYG3 -> REJECTED: opposing_side
                                  (already holding KXNFLSPREAD-26SEP13DALNYG-DAL15)
```

A scan preview that night offered **both** "New York G wins by over 2.5" and
"Dallas wins by over 4.5" on one game, hours after NFL went back on the board
at the 0.08 pilot floor. The gate was not hypothetical by the time it landed.

---

## 2026-09-13 (S1b-early) -- NFL to the pilot floor, by hand, two days early

`MIN_EDGE_THRESHOLD_NFL` 1.0 -> **0.08**. Operator decision, taken knowingly
ahead of the pre-declared 2026-09-15 review date.

**The review did not fire. It returned BRANCH C**, twice, on the same day:

```
17:32   only 12 usable settled NFL bets, need 20   (15 settled, 3 dropped)
17:5x   only 18 usable settled NFL bets, need 20   (21 settled, 3 dropped)
```

Week 1 was still settling while this was decided -- 11 NFL rows remained open,
including Monday's DEN@KC. S1b was written on 2026-08-26 "precisely so a hot or
cold Week 1 could not argue with it", and the thing it guards against is
deciding on a Sunday evening with the sample still moving. Recording that
plainly matters more than the floor itself: **"the script unfroze NFL" and
"the operator unfroze NFL early" collapse into the same memory within a month**,
and only one of them is evidence. This was the second.

**What the evidence did say**, on the 18 usable rows at the time:

```
n=18   model Brier 0.1318   market Brier 0.1399   diff -0.0081   95% CI [-0.0417, +0.0311]
       spread  n=8   model 0.1814  market 0.1959
       total   n=10  model 0.0922  market 0.0951
       mean model prob 0.630 | realised 0.611 | over-claim +0.019  (bar 0.15)
```

Model ahead in both categories, and an over-claim of +0.019 against a 0.15 bar
-- genuinely the healthiest calibration any segment here has shown, and nothing
like NCAAF's. It is branch-A *shaped*. It was two rows short of being branch A.
The CI straddling zero is the whole reason branch A caps to a pilot rather than
unfreezing outright, so the cap is doing its job either way.

**Action on 09-15: re-run `nfl_week1_review.py` on the full Week 1 sample.** If
it returns C, the floor goes back to 1.0.

### The open risk this surfaced: NFL spreads carry the S21 signature

Ran S21's own one-sidedness diagnostic against the NFL book, since the review
predates S21 and does not check for it:

```
n=8 settled NFL spreads, side mix {yes: 8}
  NESEA-NE5    px 0.22  fv 0.28   stdev* 10.36
  SFLAR-SF8    px 0.11  fv 0.20   stdev*  9.26
  ATLPIT-ATL11 px 0.10  fv 0.15   stdev* 10.81
  CHICAR-CHI11 px 0.22  fv 0.28   stdev* 10.17
  GBMIN-GB8    px 0.23  fv 0.28   stdev* 10.40
  MIALV-MIA7   px 0.16  fv 0.22   stdev* 10.41
  NODET-NO5    px 0.14  fv 0.20   stdev* 10.65
  TBCIN-TB11   px 0.10  fv 0.16   stdev* 10.65

  median reconciling stdev 10.40 vs the hardcoded 13.50   ratio 0.77
  (NCAAF, which this froze this morning: 9.5 vs 15.0, ratio 0.63)
```

8 of 8 YES on a big alternate cover, and the reconciling stdev sits in a
1.5-point band. That is the same parameter disagreement S21 describes, milder,
and `margin_stdev: 13.5` is a hardcoded prior exactly as 15.0 was. **If NFL
spreads start losing one-sidedly, suspect the stdev before variance.** The
counter-evidence is real though, and is why this is a flag and not a second
freeze: NFL spreads currently *beat* the market on Brier (0.1814 vs 0.1959),
where NCAAF's lost it.

### Settlement-log audit (run before setting the floor)

| check | result |
|:--|:--|
| `won` vs `side == result` | **5 rows wrong -> backfilled** (see below) |
| S18 invariant `fv - px == edge` | 0 violations / 466 rows |
| `cost == contracts x price` | 0 violations |
| duplicate `trade_id` | none |
| rows missing `fair_value` | 15, **all** `edge_source=reconstructed_from_kalshi_position` -- correctly dropped, not a defect |
| S21 `won` fix in production | confirmed: today's zero-fill resting NFL row scored `won=True`, not a phantom loss |

**Backfilled the 5 phantom losses S21 identified** -- all MLB totals settled
2026-09-12, all zero-fill NO rows where the result was NO, all logged as losses
by the pre-fix `revenue > cost` expression. Each now carries
`won_backfilled` naming its previous value. Global pair moves to model 0.2151 /
market 0.1942 over 451 rows (F3's baseline: 0.2270 / 0.2037 over 390). **The
five were MLB, so none of them touched the NFL decision above** -- they were
fixed because the audit was the gate on making it.

Known and *not* fixed: 6 `(ticker, side, date)` pairs settle twice, one of them
NFL (`KXNFLTOTAL-26SEP13GBMIN-67`). These are genuinely two orders on one market
-- a resting one at 0.87 that never filled and a filled one at 0.80, distinct
`trade_id`s, both scored correctly. Not corruption, but it double-counts one
game outcome in a Brier sample, so it is a mild independence violation worth
knowing about at n=18.

---

## 2026-09-13 (S21b) -- the freeze that could never end

Follow-on to S21, found while arming an NCAAF review on the NFL pattern.

**It would never have fired.** `nfl_week1_review` needs `MIN_SETTLEMENTS` (20)
settled rows. S1b works because **19 NFL positions were already in flight** when
the S1 freeze landed; they settle across Week 1 and become the evidence.
Projection for the 09-15 run: 5 settled now + 19 open = 24 settled, 21 usable --
clearing the bar by exactly one row.

NCAAF was frozen holding **nothing**. Yesterday's book settled out and the last
two resting orders were cancelled, so the freeze stops every future order, which
stops every future settlement, which pins the count at 11 settled / 14 usable --
permanently under 20. `decide()` returns branch C on every run, forever. A task
that looks armed and healthy and can never change anything: the same
"fresh, green, and wrong" shape as the 2026-09-10 entry, and the same shape as
`_MIN_CALIB_SAMPLES` never being reachable for the very sport whose stdev is
wrong.

**A freeze that blocks its own exit is not a pause, it is a deletion.**

### The fix: score the sport without betting it

A Brier head-to-head needs only (model probability, market price, outcome). It
**never needed a filled order**. `scripts/backtest/shadow_book.py`:

    shadow_book.py collect --filter ncaafb    # log what the model says
    shadow_book.py settle                     # outcomes from Kalshi, read-only
    shadow_book.py review --sport ncaaf       # Brier pair + stdev sweep

**Where it taps is the whole design.** `data/cache/last_scan.json` is written
POST-risk-gate, so at NCAAF's 1.0 floor it holds nothing -- reading it would let
the freeze suppress exactly the rows under test. `scan_all_markets()` applies
only the GLOBAL `min_edge_threshold`, never the per-sport `min_edge_for()`
(that is Gate 3, in the executor), so collecting upstream records what the MODEL
said while the gates remain the thing being judged. Verified, not assumed: a
live run collected **96 rows in one scan**, 79 of them sweep-ready.

**The sweep is the point.** S21 found the entire NCAAF edge was one uncalibrated
parameter, and `_MIN_CALIB_SAMPLES` (20/sport/category/30d) meant real bets could
never fit it. `review` re-projects each row's stored consensus across stdevs 7-18
and reports which minimises MODEL Brier -- a direct read on the parameter, from
rows that cost nothing. The devigged implied probability is recovered from the
stored (line, inferred mean, stdev) triple rather than from `raw_median_implied`,
which is PRE-devig and would silently reintroduce the overround the model removes.

**The shadow book immediately contradicted a loose reading of S21.** The 96 rows
split **58 NO / 38 YES**. The 11-of-11 YES pattern was the *placed* book -- part
stdev bias, part Gate 3 selection effect. The shadow book sees both sides, which
is what makes the sweep a measurement rather than a restatement.

### Deliberately not a decision

Nothing in `shadow_book.py` writes `.env` or lifts a freeze, unlike
`nfl_week1_review.py`. Shadow rows are not fills: no slippage, no queue position,
different survivorship. This measures **calibration**, which is what a freeze
waits on; it does not measure tradeability. `MIN_SWEEP_ROWS` (25) flags a
too-small sweep as a shape rather than a number, so a 6-row "optimum" is never
read as a result.

### Verified end to end

`--self-check` pins the reprojection (a row re-projected at its own stdev must
reproduce its own probability; a tighter stdev must pull an uncovered strike
down; NO is the complement of YES; junk details return `None`, never a
plausible number). The settle path was checked against two real finalized
markets, one `yes` and one `no`. `Shadow-Book-NCAAF` ran once on registration:
exit 0, and the second run added only 7 of 96 rows, confirming the
first-sighting dedup. After it: **0 resting orders, trade log unchanged at 216
rows, freeze intact.**

---

## 2026-09-13 (S21) -- NCAAF was betting one parameter, 11 times

Reported as "I thought we lost quite a few college football bets yesterday."
We did: **1 win / 8 losses, -$5.51 on $10.86 staked (-51% ROI)**. Everything
that settled on 09-12 was college football. But the losses are not the finding
-- 2 wins against 2.1 market-expected across 11 bets is squarely inside noise
on 12-28c longshots.

### The finding

**All 11 NCAAF bets ever placed are YES on "team covers a big alternate
spread." 11 out of 11.** An edge signal that fires in one direction every
single time is not a signal.

The pipeline itself is sound -- re-running `consensus_spread_prob` against the
live odds cache reproduces each book's own line to within 0.9 points,
symmetrically on both sides; the two-way devig is applied; `_match_team_outcome`
correctly separates Michigan from Central Michigan. Nothing is broken.

The edge comes entirely from the **margin standard deviation**. Solving, per
bet, for the stdev that would reconcile the model with Kalshi:

```
code uses              15.0
Kalshi prices as if  =   9.5   (median across all 11 bets)
```

That ratio *is* the claimed edge. Oklahoma >4.5 prices at 23.2c under stdev
15.0 and 18.0c under 12.0 -- the market price, exactly. The derivation is
strike-independent (`stdev* = 15 * ppf(1-fv) / ppf(1-px)`; the strike cancels),
so this is one disagreement restated eleven times, not eleven edges. A fat
stdev inflates P(big cover) uniformly, which is why the model finds value on
every YES and never once on the NO side.

**And 15.0 was never fitted.** `data/cache/calibration_stdevs.json` carries the
`edge_detector.py` fallback byte-for-byte. It cannot be fitted either:
`model_calibration._MIN_CALIB_SAMPLES` is 20 per (sport, category) inside 30
days, and NCAAF has 11 settles in total. Scorecard, reported as the S18 pair:
**market Brier 0.1538, model Brier 0.1744** -- the market is ahead, consistent
with F3.

This is the S1 shape exactly: a cold-start sport priced off a hardcoded prior,
live, with no freeze. NCAAF fell through to the global `MIN_EDGE_THRESHOLD=0.03`.

### Fixed

- **`MIN_EDGE_THRESHOLD_NCAAF=1.0`** in the live `.env` -- the same unreachable-
  floor idiom as the NFL freeze and World Cup. Verified end to end rather than
  assumed: `_detect_sport()` returns `ncaaf` for all three prefixes
  (`KXNCAAFSPREAD/TOTAL/GAME`), `min_edge_for()` returns 1.0000 for NCAAF spread
  and total, MLB/NCAAB stay 0.0412 and NBA 0.0512, and `doctor.py` now prints
  `sports OFF (floor >= 100%, unreachable): ncaaf, nfl`. **Temporary**, like
  S1 -- the durable rule is cold_start -> pilot mode when S10 ships.
- **Two resting NCAAF orders cancelled** (Sep-19 TEMTOL and PURUCLA, placed
  09-13 18:01). The freeze blocks new orders; it does not retract live ones.
  Both carried a **fractional partial fill** -- `fill_count_fp` 0.01 of 2.00 --
  which is worth noting on its own: `cancel_stale_resting_orders` tests
  `int(float(fill_count_fp)) != 0`, so a sub-1.0 fractional fill truncates to 0
  and the janitor treats a partially-filled order as untouched, against its own
  docstring's promise to leave partial fills alone. Not fixed here; recorded.

### Also fixed: unfilled orders were logged as losses

`calculate_pnl` returned `"won": revenue_dollars > cost`, a **profit** test worn
as a **prediction** test. On a zero-fill row both sides are 0, so `0 > 0` is
False and every resting order that settled entered the log as a loss regardless
of the outcome. `won_bet` was already sitting correctly computed two lines
above; `won` now returns it.

It matters because `calibration_study.load_rows` does **not** filter on fills --
34 of its 435 rows have zero contracts, and 5 of those are phantom losses whose
bet side actually called the result. That sample is the one F3's lambda and
S18's model-vs-market pair are computed from. For any filled row the two
expressions agree, so nothing about settled P&L moves.

The 5 existing rows in `kalshi_settlements.json` are **left as-is** -- a
backfill rewrites historical records and is the operator's call.

---

## 2026-09-11 -- Task schedules: daily tasks launch hidden via `run-hidden.vbs`

Every daily-or-more-frequent task now runs `wscript.exe scripts/schedulers/run-hidden.vbs
<original command>`, which `Run()`s it with window style 0 and `WScript.Quit(rc)`, so the
exit code still reaches the scheduler. `CLV-Capture` every 5 minutes had made the visible
`cmd.exe` 288 desktop interruptions a day. Applied to 15 tasks with `Set-ScheduledTask
-Action` only; weekly and one-shot tasks were left visible (extended to them 2026-10-03).
`pythonw.exe` was rejected for the settle tasks: no console means `sys.stdout` is `None`,
and any `sys.stdout.write` or logging `StreamHandler` in the import graph would raise.
Pre-change XML in `.claude/temp/task-backup-2026-09-11/`.

## 2026-09-10 (final) -- Two dated reviews never ran, and nothing said so

Routine health check, not a reported bug. `doctor.py` was all-pass, quota
healthy (4929 across 14 keys), no task reporting a failure.

**`U2-Review` (armed 2026-05-14) and `R8-Review` (armed 2026-05-29) had never
run.** Four and three-and-a-half months. Both are pre-declared one-shot reviews
of the kind this project relies on -- the same mechanism as S1b's
`NFL-Week1-Review`, which fires unattended on 09-15 and is the only thing
permitted to touch the S1 NFL freeze.

### Why it hid

Neither had `StartWhenAvailable`. A one-shot trigger whose time passes while
the machine is off or asleep is **dropped and never retried** -- and Task
Scheduler records nothing. The task still reads `Ready`. `LastTaskResult` stays
**`267011`** ("has not yet run"), which is **byte-identical to a task correctly
waiting for a date that has not arrived** -- `NFL-Week1-Review` reads exactly
the same right now, and is fine. There is no state anywhere that separates
"waiting" from "missed forever"; the only way to see it is to notice a trigger
date already in the past.

`schtasks /Create` cannot set the flag at all, which is why it was missing:
`install_windows_task.py` creates tasks that way, and its own docstring already
conceded the live tasks were "built by other means with richer settings
(run-as principal, wake/retry policy) than `schtasks /Create` sets here."

**25 of 29 tasks lacked it.** The four that had it were the recently-registered
ones -- `CLV-Capture`, `NFL-Week1-Review` -- where the lesson had been learned
and then not applied backwards.

### The signature has now appeared three times

``Last Run Time`` `11/30/1999` with `Last Result 267011` is exactly what
**`MonthlyCalibration`** showed on 2026-07-31, when it was diagnosed as a dead
duplicate and deleted. The diagnosis was right on the merits -- the weekly
`Calibration` task was doing all the work -- but **the flag was never checked**,
so the mechanism that could also explain a monthly task never once firing went
unexamined for another six weeks. Reading this signature as "dead task" rather
than "missed run" is the trap; they look the same.

### Fixed

- **All 27 live tasks now set it.** For dailies a miss was cheap; for the
  weeklies it costs a full cycle, and for `Calibration` enough misses push the
  stdev cache past `CALIBRATION_STDEVS_TTL_DAYS` (30).
- **Execution tasks included, by operator decision.** This is a behaviour
  change, not just reliability: a missed run now fires when the machine wakes,
  against whatever slate is live *then*. Bounded by Gate 4.8
  (`ALLOW_LIVE_BETS=false`), Gate 3.7 and each task's `--budget` / `--max-bets`.
- **`install_windows_task.py` now sets it after every `/Create`**, so the
  generator stops reproducing the defect, and **warns** rather than failing if
  no PowerShell is available -- a task without the flag still runs whenever the
  machine is up, so a restricted shell is not a reason to reject a good install.
  Prefers `pwsh`, falls back to Windows PowerShell. `tests/test_install_windows_task.py`,
  7 tests, pinning the `Folder\Leaf` -> `-TaskPath`/`-TaskName` split (a wrong
  split silently targets the wrong task). **1174 pass.**


### The hooks themselves had never run, and had rotted

Installing pre-commit surfaced two config bugs that would have failed every
commit for anyone who did:

- **flake8 got `W503` as a FILENAME.** `args: [--max-line-length=100,
  --extend-ignore=E203,W503]` is an unquoted YAML flow sequence, so it splits on
  the comma and `W503` became its own list item -> `E902 FileNotFoundError:
  'W503'`. Now quoted.
- **`.secrets.baseline` did not exist**, so detect-secrets aborted with
  `argument --baseline: Invalid path`. Generated; six flagged lines, all
  verified false positives before being baselined -- FRED's public
  `DEMO_KEY`, the `k1,k2,k3` / `abcd1234deadbeef` test fixtures, a
  `securePassword123` doc template, and a Windows task path. The baseline
  stores hashes, not values (checked).

Three pre-existing flake8 violations in `install_windows_task.py` (one E501,
two `f`-strings with no placeholders) were fixed in passing, since they now
block any commit touching that file.

### R8 was run before its task was retired: no action

`CROSS_CATEGORY_DEDUP` stays `false`. **0 flip-on, 0 flip-off, 8 need more
data** -- every sport is under the 10-cohort bar. Report at
`reports/Performance/R8_cross_category_review_2026-09-10.md`.

Worth noting from it: **MLB has 145 settled games and 0 cross-category
cohorts.** `MAX_PER_EVENT` and Gate 7 are already preventing the ML+Total+Spread
stacking R8 exists to catch, so the question R8 was armed to answer is
substantially moot on the sport that dominates the book.

`U2-Review` was not run -- its premise was a two-week post-ship reliability
check on the daily summary, and four months of the task working answers it.
Both tasks were deleted, definitions exported to
`scripts/schedulers/retired-task-xml/` (gitignored) first.

**Also:** pre-commit hooks were not installed on this machine at all. Given the
standing rule that `.env` is never committed, `detect-secrets` not running was
a live gap; installed, and the config repaired so it actually runs.

---

## 2026-09-10 (later) -- P1b: how the two books are differentiated, written down, and a pre-declared go-live criterion

Documentation only; no code changed.

### The four layers

`docs/longshot/README.md` now records how `main` and `longshot` stay apart, as
four independent layers: **selection** (`--profile` / `EDGE_RADAR_PROFILE`),
**settings** (`.env.longshot` overlaid on the base `.env`), **money**
(`KALSHI_SUBACCOUNT`), and **data** (the `"profile"` tag on every trade row).

**Only the money layer isolates anything.** The other three keep the two books
from confusing *each other*; the exchange is what stops them spending each
other's cash. Layer 2 is where the strategy actually lives, and it is four keys
-- everything else is inherited, which is the point of the merge.

Two things verified rather than assumed while writing it:

- **Reporting is pooled, not split.** `daily_summary.py`, `risk_check.py` and
  `betting_analysis.py` read the whole trade log. This is currently harmless,
  but not for the reason it looks: a dry run returns `dry_run_blocked` with no
  fill, so longshot's rows are zero-fill, dropped by both the `fill_status ==
  "resting"` and `get_filled_cost() <= 0` tests in `load_open_positions`, and
  never settle. **It stops being harmless the moment `DRY_RUN=false`.**
- **Settle and reconcile only ever see subaccount 0.** `KalshiClient()` takes
  its subaccount from the *active* profile, and every settle/reconcile task runs
  unprofiled. `CLV-Capture` needs nothing -- it reads the unfiltered log and
  calls `get_market()`, which is public market data, not portfolio-scoped.

Also recorded: **`balance_breakdown` on `get_balance()` ignores `subaccount`**
and is account-wide; only `balance` / `balance_dollars` are scoped. And scan
reports separate by *convention* only -- every `main` scheduled task pins an
explicit `--report-dir`, `longshot_scan.bat` pins none, and filenames carry
date/filter/type but **not** the profile.

### P1b -- the go-live criterion, deliberately not dated

Seven days of longshot scans (09-04 -> 09-10) have produced **one** trade row,
`dry_run_blocked`, zero fill. The 09-10 run approved **0 of 7** candidates, and
every rejection was on *edge*, not price: `4.0% < 8.9%`, `7.8% < 9.1%`,
`6.6% < 9.1%` -- R28's `NO_SIDE_MIN_EDGE_GLOBAL=0.08` plus fee.

So **`MIN_MARKET_PRICE=0.08`, the knob that defines this strategy, is barely
binding**, and flipping `DRY_RUN=false` today would change nothing except
downside. That is the actual argument against enabling it, and it is a better
one than caution.

The criterion (ROADMAP P1b) requires all three, in order: **(1)** resolve the
price floor -- 0.08 is contradicted by our own backtest (8-12c went 0W-36L,
-103.3%, across all six settled months) so decide 0.12 or 0.06; **(2)** read
**CLV, not ROI** -- at ~1 candidate/week this profile will never resolve ROI,
402 settles could not, and S8 is what makes CLV readable at n~20-30; **(3)**
then **pilot**, on S1b's branch-(A) shape -- max 2 open, <=5% of bankroll,
`UNIT_SIZE=1`, spread <=3c, held to ~40 settles.

Written now, while nothing is at stake, for the same reason S1b was: so the
call is not made on the first winning week. S10 retires it, the same way it
retires the S1 NFL freeze.

### Scheduled tasks

`Longshot-Scan` / `Email-Longshot-Scan` were deleted by the operator and
rebuilt as **`Longshot` (08:00)** and **`Email-Longshot` (08:20)** in
`\AI-Projects\Edge-Radar-MikesAILab\`, alongside every other job rather than in
a folder of their own. `InteractiveToken` as `mikes`, which the email task
requires -- `RESEND_API_KEY` is a user env var and a SYSTEM-run task cannot see
it. Verified by triggering `Email-Longshot` (`LastTaskResult 0`); the scan task
was not triggered, since its `.bat` was unchanged and already green at 10:37
and a full 15-sport scan costs Odds API credits for no new information.

- **`docs/longshot/README.md`** -- new "How the two strategies stay separate"
  and "When to enable live" sections.
- **`docs/ROADMAP.md`** -- P1b, in Priority 0a Phase 1 beside S1b.
- **`CLAUDE.md`**, **`docs/README.md`** -- pointers to the above.

---

## 2026-09-10 -- S8: CLV capture ships. It had never once been computed.

`kalshi_settler.py` derived `closing_price` from the **settlement-time** market
snapshot. A settled Kalshi market returns nothing meaningful for `last_price`,
so it evaluated to `0.0`; `0.0` is falsy; and the guard
`if closing_price and entry_price` short-circuited `clv` to `None`. Silently, on
every settle, since March: **426 settlements, 0 CLV**, with `closing_price`
split `{None: 259, 0.0: 167}`.

**The bug was never the arithmetic.** By settlement the closing book *no longer
exists* -- so no amount of care at that line could have recovered it. Reading a
settled market for a closing line is a category error, and the fix had to move
the measurement, not repair it. This matters because Priority 0a's whole thesis
is that **"CLV and Brier are the only readable signals at this sample size"**,
and one of the two has been returning nothing the entire time.

### Capture, not derivation

`scripts/kalshi/clv_capture.py` samples the book shortly **before** each open
position's event starts, and is scheduled every 5 minutes (`CLV-Capture`). Each
pass loads open, filled, real (non-dry-run) trades that have an
`event_start_time` and no capture yet, keeps those inside the window, reads each
ticker once, and writes the result. **A pass with nothing due makes zero API
calls**, which is what makes a 5-minute cadence affordable -- and cadence is
what buys coverage, which is what makes a mean CLV trustworthy.

`close_capture_reason` is one of `t_minus_5`, `t_zero_fallback` (a 10-minute
grace, because a job on a 5-minute tick cannot guarantee landing inside a
5-minute slot) or `missed`. Past that grace the book is in-play and is no longer
a *closing* line; capturing it anyway would quietly redefine CLV for exactly the
rows that were late.

### The three things it would have been easy to get wrong

- **A missing price is NULL, never 0.0.** A falsy sentinel absorbed by a
  truthiness guard is precisely how D1 hid for five months, and a zero close
  would additionally drag every mean CLV toward a fictitious `-entry_price`.
  `compute_clv` tests `is None` rather than truthiness, so a genuine 0.0 close
  on a collapsed market is computed rather than discarded -- the same bug shape,
  one level down. **Absent, `missed`, and captured are three different facts**
  and stay distinguishable: absent means capture never ran, `missed` means it
  ran and got nothing.
- **CLV is computed in bet-side probability space.** For a NO bet the close is
  the **NO** price, so a rising NO price reads as favourable movement exactly as
  a rising YES price does for a YES bet. Reading the close as a YES probability
  would invert the sign on the third of the book that is NO -- the S18 mistake,
  which has already been made once here. Verified live: a NO entered at 0.40
  against a book closing 0.50/0.62 gives **+0.16**, not -0.16.
- **The whole book is persisted**, not one scalar: `close_yes_bid`,
  `close_yes_ask`, `close_no_bid`, `close_no_ask`, `close_mid_bet_side`,
  `close_capture_at`, `close_capture_reason`. A lone midpoint makes the S14
  maker/taker A/B unreadable -- maker CLV genuinely improving is
  indistinguishable from the close being sampled on the other side of a wide
  book.

### `event_start_time` had to be captured at execution

The obvious source -- the ticker -- covers **35% of the book, and all of it is
MLB**: `ticker_scheduled_utc` needs an embedded `HHMM`, which only MLB tickers
carry. Every other sport is date-only (NHL 0/60, MLS 0/74, NCAAMB 0/56, NBA
0/32, WC 0/43). Keying capture off the ticker would have silently restricted CLV
to one sport, and the resulting mean would have been reported as the book's.

So the scheduled start comes from the matched **Odds API event's
`commence_time`**, stored in `details` by all three edge paths and persisted on
the trade row at execution. Futures carry none -- a season has no start -- and
are skipped rather than guessed.

### Concurrency: caught in review, not in production

`save_trade_log` overwrites the whole file, so a bare load -> mutate -> save
would eventually clobber a row appended by one of the ~10 scheduled execute
tasks -- and what it would lose is a **live position record** (M2's exact
failure mode). The venue reads run **outside** the cross-process lock, since
holding it across N network calls would block execution writes for as long as
Kalshi takes to answer; the captures are then re-applied **by `trade_id`**
against a fresh read taken **inside** the lock. A concurrent update to any other
field on the same row survives.

### There is nothing to backfill

CLV accrues from today. The 426 settled rows cannot be recovered, because the
books they would need stopped existing months ago. `--report` prints
`n_captured / n_settled` and currently reads **0/143**.

- **`scripts/kalshi/clv_capture.py`** -- new. `--dry-run`, `--window`, `--report`.
- **`scripts/kalshi/edge_detector.py`** -- `details["event_start_time"]` in all
  three edge paths.
- **`scripts/kalshi/kalshi_executor.py`** -- trade rows carry
  `entry_price_bet_side`, `event_start_time`, `close_capture_reason: None`.
- **`scripts/kalshi/kalshi_settler.py`** -- stops deriving `closing_price`;
  reads the captured close, and carries the whole closing book into the
  settlement row.
- **`scripts/schedulers/maintenance/clv_capture.bat`** + Windows task
  `CLV-Capture`, every 5 min. **Read-only at the venue** -- `get_market()` only,
  never an order. Verified `LastTaskResult 0`.
- **`tests/test_clv_capture.py`** -- 45 tests, including the D1 zero-vs-null
  trap, the S18 NO-side sign, and three concurrency tests. **1167 pass.**
- **Verified live** against `KXMLBGAME-26SEP131420PITCHC-PIT` in an isolated
  trade log: YES entry 0.40 -> close 0.44 -> **+0.04**; NO entry 0.40 -> close
  0.56 -> **+0.16**; the two closes sum to exactly 1.0000; a futures row was
  skipped with `reason=None` rather than given a fabricated close. The live
  trade log was not touched.

**Next:** S9 -- the reporting slice (mean CLV with bootstrap CI by sport /
category / side / price band / fee role), which is what turns this into a
decision signal. It should not be read until coverage is high: misses will not
be random, they concentrate in thin markets, and thin markets are where the bad
bets live, so low coverage biases the mean **optimistic**.

---

## 2026-09-10 (last) -- S20c: MLB's loss is expensive NO bets on totals, already gated -- and the "MLB has no book floor" claim was wrong

Investigating S20b's own closing item -- add `MIN_CONSENSUS_BOOKS_MLB`, since
"R29 built that floor for NBA only" -- turned up two facts that cancel the item
and diagnose MLB properly. **No code changed.** This is the reason not to write
the gate.

### 1. MLB is not unfloored. The claim came from S20 and S20b repeated it.

Every edge path already drops thin-consensus rows to `low`, which Gate 4.5
(`MIN_CONFIDENCE=medium`) rejects. What the paths do **not** share is where:

| path | `medium` requires |
|:--|:--|
| moneyline | `n_books >= 5` |
| spread | `n_books >= 3` **and** book range <= 4.0 |
| total | **`n_books >= 3`** |

R29 did not create MLB's floor problem by omission; it **raised NBA's** from 5
to 8 because F46 named NBA (-23.3% ROI over 32 bets). MLB was never considered
either way. Its floor is 5 on moneyline and **3 on totals** -- and a "consensus"
of 3 books is two books plus one.

**A floor of 8 was never portable to MLB anyway.** Only **9 books** ever arrive:
`fetch_odds_api` requests `regions=us`, and Pinnacle/Circa are `eu` (B7, still
blocked on a quota decision). In-season MLB game markets run **median 7 books
(min 1, max 9)**, so NBA's 8 demands 8 of a possible 9, and copying it to MLB
would reject **over half of all MLB games** -- not a floor, a shutdown.

### 2. MLB's loss is entirely totals, and it is a price problem, not a book problem

| MLB settled, by category | n | W-L | ROI | book floor |
|:--|--:|:--|--:|--:|
| moneyline | 109 | 47-62 | **+1.2%** | 5 |
| spread | 2 | 0-2 | -100.0% | 3 |
| **total** | **42** | **30-12** | **-12.8%** | **3** |

Moneyline -- two thirds of the block -- is **positive**. The whole of MLB's
-6.4% headline sits in totals, and totals wins **71% of the time while losing
12.8%**. That combination cannot be a consensus problem: you do not lose money
winning 71% of your bets unless you are paying too much for them.

You are. **33 of 42 MLB totals are NO bets, median entry price 0.80, and 35 of
42 were bought at >= 0.75c.** That is the F4/R28 NO-side drag landing in the
exact band where NO bleeds worst (F4: NO at/above 50c is -11.3% over 68 bets).

### 3. It is already gated -- verified, not assumed

`MAX_MARKET_PRICE=0.75` (Gate 3.55) shipped 2026-09-03. Checked for leaks: of
the four MLB totals with a game date on/after 09-03, the two at **0.81 and
0.79 were entered on 09-03 itself**, before the value was set, and the only
ones since are **0.74 and 0.75 -- both legal** (the gate rejects above 0.75).
No leak; the gate does what it says. F4's `NO_SIDE_KELLY_PRICE_CEILING=0.50`
damps the same population from the sizing side.

MLB by era, though the post-gate samples are far too small to confirm anything:

```
before F4 (pre 08-25)      n=143  W-L 69-74  net  $-10.35  ROI  -6.4%
F4 .. Gate 3.55            n=  6  W-L  5-1   net  $ +1.60  ROI +25.5%
since Gate 3.55 (09-03+)   n=  4  W-L  3-1   net  $ -0.55  ROI -10.1%
```

### Why no gate was written

`MIN_CONSENSUS_BOOKS_MLB` would gate a cause that could not be found, stacked on
a cause already gated, using a threshold that cannot be justified -- `n_books`
was never recorded, so there is still no evidence linking book width to MLB
outcomes in either direction. The instrument shipped this morning (S20b); a few
weeks of rows answer it properly. **Adding a live gate on a disproved premise is
the more expensive mistake**, and the same reasoning that keeps a cold-start
segment in pilot rather than under a hardcoded floor (S1).

**The real value here is that MLB is now diagnosed.** It has been carried since
2026-08-31 as the sport with a Brier "worse than a coin flip" and an unexplained
-6.4%, first blamed on quota starvation (S20, unsupported per S20b) and then on
the model. It is neither: it is one market type, bought on the wrong side at the
wrong price, by gates that have since been tightened. MLB moneyline was never
broken.

**Corrected above:** S20b's closing line ("MLB has no `MIN_CONSENSUS_BOOKS_MLB`
... so there is still no limit on how thin MLB consensus may get") repeated
S20's claim and is wrong. MLB's limit is 5 on moneyline and 3 on totals.

### Open, and now correctly scoped

- **Totals floors at 3 books while moneyline floors at 5, with no recorded
  reason** -- and totals is where the money went. Raising it to 5 is a
  consistency fix, not an evidenced one; it should wait on recorded `n_books`
  like everything else here.
- **Re-check MLB after ~20 more settled totals** to see whether Gate 3.55
  actually fixed it. n=4 proves nothing yet.
- **B7 remains blocked on an operator quota decision** and gates all of this:
  adding `eu` books changes what any book count means.

---

## 2026-09-10 (later still) -- S20b: MLB's underperformance is not quota starvation, and `n_books` was never recorded

S20's surviving question, after the 09-09 retraction, was whether MLB's **-6.4%
ROI and 0.2917 Brier** -- the only sport flagged worse than a coin flip -- were
caused by a book consensus thinned by Odds-API quota exhaustion, rather than by
the model. Its own *Verify* line specified the check: *"log `n_books` on every
MLB edge and check whether the failure days coincide with the losing trades."*

**That check was never possible.** `n_books` is computed at scan time -- it sets
`confidence` and feeds the composite in all three edge paths -- and then
discarded. It appears in **no** trade row and **no** settlement row, and never
has. The instruction to "log `n_books`" read like a small addition to existing
telemetry; there was no telemetry.

### What the logs did allow

Odds-API key-exhaustion lines are timestamped, so exhaustion **days** are
recoverable even though book width is not. Splitting MLB's settled bets by
whether their game day carried an exhaustion event is a proxy -- and a weak one,
since an exhaustion line dates the **scan**, not the book behind any one edge.

First, the exhaustion record itself is larger than S20 described. S20 counted
**166 events in August**. Across the full log history it is **577 events on 37
distinct days, 2026-04-18 → 2026-09-10**, and **every single one is
`baseball_mlb`** -- no other sport appears, ever, in six months. The pool size
at the moment of failure was **4 keys or 1 key**, never 12 or 14: by the time
MLB was refused, the pool had already collapsed, which is the S26 mechanism.

### The answer: no evidence, and the sign does not hold

| MLB settled, n=153 | n | W-L | ROI | model-market Brier |
|:--|--:|:--|--:|--:|
| Exhaustion day (±1d) | 50 | 30-20 | **-11.2%** | +0.0437 |
| Clean day | 103 | 47-56 | **-2.0%** | +0.0276 |

The pooled gap looks like the hypothesis -- until it is tested:

- **ROI difference -9.2%, 95% CI [-47.2%, +30.4%] -- straddles zero.**
- **Brier-gap difference +0.0161, CI [-0.0278, +0.0614] -- straddles zero.**
- Per month, exhaustion days are **worse in 3 of 6 months and better in 3 of 6**.

A pooled difference whose sign flips stratum to stratum is not a finding. This
repo has been here before: `correlation_check.py` produced a pooled rho of
+0.181 that was Simpson's paradox and inverted per stratum, and the rule taken
from it was to judge against strata rather than the pool. **The quota-starvation
explanation for MLB does not survive that test.**

**A first pass got the opposite answer and was wrong.** Dating entries through
`trade_id` against the trade log gave exhaustion days **+12.7%** and clean days
**-25.0%** -- an apparent refutation. The trade log holds **193 rows against 426
settlements**: it has been pruned, so only recent rows resolve, and two thirds
of settled MLB rows silently dropped out of the comparison. Dating from the game
date embedded in the ticker recovers **all 153** and reverses the result. A join
that quietly drops most of its rows is worse than no join.

**What this does not say.** It does not clear the MLB model -- the model is worse
than the market in *both* arms (+0.0437 and +0.0276, both positive), consistent
with F3. It says the *quota* explanation is unsupported, so the MLB Brier
problem should be treated as a model question rather than a data-supply one.
n=50 on the suspect arm is small, and the proxy is coarse; the direct test is
now possible for the first time and should replace this.

- **`scripts/kalshi/kalshi_executor.py`** -- trade rows carry `n_books`.
- **`scripts/kalshi/kalshi_settler.py`** -- carried into the settlement row, so
  book width can be joined to **outcomes**, the only place the question resolves.
  Absent on pre-2026-09-10 rows: **readers must treat missing as unknown, never
  as zero books**, or the whole back-catalogue reads as thin.
- **`scripts/backtest/book_width_check.py`** -- new. `--proxy` runs the
  exhaustion-day analysis above; the default splits on recorded `n_books` and
  becomes the real answer once rows accumulate. Both report ROI and the
  model-minus-market Brier pair (S18) with bootstrap CIs, and both print the
  per-month sign check, because the pooled number is exactly where this goes
  wrong. Dates from the log **line**, never the filename -- filenames are UTC
  and timestamps are local, so an evening PDT run lands in tomorrow's file.
- **`tests/test_book_width_check.py`** -- 30 tests: the UTC-filename trap, that
  a missing `n_books` is unknown rather than zero, that undatable rows are
  excluded rather than padding the control arm, and that a $0 stake yields
  `None` rather than a clean 0.0%. **1122 pass.**

**Still open:** re-run the default (non-proxy) mode once settled rows carry
`n_books`.

> **Corrected same day by S20c.** This entry originally closed by repeating
> S20's claim that "MLB has no `MIN_CONSENSUS_BOOKS_MLB` ... so there is still
> no limit on how thin MLB consensus may get". **That is wrong.** Every path
> already drops thin rows to `low`, which Gate 4.5 rejects: MLB's limit is
> `n_books >= 5` on moneyline and `>= 3` on totals. R29 did not leave MLB
> unfloored -- it *raised NBA's* from 5 to 8. See S20c, which also finds MLB's
> loss is entirely expensive NO bets on totals, already gated by Gate 3.55.

---

## 2026-09-10 (later) -- S28: the NFL Week 1 review's ROI has always been $0.00, and its S4 claim was two weeks stale

`nfl_week1_review.py` fires **once, unattended, on 2026-09-15, with `--apply`**,
and may rewrite `MIN_EDGE_THRESHOLD_NFL` in the live `.env` (S1b, pre-declared
2026-08-26). Three defects, all found by *running* it rather than reading it.

**1. `staked` was always exactly $0.00, so ROI was always `+0.0%`.**
`roi_context()` summed `cost_dollars` from the settlement log. That field does
not exist there -- the settler writes **`cost`**; `cost_dollars` is the *trade
log's* name for it. **426 of 426 settlement rows lack it**, so the sum was $0.00
for every possible input, and `roi` then fell through its own
`if staked else 0.0` guard to a clean, plausible **`+0.0%`**. On 09-10 it printed
`staked $0.00   net $-2.24   ROI +0.0%` without complaint. This has never once
produced a real number since the script was written. Now reads `cost` (falling
back to `cost_dollars` so either row shape works), and **`roi` is `None` when the
stake is unreadable** -- the report prints `ROI n/a` and names how many rows
lacked a stake. A zero indistinguishable from a real result is worse than a gap
in a report that gates a live-money decision. Correct output: `staked $2.12
net $-2.24   ROI -105.5%`.

**2. It asserted `MAX_SEGMENT_EXPOSURE_PCT` "does not exist".** A string literal
written before **S4 shipped on 2026-08-26**. The cap has been live at **0.33**
ever since, so for two weeks the report was set to tell the operator that
*nothing mechanically stops NFL exposure re-accumulating* -- inside the document
deciding whether to unfreeze NFL. Now `_segment_cap()` reads the live value and
`_segment_cap_paragraph()` states it three ways: the real cap when one is set,
the original warning **restored** when it is 0/OFF, and an explicit "could not be
read -- check `.env`" otherwise. A number that comes from `.env` cannot drift
away from `.env`.

- **`_segment_cap()` loads `.env` itself.** Nothing else in the script reads
  config -- it rewrites `.env` as text -- so no entry-point dotenv load existed
  here. Without one `get_config()` returns the **code default (0)**, which reads
  as "no cap configured" while the live file says 0.33: the same false statement,
  reached a different way. Caught because the first fix printed `0 -- OFF`
  against a `.env` that plainly said `0.33`.

**3. Branch C conflated "not enough bets" with "not enough readable bets".**
`decide()` reported `len(rows)`, which counts only settlements carrying a model
probability, as "only N settled NFL bets" -- so rows dropped for a missing
`fair_value` read as bets that were never placed. It now reports both counts and
the dropped total. This matters on the 15th: **23 of 31 NFL rows project as
usable**, clearing the >= 20 bar by 3, with 8 dropping out. Which of those two
numbers is short changes what the operator should do.

**The pre-declared branch logic is untouched** -- thresholds, branches, the
capped 0.08 pilot floor and the report-only default are all unchanged and now
covered by tests. Only the reporting around the decision was wrong.

- **`scripts/backtest/nfl_week1_review.py`** -- `roi_context()` reads `cost` and
  returns `roi: None` + `missing_cost`; new `_segment_cap()`,
  `_segment_cap_paragraph()`, `_settled_nfl_count()`; module docstring corrected.
- **`tests/test_nfl_week1_review.py`** -- new, 18 tests. Covers the exact
  `cost_dollars` row shape that produced the silent zero, that an off cap still
  warns, that the report never claims a cap it does not have, and that
  `--apply`-less runs never write `.env`. **1092 pass.**
- **Verified:** report-only run reproduces `ROI -105.5%` and `33% of equity`;
  `.env` still reads `MIN_EDGE_THRESHOLD_NFL=1.0`; verdict remains BRANCH C.

---

## 2026-09-10 -- P1: strategy profiles replace the forked Longshot repo

`Repos/Private/Other_Apps/Edge-Radar-Longshot` was a second checkout of this repo,
created 2026-09-04 to run a longshot/futures strategy whose results could be
compared against this one over time. It is retired. The strategy lives here now,
as a **profile**: `--profile longshot` overlays `.env.longshot` on the base
`.env` and routes every Kalshi call to **subaccount 1**.

**The fork was buying one thing that a fork cannot actually provide.** The
bankroll is not in the repo -- it is in the Kalshi account. Two checkouts
pointing at one API key draw on one balance, and each repo's `MAX_DAILY_LOSS`
and exposure gates see only their own activity, never the combined draw-down.
What isolates money is a **subaccount** (exchange-enforced separate wallet under
one login, Advanced API tier), which the fork itself discovered and shipped on
2026-09-07. That is an account-level fact. One codebase addresses it fine.

**Measured before deciding.** The fork's real code delta was ~74 lines across
three concerns, none of them strategy: subaccount routing, a futures-specific
Gate 6 cap, and a `dry_run` logging fix. Its *strategy* delta was two env vars
(`MIN_MARKET_PRICE` 0.08 vs 0.10, `MAX_PER_EVENT_FUTURES` 3 vs 2) -- and its own
ROADMAP header already recorded that the backtest **contradicts** the 0.08 floor
(the 8-12c band it admits went 0W-36L, -103.3% ROI over six months).

**Six days of drift had already produced a live defect in each direction:**

- The fork still mapped `KXNCAAFBGAME` and had no NCAAF spread/total wiring --
  the bug fixed here on 2026-09-03 and verified against 3,999 open markets. It
  was scanning **zero college football**, silently, in September.
- It was missing S26 (odds-quota TTL) and S27 (the Polymarket resting-order
  call), plus their tests.
- This repo was missing the fork's `dry_run` fix: `kalshi_executor.py` hardcoded
  `"dry_run": False` on **every** trade row, so a dry-run row read
  `"status": "dry_run_blocked", "dry_run": false` and nothing downstream could
  separate simulated rows from real ones.

That is the fork tax, on a delta of two env vars, in under a week.

**The overlay is also strictly safer than the fork was.** The fork ran
`MAX_OPEN_EXPOSURE_PCT=0`, `MAX_SEGMENT_EXPOSURE_PCT=0`,
`MAX_DAYS_TO_EVENT_FOR_GAME_MARKETS=0`, `MAX_BET_SIZE=100`,
`MAX_DAILY_LOSS=250` and no NFL freeze -- not by decision, but because nobody
re-tightened the shipped defaults after cloning, while its ROADMAP recorded the
posture as "conservative, matches main repo, no change needed". Under a profile
those five come from the base `.env` automatically, along with every future fix.
Verified after the merge: both profiles resolve `max_bet_size=8`,
`max_daily_loss=30`, `exposure=0.50/0.33`, `max_days=14`, `nfl_floor=1.0`.

**And it is better evidence than two repos gave.** Comparing the books now
compares strategies, not codebase versions -- identical fee model, odds cache,
calibration and gates on both sides.

### Profiles

- **`app/config.py`** -- `apply_profile_overlay()`, called from `get_config()`
  before the Config is built. Reads `EDGE_RADAR_PROFILE`, applies
  `.env.<name>` over `os.environ`. Applied here rather than at the ~18
  `load_dotenv()` call sites: it is the one place every entry point already
  routes through, and `load_dotenv()` does not override variables already set,
  so a child process inherits the overlay intact. `System.profile` carries the
  active name. **Fails closed** -- a missing overlay file raises rather than
  falling back to the base `.env`, because the base `.env` is the live-money
  wallet and a typo'd `--profile longshto` would otherwise run one strategy's
  intent against the other's bankroll, live. Same reasoning as S3's venue check.
- **`scripts/scan.py`** -- `--profile <name>` / `--profile=<name>`, consumed by
  the dispatcher and passed to the scanner as an env var. Not forwarded as a
  flag: every scanner would need an identical argparse entry, and one that
  forgot would silently run the base `.env`.
- **`scripts/doctor.py`** -- prints the active profile and subaccount first.
  Every figure below it (balance, shards, positions, exposure) is
  subaccount-scoped, so the report is unreadable without knowing which wallet.
- **`.env.longshot.example`** -- tracked template; `.env.longshot` is gitignored
  like `.env`. `.gitignore` now un-ignores `.env.*.example`.

### Ported from the fork

- **`KALSHI_SUBACCOUNT`** (0-63, default 0 = primary, validated) threaded
  through every balance / position / order / fill / settlement / cancel call in
  `kalshi_client.py`, plus `get_account_limits()`, `upgrade_to_advanced_tier()`
  and `create_subaccount()`.
- **`get_shard_balance(exchange_index)`** -- and this fixes an X1 bug here too.
  `balance_breakdown` is **account-wide and ignores `subaccount`** (verified
  2026-09-08: as subaccount 1 holding $40 on shard 0, it reported
  `{0: 109.79, 3: 13.76}`). `shard_balances()` read that field, so on any
  non-zero subaccount the funding guard saw the *primary's* cash, found no
  shortfall, and would approve an order the venue rejects `404 user_not_found`
  -- failing **open** in exactly its own case. It now takes the shards the
  decision needs and reads each scoped; it returns `{}` and fails open only
  when the client cannot answer at all.
- **`AUTO_SHARD_TRANSFER` is checked after the cap/source tests and skipped in
  dry runs.** A dry run moves no money, so the flag governing whether we may
  move money has nothing to say about it; checking it first refused every
  shard-3 candidate before it could be simulated, logging un-settleable `error`
  rows instead of dry-run bets. Live behaviour is unchanged -- with
  `dry_run=False` the verdict is identical either way.
- **`MAX_PER_EVENT_FUTURES`** -- Gate 6 cap for `category == "futures"`,
  defaulting to `MAX_PER_EVENT`. Futures outcomes partition one event rather
  than doubling down on it. +3 tests.
- **`"dry_run"` on the trade row** is now `api_status == "dry_run_blocked"`.
- **`tests/test_shard_funding.py`** -- pins `dry_run=False` via the live config.
  These tests read `dry_run` from the config, not a module global, so on any
  clone with `DRY_RUN=true` they silently took the `[dry-run]` branch and
  asserted nothing about transfers.

### Trade-log tagging

- **`kalshi_executor.py`** -- every row carries `"profile"`, mirroring the PM2c
  `"venue"` tag one level up. Absent on pre-P1 rows, so **readers must default
  to `"main"`**. This is what lets one trade log hold both books.

### Verified

- 1069 tests pass (1044 existing + 25 new profile tests).
- `doctor.py` on both profiles against the live exchange: main = subaccount 0,
  $81.70, shards `0=$68.89 / 3=$12.82`, `DRY_RUN=false`; longshot = subaccount
  1, $40.00, shard `0=$40.00`, `DRY_RUN=true`. Two wallets, one codebase.
- `--profile longshto` refuses to run and names the missing file.
- Futures scan under `--profile longshot`: 30 markets, 0 above the floor.

### Still open (carried from the fork's ROADMAP, not decided here)

- **The 0.08 floor is contradicted by our own backtest.** The recommendation on
  record is 0.12 or 0.06, not 0.08, and `spread`-as-category (23% win, +31.7%
  ROI, n=111) as the better-evidenced route to a longshot profile. Carried over
  as-is so the merge changed no strategy; resolve before this profile goes live.
- Longshot remains `DRY_RUN=true`. Nothing here turns it on.

---

## 2026-09-09 (later) -- S27: Gate 2b's resting-order call ran on a venue that has no orders endpoint

`kalshi_executor.log` carried a WARNING every single day at 09:40:

```
Resting-order exposure unavailable (GET /v1/orders -> 501: {"code":12,
"message":"The server was unable to process your request."}); Gate 2b will
under-count by any open resting order
```

Read as a Kalshi problem, it looks alarming -- Gate 2b is the only gate that
measures a standing total, and this says it is blind. It is not a Kalshi problem.
`/v1/orders` is the **Polymarket US** path (`polymarket_exec_client.py:280`);
`/portfolio/orders` is Kalshi's. 09:40 is `Daily-Polymarket-Execution` (task #21).
Kalshi's own listing works -- verified live the same day, `risk_check.py` returned
one resting order from the funded account.

`execute_pipeline` is venue-agnostic and takes whatever client it is handed. The
R4 janitor two lines above the exposure call was already gated `venue == "kalshi"`
("it parses Kalshi order shapes"); **S21's `resting_exposure()` was not**, so every
Polymarket run since it shipped on 2026-08-31 asked a venue that answers 501 with
gRPC code **12 UNIMPLEMENTED** -- deterministic, not transient, and it will never
succeed. The call could only ever fail open and warn.

**The under-count is $0.** Polymarket has never filled an order -- `kalshi_trades.json`
holds 0 PM rows, every candidate to date stops at Gate 3 -- so there are no resting
PM orders to miss. Nothing is lost by not asking.

**The cost was the warning, and that is the real defect.** A line that fires
unconditionally on every run is the S25 failure mode exactly: a suite with standing
failures stops being read, and so does a log. This one had been training the reader
to skip the string `Resting-order exposure unavailable` since 08-31 -- the same
string Kalshi would use if its listing ever *did* break, which is the case Gate 2b
actually needs someone to notice.

- **`scripts/kalshi/kalshi_executor.py`** -- the exposure call now sits behind
  `if venue == "kalshi"`, matching the janitor's guard directly above it. Other
  venues take `(0.0, {})` and log one INFO line naming the limitation, so the blind
  spot stays on the record without crying wolf. Drop the check if Polymarket ever
  ships an order listing; `resting_exposure()` itself is already generic.
- **Verified:** `polymarket_futures_edge.py:531` passes `venue="polymarket"`;
  `prediction_scanner.py` passes no venue and correctly defaults to Kalshi, which
  is right -- it trades Kalshi prediction markets. Runtime confirmation lands on the
  next 09:40 run.
- **Tests:** `tests/test_resting_exposure_venue.py` pins S21's fail-open contract
  (a venue error, and a client with no `get_orders` at all, both return `(0.0, {})`
  rather than raising) -- the behaviour that makes failing open safe. The guard
  itself is deliberately untested: reaching it needs a full authenticated venue
  round-trip, the janitor's identical guard has no test either, and a harness built
  only to prove an `if` is scaffolding. 1041 pass.

## 2026-09-09 -- A cached Odds API zero was believed forever, hoarding one key

The operator questioned a report that 12 of 14 Odds API keys were exhausted. They
were right to: a live probe found **5154 requests actually available**, with nine
keys sitting at a full 500. The cache was wrong, and had been for weeks.

`data/cache/odds_api_quota.json` stored a bare `{key: remaining}` map with **no
timestamps and no expiry**, while `get_current_key()` returns the first key not
cached at zero. So as long as *one* key had quota left, the walk stopped there and
every drained key was never contacted again -- their monthly resets came and went
unobserved, and the zero persisted indefinitely. The
`if every key is exhausted, return the current slot anyway` fallback exists for
exactly this, but only fires when **all** keys read zero, which never happened.
The pool silently collapsed from 14 usable keys to one: key `...deb642` was
carrying the entire workload at 416 remaining while `futures_edge` logged
`1 requests remaining` on the morning of 09-09. Whenever a reset lands, a zero is
only ever a fact about the past -- it can never be safely cached without a date.

**This reopens S20** (*CHANGELOG 2026-09-03*), which closed the August quota
problem as "the monthly reset" on the strength of **zero** `All N Odds API keys
returned 401/429` errors in the 09-01..09-03 logs. That evidence is confounded by
this bug: with `...deb642` holding quota, the walk never reached a cached-zero key,
so no 401 could be logged **whether or not any key had reset**. Silence was the
bug's signature, not proof of recovery. S20's own *Verify* line called for exactly
the `--live` probe that was never run ("to separate a stale cache from real
exhaustion"); running it on 09-09 is what surfaced this. S20 was right that the
keys were not permanently dead, and right to stand down the alarm -- but its stated
mechanism does not follow from what it looked at.

**The reset model is now an open question, and this fix does not depend on it.**
S20 states the quota resets on the 1st. The 09-09 probe found *heterogeneous*
`x-requests-used` on the same day -- 0 (nine keys), 84, 263, 499, 500 -- which a
synchronized 1st-of-month reset does not obviously explain, since the keys reading
263 and ~500 used were cached at zero and should have been skipped all month.
`rotate_key()` was the obvious candidate for a bypass path and is **ruled out** --
all three call sites discard its return and re-enter via `get_current_key()`. What
remains is benign: `_remaining` is per-process state seeded from the cache, a key
*absent* from it reads as usable, and once every key reads zero in-process the
documented fallback returns the current slot anyway -- so a reset is re-discovered
one key at a time, for whichever slot `_current_index` holds. That fits the spread
under **either** model, so the used counts do not discriminate between them.
**Not resolved here, and deliberately not asserted either way** -- logged as
**S26b**. The TTL is correct under both models.

- **`scripts/shared/odds_api.py`** — cache entries are now
  `{key: {"remaining": N, "checked_at": <iso>}}`. `_load_quota_cache()` drops a
  zero older than `_ZERO_TTL_HOURS` (24) so it reads as *unknown* and the key is
  probed again; `report_remaining()` and `mark_exhausted()` stamp every write.
  Non-zero readings do not expire — they are refreshed on every use anyway. The
  loader still accepts the legacy bare-int shape; a legacy zero carries no date,
  so it expires by definition, which is what migrates the live cache on first read.
  Worst case is one wasted request per drained key per day.
- **`scripts/schedulers/maintenance/odds_keys.bat`** (gitignored) + **`odds-keys`
  profile** in `install_windows_task.py` — new `WeeklyOddsKeyProbe` task, Sun 6 PM,
  runs `check_odds_keys.py --live`. 14 requests/week against a 500/key/month
  allowance. The TTL re-probes stale zeros on its own; this task is what catches a
  key going bad **before** a scan needs it, and keeps the whole pool's numbers
  honest rather than only the keys in active use. Installed and triggered live.
- **Rejected: selecting the key with the most remaining.** Proposed first, then
  dropped — it does not fix this bug (a key cached at 0 still ranks last and is
  still never picked while any non-zero key exists) and it fights the `tried:` set
  in `edge_detector.py`'s retry loop, where snapping back to the best key after a
  429 rotation would end the loop early.
- **Also found:** key `...44681c` returns **401**. It is the only key in the set
  with an uppercase character in an otherwise all-lowercase-hex list — likely a
  transcription error in `ODDS_API_KEYS` rather than a revocation. Not fixed here;
  needs checking against the source. Keys `...a630b6` / `...8e4b0a` are genuinely
  drained (500/499 used).

Tests: `tests/test_odds_quota_ttl.py` (new, 6 cases incl. the end-to-end
"a drained key comes back into rotation"); `tests/test_odds_api.py` updated —
three cases asserted the old bare-int format directly.

## 2026-09-07 -- College football never scanned: wrong Kalshi series ticker

The operator noticed zero college-football bets in the trade log and asked why.
Every scan for NCAAF returned 0 markets, silently, since launch — not a risk-gate
rejection, not an edge/threshold issue, just fetching a ticker prefix that doesn't
exist. `FILTER_SHORTCUTS["ncaafb"]` and `KALSHI_TO_ODDS_SPORT` both used
`KXNCAAFBGAME`; Kalshi's real series is `KXNCAAFGAME` (no second `B` — football,
unlike basketball, has no gender split requiring one). `KXNCAAF` (no `GAME` suffix)
does exist but is the CFP championship futures market, unrelated to weekly games —
querying it returned real markets, which made the bug easy to mistake for "working."
The no-filter scheduled scans (which walk `KALSHI_TO_ODDS_SPORT`) never fetched a
single college-football market either, for the same reason.

Also added spread and total wiring, which never existed for this sport (only
moneyline was ever mapped) — Kalshi lists `KXNCAAFSPREAD`/`KXNCAAFTOTAL` now,
confirmed live with real Sept 2026 game markets.

- **`scripts/kalshi/edge_detector.py`** — `CATEGORY_MAP`: `KXNCAAFBGAME`→`KXNCAAFGAME`
  (game), added `KXNCAAFSPREAD`/`KXNCAAFTOTAL`. `KALSHI_TO_ODDS_SPORT`: same fix,
  same additions, all → `americanfootball_ncaaf`. `FILTER_SHORTCUTS["ncaafb"]` now
  lists all three tickers instead of the one broken one. The stdev lookup
  (`_PREFIX_TO_SPORT["KXNCAAF"]`) and sport-name detection
  (`ticker_display._detect_sport`, keyed off `KXNCAAF`) were already correct —
  they matched on the right prefix even though nothing ever fetched a market that
  had it.
- **Verified live, preview-only (no `--execute`):** `KXNCAAFGAME` + `SPREAD` +
  `TOTAL` return 3,999 open markets today (was 0); a `--filter ncaafb` scan finds
  15 opportunities above the 3% floor (11 spread, 4 total; several score >= 6.0
  and would clear Gate 4). No moneyline candidates cleared edge this scan.
- **Not touched:** no `.env` override exists for NCAAF (`MIN_EDGE_THRESHOLD_NCAAF`
  etc. are all commented out in `.env.example`), so it runs on global defaults
  like NHL/soccer — same as intended once the tickers actually resolve.

Docs: `docs/kalshi/README.md`, `docs/kalshi/kalshi-sports-betting/SPORTS_GUIDE.md`
(spread/total columns), `tests/test_time_to_event_gate.py` (fixture ticker).

## 2026-09-07 -- Account-growth graph made private, reversing 2026-05-31

The Kalshi account-growth graph (real balance, deposits, settled P&L, open-position
value in dollars) was being published to the public `Edge-Radar` repo and served on
GitHub Pages at `edge-radar.mikesailab.com` — a deliberate choice from *2026-05-31
"Account-Growth Graph on the Pages Site"*. The operator reconsidered: the repo is
public and the graph exposes real personal financial figures, obscurity via an
unguessable filename (`account-40c3eb1d3d3cb9c4e07fee61.html`) plus `noindex` is not
the same as access control.

- **`scripts/schedulers/automation/refresh_account_graph.py`** — dropped `publish_local()`
  (copy into `.claude/html/`) and `push_to_master()` (the `gh` contents-API push that
  triggered the Pages deploy). The script now only pulls the live snapshot and
  regenerates HTML/PNG into `docs/my-documents/account-graph/latest/`, which was
  always gitignored. No scheduled-task change needed — `WeeklyAccountGraph` invokes
  the script by path; the publish behavior lived entirely inside the script.
- **`.claude/html/account-40c3eb1d3d3cb9c4e07fee61.html`** — `git rm`'d. It had been
  tracked despite a `.claude/html/account-*.html` gitignore rule already existing
  (added after the file was first committed, so it never actually took effect).
- **`.claude/html/index.html`** — removed the "Live P&L / Account growth chart" button
  from the hero; the target no longer exists.
- **Known gap, not yet resolved:** the file's git history on `master` still contains
  every past weekly snapshot with real dollar figures — removing it from `HEAD` does
  not scrub prior commits from a public repo. Rewriting history (`git filter-repo` +
  force-push) was deliberately not done in this pass; needs an explicit decision since
  it invalidates any existing clones/forks.

Docs: `docs/task-schedules/README.md` (task #18 purpose/output updated).

## 2026-09-04 -- risk_check.py no longer re-derives Gate 1/2 comparisons

Finding #2 from the [2026-09-03 gate-consolidation review](my-documents/repo-reviews/2026-09-03-risk-gate-consolidation-review.md):
`risk_check.py --gate` re-implemented the daily-loss and open-positions
comparisons independently of `kalshi_executor.size_order`, which could
silently drift if either file's threshold logic changed without the other.
Low blast radius (it's the human-facing preflight in
`prompts/portfolio/morning-routine.md` / `status-check.md`, not the automated
scheduler path -- scheduled runs call `execute_pipeline` directly), but
mechanical and safe to fix regardless.

Extracted `daily_loss_breached()` and `positions_at_cap()` as the shared Gate
1/2 predicates in `kalshi_executor.py`; `size_order` and `risk_check.py`
(`is_daily_limit_breached`, `run_gate_check`) both call them now instead of
each holding its own copy of `<=`/`>=` against the threshold. No threshold
values or reject behaviour changed -- purely removes a second, independently
editable copy of the same comparison. 6 new tests (`TestSharedGatePredicates`
in `tests/test_risk_gates.py`).

---

## 2026-09-03 -- New Gate 3.55: cost/payout ratio ceiling (`MAX_MARKET_PRICE`)

Operator request: no bet where cost exceeds 75% of the potential payout -- a
76c bet to win $1 (76% ratio) should not go through; 75c (75%) should. A
Kalshi/Polymarket contract pays exactly $1 if it wins, so market price *is*
the cost/payout ratio (already side-relative per S18 -- a NO bought at 73c
stores `0.73`, so no side-flipping is needed here either). Added as Gate 3.55,
directly below the existing R7 floor (`MIN_MARKET_PRICE`) it mirrors: same
config dataclass, same module-level-global/reload_risk_config wiring, same
`preflight_gate_status` label pattern (`"price-hi"` next to `"price"`). Code
default `MAX_MARKET_PRICE=1.0` (off -- a contract's price can't exceed $1
anyway, so a 1.0 ceiling never rejects); live `.env` sets `0.75`. No settled
evidence behind the 75% number -- pure operator preference, unlike R7's
14-day-review-backed floor.

---

## 2026-09-03 -- S20 closed: the Odds API quota problem was the monthly reset

S20 (2026-08-31) found 10 of 12 keys exhausted and 166 August `All N Odds API
keys returned 401/429` errors, all `baseball_mlb`. As of 09-03: **14 keys**
(operator added 2), and **zero** exhaustion errors in `logs/edge_detector_*`
for 09-01 through 09-03, against 4-48/day through August. The Odds API quota
resets on the 1st of the month -- the 10 exhausted keys came back full on
09-01, and the 2 added keys widen the margin going forward. No code change;
confirmed by log inspection, not by a `--live` probe.

**Still open, separately:** whether MLB's -6.4% ROI / 0.2917 Brier (flagged
worse than a coin flip in the 30d calibration report) was actually caused by
quota-thinned consensus, or is a real model problem now unmasked. S20 could
not distinguish the two and neither does this closure -- it only rules out
*ongoing* quota starvation as of this month. Revisit if MLB's numbers don't
improve now that its books aren't getting starved.

---

## 2026-08-31 (later) -- S25: the suite goes green, and S21: resting orders reach Gate 2b

### S25 -- five failing tests that everyone had learned to read as "known failures"

`make test` had been red since **2026-08-27**, discovered four days later during
an unrelated review. Cause: `KXMLBGAME-26AUG271900NYYBOS-NYY`, a fixture ticker
in `test_exposure_gate.py`, embeds a **start time**. At 7pm on the 27th it
drifted into the past, `is_game_started()` began returning True, and Gate 4.8
rejected the order five tests were making assertions about. Nothing changed in
the code. The clock moved.

That is the **third** time wall-clock coupling has broken this suite -- S1 broke
four tests by freezing NFL, S5 broke 126 by enabling the time-to-event cap -- and
the first time it went unnoticed, because a suite with standing failures stops
being read.

The repo already had both correct idioms, in `test_risk_gates.py`:

```python
STARTED_TICKER  = "KXMLBGAME-20JUN011840CWSMIA-MIA"   # year 20 -- always past
UPCOMING_TICKER = "KXMLBGAME-99JUN011840CWSMIA-MIA"   # year 99 -- never arrives
```

The fixture is now year 99, and `tests/test_fixture_hygiene.py` makes the
convention enforceable: no fixture ticker carrying a **start time** may sit
within 90 days of today, so a bomb is flagged a quarter before it detonates
rather than on the morning it does. Verified by planting one and watching it
fail.

**Scoped deliberately.** An earlier draft flagged every dated ticker and lit up
~50 fixtures that cannot affect a verdict -- `test_ticker_display` in particular
passes explicit `now=` values and *needs* real dates. It is also forward-looking
only: an already-past ticker has either broken the suite and been fixed, or
provably cannot reach a gate. A check that cries wolf gets deleted.

**A correction worth recording.** The review that opened this work claimed nine
fixtures would detonate on 2026-09-13, the day NFL Week 1 settles and two days
before the S1b unfreeze review. That was wrong: the Sept-13 tickers are
`KXNFLGAME-26SEP13MIALV-MIA` -- **date only, no HHMM** -- and `is_game_started`
deliberately returns False rather than guess an unknown kickoff. They were never
Gate 4.8 bombs. The urgency was right, the mechanism was not. A probe that ran
the suite against a shifted clock is what settled it; `test_fixture_hygiene`
now pins the distinction so nobody has to re-derive it.

**1020 tests pass, zero failures** -- green for the first time since 08-27.

### S21 -- a resting order commits real cash and reports $0

Gate 2b measures a standing total, and a resting order was invisible to every
input it had:

| | |
|:--|--:|
| not a position, so `exposure_from_positions` returns | **$0.00** |
| its cash has already left `balance` | **-$2.43** |
| ...but has not arrived in `portfolio_value` | **$0.00** |

So it shrinks equity *and* leaves exposure unchanged -- understating the ratio in
**both terms at once**, which makes the gate read looser than it was configured
to be. `KXMLBTOTAL-26AUG311940MILCHC-14` requested 3 contracts for $2.43 and
logged `contracts: 0, cost_dollars: 0.00`, while shard 3 fell from $15.00 to
$12.57. Exactly the $2.43.

`resting_exposure()` returns the same `(total, by_segment)` shape as
`exposure_from_positions`, and both are folded into equity and exposure before
Gate 2b runs. It fails **open** with a warning if the venue listing is
unavailable -- exposure is a sizing input, not a legality check (contrast S3).

**Price comes from our own trade log, not the venue, and that is the whole
design.** v2 expresses every order from the YES perspective: a NO buy rests as an
`ask` at `(100 - no_price)`. Pricing the 81c NO off the venue payload without
inverting yields **$0.19 a contract instead of $0.81** -- a 4x under-count, in the
one gate this exists to tighten. The inversion could not be verified against a
live resting order (there were none at the time), so it is not in the code at
all: the trade log already stores `price_cents` **bet-side**, so joining on
`order_id` needs no inversion. The venue stays authoritative for *which* orders
rest; the log for what they cost. A test pins the trap explicitly.

An order the log cannot price -- hand-placed on iOS, or a log gap -- is counted at
**$1.00/contract worst case** and logged at WARNING. Skipping it would reproduce
the exact under-count being removed, and over-stating exposure only ever tightens
the gate.

Verified live against the funded account: 28 positions, $36.30 exposure, $122.62
equity, **0 resting orders -> ratio unchanged at 29.6%**, no false positives.
+14 tests.

---

## 2026-08-31 -- S18/S19: two instruments that were reporting confidently and wrongly

Found by reviewing the trailing week's trades, settlements, logs and reports rather than
the code. Neither defect ever raised an error; both produced plausible numbers.

### S18 -- the daily digest's Brier double-flipped every NO bet

`market_price_at_entry` is **already side-relative**: a NO bought at 73c stores `0.73`,
the price paid for the NO. `daily_summary.py` flipped it anyway --

```python
predicted = float(price) if side != "no" else 1.0 - float(price)
```

-- turning that 73c NO into a `0.27` prediction and scoring it against a win. The
settlement log settles the question in one line: **0 of 133 NO-side rows** violate
`fair_value - market_price_at_entry == edge_estimated`, so the stored price is the bet's
own price on every one of them.

**33% of all 407 settled bets are NO-side**, so any window containing one was overstated.
The 2026-08-31 email reported **Brier 0.169** where the truth is **0.077**.

The second half is worse and outlives the arithmetic. This function computes the
**market's** Brier (predicted = the ask) while `betting_analysis.py` computes the
**model's** (predicted = `fair_value`). On 08-31 the two reports printed **0.169 and
0.0501 under the same label "Brier", for the same five bets, on the same day**. F3's whole
finding is *model Brier vs market Brier*, and S1b branch A is decided on exactly that
comparison -- one label covering two quantities is how that call gets made on the wrong
number. The digest now reports them as a pair:

```
- 7-day rolling: 5 bets · 4-1 (80.0% WR) · P&L +$1.20 · ROI +18.2% · Brier model 0.050 vs market 0.077
```

The model figure now agrees with `betting_analysis.py` to four decimals, which is the
cross-check that the two reports finally describe the same world.

**Why it survived:** the existing test priced every bet at 50c, where a flip is invisible.
Four new tests; the NO-side one uses 80c.

### S19 -- the live-freshness filter rejected 100% of books, and never once caught a stale one

The Odds API puts `last_update` in two different places:

| endpoint | bookmaker | market |
|:--|:--|:--|
| `/sports/{sport}/odds` | yes | yes |
| `/sports/{sport}/events/{id}/odds` | **no** | yes |

`_refresh_event_if_live()` is the only caller of the per-event endpoint -- the in-play
refresh that exists to make data *fresher*. Every response it returns has bookmakers
shaped `{key, title, markets}`. `_is_bookmaker_stale()` read only the bookmaker field,
found `None`, and took its fail-closed branch.

Measured on the 327 real per-event payloads in `data/cache/odds/events/`:

| | |
|:--|--:|
| bookmakers missing a top-level `last_update` | **1920 / 1920 (100%)** |
| markets carrying one | **5252 / 5252 (100%)** |
| median market quote age at fetch | **34s** |
| quotes actually stale against the 1200s limit | **0** |

August's logs: **2888 exclusions, every one "missing last_update", zero from the age
check.** The filter has never done the job it was written for, and the code comment
asserting *"The Odds API event endpoint returns last_update on every real response, so
this only fires on malformed/mocked data"* had it exactly backwards.

`_bookmaker_last_update()` falls back to the **oldest** market timestamp -- a bookmaker is
only as fresh as its stalest market, which keeps the conservative intent. Replaying the
same 1920 bookmakers: **100% dropped -> 0% dropped**, with fail-closed intact for a book
carrying no timestamp anywhere.

No P&L damage, because `ALLOW_LIVE_BETS=false` (S7). But it sits directly under the L1
in-play work, and it was spending Odds API quota on responses discarded wholesale -- which
fed S20, where 10 of 12 keys are exhausted and all 166 August key failures are `baseball_mlb`.

### S19b -- and the guard built to catch exactly this could not see it

All three consensus functions ordered their exits so the empty case returned first:

```python
if not fair_probs:                              # total wipeout returns HERE
    return None
if _live_consensus_too_thin(...):               # unreachable when every book is stripped
```

`_live_consensus_too_thin` only ever fired when 1-2 books survived. **The worst case --
all of them stripped -- was the one case it was blind to**, which is why it never logged
once in a month of 2888 exclusions. Reordered at all three sites. It still no-ops when
`n_excluded == 0`, so a genuine "no books matched this team" falls through unchanged; only
a wipeout *caused by the filter* now warns.

### Verification

11 new tests, of which **4 fail without the fix**. The other 7 guard against
over-correction -- stale still excluded, no-timestamp-anywhere still fails closed, pregame
untouched, bookmaker-level field still preferred -- and pass either way by design. One
replays every real cached per-event payload on disk and asserts each bookmaker is dateable,
so the fixtures cannot drift away from what the API actually sends.

The wrong belief was in the fixtures too (`tests/test_edge_detection.py:516`, *"Real Odds
API responses always carry a per-bookmaker last_update"*): every fixture modelled the
sport-level shape, so the per-event shape was never exercised. Comment corrected in both
places.

**996 pass.** Five pre-existing failures in `tests/test_exposure_gate.py` are unrelated and
predate this work -- fixture ticker `KXMLBGAME-26AUG271900NYYBOS-NYY` went into the past on
08-27, so Gate 4.8 now rejects it as in-progress. Same rotting-fixture class S1 and S5 both
hit at the conftest seam; logged, not fixed here.

---

## 2026-08-27 -- X1: just-in-time cash movement between exchange shards

**Sizing stays whole-account; spending becomes shard-aware.** Operator's call, and the
right one -- the alternative was sizing each order against its own shard's slice, which
would have made a $15 balance silently cap MLB bets that the bankroll comfortably
supports.

The mismatch it closes, with the live numbers:

| | |
|:--|--:|
| `bankroll` (sum across shards, what sizing uses) | $88.06 |
| spendable on shard 0 -- NFL, MLS, everything else | $73.07 |
| spendable on shard 3 -- MLB, tennis | $15.00 |
| one batch at `--budget 12%` | $10.57 |
| **all three intraday runs hitting MLB in one day** | **$31.71** |

All seven scheduled sports jobs pass `--budget 12%` and each is a separate batch, so the
per-batch cap never bounded the day. One MLB batch fits inside $15.00; three do not.

`shard_funding.ensure_shard_funded()` runs immediately before each order:

- **Exactly the shortfall, never a round-up.** Cash parked on the sports shard cannot back
  an NFL order, so over-moving quietly reallocates the bankroll.
- **`MAX_AUTO_SHARD_TRANSFER` (live $25) caps a single move.** A shortfall computed wrongly
  bounces off the cap instead of draining the reserve. This is what makes leaving it on
  unattended defensible.
- **Verified, not assumed.** Kalshi's own warning -- "if a later step fails, completed steps
  are not undone" -- means a 200 is not proof the money arrived, so the destination balance
  is re-read and the order is skipped if it is still short.
- **Fails open on an unknown shard** (market lookup down => pre-sharding behaviour, the
  venue's error is the backstop) and **closed on a transfer that did not settle**.
- **One attempt per order.** No retry loop around a money movement.
- **Never in `DRY_RUN`**, checked from `get_config().system.dry_run` like the janitor and
  the report banner rather than off the client, so a duck-typed client need not carry it.

Turned **off**, an underfunded order is *skipped and logged* `shard_underfunded` rather
than placed to fail -- the pre-existing behaviour was to place it and collect a
`404 user_not_found`. A refusal never stops the batch: the next order on a funded shard
still goes.

`doctor.py` now prints the per-shard split under the balance, because the sum alone is
exactly what hid this:

```
PASS  Kalshi API connected (balance: $88.06)
PASS    shards: 0=Default $73.07, 3=Tennis & Baseball $15.00
PASS    AUTO_SHARD_TRANSFER on — tops up from shard 0, max $25.00/transfer
```

Ships `false`; the live `.env` sets `true`. Config validation rejects
`AUTO_SHARD_TRANSFER=true` with a $0 cap, which could never move anything.
`scripts/shared/shard_funding.py` carries a `_demo()` self-check for the decision logic;
`tests/test_shard_funding.py` covers the wiring -- that the batch consults it, skips on
refusal, caches the shard lookup per ticker, and survives one underfunded order. **987
tests pass.**

**Still open:** S3's eligibility cache is keyed venue + product, so `kalshi:sports = ok`
remains simultaneously right for MLS and wrong for an unfunded MLB shard. X1 makes that
mostly moot -- the order is now skipped before it can 404 -- but the key is still
imprecise.

---

## 2026-08-27 -- Funded shard 3; MLB orders work again (+ a shardless cancel bug)

**$15.00 moved from shard 0 to shard 3, transfer `2e67a7ef`, status `complete`.** An MLB
order was accepted immediately afterwards, so the `user_not_found` diagnosis was right:
the account was never blocked, it was unfunded on the shard MLB had moved to.

```
before   exch 0: $88.0660   exch 3: $0.0000
after    exch 0: $73.0660   exch 3: $15.0000
```

### The wire format took three live 400s

Worth recording, because a mock would have agreed with every wrong version:

| Sent | Kalshi's answer |
|:--|:--|
| `amount: "15.0000"` (fixed-point string, as every other v2 money field) | `cannot unmarshal string into Go struct field ...amount of type int64` |
| `amount: 1500` + `source_exchange_index` | `invalid source: invalid exchange instance: "" (valid values: "event_contract", "margined")` |
| `amount: 150000` + `source`/`destination` + `source_exchange_shard` | accepted |

Two axes are easy to conflate and the field names do not help: `source`/`destination` name
the **instance** (`event_contract` | `margined`), while `source_exchange_shard` /
`destination_exchange_shard` -- **not** `..._exchange_index` -- carry the number that
`/exchange/status` and every market call `exchange_index`. Both shard fields default to 0,
so omitting them is a silent no-op transfer rather than an error. And `amount` is int64
**centicents** (10000 = $1.00), the only v2 money field that is neither a fixed-point
string nor plain cents.

### `get_balance()['balance']` is the SUM across shards

`8806` before the transfer and `8806` after, while the breakdown moved $15 between shards.
This was flagged as unknown when the split was proposed; it is now settled, and it is the
unsafe answer. `get_balance_dollars()` reads that top-level field, so **`--budget 12%` and
Gate 2b's equity denominator both size against $88.07 while an order can only spend its own
shard's slice** -- $73.07 for NFL/MLS, $15.00 for MLB. Not yet fixed; no exposure while MLB
produces nothing clearing Gate 3, and the failure mode is `insufficient_balance`, which is
correctly classified transient.

### Cancel is shard-scoped too, and fails as a bare 404

The verification order was accepted and then **could not be cancelled**:
`DELETE /portfolio/events/orders/{id}` returned `404 not_found`, leaving a live 1c resting
order on `KXMLBGAME-26AUG271910MILNYM-NYM`. It cleared on
`?exchange_index=3` (`reduced_by: 1.00`), confirmed by `GET /portfolio/orders` reporting
`exchange_index: 3` on the order.

**This is the dangerous one.** A bare `404 not_found` is indistinguishable from "already
gone", which is exactly how the R4 janitor treats it -- so
`cancel_stale_resting_orders()` would have logged a clean sweep while every MLB order kept
resting indefinitely, and `doctor.py --verify-eligibility` would have left its probe order
live on the book. `cancel_order()` now takes `exchange_index`, and both callers forward the
value the order itself reports. Regression test asserts the janitor forwards the shard,
since nothing else would catch it.

**Not fixed here:** the sum-vs-shard sizing gap above, and S3's per-product eligibility key,
which still cannot express "ok for MLS, wrong for MLB". 978 tests pass.

---

## 2026-08-27 -- MLB moved to a new exchange the account is not on

**Every MLB order will fail until this is resolved, and it is not a block.** A 1c probe
on an open MLB market returned:

```
POST /portfolio/events/orders -> 404 {"code":"user_not_found","message":"user not found"}
```

Reads are fine -- balance, positions and resting orders all answer normally with the same
key and the same signing. A **bogus** ticker returns a generic `not_found`, while a **real
open MLB** ticker returns `user_not_found`: the market resolves first, then the user lookup
fails. That is per-exchange membership, not authentication and not jurisdiction.

`exchange_index` is the whole story:

```
balance breakdown   exch 0 -> $73.366    exch 1 -> $0    exch 2 -> $0    exch 3 -> $0
KXMLBGAME     78 open markets  -> exchange_index 3      <- all of MLB
KXNFLSPREAD  200 open markets  -> exchange_index 0
KXNFLGAME     96 open markets  -> exchange_index 0
KXMLSTOTAL    90 open markets  -> exchange_index 0
```

MLB has migrated to **exchange 3**, where the account has no balance and no user record.
NFL and MLS are still on exchange 0, and a probe there is accepted normally -- which is how
`kalshi:sports` was re-verified the same day. The 08-26 hand probe succeeded because its
ticker, `KXMLBGAME-26AUG261915LADATL-LAD`, is an **exchange 0** market; the equivalent
market today is on 3. The migration therefore happened between 08-26 and 08-27.

**This defeats S3's product keying.** Eligibility is stored per venue + product, and
`sports` is one product spanning both exchanges -- so `kalshi:sports = ok`, earned honestly
on an MLS market, is simultaneously **wrong for MLB**. The preflight passes and the order
404s. Worse, `user_not_found` matches neither `_STRUCTURAL_PATTERNS` nor
`_TRANSIENT_PATTERNS`, so `_handle_structural` does not abort: a batch of N MLB candidates
would issue N failing orders, exactly the spray S3 was built to stop, reintroduced through
a dimension the cache does not model.

**Deliberately not "fixed" by widening the structural list.** Matching `user_not_found`
there would set `kalshi:sports = blocked`, which never decays and would take MLS and NFL
offline too -- an exchange-scoped problem escalated into a product-wide outage. The cache
needs the exchange dimension, or the scanner needs to drop markets whose `exchange_index`
has no balance, before the classifier is touched. Left open pending the operator's call;
no live exposure while MLB produces no candidates that clear Gate 3.

---

## 2026-08-27 -- S3a: the test suite was writing the live eligibility cache

**The gate built to stop the Nevada repeat was defeated on its first day, by
`make test`.** `data/cache/venue_eligibility.json` read:

```json
{"kalshi:sports": {"status": "ok",
                   "checked_at": "2026-08-27T01:27:31Z",
                   "reason": "order accepted (KXNBAGAME-26APR04T3-A)"}}
```

`KXNBAGAME-26APR04T3-A` is a **pytest fixture** ticker (`test_execute_batch.py`,
`test_fill_accounting.py`, `test_reconciliation.py`) -- no real order carried it. What it
overwrote was **genuine**: the 08-26 entry seeded `ok` from hand probe
`01a0407d-3ea8-7f90-9c7f-9179cebac8cc`, accepted and cancelled on
`KXMLBGAME-26AUG261915LADATL-LAD` after the geolocation check was re-verified. So the bug
is not "the gate went green on nothing" -- it is that a test run **clobbered real evidence
with fabricated evidence under the same key**, which is worse: the verdict stayed `ok`, so
nothing looked wrong.

The trade log cannot arbitrate this. The 08-26 entry says so in as many words -- the hand
probe "was placed by a one-off script that never called `log_trade`" -- and this entry's
first draft nonetheless cited the log's silence as proof eligibility had never been proven.
It had been.

The path: `_place_order_batch` calls `vel.record_success()` on any `create_order`
response whose status is not `dry_run_blocked`, and a **mocked** client never returns
`dry_run_blocked`. `ELIGIBILITY_PATH` is a module-level constant, so the write landed
on the operator's real cache. Yesterday's 18:27 test run stamped the fail-closed
preflight green on evidence of a fake fill, and `doctor.py` reported
`kalshi/sports: eligible (verified 0d ago)` from then on.

**Why it mattered.** S3's whole premise is that only a genuine venue acceptance or the
explicit `--verify-eligibility` probe may clear a block -- "auto-retry is precisely the
behaviour that produced six days of rejections". A test run is neither, and it cleared
one. Blast radius was bounded (the 08-26 batch-abort caps a re-discovery at one
rejected order), but the gate was reporting proof it did not have.

**Fix: one autouse fixture in `tests/conftest.py`**, beside `_isolate_data_logs`, which
had already learned this exact lesson for the trade log. `test_venue_eligibility.py`
patched `ELIGIBILITY_PATH` locally; the three executor tests never thought to. Patching
in conftest covers every caller, including ones not yet written -- the same reason the
trade-log isolation lives there rather than in the tests that happen to call
`log_trade()`.

The poisoned entry was reset to `{}` and **re-earned, not restored**: a fresh probe on
2026-08-27 was accepted and cancelled on `KXMLSTOTAL-26AUG29SEACHI-1`
(`01a043a8-4b90-77ef-9c7c-703573829750`), so `kalshi:sports` is `ok` on evidence from
`verify_eligibility` itself -- note the reason now reads `probe accepted (...)`, the string
only the probe writes, where the clobbered one read `order accepted (...)`, the executor's.
**That wording is the tell**, and is worth checking before trusting any future `ok`.
964 tests pass and the cache stays empty across a full test run.

**Also:** operator deposited **$25**; equity verified at **$103.09** ($73.36 cash +
$29.73 in 24 NFL positions, incl. $0.82 fees). `CLAUDE.md`'s Risk Limits header still
quoted the ~$92 it stood at; `SKILL.md` had already been corrected on 08-26.

---

## 2026-08-26 -- S3: venue eligibility preflight, fail closed

**A correctness bug, not waste.** Between 2026-08-20 and 2026-08-25 Kalshi rejected
**16 orders across 6 scheduled runs**:

```
Nevada_residents_are_not_currently_allowed_to_open_positions_in_Sports,
_Elections_and_Entertainment._Check_your_email_for_more_details.
```

The account is in California (Rancho Cordova KYC address, Fresno-County Comcast IP).
That text is what *any* API key receives when it has not completed Kalshi's periodic
**geolocation check** — the fix was a two-minute click-through at
`kalshi.com/account/profile`, and it took six days to find. Three independent failures
had to line up, and this entry fixes all three.

### 1. The batch never stopped

`_place_order_batch` caught `KalshiAPIError`, recorded it, and **kept placing**. Correct
for a 429 or a stale price; wrong for a jurisdiction block, which is deterministic — the
next order fails identically. The rejection log shows the batches, not six discoveries:

```
08-20  n=3   18:01:31, 18:01:31, 18:01:32     <- three inside one second
08-21  n=3   03:30:49, 18:01:16, 21:01:06
08-22  n=1   12:05:46
08-23  n=4   18:01:06, 18:01:07 x3            <- four inside one second
08-24  n=2   12:05:41, 18:01:10
08-25  n=3   18:01:15, 18:01:16, 18:01:16
```

There was already a short-circuit for *transport* failures
(`MAX_CONSECUTIVE_CONN_ERRORS = 3`) and none for API errors. New `_handle_structural()`
aborts on the **first** structural rejection — threshold 1, not 3, because this class is
deterministic rather than noisy. Replaying the real 08-20 batch: **1 order attempted
instead of 4.**

### 2. Nothing remembered

Every run started clean and rediscovered the block. New
`scripts/shared/venue_eligibility.py` persists a verdict to
`data/cache/venue_eligibility.json`, and `execute_pipeline` reads it before any live
order.

**Keyed on venue + PRODUCT, not venue.** The observed block names Sports, Elections and
Entertainment specifically — an account barred from sports may still trade weather or
crypto, so disabling all of Kalshi would be over-broad even though sports is currently
the entire book.

**Fails closed: `unknown` blocks exactly like `blocked`.** This is deliberately the
opposite of the risk gates (3.6, 3.7 and the day's own 2b) which fail *open* on missing
data, and the asymmetry is the point — an unmeasurable spread is a sizing question whose
worst case is a bad bet, while an unverified jurisdiction is a legality question whose
worst case is an order the venue is barred from filling. **Dry runs skip the check
entirely**: they never reach the venue, and blocking them would silence the Polymarket
dry-run evidence log its phase gate depends on.

**Nothing clears a block automatically** — auto-retry is precisely what produced six
days of this. Only two paths promote to `ok`: a real venue acceptance (a
`dry_run_blocked` response deliberately does not count — it proves nothing), or the
explicit `python scripts/doctor.py --verify-eligibility --ticker <open sports ticker>`,
which places a **real** 1c unfillable order and cancels it, exactly as was done by hand
on 08-26. An `ok` decays to `unknown` after `ELIGIBILITY_TTL_DAYS` (30) — Kalshi says it
"will send further instructions as necessary to maintain access", so eligibility is a
lease, not a fact, and a verdict that never expired is how this went unnoticed. A
`blocked` never decays: time passing is not evidence a restriction was lifted.

Classification is narrow, and **transient patterns are checked first and win ties** — a
false positive takes the account offline, so `insufficient_balance`, rate limits,
`market_closed`, `invalid_price` and `deprecated_v1_order_endpoint` can never disable a
venue. That last one matters: the other 6 of the log's 22 error rows are the 2026-06-20
v1->v2 endpoint change, four of which were successfully re-placed two days later.

### 3. All three surfaces truncated the only actionable words

The message puts the instruction **last**, and every surface cut the end:

| Surface | Cap | What it showed |
|:--------|:----|:---------------|
| console `FAIL` line | 80 | `...open positions in Sport` |
| trade log `_record_failure` | 200 | cut the `message` field mid-sentence |
| daily digest `_error_reason` | 110 | **`...Check you...`** |

The full text is 135 characters. The digest's cap landed **25 characters short** of
"Check your email for more details" — the entire fix. All three now route through
`actionable_reason()`, which elides the **middle** and keeps both ends (the head is
boilerplate, the tail is the instruction), and the trade log stores the full body. The
`code` field had in fact survived intact on disk the whole time; only the reporting ate
it.

### Verification

Simulated against the real 08-20 batch and error body:

```
STRUCTURAL REJECTION -- kalshi/sports disabled.
Nevada residents are not currently allowed to open positions in Sports,
Elections and Entertainment. Check your email for more details.
Stopping batch: 3 order(s) not attempted -- this error is deterministic, so
retrying only places identical failures.
  -> batch ABORTED after order 1 of 4

cache: kalshi/sports = blocked      kalshi/prediction = unknown (untouched)
next run's preflight: BLOCKED (no live orders)
```

`doctor.py` gained a **Venue Eligibility** section that reports `unknown` as a FAIL, not
a warning — an empty cache means live orders are blocked, and that must be loud.

**Seeded from real evidence, not assumed.** The cache was initialised to
`kalshi/sports = ok` citing probe order `01a0407d-3ea8-7f90-9c7f-9179cebac8cc`, accepted
and cancelled on `KXMLBGAME-26AUG261915LADATL-LAD` on 2026-08-26 after the geolocation
check was re-verified. Without that seed the fail-closed rule would have stopped the
20:30 scheduled run — correct behaviour, but the evidence exists, so recording it is
honest rather than convenient. The trade log could not supply it: the last accepted
order there is 2026-08-19, before the block, and the hand probe was placed by a one-off
script that never called `log_trade`.

Touches: `scripts/shared/venue_eligibility.py` (new, with `_demo()` self-check),
`scripts/shared/paths.py`, `scripts/kalshi/kalshi_executor.py` (`_handle_structural`,
preflight, success recording, full-body logging, tail-preserving console line),
`scripts/kalshi/daily_summary.py`, `scripts/doctor.py` (section +
`--verify-eligibility`), `tests/test_venue_eligibility.py` (+48). **964 tests pass.**

**Wires straight into S16.** That kill switch specifies the same trigger — "any repeated
structural rejection -> immediate disable of that venue/product until `doctor.py` reports
it eligible; no sample threshold, this is deterministic not noisy". S16 now hooks this
rather than reimplementing it.

**Known limit:** classification is pattern-based, so a venue that invents new wording for
a restriction falls through to the transient path and keeps placing. That direction is
the deliberate one — a false positive disables live trading — but it means the pattern
list needs a look whenever a new structural rejection appears in the log.

---

## 2026-08-26 -- S4: Gate 2b, cumulative open-exposure ceilings

**The first gate in the chain that measures a standing total.** Every gate before it
measures a single order (`MAX_BET_SIZE`, `MAX_BET_RATIO`), a single event
(`MAX_PER_EVENT`), a single batch (`--budget`, the Kelly `/batch_size` divisor), or a
row count (`MAX_OPEN_POSITIONS = 50`). None of them counts dollars standing across the
book -- which is how 26 NFL positions reached 31% of a ~$92 bankroll across roughly a
dozen scans over three months **with every one of those gates passing the whole way**.
S5 stopped the *lead time* that let it accumulate unnoticed; this stops the *total*.

**Two ceilings, and the pair is the point.** `MAX_OPEN_EXPOSURE_PCT` across everything,
`MAX_SEGMENT_EXPOSURE_PCT` per sport. A portfolio cap alone permits one sport to hold
all of it -- exactly the NFL shape. A segment cap alone permits N sports x the segment
cap. Segment = `_detect_sport(ticker)`, falling back to the scanner's `category`, then
`"unknown"`; deliberately *not* the event key, since Gate 6 already binds one event and
passed 26 times across 26 different events.

**Denominated in equity (cash + position value), not cash.** Cash alone is a moving
denominator that accelerates against itself: every dollar bought subtracts from cash
*and* adds to exposure, so the ratio climbs at twice the rate of the risk, and a nearly
fully-deployed book reads as far over a ceiling it has not crossed. Positions are read
from `market_exposure_dollars`, which arrives from the v2 API as a **string**
(`"0.960000"`) -- coerced per row, and an unparseable row is skipped rather than
counted as 0, since one silent zero for the whole book would open every ceiling.

**Reject *and* trim.** The gate rejects when a ceiling is already breached, and the
sizing half trims an order to the smaller of the two remaining headrooms. Reject-only
would let a book sitting at 49.9% add a full `MAX_BET_SIZE` and land well past 50%.
Trims use `max(1, ...)` like the `MAX_BET_SIZE` cap above them, so a bounded cent-scale
overshoot is possible by design -- a cap that can silently emit an unfillable
0-contract order is the worse failure. Measured on the synthetic slate below: $0.21.

**The batch loop accumulates.** Approved cost is added to both counters as the slate is
sized, or N orders each individually under the ceiling walk straight through it
together -- the same failure as the NFL book, compressed into one run instead of three
months. The R26 cached-replay path re-checks Gate 2b against current state for the same
reason it re-checks gates 5/6/7: exposure is portfolio state and the cache TTL is long
enough to have filled a ceiling since the preview. Sizing stays locked there, so replay
only drops rows.

**Fails open on unknown equity**, mirroring gates 3.6 and 3.7 -- a balance call that
returned nothing is "unknown", not "over the limit". Note this is the opposite of S3's
fail-*closed* rule for venue eligibility, and deliberately so: an unknown ceiling is a
sizing question, an unknown jurisdiction is a legality question.

**Live values are 0.50 / 0.33, not the review's 0.20 / 0.10** -- the operator's call,
made with the consequence stated: at 50/33 the book that prompted the gate **passes**
(27.8% total, 27.8% NFL), so the ceiling binds on the next pileup rather than this one.
That also dissolves the legacy-quarantine question S4 would otherwise have forced: NFL
fits under 33% either way, nothing is jammed shut, and betting in other sports keeps its
full headroom while the frozen book runs off to settlement. At 0.20 / 0.10 the same book
rejects on both counts -- covered by a test, so the choice stays visible.

Config validation rejects a value outside [0, 1]: `MAX_OPEN_EXPOSURE_PCT=50` would
otherwise read as 5000% and silently switch the cap off, which is the same class of bug
as D1's falsy `0.0`.

**Verified against the live book** (equity $107.04 = $73.36 cash + $33.68 positions):

```
exposure $29.73 = 27.8%   (all 24 open positions are NFL; nothing else is open)
  nfl  $29.73 = 27.8%   headroom $5.59 to the 33% segment cap

Gate 2b verdicts:
  KXNFLGAME-26SEP13MIALV-MIA        seg=nfl       pass
  KXMLBGAME-26AUG271900NYYBOS-NYY   seg=mlb       pass
  KXNCAAFBGAME-26AUG29ALAFSU-ALA    seg=ncaaf     pass
  KXSB-26-KC                        seg=futures   pass
```

Synthetic over-limit slate (nine MLB rows against the live book), the roadmap's stated
verification step -- note orders 4 and 5 trimmed rather than rejected, and 6-9 rejected:

```
#1  tot $29.73 (27.8%) -> APPROVED                    $7.50
#2  tot $37.23 (34.8%) -> APPROVED                    $7.50
#3  tot $44.73 (41.8%) -> APPROVED                    $7.50
#4  tot $52.23 (48.8%) -> APPROVED_CAPPED_EXPOSURE    $1.00
#5  tot $53.23 (49.7%) -> APPROVED_CAPPED_EXPOSURE    $0.50
#6  tot $53.73 (50.2%) -> REJECTED: max_open_exposure
...                                    final: 50.2% (overshoot $0.21)
```

**Not in preflight.** `preflight_gate_status()` is static per-opportunity only; exposure
is portfolio state, like gates 1/2/5/6/7, so a scan preview cannot show it. The scan
banner prints standing exposure and the largest segment instead.

`doctor.py` prints both caps and **WARNs when either is 0** -- "nothing caps TOTAL
capital deployed" is precisely the state that produced the NFL book, and it should never
scroll past looking like a healthy default.

Third config-driven test breakage prevented at the conftest seam
(`_ignore_operator_exposure_caps`, joining the S1 and S5 fixtures): tests that pin exact
contract counts pass a small `bankroll`, which doubles as the equity fallback, so a live
33% cap would silently resize orders in tests about Kelly, fees, or the flat floor.

Touches: `app/config.py` (two `RiskLimits` fields + range validation),
`scripts/kalshi/kalshi_executor.py` (`exposure_segment`, `exposure_from_positions`,
`_exposure_rejection`, Gate 2b branch, headroom trim, batch + replay accumulation, scan
banner, reload wiring), `.env`, `scripts/doctor.py`, `tests/test_exposure_gate.py` (+28),
`tests/conftest.py`. **916 tests pass.**

**Still missing after S4:** nothing re-checks a position already held -- Gate 2b, like
Gate 3.6, only runs at entry. A book that drifts over a ceiling through mark-to-market
alone is not caught, and would not have been the NFL failure mode anyway. S12's daily
scoreboard is where a standing breach becomes visible.

---

### S4 follow-up (same day): doc sweep, and the `limits` report made true

Propagating S1 / S4 / S5 into the satellite docs surfaced that **none of them had been
updated for S5 either**, and that several were describing a system that no longer exists:

- **`risk_check.py --report limits` documented a `MAX_PORTFOLIO_RISK_PCT` row that was
  never implemented** — the env var does not appear anywhere in the codebase. The report
  showed daily loss, position count and max bet size: two row-counts and a per-order cap,
  nothing about money deployed. It now prints **Open Exposure** and **Largest Segment**
  against their gate-2b ceilings, and prints **`NO CAP SET`** (not a comfortable `OK`)
  when a cap is 0. This is the same "documented but unenforced" shape as the Gate 3.6
  spread rule, which sat in CLAUDE.md as a Hard Stop for five months with no code (L2),
  and as B3's 10%-of-bankroll stop, which still has none. On the live book it reads:

  ```
  Open Exposure (gate 2b)   $29.73   $53.53    56%   OK
  Largest Segment (nfl)     $29.73   $35.33    84%   OK
  ```

  NFL at **84% of its segment ceiling** is the number worth having in front of you before
  the 2026-09-15 unfreeze review; nothing in the old report would have shown it.

- **`docs/setup/ARCHITECTURE.md` listed 12 gates in its badge and 13 in its pipeline
  table, and documented 9.** Missing: 2b, 3.6, 3.7, 4.6b, 4.8. Its risk-parameter table
  also still carried pre-2026 defaults (`MAX_OPEN_POSITIONS=10`, `MAX_PER_EVENT=3`,
  `MIN_MARKET_PRICE=$0.06`). Rewritten to 18, with a one-line scope summary — gates 1/2b
  measure the account, 2/5/6/7 the book, 3-4.8 the opportunity, 8/9/2b-cap the order.

- **`docs/scripts/per-script/kalshi_executor.md` claimed "11 gates" and listed 11**,
  missing the same five, and said sizing was "capped by gates 7-8" (it is 8-9).

- **`.claude/agents/KALSHI_BETTOR.md` quoted `UNIT_SIZE $0.50` and `KELLY_FRACTION 0.75`**,
  neither of which has been the value for months, with no note that the live `.env`
  overrides the defaults. Rewritten to lead with "run `doctor.py` before quoting a limit",
  and to state that `MIN_EDGE_THRESHOLD_NFL` is owned by `nfl_week1_review.py` and must
  not be hand-edited.

- **`.env.example`** gained both S4 knobs (in the safety-rails section, not buried) and
  Gate 3.7, and its five-item getting-started checklist now names `MAX_OPEN_EXPOSURE_PCT`
  — with both caps at 0, a fresh clone has *nothing* capping total capital deployed, and
  that should be visible at setup rather than discovered at 31%.

- **`SKILL.md`** gained S1/S4/S5 entries and a corrected bankroll (**~$107 equity** after a
  $25 deposit; the reviews quote the ~$92 it stood at). Its preflight-label list was
  missing `off`, `illiq` and `far`, and both label lists now state that preflight is
  static-only, so `ok` never means "will execute".

Also updated: `docs/setup/SETUP_GUIDE.md`, `docs/setup/AUTOMATION_GUIDE.md` (exposure caps
matter most under automation — scheduled runs accumulate across days with no human watching
a total), `docs/my-documents/guides/Bet-Sizing.md`. 916 tests still pass.

**The recurring pattern worth naming:** every one of these docs was accurate when written
and silently decayed. `doctor.py` is the only surface that reads the *running* config, which
is why CLAUDE.md points at it as the source of truth — and why **S6
(`risk_config_fingerprint()`) is the item that stops this from recurring**, rather than
another sweep like this one.

---

## 2026-08-26 -- S5: Gate 3.7, a days-to-event cap on game markets

`MAX_DAYS_TO_EVENT_FOR_GAME_MARKETS` (code default `0` = off; live `.env` **14**).
Second action item from the 2026-08-26 strategy review, and the root-cause fix
behind the S1 NFL freeze.

**The NFL book was a lead-time failure, not a football failure.** Reconciling the
26 open positions against their tickers:

```
days-to-kickoff:  min 25 · median 35 · max 112
more than 14 days out:  26 of 26
placed at 18:01 UTC (= 11:01 PT, the no-date-filter task):  20 of 26
```

Nothing settled for months, so no feedback ever arrived, while `MAX_OPEN_POSITIONS`
and `MAX_PER_EVENT` passed the whole way -- neither measures a standing total, and
`MAX_BET_RATIO` / `--budget` each bound only a single batch. Five of the six
execution tasks pass `--date today|tomorrow` and are structurally incapable of
this; the sixth runs with no date filter and placed 20 of the 26.

**The cap targets lead time, not sports.** Verified against the real book:

```
KXNFLSPREAD-26SEP13BALIND-IND5    d=17   reject   (real position; `off` first, sport frozen)
KXNCAAFBGAME-26AUG29ALAFSU-ALA    d= 2   ok       college football Week 1
KXMLBGAME-26SEP29LADATL-LAD       d=33   far      far-dated MLB
KXSB-26-KC                        d=None ok       Super Bowl future -- exempt
```

- **Futures are exempt by category, not ticker prefix.** `KXMLB-26-LAD` (World
  Series) and `KXMLBGAME-26AUG26...` share a prefix; only the scanner's own
  `category` separates them, so the exemption keys on
  `{futures, outrights, championship}`.
- **Fails open on an unmeasurable date**, mirroring Gate 3.6: a game ticker with
  no parseable date is "unknown", not "too far". This gate rejects on evidence.
- **Ships off (0).** A fresh clone's behaviour is unchanged and the suite's 2099
  fixture tickers stay valid; the live `.env` turns it on at 14.
- Ticker dates are Eastern and the comparison is UTC, so the count can be off by
  one for a few hours around midnight UTC. It can only read *lower*, so the fuzz
  never produces a false reject.

`days_to_event()` lives in `ticker_display.py` beside the existing `_DATE_RE` and
month map rather than duplicating `edge_detector._extract_game_date`.

### Also -- the test suite inherited the operator's `.env` again

Enabling the cap failed **126 tests** that have nothing to do with lead time:
fixture tickers are written for readability (`KXNFLSPREAD-26SEP13BALIND-IND5`,
`KXMLBGAME-99APR171900NYYKAC-NYY`), not for proximity to today. Same shape as the
S1 sport-freeze breakage the day before, so it is fixed at the same seam: a second
autouse fixture, `_ignore_operator_time_to_event_cap`, zeroes the cap for every
test, and the tests that exercise it set their own. **+24 tests** covering the
real NFL distances, college Week 1, the futures exemption, both fail-open paths,
and `reload_risk_config` wiring. 888 pass.

**Still missing:** S4. Gate 3.7 stops a position being opened far out; nothing yet
caps *total* open exposure, so a concentration can still build inside 14 days.

---

## 2026-08-26 -- S1: NFL live entries frozen (strategy review, Priority 0a)

First action item from
[`docs/enhancements/betting-strategy-review-2026-08-26.md`](enhancements/betting-strategy-review-2026-08-26.md).
`MIN_EDGE_THRESHOLD_NFL=1.0` in the live `.env` -- the F3 World-Cup idiom: edge is
bounded by 1, so a floor at or above 1.0 can never be cleared, and the executor
reports `sport_disabled` rather than a bogus edge comparison.

**Why.** Reconciling `kalshi_trades.json` against `kalshi_settlements.json` by
`trade_id`:

```
open NFL positions: 24    at-risk: $28.50    oldest entry: 2026-05-23
  KXNFLTOTAL   n=11   $14.96
  KXNFLSPREAD  n=10   $8.68
  KXNFLGAME    n= 3   $4.86
NFL rows in settlements: 0
```

- **$28.50 on a ~$92 bankroll is 31% of the account**, one sport, held up to 95
  days before kickoff -- and `MAX_OPEN_POSITIONS=50` / `MAX_PER_EVENT=2` both
  passed the whole way. **No gate measures total capital deployed** (S4 is the
  durable fix; this is the tourniquet).
- **Zero settled NFL history.** Its `margin_stdev: 13.5` in
  `data/cache/calibration_stdevs.json` is a hardcoded prior, not a fit -- contrast
  `baseball_mlb: 4.025`, `icehockey_nhl: 2.5`, which carry the decimals of
  something computed.
- **The open book was admitted by a pre-L2 filter.** The 2026-08-18 NFL Week 1
  audit found 13 of 27 positions past the 5c spread line (to 20c) and 18 of 27
  with zero 24h volume. Gate 3.6 stops that class of row now -- **but Gate 3.6
  only runs at entry; nothing re-checks a position already held.**

**This is a freeze mechanism, not NFL policy**, and the `.env` comment says so.
It comes out when `strategy_state.json` (S10) ships; the durable rule is
`evidence_status: cold_start` -> pilot mode, not an impossible threshold left in
`.env` forever -- which is D4 waiting to happen again.

**The existing 24 positions are held, not flattened** (S2). Market-exiting a
5-20c-wide book pays exactly the illiquidity penalty Gate 3.6 exists to avoid.
Exit a ticker only if its spread is 5c or tighter *and* the exit price implies
less expected loss than holding to settlement.

### Verified

`min_edge_for` / `preflight_gate_status` / `size_order` on all three NFL market
prefixes, against the live config:

```
KXNFLGAME-...      floor=1.00  preflight=off  REJECTED: sport_disabled (nfl: ...set to 100%)
KXNFLSPREAD-...    floor=1.00  preflight=off  REJECTED: sport_disabled
KXNFLTOTAL-...     floor=1.00  preflight=off  REJECTED: sport_disabled
KXMLBGAME-...      floor=0.04  preflight=ok   APPROVED_CAPPED_MAX_BET
```

No `--min-edge` appears in any executing scheduler `.bat` (only `--unit-size` /
`--budget`), so the `.env` floor does reach the automated runs -- checked, per D4.
A scan preview showing NFL rows as `off` needs NFL rows with edges; the 08-27
preseason slate has no Odds API coverage, so that will first be visible on a
Week 1 scan.

### Also -- two things the freeze exposed

- **`doctor.py` could truncate a switched-off sport off the right edge.** The
  per-sport line printed `mlb=3.0%  nba=4.0%  ncaab=4.0%  nfl=100.0%
  worldcup=100.0%` on one row; at an 80-column terminal `worldcup=100.0%` was
  simply not visible. Disabled sports now print on their own **WARN** line
  (`sports OFF (floor >= 100%, unreachable): nfl, worldcup`). A rule nobody can
  see is a rule nobody checks -- the L2 lesson, and the S6 one.
- **The test suite inherited the operator's `.env` freezes.** Four tests broke on
  a config change that touched no code: `TestLiquidityGate` deliberately uses the
  real `KXNFLTOTAL-26SEP13CLEJAC-20` book from the L2 audit, and
  `test_sport_disable` uses an NFL ticker as its "other sports are untouched"
  control -- both now rejected at `sport_disabled` before reaching the gate under
  test. New autouse fixture `_ignore_operator_sport_freezes` in
  `tests/conftest.py` drops floors >= 1.0 from `_PER_SPORT_MIN_EDGE` for every
  test; a test that wants a sport off still sets it explicitly (`wc_off`). Fixed
  once at the seam rather than by editing four tickers, so the next freeze does
  not break the suite again. 864 pass.

---

## 2026-08-25 -- F4: NO-side Kelly damping at the expensive end

The calibration study's clearest actionable split. Over 380 settled bets:

```
              <30c        30-50c       50-75c       >=75c
YES      n=107 +31%    n=71 +17%    n=69 +14%     n=2 +32%
NO         n=8 -72%    n=55  +5%    n=29 -17%    n=39  -9%

YES total  n=249  $224  +22.4%          NO total  n=131  $157  -7.7%
```

**YES beats NO within every shared price band**, so this is the side, not merely
that NO bets sit at expensive prices. And the bleed is concentrated at/above 50c:
n=68, $90 staked, **-11.3% ROI** -- which is exactly the region R1's existing rule
never touched. `NO_SIDE_KELLY_PRICE_FLOOR` damps NO *below* 35c and leaves the
expensive end at full Kelly.

- **`NO_SIDE_KELLY_PRICE_CEILING`** (code default `0` = off; live `.env` `0.50`)
  is the mirror of the floor, reusing the same `NO_SIDE_KELLY_MULTIPLIER`. One
  new number, no new gate, no new concept.
- **The 35-50c pocket is deliberately untouched** -- at +5.3% ROI (n=55) it is
  the one profitable NO band, and it is positive in both eras (+0.8% Mar-May,
  +37.4% Jun-Aug). A blanket NO dampener would have taxed it for nothing.
- Kelly is the binding lane above ~60c (the flat unit floor binds below ~30c), so
  damping there actually changes order size. Verified on the live config at
  bankroll $92, batch 5, 12% edge:

```
      price   YES ct   NO ct
       0.45        3       3     <- pocket, untouched
       0.50        3       2
       0.75        5       2
       0.85        8       4
```

### Why damped and not gated

A hard reject above 50c would have saved $10.24 of the book's $38.01 P&L, which
is tempting. But that population is **+4.8% in Mar-May and -16.0% in Jun-Aug**,
concentrated in MLB totals (n=28, -15.0%) and MLS totals (n=12, -22.5%) -- not
uniform enough to justify permanently blinding the system to it. Halving exposure
captures most of the benefit and keeps the population generating settlements to
re-measure against. Revisit after ~50 more NO settlements.

The threshold is also insensitive: blocking anywhere in 0.45-0.75 saves $6-10, so
0.50 is not a fitted parameter, it is the round number in a flat region.

### Also

- **+21 tests** (`tests/test_no_side_ceiling.py`) -- damping at/above the ceiling,
  the pocket left alone, default-off, no double-application with R1's floor, YES
  never touched, and `reload_risk_config` wiring. 864 pass.
- The reload test stubs `load_dotenv`: `reload_risk_config` calls it with
  `override=True` (correct -- it re-reads `.env` from disk), which would otherwise
  clobber the monkeypatched var back to the developer's own `.env` value. It also
  restores the module global by hand, since monkeypatch cannot undo an assignment
  made *inside* the call under test.

---

## 2026-08-25 -- F3: calibration study; World Cup switched off

`scripts/backtest/calibration_study.py` (new) asks the question none of the risk
knobs ask: **is the claimed edge real?** For each of 390 settled bets it compares
the model's probability (`fair_value`) and the market's (`market_price_at_entry`)
against the outcome. Findings:
`docs/my-documents/repo-reviews/2026-08-25-calibration-study.md`.

### The model is measurably worse than the price it bets against

```
n=390   model 57.0%   market 42.2%   realised 46.2%
        Brier(model) 0.2270   Brier(market) 0.2037
```

Brier(market) - Brier(model), 95% CI **[-0.0405, -0.0068]** -- entirely below
zero. And it holds in **6 of 6 months**, not as a pooled artefact. The
Brier-optimal weight on the claimed edge is **lambda = 0.16, CI [-0.04, +0.42]**:
roughly a sixth of each claimed edge is supported by outcomes.

The one test selection cannot explain -- hold the market price fixed, split by
claimed edge -- is more interesting than a flat "no signal":

```
price <=32c   hi-edge half wins +10.8 pts more than lo-edge   (real signal)
price 32-51c                    +6.2 pts
price >=51c                    -10.8 pts                       (INVERTS)
```

Genuine information on longshots; it inverts on favourites. That independently
reproduces C4 (`high` confidence Brier 0.2514 vs `medium` 0.2153) from a
different direction.

**Two corrections to the same-day betting-logic review**, which read the *trade*
log -- clobbered 2026-06-03, retaining only 119 June-onward rows. The settlement
log kept the full history (380 settled with cost, back to March):

| Review said | Actual |
|---|---|
| -20.1% ROI | **+10.0%** ($381.66 staked, +$38.01) |
| spread -28.2%, total -13.3% | **spread +39.7%**, game +8.4%, total -9.2% |
| fees 3.6% of stake | **4.3%** ($16.40) |

A sampling error on my part, not a repo defect -- `backtester.py`,
`model_calibration.py` (C8) and the R8 review all read the settlement log
correctly. F1 survives and strengthens: **$16.40 of unrecorded fees against
$38.01 gross -- 43% of the return**, taking +10.0% to +5.7%.

The Mar-May (+28.2%) to Jun-Aug (-17.5%) swing is a **composition change, not
decay**: NCAAMB (+26.9%, n=56) and MLS (+130.7%, n=35) carried the good months,
NCAAMB's season ended, and what remains is MLB (negative in both eras, largest
block at $161 staked) plus World Cup.

### World Cup switched off

43 settled bets, **-43.2% ROI**, all YES. Model 22.9% / market 16.3% / reality
**13.9%** -- the price was near-exact and the model 9 points high.

- **`MIN_EDGE_THRESHOLD_WORLDCUP=1.0`** in `.env` and `.env.example`. Edge is
  bounded by 1, so a floor >= 1.0 can never be cleared: that is the idiom for
  switching a sport off, with no new gate and no new kill switch.
- **Gate 3 reports `sport_disabled`** (and `preflight_gate_status` returns `off`)
  when the floor is unreachable, rather than a nonsensical "5% < 100%" edge
  comparison. `min_edge_for` also short-circuits the fee term there, so the
  message reads 100% and not 101%.

### The override was a silent no-op for eight sports

Turning World Cup off surfaced a second bug. `_SUPPORTED_SPORTS` in
`app/config.py` listed only `mlb, nba, nhl, nfl, ncaab, ncaaf, mls, soccer`, but
`ticker_display._detect_sport()` also returns `worldcup, ufc, boxing, golf,
nascar, ipl, esports, tennis`. For those eight, `MIN_EDGE_THRESHOLD_<SPORT>`,
`SERIES_DEDUP_HOURS_<SPORT>` and `CROSS_CATEGORY_DEDUP_<SPORT>` **were read by
nothing** -- setting them did nothing at all, with no error. All eight added; a
test now asserts no `_detect_sport` output can be orphaned again.

### The soccer note is half retracted

`SPORT_MARGIN_STDEV` carried: *"the post-devig 'always-YES' lean on soccer
spreads is largely a REAL edge (Kalshi underprices goal margins -- placed
spreads hit 31% vs 19% paid), not a stdev bug."*

On 53 settled soccer-family spreads (WC + MLS), all YES: model 21.7%, market
15.5%, **realised 15.1%**. The market was near-exact; the 31% figure did not
survive the sample growing. The always-YES lean is a **model error, not a market
inefficiency**.

The *physical* half of the note stands -- the Poisson/Skellam argument for
stdev ~1.72-1.8 is unaffected, and fitting the stdev to Kalshi's board would
still import its pricing. So the stdev is probably not the culprit; the likelier
suspects are the mean-margin inference and the normal approximation to a
discrete, skewed goal margin. Untested either way.

### Also

- **+13 tests** (`tests/test_sport_disable.py`). 843 pass.
- `calibration_study.py` has a `--self-check` that pins a deliberate property:
  lambda is *weakly identified* when claimed edges are small (its curvature goes
  as `E[edge^2]`), so the script always bootstraps a CI and never quotes the
  point estimate alone.

---

## 2026-08-25 -- F1/F2: fees made visible, venue rejections made loud, limit price fixed

The first `/betting-logic-review` pass found 14 issues. The two Critical ones (F1)
and the cheapest High one (F2) are fixed here. Full report with evidence:
`docs/my-documents/repo-reviews/2026-08-25-betting-logic-review.md`
(11 further findings recorded there, unfixed).

### F1a -- trading fees were invisible in both directions

Nothing subtracted a fee before a bet, and nothing captured one after. The post-trade
half is the subtler bug: `log_trade` reads `order.get("taker_fees_dollars", "0")`, but
the **Kalshi v2 create-order response carries no fee fields** (nor `status` -- which is
why 129 of 166 rows in the trade log say `status: "unknown"`). So every trade recorded
`taker_fees: "0"` and `calculate_pnl` computed `net_pnl = revenue - cost - 0`.

Measured over the 119 settled trades:

```
stake            $140.97
reported P&L     $-28.32   (-20.1% ROI)
est. taker fees  $  5.14   (  3.6% of stake)   <- never recorded
fee-adjusted     $-33.46   (-23.7% ROI)
```

In the units Gate 3 works in that is **1.02c per contract against a 3.0-4.0c edge floor**
-- the gate was passing bets on a quarter to a third less edge than it believed, and up to
58% less at 50c where the fee peaks. The per-order `ceil()` added ~13% on top of the linear
term (0.90c -> 1.02c) because this bankroll places 1-7 contract orders.

This matters beyond the P&L line: R7, C11, R28 and every per-sport `MIN_EDGE_THRESHOLD_*`
were calibrated on fee-free ROI, and the fee is *price-dependent* (maximal at 50c), so it
does not wash out as a constant -- it penalises exactly the mid-price band those rules
reason about.

- **New `scripts/shared/fees.py`** -- `taker_fee(contracts, price)` (exact, incl. the
  per-order roundup) and `fee_per_contract(price)` (the linear term). The fee is dollars of
  EV per contract, the same units as `edge = fair_value - market_price`, so it composes
  with the edge directly -- no division by price. Self-check via `python scripts/shared/fees.py`.
- **`min_edge_for()` returns `base_floor + fee_per_contract(opp.market_price)`.** Both
  callers -- Gate 3 in `size_order` and the R18 `preflight_gate_status` scan preview -- route
  through it, so the preview cannot promise "ok" on a row the executor will reject.
- **Kelly sizes off `max(0, edge - fee_per_contract(price))`.** Sizing on gross edge
  over-bets by `fee/edge`, roughly a third at this bankroll's typical 3c edges.
- **Settler backfills real fees.** `fetch_fill_fees()` reads `/portfolio/fills` (keyed by
  `order_id`, summed across partial fills) and stamps the charge onto the trade before P&L.
  `trade_fees()` falls back to the *modelled* fee rather than to zero -- falling back to zero
  is what made the cost invisible in the first place -- and tags `fee_source`.
- **`KALSHI_FEE_RATE`** (default `0.07`) in `app/config.py` `GateThresholds`. Kalshi has
  changed this rate before; `0` restores fee-blind behaviour.

**Not done:** historical `net_pnl` on the 119 already-settled rows is not recomputed. The
backfill only touches trades as they settle, so calibration run against the existing book
still reads ~3.6% optimistic.

### F1b -- the venue rejected every order for 5 days, silently

Kalshi geo-blocked the account on 2026-08-20 (*"Nevada residents are not currently allowed
to open positions in Sports, Elections and Entertainment"*). 13 consecutive rejections
through 2026-08-24. Nothing alerted: every consumer of the trade log **filters**
`status == "error"` rows -- correct for exposure math, but it meant a dead venue produced no
signal anywhere, and the 4:50 AM digest reported five clean days.

- **`load_failed_orders()`** in `daily_summary.py` collects error rows inside the window.
- **`render_report` prints them above the P&L**, grouped by reason with counts, so a dead
  venue cannot be scrolled past.
- **`_error_reason()`** extracts the code textually -- `_record_failure` truncates the API
  body, so the stored JSON is cut mid-string and never parses.

**Still open (not a code question):** whether the Nevada restriction is permanent. If it is,
Kalshi sports is dead for this account and Polymarket US becomes the only venue -- which
materially changes ROADMAP Priority 0.

### F2 -- the limit price was posted one cent below the ask

`size_order` computed `price_cents = int(opp.market_price * 100)`. That truncates,
and `0.29 * 100 == 28.999999999999996` in binary floating point -- so a 29c ask
posted a **28c limit**, which never fills. Checked against all 99 cent values:
**29c, 57c and 58c** were affected. Silent by construction -- the order rests
rather than erroring.

Confirmed in the trade log. Every order whose posted limit differs from its entry
price is one of those three cents, and all three are `fill_status: "resting"` --
3 of the 4 resting rows in the entire history:

```
KXNHLTOTAL-26JUN11VGKCAR-5       ask=0.57  posted=56c  resting
KXMLSTOTAL-26JUL22LAFCRSL-3      ask=0.57  posted=56c  resting
KXNFLSPREAD-26SEP13NYJTEN-TEN8   ask=0.29  posted=28c  resting
```

- **`price_cents = math.ceil(round(opp.market_price * 100, 6))`.** The
  `round(..., 6)` kills the float noise (`28.999999999999996` -> `29.0`).
- **The `ceil` is load-bearing, not belt-and-braces.** Polymarket prices off
  Gamma's `bestAsk`, which is *not* cent-aligned (`0.235`, `0.501`, ...) while the
  venue takes 2dp -- a plain `round()` would under-post a `0.501` ask at 50c. For a
  marketable buy the limit must never round *down* below the ask.
- Both venues share this value: Kalshi via `_build_v2_order_body`
  (`"price": f"{yes_price_cents_eff / 100:.4f}"`, with NO orders reaching the book
  as `100 - no_price_cents`), Polymarket via `"price": {"value": ...:.2f}`. One
  fix, both venues.
- **+111 tests** (`tests/test_limit_price.py`): all 99 cent values round-trip, the
  three broken cents pinned as explicit regressions, NO-side coverage, and sub-cent
  asks never under-posted.

### Also

- **New `/betting-logic-review` skill** (`skills/betting-logic-review/`) -- the audit that
  produced this entry, made repeatable. Verification-first: it runs a battery of checks
  against the live trade log and odds cache before reading any code, because that is where
  both of these findings actually came from. Registered in `scripts/setup/link_skills.ps1`.
- **+139 tests** (`tests/test_fees.py`, `tests/test_limit_price.py`, plus
  rejected-order coverage in `tests/test_daily_summary.py`). 830 pass.
- **`no_fees` fixture** in `tests/conftest.py` -- the C11 price-complement and per-sport-floor
  tests pin exact pre-fee arithmetic and are testing something orthogonal, so they opt out
  rather than re-deriving every expected number.

---

## 2026-08-25 -- Streamlit dashboard removed

The `webapp/` Streamlit dashboard is deleted from the repo and the hosted
`edge-radar.streamlit.app` deployment is being taken down. **The CLI plus the scheduled
email reports are now the entire operating surface.** No scan, gate, sizing, execution,
or settlement behavior changed -- the dashboard was always a second front end over the
same `scripts/` code, never a code path of its own.

**Deleted:** `webapp/` (app, services, theme, favorites, 5 view pages, `.streamlit/`
config), `docs/web-app/` (LOCAL.md, CLOUD.md), `tests/test_webapp_env_registry.py`, and
the `.claude/skills/developing-with-streamlit/` bundle (89 files -- a generic Streamlit
authoring skill with nothing left to author).

**Code changes (three real ones, the rest are comments):**

- `scripts/kalshi/kalshi_client.py` -- `_resolve_key_content()` no longer falls back to
  `st.secrets["kalshi"]["private_key"]`; it reads `KALSHI_PRIVATE_KEY` only. This was the
  last `import streamlit` in `scripts/`. Local runs were already on
  `KALSHI_PRIVATE_KEY_PATH`, so nothing in the live pipeline used the removed branch.
- `scripts/lint/check_config_centralization.py` -- `SEARCH_DIRS` drops `webapp`. The
  `# config-bootstrap` escape hatch **stays** (it is a host-shaped exception, not a
  Streamlit one) but no longer has any tagged line in the tree.
- `pyproject.toml` -- packages `["app*"]`, was `["app*", "webapp*"]`.
- `requirements.txt` -- `streamlit>=1.33.0` dropped. `pandas` stays: it is a real
  dependency of backtesting and report generation, not just the dashboard (see Q5,
  2026-04-22, which promoted it off streamlit's transitive install).
- `.devcontainer/devcontainer.json` -- no longer pip-installs streamlit, runs
  `streamlit run` on attach, or forwards port 8501.
- `.gitignore` -- `.streamlit/secrets.toml` entry removed.
- `reload_risk_config()` and the import-time gate snapshot are **unchanged** and still
  correct: the staleness they guard against is a property of any long-running host, not
  of Streamlit. Their docstrings and the CLAUDE.md callout were reworded accordingly.

**`.claude/html/index.html`** (the published Pages ops page) drops both
`edge-radar.streamlit.app` links -- the hero CTA and the Quick Links card.

**ROADMAP.** The Tier-5a Dashboard backlog is marked dropped: D3, D6, D10, D12, D13,
D15, D17, D18, D19 all targeted the Streamlit app. Shipped D-items and the A10/A11 rows
stay in the Completed index as history, annotated with the removal. **Priority 4 (Web App
Evolution) is not cancelled** -- it always began at the service layer (A2 -> A3 -> A4),
and A9 was a React front end, never Streamlit; only its "the dashboard caught up to the
CLI" framing note was rewritten. Q6 no longer cites `webapp/services.py` as a
`sys.path` offender.

Prior CHANGELOG entries that describe the dashboard are left intact as historical
record.

---

## 2026-08-24 -- Futures: `Weekly-Futures-Execution` re-enabled; golf weekly tour stops rejected on cost/benefit

### `Weekly-Futures-Execution` is live again

The task had been disabled since 2026-07-23 "pending a manual futures cycle in preview"
-- C10 had just made futures capable of clearing Gate 4 for the first time, so the next
Saturday run would have been the first-ever live order through an unexercised path. That
preview cycle ran today: 154 Kalshi futures markets, outrights fetched for the 4 active
sports (NFL/NBA/NHL/MLB, 4 Odds API requests), **0 opportunities above the 3% edge
floor**. The task was then enabled and fired manually via `schtasks /run` ->
`LastTaskResult=0`, report written to `reports/Futures/schedulers/`, **0 orders placed**.
The execute path is now exercised end-to-end, which is exactly what the disable was
waiting on.

It places **real** orders from here (`DRY_RUN=false`). Blast radius per run:
`--max-bets 3 --min-bets 1 --budget 10% --unit-size 1`, under `MAX_BET_SIZE=8` and the
full gate chain. Halt with
`Disable-ScheduledTask -TaskPath "\Edge-Radar-MikesAILab\" -TaskName "Weekly-Futures-Execution"`.

Worth noting: the paired `Email-Weekly-Futures` job (Sat 9:20 AM) was **never disabled**,
so for five weeks it emailed a report that the execution task was no longer producing.
Re-enabling closes that gap rather than creating it.

**Doc/code drift corrected.** Every doc said the task runs `--budget 5%`; the `.bat` has
always passed `--budget 10%%`, and its own header comment said 5% too. The docs and the
header now match the code. **Sizing behavior is unchanged** -- only the description was
wrong, and picking which number to keep is a bankroll decision, not a docs fix.

### Golf weekly tour stops: investigated, not viable, not built

Looked at extending `KXPGATOUR` from the 4 majors to the full PGA Tour calendar.
**Rejected on cost/benefit.** Recording the findings so this does not get
re-investigated from scratch in six months.

**There is no free consensus feed for non-major golf.** Four sources checked:

| Source | Golf outrights | Verdict |
|:-------|:---------------|:--------|
| The Odds API (have it) | 4 majors only | No tour-wide key exists -- confirmed against `/v4/sports?all=true` (176 sports, inactive included) *and* on their published coverage page |
| ESPN | Calendar + field, `odds count=0` | Schedule data, no prices |
| SportsGameOdds | Covers `PGA_MEN` / `LIV_TOUR` | Free "Amateur" tier is 8 leagues (NFL/NBA/MLB/NHL/CFB/CBB/UCL/MLS) -- golf excluded. Golf tiers are $99-299/mo |
| Polymarket (have it) | 2 novelty props only | No winner markets, so no cross-venue anchor either |

The only workable feed is **DataGolf** `betting-tools/outrights` (win odds from
11 books, every tour event), which needs a **Scratch Plus** membership at
**$30/month or $270/year** -- API access is Plus-only, the $190/yr Basic tier
excludes it.

**What killed it was the gate math, not the price.** Measured against the live
30-player TOUR Championship board:

```
pass Gate 3.6 (spread) : 30/30   <- liquidity is excellent, 0-1c spreads
pass Gate 3.5 (price)  :  1/30   <- MIN_MARKET_PRICE = 0.10
pass BOTH              :  1/30
```

Only Scheffler at 22c clears; the rest of the field sits at 1-9c. That is
structural: a 30-player winner market averages 3.3c per player, and a *regular*
tour stop is 120-156 players, where the favourite prices around 8-12% -- so a
full-field event would likely clear **zero** markets. The NO side does not
rescue it either, since a 1c player's NO sits at 99c and Gate 4.6b demands >=8%
edge on any NO bet, which is arithmetically impossible up there.

So the subscription would buy roughly **one candidate per tournament**, which
then still has to clear the 3% edge floor and composite >= 6.0 -- and futures
have produced **0 bets in 166 settled trades**. At a ~$92 bankroll with
`MAX_BET_SIZE=8`, $270/yr is about 3x the bankroll per year. Not worth it.

Revisit only if the bankroll grows enough that $270/yr is noise, or if
`MIN_MARKET_PRICE` is ever lowered for golf specifically -- though that floor is
exactly the lottery-ticket protection, and it is already the subject of an open
experiment at 0.10.

### The 4 majors are unaffected and verified working

Majors keep pricing off The Odds API for free, and re-enabling
`Weekly-Futures-Execution` means they now reach execution automatically.
Verified end-to-end today rather than assumed, since the path had not run since
July and would not naturally fire again until April 2027:

- All 4 major keys return data **year-round** -- 2027 futures are already priced
  (83-107 outcomes, 3-7 books each); de-vig gives Scheffler 12.6-13.1% across all four.
- Title routing correct on all 4, and correctly returns `None` for weekly stops
  and for qualifiers.
- Confirmed against 1,588 historical `KXPGATOUR` markets that majors really do
  arrive under this series: The Open Championship (164 markets) and U.S. Open
  (156) both routed; "The Open Last-Chance Qualifier" (16) correctly skipped,
  alongside 15 non-major stops.

Expect ~1-2 candidates per major, 4x/year: a major is a 100-156 player field, so
by fair value only the favourite clears the `MIN_MARKET_PRICE` floor. Small, but
it costs nothing.

---

## 2026-08-19 -- Email: AgentMail retired, all eight scheduled email tasks moved to Resend

AgentMail's send path failed for seven hours on 2026-08-19 while its read API kept
returning `200` -- `inboxes.list()` was healthy the whole time and every
`messages.send()` came back `403 message_rejected`. From the caller's side that is
indistinguishable from an outage, and nothing complained, because the only thing that
would have complained sends by email. Every Edge-Radar `Email-*` task migrated to
[Resend](https://resend.com) the same day, sending from the verified domain
`send.mikesailab.com`.

### What changed

**New: `scripts/custom/Python/send_report_email.py`** -- one send path for all eight
tasks. It imports the canonical sender documented in
`My-AI-Tools/Resend-API/README.md` rather than reimplementing the `POST`, so a key
rotation or another provider swap lands in one file. On top of the plain sender it adds
Edge-Radar defaults (`NOTIFY_EMAIL` / `RESEND_FROM`) and a **delivery stamp**:
`logs/last_email_sent.json` plus an append-only `logs/email_sends.jsonl`. The stamp is
the direct lesson of the outage -- a file that goes stale can be alerted on when mail
itself is what is broken. `--check` probes domain verification without spending quota,
but note that a verified domain is necessary, not sufficient: a read probe and a send
fail independently, which is the whole reason this entry exists.

**The nine report-emailer shell scripts** (`scripts/custom/Shell-Scripts/Run-Reports/`,
gitignored, so this appears in no diff) each ended their `claude -p` prompt with *"Use
the agentmail skill to send"*, leaving the inner Claude to author its own API call every
night. It did -- 40+ near-duplicate `send_*_email_<date>.py` files under
`scripts/custom/Python/`, each with the provider, the API key name, and an inbox id
hardcoded. That is why a provider migration touched forty files instead of one. The
prompts now name an exact command (write HTML + text to `.claude/temp/`, run
`send_report_email.py --subject ... --tag ...`), forbid writing bespoke send code, and
require the returned message id in the final output as proof of send. Subject lines moved
into the command, so there is one source for them rather than two that can drift.

**Config knobs.** `AGENTMAIL_INBOX` -> `RESEND_FROM` (+ optional `RESEND_REPLY_TO`) in
`.env.example`, `webapp/services.py`, `.env_sreamlitio`, and
`tests/test_webapp_env_registry.py`. `NOTIFY_EMAIL` is unchanged. The `agentmail>=0.4.5`
pin is gone from `requirements.txt` -- Resend needs no SDK, just the `requests` already
required for Kalshi.

**The API key deliberately does not live in `.env`.** `RESEND_API_KEY` is a Windows
**User**-scoped environment variable (`setx RESEND_API_KEY "re_..."`). Task Scheduler
builds a fresh environment at every launch, so a rotated key is picked up on the next run
with no file edit, no logoff, no reboot -- while an already-running process (an open
terminal, the Streamlit app) keeps its stale copy and must be restarted. A User variable
is also invisible to `SYSTEM`, which is why these tasks run as `mikes`; under `SYSTEM`
every send would fail into a warning while the run still exited 0.

### Verified

`--check` returns `OK send.mikesailab.com status=verified`; a direct send returned a
message id; and `Email-Daily-Summary` was run end-to-end through Task Scheduler under its
real principal. Docs updated: `docs/task-schedules/README.md` (placeholders, Template C,
per-task tables, troubleshooting, flow diagram).

Provider detail and the full porting table: `My-AI-Tools/Resend-API/README.md`.

---

## 2026-08-18 -- L2: the illiquidity Hard Stop finally exists in code

Triggered by an operator question -- "I'm seeing a ton of American football bets in the
scheduled runs, is this a bug?" -- after past single-sport clusters turned out to be one.

### What the book actually looked like

24 of 27 open positions (89%), and $29.73 of $34.27 exposure (87%), were **NFL Week 1**
(Sept 9-14) -- games 22-27 days out, on a ~$92 bankroll. NFL's share of trades by month:
4% in June, **0% in July, 66% in August**. A real regime change, not variance.

The concentration itself is explainable and not a bug. `no_date_filter_execution*.bat`
(5:20 AM + 11:00 AM PT) scan every posted date; in mid-August the NFL Week 1 board is up
while only MLB and MLS are in season, so NFL wins the composite ranking on essentially
every run, and the *same static 16-game slate* is re-scanned twice daily. `SERIES_DEDUP_HOURS=48`
never bites because re-bets land 3+ days apart (GB/MIN was bet Aug 4, Aug 8, Aug 13), and
`CROSS_CATEGORY_DEDUP=false` means SPREAD/TOTAL/GAME on one game are three *different*
Kalshi events, so `MAX_PER_EVENT=2` never trips -- 10 of 14 games carried 2 correlated
positions (e.g. TB moneyline *and* TB -11.5).

The edge math checked out. Strike parsing reads Kalshi's authoritative `floor_strike`, not
the ticker suffix; calibration stdevs were fresh (Aug 17) with NFL at the hardcoded
defaults; every logged edge reproduces from the normal-CDF model. No over-claim.

### The actual defect

**13 of 27 open positions breached the documented 5% illiquidity Hard Stop, and 18 of 27
had zero 24h volume.**

`CLAUDE.md` has listed *"the market is clearly illiquid (spread > 5%)"* as a non-negotiable
Hard Stop since launch, and `docs/kalshi/kalshi-sports-betting/MLB_FILTERING_GUIDE.md`
repeats it as a graduated rule (>5% skip / 3-5% reduce size / <3% full size). **Neither was
ever implemented.** The rule bound only on a human or an agent reading the file -- never on
`kalshi_executor.py`.

Spread reached scoring through exactly one path: the soft composite term
`liquidity = max(0, 10 - spread * 20)`, weighted 20%. That term saturates at 0 only at a
**50c** spread, so a 20c-wide book still scored **6.0/10 on liquidity** and cleared
`MIN_COMPOSITE_SCORE=6.0` on the strength of a big tail edge. Worked examples from the live
board:

```
KXNFLTOTAL-26SEP13CLEJAC-20   bid 0.77 / ask 0.97   20c spread   0 vol/24h
KXNFLTOTAL-26SEP13WASPHI-69   bid 0.07 / ask 0.25   18c spread   0 vol/24h
KXNFLSPREAD-26SEP13NODET-NO5  bid 0.05 / ask 0.20   15c spread   0 vol/24h
```

Two things follow, and both matter more than the concentration:

1. **The edge is measured against an ask nobody trades at.** Buying the ask in a 20c-wide
   book means a large part of the claimed 6-15% edge *is* the spread.
2. **There is no exit.** With zero volume and a bid 20c below, these positions are held to
   settlement whether or not the thesis survives.

The largest single position, `KXNFLTOTAL-26SEP13WASPHI-69` (NO, 7 contracts), risks $6.16
to win $0.84 and would have to be sold at 0.75 against the 0.88 paid.

### The fix

New **Gate 3.6**, between the R7 price floor and the composite gate:

- `MAX_BID_ASK_SPREAD` (default **0.05**) -- absolute dollars on a $0-1 contract, matching
  both the documented "5%" and the existing `liquidity` term's units. `>` not `>=`, so a 5c
  spread itself passes, per the documented wording. 0 disables.
- `MIN_MARKET_VOLUME_24H` (default **0**, off) -- contracts traded in the trailing 24h.
  Catches books with a tolerable spread that simply never trade, which a spread test alone
  cannot see. Ships off because spread is the documented rule and this is a policy addition.

Scorers now stash the raw microstructure on every `Opportunity` via
`edge_detector.liquidity_details()` (`bid_ask_spread`, `volume_24h`, `open_interest`).
The gate reads *that*, never `liquidity_score` -- the composite term is lossy and cannot
distinguish "wide" from "hopeless". Wired on all four scoring paths: Kalshi sports
(game/spread/total), Kalshi futures, Polymarket futures, Polymarket games.

**The gate fails open by design.** An Opportunity carrying no recorded spread is not
rejected -- a hand-built Opportunity, a replayed R26 scan cache, or a future scorer that
forgets the field would otherwise be blocked wholesale. Missing means unknown, and this gate
rejects only on evidence. `preflight_gate_status()` mirrors that and reports `illiq`.

Verified against a live NFL scan: of 32 scored rows, **18 now flag `illiq`**, 7 of which
previously cleared both the edge floor and the composite gate and would have reached order
placement.

### `doctor.py` now prints the reject gates

CLAUDE.md points at `python scripts/doctor.py` as "the source of truth for what is actually
running", but its Configuration block only ever printed **sizing** knobs -- DRY_RUN,
UNIT_SIZE, KELLY_FRACTION, MAX_DAILY_LOSS, MAX_OPEN_POSITIONS, MAX_PER_EVENT. Every reject
gate was invisible there, including the two that had just been added, and including
`MIN_MARKET_PRICE`, which the CLAUDE.md Risk Limits block explicitly flags as an open
experiment. A disabled safety gate looked exactly like an enforced one: nothing at all.

That is the same failure mode as the gate itself -- a rule nobody can see is a rule nobody
checks -- so the new `Reject Gates` section prints Gates 3 through 9 with the values actually
resolved, per-sport overrides included. A gate switched **off** reports `WARN` rather than
`PASS`: 0 or permissive is a legitimate setting, but it should never scroll past looking
like a healthy default. Verified in both directions, e.g. with everything opened up:

```
WARN  Gate 3.5 MIN_MARKET_PRICE = 0 -- DISABLED -- no lottery-ticket floor (R7)
WARN  Gate 3.6 MAX_BID_ASK_SPREAD = 0 -- DISABLED -- illiquid books can execute (L2)
WARN  Gate 4.8 ALLOW_LIVE_BETS = true -- OPEN -- in-progress games can execute (L1)
WARN  Gate 7   SERIES_DEDUP_HOURS = 0 -- DISABLED -- same matchup can be re-bet freely
```

Warnings do not fail the doctor run; they are surfacing, not enforcement.

Both knobs were also written into the live `.env` at their code defaults
(`MAX_BID_ASK_SPREAD=0.05`, `MIN_MARKET_VOLUME_24H=0`). Functionally a no-op -- an unset var
already resolves to the same value -- but it keeps them visible alongside the other tuned
knobs rather than implicit, and the comment block leads with the fact that the gate is on
whether or not the line exists.

### Considered and rejected: relative spread

`(ask - bid) / mid > 5%` is the more defensible rule for a board full of 10-20c longshots --
`KXNFLSPREAD-26SEP13ATLPIT-ATL11` at bid 0.13 / ask 0.15 passes the absolute test at 2c but
is 14% of its mid. Left absolute anyway: it is what the docs meant, what the existing
`liquidity` term already assumes, and switching would be a stricter *policy change* rather
than enforcing what was already written down. Revisit with settled data.

### Not addressed here

Neither is a code defect:

- **No days-out guard on sports -- proposed and declined.** The weather path bails past 7
  days (`weather_edge.py:190`); sports has nothing, so a no-date-filter run bets games 26
  days out. Raised as the obvious companion fix and **the operator declined it on
  2026-08-18** -- do not add a horizon clause without a fresh decision. Betting Week 1 early
  is intentional: those are the softest lines of the season, and the liquidity gate above
  already removes the untradeable end of that board, which was the real harm.
- **`CROSS_CATEGORY_DEDUP=false`** lets one game carry three correlated tickets. Left as-is.

The 24 open NFL positions were left alone -- with books 12-20c wide and no volume, exiting
costs more than holding to the Sept 9-14 settlements. Nothing has settled yet, so there is
no P&L evidence on the NFL cluster either way.

### Also noted

`tests/test_edge_detection.py::TestThreeWayDevig::test_three_way_uses_win_share` fails on
`master` independently of this work (confirmed by stashing these changes). Untouched here.

---

## 2026-07-31 -- scheduler cleanup: dead task removed, installer stopped duplicating live tasks

Two pieces of cruft surfaced while fixing the calibration loop.

### `MonthlyCalibration` removed

Registered as a monthly run of `model_calibration.py --days 30 --save`, it had **never once
executed** -- `Last Run Time` was still the Task Scheduler sentinel `11/30/1999` with
`Last Result 267011` ("task has not yet run"). Every calibration this repo has ever done
came from the weekly `Calibration` task, so once that task's window was widened the monthly
one was a pure duplicate against a stateless loop. Definition archived before deletion; the
recreate command lives in `docs/task-schedules/README.md` section 15, now a removal record.
Surviving weekly task re-verified after: Sun 7 PM, `Last Result 0`, next run 8/2.

### `install_windows_task.py` could silently duplicate or clobber live tasks

Every profile hardcoded an `Edge-Radar` task-folder path while the owner's live tasks sit
under `Edge-Radar-MikesAILab`. Neither direction of that mismatch was checked:

- pointed at a **different** folder (the status quo), `install` creates a parallel duplicate
  -- a second settler, or worse a second *execute* task placing real bets alongside the
  first;
- pointed at the **same** folder, it silently clobbers a live task, replacing a definition
  carrying a run-as principal and wake/retry policy with the minimal one `schtasks /Create`
  writes.

Same class of cruft as the dead task above, except these would actually fire.

Fixed: profiles now carry a `leaf` name with the folder applied centrally from a single
`TASK_FOLDER`, overridable per-run with `--task-folder`; `install` refuses when the same
leaf is already registered under any other folder, printing both paths, with `--force` to
opt in. The calibration leaf is now `Calibration`, matching the live task, so pointing
`--task-folder` at the real folder updates in place rather than making a twin. `status`
reports which folder it is inspecting, and the docstring's stale "Monthly 30-day (R16)"
description was corrected.

`--task-folder` is deliberately a CLI flag and not an env var: an installer-only,
Windows-only developer setting has no business in `app/config.py`, and
`check_config_centralization.py` correctly rejected the `os.environ` read first reached for.

`TASK_FOLDER` still defaults to `Edge-Radar` rather than any real folder -- defaulting at a
live machine's tasks would make clobbering the default behavior. The guard plus the flag
makes the choice explicit instead.

Verified: `install settle` SKIPs against the existing live `NightlySettle` and creates
nothing; with `--task-folder Edge-Radar-MikesAILab` all three overlapping profiles report no
conflict. All 24 live tasks intact afterwards, no strays created.

---

## 2026-07-31 -- pre-wager calibration preflight (REQUIRE_FRESH_CALIBRATION)

Follow-up to the C8 no-op below: a check that the calibration is actually current
*before* the executor sizes anything.

### Why age is the wrong signal

Every existing safeguard reported healthy throughout the failure. The weekly task ran on
schedule, exited 0, and rewrote the cache file every week; `CALIBRATION_STDEVS_TTL_DAYS=30`
saw a 0-5 day old file and was satisfied. The cache was fresh, green, and wrong -- it just
contained the hardcoded defaults.

So the preflight does not check age. `model_calibration.calibration_drift()` **recomputes**
what the calibrator would produce from current settled data and compares it to what is
cached. That distinguishes the two cases age cannot:

- a legitimate skip (too few samples) or hold (gap within noise) returns the baseline, and
  the cache holds the baseline, so they agree -- silent;
- a loop that is broken or behind the evidence produces a value the cache disagrees with
  -- flagged, with the sport, both values, and the sample count.

### Wiring

`execute_pipeline()` calls it before gathering portfolio state. Default posture is **warn**;
`REQUIRE_FRESH_CALIBRATION=true` makes it a hard stop on `--execute`. Preview runs never
abort -- you should always be able to look.

Warn-by-default is deliberate. A hard default block is the wrong trade for an unattended
system: most sports are legitimately out of season with too few settled bets to calibrate,
and halting all betting on a diagnostic is a worse failure than the miscalibration it
guards against. The import is local and any exception inside the check is swallowed -- a
diagnostic must not be able to take down the money path.

### A false positive caught before shipping

The first version audited against all-time settled data while the scheduled job runs
`--days 30`, and immediately reported `basketball_ncaab/spread` as drifted (cached 12.1 vs
"expected" 14.742, n=29). That was the check being wrong, not the cache: NCAAB has 29
settled bets all-time but far fewer inside 30 days, so the job legitimately skips it.
Out-of-season sports would have drifted forever. Fixed by auditing against
`SCHEDULED_CALIBRATION_DAYS`, with a test asserting it stays equal to the window in
`calibration.bat`.

Verified end to end by sabotaging the cache back to 3.45: preview warns and continues,
execute warns and continues at the default, execute refuses with
`REQUIRE_FRESH_CALIBRATION=true`. Restored afterwards; the healthy cache produces no output
at all.

New knob `REQUIRE_FRESH_CALIBRATION` (default false) in `app/config.py`, `.env.example`,
and the webapp registry -- `tests/test_webapp_env_registry.py` caught the missing webapp
entry, which is what it was built for. +5 tests (688).

---

## 2026-07-31 -- the C8 stdev loop had never calibrated anything: `--days 7` starved it

Asked to add a weekly calibration cadence. Checked the machine first. **The cadence
already existed**, and the real defect was elsewhere and worse.

### Cadence was never the problem

Three calibration tasks are registered under `\Edge-Radar-MikesAILab\`:

| Task | Schedule | Last run | Reality |
|:--|:--|:--|:--|
| `Calibration` | **Weekly**, Sun 7 PM | 7/26/2026, result 0 | the one actually doing the work |
| `MonthlyCalibration` | Monthly, day 1 | **11/30/1999 — never run** | dead duplicate the installer described |
| `Calibration Loader` | — | — | unrelated |

The cache timestamp (`2026-07-27T02:00:01Z` = 7/26 7:00 PM PDT) matches the weekly task's
last run exactly. So T3's premise -- "monthly cadence means ~30 blind days" -- was wrong,
and the ROADMAP entry has been corrected rather than quietly dropped.

### The real bug: a 7-day window cannot clear a 20-sample gate

The weekly task ran `model_calibration.py --days 7 --save`.

`save_calibration_stdevs()` is handed the **day-filtered** settled list, and
`_calibrate_one_stdev()` needs `_MIN_CALIB_SAMPLES = 20` rows **per (sport, category)**
before it will move a value. Only **~22 bets settle in any 7-day window across all sports
and categories combined**. No pair could ever reach 20.

So every weekly run skipped every sport and wrote the hardcoded defaults straight back.
That is why `data/cache/calibration_stdevs.json` was byte-identical to
`edge_detector.SPORT_*_STDEV`: **the closed calibration loop has been a silent no-op for
its entire existence.** It never once did the job C8 was built for.

| lookback | settled (all) | MLB totals visible | vs the 20-sample bar |
|:--|--:|--:|:--|
| `--days 7` | 22 | **17** | **SKIPS — writes the default back** |
| `--days 14` | 37 | 28 | calibrates |
| `--days 30` | 53 | 28 | calibrates |

### Fixes

- `scripts/schedulers/maintenance/calibration.bat`: `--days 7` → `--days 30`. **Gitignored
  — this, the actual fix, appears in no diff.** First real run moves
  `total_stdev.baseball_mlb` 3.45 → 4.005 (gap +16.1%, n=28, se=0.085), which drops the
  phantom edge on MLB high-strike unders below the R28 8% NO floor and blocks 21 of 25
  such bets (see the T1 entry below).
- `tests/test_calibration_config.py` (new, 6 tests): fails the build if the `--save`
  window is ever narrowed below 14 days, if `CURRENT_*_STDEV` drifts from
  `edge_detector.SPORT_*_STDEV` (a hand-copied duplicate that is the baseline every
  calibration multiplies against), or if the loop stops being stateless. Verified the
  window guard actually fires by reverting the `.bat` and watching it fail.
- `install_windows_task.py`: its `calibration` profile described a MONTHLY task that had
  never run and did not match the live weekly one. Reconciled to WEEKLY/Sun 19:00 pointing
  at the `.bat`, so there is one definition of the arguments.
- `model_calibration.py` docstring: corrected a claim that the loop "relies on the monthly
  loop compounding small corrections over time" -- wrong twice over. The loop is weekly,
  and it does **not** compound: `base_stdev` is the hardcoded baseline, never the prior
  cache value. Documented, because that statelessness is exactly what makes running it
  more often safe.

### Not fixed -- T4

Even with the window corrected, C8 cannot move a value until 20 of a market type's bets
have **settled**, which by construction happens after the flood. MLB totals reached 69% of
the book before any calibration could legitimately have data. No cadence or window change
addresses that; it needs a rule treating never-calibrated market types as suspect (higher
edge floor until first calibration, or a per-shape batch cap). Logged as T4, nothing
shipped. Relevant now: the Polymarket US seasonal games repoint is the next coverage
addition queued.

### `MonthlyCalibration` removed

The duplicate task was unregistered the same day (`schtasks /Delete`). It had **never once
executed** in its entire registered life -- `Last Run Time` was still the Task Scheduler
sentinel `11/30/1999` with `Last Result 267011` ("task has not yet run"). Every calibration
this repo has ever performed came from the weekly `Calibration` task instead, which makes
the monthly one pure cruft now that both would run `--days 30` against a stateless loop.

Its definition was archived before deletion and the recreate command is recorded in
`docs/task-schedules/README.md` section 15, which is now a removal record rather than a
task description. The surviving weekly task was re-verified afterwards: `Calibration`,
Sun 7 PM, `Last Result 0`, next run 8/2/2026, pointing at the fixed `.bat`.

`install_windows_task.py` also carries a note that it installs into the `Edge-Radar\` task
folder while the owner's live tasks live in `Edge-Radar-MikesAILab\` -- intentional, since
that file is a reference template rather than a turnkey installer for that machine, but it
means running it creates a parallel task rather than editing the live one.

683 tests.

---

## 2026-07-31 -- T1 resolved: the distance cap was measured and rejected; stale stdev calibration was the cause

The proposed T1 fix was a **cap on extrapolation distance** -- reject a totals bet whose
Kalshi strike sits more than ~1 sigma from the model's inferred mean. Backtested before
building. It does not survive.

### The cap would have made things worse

New tool `scripts/backtest/totals_distance_check.py` (re-runnable, mirrors
`correlation_check.py`). Extrapolation distance is recovered by inverting the normal CDF
from the stored `fair_value`, since `z = (strike - inferred_mean) / stdev` is exactly what
the model applied. Over **136 settled totals bets** -- read from the settlement log, not
the 41-row trade-log slice the first pass used:

| \|z\| bucket | n | W-L | WR | claimed | ROI |
|:--|--:|:--|--:|--:|--:|
| < 0.5 | 67 | 34W-33L | 51% | 60% | -1.1% |
| 0.5 - 1.0 | 32 | 18W-14L | 56% | 73% | **-29.5%** |
| **1.0 - 1.5** | **29** | **23W-6L** | **79%** | 89% | **+5.8%** |
| 1.5 - 2.0 | 5 | 4W-1L | 80% | 95% | -49.1% |
| > 2.0 | 3 | 2W-1L | 67% | 99% | -3.9% |

The 1.0-1.5 sigma band -- exactly where the MLB strike-12.5 bets sit -- is the **only
profitable bucket**. A cap at 1 sigma would have deleted the best band and kept the
-29.5% one. No cap was built.

### What the data actually says

The over-claim is **uniform across every bucket** (+9, +17, +10, +15, +32 points; +12%
overall, +16% MLB-only). A bias that does not vary with distance is not a distance
problem -- it is stdev calibration, which is already C8's job.

### Root cause: C8 was correct but stale

Running `model_calibration.py` today prints
`Calibrate baseball_mlb/total: base=3.45 gap=+16.1% (n=28, se=0.085) -> 4.00 (x1.161)` --
independently deriving the same +16% the backtest found. But the live cache, written
2026-07-27, still held **3.45, byte-identical to the hardcoded default**.

The reason is timing. MLB totals coverage landed **2026-07-20**, so at the 07-27 run fewer
than `_MIN_CALIB_SAMPLES = 20` had settled and the sport was skipped; the next scheduled
`MonthlyCalibration` was not until 08-01. **The flood ran for the entire blind window.**

### Action taken

Ran the calibration. `total_stdev.baseball_mlb` **3.45 -> 4.005**, verified live through
`_get_total_stdev()`. Note `data/cache/calibration_stdevs.json` is gitignored, so this
change appears in no diff.

Replayed over the 25 settled MLB NO-totals:

| | count | actual result |
|:--|--:|:--|
| Now blocked at Gate 4.6b (edge drops under the R28 8% NO floor) | **21 of 25** | 15W-6L, -$1.09, -3.1% ROI |
| Still placed | 4 | 3W-1L, -$5.19, **-63.4% ROI** |

**Honest read: the concentration is fixed, the selection quality is not.** Widening the
stdev removes 84% of the shape -- the volume problem originally spotted -- but the four
bets that still clear the floor are the *worst* performers in the group. Same "large
claimed edge = model error" pattern C4 found for confidence and C11 for sub-40c prices,
and the reason `KELLY_EDGE_CAP` exists. At n=4 that -63% is noise-level: a signal to
watch, not a result.

### T3 opened -- the structural lesson

`_MIN_CALIB_SAMPLES = 20` plus a **monthly** cadence means any newly-covered market type
can bet uncalibrated for up to ~30 days. This will recur on every coverage addition, and
one is already scheduled (the Polymarket US seasonal games repoint). Options logged, none
shipped: weekly calibration, event-triggering on first crossing 20 settled bets, or a
higher edge floor for market types that have never been calibrated.

Code added: `scripts/backtest/totals_distance_check.py`. No gate or model logic changed.

---

## 2026-07-31 -- MLB high-strike totals dominate the book (T1/T2 opened)

Operator observation: "under 13.5 or so runs in baseball" bets seemed to be placed far
more often than anything else. Investigated. Confirmed, and understated.

**Concentration.** Of 115 live trades, **31 are MLB totals (27%)**, **28 NO-side**, and
**14 sit on strike 13** -- one repeated wager shape is 12% of the whole book, against just
7 MLB moneylines in the same window. No gate prevents it: each bet is a *different game*,
so `MAX_PER_EVENT` and series dedup never engage, and `CROSS_CATEGORY_DEDUP` only collapses
categories within a single game.

**Calibration.** Those 28 settled NO bets went **18W-10L (64.3%)** against an **80.1%**
market-implied break-even -- **-12.6% ROI (-$6.28)**. Versus the market that is p=0.038
(marginal at n=28). Versus **the model's own claimed 89.7% fair value it is p=0.0003**.
Whether the bets are exactly -EV is not settled by 28 samples; that the model is wrong
about them is.

**Mechanism.** `consensus_total_prob` infers a mean total from the sportsbook line (~8.7
runs) and extrapolates to the Kalshi strike with a normal CDF at
`SPORT_TOTAL_STDEV["baseball_mlb"] = 3.45`. Strike 13 is **1.25 sigma** out, where the
answer comes from the stdev assumption rather than any book quote. There is a
**disagreement sweet spot**: near the line model and market agree, far out both approach
100% NO, and around 1.25 sigma the model says 89% NO against the market's 80%. Every MLB
game lists a strike in that window, so every game emits one near-identical NO bet. **R28's
global NO floor is 8% while the phantom edge averages 9.6%** -- the gate built to stop bad
NO bets sits just under the bias.

**Ruled out:** skew. The intuitive story (normal CDF understates a right-skewed tail) is
wrong here -- a negative binomial with the same mean and variance gives a *lower* P(>13)
(9.0% vs 10.6%), which would raise the model's NO fair value, not lower it.

**Most likely driver: adverse selection.** The model bets the games where its own noisy
inferred mean sits lowest relative to the strike, selecting the cases where that estimate
is most wrong -- the same winner's-curse pattern C4 found for high confidence and C11 found
for sub-40c prices.

**Relation to C11b.** That investigation measured *correlation* among the "four MLB unders
on one night" slate and correctly found none (totals rho -0.187, p=0.75). It never asked
why there were four. This is the answer: not a correlation problem, a generation problem.
C11b's conclusion stands; its question was the wrong one.

Opened as **T1** (concentration + calibration) and **T2** (the strike-boundary hypothesis).

### T2 verified same day -- no bug, hypothesis was wrong

T2 proposed that Kalshi's strike-13 market resolves YES on "13 or more" while the model
computes `P(> 13)` -- a 3.1-point systematic error toward NO on every totals bet in every
sport. Checked against the live Kalshi API for all 28 logged markets. It is wrong on every
count:

- **The ticker suffix is not the strike.** `KXMLBTOTAL-...MINCLE-13` carries
  `floor_strike: 12.5`; the suffix is a market index.
- `extract_strike()` reads **`floor_strike` first** (`edge_detector.py:1214`), so the model
  uses 12.5, not 13.
- Kalshi's `rules_primary` ("more than 12.5 runs ... resolves to Yes") and
  `strike_type: greater` match the model's `1 - norm.cdf(12.5)` exactly.
- `floor_strike` is a **half-integer on 28/28** markets, so no integer run total can tie the
  strike and the `>=` vs `>` distinction is mathematically moot regardless.

Recorded because the negative result is load-bearing: the cheap single-line explanation is
eliminated, so T1's cause lies in the model or in bet generation.

### The concentration is worse than first reported

The "27% of the book" figure understated it. MLB totals did not exist in the book until
**2026-07-20**, when the MLB spread/total coverage gap was closed. Before that date: 70
trades, **0** MLB totals. On and after: 45 trades, **31** MLB totals -- **69% of everything
bet since the coverage landed**. Within 11 days one bet shape took over two-thirds of all
betting.

### Caveats

All 28 bets sit in a single 11-day window, so this is not a broad sample and late-July
scoring is a real confound. Two checks against that: losses are not concentrated in one bad
day (1 of 11 days had zero wins, n=1), and treating each *day* as the unit gives a 66.5%
mean win rate against the per-bet 64.3% -- so the result is not an artifact of a few
heavily-bet days. The time trend is the useful cut: **first 5 days 11W-1L (+6.7% ROI),
after that 7W-9L (-18.3%)**. An early hot streak masked the shape for a week, which is
itself a caution against reading the opening days of any newly-covered market as
validation.

Also documented **PM2e**: the post-C10/C10b risk posture. The bugs themselves cost almost
nothing (0 Polymarket trades, 0 prediction bets, 0 trades over `MAX_BET_SIZE`, 0 NBA/NCAAB
bets in the band the stale Cloud config would have admitted), but the *fixes* made Gate 4
reachable on futures and games for the first time, on surfaces with zero settled trades,
while the venue is armed and executing unattended. T1 is the cautionary precedent for what
happens when a composite lets a new bet shape through at scale.

No code changed in this entry -- findings and roadmap only.

---

## 2026-07-31 -- C10b: the games composite had the same unreachable Gate 4

C10 (2026-07-23) diagnosed the futures composite scaling edge as `min(10, edge * 20)` --
saturating at a 50% edge instead of the sports composite's 10% -- and traced it to a
copy-paste from the `liquidity` line above it on the launch-day commit. It fixed
`scripts/kalshi/futures_edge.py` and `scripts/polymarket/polymarket_futures_edge.py`.

It missed `scripts/polymarket/polymarket_games_edge.py`. That file was written on
2026-07-20, three days before C10, and had copied `edge * 20` from the Polymarket futures
file -- which had itself copied it from its own `liquidity` line. A copy of a copy of the
same bug, so it carried no independent rationale either.

### Same disease, independently confirmed on this surface

Clearing `MIN_COMPOSITE_SCORE=6.0` required roughly **15% edge at high confidence, 26% at
medium, 38% at low**, against Polymarket game edges that run **1-7%** in practice.

The evidence log settles it: across **362 logged Gamma game rows**, not one ever reached
composite 6.0. The maximum observed was **5.30**. Gate 4 was structurally unreachable
here exactly as it was for futures -- 330 of those rows were stopped earlier at Gate 3
(edge) and 32 reached Gate 4 only to die on `score`.

### Not a floodgate

Replayed through the shipped code over those same 362 rows: only **5 (1.4%)** newly clear
Gate 4, all marginally (composite 6.02-6.26), and each still faces gates 3.5 (price), 4.5
(confidence), 4.6b (NO floor), 5, 6, and 7. The 330 edge-gated rows are unaffected --
they never reach Gate 4 at all.

**No live behavior changes.** Gamma-sourced game rows carry no US `market_slug`, so they
are auto-excluded from execution and remain dry-run evidence only. This matters for the
seasonal US games repoint on the roadmap: without it, that surface would have inherited
the same arithmetically-unreachable gate a third time.

### Two divergences kept deliberately

- **Liquidity stays `book_spread * 100`** (vs `spread * 20` on the Kalshi paths). Rows
  wider than `MAX_BOOK_SPREAD = 0.10` are already dropped upstream, so `* 20` would
  compress every surviving row into 9.8-10.0 and the term would carry no information.
  `* 100` spreads the admissible 0-0.10 band across the full 0-10 range. This does make
  games and futures composites non-comparable when they are merged and ranked together,
  but it errs strict and is the better-calibrated of the two -- not worth loosening a
  second term in the same change.
- **`high: 9` stays uncapped**, on C10's own precedent. C4 capped high->medium for
  *Kalshi sports* on 306 settled bets (F49) and explicitly scoped everything else out;
  there is still no settled Polymarket data. Worth revisiting when PM3 settlement lands
  -- this path prices against the same Odds API consensus as sports, so C4's *reasoning*
  plausibly transfers even though its evidence does not.

+4 tests (677), including a cross-surface parity check against the sports composite,
scoped to medium confidence so it does not silently encode the `high` decision above.

### C10c -- the same scale survives in all 7 prediction scanners (logged, not fixed)

The propagation sweep for this change grepped the repo for the old form and found
`edge_score = min(10, edge * 20)` still in `companies_edge.py:167`, `crypto_edge.py:227`,
`mentions_edge.py:201` and `:269`, `politics_edge.py:140`, `spx_edge.py:200`, and
`weather_edge.py:255`. Three families of this bug have now been found: futures (C10),
games (C10b), and prediction (C10c).

**No live impact today** -- Gate 4.7 (`ALLOW_PREDICTION_BETS=false`, R25) rejects every
prediction category before the composite matters, so it is latent rather than active.

Deliberately **not** fixed here: seven modules, zero settled prediction bets to replay
against, and the prediction models are already flagged as surfacing garbage fair values
(R25, F34-F39). Loosening their gate before the model rebuild would be fixing the wrong
layer first. Logged as **C10c** in ROADMAP Priority 2, to be done as part of the
prediction rebuild (R25b/R25c) and replayed against evidence the way C10 and C10b each
were. If `ALLOW_PREDICTION_BETS` is ever flipped before that, this becomes active and
must be fixed first.

### Propagation

`docs/ROADMAP.md` (C10b in the Priority 0 dry-run blockquote; new **PM2d** dashboard row;
**A10**/**A11** under Web App Evolution; **C10c** in Priority 2; a 2026-07-31 Completed
entry), `CLAUDE.md` (C10b note, dashboard row, views list, test count),
`docs/polymarket/README.md`, `docs/polymarket/polymarket-games-betting/GAMES_GUIDE.md`
(new "Composite scoring" section with the full formula),
`docs/setup/polymarket-us-setup.md`, `docs/setup/ARCHITECTURE.md`, `README.md`,
`skills/edge-radar/SKILL.md` (5 pages, not 3).

One ROADMAP nuance worth recording: **PM2d supersedes Q1** (2026-04-22), which *removed*
a Polymarket market type from the webapp. That removal was correct at the time -- it was a
UI-only stub that never reached the service layer. This one does.

---

## 2026-07-31 -- Streamlit dashboard: Polymarket venue, Config page, env-registry fix

The dashboard had drifted well behind the CLI. It exposed three market types while
`scan.py` had four, its risk-gate help text still described gate values from April, and
its Streamlit-secrets bootstrap listed ~20 fewer knobs than `app/config.py` reads. This
brings it level and adds the Polymarket venue.

### The env-var registry was the real bug

`webapp/services.py` carried a hand-maintained `_flat_keys` list naming which flat TOML
keys to lift from `st.secrets` into `os.environ`. It has to exist -- the lift must happen
*before* any script import caches config, so it cannot introspect `app.config` -- but it
was last extended in April. Everything added since was absent: the R28 NO-side globals,
both L1 live-bet gates, `MIN_CONSENSUS_BOOKS_NBA`, `CALIBRATION_STDEVS_TTL_DAYS`,
`CROSS_CATEGORY_DEDUP` (global and per-sport), both cache groups (R24b/R26), and every
Polymarket credential.

The failure mode is silent and specific to Cloud: set one of those in **Settings ->
Secrets** and nothing reads it, with no error -- the app runs on the code default while
the secret sits there looking authoritative. Local `.env` deployments were unaffected
(`python-dotenv` loads the file wholesale), which is why it went unnoticed.

Replaced with `ENV_VAR_SPEC`, one registry serving three consumers: the secrets bootstrap,
the new Config page, and anyone reading the file. `tests/test_webapp_env_registry.py`
parses `app/config.py` for every `_bool`/`_float`/`_int`/`_str`/`_list` name plus the
f-string per-sport expansions and fails if the two diverge in either direction. Writing
that test immediately surfaced nine more undocumented vars (`KALSHI_PROD_*`, `ALPACA_*`,
`TELEGRAM_*`, `PROJECT_ROOT`) -- the same gap the 2026-07-14 repo review flagged against
`.env.example`, which is now closed there too.

### Polymarket as a first-class venue

Market type `polymarket` routes the scan through `_route_filter` -- the CLI's own filter
router, imported rather than reimplemented, so the dashboard and `scan.py polymarket
--filter X` cannot disagree about which surfaces a filter covers -- and switches the
execution client to `PolymarketClient` via the `get_market_client` factory.

Three venue asymmetries needed explicit handling rather than reuse:

- **Two-flag dry run.** Orders require BOTH `DRY_RUN=false` and `POLYMARKET_DRY_RUN=false`.
  The banner and confirm dialog resolve the live state through the same logic as
  `polymarket_futures_edge._order_mode` instead of assuming `DRY_RUN` alone, so a
  Polymarket-armed account cannot show a "DRY RUN" dialog.
- **Only futures are orderable.** Gamma-sourced game rows carry no US `market_slug`. They
  now show `Exec = -` in the results table, are excluded before `execute_pipeline`
  (matching the CLI), and the confirm dialog counts only orderable rows -- selecting five
  game rows previously would have said "up to 5" and sent zero.
- **Different position shape.** Polymarket money fields are Amount objects
  (`{"value": "4.98", "currency": "USD"}`) and `market_exposure_dollars` is cost basis,
  not market value. Run through the Kalshi formatter this printed `$0.00` unrealized on
  every row; a separate formatter reads `cashValue` for mark-to-market and reconciles to
  the Portfolio Value tile. Portfolio is now Kalshi/Polymarket tabs -- but the daily-loss
  bar is deliberately shared and labelled as such, because Gate 1 reads the common trade
  log.

### Config page

New read-only page: execution mode per venue, then every variable with its live value,
its source (`set` / `default` / `unset`), group, and rationale. Credentials render as a
character count only. Exports a `.env` template with live values and secrets blanked.

This is the direct answer to "is the app actually running my config?" -- previously
unanswerable from the UI, and genuinely ambiguous because `kalshi_executor` snapshots
gates at import time.

### Smaller corrections

- **Gate column added** to scan results. The Min Edge help text had promised "Each scan
  row's Gate column previews which gate will reject it" since April; there was no such
  column. It now runs the same `preflight_gate_status` the CLI preview uses.
- **Help text resynced** -- it still cited a `$0.06` price floor (live value `0.10`) and
  omitted gates 4.6b, 4.8, and the C10/C11b changes.
- **Budget % is no longer sports-only.** The cap is venue- and type-neutral and the
  schedulers pass `--budget` on futures and Polymarket runs, so hiding the control made
  a dashboard futures run the one path with no batch cap at all.
- Settle page states Kalshi-only scope (PM3 pending) and shows a Venue column.
- `DEFAULT_UNIT_SIZE`, Max Bets, and Exclude Open defaults matched to the live `.env`.

Docs: `docs/web-app/LOCAL.md` (Polymarket mode, Config page, per-venue Portfolio, new
columns), `docs/web-app/CLOUD.md` (secrets template rebuilt -- it was missing every knob
added since April, plus the `[polymarket]` block), `.env.example` (the nine undocumented
vars). 673 tests pass.

---

## 2026-07-27 -- Working branch moved from `mike_win-desktop` to `mike_desktop`

> **Completed 2026-07-31:** two stragglers this entry missed -- the `CLAUDE.md`
> session-startup checklist and the `docs/task-schedules/README.md` account-graph note both
> still named the retired branch.

Every other repo under `Repos/Live_Apps` (Agent-Chat, edge-spectrum, my-prompt-library,
taskhub) uses `mike_desktop` as the working branch. Edge-Radar was the lone exception on
`mike_win-desktop`. It is now aligned.

The switch was clean, not a migration: `mike_win-desktop` had **0 commits** not already in
`origin/master` (PR #243 merged the last of them), and the operator deleted and re-created
`origin/mike_desktop` from `master`, so `origin/mike_desktop == origin/master == c23b3c7`.
The only working-tree change -- the weekly account-graph HTML refresh -- was already
byte-identical to the copy on `master`, so nothing had to be carried across.

Local state after the move: `mike_desktop` checked out and tracking `origin/mike_desktop`;
local `master` fast-forwarded to `origin/master`. The `git sync-master` alias
(`git fetch origin && git branch -f master origin/master`) is unaffected -- it only ever
touched `master`.

Docs updated: the `CLAUDE.md` session-startup checklist (now carries an explicit **working
branch: `mike_desktop`, deploy branch: `master`** callout, matching the sibling repos),
`docs/task-schedules/README.md` (account-graph `gh`-push rationale), and
`docs/my-documents/account-graph/README.md`. Historical references in this changelog, in
`docs/my-documents/repo-reviews/2026-07-14-repo-review.md`, and in
`docs/my-documents/temp/archive/streamlit_deployment.md` were **left as-is** -- they record
what the branch was at the time and rewriting them would falsify the record.

Nothing in code, tests, schedulers, `Makefile`, or `.github/workflows/` referenced the branch
name (`deploy.yml` watches `master` only), so no automation changed. `origin/mike_win-desktop`
still exists as a safety net and can be deleted once the new setup has been exercised.

---

## 2026-07-27 -- C11b: correlation guard measured and dropped; budget cap made floor-aware

### The correlation guard does not survive measurement

C11 left "add a correlation guard for same-night/same-league/same-direction slates" as the
open follow-up. Measuring it first killed the premise.

The naive read is convincing: pairwise concordance within clusters is 0.591 against 0.501
expected, **rho +0.181, permutation p = 0.0018**. That is Simpson's paradox. Clusters live
inside strata with very different base rates -- totals win 82% of the time, spreads 24% --
and pooling unequal-mean groups manufactures apparent within-group concordance.

Judging each cluster against its own (series, type, side) base rate, with a permutation test
that shuffles *within* stratum:

| slice   | clusters | bets | pooled rho | stratified rho | perm p |
|:--------|:---------|:-----|:-----------|:---------------|:-------|
| ALL     | 80       | 243  | +0.181     | **+0.048**     | 0.036  |
| totals  | 11       | 28   | -0.010     | **-0.187**     | 0.75   |
| spreads | 18       | 42   | -0.067     | -0.111         | 0.69   |
| game    | 12       | 35   | +0.054     | +0.027         | 0.26   |

Totals -- the four-MLB-unders case that motivated the idea -- show nothing. Even at the
aggregate +0.048, four bets behave like ~3.8 independent ones, which no sizing mechanism
needs to model. **No guard was built.** Added `scripts/backtest/correlation_check.py`, which
reports both figures side by side so the artifact stays visible; re-run as settlements
accumulate, since 28 clustered totals bets cannot detect a small rho.

### Correction to C11

The "32% of bankroll" figure used to justify `KELLY_FRACTION=0.5` was computed from
`size_order` in isolation and ignored `--budget`, which every scheduler passes (12% sports,
10% futures/Polymarket) and which proportionally scales the entire batch. Real blast radius
was already bounded at ~$11.03. The 0.5 value stands on its own merits -- full portfolio
Kelly is too aggressive -- but not for the reason originally given.

### Regression found and fixed

Because the budget is a **fixed pool**, C11's correctly-sized favorites crowd everything
else out. On the 07-27 slate the 18c MLS leg fell from 6 contracts ($1.08) to 2 ($0.36) --
about a third of its intended size -- which would have quietly starved the
`MIN_MARKET_PRICE=0.10` longshot experiment rather than testing it.

`_apply_budget_cap` now:

- **never shaves an order below its flat unit floor** `round(unit_size / price)`. That floor
  encodes "if we are betting this at all, bet at least `unit_size`"; the proportional pass
  was silently overriding it.
- **bisects for the largest feasible scale** instead of taking a single proportional pass,
  so it packs the budget properly ($10.89 of $11.03 on the 07-27 slate, vs $9.36 before).
- **drops whole orders -- lowest composite first -- only when the floors alone cannot fit.**
  An earlier draft clamped first and dropped on any overage, which deleted a whole position
  to reclaim $0.23. Shaving legs that still sit above their floor always comes first.
- never scales an order *up*: the floor is clamped to the order's own count, which the
  `MAX_BET_SIZE` / bankroll caps may already have pushed below `unit_size_contracts`.

`unit_size=None` restores the pre-C11b pure-proportional behaviour.

### Scheduler override

The `.bat` files passed `--unit-size .5` explicitly, which **overrode the `.env`
`UNIT_SIZE=1.00`** set in C11 for every automated run -- so the longshot protection never
reached automation at all. All 16 now pass `--unit-size 1`. (These live under
`scripts/schedulers/`, which is gitignored by design.)

Net effect on the 07-27 slate: longshot leg back to **6 contracts**, batch $10.89 of the
$11.03 budget, nothing dropped.

### Tests

New `TestBudgetCapUnitFloor` (8 cases): under-budget passthrough, floor honored under
pressure, the pre-C11b behaviour still reproducible via `unit_size=None`, drop-lowest-
composite when floors do not fit, never-scale-up, single-order honors budget over floor,
always-within-budget across five budget levels, empty input. Full suite **667 passed**.

### Docs propagated

Swept the repo for both the old and new forms of every touched value/flag, then updated:

- **`.env.example`** -- `KELLY_FRACTION` and `UNIT_SIZE` rationale blocks: which knob moves
  which lane, the portfolio-fraction caveat, the `f* = edge / (1 - price)` formula, and a
  warning that scheduler `.bat` files pass `--unit-size` explicitly so CLI beats `.env`.
- **`CLAUDE.md`** -- C11 + C11b notes, live-`.env` block, `--unit-size` example, test count.
- **`docs/ROADMAP.md`** -- C11 + C11b as shipped rows in Priority 2, new Completed index
  entry, `Last updated` bumped to 2026-07-27.
- **`docs/setup/ARCHITECTURE.md`** -- budget-cap section rewritten for the floor-aware /
  bisecting / drop-only-when-floors-do-not-fit behaviour.
- **`docs/scripts/SCRIPTS_REFERENCE.md`** -- registered `backtest/correlation_check.py` with
  usage, flags, and a callout to read the stratified rho rather than the pooled one.
- **`docs/scripts/per-script/kalshi_executor.md`** -- sizing formula corrected to include
  `/ (1 - market_price)`, plus the which-knob-moves-what and portfolio-fraction notes.
- **`docs/task-schedules/README.md`** -- documented scheduler flags now `--unit-size 1`.
- **`skills/edge-radar/SKILL.md`** -- sizing formula, budget-cap description (both the flag
  table and the risk-limits section), live `KELLY_FRACTION`/`UNIT_SIZE`/`MAX_BET_SIZE`
  values, `--unit-size` examples, test count.
- **`skills/edge-radar-analysis/SKILL.md`** -- `correlation_check.py` added to Related with
  the Simpson's-paradox caveat and a re-run trigger.
- **`webapp/views/scan_page.py`** -- `DEFAULT_UNIT_SIZE` 0.50 -> 1.00 to match live config.
- **`.claude/html/index.html`** -- "1/4-Kelly" -> "fractional Kelly" (live value is 0.5).
- **Memory** -- new `project-scheduler-flags-override-env` (CLI flags beat `.env`; simulate
  the full `size_order` -> ratio cap -> budget cap chain), and
  `project-longshot-kelly-experiment` rewritten now that `KELLY_FRACTION` is no longer part
  of that experiment.

Historical references to the old values in `docs/CHANGELOG.md` and the ROADMAP's Findings /
Completed sections were left intact as record.

---

## 2026-07-27 -- C11: Kelly was missing the (1 - price) divisor

### The bug

`size_order()` in `scripts/kalshi/kalshi_executor.py` sized off `kelly_fraction * edge *
bankroll`. Kelly for a binary contract is `f* = (q - p) / (1 - p)` = `edge / (1 - price)`;
the `/ (1 - price)` term was absent. That is the even-money (`b=1`) approximation -- exact
only at 50c, and increasingly wrong toward either extreme.

Favorites were under-sized by `1/(1-p)`: **2.5x at 60c, 5.0x at 80c, 5.9x at 83c**. Because
the flat `UNIT_SIZE` floor then won at high prices, nearly every bet above ~60c collapsed to
a single contract. Mean contracts by entry price: sub-40c **5.56**, 40-60c **1.83**, 60c+
**1.17**.

### Why it mattered

The starved segment is the best-calibrated one in the book. Over 367 settled trades,
realized win rate *over break-even*:

| band   | n   | avg px | model fair | real WR | break-even | WR - BE | overclaim |
|:-------|:----|:-------|:-----------|:--------|:-----------|:--------|:----------|
| <40c   | 149 | 0.211  | 0.410      | 0.255   | 0.221      | +0.034  | **+0.155** |
| 40-60c | 166 | 0.494  | 0.628      | 0.542   | 0.504      | +0.039  | +0.086    |
| >=60c  | 52  | 0.726  | 0.817      | 0.846   | 0.736      | **+0.111** | -0.029 |

60c+ is 44/52 against a 73.6% break-even -- one-sided binomial **p=0.044**, the only price
band distinguishable from noise. Model calibration inverts with price: a 15.5-point
overclaim below 40c versus *conservative* by 2.9 points at 60c+. Last 30 days: 60c+
**+4.7% ROI** vs sub-60c **-48.3%**. Re-sized over the settled history, the 60c+ segment
goes **+$10.02 -> +$47.52 at the same ROI**.

### Shipped

- `kalshi_executor.py` -- divide the Kelly bet by `max(0.01, 1 - market_price)`. Single
  sizing site; Polymarket shares it via `size_order`.
- `.env` `KELLY_FRACTION` **1 -> 0.5**. The executor divides this by `batch_size`, which
  doubles as a crude correlation guard -- so it is a *portfolio* Kelly fraction. At 1.0 a
  fully correlated slate reaches full Kelly: the 07-27 slate of four MLB unders would have
  been $29.43, **32% of bankroll and ~98% of `MAX_DAILY_LOSS` in one evening**. At 0.5 the
  same slate is $16.35 (17.8%), verified live.
- `.env` `UNIT_SIZE` **.50 -> 1.00**. Longshots bind on the flat floor, not Kelly, so
  lowering `KELLY_FRACTION` alone would have cut sub-30c sizing **39%** ($6.15 -> $3.76).
  This holds the lane at its prior size ($6.15 -> $7.10). **`UNIT_SIZE` is the longshot
  knob; `KELLY_FRACTION` is the favorites knob** -- they bind at different prices and are
  independently tunable. `KELLY_FRACTION=1` was set on 07-22 to size longshots up, which
  was the wrong knob.
- `.env` `MAX_BET_SIZE` **15 -> 8**, backstop only. Nothing recent reaches it (largest
  projected position 5.6% of bankroll), but at ~$92 bankroll $15 is 16.3% on one position,
  breaching the CLAUDE.md 10% hard stop -- a cap that was unreachable while Kelly was broken.
- `MIN_MARKET_PRICE` (Gate 3.5) untouched -- a reject threshold, independent of sizing. The
  07-22 longshot experiment continues unaffected.

### Tests

New `TestKellyPriceComplement` (7 cases): dollars-at-risk scale as `1/(1-p)`, 50c reference
point, favorites no longer collapse to the flat unit, longshots barely move, no divide-by-
zero at 99c, and R1/R28 NO-side damping still composes. Full suite **659 passed**.

Also added a shared `sizing_defaults` fixture and applied it to the five gate-test classes
that assert a bare `"APPROVED"`. Those read `MAX_BET_SIZE`/`KELLY_FRACTION` from the live
`.env` at import time, so lowering `MAX_BET_SIZE` flipped twelve unrelated gate tests to
`APPROVED_CAPPED_MAX_BET`. Same class of breakage hit the venue-min-shares tests on 07-22.

### Still open

A real correlation guard for same-night / same-league / same-threshold slates. Dividing by
`batch_size` is only a proxy -- it assumes every leg in a batch is perfectly correlated,
which over-damps independent slates and under-damps ones like tonight's four MLB unders.

---

## 2026-07-25 -- Polymarket task audit: portfolio value was always $0.00

### Audit result

Reviewed the 07-24 and 07-25 `Daily-Polymarket-Execution` runs and their paired emails.
**Both tasks ran clean, exit 0, zero orders placed.** Every executable row died at Gate 3
(edge < 3%): 07-24 rejected `PM-tec-nhl-champ-...-was` (1.3%) and `...-nj` (1.1%); 07-25
rejected the same Capitals row. The paired emails sent successfully both days.

Two structural observations from the run logs:

- **The C10 composite fix is still unexercised.** Making Gate 4 reachable changed nothing,
  because nothing survives Gate 3 to reach it. Consistent with what C10 predicted, but it
  means the fix has no live validation yet.
- **The executable funnel is collapsing: 4 -> 2 -> 1** across 07-23/24/25. Today the whole
  venue produced one orderable candidate -- a $0.04 NHL futures longshot that would also
  fail Gate 3.5 (`MIN_MARKET_PRICE=0.10`) even if its edge tripled. Until the seasonal US
  games repoint lands, this task realistically cannot fill an order; 39 of today's 40 rows
  were Gamma-sourced games, auto-excluded from execution.

### Bug: Polymarket portfolio value always reported $0.00

`polymarket_exec_client.py:167` summed `p["currentValue"]`, but the US Portfolio API names
the mark-to-market field **`cashValue`**. The key is simply absent, so the best-effort
`except` never fired and the sum silently returned zero against real open exposure. Live
account: **$0.00 -> $11.03**. Fixed, `currentValue` kept as a fallback, regression tests
added for both paths.

### Polymarket zero-fill claim corrected

`CLAUDE.md` claimed "No Polymarket order has filled yet." The account holds **two open
positions** in `tec-mlb-champ-2026-09-27` (MIL 59 sh, NYY 36 sh, ~$9.88 cost, $10.99
value). They are **not system trades** -- `kalshi_trades.json` has 0 Polymarket-tagged rows
out of 90, and both carry `updateTime: 2026-07-06` -- they were hand-placed in the iOS app.
But they *are* visible to the risk gates: they are the `Positions: 2/50` line in the scan
banner and they occupy Gate 5 / Gate 6 slots for those two markets. Claim rescoped to
Edge-Radar-placed orders, with the hand-placed pair documented.

### `Email-Polymarket-DryRun` renamed to `Email-Polymarket-Execution`

The scan stopped being a dry run on 2026-07-23, but the email still announced itself as a
"Daily Polymarket Dry-Run Report" while the paired task placed live orders. The 07-23
rename deferred this as cosmetic; it wasn't -- **the prompt never asked whether an order
had been placed**, so the one fact that matters most on an execute-enabled venue was the
one the email was never required to report. The prompt now mandates an **Execution
Outcome** section led by whether an order filled (ticker/side/qty/cost when it did).

Two further prompt guards: the agent is told not to call the run a dry run, and told that
the Summary table's `total` row is a **bet-type count** (over/under), not a sum -- it had
reported that as an "internal inconsistency" in the 07-24 and 07-25 emails, which was a
misread of `report_writer.py:78` (categories sorted by count, so `total` lands first).

Task re-registered preserving the daily 10:00 AM trigger, principal and settings; old task
unregistered and `Polymarket-DryRun-Report.sh` deleted, so exactly one task and one script
remain. Log paths keep their `dryrun` filenames on purpose -- append-only history from the
dry-run window, and the scan `.bat` still writes to them.

### Test suite: `TestVenueMinShares` un-coupled from live `.env`

Two cases had been failing since 2026-07-22 (`assert 4 == 2` on `contracts`). They pass
`unit_size=1.00` but never pinned `KELLY_FRACTION`, which is a `kalshi_executor` module
global sourced from the operator's `.env` -- when it went `0.25 -> 1`, Kelly started
clearing the flat unit floor those cases assume. Pinned to the code default via an autouse
fixture; the class tests venue min-share bumps, not Kelly sizing. **Full suite: 653 passed.**

> **Wider risk:** `kalshi_executor` snapshots every gate threshold into module globals at
> import, so any test calling `size_order` without pinning them inherits operator config.
> Nothing else fails today, but the longshot experiment is open -- if `MIN_MARKET_PRICE` or
> the Kelly fraction moves again and tests break in a way that looks unrelated, start here.

### Note: live automation is intentionally untracked

`scripts/custom/` and `scripts/schedulers/*` are gitignored **by design** -- they are the
operator's personal files and stay out of the repo (operator-confirmed 2026-07-25). So the
header-comment corrections made today to `daily_polymarket_scan.bat` and the new
`Polymarket-Execution-Report.sh` are local-only and by design absent from these commits.
**Do not propose tracking them.** When editing task wiring, expect the change to live on
this machine only, and record the *behaviour* here in docs rather than the script itself.

---

## 2026-07-23 -- Wager-quality audit: config intent recorded, skills resynced

### Audit result

Reviewed every wager placed since 2026-07-20 (15 trades) and the last four days of
scheduled runs. **No misconfigured or erroneous wagers.** All 12 daily tasks exited 0;
`doctor.py` clean. Every trade carried `risk_approval: APPROVED`, `fill_status: filled`,
and a correct venue tag, and each mapped to the right scheduled task by timestamp. All
8 NO-side bets cleared the R28 8% global floor (0.081-0.149); all composites >= 6.0; no
prediction-category or in-progress-game leakage. Settled P&L since 07-15: 10W-4L,
$10.96 staked, **+$3.71 / +33.9% ROI**.

### Config intent recorded

Two `.env` changes made 2026-07-22 read as drift because the surrounding comments still
described the prior values. Both are deliberate; documented as such in `.env`, `CLAUDE.md`,
and the `/edge-radar` skill:

- **`KELLY_FRACTION` 0.25 -> 1**, to size longshots up. Worth stating precisely, because
  the name misleads: `kalshi_executor.py:785` divides it by
  `batch_size = min(len(opportunities), --max-bets)`, and every scheduler passes
  `--max-bets 5`, so the effective multiplier is **0.20 Kelly**, not 1.0 (previously 0.05).
  The practical effect is that low-priced legs now size off Kelly instead of falling back
  to the `UNIT_SIZE` flat floor -- 11c spread legs at 6-11 contracts where they were 4.
- **`MIN_MARKET_PRICE` 0.12 -> 0.10**, deliberately re-opening the longshot lane that R7
  closed on 2026-07-14.

**The longshot evidence is weaker than the headline suggests.** Sub-15c is 6W-47L over 53
settled bets at +47.5% ROI -- but **99% of that P&L is one trade**
(`KXMLSSPREAD-26MAY16SEALAG-LAG1`, +$20.59). Ex that bet the lane is roughly breakeven,
and it is -100% in June / -33% in July. Separately, the 15-25c bucket is the *worst* on the
board at -19.2%, so R7's original "lottery-ticket floor" premise is itself weakly supported.
Flagged as an open experiment in both `.env` and `CLAUDE.md`; recheck after ~30 more
sub-15c settles.

- **`--budget 12%` on all three intraday executes is intentional** (operator-confirmed).
  Stale `.bat` headers described a de-escalating 12% -> 8% -> 5% ladder that was never
  implemented and is not wanted. Headers corrected to match the flags, with an explicit
  "do not restore the ladder" note in `same_day_execute_late.bat`,
  `no_date_filter_execution_midday.bat`, and the skill.

### Polymarket status corrected

`CLAUDE.md` still claimed orders stay `dry_run_blocked` while the venue accumulated
dry-run evidence. Both `DRY_RUN` and `POLYMARKET_DRY_RUN` have been false since
2026-07-23 and `Daily-Polymarket-Execution` passes `--execute`, so **the venue is live**.
Nothing has filled -- every candidate is still stopped at Gate 3 (observed edges 1.1-2.6%
vs the 3% floor) -- and `--max-bets 2 --budget 10%` bounds exposure, but the doc read as
though a safety flag was engaged that isn't.

### Skills resynced (91 commits of drift)

`/edge-radar` and `/edge-radar-analysis` were last touched at `9b2cff1` (L1 Phase 1).
Everything since was invisible to them, most importantly **the entire Polymarket venue**:
no `polymarket` market type, no `poly`/`pm` aliases, none of the 11 filter values. Also
added or corrected:

- Five undocumented risk-gate changes -- R28 (4.6b), L1 (4.8) and its staleness knobs,
  R29, C4, C10, C8. Gate count 13 -> 15, plus the R18 Gate-column legend.
- `MIN_MARKET_PRICE` was documented as **$0.06**, its April value, two moves stale.
- A warning that the live `.env` overrides many shipped defaults (`MAX_DAILY_LOSS` is $30,
  not $250), pointing at `make doctor` for ground truth.
- Live registered task schedule replacing the stale installer-profile table; MLB
  spread/total; tennis/Wimbledon/World Cup filters; v1->v2 order-endpoint migration; M2
  trade-log lock; `scripts/schedulers/*` being gitignored.
- Test count 347 -> 651; Makefile 18 -> 22 targets.
- `/edge-radar-analysis`: settler is **hourly at :35** (U1) plus the 11 PM backstop, not
  nightly-only -- worst-case staleness ~1h, not ~24h. Pre-R5 legacy-schema orphans
  178 -> 190 of 354. Scope note that settlements carry no `venue` field and Polymarket has
  never filled, so the report is Kalshi-only. New rule: report any slice under ~50 bets
  with *and without* its top winner.

### Open items (not fixed -- no code changed this session)

- **Trade-log orphans.** Six `status: "error"` World Cup records from the 2026-06-20 v1->v2
  410 outage (four were successfully re-placed 06-22) and two zero-fill `resting` orders
  whose markets have since closed sit in `kalshi_trades.json` as permanently "open."
  Harmless to gating -- Gate 5 reads live Kalshi positions, which correctly showed 2/50 --
  but they inflate any log-derived exposure count and pollute backtests.
- **The pytest suite writes into production `logs/`.** All 64 lines of
  `kalshi_executor_2026-07-23.log` are test fixtures (`KXMLB-TEST`, "Kalshi API 500: API
  down"); the day's real runs logged nothing there. A genuine executor failure would be
  indistinguishable from this noise.
- **`R8-Review` and `U2-Review` have never run and never will** -- one-shot triggers with
  start boundaries in the past (2026-05-29, 2026-05-14), no repetition, blank NextRun.
  That is the cross-category and 2-week calibration feedback loop, dead since install.

Docs only; no behavior change.

---

## 2026-07-23 -- Futures composite unblocked (C10) + Polymarket evidence-log split

### What shipped

The Polymarket dry-run window was not converging: four days of scheduled evidence
(8 runs, 79 rows) produced **zero** gate-passing opportunities -- 73 rejected on
`edge`, 6 on `score`. The cause turned out not to be market conditions but **gate
arithmetic**.

The futures composite scaled edge as `min(10, edge * 20)` -- saturating at a **50%**
edge -- while the sports composite uses `min(edge / 0.01, 10)`, saturating at **10%**.
Identical weights and structure otherwise; one term **5x stricter**, with no recorded
rationale (launch-day commit `1d92f0f`, where the `* 20` appears copied from the
`liquidity` line directly above it).

Clearing `MIN_COMPOSITE_SCORE=6.0` therefore required roughly **11% edge at high
confidence / 23% medium / 34% low**, against championship-futures edges that run
**1-4%** in practice. Two consequences, both long-standing and previously unexplained:

- **0 futures bets across 85 settled Kalshi trades.**
- **Polymarket US was permanently unexecutable** -- futures are its only executable
  market type, so the PM2 "prove edge in dry-run, then flip `POLYMARKET_DRY_RUN`"
  gate could never terminate no matter how long it ran.

**Fix:** aligned both futures paths (`scripts/kalshi/futures_edge.py`,
`scripts/polymarket/polymarket_futures_edge.py`) to `min(edge / 0.01, 10)`. The bar
becomes ~2.1% / 4.4% / 6.6% at typical liquidity, so the composite gate binds in the
same region as the 3-4% `MIN_EDGE_THRESHOLD` floors instead of dominating them.

**Deliberately not a floodgate.** Replayed against the four days of live Polymarket
evidence, the new scale approves **none** of the 9 observed US candidates on its own --
each remains independently blocked by Gate 3 (edge floor), Gate 3.5 (price floor) or
Gate 4.5 (confidence). Live-verified on a real scan: NHL 4.36 -> 4.8, Spurs 3.57 -> 4.4,
all still correctly gated on `edge`.

The futures `high: 9` confidence weight was **left alone** -- C4 capped high->medium for
*sports* on the F49 evidence and explicitly scoped futures out; there is still no futures
settlement data to justify either choice.

### Also

- **Evidence-log split.** 66 of the 79 logged Polymarket rows were Gamma-sourced *games*
  carrying no US `market_slug` -- auto-excluded from execution, so the log read far busier
  than the 13-row tradable universe actually was. Runs now record `executable_count`, each
  row carries an `executable` flag, and the preview gained a `US` column (ASCII-only: the
  scan runs headless under Task Scheduler, where a cp1252 console raises
  `UnicodeEncodeError` on non-ASCII).

+6 tests (645), including cross-venue scoring parity between the Kalshi and Polymarket
futures composites.

### Polymarket documentation folder

Added `docs/polymarket/`, mirroring the `docs/kalshi/` layout, as the authoritative
record of the integration:

| File | Covers |
|:-----|:-------|
| `polymarket/README.md` | Hub -- coverage matrix (executable vs evidence-only), integration status PM0->PM3, dry-run evidence artifacts, common commands |
| `polymarket-futures-betting/FUTURES_GUIDE.md` | The only executable surface: question-grouping, whole-word matching, price reading, edge model, C10 composite |
| `polymarket-games-betting/GAMES_GUIDE.md` | Gamma per-game ML/spread/total, why it can't trade on US, the three guard rails |
| `polymarket-execution/EXECUTION_GUIDE.md` | Two-flag dry-run, pipeline flow, venue min shares, slug registry, position normalization, order mapping |
| `polymarket-api/POLYMARKET_API_REFERENCE.md` | Ed25519 scheme, endpoints, response shapes, and the three signing details that cost debugging time |

Navigation is wired both ways: `docs/README.md` gained a Polymarket section, the Kalshi
README links across to it as a sibling venue, `docs/setup/polymarket-us-setup.md` points up
into the domain folder (and is now scoped to key generation + `.env` wiring), and every new
page carries a footer nav back to its index. `CLAUDE.md`'s project tree lists the new folder.

### Scheduler changes (live money)

- **`Daily-Polymarket-DryRun` -> `Daily-Polymarket-Execution`.** The task now passes
  `--execute` with batch caps (`--max-bets 2 --budget 10%`), so the daily 9:40 AM run can
  place real unattended Polymarket wagers. Renamed because the old name asserted the
  opposite of what it does; re-registered from exported XML preserving trigger and
  principal, old task unregistered, re-validated (`LastTaskResult=0`, 4 opportunities
  risk-checked, **0 orders placed**). The evidence log still writes either way -- `--save`
  runs outside the execute branch. Only futures are orderable; Gamma games are
  auto-excluded. The paired `Email-Polymarket-DryRun` job keeps its name (it only emails
  the report).
- **`Weekly-Futures-Execution` disabled.** C10 made Kalshi futures clear Gate 4 for the
  first time, so Saturday's run would have been the first-ever live futures order through
  an unexercised path. Disabled pending a manual futures cycle in preview.

Note: the scheduler `.bat` files are gitignored (`.gitignore:87` -- they hardcode local
paths), so `docs/task-schedules/README.md` is the only tracked record of what the
automation actually runs.

### Known issue (pre-existing, unrelated)

`tests/test_risk_gates.py::TestVenueMinShares` has 2 failures that reproduce on a clean
checkout: the tests read the operator's live `.env` at import time and assume the
documented `KELLY_FRACTION=0.25` while `.env` carries `1`. Test-isolation defect, not a
sizing bug.

---

## 2026-07-21 -- Task schedules: `Email-Polymarket-DryRun` added

Daily 10:00 AM, 20 minutes after the 9:40 Polymarket dry-run scan. Emailed the day's
`reports/Polymarket/` report, or a short no-opportunities proof-of-life from
`logs/polymarket_dryrun_scan.log` on empty days. Renamed `Email-Polymarket-Execution`
2026-07-25, merged into its scan task 2026-09-23, removed with the venue 2026-09-29.

## 2026-07-20 -- MLB spreads + totals wired (KXMLBSPREAD/KXMLBTOTAL coverage gap)

### What shipped

A "not much coming through" health check found `KXMLBSPREAD` and `KXMLBTOTAL` live on
Kalshi with open markets but never scanned — MLB ran **moneyline-only all season**. The
series launched after MLB was first wired (March 2026); every other major sport already
scanned all three market types, and the R2-calibrated baseball stdevs were in place.

- Fix: three map entries in `edge_detector.py` (`FILTER_SHORTCUTS["mlb"]`, `CATEGORY_MAP`,
  `KALSHI_TO_ODDS_SPORT`). Everything downstream (spread/total detectors, stdev lookup via
  the `KXMLB` prefix, bracket dedup, series dedup, ticker display) is prefix-generic.
- Live market shapes verified: bracket-style, line in `floor_strike` (e.g.
  `KXMLBSPREAD-...-SEA9` = "Seattle wins by over 8.5 runs", `KXMLBTOTAL-...-9` =
  "Over 8.5 runs").
- First scan: MLB 106 → **407 markets** (103 spreads + 176 totals); 7 gate-`ok` rows at
  +8–12% claimed edge on the next slate — all deep-bracket **Unders** (high-line NO-side
  favorites). ⚠️ This is an **uncalibrated sub-population**: the normal-CDF total model may
  overstate Under probability against MLB's right-skewed run distribution (fat blowout
  tail; a Coors Field Under 17.5 is in the first batch). Existing guards apply (R28 NO-side
  8% floor, correlated-bracket dedup, per-event cap, $1 units). Posture: bet small via the
  normal automation and review the first settlements — the 06-29 soccer-spread precedent
  (always-YES lean proved real) cuts either way.

**+5 tests (640 total).** Health check otherwise clean: all 22 scheduled tasks exit 0,
Odds API quota 3,919 remaining, MLS/MLB data pulls verified, hourly settle running.

---

## 2026-07-20 -- PM2c: Polymarket execution pipeline wired (orders gated behind POLYMARKET_DRY_RUN)

### What shipped

Resolved **PM2c** (execution-pipeline wiring — the last code step of ROADMAP Priority 0
Phase 2). `python scripts/scan.py polymarket --execute` now routes US-slug futures
opportunities through the shared `execute_pipeline` with `venue="polymarket"` — the same
risk gates, Kelly sizing, and ratio/budget caps as Kalshi — then `create_order` on the US
API. `--unit-size / --budget / --max-bets / --min-bets / --pick / --ticker` supported.

- **Two-flag dry-run safety (new `POLYMARKET_DRY_RUN`, default true)** — Polymarket orders
  return `dry_run_blocked` unless BOTH `DRY_RUN=false` and `POLYMARKET_DRY_RUN=false`.
  Required because `.env` runs Kalshi live: without a venue-scoped flag, flipping the
  scanner's `--execute` refusal would have placed live Polymarket orders immediately,
  contradicting the "prove edge in dry-run first" phase gate.
- **Venue minimum order size** — `minimumTradeQty` captured at scan time into
  `opp.details["min_order_shares"]` + the registry; `size_order` bumps sub-minimum counts
  up (post-caps) or rejects (`below_venue_min_shares`) when the bump would breach
  `MAX_BET_SIZE`/bankroll; the pipeline drops rows the ratio/budget caps push back under.
- **Positions normalized** — `PolymarketClient.get_positions` also emits Kalshi-shaped
  `market_positions` with `PM-{marketSlug}` tickers (the scanner's own convention), so
  Gate 5, per-event counts, and `status --venue polymarket` work unchanged.
- **Venue-tagged trade log** — records carry `venue`; `orderId` (US camelCase) accepted.
  Gate 1 (daily loss) spans venues by design. Batch placement now survives non-Kalshi
  exceptions (one failed order can't abort the batch); the Kalshi resting-order janitor is
  skipped for non-Kalshi venues; Gamma games opps (no US slug) are excluded from execution.

Live-verified end-to-end in preview mode: $60.12 balance, 2 US positions counted through
the normalized shape, four championships priced, the one live edge (Spurs) correctly
gate-rejected on composite score, client initialized `dry_run=True` despite global
`DRY_RUN=false`. **+15 tests (635 total).** Remaining: prove edge in the daily dry-run
window → deliberately flip `POLYMARKET_DRY_RUN`; seasonal games repoint; PM3 settlement/ops.

---

## 2026-07-20 -- Polymarket US repoint: execution rebuilt (Ed25519) + futures scanner on US data

### What shipped

Resolved **PM2c-0**. The operator's funded account is the **CFTC-regulated Polymarket US**
product (iOS-app only), which uses an **Ed25519 retail API** (`api.polymarket.us`) — not the
international EIP-712 / `py-clob-client` scheme the earlier PM2b client assumed. (The prior
"$0 empty twin wallet" diagnosis was wrong — it was the wrong product/API entirely, not a
per-sign-in-method Magic account.)

- **Auth + execution client rebuilt** — `PolymarketClient` on signed requests (shared
  `polymarket_us_auth` Ed25519 signer, raw `cryptography` + `requests`, no SDK); `app.config`
  creds → `POLYMARKET_KEY_ID` / `POLYMARKET_SECRET_KEY`; `market_registry` → US `market_slug`.
  Verified live ($60.12 buying power, real positions).
- **Futures scanner repointed to US market data** — new `polymarket_us_data` read client
  (paginates `GET /v1/markets`, groups championships by `question`, extracts each team's YES
  ask + US slug); prices US quotes vs the Odds-API consensus and records the real
  `marketSlug`. Verified live (Spurs NBA-champ +3.6%). World Cup dropped (over + not on US).
- **Config cleanup** — retired `POLYMARKET_PRIVATE_KEY` / `_FUNDER_ADDRESS` / `_SIGNATURE_TYPE`
  and the `py-clob-client` dependency; added `POLYMARKET_KEY_ID` / `POLYMARKET_SECRET_KEY`.
- **Inventory finding** — Polymarket US is **not** a Gamma mirror: game markets are
  moneyline-only + seasonal (no spreads/totals, no MLB per-game); futures are the deep,
  always-on surface. The games scanner still reads Gamma (dry-run only, not executable on
  US); its repoint is a deferred seasonal follow-on.

**620 tests pass.** Remaining before live orders: execution-pipeline wiring (size →
`create_order`, ~5-share minimum, flip the scanner `--execute` refusal). Full detail:
`docs/setup/polymarket-us-setup.md`.

---

## 2026-07-20 -- Session note: PM2b live verification — auth works, wallet identity mismatch found

### What happened

First live test of the PM2b `PolymarketClient` against the operator's real
account. The signing chain **works end-to-end**: exported key valid, EIP-712
signing + CLOB L2 credential derivation succeeded (`signature_type=1`;
signer EOA distinct from funder, as expected for a Magic proxy account).

But the configured account is **empty** — confirmed three independent ways
(CLOB collateral read, raw on-chain USDC/USDC.e balances via Polygon RPC,
Data-API portfolio value = 0). The operator sees the funds in the phone app
while the desktop session (same email) shows $0: Polymarket/Magic creates a
**separate wallet per sign-in method** (Google vs Apple vs typed-email magic
link), so the desktop-exported key + address belong to an empty twin
account. The public username lookup (`toastyllama6297`) dead-ends (no web
profile), so the funded address must come from the phone side.

### Status

**Blocked on operator action — logged as PM2c-0, the most urgent roadmap
item** (full fix steps in the ROADMAP Priority 0 table): re-login on desktop
with the phone's exact sign-in method, re-export key + address from that
session, update `.env`, re-run the read-only verification.

---

## 2026-07-20 -- Session: PM2b — PolymarketClient write half (py-clob-client)

### Why

The wallet question resolved: the operator's funded Polymarket account is an
email/Magic proxy wallet whose balance ≈ the intended bankroll, so it IS the
dedicated trading wallet (decision revised from "create a separate wallet").
That unblocked building the execution client — mock-tested now, live smoke
test once the exported key lands in `.env`.

### What landed

- **`polymarket_exec_client.PolymarketClient`** — implements the
  `MarketClient` contract via `py-clob-client` (new dep): EIP-712
  wallet-signed CLOB orders (`signature_type=1` proxy accounts), balance via
  CLOB collateral (+ Data-API position value), positions via the public Data
  API, orders/cancel/fills via CLOB. `get_settlements` returns empty until
  PM3. Lazy CLOB construction — init is network-free, and DRY_RUN order
  paths (blocked with `status="dry_run_blocked"`, exactly like KalshiClient)
  never touch the network.
- **`market_registry`** — the `MarketClient` contract speaks Kalshi-shaped
  tickers but the CLOB needs token ids; scanners now record
  ticker → {condition_id, clob_token_ids} at scan time (7-day expiry,
  atomic write), and `create_order` resolves through it (side→token is
  structural: yes=0/no=1; NO price is used directly — no 1-minus, unlike
  Kalshi's single-book API). A registry miss refuses the order.
- **Factory flip:** `get_market_client("polymarket")` now returns the real
  client; without credentials it raises the same style of setup-guidance
  error as KalshiClient (no more blanket Phase-2 refusal).
- **Config:** `PolymarketCredentials` in `app.config`
  (`POLYMARKET_PRIVATE_KEY` / `POLYMARKET_FUNDER_ADDRESS` /
  `POLYMARKET_SIGNATURE_TYPE`, default 1) + documented `.env.example` block
  with the full-account-access warning.
- **Known venue constraint:** ~5-share minimum order on most markets — at
  $1 units a 50¢ contract sizes below it. Logged as a warning; PM2c wiring
  must bump to the minimum or skip.
- **Test hygiene fix:** the scan orchestration tests were writing fixture
  entries into the real `market_registry.json`; registry path now
  monkeypatched in every scan-invoking test, polluted file purged and
  repopulated clean from a live scan (13 real entries).
- **Tests:** +18 (605 total) — registry roundtrip/prune, conformance
  signature coverage, creds guidance, network-free construction, dry-run
  block, yes/no token+price resolution, registry-miss refusal, factory.

### Remaining (PM2c)

- Live auth smoke test (blocked on the operator exporting the key to
  `.env`), execution-pipeline wiring (gates → sized orders →
  `create_order`, min-share handling, flip the scanner `--execute`
  refusal), then first live orders after the edge window proves out.

---

## 2026-07-20 -- Session: PM1d — Polymarket per-game edge detection (ML/spread/total)

### Why

The operator asked whether Polymarket carries individual game markets. The
07-14 spike said no ("0 MLB game markets") — that finding was **wrong**. Game
events exist for every MLB/NFL/NBA/NHL game (moneyline + run-line spread +
game total, tight 1–4¢ books) but are invisible to title search and default
listing order; they surface only via tag_id + open filtering — the same
discovery failure mode as the PM1b futures slugs. Game lines are the bigger
prize: ~15 MLB games/day vs 4 slow futures boards, and games **settle daily**,
so the PM2 edge-proving window can validate against real settlements in weeks
instead of waiting for October futures resolution.

### What landed

- **`polymarket_games_edge.py`** — prices every open pre-game Polymarket
  ML/spread/total against the SAME calibrated consensus model as Kalshi
  sports: `consensus_fair_value` / `consensus_spread_prob` /
  `consensus_total_prob` reused unchanged (de-vig, sharp-book weighted
  median, sport-specific stdevs incl. C8 calibrated overrides; a synthetic
  `KX<sport>` stdev-routing ticker feeds the prefix lookup). ML and totals
  priced on both sides (second outcome's effective ask = 1 − best bid);
  spreads YES-only. Category = game/spread/total, so the existing risk gates
  compose naturally (verified: ~5% Under edges correctly held by the R28
  NO-side 8% floor).
- **Client additions** — `get_tag_id(slug)` (cached), `fetch_game_events`
  (tag_id + open, paginated), `iter_game_rows` (normalizes via Gamma's
  `sportsMarketType`; skips exotic NRFI/first-five/props — dead 2¢/98¢
  books — and closed/degenerate rows).
- **Guard rails:** pre-game only (mirrors Gate 4.8's default); 10¢
  `MAX_BOOK_SPREAD` book-quality floor; and **start-time matching (±6h)**
  between the PM game and the Odds API event — team matching alone priced
  later series games against the wrong game's odds (caught live: 3 phantom
  Twins/Rangers ML edges from July 22–23 games priced with July 21 odds; the
  2026-06-03 Kalshi bug class). Doubleheaders that stay ambiguous are
  refused.
- **CLI routing:** `--filter` now takes `all` (futures+games, new default) |
  `futures` | `worldcup|nfl|mlb|nba|nhl` | `games` | `<sport>-games`.
  Games import lazily so futures-only scans skip the edge_detector stack.
- **Scheduled task widened** (`Daily-Polymarket-DryRun`): now
  `--filter all --min-edge 0.01 --top 40` so the evidence log records the
  full funnel including near-misses (17 rows on first run vs 3 at the old
  floor) — the gates still enforce real floors at execution. Re-validated
  (`LastTaskResult=0`).
- **Verified live:** 55 MLB games priced 1:1 against consensus; 2 genuine
  edges (Under 12.5 totals, +4.3%/+5.0%, gate=edge per R28); 1 NFL preseason
  game; NBA/NHL offseason gracefully empty.
- **Tests:** +9 (`test_polymarket_games.py` — row normalization, both-sides
  ML, spread strike negation, total over/under, filter routing, started-game
  skip, and a regression test for the series-date mismatch). 587 total.

---

## 2026-07-20 -- Session: U1 hourly settle + R10/C6 measurement (no tuning)

### Why

Priority 2 head items while the Polymarket dry-run window accumulates: U1
(hourly settlement) is a standalone quick win newly enabled by M2's trade-log
lock; R10 (category-weighted composite) required a measurement pass before any
weight could be chosen.

### What landed

- **U1 — `Hourly-Settle` task (every hour at :35).** Runs
  `kalshi_settler.py settle` hourly (direct python, NightlySettle pattern).
  Enabled by M2: the cross-process lock makes a settle that overlaps an
  execute task merge-safe. Fresher settlements sharpen Gate 1 (daily-loss)
  intraday, clear positions as games end, and run R4 resting-order cleanup
  timely. `:35` is the only minute slot clear of every existing task.
  `NightlySettle` kept ~1 week as belt-and-suspenders (settle is idempotent),
  then retire. Validated on install (`LastTaskResult=0`). Task #22 in
  `docs/task-schedules/README.md`.
- **R10 — RESOLVED, no re-weighting.** The April premise (Total +32% >> ML
  +11%) inverted: 90d shows ML +19.6% (n=70) vs Total -4.4% (n=42), and every
  category flips sign between adjacent ~45d slices. The spread aggregate
  (+45.3%) decomposes into WC spreads 5-31/-60% (realized ≈ the market price
  — zero alpha on the claimed +6.6% edge, post-de-vig-fix) vs MLS spreads
  +246.8% (n=14 longshot luck); combined soccer spreads land dead on model
  fair. The dominant variation is sport×regime, not category — re-weighting
  the composite on this data would fit noise (the C4 lesson). Watch-don't-
  tune; revisit only on a stable same-signed gap across two independent ~90d
  windows at n≥100. Writeup:
  `docs/my-documents/temp/r10-category-weights/README.md` (local).
- **C6 — CLOSED with the same pass.** April's Totals +32% didn't persist
  (90d -4.4%); nothing pathological either. No action.
- **Finding for the record:** the World Cup spread cohort ran at market, not
  at model — tempers the 06-29 conclusion that WC always-YES spread edge was
  "largely real." Soft follow-up: re-check soccer-spread edge realization
  early in the next major tournament.

---

## 2026-07-20 -- Session: PM2a — venue-neutral MarketClient seam (execution plumbing)

### Why

PM2 (Polymarket execution) needs a venue-agnostic client boundary before any
wallet code exists. The executor hardcoded `KalshiClient()`; extracting the
seam now is decision-free (no real money, no wallet secrets) and shortens the
risky half later, while the PM1c dry-run evidence window accumulates.

### What landed

- **`MarketClient` Protocol** (canonical `scripts/shared/market_client.py`,
  re-exported via `app/domain/market_client.py` following the `Opportunity`
  pattern): the 7-method contract the money paths actually use —
  `get_balance_dollars`, `get_positions`, `create_order`, `get_orders`,
  `cancel_order`, `get_fills`, `get_settlements` — with the KalshiClient-set
  conventions documented (dollars not cents; legacy order shape translated
  internally; DRY_RUN honored via `status="dry_run_blocked"`).
- **`get_market_client(venue)` factory** — the single place a venue name
  becomes a client (lazy imports so a venue's dependency stack only loads
  when selected). `kalshi` resolves; `polymarket` raises a clear
  NotImplementedError until the PM2 write half ships; unknown venues raise
  ValueError.
- **Executor `--venue` plumbing** (`run` + `status`): `KalshiClient()`
  hardcode replaced with the factory; `--venue polymarket` refuses with a
  clean message (exit 2), not a traceback. Verified live: `status` runs
  through the factory against the real portfolio.
- **Tests:** +21 (`test_market_client.py` — class-level KalshiClient
  conformance incl. per-method signature coverage so drift is caught,
  runtime_checkable behavior, factory routing/refusal/validation). 578 total.
- Deliberately untouched: `webapp/services.py:161` keeps its direct
  `KalshiClient()` — its Streamlit-secrets credential handling is
  Kalshi-specific and migrates when a real second venue exists.

### Next

- PM2 write half (`PolymarketClient` via `py-clob-client`), gated on the
  dry-run edge-proving window + operator answers (wallet choice, test
  stakes, sports-only scope, arb vs independent edge).

---

## 2026-07-20 -- Session: PM1c — Polymarket dry-run evidence persistence

### Why

The Phase 1→2 gate is "prove edge in dry-run," but the Polymarket scanner
accepted `--save` and silently discarded it — no evidence could ever
accumulate to satisfy the gate.

### What landed

- **`--save` is now functional** on `polymarket_futures_edge.py` (flows through
  `scan.py polymarket ... --save` unchanged): appends one run record —
  timestamp, filter, min-edge, count, and every opportunity **with its
  preflight gate verdict** — to `data/polymarket/dryrun_log.jsonl`
  (append-only time series). Zero-opportunity runs are logged too: "how often
  does edge appear at all" is part of the evidence.
- **Markdown scan report** to the new `reports/Polymarket/` directory via
  `report_writer` (new `"polymarket"` report type, reuses the futures table
  layout). `--report-dir` override supported, matching the other scanners.
- Gate preflight refactored out of the preview (`_gate_statuses`) so the
  table and the persisted record share one computation.
- **First live record captured:** NBA Spurs at 19¢ vs 23¢ fair (+4.0%), low
  confidence, gate=`score` — correctly rejected.
- **Tests:** +3 (`TestSaveDryrun` — JSONL shape + gate field + report,
  zero-opp logging, multi-run accumulation). 557 total.

### Scheduled (same day)

- New `Daily-Polymarket-DryRun` Windows task (daily 9:40 AM PST) runs the
  `--save` scan unattended, so the PM2 evidence log builds itself. Read-only,
  no paired email (output to `logs/polymarket_dryrun_scan.log`), ~4 Odds API
  requests/run. Validated on install (`LastTaskResult=0`, record appended).
  See `docs/task-schedules/README.md` task #21.

---

## 2026-07-20 -- Session: PM1b — Polymarket futures event discovery (NFL/MLB/NBA/NHL)

### Why

Phase 1 of the Polymarket integration proved the pricing path on the World Cup
only — the keyword-search fallback couldn't locate the Super Bowl / World Series /
NBA / Stanley Cup boards, blocking year-round futures coverage (ROADMAP PM1b).

### What landed

- **Root cause:** the championship boards sit beyond the first 300 active Gamma
  events, so `find_event`'s pagination fallback never reached them (and the NFL
  board is titled "NFL Champion 2027", so "super bowl" terms couldn't match it).
- **All four slugs wired into `PM_FUTURES`:** NFL `big-game-champion-2027`,
  MLB `mlb-world-series-champion-2026`, NBA `nba-2027-champion`,
  NHL `nhl-2027-champion-20260612185656162` (verified live 2026-07-20).
- **`find_event` fallback rebuilt on Gamma `/public-search`** (new
  `search_events()`): relevance-ranked search per term, open-events-only,
  all-words-of-a-term title match (excludes e.g. Conn Smythe with "nhl champion"),
  highest-volume winner (picks "World Cup Winner" over "Golden Boot Winner"),
  then a re-fetch by slug since search results may truncate the markets list.
  Slugs rot at season rollover; the fallback re-resolves all four boards from
  dead slugs (live-proven), so next season heals without a code change.
- **End-to-end verification:** `scan.py polymarket --filter futures` prices all
  four sports vs Odds API outrights — 32/30/30/32 candidates each matched 1:1 to
  sportsbook outcomes; one edge surfaced (NBA Spurs +4.0%, low confidence →
  correctly gated on composite score). World Cup board closed at the final
  (2026-07-20) and is correctly skipped — dormant until the 2030 cycle.
- **Tests:** +4 (`TestFindEvent` — slug short-circuit, closed-filter +
  volume-preference + full re-fetch, all-words matching, empty input). 554 total.

### Next

- **PM2** — Phase 2 execution (`MarketClient` Protocol, `py-clob-client`,
  wallet secrets handling), after the dry-run edge-proving window.

---

## 2026-07-20 -- Session: MLB recheck (M1), review residuals (#3/#6), trade-log lock (M2)

### Why

Post-review follow-through. The 2026-07-14 repo review left three tracked items;
this session closed the MLB executable-bets recheck (M1), two small safety residuals,
and the cross-process trade-log lock (M2).

### What landed

- **M1 — MLB executable-bets recheck (RESOLVED, no code change).** Ran on a full
  15-game slate: MLB now surfaces **15 opportunities** (vs 0 across the prior 30-day
  window), confirming the World-Cup crowding was the cause and is structurally gone.
  All rows gate on `edge` with sub-1% edges on efficient lines (Mkt≈Fair within ~1¢) —
  NOT the 2–3%-blocked-by-floor bucket, so `MIN_EDGE_THRESHOLD_MLB` / `MIN_COMPOSITE_SCORE`
  left unchanged. Odds quota confirmed healthy (3,988 across keys; one dead 401 key noted).
- **#6 — Odds API key redaction.** A `requests` exception stringifies the full URL with
  `?apiKey=<secret>`; it was logged verbatim at three sites. New `odds_api.redact_secrets()`
  masks `apiKey=<value>` before logging (edge_detector fetch + event fetch, futures_edge). +5 tests.
- **#3 — Longshot report crash guard.** `betting_analysis._render_longshot` now None-guards
  `edge`/`fair_value` (renders `—`) like the ledger, so one incomplete settlement no longer
  raises `TypeError` and kills the whole analysis report. +3 tests (new `test_betting_analysis.py`).
- **M2 — Cross-process trade-log lock.** `_atomic_write_json` (shipped 07-14) closed the
  corruption hole but not the concurrent read-modify-write lost-update race. Added
  `trade_log_lock()` (cross-process `filelock`, graceful no-op fallback) + `append_trades()`
  (re-reads under the lock before saving → merges instead of clobbering). Executor's two
  write sites now use `append_trades`. Settler split into Phase 1 (Kalshi network I/O, no
  lock) → Phase 2 (short locked critical section that re-loads fresh, preserving any executor
  append made mid-fetch, then saves) so the lock is never held across network I/O.
  `filelock>=3.12.0` added to requirements. +7 tests incl. end-to-end concurrent-append test.
- **#7 — execute batch aborted mid-placement on network errors.** The order loop only
  caught `KalshiAPIError`; a `requests` `ConnectionError`/`Timeout` from `create_order`
  propagated uncaught, aborting the batch part-placed with no failure record. `_request`
  now translates transport errors into a typed `KalshiConnectionError` (subclass of
  `KalshiAPIError`, `status_code=0`). The loop (extracted to a testable `_place_order_batch`)
  records each failure and continues instead of aborting, flagging transport failures as
  placement-UNKNOWN for reconciliation, with a circuit-breaker after 3 *consecutive* transport
  failures (a dead network stops the batch instead of hanging every remaining order to its
  timeout). Orders are **not** retried — a retried POST could double-place. +8 tests.
- **#8 — settlement P&L double-count.** Kalshi settlements are keyed per-market, so two
  trades sharing a ticker both matched the same settlement and each claimed the whole
  position's aggregate `revenue` (double-counted P&L). `calculate_pnl` now derives revenue
  **per-trade** from that trade's own filled contracts (a winning binary contract pays
  exactly $1.00) — additive across trades and, for a single trade, identical to the aggregate.
- **#9 — inconsistent revenue normalization.** The settler's `calculate_pnl`, the settler
  report builder, and `risk_check` normalized the settlement `revenue` cents field three
  different ways (two used a `> 1` guard that mis-read 1¢ as $1.00). Consolidated into one
  shared `trade_log.settlement_revenue_dollars()` (any int is cents → /100) used by both
  report builders; `calculate_pnl` no longer reads the raw field at all (#8). +7 tests.

**550 tests passing** (was 520).

---

## 2026-07-14 -- Polymarket Phase 1: read-only championship-futures edge detection (dry-run)

### Why

Kick off the Polymarket integration (Priority 0). Phase 0 spike found the Gamma API
live and healthy, but that Polymarket's sports coverage is **futures/props/politics**,
not per-game lines (0 MLB game markets; top markets are World Cup Winner $4.2B, F1
champion, retirement props). So Phase 1 targets **championship futures**, which map to
Edge-Radar's existing `futures_edge` outright fair-value model.

### What landed

- **New `scripts/polymarket/` package (read-only):**
  - `polymarket_client.py` — Gamma API client: `find_event` (slug + keyword fallback,
    paginated), `iter_future_candidates` (normalizes an event's sub-markets, skips
    closed/eliminated candidates and degenerate 0/1 prices, reads the Yes-token
    `bestAsk`). No auth, no wallet, places no orders.
  - `polymarket_futures_edge.py` — `detect_edge_futures_polymarket` mirrors
    `futures_edge.detect_edge_futures` but reads the Polymarket candidate shape and
    **reuses `fetch_outrights` + `consensus_outright_fair_values` unchanged** for the
    sportsbook fair-value side. Emits normalized `Opportunity` (category=`futures`,
    `edge_source=polymarket_vs_outrights`, `details.venue=polymarket`). YES-side only in v1.
- **Wired into `scan.py`:** `polymarket` market type (aliases `poly`/`pm`),
  `--filter worldcup|nfl|mlb|nba|nhl`. The preview shows each opp's `preflight_gate_status`
  (routes through the existing risk gates read-only). `--execute` is **refused** — execution
  is Phase 2 (wallet / `py-clob-client`).
- **Reuses the provider-agnostic seam:** Polymarket opps flow through the same
  `Opportunity` + gate logic as Kalshi — no gate code duplicated.
- **Proven live end-to-end:** ingested the World Cup Winner event, priced against
  `soccer_fifa_world_cup_winner` outrights, matched the final-4 candidates → 0 edge (a
  correct result: efficient cross-venue pricing + tournament ending ~07-19).
- **+12 tests** (`tests/test_polymarket_futures.py`); 520 passing. `scripts/polymarket`
  added to `pyproject.toml` pytest pythonpath.

### Known follow-up (PM1b)

Event **discovery** for NFL/MLB/NBA/NHL futures needs each event's exact Gamma slug or
tag_id — the keyword-search fallback didn't locate them (World Cup works via its confirmed
slug). The pricing framework is done; only discovery config is missing. See ROADMAP PM1b.

## 2026-07-14 -- Polymarket integration scoped as top priority + roadmap relocated to docs root

### Why

Polymarket account approved + funded (US-persons ToS confirmed legitimate by operator).
Goal: place wagers on Polymarket through Edge-Radar as a second execution venue. Ran a
technical spike to scope it before building.

### What changed

- **New Priority 0 on the roadmap: Polymarket integration** (PM0–PM3), marked the
  highest-priority active build. Phased Phase 1 read-only/dry-run → prove edge → Phase 2
  execution → Phase 3 settlement.
- **Spike findings:** the retired 2026-04-27 integration (commit `4361c85`) was a
  read-only Kalshi↔Polymarket arbitrage scanner (Gamma API) — never placed a bet.
  Execution is net-new (on-chain Polygon/USDC, EIP-712 wallet-signed via `py-clob-client`,
  CLOB order book, UMA settlement). Good news: `app/domain/opportunity.py` is
  provider-agnostic and `size_order()` runs on `Opportunity`, so a normalized Polymarket
  opp reuses the existing risk gates; the execution client is a clean ~7-method interface
  hardcoded as `KalshiClient()` at `kalshi_executor.py:1592` + `webapp/services.py:161`
  (introduce a `MarketClient` abstraction + factory). Recoverable git assets:
  `polymarket_edge.py` (Gamma reads) + `.claude/skills/polymarket/references/` (~9k lines
  of CLOB/trading docs). Full plan: `docs/my-documents/temp/polymarket-integration/PLAN.md`.
- **Roadmap relocated:** `docs/enhancements/ROADMAP.md` → **`docs/ROADMAP.md`** (`git mv`,
  history preserved). Fixed all 11 inbound links (README, docs/README, ARCHITECTURE,
  SCRIPTS_REFERENCE, SETUP_GUIDE, the three kalshi guides, CLAUDE.md + ARCHITECTURE trees,
  `r8_cross_category_review.py`). Historical CHANGELOG "Files:" references left as-is.
- **CLAUDE.md** — added a "🔴 NEXT UP: Polymarket" callout and marked it in-progress in the
  Planned list.

## 2026-07-14 -- Full repo review + money-path fixes, longshot floor, config reconcile, cruft purge

### Why

Session started from "not many wagers being placed." Diagnosis (30-day settled
review) flipped the premise: volume wasn't gate-starved — it was **calendar-driven**
(World Cup ending ~07-19, MLB All-Star break, NBA/NHL offseason) and the bets that
*were* placed bled **−43% ROI (12W–30L, L9 streak)**, ~98% World Cup spread-YES
longshots. The sub-15¢ price bucket went **0W–21L, −100%**. Odds API quota was
healthy (2,465 requests). A full five-agent repo review ran alongside; findings at
`docs/my-documents/repo-reviews/2026-07-14-repo-review.md`.

### What changed

**Money-path bug fixes (all 508 tests green):**
- **Calibration-on-read** (`model_calibration.py`): `save_calibration_stdevs()` was
  called unconditionally, so a read-only report run silently mutated the per-sport
  margin/total stdevs the scanner prices against. Now gated behind `--save` (all
  scheduled calibration tasks pass `--save`, so the C8 feedback loop is unaffected).
- **Trade-log corruption** (`scripts/shared/trade_log.py`): `save_trade_log` /
  `save_settlement_log` did a plain non-atomic `open("w")`. Added
  `_atomic_write_json` (temp file + fsync + `os.replace`) so a crash/interrupt can
  no longer corrupt the ledger or lose a live position. (Residual cross-process
  read-modify-write lock left as a follow-up — see repo review.)
- **R26 replay gate bypass** (`kalshi_executor.py`): the cached-preview replay path
  set `to_execute = list(cached_rows)` and skipped straight to execution, bypassing
  gates 5/6/7. It now re-checks duplicate-ticker, per-event cap, and series-dedup
  against *current* portfolio state before executing (sizing stays locked from the
  preview). Drops are reported.

**Risk-gate config reconciled to a single source of truth** (`app/config.py`) across
`.env.example` and `CLAUDE.md`:
- `MAX_OPEN_POSITIONS` → **50** everywhere (live `.env` ran 50; docs/code default
  wrongly said 10 — reconciled *up* to match live intent per operator decision).
- `MAX_PER_EVENT` → **2** in `CLAUDE.md` (was the lone outlier at 3; code/.env were 2).

**Longshot price floor (R7 tightening):** `MIN_MARKET_PRICE` **0.06 → 0.12** in live
`.env`, `.env.example`, `app/config.py` default, and `CLAUDE.md`. 30-day data: every
sub-15¢ bet lost (0W–21L / −100%) while ≥25¢ bets were profitable. This is the direct
fix for the World Cup spread-YES longshot bleed and protects future soccer/all-sport
longshots. **Requires webapp restart / Streamlit Cloud Secrets update to take effect
in long-running apps** (CLI picks it up immediately).

**Cruft purge:** `git rm` of three verified broken+orphaned scripts —
`daily_sports_scan.py` (crashed on import: `from config import …`; superseded by
`same_day_scan.bat → scan.py`), `fetch_market_data.py`, `fetch_odds.py` (orphaned,
broken auth + Polymarket response shape). Removed 16 untracked dated
`send_daily_summary_email_2026-*.py` snapshots (canonical `send_daily_summary_email.py`
retained). Updated `docs/scripts/SCRIPTS_REFERENCE.md` to drop the three blocks.
**Deliberately NOT removed:** `.claude/backup/` — its README documents it as an
intentional holding pen keeping old HTML out of the public Pages deploy (the review
agent misread it as dead cruft).

**Tests:** updated `test_config.py` (new defaults) and `test_risk_gates.py` (two tests
using $0.10 prices now neutralize the floor via monkeypatch, since they exercise the
max-bet cap / Kelly sizing, not the R7 floor). 508 passing.

### Open follow-up

- **MLB executable-bets recheck** — MLB placed 0 bets in 30 days (crowded out by
  World Cup's inflated pre-de-vig edges for the `--max-bets` slots). Should self-correct
  now that WC is ending + de-vig shipped + longshot floor raised. Recheck plan +
  commands: `docs/my-documents/temp/mlb-executable-bets/README.md`. **Run 2026-07-17/18.**
- Other repo-review follow-ups (composite-formula regression test, undocumented env
  vars `KALSHI_PROD_*`/`ALPACA_*`/`TELEGRAM_*` in `.env.example`, settlement
  double-count-by-ticker, three-way Brier definition mismatch, cross-process trade-log
  lock) are catalogued in the repo-review doc.

## 2026-06-29 -- De-vig the spread & total models (fix the always-YES bias)

### Why

A review of recent betting found World Cup spread bets were **always `YES`**
(favorite covers): 44/48 live WC spread markets priced model fair-value above
the market, including **both teams in the same match** — which is impossible for
a genuine edge. Root cause: `consensus_spread_prob` and `consensus_total_prob`
inferred the expected margin/total from the **raw, vigged** book-implied
probability (`implied_prob(book_odds)`), never de-vigging. The two-way spread/
total sums to ~1.05-1.08 implied, so each side ran ~half the vig high, inflating
the inferred mean and thus `P(cover)`/`P(over)` for both sides of every game.
The moneyline path (`consensus_fair_value`) already de-vigs — spreads/totals
were the outliers. The bias inflated claimed edges (→ Kelly oversizing, often on
the longest-shot picks) and removed the model's ability to ever take NO or pass.

### What changed

- **De-vig the two-way line before inferring the mean.** Both functions now
  divide the matched outcome's implied by the book's overround
  (`sum(implied_prob(o) for o in outcomes)`), mirroring the moneyline devig.
  Each book record now carries both `implied` (de-vigged) and `raw_implied`.
- **Validated live:** on the WC spread board the always-YES lean dropped from
  44/48 (92%) to 39/48, and mean model edge fell ~1 point — claimed edges are
  now honest. +4 tests (`TestSpreadTotalDevig`), 496 passing.

### Known residual (separate follow-up, not fixed here)

De-vig removes the vig-driven half of the bias but **not all of it**: 16/22
matches still show both sides leaning YES, traced to the **soccer margin stdev
(1.8)** making the normal-CDF tail too fat for soccer's discrete low-scoring
margins. A sensitivity sweep shows stdev ≈ 1.4 makes the model symmetric
(mean fair−mid ≈ 0, both-sides-impossible 16→1). Deferred as a calibration
decision because lowering stdev also shrinks a possibly-real underpricing edge
(placed soccer spreads hit 31% vs 19% market-implied) and should be chosen
against settled outcomes, not fit to one day's board.
## 2026-06-28 -- Wimbledon Tennis Sport Coverage Added

### Why

Wimbledon 2026 starts June 29. The scanner had no tennis mapping, so Kalshi's
Wimbledon match-winner markets were invisible. Tennis was deferred from the
2026-06-20 World Cup release because markets weren't open yet (Kalshi API
confirmed 0 open markets on June 20 for all tested prefixes).

### What landed

- **Tennis wired as a new h2h-only sport** — match-winner (`game` category) only;
  no spread or total markets on Kalshi for tennis. `KXATPMATCH` → `tennis_atp_wimbledon`
  and `KXWTAMATCH` → `tennis_wta_wimbledon` added to `CATEGORY_MAP` and
  `KALSHI_TO_ODDS_SPORT`. New `wimbledon` and `tennis` filter shortcuts.
- **Player-name extraction** — no new regex needed. Live markets read
  "... wins the *Tsitsipas* vs *Djokovic* professional tennis match in the 2026
  Wimbledon ...", which the existing "(?:vs|at) ... professional" branch in
  `extract_event_teams()` already parses, returning the two players' last names.
  Those substring-match the Odds API full names ("Stefanos Tsitsipas").
- **Display wiring** — `KXATP`/`KXWTA` prefixes → sport label "Tennis" in
  `ticker_display.py`. Player abbreviations in ticker suffixes pass through raw
  (not in the US-sport team alias table, which is correct).
- **No edge-math changes** — tennis uses the existing de-vigged h2h moneyline
  path (`detect_edge_game`). No spread/total stdev entries needed.

### 2026-06-29 — local validation + date-matching fix

The 06-28 work was authored by a cloud agent with the Kalshi API egress-blocked,
so prefixes and the rules format were guesses. Validated locally against live
markets and corrected:

- **Prefixes confirmed.** `KXATPMATCH` / `KXWTAMATCH` are correct (3+ open
  markets each on 2026-06-29). The speculative "wins this match against" regex
  the cloud agent added was dead code (real markets use the "vs ... professional
  tennis match" phrasing) and was removed.
- **Date-matching fix (the real blocker).** Tennis tickers embed the market's
  *expected expiration* date (~a day after the match), not the commence date —
  e.g. `KXATPMATCH-26JUL01TSIDJO` is the **Jun 30** 09:00 UTC match. The
  exact ET-date equality in `find_market_event()` rejected every market with
  "0 candidate events". Added a tennis branch (`_is_tennis_market()`): a player
  pair meets at most once per tournament, so the single both-players candidate
  is accepted when its commence lands within 3 days of the ticker date. After
  the fix, `--filter wimbledon` matches markets to events and `detect_edge_game`
  computes fair values (e.g. Djokovic 0.832 fair vs 0.87 ask → correctly no bet).

### Verification

`TestTennisMappings` (real-data extraction + date-tolerant matching) and
`TestTennisDisplay` → **505 passing**. Live: `python scripts/scan.py sports
--filter wimbledon` matches all 76 markets to odds events (no edges cleared the
threshold at validation time — an efficient market, not a wiring gap).

### Files

`scripts/kalshi/edge_detector.py`, `scripts/shared/ticker_display.py`,
`tests/test_edge_detection.py`, `tests/test_ticker_display.py`,
`CLAUDE.md`, `docs/kalshi/kalshi-sports-betting/SPORTS_GUIDE.md`, `docs/CHANGELOG.md`.

---

## 2026-06-24 -- C4: retire the base "high" confidence tier's composite-score premium

### Why

The 90-day review (F49) flagged that High-confidence bets keep *under*performing Medium ones (High 41.5% WR / +13.5% ROI vs Medium 53.2% / +44.4%), meeting C4's deferral condition (118 high-conf trades). The roadmap required measuring whether the tier carries any predictive signal before acting.

### What the audit found (306 settled bets)

- **No positive signal — controlled for edge.** Bucketing High vs Medium by *claimed* edge: in the 5–10% band High is 34.4% WR (n=32) vs Medium 62.7% (n=51); in the 10%+ band 45.2% vs 46.8%. At equal claimed edge, High wins less.
- **Mechanism is over-claim on efficient prices**, not "tight = low edge" as the roadmap guessed. High actually carries *higher* avg claimed edge (19.1% vs 15.9%) — a tight ≥8-sharp-book consensus is an efficient price, so a large model edge against it is most likely model error. Worst cells: NCAAMB High (33.8% edge / 28.6% WR), HIGH/NO (−29.7% ROI). High works only for NHL (70% WR).

### What landed

- **`high`→`medium` in the sports composite weight** (`{low:3, medium:6, high:6}×0.30`) across all three formulas (game/spread/total) in `edge_detector.py`. "High" no longer earns a +0.9 composite premium, so it can't float no-signal bets up the `--max-bets` queue or ease Gate 4 (`MIN_COMPOSITE_SCORE`).
- **Left intact:** the `high` *label* (still a Gate 4.6 restriction on NO-favorites), Gate 4.5, and Kelly sizing (which never read confidence). Scoped to **sports only** — futures/prediction modules mint "high" by different rules and were out of scope. No env var.
- A documented follow-up **C4b** (edge-cap the minting rule to make a meaningful High tier) is logged in the roadmap; deferred because High underperforms even at low edge.

### Verification

Full suite **493 passing**. No test asserted the internal composite formula (composite is supplied as a fixture), so the change is a pure ranking-calibration tweak; behavior validated against the 306-bet settlement history. Live automation is unaffected until the branch merges to master.

### Files

`scripts/kalshi/edge_detector.py`, `CLAUDE.md`, `docs/CHANGELOG.md`, `docs/enhancements/ROADMAP.md`.

---

## 2026-06-23 -- L1 Phase 2 live-freshness fixes (fail-closed staleness + min-books floor)

### Why

A code review of the L1 Phase 2 live-odds path found two freshness holes that both failed *open* (toward using stale/thin data) — the opposite of what the feature is for. They only bite when `ALLOW_LIVE_BETS=true` (off by default), so no live bet was affected, but they had to be fixed before live betting is enabled.

### What landed

- **Fail closed on missing `last_update` (CRITICAL #1).** `_is_bookmaker_stale` previously treated a bookmaker with a missing/unparseable `last_update` as *fresh* on an in-progress game — so a suspended feed that dropped its timestamp would silently flow into the live consensus. It now **excludes** such a book (and logs it). Real Odds API event responses always carry `last_update`, so this only fires on malformed data; pre-game markets are untouched.
- **Minimum fresh-books floor (CRITICAL #2).** After the stale filter runs on a live game, if it **thinned** the consensus below `MIN_LIVE_CONSENSUS_BOOKS` (**default 3**) surviving fresh books, the game is now skipped instead of priced off 1-2 quotes. The guard fires **only when staleness actually removed books** — a live market whose books are all fresh is no thinner than pre-game and keeps its existing behavior, as do all pre-game/futures markets.
- **Visible fallback (MEDIUM #3).** When the per-event live refresh fails (404 / quota / network), `_refresh_event_if_live` now logs a warning before falling back to the stale sport-level snapshot, instead of degrading silently.

### Verification

+4 tests (thinned-below-floor → skip, all-fresh-not-floored, missing/unparseable `last_update` exclusion, plus the config knob default + negative-value guard); existing fixtures gained a realistic per-book `last_update`. **492 passing.**

### Files

`scripts/kalshi/edge_detector.py`, `app/config.py`, `tests/test_edge_detection.py`, `tests/test_config.py`, `.env.example`, `CLAUDE.md`, `docs/CHANGELOG.md`, `docs/enhancements/ROADMAP.md`.

---

## 2026-06-23 -- 90-Day Review Fixes: NO-Side Floors (R28), NBA Consensus (R29), Auto-Stdev Calibration (C8), Live Odds Phase 2 (L1)

### Why

The 90-day review (302 settled trades) surfaced three structural P&L/calibration problems and the live-odds work had a Phase 2 remaining:
- **NO contracts net -7.0% ROI vs YES +48.1%** at near-identical (~48%) win rates (F45) — a structural pricing drag on the NO side.
- **NBA -23.3% ROI** across 32 bets (F46), partly edges built on thin/stale recreational lines.
- **Model overconfidence** — predicted probabilities run 11-25% above realized win rates across mid/high bands (F47); per-sport stdevs were still hand-tuned (F40).
- **L1 Phase 1** fixed live-edge *freshness* via caching TTLs but still re-pulled whole sports and trusted every in-play book.

### What landed

- **R28 — global NO-side floors.** Every NO bet's effective edge floor is now `max(per-sport floor, NO_SIDE_MIN_EDGE_GLOBAL)` (**default 8%**), independent of price (Gate 4.6b), plus a `NO_SIDE_KELLY_MULTIPLIER_GLOBAL` dampener on all NO sizing (**default 1.0 = off**). The edge floor does the heavy lifting; the multiplier is a tuning lever.
- **R29 — NBA consensus-book floor.** NBA games with fewer than `MIN_CONSENSUS_BOOKS_NBA` (**default 8**) agreeing books are dropped to `low` confidence, which Gate 4.5 (`MIN_CONFIDENCE=medium`) then rejects — filtering edges built on stale recreational lines.
- **C8 — auto-recalibrated per-sport stdevs.** `model_calibration.py` now writes recommended `SPORT_MARGIN_STDEV` / `SPORT_TOTAL_STDEV` to `data/cache/calibration_stdevs.json` from settled-trade outcomes; the edge detector reads them at runtime, falling back to hardcoded defaults when the cache is older than `CALIBRATION_STDEVS_TTL_DAYS` (**default 30**). Closes the F40 hand-tuning loop.
  - **Fail-safe hardening (follow-up review):** the loader now validates every cached value (numeric, finite, within `[0.5, 60]`) and rejects the whole map on any bad entry; an unsupported `version` or unreadable file falls back to defaults instead of silently retaining stale overrides; the per-lookup re-parse/re-warn loop is fixed (the file's mtime is marked processed up front); and the writer is now atomic (temp file + `Path.replace`) so a concurrent scan can't read a half-written file.
  - **Statistical fix (C8-followup):** the recommender no longer moves a sport's stdev on noise. It now requires **≥20 settled bets** in that sport+market, gates the move on **statistical significance** (the predicted-vs-realized gap must exceed 1.5 standard errors), uses a gentler `×1.0` step (was `×1.5`) clamped to **`[0.85, 1.25]`** per run (was `[0.8, 1.5]`), and **excludes settlements with no recorded `fair_value`** (previously defaulted to 0.5, contaminating the average). Run against the full 302-bet history, this writes a **single** override — NCAAB margin 12.1 → 14.7 (×1.22) from 29 spread bets at a significant +21.8pp overconfidence gap — and every other sport holds at base (below the floor or within noise). The calibration cron is now safe to run. The earlier cache (NBA totals +39%, soccer margin −20% on samples of 1–22 bets) was deleted.
- **L1 Phase 2 — targeted live fetch + stale-book suppression.** For an in-progress matched game, `fetch_event_odds_api` queries `GET /v4/sports/{sport}/events/{eventId}/odds` (bypassing the sport-level cache, with its own single-event cache via `odds_cache.load_event`/`store_event`), and `_is_bookmaker_stale` excludes any book whose line is older than `MAX_LIVE_BOOK_AGE_SECONDS` (**default 1200s / 20m**) from the live consensus.

### Verification

+15 feature tests + 6 C8 fail-safe tests (invalid-value rejection across 5 cases, unsupported-version fallback, plus a global-state reset fixture) + 5 C8 statistics tests (sample floor, significance hold, significant-widen, missing-fair_value exclusion, clamp ceiling) across `test_edge_detection.py`, `test_risk_gates.py`, `test_odds_cache.py`, `test_config.py` → **489 passing**.

### Files

`app/config.py`, `scripts/kalshi/edge_detector.py`, `scripts/kalshi/kalshi_executor.py`, `scripts/kalshi/model_calibration.py`, `scripts/shared/odds_cache.py`, `tests/test_edge_detection.py`, `tests/test_risk_gates.py`, `tests/test_odds_cache.py`, `tests/test_config.py`, `.env.example`, `CLAUDE.md`, `docs/enhancements/ROADMAP.md`, `docs/CHANGELOG.md`.

---

## 2026-06-20 -- Task schedules: first futures automation; per-task email logs

- Added `Weekly-Futures-Execution` (Sat 9:00 AM: `scan.py futures --execute`, budget 10%,
  max 3, unit $1) and the paired `Email-Weekly-Futures` (Sat 9:20 AM). `futures_edge.py`
  now always writes a report on `--save`, so 0-order weeks still email proof-of-life.
  Validated live: `LastTaskResult=0`, 0 bets, every candidate gated.
- Every email shell script now logs to `logs/email_*.log` with exit-code banners.

## 2026-06-20 -- Live In-Play Odds Freshness Fix (L1 Phase 1)

### Why

Edges on **in-progress** games were untrustworthy: the scan flagged them with a `LIVE` tag (R27) but computed the edge against **stale pre-game odds**, producing phantom edges (F44 saw `+50%` "edges" on games already underway). The Odds API already returns live in-play odds on every fetch — the staleness came entirely from caching. The in-process `_odds_cache` had **no TTL**, so in the long-running Streamlit app a pre-game snapshot stayed frozen for hours while Kalshi's price moved during the game.

### What landed

- **TTL on the in-process `_odds_cache`** (`edge_detector.fetch_odds_api`) — now stores `(stored_at_monotonic, events)` and expires entries instead of holding the first response for the whole process lifetime. Within-scan dedup is preserved (back-to-back calls in one scan are sub-second).
- **Live-aware TTL across both cache layers.** New `odds_cache.response_has_live_event()` / `effective_ttl()`: when a sport response contains an in-play event (`commence_time ≤ now`), expiry uses `ODDS_LIVE_TTL_SECONDS` (**default 45s**) instead of the 300s pre-game TTL, so in-progress games refetch current book odds. Pre-game responses keep 300s (quota-friendly). `odds_cache.load()` gained an optional `live_ttl_seconds` arg (backward compatible — `futures_edge` keeps the 3-arg call).
- **Gate 4.8 — `ALLOW_LIVE_BETS` (default off).** The freshness fix makes live edges *honest*, hence executable through scheduled scans. To keep in-play opt-in until calibrated, `size_order()` rejects bets on started games (`is_game_started(ticker)`) unless enabled; `preflight_gate_status()` surfaces it as `live-off`. Mirrors R25. Caveat: detection only fires on moneyline tickers that embed a start time (date-only spread/total tickers aren't caught).

### Verification

+15 tests (`TestLiveAwareTtl`, `TestInProcessCacheTtl`, L1 gate tests) → **463 passing**. Three `test_risk_gates.py` fixtures that used a hardcoded *past* date (`26MAR30…`, `26APR17…`) were bumped to a far-future year so they read as pre-game — fixing latent date fragility that the new gate exposed.

### Files

`scripts/shared/odds_cache.py`, `scripts/kalshi/edge_detector.py`, `app/config.py`, `scripts/kalshi/kalshi_executor.py`, `tests/test_odds_cache.py`, `tests/test_edge_detection.py`, `tests/test_risk_gates.py`, `.env.example`, `CLAUDE.md`, `docs/enhancements/live-in-play-odds-design.md`, `docs/CHANGELOG.md`.

---

## 2026-06-20 -- PGA Tour (Golf Majors) Edge Detection Fixed

### Why

PGA never surfaced edges because the wiring was pointed at the wrong tournament. `futures_edge.py` statically mapped the whole `KXPGATOUR` series to `golf_pga_championship_winner` — but that major already happened in May, so the Odds API key was inactive (no data). Meanwhile the live Kalshi markets were the **U.S. Open** (`KXPGATOUR-USO26-*`), which wasn't mapped at all. Diagnosis also revealed `KXPGATOUR` spans the *entire* PGA Tour calendar (RBC Heritage, Truist, Zurich Classic, qualifiers, ...), while The Odds API only publishes outright fields for the **4 majors**. Completes ROADMAP R19(b).

### What landed

- **`_golf_major_key(title)`** resolves the specific major from the human-readable market title (not the cryptic event code `USO`/`PGC`/...): Masters, PGA Championship, U.S. Open, The Open → the matching `golf_*_winner` Odds API key. Title-based matching cleanly rejects the **"U.S. Open Final Qualifying"** trap (contains "u.s. open" but isn't the major) and avoids "RBC Canadian Open" false-matching The Open (needs "the open"/"open championship", never bare "open").
- **Per-market routing in `scan_futures_markets`** — KXPGATOUR markets resolve their major individually; weekly tour stops + qualifiers fall through to `None` and are skipped (no odds feed → no edge, never a wrong-tournament edge).
- **`--filter pga`** now routes to the futures scanner (was a dead no-odds sports-path entry); `--filter golf-futures` unchanged.

### Verification

+7 tests (`TestGolfMajorResolution` in `tests/test_edge_detection.py`) → 449 passing. Live: `scan.py futures --filter pga` priced the U.S. Open field (71 players, 3 books) and surfaced 2 edges — both correctly caught by risk gates (sub-floor longshot → `price`, NO bet → `score`). The old wiring returned nothing.

### Files

`scripts/kalshi/futures_edge.py`, `scripts/kalshi/edge_detector.py` (pga shortcut), `tests/test_edge_detection.py`, `docs/CHANGELOG.md`, `docs/enhancements/ROADMAP.md`.

---

## 2026-06-20 -- Kalshi v2 Order Endpoint Migration (live order placement fix)

### Why

A live execute attempt failed every order with **HTTP 410 `deprecated_v1_order_endpoint`** — Kalshi retired the v1 `POST /portfolio/orders` endpoint. This blocked *all* live order placement repo-wide (a second, independent reason betting looked dead, on top of the seasonal trough). No money was at risk — 410 is a clean pre-placement rejection. Surfaced because the new World Cup coverage finally produced executable opportunities (6 orders) that drove the pipeline to the order call.

### What landed

- **Migrated `create_order` to the v2 endpoint** `POST /portfolio/events/orders` (same host — `api.elections.kalshi.com` and `external-api.kalshi.com` are interchangeable, so signing/base_url are unchanged). The v2 model is single-book / YES-perspective: `side="bid"` buys YES, `side="ask"` sells YES. The public `create_order` signature is **unchanged**; translation is internal via a new pure, unit-tested `KalshiClient._build_v2_order_body()`:
  - buy YES @ p → `bid`, `price="<p>"`; **buy NO @ p → `ask`, `price="<1−p>"`** (selling YES == buying NO at 1−price).
  - `count` → fixed-point string (`"10.00"`), `price` → YES-perspective dollar string (`"0.5600"`), `self_trade_prevention_type="taker_at_cross"` (now required), `expiration_ts` → `expiration_time`. v1 `buy_max_cost` has no v2 equivalent and was unused — dropped.
- **Response-shape fix:** the v2 create response is lean/flat (`fill_count`, `remaining_count`; no `order` wrapper, no `status`) vs the cancel/get/list schema (`fill_count_fp`, `remaining_count_fp`). New `_order_field()` helper in `kalshi_executor.py` reads both, so `log_trade` and the fill display record fills correctly instead of always reporting "resting" (which would have corrupted exposure/P&L accounting).

### Verification

Unit: +8 order-body tests (`tests/test_kalshi_client_order.py`, incl. the NO→ask inversion) + 4 v2-response tests (`tests/test_fill_accounting.py`) → **442 passing** (was 430). Live: placed two resting 1-contract orders on a World Cup market and canceled both — YES→`bid`@$0.01 (`outcome_side: yes`) and NO→`ask`@$0.99 confirmed by Kalshi as `outcome_side: no`, `no_price_dollars: 0.0100`. Both canceled; no residual exposure.

### Files

`scripts/kalshi/kalshi_client.py`, `scripts/kalshi/kalshi_executor.py`, `tests/test_kalshi_client_order.py` (new), `tests/test_fill_accounting.py`, `docs/CHANGELOG.md`.

---

## 2026-06-20 -- World Cup (FIFA) Sport Coverage Added

### Why

Wagers had dropped to ~0/day since ~June 13. Diagnosis: the pipeline is healthy — it's a **seasonal trough**. A live scan showed NBA/NHL/NCAA/European-club-soccer all out of season, leaving MLB as the only active daily sport (and books only post MLB lines ~1 day out, so future-dated Kalshi games correctly emit no edge). Meanwhile the **2026 FIFA World Cup is live** with deep Kalshi markets and an active Odds API feed — but the scanner had no mapping for it, so it was invisible. (WNBA, NCAA baseball/CWS, and Wimbledon were also considered; user chose World Cup now, Wimbledon deferred to ~June 28 when its markets/odds go live, NCAA baseball skipped as the CWS window closes within days.)

### What landed

- **World Cup wired as a soccer sport** — reuses the existing 3-way (home/draw/away) soccer edge logic with **zero changes to edge math**. `KXWCGAME`/`KXWCSPREAD`/`KXWCTOTAL` added to `CATEGORY_MAP` (game/spread/total) and `KALSHI_TO_ODDS_SPORT` (→ `soccer_fifa_world_cup`); `KXWC` → `soccer` in `_PREFIX_TO_SPORT` (margin/total stdev). New `worldcup`/`wc` filter shortcuts + folded into the combined `soccer` group. Because the no-filter scan iterates `KALSHI_TO_ODDS_SPORT`, World Cup auto-joins the daily scheduled scans with no `.bat` change.
- **Team extraction needed no change** — WC rules read "...the Congo DR vs Uzbekistan **professional** FIFA World Cup soccer game...", and `professional` is already a recognized context keyword, so `extract_event_teams` resolves country names that match the Odds API feed.
- **Display fix (country-code collision):** WC tickers use 3-letter country codes that collide with the US-sports alias map (`COL`=Colombia mis-rendered as "Colorado"). Added `_resolve_team_abbr()` in `ticker_display.py` that keeps the raw code for `KXWC*` tickers; used in both the pick-label (spread) and `parse_pick_team` (game) paths. Edge math was always correct (matches on the full name from rules); this was display-only.

### Verification

Live preview scan returned **40 World Cup opportunities** (34 spread, 6 total; edges to +14.7%, score 8.2). Moneyline produced none above 3% — expected, as 3-way match-winner prices are efficient. +6 tests (`TestWorldCupMappings` in `tests/test_edge_detection.py`; 2 country-code label tests in `tests/test_ticker_display.py`) → **430 passing** (was 424).

### Files

`scripts/kalshi/edge_detector.py`, `scripts/shared/ticker_display.py`, `tests/test_edge_detection.py`, `tests/test_ticker_display.py`, `CLAUDE.md`, `docs/kalshi/kalshi-sports-betting/SPORTS_GUIDE.md`, `docs/CHANGELOG.md`.

---

## 2026-06-15 -- R27: "Started" Column Flags In-Progress Games on Scan Views

### Why

F44 (2026-06-14): a web-UI scan CSV advertised phantom edges — +50.6% on a $0.04 "Washington lose" longshot, +34.8% on HOU@KC — while the post-start CLI priced the same games at +8–10%. Root cause: a game that has already started keeps producing edges (its market is still open) because the only "skip in-progress" filter in `edge_detector.py` keys on `expected_expiration_time`, which is the market **close** (after the game *ends*), not the start. So the scan view compares **live** Kalshi pricing against **stale** pre-game odds. Execution gates already protect real bets; the raw research/CSV surface did not.

### What landed

- **New `Started` column** on every sports scan view, showing `LIVE` for games already underway. **Tag, not exclude** — games stay visible (operator's call) so the edge is shown *with* the caveat rather than silently dropped.
- **New canonical helpers** in `scripts/shared/ticker_display.py`: `ticker_scheduled_utc(ticker)` and `is_game_started(ticker, now=None)`. They mirror the hardened `edge_detector._ticker_scheduled_utc` event-matching logic (ET wall-clock → UTC via a fixed 4h offset; a 1h EST/EDT slip is immaterial for "has it started?"). **HHMM-only** — only moneyline (GAME) tickers embed a start time (the F44 case); spread/total and NBA/NHL tickers carry date only, so `is_game_started` returns `False` rather than risk a false flag. The edge_detector matching path was left untouched to avoid regression risk.
- **Wired into four surfaces:** CLI Rich table (`edge_detector.print_opportunities`), webapp dataframe + CSV (`services.opportunities_to_rows` + `scan_page` column config), saved markdown scan report (`report_writer`), and the emailed `daily_sports_scan` table. No CLI flag and no change to `scan_all_markets` — tagging is a pure display concern, so CLI and webapp inherit it for free.
- **Tightened the misleading comment** at `edge_detector.py:1760` that called the expiration filter a "started/ended" filter — the source of the F44 confusion.

### Verification

+13 tests in `tests/test_ticker_display.py` (`TestTickerScheduledUTC` + `TestIsGameStarted`) → **424 passing** (was 411). Live smoke confirmed past/future/date-only tickers flag correctly.

### Files

`scripts/shared/ticker_display.py`, `scripts/kalshi/edge_detector.py`, `webapp/services.py`, `webapp/views/scan_page.py`, `scripts/shared/report_writer.py`, `scripts/schedulers/automation/daily_sports_scan.py`, `tests/test_ticker_display.py`, `docs/my-documents/enhancements/ROADMAP.md`, `docs/CHANGELOG.md`.

---

## 2026-06-14 -- Per-Sport Edge Floors Lowered 0.06 → 0.04 + Doc-Drift Sweep

### Why

User reported MLB wagers had dried up to ~0/day across the schedulers since the 06-03 fixes. June is almost entirely an MLB slate (NBA/NHL seasons winding down), so a throttled MLB made the whole pipeline look dead. Diagnosis confirmed MLB games are still found and matched correctly — the binding constraint is the **edge gate**, not confidence or score.

### Root cause — a double-correction

Two changes landed together on 2026-06-03/06-05 and stacked:

1. **Edge-matching correctness fixes** (opponent+date validation, strength-rank team matching) **de-inflated** MLB edges. The 06-03 report had phantom edges of +15% and +31%; honest post-fix edges now cluster at **3–6%** (live repro on 06-14 showed real MLB edges of 4.0%, 4.3%, 5.3%, ~8%).
2. **The per-sport edge floor** was set high *because* "the model over-claims ~15% edge" — but that over-claim **was** the matching bug, now fixed upstream. The floor was correcting the same error a second time, rejecting the honest 3–6% edges that remained.

### What landed

- **Lowered `MIN_EDGE_THRESHOLD_MLB`, `_NBA`, `_NCAAB` from 0.06 → 0.04** (live `.env`). Re-admits honest 4–5% edges. Running as a **2–4 week experiment** — recalibrate on fresh post-fix data (weekly `Calibration` + monthly run accumulate it) and tune from there. If 4% loses money, tighten back up on real evidence rather than the contaminated pre-fix numbers.
- **Doc-drift sweep.** Discovered the docs had been citing values that were never even the live 0.06: CLAUDE.md said NBA/NCAAB/MLB **0.08** and `MIN_MARKET_PRICE` **$0.10**; ARCHITECTURE.md / SETUP_GUIDE.md / CLOUD.md / kalshi_executor.md / the edge-radar skill variously cited NBA **0.12**, NCAAB **0.10**. Production had quietly been running 0.06. Standardized every current-state reference to the live values: **per-sport 0.04**, **`MIN_MARKET_PRICE` $0.06**. Historical CHANGELOG entries (R14, R7) left intact as record.
- **Webapp** — `scan_page.py` Min Edge help tooltip corrected (it hardcoded "NBA/NCAAB/MLB 8%" + "$0.10 floor"; the rest of the webapp reads floors dynamically from `.env` via `app.config`, so no logic change was needed).

### Files

`.env` (live floors, gitignored), `CLAUDE.md` (commit `3cf78b8`), `webapp/views/scan_page.py` (commit `1335267`), `docs/ARCHITECTURE.md`, `docs/setup/SETUP_GUIDE.md`, `docs/web-app/CLOUD.md`, `docs/scripts/kalshi_executor.md`, `.claude/skills/edge-radar/SKILL.md`, `docs/CHANGELOG.md`, plus memory (`project_edge_matching_validation.md`).

---

## 2026-06-05 -- Same-City Team-Match Inversion Fix (phantom NO-side edge)

### Why

A spot-check of why zero wagers had been placed for several days (Jun 2–5) confirmed the quiet stretch was *correct* — a thin early-June calendar (MLB plus two Finals series whose future games aren't priced yet) combined with the per-sport 0.08 edge floors and the `--min-bets 3` batch gate legitimately produces no qualifying batches. **But** the check surfaced the day's top-ranked opportunity (composite 8.3): a **+27.9% edge on "LA Dodgers lose"** in the Jun 5 Angels @ Dodgers game. That edge was entirely fabricated.

### Root cause

Kalshi truncates its market sub-titles, so the Dodgers-win market's subject reads `"Los Angeles D"` (not "Dodgers"). `_team_match` matched that against the odds event's two outcomes via a **first-match-wins** loop, and its weakest fallback rule (`kalshi_words[0]` — the city word "los") matched **both** "Los Angeles Angels" and "Los Angeles Dodgers". The loop took whichever outcome the odds feed listed first — the away Angels — so the Dodgers market was priced with the **Angels'** win probability (0.36), inverting the favorite. The "Dodgers lose" NO side (market $0.36) was then compared against `1 − 0.36 = 0.64`, manufacturing a +27.9% edge where the true edge is ~0%. Any same-city matchup where the nickname truncates was exposed; the team listed **second** in the feed was the one corrupted.

This is **not** the 2026-06-03 contamination bug — the correct game and date matched fine. It is wrong *side selection within the right event*, which that fix didn't cover.

### What landed

- **Strength-ranked, tie-refused team matching** (`scripts/kalshi/edge_detector.py`). New `_team_match_strength()` scores candidates: substring/alias (tier 3/2) > shared nickname (tier 2) > bare city word (tier 1). New `_match_team_outcome()` picks the **unique** strongest outcome and returns "ambiguous → no edge" on a genuine tie (e.g. a bare-city reference). `_team_match()` is preserved as `strength > 0`, so all other callers are byte-for-byte unchanged.
- **Applied to both team-keyed consensus functions** — `consensus_fair_value` (moneyline) and `consensus_spread_prob` (which was *worse*: it pooled **both** teams' spreads into one median when ambiguous). `consensus_total_prob` takes no team and was already safe.
- **Verified live** — the Dodgers market now prices at fair 0.639 (the actual favorite), edge collapses from +27.9% to ~0%; the phantom pick is gone from the scan.
- **Tests** — +5 regression tests (`TestSameCityDisambiguation`): strength ordering, unique-pick, city-only ambiguity refusal, correct LA-team resolution, and the end-to-end no-phantom-edge assertion. 403 → **408 passing**.

### Separate finding (not changed — flagged for decision)

The same spot-check found a **stale-offshore-line** weakness, unrelated to the matching bug: in Jun 5 Tampa Bay @ Miami, five sharp books had Miami devigged at ~0.20–0.28 while four offshore books (betonlineag, lowvig, mybookieag, betus) carried stale ~0.46 lines. The weighted median landed on the high cluster (fair 0.46, range 0.20→0.47), producing a +24.7% edge driven by book disagreement rather than value. Moneyline consensus has no disagreement penalty beyond withholding the "high" tier. Candidate future work: reject or down-weight when `max_fair − min_fair` is large.

### Files

`scripts/kalshi/edge_detector.py`, `tests/test_edge_detection.py`, `docs/scripts/edge_detector.md`, `docs/CHANGELOG.md`, plus memory (`project_edge_matching_validation.md`).

---

## 2026-06-03 -- Edge-Matching Contamination Fix, Soccer 3-Way, Test-Isolation Guard

### Why

A user spot-check after seeing implausible MLB edges (e.g. "+34.7% Minnesota lose") exposed a cross-game contamination bug in edge detection: `consensus_fair_value`/`consensus_spread_prob`/`consensus_total_prob` matched a Kalshi market against **any** odds event a single team appeared in. When a team played a series, or its game was simply absent from the feed (e.g. scanning two days out before books post lines), the detector priced the market against the **wrong game** — wrong opponent, or the wrong game of a playoff series with home/away flipped — fabricating large edges. Two NBA Finals open positions had been sized off this.

### What landed

- **Opponent + date validated matching (`find_market_event`)** — a market is priced only against the odds event that contains **both** its teams on opposite sides **and** agrees on schedule: moneyline (GAME) tickers match the embedded start time (within 6h); spread/total and NBA/NHL date-only tickers require exactly one candidate on the ticker's ET game date. Absent or ambiguous ⇒ **no edge** (never guess). Fixes both variants — wrong-opponent and the playoff-series single-event home/away flip (the old `len(candidates)==1` shortcut skipped date validation). `extract_event_teams` also strips the "Game N:" playoff prefix and the "teams in the" totals filler.
- **Belt-and-suspenders** — the three `consensus_*` functions now refuse (return None + warn) if their subject matched >1 distinct event, so a team is never pooled across games even if a caller forgets to pre-scope.
- **Soccer 3-way support** — `consensus_fair_value` skipped any market without exactly 2 outcomes, so soccer h2h (home/draw/away) silently produced **no** edges. Now uses proportional devig over 2- or 3-outcome markets; the Kalshi "team to win?" binary takes the team's devigged win share (draw → NO side). 2-way behavior unchanged.
- **MLB edge floor + threshold-drift correction** — added `MIN_EDGE_THRESHOLD_MLB=0.08` (MLB: 40% WR, -12% ROI, model over-claims ~15% edge). Corrected long-standing doc drift: R14's NBA 0.12 was **proposed but never adopted** — production runs 0.08. NBA/NCAAB/MLB now consistently documented at the 0.08 peer floor across `.env.example`, `CLAUDE.md`, and the edge-radar skill.
- **Calibration recommendation refresh** — `model_calibration.py`'s top "Confidence Signals" recommendation kept re-recommending one-way confidence bumps that already shipped as R13 (2026-04-24). Rewritten to say R13 shipped and point at the real remaining suspect: the base ">=8 sharp-books + tight-consensus" high-tier rule.
- **Test-isolation incident + guard** — `log_trade()` persists via `save_trade_log()` as a side effect, and `test_fill_accounting` calls it with an ad-hoc list, so a full `pytest` run overwrote the live `data/history/kalshi_trades.json` with a test record. Added an autouse `conftest.py` fixture redirecting the trade/settlement log paths to a per-test tmp dir (the suite now leaves both real logs byte-identical). New `scripts/kalshi/recover_trade_log.py` rebuilt the log from live Kalshi positions (15 positions, $22.03 restored; model fields like `edge_estimated` unrecoverable, set null — not needed for settlement P&L).
- **Tests** — +17 regression tests (contamination scenario, series disambiguation, wrong-date refuse, the consensus refuse-guards, 3-way soccer devig). 386 → **403 passing**.

### Caveat

The contamination likely inflated some **historical** claimed edges (MLB and consecutive-day/playoff series). Re-run calibration after ~2 weeks of clean post-fix settlements before drawing edge-bucket conclusions.

### Files

`scripts/kalshi/edge_detector.py`, `scripts/kalshi/model_calibration.py`, `scripts/kalshi/kalshi_executor.py` (docstring), `scripts/kalshi/recover_trade_log.py` (new), `tests/conftest.py`, `tests/test_edge_detection.py`, `tests/test_risk_gates.py`, `.env.example`, `CLAUDE.md`, `docs/scripts/edge_detector.md`, `docs/ARCHITECTURE.md`, `docs/SCRIPTS_REFERENCE.md`, `docs/kalshi-sports-betting/SPORTS_GUIDE.md`, `.claude/skills/edge-radar/SKILL.md`, `docs/CHANGELOG.md`, plus memory. Live `.env` (gitignored) carries the MLB override; rebuilt `data/` files are gitignored.

### Commits

`e28d157` (matching A+B), `40c3711` (test guard + recovery tool), `c066c03` (MLB floor + drift + calibration rec), `ca1d124` (series-flip date validation), `e1960ec` (soccer 3-way) on `mike_win-desktop`. This entry is the docs/memory propagation.

---

## 2026-05-31 -- Account-Growth Graph on the Pages Site (+ weekly auto-refresh)

### Why

The Kalshi account-growth graph (`/update-account-graph`) only existed locally under the gitignored `docs/my-documents/account-graph/latest/`, so it never reached the public dashboard at `edge-radar.mikesailab.com`. Wanted it one click away from the homepage, kept current automatically.

### What landed

- **Orange "Live P&L" button** in the `index.html` hero, next to the emerald *Open the app* and blue *Source* CTAs. Links to the graph with `rel="nofollow noopener"`.
- **Publish path** — the deploy workflow serves only `.claude/html/`, so the graph is copied there as `account-40c3eb1d3d3cb9c4e07fee61.html` (unguessable name). The site is public + unauthenticated, so this is *lightly hidden, not protected*: real dollar figures are visible to anyone with the link. A `<meta name="robots" content="noindex, nofollow">` tag (added to the generator's `render_html()`) keeps it out of search indexes.
- **Weekly auto-refresh** — `scripts/schedulers/automation/refresh_account_graph.py` pulls the live Kalshi snapshot, regenerates HTML + PNG, copies the HTML into `.claude/html/`, then pushes **only that one file** to `master` via the `gh` contents API (which fires the Pages deploy). Generation must run locally because it needs the `.env` Kalshi keys and the gitignored local settlements ledger. The push is best-effort and logs to `logs/account_graph_refresh.log`; it never touches the `mike_win-desktop` working branch.
- **Scheduler** — new `account-graph` profile in `install_windows_task.py` (Sundays 9 AM PT), plus `WEEKLY` schedule support added to the installer. Install with `python scripts/schedulers/automation/install_windows_task.py install account-graph`.
- **`.gitignore`** — `.claude/html/account-*.html` is ignored so the weekly out-of-band master commit is the file's sole manager and never collides with branch PRs.

### Files

`.claude/html/index.html`, `scripts/schedulers/automation/refresh_account_graph.py`, `scripts/schedulers/automation/install_windows_task.py`, `.gitignore`, `docs/CHANGELOG.md`. Local-only (gitignored): `docs/my-documents/account-graph/Script/build_account_graph.py` (noindex tag), `docs/my-documents/account-graph/README.md`, `docs/my-documents/task-schedules/README.md`.

---

## 2026-05-17 -- Task schedules: midday and late same-day runs; NextDay moved to 8:30 PM

Per `timing-analysis-2026-05-17.md`: the no-date-filter scan hit every time while
`--date today` was empty 71% of mornings, so the slate filter, not the clock, was the
bottleneck. Added daily `All-Sports-NoDateFilter-Midday-Execution` (11:00 AM) and
`All-Sports-SameDay-Late-Execution` (2:00 PM), each with an email pair. Moved
`All-Sports-NextDay-Execution` from 6:00 PM to 8:30 PM PT (it was empty 43% of the time at
6 PM, before next-day lines were posted). Retired the Mon/Thu 5:20 AM
`All-Sports-NoDateFilter-Execution` and its email.

## 2026-05-15 -- Pages Site Theme Alignment with mikesailab.com

### Why

The Pages site at `edge-radar.mikesailab.com` was visually disconnected from the parent `mikesailab.com` site — neon-teal accents, gradient hero, pulsing dot, three custom fonts (Outfit + Inter + JetBrains Mono), 545 lines of bespoke CSS. The parent site is the opposite: Tailwind, Inter, zinc/black, flat surfaces, no glow. Two sibling sites should look like siblings, especially because `mikesailab.com` already has an Edge-Radar "Live Sites" tile rendered with the parent palette + emerald accent. The Pages site now matches that vocabulary so a visitor jumping from one to the other doesn't get whiplash.

### What landed

- **`.claude/html/index.html`** — full rewrite. Replaced 545 lines of custom CSS with Tailwind CDN + Inter (single font; `ui-monospace` for `<pre>` blocks). Palette: `bg-[#060606]` background, `zinc-100/400/500/600` text, `zinc-900/40` surfaces with `border-zinc-800/60`. **Emerald** (low opacity) as Edge-Radar's accent — same color the parent site already uses on its Edge-Radar radar tile, and matches the favicon's `#10b981`. **Sky-400** small `● Live` pill in the eyebrow, matching the parent site's "Live Sites" convention. Hero gradient text + 900px radial glow gone; pulsing dot gone; multi-color pill palette (purple/orange/red) gone. 978 lines → 253 lines.
- **Mobile CTA fix** (`3736f67`) — the original 2-column grid clipped the `edge-radar.streamlit.app` label inside the emerald primary tile on narrow viewports. Switched to `flex-col sm:flex-row` so each CTA gets full width on mobile, with `min-w-0` + `truncate` as a safety net.
- **Quick Links refresh** — dropped `Reports tree` (the `reports/` directory is gitignored, so the GitHub link 404s for anyone who isn't me). Added two: `/edge-radar` skill link (`.claude/skills/edge-radar/SKILL.md`) and `Scripts Reference` (`docs/SCRIPTS_REFERENCE.md`). Now 6 tiles total — fits cleanly as 2×3 on desktop, 3×2 on tablet, 6 stacked on mobile.
- **`.claude/backup/index.html.backup-2026-05-15`** — snapshot of the prior teal-themed dashboard, captured per the documented backup convention (memory line 53 of `reference_mikesailab_domain.md`). `.claude/backup/README.md` updated with the new row.
- **Memory** — `reference_mikesailab_domain.md` got a new "Theme alignment with mikesailab.com (2026-05-15)" section documenting the palette + framework decision, plus the Quick Links count updated from 5 to 6 in the page-contents section.

### Where the deploy actually lives (unchanged)

Still GitHub Pages via `.github/workflows/deploy.yml`, fed from `.claude/html/` on `master`. Both commits sit on `mike_win-desktop` ahead of `master`; the deploy workflow's path filter (`.claude/html/**`) will fire automatically when the user merges to master.

### Files

`.claude/html/index.html`, `.claude/backup/index.html.backup-2026-05-15`, `.claude/backup/README.md`, `docs/CHANGELOG.md`, `memory/reference_mikesailab_domain.md`.

### Commits

`e20c739` (theme rewrite) and `3736f67` (mobile CTA fix + quick link refresh) on `mike_win-desktop`. This entry is the third commit in the trio (the docs/memory propagation).

---

## 2026-05-13 -- R11 Explicit Direction Fields in Settlement Schema

### Why

The settlement record's `fair_value` field carried bet-side perspective by convention, but pre-R5 entries written before the convention was tightened mixed YES- and NO-perspective values without a tag. Any post-hoc analysis that wanted to compare probabilities across bets had to read `side` separately and flip — easy to get wrong, impossible to audit. R11 makes the perspective explicit at write time so future analytics work isn't a guessing game.

### What landed

- **`scripts/kalshi/kalshi_settler.py`** — new `_compute_fair_value_yes(trade) -> (float | None, str | None)` helper. Returns YES-perspective probability and explicit side tag; refuses to guess when `side` is missing. Wired into `build_settlement_record()`. Two new keys on every settlement going forward: `fair_value_yes` (always YES-perspective) and `fair_value_side` (perspective tag for the legacy `fair_value` field). Legacy `fair_value` unchanged — `model_calibration.py`'s bet-side reader is untouched since it's been correct since R5; a YES-perspective cross-cut on the calibration loader is left for a future task when the post-R11 cohort has enough sample to warrant it.
- **`tests/test_reconciliation.py`** — new `TestComputeFairValueYes` class with the four boundary cases: YES bet preserves value, NO bet flips to `1-fv`, missing side yields `(None, None)`, missing fair_value with side present yields `(None, side)`. New `test_carries_r11_perspective_fields` on `build_settlement_record` and an extended assertion on the missing-optional-fields shape test (verifies the new keys are always present, not just sometimes-missing). **386 tests passing** (was 381, +5).
- **`data/history/README.md`** — documented the two new fields and the pre-R5/R11 perspective ambiguity. Reaffirmed the no-backfill stance: the underlying side resolution isn't reliably recoverable on the 178 pre-R5 orphans and synthesizing the field would be fabricating data.
- **`docs/my-documents/enhancements/ROADMAP.md`** — removed R11 row from P2 table; new Completed entry under `2026-05-13`; header note updated.

### Deliberately not in scope

- **No calibration-loader change.** `model_calibration.py:127-128` already assumes bet-side perspective and that assumption is correct for the post-R5 cohort. Switching it to consume `fair_value_yes` would be its own ship; doing it now would change Brier numbers across the rolling window without a clear before/after measurement story.
- **No backfill.** Same rationale as R5 — the missing fields don't exist anywhere on disk.

### Files

`scripts/kalshi/kalshi_settler.py`, `tests/test_reconciliation.py`, `data/history/README.md`, `docs/my-documents/enhancements/ROADMAP.md`, `docs/CHANGELOG.md`.

---

## 2026-05-08 -- Pages Site Privacy Pass + Streamlit Cross-Link

### Why

The Streamlit dashboard at `edge-radar.streamlit.app` is functionally complete and the user wants it discoverable from the personal GitHub Pages diagram site at `edge-radar.mikesailab.com` — but **not** advertised from the public GitHub repo. Three things had to land at once: scrub the README of every link that points strangers at the deployed instance, add the cross-link on the Pages site below its hero, and document the previously-unwritten fact that the Pages deploy is workflow-driven from `.claude/html/` (not from the orphan `gh-pages` branch).

### What landed

- **`README.md`** — removed five outbound advertisements: the `Dashboard` shields.io badge, the `Data Flow` shields.io badge, the centered hero banner pointing at the data-flow diagram, the inline pointer above the Mermaid graph, and the `Local Dashboard` + `Cloud Dashboard` rows from both the Next Steps and Documentation tables. The README no longer surfaces `mikesailab.com`, `michaelschecht.github.io/Edge-Radar/`, or `edge-radar.streamlit.app` to drive-by GitHub visitors. The `webapp/` and `.github/workflows/` lines in the architecture diagram stay — those describe code structure, not advertising.
- **`docs/ARCHITECTURE.md`** — same scrub: dropped the "View the interactive data-flow diagram" callout that pointed at the GitHub Pages site.
- **`.claude/html/index.html`** — added a small JetBrains Mono `↗ edge-radar.streamlit.app` link directly under the hero stats, styled with `var(--accent)` so it inherits the existing emerald accent and the underline picks up `var(--accent-dim)` for hover affordance. Sits inside `<section class="hero" id="overview">` so it visually closes the title block. Triggers the `Deploy to GitHub Pages` workflow on merge to master via the `.claude/html/**` path filter.
- **`webapp/theme.py`** — _briefly_ rendered the same link from `page_header()` as a misread of the user's intent (assumed `mikesailab.com` was a Streamlit deployment with a custom domain; it's actually GitHub Pages). Reverted in `8b8854e` once the hosting model was clarified — the Streamlit app linking to itself was a no-op self-link.

### Where the deploy actually lives (corrects a bad assumption)

`mikesailab.com` is a custom CNAME on GitHub Pages, **not** a Streamlit Cloud custom-domain deployment. The current Pages config is `build_type=workflow` with source `gh-pages /` — but the `gh-pages` branch is vestigial. The live site is built and uploaded by `.github/workflows/deploy.yml`, which runs on pushes to `master` that touch `.claude/html/**` and uploads the entire `.claude/html/` directory as the Pages artifact. Direct commits to the `gh-pages` branch (such as the dead `e388f5f` commit on that branch from earlier in this session) are ignored by the deploy. Future edits to the diagram site go through `.claude/html/index.html` on master, full stop.

### Files

`README.md`, `docs/ARCHITECTURE.md`, `docs/CHANGELOG.md`, `.claude/html/index.html`, `webapp/theme.py` (revert).

---

## 2026-05-01 -- Account Snapshot Chart (Snapshot Mode for `edge-radar-analysis`)

### Why

Visual companion to the markdown betting analysis. After each Kalshi balance pull the user wants to see cumulative account growth — deposit baseline through today's live total — in one re-runnable artifact, with the same sport / bet-type / side / confidence breakdowns the analysis report already produces. Markdown tables answer "how am I doing"; a chart answers "what does the growth curve look like, and where is the open-position value sitting today."

### What landed

- **`docs/my-documents/account-graph/Script/build_account_graph.py`** (local-only, gitignored) — self-contained Plotly HTML builder. Reads `data/history/kalshi_settlements.json`, parses sport + bet-type from the `KX<SPORT><BET_TYPE>-…` ticker prefix (works across the full 178-bet pre-R5 cohort whose `category` field is `null` on disk), aggregates daily P&L, and writes a single CDN-loaded HTML page — no install step.
- **CLI args:** `--cash`, `--portfolio`, `--positions` required; `--as-of`, `--deposit`, `--deposit-date`, `--out-dir`, `--settlements` optional. Each run also writes a `snapshot.json` next to the HTML capturing every input + summary stats so the chart is byte-reproducible from the snapshot file alone.
- **Folder convention:** `docs/my-documents/account-graph/Script/` for the builder, `docs/my-documents/account-graph/<M-D-YY>/` for each run's output. The dated subfolder is auto-derived from `--as-of` so historical snapshots are preserved automatically — no manual rename or move step.
- **Live point handling:** the historical line uses the settled-only model (deposit + cumulative settled P&L) since open-position market value isn't observable for past days. The `--as-of` day is anchored to the actual `cash + portfolio` total and rendered as a gold star on the chart; hover surfaces the cash / open-position / settled-only split. The "open-position drift" reported in the footer is the unrealized value sitting in open positions on the snapshot date.
- **`.claude/skills/edge-radar-analysis/SKILL.md`** (tracked) — extended with a new "Account Snapshot Chart" section documenting trigger phrases ("snapshot the account", "regenerate the account graph", "build the account chart"), required inputs, run command, optional flags, and execution steps. Skill description + argument-hint also expanded so dispatch routes correctly.

### Verification

- Smoke-tested with the user's 2026-05-01 portfolio status pull (cash $65.88, portfolio $27.54, 23 open positions): builder writes `account_graph.html` + `snapshot.json` to `5-1-26/`, settled-only balance reconciles to $78.04 (deposit $45.50 + settled P&L $32.54 across 178 bets), live total $93.42, open-position drift $15.38.
- Path resolution survives the `Script/` subfolder hop: `REPO_ROOT = SCRIPT_DIR.parents[3]`, `default_out_dir` writes to `ACCOUNT_GRAPH_DIR / <M-D-YY>` (one level above `Script/`) instead of nesting.

### How to use

```bash
# Pull live portfolio first
python scripts/kalshi/risk_check.py --report positions

# Then build the chart (auto-named M-D-YY folder)
python docs/my-documents/account-graph/Script/build_account_graph.py $
  --cash 65.88 --portfolio 27.54 --positions 23

# Or via the skill — natural-language triggers route to snapshot mode
# "snapshot the account" / "regenerate the account graph" / "build the account chart"
```

### Files

`.claude/skills/edge-radar-analysis/SKILL.md`, `docs/CHANGELOG.md`. Local-only (gitignored): `docs/my-documents/account-graph/Script/build_account_graph.py`, `docs/my-documents/account-graph/README.md`, `docs/my-documents/account-graph/<M-D-YY>/account_graph.html`, `docs/my-documents/account-graph/<M-D-YY>/snapshot.json`.

---

## 2026-04-30 -- U2: Daily P&L Email Digest

### Why

The R12-R26 P1 wave shipped through 2026-04-29 leaves Priority 1 empty. Between monthly R12 calibration runs (the next attribution checkpoint) the user has no daily wake-up signal — the evening Weekly-Analysis runs Sun-only, and the existing morning emails are forward-looking execution reports, not retrospective P&L. U2 fills that gap: a morning digest that lands before the 5:05 AM same-day execute so the user sees what happened yesterday + what's still on the books before today's bets get placed.

### What landed

- **`scripts/kalshi/daily_summary.py`** — pure-functions report generator. Joins yesterday's settlements (rolling 24h window, robust to DST) with currently open trade-log positions, today's pending events, and an optional live Kalshi balance. Sections:
  - **Yesterday** — N settled, W-L, P&L, ROI, per-sport breakdown table, top-win + top-loss callouts
  - **Open Exposure** — count + $ at risk + per-sport split (excludes `closed_at`, `fill_status=resting`, `status=error`, zero-fill)
  - **Pending Today** — open positions whose game datetime parses to today's PST calendar day (via `parse_game_datetime` from `ticker_display`)
  - **Context** — live Kalshi balance + 7-day rolling line (WR, P&L, ROI, Brier; flips probability for NO-side bets so it's directly comparable to the calibration report)
- **Empty-day proof-of-life** — every section still renders with `_No settlements in window._` / `_No open positions._` placeholders. Matches `feedback_sameday_empty_emails`: empty digest = "the system ran" signal, never silent.
- **Architecture** — clean split between pure functions (`load_recent_settlements`, `aggregate_yesterday`, `aggregate_exposure`, `filter_pending_today`, `rolling_7d_context`, `render_report`) and I/O wrappers (`_fetch_balance` swallows all Kalshi-API failures gracefully, `--save` filesystem write). `build_report()` is the test-friendly composition entry point.
- **Window choice — rolling 24h not "yesterday in PST".** Robust to DST transitions, captures the 11 PM PST settler's late-night settlements, and survives wall-clock weirdness. Defaultable via `--hours` for ad-hoc runs.
- **Two new scheduled tasks** under `\Edge-Radar\`:
  - `Daily-Summary` (Daily 4:50 AM PT) — runs `scripts/schedulers/maintenance/daily_summary.bat` → `daily_summary.py --save`
  - `Email-Daily-Summary` (Daily 5:00 AM PT) — runs `scripts/custom/Shell-Scripts/Run-Reports/Daily-Summary-Report.sh` (mirrors the existing email pattern: `claude --dangerously-skip-permissions -p` subprocess + `agentmail` skill, dark-themed HTML, skip-on-missing-report)
- **Timing rationale** — 4:50 AM PT is the slot before `All-Sports-SameDay-Execution` (5:05 AM) so "Open Exposure" reflects overnight carry rather than mixing in today's new fills. The 10-min email buffer matches the `Weekly-Analysis` precedent (the underlying report is fast — no API fetches except a single optional balance call).

### Verification

- 26 new tests in `tests/test_daily_summary.py` covering: window-boundary inclusion (`>=` cutoff), malformed-timestamp skip, sort order, open-position filtering (closed/resting/error/zero-fill), per-sport aggregation math (NBA + MLB), pending-today PST filtering across day boundaries, 7-day rolling minimum-sample threshold (5-bet floor), balance present + missing rendering, full empty-day report renders all four sections.
- **381 tests passing** (was 355). Lint clean.
- End-to-end smoke confirmed: `.bat` ran cleanly, fetched live Kalshi balance ($66.85), wrote `reports/Performance/daily_summary_2026-04-30.md` with all four sections (empty-day proof-of-life intact). Real-data round-trip with `--hours 720` showed the 173 historical settlements aggregating correctly: NHL +72.9% ROI on 44 bets, MLB -5.1% on 39, NBA -14.8% on 17 (matches the canonical 30-day numbers).

### Follow-up

A one-shot Windows scheduled task `\Edge-Radar\U2-Review` will fire on **2026-05-14 07:00 PT** (`scripts/schedulers/maintenance/u2_2week_review.bat` → `u2_2week_review.py`). It scans `reports/Performance/daily_summary_*.md` for the prior 14 days to surface firing-reliability and section-coverage stats (which sections were consistently empty across the window — candidates for trimming), then spawns a `claude --dangerously-skip-permissions -p` subprocess to do a fresh-eyes code review of `daily_summary.py` + tests with explicit instructions to be opinionated about what to drop. Output combines local-verifiable signals + model findings + an operational checklist for the user to fill in (which sections they actually read each morning, any rendering issues, anything missing) into `reports/Performance/u2_2week_review_<date>.md`. Pure analysis — never modifies code or opens PRs. Migrated to local Windows Task Scheduler (consistent with the rest of `\Edge-Radar\` and the R8-Review precedent) instead of a remote claude.ai routine — the firing-reliability signal lives only on the user's machine since `reports/Performance/` is gitignored, so a remote agent literally couldn't see it. Original remote routine `trig_01Q6iNTVkob15MewHYS5CKYH` disabled but kept for record. Doc: `docs/my-documents/task-schedules/README.md` § 15.

### How to use

The script is invoked automatically by the scheduled task. To run manually:

```bash
# Default — yesterday's 24h window, save to reports/Performance/
.venv/Scripts/python.exe scripts/kalshi/daily_summary.py --save

# Custom window
.venv/Scripts/python.exe scripts/kalshi/daily_summary.py --hours 48 --save

# Skip the live Kalshi balance fetch (offline-safe)
.venv/Scripts/python.exe scripts/kalshi/daily_summary.py --no-bankroll --save

# Manual scheduled-task trigger
schtasks /run /tn "\Edge-Radar\Daily-Summary"
schtasks /run /tn "\Edge-Radar\Email-Daily-Summary"
```

### Files

`scripts/kalshi/daily_summary.py` (new), `tests/test_daily_summary.py` (new), `scripts/schedulers/maintenance/daily_summary.bat` (new, gitignored), `scripts/custom/Shell-Scripts/Run-Reports/Daily-Summary-Report.sh` (new, gitignored), `scripts/schedulers/maintenance/u2_2week_review.py` (new, gitignored — fires 2026-05-14), `scripts/schedulers/maintenance/u2_2week_review.bat` (new, gitignored), `docs/my-documents/task-schedules/README.md` (new entries 0a/0b/15 + install snippets, gitignored), `docs/my-documents/enhancements/ROADMAP.md` (gitignored), `CLAUDE.md`, `README.md`, `.claude/skills/edge-radar/SKILL.md`, `.claude/skills/edge-radar-analysis/SKILL.md`, `docs/CHANGELOG.md`.

---

## 2026-04-29 -- R8: Cross-Category Same-Event Dedup (Optional, Per-Sport)

### Why

The existing `dedup_correlated_brackets()` keys by `(event_key, category)`, which catches alt-line brackets within a category (3× Over lines on the same NBA game collapse to one) but treats ML + Total + Spread on the same game as 3 distinct bets. F11 (14-day review) flagged 12 matchups bet ≥2× in 14d, several same-day on different categories — when an NBA game blows out, the ML + Spread + Total all win or lose together, so stacking three categories adds correlation, not diversification. Cross-category correlation is sport-dependent (NHL low-scoring → ML and Total weakly correlated; NBA blowouts → all three move together), so this needs to be opt-in per sport rather than a global flip.

### What landed

- **`dedup_correlated_brackets()`** in `scripts/kalshi/kalshi_executor.py` now accepts `cross_category_sports: set[str] | None`. When an opportunity's detected sport is in the set, the dedup key becomes `("_xcat", sport, game_id)` where `game_id` is the date+teams middle segment of the ticker (e.g. `26APR24SASPOR` from `KXNBATOTAL-26APR24SASPOR-208`). All categories on the same game collapse to the highest-composite row. Futures pass-through (R21) is checked first and immune.
- **Why a separate game_id**: `_event_key()` strips only the trailing hyphen segment, so `KXNBAGAME-…` and `KXNBATOTAL-…` produce different event keys (different prefixes). Splitting on `-` and taking `parts[1]` is identical across categories for the same game.
- **Config**: new `GateThresholds.cross_category_dedup: bool` (env `CROSS_CATEGORY_DEDUP=false` default) + `PerSportOverrides.cross_category_dedup: dict[str, bool]` (env `CROSS_CATEGORY_DEDUP_<SPORT>=true|false`) + `Config.cross_category_dedup_for(sport)` helper. Mirrors the R9 series-dedup pattern; per-sport `false` overrides global `true` in either direction.
- **Wiring**: module-level `CROSS_CATEGORY_DEDUP` and `_PER_SPORT_CROSS_CATEGORY_DEDUP` constants in `kalshi_executor.py` (test-patchable, mirrors `_PER_SPORT_SERIES_DEDUP`); `_cross_category_sports()` builds the active set on each call. `execute_pipeline` passes the set to `dedup_correlated_brackets` and surfaces it in the dedup banner when non-empty: `Deduped correlated brackets: 12 -> 8 opportunities (cross-category: ['nba', 'nfl'])`.
- **Why default OFF**: lets the user A/B test per sport against live calibration data once enough cross-category bets accumulate. Existing per-event cap (Gate 6, `MAX_PER_EVENT=2`) already provides a soft ceiling, so switching this off doesn't leave the system unbounded.
- **`.env.example`**: documents `CROSS_CATEGORY_DEDUP` in the gate section + 8 commented `CROSS_CATEGORY_DEDUP_<SPORT>` lines in the per-sport-overrides section. **CLAUDE.md**: added to Risk Limits block.

### Verification

- 4 new tests in `tests/test_risk_gates.py::TestDedupCorrelatedBrackets`: off-default preserves pre-R8 behavior (regression guard); on collapses 3 categories to highest-composite; per-sport scope (NBA collapses but MLB on same scan stays uncollapsed); futures pass-through preserved even when their sport is opted in.
- 4 new tests in `tests/test_config.py::TestPerSportOverrides`: default off; global on cascades to all sports; per-sport-only override; per-sport `false` overrides global `true`.
- **355 tests passing** (was 347). Lint clean (config-centralization guard).
- One initial round of tests caught a real bug: my first cut keyed cross-category by `_event_key`, which doesn't strip the category prefix from the ticker — so the three categories never collided. The game-id-segment approach fixes it; the failure was visible in test output before any user impact.

### How to use

Default behavior is unchanged — the system keeps ML+Total+Spread on the same game as 3 independent bets. To opt in:

```env
# Enable for every sport
CROSS_CATEGORY_DEDUP=true

# OR enable for specific sports only
CROSS_CATEGORY_DEDUP_NBA=true
CROSS_CATEGORY_DEDUP_NCAAB=true

# OR enable globally but exclude one sport
CROSS_CATEGORY_DEDUP=true
CROSS_CATEGORY_DEDUP_NHL=false
```

When active, the dedup banner prints which sports are in the cross-category set so it's visible at run time.

### Files

`app/config.py`, `scripts/kalshi/kalshi_executor.py`, `tests/test_risk_gates.py`, `tests/test_config.py`, `.env.example`, `CLAUDE.md`, `docs/my-documents/enhancements/ROADMAP.md`, `scripts/schedulers/maintenance/r8_cross_category_review.py` (new), `scripts/schedulers/maintenance/r8_review.bat` (new), `docs/my-documents/task-schedules/README.md`.

### Follow-up

A one-shot Windows scheduled task `\Edge-Radar\R8-Review` will fire on **2026-05-29 06:00 PT** (`scripts/schedulers/maintenance/r8_review.bat` → `r8_cross_category_review.py`). It slices `data/history/kalshi_settlements.json` into ML/Total/Spread same-game cohorts per sport, simulates the R8-on outcome (highest-edge bet kept — `composite_score` isn't on settlement records yet, blocked on R11), and writes a recommendation report to `reports/Performance/R8_cross_category_review_<date>.md` with FLIP ON / FLIP OFF / NEED MORE DATA per sport plus a copy-pasteable `.env` snippet for the FLIP ON sports. Smoke-run on 2026-04-29 against the live 178-bet settlement file produced "NEED MORE DATA: 5" — too thin per sport (NBA 2 cohorts, NCAAB 4, NHL 3) to recommend either way; the May 29 run will have ~30 more days of cohorts to evaluate. Migrated to local Windows Task Scheduler (consistent with the rest of `\Edge-Radar\`) instead of a remote claude.ai routine — deterministic, fast, and same management UX as `Calibration` / `Backtest` / `Weekly-Analysis`. Doc: `docs/my-documents/task-schedules/README.md` § 14. R10 (category-weighted composite score) is the next P2 item after this measurement.

---

## 2026-04-29 -- R26: File-Backed Scan Cache (Row-Order Lock for `--pick`)

### Why

User-reported bug, 2026-04-29: ran a sports scan with `--exclude-open` that returned 5 games, then ran the same scan with `--pick '1,3,4,5' --execute` (without `--exclude-open`). The execute call did a fresh live scan, the row order shifted on price/score drift between the two invocations, and the wrong bets were placed against rows 1/3/4/5 of a different ranking. Two compounding causes: every `scan.py` invocation runs `scan_all_markets()` against live Kalshi prices and Odds API data and re-sorts by `composite_score`; small drifts reorder rows. And dropping `--exclude-open` on the second call changes the row universe outright. Until R26, the `--pick` flag was a foot-gun any time the user's two invocations diverged — even seconds apart, even with identical args.

### What landed

- **`scripts/shared/scan_cache.py`** (new): `store(fingerprint, sized_orders, bankroll)`, `load() -> {fingerprint, saved_at, age_seconds, bankroll_at_scan, rows}`, `clear()`, `fingerprints_match(saved, current) -> (ok, diffs)`. Single file at `data/cache/last_scan.json`, latest preview only. Serializes `SizedOrder` (incl. embedded `Opportunity`) so the executor's existing order-placement loop rehydrates without conditional branches. Silent-on-error throughout — corrupt file = miss, never an exception. Mirrors `scripts/shared/odds_cache.py` precedent.
- **`ScanCacheConfig`** in `app/config.py`: `SCAN_CACHE_TTL_SECONDS=600` (10 min default — long enough to read the preview table and pick rows, short enough that a user returning hours later gets a fresh scan) and `SCAN_CACHE_ENABLED=true`. `validate()` rejects negative TTL.
- **`execute_pipeline` wiring** in `kalshi_executor.py`: added `fingerprint`, `cached_rows`, `cache_age_seconds` params. The dedup / sizing / bet-ratio-cap / budget-cap block is now wrapped in `if cached_rows is None:` so the replay path bypasses it entirely — those decisions are locked from the original preview. On the fresh-scan path, the rendered preview rows are persisted right after `console.print(table)`.
- **CLI wiring** in `edge_detector.py main()`: new `--rescan` flag for opt-out. When `args.execute` AND (`args.pick` OR `args.ticker`) AND not `args.rescan`, attempt cache load before scanning. Fingerprint = `{scanner, filter, category, date, exclude_open, min_edge, top}` — the args that determine row identity. `--unit-size`, `--max-bets`, `--budget`, `--min-bets` deliberately excluded since those reshape sizing/caps but the rows in `cached_rows` were already sized under the original args.
- **Mismatch handling**: on fingerprint mismatch, prints the differing keys (e.g. `exclude_open: cached=True, now=False`) and rescans live rather than silently executing the wrong universe. The user's exact bug pattern from the original report.
- **Banner on hit**: `Replaying cached preview (N rows, age Xs).` + `Pass --rescan to force a fresh scan instead.`
- **`.env.example`** documents both knobs in section 6.

### Verification

- 17 new tests in `tests/test_scan_cache.py`: round-trip preserves SizedOrder + Opportunity fields; age-is-recent; miss-after-TTL; disabled-via-zero-ttl; disabled-via-env-flag; corrupted-file-silently-misses; missing-file; wrong-version; missing-required-fields; store-disabled-does-not-write; creates-parent-dir; clear-removes-file; clear-when-missing; fingerprints identical-match / value-mismatch / extra-key / exclude-open-change-mismatch (the last specifically reproduces the user's bug case).
- **347 tests passing** (was 330). Lint clean (config-centralization guard).
- Live offline round-trip smoke: `store()` writes `data/cache/last_scan.json`, `load()` rehydrates with `age_seconds=0`, `fingerprints_match` returns `(True, [])`. File cleared after smoke.
- Live `get_config()` smoke: `ScanCacheConfig(ttl_seconds=600, enabled=True)` loads from environment as expected.

### How to use

The default workflow now Just Works:

```
python scripts/scan.py sports --filter mlb --exclude-open      # writes cache
python scripts/scan.py sports --filter mlb --exclude-open --pick '1,3,4,5' --execute   # replays cache
```

The second call replays the same row order the user saw, regardless of any live-data drift between the two invocations. To force a live rescan: append `--rescan`. To disable the cache globally: set `SCAN_CACHE_ENABLED=false` or `SCAN_CACHE_TTL_SECONDS=0` in `.env`.

### Files

`app/config.py`, `scripts/shared/scan_cache.py` (new), `scripts/kalshi/kalshi_executor.py`, `scripts/kalshi/edge_detector.py`, `tests/test_scan_cache.py` (new), `.env.example`, `CLAUDE.md`, `docs/my-documents/enhancements/ROADMAP.md`.

### Streamlit UX cleanup (2026-04-29)

Three dashboard polish fixes shipped the same day as R26:

1. **Preview/Execute results table now shows the matchup.** Previously columns were `Ticker, Side, Contracts, Price, Cost, Edge, Status` — the raw Kalshi ticker was the only identifier. The user couldn't tell which scan-table row a preview row corresponded to without parsing the ticker. Now mirrors the scan-results table via the same `format_bet_label / format_pick_label / sport_from_ticker / parse_game_datetime` helpers from `ticker_display`. Final columns: `Ticker | Sport | Bet | Type | Pick | When | Side | Contracts | Price | Cost | Edge | Status`. Files: `webapp/views/scan_page.py`.
2. **Hide Streamlit's "Press Enter to apply" hint on free-standing inputs.** The frontend renders the hint next to every `st.text_input` / `st.number_input`. On the scan page it cluttered the dense Execution Parameters row. Added CSS rules in `webapp/theme.py` with `html body` specificity prefix (Streamlit 1.56 ships its own `!important` rules at the same specificity, so the prefix is required) targeting `[data-testid="InputInstructions"]` + `[data-testid="stWidgetInstructions"]` plus structural sibling-of-baseweb-input fallbacks. Belt-and-suspenders `visibility:hidden / height:0 / overflow:hidden` so even if `display:none` loses, the element doesn't take up layout space. Visible state of the input itself (focus ring, ✓/✗ icons) is preserved.
3. **Auth form: explicit submit instead of auto-submit-on-blur.** The original `check_password()` used a bare `st.text_input` and ran `if pw == correct_pw: authenticate` on every rerun. Streamlit reruns on blur/tab-out, so typing the password then clicking away would auto-authenticate without an explicit submit click — and the "Press Enter to apply" hint would render next to the password field after typing (DOM screenshot 2026-04-29 confirmed the hint appears in a portal outside the `stTextInput` subtree, which is why the CSS rule from fix #2 didn't catch it). Wrapped the input in `st.form("auth_form")` with an explicit `st.form_submit_button("Sign in")`. Streamlit suppresses the per-widget hint inside forms (the form's submit button IS the apply trigger), so the hint goes away as a side effect. Submission now requires either clicking **Sign in** or pressing Enter while focused inside the form. Files: `webapp/app.py`.

Files: `webapp/views/scan_page.py`, `webapp/theme.py`, `webapp/app.py`, `docs/my-documents/web-app/USAGE.md`, `docs/my-documents/web-app/SETUP.md`, `docs/my-documents/web-app/ARCHITECTURE.md`, `docs/web-app/LOCAL.md`. **347 tests still passing.**

### R26 follow-up — UX fixes from first live run (2026-04-29)

User ran the new flow on a real session and surfaced two cosmetic-but-real issues:

1. **Misleading post-execute cost line.** The "Total cost: $9.40 of $70.99 available" line was computed against the full preview menu and printed before the `--pick` filter. Three rows actually placed (= $1.85 stakes), so the user reasonably thought $9.40 had gone out. Fix: after `--pick`/`--ticker` filtering, print `Placing N orders, total cost: $X.XX (selected from M-row menu totaling $Y.YY)`. The pre-filter `Total cost` line stays — it describes the menu — but the post-filter line is now the truthful one. Also fixes a latent crash on the cache-replay path: the old summary line referenced `len(approved)`, which doesn't exist when rows came from cache.
2. **Quiet fingerprint-mismatch warning.** The original mismatch message was a single dim-yellow line. Easy to miss when scrolling past a long Kalshi/Odds API fetch log. Fix: bold red boxed banner with a one-line explanation that `--pick` row numbers will reference a NEW ranking, each differing arg printed in bold red, and a bold yellow trailer naming the recovery options (`re-run preview with same args`, or `--rescan` to silence intentionally).

Files: `scripts/kalshi/kalshi_executor.py`, `scripts/kalshi/edge_detector.py`, `.claude/skills/edge-radar/SKILL.md`, `docs/scripts/edge_detector.md`. **347 tests still passing.**

---

## 2026-04-28 -- R24b: File-Backed Odds API Cache

### Why

F31 (2026-04-24): one Odds API key dropped from 175 → 0 remaining in five minutes during a normal session. The dominant cause is that every `scan.py` invocation starts with a fresh in-process `_odds_cache` / `_outrights_cache`. Running the same scan twice — or the dashboard re-rendering with a tweaked filter — refetches all 18 sport keys from scratch. R23 fixed the persistent quota counter; R24a fixed the dashboard's lack of `@st.cache_data`; R24b is the structural piece: persist the actual response payloads across processes so back-to-back invocations within a 5-minute window don't burn quota.

### What landed

- **`scripts/shared/odds_cache.py`** (new): `load(sport_key, markets, ttl_seconds)`, `store(sport_key, markets, events)`, `clear()`. Files live at `data/cache/odds/<sport_key>__<markets>.json`. Comma-sanitized filenames (`h2h,spreads,totals` → `h2h_spreads_totals`); the original markets string is preserved inside the JSON body. Silent-on-error throughout — corrupt file = miss, never an exception. Mirrors the existing `data/cache/odds_api_quota.json` precedent in `scripts/shared/odds_api.py`.
- **`OddsCacheConfig`** in `app/config.py` with `ODDS_CACHE_TTL_SECONDS` (default 300) and `ODDS_CACHE_ENABLED` (default true). `validate()` rejects negative TTL.
- **Two-tier cache wiring** in `edge_detector.fetch_odds_api()` and `futures_edge.fetch_outrights()`: in-process dict in front of the file layer. The in-process dict stays so existing tests calling `_odds_cache.clear()` still work; the file layer survives across processes. Hits log `Odds API file cache hit for X (age Ns, M events)` so cache age is visible in scan output.
- **`.env.example`** documents both knobs in section 6 (System).

### Verification

- 10 new tests in `tests/test_odds_cache.py`: hit-within-TTL, miss-after-TTL, disabled-via-zero-ttl, corrupted-file-silently-misses, missing-file, missing-required-fields, store round-trip, store-creates-parent-dir, clear-removes-all, clear-when-dir-missing.
- Updated the autouse fixture in `TestFetchOddsApiKeyRotation` (`tests/test_edge_detection.py`) to redirect `odds_cache._CACHE_DIR` to a tmpdir alongside the existing quota-cache redirect — otherwise the rotation tests sharing one process would pick up each other's stored responses.
- **330 tests passing** (was 320). Lint clean.
- Offline round-trip smoke (mocked HTTP, fake key): call 1 hits HTTP and writes the cache file; clearing only the in-process dict and calling again returns identical events with 0 HTTP calls.

### Files

`app/config.py`, `scripts/shared/odds_cache.py` (new), `scripts/kalshi/edge_detector.py`, `scripts/kalshi/futures_edge.py`, `tests/test_odds_cache.py` (new), `tests/test_edge_detection.py`, `.env.example`, `docs/my-documents/enhancements/ROADMAP.md`.

---

## 2026-04-27 -- R9: Per-Sport `SERIES_DEDUP_HOURS`

### Why

F12 (14-day review): a NYM/LAD MLB matchup was bet on Apr 14 and again on Apr 16 — about 49 hours apart, just outside the single 48h global `SERIES_DEDUP_HOURS` window. Both bets landed (every other gate passed) and both lost. Series-dedup is the gate that catches "same model wrong twice on the same matchup," and the global window was tight enough to leak adjacent-day MLB and NHL repeats. NBA matchups against the same opponent within 48h are rare outside the playoffs, so the issue is sport-shaped — not a global threshold problem.

### What landed

- **`PerSportOverrides.series_dedup_hours: dict[str, int]`** in `app/config.py` — populated from `SERIES_DEDUP_HOURS_<SPORT>` env vars. Same pattern as `MIN_EDGE_THRESHOLD_<SPORT>`.
- **`recent_matchups_from_log()`** extended with a `per_sport_hours` keyword arg. Each sport uses its own cutoff; sports without an override fall back to the global `hours`. A per-sport `0` opts that sport out, even when the global is non-zero. A global `0` with a per-sport override re-enables the gate just for the listed sport — both directions tested.
- **Gate 7 in `size_order()`** now resolves the candidate's per-sport window and reports the actual sport-specific window in the rejection message: `series_dedup (matchup NYMLAD bet within 72h)` instead of the old fixed `48h`.
- **Module-level `_PER_SPORT_SERIES_DEDUP`** in `kalshi_executor.py` — tests can patch it directly the same way `_PER_SPORT_MIN_EDGE` is patched.
- **Live `.env`:** `SERIES_DEDUP_HOURS_MLB=72` and `SERIES_DEDUP_HOURS_NHL=72`. NBA leaves the global default. 72h covers any 3-game series start-to-finish regardless of game-time skew.

### Verification

- 9 new regression tests in `test_risk_gates.py` (6 set-construction edge cases including the exact F12 49h scenario, plus 3 gate-rejection-message cases).
- 4 new config-layer tests in `test_config.py` for the new loader.
- Pre-existing `test_disabled_when_hours_zero` updated to also clear `_PER_SPORT_SERIES_DEDUP` since per-sport overrides can now re-enable the gate independently of the global.
- **320 tests passing** (was 307). Lint clean.
- Live config smoke: `_PER_SPORT_SERIES_DEDUP={'mlb': 72, 'nhl': 72}` loads correctly.

### Caveat

Gate 7 reads from `kalshi_trades.json`. After R5, that file is currently the test stub R5 surfaced — empty of real history. The gate will start protecting against new repeats as bets accumulate going forward; R5 made the missing-history visible and R9 ensures the gate catches the right pattern when history exists.

### Files

`app/config.py`, `scripts/kalshi/kalshi_executor.py`, `webapp/services.py`, `tests/test_risk_gates.py`, `tests/test_config.py`, `.env`, `.env.example`, `CLAUDE.md`, `README.md`, `docs/ARCHITECTURE.md`, `docs/setup/SETUP_GUIDE.md`, `docs/web-app/CLOUD.md`, `docs/scripts/kalshi_executor.md`, `.claude/skills/edge-radar/SKILL.md`, `.claude/html/index.html`.

---

## 2026-04-27 -- R5: Settlement-Schema Fix + Reconciliation Report

### Why

F8 (14-day review) said "10/76 14-day settlements match a trade-log entry." Investigation today revealed the actual state was worse: the production trade log got wiped at some point, leaving a single test stub from this morning and **178 settlement entries with zero `trade_id` overlap** to anything in the trade log. Beyond the orphan problem, even when the two files were both healthy the settler only carried forward a hand-picked subset of trade-side fields — missing `composite_score`, `risk_approval`, `bankroll_pct`, `closing_price`, `clv`, etc. — so calibration analytics couldn't slice settlements by score bucket or risk-approval flag without re-joining to a trade log that may not exist.

### What landed

- **`build_settlement_record()` helper** in `kalshi_settler.py` — extracted from the inline `settlement_log.append({...})` so the schema is testable. Settlement record extended from 16 → 27 fields. New fields: `order_id`, `title`, `category`, `edge_source`, `closing_price`, `clv` (settler already computes these but used to discard them), `composite_score`, `risk_approval`, `bankroll_pct`, `unit_size`, `fill_status`. Pre-existing fields unchanged. After this, every future settlement is fully self-describing for calibration without joining to the trade log.
- **`--report reconciliation` mode** in `risk_check.py` — prints trade-log/settlement counts, `trade_id` overlap %, orphaned-settlement window dates, and a field-coverage matrix per R5-added field. Surfaces the join health at every session start.
- **`data/history/README.md`** — documents the two-file lifecycle and the pre-R5 historical-orphan rationale (no backfill: the missing fields don't exist anywhere on disk and synthesizing them would be fabricating data). Added a `.gitignore` exception so the README ships with the repo while runtime state stays gitignored.
- **+10 regression tests** in `tests/test_reconciliation.py`: 5 schema-coverage + 5 report-rendering edge cases (empty / all-orphan / clean-join / mixed cohort / open-trade counting).

### Verification

- **307 tests passing** (was 297). Config lint clean.
- Live `--report reconciliation` against the user's data renders cleanly: 178 orphans (oldest 2026-03-22, newest 2026-04-27), 0% R5-field coverage. Expected pre-R5 baseline.
- The R15 normalizer in `model_calibration.py` continues to work (R5 only adds fields, never removes).

### What this does NOT solve

The 178 historical orphan settlements stay orphaned. Their trade-side context isn't recoverable. R5 stops the bleed and makes the gap measurable; A3 (DB migration) can now import a clean schema without compounding the data debt.

### Files

`scripts/kalshi/kalshi_settler.py`, `scripts/kalshi/risk_check.py`, `tests/test_reconciliation.py`, `data/history/README.md`, `.gitignore`, `docs/ARCHITECTURE.md`.

---

## 2026-04-27 -- Polymarket integration removed

### Why

Zero historical use evidenced. No `data/polymarket/`, no `reports/Polymarket/`, no scheduled tasks ever ran the polymarket subcommand. Prediction-market betting is gated off by default (`ALLOW_PREDICTION_BETS=false`, R25), and the Polymarket cross-reference branch in `prediction_scanner.py` was carrying ~350 lines of decision logic for a code path nothing exercised. Decision: full delete now, recoverable via git history if the use case revives.

### Code removed

- **Deleted:** `scripts/polymarket/` (entire directory — `__init__.py` + 872-line `polymarket_edge.py`)
- **Deleted:** `.claude/skills/polymarket/` (SKILL.md + 9 reference files)
- **Deleted:** `prompts/polymarket/` (`cross-reference-scan.md`, `crypto-arbitrage.md`)
- **Deleted:** `docs/scripts/polymarket_edge.md`
- **Stripped from `scripts/scan.py`:** `polymarket` subcommand registry entry; `poly`/`xref` aliases; example/help-text mentions
- **Stripped from `scripts/prediction/prediction_scanner.py`:** `polymarket_edge` import block; `cross_ref` parameter on `scan_prediction_markets`; `polymarket`/`poly`/`xref` filter shortcuts; the standalone xref scan branch + the per-opportunity Polymarket enrichment loop (~70 lines); `--cross-ref` CLI flag; `is_poly_filter` dispatch logic in `main()`
- **Stripped from `scripts/kalshi/fetch_market_data.py`:** `POLYMARKET_URL` constant; `fetch_polymarket_markets()`; `fetch_polymarket_orderbook()`; `--source polymarket` choice; default flipped from `polymarket` to `kalshi`
- **Stripped from `scripts/shared/paths.py`:** `POLYMARKET_DIR` constant + sys.path entry
- **Stripped from `scripts/shared/report_writer.py`:** `polymarket` key in `REPORT_DIRS`
- **Stripped from `scripts/schedulers/automation/telegram_bot.py`:** `--cross-ref` flag in `/scan prediction`
- **Stripped from `webapp/services.py`:** `scripts/polymarket` from sys.path; `cross_ref` parameter on `run_scan`; `cross_ref` plumbed through to `scan_prediction_markets`
- **Stripped from `webapp/views/scan_page.py`:** `cross_ref` defaults; "Cross-Ref Polymarket" checkbox; `cross_ref` in favorite save state and the service-layer call
- **Stripped from `Makefile`:** `scan-polymarket` target; `scan-polymarket` from `scan-all`; help-text and `.PHONY` entries
- **Stripped from `requirements.txt`:** commented `py-clob-client` line
- **Stripped from `pyproject.toml`:** `scripts/polymarket` from pytest `pythonpath`

### Docs updated

- `CLAUDE.md` — removed Polymarket from "Planned" section; removed `polymarket/` from the project tree; removed `polymarket-py` from the key-libraries list
- `README.md` — dropped "Polymarket cross-ref" bullet from supported markets, "Polymarket Cross-Reference" section, polymarket dir from tree, `polymarket-py` mention in description, "Polymarket" data-sources row
- `docs/ARCHITECTURE.md` — removed Polymarket cross-market row from prediction model table
- `docs/SCRIPTS_REFERENCE.md` — removed polymarket from goal table, scanner registry, alias resolution mermaid + alias table, scanner subgraph, `--cross-ref` tip, examples; flipped `fetch_market_data --source` default from polymarket to kalshi
- `docs/setup/SETUP_GUIDE.md` — dropped Polymarket from free-API list, data-sources table, external-docs links
- `docs/web-app/LOCAL.md` — removed `scripts/polymarket/*.py` from architecture diagram, Cross-Ref filter row, Polymarket-via-CLI note
- `docs/setup/mcp-servers.md` (formerly `docs/mcp-config/mcp-servers.md`) — removed `POLYMARKET_PRIVATE_KEY` env line, polymarket-mcp future-integration row, Polymarket fetch examples
- `docs/scripts/prediction_scanner.md` — full rewrite without `--cross-ref` references
- `.claude/skills/edge-radar/SKILL.md` — multiple sections cleaned: description frontmatter, flag table, scanner table, makefile shortcuts, polymarket subsection, scan-and-bet block, routing examples
- `prompts/predictions/full-prediction-execute.md` — full rewrite (Polymarket cross-ref was central)
- `prompts/predictions/{execute-predictions,crypto-edge-scan,scan-all-predictions}.md` — removed cross-ref blocks
- `prompts/portfolio/morning-routine.md` — removed step 7 + cross-market brief item

### Known stale (not edited — flagging for future refresh)

- `.claude/images/diagrams/**/*.{mmd,svg}` — data-flow diagrams still depict the Polymarket node; will need regeneration if/when diagrams are next refreshed.
- `.claude/html/{index.html,index2.html,dataflow.html}` and `docs/my-documents/HTML-Interactive-Pages/Edge-Radar-Only/index2-*.html` — interactive visualizations include Polymarket; same status as the Mermaid diagrams.
- `docs/my-documents/temp/archive/*` and `docs/my-documents/repo-analysis/edge_radar_repository_analysis_2026-04-22.md` — point-in-time snapshots; intentionally left as-is to preserve the historical record.

### Validation

- `pytest tests/` passing (no tests referenced polymarket).
- `python scripts/scan.py --help` no longer lists polymarket.
- `python scripts/scan.py prediction --help` no longer carries `--cross-ref`.

### Recovery path

Polymarket integration can be restored from `git show <commit-before-removal>:scripts/polymarket/polymarket_edge.py` — but if/when revisited, treat as a fresh design (Polymarket Gamma/CLOB APIs evolve, a current-state implementation will likely be more useful than reverting).

---

## 2026-04-25 -- Config centralization Phase 3 (lint guard against regression)

### `scripts/lint/check_config_centralization.py`

Replaces the original "simple grep" idea from the spec with a small Python script — necessary because the rule needs nuance the raw grep can't express.

**What it does:**
- Walks `app/`, `scripts/`, `webapp/` for `os.getenv` / `os.environ`.
- Excludes `app/config.py` (the single source of truth), `scripts/custom/` (user automation), and `scripts/lint/` itself (this script names the forbidden strings to communicate the rule).
- Skips comment-only lines.
- Skips lines tagged `# config-bootstrap` — reserved for the 4 Streamlit secrets-bootstrap lines in `webapp/services.py` (lines 69, 71, 75, 77 now carry the annotation inline).
- Exits 1 on any violation, 0 otherwise. Output names file, line, content, and tells the contributor what to do.

### Wired into automation

- `make lint-config` Makefile target.
- `.pre-commit-config.yaml` local hook with `pass_filenames: false` and `always_run: true` so the lint sees the whole tree, not just staged files (a sneaky violation in an unstaged file would otherwise slip through).

### Unit tests — 5 new tests in `tests/test_lint_config_centralization.py`

1. The current production codebase passes the lint cleanly.
2. A regression — adding `os.getenv("FOO")` to a previously clean file — is detected.
3. The `# config-bootstrap` annotation correctly suppresses violations.
4. Comment-only lines mentioning `os.getenv` textually are ignored.
5. `app/config.py` is unconditionally excluded.

**Final test count: 297 passing** (292 from earlier phases + 5 lint tests). Production-code `os.getenv` reads outside `app/config.py`: 0.

---

## 2026-04-25 -- Config centralization Phase 2 — all 8 script groups migrated

### What changed

Mechanical migration of every `os.getenv` config read across the production codebase to `app.config.get_config()`. Per-step breakdown:

| Step | Files | Calls removed |
|:----:|:------|:-------------:|
| 1 | `scripts/doctor.py` | 9 |
| 2 | `scripts/kalshi/risk_check.py` | 5 |
| 3 | `scripts/kalshi/kalshi_client.py` | 8 |
| 4+6 | `scripts/kalshi/edge_detector.py`, `scripts/kalshi/fetch_odds.py` | 1 + 2 |
| 5 | `scripts/kalshi/kalshi_executor.py` | 23 |
| 7 | `prediction_scanner.py`, `backtester.py`, `logging_setup.py`, `odds_api.py`, `fetch_market_data.py`, `telegram_bot.py` | 11 |
| 8 | `webapp/services.py` (6 reads — bootstrap retained) | 6 |

**Final tally: 65 reads removed, 0 outside `app/config.py`.** The 4 `os.environ` writes in the `webapp/services.py` Streamlit secrets bootstrap are deliberately retained — they're the input side of cfg, not config consumption.

### Notable per-file details

- **`doctor.py`:** display normalization is the only user-visible change (`UNIT_SIZE=.50` previously rendered as `$.50`; now `$0.50` via explicit `:.2f` format). Numeric values reaching every gate are byte-identical.
- **`risk_check.py`:** dropped a dead `MIN_EDGE` constant that no caller imported.
- **`kalshi_client.py`:** Streamlit-secrets timing preserved — all reads happen at instantiation, not import. The `st.secrets["kalshi"]["private_key"]` fallback in `_resolve_key_content` is kept as a backup for direct Streamlit-app use that bypasses `services.py`. Phase 1 default for `KalshiCredentials.private_key_path` tweaked from `"keys/live/kalshi_private.key"` to `""` to mirror the original `os.getenv("KALSHI_PRIVATE_KEY_PATH", "")` runtime default; preserves byte-identical "credentials not configured" error path when env is unset. `.env.example` unchanged.
- **`kalshi_executor.py`:** all 21 module-level risk constants and the per-sport edge-override dict source from `_cfg = get_config()`. Constants stay as plain mutable globals because `tests/test_risk_gates.py` mutates them directly (`kalshi_executor.MAX_OPEN_POSITIONS = 10`) — only the *initial source* changed. Two in-function `DRY_RUN` reads (resting-order janitor + execute-table title) use `get_config().system.dry_run` against the memoized cache.
- **`fetch_odds.py`, `fetch_market_data.py`, `telegram_bot.py`:** API-key constants use `cfg.X or None` to preserve `None`-on-unset semantics from the original `os.getenv("X")` — matters where credentials get spliced into HTTP headers and URL f-strings (`None` and `""` render differently).
- **`logging_setup.py`:** `from app.config import get_config` placed *after* `load_dotenv()` so `.env` values are in `os.environ` before the first cfg read.
- **`webapp/services.py`:** module-level constants (imported by `views/scan_page.py` and `views/portfolio_page.py`) sourced from `_cfg = get_config()`. `reset_config()` defensive call added between the secrets bootstrap and downstream imports — explicit contract that any code mutating `os.environ` after potentially priming the cache uses this seam. Bug found and fixed: Streamlit's `webapp/app.py` puts `webapp/` on `sys.path[0]`, which made `from app.config import …` resolve to `webapp/app.py` (a file) instead of the `app/` package. Resolved by explicitly inserting `PROJECT_ROOT` at `sys.path[0]` inside `services.py` after the script-subdir loop. Documented inline.

### Infra side-fix

`scripts/shared/paths.py` and `.venv/Lib/site-packages/edge_radar.pth` both now prepend `PROJECT_ROOT` to `sys.path` so `from app.config import get_config` resolves in any script that imports `paths`. Without this, every migrated script would need its own ad-hoc `sys.path.insert(0, str(PROJECT_ROOT))`.

### Out of scope (flagged, not migrated)

- `scripts/custom/Python/send_daily_email.py` uses `os.environ["AGENTMAIL_API_KEY"]` — user-automation script, knob not documented in `.env.example` or core docs. Migrating it would add a non-core knob to `app/config.py`, violating the "no new knobs" non-goal.

All 292 tests still pass after the migration.

---

## 2026-04-25 -- Config centralization Phase 1 (refactor scaffolding)

### `app/config.py` — typed config module landed (no script migrations yet)

- **Why:** Audit found 75 `os.getenv` calls across 14 files, with `MIN_EDGE_THRESHOLD` read in 5 places using two type styles (string `"0.03"` vs float `0.03`) and `DRY_RUN` coerced inconsistently. Tracked under `docs/my-documents/enhancements/CONFIG_CENTRALIZATION.md`.
- **What landed:** `app/config.py` with 10 frozen dataclasses (Kalshi creds, Kalshi-prod creds, OddsApi creds, Alpaca creds, Telegram creds, RiskLimits, GateThresholds, KellyConfig, PerSportOverrides, System). Each has `from_env()` for one-shot coercion; aggregate `Config.from_env()` runs `validate()`. Memoized via `get_config()` / `reset_config()`. 32 unit tests in `tests/test_config.py`.
- **What did NOT change:** No existing script touched. `os.getenv` count unchanged. `.env.example` unchanged. No behavior change of any kind. Phase 2 (mechanical migration of 8 script groups) is a separate set of commits.
- **Discrepancies flagged for a future doc-reconciliation PR (not fixed here):** `MAX_OPEN_POSITIONS` is `10` in code/CLAUDE.md but `50` in `.env.example`; `MAX_PER_EVENT` is `2` in code/`.env.example` but `3` in CLAUDE.md. Phase 1 followed code as source of truth.

---

## 2026-04-24 (PM) -- Scanner Parity, Futures Bug Hunt, Prediction-Market Audit (R17, R18, R20, R21, R22, R23, R24a, R25)

### R17. Scanner flag parity (`--budget`, `--report-dir`)
- **Problem:** User tried `futures_edge.py scan --exclude-open --budget 5%` and discovered that `--budget` and `--report-dir` were sports-only. Futures / prediction / polymarket CLIs didn't accept them, and even if they had, `execute_pipeline(budget=…)` wasn't threaded through. Risk-gate logic itself was already uniform (all four call `execute_pipeline`).
- **Fix:** Extracted `parse_budget_arg()` into `kalshi_executor.py` so all four scanners share the same `"10%"` / `"15"` / `"0.15"` / `"150"` parsing contract. Added `--budget` + `--report-dir` to futures / prediction / polymarket argparse; wired each to `execute_pipeline(budget=…)` and `save_scan_report(output_dir=…)`. Sports scanner's inline 7-line budget block replaced with the shared helper.

### R21. `dedup_correlated_brackets` now passes futures through unchanged
- **Problem:** A futures scan of 20 opportunities was being collapsed to 2 before risk gates even ran. `dedup_correlated_brackets` grouped by `(event_key, category)`; for championship futures `KXNBA-26-LAL` / `KXNBA-26-BOS` / `KXNBA-26-OKC` all share event key `KXNBA-26`, so dedup saw 16+ team outcomes as one "alt-line bracket" and kept only the top composite score.
- **Fix:** When `opp.category == "futures"`, use the full ticker as the dedup key so each outcome survives. Correct for alt-line brackets ("Over 221.5" / "Over 224.5") that are genuinely correlated, wrong for futures where each team is a distinct independent bet. Concentration still bounded by Gate 6 (`MAX_PER_EVENT=2`).

### R22. `FUTURES_MAP` prefix-collision + semantic-mismatch double bug
- **Problem:** Futures scan surfacing "+30-75% edge" on basically every MLB team — too good to be true, and it was. Two compounding bugs: (1) **Prefix collision** — iteration broke on first `ticker.startswith(prefix)` match, so `KXMLBPLAYOFFS-26-LAD` matched the `KXMLB` entry first. Same silently affected `KXNBAEAST`/`KXNBAWEST`/`KXNHLEAST`/`KXNHLWEST`. (2) **Semantic mismatch** — even with prefix ordering fixed, those 5 derivative entries pointed to championship-winner odds while representing playoff-qualification or conference-winner questions. LAD's probability to **make playoffs** (~95%) is fundamentally different from LAD's probability to **win the World Series** (~28%).
- **Fix:** Switched matching from `ticker.startswith(prefix)` to exact series extraction (`ticker.split("-", 1)[0]` lookup). Removed the 5 semantically-broken entries from `FUTURES_MAP` with a comment explaining why each needs a proper data source before being re-added (tracked in R19). Updated `FUTURES_FILTER_SHORTCUTS` to match.
- **Verification:** Same scan went from 45 bogus opportunities at +30-75% edge → 2 real opportunities at +4% edge (OKC NBA Finals, LAD World Series). Modest edges are what a sharp futures market should look like.

### R23. Robust Odds API key rotation + persistent quota cache
- **Problem:** `--filter mlb-futures` returned "No outright data" despite unfiltered scan working seconds earlier. Live probe showed first 5 of 10 keys exhausted (500/500 used each). Two compounding bugs: (1) `futures_edge.fetch_outrights` used `for attempt in range(3)`, so after keys 0-2 all 401'd the retry loop exited before reaching the healthy key at index 5. (2) `_remaining` dict was process-local — every fresh invocation rediscovered exhaustion the hard way.
- **Fix:** Replaced `range(3)` in `fetch_outrights` with the `tried: set[str]` loop pattern used in `edge_detector.fetch_odds_api` (cycles through every configured key). Added `mark_exhausted()` called on 401 responses. Persistent quota cache at `data/cache/odds_api_quota.json` — `_remaining` loaded at `_load_keys()` time, saved on every `report_remaining()` / `mark_exhausted()`. `get_current_key()` now auto-advances past keys with cached `remaining == 0`. Fallback: if every key is cached exhausted, return the current slot anyway so a monthly quota reset can be re-discovered.
- Env: nothing new — uses existing `ODDS_API_KEYS`.

### R24a. Webapp scan cache (`@st.cache_data(ttl=60)`)
- **Problem:** Zero `@st.cache` decorators existed anywhere in `webapp/` before this. Every scan-button click fired a fresh Odds API fetch, and exploratory "try a filter, scan, change filter, scan again" sessions burned requests fast. Investigation under R24 surfaced this as one contributor to F31's 175-requests-in-5-min burn rate.
- **Fix:** Added 60s TTL cache on `run_scan()` keyed on all scan parameters (market_type, ticker_filter, category, date, min_edge, top_n, exclude_open, cross_ref). Client param renamed `client` → `_client` per Streamlit convention for unhashable args. CLEAR button now also calls `run_scan.clear()` so the user can force a refresh on demand.

### R18. Scan tables show "Gate" column previewing executor rejects
- **Problem:** User ran `scan --filter mlb-futures --unit-size .5` and got "No opportunities passed risk checks" (LAD rejected on composite score 4.6 < 6.0). Same command without `--unit-size` happily listed LAD as a +4.3% edge row with no indication it would fail. Scan table promised an opportunity the system would never take.
- **Fix:** Added `preflight_gate_status(opp)` helper in `kalshi_executor.py` that checks the 5 static per-opportunity gates and returns a short label: `"ok"` / `"edge"` / `"price"` / `"score"` / `"conf"` / `"no-fav"` / `"pred-off"`. Wired into the scan-table render path of all four scanners. Green "ok" for pass, red label for the failing gate. Runtime gates (daily loss, position count, duplicate ticker, per-event cap, series dedup) require live portfolio state and are NOT checked here — `"ok"` is necessary but not sufficient.

### R20. Prediction-market audit
- **Findings:** Zero prediction-market bets in 173 historical settlements. All 6 modules (crypto / weather / spx / mentions / companies / politics) cache live data with no TTL. 4 of 6 modules have zero unit tests. Live scans produce obvious garbage: crypto +80% "edges" on 4¢ tail bets, weather showing $1.00 fair values on 1°F range markets (one was ready to execute at HIG confidence, 9.7 composite, one `--unit-size` away). `DEMO_KEY` hardcoded in `companies_edge.py`.
- **Prescription:** Safety-gate the category via R25. Rebuild (R25b/R25c) before any M1-M4 upgrades.

### R25. New Gate 4.7 — prediction-market safety gate
- **Fix:** New reject gate in `size_order()` — rejects opportunities where `opp.category in {"crypto", "weather", "spx", "mentions", "companies", "politics"}` unless `ALLOW_PREDICTION_BETS=true`. Default off. `preflight_gate_status()` returns `"pred-off"` so the R18 Gate column surfaces the rejection at scan time.
- Env: `ALLOW_PREDICTION_BETS=false` added to `.env.example`, `CLAUDE.md`, `docs/ARCHITECTURE.md`, webapp secrets passthrough.

### Gate Numbering
- **Total gates:** 13 (was 12). Reject gates 1-7 (including 3.5, 4.5, 4.6, 4.7); sizing caps 8-9.

### Tests
- 38 new tests across the session: 5 for `TestDedupCorrelatedBrackets` (R21), 7 for `TestFuturesSeriesMatch` (R22), 13 for `tests/test_odds_api.py` (R23), 9 for `TestPreflightGateStatus` (R18), 4 for the prediction safety gate (R25). 218 → 260 passing.

---

## 2026-04-24 -- 30-Day Calibration Cycle (R12, R13, R14, R15, R16)

### 30-Day Review (160 settled trades since 2026-03-25)
- **Sample:** 160 settled, 80W-80L (50%), +37.4% ROI ($43.48 P&L), Brier 0.2657. Aggregate remains healthy but concentrated: NHL +72% and NCAAB +71% carry most of the P&L; a single 7¢ MLS fill (04-20 +$14.80) is a third of the absolute P&L on its own.
- **F14 — High-confidence WR < Medium:** High 47% WR (n=57) vs Medium 53% WR (n=100). High ROI only wins via larger per-bet sizing. NBA instance is the loudest: High = 1-6 / -71% ROI.
- **F15 — NBA negative across three review windows:** 30d -14.8% (n=17), 14d -26%, post-baseline -15%. R2 stdev bump (04-21) too recent to attribute.
- **F17 — Calibration overconfidence persists 50-100%:** -14 to -22pp gap on every non-longshot probability bucket.
- **F21 — `model_calibration.py` blind to real sample:** Script read `trade_log` (16 entries, 3 closed) instead of `kalshi_settlements.json` (173 entries). R12 was impossible to run until fixed.
- **F22 — Live `.env` missing per-sport edge overrides:** For the entire post-baseline window, NBA and NCAAB were running at the 3% global floor, not the documented 8% / 10%. Silent drift — `.env.example` had them but the live env did not.

### R15. `model_calibration.py` points at settlement source
- **Fix:** New `_load_settled_trades()` normalizer reads `data/history/kalshi_settlements.json` (same source `betting_analysis.py` uses). Maps `cost` → `cost_dollars`, `won` → `settlement_won`, `settled_at` → `closed_at`; derives `category` from ticker via `bet_type_from_ticker()`. Replaces string-based ISO cutoff comparison with `datetime` parsing that tolerates trailing `Z`. All downstream helpers (`_brier_score`, `_calibration_buckets`, `_edge_bucket_stats`, `_dimension_stats`, cross-tab, recommendations) unchanged.
- Files: `scripts/kalshi/model_calibration.py`.

### R12. First full-sample calibration report
- **First run:** `reports/Calibration/2026-04-24_calibration_report.md`. 10 prioritized recommendations (2 HIGH, 8 MEDIUM). Brier 0.2657 (worse than coin-flip).
- **Per-sport Brier surfaces NBA as the worst-calibrated sport:** NBA 0.3306, NCAAB 0.2885, MLB 0.2519, NHL 0.2376 (NHL better than coin-flip — model is calibrated there), MLS 0.2364 (small sample).
- **Cross-tab insight:** medium × Total is the bread-and-butter combo (+46% ROI on n=71); high × Total is -52% on n=4 (tiny); high × ML is roughly flat at +10%.
- **Edge-bucket inversion softening:** 25%+ bucket 14d -24% ROI → 30d +16% ROI. Suggestive evidence R2 is working; needs another window + post-R13/R14 settlements to confirm.

### R14. `MIN_EDGE_THRESHOLD_NBA` bumped 0.08 → 0.12 (+ live-env override restore)
- **Fix:** NBA per-sport floor raised to 12%. Also added both `MIN_EDGE_THRESHOLD_NBA=0.12` and `MIN_EDGE_THRESHOLD_NCAAB=0.10` to the live `.env` — they were documented in `.env.example` and `CLAUDE.md` but missing from the actual env file, so both were silently falling back to the 3% global floor.
- **Scope intentionally minimal:** 17-bet NBA sample showed the bleed was concentrated in High-confidence picks (1-6, -71% ROI) and 2/3 of the NBA ML losers were sub-10¢ lottery tickets already caught by R7. Playoff-specific stdev and "NBA Totals-only" filters explicitly rejected — not enough sample. Confidence-tier fix lives in R13.
- Env: `MIN_EDGE_THRESHOLD_NBA=0.12`. Files: `.env`, `.env.example`, `CLAUDE.md`, `docs/ARCHITECTURE.md`, `docs/setup/SETUP_GUIDE.md`, `docs/web-app/CLOUD.md`, `docs/scripts/kalshi_executor.md`, `docs/kalshi-sports-betting/MLB_FILTERING_GUIDE.md`, `.claude/html/index.html`, `scripts/kalshi/kalshi_executor.py` (docstring).

### R13. Confidence bumps are now one-way (down only)
- **Problem:** `_adjust_confidence_with_stats()` applied ±1 tier bumps from three call sites (team stats, rest/B2B, sharp money). 30-day data showed upward bumps correlated with inflated claimed edge but worse realized outcomes — High-confidence WR 47% < Medium 53% portfolio-wide, NBA High at 1-6 / -71% ROI.
- **Fix:** `contradicts` still drops a tier; `supports` is now a no-op. All three call sites share the function, so the change applies uniformly. Base "high" tier remains reachable via the book-count rule (≥8 sharp books + tight consensus <5%) — only the bolt-on bumps are neutralized. Kelly sizing unaffected (sizing doesn't use confidence directly); composite score naturally compresses; Gate 4.6's confidence=high requirement naturally tightens — correct direction.
- No env var. +4 regression tests (`TestConfidenceBumpsOneWay`) → 222 passing.
- Files: `scripts/kalshi/edge_detector.py`, `tests/test_edge_detection.py`.

### R16. Monthly calibration cron
- **Fix:** New `calibration` profile in `install_windows_task.py` runs `model_calibration.py --days 30 --save` on day 1 of each month at 02:00 (after nightly settler). Required extending the installer to support `MONTHLY` schedules with `/D` day specifier; daily profiles unchanged.
- **Also:** Narrowed `scripts/schedulers/` gitignore so the portable `automation/` folder is now tracked (three `.py` files — all paths derive from `__file__`, secrets via `.env`, no machine-specific state). Sibling scheduler folders with hardcoded-path `.bat` files stay gitignored.
- Install: `python scripts/schedulers/automation/install_windows_task.py install calibration`.
- Files: `scripts/schedulers/automation/install_windows_task.py`, `scripts/schedulers/automation/daily_sports_scan.py`, `scripts/schedulers/automation/telegram_bot.py`, `docs/setup/AUTOMATION_GUIDE.md`, `.gitignore`.

### Gate Numbering
- **Total gates:** 12 (unchanged since R7).

---

## 2026-04-22 -- Repo-Analysis Response + Lottery-Ticket Floor (Q1-Q5, R7)

### Repo Analysis Response (2026-04-22 independent review)
- **Q1. Web app `market_type` wired through service layer.** UI exposed sports/futures/prediction/polymarket but `webapp/services.py run_scan()` had no `market_type` param — everything routed into `scan_all_markets` (sports-only). `run_scan()` now dispatches to `scan_all_markets` (sports), `scan_futures_markets` (futures), or `scan_prediction_markets` (prediction) based on UI selection; `cross_ref` passed through for Polymarket reference pricing on prediction scans. Invalid types raise `ValueError` at the boundary. Standalone Polymarket removed from `MARKET_TYPES`, `CATEGORIES_BY_TYPE`, `FILTERS_BY_TYPE`, sidebar `QUICK_SCANS` — UI-only, never reached service layer. CLI `scan.py polymarket` still works. Files: `webapp/services.py`, `webapp/views/scan_page.py`, `webapp/app.py`, `docs/web-app/LOCAL.md`.
- **Q2. Test env-contamination fix.** `test_approved_clean_when_no_caps_hit` read `MAX_BET_SIZE` and `KELLY_FRACTION` from `kalshi_executor` at import time, so a developer `.env` with `MAX_BET_SIZE=15` and `KELLY_FRACTION=1.0` would trip the max-bet cap and return `APPROVED_CAPPED_MAX_BET` instead of `APPROVED`. Fix: monkey-patch both module constants to documented defaults for the test's scope, matching the existing pattern in `test_approved_capped_max_bet`. Files: `tests/test_risk_gates.py`.
- **Q3. Doc drift: count-free "risk gates" references.** `docs/SCRIPTS_REFERENCE.md`, `docs/setup/AUTOMATION_GUIDE.md`, `docs/web-app/LOCAL.md` said "8 risk gates" post-R1/R3. Updated to count-free phrasing ("all risk gates") linking to `CLAUDE.md` §"Execution Gates"; CLAUDE.md heading renamed from "11 Execution Gates" to "Execution Gates". Prevents doc churn on every gate addition.
- **Q4. Pages deploy branch fix.** `.github/workflows/deploy.yml` triggered on `main`; repo default is `master`. Flipped so pushes to master actually redeploy `.claude/html/` (the Edge-Radar data-flow visualization).
- **Q5. Declared `pandas` in `requirements.txt`.** All four `webapp/views/*.py` import pandas; it was working only via Streamlit's transitive dep. Promoted to `pandas>=2.1.4` as a first-class runtime dep.

### R7. Minimum Market-Price Floor (new Gate 3.5)
- **Problem:** F10 from the 2026-04-21 14-day review showed sub-10¢ bets at 1W-3L with the model claiming "+50% edge" on 8-10¢ longshots. One win masked a systemic lottery-ticket overfit pattern.
- **Fix:** New reject gate in `size_order()` — any bet whose market price is below `MIN_MARKET_PRICE` (default **$0.10**) is rejected. Strict less-than: $0.09 rejected, $0.10 approved. No exception for edge/confidence (unlike Gate 4.6's carve-out). Set to 0 to disable and keep all longshots.
- **Defaults:** `MIN_MARKET_PRICE=0.10` chosen in discussion ("I kind of like the long shots. But I definitely agree We shouldn't go too low. I like .10") — blocks the lottery-ticket cluster while keeping moderate longshots (≥10¢) eligible.
- Env: `MIN_MARKET_PRICE` (plumbed through `.env.example`, `CLAUDE.md`, `webapp/services.py` flat-keys for Streamlit Cloud secrets).

### Gate Numbering
- **Total gates:** 12 (was 11). Reject gates 1-7 (including 3.5, 4.5, 4.6); sizing caps 8-9.

### Tests
- 5 new tests for Gate 3.5 (reject below floor, reject just below floor, approve at floor inclusive, approve above floor, disabled when `MIN_MARKET_PRICE=0`). 213 → 218 passing. Two pre-existing tests (`test_contracts_capped_by_bankroll`, `test_price_clamped_to_valid_range`) that intentionally use sub-10¢ prices patched to disable `MIN_MARKET_PRICE` for their scope so they exercise their actual intent.

---

## 2026-04-21 -- 14-Day Review Response (R1, R2, R3, R4)

### 14-Day Review (76 settled trades since 2026-04-07)
- **Sample:** 76 settled, 37W-39L (48.7%), +31% ROI, Brier 0.2646. Aggregate was carried by NHL (+87% ROI) and a single 7¢ MLS outlier.
- **F1 — NO-side systematically loses on high edge:** YES +93% ROI (n=48); NO -20% ROI (n=28); NO at ≥20% edge: 31% WR, -33% ROI (n=16). All 13 high-edge losers in the window were NO-side.
- **F6 — Low confidence:** 0W-3L / -105% ROI, consistent with the 2026-04-18 window.

### R3. `MIN_CONFIDENCE` Reject Gate (new Gate 4.5)
- **Fix:** Reject any opportunity whose confidence label ranks below `MIN_CONFIDENCE` (default `medium`). Low-confidence bets were 0W-3L / -105% ROI across two review windows — rejecting outright instead of warning.
- Env: `MIN_CONFIDENCE` (values: `low` | `medium` | `high`).

### R1. NO-Side Favorite Guard + Half-Kelly Dampener (new Gate 4.6)
- **Problem:** Every high-edge loser in the 14-day window was a NO bet on a heavy favorite. The model over-estimates edge on the "long-price, short-distance" NO side.
- **Fix — reject gate:** Reject NO bets whose market price < `NO_SIDE_FAVORITE_THRESHOLD` (default 0.25) unless edge ≥ `NO_SIDE_MIN_EDGE` (default 0.25) AND confidence = `high`. The carve-out lets genuinely sharp NO plays through but forces the bar much higher than the default 3% floor.
- **Fix — sizing dampener:** NO bets priced below `NO_SIDE_KELLY_PRICE_FLOOR` (default 0.35) are sized at `NO_SIDE_KELLY_MULTIPLIER` (default 0.5 = half-Kelly) of normal Kelly. Complements the reject gate — bets that clear it but are still on moderate favorites get downsized rather than sized at full confidence.
- Env: `NO_SIDE_FAVORITE_THRESHOLD`, `NO_SIDE_MIN_EDGE`, `NO_SIDE_KELLY_PRICE_FLOOR`, `NO_SIDE_KELLY_MULTIPLIER`.

### Gate Numbering
- **Total gates:** 11 (was 9). Reject gates 1-7 (including 4.5 and 4.6); sizing caps 8-9.

### R4. Resting-Order Janitor
- **Problem:** The 14-day review showed 16% of new orders (4/25) resting 25-66h with zero fills. Edge-Radar is fire-and-forget after placing a limit order — nothing polled Kalshi for stale orders. Stranded resting orders tied up balance and cluttered the order book without contributing to P&L.
- **Fix:** New `cancel_stale_resting_orders()` helper in `kalshi_executor.py`. Lists resting orders via `client.get_orders(status="resting")`, filters to those older than `RESTING_ORDER_MAX_HOURS` (default 24) with `fill_count_fp == 0`, and calls `client.cancel_order()` on each. Partial/full fills are left for the settler to handle.
- **Trigger:** Runs at the top of `execute_pipeline()` only when `execute=True` AND `DRY_RUN=false`. Preview scans never touch the order book; dry-run execute calls skip the janitor entirely. With the user's existing 5AM daily `--execute` scan, the natural cadence covers the 24h threshold without needing a separate scheduler.
- Env: `RESTING_ORDER_MAX_HOURS` (0 disables).

### R2. Per-Sport Stdev Bump (supersedes C2)
- **Problem:** Brier 0.2646 (still worse than coin-flip 0.2500) and a 60-70% favorite-band overconfidence gap of +18% (largest bucket, n=40). C1's Kelly soft-cap dampens sizing on fake-high edges but does not touch the underlying probability estimates. The sport-level 14-day numbers (NBA -26%, MLB -10%) persist. Meanwhile NHL is at +87% ROI and well-calibrated.
- **Fix:** Widen the normal-CDF probability distributions for the three underperforming sports.
  - `SPORT_MARGIN_STDEV`: NBA 12.0 -> 13.8 (+15%), NCAAB 11.0 -> 12.1 (+10%), MLB 3.5 -> 4.025 (+15%).
  - `SPORT_TOTAL_STDEV`: NBA 18.0 -> 20.7 (+15%), NCAAB 16.0 -> 17.6 (+10%), MLB 3.0 -> 3.45 (+15%).
  - NHL, NFL, NCAAF, soccer, MMA unchanged.
- **Mechanism:** Wider stdev pulls probability mass toward 50%, directly reducing the favorite-band overconfidence and compressing the implausibly large edges in the >=25% bucket (which realized -24% ROI in the review).
- **Attribution plan:** R12 re-runs `model_calibration.py` at 100 post-baseline trades (currently at 66). The window between R2's ship date and that checkpoint is the cleanest place to measure whether the probability-width fix improved Brier.

### Tests
- 32 new tests (181 -> 213 passing): 6 for `MIN_CONFIDENCE` gate, 4 for NO-side reject gate, 3 for NO-side Kelly multiplier, 12 for the resting-order janitor (stale/young/partial/zero-hours/API-error/malformed-timestamp/default-env coverage), 1 multiplier-vs-full-Kelly comparison, and 6 for the R2 per-sport stdev values (margin + total + NHL-untouched + other-sports-untouched + ticker-prefix lookup).

---

## 2026-04-18 -- Calibration-Driven Risk Tuning & Odds API Rotation Fix

### First Post-Baseline Calibration Run (66 Edge-Radar trades since 2026-04-03)
- **Findings:** Brier score 0.2561 (worse than coin-flip 0.2500); claimed edges >=25% realize -35% ROI while 10-15% claimed edges realize +127%; NBA -15% ROI, NCAAB -62% ROI at the global 3% floor; NHL +100% ROI; same-matchup bets on consecutive days produced compounding losses (LA Angels @ NY Yankees Apr 13/14/15, NY Mets @ LA Dodgers Apr 13/15, Colorado @ Houston Apr 14/15).
- **Report:** `reports/Calibration/2026-04-18_calibration_report.md`.

### C1. Kelly Edge Soft-Cap
- **Problem:** Kelly sizing uses `edge` linearly. A claimed 25% edge sized 2.5x larger than a 10% edge -- and the >=25% bucket is the worst-performing (-35% ROI, 30% WR on 10 trades). The system was sizing biggest on the least-calibrated signal.
- **Fix:** New `trusted_edge()` helper in `kalshi_executor.py` softly caps the edge used inside the Kelly calculation above `KELLY_EDGE_CAP` (default 0.15), with the excess multiplied by `KELLY_EDGE_DECAY` (default 0.5). Example: a claimed 25% edge sizes like 20%, a 35% edge like 25%. Raw edge still flows through gates, reports, rationale, and the trade journal -- only Kelly sizing sees the trusted value.
- Env: `KELLY_EDGE_CAP`, `KELLY_EDGE_DECAY`.

### C3. Per-Sport `MIN_EDGE_THRESHOLD`
- **Problem:** NBA lost -15% ROI (13 post-baseline trades) and NCAAB lost -62% ROI (8 trades in 14-day window) at the 3% global floor, while NHL was +100% on the same floor.
- **Fix:** New `min_edge_for(opp)` helper with `_PER_SPORT_MIN_EDGE` dict populated at import from `MIN_EDGE_THRESHOLD_<SPORT>` env vars (supported: MLB, NBA, NHL, NFL, NCAAB, NCAAF, MLS, SOCCER). Defaults set: `NBA=0.08`, `NCAAB=0.10`. Gate 3 rejection message shows the per-sport floor in effect.

### C5. Series-Level Correlation Dedup (New Gate 7)
- **Problem:** `dedup_correlated_brackets()` deduped within a single day but couldn't see across days. Same-matchup bets on consecutive nights compounded losses (LA Angels @ NY Yankees 3 nights, net negative; NY Mets @ LA Dodgers 2 nights, both losing; COL @ HOU 2 nights, both losing).
- **Fix:** New Gate 7 rejects a new bet if the same matchup (sport + team pair, date-agnostic) was already bet within `SERIES_DEDUP_HOURS` (default 48). `matchup_key(ticker)` strips the leading YY-MMM-DD date and optional HHMM game-time prefix to produce a series-invariant key. `recent_matchups_from_log()` walks the local trade log; dry-run runs don't write to the log, so no extra filtering needed.
- **Gate numbering:** Total gates now 9 (1-7 reject, 8-9 sizing cap). Previously 8.
- Env: `SERIES_DEDUP_HOURS` (0 disables).

### Bug Fix: Odds API Key Rotation Bailed Early
- **Problem:** `scan.py sports --filter mlb` returned 0 MLB events while the all-sports `.bat` scan pulled 28 -- same API keys, same date. With 10 configured keys and the first 3-4 currently exhausted on their monthly quota, the fixed `range(3)` retry loop in `fetch_odds_api()` rotated on each 401 but exited before trying the newly-rotated key. The all-sports scan masked the issue because earlier sports (golf, soccer) rotated past the dead keys first, so by the time MLB was queried the active key was fresh. Single-sport filter runs never got that warmup.
- **Fix:** Replaced the fixed-count loop with a set-based "tried every key at most once" while-loop. Explicit log message when all keys return 401/429 instead of silent empty result. Happy path unchanged (first working key succeeds, no unnecessary rotation). 4 regression tests cover all-keys-tried, rotates-past-exhausted, first-key-success, and single-key-401.
- Files: `scripts/kalshi/edge_detector.py:fetch_odds_api`.

### Tests
- 20 new tests total (161 -> 181 passing): 6 for `trusted_edge`, 5 for per-sport edge floors, 16 for series dedup (`matchup_key`, `recent_matchups_from_log`, gate behavior), 4 for Odds API rotation.

---

## 2026-04-08 -- Full Sports Coverage & Multi-Filter Support

### Expanded Odds API Sport Mapping (4 -> 18 sports)
- **Problem:** `KALSHI_TO_ODDS_SPORT` only mapped 4 sports (NBA, NHL, MLB, NCAAB). All other sports -- NFL, soccer, UFC, boxing, F1, NASCAR, PGA, IPL, college football/women's basketball -- were fetched from Kalshi but silently dropped because no external odds existed to calculate edge against.
- **Fix:** Added mappings for all 14 missing sports with Odds API coverage: NFL (`americanfootball_nfl`), NCAA Football (`americanfootball_ncaaf`), NCAA Women's Basketball (`basketball_wncaab`), MLS (`soccer_usa_mls`), EPL (`soccer_epl`), UCL (`soccer_uefa_champs_league`), La Liga (`soccer_spain_la_liga`), Serie A (`soccer_italy_serie_a`), Bundesliga (`soccer_germany_bundesliga`), Ligue 1 (`soccer_france_ligue_one`), UFC (`mma_mixed_martial_arts`), Boxing (`boxing_boxing`), F1 (`motorsport_formula_one`), PGA (`golf_pga_championship`), IPL (`cricket_ipl`).
- **CATEGORY_MAP expanded:** Added 18 new ticker prefix -> category mappings (NFL game/spread/total, MLS game/spread/total, all soccer leagues, UFC, boxing, IPL, F1, NASCAR, PGA, NCAA women's basketball) so these markets get properly categorized instead of falling to "other".
- **No-filter scan expanded:** Since the unfiltered scan (`scan.py sports`) uses `KALSHI_TO_ODDS_SPORT` keys to determine which prefixes to fetch, this change automatically expands coverage from 11 to 30 prefixes.

### Comma-Separated Multi-Filter (`--filter mlb,nhl`)
- **Problem:** `--filter` only accepted a single sport. Scanning two sports required two separate runs, wasting Odds API quota and time.
- **Fix:** `--filter` now accepts comma-separated values. Each value is resolved independently through `FILTER_SHORTCUTS`, and all prefixes are merged. Example: `--filter mlb,nhl` fetches all MLB and NHL prefixes in one scan.
- **Futures guard:** Single-value futures filters (e.g., `--filter nba-futures`) still route to the dedicated futures scanner as before.
- Files changed: `scripts/kalshi/edge_detector.py`

---

## 2026-04-08 -- Streamlit Community Cloud Deployment

### Web Dashboard Live at edge-radar.streamlit.app
- **Deployed** the Streamlit dashboard to Streamlit Community Cloud (free tier) with password-gated access.
- **Inline PEM support:** `KalshiClient` now accepts private key content as a string (not just a file path), enabling Cloud deployment where no filesystem is available. Priority: inline content > env var > `st.secrets` > file path. Local dev workflow unchanged.
- **Secrets bridge:** `webapp/services.py` injects Streamlit Cloud secrets into `os.environ` before script imports, so all existing `os.getenv()` calls (odds_api, edge_detector, etc.) work on Cloud without modification. Supports both nested (`[kalshi] / api_key`) and flat (`KALSHI_API_KEY`) TOML layouts.
- **Dependency pins loosened:** Changed all `==` pins to `>=` in `requirements.txt` — Streamlit Cloud runs Python 3.14 which can't build `scipy==1.11.4` from source (no Fortran compiler).
- **Repo public-readiness:** Removed tracked `reports/` and `.claude/memory/` from git (were committed before gitignore rules). Added `.claude/memory/` to `.gitignore`.
- **sys.path fix:** Added `webapp/` directory to `sys.path` in `app.py` so bare imports work when Streamlit Cloud runs from the repo root.
- Files changed: `kalshi_client.py`, `webapp/services.py`, `webapp/app.py`, `requirements.txt`, `.gitignore`

---

## 2026-04-06 -- Dynamic Stdev Adjustment (S5 Enhancement)

### S5. Dynamic Stdev Adjustment for Weather
- **Problem:** Sport-specific standard deviations in the normal CDF model were static constants. Weather, rest/B2B, and pitcher signals adjusted confidence or fair value, but only pitcher and rest affected the CDF stdev (and only for totals, not spreads). Spreads had no dynamic stdev adjustment at all.
- **Fix:** Weather now contributes a `stdev_adjustment` alongside its existing fair-value shift. The adjustment scales by severity: severe (+0.5), moderate (+0.3), mild (+0.1), none (0.0). Dome stadiums always return 0.0. Both `detect_edge_spread()` and `detect_edge_total()` now compound all applicable stdev adjustments (weather + rest for spreads; weather + rest + pitcher for totals).
- **Spread improvement:** `consensus_spread_prob()` now accepts a `stdev_adjustment` parameter, bringing spreads to parity with totals. Previously spreads used only the static sport-specific stdev.
- **Caching:** New `_weather_for_market()` cached helper in `scan_all_markets()` fetches weather once per home team, avoiding duplicate NWS API calls across spread and total markets for the same game.
- **Effect:** Bad weather increases the stdev in the normal CDF model, making the system more conservative on alternate lines where uncertainty compounds. Spreads now benefit from the same dynamic stdev pipeline that totals already had.
- Files changed: `scripts/shared/sports_weather.py` (added `stdev_adjustment` to return dict), `scripts/kalshi/edge_detector.py` (`consensus_spread_prob()` accepts stdev_adjustment, `detect_edge_spread()` and `detect_edge_total()` accept weather_data, new `_weather_for_market()` cache helper)

---

## 2026-04-06 -- Code Simplification (S5, S6)

### S5. Deleted `config.py` (Dead Module)
- **Problem:** `scripts/shared/config.py` defined env vars and constants (scoring weights, crypto/weather/SPX constants, `CONFIDENCE_RANK`) that were dead code -- no consumer imported them. The only two live imports were `LOG_DIR` and `LOG_LEVEL` used by `logging_setup.py`.
- **Fix:** Deleted `config.py` entirely. `logging_setup.py` now defines `LOG_DIR` and `LOG_LEVEL` inline (reads from env with `dotenv`). `webapp/services.py` now reads its env vars directly with `os.getenv()` instead of importing from config.
- Files changed: `config.py` (deleted), `logging_setup.py`, `webapp/services.py`

### S6. Removed `MAX_POSITION_CONCENTRATION` Env Var and Risk Gate
- **Problem:** Gate 7 (concentration cap at 20% of bankroll) was redundant with the `MAX_BET_SIZE` hard cap. The hard cap already limits any single position to $100, making a percentage-of-bankroll check unnecessary for the current bankroll range.
- **Fix:** Removed `MAX_CONCENTRATION` variable and concentration gate from `kalshi_executor.py`. Removed `MAX_POSITION_CONCENTRATION` from `.env`, `.env.example`, and `CLAUDE.md`. Removed `APPROVED_CAPPED_CONCENTRATION` approval subtype. Renumbered remaining gates: old gate 8 (max bet size) is now gate 7, old gate 9 (bet ratio cap) is now gate 8.
- **Gate count:** 9 gates reduced to 8. Gates 1-6 reject, gates 7-8 are sizing caps (max bet, bet ratio).
- **Tests:** Concentration gate test removed (101 tests down to 100).
- Files changed: `kalshi_executor.py`, `.env`, `.env.example`, `CLAUDE.md`

---

## 2026-04-06 -- Code Simplification (S3, S4)

### S3. Removed `--max-bet-ratio` and `--max-per-game` CLI Flags
- **Problem:** `--max-bet-ratio` and `--max-per-game` were available as CLI flags, duplicating env-only settings. This added unnecessary complexity to the CLI surface and every scanner's argument parser.
- **Fix:** Removed `--max-bet-ratio` from `edge_detector.py`, `kalshi_executor.py`, `futures_edge.py`, `prediction_scanner.py`, `polymarket_edge.py`, and `scan.py` help text. Removed `--max-per-game` from `edge_detector.py` and `kalshi_executor.py`. Removed `max_per_game` and `max_bet_ratio` parameters from `execute_pipeline()` signature.
- **Configuration:** Both settings are now `.env`-only: `MAX_BET_RATIO` (default 3.0) and `MAX_PER_EVENT` (default 2).
- Files changed: `kalshi_executor.py`, `edge_detector.py`, `futures_edge.py`, `prediction_scanner.py`, `polymarket_edge.py`, `scan.py`

### S4. Merged `MAX_BET_SIZE_SPORTS` / `MAX_BET_SIZE_PREDICTION` into Single `MAX_BET_SIZE`
- **Problem:** Two separate env vars (`MAX_BET_SIZE_SPORTS=$50`, `MAX_BET_SIZE_PREDICTION=$100`) required a category lookup helper (`_max_bet_for()`) and a `_SPORTS_CATEGORIES` set in the executor. The distinction added complexity without meaningful risk benefit.
- **Fix:** Unified into a single `MAX_BET_SIZE` env var (default $100). Removed `MAX_BET_SIZE_SPORTS`, `MAX_BET_SIZE_PREDICTION`, `_SPORTS_CATEGORIES` set, and `_max_bet_for()` helper from executor. Risk check dashboard now shows a single "Max Bet Size" row. Gate 8 uses `MAX_BET_SIZE` directly.
- Files changed: `kalshi_executor.py`, `config.py`, `risk_check.py`, `.env.example`

---

## 2026-04-06 -- Code Simplification (S1, S2)

### S1. Removed `DEFAULT_BET_SIZE` (Dead Code)
- `DEFAULT_BET_SIZE` was defined in `kalshi_executor.py` but never referenced anywhere in the codebase. Removed the line. No behavioral change.

### S2. Removed `MIN_CONFIDENCE` Env Var and Risk Gate
- **Problem:** The confidence-floor risk gate (`MIN_CONFIDENCE`) was redundant. Composite score already incorporates confidence as 30% of its weight, so a low-confidence opportunity is already penalized in the score gate. Having a separate confidence gate added complexity without adding safety.
- **Fix:** Removed the `MIN_CONFIDENCE` env var from `kalshi_executor.py`, `config.py`, and `.env.example`. Removed `CONFIDENCE_RANK` dict from executor (kept in `config.py` with a note for scoring use). Removed risk gate 5 (confidence floor). Remaining gates renumbered: old 6-10 become 5-9.
- **Gate count:** 10 gates reduced to 9. Gates 1-4 reject, gates 5-6 reject (duplicate ticker, per-event cap), gates 7-9 are sizing caps (concentration, max bet, bet ratio).
- **Tests:** Confidence gate test removed (102 tests down to 101).
- Files changed: `kalshi_executor.py`, `config.py`, `.env.example`

---

## 2026-04-06 -- Bet Ratio Cap (Risk Gate 10) & Markdown Table Fix

### Risk Gate 10: Bet Ratio Cap (`MAX_BET_RATIO`)
- **Problem:** Kelly sizing could let one high-edge, low-price bet dominate a batch. For example, 41 contracts at $0.21 = $8.61 while two other bets cost ~$2 each. A single outlier absorbs most of the batch budget.
- **Fix:** New `MAX_BET_RATIO` parameter (default 3.0). No single bet can cost more than 3x the median batch cost. Only scales down outliers -- other bets in the batch are untouched.
- **Gate type:** Sizing cap (like gates 8-9). Downsizes the outlier rather than rejecting it. Fires after Kelly sizing and before budget cap.
- **Usage:** Set in `.env` as `MAX_BET_RATIO=3.0` or override per-run with `--max-bet-ratio 2.0`
- **CLI:** `--max-bet-ratio` flag added to all scanners (`edge_detector.py`, `futures_edge.py`, `prediction_scanner.py`, `polymarket_edge.py`) and `scan.py`
- Files changed: `kalshi_executor.py` (new env var, `_apply_bet_ratio_cap()` function, `execute_pipeline()` kwarg, CLI flag), `edge_detector.py`, `futures_edge.py`, `prediction_scanner.py`, `polymarket_edge.py` (CLI flag + pass-through), `scan.py` (help text), `.env.example`, `CLAUDE.md`

### Markdown Table Pipe Fix
- **Problem:** Report markdown tables had broken column alignment on some rows. `format_bet_label()` in `ticker_display.py` was replacing `" (vs "` with `" | "`, injecting a literal pipe character into markdown table cells -- breaking the table structure.
- **Fix:** Changed replacement from `" | "` to `" vs "` in `ticker_display.py`. Added `.replace("|", "/")` sanitization on bet and pick labels in `report_writer.py` (both scan and execution report writers) as a safety net against future pipe injection.
- Files changed: `ticker_display.py`, `report_writer.py`

---

## 2026-04-06 -- Streamlit Web Dashboard (U6)

### Web Dashboard v1.0
- **Purpose:** Lightweight web UI for occasional remote access. CLI remains primary interface.
- **Stack:** Streamlit with custom dark theme (JetBrains Mono + Outfit fonts, cyan/amber/red accent palette)
- **Pages:**
  - **Scan & Execute** — all CLI flags as controls, scan to find opportunities, preview to see sizing/costs, execute to place orders
  - **Portfolio** — balance, open positions, P&L, daily loss limit progress, resting orders
  - **Settle & Report** — settle completed markets, generate P&L reports rendered as formatted markdown
- **Architecture:** Thin service layer (`webapp/services.py`) wraps existing scanner/executor/settler functions. Captures `rich` console output via stdout redirect. No business logic duplication.
- **Theme:** Custom CSS injection (`webapp/theme.py`) — dark terminal aesthetic with grid overlay, styled metric cards, gradient buttons
- **Auth:** Optional password gate via `.streamlit/secrets.toml` (gitignored)
- **Code changes:** `kalshi_settler.py` `generate_report()` now returns markdown string for web rendering
- **Skill:** Official `streamlit/agent-skills` installed at `.claude/skills/developing-with-streamlit/` (17 sub-skills)
- **Docs:** `docs/web-app/` — SETUP.md, USAGE.md, ARCHITECTURE.md
- Launch: `streamlit run webapp/app.py`

### Dashboard Enhancements (D1, D2, D4 + polish)
- **D1: Quick-scan sidebar buttons** — Sports, Futures, Prediction, Polymarket buttons in sidebar pre-select market type
- **D2: Favorite scans** — Save/load/delete named scan configs. Stored in `data/webapp/favorites.json`. Favorites appear in sidebar for one-click loading.
- **D4: Default unit size** — Changed from $1.00 to $0.50
- **Dynamic controls** — Filter, category, budget, max-per-game, and cross-ref controls adapt based on selected market type. Sports-only params hidden for futures/prediction/polymarket.
- **Clear button** — Wipes all scan results, preview, and execution data for a fresh start
- **ANSI stripping** — Console output cleaned of escape codes and rich markup before display
- **Rich table removal** — Preview shows clean pipeline summary + Streamlit dataframe instead of box-drawing character tables
- **Expander replacement** — All `st.expander` widgets replaced with toggle buttons (Material icon font renders as broken text in the custom theme)

---

## 2026-04-06 -- Min-Bets Safety Gate

### `--min-bets` Flag
- **Problem:** With `--budget 10%` and `--max-bets 6`, if only 1-2 games pass risk checks, the entire budget gets concentrated into too few positions — defeating the purpose of diversification.
- **Fix:** New `--min-bets N` flag across all scanners. If fewer than N opportunities pass the 9 risk gates, the pipeline aborts before execution with a clear message.
- **How it works:** Gate fires after risk checks but before sizing/budget scaling. Returns an empty list so no orders are placed and no reports are generated for an under-diversified batch.
- **No flag = no minimum:** When `--min-bets` is omitted (default `None`), the gate is skipped entirely — current behavior unchanged.
- Example: `scan.py sports --unit-size .5 --max-bets 6 --min-bets 3 --budget 10% --exclude-open --execute`
- Files changed: `kalshi_executor.py` (new gate in `execute_pipeline`), `edge_detector.py`, `prediction_scanner.py`, `polymarket_edge.py`, `futures_edge.py` (CLI flag + pass-through in all four)

---

## 2026-04-04 (evening) -- Budget Cap for Batch Execution

### `--budget` Flag
- **Problem:** No way to control total batch cost. Kelly + unit sizing determines per-bet amounts independently, but there was no ceiling on the sum. Users wanting to limit daily exposure to a fixed percentage of bankroll (e.g., 10%) had no mechanism to enforce it.
- **Fix:** New `--budget` flag on `scan.py`, `edge_detector.py`, and `kalshi_executor.py`. Accepts a percentage of bankroll (e.g., `10%`) or a flat dollar amount (e.g., `15`).
- **How it works:** After all bets are sized normally (Kelly/flat, per-bet caps), if total cost exceeds the budget, all approved bets are proportionally scaled down. Higher-edge bets keep proportionally more capital (Kelly weighting preserved). Each bet keeps at least 1 contract, so the actual total may slightly undershoot the budget due to contract rounding.
- **No budget = no change:** When `--budget` is omitted, the pipeline behaves exactly as before. When total is already under the budget, a green confirmation message is shown and no scaling occurs.
- Example: `scan.py sports --unit-size .5 --max-bets 5 --budget 10% --date today --exclude-open`
- Files changed: `kalshi_executor.py` (new `_apply_budget_cap()`, `budget` param on `execute_pipeline`, CLI flag), `edge_detector.py` (CLI flag + pass-through), `scan.py` (help text)

---

## 2026-04-04 (afternoon) -- Fill-Based Accounting, Sizing Gate Docs, Pitcher Parallelization

### X5. Fill-Based Trade Logging
- **Problem:** The executor logged `contracts` and `cost_dollars` from the *requested* order, not from the Kalshi API fill response. Resting or partially-filled orders overstated exposure, distorted P&L, and corrupted settlement math.
- **Fix:** `log_trade()` now records both requested and filled values:
  - `requested_contracts` / `requested_cost` — what we asked for
  - `filled_contracts` / `filled_cost` — what Kalshi actually executed (primary accounting fields)
  - `fill_status` — `resting` | `partial` | `filled`
  - Legacy `contracts` / `cost_dollars` now reflect filled values for backward compatibility
- New `get_filled_contracts()` and `get_filled_cost()` helpers in `trade_log.py` with backward-compatible fallback for pre-X5 trade records
- `kalshi_settler.py` — `calculate_pnl()` uses filled values; resting orders (zero fills) skipped during settlement; settlement log and reconciliation use filled contracts
- `risk_check.py` — "Total wagered" in P&L summary and dashboard uses filled cost
- Execution output now flags resting and partial fills visually: `(RESTING — no fills yet)`, `(PARTIAL — 3/10 filled)`
- **16 new regression tests** covering: fill helpers (old/new format), fully filled, partial fill, zero fill/resting, settlement P&L with fill-based cost

### X6. Sizing Caps vs Reject Gates (Docs + Code)
- **Problem:** `ARCHITECTURE.md` described gates 8 (concentration) and 9 (max bet) as reject gates, but the executor silently downsized and approved. Post-trade review couldn't tell if an order passed cleanly or was force-capped.
- **Fix (docs):** `ARCHITECTURE.md` now correctly documents gates 1-7 as reject gates and gates 8-9 as sizing caps with "Cap — downsize to..." behavior
- **Fix (code):** `size_order()` returns approval subtypes:
  - `APPROVED` — clean pass, no caps hit
  - `APPROVED_CAPPED_CONCENTRATION` — downsized by gate 8
  - `APPROVED_CAPPED_MAX_BET` — downsized by gate 9
- All downstream pipeline filtering updated to use `.startswith("APPROVED")`
- **3 new tests** for clean approval, concentration cap, and max bet cap scenarios

### Pitcher Stats Parallelization
- `prefetch_mlb_pitchers()` now uses `ThreadPoolExecutor(max_workers=8)` to fetch all pitcher stats concurrently
- MLB scan time reduced from ~60s to ~35s (pitcher fetch specifically: ~60s → ~11s)
- Single-game `get_game_pitchers()` also parallelized (2 pitchers fetched concurrently)

### Batch-Aware Kelly Sizing
- **Problem:** Kelly sizing was applied independently per bet, so placing 10 simultaneous bets could commit 10x what single-bet Kelly intends. Total batch exposure could exceed 50% of bankroll.
- **Fix:** `size_order()` now accepts a `batch_size` parameter. Kelly fraction is divided by the number of bets in the batch: `effective_kelly = KELLY_FRACTION / batch_size`. Each bet gets its proportional share, keeping total batch exposure consistent with what single-bet Kelly would allocate.
- `execute_pipeline()` passes `min(len(opportunities), max_bets)` as the batch size
- `KELLY_FRACTION` is now configurable in `.env` (was only in `.env.example` before)

### Bug Fix: Pitcher Data NoneType Error
- Fixed `AttributeError: 'NoneType' object has no attribute 'get'` when MLB Stats API returns `None` for a pitcher (TBD starters)
- Changed `pitcher_data.get("away_pitcher", {}).get(...)` to `(pitcher_data.get("away_pitcher") or {}).get(...)` in both game and totals detection paths

### Test Suite
- **102 tests** (up from 83): +16 fill accounting, +3 approval subtypes

---

## 2026-04-04 -- Per-Game Diversification, Pitcher Data, Rest Days, Calibration

### Correlated Bracket Dedup & Per-Game Cap Reduction
- **Problem:** Automated execution was stacking 3 of 5 bets on the same game (e.g., Over 221.5, Over 224.5, Over 228.5 on BOS@MIL). These are highly correlated — they win or lose together.
- **Fix 1:** New `dedup_correlated_brackets()` in `kalshi_executor.py` — groups opportunities by `(event_key, category)` and keeps only the highest composite score from each group. Multiple totals lines on the same game collapse to the single best one.
- **Fix 2:** `MAX_PER_EVENT` default lowered from 3 to 2 (allows ML + totals on the same game, but not 3 correlated lines)
- **Fix 3:** Scanner-level `_cap_per_game` in `edge_detector.py` also lowered from 3 to 2
- New `--max-per-game N` CLI flag on both `edge_detector.py` and `kalshi_executor.py` for session-level override
- `size_order()` accepts `max_per_event` parameter instead of using the global directly

### S1. MLB Starting Pitcher Data (`scripts/shared/pitcher_stats.py`)
- New module fetching probable pitchers + season stats from MLB Stats API (free, no key)
- **Stats fetched:** ERA, FIP (approximated), WHIP, K/9, innings pitched, record, days rest
- **Pitcher tiers:** ace (ERA ≤ 3.20), mid (ERA ≤ 4.50), back (ERA > 4.50 or TBD)
- **Matchup classification** with stdev adjustments to the total probability model:
  - ace vs ace: -0.3 stdev (tighter game, lean under)
  - ace vs mid: -0.15 stdev (lean under)
  - mid vs mid: no adjustment (neutral)
  - mid vs back: +0.2 stdev (lean over)
  - bullpen day: +0.5 stdev (high variance, lean over)
- **Integration in `edge_detector.py`:**
  - Pre-fetches all pitcher data per game date in `scan_all_markets()` (step 3c)
  - Totals: stdev adjusted by matchup quality, confidence bumped/dropped by pitcher signal
  - Games: pitcher info attached to details (informational — moneyline odds already price in starters)
  - `consensus_total_prob()` now accepts `stdev_adjustment` parameter
- **`prefetch_mlb_pitchers(date)`** — bulk pre-fetch for all games on a date, indexed by team abbreviation
- CLI: `python scripts/shared/pitcher_stats.py 2026-04-04` for a quick pitcher table

### S2. NBA/NHL Back-to-Back & Rest Day Detection (`scripts/shared/rest_days.py`)
- New module detecting back-to-backs and rest days via ESPN scoreboard API (free, no key)
- Checks 1-4 days back per team to calculate days since last game
- **NBA adjustments:** B2B adds +1.5 to stdev (more variance/fatigue), leans under. Well-rested (3+ days) tightens stdev by -0.5
- **NHL adjustments:** B2B adds +0.3 stdev, slight under lean
- Returns per team: `is_b2b`, `days_rest`, `opponent_is_b2b`, `rest_advantage`, `stdev_adjustment`, `confidence_signal`
- **Integration in `edge_detector.py`:**
  - Pre-fetches rest data for NBA/NHL in `scan_all_markets()` (step 3d)
  - Totals: stdev adjusted by rest situation, confidence bumped for under when B2B
  - Games/Spreads: confidence adjusted based on rest advantage (B2B team less likely to win/cover)
  - Rest info attached to opportunity details for transparency
- Auto-routes through `scan.py` — no extra flags needed
- CLI: `python scripts/shared/rest_days.py basketball_nba 2026-04-04` for a quick rest table

### W2. Model Calibration Tool (`scripts/kalshi/model_calibration.py`)
- New script analyzing settled trades to surface calibration issues and generate prioritized recommendations
- **Reports:** Overall Brier score, calibration curve (predicted vs realized by probability bucket), dimension breakdowns (category, confidence, sport, edge bucket), confidence x category cross-tab
- **Recommendations engine:** Prioritized HIGH/MEDIUM/LOW actions for stdev adjustments, confidence signal fixes, edge estimation issues
- **Parked until post-baseline data:** Calibration baseline set to 2026-04-03 — pre-baseline trades span multiple model versions and produce misleading recommendations. Re-run after 100+ post-baseline trades.
- CLI: `python scripts/kalshi/model_calibration.py --save --days 30`

### X4. Startup Doctor (previously implemented, marked DONE in roadmap)
- `scripts/doctor.py` verified functional — checks Python version, venv, credentials, data dirs, config, API connectivity, pre-commit hooks
- Fixed stale `MAX_PER_EVENT` default (3 → 2) in doctor display

---

## 2026-04-02 -- Execution Correctness, Risk Gates, Kelly Sizing, Display Overhaul

### X1. Portable Python Path
- `scan.py` now uses `sys.executable` instead of hardcoded `.venv/Scripts/python.exe`
- Works across any environment (CI, WSL, Docker, other machines)

### X2. Nine Risk Gates Enforced in Executor
- **Previously:** `kalshi_executor.py` loaded `KELLY_FRACTION`, `MAX_CONCENTRATION`, and `MAX_BET_SIZE` but never enforced them. Only 5 of 9 gates were active.
- **Now:** All 9 gates enforced before every order: daily loss, position count, edge, score, confidence, duplicate ticker, per-event cap, max concentration, max bet size
- **Kelly sizing:** Quarter-Kelly with flat unit as floor. High-edge bets get more contracts; low-edge bets stay at minimum unit size
- **Category-aware bet caps:** Sports ($50) vs prediction ($100) separate limits
- **Batch tracking:** Approved orders update the open ticker set and event counts in-flight so gates apply correctly across the run
- New env vars: `MAX_PER_EVENT=3`, `MAX_POSITION_CONCENTRATION=0.20`

### X3. Per-Event Position Caps (built into X2)
- Max 3 positions per game/event (configurable via `MAX_PER_EVENT`)
- Extracts event key from ticker (strips pick suffix) to group markets by game
- Prevents hidden concentration where 7 of 10 positions are on the same matchup

### D1. Bet Type Column
- Added Type column (ML/Spread/Total/Prop) to all 7 output tables across scan, execute, positions, and settlement views
- New `bet_type_from_ticker()` helper in `ticker_display.py`

### D2. Descriptive Pick Column
- Replaced raw YES/NO Side column with descriptive Pick: "Spurs win", "Over 220.5", "Blazers -7.5"
- New `format_pick_label()` helper in `ticker_display.py`
- Added Kalshi team abbreviation aliases (SAS, GSW, NOP, etc.)

### D3. Sport Column
- Added Sport column (NBA/NHL/MLB/NFL/NCAAB/etc.) to scan table, executor preview table, and markdown reports
- New `sport_from_ticker()` helper in `ticker_display.py`
- Added `KXNCAABB` prefix alias for NCAA basketball championship tickers

### D4. Context-Aware Report Saving
- When `--unit-size` is passed, saves an **execution report** (Sport, Bet, Type, Pick, Qty, Price, Cost, Edge, total cost) instead of the scan report
- When no `--unit-size`, saves the scan report as before (Mkt, Fair, Edge, Conf, Score)
- New `save_execution_report()` function in `report_writer.py`
- `execute_pipeline` now returns sized orders on preview (was returning `[]`) so the report writer can use them

### Same-Day Automated Execution Scripts
- New `scripts/schedulers/same_day_executions/same_day_scan.bat` — preview all sports today, top 10 across all sports
- New `scripts/schedulers/same_day_executions/same_day_execute.bat` — scan + execute, with portfolio status before/after
- Recommended run time: 8 AM ET (all markets posted, sportsbook lines sharp, Kalshi lag window open)
- Single command scans NFL, NBA, NHL, MLB together, ranked by composite score, 10 bets max total
- Next-day scripts also available at `scripts/schedulers/next_day_executions/` as reserve

### How Scoring Works (ARCHITECTURE.md)
- New section explaining the full flow: Fair Value → Edge → Confidence → Score
- Includes dependency diagram, confidence thresholds by market type, composite score formula with weights, and worked example

### Documentation Overhaul
- `docs/scripts/` subdirectory: 7 dedicated script docs (edge_detector, futures_edge, prediction_scanner, polymarket_edge, kalshi_executor, kalshi_settler, risk_check)
- `SCRIPTS_REFERENCE.md` slimmed to hub with routing table, common flags, daily workflow
- `kalshi_executor.py` reframed as Portfolio Status + Execution Library; `run` subcommand deprecated
- `scan.py` flags table added (13 flags documented)
- All 25 prompts updated + 6 new prompts added (totals-only, spreads-only, multi-sport-execute, weekly-review, risk-audit, full-prediction-execute)
- ARCHITECTURE.md, CLAUDE.md, README.md, SKILL.md, .env.example all updated with 9-gate risk model
- ROADMAP.md restructured with 6 tiers, informed by 3rd-party assessment

---

## 2026-03-31 -- Unified Scanner, Scheduler Reorganization, Env & Report Cleanup

### P9. Unified Scan Entry Point (`scripts/scan.py`)
- Single entry point routing to all 4 scanners: `sports`, `futures`, `prediction`, `polymarket`
- Auto-inserts `scan` subcommand when omitted
- Aliases: `sport`, `pred`, `poly`, `xref`
- All flags forwarded directly via subprocess — no duplicate argument parsing
- Updated Quick Start, More Examples, Daily Workflow, and Scripts Reference to use `scan.py`

### P10. Documentation Cleanup
- Updated SPORTS_GUIDE: replaced all `kalshi_executor.py run` with `scan.py sports`, removed duplicated daily workflow (defers to SCRIPTS_REFERENCE), fixed composite score dimensions (3 → 4 with weights), added roadmap cross-link
- Updated FUTURES_GUIDE and PREDICTION_MARKETS_GUIDE: `scan.py` commands, roadmap cross-links
- Updated ARCHITECTURE: replaced duplicated Phase 2-4 task lists with pointer to ROADMAP.md
- Added back-links from SCRIPTS_REFERENCE to all domain guides

### P11. Pre-Commit Hooks (`.pre-commit-config.yaml`)
- `detect-secrets` — credential leak prevention (requires `.secrets.baseline`)
- `black` — code formatting (line-length 100)
- `flake8` — linting (max-line-length 100, ignore E203/W503)
- `check-json`, `check-yaml` — config file validation
- `end-of-file-fixer`, `trailing-whitespace` — whitespace hygiene
- `no-commit-to-branch` — prevents direct commits to master
- Install: `make hooks` or `pip install pre-commit && pre-commit install`

### P12. Makefile
- 18 targets: `scan-mlb`, `scan-nba`, `scan-nhl`, `scan-nfl`, `scan-sports`, `scan-futures`, `scan-predictions`, `scan-polymarket`, `scan-all`, `status`, `risk`, `settle`, `report`, `reconcile`, `test`, `test-quick`, `install`, `hooks`
- `make help` for full reference
- Note: requires `make` installed (`choco install make` on Windows)

### Scheduler Directory Reorganization
- Moved 4 `.bat` morning scan jobs to `scripts/schedulers/morning_scans/`
- Moved 2 Python automation scripts to `scripts/schedulers/automation/`
- Fixed `PROJECT_ROOT` depth in `install_windows_task.py` for new path
- Updated all path references in CLAUDE.md, README.md, SCRIPTS_REFERENCE.md

### P7. `MAX_BET_SIZE_SPORTS` Added to `.env.example`
- Added `MAX_BET_SIZE_SPORTS=50` — was referenced in CLAUDE.md and used by `risk_check.py` but missing from the env template

### P8. Report Output Format Unified
- Confirmed all scanners support `--save` for markdown reports
- `kalshi_executor.py run` delegates scanning to dedicated scanners (which have `--save`), so no gap remains
- Marked complete in roadmap

---

## 2026-03-30 -- Unified CLI, Readable Displays, Date Filtering, Project Cleanup

### Unified CLI Flags Across All Scanners
- All 4 scanners (`edge_detector.py`, `futures_edge.py`, `prediction_scanner.py`, `polymarket_edge.py`) now share the same execution flags: `--execute`, `--unit-size`, `--max-bets`, `--pick`, `--ticker`, `--save`
- Previously `--execute`/`--unit-size`/`--max-bets` only worked on `edge_detector.py` and `futures_edge.py`; prediction and polymarket scanners required routing through `kalshi_executor.py`

### Date & Open Position Filters
- Added `--date` flag to all scanners and executor: filter opportunities by game date
  - Accepts: `today`, `tomorrow`, `YYYY-MM-DD`, `MM-DD`, `mar31`
- Added `--exclude-open` flag: automatically skips markets where you already have an open position (both sides of the same game)
- Both filters work on all 5 entry points

### Shared Ticker Display Module (`scripts/shared/ticker_display.py`)
- New shared module for parsing Kalshi tickers into human-readable labels
- `parse_game_datetime()` -- extracts "Mar 30 6:40pm" from any ticker
- `parse_matchup()` -- extracts "White Sox @ Miami" from game tickers
- `parse_pick_team()` -- extracts picked team name from ticker suffix
- `format_bet_label()` -- best-effort readable label for any market type
- Team name lookups for MLB (30), NBA (30), NHL (32 teams)
- All 8 display tables across 7 scripts now show game date/time and readable matchup names

### Live Risk Dashboard (`scripts/kalshi/risk_check.py`)
- Rewritten to pull live data from Kalshi API (was reading empty local JSON files)
- Shows: account balance, risk limits, open positions with readable names + dates, resting orders, today's P&L, watchlist
- Positions table shows "Bet | When | Pick | Qty | Cost | P&L" instead of raw tickers

### Executor Status Improvements (`scripts/kalshi/kalshi_executor.py`)
- `status` command now shows readable matchups + game dates instead of raw tickers

### Markdown Report Format (`scripts/kalshi/kalshi_settler.py`)
- `report --detail --save` now generates proper markdown (tables, headers, bold values, code-formatted tickers)
- Changed file extension from `.txt` to `.md`

### MLB Filtering Guide (`docs/kalshi-sports-betting/MLB_FILTERING_GUIDE.md`)
- New comprehensive guide covering 10 filtering categories for MLB picks
- Includes composite strategies: "Strong MLB Play", "Weather Fade", "Sharp Follow", "Regression Fade", "Early Season Value"

### Markdown Scan Reports (`scripts/shared/report_writer.py`)
- New shared module: all scanners now save a markdown report alongside the JSON watchlist when `--save` is passed
- Reports include: readable matchups, game dates, edge/fair/market prices, confidence, composite score
- Saved to `reports/Sports/`, `reports/Futures/`, `reports/Predictions/` with date-stamped filenames
- Example: `reports/Sports/2026-03-30_mlb_sports_scan.md`

### Test Suite (83 tests)
- Created `tests/` with 4 test files covering the highest-value targets
- `test_risk_gates.py` (19 tests): position sizing (`unit_size_contracts`), all 5 risk gate rejections, bankroll capping, price clamping
- `test_ticker_display.py` (30 tests): team code splitting, date/time parsing, matchup rendering, date filtering, position exclusion
- `test_edge_detection.py` (14 tests): N-way de-vigging, normal CDF spread/total probability math
- `test_weather.py` (11 tests): MLB and NFL weather threshold adjustments, severity classification
- Shared fixtures in `conftest.py` for sample Opportunity objects

### Standardized Logging
- All 8 entry-point scripts migrated from `logging.basicConfig` + `logging.getLogger` to `setup_logging()` from `scripts/shared/logging_setup.py`
- Every script now gets console output (INFO+) plus a dedicated log file in `logs/` (DEBUG+)
- Zero `logging.basicConfig` calls remain in the codebase
- Library modules (`team_stats.py`, `line_movement.py`, etc.) correctly use `logging.getLogger()` to inherit config from entry points

### Consolidated Import Boilerplate
- Created `.venv/Lib/site-packages/edge_radar.pth` — auto-adds all script directories to `sys.path` when the venv is active
- Removed 16 `sys.path.insert(0, ...)` lines across 15 files
- Scripts now directly import shared modules without path setup boilerplate
- Created `scripts/bootstrap.py` as fallback for non-venv usage

### Removed Scheduler Framework
- Deleted `base_scheduler.py`, `sports_scheduler.py`, `prediction_scheduler.py`, `run_schedulers.py`, `scheduler_config.py`
- The framework was overengineered — every scheduler just called `scan_all_markets()` → `execute_pipeline()`, which the CLI scripts already do
- Replaced with direct Windows Task Scheduler / cron scheduling using the existing scanner scripts
- Kept `daily_sports_scan.py` (morning edge report) and `install_windows_task.py` (Task Scheduler helper)
- Removed `docs/schedulers/SCHEDULER_GUIDE.md`
- Added "Scheduling Your Own Scans" section to SCRIPTS_REFERENCE with `schtasks` examples

### Save Flag for Status & Risk Commands
- `kalshi_executor.py status --save` saves portfolio status as markdown to `reports/Accounts/Kalshi/kalshi_status_YYYY-MM-DD.md`
- `risk_check.py --save` saves full risk dashboard as markdown to `reports/Accounts/Kalshi/kalshi_dashboard_YYYY-MM-DD.md`
- Reports include: account balance, open positions (readable matchups + dates), today's P&L, resting orders, watchlist

### Project Cleanup
- Removed empty `strategies/` directory (edge detection is centralized in scanners, not strategy-pattern architecture)
- Updated CLAUDE.md project structure to reflect current state (`tests/`, `ticker_display.py`, `report_writer.py`)

---

## 2026-03-28 -- Polymarket Cross-Reference Integration

### Polymarket Edge Module (`scripts/polymarket/polymarket_edge.py`)
- New module: cross-references Kalshi market prices against Polymarket via the Gamma API (free, no key required)
- Fetches active Polymarket markets by category (crypto, weather, S&P, politics, companies)
- Fuzzy market matching engine using 4 signals: title similarity, strike price, expiry date, asset keyword overlap
- Standalone edge detection: surfaces price discrepancies between Kalshi and Polymarket as arbitrage-style signals
- Enrichment mode: boosts composite score when Polymarket confirms an existing edge, penalizes when it disagrees
- Standalone CLI: `polymarket_edge.py scan`, `polymarket_edge.py match TICKER`

### Prediction Scanner Integration (`scripts/prediction/prediction_scanner.py`)
- Added `--cross-ref` flag to enable Polymarket cross-referencing during scans
- Added `--filter polymarket` / `poly` / `xref` shortcuts (auto-enables cross-ref mode)
- When active, the scanner: (1) finds standalone cross-market edge opportunities, and (2) enriches all existing opportunities with Polymarket confirmation/disagreement signals
- New `cross_ref` parameter on `scan_prediction_markets()` for programmatic use

---

## 2026-03-23 -- Edge Model Overhaul, Scheduler Framework, Doc Consolidation

### Spread & Total Model Recalibration (`scripts/kalshi/edge_detector.py`)
- Replaced linear probability adjustment (`+3% per point`) with normal CDF model using `scipy.stats.norm`
- Infers expected score margin from book spread + implied probability, then calculates P(margin > strike) on the bell curve
- Added sport-specific standard deviations: NBA (12), NCAAB (11), NFL (13.5), MLB (3.5), NHL (2.5), soccer (1.8)
- Same fix applied to total (over/under) markets with separate total stdev values
- Old model systematically overestimated edge on alternate spreads (caused 1W-11L on NCAAB)

### Daily Morning Scan (`scripts/schedulers/daily_sports_scan.py`)
- New script: scans MLB, NBA, NHL, NFL each morning for top 25 opportunities
- Saves timestamped report to `reports/Sports/daily_edge_reports/YYYY-MM-DD_morning_scan.md`
- Report includes edge, fair value, market price, confidence, team stats, sharp signals, weather
- `--daemon` flag runs via APScheduler at 8:00 AM PST daily with automatic DST handling
- `--top N` to customize number of opportunities (default 25)

### Line Movement & Sharp Money Detection (`scripts/shared/line_movement.py`)
- New module: ESPN scoreboard API provides opening vs closing odds (DraftKings) for free
- Detects reverse line movement (spread moves away from favorite = sharp on underdog)
- Detects sharp total movement (total drops/rises >2 pts)
- Pre-fetched once per scan, integrated into game/spread/total confidence signals
- Sharp agreement boosts confidence; contradiction reduces it
- Covers NBA, NFL, NHL, MLB, NCAAB, NCAAF

### Weather Impact for Outdoor Sports (`scripts/shared/sports_weather.py`)
- New module: NWS hourly forecast for 31 NFL + 30 MLB venues (dome/outdoor classified)
- Scoring adjustment model: wind >15mph, rain >40%, cold <32F (NFL) / <45F (MLB)
- Integrated into `detect_edge_total()`: bad weather reduces over fair value, boosts under
- Dome stadiums automatically skipped (zero adjustment)
- Free NWS API, no key required

### Team Stats Integrated into Edge Detection (`scripts/kalshi/edge_detector.py`)
- Game and spread edge detectors now look up team win% via `team_stats.py`
- Stats signal: "supports" (win% >= 60% for YES, <= 40% for NO), "contradicts" (opposite), or "neutral"
- Confidence is bumped up one level when stats support the bet, dropped when stats contradict
- Team record and signal stored in opportunity details for transparency

### Sharp Book Weighting (`scripts/kalshi/edge_detector.py`, `scripts/kalshi/futures_edge.py`)
- Added `BOOK_WEIGHTS` map: Pinnacle/Circa at 3x, mid-tier at 1-1.5x, DraftKings/FanDuel/BetMGM at 0.7x
- Replaced simple median with `weighted_median()` across all consensus functions (game, spread, total, futures)
- Sharp books pull the consensus fair value toward their more accurate lines
- 21 books mapped with weights; unknown books default to 1.0x

### Team Stats Module (`scripts/shared/team_stats.py`)
- New module providing team performance data from free APIs (no keys required)
- ESPN API: NBA, NCAAB, NFL, NCAAF standings, win%, points for/against
- NHL Stats API: standings, goal differential, L10 record, streak
- MLB Stats API: standings, run differential, winning percentage
- 6 sports covered, unified `get_team_stats(team, sport)` lookup with fuzzy name matching
- Data cached per session to minimize API calls

### Closing Line Value Tracking (`scripts/kalshi/kalshi_settler.py`)
- Settler now captures closing price from Kalshi API when settling trades
- Calculates CLV = closing_price - entry_price per trade
- Performance report includes CLV section: average CLV and beat-the-close rate
- CLV is the gold standard for validating whether the model has real predictive value

### Rebranded to Edge-Radar
- Renamed from FinAgent / Finance-Agent-Pro / edge-hunter to Edge-Radar
- Updated all references across CLAUDE.md, README, ARCHITECTURE, agents, Python docstrings, User-Agent headers, reports, and memory

### Documentation Consolidation
- Merged `USER_GUIDE.md` + `BETTING_GUIDE.md` into single `SPORTS_GUIDE.md` (1117 → 405 lines)
- Replaced `KALSHI_STRATEGY_PLAN.md` with lean `ARCHITECTURE.md` (pipeline, risk gates, data flow)
- Trimmed `FUTURES_GUIDE.md` (456 → 359 lines) and `PREDICTION_MARKETS_GUIDE.md` (414 → 252 lines)
- Slimmed `README.md` (206 → 79 lines) with doc index linking to all guides
- Eliminated ~600 lines of duplicated risk gates, command examples, and filter tables across docs

---

## 2026-03-23 -- Scheduler Framework, Trade Log Cleanup, Report Export

### Scheduler Framework (`scripts/schedulers/`)
- New per-market scheduler architecture — each sport/market gets its own independent scheduler
- `BaseScheduler` class with DRY_RUN enforcement, consecutive failure auto-pause (5 strikes), structured logging
- `SportsScheduler` and `PredictionScheduler` subclasses calling existing pipelines directly (no subprocess wrapping)
- `scheduler_config.py` — profiles loaded from `SCHED_{NAME}_*` env vars (9 registered: NBA, NHL, MLB, NFL, NCAA, soccer, crypto, weather, SPX)
- `run_schedulers.py` — CLI entry point: `--list` (show all profiles), `--only nba` (single), or launch all enabled in parallel
- All schedulers disabled by default — enable via `SCHED_{NAME}_ENABLED=true` in `.env`
- Docs: `docs/schedulers/SCHEDULER_GUIDE.md`

### Trade Log Cleanup
- Cross-validated local trade log against Kalshi API fills — identified 32 demo trades mixed with 12 live trades
- Purged all demo trades from `kalshi_trades.json` and `kalshi_settlements.json`
- Backups saved: `kalshi_trades_pre_cleanup_2026-03-23.json`, `kalshi_settlements_pre_cleanup_2026-03-23.json`
- Report now shows accurate live-only data: 12 trades, $10.67 wagered

### Report File Export
- Added `--save` flag to `kalshi_settler.py report` — writes plain-text report to `reports/Accounts/Kalshi/kalshi_report_YYYY-MM-DD.txt`
- Report includes timestamp, strips Rich markup for clean text output

### Kalshi Client Hardening
- Changed default `KALSHI_BASE_URL` fallback from demo API to production API
- Prevents accidental demo connection if env var is unset

### Odds API Key Expansion
- Added 2 additional Odds API keys (3 total) for increased rate limit capacity
- Existing key rotation in `odds_api.py` handles this automatically

### Memory System
- Added `.claude/memory/` for cross-session project context
- CLAUDE.md updated to instruct Claude Code to check memory on startup

### Futures Betting Improvements (`scripts/kalshi/futures_edge.py`)
- Added `KXNBA` (NBA Finals Champion), `KXNHL` (Stanley Cup Champion), `KXMLB` (World Series Champion) to futures map — only conference/playoff markets were previously mapped
- Added human-readable labels to all futures: output now shows "NBA Finals Champion: Oklahoma City Thunder" instead of just the ticker
- `--filter nba-futures` now scans Finals champion + both conference winners
- `--filter nfl-futures` cleaned up (removed KXNFLMVP which has no Odds API data)
- Bet type label stored in `details["bet_type"]` and used as the display title
- CLI table shows "Bet Type" column instead of raw ticker
- Updated FUTURES_GUIDE.md with NBA Finals section and corrected filter descriptions

### Per-Game Opportunity Cap (`scripts/kalshi/edge_detector.py`)
- Limits scan results to top 3 opportunities per game (sorted by edge)
- Groups markets by date+matchup extracted from ticker (e.g., all spreads/totals/game for Michigan vs Alabama share one key)
- Prevents a single game from dominating the opportunity list

### PR #14 Review
- Reviewed and rejected Jules-generated PR "Automate Kalshi Betting Pipeline & Optimize Execution"
- Issues: missing `KELLY_FRACTION` constant (runtime crash), no `DRY_RUN` gate on scheduler, missing `apscheduler` dependency, unexplained `cryptography` addition
- Built proper scheduler framework as replacement (see above)

---

## 2026-03-22 -- Live Trading, Prediction Markets, Project Reorganization

### Switched to Live Trading
- Moved from Kalshi demo to live production API
- Set `DRY_RUN=false`, `MAX_BET_SIZE_PREDICTION=5`
- Demo credentials archived in `.env` comments

### Git Repository
- Published to GitHub as private repo: `michaelschecht/Edge-Radar`
- Working branch: `mike_desktop`

### Kalshi Bettor Agent & Skill
- New `.claude/agents/KALSHI_BETTOR.md` -- dedicated Kalshi betting agent
- New `.claude/skills/kalshi-bet/SKILL.md` -- `/kalshi-bet` slash command for scan/execute/settle
- Agent auto-runs status on startup, previews before executing, respects all risk gates

### Financial Analysis Skill
- New `.claude/skills/financial-analysis/` -- research and analysis skill
- Templates: stock analysis, earnings/corporate, global markets, market sentiment, investment strategy

### Futures / Championship Edge Detector (`scripts/kalshi/futures_edge.py`)
- N-way de-vigging of outright odds from 5-12 sportsbooks
- Fuzzy name matching between Kalshi candidates and Odds API outcomes with alias table
- Supported: NFL Super Bowl, NBA conference winners, NHL conference winners, MLB playoffs, NCAAB MOP, PGA golf
- Filter shortcuts: `futures`, `nba-futures`, `nhl-futures`, `mlb-futures`, `ncaab-futures`, `golf-futures`, `nfl-futures`
- Integrated routing from `edge_detector.py` -- `--filter nba-futures` auto-routes to futures scanner
- Browse-only: NBA/NHL awards, Heisman, soccer leagues, F1, NASCAR, IPL

### Unfiltered Scan Fix
- Running the scanner without `--filter` now scans all known sport prefixes instead of pulling 5000 generic multi-event markets
- Results: 959+ sport markets across NBA, NCAAB, MLB, NHL instead of 0

### Sport Filter Expansion
- Expanded `FILTER_SHORTCUTS` from 5 to 27 sports based on live Kalshi market discovery
- Added: NFL, NCAA women's basketball, NCAA football, MLS, Champions League, EPL, La Liga, Serie A, Bundesliga, Ligue 1, UFC, boxing, F1, NASCAR, PGA golf, IPL cricket, individual esports (CS2, LoL)
- Added NBA player props (3PT, rebounds, assists, steals, points) and awards (MVP, ROY, DPOY)
- Added NHL awards (Hart, Norris, Calder)

### Prediction Market Edge Detectors (`scripts/prediction/`)
- **`probability.py`** -- shared math: strike probability (log-normal model), weather probability (normal model), realized volatility
- **`crypto_edge.py`** -- BTC, ETH, XRP, DOGE, SOL edge detection via CoinGecko (free API, with rate limit retry)
- **`weather_edge.py`** -- NYC, Chicago, Miami, Denver temperature markets via NWS API (free, no key). Uncertainty scales with forecast horizon.
- **`spx_edge.py`** -- S&P 500 binary options using Yahoo Finance for price + VIX for implied volatility
- **`mentions_edge.py`** -- TV mention markets: Poisson model for KXLASTWORDCOUNT (word counts), historical YES rate for binary mention markets (KXPOLITICSMENTION, KXFOXNEWSMENTION, KXNBAMENTION)
- **`companies_edge.py`** -- KXBANKRUPTCY (normal distribution vs historical ~750/yr baseline), KXIPO (browse only)
- **`politics_edge.py`** -- KXIMPEACH, KXQUANTUM, KXFUSION: time-decay hazard model with calibrated annual probabilities
- **`prediction_scanner.py`** -- unified CLI scanner with filters: crypto, weather, spx, mentions, companies, politics, techscience, and individual asset/series shortcuts
- All detectors produce the same `Opportunity` dataclass compatible with the existing executor pipeline

### Project Reorganization
- **Scripts:** Moved all Kalshi scripts to `scripts/kalshi/`, new prediction scripts in `scripts/prediction/`
- **Docs:** Reorganized into `docs/kalshi-sports-betting/` and `docs/kalshi-prediction-betting/`
- Fixed all `parent.parent` path resolution for new script depth
- Updated all cross-references across CLAUDE.md, agents, skills, and docs
- Removed local filesystem paths from all committed files

### Architecture Optimization
- **`scripts/shared/opportunity.py`** -- single Opportunity dataclass (was duplicated in edge_detector + prediction_scanner)
- **`scripts/shared/trade_log.py`** -- centralized trade log I/O (was duplicated in executor, settler, edge_detector)
- **`scripts/shared/paths.py`** -- standardized path setup replacing ad-hoc sys.path hacks
- **`scripts/shared/config.py`** -- centralized config: risk limits, scoring weights, model params, all loaded from .env
- **`scripts/shared/logging_setup.py`** -- dual logging to console (INFO+) and daily log file (DEBUG+) in `logs/`
- **`--prediction` flag on executor** -- prediction scanner now feeds directly into the execution pipeline
- **`reconcile` command on settler** -- compares local trade log vs Kalshi API positions, flags discrepancies
- **CLAUDE.md** updated to reflect actual implementation status vs planned features
- **`.env.example`** updated with all actually-used variables

### Odds API Key Rotation (`scripts/shared/odds_api.py`)
- Supports multiple API keys via `ODDS_API_KEYS=key1,key2,key3` in `.env`
- Auto-rotates to next key on 401/429 (exhausted/rate limited)
- Tracks remaining requests per key from response headers
- Warns when a key drops below 10 remaining
- Backwards compatible with single key

### Prompt Library (`prompts/`)
- 18 ready-to-use prompts for agents across 3 categories:
  - `prompts/sports-betting/` (6): daily scan, sport-specific, execute, settle, high conviction, compare
  - `prompts/futures/` (5): championship scan, sport report, weekly tracker, best value, portfolio builder
  - `prompts/predictions/` (7): all predictions, crypto, weather, SPX, mentions, execute, morning brief

### Reports
- `reports/NFL/2026-03-22_superbowl_futures.md` -- Super Bowl analysis (KC NO +1.6% best edge)
- `reports/mlb/2026-03-22_mlb_playoff_futures.md` -- MLB playoffs (Cleveland YES +25.5%, Cincinnati YES +21.0%)
- `reports/NBA/2026-03-22_nba_championship_futures.md` -- NBA championship (OKC YES +26.3% biggest edge across all sports)

### README
- Complete rewrite focused on sports betting, futures, and prediction markets
- Project structure, quick start, all market categories, API reference
- Removed financial-analysis skill (project dedicated to betting)

### Repo Renamed
- `Finance-Agent-Pro` -> `edge-hunter` -> `Edge-Radar`

### New Skills
- `market-mechanics-betting` -- betting theory, Kelly criterion, scoring rules
- `polymarket` -- API reference, trading guides, getting started docs

### Documentation
- `docs/kalshi-sports-betting/BETTING_GUIDE.md` -- comprehensive sport-by-sport guide with all 27 filters
- `docs/kalshi-prediction-betting/PREDICTION_MARKETS_GUIDE.md` -- crypto, weather, S&P 500, mentions, companies, politics, tech/science
- `docs/kalshi-futures-betting/FUTURES_GUIDE.md` -- NFL, NBA, NHL, MLB, golf futures with N-way de-vig
- Updated KALSHI_BETTOR agent and kalshi-bet skill with futures + prediction commands
- Updated all docs to reflect live trading, new script paths, and new commands

---

## 2026-03-18 (Session 2) -- Settlement Tracker, Filters, Unit Sizing

### Settlement Tracker (`scripts/kalshi/kalshi_settler.py`)
- Polls Kalshi settlements API and matches results to trade log
- Falls back to checking individual market status if settlement not yet posted
- Calculates per-trade P&L: revenue, cost, fees, net P&L, ROI, win/loss
- Updates trade log records with `closed_at`, `net_pnl`, `settlement_result`, `settlement_won`
- Saves settlement history to `data/history/kalshi_settlements.json`
- Performance report with: win rate, profit factor, ROI, best/worst trades
- Edge calibration: estimated edge vs. realized edge, realization rate
- Breakdowns by confidence level and market category
- `--detail` flag for per-trade table

### Sport Filtering (`--filter`)
- Added `--filter` flag to both `edge_detector.py scan` and `kalshi_executor.py run`
- Named shortcuts: `ncaamb`, `nba`, `nhl`, `mlb`, `esports`
- Also accepts raw Kalshi ticker prefixes (e.g. `KXHIGHNY`, `KXINX`)
- Only fetches odds for the filtered sport, saving Odds API quota
- Added `KXNCAAMBGAME` to category map and odds sport mapping

### Fixed Unit Sizing
- Replaced Kelly criterion with fixed unit sizing
- Default unit size: $1.00 (configurable via `UNIT_SIZE` in `.env`)
- Contracts = round($unit / price), always at least 1
- Override per run with `--unit-size` flag
- Examples: $0.02 price -> 50 contracts, $0.50 price -> 2 contracts

### Kalshi Client Update
- Added `get_settlements()` method for settlement history endpoint

### Documentation
- `docs/kalshi-sports-betting/USER_GUIDE.md` -- Complete usage guide with filtering and unit sizing sections
- Updated all docs to reflect settlement tracker, filters, and unit sizing

---

## 2026-03-18 (Session 1) -- MVP Pipeline Complete

### Kalshi API Client (`scripts/kalshi/kalshi_client.py`)
- Built authenticated API client with RSA-PSS request signing
- Supports: get_markets, get_market, get_all_open_markets, get_balance, get_positions, get_fills, create_order, cancel_order, get_order, get_orders
- CLI for quick testing (balance, markets, positions, orders, market detail)
- DRY_RUN safety gate blocks live orders on non-demo environments
- Auto-resolves relative key paths from project root
- Tested against demo env -- all endpoints confirmed working

### Edge Detector (`scripts/kalshi/edge_detector.py`)
- Scans 5000+ open Kalshi markets via paginated API calls
- Categorizes markets by ticker prefix: game, spread, total, player_prop, esports, mention, other
- Integrates with The Odds API for sportsbook consensus pricing
- Three edge models implemented:
  - **Game outcomes:** De-vigs h2h odds from 8-12 books, takes median as fair value
  - **Spreads:** Adjusts book spread probability for Kalshi strike difference
  - **Totals:** Adjusts book total probability for Kalshi line difference
- Fuzzy team name matching between Kalshi and Odds API (alias table + substring matching)
- Composite scoring: 40% edge strength, 30% confidence, 20% liquidity, 10% time sensitivity
- CLI: `scan` (batch scan) and `detail` (single market deep dive)
- Saves scored opportunities to `data/watchlists/kalshi_opportunities.json`

### Automated Executor (`scripts/kalshi/kalshi_executor.py`)
- Full scan-to-execution pipeline in one command
- Risk management gates before every order:
  - Daily loss limit check
  - Max open positions check
  - Minimum edge threshold
  - Minimum composite score
  - Confidence level filter
- Quarter-Kelly position sizing with concentration caps
- Executes limit orders on Kalshi, logs all trades
- Trade logging to `data/history/kalshi_trades.json` with full context (edge, fair value, Kelly fraction, fees)
- Portfolio status dashboard: balance, positions, P&L, resting orders, daily activity
- CLI: `run` (preview or execute), `status` (dashboard)

### First Live Demo Execution
- Placed 6 orders on Kalshi demo (1 manual test + 5 automated)
- 5 filled immediately, 1 resting
- Portfolio: $38.44 balance, $59.72 portfolio value, 5 open positions
- Total wagered: $74.09 across NBA games, spreads, MLB

### Configuration & Setup
- Demo API keys configured in `keys/demo/`
- Production API keys stored in `keys/live/`
- `.env` configured for demo environment
- `ODDS_API_KEY` added for The Odds API (free tier, 500 req/month)
- Added `keys/`, `*.key`, `*.pem` to `.gitignore`

### Documentation
- `docs/kalshi-sports-betting/KALSHI_STRATEGY_PLAN.md` -- System overview, pipeline description, remaining work
- `docs/kalshi-sports-betting/KALSHI_API_REFERENCE.md` -- API endpoints, auth, rate limits, CLI reference
- `docs/CHANGELOG.md` -- This file

---

## Pre-2026-03-18 -- Project Foundation

### Existing Before This Session
- `CLAUDE.md` -- Master project manifest with risk limits, agent roster, execution chain
- `.claude/agents/` -- 5 agent specs (MARKET_RESEARCHER, TRADE_EXECUTOR, RISK_MANAGER, DATA_ANALYST, PORTFOLIO_MONITOR)
- `scripts/kalshi/fetch_odds.py` -- The Odds API integration for sports value betting
- `scripts/kalshi/fetch_market_data.py` -- Multi-asset data fetcher (stocks, prediction markets, crypto)
- `scripts/kalshi/risk_check.py` -- Portfolio risk dashboard
- `scripts/sql/init_db.sql` -- Database schema (8 tables, 2 views)
- `.env.example` -- Environment variable template
- `.gitignore` -- Configured for Python, data files, credentials
- `.venv` -- Python virtual environment with dependencies

---

## Archive -- ROADMAP.md as it stood before the 2026-09-29 cleanup

Verbatim copy of the pre-cleanup roadmap (headings demoted two levels). It holds
the performance tables, review findings, shipped/closed/superseded items, the
Completed index and item details that were removed from ROADMAP.md. Item IDs
(S1-S28, B1-B7, PM*, C*, R*, T*, GT*, ...) resolve here.

### Edge-Radar Enhancement Roadmap

*Last updated: 2026-09-15 — **🔴 NEXT UP: S28 — Kalshi now fills fractionally and every fill parser truncates it to zero.** Found 2026-09-15 from an operator question (Kalshi showed a **$0.01 max payout** on two bets the morning email reported as placed): the venue filled **0.01 of 2.00 contracts** on each, with real fees and a real `position_fp`, while `int(float(fill_count_fp))` recorded `contracts: 0` / `$0.00` / `resting` in the trade log. Cosmetic at 0.01, but a **1.99**-contract fill logs as **1** — half a contract of paid-for exposure invisible to settlement P&L and to Gate 2b, the defect class S21 exists to close. Six call sites, not yet fixed; held back deliberately because it touches the money path and the settler. Remaining open items are S26b, the low-value S22-S24 watch list, and Phase 2 (S8 CLV capture). Prior header follows.*

<sub>Previous header - Last updated: 2026-09-07 — **🔴 NEXT UP: nothing new is open.** Shipped 2026-09-07: **college football was never scanned** — `KXNCAAFBGAME` doesn't exist on Kalshi (real series is `KXNCAAFGAME`, plus newly-added `KXNCAAFSPREAD`/`KXNCAAFTOTAL`), so every NCAAF scan silently returned 0 markets since launch; fixed and verified live (3,999 markets found, was 0; 15 opportunities clear the 3% floor in a dry preview). Also made the **account-growth graph private**, reversing 2026-05-31 — it carried real dollar balance/P&L figures and was publishing to the public repo + GitHub Pages; now local-only under the existing gitignored `docs/my-documents/`. Prior git history on `master` still has the old dollar figures — a `git filter-repo` history rewrite was deliberately not done and needs a separate decision. Remaining open items are the low-value S22-S24 watch list and Phase 2 (S8 CLV capture). Prior header follows.*</sub>
<sub>Previous header - Last updated: 2026-09-03 — **🔴 NEXT UP: nothing from the 2026-08-31 review is open** — S20 closed 2026-09-03 (the quota exhaustion was the monthly reset, not a defect; watch MLB's ROI/Brier separately). Remaining open items are the low-value S22-S24 watch list and Phase 2 (S8 CLV capture, blocked on nothing, next in priority order). Prior header follows.*</sub>

<sub>Previous header - Last updated: 2026-08-31 — **🔴 NEXT UP: S20 (Odds API quota / MLB starvation) — the last open defect from the 2026-08-31 review, and it needs a `check_odds_keys.py --live` probe before it can be scoped.** Shipped 2026-08-31: **S18** (the digest’s Brier double-flipped every NO bet — 0.169 reported against a true 0.077 — and printed the market’s Brier under the same label as `betting_analysis.py`’s model Brier; now an explicit pair), **S19 + S19b** (the live-freshness filter excluded **1920/1920 bookmakers on every live event** because the per-event Odds API endpoint puts `last_update` on markets, not bookmakers, while those quotes ran a **median 34s old against a 1200s limit** — and `_live_consensus_too_thin`, the guard built to catch exactly that, sat *after* the empty-list return so the total-wipeout case was the one case it could never see), **S21** (resting orders commit real cash and log `$0`, understating Gate 2b’s ratio in *both* terms; priced from the trade log because v2’s YES-side inversion would have counted an 81c NO at $0.19), and **S25** (the suite had been **red since 08-27** from a fixture ticker whose embedded start time drifted into the past — third instance of wall-clock coupling, first to go unnoticed; now guarded by `test_fixture_hygiene.py`). **1020 tests pass, zero failures.** Watch items S22-S24 remain. Prior header follows.*</sub>

<sub>Previous header - Last updated: 2026-08-31 — **🔴 NEXT UP: S20 (Odds API quota / MLB starvation) then S21 (resting orders invisible to Gate 2b)**. Shipped 2026-08-31: **S18** — the daily digest’s Brier double-flipped every NO bet (`market_price_at_entry` is already side-relative), reporting **0.169 where the truth is 0.077**; it also printed the *market’s* Brier while `betting_analysis.py` printed the *model’s* under the same label (0.169 vs 0.0501, same five bets, same day) — now reported as an explicit pair, and the model figure agrees with `betting_analysis.py` to four decimals. **S19 + S19b** — the L1 live-freshness filter had excluded **1920/1920 bookmakers on every live event** because the per-event Odds API endpoint puts `last_update` on markets, not bookmakers; those quotes had a **median age of 34s against a 1200s limit**, so it caught **zero** stale books in 2888 exclusions. Falls back to the oldest market timestamp; **100% dropped → 0% dropped** on replay, fail-closed intact. S19b: `_live_consensus_too_thin` sat *after* the empty-list return, so the total-wipeout case — the one it existed for — was the one case it could never see. **Both defects were invisible to the suite because the fixtures encoded the same wrong belief**; +15 tests, 996 pass. Open from the 2026-08-31 review: **S20**, **S21**, watch items S22-S24. Prior header follows.*</sub>

<sub>Previous header - Last updated: 2026-08-31 — **🔴 NEXT UP: Priority 0 (S18-S21) — the 2026-08-31 data review found four defects, three of them in the measurement layer Priority 0a depends on.** **S18**: the daily digest’s Brier double-flips NO bets (`market_price_at_entry` is already side-relative), so it printed **0.169 where the truth is 0.077** — and it computes the *market’s* Brier while `betting_analysis.py` prints the *model’s* under the same label (0.169 vs 0.0501, same five bets, same day), which is precisely the comparison F3 rests on and S1b branch A is decided by. **S19**: the L1 live-freshness filter has excluded **100% of bookmakers on every live event all month** (2888 exclusions, all “missing last_update”, **zero** from the age check it was written for) — the per-event endpoint omits the field the sport-level cache carries on 2467/2467 books, `_live_consensus_too_thin` has never fired, and the discarded refreshes burn quota. **S20**: **10 of 12 Odds API keys are exhausted** (828 requests left) and all **166** August key-exhaustion failures are `baseball_mlb` — the largest block in the book, -6.4% ROI, and the only sport whose Brier (0.2917) is flagged worse than a coin flip. **S21**: resting orders lock real cash and log `$0`, so Gate 2b’s exposure total and the digest both under-count committed capital. Watch items S22-S24. Prior header follows.*</sub>

<sub>Previous header - Last updated: 2026-08-27 — **🔴 NEXT UP: S6 (`risk_config_fingerprint`) + S2 (legacy-book reporting) close Phase 1; then Phase 2 S8 (CLV capture)**. Shipped 2026-08-27: **X1** (just-in-time cash movement between Kalshi exchange shards) and **S3a** (the test suite was silently overwriting the live S3 eligibility cache). Kalshi **sharded the exchange on 2026-08-24** — Crypto to shard 2, Tennis & Baseball to shard 3 — and cash does not follow the markets, so every MLB order was failing `404 user_not_found` until $15 was transferred; sizing stays whole-account by operator's call. Shipped 2026-08-26: **S1** (NFL freeze) + **S1b** (dated 09-15 auto-review), **S5** (Gate 3.7 time-to-event cap), **S4** (Gate 2b cumulative exposure ceilings, live 0.50/0.33), **S3** (venue eligibility preflight, fail closed) (from the [2026-08-26 betting-strategy review](./enhancements/betting-strategy-review-2026-08-26.md): the lifetime ROI CI contains zero, CLV has never once been computed, and 31% of bankroll sits in a pre-L2 NFL book. The Polymarket build is unchanged but now ranks behind it as Priority 0b.)*</sub>

<sub>Previous header - *Last updated: 2026-07-27 — **🔴 NEXT UP: Polymarket integration** (Priority 0 below — the account is approved + funded; highest-priority active build; **PM2c DONE 2026-07-20 (same session as PM2c-0): execution pipeline fully wired** — `scan.py polymarket --execute` routes US-slug futures opps through the shared `execute_pipeline` (`venue="polymarket"`): Kelly sizing, all gates, venue min-share bump/reject (`minimumTradeQty` captured scan-time), venue-tagged trade log, Gamma games auto-excluded. Live-verified against the funded account (2 US positions counted via normalized `market_positions`; Spurs edge correctly gate-rejected). **Safety: orders stay `dry_run_blocked` behind the new two-flag rule — live only when `DRY_RUN=false` AND `POLYMARKET_DRY_RUN=false` (venue flag defaults true)** — so Kalshi runs live while Polymarket accumulates dry-run evidence. Next: let the daily dry-run window prove edge → deliberately flip `POLYMARKET_DRY_RUN=false` for first live orders; the games repoint is a deferred seasonal follow-on (US game markets are moneyline-only — no spreads/totals/MLB); then PM3 settlement/ops. 635 tests. Shipped 2026-07-20: **PM1b** (slugs + search fallback), **PM1c** (evidence log + daily task), **PM2a** (MarketClient seam), and **PM1d** — per-game ML/spread/total edge detection (the PM0 "no game markets" finding was wrong; games exist behind tag_id filtering and now price through the same calibrated consensus model as Kalshi sports; games settle daily so the edge window can validate on real settlements in weeks). 587 tests). **Later session (2026-07-20):** shipped **PM1b** — all four Gamma slugs (NFL/MLB/NBA/NHL) found + wired; `find_event` fallback replaced with `/public-search` (volume-preferred, season-rollover-proof, live-proven from dead slugs); full config now prices end-to-end — and **PM1c** — `--save` now persists each dry-run scan (JSONL evidence log w/ gate verdicts + `reports/Polymarket/` markdown) so the Phase 2 gate can actually be proven (557 tests). **Earlier session (2026-07-20):** closed **M1** (MLB recheck — crowding confirmed fixed, gates correctly holding, no tuning), **M2** (cross-process trade-log lock + merge-safe append), and five 2026-07-14 review residuals — **#3** longshot-report crash guard, **#6** Odds-API-key log redaction, **#7** execute-batch network resilience, **#8** per-trade settlement revenue (no double-count), **#9** unified revenue normalization. 550 tests. Prior 2026-07-14: repo review + 3 money-path fixes, config reconcile, MIN_MARKET_PRICE 0.06→0.12, Polymarket Phase 1. **Still open from the review (lower value):** #4 composite-formula regression test, doc-trailing (Wimbledon matrix / Gate 4.8), unused-import cruft, Low-severity #10/#12/#13/#14/#16. The full ship-by-ship history lives in the [Completed](#completed) index below — keep new entries there, not on this line.*</sub>

All pending improvements for Edge-Radar in a single prioritized action list, plus findings/context behind them and an index of completed work.

Priority framing (from 2026-04-02 assessment):

> Edge-Radar does not primarily need more features right now. It needs tighter execution truth, stronger measurement, and a simpler operating surface.

Priority order: **execution correctness → calibration → risk controls → data quality → UX → features.**

Source context: 3rd-party assessments (`edge_radar_assessment_2026-04-02.md`, `edge_radar_assessment_2026-04-04.md`, `edge-radar-web-app-recommendations_2026-04-04.md`), 2026-04-18 calibration report, 2026-04-21 14-day review, 2026-04-22 repository analysis (`edge_radar_repository_analysis_2026-04-22.md`), 2026-04-24 30-day review (`reports/Performance/betting_analysis_2026-04-24_30d.md`).

---

#### Current Performance

| Metric | At Launch (03-22) | Interim (04-02) | Post-Baseline (04-18) | 14-Day (04-21) | 30-Day (04-24) | 90-Day (06-23) |
|--------|-------------------|-----------------|------------------------|-----------------|-----------------|-----------------|
| Sample | 12 bets | 54 bets | 70 bets (since 04-03 baseline) | 76 settled (last 14d) | **160 settled (last 30d)** | **302 settled (cumulative)** |
| Win rate | 8% (1/12) | 46% (25-29) | 51% (36-34) | 48.7% (37-39) | **50.0% (80-80)** | **48.3% (146-156)** |
| ROI | -88% | +29.3% | +20.3% | +31.2% ($19.55 P&L) | **+37.4% ($43.48 P&L)** | **+29.1% (+$78.21 P&L)** |
| Brier score | n/a | n/a | 0.2561 | 0.2646 | **0.2657** | **0.2513** (closer to 0.2500) |
| CLV | not tracked | tracking | tracking | tracking | tracking | **tracking** |

Aggregate ROI is solid at +29.1% but relies heavily on MLS (+137.3%) and NHL (+62.1%). NBA remains a significant underperformer at -23.3%. Brier score has improved to 0.2513 (closer to 0.2500, but still lacks strong predictive resolution). In addition, a stark asymmetry exists between YES (+48.1% ROI) and NO (-7.0% ROI) contracts.

**Update 2026-08-25 (calibration study, 380 settled, full settlement-log history).** Cumulative
**+10.0% ROI** ($381.66 staked, +$38.01) -- **+5.7% net of the fees F1 made visible**, which
consume 43% of the gross return. The YES/NO asymmetry above is confirmed and larger than F45
measured: **YES +22.4% vs NO -7.7%**, with YES ahead *within every shared price band* (acted on
as F4). Two structural facts the earlier reviews did not surface:

- **The Kalshi ask beats the model's fair value on Brier in 6 of 6 months** (0.2037 vs 0.2270;
  95% CI on the difference excludes zero). The Brier-optimal weight on the claimed edge is
  **lambda = 0.16, CI [-0.04, +0.42]** -- roughly a sixth of each claimed edge is supported by
  outcomes, and zero is inside the interval.
- **Mar-May +28.2% -> Jun-Aug -17.5% is a composition change, not decay.** NCAAMB (+26.9%,
  n=56) and MLS (+130.7%, n=35) carried the good months; NCAAMB's season ended. What remains is
  MLB (negative in both eras, largest block at $161 staked) and World Cup (-43.2%, now off).

Re-run with `python scripts/backtest/calibration_study.py`. Full writeup:
`docs/my-documents/repo-reviews/2026-08-25-calibration-study.md`.

**Update 2026-08-26 (strategy review, 402 settles, full settlement log).** Lifetime
**+$54.04 on $381.66 staked (+14.2% ROI, 46.5% win rate)** -- but the 95% bootstrap CI on that
ROI is **[-6.2%, +36.8%]** and it contains zero. Removing the five largest winners turns the
book **negative (-$8.15)**; three of the top four are sub-10c MLS spread longshots. Treat every
per-sport and per-band ROI in the table above as a concentration artifact -- excluding each
sport's own top 3 bets, MLS falls +76.5% -> +8.4%, NHL +62.1% -> +22.0%, NCAAMB +21.7% -> -2.4%.
**There is no winner to keep; "prune to the profitable sports" is not an available move.**

- **The regime broke in June.** Mar-May +32.3% (n=274) vs Jun-Aug **-13.2%** (n=128),
  permutation p = 0.018 one-sided. The bleed is broad, not localised -- YES (-16.2%),
  SPREAD (-28.2%), TOTAL (-13.3%) and the 5-15% claimed-edge bucket (-20.1%) are *all* negative
  Jun-Aug. A static gate tuned on Mar-May is tuned on a distribution that no longer exists.
- **Claimed edge is non-monotone against outcomes.** The >=20% claimed-edge bucket has the
  *worst* win rate in the book (34.8%, n=89) while 8-12% returns +30.0%. The gates have an edge
  floor and **no ceiling**: a row claiming 40% edge clears Gate 3 and is Kelly-sized off a number
  the record says is mostly fantasy.
- **Fees are 3.14% of stake and every order is a taker** (0 maker fills in 169 trades). At F3's
  lambda = 0.16, a row claiming 10% edge carries ~1.6% of trusted edge against a 3.14% toll.
  **The system is structurally negative-EV as a pure taker.**
- **CLV has never been computed** -- 150 settlements, 150 zeros (see S8/D1). Realized ROI at a
  $0.80 median stake cannot resolve this question; CLV can, in ~90 days.
- **Every figure above was generated by a looser filter than the one now running** (D6): F1
  folded the exchange fee into the Gate 3 floor on 2026-08-25. The live and historical systems
  are not the same system.

Full writeup: `docs/enhancements/betting-strategy-review-2026-08-26.md`.

---

#### Action Items (Consolidated)

One unified list. Items from retired sections (C1a, R-series, S/H/M/U/D/A/T tiers) have been merged, deduplicated against each other, and re-sorted by priority. Old IDs preserved so existing commits / comments still resolve.

##### Priority 0 — 🔴 Measurement & Data-Path Defects (2026-08-31 data review)

**Ahead of Priority 0a**, because three of these four corrupt the *instruments* 0a depends on.
Source: 2026-08-31 review of the trailing week's trades, settlements, logs, reports and live
config. Premise: Priority 0a's whole thesis is that **CLV and Brier are the only readable signals
at this sample size** — so a Brier that is silently wrong, a book-consensus filter that discards
100% of its input, and an exposure total that omits committed cash are not reporting bugs, they
are load-bearing. Each item below was verified against the live artifacts, not read off a doc.

| ID | Item | Impact | Effort | Notes |
|----|------|--------|--------|-------|
| **S28** | **Kalshi fills fractionally now — every fill parser truncates it to zero** | High | Small | **FOUND 2026-09-15, not yet fixed** (operator asked why Kalshi showed a **$0.01 max payout** on two bets the morning email reported as placed). Kalshi filled **0.01 contracts** of each of `KXMLBTOTAL-26SEP151940ATLCHC-12` (NO @73c) and `KXMLBTOTAL-26SEP151840MILPIT-11` (NO @72c): `initial_count_fp 2.00`, `fill_count_fp 0.01`, `remaining_count_fp 1.99`, with real `taker_fees_dollars 0.000100` and a live `position_fp` of `-0.01` on each. The venue was right; **our log was not** — both rows record `filled_contracts: 0`, `cost_dollars: 0.0`, `fill_status: "resting"`. Cause is one expression repeated at six sites: **`int(float(fill_count_fp))`**, and `int(float("0.01")) == 0` — `kalshi_executor.py:379`, `:967`, `:1515`, `:1561-1562`, `:1807`, and `recover_trade_log.py:68`. **The $0.02 here is not the risk.** A **1.99**-contract fill truncates to **1** — half a contract of real, paid-for exposure invisible to the trade log, to settlement P&L, and to Gate 2b's standing total, which is the exact class of defect S21 was built to close. **Second-order:** `:967` is R4's resting-order janitor; it reads `0.01` as `0`, so it will cancel these as "zero-fill" at 24h and orphan the position with no log row. **Third:** `:1567`'s `if fill_count == 0` is what mislabelled these as `resting`, so `fill_status` cannot currently express a fractional partial. Fix is `int(float(...))` → `float(...)` at all six, `== 0` → `<= 0` for the status branch, and a check that the settler's `contracts` math and every digest/report formatter tolerate a non-integer. Deliberately **not shipped the same day** — it touches the money path and the settler, and the two live orders were still resting into that evening's games. *Verify:* replay a `fill_count_fp` of `0.01` and of `1.99` through `_build_trade_row` and assert `contracts` comes back `0.01` / `1.99`, not `0` / `1`; then reconcile the two 09-15 rows against `position_fp` after settlement. |
| ~~**S18**~~ | **The daily-digest Brier double-flips NO bets — wrong since U2** | High | XS | **SHIPPED 2026-08-31.** Flip removed; the single `brier` key is now `brier_market` / `brier_model` with an `n` beside each, and the digest prints them as a pair (`Brier model 0.050 vs market 0.077` on the live 7d window, where it had reported `Brier 0.169`). The model figure now agrees with `betting_analysis.py` to four decimals — the cross-check that the two reports finally describe the same world. **Why it survived:** the existing test priced every bet at 50c, where a flip is invisible; the new NO-side test uses 80c. +4 tests. Original note: `scripts/kalshi/daily_summary.py:237-239` computes `predicted = price if side != "no" else 1.0 - price`. **`market_price_at_entry` is already side-relative** — verified across the whole settlement log: **0 of 133 NO-side rows** violate `fair_value - market_price_at_entry == edge_estimated`. So the flip turns a 73c NO into 0.27 and scores it against a win. The 2026-08-31 email reported **Brier 0.169**; the correct value on the same five bets is **0.077**. **33% of all 407 settled bets are NO-side**, so every window containing one has been overstated for as long as the digest has existed. Fix is a three-line delete. **Second defect in the same block, and the worse one long-term:** this computes the **market's** Brier (predicted = market price) while `betting_analysis.py:236` computes the **model's** (predicted = `fair_value`) — the two reports printed **0.169 and 0.0501 under the same label "Brier" for the same five bets on the same day**. F3's entire finding is *model Brier vs market Brier*, and S1b branch A is decided on exactly that comparison; two different quantities sharing one label is how that call gets made on the wrong number. Rename both, or print them as a pair. *Verify:* recompute the 7d digest against `betting_analysis.py` and require the market/model split to be explicit in both. |
| ~~**S19**~~ | **The L1 live-freshness filter discards 100% of books on every live event** | High | Small | **SHIPPED 2026-08-31, with S19b.** Confirmed from the 327 real per-event payloads in `data/cache/odds/events/`, not inferred: **1920/1920 bookmakers carry no top-level `last_update`** while **5252/5252 markets do**, at a median quote age of **34s** against the 1200s limit — so the filter was rejecting fresh books for want of a field the per-event endpoint simply does not send. New `_bookmaker_last_update()` falls back to the **oldest** market timestamp (operator's call — a bookmaker is only as fresh as its stalest market, which keeps the fail-closed intent). Replaying those same 1920 bookmakers: **100% dropped → 0% dropped**, with a book carrying no timestamp *anywhere* still excluded. **S19b — the guard was blind to its own worst case:** all three consensus functions ran `if not <data>: return None` **before** `_live_consensus_too_thin`, so a total wipeout short-circuited on the empty list and never reached the guard; it only ever fired when 1-2 books survived, which is why it had not logged once in 2888 exclusions. Reordered at all three sites, and it still no-ops when `n_excluded == 0` so a genuine "no books matched" is unchanged. **+11 tests, 4 of which fail without the fix**; the other 7 guard against over-correction and pass either way by design. One replays every cached payload on disk, so the fixtures cannot drift from what the API actually sends. **The wrong belief was in the fixtures too** (`test_edge_detection.py:516`) — every one modelled the sport-level shape, which is exactly why the per-event shape was never exercised; corrected in both places. **Shrinks S20:** those discarded refreshes were spending quota. 996 pass. Original note: `edge_detector.py:445-457` excludes any bookmaker whose `last_update` is missing. Log counts: **1204 exclusions on 08-29, 956 on 08-30, 728 on 08-26 — every single one `missing/unparseable last_update (None)`, and zero from the actual age check** in the entire month. It has never once done the job it was written for. The code comment asserts *"The Odds API event endpoint returns last_update on every real response, so this only fires on malformed/mocked data"* — **empirically false**: it fires on every live event routed through `_refresh_event_if_live` → `fetch_event_odds_api` (the per-event `/events/{id}/odds` endpoint). Meanwhile the sport-level cache carries `last_update` on **2467/2467 bookmakers and on every market object**, so the fix is a fallback to `market["last_update"]` before excluding. **Two knock-ons:** (1) `_live_consensus_too_thin` — the guard written to catch exactly this — has **never logged once** despite consensus being stripped to zero books, so the backstop is also dead; (2) the per-event refresh **spends Odds API quota on responses that are then 100% discarded**, which feeds S20. Currently harmless to P&L *only* because `ALLOW_LIVE_BETS=false` (S7 holds it there) — this is a live landmine under the L1 in-play work, not a cosmetic one. *Verify:* age-based exclusions must become non-zero and missing-field exclusions near-zero on the next live slate; assert `_live_consensus_too_thin` fires on a synthetic all-stale event. |
| ~~**S20**~~ | **10 of 12 Odds API keys exhausted — and MLB is what starves** | High | Small | **ANSWERED 2026-09-10 (S20b) — the quota-starvation explanation for MLB does not survive testing.** The check S20 specified ("log `n_books` ... check whether the failure days coincide with the losing trades") **was never possible**: `n_books` is computed at scan time and discarded, appearing in no trade or settlement row, ever. Proxied instead with Odds-API exhaustion **days** recovered from log lines — which turn out to number **577 events over 37 days (2026-04-18..09-10), all of them `baseball_mlb`**, not the 166 August events S20 counted, with the pool already collapsed to 4 or 1 keys at every failure. Split over 153 settled MLB bets: exhaustion days **-11.2% ROI** vs clean **-2.0%**, but the **ROI difference is -9.2%, CI [-47.2%, +30.4%]** and the **Brier-gap difference +0.0161, CI [-0.0278, +0.0614]** — both straddle zero — and per month exhaustion days are **worse in 3 of 6 and better in 3 of 6**. A pooled difference that flips sign per stratum is not a finding (same lesson as `correlation_check.py`'s +0.181 pooled rho). A first pass using `trade_id` gave the opposite answer and was wrong: the trade log is pruned (193 rows vs 426 settlements), so two thirds of rows silently dropped; dating from the ticker's game date recovers all 153. **Does not clear the MLB model** — it is worse than the market in both arms (+0.0437 / +0.0276, cf. F3) — it says the cause is a model question, not a data-supply one. **Now instrumented:** `n_books` persists on trade and settlement rows, and `scripts/backtest/book_width_check.py` runs both the proxy and the direct split (+30 tests). **S20c (same day) closes the MLB question and cancels the follow-on gate.** MLB is **not** unfloored — that claim came from S20 and was repeated here in error. Every path drops thin rows to `low`, which Gate 4.5 rejects: MLB is `n_books >= 5` on moneyline, `>= 3` on totals; R29 did not omit MLB, it **raised NBA's from 5 to 8** because F46 named NBA. Copying 8 was never portable anyway — only **9 books ever arrive** (`regions=us`; Pinnacle/Circa are `eu`, see B7) and in-season MLB runs **median 7**, so an 8-floor would reject over half of MLB. **And MLB's loss is not consensus at all:** by category, moneyline **+1.2%** (n=109), totals **-12.8%** (n=42) — the entire headline loss is totals, which wins **71%** while losing money, because **33 of 42 are NO bets at a median 0.80 entry** (F4's worst band). **Already gated:** `MAX_MARKET_PRICE=0.75` (Gate 3.55, 2026-09-03) — verified no leak, the only post-ship passes are 0.74 and 0.75, and the two at 0.81/0.79 were entered on 09-03 itself. No gate written: it would target a cause that could not be found, on top of one already gated, at a threshold nothing supports. **Still open:** re-run the direct mode once rows carry `n_books`; the **totals path floors at 3 while moneyline floors at 5** with no recorded reason (a consistency fix, not an evidenced one); re-check MLB after ~20 more settled totals (n=4 post-gate proves nothing); and **B7 gates all of it** — adding `eu` books changes what any book count means. Superseded detail: **REOPENED 2026-09-09 — the 09-03 closure does not follow from its evidence.** It closed on **zero** `All N Odds API keys returned 401/429` errors in the 09-01..09-03 logs. That silence is confounded by **S26**: with `...deb642` still holding quota, `get_current_key()` never reached a cached-zero key, so no 401 could be logged **whether or not anything had reset**. Silence was the bug's signature, not proof of recovery — and S20's own *Verify* line called for the `--live` probe that was never run. Run on 09-09 it found **5154 requests available across 9 keys at a full 500**, with the cache still reading 12 of 14 at zero. **What survives:** the keys were not permanently dead and the alarm was rightly stood down. **What does not:** the stated mechanism, and with it the premise for the MLB question below. **Still open, and now the actual question:** MLB's -6.4% ROI / 0.2917 Brier was measured over a period when the key pool was collapsed to one key by S26, not merely thinned by exhaustion — so quota-starved consensus is *more* plausible as a cause than S20 concluded, not less. Re-measure MLB `n_books` now that the pool is genuinely 14 wide before touching the model. Superseded detail: **CLOSED 2026-09-03.** No code change — the quota problem was the monthly reset. Keys grew 12→14 (operator added 2), and **zero** `All N Odds API keys returned 401/429` errors appear in the 09-01 through 09-03 logs, against 4-48/day through August. Confirmed by log inspection, not a `--live` probe. **Still open, separately:** whether MLB's -6.4% ROI / 0.2917 Brier was actually quota-driven or a real model problem now unmasked — this closure only rules out *ongoing* starvation; revisit if MLB doesn't improve. Original note: `data/cache/odds_api_quota.json`: **10 keys at 0 remaining, 828 requests left across the other two.** In August the logs carry **166 `All N Odds API keys returned 401/429`, and every one of them is `for baseball_mlb`** — no other sport appears, across seven separate days (08-01, 08-18, 08-19, 08-24, 08-25, 08-26, 08-27). MLB is systematically last in the scan order and eats the shortfall. **This is plausibly the same fact as MLB's performance:** MLB is the largest block in the book (143 settled, $161 staked, **-6.4% ROI**) and the 30d calibration report flags its **Brier 0.2917 with `*` — worse than a coin flip**, the only sport so flagged. A sport priced off a book thinned by quota failure is not a sport with a bad model; the two are indistinguishable from the current logs, which is itself the problem. **There is no `MIN_CONSENSUS_BOOKS_MLB`** — R29 built that guard for NBA only, so MLB has no floor under how thin its consensus may get before it still emits an edge. *Verify:* `check_odds_keys.py --live` to separate a stale cache from real exhaustion; then log `n_books` on every MLB edge and check whether the failure days coincide with the losing trades before touching the model. |
| ~~**S21**~~ | **Resting orders lock real cash and log $0 — Gate 2b under-counts** | Medium | Small | **SHIPPED 2026-08-31.** `resting_exposure()` returns the same `(total, by_segment)` shape as `exposure_from_positions`; both are folded into equity **and** exposure before Gate 2b, because a resting order understates the ratio in *both* terms — its cash has left `balance` without reaching `portfolio_value` or the positions list. **Price comes from our own trade log, not the venue, and that is the design:** v2 expresses every order YES-side, so an 81c NO rests as an `ask` at 0.19 — pricing off the venue payload without inverting counts **$0.19/contract instead of $0.81**, a 4x under-count in the one gate this tightens. The inversion could not be verified against a live resting order, so it is not in the code at all; the log already stores `price_cents` bet-side, so the `order_id` join needs no inversion. A test pins the trap. An unpriceable order (hand-placed on iOS) is counted at **$1.00/contract worst case** and warned — skipping it would reproduce the under-count, and over-stating only tightens. Fails **open** with a warning if the venue listing is down (exposure is a sizing input, not a legality check — contrast S3). Verified live: 28 positions, $36.30 exposure, $122.62 equity, 0 resting → ratio unchanged at 29.6%, no false positives. +14 tests. Original note: `KXMLBTOTAL-26AUG311940MILCHC-14` (08-31 03:30): `requested_contracts 3`, `requested_cost $2.43`, `remaining_count 3` — but `contracts: 0`, `cost_dollars: 0.00`. The venue is holding the cash: `doctor.py` reads shard 3 at **$12.57**, down **exactly $2.43** from the $15.00 recorded on 08-27. The 08-31 digest reports "$31.04 at risk" and omits it entirely. **So every consumer of committed capital — the digest, and S4's Gate 2b exposure total — is short by the value of every open resting order.** Small in absolute terms today ($2.43), but it is the same class of defect S4 was built to close: a standing total that no gate measures. Note this is *not* the same as an unfilled order costing nothing — R4 (`RESTING_ORDER_MAX_HOURS=24`) will not cancel this one before its market closes, so the cash sits committed for the market's life. **Also unreconciled:** if a resting order later partially fills, the trade row still reads 0 contracts and settlement would price P&L off 0. *Verify:* sum `requested_cost` on `fill_status == "resting"` rows into the Gate 2b denominator and the digest, and confirm against the per-shard balances in `doctor.py`. |

| ~~**S26**~~ | **A cached Odds API zero was believed forever, hoarding one key** | High | Small | **SHIPPED 2026-09-09.** `data/cache/odds_api_quota.json` held a bare `{key: remaining}` map with **no timestamp and no expiry**, while `get_current_key()` returns the first key not cached at zero — so as long as *one* key had quota the walk stopped there and every drained key was never contacted again. The `if every key is exhausted, try anyway` fallback only fires when **all** read zero, which never happened. The pool silently collapsed from 14 usable keys to one: `...deb642` carried the whole workload while `futures_edge` logged `1 requests remaining` on 09-09 and a `--live` probe found **5154 requests actually available** (9 keys at a full 500). Entries are now `{remaining, checked_at}`; a zero older than `_ZERO_TTL_HOURS` (24) loads as *unknown* so the key is re-probed, non-zero readings never expire (refreshed on use), and legacy bare ints still load — a legacy zero is undateable so it expires by definition, which migrates the live cache on first read. New `WeeklyOddsKeyProbe` task (Sun 6 PM, gitignored `.bat`) runs `check_odds_keys.py --live`: 14 requests/week, catches a key going bad **before** a scan needs it. **Rejected: picking the key with the most remaining** — it does not fix this (a cached zero still ranks last and is still never picked) and it fights the `tried:` set in `edge_detector.py`'s retry loop, where snapping back after a 429 would end the loop early. **Reopens S20.** +6 tests (`test_odds_quota_ttl.py`); 3 cases in `test_odds_api.py` asserted the old bare-int format. 1039 pass. |
| **S26b** | **The Odds API reset model is unresolved — and one key 401s** | Medium | XS | Two loose ends from S26, neither load-bearing for the fix (the TTL is correct under either model). **(1) Reset cadence.** S20 states the quota resets on the 1st; the 09-09 probe found *heterogeneous* `x-requests-used` on the same day — **0** (nine keys), **84**, **263**, **499**, **500**. A synchronized 1st-of-month reset does not obviously explain the keys reading 263 and ~500 used, since those were cached at zero and should have been skipped all month. **`rotate_key()` was the obvious candidate for a path that bypasses the zero-skip and is RULED OUT** — all three call sites (`edge_detector.py:280`, `:354`, `futures_edge.py:196`) discard its return value and re-enter via `get_current_key()`, which re-applies the skip. The remaining benign explanation is that `_remaining` is per-process state that starts from the cache and is updated live: a key **absent** from the cache reads as usable (`.get(key, 1)`), and once every key reads zero in-process the documented fallback returns the current slot anyway — so a reset does get re-discovered, one key at a time, for whichever slot `_current_index` happens to hold. That fits the observed spread under **either** reset model, so the used counts do not discriminate between them at all. Resolve by recording `x-requests-used` per key daily for one cycle — `WeeklyOddsKeyProbe` already writes the readings, it just needs them kept rather than overwritten. Until then **assert neither model in docs**. **(2) Key `...44681c` returns 401** — the only key in the set with an uppercase character in an otherwise all-lowercase-hex list, so a transcription error in `ODDS_API_KEYS` is likelier than a revocation. Check it against the source. Keys `...a630b6` / `...8e4b0a` are genuinely drained (500/499 used) and are not part of this. |
| ~~**S27**~~ | **Gate 2b's resting-order call ran on a venue with no orders endpoint** | Medium | XS | **SHIPPED 2026-09-09.** A daily WARNING at 09:40 said `Gate 2b will under-count by any open resting order`, which reads as Kalshi going blind in the one gate that measures a standing total. It is not Kalshi: `/v1/orders` is the **Polymarket US** path and 09:40 is `Daily-Polymarket-Execution` (#21). `execute_pipeline` is venue-agnostic; the R4 janitor two lines up was already gated `venue == "kalshi"`, but **S21's `resting_exposure()` was not**, so every PM run since 08-31 asked a venue that answers 501 / gRPC code 12 **UNIMPLEMENTED** -- deterministic, never going to succeed. **Under-count is $0** (PM has never filled an order), so the defect is the warning itself: an unconditional line is the **S25** failure mode, and it was training the reader to skip the exact string Kalshi would use if *its* listing ever broke. Now behind the same venue guard; other venues log one INFO naming the limitation. Kalshi's listing verified working the same day via `risk_check.py`. +2 tests pinning S21's fail-open contract; the one-line guard is deliberately untested (the janitor's identical guard is too -- reaching it needs a full authenticated round-trip). |
| ~~**S25**~~ | **The test suite had been red for four days and nobody read it** | High | Small | **SHIPPED 2026-08-31.** `make test` broke on **2026-08-27** and was found four days later during an unrelated review. No code changed — `KXMLBGAME-26AUG271900NYYBOS-NYY` in `test_exposure_gate.py` embeds a **start time**, so at 7pm on the 27th `is_game_started()` flipped and Gate 4.8 rejected the order five tests were asserting about. **Third instance of wall-clock coupling** (S1 broke 4 tests, S5 broke 126) and the first to go unnoticed, because a suite with standing failures stops being read. Fixture moved to the year-99 idiom `test_risk_gates.py` already used, and `tests/test_fixture_hygiene.py` makes it enforceable: no fixture ticker carrying a **start time** may sit within 90 days of today — flagged a quarter before it detonates, verified by planting a bomb and watching it fail. Scoped to HHMM tickers and forward-looking only; an earlier draft flagged ~50 fixtures that cannot affect a verdict, and a check that cries wolf gets deleted. **Correction to this review's own claim:** the nine "Sept-13 bombs" were wrong — those tickers are date-only, and `is_game_started` returns False rather than guess a kickoff, so they were never Gate 4.8 bombs. The urgency was right, the mechanism was not; settled with a probe that ran the suite against a shifted clock. **1020 pass, zero failures — green for the first time since 08-27.** |

**Watch items — logged, not yet actionable:**

| ID | Item | Impact | Effort | Notes |
|----|------|--------|--------|-------|
| **S22** | **`MIN_MARKET_PRICE=0.10` took its first loss; and ROI can print worse than -100%** | Low | XS | The live 0.10 is an open experiment re-opening the longshot lane (recheck after ~30 more settles). First data point: `KXMLSSPREAD-26AUG30STLDAL-DAL2` @ 11c, 9 contracts, **-$1.06 on a $0.99 stake**. n=1, no action. **The reporting artifact is worth fixing though:** `net_pnl` subtracts fees while the ROI denominator is cost-only, so a total loss prints **-107.1%** in the digest, the 7d analysis and the trade ledger. A number that cannot exist makes a correct report look broken — divide by `cost + fees`. |
| **S23** | **Equity has drifted from every doc that quotes it** | Low | XS | CLAUDE.md and the Risk Limits block quote **$121.83 equity / $88.06 cash ($73.07 shard 0 + $15.00 shard 3)**, verified 2026-08-27. `doctor.py` on 08-31 reads **$82.64 cash ($70.07 + $12.57)**, ~$31 in positions, **equity ≈ $114**. Not a defect — deposits and fills move it — but it is the fourth doc-drift instance in a week and it is quoted in a *sizing* context. **This is S6's argument, restated:** the fix is not another sweep, it is that `doctor.py` is the only surface allowed to state a balance. |
| **S24** | **MLS Sep-5 LA Galaxy vs New England silently emits no edge** | Low | XS | All ten `KXMLSSPREAD/TOTAL-26SEP05LAGNE-*` tickers log `find_market_event: 0 candidate events on 2026-09-05 — series/absent/ambiguous`. Real fixture, so this is a team-name mapping or matching-window miss, not an absent market. Low value on its own; worth a look because a silent `emitting no edge` is indistinguishable from "no edge exists" in every downstream report. |

##### Priority 0a — 🔴 Capital Preservation & CLV Measurement (2026-08-26 strategy review)

**Now the #1 item on this roadmap**, ahead of the Polymarket build. Source:
[`docs/enhancements/betting-strategy-review-2026-08-26.md`](./enhancements/betting-strategy-review-2026-08-26.md)
(claude-code + codex, agent-chat conv #54). Premise: the system is **structurally negative-EV as a
pure taker** (trusted edge ~1.6% against a 3.14% fee toll) and the 402-settle record is **not large
enough to prove otherwise in either direction**. So: stop preventable waste, install the instrument
that can settle the question in months instead of years, remove the structural cost of trading —
and only then scale. **These items deliberately do not tune thresholds.**

Six design decisions constrain everything below: (1) rolling policy may only ever *tighten*, never
loosen — a trailing window that can loosen a gate will overfit whichever slice just got lucky;
(2) every segment policy carries `last_settled_at` and an expiry (NBA/NHL/NCAAMB are out of season
as of 2026-08-26 — a demotion written today would still be enforcing a 32-bet April sample in
October); (3) `insufficient_evidence` is not `negative_clv` — different reasons, different exits;
(4) cold start means pilot mode, not prohibition; (5) legacy positions are quarantined from
performance claims in **both** directions; (6) new gate logic runs in shadow for one full cycle
before it rejects anything. **Every item names its verification step, because of S6/D4.**

**Phase 1 — stop preventable waste (this week, no evidence required):**

| ID | Item | Impact | Effort | Notes |
|----|------|--------|--------|-------|
| ~~**S1**~~ | **Freeze new NFL live entries** | High | XS | **SHIPPED 2026-08-26.** `MIN_EDGE_THRESHOLD_NFL=1.0` live; verified in-process on all three NFL prefixes (`KXNFLGAME`/`KXNFLSPREAD`/`KXNFLTOTAL` -> `preflight=off`, `REJECTED: sport_disabled`), MLB unaffected. No `--min-edge` in any executing scheduler `.bat`, so it reaches the automation (checked per D4). Two things the freeze exposed and fixed: `doctor.py` could truncate a switched-off sport off the right edge at narrow terminal width (disabled sports now get their own WARN line), and the test suite inherited operator `.env` freezes -- four tests using NFL tickers as fixtures broke on a config change that touched no code (new autouse `_ignore_operator_sport_freezes` in `tests/conftest.py`; 864 pass). A scan preview showing NFL `off` needs NFL rows with edges -- the 08-27 preseason slate has no Odds API coverage, so that lands on a Week 1 scan. Original note: | `MIN_EDGE_THRESHOLD_NFL=1.0` (the F3 World-Cup idiom — a floor >= 1.0 can never be cleared). **A freeze mechanism, not NFL policy:** NFL holds 24 open live positions with **zero settled history**, and its `margin_stdev: 13.5` in `data/cache/calibration_stdevs.json` is a hardcoded prior, not a fit (contrast `baseball_mlb: 4.025`, `icehockey_nhl: 2.5`, which carry the decimals of something computed). The key comes back out the moment S10 ships — the durable rule is strategy-state `cold_start` -> pilot, not an impossible threshold left in `.env` forever (that is D4 waiting to happen again). *Verify:* `doctor.py`; scan preview shows NFL `off`. |
| **S1b** | **NFL Week 1 review — DATED: Tuesday 2026-09-15** | High | Small | **ARMED 2026-08-26** — Windows task `\Edge-Radar-MikesAILab\NFL-Week1-Review`, one-shot 2026-09-15 07:00 PT, `StartWhenAvailable` so a machine that is off still runs it when it comes back. It settles Week 1 first, then runs `scripts/backtest/nfl_week1_review.py --apply`, which owns the decision and is the only thing permitted to touch `MIN_EDGE_THRESHOLD_NFL`; the model narrates and emails, and is explicitly forbidden from second-guessing the branch, re-running it for a different answer, or editing `.env` itself. Fails closed on every path. Verified on the live path today: `--apply` at 0 settlements -> branch C, `.env` unchanged. **The pre-declared exit from the S1 freeze. Written now, while nothing is at stake, so the call is not made on Week 1 emotion.** The 26 held positions settle across 09-09/09-10 (4), **09-13 (20)** and 09-14 MNF (2) — so Tuesday 09-15 is the first morning NFL has ever had settled evidence. **The freeze costs no learning time:** these bets are already placed and held to settlement (S2), so the data arrives whether NFL is frozen or not. **ROI on these 26 is reported but NOT decisive** — they are legacy entries from a pre-L2 filter (wide spreads, dead books), so their entry prices contaminate ROI in both directions, and n=26 could not resolve ROI even if they were clean (402 bets could not). **The two measures that ARE readable at this n:** (1) model Brier vs Kalshi-ask Brier head-to-head on the same 26, the `calibration_study.py` method — directional, not conclusive; (2) realized game margins and totals against the `margin_stdev: 13.5` / totals priors, which is measurable from all 16 Week 1 games regardless of what was bet. *Branches:* **(A)** model Brier <= market Brier **and** dispersion roughly consistent with the priors -> unfreeze to **PILOT only**: max 2 open NFL positions, <=5% of bankroll in NFL, `UNIT_SIZE=1`, spread <=3c, hold pilot until ~40 NFL settles or S8 CLV lands. **(B)** model Brier > market Brier (the pattern in 6 of 6 months overall) -> **stay frozen**, and re-evaluate on CLV once S8 ships rather than waiting years for ROI. **(C)** dispersion clearly inconsistent with the prior -> recalibrate the NFL stdev from real results **first**, then re-run A/B; never unfreeze on a prior known to be wrong. **Any unfreeze requires S4 exposure gates (or an explicit manual cap) already in place** — otherwise the same 31% pileup simply recurs. **SATISFIED 2026-08-26: S4 shipped**, live at 0.50 total / 0.33 per sport. Note NFL already stands at 27.8% of equity, so a pilot unfreeze has only ~$5.60 of segment headroom until the Week 1 book settles — which is the gate doing its job, and is a tighter real constraint than the pilot's own "<=5% of bankroll in NFL" rule. |
| **P1b** | **Longshot go-live criterion — pre-declared, deliberately NOT dated** | High | XS | **The pre-declared exit from `DRY_RUN=true` on the `longshot` profile (P1), written 2026-09-10 while nothing is at stake — the S1b precedent, so the call is not made on the first winning week.** *Current state:* seven days of longshot scans (09-04 -> 09-10) have produced **one** trade row, `dry_run_blocked`, zero fill; the 09-10 run approved **0 of 7** candidates. **The binding gate is edge, not price** — rejections read `edge_below_threshold (4.0% < 8.9%)`, `(7.8% < 9.1%)`, `(6.6% < 9.1%)`, i.e. R28's `NO_SIDE_MIN_EDGE_GLOBAL=0.08` plus fee, so `MIN_MARKET_PRICE=0.08` (**the knob that defines this strategy**) is barely doing anything. **Flipping the flag today would change nothing except downside**, which is the real reason not to. *Order of operations, all three required:* **(1) Resolve `MIN_MARKET_PRICE` first** — 0.08 is contradicted by our own backtest (the 8-12c band it admits went **0W-36L, -103.3% ROI** across all six settled months; the 0-8c band it still excludes holds the book's two biggest winners). Decide **0.12 or 0.06**; going live on a value we hold evidence against is the one clearly wrong move. Also evaluate `spread`-as-category (23% win, +31.7% ROI, n=111) as the better-evidenced route to a longshot book. **(2) Read CLV, not ROI.** At ~1 candidate/week this profile will never resolve ROI — 402 settles could not. S8 (shipped 2026-09-10) makes CLV readable at n~20-30 instead of hundreds, and that is precisely why S8 came first. Require mean CLV > 0 with a bootstrap CI, reported beside its `n_captured / n_settled` coverage per S9 — **and do not read the mean until coverage is high**: misses concentrate in thin markets, which is where the bad bets live, so low coverage biases it optimistic. **(3) Then PILOT, not live** — same shape as S1b branch (A), since this is the same cold-start problem: max 2 open longshot positions, <=5% of bankroll, `UNIT_SIZE=1`, spread <=3c, held until ~40 settles. *Two ops prerequisites, both of which trip on this exact flag and are documented in [docs/longshot/README.md](./longshot/README.md) "Known soft spots":* **(a) subaccount 1 needs its own settle + reconcile tasks** (`EDGE_RADAR_PROFILE=longshot`) — `KalshiClient()` takes its subaccount from the *active* profile and every settle/reconcile task runs unprofiled, so today they only ever see subaccount 0; without this, longshot fills never settle and its P&L never lands, which would defeat the comparison the profile exists for. **(b) `daily_summary.py` / `risk_check.py` / `betting_analysis.py` need `for_profile()` scoping** — they read the pooled trade log, harmless only while longshot is zero-fill. **`CLV-Capture` needs nothing** — it reads the unfiltered log and calls `get_market()`, which is public market data, not portfolio-scoped, so it already covers both books. *Retired by S10:* once `strategy_state.json` ships, `longshot` becomes a `cold_start` segment and this criterion becomes mechanical rather than a written promise — the same way S10 retires the S1 NFL freeze. *Verify:* `EDGE_RADAR_PROFILE=longshot python scripts/doctor.py` prints the profile and wallet; `python -c "import json,collections; print(collections.Counter(t.get('profile','main') for t in json.load(open('data/history/kalshi_trades.json'))))"` splits the book. |
| **S2** | **Quarantine the 24-position pre-L2 NFL book** | High | XS | $28.50 at risk = **31% of a ~$92 bankroll**, one sport, entries as old as 2026-05-23 (up to 95 days pre-kickoff), all `dry_run=false`. Admitted by a pre-L2 filter — the 2026-08-18 audit found 13/27 past the 5c spread line (to 20c) and 18/27 with zero 24h volume. **Gate 3.6 only runs at entry; nothing re-checks a position already held.** **Hold, do not flatten** — market-exiting a 5-20c-wide book pays exactly the illiquidity penalty Gate 3.6 exists to avoid. Do not add to any NFL event or ticker. Exit a ticker only if its current spread is <=5c *and* the exit price implies less expected loss than holding to settlement. Daily summary gains a "legacy positions (pre-current-gates)" section; the legacy book is excluded from every ROI/CLV claim. |
| ~~**S3**~~ | **Jurisdiction/product eligibility preflight — fail closed** | High | Small | **SHIPPED 2026-08-26.** New `scripts/shared/venue_eligibility.py` + `data/cache/venue_eligibility.json`, keyed on **venue + product** (the observed block named Sports/Elections/Entertainment specifically — disabling all of Kalshi would be over-broad). Three fixes, one per failure: **(1)** `_handle_structural()` aborts the batch on the **first** structural rejection — threshold 1, not the transport short-circuit's 3, because jurisdiction blocks are deterministic. The 16 rejections were 6 batches that kept firing (3 inside one second on 08-20, 4 on 08-23); replaying 08-20 now attempts **1 order instead of 4**. **(2)** The verdict persists and `execute_pipeline` reads it before any live order, `unknown` blocking exactly like `blocked` — deliberately the opposite of gates 3.6/3.7/2b, which fail *open*: an unmeasurable spread is a sizing question, an unverified jurisdiction is a legality question. Dry runs skip it (they never reach the venue, and blocking them would silence the Polymarket evidence log). Nothing clears a block automatically — only a real acceptance (`dry_run_blocked` deliberately does not count) or `doctor.py --verify-eligibility`, which places a real 1¢ unfillable probe and cancels it. `ok` decays after 30d (eligibility is a lease — Kalshi sends "further instructions as necessary"); `blocked` never decays, since time is not evidence. **(3)** All three truncation sites fixed: console 80, trade log 200, digest 110 — the last landing on **"Check you…"**, 25 chars short of "Check your email for more details", the entire fix. `actionable_reason()` elides the middle and keeps both ends. Transient patterns (`insufficient_balance`, rate limits, `deprecated_v1_order_endpoint`) are checked first and can never disable a venue. `doctor.py` reports `unknown` as FAIL, not WARN. Cache seeded from the real 08-26 probe order rather than assumed. +48 tests, 964 pass. **Feeds S16** — that kill switch specifies this exact trigger and now hooks this rather than reimplementing. **Known limit:** pattern-based, so novel restriction wording falls through to the transient path; that is the deliberate direction (a false positive disables live trading) but the list needs review when a new structural rejection appears. Original note: | **A correctness bug, not just waste (D5).** The 2026-08-26 daily summary shows 3 orders rejected by the venue: Nevada residents cannot open positions in Sports, Elections, and Entertainment. Cache venue+account eligibility at startup, print it in `doctor.py` and the daily summary, and treat **unknown eligibility as `dry_run`** — a transient API or config failure must never fall back to attempting real orders in a barred product. If the account truly cannot trade Sports on this venue, that is a day-one fact about the reachable book, not a trickle of rejects discovered over weeks. *Success:* venue-rejection count reaches 0; unknown => no live order ever placed. |
| ~~**S4**~~ | **Cumulative exposure gates (new gate 2b)** | High | Small | **SHIPPED 2026-08-26.** `MAX_OPEN_EXPOSURE_PCT` + `MAX_SEGMENT_EXPOSURE_PCT`, both fractions of **equity** (cash + position value, not cash — a cash denominator climbs at twice the rate of the risk). Code defaults 0/0; **live `.env` 0.50 / 0.33, the operator's call over the 0.20 / 0.10 proposed here**, made with the consequence stated: at 50/33 the book that prompted the gate *passes* (27.8% total, 27.8% NFL), so it binds on the next pileup rather than this one — and that dissolves the legacy-quarantine question S4 would otherwise have forced, since NFL fits under 33% either way and other sports keep full headroom while the frozen book runs off. Both thresholds are covered by tests in both directions. **Rejects when a ceiling is already breached AND trims an order to the remaining headroom** — reject-only would let a 49.9% book add a full `MAX_BET_SIZE`; the batch loop accumulates approved cost so N individually-compliant orders can't walk through together, and the R26 replay path re-checks it like gates 5/6/7. Fails open on unknown equity (the opposite of S3's fail-closed, deliberately: an unknown ceiling is a sizing question, an unknown jurisdiction is a legality question). Verified on the live book and on a synthetic nine-row over-limit slate (orders 4-5 trimmed, 6-9 rejected, overshoot $0.21 from the `max(1, ...)` floor). `doctor.py` prints both and WARNs when either is 0. +28 tests, 916 pass; third config-driven test breakage caught at the conftest seam. **Still missing:** nothing re-checks a position already held — Gate 2b, like Gate 3.6, runs only at entry; S12's scoreboard is where a standing breach becomes visible. Original note: | `MAX_OPEN_EXPOSURE_PCT=0.20` (total open at-risk / bankroll, hard reject) + `MAX_SEGMENT_EXPOSURE_PCT=0.10` (per sport/category/venue), in `.env` + `app/config.py`. **No existing gate measures total capital deployed** — `MAX_OPEN_POSITIONS=50` and `MAX_PER_EVENT=2` both passed while the NFL book accumulated to 31% across roughly a dozen scans over three months; `MAX_BET_RATIO` and `--budget 10%` each bound a *single batch*. Adjacent to **B3** (the 10%-of-bankroll Hard Stop that has no code) — same gap, different axis. *Verify:* force a synthetic over-limit scan, confirm the reject reason. |
| ~~**S5**~~ | **Time-to-event cap** | Medium | Small | **SHIPPED 2026-08-26.** Gate 3.7, `MAX_DAYS_TO_EVENT_FOR_GAME_MARKETS` (code default 0 = off, live `.env` 14), futures exempt by category. Would have blocked **all 26** NFL positions (min 25d, median 35d, max 112d) while passing college football Week 1 at 2 days out. Verified against the real book; `doctor.py` prints it; +24 tests, 888 pass. Enabling it failed 126 unrelated tests whose fixture tickers are far-dated — fixed at the conftest seam like the S1 freeze. Original note: `MAX_DAYS_TO_EVENT_FOR_GAME_MARKETS=14`; futures get a separate, longer config. Directly prevents the "September football bought in May" pattern. *Verify:* scan preview rejects far-dated game rows. |
| **S6** | **`risk_config_fingerprint()` — make D4 an invariant, not an audit** | High | Small | **Evidence added 2026-08-26:** propagating S1/S4/S5 into the satellite docs found that *none* of them had been updated for S5 either, that `ARCHITECTURE.md` advertised 12 gates in its badge and 13 in its table while documenting 9, that the `KALSHI_BETTOR` agent quoted `UNIT_SIZE $0.50` / `KELLY_FRACTION 0.75` (neither current for months), and that `risk_check.py --report limits` documented a `MAX_PORTFOLIO_RISK_PCT` row whose env var does not exist anywhere in the codebase. Every one of those docs was accurate when written. **A sweep fixes the instances; S6 fixes the class** — it is the only item here that makes "printed == executing" checkable rather than remembered. Original note: **Every recommendation in the review can be shipped to `.env` and change nothing:** scheduler `.bat` files pass `--unit-size`/`--budget` explicitly, and `kalshi_executor.py` snapshots every gate threshold into module globals at import time. One function defined at the risk boundary (the executor) and called by **both** `doctor.py` and the daily summary, hashing the *actual runtime decision inputs*: `.env` values, `.bat` command-line overrides, module-level constants **as they stand after process start**, the strategy-state file path + mtime/hash, and the eligibility-cache version. Hashing `.env` alone would miss every one of D4's failure modes. Ships with a one-time `.bat` audit and a restart of long-running hosts. *Success:* the thing printed is the thing executing — "audit the `.bat` files" stops being a recurring chore. |
| **S7** | **Hold all sizing** | — | — | Standing constraint, not a task: `KELLY_FRACTION` <= 0.5, `UNIT_SIZE=1.00`, `ALLOW_PREDICTION_BETS=false`, `ALLOW_LIVE_BETS=false`, World Cup off. The lifetime ROI CI contains zero — nothing in this review justifies more size. |

**Phase 2 — install the instrument (2-4 weeks):**

| ID | Item | Impact | Effort | Notes |
|----|------|--------|--------|-------|
| ~~**S8**~~ | **CLV has never once been computed — it is broken, not missing (D1)** | High | Med | **SHIPPED 2026-09-10.** `scripts/kalshi/clv_capture.py` samples the book shortly BEFORE each open position's event starts (task `CLV-Capture`, every 5 min, **read-only at the venue**); the settler no longer derives a closing price at all. **The bug was never the arithmetic** — by settlement the closing book no longer exists, so the measurement had to move, not be repaired. `event_start_time` comes from the matched Odds API `commence_time`, captured at execution: the ticker only carries a start time for **35% of the book and all of it is MLB**, so keying off it would have silently restricted CLV to one sport. Missing prices are **NULL, never 0.0** (`compute_clv` tests `is None`, so a genuine 0.0 close is computed rather than discarded — the D1 shape one level down), the whole book is persisted so the S14 A/B stays readable, and CLV is in **bet-side probability space** so the NO sign is not inverted (S18). **Concurrency caught in review:** the venue reads run outside the M2 lock and captures are re-applied by `trade_id` against a fresh read inside it, so a row appended by a concurrent execute task is never clobbered. **Nothing to backfill** — the 426 settled rows' books stopped existing months ago; `--report` reads 0/143 today. Verified live on a real market: YES 0.40→0.44 = +0.04, NO 0.40→0.56 = **+0.16**, closes summing to exactly 1.0000, futures skipped rather than faked. +45 tests, 1167 pass. Superseded detail: `kalshi_settler.py:326` reads `closing_price` from the **settlement-time** market snapshot (`last_price`); a settled Kalshi market returns nothing meaningful, so it is `0.0`, `0.0` is falsy, and line 334's `if closing_price and entry_price` short-circuits `clv` to `None`. Silently, on every settle, for five months: 76/169 trades carry `closing_price` with distinct values `{0.0: 76}`, 150 settlements, **0 CLV populated**. **There is nothing to backfill** — CLV accrues from the day capture ships. Fix: store `entry_price_bet_side` + `event_start_time` at execution; a new **T-5min** scheduled job writes the closing book (T-0 fallback, **never post-settlement**); `clv = close_price_bet_side - entry_price_bet_side`, **all prices in bet-side probability space** so CLV means the same thing for YES and NO. **Persist the whole closing book, not one scalar** — `close_yes_bid`, `close_yes_ask`, `close_no_bid`, `close_no_ask`, `close_mid_bet_side`, `close_capture_at`, `close_capture_reason` in {`t_minus_5`, `t_zero_fallback`, `missed`} — otherwise the S14 A/B is unreadable (you cannot tell maker CLV improving from the close being sampled on the other side of the book). **`missed` writes NULL, never 0.0** — a falsy sentinel absorbed by a truthiness guard is precisely how D1 happened, and a zero close would drag every mean toward a fictitious -entry_price. |
| **S9** | **CLV reporting slice — replaces realized ROI as the primary decision signal** | High | Small | Mean CLV in percentage points **with bootstrap CI**, by sport / category / side / price band / fee role, in `scripts/kalshi/betting_analysis.py`. **Every CLV figure prints `n_captured / n_settled` beside it** — mean CLV over 60% of the book is not the same claim as over 97%, and misses will not be random: they concentrate in thin markets, which is where the bad bets live, so low coverage biases the mean optimistic. |
| **S10** | **`strategy_state.json` — protective mode only** | High | Med | Written by analysis, read at the risk boundary. Per segment: `last_settled_at`, `evidence_status` in {`active`, `stale`, `cold_start`, `insufficient`}, `expires_after_days` (~45 for daily sports, ~120 for seasonal/futures), `default_when_stale: dry_run`, `execution`, `reason`. May demote to dry-run, raise an effective floor, or cap a stake — **nothing else** — and it **never inherits stale positive ROI**. `scripts/backtest/strategy_state.py` writes · `app/config.py` exposes path + flag · executor preflight reads · `doctor.py` prints its timestamp. Retires the S1 freeze. |
| **S11** | **Shadow diagnostics — log only, change no decision** | Medium | Small | `calibrated_edge = lambda x claimed_edge` (0.16; also log 0.25/0.40); `gate3_ceiling_would_reject` at `EDGE_CEILING_WARN=0.20` and `EDGE_CEILING_REJECT=0.30`; a `legacy_gateset` label on every trade row. Review firing rates after one full cycle before anything goes live. **A lambda multiplier alone cannot fix the non-monotone defect** — replaying all 390 settles at lambda=0.16 with unchanged floors keeps 44 bets (11% of the book) composed **entirely of the >=20% claimed-edge population that performs worst**, and at a 0.04 floor that replay goes **-11.2%**. Lambda is a monotone transform, so dropping the floor proportionally just re-cuts the same ranking at a different point. **A multiplier cannot repair a non-monotone defect; a ceiling can.** Orthogonal tools, not alternatives — both shadow-first. |
| **S12** | **The daily scoreboard — six lines, no more** | Medium | Small | Every mechanism above is invisible unless it surfaces daily: (1) `eligibility: OK \| UNKNOWN->dry_run`; (2) `risk_config_fingerprint()`; (3) `open exposure: $X (Y% of bankroll) — legacy $Z excluded`; (4) `CLV last 30d: +A.A pts [CI], n=B/C captured (D%)`; (5) segments in dry_run, with reason; (6) **kill-switch distance** — which trigger is nearest and how far. Line 6 is the important one: a kill switch you first learn about when it fires is one you will argue with; one you watch approach for three weeks is one you have already accepted by the time it trips. |
| **S13** | **Re-run `calibration_study.py` + `correlation_check.py` against CLV, not outcomes** | Medium | Small | Lambda's CI is currently **[-0.04, +0.42]** — far too wide to size against. Blocked on S8. |

**Phase 3 — remove the structural cost of trading (after S8-S10 land):**

| ID | Item | Impact | Effort | Notes |
|----|------|--------|--------|-------|
| **S14** | **Maker-fill A/B — the only lever whose payoff does not require the model to improve** | High | Med | Kalshi maker fees are zero; the settled book paid **$11.97 on $381.66 — a +3.14 percentage-point ROI swing available with no improvement in the model** (0 maker fills in 169 trades; 17 nonzero taker-fee rows). `kalshi_client.create_order()` already accepts `yes_price_cents`/`no_price_cents` with `time_in_force="good_till_canceled"` — these *are* restable limit orders; they never rest because the executor prices them to cross. **A bounded experiment, not a new default** — "post at the bid" is at least three strategies (best-bid passive, one-tick-inside-spread, today's aggressive baseline). Require a post-only flag if the venue offers one; otherwise place a maker test only when the limit sits strictly inside the opposite side so it cannot accidentally cross (**on a 1c-wide market there may be no safe maker test at all**). *Eligibility:* passes Gate 3.6, spread <=3c preferred and never >5c, nonzero 24h volume, event inside the S5 window, no legacy positions. *Allocation:* **deterministic by ticker hash, never chosen after seeing the market**; start **25% maker / 75% taker** (fill loss can starve the sample and the bankroll is small). **Sizing unchanged** — fee savings must not increase stake during the experiment. **Recompute edge at the intended order price**, never inherit the scan row's displayed price, and log `scan_price`, `limit_price`, `fill_price`, `would_cross_at_submit`, `liquidity_regime`, `fee_role`, or you cannot separate "maker improved EV" from "maker selected a different price distribution". *Metrics:* fill rate, partial-fill rate, mean CLV, realized spread captured, cancellation rate via `RESTING_ORDER_MAX_HOURS`, post-fee ROI, missed-opportunity cost on unfilled orders that later moved favorably. *Stop rule:* maker CLV underperforms taker CLV by >1pt after 100 filled maker orders, **or** fill rate <25% on otherwise-qualifying rows -> disable maker mode for that segment. *Promotion:* >= +1pt after adverse selection with the lower bootstrap bound above 0, over >=100 filled maker orders. Note the symmetry: **Gate 3.6 and a maker strategy are the same policy approached from two directions — only trade where a real two-sided market exists.** |

**Phase 4 — scale only on a pre-declared trigger:**

| ID | Item | Impact | Effort | Notes |
|----|------|--------|--------|-------|
| **S15** | **Day-90 checkpoint, with a losing branch written in advance** | High | Small | Turnover is the other multiplicand: **$382 across five months on a ~$92 bankroll, median stake $0.80** — even a genuine, durable +10% edge returns about $38 in five months. At 90 days from CLV ship: **coverage <60%** -> the capture job is the problem, fix it and interpret nothing else; **coverage fine but the global CLV CI still straddles zero** -> the answer is *not* "run longer at this size" (a $0.80 median stake will not resolve it in a second 90 days either), the honest branch is shrink to the segments with the tightest CLV CIs, or stop; **coverage fine and the lower bound is above 0** -> the promotion rule. *Promotion (deliberately harder than the kill rule, because scaling is where the damage happens):* >=150 CLV-captured bets **and** >=60 calendar days, global mean CLV **above +1.0 point with the lower 95% bound above 0**, and no segment sitting in a qualifying negative-CLV kill — then raise **exactly one knob**, `UNIT_SIZE` $1.00 -> $1.50 (the longshot lane). Wait a further 60 days before touching `KELLY_FRACTION` (the favorites lane). **Never both at once.** |
| **S16** | **Kill switches — written now, while nothing is at stake** | High | Small | **Global negative CLV:** rolling 90d, >=150 captures, mean CLV <= -1.0pt with the 95% **upper** bound below 0 -> **all automated execution to dry-run only**. **Segment negative CLV:** >=40 captures in a sport/category/side, mean <= -1.5pt with upper bound below 0 -> that segment to dry-run, reason `negative_clv`. **Insufficient evidence:** 120 days elapsed with <150 captures -> dry-run, reason `insufficient_evidence` (off-season quiet is not a bad model, but silence defaults to off, not to running). **Venue/product rejection:** any repeated structural rejection (e.g. the Nevada restriction) -> immediate disable of that venue/product until `doctor.py` reports it eligible; no sample threshold, this is deterministic not noisy. **Daily loss:** `MAX_DAILY_LOSS`, unchanged. **Distance is computed mechanically, not authored**, for S12 line 6: global/segment = `upper_ci - 0` alongside `n/150` (or `n/40`), exposure = `cap_pct - current_pct`, insufficient = `120 - days_since_first_capture_or_policy_start`, venue = binary. |
| **S17** | **Polymarket has produced no tradable evidence (D7)** | — | — | 45 dry-run passes, 1,250 rows, 54 executable, **all 54 failed on edge, 0 settlements.** Useful as a pricing lab; not a revenue candidate. This does not stop the Priority 0b build below — it sets the expectation for it, and PM3 settlement is what would change the picture. |

**Open questions this review deliberately did not settle**, and what would settle each:
lambda-multiplier vs edge ceiling (**both, both in shadow** — re-measure lambda against CLV rather
than outcomes, then check whether the ceiling still fires on rows lambda has already killed; if it
never fires independently, drop it); the sub-10c longshot lane, flagged in CLAUDE.md as an open
experiment (**keep, tiny fixed stake, and stop counting it as evidence** — F3 says cheap contracts
are the model's one clean signal, but three MLS tickets are the entire lane's P&L and 22 of its 25
bets lost; settled by mean CLV over 40+ sub-10c captures, never by realized ROI, which will not
converge); adverse selection on maker fills (**unsized** — a risk resolved by the S14 A/B, not a
settled recommendation); whether the Jun-Aug break is signal (**treat as real at p=0.018 but do not
tune against it** — if CLV was positive through a losing quarter it was variance, if CLV went
negative alongside ROI the model decayed); whether to flatten the NFL book (**hold**, per S2 —
settled by pulling live bid/ask on all 24 tickers).

**What this plan claims.** Not that Edge-Radar is profitable — the lifetime CI contains zero, the
last three months are negative, the model's Brier lost to the market in 6 of 6 months, and the
entire positive P&L is five bets. Not that it is unprofitable either — 402 settles at a $0.80
median stake cannot resolve a question this fine. **Phases 1-2 reduce loss and buy information;
S14 is the first item that increases revenue**, and it does so without requiring the model to
improve, which is why it is separated from Phase 4. **The next 90 days are a measurement project,
not a betting strategy.**

---

##### Priority 0b — 🔴 Active Build: Polymarket Integration (was Priority 0)

**The #1 item on this roadmap.** Polymarket account approved + funded (2026-07-14; US-persons ToS confirmed legitimate by operator). Goal: place wagers on Polymarket through Edge-Radar, reusing the existing provider-agnostic `Opportunity` + `size_order` risk-gate chain.

**Spike findings (2026-07-14):** The retired 2026-04-27 integration (commit `4361c85`) was a **read-only Kalshi↔Polymarket arbitrage scanner** (Gamma API) — it never placed a bet; `py-clob-client` was never wired. Execution is **net-new**: Polymarket is on-chain (Polygon/USDC), wallet-signed (EIP-712 via `py-clob-client`), CLOB order book, UMA-oracle settlement. *(⚠️ superseded 2026-07-20 — the funded account is the CFTC-regulated **Polymarket US** product: Ed25519 retail API, not on-chain / py-clob-client. See PM2c-0.)* **Good seam:** `app/domain/opportunity.py` is provider-agnostic (0 Kalshi refs) and `size_order()` runs on `Opportunity`, so a normalized Polymarket opp flows through existing gates for free. The execution client is a clean ~7-method interface (`get_balance_dollars`, `get_positions`, `create_order`, `get_orders`, `cancel_order`, `get_fills`, `get_settlements`), today hardcoded as `KalshiClient()` at `kalshi_executor.py:1592` + `webapp/services.py:161`. Recovered git assets: `polymarket_edge.py` (Gamma read layer) + `.claude/skills/polymarket/references/` (~9k lines of CLOB/trading API docs). **Full plan:** `docs/my-documents/temp/polymarket-integration/PLAN.md` (local).

**Recommended approach: Phase 1 read/dry-run → prove edge → Phase 2 execution.** Do not wire real money through a new execution path until edge is demonstrated in dry-run.

> **⚠️ Update 2026-07-23 — the dry-run gate could not terminate as written, and why.** Four days of scheduled evidence (8 runs, 79 rows) produced **zero** gate-passing opportunities: 73 rejected on `edge`, 6 on `score`. Two structural reasons, both now addressed or documented:
> 1. **The composite made futures unbettable (fixed — see C10).** Polymarket US's only executable surface is futures, and the futures composite scaled edge 5x more strictly than sports, putting Gate 4 out of reach of any realistic futures edge. Fixed 2026-07-23; the gate is now reachable, though nothing in the observed sample newly qualifies.
> 2. **The evidence log conflated two surfaces (fixed).** 66 of the 79 logged rows were Gamma-sourced *games*, which carry no US `market_slug` and are auto-excluded from execution — so the log read far busier than the tradable universe (13 rows) actually was. Runs now record `executable_count` per run and an `executable` flag per row, and the preview shows a `US` column.
>
> **Net:** the flip-`POLYMARKET_DRY_RUN` decision still awaits a genuinely qualifying edge, but the instrument now measures the tradable surface and the gate is no longer arithmetically unreachable.
>
> **⚠️ Update 2026-07-31 (C10b) — the *games* composite had the same bug, and C10 missed it.** `polymarket_games_edge.py` was written 2026-07-20, three days before C10, and had copied `edge * 20` from `polymarket_futures_edge.py` — which had itself copied it from its own `liquidity` line. A copy of a copy, so no independent rationale existed for it either. Independently confirmed on this surface: clearing `MIN_COMPOSITE_SCORE=6.0` needed **~15% edge at high confidence / 26% medium / 38% low** against game edges that run **1–7%**, and across **362 logged Gamma game rows not one ever reached 6.0** (max **5.30**). Aligned to `min(edge / 0.01, 10)`. **Not a floodgate** — replayed through the shipped code over those 362 rows, only **5 (1.4%)** newly clear Gate 4, all marginally (6.02–6.26); **330** are stopped at Gate 3 and never reach Gate 4 at all. **No live behavior change** (Gamma game rows carry no US `market_slug`), but it de-risks the seasonal US games repoint so that surface doesn't inherit an unreachable gate a third time. See **C10b** in Completed.

| ID | Item | Impact | Effort | Notes |
|----|------|--------|--------|-------|
| **PM2c-0** | ✅ **Execution rebuilt on Polymarket US retail API + futures repointed to US data (was "wallet identity mismatch")** | High | Med | **DONE 2026-07-20.** (1) **Root cause:** the funded account is the **CFTC-regulated Polymarket US** product (iOS-app only); it uses **Ed25519 API keys** (`key_id`+`secret_key`) against **`api.polymarket.us`** — not EIP-712/`py-clob-client`. The "$0 empty twin" was the wrong product entirely. (2) **Exec client rebuilt** (`PolymarketClient` on signed requests, raw `cryptography`+`requests`, no SDK; `app/config.py` creds → `key_id`/`secret_key`; `market_registry` → `market_slug`); verified live ($60.12 buying power, real positions). (3) **Futures scanner repointed to US data** (`polymarket_us_auth` shared signer + `polymarket_us_data` read client; `PM_FUTURES` → US championships priced on US quotes vs Odds consensus, real slug recorded); live-proven (Spurs NBA-champ +3.6%). **620 tests.** Full detail: [`docs/setup/polymarket-us-setup.md`](setup/polymarket-us-setup.md). **Key inventory finding:** US is NOT a Gamma mirror — **moneyline-only, seasonal game markets; no spreads/totals; no MLB per-game**; futures are the deep always-on surface. **Remaining:** games scanner still reads Gamma (dry-run only, not executable on US) — seasonal moneyline-only repoint deferred. ~~Execution-pipeline wiring~~ **DONE same day — see the PM2 row (PM2c)**; orders stay `dry_run_blocked` behind the two-flag rule (`DRY_RUN` AND `POLYMARKET_DRY_RUN`, venue flag default true) until the dry-run edge window proves out. |
| ~~PM0~~ | **Spike follow-through** | — | Small | **DONE 2026-07-14.** Restored `.claude/skills/polymarket/` API refs (to scratchpad); smoke-tested Gamma live → HTTP 200, not geoblocked, all fields present. ~~Key finding: Polymarket's sports markets are futures/props/politics, not per-game lines (0 MLB game markets).~~ **CORRECTED 2026-07-20 (PM1d):** per-game markets DO exist for every MLB/NFL/NBA/NHL game (ML + run-line spread + total, tight 1–4¢ books) — they're just invisible to title search and default listing order; they only surface via **tag_id + open filtering**. Same discovery failure mode as the PM1b slugs. The futures-first pivot still produced the right Phase 1 skeleton; PM1d added the game layer on top. |
| ~~PM1~~ | **Phase 1 — read-only futures edge detection (dry-run)** | High | Large | **LANDED 2026-07-14 (framework + World Cup path proven).** New `scripts/polymarket/{polymarket_client,polymarket_futures_edge}.py`: read-only Gamma client + a Polymarket analog of `detect_edge_futures` that reuses `futures_edge.fetch_outrights` + `consensus_outright_fair_values` unchanged, emits normalized `Opportunity` (category=futures, edge_source=`polymarket_vs_outrights`, `details.venue=polymarket`). Wired `scan.py polymarket --filter worldcup` (aliases poly/pm); routes opps through the existing gates via `preflight_gate_status` in the preview; `--execute` refused (Phase 2). +12 tests (520 total). Proven end-to-end live: ingested the WC event, priced vs `soccer_fifa_world_cup_winner`, matched the final-4 candidates (0 edge — efficient + tournament ending, a correct result). **Follow-up PM1b.** |
| ~~PM1b~~ | **Event discovery for the other futures (NFL/MLB/NBA/NHL)** | Medium | Small | **SHIPPED 2026-07-20.** All four slugs found + wired: NFL `big-game-champion-2027` (titled "NFL Champion 2027" — why "super bowl" keyword search missed it), MLB `mlb-world-series-champion-2026`, NBA `nba-2027-champion`, NHL `nhl-2027-champion-20260612185656162`. Root cause of the original miss: the boards sit beyond the first 300 active events, so the paging fallback never reached them. Fix: replaced the pagination fallback in `find_event` with Gamma **`/public-search`** (relevance-ranked) — open-events-only, all-words-of-a-term title match, highest-volume winner (picks "World Cup Winner" over "Golden Boot Winner"), then re-fetch by slug for the full markets list. Slugs rot at season rollover; the fallback is live-proven to re-resolve all four from dead slugs, so next season heals without a code change. World Cup event closed 2026-07-20 (final) — dormant until the 2030 board opens. Verified end-to-end: all 4 sports price vs Odds API outrights (32/30/30/32 candidates matched 1:1); one live edge surfaced (NBA Spurs +4.0%, low conf → correctly gated on score). +4 tests (554 total). |
| ~~PM1c~~ | **Dry-run evidence persistence (edge-proving infra)** | Medium | Small | **SHIPPED 2026-07-20.** The Phase 1→2 gate is "prove edge in dry-run," but the scanner accepted `--save` and silently discarded it — no evidence could accumulate. Now `--save` appends every run (timestamp, filter, count, each opp **with its preflight gate verdict**; zero-opp runs logged too) to `data/polymarket/dryrun_log.jsonl` and writes the standard markdown report to `reports/Polymarket/` (new `report_writer` type). First live record captured (NBA Spurs +4.0% low-conf, gated on score). +3 tests (557 total). **Scheduled same day:** `Daily-Polymarket-DryRun` Windows task (daily 9:40 AM PST) runs the scan automatically — see `docs/task-schedules/README.md` #21 — so the PM2 case builds unattended. |
| ~~PM1d~~ | **Per-game markets: ML / spread / total edge detection** | High | Medium | **SHIPPED 2026-07-20.** The PM0 "no game markets" finding was wrong (see corrected row above). New `polymarket_games_edge.py` prices every open pre-game Polymarket ML/run-line/total against the SAME calibrated consensus model as Kalshi sports (`consensus_fair_value`/`consensus_spread_prob`/`consensus_total_prob` reused unchanged, incl. de-vig, sharp-book weighting, sport stdevs + C8 overrides). Client gained `get_tag_id`/`fetch_game_events`/`iter_game_rows` (`sportsMarketType` discriminates ML/spreads/totals; exotic NRFI/F5/props skipped — dead 2¢/98¢ books). Guard rails: pre-game only (Gate 4.8 posture), `MAX_BOOK_SPREAD` 10¢ book-quality floor, and **start-time matching** (±6h) between the PM game and the odds event — team-matching alone priced later series games against the wrong game's odds (caught live: 3 phantom Twins edges; the 06-03 Kalshi bug class). `--filter` now routes `all|futures|games|<sport>-games`. Verified live: 55 MLB games priced, 2 genuine edges (Under totals ~4–5%, correctly held by the R28 NO-side 8% floor), NBA/NHL offseason gracefully empty. Scheduled task widened to `--filter all --min-edge 0.01` so the evidence log captures the full funnel (17 rows first run). **Games settle daily → the edge-proving window can now validate against actual settlements in weeks, not October.** +9 tests (587 total). |
| PM2 | **Phase 2 — execution (real funds)** | High | Large | **PM2c pipeline wiring SHIPPED 2026-07-20 (execution is code-complete; live orders await the edge window):** `scan.py polymarket --execute` (also `--unit-size/--budget/--pick/--ticker/--min-bets`) routes futures opps with a US `market_slug` through the shared `execute_pipeline` with `venue="polymarket"` — Kelly sizing, every gate, ratio/budget caps, then `create_order`. Venue specifics: (a) **two-flag dry-run** — `PolymarketClient` blocks orders unless BOTH `DRY_RUN=false` and the new `POLYMARKET_DRY_RUN=false` (default **true**; required because `.env` runs Kalshi live — without it, flipping the scanner refusal would have gone live instantly); (b) **min-share handling** — `minimumTradeQty` captured scan-time into `details["min_order_shares"]` + registry; `size_order` bumps up to it (or rejects if the bump breaches MAX_BET_SIZE/bankroll — runs post-caps so a capped count can't slip under), and the pipeline drops rows the ratio/budget caps push back below minimum; (c) **positions normalized** — `get_positions` emits Kalshi-shaped `market_positions` with `PM-{slug}` tickers, so Gate 5/per-event counts/`status --venue polymarket` work unchanged; (d) trade records carry `venue`; batch placement survives non-Kalshi exceptions; Kalshi-only janitor skipped; Gamma games opps (no US slug) auto-excluded from execution. Live-verified end-to-end (preview mode: $60.12 balance, 2 positions, Spurs edge gate-rejected on score). +15 tests (635 total). **PM2a plumbing SHIPPED 2026-07-20:** `MarketClient` Protocol + `KalshiClient` conformance + `get_market_client(venue)` factory + executor `--venue`. **PM2b client SHIPPED later 2026-07-20:** `polymarket_exec_client.PolymarketClient` (MarketClient-conformant) via `py-clob-client` — email/Magic proxy account (`signature_type=1`, key exported from Polymarket settings, funder = proxy address; operator decision revised: the funded account IS the trading wallet, balance ≈ bankroll). Lazy CLOB construction (network-free init), DRY_RUN honored identically to Kalshi (`dry_run_blocked`), balance via CLOB collateral + Data-API position value, positions via Data API, orders/cancels/fills via CLOB. Ticker→token resolution through the new scan-time **`market_registry`** (yes=token 0 / no=token 1 structural; 7-day expiry; registry miss refuses the order). Config: `POLYMARKET_PRIVATE_KEY/FUNDER_ADDRESS/SIGNATURE_TYPE` in `app.config` + `.env.example` (key = full account access — warning documented). Known venue constraint: ~5-share min order (logged; PM2c must bump or skip). +18 tests (605 total). **Remaining — PM2c:** live auth smoke test once the key lands in `.env`; execution-pipeline wiring (size PM opps through the gates → `create_order`, min-share handling, flip the scanner `--execute` refusal); then first live orders after the dry-run edge window proves out. |
| ~~PM2d~~ | **Dashboard venue support (Polymarket in the web app)** | Medium | Medium | **SHIPPED 2026-07-31.** The CLI had four market types; the dashboard exposed three. `polymarket` is now a market type that also switches the execution venue via `get_market_client`, routing the scan through the CLI's own `_route_filter` (imported, not reimplemented, so dashboard and `scan.py polymarket --filter X` cannot disagree about which surfaces a filter covers). Three venue asymmetries handled explicitly rather than reused: **(a) two-flag dry run** — the banner and confirm dialog resolve live status from BOTH `DRY_RUN` and `POLYMARKET_DRY_RUN` (same logic as `_order_mode`), so an armed account cannot show a "DRY RUN" dialog; **(b) executability** — Gamma game rows show `Exec = —`, are dropped before `execute_pipeline` (matching the CLI), and the confirm dialog counts only orderable rows (selecting 5 game rows previously read "up to 5" and would have sent zero); **(c) position shape** — PM money fields are Amount objects and `market_exposure_dollars` is cost basis not market value, which through the Kalshi formatter printed $0.00 unrealized on every row; a separate formatter reads `cashValue` and reconciles to the Portfolio Value tile. Portfolio is now per-venue tabs with a deliberately **shared** daily-loss bar (Gate 1 reads the common trade log). Live-verified against both venues in the browser. **Supersedes the Q1 removal** (2026-04-22), which correctly deleted a UI-only Polymarket stub that never reached the service layer — this one does. Files: `webapp/services.py`, `webapp/views/{scan,portfolio,settle,config}_page.py`, `webapp/app.py`. |
| **PM2e** | **⚠️ Post-C10/C10b risk posture — the gate that was holding the line is gone** | High | Small | **Opened 2026-07-31. Read before the next unattended run.** The consequence that matters most from C10/C10b is not from the bugs but from the **fixes**. Audited against the trade log, the bugs themselves cost almost nothing: **0 Polymarket trades ever placed**, 0 prediction bets, 0 trades above the current `MAX_BET_SIZE`, 0 NBA/NCAAB bets in the band the stale Cloud config would have admitted. C10's "0 futures bets in 85 settled trades" is the only demonstrated behavior change, and its **sign is unknown** — with the model over-claiming edge exactly where it was blocked (C4, C11), an unreachable Gate 4 may have been accidentally protective. **What changed:** Gate 4 is now reachable on futures and games **for the first time**, on a surface with **zero settled trades** to calibrate against. Meanwhile the venue is armed (`DRY_RUN=false` AND `POLYMARKET_DRY_RUN=false`) and `Daily-Polymarket-Execution` runs `--execute` unattended. The standing risk therefore moved from *"structurally cannot bet"* to *"can bet, uncalibrated, automatically."* What remains holding the line is Gate 3 (edge ≥3%), Gate 3.5, Gate 4.5, and the task's `--max-bets 2 --budget 10%` caps — materially thinner than a week ago. **T1 is the cautionary precedent:** the last time a composite let a new bet shape through at scale, it produced 27% of the book at −12.6% ROI. **Action:** decide deliberately whether to keep the venue armed while futures/games have no settlement history, rather than leaving it armed by default. Setting `POLYMARKET_DRY_RUN=true` halts it without touching Kalshi. |
| PM3 | **Phase 3 — settlement & ops** | Medium | Med–Large | Polymarket settler (Data API / on-chain resolution → redeem → venue-tagged `trade_log`); surface venue in daily-summary / portfolio / betting_analysis; schedulers. Extend series/event dedup to be **venue-aware** (same game on both venues = double exposure). **Partial 2026-07-31:** the dashboard already surfaces venue — per-venue Portfolio tabs, a Venue column on settlement history, and venue-filtered "Today's Trades" — and the Settle page states its Kalshi-only scope, since `PolymarketClient.get_settlements()` still returns an empty list. Settlement itself, redemption, and the venue-aware dedup remain. |

**Operator decisions (answered 2026-07-20)** — these shape the PM2 write half: (1) **Scope: sports futures only** (no politics/crypto categories; mirrors the R25 caution). (2) **Wallet — REVISED 2026-07-20:** use the **existing funded email/Magic account directly** (key exported from Polymarket Settings, `signature_type=1`); operator confirmed balance ≈ intended bankroll, so the account already IS the dedicated low-balance wallet — a separate wallet would be ceremony without benefit. If the balance ever grows past the risk budget, withdraw down to restore the blast-radius cap. (3) **Stakes: normal Kelly sizing from day one** — no $1–2 micro-stake phase (operator's call; note current knobs `UNIT_SIZE=$1` / `KELLY_FRACTION=0.25` / thin futures edges mean first orders land ≈$1–3 anyway, and the dedicated wallet caps blast radius). (4) **Strategy: independent edge betting** (Polymarket vs sportsbook fair value, as PM1 measures) — cross-venue arb explicitly not the goal for now.

##### Priority 1 — Ship Now (P&L or Correctness)

These items address the critical P&L drains and calibration overconfidence identified in the 90-day review (2026-06-23).

*R28, R29, C8 shipped 2026-06-23. Two new items opened 2026-07-31 — see below.*

| ID | Item | Impact | Effort | Notes |
|----|------|--------|--------|-------|
| **B1** | **Spread/total models mix medians across books (+ the `weighted_median` tie-break)** | Medium | Small | **From the 2026-08-25 betting-logic review (#5 + #6).** `consensus_spread_prob` and `consensus_total_prob` take `weighted_median(lines)` and `weighted_median(implied_probs)` **independently**, then invert that pair through the normal CDF. Books post *different* lines, so the resulting `(line, prob)` pair is a quote no book made and the inferred mean margin belongs to neither. **Measured, not assumed** -- reconstructing both versions over all 37 cached odds files: spreads n=1,452, **median error 0.00pt**, mean 0.21, p99 3.37, **max 8.84**, 1% above 3pt; totals n=768, mean 0.06pt. Near-zero typically, because books usually agree on the line. The effect lives almost entirely in **NFL** (mean 0.30pt, max 8.84); NBA 0.28, MLB 0.02, soccer/MLS/NHL 0.00. **Why fix it anyway:** the tail is **one-sided** (all 12 rows above 3pt push P(cover) *up*, toward YES) and the model *selects on its own errors* -- an 8.8pt spurious shift is an 8.8pt spurious edge, ~2x the Gate 3 floor and near-max on the composite's 40% edge weight, so the tail is over-represented among executed bets relative to its 1% frequency. **Timing is the real argument: NFL season opens ~2 weeks out with zero settled NFL bets in the entire history to calibrate against.** **Fix:** invert per book, then weighted-median the *inferred means* -- three lines inside the existing loop. **Fold in #6 while in the file:** `weighted_median` resolves an exact weight tie *downward* (`[0.40, 0.60]` -> `0.40`), which affects 0% of bettable moneylines/spreads and 7% of totals at mean +0.02pt -- trivial alone, but note it may *increase* B1's measured error, since the lower-value tie-break currently restores coherence by accident at 2-3 books. Fix and measure them together. |
| **B3** | **The 10%-of-bankroll Hard Stop has no code** | Medium | XS | **From the 2026-08-25 review (#7).** `CLAUDE.md` -> Hard Stops says *"REFUSE to execute ... if a single position would exceed 10% of bankroll."* `size_order` computes `bankroll_pct` and stores it on the `SizedOrder`, but **no branch ever reads it**. The only size caps are `MAX_BET_SIZE` (absolute dollars) and the bankroll check. At the live `.env` (`MAX_BET_SIZE=8`, bankroll ~$92) the effective cap is **8.7%** -- under the documented limit *by accident, not by construction*. Raise `MAX_BET_SIZE` or let the bankroll drift down and the stop silently stops being true. Same shape as the "illiquid spread > 5%" Hard Stop, which was documented from launch and only implemented in L2 (2026-08-18) after the executor had traded 20c-wide books. **Fix:** one branch after the `MAX_BET_SIZE` cap. |
| **T1** | **MLB high-strike totals dominate the book and are badly miscalibrated** | High | Med | **Opened 2026-07-31 from an operator observation** ("a ton of under-13.5 baseball runs bets"). Confirmed and larger than it looked: **31 of 115 live trades (27%) are MLB totals, 28 of them NO-side, and 14 sit on strike 13 alone** — 12% of the entire book is one repeated bet shape. Only 7 MLB moneylines in the same window. **Calibration:** those 28 NO bets went **18W-10L (64.3%)** against an **80.1%** market-implied break-even → **−12.6% ROI**. Versus the market that is p=0.038 (marginal, n=28); versus **the model's own claimed 89.7% fair value it is p=0.0003** — the model is decisively miscalibrated on this shape, which is the solid part of the finding. **Mechanism (three parts):** (1) `consensus_total_prob` extrapolates from the sportsbook line (~8.7 runs) out to the Kalshi strike with a normal CDF and `SPORT_TOTAL_STDEV["baseball_mlb"]=3.45`; strike 13 is **1.25σ** out, where the answer is dominated by the stdev assumption rather than by any market data. (2) There is a **disagreement sweet spot** — near the line model and market agree, far out both approach 100% NO, and around 1.25σ the model says 89% NO while the market says 80%. Every MLB game has a listed strike in that window, so **every game emits one near-identical NO bet**. (3) **R28's global NO floor is 8% and the phantom edge averages 9.6%** — the one gate designed to stop bad NO bets sits just below the bias. **Ruled out:** skew. A negative binomial with the same mean and variance gives a *lower* P(>13) (9.0% vs the normal's 10.6%), so "normal CDF understates a right-skewed tail" is not the driver here. **Most likely real driver: adverse selection** — the model bets the games where its own noisy inferred mean sits lowest relative to the strike, which selects the cases where that estimate is most wrong. Same winner's-curse pattern C4 and C11 each found. **Connects to C11b:** that investigation measured *correlation* among "four MLB unders on one night" and correctly found none (rho −0.187); it never asked **why there were four**. This is the answer — C11b's conclusion was right but aimed at the wrong question. **Candidate fixes, in order of cost/benefit:** (a) verify the **≥ vs >** boundary convention first (see T2 — cheapest, and possibly the whole story); (b) **cap extrapolation distance** — reject totals whose strike is more than ~1σ from the consensus line, since past that the bet is on the stdev, not on the books; (c) raise `NO_SIDE_MIN_EDGE_GLOBAL` above the phantom band or add a totals-specific floor; (d) add a **per-shape batch cap** (same sport + category + side), which `MAX_PER_EVENT` does not cover because each bet is a different game. Do (a) before anything else. |
| ~~**T3**~~ | **The C8 stdev loop had never calibrated anything — `--days 7` starved it** | High | Small | **RESOLVED 2026-07-31. My own framing of this item was wrong and is corrected here.** T3 originally claimed the loop ran *monthly*, so a newly-covered market got ~30 blind days. Checking the actual machine killed that: the task doing the work is `Calibration`, **already weekly** (Sun 7 PM, `LastResult=0`), and the `MonthlyCalibration` task the tracked installer described **has never once run** (`Last Run 11/30/1999`). Cadence was never the problem. **The real bug:** that weekly task ran `model_calibration.py --days 7 --save`. `save_calibration_stdevs()` receives the **day-filtered** list and needs `_MIN_CALIB_SAMPLES = 20` settled rows *per (sport, category)*; only **~22 bets settle in any 7-day window across all sports and categories combined**, so every pair was skipped every week and the hardcoded defaults were written straight back. That is why `calibration_stdevs.json` was byte-identical to `SPORT_*_STDEV` — **the closed calibration loop has been a silent no-op for its entire life.** At `--days 30`, MLB totals goes **17 → 28** settled and the loop fires (`3.45 → 4.005`, gap +16.1%, n=28). **Fixed** in `scripts/schedulers/maintenance/calibration.bat` (gitignored — appears in no diff), with `tests/test_calibration_config.py` failing the build if the window is ever narrowed again. Also reconciled `install_windows_task.py`, which defined a MONTHLY task that did not match the live weekly one, and confirmed the loop is **stateless** (`base_stdev` is the hardcoded baseline, never the prior cache) — so raising cadence can never compound or oscillate. Two follow-ons in **T4**. |
| **T4** | **A newly-covered market type still floods before it can be calibrated** | Medium | Small–Med | **Opened 2026-07-31 — the part of T3 that survives its correction.** Even with the window fixed, C8 cannot move a value until 20 of a market type's bets have *settled*, which by construction happens after the flood. MLB totals opened 07-20 and reached **69% of the book** before any calibration could legitimately have data. Cadence and window changes cannot fix this; only a rule that treats never-calibrated market types as suspect can. Options, none shipped: (a) hold a market type to a **higher edge floor** until it has been calibrated at least once; (b) a **per-shape batch cap** (same sport + category + side), which `MAX_PER_EVENT` does not cover because each bet is a different game; (c) cap a single (sport, category) at some share of the batch. Relevant now: the Polymarket US seasonal games repoint is the next coverage addition queued. |
| ~~**T2**~~ | ~~Verify the totals strike boundary convention (`≥` vs `>`)~~ | — | Small | **VERIFIED AND CLOSED 2026-07-31 — no bug. The hypothesis was wrong.** Checked against the live Kalshi API for all 28 logged MLB NO-total markets. Three findings, each of which independently closes it: (1) **the ticker suffix is not the strike.** `KXMLBTOTAL-…MINCLE-13` has `floor_strike: 12.5` — the suffix is a market index, not the threshold. (2) `extract_strike()` reads **`floor_strike` first** (`edge_detector.py:1214`) and only falls back to rules-text parsing, so the model uses 12.5, not 13. Kalshi's `rules_primary` says "more than 12.5 runs … resolves to Yes" and `strike_type` is uniformly `greater` — the model's `1 - norm.cdf(12.5)` matches the resolution rule exactly. (3) **`floor_strike` is a half-integer on 28/28 markets**, so no integer run total can ever tie the strike and the `≥` vs `>` distinction is *mathematically moot* regardless. Recorded because the negative result is load-bearing: it eliminates the cheap single-line explanation, so T1's cause lies in the model or in bet generation, not in a boundary convention. |

*Note: R12–R18, R20, R21–R23, R24a, R25 all shipped 2026-04-24. R27 shipped 2026-06-15.*

##### Priority 2 — Near Term (Weeks)

Items that improve measurement, close known gaps, or remove operator friction.

| ID | Item | Impact | Effort | Notes |
|----|------|--------|--------|-------|
| **B2** | **Eleven sports fall back to a basketball-scale stdev (fail closed instead)** | Medium | Small | **From the 2026-08-25 review (#9).** `_PREFIX_TO_SPORT` has 11 entries; `KALSHI_TO_ODDS_SPORT` has 35. The unmapped ones -- six European soccer leagues, WNCAAB, boxing, IPL cricket, and both tennis tours -- return the hardcoded `12.0` default from `_get_margin_stdev` / `_get_total_stdev`. **Currently latent**, because `CATEGORY_MAP` routes all of them to `"game"` (moneyline), which uses no stdev. But the trap springs the moment a spread or total series is added for any of them: a 12.0-*goal* margin stdev prices soccer as basketball. `"wins by more than 2.5 goals"` at a -0.5 line / 0.55 devigged prices at **P=0.484 instead of 0.162 -- +32 points of fabricated edge**. **Fix:** make the fallback **fail closed** -- return `None` and emit no edge for an unmapped sport rather than guessing 12.0. Then add the soccer-league (1.8 / 1.5, matching `soccer`) and WNCAAB entries. Pairs naturally with **B6**'s `CATEGORY_MAP` prefix-shadowing fix, which is the other half of the same trap. |
| **B4** | **Gate 4.8 (live-betting block) covers 9% of the book** | Medium | Small-Med | **From the 2026-08-25 review (#8).** `is_game_started()` only returns True for tickers that embed `HHMM`, which is moneyline only. Spread, total, and **all** NBA/NHL game tickers are date-only, so Gate 4.8 never fires for them -- 108 of 119 settled trades in the sample examined (**91%**). The gate's own docstring is honest about this, but `CLAUDE.md`'s gate table reads as blanket coverage, and the **F44 mechanism it was built to close** -- live Kalshi price versus stale pre-game consensus -- is still fully open on exactly the categories that actually trade. **Fix:** `find_market_event` already holds the matched odds event; stash its `commence_time` in `details` and have Gate 4.8 prefer that over the ticker parse. Also correct the `CLAUDE.md` gate row, which currently overstates coverage. |
| **B5** | **Futures N-way devig carries favorite-longshot bias** | Medium | Medium | **From the 2026-08-25 review (#10).** `devig_nway` normalises implied probabilities **proportionally**. On a 30-way championship outright the overround runs 20-40%, and books load most of it onto longshots -- so uniform normalisation leaves longshot fair values **too high**, and the model preferentially claims YES edge on 2-5c futures candidates. That is exactly the population R7's price floor exists to block. Secondary defect: `devig_nway` does not require the outcome list to be complete, so a book listing only the top 20 of 32 teams produces a `total` that is too small, inflating every devigged probability from that book before they are pooled with complete books. **Fix:** power devig (solve `sum(p_i^k) = 1` for `k`) or Shin -- both ~10 lines. Minimum viable: skip any book whose raw implied total is below a sanity floor (e.g. < 1.05) as incomplete. **Gates Polymarket US quality** -- futures are the only orderable US surface, so PM2c/PM3 inherit this bias directly. |
| **GT1** | **NO-side risk has three independent knobs for one root cause** | Medium | Medium | **From the 2026-09-03 gate-consolidation review, finding #1.** NO underperforms YES (90d: -7% vs +48% ROI; full history -7.7% vs +22.4%, YES ahead in every shared price band), and three separate mechanisms now damp it, added seven months apart on three different reviews with three unaligned price breakpoints: **Gate 4.6** (R1, Apr) rejects NO below a 25% price threshold unless edge >=25% and confidence=high; **Gate 4.6b** (R28, Aug 90d review) raises the edge floor to `NO_SIDE_MIN_EDGE_GLOBAL` (8%) for *all* NO bets; **Kelly damping** (F4, Aug calibration study) halves the Kelly fraction below 35c *and* at/above 50c, independent of both reject gates. None of the three breakpoints (25% price / 35c / 50c) line up with each other, and a new contributor has to read three CHANGELOG entries plus two functions to answer "how does Edge-Radar treat NO bets." **Not a blind merge** -- each threshold came from a different measurement window and may not collapse cleanly. **Next step:** pull the full NO-side settlement history and check whether a single edge-vs-price surface reproduces what the three rules currently approximate; only fold config knobs together if it does. See `docs/my-documents/repo-reviews/2026-09-03-risk-gate-consolidation-review.md`. |
| **C10c** | **The `edge * 20` composite scale survives in all 7 prediction scanners** | Medium | Small | **Found 2026-07-31 during the C10b propagation sweep, deliberately not fixed in that change.** `edge_score = min(10, edge * 20)` remains in `companies_edge.py:167`, `crypto_edge.py:227`, `mentions_edge.py:201` + `:269`, `politics_edge.py:140`, `spx_edge.py:200`, `weather_edge.py:255` — the same copy-paste C10 traced to the launch-day commit, now fixed in all three sports/futures/games paths but nowhere in `scripts/prediction/`. Same arithmetic consequence: Gate 4 needs ~5x the edge it should. **No live impact today** — Gate 4.7 (`ALLOW_PREDICTION_BETS=false`, R25) rejects every prediction category before composite matters, so this is latent, not active. **Not fixed with C10b on purpose:** seven modules, zero settled prediction bets to replay against, and the prediction models are already flagged as surfacing garbage fair values (R25, F34–F39) — loosening their gate before the model rebuild would be fixing the wrong layer first. **Do this as part of the prediction rebuild (R25b/R25c), not before it**, and replay against logged evidence the way C10/C10b each did. If `ALLOW_PREDICTION_BETS` is ever flipped before then, this becomes active and must be fixed first. |
| ~~M1~~ | **MLB executable-bets recheck (post-World-Cup)** | High | Small | **RESOLVED 2026-07-20 — crowding confirmed fixed; no tuning.** Ran on a full 15-game slate: MLB now surfaces **15 rows** (vs 0 all 30-day window), proving the World-Cup crowding was the cause and is structurally gone. All rows gated on `edge` with **sub-1% edges on efficient lines** (Mkt≈Fair within ~1¢; top edge +1.1%, composite 4.3–4.7). This is NOT the 2–3%-blocked-by-floor bucket — loosening would bet model-error-on-efficient-consensus (the C4 trap), so `MIN_EDGE_THRESHOLD_MLB` / `MIN_COMPOSITE_SCORE` **left unchanged**. Posture: watch-don't-tune; a real mispricing will clear the 4% floor on its own. Full writeup: `docs/my-documents/temp/mlb-executable-bets/README.md`. Side flag: Odds key `...6de244` showed only 10 requests remaining — run `check_odds_keys.py --live` before the next heavy scan day. |
| ~~M2~~ | **Cross-process trade-log lock** | Medium | Small | **SHIPPED 2026-07-20.** New `trade_log_lock()` (cross-process `filelock`, graceful no-op fallback if the dep is absent) + `append_trades()` which re-reads under the lock before saving, so a concurrent writer's append is merged not clobbered. Executor's two write sites (`log_trade` + the error-record path) now go through `append_trades`. Settler restructured into **Phase 1** (all Kalshi network I/O against a read-only snapshot, no lock) → **Phase 2** (short locked critical section that re-loads fresh — preserving any executor append made during the fetch — then saves), so the lock is never held across network I/O. +7 tests incl. an end-to-end concurrent-append-during-settle test (535 total). `filelock>=3.12.0` added to requirements. See repo review #2/#11. |
| ~~C4~~ | **Audit the base "high" confidence criteria** | Medium | Medium | **SHIPPED 2026-06-24.** Measured the tier's predictive signal on 306 settled bets: at *equal claimed edge* High underperforms Medium (5–10% edge bucket: 34% vs 63% WR) — no positive signal. The roadmap's "tight-market = lower edge" hunch was the wrong shape: High actually *over-claims* edge (19.1% vs 15.9% avg) against efficient ≥8-book consensus. Fix: capped `high`→`medium` in the sports composite weight (`edge_detector.py`) so "high" no longer floats no-signal bets up the `--max-bets` queue or helps clear Gate 4. Label retained (still gates NO-favorites at Gate 4.6); sizing never used confidence. Scoped to sports. See Completed entry below + Findings (C4 detail). Follow-up logged as **C4b** (edge-cap the base rule to make a meaningful High tier). |
| C4b | **Edge-cap the base "high" rule (make High mean something)** | Low | Small | Follow-up to C4. C4 *retired* High's composite premium but left the minting rule (≥8 books + tight consensus) intact, so "high" is now a near-inert label. Optional next step: only grant "high" when claimed edge is *modest* against the tight consensus (e.g. `edge ≤ ~10%`), since a large edge vs an efficient price is the over-claim signature (NCAAMB High: 33.8% avg edge / 28.6% WR). Caveat: C4 data showed High also underperforms at *low* edge (5–10% bucket, 34% WR), so an edge-cap may not rescue the tier — measure before shipping. Low priority; the composite fix already stops the bleeding. |
| ~~R10~~ | **Category-weighted composite score** | Medium | Medium | **RESOLVED 2026-07-20 — measured, no re-weighting.** The April premise inverted: 90d shows ML **+19.6%** (70) vs Total **-4.4%** (42), and every category flips sign between adjacent ~45d slices. The spread aggregate (+45.3%) is two opposite stories — WC spreads 5-31/-60% (realized ≈ market price, zero alpha on the claimed +6.6% edge) vs MLS spreads +246.8% (n=14 longshot luck); combined soccer spreads land dead on model fair. Dominant variation is sport×regime, not category — re-weighting would fit noise (the C4 lesson). Posture: watch-don't-tune; revisit only on a stable same-signed gap across two independent ~90d windows at n≥100. Soft follow-up logged: at the next major soccer tournament, check spread claimed-edge realization early (WC cohort ran at market, not model). Full writeup: `docs/my-documents/temp/r10-category-weights/README.md`. |
| ~~C6~~ | **Totals bias audit** | Medium | Small | **CLOSED 2026-07-20 with the R10 measurement pass.** The April +32% did not persist (90d -4.4%, slices -9.0% → +5.7%); nothing pathological either (64% WR at high prices). No action. |
| C9 | **Recalibrate soccer TOTAL stdev (1.5 → ~1.86)** | Low | Small | Follow-up logged 2026-06-29 during the spread de-vig investigation. `SPORT_TOTAL_STDEV["soccer"]=1.5` is empirically too *low*: 74 completed WC matches show a realized total-goals stdev of **1.86** (mean total 2.96), so the totals model runs a too-narrow distribution → over-confident over/under probabilities. **Left as-is deliberately** — soccer totals are currently profitable (75% WR / +24% ROI, n=24), so widening would *reduce* confidence on a winning path. Only raise toward ~1.8 with a deliberate calibration pass + backtest (pair with C6/C8). Note: under independent-Poisson goals, margin and total stdev should be ~equal; the de-vig fix already validated the **margin** stdev (1.8 ≈ Poisson 1.72) — this is the totals counterpart. Code carries a pointer comment at the `SPORT_TOTAL_STDEV["soccer"]` line. |
| ~~C8-followup~~ | **Fix C8 calibration statistics** | High | Small | **SHIPPED 2026-06-23.** Replaced the `n≥5` / `×1.5` / `[0.8,1.5]` recommender with a guarded one: `n≥20` per sport+market, a 1.5-SE significance gate, a gentler `×1.0` step clamped to `[0.85,1.25]`, and exclusion of settlements with no recorded `fair_value` (the 0.5-default contamination). Against the full 302-bet history this writes a single override (NCAAB margin 12.1→14.7 from 29 spread bets at a significant +21.8pp gap); all other sports hold at base, and the bad live cache was deleted. **Still open (deferred — needs more data / a bigger build):** the gap is still measured over gate-selected bets, so it can't fully separate stdev miscalibration from selection bias; a true per-game Brier/MLE fit, and the moneyline-heavy bet mix starving spread/total samples, remain the structural limits. |
| R23b | **Distinguish 401 vs 429 in Odds API key rotation** | Low | Small | F41 (2026-05-13 analysis). R23 rotates on both 401 and 429 and calls `mark_exhausted()` on 401. If the Odds API ever sends a 429 for transient per-second/per-minute rate limits (vs. quota exhaustion), a healthy key gets permanently dumped. Fix: only `mark_exhausted` on 401; on 429, short back-off then retry the same key. Inspect `X-Requests-Remaining` / `X-Requests-Last` headers when present. Low-urgency — no observed 429s today — but tightens the rotation contract before quota pressure increases. |
| R24c | **Audit `install_windows_task.py` vs live scheduler** | Low | Small | **Discovered during R24 investigation.** User has 13 tasks installed under `\Edge-Radar\` but `install_windows_task.py status` only knows about 5 profiles (scan, execute, settle, next-day, calibration). The 8 others (`All-Sports-SameDay-Execution`, `All-Sports-NoDateFilter-Execution`, `NextDay-Execute`, `Backtest`, `Calibration`, `Reconcile`, and 4 `Email-*` jobs) were created manually. Add the missing profiles so the installer has an honest view of what's running. Cosmetic but prevents future "where did this task come from?" confusion. **Note (2026-04-30):** U2 added 2 more (`Daily-Summary`, `Email-Daily-Summary`) — also installed manually. R24c scope grows by 2. |
| ~~C10~~ | **Futures composite: align the edge scale with sports** | High | Small | **SHIPPED 2026-07-23.** The futures composite scaled edge as `min(10, edge * 20)` (saturating at a **50%** edge) while sports uses `min(edge / 0.01, 10)` (saturating at **10%**) — identical weights and structure otherwise, one term **5x stricter**, no recorded rationale (launch-day commit `1d92f0f`; the `* 20` looks copied from the `liquidity` line above it). Consequence: clearing `MIN_COMPOSITE_SCORE=6.0` needed ~**11% edge at high confidence / 23% medium / 34% low** against championship-futures edges that run **1–4%**, so Gate 4 was structurally unreachable — **0 futures bets in 85 settled trades**, and it made **Polymarket US permanently unexecutable** (futures are its only executable market type, so the PM2 "prove edge in dry-run" gate could never terminate). Fix: both futures paths aligned to `min(edge / 0.01, 10)`; bar becomes ~2.1%/4.4%/6.6% at typical liquidity, binding in the same region as the 3–4% `MIN_EDGE_THRESHOLD` floors rather than dominating them. **Not a floodgate** — replayed on 4 days of live PM evidence it approves **none** of the 9 observed candidates alone; each stays blocked by Gate 3/3.5/4.5. Futures `high: 9` left alone (C4 scoped futures out; no futures settlement data either way). Live-verified on a real scan (NHL 4.36→4.8, Spurs 3.57→4.4, all still correctly gated). +6 tests incl. cross-venue scoring parity (645). **Docs:** new [`docs/polymarket/`](polymarket/README.md) domain folder (mirrors `docs/kalshi/`) — coverage matrix, futures/games/execution guides, Ed25519 API reference; two-way linked from the docs hub, the Kalshi README, and the setup guide. |
| ~~C11~~ | **Kelly was missing the `(1 - price)` divisor** | High | Small | **SHIPPED 2026-07-27.** `size_order()` sized off `kelly_fraction * edge * bankroll`. Kelly for a binary contract is `f* = (q - p) / (1 - p)` = `edge / (1 - price)`; the divisor was absent — the even-money (`b=1`) approximation, exact only at 50c. Favorites were under-sized by `1/(1-p)` (2.5x at 60c, 5.0x at 80c, **5.9x at 83c**), and because the flat `UNIT_SIZE` floor then won at high prices, nearly every bet above ~60c collapsed to **1 contract** (mean contracts by entry price: sub-40c 5.56, 40-60c 1.83, 60c+ 1.17). That starved the **best-calibrated band in the book**: over 367 settled trades, realized WR over break-even is sub-40c +3.4pts, 40-60c +3.9pts, **60c+ +11.1pts** (44/52 vs a 73.6% break-even, one-sided binomial **p=0.044** — the only band distinguishable from noise). Calibration inverts with price too: a **15.5-point overclaim** below 40c vs *conservative* by 2.9 points at 60c+. Last 30d: 60c+ **+4.7% ROI** vs sub-60c **-48.3%**. Re-sized over the settled history the 60c+ segment goes **+$10.02 -> +$47.52 at the same ROI**. Paired `.env` moves: `KELLY_FRACTION` 1 -> **0.5** (it is divided by `batch_size`, making it a *portfolio* fraction — at 1.0 a correlated slate reaches full Kelly), `UNIT_SIZE` .50 -> **1.00** (the longshot lane binds on the flat floor, not Kelly, so lowering `KELLY_FRACTION` alone would have cut sub-30c sizing 39%), `MAX_BET_SIZE` 15 -> **8** (backstop; $15 on a ~$92 bankroll is 16.3%, breaching the 10% hard stop — unreachable while Kelly was broken). `MIN_MARKET_PRICE` untouched. +7 tests (659). |
| ~~C11b~~ | **Correlation guard measured and dropped; budget cap made floor-aware** | High | Small | **SHIPPED 2026-07-27.** C11 left "add a correlation guard for same-night/same-league/same-direction slates" open. Measuring first killed the premise: the naive pooled estimate is **rho +0.181, p=0.0018**, but that is **Simpson's paradox** — clusters sit inside strata with very different base rates (totals win 82%, spreads 24%) and pooling unequal-mean groups manufactures apparent within-group concordance. Stratified, with a permutation test that shuffles *within* stratum: **rho +0.048** overall and, for **totals — the four-MLB-unders case that prompted it — rho -0.187 (p=0.75), i.e. nothing**. Even at +0.048, four bets behave like ~3.8 independent ones. **No guard built**; added `scripts/backtest/correlation_check.py` (reports both figures side by side) to revisit as settlements accumulate. Two things fell out. **Correction to C11:** the "32% of bankroll" figure justifying `KELLY_FRACTION=0.5` came from `size_order` in isolation and ignored `--budget`, which every scheduler passes and which scales the whole batch — real blast radius was already ~$11.03. **Regression:** the budget is a *fixed pool*, so C11's correctly-sized favorites crowd everything else out — the 18c MLS leg fell 6 contracts -> 2, which would have quietly starved the `MIN_MARKET_PRICE=0.10` longshot experiment rather than testing it. Fix: `_apply_budget_cap` now never shaves below a bet's flat unit floor, **bisects** for the largest feasible scale instead of one proportional pass, and drops whole orders (lowest composite first) *only* when the floors alone cannot fit — an earlier draft deleted a position to reclaim $0.23. Also: the scheduler `.bat` files passed `--unit-size .5`, **overriding the `.env` `UNIT_SIZE=1.00`** for every automated run, so C11's longshot protection never reached automation; all 16 now pass `--unit-size 1`. +8 tests (667). |
| ~~U1~~ | **Automated settlement cron** | Medium | Small | **SHIPPED 2026-07-20.** New `Hourly-Settle` Windows task (every hour at :35 — a slot clear of all existing task minutes) runs `kalshi_settler.py settle` directly. Enabled by M2's cross-process trade-log lock (concurrent settle+execute is now merge-safe — exactly what made hourly settling risky before). Fresher settlements also sharpen Gate 1 (daily-loss) accuracy intraday. `NightlySettle` (11 PM) kept as belt-and-suspenders during a validation week, **retired 2026-09-23**. Validated on install (`LastTaskResult=0`). See `docs/task-schedules/README.md` #22. |

##### Priority 3 — Background (Data Quality, UX, Hygiene)

Items that compound over months but don't block anything today.

**Sports data (Tier 2 origin)**

| ID | Item | Impact | Effort | Notes |
|----|------|--------|--------|-------|
| **B6** | **Four low-severity betting-logic defects (batched)** | Low | Small | **From the 2026-08-25 review (#11-#14).** Four unrelated small things, batched because each is a few lines and they touch adjacent code. **(a) Weather adjusts a total *after* the side is picked** -- `detect_edge_total` chooses YES/NO from the unadjusted fair value, then applies the weather probability shift and recomputes `edge` for the *already-chosen* side, so a shift large enough to flip which side is better cannot flip the selection. Apply the adjustment to `fair_value` before the comparison. **(b) `CATEGORY_MAP` prefix shadowing** -- `"KXEPL": "game"` matches `KXEPLSPREAD-...` by `startswith`; same for `KXUCL`, `KXLALIGA`, `KXSERIEA`, `KXBUNDESLIGA`, `KXLIGUE1`, `KXIPL`, `KXBOXING`. If Kalshi ever lists spreads or totals on those series they will be categorised `game` and priced with a **moneyline** fair value -- a guaranteed fabricated edge, not a subtle one. Match on the full series segment (`ticker.split("-")[0]`) or register the `*SPREAD`/`*TOTAL` variants ahead of the bare prefix. Pairs with **B2** -- same trap, other half. **(c) Log signal-to-noise** -- 10,252 `find_market_event` WARNING lines, of which **7,630 are benign "0 candidate events"** (books simply have not posted lines yet) and only 134 are the real ">1 candidate" ambiguity. 3,703 are `KXNFLSPREAD` and 2,907 `KXNFLTOTAL`, because Kalshi lists the whole NFL season while books post ~a week out. Drop "0 candidates" to DEBUG, keep ">1" at WARNING. Separately: scans are still pricing **June** markets in late August (`KXNBAGAME-26JUN10SASNYK`), so the `expected_expiration_time` filter is not dropping settled Finals markets -- worth a look while in there. **(d) Hardcoded EDT offset** -- `_ET_UTC_OFFSET_HOURS = 4`. The docstring argues a 1-hour EST/EDT slip is immaterial "against the multi-hour matching window", which is true for the moneyline +/-6h path but **not** for the spread/total and NBA/NHL path, which uses *exact ET-date equality*. A game commencing 04:00-05:00 UTC in winter is 11pm-midnight EST (8-9pm PT, prime West Coast tip-off); at the hardcoded -4 it resolves to the *next* ET date, `same_day` finds zero candidates, and the market is silently skipped. NBA/NHL only, November-March -- i.e. it starts biting this season. Use `zoneinfo.ZoneInfo("America/New_York")`; stdlib, no new dependency. |
| S3 | Bullpen availability tracker | Medium | Medium | IPs over last 2-3 days per reliever; tired bullpen → overs in late innings. Depends on S1 (done). |
| S4 | Injury impact scoring | Medium | Medium | Star-player status from ESPN injury report; adjust fair-value confidence -10-20% when key player questionable. |
| S6 | Wind direction classification | Low | Small | NWS wind bearing vs stadium orientation — blowing out (overs) vs blowing in (unders). |
| S7 | Umpire tendencies | Low | Medium | Strike-zone size by umpire, small edge on MLB totals. |
| S8 | Platoon splits | Low | Medium | Batter vs LHP/RHP via MLB Stats API. |

**Prediction market models (Tier 4 origin)**

| ID | Item | Impact | Effort | Notes |
|----|------|--------|--------|-------|
| R25b | **TTL caches for prediction-market modules** | Medium | Medium | F34 (2026-04-24) — all 6 modules have module-scoped caches that never invalidate. Crypto 7-day history cached at first scan of the day, used all day. Weather NWS forecast cached until process restart. SPX price cached for hours. Replace raw cache dicts with `(timestamp, value)` tuples and check age on read. Suggested TTLs: crypto 1h · weather 6h · spx 5min · mentions/companies 24h · politics never. Blocks M1-M4 — rebuilding models on top of stale-cache infra is wasted work. |
| R25c | **Rebuild one prediction model with tests, then port the pattern** | Medium | Large | Pick crypto (cleanest data source, most familiar). Write `test_crypto_edge.py` with frozen fixtures + calibration checks. Fix the obvious bugs uncovered in the audit: hardcoded vol fallbacks, one-sided-liquidity YES-picking bias, sub-10¢ tail markets producing 80% "fair values". Once the pattern works, clone to spx/weather/mentions. **Blocks M1-M4.** |
| M1 | Ensemble crypto fair value | Medium | Large | Current is CoinGecko price + trend only. Add implied vol, funding rates, on-chain, momentum. **Gated on R25c** — don't expand a broken foundation. |
| M2 | SPX volatility model | Medium | Small | Use VIX to build a price-target distribution; current model uses moving average. **Gated on R25b + R25c.** |
| M3 | Weather-model calibration | Low | Medium | Calibrate hand-coded impact % against historical NWS forecast vs actual. **Gated on R25b + R25c.** |
| M4 | Mentions seasonality | Low | Small | Election / event seasonality in TV-mention predictions. **Gated on R25b + R25c.** |

**UX & automation (Tier 5 origin)**

| ID | Item | Impact | Effort | Notes |
|----|------|--------|--------|-------|
| U3 | Interactive pick mode | Low | Medium | Pick rows directly from preview instead of rerunning with `--pick`. **Note (2026-04-29):** R26 (scan cache + replay) made the two-call `--pick` workflow safe by locking row order across invocations, so the original motivation here is mostly resolved. Still nice-to-have for one-fewer-command ergonomics, but not load-bearing. |
| U4 | Single-command session | Low | Medium | `scan.py session` = status + settle + scan + preview. |

**Futures market coverage (2026-04-24 audit, Phase 3)**

| ID | Item | Impact | Effort | Notes |
|----|------|--------|--------|-------|
| R19 | **Expand futures coverage & name matching** | Low | Medium | Scanner audit (2026-04-24) surfaced four gaps in `futures_edge.py`: (a) `FUTURES_ALIASES` only covers a subset of teams — many Kalshi candidates silently fail name-match against Odds API outcomes. Complete team-name coverage for NBA/NHL/MLB. (b) ~~Golf majors not configured~~ **SHIPPED 2026-06-20** — root cause was that `KXPGATOUR` spans the *entire* PGA Tour (weekly stops + majors + qualifiers) while The Odds API only carries the 4 majors. Fix: `_golf_major_key()` resolves the major from the market title (not the cryptic event code), routes to the correct per-major odds key (`golf_us_open_winner`, `golf_pga_championship_winner`, `golf_masters_tournament_winner`, `golf_the_open_championship_winner`), and skips weekly stops + qualifiers (no odds feed → no edge). `--filter pga` now routes to the futures scanner. Validated live: U.S. Open priced 71 players across 3 books, 2 edges surfaced (both gated). +7 tests. (c) **Re-add the 5 entries R22 removed once proper data sources exist**: `KXMLBPLAYOFFS` (needs "make MLB playoffs" outrights), `KXNBAEAST`/`KXNBAWEST` (need conference-winner outrights), `KXNHLEAST`/`KXNHLWEST` (same). Free Odds API tier doesn't appear to have these. (d) Evaluate whether NCAAB Tournament outright is worth adding. Wait until off-season MLB/NBA when futures betting becomes primary focus. |
| S9 | **Re-verify NCAA basketball coverage when the season returns (~Nov 2026)** | Medium | Small | NCAA men's (`--filter ncaamb`, `basketball_ncaab`) and women's (`--filter ncaawb`, `basketball_wncaab`) basketball are **already fully wired** (game/spread/total for men's). They're dormant now only because it's the offseason — no markets, no odds. When the 2026-27 college season tips off (early-mid November), run a live scan to confirm Kalshi `KXNCAAMB*`/`KXNCAABB*` markets resolve against Odds API events end-to-end (matching, edge floors at 0.04, gate previews). No code expected — this is an activation/verification checkpoint, not a new build. |

**Dashboard (Tier 5a origin) — ~~DROPPED 2026-08-25~~**

> The Streamlit dashboard (`webapp/`) was **removed from the repo on 2026-08-25** and the hosted app retired. Every open D-item (D3 favicon, D6 scan-result caching, D10 mobile tweaks, D12 scan-comparison view, D13 risk dashboard page, D15 watchlist page, D17 sidebar toggle, D18 remote-access guide, D19 `/healthz`) targeted that app and is dropped with it — the CLI plus the emailed scheduler reports are the operating surface. Shipped D-items stay in the Completed index as history. A future UI, if any, starts from the Priority 4 track (service layer → API → new front end), not from the Streamlit code.

**Simplification & hygiene (Tier 3 origin)**

| ID | Item | Impact | Effort | Notes |
|----|------|--------|--------|-------|
| H2 | Split `requirements.txt` into core / dev / research | Low | Small | Alpaca, Playwright, SQLAlchemy etc. aren't in the live path. |
| H3 | Separate runtime state from source tree | Low | Small | Consistent gitignore for `data/`, `logs/`, `reports/`, `__pycache__`; consider dedicated `runtime/`. |
| H7 | **Externalize `BOOK_WEIGHTS` into config** | Low | Small | F42 (2026-05-13 analysis). Sharpbook weights (Pinnacle/Circa 3×, etc.) are hardcoded in `edge_detector.py`. Books change tier occasionally and the values are inherently empirical. Move to a JSON/YAML file alongside other tunables; load through `app/config.py`. Natural pair with C8 — both are "empirical knobs that live in source today." |
| H8 | **RSA key rotation documentation** | Low | Small | F43 (2026-05-13 analysis). `keys/` is gitignored and never logged, but there's no operator runbook for *rotating* the Kalshi RSA keypair (generation cadence, Kalshi-side update, local key swap, verification). Add a short section to `docs/setup/SETUP_GUIDE.md` or a new `docs/SECURITY.md`. Pure docs. |
| Q6 | **Package `scripts/` or retire `sys.path` hacks** | Medium | Large | `pyproject.toml:13` packages only `app*`, so `scripts/` (where most logic lives) relies on pytest `pythonpath` + `.pth` + manual `sys.path.insert()` in `app/domain/opportunity.py`. Blocks clean editable installs, CI portability, and eventual PyPI/Docker packaging. Low urgency (working today), high cleanup value. Natural pair with A2. |
| GT2 | **Sizing-cap tail has no single reference** | Low | Small | **From the 2026-09-03 gate-consolidation review.** A single order can pass through up to 8 sequential size-adjustment steps -- NO-side Kelly damping, the price-complement Kelly calc, `MAX_BET_SIZE`, the Gate 2b exposure-headroom trim, the bankroll final check, the venue minimum-share bump, `_apply_bet_ratio_cap`, and `_apply_budget_cap` -- spread across three functions (`size_order`, `_apply_bet_ratio_cap`, `_apply_budget_cap`). Each step is individually well-documented in its own docstring and none should be merged (each bounds a genuinely different resource), but there's no single place a reader can see the full order of operations. Pure documentation task: add one reference table/comment near `size_order` (the review's Section B is a first draft). |
| GT3 | **`MAX_MARKET_PRICE=0.75` (Gate 3.55) ships with no settled evidence** | Low | XS | Shipped 2026-09-03 on operator preference alone -- unlike its sibling `MIN_MARKET_PRICE` (R7, backed by a 14-day review showing sub-10c bets 1W-3L), the 75% cost/payout ceiling has no data behind it yet. Not a defect; flagging it the same way `MIN_MARKET_PRICE=0.10` is flagged as an open experiment (see S22). **Recheck** once the gate has actually rejected (or would have rejected via `preflight_gate_status`'s `price-hi` label) some real candidate bets, to see whether 75% is binding at all or just sitting unused. |

**Testing (Tier 7 origin)**

| ID | Item | Impact | Effort | Notes |
|----|------|--------|--------|-------|
| T1 | Integration tests (mocked workflows) | Medium | Medium | scan→risk→preview, scan→save→execute, settle→report→CLV, API-failure paths. |
| T2 | API mocking | Medium | Small | Deterministic Kalshi / Odds API / ESPN fixtures. Prereq for T1. |
| T3 | CI/CD pipeline | Medium | Small | GitHub Actions: pytest on PR, import-smoke job, lint, detect-secrets. **Re-flagged in 2026-04-22 analysis** — only `deploy.yml` exists today; no automated guardrail against test regressions, import breakage, or packaging drift. Impact upgraded from Low to Medium. |

##### Priority 4 — Web App Evolution (Tier 6 origin)

Multi-quarter track. Build order: A2 → A3 → A4+A5 → A6+A7+A8 → A9. Assumes R5 completes first so DB migration doesn't inherit the trade-log/settlement gap.

> **Streamlit removed 2026-08-25.** There is no web surface today — the CLI and the scheduled email reports are the operating surface. That doesn't change this track's build order (it always started from the service layer, not the UI), but A2–A8 are now the whole of it until someone actually wants A9; nothing here is blocked by the removal. The A10/A11 rows below shipped against the retired dashboard and are kept as history only.

| ID | Item | Impact | Effort | Notes |
|----|------|--------|--------|-------|
| ~~A10~~ | **Cloud secrets registry (silent env-var drop)** | High | Small | **SHIPPED 2026-07-31 — code removed 2026-08-25 with the dashboard.** `webapp/services.py` carried a hand-maintained `_flat_keys` list naming which flat TOML keys to lift from `st.secrets` into the environment. It must exist — the lift happens *before* any script import caches config, so it cannot introspect `app.config` — but it was last extended in April. Everything added since was absent: the R28 NO-side globals, both L1 live-bet gates, `MIN_CONSENSUS_BOOKS_NBA`, `CALIBRATION_STDEVS_TTL_DAYS`, `CROSS_CATEGORY_DEDUP` (global + per-sport), both cache groups (R24b/R26), and every Polymarket credential. **Failure mode was silent and Cloud-only:** set one in *Settings → Secrets* and nothing reads it, no error, while the app runs on the code default. Local `.env` was unaffected (`python-dotenv` loads wholesale), which is why it went unnoticed. Replaced with one `ENV_VAR_SPEC` registry serving the bootstrap, the Config page, and the reader; `tests/test_webapp_env_registry.py` parses `app/config.py` and fails on divergence in either direction. Writing that test surfaced nine more undocumented vars (`KALSHI_PROD_*`, `ALPACA_*`, `TELEGRAM_*`, `PROJECT_ROOT`) — the same gap the 2026-07-14 repo review flagged against `.env.example`, now closed there too. |
| ~~A11~~ | **Config page** | Medium | Small | **SHIPPED 2026-07-31 — code removed 2026-08-25 with the dashboard.** Read-only view of what the running process is actually configured with: execution mode per venue, then every variable with live value, source (`set` / `default` / `unset`), group, and rationale. Credentials render as a character count only. Exports a `.env` template with live values and secrets blanked. Answers "is the app actually running my config?" — previously unanswerable from the UI and genuinely ambiguous because `kalshi_executor` snapshots gates at import time (H9 reloads them per scan/execute, but not the import-time summary). |
| A2 | Extract service layer | Critical | Large | Isolate edge calc, risk sizing/gating, fill accounting, Kalshi client from CLI concerns. New `app/services/`. |
| A3 | Replace JSON state with database | High | Medium | Postgres (prod) / SQLite (dev). Tables: `scan_runs`, `opportunities`, `risk_decisions`, `orders`, `fills`, `positions`, `settlements`, `bankroll_snapshots`, `audit_events`. **Supersedes T4.** |
| A4 | FastAPI backend | High | Large | REST layer: `POST /api/scans`, `GET /api/opportunities`, `POST /api/opportunities/{id}/execute`, `GET /api/positions`, `GET /api/settlements`, `GET /api/portfolio/summary`, etc. |
| A5 | Idempotent execution | High | Small | Client-generated idempotency key + server-side pre-submission record + market/order locks. |
| A6 | Background job runner | Medium | Medium | Scheduled scans, order-status refresh, fill sync, settlement ingestion, daily rollups. APScheduler (MVP) → Celery/Redis if needed. U1 is a smaller standalone version of this. |
| A7 | Concurrency controls | Medium | Medium | Locks around scan-triggered execution, order submission, position refresh. |
| A8 | Web secrets handling | Medium | Small | Encrypted secret storage; no raw key-path assumptions in request handlers. |
| A9 | React / Next.js dashboard | High | Large | Overview, Scan Runner, Opportunity Review, Trade Ticket, Orders & Fills, Positions, Settlements & Performance, Settings. Depends on A4. |

##### Deferred / Blocked / Superseded

| ID | Item | Reason |
|----|------|--------|
| **B7** | Fetch sharp books (`regions=us,eu`) | **BLOCKED on an operator quota decision, opened 2026-08-25 (review #3).** `BOOK_WEIGHTS` gives Pinnacle 3.0, Circa 3.0 and Bookmaker 2.5 -- but `fetch_odds_api` requests `regions=us`, and Pinnacle is an `eu`-region book on The Odds API. Across 37 cached odds files those three appear **zero times**: the books actually arriving are draftkings 527, fanduel 309, betus 281, betonlineag 257, bovada 233, betrivers 203, betmgm 200, mybookieag 144, lowvig 140. Effective weights in play are 0.7 (five books), 1.0, 1.5 (two) and 2.0 -- so the docstring's "sharp books count more than recreational" is **not true as configured**, and the whole weighted-median scheme resolves to a mild tilt toward two offshore books. **Why blocked, with the numbers:** adding the `eu` region doubles the credit cost of every call. Measured burn is **~65 calls/day (peak 158)** against **1,548 credits remaining** (3 keys x 500, 1 x 48, 8 exhausted) = **~24 days of headroom**; at `us,eu` that becomes ~130/day and **~12 days**, exhausting mid-cycle. **Three options, operator's call:** (a) add keys; (b) apply `eu` only to the pre-execution scan rather than all ~10 daily scheduled scans; (c) lengthen the pre-game cache TTL first to free headroom, then revisit. Whichever is chosen, prune `BOOK_WEIGHTS` to books that actually arrive so the config stops implying a precision it does not have. Related: **H7** (move `BOOK_WEIGHTS` out of source) and **R23b** (401 vs 429 rotation), both of which touch the same quota surface. |
| R6 | Audit Gate 2 batch-counter | **Dropped 2026-04-21.** Original evidence ("16 open vs MAX_OPEN_POSITIONS=10") read the code default, not the live `.env` (which is 50). At 16/50 there is no over-limit bleed. The latent batch-counter question is real but low-value without an actual exposure issue — revisit only if a future run shows approvals compounding past the cap. |
| C4 | Review "high confidence" bump | **Reactivated 2026-06-23 → now Priority 2.** Deferral condition met (118 high-conf trades, F49); High still underperforms Medium. |
| C2 | Bump per-sport stdev 10-20% | **Merged into R2** (more specific sport-by-sport prescription). |
| C7 | Re-run calibration monthly | **Merged into R12** (same action, concrete trigger at 100 trades). |
| D17 | Fix sidebar toggle | **Dropped 2026-08-25** with the rest of the Streamlit dashboard. (Was blocked — Material icon font rendered broken in dark theme.) |
| T4 | SQLite trade DB | **Superseded by A3.** |
| U5 | Persistent odds cache | **Subsumed by R24b** (2026-04-24) — tracked as P2 with live motivation. |
| R20 | Prediction-model audit | **Shipped 2026-04-24.** See Completed index + F34-F39. M1-M4 gated on R25b/R25c. |
| H1 | Centralize config into typed settings | **Resolved by H6** (2026-04-25). H5 did knob reduction; H6 built `app/config.py` as the single source of truth. |

---

#### Findings & Context

##### 2026-08-25 — Betting-logic review + calibration study (14 findings, 5 fixed same day)

First run of the new `/betting-logic-review` skill, followed by a calibration study built to
answer the question none of the risk knobs ask: **is the claimed edge real?**

Full writeups: `docs/my-documents/repo-reviews/2026-08-25-betting-logic-review.md` and
`2026-08-25-calibration-study.md`. Shipped as CHANGELOG **F1-F4**.

| ID | Finding | Evidence | Action |
|----|---------|----------|--------|
| F1 | **Trading fees were invisible in both directions.** Not modelled pre-trade, and the Kalshi **v2 create-order response carries no `taker_fees_dollars`** (nor `status` — hence 129 of 166 rows logging `"unknown"`), so every trade recorded a fee of 0 and settlement computed `net_pnl = revenue - cost - 0`. | $16.40 unrecorded fees against $38.01 gross P&L — **43% of the return**. 1.02c/contract against a 3-4c edge floor. | **Shipped** — `scripts/shared/fees.py`; Gate 3 floor and Kelly both net of fee; settler backfills from `/portfolio/fills`. `KALSHI_FEE_RATE` knob. |
| F1b | **The venue rejected every order for 5 days, silently.** Kalshi geo-blocked the account 2026-08-20 ("Nevada residents are not currently allowed..."). Every trade-log consumer *filters* `status == "error"`, so a dead venue produced no signal anywhere. | 13 consecutive rejections, 08-20 → 08-24. The 4:50 AM digest reported five clean days. | **Shipped** — rejections now print above the P&L, grouped by reason. **The block itself is unresolved and is an account question.** |
| F2 | **The limit price was posted one cent below the ask.** `int(price * 100)` truncates; `0.29 * 100 == 28.999999999999996`. | 29c, 57c, 58c affected. All three such orders in the log are `fill_status: "resting"` — 3 of the 4 resting rows in the entire history. | **Shipped** — `math.ceil(round(price*100, 6))`. The `ceil` is load-bearing for Polymarket, whose Gamma `bestAsk` is not cent-aligned. |
| F3 | **World Cup is a −43.2% ROI drain, and its justifying rule is overturned.** `SPORT_MARGIN_STDEV` claimed the always-YES soccer-spread lean was "a REAL edge (placed spreads hit 31% vs 19% paid)". | 43 settled WC bets, all YES: model 22.9% / market 16.3% / **reality 13.9%**. Across 53 soccer-family spreads: model 21.7%, market 15.5%, **realised 15.1%** — the market was near-exact. | **Shipped** — WC off via `MIN_EDGE_THRESHOLD_WORLDCUP=1.0`; the betting-outcome half of the soccer note retracted in code (physical Poisson/Skellam argument kept). |
| F3b | **`MIN_EDGE_THRESHOLD_*` was a silent no-op for 8 of 16 sports.** `_SUPPORTED_SPORTS` in `app/config.py` listed 8 names; `ticker_display._detect_sport()` returns 16. Setting an override for worldcup / ufc / boxing / golf / nascar / ipl / esports / tennis did **nothing**, with no error. | Found when the first attempt to floor World Cup out had no effect. | **Shipped** — all eight added; a test now fails if any `_detect_sport` output is orphaned again. |
| F4 | **The YES/NO asymmetry is the single largest effect in the book** — larger than F45 measured, and it holds *within* price bands, so it is the side and not merely that NO bets sit at expensive prices. | **YES +22.4% ($224) vs NO −7.7% ($157).** YES wins every shared band. NO bleed concentrated at/above 50c: n=68, $90, **−11.3%**. The 35-50c NO pocket is the exception at **+5.3%** and positive in both eras. | **Shipped** — `NO_SIDE_KELLY_PRICE_CEILING=0.50` (mirror of R1's floor, same multiplier). Damped not gated: that population is +4.8% Mar-May vs −16.0% Jun-Aug. |
| F5 | **The model's probabilities are measurably worse than the price it bets against.** | Brier: market 0.2037 vs model 0.2270, **market better in 6 of 6 months**, 95% CI on the difference excludes zero. Brier-optimal weight on the claimed edge **λ = 0.16, CI [−0.04, +0.42]**. Real signal on cheap contracts (≤32c: +10.8pt lift from high claimed edge) but it **inverts on favourites** (≥51c: −10.8pt). | Recorded as a standing rule in `CLAUDE.md`: treat any claimed edge as ~5x optimistic; **do not add sizing aggression without re-running `calibration_study.py`**. Shrinkage was evaluated and **rejected** in favour of F4 (in-sample λ sweep was non-monotone = overfit). |
| F6 | **`high` confidence is NOT the loser — an earlier recommendation of mine was wrong.** Brier ranks high worse than medium, but money ranks it better. | high **+13.3% ROI** (n=117) vs medium +9.8% (n=248). The Brier gap reflects high-confidence bets clustering at low prices, where being directionally right pays despite an over-claimed magnitude. | **No change.** C4's existing composite cap stands. Recorded so the recommendation is not re-derived. |

**Two corrections to my own analysis, recorded because they were load-bearing:**

1. The betting-logic review's ROI figures came from `kalshi_trades.json`, **clobbered 2026-06-03**
   and holding only 119 June-onward rows. On the full settlement log (380 settled) the book is
   **+10.0%, not −20.1%**, and **spread is the best category at +39.7%, not the worst**. The repo's
   own analytics all read the settlement log correctly — this was a sampling error on my part, not
   a defect.
2. Review findings **#5 and #6 both shrank materially** once measured against real cached books
   rather than reasoned about: #5's typical error is 0.00pt (not ~1.5pt) and lives almost entirely
   in NFL; #6 affects 0% of bettable moneylines and spreads. Both remain worth fixing (**B1**), but
   for the tail and the timing, not the average.


##### 2026-07-31 — MLB high-strike totals dominate the book (operator observation → T1/T2)

Operator flagged that "under 13.5 or so runs in baseball" bets seemed to be placed far more often than anything else. Confirmed, and understated.

**Concentration — and the 27%-of-book figure badly understates it.** MLB totals did not exist in the book until **2026-07-20**, when the MLB spread/total coverage gap was closed (see that entry in Completed). Split on that date:

| Window | Trades | MLB totals | Share |
|:--|--:|--:|--:|
| Before 2026-07-20 | 70 | **0** | 0% |
| On/after 2026-07-20 | 45 | **31** | **69%** |

So the honest headline is not "27% of the book" — it is that **within 11 days of the coverage landing, one bet shape took over more than two-thirds of all betting.** 28 of the 31 are NO-side, and the same window contains only 7 MLB moneylines. Nothing in the gate chain prevents it: each bet is a *different game*, so `MAX_PER_EVENT` and series dedup never engage, and `CROSS_CATEGORY_DEDUP` only collapses categories within a single game.

**Calibration.** The 28 settled NO bets went **18W-10L (64.3%)** against an **80.1%** market-implied break-even → **−12.6% ROI (−$6.28)**.

| Compared against | Implied win rate | Actual | One-sided binomial |
|:--|:--|:--|:--|
| Market price at entry | 80.1% | 64.3% | p = 0.038 — marginal at n=28 |
| **The model's own claimed fair value** | **89.7%** | **64.3%** | **p = 0.0003** |

The second row is the durable finding. Whether these bets are exactly −EV is not settled by 28 samples, but the model being wrong about them is.

**Caveats, stated honestly.** All 28 bets fall in a single **11-day window** (07-21 → 07-31), so this is not a broad sample of the season and late-July scoring conditions are a real confound. Two checks were run against that: losses are **not** concentrated in one bad day (only 1 of 11 days had zero wins, n=1), and treating each *day* as the unit rather than each bet gives a 66.5% mean win rate — close to the per-bet 64.3%, so the result is not an artifact of a few heavily-bet days. The time trend is the more useful cut:

| Window | Record | ROI |
|:--|:--|--:|
| First 5 days (07-21 → 25) | 11W-1L | **+6.7%** |
| After (07-26 → 31) | 7W-9L | **−18.3%** |

An early hot streak masked the shape for a week. That pattern is itself a caution against reading the first days of any newly-opened market as validation.

**Mechanism.** `consensus_total_prob` infers a mean total from the sportsbook line (~8.7 runs) and extrapolates to the Kalshi strike with a **normal CDF** at `SPORT_TOTAL_STDEV["baseball_mlb"] = 3.45`. Strike 13 is **1.25σ** out — far enough that the answer comes from the stdev assumption, not from any book quote. There is a **disagreement sweet spot**: near the line model and market agree; far out both approach 100% NO; around 1.25σ the model says 89% NO against the market's 80%. Every MLB game lists a strike in that window, so every game emits one near-identical NO bet. **R28's global NO floor is 8% and the phantom edge averages 9.6%** — the gate built to stop bad NO bets sits just under the bias.

**Ruled out.** The intuitive explanation — a normal CDF understating the right tail of a skewed run distribution — is wrong here. A negative binomial with the same mean and variance gives a *lower* P(>13) (9.0% vs 10.6%), which would make the model's NO fair value higher still.

**Most likely driver: adverse selection.** The model bets the games where its own noisy inferred mean sits lowest relative to the strike, which preferentially selects the cases where that estimate is most wrong — the same winner's-curse pattern C4 found for high confidence and C11 found for sub-40c prices.

**Relation to C11b.** That investigation measured *correlation* among the "four MLB unders on one night" slate and correctly concluded no guard was needed (totals rho −0.187, p=0.75). It never asked **why there were four unders**. This is the answer: not a correlation problem, a generation problem. C11b's conclusion stands; its question was the wrong one.

**T2 was verified the same day and is closed — no bug.** The hypothesis was that Kalshi's strike-13 market resolves on "13 or more" while the model computes `P(> 13)`, a 3.1-point systematic error toward NO on every totals bet in every sport. It is wrong on every count: the ticker suffix is not the strike (`floor_strike` is **12.5**), `extract_strike()` reads `floor_strike` and not the suffix, Kalshi's rule text and `strike_type: greater` match the model's `1 - norm.cdf(12.5)` exactly, and `floor_strike` is a half-integer on 28/28 markets so no integer total can tie it. Worth recording because the negative result is load-bearing: the cheap single-line explanation is eliminated, so T1's cause is in the model or in bet generation.

##### 2026-07-31 (same day) — the extrapolation-distance cap was measured and rejected; root cause is stale stdev calibration

The proposed T1 fix was to **cap extrapolation distance** — reject a totals bet whose strike sits more than ~1σ from the model's inferred mean, on the reasoning that past that point the answer comes from `SPORT_TOTAL_STDEV` rather than from anything a sportsbook quoted. Backtested first. **It does not survive.**

New tool: `scripts/backtest/totals_distance_check.py` (re-runnable, mirrors `correlation_check.py`). Distance is recovered by inverting the normal CDF from the stored `fair_value`, since `z = (strike − inferred_mean) / stdev` is exactly what the model applied. Over **136 settled totals bets** (the settlement log, not the 41-row trade-log slice used in the first pass):

| \|z\| bucket | n | W-L | WR | claimed | ROI |
|:--|--:|:--|--:|--:|--:|
| < 0.5 | 67 | 34W-33L | 51% | 60% | −1.1% |
| 0.5 – 1.0 | 32 | 18W-14L | 56% | 73% | **−29.5%** |
| **1.0 – 1.5** | **29** | **23W-6L** | **79%** | 89% | **+5.8%** |
| 1.5 – 2.0 | 5 | 4W-1L | 80% | 95% | −49.1% |
| > 2.0 | 3 | 2W-1L | 67% | 99% | −3.9% |

**The 1.0–1.5σ band — exactly where the MLB strike-12.5 bets sit — is the only profitable bucket.** A cap at 1σ would have deleted the best band and kept the −29.5% one. Hypothesis rejected; no cap built.

**What the data actually says.** The over-claim is *uniform across every bucket* (+9, +17, +10, +15, +32 points; **+12% overall**, **+16% MLB-only**). A bias that does not vary with distance is not a distance problem — it is **stdev calibration**, which is already C8's job.

**Root cause: the C8 loop was correct but stale.** Running `model_calibration.py` today prints `Calibrate baseball_mlb/total: base=3.45 gap=+16.1% (n=28, se=0.085) -> 4.00 (x1.161)` — it independently derives the same +16% the backtest found. But the live cache (written 2026-07-27) still held **3.45, byte-identical to the hardcoded default**. Why: MLB totals coverage landed **2026-07-20**, so on 07-27 fewer than `_MIN_CALIB_SAMPLES = 20` had settled and the sport was *skipped*; the next scheduled `MonthlyCalibration` was not until 08-01. **The flood ran for the entire blind window.**

**Action taken:** ran the calibration. `total_stdev.baseball_mlb` **3.45 → 4.005**, verified live via `_get_total_stdev()`. Note `data/cache/calibration_stdevs.json` is gitignored, so this change appears in no diff.

**Effect, replayed over the 25 settled MLB NO-totals:**

| | count | actual result |
|:--|--:|:--|
| Now blocked at Gate 4.6b (edge falls under the R28 8% NO floor) | **21 of 25** | 15W-6L, −$1.09, −3.1% ROI |
| Still placed | 4 | 3W-1L, −$5.19, **−63.4% ROI** |

**Read this honestly: the concentration is fixed, the selection quality is not.** Widening the stdev removes 84% of the shape — the volume problem the operator spotted — but the four bets that still clear the floor are the *worst* performers in the group. That is the same "large claimed edge = model error" pattern C4 found for confidence and C11 for sub-40c prices, and it is why `KELLY_EDGE_CAP` exists. At n=4 that −63% is noise-level, so it is a signal to watch, not a result.

**Structural gap worth fixing separately (T3).** `_MIN_CALIB_SAMPLES = 20` combined with a **monthly** cadence means any newly-opened market can bet uncalibrated for up to ~30 days before the loop is allowed to correct it. MLB totals opened 07-20 and produced 69% of the book inside that window. Options: run calibration weekly rather than monthly, trigger it when a (sport, category) pair first crosses 20 settled bets, or hold newly-covered market types to a higher edge floor until calibrated. Nothing shipped — this needs a deliberate choice.



##### 2026-07-14 — 30-day review + MLB volume diagnosis (42 settled trades)

Source: 30-day settled review (2026-06-14 → 07-14) prompted by "not many wagers
being placed." **The premise was wrong** — 42 bets were placed (1.4/day, tapering
to 0.6/day); the problem was concentration and losses, not volume starvation.

- **F50 — World Cup monoculture.** 41 of 42 bets were World Cup; 0 MLB, 1 NHL. The
  schedulers scan all sports unfiltered, but World Cup's pre-de-vig inflated spread
  edges out-ranked everything else for the `--max-bets` slots. Book bled −43% ROI
  (12W–30L, L9 streak).
- **F51 — sub-15¢ longshots are −EV, full stop.** The <15¢ price bucket went 0W–21L,
  −100%, −$14.53 — mostly World Cup spread-YES. By side: NO 5–0 (+17%), YES 7–30
  (−54%). By price: everything ≥25¢ was profitable. → Raised `MIN_MARKET_PRICE`
  0.06→0.12 (see Completed 2026-07-14). Not a code bug — the 06-29 de-vig already
  neutralized the always-YES *mechanism*; this is a settled-outcome calibration call.
- **F53 — MLB was never a model problem: it is expensive NO bets on totals
  (ANSWERED 2026-09-10, S20c).** MLB has been carried since 2026-08-31 as the
  sport with a Brier "worse than a coin flip" and an unexplained -6.4% ROI,
  blamed first on Odds-API quota starvation (S20 — unsupported, S20b) and then
  on the model. It is neither. By category: **moneyline +1.2% (n=109), totals
  -12.8% (n=42)** — two thirds of the block is positive and the entire loss is
  one market type. Totals wins **71% (30-12)** while losing money, which rules
  out a consensus explanation on its own; the cause is that **33 of 42 are NO
  bets at a median 0.80 entry**, F4's worst band. Already gated by Gate 3.55
  (`MAX_MARKET_PRICE=0.75`, 2026-09-03; verified no leak). **Do not tune the
  MLB model on this** — MLB moneyline was never broken. Recheck after ~20 more
  settled totals; n=4 post-gate proves nothing.

- **F52 — MLB at zero is crowding, not an MLB bug (OPEN).** MLB placed 0 executed
  bets in 30 days despite daily scanning. Likely cause: World Cup's phantom edges ate
  every slot. Should self-correct now WC is ending + de-vig shipped + longshot floor
  raised. Recheck due 2026-07-17/18 — see Priority 2 (M1) and
  `docs/my-documents/temp/mlb-executable-bets/README.md`.
- Quota healthy (2,465 Odds API requests remaining). Balance $85.75, avg bet $0.67.

##### 2026-06-23 — 90-day comprehensive review (302 settled trades)

Source: 90-day post-mortem over all 302 settled trades since launch (2026-03-22 → 2026-06-23), focused on sport performance, YES/NO pricing bias, model calibration, and longshot pricing. The working analysis doc lived under git-ignored `docs/my-documents/` and has been retired — its actionable conclusions are folded into the findings below (F45–F49) and the items they point to. Most of its *codebase* recommendations re-derived items already tracked here: BOOK_WEIGHTS→config (H7), prediction-cache TTLs / model rebuild (R25b, R25c), runtime-state split (H3), `scripts/` packaging (Q6), scheduler-inventory alignment (R24c), JSON→SQLite (A3).

> **Caveat on F45 (read before re-weighting on the YES/NO split):** YES and NO show *identical* ~48% win rates, so the entire ROI gap is a price/payout effect — which overlaps heavily with the longshot finding (F48: cheap contracts print, expensive ones don't). NO bets skew toward higher-priced favorites; YES toward cheaper underdogs. So "NO-side pricing premium" and "longshot outperformance" are likely two views of one price-dependence, not independent effects. R28 (conservative: raise the NO floor) is a reasonable hedge, but treat it as a **2–4 week experiment** and re-test the YES/NO split *controlled for price bin* before trusting the causal story.

| ID | Finding | Evidence | → Action |
|----|---------|----------|----------|
| F45 | **Extreme YES vs. NO asymmetry** — YES bets yield a highly profitable +48.1% ROI, whereas NO bets yield -7.0% ROI on similar win rates. Indicates structured pricing premium/spread friction on NO contracts. | YES: 100W–107L, Cost $176.17, P&L +$84.70. NO: 46W–49L, Cost $92.65, P&L -$6.48. | R28 |
| F46 | **NBA Underperformance** — NBA bets continue to be a net drain on the portfolio (-23.3% ROI), contrasting starkly with MLS (+137.3%) and NHL (+62.1%). | 32 NBA bets, Cost $50.43, P&L -$11.74. | R29 |
| F47 | **Model Calibration Overconfidence** — Predicted probabilities are consistently 11% to 15% higher than realized win rates in the 50%-80% bands. | 50-60% band: 41.8% WR vs 56.1% predicted. 60-70% band: 52.4% WR vs 64.3% predicted. | C8 |
| F48 | **Longshot Outperformance** — Bets priced below 15¢ deliver +123.3% ROI due to market under-valuation, contrasting with overestimation in higher probability bins. | 29 bets, 5W–24L (17.2% WR), Cost: $26.12, P&L: +$32.17 | Keep longshot filters active |
| F49 | **High-confidence paradox persists at 90 days** — High-confidence bets still *under*perform Medium ones. Confirms the R13 hypothesis (pre-patch confidence bumps tracked inflated edge, not outcomes) and **meets C4's deferral condition** (was "revisit at 50+ high-conf trades"; now 118). Action: audit the *base* "high" criteria (≥8 books + tight consensus), not just the bolt-on bumps R13 already neutralized. | High: 118 bets, 41.5% WR, +13.5% ROI (+$13.68). Medium: 169 bets, 53.3% WR, +45.5% ROI (+$66.22). | C4 (reactivated) |

###### C4 resolution (2026-06-24) — the audit and what we changed

Ran the audit F49 called for, on 306 settled bets (118 High / 173 Medium). Two cuts settled it:

- **Edge-matched (the decisive test).** Bucketing High vs Medium by *claimed* edge removes the "High just bets bigger edges" confound. Result — at equal edge, **High wins less**: in the 5–10% edge band High is 34.4% WR (n=32) vs Medium 62.7% (n=51); in the 10%+ band 45.2% (n=84) vs 46.8% (n=111). So the tier carries **no positive predictive signal** (the roadmap's pre-condition for acting).
- **Mechanism.** The roadmap guessed "High selects tight markets = less edge." Wrong shape: High actually *over-claims* edge (19.1% vs 15.9% avg). The real story — a tight ≥8-sharp-book consensus is an **efficient price**, so a large model edge against it is most likely model error. The worst cells are NCAAMB High (33.8% avg edge, 28.6% WR) and HIGH/NO (−29.7% ROI); High genuinely works only for NHL (70% WR, n=10).
- **What "high" actually did downstream** (audited in code, not assumed): (1) **+0.9 composite** vs Medium (`{low:3,medium:6,high:9}×0.30`) → ranked bets higher in the `--max-bets` queue and eased Gate 4; (2) **Gate 4.6** — a *restriction* (NO-favorites need `high`), not an unlock; (3) **sizing — none** (`size_order` never reads confidence). Only effect (1) is harmful, so that's the single thing changed: `high`→`medium` in the composite weight. Effects (2)/(3) left intact.

This is deliberately minimal and reversible (one value across three formulas). It does **not** redistribute the 30% confidence weight (a bigger calibration change — folded into R10/C4b) and does **not** add sport-specific carve-outs (28–54-bet samples too thin). Live automation is unaffected until the branch merges to master.

##### 2026-06-14 — Scan view surfaces in-progress phantom edges

Triggered by a user report: the no-date scan `.bat` returned no results while a web-UI scan exported 20 MLB rows (`docs/my-documents/temp/edge_radar_scan.csv`). Investigation reproduced the engine as healthy — the CLI raw scan showed clean +8–10% edges at 11:25am and **zero** by 12:10pm as the games started and dropped from the odds feed. The discrepancy was two-fold: (1) the web-UI CSV is the **raw pre-gate opportunity list** (no Cost/Qty/Gate columns) while the `.bat` runs the full execution pipeline (exclude-open → dedup → edge floor → price floor → score → sizing), so the count gap is largely by design; (2) **timing** — the CSV was generated near first pitch when in-progress games still carried stale pre-game odds.

| ID | Finding | Evidence | → Action |
|----|---------|----------|----------|
| F44 | **No started-game filter in `scan.py`** — in-progress games keep producing edges until the odds feed drops them, comparing stale pre-game fair values against live Kalshi prices. | CSV showed +50.6% on $0.04 "Washington lose", +34.8% on HOU@KC (CLI: +8–10% pre-start), sub-$0.06 rows. `grep` for started/in_progress/game-time filtering in `scan.py` returned no matches. Cosmetic side-note: "Arizona vs Cincinnati vs Cincinnati" is a `format_bet_label` title-fallback artifact (`ticker_display.py:334`), not contamination. | R27 (shipped 2026-06-15) |

##### 2026-05-13 — Third-party codebase analysis

Source: `docs/my-documents/enhancements/analysis-5_2_26.md`. Reviewer's framing matched the 04-22 read — concept and core logic strong, recommendations are minor refactoring or architecture improvements. Most items were either generic style advice or already addressed (file caching = R24b; webapp duplication = pending Q6/A2). Four concrete items adopted.

| ID | Finding | Evidence | → Action |
|----|---------|----------|----------|
| F40 | **Empirical stdev values still hand-tuned** — `SPORT_MARGIN_STDEV` / `SPORT_TOTAL_STDEV` in `edge_detector.py` are updated only when a human reads a calibration report and decides to bump them (R2 04-21, R14 04-24). The values are inherently empirical; with R16 monthly calibration cron now live, the loop should close. | Reviewer's #1. R2 and R14 both required manual `.env` + source edits after the calibration report surfaced the gap. | C8 |
| F41 | **Odds API rotation doesn't distinguish 401 from 429** — `mark_exhausted()` fires on 401 but rotation handles both 401/429 the same way. A transient 429 (per-second/per-minute rate limit) would permanently dump a healthy key. No observed 429s today, but the contract is fragile. | Reviewer's #3. `scripts/shared/odds_api.py` + `edge_detector.fetch_odds_api()` retry on both status codes; `mark_exhausted` is called inside the 401 branch but the rotation step doesn't differentiate semantics. | R23b |
| F42 | **`BOOK_WEIGHTS` hardcoded in source** — 21-book weighted-median map (Pinnacle/Circa 3×, DK/FD/MGM 0.7×) lives in `edge_detector.py`. Books occasionally re-tier (or get acquired / shut down) and the values are empirical, same character as the stdevs. | Reviewer's #1 (second half). | H7 |
| F43 | **No Kalshi RSA key rotation runbook** — `.env` and `keys/` are gitignored and never logged, but the operator has no documented procedure for rotating the keypair on Kalshi's side and swapping in locally. | Reviewer's #6. | H8 |

**Deliberately not acted on:**
- "Convert `_odds_cache` from module dict to Cache manager class" — the two-tier dict + file design (R24a + R24b) works, is tested, and the class wrapper is pure cosmetic. Skip.
- "Code duplication across `detect_edge_game/spread/total`" — generic refactor advice without specific evidence the duplication has caused bugs. Touch it when one of those functions next changes; not standalone work.
- "Use `match` statements for condition chains" — pure style preference. Skip.

##### 2026-04-24 — 30-day rolling review (160 settled trades)

Full report: `reports/Performance/betting_analysis_2026-04-24_30d.md`. Window 2026-03-25 → 2026-04-24.

Sample: 160 trades, 80W-80L (50.0%), +37.4% ROI ($43.48 P&L), Brier 0.2657. Aggregate healthy but concentration risk: without the single MLS 7¢ fill (04-20, +$14.80) P&L drops to ~$29 (~+25% ROI).

| ID | Finding | Evidence | → Action |
|----|---------|----------|----------|
| F14 | **Confidence tier inverted** — High WR < Medium WR | High: 47.4% WR (n=57). Medium: 53.0% WR (n=100). High ROI (+61%) wins via bet-size, not pick quality. | R13 |
| F15 | **NBA still negative across 3 consecutive review windows** | 30d: -14.8% (n=17). 14d: -26%. Post-baseline: -15%. R2 stdev bump (04-21) too recent to attribute. | R14 (gated on R12) |
| F16 | **Edge-bucket inversion softening** — suggestive R2 is working | ≥25% edge bucket: 14d -24% → 30d **+16%** ROI. Claimed edge and realized ROI no longer monotonically inverted. Needs formal R12 attribution. | R12 |
| F17 | **Calibration overconfidence persists across all favorite bands** | 50-60%: -14.7pp gap (n=46) · 60-70%: -14.2pp (n=62, largest) · 70-80%: -15.0pp · 80-90%: -13.3pp · 90-100%: -21.5pp. Systematic ~15pp overstatement on every non-longshot bucket. | R12 (measurement), R2 (already shipped — attribution pending) |
| F18 | **NO-side still losing on wider sample** — pre- and post-R1 mixed | YES: +77.7% ROI (n=102, 52.9% WR). NO: -10.4% (n=58, 44.8% WR). Most losing NO bets pre-date R1 ship (04-21); re-measure post-R1-only cohort via R12. | — (R1 watch) |
| F19 | **R7 floor ($0.10) appears effective** — only 5 sub-10¢ bets in window, all 03-26 to 04-12 (pre-R7) | Post-R7 longshots cap at 10¢. 5-10¢ bucket ROI (+248%) is carried by one pre-R7 MLS 7¢ fill. | — (R7 watch) |
| F20 | **Low confidence (3 bets, 0-3, -105% ROI)** confirms R3 gate value | Small sample but consistent with 04-18 and 04-21 windows. `MIN_CONFIDENCE=medium` doing its job. | — (R3 confirmation) |
| F21 | **`model_calibration.py` blind to real sample** — reads wrong source | `trade_log`: 16 entries / 3 closed. `kalshi_settlements.json`: 173 entries. Calibration CLI errors out with "need at least 10" despite 160 settled bets existing. Makes R12 impossible to run on the post-baseline cohort until source is fixed. Discovered while attempting `/edge-radar-analysis` follow-up today. | R15 (shipped) |
| F22 | **Live `.env` was missing both `MIN_EDGE_THRESHOLD_NBA` and `MIN_EDGE_THRESHOLD_NCAAB`** — silent fallback to global 3% floor | Only `.env.example` had them. For the entire post-baseline window, NBA and NCAAB ran at the 3% global floor, not 8% / 10%. R2 attribution needs a caveat: the stdev bump's effect was measured against a weaker edge gate than the docs implied. Does not invalidate R2 but means R12 re-run after R14 is now a true test of both changes compounding. | R14 (shipped — both thresholds added to live `.env`) |

##### 2026-04-24 — Scanner parity audit (futures / prediction / polymarket)

Triggered by "`python scripts/kalshi/futures_edge.py scan --exclude-open` only found one edge — and `--budget 5%` isn't available". Audit compared all four scanner CLIs + execution paths.

| ID | Finding | Evidence | → Action |
|----|---------|----------|----------|
| F23 | **Futures scan shows opportunities the executor will reject** | Without `--exclude-open`, futures scan at 3% edge surfaces 45 opportunities (NBA 8, NHL 10, MLB 27, PGA 0). Most are NO-side on heavy favorites at +30–75% "claimed edge" — exactly what Gate 4.6 (R1) was built to filter. Futures typically report `medium` confidence (only 4-5 books in the outrights market), so the carve-out (`confidence=high` AND edge≥25%) rejects most of them. Scanner output doesn't reflect what will actually execute. | R18 (new P2) |
| F24 | ~~"Only 1 edge found" was `--exclude-open` working correctly~~ **INCORRECT — retracted 2026-04-24**. User had zero futures positions, all 20 holdings were regular sports games. `--exclude-open` was actually a no-op (different event-key namespace). Real cause surfaced as F27. | see F27 |
| F27 | **`dedup_correlated_brackets()` was collapsing all futures outcomes into one** | `_event_key()` does `ticker.rsplit("-", 1)[0]`; for championship futures `KXNBA-26-LAL`, `KXNBA-26-BOS`, `KXNBA-26-OKC` all produce the same event key `KXNBA-26`. With `category="futures"` identical for all, dedup saw 16+ teams as one "bracket" and kept only the highest-composite-score row. 20 futures opps → 2 after dedup, then risk gates trimmed to 1. Design was correct for alt-line brackets on the same game (Over 221.5 / 224.5 / 228.5 are genuinely correlated) but wrong for futures where each team outcome is a distinct independent bet. Concentration is already bounded by Gate 6 (`MAX_PER_EVENT=2`). | R21 (shipped) |
| F28 | **`FUTURES_MAP` prefix-collision + semantic-mismatch double bug** | Two separate issues compounding: (1) **Prefix collision** — iteration broke on first `ticker.startswith(prefix)` match, so `KXMLBPLAYOFFS-26-LAD` matched the `KXMLB` entry first (because `KXMLB` came earlier in the dict). Same pattern silently affected `KXNBAEAST`/`KXNBAWEST`/`KXNHLEAST`/`KXNHLWEST` → all got labeled "Finals/Cup Champion." (2) **Semantic mismatch** — even with prefix ordering fixed, those 5 derivative entries pointed to championship-winner Odds API markets while representing playoff-qualification or conference-winner questions. LAD's probability to MAKE PLAYOFFS (~95%) is fundamentally different from LAD's probability to WIN THE WORLD SERIES (~28%) — pricing Kalshi playoff-qualifier YES against championship-winner odds produced systematic "+60-75% edge on NO" garbage. Live impact: user saw 20 futures scan rows, 19 of which were bogus. Observed in the 2026-04-24 session while debugging futures output. | R22 (shipped) |
| F29 | **`futures_edge.fetch_outrights` only retried 3 keys**, silently returning `[]` when more than 3 keys in a row were exhausted | User has 10 Odds API keys configured; live probe showed keys 0-4 exhausted (all 500/500 used), key 5 with 174 remaining, keys 6/7/9 fresh at 500, key 8 invalid (401). Because `fetch_outrights` used `for attempt in range(3)`, the retry loop exited after keys 0, 1, 2 all 401'd and never reached the healthy key at index 5. The parallel function in `edge_detector.py` had already been fixed to use a `tried: set[str]` loop that cycles through every key, but `futures_edge.py` was missed. Scanner printed "No outright data" but the real cause was swallowed HTTP errors. | R23 (shipped) |
| F30 | **`_remaining` quota map was process-local — every fresh invocation rediscovered exhaustion** | Without persistence, every new Python process burned 3+ HTTP retries hitting dead keys before finding a healthy one. For a nightly task scheduler job running 5-10 scan.py invocations, that's 15-30 wasted 401 requests per run. Combined with F29 it meant filtered single-sport scans (which don't get the all-sports "warmup" rotation) could 401 out entirely. | R23 (shipped) |
| F31 | **Quota burn rate is unexpectedly high** | Key 0 went from 175 remaining (observed in a scan at 13:32) to 0 remaining (observed 5 minutes later at ~13:37). That's ~175 requests consumed in a very short window. | R24a (shipped — webapp cache), R24b (shipped 2026-04-28 — file-backed odds cache) |
| F32 | **Webapp had no `@st.cache_data` anywhere** | `grep -rn "@st.cache" webapp/` returned 0 hits. Every click-to-scan fired a fresh Odds API fetch. A 1-minute exploratory poking session on the dashboard could burn 50-100 requests re-running the same scan with minor filter tweaks. Found while investigating F31. Unlikely to explain the full 175-in-5-min burn on its own but a meaningful contributor. | R24a (shipped) |
| F33 | **13 scheduled tasks installed, only 5 managed by `install_windows_task.py`** | `Get-ScheduledTask -TaskPath "\Edge-Radar\*"` shows 13 tasks. The installer's `status` command only knows about the 5 profiles defined in `TASK_PROFILES`. The other 8 (`All-Sports-SameDay-Execution`, `All-Sports-NoDateFilter-Execution`, `NextDay-Execute`, `Backtest`, `Calibration`, `Reconcile`, `Email-NextDay`, `Email-NoDateFilter`, `Email-SameDay`, `Email-Weekly-Analysis`) were created manually via `schtasks`. Not broken — just invisible to the installer's management UX. | R24c (new P3) |
| F35 | **Scan tables silently hid which rows the executor would reject** | User ran `scan --filter mlb-futures --unit-size .5` and got "No opportunities passed risk checks" (LAD rejected on composite score 4.6 < 6.0). Same command without `--unit-size` happily showed LAD as a +4.3% edge row with no indication it would fail the executor. Scan table promised an opportunity the system would never take. Directly motivated shipping R18 as the fix. | R18 (shipped) |

##### 2026-04-24 — Prediction-market audit (R20)

First full evaluation of `prediction_scanner.py` since it shipped ~2 weeks ago. Audit covered the 6 edge-detection modules (crypto / weather / spx / mentions / companies / politics) plus live scan output and historical settlements. Verdict: all 6 modules should be parked until properly rebuilt.

| ID | Finding | Evidence | → Action |
|----|---------|----------|----------|
| F34 | **All 6 prediction-market modules cache live data with zero TTL** | Module-scoped `_price_cache` / `_history_cache` / `_forecast_cache` / `_historical_cache` dicts never invalidate. Weather forecast cached at first scan, reused all day. Crypto 7-day history cached from module load, never refreshed — multi-day scanning uses day-1 data on day 5. SPX price cached for hours. FRED bankruptcy data persisted for the full process lifetime. Silent staleness — no log, no warning. | R25b (new P3) |
| F36 | **Live prediction scans produce obvious garbage fair values** | Crypto BTC/ETH range bets priced at $0.04-$0.07 show fair values of $0.77-$0.91 (+70-86% "edge"). Miami weather "83-84°F" bet showed $0.42 market / **$1.00 fair** / HIGH confidence / 9.7 composite — would have executed live if user had passed `--unit-size`. Mentions markets show +45% edge NO-side on sub-10¢ tails. All patterns consistent with broken fair-value models, not mispriced markets. | R25 (shipped) blocks execution; R25c rebuilds |
| F37 | **Zero prediction-market bets in 173 historical settlements** | Every settlement is a sports game (MLB / NHL / NCAAB / NBA / MLS). Prediction scanner has been running daily for weeks but has never produced a bet that cleared the gates. Result: we have **no calibration data at all** on whether any of the 6 models work. Can't attribute anything; can't A/B. Rebuilding from scratch is cheaper than debugging a model we've never measured. | R20 (shipped as audit), R25c |
| F38 | **4 of 6 prediction modules have no unit tests** | Only `test_weather.py` exists, and it actually tests `sports_weather.weather_scoring_adjustment()` — not `weather_edge.detect_edge_weather()`. No tests for crypto, spx, mentions, companies, or politics. No way to catch a regression if someone touched the files. | R25c |
| F39 | **`DEMO_KEY` hardcoded as FRED API key in `companies_edge.py`** | Line 54: `api_key = os.getenv("FRED_API_KEY", "DEMO_KEY")`. `DEMO_KEY` is FRED's public demo credential with low rate limits shared across all users. If the shared rate limit hits, companies_edge silently falls back to a hardcoded 2020-2025 bankruptcy baseline. Low-severity (this module has never placed a bet) but sloppy. | R25c |
| F25 | **Scanner flag parity gap** | `--budget` and `--report-dir` were sports-only. Futures / prediction / polymarket CLIs didn't accept them, and even if they had, `execute_pipeline(budget=…)` wasn't threaded through. Risk-gate logic itself was uniform (all four scanners share `execute_pipeline`). | R17 (shipped) |
| F26 | **Odds API outright coverage is seasonal/partial** | NBA/NHL/MLB/PGA had live outrights at audit time; NFL Super Bowl was empty (off-season), NCAAB MOP empty (post-tournament). Golf majors (Masters, US Open, The Open) not configured as separate series. UCL/EPL/European soccer leagues not on free tier. Expected — documenting so we don't re-investigate. | R19 (new P3) |

**Watch list (do not act on yet):**
- MLS: still a single-fill artifact (6 bets, one +$14.80 win carries it). Do not re-weight.
- Spread +145% ROI — same caveat as MLS; 23-bet sample includes the MLS fill.

##### 2026-04-22 — Independent repository analysis (integration truth, packaging, CI)

Full report: `docs/my-documents/repo-analysis/edge_radar_repository_analysis_2026-04-22.md`.

Framing: reviewer assessed concept quality as strong and core logic as moderate-to-strong, but flagged that **documentation quality is running ahead of integration quality**. The P&L/calibration side of the repo is healthy; the product-truth, packaging, and CI sides have visible drift. None of the findings are strategic — all are hardening work.

| ID | Finding | Evidence | → Action |
|----|---------|----------|----------|
| G1 | UI exposes 4 market types; service layer supports 1 | `webapp/views/scan_page.py:19` lists sports/futures/prediction/polymarket; `webapp/services.py` only imports & calls `scan_all_markets` (sports path) | Q1 |
| G2 | One test fails in clean venv run | `tests/test_risk_gates.py:141 test_approved_clean_when_no_caps_hit` — expects `APPROVED`, analysis claims `APPROVED_CAPPED_MAX_BET` | Q2 |
| G3 | "8 risk gates" doc claim obsolete | 3 docs still say 8 gates; live system has 11 since R1/R3 shipped 04-21 | Q3 |
| G4 | Pages deploy workflow targets wrong branch | `.github/workflows/deploy.yml:5` → `main`; repo default is `master` | Q4 |
| G5 | Undeclared runtime dep on pandas | `webapp/views/scan_page.py:5` imports pandas; `requirements.txt:21` still marks it "planned" | Q5 |
| G6 | Package boundary vs real logic location mismatch | `pyproject.toml:13` includes only `app*`/`webapp*`; `scripts/` is the real codebase, pulled in via `sys.path` mutation | Q6 |
| G7 | No automated CI guardrail | Only deploy workflow exists; no pytest/lint/import-smoke job | T3 (impact raised) |

**Deliberately not acted on:**
- "Clone-configure-run outsider experience" / PowerShell bootstrap / no-credentials demo mode — reviewer framed these as major gaps; for a solo-operator tool they're nice-to-haves. Not added to roadmap unless the tool's audience changes.
- "Reduce import-path magic gradually" as a standalone item — folded into Q6.
- "Reproducible calibration artifacts" — partially addressed by existing calibration reports in `reports/Calibration/`; revisit only if R12 (100-trade re-run) surfaces a specific artifact gap.

##### 2026-04-21 — 14-day post-C1/C3/C5 review

Sample: 76 settled trades (2026-04-07 → 2026-04-21). 37W-39L (48.7%), +31% ROI ($19.55 P&L), Brier 0.2646. Aggregate looks good but is carried by NHL and one outlier.

| ID | Finding | Evidence | → Action |
|----|---------|----------|----------|
| F1 | NO-side systematically loses on high edge | YES +93% ROI (n=48). NO -20% ROI (n=28). NO at ≥20% edge: 31% WR, -33% ROI (n=16). **All 13 high-edge losers are NO-side.** | R1 |
| F2 | Brier 0.2646 — probability estimates still adding noise | C1 dampens sizing on fake-high edges but doesn't touch the probabilities. | R2 |
| F3 | Edge-bucket inversion intact post-C1 | 5-10%: +140% · 10-15%: +111% · 15-20%: +1% · 20-25%: +3% · **25%+: -24%** (n=11). | R2, R10 |
| F4 | Overconfident in favorite band | 50-60%: +14% gap · 60-70%: +18% gap (n=40, largest bucket) · 70-80%: +14% gap. | R2 |
| F5 | NBA -26% / MLB -10% persist | C3 floor applied to new bets only; history keeps settling. | R2 |
| F6 | "Low" confidence 0W-3L, -105% ROI | Consistent across 2026-04-18 and 2026-04-21 windows. | R3 |
| F7 | 16% of recent orders orphaned resting | 4/25 resting 25-66h, 1 partial (2/5). No follow-up. | R4 |
| F8 | Trade log ↔ settlement disconnect | Only 10/76 14-day settlements match a trade log entry; 158 historical settlements unmatched. | R5, R11 |
| F10 | Extreme-price bets (<10¢) are lottery tickets | 4 bets: 1W-3L. One win masks systemic pattern of model claiming "+50% edge" on 8-10¢ longshots. | R7 |
| F11 | Within-day same-matchup dedup gap | 12 matchups bet ≥2× in 14d; several same-day on different categories. | R8 |
| F12 | 48h series-dedup window too tight | MLB_NYMLAD bet Apr 14 + Apr 16 (~49h), both landed, both lost. | R9 |
| F13 | Spread +200% ROI is an outlier | n=7 driven by one 7¢ MLS fill. Remove it: -$1.71 over 6 bets. Don't re-weight on this window. | — (watch) |

**Watch list (do not act on yet):**
- MLS +169% ROI (n=6) — single-fill artifact.
- NHL +87% ROI (n=40) — consistent; **do not stdev-bump NHL**.

##### 2026-04-18 — First post-baseline calibration (66 trades since 04-03 baseline)

Full report: `reports/Calibration/2026-04-18_calibration_report.md`.

- **Brier 0.2561** — worse than coin-flip. Probability estimates add noise.
- **Calibration curve:** 60-70% predicted → 50% realized (n=34, +15% gap); 70-80% → 58% (n=12, +14% gap). Favorites band systematically overstated.
- **Edge bucket inverted:** 10-15% edges → +127% ROI; ≥25% → -35% ROI (n=10).
- **Confidence:** High n=21 (-$0.81, avg claimed edge 22.4%), Low n=3 (0W, -$4.91), Medium n=46 (+$18.39, avg claimed edge 14.3%). Medium is carrying the model.
- **Category:** Totals +33%, ML -8%, Spread -25% ROI.
- **Sport (edge-metadata only):** NHL +100% (n=35), NBA -15%, MLB -20%, MLS -54%.
- **Series-correlation leak** observed: same matchup bet across consecutive nights — motivated C5.

##### C1 details — what shipped 2026-04-18

`trusted_edge()` in `scripts/kalshi/kalshi_executor.py` soft-caps edge inside the Kelly sizing expression only. Raw edge still flows through the edge-threshold gate, composite score, trade rationale, reports, and trade journal.

```
trusted_edge(edge) = edge                            if edge ≤ cap
                   = cap + (edge - cap) × decay      if edge > cap
```

Defaults `KELLY_EDGE_CAP=0.15`, `KELLY_EDGE_DECAY=0.5`:

| Raw edge | Trusted edge | Kelly reduction |
|---|---|---|
| ≤15% | unchanged | 0% |
| 20% | 17.5% | 12.5% |
| 25% | 20.0% | 20.0% |
| 30% | 22.5% | 25.0% |
| 35% | 25.0% | 28.6% |
| 50% | 32.5% | 35.0% |

Re-measure at 4 weeks. If ≥25% bucket is still negative, tighten to a harder cap (decay=0) or add a composite-score penalty.

---

#### Completed

Index only — detailed notes are in the collapsed section below.

##### 2026-09-07 — College football never scanned (wrong ticker) + account graph made private

Opened by the operator noticing zero college-football bets in the trade log and asking why.

| ID | Item |
|----|------|
| — | **College football has been unscannable since launch.** `FILTER_SHORTCUTS["ncaafb"]` and `KALSHI_TO_ODDS_SPORT` both pointed at `KXNCAAFBGAME`, which doesn't exist — Kalshi's real series is `KXNCAAFGAME` (no gender-split `B` the way basketball needs one). `KXNCAAF` (no `GAME` suffix) *does* exist but is the CFP championship futures market, which made the bug look superficially fine on a casual check. The no-filter scheduled scans walk the same broken dict, so this silently starved every automated run too — not a gate rejection, a fee, or an edge-threshold issue. Fixed both maps, and added `KXNCAAFSPREAD`/`KXNCAAFTOTAL`, which had never been wired at all (moneyline-only). Verified live (dry preview, no orders placed): 3,999 open markets found (was 0), 15 opportunities clear the 3% edge floor. 1032 tests pass. |
| — | **Account-growth graph made private**, reversing 2026-05-31. It carries real dollar figures (balance, deposits, settled P&L, open-position value) and was being copied into `.claude/html/` and pushed to `master` to serve on the public GitHub Pages site — flagged by the operator after noticing the file modified in `git status`. `refresh_account_graph.py` no longer publishes anywhere; output stays under the already-gitignored `docs/my-documents/account-graph/latest/`. **Not yet resolved:** the file's git history on the public repo still contains every past weekly snapshot with real dollar figures; scrubbing it needs an explicit `git filter-repo` + force-push decision, deliberately not done in this pass. |

##### 2026-08-27 — Exchange sharding fallout (X1) + a test suite writing live state (S3a)

Opened by a routine check-in on scheduled runs; the eligibility probe that was meant to confirm a clean bill of health failed for an entirely new reason.

| ID | Item |
|----|------|
| ~~S3a~~ | **`make test` was overwriting the live `venue_eligibility.json`.** `_place_order_batch` calls `record_success()` on any `create_order` response whose status is not `dry_run_blocked` — which a **mocked** client never returns — and `ELIGIBILITY_PATH` is a module-level constant. Three executor tests stamped `kalshi:sports = ok` citing pytest fixture ticker `KXNBAGAME-26APR04T3-A`, **clobbering the genuine 08-26 hand-probe evidence under the same key**. The verdict stayed `ok`, so nothing looked wrong. Fixed with an autouse fixture in `conftest.py` beside `_isolate_data_logs`, which had already learned this lesson for the trade log. The `probe accepted (...)` vs `order accepted (...)` wording is the tell when auditing any future `ok`. |
| — | **MLB moved to exchange shard 3 ("Tennis & Baseball") on 2026-08-24** and cash does not follow. Reads work; a bogus ticker returns generic `not_found` while a real open MLB ticker returns `user_not_found` — market resolves, per-shard user lookup does not. `/exchange/status` names the shards; `balance_breakdown` showed $88.07 on shard 0 and $0 on shard 3. **Not a block** — the Nevada geo-restriction had genuinely been cleared. |
| — | **`intra_exchange_transfer()` + `get_intra_exchange_transfers()`** added to `kalshi_client`. The wire format cost three live 400s: `amount` is int64 **centicents** (10000 = $1.00), not the fixed-point string every other v2 money field uses; the shard fields are `source_exchange_shard`/`destination_exchange_shard`, **not** `..._exchange_index`, and both default to 0 so omitting them is a silent no-op; `source`/`destination` are a separate axis naming the instance (`event_contract` \| `margined`). $15.00 moved, transfer `2e67a7ef`. |
| — | **`cancel_order()` is shard-scoped and failed as a bare 404.** The verification order could not be cancelled without `?exchange_index=3`, and `404 not_found` is indistinguishable from "already gone" — precisely how the **R4 janitor** treats it. It would have reported clean sweeps while every MLB order kept resting, and `doctor.py --verify-eligibility` would have abandoned its probe order live on the book. Both callers now forward the shard the order reports. |
| ~~X1~~ | **Just-in-time cash movement between shards.** Sizing stays whole-account (operator's call — the alternative would let a $15 shard balance silently cap bets the bankroll supports). `shard_funding.ensure_shard_funded()` moves **exactly the shortfall** before each order, capped by `MAX_AUTO_SHARD_TRANSFER`; the transfer is non-atomic so the destination balance is re-read and the order skipped if still short. Fails **open** on an unknown shard, **closed** on a transfer that did not settle. Off ⇒ the order is skipped and logged `shard_underfunded` rather than placed to fail. `doctor.py` prints the per-shard split — the sum alone is what hid this. **987 tests.** |
| — | **Still open:** S3's eligibility cache is keyed venue + product, so `kalshi:sports = ok` is simultaneously right for MLS and wrong for an unfunded MLB shard. X1 makes it mostly moot (the order is skipped before it can 404) but the key is still imprecise. |

##### 2026-07-31 — MLB Totals Investigation + C8 Calibration Loop Repair

Opened by an operator observation ("a ton of under-13.5 baseball runs bets"), which turned out to be the visible symptom of a self-correction loop that had never worked.

| ID | Item |
|----|------|
| T1 | **MLB high-strike totals were 69% of the book since coverage landed 07-20**, 18W-10L against an 80% break-even (−12.6% ROI), with the model claiming 89.7% — p=0.0003 against its own claim. Cause was not distance from the consensus line but a stale stdev. Resolved by repairing C8 (below); 21 of 25 such bets now fall under the R28 8% NO floor. |
| ~~T2~~ | **Strike-boundary hypothesis measured and rejected** — no bug. `floor_strike` is 12.5 (the ticker suffix is a market index, not the strike), `strike_type` is uniformly `greater`, `extract_strike()` reads `floor_strike`, and half-integer strikes make `≥` vs `>` moot. Recorded because the negative result eliminated the cheap explanation. |
| ~~T3~~ | **The C8 stdev loop had never calibrated anything.** Cadence was already weekly (my original framing was wrong and is corrected in place). The real defect: the weekly task ran `--days 7`, and `save_calibration_stdevs()` needs 20 settled rows *per (sport, category)* from that day-filtered list — only ~22 bets settle in 7 days across **all** sports. Every run skipped every sport and wrote the hardcoded defaults back, which is why the cache was byte-identical to `SPORT_*_STDEV` for its entire life. Widened to `--days 30`: `total_stdev.baseball_mlb` **3.45 → 4.005** on the first real run. |
| — | **Distance-cap fix measured and rejected.** Over 136 settled totals bets the 1.0–1.5σ band — where the MLB bets sit — was the *only* profitable bucket (+5.8%); a 1σ cap would have deleted it and kept the −29.5% band. New re-runnable tool `scripts/backtest/totals_distance_check.py`. The over-claim is uniform at every distance (+12% overall), which is a calibration signal, not a distance one. |
| — | **Pre-wager calibration preflight** (`REQUIRE_FRESH_CALIBRATION`, default false = warn). `execute_pipeline` compares the cache against what the calibrator would compute from current settled data. Deliberately **not** an age check — every age-based safeguard reported "fresh" throughout the no-op. A legitimate skip or hold recomputes to the same value and stays silent. Caught a false positive in itself before shipping (auditing all-time while the job runs 30 days flagged out-of-season NCAAB forever). |
| — | **Scheduler cleanup.** Removed `MonthlyCalibration` — a duplicate that had **never once run** (Last Run `11/30/1999`). Fixed `install_windows_task.py`, which hardcoded an `Edge-Radar\` folder while live tasks sit in `Edge-Radar-MikesAILab\`: it would have silently created parallel duplicates (a second settler, or a second *execute* task placing real bets) or, pointed the other way, clobbered a live task's run-as/wake/retry policy. Now refuses on cross-folder name collision, with `--task-folder` and `--force`. |
| — | +11 tests (688) across `test_calibration_config.py`: the `--days` window guard, `CURRENT_*_STDEV` drift from `edge_detector`, loop statelessness, and the preflight. Verified the scheduled task end to end — `.bat` from a foreign cwd, `schtasks /Run` → `Last Result 0`, cache rewritten, report produced, live pricing reading 4.005. |

##### 2026-07-31 — Dashboard Venue Support + Config Page + C10b Games Composite

| ID | Item |
|----|------|
| PM2d | **Polymarket is a dashboard venue.** Fourth market type that also switches the execution client, routing through the CLI's own `_route_filter` so the two can't disagree. Two-flag dry-run status resolved live (an armed account can't show a "DRY RUN" dialog); Gamma game rows marked `Exec = —` and dropped before `execute_pipeline`; per-venue Portfolio tabs with a shared daily-loss bar. A separate position formatter fixes $0.00 unrealized on every PM row (Amount objects + cost-basis-not-market-value) and reconciles to the Portfolio Value tile. Supersedes the Q1 removal, which deleted a UI-only stub. |
| A10 | **Cloud secrets registry — silent env-var drop.** The hand-maintained `_flat_keys` list had drifted ~20 knobs behind `app/config.py`; on Streamlit Cloud those were set in Secrets and never read, with no error. Replaced with `ENV_VAR_SPEC` + a drift test that parses `app/config.py`. Surfaced nine more undocumented vars, closing the 2026-07-14 review's `.env.example` gap. |
| A11 | **Config page.** Execution mode per venue + every variable with live value, source (`set`/`default`/`unset`), group, and rationale. Secrets shown as a length only. Exports a blanked `.env` template. |
| C10b | **Games composite had C10's unreachable Gate 4.** `polymarket_games_edge.py` predates C10 by 3 days and copied `edge * 20` from the futures file — itself a copy of its own `liquidity` line. Across **362 logged game rows none ever reached composite 6.0** (max 5.30) against a 6.0 gate. Aligned to `min(edge / 0.01, 10)`; only 5 of 362 (1.4%) newly clear Gate 4, and 330 never reach it. No live behavior change (Gamma rows aren't executable); de-risks the US games repoint. Liquidity `* 100` and `high: 9` kept deliberately, both documented. |
| — | Also: **Gate** column added to scan results (the help text had promised it since April with no such column), **Exec** column on PM scans, min-edge help text resynced to live gate values, **Budget %** no longer sports-only (the schedulers pass `--budget` on futures/PM runs, so hiding it made a dashboard futures run the one path with no batch cap). Found **C10c** — the same `edge * 20` in all 7 prediction scanners, logged to Priority 2 rather than fixed. 677 tests. |

##### 2026-07-27 — C11 Kelly Price-Complement Fix + C11b Floor-Aware Budget Cap

| ID | Item |
|----|------|
| C11 | **Kelly was missing the `(1 - price)` divisor.** Favorites under-sized by `1/(1-p)` — 5.9x at 83c — collapsing nearly every 60c+ bet to 1 contract, in the one price band that beats break-even by more than noise (+11.1pts, 44/52, p=0.044). Paired `.env`: `KELLY_FRACTION` 1→0.5, `UNIT_SIZE` .50→1.00, `MAX_BET_SIZE` 15→8. 659 tests. |
| C11b | **Correlation guard measured and dropped.** Pooled rho +0.181 was Simpson's paradox; stratified rho +0.048 overall and **-0.187 (p=0.75) for totals**. No guard built — added `scripts/backtest/correlation_check.py` instead. Fixed the real regression it surfaced: the fixed budget pool let corrected favorites squeeze the longshot lane (18c leg 6→2 contracts), so `_apply_budget_cap` is now floor-aware + bisecting, dropping whole orders only when floors cannot fit. Scheduler `.bat` files were overriding `.env` `UNIT_SIZE` via `--unit-size .5`; all 16 updated. 667 tests. |

##### 2026-07-20 — MLB Spread/Total Coverage Gap Closed (health-check finding)

| ID | Item |
|----|------|
| — | **`KXMLBSPREAD` + `KXMLBTOTAL` wired into the scanner.** Health-check ("not much coming through") found the two series live on Kalshi with open markets but absent from `FILTER_SHORTCUTS`/`CATEGORY_MAP`/`KALSHI_TO_ODDS_SPORT` — MLB scanned **moneyline-only all season** (the series launched after MLB was wired in March; every other major sport had all three types). The R2-calibrated baseball stdevs (margin 4.025 / total 3.45) were already in place, so the fix is three map entries; all detection/dedup/display machinery is prefix-generic. Live shapes verified (bracket-style, line in `floor_strike`). First scan: MLB 106→407 markets (103 spreads, 176 totals); 7 gate-`ok` rows at +8–12% claimed edge — **all deep-bracket Unders (high-line NO-side favorites), an uncalibrated sub-population**: normal-CDF tails vs right-skewed MLB run distributions may overstate Under fair values (Coors Under 17.5 among them). Gates governing it: R28 NO-floor 8%, bracket dedup, per-event cap 2, $1 units. Posture: let the automation bet small and watch the first settlements — same play as the 06-29 soccer-spread lean, which proved real. +5 tests (640). |

##### 2026-07-14 — Repo Review + Money-Path Fixes + Longshot Floor + Config Reconcile

| ID | Item |
|----|------|
| — | **Fixed 3 real-money bugs.** (1) Calibration-on-read: `model_calibration.py` called `save_calibration_stdevs()` unconditionally, so a read-only report mutated the scanner's pricing stdevs — now gated behind `--save`. (2) Non-atomic trade log: `trade_log.py` now writes via temp-file + `os.replace` (`_atomic_write_json`) so a crash can't corrupt the ledger / lose a live position. (3) R26 replay gate bypass: `kalshi_executor.py` cached-preview replay now re-checks gates 5/6/7 (duplicate ticker / per-event cap / series dedup) against current portfolio before executing. 508 tests green. |
| R7↑ | **Longshot floor raised.** `MIN_MARKET_PRICE` 0.06→0.12 (live `.env` + `.env.example` + `app/config.py` + `CLAUDE.md`). 30-day settled: every sub-15¢ bet lost (0W–21L / −100%); ≥25¢ profitable. Directly kills the World Cup spread-YES longshot bleed. Needs webapp restart / Cloud Secrets update to apply in long-running apps. |
| — | **Config reconciled to `app/config.py`.** `MAX_OPEN_POSITIONS`=50 everywhere (live intent; docs said 10), `MAX_PER_EVENT`=2 in CLAUDE.md (was 3). |
| — | **Cruft purged.** Removed orphaned/broken `daily_sports_scan.py`, `fetch_market_data.py`, `fetch_odds.py` + 16 dated email snapshots; updated SCRIPTS_REFERENCE.md. Kept `.claude/backup/` (intentional, documented). Full review: `docs/my-documents/repo-reviews/2026-07-14-repo-review.md`. |

##### 2026-06-24 — C4 Confidence-Tier Audit (Retire High's Composite Premium)

| ID | Item |
|----|------|
| C4 | **Base "high" tier no longer earns a composite-score premium.** Audited the tier's predictive value on 306 settled bets. Found High at 41.5% WR / +13.5% ROI vs Medium 53.2% / +44.4%, and — controlling for claimed edge — High underperforms Medium at *equal* edge (5–10% band: 34% vs 63% WR), i.e. **no positive signal**. Mechanism: a tight ≥8-sharp-book consensus is an efficient price, so a large model edge against it is more likely model error than alpha (High *over-claims* edge, 19.1% vs 15.9% avg). Fix: capped `high`→`medium` in the three sports composite formulas (`edge_detector.py`) so "high" can no longer float no-signal bets up the `--max-bets` queue or help clear Gate 4 (`MIN_COMPOSITE_SCORE`). The `high` label is retained as a Gate-4.6 restriction on NO-favorites; Kelly sizing never used confidence (nothing to unwind). Scoped to sports — futures/prediction "high" earned by different rules, out of scope. No env var. Follow-up **C4b** (edge-cap the minting rule) logged in Priority 2. |

##### 2026-06-23 — L1 (Phase 2) + R28 + R29 + C8 Shipped

| ID | Item |
|----|------|
| R28 | **NO-Side Sizing & Edge Override.** Implemented an elevated minimum edge floor (8%) and configurable Kelly multiplier override (default 1.0) globally for NO bets to damp contract sizing and address the NO-side contract P&L drag (-7% ROI). |
| R29 | **NBA Model & Consensus Calibration.** Raise minimum consensus book limit to 8 (`MIN_CONSENSUS_BOOKS_NBA=8`) for NBA games, dropping the confidence tier to `low` if fewer than 8 books agree, avoiding stale recreational lines. |
| C8 | **Auto-recalibrate sport stdevs.** Closed the calibration feedback loop by automating the calculation of updated CDF standard deviations from settled trade outcomes, caching recommendations to `data/cache/calibration_stdevs.json` which is read at runtime. |
| L1 (Phase 2) | **Live in-play odds — targeted live fetch + stale bookmaker suppression.** Designed and implemented Phase 2 of L1. Implemented `fetch_event_odds_api` in `edge_detector.py` to query `GET /v4/sports/{sport}/events/{eventId}/odds` when a matched game is in progress, bypassing sport-level caching. Implemented cross-process and in-process single-event caching via `odds_cache.load_event`/`store_event`. Added a bookmaker freshness check `_is_bookmaker_stale` using the new `MAX_LIVE_BOOK_AGE_SECONDS` threshold (default 1200s/20m) to exclude stale/suspended bookmaker lines from consensus calculations for live games. Added unit and integration tests. **Freshness hardening (2026-06-23 review):** `_is_bookmaker_stale` now fails *closed* on a missing/unparseable `last_update` for a live game (was treated as fresh — a suspended feed could poison consensus); a `MIN_LIVE_CONSENSUS_BOOKS` floor (default 3) skips a live game whose consensus the stale filter thinned below that many fresh books (fires only when staleness removed books — pre-game unaffected); and `_refresh_event_if_live` logs when a failed per-event refresh falls back to the stale sport-level snapshot instead of degrading silently. |

##### 2026-06-20 — L1 Phase 1 + World Cup + Kalshi v2 Orders + R19(b) PGA

| ID | Item |
|----|------|
| L1 (Phase 1) | **Live in-play odds — freshness fix + live-bet gate.** F44's phantom live edges were a caching bug, not missing data: the in-process `_odds_cache` in `fetch_odds_api` had **no TTL** and returned the first response for the whole process lifetime, so in the long-running webapp pre-game odds stayed frozen for hours while Kalshi's price moved mid-game. Odds API `/odds` already returns in-play odds (`commence_time ≤ now`). **Fix:** `_odds_cache` now stores `(stored_at_monotonic, events)` and expires; new `odds_cache.response_has_live_event()` / `effective_ttl()` apply a short **live TTL** (`ODDS_LIVE_TTL_SECONDS`, default 45s) to *both* cache layers when a response contains an in-play event, else the 300s pre-game TTL. `odds_cache.load()` gained an optional `live_ttl_seconds` arg (backward compatible — `futures_edge` keeps the 3-arg call; outrights have no in-play concept). Within-scan dedup preserved. **Gate 4.8 `ALLOW_LIVE_BETS` (default off):** the freshness fix makes live edges *honest* → executable through scheduled scans, so `size_order()` rejects `is_game_started(ticker)` bets unless enabled; `preflight_gate_status()` surfaces `live-off`. Caveat: detection only fires on moneyline tickers that embed a start time — date-only spread/total tickers slip through. **Phase 2** (per-event `/events/{id}/odds` refresh + the deferred Q3 stale per-book `last_update` guard) and **Phase 3** (real-time polling) still scoped. The new gate exposed latent test fragility — 3 `test_risk_gates.py` fixtures used hardcoded *past* dates and were bumped to a far-future year. +15 tests → **463 passing**. Files: `scripts/shared/odds_cache.py`, `scripts/kalshi/edge_detector.py`, `app/config.py`, `scripts/kalshi/kalshi_executor.py`, `tests/test_odds_cache.py`, `tests/test_edge_detection.py`, `tests/test_risk_gates.py`, `.env.example`, `CLAUDE.md`, `docs/enhancements/live-in-play-odds-design.md`. |
| — | **FIFA World Cup sport coverage.** `KXWCGAME` / `KXWCSPREAD` / `KXWCTOTAL` → `soccer_fifa_world_cup`; new `worldcup` / `wc` filter shortcuts, folded into the `soccer` group; reuses the existing 3-way soccer edge logic (zero edge-math changes) and auto-joins daily no-filter scans. Display fix: `_resolve_team_abbr()` keeps raw country codes for `KXWC*` (COL=Colombia was rendering as "Colorado"). Diagnosis along the way: the "wagers dried up since ~June 13" report was a **seasonal trough** (NBA/NHL/NCAA/Euro-club all out of season; MLB the only active daily sport), not a calibration regression. Live: 40 opps. +6 tests. Deferred: Wimbledon tennis (~June 28, needs a new player-based sport class); skipped: NCAA baseball (CWS window closing). |
| — | **Kalshi v2 order-endpoint migration.** v1 `POST /portfolio/orders` was deprecated (HTTP 410), blocking *all* live placement (a second reason betting looked dead, on top of the seasonal trough; surfaced once World Cup coverage produced executable opps — no money at risk, 410 is a clean pre-placement reject). `create_order` now posts to v2 `POST /portfolio/events/orders` (same host; single-book / YES-perspective: `bid` buys YES, `ask` sells YES). Public signature unchanged; internal pure `_build_v2_order_body()` translates buy-NO@p → `ask` price=`1−p`. New `_order_field()` reads the lean v2 create-response shape (`fill_count` / `remaining_count`, no `order` wrapper) so fills aren't misreported as "resting" (which would corrupt exposure/P&L). Validated live (2 resting 1-contract orders, both canceled, no residual exposure). +12 tests. |
| R19(b) | **PGA Tour golf majors edge detection.** `KXPGATOUR` spans the entire PGA Tour (weekly stops + majors + qualifiers) but the Odds API only carries the 4 majors, and the static map pointed at an already-finished major while live Kalshi markets were the U.S. Open. New `_golf_major_key(title)` resolves the major from the human-readable market title (not the cryptic event code), routes to the correct per-major odds key, and skips weekly stops/qualifiers (no odds → no edge, never a wrong-tournament edge). `--filter pga` routes to the futures scanner. Validated live (U.S. Open, 71 players, 3 books, 2 edges — both gated). +7 tests. Remaining R19 sub-items (team-name coverage, conference/playoff outrights, NCAAB tournament) tracked in the Priority 3 R19 row. |

##### 2026-06-15 — R27 "Started" Column on Scan Views (In-Progress Phantom-Edge Flag)

| ID | Item |
|----|------|
| R27 | **Sports scan views now flag in-progress games with a `Started`/`LIVE` column** so the operator can see when a row's edge compares *live* Kalshi pricing against *stale* pre-game odds. Motivated by F44 (2026-06-14): a web-UI scan CSV showed +50.6% on a $0.04 "Washington lose" longshot and +34.8% on HOU@KC (the post-start CLI priced the same games at +8–10%), because a started game keeps producing edges until the Odds API drops it. The root confusion was a misleading comment at `edge_detector.py:1760` — the filter there keys on `expected_expiration_time`, which is the market **close** (after the game *ends*), so it never dropped in-progress games. **Design decision (tag, not exclude):** games stay visible in the scan/CSV with a `LIVE` marker rather than being filtered out — the operator chose visibility over silent removal, and execution gates already protect *real* bets. **Implementation:** new canonical `ticker_scheduled_utc(ticker)` + `is_game_started(ticker, now=None)` in `scripts/shared/ticker_display.py`. These mirror the hardened `edge_detector._ticker_scheduled_utc` event-matching logic (ET wall-clock numerals treated as UTC then shifted by a fixed 4h ET offset — a 1h EST/EDT slip is immaterial for "has it started?"). Both are **HHMM-only**: only moneyline (GAME) tickers embed a start time, which is exactly the F44 case; spread/total and NBA/NHL tickers carry date only, so `is_game_started` returns `False` (don't guess) rather than risk false-positive flags. The edge_detector matching path was left untouched to avoid any regression risk on the recently-hardened find_market_event code. **Wired into four scan surfaces:** the CLI Rich table (`edge_detector.print_opportunities` — `[red]LIVE[/red]`), the webapp dataframe + CSV export (`services.opportunities_to_rows` + a `scan_page` column-config width hint), the saved markdown scan report (`report_writer.save_scan_report`, sports branch), and the emailed automation report (`daily_sports_scan`). No CLI flag and no change to `scan_all_markets` — tagging is a pure display concern, so both CLI and webapp inherit it for free. Also tightened the misleading expiration-filter comment. **Verification:** +13 tests in `tests/test_ticker_display.py` (`TestTickerScheduledUTC`: ET→UTC shift, midnight crossover, spread ticker, date-only→None, unparseable→None; `TestIsGameStarted`: after/at/before start, date-only never-started, unparseable→False) → **424 passing** (was 411). Live smoke confirmed past/future/date-only tickers flag correctly. Files: `scripts/shared/ticker_display.py`, `scripts/kalshi/edge_detector.py`, `webapp/services.py`, `webapp/views/scan_page.py`, `scripts/shared/report_writer.py`, `scripts/schedulers/automation/daily_sports_scan.py`, `tests/test_ticker_display.py`. |

##### 2026-06-14 — H9 Runtime Risk-Config Reload (Stale-Gate Fix)

| ID | Item |
|----|------|
| H9 | **`reload_risk_config()` — a long-running host can re-read risk-gate config without a restart.** Motivated by a user report: the webapp's execute *preview* showed `$0.05` MLB bets as **APPROVED** while a CLI scan run moments later returned nothing. Root cause: `kalshi_executor.py` snapshots all ~24 risk-gate globals (`MIN_MARKET_PRICE`, `MIN_EDGE_THRESHOLD_*`, `MIN_COMPOSITE_SCORE`, `MIN_CONFIDENCE`, the R1 NO-side gates, `CROSS_CATEGORY_DEDUP`, per-sport dicts, etc.) from `app.config` **at import time**. The CLI re-imports per run so it's always fresh; the Streamlit server imports once at startup and kept its pre-edit gates after the operator changed `.env` at 11:36 — so at 12:43 it approved bets the live `MIN_MARKET_PRICE=0.06` floor forbids ($0.05 < $0.06, Gate 3.5). H6 (config centralization) deliberately kept these as mutable module globals so the test monkey-patch seam works; that same design is what goes stale in a long-running process. **Fix:** new `reload_risk_config()` in `kalshi_executor.py` — `load_dotenv(override=True)` (re-read the `.env` file over the process env) → `reset_config()` → re-assign every risk global from a fresh `get_config()`. Wired into `webapp/services.py` at the top of `run_scan()` (refreshes the scan's R18 Gate-preview column) and `run_execute()` (refreshes before sizing/gating — the path that approved the sub-floor bet). **Deliberately NOT called by `size_order`/`execute_pipeline`** so the test seam (`kalshi_executor.MIN_MARKET_PRICE = 0`) is never clobbered mid-run; the CLI is untouched (already fresh per invocation). On Streamlit Cloud there's no `.env`, so `load_dotenv` is a no-op and the rebuild re-reads the injected Secrets already in the env — and a Secrets save there auto-reboots anyway, so the staleness window is local-only. **Import-time block and `reload_risk_config()` carry reciprocal "keep in sync" comments** since both assign the same globals. **Verification:** +3 tests (`TestReloadRiskConfig`: env-edit propagation, idempotent-without-edits, end-to-end `size_order` rejects a $0.05 bet after a raised floor) → **411 passing** (was 408). Live file-edit smoke confirmed: editing `.env` MIN_MARKET_PRICE 0.06→0.30 while the process runs, then `reload_risk_config()`, updates the global without restart. **Operator docs:** `docs/web-app/LOCAL.md` (restart-after-`.env`), `docs/web-app/CLOUD.md` (Secrets→reboot), CLAUDE.md callout after Risk Limits. Files: `scripts/kalshi/kalshi_executor.py`, `webapp/services.py`, `tests/test_risk_gates.py`, `CLAUDE.md`, `docs/web-app/LOCAL.md`, `docs/web-app/CLOUD.md`. |

##### 2026-05-13 — R11 Explicit Direction Fields in Settlement Schema

| ID | Item |
|----|------|
| R11 | **Settlement records now carry `fair_value_yes` (always YES-perspective) and `fair_value_side` (perspective tag for the legacy `fair_value` field).** Motivated by the F8 note that the legacy `fair_value` field flipped perspective between bets in the pre-R5 cohort — post-hoc NO-side analysis required reading `side` separately and flipping, which was easy to get wrong and impossible to audit. **Fix:** new `_compute_fair_value_yes(trade) -> (float \| None, str \| None)` helper in `kalshi_settler.py` returns the YES-perspective probability and the explicit side tag. Wired into `build_settlement_record()`; legacy `fair_value` unchanged so `model_calibration.py`'s bet-side reader (which has been correct since R5) is not disturbed. Missing-side returns `(None, None)` — refusing to guess perspective is safer than fabricating one; missing fair_value with side present returns `(None, side)` to preserve the partial metadata. **Verification:** +5 regression tests in `test_reconciliation.py` — dedicated `TestComputeFairValueYes` class (YES preserves, NO flips to 1-fv, missing side yields both None, missing fair_value keeps side tag) plus `test_carries_r11_perspective_fields` on `build_settlement_record` and an extended assertion on the missing-optional-fields shape test. **No code changes to the calibration loader** — that's a separate cross-cut that should land when we want YES-perspective slicing across the full cohort; today's bet-side reader is correct for post-R5 records. **No backfill** of the 178 pre-R5 orphans — the underlying side resolution isn't reliably recoverable and synthesizing the field would be fabricating data; `data/history/README.md` updated to spell out the lifecycle. Files: `scripts/kalshi/kalshi_settler.py`, `tests/test_reconciliation.py`, `data/history/README.md`. |

##### 2026-04-30 — U2 Daily P&L Email Digest

| ID | Item |
|----|------|
| U2 | **Morning P&L email digest — `daily_summary.py` + `Daily-Summary` (4:50 AM PST) + `Email-Daily-Summary` (5:00 AM PST).** First proactive measurement-and-visibility ship since the R12-R26 P1 wave; the digest gives a daily wake-up signal between the monthly R12 calibration runs while the post-R13/R14 cohort is still settling. **What it covers:** (a) **Yesterday** — rolling 24h settlements with W/L/$ summary, per-sport breakdown table, top winner + top loser. (b) **Open Exposure** — current filled positions from `kalshi_trades.json` (excludes `closed_at`, `fill_status=resting`, `status=error`, zero-fill), $ at risk total + per-sport split. (c) **Pending Today** — open positions whose game datetime falls on today's PST calendar day, parsed from ticker via `parse_game_datetime()`. (d) **Context** — live Kalshi balance fetched via `KalshiClient.get_balance_dollars()` (best-effort, falls back gracefully on API failure) plus a 7-day rolling line (WR, P&L, ROI, Brier — Brier flips probability for NO-side bets so it's directly comparable to the calibration report's reading). **Empty-day proof-of-life:** matches the SameDay email policy from `feedback_sameday_empty_emails`. The report still produces all four sections with `_No settlements in window._` / `_No open positions._` placeholders, and the email task still fires — empty digest = "the system ran" signal. **Architecture:** pure-functions split (`load_recent_settlements`, `load_open_positions`, `aggregate_yesterday`, `aggregate_exposure`, `filter_pending_today`, `rolling_7d_context`, `render_report`) with `build_report()` as the test-friendly composition entry. I/O isolated to `_fetch_balance()` (live Kalshi call, swallowed on failure) and the `--save` filesystem write. **Window choice:** rolling 24h instead of "yesterday in PST" — robust to DST, captures everything from yesterday's slate plus last night's late settlements (the 11 PM PST settler writes `settled_at` UTC timestamps that span ~07:00 UTC → 07:00 UTC the next day for PST 11PM-11PM games). **Timing choice:** 4:50 AM PST gives the digest a slot before `All-Sports-SameDay-Execution` (5:05 AM) so "Open Exposure" reflects overnight carry rather than mixing in today's new fills. The 10-min email buffer matches the `Weekly-Analysis` precedent. **Wrappers:** `scripts/schedulers/maintenance/daily_summary.bat` (cd + venv python + `--save`) and `scripts/custom/Shell-Scripts/Run-Reports/Daily-Summary-Report.sh` (mirrors the existing email pattern: `claude --dangerously-skip-permissions -p` + `agentmail` skill, dark-themed HTML, skip-on-missing-report). **Verification:** +26 regression tests in `tests/test_daily_summary.py` covering window-boundary inclusion, malformed-timestamp skip, sort order, open-position filtering (closed/resting/error/zero-fill), per-sport aggregation math, pending-today PST filtering, 7-day rolling minimum-sample threshold, balance present/missing rendering, full empty-day report renders all four sections. **381 tests passing** (was 355). End-to-end .bat smoke confirmed: live Kalshi balance fetched, report written to `reports/Performance/daily_summary_YYYY-MM-DD.md`. Files: `scripts/kalshi/daily_summary.py` (new), `scripts/schedulers/maintenance/daily_summary.bat` (new), `scripts/custom/Shell-Scripts/Run-Reports/Daily-Summary-Report.sh` (new), `tests/test_daily_summary.py` (new), `docs/my-documents/task-schedules/README.md` (added 0a/0b sections + install snippet). |

##### 2026-04-29 — R8 Cross-Category Same-Event Dedup (Optional, Per-Sport)

| ID | Item |
|----|------|
| R8 | **`dedup_correlated_brackets()` now optionally collapses ML + Total + Spread on the same game to one bet, configurable per sport.** Motivated by F11 — 14-day review showed 12 matchups bet ≥2× in 14d, several same-day on different categories. The existing `(event_key, category)` dedup catches alt-line brackets within a category (3× Over lines on the same NBA game) but treats ML + Total + Spread on the same game as 3 distinct bets, which adds correlated exposure with no diversification benefit when the game's narrative drives all three (NBA blowouts, NFL routs). **Implementation:** added `cross_category_sports: set[str] | None` parameter to `dedup_correlated_brackets()` in `kalshi_executor.py`. When an opportunity's sport (via `_detect_sport`) is in the set, the dedup key becomes `(_event_key, "_xcat")` instead of `(_event_key, category)`, so all categories on the same game collapse to the highest-composite-score row. Futures pass-through (R21) is preserved — checked first, immune to the new branch. **Config:** new `GateThresholds.cross_category_dedup: bool` (env `CROSS_CATEGORY_DEDUP`, default `false`) and `PerSportOverrides.cross_category_dedup: dict[str, bool]` (env `CROSS_CATEGORY_DEDUP_<SPORT>=true|false`, mirrors R9 pattern). New `Config.cross_category_dedup_for(sport)` helper resolves per-sport→global fallback. Per-sport `false` overrides a global `true` in either direction. **Wiring:** module-level `CROSS_CATEGORY_DEDUP` and `_PER_SPORT_CROSS_CATEGORY_DEDUP` constants in `kalshi_executor.py` (test patchable, mirrors `_PER_SPORT_SERIES_DEDUP`); `_cross_category_sports()` helper builds the active set on each call. `execute_pipeline` passes the resolved set to dedup and surfaces the active sports in the dedup banner (`Deduped correlated brackets: 12 -> 8 opportunities (cross-category: ['nba', 'nfl'])`) when any are enabled. **Why default OFF:** cross-category correlation is sport-dependent (NHL low-scoring → ML and Total are weakly correlated; NBA → all three move together on blowouts). Opt-in lets the user A/B test per sport against live calibration data. Existing per-event cap (Gate 6, `MAX_PER_EVENT=2`) already provides a soft ceiling. **Verification:** +4 regression tests in `TestDedupCorrelatedBrackets` (off-default preserves pre-R8 behavior; on collapses 3 categories to highest-composite; per-sport scope — NBA collapses but MLB on same scan stays uncollapsed; futures pass-through preserved even when their sport is opted in). +4 config tests in `TestPerSportOverrides` (default off; global on cascades to all sports; per-sport-only override; per-sport false overrides global true). **355 tests passing** (was 347). Files: `app/config.py`, `scripts/kalshi/kalshi_executor.py`, `tests/test_risk_gates.py`, `tests/test_config.py`, `.env.example`, `CLAUDE.md`. |

##### 2026-04-29 — R26 File-Backed Scan Cache (Row-Order Lock for `--pick`)

| ID | Item |
|----|------|
| R26 | **File-backed cache of the last preview's row→ticker mapping at `data/cache/last_scan.json` — `--pick … --execute` now replays the cached preview instead of rescanning live.** Motivated by a 2026-04-29 user-reported bug: ran `python scripts/scan.py sports --unit-size .5 --max-bets 10 --min-bets 3 --budget 15% --exclude-open` and got 5 games. Then ran with `--pick '1,3,4,5' --execute` (without `--exclude-open`); the second call did a fresh live scan, the row order shifted on price/score drift, and the wrong bets were placed against rows 1/3/4/5 of a different ranking. Two underlying causes: (a) every `scan.py` invocation runs `scan_all_markets()` fresh — Kalshi prices, Odds API consensus, and composite scores all refresh between calls, and the final sort is by `composite_score` (`edge_detector.py:1686`); (b) the second invocation dropped `--exclude-open`, which alone changes the row universe. **Fix:** new `scripts/shared/scan_cache.py` with `store(fingerprint, sized_orders, bankroll)`, `load() -> {fingerprint, saved_at, age_seconds, bankroll_at_scan, rows}`, `clear()`, `fingerprints_match(saved, current) -> (ok, diffs)`. Single file, latest preview only. Silent-on-error throughout — corrupt file = miss, never an exception. Mirrors `odds_cache.py` precedent. New `ScanCacheConfig` in `app/config.py` exposes `SCAN_CACHE_TTL_SECONDS=600` (10 min — long enough to read the table and pick rows, short enough that a user returning hours later gets a fresh scan) and `SCAN_CACHE_ENABLED=true`. `validate()` rejects negative TTL. **Wiring in `execute_pipeline`:** added `fingerprint`, `cached_rows`, `cache_age_seconds` params. The dedup / sizing / bet-ratio-cap / budget-cap block is now wrapped in `if cached_rows is None:` so the replay path bypasses it entirely (those decisions are locked from the original preview). On the fresh-scan path, the rendered preview rows are persisted right after `console.print(table)`. **Wiring in `edge_detector.py main()`:** new `--rescan` CLI flag for opt-out. When `args.execute` AND (`args.pick` OR `args.ticker`) AND not `args.rescan`, attempt cache load before scanning. Fingerprint = `{scanner, filter, category, date, exclude_open, min_edge, top}` — the args that determine row identity. `--unit-size`, `--max-bets`, `--budget`, `--min-bets` deliberately excluded since they reshape sizing/caps but the rows already in `cached_rows` were sized under the original args. On fingerprint mismatch, prints the differing keys and rescans. Banner on hit: `Replaying cached preview (N rows, age Xs)` + `Pass --rescan to force a fresh scan instead.` **Verification:** +17 regression tests in `tests/test_scan_cache.py` (round-trip preserves SizedOrder + Opportunity fields; age-is-recent; miss-after-TTL; disabled-via-zero-ttl; disabled-via-env-flag; corrupted-file-silently-misses; missing-file; wrong-version; missing-required-fields; store-disabled-does-not-write; creates-parent-dir; clear-removes-file; clear-when-missing; fingerprints identical-match / value-mismatch / extra-key / exclude-open-change-mismatch — the last specifically reproduces the user's bug case). **347 tests passing** (was 330). Lint clean. Live offline round-trip smoke (mocked SizedOrder + Opportunity): `store()` writes valid JSON, `load()` rehydrates with `age_seconds=0`, `fingerprints_match` returns `(True, [])`. Files: `app/config.py`, `scripts/shared/scan_cache.py` (new), `scripts/kalshi/kalshi_executor.py`, `scripts/kalshi/edge_detector.py`, `tests/test_scan_cache.py` (new), `.env.example`, `CLAUDE.md`. |

##### 2026-04-28 — R24b File-Backed Odds API Cache

| ID | Item |
|----|------|
| R24b | **Two-tier cache for Odds API responses — in-process dict in front of a new file-backed layer at `data/cache/odds/<sport_key>__<markets>.json`.** Motivated by F31 (one key dropped 175 → 0 remaining in 5 minutes during a normal session): every fresh `scan.py` invocation started with empty caches and refetched all 18 sport keys from scratch, so back-to-back scans (scheduler bursts, dashboard re-renders) doubled quota burn unnecessarily. R23 fixed the persistent quota counter; R24a fixed the dashboard's lack of `@st.cache_data`; R24b is the structural piece — persist the actual response payloads across processes. **Implementation:** new `scripts/shared/odds_cache.py` with `load(sport_key, markets, ttl_seconds) -> (events, age_seconds) \| (None, None)`, `store()`, `clear()`. Comma-sanitized filenames (`h2h,spreads,totals` → `h2h_spreads_totals`); the original markets string is preserved inside the JSON for round-trip clarity. Silent-on-error throughout — corrupt file = miss, never an exception. New `OddsCacheConfig` in `app/config.py` exposes `ODDS_CACHE_TTL_SECONDS=300` (5 min default — longer than typical filter-fiddling, shorter than meaningful pre-game line movement) and `ODDS_CACHE_ENABLED=true`. `validate()` rejects negative TTL. Wired into both `edge_detector.fetch_odds_api()` and `futures_edge.fetch_outrights()`; the existing in-process dicts stay so existing `_odds_cache.clear()` test calls still work, the file layer survives across processes. Hits log `Odds API file cache hit for X (age Ns, M events)` so cache age is visible in scan output. **Verification:** +10 regression tests in `tests/test_odds_cache.py` (hit-within-TTL, miss-after-TTL, disabled-via-zero-ttl, corrupted-file-silently-misses, missing-file, missing-required-fields, store round-trip, store-creates-parent-dir, clear-removes-all, clear-when-dir-missing). Updated the autouse fixture in `TestFetchOddsApiKeyRotation` to redirect `odds_cache._CACHE_DIR` to a tmpdir alongside the existing quota-cache redirect — otherwise the rotation tests sharing one process would pick up each other's stored responses. **330 tests passing** (was 320). Offline round-trip smoke (mocked HTTP, fake key): call 1 hits HTTP and writes `baseball_mlb__h2h_spreads_totals.json`; clearing only the in-process dict and calling again returns identical events with 0 HTTP calls. Files: `app/config.py`, `scripts/shared/odds_cache.py` (new), `scripts/kalshi/edge_detector.py`, `scripts/kalshi/futures_edge.py`, `tests/test_odds_cache.py` (new), `tests/test_edge_detection.py`, `.env.example`. |

##### 2026-04-27 — R5 Settlement-Schema Fix + Reconciliation Report + R9 Per-Sport Series Dedup

| ID | Item |
|----|------|
| R9 | **`SERIES_DEDUP_HOURS` is now per-sport.** F12 (14-day review): a NYM/LAD MLB pair was bet on Apr 14 and again on Apr 16 (~49h apart), both bets landed and both lost. The single 48h global window was tight enough to leak adjacent-day series repeats. **Fix:** added `series_dedup_hours: dict[str, int]` to `PerSportOverrides` in `app/config.py`, populated from `SERIES_DEDUP_HOURS_<SPORT>` env vars (same pattern as `MIN_EDGE_THRESHOLD_<SPORT>`). Extended `recent_matchups_from_log()` with a `per_sport_hours` keyword arg so each sport's recent-matchup keys are gated on its own cutoff (sports without an override fall back to the global). Updated Gate 7 in `size_order()` to look up the per-sport window for the candidate's matchup and report the actual sport-specific window in the rejection message ("series_dedup (matchup NYMLAD bet within 72h)" vs the old "within 48h"). A per-sport `0` opts that sport out of the gate even when the global is non-zero, and a global `0` with a per-sport override re-enables the gate just for that sport — both directions tested. **Live `.env` updated with `SERIES_DEDUP_HOURS_MLB=72` and `SERIES_DEDUP_HOURS_NHL=72`** (NHL series cycle on consecutive days the same way MLB does; 72h covers any 3-game series start-to-finish). NBA leaves the global default — same opponent twice within 48h is rare outside playoffs. **Verification:** +9 regression tests in `test_risk_gates.py` (6 set-construction edge cases including the exact F12 scenario at 49h, plus 3 gate-rejection-message cases) + 4 config-layer tests in `test_config.py`. Existing `test_disabled_when_hours_zero` updated to also clear `_PER_SPORT_SERIES_DEDUP` since per-sport overrides can re-enable the gate independently of the global. **320 tests passing** (was 307). Live config smoke test confirms `_PER_SPORT_SERIES_DEDUP={'mlb': 72, 'nhl': 72}` loads correctly. Files: `app/config.py`, `scripts/kalshi/kalshi_executor.py`, `tests/test_risk_gates.py`, `tests/test_config.py`, `.env`, `.env.example`, `CLAUDE.md`. |
| R5 | **Settler now writes a self-describing settlement record + new reconciliation report makes the trade-log/settlement join visible.** Original F8 finding said "10/76 14-day settlements match a trade-log entry"; investigation revealed worse state — production trade log was wiped at some point, leaving 178 orphan settlements (0/178 trade_id overlap) plus 1 test stub. **Fix:** (a) extracted `build_settlement_record()` helper in `kalshi_settler.py` and extended the schema to carry `order_id`, `title`, `category`, `edge_source`, `closing_price`, `clv`, `composite_score`, `risk_approval`, `bankroll_pct`, `unit_size`, `fill_status` alongside the existing legacy fields. After this, every future settlement is fully self-describing for calibration without joining to the trade log. (b) Added `print_reconciliation()` to `risk_check.py` (`--report reconciliation`) showing trade-log/settlement counts, `trade_id` overlap, orphan-window dates, and field-coverage matrix per R5-added field. Surfaces the gap at every session start. (c) Wrote `data/history/README.md` documenting the schema lifecycle + pre-R5 historical-orphan rationale (no backfill — fields don't exist on disk and synthesis would be lying); added a `.gitignore` exception so the README ships with the repo while runtime state stays gitignored. **Verification:** +10 regression tests in `tests/test_reconciliation.py` (5 schema-coverage + 5 report-rendering across empty/all-orphan/clean-join/mixed cases) → **307 tests passing.** Live `--report reconciliation` against the user's data renders cleanly: 178 orphans, 0% R5-field coverage, oldest 2026-03-22, newest 2026-04-27 — the expected pre-R5 baseline. Does NOT solve the historical 178 orphan settlements; it stops the bleed and makes the gap measurable. A3 (DB migration) can now import a clean schema. Files: `scripts/kalshi/kalshi_settler.py`, `scripts/kalshi/risk_check.py`, `tests/test_reconciliation.py`, `data/history/README.md`, `.gitignore`. |

##### 2026-04-25 — H6 Config Centralization (Phases 1–3 all shipped same day)

| ID | Item |
|----|------|
| H6 | **`app/config.py` is the single source of truth for every runtime knob.** Refactor only — no behavior changes, no new knobs. **Phase 1:** built `app/config.py` with 10 frozen dataclasses grouped by concern (`KalshiCredentials`, `KalshiProdCredentials`, `OddsApiCredentials`, `AlpacaCredentials`, `TelegramCredentials`, `RiskLimits`, `GateThresholds`, `KellyConfig`, `PerSportOverrides`, `System`). Each has `from_env()` for one-shot coercion; aggregate `Config.from_env()` runs `validate()` (catches `MAX_BET_SIZE < UNIT_SIZE`, `MIN_CONFIDENCE` not in {low,medium,high}, `KELLY_FRACTION` outside [0,1], etc.). `get_config()` / `reset_config()` memoized accessor + tests-and-Streamlit-friendly reset. `Config.edge_threshold_for_sport(sport)` replaces the per-sport-edge lookup idiom. +32 tests in `tests/test_config.py`. **Phase 2:** migrated 8 script groups (`doctor.py` → `risk_check.py` → `kalshi_client.py` → `edge_detector.py` + `fetch_odds.py` → `kalshi_executor.py` (23 calls — the largest, including all 21 module-level risk constants and the per-sport edge override loop) → 6 small modules (`prediction_scanner.py`, `backtester.py`, `logging_setup.py`, `odds_api.py`, `fetch_market_data.py`, `telegram_bot.py`) → `webapp/services.py`). **65 reads removed across 16 files.** Module-level constants stay mutable globals so existing `tests/test_risk_gates.py` monkey-patching pattern continues to work. Sys-path side-fix added to `scripts/shared/paths.py` and `.venv/Lib/site-packages/edge_radar.pth` to prepend `PROJECT_ROOT` so `from app.config import …` resolves in scripts that import `paths`. **Phase 3:** lint guard `scripts/lint/check_config_centralization.py` walks `app/`/`scripts/`/`webapp/`, excludes `app/config.py` + `scripts/custom/` + `scripts/lint/`, skips comment-only lines and lines tagged `# config-bootstrap`. Wired into `make lint-config` + `.pre-commit-config.yaml` (`pass_filenames: false` + `always_run: true` so it sees the whole tree). +5 tests (`tests/test_lint_config_centralization.py`). **Final:** **297 tests passing. Production-code `os.getenv` reads outside `app/config.py`: 0.** The 4 `os.environ` writes in `webapp/services.py` are the deliberately retained Streamlit secrets bootstrap, annotated `# config-bootstrap` and lint-recognized. Doc: `docs/my-documents/enhancements/CONFIG_CENTRALIZATION.md`. Replaces and supersedes the partial H1/H5 fix. |

##### 2026-04-24 — R12–R18 + R20 + R21–R23 + R24a + R25 Shipped (30-day cycle + automation + scanner parity + 3 futures fixes + Odds API key rotation + webapp scan cache + scan-table gate column + prediction audit + prediction safety gate)

| ID | Item |
|----|------|
| R15 | **`model_calibration.py` now reads `data/history/kalshi_settlements.json`** instead of `trade_log`. `trade_log` only captured 16 entries (3 closed) because most bets predated its introduction; settlements file has 173. Added `_load_settled_trades()` normalizer that maps `cost` → `cost_dollars`, `won` → `settlement_won`, `settled_at` → `closed_at`, and derives `category` from ticker via `bet_type_from_ticker()`. Replaced string-based ISO cutoff comparison with `datetime` parsing that tolerates trailing `Z`. All existing downstream helpers (`_brier_score`, `_calibration_buckets`, `_edge_bucket_stats`, `_dimension_stats`, cross-tab, recommendations) unchanged — only the loader swapped. Files: `scripts/kalshi/model_calibration.py`. |
| R12 | **First R12 calibration run against full 160-trade cohort.** Report: `reports/Calibration/2026-04-24_calibration_report.md`. Produced 10 prioritized recommendations (2 HIGH, 8 MEDIUM). Headline: Brier 0.2657 (worse than coin-flip, confirming F17 persistence). Per-sport Brier surfaces NBA = 0.3306 as the worst-calibrated sport, motivated R14 floor bump. High-confidence WR < Medium confirms F14 → R13. Edge-bucket inversion softened to 25%+ @ +16% ROI vs -24% at 14-day window — evidence R2 is working, but Brier hasn't moved. |
| R14 | **`MIN_EDGE_THRESHOLD_NBA` bumped 0.08 → 0.12.** Scope deliberately minimal: one env bump after slicing the 17-bet NBA cohort showed the real damage was concentrated in High-confidence picks (1-6, -71% ROI), not a sport-wide probability-model problem. NBA Totals (n=13) is near coin-flip at +5% ROI, Brier 0.3308; NBA ML (n=3) was -106% ROI but 2/3 of the losers were sub-10¢ lottery tickets already caught by R7. Playoff-specific stdev and "NBA Totals-only" filter explicitly rejected — not enough sample to justify either. Real fix for High-confidence NBA bleed moves to R13. **Also fixed**: live `.env` was missing both NBA and NCAAB overrides entirely (silently falling back to the 3% global floor). Added both. Files: `.env`, `.env.example`, `CLAUDE.md`, `docs/ARCHITECTURE.md`, `docs/setup/SETUP_GUIDE.md`, `docs/web-app/CLOUD.md`, `scripts/kalshi/kalshi_executor.py` (docstring), `.claude/html/index.html`. |
| R13 | **Confidence bumps now one-way (down only).** Changed `_adjust_confidence_with_stats()` in `edge_detector.py`: `contradicts` still drops a tier, `supports` is now a no-op (previously bumped up a tier). Applies to all three call sites (team stats, rest/B2B, sharp money) since they share the function. Rationale: 30-day data showed High-confidence WR 47% < Medium 53% overall, and NBA High = 1-6 / -71% ROI. Upward bumps were correlated with inflated claimed edge, not better outcomes — the calibration report's HIGH-priority recommendation matched this directly. Base "high" tier is still reachable via the book-count rule (≥8 sharp books + tight consensus <5%), just the bolt-on bumps don't push you there anymore. Rare R1 (NO-favorite guard requires `confidence=high`) naturally tightens as a side-effect — correct direction. +4 regression tests (`TestConfidenceBumpsOneWay`) → 222 tests passing. Files: `scripts/kalshi/edge_detector.py`, `tests/test_edge_detection.py`. |
| R16 | **Monthly R12 calibration cron.** Added `calibration` profile to `install_windows_task.py` — schedules `model_calibration.py --days 30 --save` on day 1 of each month at 02:00 (after nightly settler). Required extending the installer to support `MONTHLY` + `day` keys; daily profiles unchanged. Updated `docs/setup/AUTOMATION_GUIDE.md` profile table and recommended-setup block. Ship-to-user is one command: `python scripts/schedulers/automation/install_windows_task.py install calibration`. Files: `scripts/schedulers/automation/install_windows_task.py`, `docs/setup/AUTOMATION_GUIDE.md`. |
| R17 | **Scanner flag parity — `--budget` + `--report-dir` across all four scanners.** Futures / prediction / polymarket didn't accept `--budget` or `--report-dir`, and even if they had, `execute_pipeline(budget=…)` wasn't threaded through. Triggered by "`scan --exclude-open --budget 5%` isn't available" + scanner audit that found the gap uniform across three scanners. Extracted `parse_budget_arg()` into `kalshi_executor.py` so all four scanners share the same "10%" / "15" / "0.15" / "150" parsing contract. Added `--budget` + `--report-dir` to futures / prediction / polymarket argparse; wired each to `execute_pipeline(budget=…)` and `save_scan_report(output_dir=…)`. Sports scanner's inline 7-line budget block replaced with the shared helper. Files: `scripts/kalshi/kalshi_executor.py`, `scripts/kalshi/edge_detector.py`, `scripts/kalshi/futures_edge.py`, `scripts/prediction/prediction_scanner.py`, `scripts/polymarket/polymarket_edge.py`. |
| R21 | **`dedup_correlated_brackets()` now passes futures through unchanged.** Bug discovered when debugging "only 1 edge in futures scan". Dedup's `(event_key, category)` grouping collapsed all 16+ team outcomes in a championship (`KXNBA-26-LAL`, `KXNBA-26-BOS`, …) to one entry because `_event_key()` stripped the team suffix. Correct for alt-line brackets ("Over 221.5" / "Over 224.5" on same game), wrong for futures where each team is a distinct independent bet. Fix: when `opp.category == "futures"`, use the full ticker as the dedup key so each outcome survives. Concentration on championship still bounded by Gate 6 (`MAX_PER_EVENT=2`) — verified against live data: 15 MLB WS opps now correctly flow to Gate 6 (caps at 2) rather than getting pre-killed. Also retracts F24 (my earlier hand-waved explanation blaming `--exclude-open`). +5 regression tests (`TestDedupCorrelatedBrackets`) → 227 tests passing. Files: `scripts/kalshi/kalshi_executor.py`, `tests/test_risk_gates.py`. |
| R22 | **`FUTURES_MAP` prefix-collision + semantic-mismatch fix.** User noticed futures scan surfacing "+30-75% edge" on basically every MLB team — too good to be true, and it was. Two bugs compounding (F28): (1) prefix matching used `startswith` so `KXMLBPLAYOFFS-26-LAD` matched the `KXMLB` entry and got priced against World Series winner odds; (2) even if ordering was fixed, the `KXMLBPLAYOFFS` entry itself pointed to championship-winner odds, which fundamentally misrepresents playoff-qualification probability. Same issue silently affected NBA/NHL conference tickers. **Fix:** (a) switched matching from `ticker.startswith(prefix)` to exact series extraction (`ticker.split("-", 1)[0]` lookup) — surgical, can't collide; (b) removed the 5 semantically-broken entries from `FUTURES_MAP` (`KXMLBPLAYOFFS`, `KXNBAEAST`, `KXNBAWEST`, `KXNHLEAST`, `KXNHLWEST`) with a comment explaining why each needs a proper data source before being re-added (tracked in R19); (c) updated `FUTURES_FILTER_SHORTCUTS` to match. Live verification: same scan went from 45 bogus opportunities at +30-75% edge → 2 real opportunities at +4% edge (OKC NBA Finals, LAD World Series). +7 regression tests (`TestFuturesSeriesMatch`) → 234 tests passing. Files: `scripts/kalshi/futures_edge.py`, `tests/test_edge_detection.py`. |
| R23 | **Odds API key rotation + persistent quota cache.** Discovered when `--filter mlb-futures` returned "No outright data" despite the unfiltered scan working 5 minutes earlier. Live probe showed first 5 of 10 keys exhausted; `futures_edge.fetch_outrights` used `for attempt in range(3)` so the retry loop exited before cycling to a healthy key (F29). Compounded by F30: `_remaining` was process-local, so every fresh invocation rediscovered exhaustion the hard way. **Fix:** (a) replaced `range(3)` in `fetch_outrights` with the same `tried: set[str]` loop `edge_detector.fetch_odds_api` already uses (cycles through every configured key); (b) added `mark_exhausted()` to `odds_api.py` — called on 401 responses to immediately flag the key as dead; (c) added persistent quota cache at `data/cache/odds_api_quota.json` — `_remaining` dict is loaded at `_load_keys()` time and saved on every `report_remaining()` / `mark_exhausted()` call; (d) `get_current_key()` now auto-advances past keys with cached `remaining == 0` so fresh processes skip exhausted keys instantly. Fallback: if every key is cached exhausted, return the current slot anyway so a monthly quota reset can be re-discovered. Same `mark_exhausted` call added to `edge_detector.fetch_odds_api` for parity. +13 regression tests (`tests/test_odds_api.py` + autouse fixture on `TestFetchOddsApiKeyRotation` to prevent cache pollution) → 247 tests passing. Files: `scripts/shared/odds_api.py`, `scripts/kalshi/futures_edge.py`, `scripts/kalshi/edge_detector.py`, `tests/test_odds_api.py`, `tests/test_edge_detection.py`. |
| R24a | **Webapp `run_scan()` now cached with `@st.cache_data(ttl=60)`.** Zero `@st.cache` decorators existed anywhere in `webapp/` before this (F32) — every scan-button click fired a fresh Odds API fetch, and exploratory "try a filter, scan, change filter, scan again" sessions burned requests fast. Added a 60s TTL cache keyed on all scan parameters (market_type, ticker_filter, category, date, min_edge, top_n, exclude_open, cross_ref). Client param renamed `client` → `_client` per Streamlit convention for unhashable args. CLEAR button now also calls `run_scan.clear()` so the user can force a refresh on demand. Rationale for 60s: Kalshi prices can move within a minute; absorbs the typical rapid-click loop without serving stale data long enough for anyone to act on. Investigation under R24 also surfaced F33 (8 manually-installed scheduler tasks not tracked by the installer) → R24c, and motivated R24b (file-backed odds cache across CLI invocations). Files: `webapp/services.py`, `webapp/views/scan_page.py`. |
| R18 | **Scan tables now show a "Gate" column previewing which rows will survive the risk gates.** User noticed `scan --filter mlb-futures --unit-size .5` rejected the only opportunity (LAD at 4.6 composite score) while `scan --filter mlb-futures` (scan-only, no unit-size) happily listed it with no indication that the executor would reject. F23 / F35 flagged this pattern — scan shows edges the executor won't take. **Fix:** Added `preflight_gate_status(opp)` helper in `kalshi_executor.py` that checks the 5 static per-opportunity gates (Gate 3 edge floor, Gate 3.5 price floor, Gate 4 composite, Gate 4.5 confidence, Gate 4.6 NO-favorite) and returns a short label (`"ok"` / `"edge"` / `"price"` / `"score"` / `"conf"` / `"no-fav"`). Wired into the scan-table render path of all four scanners (`edge_detector.print_opportunities`, `futures_edge` inline table, `prediction_scanner.print_opportunities`, `polymarket_edge` inline table). Color-coded: green "ok" for pass, red label for the failing gate. Runtime gates (daily loss, position count, duplicate ticker, per-event cap, series dedup) still require live portfolio state — docstring is explicit that "ok" is a necessary-but-not-sufficient signal. +9 regression tests (`TestPreflightGateStatus`) covering each gate and the first-failing-wins ordering → 256 tests passing. Files: `scripts/kalshi/kalshi_executor.py`, `scripts/kalshi/edge_detector.py`, `scripts/kalshi/futures_edge.py`, `scripts/prediction/prediction_scanner.py`, `scripts/polymarket/polymarket_edge.py`, `tests/test_risk_gates.py`. |
| R20 | **Prediction-market audit complete — 6 modules parked until rebuilt.** First full evaluation of `prediction_scanner.py` since it shipped. Covered the 6 edge-detection modules (crypto / weather / spx / mentions / companies / politics) plus live scan output and historical settlements. Surfaced F34-F39: all 6 modules cache live data without TTL, zero prediction-market bets in 173 historical settlements (no calibration data at all), live scans produce garbage fair values (crypto +80% on 4¢ tails; a Miami weather bet was one `--unit-size` away from executing at $1.00 fair value with HIGH confidence / 9.7 composite), 4 of 6 modules have no unit tests, `DEMO_KEY` hardcoded as FRED API credential. Audit artifact: the Explore-agent report is in the conversation transcript; structural conclusions captured in F34-F39. Prescription: R25 ships the safety gate to block execution; R25b (TTL caches) and R25c (rebuild with tests) are the prerequisites for M1-M4. |
| R25 | **Gate 4.7 — prediction-market safety gate.** New reject gate in `size_order()`: rejects opportunities where `opp.category in {"crypto", "weather", "spx", "mentions", "companies", "politics"}` unless `ALLOW_PREDICTION_BETS=true`. Default: false. Placed between Gate 4.6 (NO-favorite) and Gate 5 (duplicate ticker). `preflight_gate_status()` extended to return `"pred-off"` so the R18 scan-table Gate column surfaces the rejection at scan time — users see it before running `--unit-size`. Directly prevents the Miami weather bet (F36) from ever executing. `ALLOW_PREDICTION_BETS` plumbed through `.env.example` and CLAUDE.md (Execution Gates table + Risk Limits block). Sports / futures / polymarket paths unchanged — verified live. Users can opt back in per-session with the env flag once R25b+R25c are shipped. +4 regression tests covering: all 6 categories blocked by default, env flag opens the gate, sports categories untouched, end-to-end `size_order` integration on a crypto opportunity. 260 tests passing. Files: `scripts/kalshi/kalshi_executor.py`, `.env.example`, `CLAUDE.md`, `tests/test_risk_gates.py`. |

##### 2026-04-22 — R7 Shipped (Gate 3.5 lottery-ticket floor)

| ID | Item |
|----|------|
| R7 | **Gate 3.5 — minimum market-price floor.** New reject gate in `size_order()` rejects any bet priced below `MIN_MARKET_PRICE` (default **$0.10**, user preference: "kind of like the long shots. But I definitely agree We shouldn't go too low. I like .10"). Strict less-than: $0.09 rejected, $0.10 approved. No exception for edge/confidence — unlike Gate 4.6, this is a hard structural floor. `MIN_MARKET_PRICE=0` disables. Addresses F10 (sub-10¢ bets went 1W-3L with model claiming "+50% edge" on 8-10¢ longshots). Plumbed through `.env.example`, `CLAUDE.md` (gate table + Risk Limits block), `webapp/services.py` flat-keys. +5 regression tests (218 total). Two pre-existing tests (`test_contracts_capped_by_bankroll`, `test_price_clamped_to_valid_range`) that intentionally use sub-10¢ prices patched to set `MIN_MARKET_PRICE=0` for their scope. Docs touched in Q3 (`SCRIPTS_REFERENCE.md`, `AUTOMATION_GUIDE.md`, `web-app/LOCAL.md`) rewritten from "11 risk gates" → "all risk gates" + CLAUDE.md heading changed to "Execution Gates" — count-free references so the next gate addition won't require doc churn. Files: `scripts/kalshi/kalshi_executor.py`, `.env.example`, `CLAUDE.md`, `webapp/services.py`, 3 doc files, `tests/test_risk_gates.py`. |

##### 2026-04-22 — Repo Analysis Response (Q1–Q5)

| ID | Item |
|----|------|
| Q1 | **Web app `market_type` wired through the service layer.** `run_scan()` now dispatches to `scan_all_markets` (sports), `scan_futures_markets` (futures), or `scan_prediction_markets` (prediction) based on the UI selection, and passes `cross_ref` through for Polymarket reference pricing on prediction scans. Invalid market types raise `ValueError` at the boundary. Standalone Polymarket market type removed from `MARKET_TYPES`, `CATEGORIES_BY_TYPE`, `FILTERS_BY_TYPE`, and the sidebar `QUICK_SCANS` — it was UI-only and never reached the service layer. `docs/web-app/LOCAL.md` updated to match. Resolves G1. Files: `webapp/services.py`, `webapp/views/scan_page.py`, `webapp/app.py`, `docs/web-app/LOCAL.md`. |
| Q2 | **Fixed `test_approved_clean_when_no_caps_hit` env-contamination.** Root cause: test read `MAX_BET_SIZE` and `KELLY_FRACTION` from `kalshi_executor` at import time, so developer `.env` overrides (e.g. `MAX_BET_SIZE=15`, `KELLY_FRACTION=1.0`) would cause the 5% edge / $500 bankroll / $1 unit-size case to trip the max-bet cap and return `APPROVED_CAPPED_MAX_BET` instead of `APPROVED`. Fix: monkey-patch both module constants to documented defaults (100.0 / 0.25) for the test's scope, matching the existing pattern in sibling `test_approved_capped_max_bet`. Sizing logic itself was correct. All 213 tests pass. Resolves G2. Files: `tests/test_risk_gates.py`. |
| Q3 | **Doc drift: "8 risk gates" → "11 risk gates".** Updated `docs/SCRIPTS_REFERENCE.md:413`, `docs/setup/AUTOMATION_GUIDE.md:17`, `docs/web-app/LOCAL.md:184` to reflect live gate count post-R1/R3 and cross-link to `CLAUDE.md` §"11 Execution Gates" as the canonical source. Resolves G3. |
| Q4 | **Pages deploy branch fixed: `main` → `master`.** `.github/workflows/deploy.yml` trigger corrected so pushes to the actual default branch republish `.claude/html/` (the "Edge-Radar · Data Flow" static page). **Side effect:** the next push to master will trigger a real Pages deploy — expected and intended. Resolves G4. Files: `.github/workflows/deploy.yml`. |
| Q5 | **Declared `pandas` in `requirements.txt`.** All four webapp view pages (`scan_page.py`, `settle_page.py`, `portfolio_page.py`, `backtest_page.py`) import pandas; it was working only because streamlit pulls it transitively. Promoted to `pandas>=2.1.4` as a first-class runtime dep. Audited for other transitive-only imports — none found in `scripts/` or `webapp/`. Resolves G5. Files: `requirements.txt`. |

##### 2026-04-21 — 14-Day Review Response (R1, R2, R3, R4)

| ID | Item |
|----|------|
| R3 | Gate 4.5 — `MIN_CONFIDENCE` (default `medium`) rejects low-confidence opportunities. Addresses 0W-3L / -105% ROI in two review windows. |
| R1 | Gate 4.6 — NO-side favorite guard: reject NO bets priced below `NO_SIDE_FAVORITE_THRESHOLD` (0.25) unless edge ≥ `NO_SIDE_MIN_EDGE` (0.25) AND `confidence=high`. Plus sizing dampener: NO bets priced below `NO_SIDE_KELLY_PRICE_FLOOR` (0.35) sized at `NO_SIDE_KELLY_MULTIPLIER` (0.5 = half-Kelly). Addresses F1 — all 13 high-edge losers in 14d window were NO-side. +14 regression tests (195 total). |
| R4 | Resting-order janitor — `cancel_stale_resting_orders()` runs at the top of `execute_pipeline()` when `execute=True` AND `DRY_RUN=false`. Cancels resting orders older than `RESTING_ORDER_MAX_HOURS` (default 24) with zero fills. Partial/full fills left to the settler. Addresses F7 — 16% of new orders resting 25-66h with no follow-up. +12 tests (207 total). |
| R2 | Per-sport stdev bump in `SPORT_MARGIN_STDEV` / `SPORT_TOTAL_STDEV` (edge_detector.py). NBA +15% (12.0→13.8 margin, 18.0→20.7 total), NCAAB +10% (11.0→12.1, 16.0→17.6), MLB +15% (3.5→4.025, 3.0→3.45). NHL untouched (+87% ROI, well-calibrated). Direct fix for Brier 0.2646 and the 60-70% favorite-band overconfidence (F2, F3, F4, F5). Supersedes C2. +6 tests (213 total). R12 (re-run calibration at 100 trades) is the attribution check. |

##### 2026-04-18 — Calibration-Driven Tuning

| ID | Item |
|----|------|
| C1 | Soft-cap edge used in Kelly sizing (`trusted_edge()`, `KELLY_EDGE_CAP=0.15`, `KELLY_EDGE_DECAY=0.5`, +6 tests) |
| C3 | Per-sport `MIN_EDGE_THRESHOLD` (NBA=8%, NCAAB=10%, `min_edge_for()` helper, +5 tests) |
| C5 | Series-level dedup — Gate 7, `matchup_key()`, `SERIES_DEDUP_HOURS=48`, +16 tests (177 total passing) |

##### 2026-04-07 — Backtesting, Dashboard Batch 2, Package Structure

| ID | Item |
|----|------|
| W1 | Backtesting framework — equity curve, Sharpe, drawdown, calibration curve, strategy simulation, +32 tests |
| H4 | Package structure — `pyproject.toml` with `pythonpath`, `__init__.py` files, simplified `conftest.py` |
| A1 | Domain package extracted — `app/domain/` with `Opportunity`, `RiskDecision`, `ExecutionPreview`, `ExecutionResult`, +7 tests |
| D5 | Auto-refresh portfolio (`st.fragment(run_every=30s)` + toggle) |
| D7 | Position P&L color coding (W/L/F count + unrealized P&L) |
| D8 | Execution confirmation dialog (`@st.dialog`) |
| D9 | Toast notifications after execution and settlement |
| D11 | Settlement history tab (sortable + CSV export) |
| D14 | CSV export buttons on scan/positions/settlements/report |
| D16 | `streamlit>=1.33.0` added to `requirements.txt` |

##### 2026-04-06 — Dashboard v1.0, Dynamic Stdev, Simplification

| ID | Item |
|----|------|
| U6 | Streamlit dashboard v1.0 — 3 pages (Scan & Execute, Portfolio, Settle & Report), dark theme, favorites, quick-scan |
| D1 | Quick-scan sidebar buttons |
| D2 | Favorite scans |
| D4 | Default unit size $0.50 |
| S5 | Dynamic stdev adjustment — weather severity, rest/B2B applies to spreads, per-home-team weather cache |
| H5 | Simplified scripts & config — removed `DEFAULT_BET_SIZE`, `MIN_CONFIDENCE`, `MAX_POSITION_CONCENTRATION`, merged `MAX_BET_SIZE_*`; -4 env vars, -2 CLI flags, -2 gates. See `archive/SIMPLIFICATION.md`. |
| H1 | Centralize config (resolved by H5 — `config.py` deleted; `kalshi_executor.py` is canonical) |

##### 2026-04-04 — Fill-based Logging, MLB Pitcher Data, Calibration Tooling

| ID | Item |
|----|------|
| X5 | Fill-based trade logging — `filled_contracts`/`filled_cost` vs `requested_*`, `fill_status`, +16 regression tests |
| X6 | Gates 8-9 documented as sizing caps; approval subtypes `APPROVED`, `APPROVED_CAPPED_CONCENTRATION`, `APPROVED_CAPPED_MAX_BET` |
| S1 | Starting pitcher data — ERA / FIP / WHIP / K9 / days-rest, matchup classification, stdev adjustment |
| S2 | Back-to-back / rest days — NBA / NHL detection via ESPN scoreboard, stdev + confidence adjustment |
| W2 | `model_calibration.py` — Brier, calibration curve, dimension breakdowns, cross-tabs, prioritized recommendations |
| W4 | Win-rate analytics by dimension (confidence × category × sport × edge bucket) |

##### 2026-04-02 — Execution Correctness

| ID | Item |
|----|------|
| X1 | Hardcoded Python path fixed (`sys.executable`) |
| X2 | All 9 risk gates enforced in executor; Kelly sizing with unit-size floor |
| X3 | Per-event caps + correlated-bracket dedup (`dedup_correlated_brackets()`) |
| X4 | Startup doctor command (`scripts/doctor.py`) |
| W3 | Kelly Criterion sizing (part of X2) |

##### 2026-04-01 — Display Improvements

| ID | Item |
|----|------|
| D1 | Bet-type column (ML/Spread/Total/Prop) in all output tables |
| D2 | Descriptive Pick column replacing raw YES/NO |

##### 2026-03-23 — Edge Model Improvements

| ID | Item |
|----|------|
| E1 | Normal CDF spread/total model |
| E2 | Closing Line Value tracking |
| E3 | Sharp book weighting (Pinnacle 3×) |
| E4 | Team performance stats (ESPN/NHL/MLB APIs) |
| E5 | Injury / line-disagreement signal |
| E6 | Line movement & sharp-money detection |
| E7 | Weather for outdoor sports (NWS API) |

##### 2026-03-30 to 31 — Project Quality

| ID | Item |
|----|------|
| P1 | Standardize CLI flags |
| P2 | Standardize logging (`setup_logging`) |
| P3 | Consolidate import boilerplate (`.pth`) |
| P4 | Markdown scan reports |
| P5 | Initial test suite (83 tests) |
| P6 | Remove empty `strategies/` |
| P7 | `MAX_BET_SIZE_SPORTS` in `.env.example` |
| P8 | Unify report output format |
| P9 | Unified `scan.py` entry point |
| P10 | Docs cleanup + `docs/scripts/` sub-docs |
| P11 | Pre-commit hooks |
| P12 | Makefile (18 targets) |

---

#### Completed Item Details

<details>
<summary>X1-X4. Execution Correctness (2026-04-02 to 2026-04-04)</summary>

**X1.** Replaced hardcoded `.venv/Scripts/python.exe` in `scan.py` with `sys.executable`. Now works across any environment (CI, WSL, Docker, other machines).

**X2.** Enforced all risk gates that were previously loaded but never checked in `kalshi_executor.py`. The executor now runs 9 gates before every order: daily loss, max open positions, edge threshold, composite score, confidence floor, duplicate ticker, per-event cap, max concentration, max bet size. Position sizing upgraded from flat unit to quarter-Kelly with flat unit as floor. Pipeline tracks approved orders within the batch so gates apply correctly across the run.

**X3.** Per-event caps + correlated-bracket dedup (updated 2026-04-04). `dedup_correlated_brackets()` groups by `(event_key, category)` and keeps only the highest composite score. `MAX_PER_EVENT` default lowered from 3 to 2. New `--max-per-game` CLI flag for session override.

**X4.** Startup doctor command (`scripts/doctor.py`). Validates Python version, venv, credentials (Kalshi key + private key path, Odds API keys), data directories, config values, API connectivity, and pre-commit hooks.

**Breaking change:** `MAX_BET_SIZE` split into `MAX_BET_SIZE_SPORTS` / `MAX_BET_SIZE_PREDICTION` (later re-merged in H5).
</details>

<details>
<summary>X5. Fill-based Trade Logging (2026-04-04)</summary>

Executor previously logged `requested_contracts` / `requested_cost` regardless of fill. Resting/partial orders overstated exposure. Added `filled_contracts` / `filled_cost` fields and `fill_status` enum (`filled`, `partial`, `resting`, `failed`). Settler / risk_check now read fill-based values. 16 regression tests for resting, partial, and zero-fill responses.
</details>

<details>
<summary>X6. Sizing Caps vs Reject Gates (2026-04-04)</summary>

`ARCHITECTURE.md` previously described concentration and max-bet as reject gates, but executor silently downsized. Docs updated to describe gates 8-9 as sizing caps. New approval subtypes `APPROVED`, `APPROVED_CAPPED_CONCENTRATION`, `APPROVED_CAPPED_MAX_BET` in trade log distinguish clean from force-capped.
</details>

<details>
<summary>E1. Normal CDF Spread/Total Model (2026-03-23)</summary>

Replaced linear `+3% per point` with `scipy.stats.norm` bell curve. Infers expected margin from book spread + implied probability, then `P(margin > strike)` on the bell curve. Sport-specific stdevs: NBA (12), NCAAB (11), NFL (13.5), MLB (3.5), NHL (2.5), soccer (1.8). Separate stdevs for totals.

**Context:** live trading 2026-03-22 had 1W-11L on NCAAB spreads at estimated 33% edge → realized -88% ROI. Linear model systematically overestimated edge on alternate spreads.
</details>

<details>
<summary>E2-E7. Edge Model Signals (2026-03-23)</summary>

- **E2:** CLV — settler captures `last_price` from Kalshi at settlement; average CLV + beat-the-close rate in performance report.
- **E3:** Sharp book weighting — 21-book `BOOK_WEIGHTS` map (Pinnacle/Circa 3×, DraftKings/FanDuel/BetMGM 0.7×), weighted-median consensus.
- **E4:** Team stats — `team_stats.py`, 6 sports from free APIs (ESPN NBA/NCAAB/NFL/NCAAF, NHL Stats, MLB Stats). Win%, run/goal diff, L10, streak.
- **E5:** Injury proxy — spread disagreement >4pts across books triggers confidence downgrade (ESPN injury endpoints were unreliable).
- **E6:** Line movement — `line_movement.py` uses ESPN scoreboard open-vs-close; detects reverse line movement + sharp total movement.
- **E7:** Weather — `sports_weather.py` NWS hourly forecast for 31 NFL + 30 MLB venues. Wind >15mph, rain >40%, cold <32F (NFL) / <45F (MLB).
</details>

<details>
<summary>D1-D2. Display Improvements (2026-04-01)</summary>

Type column (ML/Spread/Total/Prop) across all 7 output tables. Descriptive Pick column replacing raw YES/NO ("Over 220.5", "Spurs -4.5", "Heat win"). `bet_type_from_ticker()` + `format_pick_label()` in `ticker_display.py`. Kalshi team abbreviation aliases (SAS, GSW, NOP, etc.).
</details>

<details>
<summary>P1-P12. Project Quality (2026-03-30 to 31)</summary>

Standardized CLI flags (P1), logging (P2), imports via .pth (P3), markdown reports (P4), 83-test suite (P5), removed empty `strategies/` (P6), `.env.example` (P7), unified report format (P8), `scan.py` entry point (P9), docs cleanup + `docs/scripts/` (P10), pre-commit hooks (P11), Makefile 18 targets (P12).
</details>
