# Which knob moves which price band

Every knob a profile can set, the band it binds in, and what it does *nothing* for. Read this
before writing `.env.<name>` — a profile whose knob does not bind in its own price band is a month
of dry-run rows that say nothing.

---

## The two sizing lanes

Sizing is `max(flat floor, Kelly)`, and which term wins is decided by price alone.

```
contracts = max( round(UNIT_SIZE / price),              # the flat floor
                 kelly(edge, price) * KELLY_FRACTION )  # Kelly, / batch_size
```

with **Kelly = `edge / (1 - price)`**. The `(1 - price)` divisor is the part that makes the lanes
split; without it favourites are under-sized 2.5x at 60c and 5x at 80c, and the flat floor collapses
nearly every bet above ~60c to a single contract.

| Price | Flat floor at `UNIT_SIZE=1.00` | Which term wins |
|---:|---:|:---|
| 0.08 | 13 contracts | **floor** — Kelly is nowhere near |
| 0.20 | 5 | **floor** |
| 0.30 | 3 | floor, marginally |
| 0.50 | 2 | either, depending on edge |
| 0.65 | 2 | **Kelly** |
| 0.80 | 1 | **Kelly**, by a wide margin |

**Consequence for a profile:**

- A **longshot** strategy lives below ~30c → its knob is `UNIT_SIZE`. `KELLY_FRACTION` is inert
  there and changing it produces an identical book.
- A **favourites** strategy lives above ~60c → its knob is `KELLY_FRACTION`. `UNIT_SIZE` is
  irrelevant.
- A strategy that spans both is two strategies. Split it, or accept that you cannot attribute the
  result to either knob.

---

## Selection knobs — what the book is allowed to buy

These change *which rows survive the gates*, not their size. They are the sharpest instrument a
profile has, because a rejected row costs nothing and teaches nothing.

| Knob | Gate | Binds | Use it for |
|:---|:---|:---|:---|
| `MIN_MARKET_PRICE` | 3.5 | the cheap end | Longshot / lottery-ticket books. The single knob that defines "how cheap is too cheap". |
| `MAX_MARKET_PRICE` | 3.55 | the expensive end | Cost/payout ceiling. A 76c bet to win $1 is rejected at 0.75; 75c passes. |
| `MIN_EDGE_THRESHOLD_<SPORT>` | 3 | one sport | Sport-specific angles, pilot floors, and freezes. **≥ 1.0 can never be cleared, so it is the idiom for switching a sport off** — the executor reports `sport_disabled`. |
| `MIN_EDGE_THRESHOLD_<SPORT>_<CATEGORY>` | 3 | one sport's market type | `game`, `spread` or `total`. Narrows a sport floor to one market type and wins over the sport-wide value (`min_edge_for()`). Live example: `MIN_EDGE_THRESHOLD_MLB_SPREAD` went to 0.08 after MLB spreads went 0-9 while totals ran 11-2 on the same 0.03 floor, then to 1.0 (off) on 2026-10-03; `MIN_EDGE_THRESHOLD_NFL_SPREAD=1.0` has been off since 2026-11-03 while the discrete NFL margin model is judged in the shadow book. |
| `MIN_EDGE_THRESHOLD` | 3 | everything | Rarely right in a profile: it moves the whole book, so nothing is attributable. |
| `MIN_COMPOSITE_SCORE` | 4 | everything | A blunt quality bar. Remember every composite scales edge as `min(edge / 0.01, 10)`. |
| `MIN_CONFIDENCE` | 4.5 | everything | Note confidence bumps are **one-way, down only** — `supports` is a no-op. |
| `MAX_BID_ASK_SPREAD` / `MIN_MARKET_VOLUME_24H` | 3.6 | illiquid books | Tightening is defensible; **loosening is how you pay the illiquidity penalty the gate exists to avoid**. |
| `MAX_DAYS_TO_EVENT_FOR_GAME_MARKETS` | 3.7 | lead time | Caps how far ahead a *game* may be bought. Futures are exempt by category. Lead time, not sport, was the mechanism behind the book that reached 31% of bankroll. |
| `MAX_PER_EVENT_FUTURES` | 6 | futures only | Futures outcomes **partition** one event (three underdogs in a championship) rather than doubling down, so they earn a wider cap than three sides of one game. |
| `SERIES_DEDUP_HOURS[_SPORT]` | 7 | repeat matchups | MLB/NHL series cycle on consecutive days — 72h, not 48. |

