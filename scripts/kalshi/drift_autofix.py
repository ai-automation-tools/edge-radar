#!/usr/bin/env python
"""Auto-fix stage of Integration-Drift-Check: propose a fix as a DRAFT PR.

Called by integration_drift.py --autofix on WARN/FAIL days only. A headless
Claude session edits a throwaway git worktree; everything after that is
deterministic and decides whether a PR exists at all:

  1. no diff                          -> no PR ("no code change proposed")
  2. a path outside ALLOWED / a delete -> no PR (rejected)
  3. fewer tests collected, or a fail  -> one retry with the failure, then no PR
  4. probe on the fixed tree not better than today's -> no PR
  5. otherwise: commit, push `drift-fix/<date>`, open a DRAFT PR into mike_desktop

Never merges, never touches the main checkout, master or mike_desktop, .env, or
the money path (executor, risk gates, config, the Kalshi client). A still-open
drift-fix PR suppresses new attempts, so an unresolved issue does not spawn a PR a day.

Containment (ER-04), because agent-written code runs here before any human
reviews it:
  - the fix session can read only inside the worktree (`Read(./**)` etc.), and its
    prompt carries the probe output only, never the WebFetch-capable analysis;
  - the worktree's tests and probe run with an allowlisted environment: no
    `.env`, no credentials, `DRY_RUN=true`, and the probe reads markets unsigned;
  - the public PR and commit carry the probe table, a diff stat and the test
    tail, not the session's own words (those go to the owner's email only).

The venv's edge_radar.pth pins the MAIN repo's script dirs to the front of
sys.path, so a plain `pytest` in the worktree would test the main checkout.
`--in-tree` re-points sys.path at the worktree before running anything.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from agent_cli import run_agent  # scripts/shared

MAIN = Path(__file__).resolve().parents[2]
PYTHON = MAIN / ".venv" / "Scripts" / "python.exe"
BASE_BRANCH = "mike_desktop"
BRANCH_PREFIX = "drift-fix/"
# What a drift fix may touch: parsing/matching code and tests. Not the probe
# itself (it would grade its own homework), not the executor, risk gates or the
# Kalshi client (it places orders).
ALLOWED = re.compile(
    r"^(scripts/kalshi/(edge_detector|futures_edge)\.py"
    r"|scripts/shared/(ticker_display|odds_api|market_client)\.py"
    r"|tests/[\w/]+\.py)$"
)
_SUBDIRS = (
    "",
    "scripts/shared",
    "scripts/kalshi",
    "scripts/prediction",
    "scripts/schedulers",
    "scripts",
)
_RANK = {"OK": 0, "WARN": 1, "FAIL": 2}
# The only variables the worktree's tests and probe inherit: enough for Windows,
# Python and git to run. Everything else (API keys, Resend/GitHub tokens, the
# AGENT_CLI path) stays behind. Windows upper-cases os.environ keys.
_ENV_KEEP = {
    "APPDATA",
    "COMPUTERNAME",
    "COMSPEC",
    "HOME",
    "HOMEDRIVE",
    "HOMEPATH",
    "LANG",
    "LOCALAPPDATA",
    "NUMBER_OF_PROCESSORS",
    "OS",
    "PATH",
    "PATHEXT",
    "PROCESSOR_ARCHITECTURE",
    "PROGRAMDATA",
    "PROGRAMFILES",
    "PROGRAMFILES(X86)",
    "SYSTEMDRIVE",
    "SYSTEMROOT",
    "TEMP",
    "TMP",
    "TZ",
    "USERNAME",
    "USERPROFILE",
    "WINDIR",
}
INPUT_DIR = "data/drift_input"  # gitignored; the probe output the fix session may read

FIX_PROMPT = """You are fixing an Edge-Radar integration drift, unattended, in a throwaway
git worktree (the current directory). Read CLAUDE.md and the CHANGELOG entry
"2026-10-03 -- M1" first: Kalshi changed market wording/fields and the scanner
silently stopped scoring markets.

