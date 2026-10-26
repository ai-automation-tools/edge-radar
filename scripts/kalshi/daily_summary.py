"""
daily_summary.py — Morning P&L digest.

Joins yesterday's settlements (rolling 24h window) with currently open trade-log
positions to produce a short markdown report covering:

  * Yesterday's realized P&L (W/L, $, ROI), with per-sport breakdown
  * Currently open exposure (count, $ at risk, per-sport breakdown)
  * Today's pending events (open positions whose game datetime is today)
  * Optional live Kalshi balance line
  * 7-day rolling context (WR, $ P&L, Brier)

Empty-day behavior: the report is still produced (proof-of-life pattern).

Usage:
    python scripts/kalshi/daily_summary.py                       # to stdout
    python scripts/kalshi/daily_summary.py --save          # reports/Performance/daily_summary_*.md
    python scripts/kalshi/daily_summary.py --hours 24      # "yesterday" window (default 24h)
    python scripts/kalshi/daily_summary.py --no-bankroll         # skip live Kalshi balance fetch
"""

from __future__ import annotations

import argparse
import statistics
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import paths  # noqa: F401 -- path setup
from dotenv import load_dotenv
from ticker_display import (
    bet_type_from_ticker,
    parse_game_datetime,
    parse_matchup,
    sport_from_ticker,
)
from trade_log import get_filled_cost, load_settlement_log, load_trade_log

load_dotenv()


SETTLEMENTS_PATH = Path("data/history/kalshi_settlements.json")
TRADES_PATH = Path("data/history/kalshi_trades.json")
DEFAULT_OUT_DIR = Path("reports/Performance")


# ── Helpers ──────────────────────────────────────────────────────────────────


