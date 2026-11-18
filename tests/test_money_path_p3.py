"""Audit P3 money-path fixes: ER-35, ER-37, ER-38, ER-40, ER-41, ER-43, ER-44, ER-46."""

import dataclasses
from datetime import datetime, timezone
from types import SimpleNamespace

import app.config
import pytest
import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

import edge_detector as ed
import kalshi_client as kc
import kalshi_executor as ke
import risk_check as rc
import scan_cache
from opportunity import Opportunity
from trade_log import get_filled_contracts, get_filled_cost, settlement_revenue_dollars

_PEM = (
    rsa.generate_private_key(public_exponent=65537, key_size=2048)
    .private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    .decode()
)


def _client(base_url="https://api.elections.kalshi.com/trade-api/v2"):
    return kc.KalshiClient(api_key="k", private_key_content=_PEM, base_url=base_url)


# ── ER-46: demo is an exact host, everything else is live ─────────────────────


@pytest.mark.parametrize(
    "url, demo",
    [
        ("https://demo-api.kalshi.co/trade-api/v2", True),
        ("https://api.elections.kalshi.com/trade-api/v2", False),
        ("https://api.elections.kalshi.com/demo/trade-api/v2", False),
        ("https://demo-api.kalshi.co.evil.example/trade-api/v2", False),
    ],
)
def test_demo_is_an_exact_host(url, demo):
    assert _client(url).is_demo is demo


# ── ER-44: GETs retry, POSTs never ────────────────────────────────────────────


class _Resp:
    def __init__(self, status, payload=None):
        self.status_code, self._payload = status, payload or {}
        self.ok = 200 <= status < 300
        self.content = b"{}"
        self.text = ""

    def json(self):
        return self._payload


@pytest.fixture
def http(monkeypatch):
    calls, queue = [], []

    def fake(method, url, **kw):
        calls.append(method)
        nxt = queue.pop(0)
        if isinstance(nxt, Exception):
            raise nxt
        return nxt

    monkeypatch.setattr(kc.requests, "request", fake)
    monkeypatch.setattr(kc.time, "sleep", lambda s: None)
    return SimpleNamespace(calls=calls, queue=queue)


def test_get_retries_429_and_transport_errors(http):
    http.queue += [_Resp(429), requests.ConnectionError("reset"), _Resp(200, {"ok": 1})]
    assert _client()._get("/x") == {"ok": 1}
    assert http.calls == ["GET"] * 3


def test_get_gives_up_after_the_retries(http):
    http.queue += [_Resp(503)] * 3
    with pytest.raises(kc.KalshiAPIError):
        _client()._get("/x")
    assert len(http.calls) == 1 + kc.GET_RETRIES


def test_get_does_not_retry_a_client_error(http):
    http.queue += [_Resp(400)]
    with pytest.raises(kc.KalshiAPIError):
        _client()._get("/x")
    assert http.calls == ["GET"]


def test_post_is_never_retried(http):
    http.queue += [_Resp(429), _Resp(200)]
    with pytest.raises(kc.KalshiRateLimitError):
        _client()._post("/portfolio/events/orders", {})
    assert http.calls == ["POST"]


# ── ER-40: listings follow the cursor ─────────────────────────────────────────


def test_positions_and_orders_read_every_page(monkeypatch):
    c = _client()
    pages = {
        None: {"market_positions": [{"ticker": "A"}], "event_positions": [], "cursor": "p2"},
        "p2": {"market_positions": [{"ticker": "B"}], "event_positions": [], "cursor": ""},
    }
    seen = []

    def fake_get(path, params=None):
        seen.append(params.get("cursor"))
        return dict(pages[params.get("cursor")])

    monkeypatch.setattr(c, "_get", fake_get)
    out = c.get_positions(limit=1, count_filter="position")
    assert [p["ticker"] for p in out["market_positions"]] == ["A", "B"]
    assert seen == [None, "p2"]

    pages[None] = {"orders": [{"order_id": 1}], "cursor": "p2"}
    pages["p2"] = {"orders": [{"order_id": 2}], "cursor": ""}
    assert [o["order_id"] for o in c.get_orders(status="resting")["orders"]] == [1, 2]


# ── ER-43: accounting helpers ─────────────────────────────────────────────────


def test_balance_prefers_dollar_fields(monkeypatch):
    c = _client()
    monkeypatch.setattr(c, "get_balance", lambda: {"balance": 4000, "balance_dollars": "40.0000"})
    assert c.get_balance_dollars()["balance"] == 40.0
    monkeypatch.setattr(c, "get_balance", lambda: {"balance": 1234, "portfolio_value": None})
    assert c.get_balance_dollars() == {"balance": 12.34, "portfolio_value": 0.0, "updated_ts": None}


