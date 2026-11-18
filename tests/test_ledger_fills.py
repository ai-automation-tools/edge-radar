"""ER-02: the ledger records every real fill (BUG-01, BUG-02, BUG-03 in the 2026-11-16 audit).

The trade log feeds Gate 1, calibration, CLV and the S15 checkpoint, so a fill it misses is a
wrong number in all four. Stub clients only; conftest redirects the logs to a temp folder.
"""

from datetime import datetime, timedelta, timezone

import kalshi_executor as ke
import kalshi_settler as ks
import trade_log
from kalshi_executor import SizedOrder, _place_order_batch, cancel_live_resting_orders
from opportunity import Opportunity
from trade_log import load_settlement_log, load_trade_log, save_trade_log

T = "KXNFLGAME-26NOV15AAABBB-AAA"


def _row(oid, fill_status="resting", filled=0.0, requested=5, price=0.55, side="yes"):
    return {
        "trade_id": f"t-{oid}",
        "order_id": oid,
        "ticker": T,
        "side": side,
        "status": "unknown",
        "fill_status": fill_status,
        "requested_contracts": requested,
        "filled_contracts": filled,
        "filled_cost": round(filled * price, 4),
        "market_price_at_entry": price,
        "net_pnl": 0,
        "closed_at": None,
    }


class _Venue:
    """Settles `T` with `result`; `orders` maps order_id -> order payload, or an exception."""

    def __init__(self, orders, result="no", fees=None):
        self.orders, self.result, self.fees = orders, result, fees or {}

    def get_order(self, oid):
        o = self.orders[oid]
        if isinstance(o, Exception):
            raise o
        return {"order": o}

    def get_settlements(self, limit=200, cursor=None, **_):
        return {"settlements": [{"ticker": T, "market_result": self.result}], "cursor": ""}

    def get_fills(self, limit=200, cursor=None, **_):
        return {
            "fills": [{"order_id": k, "fee_cost": v} for k, v in self.fees.items()],
            "cursor": "",
        }

    def get_market(self, ticker):
        return {"market": {"status": "settled"}}


def _order(fill, remaining, status="executed"):
    return {
        "fill_count_fp": f"{fill:.2f}",
        "remaining_count_fp": f"{remaining:.2f}",
        "status": status,
    }


# ── BUG-01: late fills on resting / partial rows ──────────────────────────────


def test_resting_row_that_filled_late_settles_at_its_real_cost():
    save_trade_log([_row("late")])
    ks.settle_trades(_Venue({"late": _order(5, 0)}, result="no", fees={"late": "0.09"}))
    (row,) = load_trade_log()
    assert row["fill_status"] == "filled" and row["filled_contracts"] == 5
    assert row["net_pnl"] == round(-(5 * 0.55) - 0.09, 4)  # was -0.09
    assert load_settlement_log()[0]["net_pnl"] == row["net_pnl"]


def test_partial_row_picks_up_later_fills():
    save_trade_log([_row("part", fill_status="partial", filled=2, price=0.40)])
    ks.settle_trades(_Venue({"part": _order(4, 1, "resting")}, result="yes", fees={"part": "0.08"}))
    (row,) = load_trade_log()
    assert row["filled_contracts"] == 4 and row["fill_status"] == "partial"
    assert row["net_pnl"] == round(4 * 1.00 - 4 * 0.40 - 0.08, 4)


def test_venue_cancel_with_no_fills_closes_the_row_at_zero():
    save_trade_log([_row("gone")])
    ks.settle_trades(_Venue({"gone": _order(0, 0, "canceled")}))
    (row,) = load_trade_log()
    assert row["fill_status"] == "cancelled" and row["closed_at"] and row["net_pnl"] == 0
    assert load_settlement_log() == []


def test_unconfirmed_resting_row_is_not_settled_at_zero():
    save_trade_log([_row("unknown")])
    ks.settle_trades(_Venue({"unknown": RuntimeError("404")}))
    (row,) = load_trade_log()
    assert row["closed_at"] is None and row["fill_status"] == "resting"
    assert load_settlement_log() == []


# ── BUG-02: the live janitor's cancel write-back ─────────────────────────────


