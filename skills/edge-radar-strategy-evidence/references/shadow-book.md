# The shadow book — evidence at zero risk

`scripts/backtest/shadow_book.py`. The only tool here that **generates** evidence instead of reading
it, and the answer to the one structural problem a freeze creates.

---

## 1. The problem it solves

**A freeze stops orders, so it also stops the settlements that would justify lifting it.**

- NFL escaped this by accident: 19 positions were already in flight when its freeze landed, and they
  settled into the review.
- NCAAF did not. It was frozen holding **nothing**, pinning its settled count at **11** forever,
  under the review template's bar of **20**. A review armed on the NFL pattern would return
  stay-frozen on every run until the end of time.

The same trap catches any heavily-gated segment, not just a frozen one: a per-sport floor at 2–3x
global, a tight price floor, a strict liquidity gate — each suppresses exactly the population under
judgement.

**The way out:** a Brier head-to-head needs only **(model probability, market price, outcome)**. It
**never needed a filled order.** So let the model keep scoring the sport, log the rows, let Kalshi
settle them anyway, and leave the freeze fully in force.

---

## 2. Use it

```bash
python scripts/backtest/shadow_book.py collect --filter ncaafb        # score and log
python scripts/backtest/shadow_book.py collect --filter ncaafb --date today
python scripts/backtest/shadow_book.py settle                          # fill in outcomes
python scripts/backtest/shadow_book.py review --sport ncaaf --save     # the read
python scripts/backtest/shadow_book.py --self-check
```

- **`collect`** scores the sport and appends rows not already logged, keyed so re-running is
  idempotent. It scans with `max_per_game=None` — **every strike**, since the default 2-per-game cap
  keeps only the highest-edge strikes and a "pre-gate" population is only pre-gate if nothing ranked it. `--min-edge` defaults to **0.0** — you want everything the model said, not what would
  have passed.
- **`settle`** fills in each open row's outcome from Kalshi. **No money is involved at any point.**
- **`review`** prints the model/market Brier pair plus a stdev sweep, **split into spreads
  (`margin_stdev`) and totals (`total_stdev`)** — a pooled sweep can call 1.0x best while the two halves
  want opposite moves (NCAAF 2026-11-03: spreads ~0.8x, totals ~1.2x). Each best fit carries a
  **game-clustered** 95% CI on its gain over 1.0x, since one game's strikes move together; if it
  straddles zero, keep collecting.
- Schedule `collect` daily and `settle` alongside the normal settle task; the evidence accrues on
  its own while the freeze holds.

---

## 3. Where it taps, and why that is the whole design

| Source | Written | Usable for this? |
|:---|:---|:---|
| `data/cache/last_scan.json` | **post**-risk-gate | **No.** At a frozen sport's 1.0 floor it holds nothing — the freeze suppresses exactly the rows under test. |
| `scan_all_markets()` | pre-gate | **Yes.** It applies only the **global** `min_edge_threshold`, never the per-sport `min_edge_for()` (that is Gate 3, in the executor). |

Collecting upstream of the gates records **what the model said**, while the gates stay the thing
being judged. Reading `last_scan.json` instead would measure the freeze.

---

## 4. Fitting a parameter it could never fit from live bets

`review` re-projects each stored row's consensus at a range of candidate stdevs and reports which
minimises **model** Brier. (Rows priced by the discrete NFL model, `margin_model: nfl_discrete`, are
skipped — the inversion is normal-only; that fit lives in `fit_nfl_margin.py`.) This is the part that cannot be done any other way.

The motivating case: all 11 NCAAF bets ever placed were YES on "team covers a big alternate spread",
and the entire claimed edge was one uncalibrated `margin_stdev` — **15.0 in the code against a market
pricing ~9.5**. Solving per bet for the value that reconciles model with market gives a median of
9.5, and the derivation is strike-independent (`stdev* = 15 * ppf(1-fv) / ppf(1-px)`), so it is one
disagreement restated eleven times, not eleven observations.

And it could never have been fixed from live bets: `_MIN_CALIB_SAMPLES` is **20 per
sport/category/30d**, and 11 lifetime settles never reach it. The sweep reads the parameter directly,
from rows that cost nothing.

> **Generalise:** whenever a claimed edge reduces to one parameter, the shadow book can fit that
> parameter without risking a dollar. Ask "what number, changed, would make the model agree with the
> market?" — if there is exactly one, that is the finding.

---

## 5. What it deliberately is not

- **It writes nothing.** No `.env`, no freeze lifted, no floor moved. Contrast the pre-declared
  review, which does and is allowed to because its rule was written first. **Read the shadow book,
  then decide by hand** — and label that decision as an operator call.
- **It measures calibration, not tradeability.** Shadow rows are not fills: **no slippage, no queue
  position**, and survivorship differs from a live book. A sport can price beautifully in the shadow
  book and still be untradeable on a 20c-wide market.
- **It is not a backtest.** It records the model's forward statements from now on; it cannot
  reconstruct what the model would have said last month.

---

## 6. Reading the output

1. **The Brier pair, labelled** — model vs market, with the CI on the difference. Model worse than
   market is the *overall* pattern (6 of 6 months), so a sport that beats the market is the signal
   worth acting on.
2. **The stdev sweep** — where model Brier minimises. A minimum far from the code's value is a
   parameter finding; a flat sweep means the parameter is not what is wrong.
3. **Side balance** — if every shadow row is the same side, you are looking at a parameter, not a
   signal, and the sweep will tell you which one.
4. **n, and the date range** — record both with any conclusion. A shadow book accumulates fast
   enough that "n=40 over three weeks in September" and "n=40 over one weekend" are different
   claims about a sport with weekly seasonality.

---

## 7. When to reach for it

| Situation | Shadow book? |
|:---|:---|
| Sport frozen at a ≥1.0 floor | **Yes** — it is the only exit ramp. |
| Segment gated so hard it places ~1 bet a week | **Yes** — live evidence will take years. |
| A claimed edge reduces to one uncalibrated parameter | **Yes** — sweep it. |
| New market/sport, before any money | **Yes** — cheapest possible cold start. |
| Profile in dry-run | **No** — dry-run rows already log identically to live. Use those. |
| Deciding whether something is *tradeable* (spread, fill quality) | **No** — it models neither. |
| Reconstructing the past | **No** — it is forward-only. |
