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


# ── Pending file before the POST (ER-13 leftover) ────────────────────────────

import json  # noqa: E402

import trade_log  # noqa: E402


class _CheckingVenue(_Venue):
    """Asserts the pending file exists at the moment of the POST."""

    def create_order(self, **kw):
        cid = kw["client_order_id"]
        assert (trade_log.pending_dir() / f"{cid}.json").is_file(), "no pending file before POST"
        return super().create_order(**kw)


def test_pending_file_exists_during_post_and_is_cleared_after():
    venue = _CheckingVenue()
    assert len(ke._place_order_batch(venue, [_sized()], [])) == 1
    assert not list(trade_log.pending_dir().glob("*.json"))


def test_transport_error_not_found_keeps_the_pending_file():
    venue = _Venue(raise_first=True, landed=False)
    ke._place_order_batch(venue, [_sized()], [])
    (f,) = trade_log.pending_dir().glob("*.json")
    rec = json.loads(f.read_text(encoding="utf-8"))
    assert rec["client_order_id"] == venue.sent[0]["client_order_id"] == f.stem
    assert rec["requested_contracts"] == 2 and rec["filled_contracts"] == 0


def _stale_pending(cid="c1", ticker="KXNBAGAME-26APR04T1-A"):
    s = _sized(ticker)
    trade_log.write_pending(
        cid, {**ke._trade_record({"order": {"status": "pending"}}, s), "client_order_id": cid}
    )
    return trade_log.pending_dir() / f"{cid}.json"


def test_recover_pending_books_a_found_order_once():
    f = _stale_pending()
    order = {
        "order_id": "o9",
        "client_order_id": "c1",
        "status": "resting",
        "fill_count_fp": "1.00",
        "remaining_count_fp": "1.00",
    }
    assert trade_log.recover_pending(lambda t, c: order, now=f.stat().st_mtime + 1000) == 1
    (row,) = trade_log.load_trade_log()
    assert (
        row["order_id"] == "o9"
        and row["filled_contracts"] == 1.0
        and row["fill_status"] == "partial"
    )
    assert not f.exists()
    _stale_pending()  # the same order again: not booked twice
    assert trade_log.recover_pending(lambda t, c: order, now=f.stat().st_mtime + 1000) == 0
    assert len(trade_log.load_trade_log()) == 1


def test_recover_pending_drops_unknown_and_dead_orders_keeps_unreadable_venue():
    f = _stale_pending()
    later = f.stat().st_mtime + 1000

    def boom(t, c):
        raise RuntimeError("venue down")

    assert trade_log.recover_pending(boom, now=later) == 0 and f.exists()  # can't tell: kept
    assert (
        trade_log.recover_pending(lambda t, c: None, now=f.stat().st_mtime + 10) == 0 and f.exists()
    )  # too young
    assert (
        trade_log.recover_pending(lambda t, c: None, now=later) == 0 and not f.exists()
    )  # never landed
    f = _stale_pending("c2")
    dead = {"order_id": "o2", "status": "canceled", "fill_count_fp": "0.00"}
    assert trade_log.recover_pending(lambda t, c: dead, now=later) == 0 and not f.exists()
    assert trade_log.load_trade_log() == []
