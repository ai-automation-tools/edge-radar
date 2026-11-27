# Eight tools, eight questions

Everything in `scripts/backtest/`. Each was written for one question that could not be answered from
the routine performance report, and each carries its motivation in its module docstring — **read the
docstring before the code; it says what the tool is allowed to conclude.**

---

## 1. `calibration_study.py` — is the claimed edge worth anything?

**The question:** does the model price better than the market, and how much of each claimed edge
should we act on?

```bash
python scripts/backtest/calibration_study.py                      # whole settled book
python scripts/backtest/calibration_study.py --sport mlb          # one sport
python scripts/backtest/calibration_study.py --category spread --min-n 15
python scripts/backtest/calibration_study.py --save
```

**What it computes:** model and market Brier, log loss, the Brier-optimal weight **λ** on claimed
edge over a grid, bootstrap CIs, and an information test that splits high- vs low-edge halves within
price bands.

**What it found, and the standing prior:** market Brier beat model Brier in **6 of 6 months**
(0.2037 vs 0.2270, CI on the difference excluding zero). **λ = 0.16, CI [-0.04, +0.42]** — about a
sixth of each claimed edge is supported. The model does show real signal on cheap contracts (≤32c:
the high-edge half wins +10.8 points more than the low-edge half) but **inverts on favourites**
(≥51c: -10.8 points), which independently reproduces the earlier "high confidence underperforms"
finding.

> **This is the tool that must be re-run before any sizing increase.** Not the performance report —
> a good month of ROI and a λ of 0.16 are entirely compatible.

**Caveat:** `load_rows` does **not** filter on fills, so zero-contract rows are in the sample. Check
the fill count when a result hinges on a handful of rows.

---

## 2. `backtester.py` — how would a variant have done?

**The question:** counterfactual strategy comparison over the settled book.

```bash
python scripts/backtest/backtester.py                          # full report
python scripts/backtest/backtester.py --sport mlb --min-edge 0.05
python scripts/backtest/backtester.py --confidence high --after 2026-06-01
python scripts/backtest/backtester.py --simulate --save        # strategy comparison
```

**Use it for:** "what if the floor had been 0.12", "what if we had only taken spreads", "what does
the book look like after this date". `--simulate` is the strategy-comparison mode; `--save` writes a
markdown report.

**What it cannot tell you:** anything about rows that never existed. It re-scores **what was
actually bet**, so it can only narrow a book, never widen one. A strategy that would have bought
markets the gates rejected is invisible here — that is a shadow-book question.

---

## 3. `correlation_check.py` — do our bets resolve together?

**The question:** should same-night / same-league / same-direction bets be damped beyond what the
`batch_size` divisor already does?

```bash
python scripts/backtest/correlation_check.py
python scripts/backtest/correlation_check.py --since 2026-06-01 --category total
```

**The answer on record is no, and the reasoning is the valuable part.** Pooling every cluster
against a single global win rate reports **rho ≈ +0.181** — and that is Simpson's paradox. Clusters
live inside strata with very different base rates (totals win ~82%, spreads ~24%), and pooling
groups with unequal means manufactures apparent within-group concordance. Judged against per-stratum
base rates it is **+0.048 overall and -0.187 for totals**.

So there is deliberately **no correlation guard** in the system. That is *"no evidence of
correlation"*, not proof of independence — **re-run it as settlements accumulate**, and quote the
per-stratum number, never the pooled one.

---

## 4. `book_width_check.py` — was the book thin on the losing days?

**The question:** does a sport underperform because consensus was built from too few bookmakers?

```bash
python scripts/backtest/book_width_check.py --sport mlb --proxy
python scripts/backtest/book_width_check.py --sport nba --thin 5 --json
```

**Why `--proxy` exists is the lesson.** The question was asked and could not be answered, because
`n_books` was computed at scan time — it sets `confidence` and feeds the composite — and then
**thrown away**. Nothing in the trade log or settlement log ever carried it. `--proxy` recovers
Odds-API key-exhaustion days from the logs and splits a sport's settled bets by whether their game
day had thin coverage.

