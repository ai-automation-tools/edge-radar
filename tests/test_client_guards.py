"""ER-01: client-level cap and kill switch, plus the harness approval rules that front them.

`KalshiClient.create_order` is the one call every order passes through, so the cap and the
`data/KILL` switch live there. These tests build the client without credentials and replace
`_post`, so nothing can reach the venue.
"""

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import kalshi_client
import venue_eligibility as vel
from kalshi_client import KalshiClient, OrderRefusedError

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "_guard_live_orders", ROOT / "scripts" / "hooks" / "guard_live_orders.py"
)
guard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(guard)


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


@pytest.mark.parametrize(
    "command",
    [
        "python scripts/scan.py sports --filter nba --execute",
        ".venv/Scripts/python.exe scripts/scan.py sports --go",
        "cd x && python scan.py sports --mode execute --max-bets 3",
        "python scripts/scan.py sports --mode=execute",
        "python scripts/doctor.py --verify-eligibility --ticker KXT",
        'python -c "from kalshi_client import KalshiClient; KalshiClient().create_order(...)"',
        "python - <<'EOF'\nc.intra_exchange_transfer(5, 0, 3)\nEOF",
        "$env:DRY_RUN='true'; python scripts/scan.py sports --send-it",
    ],
)
def test_hook_blocks_order_commands(command):
    assert guard.blocked(command)


@pytest.mark.parametrize(
    "command",
    [
        "python scripts/scan.py sports --filter nba",  # preview
        "python scripts/scan.py sports --good-flag",  # --go needs a word boundary
        "git commit -m 'fix(ER-01): --execute help text'",
        "grep -n create_order scripts/kalshi/kalshi_client.py",
        "python -m pytest tests/test_client_guards.py -q",
    ],
)
def test_hook_allows_everything_else(command):
    assert not guard.blocked(command)


def test_hook_exits_2_and_is_wired_for_both_shells(monkeypatch, capsys):
    import io

    monkeypatch.setattr(
        "sys.stdin", io.StringIO(json.dumps({"tool_input": {"command": "python scan.py --go"}}))
    )
    assert guard.main() == 2 and "! <command>" in capsys.readouterr().err

    rules = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    (entry,) = rules["hooks"]["PreToolUse"]
    assert entry["matcher"] == "Bash|PowerShell"
    assert "guard_live_orders.py" in entry["hooks"][0]["command"]
    assert "Edit(./.env)" in rules["permissions"]["deny"]


def test_skill_and_agent_do_not_invite_bypasses():
    skill = (ROOT / "skills" / "edge-radar" / "SKILL.md").read_text(encoding="utf-8")
    assert "disable-model-invocation: true" in skill.split("---")[1]
    assert "no confirmation needed" not in skill and "still asks" not in skill
    for agent in (ROOT / ".claude" / "agents").glob("*.md"):  # ER-26 retired kalshi-bettor
        text = agent.read_text(encoding="utf-8")
        assert "insist" not in text and "just do it" not in text, agent.name
