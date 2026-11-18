"""ER-50: the ops-health table turns a broken unattended task into a FAIL line."""

from datetime import datetime, timedelta, timezone

import ops_health
from daily_summary import build_report
from ops_health import Check, backup_check, render, settlement_check, task_checks

NOW = datetime(2026, 11, 18, 13, 0, tzinfo=timezone.utc)


def _iso(dt):
    return dt.isoformat()


def _task(name, state="Ready", result=0, last_h=6, next_h=18, args=""):
    return {
        "name": name,
        "state": state,
        "result": result,
        "last": _iso(NOW - timedelta(hours=last_h)) if last_h is not None else "",
        "next": _iso(NOW + timedelta(hours=next_h)) if next_h is not None else "",
        "args": args,
    }


def _status(checks, name):
    return next(c.status for c in checks if c.name == name)


def test_disabled_execute_task_is_fail_other_disabled_is_warn():
    checks = task_checks(
        [
            _task("All-Sports-SameDay-Execution", state="Disabled"),
            _task("Backtest", state="Disabled"),
        ],
        NOW,
    )
    assert _status(checks, "All-Sports-SameDay-Execution") == "FAIL"
    assert _status(checks, "Backtest") == "WARN"


def test_failing_result_is_fail_running_is_ok():
    checks = task_checks([_task("Reconcile", result=1), _task("CLV-Capture", result=0x41301)], NOW)
    assert _status(checks, "Reconcile") == "FAIL"
    assert "0x1" in next(c.detail for c in checks if c.name == "Reconcile")
    assert _status(checks, "CLV-Capture") == "OK"


def test_never_ran_and_missed_start_are_warnings():
    checks = task_checks(
        [
            _task("Calibration", result=0x41303, last_h=None),
            _task("Daily-Summary", next_h=-3),
        ],
        NOW,
    )
    assert _status(checks, "Calibration") == "WARN"
    assert _status(checks, "Daily-Summary") == "WARN"


def test_unreadable_or_empty_task_folder():
    assert task_checks(None, NOW)[0].status == "WARN"
    assert task_checks([], NOW)[0].status == "FAIL"


def test_settlement_age():
    fresh = [{"settled_at": _iso(NOW - timedelta(hours=5))}]
    stale = [{"settled_at": _iso(NOW - timedelta(days=4))}]
    assert settlement_check(fresh, NOW).status == "OK"
    assert settlement_check(stale, NOW).status == "WARN"
    assert settlement_check([], NOW).status == "WARN"


def test_backup_found_through_the_reconcile_task(tmp_path):
    zip_ = tmp_path / "edge-radar-ledger_20261118T073003Z.zip"
    zip_.write_bytes(b"PK")
    args = f'"run-hidden.vbs" "python.exe" "backup_ledger.py" --dest "{tmp_path}"'
    assert backup_check([_task("Reconcile", args=args)], datetime.now(timezone.utc)).status == "OK"
    assert backup_check([_task("Reconcile")], NOW).status == "WARN"
    empty = tmp_path / "empty"
    empty.mkdir()
    args = f'"backup_ledger.py" --dest "{empty}"'
    assert backup_check([_task("Reconcile", args=args)], NOW).status == "FAIL"


def test_render_lists_fail_first_with_a_verdict():
    text = render([Check("a", "OK", "x"), Check("b", "FAIL", "y"), Check("c", "WARN", "z")])
    rows = [ln for ln in text.splitlines() if ln.startswith("| ") and "Check" not in ln]
    assert rows[0].startswith("| b | FAIL")
    assert "**Status: FAIL** 1 FAIL, 1 WARN" in text
    assert render([Check("a", "OK", "x")]).count("**Status: OK**") == 1


def test_daily_summary_puts_ops_health_first(monkeypatch):
    monkeypatch.setattr(ops_health, "query_tasks", lambda: [_task("X-Execution", state="Disabled")])
    ops = render(ops_health.collect(NOW, []))
    report = build_report(NOW, 24, settlements=[], trades=[], balance=None, ops=ops)
    assert "## Ops health" in report
    assert "| X-Execution | FAIL |" in report
    first_section = next(ln for ln in report.splitlines() if ln.startswith("## "))
    assert first_section == "## Ops health"
    assert "## Ops health" not in build_report(NOW, 24, settlements=[], trades=[], balance=None)


def test_fail_reaches_the_email_subject():
    """Acceptance: a disabled execute task shows FAIL in the morning email."""
    import importlib.util
    from pathlib import Path

    path = (
        Path(__file__).resolve().parents[1] / "scripts/schedulers/automation/render_report_email.py"
    )
    spec = importlib.util.spec_from_file_location("_rre_ops", path)
    rre = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rre)

    ops = render(task_checks([_task("All-Sports-SameDay-Execution", state="Disabled")], NOW))
    report = build_report(NOW, 24, settlements=[], trades=[], balance=None, ops=ops)
    detail, _cells, tone = rre.status("Daily Summary", report)
    assert detail == "FAIL" and tone == "red"
    assert "| Daily Summary | FAIL |" in rre.subject("Daily Summary", detail)
