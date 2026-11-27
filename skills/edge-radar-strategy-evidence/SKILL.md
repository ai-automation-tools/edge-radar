---
name: edge-radar-strategy-evidence
description: >-
  Decide whether an Edge-Radar betting strategy, sport, parameter or claimed edge is actually
  supported by outcomes — pick the right tool in scripts/backtest/ for the question, report the
  model-vs-market Brier pair rather than a bare "Brier", collect zero-risk shadow rows when a
  freeze or gate blocks its own evidence, and say what the sample can and cannot carry. Use for
  "is this strategy working", "should we unfreeze X", "is the edge real", "what does the settled
  book say about Y", "fit this parameter", "before/after a risk-gate change", "how many bets until
  we know", any claim about ROI, win rate, calibration, CLV or correlation, and any proposal to
  raise sizing or loosen a gate.
---

# Strategy evidence

**The question is never "did it win". It is "does this sample support acting differently".**

> **The frame that governs everything here:** over 390 settled bets the *market's* Brier beat the
> *model's* in **6 of 6 months** (0.2037 vs 0.2270, CI on the difference excluding zero), and the
> Brier-optimal weight on claimed edge is **λ = 0.16, CI [-0.04, +0.42]**. Roughly a **sixth** of
> each claimed edge is supported by outcomes. Treat any claimed edge as ~5x optimistic until
> re-measured, and **never add sizing aggression without re-running `calibration_study.py` first.**

This skill picks the tool and reads the result. `edge-radar-strategy-profiles` covers designing the
strategy; the repo's `/edge-radar-analysis` covers the routine performance report; the repo's
`/betting-logic-review` audits the code that produced the numbers.

---

## 1. Route the question

| The question | Tool | Read |
|:---|:---|:---|
| "Is the model better than the market at pricing this?" · "Is the claimed edge real?" | `calibration_study.py` | [`references/tool-map.md`](references/tool-map.md) §1 |
| "Should this frozen / gated sport come back?" | the pre-declared review (`nfl_week1_review.py` is the template) | §3 below |
| "The sport is frozen, so it has no settlements — now what?" | `shadow_book.py` | [`references/shadow-book.md`](references/shadow-book.md) |
| "What value should this parameter actually be?" | `shadow_book.py review` (stdev sweep) | [`references/shadow-book.md`](references/shadow-book.md) §4 |
| "How would strategy variant X have done?" | `backtester.py --simulate` | [`references/tool-map.md`](references/tool-map.md) §2 |
| "Do our bets resolve together? Should we damp correlated slates?" | `correlation_check.py` | [`references/tool-map.md`](references/tool-map.md) §3 |
| "Is this sport underperforming because the book was thin?" | `book_width_check.py` | [`references/tool-map.md`](references/tool-map.md) §4 |
| "Are we extrapolating a totals model too far from a real quote?" | `totals_distance_check.py` | [`references/tool-map.md`](references/tool-map.md) §5 |
| "Is any sport quietly broken?" (dead series, context leaking between sports, one-directional over-claim) | `betting_audit.py` | [`references/tool-map.md`](references/tool-map.md) §7 |
| "Are NFL margins priced right?" (key-number weights) | `fit_nfl_margin.py` | [`references/tool-map.md`](references/tool-map.md) §8 |
| "How are we doing?" (routine, by sport/side/band) | the repo's `/edge-radar-analysis` | — |

**If no tool answers it, the honest answer is usually "the log does not carry that."** Two real
examples: `n_books` was computed at scan time and thrown away, so "were the losing days the thin
days" was unanswerable for months; and exchange fees were never captured on the trade row, so every
settled `net_pnl` computed against a fee of 0. **Before designing an analysis, confirm the field
exists in the log** — and if it does not, the deliverable is to start logging it.

---

## 2. Report the pair, labelled

**"Brier" alone is not a quantity.**

