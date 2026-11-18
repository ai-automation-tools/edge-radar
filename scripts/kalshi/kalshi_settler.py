"""
kalshi_settler.py
Settlement tracker for Kalshi positions.

Polls the Kalshi API for settled markets, matches them to our trade log,
calculates realized P&L, and updates records. Also generates performance
reports to validate whether our edge detection is working.

Usage:
    python scripts/kalshi_settler.py settle           # Update trade log with settlements
    python scripts/kalshi_settler.py report            # P&L and performance summary
    python scripts/kalshi_settler.py report --detail    # Per-trade breakdown
"""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

# Put scripts/shared on sys.path so `import paths` works without the venv .pth (fresh clone).
if (_SHARED := str(Path(__file__).resolve().parents[1] / "shared")) not in sys.path:
    sys.path.insert(0, _SHARED)
import paths  # noqa: F401,E402

# Shared imports
from trade_log import (
    load_trade_log,
    save_trade_log,
    load_settlement_log,
    save_settlement_log,
    trade_log_lock,
    settlement_revenue_dollars,
    get_filled_contracts,
    get_filled_cost,
    recover_journal,
    recover_pending,
    set_row_fills,
)

from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from kalshi_client import KalshiClient
from logging_setup import setup_logging
from fees import taker_fee

# ── Setup ─────────────────────────────────────────────────────────────────────
load_dotenv()
log = setup_logging("kalshi_settler")
console = Console()


# ── Fees ──────────────────────────────────────────────────────────────────────

# The fee field on a Kalshi v2 fill. `fee_cost` is the real one, verified
# against the live endpoint on 2026-09-16; the rest are kept only so a rename
# degrades to a stale-but-present reading rather than a silent zero. Order
# matters -- first key PRESENT wins, not first key truthy, because a genuine
# maker fill reports "0.000000" and must be recorded as a measured zero.
_FILL_FEE_KEYS = ("fee_cost", "fee_dollars", "taker_fee_dollars", "fee")


def _fill_fee(fill: dict) -> float | None:
    """Fee charged on one fill, or None if the payload names it something new.

    None is not zero. A missing fee field means the endpoint changed shape and
    the caller must NOT record a measured zero over it -- that is exactly the
    bug this function exists to prevent.
    """
    for key in _FILL_FEE_KEYS:
        if key in fill:
            try:
                return float(fill[key] or 0)
            except (TypeError, ValueError):
                return None
    return None


def fetch_fill_fees(client: KalshiClient, max_pages: int = 20) -> dict[str, float]:
    """Map order_id -> total fees actually charged, from `/portfolio/fills`.

    The Kalshi **v2 create-order response carries no fee fields** (and no
    `status` either -- hence the 129 `"unknown"` rows in the log), so
    `log_trade` has always recorded `taker_fees: "0"`. Settlement then computed
    `net_pnl = revenue - cost - 0`, understating the true cost of every trade by
    ~1c per contract. The fills endpoint is the authoritative record, so read it
    here at settle time rather than trusting the create response.

    **The field is `fee_cost`.** This read `fee_dollars or taker_fee_dollars or
    fee` -- three names the endpoint has never used -- so it resolved to 0 on
    every fill and stamped 67 rows `fee_source: "fills_api", taker_fees: 0.0`:
    a modelled number wearing a measured label. It looked defensible ("Kalshi
    charges no maker fee and we post limit orders"), and it was not: 136 of 138
    orders in the book carry a nonzero `fee_cost` and 133 are flagged
    `is_taker`. A marketable limit at the ask crosses the spread, so it fills as
    TAKER; posting a limit order is not the same fact as resting on the book.
    P&L was never wrong -- `trade_fees()` falls back to the model on a zero --
    but the label said measured, and the real $4.11 never entered the log.

    Returns {} on any API failure -- callers fall back to the modelled fee.
    """
    fees: dict[str, float] = {}
    cursor = None
    unnamed = 0
    try:
        for _ in range(max_pages):
            resp = client.get_fills(limit=200, cursor=cursor)
            for fill in resp.get("fills", []):
                oid = fill.get("order_id")
                if not oid:
                    continue
                amount = _fill_fee(fill)
                if amount is None:
                    unnamed += 1
                    continue
                fees[oid] = round(fees.get(oid, 0.0) + amount, 6)
            cursor = resp.get("cursor", "")
            if not cursor:
                break
    except Exception as e:
        log.warning("Could not fetch fills for fee backfill: %s", e)
        return {}
    if unnamed:
        log.warning(
            "%d fills carried no recognised fee field (tried %s) -- the payload "
            "has been renamed again; falling back to the modelled fee for those",
            unnamed,
            ", ".join(_FILL_FEE_KEYS),
        )
    return fees


def trade_fees(trade: dict) -> float:
    """Fees for a trade: recorded if present, otherwise the modelled taker fee.

    Falling back to the model rather than to zero is the point -- a zero here is
    what made the whole fee cost invisible. `KALSHI_FEE_RATE=0` disables the
    model and restores the old behaviour.
    """
    recorded = float(trade.get("taker_fees") or 0) + float(trade.get("maker_fees") or 0)
    if recorded > 0:
        return recorded
    return taker_fee(
        get_filled_contracts(trade) or 0, float(trade.get("market_price_at_entry") or 0)
    )


# ── Settlement Logic ──────────────────────────────────────────────────────────


def _yes_payout(result: str, settlement: dict) -> float | None:
    """Dollars one YES contract paid, or None when the settlement doesn't say.

    Settlements carry `value` (cents); the market-status fallback carries the
    market's `settlement_value_dollars`.
    """
    if result in ("yes", "no"):
        return 1.0 if result == "yes" else 0.0
    if settlement.get("value") is not None:
        return float(settlement["value"]) / 100
    if settlement.get("settlement_value_dollars") is not None:
        return float(settlement["settlement_value_dollars"])
    return None


