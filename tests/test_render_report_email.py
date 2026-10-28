"""render_report_email: tables survive byte-exact, and stale reports are never sent."""

import importlib.util
import os
import time
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
