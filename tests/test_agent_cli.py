"""agent_cli builds a real allowlist on both paths (plain claude and the AGENT_CLI adapter)."""

import agent_cli


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


def test_plain_without_allowlist_skips_permissions(monkeypatch):
    _plain(monkeypatch)
    assert "--dangerously-skip-permissions" in agent_cli.agent_command(model="opus")


def test_adapter_gets_the_same_request(monkeypatch):
    monkeypatch.setenv("AGENT_CLI", r"C:\x\Invoke-AgentCli.ps1")
    cmd = agent_cli.agent_command(
        model="opus", allow_tools=["Read", "Grep"], max_turns=40, timeout=900
    )
    assert cmd[:4] == ["pwsh", "-NoProfile", "-File", r"C:\x\Invoke-AgentCli.ps1"]
    assert cmd[cmd.index("-AllowTools") + 1] == "Read,Grep"
    assert cmd[cmd.index("-Timeout") + 1] == "900s"
    assert "claude" not in cmd