def calculate_pnl(trade: dict, settlement: dict) -> dict:
    """
    Calculate realized P&L for a settled trade.

    For binary contracts:
    - YES contract pays $1.00 if result is "yes", $0.00 if "no"
    - NO contract pays $1.00 if result is "no", $0.00 if "yes"

    P&L = revenue - cost - fees
    """
    side = trade.get("side", "")
    result = settlement.get("market_result", "")
    contracts = get_filled_contracts(trade)
    cost = get_filled_cost(trade)
    fees = trade_fees(trade)

    # Revenue is computed PER-TRADE from this trade's own filled contracts, NOT
    # from the settlement's position-level `revenue` aggregate: a winning binary
    # contract pays exactly $1.00. Kalshi settlements are keyed per-market, so if
    # two trades share a ticker they both matched the same settlement — applying
    # its aggregate revenue to each double-counted the position's payout (review
    # #8). Deriving revenue from each trade's own filled contracts is additive
    # and, for a single trade, identical to the aggregate (contracts x $1.00).
    #
    # ER-15: only yes/no is a win or a loss. `scalar` settles each YES contract
    # at `value` cents (NO gets the rest); anything else (void, blank) is booked
    # as a refund of cost, not a total loss. Neither is a prediction outcome, so
    # `won` is None and the calibration readers skip the row.
    yes_payout = _yes_payout(result, settlement)
    if yes_payout is None:
        won_bet = None
        revenue_dollars = cost
        log.warning(
            "%s settled %r with no payout value; booked as a refund", trade.get("ticker"), result
        )
    else:
        won_bet = side == result if result in ("yes", "no") else None
        payout = yes_payout if side == "yes" else 1.0 - yes_payout
        revenue_dollars = round(contracts * payout, 4)

    net_pnl = revenue_dollars - cost - fees

    return {
        # `won` is whether the PREDICTION was right, not whether the row turned a
        # profit -- win rate and Brier both want the former, and net_pnl already
        # carries the latter. The old `revenue_dollars > cost` conflated them and
        # collapsed to `0 > 0` on a zero-fill row, so every resting order that
        # settled was logged as a loss regardless of outcome. calibration_study's
        # `load_rows` does not filter on fills, so those phantom losses fed
        # straight into the model-vs-market Brier that F3 and S18 rest on.
        "won": won_bet,
        "revenue": round(revenue_dollars, 4),
        "cost": round(cost, 4),
        "fees": round(fees, 4),
        "net_pnl": round(net_pnl, 4),
        "roi": round(net_pnl / cost, 4) if cost > 0 else 0,
        "result": result,
    }


def _compute_fair_value_yes(trade: dict) -> tuple[float | None, str | None]:
    """Normalize `fair_value` to YES perspective and tag the legacy field's side.

    Pre-R11 the settler stored `fair_value` as the bet-side probability without
    tagging perspective, so post-hoc analysis of NO bets had to flip the value
    by reading `side` separately. Returns (yes_perspective_value, side_tag).
    Either may be None if the source data is incomplete.
    """
    fv = trade.get("fair_value")
    side = trade.get("side")
    if side not in ("yes", "no"):
        return None, None
    if fv is None:
        return None, side
    fv = float(fv)
    if side == "yes":
        return fv, "yes"
    return round(1.0 - fv, 6), "no"


def build_settlement_record(
    trade: dict,
    pnl: dict,
    closing_price: float | None,
    clv: float | None,
) -> dict:
    """Construct a settlement-log record from a trade + pnl pair.

    Carries the full trade-side context so the settlement is self-describing
    for calibration/analytics — see ROADMAP R5 (2026-04-27) and R11 (2026-05-13).
    """
    fair_value_yes, fair_value_side = _compute_fair_value_yes(trade)
    return {
        "trade_id": trade.get("trade_id"),
        "order_id": trade.get("order_id"),
        "ticker": trade.get("ticker", ""),
        "title": trade.get("title"),
        "category": trade.get("category"),
        "side": trade.get("side"),
        "result": pnl["result"],
        "won": pnl["won"],
        "contracts": get_filled_contracts(trade),
        "cost": pnl["cost"],
        "revenue": pnl["revenue"],
        "fees": pnl["fees"],
        "net_pnl": pnl["net_pnl"],
        "roi": pnl["roi"],
        "edge_estimated": trade.get("edge_estimated"),
        "edge_source": trade.get("edge_source"),
        "fair_value": trade.get("fair_value"),
        "fair_value_yes": fair_value_yes,
        "fair_value_side": fair_value_side,
        "market_price_at_entry": trade.get("market_price_at_entry"),
        "closing_price": closing_price,
        "clv": clv,
        # S8: the whole closing book, not just the midpoint. A single scalar
        # makes the S14 maker/taker A/B unreadable -- you cannot distinguish
        # maker CLV genuinely improving from the close having been sampled on
        # the other side of a wide book. `close_capture_reason` separates
        # "never captured" (None) from "capture ran and got nothing"
        # ("missed"), which are different facts.
        "entry_price_bet_side": trade.get("entry_price_bet_side"),
        "close_yes_bid": trade.get("close_yes_bid"),
        "close_yes_ask": trade.get("close_yes_ask"),
        "close_no_bid": trade.get("close_no_bid"),
        "close_no_ask": trade.get("close_no_ask"),
        "close_mid_bet_side": trade.get("close_mid_bet_side"),
        "close_capture_at": trade.get("close_capture_at"),
        "close_capture_reason": trade.get("close_capture_reason"),
        "confidence": trade.get("confidence"),
        # S20b: carried through so book-width can be joined to OUTCOMES, which
        # is the only place the question is answerable. Absent on pre-2026-09-10
        # rows -- readers must treat missing as unknown, not as zero books.
        "n_books": trade.get("n_books"),
        "composite_score": trade.get("composite_score"),
        "risk_approval": trade.get("risk_approval"),
        "bankroll_pct": trade.get("bankroll_pct"),
        "unit_size": trade.get("unit_size"),
        "fill_status": trade.get("fill_status"),
        "settled_at": trade.get("closed_at"),
    }


