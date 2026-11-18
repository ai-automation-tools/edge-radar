"""`kalshi_executor.py status` parses past main()'s execute-only setup.

B7 read `args.execute` unguarded, and `status` has no such flag, so every
status call (the execute wrappers, `make status`) died with AttributeError.
"""

import sys

import kalshi_executor as ke
import pytest


def test_status_subcommand_reaches_the_client(monkeypatch):
    def refuse(venue):
        raise NotImplementedError("stop before any network call")

    monkeypatch.setattr(ke, "get_market_client", refuse)
    monkeypatch.setattr(sys, "argv", ["kalshi_executor.py", "status"])
    with pytest.raises(SystemExit) as e:
        ke.main()
    assert e.value.code == 2


# ER-14: a trailing % means percent; "1%" was 100% of bankroll and "0.5%" was 50%.
@pytest.mark.parametrize(
    "raw, want",
    [
        ("1%", 0.01),
        ("0.5%", 0.005),
        ("12%", 0.12),
        ("100%", 1.0),
        ("15", 0.15),
        ("0.15", 0.15),
        ("150", 150.0),
        (None, None),
    ],
)
def test_parse_budget_arg(raw, want):
    assert ke.parse_budget_arg(raw) == (None if want is None else pytest.approx(want))


@pytest.mark.parametrize("raw", ["1", "1.0", "0", "-5", "0%", "150%", "nan", "inf", "abc"])
def test_parse_budget_arg_refuses(raw):
    with pytest.raises(ValueError):
        ke.parse_budget_arg(raw)
