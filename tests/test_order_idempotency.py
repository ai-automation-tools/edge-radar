"""ER-13: orders carry a client_order_id, a lost response is looked up before it
is written off, resting orders count for Gate 5/6, and execute runs serialize."""

import pytest

import kalshi_executor as ke
from kalshi_client import KalshiConnectionError
from opportunity import Opportunity
from test_replay_gates import _Client, _replay, _row


def _sized(ticker="KXNBAGAME-26APR04T1-A"):
    opp = Opportunity(ticker, "g", "game", "yes", 0.5, 0.6, 0.1, "t", "high", 8.0, 8.5, {})
    return ke.SizedOrder(opp, 2, 50, 1.0, 0.01, "APPROVED")


class _Venue:
    """create_order raises or answers per script; get_orders lists what 'landed'."""

    def __init__(self, raise_first=False, landed=True):
        self.raise_first, self.landed, self.sent = raise_first, landed, []

    def create_order(self, **kw):
        self.sent.append(kw)
        if self.raise_first and len(self.sent) == 1:
            raise KalshiConnectionError("Timeout: read")
        return {"order": {"order_id": f"o{len(self.sent)}", "status": "resting"}}

    def get_orders(self, **kw):
        if not self.landed:
            return {"orders": []}
        kw0 = self.sent[0]
        return {
            "orders": [
                {
                    "order_id": "o-found",
                    "ticker": kw0["ticker"],
                    "client_order_id": kw0["client_order_id"],
                    "status": "resting",
                }
            ]
        }


def test_every_post_carries_a_distinct_client_order_id():
    venue = _Venue()
    ke._place_order_batch(venue, [_sized("A-1"), _sized("B-2")], [])
    ids = [kw.get("client_order_id") for kw in venue.sent]
    assert all(ids) and len(set(ids)) == 2


def test_lost_response_found_by_client_order_id_is_booked():
    venue, log = _Venue(raise_first=True), []
    s = _sized()
    results = ke._place_order_batch(venue, [s], log)
    assert len(results) == 1 and s.outcome == "placed"
    assert not [r for r in log if r.get("status") == "error"]


def test_lost_response_not_found_is_still_recorded_unknown():
    venue, log = _Venue(raise_first=True, landed=False), []
    s = _sized()
    assert ke._place_order_batch(venue, [s], log) == []
    err = [r for r in log if r.get("status") == "error"]
    assert s.outcome == "failed" and venue.sent[0]["client_order_id"] in err[0]["error"]


class _RestingClient(_Client):
    def get_orders(self, **kw):
        return {
            "orders": [
                {
                    "order_id": "r1",
                    "ticker": _row(120).opportunity.ticker,
                    "remaining_count_fp": "2.00",
                }
            ]
        }


def test_resting_order_blocks_a_second_order_on_the_same_ticker(monkeypatch):
    t = _row(120).opportunity.ticker
    monkeypatch.setattr(
        ke, "load_trade_log", lambda: [{"order_id": "r1", "side": "yes", "ticker": t}]
    )
    assert _replay(_Client(), [_row(120)]) != []
    assert _replay(_RestingClient(), [_row(120)]) == []


def test_second_execute_run_waits_then_gives_up():
    with ke.execute_run_lock():
        with pytest.raises(ke.ExecuteRunBusy):
            with ke.execute_run_lock(timeout=0.2):
                pass
    with ke.execute_run_lock(timeout=0.2):  # released
        pass


def test_only_execute_runs_take_the_lock(monkeypatch):
    taken = []
    monkeypatch.setattr(ke, "execute_run_lock", lambda: taken.append(1) or _null())
    _replay(_Client(), [_row(120)])
    assert taken == []
    # DRY_RUN=true in tests; the stub has no create_order, so the order fails
    # into the redirected test ledger and nothing leaves the process.
    ke.execute_pipeline(_Client(), [], execute=True, cached_rows=[_row(120)], cache_age_seconds=300)
    assert taken == [1]


class _null:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False