def backfill_fees(client: KalshiClient, apply: bool = False) -> dict:
    """Re-stamp real `fee_cost` onto rows the renamed-field bug zeroed.

    `fetch_fill_fees` read three field names the endpoint has never used, so
    every row it touched recorded `taker_fees: 0.0` under a `fills_api` label.
    The settler only stamps fees on rows it is settling *now*, so fixing the
    reader does not repair the book behind it -- those rows are closed and will
    never be revisited. This walks the whole log once.

    It does NOT recompute `won`, `revenue` or `cost`. Only `fees` changes, and
    `net_pnl` follows it. Reports first; `--apply` writes.
    """
    fees = fetch_fill_fees(client)
    if not fees:
        rprint("[yellow]No fills returned -- nothing to backfill.[/yellow]")
        return {"matched": 0, "changed": 0, "delta": 0.0, "applied": False}

    changed, delta = 0, 0.0
    with trade_log_lock():
        trade_log = load_trade_log()
        settlement_log = load_settlement_log()
        by_order = {}
        for st in settlement_log:
            if st.get("order_id"):
                by_order.setdefault(st["order_id"], []).append(st)

        for trade in trade_log:
            oid = trade.get("order_id") or ""
            if oid not in fees:
                continue
            actual = fees[oid]
            before = float(trade.get("taker_fees") or 0)
            if abs(actual - before) < 1e-9:
                continue
            changed += 1
            delta += actual - before
            if not apply:
                continue
            trade["taker_fees"] = actual
            trade["fee_source"] = "fills_api"
            # A settled row's arithmetic was computed with the MODELLED fee
            # (trade_fees falls back on a recorded zero), so net_pnl moves by
            # the difference between the two, not by `actual` itself.
            for st in by_order.get(oid, []):
                if st.get("fees") is None or st.get("net_pnl") is None:
                    continue
                st["net_pnl"] = round(float(st["net_pnl"]) + float(st["fees"]) - actual, 4)
                st["fees"] = round(actual, 4)
                cost = float(st.get("cost") or 0)
                st["roi"] = round(st["net_pnl"] / cost, 4) if cost > 0 else 0

        if apply and changed:
            save_trade_log(trade_log)
            save_settlement_log(settlement_log)

    verb = "Updated" if apply else "Would update"
    rprint(
        f"  {verb} [cyan]{changed}[/cyan] trade rows; "
        f"recorded fees move by [cyan]${delta:+.4f}[/cyan]"
    )
    if not apply:
        rprint("  [dim]dry run -- pass --apply to write[/dim]")
    return {
        "matched": len(fees),
        "changed": changed,
        "delta": round(delta, 4),
        "applied": bool(apply and changed),
    }


_VENUE_CANCELLED = {"canceled", "cancelled", "expired"}


def _has_exposure(trade: dict) -> bool:
    """Open, not an error, and holding fills: the one settle predicate for both phases.

    A `resting` row is settled only after the pre-settle refresh has promoted it
    with real fills (BUG-01). Before, Phase 2 settled any open row whose ticker
    settled, so an order that filled after the create response booked $0.
    """
    return (
        trade.get("closed_at") is None
        and trade.get("status") != "error"
        and trade.get("fill_status") != "resting"
    )


def _count(order: dict, *keys: str) -> float:
    for key in keys:
        if order.get(key) not in (None, ""):
            return float(order[key])
    return 0.0


def fetch_order_states(client: KalshiClient, trades: list[dict]) -> dict[str, dict]:
    """Venue order state for every open `resting` / `partial` Kalshi row (BUG-01, X2).

    One `GET /portfolio/orders/{id}` per row; there are only ever a handful. A
    read that fails leaves its row out, and an unconfirmed `resting` row is then
    not settled this run rather than settled at a fill count that may be stale.
    Only this client's profile: another profile's orders sit in a subaccount
    this client can't read (they 401), so asking every hour only adds noise.
    """
    from app.config import get_config

    profile = get_config().system.profile
    states: dict[str, dict] = {}
    for t in trades:
        oid = t.get("order_id")
        if (
            not oid
            or t.get("closed_at") is not None
            or t.get("status") == "error"
            or t.get("fill_status") not in ("resting", "partial")
            or (t.get("venue") or "kalshi") != "kalshi"
            or t.get("profile", "main") != profile
        ):
            continue
        try:
            resp = client.get_order(oid)
        except Exception as e:  # noqa: BLE001
            log.warning("Fill refresh: could not read order %s (%s); row left as is", oid, e)
            continue
        order = resp.get("order", resp) if isinstance(resp, dict) else None
        if order:
            states[oid] = order
    return states


def apply_order_states(
    trades: list[dict], states: dict[str, dict], now: datetime | None = None
) -> int:
    """Bring open rows up to the venue's fills; return how many rows changed.

    More fills than the log knows: the row's fills, cost and status are raised
    (`set_row_fills`). No fills and the venue has cancelled or expired the order:
    the row is closed as cancelled at $0 (X2: a venue-side cancel used to leave
    it `resting` forever).
    """
    stamp = (now or datetime.now(timezone.utc)).isoformat()
    changed = 0
    for t in trades:
        order = states.get(t.get("order_id") or "")
        if order is None or t.get("closed_at") is not None:
            continue
        fill = _count(order, "fill_count_fp", "fill_count")
        remaining = _count(order, "remaining_count_fp", "remaining_count")
        if fill <= 0 and get_filled_contracts(t) <= 0:
            if (order.get("status") or "").lower() in _VENUE_CANCELLED:
                t.update(fill_status="cancelled", closed_at=stamp, net_pnl=0, remaining_count=0)
                changed += 1
            continue
        if set_row_fills(t, fill, remaining):
            t["fills_refreshed_at"] = stamp
            changed += 1
    return changed


