"""
ops_health.py -- is the unattended machinery running? (ER-50)

One table, read at the top of the morning Daily-Summary email and by
`python scripts/doctor.py --ops`:

  * every scheduled task in the Edge-Radar Task Scheduler folder: state, last
    run, last result, next run. A disabled or failing execute task is FAIL.
  * the newest settlement, so a settler that runs but finds nothing shows up
  * the newest scheduler report per preset folder
  * the newest ledger backup (the `--dest` the Reconcile task passes to
    backup_ledger.py)
  * the size of data/ and logs/

Read-only: it queries Task Scheduler and stats files, nothing else. Off Windows,
or when Task Scheduler can't be read, the task rows become one WARN line and
the file checks still run.
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import paths

ROOT = paths.PROJECT_ROOT
PT = ZoneInfo("America/Los_Angeles")  # the times every Edge-Radar report uses

# Every task under a Task Scheduler folder whose path contains this (see
# docs/task-schedules/README.md) -- no folder name to keep in sync.
TASK_FOLDER_MATCH = "Edge-Radar"

# Task Scheduler result codes that are not failures.
_OK_RESULTS = {0, 0x41301, 0x41325}  # success, currently running, queued
_NEVER_RAN = 0x41303

_PS_QUERY = (
    "$rows = Get-ScheduledTask | Where-Object TaskPath -match '"
    + TASK_FOLDER_MATCH
    + "' | ForEach-Object { $i = $_ | Get-ScheduledTaskInfo; [pscustomobject]@{"
    "name = $_.TaskName; state = [string]$_.State;"
    " last = if ($i.LastRunTime) { $i.LastRunTime.ToUniversalTime().ToString('o') } else { '' };"
    " result = [int64]$i.LastTaskResult;"
    " next = if ($i.NextRunTime) { $i.NextRunTime.ToUniversalTime().ToString('o') } else { '' };"
    " args = (($_.Actions | ForEach-Object { [string]$_.Arguments }) -join ' ') } };"
    " ConvertTo-Json -InputObject @($rows) -Compress"
)


@dataclass
class Check:
    name: str
    status: str  # OK | WARN | FAIL
    detail: str


def _ago(then: datetime, now: datetime) -> str:
    hours = (now - then).total_seconds() / 3600
    return f"{hours:.0f}h ago" if hours < 48 else f"{hours / 24:.0f}d ago"


def _parse(ts: str) -> datetime | None:
    if not ts or ts.startswith(("0001", "1999")):
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def query_tasks() -> list[dict] | None:
    """The Edge-Radar scheduled tasks, or None when Task Scheduler can't be read."""
    try:
        proc = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", _PS_QUERY],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    try:
        rows = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None
    return rows if isinstance(rows, list) else [rows]


def task_checks(rows: list[dict] | None, now: datetime) -> list[Check]:
    if rows is None:
        return [Check("Scheduled tasks", "WARN", "Task Scheduler not readable on this machine")]
    if not rows:
        return [Check("Scheduled tasks", "FAIL", f"no task under a '{TASK_FOLDER_MATCH}' folder")]
    out = []
    for r in sorted(rows, key=lambda r: r.get("name", "")):
        name = r.get("name", "?")
        live = "Execution" in name  # the tasks that place orders
        last, nxt = _parse(r.get("last", "")), _parse(r.get("next", ""))
        result = int(r.get("result") or 0)
        when = f"last {_ago(last, now)}" if last else "never ran"
        when += (
            f", next {nxt.astimezone(PT).strftime('%a %I:%M %p')} PT" if nxt else ", no next run"
        )
        if r.get("state") == "Disabled":
            status, why = ("FAIL" if live else "WARN"), "disabled"
        elif r.get("state") == "Running":
            # LastTaskResult is mid-flight while a task runs (Daily-Summary reads its
            # own row as 0x800710E0), so trust the next finished run instead.
            status, why = "OK", "running now"
        elif result == _NEVER_RAN or last is None:
            status, why = "WARN", "has not run yet"
        elif result not in _OK_RESULTS:
            status, why = "FAIL", f"last run failed (0x{result & 0xFFFFFFFF:X})"
        elif nxt is None:
            status, why = "WARN", "nothing scheduled"
        elif (now - nxt).total_seconds() > 3600:
            status, why = "WARN", "missed its last start (machine asleep or off?)"
        else:
            status, why = "OK", "ok"
        out.append(Check(name, status, f"{why}; {when}"))
    return out


