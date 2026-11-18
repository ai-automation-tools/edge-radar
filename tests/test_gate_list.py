"""ER-19: one ordered gate list (`GATES`) behind the fresh, preview and replay
paths, and a test suite that never reads the operator's `.env`."""

import os
from datetime import datetime, timedelta, timezone

import kalshi_executor as ke
import pytest
from dotenv import load_dotenv
from opportunity import Opportunity

TICKER = "KXNHLTOTAL-26NOV16BOSTOR-6"


def _opp(edge=0.10):
    start = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
    return Opportunity(
        TICKER, "t", "total", "yes", 0.45, 0.45 + edge, edge, "x", "high", 8, 8,
        {"venue": "kalshi", "event_start_time": start},
    )  # fmt: skip


def _row(edge=0.10):
    return ke.SizedOrder(_opp(edge), 2, 45, 0.90, 0.009, "APPROVED")


class _Client:
    def __init__(self, balance=100.0):
        self.balance = balance

    def get_balance_dollars(self):
        return {"balance": self.balance, "portfolio_value": 0.0}

    def get_positions(self, **kw):
        return {"market_positions": []}

    def get_orders(self, **kw):
        return {"orders": []}


def _replay(rows, client=None):
    return ke.execute_pipeline(
        client or _Client(), [], execute=False, cached_rows=rows, cache_age_seconds=60
    )


@pytest.fixture(autouse=True)
def _no_calibration_check(monkeypatch):
    monkeypatch.setattr(ke, "_calibration_preflight", lambda execute: True)


def _size(opp):
    return ke.size_order(opp, 100.0, 0, 0.0)


def test_one_added_gate_reaches_all_three_paths(monkeypatch):
    blocked = ("9", "test", lambda opp, ctx: "test_gate (blocks everything)")
    monkeypatch.setattr(ke, "GATES", ke.GATES + (blocked,))

    assert _size(_opp()).risk_approval == "REJECTED: test_gate (blocks everything)"
    assert ke.preflight_gate_status(_opp()) == "test"
    assert _replay([_row()]) == []


def test_replay_runs_the_static_gates_against_current_config(monkeypatch):
    assert [s.opportunity.ticker for s in _replay([_row(0.10)])] == [TICKER]
    monkeypatch.setattr(ke, "MIN_EDGE_THRESHOLD", 0.20)  # raised since the preview
    assert _size(_opp(0.10)).risk_approval.startswith("REJECTED: edge_below_threshold")
    assert _replay([_row(0.10)]) == []


def test_replay_refuses_an_empty_bankroll():
    assert _replay([_row()], _Client(balance=0.0)) == []


def test_preview_skips_portfolio_gates_and_keeps_order():
    static = [label for _, label, _ in ke.GATES if label]
    assert static[:2] == ["off", "edge"] and static[-1] == "live-off"
    # The first gate is daily loss; a preview has no P&L to read and must not try.
    assert ke.first_rejection(_opp(), None, static_only=True) is None


def test_the_suite_never_loads_the_operators_env(tmp_path, monkeypatch):
    monkeypatch.delenv("ER19_PROBE", raising=False)
    env = tmp_path / ".env"
    env.write_text("ER19_PROBE=leaked\n")
    assert load_dotenv(env) is False
    assert "ER19_PROBE" not in os.environ