class _Janitor:
    def __init__(self, orders):
        self.orders, self.cancelled = orders, []

    def get_orders(self, status=None, limit=100):
        return {"orders": self.orders}

    def cancel_order(self, oid, exchange_index=None):
        self.cancelled.append(oid)
        return {"order_id": oid}


def test_janitor_cancel_keeps_a_partly_filled_row_open(monkeypatch):
    monkeypatch.setattr(ke, "ALLOW_LIVE_BETS", False)
    now = datetime(2026, 11, 16, 3, 0, tzinfo=timezone.utc)
    row = _row("ord-1", price=0.50) | {"event_start_time": (now - timedelta(hours=1)).isoformat()}
    save_trade_log([row])
    venue = _Janitor(
        [{"order_id": "ord-1", "ticker": T, "fill_count_fp": "2.00", "remaining_count_fp": "3.00"}]
    )

    cancelled = cancel_live_resting_orders(venue, load_trade_log(), now=now)
    assert venue.cancelled == ["ord-1"] and cancelled[0]["filled"] == 2
    assert trade_log.mark_cancelled({c["order_id"]: c["filled"] for c in cancelled}) == 0

    (row,) = load_trade_log()
    assert row["closed_at"] is None and row["fill_status"] == "partial"
    assert row["filled_contracts"] == 2 and row["filled_cost"] == 1.0


# ── BUG-03: an accepted order whose log write fails ──────────────────────────


def _sized():
    opp = Opportunity(
        ticker=T,
        title="g",
        category="game",
        side="yes",
        market_price=0.50,
        fair_value=0.60,
        edge=0.10,
        edge_source="test",
        confidence="high",
        liquidity_score=8.0,
        composite_score=8.5,
        details={},
    )
    return SizedOrder(
        opportunity=opp,
        contracts=3,
        price_cents=50,
        cost_dollars=1.5,
        bankroll_pct=0.01,
        risk_approval="APPROVED",
    )


class _Accepts:
    def create_order(self, **_):
        return {"order": {"order_id": "venue-1", "fill_count": "3.00", "remaining_count": "0.00"}}


def _fail_first(n, monkeypatch):
    real, calls = trade_log.append_trades, {"n": 0}

    def flaky(records):
        calls["n"] += 1
        if calls["n"] <= n:
            raise PermissionError(13, "Access is denied")
        return real(records)

    monkeypatch.setattr(trade_log, "append_trades", flaky)
    monkeypatch.setattr(trade_log.time, "sleep", lambda s: None)
    return real


def test_one_failed_write_still_books_one_real_row(monkeypatch):
    _fail_first(1, monkeypatch)
    results = _place_order_batch(_Accepts(), [_sized()], [])
    rows = load_trade_log()
    assert len(results) == 1 and len(rows) == 1
    assert rows[0]["order_id"] == "venue-1" and rows[0]["status"] != "error"


def test_persistent_write_failure_journals_and_settle_recovers(monkeypatch):
    real = _fail_first(99, monkeypatch)
    _place_order_batch(_Accepts(), [_sized()], [])
    assert load_trade_log() == [] and trade_log.journal_path().exists()

    # Not monkeypatch.undo(): that would also undo conftest's redirect of the log paths.
    monkeypatch.setattr(trade_log, "append_trades", real)
    assert trade_log.recover_journal() == 1
    (row,) = load_trade_log()
    assert row["order_id"] == "venue-1" and row["status"] != "error"
    assert not trade_log.journal_path().exists()
    assert trade_log.recover_journal() == 0


def test_audit_fills_reports_closed_rows_the_venue_filled():
    closed = _row("old") | {"closed_at": "2026-10-01T00:00:00Z", "settlement_result": "no"}
    fine = _row("ok-zero") | {"closed_at": "2026-10-01T00:00:00Z"}
    save_trade_log([closed, fine])
    found = ks.audit_closed_fills(
        _Venue({"old": _order(3, 0), "ok-zero": _order(0, 0, "canceled")})
    )
    assert [(f["trade_id"], f["venue_fill"]) for f in found] == [("t-old", 3.0)]
    assert load_trade_log()[0]["filled_contracts"] == 0  # report only, nothing written