def _newest(paths_: list[Path]) -> Path | None:
    files = [p for p in paths_ if p.is_file()]
    return max(files, key=lambda p: p.stat().st_mtime) if files else None


def _mtime(p: Path) -> datetime:
    return datetime.fromtimestamp(p.stat().st_mtime, timezone.utc)


def settlement_check(settlements: list[dict], now: datetime) -> Check:
    stamps = [_parse(s.get("settled_at", "")) for s in settlements]
    stamps = [s for s in stamps if s]
    if not stamps:
        return Check("Newest settlement", "WARN", "no settlements logged")
    newest = max(stamps)
    status = "OK" if (now - newest).days < 3 else "WARN"
    return Check("Newest settlement", status, _ago(newest, now))


def backup_check(rows: list[dict] | None, now: datetime) -> Check:
    dest = None
    for r in rows or []:
        m = re.search(r'backup_ledger\.py"?\s+--dest\s+"([^"]+)"', r.get("args", ""))
        if m:
            dest = Path(m.group(1))
    if dest is None:
        return Check("Ledger backup", "WARN", "no task runs backup_ledger.py --dest")
    newest = _newest(list(dest.glob("edge-radar-ledger_*.zip"))) if dest.is_dir() else None
    if newest is None:
        return Check("Ledger backup", "FAIL", f"no backup zip in {dest.name}/")
    age = now - _mtime(newest)
    status = "OK" if age.days < 2 else "WARN" if age.days < 7 else "FAIL"
    return Check("Ledger backup", status, f"{newest.name}, {_ago(_mtime(newest), now)}")


def report_checks(now: datetime) -> list[Check]:
    base = ROOT / "reports" / "Sports" / "schedulers"
    out = []
    for folder in sorted(p for p in base.glob("*") if p.is_dir()) if base.is_dir() else []:
        newest = _newest(list(folder.glob("*.md")))
        if newest:
            out.append(Check(f"Reports: {folder.name}", "OK", _ago(_mtime(newest), now)))
    return out


def _size_mb(folder: Path) -> float:
    if not folder.is_dir():
        return 0.0
    return sum(p.stat().st_size for p in folder.rglob("*") if p.is_file()) / 1e6


def size_checks() -> list[Check]:
    out = []
    for label, folder, warn_mb in (("data/", paths.DATA_DIR, 500), ("logs/", ROOT / "logs", 500)):
        mb = _size_mb(folder)
        out.append(Check(f"Size {label}", "WARN" if mb > warn_mb else "OK", f"{mb:,.0f} MB"))
    return out


def collect(now: datetime, settlements: list[dict], rows: list[dict] | None = None) -> list[Check]:
    rows = query_tasks() if rows is None else rows
    return [
        *task_checks(rows, now),
        settlement_check(settlements, now),
        backup_check(rows, now),
        *report_checks(now),
        *size_checks(),
    ]


def render(checks: list[Check]) -> str:
    """Markdown section, FAIL rows first, under a `**Status: OK|WARN|FAIL**` verdict."""
    order = {"FAIL": 0, "WARN": 1, "OK": 2}
    fails = sum(c.status == "FAIL" for c in checks)
    warns = sum(c.status == "WARN" for c in checks)
    # A `**Status: X**` line is what render_report_email.py puts in the subject and
    # banner colour, so a FAIL here reads "Daily Summary | FAIL" in the inbox.
    word = "FAIL" if fails else "WARN" if warns else "OK"
    verdict = f"**Status: {word}** {fails} FAIL, {warns} WARN across {len(checks)} ops checks."
    lines = ["## Ops health", "", verdict, "", "| Check | Status | Detail |", "|:--|:--|:--|"]
    for c in sorted(checks, key=lambda c: (order.get(c.status, 3), c.name)):
        lines.append(f"| {c.name} | {c.status} | {c.detail} |")
    return "\n".join(lines) + "\n"
