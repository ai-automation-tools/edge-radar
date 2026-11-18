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
