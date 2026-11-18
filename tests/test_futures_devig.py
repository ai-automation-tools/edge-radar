"""ER-42 / B5: power de-vig behind FUTURES_DEVIG, and the shadow-book A/B that judges it."""

import pytest

import futures_edge as fe
import shadow_book as sb

FIELD = [  # one favourite, two mid, one longshot: raw implied total ~1.18
    {"name": "Fav", "price": 1.9},
    {"name": "Mid A", "price": 3.5},
    {"name": "Mid B", "price": 4.5},
    {"name": "Long", "price": 7.0},
]


def test_power_sums_to_one_and_takes_more_from_the_longshot():
    prop = fe.devig_nway(FIELD, "proportional")
    powr = fe.devig_nway(FIELD, "power")
    assert sum(prop.values()) == pytest.approx(1.0)
    assert sum(powr.values()) == pytest.approx(1.0, abs=1e-9)
    assert powr["Long"] < prop["Long"]  # the longshot keeps less of the overround
    assert powr["Fav"] > prop["Fav"]


def test_power_skips_an_incomplete_book():
    partial = [{"name": "Fav", "price": 2.2}, {"name": "Mid A", "price": 4.0}]  # total ~0.70
    assert fe.devig_nway(partial, "power") == {}
    assert fe.devig_nway(partial, "proportional")  # unchanged behaviour


def test_default_is_proportional_and_power_is_opt_in(monkeypatch):
    from app import config

    assert fe.devig_nway(FIELD) == fe.devig_nway(FIELD, "proportional")
    monkeypatch.setenv("FUTURES_DEVIG", "power")
    config.reset_config()
    try:
        assert fe.devig_nway(FIELD) == fe.devig_nway(FIELD, "power")
        monkeypatch.setenv("FUTURES_DEVIG", "shin")
        config.reset_config()
        with pytest.raises(ValueError, match="FUTURES_DEVIG"):
            config.get_config()
    finally:
        monkeypatch.delenv("FUTURES_DEVIG")
        config.reset_config()


def test_devig_review_reports_both_briers():
    def row(fair, power, price, won):
        return {
            "ticker": f"KXNBA-26-{fair}",
            "side": "yes",
            "market_price": price,
            "fair_value": fair,
            "details": {"devig_ab": True, "fair_power": power},
            "won": won,
        }

    rows = [row(0.30, 0.25, 0.28, False), row(0.50, 0.55, 0.52, True), row(0.10, 0.06, 0.08, False)]
    text = sb.devig_review(rows + [dict(row(0.2, 0.2, 0.2, None))])
    assert "3 settled rows (1 still open)" in text
    assert "PROPORTIONAL Brier" in text and "POWER Brier" in text and "MARKET Brier" in text
    assert "No settled A/B rows yet" in sb.devig_review([])


def test_devig_ab_rows_prices_every_market_under_both_methods(monkeypatch):
    """No edge filter and no side choice: each matched market gets both fair values."""

    class Client:
        def get_markets(self, **kw):
            if kw.get("series_ticker") != "KXNBA":
                return {"markets": []}
            return {
                "markets": [
                    {"ticker": "KXNBA-26-FAV", "yes_sub_title": "Fav", "yes_ask_dollars": "0.40"},
                    {"ticker": "KXNBA-26-LONG", "yes_sub_title": "Long", "yes_ask_dollars": "0.20"},
                    {
                        "ticker": "KXNBA-26-NONE",
                        "yes_sub_title": "Nobody",
                        "yes_ask_dollars": "0.05",
                    },
                ]
            }

    book = {"key": "pinnacle", "markets": [{"key": "outrights", "outcomes": FIELD}]}
    monkeypatch.setattr(fe, "fetch_outrights", lambda sport_key: [{"bookmakers": [book]}])
    monkeypatch.setattr(fe, "get_current_key", lambda: "k")
    rows = {r["ticker"]: r for r in fe.devig_ab_rows(Client(), "KXNBA")}
    assert set(rows) == {"KXNBA-26-FAV", "KXNBA-26-LONG"}  # "Nobody" has no outright
    long_ = rows["KXNBA-26-LONG"]
    assert long_["fair_power"] < long_["fair_proportional"]
    assert long_["market_price"] == 0.20