@pytest.mark.parametrize(
    "raw, dollars", [(None, 0.0), ("", 0.0), (56, 0.56), ("56", 0.56), ("0.56", 0.56), (0.56, 0.56)]
)
def test_settlement_revenue_dollars(raw, dollars):
    assert settlement_revenue_dollars(raw) == dollars


def test_fill_helpers_treat_null_as_missing():
    row = {"filled_contracts": None, "filled_cost": None, "fill_count": 3}
    row["market_price_at_entry"] = 0.4
    assert get_filled_contracts(row) == 3.0
    assert get_filled_cost(row) == 1.2
    assert get_filled_contracts({"contracts": None}) == 0.0
    assert get_filled_cost({"cost_dollars": None}) == 0.0


def _opp(ticker="KXMLBGAME-99AUG271900NYYBOS-NYY", price=0.50):
    return Opportunity(
        ticker=ticker,
        title="",
        category="game",
        side="yes",
        market_price=price,
        fair_value=price + 0.12,
        edge=0.12,
        edge_source="test",
        confidence="high",
        liquidity_score=9.0,
        composite_score=9.9,
        details={"bid_ask_spread": 0.01},
    )


@pytest.mark.parametrize("bankroll", [0.0, -5.0, float("nan")])
def test_sizing_refuses_without_a_bankroll(bankroll):
    s = ke.size_order(_opp(), bankroll=bankroll, open_positions=0, daily_pnl=0.0)
    assert s.contracts == 0
    assert "no_bankroll" in s.risk_approval


# ── ER-37: Gate 7 counts only real orders ─────────────────────────────────────


def test_series_dedup_ignores_error_and_dry_run_rows():
    now = datetime.now(timezone.utc)
    ts = now.isoformat()
    t = "KXMLBGAME-26APR14LAAANYY-NYY"
    rows = [
        {"ticker": t, "timestamp": ts, "status": "error"},
        {"ticker": t, "timestamp": ts, "status": "dry_run_blocked", "dry_run": True},
    ]
    assert ke.recent_matchups_from_log(rows, hours=48, now=now) == set()
    rows.append({"ticker": t, "timestamp": ts, "status": "executed"})
    assert ke.recent_matchups_from_log(rows, hours=48, now=now) == {("mlb", "LAAANYY")}


# ── ER-41: shard funding covers the fee ───────────────────────────────────────


def test_funding_need_includes_fee_and_a_cent():
    s = ke.SizedOrder(
        opportunity=_opp(price=0.50),
        contracts=10,
        price_cents=50,
        cost_dollars=5.0,
        bankroll_pct=0.05,
        risk_approval="APPROVED",
    )
    assert ke._funding_need(s) == round(5.0 + ke.taker_fee(10, 0.50) + 0.01, 2)
    assert ke._funding_need(s) > 5.0


# ── ER-35: the scan cache is per wallet ───────────────────────────────────────


def test_scan_fingerprint_differs_across_profiles(monkeypatch):
    args = SimpleNamespace(
        ticker_filter="mlb", category=None, exclude_open=True, min_edge=0.05, top=20
    )
    cfg = ed.get_config()

    def as_profile(name):
        system = dataclasses.replace(cfg.system, profile=name)
        monkeypatch.setattr(ed, "get_config", lambda: dataclasses.replace(cfg, system=system))
        return ed.scan_fingerprint(args, "2026-11-17", SimpleNamespace(subaccount=0))

    main, longshot = as_profile("main"), as_profile("longshot")
    ok, diffs = scan_cache.fingerprints_match(main, longshot)
    assert not ok and any(d.startswith("profile") for d in diffs)
    assert not scan_cache.fingerprints_match(main, {**main, "subaccount": 1})[
        0
    ], "another subaccount is another wallet"


# ── ER-38: risk_check --gate reads this profile's P&L ─────────────────────────


def test_gate_pnl_is_profile_scoped(monkeypatch):
    today = datetime.now(timezone.utc).isoformat()
    rows = [
        {"profile": "main", "timestamp": today, "closed_at": today, "net_pnl": -10.0},
        {"profile": "longshot", "timestamp": today, "closed_at": today, "net_pnl": -500.0},
        {"timestamp": today, "closed_at": today, "net_pnl": -5.0},  # pre-P1 row: main's
    ]
    monkeypatch.setattr(rc, "load_trade_log", lambda: rows)
    cfg = app.config.get_config()
    main = dataclasses.replace(cfg, system=dataclasses.replace(cfg.system, profile="main"))
    monkeypatch.setattr(app.config, "get_config", lambda: main)
    trades, pnl = rc.get_today_trades()
    assert pnl == -15.0
    assert len(trades) == 2