Today's probe output (flagged series, unparsed/unmatched examples): {md}
Full probe JSON: {js}
You can read only files inside this worktree.
{retry}
Make the SMALLEST fix that makes the flagged markets parse and match again, in
scripts/kalshi/edge_detector.py (or futures_edge.py /
scripts/shared/ticker_display.py / odds_api.py / market_client.py only if the cause
is there). Add a regression test using the real wording from the examples, in
tests/test_edge_detection.py. Keep existing tests passing; do not delete or weaken
any test. Do not edit anything else -- other paths are rejected automatically, and
so is the whole fix. Match the surrounding code style and comment density.

If the flags are a probe false positive, or you are not confident in a fix, change
NOTHING and say why -- no change is a valid outcome and opens no PR. The full test
suite and the probe are re-run after you finish; you do not need to run them.
End with a 3-6 line summary of what you changed and why.
"""


# ── In-tree runner (child process) ───────────────────────────────────────────


def _in_tree(tree: Path, argv: list[str]) -> int:
    main_dirs = {str((MAIN / d).resolve()) if d else str(MAIN.resolve()) for d in _SUBDIRS}
    sys.path[:] = [p for p in sys.path if str(Path(p).resolve()) not in main_dirs]
    for d in reversed(_SUBDIRS):
        sys.path.insert(0, str(tree / d) if d else str(tree))
    os.chdir(tree)
    # ER-04: no .env and no key path. The worktree has neither, _tree_env() passed no
    # credentials, and the probe reads markets unsigned. Agent-written tests run here.
    os.environ["DRY_RUN"] = "true"  # config-bootstrap
    if argv[0] == "pytest":
        import pytest

        return pytest.main(argv[1:])
    import runpy

    sys.argv = [str(tree / argv[0]), *argv[1:]]
    try:
        runpy.run_path(sys.argv[0], run_name="__main__")
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 0
    return 0


def _tree_env() -> dict[str, str]:
    """The child's environment: the allowlist above, plus DRY_RUN=true."""
    env = {k: v for k, v in os.environ.items() if k.upper() in _ENV_KEEP}  # config-bootstrap
    env["DRY_RUN"] = "true"
    return env


def _tree_run(tree: Path, *argv: str, timeout: int = 900) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(PYTHON), str(Path(__file__).resolve()), "--in-tree", str(tree), *argv],
        env=_tree_env(),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )


# ── Orchestrator ─────────────────────────────────────────────────────────────


def _git(*args: str, cwd: Path = MAIN, check: bool = True) -> str:
    out = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8", check=False
    )
    if check and out.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {out.stderr.strip()[-300:]}")
    # rstrip only: `git status --porcelain` lines start with a space (" M path"),
    # and a full strip() shifted the first path by one char ("cripts/...").
    return out.stdout.rstrip()