> **Generalise this before your own analysis:** confirm the field is *persisted*, not merely
> computed. A value that exists only inside a scan is unavailable to every later question.

---

## 5. `totals_distance_check.py` — are we extrapolating too far?

**The question:** does totals performance depend on how far the Kalshi strike sits from the model's
inferred mean?

```bash
python scripts/backtest/totals_distance_check.py --sport MLB --since 2026-07-01
```

**The context:** MLB "under ~13 runs" bets were 69% of everything bet after MLB totals coverage
landed, and the model over-claimed their win rate by ~26 points (claimed 89.7%, realised 64.3%). The
proposed fix was a cap on extrapolation distance, on the reasoning that past some distance the
answer comes from a hardcoded stdev rather than from anything a sportsbook actually quoted.

**This is the shape to copy** when a single bet type dominates a book: measure whether performance
degrades with distance from a real quote *before* adding a cap.

---

## 6. `nfl_week1_review.py` — the pre-declared decision

**The question:** does a frozen sport come back, and to what?

```bash
python scripts/backtest/nfl_week1_review.py              # report only, never writes
python scripts/backtest/nfl_week1_review.py --apply      # apply branch A if it fires
python scripts/backtest/nfl_week1_review.py --self-check # asserts on the branch logic
```

Not a general tool — a **template**. Copy its structure for any decision that changes a gate:
constants at the top with a comment forbidding post-hoc edits, a pure `decide(rows)`, three named
branches where every failure path (including *any exception*) stays frozen, report-only by default,
a fail-closed `--apply`, and a `--self-check` that exercises the branch table on synthetic rows.

Full structure → [`launch-and-kill.md`](../../edge-radar-strategy-profiles/references/launch-and-kill.md).

---

## 7. `betting_audit.py` — is any sport quietly broken?

**The question:** the `/betting-logic-review` battery, run mechanically across every sport.

```bash
python scripts/backtest/betting_audit.py --save
python scripts/backtest/betting_audit.py --save --analyze auto   # adds a read-only claude -p pass
```

Born from defects found only by hand: a sport scanned at zero markets all season (dead series
prefixes), rest-day context leaking between sports that share a team code, and spread/total models
that over-claim in one direction while outcomes track the market. It reads local data only (settlement
and trade logs, shadow book, logs, the latest drift probe), writes nothing but its report and never
touches `.env`. It runs weekly, folded into the Sunday Weekly-Analysis email. Read it before
designing a bespoke check — the defect may already be one of its rows.

---

## 8. `fit_nfl_margin.py` — are NFL margins priced right?

**The question:** NFL margins are whole numbers that pile on 3 and 7, so a normal CDF over-priced
"a small favourite wins by over 7.5" by ~8 points (3,949 games; 2026-11-03). Production now prices NFL
spreads on key-number weights (`edge_detector._NFL_KEY_WEIGHTS`), and this script fits and validates
them: fit on seasons through 2020, score later seasons with the **production** functions.

```bash
python scripts/backtest/fit_nfl_margin.py            # holdout table + refit
```

Read-only: paste refitted weights into `_NFL_KEY_WEIGHTS` by hand. **Shape to copy:** when one strike
dominates a sport's bets, compare the model to history at that strike before trusting the edge.

---

## 9. And `shadow_book.py`

The only one that generates evidence rather than reading it. It has its own file:
[`shadow-book.md`](shadow-book.md).

---

## Picking between them

| Symptom | Start with |
|:---|:---|
| A strategy "looks good" and someone wants to size up | §1 `calibration_study.py`. Always. |
| One bet type dominates the book | §5 `totals_distance_check.py`, then the one-sided-book test |
| A sport is losing and nobody knows why | §4 `book_width_check.py --proxy`, then §1 scoped to that sport |
| Someone wants a new damping rule for correlated slates | §3 `correlation_check.py` — and read the per-stratum number |
| "What if we had done X instead" | §2 `backtester.py --simulate`, remembering it can only narrow |
| A gate needs to move | §6's template |
| A weekly "is anything broken across sports" sweep | §7 `betting_audit.py` |
| The segment is frozen and has no settlements | [`shadow-book.md`](shadow-book.md) |