def audit_closed_fills(client: KalshiClient) -> list[dict]:
    """Closed rows booked with fewer fills than the venue reports (ER-02 one-off). Read-only.

    The settler never revisits a closed row, so rows closed before BUG-01/02 were
    fixed keep whatever fill count they were closed with. One `get_order` per
    closed resting / partial / cancelled row. Prints the mismatches and returns
    them; correcting their P&L is a separate, owner-approved step.
    """
    rows = [
        t
        for t in load_trade_log()
        if t.get("closed_at") is not None
        and t.get("status") != "error"
        and t.get("order_id")
        and t.get("fill_status") in ("resting", "partial", "cancelled")
        and (t.get("venue") or "kalshi") == "kalshi"
    ]
    found = []
    for t in rows:
        try:
            resp = client.get_order(t["order_id"])
        except Exception as e:  # noqa: BLE001
            found.append(
                {"trade_id": t.get("trade_id"), "ticker": t.get("ticker"), "error": str(e)}
            )
            continue
        order = resp.get("order", resp)
        venue_fill = _count(order, "fill_count_fp", "fill_count")
        if venue_fill > get_filled_contracts(t):
            found.append(
                {
                    "trade_id": t.get("trade_id"),
                    "ticker": t.get("ticker"),
                    "side": t.get("side"),
                    "fill_status": t.get("fill_status"),
                    "logged_fill": get_filled_contracts(t),
                    "venue_fill": venue_fill,
                    "result": t.get("settlement_result"),
                    "closed_at": t.get("closed_at"),
                }
            )
    table = Table(title=f"Closed rows vs venue fills ({len(rows)} checked)")
    for col in ("ticker", "side", "fill_status", "logged", "venue", "result", "note"):
        table.add_column(col)
    for f in found:
        table.add_row(
            str(f.get("ticker")),
            str(f.get("side", "")),
            str(f.get("fill_status", "")),
            str(f.get("logged_fill", "")),
            str(f.get("venue_fill", "")),
            str(f.get("result") or ""),
            f.get("error", "")[:40],
        )
    console.print(table)
    rprint(
        f"{sum('error' not in f for f in found)} under-booked, "
        f"{sum('error' in f for f in found)} unreadable"
    )
    return found


def _order_by_client_id(client: KalshiClient, ticker: str, client_order_id: str) -> dict | None:
    """The venue's order with this client_order_id, or None. Raises if the read fails."""
    resp = client.get_orders(ticker=ticker, limit=100)
    orders = resp.get("orders", []) if isinstance(resp, dict) else []
    return next((o for o in orders if o.get("client_order_id") == client_order_id), None)


def settle_trades(client: KalshiClient) -> dict:
    """
    Fetch settlements from Kalshi and update the trade log.
    Returns summary of what changed.

    Two phases so we never hold the cross-process trade-log lock across network
    I/O (M2): **Phase 1** does all the Kalshi fetching against a read-only
    snapshot; **Phase 2** takes the lock, re-reads the logs fresh (so a trade an
    executor appended while we were fetching is preserved, not clobbered),
    applies the settlements, and saves.
    """
    # ── Phase 1: fetch everything from Kalshi (no lock) ────────────────────────
    # ER-13: an order a crashed execute run sent but never logged.
    pending = recover_pending(lambda ticker, cid: _order_by_client_id(client, ticker, cid))
    if pending:
        rprint(f"  [yellow]Booked {pending} order(s) left pending by a crashed run[/yellow]")
    # BUG-03: an accepted order whose log write failed sits in the journal.
    recovered = recover_journal()
    if recovered:
        rprint(f"  [yellow]Recovered {recovered} journaled trade(s) into the log[/yellow]")
    snapshot = load_trade_log()

    # BUG-01: re-read open resting/partial orders so late fills count before
    # anything settles. Applied to the snapshot here (so newly filled rows are
    # in the tickers we check) and again to the fresh read in Phase 2.
    order_states = fetch_order_states(client, snapshot)
    apply_order_states(snapshot, order_states)

    unsettled = [t for t in snapshot if _has_exposure(t)]

    if not unsettled:
        if order_states:
            with trade_log_lock():
                trade_log = load_trade_log()
                if apply_order_states(trade_log, order_states):
                    save_trade_log(trade_log)
        rprint("[dim]No unsettled trades in log.[/dim]")
        return {"settled": 0, "still_open": 0}

    unsettled_tickers = {t["ticker"] for t in unsettled}
    rprint(f"Checking {len(unsettled)} unsettled trades across {len(unsettled_tickers)} markets...")

    # Fetch settlements from Kalshi
    all_settlements = []
    cursor = None
    for _ in range(10):
        resp = client.get_settlements(limit=200, cursor=cursor)
        settlements = resp.get("settlements", [])
        all_settlements.extend(settlements)
        cursor = resp.get("cursor", "")
        if not cursor:
            break

    rprint(f"  Fetched {len(all_settlements)} settlements from Kalshi")

    # Real fees, keyed by order_id. The create-order response never carried them,
    # so this is the only place the true cost enters the log.
    fill_fees = fetch_fill_fees(client)
    if fill_fees:
        rprint(f"  Fetched fees for {len(fill_fees)} filled orders")

    # Index settlements by ticker
    settlement_map: dict[str, dict] = {}
    for s in all_settlements:
        ticker = s.get("ticker", "")
        settlement_map[ticker] = s

    # Fetch each unsettled market once — reused for both the settled/closed
    # fallback (below) and the closing-price/CLV capture in Phase 2.
    market_by_ticker: dict[str, dict] = {}
    for ticker in unsettled_tickers:
        try:
            market_by_ticker[ticker] = client.get_market(ticker).get("market", {})
        except Exception as e:
            log.debug("Could not fetch market %s: %s", ticker, e)

    # Also check market status for tickers not in settlements
    # (market might be settled but we haven't received settlement yet)
    for ticker in unsettled_tickers:
        if ticker not in settlement_map:
            market = market_by_ticker.get(ticker, {})
            status = market.get("status", "")
            if status in ("settled", "closed"):
                result = market.get("result", "")
                if result:
                    settlement_map[ticker] = {
                        "ticker": ticker,
                        "market_result": result,
                        "revenue": 0,  # will be calculated
                        "settlement_value_dollars": market.get("settlement_value_dollars"),
                        "settled_time": market.get("close_time", ""),
                    }
                    rprint(f"  [dim]Market {ticker} is {status}, result={result}[/dim]")

    # ── Phase 2: apply under the lock, re-reading fresh (no network here) ───────
    settled_count = 0
    still_open = 0

    with trade_log_lock():
        trade_log = load_trade_log()
        settlement_log = load_settlement_log()
        apply_order_states(trade_log, order_states)

        for trade in trade_log:
            if not _has_exposure(trade):
                continue

            ticker = trade.get("ticker", "")
            settlement = settlement_map.get(ticker)

            if settlement is None:
                still_open += 1
                continue

            # Stamp the real fee before P&L so it lands in the trade record too,
            # not just this settlement's arithmetic.
            actual_fee = fill_fees.get(trade.get("order_id") or "")
            if actual_fee is not None:
                trade["taker_fees"] = actual_fee
                trade["fee_source"] = "fills_api"
            elif not float(trade.get("taker_fees") or 0):
                trade["fee_source"] = "modelled"

            # Calculate P&L
            pnl = calculate_pnl(trade, settlement)

            # S8: CLV comes from `clv_capture.py`, which samples the book
            # BEFORE the event starts. It is deliberately not derived here.
            #
            # This block used to read `last_price` off the settlement-time
            # snapshot. A settled Kalshi market returns nothing meaningful
            # there, so it evaluated to `0.0`, `0.0` is falsy, and the guard
            # `if closing_price and entry_price` short-circuited `clv` to
            # `None` -- silently, on every settle, for five months. 426
            # settlements, 0 CLV, `closing_price` split {None: 259, 0.0: 167}.
            #
            # The deeper point is that the bug was not the arithmetic: by
            # settlement the closing book **no longer exists**, so no amount of
            # care here could have recovered it. Reading a settled market for a
            # closing line is a category error, not an off-by-one.
            closing_price = trade.get("close_mid_bet_side")
            clv = trade.get("clv")
            if clv is None and trade.get("close_capture_reason") is None:
                # Never captured -- pre-S8 rows, futures, and anything whose
                # event carried no start time. Left as None, which is the
                # honest value; S9 reports `n_captured / n_settled` so the gap
                # stays visible instead of averaging as zero.
                log.debug("No closing-book capture for %s; CLV stays None", ticker)

            # Update trade record
            trade["net_pnl"] = pnl["net_pnl"]
            trade["closed_at"] = settlement.get(
                "settled_time", datetime.now(timezone.utc).isoformat()
            )
            trade["settlement_result"] = pnl["result"]
            trade["settlement_revenue"] = pnl["revenue"]
            trade["settlement_won"] = pnl["won"]
            trade["settlement_roi"] = pnl["roi"]
            trade["closing_price"] = closing_price
            trade["clv"] = clv

            settled_count += 1

            won_str = (
                f"[yellow]{(pnl['result'] or 'void').upper()}[/yellow]"
                if pnl["won"] is None
                else "[green]WON[/green]" if pnl["won"] else "[red]LOST[/red]"
            )
            rprint(
                f"  {won_str} {ticker} "
                f"({trade['side'].upper()}) "
                f"P&L: ${pnl['net_pnl']:+.2f} "
                f"(cost=${pnl['cost']:.2f}, rev=${pnl['revenue']:.2f}, fees=${pnl['fees']:.2f})"
            )

            settlement_log.append(build_settlement_record(trade, pnl, closing_price, clv))

        # Save (still inside the lock — atomic writes onto the fresh-read logs)
        save_trade_log(trade_log)
        save_settlement_log(settlement_log)

    rprint(
        f"\n  Settled: [green]{settled_count}[/green]  Still open: [yellow]{still_open}[/yellow]"
    )
    return {"settled": settled_count, "still_open": still_open}