def _open_fix_pr() -> str | None:
    out = subprocess.run(
        ["gh", "pr", "list", "--state", "open", "--json", "url,headRefName"],
        cwd=MAIN,
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        prs = json.loads(out.stdout or "[]")
    except ValueError:
        return None
    return next((p["url"] for p in prs if p["headRefName"].startswith(BRANCH_PREFIX)), None)


def _changed(tree: Path) -> list[tuple[str, str]]:
    """(status, path) for every change incl. untracked, '/'-separated."""
    rows = []
    for line in _git(
        "status", "--porcelain", "--untracked-files=all", cwd=tree, check=False
    ).splitlines():
        status, path = line[:2].strip(), line[3:].strip().strip('"').replace("\\", "/")
        if " -> " in path:
            path = path.split(" -> ")[1]
        rows.append((status, path))
    return rows


def _collected(tree: Path) -> int:
    out = _tree_run(tree, "pytest", "tests", "--collect-only", "-q").stdout
    m = re.search(r"(\d+) tests? collected", out)
    return int(m.group(1)) if m else 0


def _probe(tree: Path) -> dict:
    out_json = tree / "data" / "probe_after.json"
    _tree_run(tree, "scripts/kalshi/integration_drift.py", "--json-out", str(out_json))
    try:
        return json.loads(out_json.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"status": "FAIL", "series": []}


def _score(probe: dict) -> int:
    return sum(_RANK.get(s.get("level", "OK"), 0) for s in probe.get("series", []))


# ER-04: reads scoped to the worktree. A bare `Read`/`Grep` allow rule approves
# reads anywhere (verified 2026-11-17: it returned a file from the parent folder);
# the `(./**)` forms refuse them under dontAsk while reads inside still work.
FIX_TOOLS = [
    "Read(./**)",
    "Grep(./**)",
    "Glob(./**)",
    "Edit(scripts/**)",
    "Edit(tests/**)",
    "Write(tests/**)",
]


def _claude_fix(tree: Path, retry: str) -> str:
    prompt = FIX_PROMPT.format(
        md=f"{INPUT_DIR}/probe.md", js=f"{INPUT_DIR}/probe.json", retry=retry
    )
    tools = FIX_TOOLS
    try:
        proc = run_agent(
            prompt, cwd=tree, timeout=1500, model="opus", allow_tools=tools, max_turns=60
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        return f"(fix session did not complete: {type(e).__name__})"
    return (proc.stdout or proc.stderr or "").strip()


def _verify(tree: Path, baseline_tests: int, before: dict) -> tuple[str | None, dict, str]:
    """Return (rejection reason or None, probe_after, pytest tail)."""
    changes = _changed(tree)
    bad = [p for s, p in changes if s == "D" or not ALLOWED.match(p)]
    if bad:
        return f"touched disallowed paths or deleted files: {', '.join(bad)}", {}, ""
    if _collected(tree) < baseline_tests:
        return "fewer tests collected than before the fix", {}, ""
    res = _tree_run(tree, "pytest", "tests", "-q", "-x", "-p", "no:cacheprovider")
    tail = "\n".join(res.stdout.strip().splitlines()[-25:])
    if res.returncode != 0:
        return "test suite failed", {}, tail
    after = _probe(tree)
    if _score(after) >= _score(before):
        return (
            f"probe did not improve ({before.get('status')} -> {after.get('status')})",
            after,
            tail,
        )
    return None, after, tail


def _flag_table(before: dict, after: dict) -> str:
    a = {s["prefix"]: s for s in after.get("series", [])}
    rows = ["| Series | Before | After |", "|:--|:--|:--|"]
    for s in before.get("series", []):
        if s.get("level") != "OK":
            t = a.get(s["prefix"], {})
            rows.append(
                f"| {s['prefix']} | {s['level']}: {'; '.join(s.get('reasons', []))} "
                f"| {t.get('level', '?')} {'; '.join(t.get('reasons', []))} |"
            )
    return "\n".join(rows)


def _commit_and_pr(tree: Path, branch: str, before: dict, after: dict, tail: str) -> str:
    """Commit, push and open the draft. ER-04: nothing the session wrote goes public
    except the diff itself; its summary is in the owner's emailed report."""
    _git("add", "-A", cwd=tree)
    stat = _git("diff", "--cached", "--stat", cwd=tree, check=False)
    msg = (
        f"fix(drift): auto-proposed fix for {before.get('status')} drift probe\n\n"
        f"{stat}\n\n"
        "Opened by Integration-Drift-Check (drift_autofix.py). Review before merging.\n\n"
        "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
    )
    for _ in range(2):  # black may reformat on the first attempt; re-stage once
        res = subprocess.run(
            ["git", "commit", "-q", "-F", "-"],
            input=msg,
            cwd=tree,
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0:
            break
        _git("add", "-A", cwd=tree)
    else:
        raise RuntimeError(f"commit failed (pre-commit): {(res.stdout + res.stderr)[-400:]}")
    _git("push", "-q", "origin", f"HEAD:refs/heads/{branch}", cwd=tree)
    body = (
        "**Draft opened automatically by `Integration-Drift-Check`.** Never auto-merged — "
        "review the diff, then merge into `mike_desktop` as usual.\n\n"
        f"## Probe\n\n{_flag_table(before, after)}\n\n"
        f"## Changed\n\n```\n{stat}\n```\n\n"
        "The fix session's own summary is in the owner's drift-check email.\n\n"
        f"## Verification\n\n- Paths limited to parsing/matching code + tests (enforced)\n"
        f"- Test count not reduced; full suite run in the worktree:\n\n```\n{tail[-1200:]}\n```\n\n"
        "🤖 Generated with [Claude Code](https://claude.com/claude-code)"
    )
    out = subprocess.run(
        [
            "gh",
            "pr",
            "create",
            "--draft",
            "--base",
            BASE_BRANCH,
            "--head",
            branch,
            "--title",
            f"Drift fix {branch.split('/', 1)[1]}: {before.get('status')} probe",
            "--body",
            body,
        ],
        cwd=MAIN,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if out.returncode != 0:
        raise RuntimeError(f"gh pr create: {out.stderr.strip()[-300:]}")
    return out.stdout.strip().splitlines()[-1]


def attempt(md_path: Path, json_path: Path, probe_md: str) -> str:
    """Run the whole stage; return a markdown section for the emailed report.

    `probe_md` is the probe's report BEFORE the analysis section was appended: the
    analysis session can fetch web pages, so its text never reaches this one.
    """
    head = "## Auto-fix\n\n"
    existing = _open_fix_pr()
    if existing:
        return head + f"Skipped: a drift-fix PR is still open: {existing}\n"
    before = json.loads(json_path.read_text(encoding="utf-8"))
    stamp = datetime.now().strftime("%Y-%m-%d")
    branch = f"{BRANCH_PREFIX}{stamp}"
    tree = Path(tempfile.gettempdir()) / f"edge-radar-drift-fix-{stamp}"
    _git("fetch", "-q", "origin", BASE_BRANCH)
    if tree.exists():
        _git("worktree", "remove", "--force", str(tree), check=False)
        shutil.rmtree(tree, ignore_errors=True)
    _git("worktree", "add", "-q", "--detach", str(tree), f"origin/{BASE_BRANCH}")
    try:
        # Gitignored data the probe reads: cached odds + wording baseline only.
        cache = tree / "data" / "cache"
        shutil.copytree(MAIN / "data" / "cache" / "odds", cache / "odds")
        if (MAIN / "data" / "cache" / "drift_baseline.json").exists():
            shutil.copy2(MAIN / "data" / "cache" / "drift_baseline.json", cache)
        inputs = tree / INPUT_DIR  # the session can't read outside the worktree
        inputs.mkdir(parents=True, exist_ok=True)
        (inputs / "probe.md").write_text(probe_md, encoding="utf-8")
        shutil.copy2(json_path, inputs / "probe.json")
        baseline_tests = _collected(tree)
        retry, summary = "", ""
        for attempt_no in (1, 2):
            summary = _claude_fix(tree, retry)
            if not _changed(tree):
                return head + "No code change proposed, so no PR.\n\n" + _quote(summary)
            reason, after, tail = _verify(tree, baseline_tests, before)
            if reason is None:
                url = _commit_and_pr(tree, branch, before, after, tail)
                return head + f"**Draft PR opened:** {url}\n\n" + _quote(summary)
            if attempt_no == 1 and reason == "test suite failed":
                retry = (
                    f"\nYOUR PREVIOUS ATTEMPT FAILED THE TEST SUITE:\n```\n{tail}\n```\nFix it.\n"
                )
                continue
            patch = md_path.with_suffix(".rejected.patch")
            patch.write_text(_git("diff", cwd=tree, check=False), encoding="utf-8")
            return (
                head + f"Fix attempted but **rejected, no PR**: {reason}. "
                f"Diff kept at `{patch.name}`.\n\n" + _quote(summary)
            )
    except Exception as e:  # noqa: BLE001 -- the report must still go out
        return head + f"Auto-fix stage error, no PR: {type(e).__name__}: {e}\n"
    finally:
        _git("worktree", "remove", "--force", str(tree), check=False)
        shutil.rmtree(tree, ignore_errors=True)
    return head + "No PR.\n"


def _quote(text: str) -> str:
    return "\n".join("> " + ln for ln in text.strip()[-2500:].splitlines()) + "\n" if text else ""


if __name__ == "__main__":
    if len(sys.argv) > 3 and sys.argv[1] == "--in-tree":
        sys.exit(_in_tree(Path(sys.argv[2]), sys.argv[3:]))
    sys.exit("usage: called by integration_drift.py --autofix")
