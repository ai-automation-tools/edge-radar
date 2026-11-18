"""Shard funding (2026-08-27): sizing is whole-account, spending is per-shard.

`scripts/shared/shard_funding.py` carries a `_demo()` self-check for the pure
decision logic. These cover the part that matters operationally: that
`_place_order_batch` consults it, honours a refusal by skipping the order, and
never lets a refusal take down the rest of the batch.
"""

import dataclasses

import pytest

import kalshi_executor as ke
import shard_funding
from kalshi_executor import _place_order_batch, SizedOrder
from opportunity import Opportunity


def _sized(i, cost=5.0, ticker=None):
    opp = Opportunity(
        ticker=ticker or f"KXMLBGAME-26AUG27T{i}-A",
        title=f"Game {i}",
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
        contracts=10,
        price_cents=50,
        cost_dollars=cost,
        bankroll_pct=0.05,
        risk_approval="APPROVED",
    )


class _Client:
    """Duck-typed Kalshi client: per-shard balances, scripted market shards."""

    def __init__(self, balances, shards, transfer_lands=True):
        self._b = dict(balances)
        self._shards = dict(shards)
        self._lands = transfer_lands
        self.orders: list[str] = []
        self.transfers: list[tuple[float, int, int]] = []

    def get_market(self, ticker):
        return {"market": {"ticker": ticker, "exchange_index": self._shards.get(ticker)}}

    def get_shard_balance(self, exchange_index):
        return self._b.get(int(exchange_index), 0.0)

    def get_balance(self):
        # Account-wide and wrong per-subaccount, like the real API (2026-09-08).
        return {
            "balance_breakdown": [
                {"exchange_index": k, "balance": "999.0000"} for k in (0, 1, 2, 3)
            ]
        }

    def intra_exchange_transfer(self, amount, source_shard, destination_shard):
        self.transfers.append((amount, source_shard, destination_shard))
        if self._lands:
            self._b[source_shard] -= amount
            self._b[destination_shard] = self._b.get(destination_shard, 0) + amount
        return {"transfer_id": "t"}

    def create_order(self, **kw):
        self.orders.append(kw["ticker"])
        return {"order_id": "ord", "fill_count": "10.00", "remaining_count": "0.00"}


@pytest.fixture(autouse=True)
def _enable(monkeypatch):
    monkeypatch.setattr(ke, "AUTO_SHARD_TRANSFER", True)
    monkeypatch.setattr(ke, "SHARD_FUNDING_SOURCE", 0)
    monkeypatch.setattr(ke, "MAX_AUTO_SHARD_TRANSFER", 25.0)
    # The call site reads dry_run from the LIVE config, not a module global, so
    # these tests silently took the "[dry-run] would move" branch and asserted
    # nothing about transfers on any clone whose `.env` has DRY_RUN=true (this
    # fork's does). Pin it so the transfer path is actually exercised.
    live = ke.get_config()
    pinned = dataclasses.replace(live, system=dataclasses.replace(live.system, dry_run=False))
    monkeypatch.setattr(ke, "get_config", lambda: pinned)


def test_tops_up_the_shard_then_places(monkeypatch):
    monkeypatch.setattr(ke, "vel", _AlwaysEligible())
    c = _Client({0: 70.0, 3: 1.0}, {"KXMLBGAME-26AUG27T0-A": 3})
    tl = []
    results = _place_order_batch(c, [_sized(0, cost=5.0)], tl)

    # ER-41: cost $5.00 + taker fee $0.18 (10 @ 50c) + 1c headroom = $5.19 needed;
    # the shard holds $1.00, so $4.19 moves. Exactly the cost left the fee unfunded.
    assert c.transfers == [(4.19, 0, 3)], "moves the shortfall including fee headroom"
    assert c.orders == ["KXMLBGAME-26AUG27T0-A"]
    assert len(results) == 1


