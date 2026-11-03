"""
shadow_book.py -- S21b: evidence for a frozen sport, at zero risk.

A freeze stops orders, so it also stops the settlements that would justify
lifting it. NFL never hit this: 19 positions were already in flight when S1
landed, and they settle into the S1b review. **NCAAF has no such stream** --
it was frozen (S21, 2026-09-13) holding nothing, so its settled count is pinned
at 11 forever, under `nfl_week1_review.MIN_SETTLEMENTS` (20). A review armed on
the NFL pattern would return branch C on every run until the end of time: the
"fresh, green, and wrong" shape the 2026-09-10 entry is about.

This is the missing exit ramp. A Brier head-to-head needs only
(model probability, market price, outcome) -- **it never needed a filled
order**. So the model keeps scoring the sport, the rows are logged, Kalshi
settles them anyway, and the freeze stays fully in force.

Where it taps matters. `data/cache/last_scan.json` is written POST-risk-gate,
so at a frozen sport's 1.0 floor it holds nothing -- the freeze would suppress
exactly the rows under test. `scan_all_markets()` applies only the GLOBAL
`min_edge_threshold`, never the per-sport `min_edge_for()` (that is Gate 3, in
the executor), so collecting upstream of the gates records what the MODEL said
while the gates stay the thing being judged.

## Why this beats waiting for settled bets

It tests the actual hypothesis. S21's finding is that every NCAAF edge was one
uncalibrated parameter -- `margin_stdev` 15.0 against a market pricing ~9.5 --
and `_MIN_CALIB_SAMPLES` (20/sport/category/30d) means real bets could never
fit it. `review` re-projects each row's stored consensus at a range of stdevs
and reports which minimises MODEL Brier. That is a direct read on the parameter,
from rows that cost nothing, and it needs no filled order at all.

## Deliberately NOT a decision

Nothing here writes `.env` or lifts a freeze; contrast `nfl_week1_review.py`,
which does and is pre-declared. Shadow rows are not real fills: no slippage, no
queue position, and survivorship differs from a live book. This measures
CALIBRATION, which is the thing a freeze is waiting on -- it does not measure
tradeability. Read it, then decide by hand.

Usage:
    python scripts/backtest/shadow_book.py collect --filter ncaafb
    python scripts/backtest/shadow_book.py settle
    python scripts/backtest/shadow_book.py review --sport ncaaf
    python scripts/backtest/shadow_book.py --self-check
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import paths  # noqa: F401  -- adds scripts/shared to sys.path

from scipy.stats import norm  # noqa: E402

SHADOW_LOG = Path(paths.DATA_DIR) / "history" / "shadow_book.json"

#: Multiples of each row's OWN stdev the sweep re-projects at. Relative, not
#: absolute: a fixed 7-18 grid (sized for football's 15.0) is meaningless for
#: MLB (4.025) or NHL totals (2.2), and silently reported "best fit 7.0".
SWEEP_SCALES = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4]

#: Below this the sweep is noise-fitting, not measurement. Printed either way,
#: but flagged, so a 6-row "optimum" is never read as a result.
MIN_SWEEP_ROWS = 25


# -- Store --------------------------------------------------------------------


def load_shadow() -> list[dict]:
    """Rows logged so far. A missing or corrupt file reads as empty, never raises.

    Mirrors `scan_cache`/`odds_cache`: this is an evidence log, and a parse
    error on it must never take down the scan that is trying to append to it.
    """
    if not SHADOW_LOG.exists():
        return []
    try:
        data = json.loads(SHADOW_LOG.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_shadow(rows: list[dict]) -> None:
    """Atomic replace -- a crash mid-write must not truncate the log."""
    SHADOW_LOG.parent.mkdir(parents=True, exist_ok=True)
    tmp = SHADOW_LOG.with_suffix(".tmp")
    tmp.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    os.replace(tmp, SHADOW_LOG)


def _key(row: dict) -> tuple[str, str]:
    return (row.get("ticker", ""), row.get("side", ""))


# -- collect ------------------------------------------------------------------


def collect(ticker_filter: str, date_filter: str | None = None, min_edge: float = 0.0) -> dict:
    """Score the sport and append rows not already logged.

    **First sighting wins.** A ticker re-scored tomorrow at a drifted price is
    NOT overwritten: the logged row is this book's entry, and rewriting it would
    let the market's later move leak into what the model is recorded as having
    claimed -- scoring the model against a price it never saw.
    """
    from kalshi_client import KalshiClient
    from edge_detector import scan_all_markets

    client = KalshiClient()
    opps = scan_all_markets(
        client,
        min_edge=min_edge,
        ticker_filter=ticker_filter,
        date_filter=date_filter,
        top_n=10_000,
    )

    rows = load_shadow()
    seen = {_key(r) for r in rows}
    now = datetime.now(timezone.utc).isoformat()
    added = 0
    for o in opps:
        row = {
            "ticker": o.ticker,
            "title": o.title,
            "category": o.category,
            "side": o.side,
            "market_price": o.market_price,
            "fair_value": o.fair_value,
            "edge": o.edge,
            "edge_source": o.edge_source,
            "confidence": o.confidence,
            "composite_score": o.composite_score,
            "details": o.details,
            "observed_at": now,
            "result": None,
            "won": None,
        }
        if _key(row) in seen:
            continue
        rows.append(row)
        seen.add(_key(row))
        added += 1

    save_shadow(rows)
    return {"scanned": len(opps), "added": added, "total": len(rows)}


# -- settle -------------------------------------------------------------------


def settle(limit: int | None = None) -> dict:
    """Fill in each open row's outcome from Kalshi. No money is involved.

    Kalshi reports `result` as "" until a market settles, so an unsettled
    lookup is a no-op and the row is retried on the next run.
    """
    from kalshi_client import KalshiClient, KalshiAPIError

    rows = load_shadow()
    pending = [r for r in rows if r.get("result") is None]
    if limit:
        pending = pending[:limit]
    if not pending:
        return {"checked": 0, "settled": 0, "open": 0}

    client = KalshiClient()
    settled = 0
    for r in pending:
        try:
            market = client.get_market(r["ticker"])
        except KalshiAPIError:
            continue  # closed, delisted, or off-shard -- retry next run
        m = market.get("market", market) if isinstance(market, dict) else {}
        result = (m.get("result") or "").strip().lower()
        if result not in ("yes", "no"):
            continue
        r["result"] = result
        r["won"] = r["side"] == result
        r["settled_at"] = datetime.now(timezone.utc).isoformat()
        settled += 1

    save_shadow(rows)
    return {
        "checked": len(pending),
        "settled": settled,
        "open": sum(1 for r in rows if r.get("result") is None),
    }


# -- the stdev sweep ----------------------------------------------------------


def _own_stdev(details: dict, category: str) -> float | None:
    try:
        return float(details["margin_stdev"] if category == "spread" else details["total_stdev"])
    except (KeyError, TypeError, ValueError):
        return None


def reproject(details: dict, category: str, side: str, stdev: float) -> float | None:
    """This row's probability had the model used `stdev` instead of its own.

    Inverts the same normal model `consensus_spread_prob` /
    `consensus_total_prob` use. The book's devigged implied probability is not
    stored directly -- `raw_median_implied` is PRE-devig and would reintroduce
    the overround this model removes -- so it is recovered from the stored
    (line, inferred mean, stdev) triple, which is exactly the devigged value by
    construction. Returns the YES probability; the caller flips for a NO row.

    Since B1 (2026-09-29) the stored mean is the weighted median of PER-BOOK
    means, so this re-projection around the median line is exact when the
    books share a line (the usual case) and approximate when they split.
    Rows recorded before B1 are exact as before.
    """
    try:
        old = float(details["margin_stdev"] if category == "spread" else details["total_stdev"])
        strike = float(details["kalshi_strike"])
        if category == "spread":
            line = -float(details["median_book_spread"])
            mean = float(details["inferred_mean_margin"])
        else:
            line = float(details["median_book_line"])
            mean = float(details["inferred_mean_total"])
    except (KeyError, TypeError, ValueError):
        return None
    if old <= 0 or stdev <= 0:
        return None

    # mean = line - old * ppf(1 - implied)  =>  recover the devigged implied
    z = (line - mean) / old
    mean_at = line - stdev * z
    p_yes = 1.0 - norm.cdf(strike, loc=mean_at, scale=stdev)
    p_yes = max(0.01, min(0.99, p_yes))
    return p_yes if side == "yes" else 1.0 - p_yes


def sweep(rows: list[dict]) -> list[dict]:
    """Model Brier at each multiple of the in-code stdev, over re-projectable rows.

    `stdev` in each result is the scale times the median in-code stdev, so a
    single-sport review reads in that sport's units.
    """
    usable = [
        r
        for r in rows
        if r.get("won") is not None
        and r.get("category") in ("spread", "total")
        and reproject(
            r.get("details") or {},
            r["category"],
            r["side"],
            _own_stdev(r.get("details") or {}, r["category"]) or 0,
        )
        is not None
    ]
    if not usable:
        return []
    owns = sorted(_own_stdev(r["details"], r["category"]) for r in usable)
    median_own = owns[len(owns) // 2]
    out = []
    for k in SWEEP_SCALES:
        ps, ys = [], []
        for r in usable:
            own = _own_stdev(r["details"], r["category"])
            p = reproject(r["details"], r["category"], r["side"], k * own)
            if p is None:
                continue
            ps.append(p)
            ys.append(1.0 if r["won"] else 0.0)
        if ps:
            out.append(
                {
                    "scale": k,
                    "stdev": k * median_own,
                    "n": len(ps),
                    "brier": sum((p - y) ** 2 for p, y in zip(ps, ys)) / len(ps),
                }
            )
    return out


def clustered_gain_ci(
    rows: list[dict], scale: float, n_boot: int = 2000
) -> tuple[float, float, float]:
    """Brier at 1.0x minus Brier at `scale`, with a 95% CI resampled by GAME.

    >0 means `scale` fits better. One game lists many strikes whose outcomes
    move together, so a row-level bootstrap overstates precision; the event
    ticker (everything before the last '-') is the resampling unit.
    """
    import random

    games: dict[str, list[float]] = {}
    for r in rows:
        if r.get("won") is None or r.get("category") not in ("spread", "total"):
            continue
        own = _own_stdev(r.get("details") or {}, r["category"])
        if not own:
            continue
        a = reproject(r["details"], r["category"], r["side"], own)
        b = reproject(r["details"], r["category"], r["side"], scale * own)
        if a is None or b is None:
            continue
        y = 1.0 if r["won"] else 0.0
        games.setdefault(r.get("ticker", "").rsplit("-", 1)[0], []).append(
            (a - y) ** 2 - (b - y) ** 2
        )
    keys = list(games)
    if not keys:
        return 0.0, 0.0, 0.0

    def mean(ks):
        vals = [x for k in ks for x in games[k]]
        return sum(vals) / len(vals)

    rng = random.Random(0)
    boots = sorted(mean([rng.choice(keys) for _ in keys]) for _ in range(n_boot))
    return mean(keys), boots[int(0.025 * n_boot)], boots[int(0.975 * n_boot) - 1]


# -- review -------------------------------------------------------------------


def _sport_of(ticker: str) -> str:
    from calibration_study import parse_ticker

    return parse_ticker(ticker)[0]


def review(sport: str | None = None) -> str:
    from calibration_study import bootstrap_ci, brier

    rows = [r for r in load_shadow() if r.get("won") is not None]
    if sport:
        rows = [r for r in rows if _sport_of(r["ticker"]) == sport]

    label = (sport or "all").upper()
    out = [f"# Shadow book review -- {label}", ""]
    if not rows:
        settled_any = any(r.get("won") is not None for r in load_shadow())
        out.append(
            f"No settled shadow rows for {label}. "
            + (
                "Run `collect`, then `settle` once the games are final."
                if not settled_any
                else "Rows exist for other sports -- check the --sport name "
                "matches `calibration_study.parse_ticker`."
            )
        )
        return "\n".join(out)

    ys = [1.0 if r["won"] else 0.0 for r in rows]
    pm = [r["fair_value"] for r in rows]
    pk = [r["market_price"] for r in rows]
    b_model, b_market = brier(pm, ys), brier(pk, ys)

    # S18: "Brier" alone is not a quantity. Always the pair, always labelled.
    out += [
        f"{len(rows)} settled shadow rows. **No money was at risk on any of them.**",
        "",
        f"- MARKET Brier (predicted = Kalshi price) : **{b_market:.4f}**",
        f"- MODEL  Brier (predicted = fair_value)   : **{b_model:.4f}**",
        f"- difference (market - model, >0 favours the model): {b_market - b_model:+.4f}",
    ]
    cirows = [{"p_model": a, "p_market": b, "y": y} for a, b, y in zip(pm, pk, ys)]
    lo, hi = bootstrap_ci(
        cirows,
        lambda rs: (
            brier([r["p_market"] for r in rs], [r["y"] for r in rs])
            - brier([r["p_model"] for r in rs], [r["y"] for r in rs])
        ),
    )
    out += [
        f"- 95% CI on that difference: [{lo:+.4f}, {hi:+.4f}]"
        + (
            "  -- straddles zero, so this is directional only"
            if lo <= 0 <= hi
            else "  -- excludes zero"
        ),
        "",
    ]

    realised = sum(ys) / len(ys)
    out += [
        f"Model claimed {sum(pm) / len(pm):.1%} on average; "
        f"{realised:.1%} actually happened. "
        f"Market said {sum(pk) / len(pk):.1%}.",
        "",
        "## Which margin/total stdev fits best?",
        "",
    ]

    # Spreads and totals are separate parameters (margin_stdev vs total_stdev),
    # so each gets its own sweep. A pooled sweep can call 1.0x best while the
    # two halves want opposite moves -- NCAAF 2026-11-03: spreads ~0.8x, totals ~1.2x.
    any_sweep = False
    for cat in ("spread", "total"):
        crows = [r for r in rows if r.get("category") == cat]
        sw = sweep(crows)
        if not sw:
            continue
        any_sweep = True
        cy = [1.0 if r["won"] else 0.0 for r in crows]
        best = min(sw, key=lambda d: d["brier"])
        out += [
            f"### {cat.title()}s ({'margin' if cat == 'spread' else 'total'}_stdev)",
            "",
            f"{len(crows)} rows. "
            f"MARKET Brier **{brier([r['market_price'] for r in crows], cy):.4f}**, "
            f"MODEL Brier **{brier([r['fair_value'] for r in crows], cy):.4f}**.",
            "",
            "| x code | ~stdev | model Brier |",
            "|------:|------:|------------:|",
        ]
        for d in sw:
            mark = "  <- best" if d is best else ("  <- in code" if d["scale"] == 1.0 else "")
            out.append(f"| {d['scale']:.1f} | {d['stdev']:.2f} | {d['brier']:.4f}{mark} |")
        out += [
            "",
            f"Best fit **{best['scale']:.1f}x** the in-code stdev "
            f"(~{best['stdev']:.2f}) over {best['n']} rows.",
        ]
        if best["scale"] != 1.0:
            g, glo, ghi = clustered_gain_ci(crows, best["scale"])
            out.append(
                f"Gain over 1.0x: {g:+.4f} Brier, 95% game-clustered CI [{glo:+.4f}, {ghi:+.4f}]"
                + (
                    " -- straddles zero; keep collecting before changing the stdev."
                    if glo <= 0 <= ghi
                    else " -- excludes zero."
                )
            )
        if best["n"] < MIN_SWEEP_ROWS:
            out.append(
                f"**Under {MIN_SWEEP_ROWS} rows -- treat this as a shape, not a "
                f"number.** Keep collecting before changing a stdev on it."
            )
        out.append("")
    if not any_sweep:
        out.append("No rows carry the consensus detail the sweep needs.")
    return "\n".join(out).rstrip()


# -- self-check ---------------------------------------------------------------


def self_check() -> None:
    """The reprojection is the only real logic here, so it is what gets pinned."""
    # A row re-projected at its OWN stdev must reproduce its own probability --
    # otherwise the recovered implied is wrong and every sweep column is wrong.
    d = {
        "margin_stdev": 15.0,
        "kalshi_strike": 7.5,
        "median_book_spread": -5.5,
        "inferred_mean_margin": 5.5,
    }
    same = reproject(d, "spread", "yes", 15.0)
    direct = 1.0 - norm.cdf(7.5, loc=5.5, scale=15.0)
    assert abs(same - direct) < 1e-9, (same, direct)

    # A tighter stdev must pull a not-yet-covered strike DOWN: less spare
    # probability mass above a strike the mean has not reached. This is the
    # S21 mechanism, so it is asserted rather than assumed.
    assert reproject(d, "spread", "yes", 9.5) < same

    # NO is the complement of YES at every stdev.
    assert (
        abs(reproject(d, "spread", "no", 12.0) + reproject(d, "spread", "yes", 12.0) - 1.0) < 1e-9
    )

    # Totals travel the other branch and must work the same way.
    t = {
        "total_stdev": 14.0,
        "kalshi_strike": 55.0,
        "median_book_line": 52.0,
        "inferred_mean_total": 52.0,
    }
    assert (
        abs(reproject(t, "total", "yes", 14.0) - (1.0 - norm.cdf(55.0, loc=52.0, scale=14.0)))
        < 1e-9
    )

    # Junk details must return None, never a plausible-looking number.
    assert reproject({}, "spread", "yes", 15.0) is None
    assert reproject({"margin_stdev": 0}, "spread", "yes", 15.0) is None
    # The sweep is relative: a row at 4.025 is swept around 4.025, not 7-18,
    # and the 1.0x column reproduces the row's own probability.
    m = dict(
        d, margin_stdev=4.025, kalshi_strike=2.5, median_book_spread=-1.5, inferred_mean_margin=1.0
    )
    sw = sweep([{"won": True, "category": "spread", "side": "yes", "details": m}])
    at1 = next(x for x in sw if x["scale"] == 1.0)
    assert abs(at1["stdev"] - 4.025) < 1e-9
    assert abs(at1["brier"] - (reproject(m, "spread", "yes", 4.025) - 1.0) ** 2) < 1e-9

    # Clustered gain: 1.0x vs itself is exactly zero, and a row whose outcome
    # sits above the 1.0x probability gains from a scale that raises it.
    one = [{"won": True, "category": "spread", "side": "yes", "details": d, "ticker": "G1-X"}]
    assert clustered_gain_ci(one, 1.0) == (0.0, 0.0, 0.0)
    assert clustered_gain_ci(one, 1.4)[0] > 0  # wider stdev lifts an uncovered strike toward 1
    print("shadow_book self-check: OK")


def main() -> int:
    p = argparse.ArgumentParser(description="Shadow book: evidence for a frozen sport.")
    p.add_argument("--self-check", action="store_true")
    sub = p.add_subparsers(dest="cmd")

    c = sub.add_parser("collect", help="scan a sport and log the model's rows")
    c.add_argument("--filter", default="ncaafb", help="scanner filter shortcut")
    c.add_argument("--date", default=None, help="YYYY-MM-DD, today, tomorrow")
    c.add_argument(
        "--min-edge",
        type=float,
        default=0.0,
        help="0.0 (default) logs every scored row, not just edges",
    )

    s = sub.add_parser("settle", help="fill in outcomes from Kalshi")
    s.add_argument("--limit", type=int, default=None)

    r = sub.add_parser("review", help="Brier pair + stdev sweep")
    r.add_argument("--sport", default="ncaaf")
    r.add_argument("--save", action="store_true")

    a = p.parse_args()
    if a.self_check:
        self_check()
        return 0

    if a.cmd == "collect":
        st = collect(a.filter, a.date, a.min_edge)
        print(
            f"scanned {st['scanned']}, added {st['added']} new, "
            f"{st['total']} in the shadow book"
        )
    elif a.cmd == "settle":
        st = settle(a.limit)
        print(f"checked {st['checked']}, settled {st['settled']}, " f"{st['open']} still open")
    elif a.cmd == "review":
        text = review(a.sport)
        print(text)
        if a.save:
            out = Path(paths.PROJECT_ROOT) / "reports" / "Performance"
            out.mkdir(parents=True, exist_ok=True)
            f = out / f"shadow-book-{a.sport}-{datetime.now().date()}.md"
            f.write_text(text, encoding="utf-8")
            print(f"\nsaved -> {f}")
    else:
        p.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