def _parse_iso(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def _fmt_money(x: float) -> str:
    sign = "-" if x < 0 else ""
    return f"{sign}${abs(x):.2f}"


def _fmt_signed(x: float) -> str:
    if x == 0:
        return "$0.00"
    return f"{'+' if x > 0 else '-'}${abs(x):.2f}"


def _fmt_roi(pnl: float, cost: float) -> str:
    if cost <= 0:
        return "—"
    return f"{pnl / cost * 100:+.1f}%"


def _sport_label(ticker: str) -> str:
    return sport_from_ticker(ticker) or "Other"


def _matchup_label(ticker: str) -> str:
    """parse_matchup() can return empty for non-game tickers; fall back to the raw ticker."""
    return parse_matchup(ticker) or ticker


def _is_today_in_pst(ticker: str, now: datetime) -> bool:
    """True when the ticker's game datetime falls on the same PST calendar day as `now`.

    Falls back to False on unparseable tickers (futures / prediction markets etc.).
    """
    label = parse_game_datetime(ticker)
    if not label:
        return False
    # parse_game_datetime returns "Apr 30 6:40pm" or "Apr 30" — match on month+day
    pst_now = now.astimezone(timezone(timedelta(hours=-8)))
    today_label = f"{pst_now.strftime('%b')} {pst_now.day}"
    return label.startswith(today_label)


# ── Data loading ─────────────────────────────────────────────────────────────


def load_recent_settlements(
    rows: list[dict] | None,
    hours: int,
    now: datetime,
) -> list[dict]:
    """Return settlements with settled_at within `hours` of `now`.

    Pass-through if `rows` is None (caller supplies them).  Sorted ascending.
    """
    if rows is None:
        rows = load_settlement_log()
    cutoff = now - timedelta(hours=hours)
    out: list[dict] = []
    for row in rows:
        ts_raw = row.get("settled_at")
        if not ts_raw:
            continue
        try:
            ts = _parse_iso(ts_raw)
        except ValueError:
            continue
        if ts >= cutoff:
            enriched = dict(row)
            enriched["_ts"] = ts
            out.append(enriched)
    out.sort(key=lambda r: r["_ts"])
    return out


def load_open_positions(rows: list[dict] | None) -> list[dict]:
    """Return open trade-log entries (filled, no settlement, not resting/error).

    Resting orders have no exposure (zero fills); excluded so $ at risk reflects
    only actually-filled positions.
    """
    if rows is None:
        rows = load_trade_log()
    out: list[dict] = []
    for t in rows:
        if t.get("closed_at"):
            continue
        if t.get("status") == "error":
            continue
        if t.get("fill_status") == "resting":
            continue
        if get_filled_cost(t) <= 0:
            continue
        out.append(t)
    return out


# ── Aggregations ─────────────────────────────────────────────────────────────


@dataclass
class YesterdaySlice:
    n: int
    wins: int
    pnl: float
    cost: float

    @property
    def losses(self) -> int:
        return self.n - self.wins

    @property
    def win_rate(self) -> float:
        return (self.wins / self.n * 100.0) if self.n else 0.0


@dataclass
class ExposureSlice:
    n: int
    cost: float


def aggregate_yesterday(
    settlements: list[dict],
) -> tuple[YesterdaySlice, dict[str, YesterdaySlice]]:
    overall = YesterdaySlice(0, 0, 0.0, 0.0)
    by_sport: dict[str, YesterdaySlice] = defaultdict(lambda: YesterdaySlice(0, 0, 0.0, 0.0))
    for s in settlements:
        cost = float(s.get("cost") or 0.0)
        pnl = float(s.get("net_pnl") or 0.0)
        won = bool(s.get("won"))
        sport = _sport_label(s.get("ticker", ""))

        overall.n += 1
        overall.wins += int(won)
        overall.pnl += pnl
        overall.cost += cost

        b = by_sport[sport]
        b.n += 1
        b.wins += int(won)
        b.pnl += pnl
        b.cost += cost
    return overall, dict(by_sport)


def aggregate_exposure(positions: list[dict]) -> tuple[ExposureSlice, dict[str, ExposureSlice]]:
    overall = ExposureSlice(0, 0.0)
    by_sport: dict[str, ExposureSlice] = defaultdict(lambda: ExposureSlice(0, 0.0))
    for t in positions:
        cost = get_filled_cost(t)
        sport = _sport_label(t.get("ticker", ""))
        overall.n += 1
        overall.cost += cost
        b = by_sport[sport]
        b.n += 1
        b.cost += cost
    return overall, dict(by_sport)


def filter_pending_today(positions: list[dict], now: datetime) -> list[dict]:
    return [t for t in positions if _is_today_in_pst(t.get("ticker", ""), now)]


def rolling_7d_context(rows: list[dict], now: datetime) -> dict | None:
    """Return WR / P&L / Brier over the trailing 7 days, or None if <5 settlements."""
    cutoff = now - timedelta(days=7)
    in_window = []
    for r in rows:
        ts_raw = r.get("settled_at")
        if not ts_raw:
            continue
        try:
            ts = _parse_iso(ts_raw)
        except ValueError:
            continue
        if ts >= cutoff:
            in_window.append(r)
    if len(in_window) < 5:
        return None
    n = len(in_window)
    wins = sum(1 for r in in_window if r.get("won"))
    pnl = sum(float(r.get("net_pnl") or 0.0) for r in in_window)
    cost = sum(float(r.get("cost") or 0.0) for r in in_window)
    # Two Brier scores, both in BET-SIDE space: outcome is "did this bet win".
    #
    # `market_price_at_entry` and `fair_value` are ALREADY side-relative — a NO
    # bought at 73c stores 0.73, not 0.27 (the settlement log satisfies
    # `fair_value - market_price_at_entry == edge_estimated` on every NO row).
    # An earlier version flipped the price for NO bets, which scored a 73c NO as
    # a 0.27 prediction against a win and inflated the reported Brier whenever a
    # NO settled (S18). Do not reintroduce the flip.
    #
    # They answer different questions and F3/S1b turn on the comparison, so
    # report them as a pair rather than one unlabelled "Brier":
    #   market — the venue's ask, the benchmark to beat
    #   model  — our fair value, the thing under test
    market_terms, model_terms = [], []
    for r in in_window:
        outcome = 1.0 if r.get("won") else 0.0
        price = r.get("market_price_at_entry")
        if price is not None:
            market_terms.append((float(price) - outcome) ** 2)
        fv = r.get("fair_value")
        if fv is not None:
            model_terms.append((float(fv) - outcome) ** 2)
    return {
        "n": n,
        "wins": wins,
        "win_rate": wins / n * 100.0,
        "pnl": pnl,
        "cost": cost,
        "roi": (pnl / cost * 100.0) if cost else 0.0,
        "brier_market": statistics.mean(market_terms) if market_terms else None,
        "brier_model": statistics.mean(model_terms) if model_terms else None,
        "brier_n_market": len(market_terms),
        "brier_n_model": len(model_terms),
    }


# ── Rendering ────────────────────────────────────────────────────────────────


def _format_today_pst(now: datetime) -> str:
    pst = now.astimezone(timezone(timedelta(hours=-8)))
    return pst.strftime("%Y-%m-%d")


def _format_window_label(now: datetime, hours: int) -> str:
    pst = now.astimezone(timezone(timedelta(hours=-8)))
    end = pst.strftime("%a %b %d %I:%M %p PST")
    start = (pst - timedelta(hours=hours)).strftime("%a %b %d %I:%M %p PST")
    return f"{start} → {end}"


def load_failed_orders(rows: list[dict] | None, hours: int, now: datetime) -> list[dict]:
    """Orders the venue REJECTED inside the window.

    Every other consumer of the trade log *filters* `status == "error"` rows --
    correct for exposure, but it meant a venue rejecting every order produced no
    signal at all. Kalshi geo-blocked this account on 2026-08-20 and the digest
    reported five clean days while 13 consecutive orders failed. Surfacing the
    count is the whole point of this function.
    """
    if rows is None:
        rows = load_trade_log()
    cutoff = now - timedelta(hours=hours)
    out: list[dict] = []
    for t in rows:
        if t.get("status") != "error":
            continue
        try:
            ts = _parse_iso(t.get("timestamp") or "")
        except ValueError:
            continue
        if ts >= cutoff:
            out.append(t)
    return out


def _error_reason(trade: dict) -> str:
    """Short human-readable reason from an error trade's raw API error blob.

    S3 (2026-08-26): delegates to `venue_eligibility.actionable_reason`, which
    keeps the END of the message. The old 110-char tail-truncation cut the
    2026-08-20 geo-block at **"Check you..."** -- 25 characters short of "Check
    your email for more details", the only actionable words in it, and the
    reason a two-minute fix took six days to find.
    """
    from venue_eligibility import actionable_reason

    return actionable_reason(trade.get("error") or "")


def load_post_kickoff_orders(rows: list[dict] | None, hours: int, now: datetime) -> list[dict]:
    """Live-money orders placed AFTER their event had already started.

    Gate 4.8 rejects these, but it **fails open** when neither
    `details["event_start_time"]` nor the ticker yields a dateable start, so a
    market whose start time nothing can name still gets through. That is the
    right call at gate time -- an unknown start is a sizing question, not a
    legality one -- and it is exactly why the condition needs a detector behind
    it as well as a gate in front of it.

    S23 (2026-09-16) is the case in point: the gate read start times out of the
    TICKER, which only moneyline series embed, so it never fired on a spread, a
    total, or any football market, and 10 NCAAF orders went in 26-122 minutes
    after kickoff on 09-12. Nothing noticed for four days. The book already
    carried two independent tells and no reader:
    `timestamp > event_start_time`, and `close_capture_reason: "missed"` on
    exactly those rows -- the t-minus-5 CLV window cannot be sampled for a game
    that has started. The first is the measurement; the second is corroboration
    for rows with no start time recorded, and is reported separately because on
    its own it has other causes (a capture task that simply did not run).

    Entries are `{"trade": ..., "minutes_late": float | None, "tell": str}`.
    """
    if rows is None:
        rows = load_trade_log()
    cutoff = now - timedelta(hours=hours)
    out: list[dict] = []
    for t in rows:
        if t.get("dry_run") or t.get("status") == "error":
            continue
        try:
            placed = _parse_iso(t.get("timestamp") or "")
        except ValueError:
            continue
        if placed < cutoff:
            continue

        start_raw = t.get("event_start_time") or (t.get("details") or {}).get("event_start_time")
        if start_raw:
            try:
                start = _parse_iso(str(start_raw))
            except ValueError:
                continue
            if placed > start:
                out.append(
                    {
                        "trade": t,
                        "minutes_late": (placed - start).total_seconds() / 60.0,
                        "tell": "event_start_time",
                    }
                )
            continue

        # No start time on the row: fall back to the corroborating tell. Weaker
        # -- flagged, never counted as proven -- because a capture task that did
        # not run produces the same flag.
        if t.get("close_capture_reason") == "missed":
            out.append({"trade": t, "minutes_late": None, "tell": "close_capture_reason=missed"})
    return out


def load_one_sided_series(
    settlements: list[dict],
    now: datetime,
    days: int = 60,
    min_n: int = 8,
    floors: dict[str, float] | None = None,
) -> list[dict]:
    """Series whose recent book is >= 90% one side AND loses to the model's own
    expectation by >= 1.5 sigma -- the S21 diagnostic, made mechanical.

    WC, MLB and MLS spreads were each switched off by hand only after this exact
    shape had cost money (2026-10-26 betting-logic review #6). A series whose
    floor is already >= 1.0 (switched off) is skipped so the alarm goes quiet
    once acted on.
    """
    from ticker_display import _detect_sport

    if floors is None:
        from app.config import get_config

        floors = get_config().per_sport.min_edge
    cutoff = now - timedelta(days=days)
    groups: dict[str, list[dict]] = {}
    for s in settlements:
        try:
            if _parse_iso(s.get("settled_at") or "") < cutoff:
                continue
        except ValueError:
            continue
        if s.get("fair_value") is None or float(s.get("contracts") or 0) <= 0:
            continue
        groups.setdefault((s.get("ticker") or "").split("-")[0], []).append(s)

    out = []
    for series, rows in groups.items():
        n = len(rows)
        yes = sum(1 for r in rows if r.get("side") == "yes")
        if n < min_n or max(yes, n - yes) / n < 0.9:
            continue
        sport, cat = _detect_sport(rows[0]["ticker"]), rows[0].get("category")
        if floors.get(f"{sport}_{cat}", floors.get(sport, 0.0)) >= 1.0:
            continue
        wins = sum(1 for r in rows if r.get("won"))
        exp = sum(float(r["fair_value"]) for r in rows)
        var = sum(float(r["fair_value"]) * (1 - float(r["fair_value"])) for r in rows)
        z = (wins - exp) / var**0.5 if var else 0.0
        if z <= -1.5:
            mkt = sum(float(r.get("market_price_at_entry") or 0) for r in rows)
            out.append(
                {
                    "series": series,
                    "n": n,
                    "one_side": max(yes, n - yes),
                    "wins": wins,
                    "model": exp,
                    "market": mkt,
                    "z": z,
                }
            )
    return sorted(out, key=lambda r: r["z"])


def render_report(
    settlements_yesterday: list[dict],
    open_positions: list[dict],
    pending_today: list[dict],
    rolling_7d: dict | None,
    balance_dollars: float | None,
    now: datetime,
    hours: int,
    failed_orders: list[dict] | None = None,
    post_kickoff: list[dict] | None = None,
    one_sided: list[dict] | None = None,
) -> str:
    today = _format_today_pst(now)
    overall, by_sport = aggregate_yesterday(settlements_yesterday)
    exp_overall, exp_by_sport = aggregate_exposure(open_positions)

    lines: list[str] = []
    lines.append(f"# Edge-Radar Daily Summary — {today}")
    lines.append("")
    lines.append(f"**Window:** {_format_window_label(now, hours)} (rolling {hours}h)")
    lines.append("")

    # ── Rejected orders ───────────────────────────────────────────────────────
    # First, above everything: a venue that won't accept orders makes every
    # number below it meaningless.
    if failed_orders:
        reasons: dict[str, int] = {}
        for t in failed_orders:
            r = _error_reason(t)
            reasons[r] = reasons.get(r, 0) + 1
        lines.append(
            f"> ⛔ **{len(failed_orders)} order(s) REJECTED by the venue** in this window."
        )
        for reason, count in sorted(reasons.items(), key=lambda kv: -kv[1]):
            lines.append(f"> - {count}x — {reason}")
        lines.append("")

    # ── One-sided losing series ───────────────────────────────────────────────
    # A series the model only ever bets one way, and loses to its own
    # expectation: a parameter, not a signal. Act before it costs more.
    for r in one_sided or []:
        lines.append(
            f"> 📉 **{r['series']}**: {r['one_side']}/{r['n']} bets one side over 60d, "
            f"{r['wins']} won vs {r['model']:.1f} model / {r['market']:.1f} market "
            f"(z {r['z']:+.1f}). Consider a floor or switch-off."
        )
    if one_sided:
        lines.append("")

    # ── Post-kickoff orders ───────────────────────────────────────────────────
    # Also above everything: with ALLOW_LIVE_BETS=false these should not exist,
    # and the NCAAF book split on this line ran -36.5% post-kickoff against
    # +13.6% pre-game. A hit here means Gate 4.8 failed open on a market whose
    # start time nothing could name.
    if post_kickoff:
        proven = [r for r in post_kickoff if r["tell"] == "event_start_time"]
        suspected = [r for r in post_kickoff if r["tell"] != "event_start_time"]
        if proven:
            lines.append(
                f"> 🚨 **{len(proven)} order(s) placed AFTER kickoff** in this "
                f"window, with `ALLOW_LIVE_BETS=false`."
            )
            for r in sorted(proven, key=lambda r: -(r["minutes_late"] or 0))[:6]:
                t = r["trade"]
                lines.append(
                    f"> - {_matchup_label(t.get('ticker', ''))} "
                    f"({_sport_label(t.get('ticker', ''))}, "
                    f"{(t.get('side') or '').upper()}, "
                    f"{_fmt_money(get_filled_cost(t))}) — "
                    f"+{r['minutes_late']:.0f} min late"
                )
        if suspected:
            lines.append(
                f"> ⚠️ {len(suspected)} order(s) carry no `event_start_time` and "
                f"missed the pre-game CLV capture — possible post-kickoff entry, "
                f"unproven (the capture task not running looks identical)."
            )
        lines.append("")

    # ── Yesterday ─────────────────────────────────────────────────────────────
    lines.append("## Yesterday")
    lines.append("")
    if overall.n == 0:
        lines.append("_No settlements in window._")
        lines.append("")
    else:
        lines.append(
            f"**{overall.n} settled** &nbsp;·&nbsp; "
            f"**{overall.wins}-{overall.losses}** ({overall.win_rate:.1f}% WR) &nbsp;·&nbsp; "
            f"**P&L {_fmt_signed(overall.pnl)}** &nbsp;·&nbsp; "
            f"ROI {_fmt_roi(overall.pnl, overall.cost)}"
        )
        lines.append("")
        if by_sport:
            lines.append("| Sport | N | W-L | WR | P&L | ROI |")
            lines.append("|---|---:|---:|---:|---:|---:|")
            for sport in sorted(by_sport.keys()):
                b = by_sport[sport]
                lines.append(
                    f"| {sport} | {b.n} | {b.wins}-{b.losses} | "
                    f"{b.win_rate:.0f}% | {_fmt_signed(b.pnl)} | {_fmt_roi(b.pnl, b.cost)} |"
                )
            lines.append("")

        # Top winner / loser
        winners = sorted(settlements_yesterday, key=lambda r: -float(r.get("net_pnl") or 0.0))
        losers = sorted(settlements_yesterday, key=lambda r: float(r.get("net_pnl") or 0.0))
        if winners and float(winners[0].get("net_pnl") or 0.0) > 0:
            w = winners[0]
            lines.append(
                f"- **Top win:** {_matchup_label(w.get('ticker', ''))} "
                f"({bet_type_from_ticker(w.get('ticker', ''))}, {(w.get('side') or '').upper()}) "
                f"{_fmt_signed(float(w.get('net_pnl') or 0.0))}"
            )
        if losers and float(losers[0].get("net_pnl") or 0.0) < 0:
            worst = losers[0]
            lines.append(
                f"- **Top loss:** {_matchup_label(worst.get('ticker', ''))} "
                f"({bet_type_from_ticker(worst.get('ticker', ''))}, "
                f"{(worst.get('side') or '').upper()}) "
                f"{_fmt_signed(float(worst.get('net_pnl') or 0.0))}"
            )
        lines.append("")

    # ── Current exposure ─────────────────────────────────────────────────────
    lines.append("## Open Exposure")
    lines.append("")
    if exp_overall.n == 0:
        lines.append("_No open positions._")
        lines.append("")
    else:
        lines.append(
            f"**{exp_overall.n} open positions** &nbsp;·&nbsp; "
            f"**{_fmt_money(exp_overall.cost)} at risk**"
        )
        lines.append("")
        if exp_by_sport:
            lines.append("| Sport | N | At risk |")
            lines.append("|---|---:|---:|")
            for sport in sorted(exp_by_sport.keys()):
                b = exp_by_sport[sport]
                lines.append(f"| {sport} | {b.n} | {_fmt_money(b.cost)} |")
            lines.append("")

    # ── Pending today ────────────────────────────────────────────────────────
    lines.append("## Pending Today")
    lines.append("")
    if not pending_today:
        lines.append("_No open positions on today's slate._")
        lines.append("")
    else:
        lines.append(f"**{len(pending_today)} positions** scheduled for today (PST):")
        lines.append("")
        lines.append("| When | Sport | Matchup | Side | Cost |")
        lines.append("|---|---|---|---|---:|")
        for t in pending_today:
            ticker = t.get("ticker", "")
            lines.append(
                f"| {parse_game_datetime(ticker)} | {_sport_label(ticker)} | "
                f"{_matchup_label(ticker)} | {(t.get('side') or '').upper()} | "
                f"{_fmt_money(get_filled_cost(t))} |"
            )
        lines.append("")

    # ── Bankroll + 7d context ────────────────────────────────────────────────
    lines.append("## Context")
    lines.append("")
    if balance_dollars is not None:
        lines.append(
            f"- **Balance:** {_fmt_money(balance_dollars)} &nbsp;·&nbsp; "
            f"yesterday Δ {_fmt_signed(overall.pnl)}"
        )
    else:
        lines.append(f"- Yesterday Δ: {_fmt_signed(overall.pnl)} _(balance unavailable)_")
    if rolling_7d:
        bm, bd = rolling_7d.get("brier_market"), rolling_7d.get("brier_model")
        # Model vs market on the same bets — the F3 comparison, not one bare number.
        brier_str = "Brier model {} vs market {}".format(
            f"{bd:.3f}" if bd is not None else "—",
            f"{bm:.3f}" if bm is not None else "—",
        )
        lines.append(
            f"- **7-day rolling:** {rolling_7d['n']} bets &nbsp;·&nbsp; "
            f"{rolling_7d['wins']}-{rolling_7d['n'] - rolling_7d['wins']} "
            f"({rolling_7d['win_rate']:.1f}% WR) &nbsp;·&nbsp; "
            f"P&L {_fmt_signed(rolling_7d['pnl'])} &nbsp;·&nbsp; "
            f"ROI {rolling_7d['roi']:+.1f}% &nbsp;·&nbsp; {brier_str}"
        )
    else:
        lines.append("- 7-day rolling: insufficient sample (<5 settlements)")
    lines.append("")

    return "\n".join(lines)


# ── Live Kalshi balance fetch (optional, swappable for tests) ────────────────


def _fetch_balance() -> float | None:
    """Best-effort live Kalshi balance fetch.  Returns None on any failure."""
    try:
        from kalshi_client import KalshiClient

        client = KalshiClient()
        bal = client.get_balance_dollars()
        # Kalshi balance dict has variants — try the common keys, else None
        if isinstance(bal, dict):
            for k in ("balance", "available_balance", "cash"):
                if k in bal:
                    return float(bal[k])
            # Some return nested under "balance" -> {"available": ...}
            return None
        return float(bal)
    except Exception:
        return None


# ── CLI ──────────────────────────────────────────────────────────────────────


def build_report(
    now: datetime,
    hours: int,
    settlements: list[dict] | None = None,
    trades: list[dict] | None = None,
    balance: float | None = None,
) -> str:
    """Public entry that pure-renders a report.  All I/O is parameterized for tests."""
    all_settlements = settlements if settlements is not None else load_settlement_log()
    all_trades = trades if trades is not None else load_trade_log()
    yesterday = load_recent_settlements(all_settlements, hours, now)
    open_positions = load_open_positions(all_trades)
    pending = filter_pending_today(open_positions, now)
    rolling = rolling_7d_context(all_settlements, now)
    failed = load_failed_orders(all_trades, hours, now)
    late = load_post_kickoff_orders(all_trades, hours, now)
    return render_report(
        yesterday,
        open_positions,
        pending,
        rolling,
        balance,
        now,
        hours,
        failed_orders=failed,
        post_kickoff=late,
        one_sided=load_one_sided_series(all_settlements, now),
    )


def _parse_args(argv: list[str]) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--hours", type=int, default=24, help="Rolling-window size for 'yesterday' (default: 24)"
    )
    ap.add_argument(
        "--save", action="store_true", help=f"Save to {DEFAULT_OUT_DIR}/daily_summary_YYYY-MM-DD.md"
    )
    ap.add_argument(
        "--out", type=Path, default=None, help="Explicit output path (overrides --save default)"
    )
    ap.add_argument("--no-bankroll", action="store_true", help="Skip live Kalshi balance fetch")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    now = datetime.now(timezone.utc)
    balance = None if args.no_bankroll else _fetch_balance()

    report = build_report(now, args.hours, balance=balance)

    out_path: Path | None = args.out
    if args.save and not out_path:
        DEFAULT_OUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = DEFAULT_OUT_DIR / f"daily_summary_{_format_today_pst(now)}.md"

    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report, encoding="utf-8")
        print(f"Wrote {out_path}")
    else:
        # Force UTF-8 on stdout so unicode in the report doesn't trip cp1252 on Windows
        sys.stdout.buffer.write(report.encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
