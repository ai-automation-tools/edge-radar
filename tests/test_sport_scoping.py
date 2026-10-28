"""2026-10-27 betting-logic review: per-sport scoping in the scanner.

1. The six European soccer leagues were wired as bare `KX<LEAGUE>` series,
   which Kalshi does not have (the series are `KX<LEAGUE>GAME/SPREAD/TOTAL`).
   Every scan fetched zero markets for them, silently, all season.
2. NBA/NHL rest-day data was keyed by team abbreviation alone, so it leaked
   into every sport sharing one (MLS totals took the NBA's +1.5 back-to-back
   stdev on a 1.5-goal base) and one date's rest overwrote another's.
3. Sharp-money signals were one flat dict across sports, matched by substring.
"""

import edge_detector as ed
from ticker_display import _detect_sport

LEAGUES = ("EPL", "LALIGA", "UCL", "SERIEA", "BUNDESLIGA", "LIGUE1")


def test_european_leagues_use_real_series_prefixes():
    for lg in LEAGUES:
        assert f"KX{lg}" not in ed.KALSHI_TO_ODDS_SPORT
        for kind, cat in (("GAME", "game"), ("SPREAD", "spread"), ("TOTAL", "total")):
            prefix = f"KX{lg}{kind}"
            assert prefix in ed.KALSHI_TO_ODDS_SPORT
            assert ed.categorize_market(prefix + "-26NOV02NEWEVE-NEW3") == cat
            # Soccer stdevs, the discrete-margin spread guard, and the
            # MIN_EDGE_THRESHOLD_SOCCER floor all key off these.
            assert ed._sport_for_ticker(prefix + "-26NOV02NEWEVE-NEW3") == "soccer"
            assert _detect_sport(prefix + "-26NOV02NEWEVE-NEW3") == "soccer"
            assert prefix in ed.FILTER_SHORTCUTS["eurosoccer"]
            assert prefix in ed.FILTER_SHORTCUTS["soccer"]


def test_sharp_signal_needs_exact_team_match():
    sig = {"NE": {"sharp_signal": "over", "signal_reason": "x"}}
    # "ne" is a substring of "Tennessee" and "MIN" -- neither is New England.
    assert not ed._sharp_money_signal("TEN", "yes", "KXNFLTOTAL-26NOV01HOUTEN-44", sig)[
        "signal_found"
    ]
    assert not ed._sharp_money_signal(
        "Tennessee Titans", "yes", "KXNFLSPREAD-26NOV01HOUTEN-TEN3", sig
    )["signal_found"]
    hit = ed._sharp_money_signal("MIA", "yes", "KXNFLTOTAL-26NOV01NEMIA-44", sig)
    assert hit["signal_found"] and hit["agrees_with_bet"] is True


def _scan_with(monkeypatch, markets, rest_by_sport_date, sharp_by_sport):
    """Run scan_all_markets over canned markets; capture what each detector got."""
    seen = {}

    class _Client:
        def get_markets(self, series_ticker=None, **_):
            return {"markets": [m for m in markets if m["ticker"].startswith(series_ticker)]}

    def _fake_total(market, events, sharp_signals=None, rest_data=None, **_):
        seen[market["ticker"]] = {"rest": rest_data, "sharp": sharp_signals}
        return None

    monkeypatch.setattr(ed, "get_current_key", lambda: "k")
    monkeypatch.setattr(ed, "fetch_odds_api", lambda sport, markets=None: [])
    monkeypatch.setattr(ed, "get_line_movement", lambda sport: sharp_by_sport.get(sport, []))
    monkeypatch.setattr(
        ed, "prefetch_rest_data", lambda sport, gd: rest_by_sport_date.get((sport, gd), {})
    )
    monkeypatch.setattr(ed, "prefetch_mlb_pitchers", lambda gd: {})
    monkeypatch.setattr(ed, "get_game_weather", lambda *a, **k: None)
    monkeypatch.setattr(ed, "detect_edge_total", _fake_total)
    ed.scan_all_markets(_Client(), ticker_filter="KXNBATOTAL,KXMLSTOTAL,KXNHLTOTAL")
    return seen


def test_rest_and_sharp_data_stay_in_their_own_sport_and_date(monkeypatch):
    markets = [
        {"ticker": "KXNBATOTAL-26OCT28GSWDAL-230"},
        {"ticker": "KXNBATOTAL-26OCT29BOSDAL-230"},
        {"ticker": "KXMLSTOTAL-26OCT28HOUDAL-3"},
        {"ticker": "KXNHLTOTAL-26OCT28BOSDAL-6"},
    ]
    nba28 = {"DAL": {"is_b2b": True, "stdev_adjustment": 1.5}}
    nba29 = {"DAL": {"is_b2b": False, "stdev_adjustment": 0.0}}
    nhl28 = {"DAL": {"is_b2b": False, "stdev_adjustment": -0.1}}
    rest = {
        ("basketball_nba", "2026-10-28"): nba28,
        ("basketball_nba", "2026-10-29"): nba29,
        ("icehockey_nhl", "2026-10-28"): nhl28,
    }
    nba_move = {"home_team": "DAL", "away_team": "GSW", "sharp_signal": "over"}
    seen = _scan_with(monkeypatch, markets, rest, {"basketball_nba": [nba_move]})

    assert seen["KXNBATOTAL-26OCT28GSWDAL-230"]["rest"] == nba28["DAL"]
    assert seen["KXNBATOTAL-26OCT29BOSDAL-230"]["rest"] == nba29["DAL"]
    assert seen["KXNHLTOTAL-26OCT28BOSDAL-6"]["rest"] == nhl28["DAL"]
    assert seen["KXMLSTOTAL-26OCT28HOUDAL-3"]["rest"] is None
    assert "DAL" in seen["KXNBATOTAL-26OCT28GSWDAL-230"]["sharp"]
    assert seen["KXMLSTOTAL-26OCT28HOUDAL-3"]["sharp"] == {}
    assert seen["KXNHLTOTAL-26OCT28BOSDAL-6"]["sharp"] == {}


def test_drift_check_flags_sport_with_odds_but_no_series(monkeypatch, tmp_path):
    """The dead European prefixes sat in "Context: no open markets" all season.
    A sport whose every series is empty while the books list games is now WARN."""
    from datetime import datetime, timedelta, timezone

    import integration_drift as idr

    soon = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    monkeypatch.setattr(idr, "KalshiClient", lambda: None)
    monkeypatch.setattr(idr, "fetch_series", lambda client, prefix: [])
    monkeypatch.setattr(
        idr,
        "load_cached_events",
        lambda sport: ([{"commence_time": soon}], 1.0) if sport == "soccer_epl" else ([], None),
    )
    monkeypatch.setattr(idr, "BASELINE_PATH", tmp_path / "baseline.json")
    monkeypatch.setattr(idr, "last_bet_by_sport", lambda: {})
    out = tmp_path / "drift.json"
    idr.run(save=False, update_baseline=False, analyze="never", json_out=str(out))

    import json

    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["status"] == "WARN"
    assert [d["sport"] for d in payload["dark"]] == ["soccer_epl"]
