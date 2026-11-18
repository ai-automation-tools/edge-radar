"""ER-16: Gate 1 sums a calendar day in DAILY_LOSS_TZ, not UTC's."""

from datetime import datetime, timezone

import pytest

from trade_log import get_today_pnl

NY = "America/New_York"
CHECK = datetime(2026, 11, 19, 1, 0, tzinfo=timezone.utc)  # 8 pm ET on Nov 18


def _row(closed_at, pnl=-10):
    return {"net_pnl": pnl, "closed_at": closed_at}


def test_losses_either_side_of_utc_midnight_share_one_eastern_day():
    rows = [_row("2026-11-18T23:30:00Z"), _row("2026-11-19T00:30:00+00:00")]
    assert get_today_pnl(rows, now=CHECK, tz=NY) == -20
    assert get_today_pnl(rows, now=CHECK, tz="UTC") == -10  # the old split


def test_the_eastern_day_ends_at_eastern_midnight():
    rows = [_row("2026-11-18T04:59:00Z"), _row("2026-11-18T05:01:00Z")]  # 23:59 / 00:01 ET
    assert get_today_pnl(rows, now=CHECK, tz=NY) == -10


def test_naive_and_malformed_stamps_never_hide_a_loss():
    rows = [
        _row("2026-11-19T00:30:00"),  # naive -> UTC -> Nov 18 ET
        _row("2026-11-18 garbage"),  # unparseable, but dated today ET
        _row(None),
        _row("2026-11-17T12:00:00Z"),
    ]
    assert get_today_pnl(rows, now=CHECK, tz=NY) == -20


def test_zone_comes_from_config(monkeypatch):
    from app import config

    monkeypatch.setenv("DAILY_LOSS_TZ", "UTC")
    config.reset_config()
    try:
        rows = [_row("2026-11-18T23:30:00Z")]
        assert get_today_pnl(rows, now=CHECK) == 0
    finally:
        monkeypatch.delenv("DAILY_LOSS_TZ")
        config.reset_config()
    assert get_today_pnl([_row("2026-11-18T23:30:00Z")], now=CHECK) == -10


def test_bad_zone_fails_validation(monkeypatch):
    from app import config

    monkeypatch.setenv("DAILY_LOSS_TZ", "Mars/Olympus")
    config.reset_config()
    try:
        with pytest.raises(ValueError, match="DAILY_LOSS_TZ"):
            config.get_config()
    finally:
        monkeypatch.delenv("DAILY_LOSS_TZ")
        config.reset_config()