| Predicted with | Is | Call it |
|:---|:---|:---|
| `market_price_at_entry` | the benchmark | **market Brier** |
| `fair_value` | the thing under test | **model Brier** |

Both were once printed under one label on the same five bets on the same day — 0.169 against
0.0501. Every unfreeze decision and the λ finding turn on the comparison, so always give **both
numbers, both labels, and the bootstrap CI on the difference.** A model Brier with no market Brier
next to it is not evidence of anything.

Two data hazards that silently corrupt the pair:

- **`market_price_at_entry` and `fair_value` are already side-relative.** A NO bought at 73c stores
  `0.73` — the price paid for the NO. Never flip them for NO rows. Flipping scored a 73c NO as a
  `0.27` prediction against a win and reported Brier 0.169 where the truth was 0.077 — wrong on
  every window containing a NO settlement, which is a third of the book.
- **`won` is whether the *prediction* was right, never whether the row profited.** A zero-fill row
  that settled correctly was once logged as a loss, because `revenue > cost` collapses to `0 > 0`.
  `calibration_study.load_rows` does **not** filter on fills, so those phantom losses fed the very
  sample λ and the model-vs-market pair are computed from. Filled rows are unaffected.

---

## 3. When the decision is a gate change

Any proposal that unfreezes a sport, lowers a floor, raises sizing, or loosens a gate goes through
a **pre-declared rule** — constants at the top, a pure `decide(rows)` function, named branches, and
every failure path landing on "do nothing". `scripts/backtest/nfl_week1_review.py` is the working
template; the full structure and the override-labelling rule are in the profiles skill's
[`launch-and-kill.md`](../edge-radar-strategy-profiles/references/launch-and-kill.md).

Three things to insist on when reading one:

1. **Usable ≠ settled.** A review counting rows that carry a model probability will silently drop
   rows missing `fair_value`. "Too few settlements" then reads as "the sport barely traded" when the
   real cause is that the rows exist and are unreadable. **State both numbers** — one projection was
   23 usable out of 31 settled, and which of those is short changes what to do about it.
2. **A CI that straddles zero is the answer, not a nuisance.** At n≈25 it will. The correct response
   is a **capped pilot floor**, not a coin flip between frozen and unfrozen. The cap *is* the
   response to the uncertainty.
3. **Over-claim is a separate bar from Brier.** A good Brier alongside a large mean over-claim is
   luck, not calibration — hence a second constant (`MAX_MODEL_ERR = 0.15`) that fails independently.

---

## 4. Sample-size reality

| Sample | What it can support |
|---:|:---|
| **< 20** | Nothing. No branch fires. Do not read ROI, do not read win rate. |
| **20–40** | A directional model-vs-market Brier read, with a CI that will straddle zero. Enough for a **capped pilot**, never for normal sizing. |
| **~100+** | A price-band or category split worth quoting (e.g. spread-as-category at 23% win, +31.7% ROI, n=111). |
| **~400** | The λ-scale question — is claimed edge worth anything at all. This is where the 6-of-6-months finding lives. |
| **ROI, ever** | Slow. For any book that will not accumulate hundreds of settles, **read CLV instead** — closing-line value is a measurement; ROI at n≈30 is a story. |

Calibration has its own bar: `_MIN_CALIB_SAMPLES` is **20 per sport/category/30d**, so a sport with
11 lifetime settles can *never* fit its own parameters from live bets. That is a shadow-book job.

---

## 5. Diagnostics that catch a fake edge fast

Run these before a deep analysis. Each has caught a real defect.

- **The one-sided-book test.** *An edge that fires in one direction every time is a parameter, not a
  signal.* All 11 NCAAF bets ever placed were YES on "team covers a big alternate spread", and the
  whole claimed edge was one uncalibrated `margin_stdev` — 15.0 in the code against a market pricing
  ~9.5, a disagreement restated eleven times. A fat stdev inflates P(big cover) uniformly, which is
  exactly why only the YES side was ever taken. **Check side balance before reading a losing streak
  as variance.**
