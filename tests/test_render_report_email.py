"""render_report_email: tables survive byte-exact, and stale reports are never sent."""

import importlib.util
import os
import time
from datetime import datetime
from pathlib import Path

_PATH = (
    Path(__file__).resolve().parent.parent / "scripts/schedulers/automation/render_report_email.py"
)
_spec = importlib.util.spec_from_file_location("_render_report_email", _PATH)
r = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(r)

ORDERS = """## Orders

| # | Sport | Qty | Price |
|--:|:------|----:|------:|
| 1 | MLB | 3 | $0.41 |
"""


def test_every_column_and_cell_survives():
    out = r.md_to_html(ORDERS)
    for cell in ("Sport", "Qty", "Price", ">MLB<", ">3<", ">$0.41<"):
        assert cell in out
    # inline style merged with the table's own alignment, not replacing it
    assert 'text-align:right"' in out and "border:1px solid" in out


def test_raw_html_in_a_report_is_escaped():
    """ER-22: market titles and model text reach the email; tags must not render."""
    out = r.md_to_html("Title <img src=x onerror=1> and <b onmouseover=1>x</b> <TN>\n")
    assert "<img" not in out and "<b " not in out
    assert "&lt;img src=x onerror=1&gt;" in out and "&lt;TN&gt;" in out


def test_newest_fresh_report_wins_and_stale_is_ignored(tmp_path):
    old, new = tmp_path / "2026-09-01_x.md", tmp_path / "2026-09-02_x.md"
    old.write_text("old")
    new.write_text("new")
    now = time.time()
    os.utime(old, (now - 7200, now - 7200))
    assert r.find_report(tmp_path, "*.md", 3) == new
    os.utime(new, (now - 5 * 3600, now - 5 * 3600))
    assert r.find_report(tmp_path, "*.md", 3) == old
    assert r.find_report(tmp_path, "*.md", 1) is None


def test_log_excerpt_keeps_last_run_without_info(tmp_path):
    log = tmp_path / "scan.log"
    log.write_text(
        "=====\nrun one\n=====\n" "x | model_calibration | INFO | noise\nApproved: 0  Rejected: 4\n"
    )
    assert r.log_excerpt(log) == "Approved: 0  Rejected: 4"


def test_weekly_analysis_email_opens_with_audit_flags():
    """2026-10-27: one Sunday email -- the audit's flags lead the analysis."""
    audit = (
        "# Betting Audit -- 2026-11-01\n\n**Status: WARN** · window 60d\n\nintro\n\n"
        "## Flags\n\n- `KXNCAAFTOTAL` 93% under\n\n"
        "## Model vs market\n\n| a | b |\n|--|--|\n| 1 | 2 |\n\n"
        "## Analysis\n\nNCAAF total stdev looks narrow.\n"
    )
    lead = r.lead_sections(audit, r.LEADS["weekly-analysis"][2])
    assert lead.startswith("# Betting Audit") and "**Status: WARN**" in lead
    assert "93% under" in lead and "stdev looks narrow" in lead
    assert "Model vs market" not in lead and "intro" not in lead


# ── ER-07: a failed execute run emails [FAILED] instead of exiting 2 silently


def _exec_preset(tmp_path, monkeypatch, log_text=None, report=True):
    monkeypatch.setattr(r, "REPO", tmp_path)
    folder = tmp_path / r.PRESETS["same-day"][0]
    folder.mkdir(parents=True)
    if report:
        (folder / "2026-11-17_sports_execution.md").write_text("# report")
    if log_text is not None:
        log = tmp_path / r.SCAN_LOGS["same-day"]
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(log_text)


def test_clean_execute_run_is_not_a_failure(tmp_path, monkeypatch):
    _exec_preset(tmp_path, monkeypatch, "===== old\nexit code 1\n===== new\nok\nexit code 0 \n")
    assert r.failure("same-day", 3) is None


