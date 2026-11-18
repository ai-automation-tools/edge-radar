"""ER-15 follow-up: void/scalar settlements are neither wins nor losses in the
risk dashboard (risk_check) or the calibration report (model_calibration)."""

import json

import model_calibration as mc
import risk_check as rc


def _kalshi(result, *, yes_cost=4.0, revenue_cents=400, yes_count=10):
    return {
        "ticker": "KXNBAGAME-26NOV17BOSNYK-BOS",
        "market_result": result,
        "yes_count_fp": yes_count,
        "no_count_fp": 0,
        "yes_total_cost_dollars": yes_cost,
        "no_total_cost_dollars": 0,
        "revenue": revenue_cents,
        "fee_cost": 0.1,
        "settled_time": "2026-11-17T03:00:00Z",
    }


def test_settlement_record_marks_non_binary_results_void():
    assert rc._settlement_record(_kalshi("yes", revenue_cents=1000))["won"] is True
    assert rc._settlement_record(_kalshi("no", revenue_cents=0))["won"] is False
    void = rc._settlement_record(_kalshi("scalar"))
    assert void["won"] is None
    assert void["net_pnl"] == -0.1  # refund minus fees: counts in P&L
    assert rc._settlement_record(_kalshi("", yes_cost=0, revenue_cents=0, yes_count=0)) is None


def test_win_rate_counts_only_decided_rows():
    recs = [{"won": True}, {"won": False}, {"won": None}]
    assert rc._win_rate(recs) == "1/2 (50%)"
    assert rc._win_rate([{"won": None}]) == "-"


def test_calibration_skips_void_settlements(tmp_path, monkeypatch):
    path = tmp_path / "kalshi_settlements.json"
    rows = [
        {"ticker": "KXNBAGAME-A", "won": True, "cost": 1.0},
        {"ticker": "KXNBAGAME-B", "won": None, "cost": 1.0},
        {"ticker": "KXNBAGAME-C", "won": False, "cost": 1.0},
    ]
    path.write_text(json.dumps(rows), encoding="utf-8")
    monkeypatch.setattr(mc, "SETTLEMENTS_PATH", path)
    trades = mc._load_settled_trades()
    assert [t["ticker"] for t in trades] == ["KXNBAGAME-A", "KXNBAGAME-C"]
    assert [t["settlement_won"] for t in trades] == [True, False]
