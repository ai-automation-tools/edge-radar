"""Weekly betting audit (2026-10-27): the review battery's detectors."""

from datetime import datetime, timedelta, timezone

import betting_audit as ba

NOW = datetime(2026, 10, 27, tzinfo=timezone.utc)


def _settled(ticker, side, won, fv, px, days_ago=5):
    return {
        "ticker": ticker,
        "side": side,
        "won": won,
        "fair_value": fv,
        "market_price_at_entry": px,
        "contracts": 2,
        "cost": 2 * px,
        "net_pnl": (2 - 2 * px) if won else -2 * px,
        "settled_at": (NOW - timedelta(days=days_ago)).isoformat(),
    }


def test_model_over_claim_shows_as_negative_model_z():
    # 10 big-cover YES bets: model says 30%, market 15%, none win.
    rows = [_settled("KXNHLSPREAD-26OCT24ANAPHI-ANA3", "yes", False, 0.30, 0.15) for _ in range(10)]
    (r,) = ba.calibration_by_series(rows, NOW - timedelta(days=60))
    assert (r["n"], r["wins"]) == (10, 0)
    assert r["z_model"] < -1.5 < r["z_market"]


def test_calibration_window_and_zero_fill_rows_are_excluded():
    rows = [
        _settled("KXNFLSPREAD-26OCT25X-SEA8", "yes", True, 0.4, 0.3, days_ago=90),
        dict(_settled("KXNFLSPREAD-26OCT25X-SEA8", "yes", True, 0.4, 0.3), contracts=0),
    ]
    assert ba.calibration_by_series(rows, NOW - timedelta(days=60)) == []


def test_candidate_skew_reads_totals_as_over_under():
    obs = (NOW - timedelta(days=1)).isoformat()
    shadow = [
        {
            "ticker": "KXMLSTOTAL-26OCT28HOUMIN-6",
            "category": "total",
            "side": "no",
            "edge": 0.06,
            "observed_at": obs,
        }
        for _ in range(9)
    ] + [
        {
            "ticker": "KXMLSTOTAL-26OCT28HOUMIN-2",
            "category": "total",
            "side": "yes",
            "edge": 0.05,
            "observed_at": obs,
        },
        {
            "ticker": "KXMLSTOTAL-26OCT28HOUMIN-3",
            "category": "total",
            "side": "yes",
            "edge": 0.01,
            "observed_at": obs,
        },  # below min edge: not a candidate
    ]
    (r,) = ba.candidate_skew(shadow, NOW - timedelta(days=14))
    assert (r["n"], r["top"], round(r["share"], 2)) == (10, "under", 0.9)


def test_rest_data_on_a_non_rest_sport_is_a_leak():
    obs = (NOW - timedelta(days=1)).isoformat()
    shadow = [
        {
            "ticker": "KXMLSTOTAL-26OCT24HOUMIN-4",
            "details": {"rest": {"is_b2b": True}},
            "observed_at": obs,
        },
        {
            "ticker": "KXNBATOTAL-26OCT28GSWMIN-230",
            "details": {"rest": {"is_b2b": True}},
            "observed_at": obs,
        },
    ]
    leaks = ba.context_leaks(shadow, NOW - timedelta(days=14))
    assert leaks["shadow"] == ["KXMLSTOTAL-26OCT24HOUMIN-4"]


def test_order_health_flags_post_kickoff_and_feeless_settled_rows():
    ts = (NOW - timedelta(days=1)).isoformat()
    trades = [
        {
            "ticker": "A",
            "timestamp": ts,
            "event_start_time": (NOW - timedelta(days=2)).isoformat(),
            "filled_contracts": 1,
            "taker_fees": "0.01",
        },
        {
            "ticker": "B",
            "timestamp": ts,
            "event_start_time": NOW.isoformat(),
            "filled_contracts": 1,
            "taker_fees": "0",
            "closed_at": NOW.isoformat(),
        },
        {
            "ticker": "C",
            "timestamp": ts,
            "event_start_time": NOW.isoformat(),
            "filled_contracts": 1,
            "taker_fees": "0",
        },  # unsettled: fee not stamped yet
        {"ticker": "D", "timestamp": ts, "dry_run": True},
    ]
    h = ba.order_health(trades, NOW - timedelta(days=14))
    assert h["orders"] == 3
    assert h["post_kickoff"] == ["A"]
    assert h["zero_fee_filled"] == ["B"]