- **Is the parameter fitted or inherited?** `calibration_stdevs.json` carried the `edge_detector.py`
  fallback byte-for-byte. A "calibrated" value identical to the hardcoded fallback was never fitted.
- **Simpson's paradox on any pooled statistic.** The naive pooled correlation of +0.181 is an
  artefact of pooling strata with very different base rates (totals win ~82%, spreads ~24%); judged
  against per-stratum base rates it is **+0.048 overall and -0.187 for totals**. There is deliberately
  **no correlation guard** as a result — and that is "no evidence of correlation", not proof of
  independence, so re-run it as settlements accumulate.
- **Does the claimed population even exist post-gate?** Two composites once used `edge * 20`,
  saturating at a 50% edge instead of 10%, which made a gate structurally unreachable: 0 futures bets
  in 85 settled trades, 0 of 362 rows ever reaching the bar. **Every composite scales edge as
  `min(edge / 0.01, 10)`.** A category with a suspiciously round zero is the tell.
- **Does the filter reject everything for one reason?** A staleness filter once rejected **100%** of
  books on every live event (2888 exclusions in a month, zero from the age check it was blamed on)
  while those quotes ran a median 34s old against a 1200s limit. A 100% rejection rate is a bug
  until proven otherwise.

---

## 6. Checklist

1. **Name the decision** the evidence is for. "Curiosity" is a fine reason to run a report and a bad
   reason to change a gate.
2. **Route to the tool** (§1). If nothing fits, check the log carries the field before designing
   anything.
3. **Confirm the sample can carry the claim** (§4) *before* computing, not after.
4. **Run the diagnostics** (§5) — they are cheap and they are where the real findings come from.
5. **Report the model/market Brier pair, labelled, with the CI** (§2).
6. **If the decision is a gate change**, write the rule as a pre-declared branch table (§3) and run
   its `--self-check`.
7. **If the segment is frozen or gated out of its own evidence**, collect shadow rows instead →
   [`references/shadow-book.md`](references/shadow-book.md).
8. **Write the conclusion down with its date, its n, and its CI.** A finding with no sample size
   attached becomes folklore within a month and is then unfalsifiable.
9. **Say what you did *not* measure.** Calibration is not tradeability; a shadow book has no
   slippage and no queue position.

---

## 7. Anti-patterns

- **A bare "Brier".** Model or market? The two were printed under one label once already.
- **Flipping price and fair value for NO rows.** They are already side-relative.
- **Reading ROI at n≈30.** Read CLV.
- **Quoting a pooled statistic across strata with different base rates.** +0.181 becomes +0.048.
- **Treating a losing streak as variance without checking side balance.** One-sided books are
  parameters, not signals.
- **Calling a value "calibrated" without checking it differs from the hardcoded fallback.**
- **Raising sizing on a fresh-looking win rate.** λ ≈ 0.16. Re-run `calibration_study.py` first.
- **Arming a freeze review on a segment whose freeze stops its own evidence.** It returns
  stay-frozen forever.
- **Reading `data/cache/last_scan.json` for pre-gate evidence.** It is written **post**-gate, so at
  a 1.0 floor it holds nothing — the freeze suppresses exactly the rows under test.
- **Editing a pre-declared constant after seeing the data.** That is an override; label it as one.
- **A finding with no n and no date.** Unfalsifiable by next month.

---

## Related

| For | See |
|:---|:---|
| Designing the strategy the evidence is about | the `edge-radar-strategy-profiles` skill |
| The pre-declared-rule template and override labelling | [`launch-and-kill.md`](../edge-radar-strategy-profiles/references/launch-and-kill.md) |
| Routine performance reporting | the repo's `/edge-radar-analysis` skill |
| Auditing the code that produced the numbers | the repo's `/betting-logic-review` skill |
| Turning belief into a bet size | the `market-mechanics-betting` skill |