# ── Performance Report ────────────────────────────────────────────────────────


def _fetch_api_settlements(client: KalshiClient, days: int | None = None) -> list[dict]:
    """Fetch all settlements from the Kalshi API, optionally filtered by date."""
    all_settlements: list[dict] = []
    cursor = None
    for _ in range(20):  # safety limit
        resp = client.get_settlements(limit=200, cursor=cursor)
        settlements = resp.get("settlements", [])
        all_settlements.extend(settlements)
        cursor = resp.get("cursor", "")
        if not cursor:
            break

    if days is not None:
        from datetime import timedelta

        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        all_settlements = [s for s in all_settlements if (s.get("settled_time") or "") >= cutoff]

    return all_settlements


def _settlement_to_record(s: dict) -> dict:
    """Convert a Kalshi API settlement into a normalized record for reporting."""
    yes_count = float(s.get("yes_count_fp", 0))
    no_count = float(s.get("no_count_fp", 0))
    yes_cost = float(s.get("yes_total_cost_dollars", 0))
    no_cost = float(s.get("no_total_cost_dollars", 0))
    revenue = settlement_revenue_dollars(s.get("revenue", 0))
    fees = float(s.get("fee_cost", 0))
    result = s.get("market_result", "")

    # Determine which side we were on
    if yes_count > 0 and no_count > 0:
        side = "yes" if yes_cost > no_cost else "no"
    elif yes_count > 0:
        side = "yes"
    else:
        side = "no"

    contracts = yes_count if side == "yes" else no_count
    cost = yes_cost if side == "yes" else no_cost
    won = side == result if result in ("yes", "no") else None  # ER-15
    net_pnl = revenue - cost - fees

    return {
        "ticker": s.get("ticker", ""),
        "event_ticker": s.get("event_ticker", ""),
        "side": side,
        "contracts": contracts,
        "cost": round(cost, 4),
        "revenue": round(revenue, 4),
        "fees": round(fees, 4),
        "net_pnl": round(net_pnl, 4),
        "roi": round(net_pnl / cost, 4) if cost > 0 else 0,
        "won": won,
        "result": result,
        "settled_time": s.get("settled_time", ""),
    }


