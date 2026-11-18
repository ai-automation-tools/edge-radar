"""ER-03: the scan-cache replay path (--pick/--ticker) re-checks Gate 2 and
Gate 4.8 and re-clamps MAX_BET_SIZE. Preview only (execute=False)."""

from datetime import datetime, timedelta, timezone

import kalshi_executor as ke
import pytest
from opportunity import Opportunity


class _Client:
    def __init__(self, positions=()):
        self._positions = list(positions)

    def get_balance_dollars(self):
        return {"balance": 100.0, "portfolio_value": 5.0}

    def get_positions(self, **kw):
        return {"market_positions": self._positions}

    def get_orders(self, **kw):
        return {"orders": []}


_HELD = {
    "ticker": "KXNBAGAME-26NOV16LALBOS-LAL",
    "position_fp": "2",
    "market_exposure_dollars": "1.00",
}


def _row(start_offset_min: int, contracts: int = 2, price: float = 0.45):
    start = (datetime.now(timezone.utc) + timedelta(minutes=start_offset_min)).isoformat()
    opp = Opportunity(
        "KXNHLTOTAL-26NOV16BOSTOR-6",
        "t",
        "total",
        "yes",
        price,
        0.55,
        0.10,
        "x",
        "high",
        8,
        8,
        {"venue": "kalshi", "event_start_time": start},
    )
    cost = contracts * price
    return ke.SizedOrder(opp, contracts, round(price * 100), cost, cost / 100, "APPROVED")


@pytest.fixture(autouse=True)
def _gates(monkeypatch):
    monkeypatch.setattr(ke, "_calibration_preflight", lambda execute: True)
    monkeypatch.setattr(ke, "MAX_OPEN_POSITIONS", 10)
    monkeypatch.setattr(ke, "ALLOW_LIVE_BETS", False)
    monkeypatch.setattr(ke, "MAX_OPEN_EXPOSURE_PCT", 0)
    monkeypatch.setattr(ke, "MAX_SEGMENT_EXPOSURE_PCT", 0)
    monkeypatch.setattr(ke, "MAX_BET_SIZE", 50.0)


def _replay(client, rows):
    return ke.execute_pipeline(client, [], execute=False, cached_rows=rows, cache_age_seconds=300)


def test_started_game_is_dropped():
    assert _replay(_Client(), [_row(-40)]) == []


def test_row_over_max_open_positions_is_dropped(monkeypatch):
    monkeypatch.setattr(ke, "MAX_OPEN_POSITIONS", 1)
    assert _replay(_Client([_HELD]), [_row(120)]) == []


def test_bet_size_reclamped_to_current_cap(monkeypatch):
    monkeypatch.setattr(ke, "MAX_BET_SIZE", 2.0)
    out = _replay(_Client(), [_row(120, contracts=20)])
    assert [s.contracts for s in out] == [4]  # int(2.00 / 0.45)
    assert out[0].risk_approval == "APPROVED_CAPPED_MAX_BET"


def test_clean_row_still_replays():
    out = _replay(_Client(), [_row(120)])
    assert [s.contracts for s in out] == [2]