def test_no_transfer_when_shard_already_covers_it(monkeypatch):
    monkeypatch.setattr(ke, "vel", _AlwaysEligible())
    c = _Client({0: 70.0, 3: 40.0}, {"KXMLBGAME-26AUG27T0-A": 3})
    _place_order_batch(c, [_sized(0, cost=5.0)], [])
    assert c.transfers == []
    assert c.orders == ["KXMLBGAME-26AUG27T0-A"]


def test_underfunded_order_is_skipped_not_placed(monkeypatch):
    """The whole point: placing anyway just buys a 404 user_not_found."""
    monkeypatch.setattr(ke, "vel", _AlwaysEligible())
    monkeypatch.setattr(ke, "MAX_AUTO_SHARD_TRANSFER", 1.0)  # cap below shortfall
    c = _Client({0: 70.0, 3: 0.0}, {"KXMLBGAME-26AUG27T0-A": 3})
    tl = []
    results = _place_order_batch(c, [_sized(0, cost=5.0)], tl)

    assert c.orders == [], "must not reach the venue"
    assert c.transfers == []
    assert results == []
    assert tl and tl[0]["status"] == "error"
    assert "shard_underfunded" in tl[0]["error"]


def test_one_underfunded_order_does_not_stop_the_batch(monkeypatch):
    monkeypatch.setattr(ke, "vel", _AlwaysEligible())
    monkeypatch.setattr(ke, "MAX_AUTO_SHARD_TRANSFER", 1.0)
    c = _Client(
        {0: 70.0, 3: 0.0},
        {
            "KXMLBGAME-26AUG27T0-A": 3,  # shard 3, broke -> skipped
            "KXNFLGAME-26SEP13T1-A": 0,
        },  # shard 0, funded -> placed
    )
    orders = [_sized(0, cost=5.0), _sized(1, cost=5.0, ticker="KXNFLGAME-26SEP13T1-A")]
    results = _place_order_batch(c, orders, [])

    assert c.orders == ["KXNFLGAME-26SEP13T1-A"]
    assert len(results) == 1


def test_unknown_shard_fails_open(monkeypatch):
    """A market lookup that fails must not block trading as it did pre-sharding."""
    monkeypatch.setattr(ke, "vel", _AlwaysEligible())

    class _NoMarket(_Client):
        def get_market(self, ticker):
            raise RuntimeError("lookup down")

    c = _NoMarket({0: 70.0}, {})
    _place_order_batch(c, [_sized(0, cost=5.0)], [])
    assert c.orders == ["KXMLBGAME-26AUG27T0-A"]
    assert c.transfers == []


def test_market_is_looked_up_once_per_ticker(monkeypatch):
    monkeypatch.setattr(ke, "vel", _AlwaysEligible())
    c = _Client({0: 70.0, 3: 90.0}, {"KXMLBGAME-26AUG27T0-A": 3})
    seen = []
    orig = c.get_market
    c.get_market = lambda t: (seen.append(t), orig(t))[1]

    same = [_sized(0, cost=1.0), _sized(0, cost=1.0), _sized(0, cost=1.0)]
    _place_order_batch(c, same, [])
    assert seen == ["KXMLBGAME-26AUG27T0-A"], "shard lookup must be cached per batch"


def test_transfer_that_does_not_settle_blocks_the_order(monkeypatch):
    """Kalshi's transfer is non-atomic; a 200 is not proof the money arrived."""
    monkeypatch.setattr(ke, "vel", _AlwaysEligible())
    c = _Client({0: 70.0, 3: 0.0}, {"KXMLBGAME-26AUG27T0-A": 3}, transfer_lands=False)
    tl = []
    _place_order_batch(c, [_sized(0, cost=5.0)], tl)

    assert c.transfers, "it did attempt the move"
    assert c.orders == [], "but must not place against money that never landed"
    assert "did not settle" in tl[0]["error"]


