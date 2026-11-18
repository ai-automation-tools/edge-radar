"""ER-15: void and scalar settlements are not total losses.

`calculate_pnl` paid $1.00 on a matching yes/no and $0 on everything else, so a
void on a $2.00 stake booked -$2.07 and a scalar settlement booked the whole
stake as lost.
"""

import pytest

import kalshi_settler as ks
from calibration_study import load_rows

TRADE = {
    "ticker": "KXMLSTOTAL-26JUL16CHIVAN-3",
    "side": "yes",
    "filled_contracts": 2,
    "filled_cost": 2.00,
    "taker_fees": "0.07",
    "maker_fees": "0",
}


def test_void_is_a_refund_not_a_loss():
    pnl = ks.calculate_pnl(TRADE, {"market_result": "void"})
    assert pnl["won"] is None
    assert pnl["revenue"] == 2.00
    assert pnl["net_pnl"] == pytest.approx(-0.07)


@pytest.mark.parametrize("side, want", [("yes", 1.34), ("no", 0.66)])
def test_scalar_pays_the_settlement_value(side, want):
    pnl = ks.calculate_pnl({**TRADE, "side": side}, {"market_result": "scalar", "value": 67})
    assert pnl["won"] is None
    assert pnl["revenue"] == pytest.approx(want)


def test_scalar_from_the_market_fallback():
    settlement = {"market_result": "scalar", "settlement_value_dollars": "0.6700"}
    assert ks.calculate_pnl(TRADE, settlement)["revenue"] == pytest.approx(1.34)


def test_yes_no_unchanged():
    assert ks.calculate_pnl(TRADE, {"market_result": "yes"})["won"] is True
    lost = ks.calculate_pnl(TRADE, {"market_result": "no"})
    assert lost["won"] is False and lost["net_pnl"] == pytest.approx(-2.07)


def test_calibration_skips_non_binary_settlements():
    row = {"fair_value": 0.6, "market_price_at_entry": 0.5, "ticker": TRADE["ticker"]}
    assert len(load_rows([{**row, "won": True}, {**row, "won": None}])) == 1