def test_nonzero_scan_exit_is_a_failure_even_with_a_report(tmp_path, monkeypatch):
    _exec_preset(tmp_path, monkeypatch, "===== run\nTraceback ...\nexit code 1 \n")
    assert r.failure("same-day", 3) == "scan exited 1"
    page, text = r.build_failure("same-day", "scan exited 1")
    assert "FAILED" in page and "Traceback" in text


def test_missing_report_on_execute_preset_is_a_failure(tmp_path, monkeypatch):
    _exec_preset(tmp_path, monkeypatch, report=False)
    assert r.failure("same-day", 3) == "no report newer than 3h"
    assert "no scan log" in r.build_failure("same-day", "x")[1]


def test_non_execute_preset_never_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(r, "REPO", tmp_path)
    assert r.failure("daily-summary", 3) is None


# ── ER-33: the inbox line answers "did it trade?"; the email reads on a phone

LIVE_REPORT = (
    "# Sports Execution Report\n\n**LIVE · REAL MONEY · PROD** · 1 placed · 1 failed\n\n"
    "**Sized cost: $2.08**\n**Placed cost: $1.04**\n"
)


def _fixed_day(monkeypatch):
    day = datetime(2026, 11, 16, 17, 5, tzinfo=r.LOCAL_ZONES[0][1])
    monkeypatch.setattr(r, "_local_now", lambda: day)


def test_subject_shows_mode_count_cost_and_date(monkeypatch):
    _fixed_day(monkeypatch)
    detail, cells, tone = r.status("Same-Day", LIVE_REPORT)
    assert r.subject("Same-Day", detail) == (
        "Edge-Radar | Same-Day | LIVE · 1 placed · 1 failed · $1.04 | Mon Nov 16"
    )
    assert ("Cost", "$1.04 placed") in cells and tone == "amber"


def test_subject_for_dry_runs_failures_and_plain_reports(monkeypatch):
    _fixed_day(monkeypatch)
    dry = "**DRY RUN · nothing sent** · 2 dry run\n\n**Sized cost: $3.10**\n"
    assert r.status("Next-Day", dry)[0] == "DRY RUN · 2 dry run · $3.10 sized"
    failed = r.status("Same-Day", "", "scan exited 1")
    assert r.subject("Same-Day", failed[0], failed=True) == (
        "[FAILED] Edge-Radar | Same-Day | scan exited 1 | Mon Nov 16"
    )
    assert failed[2] == "red"
    warn = r.status("Weekly Analysis", "# Audit\n\n**Status: WARN** · window 60d\n")
    assert warn[0] == "WARN" and warn[2] == "amber"
    assert r.subject("Daily Summary", r.status("Daily Summary", "# x\n")[0]) == (
        "Edge-Radar | Daily Summary | Mon Nov 16"
    )


def test_page_has_banner_preheader_and_readable_footer(monkeypatch):
    _fixed_day(monkeypatch)
    page = r.wrap(["<p>body</p>"], "x.md", r.status("Same-Day", LIVE_REPORT))
    assert page.index("display:none") < page.index('<table role="presentation"')
    assert "LIVE · REAL MONEY · PROD · 1 placed · 1 failed · $1.04 placed" in page
    assert "color:#6b7280;font-size:12px" in page and "#888" not in page
    assert "PT" in page and "ET" in page and "UTC" in page


def test_wide_table_gets_a_stacked_copy_for_phones():
    wide = (
        "| # | Sport | Bet | Type | Pick | When | Qty | Cost |\n"
        "|--:|:--|:--|:--|:--|:--|--:|--:|\n"
        "| 1 | NBA | LAL vs BOS | ML | LAL | Nov 16 | 2 | $1.04 |\n"
    )
    out = r.md_to_html(wide)
    assert 'class="er-wide"' in out and 'class="er-stack"' in out
    assert "<strong>#1 · NBA · LAL vs BOS</strong>" in out
    assert '<span style="color:#6b7280">Cost</span> $1.04' in out
    assert "er-stack" not in r.md_to_html(ORDERS)  # four columns fit a phone
    assert "@media only screen and (max-width:600px)" in r.wrap([out], "x.md")
