---
name: edge-radar-strategy-profiles
description: >-
  Design, launch, compare and retire an Edge-Radar betting strategy as a `.env.<name>` profile
  overlay rather than a fork — pick the knob that actually moves the price band you mean, isolate
  the bankroll with a Kalshi subaccount, and run the dry-run → pilot → live ladder with the exit
  rule written before any money is at stake. Use whenever the user wants a new betting strategy, a
  second book, a longshot/favourites/spread-only/underdog angle, "a separate account to try X",
  different sizing or a different price floor for one slice of markets; whenever an existing
  profile needs comparing, promoting to live, or killing; and whenever someone proposes cloning
  the repo, adding a second API key, or hand-editing `.env` to test an idea.
---

# Strategy profiles

**A strategy is a `.env.<name>` file and a subaccount. It is never a fork, never a second API key,
and never an edit to the live `.env`.**

> **The frame:** two strategies, one codebase, two wallets. Everything the overlay does not name is
> inherited — risk gates, fee model, calibration, per-sport floors, every future bug fix — so a
> comparison between two books measures the *strategies* rather than two drifting copies of the
> code. That inheritance is the entire product. Anything that breaks it (a fork, a clone, a second
> checkout) turns "which strategy is better" into an unanswerable question.

This skill covers **deciding what the strategy is** and **getting it from idea to live money
safely**.

> **🔒 Needs owner: money moves only on the owner's word.** Three steps here touch real money:
> **creating or funding a subaccount**, **any edit that sets `DRY_RUN=false`**, and **promoting a
> profile to pilot or live**. An agent never does them on its own, unattended or not. Prepare the
> exact command, `.env.<name>` diff or task change, show it with the evidence that the entry
> condition is met, then **stop** and wait for the owner to run or approve it. A scheduled job that
> reaches one of these steps reports it and ends. The repo's own `/edge-radar` skill covers running a scan once you know what you want;
`edge-radar-strategy-evidence` covers proving it works.

---

## 1. Before anything: is this a profile at all?

| The idea is… | Then it is… |
|:---|:---|
| Different **sizing**, **price floor**, **per-event cap**, **edge floor**, or **execution posture** for a slice of markets | A profile. Continue. |
| A different **fair-value model** for a market the code already prices | Not a profile — that is an edge-detector change, and it should reach *both* books. |
| A **new sport, category or venue** nothing prices yet | Not a profile — onboard the market first at the global floor, then profile it if you want a second angle on it. |
| "The same thing but with more money" | Not a strategy. Change `UNIT_SIZE` / `KELLY_FRACTION` in the base `.env` and record why. |

A profile answers **"what should this book buy, and how big?"** If the idea changes what a contract
is *worth*, it belongs in the model, where both books get it.

---

## 2. Pick the knob — there are two lanes, not one

The most common wasted profile is one that moves a knob which does not bind in the price band the
strategy is about. Sizing has **two independent lanes**, and they meet around 30–60c:

| Price band | What binds | The knob | What the other knob does |
|:---|:---|:---|:---|
| **below ~30c** | the flat floor, `round(UNIT_SIZE / price)` | **`UNIT_SIZE`** — the longshot knob | `KELLY_FRACTION` is inert; Kelly never clears the floor |
| **above ~60c** | Kelly, `edge / (1 - price)` | **`KELLY_FRACTION`** — the favourites knob | `UNIT_SIZE` is irrelevant; the floor was cleared long ago |

So a longshot profile that tunes `KELLY_FRACTION` has changed nothing, and a favourites profile
that tunes `UNIT_SIZE` has changed nothing. Every knob and the band it moves →
[`references/knobs.md`](references/knobs.md).

**`KELLY_FRACTION` is a portfolio fraction, not per-bet** — the executor divides it by
`batch_size = min(len(opportunities), --max-bets)`. That divisor doubles as the only correlation
guard in the system, so **keep it ≤ 0.5 in any profile**. At 1.0 a fully correlated slate reaches
full portfolio Kelly in one night.

---

## 3. Write the overlay

```bash
cp .env.longshot.example .env.<name>   # or start empty — the example is a teaching file
```

Four rules, each of which has already cost someone something:

1. **Write only what differs.** Every line copied across from `.env` is a line that stops
   inheriting fixes. The fork this system replaced shipped `MAX_OPEN_EXPOSURE_PCT=0`,
   `MAX_SEGMENT_EXPOSURE_PCT=0`, `MAX_DAYS_TO_EVENT_FOR_GAME_MARKETS=0`, `MAX_BET_SIZE=100` and
   `MAX_DAILY_LOSS=250` — not by decision, but because nobody re-tightened the shipped defaults
   after cloning, while its own roadmap recorded the risk posture as *"conservative, matches main
   repo, no change needed."*
