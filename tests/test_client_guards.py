"""ER-01: client-level cap and kill switch, plus the harness approval rules that front them.

`KalshiClient.create_order` is the one call every order passes through, so the cap and the
`data/KILL` switch live there. These tests build the client without credentials and replace
`_post`, so nothing can reach the venue.
"""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import kalshi_client
import venue_eligibility as vel
from kalshi_client import KalshiClient, OrderRefusedError

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def live(monkeypatch, tmp_path):
    """A non-demo, DRY_RUN=false client with MAX_BET_SIZE=$10 and a recording `_post`."""
    client = KalshiClient.__new__(KalshiClient)
    client.dry_run, client.is_demo, client.subaccount = False, False, 0
    client.posts = []
    client._post = lambda path, body=None: client.posts.append((path, body)) or {"order": {}}
    cfg = SimpleNamespace(risk=SimpleNamespace(max_bet_size=10.0))
    monkeypatch.setattr(kalshi_client, "get_config", lambda: cfg)
    monkeypatch.setattr(kalshi_client, "KILL_FILE", tmp_path / "KILL")
    return client


def _buy(client, side, count, cents):
    price = {"yes_price_cents": cents} if side == "yes" else {"no_price_cents": cents}
    return client.create_order(ticker="KXT", side=side, action="buy", count=count, **price)


def test_oversized_order_raises_before_post(live):
    with pytest.raises(OrderRefusedError, match="MAX_BET_SIZE"):
        _buy(live, "yes", 1000, 99)
    assert live.posts == []


def test_order_within_cap_is_sent(live):
    _buy(live, "yes", 10, 56)  # $5.60
    assert len(live.posts) == 1


def test_no_side_is_costed_at_the_no_price(live):
    _buy(live, "no", 20, 40)  # $8.00 (the YES-equivalent 60c would read $12)
    with pytest.raises(OrderRefusedError):
        _buy(live, "no", 30, 40)  # $12.00
    assert len(live.posts) == 1


def test_one_cent_rounding_slack(live):
    # The executor sizes 28 contracts at a 35.5c market price ($9.94) and places at 36c ($10.08).
    _buy(live, "yes", 28, 36)
    assert len(live.posts) == 1


def test_kill_file_refuses_orders_and_transfers(live):
    kalshi_client.KILL_FILE.touch()
    with pytest.raises(OrderRefusedError, match="kill switch"):
        _buy(live, "yes", 1, 1)
    with pytest.raises(OrderRefusedError, match="kill switch"):
        live.intra_exchange_transfer(1.0, source_shard=0, destination_shard=3)
    assert live.posts == []


def test_dry_run_still_short_circuits(live):
    kalshi_client.KILL_FILE.touch()
    live.dry_run = True
    assert _buy(live, "yes", 1000, 99)["status"] == "dry_run_blocked"


def test_refusals_never_disable_a_venue(live):
    # The executor's generic handler feeds str(e) to the structural-block check.
    with pytest.raises(OrderRefusedError) as cap:
        _buy(live, "yes", 1000, 99)
    kalshi_client.KILL_FILE.touch()
    with pytest.raises(OrderRefusedError) as kill:
        _buy(live, "yes", 1, 1)
    for exc in (cap, kill):
        assert not vel.is_structural_rejection(str(exc.value))


def test_harness_asks_before_order_commands():
    rules = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    ask = rules["permissions"]["ask"]
    for needle in ("--execute", "--go", "--send-it", "--mode execute", "create_order"):
        assert any(needle in r and r.startswith("Bash(") for r in ask), needle
        assert any(needle in r and r.startswith("PowerShell(") for r in ask), needle
    assert "Edit(./.env)" in rules["permissions"]["deny"]


def test_skill_and_agent_do_not_invite_bypasses():
    skill = (ROOT / "skills" / "edge-radar" / "SKILL.md").read_text(encoding="utf-8")
    assert "disable-model-invocation: true" in skill.split("---")[1]
    assert "no confirmation needed" not in skill
    agent = (ROOT / ".claude" / "agents" / "KALSHI_BETTOR.md").read_text(encoding="utf-8")
    assert "insist" not in agent and "just do it" not in agent
