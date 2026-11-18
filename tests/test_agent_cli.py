"""agent_cli builds a real allowlist on both paths (plain claude and the AGENT_CLI adapter)."""

import re
import subprocess
from pathlib import Path

import agent_cli
import pytest


def _plain(monkeypatch):
    monkeypatch.delenv("AGENT_CLI", raising=False)
    monkeypatch.setattr(agent_cli, "_ENV_FILE", agent_cli.Path("does-not-exist.env"))


def test_plain_allowlist_is_enforced_not_just_preapproved(monkeypatch):
    _plain(monkeypatch)
    cmd = agent_cli.agent_command(
        model="opus", allow_tools=["Read", "Edit(tests/**)"], max_turns=60
    )
    assert cmd[:2] == ["claude", "-p"]
    assert cmd[cmd.index("--tools") + 1] == "Edit,Read"
    assert cmd[cmd.index("--allowedTools") + 1] == "Read,Edit(tests/**)"
    assert cmd[cmd.index("--permission-mode") + 1] == "dontAsk"
    assert cmd[cmd.index("--setting-sources") + 1] == "project"
    assert "--dangerously-skip-permissions" not in cmd


def test_no_allowlist_is_refused(monkeypatch):
    _plain(monkeypatch)
    with pytest.raises(ValueError):
        agent_cli.agent_command(model="opus")
    monkeypatch.setenv("AGENT_CLI", "adapter.ps1")
    with pytest.raises(ValueError):
        agent_cli.agent_command(model="opus", allow_tools=[])


def test_unrestricted_must_be_asked_for_by_name(monkeypatch):
    _plain(monkeypatch)
    assert "--dangerously-skip-permissions" in agent_cli.agent_command(unrestricted=True)


# An argv list starting with "claude" (the audit's own criterion); prose mentioning
# `claude -p` in docstrings and help text is fine.
_SHELLS_CLAUDE = re.compile(r"""\[\s*["']claude["']\s*,""")


def test_only_agent_cli_shells_claude_p():
    """ER-09: every tracked script reaches `claude -p` through agent_cli."""
    root = Path(__file__).resolve().parents[1]
    tracked = subprocess.run(
        ["git", "ls-files", "scripts", "app"], cwd=root, capture_output=True, text=True, check=True
    ).stdout.split()
    hits = [
        f
        for f in tracked
        if f.endswith(".py")
        and f != "scripts/shared/agent_cli.py"
        and _SHELLS_CLAUDE.search((root / f).read_text(encoding="utf-8", errors="replace"))
    ]
    assert hits == []


def test_adapter_gets_the_same_request(monkeypatch):
    monkeypatch.setenv("AGENT_CLI", r"C:\x\Invoke-AgentCli.ps1")
    cmd = agent_cli.agent_command(
        model="opus", allow_tools=["Read", "Grep"], max_turns=40, timeout=900
    )
    assert cmd[:4] == ["pwsh", "-NoProfile", "-File", r"C:\x\Invoke-AgentCli.ps1"]
    assert cmd[cmd.index("-AllowTools") + 1] == "Read,Grep"
    assert cmd[cmd.index("-Timeout") + 1] == "900s"
    assert "claude" not in cmd