def test_disabled_flag_skips_rather_than_moving_money(monkeypatch):
    monkeypatch.setattr(ke, "vel", _AlwaysEligible())
    monkeypatch.setattr(ke, "AUTO_SHARD_TRANSFER", False)
    c = _Client({0: 70.0, 3: 0.0}, {"KXMLBGAME-26AUG27T0-A": 3})
    tl = []
    _place_order_batch(c, [_sized(0, cost=5.0)], tl)
    assert c.transfers == [] and c.orders == []
    assert "AUTO_SHARD_TRANSFER is off" in tl[0]["error"]


def test_dry_run_never_moves_money(monkeypatch):
    monkeypatch.setattr(ke, "vel", _AlwaysEligible())
    ok, note = shard_funding.ensure_shard_funded(
        _Client({0: 70.0, 3: 0.0}, {}),
        3,
        5.0,
        enabled=True,
        source_shard=0,
        max_transfer=25.0,
        dry_run=True,
    )
    assert ok and "[dry-run]" in note


class _AlwaysEligible:
    """Stand-in for `venue_eligibility` so these tests exercise shard logic only."""

    @staticmethod
    def product_for(category):
        return "sports"

    @staticmethod
    def record_success(*a, **kw):
        return None

    @staticmethod
    def record_rejection(*a, **kw):
        return False

    @staticmethod
    def actionable_reason(raw, limit=160):
        return str(raw)


# ── shard_names(): the venue's shard list, not a sport table (U1, 2026-10-05) ──

_STATUS = {
    "exchange_active": True,
    "exchange_index_statuses": [
        {"exchange_index": 0, "description": "Default"},
        {"exchange_index": 1, "description": "Combos"},
        {"exchange_index": 2, "description": "Crypto & Commodities"},
        {"exchange_index": 3, "description": "Tennis, Baseball, Basketball"},
    ],
}


class TestShardNames:
    def test_reads_the_venue_list_when_the_client_can_answer(self):
        class C:
            def get_exchange_status(self):
                return _STATUS

        names = shard_funding.shard_names(C())
        assert names == {
            0: "Default",
            1: "Combos",
            2: "Crypto & Commodities",
            3: "Tennis, Baseball, Basketball",
        }

    def test_venue_wins_over_the_fallback_when_a_category_moves(self):
        """2026-09-10: Basketball joined shard 3. A hardcoded map kept the
        08-24 names; the venue's description is what gets printed."""

        class C:
            def get_exchange_status(self):
                return {
                    "exchange_index_statuses": [
                        {"exchange_index": 3, "description": "Everything Else"},
                    ]
                }

        assert shard_funding.shard_names(C()) == {3: "Everything Else"}

    def test_falls_back_when_the_client_cannot_answer(self):
        class NoStatus:
            pass

        assert shard_funding.shard_names(NoStatus()) == shard_funding.FALLBACK_SHARD_NAMES

    def test_falls_back_when_the_venue_errors_or_returns_nothing(self):
        class Boom:
            def get_exchange_status(self):
                raise RuntimeError("502")

        class Empty:
            def get_exchange_status(self):
                return {"exchange_index_statuses": []}

        assert shard_funding.shard_names(Boom()) == shard_funding.FALLBACK_SHARD_NAMES
        assert shard_funding.shard_names(Empty()) == shard_funding.FALLBACK_SHARD_NAMES

    def test_fallback_is_a_copy(self):
        names = shard_funding.shard_names(object())
        names[9] = "scratch"
        assert 9 not in shard_funding.FALLBACK_SHARD_NAMES

    def test_executor_shard_comes_from_the_market_not_from_the_sport(self):
        """The money decision never consults a sport table: an NBA ticker on
        shard 3 is funded on shard 3 because the market payload says so."""
        client = _Client({0: 70.0, 3: 0.0}, {"KXNBAGAME-26OCT11CHIDEN-DEN": 3})
        ok, note = shard_funding.ensure_shard_funded(
            client,
            client.get_market("KXNBAGAME-26OCT11CHIDEN-DEN")["market"]["exchange_index"],
            5.0,
            enabled=True,
            source_shard=0,
            max_transfer=25.0,
            dry_run=False,
        )
        assert ok and client.transfers == [(5.0, 0, 3)], (ok, note, client.transfers)