2. **`KALSHI_SUBACCOUNT=<n>` is mandatory, and it is the only line that isolates money.** Not a
   second API key, not a second checkout — both still draw on one balance, and each copy's
   `MAX_DAILY_LOSS` and exposure gates would see only their own activity, never the combined
   draw-down. A subaccount is an exchange-enforced separate wallet under one login (Advanced API
   tier), created once with `client.create_subaccount()`.
3. **`DRY_RUN=true` until the evidence window closes.** The base `.env` runs Kalshi live and a new
   profile must not inherit that. Removing this line is a decision with a pre-declared trigger
   (§5), not a step in setup.
4. **Comment the *why*, with the number.** `.env.longshot.example` carries a ⚠️ block on its own
   `MIN_MARKET_PRICE=0.08` recording that the 8–12c band it newly admits went **0W-36L
   (-103.3% ROI)** across all six settled months, while the 0–8c band it still excludes holds the
   book's two biggest winners. A value with no evidence attached is folklore within six weeks.

**It fails closed.** A missing `.env.<name>` raises rather than falling back to the base `.env`,
because the base `.env` is the live-money wallet: a typo'd `--profile longshto` that silently
resolved to `main` would run one strategy's intent against the other's bankroll, live. Same
reasoning as the venue-eligibility check.

---

## 4. Select it, and prove you selected it

```bash
python scripts/scan.py sports --profile <name> --filter mlb --date today
EDGE_RADAR_PROFILE=<name> python scripts/doctor.py     # every non-scan entry point
```

`--profile` is consumed by `scan.py`, not forwarded to the scanners; it reaches the child as
`EDGE_RADAR_PROFILE`, and `load_dotenv()` does not override variables already set, so the overlay
survives the child's own `.env` load. **Everything that is not `scan.py` takes the env var, not the
flag** — `doctor.py`, settle, reconcile, any ad-hoc script.

**Run `doctor.py` under the profile before the first execution.** It prints `PROFILE = <name>` and
the subaccount; a portfolio report run *without* the profile is reading the wrong account's money.
Confirm the banner names the wallet you meant.

---

## 5. The ladder: dry-run → pilot → live

Never straight to live, and never on a date. Each rung has an entry condition written **before** it
is reachable — the discipline in full, with a worked pre-declared rule, in
[`references/launch-and-kill.md`](references/launch-and-kill.md).

| Rung | Posture | Leaves when |
|:---|:---|:---|
| **1 — dry-run** | `DRY_RUN=true`. Rows log identically to live, so they stay valid evidence. | The profile's own knob is demonstrably **binding**. If every rejection is on *edge*, the profile setting is changing nothing, and going live changes nothing except downside. |
| **2 — pilot** 🔒 Needs owner | `DRY_RUN=false` **plus** a capped edge floor (≈2–3x global) and a `MAX_SEGMENT_EXPOSURE_PCT` that actually binds the segment. | The pre-declared review fires on real settled rows. |
| **3 — live** 🔒 Needs owner | Normal floors. | — |

The pilot cap **is** the response to uncertainty. When a review's bootstrap CI straddles zero — and
at n≈25 it will — the answer is a capped floor, not a coin flip between frozen and unfrozen.

**Flipping `DRY_RUN=false` is the owner's call (🔒 Needs owner): prepare the diff and stop.
Before proposing it on any profile, clear the soft-spot list.** Three surfaces are
safe today only *because* the second book never fills:

- **Reporting is pooled.** `daily_summary.py`, `risk_check.py` and `betting_analysis.py` read the
  whole trade log. A dry run writes zero-fill rows that never settle, so nothing blends today. Real
  fills blend both books immediately — these need `for_profile()` or a per-profile split first.
- **Settlement and reconciliation only ever see subaccount 0.** `Hourly-Settle` and `Reconcile`
  both run unprofiled. A live second wallet needs its **own** settle and reconcile
  tasks under `EDGE_RADAR_PROFILE=<name>`, or its fills never settle and its P&L never lands.
  (`CLV-Capture` is fine — it reads the unfiltered log and calls public market data.)
- **Scan report filenames carry no profile tag.** Two profiles scanning the same filter on the same
  day into the same directory overwrite each other silently. Pin `--report-dir` per profile.

---

## 6. Compare the two books

One trade log holds both, and every row carries `"profile"`. **Rows written before P1 have no key,
so every reader must default to `"main"`.**