---

## Exposure knobs — how much of the bankroll this book may hold

| Knob | Gate | Note |
|:---|:---|:---|
| `MAX_OPEN_EXPOSURE_PCT` | 2b | Total open at-risk / **equity** (cash + position value), not cash. Every dollar bought subtracts from cash *and* adds to exposure, so a cash denominator climbs at twice the rate of the real risk. |
| `MAX_SEGMENT_EXPOSURE_PCT` | 2b | The per-sport companion. **The pair is the point** — a portfolio cap alone lets one sport hold all of it; a segment cap alone lets N sports each hold their share. |
| `MAX_BET_SIZE` | 8 | Hard per-bet cap. |
| `MAX_BET_RATIO` | 9 | Per-bet cap as a multiple of the batch median. Binds one batch only. |
| `MAX_DAILY_LOSS` | 1 | **Reads the trade log, scoped by `for_profile()`.** Each book has its own. |

Gate 2b is the only gate in the chain that measures a **standing total** — the rest count rows, bind
one event, or bind one batch. It also runs **only at entry**, so a book already over the ceiling is
not re-checked.

> **Gate 2b rejects when a ceiling is already breached and trims otherwise.** Reject-only would let
> a book at 49.9% add a full `MAX_BET_SIZE`. Trims use `max(1, …)`, so a bounded cent-scale
> overshoot is by design — an unfillable 0-contract order is the worse failure.

---

## Side knobs — YES vs NO

Over 380 settled bets **NO runs -7.7% ROI against YES's +22.4%**, and YES beats NO *within every
shared price band*. The bleed concentrates at/above 50c (n=68, $90 staked, -11.3%). The 35–50c
pocket is the one profitable NO band (+5.3%, n=55) and is deliberately left alone.

| Knob | Effect |
|:---|:---|
| `NO_SIDE_MIN_EDGE_GLOBAL` | Effective edge floor on **any** NO bet = `max(per-sport floor, this)`. |
| `NO_SIDE_FAVORITE_THRESHOLD` / `NO_SIDE_MIN_EDGE` | Cheap-NO bets face an elevated bar *and* need `confidence=high`. |
| `NO_SIDE_KELLY_PRICE_FLOOR` / `_CEILING` / `_MULTIPLIER` | Half-Kelly outside `[floor, ceiling)`. **Damped, not gated** — that population is +4.8% in one season-half and -16.0% in the next, too uneven for a hard reject, and halving keeps it generating data. |

**A NO-side profile is a legitimate strategy shape**, but it is the one where the settled book
already has a strong prior. Any NO-heavy profile needs to state, up front, why it expects to beat
-7.7%.

---

## Knobs a profile should almost never touch

| Knob | Why not |
|:---|:---|
| `KALSHI_FEE_RATE` | The fee is real: `ceil(0.07 × C × P × (1-P))` per order, ~1.02c/contract against a 3–4c floor. Setting it to 0 does not save money, it hides a quarter to a third of the edge you are screening on. |
| `ALLOW_PREDICTION_BETS` / `ALLOW_LIVE_BETS` | These open whole *categories*, not a strategy. If a profile is about crypto or in-play, say so and treat it as a market-onboarding question, not a knob. |
| `KELLY_EDGE_CAP` / `KELLY_EDGE_DECAY` | The soft cap exists because claimed edge is roughly 5x optimistic (the Brier-optimal weight on claimed edge is **λ ≈ 0.16**). Raising it multiplies a known bias. |
| `CALIBRATION_STDEVS_TTL_DAYS` | Calibration should be identical across books, or a comparison measures the calibration rather than the strategy. |
| Anything in the base `.env` you meant to change globally | Change it globally. An overlay is for what *differs*. |

---

## The sanity check before you commit the file

Run a dry scan and read the **rejection reasons**:

```bash
python scripts/scan.py sports --profile <name> --filter <f> --date today
```

- Every rejection on **edge** → your knob is not binding. The profile is currently a no-op.
- Rejections on **your** knob (`price below floor`, `per-event cap`, `sport_disabled`) → it binds.
  This is the only evidence that the profile is a different strategy at all.
- **Zero candidates** → you cannot tell the two apart. Widen the filter or the date window before
  concluding anything.