def generate_report(detail: bool = False, save: bool = False, days: int | None = None):
    """Generate P&L and performance report from Kalshi API + local trade log.

    Pulls settlement data directly from the Kalshi API so the report is
    accurate even for trades placed outside Edge-Radar (e.g. on the website).
    Local trade log data enriches the report with edge estimates and confidence.

    Args:
        detail: Show per-trade breakdown table.
        save: Write report to reports/Accounts/Kalshi/ with today's date.
        days: Only include trades settled in the last N days. None = all time.
    """
    from ticker_display import (
        format_bet_label,
        bet_type_from_ticker,
        parse_game_datetime,
        sport_from_ticker,
    )

    # ── Fetch data from Kalshi API ───────────────────────────────────────────
    client = KalshiClient()

    rprint("[dim]Fetching account data from Kalshi API...[/dim]")
    api_settlements = _fetch_api_settlements(client, days=days)
    api_positions = client.get_positions(limit=200, count_filter="position").get(
        "market_positions", []
    )
    balance = client.get_balance_dollars()

    # Normalize settlements
    settled_records = [_settlement_to_record(s) for s in api_settlements]
    # Filter out zero-exposure settlements (no position)
    settled_records = [r for r in settled_records if r["cost"] > 0 or r["revenue"] > 0]

    # Enrich with local trade log data (edge estimates, confidence, etc.)
    trade_log = load_trade_log()
    local_by_ticker = {}
    for t in trade_log:
        local_by_ticker[t.get("ticker", "")] = t

    for rec in settled_records:
        local = local_by_ticker.get(rec["ticker"])
        if local:
            rec["edge_estimated"] = local.get("edge_estimated", 0)
            rec["confidence"] = local.get("confidence", "")
            rec["category"] = local.get("category", "")
            rec["title"] = local.get("title", "")
            rec["composite_score"] = local.get("composite_score", 0)

    # ── Markdown + console output ────────────────────────────────────────────
    md: list[str] = []
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    period = f"Last {days} days" if days else "All time"

    rprint(f"\n-- Kalshi Account Report ({period}) --")
    rprint(f"  Generated: {generated_at}")

    md.append(f"# Kalshi Account Report ({period})")
    md.append("")
    md.append(f"*Generated: {generated_at}*")

    # ── Account Balance ──────────────────────────────────────────────────────
    bal = balance.get("balance", 0)
    portfolio = balance.get("portfolio_value", 0)
    total_value = bal + portfolio

    rprint("\n[bold]Account Balance[/bold]")
    rprint(f"  Available:       ${bal:.2f}")
    rprint(f"  Portfolio value: ${portfolio:.2f}")
    rprint(f"  Total value:     ${total_value:.2f}")

    md.append("")
    md.append("## Account Balance")
    md.append("")
    md.append("| Metric | Value |")
    md.append("|--------|-------|")
    md.append(f"| Available | ${bal:.2f} |")
    md.append(f"| Portfolio value | ${portfolio:.2f} |")
    md.append(f"| Total value | **${total_value:.2f}** |")

    # ── Open Positions (from API) ────────────────────────────────────────────
    live_positions = [p for p in api_positions if float(p.get("position_fp", 0)) != 0]

    if live_positions:
        rprint(f"\n[bold]Open Positions ({len(live_positions)})[/bold]")
        md.append("")
        md.append(f"## Open Positions ({len(live_positions)})")
        md.append("")
        md.append("| Bet | Side | Contracts | Exposure |")
        md.append("|-----|------|-----------|----------|")

        for p in live_positions:
            ticker = p.get("ticker", "")
            pos = float(p.get("position_fp", 0))
            side = "YES" if pos > 0 else "NO"
            contracts = int(abs(pos))
            exposure = float(p.get("market_exposure_dollars", 0))
            local = local_by_ticker.get(ticker)
            bet_label = format_bet_label(ticker, local.get("title", ticker) if local else ticker)

            rprint(f"  {bet_label[:40]} | {side} x{contracts} | ${exposure:.2f}")
            md.append(f"| {bet_label[:40]} | {side} | {contracts} | ${exposure:.2f} |")

    # ── Settlement Summary ───────────────────────────────────────────────────
    wins = [r for r in settled_records if r["won"]]
    losses = [r for r in settled_records if r["won"] is False]

    total_settled = len(settled_records)
    total_pnl = sum(r["net_pnl"] for r in settled_records)
    total_wagered = sum(r["cost"] for r in settled_records)
    total_revenue = sum(r["revenue"] for r in settled_records)
    total_fees = sum(r["fees"] for r in settled_records)
    win_rate = len(wins) / total_settled if total_settled else 0
    avg_win = sum(r["net_pnl"] for r in wins) / len(wins) if wins else 0
    avg_loss = sum(r["net_pnl"] for r in losses) / len(losses) if losses else 0
    roi = total_pnl / total_wagered if total_wagered > 0 else 0

    pnl_color = "green" if total_pnl >= 0 else "red"

    rprint(f"\n[bold]Settlement Summary ({total_settled} bets)[/bold]")
    rprint(f"  Record:          {len(wins)}W - {len(losses)}L ({win_rate:.0%})")
    rprint(f"  Net P&L:         [{pnl_color}]${total_pnl:+.2f}[/{pnl_color}]")
    rprint(f"  Total wagered:   ${total_wagered:.2f}")
    rprint(f"  Total revenue:   ${total_revenue:.2f}")
    rprint(f"  Total fees:      ${total_fees:.2f}")
    rprint(f"  ROI:             [{pnl_color}]{roi:+.1%}[/{pnl_color}]")
    rprint(f"  Avg win:         ${avg_win:+.2f}")
    rprint(f"  Avg loss:        ${avg_loss:+.2f}")

    md.append("")
    md.append(f"## Settlement Summary ({total_settled} bets)")
    md.append("")
    md.append("| Metric | Value |")
    md.append("|--------|-------|")
    md.append(f"| Record | **{len(wins)}W - {len(losses)}L ({win_rate:.0%})** |")
    md.append(f"| Net P&L | **${total_pnl:+.2f}** |")
    md.append(f"| Total wagered | ${total_wagered:.2f} |")
    md.append(f"| Total revenue | ${total_revenue:.2f} |")
    md.append(f"| Total fees | ${total_fees:.2f} |")
    md.append(f"| ROI | **{roi:+.1%}** |")
    md.append(f"| Avg win | ${avg_win:+.2f} |")
    md.append(f"| Avg loss | ${avg_loss:+.2f} |")

    if wins and losses:
        loss_total = abs(sum(r["net_pnl"] for r in losses))
        if loss_total > 0:
            profit_factor = abs(sum(r["net_pnl"] for r in wins)) / loss_total
            rprint(f"  Profit factor:   {profit_factor:.2f}")
            md.append(f"| Profit factor | {profit_factor:.2f} |")

    if settled_records:
        best = max(settled_records, key=lambda r: r["net_pnl"])
        worst = min(settled_records, key=lambda r: r["net_pnl"])
        best_label = format_bet_label(best["ticker"], best.get("title", best["ticker"]))
        worst_label = format_bet_label(worst["ticker"], worst.get("title", worst["ticker"]))
        rprint(f"  Best trade:      ${best['net_pnl']:+.2f} ({best_label[:30]})")
        rprint(f"  Worst trade:     ${worst['net_pnl']:+.2f} ({worst_label[:30]})")
        md.append(f"| Best trade | ${best['net_pnl']:+.2f} — {best_label[:30]} |")
        md.append(f"| Worst trade | ${worst['net_pnl']:+.2f} — {worst_label[:30]} |")

    # ── Edge Calibration (only for trades with local data) ───────────────────
    edge_trades = [r for r in settled_records if r.get("edge_estimated")]
    if edge_trades:
        avg_edge_est = sum(r["edge_estimated"] for r in edge_trades) / len(edge_trades)
        edge_wagered = sum(r["cost"] for r in edge_trades)
        edge_pnl = sum(r["net_pnl"] for r in edge_trades)
        edge_realized = edge_pnl / edge_wagered if edge_wagered > 0 else 0

        rprint(f"\n[bold]Edge Calibration ({len(edge_trades)} Edge-Radar trades)[/bold]")
        rprint(f"  Avg estimated edge:  {avg_edge_est:.1%}")
        rprint(f"  Realized edge (ROI): {edge_realized:+.1%}")

        md.append("")
        md.append(f"## Edge Calibration ({len(edge_trades)} Edge-Radar trades)")
        md.append("")
        md.append("| Metric | Value |")
        md.append("|--------|-------|")
        md.append(f"| Avg estimated edge | {avg_edge_est:.1%} |")
        md.append(f"| Realized edge (ROI) | {edge_realized:+.1%} |")

        if avg_edge_est > 0:
            realization = edge_realized / avg_edge_est
            rprint(f"  Edge realization:    {realization:.0%}")
            md.append(f"| Edge realization | {realization:.0%} |")

    # ── Dimensional breakdowns ───────────────────────────────────────────────
    def _breakdown(label: str, groups: dict, md: list):
        """Print and append a dimensional breakdown table."""
        if not groups:
            return
        rprint(f"\n[bold]{label}[/bold]")
        md.append("")
        md.append(f"### {label}")
        md.append("")
        md.append(f"| {label} | Bets | Win Rate | P&L | ROI |")
        md.append(f"|{'-' * max(len(label), 4)}--|------|----------|-----|-----|")
        for name, records in sorted(groups.items(), key=lambda x: -sum(r["net_pnl"] for r in x[1])):
            n = len(records)
            w = sum(1 for r in records if r["won"])
            pnl = sum(r["net_pnl"] for r in records)
            wagered = sum(r["cost"] for r in records)
            roi_val = pnl / wagered if wagered > 0 else 0
            wr = w / n if n else 0
            pnl_color = "green" if pnl >= 0 else "red"
            rprint(
                f"  {name:>12}: {n} bets, {w}/{n} ({wr:.0%}), "
                f"[{pnl_color}]${pnl:+.2f}[/{pnl_color}], ROI {roi_val:+.0%}"
            )
            md.append(f"| {name} | {n} | {w}/{n} ({wr:.0%}) | ${pnl:+.2f} | {roi_val:+.0%} |")

    if settled_records:
        # By sport (derived from ticker)
        sport_groups: dict[str, list] = {}
        for r in settled_records:
            sport = sport_from_ticker(r["ticker"]) or "Other"
            sport_groups.setdefault(sport, []).append(r)
        _breakdown("By Sport", sport_groups, md)

        # By bet type (derived from ticker)
        type_groups: dict[str, list] = {}
        for r in settled_records:
            btype = bet_type_from_ticker(r["ticker"])
            type_groups.setdefault(btype, []).append(r)
        _breakdown("By Type", type_groups, md)

        # By result
        result_groups: dict[str, list] = {}
        for r in settled_records:
            result_groups.setdefault(r["side"].upper(), []).append(r)
        _breakdown("By Side", result_groups, md)

    # ── Detail table ─────────────────────────────────────────────────────────
    if detail and settled_records:
        rprint("")
        table = Table(title="Settlement Detail", show_lines=True)
        table.add_column("#", style="dim", justify="right")
        table.add_column("Bet", style="cyan", max_width=30)
        table.add_column("Type", style="magenta")
        table.add_column("Date", style="dim")
        table.add_column("Side")
        table.add_column("Result")
        table.add_column("Qty", justify="right")
        table.add_column("Cost", justify="right")
        table.add_column("Revenue", justify="right")
        table.add_column("P&L", justify="right")

        md.append("")
        md.append("## Settlement Detail")
        md.append("")
        md.append("| # | Bet | Type | Date | Side | Result | Qty | Cost | Revenue | P&L |")
        md.append("|---|-----|------|------|------|--------|-----|------|---------|-----|")

        for i, r in enumerate(sorted(settled_records, key=lambda x: x.get("settled_time", "")), 1):
            pnl_color = "green" if r["net_pnl"] >= 0 else "red"
            won_str = "-" if r["won"] is None else "W" if r["won"] else "L"
            ticker = r["ticker"]
            bet_label = format_bet_label(ticker, r.get("title", ticker))
            btype = bet_type_from_ticker(ticker)
            when = parse_game_datetime(ticker)

            table.add_row(
                str(i),
                bet_label[:30],
                btype,
                when,
                r["side"].upper(),
                f"{r['result'].upper()} ({won_str})",
                str(r["contracts"]),
                f"${r['cost']:.2f}",
                f"${r['revenue']:.2f}",
                f"[{pnl_color}]${r['net_pnl']:+.2f}[/{pnl_color}]",
            )
            md.append(
                f"| {i} | {bet_label[:30]} | {btype} | {when} | "
                f"{r['side'].upper()} | {r['result'].upper()} ({won_str}) | "
                f"{r['contracts']} | ${r['cost']:.2f} | ${r['revenue']:.2f} | "
                f"${r['net_pnl']:+.2f} |"
            )
        console.print(table)

    if not settled_records:
        rprint("\n  [dim]No settlements in this period.[/dim]")
        md.append("")
        md.append("> No settlements found for this period.")

    # ── Save to file
    if save:
        _save_report_file(md, days=days)

    return "\n".join(md)


