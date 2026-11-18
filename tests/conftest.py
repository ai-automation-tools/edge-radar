"""Shared fixtures for Edge-Radar tests.

Path setup is handled by [tool.pytest.ini_options] pythonpath in
pyproject.toml.  This file only provides shared fixtures.
"""

import os
import tempfile

# Must run before any script module is imported: `setup_logging()` attaches
# its FileHandler at import time, so a fixture is too late. Without this,
# mocked failures from the test suite were written into the live logs/.
os.environ["EDGE_RADAR_LOG_DIR"] = tempfile.mkdtemp(prefix="edge_radar_test_logs_")

# ER-19: tests run on the code's defaults, never the operator's `.env`. Every
# script calls `load_dotenv()` at import, so a live knob (a sport frozen, a
# date cap, an exposure ceiling) used to fail tests on one machine only, and
# each one needed its own "ignore the operator's .env" fixture here. python-
# dotenv honours this switch in `load_dotenv()`; a profile would overlay
# `.env.<profile>`, so that goes too. Tests that want a knob set it themselves.
os.environ["PYTHON_DOTENV_DISABLED"] = "1"
os.environ.pop("EDGE_RADAR_PROFILE", None)

import pytest  # noqa: E402
import trade_log  # noqa: E402
from opportunity import Opportunity  # noqa: E402


@pytest.fixture(autouse=True)
def _isolate_data_logs(tmp_path, monkeypatch):
    """Defense-in-depth: never let a test read or write the real trade /
    settlement logs under data/history/.

    ``log_trade()`` persists via ``save_trade_log()`` as a side effect, so a
    test that calls it with an ad-hoc list (e.g. test_fill_accounting) would
    otherwise overwrite the live ``kalshi_trades.json`` with test records.
    Redirecting the module-level path constants to a per-test tmp dir makes
    every test hermetic regardless of how it exercises the I/O helpers.
    """
    monkeypatch.setattr(trade_log, "TRADE_LOG_PATH", tmp_path / "kalshi_trades.json")
    monkeypatch.setattr(trade_log, "SETTLEMENT_LOG_PATH", tmp_path / "kalshi_settlements.json")


@pytest.fixture(autouse=True)
def _isolate_venue_eligibility(tmp_path, monkeypatch):
    """Never let a test write the operator's real S3 eligibility cache.

    `_place_order_batch` calls `record_success()` on any create_order response
    whose status is not `dry_run_blocked` -- which a mocked client always is.
    So `make test` (test_execute_batch, test_fill_accounting, test_reconciliation)
    stamped `kalshi:sports = ok` into the live cache on evidence of a fake fill,
    turning the fail-closed preflight green with nothing behind it. Same lesson
    as `_isolate_data_logs`: a module-level path constant must be redirected for
    every test, not only the ones that think about it.
    """
    import venue_eligibility as vel

    monkeypatch.setattr(vel, "ELIGIBILITY_PATH", tmp_path / "venue_eligibility.json")


@pytest.fixture
def no_fees(monkeypatch):
    """Zero the exchange fee rate for tests that pin exact pre-fee arithmetic.

    Gate 3 and Kelly sizing became fee-aware on 2026-08-25. Tests written to pin
    the *price-complement* (C11) or *per-sport floor* mechanics are testing
    something orthogonal to fees, so they opt out here rather than re-deriving
    every expected number with a fee term folded in. Tests of the fee behaviour
    itself do not use this fixture.
    """
    from app.config import reset_config

    monkeypatch.setenv("KALSHI_FEE_RATE", "0")
    reset_config()
    yield
    monkeypatch.delenv("KALSHI_FEE_RATE", raising=False)
    reset_config()


@pytest.fixture
def sample_opportunity():
    """A basic approved-worthy Opportunity."""
    return Opportunity(
        ticker="KXMLBGAME-26MAR301840CWSMIA-MIA",
        title="Chicago WS vs Miami Winner? (vs Miami)",
        category="game",
        side="yes",
        market_price=0.45,
        fair_value=0.56,
        edge=0.11,
        edge_source="odds_consensus",
        confidence="high",
        liquidity_score=8.0,
        composite_score=8.5,
        details={"n_books": 8},
    )


@pytest.fixture
def low_edge_opportunity():
    """An Opportunity below typical edge threshold."""
    return Opportunity(
        ticker="KXMLBGAME-26MAR301840PITCIN-PIT",
        title="Pittsburgh vs Cincinnati Winner?",
        category="game",
        side="yes",
        market_price=0.50,
        fair_value=0.51,
        edge=0.01,
        edge_source="odds_consensus",
        confidence="low",
        liquidity_score=5.0,
        composite_score=3.0,
        details={},
    )