```bash
python -c "import json,collections; print(collections.Counter(t.get('profile','main') for t in json.load(open('data/history/kalshi_trades.json'))))"
```

One shared log is *better* evidence than two logs gave — both books run identical code, odds cache,
fees and calibration, so a comparison measures the strategies. But any gate reading **history**
rather than the venue must be scoped or it measures the wrong book. Two do, and
`trade_log.for_profile()` scopes both:

| Gate | Reads | Scoped by |
|:---|:---|:---|
| **1** — daily loss limit | trade log | `for_profile()` |
| **7** — series dedup | trade log | `for_profile()` |
| 5 — already holding | live venue positions | the subaccount |
| 6 — per-event cap | live venue positions | the subaccount |

Unscoped this is not cosmetic: a bad day on `main` halts the other book, and a matchup one profile
bet blocks the other — *across two genuinely separate wallets*. It was live for exactly one run
after the merge, and the second book's banner reported the first book's P&L and dedup count.
**Settlement, CLV capture and reconciliation deliberately do not scope** — they act on a row by
`trade_id` or ticker, and a row is a row regardless of which strategy opened it.

> **Any new gate or report that reads the trade log must decide, explicitly, whether it is
> per-book or whole-book.** That is the one recurring bug in this design.

---

## 7. Checklist

1. **Confirm it is a profile** (§1), not a model change wearing a profile's clothes.
2. **Name the price band** the strategy is about, then pick the knob that binds there (§2).
3. **Create and fund the subaccount.** 🔒 Needs owner: prepare the steps and the amount, then
   stop; the owner creates and funds it. Record which number, and when.
4. **Write `.env.<name>`** — deltas only, `KALSHI_SUBACCOUNT` set, `DRY_RUN=true`, every value
   carrying its evidence in a comment.
5. **Write the exit rule now**, while nothing is at stake → [`references/launch-and-kill.md`](references/launch-and-kill.md).
6. **`EDGE_RADAR_PROFILE=<name> python scripts/doctor.py`** — confirm the banner names the wallet.
7. **Dry-run a scan**, then read the *rejection reasons*, not the candidate count, to confirm the
   profile's knob is binding.
8. **Prove it** → the `edge-radar-strategy-evidence` skill.
9. **Promote to pilot** only when the pre-declared rule fires, and fix the §5 soft spots first.
   🔒 Needs owner: present the evidence and the `DRY_RUN=false` diff, then stop. Pilot → live is
   the same: the owner promotes.
10. **Document it** in `docs/<name>/README.md` on the four-layer shape — selection, settings, money,
    data — plus what is deliberately shared and what is still pooled.

---

## 8. Anti-patterns

- **Forking the repo to try a strategy.** The fork this replaced lasted six days and, on a delta of
  two env vars, drifted into a live defect *in each direction*: it scanned zero college football all
  September on a stale ticker prefix and was missing two shipped features, while the main side was
  missing its own trade-row fix. Add a profile.
- **A second API key "for isolation".** It isolates nothing — both keys draw on one balance.
- **Editing the live `.env` to test an idea.** That is the live-money wallet, and the edit outlives
  your memory of making it.
- **Copying the whole `.env` into the overlay.** It stops inheriting fixes the day you write it.
- **Tuning `KELLY_FRACTION` for a longshot book** (or `UNIT_SIZE` for a favourites book). Neither
  binds where you mean, so the profile is a no-op you will spend a month interpreting.
- **`KELLY_FRACTION` above 0.5.** The batch divisor is the only correlation guard there is.
- **Going live because the dry-run "looks good".** A dry run whose knob never binds is showing you
  the base strategy.
- **Promoting on a date rather than a rule.** A date cannot lose an argument with a hot week.
- **`DRY_RUN=false` without a profiled settle + reconcile task.** The fills are real; the P&L never
  lands, and you end up comparing a book whose wins are invisible.
- **Two profiles scanning the same filter into the same report dir.** Silent overwrite.
- **An overlay value with no comment saying what evidence set it.** In six weeks it is a rule nobody
  can defend, and therefore nobody can remove.

---

## Related

| For | See |
|:---|:---|
| Proving a strategy before it gets money | the `edge-radar-strategy-evidence` skill |
| Running a scan, placing a bet, settling | the repo's `/edge-radar` skill |
| Post-hoc performance of what settled | the repo's `/edge-radar-analysis` skill |
| Auditing the math for money bugs | the repo's `/betting-logic-review` skill |
| The worked example, four layers deep | `docs/longshot/README.md` in the repo (the strategy was retired 2026-09-28; the profile mechanism and the doc stay) |
