"""Headless agent sessions for the unattended maintenance scripts.

Runs ``claude -p`` by default. When ``AGENT_CLI`` is set (in ``.env``) to a PowerShell
agent adapter -- a script that takes the prompt on stdin, prints the session's final text
and accepts ``-Model``, ``-AllowTools``, ``-MaxTurns`` and ``-Timeout`` -- the session goes
through it instead, so the provider and model mapping live in one place outside this repo.

Either way the prompt goes in on stdin and ``allow_tools`` is a real allowlist: only those
tools exist, anything no rule allows is refused, and user-level settings don't apply.
(``--allowedTools`` alone only pre-approves; other tools a user's settings allow still run.)
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


def _adapter() -> str:
    """AGENT_CLI from the environment, else from the repo's .env (not every caller loads it)."""
    # Read before app.config: drift_autofix's orchestrator never builds a Config.
    value = os.environ.get("AGENT_CLI", "").strip()  # config-bootstrap
    if not value and _ENV_FILE.exists():
        from dotenv import dotenv_values

        value = (dotenv_values(_ENV_FILE).get("AGENT_CLI") or "").strip()
    return value


def agent_command(
    *,
    model: str | None = None,
    allow_tools: list[str] | None = None,
    max_turns: int | None = None,
    timeout: int | None = None,
) -> list[str]:
    """The command line for one session. Without allow_tools it runs unrestricted."""
    adapter = _adapter()
    if adapter:
        cmd = ["pwsh", "-NoProfile", "-File", adapter]
        if model:
            cmd += ["-Model", model]
        if allow_tools:
            cmd += ["-AllowTools", ",".join(allow_tools)]
        if max_turns:
            cmd += ["-MaxTurns", str(max_turns)]
        if timeout:
            cmd += ["-Timeout", f"{timeout}s"]  # the adapter kills the whole session tree
        return cmd
    cmd = ["claude", "-p"]
    if model:
        cmd += ["--model", model]
    if allow_tools:
        names = sorted({re.sub(r"\(.*$", "", t).strip() for t in allow_tools})
        cmd += [
            "--tools",
            ",".join(names),
            "--allowedTools",
            ",".join(allow_tools),
            "--permission-mode",
            "dontAsk",
            "--setting-sources",
            "project",
        ]
    else:
        cmd.append("--dangerously-skip-permissions")
    if max_turns:
        cmd += ["--max-turns", str(max_turns)]
    return cmd


def run_agent(
    prompt: str,
    *,
    cwd: Path,
    timeout: int,
    model: str | None = None,
    allow_tools: list[str] | None = None,
    max_turns: int | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run one session; raises FileNotFoundError / subprocess.TimeoutExpired like subprocess.run."""
    cmd = agent_command(model=model, allow_tools=allow_tools, max_turns=max_turns, timeout=timeout)
    # Through the adapter its own deadline fires first (exit 124); this one is the backstop.
    py_timeout = timeout + 120 if cmd[0] == "pwsh" else timeout
    return subprocess.run(
        cmd,
        input=prompt,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=py_timeout,
        check=False,
    )