def _save_report_file(lines: list[str], days: int | None = None):
    """Write report lines to reports/Accounts/Kalshi/ with today's date.

    When ``days`` is 7 or 30, saves into a weekly/ or monthly/ subdirectory
    so scheduled reports don't overwrite the default all-time report.
    """
    base = Path(__file__).resolve().parent.parent.parent / "reports" / "Accounts" / "Kalshi"
    if days is not None and days <= 7:
        report_dir = base / "weekly"
    elif days is not None and days <= 30:
        report_dir = base / "monthly"
    else:
        report_dir = base
    report_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    report_path = report_dir / f"kalshi_report_{today}.md"

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    rprint(f"\n[green]Report saved to:[/green] {report_path}")


# ── Reconciliation ───────────────────────────────────────────────────────────


def local_open_positions(trade_log: list[dict]) -> dict[str, dict]:
    """Open Kalshi positions per ticker from the local log, signed like the API.

    Keys on fills, not ``status``: the executor copies Kalshi's order status,
    which has come back empty since 2026-06 and is logged as ``"unknown"`` -- a
    ``status == "executed"`` filter here matched nothing for three months.
    Errors are excluded explicitly because ``get_filled_contracts`` falls back
    to the requested size for rows with no fill fields. Kalshi reports a NO
    position as negative, so NO fills count negative.
    """
    positions: dict[str, dict] = {}
    for t in trade_log:
        if (
            t.get("closed_at")
            or t.get("status") == "error"
            or (t.get("venue") or "kalshi") != "kalshi"
        ):
            continue
        filled = get_filled_contracts(t)
        if filled <= 0:
            continue
        ticker = t.get("ticker", "")
        info = positions.setdefault(ticker, {"contracts": 0, "trades": []})
        info["contracts"] += -filled if t.get("side") == "no" else filled
        info["trades"].append(t.get("trade_id", "?")[:8])
    return positions


