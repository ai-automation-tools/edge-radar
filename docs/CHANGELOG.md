# Changelog

---

## 2026-11-18 -- Gate 1 counts an Eastern day (ER-16)

- **Gate 1's "today" was UTC's calendar day**, which rolls over at 7-8 pm ET, in the middle of the
  evening slate: losses closed before and after it sat on two different `MAX_DAILY_LOSS` budgets.
  `get_today_pnl()` now converts each `closed_at` to `DAILY_LOSS_TZ` (default `America/New_York`,
  owner's choice over a rolling 24 h) and sums the zone's calendar day. Rows closed at 23:30Z and
  00:30Z both count toward an 01:00Z check.
- A naive stamp is read as UTC; one that does not parse still counts if it starts with today's date,
  so a malformed row cannot hide a loss. A bad zone name fails config validation.
- Same function feeds the executor status line and `risk_check.py`, so all three agree. The
  Daily-Summary's rolling 24 h "yesterday" is a report window, not the gate, and is unchanged.
- Tests: `tests/test_daily_loss_window.py`.

---

## 2026-11-18 -- Security re-lock: six packages

GitHub listed 80 open Dependabot alerts on master (7 critical), all from six packages. Python is
out of Dependabot's version updates (its re-locks drop `--universal`), so they are bumped here with
the repo's own `make lock` command plus `--upgrade-package`; nothing else moved.

- Runtime (`requirements.txt`): certifi 2026.10.23, cryptography 50.0.2 (was 49), filelock 4.2.12,
  urllib3 2.8.0.
- Dev only (`requirements-dev.txt`): the same four, plus pillow 13.0.0 and black 26.10.1.
- Tested in a fresh venv from the new lock: full suite passes. `cryptography` signs every Kalshi
  request, so `tests/test_kalshi_signing.py` now checks an RSA-PSS signature round-trips.
- Supersedes Dependabot #389 (filelock).

---

## 2026-11-18 -- Smaller agent docs (ER-47)

Every agent session loaded ~30k tokens of AGENTS.md and the `/edge-radar` skill before doing anything,
and the changelog had grown to 819 KB. Nothing was deleted; it moved.

- **`AGENTS.md`** 61 KB -> under 20 KB. Each rule is now one or two lines with its tag (*F1*, *S4*, ...).
  The evidence paragraphs moved word for word to the new **`docs/RULES-RATIONALE.md`**, along with the
  fully commented env block and the live-override history. The env block in AGENTS.md keeps the main
  knobs; `.env.example` lists every one. The project tree now matches the repo (no `app/domain/`, no
  `.claude/agents/`).
- **`skills/edge-radar/SKILL.md`** 57 KB -> under 15 KB. The filter list, the long risk-limit notes, the
  operations guide and the internals moved verbatim to `skills/edge-radar/references/`, which the core
  file indexes.
- **`docs/CHANGELOG.md`** 819 KB -> about 83 KB. Entries before 2026-10 moved to
  `docs/changelog/<YYYY-MM>.md`, and the pre-2026-09-29 roadmap to its own file there; a dated citation
  like *CHANGELOG 2026-08-26* is in that month's file. Relative links gained a `../`.
- **Guard:** `tests/test_doc_size.py` fails if any of the three grows past its limit, and the link check
  skips the archive the way it already skipped the changelog.

---

## 2026-11-18 -- Ops health in the Daily-Summary (ER-50)

- **New** `scripts/shared/ops_health.py`, read-only. It lists every scheduled task under an
  `Edge-Radar` Task Scheduler folder with its state, last run, last result and next run, then adds
  the newest settlement, the newest ledger backup (found through the Reconcile task's
  `backup_ledger.py --dest`), the newest report per scheduler preset, and the size of `data/` and `logs/`.
  - A disabled or failing execute task is FAIL. Any other disabled task, a task that never ran, one
    that missed its start, a settlement older than 3 days or a backup older than 2 days is WARN; a
    backup older than 7 days or missing is FAIL.
- **Daily-Summary** opens with the table under a `**Status: OK|WARN|FAIL**` line, which the email
  renderer already turns into the subject and banner colour, so a broken execute task reads
  `Edge-Radar | Daily Summary | FAIL` in the inbox. `--no-ops` skips it; an error building it becomes
  a WARN line instead of a lost summary.
- **`doctor.py --ops`** prints the same table and exits 1 on any FAIL.
- Tests: `tests/test_ops_health.py`, including the email subject for a disabled execute task.

---

## 2026-11-18 -- Keep local images ignored

- **`.gitignore`** ignores `.claude/images/` again. ER-51 removed the tracked files there and the old
  `.claude/images/screenshots/` rule with them, which left a checkout's local screenshots showing as
  untracked files that `git add -A` would commit.

---

## 2026-11-18 -- Stale branches (ER-49)

- **GitHub** Deleted 13 stale remote branches (every PR merged or abandoned; the head SHAs are in
  the audit notes if one is ever wanted back) and turned on "delete branch on merge". The remote
  keeps `master`, `mike_desktop`, `gh-pages` and open PR heads.

---

## 2026-11-18 -- Skill links and pinned models (ER-48)

- **Skills** `.gitignore` ignores `.claude/skills/` as a whole, and `link_skills.ps1` links every
  `skills/*` folder with a `SKILL.md`, so a new skill needs no edit in either. The script re-points a
  junction whose target differs only in case (the clones made before the `Edge-Radar` to
  `edge-radar` rename) and removes an old junction without following it into the skill folder.
- **Models** `betting_audit.py --analyze` runs on `opus` and `integration_drift.py` on `sonnet`;
  `drift_autofix.py` already named `opus`. `tests/test_agent_cli.py` fails on a `run_agent` call
  without a model. The three skills pin `model:` in their front matter. The table is in
  `docs/setup/AUTOMATION_GUIDE.md`.

---

## 2026-11-18 -- Repo hygiene (ER-51)

- **Removed** `.claude/backup/` (old site HTML, 912 KB), `.claude/images/` (unreferenced legacy
  diagrams, logos and a screenshot, 11 MB) and `docs/longshot/fork-evidence-window/` (the retired
  fork's scan reports). All of it stays in git history.
- **Added** `CONTRIBUTING.md` (setup, tests, the money path, the diagram re-pin) and
  `.github/CODEOWNERS` over `scripts/kalshi`, `scripts/shared`, `scripts/schedulers`, `app`,
  `.env.example` and `.github`.
- **Makefile** Bare `make` prints the help instead of running `scan-mlb`, which hit the network.
- **Dev container** Python 3.12, `make install` and `pre-commit install`, and a `.env` copied from
  `.env.example` (DRY_RUN=true); it no longer looks for a `packages.txt` that never existed.
- Kept `.env.longshot.example`: the profile mechanism is still in the code and it is the only worked
  example of an overlay. The ROADMAP's release-gate lines were already in place.

---

## 2026-11-18 -- De-vig docstrings and a narrower order preview (ER-42, ER-52)

- **De-vig** `devig_two_way()` said "power method"; it is proportional, and now says so.
  `devig_nway()` notes that proportional de-vig leaves longshot fair values high. The switch to
  power or Shin de-vig stays open as ROADMAP B5, to be A/B'd in the shadow book first.
- **Order preview** `preview_table()` fits a 100-column log with one line per order: no row rules,
  the bet type folded into the Bet column, and long Bet and Pick labels cut with an ellipsis instead
  of wrapping. `tests/test_preview_table.py` renders it at 100 columns.

---

## 2026-11-18 -- Dead and fragile code (ER-45)

- **Removed** `app/domain/`, a re-export layer only its own tests imported, and the readers for
  `data/watchlists/kalshi_opportunities.json` and `prediction_opportunities.json`, which nothing has
  written for months: `kalshi_executor.py run --from-file` and `risk_check.py --report watchlist`
  (and the watchlist section of its saved dashboard). Docs that said `--save` writes those files now
  say it writes a markdown report.
- **Config** `get_config()` loads the repo-root `.env` once per process before its first read, so a
  script that imports config before calling `load_dotenv()` still gets its settings.
- **Caches** The scan cache and odds cache write through a temp file and `os.replace`
  (`trade_log.write_text_atomic`), like the trade log, so a reader never sees half a file.
- **Trade-log lock** A 30 s lock timeout now logs at ERROR, not WARNING: it means another process
  hung holding the lock and the write may lose its update.

---

## 2026-11-18 -- Fee rounding and segment keys (ER-36, ER-39)

- **Fees** `taker_fee()` rounds the cent amount to 6 places before rounding up, so float noise no
  longer adds a cent to an exact-cent fee (4 contracts at 50c is $0.07, not $0.08; 81 of the 19,800
  price and size pairs were a cent high). `tests/test_fees.py` checks every pair in exact arithmetic.
- **Gate 2b** Open positions, resting orders and new bets now share one segment key,
  `segment_key(ticker)`: the sport, else `unknown`. A new bet on a sport-less ticker used to be keyed
  by its scanner category (`futures`), while the positions it should count against sat in `unknown`,
  so `MAX_SEGMENT_EXPOSURE_PCT` never saw them together.
- **Diagram** Re-pinned to the new executor: every cited executor range moved down 6 lines, same code.

---

## 2026-11-18 -- Homepage and diagram page in the org house style (ER-31)

- **Site** The homepage stylesheet uses only tokens below its two token blocks (the GitHub button,
  black in both themes, is the one exception), with the shared web-house-style names. The light theme
  swaps token values instead of overriding 40 rules, and the series colours (`--c`) in markup and
  script are token references, so they take their -700 shades in light. Lighthouse accessibility
  stays at 100.
  - The top-bar mark is the app icon (`site/favicon.svg`), not a letter tile.
  - The theme switch is the last control before the phone menu; the nav shows from 760px and the
    Jump to button from 900px.
  - The footer's GitHub link is gone; the source bar and the hero button are the repo links.
  - The diagram picture links to the interactive page instead of loading it into a frame that
    trapped scrolling.
- **Diagram page** `site/diagram/betting-data-flow.html` has the favicon, a source bar with
  "← Edge-Radar" and View source, a main landmark, the house ground and type, and the homepage's
  theme choice (dark by default, not the OS setting). The build script writes that copy and
  `--check` compares against it.
- **Tests** `tests/test_site.py` checks the token rule, the mark, the control order, the repo links
  and the diagram page's chrome.

---

## 2026-11-18 -- Homepage performance (ER-32)

- **Site** Measured with Chrome DevTools traces on Slow 4G: desktop layout shift is 0.008 (the audit
  measured 0.20) and phone LCP is 1.34 s at 4x CPU slowdown (2.39 s before).
  - The Google Fonts stylesheet no longer blocks the first paint. Until Inter arrives the system font
    stands in, scaled to Inter's x-height with `font-size-adjust`, so the swap barely moves text.
  - Text widths use `em` instead of `ch`; `ch` follows whichever font is showing, so the hero's fine
    print gained a line in the fallback and the hero re-centred on the swap.
  - On phones the three hero buttons stack; the row fitted by 2px in Inter and broke in the fallback.
  - The data-flow diagram shows its 240 KB picture first. The 845 KB interactive page loads when
    the reader asks for it, takes focus, and still follows the page theme.
- **Tests** `tests/test_site.py` checks there is no render-blocking external CSS, no `ch` widths and
  a poster-first diagram.

---

## 2026-11-18 -- Homepage accessibility (ER-30)

- **Site** Lighthouse accessibility is 100 on desktop, mobile and the light theme (it was 91, 88, 88):
  - The command palette is a native modal `<dialog>`: Tab stays inside, Esc and a click outside
    close it, focus returns to where it was. The input is a combobox over a grouped listbox, and the
    shortcut reads Ctrl K, or ⌘K on Apple devices.
  - The Quick start tabs form a real tablist (arrow keys, Home and End) with a tabpanel; the shell
    switch and Copy sit outside it and get their own row on phones, where they were off-screen.
  - Contrast: `--fg-4` is #7e7e87 (5.0:1) and no text uses `--fg-5`, here and on the ops deck.
    N/A gate chips use a dashed border instead of 55% opacity. In-text links are underlined.
  - Focus is visible on the gate-lab sliders, the gate search and the theme switch.
  - A Pause motion button stops the radar sweep, the pulsing dots, the connector and the cursor,
    and remembers the choice; the radar also stops while off-screen. The page no longer overwrites
    the diagram's own motion setting on every load.
  - Gate cards are a heading with a disclosure button, and their hidden detail is `inert`. The
    phone-only GitHub button with no name is gone; "View source" is a 24px target (34px on phones).
- **Tests** `tests/test_site.py` pins the contrast tokens, the dialog, the tablist and the motion control.

---

## 2026-11-18 -- Retire dead AI tooling (ER-26)

- **Removed** the `footballbin-predictions`, `kalshi-markets`, `document-writer` and
  `market-mechanics-betting` skills under `.claude/skills/`, the `kalshi-bettor` and
  `documentation-expert` agents, and the AGENTS.md roster of five agents that were never defined.
  `.claude/agents/` is no longer git-ignored.
- **Moved** the Kelly, scoring-rule and betting-theory notes to
  `skills/betting-logic-review/references/`, linked from that skill.
- **Renamed** `/repo-review` to `/edge-radar-repo-review` (it collided with a user-scope skill).
- **Docs** `docs/setup/mcp-servers.md` is now half a page: no MCP server is needed, and none may
  place orders. The edge-radar skill no longer says NFL is off (it runs a pilot floor). `CLAUDE.md`
  and `/sync-docs` use Claude Code's project auto-memory instead of two retired memory folders.

---

## 2026-11-18 -- Docs match the code (ER-29)

- **Docs** every risk-gate count says 21 (ARCHITECTURE said 18, the executor doc 16, the skill fifteen),
  and the ARCHITECTURE and executor gate tables gain the missing 3.05, 3.55 and 6b rows. Sportsbook
  claims now say nine US books plus Pinnacle on live runs (`BOOK_WEIGHTS`), not 12 with Circa. The
  README's docs link, the `cd edge-radar` quick start (README and site), the skill's Automation Guide
  link, and two stale AGENTS.md lines (positions files, SQLite) are fixed.
- **Config** `.env.example` documents `MAX_EDGE`, `EDGE_RADAR_PROFILE` and the per-category
  `MIN_EDGE_THRESHOLD_<SPORT>_<CATEGORY>` floors.
- **Tests** new `tests/test_doc_accuracy.py`: relative links resolve, gate counts and tables match
  AGENTS.md, sportsbook claims match `BOOK_WEIGHTS`, and every key `app/config.py` reads is in
  `.env.example`.

---

## 2026-11-18 -- logs/ stays bounded (ER-28)

- **Ops** new `scripts/shared/prune_logs.py`, run by `maintenance\reconcile.bat` after the nightly
  reconcile: deletes `<name>_<date>.log` files more than 90 days old and cuts fixed-name logs over 5 MB
  to their newest 1 MB at a line break. The wrapper still exits with the reconcile's code.
- **Tests** `tests/test_prune_logs.py`.

---

## 2026-11-18 -- Security headers on the public site (ER-23)

- **Site** new `site/vercel.json`: a Content-Security-Policy limited to the page's own origin, the org
  consent script and Google Fonts, with `frame-ancestors 'self'` and `object-src 'none'`; `nosniff`,
  `X-Frame-Options: SAMEORIGIN`, `Referrer-Policy` and `Permissions-Policy` on every path; the favicon
  and the betting diagram cache for a day instead of revalidating on every load.
- **Tests** `tests/test_site.py` checks the headers and fails when the page loads a script or
  stylesheet from an origin the CSP doesn't allow.

---

## 2026-11-17 -- Roadmap catches up with the audit fixes

- **Docs** `docs/ROADMAP.md` now lists every audit item merged so far, including ER-18, ER-20, ER-21,
  ER-27 and the P3 money-path batch, which shipped without their own roadmap lines, and ends the audit
  section with what is still open.

---

## 2026-11-17 -- Report emails answer "did it trade?" from the inbox (ER-33)

- **Email** Subjects carry the outcome and the date:
  `Edge-Radar | Same-Day | LIVE · 2 placed · 1 failed · $2.08 | Mon Nov 16`. The old fixed subjects
  (`Edge-Radar | Same Day Execution Report`) threaded every day's report into one Gmail conversation, and the
  ER-12 mode line had no cost. Placed cost on a live run, sized cost otherwise. Reports with a
  `**Status: X**` line show X; a failed run shows its reason after `[FAILED]`. The label is short per preset
  (`Same-Day`, `Midday`, `Next-Day`, `Drift Check`, ...).
- **Email** A three-cell banner opens every email (mode, orders, cost; or report, status, time), coloured
  green for a live run that placed orders, amber when any order failed or was blocked or a report says WARN,
  red for a failed run, grey otherwise. Its text is also the preheader, the line an inbox shows after the
  subject, and the first line of the plain-text part.
- **Email** Phones: tables wider than six columns (the 11-column Orders table) get a stacked copy, one card
  per row, that a media query swaps in below 600px; checked at 390px with no sideways scroll. Clients that
  drop `<style>` keep the table, as before.
- **Reports** Scan and execution reports stamp times as `08:05 PM UTC · 12:05 PM PT · 03:05 PM ET`
  (`report_writer.time_line`), as does the email footer. Counts are pluralised ("1 order", "1 opportunity").
  The footer text is `#6b7280` (4.8:1), up from `#888` (3.5:1).

---

## 2026-11-17 -- One gate list for every order path (ER-19)

- **Risk** The reject gates were written out three times: in `size_order` (fresh scan), in
  `preflight_gate_status` (the scan table's Gate column) and in the `--pick`/`--ticker` cache
  replay. The copies had drifted, which is how a replay once skipped Gates 2 and 4.8 (ER-03). They
  are now one ordered list, `GATES` in `kalshi_executor.py`, run by all three through
  `first_rejection()`. A new gate goes in once.
- **Risk** A replay now runs every gate against current state and config, not a subset: a row whose
  edge falls under a floor raised since the preview, a sport switched off, or a $0 balance is
  dropped. Series dedup on replay now honours a per-sport `SERIES_DEDUP_HOURS_<SPORT>=0`, as the
  fresh path always did. Drop messages use the same reason text as `size_order`, with the gate id.
- **Unchanged** Fresh-scan verdicts and sizes: 40,000 randomized opportunities and portfolio states
  gave identical results before and after. Gate ids and order are as before; the old docstring
  listed them out of order and called the max-bet cap "Gate 7", which is series dedup.
- **Tests** The suite no longer reads the operator's `.env`: conftest sets
  `PYTHON_DOTENV_DISABLED=1` before anything imports, so every test runs on the code's defaults,
  and the four "ignore the operator's .env" fixtures are gone. `tests/test_gate_list.py` pins one
  added gate reaching all three paths, the replay's static gates, and the `.env` switch.
- **Not done** A frozen `RiskConfig` passed into `size_order`. About 180 gate tests set the module
  globals directly, so it means rewriting them; the hermetic suite already removes the failure it
  was for (tests that passed or failed depending on one machine's `.env`).

---

## 2026-11-17 -- Scheduled wrappers and the email sender are tracked (ER-27)

- **Ops** The `.bat` wrappers the scheduled tasks run, five of which place orders, were gitignored,
  so a change to a live task's flags left no history. The 15 the tasks and the installer use, plus
  `run-hidden.vbs` and its guard, are now tracked where the tasks already point. Old and one-off
  wrappers stay ignored. `.gitattributes` gives `.bat` files CRLF.
- **Fix** The execute wrappers' headers said "Unit size $0.50" and "9 risk gates" while the
  command ran `--unit-size 1` against 21. The headers now point at the command line, which is the
  only copy of the flags.
- **Email** The one send path, `scripts/custom/Python/send_report_email.py`, was untracked, carried
  a personal default recipient and imported a helper from outside the repo. Its replacement,
  `scripts/schedulers/automation/send_report_email.py`, calls Resend's REST API directly and reads
  `NOTIFY_EMAIL`, `RESEND_FROM`, `RESEND_REPLY_TO` and `RESEND_API_KEY` through
  `app.config.EmailConfig`, with no defaults: an unset recipient or sender fails the send.
  `--check` probes the key and domain without sending. `render_report_email.py` uses it.
- **Tests** `tests/test_scheduler_wrappers.py` checks the wrappers are tracked, use `%~dp0`, carry
  no drive paths and are CRLF, and covers the sender. `test_cronsole_registry`'s flag comparison
  used to skip without the `.bat` files; it now runs everywhere and stops at the ER-07 log
  redirect, which had broken it on the owner's machine.

---

## 2026-11-17 -- Dependabot no longer bumps the Python locks (ER-20 follow-up)

- **Fix** ER-20 moved Python updates to Dependabot's `uv` ecosystem. Its first PR (#389) re-locked
  without `--universal` and the runtime constraint: it dropped the Windows-only `tzdata` and
  `colorama` and pinned numpy/scipy to their 3.11 releases on every Python. The Python block is
  gone; bump with `make lock`. Actions updates and security alerts are unchanged.

---

## 2026-11-17 -- Money-path hardening (ER-35, 37, 38, 40, 41, 43, 44, 46)

- **ER-46** Demo detection is an exact host match (`demo-api.kalshi.co`) instead of a substring
  test on the base URL; any other URL is treated as live.
- **ER-43** Sizing with a balance of $0 or less (or a failed read) still bought one contract,
  because the bankroll cap rounds up to 1 and the Hard Stop skipped itself. A new `no_bankroll`
  rejection runs right after Gate 1. `get_balance_dollars` reads the venue's `*_dollars` fields
  first; `settlement_revenue_dollars` reads `None` as $0 and the string `"56"` as 56 cents, not
  $56; the fill helpers treat a null field as missing instead of crashing.
- **ER-44** A GET that gets no response, a 429 or a 5xx is retried twice with jittered backoff.
  POST and DELETE are never retried (a lost order response is ER-13's job).
- **ER-40** `get_positions` and `get_orders` follow `cursor` to the last page (capped at 50) when
  called without one, so every caller sees the whole book instead of the first 50-200 rows.
- **ER-37** Gate 7 (series dedup) counted failed placements and dry-run rows as bets and blocked
  matchups with no money on them. It now skips both.
- **ER-41** Shard auto-funding moved exactly the order cost; it now moves cost + taker fee + 1
  cent, so the order isn't refused for the fee after the transfer.
- **ER-35** The scan-cache fingerprint now carries the profile and subaccount, so a preview
  can't be replayed with `--pick` into another wallet. The first replay after this update
  rescans, because the old cache has no wallet keys.
- **ER-38** `risk_check --gate` summed today's P&L across every profile; it now uses this
  profile's rows, like the executor's Gate 1.
- `tests/test_money_path_p3.py` (24 tests); `test_shard_funding` now expects the fee headroom.

---

## 2026-11-17 -- Void settlements in the risk and calibration reports (ER-15 follow-up)

- **Fix** ER-15 marked scalar and voided settlements `won=None`, but two reports still counted them
  as losses. `risk_check.py`'s dashboard now shows them as `void`, adds them to the record line
  (`3W - 2L (60%) + 1 void`) and leaves them out of every win rate; their P&L (refund minus fees)
  still counts. `model_calibration.py` skips them, since there is no yes/no outcome to score a
  probability against.
- `tests/test_void_settlement_reports.py` covers both.

---

## 2026-11-17 -- Hashed dependency locks, Actions pinned by SHA (ER-20)

- **Supply chain** `requirements.txt` held floor pins (`>=`), so every install could pull a different
  version. It is now a hashed lock built from `requirements.in` with `uv pip compile --universal`:
  exact versions, and pip refuses a file whose hash doesn't match. Versions match the live venv on
  Python 3.12; numpy and scipy fork to their last 3.11 releases on 3.11. Tests and dev tools live in
  `requirements-dev.in` / `requirements-dev.txt`, constrained to the same runtime pins. Re-lock with
  `make lock`.
- **Deps** Declared what the code imports: `numpy` (edge detector, backtests) and, on Windows,
  `tzdata`. `zoneinfo` has no system time-zone data there; it only worked because pandas pulled
  `tzdata` in. Dropped `pandas`, `pytest-asyncio` and `pytest-mock` (nothing uses them) and the block
  of commented "planned" packages. `pillow` (for `make_favicon.py`) is a dev dependency.
- **CI** Installs `--require-hashes -r requirements-dev.txt`. Every `uses:` in the three workflows
  is pinned to a full commit SHA with the version in a comment; Dependabot bumps both.
- **Dependabot** The Python updates use the `uv` ecosystem, which re-runs the command recorded in
  each lock's header, so hashes stay in step with pins.
- **Docs** `SETUP_GUIDE.md`, `AGENTS.md` and `UPSTREAMS.md` describe the locks. The README still
  installs `requirements.txt`, which is all a user needs.

---

## 2026-11-17 -- CI runs lint, secret scan and Python 3.11 (ER-21)

- **CI** Only pytest on 3.12 ran, so nothing stopped a PR that skipped the local hooks. CI now
  runs the tests on 3.11 and 3.12, and a `lint` job runs the pre-commit hooks (black, flake8,
  detect-secrets, the `os.getenv` guard) on the files the PR changed. About 45 older files
  aren't black-clean yet and get formatted when next touched. The required `ci` check is now a
  gate job that passes only when the others do, so branch protection didn't change.
- **Style** `model_calibration.py`, `risk_check.py` and `prediction_scanner.py` are now black and
  flake8 clean (unused imports, f-strings without placeholders, two dead variables, long lines
  split). The parsed code is unchanged apart from the removed imports and dead variables. With
  that they get the ER-18 path block, so every entry point now runs in a fresh clone.
- **Config** `pyproject.toml` set black to 120 columns while the hook used 100; both are 100.

---

## 2026-11-17 -- Scripts run in a fresh clone (ER-18)

- **Fix** 18 entry points (the settler, futures scanner, executor, edge detector, backtests and
  others) only imported because of `.venv/Lib/site-packages/edge_radar.pth`, which no setup step
  creates. In a fresh clone they died with `ModuleNotFoundError`. Each now adds `scripts/shared`
  to `sys.path` from its own location and imports `paths`, which adds the rest.
- **Style** Five of those files predated black/flake8; they were formatted in a separate commit
  with no logic change. Three more (`model_calibration.py`, `risk_check.py`,
  `prediction_scanner.py`) need a larger lint cleanup and are left for ER-21.
- **Docs** `SETUP_GUIDE.md` and `AGENTS.md` no longer say imports depend on the `.pth`.
- `tests/test_fresh_clone_imports.py` loads every script with a `__main__` block in a child
  interpreter that skips `.pth` files, and fails if one breaks or if a known-broken one is fixed
  without being taken off the list.

---

## 2026-11-17 -- Execute prompts wait for go (ER-25)

- **Safety** Nine prompts under `prompts/` place orders. Most ran a fresh `scan.py ... --execute`
  as their first command, which places orders immediately, even where the text said "wait for my
  confirmation"; `multi-sport-execute.md` bet up to ten rows nobody had seen. Each now ends with
  one "Placing orders" block: run the sizing preview (no `--execute`), wait for **go**, then place
  exactly the chosen rows. Sports use `--execute --pick '<rows>'`, which replays the cached
  preview; futures and predictions use `--execute --ticker`, because those scanners don't cache
  and a fresh scan can renumber rows.
- **Docs** `prompts/README.md` described the old promise; it now describes the rule.
- `tests/test_prompts.py` fails on any `scripts/scan.py ... --execute` line without `--pick` or
  `--ticker`, and on any order-placing prompt that doesn't wait for **go**.

---

## 2026-11-17 -- Risk and eligibility notice (ER-10)

- **Docs** The README and the public site carried only "Not financial advice". Both now have a
  "Risk and eligibility" block: you can lose the whole stake, quoted results are one operator's
  small sample and not a forecast, Kalshi's age and location rules are the user's responsibility,
  US help at 1-800-GAMBLER, and no affiliation with Kalshi or The Odds API. On the site it sits
  in the footer, linked from the hero.
- **UX** The site's disclaimer text used `--fg-4` / `--fg-5` (4.19:1 and 2.62:1 on the dark
  background). It now uses `--fg-3`, which clears 4.5:1 in both themes.
- **Docs** The two gate cards that quote ROI from the ~380-bet sample now say so.
- `tests/test_site.py` fails if the block goes missing from either page or the contrast drops.

---

## 2026-11-17 -- Idempotent orders, resting-aware gates, one execute run per profile (ER-13)

- **Fix** Orders went out without a `client_order_id`, so an order whose response was lost (a
  timeout after Kalshi accepted it) was written off as "placement UNKNOWN" and never reconciled.
  Every POST now carries one, and on a transport error the executor asks `get_orders` for it: found
  means it is booked like any accepted order; not found keeps the UNKNOWN row, which now names the
  id.
- **Fix** Gate 5 (duplicate ticker) and Gate 6 (per-event count) read positions only, and a resting
  zero-fill order is not a position, so a second order could go onto the same market before the
  first filled. Resting orders with a logged side now count for both.
- **Fix** Two overlapping execute runs each read positions before either placed, so both passed
  Gates 5, 6 and 2b on the same state. An execute run now holds `.execute_<profile>.lock` (next to
  the trade log) from state gathering through placement; a second run waits up to 15 minutes, then
  raises `ExecuteRunBusy` (a scheduled run emails `[FAILED]`). Previews don't take it.
- **Not done:** a pending ledger row written before the POST, which would also cover a process that
  dies mid-request.

---

## 2026-11-17 -- Void and scalar settlements (ER-15)

- **Fix** `calculate_pnl` paid $1.00 on a matching yes/no and $0 on anything else, so a void on a
  $2.00 stake booked -$2.07 and a scalar settlement lost the whole stake. Now `scalar` pays the
  settlement's `value` per YES contract (NO gets the rest; the market-status fallback carries
  `settlement_value_dollars`), and any other result is booked as a refund with a warning.
- **Fix** Those rows get `won: None`. `calibration_study` and the daily summary's Brier skip them;
  the settler report shows `-` instead of W/L. `model_calibration.py` and `risk_check.py` still read
  `None` as a loss: both predate black/flake8 and any edit reformats all of them.
- The one existing scalar row (July, booked from the API's real revenue) is untouched.

---

## 2026-11-17 -- LIVE / DRY RUN labels and placed-not-requested reports (ER-12)

- **Fix** Execution reports and emails listed every order the run *meant* to place, even when the
  eligibility preflight blocked all of them or the venue rejected some. Each `SizedOrder` now
  carries an `outcome` (placed, failed, blocked, not attempted, dry run, preview), set where it
  happens; the report gets a Status column and a placed-cost line, and the console summary counts
  outcomes instead of "Orders placed: N".
- **UX** `mode_banner()` gives one label for the run: `LIVE · REAL MONEY · PROD`, `DRY RUN · nothing
  sent`, `DEMO · paper orders`, or `PREVIEW · …`. The preview used to say "DRY RUN" even with live
  trading on, and a live run said only "EXECUTING". It titles the console table, opens the
  execution report (`**LIVE · REAL MONEY · PROD** · 0 placed · 3 blocked`), and
  `render_report_email.py` appends that line to the subject.
- **UX** The scan report's in-play marker says `in play` instead of `LIVE`.

---

## 2026-11-17 -- Telegram bot removed (ER-17)

- **Security** `scripts/schedulers/automation/telegram_bot.py` could flip `DRY_RUN` in `.env` from
  one chat message, authorised on chat id only. It had no scheduled task and had not run since
  April, so it is deleted rather than hardened. `TelegramCredentials` in `app/config.py`, the
  `TELEGRAM_*` lines in `.env.example` and its `docs/UPSTREAMS.md` row go with it. No tracked
  code writes `DRY_RUN` to `.env` now; halting is `data/KILL` or the ops-deck commands (ER-11).

---

## 2026-11-17 -- `--budget` percent parsing (ER-14)

- **Fix** `parse_budget_arg` stripped the `%` before its range check, so `--budget 1%` and
  `--budget 1` meant 100% of bankroll and `0.5%` meant 50%. A trailing `%` now always means
  percent; a bare `1` is refused (100% or 1%?); zero, negative, non-numeric and over-100%
  values are refused. Every scheduled run passes `12%` or `10%`, which parse as before.
- **Fix** `kalshi_executor.py run` had its own copy of the old parser; it now calls the shared one.
- **Docs** The `--budget` help texts said a bare `15` meant $15. The code has always read it as
  15%; the executor, sports and futures help now say so (dollars only above 100).
  `prediction_scanner.py` still has the old wording: the file predates black/flake8 and any
  edit reformats all of it.

---

## 2026-11-17 -- Report emails escape HTML (ER-22)

- **Security** `render_report_email.py` used markdown-it's `commonmark` preset, which passes raw
  HTML through. Report text includes Kalshi market titles and model output, so a tag in either
  rendered in the email. It now escapes HTML (`html=False`).
- **Fix** Side effect: placeholders such as `<TN>` and `<league>` in the drift and betting-audit
  reports were swallowed as unknown tags and missing from the emails. They now show as text.

---

## 2026-11-17 -- Drift auto-fix contained (ER-04)

- **Security** The daily drift auto-fix runs agent-written code before any review. Hardened:
  - `kalshi_client.py` removed from the paths a fix may touch.
  - The fix session reads only inside its worktree (`Read(./**)` etc.). A bare `Read`/`Grep`
    rule approved reads anywhere; checked against the CLI before the change.
  - The fix prompt gets the probe report and JSON, copied into the worktree, never the analysis
    section (that session has WebFetch/WebSearch).
  - The worktree's tests and probe run with an allowlisted environment: no `.env`, no keys or
    tokens, `DRY_RUN=true`.
  - The public commit and draft PR carry a diff stat instead of the session's summary, which
    stays in the owner's email.
- **Change** `integration_drift.py` reads markets with an unsigned `GET /markets` (`PublicMarkets`)
  instead of a signed `KalshiClient`, in the daily run too. Same data; no credentials needed.
  Verified: an in-tree probe with the scrubbed environment returned OK on all 40 series.
- **Test** `tests/test_integration_drift.py`: allowlist rejects `kalshi_client.py`; no credentials in
  the worktree's environment; a planted script run by `--in-tree` sees no `KALSHI_API_KEY`;
  fix-session reads are scoped; the probe sends no auth headers.

---

## 2026-11-17 -- Unattended agent sessions need an allowlist (ER-09)

- **Fix** AI-02/SEC-14: the weekly betting audit's analysis pass shelled `claude -p` with only
  `--allowedTools Read,Grep,Glob`. That pre-approves those tools but doesn't restrict the session:
  anything the user's settings allowed still ran, unattended, in the live checkout. It now goes
  through `agent_cli.run_agent`, where only the listed tools exist.
- **Fix** AI-03: `agent_cli.agent_command` fell back to `--dangerously-skip-permissions` when a
  caller passed no allowlist. It now raises `ValueError` unless the caller passes `unrestricted=True`
  by name. No tracked caller does.
- **Test** `tests/test_agent_cli.py` fails if any tracked script other than `agent_cli.py` builds a
  `claude` argv.

---

## 2026-11-17 -- Nightly ledger backup (ER-08)

- **New** `scripts/shared/backup_ledger.py --dest <folder>`: zips `kalshi_trades.json`,
  `kalshi_settlements.json`, the trade journal and `shadow_book.json` into a dated zip, keeps 30 days.
  The trade and settlement logs are read under the trade-log lock. Each JSON member is re-parsed from
  the finished zip; a source that doesn't parse is still kept, and the run exits 1. Fixes OPS-02: the
  ledger was in no backup, and its trade-side context can't be rebuilt from Kalshi.
- **Ops** Runs as the second action of the `Reconcile` task. Restore steps and a quarterly drill:
  `data/history/README.md`.

---

## 2026-11-17 -- Failed live-execute runs email [FAILED] (ER-07)

- **Fix** OPS-01: a crashed live-execute scan was invisible. Its `.bat` dropped the exit code and its
  output, and the email action exited 2 without sending. Task Scheduler showed only that code, which
  also meant "nothing to report". Execute wrappers now append the scan's output and `exit code N` to
  `logs/scan_<preset>.log` and `exit /b` it. For the five execute presets, `render_report_email.py`
  sends `[FAILED] <subject>` with the log's last run and exits 1 when the scan exited non-zero or
  wrote no report.
- **Fix** `kalshi_executor.py status` (and `make status`) crashed on every call with
  `AttributeError: 'Namespace' object has no attribute 'execute'` since B7 (2026-11-05). The
  execute wrappers call it before and after every scan, so this went unseen for the same reason.
- **Docs** `docs/task-schedules/README.md`: wrapper template, email behaviour, troubleshooting. The
  claim that the exit code is passed through now says what it needs: `exit /b` in the `.bat`.

---

## 2026-11-17 -- Cache replay runs the position and live-game gates (ER-03)

- **Fix** BUG-04: replaying a cached preview with `--pick` / `--ticker` re-checked Gates 5, 6, 6b,
  7 and 2b but not Gate 2 (max open positions) or Gate 4.8 (game started). Within the 600 s cache
  TTL a replay could exceed `MAX_OPEN_POSITIONS` or place an in-play bet with
  `ALLOW_LIVE_BETS=false`. The replay loop now drops those rows, and clamps a row's contracts to
  the current `MAX_BET_SIZE` if it was lowered since the preview.
- **Fix** On replay, `--pick` / `--ticker` were resolved against the re-gated list, so a dropped
  row shifted the numbers and `--pick 3` could place a bet other than preview row 3. The pick now
  runs on the cached menu first and only the picked rows are re-gated. Pinned by
  `tests/test_replay_gates.py`.

---

## 2026-11-17 -- The ledger records every real fill (ER-02, X2)

- **Fix** BUG-01: an order that filled after the create response settled at $0, because nothing
  re-read it. The settler now re-reads every open `resting`/`partial` order of its profile
  (`GET /portfolio/orders/{id}`) before settling and raises the row's fills and cost. A `resting`
  row is settled only once the venue confirms it, and one predicate decides exposure in both
  phases. A venue-side cancel with no fills closes the row at $0 (closes X2).
- **Fix** BUG-02: the live-order janitor decided "zero fill" from the log, which misses late fills,
  so a partly filled order was closed as a $0 cancel. Janitors now pass the venue's fill count
  to `mark_cancelled`, which closes only zero-fill rows and keeps the rest open as `partial`.
- **Fix** BUG-03: a log write that failed after Kalshi accepted the order (on Windows,
  `PermissionError` while CLV-Capture reads the file) was recorded as a failed order, hiding a
  real position. Bookkeeping after acceptance can no longer reach the error handlers. The write
  retries for about 3 s, then goes to `data/history/trade_journal.jsonl`, which the next settle
  merges back in.
- **New** `kalshi_settler.py audit-fills`: read-only check of closed rows against venue fills.
  At commit time it found one closed `partial` row under-booked (1 of 8 contracts); older orders
  return 404 and can't be checked.
- **Docs** Betting diagram re-pinned; the Settler node reads "refresh fills, P&L, CLV".

---

## 2026-11-17 -- Live orders need approval; client-level cap and kill switch (ER-01)

- **Fix** `KalshiClient.create_order` now refuses an order whose notional (contracts x the price of
  the side bought) exceeds `MAX_BET_SIZE` by more than 1c per contract, the executor's limit-price
  rounding. It's the one call every order passes through, so the cap holds even for a caller that
  skips `size_order`. Over the 284 live orders in the ledger it would have refused none.
- **Fix** Kill switch: while `data/KILL` exists, `create_order` and `intra_exchange_transfer` refuse.
  `DRY_RUN=true` still short-circuits first, so previews are unchanged. Refusals raise
  `OrderRefusedError`, which the executor records per order and never treats as a venue block.
- **Security** New tracked `.claude/settings.json` with a PreToolUse hook,
  `scripts/hooks/guard_live_orders.py`. It blocks any agent-run Bash or PowerShell command carrying
  `--execute`, `--go`, `--send-it`, `--mode execute`, `--verify-eligibility`, `create_order` or
  `intra_exchange_transfer` (read-only commands such as `git` and `grep` pass). A hook, not ask
  rules, because ask rules don't hold in bypass-permissions sessions; checked in a bypass-mode
  session. The owner places orders by typing `! <command>`. The settings also deny edits to
  `.env`, `.env.longshot` and `keys/`. The `edge-radar` skill is now user-invoked only
  (`disable-model-invocation`) and hands the order command to the user; `KALSHI_BETTOR` no longer
  follows a user who "insists" on overriding a risk limit.
- **Docs** Betting diagram re-pinned: the "Place order" node cites the new guard and reads
  "DRY_RUN, cap, KILL block"; the knobs card lists `data/KILL`.

---

## 2026-11-17 -- Audit follow-ups; halt docs name the real task folder (ER-11, R24c)

- **Docs** `docs/ROADMAP.md` gains "Audit follow-ups, 2026-11-16": the P0 and P1 items from the
  2026-11-16 audit (ER-01 to ER-12), in work order. ER-02 will close X2.
- **Fix** ER-11: the ops deck, `docs/task-schedules/README.md` and the `edge-radar` skill pointed the
  halt and manual-run commands at a Task Scheduler folder that no longer exists. They now name
  `\AI-Automation-Tools-Org-LocalApps\Edge-Radar-MikesAILab\`, and the halt boxes put
  `DRY_RUN=true` first. `docs/scripts/SCRIPTS_REFERENCE.md` examples use `<repo>` instead of a
  machine path.
- **Fix** R24c: `install_windows_task.py status` also lists every task in the folder it didn't
  install (the owner's folder shows all 16), pinned by `tests/test_install_windows_task.py`.
- **Fix** ER-01 (help text only): `scan.py --help` no longer says `--execute` asks for confirmation.
  It doesn't; the rest of ER-01 is open.

---

## 2026-11-16 -- Upstream check

- **Docs** All 13 `UPSTREAMS.md` rows checked. Queued K2: Kalshi renamed the order-error status
  `market_closed` to `market_inactive` (2026-11-05), so `venue_eligibility` should list it as
  transient; money path, no code change here. The Odds API now calls the bookmaker-level
  `last_update` on `/odds` deprecated, so the Odds API row notes `_bookmaker_last_update()` must
  keep its market-timestamp fallback (it does). The live ESPN, MLB, NHL and Yahoo responses still
  carry the keys the parsers read. CoinGecko's 2026-11-25 ticker-ID change and `/derivatives`
  pagination touch endpoints the code does not call.

---

## 2026-11-13 -- About text names Kalshi only

- **Metadata** The GitHub About text no longer names Polymarket US, removed 2026-09-29. The
  roadmap item is checked off.

---

## 2026-11-11 -- Roadmap rechecked against the org's 2026-11 requirements

- **Docs** `docs/ROADMAP.md` rechecked against the org's 2026-11 requirements. B7b and S15 change
  the live money config, so they are marked 🔒 Needs owner. S26b no longer prints a key suffix. T3
  is narrowed to what's left now that pytest runs in CI. R24c names the current Task Scheduler folder
  and the doc it has to fix. New items: templates for the rest of the scheduled jobs (🔒 Needs owner
  until it's decided which may go public), one risk-gate count everywhere, a ROADMAP link on the
  public page, security headers on the public page, and the About text (🔒).

---

## 2026-11-10 -- Scheduled jobs as Cronsole templates

- **Added** `scripts/schedulers/automation/build_cronsole_registry.py` generates a Registry v1
  catalog into `site/registry/`: six templates (scan, execute, next-day, settle, calibration,
  odds-keys) and an `edge-radar` pack. Vercel serves it at
  `edge-radar.ai-automation-tools.dev/registry/`, and the Cronsole gallery lists it, so anyone
  can schedule these jobs from Cronsole. The templates are now the tracked definition of the
  jobs; the installer's `.bat` files are gitignored and a clone never had them.
- **Safety** The two templates that can bet take a Mode parameter defaulting to `preview`.
  `scan.py` gains `--mode preview|execute`: `execute` adds `--execute`, `preview` adds nothing, and
  an unknown value or `preview` beside `--execute` exits rather than guessing.
- **Excluded** `account-graph`: its script is under gitignored `docs/my-documents/`.
- **Checks** `tests/test_cronsole_registry.py`: catalog current, one template per installer
  profile (or a stated reason), no template with a literal `--execute`, the live two default to
  preview, and, where the `.bat` files exist, the same scan flags as each `.bat`. A daily
  *Registry drift* workflow hashes every served file against `master`.
- **Docs** `AUTOMATION_GUIDE.md` lists the templates with gallery links; the README links the pack.
- **Site** The public page gains a **Schedule** section (nav, mobile nav and ⌘K palette): one
  card per template, read live from `registry/index.json` so it cannot drift from the gallery.
  Each card has *Get it for Cronsole* (the template in the gallery) and *Template JSON*, and
  says whether it can place orders. The section links the whole pack and the automation guide.
  `tests/test_site.py` pins the wiring.

---

## 2026-11-09 -- CI runs the tests; security policy; MIT licence

- **CI** `.github/workflows/ci.yml` runs `pytest tests/` on Python 3.12 on every pull request and
  every push to `master` (#358). Import smoke, lint and detect-secrets are still open (T3).
- **Docs** `SECURITY.md` says how to report a vulnerability (#359).
- **Docs** `LICENSE`: MIT, the owner's choice on 2026-11-09 (#360).

---

## 2026-11-09 -- Odds API keys out of logs and the quota cache

- **Finding** CodeQL `py/clear-text-logging-sensitive-data` (alerts 1 and 2): `odds_api.py`
  logged the last 6 characters of a key. Worse, `data/cache/odds_api_quota.json` stored every
  key in full, as the JSON keys.
- **Change** Logs and `get_status()` name a key by its slot in `ODDS_API_KEYS` (`#3`). The cache
  stores `sha256:<16 hex>` ids. A cache written before this loads as before; the next save
  rewrites it without the raw keys. `check_odds_keys.py` still prints a suffix to the console,
  so a key can be matched to its account by hand.

---

## 2026-11-07 -- NHL totals floor 0.06 -> 0.05 (operator override)

- **Finding** 0 orders on 11-06 and 11-07, ~12 in 12 days. Not a matching fault: the 11-08
  preview scored the full slate (16 NBA, 27 NFL, ~40 soccer events, NHL) and produced 56 rows
  at >= 3% gross edge, of which 52 failed Gate 3, 3 sat in disabled spread series and 1 failed
  another gate. Best row: NHL VGK@BUF Over 5.5 at 60c, +6.8% against a 7.7% effective floor
  (0.06 + 1.7% fee).
- **Change** Live `.env` `MIN_EDGE_THRESHOLD_NHL_TOTAL` 0.06 -> 0.05. **Operator override on
  volume, not evidence** -- the 10-03 reason (overs 16-15 lifetime at -17%, Kalshi o5.5 priced
  5-9pts under books, settlement rules unverified) still stands, and the admitted row is an over.
- **Effect** Admitted 1 of 9 NHL rows on 11-08 (`KXNHLTOTAL-26NOV08VGKBUF-6`, YES x3 @ 60c,
  $1.80). NO-side rows are unaffected: R28's 8% global NO floor binds first. Lowering the global
  or soccer floor would have admitted ~0, since those rows price at 77-93c, above
  `MAX_MARKET_PRICE=0.75`.
- **Recheck** Revert to 0.06 if the next ~15 NHL overs settled under this floor run negative.

---

## 2026-11-06 -- UFC cards scored again; two college names disambiguated

- **Finding** Kalshi dates UFC tickers a day *before* the card (`KXUFCFIGHT-26NOV06...`, fights
  Sat Nov 7 ET). `find_market_event` required the odds event on the ticker's ET date, so whole
  cards went unscored on and off since late August (198 refusals in Oct-Nov; 48 of 48 open
  markets on 11-06). The drift check reported UFC "100% odds-matched" because it matches names,
  not dates, so nothing flagged it.
- **Fix** MMA and boxing take the tennis branch: a single both-fighters candidate within 3 days
  of the ticker date. After the fix every open fight is priced (edges 0-2.3% on 11-06).
- **Names** `_team_match_strength` drops periods ("South Carolina St." now substring-matches
  "South Carolina St Bulldogs" instead of tying "South Carolina Upstate" on the city word), and
  a `florida international -> florida int'l` alias stops a tie with West Florida. Both games
  had been emitting no edge.
- **Context** The wager slowdown since mid-October is by design, not a fault: MLB/MLS/NHL/NFL
  spreads were switched off one by one (NFL spreads, the last big producer, on 11-03), and the
  remaining pilot floors plus the F1 fee pass ~1 bet/day.

---

## 2026-11-05 -- B7: sharp `eu` books on execute runs only; `BOOK_WEIGHTS` pruned

- **Finding** Every Odds API call requested `regions=us`. Pinnacle is served only in `eu`, so the
  3.0x sharp weight never applied: every cached response holds exactly nine US books
  (DraftKings, FanDuel, Bovada, BetMGM, MyBookie, BetRivers, BetOnline, BetUS, LowVig). The
  "sharp-weighted consensus" was a US recreational consensus.
- **Config** `ODDS_API_REGIONS_EXECUTE` (default `us`, so nothing changes until set). When a
  scanner or `kalshi_executor.py` runs with `--execute`, its process requests these regions;
  previews, shadow book, calibration and every other reader stay `us`. That was the quota option
  chosen: each extra region costs one request per call, and only the runs that place orders pay it.
- **Cache** Regions are part of both cache keys (in-process and file). Without that, an
  `--execute` run inside the 300s TTL of a preview would be served the us-only response and `eu`
  would never be fetched. `us` keeps the pre-B7 filenames.
- **Caveats** (1) Preview and execute can now disagree: Pinnacle at 3x moves the consensus, so
  an execute run may place different rows from the preview it follows. An R26 `--pick` replay
  places the preview's rows unchanged, at us-only prices. (2) The `n_books` floors (R29 NBA=8,
  MLB 5/3) were tuned on a 9-book pool, and `eu` adds books, so they mean something different
  once this is on. Re-check them (ROADMAP B7b).
- **`BOOK_WEIGHTS`** pruned to keys that actually arrive, plus `pinnacle`. Circa, Bookmaker,
  Caesars, ESPN Bet, PointsBet, SuperBook, Hard Rock, Bally, Fliff and `pinnaclesports` never
  appeared. Anything else, including the other `eu` books, gets `DEFAULT_BOOK_WEIGHT` (1.0).
- **Diagram** re-pinned to `2b39b0e`: line ranges shifted, `odds_cache` range now covers the
  regions key, and the Odds API node reads "us; +eu on execute".

---

## 2026-11-03 -- NFL spreads priced on key-number margins; NFL spreads switched off; shadow book sees every strike

- **Finding** 25 of 45 live NFL spread bets since August were YES "wins by over 7.5", at 23-32c
  (1-4pt favourites); NCAAF 10 of 23. Against 3,949 NFL games 2012-2025 (nflverse closing lines),
  the normal margin model over-prices exactly that bet: a 2.5-3pt favourite covers 7.5 **27-29%**
  of the time, the model said **36-37%**. Margins pile on 3 (8.2% of games) and 7 (5.5%), where a
  normal with stdev 13.5 puts ~3% each. The ~8pt error is the whole 7.5-9pt claimed edge on those
  bets; the market (~27c) was right. NFL 7.5 YES went 8/22 (+$12.90) against ~5.6 expected at
  market, which is luck, not edge.
- **`.env`** `MIN_EDGE_THRESHOLD_NFL_SPREAD=1.0` -- NFL spreads OFF, operator decision. Moneyline
  and totals keep the 0.06 NFL pilot floor. Two 7.5 orders placed today (CLE@NO `NO8`,
  CIN@ATL `CIN8`) are held, per S2.
- **Model** `consensus_spread_prob` prices NFL on whole-number margins: normal mass at each margin
  k times a fitted weight `w[|k|]` (3 -> 2.33, 7 -> 1.58, 0 -> 0.24), stdev 11.5. Each book's
  mean is inferred by the same model, and a whole-number line's quote is read as conditional on
  no push. Holdout (fit <=2020, scored 2021+, production functions): 1-4pt favourites over 7.5
  27.3% actual / 36.2% normal / **30.7% discrete**, and discrete has the lower Brier at every
  strike for small favourites. On today's slate the median claimed edge at 7.5 fell from ~8pts to
  0.9pts, and no NFL strike clears the effective floor. Details carry `margin_model`. Other sports
  are unchanged. Refit with `scripts/backtest/fit_nfl_margin.py` (new, read-only).
- **Shadow book** `scan_all_markets(max_per_game=None)` skips the 2-per-game cap, and
  `shadow_book collect` uses it: the cap kept only each game's highest-edge strikes, so the
  "pre-gate" book was edge-selected and reviews saw mostly the strikes the model over-prices
  (244 NFL strikes per collect, was 30). `review` sweeps spreads and totals separately with a
  game-clustered CI (PR #351), and skips `nfl_discrete` rows in the normal-only stdev sweep.
  `shadow_book.bat` (local) now collects `KXNFLSPREAD` and `KXNFLTOTAL` daily.
- **Next** NFL spreads stay off until the shadow book shows the discrete model at or ahead of the
  market on settled rows. NCAAF bunches on 7 less, but its 7.5 rows run ~3pts high in the shadow
  book (108 won vs ~115 model / ~104 market); not refitted.
- **Diagram** Re-pinned to `cde08ae`: `edge_detector.py` ranges shifted, and "Fair probability"
  now cites the discrete NFL model.
## 2026-11-02 -- Automation guide points to Cronsole

- **Docs** `docs/setup/AUTOMATION_GUIDE.md` gains a short "See the tasks in Cronsole" note: the tasks the
  installer registers show up in Cronsole's dashboard via its Windows agent. Docs only.

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

---

## Older entries

Entries from before 2026-10 are archived by month in [changelog/](changelog/README.md), along with the pre-2026-09-29 ROADMAP.