def reconcile_positions(client: KalshiClient):
    """
    Compare local trade log against Kalshi API positions.
    Flags discrepancies: trades in API but not local, or vice versa.
    """
    rprint("\n[bold]Reconciling local trade log vs Kalshi API...[/bold]")

    local_tickers = local_open_positions(load_trade_log())

    # API: actual positions on Kalshi
    api_positions = client.get_positions(limit=200, count_filter="position")
    api_tickers = {}
    for p in api_positions.get("market_positions", []):
        ticker = p.get("ticker", "")
        position = float(p.get("position_fp", "0") or 0)
        if position != 0:
            api_tickers[ticker] = {
                "position": position,
                "exposure": p.get("market_exposure_dollars", "0"),
            }

    # Compare
    only_local = set(local_tickers.keys()) - set(api_tickers.keys())
    only_api = set(api_tickers.keys()) - set(local_tickers.keys())
    in_both = set(local_tickers.keys()) & set(api_tickers.keys())

    rprint(f"  Local unsettled: {len(local_tickers)} tickers")
    rprint(f"  Kalshi API:      {len(api_tickers)} positions")

    issues = False

    if only_local:
        issues = True
        rprint(f"\n  [yellow]In local log but NOT on Kalshi ({len(only_local)}):[/yellow]")
        rprint("  [dim](May have been settled, cancelled, or sold on Kalshi directly)[/dim]")
        for ticker in sorted(only_local):
            info = local_tickers[ticker]
            rprint(f"    {ticker}  contracts={info['contracts']}")

    if only_api:
        issues = True
        rprint(f"\n  [yellow]On Kalshi but NOT in local log ({len(only_api)}):[/yellow]")
        rprint("  [dim](May have been placed manually on Kalshi website)[/dim]")
        for ticker in sorted(only_api):
            info = api_tickers[ticker]
            rprint(f"    {ticker}  position={info['position']}  exposure=${info['exposure']}")

    if in_both:
        mismatches = []
        for ticker in in_both:
            local_qty = local_tickers[ticker]["contracts"]
            api_qty = api_tickers[ticker]["position"]
            if local_qty != api_qty:
                mismatches.append((ticker, local_qty, api_qty))

        if mismatches:
            issues = True
            rprint(f"\n  [yellow]Quantity mismatches ({len(mismatches)}):[/yellow]")
            for ticker, local_qty, api_qty in mismatches:
                rprint(f"    {ticker}  local={local_qty}  kalshi={api_qty}")

    if not issues:
        rprint("\n  [green]All positions match.[/green]")
    else:
        rprint("\n  [yellow]Run 'settle' to resolve stale local entries.[/yellow]")


# ── CLI ───────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Kalshi settlement tracker & performance reporting"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("settle", help="Check for settled markets and update trade log P&L")

    report_p = sub.add_parser("report", help="Performance report")
    report_p.add_argument("--detail", action="store_true", help="Show per-trade breakdown")
    report_p.add_argument(
        "--save", action="store_true", help="Save report to reports/Accounts/Kalshi/"
    )
    report_p.add_argument(
        "--days",
        type=int,
        default=None,
        help="Only include trades settled in the last N days (default: all)",
    )

    sub.add_parser("reconcile", help="Compare local trade log vs Kalshi API positions")
    sub.add_parser(
        "audit-fills", help="Read-only: closed rows booked with fewer fills than the venue reports"
    )

    bf_p = sub.add_parser(
        "backfill-fees", help="Re-stamp real fill fees onto rows the renamed-field bug zeroed"
    )
    bf_p.add_argument("--apply", action="store_true", help="Write the changes (default: dry run)")

    args = parser.parse_args()

    if args.command == "settle":
        client = KalshiClient()
        settle_trades(client)

    elif args.command == "report":
        generate_report(detail=args.detail, save=args.save, days=args.days)

    elif args.command == "reconcile":
        client = KalshiClient()
        reconcile_positions(client)

    elif args.command == "audit-fills":
        audit_closed_fills(KalshiClient())

    elif args.command == "backfill-fees":
        client = KalshiClient()
        backfill_fees(client, apply=args.apply)


if __name__ == "__main__":
    main()
